# MSK-Therapy-OS — Milestone P23 Audit
## P23_02: Upper Limb Armature Rig, Kinematic Mapping & Joint Constraints

**Tài liệu ID:** `MSK-P23-AUD-002`  
**Ngày thực hiện:** 2026-11-03  
**Phân loại:** `ENGINEERING_RESEARCH_ONLY`  

---

### 1. Phân cấp Cấu trúc Khung Xương (Armature Hierarchy)

Armature cánh tay phải (`Armature_UpperLimb_R`) được dựng theo giải phẫu sinh học chuẩn:

```text
clavicle.R (Xương đòn: 0.02, 0.0, 1.42 -> 0.18, 0.0, 1.42)
  └── upper_arm.R (Xương cánh tay / Humerus: length = 0.30m)
        └── forearm.R (Xương cẳng tay / Ulna-Radius: length = 0.26m) [use_connect=True]
              └── hand.R (Bàn tay: length = 0.16m) [use_connect=True]

[Non-Deforming Controls]
├── wrist_IK.R   # Xương đích IK tại khớp cổ tay
└── elbow_pole.R # Xương định hướng mặt phẳng khuỷu tay
```

---

### 2. Thiết lập Ràng buộc IK và Ranh giới Cơ sinh học (Joint Constraints)

#### A. Ràng buộc Động học Nghịch đảo (IK Constraint)
- Gán trên pose bone `forearm.R`.
- **Target:** `Armature_UpperLimb_R`, Subtarget: `wrist_IK.R`.
- **Chain Length:** 2 (tác động lên `forearm.R` và `upper_arm.R`).
- **Pole Target:** `elbow_pole.R`, Pole Angle: $0.0^\circ$.

#### B. Khóa Giới hạn Xoay Khớp Khuỷu (Kapandji 2007 Limit Rotation)
Khớp cánh tay - cẳng tay (humeroulnar joint) hoạt động theo cơ chế bản lề một trục:
- **Trục uốn/gập ($X$):** $[0.0^\circ, 145.0^\circ]$ (Gập tối đa $145^\circ$, duỗi thẳng tối đa $0^\circ$).
- **Trục ngang ($Y$) và trục dọc ($Z$):** Cố định $[0^\circ, 0^\circ]$ trong chế độ bản lề thuần túy.
- **Dẫn chiếu khoa học:** *Kapandji IA. The Physiology of the Joints, Vol 1 (Upper Limb), 6th ed., Churchill Livingstone, 2007.*
- **Trạng thái thẩm định:** `EXPERT_REVIEW_PENDING`.
