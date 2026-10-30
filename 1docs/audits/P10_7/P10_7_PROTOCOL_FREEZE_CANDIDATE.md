# MSK-THERAPY-OS — RESEARCH PROTOCOL & STATISTICAL ANALYSIS PLAN
## Version: v1.0-RC-P10.7 (Protocol Freeze Candidate)

> [!IMPORTANT]
> **GOVERNANCE STATUS: `PROTOCOL_FREEZE_CANDIDATE / EXTERNAL_REVIEW_REQUIRED`**  
> This protocol and Statistical Analysis Plan (SAP) represent a versioned, canonically frozen candidate specification. It has **NOT** been approved by an external institutional review board (IRB), ethics committee (IEC), or independent biostatistician. Zero empirical clinical data may be ingested or analyzed under this protocol until all prerequisite external authorizations are verifiably executed.

**Canonical SHA-256 Manifest Digest:**  
`7a1da2a0f959ea7ab5125c37f8e996b5abec318e9d3978c3150f65a6944f3a31`

**Release Tag:** `v2.1.0-local-rc3`  
**Date of Freeze Candidate Generation:** 2026-10-30  
**Target Software Engine:** MSK-Therapy-OS Multicenter Offline Validation Pipeline  

---

## 1. Scientific Objective & Primary Estimand

### 1.1 Objective
To quantitatively evaluate the spatial registration accuracy of the MSK-Therapy-OS 3D computational anatomy atlas against independent, dual-radiologist consensus osseous and soft-tissue landmarks derived from de-identified clinical DICOM series across three prespecified anatomical regions.

### 1.2 Primary Estimand
The population mean 3D Euclidean registration error ($\mu_{\text{error}}$, in millimeters) between algorithmically registered atlas landmark coordinates $\mathbf{x}_{\text{algo}, ij}$ and independent human expert consensus coordinates $\mathbf{x}_{\text{consensus}, ij}$ across prespecified anatomical landmarks $j=1, \dots, m_i$ evaluated exclusively on an unblinded $30\%$ holdout cohort:

$$\mu_{\text{error}} = \mathbb{E}\left[ \|\mathbf{x}_{\text{algo}, ij} - \mathbf{x}_{\text{consensus}, ij}\|_2 \right]$$

### 1.3 Hypotheses
The primary statistical test evaluates one-sided non-inferiority against a prespecified clinically acceptable boundary $\Delta_0 = 3.00\text{ mm}$:

$$H_0: \mu_{\text{error}} \ge 3.00\text{ mm} \quad \text{vs.} \quad H_1: \mu_{\text{error}} < 3.00\text{ mm}$$

---

## 2. Anatomical Landmark Definitions

Validation is conducted strictly on verifiable physical anatomical structures, NOT on inferred acupoints:

### Cohort A: Head & Cervical Spine (CT)
1. **NASION:** Midpoint of the nasofrontal suture in the mid-sagittal plane.
2. **INION:** Most prominent point of the external occipital protuberance at the posterior skull base.
3. **GLABELLA:** Most anterior midpoint prominence between superciliary arches.
4. **MASTOID_PROCESS_L / R:** Inferiormost apex of the left and right mastoid processes of the temporal bones.
5. **C7_SPINOUS_PROCESS:** Dorsal-most tip of the spinous process of the 7th cervical vertebra.

### Cohort B: Knee Joint & Lower Extremity (MRI)
1. **TIBIAL_TUBEROSITY:** Apex of the anterior osseous tuberosity of the proximal tibia.
2. **PATELLA_INFERIOR_POLE:** Distalmost osseous apex of the patella at the patellar tendon origin.
3. **MEDIAL_FEMORAL_EPICONDYLE:** Maximum osseous convexity on the medial aspect of the medial femoral condyle.
4. **LATERAL_FEMORAL_EPICONDYLE:** Maximum osseous convexity on the lateral aspect of the lateral femoral condyle.
5. **HEAD_OF_FIBULA:** Superiormost lateral tip of the proximal fibular head.
6. **MEDIAL_MALLEOLUS_TIP:** Inferiormost point of the medial ankle malleolus.

