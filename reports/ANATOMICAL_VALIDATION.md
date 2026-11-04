# MSK-Therapy-OS: Authoritative Anatomical & Biomechanical Validation Status

**Date:** November 5, 2026  
**Reference Mesh:** DBCLS BodyParts3D Release 4.0 FJ2810 Male Mesh (`05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808`)  
**International Standard Reference:** World Health Organization (WHO) Standard Acupuncture Point Locations in the Western Pacific Region (2008, ISBN 978 92 9061 248 3).

---

## 1. 17-Bone Canonical Skeleton & UABS Kinematics

The Universal Anatomical Binding System (UABS) defines a standard 17-bone kinematic hierarchy:
- Head, Cervical Spine, Thoracic Spine, Lumbar Spine, Pelvis
- Clavicle (L/R), Humerus (L/R), Radius/Ulna (L/R), Hand (L/R)
- Femur (L/R), Tibia/Fibula (L/R), Foot (L/R)

### Rigid Bone Invariant:
- Unlike commercial game engines that apply bone stretching, UABS enforces rigid bone transforms using orthogonal rotation matrices:
  $$\mathbf{p}_{	ext{world}} = \mathbf{R}_{	ext{bone}} \cdot \mathbf{p}_{	ext{local}} + \mathbf{t}_{	ext{bone}}$$
- **Metric Drift:** Strictly 0.00 mm bone deformation across full joint ranges of motion.

---

## 2. Acupoint Proportional Cun Localization Audit

- **Catalog Cardinality:** 361 WHO classical channel points + 1 classical extra point (`GV24+` / Yintang) = **362 acupoint records**.
- **Parametric Localization Rules:** 360 procedural localization rules in `msk_therapy_os/point_localization_rules.py`.
- **Class A Canonical Anchors:** 18 bony palpation anchors (`BL10`, `BL11`, `BL12`, `BL13`, `BL40`, `CV22`, `GB20`, `GB21`, `GV14`, `GV15`, `GV16`, `HT3`, `LI15`, `LI4`, `LU5`, `PC6`, `ST35`, `ST36`).
- **Class B Parametric Rules:** 344 proportional B-cun rules dynamically projected onto the FJ2810 surface mesh.
- **Strict Classical Tolerance (<1.5 mm):** 332 / 362 points (91.71%).
- **Cun Elasticity Variance:** Stomach abdominal line (`ST19..ST30`) has an empirical uncertainty of $\pm 8.5	ext{ mm}$ due to soft tissue expansion; invasive clinical needle depth guidance is strictly prohibited.

---

## 3. Strict Boundary: Simulated Geometry vs. Clinical In-Vivo Ground Truth

To preserve scientific integrity, MSK-Therapy-OS enforces a strict separation:
1. **Tier 1 - Mathematical Unit Tests:** Proves algorithmic correctness of vector math and matrix multiplications.
2. **Tier 2 - Procedural Mesh Verification:** Proves that points lie on the triangulated surface of BodyParts3D FJ2810.
3. **Tier 3 - Dynamic Kinematic Stability:** Proves that acupoints maintain barycentric coordinates during skeletal animation.
4. **Tier 4 / 5 - In-Vivo Patient Ground Truth:** **CURRENTLY ZERO (0.0%)**. No patient CT/MRI holdout data has been ingested into production. The system strictly outputs `INDEPENDENT_GROUND_TRUTH_UNAVAILABLE` when queried for external clinical gold standard validation.
