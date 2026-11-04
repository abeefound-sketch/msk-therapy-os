# MASTER PROMPT CHO CODING AGENT
## MSK-Therapy-OS | P19 Architecture Reset & Source-of-Truth Governance + P20 Knowledge Vault Foundation

**Vai trò:** Principal Software Architect + Forensic Code Auditor + Open-Source Integration Engineer + Data Provenance Engineer + Test Engineer.

**Nhiệm vụ:** Thực thi P19 trên repository thực, song song triển khai P20 Knowledge Vault có thể chạy độc lập. Chuẩn bị hồ sơ quyết định và backlog có điều kiện cho P21–P26. KHÔNG tiếp tục cách làm "thêm tính năng rồi chạy test". Mục tiêu là loại bỏ sự mơ hồ về dữ liệu, nguồn tọa độ và runtime, bảo toàn các chức năng hiện có, không tự tuyên bố được xác nhận chuyên môn.

**Ngôn ngữ báo cáo:** Tiếng Việt; giữ nguyên tên file, mã, API và thuật ngữ kỹ thuật khi phù hợp.

---

## 0. Bối cảnh, đầu vào và nguyên tắc chứng cứ

### Đầu vào phải khảo sát

1. **Repository MSK-Therapy-OS đang hoạt động**: kiểm tra Git working tree, branch, HEAD, tags, trạng thái P18, cấu trúc project, database, assets và lệnh khởi chạy hiện có.
2. **Gói tham chiếu đính kèm:** `msk-therapy-os-p17-roadmap-source.zip` và `msk-therapy-os-p17-roadmap-prompt.md`. Đây là snapshot P17 dùng để đối chiếu, **không tự động là source of truth của P18/current runtime**.
3. Tài liệu trong repo, tối thiểu: `README.md`, `1docs/SPEC.md`, `1docs/ARCHITECTURE.md`, `1docs/EVIDENCE.md`, `1docs/COORDINATE_REGISTRY.md`, `1docs/INTEGRATION_DECISION.md`, `1docs/OPEN_SOURCE_DECISION_MATRIX.md`, `1docs/OPEN_SOURCE_LICENSING_AUDIT.md`, `1docs/audits/P17/`, cùng tài liệu P18 nếu tìm thấy.
4. **Kho starter** `MSK_Knowledge_Vault_Starter_Offline.zip` nếu thực sự có trong workspace hoặc do người dùng cung cấp. Không giả vờ đã đọc nếu không thấy. Nếu thiếu, tạo P20 scaffold theo các yêu cầu trong prompt này và đánh dấu `STARTER_NOT_AVAILABLE`.
5. Có thể rà soát các nguồn bên ngoài được đề xuất như **Human Atlas, TARA, `tcm-3d`, các công cụ mesh**, nhưng **không mặc định chính xác hay có quyền sử dụng**. Xác định đúng repo, giấy phép, asset, độ tin cậy và commit trước khi cân nhắc đưa vào hệ thống.

### Quy tắc ưu tiên sự thật

- **Live runtime và bằng chứng tái lập được** > mã nguồn có thể chạy > test thực đo > dữ liệu và metadata thô > tài liệu thiết kế > báo cáo PASS > lời tuyên bố.
- Mọi phát hiện phải có: `file:line` hoặc path, commit/hash (nếu có), cách tái lập, expected/actual, phạm vi ảnh hưởng, mức độ tin cậy.
- Phân biệt rõ `OBSERVED`, `REPRODUCED`, `INFERRED`, `CLAIMED`, `NOT_OBSERVABLE`, `NOT_TESTED`, `BLOCKED`.
- Nếu P18 không có trong workspace: **không được viết "P18 đã đóng băng/đã kiểm toán"**. Báo `P18_BASELINE_UNVERIFIED`, dùng snapshot P17 như dữ liệu đối chiếu, ghi rõ điều kiện để xác lập baseline thật.
- Không nâng `ENGINEERING PASS` thành `ANATOMICAL VERIFIED` hay `CLINICAL APPROVED` thông qua test tự viết hoặc dữ liệu mock.

### Các tín hiệu cụ thể phải điều tra, không được kết luận trước

