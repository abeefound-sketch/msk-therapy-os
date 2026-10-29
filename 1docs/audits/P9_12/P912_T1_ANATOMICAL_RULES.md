# P9.12 Tranche 1 Anatomical Localization Rules Specification

**Milestone:** P9.12 Tranche 1: Anatomical Remediation: Proximal Extremities & Limb Girdles  
**Auditor:** Principal Computational Anatomy Engineer & Medical 3D Registration Specialist  
**Date:** 2026-10-28  
**Repository State:** `feat/p9.4-definitive-meridian-atlas-correction`  
**Standard Authority:** World Health Organization (WHO) Standard Acupuncture Point Locations (2008) & BodyParts3D FJ2810  

---

## 1. Mathematical Framework & Proportional Scaling

The 48 acupoints remediated in Tranche 1 are located in complex proximal extremity regions and limb girdles: the upper arm, shoulder girdle, axilla, elbow, anterior/medial/lateral/posterior thigh, knee, groin, pelvic girdle, and posterior calf.

Each point's spatial position is computed deterministically via parametric B-cun proportional interpolation between audited BodyParts3D canonical skeletal landmarks:

$$\mathbf{P}_{\text{chord}}(t) = (1 - t) \cdot \mathbf{L}_{\text{start}} + t \cdot \mathbf{L}_{\text{end}}$$

$$\mathbf{P}_{\text{calibrated}} = \mathbf{P}_{\text{chord}}(t) + \Delta_{\text{lateral}} \cdot \hat{\mathbf{n}}_{\text{lat}}$$

Where:
- $\mathbf{L}_{\text{start}}, \mathbf{L}_{\text{end}}$ are verified non-quarantined BodyParts3D skeletal anchors.
- $t \in [0.0, 1.0]$ is the standardized B-cun fractional ratio defined in the WHO 2008 Standard.
- $\Delta_{\text{lateral}}$ is the transverse muscular/fascial offset scaled by regional B-cun metric ratios.
- $\hat{\mathbf{n}}_{\text{lat}}$ is the outward normal vector orthogonal to the longitudinal bone axis.
- Left/Right laterality is enforced via bilateral sagittal reflection: $X_{\text{Left}} = -X_{\text{Right}}$, $Y_{\text{Left}} = Y_{\text{Right}}$, $Z_{\text{Left}} = Z_{\text{Right}}$.

---

## 2. Comprehensive Group Rule Specifications

### 2.1 Stomach Channel (ST) — Anterior Thigh & Knee (4 Points)
1. **`ST31` (Biguan, 髀关):**
   - **WHO 2008 Standard (p. 74):** Anterior thigh, directly inferior to the anterior superior iliac spine (ASIS), in the depression lateral to the sartorius muscle, level with the pubic symphysis.
   - **Mathematical Anchor:** `LM_ASIS_R` $(0.132, 0.942, 0.075)$ to `LM_PATELLA_INFERIOR_R` $(0.115, 0.468, 0.082)$.
   - **Fraction:** $t = 0.1500$. Level with pubic symphysis ($Y \approx 0.871\text{ m}$).
   - **FMA Concept:** `FMA:22312` (Anterior thigh / Sartorius lateral groove).
2. **`ST32` (Futu, 伏兔):**
   - **WHO 2008 Standard (p. 75):** Anterior thigh, on line connecting ASIS and lateral border of patella, 6 B-cun superior to base of patella.
   - **Mathematical Anchor:** `LM_ASIS_R` to `LM_PATELLA_INFERIOR_R`.
   - **Fraction:** $t = 12 / 18 = 0.6667$. Rectus femoris belly ($Y \approx 0.626\text{ m}$).
   - **FMA Concept:** `FMA:22312` (Rectus femoris muscle belly).
3. **`ST33` (Yinshi, 阴市):**
   - **WHO 2008 Standard (p. 75):** Anterior thigh, on line connecting ASIS and lateral patellar border, 3 B-cun superior to base of patella.
   - **Mathematical Anchor:** `LM_ASIS_R` to `LM_PATELLA_INFERIOR_R`.
   - **Fraction:** $t = 15 / 18 = 0.8333$. Lateral border of rectus femoris tendon ($Y \approx 0.547\text{ m}$).
   - **FMA Concept:** `FMA:22312` (Vastus lateralis / Rectus femoris tendon).
