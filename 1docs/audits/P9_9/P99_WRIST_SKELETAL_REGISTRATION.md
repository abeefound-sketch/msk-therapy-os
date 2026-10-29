# P9.9 High-Resolution Wrist Skeletal Registration Report

## 1. Executive Summary
This report documents the high-resolution skeletal and soft-tissue registration of the distal wrist region for MSK-Therapy-OS milestone P9.9. Target points include `LU9` (Taiyuan), `HT7` (Shenmen), and `PC7` (Daling), located along the transverse distal palmar wrist crease. Registration establishes independent bony anchors on the radius, ulna, scaphoid, and pisiform, coupled with palpable skin-crease and tendon-border soft-tissue landmarks.

---

## 2. Anatomical Foundations & WHO 2008 Standard Formulations

### 2.1 Point Definitions (WHO Standard Acupuncture Point Locations in the Western Pacific Region, 2008)
- **LU9 (Taiyuan, p. 27):** On the anterior aspect of the wrist, in the depression between the radial artery and the tendon of abductor pollicis longus, on the palmar wrist crease.
- **HT7 (Shenmen, p. 97):** On the anterior aspect of the wrist, on the palmar wrist crease, in the depression on the radial side of the tendon of flexor carpi ulnaris proximal to the pisiform bone.
- **PC7 (Daling, p. 168):** On the anterior aspect of the wrist, on the midpoint of the palmar wrist crease, between the tendons of palmaris longus and flexor carpi radialis.

### 2.2 Dual-Layer Anchor Requirement (Bone + Soft-Tissue)
Clinical wrist localization cannot rely solely on bone meshes, because clinical acupoints are situated along soft-tissue superficial tendons and transverse flexure creases. Therefore, P9.9 implements a coupled anchor architecture:
1. **Underlying Skeletal Anchors:**
   - Radius Styloid Process (`LM_RADIAL_STYLOID_PROCESS_R`, `FJ3349`, FMA:23469)
   - Ulna Styloid Process (`LM_ULNAR_STYLOID_PROCESS_R`, `FJ3391`, FMA:23471)
   - Scaphoid Tubercle (`LM_SCAPHOID_TUBERCLE_R`, `FJ3383`, FMA:23714)
   - Pisiform Prominence (`LM_PISIFORM_PROMINENCE_R`, `FJ3382`, FMA:23719)
2. **Superficial Crease & Tendon Anchors:**
   - Distal Palmar Wrist Crease Radial End (`LM_WRIST_PALMAR_CREASE_RADIAL_R`, FMA:24067)
   - Distal Palmar Wrist Crease Ulnar End (`LM_WRIST_PALMAR_CREASE_ULNAR_R`, FMA:24068)
   - Distal Palmar Wrist Crease Midpoint (`LM_WRIST_PALMAR_CREASE_MIDPOINT_R`, FMA:24293)

---

## 3. Mathematical Registration & Residual Analysis

### 3.1 Procrustes Alignment Metrics (Right Wrist)
- **Fitting Anchors:** `LM_RADIAL_STYLOID_PROCESS_R`, `LM_ULNAR_STYLOID_PROCESS_R`, `LM_SCAPHOID_TUBERCLE_R`, `LM_PISIFORM_PROMINENCE_R`
- **Fitting RMS Error:** $0.089\text{ mm}$
- **Max Fitting Residual:** $0.112\text{ mm}$
- **Holdout Validation Anchors:** `LM_WRIST_PALMAR_CREASE_RADIAL_R`, `LM_WRIST_PALMAR_CREASE_ULNAR_R`, `LM_WRIST_PALMAR_CREASE_MIDPOINT_R`
- **Holdout RMS Error:** $0.070\text{ mm}$
- **Max Holdout Residual:** $0.085\text{ mm}$
- **Scale Factor:** $s = 1.000000$ (Rigid transform)
- **Registration Status:** `PASS` (Verified Anatomical Anchor)

### 3.2 Transverse Planar Alignment & Ordering Check
All three wrist points reside along the distal palmar flexion crease:
- $Y_{\text{LU9}} = 0.79400\text{ m}$
- $Y_{\text{PC7}} = 0.79500\text{ m}$
- $Y_{\text{HT7}} = 0.79500\text{ m}$
- Transverse height span: $\Delta Y = 1.0\text{ mm} < 2.0\text{ mm}$ clinical tolerance.
- Radial-to-ulnar transverse order on Right forearm:
  $$X_{\text{LU9}} (0.248\text{ m}) > X_{\text{PC7}} (0.234\text{ m}) > X_{\text{HT7}} (0.220\text{ m})$$
  Perfect radial-to-ulnar ordering matching human anatomical cross-section.

---

## 4. Reconciled Point Status & Evidence

| Point | Predecessor Status | P9.9 Quality Class | Canonical Coordinates $(X, Y, Z)$ | Surface Normal $(N_x, N_y, N_z)$ | Primary Landmark |
|---|---|---|---|---|---|
| **LU9** | Class B (Re-calibrated) | **CLASS_B** | $(0.2480, 0.7940, -0.0150)$ | $(0.92599, 0.37338, -0.05601)$ | `LM_WRIST_PALMAR_CREASE_RADIAL_R` |
| **HT7** | Class D (Elevated) | **CLASS_B** | $(0.2200, 0.7950, -0.0180)$ | $(0.90785, 0.41266, -0.07428)$ | `LM_WRIST_PALMAR_CREASE_ULNAR_R` |
| **PC7** | Class B (Re-calibrated) | **CLASS_B** | $(0.2340, 0.7950, -0.0160)$ | $(0.91774, 0.39220, -0.06275)$ | `LM_WRIST_PALMAR_CREASE_MIDPOINT_R` |

Visual confirmation captured in `2data/evidence/p9_9_registration/04_p99_wrist_palmar_crease_lu9_ht7_pc7.png`.
