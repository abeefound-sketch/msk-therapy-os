# MSK-THERAPY-OS V1.0 — PRODUCT COMPLETION MASTER IMPLEMENTATION PROMPT

> **Giao cho:** Principal Software Architect + Blender 3.6 Technical Director + Computational Anatomy / Rigging Engineer + WebGL Engineer + QA & Data Provenance Auditor
>
> **Repository hiện hành:** `D:\5Projects\msk-therapy-os`
>
> **Ngôn ngữ báo cáo:** Tiếng Việt. **Phạm vi:** `ENGINEERING_RESEARCH_ONLY` / `CLINICAL_VALIDATION = NOT_ESTABLISHED`.
>
> **Tài liệu này tự đủ để triển khai; không bắt buộc phải có prompt P34–P37 cũ.** Bắt đầu từ repository thực tế, KHÔNG tạo một ứng dụng mới để né các lỗi của MSK-Therapy-OS hiện hành.

## 0. MỆNH LỆNH SẢN PHẨM: NGỪNG TĂNG MILESTONE, HOÀN THÀNH V1.0

Chuyển từ chuỗi các milestone kỹ thuật P18–P37 sang **năm work package có cổng nghiệm thu sản phẩm**:

- **A — Atlas Foundation:** lớp giải phẫu có nguồn, một định danh cấu trúc thống nhất, khung tọa độ/đơn vị, chọn/ẩn/hiện cấu trúc bằng UI thật.
- **B — Parametric Body:** điều chỉnh hình thể bằng slider, biến dạng da và cập nhật những cấu trúc xương/khớp có thể hỗ trợ một cách có kiểm soát.
- **C — Dynamic Acupoints & Meridians:** điểm/đường neo vào đúng cấu trúc và biến đổi theo morph + pose; chỉnh tay, versioning, undo, provenance.
- **D — Motion Integration:** kéo/điều khiển tư thế bằng chuột và nhập video qua MediaPipe; **WebGL mesh thật phải chuyển động**, không chỉ con số DOM.
- **E — Unified Product:** một giao diện thao tác, truy xuất Knowledge Vault, lưu/mở dự án và kiểm thử E2E trên phần cứng mục tiêu.

**Ưu tiên:** A → B → C → D → E về phụ thuộc dữ liệu, nhưng xây **một vertical slice xuyên suốt** từ đầu để bắt lỗi giao diện và xuất dữ liệu sớm. Không coi mô hình toàn thân đã hoàn thiện là điều kiện để làm một bản demo hữu ích.

**Vertical slice đầu tiên:** vai phải → cánh tay phải → cẳng tay phải → bàn tay phải với LI4 (và LI14/LI15 nếu có dữ liệu phù hợp), một bề mặt da đã được đăng ký với xương, một bộ slider có hiệu ứng hình học rõ ràng và một chuỗi 100 frame từ video thật. ST36/KI3 ở mô-đun chân riêng, không được gắn giả lên tay. Đích dài hạn: toàn thân nhiều lớp; V1.0 chỉ được công bố đúng phạm vi đã hoạt động.

## 1. BASELINE ĐÃ ĐƯỢC BÁO CÁO, CHƯA ĐƯỢC COI LÀ BẰNG CHỨNG MỚI

Tại báo cáo P34–P37 do chủ dự án cung cấp:

- Git HEAD báo cáo `4990f173a880e8a671c0622a04dd88c67264679c`; working tree chứa các thay đổi chưa commit. Không giả định Git HEAD phản ánh đầy đủ thành quả P37.
- Windows 11, i7-5600U / Intel HD 5500 / 8 GB RAM; Blender 3.6.5 LTS; Python 3.11 với MediaPipe sidecar.
- `tools/extract_bp3d_meshes.py` được báo cáo đã trích xuất xương từ `3refs/upstream/tcm-3d/public/models/body-13.bin`.
- Có `anatomy_asset_registry.py`, `surface_anchor_registry.py`, `rig_binding_adapter.py`, `motion_comparison_harness.py`, `headless_p35_full_limb_binding.py`.
- Có scene `1docs/audits/P35/evidence/p35_full_limb_binding.blend`; motion thật `research/motion_samples/real_human_motion_cam01.mp4` và chuỗi dữ liệu P28.
- LI4 được gắn ở Metacarpal_2_R trong scene nghiên cứu; ST36 và KI3 có xương đã trích xuất nhưng chưa rig chân; toàn bộ vị trí huyệt vẫn chờ thẩm định chuyên môn.
- P34 phát hiện **Web Atlas chỉ đổi con số timeline/text, chưa cập nhật geometry động**; P37 mới thêm nhãn cảnh báo `WEB_MOTION_GEOMETRY_NOT_CONNECTED`, chưa chứng minh đã khắc phục.
- P36 báo `ACCURACY_NOT_ESTABLISHED` do thiếu ground truth; residual retarget không phải sai số trên người thật.
- P37 báo 114/114 kiểm thử PASS, G1/G2 PASS trong phạm vi kỹ thuật, G3/G4 PENDING. Phải tái kiểm chứng, không tự nâng cấp G3/G4.
- Kho tri thức thực: `knowledge_vault/vault.db`; database vận hành khác: `msk_therapy_os.sqlite3`. Không tự hợp nhất DB, không ghi đè dữ liệu hiện tại.

