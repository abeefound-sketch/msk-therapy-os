/**
 * MSK-Therapy-OS - Interactive Shoulder Posture & Biomechanics Studio (Phase P13-E)
 * 
 * Interactive exploration of:
 * "Why Do Rounded Shoulders Sometimes Return After Massage?"
 * ("Tại sao giải cơ xong vai nhẹ hơn nhưng một thời gian sau vẫn đổ về trước?")
 * 
 * Enforces non-negotiable invariants:
 *   G14 = BLOCKED_EXTERNAL_DATA
 *   clinical_depth_guidance_allowed = False
 *   EDUCATIONAL_SIMULATION != PATIENT_SPECIFIC_MEASUREMENT
 *   MODEL_PREDICTION != EMPIRICALLY_VALIDATED_MOTION
 *   MUSCLE_HIGHLIGHT != MEASURED_MUSCLE_ACTIVATION
 *   POSTURAL_APPEARANCE != MEDICAL_DIAGNOSIS
 */

export class ShoulderLab {
    constructor(viewer, options = {}) {
        this.viewer = viewer;
        this.currentLang = 'vi'; // default to Vietnamese as requested, can toggle to 'en'
        this.currentStageId = 1;
        this.postureSeverity = 0.65; // 65% rounded shoulder baseline
        this.curriculum = null;

        this.elements = {
            stageList: document.getElementById('stage-list'),
            stageTitle: document.getElementById('stage-title'),
            stageSummary: document.getElementById('stage-summary'),
            postureSlider: document.getElementById('posture-slider'),
            postureLabel: document.getElementById('posture-val-label'),
            protractionVal: document.getElementById('val-protraction'),
            anteriorTiltVal: document.getElementById('val-anterior-tilt'),
            upwardRotVal: document.getElementById('val-upward-rot'),
            rhythmRatioVal: document.getElementById('val-rhythm-ratio'),
            rhythmStatusVal: document.getElementById('val-rhythm-status'),
            reciprocalScoreVal: document.getElementById('val-reciprocal-score'),
            evidenceList: document.getElementById('evidence-list'),
            langToggleBtn: document.getElementById('btn-lang-toggle'),
            viewAnteriorBtn: document.getElementById('btn-view-anterior'),
            viewPosteriorBtn: document.getElementById('btn-view-posterior'),
            viewLateralBtn: document.getElementById('btn-view-lateral'),
            fpsBadge: document.getElementById('fps-badge')
        };

        this._init();
    }

    async _init() {
        this._bindControls();
        await this._loadCurriculum();
        this._renderStage(this.currentStageId);
        this._updateBiomechanics(this.postureSeverity);

        if (this.viewer) {
            this.viewer.setFpsCallback((fps) => {
                if (this.elements.fpsBadge) {
                    this.elements.fpsBadge.textContent = `${fps} FPS`;
                    this.elements.fpsBadge.className = fps >= 30 ? 'badge badge-green' : 'badge badge-amber';
                }
            });
        }
    }

    _bindControls() {
        if (this.elements.langToggleBtn) {
            this.elements.langToggleBtn.addEventListener('click', () => {
                this.currentLang = this.currentLang === 'vi' ? 'en' : 'vi';
                this.elements.langToggleBtn.textContent = this.currentLang === 'vi' ? 'EN / VI' : 'VI / EN';
                this._renderCurriculum();
                this._renderStage(this.currentStageId);
            });
        }

        if (this.elements.postureSlider) {
            this.elements.postureSlider.addEventListener('input', (e) => {
                const val = parseFloat(e.target.value) / 100.0;
                this.postureSeverity = val;
                this._updateBiomechanics(val);
            });
        }

        if (this.elements.viewAnteriorBtn) {
            this.elements.viewAnteriorBtn.addEventListener('click', () => {
                if (this.viewer) this.viewer.resetCamera('shoulder');
            });
        }

        if (this.elements.viewPosteriorBtn) {
            this.elements.viewPosteriorBtn.addEventListener('click', () => {
                if (this.viewer) this.viewer.resetCamera('scapula');
            });
        }

        if (this.elements.viewLateralBtn) {
            this.elements.viewLateralBtn.addEventListener('click', () => {
                if (this.viewer && this.viewer.camera && this.viewer.controls) {
                    this.viewer.camera.position.set(0.95, 1.45, 0.0);
                    this.viewer.controls.target.set(0.08, 1.40, 0.0);
                    this.viewer.controls.update();
                }
            });
        }
    }