### Cohort C: Upper Extremity & Forearm (CT or MRI)
1. **RADIAL_STYLOID:** Distalmost osseous point of the styloid process of the radius.
2. **ULNAR_STYLOID:** Distalmost osseous point of the styloid process of the ulna.
3. **BICEPS_TENDON_DISTAL:** Center of distal biceps tendon insertion at the radial tuberosity.
4. **MEDIAL_HUMERAL_EPICONDYLE:** Medialmost prominence of the distal humerus.
5. **LATERAL_HUMERAL_EPICONDYLE:** Lateralmost prominence of the distal humerus.

---

## 3. Imaging Modality & Acquisition Requirements

| Parameter | Cohort A (Head/Neck) | Cohort B (Knee/Leg) | Cohort C (Upper Extremity) |
| :--- | :--- | :--- | :--- |
| **Primary Modality** | Volumetric CT | 1.5T or 3.0T MRI | High-Resolution CT or MRI |
| **Field of View (FOV)** | Full cranium to C7 included | Distal femur to proximal tibia | Distal humerus to carpal bones |
| **Max Slice Thickness** | $\le 1.25\text{ mm}$ (isotropic preferred) | $\le 3.00\text{ mm}$ | $\le 2.00\text{ mm}$ |
| **In-Plane Matrix** | $\ge 512 \times 512$ | $\ge 256 \times 256$ | $\ge 512 \times 512$ (CT) / $256 \times 256$ (MRI) |
| **Voxel Dimension** | $\le 0.5 \times 0.5 \times 1.25\text{ mm}$ | $\le 0.8 \times 0.8 \times 3.0\text{ mm}$ | $\le 0.6 \times 0.6 \times 2.0\text{ mm}$ |
| **Reconstruction Kernel** | Standard / Bone kernel | Proton Density / T1 / T2 TSE | Bone (CT) or T1/PD (MRI) |

---

## 4. Independent Observation & Annotation Methods

1. **Dual Independent Annotation:** Each scan series is annotated independently by two board-certified musculoskeletal radiologists blinded to algorithm predictions, patient identifying data, and each other's coordinates.
2. **Annotation Tool:** Standard calibrated DICOM PACS viewer with 3D multiplanar reconstruction (MPR). Coordinates exported in DICOM Patient Coordinate System $(X, Y, Z)$ in millimeters.
3. **Consensus & Adjudication:**
   - Where the inter-observer distance $d = \|\mathbf{x}_1 - \mathbf{x}_2\| \le \tau_{\text{concordance}}$ ($2.0\text{ mm}$ for CT, $2.5\text{ mm}$ for MRI), the ground truth is defined as the centroid $\mathbf{x}_{\text{consensus}} = (\mathbf{x}_1 + \mathbf{x}_2) / 2$.
   - Where $d > \tau_{\text{concordance}}$, the landmark is flagged for independent tie-breaking adjudication by a third senior radiologist.

---

## 5. Calibration & Validation Procedures

1. **Partitioning:** The total cohort $N$ is partitioned deterministically into:
   - **Calibration Subset ($50\%$):** Utilized for initial affine / thin-plate spline deformation tuning.
   - **Tuning / Optimization Subset ($20\%$):** Utilized for hyperparameter selection (rigidity penalties, boundary weights).
   - **Holdout Validation Subset ($30\%$):** **Strictly sealed and air-gapped.**
2. **Algorithm Execution:** Ingests only de-identified DICOM series; registers canonical atlas mesh; computes predicted landmark coordinates; seals predictions before holdout ground truth is unblinded.

---

## 6. Holdout Protection & Cryptographic Sealing

1. The holdout partition identifiers are hashed with HMAC-SHA-256 and committed to the immutable project audit log prior to model training.
2. An independent research QA coordinator witnesses the sealing.
3. Ground-truth coordinates for holdout cases remain in an encrypted vault (`AES-256-GCM`).
4. The key is released only after the registration engine produces signed, timestamped coordinate predictions for all holdout subjects.

---

## 7. Primary & Secondary Endpoints

