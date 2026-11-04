# MSK-Therapy-OS — Milestone P21 Forensic Preflight
## P21_00: Baseline Survey, Environment Integrity & Forensic Preflight (Blender & Motion)

**Tài liệu ID:** `MSK-P21-AUD-000-BLENDER`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái Preflight:** `PREFLIGHT_PASS_VERIFIED`  

---

### 1. Khảo sát Phần cứng & Môi trường Thực thi Thực tế (Ground-Truth Observation)

Đo lường trực tiếp trên máy trạm thực tế (Target Machine Benchmark):

| Thông số | Giá trị thực tế đo lường | Ghi chú & Thẩm định |
|---|---|---|
| **Hệ điều hành** | Windows 11 64-bit | Shell: PowerShell |
| **CPU** | Intel(R) Core(TM) i7-5600U CPU @ 2.60GHz | 2 Cores, 4 Logical Processors (Broadwell) |
| **GPU** | Intel(R) HD Graphics 5500 | Driver: WDDM 2.0; Hỗ trợ OpenGL 4.4 / DirectX 12 |
| **RAM** | 7.89 GB Physical Memory | Trùng khớp cấu hình chuẩn `Intel HD 5500 / 8GB RAM` được chỉ định trong Master Prompt |
| **Python Runtime** | Python 3.11.9 (64-bit) | `C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe` |
| **Blender Runtime** | **Blender 3.6.5 LTS** (Release) | Build hash: `cf1e1ed46b7e`, Build date: 2023-10-19; Đường dẫn: `C:\Program Files\Blender Foundation\Blender 3.6\blender.exe` |
| **Blender Python** | Python 3.10.13 embedded | Khởi chạy native `bpy` thành công không lỗi |

---

### 2. Khảo sát Trạng thái Repository & Giữ nguyên Ranh giới An toàn

- **Active Branch:** `fix/p18-meridian-anatomical-geometry`
- **HEAD Commit:** `4990f173a880e8a671c0622a04dd88c67264679c`
- **Bảo toàn dữ liệu P18–P20:**
  * Giữ nguyên toàn bộ 19 bài test của P19 & P20 (`tests/test_p19_lineage_and_governance.py`, `tests/test_p20_knowledge_vault.py`).
  * Giữ nguyên Web sandbox P21 cũ (`msk_therapy_os/static/sandbox_p21/`, `tests/test_p21_atlas_poc.py`).
  * Tuyệt đối không `git reset --hard`, không `git clean -fd`, không push hoặc merge vào branch chính.
  * Tách biệt công cụ authoring offline: `tools/blender_anatomy_studio/`.

---

### 3. Kết quả Rerun Test Suite Kế thừa

Chạy kiểm tra hồi quy toàn diện trước khi phát triển:
- `tests/test_p19_lineage_and_governance.py`: 8/8 PASSED.
- `tests/test_p20_knowledge_vault.py`: 11/11 PASSED.
- `tests/test_p21_atlas_poc.py`: 15/15 PASSED.
- **Tổng cộng kế thừa:** 34/34 test PASSED (100%).

---

### 4. Kết luận Preflight

Môi trường thực tế đáp ứng 100% điều kiện tiên quyết. Sẵn sàng khởi động quy trình tích hợp Blender Anatomical Studio PoC và Motion Validation.
