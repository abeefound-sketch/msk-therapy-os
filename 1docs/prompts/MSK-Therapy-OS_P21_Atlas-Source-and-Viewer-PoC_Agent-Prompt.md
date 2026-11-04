# MSK-Therapy-OS — Coding Agent Prompt P21
## Anatomical Source Validation + Interactive Atlas Proof of Concept

**Ngôn ngữ báo cáo:** Tiếng Việt. **Phạm vi:** nghiên cứu, học tập, ghi chú giải phẫu; không sử dụng để chẩn đoán, kê đơn hay chỉ dẫn điều trị tự động.

### Bối cảnh cần đọc trước khi sửa code

1. Làm việc trên repository **thực tế** đang chứa P18, P19, P20; đọc `1docs/audits/P19/`, `1docs/audits/P20/`, registry nguồn dữ liệu và tài liệu kiến trúc hiện hành. Không dựa vào một bản ZIP cũ để giả định trạng thái code.
2. Báo cáo P19/P20 hiện là **ENGINEERING_PASS_SCOPE_LIMITED**; G3 và G4 còn `PENDING`. Kết quả Agent tự báo không thay thế kiểm chứng độc lập.
3. P19 báo `static/atlas/` vẫn dùng DEMO-BODY procedural vì `atlases.json` rỗng, có các bộ tọa độ huyệt bất đồng nghiêm trọng (LI4, ST36, KI3, GV14, GB21). Không được xem sự trùng khớp mặt mesh là xác nhận huyệt học.
4. P20 Knowledge Vault đã có CLI/SQLite nhưng gói `MSK_Knowledge_Vault_Starter_Offline.zip` không có trong workspace. Không được tuyên bố đã nhập bộ starter đó.
5. Mục tiêu tối thượng của Atlas: có **mô hình giải phẫu 3D thực sự có xương, cơ, nội tạng, các lớp có thể hiện/ẩn**, cho người dùng **tự đánh dấu huyệt, tự vẽ đường kinh và ghi chú**, lưu được để tiếp tục học, xuất Markdown. Đây là ưu tiên cao hơn mở rộng số huyệt sinh bằng công thức.

### Mục tiêu P21

Đánh giá độc lập các nguồn open-source (ứng viên gợi ý: Human Atlas, TARA, tcm-3d và các công cụ xử lý mesh như three-mesh-bvh; tìm đúng upstream URL, không coi các tên này là tên repo đã được xác minh). **Chọn được ít nhất một pipeline dữ liệu giải phẫu thật** và tạo **proof-of-concept có thể thao tác trong browser**, hoàn toàn cách ly với Atlas hiện tại. Không merge production hoặc tự triển khai P22.

### Quy trình bắt buộc

**P21.0 — Preflight và điểm phục hồi**

- In `git status --short`, branch, HEAD, danh sách thay đổi P19/P20 còn chưa commit; kiểm tra tất cả đường dẫn thực sự tồn tại.
- Không overwrite, stash, reset hay xóa dữ liệu không được phép. Tạo branch nghiên cứu P21 chỉ khi thao tác an toàn; nếu workspace dirty, bảo vệ toàn bộ thay đổi và ghi rõ lý do giới hạn.
- Rerun tối thiểu các bài test P19/P20; lưu lệnh và output thật, không thay bằng số PASS từ báo cáo trước.
- Kiểm tra dữ liệu chính: registry, orientation, units, transforms, mesh hash; giữ nguyên canonical/legacy resolver của runtime hiện hành.

**P21.1 — Kiểm định nguồn và giấy phép**