**Preflight bắt buộc:** `git status --porcelain=v1`, `git rev-parse HEAD`, liệt kê diff, xác minh tồn tại/hash bản gốc, kiểm tra lệnh test, kiểm tra Blender executable, Web Atlas entrypoint, scene/mesh, sidecar và CSDL. Ghi rõ `OBSERVED / CLAIMED / NOT_REPRODUCED / BLOCKED` trong `1docs/product_v1/audits/V1_00_BASELINE.md`. Sao lưu trước mọi migration. Không reset/stash/delete/push/merge/deploy.

## 2. NGUYÊN TẮC CÔNG NGHỆ VÀ OPEN-SOURCE REUSE

**Đánh giá repo có sẵn trước khi tự viết.** Dùng bản commit/tag cố định, lưu URL, SHA và asset-level license trong manifest. Không tải dữ liệu tùy tiện nếu xung đột license; không trộn license theo suy đoán.

| Nguồn | Cách dùng được phép khảo sát | Điều kiện bắt buộc |
| --- | --- | --- |
| BodyParts3D / asset đã có | Cơ sở xương/cơ và định danh cấu trúc hiện hành | Kiểm tra giấy phép **asset cụ thể** và quyền phân phối trước khi export/bundle. Không suy từ tên repo ra license của mọi mesh. |
| Z-Anatomy | Anatomical structures, naming, visual reference, Blender template | CC BY-SA 4.0 cho nguồn tổng thể; một số asset tham chiếu có điều khoản NC khác nhau. Quarantine phần không tương thích. |
| MakeHuman (ứng dụng độc lập) | Tạo bề mặt cơ thể tham số hóa, xuất kiểu OBJ/DAE/FBX hoặc format được chứng minh tương thích | Core assets CC0, mã ứng dụng AGPL; không gộp source AGPL vào sản phẩm tùy tiện. Đo và chứng minh pipeline export/import thực tế. |
| MPFB2 | Nghiên cứu khả năng, **không sử dụng trực tiếp trên Blender 3.6** | Tài liệu chính thức yêu cầu Blender ≥4.2. Không silently upgrade máy hoặc ép cài. |
| SMPL-X | Chỉ đánh giá trong nghiên cứu cách ly nếu hữu ích | Giấy phép academic/non-commercial, hạn chế phân phối; không thành dependency của bản có mục tiêu thương mại nếu thiếu quyền. |
| Blender 3.6 + bpy | Rigging, shape keys, binding, exporter, batch test | Duy trì compatibility Blender 3.6, không đòi người dùng tự thao tác GUI. |
| MediaPipe sidecar / CMU / OpenSim | Tái sử dụng P28–P36, motion bank, IK | Giữ sidecar độc lập, license từng video/motion, giữ `ACCURACY_NOT_ESTABLISHED` khi không có ground truth. |
| Three.js / Web Atlas hiện có | Render skinning, morph targets, animation, picking | Tái sử dụng WebGL đang có; nếu chuyển sang glTF 2.0, phải kiểm tra `SkinnedMesh`, `AnimationMixer`, morph weights và Blender export trên hardware 8GB. |

**Feasibility gate cho MakeHuman:** thử độc lập một cơ thể có hai hình thể, import sang Blender 3.6 không mất thang đo, topology, skeleton alignment và license metadata. Nếu thất bại, **không chặn toàn dự án**: triển khai slider có phạm vi nhỏ trên mesh skin được cấp phép và hỗ trợ shape keys/parametric deformation đã kiểm thử, ghi rõ `FALLBACK_DEFORMATION_APPROXIMATION`. Không tự nhận đó là mô hình bệnh nhân thật.

