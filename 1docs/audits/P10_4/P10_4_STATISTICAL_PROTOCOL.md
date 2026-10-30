# P10.4 SCIENTIFIC STATISTICAL ANALYSIS PLAN & PROTOCOL REPORT

**Milestone:** P10.4 — Independent Release Certification, Institutional Pilot Integration & Evidence Reproducibility  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Document Type:** Prespecified Statistical Analysis Plan (SAP) & Validation Protocol Draft  
**Lead Auditor / Role:** Biostatistical Validation Engineer & Scientific Validation Lead  
**Audit Date:** 2026-10-30  
**Gate P405 Verdict:** **PASS**

---

## 1. Executive Summary

Milestone P10.4 establishes a prespecified, mathematically rigorous Statistical Analysis Plan (SAP) governing any future external empirical validation of the MSK-Therapy-OS 3D meridian and computational anatomy atlas. This protocol establishes statistical power requirements, cluster correlation adjustments, multiple comparisons risk mitigation, and scanner heterogeneity controls.

---

## 2. Prespecified Cohort Sample Sizing & Power Analysis

The proposed empirical validation protocol allocates samples across three anatomical cohorts:

| Cohort Identifier | Target Anatomy | Minimum Subjects ($N$) | Minimum Landmarked Points | Intra-Subject Cluster Points | Total Observations |
|---|---|---|---|---|---|
| `COHORT_A_HEAD_NECK_CT` | Cranium & Cervical Spine | $N \ge 30$ | 12 points | Bilateral + Midline | $\ge 360$ observations |
| `COHORT_B_KNEE_EXTREMITY_MRI` | Knee & Lower Extremity | $N \ge 25$ | 10 points | Bilateral | $\ge 250$ observations |
| `COHORT_C_UPPER_LIMB_CT_MRI` | Forearm & Hand/Wrist | $N \ge 30$ | 13 points | Bilateral | $\ge 390$ observations |
| **Combined Target** | **Whole Body Regional** | **$N \ge 85$ subjects** | **35 benchmark points** | **Multi-tier** | **$\ge 1,000$ observations** |

### 2.1 Power Justification
- **Null Hypothesis ($H_0$):** The true population Mean Radial Error $\mu \ge 3.0\text{ mm}$ (Atlas exceeds clinical non-inferiority margin).
- **Alternative Hypothesis ($H_1$):** The true population Mean Radial Error $\mu < 3.0\text{ mm}$.
- **Effect Size Assumptions:** Expected mean error under calibrated rules $\mu_1 = 1.60\text{ mm}$, standard deviation $\sigma = 1.20\text{ mm}$.
- **Intraclass Correlation (ICC):** Accounting for intra-subject clustering $\rho = 0.35$ across landmarks within the same patient.
- **Design Effect ($DE$):** For an average cluster size $m = 12$ points per subject:
  $$DE = 1 + (m - 1)\rho = 1 + (11)(0.35) = 4.85$$
- **Effective Sample Size ($N_{\text{eff}}$):** With $N = 85$ subjects and $M \approx 1,000$ observations, $N_{\text{eff}} = \frac{1000}{4.85} \approx 206$ independent degrees of freedom.
- **Statistical Power:** At $\alpha = 0.05$ (one-sided), $N_{\text{eff}} \ge 200$ yields $>99.9\%$ statistical power to reject $H_0$ if the true mean error is $\le 2.0\text{ mm}$.

---

## 3. Statistical Methodology

### 3.1 Cluster Bootstrap Resampling
Because multiple landmark observations are clustered within individual subjects, standard naive IID (independent and identically distributed) confidence intervals underestimate standard errors.
- **Resampling Unit:** Subject ID (cluster level), not individual observations.
- **Number of Replications:** Prespecified benchmark at $B = 1,000$ bootstrap iterations.
- **Seed Standard:** Deterministic evaluation seed `20261030`.
- **Interval Estimation:** Empirical percentile method:
  $$\text{CI}_{95\%} = \left[ P_{2.5}^*, P_{97.5}^* \right]$$

### 3.2 Multiple Comparisons Control
When evaluating 35 distinct acupoints simultaneously:
- **Family-Wise Error Rate (FWER):** Controlled via Bonferroni adjustment for primary equivalence endpoints ($\alpha_{\text{adjusted}} = \frac{0.05}{35} = 0.00143$).
- **False Discovery Rate (FDR):** Secondary point-by-point diagnostic screening utilizes the Benjamini-Hochberg procedure at $q = 0.05$.

### 3.3 Site and Scanner Heterogeneity Control
Multi-institutional data will exhibit inter-site variability due to differing scanner manufacturers (GE, Siemens, Philips) and reconstruction protocols:
- Fixed-effects analysis of variance (ANOVA) across imaging modalities.
- Random-effects mixed linear models with `site_id` and `scanner_model` as random intercepts to quantify variance components attributable to scanner hardware.

---

## 4. Prespecified Clinical Acceptance Criteria

To be eligible for empirical release, any external empirical dataset must satisfy all of the following prespecified thresholds on the **locked holdout partition (30%)**:

1. **Mean Radial Error:** $\le 3.0\text{ mm}$ across all evaluated points.
2. **Root Mean Square Error (RMSE):** $\le 4.0\text{ mm}$.
3. **95th Percentile Radial Error (P95):** $\le 6.0\text{ mm}$.
4. **Upper Bound of 95% Bootstrap CI:** $\text{RMSE}_{\text{upper}} \le 4.5\text{ mm}$.
5. **Gross Outlier Ratio ($>10\text{ mm}$):** $\le 2.0\%$ of all observations.

---

## 5. Epistemological Boundary Disclaimer

Software implementation of statistical algorithms does **NOT** constitute execution of the statistical protocol. Statistical analysis requires genuine external empirical datasets acquired under approved Data Use Agreements and IRB protocols. In the absence of such data, Gate G14 remains strictly `BLOCKED_EXTERNAL_DATA`.

Gate P405 is certified as **PASS** based on complete mathematical specification and reference implementation reproducibility.
