# BÁO CÁO NGHIÊN CỨU LIÊN HỆ ĐỘNG HỌC VÀ TRI THỨC Y VĂN — bundle_p31_20261103T070334Z
> [!IMPORTANT]
> **PHẠM VI: ENGINEERING_RESEARCH_ONLY**
> **RÀNG BUỘC AN TOÀN:** STRICT_RESEARCH_ONLY - NO_AUTONOMOUS_DIAGNOSIS_OR_PRESCRIPTION
> Hệ thống nghiêm cấm tự động chẩn đoán, kê đơn hoặc hướng dẫn trị liệu lâm sàng.

## 1. Tổng Quan Khung Cảnh Giải Phẫu (Scene Asset Manifest)
| Asset ID | Tên Cấu Trúc | Bone Parent | FMA ID | Số Tam Giác | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `mesh_humerus_r` | Humerus_R | `upper_arm.R` | `FMA:23412` | 2,836 | `AVAILABLE` |
| `mesh_scapula_r` | Scapula_R | `clavicle.R` | `FMA:23240` | 3,356 | `AVAILABLE` |
| `mesh_clavicle_r` | Clavicle_R | `clavicle.R` | `FMA:13337` | 1,776 | `AVAILABLE` |
| `mesh_thorax` | Thorax | `root` | `FMA:7476` | 5,072 | `AVAILABLE` |
| `mesh_radius_r` | Radius_R | `forearm.R` | `FMA:23463` | 0 | `ASSET_NOT_AVAILABLE` |
| `mesh_ulna_r` | Ulna_R | `forearm.R` | `FMA:23466` | 0 | `ASSET_NOT_AVAILABLE` |
| `mesh_metacarpals_r` | Metacarpals_R | `hand.R` | `FMA:23910` | 0 | `ASSET_NOT_AVAILABLE` |
| `mesh_tibia_r` | Tibia_R | `shank.R` | `FMA:24476` | 0 | `ASSET_NOT_AVAILABLE` |

## 2. Tọa Độ Mốc Giải Phẫu & Huyệt Vị (Surface Anchor Registry)
| Mã Huyệt / Mốc | Cấu Trúc Bám | Bone Parent | Dịch Chuyển (mm) | Trôi Bề Mặt (mm) | Trạng Thái Bám |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `LI14` | Tuberositas deltoidea humeri | `Humerus_R` | 775.2 mm | 0.00008 mm | `VALID_SURFACE_ANCHOR` |
| `LI15` | Angulus acromii / Sulcus intertubercularis | `Scapula_R` | 54.5 mm | 0.00004 mm | `VALID_SURFACE_ANCHOR` |
| `LATERAL_EPICONDYLE` | Epicondylus lateralis humeri | `Humerus_R` | 785.5 mm | 0.00000 mm | `VALID_SURFACE_ANCHOR` |
| `LI4` | First dorsal interosseous / 2nd metacarpal shaft | `None` | 0.0 mm | 0.00000 mm | `ASSET_NOT_AVAILABLE` |
| `ST36` | Tibialis anterior / Margo anterior tibiae | `None` | 0.0 mm | 0.00000 mm | `ASSET_NOT_AVAILABLE` |
| `KI3` | Sulcus malleolaris / Tendo calcaneus | `None` | 0.0 mm | 0.00000 mm | `ASSET_NOT_AVAILABLE` |

## 3. Chỉ Số Kiểm Định Động Học & Độ Bất Định (Kinematic Uncertainty)
- **Tổng số frame chuyển động:** 100 frames (60 FPS)
- **Tốc độ góc tối đa đo được:** 240.5°/s (Ngưỡng cảnh báo: 720°/s)
- **Bước nhảy góc đơn frame lớn nhất:** 12.4° (Ngưỡng cảnh báo: 45°)
- **Bảo toàn chiều dài xương (Bone length invariance):** Sai lệch tối đa 0.0001 mm
- **Mô hình phối hợp bả vai - cánh tay:** 2:1 (Inman 1944 / Seth 2016)
- **Trạng thái độ chính xác lâm sàng:** `ACCURACY_NOT_ESTABLISHED` (NOT_ESTABLISHED)

## 4. Dẫn Chiếu Y Văn & Bằng Chứng Tri Thức (Knowledge Vault)
### Mốc `LI14` — 臂臑 (Binao)
- **Vị trí giải phẫu:** Tuberositas deltoidea humeri, lateral aspect of arm, m. deltoideus insertion
- **Định danh FMA:** `FMA:23412 (Deltoid tuberosity of humerus)`
- **Dẫn chiếu chuẩn WHO:** WHO Standard 2008, p. 41: On the lateral aspect of the arm, posterior to the distal insertion of the deltoid muscle, 7 B-cun superior to the cubital crease.
- **Độ bất định sinh lý:** ±5.0 mm
- **Trạng thái mô hình 3D:** `AVAILABLE`
- **Bằng chứng đã lập chỉ mục trong Knowledge Vault:**
  * [clm_eea76333f995] Binao (<b>LI14</b>) is located on the lateral aspect of the arm at the distal insertion of the deltoid muscle on...

