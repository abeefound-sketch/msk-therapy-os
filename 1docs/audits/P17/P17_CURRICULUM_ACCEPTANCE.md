# P17 Unified Musculoskeletal Curriculum Acceptance Audit

## 1. Compliance Standard

Under Acceptance Principle P17-05:
- The 10-topic unified curriculum must provide complete bilingual (EN/VI) pedagogical progression.
- Clicking any module updates stage content and navigates 3D visual focus to relevant structures.
- Explains the core educational paradox: why manual soft-tissue release produces transient symptom reduction but posture frequently returns without progressive active exercise and ergonomic intervention.

---

## 2. Ten Curriculum Topics Verification

| Stage ID | Topic Name (EN) | Tên Chuyên Đề (VI) | Focus Muscles | 3D Camera / Scene Focus | Functional Verification |
|---|---|---|---|---|---|
| 1 | Anatomy: Architecture | Cấu trúc Đầu, Cổ & Đai Vai | Upper Trap, Levator, Suboccipital, Anterior Deltoid | Anterior Torso & Cervical Spine | Verified |
| 2 | Joint Motion: Kinematics | Cơ học Vận động Bả vai & Cổ | Serratus Anterior, Lower Trap, SCM, Splenius | Scapular Posterior / Lateral | Verified |
| 3 | Alignment: Forward-Head | Tư thế Đầu đổ trước & Đa dạng | Suboccipital, Longus Colli, Pectoralis Minor | Cervicothoracic Sagittal Profile | Verified |
| 4 | Physics: Gravity & Lever Arms | Vật lý: Trọng lực, Cánh tay đòn | Extensor Group, Trapezius | C7-T1 Sagittal Lever Arm | Verified |
| 5 | Muscle Mechanics: Coordination | Phối hợp Cơ & Cân bằng đối vận | Deltoid, Supraspinatus, Serratus, Trapezius | Upper Crossed Muscle Map | Verified |
| 6 | Transient Relief vs Adaptation | Nghịch lý: Nhẹ cơ tức thời vs Tái phát | Ruffini Mechanoreceptors, Fascia | Whole Girdle Architecture | Verified |
| 7 | Active Progressions | Tập luyện Chủ động & Thần kinh cơ | Deep Neck Flexors, Lower Trapezius | Posture Alignment Simulation | Verified |
| 8 | Ergonomics & Workstation | Công thái học & Thói quen vận động | Ergonomic Postural Chain | Neutral Reference Pose | Verified |
| 9 | Red Flags & Triage | Cảnh báo Đỏ & Tầm soát an toàn | None (Medical Triage Card) | Non-Diagnostic Safety Card | Verified |
| 10 | Clinical Study Readiness | Sẵn sàng Nghiên cứu Lâm sàng | Governance Registry | G14 Invariant Disclaimer | Verified |

---

## 3. Interactive Curriculum Behavior

- **Navigation**: Clicking `.stage-nav-item` updates `this.currentStageId`, highlights the nav item with `.active` border, and renders module title and summary text without page reload.
- **3D Highlighting**: Automatically passes `stage.focus_muscles` to `this.viewer.highlightMuscles()`.
- **Region Adaptation**: If `stage.region` specifies a different focus (e.g. Cervical for Stage 3, Shoulder for Stage 2), camera smoothly re-centers on that anatomical region.
- **Evidence Screenshot**: `1docs/audits/P17/screenshots/09_curriculum_module_switching.png`. Verified in `tests/test_p17_functional_acceptance_playwright.py` Step 9.