- Trong snapshot P17, `1docs/COORDINATE_REGISTRY.md` định nghĩa `+X` là phía **phải giải phẫu**, nhưng metadata tại `msk_therapy_os/static/atlas/data/acupuncture_3d.json` định nghĩa `+X Left`. Kiểm tra đây là lỗi chú thích, phép biến đổi chưa áp dụng, hay lỗi làm đổi bên trong runtime. Không "sửa" bằng cách đảo dấu hàng loạt trước khi tái lập.
- `msk_therapy_os/spatial_resolver.py` có các seed `AUDITED_CANONICAL_POINTS`, mô tả 4 lớp nguồn; `point_localization_rules.py`, `landmark_registry.py`, `anatomical_registration.py`, `cun_scaling.py`, `points.py`, `meridian_route_graph.py`, `meridian_surface_engine.py` cùng tham gia suy ra và dựng hình. Cần đo xem đâu là **nguồn thực sự đã được runtime chọn**, thay vì tin nhãn `authoritative` trong docstring.
- `msk_therapy_os/server.py` có endpoint liên quan `/api/atlas/meridians/resolve`; giao diện `static/atlas/meridians.js` có `AtlasSpatialState` và cơ chế mode/layer. Phải truy vết từ file dữ liệu qua API đến đối tượng được vẽ trên canvas, kể cả cache, SQLite override và fallback.
- Snapshot P17 có GLB tại `msk_therapy_os/static/education/models/` nhưng có thể là mô hình riêng của **Education Studio**, không phải mesh đang dùng bởi Atlas. Không đánh đồng "có file `.glb`" với "Atlas đã dùng mesh giải phẫu đúng".
- Báo cáo P17 tự ghi nhận 806 kiểm thử unit/integration và 24 nhóm Playwright PASS, nhưng đó là **tuyên bố của snapshot**. Chạy lại và phân loại test nào chứng minh runtime và test nào chỉ khẳng định mock/self-assertion.

---

## 1. Phạm vi, kiến trúc đích và điều không được làm

### Kiến trúc logic đích

```text
MSK-Therapy-OS (Shell / Orchestration / Auth / Observability)
    |
    +-- Anatomical Atlas (anatomy mesh + landmarks + traditional acupoints + meridian overlays)
    |      `-- Source adapters + transform registry + independent validation
    |
    +-- Knowledge Vault (Markdown + originals + claims + citations + contradictory viewpoints)
    |      `-- SQLite indexing / full text search / immutable provenance
    |
    +-- Clinical Workspace (SOAP / ROM / outcomes / visits; isolated patient store)
    |
    `-- Adapter & Verification (contracts / licensing / lineage / tests / evidence gates)
