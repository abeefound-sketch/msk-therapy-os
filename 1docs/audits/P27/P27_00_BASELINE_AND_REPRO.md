# MSK-Therapy-OS — Milestone P27 Audit
## P27_00: Independent Engineering Reality Check & Baseline Verification
### Forensic Reality Check · Code vs Claims Audit · Mesh Licensing · Rig-Mesh Binding · Knowledge Vault Lineage

**Tài liệu ID:** `MSK-P27-AUD-000-BASELINE`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Kiểm toán viên:** Independent Engineering & Forensic Verification Lead  
**Trạng thái Cổng:** G1: **PASS** | G2: **PASS** | G3: **BLOCKED** | G4: **BLOCKED**  
**Quyết định Điều hành:** $$\mathbf{CONDITIONAL\_GO\_FOR\_P28}$$

---

### 1. Hiện trạng Git HEAD và Môi trường Thực thi (Baseline Environment)

| Thông số | Giá trị Đo đạc Thực tế | Ghi chú Thẩm định |
|---|---|---|
| **Git Working Directory** | `D:\5Projects\msk-therapy-os` | Không gian làm việc chính thức |
| **Git Branch** | `fix/p18-meridian-anatomical-geometry` | Nhánh kỹ thuật hiện hành |
| **Git HEAD Commit** | `4990f173a880e8a671c0622a04dd88c67264679c` | `fix(p18): remediate anatomical geometry divergence` |
| **Working Tree State** | DIRTY (Uncommitted modifications in P17 screenshots, incident_log, server.py, coordinate_registry; untracked P19–P26 modules) | Bảo toàn 100% dữ liệu, không reset/clean |
| **Hệ điều hành** | Windows 11 64-bit | Local environment |
| **Bộ xử lý (CPU)** | Intel(R) Core(TM) i7-5600U @ 2.60GHz (2 cores, 4 threads) | Giới hạn tài nguyên phần cứng |
| **Bộ nhớ đồ họa (GPU)** | Intel(R) HD Graphics 5500 | Không có GPU rời / Không hỗ trợ CUDA |
| **Bộ nhớ hệ thống (RAM)** | 7.89 GB Physical Memory | Giới hạn dung lượng mô hình lớn |
| **Blender Runtime** | Blender 3.6.5 LTS (Release hash `cf1e1ed46b7e`) | `C:\Program Files\Blender Foundation\Blender 3.6\blender.exe` |
| **Python Runtime** | Python 3.11.9 (System) | `C:\Users\tuanh\AppData\Local\Programs\Python\Python311\python.exe` |

---

### 2. Bảng Đối Chiếu Hiện Thực: Tuyên Bố P21–P26 (Claims) vs Thực Tế Mã Nguồn & Runtime (Reality)

Báo cáo kiểm toán độc lập này rà soát chi tiết toàn bộ các tuyên bố PASS từ giai đoạn P21–P26 dựa trên bằng chứng vật lý, mã nguồn, tệp tin nhị phân và môi trường thực nghiệm.

