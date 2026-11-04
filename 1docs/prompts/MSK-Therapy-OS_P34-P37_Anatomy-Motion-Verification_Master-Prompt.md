# MASTER IMPLEMENTATION PROMPT — MSK-Therapy-OS P34–P37

**Vai trò:** Principal Software Architect, Anatomical Data Engineer, Biomechanics/Computer Vision Engineer, Scientific QA Auditor.

**Repository hiện hành:** `D:\5Projects\msk-therapy-os` (kiểm tra đường dẫn thực tế trước khi chạy).  
**Máy mục tiêu:** Windows, Blender 3.6.5 LTS, CPU i7-5600U, Intel HD 5500, RAM 8 GB; Python sidecar độc lập.  
**Phạm vi bất biến:** `RELEASE_SCOPE=ENGINEERING_RESEARCH_ONLY`; `CLINICAL_VALIDATION=NOT_ESTABLISHED`.  
**Nhiệm vụ:** TRIỂN KHAI thực tế P34–P37, nhưng theo các dependency gates. Code, test, tái lập, bằng chứng runtime và báo cáo. Không chỉ soạn kế hoạch. Không tự push/merge/deploy.

## 0. Ngữ cảnh và các tuyên bố phải tái kiểm chứng

Báo cáo P33 đề cập: 98/98 tests PASS; video 100 frames → MediaPipe inference tươi → Blender 3.6 → Web Atlas; Blender scene `p33_hardened_release.blend`; Knowledge Vault có 14 documents/18 claims; G3/G4 BLOCKED. Cũng báo `ASSET_NOT_AVAILABLE` cho các vùng cần LI4/ST36/KI3, chưa có đo sai số chuyển động với ground truth độc lập, và UI có timeline/WebGL/Markdown.

**Không coi báo cáo là chứng cứ tự xác thực.** Kiểm tra code, SHA-256, log, ảnh, asset, runtime và hiện trạng Git. Chú ý hai số liệu P33: tại video frame 050 MediaPipe ghi nâng vai 98.0°, còn Blender render frame 050 mô tả nâng 45°. Chưa đủ cơ sở kết luận lỗi vì có thể khác frame mapping/định nghĩa góc; phải truy vết cùng timestamp, trục, bên cơ thể, phép chuyển hệ tọa độ, FK/IK và phép đo. Nếu không đối chiếu được thì `END_TO_END_ANGLE_CONSISTENCY_NOT_PROVEN`.

P33 gọi G4 là phê duyệt FDA/CE-MDR: **sửa governance**. G4 là *Independent Engineering Acceptance*, không phải chứng nhận thiết bị y tế. Tạo một cổng pháp lý/quy định riêng chỉ khi có mục đích triển khai lâm sàng trong tương lai. Không khẳng định mặc định bắt buộc RCT hoặc chứng nhận y tế cho bản nghiên cứu này.

## 1. Quy tắc thực thi

1. Đọc tài liệu, logs, git status/HEAD, tree và mã nguồn trước khi sửa. Sao lưu có kiểm chứng các DB, scene, manifests, dữ liệu người dùng; không reset/stash/xóa dữ liệu làm việc.
2. Tạo nhánh làm việc cục bộ chỉ nếu an toàn với working tree. Không sửa lịch sử Git hoặc tự commit nếu policy repo không cho phép; không push/merge/deploy.
3. Mọi upstream phải có URL, revision/commit hoặc version, checksum, license thực tế ở **mức asset**, provenance và điều kiện tái phân phối. Không suy luận tất cả Z-Anatomy/BodyParts3D đều cùng một giấy phép. Cô lập asset NC/không rõ quyền; không tự tải vào gói phát hành.
4. Không tạo huyệt/landmark bằng tọa độ đoán và gắn nhãn WHO verified. Không gắn huyệt vào segment khác chỉ để tạo chuyển động. Cấm clinical advice tự động.
5. Phân biệt `ENGINEERING_PASS`, `ANATOMICAL_REVIEW_PENDING`, `ACCURACY_NOT_ESTABLISHED`, `INDEPENDENT_ACCEPTANCE_PENDING`. Nếu không có external reviewer thì G4 phải PENDING/BLOCKED.
6. Không coi test synthetic là bằng chứng inference thực hay độ chính xác lâm sàng. Không suy luận rằng visual đẹp = độ chính xác y học.
7. Không yêu cầu người dùng tự học Blender hoặc thao tác bằng tay. Dùng Blender headless/bpy, CLI, Playwright tự động; nếu bắt buộc có thao tác người thật, ghi rõ BLOCKED.
8. Dữ liệu bệnh nhân thật không nằm trong phạm vi. Chỉ dùng dữ liệu demo hợp pháp, không PII/PHI.
9. Mỗi milestone ghi `DONE / PARTIAL / BLOCKED`, các gates G1–G4 độc lập. Khi gate phụ thuộc không đạt, không tự vượt gate; tiếp tục việc độc lập có thể làm được.