```

Đây là **5 khối chức năng**, bao gồm Shell và Adapter & Verification; có thể cùng nằm trong một mono-repo ban đầu miễn là ranh giới hợp đồng/module độc lập và khả năng thay thế được chứng minh. **Không bắt buộc chia ngay thành nhiều Git repo.** Không tạo distributed system hoặc microservices chỉ để có vẻ hiện đại.

### Non-negotiable

1. P18: **freeze only after verifying actual P18 commit/status**. Tạo branch/tag/snapshot sao lưu theo phương thức an toàn và không phá lịch sử; nếu P18 không sẵn, ghi BLOCKED thay vì tạo nhãn giả.
2. P19 **audit-first**: không viết mới resolver, waypoint, camera-based pose hay mô hình người trước khi có bản đồ nguồn, xác định sự bất nhất và hướng sửa được phê duyệt.
3. P20 độc lập với Atlas và với database bệnh nhân; có thể phát triển song song trên branch/worktree riêng.
4. Không dùng dữ liệu bệnh nhân thật, không đưa PHI/PII vào logs, fixtures, prompt, vector store, demo hay repo nguồn. `Clinical Workspace` ở giai đoạn này chỉ là kế hoạch và dữ liệu giả lập.
5. Không phát sinh chẩn đoán tự động, kê phác đồ, liều điện DDS, gợi ý kỹ thuật thrust tốc độ cao, hay biến đồ thị kinh lạc truyền thống thành cấu trúc thần kinh/giải phẫu được chứng minh.
6. Giữ invariant an toàn hiện có: `G14 = BLOCKED_EXTERNAL_DATA`, `clinical_depth_guidance_allowed = False`, `CLINICAL_VALIDATION = NOT_ESTABLISHED`, `RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY`, trừ khi chính cấu hình thực tế đã đổi thì ghi sai lệch và fail closed.
7. Windows 64-bit, Intel i7-5600U/8 GB/Intel HD 5500, offline-first; production backend Python stdlib + SQLite, frontend vanilla HTML/CSS/JS, Three.js đã được vendored khi thật sự cần. Dependency bổ sung chỉ tồn tại trong sandbox/dev evaluation, ghi rõ nguồn, giấy phép, size, khả năng offline; không đưa tự động vào runtime.
8. Không xóa code cũ, sửa hàng loạt tọa độ, migrate DB không hồi phục, overwrite `EVIDENCE.md`, hoặc đổi endpoint công khai khi chưa có rollback và regression. Mọi retirement phải theo `inventory -> deprecate -> feature flag -> measured migration -> removal approval`.
9. Không tự `git push`, merge `main`, phát hành clinical production, hoặc tải/phân phối các tài sản có giấy phép không rõ. Giữ các thay đổi nội bộ trong branch; công bố diff và điểm cần chấp thuận.
10. Nếu không thể chạy UI, OpenGL, webcam, Playwright hoặc kiểm thử trên máy mục tiêu, báo đúng `NOT_OBSERVABLE`, kèm bước xác minh tại môi trường phù hợp; không thay bằng screenshot giả, thời gian khung hình hardcode hay test mock.

---

## 2. Bước 0: Forensic Baseline & Safety Preflight (bắt buộc trước khi sửa)

Thực thi:

1. Ghi `git status --short`, branch, `git rev-parse HEAD`, tag gần nhất, tình trạng thay đổi chưa commit; kiểm tra `.gitignore`, dependency và assets lớn. Không overwrite thay đổi của người khác.
2. Khảo sát README và các launcher (`start_app.py`, `start_studio.bat`, CLI). Xác định đúng runtime host/port/routes và database path trong môi trường thực.
3. Kiểm tra các reports P17, P18, các artifacts/timestamps/hashes; đối chiếu claim PASS với tệp có mặt và lệnh tái lập.
4. Backup có thể phục hồi: database SQLite (nếu có) bằng backup API, asset manifests và config **không chứa thông tin nhạy cảm**. Tạo hash SHA-256 của input baseline/snapshot.
5. Chạy các unit tests phù hợp và E2E khi môi trường đủ điều kiện; ghi command, interpreter/browser, exit code, stdout/stderr log, số test collect/pass/skip/fail. Không dựa vào số PASS trong Markdown cũ.
6. Kiểm tra hard stop an toàn, readonly mode, CORS/CSRF, auth và quyền truy cập hiện tại; không sửa security một cách ngầm định.

**Deliverable:** `1docs/audits/P19/P19_00_BASELINE_AND_EVIDENCE.md` và `1docs/audits/P19/evidence/` với lệnh và kết quả có thể tái lập. Ghi `P18_BASELINE_CONFIRMED` hoặc `P18_BASELINE_UNVERIFIED`.

---

## 3. P19: Architecture Reset & Source-of-Truth Governance

### P19.A — Module ownership và dependency audit

Lập bản đồ tất cả module quan trọng theo các cột:

`module | chức năng | runtime entrypoint | inputs | outputs | data writes | calls/dependencies | owner đề xuất | duplicated function | decision KEEP/ISOLATE/DEPRECATE/REPLACE | evidence`.

Đặc biệt so sánh Atlas 2D/3D, Education Studio, Meridian Engine, landmark registration, spatial resolver, custom point editor, SOAP/ROM/FHIR, safety, evidence. Mục tiêu là **giảm chồng chéo quyền quyết định**, không phải xóa hàng loạt.

### P19.B — Coordinate/mesh/point data lineage audit (trọng tâm)

Với ít nhất `LI4`, `ST36`, `KI3` và một điểm ở cổ vai để bắt lỗi frame, tạo một **lineage trace** theo đường:

```text
upstream document/dataset (license, edition, commit, hash)
    -> source ID / source coordinates / landmark definitions
    -> transform id + version + handedness + axes + units + origin
    -> canonical point with laterality and posture
    -> mesh id + hash + anatomical part + surface projection
    -> resolver/layer selection + cache + SQLite overrides
    -> REST response (actual numeric XYZ + evidence metadata)
    -> frontend state + actual WebGL/object coordinates
    -> human inspection / domain review status
