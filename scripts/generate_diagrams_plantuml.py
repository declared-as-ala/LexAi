#!/usr/bin/env python3
"""Generate all UML diagrams via Kroki API (PlantUML) for the LexAI rapport."""
import requests, os, sys

OUT = r"c:/Users/Ala/Desktop/PFE/rapport/images"
os.makedirs(OUT, exist_ok=True)

KROKI = "https://kroki.io/plantuml/png"

SKIN_UC = """
skinparam defaultFontName Arial
skinparam defaultFontSize 11
skinparam usecase {
  BackgroundColor #D6EAF8
  BorderColor #2471A3
  BorderThickness 2
  ArrowColor #2C3E50
}
skinparam actor {
  BackgroundColor #FDFEFE
  BorderColor #2C3E50
  BorderThickness 2
}
skinparam rectangle {
  BackgroundColor #FAFBFC
  BorderColor #808B96
  BorderThickness 1
  BorderStyle dashed
  FontStyle italic
  FontColor #626567
}
skinparam shadowing false
"""

SKIN_SEQ = """
skinparam defaultFontName Arial
skinparam defaultFontSize 10
skinparam sequence {
  ArrowColor #2C3E50
  ActorBorderColor #2C3E50
  LifeLineBorderColor #BDC3C7
  LifeLineBackgroundColor #FAFAFA
  ParticipantBackgroundColor #2471A3
  ParticipantBorderColor #1A5276
  ParticipantFontColor white
  ParticipantFontStyle bold
  BoxBackgroundColor #EBF5FB
  BoxBorderColor #2471A3
  DividerBackgroundColor #EBF5FB
  GroupBackgroundColor #EBF5FB
}
skinparam note {
  BackgroundColor #FEFBD8
  BorderColor #E5E700
}
skinparam shadowing false
"""

