# P10.4B SCIENTIFIC CLAIM BOUNDARIES & EPISTEMOLOGICAL CLASSIFICATION

**Milestone:** P10.4B — Institutional Pilot Activation, External Evidence Preparation & Scientific Readiness  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Enforcement Module:** [`msk_therapy_os/scientific_claim_guard.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/scientific_claim_guard.py)  
**Lead Auditor / Role:** Principal Research Software Engineer & Computational Anatomy Lead  
**Audit Date:** 2026-10-30  
**Gate B405 Verdict:** **PASS (ZERO UNSUPPORTED SCIENTIFIC CLAIMS)**

---

## 1. Executive Summary

Milestone P10.4B establishes automated report-level and documentation-level claim validation guards. The system formally categorizes scientific statements into five distinct epistemological tiers and enforces runtime prohibitions against category conflations.

---

## 2. The Five Epistemological Claim Tiers

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   FIVE SCIENTIFIC EVIDENCE TIERS                       │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 1: PHYSICAL_ANATOMICAL_LANDMARK                                   │
│ Physical bones, articular margins, and fascial borders directly        │
│ verifiable on radiological cross-sectional scans (CT, MRI, Ultrasound).│
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2: REGISTRATION_SPATIAL_ACCURACY                                  │
│ Mathematical metric describing the geometric error (in mm) between     │
│ reference points and transformed canonical surfaces (Dice, RMSE).      │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3: INFERRED_ACUPOINT_LOCALIZATION                                 │
│ Coordinates estimated on a subject's skin surface based on anatomical  │
│ proportional division (B-cun) and directional normals.                │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 4: MERIDIAN_REPRESENTATION                                        │
│ Curvilinear geometric trajectories connecting standardized acupoints   │
│ according to traditional Chinese / WHO acupuncture conventions.        │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 5: CLINICAL_TREATMENT_EFFICACY                                    │
│ Therapeutic outcomes, neurophysiological modulation, and symptom relief│
│ assessed in randomized controlled clinical trials.                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Strict Category Crossing Prohibitions

The following logical category jumps are hard-blocked by `ScientificClaimValidator`:

### Invariant 1: Geometric Accuracy $\neq$ Physical Meridian Existence
Achieving sub-millimeter registration of cranial or limb landmarks on a CT scan demonstrates that the mathematical affine/non-rigid mesh transformation is accurate. It does **NOT** prove that traditional meridian lines exist as physical histological or macro-anatomical tubular conduits.

### Invariant 2: Inferred Coordinate Accuracy $\neq$ Clinical Efficacy
Accurately locating an acupoint coordinate (e.g., ST36) relative to the tibial tuberosity does **NOT** prove that inserting a needle or applying microcurrent produces clinical efficacy or cures any medical condition.

### Invariant 3: CT/MRI Scans Are Not Direct Meridian Images
Traditional acupuncture meridians cannot be claimed as directly visible radiological density structures on standard diagnostic CT or MRI images.

### Invariant 4: Puncture Depth Guidance Is Strictly Forbidden
Needle insertion depth guidance remains permanently disabled (`clinical_depth_guidance_allowed: False`).

---

## 4. Automated Guard Verification

The claim-validation guard was tested against deliberate adversarial assertions in `tests/test_p10_4b_scientific_readiness.py`:
- `test_claim_guard_prohibits_registration_proving_meridian_existence`: **PASS (REJECTED)**
- `test_claim_guard_prohibits_coordinate_accuracy_proving_efficacy`: **PASS (REJECTED)**
- `test_claim_guard_prohibits_needle_depth_guidance`: **PASS (REJECTED)**
- `test_claim_guard_allows_legitimate_engineering_statements`: **PASS (ALLOWED)**

---

## 5. Verification Verdict

All scientific assertions across documentation and software outputs respect strict epistemological boundaries. Gate B405 is certified as **PASS**.