```

**Yêu cầu thực nghiệm:**

- Kiểm tra hướng `+X` bằng các mốc trái/phải trên hình thật. Không tin nhãn. Kiểm tra scaling mm/cm/m, origin, handedness, matrix multiplication order, mirroring, normal vectors, camera/scene world transforms, pose deltas.
- Kiểm tra **tính hiện diện thật của surface mesh**: asset được load có phải BodyParts3D `FJ2810` như tài liệu khẳng định không, hash đúng không, 3D positions có cùng reference pose/space không; xem network/runtime resource loader. Mesh Education Studio phải được phân biệt riêng.
- Gọi API bằng dữ liệu test thực, log ID/coordinates và ngữ cảnh. So sánh với object/marker ở browser; không coi "marker nằm trên bề mặt" là bằng chứng đúng vị trí giải phẫu.
- Kiểm tra **phủ quyết ghi đè**: data JSON, Python dict seed, hardcoded JS marker, SQLite override, user edits, cache, fallback. Mọi đường đi phải có precedence công khai; trường hợp xung đột phải có báo cáo và không tự chọn rồi che đi.
- Kiểm tra sự khác biệt giữa định nghĩa vị trí theo tài liệu huyệt học, quyết định gán tọa độ lên một mesh mẫu, và thao tác chiếu lên bề mặt. **WHO định nghĩa vị trí không đồng nghĩa với cung cấp XYZ đúng cho mọi cơ thể.**
- Dựng tests **có thể thất bại thực sự**: fixture độc lập, round-trip transform, left/right inversion, unit conversion, invalid mesh hash, stale cache, conflicting overrides, asymmetric posture, API/UI drift, missing metadata, fallback without source.
- Không mặc định con số sai lệch 5/15/35 mm cũ là tiêu chuẩn y học; ngưỡng kỹ thuật chỉ được dùng nếu lý giải và có đánh giá chuyên môn phù hợp.

**Minimum output:** `P19_01_ARCHITECTURE_MAP.md`, `P19_02_SOURCE_OF_TRUTH_REGISTRY.csv` (hoặc JSON), `P19_03_COORDINATE_LINEAGE.md`, `P19_04_RUNTIME_CONFLICT_MATRIX.md`, test/trace evidence. Ghi rõ **single authoritative runtime selection policy** nhưng không đòi mọi loại tri thức phải có cùng một nguồn chân lý: chuẩn vị trí, bản vẽ truyền thống và hình học mesh cần provenance khác nhau.

### P19.C — Quy tắc dữ liệu và contracts cho Adapter & Verification

Thiết kế, tài liệu hóa và thử nghiệm **contract** (ưu tiên Python dataclasses/JSON schema mô tả tương thích stdlib) bao gồm:

- `source_id`, `source_type`, `dataset_version`, `license`, `citation_uri`, `file_hash`, `review_status`.
- `mesh_id`, `mesh_hash`, `reference_pose`, `units`, `frame_id`, `axis_convention`, `handedness`, `origin`, `transform_id`, `transform_version`.
- `point_code`, `standard_system`, `laterality`, `landmark_rule`, `coordinate_xyz`, `uncertainty`, `provenance`, `validation_status`.
- `computed_geometry` ≠ `source_record` ≠ `expert-reviewed position`.
- `resolver_selection_reason`, `override_history`, `fallback_reason`, `runtime_trace_id`, `source_conflicts[]`.

Mọi conversion phải công khai, deterministic, versioned, kiểm tra qua round-trip trong tolerance số học được định nghĩa. Nguồn không tương thích frame/mesh phải **fail closed** hoặc hiển thị `UNVERIFIED`, không âm thầm tương thích hóa.

Ở P19, có thể bổ sung **instrumentation read-only** và unit tests nhỏ an toàn để chứng minh lineage; **không thực hiện atlas rewrite**.

### P19.D — Deprecation và integration strategy

Mỗi engine trùng lặp có ADR:

- Vì sao giữ, cô lập, thay thế hoặc loại bỏ về sau;
- Consumer thực tế đang gọi;
- Behavior được bảo toàn;
- Plan migration và rollback;
- Có hay chưa có test thực chứng;
- Ảnh hưởng Windows offline, hiệu năng, UI và security.

Tạo feature flags an toàn nếu cần để cô lập resolver thử nghiệm, **default behavior không đổi**. Không đưa adapter mới vào public/default clinical workflow khi chưa qua G1–G4.

### P19.E — Nghiệm thu P19

P19 chỉ `ENGINEERING PASS` khi:

1. Bản đồ module có đầy đủ runtime inputs/outputs, mọi tuyến quyết định tọa độ đang chạy được ghi nhận.
2. Có **trace cụ thể** từ nguồn tới API và browser cho 3 huyệt mẫu (nếu chưa tái lập được, ghi rõ `BLOCKED`, không PASS).
3. Có giải thích/kiểm thử xung đột `+X Right` vs `+X Left`, tình trạng mesh thật, override, mode precedence và fallback.
4. Unit/API/E2E hiện có không bị phá trong phạm vi môi trường có thể chạy, hoặc có regression log kèm nguyên nhân và rollback.
5. G3 anatomy validity vẫn `PENDING_EXPERT_REVIEW` đến khi reviewer độc lập đánh giá đúng tập bằng chứng; không được tự cấp.

---

## 4. P20: Knowledge Vault Foundation (được triển khai song song P19)

### Mục tiêu MVP

Kho tri thức **offline**, dùng được khi Atlas hỏng/không chạy; nhập bằng copy-paste text/Markdown, phân loại, tìm kiếm full text, tách claims, lưu nguồn và các quan điểm mâu thuẫn. Tích hợp với `1docs/EVIDENCE.md` bằng **liên kết/adapter**, không overwrite hay coi mọi mục là tài liệu đã thẩm định.

### Cấu trúc đề xuất (điều chỉnh theo repo thực)

```text
knowledge_vault/
  README.md
  originals/               # nguồn lưu theo nội dung/hash; tuyệt đối không chứa PHI
  notes/                   # Markdown do người dùng biên soạn
  schemas/                 # documented data contracts
  vault.db                 # LOCAL, gitignored; SQLite
  import_export/           # nếu cần công cụ migration/backup
