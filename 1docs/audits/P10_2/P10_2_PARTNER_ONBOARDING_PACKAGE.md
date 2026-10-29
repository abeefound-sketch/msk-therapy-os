# P10.2 EXTERNAL PARTNER ONBOARDING & CLINICAL RESEARCH INTAKE KIT
## Institutional Templates, Governance Checklists, and Technical Specifications for Independent Validation Partners

> **CLASSIFICATION:** INSTITUTIONAL ONBOARDING PACKAGE  
> **MILESTONE:** P10.2  
> **INTENDED AUDIENCE:** Academic Medical Centers, Radiology Research Departments, Anatomy Institutes, DUA/IRB Review Boards  
> **STATUS:** READY FOR INSTITUTIONAL COLLABORATION

---

## 1. Welcome & Purpose of the Onboarding Package

MSK-Therapy-OS provides an open, deterministic computational anatomical atlas. To achieve empirical validation (Milestone P10.3 / Gate G14), the platform requires high-resolution in-vivo human ground truth datasets from independent academic and clinical institutions.

This package provides institutional research partners with the exact legal, ethical, and technical templates needed to prepare, de-identify, and submit reference anatomical observations without compromising patient privacy or data integrity.

---

## 2. Institutional Checklist & Ingestion Workflow

```
 Phase 1: Governance          Phase 2: Data Prep           Phase 3: Intake & Audit
 ┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
 │ 1. DUA / MTA Review  │ ──> │ 4. De-identification │ ──> │ 7. SHA-256 Hash Verif│
 │ 2. IRB/Ethics Cert   │     │    (18 HIPAA Elements)│     │ 8. Intake Quarantine │
 │ 3. Reviewer COI Form │     │ 5. DICOM LPS Normaliz│     │ 9. Admin Sign-Off    │
 └──────────────────────┘     │ 6. Manifest Generat  │     └──────────────────────┘
                              └──────────────────────┘
```

---

## 3. Template 1: External Data Access & Submission Request Form

```markdown
### MSK-THERAPY-OS DATA SUBMISSION REQUEST
- **Submitting Institution:** [e.g., Department of Radiology, University Hospital]
- **Principal Investigator / Site Lead:** [Name, Academic Title, Email]
- **Target Pilot Cohort:**
  [ ] Cohort A: Abdominal Meridian Points (ST19–ST30)
  [ ] Cohort B: Bilateral Extremities (Upper / Lower Limbs)
  [ ] Cohort C: Craniofacial & Cervical (Yintang / GV24+)
  [ ] Other Anatomical Region: _________________________
- **Acquisition Modality:** [ ] Volumetric CT  [ ] 3T MRI  [ ] 3D Optical Surface Scan
- **Cohort Sample Size ($N$ subjects):** [e.g., 30]
- **IRB / Ethics Protocol #:** [e.g., IRB-2026-MSK-01]
- **DUA / MTA Reference #:** [e.g., DUA-2026-EXT-04]
- **Target Ingestion Date:** [YYYY-MM-DD]
```

---

## 4. Template 2: Dataset Technical Specification Manifest (`v1.1-P10`)

Submissions must provide a dataset descriptor JSON adhering to schema version `1.1-P10`:

```json
{
  "schema_version": "1.1-P10",
  "dataset_id": "DS-HOSP-2026-COHORT-A",
  "name": "High-Resolution In-Vivo Abdominal CT Ground Truth Cohort",
  "source_organization": "Department of Anatomy, University Medical Center",
  "version": "1.0",
  "license": "Research Use Only - Data Use Agreement Enforced",
  "modality": "IN_VIVO_CT",
  "is_synthetic_fixture": false,
  "sample_size": 30,
  "administrative_verification_status": "PENDING_ADMIN_SIGN_OFF",
  "governance_metadata": {
    "ethics_approval_id": "IRB-2026-8812",
    "dua_id": "DUA-UMC-MSK-001",
    "authorization_expiration_date": "2027-12-31",
    "lead_clinical_investigator": "Dr. Elena Rostova, MD, PhD"
  },
  "coordinate_reference_frame": "DICOM_LPS",
  "units": "meters",
  "registration_method": "5-point rigid Procrustes to BodyParts3D skeletal frame"
}
```

---

## 5. Template 3: De-Identification & HIPAA Safe Harbor Compliance Guide

Partners must guarantee that no Protected Health Information (PHI) enters the dataset.

### Mandatory Pre-Processing Steps:
1. **Strip All 18 HIPAA Identifiers:** Names, geographic data smaller than state, dates (replace with age in years or relative days), telephone numbers, fax, emails, SSN, MRN, health plan IDs, account numbers, certificate/license numbers, vehicle IDs, device serial numbers, URLs, IP addresses, biometric identifiers, full-face photos.
2. **Defacing for Craniofacial Imaging (Cohort C):** Volumetric head CTs must have facial features defaced/obfuscated using standard neuroimaging defacing tools (e.g. PyDeface or equivalent) to prevent biometric facial reconstruction, while strictly preserving cranial skeletal landmarks (Nasion, Glabella, Inion).
3. **Pseudonym Format:** Subject IDs must follow pseudonymous format `P-XXX` (e.g., `P-001`, `P-002`). Free-text strings in `notes` or `source_image_reference` are automatically screened by the intake quarantine scanner.

---

## 6. Template 4: Independent Reviewer Conflict-of-Interest (COI) Declaration

Each independent observer and reviewer must execute this declaration prior to data ingestion:

```markdown
### INDEPENDENT OBSERVER / REVIEWER COI DECLARATION
I, _______________________________ [Full Name], acting in the capacity of:
[ ] Independent Observer
[ ] Primary Radiologist Reviewer
[ ] Secondary Anatomist Reviewer

Hereby certify under institutional research guidelines:
1. I am NOT a core software developer or algorithm architect of MSK-Therapy-OS.
2. I have no financial interest or intellectual property stake in the outcome of this validation.
3. My anatomical observations and coordinate landmarkings represent independent clinical judgments based strictly on physical imaging evidence.
4. I acknowledge that my observer ID (______________) cannot be used as reviewer ID for my own observations.

Signature: ____________________________________ Date: ___________________
```

---

## 7. Template 5: Secure Data Transfer & Checksum Protocol

To ensure data integrity and prevent transmission corruption:
1. Generate a SHA-256 checksum for each data file and manifest:
   ```powershell
   Get-FileHash -Algorithm SHA256 ./observations.json
   ```
2. Encrypt package using AES-256 or transfer via secure SFTP/TLS 1.3 data enclave.
3. Submit manifest with `source_checksum` field populated. The ingestion engine automatically validates SHA-256 before processing.

---

## 8. Template 6: Data Retention & Disposal Schedule

1. **Active Validation Period:** Data retained in local SQLite database for the duration of the validation study.
2. **Quarantine Storage:** Any quarantined data rejected by automated HIPAA screening is held in `data/quarantine/` for a maximum of 30 days pending partner notification, after which it is securely overwritten using DoD 5220.22-M wiping standards.
3. **Post-Validation Archival:** Per DUA requirements, raw volumetric DICOMs are stored exclusively in partner institutional enclaves; MSK-Therapy-OS retains only the anonymized coordinate triplets and validation report manifests.