## P34 — INDEPENDENT SOURCE & REALITY RECONCILIATION

**Mục tiêu:** Biết chính xác hệ thống hiện tại đã làm được gì, đang dùng dữ liệu nào và claim nào chưa được chứng minh.

### Phải làm

- Kiểm tra P33 release scene, source file hashes, audit logs, đầy đủ 98 tests và browser E2E. Ghi lệnh tái lập, môi trường và kết quả *observed*; không copy log cũ làm bằng chứng mới.
- Bản đồ hóa đường đi **video timestamp → MediaPipe world landmarks → axis/scale transform → angle convention → constraint solver → Blender pose bone → mesh/marker → Web Atlas animation**. Đưa một frame cụ thể qua toàn bộ pipeline và xuất bảng số liệu trước/sau ở cùng hệ tham chiếu.
- Xác minh Web Atlas đang hiển thị animation đúng xuất từ Blender hay chỉ phát lại thanh timeline với số góc. Nếu chỉ có UI playback, báo `WEB_MOTION_GEOMETRY_NOT_CONNECTED`.
- Kiểm tra nguồn thật của `vault.db`, `msk_therapy_os.sqlite3`, cross-system bridge, claim IDs; tránh nhân bản/tự gán review status.
- Lập inventory asset: cấu trúc nào *thực sự* có trong GLB/.blend và cấu trúc nào chỉ được nhắc tên. Kiểm tra nguồn của Radius, Ulna, Carpals, Metacarpals, Tibia, Fibula, các cấu trúc bề mặt gắn huyệt. Ưu tiên tìm trong nguồn đã có trước khi clone repo khác.
- Audit dữ liệu/giấy phép ở mức **từng file**: nguồn gốc BodyParts3D, Z-Anatomy, các tài sản nguồn khác (kể cả NC), CMU mocap, video Pose2Sim, model MediaPipe, tài liệu WHO/GB/T. Không tự suy ra quyền tái phân phối từ tên repository.
- Kiểm tra giả định nhịp scapulohumeral 2:1: nếu dùng công thức cứng, gắn nhãn **mô hình đơn giản hóa**, không xem là chân lý ở toàn ROM/mọi người.
- Sửa ma trận G1–G4 và bổ sung regulatory boundary tách biệt.

### Bàn giao

`1docs/audits/P34/P34_00_BASELINE_AND_REPRO.md`  
`1docs/audits/P34/P34_01_P33_CLAIM_TO_RUNTIME_MATRIX.md`  
`1docs/audits/P34/P34_02_ASSET_AND_LICENSE_LINEAGE.csv`  
`1docs/audits/P34/P34_03_MOTION_FRAME_TRACE.csv`  
`1docs/audits/P34/P34_04_GATES_AND_BLOCKERS.md`

**Gate P34:** Chỉ PASS kỹ thuật với bằng chứng tái lập, asset/giấy phép được phân loại, motion trace không bỏ qua transform. Những phần không chứng minh được phải có cờ rõ ràng, không ẩn bằng generic PASS.

## P35 — ANATOMICAL ATLAS COMPLETENESS & CORRECT SURFACE ANCHORING

**Mục tiêu:** Hoàn thiện *một vùng mẫu thực sự* trước khi mở rộng toàn thân. Ưu tiên bàn tay phải (LI4); sau khi đủ chứng cứ mới mở cẳng chân (ST36) và cổ chân (KI3).

### Phải làm

