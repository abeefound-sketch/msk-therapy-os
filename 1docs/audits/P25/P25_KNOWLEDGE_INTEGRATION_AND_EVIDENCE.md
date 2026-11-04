# MSK-Therapy-OS — Milestone P25 Audit
## P25: Knowledge Vault Integration, Evidence Linking & Clinical Safety Governance

**Tài liệu ID:** `MSK-P25-AUD-001`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Kiến trúc Cầu nối Tri thức Không Nhân bản (Single Database Principle)

Hệ thống tuân thủ nghiêm ngặt nguyên tắc kế thừa: **Tuyệt đối không tạo cơ sở dữ liệu thứ hai.**
- Tái sử dụng 100% engine và database SQLite P20 hiện hành (`msk_therapy_os.sqlite3`).
- Thiết lập module cầu nối `StudioKnowledgeBridge` tại `msk_therapy_os/knowledge_vault/studio_bridge.py`.

```text
[Blender / Motion Objects]
├── Acupoints: LI4, ST36, KI3
├── Joints: right_elbow, right_shoulder
└── Motion Trials: seth_elevation, cmu_02_01
           │
           ▼
[StudioKnowledgeBridge] ───► [CoordinateRegistry & JointConstraintRegistry]
           │
           ▼
[KnowledgeVault Engine] ───► Full-Text Search (FTS5) & Contradiction Graph
           │
           ▼
[Markdown Evidence Bundle] (Không chứa PII, mang banner ENGINEERING_RESEARCH_ONLY)
```

---

### 2. Khả năng Tra cứu Bằng chứng Liên kết (Evidence Resolvers)

1. **Tra cứu Huyệt vị (`resolve_acupoint_knowledge`):**  
   Truy xuất đồng thời:
   - Tên khoa học, tên chữ Hán, định danh FMA (`FMA:23910`, `FMA:24476`, `FMA:51111`).
   - Dẫn chiếu y văn chuẩn quốc tế: *WHO Standard Acupuncture Point Locations (2008)* và *GB/T 12346-2021*.
   - Sai số sinh lý dự kiến ($\pm 5\text{ mm}$ đến $\pm 18\text{ mm}$).
   - Các luận điểm đối nghịch và trạng thái thẩm định `EXPERT_REVIEW_PENDING`.
2. **Tra cứu Khớp cơ sinh học (`resolve_joint_knowledge`):**  
   Truy xuất:
   - Các bậc tự do chuyển động (`flexion_extension`, `scapulohumeral_elevation`).
   - Dẫn chiếu y văn cơ sinh học (*Kapandji 2007*, *Seth 2016*, *AAOS 1965*).
   - Ranh giới cứng (hard limits) và giả định mô hình.

---

### 3. Bảo toàn Bất biến An toàn Lâm sàng (Safety Invariants)

- `RELEASE_SCOPE = "ENGINEERING_RESEARCH_ONLY"`
- `CLINICAL_VALIDATION = "NOT_ESTABLISHED"`
- `clinical_depth_guidance_allowed = False`
- Mọi tài liệu xuất bản đều tự động gắn cờ cảnh báo, nghiêm cấm suy diễn tên huyệt hay tọa độ thành phác đồ điều trị, chẩn đoán tự động hay chỉ định xâm lấn.

---

### 4. Đánh giá Cổng G1–G4 Milestone P25

- **G1 Functional:** **PASS** (Cầu nối tra cứu, liên kết claims và xuất Markdown hoạt động 100%).
- **G2 Data Integrity:** **PASS** (Không nhân bản DB, bảo toàn định dạng FMA và WHO).
- **G3 Domain Validity:** **PENDING** (Chưa có hội đồng y học phê chuẩn các liên kết điều trị).
- **G4 Independent Acceptance:** **PENDING** (Chờ kiểm toán viên độc lập).

**Quyết định Điều hành:** $$\mathbf{CONDITIONAL\_GO} \longrightarrow \mathbf{Milestone\ P26}$$
