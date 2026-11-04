# MSK-Therapy-OS — MASTER IMPLEMENTATION PROMPT P21–P26
## Blender Anatomical Studio · Anatomical Source-of-Truth · Constrained Motion Reconstruction · MediaPipe · OpenSim · Clinical Evidence

**Loại tài liệu:** Lệnh thực thi cho Coding Agent trong repository hiện hành.  
**Ngôn ngữ báo cáo:** Tiếng Việt; tên API, schema, tên file, constants sử dụng tiếng Anh.  
**Phạm vi sản phẩm:** `ENGINEERING_RESEARCH_ONLY` — nghiên cứu, giáo dục giải phẫu và kiểm thử chuyển động, **không phải công cụ chẩn đoán hoặc tư vấn điều trị tự động**.  
**Quy tắc chính:** *Có mã chạy thật, dữ liệu thật, bằng chứng thật; không đánh đồng test PASS với chứng nhận giải phẫu/lâm sàng.*

---

## 0. Quyền hạn và điểm bắt đầu

Bạn là **Principal Software Architect + Blender Technical Director + Biomechanics Engineer + Forensic Verification Lead**. Hãy trực tiếp khảo sát, thiết kế, viết code, chạy thử, kiểm thử và bàn giao bằng chứng trong repo đang được người dùng phát triển. **Không chỉ lập roadmap.**

Repo đầu vào: repository **MSK-Therapy-OS thực tế** đang chứa P18/P19/P20 và có thể đã triển khai một phần P21. Tự xác định workspace, branch, HEAD và mọi thay đổi local; **không đoán** đường dẫn, commit, tiến độ từ tài liệu cũ. Ưu tiên đọc trước:

- `1docs/prompts/MSK-Therapy-OS_Coding-Agent_Master-Prompt_P19-P20.md` (nếu có).
- `1docs/prompts/MSK-Therapy-OS_P21_Atlas-Source-and-Viewer-PoC_Agent-Prompt.md` (nếu có).
- `1docs/audits/P18/`, `1docs/audits/P19/`, `1docs/audits/P20/`, `1docs/audits/P21/` nếu tồn tại.
- `1docs/EVIDENCE.md`, registry tọa độ/source-of-truth, `1docs/ARCHITECTURE.md`, file `README.md`, specs về anatomy/meridian/biomechanics; mã runtime hiện hành và tests.

**Những phát hiện lịch sử cần kiểm chứng lại, không coi là dữ liệu runtime đã được xác nhận độc lập:**

- P19/P20 được agent trước báo `ENGINEERING_PASS_SCOPE_LIMITED`; **G3 Domain Validity** và **G4 Independent Acceptance** chưa đạt.
- P19 báo Atlas browser còn fallback `DEMO-BODY` procedural; có bất đồng vị trí LI4/ST36/KI3 và xung đột quy ước `+X Left / +X Right`; đồng bộ ảnh thị giác, API, mesh chưa được chứng nhận chuyên môn.
- P20 có Knowledge Vault Markdown/SQLite, claim/citation/conflict; cần tận dụng, không tạo cơ sở dữ liệu tri thức thứ hai.
- Đã từng thấy đường xử lý camera dùng pose mẫu thay cho khung hình webcam. Nếu còn, phải **chỉ ra rõ mã nguồn và sửa fail-closed**; không được tuyên bố đã thu chuyển động thực khi chỉ dùng TADASANA/placeholder.

**Bất biến an toàn cần giữ nguyên hoặc nghiêm ngặt hơn:**

- `RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY`, `CLINICAL_VALIDATION = NOT_ESTABLISHED`, `clinical_depth_guidance_allowed = False` (xác nhận tên constant thực tế).
- Không đưa hồ sơ bệnh nhân thật vào development, prompt, logs, demo hoặc test.
- Không thay thế, xóa hoặc làm hỏng dữ liệu P18–P20, Atlas/Clinical Workspace đã vận hành, các guardrails, database, static assets.
- Không `git reset --hard`, `git clean -fd`, tự stash làm mất trạng thái, push/merge/deploy, hoặc thay data production; nếu workspace dirty, bảo toàn mọi file và tạo nhánh/sandbox an toàn **chỉ khi có thể làm mà không phá thay đổi hiện có**.
- Không cài thêm pip/npm trong **runtime chính**. Tool phân tích/Blender/motion được phép có môi trường Python **riêng**, lockfile và script thiết lập tường minh.
- Bản ghi `USER_ANNOTATED_UNVERIFIED` không được biến thành `ANATOMICAL_VERIFIED` chỉ vì trùng bề mặt mesh hoặc IK chạy không lỗi.

---

## 1. Quyết định kiến trúc bắt buộc

Dùng mô hình **hai lớp, ba pipeline**, giữ module độc lập:

