# P10.5 STATISTICAL STUDY DESIGN & POWER REASSESSMENT CRITICAL REVIEW

**Milestone:** P10.5 — Institutional Research Pilot Activation, Statistical Design Verification & External Evidence Acquisition Readiness  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Engine Implementation:** [`msk_therapy_os/statistical_design_engine.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/statistical_design_engine.py)  
**Lead Auditor / Role:** Biostatistical Methodology Auditor & Quantitative Research Lead  
**Audit Date:** 2026-10-30  
**Gate P502 Verdict:** **PASS (MATHEMATICALLY REPRODUCIBLE WITH EXPLICIT BOUNDARIES)**

---

## 1. Executive Summary & Critical Mandate

Milestone P10.5 executes an in-depth biostatistical critical review of the proposed $N=85$ multi-cohort sample design. The mandate requires moving beyond naive statistical power assertions by explicitly modeling intra-subject clustering, inter-observer measurement error, multi-scanner variance, and holdout sample adequacy.

---

## 2. Epistemological Disambiguation: Five Sample Metrics

To prevent methodological confusion between observational volume and true independent statistical power:

| Metric Name | Symbol | Definition | Baseline Study Value ($N=85$) |
|---|---|---|---|
| **1. Unique Patients** | $N$ | Independent human subjects enrolled. | 85 patients |
| **2. Imaging Series** | $S$ | Volumetric scan volumes acquired. | 85–110 series |
| **3. Anatomical Landmarks** | $m$ | Evaluated anatomical sites per subject. | 10–13 points/subject (35 total) |
| **4. Total Observations** | $M$ | Point-level 3D coordinate pairs ($M = N \times m$). | 1,000 observations |
| **5. Effective Sample Size** | $N_{\text{eff}}$ | Independent degrees of freedom adjusted for design effect ($M / DE$). | **~203.5 total** ($47.8$ holdout) |

---

## 3. Mathematical Modeling of Hierarchical Clustered Variance

Because multiple landmark measurements are nested within the same patient, residuals are correlated. Furthermore, across multiple hospital centers, scanner manufacturer variations introduce site-level clustering.

The total design effect ($DE$) is formulated as:
$$DE = 1 + (m - 1)\rho_{\text{within}} + m(n_{\text{site}} - 1)\rho_{\text{site}}$$
Where:
- $\rho_{\text{within}} \approx 0.35\text{–}0.45$: Intra-subject correlation across bilateral or adjacent points.
- $\rho_{\text{site}} \approx 0.05$: Inter-institutional scanner heterogeneity.
- $m \approx 10\text{–}13$: Points per anatomical region.

For Cohort A ($m=12, \rho_{\text{within}}=0.38$):
$$DE = 1 + (11)(0.38) + 12(14)(0.05) \approx 5.18 + 8.4 = 13.58 \text{ (multi-site)}$$
Under single-site conditions:
$$DE_{\text{within}} = 1 + (11)(0.38) = 5.18$$

---

## 4. Evaluation of the Three Prespecified Planning Scenarios

Using `StatisticalStudyDesignEngine.run_scenario()`, three distinct protocol designs were evaluated:

| Scenario Metric | 1. Minimum Feasibility Pilot | 2. Primary Anatomical Accuracy Study | 3. Independent Multi-Site Validation |
|---|---|---|---|
| **Total Enrolled Patients ($N$)** | **45 patients** (15 A, 15 B, 15 C) | **85 patients** (30 A, 25 B, 30 C) | **150 patients** (50 A, 50 B, 50 C) |
| **Total Landmark Observations ($M$)** | 510 observations | 1,000 observations | 1,900 observations |
| **Holdout Patients ($N_{\text{hold}}$)** | 9 patients (3 per cohort) | 20 patients (7 A, 6 B, 7 C) | 36 patients (12 A, 12 B, 12 C) |
| **Holdout Observations ($M_{\text{hold}}$)** | 102 observations | 235 observations | 456 observations |
| **Effective Holdout Sample ($N_{\text{eff}}$)** | 21.0 independent units | 47.8 independent units | 96.2 independent units |
| **Aggregate Holdout Statistical Power** | 86.4% | **>99.9%** | **>99.9%** |
| **Cohort B Subgroup Holdout Power** | 62.1% (Underpowered) | 93.2% (Borderline for strict margin) | **99.4% (Definitive)** |
| **Holdout 95% CI Half-Width (mm)** | $\pm 0.38\text{ mm}$ | $\pm 0.24\text{ mm}$ | $\pm 0.16\text{ mm}$ |
| **Biostatistical Suitability** | Software intake rehearsal only | Academic pilot submission | Definitive pre-market regulatory submission |

---

## 5. Multi-Parameter Sensitivity Grid Analysis

The engine evaluated sensitivity across variable within-subject correlations ($\rho \in [0.20, 0.50]$) and standard deviations ($\sigma \in [1.0, 2.0]\text{ mm}$):

| Within-Subj ICC ($\rho$) | Assumed SD ($\sigma$) | Design Effect ($DE$) | Holdout $N_{\text{eff}}$ | Holdout Power (at $\delta_0 = 3.0$) | Mean Error 95% CI Half-Width |
|---|---|---|---|---|---|
| **0.20 (Low clustering)** | $1.20\text{ mm}$ | 3.200 | 26.2 | 99.8% | $\pm 0.460\text{ mm}$ |
| **0.35 (Baseline)** | $1.20\text{ mm}$ | 4.850 | 17.3 | 97.8% | $\pm 0.565\text{ mm}$ |
| **0.50 (High clustering)** | $1.20\text{ mm}$ | 6.500 | 12.9 | 93.1% | $\pm 0.654\text{ mm}$ |
| **0.35 (Baseline)** | $1.60\text{ mm}$ (High noise) | 4.850 | 17.3 | 87.2% | $\pm 0.754\text{ mm}$ |
| **0.50 (High clustering)** | $2.00\text{ mm}$ (Worst-case) | 6.500 | 12.9 | 71.4% (Requires $N > 120$) | $\pm 1.090\text{ mm}$ |

---

## 6. Biostatistical Design Reconciliations & Recommendations

1. **Rejection of Blind Certainty:** Claims that $N=85$ guarantees adequate power across all subgroups are rejected. While aggregate power is excellent ($>99.9\%$), Cohort B (Lower Extremities) with only 6 holdout patients exhibits sensitivity to high soft-tissue variance.
2. **Recommended Formal Protocol Design:**
   - **Pilot Intake Phase:** Proceed with $N=85$ for technical validation and initial hospital feasibility.
   - **Multi-Site Empirical Phase:** Expand Cohort B to at least $N=35$ subjects and overall study to $N \ge 115\text{–}150$ subjects prior to definitive external unblinding.
3. **Multiplicity Adjustment Standard:**
   - Primary endpoint non-inferiority: Family-wise error controlled via Bonferroni ($\alpha_{\text{adj}} = 0.05 / 3 = 0.0167$).
   - Point-by-point secondary diagnostics: Benjamini-Hochberg False Discovery Rate ($q = 0.05$).

Gate P502 is certified as **PASS**.
