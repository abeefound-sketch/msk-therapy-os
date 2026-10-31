/**
 * MSK-Therapy-OS - 3D Musculoskeletal Education & Biomechanics Viewer
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
 * 
 * Hardware optimized for Intel Core i7-5600U / Intel HD Graphics 5500.
 * Licensing:
 * - Code: MIT License
 * - Muscular Geometry (anatomy.glb): CC BY-SA 2.1 JP (BodyParts3D via DBCLS & Z-Anatomy)
 * - Skeletal Geometry (shoulder_skeleton.glb): CC BY-SA 2.1 JP / CC BY 4.0 (BodyParts3D v4.0)
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export class AnatomyViewer {
    constructor(canvasContainerId, options = {}) {
        this.container = document.getElementById(canvasContainerId);
        if (!this.container) {
            throw new Error(`Container #${canvasContainerId} not found`);
        }

        this.options = Object.assign({
            musclesUrl: './models/anatomy.glb',
            skeletonUrl: './models/cervicothoracic_skeleton.glb',
            onMeshSelected: null,
            onLoadProgress: null,
            onLoadComplete: null,
            onError: null,
            onPoseUpdated: null
        }, options);

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;

        // Model Roots
        this.muscleRoot = null;
        this.skeletonRoot = null;
        this.meshes = new Map(); // name -> THREE.Mesh
        this.materials = new Map(); // name -> original THREE.Material

        // Anatomical Joint Pivot Nodes (Hierarchical Kinematic Chain)
        // BodyParts3D Coordinate Frame (meters, Y-up, Right shoulder in -X)
        this.jointCenters = {
            sc: new THREE.Vector3(-0.018, 1.405, 0.038),   // Sternoclavicular joint
            ac: new THREE.Vector3(-0.142, 1.415, -0.025),  // Acromioclavicular joint
            gh: new THREE.Vector3(-0.165, 1.395, -0.020),  // Glenohumeral joint center
            c7t1: new THREE.Vector3(-0.001, 1.448, -0.046), // C7-T1 Cervicothoracic junction
            aa: new THREE.Vector3(-0.001, 1.542, -0.037),   // Atlanto-axial (C1-C2) pivot
            ao: new THREE.Vector3(-0.001, 1.556, -0.036)    // Atlanto-occipital (Occiput) pivot
        };

        this.pivots = {
            sc: new THREE.Group(),
            ac: new THREE.Group(),
            gh: new THREE.Group(),
            c7t1: new THREE.Group(),
            aa: new THREE.Group(),
            ao: new THREE.Group()
        };

        this.bones = {
            thorax: null,
            clavicle: null,
            scapula: null,
            humerus: null,
            cervicalLower: null,
            cervicalUpper: null,
            skull: null,
            levator: null,
            suboccipital: null
        };

        // Kinematic Motion Player State
        this.motionData = null;       // Parsed .mot file
        this.muscleData = null;       // Parsed .sto file
        this.currentTime = 0.0;
        this.timelineDuration = 2.0;  // seconds
        this.isPlaying = false;
        this.playbackSpeed = 1.0;
        this.activeScenarioId = 'seth_shoulder_elevation';
        this.currentMode = 'ANATOMICAL_FUNCTION'; // 'ANATOMICAL_FUNCTION', 'MODEL_ESTIMATED', 'SCENARIO_COMPARISON'

        // Interaction
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2(-999, -999);
        this.hoveredMesh = null;
        this.selectedMeshName = null;

        // Performance & Animation Loop
        this.isAnimating = false;
        this.animationFrameId = null;
        this.lastFrameTime = performance.now();
        this.frameCount = 0;
        this.fps = 60;
        this.fpsCallback = null;

        // Palettes
        this.colors = {
            muscleDefault: 0xb55a5a,
            muscleHighlighted: 0x38bdf8,
            muscleInhibited: 0x94a3b8,
            muscleHypertonic: 0xf43f5e,
            boneDefault: 0xd8d0c5,
            boneHighlighted: 0xfde047,
            activationLow: 0x3b82f6,
            activationMid: 0xeab308,
            activationHigh: 0xef4444
        };

        this._initScene();
        this._bindEvents();
    }

    _initScene() {
        const width = this.container.clientWidth || 800;
        const height = this.container.clientHeight || 600;

        // 1. Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a101d);

        // 2. Camera
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.05, 50.0);
        this.camera.position.set(-0.25, 1.48, 1.05); // Focused on Right shoulder complex

        // 3. WebGL Renderer
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            powerPreference: 'default', // Intel HD 5500 friendly
            alpha: false
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.container.appendChild(this.renderer.domElement);

        // 4. Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.90);
        this.scene.add(ambientLight);

        const dirLightFront = new THREE.DirectionalLight(0xffffff, 1.3);
        dirLightFront.position.set(1.5, 3.0, 2.0);
        this.scene.add(dirLightFront);

        const dirLightBack = new THREE.DirectionalLight(0x90b0e0, 0.7);
        dirLightBack.position.set(-1.5, 2.0, -2.0);
        this.scene.add(dirLightBack);

        // 5. OrbitControls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.08;
        this.controls.target.set(-0.10, 1.38, -0.02); // Right shoulder center
        this.controls.minDistance = 0.25;
        this.controls.maxDistance = 3.5;
        this.controls.update();

        // 6. Kinematic Scene Graph Hierarchy
        this._buildKinematicHierarchy();
    }

    _buildKinematicHierarchy() {
        this.skeletonRoot = new THREE.Group();
        this.skeletonRoot.name = 'KinematicSkeletonRoot';
        this.scene.add(this.skeletonRoot);

        // SC Pivot: Sternoclavicular joint center
        this.pivots.sc.name = 'SternoclavicularPivot';
        this.pivots.sc.position.copy(this.jointCenters.sc);
        this.skeletonRoot.add(this.pivots.sc);

        // AC Pivot: Acromioclavicular joint relative to SC
        const acRel = new THREE.Vector3().subVectors(this.jointCenters.ac, this.jointCenters.sc);
        this.pivots.ac.name = 'AcromioclavicularPivot';
        this.pivots.ac.position.copy(acRel);
        this.pivots.sc.add(this.pivots.ac);

        // GH Pivot: Glenohumeral joint relative to AC
        const ghRel = new THREE.Vector3().subVectors(this.jointCenters.gh, this.jointCenters.ac);
        this.pivots.gh.name = 'GlenohumeralPivot';
        this.pivots.gh.position.copy(ghRel);
        this.pivots.ac.add(this.pivots.gh);

        // C7-T1 Pivot: Base of neck attached to SkeletonRoot
        this.pivots.c7t1.name = 'CervicothoracicPivot_C7T1';
        this.pivots.c7t1.position.copy(this.jointCenters.c7t1);
        this.skeletonRoot.add(this.pivots.c7t1);

        // Atlanto-Axial Pivot (C1-C2) relative to C7-T1
        const aaRel = new THREE.Vector3().subVectors(this.jointCenters.aa, this.jointCenters.c7t1);
        this.pivots.aa.name = 'AtlantoAxialPivot';
        this.pivots.aa.position.copy(aaRel);
        this.pivots.c7t1.add(this.pivots.aa);

        // Atlanto-Occipital Pivot relative to C1-C2
        const aoRel = new THREE.Vector3().subVectors(this.jointCenters.ao, this.jointCenters.aa);
        this.pivots.ao.name = 'AtlantoOccipitalPivot';
        this.pivots.ao.position.copy(aoRel);
        this.pivots.aa.add(this.pivots.ao);
    }

    _bindEvents() {
        window.addEventListener('resize', () => this._onResize());

        const canvas = this.renderer.domElement;
        canvas.addEventListener('mousemove', (e) => this._onMouseMove(e));
        canvas.addEventListener('click', (e) => this._onClick(e));

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAnimation();
            } else {
                this.startAnimation();
            }
        });
    }

    _onResize() {
        if (!this.container || !this.renderer || !this.camera) return;
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        if (width === 0 || height === 0) return;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    _onMouseMove(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    }

    _onClick(event) {
        if (this.hoveredMesh) {
            const meshName = this.hoveredMesh.name;
            this.selectMuscle(meshName);
            if (typeof this.options.onMeshSelected === 'function') {
                this.options.onMeshSelected(meshName);
            }
        }
    }

    /**
     * Load both shoulder skeleton and muscular geometry asynchronously.
     */
    async loadModel() {
        const loader = new GLTFLoader();

        if (typeof this.options.onLoadProgress === 'function') {
            this.options.onLoadProgress(15, 'Loading osseous skeleton (shoulder_skeleton.glb)...');
        }

        try {
            // 1. Load Osseous Skeleton
            await new Promise((resolve, reject) => {
                loader.load(
                    this.options.skeletonUrl,
                    (gltf) => {
                        this._setupSkeleton(gltf.scene);
                        resolve();
                    },
                    undefined,
                    (err) => {
                        console.warn('[AnatomyViewer] Skeleton load failed, continuing with muscles:', err);
                        resolve(); // Non-fatal fallback
                    }
                );
            });

            if (typeof this.options.onLoadProgress === 'function') {
                this.options.onLoadProgress(50, 'Loading muscular geometry (anatomy.glb)...');
            }

            // 2. Load Muscle Anatomy
            await new Promise((resolve, reject) => {
                loader.load(
                    this.options.musclesUrl,
                    (gltf) => {
                        this.muscleRoot = gltf.scene;
                        this.muscleRoot.traverse((child) => {
                            if (child.isMesh) {
                                if (!child.geometry.attributes.normal) {
                                    child.geometry.computeVertexNormals();
                                }
                                const originalMat = child.material.clone();
                                originalMat.roughness = 0.55;
                                originalMat.metalness = 0.10;
                                originalMat.transparent = true;
                                originalMat.opacity = 0.65; // Semi-transparent by default to show skeleton inside
                                child.material = originalMat;

                                const name = child.name || child.id.toString();
                                this.meshes.set(name, child);
                                this.materials.set(name, originalMat);
                            }
                        });
                        this.scene.add(this.muscleRoot);
                        resolve();
                    },
                    (xhr) => {
                        if (xhr.total && xhr.total > 0) {
                            const pct = 50 + Math.round((xhr.loaded / xhr.total) * 45);
                            if (typeof this.options.onLoadProgress === 'function') {
                                this.options.onLoadProgress(pct, `Loading muscles (${pct}%)...`);
                            }
                        }
                    },
                    (err) => reject(err)
                );
            });

            // 3. Load default OpenSim elevation motion & muscle activation
            await this.loadMotionData('./data/seth_shoulder_elevation.mot', './data/seth_shoulder_elevation.sto');

            if (typeof this.options.onLoadComplete === 'function') {
                this.options.onLoadComplete({
                    meshCount: this.meshes.size,
                    hasSkeleton: !!this.bones.scapula
                });
            }

            this.startAnimation();
        } catch (error) {
            console.error('[AnatomyViewer] Load Error:', error);
            if (typeof this.options.onError === 'function') {
                this.options.onError(error);
            }
        }
    }

    _setupSkeleton(scene) {
        const boneMat = new THREE.MeshStandardMaterial({
            color: this.colors.boneDefault,
            roughness: 0.65,
            metalness: 0.05
        });

        scene.traverse((child) => {
            if (child.isMesh) {
                const name = child.name;
                if (child.material && child.material.name === 'LevatorMaterial') {
                    child.material = new THREE.MeshStandardMaterial({
                        color: 0xd97768, // terracotta muscle
                        roughness: 0.65,
                        metalness: 0.05
                    });
                } else if (child.material && child.material.name === 'SuboccipitalMaterial') {
                    child.material = new THREE.MeshStandardMaterial({
                        color: 0xc44536, // deep ruby muscle
                        roughness: 0.65,
                        metalness: 0.05
                    });
                } else {
                    child.material = boneMat.clone();
                }

                if (name === 'Thorax') {
                    this.bones.thorax = child;
                    this.skeletonRoot.add(child);
                } else if (name === 'Clavicle_R') {
                    this.bones.clavicle = child;
                    child.position.set(-this.jointCenters.sc.x, -this.jointCenters.sc.y, -this.jointCenters.sc.z);
                    this.pivots.sc.add(child);
                } else if (name === 'Scapula_R') {
                    this.bones.scapula = child;
                    child.position.set(-this.jointCenters.ac.x, -this.jointCenters.ac.y, -this.jointCenters.ac.z);
                    this.pivots.ac.add(child);
                } else if (name === 'Humerus_R') {
                    this.bones.humerus = child;
                    child.position.set(-this.jointCenters.gh.x, -this.jointCenters.gh.y, -this.jointCenters.gh.z);
                    this.pivots.gh.add(child);
                } else if (name === 'Cervical_Lower') {
                    this.bones.cervicalLower = child;
                    child.position.set(-this.jointCenters.c7t1.x, -this.jointCenters.c7t1.y, -this.jointCenters.c7t1.z);
                    this.pivots.c7t1.add(child);
                } else if (name === 'Cervical_Upper') {
                    this.bones.cervicalUpper = child;
                    child.position.set(-this.jointCenters.aa.x, -this.jointCenters.aa.y, -this.jointCenters.aa.z);
                    this.pivots.aa.add(child);
                } else if (name === 'Skull_Cranium') {
                    this.bones.skull = child;
                    child.position.set(-this.jointCenters.ao.x, -this.jointCenters.ao.y, -this.jointCenters.ao.z);
                    this.pivots.ao.add(child);
                } else if (name === 'Levator_Scapulae') {
                    this.bones.levator = child;
                    this.skeletonRoot.add(child);
                } else if (name === 'Suboccipital_Muscles') {
                    this.bones.suboccipital = child;
                    child.position.set(-this.jointCenters.ao.x, -this.jointCenters.ao.y, -this.jointCenters.ao.z);
                    this.pivots.ao.add(child);
                }
                this.meshes.set(name, child);
            }
        });
    }

    /**
     * Strict OpenSim Text Parser in JavaScript
     * Validates size, headers, monotonic timestamps, and finite floats.
     */
    static parseOpenSimText(content, filename = 'motion.mot') {
        if (!content || typeof content !== 'string') {
            throw new Error('OpenSim motion data is empty or invalid');
        }
        if (content.length > 10 * 1024 * 1024) {
            throw new Error('OpenSim file exceeds 10MB limit');
        }

        const lines = content.split(/\r?\n/).map(l => l.trim());
        let headerLineIdx = -1;
        let inDegrees = true;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (line.toLowerCase().startsWith('indegrees=')) {
                inDegrees = line.split('=')[1].trim().toLowerCase() === 'yes';
            }
            if (line.toLowerCase() === 'endheader') {
                headerLineIdx = i + 1;
                break;
            }
        }

        if (headerLineIdx === -1 || headerLineIdx >= lines.length) {
            throw new Error(`OpenSim file '${filename}' missing 'endheader' token`);
        }

        const headers = lines[headerLineIdx].split(/\s+/).filter(Boolean);
        if (headers.length === 0 || headers[0].toLowerCase() !== 'time') {
            throw new Error(`First column must be 'time', found '${headers[0] || 'None'}'`);
        }

        // Duplicate column check
        const seen = new Set();
        for (const h of headers) {
            if (seen.has(h)) throw new Error(`Duplicate column '${h}' in OpenSim file`);
            seen.add(h);
        }

        const times = [];
        const data = {};
        headers.forEach(h => data[h] = []);

        let lastTime = -Infinity;
        for (let i = headerLineIdx + 1; i < lines.length; i++) {
            const line = lines[i];
            if (!line || line.startsWith('#')) continue;
            const parts = line.split(/\s+/).filter(Boolean);
            if (parts.length < headers.length) continue;

            const t = parseFloat(parts[0]);
            if (isNaN(t) || !isFinite(t)) throw new Error(`Non-finite time at line ${i + 1}`);
            if (t < lastTime) throw new Error(`Time must be strictly monotonic at line ${i + 1}`);
            lastTime = t;
            times.push(t);

            for (let c = 0; c < headers.length; c++) {
                const val = parseFloat(parts[c]);
                if (isNaN(val) || !isFinite(val)) throw new Error(`Non-finite float in column '${headers[c]}' line ${i + 1}`);
                data[headers[c]].push(val);
            }
        }

        return {
            filename,
            inDegrees,
            headers,
            times,
            data,
            duration: times.length > 0 ? times[times.length - 1] - times[0] : 0.0
        };
    }

    async loadMotionData(motUrl, stoUrl = null) {
        try {
            const motResp = await fetch(motUrl);
            if (motResp.ok) {
                const text = await motResp.text();
                this.motionData = AnatomyViewer.parseOpenSimText(text, motUrl);
                this.timelineDuration = this.motionData.duration || 2.0;
            }

            if (stoUrl) {
                const stoResp = await fetch(stoUrl);
                if (stoResp.ok) {
                    const text = await stoResp.text();
                    this.muscleData = AnatomyViewer.parseOpenSimText(text, stoUrl);
                } else {
                    this.muscleData = null;
                }
            } else {
                this.muscleData = null;
            }

            this.seek(0.0);
        } catch (err) {
            console.warn('[AnatomyViewer] Motion data fetch/parse failed:', err);
        }
    }

    /**
     * Interpolate coordinate channel at time t.
     */
    _interpolateChannel(times, values, t) {
        if (!times || times.length === 0) return 0.0;
        if (t <= times[0]) return values[0];
        if (t >= times[times.length - 1]) return values[values.length - 1];

        // Binary search for bracket
        let low = 0;
        let high = times.length - 1;
        while (low <= high) {
            const mid = Math.floor((low + high) / 2);
            if (times[mid] === t) return values[mid];
            if (times[mid] < t) low = mid + 1;
            else high = mid - 1;
        }

        const idx0 = Math.max(0, high);
        const idx1 = Math.min(times.length - 1, low);
        if (idx0 === idx1) return values[idx0];

        const dt = times[idx1] - times[idx0];
        const alpha = (t - times[idx0]) / dt;
        return values[idx0] + alpha * (values[idx1] - values[idx0]);
    }

    /**
     * Set the current kinematic time and update all skeletal pivot transformations.
     */
    seek(t) {
        this.currentTime = Math.max(0.0, Math.min(t, this.timelineDuration));
        if (!this.motionData) return;

        const md = this.motionData;
        const getVal = (col) => {
            if (!md.data[col]) return 0.0;
            return this._interpolateChannel(md.times, md.data[col], this.currentTime);
        };

        // Extract coordinate angles (degrees)
        const armElevation = getVal('arm_elevation') || getVal('r_shoulder_elev');
        const scapUpwardRot = getVal('scapula_upward_rot');
        const scapTilt = getVal('scapula_anterior_tilt') || getVal('scapula_posterior_tilt');
        const scapProt = getVal('scapula_internal_rot') || getVal('scapula_protraction');
        const clavElev = getVal('clavicle_elev') || getVal('clavicle_elevation');
        const clavRetract = getVal('clavicle_retraction');
        const armRot = getVal('arm_rot') || 0.0;

        // Relative Glenohumeral elevation = Total Arm Elevation - Scapular Upward Rotation
        const ghElev = Math.max(0.0, armElevation - scapUpwardRot);

        // 1. Clavicle (SC Pivot) Transformations
        // Elevation rotates around +Z (clockwise for Right shoulder in -X)
        this.pivots.sc.rotation.z = -THREE.MathUtils.degToRad(clavElev);
        this.pivots.sc.rotation.y = -THREE.MathUtils.degToRad(clavRetract * 0.5);

        // 2. Scapula (AC Pivot) Transformations
        // Upward rotation around +Z (clockwise for Right shoulder in -X)
        this.pivots.ac.rotation.z = -THREE.MathUtils.degToRad(scapUpwardRot);
        // Anterior (+) / Posterior (-) tilt around X
        this.pivots.ac.rotation.x = THREE.MathUtils.degToRad(scapTilt);
        // Internal rotation / protraction around Y
        this.pivots.ac.rotation.y = THREE.MathUtils.degToRad(scapProt);

        // 3. Humerus (GH Pivot) Transformations
        // Elevation relative to glenoid cavity around +Z
        this.pivots.gh.rotation.z = -THREE.MathUtils.degToRad(ghElev);
        // Axial external/internal rotation around Y
        this.pivots.gh.rotation.y = THREE.MathUtils.degToRad(armRot);

        // 4. Cervical Spine & Cranium Transformations
        const cervFlex = getVal('cervical_flexion') || 0.0;
        const lowerFlex = getVal('lower_cervical_flex') || 0.0;
        const upperFlex = getVal('upper_cervical_flex') || 0.0;
        const headTrans = getVal('head_anterior_trans') || 0.0;
        const cvaAngle = getVal('cva_angle') || (53.0 - (headTrans / 50.0) * 20.0);

        if (this.pivots.c7t1) {
            this.pivots.c7t1.rotation.x = THREE.MathUtils.degToRad(lowerFlex);
            this.pivots.c7t1.position.z = this.jointCenters.c7t1.z + (headTrans * 0.0004);
        }
        if (this.pivots.aa) {
            this.pivots.aa.rotation.x = THREE.MathUtils.degToRad(upperFlex * 0.4);
        }
        if (this.pivots.ao) {
            this.pivots.ao.rotation.x = THREE.MathUtils.degToRad(upperFlex * 0.6);
        }

        // Extract muscle activations if available in Mode 2
        const muscleActivations = {};
        if (this.muscleData) {
            for (const col of this.muscleData.headers) {
                if (col.toLowerCase() !== 'time') {
                    muscleActivations[col] = this._interpolateChannel(this.muscleData.times, this.muscleData.data[col], this.currentTime);
                }
            }
        }

        if (this.currentMode === 'MODEL_ESTIMATED') {
            this._applyMuscleActivationColors(muscleActivations);
        }

        // Notify UI listeners
        if (typeof this.options.onPoseUpdated === 'function') {
            this.options.onPoseUpdated({
                time: this.currentTime,
                duration: this.timelineDuration,
                armElevation: round2(armElevation),
                scapUpwardRot: round2(scapUpwardRot),
                scapTilt: round2(scapTilt),
                scapProt: round2(scapProt),
                clavElev: round2(clavElev),
                ghElev: round2(ghElev),
                cervFlex: round2(cervFlex),
                lowerFlex: round2(lowerFlex),
                upperFlex: round2(upperFlex),
                headTrans: round2(headTrans),
                cvaAngle: round2(cvaAngle),
                muscleActivations
            });
        }
    }

    _applyMuscleActivationColors(activations) {
        if (!activations || Object.keys(activations).length === 0) return;

        // Map OpenSim muscle keys to mesh identifiers
        const muscleKeyMap = {
            'deltoid_anterior': ['deltoid_anterior', 'deltoideus_clavicular', 'delt_a'],
            'deltoid_lateral': ['deltoid_lateral', 'deltoideus_acromial', 'delt_l'],
            'deltoid_posterior': ['deltoid_posterior', 'deltoideus_spinal', 'delt_p'],
            'supraspinatus': ['supraspinatus', 'supra'],
            'infraspinatus': ['infraspinatus', 'infra'],
            'subscapularis': ['subscapularis', 'subscap'],
            'serratus_anterior': ['serratus_anterior', 'serratus_l', 'serratus_u', 'serratus'],
            'serratus': ['serratus', 'serratus_anterior', 'serratus_l', 'serratus_u'],
            'trapezius_upper': ['trapezius_upper', 'trapezius_descending', 'trap_u', 'trap-u'],
            'trap_u': ['trap_u', 'trap-u', 'trapezius_upper'],
            'trapezius_lower': ['trapezius_lower', 'trapezius_ascending', 'trap_l', 'trap-l'],
            'trap_l': ['trap_l', 'trap-l', 'trapezius_lower'],
            'pectoralis_minor': ['pectoralis_minor', 'pec_minor'],
            'pectoralis_major': ['pectoralis_major', 'pec_major'],
            'scm': ['scm'],
            'scalenes': ['scalenes'],
            'splenius': ['splenius'],
            'suboccipital': ['Suboccipital_Muscles', 'suboccipital'],
            'levator': ['Levator_Scapulae', 'levator'],
            'longus_colli': ['longus', 'longus_colli']
        };

        this.meshes.forEach((mesh, name) => {
            const lower = name.toLowerCase();
            let matchedAct = null;

            for (const [key, aliases] of Object.entries(muscleKeyMap)) {
                if (aliases.some(a => lower.includes(a))) {
                    matchedAct = activations[key] !== undefined ? activations[key] : (
                        key === 'deltoid_lateral' ? activations['delt_l'] :
                        key === 'deltoid_anterior' ? activations['delt_a'] :
                        key === 'deltoid_posterior' ? activations['delt_p'] :
                        key === 'supraspinatus' ? activations['supra'] :
                        key === 'infraspinatus' ? activations['infra'] :
                        key === 'subscapularis' ? activations['subscap'] :
                        key === 'serratus_anterior' ? (activations['serratus_l'] !== undefined ? activations['serratus_l'] : activations['serratus_u']) :
                        key === 'trapezius_upper' ? activations['trap_u'] :
                        key === 'trapezius_lower' ? activations['trap_l'] :
                        key === 'pectoralis_major' ? activations['pec_major'] :
                        key === 'pectoralis_minor' ? activations['pec_minor'] : null
                    );
                    break;
                }
            }

            if (matchedAct !== null && matchedAct !== undefined) {
                // Color ramp: Blue (0.0) -> Yellow (0.5) -> Red (1.0)
                const act = Math.max(0.0, Math.min(1.0, matchedAct));
                const col = new THREE.Color();
                if (act < 0.5) {
                    col.lerpColors(new THREE.Color(this.colors.activationLow), new THREE.Color(this.colors.activationMid), act * 2.0);
                } else {
                    col.lerpColors(new THREE.Color(this.colors.activationMid), new THREE.Color(this.colors.activationHigh), (act - 0.5) * 2.0);
                }
                mesh.material.color.copy(col);
                mesh.material.opacity = 0.85;
            }
        });
    }

    play() {
        this.isPlaying = true;
    }

    pause() {
        this.isPlaying = false;
    }

    togglePlay() {
        this.isPlaying = !this.isPlaying;
        return this.isPlaying;
    }

    reset() {
        this.seek(0.0);
    }

    setPlaybackSpeed(speed) {
        this.playbackSpeed = Math.max(0.1, Math.min(3.0, speed));
    }

    setVisualMode(mode) {
        this.currentMode = mode; // 'ANATOMICAL_FUNCTION', 'MODEL_ESTIMATED', 'SCENARIO_COMPARISON'
        if (mode === 'ANATOMICAL_FUNCTION') {
            this.clearHighlights();
        } else if (mode === 'MODEL_ESTIMATED') {
            this.seek(this.currentTime);
        }
    }

    setSkeletonVisible(visible) {
        if (this.skeletonRoot) this.skeletonRoot.visible = visible;
    }

    setMuscleOpacity(opacity) {
        const op = Math.max(0.0, Math.min(1.0, opacity));
        if (this.muscleRoot) {
            this.muscleRoot.visible = op > 0.01;
            this.meshes.forEach((mesh, name) => {
                if (!name.includes('Thorax') && !name.includes('Clavicle') && !name.includes('Scapula') && !name.includes('Humerus')) {
                    mesh.material.opacity = op;
                }
            });
        }
    }

    startAnimation() {
        if (this.isAnimating) return;
        this.isAnimating = true;
        this.lastFrameTime = performance.now();

        const renderLoop = (time) => {
            if (!this.isAnimating) return;

            // Frame time delta
            const dt = (time - this.lastFrameTime) / 1000.0;
            this.lastFrameTime = time;

            // Compute FPS
            this.frameCount++;
            if (this.frameCount >= 20) {
                this.fps = Math.round(1.0 / Math.max(0.001, dt));
                this.frameCount = 0;
                if (this.fpsCallback) this.fpsCallback(this.fps);
            }

            // Advance kinematic playback
            if (this.isPlaying && this.timelineDuration > 0) {
                let nextTime = this.currentTime + dt * this.playbackSpeed;
                if (nextTime > this.timelineDuration) {
                    nextTime = 0.0; // Loop seamlessly
                }
                this.seek(nextTime);
            }

            // Controls
            if (this.controls) this.controls.update();

            // Raycasting hover
            if (this.mouse.x !== -999 && this.camera && this.muscleRoot) {
                this.raycaster.setFromCamera(this.mouse, this.camera);
                const intersects = this.raycaster.intersectObjects(Array.from(this.meshes.values()), false);
                if (intersects.length > 0) {
                    this.hoveredMesh = intersects[0].object;
                    this.renderer.domElement.style.cursor = 'pointer';
                } else {
                    this.hoveredMesh = null;
                    this.renderer.domElement.style.cursor = 'default';
                }
            }

            this.renderer.render(this.scene, this.camera);
            this.animationFrameId = requestAnimationFrame(renderLoop);
        };

        this.animationFrameId = requestAnimationFrame(renderLoop);
    }

    stopAnimation() {
        this.isAnimating = false;
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }

    setFpsCallback(callback) {
        this.fpsCallback = callback;
    }

    resetCamera(focusArea = 'shoulder') {
        if (!this.camera || !this.controls) return;

        if (focusArea === 'shoulder') {
            this.camera.position.set(-0.25, 1.48, 1.05);
            this.controls.target.set(-0.10, 1.38, -0.02);
        } else if (focusArea === 'posterior') {
            this.camera.position.set(-0.25, 1.48, -0.95); // Posterior view of Right Scapula
            this.controls.target.set(-0.10, 1.38, -0.02);
        } else if (focusArea === 'lateral') {
            this.camera.position.set(-1.10, 1.42, -0.02); // Lateral view from right side
            this.controls.target.set(-0.10, 1.38, -0.02);
        }
        this.controls.update();
    }

    highlightMuscles(muscleNames, colorHex = null) {
        const highlightColor = new THREE.Color(colorHex || this.colors.muscleHighlighted);
        const targetSet = new Set(muscleNames.map(s => s.toLowerCase()));

        this.meshes.forEach((mesh, name) => {
            const lower = name.toLowerCase();
            const isBone = name === 'Thorax' || name === 'Clavicle_R' || name === 'Scapula_R' || name === 'Humerus_R';
            if (isBone) return; // Keep bone material intact

            const isTarget = Array.from(targetSet).some(t => lower.includes(t));

            if (isTarget) {
                mesh.material.color.copy(highlightColor);
                mesh.material.opacity = 0.95;
            } else {
                mesh.material.color.setHex(this.colors.muscleDefault);
                mesh.material.opacity = targetSet.size > 0 ? 0.20 : 0.65;
            }
        });
    }

    selectMuscle(muscleName) {
        this.selectedMeshName = muscleName;
        this.highlightMuscles([muscleName], this.colors.muscleHighlighted);
    }

    clearHighlights() {
        this.selectedMeshName = null;
        this.meshes.forEach((mesh, name) => {
            const isBone = name === 'Thorax' || name === 'Clavicle_R' || name === 'Scapula_R' || name === 'Humerus_R';
            if (!isBone) {
                mesh.material.color.setHex(this.colors.muscleDefault);
                mesh.material.opacity = 0.65;
            }
        });
    }

    dispose() {
        this.stopAnimation();
        window.removeEventListener('resize', () => this._onResize());
        if (this.renderer && this.renderer.domElement) {
            this.renderer.dispose();
            if (this.renderer.domElement.parentNode) {
                this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
            }
        }
    }
}

function round2(v) {
    return Math.round(v * 100) / 100;
}
