"""
Generate a synthetic PDF contract with intentional compliance defects.
For QA only — not a real legal document.

Requires: pip install pymupdf
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Install pymupdf: pip install pymupdf", file=sys.stderr)
    sys.exit(1)

OUT = Path(__file__).resolve().parents[1] / "data" / "test_samples" / "contract_bad_compliance_fr.pdf"

CHECKLIST = """
CONTRAT DE TEST — NE PAS UTILISER EN PRODUCTION
Référence interne: QA-BAD-CONTRACT-001

Ce document est volontairement défectueux pour valider les Agents 1, 2 et 3.

=== CE QUE LE SYSTÈME DEVRAIT DÉTECTER (Agent 2 — drapeaux typiques) ===
• missing_retention_period : traitement de données sans durée de conservation.
• missing_consent_mechanism : aucune base légale / consentement explicite clair.
• missing_dpo_reference : traitement sensible sans mention DPO / point de contact dédié.
• excessive_data_collection : collecte large sans finalité proportionnée.
• missing_security_measures : absence de mesures techniques et organisationnelles.
• unlawful_cross_border_transfer : transfert hors Tunisie / UE sans garanties (SCC, etc.).
• missing_data_subject_rights : pas d’accès, rectification, effacement, opposition.
• unclear_liability_cap : plafond de responsabilité absent ou contradictoire.
• lnpdp_relevant / gdpr_relevant : clauses traitement de données personnelles.

=== Agent 3 (règles LNPDP / GDPR / ISO) ===
Corréler les violations aux articles via rule_engine (ex. conservation, sécurité,
transferts, droits des personnes) selon vos fichiers JSON lnpdp.json / gdpr.json.

=== Fin de la checklist ===
""".strip()

CONTRACT_BODY = """
CONTRAT DE PRESTATION DE SERVICES ET TRAITEMENT DE DONNÉES
Entre la société ACME SARL (« le Prestataire ») et le client final (« le Client »),
il est convenu ce qui suit, sans ordre d’importance juridique.

Article 1 — Objet
Le Prestataire fournit des services cloud et collecte toutes les informations
nécessaires sur les employés, la famille, les habitudes de navigation, la géolocalisation
en temps réel et les données de santé lorsque cela est utile à l’amélioration du service.

Article 2 — Données personnelles
Les données personnelles des utilisateurs sont traitées pour les besoins du service.
Le Client accepte implicitement tout traitement ultérieur. Aucune durée de conservation
n’est fixée : les données peuvent être conservées indéfiniment.

Article 3 — Transferts
Les données peuvent être stockées et traitées sur des serveurs situés aux États-Unis,
en Chine et dans tout pays offrant des tarifs compétitifs, sans formalité supplémentaire.

Article 4 — Sécurité
Le Prestataire applique des mesures de sécurité « raisonnables » sans autre précision.

Article 5 — Droits des personnes
Les personnes concernées n’ont pas d’interface dédiée pour exercer leurs droits.

Article 6 — Responsabilité
En cas de faute, la responsabilité du Prestataire est illimitée pour certains dommages
et nulle pour d’autres, selon appréciation unilatérale du Prestataire.

Article 7 — Sous-traitance
Le Prestataire peut sous-traiter à tout tiers sans information préalable du Client.

Article 8 — Loi applicable
Les parties reconnaissent la compétence exclusive des tribunaux du Prestataire.

Fait à Tunis, sans date ni signature électronique qualifiée.
""".strip()


def _add_wrapped_page(doc: fitz.Document, title: str, body: str, fontsize: float = 10) -> None:
    page = doc.new_page(width=595, height=842)  # A4
    margin = 50
    rect = fitz.Rect(margin, margin, 595 - margin, 842 - margin)
    text = f"{title}\n\n{body}"
    page.insert_textbox(
        rect,
        text,
        fontsize=fontsize,
        fontname="helv",
        align=fitz.TEXT_ALIGN_LEFT,
    )


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    _add_wrapped_page(
        doc,
        "CHECKLIST DÉTECTION (lecture QA)",
        CHECKLIST,
        fontsize=9,
    )
    _add_wrapped_page(
        doc,
        "TEXTE DU CONTRAT SYNTHÉTIQUE (défauts intentionnels)",
        CONTRACT_BODY,
        fontsize=11,
    )
    doc.save(str(OUT))
    doc.close()
    print(f"Wrote: {OUT}")


if __name__ == "__main__":
    main()