| Cột mốc | Tuyên bố trước đó (Claimed) | Thực tế phát hiện qua mã nguồn & runtime (Reality Check) | Mức độ Sai lệch / Rủi ro | Phán quyết Kỹ thuật |
|---|---|---|---|---|
| **P21** | Nạp mô hình giải phẫu thật và đặt 3 mốc huyệt `LI4`, `ST36`, `KI3` bám bề mặt xương. | Mesh nạp là `shoulder_skeleton.glb` (chỉ có xương đòn `Clavicle_R`, xương bả vai `Scapula_R`, xương cánh tay `Humerus_R`). **Hoàn toàn không có xương cẳng tay và bàn tay.**<br>Do đó:<br>- `LI4` (Hợp cốc - thuộc bàn tay giữa xương bàn ngón 1 & 2) bị ép gán vào `Humerus_R` (xương cánh tay).<br>- `ST36` (Túc tam lý - thuộc cẳng chân dưới xương bánh chè) bị ép gán vào `Scapula_R` (xương bả vai).<br>- `KI3` (Thái khê - thuộc mắt cá trong cổ chân) bị ép gán vào `Clavicle_R` (xương đòn). | **RẤT CAO** (Giải phẫu bị gán sai vị trí xương thực tế để phục vụ demo hình học). | **MOCK_SURFACE_PROXY_ONLY**<br>Chỉ đạt giá trị kiểm thử thuật toán raycast/barycentric, hoàn toàn không có giá trị giải phẫu học thật. |
| **P22** | Chuẩn hóa hệ quy chiếu và truy vết phả hệ y văn cho `LI4`, `ST36`, `KI3`. | Tọa độ canonical trong `CoordinateRegistry` là các hằng số lý thuyết phỏng đoán, chưa có thẩm định chuyên gia trên mesh BodyParts3D thực. Sai số lâm sàng thực tế $\pm 5.0\text{ mm}$ đến $\pm 10.0\text{ mm}$ vẫn tồn tại. | **TRUNG BÌNH** (Đã ghi nhãn `EXPERT_REVIEW_PENDING` nhưng chưa có dữ liệu đo đạc trực tiếp trên xác hoặc MRI). | **THEORETICAL_REGISTRY_PASS**<br>Đạt tiêu chuẩn engineering contract; G3 Domain Validity vẫn giữ `BLOCKED`. |
| **P23** | Armature cánh tay có IK và giới hạn góc Kapandji, cử động cùng dữ liệu CMU Mocap / OpenSim. | Armature `Armature_UpperLimb_R` được tạo độc lập trong collection `MSK_Rigs`. **Các mesh xương (`Humerus_R`, `Clavicle_R`, `Scapula_R`) hoàn toàn CHƯA được gán Armature Modifier hoặc chia nhóm đỉnh (Vertex Groups / Skinning Weights) vào xương của Armature.**<br>Khi Armature xoay keyframe trong timeline, **chỉ có khung xương rig di chuyển, các mô hình xương giải phẫu đứng yên 100% tại chỗ.** | **NGHIÊM TRỌNG** (Chuyển động của Armature không kéo theo chuyển động của mô hình xương/cơ/da hay huyệt). | **RIG_STANDALONE_ONLY**<br>Chưa có Skinning / Deform Binding giữa Mesh và Bones. |
| **P24** | Nhận diện tư thế MediaPipe từ video, tái cấu trúc động học qua IK và ma trận khả năng quan sát. | Thư viện `mediapipe` và `cv2` **CHƯA ĐƯỢC CÀI ĐẶT** trong Python hệ thống (`ModuleNotFoundError`). Bộ kiểm thử P24 chỉ chạy trên các vector tọa độ giả lập số học do tác giả gõ tay trong mã kiểm thử (`(0.0, 1.42, 0.0)`, `(0.0, 1.12, 0.0)`). Chưa từng có một tệp video thật nào được trích xuất frame hoặc chạy qua mạng nơ-ron MediaPipe. | **RẤT CAO** (Toàn bộ pipeline P24 trước đó là tính toán hình học thuần túy trên dữ liệu tổng hợp, không phải MediaPipe runtime thật). | **SYNTHETIC_STUB_ONLY**<br>Cần triển khai môi trường độc lập và chạy video thực tế ở P28. |
| **P25** | Tích hợp Knowledge Vault không tạo DB thứ hai, tra cứu chéo claims và citations cho huyệt và khớp. | `StudioKnowledgeBridge` trỏ mặc định vào `msk_therapy_os.sqlite3`. Bảng `documents`, `claims`, `citations` trong database này có **0 dòng dữ liệu** (trống rỗng). Dữ liệu P20 thực tế nằm ở `knowledge_vault/vault.db` (12 documents, 13 claims). Ngoài ra, cả hai database đều **hoàn toàn không có claim nào cho `LI4`, `ST36`, `KI3`**. Toàn bộ kết quả tra cứu được sinh ra từ các hằng số hardcode trong `CoordinateRegistry`, mảng `claims` trả về rỗng `[]`. | **TRUNG BÌNH - CAO** (Phân mảnh dữ liệu giữa 2 tệp SQLite, thông tin y văn chưa được nạp vào DB). | **DECOUPLED_BRIDGE_PASS**<br>Bridge hoạt động về mặt giao diện lập trình nhưng chưa có dữ liệu y văn thực sự cho các huyệt mẫu. |
| **P26** | Giao thức nghiên cứu nhân trắc học tỷ lệ chi, phân tích STA và biến thiên BMI. | Đã xác lập đúng ranh giới đạo đức (zero PHI), giới hạn thống kê (Limits of Agreement, Bland-Altman) và gắn nhãn fail-closed. Không có hành vi tự phong chứng nhận lâm sàng. | **THẤP** (Đúng chuẩn mực an toàn). | **RESEARCH_GOVERNANCE_PASS**<br>G3: BLOCKED, G4: BLOCKED đúng nguyên tắc. |