**Không được:** chuyển dữ liệu xương/cơ Z-Anatomy sang hình thể MakeHuman bằng scale XYZ toàn cục rồi gọi là anatomical registration; coi một slider “body fat” tương đương độ dày mỡ dưới da của cá nhân; dùng AI sinh mesh không nguồn và đưa vào trạng thái verified.

## 3. KIẾN TRÚC MODULE / HỢP ĐỒNG THỐNG NHẤT

Giữ MSK-Therapy-OS là shell và Knowledge Vault làm kho tri thức. Tổ chức module dưới các thư mục phù hợp với repository thực tế, tránh duplicate engine; có thể dùng tên sau nếu chưa tồn tại:

```text
msk_therapy_os/
  anatomy/               # reference frames, anatomical ID registry, asset provenance
  body_parametric/        # morph params, deformation/registration adapters
  dynamic_anchors/        # acupoints, meridian waypoints, reattachment/versioning
  motion_bridge/          # existing motion sequence, pose & rig mapping
  project_io/             # schema, save/open, migration, manifest
  knowledge_vault/        # existing implementation: reuse, don't fork
msk_therapy_os/static/atlas/  # unified interactive viewer + product controls
 tools/blender_anatomy_studio/ # existing Blender 3.6 bpy scripts/addon
 tools/pose_sidecar/          # existing MediaPipe runtime
1docs/product_v1/            # status, contracts, QA, evidence
```

Mọi dự án chứa **ModelAsset + BodyParameters + JointHierarchy + StructuralMapping + SurfaceAnchors + PoseSequence + KnowledgeRefs + Provenance + ReviewState**. Định nghĩa schema version rõ ràng. Hợp đồng tối thiểu:

- `source_asset_id`, asset URI/reference, SHA256 immutable of **base asset**, legal provenance, coordinate system, units, L/R.
- `anatomy_structure_id`, upstream FMA/BodyParts3D identifiers nếu có và được xác minh; `segment_id`, `rig_bone_id`.
- `body_parameter_id`, value, valid range, rendering-only vs research-estimated type, source/uncertainty, `morph_version`.
- `landmark_id` và `surface_anchor` (face id + barycentric on a stable mesh, hoặc registered landmark frame), `reference_mesh_version`, local transform, normals, review state.
- `motion_id`, frame timestamp, observable vs estimated, transform convention, source/video hash.
- `project_id`, schema_version, data refs, scene/mesh hash, event log, user corrections.

Phân biệt **base mesh hash** và **derived/morphed mesh hash**; morph hợp lệ không được báo lỗi stale base asset. Nếu topology thay đổi khiến face id không còn hợp lệ, bắt buộc remap có bằng chứng hoặc `ANCHOR_REVIEW_REQUIRED`. Chống double transform theo thứ tự chuẩn: `Base Anatomy → Body Morph & Registration → Anchor Recompute → Pose/Rig → Render`, với vị trí sau morph+pose lưu riêng world-space và local-space.

Mọi cập nhật phải có version/undo và khả năng quay lại preset gốc. Nếu không thể đăng ký cấu trúc thì giữ nguyên cùng nhãn `UNREGISTERED`, không nắn bừa cho trông đẹp.

## 4. WORK PACKAGE A — ATLAS FOUNDATION

### Triển khai

1. Audit tất cả mesh thực sự có: skin, bones, muscles, organs, tendon, nerve; phân biệt **available / inferred / missing**.
2. Dựng `AnatomyAssetRegistry` chuẩn và mapping giữa BodyParts3D, Blender rig, Three.js scene, Knowledge Vault; giữ metadata license trong mọi export.
3. Tạo một demo vùng phải vai→bàn tay gồm **mesh xương đã chứng minh nguồn** và **bề mặt da độc lập**. Nếu thiếu da tương thích, lấy skin từ MakeHuman/nguồn hợp lệ qua feasibility gate.
4. Cung cấp UI Web Atlas bật/tắt lớp BONE / MUSCLE / SKIN / ORGAN chỉ khi có thật; chọn được mesh để xem ID, nguồn, license, trạng thái.
5. Hỗ trợ rotate/zoom/pan/select; hiển thị màn hình khuyết thiếu trung thực thay vì procedural anatomy giả.

