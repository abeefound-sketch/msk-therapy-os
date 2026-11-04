# MSK-Therapy-OS — Milestone P19 Forensic Audit
## P19_03: Deep Coordinate Lineage, Surface Projection & Discrepancy Forensic Report

**Tài liệu ID:** `MSK-P19-LIN-003`  
**Ngày thực hiện:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Auditor Roles:** Principal 3D Geometry Engineer + Forensic Auditor + Anatomical Registration Specialist  
**Điểm kiểm toán trọng tâm:** `LI4` (Hợp Cốc), `ST36` (Túc Tam Lý), `KI3` (Thái Khê), cùng `GV14` (Đại Chùy) & `GB21` (Kiên Tỉnh)  

---

### 1. Chuỗi Truy Vết Dòng Dữ Liệu (authoritative 9-Stage Lineage Pipeline)

Mọi tọa độ hiển thị trên màn hình đều phải đi qua chuỗi 9 chặng sau:

```text
[1. Upstream Document / Dataset] (WHO 2008 / JICio tcm-3d / BodyParts3D 4.0)
     │
     ▼
[2. Source Coordinates & Landmark Rules] (Tọa độ gốc hoặc định nghĩa mốc giải phẫu)
     │
     ▼
[3. Transform & Axis Convention] (Origin floor/pelvis, handedness, +X Right vs +X Left)
     │
     ▼
[4. Canonical Point Resolution] (Laterality right/left/midline, B-cun proportional rule)
     │
     ▼
[5. Mesh Projection & Query] (Khoảng cách tới mặt da fj2810_softened.bin qua BVH/Grid)
     │
     ▼
[6. Server Layer & SQLite Precedence] (canonical vs legacy vs upstream; override priority)
     │
     ▼
[7. REST API Response] (GET /api/acupuncture-3d, POST /api/atlas/geometry/resolve)
     │
     ▼
[8. Frontend State & WebGL Viewport] (AtlasSpatialState, mat4 perspective, projectPoint)
     │
     ▼
[9. Human Domain / Clinical Verification] (PENDING_EXPERT_REVIEW - Cấm tự tuyên bố)
```

---

### 2. Bảng Đo Đạc Thực Tế Trên Authentic Mesh vs. Canonical Resolver

Thực nghiệm đo đạc trực tiếp trên mô hình BodyParts3D softened skin mesh (`fj2810_softened.bin`, SHA-256 `05b49233...`, 24,958 đỉnh, 46,174 tam giác). Bounding box chuẩn:
- $X \in [-0.334004, +0.332754]\text{ m}$ (Chiều rộng cơ thể: $0.6668\text{ m}$)
- $Y \in [0.000000, +1.719431]\text{ m}$ (Chiều cao cơ thể: $1.7194\text{ m}$)
- $Z \in [-0.145239, +0.146783]\text{ m}$ (Chiều sâu lồng ngực/bụng: $0.2920\text{ m}$)