---

### 3. Kiểm toán Giấy phép Mô hình 3D (Mesh Licensing Forensics)

| Mesh Asset | Đường dẫn Lưu trữ | Định dạng / Kích thước | Nguồn gốc Thượng nguồn | Giấy phép Khai báo | Phân tích Rủi ro Pháp lý | Quyết định Kiểm toán |
|---|---|---|---|---|---|---|
| `shoulder_skeleton.glb` | `msk_therapy_os/static/education/models/` | GLB (1.98 MB) | BodyParts3D 4.0 / Open Anatomy Atlas | CC BY 4.0 International | Yêu cầu ghi công DBCLS Japan. Không chứa điều khoản ShareAlike (copyleft). Không cấm thương mại. | **ACCEPTED_FOR_STUDIO** |
| `anatomy.glb` | `msk_therapy_os/static/education/models/` | GLB (1.28 MB) | Phân đoạn cơ học giải phẫu WaterCMY | MIT Code / CC BY 4.0 Assets | Cần ghi rõ quyền tác giả WaterCMY và liên kết BodyParts3D. | **ACCEPTED_FOR_STUDIO** |
| `body.glb` | `3refs/upstream/tcm-acupoints/` | GLB Draco (1.1 MB) | Z-Anatomy (v1.0 snapshot) | **CC BY-SA 4.0** | Rủi ro Copyleft lan truyền (Viral ShareAlike). Nếu đóng gói cùng phần mềm độc quyền sẽ buộc toàn bộ sản phẩm phải mở mã nguồn. | **STRICTLY_QUARANTINED** (Cấm đưa vào gói bundle chính thức) |

---

### 4. Kiểm toán Hệ Tọa Độ và Liên Kết Rig–Anatomy

#### 4.1. Hệ quy chiếu không gian (Spatial Coordinate System)
- Hệ quy chiếu được chốt: `CANONICAL_BODYPARTS3D_FRAME` (Đơn vị: mét, Chiều cao: $+Y$ up, Ngang: $+X$ right-lateral, Sâu: $+Z$ anterior).
- Khác biệt với Blender 3.6 mặc định: Blender sử dụng $+Z$ up, $+Y$ depth, $+X$ lateral.
- Ma trận chuyển đổi đồng nhất từ Blender sang BodyParts3D:
  $$\mathbf{T}_{\text{Blender} \to \text{BP3D}} = \begin{bmatrix} 1 & 0 & 0 & 0 \\ 0 & 0 & 1 & 0 \\ 0 & -1 & 0 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}$$
- Đã kiểm tra tính khả nghịch và sai số hoàn nguyên số học: $\Delta < 10^{-12}\text{ m}$.

#### 4.2. Khuyết tật Liên kết Rig và Mesh (Armature-to-Mesh Binding Gap)
- **Hiện tượng:** Trong `tools/blender_anatomy_studio/addon/rig.py`, hàm `build_upper_limb_armature()` tạo 4 xương nhưng không gán quan hệ Parent giữa các Object Mesh và Armature Bones.
- **Hệ quả thực tế:** 
  1. Khi Armature cử động (chẳng hạn gập khuỷu $90^\circ$), xương ảo di chuyển từ vị trí thẳng đứng ra phía trước.
  2. Mesh `Humerus_R` và cụm xương bả vai vẫn nằm nguyên tại tọa độ tĩnh ban đầu.
  3. Mốc huyệt `LI4` bám trên bề mặt mesh `Humerus_R` không di chuyển theo chuyển động của cánh tay.
