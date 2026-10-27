# CONDITION-TO-PROTOCOL MAPPING & SEARCH ENGINE AUDIT

**Document ID:** `AUDIT-DC-CONDITION-PROTOCOL-MAPPING`  
**Execution Date:** 2026-10-27  
**Engine:** `search_dien_chan_conditions` (`msk_therapy_os/dien_chan/search.py`)  
**Knowledge Base:** SQLite Local-First Schema (`msk_therapy_os/dien_chan/db.py`)

---

## 1. RELATIONAL KNOWLEDGE BASE INVENTORY

The local SQLite database stores classical reflexology protocols, symptom ontologies, and safety triage criteria across 7 isolated relational tables:

```
dien_chan_sources ──< dien_chan_points ──< dien_chan_protocol_points >── dien_chan_protocols >── dien_chan_conditions
                                                                                 │
                                                                                 ├──< dien_chan_evidence
                                                                                 └──< dien_chan_reviews
```

### 1.1. Curated Conditions Catalog

| Condition ID | Primary Vietnamese Name | Category | Primary Synonyms | Clinical Triage & Red-Flag Warnings |
|:---|:---|:---|:---|:---|
| `COND_HEADACHE_SINUS` | Đau đầu – Viêm xoang | `cranial_facial` | "đau đầu", "viêm xoang", "nhức đầu", "nghẹt mũi", "xoang trán", "xoang hàm", "sổ mũi", "viêm mũi dị ứng", "đau nửa đầu", "headache", "sinusitis" | **CẢNH BÁO NGUY HIỂM:** Đau đầu dữ dội đột ngột (như sét đánh), sốt cao kèm cứng gáy, nôn vọt, co giật, mờ mắt hoặc yếu liệt nửa người là dấu hiệu xuất huyết dưới nhện hoặc viêm màng não cấp. Chuyển cấp cứu y tế ngay lập tức. |
| `COND_NECK_SHOULDER` | Đau mỏi cổ vai gáy | `musculoskeletal` | "đau cổ gáy", "mỏi vai gáy", "căng cứng cổ", "cổ vai gáy", "thoái hóa cổ", "neck pain", "shoulder tension" | **CẢNH BÁO:** Tê bì lan xuống cánh tay/bàn tay kèm teo cơ, mất phản xạ gân xương hoặc rối loạn đại tiểu tiện gợi ý chèn ép tủy cổ cấp tính. Cần khám chuyên khoa ngoại thần kinh. |
| `COND_LUMBAR_SPINE` | Đau cột sống thắt lưng | `musculoskeletal` | "đau lưng", "đau thắt lưng", "mỏi lưng", "thoái hóa thắt lưng", "thoát vị đĩa đệm", "low back pain" | **CẢNH BÁO:** Rối loạn cơ tròn (bí tiểu hoặc tiểu không tự chủ), mất cảm giác vùng yên ngựa (hội chứng chùm đuôi ngựa) là cấp cứu ngoại khoa khẩn cấp. |
| `COND_INSOMNIA` | Mất ngủ – Căng thẳng thần kinh | `neurological` | "mất ngủ", "khó ngủ", "ngủ không sâu giấc", "trằn trọc", "căng thẳng", "stress", "insomnia" | **CẢNH BÁO:** Mất ngủ kéo dài kèm sút cân nhanh, ảo giác hoặc thay đổi ý thức đột ngột cần được đánh giá chuyên khoa tâm thần kinh. |

---

## 2. SOURCE-BACKED PROTOCOL MATRIX

### 2.1. Protocol `PROTO_HEADACHE_SINUS_01` (Image B Ground Truth)
* **Title:** Phác đồ Đau Đầu – Viêm Xoang (*Dien Chan Headache & Sinusitis Master Protocol*)
* **Source:** `SRC_IMG_DC_02` (Đồ hình trị liệu: Đau Đầu – Viêm Xoang, Image B)
* **Therapeutic Intent:** Thông khiếu xoang mặt, tiêu viêm, an thần định tâm và giải phóng áp lực xoang trán/hàm.
* **Evidence Level:** `TRADITIONAL_REFLEXOLOGY_REFERENCE`
* **Ordered Point Sequence (11 Points):**

