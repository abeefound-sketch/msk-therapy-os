# MSK-Therapy-OS Roadmap V2.1

Current confirmed baseline source: uploaded M2.8.2 snapshot (not checked-out live Git). Planned IDs are *not completed functionality*.

| Phase | Scope | Acceptance gate | State |
|---|---|---|---|
| Foundation/M3-F0 | Typed provenance, migrations, common case/visit contracts, safety + audit | Backwards-compatible and negative tests | Partial prototype in snapshot |
| M2.9 | Evidence-typed anatomy–point–organ relationship explorer | Bidirectional search, verified mappings only, teaching labels | Code + tests pass, browser/evidence acceptance pending |
| M2.10 | Custom point atlas / reflexology research studio | Versioned 2D point/line/zone annotations, positive/negative/unassessed longitudinal recording | Partial code + tests; full editing/export pending |
| M3-P0 | Multi-patient, PROMs, CTCAE, FHIR, clinical RBAC | Cross-case isolation, approval, recovery, reviewed exports | Planned |
| M2.11 | Photo pose to static anatomical reference | Quality/abstention + manual correction + curated muscle-role evidence | Planned |
| M2.12 | Editable illustrative surface avatar from three views | Versioned surface edits, independent Atlas, measured performance | Planned |
| M4 | Kinematic arcs and optional biomechanical models | FPS/memory and clinically honest estimated output | Planned |
| M5 | Anatomy depth layers | Anatomical source/mapping, no safety-depth inference | Planned |
| M6 | Longitudinal cohort analysis hub | Reproducible statistics, missingness, privacy, no causal efficacy assertions | Planned |
| HF-DEMO | Read-only Docker Space on a single HTTPS link | Local Docker smoke + public-route threat review + token-gated upload | Docker recipe written; build/deploy blocked |

**Sequence:** Foundation → M2.9 → M2.10 → M3-P0 → M2.11 → M2.12 → M4 → M5 → M6. HF-DEMO is parallel after read-only security hardening. This deliberately moves M3 core security before activating uploads and Internet write access.

See `HANDOFF_ROADMAP_V2_1_CODING_AGENT.md` for detailed instructions, exact modifications and source traceability.
