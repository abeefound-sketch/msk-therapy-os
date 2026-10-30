# P14 Shoulder Lesson & Interactive Quiz Acceptance Audit

**Milestone:** P14 — Evidence-Grounded Dynamic Biomechanics, Muscle Recruitment Visualization & Interactive MSK Education  
**Date:** October 31, 2026  
**Auditor / Content Lead:** Scientific Content Reviewer & Education UX Auditor  
**Status:** VALIDATED  

---

## 1. Executive Summary

This document verifies the pedagogical integrity, curriculum completeness, and interactive assessment features delivered in Phase P14-G of the MSK-Therapy-OS Shoulder Education Studio.

The application addresses the fundamental educational inquiry:
> *"What happens to the scapula, humerus, clavicle and surrounding muscles when a person raises an arm, and why might forward shoulder posture or discomfort return after temporary symptom relief?"*  
> (*"Điều gì xảy ra với xương bả vai, cánh tay, xương đòn và các cơ khi giơ tay, và vì sao cảm giác nhẹ nhõm sau giải cơ thường chỉ duy trì tạm thời rồi vai lại đổ trước như cũ?"*)

---

## 2. 8-Stage Interactive Curriculum Structure

The lesson is structured into eight progressive modules available in both English and Vietnamese:

| Stage | Title (EN) | Title (VI) | Pedagogical Objective | Focus Muscles |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Explore:** Skeletal Architecture & Muscle Girdle | **Khám phá:** Khung xương bả vai & Hệ thống cơ | Identify Thorax, Clavicle, Scapula, Humerus; understand shoulder as 4-joint system. | Deltoid, Trapezius, Serratus, Pec Minor |
| **2** | **Observe:** Illustrative Forward Posture & Neutral | **Quan sát:** Hình thái vai đổ trước & Vị trí trung tính | Distinguish resting visual posture from clinical pathology or muscle weakness. | Pectoralis Minor, Pectoralis Major |
| **3** | **Move:** Dynamic Arm Elevation & Joint Kinematics | **Chuyển động:** Nâng tay & Cơ sinh học các khớp | Observe real-time 3D clavicular elevation, scapular upward rotation, posterior tilt. | Deltoid Lateral, Serratus, Lower Trap |
| **4** | **Understand:** Muscle Involvement vs. Measured Activation | **Thấu hiểu:** Vai trò giải phẫu vs. Kích hoạt mô phỏng | Differentiate anatomical participation from OpenSim static optimization estimates. | Deltoid, Supraspinatus, Serratus |
| **5** | **Compare:** Unloaded Movement vs. Forward Shoulder Alignment | **So sánh:** Vận động tự do vs. Kịch bản tư thế vai đổ trước | Compare standard OpenSim kinematics with illustrative forward posture scenarios. | Pectoralis Minor, Upper Trapezius |
| **6** | **Self-Care:** Evidence-Informed Active Re-Education | **Tự chăm sóc:** Giáo dục vận động chủ động dựa trên bằng chứng | Explain why active progressive loading and workplace ergonomics drive lasting adaptation. | Serratus Anterior, Lower Trapezius |
| **7** | **Quiz:** Test Your Biomechanical Understanding | **Trắc nghiệm:** Kiểm tra hiểu biết cơ sinh học | Evaluate user comprehension with 4 evidence-grounded questions and feedback. | Interactive Quiz Engine |
| **8** | **Evidence:** Peer-Reviewed Scientific Register | **Y văn:** Danh mục nghiên cứu khoa học phản biện | Inspect peer-reviewed citations EV-01 through EV-08 with study design and takeaways. | Peer-Reviewed Register |

---

## 3. Interactive Quiz Assessment & Validation

Stage 7 features an interactive comprehension widget with instant validation:

### Question 1: Scapulohumeral Rhythm Universality
- **Prompt:** *Is the 2:1 scapulohumeral rhythm an invariant biological law that applies identically to every person?*
- **Options:**
  - A. Yes, all healthy shoulders strictly elevate at exactly 2:1.
  - B. **(Correct)** No, it is an idealized historical average. Scapular motion varies dynamically with elevation phase, external loads, and movement planes.
  - C. Yes, any ratio above 2.1 is always a clinical disease called dyskinesia.
- **Scientific Rationale:** Inman (1944) described an overall average, but contemporary 3D kinematics (Ludewig 2000, Sugamoto 2002) demonstrate non-linear phase variability and wide asymptomatic variation.

### Question 2: Visual Posture Inspection vs. Muscle Weakness
- **Prompt:** *Can visual posture inspection alone definitively prove that a specific muscle is weak or short?*
- **Options:**
  - A. Yes, rounded shoulders always mean the pectoralis minor is physically short and the lower trapezius is weak.
  - B. **(Correct)** No, posture reflects resting alignment. Muscle activation and strength require dynamic testing and clinical evaluation.
  - C. Yes, posture is directly proportional to EMG electrical activity.
- **Scientific Rationale:** Asymptomatic individuals frequently display forward shoulder postures with normal muscular strength and zero pain. Postural appearance alone is not a medical diagnosis.

### Question 3: OpenSim Static Optimization vs. Measured EMG
- **Prompt:** *Does muscle activation calculated by OpenSim represent directly measured human EMG data?*
- **Options:**
  - A. Yes, OpenSim records actual electrical signals through surface electrodes.
  - B. **(Correct)** No, OpenSim muscle activations are mathematical estimates derived from optimization algorithms, not measured bioelectrical signals.
  - C. Yes, simulation and human measurement are identical.
- **Scientific Rationale:** OpenSim solves static optimization to predict recruitment based on mathematical objective functions; it is a computational model estimate, not an empirical bioelectrical recording.

### Question 4: Transient Massage Relief vs. Lasting Structural Change
- **Prompt:** *Why does forward shoulder posture or stiffness often return days after feeling light from a massage?*
- **Options:**
  - A. Because the therapist did not use enough pressure.
  - B. **(Correct)** Because manual therapy provides transient neurosensory relief, but lasting change requires active exercise, progressive strengthening, and ergonomic habituation.
  - C. Because massage permanently shortens the posterior muscles.
- **Scientific Rationale:** Manual manipulation stimulates mechanoreceptors to reduce local tone transiently (Schleip 2003). Long-term remodeling and motor repatterning require active neuromuscular recruitment and progressive loading.

---

## 4. Bilingual Verification

All 8 lesson stages, 4 quiz questions, 12 answer options, and 4 detailed scientific explanations have been verified in both English and Vietnamese. Toggling between languages updates the DOM immediately without page reload or state loss.
