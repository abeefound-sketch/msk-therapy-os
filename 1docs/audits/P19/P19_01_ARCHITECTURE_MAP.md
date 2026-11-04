# MSK-Therapy-OS — Milestone P19 Architecture Map
## P19_01: Module Ownership, Runtime Dependency & Duplication Audit

**Tài liệu ID:** `MSK-P19-MAP-001`  
**Ngày lập:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Vai trò:** Principal Software Architect + Forensic Auditor  

---

### 1. Bản Đồ Tổng Thể Các Khối Chức Năng (Target Logic Architecture)

Hệ thống được chuẩn hóa thành 5 khối chức năng theo hợp đồng phân định rõ ràng, chạy chung monorepo nhưng tách biệt ranh giới dữ liệu và luồng thực thi:

```text
MSK-Therapy-OS (Shell / Orchestration / Auth / Observability)
    |
    +-- 1. Anatomical Atlas (anatomy mesh + landmarks + traditional acupoints + meridian overlays)
    |      `-- Source adapters + transform registry + independent validation
    |
    +-- 2. Knowledge Vault (Markdown + originals + claims + citations + contradictory viewpoints)
    |      `-- SQLite indexing / full text search / immutable provenance (P20 - Hoạt động độc lập)
    |
    +-- 3. Clinical Workspace (SOAP / ROM / outcomes / visits; isolated patient store - Synthetic only)
    |
    +-- 4. Education Studio (Kinematics / Biomechanics / Muscle activation / Cervicothoracic models)
    |
    `-- 5. Adapter & Verification (contracts / licensing / lineage / tests / evidence gates)