DIAGRAMS = {

# ─── USE CASE DIAGRAMS ──────────────────────────────────────────────────────

"uc_sprint1": f"""@startuml
title Diagramme de cas d'utilisation — Sprint 1 : Agent 1 — Extraction documentaire
left to right direction
{SKIN_UC}
actor "Juriste" as J
actor "Administrateur" as A

rectangle "Plateforme LexAI — Agent 1 : Extraction documentaire" {{
  usecase "Televerser un contrat\\n(PDF/DOCX/TXT/HTML)" as UC1
  usecase "Suivre la progression\\ndu traitement" as UC2
  usecase "Consulter les resultats\\nd'extraction" as UC3
  usecase "Relancer un traitement\\nechoue" as UC4
  usecase "Supprimer un document" as UC5
}}

J --> UC1
J --> UC2
J --> UC3
J --> UC5
A --> UC4
A --> UC5
@enduml""",

"uc_sprint2": f"""@startuml
title Diagramme de cas d'utilisation — Sprint 2 : Agent 2 — Analyse NLP
left to right direction
{SKIN_UC}
actor "Juriste" as J
actor "Systeme (Auto)" as S

rectangle "Plateforme LexAI — Agent 2 : Analyse NLP" {{
  usecase "Declencher l'analyse\\nNLP manuellement" as UC1
  usecase "Consulter les clauses\\nsegmentees" as UC2
  usecase "Filtrer par label\\net flag de conformite" as UC3
  usecase "Consulter les entites\\njuridiques extraites" as UC4
  usecase "Consulter le score\\nde confiance" as UC5
}}

J --> UC1
J --> UC2
J --> UC3
J --> UC4
J --> UC5
S --> UC1
@enduml""",

"uc_sprint3": f"""@startuml
title Diagramme de cas d'utilisation — Sprint 3 : Agent 3 — Evaluation de conformite
left to right direction
{SKIN_UC}
actor "Responsable\\nconformite" as RC
actor "Juriste" as J

rectangle "Plateforme LexAI — Agent 3 : Evaluation de conformite" {{
  usecase "Consulter le score\\nde conformite global" as UC1
  usecase "Consulter les violations\\npar referentiel" as UC2
  usecase "Consulter les clauses\\nobligatoires manquantes" as UC3
  usecase "Identifier le niveau\\nde risque juridique" as UC4
  usecase "Re-declencher\\nl'evaluation" as UC5
}}

RC --> UC1
RC --> UC2
RC --> UC3
RC --> UC4
J --> UC5
J --> UC1
@enduml""",

"uc_sprint4": f"""@startuml
title Diagramme de cas d'utilisation — Sprint 4 : Agent 4 — Generation de recommandations
left to right direction
{SKIN_UC}
actor "Juriste" as J

rectangle "Plateforme LexAI — Agent 4 : Generation de recommandations" {{
  usecase "Consulter les\\nrecommandations" as UC1
  usecase "Accepter une\\nrecommandation" as UC2
  usecase "Rejeter une\\nrecommandation" as UC3
  usecase "Exporter le contrat\\nrevise (DOCX/PDF)" as UC4
  usecase "Re-generer les\\nrecommandations" as UC5
}}

J --> UC1
J --> UC2
J --> UC3
J --> UC4
J --> UC5
@enduml""",

# ─── SEQUENCE DIAGRAMS ──────────────────────────────────────────────────────

"seq_sprint1": f"""@startuml
title Diagramme de sequence — Sprint 1 : Televerser et extraire un contrat
{SKIN_SEQ}
participant "Juriste" as J
participant "API FastAPI" as API
participant "Worker Celery" as W
participant "Provider\\n(PDF/DOCX...)" as P
participant "PostgreSQL" as DB

== 1 - Televersement ==
J -> API: POST /documents/upload (fichier)
note right: Validation MIME, extension, taille <= 50 Mo
API -> DB: INSERT documents (status=queued)
DB --> API: document_id
API --> J: 201 {{ document_id }}

== 2 - Traitement asynchrone ==
API -> W: enqueue_extraction(document_id)
W -> DB: UPDATE status=extracting (10%)

== 3 - Extraction selon le type MIME ==
W -> P: get_provider(mime_type)
P --> W: PdfProvider / DocxProvider / TxtProvider...
W -> P: provider.extract(file_path)
P --> W: ExtractionArtifact (raw_text, structure_json)

== 4 - Normalisation et persistance ==
note over W: Normalisation UTF-8, CRLF->LF, espaces
W -> DB: INSERT extractions (normalized_text, structure)
W -> DB: UPDATE status=extracted (100%)
@enduml""",

"seq_sprint2": f"""@startuml
title Diagramme de sequence — Sprint 2 : Analyser les clauses NLP
{SKIN_SEQ}
participant "Worker\\nCelery" as W
participant "Language\\nDetector" as LD
participant "Clause\\nSegmenter" as CS
participant "Entity\\nExtractor" as EE
participant "Clause\\nClassifier" as CC
participant "PostgreSQL" as DB

note over W: Declenche automatiquement apres extraction reussie

== 1 - Detection de la langue ==
W -> LD: detect(normalized_text)
LD --> W: "fr" / "ar" / "en"

== 2 - Segmentation en clauses ==
W -> CS: segment(text, structure_json)
note right: 3 strategies : structure_json,\\nregex articles, paragraphes
CS --> W: [ClauseSegment x N] (text, start_char, end_char)

== 3 - Boucle sur chaque clause ==
loop Pour chaque clause
  W -> EE: extract_entities(clause)
  EE --> W: [Entity] (PARTY, ROLE, DURATION, LAW_REFERENCE...)
  W -> CC: classify(clause_text)
  CC --> W: {{ labels, compliance_flags, confidence }}
end

== 4 - Persistance ==
W -> DB: INSERT nlp_analyses (clauses_json, entities_json)
W -> DB: UPDATE status=analyzed (100%)
@enduml""",

"seq_sprint3": f"""@startuml
title Diagramme de sequence — Sprint 3 : Evaluer la conformite reglementaire
{SKIN_SEQ}
participant "Worker\\nCelery" as W
participant "Rule\\nEngine" as RE
participant "Compliance\\nScorer" as CS
participant "PostgreSQL" as DB

note over W: Declenche automatiquement apres analyse NLP reussie

== 1 - Chargement des regles ==
W -> RE: load_rules()
note right: 44 regles JSON\\n(LNPDP, GDPR, ISO27001, ISO9001)
RE --> W: rules loaded

== 2 - Determination des referentiels actifs ==
W -> RE: determine_active_frameworks(clauses)
RE --> W: [LNPDP, GDPR, ISO27001]

== 3 - Correspondance regles / clauses ==
W -> RE: evaluate(clauses)
note right: match_rules_to_clauses()\\ndetect_missing_clauses()
RE --> W: violations[] + missing_clauses[]

== 4 - Calcul du score ==
W -> CS: compute_scores(violations, frameworks)
note right: score(F) = 100 - SUM w(severity)\\nglobal = SUM score(F) x weight(F)
CS --> W: {{ global_score, per_framework, litigation_risk }}

== 5 - Persistance ==
W -> DB: INSERT evaluations (global_score, violations_json)
W -> DB: UPDATE status=evaluated (100%)
@enduml""",

"seq_sprint4": f"""@startuml
title Diagramme de sequence — Sprint 4 : Generer des recommandations
{SKIN_SEQ}
participant "Worker\\nCelery" as W
participant "Recommender" as R
participant "Template\\nLibrary" as TL
participant "PostgreSQL" as DB

note over W: Declenche automatiquement apres evaluation reussie

== 1 - Tri des violations ==
W -> R: build_recommendations(violations, clauses)
note right: Tri par severite\\ncritical > high > medium > low

== 2 - Boucle sur chaque violation ==
loop Pour chaque violation
  R -> TL: lookup_template(rule_id)
  TL --> R: template ou None
  alt Template trouve
    R -> R: slot_filling(template, NLP entities)
    note right: {{RETENTION_PERIOD}} -> entite DURATION
    note right: generated_by = "template_v1"
  else Pas de template
    R -> R: fallback_recommendation(violation)
    note right: generated_by = "fallback_v1"
  end
end
R --> W: [Recommendation x N]

== 3 - Persistance ==
W -> DB: DELETE old recommendations (idempotence)
W -> DB: INSERT recommendations (N lignes)
W -> DB: UPDATE status=complete, finished_at=NOW()
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
    print(f"Generating {len(DIAGRAMS)} diagrams via Kroki (PlantUML)...")
    for name, code in DIAGRAMS.items():
        generate(name, code)
    print(f"\nDone! Saved to {OUT}")