### Acceptance A (runtime)

- Browser Chromium mở được 3D scene có geometry thật; toggle đổi visibility của object thật; chọn mesh được đúng ID + metadata; không chỉ cập nhật text.
- Một asset thiếu không được tự tạo placeholder và gắn nhãn verified.
- Export Blender→Web giữ đúng topology/axis/unit/laterality trong tolerance đã quy định.

## 5. WORK PACKAGE B — PARAMETRIC BODY & ANATOMICAL REGISTRATION

### Triển khai

**Ưu tiên ba slider có thể quan sát:** `height_scale` / `right_arm_length_ratio` / `right_arm_circumference_visual`. Nếu feasible, bổ sung `regional_soft_tissue_appearance` với nhãn **visual approximation only**; không gắn slider “fat” với mm mỡ bệnh nhân.

1. Tạo `BodyParameters` và preset `baseline`, `slender`, `broader`, `longer_arm` có giá trị rõ ràng. Giới hạn phạm vi dựa trên bộ asset và tính ổn định hình học, không đại diện ROM hay quần thể y học.
2. Dựng MakeHuman independent-export adapter nếu thử nghiệm chứng minh tương thích; KHÔNG yêu cầu MPFB2 Blender 4.x.
3. Tạo `AnatomicalRegistrationAdapter`: khớp các anatomical landmarks tin cậy, segment-specific transforms, joint pivots, local coordinate frames; phân biệt xương rigid scaling/placement và soft-tissue deformation.
4. Khi kéo slider trong **Web Atlas**, geometry/skin phải thực sự thay đổi hình dạng. Sử dụng morph targets/shape keys hoặc deform in-place có kiểm soát; không chỉ resize toàn scene hay đổi label.
5. Cập nhật bone positions, joint centers và registration state; kiểm tra mesh penetration, gãy mesh, gaps, inverted normals, unrealistic topology, xương bị kéo thành cao su. Cho phép trạng thái `REGISTRATION_UNCERTAIN`.
6. Chứng minh preset lưu và hồi phục, chuyển nhanh giữa preset không tích lũy sai số, mỗi lần morph là deterministic trên cùng base asset.

### Acceptance B

- Tối thiểu 3 slider UI tác động thật lên vertices và hệ khớp tương ứng; before/after có vertex hash/distance/bounding box và screenshot kiểm chứng.
- Height và length là thay đổi tỷ lệ trình diễn theo reference frame rõ ràng; circumference chỉ được coi là hình thể trực quan nếu thiếu volumetric model.
- Khi trở về baseline, sai lệch mesh so với baseline dưới tolerance đã công bố, không drift sau ≥20 vòng slider qua lại.
- Không dùng một mesh hoàn toàn mới khiến toàn bộ anchor mất đi mà không thông báo/reproject.

## 6. WORK PACKAGE C — DYNAMIC ACUPOINTS & MERIDIANS

### Triển khai

1. Xây `DynamicAcupointRegistry`, `MeridianWaypointRegistry` kế thừa P19–P37. Phân biệt `BONE_LANDMARK`, `SKIN_SURFACE`, `MANUAL_ANNOTATION`, `DERIVED_UNVERIFIED`.
2. LI4 được neo vào cấu trúc tay phù hợp theo lineage hiện có, **không gắn trực tiếp vào humerus**; khi body morph, điểm 3D phải tính lại theo registration và bề mặt mục tiêu. Neo lên xương không được coi là đã định vị đúng vị trí huyệt trên da.
3. LI14/LI15 chỉ hiển thị mức thẩm định đã được chứng minh trong bằng chứng hiện có; không tự phong `ANATOMICAL_VERIFIED`.
4. Đường kinh là đường trình diễn có waypoint; mỗi waypoint có nguồn và segment, không tự tạo tuyến để lấp khoảng trống trên cơ thể mới mà gắn nhãn đã chuẩn hóa.
5. UI click để đặt/sửa vị trí mốc; drag/undo/redo, ghi tác giả/nguồn/trạng thái/morph version; sau morph → pose → reload vẫn đồng bộ.
6. ST36/KI3 hiển thị mô tả + trạng thái `RIG_OR_SURFACE_UNAVAILABLE` nếu chưa có rig/skin chân; tuyệt đối không mô phỏng chúng trên chi trên.
7. Cơ chế cảnh báo với morph cực đoan: `NEEDS_MANUAL_REVIEW`, có manual override riêng, không ghi đè dữ liệu gốc.

