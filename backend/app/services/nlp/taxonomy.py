"""
Taxonomy Registry for Agent 2.
Defines all valid clause labels, compliance flags, and entity types used
across the NLP pipeline. Single source of truth — referenced by classifier,
evaluator, and UI.
"""

from enum import Enum


class ClauseLabel(str, Enum):
    DEFINITION = "definition"
    OBLIGATION = "obligation"
    LIABILITY = "liability"
    TERMINATION = "termination"
    DATA_PROCESSING = "data_processing"
    CONFIDENTIALITY = "confidentiality"
    DISPUTE_RESOLUTION = "dispute_resolution"
    FORCE_MAJEURE = "force_majeure"
    PENALTY = "penalty"
    IP_RIGHTS = "ip_rights"
    PAYMENT = "payment"
    WARRANTY = "warranty"


class ComplianceFlag(str, Enum):
    LNPDP_RELEVANT = "lnpdp_relevant"
    GDPR_RELEVANT = "gdpr_relevant"
    MISSING_RETENTION_PERIOD = "missing_retention_period"
    MISSING_CONSENT_MECHANISM = "missing_consent_mechanism"
    MISSING_DPO_REFERENCE = "missing_dpo_reference"
    EXCESSIVE_DATA_COLLECTION = "excessive_data_collection"
    MISSING_SECURITY_MEASURES = "missing_security_measures"
    UNLAWFUL_CROSS_BORDER_TRANSFER = "unlawful_cross_border_transfer"
    MISSING_DATA_SUBJECT_RIGHTS = "missing_data_subject_rights"
    UNCLEAR_LIABILITY_CAP = "unclear_liability_cap"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EntityLabel(str, Enum):
    PARTY = "PARTY"
    ROLE = "ROLE"
    DATA_CATEGORY = "DATA_CATEGORY"
    DURATION = "DURATION"
    AMOUNT = "AMOUNT"
    LAW_REFERENCE = "LAW_REFERENCE"
    JURISDICTION = "JURISDICTION"
    DATE = "DATE"


# Human-readable descriptions for UI display
TAXONOMY = {
    "clause_labels": {
        ClauseLabel.DEFINITION: "Clause that defines terms used in the contract",
        ClauseLabel.OBLIGATION: "Clause that imposes duties on one or both parties",
        ClauseLabel.LIABILITY: "Clause that limits or assigns liability",
        ClauseLabel.TERMINATION: "Clause that defines when/how the contract ends",
        ClauseLabel.DATA_PROCESSING: "Clause that describes how personal data is handled",
        ClauseLabel.CONFIDENTIALITY: "Clause covering information secrecy obligations",
        ClauseLabel.DISPUTE_RESOLUTION: "Clause covering arbitration, jurisdiction, governing law",
        ClauseLabel.FORCE_MAJEURE: "Clause covering exceptional circumstances",
        ClauseLabel.PENALTY: "Clause defining fines, damages, or breach consequences",
        ClauseLabel.IP_RIGHTS: "Clause covering intellectual property ownership or licensing",
        ClauseLabel.PAYMENT: "Clause covering payment terms, amounts, or schedules",
        ClauseLabel.WARRANTY: "Clause guaranteeing service or product quality",
    },
    "compliance_flags": {
        ComplianceFlag.LNPDP_RELEVANT: "Clause triggers LNPDP (Tunisian data protection) obligations",
        ComplianceFlag.GDPR_RELEVANT: "Clause triggers GDPR/RGPD obligations",
        ComplianceFlag.MISSING_RETENTION_PERIOD: "Data processing clause lacks a retention duration",
        ComplianceFlag.MISSING_CONSENT_MECHANISM: "No valid consent basis specified",
        ComplianceFlag.MISSING_DPO_REFERENCE: "No DPO contact when required",
        ComplianceFlag.EXCESSIVE_DATA_COLLECTION: "Data collected beyond stated purpose",
        ComplianceFlag.MISSING_SECURITY_MEASURES: "No technical/organizational security measures specified",
        ComplianceFlag.UNLAWFUL_CROSS_BORDER_TRANSFER: "Data transferred abroad without safeguards",
        ComplianceFlag.MISSING_DATA_SUBJECT_RIGHTS: "Fails to mention data subject rights",
        ComplianceFlag.UNCLEAR_LIABILITY_CAP: "Liability limitation is ambiguous or missing",
    },
    "entity_labels": {
        EntityLabel.PARTY: "Contracting parties (company or person names)",
        EntityLabel.ROLE: "Roles: responsable du traitement, sous-traitant, DPO",
        EntityLabel.DATA_CATEGORY: "Data types: données personnelles, données sensibles",
        EntityLabel.DURATION: "Time periods: 30 jours, 5 ans",
        EntityLabel.AMOUNT: "Monetary values, percentages, quantities",
        EntityLabel.LAW_REFERENCE: "Legal references: LNPDP, RGPD, Art. 23",
        EntityLabel.JURISDICTION: "Geographic scopes: Tunisie, Union européenne",
        EntityLabel.DATE: "Specific dates or date ranges",
    },
}

# Flat list of clause label strings (used by zero-shot classifier)
CLAUSE_LABEL_STRINGS: list[str] = [label.value for label in ClauseLabel]

# Flat list of compliance flag strings
COMPLIANCE_FLAG_STRINGS: list[str] = [flag.value for flag in ComplianceFlag]
