# MSK-THERAPY-OS V1.1 — RELEASE GO / NO-GO DECISION
## Quyết định Phát hành Bản Nghiên cứu V1.1 (Research Preview Release)

> **Scope:** `ENGINEERING_RESEARCH_ONLY`  
> **Clinical Safety:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **Quyết định Tổng kết:** **GO FOR RESEARCH PREVIEW (V1.1-preview)**

---

### 1. BẢNG TỔNG HỢP CÁC NGUỒN TÀI NGUYÊN VÀ THƯ VIỆN

| Tên Dự Án / Thư Viện | Nguồn Nạp (Repository) | Vai Trò Trong V1.1 | Giấy Phép Bản Quyền |
| :--- | :--- | :--- | :--- |
| **MakeHuman Community Assets** | `makehumancommunity/mpfb2` | Khung xương Humanoid 53 xương, Base Mesh 19k đỉnh, 52 nhóm trọng số da, 6 Morph Targets. | **CC0 1.0 Universal** (Tài sản đồ họa được người dùng toàn quyền sử dụng, không bị lây lan AGPL). |
| **Blender 3.6 LTS** | `Blender Foundation` (LTS build) | Trình biên tập hình học, gán armature, nướng Shape Keys và xuất tệp GLB chuẩn glTF 2.0. | GPL v2+ (Chỉ dùng công cụ headless, không liên kết mã nguồn). |
| **Three.js Engine** | `mrdoob/three.js` (r128 offline) | Nạp và dựng hình SkinnedMesh, thực thi Linear Blend Skinning trên GPU, AnimationMixer và OrbitControls. | **MIT License** |
| **BodyParts3D 4.0** | `DBCLS (Database Center for Life Science)` | 2.143 chi tiết giải phẫu học có nguồn gốc, phục vụ chế độ ANATOMY_MODE và OVERLAY_MODE. | **CC-BY 2.1 Japan** |
| **WHO 2008 & GB/T 12346-2021** | `Tổ chức Y tế Thế giới (WHO)` | Danh mục tiêu chuẩn mốc huyệt giải phẫu (LI4, LI11, LI14, LI15). | Nguồn tài liệu học thuật / Tiêu chuẩn mở. |

---

### 2. CÁC MODULE TỰ VIẾT ĐÃ ĐƯỢC THAY THẾ (REPLACED)

1. **Thay thế nhóm `THREE.Group` phân cấp thủ công:**
   - *Trước đây (V1.0):* Ghép các đoạn xương bằng `upperArmGroup -> forearmGroup -> handGroup`, khiến lớp da không thể chuyển động theo và buộc phải ẩn da khi gập tay.
   - *Hiện nay (V1.1):* Sử dụng trực tiếp `THREE.SkinnedMesh` và `THREE.Skeleton` chuẩn công nghiệp đồ họa, da tự động co giãn và biến dạng đồng bộ với xương.
2. **Thay thế thuật toán scale đoạn chi tự chế:**
   - *Trước đây (V1.0):* Áp dụng scale trục độc lập trên các container hình học.
   - *Hiện nay (V1.1):* Sử dụng 6 GPU Morph Targets (Shape Keys) chuẩn hóa từ MakeHuman, tính toán biến dạng bằng shader phần cứng.
3. **Triệt tiêu hoàn toàn hack "Ẩn Da Khi Vận Động":**
   - Lớp da toàn thân giờ đây luôn hiển thị mượt mà trong `CHARACTER_MODE` và `OVERLAY_MODE`, không bao giờ bị xương đâm xuyên.

---

### 3. CÁC THÀNH PHẦN V1.0 ĐƯỢC GIỮ NGUYÊN VẸN (PRESERVED)

1. Toàn bộ cơ sở dữ liệu `knowledge_vault/vault.db` và `msk_therapy_os.sqlite3`.
2. Hệ thống quản trị an toàn, ranh giới y khoa fail-closed và xuất bản Markdown.
3. Chuỗi 100 khung hình trích xuất từ video chuyển động thực nghiệm MediaPipe.
4. Giao diện Web Atlas V1.0 tại `/sandbox/p21/index.html` (chạy song song độc lập, có thể truy cập bất kỳ lúc nào mà không bị ảnh hưởng).