```text
                       MSK-Therapy-OS (shell / auth / registry / audit)
                         |               |               |
                  Anatomical Atlas   Knowledge Vault   Clinical Workspace
                         |               |          (synthetic-only)
                    IMPORT/EXPORT      evidence link
                         |
        Blender 3.6 Anatomical Studio (desktop AUTHORING, offline)
            |              |               |
       Anatomy assets   Rig/Armature   Manual acupoints/curves/notes
            |              |               |
       asset manifest  Motion Adapter   annotation provenance
                          ^
                  Constrained Motion Solver (sidecar)
                    ^       ^           ^
             Motion Bank  Joint ROM   Pose observations
               (CMU)     Registry     (MediaPipe)
                             |
                 Optional OpenSim/Pose2Sim verification
```

- **Blender 3.6** là công cụ *authoring/editor*, không tự động thay thế giao diện WebGL, Knowledge Vault hay Clinical Workspace. Có thể duy trì 3.6 do hạn chế phần cứng, nhưng ghi rõ EOL và thiết kế adapter không phụ thuộc API riêng của 3.6; không buộc nâng cấp chỉ để đạt demo.
- **Z-Anatomy** là ứng viên nguồn giải phẫu, không phải dữ liệu y học mặc nhiên chính xác. **Tách toàn bộ quyền sử dụng code và quyền sử dụng từng mesh, ảnh, texture, định nghĩa.** Z-Anatomy công bố CC BY-SA 4.0 nhưng liệt kê một số tài sản nguồn NC. **Quarantine tài sản NC/không rõ nguồn**, không đưa vào bundle có thể phát hành. Xem cả ứng viên thay thế có giấy phép thuận lợi nếu cần.
- **CMU Motion Capture Database** chỉ là *motion prior* (mẫu chuyển động quan sát), **không phải chuẩn giới hạn ROM giải phẫu**, không phải tiêu chuẩn an toàn y khoa. Tôn trọng điều kiện sử dụng và không bán lại dữ liệu thô/dạng chuyển đổi như một sản phẩm độc lập.
- **MediaPipe Pose Landmarker** ước lượng 33 landmarks; `normalized_landmarks`/`world_landmarks` là các hệ tọa độ khác nhau, dữ liệu 3D từ một camera vẫn có độ bất định và vùng mù. Không được coi world landmarks là ground-truth 3D hay đo góc lâm sàng được xác nhận.
- **OpenSim** là tùy chọn tính động học/IK và mô phỏng đã có. **Pose2Sim** (Python `>=3.11` theo dự án hiện tại) là pipeline tham khảo/adapter độc lập. Không cài Pose2Sim vào Python nhúng của Blender 3.6; liên lạc bằng file JSON/CSV/TRC/MOT có schema/manifest. Đừng giả định OpenSim visualizer = rig giải phẫu Z-Anatomy hoàn chỉnh.
- MuSkeMo hiện có các bản được kiểm thử trên Blender 4.x/5.x: không yêu cầu chạy trên Blender 3.6 và không được dùng fork không rõ độ tương thích để né test.
- **Không được giới thiệu hay tính toán tải khớp/lực cơ là con số tin cậy** khi chưa chứng minh input, tham số, mô hình và thẩm định độc lập. Render animation ≠ physical simulation ≠ clinical assessment.

### Các nguồn cần audit (không tải bừa toàn bộ hoặc tin README thay runtime)

| Nguồn chính thức | Vai trò dự kiến | Điều phải kiểm chứng |
|---|---|---|
| https://github.com/Z-Anatomy/Models-of-human-anatomy | template/meshes/nhãn cơ thể | Blender 3.6 chạy thực tế, license theo **từng asset**, xuất GLB |
| https://mocap.cs.cmu.edu/ | mẫu chuyển động ASF/AMC hoặc bản quy đổi được cấp phép | quyền dùng, cỡ mẫu, trục, FPS, subject, lỗi tay/ngón |
| https://github.com/perfanalytics/pose2sim | pipeline video/multi-camera → OpenSim | Python >=3.11, dependency, license, DEMO, đường nhập MediaPipe |
| https://github.com/davidpagnon/Pose2Sim_Blender | adapter/visualizer tham khảo | quy trình cài cho Blender <4.4, rig thật hay chỉ visualization |
| https://github.com/google-ai-edge/mediapipe | pose landmarks (sidecar) | model asset/version/license, runtime CPU offline, tin cậy landmark |
| https://opensim.stanford.edu/ | IK/joint mechanics/research | model license, definitions, units, coordinate ranges, runtime khả dụng |
| https://www.slicer.org/ | tùy chọn dữ liệu phân đoạn/đối chiếu mesh | license/nguồn ảnh, anatomy coverage, mô hình scanner và tư thế |
| https://github.com/PashavanBijlert/MuSkeMo | đánh giá tham khảo | yêu cầu Blender version; không làm dependency bắt buộc |

**Tham khảo:**
- Blender 3.6 manual: https://docs.blender.org/manual/en/3.6/ ; EOL: https://www.blender.org/download/lts/3-6/
- MediaPipe task guide: https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker
- OpenSim IK explanation: https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim33/pages/53674149
- CMU FAQ/license: https://mocap.cs.cmu.edu/

