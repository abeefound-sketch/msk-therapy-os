# MSK-THERAPY-OS V1.2 — BÁO CÁO GIAI ĐOẠN PHASE A
## BASELINE INVENTORY & GAP ANALYSIS

> [!IMPORTANT]
> **Phạm vi thẩm định:** `RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY`  
> **Xác nhận lâm sàng:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **Cổng G3:** `PENDING` (Không tự động gán nhãn phê duyệt lâm sàng)  
> **Mục tiêu V1.2:** Triển khai hệ thống **Anatomical Binding System (ABS)** tái sử dụng để liên kết cấu trúc giải phẫu BodyParts3D/Z-Anatomy với canonical humanoid skeleton (MakeHuman 53-bone rig V1.1).  
> **Deliverable cốt lõi:** Một cánh tay giải phẫu 3D hoàn chỉnh gồm **xương (Humerus, Radius, Ulna, Metacarpal), cơ nhị đầu (Biceps brachii - 2 đầu), cơ tam đầu (Triceps brachii - 3 đầu), da và marker huyệt** di chuyển đồng bộ khi gập khuỷu $0^\circ \to 90^\circ$.

---

## 1. KIỂM TRA TRẠNG THÁI GIT & WORKING TREE

| Chỉ số | Giá trị thực tế | Ghi chú kỹ thuật |
| :--- | :--- | :--- |
| **Git Commit HEAD** | `4990f17` | `fix/p18-meridian-anatomical-geometry` |
| **Working Tree Policy** | Không commit, không stash, không push/merge | Tuân thủ tuyệt đối quy định sandbox |
| **Bảo lưu baseline V1.0** | Hoàn toàn nguyên vẹn | `/sandbox/p21/` & `run_v1_product.ps1` |
| **Bảo lưu baseline V1.1** | Hoàn toàn nguyên vẹn | Rollback target an toàn tại `msk_therapy_os/static/character_v11/` |

---

## 2. KIỂM TOÁN TỆP GLB MAKEHUMAN HIỆN TẠI (`rigged_human_v11.glb`)

| Thuộc tính glTF 2.0 | Kết quả kiểm toán thực tế | Đánh giá |
| :--- | :--- | :--- |
| **Kích thước file** | 16.490.992 bytes (~16.49 MB) | Đạt ngưỡng tải WebGL (< 20 MB) |
| **Số lượng Node** | 55 nodes (1 root, 1 mesh, 53 joints) | Khớp hoàn toàn cấu trúc MakeHuman game rig |
| **Số lượng SkinnedMesh** | 1 mesh (`base` / `HumanBody`) | Chỉ bao gồm lớp vỏ da nhân vật |
| **Số đỉnh (Vertices)** | 19.158 vertices | Tương thích GPU và WebGL 2.0 |
| **Số Shape Keys (Morphs)** | 6 morph targets (`Height`, `Proportions`, `ShoulderWidth`, `WaistCircumference`, `ArmLength`, `LegLength`) | Hoạt động trên WebGL GPU shader |
| **Số lượng Skeleton Bones** | 53 bones chuẩn humanoid | Cây phân cấp xương từ `root` qua `spine` đến các chi |
| **Vertex Groups (Skin Weights)** | 52 vertex groups có trọng số gán | Linear Blend Skinning mượt mà |
| **Animation Tracks** | 1 track (`A_HumanoidMotion`, 180 frames, 159 channels) | Bao gồm gập khuỷu, dạng vai, gập gối, xoay thân |

---

## 3. KHẢO SÁT TÀI SẢN GIẢI PHẪU THỰC TẾ (BODYPARTS3D 4.0)

Đã thẩm định và nạp các mesh giải phẫu nguồn từ BodyParts3D (Bản quyền **CC BY 4.0 DBCLS Japan**):

