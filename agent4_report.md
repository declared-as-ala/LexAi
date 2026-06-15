# Agent 4 — Recommandateur : Rapport Technique

> **Statut** : Complet (V1 — template-based)
> **Date** : 2026-04-20

---

## 1. Rôle de l'Agent 4

Agent 4 est la dernière étape du pipeline LexAI. Il reçoit les violations détectées par Agent 3 et les clauses analysées par Agent 2, puis produit pour chaque violation :

- Une **description claire du problème** identifié
- Une **recommandation concrète** en français indiquant quoi corriger
- Une **clause de remplacement rédigée** (prête à copier-coller dans le contrat)
- Un **raisonnement juridique** qui cite l'article de loi exact

Les recommandations sont triées par priorité : `critical` en premier, `high`, `medium`, `low`.

---

## 2. Architecture générale

```
Agent 3 output (violations JSON)
Agent 2 output (clauses + entités NLP)
              │
              ▼
     [ build_recommendation_rows() ]
              │
     ┌────────┴────────────┐
     │                     │
Template trouvé ?     Template absent ?
     │                     │
Slot-filling          Fallback générique
(template_v1)         (fallback_v1)
     │                     │
     └────────┬────────────┘
              │
     [ Sauvegarde en base PostgreSQL ]
              │
     Document status → complete (100%)
```

---

## 3. Composants implémentés

### 3.1 Bibliothèque de templates — `recommendations_fr.json`

Fichier JSON unique contenant **24 templates de recommandations** couvrant les violations les plus fréquentes des 4 frameworks :

| Framework | Templates |
|-----------|-----------|
| LNPDP 2004-63 | 10 templates (Art. 3, 5, 7, 14, 22, 23, 24, 28, 36, 40) |
| GDPR EU 2016/679 | 8 templates (Art. 5, 6, 13, 17, 28, 32, 33, 44) |
| ISO 27001:2022 | 4 templates (A.5.1, A.8.2, A.8.10, A.5.23) |
| ISO 9001:2015 | 2 templates (§8.4.1, §8.4.3) |

**Structure d'un template :**

```json
{
  "rule_id": "lnpdp_art23_retention",
  "framework": "LNPDP",
  "article": "Art. 23",
  "issue_description": "La durée de conservation des données personnelles n'est pas précisée.",
  "recommendation_text": "Spécifier une durée de conservation définie et justifiée...",
  "rewritten_clause": "Durée de conservation\n\nLes données à caractère personnel collectées... {RETENTION_PERIOD} ...",
  "legal_rationale": "L'article 23 de la LNPDP impose une durée de conservation limitée.",
  "slots": {
    "RETENTION_PERIOD": { "entity_label": "DURATION", "default": "[durée à préciser]" }
  }
}
```

Chaque template est indexé par `rule_id` — le même identifiant utilisé par le moteur de règles d'Agent 3. La correspondance est donc directe et sans ambiguïté.

---

### 3.2 Moteur de recommandations — `recommender.py`

Fichier central : `backend/app/legal/recommender.py`

#### Chargement des templates

```python
def load_templates_by_rule_id() -> dict[str, dict]:
    raw = json.loads(_TEMPLATES_PATH.read_text(encoding="utf-8"))
    templates = raw.get("templates") or []
    return {str(t["rule_id"]): t for t in templates if t.get("rule_id")}
```

Les templates sont chargés en mémoire au démarrage et indexés par `rule_id` pour un lookup O(1).

#### Slot-filling dynamique

Les slots `{VARIABLE}` dans les templates sont résolus selon cette priorité :

1. **Entité NLP extraite par Agent 2** : si le slot définit un `entity_label` (ex: `"DURATION"`), Agent 4 cherche dans les entités de la clause concernée l'entité avec ce label et la plus haute confiance
2. **Valeur par défaut** (`default`) : si aucune entité trouvée, utilise le texte de fallback du template (ex: `"[durée à préciser]"`)

```python
def _first_entity_by_label(clause, label):
    # Parcourt clause["entities"], filtre par label, retourne l'entité
    # avec la confidence la plus haute
    best = None
    for ent in clause.get("entities") or []:
        if ent.get("label") != label:
            continue
        conf = float(ent.get("confidence") or 0.0)
        if best is None or conf > best[0]:
            best = (conf, ent["text"])
    return best[1] if best else None
```

