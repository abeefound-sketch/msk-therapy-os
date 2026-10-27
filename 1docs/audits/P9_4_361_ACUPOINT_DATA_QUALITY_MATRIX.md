# P9.4 AUDIT: 361 ACUPOINT DATA QUALITY & COVERAGE MATRIX

**Author:** Principal Computational Anatomy Engineer, Quality Assurance Automation Lead  
**Project:** MSK-Therapy-OS  
**Repository Branch:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Reference Mesh:** BodyParts3D FJ2810 Canonical Ground Truth (`05b4923391bb7cfe1152a3102bb62167d54db701d6592755c7b73fc3fdfc3808`)  
**Date:** October 2026  

---

## 1. SUMMARY MATRIX BY MERIDIAN CHANNEL

| Meridian Code | Channel Name | Total Points | Class A (Audited) | Class B (Landmark) | Class C (Surface) | Class D (Legacy) | Class E (Missing) | Left Coverage | Right Coverage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LU** | Lung Meridian | 11 | 1 | 0 | 0 | 10 | 0 | 11/11 | 11/11 |
| **LI** | Large Intestine Meridian | 20 | 2 | 0 | 0 | 18 | 0 | 20/20 | 20/20 |
| **ST** | Stomach Meridian | 45 | 2 | 0 | 0 | 43 | 0 | 45/45 | 45/45 |
| **SP** | Spleen Meridian | 21 | 0 | 0 | 0 | 21 | 0 | 21/21 | 21/21 |
| **HT** | Heart Meridian | 9 | 1 | 0 | 0 | 8 | 0 | 9/9 | 9/9 |
| **SI** | Small Intestine Meridian | 19 | 0 | 0 | 0 | 19 | 0 | 19/19 | 19/19 |
| **BL** | Bladder Meridian | 67 | 5 | 0 | 0 | 62 | 0 | 67/67 | 67/67 |
| **KI** | Kidney Meridian | 27 | 0 | 0 | 0 | 27 | 0 | 27/27 | 27/27 |
| **PC** | Pericardium Meridian | 9 | 1 | 0 | 0 | 8 | 0 | 9/9 | 9/9 |
| **TE** | Triple Energizer Meridian | 23 | 0 | 0 | 0 | 23 | 0 | 23/23 | 23/23 |
| **GB** | Gallbladder Meridian | 44 | 2 | 0 | 0 | 42 | 0 | 44/44 | 44/44 |
| **LR** | Liver Meridian | 14 | 0 | 0 | 0 | 14 | 0 | 14/14 | 14/14 |
| **GV** | Governing Vessel (Du Mai) | 29 | 3 | 0 | 0 | 26 | 0 | Midline | Midline |
| **CV** | Conception Vessel (Ren Mai) | 24 | 1 | 0 | 0 | 23 | 0 | Midline | Midline |
| **TOTAL** | **All 14 Channels** | **362** | **18** | **0** | **0** | **344** | **0** | **100%** | **100%** |

---

## 2. COMPLETE 361-POINT INVENTORY TABLE

Every classical acupuncture point code in the application is enumerated below with its verified classification and provenance:

| Point Code | Meridian | Names (EN / ZH / VI) | Class | Localization Method | Canonical Position [X, Y, Z] (m) | Landmark / Skeletal Anchor | WHO Reference Rule | Uncertainty | Review Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LU1** | LU | Zhongfu / 中府 / Trung Phủ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1297, 1.3475, 0.0688]` | FJ2810 (Skin of body) - Triangle #3... | 锁骨外端下方约一横指、再向下一肋间的凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LU2** | LU | Yunmen / 云门 / Vân Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1526, 1.4130, 0.0138]` | FJ2810 (Skin of body) - Triangle #3... | 正坐，手叉腰，锁骨外端下方出现的三角形凹陷中点处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LU3** | LU | Tianfu / 天府 / Thiên Phủ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2333, 1.2583, -0.0105]` | FJ2810 (Skin of body) - Triangle #3... | 臂向前平举，俯头以鼻尖接触上臂内侧处即是。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LU4** | LU | Xiabai / 侠白 / Hiệp Bạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2393, 1.1878, -0.0079]` | FJ2810 (Skin of body) - Triangle #3... | 天府直下 1 横指处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LU5** | LU | Chize / 尺泽 / Xích Trạch | **CLASS_A** | `LANDMARK_DEFINED` | `[0.2340, 1.1130, 0.0056]` | Cubital crease, radial side of tend... | Forearm 12 B-cun proximal boundary | ±15.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **LU6** | LU | Kongzui / 孔最 / Khổng Tối | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2542, 1.0305, 0.0146]` | FJ2810 (Skin of body) - Triangle #3... | 尺泽与太渊连线中点向上 1 横指处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LU7** | LU | Lieque / 列缺 / Liệt Khuyết | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2809, 0.9160, 0.0108]` | FJ2810 (Skin of body) - Triangle #4... | 两手虎口交叉，一手食指压在另一手桡骨茎突上，食指尖下凹陷即是。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LU8** | LU | Jingqu / 经渠 / Kinh Cừ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2648, 0.9036, 0.0337]` | FJ2810 (Skin of body) - Triangle #3... | 太渊上 1 横指，桡动脉搏动处桡侧。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LU9** | LU | Taiyuan / 太渊 / Thái Uyên | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2730, 0.8870, 0.0413]` | FJ2810 (Skin of body) - Triangle #3... | 腕横纹桡侧端、可触及桡动脉搏动处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LU10** | LU | Yuji / 鱼际 / Ngư Tế | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2704, 0.8239, 0.0496]` | FJ2810 (Skin of body) - Triangle #3... | 拇指根部掌侧肌肉隆起（大鱼际）中点赤白肉际。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LU11** | LU | Shaoshang / 少商 / Thiếu Thương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2656, 0.7617, 0.0711]` | FJ2810 (Skin of body) - Triangle #3... | 拇指指甲桡侧缘与基底缘交点旁。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI1** | LI | Shangyang / 商阳 / Thương Dương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2686, 0.7592, 0.0541]` | FJ2810 (Skin of body) - Triangle #3... | 食指桡侧指甲根角旁。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI2** | LI | Erjian / 二间 / Nhị Gian | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2615, 0.7823, 0.0584]` | FJ2810 (Skin of body) - Triangle #3... | 握拳，第2掌指关节前桡侧、皮肤明暗交界处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI3** | LI | Sanjian / 三间 / Tam Gian | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2653, 0.8067, 0.0545]` | FJ2810 (Skin of body) - Triangle #3... | 握拳，第2掌指关节后桡侧凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI4** | LI | Hegu / 合谷 / Hợp Cốc | **CLASS_A** | `LANDMARK_DEFINED` | `[0.2860, 0.8310, 0.0141]` | Radial border of 2nd metacarpal bon... | Hand 2nd Metacarpal Proportional Divisio... | ±12.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **LI5** | LI | Yangxi / 阳溪 / Dương Khê | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2544, 0.8823, 0.0431]` | FJ2810 (Skin of body) - Triangle #3... | 拇指翘起，腕背桡侧两条肌腱（拇长、拇短伸肌腱）之间的凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI6** | LI | Pianli / 偏历 / Phần Lịch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2567, 0.9361, 0.0291]` | FJ2810 (Skin of body) - Triangle #3... | 阳溪与曲池连线，腕横纹上 4 横指处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI7** | LI | Wenliu / 温溜 / Ôn Lưu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2554, 0.9742, 0.0235]` | FJ2810 (Skin of body) - Triangle #3... | 阳溪与曲池连线中点稍下，腕横纹上约一掌处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI8** | LI | Xialian / 下廉 / Hạ Liêm | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2584, 1.0212, 0.0141]` | FJ2810 (Skin of body) - Triangle #3... | 曲池下约 5 横指，阳溪与曲池连线上。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI9** | LI | Shanglian / 上廉 / Thượng Liêm | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2532, 1.0304, 0.0151]` | FJ2810 (Skin of body) - Triangle #3... | 曲池下约 4 横指，阳溪与曲池连线上。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI10** | LI | Shousanli / 手三里 / Thủ Tam Lý | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2543, 1.0434, 0.0129]` | FJ2810 (Skin of body) - Triangle #3... | 曲池下三横指（2寸），前臂桡侧。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI11** | LI | Quchi / 曲池 / Khúc Trì | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2647, 1.1180, -0.0220]` | FJ2810 (Skin of body) - Triangle #3... | 屈肘，肘横纹桡侧端凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI12** | LI | Zhouliao / 肘髎 / 肘 Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2585, 1.1479, -0.0291]` | FJ2810 (Skin of body) - Triangle #3... | 屈肘，曲池外上方、肱骨外上髁上缘骨边处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI13** | LI | Shouwuli / 手五里 / Thủ Ngũ Lý | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2450, 1.2183, -0.0236]` | FJ2810 (Skin of body) - Triangle #3... | 曲池与肩髃连线上，曲池上 4 横指处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI14** | LI | Binao / 臂臑 / Tý Nhu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2359, 1.3184, -0.0271]` | FJ2810 (Skin of body) - Triangle #3... | 曲池与肩髃连线上，三角肌下端前缘处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI15** | LI | Jianyu / 肩髃 / Kiên Ngung | **CLASS_A** | `LANDMARK_DEFINED` | `[0.1660, 1.4210, -0.0250]` | Anterior depression of acromion of ... | Shoulder girdle bony anchor | ±8.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **LI16** | LI | Jugu / 巨骨 / Cự Cốt | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1330, 1.4402, -0.0344]` | FJ2810 (Skin of body) - Triangle #3... | 肩上方，锁骨外端与肩胛冈之间的“V”形凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI17** | LI | Tianding / 天鼎 / Thiên Đỉnh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0470, 1.4857, 0.0050]` | FJ2810 (Skin of body) - Triangle #2... | 喉结旁下方，扶突直下约 1 寸、胸锁乳突肌后缘处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI18** | LI | Futu / 扶突 / Phù Đột | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0434, 1.5176, 0.0557]` | FJ2810 (Skin of body) - Triangle #2... | 喉结旁开约 3 横指，胸锁乳突肌两头之间。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI19** | LI | Kouheliao / 口禾髎 / Khẩu Hòa Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0163, 1.5747, 0.0862]` | FJ2810 (Skin of body) - Triangle #2... | 鼻孔外缘直下、近上唇处，水沟（人中）旁开。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LI20** | LI | Yingxiang / 迎香 / Nghênh Hương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0162, 1.5925, 0.0712]` | FJ2810 (Skin of body) - Triangle #2... | 鼻翼外缘中点，旁开鼻唇沟取之。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST1** | ST | Chengqi / 承泣 / Thừa Khấp | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0236, 1.6001, 0.0632]` | FJ2810 (Skin of body) - Triangle #2... | 平视，瞳孔正下方、眼眶下缘内侧。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST2** | ST | Sibai / 四白 / Tứ Bạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0356, 1.5795, 0.0711]` | FJ2810 (Skin of body) - Triangle #2... | 瞳孔直下约一横指、眶下缘下方的小凹陷（眶下孔）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST3** | ST | Juliao / 巨髎 / Cự Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0283, 1.5791, 0.0749]` | FJ2810 (Skin of body) - Triangle #2... | 瞳孔直下，與鼻翼下緣平齊處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST4** | ST | Dicang / 地仓 / Địa Thương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0309, 1.5635, 0.0776]` | FJ2810 (Skin of body) - Triangle #2... | 口角外侧旁开约半横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST5** | ST | Daying / 大迎 / Đại Nghênh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0416, 1.5465, 0.0694]` | FJ2810 (Skin of body) - Triangle #2... | 下頷角前上方約1寸，咬肌附著處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST6** | ST | Jiache / 颊车 / Giáp Xa | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0530, 1.5556, 0.0567]` | FJ2810 (Skin of body) - Triangle #2... | 咬牙时下颌角前上方肌肉鼓起最高点。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST7** | ST | Xiaguan / 下关 / Hạ Quan | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0583, 1.5772, 0.0469]` | FJ2810 (Skin of body) - Triangle #2... | 闭口，耳屏前方颧弓下凹陷；张口时凹陷消失。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST8** | ST | Touwei / 头维 / Đầu Duy | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0615, 1.6386, 0.0381]` | FJ2810 (Skin of body) - Triangle #2... | 额角发际向上半横指处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST9** | ST | Renying / 人迎 / Nhân Nghênh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0301, 1.5022, 0.0646]` | FJ2810 (Skin of body) - Triangle #2... | 喉结旁开约1.5寸，胸锁乳突肌前缘可触及动脉搏动处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST10** | ST | Shuitu / 水突 / Thủy Đột | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0318, 1.4788, 0.0187]` | FJ2810 (Skin of body) - Triangle #2... | 人迎穴直下，胸鎖乳突肌前緣。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST11** | ST | Qishe / 气舍 / Khí Xá | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0346, 1.4553, 0.0220]` | FJ2810 (Skin of body) - Triangle #2... | 鎖骨內側端上緣，胸鎖乳突肌胸骨頭與鎖骨頭之間凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST12** | ST | Quepen / 缺盆 / Khuyết 盆 | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0489, 1.4325, 0.0304]` | FJ2810 (Skin of body) - Triangle #2... | 鎖骨中點上緣凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST13** | ST | Qihu / 气户 / Khí Hộ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0502, 1.4078, 0.0540]` | FJ2810 (Skin of body) - Triangle #2... | 鎖骨中點下緣，距前正中線4寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST14** | ST | Kufang / 库房 / 库 Phòng | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0644, 1.3475, 0.0994]` | FJ2810 (Skin of body) - Triangle #2... | 氣戶穴直下1.6寸，第一肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST15** | ST | Wuyi / 屋翳 / Ốc Ế | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0653, 1.3187, 0.1120]` | FJ2810 (Skin of body) - Triangle #2... | 庫房穴直下1.6寸，第二肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST16** | ST | Yingchuang / 膺窗 / Ưng Song | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0663, 1.2899, 0.1211]` | FJ2810 (Skin of body) - Triangle #2... | 屋翳穴直下1.6寸，第三肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST17** | ST | Ruzhong / 乳中 / Nhũ Trung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0673, 1.2611, 0.1240]` | FJ2810 (Skin of body) - Triangle #2... | 乳頭中央。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST18** | ST | Rugen / 乳根 / Nhũ Căn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0672, 1.2323, 0.1167]` | FJ2810 (Skin of body) - Triangle #2... | 乳頭正下方，往下摸到一根肋骨（第五肋骨）的間隙處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST19** | ST | Burong / 不容 / Bất Dung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0480, 1.1748, 0.1193]` | FJ2810 (Skin of body) - Triangle #2... | 臍上6寸，前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST20** | ST | Chengman / 承满 / Thừa Mãn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0480, 1.1460, 0.1176]` | FJ2810 (Skin of body) - Triangle #2... | 不容穴直下1寸，前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST21** | ST | Liangmen / 梁门 / Lương Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0480, 1.1172, 0.1112]` | FJ2810 (Skin of body) - Triangle #2... | 承滿穴直下1寸，前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST22** | ST | Guanmen / 关门 / Quan Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0481, 1.0883, 0.1104]` | FJ2810 (Skin of body) - Triangle #2... | 梁門穴直下1寸，前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST23** | ST | Taiyi / 太乙 / Thái 乙 | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0481, 1.0690, 0.1077]` | FJ2810 (Skin of body) - Triangle #2... | 關門穴直下1寸，前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST24** | ST | Huaroumen / 滑肉门 / Hoạt Nhục Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0481, 1.0449, 0.1041]` | FJ2810 (Skin of body) - Triangle #2... | 太乙穴直下1寸，前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST25** | ST | Tianshu / 天枢 / Thiên Xu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0482, 1.0209, 0.1013]` | FJ2810 (Skin of body) - Triangle #2... | 脐中旁开约三横指（2寸）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST26** | ST | Wailing / 外陵 / Ngoại Lăng | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0481, 0.9921, 0.0945]` | FJ2810 (Skin of body) - Triangle #2... | 天樞穴直下1寸，前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST27** | ST | Daju / 大巨 / Đại Cự | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0481, 0.9681, 0.0869]` | FJ2810 (Skin of body) - Triangle #2... | 外陵穴直下1寸，前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST28** | ST | Shuidao / 水道 / Thủy Đạo | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0481, 0.9394, 0.0773]` | FJ2810 (Skin of body) - Triangle #4... | 大巨穴直下3寸（臍下3寸），前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST29** | ST | Guilai / 归来 / Quy Lai | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0481, 0.9106, 0.0692]` | FJ2810 (Skin of body) - Triangle #4... | 水道穴直下2寸，前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST30** | ST | Qichong / 气冲 / Khí Xung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0481, 0.8818, 0.0622]` | FJ2810 (Skin of body) - Triangle #4... | 歸來穴直下1寸（臍下5寸），前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST31** | ST | Biguan / 髀关 / Bễ Quan | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0879, 0.7552, 0.0709]` | FJ2810 (Skin of body) - Triangle #2... | 髂前上棘與髕骨外緣連線上，平臀溝處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST32** | ST | Futu / 伏兔 / Phục Thỏ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0928, 0.6333, 0.0686]` | FJ2810 (Skin of body) - Triangle #2... | 膝蓋上6寸，大腿前側肌肉隆起處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST33** | ST | Yinshi / 阴市 / Âm Thị | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0922, 0.5753, 0.0592]` | FJ2810 (Skin of body) - Triangle #2... | 髂前上棘與髕骨外緣連線上，髕底上3寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST34** | ST | Liangqiu / 梁丘 / Lương Khâu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0917, 0.5116, 0.0515]` | FJ2810 (Skin of body) - Triangle #2... | 伸腿绷紧大腿，髌骨外上缘上两横指凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST35** | ST | Dubi / 犊鼻 / Độc Tị | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0990, 0.4350, 0.0266]` | Depression lateral to patellar liga... | Lower extremity knee baseline anchor | ±14.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **ST36** | ST | Zusanli / 足三里 / Túc Tam Lý | **CLASS_A** | `LANDMARK_DEFINED` | `[0.1110, 0.3680, 0.0146]` | Anterior aspect of leg, 3 B-cun inf... | Leg 16 B-cun segment (3 cun inferior to ... | ±12.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **ST37** | ST | Shangjuxu / 上巨虚 / Thượng Cự 虚 | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1055, 0.3344, 0.0160]` | FJ2810 (Skin of body) - Triangle #3... | 足三里直下四横指，胫骨外约一横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST38** | ST | Tiaokou / 条口 / Điều Khẩu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1039, 0.3042, 0.0120]` | FJ2810 (Skin of body) - Triangle #2... | 犊鼻与外踝连线中点附近，胫骨外约一横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST39** | ST | Xiajuxu / 下巨虚 / Hạ Cự 虚 | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1000, 0.2723, 0.0077]` | FJ2810 (Skin of body) - Triangle #2... | 膝蓋外側凹陷下三手掌寬處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST40** | ST | Fenglong / 丰隆 / Phong Long | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1043, 0.2486, 0.0009]` | FJ2810 (Skin of body) - Triangle #2... | 外踝尖与外膝眼连线中点，胫骨前缘外约两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST41** | ST | Jiexi / 解溪 / Giải Khê | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0820, 0.0924, 0.0154]` | FJ2810 (Skin of body) - Triangle #2... | 足背与小腿交界处横纹中点，两条大筋之间凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST42** | ST | Chongyang / 冲阳 / Xung Dương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1103, 0.0591, 0.0544]` | FJ2810 (Skin of body) - Triangle #3... | 腳背最高處，摸到脈搏跳動的地方。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST43** | ST | Xiangu / 陷谷 / Hãm Cốc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1057, 0.0435, 0.0781]` | FJ2810 (Skin of body) - Triangle #3... | 腳背第2、3趾骨縫後方的凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST44** | ST | Neiting / 内庭 / Nội Đình | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0975, 0.0350, 0.0990]` | FJ2810 (Skin of body) - Triangle #2... | Standard B-Cun | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **ST45** | ST | Lidui / 厉兑 / Lệ Đoái | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0937, 0.0260, 0.1112]` | FJ2810 (Skin of body) - Triangle #2... | 腳第2趾甲外側角旁約一分處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP1** | SP | Yinbai / 隐白 / Ẩn Bạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0841, 0.0179, 0.1007]` | FJ2810 (Skin of body) - Triangle #2... | 大腳趾內側（靠身體中心那側），指甲根角旁約0.1寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP2** | SP | Dadu / 大都 / Đại Đô | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0732, 0.0261, 0.0780]` | FJ2810 (Skin of body) - Triangle #2... | 大腳趾內側，關節前方的凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP3** | SP | Taibai / 太白 / Thái Bạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0750, 0.0459, 0.0570]` | FJ2810 (Skin of body) - Triangle #2... | 足内侧缘，第1跖趾关节后下方赤白肉际。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP4** | SP | Gongsun / 公孙 / Công Tôn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0738, 0.0670, 0.0393]` | FJ2810 (Skin of body) - Triangle #2... | 足内侧缘，第1跖骨底前下方凹陷，赤白肉际。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP5** | SP | Shangqiu / 商丘 / Thương Khâu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0462, 0.0719, -0.0019]` | FJ2810 (Skin of body) - Triangle #2... | 腳踝內側骨頭前下方的凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP6** | SP | Sanyinjiao / 三阴交 / Tam Âm Giao | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0472, 0.1500, -0.0260]` | FJ2810 (Skin of body) - Triangle #2... | 内踝尖直上四横指，胫骨内侧后缘。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP7** | SP | Lougu / 漏谷 / Lậu Cốc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0473, 0.2035, -0.0177]` | FJ2810 (Skin of body) - Triangle #2... | 內踝尖上6寸，脛骨內側緣後方。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP8** | SP | Diji / 地机 / Địa Cơ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0598, 0.2487, -0.0020]` | FJ2810 (Skin of body) - Triangle #2... | 阴陵泉直下四横指，胫骨内侧后缘。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP9** | SP | Yinlingquan / 阴陵泉 / Âm Lăng Tuyền | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0290, 0.4280, -0.0150]` | FJ2810 (Skin of body) - Triangle #2... | 沿胫骨内侧缘由下向上推，至膝下转角凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP10** | SP | Xuehai / 血海 / Huyết Hải | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0650, 0.4983, 0.0468]` | FJ2810 (Skin of body) - Triangle #2... | 屈膝，对侧手掌按膝盖，拇指尖所指股内侧隆起处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP11** | SP | Jimen / 箕门 / Cơ Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0682, 0.6200, 0.0604]` | FJ2810 (Skin of body) - Triangle #2... | 大腿內側，血海上6寸，股動脈搏動處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP12** | SP | Chongmen / 冲门 / Xung Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0721, 0.8674, 0.0647]` | FJ2810 (Skin of body) - Triangle #4... | 恥骨聯合上緣旁開3.5寸，腹股溝動脈搏動處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP13** | SP | Fushe / 府舍 / Phủ Xá | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0961, 0.9154, 0.0710]` | FJ2810 (Skin of body) - Triangle #2... | 衝門外上方0.7寸，前正中線旁開4寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP14** | SP | Fujie / 腹结 / Phúc Kết | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1009, 0.9633, 0.0753]` | FJ2810 (Skin of body) - Triangle #2... | 大橫穴下1.3寸，前正中線旁開4寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP15** | SP | Daheng / 大横 / Đại Hoành | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1057, 1.0209, 0.0753]` | FJ2810 (Skin of body) - Triangle #3... | 平脐，前正中线旁开约六横指（乳头直下一带）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP16** | SP | Fuai / 腹哀 / Phúc Ai | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1057, 1.0882, 0.0658]` | FJ2810 (Skin of body) - Triangle #3... | 臍上3寸，前正中線旁開4寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP17** | SP | Shidou / 食窦 / Thực Đậu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1249, 1.2323, 0.0846]` | FJ2810 (Skin of body) - Triangle #3... | 乳中旁開6寸，第五肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP18** | SP | Tianxi / 天溪 / Thiên Khê | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1297, 1.2659, 0.0960]` | FJ2810 (Skin of body) - Triangle #3... | 乳中旁開6寸，第四肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP19** | SP | Xiongxiang / 胸乡 / Hung Hương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1345, 1.2995, 0.0869]` | FJ2810 (Skin of body) - Triangle #3... | 乳中旁開6寸，第三肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP20** | SP | Zhourong / 周荣 / Chu Vinh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1345, 1.3331, 0.0726]` | FJ2810 (Skin of body) - Triangle #3... | 乳中旁開6寸，第二肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SP21** | SP | Dabao / 大包 / Đại Bao | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1489, 1.2515, 0.0480]` | FJ2810 (Skin of body) - Triangle #3... | 側胸部，腋中線第6肋間隙（約當腋下3寸）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **HT1** | HT | Jiquan / 极泉 / Cực Tuyền | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1887, 1.4028, 0.0133]` | FJ2810 (Skin of body) - Triangle #3... | 上臂外展，腋窝顶点、动脉搏动处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **HT2** | HT | Qingling / 青灵 / Thanh Linh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2246, 1.2082, 0.0061]` | FJ2810 (Skin of body) - Triangle #3... | 少海与极泉连线上，肘横纹上 4 横指，肱二头肌内侧沟处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **HT3** | HT | Shaohai / 少海 / Thiếu Hải | **CLASS_A** | `LANDMARK_DEFINED` | `[0.2322, 1.1139, 0.0056]` | Midway between medial epicondyle of... | Arm-Forearm transition reference | ±12.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **HT4** | HT | Lingdao / 灵道 / Linh Đạo | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2501, 0.9226, 0.0321]` | FJ2810 (Skin of body) - Triangle #3... | 神门上 2 横指，尺侧腕屈肌腱桡侧。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **HT5** | HT | Tongli / 通里 / Thông Lý | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2513, 0.9088, 0.0346]` | FJ2810 (Skin of body) - Triangle #3... | 神门上一横指，尺侧筋腱桡侧。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **HT6** | HT | Yinxi / 阴郄 / Âm Khích | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2493, 0.8961, 0.0381]` | FJ2810 (Skin of body) - Triangle #3... | 神门上半横指，尺侧腕屈肌腱桡侧。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **HT7** | HT | Shenmen / 神门 / Thần Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2380, 0.8840, 0.0401]` | FJ2810 (Skin of body) - Triangle #3... | 腕横纹小指侧，摸到豌豆骨，其桡侧筋腱旁凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **HT8** | HT | Shaofu / 少府 / Thiếu Phủ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2642, 0.8161, 0.0517]` | FJ2810 (Skin of body) - Triangle #3... | 握拳时小指尖所指的掌心处，第4、5掌骨之间。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **HT9** | HT | Shaochong / 少冲 / Thiếu Xung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2532, 0.7627, 0.0779]` | FJ2810 (Skin of body) - Triangle #3... | 小指桡侧指甲根角旁。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI1** | SI | Shaoze / 少泽 / Thiếu Trạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2504, 0.7533, 0.0931]` | FJ2810 (Skin of body) - Triangle #3... | 小指內側（靠外側手邊），指甲根角旁約0.1寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI2** | SI | Qiangu / 前谷 / Tiền Cốc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2437, 0.7883, 0.0634]` | FJ2810 (Skin of body) - Triangle #3... | 小指根部關節前方的橫紋盡頭處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI3** | SI | Houxi / 后溪 / Hậu Khê | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1618, 0.7974, -0.0249]` | FJ2810 (Skin of body) - Triangle #3... | 握拳，第5掌指关节后掌横纹尽头隆起处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI4** | SI | Wangu / 腕骨 / Uyển Cốt | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2536, 0.8652, 0.0496]` | FJ2810 (Skin of body) - Triangle #3... | 手掌尺侧（小指侧），沿第5掌骨向腕推，赤白肉际凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI5** | SI | Yanggu / 阳谷 / Dương Cốc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2496, 0.8814, 0.0435]` | FJ2810 (Skin of body) - Triangle #3... | 小指側手腕皺摺處，按壓有凹陷的位置。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI6** | SI | Yanglao / 养老 / 养 Lão | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2489, 0.9026, 0.0361]` | FJ2810 (Skin of body) - Triangle #3... | 掌心向下，按住尺骨小头高点，掌心转向胸前时手指滑入的骨缝处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI7** | SI | Zhizheng / 支正 / Chi Chính | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2536, 1.0131, -0.0513]` | FJ2810 (Skin of body) - Triangle #3... | 手腕背橫紋往上量約5寸（約一隻手掌寬），前臂外側中央凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI8** | SI | Xiaohai / 小海 / Tiểu Hải | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2557, 1.1103, -0.0522]` | FJ2810 (Skin of body) - Triangle #3... | 屈肘，肘尖与肘内侧高骨之间的凹陷（按之常有触电感）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI9** | SI | Jianzhen / 肩贞 / Kiên Trinh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2230, 1.3687, -0.0703]` | FJ2810 (Skin of body) - Triangle #3... | 腋後紋頭直上1寸，肩關節後下方。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI10** | SI | Naoshu / 臑俞 / Nhu Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1923, 1.3674, -0.1001]` | FJ2810 (Skin of body) - Triangle #3... | 肩貞直下，腋後皺襞上緣。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI11** | SI | Tianzong / 天宗 / Thiên Tông | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1348, 1.3098, -0.1299]` | FJ2810 (Skin of body) - Triangle #3... | 肩胛骨冈下窝中央凹陷，按之酸胀明显处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI12** | SI | Bingfeng / 秉风 / Bỉnh Phong | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1087, 1.4111, -0.1239]` | FJ2810 (Skin of body) - Triangle #3... | 肩胛岡上緣中點上方凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI13** | SI | Quyuan / 曲垣 / Khúc Viên | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0750, 1.4232, -0.1236]` | FJ2810 (Skin of body) - Triangle #2... | 肩胛岡內側端上緣凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI14** | SI | Jianwaishu / 肩外俞 / Kiên Ngoại Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0650, 1.4422, -0.1110]` | FJ2810 (Skin of body) - Triangle #2... | 第一胸椎棘突下旁開3寸，肩胛骨內側緣。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI15** | SI | Jianzhongshu / 肩中俞 / Kiên Trung Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0447, 1.4426, -0.1139]` | FJ2810 (Skin of body) - Triangle #2... | 第七頸椎（大椎）旁開2寸，肩胛骨內側緣上端。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI16** | SI | Tianchuang / 天窗 / Thiên Song | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0368, 1.5020, -0.0709]` | FJ2810 (Skin of body) - Triangle #2... | 正坐或仰臥，於喉結水平高度，找到頸部側面明顯的胸鎖乳突肌，在其後緣（靠近後頸側）... | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI17** | SI | Tianrong / 天容 / Thiên Dung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0813, 1.4301, 0.0084]` | FJ2810 (Skin of body) - Triangle #2... | 下頷角後方，胸鎖乳突肌前緣凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI18** | SI | Quanliao / 颧髎 / Quyền Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0398, 1.5776, 0.0695]` | FJ2810 (Skin of body) - Triangle #2... | 颧骨最高点下缘、外眼角直下凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **SI19** | SI | Tinggong / 听宫 / Thính Cung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0645, 1.5920, 0.0328]` | FJ2810 (Skin of body) - Triangle #2... | 微张口，耳屏前方出现的凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL1** | BL | Jingming / 睛明 / Tình Minh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0135, 1.6051, 0.0728]` | FJ2810 (Skin of body) - Triangle #2... | 闭目，内眼角稍内上方的小凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL2** | BL | Zanzhu / 攒竹 / Toản Trúc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0183, 1.6198, 0.0811]` | FJ2810 (Skin of body) - Triangle #2... | 眉毛内侧端凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL3** | BL | Meichong / 眉冲 / Mi Xung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0211, 1.6653, 0.0716]` | FJ2810 (Skin of body) - Triangle #2... | 攢竹直上入髮際0.5寸，神庭旁0.75寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL4** | BL | Qucha / 曲差 / Khúc Sai | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0292, 1.6812, 0.0585]` | FJ2810 (Skin of body) - Triangle #2... | 神庭旁1.5寸，前髮際上0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL5** | BL | Wuchu / 五处 / Ngũ Xứ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0296, 1.7026, 0.0299]` | FJ2810 (Skin of body) - Triangle #2... | 曲差後0.5寸（即前髮際上1寸，神庭旁1.5寸）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL6** | BL | Chengguang / 承光 / Thừa Quang | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0275, 1.7118, 0.0050]` | FJ2810 (Skin of body) - Triangle #2... | 五處後1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL7** | BL | Tongtian / 通天 / Thông Thiên | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0288, 1.7134, -0.0263]` | FJ2810 (Skin of body) - Triangle #2... | 百會前約1寸處往外旁開約兩指寬。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL8** | BL | Luoque / 络却 / Lạc Khước | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0306, 1.7029, -0.0758]` | FJ2810 (Skin of body) - Triangle #2... | 承光後1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL9** | BL | Yuzhen / 玉枕 / Ngọc Chẩm | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0300, 1.6492, -0.1163]` | FJ2810 (Skin of body) - Triangle #2... | 腦戶（後正中線，枕外隆凸上緣）旁1.3寸，向上約1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL10** | BL | Tianzhu / 天柱 / Thiên Trụ | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0300, 1.5695, -0.0800]` | Trapezius muscle occipital attachme... | Suboccipital transverse division | ±10.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **BL11** | BL | Dazhu / 大杼 / Đại Trữ | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0350, 1.4200, -0.0880]` | 1.5 cun lateral to T1 spinous proce... | Back Bladder line 1.5 B-cun | ±10.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **BL12** | BL | Fengmen / 风门 / Phong Môn | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0350, 1.3900, -0.0900]` | 1.5 cun lateral to T2 spinous proce... | Back Bladder line 1.5 B-cun | ±10.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **BL13** | BL | Feishu / 肺俞 / Phế Du | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0350, 1.3600, -0.0920]` | 1.5 cun lateral to T3 spinous proce... | Back Bladder line 1.5 B-cun | ±10.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **BL14** | BL | Jueyinshu / 厥阴俞 / 厥 Âm Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0337, 1.3388, -0.1348]` | FJ2810 (Skin of body) - Triangle #2... | 两肩胛冈内侧端连线约平第3胸椎，再下一节棘突下旁开两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL15** | BL | Xinshu / 心俞 / 心 Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0338, 1.3099, -0.1355]` | FJ2810 (Skin of body) - Triangle #2... | 两肩胛骨下角连线平第7胸椎，向上数2椎，旁开两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL16** | BL | Dushu / 督俞 / Đốc Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0338, 1.2859, -0.1316]` | FJ2810 (Skin of body) - Triangle #2... | 膈俞（第7胸椎）上一椎體，旁開兩指寬。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL17** | BL | Geshu / 膈俞 / Cách Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0338, 1.2618, -0.1278]` | FJ2810 (Skin of body) - Triangle #2... | 两肩胛骨下角连线平第7胸椎，棘突下旁开两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL18** | BL | Ganshu / 肝俞 / 肝 Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0338, 1.2329, -0.1254]` | FJ2810 (Skin of body) - Triangle #2... | 肩胛下角平第7胸椎，向下数2椎，旁开两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL19** | BL | Danshu / 胆俞 / 胆 Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0338, 1.2087, -0.1214]` | FJ2810 (Skin of body) - Triangle #2... | 约平两侧肩胛下角连线下方第3节棘突下旁开两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL20** | BL | Pishu / 脾俞 / Tỳ Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0338, 1.1846, -0.1164]` | FJ2810 (Skin of body) - Triangle #2... | 第12肋端约平第2腰椎，向上约3椎，旁开两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL21** | BL | Weishu / 胃俞 / Vị Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0337, 1.1557, -0.1099]` | FJ2810 (Skin of body) - Triangle #2... | 脾俞下一椎，旁开两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL22** | BL | Sanjiaoshu / 三焦俞 / Tam Tiêu Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0337, 1.1268, -0.1064]` | FJ2810 (Skin of body) - Triangle #2... | 约平最下肋端连线（第1腰椎），棘突下旁开两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL23** | BL | Shenshu / 肾俞 / Thận Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0337, 1.0979, -0.1025]` | FJ2810 (Skin of body) - Triangle #2... | 与肚脐相对的腰椎（第2腰椎）棘突下，旁开两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL24** | BL | Qihaishu / 气海俞 / Khí Hải Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0337, 1.0692, -0.0978]` | FJ2810 (Skin of body) - Triangle #2... | 腎俞（第2腰椎）下一椎體（第3腰椎），旁開約兩指寬。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL25** | BL | Dachangshu / 大肠俞 / Đại Trường Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0337, 1.0404, -0.0970]` | FJ2810 (Skin of body) - Triangle #2... | 两侧髂嵴最高点连线平第4腰椎，棘突下旁开两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL26** | BL | Guanyuanshu / 关元俞 / Quan Nguyên Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0337, 1.0116, -0.1027]` | FJ2810 (Skin of body) - Triangle #2... | 腰陽關（第4腰椎下）下一椎體，旁開兩指寬。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL27** | BL | Xiaochangshu / 小肠俞 / Tiểu Trường Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0337, 0.9829, -0.1127]` | FJ2810 (Skin of body) - Triangle #2... | 大腸俞（第4腰椎）往下至骶骨，第一對骶後孔外側凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL28** | BL | Pangguangshu / 膀胱俞 / Bàng Quang Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0338, 0.9589, -0.1260]` | FJ2810 (Skin of body) - Triangle #2... | 骶部，约平第2骶后孔，正中嵴旁开两横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL29** | BL | Zhonglvshu / 中膂俞 / Trung 膂 Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0318, 0.9349, -0.1358]` | FJ2810 (Skin of body) - Triangle #2... | 白環俞上一椎體，旁開兩指寬。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL30** | BL | Baihuanshu / 白环俞 / Bạch Hoàn Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0299, 0.9110, -0.1398]` | FJ2810 (Skin of body) - Triangle #2... | 骶正中嵴旁開1.5寸，平第4骶後孔。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL31** | BL | Shangliao / 上髎 / Thượng Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0270, 0.9685, -0.1189]` | FJ2810 (Skin of body) - Triangle #2... | 骶骨背面第一對骶後孔（約當髂後上棘內下方）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL32** | BL | Ciliao / 次髎 / Thứ Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0270, 0.9445, -0.1309]` | FJ2810 (Skin of body) - Triangle #2... | 骶骨上、髂后上棘内下方可触及的骨孔处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL33** | BL | Zhongliao / 中髎 / Trung Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0270, 0.9205, -0.1375]` | FJ2810 (Skin of body) - Triangle #2... | 次髎下方，第三對骶後孔。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL34** | BL | Xialiao / 下髎 / Hạ Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0270, 0.8966, -0.1395]` | FJ2810 (Skin of body) - Triangle #2... | 中髎下方，第四對骶後孔。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL35** | BL | Huiyang / 会阳 / Hội Dương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0242, 0.8678, -0.1317]` | FJ2810 (Skin of body) - Triangle #2... | 尾骨端旁開0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL36** | BL | Chengfu / 承扶 / Thừa Phù | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0733, 0.7565, -0.0994]` | FJ2810 (Skin of body) - Triangle #2... | 臀溝正中（臀部下方橫紋中點）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL37** | BL | Yinmen / 殷门 / Ân Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0777, 0.6418, -0.0922]` | FJ2810 (Skin of body) - Triangle #2... | 承扶下6寸，大腿後側正中。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL38** | BL | Fuxi / 浮郄 / Phù Khích | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0808, 0.5101, -0.0762]` | FJ2810 (Skin of body) - Triangle #2... | 委陽穴上1寸，股二頭肌腱內側。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL39** | BL | Weiyang / 委阳 / Ủy Dương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0923, 0.4591, -0.0875]` | FJ2810 (Skin of body) - Triangle #2... | 膝蓋後方橫紋的外側盡頭處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL40** | BL | Weizhong / 委中 / Ủy Trung | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0810, 0.4450, -0.0953]` | Popliteal crease midpoint between b... | Boundary between Thigh 19 B-cun and Leg ... | ±16.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **BL41** | BL | Fufen / 附分 / Phụ Phân | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0457, 1.4083, -0.1288]` | FJ2810 (Skin of body) - Triangle #2... | 風門旁開1.5寸（即兩指寬再加1.5寸）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL42** | BL | Pohu / 魄户 / Phách Hộ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0577, 1.3580, -0.1414]` | FJ2810 (Skin of body) - Triangle #2... | 肺俞旁開1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL43** | BL | Gaohuang / 膏肓 / Cao Hoang | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0578, 1.3291, -0.1442]` | FJ2810 (Skin of body) - Triangle #2... | 厥陰俞旁開1.5寸，肩胛骨內側緣。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL44** | BL | Shentang / 神堂 / Thần Đường | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0578, 1.3003, -0.1407]` | FJ2810 (Skin of body) - Triangle #2... | 心俞旁開1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL45** | BL | Yixi / 譩譆 / Y Hê | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0579, 1.2714, -0.1358]` | FJ2810 (Skin of body) - Triangle #2... | 肩胛骨下角連線往上一個椎體（第六胸椎），旁開一虎口（約4橫指）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL46** | BL | Geguan / 膈关 / Cách Quan | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0579, 1.2425, -0.1317]` | FJ2810 (Skin of body) - Triangle #2... | 膈俞旁開1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL47** | BL | Hunmen / 魂门 / Hồn Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0578, 1.2136, -0.1255]` | FJ2810 (Skin of body) - Triangle #2... | 肝俞旁開1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL48** | BL | Yanggang / 阳纲 / Dương 纲 | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0578, 1.1895, -0.1197]` | FJ2810 (Skin of body) - Triangle #2... | 膽俞旁開1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL49** | BL | Yishe / 意舍 / Ý Xá | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0578, 1.1653, -0.1145]` | FJ2810 (Skin of body) - Triangle #2... | 脾俞旁開約兩指寬（因內與脾俞相平，脾俞旁開1.5寸，再加1.5寸）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL50** | BL | Weicang / 胃仓 / Vị Thương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0577, 1.1364, -0.1081]` | FJ2810 (Skin of body) - Triangle #2... | 胃俞旁開1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL51** | BL | Huangmen / 肓门 / Hoang Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0577, 1.1076, -0.1022]` | FJ2810 (Skin of body) - Triangle #2... | 三焦俞旁開1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL52** | BL | Zhishi / 志室 / Chí Thất | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0577, 1.0788, -0.0965]` | FJ2810 (Skin of body) - Triangle #2... | 命门（第2腰椎下）旁开约四横指（3寸），腰部肌肉外侧。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL53** | BL | Baohuang / 胞肓 / Bào Hoang | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0529, 0.9541, -0.1294]` | FJ2810 (Skin of body) - Triangle #2... | 膀胱俞旁開1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL54** | BL | Zhibian / 秩边 / Trật Biên | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0578, 0.8966, -0.1411]` | FJ2810 (Skin of body) - Triangle #2... | 白環俞旁開1.5寸，臀大肌外緣。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL55** | BL | Heyang / 合阳 / Hợp Dương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0927, 0.3755, -0.1086]` | FJ2810 (Skin of body) - Triangle #2... | 委中穴直下2寸，小腿後側正中。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL56** | BL | Chengjin / 承筋 / Thừa Cân | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0966, 0.3154, -0.1061]` | FJ2810 (Skin of body) - Triangle #2... | 合陽直下2寸，小腿肚最高點。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL57** | BL | Chengshan / 承山 / Thừa Sơn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0995, 0.2528, -0.0877]` | FJ2810 (Skin of body) - Triangle #3... | 伸直小腿或提踵，腓肠肌肌腹下方出现的 "人" 字形凹陷尖端。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL58** | BL | Feiyang / 飞扬 / Phi Dương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0890, 0.1830, -0.0734]` | FJ2810 (Skin of body) - Triangle #2... | 承山穴向外側旁開一個大拇指寬，再往下一點點。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL59** | BL | Fuyang / 跗阳 / Phụ Dương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0926, 0.1302, -0.0623]` | FJ2810 (Skin of body) - Triangle #2... | 崑崙穴直上3寸，跟腱前緣。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL60** | BL | Kunlun / 昆仑 / Côn Lôn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1063, 0.0640, -0.0570]` | FJ2810 (Skin of body) - Triangle #3... | 外踝最高点与跟腱之间凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL61** | BL | Pucan / 仆参 / Bộc Tham | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1015, 0.1304, -0.0277]` | FJ2810 (Skin of body) - Triangle #3... | 足跟外側，崑崙直下，跟骨外側下方凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL62** | BL | Shenmai / 申脉 / Thân Mạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1005, 0.1011, -0.0145]` | FJ2810 (Skin of body) - Triangle #2... | 外踝正下方凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL63** | BL | Jinmen / 金门 / Kim Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1006, 0.0821, 0.0096]` | FJ2810 (Skin of body) - Triangle #2... | 腳掌外側，外踝骨前緣垂直往下，骰骨下方的凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL64** | BL | Jinggu / 京骨 / Kinh Cốt | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1144, 0.0678, 0.0286]` | FJ2810 (Skin of body) - Triangle #3... | 腳外側中間有一塊突出的骨頭，其下方的凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL65** | BL | Shugu / 束骨 / Thúc Cốt | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1206, 0.0510, 0.0572]` | FJ2810 (Skin of body) - Triangle #3... | 小腳趾根部關節後方的凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL66** | BL | Zutonggu / 足通谷 / Túc Thông Cốc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1221, 0.0366, 0.0809]` | FJ2810 (Skin of body) - Triangle #3... | 小腳趾根部關節前方的凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **BL67** | BL | Zhiyin / 至阴 / Chí Âm | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1224, 0.0296, 0.1021]` | FJ2810 (Skin of body) - Triangle #3... | 小趾外侧趾甲根角旁。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI1** | KI | Yongquan / 涌泉 / Dũng Tuyền | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1010, 0.0031, 0.0690]` | FJ2810 (Skin of body) - Triangle #2... | 卷足趾，足底前1/3正中出现的凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI2** | KI | Rangu / 然谷 / Nhiên Cốc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0655, 0.0853, 0.0183]` | FJ2810 (Skin of body) - Triangle #2... | 足内侧舟骨粗隆（内踝前下方的高骨）下缘，赤白肉际。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI3** | KI | Taixi / 太溪 / Thái Khê | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[-0.0759, 0.0845, -0.0704]` | FJ2810 (Skin of body) - Triangle #1... | 内踝最高点与跟腱之间凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI4** | KI | Dazhong / 大钟 / Đại Chung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0422, 0.1268, -0.0400]` | FJ2810 (Skin of body) - Triangle #2... | 腳踝內側骨頭後下方，跟腱前的凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI5** | KI | Shuiquan / 水泉 / Thủy Tuyền | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0435, 0.1139, -0.0296]` | FJ2810 (Skin of body) - Triangle #2... | 腳踝內側太溪穴往下約一橫指處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI6** | KI | Zhaohai / 照海 / Chiếu Hải | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0381, 0.0833, -0.0245]` | FJ2810 (Skin of body) - Triangle #2... | 内踝尖正下方约一横指凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI7** | KI | Fuliu / 复溜 / Phục Lưu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0453, 0.1247, -0.0257]` | FJ2810 (Skin of body) - Triangle #2... | 太溪直上三横指，跟腱前缘。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI8** | KI | Jiaoxin / 交信 / Giao Tín | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0460, 0.1330, -0.0255]` | FJ2810 (Skin of body) - Triangle #2... | 內踝尖上2寸，脛骨內側緣後方，復溜穴前0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI9** | KI | Zhubin / 筑宾 / Trúc Tân | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0568, 0.2296, -0.0049]` | FJ2810 (Skin of body) - Triangle #2... | 內踝上方約一個手掌長度（約5寸），小腿肚內側下方凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI10** | KI | Yingu / 阴谷 / Âm Cốc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0559, 0.4306, 0.0149]` | FJ2810 (Skin of body) - Triangle #2... | 屈膝，腘窝横纹内侧端两筋之间。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI11** | KI | Henggu / 横骨 / Hoành Cốt | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0193, 0.8914, 0.0607]` | FJ2810 (Skin of body) - Triangle #4... | 臍下5寸，前正中線旁開0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI12** | KI | Dahe / 大赫 / Đại Hách | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0193, 0.9202, 0.0709]` | FJ2810 (Skin of body) - Triangle #4... | 中極穴左右各旁開約半拇指寬（約0.5寸）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI13** | KI | Qixue / 气穴 / Khí Huyệt | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0193, 0.9489, 0.0813]` | FJ2810 (Skin of body) - Triangle #4... | 臍下3寸，前正中線旁開0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI14** | KI | Siman / 四满 / Tứ Mãn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0193, 0.9777, 0.0921]` | FJ2810 (Skin of body) - Triangle #2... | 臍下2寸，前正中線旁開0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI15** | KI | Zhongzhu / 中注 / Trung 注 | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0193, 1.0065, 0.1032]` | FJ2810 (Skin of body) - Triangle #2... | 臍下1寸，前正中線旁開0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI16** | KI | Huangshu / 肓俞 / Hoang Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0193, 1.0257, 0.1036]` | FJ2810 (Skin of body) - Triangle #2... | 臍旁開0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI17** | KI | Shangqu / 商曲 / Thương Khúc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0193, 1.0546, 0.1048]` | FJ2810 (Skin of body) - Triangle #2... | 臍上2寸，前正中線旁開0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI18** | KI | Shiguan / 石关 / Thạch Quan | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0193, 1.0787, 0.1098]` | FJ2810 (Skin of body) - Triangle #2... | 臍上6寸，前正中線旁開0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI19** | KI | Yindu / 阴都 / Âm Đô | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0192, 1.1076, 0.1134]` | FJ2810 (Skin of body) - Triangle #2... | 臍上4寸，前正中線旁開0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI20** | KI | Futonggu / 腹通谷 / Phúc Thông Cốc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0192, 1.1316, 0.1165]` | FJ2810 (Skin of body) - Triangle #2... | 臍上5寸，前正中線旁開0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI21** | KI | Youmen / 幽门 / U Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0192, 1.1556, 0.1183]` | FJ2810 (Skin of body) - Triangle #2... | 臍上6寸，前正中線旁開0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI22** | KI | Bulang / 步廊 / Bộ Lang | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0528, 1.2131, 0.1203]` | FJ2810 (Skin of body) - Triangle #2... | 前正中線旁開2寸，第五肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI23** | KI | Shenfeng / 神封 / Thần Phong | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0528, 1.2467, 0.1202]` | FJ2810 (Skin of body) - Triangle #2... | 前正中線旁開2寸，第四肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI24** | KI | Lingxu / 灵墟 / Linh Khư | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0529, 1.2803, 0.1245]` | FJ2810 (Skin of body) - Triangle #2... | 前正中線旁開2寸，第三肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI25** | KI | Shencang / 神藏 / Thần Tàng | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0529, 1.3139, 0.1158]` | FJ2810 (Skin of body) - Triangle #2... | 前正中線旁開2寸，第二肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI26** | KI | Yuzhong / 彧中 / Húc Trung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0529, 1.3475, 0.1003]` | FJ2810 (Skin of body) - Triangle #2... | 前正中線旁開2寸，第一肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **KI27** | KI | Shufu / 俞府 / Du Phủ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0404, 1.4122, 0.0518]` | FJ2810 (Skin of body) - Triangle #2... | 鎖骨下緣，前正中線旁開2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **PC1** | PC | Tianchi / 天池 / Thiên Trì | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1105, 1.2419, 0.1022]` | FJ2810 (Skin of body) - Triangle #3... | 乳头外侧 1 横指、与乳头同高的肋间处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **PC2** | PC | Tianquan / 天泉 / Thiên Tuyền | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2208, 1.2782, 0.0015]` | FJ2810 (Skin of body) - Triangle #3... | 腋前纹头直下 2 横指，上臂内侧肱二头肌处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **PC3** | PC | Quze / 曲泽 / Khúc Trạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2318, 1.1135, 0.0056]` | FJ2810 (Skin of body) - Triangle #3... | 微屈肘，肘横纹上大筋（肱二头肌腱）尺侧凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **PC4** | PC | Ximen / 郄门 / Khích Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2534, 0.9932, 0.0212]` | FJ2810 (Skin of body) - Triangle #3... | 腕横纹与肘横纹连线下 2/5 处，两条肌腱之间。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **PC5** | PC | Jianshi / 间使 / Gian Sử | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2555, 0.9505, 0.0271]` | FJ2810 (Skin of body) - Triangle #3... | 内关上 1 横指，两条肌腱之间。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **PC6** | PC | Neiguan / 内关 / Nội Quan | **CLASS_A** | `LANDMARK_DEFINED` | `[0.2412, 0.9250, 0.0314]` | Between tendons of palmaris longus ... | Forearm 12 B-cun segment (2 cun proximal... | ±10.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **PC7** | PC | Daling / 大陵 / Đại Lăng | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2542, 0.8776, 0.0451]` | FJ2810 (Skin of body) - Triangle #3... | 腕横纹正中，两筋之间。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **PC8** | PC | Laogong / 劳宫 / Lao Cung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2646, 0.8105, 0.0533]` | FJ2810 (Skin of body) - Triangle #3... | 握拳屈指，中指尖所指掌心处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **PC9** | PC | Zhongchong / 中冲 / Trung Xung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2520, 0.7453, 0.0719]` | FJ2810 (Skin of body) - Triangle #3... | 中指尖端正中处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE1** | TE | Guanchong / 关冲 / Quan Xung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2518, 0.7437, 0.1080]` | FJ2810 (Skin of body) - Triangle #3... | 无名指指甲尺侧（靠小指侧）根角旁。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE2** | TE | Yemen / 液门 / Dịch Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2409, 0.7981, 0.0558]` | FJ2810 (Skin of body) - Triangle #3... | 手第4、5指縫間的凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE3** | TE | Zhongzhu / 中渚 / Trung Chử | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2416, 0.8265, 0.0530]` | FJ2810 (Skin of body) - Triangle #3... | 握拳，第4、5掌指关节后方凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE4** | TE | Yangchi / 阳池 / Dương Trì | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2476, 0.8840, -0.0085]` | FJ2810 (Skin of body) - Triangle #3... | 腕背横纹中点偏尺侧，指伸肌腱与小指伸肌腱之间凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE5** | TE | Waiguan / 外关 / Ngoại Quan | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2450, 0.9250, -0.0241]` | FJ2810 (Skin of body) - Triangle #3... | 与内关相对，腕背横纹上三横指，两骨之间。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE6** | TE | Zhigou / 支沟 / Chi Câu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2460, 0.9495, -0.0338]` | FJ2810 (Skin of body) - Triangle #3... | 腕背横纹上四横指，前臂两骨之间。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE7** | TE | Huizong / 会宗 / Hội Tông | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2455, 0.9544, -0.0356]` | FJ2810 (Skin of body) - Triangle #3... | 支溝穴旁開一指寬處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE8** | TE | Sanyangluo / 三阳络 / Tam Dương Lạc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2462, 0.9738, -0.0424]` | FJ2810 (Skin of body) - Triangle #3... | 腕背橫紋上5寸，尺骨與橈骨之間（支溝穴上2寸）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE9** | TE | Sidu / 四渎 / Tứ Độc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2480, 1.0224, -0.0557]` | FJ2810 (Skin of body) - Triangle #3... | 肘尖下方5寸，尺骨與橈骨之間（三陽絡上1寸）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE10** | TE | Tianjing / 天井 / Thiên Tỉnh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2545, 1.1162, -0.0542]` | FJ2810 (Skin of body) - Triangle #3... | 手肘彎曲時，肘尖往上約一橫指寬的凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE11** | TE | Qinglengyuan / 清冷渊 / Thanh Lãnh Uyên | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2480, 1.1696, -0.0525]` | FJ2810 (Skin of body) - Triangle #3... | 肘尖（尺骨鷹嘴）上2寸，肱三頭肌外側。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE12** | TE | Xiaoluo / 消泺 / Tiêu Lạc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2372, 1.2692, -0.0620]` | FJ2810 (Skin of body) - Triangle #3... | 清冷淵上3寸，三角肌後下緣。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE13** | TE | Naohui / 臑会 / Nhu Hội | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.2301, 1.3388, -0.0718]` | FJ2810 (Skin of body) - Triangle #3... | 肩髎下3寸，三角肌後緣。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE14** | TE | Jianliao / 肩髎 / Kiên Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1937, 1.4140, -0.0694]` | FJ2810 (Skin of body) - Triangle #3... | 肩峰後下方，上臂外展時呈凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE15** | TE | Tianliao / 天髎 / Thiên Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1005, 1.4597, -0.0685]` | FJ2810 (Skin of body) - Triangle #2... | 肩井穴後約1寸，與大椎、肩峰連線中點。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE16** | TE | Tianyou / 天牖 / Thiên Dũ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0544, 1.5186, -0.0332]` | FJ2810 (Skin of body) - Triangle #2... | 乳突後下方，胸鎖乳突肌後緣，平下頷角。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE17** | TE | Yifeng / 翳风 / Ế Phong | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0628, 1.5729, -0.0129]` | FJ2810 (Skin of body) - Triangle #2... | 耳垂后方，按之酸胀并向耳深部放散处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE18** | TE | Chimai / 瘛脉 / 瘛 Mạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0678, 1.5876, -0.0173]` | FJ2810 (Skin of body) - Triangle #2... | 耳後乳突中央，翳風與角孫沿耳輪連線中點。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE19** | TE | Luxi / 颅息 / Lư Tức | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0710, 1.6046, -0.0143]` | FJ2810 (Skin of body) - Triangle #2... | 瘈脈上1寸，耳後青筋處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE20** | TE | Jiaosun / 角孙 / Giác Tôn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0704, 1.6258, 0.0036]` | FJ2810 (Skin of body) - Triangle #2... | 折耳，耳尖正上髮際凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE21** | TE | Ermen / 耳门 / Nhĩ Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0665, 1.5983, 0.0235]` | FJ2810 (Skin of body) - Triangle #2... | 耳屏上切跡前方，張口取之凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE22** | TE | Erheliao / 耳和髎 / Nhĩ Hòa Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0641, 1.6050, 0.0301]` | FJ2810 (Skin of body) - Triangle #2... | 耳屏前緣，與鬢髮交界處，張口時動脈搏動處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **TE23** | TE | Sizhukong / 丝竹空 / Ty Trúc Không | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0487, 1.6279, 0.0670]` | FJ2810 (Skin of body) - Triangle #2... | 眉毛外侧端凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB1** | GB | Tongziliao / 瞳子髎 / Đồng Tử Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0432, 1.6118, 0.0698]` | FJ2810 (Skin of body) - Triangle #2... | 外眼角外侧约半横指凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB2** | GB | Tinghui / 听会 / Thính Hội | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0663, 1.5828, 0.0256]` | FJ2810 (Skin of body) - Triangle #2... | 耳屏下方切迹前、张口出现的凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB3** | GB | Shangguan / 上关 / Thượng Quan | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0668, 1.6013, 0.0210]` | FJ2810 (Skin of body) - Triangle #2... | 下關穴直上1寸，顴弓上緣凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB4** | GB | Hanyan / 颔厌 / Hạm Yếm | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0633, 1.6289, 0.0312]` | FJ2810 (Skin of body) - Triangle #2... | 頭維與曲鬢弧形連線的上1/4處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB5** | GB | Xuanlu / 悬颅 / Huyền Lư | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0659, 1.6253, 0.0206]` | FJ2810 (Skin of body) - Triangle #2... | 頭維與曲鬢弧形連線的中點。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB6** | GB | Xuanli / 悬厘 / Huyền Ly | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0684, 1.6187, 0.0106]` | FJ2810 (Skin of body) - Triangle #2... | 頭維與曲鬢弧形連線的下1/4處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB7** | GB | Qubin / 曲鬓 / Khúc Mấn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0707, 1.6119, -0.0037]` | FJ2810 (Skin of body) - Triangle #2... | 耳尖水平前方，鬢髮內凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB8** | GB | Shuaigu / 率谷 / Suất Cốc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0742, 1.6458, -0.0083]` | FJ2810 (Skin of body) - Triangle #2... | 耳尖正上方约两横指、入发际处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB9** | GB | Tianchong / 天冲 / Thiên Xung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0783, 1.6378, -0.0345]` | FJ2810 (Skin of body) - Triangle #2... | 率谷穴後0.5寸，耳尖直上入髮際2寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB10** | GB | Fubai / 浮白 / Phù Bạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0753, 1.6184, -0.0563]` | FJ2810 (Skin of body) - Triangle #2... | 天衝穴直下約1寸，乳突後上方。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB11** | GB | Touqiaoyin / 头窍阴 / Đầu Khiếu Âm | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0675, 1.5937, -0.0676]` | FJ2810 (Skin of body) - Triangle #2... | 浮白穴下約1寸，乳突後緣。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB12** | GB | Wangu / 完骨 / Hoàn Cốt | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0565, 1.5709, -0.0623]` | FJ2810 (Skin of body) - Triangle #2... | 乳突後下方凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB13** | GB | Benshen / 本神 / Bản Thần | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0492, 1.6644, 0.0520]` | FJ2810 (Skin of body) - Triangle #2... | 神庭旁3寸，前髮際上0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB14** | GB | Yangbai / 阳白 / Dương Bạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0422, 1.6439, 0.0676]` | FJ2810 (Skin of body) - Triangle #2... | 正视前方，眉毛中点上方约一横指、瞳孔正上方。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB15** | GB | Toulinqi / 头临泣 / Đầu Lâm Khấp | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0448, 1.6776, 0.0478]` | FJ2810 (Skin of body) - Triangle #2... | 瞳孔直上，入前髮際0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB16** | GB | Muchuang / 目窗 / Mục Song | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0441, 1.6935, 0.0271]` | FJ2810 (Skin of body) - Triangle #2... | 頭臨泣後1寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB17** | GB | Zhengying / 正营 / Chính Dinh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0427, 1.7024, 0.0048]` | FJ2810 (Skin of body) - Triangle #2... | 目窗後1寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB18** | GB | Chengling / 承灵 / Thừa Linh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0425, 1.7060, -0.0257]` | FJ2810 (Skin of body) - Triangle #2... | 正營後1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB19** | GB | Naokong / 脑空 / Não Không | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0489, 1.6880, -0.0799]` | FJ2810 (Skin of body) - Triangle #2... | 後腦勺正中突起的骨頭（枕外隆凸）外側約三橫指，風池穴正上方。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB20** | GB | Fengchi / 风池 / Phong Trì | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0450, 1.5690, -0.0760]` | Suboccipital depression between SCM... | Bimastoid transverse width proportional ... | ±10.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **GB21** | GB | Jianjing / 肩井 / Kiên Tỉnh | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0725, 1.4580, -0.0580]` | Midpoint of line connecting C7 spin... | Bi-acromial shoulder width proportional ... | ±18.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **GB22** | GB | Yuanye / 渊腋 / Uyên Dịch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1585, 1.2515, 0.0208]` | FJ2810 (Skin of body) - Triangle #3... | 腋窩下3寸，第四肋間隙。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB23** | GB | Zhejin / 辄筋 / Triếp Cân | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1537, 1.2227, 0.0266]` | FJ2810 (Skin of body) - Triangle #3... | 淵腋前1寸，第四肋間。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB24** | GB | Riyue / 日月 / Nhật Nguyệt | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1249, 1.1891, 0.0854]` | FJ2810 (Skin of body) - Triangle #3... | 乳頭正下方，乳根再往下數兩個肋間隙（第七肋間）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB25** | GB | Jingmen / 京门 / Kinh Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1394, 1.0886, 0.0056]` | FJ2810 (Skin of body) - Triangle #3... | 側腰部，最後一根肋骨尖端下方。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB26** | GB | Daimai / 带脉 / Đới Mạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1441, 1.0210, 0.0312]` | FJ2810 (Skin of body) - Triangle #3... | 章門穴正下方，與肚臍同高的水平線上。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB27** | GB | Wushu / 五枢 / Ngũ Xu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1345, 0.9634, 0.0582]` | FJ2810 (Skin of body) - Triangle #3... | 側腹部，臍下3寸，前正中線旁開7寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB28** | GB | Weidao / 维道 / Duy Đạo | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1249, 0.9202, 0.0624]` | FJ2810 (Skin of body) - Triangle #3... | 五樞穴直下0.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB29** | GB | Juliao / 居髎 / Cư Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1298, 0.8774, -0.0910]` | FJ2810 (Skin of body) - Triangle #3... | 髂前上棘與股骨大轉子連線中點凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB30** | GB | Huantiao / 环跳 / Hoàn Khiêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1119, 0.7851, -0.0988]` | FJ2810 (Skin of body) - Triangle #3... | 侧卧屈髋屈膝，大转子与骶裂孔连线外1/3处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB31** | GB | Fengshi / 风市 / Phong Thị | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1118, 0.5646, -0.0654]` | FJ2810 (Skin of body) - Triangle #3... | 直立两手自然下垂，中指指尖触及大腿外侧处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB32** | GB | Zhongdu / 中渎 / Trung Độc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1107, 0.4988, -0.0619]` | FJ2810 (Skin of body) - Triangle #3... | 膝蓋外側上方5寸，股外側肌與髂脛束之間。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB33** | GB | Xiyangguan / 膝阳关 / Tất Dương Quan | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1127, 0.4534, -0.0717]` | FJ2810 (Skin of body) - Triangle #3... | 陽陵泉上3寸，膝外側橫紋端。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB34** | GB | Yanglingquan / 阳陵泉 / Dương Lăng Tuyền | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1339, 0.4170, -0.0260]` | FJ2810 (Skin of body) - Triangle #3... | 膝外下方，腓骨小头前下方凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB35** | GB | Yangjiao / 阳交 / Dương Giao | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1114, 0.2855, -0.0903]` | FJ2810 (Skin of body) - Triangle #3... | 外踝尖上7寸，腓骨前緣（外丘後約1寸）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB36** | GB | Waiqiu / 外丘 / Ngoại Khâu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1087, 0.2599, -0.0003]` | FJ2810 (Skin of body) - Triangle #3... | 外踝尖向上量一整手掌加三指寬度。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB37** | GB | Guangming / 光明 / Quang Minh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1053, 0.2302, -0.0036]` | FJ2810 (Skin of body) - Triangle #3... | 外踝尖向上量一整手掌寬度。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB38** | GB | Yangfu / 阳辅 / Dương Phụ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0951, 0.1878, -0.0033]` | FJ2810 (Skin of body) - Triangle #2... | 外踝尖向上量四橫指寬度。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB39** | GB | Xuanzhong / 悬钟 / Huyền Chung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0938, 0.1466, -0.0048]` | FJ2810 (Skin of body) - Triangle #2... | 外踝尖直上四横指，腓骨前缘。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB40** | GB | Qiuxu / 丘墟 / Khâu Khư | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0930, 0.0846, 0.0167]` | FJ2810 (Skin of body) - Triangle #3... | 外踝前下方的明显凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB41** | GB | Zulinqi / 足临泣 / Túc Lâm Khấp | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1168, 0.0603, 0.0446]` | FJ2810 (Skin of body) - Triangle #3... | 足背第4、5趾缝向上推至两骨结合前凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB42** | GB | Diwuhui / 地五会 / Địa Ngũ Hội | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1207, 0.0468, 0.0654]` | FJ2810 (Skin of body) - Triangle #3... | 足背第4、5蹠骨間，俠溪後1寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB43** | GB | Xiaxi / 侠溪 / Hiệp Khê | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1208, 0.0341, 0.0891]` | FJ2810 (Skin of body) - Triangle #3... | 足背第4、5趾缝纹头后方凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GB44** | GB | Zuqiaoyin / 足窍阴 / Túc Khiếu Âm | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1206, 0.0267, 0.1054]` | FJ2810 (Skin of body) - Triangle #3... | 腳第4趾甲外側角旁約一分處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR1** | LR | Dadun / 大敦 / Đại Đôn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0876, 0.0181, 0.1059]` | FJ2810 (Skin of body) - Triangle #2... | 大腳趾外側（靠近第二腳趾那側），指甲根角旁約0.1寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR2** | LR | Xingjian / 行间 / Hành Gian | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0890, 0.0487, 0.0733]` | FJ2810 (Skin of body) - Triangle #2... | 足背第1、2趾缝纹头后方赤白肉际。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR3** | LR | Taichong / 太冲 / Thái Xung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0970, 0.0667, 0.0470]` | FJ2810 (Skin of body) - Triangle #2... | 足背第1、2趾缝向上推，至两骨结合前凹陷、可触及动脉处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR4** | LR | Zhongfeng / 中封 / Trung Phong | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0635, 0.0838, 0.0176]` | FJ2810 (Skin of body) - Triangle #2... | 腳踝內側骨頭前方，按壓有凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR5** | LR | Ligou / 蠡沟 / Lễ Câu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0494, 0.1933, -0.0179]` | FJ2810 (Skin of body) - Triangle #2... | 內踝尖向上量一整手掌寬度。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR6** | LR | Zhongdu / 中都 / Trung Đô | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0573, 0.2293, -0.0047]` | FJ2810 (Skin of body) - Triangle #2... | 內踝尖往上量一整手掌加三指寬度。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR7** | LR | Xiguan / 膝关 / Tất Quan | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0481, 0.4077, 0.0045]` | FJ2810 (Skin of body) - Triangle #2... | 犢鼻穴下2寸，脛骨內側髁後下方凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR8** | LR | Ququan / 曲泉 / Khúc Tuyền | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0448, 0.4456, 0.0118]` | FJ2810 (Skin of body) - Triangle #2... | 屈膝，膝内侧横纹头上方，可摸到的筋的内侧凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR9** | LR | Yinbao / 阴包 / Âm Bao | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0626, 0.5619, 0.0530]` | FJ2810 (Skin of body) - Triangle #2... | 膝蓋內側上方4寸，大腿內側兩筋之間。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR10** | LR | Zuwuli / 足五里 / Túc Ngũ Lý | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0605, 0.6588, 0.0609]` | FJ2810 (Skin of body) - Triangle #2... | 氣衝穴直下3寸，大腿內側根部。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR11** | LR | Yinlian / 阴廉 / Âm Liêm | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0570, 0.7360, 0.0573]` | FJ2810 (Skin of body) - Triangle #4... | 氣衝穴外下方2寸，股動脈搏動處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR12** | LR | Jimai / 急脉 / Cấp Mạch | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0529, 0.8482, 0.0573]` | FJ2810 (Skin of body) - Triangle #4... | 恥骨聯合上緣旁開2.5寸，腹股溝動脈搏動處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR13** | LR | Zhangmen / 章门 / Chương Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.1393, 1.0594, 0.0179]` | FJ2810 (Skin of body) - Triangle #3... | 侧腹部，屈肘合腋时肘尖所到处、第11肋骨端下方。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **LR14** | LR | Qimen / 期门 / Kỳ Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0960, 1.1891, 0.1077]` | FJ2810 (Skin of body) - Triangle #2... | 乳头直下，第6肋间隙处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV1** | GV | Changqiang / 长强 / Trường Cường | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 0.8390, -0.0888]` | FJ2810 (Skin of body) - Triangle #2... | 尾骨最尖端與肛門之間凹陷的中點。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV2** | GV | Yaoshu / 腰俞 / Yêu Du | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 0.8966, -0.1279]` | FJ2810 (Skin of body) - Triangle #2... | 尾骨端上方，骶骨下端凹陷處（正對骶管裂孔）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV3** | GV | Yaoyangguan / 腰阳关 / Yêu Dương Quan | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 0.9637, -0.1149]` | FJ2810 (Skin of body) - Triangle #2... | 两侧髂嵴最高点连线平第4腰椎，棘突下凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV4** | GV | Mingmen / 命门 / Mệnh Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.0212, -0.0979]` | FJ2810 (Skin of body) - Triangle #2... | 与肚脐相对的腰椎（第2腰椎）棘突下凹陷，与两侧肾俞平齐。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV5** | GV | Xuanshu / 悬枢 / Huyền Xu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.0596, -0.0958]` | FJ2810 (Skin of body) - Triangle #2... | 命門（第2腰椎）上一椎體（第1腰椎）下方凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV6** | GV | Jizhong / 脊中 / Tích Trung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.1172, -0.0986]` | FJ2810 (Skin of body) - Triangle #2... | 兩肩胛骨下角連線（第7胸椎）向下推4個椎體，即第11胸椎下方凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV7** | GV | Zhongshu / 中枢 / Trung Xu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.1557, -0.0987]` | FJ2810 (Skin of body) - Triangle #2... | 脊中（第11胸椎）上一椎體（第10胸椎）下方凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV8** | GV | Jinsuo / 筋缩 / Cân Súc | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.1943, -0.1028]` | FJ2810 (Skin of body) - Triangle #2... | 中樞（第10胸椎）上一椎體（第9胸椎）下方凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV9** | GV | Zhiyang / 至阳 / Chí Dương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.2521, -0.1142]` | FJ2810 (Skin of body) - Triangle #2... | 兩肩胛骨下角連線中點（第7胸椎）下方凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV10** | GV | Lingtai / 灵台 / Linh Đài | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.2858, -0.1186]` | FJ2810 (Skin of body) - Triangle #2... | 至陽（第7胸椎）上一椎體（第6胸椎）下方凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV11** | GV | Shendao / 神道 / Thần Đạo | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.3195, -0.1197]` | FJ2810 (Skin of body) - Triangle #2... | 兩肩胛骨下角連線（第7胸椎）向上推2個椎體（第5胸椎）下方凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV12** | GV | Shenzhu / 身柱 / Thân Trụ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.3580, -0.1167]` | FJ2810 (Skin of body) - Triangle #2... | 兩側肩胛岡內側端連線（約第3胸椎）正中下方凹陷。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV13** | GV | Taodao / 陶道 / Đào Đạo | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.4018, -0.1177]` | FJ2810 (Skin of body) - Triangle #2... | 大椎（第7頸椎）下方凹陷（即第1胸椎棘突下）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV14** | GV | Dazhui / 大椎 / Đại Chùy | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0000, 1.4465, -0.0850]` | Depression inferior to spinous proc... | Posterior midline primary origin | ±8.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **GV15** | GV | Yamen / 哑门 / Á Môn | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0000, 1.5200, -0.0780]` | Posterior midline, superior to C2 s... | Posterior cervical hairline division | ±8.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **GV16** | GV | Fengfu / 风府 / Phong Phủ | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0000, 1.5750, -0.0820]` | External occipital protuberance dep... | Cranial base bony anchor | ±8.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **GV17** | GV | Naohu / 脑户 / Não Hộ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.5950, -0.1160]` | FJ2810 (Skin of body) - Triangle #2... | 風府直上1.5寸，枕骨粗隆上緣。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV18** | GV | Qiangjian / 强间 / Cường Gian | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.6559, -0.1193]` | FJ2810 (Skin of body) - Triangle #2... | 百會後3寸（或腦戶上1.5寸）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV19** | GV | Houding / 后顶 / Hậu Đỉnh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.7111, -0.0686]` | FJ2810 (Skin of body) - Triangle #2... | 百會穴直後1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV20** | GV | Baihui / 百会 / Bách Hội | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.7188, -0.0047]` | FJ2810 (Skin of body) - Triangle #2... | 两耳尖向上连线与头顶正中线交点。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV21** | GV | Qianding / 前顶 / Tiền Đỉnh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.7072, 0.0379]` | FJ2810 (Skin of body) - Triangle #2... | 百會穴直前1.5寸。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV22** | GV | Xinhui / 囟会 / Tín Hội | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.6876, 0.0609]` | FJ2810 (Skin of body) - Triangle #2... | 前髮際正中直上2寸（約拇指與食指併攏之寬度）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV23** | GV | Shangxing / 上星 / Thượng Tinh | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.6679, 0.0736]` | FJ2810 (Skin of body) - Triangle #2... | 前发际正中向上约一横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV24** | GV | Shenting / 神庭 / Thần Đình | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.6484, 0.0806]` | FJ2810 (Skin of body) - Triangle #2... | 前发际正中往上约半横指处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV24+** | GV | Yintang / 印堂 / 印 Đường | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.6150, 0.0823]` | FJ2810 (Skin of body) - Triangle #2... | Standard B-Cun | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV25** | GV | Suliao / 素髎 / Tố Liêu | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.5814, 0.0987]` | FJ2810 (Skin of body) - Triangle #2... | 鼻尖正中央。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV26** | GV | Shuigou / 水沟 / Thủy Câu (Nhân Trung) | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.5571, 0.0963]` | FJ2810 (Skin of body) - Triangle #2... | 鼻唇之间人中沟上1/3处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV27** | GV | Duiduan / 兑端 / Đoái Đoan | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.5439, 0.0912]` | FJ2810 (Skin of body) - Triangle #2... | 上唇正中，皮膚與黏膜交界處（唇珠上方）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **GV28** | GV | Yinjiao / 龈交 / Ngân Giao | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.5171, 0.1107]` | Unverified against BodyParts3D post... | 翻開上唇，上唇繫帶與上牙齦交界處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV1** | CV | Huiyin / 会阴 / Hội Âm | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 0.8338, 0.0341]` | FJ2810 (Skin of body) - Triangle #4... | 會陰部正中。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV2** | CV | Qugu / 曲骨 / Khúc Cốt | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 0.8866, 0.0577]` | FJ2810 (Skin of body) - Triangle #4... | 下腹部正中，向下摸到耻骨硬缘的上方。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV3** | CV | Zhongji / 中极 / Trung Cực | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 0.9202, 0.0707]` | FJ2810 (Skin of body) - Triangle #4... | 脐下五横指、耻骨联合上方约一横指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV4** | CV | Guanyuan / 关元 / Quan Nguyên | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 0.9490, 0.0814]` | FJ2810 (Skin of body) - Triangle #4... | 脐下四横指，前正中线上。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV5** | CV | Shimen / 石门 / Thạch Môn | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 0.9681, 0.0887]` | FJ2810 (Skin of body) - Triangle #4... | 肚臍正下方三橫指寬處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV6** | CV | Qihai / 气海 / Khí Hải | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 0.9873, 0.0964]` | FJ2810 (Skin of body) - Triangle #2... | 脐下约两横指，前正中线上。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV7** | CV | Yinjiao / 阴交 / Âm Giao | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.0066, 0.1032]` | FJ2810 (Skin of body) - Triangle #2... | 肚臍正下方約一橫指（拇指）寬度。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV8** | CV | Shenque / 神阙 / Thần Khuyết | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.0258, 0.1008]` | FJ2810 (Skin of body) - Triangle #2... | 肚脐正中。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV9** | CV | Shuifen / 水分 / Thủy Phân | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.0498, 0.1011]` | FJ2810 (Skin of body) - Triangle #2... | 肚臍正上方約一拇指橫寬（約1寸）處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV10** | CV | Xiawan / 下脘 / Hạ Quản | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.0739, 0.1076]` | FJ2810 (Skin of body) - Triangle #2... | 肚臍正上方約三橫指（食、中、無名指併攏）寬度。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV11** | CV | Jianli / 建里 / Kiến Lý | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.0980, 0.1116]` | FJ2810 (Skin of body) - Triangle #2... | 肚臍正上方約四橫指（併攏）寬度。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV12** | CV | Zhongwan / 中脘 / Trung Quản | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.1220, 0.1143]` | FJ2810 (Skin of body) - Triangle #2... | 胸骨下端与肚脐连线中点。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV13** | CV | Shangwan / 上脘 / Thượng Quản | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.1460, 0.1157]` | FJ2810 (Skin of body) - Triangle #2... | 肚臍往上量約7橫指。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV14** | CV | Juque / 巨阙 / Cự Khuyết | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.1700, 0.1160]` | FJ2810 (Skin of body) - Triangle #2... | 肚臍往上量約8橫指（或從胸骨下方凹陷處與肚臍連線中點再往上）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV15** | CV | Jiuwei / 鸠尾 / Cưu Vĩ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.1940, 0.1164]` | FJ2810 (Skin of body) - Triangle #2... | 胸骨下端（劍突）下方凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV16** | CV | Zhongting / 中庭 / Trung Đình | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.2275, 0.1145]` | FJ2810 (Skin of body) - Triangle #2... | 膻中穴直下1.6寸，胸骨體下端與劍突連接處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV17** | CV | Danzhong / 膻中 / Đản Trung (Chiên Trung) | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.2515, 0.1120]` | FJ2810 (Skin of body) - Triangle #2... | 两乳头连线中点，胸骨正中。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV18** | CV | Yutang / 玉堂 / Ngọc Đường | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.2803, 0.1124]` | FJ2810 (Skin of body) - Triangle #2... | 膻中（平第4肋）上一肋（第3肋）水平。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV19** | CV | Zigong / 紫宫 / Tử Cung | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.3091, 0.1068]` | FJ2810 (Skin of body) - Triangle #2... | 玉堂（第3肋）上一肋（第2肋）水平。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV20** | CV | Huagai / 华盖 / Hoa Cái | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.3379, 0.0926]` | FJ2810 (Skin of body) - Triangle #2... | 紫宮（第2肋）上一肋（第1肋）水平。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV21** | CV | Xuanji / 璇玑 / Tuyền Cơ | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.3667, 0.0816]` | FJ2810 (Skin of body) - Triangle #2... | 天突（胸骨上窩）直下1寸（約胸骨柄中央）。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV22** | CV | Tiantu / 天突 / Thiên Đột | **CLASS_A** | `LANDMARK_DEFINED` | `[0.0000, 1.4380, 0.0450]` | Center of suprasternal fossa / jugu... | Sternal segment superior boundary | ±6.0 mm | `VERIFIED_ANATOMICAL_ANCHOR` |
| **CV23** | CV | Lianquan / 廉泉 / Liêm Tuyền | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.5137, 0.0832]` | FJ2810 (Skin of body) - Triangle #2... | 下颌与喉结之间、舌骨上方的凹陷处。 | ±15.0 mm | `PRE_BAKED_LEGACY` |
| **CV24** | CV | Chengjiang / 承浆 / Thừa Tương | **CLASS_D** | `SURFACE_RAYCAST_UNCALIBRATED` | `[0.0000, 1.5525, 0.0920]` | FJ2810 (Skin of body) - Triangle #2... | 下唇正中，下唇溝凹陷處。 | ±15.0 mm | `PRE_BAKED_LEGACY` |

---

*End of 361 Acupoint Data Quality Matrix.*