### Acceptance C

- LI4 và ít nhất một waypoint được neo đúng vùng được hỗ trợ, chịu tác động đồng thời morph + pose.
- Các anchor phải thay đổi **world coordinate** có lý do, nhưng giữ local/barycentric invariant khi topology ổn định. Thử sai left/right, hash, face id, parent segment, order of transforms.
- Lưu/mở lại đúng vị trí và lịch sử sửa, không có dịch chuyển âm thầm.
- UI hiện tên huyệt, nguồn, `EXPERT_REVIEW_PENDING`; không suy diễn độ sâu châm hay chỉ định điều trị.

## 7. WORK PACKAGE D — REAL MOTION IN WEB VIEWER + MOUSE POSE

### Triển khai

**Đây là blocker sản phẩm quan trọng nhất từ P34:** Web Atlas mới cập nhật DOM numbers nhưng **chưa chuyển mesh 3D**. Bắt buộc sửa nó, không được chỉ dựng một trang demo tách biệt.

1. Kết nối scene/rig/morph đã tạo từ Blender 3.6 sang Web Atlas hiện hành bằng GLB/glTF + `SkinnedMesh`/`AnimationMixer` hoặc pipeline đã có bằng dữ liệu transform có contract. Lưu inverse bind, bone hierarchy, transform/coordinate conventions.
2. Từ sequence MediaPipe P28 (video 100 frames), khi Play/slider timeline, **vertices của mesh xương/da và marker trên Canvas thực sự đổi vị trí**; ảnh/video ghép frame/timestamp dùng được làm evidence.
3. Hỗ trợ mouse pose trong Web Atlas: chọn segment và kéo một handle để điều chỉnh ít nhất shoulder elevation/elbow flexion; use IK/FK arbitration rõ ràng, clamp constraints và không nhảy pose khi đổi mode.
4. Giữ nhất quán khi body đã morph: blend skinning + shape keys theo đúng thứ tự; marker bám cấu trúc; đường kinh update; không thay đổi bone lengths do animation trừ khi model parameter thực sự chỉnh length.
5. Gắn nhãn `ESTIMATED` cho tư thế từ một camera, `UNOBSERVABLE` cho forearm axial pronation/supination khi thiếu tín hiệu; không tự sinh accuracy/clinical claims. Giữ OpenSim/Pose2Sim optional, không bắt buộc làm lại.
6. Đo render FPS ở browser thực (requestAnimationFrame/WebGL) trên Intel HD 5500 và peak RAM trong runtime thật; tách biệt headless Blender depsgraph throughput và WebGL visible FPS.

### Acceptance D — MUST PASS

- Ở cùng timestamp F1/F50/F100, đo/ghi **object matrix / skin vertex world-space positions** trên Web Canvas; chúng phải thay đổi phù hợp scene Blender tham chiếu trong tolerance đã định nghĩa. Không chỉ DOM đổi số.
- Pose kéo chuột tạo hình học khác rõ ràng và reproducible; ảnh before/after, browser test + video/gif capture nếu sẵn có.
- Sau morph, playback chạy, không mất binding, anchor không trượt do lỗi phần mềm.
- Nếu browser không thể chạy skinned meshes vì hạn chế máy, cho phép *degraded mode* công khai, nhưng **không PASS D**.

## 8. WORK PACKAGE E — UNIFIED PRODUCT, KNOWLEDGE & PERSISTENCE

### Triển khai

Xây trong giao diện MSK-Therapy-OS hiện có, không yêu cầu người dùng mở Blender để sử dụng hằng ngày. Blender là tác vụ xây dựng/biên tập asset nội bộ cho Coding Agent.

Panel cơ bản: (1) Anatomy Layers, (2) Body Parameters/Preset, (3) Acupoint/Meridian Edit, (4) Pose Timeline/Mouse/Video Import, (5) Knowledge/Evidence, (6) Save/Open/Export. Tối ưu UI khả dụng ở màn hình 1366x768 và phần cứng 8GB.

- Click LI4 → thông tin giải phẫu có nguồn, liên kết note trong `knowledge_vault/vault.db`, claim conflicts/verification status; không dùng DB rỗng khác.
- Save project thành **portable manifest** + các asset refs/hashes + body params + anchors/versions + motion refs + notes; write atomically; re-open deterministic. Không đóng gói dữ liệu nhạy cảm; không overwrite original files.
- Có một lệnh start trên Windows để người dùng vào đúng Web Atlas; mọi pipeline backend/Blender/sidecar có script tự động cho Coding Agent, không yêu cầu học Blender.
- Không cần hoàn thiện Clinical Workspace, chẩn đoán tự động hay multi-patient system trong V1.0.

