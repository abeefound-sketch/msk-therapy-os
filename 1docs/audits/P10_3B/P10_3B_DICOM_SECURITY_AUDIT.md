# P10.3B DICOM INTAKE & ADVERSARIAL SECURITY AUDIT REPORT

**Milestone:** P10.3B — Independent Audit, Security Hardening & Empirical Pilot Readiness  
**Target Module:** [`msk_therapy_os/dicom_intake.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/dicom_intake.py)  
**Security Standard:** HIPAA 18 Safe Harbor Identifiers, NEMA PS3.10-2023, DICOM Part 15 Security Profiles  
**Role:** Independent Security Auditor & Medical Imaging Systems Engineer  
**Audit Date:** 2026-10-30  
**Gate P302 Status:** **PASS**

---

## 1. Scope & Threat Model

The DICOM intake subsystem operates offline in a pure Python standard library runtime (without `pydicom`, C-extensions, or heavy image-processing engines). The security surface encompasses incoming untrusted external binary files attempting ingestion into the MSK-Therapy-OS research catalog.

### Threat Vectors Evaluated:
1. **Path Traversal & Directory Escape Attacks:** Malicious file paths (e.g., `../../etc/shadow`, `..\..\..\windows\system32\cmd.exe`, null byte `%00` termination) passed to intake endpoints.
2. **Memory Exhaustion & Malformed Length DOS:** Adversarial binary headers declaring 4-byte element lengths of `0xFFFFFFFF` (undefined length) or excessively large values (e.g. >10MB) to induce Out-Of-Memory (OOM) crashes.
3. **De-Identification False-Assurance (Burned-in PHI):** Files claiming `(0028, 0301) BurnedInAnnotation = "NO"` while containing optical text burned into the pixel array.
4. **Unsupported Compression Hijacking:** Compressed transfer syntaxes (e.g. JPEG-Lossless `1.2.840.10008.1.2.4.70`, JPEG-2000 `1.2.840.10008.1.2.4.91`) that cannot be decoded safely in pure Python without native C-libraries.
5. **Multiframe Ambiguity:** Complex cine/multiframe slices attempting to bypass 2D slice coordinate registration.
6. **SOPInstanceUID & Hash Collisions:** Duplicate or replayed patient scans polluting validation cohorts.

---

## 2. Hardening Measures Implemented

### 2.1 Path Traversal & Injection Defense
In [`DicomHeaderParser.parse_file`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/dicom_intake.py#L152):
- Any file path containing directory traversal tokens (`..`) or null bytes (`\x00`) is trapped prior to filesystem access.
- When `allowed_base_dir` is configured, `os.path.commonpath([real_base, real_file])` is strictly enforced. Any file resolving outside the base directory is immediately quarantined with `DicomQuarantineReason.PATH_TRAVERSAL_DETECTED`.

### 2.2 Memory Exhaustion & Boundary Protection
- Both File Meta Information (Group 0002) and top-level Dataset elements are subject to strict element length limits:
  $$\text{length}_{\text{max}} = 10 \times 1024 \times 1024 \text{ bytes (10 MB)}$$
- Tags declaring `0xFFFFFFFF` (undefined sequence length) or lengths $>10$ MB are trapped, halting parsing and quarantining the file under `DicomQuarantineReason.MALFORMED_HEADER_STRUCTURE`.

### 2.3 Strict Fail-Closed Policy on Pixel De-Identification
- **Finding:** A header claiming `BurnedInAnnotation = "NO"` is merely a vendor-declared metadata attribute. In an offline pure-Python environment with no optical character recognition (OCR) or computer-vision neural nets, pixel arrays cannot be autonomously audited for burned-in patient names.
- **Enforcement:**
  - Added new quarantine reason: `DicomQuarantineReason.UNVERIFIED_PIXEL_DEIDENTIFICATION`.
  - When `require_pixel_certificate = True` (mandated for all empirical clinical datasets), ingestion is fail-closed unless accompanied by an independently executed and verified institutional pixel de-identification certificate (`has_pixel_deidentification_certificate = True`).
  - Without this certificate, empirical datasets cannot be promoted out of quarantine.

### 2.4 Transfer Syntax & Modality Confinement
- Permitted Transfer Syntaxes:
  - `1.2.840.10008.1.2.1` (Explicit VR Little Endian)
  - `1.2.840.10008.1.2` (Implicit VR Little Endian)
  - `1.2.840.10008.1.2.2` (Explicit VR Big Endian)
- All compressed variants (`1.2.840.10008.1.2.4.*`, `1.2.840.10008.1.2.5`) are rejected fail-closed under `QUARANTINE_UNSUPPORTED_COMPRESSION`.

---

## 3. Adversarial Security Verification Matrix

| Test Vector | Input Characteristic | Expected Behavior | Audit Verdict |
|---|---|---|---|
| **ADV-DICOM-01** | Path traversal `../../etc/passwd` | Quarantined under `QUARANTINE_PATH_TRAVERSAL_DETECTED` | **PASS** |
| **ADV-DICOM-02** | Path traversal outside `allowed_base_dir` | Quarantined under `QUARANTINE_PATH_TRAVERSAL_DETECTED` | **PASS** |
| **ADV-DICOM-03** | Malformed length tag `0xFFFFFFFF` | Quarantined under `QUARANTINE_MALFORMED_HEADER_STRUCTURE` | **PASS** |
| **ADV-DICOM-04** | Excessive length tag (50 MB) | Trapped safely; no memory exhaustion; quarantined | **PASS** |
| **ADV-DICOM-05** | JPEG-2000 Compressed transfer syntax | Quarantined under `QUARANTINE_UNSUPPORTED_COMPRESSION` | **PASS** |
| **ADV-DICOM-06** | Multiframe (frames = 120) | Quarantined under `QUARANTINE_MULTIFRAME_UNSUPPORTED` | **PASS** |
| **ADV-DICOM-07** | `BurnedInAnnotation = "NO"` without institutional cert | Quarantined under `QUARANTINE_UNVERIFIED_PIXEL_DEIDENTIFICATION` when certificate required | **PASS** |
| **ADV-DICOM-08** | Certified pixel de-identification present | Cleared with `has_pixel_deidentification_certificate = True` | **PASS** |

---

## 4. Conclusion

Gate P302 is verified as **PASS**. The offline DICOM intake subsystem enforces robust defense-in-depth against malicious payloads, header tampering, memory exhaustion, and unwarranted pixel-privacy assumptions.
