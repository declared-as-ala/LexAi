"""
ClauseClassifier — Agent 2 submodule.
Multi-label clause classification.

Loading priority:
  1. Fine-tuned model at data/models/clause_classifier/  (best accuracy)
  2. Zero-shot XLM-RoBERTa legal model                   (no training needed)
  3. Keyword heuristics                                   (always works)

To train the fine-tuned model:
  python scripts/download_datasets.py
  python scripts/convert_cuad.py
  python scripts/convert_ledgar.py
  python scripts/generate_synthetic.py
  python scripts/build_dataset.py
  python scripts/train_classifier.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from app.core.logging import get_logger
from app.services.nlp.clause_segmenter import ClauseSegment
from app.services.nlp.taxonomy import (
    CLAUSE_LABEL_STRINGS,
    ClauseLabel,
    ComplianceFlag,
)

logger = get_logger(__name__)

# Path to fine-tuned model (produced by train_classifier.py)
# DATA_DIR env var lets Docker override the path via a volume mount.
_DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent.parent.parent.parent.parent / "data"))
_FINETUNED_MODEL_DIR = _DATA_DIR / "models" / "clause_classifier"

# Zero-shot fallback models (tried in order if fine-tuned model absent)
_ZEROSHOT_MODELS = [
    "joelniklaus/legal-xlm-roberta-large",
    "joeddav/xlm-roberta-large-xnli",
]

# Thresholds
_FINETUNED_THRESHOLD = 0.40   # sigmoid score threshold for fine-tuned model
_ZEROSHOT_THRESHOLD  = 0.25   # zero-shot NLI entailment threshold

# Module-level pipeline cache (avoids reloading on every Celery task)
_PIPELINE_CACHE: object | None = None      # loaded pipeline or False
_PIPELINE_MODEL_NAME: str = "none"
_PIPELINE_MODE: str = "none"               # "finetuned" | "zeroshot" | "heuristic"

# Compliance keyword heuristics
_LNPDP_KEYWORDS = {
    "lnpdp", "2004-63", "données personnelles", "données à caractère personnel",
    "inpdp", "protection des données", "traitement des données",
}
_GDPR_KEYWORDS = {
    "rgpd", "gdpr", "règlement général", "general data protection",
    "responsable du traitement", "sous-traitant", "dpo",
    "délégué à la protection",
}
_RETENTION_KEYWORDS = {
    "durée de conservation", "période de conservation", "retention period",
    "conservation des données", "période de rétention",
}
_CONSENT_KEYWORDS = {
    "consentement", "consent", "base légale", "legal basis",
    "finalité", "purpose", "opt-in", "opt-out",
}
_SECURITY_KEYWORDS = {
    "mesures de sécurité", "security measures", "chiffrement", "encryption",
    "pseudonymisation", "anonymisation", "accès autorisé", "authorized access",
}
_CROSS_BORDER_KEYWORDS = {
    "transfert international", "transfert transfrontalier", "cross-border transfer",
    "pays tiers", "third country", "hors de tunisie", "hors de l'ue",
}


@dataclass
class ClassificationResult:
    labels: list[str] = field(default_factory=list)
    compliance_flags: list[str] = field(default_factory=list)
    confidence: float = 0.0
    model_used: str = "none"


class ClauseClassifier:
    """
    Multi-label clause classifier.
    Lazy-loads the best available model on first call.
    """

    def __init__(self, language: str = "fr"):
        self.language = language

    # ── Model loading ─────────────────────────────────────────────────────────

    def _load_pipeline(self):
        global _PIPELINE_CACHE, _PIPELINE_MODEL_NAME, _PIPELINE_MODE

        if _PIPELINE_CACHE is not None:
            return _PIPELINE_CACHE if _PIPELINE_CACHE is not False else None

        # 1. Try fine-tuned model
        if _FINETUNED_MODEL_DIR.exists() and (_FINETUNED_MODEL_DIR / "config.json").exists():
            try:
                from transformers import pipeline as hf_pipeline  # type: ignore
                pipe = hf_pipeline(
                    "text-classification",
                    model=str(_FINETUNED_MODEL_DIR),
                    tokenizer=str(_FINETUNED_MODEL_DIR),
                    device=-1,
                )
                _PIPELINE_CACHE = pipe
                _PIPELINE_MODEL_NAME = "finetuned/clause_classifier"
                _PIPELINE_MODE = "finetuned"
                logger.info("classifier_loaded_finetuned", extra={"extra": {"model": str(_FINETUNED_MODEL_DIR)}})
                return pipe
            except Exception as exc:
                logger.warning("finetuned_model_load_failed", extra={"extra": {"error": str(exc)[:200]}})

        # 2. Try zero-shot models
        try:
            from transformers import pipeline as hf_pipeline  # type: ignore
            for model_id in _ZEROSHOT_MODELS:
                try:
                    pipe = hf_pipeline(
                        "zero-shot-classification",
                        model=model_id,
                        multi_label=True,
                        device=-1,
                    )
                    _PIPELINE_CACHE = pipe
                    _PIPELINE_MODEL_NAME = model_id
                    _PIPELINE_MODE = "zeroshot"
                    logger.info("classifier_loaded_zeroshot", extra={"extra": {"model": model_id}})
                    return pipe
                except Exception as exc:
                    logger.warning("zeroshot_model_failed", extra={"extra": {"model": model_id, "error": str(exc)[:100]}})
        except ImportError:
            logger.warning("transformers_not_installed")

        # 3. Heuristic fallback
        _PIPELINE_CACHE = False
        _PIPELINE_MODE = "heuristic"
        logger.info("classifier_using_heuristic")
        return None

    @property
    def _model_used(self) -> str:
        if _PIPELINE_CACHE and _PIPELINE_CACHE is not False:
            return _PIPELINE_MODEL_NAME
        return "heuristic"

    # ── Classification ────────────────────────────────────────────────────────

    def _heuristic_confidence(self, label_count: int) -> float:
        """Uncalibrated band for keyword rules so UI is not stuck at 0% when no HF model runs."""
        n = max(1, label_count)
        return round(min(0.78, 0.34 + 0.07 * n), 2)

    def classify(self, clause: ClauseSegment) -> ClassificationResult:
        text = clause.text.strip()
        if not text:
            return ClassificationResult()

        labels: list[str] = []
        confidence = 0.0
        pipe = self._load_pipeline()
        labels_from_keywords = False

        if pipe is not None:
            try:
                if _PIPELINE_MODE == "finetuned":
                    labels, confidence = self._classify_finetuned(pipe, text)
                else:
                    labels, confidence = self._classify_zeroshot(pipe, text)
            except Exception as exc:
                logger.warning("classifier_inference_failed", extra={"extra": {"error": str(exc)}})

        if not labels:
            labels = self._heuristic_labels(text)
            labels_from_keywords = True

        if labels_from_keywords:
            confidence = self._heuristic_confidence(len(labels))

        # Only fire data-privacy compliance flags when the clause is classified as
        # data_processing; other clause types (force_majeure, payment, etc.) should
        # not trigger "missing retention period" or "missing consent" false positives.
        is_data_clause = ClauseLabel.DATA_PROCESSING.value in labels
        compliance_flags = self._detect_compliance_flags(text, is_data_clause=is_data_clause)

        return ClassificationResult(
            labels=labels,
            compliance_flags=compliance_flags,
            confidence=confidence,
            model_used=self._model_used,
        )

    def _classify_finetuned(self, pipe, text: str) -> tuple[list[str], float]:
        """Use fine-tuned multi-label classifier."""
        # top_k=None returns all labels with scores (replaces removed return_all_scores=True)
        result = pipe(text[:512], truncation=True, top_k=None)
        # result shape: [[{label, score}, ...]] (list of list when top_k=None)
        items = result[0] if isinstance(result[0], list) else result
        labels = []
        top_score = 0.0
        valid_labels = {l.value for l in ClauseLabel}
        for item in items:
            label = item["label"]
            score = item["score"]
            if score >= _FINETUNED_THRESHOLD and label in valid_labels:
                labels.append(label)
                top_score = max(top_score, score)
        return labels, round(top_score, 3)

    def _classify_zeroshot(self, pipe, text: str) -> tuple[list[str], float]:
        """Use zero-shot NLI pipeline."""
        result = pipe(text[:512], candidate_labels=CLAUSE_LABEL_STRINGS, multi_label=True)
        labels = []
        top_score = 0.0
        for label, score in zip(result["labels"], result["scores"]):
            if score >= _ZEROSHOT_THRESHOLD:
                labels.append(label)
                top_score = max(top_score, score)
        if result["scores"]:
            top_score = round(float(result["scores"][0]), 3)
        return labels, top_score

    def classify_all(self, clauses: list[ClauseSegment]) -> dict[str, ClassificationResult]:
        return {clause.clause_id: self.classify(clause) for clause in clauses}

    # ── Heuristic fallback ────────────────────────────────────────────────────

    def _heuristic_labels(self, text: str) -> list[str]:
        lower = text.lower()
        labels = []
        if any(k in lower for k in {"données personnelles", "traitement", "données à caractère"}):
            labels.append(ClauseLabel.DATA_PROCESSING.value)
        if any(k in lower for k in {"confidentiel", "secret", "divulguer", "confidentialité"}):
            labels.append(ClauseLabel.CONFIDENTIALITY.value)
        if any(k in lower for k in {"responsabilité", "liability", "dommages", "préjudice", "indemnif"}):
            labels.append(ClauseLabel.LIABILITY.value)
        if any(k in lower for k in {"résiliation", "termination", "résoudre", "mettre fin", "préavis", "dénonciation"}):
            labels.append(ClauseLabel.TERMINATION.value)
        if any(k in lower for k in {"définition", "au sens de", "s'entend par", "désigne", "signifie"}):
            labels.append(ClauseLabel.DEFINITION.value)
        if any(k in lower for k in {"s'engage", "obligation", "doit", "devra", "tenu de"}):
            labels.append(ClauseLabel.OBLIGATION.value)
        if any(k in lower for k in {"pénalité", "pénalités", "amende", "dommages-intérêts"}):
            labels.append(ClauseLabel.PENALTY.value)
        if any(k in lower for k in {"arbitrage", "juridiction", "tribunal", "compétent", "litige", "droit applicable"}):
            labels.append(ClauseLabel.DISPUTE_RESOLUTION.value)
        if any(k in lower for k in {"force majeure", "cas fortuit", "événement imprévisible"}):
            labels.append(ClauseLabel.FORCE_MAJEURE.value)
        if any(k in lower for k in {"propriété intellectuelle", "droits d'auteur", "brevet", "marque", "licence"}):
            labels.append(ClauseLabel.IP_RIGHTS.value)
        if any(k in lower for k in {"paiement", "prix", "facture", "rémunération", "honoraires", "montant"}):
            labels.append(ClauseLabel.PAYMENT.value)
        if any(k in lower for k in {"garantie", "warranty", "guarantee", "qualité", "conformité"}):
            labels.append(ClauseLabel.WARRANTY.value)
        return labels or [ClauseLabel.OBLIGATION.value]

    def _detect_compliance_flags(self, text: str, is_data_clause: bool = False) -> list[str]:
        lower = text.lower()
        flags = []

        # Informational flags: fire whenever the text references these frameworks
        if any(k in lower for k in _LNPDP_KEYWORDS):
            flags.append(ComplianceFlag.LNPDP_RELEVANT.value)
        if any(k in lower for k in _GDPR_KEYWORDS):
            flags.append(ComplianceFlag.GDPR_RELEVANT.value)

        # Gap flags: only meaningful for data_processing clauses to avoid false positives
        # on force_majeure, payment, termination, etc.
        if is_data_clause:
            if not any(k in lower for k in _RETENTION_KEYWORDS | {"conservation", "retention", "durée"}):
                flags.append(ComplianceFlag.MISSING_RETENTION_PERIOD.value)
            if not any(k in lower for k in _CONSENT_KEYWORDS):
                flags.append(ComplianceFlag.MISSING_CONSENT_MECHANISM.value)
            if not any(k in lower for k in _SECURITY_KEYWORDS):
                flags.append(ComplianceFlag.MISSING_SECURITY_MEASURES.value)
            if not any(k in lower for k in {"droit d'accès", "rectification", "opposition", "suppression", "droits"}):
                flags.append(ComplianceFlag.MISSING_DATA_SUBJECT_RIGHTS.value)

        # Cross-border transfer risk: fire on any clause mentioning transfer keywords
        if any(k in lower for k in _CROSS_BORDER_KEYWORDS):
            flags.append(ComplianceFlag.UNLAWFUL_CROSS_BORDER_TRANSFER.value)

        return flags