### Acceptance E — USER ACTION TEST

Người dùng không viết code thực hiện được trên một giao diện:

1. Khởi động → thấy người 3D thật và lớp xương/da.
2. Tắt/bật xương/da → geometry thay đổi hiển thị.
3. Kéo slider chiều dài tay/vóc dáng → hình thể đổi thật.
4. Click LI4 và xem cảnh báo chuyên môn.
5. Chỉnh LI4 thủ công → undo/redo → marker đúng sau morph.
6. Kéo cánh tay bằng chuột, hoặc Play sequence MediaPipe → 3D mesh chuyển động.
7. Mở tài liệu liên quan trong Knowledge Vault.
8. Save → đóng app → reopen → khôi phục đúng morph, pose, marker, ghi chú.
9. Xuất Markdown gồm parameters, nguồn, uncertainties và trạng thái kiểm chứng.

Mỗi bước có browser evidence, log và *observable scene graph/vertex change*. Chỉ HTTP 200 hoặc DOM text không đủ để PASS.

## 9. CHIẾN LƯỢC TRIỂN KHAI THEO RỦI RO

**Bước 0 — Freeze + Product Gaps (ngay):** inventory P18–P37, audit repo/asset/license/compatibility/DB; tạo `V1_00_BASELINE.md`, `V1_01_PRODUCT_GAP_MATRIX.md` và nguồn bằng chứng. Không sửa gì ngoài blocker cần thiết trước khi hiểu trạng thái hiện tại.

**Bước 1 — Vertical Slice 0 (sửa blocker WebGL):** dùng rig/scene P35 với một morph cực nhỏ hoặc baseline; xuất/đưa được **geometry động** vào Web Atlas. Đây là mục chặn. Nếu thất bại, ghi `PRODUCT_BLOCKED`, không tô đẹp bằng UI giả.

**Bước 2 — Atlas + Parametric Feasibility:** A/B. Test MakeHuman độc lập với Blender 3.6, so với fallback shape-key. Quyết định dựa trên bằng chứng asset có sẵn và vận hành 8GB. Không cố fork cả MakeHuman chỉ để xuất một mesh.

**Bước 3 — C/D Integration:** Anchor có nguồn → morph → pose, manual edits & versioning. Video import optional sau khi scene geometry WebGL chạy ổn từ motion sequence sẵn có.

**Bước 4 — E Completion:** API/project persistence/Knowledge Vault + browser product acceptance. Sau đó mới cân nhắc UI toàn thân và chân.

Agent được phép tự triển khai đến khi hết điều kiện làm việc thực tế; không hỏi thêm các quyết định đã ghi ở đây. Nếu một dependency bị BLOCKED, làm tiếp phần độc lập và chỉ rõ tỉ lệ/điều kiện chưa thể đạt. Ưu tiên xây code chạy được hơn là tạo roadmap mở rộng.

## 10. CHẤT LƯỢNG / SAFETY / LICENSING / ACCEPTANCE

Bốn gate cần giữ độc lập:

- **G1 Functional:** runtime thực: Blender scene, WebGL scene, sliders, animation, edit, save/reopen.
- **G2 Data Integrity:** trục/đơn vị/parent/hashes/asset licenses/anchors/version/DB provenance không mất qua export/import.
- **G3 Domain Validity:** reviewer giải phẫu/YHCT/bio-mechanics thẩm định trong phạm vi phù hợp. Chưa có thì PENDING. Bề mặt bám đúng không đồng nghĩa huyệt chính xác; morph không đồng nghĩa ảnh chụp bệnh nhân.
- **G4 Independent Engineering Acceptance:** QA/auditor độc lập không thuộc nhóm triển khai, tự tái lập từ source/artifacts. Không trộn với thủ tục pháp lý thiết bị y tế. Agent nội bộ có thể chuẩn bị **review packet** nhưng không tự nhận G4 PASS.

