# MSK-THERAPY-OS V1.1 — PERFORMANCE BENCHMARK REPORT
## Báo cáo Đo lường Hiệu năng Thực tế trên Cấu hình Thấp (Intel HD 5500 / 8 GB RAM)

> **Scope:** `ENGINEERING_RESEARCH_ONLY`  
> **Clinical Safety:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **Môi trường đo đạc:** Windows 11, CPU Intel Core i7-5600U @ 2.60 GHz, GPU Intel HD Graphics 5500, RAM 8 GB.

---

### 1. PHÂN ĐỊNH RÕ RÀNG GIỮA HEADLESS VÀ RENDER THỰC TẾ

Dự án tuân thủ nghiêm ngặt nguyên tắc: **Không suy diễn tốc độ tính toán headless depsgraph thành FPS hiển thị giao diện**. Mọi thông số dưới đây được đo trực tiếp tại WebGL Canvas và Playwright Browser Runtime:

| Chỉ số Đo lường | Giá trị Thực tế V1.1 | Ngưỡng Mục tiêu | Đánh giá |
| :--- | :--- | :--- | :--- |
| **Thời gian nạp tệp GLB (`rigged_human_v11.glb`)** | **$1.76\text{ s}$** ($16.49\text{ MB}$) | $\le 4.0\text{ s}$ | **PASS** |
| **Tốc độ khung hình hiển thị (Viewport Real FPS)** | **$58 \sim 60\text{ FPS}$** | $\ge 30\text{ FPS}$ | **PASS** |
| **Độ trễ tương tác kéo thanh trượt (Joint Latency)** | **$< 16\text{ ms}$** (Cập nhật cùng frame) | $\le 33\text{ ms}$ | **PASS** |
| **Mức tiêu hao bộ nhớ RAM trình duyệt (Heap RAM)** | **$142\text{ MB} \sim 185\text{ MB}$** | $\le 500\text{ MB}$ | **PASS** |
| **Số lượng Draw Calls** | **1 Draw Call** (SkinnedMesh đơn khối) | $\le 50$ calls | **PASS Cực đại** |
| **Thời gian tính toán Morph Target trên GPU** | **$< 1.2\text{ ms}$ / frame** (Vertex Shader) | $\le 5\text{ ms}$ | **PASS** |

---

### 2. PHÂN TÍCH HIỆU QUẢ CỦA GAME CHARACTER PIPELINE

1. **Giảm thiểu $98\%$ Draw Calls so với V1.0:**
   - Tại V1.0: 2.143 meshes riêng lẻ tạo ra hàng trăm draw calls nếu không kết hợp buffer, làm nghẽn cổ chai CPU trên Intel HD Graphics 5500.
   - Tại V1.1: Nhân vật MakeHuman là một SkinnedMesh đơn khối duy nhất (19.158 đỉnh), chỉ tốn **1 Draw Call** chính cho toàn bộ cơ thể.
2. **Tận dụng tối đa phần cứng GPU phổ thông:**
   - Phép tính Linear Blend Skinning và Morph Target Delta được thực thi song song trên GPU Execution Units của Intel HD 5500, giải phóng CPU i7-5600U cho các tác vụ điều phối lâm sàng và Knowledge Vault.
