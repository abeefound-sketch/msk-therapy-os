# P10.4B ENGINEERING HANDOFF & OPERATIONAL PILOT DOSSIER

**Milestone:** P10.4B — Institutional Pilot Activation, External Evidence Preparation & Scientific Readiness  
**Repository:** `D:\5Projects\msk-therapy-os`  
**Active Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**System Version:** `v2.1.0-local-rc3`  
**Release Scope:** `ENGINEERING_RESEARCH_ONLY`  
**Date:** 2026-10-30  
**Lead Authors:** Principal Research Software Engineer & Clinical Research Operations Architect  

---

## 1. Executive Summary & Deliverables Completed

Milestone P10.4B completes all engineering, biostatistical, documentation, and governance preparations required for institutional pilot onboarding. The software is ready to receive independently approved research datasets without fabricating clinical certifications or compromising patient privacy.

### Complete Documentation Dossier in [`1docs/audits/P10_4B/`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/):
1. [`P10_4B_RELEASE_REPRODUCTION.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_RELEASE_REPRODUCTION.md) — Gate B401: Clean-room baseline reproduction on physical hardware.
2. [`P10_4B_STATISTICAL_POWER_REASSESSMENT.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_STATISTICAL_POWER_REASSESSMENT.md) — Gate B402: Power, cluster design effects, and holdout sample adequacy.
3. [`P10_4B_PRESPECIFIED_SAP_DRAFT.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_PRESPECIFIED_SAP_DRAFT.md) — Gate B402: Prespecified Statistical Analysis Plan (SAP) draft.
4. [`P10_4B_INSTITUTIONAL_PARTNER_PACKAGE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_INSTITUTIONAL_PARTNER_PACKAGE.md) — Gate B403: 12-section partner onboarding package.
5. [`P10_4B_EXTERNAL_DATA_PREFLIGHT.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_EXTERNAL_DATA_PREFLIGHT.md) — Gate B404: Technical intake preflight verification.
6. [`P10_4B_SCIENTIFIC_CLAIM_BOUNDARIES.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_SCIENTIFIC_CLAIM_BOUNDARIES.md) — Gate B405: 5-tier epistemological claim boundary guard.
7. [`P10_4B_INDEPENDENT_REVIEW_PROTOCOL.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_INDEPENDENT_REVIEW_PROTOCOL.md) — Gate B406: Offline independent reviewer protocol.
8. [`P10_4B_SYNTHETIC_PILOT_EVIDENCE.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_SYNTHETIC_PILOT_EVIDENCE.md) — Gate B407: Synthetic pilot rehearsal & full regression.
9. [`P10_4B_EXTERNAL_BLOCKER_REGISTER.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_EXTERNAL_BLOCKER_REGISTER.md) — Gate B408: Actionable register of 8 external dependencies.
10. [`P10_4B_FINAL_ACCEPTANCE_MATRIX.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_FINAL_ACCEPTANCE_MATRIX.md) — Master acceptance matrix.
11. [`P10_4B_ENGINEERING_HANDOFF.md`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P10_4B/P10_4B_ENGINEERING_HANDOFF.md) — This operational handoff report.

---

## 2. Inventory of Source Code Modifications in P10.4B

### 2.1 Newly Implemented Modules
| Module Path | Primary Responsibilities | Dependencies |
|---|---|---|
| [`msk_therapy_os/scientific_claim_guard.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/scientific_claim_guard.py) | Enforces 5 epistemological tiers, blocks category conflations (e.g. registration error $\neq$ meridian existence or clinical efficacy). | Python standard library |
| [`msk_therapy_os/reviewer_workflow.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/reviewer_workflow.py) | Independent reviewer workflow, developer agent exclusion (`DEVELOPER_AGENT_EXCLUSION`), checklist sealing. | Python standard library |
| [`msk_therapy_os/statistical_power.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/statistical_power.py) | Deterministic sample size, cluster design effect ($DE = 1 + (m-1)\rho$), effective sample size, holdout power. | Python standard library |
| [`tests/test_p10_4b_scientific_readiness.py`](file:///D:/5Projects/msk-therapy-os/tests/test_p10_4b_scientific_readiness.py) | 9 automated unit/integration tests validating claim guards, reviewer workflows, and power calculations. | `pytest` |

---

## 3. Verified Reproduction Commands

```powershell
# 1. Workspace
cd D:\5Projects\msk-therapy-os

# 2. Execute non-Playwright suite (720 tests)
python -m pytest -m "not playwright" -q

# 3. Execute browser E2E suite (16 tests)
python -m pytest -m "playwright" -q

# 4. Total tests: 736 passed
```

---

## 4. Git Revision & State

- **Branch:** `feat/p9.4-definitive-meridian-atlas-correction`
- **Target Git Commit:** `feat(p10.4b): institutional pilot activation, external evidence preparation, and scientific readiness`
- **Release Status:** `ENGINEERING_RESEARCH_ONLY`
- **Gate G14:** `BLOCKED_EXTERNAL_DATA`
