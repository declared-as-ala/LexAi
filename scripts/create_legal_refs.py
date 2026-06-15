"""Create legal reference JSON files for Agent 3 rule engine and Agent 4 RAG."""
import json

# LNPDP - Key articles for Agent 3 rules
lnpdp_refs = {
    "law": "Loi n 2004-63 du 27 juillet 2004 portant sur la protection des donnees a caractere personnel (LNPDP)",
    "authority": "Instance Nationale de Protection des Donnees Personnelles (INPDP)",
    "articles": [
        {
            "article": "Art. 6",
            "title": "Conditions de licéité du traitement",
            "text": "Le traitement des données à caractère personnel nest licite que si la personne concernée a donné son consentement, ou si le traitement est nécessaire à lexécution dun contrat.",
            "compliance_flags": ["missing_consent_mechanism", "lnpdp_relevant"],
            "severity": "critical"
        },
        {
            "article": "Art. 7",
            "title": "Information de la personne concernée",
            "text": "Le responsable du traitement doit informer la personne concernée de lidentité du responsable, de la finalité du traitement, des destinataires des données, et de lexistence dun droit daccès et de rectification.",
            "compliance_flags": ["lnpdp_relevant"],
            "severity": "high"
        },
        {
            "article": "Art. 23",
            "title": "Durée de conservation",
            "text": "Les données à caractère personnel ne peuvent être conservées au-delà de la durée nécessaire à la réalisation des finalités pour lesquelles elles ont été collectées.",
            "compliance_flags": ["missing_retention_period", "lnpdp_relevant", "data_processing"],
            "severity": "high"
        },
        {
            "article": "Art. 46",
            "title": "Transferts internationaux",
            "text": "Le transfert vers un pays étranger de données à caractère personnel ne peut avoir lieu que si ce pays assure un niveau de protection suffisant.",
            "compliance_flags": ["cross_border_transfer", "lnpdp_relevant"],
            "severity": "high"
        },
        {
            "article": "Art. 28",
            "title": "Mesures de sécurité",
            "text": "Le responsable du traitement est tenu de mettre en oeuvre les mesures techniques et organisationnelles appropriées pour protéger les données à caractère personnel.",
            "compliance_flags": ["missing_security_measures", "lnpdp_relevant"],
            "severity": "high"
        }
    ]
}

with open("data/raw/legal_refs/lnpdp/lnpdp_key_articles.json", "w", encoding="utf-8") as f:
    json.dump(lnpdp_refs, f, ensure_ascii=False, indent=2)
print("Saved lnpdp_key_articles.json")

# GDPR - Key articles for Agent 3 rules
gdpr_refs = {
    "law": "Règlement (UE) 2016/679 du Parlement européen et du Conseil (RGPD)",
    "articles": [
        {
            "article": "Art. 5",
            "title": "Principes relatifs au traitement",
            "text": "Les données à caractère personnel doivent être traitées de manière licite, loyale et transparente; collectées pour des finalités déterminées, explicites et légitimes.",
            "compliance_flags": ["missing_retention_period", "gdpr_relevant"],
            "severity": "critical"
        },
        {
            "article": "Art. 6",
            "title": "Licéité du traitement",
            "text": "Le traitement nest licite que si la personne concernée a consenti, ou si le traitement est nécessaire à lexécution dun contrat.",
            "compliance_flags": ["missing_consent_mechanism", "gdpr_relevant"],
            "severity": "critical"
        },
        {
            "article": "Art. 13",
            "title": "Informations à fournir",
            "text": "Lorsque des données sont collectées, le responsable du traitement fournit à la personne concernée son identité, les finalités, la durée de conservation, lexistence des droits daccès et rectification.",
            "compliance_flags": ["gdpr_relevant"],
            "severity": "high"
        },
        {
            "article": "Art. 28",
            "title": "Sous-traitant",
            "text": "Le contrat lie le sous-traitant au responsable et stipule notamment lobjet, la durée, la nature et la finalité du traitement des données à caractère personnel.",
            "compliance_flags": ["data_processing", "gdpr_relevant"],
            "severity": "high"
        },
        {
            "article": "Art. 32",
            "title": "Sécurité du traitement",
            "text": "Le responsable du traitement met en oeuvre les mesures techniques et organisationnelles appropriées afin de garantir un niveau de sécurité adapté au risque.",
            "compliance_flags": ["missing_security_measures", "gdpr_relevant"],
            "severity": "high"
        },
        {
            "article": "Art. 37",
            "title": "Délégué à la protection des données (DPO)",
            "text": "Le responsable désigne un délégué à la protection des données lorsque le traitement à grande échelle de catégories particulières de données est effectué.",
            "compliance_flags": ["missing_dpo", "gdpr_relevant"],
            "severity": "medium"
        }
    ]
}

with open("data/raw/legal_refs/gdpr/gdpr_key_articles.json", "w", encoding="utf-8") as f:
    json.dump(gdpr_refs, f, ensure_ascii=False, indent=2)
print("Saved gdpr_key_articles.json")

# COC - Code des Obligations et Contrats (Tunisia)
coc_refs = {
    "law": "Code des Obligations et Contrats (COC) tunisien",
    "articles": [
        {
            "article": "Art. 27",
            "title": "Conditions de validité du contrat",
            "text": "La convention nest valable que si les parties sont capables de sobliger, si elles ont donné leur consentement et si lobligation a un objet certain et une cause licite.",
            "compliance_flags": ["missing_consent_mechanism"],
            "severity": "critical"
        },
        {
            "article": "Art. 107",
            "title": "Responsabilité contractuelle",
            "text": "Lorsquune partie ne remplit pas ses engagements, lautre partie peut demander lexécution forcée ou la résolution du contrat avec des dommages et intérêts.",
            "compliance_flags": [],
            "severity": "medium"
        },
        {
            "article": "Art. 275",
            "title": "Clause pénale",
            "text": "Les parties peuvent convenir à lavance de la somme que devra payer la partie défaillante à titre de dommages et intérêts pour inexécution.",
            "compliance_flags": [],
            "severity": "low"
        },
        {
            "article": "Art. 318",
            "title": "Résiliation du contrat",
            "text": "La résiliation dun contrat à durée indéterminée peut être demandée sous réserve dun préavis suffisant. La résiliation abusive peut donner lieu à dommages et intérêts.",
            "compliance_flags": [],
            "severity": "medium"
        }
    ]
}

with open("data/raw/legal_refs/coc/coc_key_articles.json", "w", encoding="utf-8") as f:
    json.dump(coc_refs, f, ensure_ascii=False, indent=2)
print("Saved coc_key_articles.json")

print("\nAll legal reference files created.")
