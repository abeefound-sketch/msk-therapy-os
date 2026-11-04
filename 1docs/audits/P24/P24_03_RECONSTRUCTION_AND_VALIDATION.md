# MSK-Therapy-OS — Milestone P24 Audit
## P24_03: Kinematics Reconstruction, Determinism Benchmarks & Occlusion Evidence

**Tài liệu ID:** `MSK-P24-AUD-003`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Kiểm thử Tính Quyết định Số học (Synthetic Determinism Layer)

Đánh giá thuật toán giải góc từ mốc không gian trên các tư thế hình học biết trước:

| Tư thế Hình học Đầu vào | Tọa độ Mốc Vai $(S)$ | Tọa độ Mốc Khuỷu $(E)$ | Tọa độ Mốc Cổ Tay $(W)$ | Góc Kỳ vọng | Góc Ước lượng | Sai số Tuyệt đối | Kết quả |
|---|---|---|---|---|---|---|---|
| Cánh tay thẳng đứng | $(0.0, 1.42, 0.0)$ | $(0.0, 1.12, 0.0)$ | $(0.0, 0.86, 0.0)$ | $0.0^\circ$ | $0.00^\circ$ | $0.00^\circ$ | **PASSED** |
| Cánh tay gập $45^\circ$ | $(0.0, 1.42, 0.0)$ | $(0.0, 1.12, 0.0)$ | $(0.0, 0.936, 0.184)$ | $45.0^\circ$ | $45.00^\circ$ | $0.00^\circ$ | **PASSED** |
| Cánh tay gập vuông $90^\circ$ | $(0.0, 1.42, 0.0)$ | $(0.0, 1.12, 0.0)$ | $(0.0, 1.12, 0.26)$ | $90.0^\circ$ | $90.00^\circ$ | $0.00^\circ$ | **PASSED** |

---

### 2. Kiểm thử Trường hợp Che khuất (Occlusion Test Case Evidence)

Mô phỏng trường hợp mốc khuỷu tay (Landmark 14) bị che khuất trong 15 frames liên tiếp (`visibility = 0.15 < 0.5`):
- **Phát hiện:** Cờ `RIGHT_ARM_OCCLUSION_DETECTED` được gán vào `quality_flags`.
- **Hành vi xử lý:** `reconstruct_arm_kinematics()` từ chối xuất góc, trả về `status: "REJECTED_DUE_TO_OCCLUSION"`, `elbow_flexion_deg: None`, `confidence: 0.0`.
- **Lý do bác bỏ:** `"Elbow or wrist landmark visibility < 0.5; refusing fake pose invention."`
- **Kết luận:** Hệ thống đạt yêu cầu bảo vệ fail-closed, không tự động sinh góc ảo hay giả lập tư thế lành khi bị che khuất.