| Acupoint | Nguồn Baked JSON $[X, Y, Z]$ | Khoảng cách tới Mesh mặt da (mm) | Tam giác Mesh | Nguồn Canonical Resolver $[X, Y, Z]$ | Khoảng cách tới Mesh mặt da (mm) | Bounding Box Mesh | Sai lệch Euclidean $\Delta$ (Baked vs Canon) | Nguyên nhân bản chất (Root Cause) |
|---|---|---|---|---|---|---|---|---|
| **`LI4`** (Hợp cốc) | `[0.2860, 0.8310, 0.0141]` | **0.002 mm** (Mặt da thực) | #40601 (Khớp 100%) | `[0.3420, 0.8120, 0.0820]` | **13.736 mm** (Bay lơ lửng) | **VI PHẠM VÙNG BIÊN** ($X=0.3420 > 0.3328$, bay ra ngoài 9.25mm) | **90.01 mm** | Mốc giải phẫu xương đốt bàn ngón II bị đặt ở tư thế dạng tay không trùng với tư thế chuẩn buông xuôi của BodyParts3D |
| **`ST36`** (Túc tam lý) | `[0.1110, 0.3680, 0.0146]` | **0.004 mm** (Mặt da thực) | #30941 (Khớp 100%) | `[0.1120, 0.3880, 0.0640]` | **45.842 mm** (Bay phía trước cẳng chân) | Nằm trong BBox | **53.28 mm** | Quy tắc B-cun 3 thốn dưới Độc Tỵ được tính theo tỷ lệ chiều cao phẳng, đặt Z ra trước mào chày 4.5 cm |
| **`KI3`** (Thái khê) | `[-0.0759, 0.0845, -0.0705]` | **0.000 mm** (Mặt da thực) | #13875 (Khớp 100%) | `[0.0904, 0.0559, -0.0223]` | **17.003 mm** | Nằm trong BBox | **175.45 mm** (Cực đại) | **XUNG ĐỘT QUY ƯỚC TRỤC X**: Baked JSON quy định $+X$ Left (chân phải mang dấu âm), Canonical Rule hiểu nhầm $+X$ Right nên gán chân phải dấu dương! |
| **`GV14`** (Đại chùy) | `[0.0000, 1.4465, -0.0850]` | **16.960 mm** (Thụt vào trong) | #21933 | `[0.0000, 1.4720, -0.0950]` | **0.843 mm** (Mặt da gai C7) | Nằm trong BBox | **27.39 mm** | Baked JSON bắt nhầm mặt phẳng mô mềm nông dưới gai C7; Canonical anchor C7 khớp mốc xương chính xác hơn |
| **`GB21`** (Kiên tỉnh) | `[0.0725, 1.4580, -0.0580]` | **14.206 mm** (Lõm vào trong) | #29231 | `[0.1080, 1.4480, 0.0120]` | **22.071 mm** (Nhô ra trước) | Nằm trong BBox | **79.12 mm** | Độ cong cơ thang (m. trapezius) lượn 3D; phép chiếu đường thẳng giữa C7 và mỏm cùng vai bỏ qua độ võng của vai |

---

### 3. Điều Tra Sâu Về Xung Đột Hệ Trục Tọa Độ: `+X Right` vs. `+X Left`

#### 3.1 Nguồn gốc của mâu thuẫn
- Trong `1docs/COORDINATE_REGISTRY.md` (biên soạn 2026-10-21):
  - Định nghĩa lý thuyết: Hệ tọa độ Descartes bàn tay phải: $+X$ Right (phải giải phẫu của người bệnh), $+Y$ Superior (hướng đầu), $+Z$ Anterior (hướng trước bụng).
- Trong `msk_therapy_os/static/atlas/data/acupuncture_3d.json` (dữ liệu kế thừa từ BodyParts3D 4.0 và JICio/tcm-3d):
  - Metadata ghi rõ: `"coordinate_system": "BodyParts3D 4.0 / Open Anatomy Atlas (Meters: +X Left, +Y Superior, +Z Anterior)"`.
  - Trên mô hình giải phẫu gốc của BodyParts3D (Nhật Bản), trục $+X$ là phía **trái bệnh nhân (Patient Left)**, tương đương với bên phải màn hình khi người dùng nhìn đối diện từ phía trước ($+Z$).

#### 3.2 Hậu quả trong mã nguồn
- Khi các kỹ sư phát triển `point_localization_rules.py`, họ đọc tài liệu `COORDINATE_REGISTRY.md` và gán tọa độ mốc cho nửa người bên phải bằng tọa độ dương ($X > 0$).
- Kết quả đối với huyệt **KI3 (Thái khê)**:
  - Vị trí thực tế trên chân phải của mesh BodyParts3D: $X = -0.07589\text{ m}$.
  - Vị trí do `point_localization_rules.py` tính toán cho chân phải: $X = +0.09040\text{ m}$.
  - Chênh lệch trục X: $|+0.09040 - (-0.07589)| = 0.16629\text{ m} = 166.29\text{ mm}$!
  - Khi cộng thêm độ lệch trục Y và Z, sai lệch khoảng cách không gian chạm mốc **$175.45\text{ mm}$**, đẩy huyệt Thái khê từ cổ chân phải nhảy sang khoảng không hoặc phía trong cổ chân trái!

#### 3.3 Phán quyết kỹ thuật P19
- **CẤM** sửa lỗi bằng cách tự ý nhân $-1$ hàng loạt trên toàn bộ 362 huyệt.
- Giữ nguyên trạng thái độc lập của các nguồn. Ghi nhận rõ:
  1. File `acupuncture_3d.json` tuân thủ quy ước trục của BodyParts3D ($+X$ Left).
  2. Bảng `COORDINATE_REGISTRY.md` mô tả quy ước chuẩn giải phẫu cổ điển ($+X$ Right) nhưng chưa đồng bộ biến đổi với asset nhị phân.
  3. Tại P19, ghi nhận trạng thái `COORDINATE_HANDEDNESS_DISCREPANCY` vào `P19_04_RUNTIME_CONFLICT_MATRIX.md`. Chuyển đổi chính thức được đưa vào Gate phê duyệt của Milestone P22.