4. **`ST34` (Liangqiu, 梁丘):**
   - **WHO 2008 Standard (p. 76):** Anterior thigh, on line connecting ASIS and lateral patellar border, 2 B-cun superior to base of patella.
   - **Mathematical Anchor:** `LM_ASIS_R` to `LM_PATELLA_INFERIOR_R`.
   - **Fraction:** $t = 16 / 18 = 0.8889$. In depression superior to lateral patella ($Y \approx 0.521\text{ m}$).
   - **FMA Concept:** `FMA:22312` (Suprapatellar lateral depression).

---

### 2.2 Spleen Channel (SP) — Medial Thigh, Groin & Shoulder Girdle (4 Points)
1. **`SP11` (Jimen, 箕门):**
   - **WHO 2008 Standard (p. 90):** Medial thigh, 6 B-cun superior to SP10, on line connecting SP10 and SP12, medial border of sartorius.
   - **Mathematical Anchor:** `LM_PATELLA_INFERIOR_R` to `LM_PUBIC_SYMPHYSIS`.
   - **Fraction:** $t = 0.4400$. Medial thigh sartorius border ($Y \approx 0.642\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Sartorius medial margin).
2. **`SP12` (Chongmen, 冲门):**
   - **WHO 2008 Standard (p. 91):** Inguinal region, 3.5 B-cun lateral to anterior midline, level with superior border of pubic symphysis.
   - **Mathematical Anchor:** `LM_PUBIC_SYMPHYSIS` to `LM_ASIS_R`.
   - **Fraction:** $t = 0.4500$. Inguinal groove lateral to femoral artery ($Y \approx 0.899\text{ m}, X \approx 0.059\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Femoral triangle / Inguinal ligament).
3. **`SP13` (Fushe, 府舍):**
   - **WHO 2008 Standard (p. 91):** Lower abdomen, 0.7 B-cun superior and 0.5 B-cun lateral to SP12, 4 B-cun lateral to anterior midline.
   - **Mathematical Anchor:** `LM_PUBIC_SYMPHYSIS` to `LM_ASIS_R`.
   - **Fraction:** $t = 0.5500$. Lower abdomen lateral to rectus abdominis ($Y \approx 0.907\text{ m}, X \approx 0.073\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Inguinal abdominal margin).
4. **`SP20` (Zhourong, 周荣):**
   - **WHO 2008 Standard (p. 95):** Anterior chest, 2nd intercostal space, 6 B-cun lateral to anterior midline.
   - **Mathematical Anchor:** `LM_CLAVICLE_MIDPOINT_R` to `LM_AXILLARY_FOLD_ANT_R`.
   - **Fraction:** $t = 0.4000$. 2nd ICS in infraclavicular fossa ($Y \approx 1.380\text{ m}, X \approx 0.116\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Infraclavicular fossa / 2nd intercostal space).

---

### 2.3 Liver Channel (LR) — Medial Thigh & Groin (4 Points)
1. **`LR9` (Yinbao, 阴包):**
   - **WHO 2008 Standard (p. 197):** Medial thigh, 4 B-cun superior to medial femoral epicondyle, between vastus medialis and sartorius.
   - **Mathematical Anchor:** `LM_TIBIA_MEDIAL_CONDYLE_R` to `LM_PUBIC_SYMPHYSIS`.
   - **Fraction:** $t = 4 / 18 = 0.2222$. Medial thigh muscle groove ($Y \approx 0.525\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Vastus medialis / Sartorius groove).
2. **`LR10` (Zuwuli, 足五里):**
   - **WHO 2008 Standard (p. 197):** Medial thigh, 3 B-cun inferior to ST30, anterior border of adductor longus.
   - **Mathematical Anchor:** `LM_PUBIC_SYMPHYSIS` to `LM_TIBIA_MEDIAL_CONDYLE_R`, with 2.5 cun lateral offset.
   - **Fraction:** $t = 0.2000$, $\Delta_{\text{lat}} = 37.5\text{ mm}$. Adductor longus margin ($Y \approx 0.777\text{ m}, X \approx 0.043\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Adductor longus anterior margin).
