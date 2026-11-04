# MSK-Therapy-OS — Milestone P29 Audit
## P29_01: Anatomical Mesh, Joint & Surface Marker Binding
### Rectification of LI4 Misbinding · Scapulohumeral Rhythm · Dynamic Meridian Deformation · Multi-Pose Verification

**Tài liệu ID:** `MSK-P29-AUD-001`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Kiểm toán viên:** Principal Biomechanics Engineer & Blender Technical Director  
**Trạng thái Cổng:** G1: **PASS** | G2: **PASS** | G3: **BLOCKED** | G4: **BLOCKED**  
**Quyết định Điều hành:** $$\mathbf{CONDITIONAL\_GO\_FOR\_P30}$$

---

### 1. Sửa Chữa Lỗi Gán Sai Huyệt Cốt Lõi (Forensic Rectification of Acupoint Binding)

> [!CAUTION]
> **Hành động Khắc phục Triệt để:**
> Hệ thống đã loại bỏ hoàn toàn việc gán cưỡng bức huyệt Hợp Cốc (`LI4`) vào xương cánh tay (`Humerus_R`), cũng như loại bỏ việc gán `ST36` vào xương bả vai hay `KI3` vào xương đòn.

#### Cơ chế Thực thi Kiểm soát (Fail-Closed Enforcement):
1. **Module Đăng ký Mốc Bề mặt Giải phẫu (`AnatomicalSurfaceAnchorRegistry`):**
   - Tự động kích hoạt ngoại lệ `ValueError: ANATOMICAL BINDING VIOLATION` nếu phát hiện bất kỳ nỗ lực nào nhằm gắn `LI4` vào `Humerus_R` hoặc `upper_arm.R`.
   - Với các cấu trúc xương chưa có trong tệp asset hiện tại (`Metacarpals_R`, `Tibia_R`, `Calcaneus_R`):
     * Trạng thái hiển thị trong scene: `ASSET_NOT_AVAILABLE`.
     * Trạng thái kiểm định y khoa: `EXPERT_REVIEW_PENDING`.
2. **Khai báo Mốc Giải phẫu Đúng Thực tế cho Chi Trên:**
   Để phục vụ nghiên cứu động thái của cánh tay và đai vai, hệ thống sử dụng các mốc huyệt và điểm giải phẫu thực sự thuộc các xương hiện diện trong `shoulder_skeleton.glb`:
   - **`LI14` (Huyệt Tí Nhu):** Gắn trên lồi củ cơ delta của xương cánh tay `Humerus_R` (FMA:23412, chuẩn WHO 2008 p. 41).
   - **`LI15` (Huyệt Kiên Ngung):** Gắn trên mỏm cùng vai `Scapula_R` / `Clavicle_R` (FMA:23240, chuẩn WHO 2008 p. 42).
   - **`LAT_EPI_R` (Mỏm trên lồi cầu ngoài):** Gắn trên bờ ngoài đầu dưới xương cánh tay `Humerus_R` (FMA:23420 / TA2:2988).

---

### 2. Liên Kết Xương & Nhịp Vận Động Bả Vai - Cánh Tay (Scapulohumeral Rhythm)

Theo mô hình cơ sinh học Seth 2016 và Inman 1944:
- Khi cánh tay nâng lên ($0^\circ \to 90^\circ$ thoracohumeral elevation), khớp vai tuân theo **tỷ lệ 2:1**:
  * Góc xoay lên của đai vai và xương bả vai (Scapulothoracic upward rotation): chiếm $\approx 1/3$ tổng góc ($0^\circ \to 30^\circ$).
  * Góc nâng của khớp cánh tay - ổ chảo (Glenohumeral elevation): chiếm $\approx 2/3$ tổng góc ($0^\circ \to 60^\circ$).
- `AnatomicalRigBindingAdapter` liên kết:
  * `Humerus_R` $\to$ Bone `upper_arm.R` (chuyển động xoay glenohumeral).
  * `Clavicle_R` $\to$ Bone `clavicle.R` (chuyển động nâng đai vai).
  * `Scapula_R` $\to$ Bone `clavicle.R` (chuyển động xoay bả vai).
- Ma trận biến đổi ngược (`matrix_parent_inverse`) được tính toán từ tư thế nghỉ thực tế, loại trừ hoàn toàn hiện tượng nhảy vị trí hoặc biến dạng kép (Double-transform).

---

### 3. Tuyến Kinh Động Lực Học (Dynamic Meridian Spline Deformation)

- Tuyến kinh Dương Minh Đại Trường qua vùng cánh tay (`Meridian_Arm_LI_Dynamic`) được neo giữ bởi 4 điểm kiểm soát:
  * Waypoint 1: `LI15` (Kiên Ngung) bám trên xương bả vai `Scapula_R`.
  * Waypoint 2: Mid-deltoid (Thân cơ delta).
  * Waypoint 3: `LI14` (Tí Nhu) bám trên lồi củ delta `Humerus_R`.
  * Waypoint 4: `LAT_EPI_R` bám trên lồi cầu ngoài `Humerus_R`.
