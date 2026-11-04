# MSK-THERAPY-OS V1.2 — HỆ THỐNG BIẾN DẠNG CƠ SINH HỌC
## MUSCLE DEFORMATION BINDING SPECIFICATION

> [!NOTE]
> **Module triển khai:** [`muscle_deformation_binding.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_binding/muscle_deformation_binding.py)  
> **Nguồn gốc dữ liệu:** BodyParts3D 4.0 (CC BY 4.0 DBCLS Japan)  
> **Các cơ bắp hoạt động:** Biceps brachii (2 đầu), Triceps brachii (3 đầu), Brachialis.  
> **Ranh giới:** `ENGINEERING_RESEARCH_ONLY; NOT_FOR_CLINICAL_USE`

---

## 1. DANH MỤC CƠ BẮP GIẢI PHẪU VÀ THÔNG SỐ ĐỘNG HỌC

| ID | Tên cơ giải phẫu | Xương nguyên ủy | Xương bám tận | Chiều dài nghỉ $L_{\text{rest}}$ ($0^\circ$) | Chiều dài gập $L_{90}$ ($90^\circ$) | Tỷ lệ co/giãn ($90^\circ$) | Hiện tượng cơ học |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FJ1478` | Biceps brachii (Đầu dài) | `upperarm_r` | `lowerarm_r` (Xương quay) | $0.315\text{ m}$ | $0.242\text{ m}$ | $-23.17\%$ (Co ngắn) | Phồng bụng cơ $k = 1.141$ |
| `FJ1512` | Biceps brachii (Đầu ngắn) | `upperarm_r` | `lowerarm_r` (Xương quay) | $0.298\text{ m}$ | $0.230\text{ m}$ | $-22.82\%$ (Co ngắn) | Phồng bụng cơ $k = 1.139$ |
| `FJ1477` | Triceps brachii (Đầu ngoài) | `upperarm_r` | `lowerarm_r` (Mỏm khuỷu) | $0.210\text{ m}$ | $0.252\text{ m}$ | $+20.00\%$ (Giãn dài) | Căng bề mặt sau khuỷu |
| `FJ1479` | Triceps brachii (Đầu dài) | `upperarm_r` | `lowerarm_r` (Mỏm khuỷu) | $0.245\text{ m}$ | $0.294\text{ m}$ | $+20.00\%$ (Giãn dài) | Căng bề mặt sau khuỷu |
| `FJ1480` | Triceps brachii (Đầu trong) | `upperarm_r` | `lowerarm_r` (Mỏm khuỷu) | $0.185\text{ m}$ | $0.222\text{ m}$ | $+20.00\%$ (Giãn dài) | Căng mặt trong khuỷu |
| `FJ1486` | Brachialis (Cơ cánh tay) | `upperarm_r` | `lowerarm_r` (Mỏm vẹt trụ) | $0.160\text{ m}$ | $0.125\text{ m}$ | $-21.88\%$ (Co ngắn) | Co sâu nâng cẳng tay |

---

## 2. NGUYÊN LÝ BẢO TOÀN THỂ TÍCH ĐẲNG TÍCH (ISOVOLUMETRIC BULGING)

1. **Sinh lý học cơ bắp:** Cơ bắp sinh học chủ yếu gồm nước và các bó sợi cơ actin-myosin không nén được ($V = \text{const}$). Khi chiều dài cơ $L$ co ngắn lại dọc theo trục cơ, tiết diện ngang $A$ buộc phải mở rộng tương ứng:
   $$V = A \cdot L = \text{const} \implies \frac{A_{\text{curr}}}{A_{\text{rest}}} = \frac{L_{\text{rest}}}{L_{\text{curr}}}$$
2. **Hệ số phồng bán kính (Radial Bulge Factor $k_{\text{bulge}}$):**
   $$k_{\text{bulge}} = \sqrt{\frac{L_{\text{rest}}}{L_{\text{curr}}}}$$
   - Tại góc gập khuỷu $0^\circ$: $k_{\text{bulge}} = 1.000$ (Trạng thái nghỉ, không phồng).
   - Tại góc gập khuỷu $45^\circ$: $k_{\text{bulge}} = 1.065$ (Phồng nhẹ 6.5%).
   - Tại góc gập khuỷu $90^\circ$: $k_{\text{bulge}} = 1.141$ (Bụng cơ nhị đầu phồng $14.1\%$).

---

## 3. KỸ THUẬT KẾT HỢP DUAL-BONE SKINNING VÀ MORPH TARGET (SHAPE KEY)

Trong tệp tài sản 3D `rigged_arm_anatomy_v12.glb`:
- **Dual-Bone Skinning:** Cơ bắp được gán trọng số pha trộn (gradient weight blending) giữa `upperarm_r` và `lowerarm_r`. Khi cẳng tay gập lên, phần bám tận di chuyển theo xương quay và xương trụ, uốn cong cơ tại nếp gấp khuỷu một cách tự nhiên.
- **Morph Target (`Biceps_Bulge`):** Một Shape Key chuyên biệt di chuyển các đỉnh ở bụng cơ theo hướng pháp tuyến (surface normal vector $\vec{n}$). Ảnh hưởng của Shape Key (`morphTargetInfluences[0]`) được điều biến động học theo góc gập khuỷu từ $0.0 \to 1.0$.
- Phối hợp hai kỹ thuật giúp triệt tiêu hoàn toàn hiện tượng kẹo cao su ("candy-wrapper artifact") thường gặp khi chỉ dùng rig xương thuần túy.
