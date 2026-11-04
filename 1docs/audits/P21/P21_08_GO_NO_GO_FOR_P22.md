# MSK-Therapy-OS — Milestone P21 Executive Decision
## P21_08: Formal GO / NO-GO Decision for Milestone P22

**Tài liệu ID:** `MSK-P21-AUD-008`  
**Ngày thực hiện:** 2026-11-01  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  
**Quyết định Toàn Cục:** $$\mathbf{CONDITIONAL\_GO}$$ (ĐỦ ĐIỀU KIỆN TIẾN HÀNH P22 KÈM ĐIỀU KIỆN RÀNG BUỘC)  

---

### 1. Cơ sở Đưa ra Quyết định (Decision Rationale)

Milestone P21 đã hoàn thành xuất sắc mục tiêu kỹ thuật cốt lõi được giao:
1. **Đã giải quyết triệt để vấn đề "Anatomy Giả":** Đã kiểm định, tích hợp và chạy thành công pipeline giải phẫu 3D thật **BodyParts3D Release 4.0** (DBCLS Nhật Bản, CC BY 4.0), chứa **2,234 cấu trúc giải phẫu**, phân lớp rành mạch: Xương (296), Cơ (402), Nội tạng (249 tạng chính), Da (FJ2810 toàn thân).
2. **Đã bàn giao PoC tương tác hoàn chỉnh:** Khởi chạy độc lập tại `/sandbox/p21/`, cho phép ẩn/hiện từng lớp, raycasting bắt dính bề mặt cấu trúc, đánh dấu huyệt thủ công (`USER_ANNOTATED_UNVERIFIED`), vẽ tuyến đường kinh đa điểm (hỗ trợ hoàn tác Undo), lưu trữ và xuất Markdown tương thích 100% với Knowledge Vault P20.
3. **Bảo toàn ranh giới an toàn tuyệt đối:** Toàn bộ hệ thống Atlas cũ tại `/atlas/` và Education Studio tại `/education/` được giữ nguyên vẹn 100%, không bị xâm lấn hay xung đột mã nguồn. Toàn bộ 34 bài kiểm thử tự động P19–P21 đều vượt qua (100% PASS).
4. **Không ngộ nhận pháp lý và học thuật:** Đã nhận diện rủi ro copyleft của Z-Anatomy (CC BY-SA 4.0), minh bạch hóa trạng thái Cổng G3/G4 là `PENDING`, và cấm tuyệt đối việc tự phong danh hiệu phê duyệt lâm sàng.

Do đó, hệ thống đủ điều kiện kỹ thuật để chuyển sang **Milestone P22 (Anatomical Registration & Acupoint Resolver Architecture)**.

---

### 2. Các Điều Kiện Tiên Quyết Bắt Buộc cho P22 (Binding Conditions)

Để bước vào P22 một cách an toàn và chuẩn mực khoa học, đội ngũ phát triển bắt buộc phải tuân thủ 5 điều kiện sau:

#### Điều kiện 1: Cấm tái kích hoạt các công thức nội suy tọa độ cũ
Không được tiếp tục chỉnh sửa hay "chắp vá" các công thức giải tọa độ huyệt kiểu cũ (heuristic/procedural bounding box) đã bị vạch trần xung đột nghiêm trọng ở P19. Mọi thuật toán ánh xạ huyệt trong P22 phải được xây dựng lại dựa trên mốc giải phẫu thực tế (Anatomical Landmarks) của khung xương và hệ cơ BodyParts3D.

#### Điều kiện 2: Thiết lập Bộ Tham Chiếu Thẩm Định Chuyên Biệt cho LI4, ST36, KI3
Trước khi lập trình bộ giải tọa độ P22, bắt buộc phải định nghĩa bộ tiêu chí giải phẫu cụ thể cho 3 huyệt mốc:
- **LI4 (Hợp Cốc):** Phải gắn kết trên mặt phẳng giải phẫu bờ quay xương bàn tay II (Radial aspect of 2nd metacarpal bone) hoặc cơ gian cốt mu tay I (1st dorsal interosseous muscle), không được trôi dạt ra ngoài không gian bàn tay.
- **ST36 (Túc Tam Lý):** Phải gắn kết tại bờ ngoài lồi củ chày 1 khoát ngón tay, trên thân cơ cẳng chân trước (Tibialis anterior muscle) ở cẳng chân T/P.
- **KI3 (Thái Khê):** Phải gắn kết tại chỗ lõm giữa đỉnh mắt cá trong (Medial malleolus) và bờ trong gân gót (Achilles tendon).
*Lưu ý cốt tử:* **Độ lệch $< 15\text{ mm}$ với một điểm máy móc KHÔNG được xem là bằng chứng huyệt học.** Bắt buộc phải có reviewer chuyên môn y học cổ truyền thẩm định.

#### Điều kiện 3: Giữ nguyên Core Hình học BodyParts3D 4.0
Tiếp tục sử dụng dữ liệu 2,234 cấu trúc BodyParts3D 4.0 đã kiểm chứng làm hệ tọa độ cơ sở (Canonical Reference Frame). Không đổi sang các mô hình chưa rõ nguồn gốc hoặc có giấy phép copyleft (như Z-Anatomy CC BY-SA 4.0).

#### Điều kiện 4: Duy trì Sandbox Cách ly cho đến khi Hoàn tất Kiểm thử
Mọi cải tiến của P22 phải tiếp tục được thử nghiệm trong không gian sandbox hoặc nhánh phát triển có kiểm soát, chỉ hợp nhất vào production khi đã có biên bản nghiệm thu độc lập.

#### Điều kiện 5: Bảo lưu Phạm vi Nghiên cứu (Research-Only)
Mã nguồn và báo cáo P22 tiếp tục mang nhãn `RELEASE_SCOPE = "ENGINEERING_RESEARCH_ONLY"`, không phục vụ mục đích chẩn đoán hay điều trị y tế trực tiếp trên người bệnh.

---

### 3. Lộ trình Kỹ thuật Đề xuất cho P22 (Roadmap Outlook)

```text
+-----------------------------------------------------------------------------------+
| MILESTONE P21 (ĐÃ HOÀN THÀNH)                                                     |
| - Xác nhận nguồn giải phẫu thật: BodyParts3D 4.0 (CC BY 4.0, 2,234 meshes).      |
| - Hoàn thành PoC tương tác 4 lớp: Xương, Cơ, Tạng, Da + Đánh dấu huyệt + Vẽ tuyến.|
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| MILESTONE P22 (CONDITIONAL GO)                                                    |
| - Xây dựng bộ giải phẫu mốc chuẩn (Landmark Surface Anchor Engine).              |
| - Thiết lập hợp đồng mốc xương/cơ cho LI4, ST36, KI3 với sự tham vấn chuyên gia.  |
| - Thuật toán gắn kết bề mặt (Barycentric + Normal Projection) trên mesh thật.    |
| - Tích hợp bộ giải mới vào Knowledge Vault P20 để kiểm chứng độ tái lập.          |
+-----------------------------------------------------------------------------------+
```

---

### 4. Kết luận Lãnh đạo Kỹ thuật (Sign-off)

- **Trạng thái P21:** `ENGINEERING_PASS_SCOPE_LIMITED`  
- **Quyết định:** **`CONDITIONAL_GO`** cho P22.  
- **Ủy quyền:** Đội ngũ phát triển được phép tiến hành lập kế hoạch chi tiết cho P22 theo đúng 5 điều kiện ràng buộc nêu trên, không tự ý đẩy mã nguồn lên nhánh chính (main/production) khi chưa có sự phê duyệt chính thức.
