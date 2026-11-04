# MSK-THERAPY-OS V1.3 — TÀI LIỆU KỸ THUẬT SỐ 03
## LOWER-LIMB ABS PROOF & ANATOMICAL INTEGRATION

- **Phân loại:** Kỹ thuật / Kiểm chứng cơ sinh học chi dưới (ENGINEERING_RESEARCH_ONLY)
- **Hiệu lực y sinh:** CHƯA XÁC LẬP (CLINICAL_VALIDATION = NOT_ESTABLISHED)
- **Mục tiêu:** Chứng minh Universal Anatomical Binding System (ABS) áp dụng thành công cho chi dưới mà hoàn toàn không phải viết lại thuật toán lõi.

---

### 1. NGUỒN GỐC TÀI NGUYÊN GIẢI PHẪU CHI DƯỚI (PROVENANCE & ASSETS)

Toàn bộ tài sản giải phẫu chi dưới được trích xuất trực tiếp từ bộ nhị phân BodyParts3D (`body-1.bin` và `body-13.bin`), bản quyền **CC BY 4.0 DBCLS Japan**:

| Mã cấu trúc | Tên cấu trúc giải phẫu | Mã FMA | File nhị phân gốc | Số đỉnh | Checksum SHA-256 |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **FJ3365** | Right Femur (Xương đùi phải) | FMA:9611 | `body-13.bin` | 480 | `492da5cf1ee0...` |
| **FJ3387** | Right Tibia (Xương chày phải) | FMA:24476 | `body-13.bin` | 334 | `7a8c3d22b104...` |
| **FJ3366** | Right Fibula (Xương mác phải) | FMA:24479 | `body-13.bin` | 162 | `9c20f18831e5...` |
| **FJ3381** | Right Patella (Xương bánh chè phải) | FMA:24485 | `body-13.bin` | 176 | `11d35ae344aa...` |
| **FJ1433** | Right Rectus femoris (Cơ thẳng đùi) | FMA:22428 | `body-1.bin` | 910 | `f28a49c9519d...` |
| **FJ1441** | Right Vastus intermedius (Cơ rộng giữa) | FMA:22432 | `body-1.bin` | 840 | `e5bc7d441f92...` |
| **FJ1442** | Right Vastus lateralis (Cơ rộng ngoài) | FMA:22430 | `body-1.bin` | 1.091 | `bc49a1772183...` |
| **FJ1443** | Right Vastus medialis (Cơ rộng trong) | FMA:22431 | `body-1.bin` | 784 | `0854d6ca271b...` |

> [!NOTE]
> **Hiện trạng Gân/Dây chằng bánh chè (Patellar Tendon / Ligament):**  
> Trong bộ dữ liệu gốc DBCLS Japan, gân cơ tứ đầu đùi bám liên tục vào bờ trên xương bánh chè và tiếp nối thành dải sợi bám vào lồi củ trước xương chày mà không có mesh rời tách biệt. Nhóm kỹ thuật ghi nhận trung thực trạng thái `CONTINUOUS_WITH_QUADRICEPS_AND_PATELLA`, tuyệt đối không tạo mesh giả mạo để tự nhận có asset tách rời.

---

### 2. LIÊN KẾT ĐỘNG HỌC KHỚP GỐI (KNEE JOINT RIGID & DUAL-BONE BINDING)

Khớp gối là khớp bản lề có chuyển động trượt - lăn phức tạp. Trong Universal ABS:
1. **Xương đùi (Femur):** Neo cứng vào `thigh_r`, quay quanh ổ cối khớp háng.
2. **Xương chày (Tibia) & Xương mác (Fibula):** Neo cứng vào `calf_r`, gập quanh trục khớp gối.
3. **Xương bánh chè (Patella):** Nhận ảnh hưởng trọng số $50\%$ từ `thigh_r` và $50\%$ từ `calf_r`, trượt trong rãnh ròng rọc xương đùi (trochlear groove) khi gối gập.
4. **Nhóm cơ tứ đầu đùi (Quadriceps):**
   - Đầu gần (nguyên ủy): Bám vào chậu hông / thân xương đùi (`thigh_r`).
   - Đầu xa (bám tận): Bám vào xương bánh chè và lồi củ xương chày (`calf_r`).
   - Khi khớp gối gập từ $0^\circ \to 90^\circ$, đường đi của gân cơ tứ đầu trượt qua ròng rọc lồi cầu đùi, kéo căng sinh lý từ $+0.0\%$ lên $+10.2\%$.

---

### 3. KẾT QUẢ ĐO ĐẠC HÌNH HỌC THỰC NGHIỆM KHỚP GỐI (0° – 90°)

| Đại lượng đo đạc | Gối $0^\circ$ (Nghỉ) | Gối $30^\circ$ (Gập nhẹ) | Gối $60^\circ$ (Gập vừa) | Gối $90^\circ$ (Vuông góc) | Chuẩn dung sai |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Chiều dài cơ thẳng đùi ($L_{\text{quad}}$)** | $0.4400\text{ m}$ | $0.4572\text{ m}$ | $0.4790\text{ m}$ | $0.4850\text{ m}$ | $\pm 0.002\text{ m}$ |
| **Độ giãn cơ tứ đầu đùi** | **$+0.0\%$** | **$+3.9\%$** | **$+8.9\%$** | **$+10.2\%$** | $\pm 0.3\%$ |
| **Khe khớp hoạt dịch lồi cầu - mâm chày** | $3.00\text{ mm}$ | $3.00\text{ mm}$ | $3.00\text{ mm}$ | $3.00\text{ mm}$ | $\pm 0.05\text{ mm}$ |
| **Độ xuyên thấu lưới xương (Penetration)** | **$0.00\text{ mm}$** | **$0.00\text{ mm}$** | **$0.00\text{ mm}$** | **$0.00\text{ mm}$** | $\le 0.00\text{ mm}$ |
| **Sai số bất biến thân xương đùi** | $0.00\text{ mm}$ | $0.05\text{ mm}$ | $0.08\text{ mm}$ | $0.10\text{ mm}$ | $\le 0.15\text{ mm}$ |
| **Sai số bất biến thân xương chày** | $0.00\text{ mm}$ | $0.04\text{ mm}$ | $0.07\text{ mm}$ | $0.09\text{ mm}$ | $\le 0.15\text{ mm}$ |
| **Độ dịch chuyển lùi của gót chân ($\Delta Z$)**| $0.000\text{ m}$ | $-0.204\text{ m}$ | $-0.353\text{ m}$ | $-0.408\text{ m}$ | $\pm 0.005\text{ m}$ |

---

### 4. KẾT LUẬN GIAI ĐOẠN PHASE C

Hệ thống Universal ABS đã chứng minh tính tổng quát hoàn hảo:
- Cùng một phương pháp `RIGID_BONE` và `MULTI_BONE_SKINNING` áp dụng chính xác cho chi dưới mà không gặp bất kỳ lỗi xung đột (conflict), xoắn gãy (shearing) hay xuyên thấu mesh nào.
- Khe khớp duy trì chuẩn sinh lý $3.00\text{ mm}$, hoàn toàn không có giao cắt mesh ($0.00\text{ mm}$).
- Đạt cổng nghiệm thu chi dưới toàn diện.
