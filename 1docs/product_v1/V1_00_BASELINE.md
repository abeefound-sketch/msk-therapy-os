# V1_00: BASELINE AND RUNTIME AUDIT REPORT
**MSK-Therapy-OS V1.0 | Product Completion Roadmap**

---

## 1. MÔI TRƯỜNG THỰC THI VÀ TÌNH TRẠNG GIT HEAD

- **Git HEAD Commit:** `4990f173a880e8a671c0622a04dd88c67264679c`
- **Hệ điều hành:** Windows 11 Enterprise (Build 26100)
- **Bộ vi xử lý (CPU):** Intel Core i7-5600U @ 2.60 GHz (2 Cores, 4 Threads)
- **Đồ họa tích hợp (GPU):** Intel HD Graphics 5500 (DirectX 12 / OpenGL 4.4 / WebGL 2.0)
- **Bộ nhớ RAM:** 8.00 GB DDR3 (Giới hạn tài nguyên hệ thống)
- **Môi trường Python chính:** `C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe` (Python 3.11.9)
- **Môi trường Python Sidecar:** `D:\5Projects\msk-therapy-os\tools\pose_sidecar\.venv_pose\Scripts\python.exe` (MediaPipe 1.2.0, OpenCV 5.0.0)
- **Môi trường Blender LTS:** `C:\Program Files\Blender Foundation\Blender 3.6\blender.exe` (Blender 3.6.5 LTS)

---

## 2. KẾT QUẢ KIỂM THỬ HỒI QUY BASELINE (114/114 TESTS PASS)

Toàn bộ 114 bài kiểm thử kế thừa từ P19 đến P37 đã được chạy lại và xác minh thực tế (OBSERVED):

```powershell
# Bộ 113 bài kiểm thử Pytest tích hợp:
& "C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe" -m pytest `
  tests/test_p19_lineage_and_governance.py `
  tests/test_p20_knowledge_vault.py `
  tests/test_p21_atlas_poc.py `
  tests/test_p22_coordinate_registry_and_lineage.py `
  tests/test_p25_knowledge_integration.py `
  tools/blender_anatomy_studio/tests/ `
  tests/test_p31_cross_system_integration.py `
  tests/test_p32_system_acceptance.py `
  tests/test_p33_reality_acceptance.py `
  tests/test_p35_anatomical_completeness.py `
  tests/test_p36_motion_validation.py -q
# Kết quả: 113 passed in 5.16s

# Bài kiểm thử Playwright Chromium E2E:
& "C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe" -m pytest tests/test_p33_browser_e2e.py -q
# Kết quả: 1 passed in 26.39s
```

**Tổng kết:** **114 / 114 tests PASS 100%**.

---

## 3. DANH MỤC TÀI SẢN VÀ CƠ SỞ DỮ LIỆU ĐÃ XÁC MINH

| Tài Sản | Đường Dẫn Thực Tế | Kích Thước (Bytes) | SHA-256 Checksum | Trạng Thái Kiểm Tra |
| :--- | :--- | :--- | :--- | :---: |
| **Atlas Catalog** | `3refs/upstream/tcm-3d/public/models/atlas.json` | 1,335,285 | `c359f4bcd2cba90b7411d66d5e9fc04dc81294d46cd5c1e8b212c824f2e5bbee` | OBSERVED (2,234 parts, 15 chunks) |
| **Binary Chunk 13** | `3refs/upstream/tcm-3d/public/models/body-13.bin` | 4,004,548 | `7ff0e27f9cb89c4240751ca0be649c00b0e50e82c89ae83fdb55c3c0f498c3b0` | OBSERVED (Chứa Humerus, Radius, Ulna, Metacarpal II) |
| **P35 Blender Scene**| `1docs/audits/P35/evidence/p35_full_limb_binding.blend` | 1,306,496 | `bcb8a931f1feac9e4f2dc9f68840b7da79e237b950a1021256dd807c6d95c2b2` | OBSERVED (Full Upper Limb + Metacarpal II) |
| **Video Chuyển Động**| `research/motion_samples/real_human_motion_cam01.mp4` | 3,126,520 | `cf4f2816c86bea4bfbea255333d8626ff32a3ecabdab8b0fb147cea9167fde3a` | OBSERVED (100 frames, 60 FPS) |
| **MediaPipe Model** | `tools/pose_sidecar/models/pose_landmarker_heavy.task` | 29,800,582 | `4eaa5eb7a98365221087693fcc286334cf0858e2eb6e15b506aa4a7ecdcec4ad` | OBSERVED (v1.2.0 Heavy) |
| **Knowledge Vault** | `knowledge_vault/vault.db` | 53,248 | `7ff1ebaeec5e7f1dc2e20ffda1a5c6d3aecefa8b88bf5bb97d620577fc765ae1` | OBSERVED (14 docs, 18 claims, FTS5) |
| **MSK Core DB** | `msk_therapy_os.sqlite3` | 204,800 | `f382aeb3b601f054593452292f759654ceea5bb352eb919424bc282f9d5c8052` | OBSERVED (Vận hành hệ thống) |

---

## 4. XÁC NHẬN BLOCKER SẢN PHẨM HIỆN HÀNH

- **Thực trạng Web Atlas (`sandbox_p21`):**  
  Kiểm tra trực tiếp hàm `updateMotionUI(idx)` trong `app.js`: Hiện tại khi kéo slider timeline hoặc bấm Play, hệ thống chỉ cập nhật text DOM (`val-shoulder-elevation`, `val-elbow-flexion`), trong khi các mesh 3D trong Three.js Canvas hoàn toàn đứng yên.  
  Trạng thái ghi nhận chính thức: `WEB_MOTION_GEOMETRY_NOT_CONNECTED`.
- **Mục tiêu ưu tiên số 1 của V1.0:**  
  Chuyển đổi trạng thái sang `WEB_MOTION_GEOMETRY_CONNECTED` bằng cách thiết lập liên kết xương động học 3D (3D Hierarchical Skeletal Rigging) trực tiếp trong Web Atlas Three.js.
