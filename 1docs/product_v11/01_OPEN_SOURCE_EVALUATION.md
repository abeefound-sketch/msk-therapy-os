# MSK-THERAPY-OS V1.1 — OPEN-SOURCE CHARACTER PIPELINE EVALUATION
## Đánh giá và Lựa chọn Pipeline Nhân vật 3D Mã nguồn Mở

> **Scope:** `ENGINEERING_RESEARCH_ONLY`  
> **Clinical Safety:** `CLINICAL_VALIDATION = NOT_ESTABLISHED`

---

### 1. BẢNG MA TRẬN QUYẾT ĐỊNH PIPELINE (DECISION MATRIX)

| Tiêu chí kỹ thuật | MakeHuman Community Assets | Blender Rigify Addon | Three.js Standard Engine | MakeHuman Standalone Desktop (GUI) |
| :--- | :--- | :--- | :--- | :--- |
| **Repository** | `makehumancommunity/mpfb2` & `makehuman` | Tích hợp sẵn trong Blender 3.6 LTS | `mrdoob/three.js` (r128 offline) | `makehumancommunity/makehuman` |
| **Commit / Version** | Master / MPFB2 `last_blender3_version` | Blender 3.6.5 LTS core addon | r128 (đã tích hợp tại `/education/vendor/three/`) | v1.3.0 standalone bundle |
| **Giấy phép Bản quyền** | **CC0 1.0 Universal** (Toàn bộ tài nguyên 3D: base mesh, rig, weights, targets) | GPL v2+ (Blender core script) | MIT License | Mã nguồn: AGPLv3; Assets: CC0 |
| **Lây lan bản quyền (Copyleft)** | **KHÔNG** (Dự án tuyên bố Output là User Data, không chịu ràng buộc AGPL) | Không ràng buộc đối với tệp GLB xuất ra | KHÔNG (Permissive MIT) | Cần môi trường PyQt5 nặng nề |
| **Tương thích Blender 3.6** | Hoàn toàn tương thích (đọc trực tiếp `.obj`, `.json`, `.target.gz`) | Hoàn toàn tương thích | Không áp dụng (Client-side) | Độc lập ngoài Blender |
| **Khả năng Xuất/Nhập GLB** | Xuất GLB chuẩn glTF 2.0 có Skins + Morphs | Xuất GLB hỗ trợ animation | Nạp trực tiếp qua `GLTFLoader` | Cần xuất trung gian qua FBX/DAE |
| **Vận hành Offline 100%** | $100\%$ Offline (Tải một lần vào `makehuman_assets/`, dung lượng < 6 MB) | $100\%$ Offline | $100\%$ Offline | Cần cài đặt gói desktop lớn (~400 MB) |
| **Phần cứng 8 GB RAM / HD 5500** | Rất nhẹ (Mesh 19k đỉnh, RAM load < 15 MB) | Nhẹ đối với armature cơ bản | Chạy mượt mà 60 FPS trên Intel HD 5500 | Tiêu tốn nhiều RAM cho PyQt5 GUI |
| **Quyết định (DECISION)** | **KEEP & ADAPT (Ưu tiên số 1)** | **ADAPT (Dùng tham chiếu bổ trợ)** | **KEEP (Tiêu chuẩn hiển thị Web)** | **REJECT (Tránh phụ thuộc GUI cồng kềnh)** |

---

### 2. PHÂN TÍCH GIẤY PHÉP VÀ TÍNH ĐỘC LẬP TÀI SẢN (LICENSE MANIFEST)

Để bảo đảm tính trong sạch pháp lý tuyệt đối cho MSK-Therapy-OS, toàn bộ tài sản sử dụng trong pipeline được phân định ranh giới rõ ràng:

1. **MakeHuman 3D Assets (CC0 1.0 Universal):**
   - Tệp đỉnh cơ sở: `base.obj` (19.158 đỉnh, 18.486 đa giác).
   - Khung xương: `rig.game_engine.json` (53 xương chuẩn humanoid game engine).
   - Trọng số da: `weights.game_engine.json` (52 nhóm đỉnh gán trọng số thực tế).
   - Tệp hình thể tham số: `male-young-maxheight.target.gz`, `shoulder-width-incr.target.gz`, `waist-circ-incr.target.gz`, `*-vert-incr.target.gz`.
   - *Căn cứ pháp lý:* Tệp `LICENSE.ASSETS.md` và Mục D trong `LICENSE.md` của MakeHuman Community nêu rõ: Toàn bộ dữ liệu đồ họa (assets) được phát hành theo **CC0 1.0 Universal**. Mọi sản phẩm xuất ra từ assets này được coi là dữ liệu của người dùng, không bị ràng buộc bởi giấy phép mã nguồn AGPL.

2. **Tài sản Giải phẫu Kế thừa (BodyParts3D / Z-Anatomy):**
   - Giấy phép: Creative Commons Attribution 2.1 Japan (CC-BY 2.1 JP) và CC-BY-SA 4.0.
   - Vị trí lưu trữ: `3refs/upstream/tcm-3d/public/models/` (15 binary chunks) và `tools/blender_anatomy_studio/assets/bp3d/`.
   - Tính độc lập: Hoàn toàn độc lập với nhân vật MakeHuman, chỉ liên kết thông qua bộ chuyển đổi đăng ký giải phẫu `CharacterAnatomyRegistrationAdapter`.

3. **Three.js Web Engine (MIT License):**
   - Vị trí: `msk_therapy_os/static/education/vendor/three/`.
   - Tận dụng `GLTFLoader`, `SkinnedMesh`, `Skeleton`, `Bone`, `AnimationMixer`, không viết lại thuật toán skinning.

---

### 3. KẾT LUẬN LỰA CHỌN KỸ THUẬT

Dự án chọn **Phương án A: Khai thác trực tiếp MakeHuman Humanoid Base Mesh + Game Engine Rig + Skin Weights + Parametric Morph Targets** thông qua script tự động hóa Blender 3.6 LTS:
- **Số bước xử lý tối thiểu:** Chỉ cần chạy một script Python duy nhất (`tools/build_rigged_human_v11.py`) trong môi trường Blender headless để tạo tệp GLB chuẩn.
- **Bảo toàn 100% Skinning:** Trọng số da của MakeHuman được họa sĩ giải phẫu cân chỉnh thủ công, không bị biến dạng gấp nếp hay lỗi xé lưới khi gập khuỷu tay hoặc dạng cánh tay.
- **Tương thích hoàn hảo với Three.js:** `SkinnedMesh` của Three.js đọc trực tiếp bone hierarchy và inverse bind matrices trong GLB mà không cần bất kỳ bộ điều hợp phức tạp nào.