3. **`LR11` (Yinlian, 阴廉):**
   - **WHO 2008 Standard (p. 198):** Medial thigh, 2 B-cun inferior to ST30, 2 B-cun lateral to anterior midline.
   - **Mathematical Anchor:** `LM_PUBIC_SYMPHYSIS` to `LM_TIBIA_MEDIAL_CONDYLE_R`, with 2.0 cun lateral offset.
   - **Fraction:** $t = 0.1200$, $\Delta_{\text{lat}} = 30.0\text{ mm}$. Inguinal adductor groove ($Y \approx 0.812\text{ m}, X \approx 0.033\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Gracilis / Adductor longus proximal groove).
4. **`LR12` (Jimai, 急脉):**
   - **WHO 2008 Standard (p. 198):** Inguinal region, lateral and inferior to pubic tubercle, in femoral groove medial to femoral vein.
   - **Mathematical Anchor:** `LM_PUBIC_SYMPHYSIS` to `LM_TIBIA_MEDIAL_CONDYLE_R`, with 1.5 cun lateral offset.
   - **Fraction:** $t = 0.0500$, $\Delta_{\text{lat}} = 22.5\text{ mm}$. Femoral groove medial to vein ($Y \approx 0.842\text{ m}, X \approx 0.024\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Pubic tubercle lateral femoral groove).

---

### 2.4 Gallbladder Channel (GB) — Lateral Thigh & Hip Girdle (4 Points)
1. **`GB29` (Juliao, 居髎):**
   - **WHO 2008 Standard (p. 182):** Hip region, midpoint of line connecting ASIS and prominence of greater trochanter.
   - **Mathematical Anchor:** `LM_ASIS_R` $(0.132, 0.942, 0.075)$ to `LM_GREATER_TROCHANTER_R` $(0.178, 0.855, -0.012)$.
   - **Fraction:** $t = 0.5000$ (exact geometric bisection). $Y \approx 0.899\text{ m}, X \approx 0.155\text{ m}, Z \approx 0.032\text{ m}$.
   - **FMA Concept:** `FMA:22312` (Hip joint / Gluteus medius).
2. **`GB31` (Fengshi, 风市):**
   - **WHO 2008 Standard (p. 183):** Lateral thigh, 7 B-cun superior to popliteal crease, posterior to iliotibial band.
   - **Mathematical Anchor:** `LM_GREATER_TROCHANTER_R` to `LM_POPLITEAL_CREASE_R`.
   - **Fraction:** $t = 12 / 19 = 0.6316$. Posterior to IT band ($Y \approx 0.607\text{ m}$).
   - **FMA Concept:** `FMA:22312` (Iliotibial tract posterior border).
3. **`GB32` (Zhongdu, 中渎):**
   - **WHO 2008 Standard (p. 183):** Lateral thigh, 5 B-cun superior to popliteal crease, between vastus lateralis and biceps femoris.
   - **Mathematical Anchor:** `LM_GREATER_TROCHANTER_R` to `LM_POPLITEAL_CREASE_R`.
   - **Fraction:** $t = 14 / 19 = 0.7368$. Lateral thigh groove ($Y \approx 0.565\text{ m}$).
   - **FMA Concept:** `FMA:22312` (Vastus lateralis / Biceps femoris groove).
4. **`GB33` (Xiyangguan, 膝阳关):**
   - **WHO 2008 Standard (p. 184):** Lateral aspect of knee, 3 B-cun superior to GB34, depression superior to lateral femoral epicondyle.
   - **Mathematical Anchor:** `LM_GREATER_TROCHANTER_R` to `LM_POPLITEAL_CREASE_R`.
   - **Fraction:** $t = 17 / 19 = 0.8947$. Superior to lateral femoral epicondyle ($Y \approx 0.503\text{ m}$).
   - **FMA Concept:** `FMA:22312` (Lateral femoral epicondyle superior depression).

---

### 2.5 Bladder Channel (BL) — Posterior Thigh, Girdle & Calf (11 Points)
1. **`BL36` (Chengfu, 承扶):**
   - **WHO 2008 Standard (p. 120):** Posterior thigh, midpoint of gluteal fold.
   - **Mathematical Anchor:** `LM_GREATER_TROCHANTER_R` to `LM_POPLITEAL_CREASE_R`.
   - **Fraction:** $t = 0.1500$. Gluteal fold midpoint ($Y \approx 0.796\text{ m}, Z \approx -0.018\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Gluteal fold / Biceps femoris long head).
