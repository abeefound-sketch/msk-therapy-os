# MSK-THERAPY-OS V1.1 — DYNAMIC ACUPOINTS ACCEPTANCE
## Báo cáo Nghiệm thu Huyệt vị Động và Đường kinh 3D

> **Scope:** `ENGINEERING_RESEARCH_ONLY`  
> **Clinical Safety:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`  
> **Bộ điều hợp:** `msk_therapy_os/character_acupoints_adapter.py`

---

### 1. NGUYÊN TẮC RÀO CHẮN AN TOÀN (SAFETY GUARDRAILS)

1. **Phân cấp Trạng thái Quản trị (Governance Statuses):**
   - `CANONICAL_SOURCE_REFERENCE`: Tọa độ mốc trích dẫn nguyên văn từ tài liệu tiêu chuẩn WHO 2008 hoặc GB/T 12346-2021.
   - `REGISTERED_CANDIDATE`: Mốc huyệt đã được ánh xạ vào xương hoặc bề mặt da nhân vật nhưng chưa qua hội đồng chuyên gia y khoa nghiệm thu.
   - `USER_ADJUSTED`: Mốc huyệt do người dùng tự tinh chỉnh vị trí theo ca nghiên cứu cụ thể.
   - `EXPERT_REVIEW_PENDING`: Đang chờ thẩm định của chuyên gia châm cứu lâm sàng.
   - `INVALID_BINDING`: Huyệt bị gán sai vào phân đoạn giải phẫu không tương thích (ví dụ: gán LI4 vào xương đòn).
2. **Nghiêm cấm tự tuyên bố ANATOMICAL_VERIFIED:** Toàn bộ huyệt vị mới trên da nhân vật duy trì trạng thái **`REGISTERED_CANDIDATE`** hoặc **`USER_ADJUSTED`**, có đóng dấu watermark `RESEARCH_ONLY`.

---

### 2. KẾT QUẢ ĐĂNG KÝ CÁC MỐC HUYỆT TIÊU BIỂU (LI4, LI11, LI14, LI15)

| Mã Huyệt | Tên Huyệt (Hán-Việt) | Xương / Khớp Neo | Cấu Trúc BodyParts3D | Tọa độ Offset Cục bộ | Trạng thái Quản trị |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`LI4`** | Hợp Cốc (Hégǔ) | `hand_r` | `FJ3352` (Metacarpal 2 R) | `[0.015, 0.035, 0.025]` m | <span class="pill-candidate">REGISTERED_CANDIDATE</span> |
| **`LI11`** | Khúc Trì (Qūchí) | `lowerarm_r` | `FJ3381` (Radius R / Crease) | `[0.025, 0.010, 0.015]` m | <span class="pill-candidate">REGISTERED_CANDIDATE</span> |
| **`LI14`** | Tí Nhu (Bìnào) | `upperarm_r` | `FJ3368` (Deltoid Insertion) | `[-0.020, -0.150, 0.035]` m | <span class="pill-candidate">REGISTERED_CANDIDATE</span> |
| **`LI15`** | Kiên Ngung (Jiānyú) | `clavicle_r` | `FJ3238` (Acromion dip) | `[-0.140, 0.010, 0.025]` m | <span class="pill-candidate">REGISTERED_CANDIDATE</span> |

---

### 3. ĐƯỜNG KINH THỦ DƯƠNG MINH 3D ĐỘNG (DYNAMIC MERIDIAN TUBE)

- **Cơ chế hoạt động:** Đường kinh không dùng các tọa độ cố định trong không gian thế giới. Thay vào đó, đường kinh được cấu tạo từ các đỉnh động kết nối chuỗi mốc:
  $$\mathbf{P}_{\text{LI4}}(t) \longrightarrow \mathbf{P}_{\text{LI11}}(t) \longrightarrow \mathbf{P}_{\text{LI14}}(t) \longrightarrow \mathbf{P}_{\text{LI15}}(t)$$
- Khi cánh tay gập khuỷu từ $0^\circ \to 45^\circ \to 90^\circ$ hoặc dang vai $0^\circ \to 60^\circ$:
  - Mốc `LI4` di chuyển cùng bàn tay theo ma trận thế giới của `hand_r`.
  - Mốc `LI11` di chuyển cùng nếp gấp khuỷu tay theo `lowerarm_r`.
  - Đoạn đường kinh giữa `LI4` và `LI11` tự động uốn cong theo đoạn cẳng tay, giữ dính chặt vào bề mặt da mà không bị đứt gãy hoặc xuyên sâu vào lòng xương.
- **Tính năng Undo / Redo & Lịch sử phiên bản:**
  - Hỗ trợ hoàn tác (Undo) và làm lại (Redo) mọi thao tác di chuyển vị trí mốc huyệt.
  - Tự động tăng số hiệu phiên bản (`version`) và lưu trữ nhật ký điều chỉnh kèm dấu thời gian.