| Seq | Point Code | Grid | Name (VI) | Technique | Laterality | Clinical Justification & Caution |
|:---:|:---:|:---:|:---|:---:|:---:|:---|
| 1 | `DC_103` | `O-2` | Giữa trán | Day ấn 30s | Midline | Hạ áp lực nội sọ, trấn tĩnh vỏ não, an thần. |
| 2 | `DC_106` | `O-3` | Trán dưới | Day ấn 30s | Midline | Điều hòa trung khu thần kinh, giảm co thắt mạch. |
| 3 | `DC_107` | `A-3` | Hai bên trán | Day ấn 30s | Bilateral | Giải tỏa ứ trệ hốc xoang trán hai bên. |
| 4 | `DC_300` | `C-1` | Trán trên con ngươi | Day ấn 30s | Bilateral | Bổ thận thủy, hỗ trợ tiêu viêm niêm mạc xoang. |
| 5 | `DC_73` | `C-6` | Bờ dưới ổ mắt | Day nhẹ 30s | Bilateral | Giảm sưng nề, thông dẫn lưu xoang hàm. |
| 6 | `DC_189` | `O-5` | Sống mũi | Vuốt dọc 30s | Midline | Kích thích thông khiếu đường thở vùng mũi. |
| 7 | `DC_61` | `B-8` | Hốc cánh mũi | Day ấn 30s | Bilateral | Tác dụng kháng viêm và cắt cơn đau xoang mạnh. |
| 8 | `DC_19` | `O-8` | Nhân trung | Ấn nhấp 15s | Midline | Thông khí phế quản. *Chống chỉ định khi huyết áp cao kịch phát.* |
| 9 | `DC_127` | `O-11` | Hõm cằm | Day ấn 30s | Midline | Làm ấm cơ thể, tăng cường hệ miễn dịch. |
| 10 | `DC_96` | `G-4` | Thái dương | Day nhẹ 30s | Bilateral | Giải tỏa co thắt mạch máu thái dương (đau nửa đầu). |
| 11 | `DC_43` | `O-7.5` | Đỉnh chóp mũi | Chấm day 15s | Midline | Làm ấm và thông nghẹt mũi tức thì. |

### 2.2. Complementary Protocols

#### `PROTO_NECK_SHOULDER_01` (Cervical Tension)
* Points: `DC_26` (Ấn đường, Midline), `DC_34` (Đầu mày, Bilateral), `DC_61` (Cánh mũi, Bilateral), `DC_15` (Dái tai sau, Bilateral), `DC_16` (Đỉnh tai, Bilateral).

#### `PROTO_LUMBAR_SPINE_01` (Lumbar Spine Balance)
* Points: `DC_1` (Sống mũi thắt lưng, Midline), `DC_19` (Nhân trung, Midline), `DC_26` (Ấn đường, Midline), `DC_127` (Hõm cằm, Midline).

#### `PROTO_INSOMNIA_01` (Sedation & Sleep Regulation)
* Points: `DC_103` (Giữa trán, Midline), `DC_106` (Hạ trán, Midline), `DC_26` (Ấn đường, Midline), `DC_0` (Supratragic notch, Bilateral).

---

## 3. SEARCH ENGINE VERIFICATION & ZERO HALLUCINATION BENCHMARK

The search pipeline was evaluated against both targeted and adversarial queries:

| Test Query | Normalized Query | Match Type | Returned Condition | Protocol Activated | Verdict |
|:---|:---|:---:|:---|:---:|:---:|
| `"Đau đầu - Viêm xoang"` | `dau dau viem xoang` | Exact Name | `COND_HEADACHE_SINUS` | `PROTO_HEADACHE_SINUS_01` (11 pts) | PASS |
| `"nhức nửa đầu"` | `nhuc nua dau` | Synonym Match | `COND_HEADACHE_SINUS` | `PROTO_HEADACHE_SINUS_01` (11 pts) | PASS |
| `"viem xoang"` | `viem xoang` | Unaccented Match | `COND_HEADACHE_SINUS` | `PROTO_HEADACHE_SINUS_01` (11 pts) | PASS |
| `"mỏi vai gáy"` | `moi vai gay` | Synonym Match | `COND_NECK_SHOULDER` | `PROTO_NECK_SHOULDER_01` (5 pts) | PASS |
| `"thoát vị đĩa đệm"` | `thoat vi dia dem` | Synonym Match | `COND_LUMBAR_SPINE` | `PROTO_LUMBAR_SPINE_01` (4 pts) | PASS |
| `"mat ngu"` | `mat ngu` | Unaccented Match | `COND_INSOMNIA` | `PROTO_INSOMNIA_01` (4 pts) | PASS |
| `"bệnh lạ không có"` | `benh la khong co` | Stopword Filtration | *None (Filtered)* | *None (Abstention)* | PASS |
| `"hội chứng lupus ban đỏ XYZ"` | `hoi chung lupus ban do xyz` | Unknown Query | *None (Zero Matches)* | *None (Abstention)* | PASS |

### Zero-Hallucination Rejection Guarantee
When an unmapped condition is requested, the system outputs:
> *"Chưa có dữ liệu đã đối chiếu. Hệ thống không tạo phác đồ giả."*
Zero synthetic points are generated. Zero generative AI hallucinations are permitted in the medical pathway.
