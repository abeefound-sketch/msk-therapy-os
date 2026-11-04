# MSK-Therapy-OS — Milestone P23 Audit
## P23_04: Blender Animation Playback Evidence & Timeline Scrubbing Guide

**Tài liệu ID:** `MSK-P23-AUD-004`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Bằng chứng Playback Chuyển động Cánh tay (Animation Evidence)

Chuỗi chuyển động gập/duỗi khuỷu và nâng vai đã được nạp thành công vào hệ thống Timeline của Blender 3.6:
- **Tập tin cảnh:** `1docs/audits/P21/evidence/p21_studio_export.blend` (2,202,700 bytes)
- **Khung hình Keyframe:**
  * **Frame 1:** Khớp vai $0^\circ$, Khớp khuỷu $0^\circ$ (Cánh tay buông tự nhiên).
  * **Frame 20:** Khớp vai $45^\circ$, Khớp khuỷu $45^\circ$.
  * **Frame 40:** Khớp vai $90^\circ$, Khớp khuỷu $90^\circ$ (Cánh tay giơ ngang gập vuông góc).
- **Hình ảnh kết xuất tại Frame 30 (tư thế trung gian đang gập):**  
  [02_blender_arm_rig_flexed_pose.png](file:///D:/5Projects/msk-therapy-os/1docs/audits/P21/screenshots/02_blender_arm_rig_flexed_pose.png)

---

### 2. Thao tác Tua Dòng Thời gian (Timeline Scrubbing)

Để kiểm chứng chuyển động:
1. Mở tệp `p21_studio_export.blend` trong Blender 3.6.
2. Trên cửa sổ `Timeline` phía dưới màn hình:
   - Kéo chuột (scrub) thanh trỏ thời gian qua lại giữa Frame 1 và Frame 40.
   - Quan sát cánh tay di chuyển mượt mà theo đường cong nội suy Bézier.
   - Nhận thấy mốc huyệt `LI4` bám chắc vào cấu trúc xương cánh tay, không bị xê dịch hay lật trục.