2. **`BL37` (Yinmen, 殷门):**
   - **WHO 2008 Standard (p. 120):** Posterior thigh, 6 B-cun inferior to BL36 on line connecting BL36 and BL40.
   - **Mathematical Anchor:** `LM_GREATER_TROCHANTER_R` to `LM_POPLITEAL_CREASE_R`.
   - **Fraction:** $t = 0.5000$. Posterior midline of thigh ($Y \approx 0.659\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Biceps femoris / Semitendinosus interval).
3. **`BL38` (Fuxi, 浮郄):**
   - **WHO 2008 Standard (p. 121):** Popliteal fossa, 1 B-cun superior to BL39, medial border of biceps femoris tendon.
   - **Mathematical Anchor:** `LM_GREATER_TROCHANTER_R` to `LM_POPLITEAL_CREASE_R`.
   - **Fraction:** $t = 0.8800$. Medial border of biceps tendon ($Y \approx 0.509\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Biceps femoris tendon medial border).
4. **`BL39` (Weiyang, 委阳):**
   - **WHO 2008 Standard (p. 121):** Popliteal crease, medial to biceps femoris tendon, at same level as BL40.
   - **Mathematical Anchor:** `LM_GREATER_TROCHANTER_R` to `LM_POPLITEAL_CREASE_R`.
   - **Fraction:** $t = 0.9600$. Lateral border of popliteal crease ($Y \approx 0.478\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Popliteal crease lateral terminus).
5. **`BL53` (Baohuang, 胞肓):**
   - **WHO 2008 Standard (p. 128):** Gluteal region, level of 2nd posterior sacral foramen, 3 B-cun lateral to median sacral crest.
   - **Mathematical Anchor:** `LM_SACRAL_HIATUS` to `LM_GREATER_TROCHANTER_R`.
   - **Fraction:** $t = 0.5500$. Gluteal musculature ($Y \approx 0.869\text{ m}, X \approx 0.098\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Gluteus maximus / 2nd sacral foramen level).
6. **`BL55` (Heyang, 合阳):**
   - **WHO 2008 Standard (p. 129):** Posterior leg, 2 B-cun inferior to BL40 on line connecting BL40 and BL57.
   - **Mathematical Anchor:** `LM_POPLITEAL_CREASE_R` to `LM_CALCANEUS_POST_R`.
   - **Fraction:** $t = 2 / 16 = 0.1250$. Gastrocnemius proximal midline ($Y \approx 0.407\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Gastrocnemius interval 2 cun below popliteal).
7. **`BL56` (Chengjin, 承筋):**
   - **WHO 2008 Standard (p. 129):** Posterior leg, 5 B-cun inferior to BL40, center of gastrocnemius muscle belly.
   - **Mathematical Anchor:** `LM_POPLITEAL_CREASE_R` to `LM_CALCANEUS_POST_R`.
   - **Fraction:** $t = 5 / 16 = 0.3125$. Midpoint of gastrocnemius belly ($Y \approx 0.325\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Gastrocnemius muscle belly center).
8. **`BL57` (Chengshan, 承山):**
   - **WHO 2008 Standard (p. 130):** Posterior leg, in depression at inferior junction of gastrocnemius muscle bellies, 8 B-cun inferior to BL40.
   - **Mathematical Anchor:** `LM_POPLITEAL_CREASE_R` to `LM_CALCANEUS_POST_R`.
   - **Fraction:** $t = 8 / 16 = 0.5000$. Musculotendinous junction ($Y \approx 0.243\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Gastrocnemius inferior belly junction).
9. **`BL58` (Feiyang, 飞扬):**
   - **WHO 2008 Standard (p. 130):** Posterior-lateral leg, 7 B-cun superior to BL60, 1 B-cun inferior and lateral to BL57.
   - **Mathematical Anchor:** `LM_POPLITEAL_CREASE_R` to `LM_CALCANEUS_POST_R`.
   - **Fraction:** $t = 9 / 16 = 0.5625$. Lateral border of Achilles / soleus ($Y \approx 0.216\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Gastrocnemius lateral margin).