Mỗi nguồn ghi: upstream URL, commit/release, ngày kiểm tra, hash, **code license**, **data/asset license**, nguồn phái sinh, yêu cầu attribution/share-alike, điều kiện commercial, phiên bản/test, mức độ tin cậy, blocker. Nếu không truy cập được mạng, ghi `SOURCE_NOT_VERIFIED` và chỉ thực hiện với dữ liệu đã có trong workspace; không bịa hash hoặc commit.

---

## 2. Roadmap mới và thứ tự triển khai (chính thức trong nhánh này)

| Milestone | Chức năng phải làm thật | Cổng trước khi đi tiếp |
|---|---|---|
| **P21 — Blender Anatomical Studio PoC** | Nạp giải phẫu thật có nguồn, show/hide lớp, đánh dấu, vẽ đường, lưu/mở lại, export/import với MSK | Asset hợp lệ + demo Blender 3.6 thực, không procedural thay anatomy |
| **P22 — Anatomical Source-of-Truth & Validation** | Chốt registry mesh/axis/units/landmarks; truy vết LI4, ST36, KI3; bộ kiểm tra độc lập | Không silent transform, 3 vị trí có trạng thái chuyên môn rõ; **G3 không tự PASS** |
| **P23 — Motion Bank + Constrained Rig** | CMU samples có nguồn, armature cánh tay, FK/IK, joint constraints, retargeting và playback | Demo một cánh tay với dữ liệu chuyển động thật, số đo/đồ thị lỗi, test đối chiếu |
| **P24 — MediaPipe Pose Import & Reconstruction** | Video/ảnh thật → landmarks → lọc lỗi → IK có ràng buộc → Blender; xuất uncertainty | Có bằng chứng frame thật, không hardcode; lỗi/occlusion được phát hiện |
| **P25 — Knowledge/Atlas/Motion Integration** | Click cấu trúc/huyệt/khớp → nguồn/claim/giới hạn, lưu note Markdown, dữ liệu synthetic | Truy xuất được nguồn, không đưa claim chưa duyệt thành hướng dẫn điều trị |
| **P26 — Patient-Specific Research (NOT clinical release)** | Nghiên cứu chiều dài chi, calibration, uncertainty và generalization | Thẩm định chuyên môn & độc lập; nếu không có reference data: `RESEARCH_ONLY/BLOCKED` |

**Quy tắc tiến độ:** thực thi **P21 ngay**. Sau khi G1/G2 P21 pass thực, tiếp tục P22 và P23 (song song phần độc lập được). Không cần xin xác nhận lại cho các công việc nghiên cứu/engineering trong phạm vi an toàn. P24 chỉ khi P23 có rig/retargeting functioning, P25 dùng các adapter đã ổn, P26 là nghiên cứu giới hạn và không nâng thành clinical release. Nếu thiếu phần mềm, GPU, data hoặc source: ghi `BLOCKED`, xây **contract/test fixture trung thực** và thực hiện phần không phụ thuộc; không tự đánh dấu nhiệm vụ chính đã hoàn tất. Không tốn nguồn lực làm cả hệ thống mà bỏ qua MVP thực tế.

---

## 3. P21 — Blender Anatomical Studio, deliverable đầu tiên

### P21.0 Preflight + safe checkpoint

1. `git status --short`, `git branch --show-current`, `git rev-parse HEAD`, kiểm tra Python/Blender có sẵn (`blender --version` hoặc tìm executable Windows), CPU/GPU/RAM; ghi output thật và lý do không chạy được nếu thiếu.
2. Inventory cấu trúc repo P18–P20, đọc acceptance/registry; khảo sát P21 cũ nếu đã có, **không tạo duplicate**.
3. Tạo `research/anatomy_studio/` hoặc `tools/blender_anatomy_studio/` theo layout phù hợp hiện tại; giữ core app và DB bất biến. Không overwrite file đã sửa chưa commit.
4. Thiết lập test-runner offline + sha256 + audit text; không có mạng thì không nói là đã clone/verify.

### P21.1 Asset review + source-of-truth

- Clone/download Z-Anatomy trong sandbox `research/upstream/` gitignored, pin release/commit; không thay thế tất cả Atlas assets ngay.
- Liệt kê **từng** mesh và phụ thuộc, anatomy class `BONE/MUSCLE/ORGAN/SKIN/OTHER`, tên cấu trúc, đối xứng trái/phải, axis, units, origin, coordinate frame, transforms, polygon count, file size, hash, nguồn và giấy phép.
- Tránh phát hành asset có `NC` hoặc quyền không rõ; với asset share-alike, ghi rõ hệ quả phân phối derivative; chưa rõ: `QUARANTINED`.
- Dùng dữ liệu giải phẫu thật có licence rõ. Nếu Z-Anatomy không mở trong Blender 3.6 hoặc không có mesh hợp lệ, thử candidate thay thế và ghi tường minh, **không dựng hình procedural để tuyên bố đã sửa Atlas**.

### P21.2 Add-on Blender 3.6 tối thiểu

Tổ chức các module (có thể thay tên nếu tương thích code cũ):