```

---

### 2. Bảng Kiểm Toán Chi Tiết Từng Module (Module Inventory & Audit Matrix)

| Module / File | Chức năng chính | Runtime Entrypoint | Inputs | Outputs | Data Writes | Calls / Dependencies | Owner đề xuất | Chức năng trùng lặp / Xung đột | Quyết định P19 | Bằng chứng thực tế |
|---|---|---|---|---|---|---|---|---|---|---|
| `msk_therapy_os/server.py` | HTTP Server (REST API, static files, auth routing, CORS) | `create_server()`, `MSKRequestHandler` | HTTP requests trên port 8080/ephemeral | JSON responses, HTML/JS/CSS, binary chunks | SQLite (khi mutate) | `auth.py`, `spatial_resolver.py`, `assessment.py`, `points.py`, `safety.py` | Shell / Platform Team | Trộn lẫn logic điều phối Atlas, Education, Auth, và DB trong cùng file (>2800 dòng) | **KEEP** (Không refactor lớn ở P19; giữ tương thích 100%) | `tests/test_server.py` (13 tests PASS) |
| `msk_therapy_os/spatial_resolver.py` | Giải tọa độ không gian 4 lớp (`canonical`, `legacy_raycast`, `upstream_raw`, `pose_adjusted`) | `AnatomicalSpatialResolver.resolve_point()`, `resolve_atlas_geometry()` | Point code, layer_mode, morphology, joint_angles, sqlite_overrides | GeoJSON-like dict (XYZ, normals, status, instances) | Không ghi (Read-only) | `landmark_registry.py`, `point_localization_rules.py`, `cun_scaling.py`, `geometry_contracts.py` | Spatial Engine Team | Xung đột tọa độ với baked `acupuncture_3d.json` (130 điểm lệch $\ge 50$mm; LI4 bay ra ngoài mesh 9.2mm) | **ISOLATE** (Bảo toàn hợp đồng P18; fail-closed `UPSTREAM_TRANSFORM_UNAVAILABLE`) | `tests/test_p18_geometry_remediation.py`, `tests/test_p18_reproducible_failures.py` |
| `msk_therapy_os/meridian_surface_engine.py` | Dựng đường kinh lạc 3D dạng spline bám mặt da có kiểm tra cache | `MeridianSurfacePathEngine.reconstruct_channel()` | Channel code, side, points dict, mesh normals | Mảng đa giác 3D (polyline vertices, normals, face indices) | In-memory cache | `geometry_contracts.py` (point digest computation) | Spatial Engine Team | Spline Catmull-Rom nâng độ cao sagitta không chiếu qua KD-tree raycast trên GPU | **KEEP** (Đã gắn point_digest SHA-256 ở P18 ngăn stale cache) | `tests/test_p18_geometry_remediation.py::test_meridian_engine_cache_invalidates_on_point_mutation` |
| `msk_therapy_os/meridian_route_graph.py` | Đồ thị kết nối topology các đường kinh và nhánh huyệt | `get_meridian_graph()` | Channel codes | Danh sách cạnh, đỉnh, waypoint | Không ghi | `point_localization_rules.py` | Spatial Engine Team | Cung cấp topo độc lập với đường vẽ polyline trong baked JSON | **KEEP** (Dùng làm cơ sở tái thiết P23) | `tests/test_p9_4_definitive_atlas.py` |
| `msk_therapy_os/landmark_registry.py` | Danh mục mốc xương và cơ giải phẫu BodyParts3D | `get_landmark()`, `LANDMARK_REGISTRY` | Landmark ID | Tọa độ 3D, FMA ID, cấu trúc giải phẫu | Không ghi | Không | Anatomy Modeling Team | Trùng một phần định nghĩa mốc với `research/workbench/` | **KEEP** (Nguồn mốc giải phẫu cốt lõi cho B-cun) | `tests/test_p9_9_skeletal_registration.py` |
| `msk_therapy_os/point_localization_rules.py` | Quy tắc định vị huyệt theo tỷ lệ B-cun của WHO 2008 | `PointLocalizationEngine.resolve_point_location()` | Acupoint code | Tọa độ suy luận, chất lượng tier, công thức | Không ghi | `landmark_registry.py`, `cun_scaling.py` | Clinical Anatomy Team | Tự tính tọa độ độc lập với baked JSON, dẫn tới lệch KI3 175.45mm do nhầm dấu trục X | **KEEP** (Gắn nhãn CLASS_B; không dùng cho needle guidance) | `tests/test_p18_reproducible_failures.py::test_reproduce_two_spatial_sources_drift` |
| `msk_therapy_os/cun_scaling.py` | Tính toán tỷ lệ thốn F-cun và B-cun | `CunScaleEngine` | Chiều cao, chiều dài xương chi | Tỷ lệ co giãn (m/cun) | Không ghi | Không | Clinical Anatomy Team | Trùng logic tính toán trong `biomechanics_adapter.py` | **KEEP** (Chuẩn hóa công thức B-cun chuẩn WHO) | `tests/test_p9_pose_aware_registration.py` |
| `msk_therapy_os/points.py` | Quản lý database huyệt, custom points, overrides | `list_custom_points()`, `save_point_override()` | SQLite connection, payload | Bản ghi huyệt cá nhân hóa | Ghi bảng `custom_points`, `reference_point_overrides` | `db.py`, `auth.py` | Data Governance Team | Có thể ghi đè tọa độ chuẩn nếu quyền Admin/Reviewer | **KEEP** (Bảo vệ qua RBAC và audit trail) | `tests/test_security_and_governance.py` |
| `msk_therapy_os/geometry_contracts.py` | Hợp đồng chất lượng hình học và Mesh identity | `AcupointQualityTier`, `MeshIdentity` | Tọa độ, normals, codes | Digest SHA-256, Contract Enums | Không ghi | `hashlib`, `json` | Governance Team | Được bổ sung ở P18 để chặn overclaim CLASS_B | **KEEP** (Nền tảng hợp đồng cho P19/P20) | `tests/test_p18_geometry_remediation.py` |
| `msk_therapy_os/biomechanics_adapter.py` | Adapter động lực học, cơ tham gia, kích hoạt cơ cho Studio | `BiomechanicsAdapter` | Khung giờ vận động, góc khớp, mode A/B/C/D | Chỉ số góc cơ học, tỷ lệ tham gia cơ, activation curves | Không ghi | `kinematics.py` | Biomechanics Team | Trùng lặp một số góc khớp với `pose_rigging.py` | **KEEP** (Dành riêng cho Education Studio `/education/`) | `tests/test_p17_functional_acceptance_playwright.py` |
| `msk_therapy_os/kinematics.py` | Tính toán góc vận động đốt sống cổ và chi dưới | `compute_joint_angles()` | Dữ liệu chuyển động | Góc uốn/duỗi/xoay | Không ghi | Không | Biomechanics Team | Phục vụ bài học P14/P15/P16 | **KEEP** | `tests/test_kinematics.py` |
| `msk_therapy_os/safety.py` | Bộ chặn cứng an toàn lâm sàng, cấm châm cứu xâm lấn, cấm DDS | `screen_safety_flags()`, `hard_stop()` | Triệu chứng, cờ đỏ lâm sàng | Kết quả chặn, chuyển viện khẩn | Ghi bảng `safety_logs` | Không | Clinical Safety Team | Duy nhất | **KEEP** (Hằng số an toàn tối thượng) | `tests/test_safety.py` (6 tests PASS) |
| `msk_therapy_os/auth.py` | Quản lý xác thực, RBAC, phân quyền Reviewer/Admin | `authenticate()`, `require_role()` | Session token, credentials | Quyền hạn, danh tính | Ghi bảng `users`, `sessions` | `db.py` | Security Team | Duy nhất | **KEEP** | `tests/test_auth_and_rbac.py` (22 tests PASS) |
| `msk_therapy_os/static/atlas/` (JS/HTML) | Giao diện WebGL Atlas 3D kinh lạc, Three.js viewer, SVG overlays | Browser URL `/atlas/` | Dữ liệu `/api/acupuncture-3d`, WebGL contexts | Render 3D ma-nơ-canh và các huyệt trên canvas | LocalStorage | Three.js (vendored) | Frontend Team | WebGL tải `DEMO-BODY` procedural, trong khi UI ghi BodyParts3D | **KEEP WITH WARNING** (P18 đã gắn cảnh báo `UNVERIFIED PROCEDURAL GEOMETRY`) | `tests/test_p9_2_playwright_atlas.py` |
| `msk_therapy_os/static/education/` (JS/HTML/GLB) | Giao diện MSK Education Studio 3D (P13-P17) | Browser URL `/education/?v=p17` | Dữ liệu GLB mô hình giải phẫu | Render chuyển động cơ sinh học khớp cổ-vai | LocalStorage | Three.js | Education Team | Có 3 file `.glb` độc lập, không chia sẻ mesh với Atlas `/atlas/` | **ISOLATE** (Tách bạch rõ ranh giới với Anatomical Atlas) | `tests/test_p17_functional_acceptance_playwright.py` |
| `research/workbench/` | Bộ công cụ kiểm chuẩn giải phẫu offline và đo khoảng cách mesh | CLI scripts (`python -m research.workbench.cli`) | `fj2810_softened.bin`, datasets | Báo cáo kiểm định hình học | Xuất CSV/JSON | `numpy`, `struct` | Research Team | Độc lập với runtime WebGL | **KEEP** (Công cụ đo đạc pháp y chuẩn) | `tests/test_anatomical_workbench.py` (13 tests PASS) |
| `msk_therapy_os/dien_chan/` | Hệ thống phản chiếu diện chẩn khuôn mặt 2D/3D | `/api/dien-chan/points` | Tọa độ mặt, hình ảnh nguồn | Danh sách huyệt diện chẩn | Không ghi | `server.py` | Traditional Medicine Team | Không trùng với 14 kinh lạc; hệ tọa độ mặt riêng | **ISOLATE** (Giữ độc lập, namespace `DIEN_CHAN_REFLEX`) | `tests/test_dien_chan_core.py`, `tests/test_dien_chan_playwright.py` |

---

### 3. Đánh Giá Trùng Lặp & Xung Đột Quyết Định (Conflict Analysis)

1. **Atlas WebGL vs. Spatial Resolver:**
   - *Thực trạng:* `server.py` tải `acupuncture_3d.json` (baked raycast coordinates) nhưng đồng thời bổ sung `canonical_position` từ `spatial_resolver.py`. Trên giao diện `meridians.js`, khi layer_mode là `canonical`, `resolved_world_position` được ưu tiên hơn `position`.
   - *Khuyến nghị:* Giữ nguyên cơ chế chuyển layer có thông tin minh bạch; cấm ghi đè âm thầm.

2. **Education Studio vs. Meridian Atlas Mesh:**
   - *Thực trạng:* Thư mục `static/education/models/` có `anatomy.glb`, `cervicothoracic_skeleton.glb`, `shoulder_skeleton.glb`. Thư mục `static/atlas/` lại không có file `.glb` nào và chạy procedural mannequin `DEMO-BODY`.
   - *Khuyến nghị:* Cô lập hoàn toàn 2 subsystem. Không được cho phép người dùng lầm tưởng Atlas đang sử dụng mesh giải phẫu của Studio.

3. **Knowledge Vault vs. Clinical Patient Store:**
   - *Thực trạng:* Trước P20, tài liệu y văn nằm rải rác trong `1docs/EVIDENCE.md` và mã nguồn cứng. Database `msk_therapy_os.sqlite3` chứa các bảng lâm sàng (`cases`, `visits`, `soap_notes`).
   - *Khuyến nghị:* Triển khai P20 Knowledge Vault với **database SQLite riêng biệt (`vault.db`)**, hoàn toàn độc lập với `msk_therapy_os.sqlite3` để bảo vệ ranh giới an toàn dữ liệu y tế.