10. **`BL59` (Fuyang, 跗阳):**
    - **WHO 2008 Standard (p. 131):** Posterior-lateral leg, 3 B-cun superior to BL60, posterior to fibula.
    - **Mathematical Anchor:** `LM_POPLITEAL_CREASE_R` to `LM_CALCANEUS_POST_R`.
    - **Fraction:** $t = 13 / 16 = 0.8125$. Posterior to fibular shaft ($Y \approx 0.106\text{ m}$).
    - **FMA Concept:** `FMA:22314` (Peroneal / Achilles lateral interval).
11. **`BL60` (Kunlun, 昆仑):**
    - **WHO 2008 Standard (p. 131):** Posterolateral ankle, in depression between lateral malleolus prominence and Achilles tendon.
    - **Mathematical Anchor:** `LM_LAT_MALLEOLUS_R` $(0.138, 0.074, 0.008)$ to `LM_CALCANEUS_POST_R` $(0.108, 0.024, -0.068)$.
    - **Fraction:** $t = 0.5000$. Lateral retromalleolar depression ($Y \approx 0.049\text{ m}$).
    - **FMA Concept:** `FMA:22314` (Lateral retromalleolar depression).

---

### 2.6 Kidney Channel (KI) — Medial Crural Calf (2 Points)
1. **`KI8` (Jiaoxin, 交信):**
   - **WHO 2008 Standard (p. 142):** Medial leg, 2 B-cun superior to medial malleolus, on posterior border of medial tibia.
   - **Mathematical Anchor:** `LM_MED_MALLEOLUS_R` to `LM_TIBIA_MEDIAL_CONDYLE_R`.
   - **Fraction:** $t = 2 / 13 = 0.1538$. Posterior border of tibia ($Y \approx 0.135\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Tibial posterior medial margin).
2. **`KI9` (Zhubin, 筑宾):**
   - **WHO 2008 Standard (p. 143):** Medial leg, 5 B-cun superior to medial malleolus, at inferior border of gastrocnemius muscle belly.
   - **Mathematical Anchor:** `LM_MED_MALLEOLUS_R` to `LM_TIBIA_MEDIAL_CONDYLE_R`.
   - **Fraction:** $t = 5 / 13 = 0.3846$. Inferior border of medial gastrocnemius ($Y \approx 0.215\text{ m}$).
   - **FMA Concept:** `FMA:22314` (Gastrocnemius medial belly inferior margin).

---

### 2.7 Heart Channel (HT) — Axilla & Upper Arm (2 Points)
1. **`HT1` (Jiquan, 极泉):**
   - **WHO 2008 Standard (p. 106):** Center of axillary fossa, medial to axillary artery.
   - **Mathematical Anchor:** `LM_AXILLARY_FOLD_ANT_R` $(0.148, 1.332, 0.054)$ to `LM_CUBITAL_CREASE_R`.
   - **Fraction:** $t = 0.0500$. Apex of axillary pyramid ($Y \approx 1.320\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Axillary fossa center).
2. **`HT2` (Qingling, 青灵):**
   - **WHO 2008 Standard (p. 106):** Medial arm, 3 B-cun superior to medial epicondyle of humerus, groove medial to biceps brachii.
   - **Mathematical Anchor:** `LM_AXILLARY_FOLD_ANT_R` to `LM_MED_EPICONDYLE_HUMERUS_R`.
   - **Fraction:** $t = 6 / 9 = 0.6667$. Medial bicipital groove ($Y \approx 1.169\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Medial bicipital groove).

---

### 2.8 Pericardium Channel (PC) — Pectoral Girdle & Upper Arm (2 Points)
1. **`PC1` (Tianchi, 天池):**
   - **WHO 2008 Standard (p. 165):** Anterior chest, 4th intercostal space, 1 B-cun lateral to nipple, 5 B-cun lateral to anterior midline.
   - **Mathematical Anchor:** `LM_CLAVICLE_MIDPOINT_R` to `LM_AXILLARY_FOLD_ANT_R`.
   - **Fraction:** $t = 0.5000$. Pectoral girdle 4th intercostal level ($Y \approx 1.372\text{ m}, X \approx 0.121\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Pectoralis major / 4th intercostal space).