msk_therapy_os/knowledge_vault/  # package Python stdlib; giữ hướng import rạch ròi
1docs/audits/P20/
```

Không đưa các nội dung có bản quyền không được phép tái phân phối vào Git; tài liệu nguồn có license/reuse flags, lưu metadata/excerpt hợp lệ và URL khi cần.

### Data model bắt buộc

- `documents`: `doc_id`, SHA256/dedup key, title, author/org, date, document_type, namespace (`ANATOMY_EVIDENCE`, `TRADITIONAL_MERIDIAN`, `DIEN_CHAN_REFLEX`, `RESEARCH_NOTE`, ...), language, source URI, original location, license/reuse permission, import timestamp, raw hash, review status.
- `claims`: `claim_id`, exact source span/quote vị trí, claim text, claim type, assertion vs inference, status (`UNREVIEWED`, `CONTESTED`, `SUPPORTED`, `REJECTED`, `RETRACTED`...), evidence type/tier riêng, author/reviewer/time, uncertainty; **status khác evidence quality**.
- `citations`: `claim_id`, `doc_id`, page/section/offset, source availability, retrieval date, relationship (`SUPPORTS`, `CONTRADICTS`, `CONTEXT`, `CITES`).
- `relations`: claim-to-claim/document-to-document links, typed relationship, provenance.
- `reviews` và append-only `audit_events`: change history, actor, before/after metadata, timestamp, rationale. Không ghi đè trạng thái cũ không dấu vết.
- `tags`, `document_tags`; optional `entities` cho anatomical/acupoint/meridian codes nhưng **không buộc Knowledge phụ thuộc Atlas**.
- Chọn schema có FK, unique constraints, migrations được version, `PRAGMA foreign_keys=ON`, transactions. FTS5 nếu SQLite runtime hỗ trợ, fallback documented khi không có. Không dùng thuật toán AI sinh claim rồi tự xét đúng.

### Chức năng người dùng tối thiểu

1. `import`: file Markdown, plain text, stdin/copy-paste; metadata thiếu được ghi `UNKNOWN`, không suy diễn nguồn.
2. `classify`: namespace, tags, nội dung gốc/diễn giải; hỗ trợ trạng thái chưa xác minh.
3. `claim add/link/review`: thao tác minh bạch, không tự động `APPROVED`.
4. `search`: keyword, phrase, tag, nguồn, namespace, status; trả về vị trí nguồn và các liên kết.
5. `conflicts`: phát hiện/nhập quan hệ mâu thuẫn, **giữ cả hai nhận định**; không auto-delete hoặc auto-merge quan điểm.
6. `export`: Markdown + JSON/SQLite backup, bảo toàn source ID, citation, hash và review history.
7. Một lối dùng đơn giản cho người không lập trình: **CLI documented và giao diện nhập/search tối giản nếu có thể implement an toàn theo stdlib**. Không dựng giao diện bóng bẩy trước khi có persistence và search thật.
8. Import lặp cùng tệp phải idempotent hoặc có version history rõ ràng; xóa/chỉnh sửa phải có cách khôi phục; không silent overwrite.

### Bảo mật tối thiểu

- Chạy local-only mặc định (bind 127.0.0.1); nếu có HTTP import, thực thi giới hạn kích thước, CSRF, content-type, escaping HTML/XSS, không đọc URL từ xa mặc định, không truy cập file ngoài vault do path traversal, không thực thi Markdown/HTML/JS, không follow symlink nguy hiểm.
- Ngăn SQL injection bằng tham số, xử lý file encoding, encoding errors, duplicate, Unicode tiếng Việt/tiếng Anh, lỗi SQLite FTS5 thiếu.
- Phân tách hoàn toàn vault DB và Clinical patient DB. Không tải nhập dữ liệu riêng tư trong demo; cơ chế phát hiện và cảnh báo PHI nếu thiết kế được, nhưng không tự tuyên bố DLP tuyệt đối.

### Bộ dữ liệu nghiệm thu bắt buộc (synthetic, không có PHI)

- Một tài liệu tham khảo giải phẫu kèm citation hợp lệ;
- Một tài liệu giải thích khái niệm huyệt/kinh lạc được gắn đúng namespace và mức xác thực;
- Hai claims mâu thuẫn, cùng tồn tại và truy xuất đầy đủ;
- Một bản ghi nguồn thiếu tác giả/URL, hiển thị `UNKNOWN` thay vì tự điền;
- Một import trùng tệp, một cập nhật có audit history;
- Một tìm kiếm tiếng Việt có dấu và một tìm kiếm tiếng Anh;
- Một doc/claim không được phép hiển thị như `CLINICAL APPROVED`.

**P20 deliverables:** code chạy độc lập; schema/migration; CLI và/hoặc UI; `P20_KNOWLEDGE_VAULT_CONTRACT.md`, `P20_MIGRATION_AND_BACKUP.md`, hướng dẫn thao tác từ copy-paste đến truy xuất, bảng test và bằng chứng; đường liên kết an toàn tới `1docs/EVIDENCE.md`. Nếu starter ZIP thực sự có, giữ cấu trúc/semantics hiện hữu khi khả thi và ghi diff.

---

## 5. P21–P26: Chỉ thiết kế interface, decision backlog và gates, KHÔNG triển khai vượt quyền

Tạo `1docs/ROADMAP_P19_P26_GATED.md` và `1docs/audits/P19/P21_UPSTREAM_FEASIBILITY_REGISTER.md`.

| Milestone | Phạm vi sau khi gate trước đạt | Điểm chặn chính |
|---|---|---|
| P21 Open-Source Modules | Xác thực đúng repo Human Atlas, TARA, `tcm-3d`, tools mesh; clone/pin SHA trong **sandbox cách ly** sau khi xem license; chạy standalone và lập integration adapter plan | Source URL/SHA, code/data license, OS/runtime fit, geometry provenance chưa rõ => `REJECT/DEFER` |
| P22 Anatomical Atlas Repair | Thay hoặc sửa **một** pipeline được chọn cho LI4/ST36/KI3; shared transform source API/UI; witness tests | Chỉ triển khai sau P19 data lineage và reviewer-accepted references; thiếu chuyên gia => `ENGINEERING ONLY` |
| P23 Meridian Reconstruction | Graph waypoints có nguồn, bề mặt và nhánh, tuyến từng kinh, phiên bản/uncertainty | Không coi spline bám da là đúng kinh lạc; cần thẩm định từng tuyến |
| P24 Vault–Atlas Integration | Click huyệt mở evidence/contraindication context/source claims; trạng thái chuyên môn rõ | `UNREVIEWED`/`CONTESTED` không được trình bày như xác nhận/khuyến cáo lâm sàng |
| P25 Clinical Workspace | SOAP/ROM/visits/outcomes synthetic, security/privacy/legal gate riêng | Bệnh nhân thật bị khóa cho đến review pháp lý, consent, RBAC, encryption, audit, backup và operational controls |
| P26 Patient-Specific Anatomy Research | Scale height/limb ratio, posture, landmarks, propagate uncertainty/validation | Không suy ra vị trí huyệt thật từ tỷ lệ cơ thể chung; nghiên cứu không tự chuyển thành treatment guidance |

**P21 evaluation:** phân biệt mã nguồn và asset license; kiểm tra license của model/dataset, restrictions thương mại/phân phối, transitive deps, engine version, offline availability, Windows Intel HD 5500. Pin SHAs, hashes, test commands và PASS/FAIL; không cam kết repo "uy tín" chỉ từ tên gọi.

---

## 6. Gate framework áp dụng cho TỪNG deliverable

**G1 — Functional:** có chức năng thật, có command log và runtime artifacts; mọi enabled UI control tạo thay đổi có thể quan sát.

**G2 — Data Integrity:** dữ liệu có nguồn/hashes/version, lineage đầy đủ, source precedence không mơ hồ, SQLite/JSON/UI nhất quán, không silent overwrite.

**G3 — Domain Validity:** Anatomy/acupoint/meridian/clinical content chỉ được thẩm định bởi người có chuyên môn phù hợp, trên bộ reference và protocol đã ghi nhận; kỹ sư có thể báo `PENDING_EXPERT_REVIEW`, không tự xác nhận.

**G4 — Independent Acceptance:** bằng chứng được người/nhóm **độc lập với implementer** kiểm tra. Agent có thể chuẩn bị evidence pack và đề xuất verdict; nếu chưa có reviewer độc lập, G4=`PENDING`, không gọi tự đánh giá là độc lập.

Báo cáo bắt buộc có các cột:

`milestone | gate | requirement | method | actual evidence path | observed result | owner/reviewer | verdict PASS/FAIL/BLOCKED/NOT_TESTED/PENDING | next action`.

**Verdict tổng:** `ENGINEERING_PASS_SCOPE_LIMITED`, `BLOCKED`, `FAIL`, hoặc `PENDING_INDEPENDENT_ACCEPTANCE`; không ghi `CLINICAL_APPROVED` nếu không có chứng từ kiểm định chuyên môn/hợp quy. Khi bất kỳ G1/G2 thiết yếu fail, không được lên P22; khi G3/G4 pending, không dùng dữ liệu để khẳng định điều trị chính xác.

---

## 7. Test matrix & hostile checks

Tối thiểu phải có:

- **Baseline regression:** chạy tests hiện có, browser/e2e nếu sẵn; ghi không chạy được và nguyên nhân, không giảm số test hoặc skip âm thầm.
- **Coordinates:** unit cm/mm/m, `+X Left/Right`, mirrored laterality, origin offset, matrix ordering, rotations, mesh/hash mismatch, hand/foot region selection, bilateral point identity, stale cache, SQLite override priority.
- **Lineage falsification:** sửa fixture nguồn/transform/override để cố ý làm lệch một giá trị; test phải bắt được; không được cùng một implementation tự làm oracle rồi tự pass.
- **Runtime contract:** source input XYZ → API XYZ → rendered marker position in same canonical frame; ảnh không thay thế numerical assertions. Có ảnh/log/capture thật cho browser khi môi trường cho phép.
- **Vault:** immutable original, repeated import, malformed frontmatter/Markdown, conflicting claims, citation missing, FTS5 disabled, SQL injection, XSS via Markdown, path traversal, export/import round trip, backup-restore, Vietnamese diacritics.
- **Safety regression:** default offline, no PHI, hard stops intact, auth/CSRF, no autonomous diagnostic/treatment/electrical dosing; no accidental live writable API for experimental sources.
- **Performance:** đo memory, load time, FPS theo đúng máy được chạy; nếu không ở Intel HD 5500 thì không gắn nhãn đã nghiệm thu trên phần cứng mục tiêu.

Không tự đặt "100% PASS" cho các hạng mục chưa chạy hoặc tự tạo fixtures chỉ trùng logic production.

---

## 8. Cách tiến hành và thứ tự commit

1. **P19 Discovery**: baseline, inventory, lineage, conflicts, safety preflight. Đưa báo cáo và test reproduction vào riêng một commit không xâm lấn (nếu repo có Git và working tree an toàn).
2. **P19 Contracts**: ADR, source registry, contracts, read-only tracing, negative tests. Mọi thay đổi behavior phải sau approval và feature flag.
3. **P20 MVP trên branch/worktree riêng**: implement SQLite/Markdown import → claims/citations → search → audit → export → integration read-only link; sau đó chạy test thật.
4. **Consolidation**: kiểm tra P19/P20 độc lập, đánh giá xung đột trước merge, cập nhật roadmap gated P21–P26. Không merge `main` hoặc vượt qua gate do tự đánh giá.
5. Chỉ thực hiện P21+ implementation sau khi có quyết định tiếp theo và đủ upstream evidence; trong lần giao việc này **dừng ở P19/P20 và kế hoạch P21–P26**.

Nếu repository hiện tại thiếu hoặc P18 không truy cập được, vẫn hoàn thành những phần **có thể chứng minh** (snapshot audit, P20 standalone) và báo rõ `BLOCKED` cho các hạng mục phụ thuộc live repo. Không ngồi chờ, không giả lập thành công.

---

## 9. Tệp bàn giao bắt buộc

```text
1docs/audits/P19/
  P19_00_BASELINE_AND_EVIDENCE.md
  P19_01_ARCHITECTURE_MAP.md
  P19_02_SOURCE_OF_TRUTH_REGISTRY.csv (hoặc .json)
  P19_03_COORDINATE_LINEAGE.md
  P19_04_RUNTIME_CONFLICT_MATRIX.md
  P19_05_ENGINE_RETIREMENT_ADRS.md
  P19_06_INDEPENDENT_ACCEPTANCE_MATRIX.md
  P21_UPSTREAM_FEASIBILITY_REGISTER.md
  evidence/ (commands, test logs, hashes, runtime captures nếu có)
