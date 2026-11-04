# MSK-THERAPY-OS V1.2.1 — TÀI LIỆU KỸ THUẬT SỐ 04
## DYNAMIC ACUPOINTS & 3D MERIDIAN SPECIFICATION

- **Phân loại:** Kỹ thuật / Mô phỏng giải phẫu số (ENGINEERING_RESEARCH_ONLY)
- **Chuẩn nguồn tham chiếu:** 
  - WHO Standard Acupuncture Point Locations in the Western Pacific Region (2008)
  - Tiêu chuẩn quốc gia Trung Quốc GB/T 12346-2021 (Nomenclature and location of meridian points)
- **Hiệu lực y học:** CHƯA XÁC LẬP (CLINICAL_VALIDATION = NOT_ESTABLISHED). Tuyệt đối không dùng mô hình để hướng dẫn châm cứu, điện châm hoặc bấm huyệt trên bệnh nhân thực tế.

---

### 1. DANH MỤC HUYỆT VỊ ĐỘNG HỌC TRÊN CHI TRÊN (DYNAMIC ACUPOINTS)

MSK-Therapy-OS V1.2.1 định vị chính xác 4 mốc huyệt thuộc **Thủ Dương Minh Đại Trường Kinh (Large Intestine Meridian - LI)** trên cánh tay, khắc phục hoàn toàn các sai lệch về xương cha hoặc nhầm lẫn bên (laterality) trước đây:

```
[LI15 Kiên Ngung] (Mỏm cùng vai)
        │
[LI14 Tí Nhu]     (Bờ ngoài cánh tay / Chân cơ delta)
        │
[LI11 Khúc Trì]   (Nếp gấp khuỷu ngoài)
        │
[LI4 Hợp Cốc]     (Mu bàn tay / Giữa xương bàn I & II)
```

#### Bảng thông số định vị giải phẫu

| Mã huyệt | Tên huyệt | Xương gắn kết (Parent Bone) | Tọa độ tương đối (Local Offset m) | Tọa độ chuẩn ($0^\circ$ Rest m) | Tham chiếu tiêu chuẩn |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LI4** | Hợp Cốc (Hegu) | `hand_r` | `(0.040, 0.020, 0.015)` | `(0.760, 1.480, 0.005)` | WHO 2008: tr. 45; GB/T 12346-2021: 4.2 |
| **LI11** | Khúc Trì (Quchi) | `lowerarm_r` | `(0.010, 0.030, 0.010)` | `(0.470, 1.490, 0.000)` | WHO 2008: tr. 47; GB/T 12346-2021: 4.9 |
| **LI14** | Tí Nhu (Binao) | `upperarm_r` | `(0.120, 0.025, 0.012)` | `(0.300, 1.485, 0.002)` | WHO 2008: tr. 48; GB/T 12346-2021: 4.12 |
| **LI15** | Kiên Ngung (Jianyu) | `clavicle_r` | `(0.180, 0.035, 0.010)` | `(0.180, 1.515, -0.010)` | WHO 2008: tr. 49; GB/T 12346-2021: 4.13 |

---

### 2. CƠ CHẾ BÁM DÍNH VÀ ĐỘNG HỌC MỐC HUYỆT (SURFACE ANCHOR KINEMATICS)

1. **Khắc phục lỗi định vị LI4:**
   - Trong một số bản thử nghiệm V1.0 cũ, huyệt LI4 từng bị gán nhầm cha vào `clavicle_l` hoặc `clavicle_r`.
   - Trong V1.2 và V1.2.1, LI4 được ràng buộc tuyệt đối vào `hand_r`. Khi xương cẳng tay (`lowerarm_r`) xoay quanh khớp khuỷu, ma trận thế giới của `hand_r` được nhân dồn theo chuỗi động học:
     $$M_{\text{hand\_r}}^{\text{world}} = M_{\text{clavicle}}^{\text{world}} \times M_{\text{upperarm}}^{\text{local}} \times M_{\text{lowerarm}}^{\text{local}} \times M_{\text{hand}}^{\text{local}}$$
2. **Quỹ đạo chuyển động của LI4 khi gập khuỷu:**
   - Tại $0^\circ$ (Duỗi thẳng): $Y_{\text{LI4}} = 1.480\text{ m}$.
   - Tại $45^\circ$ (Gập trung gian): $Y_{\text{LI4}} = 1.678\text{ m}$ ($\Delta Y = +0.198\text{ m}$).
   - Tại $90^\circ$ (Gập vuông góc): $Y_{\text{LI4}} = 1.760\text{ m}$ ($\Delta Y = +0.280\text{ m}$).
   - Tại $120^\circ$ (Gập sâu): $Y_{\text{LI4}} = 1.792\text{ m}$ ($\Delta Y = +0.312\text{ m}$).
   - Mốc huyệt di chuyển hoàn toàn trơn tru cùng bàn tay, không bị rớt lại hay lệch khỏi bề mặt da.

---

### 3. ĐƯỜNG KINH LẠC DẠNG ỐNG ĐỘNG 3D (DYNAMIC 3D TUBE GEOMETRY)

Khác với đường vẽ 2D hoặc đường line cứng cố định trong Three.js, V1.2.1 hiện thực hóa đường kinh bằng cấu trúc hình học ống tròn thể tích 3D thực:

1. **Đường cong Spline liên tục (`THREE.CatmullRomCurve3D`):**
   - Thuật toán lấy tọa độ thế giới hiện hành của 4 mốc huyệt LI4, LI11, LI14, LI15 kèm theo các điểm trung gian nội suy theo bề mặt da cẳng tay và cánh tay.
2. **Tái tạo lưới động học (Dynamic Mesh Generation):**
   - Bán kính ống: $r = 3.0\text{ mm}$ (`radius = 0.003`).
   - Độ phân giải: 32 phân đoạn dọc, 8 phân đoạn tròn.
   - Vật liệu: `MeshStandardMaterial` màu vàng kinh lạc (`#ffd700`), độ nhám $0.3$, độ phát quang nhẹ (`emissive = #ffaa00`, intensity: $0.25$).
   - Tại mỗi khung hình chuyển động hoặc khi người dùng kéo thanh trượt góc gập, `meridianLine.geometry` được cập nhật đồng bộ:
     ```javascript
     const curve = new THREE.CatmullRomCurve3D(points, false, 'catmullrom', 0.2);
     meridianLine.geometry.dispose();
     meridianLine.geometry = new THREE.TubeGeometry(curve, 32, 0.003, 8, false);
     ```
3. **Độ ổn định hình học:**
   - Không xuất hiện hiện tượng thắt nút (self-intersection).
   - Không bị xoắn gập (twisting artifacts) tại góc khuỷu gập sâu $120^\circ$.
   - Giữ nguyên khoảng cách bám trên mặt phẳng da ngoài.

---

### 4. GIỚI HẠN VÀ KHUYẾN CÁO Y KHOA

> [!WARNING]
> Toàn bộ đường kinh và mốc huyệt trong mô hình này được xây dựng cho mục đích **mô phỏng kỹ thuật đồ họa và giáo dục giải phẫu đại cương (ENGINEERING_RESEARCH_ONLY)**. Đường kinh là mô hình toán học spline nội suy trực quan, không phải là cấu trúc giải phẫu vật lý được công nhận trong y học hiện đại và chưa được kiểm nghiệm an toàn lâm sàng (CLINICAL_VALIDATION = NOT_ESTABLISHED).