**Exemple concret :**

Violation : `lnpdp_art23_retention` sur une clause contenant l'entité `{text: "3 ans", label: "DURATION", confidence: 0.94}`

Slot `{RETENTION_PERIOD}` → Agent 4 trouve `"3 ans"` via NER → la clause réécrite contient `"3 ans"` au lieu de `"[durée à préciser]"`

#### Fallback pour violations sans template

Si une violation a un `rule_id` pour lequel aucun template n'existe :

```python
def _fallback_recommendation(violation):
    return {
        "recommendation_text": f"Mettre à jour la clause ({framework} {article}). Indication : {hint}",
        "rewritten_clause": f"[Proposition indicative]\n{clause_text}\n— Ajouts : {hint}",
        "legal_rationale": f"Référence : {framework} {article}",
        "generated_by": "fallback_v1",
    }
```

Le champ `generated_by` permet de distinguer en base et en API si la recommandation vient d'un template (`template_v1`) ou du fallback (`fallback_v1`).

#### Tri par sévérité

Les violations sont triées avant traitement : `critical → high → medium → low`. Le champ `priority` (1, 2, 3…) dans la table reflète cet ordre — Agent 4 présente toujours les problèmes les plus graves en premier.

---

### 3.3 Tâche Celery — `tasks/recommendation.py`

Agent 4 s'exécute en arrière-plan via Celery, exactement comme les agents précédents.

**Déclenchement automatique** : à la fin de la tâche Agent 3, si l'évaluation réussit, Agent 3 appelle directement :

```python
from app.tasks.recommendation import enqueue_recommendation
enqueue_recommendation(document_id)
```

**Cycle de statut du document pendant Agent 4 :**

```
STATUS_RECOMMENDING (0%)  → "Generating recommendations…"
STAGE_REC_TEMPLATES (40%) → "Applying recommendation templates…"
STAGE_REC_PERSISTING (85%)→ "Saving recommendations…"
STATUS_COMPLETE (100%)    → "Pipeline complete — N recommendation(s) generated"
```

C'est le seul agent qui passe le document à `STATUS_COMPLETE` et écrit `finished_at` — il marque la fin du pipeline entier.

**Idempotence** : avant d'insérer de nouvelles recommandations, la tâche supprime celles déjà existantes pour le document :

```python
db.query(Recommendation).filter(Recommendation.document_id == document_id).delete()
```

Un re-trigger (`POST /documents/{id}/recommend`) repart donc proprement de zéro.

---

### 3.4 Modèle de base de données — `db/models/recommendation.py`

Table `recommendations` dans PostgreSQL :

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | Integer PK | Identifiant interne |
| `document_id` | FK → documents | Document parent |
| `violation_id` | String | ID de la violation Agent 3 source |
| `clause_id` | String | ID de la clause Agent 2 concernée |
| `violation_rule_id` | String | `rule_id` de la règle qui a déclenché la violation |
| `framework` | String | LNPDP / GDPR / ISO27001 / ISO9001 |
| `article` | String | Référence légale exacte (ex: "Art. 23") |
| `severity` | String | critical / high / medium / low |
| `priority` | Integer | Ordre d'affichage (1 = plus urgent) |
| `issue_description` | Text | Description du problème |
| `recommendation_text` | Text | Que faire concrètement |
| `rewritten_clause` | Text | Clause de remplacement complète |
| `legal_rationale` | Text | Justification juridique |
| `generated_by` | String | `template_v1` ou `fallback_v1` |
| `created_at` | DateTime | Timestamp de génération |

---