Với mỗi upstream, lập `P21_UPSTREAM_SOURCE_MATRIX.csv` gồm: tên, URL gốc, maintainer, commit/tag pin, ngày truy cập, chức năng, code license, **asset/data license riêng**, điều kiện ghi công/chia sẻ, khả năng dùng thương mại, nguồn hình học, độ phủ xương/cơ/nội tạng/da, segmentation, metadata cấu trúc, đơn vị tọa độ, trục/tư thế, format, dung lượng, khả năng offline, hardware cost, khả năng xuất/nhập, mức tin cậy, blockers. Không được suy diễn license của mesh từ license code. Giấy phép chưa rõ: `QUARANTINE`, không nhúng. Không giới hạn tiêu chí pháp lý chỉ ở MIT/CC-BY; lập luận tương thích theo từng trường hợp, phân biệt điều kiện tuân thủ, phân phối và sử dụng nội bộ; nguồn NC/không rõ quyền không được đưa vào bundle thương mại.

**P21.2 — Chạy upstream độc lập**

- Clone/download vào `research/upstream/` hoặc thư mục sandbox có gitignore; pin commit, hash assets và tạo hướng dẫn tái lập. Không đổ mã nguồn chưa kiểm toán vào `msk_therapy_os/static/atlas/`.
- Chạy demo upstream và chụp chứng cứ runtime. Với repo không hoạt động hoặc chỉ có data placeholder, ghi `FAILED/BLOCKED` trung thực.
- Không tạo anatomy giả bằng ellipsoid hay hình học tự sinh để đạt mục tiêu nghiệm thu. Có thể duy trì DEMO-BODY cũ với banner hiện có để tương thích ngược.

**P21.3 — Khảo sát model anatomy có đủ lớp**

- Đánh giá khả năng cung cấp anatomy thật ở 4 nhóm: **bone**, **muscle**, **viscera/organs**, **skin/exterior**, kèm tên từng cấu trúc và nguồn. Phân biệt coverage thực tế và coverage mục tiêu.
- Xác nhận mỗi mesh được tải là tài sản gốc được phép sử dụng, không phải placeholder/sphere/parametric replica. Bằng chứng: SHA-256, object count, vertex/face count, bounding box, unit/trục, metadata, screenshot và attribution.
- Chọn pipeline được khuyến nghị theo tiêu chí: độ đầy đủ giải phẫu, độ tin cậy, giấy phép rõ, phân lớp được, khả năng mở rộng, offline và hiệu năng trên Windows 8 GB / Intel HD 5500.
- Nếu không tồn tại nguồn đủ ba nhóm bone/muscle/organ hợp lệ, **không chế tác giả** để đạt gate. Chọn candidate khả thi nhất, ghi rõ phần thiếu và `PARTIAL/NO-GO` cho phần còn lại.

**P21.4 — Atlas viewer proof-of-concept (không sửa runtime production)**

Tạo route hoặc ứng dụng sandbox tách biệt với Atlas cũ; ưu tiên tận dụng WebGL/Three.js đã có, không ép thêm npm/bundler/backend dependency vào runtime.

Tối thiểu cần demo được nếu asset hợp lệ:

1. Nạp mesh thật, hiển thị metadata `source_id`, version, license, verification và cảnh báo research-only.
2. Cây cấu trúc giải phẫu, chọn object, highlight, orbit/zoom, isolate, hide/show theo từng lớp bone/muscle/organs/skin. Không gọi mesh ngoài da là “full anatomy”.
3. Click một cấu trúc để xem tên, loại, nguồn và chú thích.
4. Chế độ **manual acupoint**: đặt marker bằng raycast lên bề mặt cấu trúc đã chọn, gắn nhãn và ghi chú; `USER_ANNOTATED_UNVERIFIED` mặc định.
5. Chế độ **manual meridian/polyline**: đặt nhiều waypoint theo thứ tự bằng click; sửa/xóa/undo/redraw; không tự nối bằng công thức huyệt học hoặc gọi đường vẽ là đường kinh đã xác minh.
6. Lưu và tải lại annotation. Mỗi marker/waypoint phải lưu object/mesh ID, local coordinates hoặc triangle + barycentric attachment, transform ID/version, source asset hash và metadata độ bất định để không bị trôi khi đổi camera, zoom hoặc thay đổi hệ tọa độ. Khi nguồn mesh đổi, fail-closed hoặc yêu cầu remap; không tự dời im lặng.
7. Liên kết với Knowledge Vault P20 ở mức adapter **read-only** hoặc xuất Markdown kèm nguồn mesh, IDs, tọa độ, ghi chú, tình trạng thẩm định và hash; nếu chưa có integration thì ít nhất export/import Markdown độc lập. Không truy cập hồ sơ bệnh nhân thật.

