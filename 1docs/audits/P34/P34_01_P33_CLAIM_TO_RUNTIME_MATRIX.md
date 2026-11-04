# P34_01: P33 CLAIM TO RUNTIME REALITY AUDIT MATRIX
**MSK-Therapy-OS | Milestone P34: Independent Source & Reality Reconciliation**

---

## 1. MA TRẬN ĐỐI CHIẾU TUYÊN BỐ P33 VS THỰC TẾ QUAN SÁT (CLAIM VS RUNTIME REALITY)

| Hạng Mục Kiểm Toán | Tuyên Bố Tại Báo Cáo P33 | Thực Tế Kiểm Tra Mã Nguồn & Runtime | Kết Luận Kiểm Toán | Bằng Chứng Kỹ Thuật |
| :--- | :--- | :--- | :---: | :--- |
| **Góc Nâng Vai Frame 050 (MediaPipe)** | Nâng vai 98.02° tại Frame 050, độ tin cậy 1.000. | `p33_fresh_inference_run.json` và `p28_real_motion_sequence.json` ghi nhận: `shoulder_elevation_deg: 98.02`, `elbow_flexion_deg: 80.44`. | **CONFIRMED** | `1docs/audits/P33/evidence/p33_fresh_inference_run.json#L45-L60` |
| **Góc Nâng Vai Frame 050 (Blender Render)** | Render Frame 050 hiển thị cánh tay nâng ~45° hoặc 75°. | `p33_hardened_release.blend` chứa Action `Armature_UpperLimb_RAction` chỉ có 3 keyframes (F1=0°, F30=45°, F60=90°). Tại F50 nội suy ra 75° (50° cánh tay + 25° xương đòn). | **CONTRADICTED (Lệch Pipeline)** | `headless_p29_anatomical_binding.py` tạo scene 60 frames demo, P33 tái sử dụng nhầm file này thay vì chuỗi 100 frames thực của P28. |
| **Sự Nhất Quán Góc End-to-End** | Báo cáo P33 ngụ ý chuyển động từ video chạy xuyên suốt vào Blender release. | `p28_real_video_motion.blend` có đủ 100 frames (F50 đạt 98.53°), nhưng `p33_hardened_release.blend` chỉ chứa 3 keyframes của P29. | **END_TO_END_ANGLE_CONSISTENCY_NOT_PROVEN (Trong scene P33)** | Phải thống nhất retarget 100 frames MediaPipe vào rig 2:1 ở Milestone P35. |
| **Web Atlas Dynamic Motion** | Web Atlas có timeline slider, phát lại hoạt ảnh chuyển động. | `app.js` (`updateMotionUI`) chỉ cập nhật giá trị text DOM (`elValShoulder`, `elValElbow`). Three.js Canvas hiển thị mesh tĩnh của BodyParts3D, chưa kết nối biến dạng xương 3D. | **WEB_MOTION_GEOMETRY_NOT_CONNECTED** | `msk_therapy_os/static/sandbox_p21/app.js#L925-L934` |
| **Định Nghĩa Cổng Nghiệm Thu G4** | G4 yêu cầu chứng nhận thiết bị y tế FDA/CE-MDR và thử nghiệm RCT. | Sai lệch phạm vi quản trị. G4 là *Independent Engineering Acceptance* (kiểm toán kỹ thuật độc lập mã nguồn, thuật toán và kiểm thử). Chứng nhận y tế thuộc phạm vi pháp lý riêng. | **GOVERNANCE_REDEFINED** | G4 được hiệu chỉnh thành nghiệm thu kỹ thuật độc lập. |
| **Tài Sản Xương Cho Huyệt LI4, ST36, KI3** | Báo cáo `ASSET_NOT_AVAILABLE` cho toàn bộ chi dưới và bàn tay. | `3refs/upstream/tcm-3d/public/models/body-13.bin` (BodyParts3D, CC BY 4.0) có sẵn `FJ3352` (xương bàn tay 2 - LI4), `FJ3349` (xương quay), `FJ3391` (xương trụ), `FJ3387` (xương chày - ST36). | **ASSETS_DISCOVERED_IN_REPO** | Mô hình giải phẫu thật có sẵn trong repo, đủ điều kiện trích xuất và neo mốc. |

