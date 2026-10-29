# P9.9 Kidney Distal Foot Remediation Report

## 1. Executive Summary
This report documents the evidence-driven anatomical calibration and remediation of the six distal points of the Kidney Meridian of Foot Shaoyin (`KI1` through `KI6`) in MSK-Therapy-OS milestone P9.9. Prior to P9.9, `KI2`, `KI4`, and `KI5` were uncalibrated legacy raycast points (Class D), while `KI1` suffered from an outward-pointing normal rather than a downward-pointing plantar normal. In P9.9, all six points are grounded upon independent skeletal and soft-tissue geometry, achieving 100% Class B compliance for the distal kidney chain.

---

## 2. Anatomical Foundations & Point-by-Point Calibration

### 2.1 KI1 (Yongquan - 涌泉)
- **WHO 2008 Standard (p. 149):** On the sole of the foot, in the depression formed when the foot is in plantar flexion, at the junction of the anterior one-third and posterior two-thirds of the line connecting the web margin between the 2nd and 3rd toes and the heel.
- **Remediation Action:**
  - Grounded upon `LM_PLANTAR_METATARSAL_INTERVAL_R` $(0.0420, 0.0120, 0.0680)$ at the inter-metatarsal depression between metatarsals 2 and 3.
  - **Surface Normal Direction:** Corrected from generic outward radial raycast to true plantar orientation pointing downward into the supporting ground surface:
    $$\vec{N}_{\text{KI1}} = (0.0000, -0.9900, -0.1400)$$
  - **Quality Class:** **CLASS_B**

### 2.2 KI2 (Rangu - 然谷)
- **WHO 2008 Standard (p. 150):** On the medial aspect of the foot, in the depression anteroinferior to the tuberosity of the navicular bone, at the border between the red and white flesh.
- **Remediation Action:**
  - Formulated as a parametric interpolation along the medial longitudinal arch between `LM_NAVICULAR_TUBEROSITY_R` and `LM_METATARSAL1_BASE_R` (fraction 0.35).
  - Derived Position: $(0.06425, 0.05654, 0.01977)$.
  - **Quality Class:** **CLASS_B** (Elevated from Class D).

### 2.3 KI3 (Taixi - 太溪)
- **WHO 2008 Standard (p. 151):** On the posteromedial aspect of the ankle, in the depression between the prominence of the medial malleolus and the calcaneal tendon.
- **Remediation Action:**
  - Interpolated between `LM_MED_MALLEOLUS_R` and `LM_CALCANEUS_POST_R` at fraction 0.45.
  - Derived Position: $(0.09040, 0.05590, -0.02235)$.
  - **Quality Class:** **CLASS_B** (Re-calibrated with sub-millimeter anchor coordinates).

### 2.4 KI4 (Dazhong - 大钟)
- **WHO 2008 Standard (p. 151):** On the posteromedial aspect of the ankle, posteroinferior to the medial malleolus, in the depression anterior to the medial attachment of the calcaneal tendon.
- **Remediation Action:**
  - Interpolated along the posteroinferior trajectory from `LM_MED_MALLEOLUS_R` toward `LM_CALCANEUS_MEDIAL_TUBEROSITY_R` (fraction 0.40).
  - Derived Position: $(0.06080, 0.06560, -0.01580)$.
  - **Quality Class:** **CLASS_B** (Elevated from Class D).

### 2.5 KI5 (Shuiquan - 水泉)
- **WHO 2008 Standard (p. 152):** On the medial aspect of the foot, 1 B-cun directly inferior to KI3, in the depression anterosuperior to the medial process of the calcaneal tuberosity.
- **Remediation Action:**
  - Anchored directly on the palpable depression anterosuperior to `LM_CALCANEUS_MEDIAL_TUBEROSITY_R` $(0.0380, 0.0410, -0.0620)$.
  - Derived Position: $(0.03800, 0.04100, -0.06200)$.
  - **Quality Class:** **CLASS_B** (Elevated from Class D).

### 2.6 KI6 (Zhaohai - 照海)
- **WHO 2008 Standard (p. 153):** On the medial aspect of the foot, in the depression 1 B-cun directly inferior to the prominence of the medial malleolus.
- **Remediation Action:**
  - Interpolated directly inferior to `LM_MED_MALLEOLUS_R` toward the medial calcaneal process (fraction 0.25).
  - Derived Position: $(0.06650, 0.07175, -0.00425)$.
  - **Quality Class:** **CLASS_B** (Re-calibrated).

---

## 3. Comparative Summary Table

| Point Code | Name (EN / ZH / VI) | Predecessor (P9.8) | P9.9 Quality | Canonical Position $(X, Y, Z)$ | Surface Normal $(N_x, N_y, N_z)$ |
|---|---|---|---|---|---|
| **KI1** | Yongquan / 涌泉 / Dũng Tuyền | Class B | **CLASS_B** | $(0.04200, 0.01200, 0.06800)$ | $(0.00000, -0.99000, -0.14000)$ |
| **KI2** | Rangu / 然谷 / Nhiên Cốc | Class D | **CLASS_B** | $(0.06425, 0.05654, 0.01977)$ | $(0.53325, 0.82990, 0.16407)$ |
| **KI3** | Taixi / 太溪 / Thái Khê | Class B | **CLASS_B** | $(0.09040, 0.05590, -0.02235)$ | $(0.66157, 0.73183, -0.16356)$ |
| **KI4** | Dazhong / 大钟 / Đại Chung | Class D | **CLASS_B** | $(0.06080, 0.06560, -0.01580)$ | $(0.51484, 0.84678, -0.13379)$ |
| **KI5** | Shuiquan / 水泉 / Thủy Tuyền | Class D | **CLASS_B** | $(0.03800, 0.04100, -0.06200)$ | $(0.30733, 0.80877, -0.50144)$ |
| **KI6** | Zhaohai / 照海 / Chiếu Hải | Class B | **CLASS_B** | $(0.06650, 0.07175, -0.00425)$ | $(0.42553, 0.63989, 0.63989)$ |

Visual proof captured in `2data/evidence/p9_9_registration/03_p99_kidney_distal_foot_plantar_ki1_ki6.png`.