### 3.1. Cấu trúc xương chi trên (Skeletal Assets)
| ID | Tên giải phẫu | Tên file OBJ | Số đỉnh | Nguồn gốc Chunk | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `FJ3362` | Clavicle (Xương đòn phải) | `Clavicle_R.obj` | 310 | `body-13.bin` | Sẵn sàng |
| `FJ3384` | Scapula (Xương bả vai phải) | `Scapula_R.obj` | 2.348 | `body-13.bin` | Sẵn sàng |
| `FJ3368` | Humerus (Xương cánh tay phải) | `Humerus_R.obj` | 794 | `body-13.bin` | Sẵn sàng |
| `FJ3349` | Radius (Xương quay phải) | `Radius_R.obj` | 249 | `body-13.bin` | Sẵn sàng |
| `FJ3391` | Ulna (Xương trụ phải) | `Ulna_R.obj` | 305 | `body-13.bin` | Sẵn sàng |
| `FJ3352` | Metacarpal 2 (Xương đốt bàn 2 phải) | `Metacarpal_2_R.obj` | 246 | `body-13.bin` | Sẵn sàng |

### 3.2. Cấu trúc cơ bắp cánh tay (Muscular Assets trích xuất mới cho V1.2)
| ID | Tên cơ giải phẫu | Tên file OBJ | Số đỉnh | Nguồn gốc Chunk | Tác dụng cơ học |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `FJ1478` | Biceps brachii - Long head (Đầu dài cơ nhị đầu) | `Biceps_brachii_long_R.obj` | 466 | `body-3.bin` | Gập khuỷu, ngửa cẳng tay, ổn định khớp vai |
| `FJ1512` | Biceps brachii - Short head (Đầu ngắn cơ nhị đầu) | `Biceps_brachii_short_R.obj` | 1.035 | `body-4.bin` | Gập khuỷu, khép cánh tay |
| `FJ1477` | Triceps brachii - Lateral head (Đầu ngoài cơ tam đầu) | `Triceps_brachii_lateral_R.obj` | 656 | `body-3.bin` | Duỗi cẳng tay tại khớp khuỷu |
| `FJ1479` | Triceps brachii - Long head (Đầu dài cơ tam đầu) | `Triceps_brachii_long_R.obj` | 504 | `body-3.bin` | Duỗi cẳng tay, khép và duỗi cánh tay |
| `FJ1480` | Triceps brachii - Medial head (Đầu trong cơ tam đầu) | `Triceps_brachii_medial_R.obj` | 325 | `body-3.bin` | Duỗi cẳng tay (chủ vận mọi góc) |
| `FJ1486` | Brachialis (Cơ cánh tay) | `Brachialis_R.obj` | 630 | `body-3.bin` | Gập khuỷu nguyên phát |
| `FJ1488` | Coracobrachialis (Cơ quạ cánh tay) | `Coracobrachialis_R.obj` | 329 | `body-3.bin` | Gập và khép cánh tay |

---

## 4. PHÂN TÍCH KHOẢNG TRỐNG KỸ THUẬT (GAP ANALYSIS) GIỮA V1.1 VÀ V1.2

| Hạng mục kiểm toán | Hiện trạng V1.1 | Yêu cầu bắt buộc V1.2 | Khoảng trống kỹ thuật & Giải pháp V1.2 |
| :--- | :--- | :--- | :--- |
| **Xương cánh tay (Humerus, Radius, Ulna)** | Gắn qua Three.js `bonesMap[bone].add(mesh)` dưới dạng hình khối tượng trưng (cylinder/box) | Mesh giải phẫu thật BodyParts3D gắn cứng qua ma trận `RigidBoneBinding` có kiểm soát sai số | Sử dụng `RigidBoneBinding` tích hợp ma trận liên kết $M_{\text{bind}}$ và $M_{\text{inv}}$, kiểm định khoảng cách trôi (drift < 1 mm). |
| **Cơ nhị đầu (Biceps brachii)** | **HOÀN TOÀN CHƯA CÓ** | Có mesh thật, biến dạng (deformation) co ngắn và phồng bụng cơ khi gập khuỷu $0^\circ \to 90^\circ$ | Nạp mesh `FJ1478` & `FJ1512`, gán dual-bone blend weights (hoặc morph target bulge) đồng bộ với chuyển động `lowerarm_r`. |
| **Cơ tam đầu (Triceps brachii)** | **HOÀN TOÀN CHƯA CÓ** | Có mesh thật, giãn dài tự nhiên trên mặt sau khuỷu tay khi gập khuỷu | Nạp mesh `FJ1477`, `FJ1479`, `FJ1480`, liên kết đầu bám tận (olecranon) với xương trụ và cẳng tay. |
| **Khung xương chuẩn (Skeleton Contract)** | Hardcode tên xương trong adapter và Three.js viewer | `CanonicalSkeletonAdapter` thống nhất định nghĩa stable bone IDs, bind pose, rotation axes, bone lengths | Chuẩn hóa `CanonicalSkeletonAdapter` dùng chung cho toàn bộ hệ thống Python và Three.js. |
| **Mốc huyệt (Surface Anchors)** | Đính vào bone theo offset cố định | `SurfaceAnchorBinding` đính mốc vào cả bề mặt da lẫn xương cữ | Đồng bộ tọa độ huyệt `LI4`, `LI11`, `LI14`, `LI15` khi cơ bắp và da biến dạng. |
| **Phạm vi thẩm định** | Thử nghiệm toàn thân nhân vật game | **Tập trung duy nhất vào cánh tay giải phẫu 3D** | Xây dựng Arm Anatomy Studio chuyên sâu cho khớp khuỷu $0^\circ \to 90^\circ$. |

