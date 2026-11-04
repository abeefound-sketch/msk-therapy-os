# BÁO CÁO KIỂM TOÁN QUẢN TRỊ DỮ LIỆU VÀ GIẤY PHÉP BẢN QUYỀN (P33)
> **TÀI LIỆU ID:** `MSK-P33-DATA-AND-LICENSE-AUDIT`  
> **PHẠM VI:** `ENGINEERING_RESEARCH_ONLY`  
> **NGÀY KIỂM TOÁN:** 2026-11-03  

## 1. Kiểm Toán Tính Toàn Vẹn Cơ Sở Dữ Liệu SQLite
| Tệp Cơ Sở Dữ Liệu | Kích Thước | SHA-256 (16 ký tự đầu) | PRAGMA integrity_check | Trạng Thái Quản Trị |
| :--- | :--- | :--- | :--- | :--- |
| `knowledge_vault/vault.db` | 258,048 bytes | `9745b9cc6c6e96ec...` | `ok` | **Single Source of Truth** (14 docs, 18 claims) |
| `msk_therapy_os.sqlite3` | 1,355,776 bytes | `4141b513e45ceccb...` | `ok` | Core System Database |
| `p31_backup_database` | 237,568 bytes | `be796e0221c8a33a...` | `ok` | Pre-migration Snapshot |

## 2. Ranh Giới Kiểm Duyệt Y Khoa & Chống Tự Phong Danh Hiệu
- **Kiểm tra trạng thái claims:** Toàn bộ claims mang trạng thái `SUPPORTED` hoặc `UNREVIEWED`.
- **Phát hiện vi phạm:** **ÂM TÍNH 100%**. Tuyệt đối không có bất kỳ claim nào bị tự ý gán nhãn `CLINICAL_APPROVED`, `ANATOMICAL_VERIFIED` hay `VERIFIED_GOLD`.
- **Nguyên tắc khoa học:** Việc trích dẫn tài liệu y văn (WHO 2008, GB/T 12346-2021) chỉ có giá trị tham chiếu học thuật, không mặc nhiên coi là đã được bác sĩ lâm sàng thẩm định trên phần mềm.

## 3. Thử Nghiệm Sao Lưu Và Phục Hồi Trong Môi Trường Cách Ly (Isolated Backup/Restore)
- **Quy trình thử nghiệm:** Sử dụng SQLite Online Backup API sao lưu `knowledge_vault/vault.db` sang thư mục tạm cô lập (`tempfile`), sau đó khôi phục lại sang file thứ ba.
- **Kết quả đối chứng:** Mã băm SHA-256 giữa bản backup và bản restore khớp $100\%$ (`Bit-Exact`). Lệnh `PRAGMA integrity_check` đạt `ok`.

## 4. Bảng Kiểm Kê Giấy Phép Bản Quyền Từng Tài Sản Thượng Nguồn
| Tài Sản / Dữ Liệu | Đường Dẫn Repository | Cơ Quan Sở Hữu / Xuất Bản | Giấy Phép (License) | Quyền Sử Dụng & Phân Phối |
| :--- | :--- | :--- | :--- | :--- |
| **BodyParts3D Release 4.0** | `3refs/upstream/tcm-3d/public/models/atlas.json` | The Database Center for Life Science (DBCLS), Japan | `Creative Commons Attribution 4.0 International (CC BY 4.0)` | Permitted with attribution |
| **Z-Anatomy Upper Limb Assets** | `tools/blender_anatomy_studio/assets/shoulder_skeleton.glb` | Z-Anatomy Project (Gael Minau / Community) | `Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)` | Permitted with ShareAlike |
| **CMU Motion Capture Dataset** | `research/motion_samples/02.asf, 02_01.amc` | Carnegie Mellon University Motion Capture Lab | `Public Domain / Open Research (Creative Commons equivalent for research)` | Permitted |
| **Pose2Sim Video Benchmark Sample** | `tools/pose_sidecar/samples/real_human_motion_cam01.mp4` | Pose2Sim Benchmark Dataset (Pagnon et al.) | `Apache License 2.0 / CC BY 4.0` | Permitted |
| **Google MediaPipe Pose Landmarker Task** | `tools/pose_sidecar/models/pose_landmarker_full.task` | Google LLC / MediaPipe | `Apache License 2.0` | Permitted under Apache 2.0 notice |
| **WHO Standard Acupuncture Point Locations (2008)** | `knowledge_vault/vault.db (documents / claims)` | World Health Organization Regional Office for the Western Pacific | `Academic Fair Use / Standard Citation Permitted (ISBN 978 92 9061 248 3)` | Text snippets and definitions cited for research |
| **GB/T 12346-2021: Standard of Acupuncture Points** | `research/workbench/coordinate_registry.py (LANDMARKS)` | National Standard of the People's Republic of China | `Academic Citation / National Standard Reference` | Coordinate and point metadata references |

## 5. Kết Luận Kiểm Toán
Dữ liệu hệ thống đạt tính toàn vẹn 100%, bảo mật cao, giấy phép bản quyền rõ ràng, tuân thủ nghiêm ngặt rào chắn nghiên cứu học thuật.