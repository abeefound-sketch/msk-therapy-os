# MSK-Therapy-OS — Milestone P29 Audit
## P29_00: Baseline Environment, Dependency Preflight & Forensic Inventory
### Reality-Gated Implementation · Asset Auditing · Marker-to-Anatomy Forensic Rectification

**Tài liệu ID:** `MSK-P29-AUD-000-PREFLIGHT`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Kiểm toán viên:** Principal Software Architect & Biomechanics Integrity Lead  
**Trạng thái Cổng:** G1: **PASS** | G2: **PASS** | G3: **BLOCKED** | G4: **BLOCKED**  
**Quyết định Điều hành:** $$\mathbf{CONDITIONAL\_GO\_FOR\_P29}$$

---

### 1. Hiện trạng Git HEAD và Môi trường Thực thi (Preflight Baseline)

| Thành phần | Thông số Đo đạc Thực tế | Tình trạng Kiểm toán |
|---|---|---|
| **Git Working Directory** | `D:\5Projects\msk-therapy-os` | Không gian làm việc chính thức |
| **Git Branch** | `fix/p18-meridian-anatomical-geometry` | Branch hiện hành |
| **Git HEAD Commit** | `4990f173a880e8a671c0622a04dd88c67264679c` | Đồng bộ 100% |
| **Working Tree State** | DIRTY (Chứa các deliverables P19–P28, không reset, không stash) | Bảo toàn toàn vẹn dữ liệu |
| **Blender Executable** | `C:\Program Files\Blender Foundation\Blender 3.6\blender.exe` | Blender 3.6.5 LTS (cf1e1ed46b7e) |
| **Python Sidecar Environment** | `D:\5Projects\msk-therapy-os\tools\pose_sidecar\.venv_pose` | Python 3.11 · MediaPipe 1.2.0 · OpenCV 5.0.0 |
| **MediaPipe Neural Task** | `tools/pose_sidecar/models/pose_landmarker_full.task` (9.4 MB) | SHA-256: `4eaa5eb7a98365221087693fcc286334cf0858e2eb6e15b506aa4a7ecdcec4ad` |
| **Mẫu Video Thực nghiệm** | `tools/pose_sidecar/samples/real_human_motion_cam01.mp4` (387 KB) | SHA-256: `cf4f2816c86bea4bfbea255333d8626ff32a3ecabdab8b0fb147cea9167fde3a` |
| **Tệp Cảnh P28 Baseline** | `1docs/audits/P28/evidence/p28_real_video_motion.blend` (2.05 MB) | Khởi tạo thành công từ P28 |
| **Tình trạng Kiểm thử Kế thừa** | 74 / 74 tests PASSED (100% pass rate) | Sạch sẽ, không có test lỗi |

---

### 2. Kiểm toán Tài Nguyên Giải Phẫu Hiện Hữu (Anatomical Asset Forensics)

Qua kiểm tra trực tiếp các tệp nhị phân GLB trên hệ thống:

#### 2.1. Tệp `shoulder_skeleton.glb` (386,856 bytes)
- **Cấu trúc thực tế chứa trong mesh:**
  1. `Clavicle_R` (Xương đòn phải): 420 đỉnh
  2. `Scapula_R` (Xương bả vai phải): 2,896 đỉnh
  3. `Humerus_R` (Xương cánh tay phải): 794 đỉnh
  4. `Thorax` (Khung lồng ngực đối chứng): 7,644 đỉnh
- **Cấu trúc KHÔNG tồn tại (`ASSET_NOT_AVAILABLE`):**
  - Xương quay (`Radius_R`): **KHÔNG CÓ**
  - Xương trụ (`Ulna_R`): **KHÔNG CÓ**
  - Xương cổ tay (`Carpals_R`): **KHÔNG CÓ**
  - Xương bàn tay (`Metacarpals_R`): **KHÔNG CÓ**
  - Xương ngón tay (`Phalanges_R`): **KHÔNG CÓ**
  - Toàn bộ xương chi dưới (`Femur`, `Tibia`, `Fibula`, `Tarsals`): **KHÔNG CÓ**

#### 2.2. Tệp `anatomy.glb` (9,291,204 bytes)
- Chứa 54 nhóm cơ (deltoids, biceps, triceps, brachioradialis, v.v.), không chứa các segment xương rời để rig armature trực tiếp.

---

### 3. Nhận diện Lỗi Cốt Lõi P28 và Kế Hoạch Sửa Chữa (Rectification Strategy)

> [!WARNING]
> **Vấn đề cốt lõi được chỉ định bởi Lead Auditor:**
> Trong P28, mốc huyệt `LI4` (Hợp Cốc) đã bị gán trực tiếp vào `Humerus_R` (`LI4.parent = Humerus_R`).  
> **Sai lệch nghiêm trọng:** Về mặt giải phẫu học, huyệt Hợp Cốc nằm ở mu bàn tay, giữa xương bàn ngón tay I và II (First Dorsal Interosseous space). Việc gán `LI4` vào xương cánh tay `Humerus_R` chỉ để nó "di chuyển theo rig" là hành vi sai lệch giải phẫu học, vi phạm nguyên tắc cơ bản của dự án.

#### Kế hoạch Khắc phục Toàn diện cho P29:
1. **Xác lập ranh giới mốc huyệt:**
   - Với các huyệt mà cấu trúc xương mang nó **không có mặt trong asset hiện tại** (như `LI4` trên xương bàn tay, `ST36` trên xương chày, `KI3` trên xương gót/mắt cá trong):
     * Gắn nhãn trạng thái chính xác: `ASSET_NOT_AVAILABLE`.
     * Giữ nguyên trạng thái thẩm định: `EXPERT_REVIEW_PENDING`.
     * **TUYỆT ĐỐI CẤM** gán `LI4` vào `Humerus_R`, `ST36` vào `Scapula_R`, hoặc `KI3` vào `Clavicle_R`.
2. **Khởi tạo các Mốc Giải phẫu Đúng Thực tế cho Cánh tay:**
   - Để kiểm chứng chuyển động của xương cánh tay và đai vai, sử dụng các mốc giải phẫu thực sự thuộc các xương hiện có:
     * `DELTOID_TUBEROSITY` (Lồi củ delta trên `Humerus_R`, FMA:23412).
     * `LATERAL_EPICONDYLE` (Mỏm trên lồi cầu ngoài trên `Humerus_R`, FMA:23420).
     * `ACROMION_ANGLE` (Góc mỏm cùng vai trên `Scapula_R`, FMA:23240).
     * Huyệt `LI14` (Tí Nhu - nằm ở bờ ngoài cánh tay, nơi bám cơ delta vào xương cánh tay `Humerus_R`, FMA:23412).
     * Huyệt `LI15` (Kiên Ngung - nằm ở chỗ lõm bờ trước dưới mỏm cùng vai trên `Scapula_R`/`Clavicle_R`, FMA:23240).
3. **Đường kinh động lực học (Dynamic Meridian Re-computation):**
   - Tuyến kinh Dương Minh Đại Trường qua vùng cánh tay sẽ nối từ mốc cẳng tay (tham chiếu) qua `LI14` (bám `Humerus_R`) lên `LI15` (bám đai vai).
   - Khi xương cánh tay cử động nâng lên theo video MediaPipe, waypoint `LI14` di chuyển cùng `Humerus_R`, waypoint `LI15` neo giữ tại đai vai, và đường spline nối giữa chúng được tái dựng động trong không gian 3D mà không bị trôi hay đứt gãy.