```text
tools/blender_anatomy_studio/
  addon/__init__.py
  addon/layers.py
  addon/annotations.py
  addon/meridian_curves.py
  addon/notes.py
  addon/rig.py
  addon/import_export.py
  contracts/anatomy_asset_manifest.schema.json
  contracts/annotation.schema.json
  contracts/motion_sequence.schema.json
  README.md
  tests/
research/upstream/               # gitignored, chỉ clone/tải asset có kiểm soát
research/motion_samples/         # gitignored nếu có license/size concern
1docs/audits/P21/
```

MVP Blender: mở model gốc; cây anatomy theo tên; bật/tắt/isolating bone/muscle/organ/skin nếu thực có; camera; chọn object; manual marker và đặt tên huyệt; vẽ polyline/curve kinh lạc bằng mouse; sửa/undo/xóa; notes; **save `.blend` và xuất JSON/Markdown rồi import lại đúng vị trí**. Trạng thái mặc định `USER_ANNOTATED_UNVERIFIED`.

**Không chỉ dùng Grease Pencil stroke không metadata** để lưu vị trí. Annotation phải liên kết `asset_id`, `mesh_id`, `mesh_sha256`, `triangle_id`/barycentric hoặc local surface anchor, coordinate frame, transform chain, side, review status, note source, author, timestamp. Khi rig mesh biến dạng, cần có mapping qua parent bone/skin weights/barycentric evaluated mesh tùy mục đích, kiểm tra điểm có trôi không; không đặt annotation ở global XYZ rồi xem là bám giải phẫu.

Xuất 1 gói `JSON + GLB (nếu được cấp phép) + Markdown + manifest`. Dùng bộ schema có `schema_version`, `source_checksum` và migration. Người dùng phải có thể đọc offline. Atlas browser chỉ nhập asset đủ điều kiện và giữ banner provenance rõ; không ghi đè trạng thái P18–P20.

**P21 acceptance tối thiểu:** Blender chạy thực 3.6; có mesh anatomy thật; ẩn/hiện **những** lớp thật tồn tại; 3 markers + 1 đường >=4 waypoint; note tiếng Việt; save/reopen `.blend`; export/import JSON; asset hash và frame không thay đổi; ảnh chụp thật; không tăng permissions runtime chính. Nếu thiếu layers do asset thiếu, không khai PASS cho layer đó.

---

## 4. P22 — Registry và độ đúng giải phẫu (tách khỏi UI)

Thiết lập `Anatomical Source-of-Truth Registry` chung giữa Blender và WebGL, không hồi sinh đa resolver mâu thuẫn:

- `mesh_id`, `mesh_source`, `mesh_hash`, object identity, segmentation label, version, license, provenance.
- `frame_id`, units, handedness, anatomical L/R, forward/up, rest pose; transform matrix (full homogeneous 4×4), source and destination frames, deterministic composition/inverse, numerical roundtrip tests.
- `landmark_id`, method (manual/source/derived), người cung cấp, source document/version, surface attachment, uncertainty, reviewer decision.
- `acupoint_id`, traditional position description with citation, `proposed_anchor`, mesh binding, confidence, status `UNREVIEWED/CONTESTED/REVIEWED` (không đồng nghĩa CLINICAL_APPROVED).

Chọn 3 điểm LI4, ST36, KI3 **trên cùng mesh cùng pose cùng frame**; trace `original source → normalization → transformed location → Blender → export → browser → reimport`. Kiểm soát đảo trục, góc chi/pose khác, scale/mirror, lưỡng nghĩa bên trái/phải. Dùng kiểm chứng hình học *và* tài liệu vị trí huyệt có nguồn; sai số giữa các nguồn không tự xác định bộ đúng, khoảng cách tới skin không chứng minh đúng huyệt. Khi thiếu expert review, gắn `EXPERT_REVIEW_PENDING`. Không dùng ngưỡng `<15mm` một cách tùy tiện để tự chứng minh chính xác huyệt.

Tạo negative tests cố ý đảo trục, lệch scale, mesh đổi hash, pose đổi, waypoint bị mất, annotation sai phía; tất cả phải fail loudly, không silent fallback.

---

## 5. P23 — Motion Bank + Constrained Human Motion (ưu tiên cánh tay)

### P23.1 Motion Bank (không phải ROM Bank)

- Import một tập nhỏ, có chú giải dữ liệu thật từ CMU (gợi ý: gập/duỗi khuỷu, dạng/khép vai, nâng tay, đưa tay ra trước). Không tải cả corpus để có vẻ nhiều dữ liệu.
- Ưu tiên format gốc có nguồn (`ASF/AMC`) hoặc `BVH` chỉ nếu xác minh nguồn chuyển đổi/transform. Lưu original checksum, subject/session/trial, frame rate, units, BVH hierarchy, axis order, rest pose, bone lengths, coordinate convention và số frame bị loại.
- Tổ chức `MotionSequence` frame-by-frame (time, joint angles/rotations, root pose, confidence/quality, source, mapping). Nếu capture không có cổ tay/sấp ngửa hoặc ngón tay thật, ghi `UNOBSERVABLE` — không tự tạo cử động rồi gắn nhãn measured.
- **Không dùng extreme min/max observed trong CMU làm ranh giới giải phẫu.** Motion prior là ràng buộc mềm để gợi ý chuyển động, không thay ROM có nguồn khoa học.