1docs/audits/P20/
  P20_KNOWLEDGE_VAULT_ACCEPTANCE.md
  evidence/ (import/search/conflict/backup restoration logs)
1docs/ROADMAP_P19_P26_GATED.md
1docs/P20_KNOWLEDGE_VAULT_CONTRACT.md
1docs/P20_MIGRATION_AND_BACKUP.md
knowledge_vault/ (vault sources/docs; local DB gitignored)
msk_therapy_os/knowledge_vault/ (logic độc lập, hoặc path tương đương được giải thích)
tests/ (tests P19 instrumentation/P20 vault)
```

Có thể điều chỉnh tên/đường dẫn để phù hợp convention hiện hữu, nhưng **không được thiếu loại bằng chứng**. Tất cả thay đổi tài liệu phải **append hoặc tệp mới**, không ghi đè mất bằng chứng cũ trong `EVIDENCE.md`, audit reports hay P17/P18.

---

## 10. Định dạng báo cáo cuối của Coding Agent

**A. Baseline thực tế:** branch/commit, trạng thái P18, snapshot hash, số lượng tests **thực chạy** và không chạy.

**B. Sơ đồ kiến trúc:** các module, runtime dependency, dữ liệu/ownership, điểm trùng lặp, keep/deprecate recommendations.

**C. 3-trace Atlas:** LI4/ST36/KI3, đầu vào nguồn, transform, mesh, API, marker, metadata xung đột, bằng chứng/hình ảnh và các `BLOCKED` thực tế.

**D. Knowledge Vault demo:** các lệnh chính xác để người dùng paste Markdown, gán claim/source, tìm kiếm, xem hai claim mâu thuẫn, export và restore trong môi trường local.

**E. Bảng Gate G1–G4:** từng gate có verdict riêng, ai có quyền ký, chi tiết chưa chứng minh.

**F. Code changes:** danh sách file add/modify, commits/diff, backward-compatibility, rollback; source/license register và kết quả security review.

**G. Quyết định tiếp theo:** `GO / CONDITIONAL GO / NO-GO` cho P21; blocker và mức độ ưu tiên để chuẩn bị P22. Không kiến nghị mở rộng toàn bộ 361/362 huyệt trước khi chứng minh 3 mẫu.

**H. Hướng dẫn tái lập:** Windows PowerShell commands từ clean checkout và các môi trường thực sự đã được kiểm tra; ghi expected output chính xác, không tự bịa hiệu năng.

---

## 11. Điều kiện kết thúc nhiệm vụ

Nhiệm vụ lần này hoàn thành khi **(i)** có forensic architecture map + source of truth registry có thể kiểm tra; **(ii)** chứng minh thực tế được các tuyến đang có hoặc chỉ rõ chính xác blocker; **(iii)** P20 Knowledge Vault chạy độc lập và có workflow nhập-tìm-đối chiếu-xuất với audit trail; **(iv)** có acceptance matrix trung thực và backlog có điều kiện P21–P26.

Không chấp nhận một báo cáo chỉ gồm roadmap/README, những test green không kiểm chứng đúng dữ liệu y học, hoặc demo bề mặt 3D đẹp nhưng không truy vết được nguồn.

**BẮT ĐẦU NGAY:** khám phá repository thực tế và file đầu vào, lập `P19_00_BASELINE_AND_EVIDENCE.md`, rồi triển khai P19/P20 theo các giới hạn trên. Tự thực thi những gì có thể thực thi an toàn; không hỏi lại những thông tin đã có trong repository; nếu thiếu dữ liệu hoặc reviewer, gắn `BLOCKED/PENDING` và tiếp tục phần không bị phụ thuộc.