---

## 5. TÍNH TOÁN SAI LỆCH HỆ TỌA ĐỘ (COORDINATE ALIGNMENT AUDIT)

1. **Hệ tọa độ BodyParts3D (CT/MRI Scanner Frame):**
   - Đơn vị: Mét ($m$).
   - $X$: Trục ngang (âm là bên Phải, dương là bên Trái).
   - $Y$: Trục dọc (Superior/Inferior, chiều cao $1.108\text{ m} \to 1.415\text{ m}$ cho cánh tay).
   - $Z$: Trục trước-sau (Anterior/Posterior, âm là Sau, dương là Trước).
   - Tư thế giải phẫu: Cánh tay buông thẳng dọc thân mình.

2. **Hệ tọa độ MakeHuman Canonical Armature (Blender/glTF Frame):**
   - Đơn vị: Mét ($m$).
   - $X$: Trục ngang (âm là bên Phải, dương là bên Trái).
   - $Y$: Trục trước-sau (Anterior/Posterior).
   - $Z$: Trục dọc (Superior/Inferior).
   - Tư thế nghỉ (Rest pose): Nhân vật ở tư thế A-pose (cánh tay dạng chéo góc khoảng $42.4^\circ \approx 0.74\text{ rad}$).

3. **Chuyển đổi đồng bộ (Harmonized Transformation):**
   - Cần một ma trận biến đổi affine $T_{\text{bp3d}\to\text{canonical}}$ để ánh xạ từ không gian BodyParts3D sang không gian Canonical Skeleton:
     $$P_{\text{canonical}} = R_{\text{align}} \cdot (P_{\text{bp3d}} - P_{\text{center}}) + P_{\text{bone}}$$
   - Đảm bảo triệt tiêu hoàn toàn lỗi double-transform và scale mismatch (tất cả chuẩn hóa theo đơn vị mét $1.0\text{ m}$).

---

## 6. KẾT LUẬN VÀ PHƯƠNG ÁN HÀNH ĐỘNG PHASE B & C

- **Kết luận:** Khoảng trống lớn nhất của V1.1 là sự thiếu vắng hoàn toàn của các cơ bắp giải phẫu thực tế (Biceps và Triceps). Việc chỉ di chuyển da và xương tượng trưng không đáp ứng được yêu cầu mô hình hóa cơ xương khớp lâm sàng.
- **Phương án thực thi:**
  1. **Phase B:** Xây dựng `msk_therapy_os/canonical_skeleton_adapter.py` chuẩn hóa hợp đồng khung xương MakeHuman.
  2. **Phase C:** Xây dựng `msk_therapy_os/anatomical_binding/` với 4 adapter cốt lõi:
     - `rigid_bone_binding.py`
     - `muscle_deformation_binding.py`
     - `surface_anchor_binding.py`
     - `kinematic_chain_coordinator.py`
  3. **Phase D:** Xuất bản asset cánh tay giải phẫu 3D thực tế và giao diện tương tác Three.js chuyên biệt.
  4. **Phase E:** Kiểm thử tự động E2E với Playwright và hoàn tất hồ sơ nghiệm thu.
- **Rollback safety:** Baseline V1.1 tại `msk_therapy_os/static/character_v11/` được giữ nguyên vẹn 100%.