---

### 4. Kiểm Tra Tính Hiện Diện Thật Của 3D Mesh Runtime

#### 4.1 Phân tích Runtime Loader của WebGL Atlas (`/atlas/`)
1. Khi trình duyệt mở `/atlas/`, hàm `loadBest()` trong `app.js` cố gắng đọc file `data/atlases.json`.
2. File `data/atlases.json` trên đĩa có nội dung: `{"atlases": [], "default": ""}`.
3. Không tìm thấy atlas nhị phân nào được cấu hình tải qua mạng, `loadBest()` kích hoạt cơ chế fallback: gọi `buildProceduralAtlas()` từ `procedural.js`.
4. Trình duyệt vẽ một ma-nơ-canh ước lượng được tạo từ các khối hình học cơ bản (`Geometry.genSphere`, `Geometry.genCapsule`, `Geometry.genBox`) với khoảng 2,400 đỉnh.
5. **KẾT LUẬN QUAN TRỌNG:** Giao diện WebGL Atlas ở chế độ offline **CHƯA TỪNG TẢI** file `fj2810_softened.bin`!
6. Băng cảnh báo do P18 thiết lập:
   `[UNVERIFIED PROCEDURAL GEOMETRY] Đang sử dụng ma-nơ-canh ước lượng (Demo Mannequin). Tọa độ huyệt và đường kinh chỉ mang tính chất minh họa thao tác, CHƯA ĐƯỢC THẨM ĐỊNH trên mô hình chuẩn BodyParts3D FJ2810.`
   Cảnh báo này là chính xác 100% với sự thật runtime.

#### 4.2 Phân tích Mô hình GLB trong Education Studio (`/education/?v=p17`)
- Thư mục `msk_therapy_os/static/education/models/` chứa 3 file GLB:
  - `anatomy.glb` (9.29 MB): Mô hình cơ và xương toàn thân.
  - `cervicothoracic_skeleton.glb` (1.54 MB): Mô hình cột sống cổ - ngực.
  - `shoulder_skeleton.glb` (0.39 MB): Khớp vai và xương bả vai.
- Các file này chỉ được tải bởi `static/education/app.js` cho mục đích giảng dạy cơ sinh học cơ-xương-khớp.
- Không có bất kỳ đường liên kết nào giữa các file GLB này và hệ thống huyệt kinh lạc của Atlas 3D.

---

### 5. Cơ Chế Ưu Tiên Ghi Đè (Runtime Precedence Hierarchy)

Khi client gọi API hoặc cập nhật giao diện, thứ tự ưu tiên tuyệt đối được quy định như sau:

```text
[Ưu tiên 1 - Cao nhất] SQLite Reference Overrides (bảng `reference_point_overrides`)
    ↳ Chỉ áp dụng khi có bản ghi hợp lệ do Admin/Reviewer phê duyệt
    
[Ưu tiên 2] User Custom Points (bảng `custom_points`)
    ↳ Điểm do người dùng định nghĩa, mang namespace riêng

[Ưu tiên 3] Canonical Spatial Resolver (tùy thuộc `layer_mode` do người dùng chọn trên UI):
    ↳ `canonical`: Tọa độ B-cun hoặc AUDITED_CANONICAL_POINTS
    ↳ `pose_adjusted`: Tính thêm góc khớp động học
    ↳ `legacy_raycast`: Tọa độ chiếu bề mặt lịch sử
    ↳ `upstream_raw`: FAIL-CLOSED (trả về UPSTREAM_TRANSFORM_UNAVAILABLE)

[Ưu tiên 4 - Mặc định dữ liệu] Static Baked Dataset (`acupuncture_3d.json`)
    ↳ Dữ liệu chiếu tia mặt da lịch sử BodyParts3D FJ2810

[Ưu tiên 5 - Fallback hình học] Procedural Mannequin (`DEMO-BODY`)
    ↳ Khi không có binary mesh tải về, luôn bật cờ UNVERIFIED PROCEDURAL GEOMETRY
```

**Bảo đảm an toàn:** Không có bất kỳ cơ chế ghi đè âm thầm nào được phép che giấu sai lệch. Mọi sai lệch giữa các lớp đều được log và hiển thị trên panel QA Inspector (`meridians.js:updateP9QAInspector`).
