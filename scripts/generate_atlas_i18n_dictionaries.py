import json
from pathlib import Path

ATLAS_I18N_DIR = Path("D:/5Projects/msk-therapy-os/msk_therapy_os/static/atlas/i18n")
ATLAS_I18N_DIR.mkdir(parents=True, exist_ok=True)

ATLAS_EN = {
  "title": "Open Anatomy Atlas",
  "modes": {
    "explore": "Explore",
    "quiz": "Quiz",
    "surface": "🌐 Surface",
    "surface_title": "Surface Meridian Mode: Skin mesh with surface-anchored meridians",
    "anatomy": "🦴 Anatomy",
    "anatomy_title": "Musculoskeletal Anatomy Mode: Deep bones, muscles, joints",
    "compare": "⚖ Compare",
    "compare_title": "Comparative Research Mode: Synchronized dual split-view"
  },
  "camera": {
    "front": "Front",
    "front_title": "Front view (1)",
    "back": "Back",
    "back_title": "Back view (2)",
    "left": "Left",
    "left_title": "Patient's left side (3)",
    "right": "Right",
    "right_title": "Patient's right side (4)",
    "full_body": "Full Body",
    "full_body_title": "Full body framing (Home)",
    "focus": "Focus",
    "focus_title": "Focus on selected structure or acupoint (F)",
    "reset": "Reset",
    "reset_title": "Show everything and reset the view (A)",
    "xray": "X-ray",
    "xray_title": "X-ray: see through everything except the selection (X)",
    "shot": "Save image",
    "shot_title": "Save a picture of the current view",
    "data": "Atlas data",
    "data_title": "Atlas data",
    "about": "About",
    "about_title": "About this atlas and who made it",
    "help": "?",
    "help_title": "Keyboard shortcuts (?)"
  },
  "tabs": {
    "layers": "Layers",
    "structures": "Structures",
    "sections": "Sections",
    "meridians": "Meridians"
  },
  "layers": {
    "show_hidden": "Show hidden structures",
    "by_region": "By region",
    "by_type": "By type",
    "skin_opacity": "Skin Opacity:",
    "opacity_slider_title": "Adjust skin transparency to see internal anatomy"
  },
  "actions": {
    "focus": "Focus",
    "focus_title": "Zoom to it (F)",
    "isolate": "Isolate",
    "isolate_title": "Hide everything else (I)",
    "hide": "Hide",
    "hide_title": "Hide it (H)",
    "close": "Close"
  },
  "meridians": {
    "title": "Acupuncture & Traditional Reflex Overlay",
    "show_meridians": "Classical Meridians (14)",
    "show_points": "WHO Standard Acupoints (362)",
    "show_thai": "Thai Sen Sib (3)",
    "show_dien_chan": "Vietnamese Dien Chan (4)",
    "filter_channel": "Channel:",
    "filter_region": "Region:",
    "all_channels": "All Channels",
    "all_regions": "All Regions",
    "verified_only": "Verified Anchors Only"
  },
  "sections": {
    "no_cut": "No cut",
    "axial": "Axial (transverse)",
    "coronal": "Coronal (front / back)",
    "sagittal": "Sagittal (left / right)",
    "keep_other_side": "Keep the other side",
    "position": "Position:"
  },
  "quiz": {
    "find_it": "Find it: click the named structure",
    "name_it": "Name it: pick the name of the highlighted structure",
    "start": "Start quiz",
    "next": "Next question",
    "skip": "Skip",
    "stop": "End quiz",
    "again": "Try again",
    "questions": "Questions:"
  },
  "hints": {
    "orbit_hint": "Left drag to orbit | Right / Shift+drag to pan | Scroll to zoom | Click to identify",
    "click_identify": "Click any structure to identify it",
    "loading": "Loading atlas..."
  }
}

