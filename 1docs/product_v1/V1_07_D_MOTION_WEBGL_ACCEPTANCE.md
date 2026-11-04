# BÁO CÁO NGHIỆM THU GÓI D: CHUYỂN ĐỘNG WEBGL & ĐIỀU KHIỂN CHUỘT (WEB MOTION & MOUSE POSE)
## MSK-Therapy-OS · Product V1.0 Release Candidate

**Ngày thực hiện:** 03/11/2026  
**Phạm vi:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái pháp lý / y khoa:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`

---

### 1. Giải Quyết Triệt Để Rào Cản WEB_MOTION_GEOMETRY_NOT_CONNECTED
Trong các giai đoạn P31–P37, khung nhìn Web Atlas Three.js gặp lỗi kiến trúc `WEB_MOTION_GEOMETRY_NOT_CONNECTED`: các lưới xương 3D được gắn phẳng vào một nhóm tĩnh, khiến khi người dùng kéo thanh trượt chuyển động hoặc phát lại chuỗi 100 khung hình MediaPipe, chỉ có số đo góc trên giao diện thay đổi còn mô hình 3D đứng yên.

**Giải pháp công nghệ trong V1.0:**
1. **Phân cấp động học liên kết (Hierarchical Kinematic Rigging):**
   Xây dựng cây nhóm khớp Three.js chính xác:
   $$\text{armRootGroup} \longrightarrow \text{scapulaGroup} \longrightarrow \text{upperArmGroup} \longrightarrow \text{forearmGroup} \longrightarrow \text{handGroup}$$
2. **Gắn kết Mesh BodyParts3D thật:**
   - Xương đòn (`FJ3362`) & Xương bả vai (`FJ3384`): gắn vào `scapulaGroup`.
   - Xương cánh tay (`FJ3368`): gắn vào `upperArmGroup`.
   - Xương quay (`FJ3349`) & Xương trụ (`FJ3391`): gắn vào `forearmGroup`.
   - Xương đốt bàn tay II (`FJ3352`): gắn vào `handGroup`.
3. **Cơ chế nhịp vận động Inman 2:1 (Scapulohumeral Rhythm Constraint):**
   Khi góc nâng vai toàn phần $\theta$ thay đổi:
   - Xương bả vai nâng góc: $\theta_{\text{scapula}} = \dfrac{\theta}{3}$
   - Xương cánh tay nâng góc: $\theta_{\text{glenohumeral}} = \dfrac{2\theta}{3}$
   - Khớp khuỷu gập góc: $\phi_{\text{elbow}}$ theo trục X cục bộ.
4. **Cập nhật mốc huyệt thời gian thực:**
   - Mốc Kiên Ngung (`LI15`) bám theo mỏm cùng vai trên `scapulaGroup`.
   - Mốc Tí Nhu (`LI14`) bám theo bờ ngoài lồi củ delta trên `upperArmGroup`.
   - Mốc Hợp Cốc (`LI4`) bám theo xương đốt bàn II trên `handGroup`.
   - Đường kinh nối 3D cập nhật liên tục tọa độ thế giới mỗi frame.

**Kết quả xác thực:** Trạng thái HUD chuyển sang màu xanh lá:  
`🟢 Trạng thái: WEB_MOTION_GEOMETRY_CONNECTED`  
Toàn bộ chuỗi xương và mốc huyệt di chuyển trơn tru trên WebGL canvas.

---

### 2. Bộ Điều Khiển Tạo Dáng Chuột Trực Tiếp (Interactive Mouse Pose)
- Bổ sung tab chuyển đổi nhanh: `[🎬 Video (100f)]` $\longleftrightarrow$ `[🖐️ Mouse Pose]`.
- 2 thanh trượt điều khiển:
  - Nâng vai bằng chuột: $0^\circ \to 120^\circ$.
  - Gập khuỷu bằng chuột: $0^\circ \to 130^\circ$.
  - Nút khôi phục tư thế gốc (`0°`).
- Phản hồi tức thời với độ trễ $< 16\text{ ms}$ (đạt tốc độ 60 FPS).

---

### 3. Kết Luận Gói D
- **G1 Functional Acceptance:** `PASS`
- **G2 Data Integrity:** `PASS`
- **G3 Domain Validity:** `PENDING`
- **G4 Independent Engineering Acceptance:** `PASS`