- Thẩm định asset nguồn có đủ cấu trúc xương, cơ và bề mặt liên quan không. Nếu thiếu, thử tìm nguồn mở khác **có quyền sử dụng rõ** rồi đánh giá geometry, mesh quality, scale, laterality, transform. Không ghép mesh khác người/hệ tọa độ tùy ý.
- Xây `AnatomyAssetRegistry`, `CanonicalFrameTransformRegistry`, `SurfaceAnchorRegistry` dùng stable IDs, SHA-256 mesh, local coords/barycentric, normals, bên trái/phải, phiên bản scene và nguồn.
- Thiết lập bone/mesh binding đúng phân đoạn. Với rigid bone: biến đổi rigid không đổi hình. Với da/cơ: không tự khẳng định biến dạng sinh học; hiển thị `DEFORMATION_MODEL_NOT_VALIDATED` khi chưa có mô hình/đối chứng. Chưa ưu tiên FEM nếu chưa cần cho PoC.
- Nêu rõ LI4/ST36/KI3 **không thể được chứng nhận** chỉ bằng khoảng cách tới mesh; bắt buộc có mốc tham chiếu chuyên môn và đánh giá độc lập. Không tự gỡ `EXPERT_REVIEW_PENDING`.
- Đảm bảo vị trí trên mesh, pose bone, waypoint meridian và API/Web Atlas giữ cùng object identity và frame; không mất khi save/reopen/export/import. Negative tests cho missing mesh, wrong body segment, flipped laterality, unit mismatch, stale mesh hash, invalid barycentric coordinates, missing bones.
- Nếu thiếu quyền dùng hoặc mô hình không phù hợp, thực hiện demo với phạm vi nhỏ có thể kiểm chứng và giữ các điểm khác ở `ASSET_NOT_AVAILABLE`.

### Bàn giao

`1docs/audits/P35/P35_ASSET_COMPOSITION_AND_ANCHORING.md`, test files, demo Blender và ảnh 3 tư thế, JSON bundle và bảng trạng thái LI4/ST36/KI3.

**Gate P35:** Trên ít nhất một cấu trúc vùng mẫu có asset đúng nguồn, có chuyển động rigid mesh + anchor đúng phân đoạn; round trip không trôi. Không dùng marker đứng yên hay bị gắn nhầm. G3 vẫn PENDING nếu chưa có reviewer.

## P36 — QUANTITATIVE MOTION VALIDATION

**Mục tiêu:** Đo sai số chuyển động **đúng nghĩa**; phân biệt tái lập phần mềm và độ chính xác đo trên người.

### Phải làm

- Xác định input ground truth độc lập: motion capture có reference markers hoặc phép đo goniometer/IMU/đa camera đã đồng bộ, có metadata, phép đo/định nghĩa góc và quyền sử dụng. CMU ASF/AMC có thể làm dữ liệu tham chiếu nhưng phải kiểm tra có khớp camera/video, subject, frame và góc quan sát hay không; không lấy hai mẫu chuyển động khác người làm ground truth từng frame.
- Thực thi `MotionComparisonHarness`: align timestamp/resampling, unit/frame transform, joint angle definition, left/right, anatomical coordinate frames, lag estimation, discontinuities và dropout accounting.
- Tính MAE, RMSE, p95, bias, valid frame rate, temporal jitter, confidence/visibility, bone-length deviation **chỉ khi đủ paired ground truth**. Xuất metrics, mẫu số, CI/uncertainty nếu hợp lệ. Nếu thiếu thì `ACCURACY_NOT_ESTABLISHED`, nhưng vẫn có thể PASS phần functional.
- So sánh frame MediaPipe 050 và Blender frame 050 của P33: xuất chain-of-custody rõ, chỉ gọi đó là mismatch khi frame/time/angle definitions thực sự tương đương.
- Kiểm thử với video thật, che khuất, low-confidence, dropped frames, tốc độ khác nhau, xoay ngoài mặt phẳng và giới hạn đơn camera. Không suy đoán pronation/supination từ hai điểm khuỷu–cổ tay. Không hứa camera thứ hai giải quyết mọi trường hợp nếu chưa được hiệu chuẩn và đánh giá.
- OpenSim/Pose2Sim chỉ là adapter research với env riêng; không đòi cài vào Python Blender 3.6. Nếu library không có/không tương thích, log BLOCKED chứ không giả mô phỏng.
- Kiểm định sai số retargeting khác với sai số markerless pose estimation và khác với sai số model biomechanics.

### Bàn giao

`1docs/audits/P36/P36_REFERENCE_DATA_AND_PROTOCOL.md`, `P36_FRAME_ALIGNED_METRICS.csv`, `P36_UNCERTAINTY_AND_FAILURE_CASES.md`, scripts/tests, video-to-blend proof và benchmark có metadata.

**Gate P36:** Functional có thể PASS nếu pipeline thực chạy; Accuracy chỉ PASS khi có dữ liệu ground truth độc lập và ngưỡng định trước. Không có ground truth = PENDING, không tự đặt 0° sai số.