### P23.2 Joint Constraint Registry (hard/soft rõ ràng)

Registry cần có schema:

```yaml
joint_id: left_elbow
kinematic_dofs: [flexion_extension]
axis_frame: local_humerus
units: deg
rom_reference: null       # must be cited before authoritative bounds
rom_context: null         # active/passive, position, demographic scope
bounds_status: UNVERIFIED
hard_limits: null         # no invented clinical limits
soft_prior_id: null       # CMU/motion bank if available
model_assumptions: []
review_status: UNREVIEWED
```

Các DOF vai/phức hợp scapulothoracic, khuỷu, sấp ngửa cẳng tay khác nhau. **Không suy luận sấp/ngửa từ elbow–wrist vector của MediaPipe**; nếu không quan sát được thì `UNOBSERVABLE`. ROM thay đổi theo người, khớp, phép đo, tư thế và tình trạng lâm sàng. Không clamp bừa vào một con số tuyệt đối trên toàn dân số. Constraint mang tính cơ học/numerical và thông tin tham chiếu phải được phân biệt.

### P23.3 Blender rig một cánh tay và retargeting

- Dựng Armature đơn giản `clavicle/scapula (scope documented) → humerus → forearm` và khớp khuỷu có trục/bậc tự do tường minh; bind anatomy bone, rồi nếu khả thi muscles/skin theo hierarchy và weights. Không buộc full-body skeleton.
- Các mẫu: `elbow flexion/extension`, `shoulder flexion/extension`, `shoulder abduction/adduction`; ít nhất 1 trial thật chạy trọn pipeline từ motion capture → normalized sequence → DOF → Blender animation; hỗ trợ playback/scrub/undo.
- Chọn một solver tối giản có kiểm thử FK/IK và constraints bằng Python riêng hoặc Blender native IK; tích hợp OpenSim **chỉ sau** khi model mapping/units có bằng chứng đúng. Không viết mới cả framework dynamics.
- Sau retarget, marker phải giữ tương quan với cấu trúc trong suốt animation, không lật trái/phải, không bone stretch không chủ ý, không đảo khớp/twist phi lý; khi motion không đủ DOF, đánh dấu hạn chế thay vì lấp bằng data được bịa.
- Lưu kết quả ở định dạng mở (`.blend` + JSON + glTF animation hoặc `.mot` tùy khả năng). Có thể chọn `Pose2Sim`/`Pose2Sim_Blender` như *adapter nghiên cứu*, nhưng verify phiên bản hoạt động trên Blender 3.6 và giải quyết vấn đề rig; nếu không tương thích, dùng converter riêng không phải fork ẩn.

### P23.4 Quality metrics và independent test evidence

Test: FK→IK→FK roundtrip với pose synthetic đã biết (numerical only), kinematic root invariants, bone-length invariance, side sign, axis flip, continuity, velocity/acceleration spikes, out-of-range flags, no observation/low confidence, reproducibility after Blender save/reopen. Ghi RMS/per-joint angular error và độ lệch tọa độ trong tập validation **có nguồn chuẩn**; nếu không có ground truth thì `ERROR_NOT_MEASURABLE`, không đặt ngưỡng PASS giả. Dữ liệu sample/trial dùng phát triển phải tách khỏi trial đánh giá.

**P23 acceptance:** có motion sample thật kèm nguồn và hash, animation Blender cho một cánh tay vận hành, IK/retargeting với tests số học, constraints minh bạch, report lỗi có thể tái lập. Không gọi *ANATOMICALLY_VERIFIED* hoặc *CLINICALLY_VALIDATED*.

---

## 6. P24 — MediaPipe → Motion Reconstruction → Blender

### P24.1 Môi trường tách biệt, offline

- `tools/pose_sidecar/` với virtual environment Python tương thích MediaPipe/Pose2Sim, requirements khóa phiên bản và SHA/URL nguồn model; **không dùng pip trong runtime chính hoặc embedded Python Blender 3.6**.
- Chạy offline sau khi dependencies/model hợp lệ đã được provision; nếu cần tải model lúc cài, ghi internet setup-time và runtime offline riêng.
- Input: **ảnh hoặc video có thật** (test sample được cấp phép, không dùng dữ liệu bệnh nhân). Camera live là tùy chọn và phải thực đọc frame với timestamp; không được thay bằng pose mẫu.
- Output: JSON theo `pose_observation.schema.json` gồm `model_id/version/hash`, `source_video_hash`, `frame_id`, `timestamp`, `camera_id`, `image_width/height`, `landmarks_normalized`, `landmarks_world_estimated`, `visibility/presence`, optional calibration, uncertainties, dropped frames, runtime metadata.

### P24.2 Mapping/quality/fail-closed

