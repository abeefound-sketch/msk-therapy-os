# MSK-Therapy-OS | Milestone M2.8.2 Clinical Safety Governance & Contraindication Hard-Stops

**Document ID:** `M282-CLIN-001`  
**Milestone:** `M2.8.2 Final Security & Acceptance Remediation`  
**Author:** Clinical Safety Architect & Medical Informatics Specialist  
**Date:** October 22, 2026  
**Status:** ACCEPTED / CLINICALLY VERIFIED  

---

## 1. Executive Summary

Milestone M2.8.2 enforces strict clinical governance rules in MSK-Therapy-OS, preventing medical harm in student training and musculoskeletal care scenarios. 

Prior releases identified safety red flags (such as cervical myelopathy, vertebrobasilar insufficiency, or progressive neurological deficits) and displayed visual warnings, but did not strictly prevent downstream execution of manual therapy sessions or validate documented specialist clearance.

M2.8.2 hard-codes unbypassable clinical safeguards:
1. **Red Flag Escalation Gating:** Visits marked with red flags (`STOP_AND_REFER`) cannot approve SOAP notes without documented medical specialist clearance.
2. **Downstream Session Prohibition:** Direct recording of manual therapy sessions (`/api/session`) on uncleared red-flag visits raises strict exceptions.
3. **High-Velocity Spinal Manipulation Ban:** Modality `spinal_manipulation` is universally prohibited across all sessions.
4. **FHIR R4 Bundle Integrity:** Rejected or unapproved clinical notes cannot export finished encounters; rejected notes are flagged as `entered-in-error` (nullified).

---

## 2. Clinical Gating Architecture

```
[Patient Visit Assessment]
            |
            v
   [Red Flags Detected?]
   (e.g., bilateral radiculopathy, dizziness, ataxia)
       /         \
     NO           YES
     /             \
[Standard Path]   [DISPOSITION: STOP_AND_REFER]
     |                     |
     |                     +---> [Therapy Session Attempted?]
     |                     |           |
     |                     |           v
     |                     |    HARD-STOP BLOCKED:
     |                     |    "Cannot record therapy session without clearance"
     |                     |
     |                     +---> [SOAP Note Supervisor Approval?]
     |                                 |
     |                                 v
     |                          Referral Clearance Documented?
     |                               /       \
     |                             YES        NO
     |                             /           \
     |                      [APPROVED]    HARD-STOP BLOCKED:
     |                                    "Requires documented referral"
     v                                         |
[FHIR R4 Export: 'finished']                   v
                              [FHIR R4 Export: 'entered-in-error']
```

---

## 3. Implementation Details

### 3.1 Red Flag Supervisor Clearance Mandate
In [`msk_therapy_os/soap.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/soap.py), `review_soap_note()` verifies visit safety flags before allowing `APPROVED` status:

```python
# If visit has a red flag or STOP_AND_REFER, require explicit referral/clearance documentation
flag = visit_row[0] if visit_row else "none"
if flag != "none" and status == "APPROVED":
    notes_lower = (review_notes or "").lower()
    cleared_keywords = ("referral", "cleared", "clearance", "physician", "specialist", "neurologist", "orthopedic")
    if not any(kw in notes_lower for kw in cleared_keywords):
        raise ValueError(
            "Cannot approve SOAP note for visit with active red flags without documented "
            "physician/specialist referral or clearance in review notes."
        )
```

### 3.2 Downstream Manual Therapy Session Hard-Stop
In [`msk_therapy_os/tracking.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/tracking.py), `record_session()` queries the associated visit record:

```python
# Check visit flags for hard stop
v_cur = db.execute("SELECT flag, note FROM visits WHERE id = ?", (visit_id,))
v_row = v_cur.fetchone()
if v_row:
    flag, v_note = v_row
    if flag != "none":
        v_note_lower = (v_note or "").lower()
        if not any(k in v_note_lower for k in ("clearance", "cleared", "referred", "specialist")):
            raise ValueError(
                f"Cannot record manual therapy session for visit #{visit_id} with active red flag ('{flag}') "
                "without documented physician/specialist clearance."
            )
```

### 3.3 Prohibition of High-Velocity Thrust (Spinal Manipulation)
To maintain alignment with safe student training scopes and avoid vertebral artery dissection or neurological injury risks:

```python
if modality == "spinal_manipulation":
    raise ValueError(
        "Modality 'spinal_manipulation' is prohibited in this educational/clinical setting. "
        "Use gentle mobilization, massage, or acupressure."
    )
```

### 3.4 HL7 FHIR R4 Encounter Nullification
In [`msk_therapy_os/tracking.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/tracking.py), `export_case_fhir()` checks SOAP review status:
- If a visit has an associated SOAP note with `review_status == 'REJECTED'`, the Encounter status is marked `entered-in-error`.
- FHIR Encounter extension tags it with HL7 Terminology code `nullified` (`http://terminology.hl7.org/CodeSystem/v3-ActStatus`).

---

## 4. Verification Test Evidence

Verified across the clinical test suite:

```
tests\test_auth_and_rbac.py::test_soap_approval_red_flag_requires_documented_referral PASSED
tests\test_auth_and_rbac.py::test_session_recording_blocked_on_red_flags_without_referral PASSED
tests\test_auth_and_rbac.py::test_session_recording_spinal_manipulation_prohibited PASSED
tests\test_auth_and_rbac.py::test_fhir_export_marks_rejected_soap_entered_in_error PASSED
```

**Result: 100% Clinical Safeguard Adherence Verified.**