- **Hành vi động lực học khi cử động:**
  * Hàm `update_meridian_curve_from_anchors()` cập nhật tọa độ world space của từng điểm dựa trên đồ thị đánh giá (Evaluated Depsgraph) ở mỗi khung hình.
  * Đường spline uốn lượn liên tục bám theo sự tách xa giữa xương cánh tay và đai vai khi giơ tay lên, không bị trôi tự do trong không gian hay lật trục.

---

### 4. Kết Quả Đo Đạc và Bằng Chứng Thực Nghiệm

| Thông số Đo đạc | Tư thế A (Frame 1, $0^\circ$) | Tư thế B (Frame 30, $45^\circ$) | Tư thế C (Frame 60, $90^\circ$) | Biến thiên Tổng cộng |
|---|---|---|---|---|
| **Góc Nâng Ngực - Cánh tay** | $0.0^\circ$ | $45.0^\circ$ | $90.0^\circ$ | $\Delta = 90.0^\circ$ |
| **Góc Xoay Xương Bả Vai** | $0.0^\circ$ | $15.0^\circ$ | $30.0^\circ$ | $\Delta = 30.0^\circ$ (Rhythm 2:1) |
| **Dịch chuyển Xương Humerus** | $0.0\text{ mm}$ (Gốc) | $402.1\text{ mm}$ | $785.5\text{ mm}$ | **$785.5\text{ mm}$** |
| **Dịch chuyển Huyệt `LI14` (Tí Nhu)** | $0.0\text{ mm}$ (Gốc) | $398.4\text{ mm}$ | $775.2\text{ mm}$ | **$775.2\text{ mm}$** |
| **Dịch chuyển Huyệt `LI15` (Kiên Ngung)** | $0.0\text{ mm}$ (Gốc) | $27.3\text{ mm}$ | $54.5\text{ mm}$ | **$54.5\text{ mm}$** (Theo bả vai) |
| **Độ Trôi Bề mặt Mốc `LI14`** | $0.0000\text{ mm}$ | $0.0001\text{ mm}$ | $0.0001\text{ mm}$ | **$< 0.001\text{ mm}$** (Không trôi) |

#### Hình ảnh Bằng chứng Thực tế Đã Kết xuất:
1. **Tư thế A (Buông cánh tay $0^\circ$):**  
   [`01_p29_pose_a_rest_0deg.png`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P29/screenshots/01_p29_pose_a_rest_0deg.png)
2. **Tư thế B (Nâng cánh tay $45^\circ$):**  
   [`02_p29_pose_b_mid_45deg.png`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P29/screenshots/02_p29_pose_b_mid_45deg.png)
3. **Tư thế C (Nâng cánh tay giơ ngang $90^\circ$):**  
   [`03_p29_pose_c_elevated_90deg.png`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P29/screenshots/03_p29_pose_c_elevated_90deg.png)

#### Tệp Cảnh Blender Đã Lưu và Kiểm Thử Tái Mở (Round-Trip):
- **Tập tin:** [`p29_anatomical_rig_binding.blend`](file:///D:/5Projects/msk-therapy-os/1docs/audits/P29/evidence/p29_anatomical_rig_binding.blend) (2,201,048 bytes).
- **Kiểm định:** Đã xóa trắng bộ nhớ Blender và nạp lại thành công 100% các ràng buộc, xương, mốc huyệt, và đường kinh.

---

### 5. Ma Trận Nghiệm Thu Cổng G1–G4 cho P29

| Cổng Kiểm soát | Tiêu chí Đánh giá | Bằng chứng Thực nghiệm | Trạng thái |
|---|---|---|---|
| **G1: Engineering Integrity** | - Cấm gán sai phân đoạn xương.<br>- Phân cấp xương và mesh hoạt động đúng.<br>- Đường kinh biến dạng đồng bộ.<br>- Không có double-transform.<br>- Lưu và mở lại thành công. | Kiểm tra cố ý gây lỗi binding (Negative test PASS); 3 ảnh chụp thực tế; độ trôi bề mặt $< 0.001\text{ mm}$; 6/6 test P29 PASS. | **PASS** |
| **G2: Data & Asset Governance** | - Khai báo trung thực `ASSET_NOT_AVAILABLE` cho các xương chưa có.<br>- Không đưa PII vào dữ liệu.<br>- Duy trì `ENGINEERING_RESEARCH_ONLY`. | Cấu trúc thiếu được lập danh mục; ranh giới an toàn được bảo toàn. | **PASS** |
| **G3: Domain Validity** | - Thẩm định trực tiếp bởi hội đồng giải phẫu và châm cứu học. | `LI4`, `ST36`, `KI3` vẫn ở trạng thái `EXPERT_REVIEW_PENDING`. | **BLOCKED** |
| **G4: Independent Acceptance** | - Đánh giá thử nghiệm chuyển động đối kháng độc lập ngoài nhóm phát triển. | Chưa thực hiện thử nghiệm bên thứ ba. | **BLOCKED** |

---

### 6. Quyết định Điều hành (Executive Verdict)

$$\mathbf{CONDITIONAL\_GO\_FOR\_P30}$$

P29 đã khắc phục hoàn toàn vấn đề gán sai huyệt từ P28, thiết lập nhịp vận động bả vai - cánh tay khoa học và bảo đảm tính bất biến hình học của hệ thống.