- Lập bảng ánh xạ `MediaPipe landmark IDs → kinematic model markers`; shoulder/elbow/wrist là landmarks bề mặt suy đoán, không phải anatomical joint centers đo trực tiếp.
- Frame conventions chuẩn: camera coordinate, MediaPipe normalized image, MediaPipe world estimated, Blender local rig, OpenSim model. Có phép transform duy nhất với code và unit tests cho từng cặp. `world_estimated` không được tự nhận là metrically calibrated ground truth.
- Confidence/visibility: reject hoặc giảm weight ở frame occluded; không flip L/R silently; record tracking failures; temporal smoothing có version và log tham số; hiển thị raw vs filtered; nghiêm cấm tự đúc dữ liệu im lặng.
- **MediaPipe single camera không đủ quan sát nhiều DOF/chiều sâu**: lập `OBSERVABILITY_MATRIX`, `UNKNOWN_DEPTH`, `PRONATION_NOT_OBSERVABLE`, `PARTIAL_RECONSTRUCTION`, cho phép feedback multi-view khi cần.
- Dùng motion priors CMU **mềm**, joint constraints có nguồn (hoặc numeric-only theo phạm vi), tối ưu IK; output có thể đánh `ESTIMATED_UNCERTAIN`, kèm residual measurement, confidence, uncertainty flags.
- Import sang Blender và playback cùng 1 video trial, overlay quan sát/ước lượng; khi không có source hoặc không có đủ landmark để solve, **không render pose mẫu giả như pose đo**.

### P24.3 Đối chứng

Chạy 2 lớp kiểm thử:
1. **Synthetic determinism**: chuyển 1–3 poses biết trước qua projection/coordinate transform và giải lại; dùng để tìm lỗi code, không tuyên bố độ chính xác camera.
2. **Recorded clip**: 1 video thực, có source/license, đọc frame thật, output landmarks và animation; nếu có reference angle/goniometer hoặc multi-camera calibrated thì đo MAE/RMSE per joint và confidence coverage. Không có ground truth: `CLINICAL_ACCURACY_NOT_EVALUATED`.

Cần báo cáo latency, CPU, RAM và FPS thực đo; nếu không test trên Intel HD 5500 / RAM 8GB, ghi `TARGET_HARDWARE_UNVERIFIED`. Không tự tuyên bố OpenSim biomechanics validated chỉ vì animation đẹp.

---

## 7. P25 — Liên kết Knowledge Vault và MSK (không tự động chẩn đoán)

- Reuse P20 SQLite/Markdown schema và audit log, **không tách một vault thứ hai**.
- Cho phép click `structure_id`, `joint_id`, `acupoint_id`, `meridian_curve_id`, `motion_trial_id` rồi mở các nguồn trích dẫn liên quan, review status, quality, contradictions, note và provenance. Tài liệu của WHO/OpenSim/tài liệu y học phải được trích dẫn chính xác, không suy ra công dụng điều trị từ tên huyệt.
- Metadata nguồn: title/author/date/version/link/section, claim ID, extraction method, contradiction edges, review status, license, người phê duyệt (nếu có), ngày phê duyệt.
- Export Markdown cho học tập và phản hồi kỹ thuật, **không chứa PII**. Khi nguồn không khả dụng hoặc chưa được thẩm định, hiển thị `UNVERIFIED/CONTESTED` chứ không viết khẳng định y học chắc chắn.
- Clinical Workspace chỉ demo bằng hồ sơ nhân tạo; quyền bệnh nhân thật là gate bảo mật/pháp lý riêng, không scope của nhiệm vụ này. Không tự đưa ra chẩn đoán, quyết định điều trị, chỉ định xâm lấn hay điện trị liệu.

---

## 8. P26 — Patient-specific anatomy research có giới hạn

- Có thể thiết kế calibration ratio (chiều dài chi, chiều cao, mốc đo trực tiếp, pose), hiện uncertainty, compare to reference **research data**.
- Không coi chiều cao hoặc một ảnh là đủ xác định anatomy 3D cá thể. Không hiệu chỉnh huyệt hoặc ROM cho người thật bằng công thức thiếu kiểm chứng.
- Việc cá nhân hóa nào cần IRB/consent/data governance thì chỉ mô tả protocol và làm với synthetic/anonymized, không thu dữ liệu thật.
- Bàn giao framework thẩm định: ground truth reference, observers, inter-rater, bias, MAE/RMSE/limits of agreement per joint/landmark, demographic/pose generalization, limits, uncertainty, G3/G4 independent review. Không có reference => `RESEARCH_ONLY / NO_CLINICAL_GO`.

---

## 9. Interface contracts / persistence / anti-hallucination

Tạo JSON schemas và validators (giữ tương thích standard library nơi có thể):

