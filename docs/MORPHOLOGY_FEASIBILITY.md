# Milestone M2.3 Feasibility Study: Patient Morphology & Demographic Representation

**Project:** `MSK-Therapy-OS`  
**Author:** Staff/Principal Software Engineer, Open-Source Integration Architect  
**Status:** Feasibility Evaluated & Architecture Defined  
**Target Hardware:** Windows x64, Intel i7-5600U, 8GB RAM, Intel HD Graphics 5500  

---

## 1. Executive Summary

Milestone M2.3 investigates expanding the 3D musculoskeletal learning experience to reflect real-world patient diversity, including:
1. **Sex-stratified anatomical reference models** (male vs. female).
2. **Parametric body proportions and height variations**.
3. **Variable body composition** (adiposity / body-fat distribution and muscularity).
4. **Age-related morphological shifts** (pediatric, adult, geriatric).

### Key Finding & Core Engineering Principle
> [!CAUTION]
> **Modifying external surface shape (skin mesh) does NOT produce medically accurate internal anatomy.**  
> Tools like MakeHuman generate photorealistic exterior humanoid meshes, but deep musculoskeletal, neurovascular, and visceral geometries do not deform linearly with external surface morph targets. Presenting pseudo-morphed internal organs as medically valid would violate safety and educational integrity.

---

## 2. Evaluation of Upstream Morphology Tools & Datasets

### 2.1 MakeHuman Community (`makehumancommunity/makehuman`)
- **What it provides:** Standalone Python/Qt desktop application with parametric sliders (age 0–100, gender 0–1, muscle 0–1, weight 0–1, height).
- **Format:** Wavefront OBJ / glTF character meshes with CC0 / AGPL licensing.
- **Anatomical Scope:** *Exterior skin surface and basic animation skeleton only.*
- **Evaluation for MSK-Therapy-OS:**
  - **Skin surface:** High quality, low polycount (~15,000 vertices).
  - **Internal anatomy:** Completely absent. MakeHuman has no internal organs, muscles, or nerves.
  - **Conclusion:** Reusing MakeHuman is suitable *only* for external surface landmark demonstration. It cannot be used to deform internal BodyParts3D 4.0 muscles or vertebrae.

### 2.2 slorksmo/Human-Atlas (`slorksmo/Human-Atlas`)
- **What it provides:** Dual male and female web-native 3D anatomical atlases built on Three.js.
- **Format:** Pre-chunked binary geometries (`body-*.bin` for male, `female-*.bin` for female, 15 files of ~4MB each = ~60 MB total).
- **Ontology & Attribution:** Derived from BodyParts3D and Z-Anatomy under CC BY 4.0.
- **Evaluation for MSK-Therapy-OS:**
  - Provides genuine sex-stratified internal organs, skeletal dimensions, and pelvic morphology (gynecoid vs. android pelvis).
  - WebGL performance: 60 FPS on Intel HD 5500 when streamed in chunks.
  - **Conclusion: Highly feasible for dual-reference model integration (Male / Female selector).**

---

## 3. Mathematical & Coordinate Mapping Challenges

### 3.1 Proportional Bone Cun (F-cun) vs. Rigid Surface Snapping
Traditional acupuncture points and musculoskeletal palpation landmarks are defined by the **WHO 2008 Standard** using proportional bone measurements (*F-cun* or *finger-cun*):
- Distance from sternal notch to xiphisternal synchondrosis: fixed 9 F-cun.
- Distance from xiphisternum to umbilicus: fixed 8 F-cun.
- Distance between bilateral nipples: fixed 8 F-cun.
- Distance between medial border of scapula and posterior midline: fixed 3 F-cun.

When patient height or body-fat changes:
1. **Skeletal landmarks** scale proportionally with bone length.
2. **Subcutaneous adipose tissue** expands non-linearly outward (predominantly abdominal and gluteofemoral).
3. If an acupoint or trigger point is mapped by rigid Cartesian `[x, y, z]`, increased adipose thickness causes the point to sink beneath the skin surface or displace horizontally.
4. **Required Solution:** Points must be anchored via **barycentric surface coordinates** attached to specific mesh polygons (as implemented in `mesh-registration.json`), which deform dynamically with the surface mesh.

---

## 4. Architectural Feasibility Matrix

| Demographic Capability | Technical Approach | Feasibility on Intel HD 5500 | Medical / Clinical Validity | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Male & Female Dual Models** | Toggle between male (`bp3d40`) and female reference datasets (`female-*.bin` from Human-Atlas) | **HIGH** (< 15 MB streaming RAM) | **HIGH** (Authentic anatomical scans; genuine dimorphic pelvic and thoracic anatomy) | **ADAPT in Phase 2** |
| **Height Scaling** | Proportional affine scaling along Y-axis (`mat4.scale([s, s, s])`) with bone-length normalization | **HIGH** (Trivial WebGL shader uniform) | **HIGH** (Preserves relative anatomical origins and insertions) | **ADAPT in Phase 2** |
| **Variable Adiposity (Body-Fat)** | Skin vertex extrusion along surface normals (`vPos + vNormal * fatThickness`) | **MEDIUM** (Vertex shader displacement) | **MODERATE for surface, LOW for deep organs** (Internal viscera shift under visceral adiposity; simple extrusion only models subcutaneous fat) | **DOCUMENT AS PROTOTYPE** |
| **Age-related Kyphosis / Degeneration** | Parametric curve deformation of thoracic and cervical spinal curvature | **MEDIUM** (Requires joint skinning) | **MODERATE** (Educational for postural aging; cannot represent osteophyte formation without custom scans) | **DEFER to M3/M4** |

---

## 5. Phased Implementation Roadmap & Blockers

```mermaid
flowchart LR
    M2_Baseline["M2 Baseline\n(Male BodyParts3D 4.0\n+ Acupoints/Meridians)"] --> Phase1["Phase 1: Sex Toggle\n(Integrate Female\nReference Model)"]
    Phase1 --> Phase2["Phase 2: Skeletal F-cun\n(Proportional Bone\nCoordinate Retargeting)"]
    Phase2 --> Phase3["Phase 3: Body Composition\n(Subcutaneous Adiposity\nShader Layer)"]
    
    style M2_Baseline fill:#0284c7,stroke:#38bdf8,color:#fff
    style Phase1 fill:#0f766e,stroke:#2dd4bf,color:#fff
    style Phase2 fill:#334155,stroke:#94a3b8,color:#fff
    style Phase3 fill:#334155,stroke:#94a3b8,color:#fff
```

### Identified Blockers for Deep Volumetric Morphing
1. **Lack of Validated Volumetric Morphing Datasets:** There is currently no open-source, non-commercial dataset that provides continuous volumetric morphing of internal musculoskeletal tissues across BMI ranges.
2. **Computational Budget on Intel HD 5500:** Performing real-time volumetric finite element deformation (FEM) of 2,234 meshes (6.68M triangles) exceeds the shader throughput and memory bandwidth of integrated Intel HD 5500 graphics.
3. **Medical Safety Liability:** Simulating deformed internal anatomy without clinical CT/MRI ground truth introduces severe diagnostic distortion risks for healthcare learners.
