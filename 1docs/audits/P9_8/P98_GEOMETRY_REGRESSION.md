# P9.8 Geometry & Topological Invariance Regression Report

**Document ID:** `P98_GEOMETRY_REGRESSION.md`  
**Milestone:** P9.8 Anatomical Ground Truth & Evidence Integrity Hardening  
**Status:** APPROVED | GEOMETRIC INVARIANTS PRESERVED  
**Date:** 2026-10-28  

---

## 1. Midline Invariance ($X = 0.000	ext{ mm}$)

The classical Governor Vessel (GV) and Conception Vessel (CV) channels follow the exact anterior and posterior anatomical midlines (*linea alba*, anterior median line of sternum, posterior median line of spine).

### Mathematical Invariant:
$$orall p \in 	ext{GV} \cup 	ext{CV}, \quad |X(p)| < 0.001	ext{ mm}$$

### Audit Results:
- **GV Channel (28 points):** Max $|X| = 0.000000	ext{ m}$. Mean residual $= 0.0000	ext{ mm}$.
- **CV Channel (24 points):** Max $|X| = 0.000000	ext{ m}$. Mean residual $= 0.0000	ext{ mm}$.
- **Verdict:** **PASS | ZERO MIDLINE DRIFT**

---

## 2. Bilateral Sagittal Symmetry

Paired bilateral channels (LU, LI, ST, SP, HT, SI, BL, KI, PC, TE, GB, LR) must demonstrate exact reflection symmetry across the sagittal plane ($X = 0$):
$$X_{	ext{left}} = -X_{	ext{right}}, \quad Y_{	ext{left}} = Y_{	ext{right}}, \quad Z_{	ext{left}} = Z_{	ext{right}}$$

### Audit Results:
- Evaluated across all 118 Class B and 18 Class A bilateral points.
- Maximum observed symmetry discrepancy: $< 0.0001	ext{ mm}$.
- **Verdict:** **PASS | EXACT BILATERAL REFLECTION**

---

## 3. Craniocaudal Monotonicity (Bladder Paraspinal Columns)

The outer Bladder column (`BL41` through `BL50`) descends parallel to the spine along the medial scapular border from T2 to T12:
$$Y(	ext{BL41}) > Y(	ext{BL42}) > Y(	ext{BL43}) > \dots > Y(	ext{BL50})$$

### Audit Results:
- Vertebral levels verified: T2 (`BL41`), T3 (`BL42`), T4 (`BL43`), T5 (`BL44`), T6 (`BL45`), T7 (`BL46`), T9 (`BL47`), T10 (`BL48`), T11 (`BL49`), T12 (`BL50`).
- T8 omission strictly respected (classical skip).
- Y coordinates descend strictly monotonically from $1.365	ext{ m}$ to $1.155	ext{ m}$.
- Lateral distance remains consistently anchored at $X = 67.50	ext{ mm}$.
- **Verdict:** **PASS | MONOTONIC DESCENDING ORDER CONFIRMED**

---

## 4. Surface Normal Orientation

All acupoint coordinate frames define an outward-pointing unit normal vector $ec{n} = (n_x, n_y, n_z)$ perpendicular to the local skin surface.

### Mathematical Invariant:
$$ec{n} \cdot ec{d}_{	ext{centroid}} > 0, \quad \|ec{n}\| = 1.0 \pm 0.001$$

### Audit Results:
- Anterior points (CV, ST anterior): $n_z > 0.0$
- Posterior points (GV back, BL back): $n_z < 0.0$
- Lateral points (GB cranial, LI arm): $|n_x| > 0.707$
- Normals evaluated for all 362 points; zero inverted normals detected.
- **Verdict:** **PASS | ALL NORMALS OUTWARD ORIENTED**
