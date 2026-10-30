# P10.4B STATISTICAL POWER & SAMPLE ALLOCATION REASSESSMENT

**Milestone:** P10.4B — Institutional Pilot Activation, External Evidence Preparation & Scientific Readiness  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Calculation Engine:** [`msk_therapy_os/statistical_power.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/statistical_power.py)  
**Lead Auditor / Role:** Biostatistical Methods Reviewer & Computational Anatomy Lead  
**Audit Date:** 2026-10-30  
**Gate B402 Sub-Evaluation:** **PASS (MATHEMATICALLY REPRODUCIBLE)**

---

## 1. Executive Summary

Milestone P10.4B executes a rigorous biostatistical re-evaluation of the pilot sample-size allocation proposed in P10.3 and P10.4. Specifically, this analysis investigates whether a 25% holdout partition (yielding $N \approx 6\text{–}8$ subjects per cohort) provides sufficient statistical power to estimate cohort-specific Root Mean Square Error (RMSE) and 95% confidence intervals against prespecified clinical equivalence margins ($\text{Mean Error} \le 3.0\text{ mm}$, $\text{RMSE} \le 4.0\text{ mm}$).

---

## 2. Definitional Precision: Five Distinct Sample Metrics

To prevent methodological ambiguity, all statistical protocols must explicitly distinguish:

1. **Number of Patients ($N$):** Unique human individuals enrolled in the study.
2. **Number of Imaging Studies:** Radiological acquisitions (typically 1 scan volume per patient; occasionally dual-modality).
3. **Number of Landmarks ($m$):** Distinct anatomical sites annotated per subject (12 in Cohort A, 10 in Cohort B, 13 in Cohort C).
4. **Total Observations ($M$):** $M = N \times m$ individual 3D coordinate measurements.
5. **Effective Independent Sample Size ($N_{\text{eff}}$):** Sample size adjusted for intra-subject clustering:
   $$N_{\text{eff}} = \frac{M}{\text{Design Effect}} = \frac{N \times m}{1 + (m - 1)\rho}$$
   where $\rho$ is the intraclass correlation coefficient (ICC).

---

## 3. Baseline Sizing Analysis (85 Total Patients, 50/25/25 Partition)

Under the reported baseline design ($N=30$ for A, $N=25$ for B, $N=30$ for C):

| Cohort | Anatomy | Patients ($N$) | Points ($m$) | Obs ($M$) | Intra-Subj ICC ($\rho$) | Design Effect ($DE$) | Effective $N_{\text{total}}$ | Holdout Patients ($N_{\text{hold}}$) | Holdout Obs | Effective Holdout $N_{\text{eff}}$ | Holdout Statistical Power | Holdout 95% CI Half-Width (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Cohort A** | Head & Neck CT | 30 | 12 | 360 | 0.35 | 4.850 | 74.2 | 7 | 84 | 17.3 | **97.8%** | $\pm 0.400\text{ mm}$ |
| **Cohort B** | Knee MRI | 25 | 10 | 250 | 0.40 | 4.600 | 54.3 | 6 | 60 | 13.0 | **93.2%** | $\pm 0.461\text{ mm}$ |
| **Cohort C** | Upper Limb CT/MRI| 30 | 13 | 390 | 0.35 | 5.200 | 75.0 | 7 | 91 | 17.5 | **97.9%** | $\pm 0.398\text{ mm}$ |
| **Aggregate**| **All Regions** | **85** | **35** | **1,000** | **~0.37** | **~4.88** | **203.5** | **20** | **235** | **47.8** | **>99.9%** | $\pm 0.241\text{ mm}$ |

### Finding on Holdout Sufficiency:
- At the **aggregate level** ($N=20$ holdout patients, 235 holdout observations, $N_{\text{eff}} = 47.8$), statistical power exceeds $99.9\%$, with high estimation precision ($\text{CI half-width} \approx \pm 0.24\text{ mm}$).
- At the **cohort-specific level**, Cohort B with only $N_{\text{hold}} = 6$ patients ($N_{\text{eff}} = 13.0$) achieves $93.2\%$ power, but exhibits a broader CI half-width ($\pm 0.46\text{ mm}$). While acceptable under minimum exploratory pilot criteria, expanding Cohort B is strongly recommended for definitive regulatory acceptance.

---

## 4. Alternative Allocation Strategy: Expanded Robust Pilot ($N=115$)

To guarantee that each cohort holdout contains at least $N_{\text{hold}} \ge 10\text{–}12$ independent subjects and $\ge 100$ holdout observations:

| Strategy | Cohort A ($N$) | Cohort B ($N$) | Cohort C ($N$) | Total $N$ | Partition Ratio (Calib/Tune/Hold) | Holdout Patients | Holdout Power (Cohort B) | Recommended Purpose |
|---|---|---|---|---|---|---|---|---|
| **Option 1 (Baseline)** | 30 | 25 | 30 | **85** | 50% / 25% / 25% | 20 patients | 93.2% | Feasibility / Pilot Rehearsal |
| **Option 2 (Balanced Holdout)** | 30 | 30 | 30 | **90** | 40% / 30% / 30% | 27 patients | 97.5% | Balanced Multi-Center Pilot |
| **Option 3 (Expanded Robust)** | 40 | 35 | 40 | **115** | 50% / 20% / 30% | 35 patients | **99.4%** | Definitive Empirical Submission |

---

## 5. Formal Biostatistical Recommendation

1. **Phase 1 Pilot Rehearsal:** Proceed with the baseline $N=85$ allocation for software verification and initial hospital intake rehearsals.
2. **Phase 2 Empirical Protocol Registration:** When executing multi-center data agreements, prespecify **Option 3 ($N=115$)** to prevent underpowered sub-group evaluations in complex extremities (Knee/Ankle in Cohort B).
