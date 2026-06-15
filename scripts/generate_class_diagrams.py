#!/usr/bin/env python3
"""Generate class diagrams + global UC for LexAI rapport via Kroki."""
import requests, os, sys

OUT = r"c:/Users/Ala/Desktop/PFE/rapport/images"
os.makedirs(OUT, exist_ok=True)
KROKI = "https://kroki.io/plantuml/png"

SKIN = """
skinparam defaultFontName Arial
skinparam defaultFontSize 10
skinparam class {
  BackgroundColor #D6EAF8
  BorderColor #2471A3
  HeaderBackgroundColor #2471A3
  HeaderFontColor white
  BorderThickness 1.5
}
skinparam ArrowColor #2C3E50
skinparam shadowing false
"""

DIAGRAMS = {

"uc_global": """@startuml
title Diagramme de cas d utilisation global - Plateforme LexAI
left to right direction
skinparam defaultFontName Arial
skinparam defaultFontSize 11
skinparam usecase {
  BackgroundColor #D6EAF8
  BorderColor #2471A3
}
skinparam actor {
  BackgroundColor #FDFEFE
  BorderColor #2C3E50
}
skinparam rectangle {
  BackgroundColor #FAFBFC
  BorderColor #808B96
}
skinparam shadowing false

actor "Juriste" as J
actor "Responsable conformite" as RC
actor "Administrateur" as A

rectangle "Plateforme LexAI" {
  usecase "Televerser un contrat" as UC1
  usecase "Suivre la progression" as UC2
  usecase "Consulter extraction" as UC3
  usecase "Consulter analyse NLP" as UC4
  usecase "Evaluer la conformite" as UC5
  usecase "Consulter recommandations" as UC6
  usecase "Exporter contrat revise" as UC7
  usecase "Relancer traitement" as UC8
  usecase "Supprimer un document" as UC9
}

J --> UC1
J --> UC2
J --> UC3
J --> UC4
J --> UC6
J --> UC7
J --> UC9
RC --> UC5
RC --> UC6
RC --> UC7
A --> UC8
A --> UC9
@enduml""",

"class_agent1": """@startuml
title Diagramme de classes -- Agent 1 : Extraction documentaire
""" + SKIN + """
abstract class DocumentExtractorProvider {
  + {abstract} extract(file_path: Path): ExtractionArtifact
}

class PdfProvider {
  + extract(file_path: Path): ExtractionArtifact
  - extract_pages(doc): list
  - detect_scanned(page): bool
}

class DocxProvider {
  + extract(file_path: Path): ExtractionArtifact
  - extract_headings(doc): list
}

class TxtProvider {
  + extract(file_path: Path): ExtractionArtifact
}

class HtmlProvider {
  + extract(file_path: Path): ExtractionArtifact
  - strip_scripts(soup): str
}

class ProviderRegistry {
  - _registry: dict
  + get_provider(mime_type: str): DocumentExtractorProvider
  + register(mime_type: str, provider)
}

class Normalizer {
  + normalize(raw_text: str): str
  - fix_encoding(text: str): str
  - collapse_whitespace(text: str): str
  - normalize_newlines(text: str): str
}

class ExtractionArtifact {
  + raw_text: str
  + structure_json: dict
  + page_metadata: list
  + warnings: list
}

class Document {
  + id: int
  + filename: str
  + mime_type: str
  + status: str
  + progress_percent: int
  + task_id: str
  + created_at: datetime
  + finished_at: datetime
}

class Extraction {
  + id: int
  + document_id: int
  + raw_text: str
  + normalized_text: str
  + structure_json: str
  + warnings: list
  + created_at: datetime
}

DocumentExtractorProvider <|-- PdfProvider
DocumentExtractorProvider <|-- DocxProvider
DocumentExtractorProvider <|-- TxtProvider
DocumentExtractorProvider <|-- HtmlProvider
ProviderRegistry o-- DocumentExtractorProvider
Document "1" -- "1" Extraction : has
@enduml""",

"class_agent2": """@startuml
title Diagramme de classes -- Agent 2 : Analyse NLP
""" + SKIN + """
class LanguageDetector {
  + detect(text: str): str
  - arabic_heuristic(text: str): bool
  - langdetect_fallback(text: str): str
}

class ClauseSegmenter {
  + segment(text: str, structure: dict): list
  - strategy_structure(text, structure): list
  - strategy_regex(text: str): list
  - strategy_paragraphs(text: str): list
}

class EntityExtractor {
  - nlp_model
  - _nlp_source: str
  + extract(clause: ClauseSegment): list
  - apply_rules(doc): list
}

class ClauseClassifier {
  - pipeline
  - threshold: float
  - _model_mode: str
  + classify(text: str): ClassificationResult
  - keyword_fallback(text: str): list
}

class ClauseSegment {
  + clause_id: str
  + text: str
  + start_char: int
  + end_char: int
  + language: str
  + labels: list
  + compliance_flags: list
  + entities: list
  + confidence: float
}

class Entity {
  + text: str
  + label: str
  + start: int
  + end: int
  + confidence: float
}

class NLPAnalysis {
  + id: int
  + document_id: int
  + language: str
  + clause_count: int
  + clauses_json: str
  + entities_json: str
  + created_at: datetime
}

NLPAnalysis "1" *-- "N" ClauseSegment : contains
ClauseSegment "1" *-- "N" Entity : has
ClauseClassifier --> ClauseSegment : enriches
EntityExtractor --> ClauseSegment : enriches
@enduml""",

"class_agent3": """@startuml
title Diagramme de classes -- Agent 3 : Evaluation de conformite
""" + SKIN + """
class RuleEngine {
  - rules: dict
  - weights: dict
  - mandatory_clauses: list
  + load_rules(): void
  + evaluate(clauses: list): EvaluationResult
  + determine_active_frameworks(clauses): list
  - match_rule(rule, clause): bool
  - detect_missing_clauses(clauses): list
}

class Rule {
  + rule_id: str
  + article: str
  + framework: str
  + title: str
  + trigger_flags: list
  + trigger_labels: list
  + severity: str
  + mandatory: bool
  + remediation_hint: str
}

class Violation {
  + violation_id: str
  + rule_id: str
  + clause_id: str
  + framework: str
  + article: str
  + severity: str
  + description: str
  + remediation_hint: str
}

class ComplianceScorer {
  - severity_weights: dict
  - framework_weights: dict
  + compute_scores(violations, frameworks): ScoreResult
  - framework_score(violations, framework): float
  - global_score(framework_scores): float
  - litigation_risk(score: float): str
}

class ScoreResult {
  + global_score: float
  + lnpdp_score: float
  + gdpr_score: float
  + iso27001_score: float
  + iso9001_score: float
  + litigation_risk: str
  + active_frameworks: list
}

class Evaluation {
  + id: int
  + document_id: int
  + global_score: float
  + litigation_risk: str
  + violations_json: str
  + missing_clauses_json: str
  + active_frameworks_json: str
  + evaluated_at: datetime
}

RuleEngine "1" o-- "N" Rule
RuleEngine --> Violation : produces
RuleEngine --> ComplianceScorer : uses
ComplianceScorer --> ScoreResult : produces
Evaluation "1" *-- "N" Violation
@enduml""",

"class_agent4": """@startuml
title Diagramme de classes -- Agent 4 : Generation de recommandations
""" + SKIN + """
class Recommender {
  - templates: dict
  + build_recommendations(violations, clauses): list
  + load_templates(): void
  - slot_filling(template, entities): str
  - fallback_recommendation(violation): dict
  - first_entity_by_label(clause, label): str
  - sort_by_severity(violations): list
}

class Template {
  + rule_id: str
  + framework: str
  + article: str
  + issue_description: str
  + recommendation_text: str
  + rewritten_clause: str
  + legal_rationale: str
  + slots: dict
}

class Recommendation {
  + id: int
  + document_id: int
  + violation_id: str
  + clause_id: str
  + violation_rule_id: str
  + framework: str
  + severity: str
  + priority: int
  + issue_description: str
  + recommendation_text: str
  + rewritten_clause: str
  + legal_rationale: str
  + generated_by: str
  + created_at: datetime
}

class Rewrite {
  + id: int
  + document_id: int
  + recommendation_id: int
  + decision: str
  + revised_text: str
  + decided_at: datetime
}

class RewriteEngine {
  + assemble_revised_contract(document_id, decisions): str
  + export_docx(text: str): bytes
  + export_pdf(text: str): bytes
}

Recommender "1" o-- "N" Template
Recommender --> Recommendation : produces
Recommendation "1" --> "0..1" Rewrite
RewriteEngine --> Rewrite : reads
@enduml""",
}

def generate(name, code):
    try:
        r = requests.post(KROKI, data=code.encode("utf-8"),
                          headers={"Content-Type": "text/plain"}, timeout=30)
        r.raise_for_status()
        path = os.path.join(OUT, f"{name}.png")
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"  OK  {name}.png  ({len(r.content)//1024} KB)")
    except Exception as e:
        print(f"  ERR {name}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print(f"Generating {len(DIAGRAMS)} diagrams via Kroki...")
    for name, code in DIAGRAMS.items():
        generate(name, code)
    print(f"\nDone! Saved to {OUT}")
