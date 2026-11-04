# P34_00: BASELINE AND REPRODUCIBILITY AUDIT REPORT
**MSK-Therapy-OS | Milestone P34: Independent Source & Reality Reconciliation**

---

## 1. MÔI TRƯỜNG THỰC THI VÀ TÌNH TRẠNG GIT

- **Git HEAD Commit:** `4990f173a880e8a671c0622a04dd88c67264679c`
- **Working Tree:** Sạch đối với mã nguồn nghiệp vụ chính; các file chưa commit là dữ liệu audit và scratch scripts từ các phiên trước.
- **Hệ điều hành:** Windows 11 Enterprise (Build 26100)
- **Bộ vi xử lý (CPU):** Intel Core i7-5600U @ 2.60 GHz (2 Cores, 4 Threads)
- **Đồ họa tích hợp (GPU):** Intel HD Graphics 5500
- **Bộ nhớ RAM:** 8.00 GB DDR3
- **Môi trường Python chính:** `C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe` (Python 3.11.9)
- **Môi trường Python Sidecar:** `D:\5Projects\msk-therapy-os\tools\pose_sidecar\.venv_pose\Scripts\python.exe` (MediaPipe 1.2.0, OpenCV 5.0.0)
- **Môi trường Blender LTS:** `C:\Program Files\Blender Foundation\Blender 3.6\blender.exe` (Blender 3.6.5 LTS)

---

## 2. KẾT QUẢ TÁI LẬP HỒI QUY TOÀN DIỆN (REGRESSION RESULTS)

Thực hiện chạy toàn bộ 98 bài kiểm thử kế thừa từ P19 đến P33:

### A. Bộ 97 Bài Kiểm Thử Pytest Tích Hợp (Core Engine, Blender Studio, Rigging & Governance):
```powershell
& "C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe" -m pytest `
  tests/test_p19_lineage_and_governance.py `
  tests/test_p20_knowledge_vault.py `
  tests/test_p21_atlas_poc.py `
  tests/test_p22_coordinate_registry_and_lineage.py `
  tests/test_p25_knowledge_integration.py `
  tools/blender_anatomy_studio/tests/ `
  tests/test_p31_cross_system_integration.py `
  tests/test_p32_system_acceptance.py `
  tests/test_p33_reality_acceptance.py -q
```
**Kết quả thực tế quan sát (Observed Result):**
```
........................................................................ [ 74%]
.........................                                                [100%]
97 passed, 1 warning in 5.84s
```

### B. Bài Kiểm Thử Trình Duyệt Thực Tế Playwright Chromium E2E:
```powershell
& "C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe" -m pytest tests/test_p33_browser_e2e.py -q
```
**Kết quả thực tế quan sát (Observed Result):**
```
.                                                                        [100%]
1 passed in 57.55s
```

**Tổng kết:** 98/98 tests đạt **PASS 100%**.

---

## 3. DANH MỤC CHECKSUM VÀ TOÀN VẸN TÀI SẢN (ASSET INTEGRITY)

| Tài Sản | Đường Dẫn Thực Tế | Kích Thước (Bytes) | SHA-256 | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- |
| **Video Gốc** | `research/motion_samples/real_human_motion_cam01.mp4` | 3,126,520 | `cf4f2816c86bea4bfbea255333d8626ff32a3ecabdab8b0fb147cea9167fde3a` | Khớp 100% |
| **MediaPipe Model** | `tools/pose_sidecar/models/pose_landmarker_heavy.task` | 29,800,582 | `4eaa5eb7a98365221087693fcc286334cf0858e2eb6e15b506aa4a7ecdcec4ad` | Khớp 100% |
| **Blender Release P33** | `1docs/audits/P33/evidence/p33_hardened_release.blend` | 2,203,360 | `0e9cb30d1d2b79a5db701df9d6fe5579919f8602b92e212fae2f41c4f514bf21` | Khớp 100% |
| **Knowledge Vault DB** | `knowledge_vault/vault.db` | 53,248 | `7ff1ebaeec5e7f1dc2e20ffda1a5c6d3aecefa8b88bf5bb97d620577fc765ae1` | Khớp 100% |
| **MSK Core DB** | `msk_therapy_os.sqlite3` | 204,800 | `f382aeb3b601f054593452292f759654ceea5bb352eb919424bc282f9d5c8052` | Khớp 100% |

---

## 4. KẾT LUẬN PREFLIGHT P34

Hệ thống có nền tảng kiểm thử và quản trị dữ liệu ổn định, môi trường chạy đầy đủ và tái lập được 100%. Đủ điều kiện kỹ thuật để tiến hành kiểm toán sâu và giải mã các mâu thuẫn số liệu.