- **Primary Endpoint:** Mean 3D Euclidean error ($\mu_{\text{error}}$) across all valid landmarks in the holdout partition.
- **Secondary Endpoints:**
  1. Root Mean Square Error ($\text{RMSE}$) across landmarks.
  2. 95th Percentile Error ($E_{95}$) across landmarks.
  3. Directional Axis Error: Residuals decomposed into anatomical axes ($X$: Left-Right, $Y$: Anterior-Posterior, $Z$: Superior-Inferior).
  4. Inter-observer variability ($\sigma_{\text{obs}}$) across independent readers.

---

## 8. RMSE Acceptance Criteria

To achieve clinical research acceptance, the holdout partition must satisfy:
- **Cohort A:** $\text{RMSE} \le 2.20\text{ mm}$ (Upper 95% CI bound $\le 2.50\text{ mm}$).
- **Cohort B:** $\text{RMSE} \le 2.80\text{ mm}$ (Upper 95% CI bound $\le 3.20\text{ mm}$).
- **Cohort C:** $\text{RMSE} \le 2.40\text{ mm}$ (Upper 95% CI bound $\le 2.70\text{ mm}$).

---

## 9. Inter-Observer Uncertainty & Measurement Reliability

Observer measurement error ($\sigma_{\text{obs}}$) will be estimated via two-way random-effects Intraclass Correlation Coefficients ($\text{ICC}(2, 1)$) for absolute agreement:
- An $\text{ICC} < 0.75$ indicates inadequate landmark definition and triggers protocol review.
- Landmark-specific observer variance will be reported alongside algorithmic error.

---

## 10. Statistical Analysis Methods

### 10.1 Primary Analysis Model
To account for clustering of multiple landmarks within each subject and clustering of subjects within clinical sites, a linear mixed-effects model (LMM) with random intercepts will be estimated:

$$y_{ijk} = \mu + \gamma_i + \beta_{j(i)} + \epsilon_{ijk}$$

Where:
- $y_{ijk}$ is the registration error for landmark $k$ in subject $j$ at site $i$.
- $\mu$ is the overall mean registration error.
- $\gamma_i \sim \mathcal{N}(0, \sigma_{\text{site}}^2)$ is the random effect of site $i$.
- $\beta_{j(i)} \sim \mathcal{N}(0, \sigma_{\text{subject}}^2)$ is the random effect of subject $j$ nested in site $i$.
- $\epsilon_{ijk} \sim \mathcal{N}(0, \sigma_{\text{residual}}^2)$ is the residual measurement error.

### 10.2 Non-Inferiority Testing
The upper bound of the two-sided $90\%$ confidence interval (equivalent to one-sided $95\%$ upper confidence limit) of $\hat{\mu}$ will be compared against $\Delta_0 = 3.00\text{ mm}$. If $\hat{\mu}_{\text{upper}} < 3.00\text{ mm}$, non-inferiority is declared.

---

## 11. Confidence Intervals & Degrees of Freedom

Due to small cluster numbers in holdout subsets ($N_h = 8\text{–}15$ subjects per cohort), confidence intervals must NOT rely on standard normal asymptotic assumptions.
Degrees of freedom will be computed using Kenward-Roger or Satterthwaite approximation:

$$\text{df} \approx N_{\text{holdout}} - 1$$

Student's $t$ critical values ($t_{0.025, \text{df}}$) will be strictly enforced for all interval estimations.

---

## 12. Sample Size Assumptions & Sizing Scenarios

| Scenario | Total $N$ | Holdout $N_h$ | Cluster $\text{df}$ | Min Subgroup Power (Cohort B) | Primary Operational Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Scenario 1: Feasibility Pilot** | 45 | 4 / cohort | 3 | $58.7\%$ (asymp) / $\approx 31.4\%$ ($t$) | Protocol rehearsal, DICOM intake test only |
| **Scenario 2: Primary Clinical Pilot** | 85 | 8 / cohort | 7 | **$81.6\%$ (asymp) / $\approx 74.2\%$ ($t$)** | **Recommended prospective pilot study** |
| **Scenario 3: Confirmatory Study** | 115 | 11 / cohort | 10 | $88.9\%$ (asymp) / $\approx 84.1\%$ ($t$) | Multi-site confirmatory accuracy study |
| **Scenario 4: Multi-Site Reference** | 150 | 15 / cohort | 14 | $97.4\%$ (asymp) / $\approx 95.2\%$ ($t$) | Expanded international reference study |