- **Giải pháp khắc phục bắt buộc cho P28:**
  * Bổ sung cơ chế liên kết đối tượng: Parent `Humerus_R` vào Bone `upper_arm.R` với kiểu `BONE` parenting (hoặc Armature Modifier với vertex weights).
  * Gắn mốc huyệt vào xương chuyển động thông qua local coordinate frame của Pose Bone để khi Armature quay, huyệt quay chính xác cùng xương.

---

### 5. Kiểm toán Nguồn Dữ Liệu Knowledge Vault (Data Provenance & Integrity)

1. **Hiện tượng phân mảnh cơ sở dữ liệu:**
   - Dự án hiện có hai tệp cơ sở dữ liệu chứa bảng của Knowledge Vault:
     * `msk_therapy_os.sqlite3` (1.35 MB, database chính của hệ thống, nhưng các bảng `documents` và `claims` có 0 bản ghi).
     * `knowledge_vault/vault.db` (237 KB, database độc lập của P20, chứa 12 documents và 13 claims).
2. **Khắc phục đồng bộ:**
   - Cập nhật `StudioKnowledgeBridge` để tự động nhận diện và ưu tiên trỏ vào `knowledge_vault/vault.db` nếu `msk_therapy_os.sqlite3` chưa được đồng bộ dữ liệu.
   - Bổ sung tài liệu tri thức y văn chính thức cho 3 huyệt mẫu (`LI4`, `ST36`, `KI3`) vào Vault để đảm bảo các truy vấn tra cứu không trả về mảng rỗng `claims: []`.

---

### 6. Ma Trận Nghiệm Thu Cổng G1–G4 cho P27

| Cổng Kiểm soát | Tiêu chí Đánh giá | Bằng chứng Thực nghiệm | Trạng thái |
|---|---|---|---|
| **G1: Engineering Integrity** | - Mã nguồn chạy không lỗi trên Python 3.11 và Blender 3.6.<br>- Đối chiếu 100% các tuyên bố PASS với thực tế.<br>- Chỉ ra chính xác các điểm thiếu sót, sai lệch và mock dữ liệu. | Toàn bộ 67/67 tests kế thừa PASS; tài liệu kiểm toán P27_00 vạch rõ 5 điểm khác biệt giữa tuyên bố và hiện thực. | **PASS** |
| **G2: Safety & Data Governance** | - Giữ nguyên `RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY`.<br>- Không có thông tin PII/PHI.<br>- Cách ly tài nguyên CC BY-SA khỏi bundle chính thức. | Toàn bộ quy tắc an toàn được thực thi; Z-Anatomy được đánh dấu QUARANTINED. | **PASS** |
| **G3: Domain Validity** | - Thẩm định bởi bác sĩ y học cổ truyền và chuyên gia giải phẫu học.<br>- Vị trí huyệt trên mesh phản ánh đúng giải phẫu thực. | `LI4` đang gán tạm vào xương cánh tay do thiếu mesh bàn tay; chưa có bác sĩ thẩm định. | **BLOCKED** |
| **G4: Independent Acceptance** | - Thử nghiệm lâm sàng hoặc kiểm định độc lập của bên thứ ba. | Chưa có kiểm định bên ngoài. | **BLOCKED** |

---

### 7. Quyết định Điều hành (Executive Verdict)

$$\mathbf{CONDITIONAL\_GO\_FOR\_P28}$$

**Điều kiện chuyển giai đoạn sang P28:**
1. Giữ nguyên ranh giới kỹ thuật: Thừa nhận P21–P26 chỉ đạt cấp độ mô phỏng số học (Synthetic Simulation), chưa phải pipeline MediaPipe thật và chưa có liên kết Rig–Mesh thật.
2. Triển khai ngay P28 với quy trình khép kín:
   - Chuẩn bị video chuyển động tay thực tế.
   - Cài đặt / khởi tạo môi trường Python chứa thư viện MediaPipe và OpenCV độc lập.
   - Chạy inference MediaPipe thật trích xuất tọa độ 33 mốc không gian theo từng frame.
   - Truyền chuỗi góc khớp qua `JointConstraintRegistry` (kẹp góc Kapandji $0^\circ$–$145^\circ$).
   - Kết nối trực tiếp Pose Bone với Mesh trong Blender 3.6, nạp animation và xuất file `.blend` thực.
   - Kết xuất hình ảnh/video bằng chứng thực tế chứng minh xương chuyển động cùng rig.