### Mốc `LI15` — 肩髃 (Jianyu)
- **Vị trí giải phẫu:** Acromion of scapula and greater tubercle of humerus depression
- **Định danh FMA:** `FMA:23240 (Acromion of scapula)`
- **Dẫn chiếu chuẩn WHO:** WHO Standard 2008, p. 42: On the shoulder girdle, in the depression between the acromial angle and the greater tubercle of the humerus when the arm is abducted.
- **Độ bất định sinh lý:** ±5.0 mm
- **Trạng thái mô hình 3D:** `AVAILABLE`
- **Bằng chứng đã lập chỉ mục trong Knowledge Vault:**
  * [clm_e1731ad4e27a] Jianyu (<b>LI15</b>) is located on the shoulder girdle in the depression between the acromial angle and greater tubercle of humerus...

### Mốc `LI4` — 合谷 (Hegu)
- **Vị trí giải phẫu:** Radial aspect of 2nd metacarpal bone, midpoint of shaft, 1st dorsal interosseous muscle
- **Định danh FMA:** `FMA:23910 (Second metacarpal bone) & FMA:37385 (First dorsal interosseous muscle)`
- **Dẫn chiếu chuẩn WHO:** WHO Standard 2008, p. 57: On the dorsum of the hand, radial to the midpoint of the second metacarpal bone.
- **Độ bất định sinh lý:** ±5.0 mm
- **Trạng thái mô hình 3D:** `ASSET_NOT_AVAILABLE`
- **Bằng chứng đã lập chỉ mục trong Knowledge Vault:**
  * [clm_59cc9618e33c] Hegu (<b>LI4</b>) is located on the dorsum of the hand, radial to the midpoint of the second metacarpal bone (FMA...

### Mốc `ST36` — 足三里 (Zusanli)
- **Vị trí giải phẫu:** Anterior aspect of leg, 1 finger-breadth lateral to anterior crest of tibia, m. tibialis anterior
- **Định danh FMA:** `FMA:24476 (Tibia) & FMA:45155 (Tibialis anterior muscle)`
- **Dẫn chiếu chuẩn WHO:** WHO Standard 2008, p. 75: Anterior region of leg, 3 B-cun inferior to ST35, one finger-breadth lateral to anterior crest of tibia.
- **Độ bất định sinh lý:** ±8.0 mm
- **Trạng thái mô hình 3D:** `ASSET_NOT_AVAILABLE`
- **Bằng chứng đã lập chỉ mục trong Knowledge Vault:**
  * [clm_d0621a6b0cfe] Zusanli (<b>ST36</b>) is located on the anterior-lateral aspect of the leg lateral to the anterior crest of the tibia...

### Mốc `KI3` — 太溪 (Taixi)
- **Vị trí giải phẫu:** Posteromedial aspect of ankle, depression between prominence of medial malleolus and tendo calcaneus
- **Định danh FMA:** `FMA:24476 (Tibia, medial malleolus) & FMA:51111 (Calcaneal tendon)`
- **Dẫn chiếu chuẩn WHO:** WHO Standard 2008, p. 138: Posteromedial region of ankle, in the depression between the prominence of the medial malleolus and the calcaneal tendon.
- **Độ bất định sinh lý:** ±6.0 mm
- **Trạng thái mô hình 3D:** `ASSET_NOT_AVAILABLE`
- **Bằng chứng đã lập chỉ mục trong Knowledge Vault:**
  * [clm_ee10ef88bf52] Taixi (<b>KI3</b>) is located in the depression between the medial malleolus and the calcaneal tendon (FMA:51111).

## 5. Ranh Giới Nghiên Cứu & Bảo Mật Dữ Liệu
- **Kiểm tra thông tin PII:** Âm tính 100%. Không chứa danh tính cá nhân, thông tin định danh y tế hoặc bản ghi lâm sàng.
- **Mục đích sử dụng:** Thí nghiệm kỹ thuật, nghiên cứu động học chuyển động, phục vụ đào tạo và trực quan hóa khoa học.
- **Khuyến cáo:** Tuyệt đối không sử dụng kết quả định vị huyệt hoặc góc khớp từ camera đơn để can thiệp trị liệu lâm sàng.