Nếu một phần chưa thực hiện được, báo blocker cùng evidence và kế hoạch nhỏ nhất giải quyết; không đánh dấu PASS bằng mock.

**P21.5 — Tests và bằng chứng**

- Test dữ liệu: model thật và license rõ, hash đúng, không thiếu asset offline, unit/trục/transform nhất quán, không ép chiều âm/dương bằng offset giả.
- Test UI browser: hide/show layer, raycast/marker, 3+ waypoint polyline, chỉnh sửa/undo, save/reload, export Markdown, camera view không làm trôi marker, missing mesh báo lỗi rõ.
- Ghi hình hoặc ảnh chụp browser thật kèm console log, testcase/lệnh và trạng thái pass/fail. Đo FPS/load-time/memory có phương pháp; nếu không chạy trên Intel HD 5500, chỉ báo benchmark môi trường thực đo và `TARGET_HARDWARE_UNVERIFIED`.
- Rerun regression P18/P19/P20; nếu không chạy được full suite, ghi subset đã chạy và lý do, không tự suy rộng 100%.
- Không được tự cấp G3 `ANATOMICAL_VERIFIED`, `CLINICAL_APPROVED` hay G4 `INDEPENDENT_ACCEPTANCE`.

### Sản phẩm bàn giao

Tạo trong `1docs/audits/P21/`:

- `P21_00_PREFLIGHT_AND_BASELINE.md`
- `P21_01_UPSTREAM_SOURCE_MATRIX.csv`
- `P21_02_ASSET_LICENSE_AND_ATTRIBUTION.md`
- `P21_03_ANATOMY_COVERAGE_AND_GEOMETRY.md`
- `P21_04_COORDINATE_AND_MESH_CONTRACT.md`
- `P21_05_ATLAS_VIEWER_POC_USER_GUIDE.md`
- `P21_06_TEST_AND_RUNTIME_EVIDENCE.md`
- `P21_07_G1_G4_ACCEPTANCE_MATRIX.md`
- `P21_08_GO_NO_GO_FOR_P22.md`

Cung cấp danh sách file code, đường dẫn mở PoC, lệnh chạy Windows PowerShell, test output, screenshots, asset provenance, các hạn chế và quyết định GO/CONDITIONAL GO/NO-GO rõ ràng.

### Điều kiện dừng

P21 chỉ đạt `ENGINEERING_PASS_SCOPE_LIMITED` nếu có **viewer hoạt động với mesh giải phẫu gốc hợp lệ**, tương tác được ít nhất với layer/structure thật, tạo và hồi phục annotation, xuất Markdown có provenance, đồng thời không làm hỏng Atlas cũ. Nếu chưa có model thật, chỉ `RESEARCH_COMPLETE / VIEWER_BLOCKED` và không tiến sang P22.

Trước khi làm P22, đề xuất bộ giải phẫu/tham chiếu thẩm định riêng cho LI4/ST36/KI3; **độ lệch <15 mm với một điểm máy móc không được xem là bằng chứng huyệt học**. Cần reviewer chuyên môn và định nghĩa riêng về mặt phẳng, mốc giải phẫu, bề mặt và đối tượng tham chiếu.

**BẮT ĐẦU NGAY:** Preflight → inventory nguồn → clone sandbox → chọn asset → PoC → tests → báo cáo. Không chỉ đưa ra kế hoạch. Không tự push/merge/deploy, không ghi dữ liệu bệnh nhân thật.