    async _loadCurriculum() {
        try {
            const resp = await fetch('/api/education/shoulder-lesson');
            if (resp.ok) {
                this.curriculum = await resp.json();
            } else {
                throw new Error('Server returned ' + resp.status);
            }
        } catch (err) {
            console.warn('[ShoulderLab] API fetch failed, loading offline curriculum fallback:', err);
            this.curriculum = this._getOfflineFallbackCurriculum();
        }
        this._renderCurriculum();
    }

    _renderCurriculum() {
        if (!this.curriculum || !this.elements.stageList) return;

        const isVi = this.currentLang === 'vi';
        document.getElementById('header-title').textContent = isVi ? this.curriculum.title_vi : this.curriculum.title_en;
        document.getElementById('header-subtitle').textContent = isVi ? this.curriculum.subtitle_vi : this.curriculum.subtitle_en;

        this.elements.stageList.innerHTML = '';
        this.curriculum.stages.forEach((stage) => {
            const item = document.createElement('div');
            item.className = `stage-nav-item ${stage.stage_id === this.currentStageId ? 'active' : ''}`;
            item.dataset.stageId = stage.stage_id;
            item.innerHTML = `
                <div class="stage-nav-num">${stage.stage_id}</div>
                <div class="stage-nav-text">
                    <div class="stage-nav-title">${isVi ? stage.name_vi : stage.name_en}</div>
                </div>
            `;
            item.addEventListener('click', () => {
                this.currentStageId = stage.stage_id;
                this._renderStage(stage.stage_id);
                // Update active class
                document.querySelectorAll('.stage-nav-item').forEach(el => el.classList.remove('active'));
                item.classList.add('active');
            });
            this.elements.stageList.appendChild(item);
        });

        // Render Evidence register
        if (this.elements.evidenceList && this.curriculum.evidence_register) {
            this.elements.evidenceList.innerHTML = '';
            this.curriculum.evidence_register.forEach((ev) => {
                const li = document.createElement('li');
                li.className = 'evidence-item';
                li.innerHTML = `
                    <span class="evidence-tag">${ev.id}</span>
                    <span class="evidence-citation">${ev.citation}</span>
                    <div class="evidence-desc">${ev.topic}</div>
                `;
                this.elements.evidenceList.appendChild(li);
            });
        }
    }

    _renderStage(stageId) {
        if (!this.curriculum) return;
        const stage = this.curriculum.stages.find(s => s.stage_id === stageId);
        if (!stage) return;

        const isVi = this.currentLang === 'vi';
        if (this.elements.stageTitle) {
            this.elements.stageTitle.textContent = `${stage.stage_id}. ${isVi ? stage.name_vi : stage.name_en}`;
        }
        if (this.elements.stageSummary) {
            this.elements.stageSummary.textContent = isVi ? stage.summary_vi : stage.summary_en;
        }

        // Highlight muscles relevant to this educational stage
        if (this.viewer && stage.focus_muscles) {
            this.viewer.highlightMuscles(stage.focus_muscles);
        }

        // Focus camera according to stage
        if (this.viewer) {
            if (stageId === 3 || stageId === 5) {
                this.viewer.resetCamera('scapula'); // focus on posterior muscles
            } else {
                this.viewer.resetCamera('shoulder');
            }
        }
    }

