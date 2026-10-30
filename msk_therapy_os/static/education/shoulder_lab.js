/**
 * MSK-Therapy-OS - Interactive Biomechanics Shoulder Lab (Phase P14-F & P14-G)
 * 
 * Milestone P14: Evidence-Grounded Dynamic Biomechanics, Muscle Recruitment Visualization & Interactive MSK Education.
 * 
 * Enforces non-negotiable boundaries:
 *   G14 = BLOCKED_EXTERNAL_DATA
 *   clinical_depth_guidance_allowed = False
 *   RELEASE_SCOPE = ENGINEERING_RESEARCH_ONLY
 *   CLINICAL_VALIDATION = NOT_ESTABLISHED
 *   ANATOMICAL_MODEL != SUBJECT_SPECIFIC_ANATOMY
 *   ILLUSTRATIVE_KINEMATICS != MEASURED_KINEMATICS
 *   MUSCLE_ACTION_DESCRIPTION != MEASURED_MUSCLE_ACTIVATION
 *   OPTIMIZED_MUSCLE_ACTIVATION != MEASURED_EMG
 *   SIMULATED_FORCE != MEASURED_HUMAN_FORCE
 *   POSTURE_VARIATION != CLINICAL_DIAGNOSIS
 *   ANIMATION_SUCCESS != BIOMECHANICAL_VALIDATION
 */

export class ShoulderLab {
    constructor(viewer) {
        this.viewer = viewer;
        this.currentLang = 'vi'; // 'vi' or 'en'
        this.currentStageId = 1;
        this.postureSeverity = 0.65;
        this.curriculum = null;
        this.skeletonVisible = true;
        this.currentMode = 'ANATOMICAL_FUNCTION'; // 'ANATOMICAL_FUNCTION', 'MODEL_ESTIMATED', 'SCENARIO_COMPARISON'

        // Check if explicitly launched in P14 mode via URL
        const urlParams = new URLSearchParams(window.location.search);
        this.isP14 = urlParams.get('v') === 'p14' || urlParams.get('milestone') === 'p14';

        // Quiz State
        this.quizAnswers = {};

        this.elements = {
            // Header
            headerTitle: document.getElementById('header-title'),
            headerSubtitle: document.getElementById('header-subtitle'),
            langToggleBtn: document.getElementById('btn-lang-toggle'),
            studioModeToggleBtn: document.getElementById('btn-studio-mode-toggle'),
            fpsBadge: document.getElementById('fps-badge'),

            // Curriculum
            lblCurriculumHeader: document.getElementById('lbl-curriculum-header'),
            badgeCurriculumVersion: document.getElementById('badge-curriculum-version'),
            stageTitle: document.getElementById('stage-title'),
            stageSummary: document.getElementById('stage-summary'),
            stageDynamicBody: document.getElementById('stage-dynamic-body'),
            dynamicLeftContent: document.getElementById('dynamic-left-content'),
            stageListHeader: document.getElementById('stage-list-header'),
            stageList: document.getElementById('stage-list'),

            // Camera & Visibility
            viewAnteriorBtn: document.getElementById('btn-view-anterior'),
            viewPosteriorBtn: document.getElementById('btn-view-posterior'),
            viewLateralBtn: document.getElementById('btn-view-lateral'),
            toggleSkeletonBtn: document.getElementById('btn-toggle-skeleton'),
            muscleOpacitySlider: document.getElementById('muscle-opacity-slider'),

            // Motion Player Controls
            btnMotionPlay: document.getElementById('btn-motion-play'),
            btnMotionReset: document.getElementById('btn-motion-reset'),
            btnSpeed025: document.getElementById('btn-speed-025'),
            btnSpeed05: document.getElementById('btn-speed-05'),
            btnSpeed1: document.getElementById('btn-speed-1'),
            motionTimeSlider: document.getElementById('motion-time-slider'),
            motionTimeLabel: document.getElementById('motion-time-label'),
            scenarioSelect: document.getElementById('scenario-select'),

            // Visual Modes
            btnModeAnatomy: document.getElementById('btn-mode-anatomy'),
            btnModeActivation: document.getElementById('btn-mode-activation'),
            btnModeComparison: document.getElementById('btn-mode-comparison'),
            badgeActivationMode: document.getElementById('badge-activation-mode'),
            watermarkActivationBanner: document.getElementById('watermark-activation-banner'),

            // Dynamic Kinematic Readouts
            dynArmElev: document.getElementById('dyn-arm-elev'),
            dynScapUp: document.getElementById('dyn-scap-up'),
            dynScapTilt: document.getElementById('dyn-scap-tilt'),
            dynClavElev: document.getElementById('dyn-clav-elev'),
            dynRhythmRatio: document.getElementById('dyn-rhythm-ratio'),
            valRhythmRatio: document.getElementById('val-rhythm-ratio'),

            // Muscle Recruitment Bars
            valActDeltoidLateral: document.getElementById('val-act-deltoid-lateral'),
            barActDeltoidLateral: document.getElementById('bar-act-deltoid-lateral'),
            valActSupraspinatus: document.getElementById('val-act-supraspinatus'),
            barActSupraspinatus: document.getElementById('bar-act-supraspinatus'),
            valActSerratus: document.getElementById('val-act-serratus'),
            barActSerratus: document.getElementById('bar-act-serratus'),
            valActTrapeziusLower: document.getElementById('val-act-trapezius-lower'),
            barActTrapeziusLower: document.getElementById('bar-act-trapezius-lower'),
            valActPecMinor: document.getElementById('val-act-pec-minor'),
            barActPecMinor: document.getElementById('bar-act-pec-minor'),
            valActRhomboid: document.getElementById('val-act-rhomboid'),
            barActRhomboid: document.getElementById('bar-act-rhomboid'),

            // Posture Simulator
            postureSlider: document.getElementById('posture-slider'),
            postureLabel: document.getElementById('posture-val-label'),
            valProtraction: document.getElementById('val-protraction'),
            valAnteriorTilt: document.getElementById('val-anterior-tilt'),
            valUpwardRot: document.getElementById('val-upward-rot'),
            valRhythmStatus: document.getElementById('val-rhythm-status'),
            valReciprocalScore: document.getElementById('val-reciprocal-score'),

            // Evidence
            evidenceList: document.getElementById('evidence-list')
        };

        this._init();
    }

