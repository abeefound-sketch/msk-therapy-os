# MSK-Therapy-OS — Milestone P19 Forensic Audit
## P19_04: Runtime Conflict Matrix, Fallbacks & Silent Overrides Detection

**Tài liệu ID:** `MSK-P19-RCM-004`  
**Ngày thực hiện:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Vai trò:** Forensic Code Auditor + Data Provenance Engineer  

---

### 1. Bảng Ma Trận Xung Đột Runtime & Cơ Chế Fallback (Conflict Matrix)

| ID Xung đột | Thành phần xung đột A | Thành phần xung đột B | Biểu hiện sai lệch quan sát được | Mức độ nghiêm trọng | Trạng thái xử lý tại P18 / P19 | Cơ chế Fail-Safe hoặc Fallback | Bằng chứng tái lập |
|---|---|---|---|:---:|---|---|---|
| **CONF-01** | `1docs/COORDINATE_REGISTRY.md` ($+X$ Right) | `acupuncture_3d.json` ($+X$ Left BodyParts3D) | Tọa độ huyệt chân phải KI3 bị ngược dấu X: $-0.0759$m vs $+0.0904$m, gây sai số không gian $175.45$ mm | **CRITICAL** | Ghi nhận mâu thuẫn hệ trục trong P19 audit; cấm lật dấu hàng loạt | Hiển thị trung thực 2 nguồn trong bảng đối chiếu; giữ nguyên trạng thái P18 | `scratch/trace_points_audit.py`, `tools/forensics/compare_spatial_sources.py` |
| **CONF-02** | WebGL UI tuyên bố dùng BodyParts3D FJ2810 | File `data/atlases.json` rỗng (`{"atlases": []}`) | Trình duyệt thực tế render `DEMO-BODY` (ma-nơ-canh ghép từ hình cầu/trụ của `procedural.js`) | **HIGH** | Đã xử lý ở P18: gắn banner cảnh báo vĩnh viễn trên UI | Hiển thị banner màu vàng cam `[UNVERIFIED PROCEDURAL GEOMETRY]` | `tests/test_p18_geometry_remediation.py::test_procedural_fallback_status_contract` |
| **CONF-03** | Baked Static JSON (`acupuncture_3d.json`) | Canonical Spatial Resolver (`AnatomicalSpatialResolver`) | 130/362 điểm lệch $\ge 50$mm; 28 điểm lệch $\ge 100$mm; LI4 bay ra ngoài mesh $9.25$mm | **HIGH** | Ghi nhận chi tiết trong `P18_ACUPOINT_RECONCILIATION.csv` và P19 Lineage | Cung cấp tùy chọn chuyển layer rõ ràng (`canonical` vs `legacy_raycast`); QA panel hiển thị sai lệch | `1docs/audits/P18/P18_ACUPOINT_RECONCILIATION.csv` |
| **CONF-04** | Chế độ `upstream_raw` ban đầu (thêm hằng số giả $dx, dy, dz$) | Yêu cầu trung thực dữ liệu nguồn | Trước P18, mã nguồn cộng bừa $dx=-8$mm, $dy=+12$mm, $dz=-10$mm rồi ghi là delta model | **CRITICAL (Dữ liệu giả)** | Đã xóa triệt để ở P18 commit `4990f17` | **Fail-closed**: Trả về `UPSTREAM_TRANSFORM_UNAVAILABLE`, không cộng số giả | `tests/test_p18_reproducible_failures.py::test_reproduce_upstream_raw_synthetic_offset_defect` |
| **CONF-05** | Cache đường kinh trong `MeridianSurfacePathEngine` | Thay đổi tọa độ đầu vào của huyệt | Sửa tọa độ huyệt nhưng engine trả về đường kinh cũ từ in-memory cache | **HIGH** | Đã xử lý ở P18: bổ sung `point_digest` SHA-256 vào cache key | Thay đổi bất kỳ tọa độ nào sẽ tự động vô hiệu hóa cache cũ và tính toán lại | `tests/test_p18_geometry_remediation.py::test_meridian_engine_cache_invalidates_on_point_mutation` |
| **CONF-06** | UI tuyên bố kiểm tra chiều sâu WebGL Depth Buffer | Mã nguồn thực tế trong `meridians.js` | Không gọi `gl.readPixels()` vì gây nghẽn GPU trên chip Intel HD 5500; chỉ dùng dot-product pháp tuyến | **MEDIUM** | Đã sửa thông báo ở P18 | QA Inspector ghi rõ `OCCLUSION_APPROXIMATE (Normal-facing / Raycast; WebGL depth buffer unbound)` | `msk_therapy_os/static/atlas/meridians.js:updateP9QAInspector` |
| **CONF-07** | Mô hình 3D trong Education Studio (`static/education/models/`) | Mô hình 3D trong Meridian Atlas (`static/atlas/`) | Người dùng có thể lầm tưởng các file `.glb` giải phẫu của Studio đang được Atlas sử dụng | **MEDIUM** | Phân lập hoàn toàn ranh giới giữa Studio và Atlas | Không chia sẻ mô hình hay asset qua lại; Studio chỉ phục vụ đào tạo cơ-xương-khớp | `P19_01_ARCHITECTURE_MAP.md` |
| **CONF-08** | Lạm phát nhãn chất lượng (Quality Inflation) | Phân loại độ tin cậy thực tế | Trước P18, toàn bộ 344 điểm đều bị ép gắn nhãn `CLASS_B` dù không có mốc kiểm định | **HIGH** | Thiết lập bảng phân loại chất lượng 5 bậc chặt chẽ trong `geometry_contracts.py` | `CLASS_A` (18 điểm mốc duyệt), `CLASS_B` (B-cun có cơ sở), `CLASS_D` (hình học ước lượng) | `tests/test_p18_reproducible_failures.py::test_reproduce_quality_classification_overclaim` |

---

### 2. Chi Tiết Các Cơ Chế Ghi Đè Âm Thầm Đã Bị Vô Hiệu Hóa

1. **Vô hiệu hóa việc ghi đè tọa độ không dấu vết:**
   - Trong `server.py`, endpoint `/api/acupuncture-3d` hợp nhất các bản ghi từ SQLite `reference_point_overrides`.
   - Nếu có override, thuộc tính `is_overridden: true` bắt buộc phải được trả về kèm `notes` và `review_status`.
   - Bảng `reference_point_overrides` hiện có `0` bản ghi trên database gốc, đảm bảo không có sự can thiệp dữ liệu ngầm.

2. **Cơ chế Fail-Closed của Upstream Raw:**
   - Khi gọi layer `upstream_raw`, hệ thống trả về:
     ```json
     {
       "registration_status": "UPSTREAM_TRANSFORM_UNAVAILABLE",
       "rejection_reason": "No empirical transformation matrix between upstream mesh and BodyParts3D FJ2810. Synthetic offset removed under P18 governance."
     }
     ```
   - Không sinh dữ liệu ngẫu nhiên, không suy diễn ma trận quay chưa kiểm chứng.

3. **Ngăn chặn tự nâng cấp trạng thái xác thực lâm sàng:**
   - Hằng số `CLINICAL_VALIDATION = "NOT_ESTABLISHED"` và `RELEASE_SCOPE = "ENGINEERING_RESEARCH_ONLY"` được khóa cứng tại cấp độ module và được xác thực qua test suite `test_p18_geometry_remediation.py`.
   - Bất kỳ mã nguồn nào cố gắng trả về `ANATOMICAL_VERIFIED` mà không qua quy trình kiểm định chuyên gia đều bị test suite đánh trượt.