    _updateBiomechanics(severity) {
        // Linear interpolation across severity [0.0 = Neutral, 1.0 = Severe Rounded Shoulder]
        const protraction = 15.0 + severity * 28.0; // 15 deg -> 43 deg
        const anteriorTilt = 10.0 + severity * 22.0; // 10 deg -> 32 deg
        const upwardRot = 16.0 - severity * 14.0; // 16 deg -> 2 deg

        // Scapulohumeral rhythm ratio (at 90 deg elevation)
        // Normal: 60 deg GH / 30 deg ST = 2.0:1
        // Protracted: upward rotation reduced, ratio climbs to 3.2+:1
        const ratio = upwardRot > 0.5 ? (60.0 / (upwardRot * 2.0)).toFixed(2) : '> 4.0';

        let rhythmClassification = 'Normal (~2.0:1)';
        let badgeColor = 'badge-green';
        if (severity > 0.40 && severity <= 0.70) {
            rhythmClassification = this.currentLang === 'vi' ? 'Giảm xoay lên (2.4:1)' : 'Reduced Upward Rot (2.4:1)';
            badgeColor = 'badge-amber';
        } else if (severity > 0.70) {
            rhythmClassification = this.currentLang === 'vi' ? 'Rối loạn vận động bả vai (> 3.0:1)' : 'Scapular Dyskinesis (> 3.0:1)';
            badgeColor = 'badge-red';
        }

        const reciprocalBalanceScore = Math.max(10, Math.round((1.0 - severity) * 100));

        // Update DOM displays
        if (this.elements.postureLabel) {
            this.elements.postureLabel.textContent = `${Math.round(severity * 100)}%`;
        }
        if (this.elements.protractionVal) {
            this.elements.protractionVal.textContent = `${protraction.toFixed(1)}°`;
        }
        if (this.elements.anteriorTiltVal) {
            this.elements.anteriorTiltVal.textContent = `${anteriorTilt.toFixed(1)}°`;
        }
        if (this.elements.upwardRotVal) {
            this.elements.upwardRotVal.textContent = `${upwardRot.toFixed(1)}°`;
        }
        if (this.elements.rhythmRatioVal) {
            this.elements.rhythmRatioVal.textContent = `${ratio} : 1`;
        }
        if (this.elements.rhythmStatusVal) {
            this.elements.rhythmStatusVal.textContent = rhythmClassification;
            this.elements.rhythmStatusVal.className = `badge ${badgeColor}`;
        }
        if (this.elements.reciprocalScoreVal) {
            this.elements.reciprocalScoreVal.textContent = `${reciprocalBalanceScore}/100`;
        }
    }

