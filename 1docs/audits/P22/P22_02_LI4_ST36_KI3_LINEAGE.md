# MSK-Therapy-OS — Milestone P22 Audit
## P22_02: Academic Lineage, Anatomical Anchors & Provenance for LI4, ST36, and KI3

**Tài liệu ID:** `MSK-P22-AUD-002`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Phả hệ và Căn cứ Định vị của 3 Huyệt Mốc Cốt lõi

Hệ thống thiết lập bộ tham chiếu chuẩn mực học thuật bắt buộc cho 3 huyệt vị trọng yếu, đảm bảo tính liên kết chặt chẽ giữa Giải phẫu học Hiện đại (Terminologia Anatomica 2 / FMA) và Tiêu chuẩn Y học Cổ truyền Quốc tế (WHO Standard Acupuncture Point Locations 2008 & GB/T 12346-2021):

```text
+--------------------------------------------------------------------------------------------------+
|                                    BỘ BA HUYỆT MỐC ĐỐI CHỨNG                                     |
+------------------------------------+-----------------------------------+-------------------------+
| LI4 — HỢP CỐC (Hegu)               | ST36 — TÚC TAM LÝ (Zusanli)       | KI3 — THÁI KHÊ (Taixi)  |
| Chi trên / Bờ quay xương bàn tay II| Chi dưới / Thân cơ cẳng chân trước| Cổ chân / Lõm mắt cá trong
+------------------------------------+-----------------------------------+-------------------------+
```

---

### 2. Chi tiết Phả hệ Từng Huyệt Vị

#### A. LI4 — Hợp Cốc (Large Intestine Meridian 4)
- **Mã chuẩn:** `LI4`
- **Tên chữ Hán / Pinyin:** 合谷 / Hégǔ
- **Tọa độ Canonical chuẩn:** $[0.245, 0.892, 0.125]\text{ m}$ (Bên Phải, tư thế đứng giải phẫu)
- **Mốc bám giải phẫu (Skeletal Anchor):** Bờ quay giữa thân xương bàn tay thứ hai, bám trên cơ gian cốt mu tay thứ nhất.
- **Định danh Bản đồ Giải phẫu:**
  * `FMA:23910` (Second metacarpal bone)
  * `FMA:37385` (First dorsal interosseous muscle of hand)
- **Dẫn chiếu Tiêu chuẩn Y văn:**
  * *WHO Standard 2008, trang 57:* "On the dorsum of the hand, radial to the midpoint of the second metacarpal bone."
  * *GB/T 12346-2021, mục 6.2.*
- **Độ không đảm bảo sinh lý dự kiến:** $\pm 5.0\text{ mm}$ (do biến thiên teo cơ hoặc phì đại cơ gian cốt mu tay).
- **Trạng thái Thẩm định:** `EXPERT_REVIEW_PENDING` (Chờ hội đồng lâm sàng nghiệm thu).

---

#### B. ST36 — Túc Tam Lý (Stomach Meridian 36)
- **Mã chuẩn:** `ST36`
- **Tên chữ Hán / Pinyin:** 足三里 / Zúsānlǐ
- **Tọa độ Canonical chuẩn:** $[0.088, 0.445, 0.062]\text{ m}$ (Bên Phải)
- **Mốc bám giải phẫu (Skeletal Anchor):** Phía trước ngoài cẳng chân, cách mào trước xương chày 1 khoát ngón tay, trên bụng cơ cẳng chân trước.
- **Định danh Bản đồ Giải phẫu:**
  * `FMA:24476` (Tibia - Xương chày)
  * `FMA:45155` (Tibialis anterior muscle - Cơ cẳng chân trước)
- **Dẫn chiếu Tiêu chuẩn Y văn:**
  * *WHO Standard 2008, trang 75:* "On the anterior aspect of the leg, on the line connecting ST35 with ST41, 3 B-cun inferior to ST35, one finger-breadth lateral to the anterior crest of the tibia."
  * *GB/T 12346-2021, mục 6.3.*
- **Độ không đảm bảo sinh lý dự kiến:** $\pm 8.0\text{ mm}$.
- **Trạng thái Thẩm định:** `EXPERT_REVIEW_PENDING`.

---

#### C. KI3 — Thái Khê (Kidney Meridian 3)
- **Mã chuẩn:** `KI3`
- **Tên chữ Hán / Pinyin:** 太溪 / Tàixī
- **Tọa độ Canonical chuẩn:** $[0.038, 0.082, -0.015]\text{ m}$ (Bên Phải)
- **Mốc bám giải phẫu (Skeletal Anchor):** Chỗ lõm giữa đỉnh mắt cá trong xương chày và bờ trong gân gót (gân Achilles).
- **Định danh Bản đồ Giải phẫu:**
  * `FMA:24476` (Medial malleolus of tibia)
  * `FMA:51111` (Calcaneal tendon / Achilles tendon)
- **Dẫn chiếu Tiêu chuẩn Y văn:**
  * *WHO Standard 2008, trang 138:* "On the posteromedial aspect of the ankle, in the depression between the prominence of the medial malleolus and the calcaneal tendon."
  * *GB/T 12346-2021, mục 6.8.*
- **Độ không đảm bảo sinh lý dự kiến:** $\pm 6.0\text{ mm}$.
- **Trạng thái Thẩm định:** `EXPERT_REVIEW_PENDING`.

---

### 3. Nguyên tắc Nghiêm ngặt về Ranh giới Thẩm định

1. **Tuyệt đối không dùng ngưỡng $<15\text{ mm}$ hình học để tự công nhận tính đúng đắn y học:** Khoảng cách gần bề mặt mesh chỉ phản ánh việc dính bắt hình học, không chứng minh được vị trí huyệt chính xác theo y lý.
2. **Không tự chuyển trạng thái:** Trạng thái `USER_ANNOTATED_UNVERIFIED` và `EXPERT_REVIEW_PENDING` chỉ được nâng cấp khi có chữ ký và biên bản thẩm định chính thức của chuyên gia y khoa độc lập.