2. **`PC2` (Tianquan, 天泉):**
   - **WHO 2008 Standard (p. 165):** Anterior arm, 2 B-cun inferior to anterior axillary fold, between two heads of biceps brachii.
   - **Mathematical Anchor:** `LM_AXILLARY_FOLD_ANT_R` to `LM_CUBITAL_CREASE_R`.
   - **Fraction:** $t = 2 / 9 = 0.2222$. Between long and short heads of biceps brachii ($Y \approx 1.276\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Biceps brachii inter-head interval).

---

### 2.9 Large Intestine Channel (LI) — Upper Arm, Elbow & Girdle (4 Points)
1. **`LI12` (Zhouliao, 肘髎):**
   - **WHO 2008 Standard (p. 57):** Posterolateral elbow, 1 B-cun superior and lateral to LI11, on anterior border of lateral humeral epicondyle.
   - **Mathematical Anchor:** `LM_LAT_EPICONDYLE_HUMERUS_R` to `LM_ACROMION_R`.
   - **Fraction:** $t = 0.0800$. Epicondylar ridge ($Y \approx 1.111\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Lateral humeral supracondylar ridge).
2. **`LI13` (Shouwuli, 手五里):**
   - **WHO 2008 Standard (p. 58):** Lateral arm, on line connecting LI11 and LI15, 3 B-cun superior to lateral epicondyle.
   - **Mathematical Anchor:** `LM_LAT_EPICONDYLE_HUMERUS_R` to `LM_ACROMION_R`.
   - **Fraction:** $t = 3 / 10 = 0.3000$. Lateral humerus column ($Y \approx 1.183\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Brachioradialis / Triceps lateral margin).
3. **`LI14` (Binao, 臂臑):**
   - **WHO 2008 Standard (p. 58):** Lateral arm, on line connecting LI11 and LI15, 7 B-cun superior to LI11, at deltoid insertion.
   - **Mathematical Anchor:** `LM_LAT_EPICONDYLE_HUMERUS_R` to `LM_ACROMION_R`.
   - **Fraction:** $t = 7 / 10 = 0.7000$. Deltoid muscle tuberosity ($Y \approx 1.314\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Deltoid muscle humeral insertion).
4. **`LI16` (Jugu, 巨骨):**
   - **WHO 2008 Standard (p. 59):** Shoulder girdle, in depression between acromial end of clavicle and spine of scapula.
   - **Mathematical Anchor:** `LM_ACROMION_R` to `LM_SCAPULA_MEDIAL_BORDER_R`.
   - **Fraction:** $t = 0.4000$. Clavicle-scapula spine junction ($Y \approx 1.385\text{ m}, X \approx 0.140\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Acromioclavicular suprascapular fossa).

---

### 2.10 Triple Energizer Channel (TE) — Upper Arm, Elbow & Girdle (5 Points)
1. **`TE10` (Tianjing, 天井):**
   - **WHO 2008 Standard (p. 153):** Posterior elbow, in depression 1 B-cun superior to olecranon with elbow flexed.
   - **Mathematical Anchor:** `LM_LAT_EPICONDYLE_HUMERUS_R` to `LM_ACROMION_R`.
   - **Fraction:** $t = 0.0800$. Olecranon fossa posterior depression ($Y \approx 1.111\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Olecranon fossa).
2. **`TE11` (Qinglengyuan, 清冷渊):**
   - **WHO 2008 Standard (p. 153):** Posterior arm, on line connecting TE10 and TE14, 1 B-cun superior to TE10.
   - **Mathematical Anchor:** `LM_LAT_EPICONDYLE_HUMERUS_R` to `LM_ACROMION_R`.
   - **Fraction:** $t = 0.1800$. Posterior triceps tendon ($Y \approx 1.144\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Triceps tendon posterior aspect).
3. **`TE12` (Xiaoluo, 消泺):**
   - **WHO 2008 Standard (p. 154):** Posterior arm, on line connecting TE10 and TE14, 5 B-cun superior to TE10.
   - **Mathematical Anchor:** `LM_LAT_EPICONDYLE_HUMERUS_R` to `LM_ACROMION_R`.
   - **Fraction:** $t = 0.5500$. Triceps muscle belly center ($Y \approx 1.265\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Triceps brachii belly center).
