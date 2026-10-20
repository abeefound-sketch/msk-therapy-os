# Architecture Decision Record

## ADR-001 - One orchestration repo, upstream adapters
**Status:** Accepted for prototype.  
**Rationale:** Smaller operational surface, stable interfaces, avoids licensing/upgrade conflicts.

## ADR-002 - SQLite and Python standard library first
**Status:** Accepted for synthetic prototype only.  
**Rationale:** 8 GB RAM laptop; zero external services. Revisit before patient use.

## ADR-003 - Safety rule engine before AI
**Status:** Accepted.  
**Rationale:** Red flags are explicit and auditable. AI is read-only, optional, and must never override safety rules.

## ADR-004 - Educational anatomy viewer rather than diagnosis image engine
**Status:** Accepted.  
**Rationale:** The atlas illustrates structures but cannot infer tissue injury or locate nerve compression from palpation.

## ADR-005 - Modular M1 architecture with backward-compatible CLI contracts
**Status:** Accepted in M1.  
**Rationale:** Clean separation of concerns (`db`, `models`, `safety`, `assessment`, `soap`, `evidence`, `anatomy`, `reporting`) while keeping 100% backward compatibility with M0 CLI commands and function signatures (`add_visit`, `init`, `seed_demo`).

## ADR-006 - Hard safety gating and modality contraindication matrix
**Status:** Accepted in M1.  
**Rationale:** Evaluates reported red flags and modality-specific contraindications (general massage and DDS/electrical contraindications from FDA guidelines). If any flag or contraindication is triggered, disposition is strictly `STOP_AND_REFER`. High-velocity spinal thrust manipulation is forbidden by contract.

## ADR-007 - Four-tier evidence provenance and namespace segregation
**Status:** Accepted in M1.  
**Rationale:** All educational assertions must cite a vetted source across 4 defined tiers (Tier 1 Clinical Guidelines, Tier 2 Peer-Reviewed Anatomy, Tier 3 Manufacturer Manuals, Tier 4 Traditional Schemas). Traditional Thai Sen lines and Dien Chan facial points are placed in distinct namespaces (`TRADITIONAL_MERIDIAN`, `DIEN_CHAN_REFLEX`) with disclaimers that they are not anatomical nerves or vessels.

## ADR-008 - Role-based supervision workflow and offline Markdown reports
**Status:** Accepted in M1.  
**Rationale:** Students can draft SOAP notes (`DRAFT`), while only accounts with the `reviewer` role can approve notes (`APPROVED`). Offline case reports audit missing intakes, missing SOAP notes, and flag incomparability when different ROM instruments are mixed.


## ADR-009 - 2D Interactive SVG Body-Map and Zero-Dependency HTTP Server (Milestone M2)
**Status:** Accepted in M2.  
**Rationale:** Target workstation hardware (Intel Core i7-5600U, Intel HD 5500, 8 GB RAM) struggles with full-resolution local 3D WebGL meshes without heavy GPU resources. Milestone M2 delivers a 2D interactive SVG body-map running in standard HTML5/CSS/Vanilla JS served by Python's built-in `http.server`. Detailed 3D anatomical structures link outward to Open Anatomy Atlas via BodyParts3D FMA query URLs, achieving instantaneous 60fps responsiveness and zero external runtime dependencies.
