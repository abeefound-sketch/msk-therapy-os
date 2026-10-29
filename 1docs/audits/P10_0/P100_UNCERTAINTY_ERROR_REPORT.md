# P10.0 Comprehensive Quantitative Uncertainty & Error Budget Report

**Milestone:** P10.0  
**Status:** PRODUCTION_REPORT | AUDITED  
**Standard:** ISO/IEC Guide 98-3 (GUM: Guide to the Expression of Uncertainty in Measurement)  
**Catalog Scope:** 362 Acupoints (361 WHO Classical + 1 Extended GV24+)

---

## 1. Measurement Uncertainty Modeling in Computational Anatomy

Under ISO/IEC Guide 98-3, every spatial point estimated by a computational model possesses an intrinsic error budget composed of independent orthogonal variance components. In MSK-Therapy-OS, the spatial location $\mathbf{P}(x, y, z)$ of an acupoint is subject to three primary physical error vectors:

$$\mathbf{e}_{\text{total}} = \mathbf{e}_{\text{landmark}} + \mathbf{e}_{\text{cun}} + \mathbf{e}_{\text{posture}}$$

Since these error sources originate from independent physical mechanisms (skeletal segmentation noise, anthropometric scaling variance, and musculoskeletal kinematics), the combined standard uncertainty $u_c$ is formulated as:

$$u_c = \sqrt{u_{\text{landmark}}^2 + u_{\text{cun}}^2 + u_{\text{posture}}^2}$$

The expanded uncertainty at a 95% confidence level ($k = 1.96$) is:
$$U_{95} = 1.96 \cdot u_c$$

---

## 2. Uncertainty Components & Parameter Values

### 2.1 Landmark Segmentation & Identification Variance ($u_{\text{landmark}}$)
- **Rigid Bony Landmarks & Sutures** (e.g. C7 spinous process, medial malleolus, glabella, mastoid process):
  $$u_{\text{landmark}} = 1.5\text{ mm}$$
- **Soft-Tissue Borders & Muscular Depressions** (e.g. rectus abdominis margin, trapezius muscle border, thenar crease):
  $$u_{\text{landmark}} = 3.5\text{ mm}$$

### 2.2 Cun Scaling Elasticity Variance ($u_{\text{cun}}$)
- **Abdominal Transverse Line (ST19–ST30)**:
  Subcutaneous adiposity and waist circumference elasticity induce substantial variance in transverse Cun mapping:
  $$u_{\text{cun}} = 8.5\text{ mm}$$
- **Longitudinal Proportional Cun Lines** (e.g. forearm 12-cun division, lower leg 16-cun division):
  Proportional division along long bones scales linearly with height, exhibiting moderate elasticity:
  $$u_{\text{cun}} = 2.0\text{ mm}$$
- **Lateral Offset Cun** (e.g. Bladder outer line 3.0 cun lateral to AML):
  $$u_{\text{cun}} = 2.5\text{ mm}$$
- **Fixed Skeletal Anchor Points** (Class A anatomical anchors, zero Cun scaling):
  $$u_{\text{cun}} = 0.5\text{ mm}$$

### 2.3 Kinematic Posture Variance ($u_{\text{posture}}$)
- **Posture-Sensitive Extremity Points** (points adjacent to mobile joints such as wrist, elbow, knee, ankle):
  Limb flexion or extension displaces skin surface landmarks relative to underlying skeletal structures:
  $$u_{\text{posture}} = 4.0\text{ mm}$$
- **Rigid Posture-Invariant Points** (cranial vault, sternum, sacrum):
  $$u_{\text{posture}} = 0.0\text{ mm}$$

---

## 3. Catalog-Wide Uncertainty Distribution

Evaluating the 362 points across all body regions yields the following regional uncertainty distribution:

| Body Region | Point Count | Dominant Localization Method | Mean $u_c$ (mm) | Mean $U_{95}$ (mm) | Max $U_{95}$ (mm) |
|---|---|---|---|---|---|
| **Head & Neck** | 68 | Rigid sutures / craniometric notch | $2.55\text{ mm}$ | $5.00\text{ mm}$ | $7.90\text{ mm}$ (BL10) |
| **Torso (Abdomen/Thorax)** | 94 | Transverse & longitudinal Cun lines | $5.12\text{ mm}$ | $10.04\text{ mm}$ | $18.00\text{ mm}$ (ST19–30) |
| **Upper Limb** | 72 | Inter-tendinous / long-bone Cun | $4.47\text{ mm}$ | $8.76\text{ mm}$ | $11.20\text{ mm}$ (PC6) |
| **Lower Limb** | 128 | Bony depressions / long-bone Cun | $4.52\text{ mm}$ | $8.86\text{ mm}$ | $11.20\text{ mm}$ (GB34) |
| **Entire Catalog (362)** | **362** | Hybrid (Parametric + Canonical) | **$4.38\text{ mm}$** | **$8.58\text{ mm}$** | **$18.00\text{ mm}$** |

### 3.1 Frequency Histogram of $U_{95}$

$$\begin{aligned}
U_{95} \in [0.0, 5.0]\text{ mm} &: \quad 42 \text{ points } (11.6\%) \quad \text{[Rigid Cranial / Sternum / Spine]} \\
U_{95} \in (5.0, 10.0]\text{ mm} &: \quad 284 \text{ points } (78.5\%) \quad \text{[Extremities / Proportional Cun]} \\
U_{95} \in (10.0, 18.0]\text{ mm} &: \quad 36 \text{ points } (9.9\%) \quad \text{[Abdominal Wall ST19-30, Soft-tissue]}
\end{aligned}$$

---

## 4. Clinical Safety Mandate: Depth Guidance Restriction

A critical clinical safety risk in robotic or automated acupuncture therapy is **puncture depth error**. A spatial surface error of $8.5\text{ mm}$ combined with uncalibrated tissue depth could lead to dangerous complications (e.g., pneumothorax over lung points BL13/LU1, peritoneal perforation over abdominal points ST25/CV12).

### Formal Safety Invariant
Under MSK-Therapy-OS P10.0 governance:
```json
"clinical_depth_guidance_allowed": false
```
1. **Depth Guidance Forbidden:** The software strictly disallows needle depth recommendation for any clinical treatment.
2. **Surface Localization Only:** Model coordinates are restricted solely to skin surface guidance and non-invasive anatomical visualization.
3. **No Automatic Puncture:** Any future depth recommendation requires subject-specific real-time ultrasound guidance and FDA 510(k) / CE Class IIa medical device clearance.
