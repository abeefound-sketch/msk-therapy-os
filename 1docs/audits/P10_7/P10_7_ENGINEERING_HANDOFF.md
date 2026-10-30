# MSK-THERAPY-OS — P10.7 ENGINEERING HANDOFF SPECIFICATION

**Milestone:** P10.7 — Scientific Protocol Lock, External Review Submission Readiness & Research Partnership Handoff  
**Release Tag:** `v2.1.0-local-rc3`  
**Date:** 2026-10-30  
**Target Audience:** Human Principal Investigator, Clinical Research Coordinator, and Institutional Project Owner  
**Handoff Declaration:** `ENGINEERING_HANDOFF_COMPLETE / EXTERNAL_ACTION_REQUIRED`  

---

## 1. Handoff Rationale & Mandatory Stop Rule

With the successful execution and verification of Milestone P10.7, **all software engineering, synthetic validation, mathematical modeling, and institutional package preparation tasks are complete.**

```text
[MANDATORY STOP RULE DECLARED]
All P10.7 engineering acceptance gates (P701–P707) are satisfied.
Outstanding requirements are strictly external:
  1. Human independent biostatistical protocol review.
  2. Institutional partner outreach, DUA execution, and IRB clearance.
  3. Real-world hospital PACS DICOM extraction and radiologist annotation.

The coding agent and software developers CANNOT build additional internal feature layers
to substitute for missing empirical evidence.
```

---

## 2. Directory Structure of Deliverables

```text
D:\5Projects\msk-therapy-os\
├── 1docs\audits\P10_7\
│   ├── P10_7_BASELINE_VERIFICATION.md
│   ├── P10_7_STATISTICAL_REPRODUCIBILITY.md
│   ├── P10_7_PROTOCOL_FREEZE_CANDIDATE.md
│   ├── P10_7_INDEPENDENT_REVIEW_PACKAGE.md
│   ├── P10_7_PARTNER_PACKAGE_INDEX.md
│   ├── P10_7_EXTERNAL_ACTION_REGISTER.md
│   ├── P10_7_SECURITY_AND_REGRESSION.md
│   ├── P10_7_FINAL_ACCEPTANCE_MATRIX.md
│   ├── P10_7_ENGINEERING_HANDOFF.md
│   ├── P10_7_EXECUTIVE_DECISION.md
│   └── partners\
│       ├── charite_berlin\
│       │   └── CHARITE_P10_7_PARTNER_PACKAGE.md
│       ├── mgh_harvard\
│       │   └── MGH_HARVARD_P10_7_PARTNER_PACKAGE.md
│       └── snuh_seoul\
│           └── SNUH_P10_7_PARTNER_PACKAGE.md
├── 2data\evidence\p10_7_validation\
│   └── 01_p10_7_protocol_lock_and_review_readiness.png
├── msk_therapy_os\
│   ├── protocol_freeze.py
│   ├── statistical_oracle.py
│   ├── external_dependency_register.py
│   ├── server.py (Updated with /api/atlas/validation/p10-7-dashboard)
│   └── static\atlas\meridians.js (Updated with #btnP107ProtocolLock UI)
├── scripts\
│   └── reproduce_p10_7_review_statistics.py
└── tests\
    ├── test_p10_7_governance_and_protocol_lock.py
    └── test_p10_7_playwright.py
```

---

## 3. How to Execute and Verify the System

### 3.1 Non-Sensitive Reviewer Statistical Verification
```powershell
cd D:\5Projects\msk-therapy-os
python scripts/reproduce_p10_7_review_statistics.py
```
Outputs exact deterministic design effects, effective sample sizes, variance components, and Student's $t$ dilation factors across all 4 scenarios without third-party mathematical libraries.

### 3.2 Unit & Integration Regression Suite (751 tests)
```powershell
cd D:\5Projects\msk-therapy-os
python -m pytest -m "not playwright" -q
```
Executes all 751 non-browser tests across core algorithms, security guards, statistical models, and intake controllers.

### 3.3 Visual & Hardware Playwright E2E Suite (19 tests)
```powershell
cd D:\5Projects\msk-therapy-os
python -m pytest tests/test_p10_7_playwright.py -v
```
Spins up the local multi-threaded HTTP server, launches headless Chromium, triggers `#btnP107ProtocolLock`, and captures full-resolution visual evidence to `2data/evidence/p10_7_validation/`.

---

## 4. Sequence of Immediate Human Actions

1. **Week 1:** Transmit Dossier 1 ([`P10_7_INDEPENDENT_REVIEW_PACKAGE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_7/P10_7_INDEPENDENT_REVIEW_PACKAGE.md)) and [`scripts/reproduce_p10_7_review_statistics.py`](file:///D:/5Projects/msk-therapy-os/scripts/reproduce_p10_7_review_statistics.py) to an independent academic biostatistician for SAP sign-off.
2. **Week 2:** Review and finalize the prospective outreach communication (Section 15 of partner packages) for candidate clinical department chairs.
3. **Week 3–4:** Issue formal partnership inquiries to Charité Berlin, MGH/Harvard, and/or SNUH Seoul.
4. **Month 2–3:** Negotiate bilateral Data Use Agreements (DUA) and submit retrospective research applications to institutional ethics boards.
5. **Month 4+:** Ingest authorized, defaced DICOM series into the intake controller upon external verification.