## P37 — RESEARCH WORKSPACE CONSOLIDATION & HANDOFF

**Mục tiêu:** Tập trung trải nghiệm sử dụng và đóng gói một bản nghiên cứu có thể kiểm toán, không thêm engine thứ ba.

### Phải làm

- Khóa một nguồn sự thật cho claim/evidence trong Knowledge Vault; giải quyết đường dẫn bridge, migration nếu thật sự cần và có rollback.
- Liên kết một cấu trúc đã xác minh kỹ thuật với 3D viewer, motion sequence, anchor, Markdown evidence, provenance, confidence và review status; hiển thị mọi phần `UNVERIFIED/UNKNOWN/UNOBSERVABLE` rõ ràng.
- Web Atlas phải có kiểm thử từ *motion data* đến *geometry pose* ở cùng frame, không chỉ thanh timeline hoạt động. Nếu renderer chưa hỗ trợ skeletal animation, tạo adapter PoC nhỏ và gắn nhãn hạn chế.
- Chuẩn bị reviewer packet để chuyên gia giải phẫu có thể duyệt LI4/ST36/KI3 trên mốc giải phẫu có nguồn; phải lưu danh tính/role reviewer được xác thực, bằng chứng, quyết định và lý do; không tự ký thay.
- Chạy regression liên quan P19–P36, E2E browser và Blender, database backup/restore, asset checksum, error paths. Đo FPS **trong viewport thật** nếu có UI; nếu chỉ headless, giữ `VIEWPORT_FPS_NOT_MEASURED`.
- Đóng gói reproducibility: lệnh chạy PowerShell cụ thể, pinned versions, checksum, licenses/attribution, snapshot manifest, export demo không chứa thông tin bệnh nhân, hướng dẫn rollback.

### Bàn giao

`1docs/audits/P37/P37_FINAL_ENGINEERING_REPORT.md`  
`1docs/audits/P37/P37_G1_G4_ACCEPTANCE_MATRIX.md`  
`1docs/audits/P37/P37_REVIEWER_PACKET.md`  
`1docs/audits/P37/P37_RESEARCH_RELEASE_MANIFEST.json`  
Cập nhật roadmap hiện có, không tạo bản sao nguồn sự thật mới.

## 2. Cổng nghiệm thu, quyền phê duyệt và cách báo cáo

- **G1 Functional:** Có runtime thật, testcase negative/positive, ảnh/log/artefact có thể chạy lại.
- **G2 Data Integrity:** Asset hash/transform/schema/provenance/SQLite/quyền sử dụng có chứng cứ, không ghi đè âm thầm.
- **G3 Domain Validity:** Chỉ reviewer chuyên môn đủ năng lực + phương pháp chuẩn phù hợp có quyền thẩm định. Agent phải để PENDING nếu chưa có review.
- **G4 Independent Acceptance:** Kiểm toán kỹ thuật độc lập bên ngoài người/agent tự xây; *không phải FDA/CE/MDR approval*. Nếu chưa có bên độc lập, PENDING.
- **Regulatory/Clinical Deployment Gate:** Ngoài P34–P37, chưa triển khai; không nâng scope sản phẩm nghiên cứu lên chẩn đoán/điều trị.

### Format final response (tiếng Việt)

1. Git HEAD và tình trạng working tree; hash source/asset cốt lõi.
2. Những claims P33 được CONFIRMED / CONTRADICTED / NOT_OBSERVABLE, kèm đường dẫn bằng chứng.
3. Bảng `P34–P37 | DONE/PARTIAL/BLOCKED | G1 | G2 | G3 | G4 | Evidence`.
4. Các code files, tests, model assets và adapters đã tạo/sửa, lý do.
5. Paired angle-trace và metrics thật (hoặc lý do `ACCURACY_NOT_ESTABLISHED`).
6. Trạng thái LI4/ST36/KI3 theo từng nguồn và từng mesh, không công nhận tự động.
7. Lệnh tái lập PowerShell, demo, video/ảnh, sai số, giới hạn và rollback.
8. Rủi ro giấy phép, phạm vi bản nghiên cứu, decision GO/NO-GO.
9. Những công việc cần reviewer thực sự và input tối thiểu để unblock.

**BẮT ĐẦU NGAY tại P34 preflight.** Không dừng vì thiếu prompt cũ, không hỏi xác nhận từng bước. Triển khai tối đa phần đủ điều kiện; với phần còn thiếu nguồn/ground truth/reviewer thì báo BLOCKED trung thực, tuyệt đối không giả PASS.