4. **`TE13` (Naohui, 臑会):**
   - **WHO 2008 Standard (p. 154):** Posterior arm, 3 B-cun inferior to TE14, on posterior border of deltoid muscle.
   - **Mathematical Anchor:** `LM_LAT_EPICONDYLE_HUMERUS_R` to `LM_ACROMION_R`.
   - **Fraction:** $t = 0.7000$. Posterior deltoid border ($Y \approx 1.314\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Deltoid muscle posterior margin).
5. **`TE15` (Tianliao, 天髎):**
   - **WHO 2008 Standard (p. 155):** Scapular region, midway between GB21 and superior angle of scapula.
   - **Mathematical Anchor:** `LM_ACROMION_R` to `LM_C7_SPINE`.
   - **Fraction:** $t = 0.4500$. Superior scapular angle depression ($Y \approx 1.442\text{ m}, X \approx 0.103\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Suprascapular fossa superior angle).

---

### 2.11 Small Intestine Channel (SI) — Scapular Girdle & Upper Back (6 Points)
1. **`SI9` (Jianzhen, 肩贞):**
   - **WHO 2008 Standard (p. 113):** Posterior shoulder, 1 B-cun superior to posterior end of axillary fold.
   - **Mathematical Anchor:** `LM_ACROMION_R` to `LM_SCAPULA_MEDIAL_BORDER_R`.
   - **Fraction:** $t = 0.2500$. Deltoid posterior margin ($Y \approx 1.395\text{ m}, X \approx 0.158\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Deltoid posterior border / Teres major).
2. **`SI10` (Naoshu, 臑俞):**
   - **WHO 2008 Standard (p. 114):** Posterior shoulder, directly superior to SI9, depression inferior to scapular spine.
   - **Mathematical Anchor:** `LM_ACROMION_R` to `LM_SCAPULA_MEDIAL_BORDER_R`.
   - **Fraction:** $t = 0.3500$. Infraspinatus scapular depression ($Y \approx 1.389\text{ m}, X \approx 0.146\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Infraspinatus fossa lateral margin).
3. **`SI12` (Bingfeng, 秉风):**
   - **WHO 2008 Standard (p. 115):** Scapular region, center of supraspinatus fossa, directly superior to SI11.
   - **Mathematical Anchor:** `LM_ACROMION_R` to `LM_SCAPULA_MEDIAL_BORDER_R`.
   - **Fraction:** $t = 0.5000$. Supraspinatus fossa center ($Y \approx 1.379\text{ m}, X \approx 0.128\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Supraspinatus fossa center).
4. **`SI13` (Quyuan, 曲垣):**
   - **WHO 2008 Standard (p. 115):** Scapular region, depression superior to medial end of scapular spine.
   - **Mathematical Anchor:** `LM_ACROMION_R` to `LM_SCAPULA_MEDIAL_BORDER_R`.
   - **Fraction:** $t = 0.6500$. Medial scapular spine fossa ($Y \approx 1.368\text{ m}, X \approx 0.110\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Scapular spine medial terminus).
5. **`SI14` (Jianwaishu, 肩外俞):**
   - **WHO 2008 Standard (p. 116):** Upper back, 3 B-cun lateral to inferior border of spinous process of T1.
   - **Mathematical Anchor:** `LM_SCAPULA_MEDIAL_BORDER_R` to `LM_C7_SPINE`.
   - **Fraction:** $t = 0.3500$. Upper back 3 cun lateral to T1 ($Y \approx 1.392\text{ m}, X \approx 0.044\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Trapezius / Rhomboid major medial border).
6. **`SI15` (Jianzhongshu, 肩中俞):**
   - **WHO 2008 Standard (p. 116):** Upper back, 2 B-cun lateral to inferior border of spinous process of C7.
   - **Mathematical Anchor:** `LM_SCAPULA_MEDIAL_BORDER_R` to `LM_C7_SPINE`.
   - **Fraction:** $t = 0.6000$. Neck base 2 cun lateral to C7 ($Y \approx 1.425\text{ m}, X \approx 0.027\text{ m}$).
   - **FMA Concept:** `FMA:24294` (Levator scapulae / Trapezius cervical margin).