ATLAS_ZH = {
  "title": "开放解剖图谱 (Open Anatomy Atlas)",
  "modes": {
    "explore": "探索",
    "quiz": "测验",
    "surface": "🌐 体表经络",
    "surface_title": "体表经络模式：皮肤网格与体表针灸穴位经络",
    "anatomy": "🦴 肌骨解剖",
    "anatomy_title": "肌骨解剖模式：深层骨骼、肌肉与关节",
    "compare": "⚖ 对比对照",
    "compare_title": "对比研究模式：左右分屏双向同步视图"
  },
  "camera": {
    "front": "正面",
    "front_title": "正视观察 (快捷键 1)",
    "back": "背面",
    "back_title": "后视观察 (快捷键 2)",
    "left": "左侧",
    "left_title": "观察患者左侧 (快捷键 3)",
    "right": "右侧",
    "right_title": "观察患者右侧 (快捷键 4)",
    "full_body": "全身",
    "full_body_title": "全身视野取景 (Home 键)",
    "focus": "聚焦",
    "focus_title": "聚焦到选中的解剖结构或穴位 (F 键)",
    "reset": "重置",
    "reset_title": "显示全部并重置视角 (A 键)",
    "xray": "透视",
    "xray_title": "X射线半透明透视模式 (X 键)",
    "shot": "保存图片",
    "shot_title": "保存当前视图截图",
    "data": "图谱数据",
    "data_title": "查看图谱数据来源",
    "about": "关于",
    "about_title": "关于此解剖图谱与制作信息",
    "help": "?",
    "help_title": "键盘快捷键帮助 (?)"
  },
  "tabs": {
    "layers": "解剖图层",
    "structures": "结构目录",
    "sections": "断层切片",
    "meridians": "经络穴位"
  },
  "layers": {
    "show_hidden": "显示隐藏结构",
    "by_region": "按区域划分",
    "by_type": "按类型划分",
    "skin_opacity": "皮肤透明度：",
    "opacity_slider_title": "调节皮肤透明度以观察深层内部解剖结构"
  },
  "actions": {
    "focus": "聚焦",
    "focus_title": "缩放对齐至该结构 (F 键)",
    "isolate": "单独显示",
    "isolate_title": "隐藏所有其他非选中结构 (I 键)",
    "hide": "隐藏",
    "hide_title": "隐藏该结构 (H 键)",
    "close": "关闭"
  },
  "meridians": {
    "title": "针灸穴位与传统反射覆盖层",
    "show_meridians": "十四古典经络",
    "show_points": "WHO 标准 362 腧穴",
    "show_thai": "泰式十线 (Sen Sib)",
    "show_dien_chan": "越南面针反射区 (Dien Chan)",
    "filter_channel": "经脉筛选：",
    "filter_region": "部位筛选：",
    "all_channels": "全部经脉",
    "all_regions": "全部区域",
    "verified_only": "仅显示已验证基准穴位"
  },
  "sections": {
    "no_cut": "不剖切",
    "axial": "横断面 (轴位)",
    "coronal": "冠状面 (前后向)",
    "sagittal": "矢状面 (左右向)",
    "keep_other_side": "保留另一侧",
    "position": "剖切位置："
  },
  "quiz": {
    "find_it": "寻找结构：点击被提问的结构名称",
    "name_it": "辨认命名：选出高亮高亮结构的正确名称",
    "start": "开始测验",
    "next": "下一题",
    "skip": "跳过",
    "stop": "结束测验",
    "again": "再试一次",
    "questions": "题数："
  },
  "hints": {
    "orbit_hint": "左键拖拽旋转 | 右键/Shift+左键平移 | 滚轮缩放 | 点击识别结构",
    "click_identify": "点击任意结构查看其解剖命名",
    "loading": "正在加载解剖图谱..."
  }
}