1. `anatomy_asset_manifest.v1.json`: `source_id`, `asset_sha256`, `license_id`, `license_scope`, `attribution`, `structure_ids`, `frame_id`, `units`, `mesh_transform`, `anatomy_classes`, `review_status`.
2. `annotation.v1.json`: `annotation_id`, `type`, `structure_id`, `mesh_hash`, `triangle/barycentric` hoặc parent/bind coordinate, `transform_version`, `side`, `author`, `source_claim_ids`, `review_status`, `uncertainty`.
3. `joint_constraint.v1.json`: `joint_id`, `dofs`, `axis`, `convention`, `units`, `rom_context`, `rom_source`, `constraint_type`, `bounds_status`, `review_status`.
4. `motion_sequence.v1.json`: `motion_id`, `source_trial`, `fps`, `root_transform`, `rig_version`, `source_skeleton`, `target_skeleton`, per-frame rotations + temporal quality and provenance.
5. `pose_observation.v1.json`: model and data provenance, frame timestamp, normalized/world estimated landmarks, visibility/presence, camera calibration, quality flags.
6. `validation_report.v1.json`: trial IDs, validator/test IDs, result `PASS/FAIL/PENDING/BLOCKED`, measured metrics, units, ground-truth ID, artifact hashes, reviewer and confidence limitations.

**Fail-closed bắt buộc** đối với thiếu mesh, đổi hash, khác đơn vị, đảo trục không xác định, thiếu source/attribution, rig mapping không rõ, marker L/R bất đồng, độ tin cậy thấp, dữ liệu pose bị thay bằng template. UI cần giải thích lý do không thể tính toán thay vì dùng số giả.

Giữ namespace rõ ràng: **`anatomical_mesh`**, **`traditional_acupoint`**, **`biomechanical_joint`**, **`observed_pose`**, **`reconstructed_pose`** không nhập nhằng. API/CLI/Blender/brower phải cùng schema version, unit, frame, hash.

---

## 10. Four independent quality gates, đo được thay vì tô xanh report

| Gate | PASS chỉ khi | Không được coi là PASS khi |
|---|---|---|
| **G1 Functional** | Có UI Blender/brower/runtime thật, input thật, playback, save/reopen, smoke tests và output kiểm chứng | Mocks, ảnh thiết kế, chức năng chỉ nằm trong file code, log được viết tay |
| **G2 Data Integrity** | Source/hash/license/units/frames/IDs/transform xuyên pipeline, no silent fallback/overwrite, roundtrip/boundary tests | Chỉ đúng hình học gần mesh, dữ liệu không rõ nguồn, axis swap ngầm |
| **G3 Domain Validity** | Expert review bằng benchmark/ground truth đúng lĩnh vực, định nghĩa sai số & phạm vi; quyết định được ký thực | Các test số học hoặc code review của chính agent; P19/P20 tự báo PASS |
| **G4 Independent Acceptance** | Reviewer độc lập tái lập trên code/assets/commands và ký kết quả | Agent tự đánh giá lại các test mình tự viết |

**Quyền công bố:** Agent chỉ có quyền báo `ENGINEERING_PASS_SCOPE_LIMITED`, `PARTIAL`, `BLOCKED`, `FAIL` và giữ G3/G4 `PENDING` khi chưa có kiểm toán thực sự. `GO_TO_NEXT_RESEARCH_PHASE` không đồng nghĩa clinical approval hoặc production release.

---

## 11. Validation cases bắt buộc (đầu vào → quan sát → kỳ vọng)

- Asset đổi hash sau khi annotation đã lưu → load báo mismatch và đòi remap, không silently tiếp tục.
- Anatomy trái/phải đảo dấu X hoặc centimeters ↔ meters → phải detect và FAIL.
- Blender rig chuyển elbow 30°/60°/90° synthetic → FK/IK numerical consistency và bone length không trôi; không tuyên bố đây là medical ROM.
- Một motion sample CMU gốc có real frames → xuất `motion_sequence`, Blender playback và save/reopen không đổi relative joint motion.
- Landmark elbow bị che khuất 15 frames → chất lượng giảm, có missing/occlusion markers, không tự tạo pose chắc chắn.
- Video source không tồn tại hoặc camera service chỉ dùng placeholder → explicit `NO_OBSERVATION`, không xuất báo cáo clinical.
- Input có left/right mismatch → fail/flag, không auto mirror vì dễ làm sai huyệt/khớp.
- Tách license compliant và NC asset → NC bị quarantine, output bundle không lẫn asset NC.
- Import annotation về WebGL và đưa lại Blender → roundtrip positions/IDs/hash trong ngưỡng số học định nghĩa trước, ghi sai số đo, visual screenshots thật.
- Regression của P18/P19/P20 không bị gãy: thống kê chính xác test đã chạy, test chưa chạy. Browser test chưa thực hiện = `NOT_RUN`, tuyệt đối không ghi 24/24 pass nếu mới chạy 1.

Báo cáo dữ liệu lỗi/benchmark *không được làm sạch dấu vết* bằng cách drop bad frames hay filtered anomalies mà không log.

---

## 12. Artifact layout / báo cáo bắt buộc

Không bịa file đã tạo; thực hiện đến đâu nộp đến đó. Tạo thư mục tương ứng, không làm đổi cấu trúc cũ khi không cần.

