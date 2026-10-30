# P14-B: BIOMECHANICAL & SCIENTIFIC CLAIM CORRECTIONS
## Musculoskeletal Therapy OS (MSK-Therapy-OS) — Milestone P14
### Elimination of Dogmatic Rules · Scapulohumeral Variability · Evidence-Grounded Scientific Restatement

- **Milestone:** P14 (Phase P14-B: Scientific Restatement)
- **Document ID:** `1docs/audits/P14/P14_SCIENTIFIC_CLAIM_CORRECTIONS.md`
- **Audit Date:** 2026-10-30
- **Auditor:** Musculoskeletal Biomechanics Engineer & Scientific Content Reviewer
- **Status:** APPROVED & MANDATED FOR CODEBASE INTEGRATION

---

## 1. CRITICAL CORRECTION 1: SCAPULOHUMERAL RHYTHM VARIABILITY

### P13 Defect:
Milestone P13 presented the historical 2:1 scapulohumeral rhythm as a universal physiological constant, automatically classifying ratios $> 2.4:1$ as "Scapular Dyskinesia" and $< 1.6:1$ as "Compensatory Shrug".

### Scientific Reality & Correction:
1. **Phase-Dependent Non-Linearity:** Inman et al. (1944) reported an *overall average* of 2:1 across full arm elevation. However, 3D kinematic studies (Ludewig & Cook 2000, McClure et al. 2001, Sugamoto et al. 2002) demonstrate that the ratio changes significantly throughout movement:
   - *Setting Phase ($0^\circ - 30^\circ$):* Scapular upward rotation is minimal and highly variable among healthy subjects; motion is primarily glenohumeral.
   - *Mid-Range ($30^\circ - 90^\circ$):* Scapulothoracic motion increases, often exhibiting ratios of $2.2:1$ to $2.7:1$.
   - *Terminal Elevation ($90^\circ - 180^\circ$):* Scapular upward rotation accelerates to maintain subacromial clearance.
2. **Impact of External Load & Plane:** External load (e.g. lifting a 2 kg hand weight) increases early scapular upward rotation (decreasing the ratio) to optimize deltoid length-tension relationships (Pascoal et al. 2000). Ratios also differ between the scapular plane (scaption), sagittal plane (flexion), and frontal plane (abduction).
3. **Measurement Definition Distinctions:**
   - *Glenohumeral-to-Scapulothoracic Ratio:* $\theta_{\text{GH}} / \theta_{\text{ST}}$ (e.g. $120^\circ / 60^\circ = 2.0$).
   - *Humerothoracic-to-Scapulothoracic Ratio:* $\theta_{\text{HT}} / \theta_{\text{ST}}$ (e.g. $180^\circ / 60^\circ = 3.0$).
4. **Mandated Code & UI Action:**
   - Remove automatic diagnostic classifications ("Normal" vs "Dyskinesia").
   - When a 2:1 ratio is displayed, permanently label it:
     ```text
     IDEALIZED EDUCATIONAL EXAMPLE — NOT A UNIVERSAL NORMAL RANGE
     ```
   - Provide explicit disclaimers regarding kinematic variability across healthy populations.

---

## 2. CRITICAL CORRECTION 2: MUSCLE BEHAVIOR IN ROUNDED SHOULDER POSTURE

### P13 Defect:
P13 asserted that a rounded-shoulder posture *proves* pectoralis minor shortening, lower trapezius inhibition, and serratus anterior weakness.

### Scientific Reality & Correction:
1. **Asymptomatic Postural Prevalence:** Epidemiological investigations demonstrate that forward head and rounded shoulder postures are widely prevalent in healthy, asymptomatic populations with zero shoulder pain, normal rotator cuff function, and normal electromyographic (EMG) recruitment.
2. **Absence of Strict Causality:** While Kendall (2005) and Janda described "Upper Crossed Syndrome" as a clinical model, observational studies fail to demonstrate a consistent 1-to-1 correlation between resting posture and dynamic muscle weakness.
3. **Mandated Code & UI Action:**
   - Reframe muscle shortening and reciprocal inhibition as **hypotheses and potential contributing factors**, not definitive diagnostic facts.
   - State clearly: *"Posture variation does not inherently indicate tissue pathology or muscular weakness."*

---

## 3. CRITICAL CORRECTION 3: MECHANISMS OF MANUAL SOFT-TISSUE SYMPTOM RELIEF

### P13 Defect:
P13 claimed that manual massage "resets mechanoreceptors and reverses motor control faults."

### Scientific Reality & Correction:
1. **Sensory & Perceptual Modulation:** Manual therapy, myofascial release, and massage stimulate low-threshold cutaneous and subcutaneous mechanoreceptors (Ruffini, Pacinian, interstitial type III/IV), modulating central pain perception and transiently reducing muscle spindle gain.
2. **Transient vs. Structural Effects:** This neurosensory modulation produces an immediate subjective sensation of lightness and ease of movement, but does **not** mechanically elongate collagenous fascial sheets or reprogram automated motor schemas. Long-term functional adaptation requires active exercise, progressive loading, and habitual ergonomic modifications.
3. **Mandated Code & UI Action:**
   - Accurately distinguish short-term sensory relief from lasting neuromuscular and structural adaptation.
   - Avoid unsubstantiated claims regarding permanent neurological reprogramming from passive manual modalities.

---

## 4. CRITICAL CORRECTION 4: RECLASSIFICATION OF POSTURE SLIDER

### P13 Defect:
The 0–100% slider appeared as an objective biometric measurement of "postural severity".

### Scientific Reality & Correction:
1. A 2D slider is a synthetic teaching simulation tool, not an instrumented clinical posture analysis.
2. **Mandated Code & UI Action:**
   - Rename and reclassify the control to:
     ```text
     ILLUSTRATIVE POSTURE SCENARIO SIMULATOR (NOT A DIAGNOSTIC MEASUREMENT)
     ```
   - Embed clear disclaimers that slider values are arbitrary educational scenario indices.

---

## 5. AUDIT VERDICT

All scientific restatements are approved and must be reflected across [`msk_therapy_os/biomechanics_adapter.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/biomechanics_adapter.py), [`msk_therapy_os/static/education/shoulder_lab.js`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/static/education/shoulder_lab.js), and the studio HTML.