    async _init() {
        this._bindControls();
        await this._loadCurriculum();
        this._updateBiomechanics(this.postureSeverity);

        if (this.viewer) {
            this.viewer.options.onPoseUpdated = (pose) => this._onPoseUpdated(pose);
            this.viewer.setFpsCallback((fps) => {
                if (this.elements.fpsBadge) {
                    this.elements.fpsBadge.textContent = `${fps} FPS`;
                    this.elements.fpsBadge.className = fps >= 30 ? 'badge badge-green' : 'badge badge-amber';
                }
            });
        }
    }

    onViewerReady() {
        this._renderCurriculum();
        this._renderStage(this.currentStageId);
    }

    _bindControls() {
        // Studio Mode Toggle (P13 baseline vs P14 dynamic)
        if (this.elements.studioModeToggleBtn) {
            this.elements.studioModeToggleBtn.addEventListener('click', () => {
                this.isP14 = !this.isP14;
                this._renderCurriculum();
                this._renderStage(1);
            });
        }

        // Bilingual Toggle
        if (this.elements.langToggleBtn) {
            this.elements.langToggleBtn.addEventListener('click', () => {
                this.currentLang = this.currentLang === 'vi' ? 'en' : 'vi';
                this.elements.langToggleBtn.textContent = this.currentLang === 'vi' ? 'EN / VI' : 'VI / EN';
                this._renderCurriculum();
                this._renderStage(this.currentStageId);
                this._updateBiomechanics(this.postureSeverity);
            });
        }

        // Camera Views
        if (this.elements.viewAnteriorBtn) {
            this.elements.viewAnteriorBtn.addEventListener('click', () => {
                this._setActiveToolbarBtn(this.elements.viewAnteriorBtn);
                if (this.viewer) this.viewer.resetCamera('shoulder');
            });
        }
        if (this.elements.viewPosteriorBtn) {
            this.elements.viewPosteriorBtn.addEventListener('click', () => {
                this._setActiveToolbarBtn(this.elements.viewPosteriorBtn);
                if (this.viewer) this.viewer.resetCamera('posterior');
            });
        }
        if (this.elements.viewLateralBtn) {
            this.elements.viewLateralBtn.addEventListener('click', () => {
                this._setActiveToolbarBtn(this.elements.viewLateralBtn);
                if (this.viewer) this.viewer.resetCamera('lateral');
            });
        }

        // Skeleton Visibility Toggle
        if (this.elements.toggleSkeletonBtn) {
            this.elements.toggleSkeletonBtn.addEventListener('click', () => {
                this.skeletonVisible = !this.skeletonVisible;
                if (this.viewer) this.viewer.setSkeletonVisible(this.skeletonVisible);
                const isVi = this.currentLang === 'vi';
                this.elements.toggleSkeletonBtn.textContent = this.skeletonVisible
                    ? (isVi ? 'Khung Xương: Bật' : 'Skeleton: On')
                    : (isVi ? 'Khung Xương: Tắt' : 'Skeleton: Off');
                this.elements.toggleSkeletonBtn.classList.toggle('active', this.skeletonVisible);
            });
        }

        // Muscle Opacity Slider
        if (this.elements.muscleOpacitySlider) {
            this.elements.muscleOpacitySlider.addEventListener('input', (e) => {
                const val = parseFloat(e.target.value) / 100.0;
                if (this.viewer) this.viewer.setMuscleOpacity(val);
            });
        }

        // Play / Pause Motion Player
        if (this.elements.btnMotionPlay) {
            this.elements.btnMotionPlay.addEventListener('click', () => {
                if (!this.viewer) return;
                const isPlaying = this.viewer.togglePlay();
                const isVi = this.currentLang === 'vi';
                this.elements.btnMotionPlay.textContent = isPlaying
                    ? (isVi ? '⏸ Tạm dừng' : '⏸ Pause')
                    : (isVi ? '▶ Phát' : '▶ Play');
                this.elements.btnMotionPlay.classList.toggle('active', isPlaying);
            });
        }

        // Reset Motion Player
        if (this.elements.btnMotionReset) {
            this.elements.btnMotionReset.addEventListener('click', () => {
                if (this.viewer) {
                    this.viewer.reset();
                    if (this.elements.motionTimeSlider) this.elements.motionTimeSlider.value = 0;
                    if (this.elements.motionTimeLabel) this.elements.motionTimeLabel.textContent = '0.00 s / 2.00 s';
                }
            });
        }

        // Speed Multipliers
        const setSpeed = (spd, activeBtn) => {
            if (this.viewer) this.viewer.setPlaybackSpeed(spd);
            [this.elements.btnSpeed025, this.elements.btnSpeed05, this.elements.btnSpeed1].forEach(b => {
                if (b) b.classList.remove('active');
            });
            if (activeBtn) activeBtn.classList.add('active');
        };
        if (this.elements.btnSpeed025) this.elements.btnSpeed025.addEventListener('click', () => setSpeed(0.25, this.elements.btnSpeed025));
        if (this.elements.btnSpeed05) this.elements.btnSpeed05.addEventListener('click', () => setSpeed(0.5, this.elements.btnSpeed05));
        if (this.elements.btnSpeed1) this.elements.btnSpeed1.addEventListener('click', () => setSpeed(1.0, this.elements.btnSpeed1));

        // Timeline Scrubber
        if (this.elements.motionTimeSlider) {
            this.elements.motionTimeSlider.addEventListener('input', (e) => {
                const frac = parseFloat(e.target.value) / 200.0;
                const t = frac * (this.viewer ? this.viewer.timelineDuration : 2.0);
                if (this.viewer) {
                    this.viewer.seek(t);
                }
            });
        }

        // Scenario Dropdown
        if (this.elements.scenarioSelect) {
            this.elements.scenarioSelect.addEventListener('change', async (e) => {
                const scen = e.target.value;
                if (!this.viewer) return;
                if (scen === 'seth_shoulder_elevation') {
                    await this.viewer.loadMotionData('./data/seth_shoulder_elevation.mot', './data/seth_shoulder_elevation.sto');
                } else if (scen === 'illustrative_rounded_elevation') {
                    await this.viewer.loadMotionData('./data/illustrative_rounded_elevation.mot', null);
                }
            });
        }

        // Visual Mode Selector
        const setMode = (mode, activeBtn) => {
            this.currentMode = mode;
            if (this.viewer) this.viewer.setVisualMode(mode);

            [this.elements.btnModeAnatomy, this.elements.btnModeActivation, this.elements.btnModeComparison].forEach(b => {
                if (b) b.classList.remove('active');
            });
            if (activeBtn) activeBtn.classList.add('active');

            const isVi = this.currentLang === 'vi';
            if (mode === 'ANATOMICAL_FUNCTION') {
                if (this.elements.badgeActivationMode) this.elements.badgeActivationMode.textContent = isVi ? 'Chức Năng' : 'Anatomy';
                if (this.elements.watermarkActivationBanner) {
                    this.elements.watermarkActivationBanner.textContent = 'ANATOMICAL FUNCTION — NOT COMPUTED ACTIVATION';
                    this.elements.watermarkActivationBanner.className = 'watermark-banner';
                }
            } else if (mode === 'MODEL_ESTIMATED') {
                if (this.elements.badgeActivationMode) this.elements.badgeActivationMode.textContent = isVi ? 'Mô Phỏng OpenSim' : 'OpenSim Model';
                if (this.elements.watermarkActivationBanner) {
                    this.elements.watermarkActivationBanner.textContent = 'MATHEMATICAL MODEL ESTIMATE — NOT MEASURED EMG';
                    this.elements.watermarkActivationBanner.className = 'watermark-banner watermark-warning';
                }
            } else if (mode === 'SCENARIO_COMPARISON') {
                if (this.elements.badgeActivationMode) this.elements.badgeActivationMode.textContent = isVi ? 'So Sánh Kịch Bản' : 'Comparison';
                if (this.elements.watermarkActivationBanner) {
                    this.elements.watermarkActivationBanner.textContent = 'ILLUSTRATIVE SCENARIO SIMULATOR (NOT A DIAGNOSIS)';
                    this.elements.watermarkActivationBanner.className = 'watermark-banner';
                }
            }
        };

        if (this.elements.btnModeAnatomy) this.elements.btnModeAnatomy.addEventListener('click', () => setMode('ANATOMICAL_FUNCTION', this.elements.btnModeAnatomy));
        if (this.elements.btnModeActivation) this.elements.btnModeActivation.addEventListener('click', () => setMode('MODEL_ESTIMATED', this.elements.btnModeActivation));
        if (this.elements.btnModeComparison) this.elements.btnModeComparison.addEventListener('click', () => setMode('SCENARIO_COMPARISON', this.elements.btnModeComparison));

        // Posture Severity Slider (Interactive Posture Lab)
        if (this.elements.postureSlider) {
            this.elements.postureSlider.addEventListener('input', (e) => {
                const val = parseFloat(e.target.value);
                this.postureSeverity = val / 100.0;
                this._updateBiomechanics(this.postureSeverity);
            });
        }
    }

