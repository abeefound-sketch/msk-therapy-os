# P37: ANATOMICAL AND ACUPUNCTURE REVIEWER PACKET
**MSK-Therapy-OS | Milestone P37: Research Release Consolidation**

---

## 1. MỤC ĐÍCH VÀ PHẠM VI HỒ SƠ THẨM ĐỊNH (PURPOSE & SCOPE)

Hồ sơ này được chuẩn bị dành riêng cho các **Chuyên Gia Giải Phẫu Học (Anatomists)**, **Bác Sĩ Y Học Cổ Truyền / Châm Cứu (Licensed Acupuncturists)**, và **Kỹ Sư Cơ Sinh Học (Biomechanists)** nhằm độc lập thẩm định, đánh giá và quyết định tính hợp lệ lâm sàng (Domain Validity — Gate G3) của các mốc giải phẫu và huyệt vị trên hệ thống MSK-Therapy-OS.

> [!IMPORTANT]
> **Ranh Giới Thẩm Quyền Phê Duyệt:**  
> Coding Agent và Đội ngũ phát triển phần mềm **TUYỆT ĐỐI KHÔNG ĐƯỢC PHÉP TỰ KÝ DUYỆT** tính chính xác giải phẫu hoặc lâm sàng. Mọi mốc trong gói phát hành hiện tại được gắn nhãn mặc định là:  
> `EXPERT_REVIEW_PENDING`.

---

## 2. DANH MỤC MỐC GIẢI PHẪU VÀ HUYỆT VỊ CẦN THẨM ĐỊNH

### A. Huyệt Hợp Cốc (LI4 — Hegu)
- **Tên La-tinh / TA2:** *Musculus interosseus dorsalis primus / Ossa metacarpalia I-II*
- **Định danh ontology:** FMA:23910 (Xương đốt bàn tay II), FMA:37385 (Cơ gian cốt mu tay I)
- **Chuẩn y văn tham chiếu:**  
  - *WHO Standard Acupuncture Point Locations in the Western Pacific Region (2008), tr. 33, 57:*  
    "On the dorsum of the hand, radial to the midpoint of the second metacarpal bone."
  - *GB/T 12346-2021 (Tiêu chuẩn Quốc gia CHND Trung Hoa), Mục 6.2.*
- **Mesh giải phẫu được gắn:** `Metacarpal_2_R` (`FJ3352`, CC BY 4.0 DBCLS Japan).
- **Mã băm dữ liệu mesh:** `23c39f4eb1ff3ffc0ff314ae1938507851390499ba5d3989cf8bdfa3754e60fa`
- **Tọa độ bề mặt cục bộ (Mét):** $(-0.280000, 0.835000, 0.035000)$
- **Vector pháp tuyến bề mặt:** $(-0.700000, 0.000000, 0.700000)$
- **Tọa độ trọng tâm (Barycentric):** $u=0.50, v=0.50, w=0.00$
- **Ranh giới an toàn:** Chống chỉ định phụ nữ mang thai (nguy cơ co bóp tử cung).

---

### B. Huyệt Túc Tam Lý (ST36 — Zusanli)
- **Tên La-tinh / TA2:** *Margo anterior tibiae / Musculus tibialis anterior*
- **Định danh ontology:** FMA:24477 (Xương chày), FMA:45155 (Cơ cày trước)
- **Chuẩn y văn tham chiếu:**  
  - *WHO Standard Acupuncture Point Locations (2008), tr. 69, 75:*  
    "Anterior region of leg, 3 B-cun inferior to ST35, one finger-breadth lateral to anterior crest of tibia."
  - *GB/T 12346-2021, Mục 6.3.*
- **Mesh giải phẫu được trích xuất:** `Tibia_R` (`FJ3387`, CC BY 4.0 DBCLS Japan).
- **Mã băm dữ liệu mesh:** `2fe1e44d01ad47a4ba7ff0a653bb1e5c464b55e37ca98bb55f41aa8ce04a0808`
- **Trạng thái hiện tại:** `ASSET_EXTRACTED` (Chờ tích hợp vào Rig chi dưới).

---

