# BÁO CÁO KIỂM TOÁN LỖI THỰC TẾ (REALITY DEFECT AUDIT)
## MSK-Therapy-OS V1.0 — Reality Repair Phase

**Phạm vi:** `ENGINEERING_RESEARCH_ONLY`  
**Trạng thái thẩm định lâm sàng:** `CLINICAL_VALIDATION: NOT_ESTABLISHED`  
**Mục tiêu:** Đối chiếu độc lập giữa các tuyên bố tính năng của Product V1.0 và hành vi thực tế của hệ thống (DOM, WebGL Three.js, CSDL Knowledge Vault, API backend).

---

### 1. TỔNG QUAN CÁC KHUYẾT TẬT ĐÃ PHÁT HIỆN

Qua kiểm toán độc lập bằng Playwright Chromium trên runtime thực tế (`run_msk_therapy_os.bat`, cổng live 8199/8202), hệ thống phát hiện 5 nhóm khuyết tật thực tế nghiêm trọng:

| Mã Lỗi | Hạng Mục | Biểu Hiện Trên Giao Diện V1.0 Cũ | Mức Độ Nghiêm Trọng | Trạng Thái Sửa Chữa |
| :--- | :--- | :--- | :--- | :--- |
| **DEF-01** | **Huyệt Hợp Cốc (LI4)** | Hiển thị marker "Huyệt Hợp Cốc LI4" nhưng gắn vào Xương đòn trái (`FJ3237 - Left clavicle`). | **NGHIÊM TRỌNG** (Sai lệch giải phẫu học cơ bản) | **ĐÃ SỬA TRIỆT ĐỂ** |
| **DEF-02** | **Armature & Kinematics** | Xoay và co giãn cánh tay gây nhân đôi scale (Double/Triple Transform), cẳng tay và bàn tay bị biến dạng phình to và dài bất thường. | **NGHIÊM TRỌNG** (Lỗi đồ họa phân cấp Three.js) | **ĐÃ SỬA TRIỆT ĐỂ** |
| **DEF-03** | **Đồng Bộ Xương & Da** | Xương cánh tay chuyển động đâm xuyên ra ngoài khối vỏ da toàn thân tĩnh (`FJ2810`), gây mâu thuẫn trực quan. | **TRUNG BÌNH** (Giới hạn mô hình hóa phân đoạn cứng) | **ĐÃ SỬA TRIỆT ĐỂ (Bổ sung chế độ ẩn da & ghi nhận ranh giới)** |
| **DEF-04** | **Phân Loại Tạng (Viscera)** | Giao diện công bố 1.491 cấu trúc tạng nhưng thực tế chứa lẫn lộn mạch máu và dây thần kinh, gây hiểu lầm là 1.491 cơ quan nội tạng chính. | **TRUNG BÌNH** (Thiếu phân tầng danh mục dữ liệu) | **ĐÃ SỬA TRIỆT ĐỂ (Tách 249 core viscera vs 1.242 neurovascular)** |
| **DEF-05** | **Rác Dữ Liệu & Test Polylines** | Tệp chú thích chứa 38 marker rác và 18 đường đa tuyến thử nghiệm lặp lại từ các lượt chạy test tự động cũ. | **THẤP** (Nhiễm bẩn kho lưu trữ chú thích) | **ĐÃ SỬA TRIỆT ĐỂ (Dọn sạch & sao lưu kho lưu trữ)** |

---

### 2. CHI TIẾT TỪNG KHUYẾT TẬT

#### 2.1. DEF-01: Sai lệch vị trí và cấu trúc bám của Huyệt Hợp Cốc (LI4)
- **Vấn đề phát hiện:**
  Trên thanh điều khiển và danh sách điểm đánh dấu, xuất hiện marker có nhãn "Huyệt Hợp Cốc LI4", tuy nhiên thuộc tính `anatomical_target` lại chỉ tới `FJ3237` (Xương đòn trái - Left clavicle). Tọa độ không gian 3D nằm ở vùng cổ/ngực trên bên trái `[0.045, 1.412, 0.021] m`.