---

## 2. GIẢI MÃ TOÁN HỌC VÀ NGUYÊN NHÂN GỐC CỦA MÂU THUẪN FRAME 050

```
[Video 100 frames] 
       │
       ▼
[MediaPipe Inference tươi] ──> Frame 50: Vai = 98.02°, Khuỷu = 80.44°
       │
       ├─ (Đường đi 1: P28) ──> p28_real_video_motion.blend (100 frames)
       │                        └── Frame 50: upper_arm = 98.53°, forearm = 78.00° (KHỚP!)
       │
       └─ (Đường đi 2: P29/P33) ──> headless_p29_anatomical_binding.py (Test nhịp 2:1)
                                    └── Keyframe F1=0°, F30=45°, F60=90° (Chỉ 60 frames!)
                                    └── Frame 50 = Nội suy giữa F30 & F60 = 75.00°
                                    └── P33 dùng file này để render -> Báo cáo thấy F50 = 75°!
```

**Kết luận kiểm toán:**
Không có lỗi thuật toán trong việc tính góc của MediaPipe hay phép quay Euler của Blender. Mâu thuẫn phát sinh do sự **nhầm lẫn file tài sản**: P33 đã sử dụng file kiểm thử nhịp vận động tổng hợp (synthetic 3-keyframe rhythm test) của P29 làm file phát hành release, thay vì nạp chuỗi 100 keyframes thực tế từ P28 vào rig nhịp 2:1.

---

## 3. THỰC TRẠNG WEB ATLAS (WEB_MOTION_GEOMETRY_NOT_CONNECTED)

Kiểm tra trực tiếp mã nguồn `msk_therapy_os/static/sandbox_p21/app.js`:
```javascript
function updateMotionUI(idx) {
    currentMotionIndex = idx;
    elTimeline.value = idx;
    elFrameDisplay.innerText = `Frame: ${idx} / ${motionFrames.length - 1}`;
    if (motionFrames[idx]) {
        const rot = motionFrames[idx].joint_angles_deg || {};
        elValShoulder.innerText = `${rot.shoulder_elevation || 0.0}°`;
        elValElbow.innerText = `${rot.elbow_flexion || 0.0}°`;
    }
}
```
Hàm `updateMotionUI` hoàn toàn không thay đổi transform, ma trận quay hay xương của Three.js BufferGeometry. Các cấu trúc giải phẫu hiển thị trong canvas 3D là các mesh tĩnh nạp từ `body-*.bin`.
Do đó, theo chỉ dẫn Master Prompt, hệ thống Web Atlas được ghi nhận chính thức là:  
`WEB_MOTION_GEOMETRY_NOT_CONNECTED`.

---

## 4. HIỆU CHỈNH QUẢN TRỊ CỔNG G4 (INDEPENDENT ENGINEERING ACCEPTANCE)

Báo cáo P33 coi G4 là rào cản pháp lý y tế (FDA 510(k), CE-MDR), điều này không phù hợp với phân loại dự án phần mềm nghiên cứu kỹ thuật (`RELEASE_SCOPE=ENGINEERING_RESEARCH_ONLY`).
Hiệu chỉnh chuẩn hóa:
- **G1: Functional Verification:** Mã nguồn chạy thực tế, không dùng mock/synthetic pose.
- **G2: Data Integrity & Provenance:** Hợp đồng dữ liệu chuẩn, checksum bit-exact, có phả hệ rõ ràng.
- **G3: Domain Validity (PENDING):** Thẩm định y học/giải phẫu học từ chuyên gia độc lập.
- **G4: Independent Engineering Acceptance (PENDING):** Đánh giá kỹ thuật độc lập bởi kỹ sư/chuyên gia kiểm toán phần mềm bên ngoài (Audit Code, Math, Testcases & Reproducibility).
- **Clinical/Regulatory Gate (OUT OF SCOPE):** Cổng phê duyệt thiết bị y tế chỉ áp dụng nếu nâng phạm vi sang chẩn đoán/điều trị lâm sàng.