### C. Huyệt Thái Khê (KI3 — Taixi)
- **Tên La-tinh / TA2:** *Sulcus malleolaris / Tendo calcaneus*
- **Định danh ontology:** FMA:24497 (Xương gót), FMA:51111 (Gân gót / Achilles)
- **Chuẩn y văn tham chiếu:**  
  - *WHO Standard Acupuncture Point Locations (2008), tr. 112, 138:*  
    "Posteromedial region of ankle, in the depression between prominence of medial malleolus and calcaneal tendon."
  - *GB/T 12346-2021, Mục 6.8.*
- **Mesh giải phẫu được trích xuất:** `Calcaneus_R` (`FJ3360`, CC BY 4.0 DBCLS Japan).
- **Mã băm dữ liệu mesh:** `5db839d328652d8b1aa6a56e5dfc929a7566b6c507c5aa3f37b7ca2c5025a153`
- **Trạng thái hiện tại:** `ASSET_EXTRACTED` (Chờ tích hợp vào Rig chi dưới).

---

## 3. PHIẾU NGHIỆM THU CHUYÊN GIA ĐỘC LẬP (EXPERT REVIEW & SIGN-OFF FORM)

```
================================================================================
CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM / QUỐC TẾ
BIÊN BẢN ĐÁNH GIÁ VÀ THẨM ĐỊNH GIẢI PHẪU HỌC & Y HỌC CỔ TRUYỀN (GATE G3)
================================================================================

1. THÔNG TIN CHUYÊN GIA THẨM ĐỊNH (EXPERT REVIEWER CREDENTIALS):
   Họ và tên: ................................................................
   Học hàm, học vị: ..........................................................
   Chuyên khoa: [ ] Giải Phẫu Học  [ ] Châm Cứu & YHCT  [ ] Cơ Sinh Học
   Cơ quan công tác: .........................................................
   Số chứng chỉ hành nghề / ORCID ID: .......................................
   Email xác thực: ...........................................................

2. HỒ SƠ BẰNG CHỨNG ĐÃ KIỂM TRA:
   [ ] Tệp Blender: 1docs/audits/P35/evidence/p35_full_limb_binding.blend
   [ ] Ảnh tư thế: p35_blender_render_frame_001.png, 050.png, 100.png
   [ ] Tọa độ bề mặt và độ trôi hình học: < 0.0002 mm (0.2 micromet)
   [ ] Đối chiếu y văn WHO 2008 và GB/T 12346-2021

3. KẾT LUẬN VÀ QUYẾT ĐỊNH THẨM ĐỊNH (CHỌN MỘT):
   [ ] CHẤP THUẬN (APPROVED) — Vị trí mốc hình học phản ánh đúng giải phẫu quy chuẩn.
   [ ] YÊU CẦU ĐIỀU CHỈNH (REVISION REQUIRED) — Cần dịch chuyển tọa độ mốc.
   [ ] TỪ CHỐI (REJECTED) — Mô hình hình học không đáp ứng tiêu chuẩn chuyên môn.

4. Ý KIẾN CHUYÊN MÔN VÀ LÝ GIẢI (CLINICAL RATIONALE):
   ...........................................................................
   ...........................................................................

5. CHỮ KÝ VÀ NGÀY KÝ:
   Ngày ký: ..... / ..... / 202...
   Chữ ký chuyên gia: ........................................................
================================================================================
```

---

## 4. DANH MỤC THÔNG TIN ĐẦU VÀO TỐI THIỂU ĐỂ GỠ BLOCK G3

Để chuyển trạng thái từ `EXPERT_REVIEW_PENDING` sang `APPROVED`, quy trình yêu cầu tối thiểu:
1. Xác nhận độc lập của ít nhất **01 Bác sĩ Châm cứu / Giảng viên Giải phẫu** có chứng chỉ hành nghề hoặc học vị Tiến sĩ.
2. Kiểm tra trực quan trên mô hình 3D (Blender Viewport hoặc 3D Print tương đương).
3. Đánh giá sai số độ dày mô mềm (STA - Soft Tissue Artifact): Xác nhận khoảng cách sai số chấp nhận được trong lâm sàng ($\pm 5.0\text{ mm}$ đối với LI4 theo WHO 2008).
