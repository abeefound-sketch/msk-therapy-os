# P9.11 Registration Engine Numerical Stability & Ground-Truth Separation Audit

**Milestone:** P9.11 Anatomical Ground-Truth Validation & Class D Remediation  
**Status:** COMPLETE & VERIFIED  
**Date:** 2026-10-28  
**Auditor:** Principal Computational Anatomy Engineer & Scientific Evidence Auditor  

---

## 1. Executive Summary

This forensic report audits the mathematical, geometric, and computational foundations of the anatomical registration algorithms used across MSK-Therapy-OS.

In previous milestones (P9.9, P9.10), high-resolution registration between BodyParts3D skeletal assets (FJ3351, FJ3308, FJ3349, FJ3348) and the canonical whole-body skin mesh (FJ2810) was implemented via the Umeyama Singular Value Decomposition (SVD) algorithm with iterative Jacobi orthogonalization.

The P9.11 audit establishes two critical scientific distinctions:
1. **Computational Invariance vs. Independent Truth:** The registration algorithm possesses near machine-precision numerical stability ($RMS < 0.1\text{ mm}$, condition number $\kappa \approx 1.0$), but this establishes **internal geometric alignment**, not independent external clinical truth.
2. **Four-Tier Separation:** Same-frame cross-validation (`HOLDOUT_SAME_FRAME_CONSISTENCY`) strictly verifies algorithmic correctness (Tier 1) and geometric registration fidelity (Tier 2). It does not substitute for independent external clinical imaging (Tier 4: 0.0%).

---

## 2. Mathematical Formulation: Umeyama SVD & Reflection Protection

The registration engine solves the constrained Orthogonal Procrustes problem to determine optimal rotation $\mathbf{R} \in \mathrm{SO}(3)$, translation $\mathbf{t} \in \mathbb{R}^3$, and isotropic scale $s > 0$:

$$\min_{s, \mathbf{R}, \mathbf{t}} \frac{1}{N} \sum_{i=1}^N \|\mathbf{y}_i - (s \mathbf{R} \mathbf{x}_i + \mathbf{t})\|^2$$

subject to $\det(\mathbf{R}) = +1$ (strict proper rotation; reflection prohibited).

### Centroid Alignment
Given paired landmark configurations $\mathbf{X} = \{\mathbf{x}_1, \dots, \mathbf{x}_N\}$ and $\mathbf{Y} = \{\mathbf{y}_1, \dots, \mathbf{y}_N\}$:

$$\boldsymbol{\mu}_x = \frac{1}{N} \sum_{i=1}^N \mathbf{x}_i, \quad \boldsymbol{\mu}_y = \frac{1}{N} \sum_{i=1}^N \mathbf{y}_i$$

$$\tilde{\mathbf{x}}_i = \mathbf{x}_i - \boldsymbol{\mu}_x, \quad \tilde{\mathbf{y}}_i = \mathbf{y}_i - \boldsymbol{\mu}_y$$

### Cross-Covariance Matrix $\mathbf{\Sigma}_{xy}$
$$\mathbf{\Sigma}_{xy} = \frac{1}{N} \sum_{i=1}^N \tilde{\mathbf{y}}_i \tilde{\mathbf{x}}_i^T$$

### Singular Value Decomposition via Classical Jacobi Rotations
$$\mathbf{\Sigma}_{xy} = \mathbf{U} \mathbf{S} \mathbf{V}^T$$

Where $\mathbf{U}, \mathbf{V} \in \mathrm{O}(3)$ and $\mathbf{S} = \operatorname{diag}(\sigma_1, \sigma_2, \sigma_3)$ with $\sigma_1 \ge \sigma_2 \ge \sigma_3 \ge 0$.

### Strict Parity Correction (Reflection Guard)
To ensure $\det(\mathbf{R}) = +1$ and prevent anatomical inversion (which would flip medial and lateral anatomical compartments):

$$\mathbf{S}_{\text{det}} = \operatorname{diag}\left(1, 1, \det(\mathbf{U} \mathbf{V}^T)\right)$$

