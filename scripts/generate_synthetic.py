"""
Generate synthetic French clause examples from our legal reference texts.

Sources:
  data/raw/legal_refs/lnpdp/lnpdp_key_articles.json
  data/raw/legal_refs/gdpr/gdpr_key_articles.json
  data/raw/legal_refs/coc/coc_key_articles.json

Strategy:
  Each legal article describes a requirement. We write multiple contract clause
  templates per article — both compliant and non-compliant variants —
  with slot-fill placeholders replaced by realistic values.

Output: data/raw/datasets/synthetic_fr/synthetic_clauses.json
        data/raw/datasets/synthetic_fr/synthetic_ner.json

Usage: python scripts/generate_synthetic.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

DATA_DIR  = Path(__file__).parent.parent / "data"
REFS_DIR  = DATA_DIR / "raw" / "legal_refs"
OUT_DIR   = DATA_DIR / "raw" / "datasets" / "synthetic_fr"

random.seed(42)

# ── Slot-fill values ─────────────────────────────────────────────────────────

COMPANY_NAMES = [
    "Tunisie Télécom", "BIAT", "Poulina Group", "Délice Holding",
    "Amen Bank", "Steg", "Orange Tunisie", "Ooredoo Tunisie",
    "Banque de l'Habitat", "STB", "Attijari Bank", "UIB",
]
ROLES = ["le Prestataire", "le Client", "le Fournisseur", "le Cocontractant"]
DURATIONS = ["1 an", "2 ans", "3 ans", "5 ans", "6 mois", "12 mois", "36 mois"]
DATES = ["01/01/2025", "31/12/2025", "30/06/2026", "01/03/2025"]
AMOUNTS = ["5 000 TND", "10 000 TND", "50 000 TND", "100 000 EUR", "500 000 TND"]
COURTS = [
    "le Tribunal de Première Instance de Tunis",
    "le Tribunal de Commerce de Tunis",
    "la Cour d'Appel de Tunis",
]
ARBITRATION_CENTERS = [
    "le Centre d'Arbitrage et de Médiation de Tunis (CAMT)",
    "la Cour Internationale d'Arbitrage de la CCI",
]

def _pick(*options):
    return random.choice(options)


# ── Template definitions ─────────────────────────────────────────────────────
# Each entry: (label, compliance_flags, [template strings])
# Templates may contain {COMPANY}, {ROLE}, {DURATION}, {DATE}, {AMOUNT}, {COURT}

TEMPLATES: list[tuple[str, list[str], list[str]]] = [

    # ── data_processing ───────────────────────────────────────────────────────
    ("data_processing", ["lnpdp_relevant", "missing_retention_period"], [
        "{COMPANY} collecte et traite les données à caractère personnel des utilisateurs dans le cadre de l'exécution du présent contrat. Le traitement est effectué conformément à la loi n°2004-63.",
        "Le responsable du traitement s'engage à ne collecter que les données strictement nécessaires à la finalité décrite aux présentes. Toute collecte excessive est proscrite.",
        "{ROLE} traite les données personnelles des personnes concernées pour les finalités suivantes : gestion de la relation client, facturation et recouvrement.",
        "Les données à caractère personnel collectées dans le cadre du présent accord incluent : nom, prénom, adresse email, numéro de téléphone et données de connexion.",
        "Le sous-traitant traite les données personnelles uniquement sur instruction documentée du responsable du traitement, conformément à l'article 28 du RGPD.",
    ]),

    ("data_processing", ["lnpdp_relevant", "missing_consent_mechanism"], [
        "{COMPANY} collecte des données personnelles sans préciser la base légale applicable au traitement. Les finalités du traitement ne sont pas clairement définies.",
        "Le traitement des données est effectué par {ROLE} à des fins commerciales. Aucune mention du consentement ou de la nécessité contractuelle n'est précisée.",
        "Les données à caractère personnel sont transmises à des tiers partenaires sans indication du fondement juridique de ce partage.",
    ]),

    ("data_processing", ["lnpdp_relevant", "missing_security_measures"], [
        "{COMPANY} collecte les données personnelles des clients dans le cadre de la gestion des commandes. Aucune mesure de sécurité technique n'est mentionnée.",
        "Le responsable du traitement conserve les données sur ses serveurs internes sans décrire les mesures de protection mises en place.",
        "Les données sont partagées par voie électronique entre {ROLE} et ses sous-traitants. Le contrat ne prévoit pas de protocole de sécurité spécifique.",
    ]),

    ("data_processing", ["lnpdp_relevant", "gdpr_relevant"], [
        "Le responsable du traitement s'engage à mettre en œuvre les mesures techniques et organisationnelles appropriées pour protéger les données à caractère personnel, conformément à l'article 28 de la loi n°2004-63 (LNPDP) et à l'article 32 du RGPD.",
        "Les données personnelles collectées seront conservées pendant une durée de {DURATION} à compter de la fin du contrat, conformément aux exigences de l'Art. 23 LNPDP.",
        "Le présent contrat de traitement de données est conclu entre {COMPANY} (responsable du traitement) et {ROLE} (sous-traitant), conformément à l'Art. 28 RGPD et à l'Art. 23 LNPDP.",
    ]),

    ("data_processing", ["gdpr_relevant", "missing_dpo_reference"], [
        "{COMPANY} effectue un traitement à grande échelle de données de santé sans désigner de délégué à la protection des données (DPO), en violation de l'article 37 du RGPD.",
        "Le responsable du traitement n'a pas désigné de DPO alors que le traitement porte sur des données sensibles au sens de l'article 37 du Règlement européen.",
        "Aucun délégué à la protection des données n'est mentionné dans le présent accord malgré le traitement massif de données personnelles par {COMPANY}.",
        "{COMPANY} traite des données biométriques sans avoir désigné de DPO, ce qui constitue une violation de l'obligation prévue à l'article 37 du RGPD.",
    ]),

    ("data_processing", ["lnpdp_relevant", "unlawful_cross_border_transfer"], [
        "{COMPANY} transfère les données personnelles vers un serveur hébergé hors de Tunisie sans s'assurer que le pays destinataire offre un niveau de protection adéquat, conformément à l'Art. 46 LNPDP.",
        "Les données à caractère personnel sont transférées vers un pays tiers sans clause contractuelle type ni décision d'adéquation, ce qui constitue un transfert transfrontalier non sécurisé.",
        "Le sous-traitant est autorisé à héberger les données hors de Tunisie uniquement dans les pays figurant sur la liste d'adéquation de l'INPDP.",
        "Tout transfert de données personnelles vers un État non membre de la liste d'adéquation de l'INPDP est formellement interdit sans autorisation préalable.",
        "Les données à caractère personnel ne peuvent être transférées hors de Tunisie qu'après notification préalable à l'INPDP, conformément à la loi n°2004-63.",
    ]),

    ("data_processing", ["lnpdp_relevant", "missing_data_subject_rights"], [
        "Le présent contrat ne mentionne pas les droits des personnes concernées (accès, rectification, suppression) prévus par la loi n°2004-63 (LNPDP).",
        "{COMPANY} collecte et traite les données personnelles des clients sans prévoir de mécanisme permettant aux personnes concernées d'exercer leurs droits.",
        "Aucune procédure de réponse aux demandes d'exercice des droits des personnes concernées n'est définie dans le présent accord.",
        "Le contrat ne prévoit pas de délai de réponse aux demandes de suppression ou de portabilité des données adressées à {COMPANY}.",
    ]),

    ("data_processing", ["lnpdp_relevant", "missing_retention_period", "gdpr_relevant"], [
        "Le présent accord de traitement de données entre {COMPANY} et {ROLE} ne précise pas la durée de conservation des données personnelles collectées.",
        "Les données à caractère personnel seront traitées par {COMPANY} sans limitation de durée, en violation de l'article 23 de la loi n°2004-63.",
        "Conformément au principe de limitation de la conservation, {COMPANY} s'engage à définir et à respecter des durées de conservation pour chaque catégorie de données traitées.",
        "Le contrat omet de préciser la durée de conservation des données collectées, ce qui est contraire aux exigences de l'Art. 5 RGPD et de l'Art. 23 LNPDP.",
    ]),

    # ── confidentiality ───────────────────────────────────────────────────────
    ("confidentiality", [], [
        "Les parties s'engagent à maintenir strictement confidentielles toutes les informations échangées dans le cadre du présent contrat et à ne pas les divulguer à des tiers sans autorisation préalable écrite.",
        "Toute information désignée comme confidentielle par l'une des parties ne pourra être divulguée, communiquée ou utilisée par l'autre partie à d'autres fins que l'exécution du présent contrat.",
        "{COMPANY} s'engage à ne pas divulguer les informations confidentielles reçues de {ROLE} pendant une durée de {DURATION} après la résiliation du présent accord.",
        "Les informations confidentielles comprennent notamment les données techniques, financières, commerciales et stratégiques échangées entre les parties.",
        "L'obligation de confidentialité s'étend à l'ensemble des employés, sous-traitants et mandataires des parties ayant accès aux informations confidentielles.",
        "En cas de violation de la clause de confidentialité, la partie lésée peut réclamer des dommages et intérêts conformément aux dispositions du Code des Obligations et Contrats tunisien.",
    ]),

    # ── termination ───────────────────────────────────────────────────────────
    ("termination", [], [
        "Le présent contrat est conclu pour une durée de {DURATION} à compter de la date de signature. À l'expiration de cette période, il sera renouvelé tacitement pour des périodes successives d'un an, sauf dénonciation par l'une des parties avec un préavis de 3 mois.",
        "Chacune des parties peut résilier le présent contrat en cas de manquement grave de l'autre partie à ses obligations, après mise en demeure restée sans effet pendant 30 jours.",
        "Le contrat prendra fin de plein droit le {DATE} sans qu'il soit nécessaire d'accomplir aucune formalité judiciaire.",
        "{COMPANY} peut résilier le présent contrat à tout moment, moyennant un préavis de 90 jours notifié par lettre recommandée avec accusé de réception.",
        "En cas de résiliation anticipée du fait de {ROLE}, ce dernier devra s'acquitter d'une indemnité de résiliation équivalente à 3 mois de prestation.",
        "Conformément à l'article 318 du COC, la résiliation d'un contrat à durée indéterminée peut être demandée sous réserve d'un préavis suffisant.",
    ]),

    # ── liability ─────────────────────────────────────────────────────────────
    ("liability", [], [
        "La responsabilité de {COMPANY} au titre du présent contrat est limitée au montant des sommes effectivement versées par {ROLE} au cours des 12 derniers mois précédant la survenance du préjudice.",
        "En aucun cas {COMPANY} ne pourra être tenue responsable des dommages indirects, pertes d'exploitation ou manque à gagner subis par {ROLE}.",
        "Chaque partie reste responsable des dommages directs causés par sa faute ou négligence dans l'exécution du présent contrat.",
        "La responsabilité totale de {ROLE} ne pourra excéder {AMOUNT} par sinistre et par année contractuelle.",
        "Conformément à l'article 107 du COC, en cas d'inexécution, la partie lésée peut demander l'exécution forcée ou la résolution du contrat avec dommages et intérêts.",
    ]),

    # ── dispute_resolution ────────────────────────────────────────────────────
    ("dispute_resolution", [], [
        "Tout litige relatif à l'interprétation ou à l'exécution du présent contrat sera soumis à la compétence exclusive de {COURT}.",
        "En cas de différend, les parties s'engagent à tenter de résoudre leur litige à l'amiable dans un délai de 30 jours avant tout recours judiciaire.",
        "Le présent contrat est régi par le droit tunisien. Tout litige sera soumis à {ARBITRATION_CENTER}.",
        "Les parties conviennent de soumettre tout litige né du présent accord à un arbitrage conformément au règlement de {ARBITRATION_CENTER}.",
        "Le droit applicable au présent contrat est le droit tunisien. Les juridictions tunisiennes sont seules compétentes.",
    ]),

    # ── payment ───────────────────────────────────────────────────────────────
    ("payment", [], [
        "En contrepartie des prestations rendues, {ROLE} s'engage à verser à {COMPANY} la somme de {AMOUNT} HT par mois, payable à terme échu, dans un délai de 30 jours à compter de la réception de la facture.",
        "Les prix sont révisables annuellement selon l'indice des prix à la consommation publié par l'Institut National de la Statistique tunisien.",
        "Tout retard de paiement donnera lieu à l'application d'intérêts de retard au taux légal en vigueur en Tunisie, majoré de 2 points.",
        "La rémunération forfaitaire convenue entre les parties est fixée à {AMOUNT} pour la durée totale du contrat.",
        "Les factures impayées au-delà de 60 jours entraîneront la suspension automatique des prestations, sans préjudice des autres recours.",
    ]),

    # ── obligation ────────────────────────────────────────────────────────────
    ("obligation", [], [
        "{COMPANY} s'engage à exécuter les prestations définies à l'annexe technique dans les délais convenus et selon les spécifications contractuelles.",
        "{ROLE} devra fournir à {COMPANY} l'ensemble des informations, accès et ressources nécessaires à la bonne exécution des prestations.",
        "Les parties s'obligent mutuellement à respecter les dispositions légales et réglementaires applicables à leur activité respective.",
        "{COMPANY} est tenu de maintenir une équipe dédiée au projet composée d'au moins 3 consultants pendant toute la durée du contrat.",
        "Chaque partie désignera un interlocuteur référent qui sera responsable de la coordination et du suivi de l'exécution du contrat.",
        "{ROLE} s'interdit de faire appel, directement ou indirectement, aux collaborateurs de {COMPANY} pendant la durée du contrat et dans les 12 mois suivant son terme.",
    ]),

    # ── force_majeure ─────────────────────────────────────────────────────────
    ("force_majeure", [], [
        "Aucune des parties, ni {COMPANY} ni {ROLE}, ne pourra être tenue responsable de l'inexécution de ses obligations lorsque celle-ci résulte d'un cas de force majeure tel que défini par la jurisprudence tunisienne.",
        "Constituent des cas de force majeure au sens du présent accord entre {COMPANY} et {ROLE} : catastrophes naturelles, grèves générales, actes terroristes ou décisions gouvernementales.",
        "La partie invoquant un cas de force majeure, qu'il s'agisse de {COMPANY} ou de {ROLE}, devra en notifier l'autre partie par écrit dans un délai de 5 jours ouvrables.",
        "Si la force majeure persiste au-delà de {DURATION}, {COMPANY} ou {ROLE} aura le droit de résilier le contrat sans indemnité.",
        "En cas de survenance d'un événement de force majeure affectant {COMPANY}, les obligations de {ROLE} sont également suspendues de plein droit pendant toute la durée dudit événement.",
        "La partie affectée par un cas de force majeure, qu'il s'agisse de {COMPANY} ou de {ROLE}, devra prendre toutes les mesures raisonnables pour limiter les effets de l'événement.",
        "Les événements reconnus comme cas de force majeure dans le contrat entre {COMPANY} et {ROLE} incluent : pandémies, catastrophes naturelles, guerre, émeutes et cyberattaques d'État.",
        "En cas de force majeure, {COMPANY} sera dispensé d'exécuter ses obligations pour la durée de l'empêchement, sans que cela puisse donner lieu à indemnisation de {ROLE}.",
        "Le cas de force majeure suspend l'exécution du contrat entre {COMPANY} et {ROLE} mais ne libère pas définitivement les parties ; les obligations reprennent dès la cessation de l'événement.",
        "Conformément à l'article 283 du COC, la force majeure exonère {COMPANY} de toute responsabilité envers {ROLE} dès lors que l'événement est imprévisible et irrésistible.",
        "Toute décision administrative ou réglementaire imposant l'arrêt des activités de {COMPANY} sera considérée comme un événement de force majeure au sens du contrat avec {ROLE}.",
        "Les grèves nationales, les crises sanitaires et les catastrophes climatiques constituent des événements de force majeure libérant {ROLE} de ses obligations envers {COMPANY}.",
        "En cas de force majeure d'une durée supérieure à {DURATION}, {COMPANY} et {ROLE} se réuniront afin de négocier de bonne foi une adaptation ou une résiliation amiable du contrat.",
        "La partie invoquant la force majeure, que ce soit {COMPANY} ou {ROLE}, est tenue de fournir toute preuve documentée de l'événement allégué dans un délai raisonnable.",
        "Les perturbations majeures des réseaux de communication affectant {COMPANY} sont assimilées à des cas de force majeure libérant {ROLE} de toute pénalité de retard.",
        "Ni {COMPANY} ni {ROLE} ne pourront être tenus pour responsables des retards ou défaillances d'exécution causés par des circonstances indépendantes de leur volonté.",
        "En cas de force majeure prolongée au-delà de {DURATION}, {COMPANY} s'engage à désigner un interlocuteur dédié pour coordonner avec {ROLE} les mesures de continuité d'activité.",
        "Le déclenchement d'un état d'exception par les autorités tunisiennes constitue un cas de force majeure au titre du présent contrat entre {COMPANY} et {ROLE}.",
        "La survenance d'une catastrophe naturelle affectant les infrastructures de {COMPANY} suspend de plein droit les délais contractuels convenus avec {ROLE} pour une durée équivalente.",
        "Le contrat entre {COMPANY} et {ROLE} prévoit expressément que la pandémie ou une épidémie déclarée par l'OMS constitue un événement de force majeure de plein droit.",
        "En cas de force majeure, {ROLE} disposera d'un délai de {DURATION} supplémentaire pour l'exécution de ses obligations contractuelles envers {COMPANY}.",
        "La clause de force majeure du présent accord entre {COMPANY} et {ROLE} s'applique en cas d'embargo, de blocus commercial ou de sanctions économiques internationales.",
        "Lorsque {COMPANY} est empêché d'exécuter ses prestations en raison d'une force majeure, {ROLE} est dispensé de toute obligation de paiement pour la période d'inexécution.",
        "Les événements de force majeure notifiés par {COMPANY} à {ROLE} dans les délais prévus ne donneront lieu ni à pénalités ni à indemnités entre les parties.",
        "En cas de force majeure, {COMPANY} reprendra l'exécution de ses obligations dans un délai raisonnable après la cessation de l'événement, sans pénalité envers {ROLE}.",
    ]),

    # ── ip_rights ─────────────────────────────────────────────────────────────
    ("ip_rights", [], [
        "Tous les droits de propriété intellectuelle afférents aux livrables produits dans le cadre du présent contrat sont cédés à titre exclusif à {COMPANY} dès leur création.",
        "{ROLE} concède à {COMPANY} une licence d'utilisation non exclusive, non transférable et limitée au territoire tunisien sur les logiciels fournis dans le cadre du présent accord.",
        "Les créations réalisées par {COMPANY} dans le cadre de la mission restent sa propriété exclusive. {ROLE} bénéficie d'une licence d'utilisation pour les besoins internes de sa société.",
        "Chaque partie conserve la propriété de ses droits préexistants. Les développements spécifiques réalisés pour {ROLE} lui sont cédés à titre exclusif.",
    ]),

    # ── penalty ───────────────────────────────────────────────────────────────
    ("penalty", [], [
        "En cas de retard dans la livraison, {COMPANY} devra s'acquitter d'une pénalité de retard de 0,5 % du montant mensuel par jour ouvrable de retard, dans la limite de 10 % du montant total du contrat.",
        "Conformément à l'article 275 du COC, les parties conviennent que le montant des dommages et intérêts en cas d'inexécution s'élève à {AMOUNT}.",
        "Toute violation de la clause de non-concurrence donnera lieu au paiement d'une indemnité forfaitaire de {AMOUNT} à la partie lésée.",
        "Les pénalités contractuelles sont plafonnées à 15 % du montant total du contrat et constituent une réparation forfaitaire exclusive de tout autre recours.",
    ]),

    # ── warranty ──────────────────────────────────────────────────────────────
    ("warranty", [], [
        "{COMPANY} garantit que les prestations fournies seront exécutées conformément aux règles de l'art et aux spécifications techniques définies à l'annexe.",
        "La garantie de bon fonctionnement couvre une période de {DURATION} à compter de la réception définitive des travaux.",
        "{ROLE} garantit qu'il dispose de tous les droits et autorisations nécessaires pour conclure le présent contrat et exécuter les obligations qui en découlent.",
        "En cas de non-conformité constatée pendant la période de garantie, {COMPANY} s'engage à effectuer les corrections nécessaires dans un délai de 10 jours ouvrables.",
    ]),

    # ── definition ────────────────────────────────────────────────────────────
    ("definition", [], [
        "Au sens du présent contrat, on entend par « Données Personnelles » toute information relative à une personne physique identifiée ou identifiable, au sens de la loi n°2004-63.",
        "Les termes « Prestation », « Livrable » et « Délai » utilisés dans le présent accord s'entendent conformément aux définitions figurant à l'annexe A.",
        "Le terme « Partie » désigne indistinctement {COMPANY} ou {ROLE} selon le contexte ; le terme « Parties » désigne les deux cocontractants.",
        "Par « Informations Confidentielles », on entend l'ensemble des données techniques, commerciales, financières et stratégiques échangées entre les parties.",
        "Le mot « Jour Ouvrable » désigne tout jour du lundi au vendredi, à l'exclusion des jours fériés légaux en Tunisie.",
    ]),
]

# ── NER annotation templates ─────────────────────────────────────────────────
# Each entry: sentence template + entity spans description
# Format: (text, [(label, start_keyword)])
# We'll locate entities by searching the filled text.

NER_TEMPLATES: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "Le responsable du traitement, {COMPANY}, s'engage à informer la personne concernée.",
        [("ROLE", "responsable du traitement"), ("PARTY", "{COMPANY}")]
    ),
    (
        "Le sous-traitant {COMPANY} traite les données personnelles sur instruction de {ROLE}.",
        [("ROLE", "sous-traitant"), ("PARTY", "{COMPANY}"), ("DATA_CATEGORY", "données personnelles"), ("PARTY", "{ROLE}")]
    ),
    (
        "Les données à caractère personnel seront conservées pendant {DURATION} conformément à l'Art. 23 LNPDP.",
        [("DATA_CATEGORY", "données à caractère personnel"), ("DURATION", "{DURATION}"), ("LAW_REFERENCE", "Art. 23 LNPDP")]
    ),
    (
        "{COMPANY} s'engage à respecter les dispositions du RGPD et de la loi n°2004-63 (LNPDP).",
        [("PARTY", "{COMPANY}"), ("LAW_REFERENCE", "RGPD"), ("LAW_REFERENCE", "loi n°2004-63"), ("LAW_REFERENCE", "LNPDP")]
    ),
    (
        "Le délégué à la protection des données (DPO) désigné par {COMPANY} est joignable à l'adresse suivante.",
        [("ROLE", "délégué à la protection des données"), ("ROLE", "DPO"), ("PARTY", "{COMPANY}")]
    ),
    (
        "Tout litige sera soumis au {COURT}, conformément au droit tunisien.",
        [("JURISDICTION", "{COURT}"), ("LAW_REFERENCE", "droit tunisien")]
    ),
    (
        "La rémunération mensuelle s'élève à {AMOUNT}, payable dans un délai de 30 jours.",
        [("AMOUNT", "{AMOUNT}"), ("DURATION", "30 jours")]
    ),
    (
        "Le contrat entre {COMPANY} et {ROLE} prend effet le {DATE} pour une durée de {DURATION}.",
        [("PARTY", "{COMPANY}"), ("PARTY", "{ROLE}"), ("DATE", "{DATE}"), ("DURATION", "{DURATION}")]
    ),
    (
        "Les données sensibles de la personne concernée sont hébergées hors de Tunisie, en violation de l'Art. 46 LNPDP.",
        [("DATA_CATEGORY", "données sensibles"), ("JURISDICTION", "Tunisie"), ("LAW_REFERENCE", "Art. 46 LNPDP")]
    ),
    (
        "{COMPANY} cède à {ROLE} tous les droits de propriété intellectuelle sur les livrables produits dans le cadre de ce contrat.",
        [("PARTY", "{COMPANY}"), ("PARTY", "{ROLE}")]
    ),
    (
        "En cas de manquement grave, le contrat pourra être résilié avec un préavis de {DURATION}, conformément à l'article 318 du COC.",
        [("DURATION", "{DURATION}"), ("LAW_REFERENCE", "article 318 du COC")]
    ),
    (
        "La personne concernée dispose d'un droit d'accès, de rectification et de suppression de ses données personnelles.",
        [("ROLE", "personne concernée"), ("DATA_CATEGORY", "données personnelles")]
    ),
    (
        "Les données bancaires et données de santé collectées par {COMPANY} sont soumises à des mesures de sécurité renforcées.",
        [("DATA_CATEGORY", "données bancaires"), ("DATA_CATEGORY", "données de santé"), ("PARTY", "{COMPANY}")]
    ),
    (
        "Le présent accord est régi par le droit tunisien ; tout différend sera porté devant {COURT}.",
        [("LAW_REFERENCE", "droit tunisien"), ("JURISDICTION", "{COURT}")]
    ),
    (
        "Le paiement de {AMOUNT} devra intervenir au plus tard le {DATE}.",
        [("AMOUNT", "{AMOUNT}"), ("DATE", "{DATE}")]
    ),
]


def _fill_slots(template: str) -> str:
    """Replace {SLOT} placeholders with random values."""
    return (
        template
        .replace("{COMPANY}", _pick(*COMPANY_NAMES))
        .replace("{ROLE}", _pick(*ROLES))
        .replace("{DURATION}", _pick(*DURATIONS))
        .replace("{DATE}", _pick(*DATES))
        .replace("{AMOUNT}", _pick(*AMOUNTS))
        .replace("{COURT}", _pick(*COURTS))
        .replace("{ARBITRATION_CENTER}", _pick(*ARBITRATION_CENTERS))
    )


def generate_clause_examples(n_per_template: int = 5) -> list[dict]:
    """Generate n_per_template filled variants per template."""
    records = []
    for label, flags, templates in TEMPLATES:
        for template in templates:
            for _ in range(n_per_template):
                text = _fill_slots(template)
                records.append({
                    "text": text,
                    "labels": [label],
                    "compliance_flags": flags,
                    "language": "fr",
                    "source": "synthetic",
                })
    return records


def generate_ner_examples(n_per_template: int = 8) -> list[dict]:
    """Generate NER-annotated examples with entity spans."""
    records = []
    for template, entity_specs in NER_TEMPLATES:
        for _ in range(n_per_template):
            text = _fill_slots(template)
            entities = []
            for label, keyword_template in entity_specs:
                # The keyword may itself have been a slot — fill it too
                keyword = _fill_slots(keyword_template)
                start = text.find(keyword)
                if start == -1:
                    continue
                entities.append({
                    "text": keyword,
                    "label": label,
                    "start": start,
                    "end": start + len(keyword),
                })
            if entities:
                records.append({
                    "text": text,
                    "entities": entities,
                    "language": "fr",
                    "source": "synthetic",
                })
    return records


def generate_from_legal_refs() -> list[dict]:
    """
    Turn each legal article text into a clause example.
    The article text describes what a compliant clause SHOULD contain,
    so we label it as data_processing with the article's compliance_flags.
    """
    records = []
    for ref_file in REFS_DIR.glob("**/*.json"):
        data = json.loads(ref_file.read_text(encoding="utf-8"))
        articles = data.get("articles", [])
        for article in articles:
            text = article.get("text", "").strip()
            flags = article.get("compliance_flags", [])
            if not text or len(text) < 40:
                continue
            # Determine label from flags
            label = "data_processing" if any("data" in f or "lnpdp" in f or "gdpr" in f for f in flags) else "obligation"
            records.append({
                "text": text,
                "labels": [label],
                "compliance_flags": [f for f in flags if f in [
                    "lnpdp_relevant", "gdpr_relevant", "missing_retention_period",
                    "missing_consent_mechanism", "missing_security_measures",
                    "unlawful_cross_border_transfer", "missing_data_subject_rights",
                ]],
                "language": "fr",
                "source": "legal_refs",
            })
    return records


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Clause classification examples
    clause_records = generate_clause_examples(n_per_template=12)
    clause_records += generate_from_legal_refs()

    from collections import Counter
    label_counts: Counter = Counter()
    for r in clause_records:
        for lbl in r["labels"]:
            label_counts[lbl] += 1

    out_clauses = OUT_DIR / "synthetic_clauses.json"
    out_clauses.write_text(json.dumps(clause_records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Synthetic clause examples: {len(clause_records)} -> {out_clauses}")
    print("Label distribution:")
    for label, count in label_counts.most_common():
        print(f"  {label}: {count}")

    # NER examples
    ner_records = generate_ner_examples(n_per_template=10)
    out_ner = OUT_DIR / "synthetic_ner.json"
    out_ner.write_text(json.dumps(ner_records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSynthetic NER examples: {len(ner_records)} -> {out_ner}")


if __name__ == "__main__":
    main()
