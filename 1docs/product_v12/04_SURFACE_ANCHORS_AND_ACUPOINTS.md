# MSK-THERAPY-OS V1.2 — MỐC HUYỆT VÀ ĐÍNH BỀ MẶT ĐỘNG
## SURFACE ANCHORS & DYNAMIC ACUPOINTS SPECIFICATION

> [!NOTE]
> **Module triển khai:** [`surface_anchor_binding.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_binding/surface_anchor_binding.py)  
> **Huyệt đạo thực nghiệm:** Thủ Dương Minh Đại Trường Kinh (LI) — `LI4`, `LI11`, `LI14`, `LI15`.  
> **Ranh giới:** `ENGINEERING_RESEARCH_ONLY; NOT_FOR_CLINICAL_ACUPUNCTURE`

---

## 1. BẢNG MỐC HUYỆT VÀ LIÊN KẾT CƠ - XƯƠNG - DA

| Mã huyệt | Tên Hán Việt | Tên Tiếng Anh | Xương Canonical | Cấu trúc giải phẫu chuẩn (BP3D) | Tọa độ Offset cục bộ ($m$) | Pháp tuyến mặt da $\vec{n}$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LI4** | Hợp Cốc | Hegu | `hand_r` | `FJ3352` (Xương đốt bàn 2) | `[0.015, 0.025, 0.012]` | `[0.0, 0.0, 1.0]` |
| **LI11** | Khúc Trì | Quchi | `lowerarm_r` | `FJ3349` (Xương quay & Lồi cầu ngoài) | `[-0.020, 0.005, 0.035]` | `[-0.707, 0.0, 0.707]` |
| **LI14** | Tí Nhu | Binao | `upperarm_r` | `FJ3368` (Lồi củ cơ delta xương cánh tay) | `[-0.040, 0.120, 0.010]` | `[-1.0, 0.0, 0.0]` |
| **LI15** | Kiên Ngung | Jianyu | `clavicle_r` | `FJ3362` (Mỏm cùng vai & Xương đòn) | `[-0.140, -0.010, 0.025]` | `[0.0, 1.0, 0.0]` |

---

## 2. CƠ CHẾ ĐỒNG BỘ ĐỘNG HỌC KHI GẬP KHUỶU

1. **Huyệt Hợp Cốc (LI4):**
   - Đính vào xương bàn tay (`hand_r`) và bề mặt mu bàn tay.
   - Khi khuỷu gập $0^\circ \to 90^\circ$, xương bàn tay nâng cao dọc theo trục $Y$ thế giới ($\Delta Y = +0.2386\text{ m}$). Huyệt LI4 di chuyển chính xác theo chuyển động của bàn tay, không bị rớt lại hay trôi dạt khỏi xương đốt bàn 2.
2. **Huyệt Khúc Trì (LI11):**
   - Đính vào cẳng tay trên (`lowerarm_r`) tại nếp gấp khuỷu ngoài.
   - Khi khuỷu gập $90^\circ$, huyệt LI11 nằm chính xác tại đỉnh nếp gấp giữa lồi cầu ngoài xương cánh tay và cơ ngửa dài/cơ quay.
3. **Huyệt Tí Nhu (LI14) & Kiên Ngung (LI15):**
   - Duy trì liên kết với xương cánh tay (`upperarm_r`) và đai vai (`clavicle_r`), ổn định vị trí tương đối khi khuỷu gập duỗi và chỉ chuyển động khi dạng khớp vai.

---

## 3. HIỂN THỊ TRỰC QUAN TRONG THREE.JS STUDIO

- Mỗi huyệt được biểu diễn bằng một khối cầu phát sáng PBR (Emissive sphere) kèm vòng hào quang xung nhịp (`pulsing glow ring`).
- Người dùng có thể quan sát xuyên thấu vị trí huyệt đạo tương quan với mô da bên ngoài và đầu xương giải phẫu bên trong trong chế độ `OVERLAY_MODE`.
