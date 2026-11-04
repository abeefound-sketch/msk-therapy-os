# MSK-THERAPY-OS V1.3 — TÀI LIỆU KỸ THUẬT SỐ 05
## DYNAMIC ACUPOINTS & FULL-BODY 3D MERIDIANS SPECIFICATION

- **Phân loại:** Kỹ thuật / Đồ họa giải phẫu y học cổ truyền (ENGINEERING_RESEARCH_ONLY)
- **Chuẩn tham chiếu quốc tế & quốc gia:**
  - WHO Standard Acupuncture Point Locations in the Western Pacific Region (2008)
  - Tiêu chuẩn quốc gia Trung Quốc GB/T 12346-2021 (Nomenclature and location of meridian points)
- **Hiệu lực y sinh:** CHƯA XÁC LẬP (CLINICAL_VALIDATION = NOT_ESTABLISHED). Tuyệt đối cấm sử dụng mô hình đồ họa để hướng dẫn hoặc thực hành châm cứu, bấm huyệt hay điện châm trên người bệnh.

---

### 1. DANH MỤC 6 MỐC HUYỆT ĐỘNG HỌC (CHI TRÊN & CHI DƯỚI)

Universal ABS tích hợp 6 mốc huyệt tiêu chuẩn, liên kết trực tiếp vào các đốt xương cha tương ứng:

```
CHI TRÊN (Thủ Dương Minh Đại Trường Kinh):
[LI15 Kiên Ngung] (clavicle_r)
       │
[LI14 Tí Nhu]     (upperarm_r)
       │
[LI11 Khúc Trì]   (lowerarm_r)
       │
[LI4 Hợp Cốc]     (hand_r)

CHI DƯỚI (Túc Dương Minh Vị Kinh & Túc Thiếu Âm Thận Kinh):
[ST36 Túc Tam Lý] (calf_r - Mặt trước ngoài xương chày)
       │
[KI3 Thái Khê]    (calf_r / foot_r - Hõm sau mắt cá trong)
```

#### Bảng thông số định vị chuẩn:

| Mã huyệt | Tên huyệt | Kinh lạc | Xương cha | Tọa độ Offset (m) | Tham chiếu chuẩn |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LI4** | Hợp Cốc (Hegu) | Đại Trường (LI) | `hand_r` | `(0.040, 0.020, 0.015)` | WHO 2008: tr. 45; GB/T 12346-2021: 4.2 |
| **LI11** | Khúc Trì (Quchi) | Đại Trường (LI) | `lowerarm_r` | `(0.010, 0.030, 0.010)` | WHO 2008: tr. 47; GB/T 12346-2021: 4.9 |
| **LI14** | Tí Nhu (Binao) | Đại Trường (LI) | `upperarm_r` | `(0.120, 0.025, 0.012)` | WHO 2008: tr. 48; GB/T 12346-2021: 4.12 |
| **LI15** | Kiên Ngung (Jianyu) | Đại Trường (LI) | `clavicle_r` | `(0.180, 0.035, 0.010)` | WHO 2008: tr. 49; GB/T 12346-2021: 4.13 |
| **ST36** | Túc Tam Lý (Zusanli) | Vị Kinh (ST) | `calf_r` | `(0.025, 0.018, -0.065)` | WHO 2008: tr. 67; GB/T 12346-2021: 5.36 |
| **KI3** | Thái Khê (Taixi) | Thận Kinh (KI) | `calf_r` | `(-0.018, 0.010, -0.370)`| WHO 2008: tr. 109; GB/T 12346-2021: 9.3 |

---

### 2. PHÂN TÍCH ĐỊNH VỊ GIẢI PHẪU HUYỆT CHI DƯỚI (ST36 & KI3)

1. **Huyệt Túc Tam Lý (ST36):**
   - *Vị trí chuẩn:* Dưới mắt đầu gối ngoài (Độc Tỵ - ST35) 3 thốn (khoảng 1 thốn dưới mào chày), cách mào chày trước ra phía ngoài một khoát ngón tay (khoảng 1 ngón trỏ).
   - *Gắn kết trong ABS:* Neo trực tiếp vào thân xương chày `calf_r`. Khi khớp gối gập $60^\circ \to 90^\circ$, mốc huyệt ST36 chuyển động đồng bộ theo góc quay của xương chày, nâng cao $+0.041\text{ m}$ và duy trì khoảng cách ổn định cách mào chày $18\text{ mm}$.
2. **Huyệt Thái Khê (KI3):**
   - *Vị trí chuẩn:* Tại chỗ lõm giữa điểm cao nhất của mắt cá trong xương chày và bờ trong gân gót (Achilles tendon).
   - *Gắn kết trong ABS:* Neo tại đầu dưới xương chày (`calf_r`) tiếp giáp cổ chân (`foot_r`). Khi bàn chân gập mu hoặc duỗi, khoảng cách giữa mắt cá trong và gân gót được bảo toàn, mốc huyệt dịch chuyển chính xác theo khối cổ chân.

---

### 3. ĐƯỜNG KINH 3D DẠNG ỐNG ĐỘNG (DYNAMIC 3D TUBE MERIDIANS)

MSK-Therapy-OS V1.3 hiện thực hóa đồng thời 2 đường kinh lạc thể tích:
1. **Kinh Đại Trường (LI):** Ống màu vàng hoàng kim (`#ffd700`), bán kính $3.0\text{ mm}$, uốn cong mềm mại qua LI4 $\to$ LI11 $\to$ LI14 $\to$ LI15.
2. **Kinh Vị (ST):** Ống màu xanh ngọc dạ quang (`#00d2ff`), bán kính $3.0\text{ mm}$, uốn cong từ bờ ngoài xương bánh chè qua ST36 chạy dọc cẳng chân trước xuống mu bàn chân.
3. **Cơ chế tái tạo thời gian thực:**
   ```javascript
   const curve = new THREE.CatmullRomCurve3(points);
   tubeMesh.geometry.dispose();
   tubeMesh.geometry = new THREE.TubeGeometry(curve, 32, 0.003, 8, false);
   ```
   Ống kinh lạc uốn cong trơn tru theo mặt da khi tay và chân cùng vận động mà không bị gãy góc (kinking) hay thắt nút (self-intersection).