```text
1docs/audits/P21/
  P21_00_PREFLIGHT.md
  P21_01_SOURCE_LICENSE_ASSET_MATRIX.csv
  P21_02_BLENDER_36_COMPATIBILITY.md
  P21_03_ANATOMY_STUDIO_POC.md
  P21_04_DEMO_AND_EVIDENCE.md
  P21_05_GATES.md
1docs/audits/P22/
  P22_01_COORDINATE_AND_LANDMARK_REGISTRY.md
  P22_02_LI4_ST36_KI3_LINEAGE.md
  P22_03_TEST_MATRIX.md
1docs/audits/P23/
  P23_00_MOTION_UPSTREAM_REGISTER.md
  P23_01_MOTION_BANK_SCHEMA_AND_SAMPLES.md
  P23_02_ARM_RIG_MAPPING_AND_CONSTRAINTS.md
  P23_03_IK_RETARGETING_AND_METRICS.md
  P23_04_PLAYBACK_BROWSER_BLENDER_EVIDENCE.md
  P23_05_GATES_GO_NO_GO.md
1docs/audits/P24/
  P24_01_MEDIAPIPE_MODEL_AND_CAMERA_PIPELINE.md
  P24_02_OBSERVABILITY_MATRIX.md
  P24_03_RECONSTRUCTION_AND_VALIDATION.md
  P24_04_GATES.md
1docs/audits/P25/
  P25_KNOWLEDGE_INTEGRATION_AND_EVIDENCE.md
1docs/audits/P26/
  P26_PATIENT_SPECIFIC_RESEARCH_PROTOCOL.md
1docs/audits/ROADMAP_P21_P26_STATUS.md
```

Cần có tests, fixtures (synthetic vs genuine tách riêng), source/asset manifests, logs, screenshots hoặc video chạy thật, `.blend` PoC (nếu có và được phép phân phối), setup scripts PowerShell và Linux (nếu dùng), instructions offline, CLI commands, dữ liệu sample có license hoặc link chính thức + hash, reproducibility. Lưu sample lớn trong gitignored/cache và publish manifest thay vì nhét nhị phân vào Git.

**Mỗi milestone báo cáo**: trạng thái, file mới/sửa, hash/commit, commands chạy thật + exit code + output, demo thao tác thực, FPS/RAM/hardware thực đo (hoặc NOT_TESTED), test pass/fail/skip, known limitations, G1–G4, blockers, rollback, GO/CONDITIONAL_GO/NO_GO.

---

## 13. Định nghĩa DONE cho bản demo đầu tiên, và lệnh hành động

### MVP tối thiểu (thứ tự ưu tiên — phải hoàn thành trước khi mở rộng)

1. **P21**: Blender 3.6 mở được **model thật được phép sử dụng** và hide/show cấu trúc; đặt 3 huyệt thủ công và 1 đường ít nhất 4 waypoint; lưu `.blend`, JSON, Markdown và mở lại khớp; provenance đầy đủ.
2. **P22**: Khớp/ghi rõ mapping mesh coordinate và anatomy left/right; trace LI4/ST36/KI3, không tự xác nhận vị trí y học.
3. **P23**: Rig **một cánh tay**; nạp **ít nhất một trial motion capture thật**; phát animation gập/duỗi khuỷu và ít nhất một chuyển động vai với constraints; có quantitative code-level tests và evidence.
4. **P24**: Dùng **một video thực** qua MediaPipe, import landmarks thành animation cánh tay, log confidence và giới hạn quan sát; không fake pose từ sample cứng.
5. **P25+P26**: Liên kết Knowledge Vault và viết validation research protocol, không đưa ra clinical advice hoặc patient-specific intervention.

### Lệnh đầu tiên bắt buộc

1. Tạo `1docs/audits/P21/P21_00_PREFLIGHT.md` sau khi chạy preflight trên repository thực tế.
2. Đọc P19–P20 và P21 cũ, đối chiếu actual code/features/tests, không làm trùng các adapter đã có.
3. Tạo `P21_01_SOURCE_LICENSE_ASSET_MATRIX.csv`, xác minh Blender 3.6 và nguồn Z-Anatomy. Nếu thiếu Blender/asset, ghi rõ blocker và dựng schema/test/CLI độc lập cho các phần không bị chặn.
4. **Implement code**, chạy Blender pipeline, export/import, ghi evidence thật. Không dừng sau bản kế hoạch.
5. Theo gating tuần tự ở mục 2, đi tiếp P22/P23/P24 nếu điều kiện đã đạt. Báo cáo tiến độ ở từng gate; không tự merge hay push.
6. Cuối cùng đưa báo cáo ngắn tiếng Việt: *đã chạy thật điều gì, chưa chạy được điều gì, bằng chứng nằm ở đâu, lệnh để tôi tự mở demo, điểm quyết định tiếp theo là gì*.

**Nhắc lại:** Đầu ra phải là hệ thống có thể kiểm chứng. Chuyển động mượt không chứng minh khớp đúng; bám mesh không chứng minh huyệt đúng; code PASS không chứng minh hiệu lực điều trị. Tiến hành ngay, không chỉ diễn giải cách thực hiện.