ATLAS_VI = {
  "title": "Atlas Giải Phẫu Mở (Open Anatomy Atlas)",
  "modes": {
    "explore": "Khám Phá",
    "quiz": "Trắc Nghiệm",
    "surface": "🌐 Thể Biểu",
    "surface_title": "Chế độ Thể biểu & Kinh lạc: Bề mặt da gắn hệ thống huyệt vị và kinh lạc",
    "anatomy": "🦴 Cơ Xương",
    "anatomy_title": "Chế độ Cơ xương khớp: Cấu trúc sâu gồm xương, cơ và khớp",
    "compare": "⚖ Đối Chiếu",
    "compare_title": "Chế độ Đối chiếu nghiên cứu: Màn hình chia đôi đồng bộ song song"
  },
  "camera": {
    "front": "Mặt Trước",
    "front_title": "Quan sát mặt trước (Phím 1)",
    "back": "Mặt Sau",
    "back_title": "Quan sát mặt sau (Phím 2)",
    "left": "Bên Trái",
    "left_title": "Quan sát phía bên trái người bệnh (Phím 3)",
    "right": "Bên Phải",
    "right_title": "Quan sát phía bên phải người bệnh (Phím 4)",
    "full_body": "Toàn Thân",
    "full_body_title": "Thu phóng quan sát toàn thân (Phím Home)",
    "focus": "Tiêu Điểm",
    "focus_title": "Tập trung vào cấu trúc hoặc huyệt vị đang chọn (Phím F)",
    "reset": "Đặt Lại",
    "reset_title": "Hiện toàn bộ và đặt lại góc nhìn mặc định (Phím A)",
    "xray": "X-Quang",
    "xray_title": "Chế độ trong suốt xuyên thấu X-quang (Phím X)",
    "shot": "Lưu hình ảnh",
    "shot_title": "Chụp lưu ảnh góc nhìn hiện tại",
    "data": "Dữ liệu",
    "data_title": "Xem nguồn dữ liệu atlas",
    "about": "Giới thiệu",
    "about_title": "Thông tin về atlas giải phẫu này",
    "help": "?",
    "help_title": "Phím tắt bàn phím (?)"
  },
  "tabs": {
    "layers": "Lớp Giải Phẫu",
    "structures": "Cấu Trúc",
    "sections": "Mặt Cắt",
    "meridians": "Kinh Lạc"
  },
  "layers": {
    "show_hidden": "Hiện cấu trúc đã ẩn",
    "by_region": "Theo vùng cơ thể",
    "by_type": "Theo loại giải phẫu",
    "skin_opacity": "Độ mờ của da:",
    "opacity_slider_title": "Điều chỉnh độ trong suốt của da để quan sát cấu trúc bên trong"
  },
  "actions": {
    "focus": "Tiêu Điểm",
    "focus_title": "Thu phóng tập trung vào đối tượng (Phím F)",
    "isolate": "Cô Lập",
    "isolate_title": "Ẩn tất cả cấu trúc khác ngoài đối tượng đang chọn (Phím I)",
    "hide": "Ẩn",
    "hide_title": "Ẩn cấu trúc này (Phím H)",
    "close": "Đóng"
  },
  "meridians": {
    "title": "Hệ Thống Huyệt Vị & Lớp Phản Xạ Cổ Truyền",
    "show_meridians": "14 Đường Kinh Lạc Cổ Điển",
    "show_points": "362 Huyệt Vị Chuẩn WHO",
    "show_thai": "Kinh Lạc Thái (Sen Sib)",
    "show_dien_chan": "Diện Chẩn Mặt (Bùi Quốc Châu)",
    "filter_channel": "Lọc kinh lạc:",
    "filter_region": "Lọc vùng:",
    "all_channels": "Tất cả đường kinh",
    "all_regions": "Tất cả vùng",
    "verified_only": "Chỉ hiện mốc chuẩn đã kiểm chứng"
  },
  "sections": {
    "no_cut": "Không cắt",
    "axial": "Mặt cắt ngang (Axial)",
    "coronal": "Mặt cắt đứng ngang (Coronal)",
    "sagittal": "Mặt cắt đứng dọc (Sagittal)",
    "keep_other_side": "Giữ nửa đối diện",
    "position": "Vị trí mặt cắt:"
  },
  "quiz": {
    "find_it": "Tìm vị trí: Nhấp vào cấu trúc theo tên gọi",
    "name_it": "Đặt tên: Chọn đúng tên của cấu trúc đang sáng",
    "start": "Bắt đầu bài trắc nghiệm",
    "next": "Câu tiếp theo",
    "skip": "Bỏ qua",
    "stop": "Kết thúc bài thi",
    "again": "Làm lại",
    "questions": "Số câu hỏi:"
  },
  "hints": {
    "orbit_hint": "Kéo chuột trái để xoay | Chuột phải / Shift+trái để di chuyển | Cuộn để phóng to | Nhấp để nhận diện",
    "click_identify": "Nhấp vào bất kỳ cấu trúc nào để xem tên gọi",
    "loading": "Đang tải bản đồ giải phẫu..."
  }
}

with open(ATLAS_I18N_DIR / "en.json", "w", encoding="utf-8") as f:
    json.dump(ATLAS_EN, f, ensure_ascii=False, indent=2)

with open(ATLAS_I18N_DIR / "zh.json", "w", encoding="utf-8") as f:
    json.dump(ATLAS_ZH, f, ensure_ascii=False, indent=2)

with open(ATLAS_I18N_DIR / "vi.json", "w", encoding="utf-8") as f:
    json.dump(ATLAS_VI, f, ensure_ascii=False, indent=2)

print(f"Atlas i18n dictionaries written: en.json, zh.json, vi.json to {ATLAS_I18N_DIR}")
