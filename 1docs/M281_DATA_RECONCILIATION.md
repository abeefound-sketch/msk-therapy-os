# MSK-Therapy-OS | Milestone M2.8.1 Point Count Reconciliation Report

**Document ID:** `M281-REC-001`  
**Milestone:** `M2.8.1 Acceptance Hardening`  
**Author:** Medical Terminology Architect & Senior Full-Stack Engineer  
**Date:** October 22, 2026  
**Status:** MATHEMATICALLY VERIFIED / DYNAMIC FORMULA ENFORCED  

---

## 1. Executive Summary

Milestone M2.8.1 resolves the acupoint counting discrepancy across WHO, National Chinese standards (GB/T 12346), Vietnamese Dien Chan reflexology, and locally authored custom points. 

Historically, certain project notes cited a static figure of **368 points**. This document and automated test suite prove that **368 was an artifact of a specific test state (366 baseline + 2 custom points)**. The runtime total points count is **strictly dynamic**, governed by mathematical conservation rules, and never hardcoded.

---

## 2. Dynamic Point Conservation Mathematics

The runtime system calculates total available points dynamically via:

$$N_{\text{runtime\_total}} = N_{\text{canonical}} + N_{\text{dien\_chan}} + N_{\text{active\_custom}}$$

```
+------------------------------------+-------+-----------------------------------------------------------+
| Dataset Component                  | Count | Standard Citation & Provenance                            |
+------------------------------------+-------+-----------------------------------------------------------+
| WHO Classical 14 Channels          | 361   | WHO Standard Acupuncture Point Locations (WPRO 2008)      |
| National Standard Yintang Addition | +1    | GB/T 12346-2006 / GB/T 12346-2021 (GV24+ in Du Mai)       |
| Total Regular Canonical Points     | 362   | Base Canonical Reference (`acupuncture_3d.json`)           |
| Vietnamese Dien Chan Facial Points | 4     | Prof. Bui Quoc Chau (1980) (`lib_dien_chan` namespace)    |
| Clean Baseline Runtime Total       | 366   | Zero custom points installed (362 + 4)                    |
| Active Custom User Points          | N_c   | Dynamic SQLite query (`custom_points` WHERE is_deleted=0) |
+------------------------------------+-------+-----------------------------------------------------------+
```

### 2.1 The 361 vs 362 Point Derivation
* **WHO WPRO 2008:** Recognizes 361 classical points across the 14 regular channels (12 organ meridians totaling 309 points + 28 Governing Vessel (GV) points + 24 Conception Vessel (CV) points). In WHO standards, **Yintang** is classified as an Extra Point (`EX-HN3`).
* **GB/T 12346-2006 & GB/T 12346-2021:** Officially standardizes **Yintang** (`GV24+` / `GV29`) as the 29th point of Du Mai (Governing Vessel). This brings the canonical regular meridian point total to exactly **362**.

### 2.2 Namespace Isolation
To prevent cross-tradition contamination, each point belongs to an explicit namespace:
1. `WHO_CLASSICAL`: 361 standard channel points.
2. `EXTRA_POINTS`: Classical extra-meridian acupoints (Yintang, Taiyang, Huatuojiaji).
3. `DIEN_CHAN`: Vietnamese facial reflex landmarks (DC_0, DC_1, DC_26, DC_126).
4. `THAI_SEN_SIB`: Wat Po / MoPH traditional Sen Sib landmarks.
5. `MSK_LANDMARK`: BodyParts3D bony palpation landmarks and trigger points.
6. `USER_CUSTOM`: Locally authored custom points and clinical research observations.

---

## 3. Dynamic Lifecycle Verification

Automated integration test [`test_dynamic_reconciliation_math_lifecycle`](file:///D:/5Projects/msk-therapy-os/tests/test_security_and_governance.py#L225-L270) verifies that the API endpoint `/api/governance/reconciliation` recalculates totals dynamically:

```
[Clean Baseline DB]  -> ActiveCustom: 0 -> TotalRuntime: 366 (362 + 4 + 0)
[Add 1 Custom Point] -> ActiveCustom: 1 -> TotalRuntime: 367 (362 + 4 + 1)
[Add 2 Custom Points]-> ActiveCustom: 2 -> TotalRuntime: 368 (362 + 4 + 2)  <-- [Explains prior 368 metric]
[Soft-Delete 1 Point]-> ActiveCustom: 1 -> TotalRuntime: 367 (362 + 4 + 1)
[Restore Point]      -> ActiveCustom: 2 -> TotalRuntime: 368 (362 + 4 + 2)
```

At no point in the codebase is 368 hardcoded. The calculation in [`msk_therapy_os/server.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/server.py#L515-L537) executes:

```python
acu_cnt = len(d.get("points", {}))           # 362
dc_cnt = len(d.get("dien_chan", []))          # 4
active_custom = len(list_custom_points(db, include_deleted=False)) # N_c
runtime_total_points = acu_cnt + dc_cnt + active_custom
```

---

## 4. Visual Conservation Formula

In the 3D Atlas, when the Adaptive Scaling & Smart Density engine clusters or filters points at varying zoom levels, the total number of points satisfies exact conservation:

$$\text{Total Available Points} = \text{Visible Unclustered} + \text{Clustered Points} + \text{Filtered Inactive Points}$$

* Points are never deleted or modified during zoom operations.
* Centroids calculate arithmetic means of grouped coordinates.
* Clicking or zooming into a cluster expands it back into constituent points.