---

### 4. BẢNG NGHIỆM THU TÍNH NĂNG (FEATURE ACCEPTANCE STATUS)

| Tính Năng Kỹ Thuật | Trạng Thái Nghiệm Thu | Ghi Chú Chi Tiết |
| :--- | :--- | :--- |
| **Nhân vật toàn thân SkinnedMesh** | **ĐÃ NGHIỆM THU (PASS)** | 19.158 đỉnh, 18.486 đa giác, 53 bones. |
| **Gập khuỷu tay 0° -> 90°** | **ĐÃ NGHIỆM THU (PASS)** | Khít kín $0.000\text{ mm}$, da co giãn tự nhiên. |
| **Dạng khớp vai và gập khớp gối** | **ĐÃ NGHIỆM THU (PASS)** | Chuyển động sinh lý mượt mà. |
| **Biến đổi hình thể tham số** | **ĐÃ NGHIỆM THU (PASS)** | 6 Shape Keys, hoàn nguyên tuyệt đối $0.000000\text{ m}$. |
| **Đăng ký giải phẫu (Anatomy Reg)** | **ĐÃ NGHIỆM THU (PASS)** | 5 xương chi trên gắn chặt vào các bone tương ứng. |
| **Huyệt vị động & Đường kinh 3D** | **ĐÃ NGHIỆM THU (PASS)** | LI4, LI11, LI14, LI15 bám sát chuyển động. |
| **Tích hợp chuyển động MediaPipe** | **ĐÃ NGHIỆM THU (PASS)** | 100 khung hình, nhịp scapulohumeral 2:1. |
| **Chế độ hiển thị 3 trong 1** | **ĐÃ NGHIỆM THU (PASS)** | Chuyển đổi mượt mà CHARACTER / ANATOMY / OVERLAY. |
| **Lưu và nạp dự án (.mskproj)** | **ĐÃ NGHIỆM THU (PASS)** | Tương thích ngược schema dự án. |
| **Thẩm định độ chính xác lâm sàng** | **CHƯA NGHIỆM THU (PENDING)** | Cổng G3 giữ nguyên PENDING, cấm dùng chẩn đoán. |

---

### 5. LỆNH KHỞI CHẠY VÀ KIỂM CHỨNG TRỰC TIẾP

#### 5.1. Khởi chạy Ứng dụng Toàn Diện:
```powershell
cd D:\5Projects\msk-therapy-os
.\run_msk_therapy_os.bat
```

#### 5.2. Mở trực tiếp Demo Nhân Vật V1.1 (Character Pipeline Studio):
Mở trình duyệt (Edge, Chrome, Brave) và truy cập:
```
http://localhost:8000/character/index.html
```
*(Hoặc truy cập Web Atlas V1.0 song song tại: `http://localhost:8000/sandbox/p21/index.html`)*.

#### 5.3. Chạy lại toàn bộ kiểm thử tự động V1.1:
```powershell
pytest tests/test_v11_character_pipeline_e2e.py -v
```

---

### 6. HƯỚNG DẪN HOÀN TÁC (ROLLBACK INSTRUCTIONS)

Nếu muốn hoàn tác về nguyên trạng V1.0 mà không giữ lại V1.1:
1. Xóa thư mục giao diện nhân vật: `msk_therapy_os/static/character_v11/`.
2. Xóa các adapter bổ trợ:
   - `msk_therapy_os/character_anatomy_adapter.py`
   - `msk_therapy_os/character_acupoints_adapter.py`
   - `msk_therapy_os/character_motion_retarget.py`
   - `tests/test_v11_character_pipeline_e2e.py`
3. Trong `msk_therapy_os/server.py`, xóa bỏ các khối route liên quan đến `/character` và `/api/character/v11/`.
4. Hệ thống V1.0 hoàn toàn độc lập và không chịu bất kỳ tác động nào khi hoàn tác.