**Nghiêm cấm:** dùng generative AI mesh như ground truth; gắn cấu trúc không có nguồn và gọi verified; tự tính độ sâu huyệt/chiều dày mỡ thực; tự suy từ tư thế sang chỉ định chữa bệnh; dùng video không rõ consent/license; giả lập test thay runtime; bịa benchmark; chạm dữ liệu bệnh nhân; thay đổi safety flags; phát hành thương mại khi asset license chưa giải quyết.

**Đo hiệu năng:** browser WebGL FPS khi render thật; MSK app RAM; Blender processing time; MediaPipe offline throughput; load/save; giới hạn 8GB. Phải có `measured_on_machine`, settings và sampling method. Tối ưu bằng LOD/mesh simplification *có lưu nguồn*, lazy loading, drawcall reduction; không hy sinh geometry correctness.

**Testing:** test contract, coordinate roundtrip, scale/laterality, topology / morph stability, weighted skin transforms, marker reprojection, change event, UI cross-state, license/quarantine, valid save/open, corrupted project refusal, security path traversal, P19–P37 regression. Capture screen shots WebGL at 3 body morph settings × 3 poses if possible. Không hardcode expected result từ implementation đang kiểm tra và tự coi đó là ground truth.

## 11. DELIVERABLES TỐI THIỂU

Tạo hoặc cập nhật:

```text
1docs/product_v1/
  V1_00_BASELINE.md
  V1_01_PRODUCT_GAP_MATRIX.md
  V1_02_OPEN_SOURCE_LICENSE_COMPATIBILITY.csv
  V1_03_ARCHITECTURE_AND_DATA_CONTRACTS.md
  V1_04_A_ATLAS_ACCEPTANCE.md
  V1_05_B_MORPH_ACCEPTANCE.md
  V1_06_C_DYNAMIC_ANCHORS_ACCEPTANCE.md
  V1_07_D_MOTION_WEBGL_ACCEPTANCE.md
  V1_08_E_PRODUCT_E2E_ACCEPTANCE.md
  V1_09_PERFORMANCE_AND_LIMITATIONS.md
  V1_10_G1_G4_MATRIX.md
  V1_11_USER_GUIDE_NON_DEVELOPER.md
  V1_12_RELEASE_MANIFEST_AND_GO_NO_GO.md
  evidence/   # Playwright PNG/video, Blender render, logs, hashes, metrics
```

Bàn giao một **V1.0 Research Preview** chạy được (chỉ nếu A–E đạt G1/G2 trong vertical slice), startup script cho Windows, assets có license, Blender `.blend`, glTF/GLB, body preset JSON, motion sequence, project file sample, automated tests, failure logs, Markdown sample và exact reproduction/rollback commands.

Nếu chưa xong một gói, ghi `PARTIAL / BLOCKED / FAIL` kèm blocker cụ thể. Tuyệt đối không gọi `V1.0 PRODUCT COMPLETE` khi bước E2E chưa đạt.

Không commit/merge/push/deploy trừ khi có chỉ định riêng. Duy trì mọi tài sản P18–P37, backup DB trước khi sửa, chỉ ghi files mới ở workspace kiểm soát.

## 12. BÁO CÁO CUỐI VÀ CÂU LỆNH BẮT ĐẦU

Cuối lượt thực thi, báo cáo tiếng Việt có các phần:

1. Git HEAD + working tree + artifacts đã xác minh thực.
2. Chọn nguồn mở nào, phiên bản/giấy phép/commit, và nguồn nào bị từ chối.
3. Tệp tạo/sửa và kết quả A–E (DONE/PARTIAL/BLOCKED).
4. **Ảnh browser trước/sau morph và pose** + khác biệt thực của vertex/object transforms.
5. Giải thích cách đồng bộ anatomical anchors qua morph + motion.
6. Test suites đã chạy thật (passed/failed/skipped) + điểm khác giữa test và thao tác sản phẩm.
7. Hiệu năng có phương pháp đo; giới hạn còn tồn tại.
8. G1/G2/G3/G4 độc lập, GO/NO-GO cho V1.0 Research Preview.
9. **Một bước duy nhất có giá trị cao nhất tiếp theo** nếu vẫn còn blocker, không tự đẻ P38/P39.

**BẮT ĐẦU NGAY:** xác thực baseline P34–P37, kiểm tra blocker `WEB_MOTION_GEOMETRY_NOT_CONNECTED`, triển khai vertical slice có geometry động thật trên Web Atlas, sau đó hoàn thành A–E theo gate. Không dừng chỉ để viết kế hoạch. Không yêu cầu người dùng tự học Blender.
