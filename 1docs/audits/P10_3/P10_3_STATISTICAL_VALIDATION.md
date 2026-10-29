# P10.3 QUANTITATIVE STATISTICAL VALIDATION & BOOTSTRAP AUDIT
## Metric Formulations, Cluster Bootstrap Resampling, Intra-Class Correlation, and Power Analysis

> **CLASSIFICATION:** QUANTITATIVE VALIDATION & BIOSTATISTICS AUDIT  
> **MILESTONE:** P10.3A  
> **COMPONENT:** `validate_catalog()` & `compute_subject_bootstrap_ci()` in `msk_therapy_os/anatomical_validation.py`  
> **STATUS:** PASSED — RIGOROUS QUANTITATIVE METRICS VERIFIED

---

## 1. Executive Summary & Biostatistical Scope

Milestone P10.3A establishes a comprehensive biostatistical evaluation engine designed for clinical imaging validation. Unlike simple regression metrics, medical anatomical validation must account for:
1. **Cluster Correlation:** Multiple landmark observations from the same patient are correlated (shared body habitus, posture, scanner distortion).
2. **Heavy-Tailed Skewness:** Cutaneous landmark errors are strictly non-negative ($e_i \ge 0$) and frequently exhibit positive skewness, violating standard Gaussian assumptions.
3. **Multi-Directional Spatial Biases:** Systematic lateral, cranial, or ventral model offsets must be decomposed as 3D vectors.
4. **Subject-Level Cluster Bootstrapping:** Empirical 95% Confidence Intervals derived from 1,000 patient-level resamples.

---

## 2. Mathematical Metric Formulations

### 2.1 Primary Error Residuals & Aggregations
For $N$ observations where $\mathbf{p}_i^{\text{model}}$ is the predicted coordinate and $\mathbf{p}_i^{\text{ref}}$ is the consensus reference coordinate in millimeters:
$$e_i = \|\mathbf{p}_i^{\text{model}} - \mathbf{p}_i^{\text{ref}}\|_2 = \sqrt{(x_i^m - x_i^r)^2 + (y_i^m - y_i^r)^2 + (z_i^m - z_i^r)^2}$$

- **Root Mean Square Error (RMSE):**
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} e_i^2}$$
- **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} e_i$$
- **Median & 95th Percentile ($P_{95}$):**
  $$\text{Median} = \text{Percentile}_{50}(e), \quad P_{95} = \text{Percentile}_{95}(e)$$

### 2.2 3D Spatial Bias Vector & Bilateral Asymmetry
- **Bias Vector $\boldsymbol{\Delta}$ (in mm):**
  $$\boldsymbol{\Delta} = [\Delta X, \Delta Y, \Delta Z] = \left[ \frac{1}{N}\sum (x_i^m - x_i^r), \; \frac{1}{N}\sum (y_i^m - y_i^r), \; \frac{1}{N}\sum (z_i^m - z_i^r) \right]$$
- **Bilateral Asymmetry Differential:**
  $$\Delta_{\text{sym}} = |\text{RMSE}_{\text{Left}} - \text{RMSE}_{\text{Right}}|$$

### 2.3 Nonparametric Outlier Distribution (IQR)
- $Q_1 = \text{Percentile}_{25}(e)$, $Q_3 = \text{Percentile}_{75}(e)$, $\text{IQR} = Q_3 - Q_1$
- Outlier Threshold Fence:
  $$\text{Fence}_{\text{upper}} = Q_3 + 1.5 \times \text{IQR}$$
  Observations with $e_i > \text{Fence}_{\text{upper}}$ are flagged as anomalous anatomical outliers.

---

## 3. Normal Approximation vs. Subject-Level Cluster Bootstrap

### 3.1 Limitation of Normal Approximation Confidence Intervals
Standard software often computes 95% confidence intervals using:
$$\text{CI}_{\text{normal}} = \bar{e} \pm 1.96 \cdot \frac{s}{\sqrt{N}}$$
**This approximation is fundamentally invalid for clustered anatomical data:**
1. It assumes independent and identically distributed (i.i.d.) observations, ignoring patient-level clustering.
2. It assumes symmetrical Gaussian dispersion, occasionally producing impossible negative lower bounds ($\text{CI}_{\text{lower}} < 0$).

