"""Rule-based safety gating, red flags screening, and modality contraindication engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from msk_therapy_os.models import Disposition


# Baseline M0 red flags preserved for full backward compatibility, plus clinical additions from IFOMPT/NICE.
RED_FLAGS_MAP: Dict[str, str] = {
    "none": "No red flag reported.",
    "progressive_weakness": "Progressive neurological motor weakness (suggestive of motor nerve root or spinal cord compression).",
    "bowel_bladder_change": "Sudden loss of bowel or bladder control (classic sign of Cauda Equina Syndrome).",
    "saddle_numbness": "Perianal, perineal, or groin numbness / paresthesia (Cauda Equina Syndrome red flag).",
    "fever_with_spinal_pain": "Fever, chills, or unexplained night sweats with localized spinal tenderness (suggestive of spinal infection/discitis).",
    "major_trauma": "Major acute trauma (fall from height, high-speed motor vehicle collision) with risk of fracture or instability.",
    "unexplained_weight_loss_history_cancer": "Unexplained weight loss (>10% body weight) and personal history of cancer (risk of spinal metastasis).",
    "severe_unremitting_night_pain": "Constant, severe, unremitting spinal pain unaffected by position or rest.",
    "acute_cervical_myelopathy": "Signs of spinal cord compression: gait ataxia, bilateral hand clumsiness, pathologically brisk reflexes.",
    "vascular_stroke_signs": "Cervical arterial dysfunction / stroke symptoms (FAST signs, drop attacks, diplopia, dysarthria, dysphagia).",
    "dvt_thrombosis_signs": "Signs of deep vein thrombosis: acute localized unilateral limb swelling, redness, heat, deep calf tenderness.",
    "suspected_fracture": "Severe focal bone tenderness, visible deformity, or inability to bear weight after minor trauma in osteoporotic patient.",
}

RED_FLAGS = tuple(RED_FLAGS_MAP.keys())

# Modality Contraindications
MODALITY_CONTRAINDICATIONS: Dict[str, Dict[str, str]] = {
    "manual_massage": {
        "systemic_infection": "Acute febrile systemic illness or contagious infectious disease.",
        "active_dvt": "Deep vein thrombosis or active thrombophlebitis (embolism risk).",
        "uncontrolled_hypertension": "Severe uncontrolled hypertension or acute cardiovascular instability.",
        "open_wound_dermatitis": "Broken skin, acute dermatitis, burns, or open lesions in treatment area.",
        "acute_inflammatory_arthritis": "Acute flare of inflammatory arthritis or septic joint.",
    },
    "dds_device": {
        "cardiac_pacemaker": "Cardiac pacemaker or implanted defibrillator (fatal arrhythmia risk from stray electrical currents).",
        "implanted_electronic_device": "Any implanted neurostimulator or electronic medical implant.",
        "pregnancy": "Pregnancy (unknown teratogenic or contractility effects from non-standardized currents).",
        "active_malignancy": "Active malignancy or tumor site (risk of stimulating tumor perfusion/growth).",
        "trans_thoracic_application": "Transthoracic current vector (risk of cardiac arrhythmia).",
        "carotid_sinus_application": "Electrode placement over carotid sinus (risk of acute severe bradycardia and syncope).",
        "missing_device_specs": "DDS is an ambiguous product label. Unverified make, model, waveform, and peak current limits.",
    },
    "passive_stretch": {
        "joint_instability": "Acute joint dislocation, ligamentous rupture, or unhealed fracture.",
        "vertebral_artery_insufficiency": "Vascular compromise provoked during cervical end-range positioning.",
    },
    "spinal_manipulation": {
        "all_scenarios": "High-velocity low-amplitude thrust spinal manipulation is strictly prohibited in this educational tool.",
    },
}


@dataclass(frozen=True)
class SafetyEvaluation:
    disposition: Disposition
    is_safe_to_proceed: bool
    flags_triggered: List[str]
    contraindications_triggered: List[str]
    escalation_instructions: str
    clinical_rationale: str
    evidence_id: str


def evaluate_safety(
    flag: str = "none",
    modality: Optional[str] = None,
    contraindications: Optional[List[str]] = None,
) -> SafetyEvaluation:
    """Evaluate patient safety inputs against rule-based clinical hard gates.

    Rule 1: Any positive red flag triggers an immediate STOP_AND_REFER.
    Rule 2: High-velocity spinal manipulation is strictly forbidden.
    Rule 3: DDS device workflows require verified specifications and have strict electrical contraindications.
    Rule 4: Any detected modality contraindication triggers STOP_AND_REFER.
    """
    flag = flag.strip().lower()
    if flag not in RED_FLAGS_MAP:
        raise ValueError(f"Unknown flag '{flag}'. Must be one of: {', '.join(RED_FLAGS)}")

    triggered_flags = [flag] if flag != "none" else []
    triggered_contraindications: List[str] = []

    # Check modality-specific rules
    if modality:
        mod_key = modality.strip().lower()
        if mod_key == "spinal_manipulation":
            return SafetyEvaluation(
                disposition=Disposition.STOP_AND_REFER,
                is_safe_to_proceed=False,
                flags_triggered=triggered_flags,
                contraindications_triggered=["forbidden_modality: spinal_manipulation"],
                escalation_instructions="HIGH-VELOCITY SPINAL MANIPULATION IS STRICTLY PROHIBITED in MSK-Therapy-OS.",
                clinical_rationale="High-velocity cervical/spinal thrust manipulation carries catastrophic neurovascular risks (vertebral artery dissection, spinal cord injury) and must never be taught via software.",
                evidence_id="EVID-G-002",
            )

        if mod_key == "dds_device":
            # DDS device requires exact model verification
            if contraindications and "missing_device_specs" in contraindications:
                triggered_contraindications.append("missing_device_specs: DDS make/model/waveform unverified")

        # Check known contraindications for modality
        if mod_key in MODALITY_CONTRAINDICATIONS and contraindications:
            known = MODALITY_CONTRAINDICATIONS[mod_key]
            for c in contraindications:
                c_clean = c.strip().lower()
                if c_clean in known:
                    triggered_contraindications.append(f"{c_clean} ({known[c_clean]})")

    # If any positive red flag is detected -> hard stop independent of pain or modality
    if triggered_flags:
        flag_desc = RED_FLAGS_MAP[flag]
        return SafetyEvaluation(
            disposition=Disposition.STOP_AND_REFER,
            is_safe_to_proceed=False,
            flags_triggered=triggered_flags,
            contraindications_triggered=triggered_contraindications,
            escalation_instructions=(
                "HARD STOP AND IMMEDIATE REFERRAL: CRITICAL RED FLAG DETECTED. DO NOT PROCEED with massage, manual techniques, or electrical devices. "
                "Immediately document findings and direct patient to emergency medical evaluation or a qualified physician."
            ),
            clinical_rationale=f"Reported red flag: {flag_desc} Under clinical triage guidelines (NICE NG59, IFOMPT), physical interventions are contraindicated pending formal medical clearance.",
            evidence_id="EVID-G-001" if "bowel" in flag or "saddle" in flag or "fever" in flag else "EVID-G-002",
        )

    # If any contraindication is detected -> stop
    if triggered_contraindications:
        return SafetyEvaluation(
            disposition=Disposition.STOP_AND_REFER,
            is_safe_to_proceed=False,
            flags_triggered=[],
            contraindications_triggered=triggered_contraindications,
            escalation_instructions=(
                "MODALITY CONTRAINDICATION DETECTED. The requested intervention is contraindicated for this condition. "
                "Document findings and consult supervising clinical instructor."
            ),
            clinical_rationale="Contraindicated condition detected under FDA / clinical manual therapy guidelines.",
            evidence_id="EVID-G-003",
        )

    # Document-only scenario for educational recording
    return SafetyEvaluation(
        disposition=Disposition.DOCUMENT_ONLY,
        is_safe_to_proceed=True,
        flags_triggered=[],
        contraindications_triggered=[],
        escalation_instructions="No red flags or absolute contraindications entered. Proceed with educational scenario observation only.",
        clinical_rationale="Educational synthetic observation. NOTE: Absence of entered flags does NOT constitute medical clearance or treatment endorsement.",
        evidence_id="EVID-G-001",
    )
