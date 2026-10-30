"""MSK-Therapy-OS P10.4B Scientific Claim Boundary Guard

Enforces strict epistemological separation across 5 distinct scientific claim categories.
Prevents category conflation (e.g. asserting that CT/MRI registration proves meridian existence
or clinical acupuncture efficacy).

Five Epistemological Claim Tiers:
1. PHYSICAL_ANATOMICAL_LANDMARK: Physical osseous or soft-tissue features directly visible on scans.
2. REGISTRATION_SPATIAL_ACCURACY: Mathematical distance/error of coordinate transformation algorithms.
3. INFERRED_ACUPOINT_LOCALIZATION: Computationally estimated acupoint coordinates based on rules.
4. MERIDIAN_REPRESENTATION: Traditional curvilinear trajectory models connecting acupoints.
5. CLINICAL_TREATMENT_EFFICACY: Patient-reported outcomes, therapeutic efficacy, neurophysiological action.

Invariants:
- REGISTRATION_SPATIAL_ACCURACY != MERIDIAN_PHYSICAL_EXISTENCE
- INFERRED_ACUPOINT_LOCALIZATION != CLINICAL_TREATMENT_EFFICACY
- PHYSICAL_ANATOMICAL_LANDMARK != TRADITIONAL_MERIDIAN_PATHWAY
- ENGINEERING_READY != CLINICALLY_VALIDATED
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ClaimCategory(str, Enum):
    PHYSICAL_ANATOMICAL_LANDMARK = "PHYSICAL_ANATOMICAL_LANDMARK"
    REGISTRATION_SPATIAL_ACCURACY = "REGISTRATION_SPATIAL_ACCURACY"
    INFERRED_ACUPOINT_LOCALIZATION = "INFERRED_ACUPOINT_LOCALIZATION"
    MERIDIAN_REPRESENTATION = "MERIDIAN_REPRESENTATION"
    CLINICAL_TREATMENT_EFFICACY = "CLINICAL_TREATMENT_EFFICACY"


class InvalidScientificClaimError(ValueError):
    """Raised when an unverified assertion conflates evidence categories."""
    pass


@dataclass
class ScientificClaim:
    claim_id: str
    category: ClaimCategory
    statement: str
    supporting_evidence_ids: List[str]
    is_empirical: bool = False
    context_tags: List[str] = None


# Patterns that cross category boundaries improperly
_PROHIBITED_CLAIM_PATTERNS = [
    # Imaging/registration claimed as proof of meridian physical existence
    (
        re.compile(r"(image|ct|mri|registration|transform|alignment|dice|rmse).*(proves?|demonstrates?|confirms?).*(meridian.*exist|physical.*meridian|anatomical.*meridian)", re.IGNORECASE),
        "Category Conflation: Imaging registration accuracy cannot be asserted as proof of physical meridian existence."
    ),
    # Computational localization claimed as proof of therapeutic efficacy
    (
        re.compile(r"(inferred|localization|coordinate|cun|accuracy|algorithm).*(proves?|establishes?|validates?).*(efficacy|cure|clinical.*benefit|therapeutic.*action)", re.IGNORECASE),
        "Category Conflation: Computational coordinate estimation cannot be asserted as proof of clinical treatment efficacy."
    ),
    # Direct physical visualization of meridian on standard radiological CT/MRI
    (
        re.compile(r"(meridian|jing-luo|jingluo).*(visible|imaged|directly.*seen|radiological.*density).*(ct|mri|radiology|x-ray)", re.IGNORECASE),
        "Category Conflation: Traditional meridians are not directly visible histological/radiological density structures on standard CT/MRI."
    ),
    # Needle depth prescription
    (
        re.compile(r"(recommend|prescribe|instruct).*(puncture|needle|insertion).*(depth|\d+\s*(mm|cm|cun))", re.IGNORECASE),
        "Safety Prohibition: Invasive needle puncture depth guidance is strictly prohibited (clinical_depth_guidance_allowed: False)."
    ),
    # Autonomous diagnosis
    (
        re.compile(r"(system|software|ai|algorithm).*(diagnoses?|diagnosed|prescribes?).*(patient|condition|pathology)", re.IGNORECASE),
        "Safety Prohibition: Autonomous diagnosis and therapy prescription are strictly prohibited."
    )
]


class ScientificClaimValidator:
    """Validates scientific assertions, audit reports, and research statements against category conflation."""

    @staticmethod
    def audit_statement(statement: str) -> Tuple[bool, List[str]]:
        """Checks a textual claim or documentation string for prohibited category crossings.
        
        Returns:
            (is_compliant, violations_list)
        """
        violations: List[str] = []
        for pattern, reason in _PROHIBITED_CLAIM_PATTERNS:
            if pattern.search(statement):
                violations.append(reason)
        return len(violations) == 0, violations

    @staticmethod
    def validate_claim_structure(claim: ScientificClaim) -> Tuple[bool, List[str]]:
        """Validates formal claim object structure and category constraints."""
        ok, violations = ScientificClaimValidator.audit_statement(claim.statement)
        
        # Clinical efficacy claims cannot be made from non-empirical evidence
        if claim.category == ClaimCategory.CLINICAL_TREATMENT_EFFICACY and not claim.is_empirical:
            violations.append("Efficacy claims cannot be made without authorized external empirical trial datasets.")
            
        return len(violations) == 0, violations

    @staticmethod
    def enforce_guard(statement: str) -> None:
        """Raises InvalidScientificClaimError if statement violates scientific claim boundaries."""
        ok, violations = ScientificClaimValidator.audit_statement(statement)
        if not ok:
            raise InvalidScientificClaimError("; ".join(violations))
