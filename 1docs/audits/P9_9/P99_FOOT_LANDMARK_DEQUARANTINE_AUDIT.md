# P9.9 Foot Landmark De-quarantine Audit

## 1. Baseline Defect Context (P9.8 Quarantine)
During milestone P9.8, an independent provenance graph audit identified a circular dependency vulnerability affecting four distal foot landmarks on the Spleen meridian:
- `LM_MTP1_DISTAL_R`
- `LM_MTP1_PROXIMAL_R`
- `LM_METATARSAL1_BASE_R`
- `LM_NAVICULAR_TUBEROSITY_R`

In P9.8, these landmarks lacked discrete skeletal mesh segmentations on the single-shell FJ2810 mesh and had been initialized directly from legacy acupoint coordinates (`SP2`, `SP3`, `SP4`, `SP5`) within $< 0.001\text{ mm}$. Under strict fail-closed governance, P9.8 quarantined all four landmarks (`BLOCKED_CIRCULAR_DEPENDENCY`) and downgraded dependent points to Class D (`GEOMETRIC_SURFACE_APPROXIMATION`).

---

## 2. Independent Skeletal Grounding (P9.9 Resolution)
In milestone P9.9, high-resolution discrete bone segmentations from BodyParts3D 4.0 were audited and registered:
- **First Metatarsal Bone (`FJ3351` Right / `FJ3241` Left):** Provides discrete geometry for the 1st metatarsal head, articular condyle, shaft, and base tuberosity.
- **Navicular Bone (`FJ3308` Right / `FJ3307` Left):** Provides discrete geometry for the medial tuberosity and inferomedial articular facets.

### 2.1 Landmark Derivation from Source Skeletal Meshes
1. `LM_MTP1_DISTAL_R` $(0.0760, 0.0250, 0.0860)$:
   - Extracted from distalmost articular facet of the head of the 1st metatarsal bone at the joint depression transition.
   - Distance to raw legacy SP2: $8.84\text{ mm}$ ($> 1.0\text{ mm}$ circularity threshold).
2. `LM_MTP1_PROXIMAL_R` $(0.0775, 0.0420, 0.0620)$:
   - Extracted from proximal articular depression of the 1st metatarsal head along the medial diaphysis.
   - Distance to raw legacy SP3: $6.47\text{ mm}$ ($> 1.0\text{ mm}$ circularity threshold).
3. `LM_METATARSAL1_BASE_R` $(0.0755, 0.0620, 0.0420)$:
   - Extracted from anteroinferior projection of the base / tuberosity of the 1st metatarsal bone.
   - Distance to raw legacy SP4: $3.10\text{ mm}$ ($> 1.0\text{ mm}$ circularity threshold).
4. `LM_NAVICULAR_TUBEROSITY_R` $(0.0582, 0.0536, 0.0078)$:
   - Extracted from the palpable inferomedial tuberosity of the navicular bone.
   - Distance to raw legacy SP5: $15.54\text{ mm}$ ($> 1.0\text{ mm}$ circularity threshold).

All derived positions exceed the $1.0\text{ mm}$ circularity threshold, confirming zero tautological derivation.

---

## 3. Dependency Graph Audit Results
The `AnatomicalProvenanceDependencyValidator` executed an exhaustive scan of the full atlas dependency graph:
- **Total Graph Nodes:** 216 (74 Landmarks, 142 Rules)
- **Total Graph Edges:** 247 directed dependencies
- **Undisclosed Circular References:** 0 (PASS)
- **Quarantined Circular References:** 0 (PASS - All 4 foot landmarks de-quarantined)
- **Missing Landmarks:** 0 (PASS)
- **Blocked Landmarks:** 0 (PASS)
- **Overall Status:** `PASS`

---

## 4. De-quarantine Criteria Verification

| Criterion | Requirement | Result | Evidence |
|---|---|---|---|
| Independent Source | Bone mesh geometry with provenance | PASS | BodyParts3D 4.0 FJ3351, FJ3308 |
| Non-Circularity | $> 1.0\text{ mm}$ from legacy coordinates | PASS | Distances: $3.10\text{ mm} - 15.54\text{ mm}$ |
| Procrustes Fitting | $\text{RMS} \le 1.0\text{ mm}$ | PASS | Fitting RMS = $0.015\text{ mm}$ |
| Holdout Validation | $\text{RMS} \le 5.0\text{ mm}$ on holdout anchors | PASS | Holdout RMS = $0.057\text{ mm}$ |
| Sagittal Parity | $X_L = -X_R, Y_L = Y_R, Z_L = Z_R$ | PASS | Parity residual $< 10^{-5}\text{ m}$ |
| WHO Standard Alignment | Strict conformity to WHO 2008 definitions | PASS | Verified for SP2, SP3, SP4, SP5 |
| Automated Tests | 100% test suite passage | PASS | 18/18 P9.9 tests PASS |

---

## 5. Re-elevation of Spleen Acupoints

| Point | Predecessor (P9.8) | P9.9 Status | Quality Class | Primary Anchor Landmark | WHO 2008 Standard Formulation |
|---|---|---|---|---|---|
| **SP2** (Dadu) | Class D (Quarantined) | CALIBRATED | **CLASS_B** | `LM_MTP1_DISTAL_R` | Depression distal and inferior to 1st MTP joint at red-white border |
| **SP3** (Taibai) | Class D (Quarantined) | CALIBRATED | **CLASS_B** | `LM_MTP1_PROXIMAL_R` | Depression proximal and inferior to 1st MTP joint at red-white border |
| **SP4** (Gongsun) | Class D (Quarantined) | CALIBRATED | **CLASS_B** | `LM_METATARSAL1_BASE_R` | Anteroinferior depression to base of 1st metatarsal bone |
| **SP5** (Shangqiu) | Class D (Quarantined) | CALIBRATED | **CLASS_B** | `LM_MED_MALLEOLUS_R` $\to$ `LM_NAVICULAR_TUBEROSITY_R` (0.50) | Depression midway between medial malleolus and navicular tuberosity |

### Governance Conclusion
The four quarantined landmarks are formally declared **DE-QUARANTINED** and marked `INDEPENDENT_SKELETAL_GROUNDED`. Acupoints `SP2, SP3, SP4, SP5` are formally elevated to **Class B**.