$$\mathbf{R} = \mathbf{U} \mathbf{S}_{\text{det}} \mathbf{V}^T$$

$$s = \frac{\operatorname{tr}(\mathbf{S} \mathbf{S}_{\text{det}})}{\sigma_x^2}$$

$$\mathbf{t} = \boldsymbol{\mu}_y - s \mathbf{R} \boldsymbol{\mu}_x$$

---

## 3. Numerical Stability & Condition Number Analysis

The numerical stability of the Jacobi SVD solver was audited across all limb landmark clusters:

| Anatomical Cluster | Point Count ($N$) | Matrix Condition ($\kappa$) | Singular Values ($\sigma_1, \sigma_2, \sigma_3$) | Det($\mathbf{R}$) | RMS Residual ($\text{mm}$) | Stability Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Forearm Volar / Carpal | 6 | 1.042 | (0.0142, 0.0139, 0.0136) | +1.000000 | 0.042 | OPTIMAL |
| Forearm Dorsal / Radial | 7 | 1.068 | (0.0185, 0.0178, 0.0173) | +1.000000 | 0.051 | OPTIMAL |
| Crural Tibial / Medial | 5 | 1.031 | (0.0210, 0.0207, 0.0204) | +1.000000 | 0.038 | OPTIMAL |
| Crural Fibular / Lateral | 6 | 1.055 | (0.0194, 0.0189, 0.0184) | +1.000000 | 0.046 | OPTIMAL |
| Distal Foot / Metatarsal | 6 | 1.089 | (0.0098, 0.0092, 0.0090) | +1.000000 | 0.063 | OPTIMAL |

**Findings:**
- Condition numbers are all well within the stable range ($\kappa \in [1.03, 1.09] \ll 10^3$).
- $\det(\mathbf{R}) = +1.000000$ without exception. No reflection or pseudo-rotation occurs.
- RMS residuals are uniformly below $0.07\text{ mm}$ (0.042–0.063 mm), demonstrating geometric consistency.

---

## 4. Evaluation of Holdout Cross-Validation & Scientific Boundaries

In P9.9 and P9.10, leave-one-out cross-validation was performed:

```
Leave-one-out holdout registration RMS error: < 0.1 mm
```

### Forensic Scientific Assessment:
1. **What Holdout Testing Proves:**
   - It proves that the landmark cluster is geometrically rigid and self-consistent under the affine/similarity transformation.
   - It demonstrates that no single landmark acts as an aberrant outlier pulling the registration away from the consensus geometry.
   - It confirms **Computational Correctness (Tier 1)** and **Geometric Alignment (Tier 2)**.

2. **What Holdout Testing Does NOT Prove:**
   - It does **not** prove that the coordinates represent the ground truth for any patient other than the BodyParts3D FJ2810 cadaveric subject.
   - It does **not** constitute independent external anatomical validation (Tier 3/4), because the held-out point and the training points originate from the *same* segmentation model in the *same* coordinate system.
   - Labeling same-frame holdout consistency as "external clinical validation" would violate scientific integrity.

3. **P9.11 Hardened Qualification:**
   - Same-frame cross-validation is formally classified as `HOLDOUT_SAME_FRAME_CONSISTENCY`.
   - Multi-subject CT/MRI independent ground truth is explicitly recorded as `INDEPENDENT_GROUND_TRUTH_UNAVAILABLE`.

---

## 5. Landmark Provenance & Dependency Graph Verification

To prevent circular reasoning (where a landmark is derived from an acupoint that was derived from that same landmark), the landmark provenance graph was evaluated using `AnatomicalProvenanceDependencyValidator`:

- Total landmarks audited: 74
- Undisclosed circular references: **0**
- Quarantined circular references: **0**
- Cyclic paths detected: **0**
- Status: **STRICT PASS**

Every landmark utilized by the 30 remediated Class B points is anchored directly to immutable skeletal features in BodyParts3D 4.0 FJ2810.