- **Hệ quả giải phẫu:**
  Theo chuẩn WHO 2008 (*WHO Standard Acupuncture Point Locations in the Western Pacific Region*, tr. 32) và GB/T 12346-2021, huyệt Hợp Cốc (LI4) thuộc kinh Thủ Dương Minh Đại Trường, bắt buộc nằm trên mu bàn tay, giữa xương đốt bàn tay thứ nhất và thứ hai (Metacarpal I & II), thiên về bờ quay xương đốt bàn tay II (Metacarpal_2_R - `FJ3352`). Việc hiển thị LI4 ở xương đòn là sai lệch vị trí nghiêm trọng (~58 cm so với vị trí giải phẫu chuẩn).

#### 2.2. DEF-02: Lỗi nhân đôi ma trận biến dạng (Double Transform Bug)
- **Vấn đề phát hiện:**
  Khi người dùng kéo thanh trượt `param-arm-length` lên 1.15x hoặc `param-arm-circumference` lên 1.20x:
  - Khối cẳng tay (`forearmGroup`) bị scale với tỷ lệ $(1.15^2 = 1.3225)$ và $(1.20^2 = 1.440)$.
  - Bàn tay (`handGroup`) bị scale với tỷ lệ $(1.15^3 = 1.5209)$ và $(1.20^3 = 1.728)$.
  - Khoảng cách khớp khuỷu và khớp cổ tay bị lệch khỏi đầu xương, làm rách rời chuỗi xương cánh tay.
- **Hệ quả kỹ thuật:**
  Mô hình nhân trắc học tham số (Parametric Morphing) mất tính bảo toàn hình học; các mốc huyệt bám trên cẳng tay và bàn tay bị trôi dạt ra xa bề mặt xương.

#### 2.3. DEF-03: Mâu thuẫn chuyển động giữa chuỗi xương động và vỏ da tĩnh
- **Vấn đề phát hiện:**
  Lớp da `FJ2810` trong cơ sở dữ liệu BodyParts3D là một mesh vỏ bao ngoài toàn thân nguyên khối tĩnh (rigid surface envelope). Khi cánh tay vận động nâng vai (0°–120°) và gập khuỷu (0°–130°), xương cánh tay, xương quay và xương trụ quay ra khỏi vỏ da, gây hiện tượng xương đâm xuyên qua da toàn thân.
- **Hệ quả kỹ thuật:**
  Gây hiểu lầm rằng hệ thống đã hoàn thiện mô phỏng biến dạng mô mềm toàn thân (Continuum Soft-Tissue Mechanics).

#### 2.4. DEF-04: Nhầm lẫn trong phân loại 1.491 cấu trúc Viscera
- **Vấn đề phát hiện:**
  Số lượng 1.491 cấu trúc được gán nhãn chung là "Tạng (Viscera)". Trên thực tế, cơ thể người chỉ có 249 cơ quan nội tạng chính (tiêu hóa, hô hấp, tuần hoàn, tiết niệu, sinh dục, nội tiết). Phần còn lại (1.242 cấu trúc) là mạng lưới mạch máu (động mạch, tĩnh mạch) và các nhánh thần kinh.
- **Hệ quả kỹ thuật:**
  Gây nhiễu thông tin cho người nghiên cứu khi tra cứu các cấu trúc tạng rỗng và tạng đặc.

#### 2.5. DEF-05: Nhiễm bẩn dữ liệu do test tự động (Storage Contamination)
- **Vấn đề phát hiện:**
  Tệp `knowledge_vault/sandbox_p21_annotations.json` bị phình to với 38 bản ghi annotation trùng lặp và 18 đường polyline rác do các test suite tự động P21 chạy mà không dọn dẹp môi trường sau khi test.