### 3.2 Subject-Level Cluster Bootstrap Algorithm
The method `compute_subject_bootstrap_ci()` solves this:
1. Let $\mathcal{S} = \{S_1, S_2, \dots, S_K\}$ be the set of $K$ unique patient pseudonyms.
2. For $b = 1, \dots, B$ (with $B = 1000$ replications):
   - Draw a sample $\mathcal{S}^{*(b)}$ of size $K$ from $\mathcal{S}$ **with replacement**.
   - Pool all landmark observation residuals belonging to subjects in $\mathcal{S}^{*(b)}$.
   - Compute replication RMSE: $\text{RMSE}^{*(b)} = \sqrt{\frac{1}{M_b} \sum e^2}$.
3. Sort the bootstrap estimates: $\text{RMSE}^{*(1)} \le \dots \le \text{RMSE}^{*(B)}$.
4. Determine empirical 95% Confidence Interval:
   $$\text{CI}_{95\%}^{\text{boot}} = \left[ \text{RMSE}^{*(\lfloor 0.025 B \rfloor)}, \; \text{RMSE}^{*(\lfloor 0.975 B \rfloor)} \right]$$

---

## 4. Power Analysis & Clustered Sample Size Recalculation

A critical audit finding from P10.2 was that treating 43 landmark observations as equivalent to 43 independent subjects was invalid.

### 4.1 Intra-Cluster Correlation (ICC) & Design Effect
Landmarks measured on the same subject share inter-subject variance:
$$\text{ICC} = \frac{\sigma_{\text{between}}^2}{\sigma_{\text{between}}^2 + \sigma_{\text{within}}^2}$$
If each subject provides $m$ landmark observations, the **Design Effect ($D_{\text{eff}}$)** is:
$$D_{\text{eff}} = 1 + (m - 1) \cdot \text{ICC}$$
And the **Effective Independent Sample Size ($N_{\text{eff}}$)** is:
$$N_{\text{eff}} = \frac{N_{\text{total}}}{D_{\text{eff}}} = \frac{K \cdot m}{1 + (m - 1) \cdot \text{ICC}}$$

### 4.2 Revised Sample Size Requirement:
To achieve statistical power $(1 - \beta) = 0.80$ at significance $\alpha = 0.05$ to detect a meaningful deviation $\delta = 1.5\text{ mm}$:
$$K_{\text{subjects}} \ge \frac{(Z_{\alpha/2} + Z_\beta)^2 \cdot \sigma^2}{\delta^2} \cdot \left[ \frac{1 + (m - 1) \cdot \text{ICC}}{m} \right]$$
Assuming $\text{ICC} \approx 0.40$ and $m = 10$ points per patient:
$$D_{\text{eff}} = 1 + 9 \times 0.40 = 4.6$$
$$\implies \text{A minimum of } K \ge 30\text{ to } 43\text{ INDEPENDENT SUBJECTS is required (not merely 43 observations).}$$

---

## 5. Preregistered Cohort Acceptance Thresholds

| Pilot Cohort | Primary Region | Preregistered Acceptance ($\text{RMSE}$) | High-Accuracy Target ($\text{RMSE}$) | Current Empirical Status |
|---|---|---|---|---|
| **Cohort A** | Abdomen (ST19–ST30) | $\le 10.0\text{ mm}$ | $\le 5.0\text{ mm}$ | **BLOCKED_EXTERNAL_DATA** |
| **Cohort B** | Bilateral Extremities | $\le 10.0\text{ mm}$ | $\le 5.0\text{ mm}$ | **BLOCKED_EXTERNAL_DATA** |
| **Cohort C** | Craniofacial (Yintang/GV24+) | $\le 5.0\text{ mm}$ | $\le 3.0\text{ mm}$ | **BLOCKED_EXTERNAL_DATA** |

These thresholds are pre-registered research criteria, not autonomous clinical safety standards.

---

## 6. Audit Conclusion & Gate E Certification

| Test Case | Description | Result |
|---|---|---|
| Complete Metric Output | RMSE, MAE, Bias Vector, Bilateral Asymmetry | **PASS** |
| Outlier IQR Calculation | Correct $Q_1, Q_3, \text{IQR}$, and upper fence detection | **PASS** |
| ICC & Effective Sample Size | Correct calculation of $D_{\text{eff}}$ and $N_{\text{eff}}$ | **PASS** |
| Subject Bootstrap CI | 1000 resamples yield valid empirical $[L, U]$ | **PASS** |
| Insufficient Sample Protection | Blocks bootstrap when $K < 3$ subjects | **PASS** |

**Gate E Verdict:** **PASS**. Quantitative statistical validation engine is mathematically verified, cluster-aware, and reproducible.
