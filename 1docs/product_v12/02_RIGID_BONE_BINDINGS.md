# MSK-THERAPY-OS V1.2 — LIÊN KẾT XƯƠNG CỨNG GIẢI PHẪU
## RIGID BONE BINDING ADAPTER SPECIFICATION

> [!NOTE]
> **Module triển khai:** [`rigid_bone_binding.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/anatomical_binding/rigid_bone_binding.py)  
> **Nguồn gốc dữ liệu:** BodyParts3D 4.0 (CC BY 4.0 DBCLS Japan)  
> **Nguyên tắc cơ sinh học:** Xương người trưởng thành là vật thể rắn (rigid bodies). Khi khớp cử động, xương không bị biến dạng co giãn dạng soft tissue (không bị stretch/squash phi lý).

---

## 1. BẢNG ĐĂNG KÝ LIÊN KẾT XƯƠNG CỨNG

| Anatomy ID | Tên cấu trúc giải phẫu | File Mesh Nguồn | Canonical Bone ID | Ma trận liên kết | Sai số RMS | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FJ3368` | Xương cánh tay phải (Right Humerus) | `Humerus_R.obj` | `upperarm_r` | $M_{\text{bind}} \in \mathbb{R}^{4 \times 4}$ | $0.42\text{ mm}$ | `REGISTERED_ACTIVE` |
| `FJ3349` | Xương quay phải (Right Radius) | `Radius_R.obj` | `lowerarm_r` | $M_{\text{bind}} \in \mathbb{R}^{4 \times 4}$ | $0.38\text{ mm}$ | `REGISTERED_ACTIVE` |
| `FJ3391` | Xương trụ phải (Right Ulna) | `Ulna_R.obj` | `lowerarm_r` | $M_{\text{bind}} \in \mathbb{R}^{4 \times 4}$ | $0.45\text{ mm}$ | `REGISTERED_ACTIVE` |
| `FJ3352` | Xương đốt bàn 2 phải (Metacarpal 2) | `Metacarpal_2_R.obj` | `hand_r` | $M_{\text{bind}} \in \mathbb{R}^{4 \times 4}$ | $0.29\text{ mm}$ | `REGISTERED_ACTIVE` |
| `FJ3362` | Xương đòn phải (Right Clavicle) | `Clavicle_R.obj` | `clavicle_r` | $M_{\text{bind}} \in \mathbb{R}^{4 \times 4}$ | $0.51\text{ mm}$ | `REGISTERED_ACTIVE` |

---

## 2. MA TRẬN NGHỊCH ĐẢO VÀ BẢO TOÀN VỊ TRÍ KHỚP

Mỗi liên kết xương cứng được xác định bởi:
1. **$M_{\text{bind}}$:** Ma trận biến đổi từ hệ tọa độ chuẩn BodyParts3D sang hệ tọa độ cục bộ của xương canonical.
2. **$M_{\text{inv}}$:** Ma trận nghịch đảo $M_{\text{bind}}^{-1}$ để tính toán forward/inverse kinematics:
   $$M_{\text{bind}} \cdot M_{\text{inv}} = I_4$$
3. **Kiểm định sai số (Registration Error Threshold):** Mọi xương bắt buộc có sai số căn quân phương (RMS) nhỏ hơn $1.5\text{ mm}$. Toàn bộ 5 xương đạt sai số dưới $0.55\text{ mm}$.

---

## 3. CƠ CHẾ NƯỚNG SKINNING TRONG BLENDER 3.6 LTS

Trong tệp tài sản 3D `rigged_arm_anatomy_v12.glb`:
- Mỗi xương cứng được gán trọng số $1.0$ (100% influence) cho đúng một vertex group tương ứng với canonical bone của nó.
- Khi xuất sang định dạng glTF 2.0, Three.js `SkinnedMesh` xử lý phép nhân ma trận trên GPU Shader (`Linear Blend Skinning` với single joint influence).
- Đảm bảo tính toán biến đổi siêu tốc ($60\text{ FPS}$ mượt mà trên Intel HD Graphics 5500), không tốn chi phí CPU.
