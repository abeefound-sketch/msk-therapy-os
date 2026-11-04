# MSK-Therapy-OS — Milestone P22 Audit
## P22_01: Anatomical Source-of-Truth Registry & Coordinate Transformation Contract

**Tài liệu ID:** `MSK-P22-AUD-001`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Định nghĩa Hệ Quy Chiếu Chuẩn (Canonical Reference Frame)

MSK-Therapy-OS thiết lập một hệ quy chiếu giải phẫu chuẩn duy nhất làm nền tảng (`CANONICAL_BODYPARTS3D_FRAME`):
- **Gốc tọa độ ($0,0,0$):** Mặt phẳng sàn ngay dưới tâm khối cơ thể người đứng thẳng giải phẫu chuẩn.
- **Mặt phẳng sàn:** $Y = 0.00\text{ m}$.
- **Tâm khớp háng / Đan Điền:** $Y \approx 0.86\text{ m}$.
- **Đỉnh đốt sống C7 (Đại Chùy GV14):** $Y \approx 1.478\text{ m}$.
- **Đỉnh đầu (Bách Hội GV20):** $Y \approx 1.718\text{ m}$.
- **Quy ước trục không gian (Right-Handed):**
  * $+X$: Sang phải của bệnh nhân (Patient Right)
  * $+Y$: Hướng lên đỉnh đầu (Superior / Up)
  * $+Z$: Hướng ra phía trước ngực (Anterior / Front)
- **Đơn vị đo lường:** Mét (SI Meters).

---

### 2. Ma trận Chuyển đổi Đồng nhất 4×4 giữa các Không gian (Homogeneous Transforms)

#### Chuyển đổi từ Canonical sang Blender ($T_{\text{Canonical} \to \text{Blender}}$)
Blender sử dụng trục $+Z$ hướng lên trên và $+Y$ hướng ra xa:
$$
\begin{bmatrix} X_{\text{Blender}} \\ Y_{\text{Blender}} \\ Z_{\text{Blender}} \\ 1 \end{bmatrix}
=
\begin{bmatrix}
1 & 0 & 0 & 0 \\
0 & 0 & 1 & 0 \\
0 & 1 & 0 & 0 \\
0 & 0 & 0 & 1
\end{bmatrix}
\begin{bmatrix} X_{\text{Canonical}} \\ Y_{\text{Canonical}} \\ Z_{\text{Canonical}} \\ 1 \end{bmatrix}
$$
Ma trận này là trực giao và đối xứng ($T^{-1} = T$), đảm bảo tính hoàn nguyên số học tuyệt đối:
$$\| p - T^{-1}(T(p)) \|_\infty < 10^{-12}\text{ m}$$

---

### 3. Bộ Quy tắc An toàn Fail-Closed Bắt buộc

1. **Từ chối sai lệch đơn vị (Scale Divergence Guard):** Nếu khoảng cách độ lớn của tọa độ vượt quá $5.0\text{ m}$ hoặc nhỏ hơn $5\text{ mm}$ đối với cơ thể người, hệ thống ném ngoại lệ `ScaleDivergenceError` và từ chối xử lý, ngăn chặn việc nhầm lẫn giữa milimét và mét.
2. **Từ chối đảo trục bên (Laterality Inversion Conflict):** Nếu huyệt được khai báo bên phải (`side="RIGHT"`) nhưng tọa độ $X < -0.02\text{ m}$, hệ thống ném ngoại lệ `LateralityInversionConflictError`.
3. **Từ chối khi mã băm mesh bị thay đổi:** Mọi thay đổi cấu trúc lưới làm lệch SHA-256 đều ném `MeshChecksumMismatchError`.
4. **Từ chối tuyến kinh thiếu điểm:** Tuyến kinh có ít hơn 4 điểm ném ngoại lệ `IncompletePathwayError`.