### 3.5 API REST — `api/routes/recommendation.py`

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/documents/{id}/recommendations` | Liste toutes les recommandations triées par priorité |
| `POST` | `/documents/{id}/recommend` | Déclenche (ou re-déclenche) manuellement Agent 4 |

Le `POST` accepte uniquement les documents en statut `evaluated` ou `complete` — pas question de générer des recommandations sans évaluation Agent 3.

**Schéma de réponse `GET` :**

```json
{
  "document_id": 42,
  "total": 3,
  "recommendations": [
    {
      "id": 1,
      "priority": 1,
      "framework": "LNPDP",
      "article": "Art. 23",
      "severity": "high",
      "clause_id": "c-003",
      "violation_id": "v-001",
      "violation_rule_id": "lnpdp_art23_retention",
      "issue_description": "La durée de conservation des données personnelles n'est pas précisée.",
      "recommendation_text": "Spécifier une durée de conservation...",
      "rewritten_clause": "Durée de conservation\n\nLes données... pendant une durée de 3 ans...",
      "legal_rationale": "L'article 23 de la LNPDP impose...",
      "generated_by": "template_v1",
      "created_at": "2026-04-20T10:32:00Z"
    }
  ]
}
```

---

## 4. Flux de données complet Agent 2 → 3 → 4

```
Agent 2 produit pour chaque clause :
{
  "clause_id": "c-003",
  "text": "Les données seront conservées...",
  "labels": ["data_retention", "data_processing"],
  "entities": [{"text": "3 ans", "label": "DURATION", "confidence": 0.94}],
  "flags": ["missing_retention_period"]
}

Agent 3 détecte la violation :
{
  "violation_id": "v-001",
  "rule_id": "lnpdp_art23_retention",
  "clause_id": "c-003",
  "framework": "LNPDP",
  "article": "Art. 23",
  "severity": "high",
  "remediation_hint": "Préciser une durée maximale de conservation."
}

Agent 4 produit la recommandation :
- Lookup : templates["lnpdp_art23_retention"] → template trouvé
- Slot {RETENTION_PERIOD} → entité DURATION "3 ans" trouvée dans c-003
- rewritten_clause : "...pendant une durée de 3 ans à compter de..."
- generated_by : "template_v1"
```

---

## 5. Ce qu'Agent 4 ne fait PAS (limites V1)

| Limite | Impact | Solution V2 |
|--------|--------|-------------|
| Pas de LLM | Clauses réécrites génériques, pas contextualisées au secteur | Mistral 7B ou Claude API |
| Templates couvrent 24/44 règles | Violations sans template → fallback générique | Compléter les 20 templates manquants |
| Pas de fusion de violations | Si 2 violations touchent la même clause → 2 recommandations séparées | LLM pour fusionner en une seule clause cohérente |
| Langue fixe (français) | Pas de recommandations en arabe | XLM-RoBERTa + templates arabes |
| Pas de validation humaine | Les clauses réécrites ne sont pas relues par un juriste | Interface Human-in-the-Loop |

---

## 6. Inventaire des fichiers Agent 4

```
backend/
├── app/
│   ├── legal/
│   │   ├── recommender.py                    # Moteur de slot-filling et fallback
│   │   └── templates/
│   │       └── recommendations_fr.json        # 24 templates de recommandations
│   ├── tasks/
│   │   └── recommendation.py                 # Tâche Celery Agent 4
│   ├── db/models/
│   │   └── recommendation.py                 # ORM SQLAlchemy table recommendations
│   ├── schemas/
│   │   └── recommendation.py                 # Pydantic schemas API
│   └── api/routes/
│       └── recommendation.py                 # Endpoints REST
```

---

## 7. Évolution V2 — Intégration LLM

L'architecture actuelle est conçue pour accueillir un LLM sans tout réécrire. Le plan :

```python
# Dans build_recommendation_rows(), après le slot-filling :
if USE_LLM and generated_by == "template_v1":
    rewritten_clause = llm_enrich(
        template_clause=rewritten_clause,
        contract_context=clause["text"],
        violation=violation,
        entities=clause["entities"],
    )
    generated_by = "llm_v2"
```

**Modèle recommandé** : `claude-haiku-4-5` via l'API Anthropic (rapide, < 1s, sans GPU local) ou Mistral 7B via Ollama pour un déploiement 100% local sans dépendance cloud.

Le champ `generated_by` en base (`template_v1` vs `llm_v2`) permettra de mesurer l'impact du LLM sur la satisfaction des utilisateurs sans casser la V1.