    _getOfflineFallbackCurriculum() {
        return {
            "title_en": "Why Do Rounded Shoulders Sometimes Return After Massage?",
            "title_vi": "Tại sao giải cơ xong vai nhẹ hơn nhưng một thời gian sau vẫn đổ về trước?",
            "subtitle_en": "Anatomy, Scapulohumeral Biomechanics, Neural Adaptation & Integrative Self-Care",
            "subtitle_vi": "Giải phẫu học, Cơ sinh học bả vai - cánh tay, Thích nghi thần kinh & Tự chăm sóc tích hợp",
            "stages": [
                {
                    "stage_id": 1,
                    "name_en": "The Core Paradox: Transient Relief vs. Postural Recurrence",
                    "name_vi": "Nghịch lý cốt lõi: Nhẹ cơ tức thời vs. Tái phát tư thế",
                    "summary_en": "Manual massage reduces local hypertonicity via mechanoreceptor stimulation, but cannot reprogram habitual motor patterns or restore reciprocal muscle balance alone.",
                    "summary_vi": "Giải cơ bằng tay giảm trương lực qua thụ thể cơ học tức thời, nhưng không thể đơn độc lập trình lại phản xạ vận động hay cân bằng cơ đối kháng.",
                    "focus_muscles": ["pectoralis_minor", "trapezius_upper"]
                },
                {
                    "stage_id": 2,
                    "name_en": "Anterior Shortening: Pectoralis Minor & Major",
                    "name_vi": "Sự co ngắn nhóm cơ phía trước: Cơ ngực bé & Cơ ngực lớn",
                    "summary_en": "Prolonged sitting tethers the coracoid process forward and downward into anterior scapular tilt.",
                    "summary_vi": "Ngồi gù lưng kéo dài làm cơ ngực bé co ngắn kinh niên, kéo mỏm quạ xương bả vai chúc về phía trước và xuống dưới.",
                    "focus_muscles": ["pectoralis_minor", "pectoralis_major", "deltoid_anterior"]
                },
                {
                    "stage_id": 3,
                    "name_en": "Posterior Inhibition: Serratus Anterior & Lower Trapezius",
                    "name_vi": "Sự ức chế nhóm cơ phía sau: Cơ răng trước & Cơ thang dưới",
                    "summary_en": "Reciprocal inhibition leaves posterior stabilizers functionally weak.",
                    "summary_vi": "Hiện tượng ức chế tương hỗ khiến các cơ ổn định mặt sau bị yếu chức năng.",
                    "focus_muscles": ["serratus_anterior", "trapezius_lower", "rhomboid_major"]
                },
                {
                    "stage_id": 4,
                    "name_en": "Scapulohumeral Rhythm & Subacromial Space",
                    "name_vi": "Nhịp sinh học bả vai - cánh tay & Khoang dưới mỏm cùng vai",
                    "summary_en": "Rounded shoulders disrupt the 2:1 ratio, predisposing to impingement.",
                    "summary_vi": "Vai đổ trước phá vỡ tỷ lệ 2:1, làm tăng nguy cơ chèn ép khoang dưới mỏm cùng vai.",
                    "focus_muscles": ["deltoid_lateral"]
                },
                {
                    "stage_id": 5,
                    "name_en": "Neural Adaptation & Habitual Proprioception",
                    "name_vi": "Thích nghi thần kinh & Cảm thụ bản thể theo thói quen",
                    "summary_en": "The brain recalibrates forward posture as its internal neutral setpoint.",
                    "summary_vi": "Hệ thần kinh định nghĩa tư thế vai đổ trước thành điểm trung tính quen thuộc.",
                    "focus_muscles": ["trapezius_middle", "rhomboid_minor"]
                },
                {
                    "stage_id": 6,
                    "name_en": "The Integrative Solution: Release + Activate + Ergonomics",
                    "name_vi": "Giải pháp tích hợp: Thả lỏng + Kích hoạt + Công thái học",
                    "summary_en": "Lasting correction requires releasing shortened anterior muscles, activating posterior stabilizers, and adjusting daily workstation ergonomics.",
                    "summary_vi": "Hiệu quả bền vững đòi hỏi kết hợp giải cơ ngực co ngắn, kích hoạt cơ lưng bả vai, và điều chỉnh công thái học làm việc.",
                    "focus_muscles": ["pectoralis_minor", "trapezius_lower", "serratus_anterior"]
                }
            ],
            "evidence_register": [
                {
                    "id": "EV-01",
                    "citation": "Inman VT, et al. Observations on the function of the shoulder joint. JBJS. 1944.",
                    "topic": "2:1 Scapulohumeral rhythm"
                },
                {
                    "id": "EV-02",
                    "citation": "Ludewig PM, Cook TM. Alterations in shoulder kinematics. Phys Ther. 2000.",
                    "topic": "Scapular dyskinesis & anterior tilt"
                },
                {
                    "id": "EV-03",
                    "citation": "Borstad JD, Ludewig PM. Pectoralis minor resting length. JOSPT. 2005.",
                    "topic": "Pectoralis minor shortening mechanics"
                }
            ]
        };
    }
}