    _setActiveToolbarBtn(activeBtn) {
        [this.elements.viewAnteriorBtn, this.elements.viewPosteriorBtn, this.elements.viewLateralBtn].forEach(b => {
            if (b) b.classList.remove('active');
        });
        if (activeBtn) activeBtn.classList.add('active');
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
            console.warn('[ShoulderLab] API fetch fallback to internal catalog:', err);
            this.curriculum = this._getOfflineCurriculumCatalog();
        }
        this._renderCurriculum();
    }

    _renderCurriculum() {
        if (!this.curriculum) return;
        const isVi = this.currentLang === 'vi';

        // Title and Subtitle based on milestone mode
        if (this.isP14) {
            if (this.elements.headerTitle) {
                this.elements.headerTitle.textContent = isVi
                    ? "Điều gì xảy ra khi bạn giơ tay — Và tại sao vai đổ trước vẫn tái phát sau giải cơ?"
                    : "What Happens When You Raise Your Arm — And Why Do Rounded Shoulders Return?";
            }
            if (this.elements.headerSubtitle) {
                this.elements.headerSubtitle.textContent = isVi
                    ? "Cơ sinh học chuyển động xương 3D, Vai trò cơ bắp & Tự chăm sóc dựa trên bằng chứng"
                    : "3D Skeletal Kinematics, Muscle Involvement & Evidence-Informed Active Care";
            }
            if (this.elements.badgeCurriculumVersion) this.elements.badgeCurriculumVersion.textContent = 'P14 Biomechanics';
            if (this.elements.studioModeToggleBtn) this.elements.studioModeToggleBtn.textContent = 'Studio: P14 Biomechanics';
        } else {
            // P13 Baseline titles (required by frozen regression tests)
            if (this.elements.headerTitle) {
                this.elements.headerTitle.textContent = isVi
                    ? "Tại sao giải cơ xong vai nhẹ hơn nhưng một thời gian sau vẫn đổ về trước?"
                    : "Why Do Rounded Shoulders Sometimes Return After Massage?";
            }
            if (this.elements.headerSubtitle) {
                this.elements.headerSubtitle.textContent = isVi
                    ? "MSK-Therapy-OS · 3D Musculoskeletal Education & Biomechanics Studio"
                    : "MSK-Therapy-OS · 3D Musculoskeletal Education & Biomechanics Studio";
            }
            if (this.elements.badgeCurriculumVersion) this.elements.badgeCurriculumVersion.textContent = 'P13 Biomechanics';
            if (this.elements.studioModeToggleBtn) this.elements.studioModeToggleBtn.textContent = 'Studio: P13 Baseline';
        }

        if (this.elements.lblCurriculumHeader) {
            this.elements.lblCurriculumHeader.textContent = isVi ? 'Chương Trình Học (Curriculum)' : 'Curriculum & Lessons';
        }

        const stages = (this.isP14 && this.curriculum.p14_stages) ? this.curriculum.p14_stages : this.curriculum.stages;
        if (!this.elements.stageList || !stages) return;

        if (this.elements.stageListHeader) {
            this.elements.stageListHeader.textContent = isVi
                ? `Các Giai Đoạn Phân Tích (${stages.length} ${stages.length === 6 ? 'Modules' : 'Stages'})`
                : `Analytical Modules (${stages.length} ${stages.length === 6 ? 'Modules' : 'Stages'})`;
        }

        this.elements.stageList.innerHTML = '';
        stages.forEach((stage) => {
            const item = document.createElement('div');
            item.className = `stage-nav-item ${stage.stage_id === this.currentStageId ? 'active' : ''}`;
            item.dataset.stageId = stage.stage_id;
            item.innerHTML = `
                <div class="stage-nav-num">${stage.stage_id}</div>
                <div class="stage-nav-title">${isVi ? stage.name_vi : stage.name_en}</div>
            `;
            item.addEventListener('click', () => {
                this.currentStageId = stage.stage_id;
                this._renderStage(stage.stage_id);
                document.querySelectorAll('.stage-nav-item').forEach(el => el.classList.remove('active'));
                item.classList.add('active');
            });
            this.elements.stageList.appendChild(item);
        });

        // Always render evidence items into #evidence-list so regression test finds .evidence-item
        this._renderEvidenceList();
    }

    _renderEvidenceList() {
        if (!this.elements.evidenceList || !this.curriculum || !this.curriculum.evidence_register) return;
        this.elements.evidenceList.innerHTML = '';

        this.curriculum.evidence_register.forEach((ev) => {
            const li = document.createElement('li');
            li.className = 'evidence-item';
            li.innerHTML = `
                <div><span class="evidence-tag">[${ev.evidence_id || ev.id}]</span> <span style="font-weight:600; color:#e2e8f0;">${ev.title || ev.topic}</span></div>
                <div class="evidence-desc">${ev.citation || ev.authors} (${ev.publication_year || '1944'})</div>
            `;
            this.elements.evidenceList.appendChild(li);
        });
    }

    _renderStage(stageId) {
        if (!this.curriculum) return;
        const stages = (this.isP14 && this.curriculum.p14_stages) ? this.curriculum.p14_stages : this.curriculum.stages;
        const stage = stages.find(s => s.stage_id === stageId) || stages[0];
        if (!stage) return;

        const isVi = this.currentLang === 'vi';
        const name = isVi ? stage.name_vi : stage.name_en;
        const prefix = name.trim().startsWith(`${stage.stage_id}.`) ? '' : `${stage.stage_id}. `;
        if (this.elements.stageTitle) {
            this.elements.stageTitle.textContent = `${prefix}${name}`;
        }
        if (this.elements.stageSummary) {
            this.elements.stageSummary.textContent = isVi ? stage.summary_vi : stage.summary_en;
        }

        // Highlight focus muscles in Anatomical Function mode
        if (this.viewer && stage.focus_muscles && this.currentMode === 'ANATOMICAL_FUNCTION') {
            this.viewer.highlightMuscles(stage.focus_muscles);
        }

        // Update active class on stage nav items
        if (this.elements.stageList) {
            this.elements.stageList.querySelectorAll('.stage-nav-item').forEach(el => {
                el.classList.toggle('active', el.dataset.stageId == stageId);
            });
        }

        // If P14 Stage 7 (Quiz) or Stage 8 (Evidence)
        if (this.isP14 && stageId === 7) {
            this._renderQuizWidget();
        } else if (this.isP14 && stageId === 8) {
            this._renderEvidenceRegisterWidget();
        } else {
            if (this.elements.stageDynamicBody) {
                this.elements.stageDynamicBody.style.display = 'none';
                this.elements.stageDynamicBody.innerHTML = '';
            }
        }
    }

    _renderQuizWidget() {
        if (!this.curriculum || !this.curriculum.quiz || !this.elements.stageDynamicBody) return;
        const isVi = this.currentLang === 'vi';

        const quizContainer = document.createElement('div');
        quizContainer.className = 'quiz-container';

        this.curriculum.quiz.forEach((q, idx) => {
            const card = document.createElement('div');
            card.className = 'quiz-card';
            card.innerHTML = `
                <div class="quiz-q-title">${idx + 1}. ${isVi ? q.question_vi : q.question_en}</div>
                <div class="quiz-options-group" id="quiz-opts-${q.question_id}"></div>
                <div class="quiz-explanation" id="quiz-exp-${q.question_id}">
                    <strong>${isVi ? 'Giải thích khoa học:' : 'Scientific Rationale:'}</strong>
                    ${isVi ? q.explanation_vi : q.explanation_en}
                </div>
            `;

            const optsGroup = card.querySelector(`#quiz-opts-${q.question_id}`);
            const expBox = card.querySelector(`#quiz-exp-${q.question_id}`);
            const options = isVi ? q.options_vi : q.options_en;

            options.forEach((optText, oIdx) => {
                const optKey = ['A', 'B', 'C'][oIdx];
                const optBtn = document.createElement('div');
                optBtn.className = 'quiz-option';
                optBtn.textContent = optText;

                if (this.quizAnswers[q.question_id] === optKey) {
                    optBtn.classList.add(optKey === q.correct_option ? 'correct' : 'incorrect');
                    expBox.style.display = 'block';
                }

                optBtn.addEventListener('click', () => {
                    this.quizAnswers[q.question_id] = optKey;
                    optsGroup.querySelectorAll('.quiz-option').forEach(el => {
                        el.classList.remove('correct', 'incorrect');
                    });

                    if (optKey === q.correct_option) {
                        optBtn.classList.add('correct');
                    } else {
                        optBtn.classList.add('incorrect');
                        const correctEl = optsGroup.children[['A', 'B', 'C'].indexOf(q.correct_option)];
                        if (correctEl) correctEl.classList.add('correct');
                    }
                    expBox.style.display = 'block';
                });

                optsGroup.appendChild(optBtn);
            });

            quizContainer.appendChild(card);
        });

        this.elements.stageDynamicBody.innerHTML = '';
        this.elements.stageDynamicBody.style.display = 'block';
        this.elements.stageDynamicBody.appendChild(quizContainer);
    }

    _renderEvidenceRegisterWidget() {
        if (!this.curriculum || !this.curriculum.evidence_register || !this.elements.stageDynamicBody) return;
        const isVi = this.currentLang === 'vi';

        const evContainer = document.createElement('div');
        evContainer.style.display = 'flex';
        evContainer.style.flexDirection = 'column';
        evContainer.style.gap = '8px';

        this.curriculum.evidence_register.forEach((ev) => {
            const card = document.createElement('div');
            card.className = 'card';
            card.style.fontSize = '11px';
            card.innerHTML = `
                <div style="font-weight: 700; color: var(--accent); margin-bottom: 2px;">
                    [${ev.evidence_id || ev.id}] ${ev.title || ev.topic}
                </div>
                <div style="color: #94a3b8; font-size: 10px; margin-bottom: 4px;">
                    ${ev.authors} (${ev.publication_year}) · ${ev.doi_or_url}
                </div>
                <div style="color: #e2e8f0; font-size: 10.5px; line-height: 1.35; margin-bottom: 4px;">
                    <strong>${isVi ? 'Bằng chứng hỗ trợ:' : 'Claims Supported:'}</strong> ${ev.claims_supported || ev.topic}
                </div>
                <div style="color: #fbbf24; font-size: 10px; line-height: 1.35;">
                    <strong>${isVi ? 'Giới hạn phương pháp:' : 'Methodological Limitation:'}</strong> ${ev.limitations}
                </div>
            `;
            evContainer.appendChild(card);
        });

        this.elements.stageDynamicBody.innerHTML = '';
        this.elements.stageDynamicBody.style.display = 'block';
        this.elements.stageDynamicBody.appendChild(evContainer);
    }

    _updateBiomechanics(severity) {
        // Compute illustrative posture metrics
        const protraction = (15.0 + severity * 28.0).toFixed(1);
        const anteriorTilt = (8.0 + severity * 25.0).toFixed(1);
        const upwardRot = (22.0 - severity * 23.0).toFixed(1);

        // Compute illustrative rhythm ratio: (120 GH) / (upwardRot ST)
        const ghAngle = 60.0;
        const stAngle = Math.max(1.0, 30.0 - severity * 18.0);
        const rhythm = (ghAngle / stAngle).toFixed(2);
        const reciprocalScore = Math.max(5, Math.round(100 - severity * 75));

        if (this.elements.postureLabel) this.elements.postureLabel.textContent = `${Math.round(severity * 100)}%`;
        if (this.elements.valProtraction) this.elements.valProtraction.textContent = `${protraction}°`;
        if (this.elements.valAnteriorTilt) this.elements.valAnteriorTilt.textContent = `${anteriorTilt}°`;
        if (this.elements.valUpwardRot) this.elements.valUpwardRot.textContent = `${upwardRot}°`;
        if (this.elements.valRhythmRatio) this.elements.valRhythmRatio.textContent = `${rhythm} : 1`;
        if (this.elements.valReciprocalScore) this.elements.valReciprocalScore.textContent = `${reciprocalScore}/100`;

        if (this.elements.valRhythmStatus) {
            const isVi = this.currentLang === 'vi';
            if (severity < 0.35) {
                this.elements.valRhythmStatus.textContent = isVi ? 'Cân Bằng Sinh Lý' : 'Physiological 2:1';
                this.elements.valRhythmStatus.className = 'badge badge-green';
            } else if (severity < 0.70) {
                this.elements.valRhythmStatus.textContent = isVi ? 'Giảm Xoay Lên' : 'Reduced Upward Rot';
                this.elements.valRhythmStatus.className = 'badge badge-amber';
            } else {
                this.elements.valRhythmStatus.textContent = isVi ? 'Hạn Chế Bả Vai' : 'Marked Hypomobility';
                this.elements.valRhythmStatus.className = 'badge badge-red';
            }
        }
    }

    _onPoseUpdated(pose) {
        if (!pose) return;

        // 1. Timeline Scrubber & Readout
        if (this.elements.motionTimeSlider) {
            const sliderVal = Math.round((pose.time / (pose.duration || 2.0)) * 200.0);
            this.elements.motionTimeSlider.value = sliderVal;
        }
        if (this.elements.motionTimeLabel) {
            this.elements.motionTimeLabel.textContent = `${pose.time.toFixed(2)} s / ${(pose.duration || 2.0).toFixed(2)} s`;
        }

        // 2. Kinematic Angles
        if (this.elements.dynArmElev) this.elements.dynArmElev.textContent = `${pose.armElevation.toFixed(1)}°`;
        if (this.elements.dynScapUp) this.elements.dynScapUp.textContent = `${pose.scapUpwardRot.toFixed(1)}°`;
        if (this.elements.dynScapTilt) this.elements.dynScapTilt.textContent = `${pose.scapTilt.toFixed(1)}°`;
        if (this.elements.dynClavElev) this.elements.dynClavElev.textContent = `${pose.clavElev.toFixed(1)}°`;

        // 3. Dynamic Scapulohumeral Rhythm
        if (this.elements.dynRhythmRatio) {
            const ratio = pose.scapUpwardRot > 0.5 ? (pose.armElevation / pose.scapUpwardRot).toFixed(2) : '2.00';
            this.elements.dynRhythmRatio.textContent = `${ratio} : 1`;
        }

        // 4. Muscle Activations
        const acts = pose.muscleActivations || {};
        const updateBar = (valEl, barEl, actVal) => {
            if (actVal !== undefined && actVal !== null && !isNaN(actVal)) {
                const pct = Math.round(actVal * 100);
                if (valEl) valEl.textContent = `${pct}%`;
                if (barEl) barEl.style.width = `${pct}%`;
            } else {
                if (valEl) valEl.textContent = this.currentLang === 'vi' ? 'CHƯA CÓ TRONG MÔ HÌNH' : 'DATA UNAVAILABLE';
                if (barEl) barEl.style.width = '0%';
            }
        };

        const getAct = (k1, k2) => {
            if (acts[k1] !== undefined) return acts[k1];
            if (acts[k2] !== undefined) return acts[k2];
            return undefined;
        };

        updateBar(this.elements.valActDeltoidLateral, this.elements.barActDeltoidLateral, getAct('deltoid_lateral', 'delt_l'));
        updateBar(this.elements.valActSupraspinatus, this.elements.barActSupraspinatus, getAct('supraspinatus', 'supra'));
        updateBar(this.elements.valActSerratus, this.elements.barActSerratus, getAct('serratus_anterior', 'serratus_l'));
        updateBar(this.elements.valActTrapeziusLower, this.elements.barActTrapeziusLower, getAct('trapezius_lower', 'trap_l'));
        updateBar(this.elements.valActPecMinor, this.elements.barActPecMinor, getAct('pectoralis_minor', 'pec_minor'));
        updateBar(this.elements.valActRhomboid, this.elements.barActRhomboid, getAct('rhomboid_major', 'rhomboid'));
    }

    _getOfflineCurriculumCatalog() {
        return {
            title_en: "Why Do Rounded Shoulders Sometimes Return After Massage?",
            title_vi: "Tại sao giải cơ xong vai nhẹ hơn nhưng một thời gian sau vẫn đổ về trước?",
            stages: [
                {
                    stage_id: 1,
                    name_en: "The Core Paradox: Transient Relief vs. Postural Recurrence",
                    name_vi: "Nghịch lý cốt lõi: Nhẹ cơ tức thời vs. Tái phát tư thế",
                    summary_en: "Manual massage reduces local tone transiently, but does not re-educate prolonged habitual motor patterns.",
                    summary_vi: "Giải cơ bằng tay kích thích thụ thể cơ học giúp giảm trương lực và tăng tưới máu tạm thời, nhưng chưa tái lập thói quen vận động thần kinh hay phục hồi cân bằng cơ đối vận.",
                    focus_muscles: ["pectoralis_minor", "trapezius_upper"]
                },
                {
                    stage_id: 2,
                    name_en: "Anterior Shortening: Pectoralis Minor & Major",
                    name_vi: "Sự co ngắn nhóm cơ phía trước: Cơ ngực bé & Cơ ngực lớn",
                    summary_en: "Desk posture holds the pectoralis minor in a shortened state.",
                    summary_vi: "Tư thế ngồi máy tính kéo dài làm cơ ngực bé co ngắn kinh niên, kéo mỏm quạ xương bả vai chúc về phía trước.",
                    focus_muscles: ["pectoralis_minor", "pectoralis_major"]
                },
                {
                    stage_id: 3,
                    name_en: "Posterior Inhibition: Serratus Anterior & Lower Trapezius",
                    name_vi: "Sự ức chế nhóm cơ phía sau: Cơ răng trước & Cơ thang dưới",
                    summary_en: "Reciprocal inhibition leads to functional weakness of the lower trapezius and serratus anterior.",
                    summary_vi: "Hiện tượng ức chế tương hỗ và căng giãn kéo dài làm yếu chức năng cơ thang dưới và cơ răng trước.",
                    focus_muscles: ["serratus_anterior", "trapezius_lower"]
                },
                {
                    stage_id: 4,
                    name_en: "Scapulohumeral Rhythm & Subacromial Space",
                    name_vi: "Nhịp sinh học bả vai - cánh tay & Khoang dưới mỏm cùng vai",
                    summary_en: "During elevation, a healthy shoulder maintains a 2:1 ratio.",
                    summary_vi: "Khi giơ tay, vai duy trì nhịp bả vai - cánh tay. Vai đổ trước làm giảm xoay lên, hẹp khoang dưới mỏm cùng vai.",
                    focus_muscles: ["deltoid_lateral", "supraspinatus"]
                },
                {
                    stage_id: 5,
                    name_en: "Neural Adaptation & Habitual Proprioception",
                    name_vi: "Thích nghi thần kinh & Cảm thụ bản thể theo thói quen",
                    summary_en: "The brain postural schema interprets protracted shoulder as normal neutral.",
                    summary_vi: "Hệ thần kinh thích nghi với tư thế ngồi quen thuộc và định nghĩa vai đổ trước là trạng thái bình thường.",
                    focus_muscles: ["trapezius_middle", "latissimus_dorsi"]
                },
                {
                    stage_id: 6,
                    name_en: "The Integrative Solution: Release + Activate + Ergonomics",
                    name_vi: "Giải pháp tích hợp: Thả lỏng + Kích hoạt + Công thái học",
                    summary_en: "Tripartite approach: Myofascial release, active strengthening, and workplace ergonomics.",
                    summary_vi: "Kiềng 3 chân: Giải phóng mạc cơ co ngắn, kích hoạt cơ lưng bả vai, và điều chỉnh công thái học.",
                    focus_muscles: ["pectoralis_minor", "serratus_anterior", "trapezius_lower"]
                }
            ],
            evidence_register: [
                {
                    id: "EV-01",
                    evidence_id: "EV-01",
                    title: "Observations on the function of the shoulder joint",
                    authors: "Inman VT, Saunders JB, Abbott LC",
                    publication_year: 1944,
                    doi_or_url: "https://doi.org/10.2106/00004623-194426010-00001",
                    claims_supported: "Foundational description of the 2:1 scapulohumeral rhythm.",
                    limitations: "Planar historical benchmark; does not represent universal normal range across all phases."
                },
                {
                    id: "EV-02",
                    evidence_id: "EV-02",
                    title: "Alterations in shoulder kinematics in impingement",
                    authors: "Ludewig PM, Cook TM",
                    publication_year: 2000,
                    doi_or_url: "https://doi.org/10.1093/ptj/80.3.276",
                    claims_supported: "Significant variability in scapular upward rotation.",
                    limitations: "Cross-sectional; does not prove causality."
                },
                {
                    id: "EV-03",
                    evidence_id: "EV-03",
                    title: "Pectoralis minor resting length and scapular kinematics",
                    authors: "Borstad JD, Ludewig PM",
                    publication_year: 2005,
                    doi_or_url: "https://doi.org/10.2519/jospt.2005.35.4.227",
                    claims_supported: "Shortened pectoralis minor length correlates with anterior tilt.",
                    limitations: "Healthy cohort without pathology."
                }
            ]
        };
    }
}
