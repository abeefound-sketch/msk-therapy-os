# P9.8 Scapular Landmark Validation & Interscapular Calibration

**Document ID:** `P98_SCAPULAR_LANDMARK_VALIDATION.md`  
**Milestone:** P9.8 Anatomical Ground Truth & Evidence Integrity Hardening  
**Status:** APPROVED | MESH GROUNDED & TRACEABLE  
**Date:** 2026-10-28  

---

## 1. Anatomical Basis & Landmark Grounding

The medial border of the scapula (*margo medialis scapulae*, FMA 13449) is the primary anatomical reference for paraspinal acupoint localization along the Bladder (BL) channel and outer branch.

In `msk_therapy_os/landmark_registry.py`, bilateral scapular landmarks are registered:
- `LM_SCAPULA_MEDIAL_BORDER_R`: $(+0.0675	ext{ m}, +1.3500	ext{ m}, -0.0980	ext{ m})$
- `LM_SCAPULA_MEDIAL_BORDER_L`: $(-0.0675	ext{ m}, +1.3500	ext{ m}, -0.0980	ext{ m})$

### Mesh Grounding on BodyParts3D FJ2810:
- Scapular skeletal boundaries in `FJ2810` place the medial border at $X = \pm 0.0675	ext{ m} = \pm 67.5	ext{ mm}$.
- Transverse interscapular distance between bilateral medial borders:
  $$D_{	ext{interscapular}} = 0.0675 - (-0.0675) = 0.1350	ext{ m} = 135.0	ext{ mm}$$
- Bilateral symmetry across the sagittal plane ($X = 0.000$) is exact ($|X_R| = |X_L| = 67.50	ext{ mm}$).

---

## 2. Proportional B-Cun Derivation

According to the WHO Standard Acupuncture Point Locations (2008), Section 2.1.3 (*Proportional Bone Cun of the Back*):
> "The distance between the medial borders of the two scapulae is defined as **6 B-cun**."

Calculating the interscapular cun scaling factor:
$$	ext{Cun Ratio}_{	ext{interscapular}} = rac{135.0	ext{ mm}}{6	ext{ B-cun}} = \mathbf{22.50	ext{ mm / cun}}$$

This is codified in `msk_therapy_os/cun_scaling.py` as `SEG_BACK_INTERSCAPULAR`:
```python
ProportionalSegment(
    segment_id="SEG_BACK_INTERSCAPULAR",
    name_en="Interscapular transverse distance (medial scapular borders)",
    standard_cun=6.0,
    measured_length_mm=135.0,
    cun_ratio_mm=22.50,
    reference_standard="WHO Standard 2008 Section 2.1.3",
    start_landmark_id="LM_SCAPULA_MEDIAL_BORDER_R",
    end_landmark_id="LM_SCAPULA_MEDIAL_BORDER_L",
    uncertainty_radius_mm=4.5
)
```

---

## 3. Calibration of Paraspinal Bladder Channels

Nineteen paraspinal Bladder rules reference `SEG_BACK_INTERSCAPULAR`:
- **Inner Bladder Column (1.5 cun lateral to posterior midline):**
  $$X_{	ext{inner}} = 1.5	ext{ cun} 	imes 22.5	ext{ mm/cun} = \mathbf{33.75	ext{ mm}}$$
  Affects: `BL11, BL12, BL13, BL14, BL15, BL23, BL25`
- **Outer Bladder Column (3.0 cun lateral to posterior midline):**
  $$X_{	ext{outer}} = 3.0	ext{ cun} 	imes 22.5	ext{ mm/cun} = \mathbf{67.50	ext{ mm}}$$
  Affects: `BL41, BL42, BL43, BL44, BL45, BL46, BL47, BL48, BL49, BL50, BL52, BL54`

### Anatomical Concordance:
The outer Bladder column at $X = 67.50	ext{ mm}$ aligns precisely with the medial border of the scapula ($X = 67.50	ext{ mm}$), exactly fulfilling classical anatomical texts describing the outer branch running along the vertebral border of the shoulder blade.

---

## 4. Explicit Uncertainty Disclosure

Scapular position varies dynamically with shoulder protraction/retraction and arm position. Because BodyParts3D `FJ2810` represents a neutral standing posture, an explicit uncertainty margin of **$\pm 4.5	ext{ mm}$ (0.2 cun)** is formally assigned to all interscapular rules in the provenance matrix.