> [!NOTE]
> All power calculations are contingent on independent biostatistical confirmation before institutional enrollment commences.

---

## 13. Missing Data & Outlier Policies

1. **Missing Landmarks:** Landmarks obscured by severe surgical artifacts, metal implants, or pathological osteolysis will be recorded as `MISSING_PATHOLOGY` and excluded from complete-case analysis.
2. **Missingness Mechanism:** If missingness exceeds $5\%$, Little's MCAR test will be performed. If missing at random (MAR), multiple imputation by chained equations (MICE, $m=10$ imputations) will serve as sensitivity analysis.
3. **Outliers:** Individual landmark errors exceeding $10.0\text{ mm}$ will undergo blinded clinical re-review to determine whether the deviation is attributable to anatomical anomaly, identification error, or algorithmic failure. No outlier may be removed without documented clinical rationale.

---

## 14. Multiplicity Control

To control the family-wise error rate across the three cohorts at $\alpha = 0.05$:
- **Hierarchical Fixed-Sequence Testing:** Testing proceeds sequentially:
  $$\text{Cohort A (Head/Neck)} \longrightarrow \text{Cohort C (Upper Limb)} \longrightarrow \text{Cohort B (Knee/Extremity)}$$
  If statistical significance is not achieved at any step, confirmatory testing stops, and subsequent cohort tests are designated exploratory.
- Alternatively, Bonferroni adjusted threshold $\alpha_{\text{adj}} = 0.05 / 3 \approx 0.0167$ will be applied for simultaneous testing.

---

## 15. Site & Scanner Heterogeneity

1. Scanning protocols must be standardized across participating institutions.
2. Heterogeneity will be quantified using the between-site Intraclass Correlation Coefficient ($\rho_{\text{site}}$).
3. Scanner manufacturer (Siemens, GE, Philips) and field strength (1.5T vs 3.0T) will be evaluated as fixed covariates in secondary exploratory models.

---

## 16. Protocol Deviation Handling

1. All deviations (e.g., non-compliant slice thickness, patient motion artifact) will be logged in an immutable electronic protocol deviation log.
2. Deviations are categorized as **Minor** (slice thickness $\le 15\%$ above target) or **Major** (incorrect modality, missing essential landmarks, unauthorized re-identification attempt). Major deviations result in case exclusion from the primary per-protocol cohort.

---

## 17. Independent Adjudication Committee

1. A three-member Independent Review and Adjudication Committee (one independent biostatistician, one senior radiologist, one clinical anatomist) will govern study execution.
2. Committee members must have zero financial or consulting conflicts of interest with the software development team.
3. The committee has sole authority to declare unblinding and adjudicate unresolved landmark discrepancies.

---

## 18. Data Governance, Retention & Scientific Limitations

### 18.1 Governance & Privacy
1. All scans must be stripped of all 18 HIPAA Safe Harbor identifiers (45 CFR § 164.514(b)(2)) and comply with EU GDPR Article 89 pseudonymization requirements.
2. Local execution on air-gapped on-premise hardware; zero external network transmission.
3. Primary data retained in encrypted archival storage for a minimum of 5 years following publication.

### 18.2 Fundamental Scientific Limitations
1. **CT/MRI Scans Image Physical Anatomy, Not Meridians:** Computed tomography and magnetic resonance imaging visualize bones, ligaments, tendons, muscles, and vessels. They do NOT image traditional meridians or acupuncture points as histological structures.
2. **Registration Accuracy Does Not Prove Efficacy:** Demonstrating accurate mathematical alignment between a 3D atlas and patient anatomy does NOT establish therapeutic efficacy, clinical outcome benefit, or neurophysiological mechanisms.
3. **Strict Non-Clinical Boundary:** This software is strictly for research exploration (`ENGINEERING_RESEARCH_ONLY`). Autonomous diagnosis, therapeutic prescription, and invasive needle puncture guidance are strictly prohibited (`clinical_depth_guidance_allowed: False`).
