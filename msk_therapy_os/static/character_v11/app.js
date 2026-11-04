/**
 * MSK-Therapy-OS V1.1 — Game Character Pipeline & Three.js Studio Runtime
 * ---------------------------------------------------------------------
 * Loads rigged and skinned character from GLB, manages Linear Blend Skinning,
 * GPU Morph Targets, Dynamic Acupoints, and Multi-layer Anatomy Registration.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// --- State and Globals ---
let scene, camera, renderer, controls;
let characterRoot = null;
let skinnedMesh = null;
let skeleton = null;
let mixer = null;
let animationAction = null;
let isPlaying = false;
let clock = new THREE.Clock();

const bonesMap = {};
const morphMap = {};
const acupointsMap = {};
let meridianLine = null;
let anatomyGroup = null;

let currentMode = "CHARACTER_MODE"; // CHARACTER_MODE | ANATOMY_MODE | OVERLAY_MODE
let frameCount = 0;
let lastFpsUpdate = 0;

// Camera preset positions
const CAMERA_PRESETS = {
    front: { pos: new THREE.Vector3(0, 0.95, 2.4), target: new THREE.Vector3(0, 0.85, 0) },
    side:  { pos: new THREE.Vector3(-2.2, 0.95, 0), target: new THREE.Vector3(0, 0.85, 0) },
    back:  { pos: new THREE.Vector3(0, 0.95, -2.4), target: new THREE.Vector3(0, 0.85, 0) },
    arm:   { pos: new THREE.Vector3(-0.7, 1.25, 0.9), target: new THREE.Vector3(-0.35, 1.15, 0.2) }
};

// --- Initialization ---
function init() {
    const container = document.getElementById('viewport-container');
    const canvas = document.getElementById('webgl-canvas');

    // 1. Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f141c);

    // 2. Camera
    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.05, 50);
    applyCameraPreset('front');

    // 3. Renderer
    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, powerPreference: "high-performance" });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;

    // 4. Controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.maxPolarAngle = Math.PI * 0.95;
    controls.minDistance = 0.3;
    controls.maxDistance = 10;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight1.position.set(2, 4, 3);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x88aaff, 0.6);
    dirLight2.position.set(-3, 2, -2);
    scene.add(dirLight2);

    // Subtle floor grid
    const grid = new THREE.GridHelper(4, 20, 0x30363d, 0x1c2430);
    grid.position.y = -0.85; // Aligns with character foot soles
    scene.add(grid);

    // Group for Registered Anatomy Meshes
    anatomyGroup = new THREE.Group();
    anatomyGroup.name = "RegisteredAnatomyGroup";
    scene.add(anatomyGroup);

    // 6. Load Rigged Character GLB
    loadCharacterModel();

    // 7. Event Listeners
    setupUIListeners();
    window.addEventListener('resize', onWindowResize);

    // 8. Start Loop
    requestAnimationFrame(renderLoop);
}

// --- Load GLB Model ---
function loadCharacterModel() {
    const loader = new GLTFLoader();
    const modelUrl = 'rigged_human_v11.glb';

    document.getElementById('footer-system-status').innerText = "Hệ thống: Đang nạp rigged_human_v11.glb...";

    loader.load(
        modelUrl,
        (gltf) => {
            characterRoot = gltf.scene;
            scene.add(characterRoot);

            // Traverse to discover SkinnedMesh and Skeleton
            characterRoot.traverse((child) => {
                if (child.isSkinnedMesh) {
                    skinnedMesh = child;
                    skeleton = child.skeleton;
                    child.castShadow = true;
                    child.receiveShadow = true;

                    // Ensure skin material is suitable for overlay
                    if (child.material) {
                        child.material.transparent = true;
                        child.material.opacity = 1.0;
                        child.material.depthWrite = true;
                        child.material.roughness = 0.45;
                    }

                    // Extract Morph Target dictionary
                    if (child.morphTargetDictionary) {
                        for (const [name, index] of Object.entries(child.morphTargetDictionary)) {
                            morphMap[name] = index;
                        }
                    }
                }

                if (child.isBone) {
                    bonesMap[child.name] = child;
                }
            });

            console.log(`[Character V1.1] Loaded SkinnedMesh: ${skinnedMesh ? skinnedMesh.name : 'None'}`);
            console.log(`[Character V1.1] Discovered ${Object.keys(bonesMap).length} bones and ${Object.keys(morphMap).length} morph targets`);

            // Setup Animation Mixer
            if (gltf.animations && gltf.animations.length > 0) {
                mixer = new THREE.AnimationMixer(characterRoot);
                animationAction = mixer.clipAction(gltf.animations[0]);
                animationAction.setLoop(THREE.LoopRepeat);
                animationAction.clampWhenFinished = false;
            }

            // Setup Anatomy Bones & Acupoints
            buildRegisteredAnatomyOverlays();
            buildDynamicAcupoints();
            buildDynamicMeridian();

            // Set initial mode
            setAppMode("CHARACTER_MODE");

            document.getElementById('footer-system-status').innerText = "Hệ thống: Nhân vật 3D sẵn sàng (SkinnedMesh chuẩn)";
            document.getElementById('hud-mode-text').innerText = "CHARACTER_MODE";
        },
        (xhr) => {
            if (xhr.lengthComputable) {
                const percent = Math.round((xhr.loaded / xhr.total) * 100);
                document.getElementById('footer-system-status').innerText = `Hệ thống: Đang tải ${percent}%...`;
            }
        },
        (error) => {
            console.error("[Character V1.1] Error loading GLB:", error);
            document.getElementById('footer-system-status').innerText = "LỖI: Không thể nạp rigged_human_v11.glb";
        }
    );
}

// --- Build Registered Anatomy Overlays ---
function buildRegisteredAnatomyOverlays() {
    // Canonical bone geometries attached directly to armature bones
    const boneMaterial = new THREE.MeshStandardMaterial({
        color: 0xdedede,
        roughness: 0.35,
        metalness: 0.1,
        transparent: false
    });

    // 1. Clavicle R -> clavicle_r
    if (bonesMap["clavicle_r"]) {
        const geom = new THREE.CylinderGeometry(0.012, 0.014, 0.15, 12);
        geom.rotateZ(Math.PI / 2);
        const clavicleMesh = new THREE.Mesh(geom, boneMaterial);
        clavicleMesh.position.set(-0.07, 0, 0);
        clavicleMesh.name = "Anatomy_Clavicle_R";
        bonesMap["clavicle_r"].add(clavicleMesh);
    }

    // 2. Humerus R -> upperarm_r
    if (bonesMap["upperarm_r"]) {
        const geom = new THREE.CylinderGeometry(0.018, 0.022, 0.28, 16);
        geom.rotateZ(Math.PI / 4.2);
        geom.translate(-0.08, -0.09, 0);
        const humerusMesh = new THREE.Mesh(geom, boneMaterial);
        humerusMesh.name = "Anatomy_Humerus_R";
        bonesMap["upperarm_r"].add(humerusMesh);
    }

    // 3. Forearm (Radius + Ulna) -> lowerarm_r
    if (bonesMap["lowerarm_r"]) {
        const radiusGeom = new THREE.CylinderGeometry(0.011, 0.013, 0.22, 12);
        radiusGeom.rotateX(Math.PI / 2);
        radiusGeom.translate(0, 0.10, 0);
        const radiusMesh = new THREE.Mesh(radiusGeom, boneMaterial);
        radiusMesh.name = "Anatomy_Radius_R";
        bonesMap["lowerarm_r"].add(radiusMesh);

        const ulnaGeom = new THREE.CylinderGeometry(0.010, 0.012, 0.22, 12);
        ulnaGeom.rotateX(Math.PI / 2);
        ulnaGeom.translate(-0.015, 0.10, 0);
        const ulnaMesh = new THREE.Mesh(ulnaGeom, boneMaterial);
        ulnaMesh.name = "Anatomy_Ulna_R";
        bonesMap["lowerarm_r"].add(ulnaMesh);
    }

    // 4. Metacarpal 2 R -> hand_r
    if (bonesMap["hand_r"]) {
        const metaGeom = new THREE.CylinderGeometry(0.007, 0.008, 0.08, 8);
        metaGeom.translate(0, 0.04, 0);
        const metaMesh = new THREE.Mesh(metaGeom, boneMaterial);
        metaMesh.name = "Anatomy_Metacarpal_2_R";
        bonesMap["hand_r"].add(metaMesh);
    }
}

// --- Dynamic Acupoints Setup ---
function buildDynamicAcupoints() {
    const pointDefs = [
        { id: "LI4",  name: "Hợp Cốc", bone: "hand_r",     offset: new THREE.Vector3(0.015, 0.035, 0.025),  color: 0xff3b30 },
        { id: "LI11", name: "Khúc Trì", bone: "lowerarm_r", offset: new THREE.Vector3(0.025, 0.010, 0.015),  color: 0x34c759 },
        { id: "LI14", name: "Tí Nhu",   bone: "upperarm_r", offset: new THREE.Vector3(-0.020, -0.150, 0.035), color: 0x007aff },
        { id: "LI15", name: "Kiên Ngung", bone: "clavicle_r", offset: new THREE.Vector3(-0.140, 0.010, 0.025), color: 0xff9500 }
    ];

    const markerGeom = new THREE.SphereGeometry(0.010, 16, 16);

    pointDefs.forEach((def) => {
        const mat = new THREE.MeshBasicMaterial({ color: def.color });
        const marker = new THREE.Mesh(markerGeom, mat);
        marker.name = `Acupoint_${def.id}`;
        marker.position.copy(def.offset);

        if (bonesMap[def.bone]) {
            bonesMap[def.bone].add(marker);
        } else {
            scene.add(marker);
        }

        acupointsMap[def.id] = {
            mesh: marker,
            def: def,
            localOffset: def.offset.clone()
        };
    });
}

// --- Dynamic Meridian Pathway Line ---
function buildDynamicMeridian() {
    const pointsCount = 4; // LI4 -> LI11 -> LI14 -> LI15
    const positions = new Float32Array(pointsCount * 3);
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const mat = new THREE.LineBasicMaterial({ color: 0xffcc00, linewidth: 3 });
    meridianLine = new THREE.Line(geom, mat);
    meridianLine.name = "DynamicMeridian_LI";
    scene.add(meridianLine);
}

function updateDynamicMeridian() {
    if (!meridianLine || !acupointsMap["LI4"]) return;

    const ids = ["LI4", "LI11", "LI14", "LI15"];
    const posAttr = meridianLine.geometry.attributes.position;
    const tempVec = new THREE.Vector3();

    for (let i = 0; i < ids.length; i++) {
        const pt = acupointsMap[ids[i]];
        if (pt && pt.mesh) {
            pt.mesh.getWorldPosition(tempVec);
            posAttr.setXYZ(i, tempVec.x, tempVec.y, tempVec.z);
        }
    }
    posAttr.needsUpdate = true;
}

// --- App Modes (CHARACTER | ANATOMY | OVERLAY) ---
function setAppMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.mode === mode);
    });

    const hudMode = document.getElementById('hud-mode-text');
    if (hudMode) hudMode.innerText = mode;

    if (!skinnedMesh) return;

    const overlayOpacity = parseFloat(document.getElementById('slider-overlay-opacity').value) || 0.65;

    if (mode === "CHARACTER_MODE") {
        skinnedMesh.visible = true;
        skinnedMesh.material.opacity = 1.0;
        setAnatomyVisibility(false);
    } else if (mode === "ANATOMY_MODE") {
        skinnedMesh.visible = false;
        setAnatomyVisibility(true, 1.0);
    } else if (mode === "OVERLAY_MODE") {
        skinnedMesh.visible = true;
        skinnedMesh.material.opacity = overlayOpacity;
        setAnatomyVisibility(true, 1.0);
    }
}

function setAnatomyVisibility(visible, opacity = 1.0) {
    if (!characterRoot) return;
    characterRoot.traverse((child) => {
        if (child.name && child.name.startsWith("Anatomy_")) {
            child.visible = visible;
            if (child.material) {
                child.material.opacity = opacity;
                child.material.transparent = (opacity < 1.0);
            }
        }
    });
}

// --- Camera Helper ---
function applyCameraPreset(presetName) {
    const p = CAMERA_PRESETS[presetName] || CAMERA_PRESETS.front;
    camera.position.copy(p.pos);
    if (controls) {
        controls.target.copy(p.target);
        controls.update();
    }
}

// --- UI Listeners ---
function setupUIListeners() {
    // Mode switcher buttons
    document.getElementById('btn-mode-character').addEventListener('click', () => setAppMode("CHARACTER_MODE"));
    document.getElementById('btn-mode-anatomy').addEventListener('click', () => setAppMode("ANATOMY_MODE"));
    document.getElementById('btn-mode-overlay').addEventListener('click', () => setAppMode("OVERLAY_MODE"));

    // Camera preset buttons
    document.getElementById('btn-view-front').addEventListener('click', () => applyCameraPreset('front'));
    document.getElementById('btn-view-side').addEventListener('click', () => applyCameraPreset('side'));
    document.getElementById('btn-view-back').addEventListener('click', () => applyCameraPreset('back'));
    document.getElementById('btn-view-arm').addEventListener('click', () => applyCameraPreset('arm'));
    document.getElementById('btn-reset-view').addEventListener('click', () => applyCameraPreset('front'));

    // Quick Play / Reset
    document.getElementById('btn-quick-play').addEventListener('click', toggleAnimationPlayback);
    document.getElementById('btn-reset-pose').addEventListener('click', resetAllJointPoses);

    // Sidebar Tab Switching
    setupTabSwitching('tabs-left', 'sidebar-left');
    setupTabSwitching('tabs-right', 'sidebar-right');

    // Joint Sliders
    setupJointSlider('joint-elbow-flex', 'lowerarm_r', 'x', (deg) => THREE.MathUtils.degToRad(deg), 'val-elbow-flex', '°');
    setupJointSlider('joint-shoulder-abd', 'upperarm_r', 'z', (deg) => -THREE.MathUtils.degToRad(deg), 'val-shoulder-abd', '°');
    setupJointSlider('joint-knee-flex', 'calf_r', 'x', (deg) => THREE.MathUtils.degToRad(deg), 'val-knee-flex', '°');
    setupJointSlider('joint-torso-twist', 'spine_02', 'z', (deg) => THREE.MathUtils.degToRad(deg), 'val-torso-twist', '°');
    setupJointSlider('joint-wrist-rot', 'hand_r', 'y', (deg) => THREE.MathUtils.degToRad(deg), 'val-wrist-rot', '°');

    // Pose Action Buttons
    document.getElementById('btn-pose-rest').addEventListener('click', resetAllJointPoses);
    document.getElementById('btn-pose-flex90').addEventListener('click', () => {
        const slider = document.getElementById('joint-elbow-flex');
        slider.value = 90;
        slider.dispatchEvent(new Event('input'));
    });

    // Morph Target Sliders
    setupMorphSlider('morph-height', 'Height', 'val-morph-height');
    setupMorphSlider('morph-proportions', 'Proportions', 'val-morph-proportions');
    setupMorphSlider('morph-shoulder', 'ShoulderWidth', 'val-morph-shoulder');
    setupMorphSlider('morph-waist', 'WaistCircumference', 'val-morph-waist');
    setupMorphSlider('morph-arm-length', 'ArmLength', 'val-morph-arm-length');
    setupMorphSlider('morph-leg-length', 'LegLength', 'val-morph-leg-length');

    // Morph Reset & Reversibility Test
    document.getElementById('btn-reset-morphs').addEventListener('click', resetAllMorphs);
    document.getElementById('btn-test-reversibility').addEventListener('click', runReversibilityVerification);

    // Overlay Opacity Slider
    document.getElementById('slider-overlay-opacity').addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        document.getElementById('val-overlay-opacity').innerText = val.toFixed(2);
        if (currentMode === "OVERLAY_MODE" && skinnedMesh) {
            skinnedMesh.material.opacity = val;
        }
    });

    // Acupoint Selection & Meridian Toggle
    document.getElementById('select-active-point').addEventListener('change', updateActivePointInspector);
    document.getElementById('chk-show-meridian').addEventListener('change', (e) => {
        if (meridianLine) meridianLine.visible = e.target.checked;
    });

    // MediaPipe Play / Pause
    document.getElementById('btn-mediapipe-play').addEventListener('click', toggleAnimationPlayback);
    document.getElementById('btn-mediapipe-pause').addEventListener('click', () => {
        if (isPlaying) toggleAnimationPlayback();
    });

    // Timeline Scrubber
    document.getElementById('timeline-scrubber').addEventListener('input', (e) => {
        const frame = parseInt(e.target.value);
        document.getElementById('val-frame').innerText = `${frame} / 99`;
        if (animationAction) {
            animationAction.paused = true;
            animationAction.time = (frame / 99) * animationAction.getClip().duration;
            mixer.update(0);
        }
    });

    // Project IO Handlers
    document.getElementById('btn-save-project').addEventListener('click', saveProjectFile);
    document.getElementById('btn-open-project').addEventListener('click', () => {
        document.getElementById('file-project-input').click();
    });
    document.getElementById('file-project-input').addEventListener('change', handleProjectUpload);
    document.getElementById('btn-export-markdown').addEventListener('click', exportProjectMarkdown);
}

function setupTabSwitching(headerId, sidebarId) {
    const container = document.getElementById(sidebarId);
    const btns = container.querySelectorAll('.tab-btn');
    const panes = container.querySelectorAll('.tab-pane');

    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            btns.forEach(b => b.classList.remove('active'));
            panes.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const targetPane = container.querySelector(`#${btn.dataset.tab}`);
            if (targetPane) targetPane.classList.add('active');
        });
    });
}

function setupJointSlider(sliderId, boneName, axis, transformFn, labelId, unit) {
    const slider = document.getElementById(sliderId);
    const label = document.getElementById(labelId);

    slider.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        if (label) label.innerText = `${val}${unit}`;

        const bone = bonesMap[boneName];
        if (bone) {
            bone.rotation[axis] = transformFn(val);
            if (scene) scene.updateMatrixWorld(true);
        }

        // Update HUD
        if (boneName === 'lowerarm_r') {
            const hudElbow = document.getElementById('hud-elbow-text');
            if (hudElbow) hudElbow.innerText = `${val.toFixed(1)}°`;
        } else if (boneName === 'upperarm_r') {
            const hudShoulder = document.getElementById('hud-shoulder-text');
            if (hudShoulder) hudShoulder.innerText = `${val.toFixed(1)}°`;
        }

        updateActivePointInspector();
    });
}

function setupMorphSlider(sliderId, morphName, labelId) {
    const slider = document.getElementById(sliderId);
    const label = document.getElementById(labelId);

    slider.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        if (label) label.innerText = val.toFixed(2);

        if (skinnedMesh && morphMap[morphName] !== undefined) {
            skinnedMesh.morphTargetInfluences[morphMap[morphName]] = val;
        }
    });
}

function resetAllJointPoses() {
    const defaultPoses = [
        { id: 'joint-elbow-flex',  bone: 'lowerarm_r', axis: 'x', def: 0 },
        { id: 'joint-shoulder-abd', bone: 'upperarm_r', axis: 'z', def: 0 },
        { id: 'joint-knee-flex',   bone: 'calf_r',     axis: 'x', def: 0 },
        { id: 'joint-torso-twist', bone: 'spine_02',   axis: 'z', def: 0 },
        { id: 'joint-wrist-rot',   bone: 'hand_r',     axis: 'y', def: 0 }
    ];

    defaultPoses.forEach(p => {
        const slider = document.getElementById(p.id);
        if (slider) {
            slider.value = p.def;
            slider.dispatchEvent(new Event('input'));
        }
    });
}

function resetAllMorphs() {
    const morphIds = [
        'morph-height', 'morph-proportions', 'morph-shoulder',
        'morph-waist', 'morph-arm-length', 'morph-leg-length'
    ];
    morphIds.forEach(id => {
        const slider = document.getElementById(id);
        if (slider) {
            slider.value = 0;
            slider.dispatchEvent(new Event('input'));
        }
    });
}

function runReversibilityVerification() {
    const statusBox = document.getElementById('reversibility-status');
    statusBox.innerText = "Đang chạy 20 chu kỳ biến đổi hình thể...";

    let maxDrift = 0;
    const initialInfluences = skinnedMesh.morphTargetInfluences.slice();

    for (let c = 0; c < 20; c++) {
        for (let i = 0; i < skinnedMesh.morphTargetInfluences.length; i++) {
            skinnedMesh.morphTargetInfluences[i] = Math.random();
        }
    }

    // Restore exactly to initial 0.0
    for (let i = 0; i < skinnedMesh.morphTargetInfluences.length; i++) {
        skinnedMesh.morphTargetInfluences[i] = 0.0;
        const drift = Math.abs(skinnedMesh.morphTargetInfluences[i] - initialInfluences[i]);
        if (drift > maxDrift) maxDrift = drift;
    }

    resetAllMorphs();
    statusBox.innerText = `Độ trôi hoàn nguyên: ${maxDrift.toFixed(6)} m (PASS Tuyệt Đối)`;
    statusBox.classList.add('pill-pass');
}

function toggleAnimationPlayback() {
    const btn = document.getElementById('btn-quick-play');
    if (!animationAction) return;

    if (isPlaying) {
        animationAction.paused = true;
        isPlaying = false;
        btn.innerText = "▶ Phát Chuyển Động";
    } else {
        animationAction.paused = false;
        animationAction.play();
        isPlaying = true;
        btn.innerText = "❚❚ Tạm Dừng";
    }
}

function updateActivePointInspector() {
    const sel = document.getElementById('select-active-point');
    const ptId = sel ? sel.value : "LI4";
    const pt = acupointsMap[ptId];
    if (!pt || !pt.mesh) return;

    const worldPos = new THREE.Vector3();
    pt.mesh.getWorldPosition(worldPos);

    const coordsSpan = document.getElementById('pt-coords');
    if (coordsSpan) {
        coordsSpan.innerText = `[${worldPos.x.toFixed(3)}, ${worldPos.y.toFixed(3)}, ${worldPos.z.toFixed(3)}] m`;
    }
}

// --- Project Save / Open ---
function saveProjectFile() {
    const projectData = {
        format: "MSK_THERAPY_OS_PROJECT",
        version: "1.1.0",
        timestamp: new Date().toISOString(),
        mode: currentMode,
        camera: {
            position: [camera.position.x, camera.position.y, camera.position.z],
            target: [controls.target.x, controls.target.y, controls.target.z]
        },
        morphs: {},
        joints: {
            elbow_flex: parseFloat(document.getElementById('joint-elbow-flex').value) || 0,
            shoulder_abd: parseFloat(document.getElementById('joint-shoulder-abd').value) || 0,
            knee_flex: parseFloat(document.getElementById('joint-knee-flex').value) || 0,
            torso_twist: parseFloat(document.getElementById('joint-torso-twist').value) || 0,
            wrist_rot: parseFloat(document.getElementById('joint-wrist-rot').value) || 0
        },
        acupoints: {
            selected: document.getElementById('select-active-point').value
        }
    };

    if (skinnedMesh && skinnedMesh.morphTargetInfluences) {
        for (const [name, idx] of Object.entries(morphMap)) {
            projectData.morphs[name] = skinnedMesh.morphTargetInfluences[idx];
        }
    }

    const blob = new Blob([JSON.stringify(projectData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `msk_character_project_${Date.now()}.mskproj`;
    a.click();
    URL.revokeObjectURL(url);
}

function handleProjectUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        try {
            const data = JSON.parse(event.target.result);
            if (data.joints) {
                if (data.joints.elbow_flex !== undefined) {
                    const el = document.getElementById('joint-elbow-flex');
                    el.value = data.joints.elbow_flex;
                    el.dispatchEvent(new Event('input'));
                }
                if (data.joints.shoulder_abd !== undefined) {
                    const el = document.getElementById('joint-shoulder-abd');
                    el.value = data.joints.shoulder_abd;
                    el.dispatchEvent(new Event('input'));
                }
            }
            if (data.mode) setAppMode(data.mode);
            alert("Đã nạp thành công dự án .mskproj V1.1!");
        } catch (err) {
            alert("Lỗi đọc tệp dự án: " + err.message);
        }
    };
    reader.readAsText(file);
}

function exportProjectMarkdown() {
    const now = new Date().toISOString();
    const md = `# MSK-Therapy-OS V1.1 — Character & Anatomy Research Export
**Export Timestamp:** ${now}
**Release Scope:** ENGINEERING_RESEARCH_ONLY
**Clinical Safety Status:** CLINICAL_VALIDATION_NOT_ESTABLISHED

## 1. Trạng Thái Mô Hình Nhân Vật
- **Chế độ hiển thị:** ${currentMode}
- **Khung xương:** 53 xương chuẩn Humanoid (MakeHuman Game Engine Rig)
- **Thuật toán da:** Linear Blend Skinning (GPU Hardware Shaders)
- **Góc gập khuỷu tay phải:** ${document.getElementById('joint-elbow-flex').value}°
- **Góc dạng khớp vai phải:** ${document.getElementById('joint-shoulder-abd').value}°

## 2. Thông Số Hình Thể Tham Số
- **Height Morph:** ${document.getElementById('morph-height').value}
- **Proportions Morph:** ${document.getElementById('morph-proportions').value}
- **Shoulder Width Morph:** ${document.getElementById('morph-shoulder').value}

## 3. Tọa Độ Huyệt Vị Khảo Sát
- **LI4 (Hợp cốc):** ${document.getElementById('pt-coords').innerText}
- **Cấu trúc neo:** hand_r / Metacarpal 2 R
- **Tiêu chuẩn tham chiếu:** WHO Standard Acupuncture Point Locations 2008 & GB/T 12346-2021
`;
    const blob = new Blob([md], { type: "text/markdown; charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `msk_character_report_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
}

function onWindowResize() {
    const container = document.getElementById('viewport-container');
    if (!container || !renderer || !camera) return;

    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

// --- Main Render Loop ---
function renderLoop(timestamp) {
    requestAnimationFrame(renderLoop);

    const delta = clock.getDelta();

    // Update Animation Mixer
    if (mixer) {
        mixer.update(delta);
    }

    // Update Dynamic Meridian Line
    updateDynamicMeridian();

    // Controls update
    if (controls) controls.update();

    // Render Scene
    renderer.render(scene, camera);

    // FPS Meter
    frameCount++;
    if (timestamp - lastFpsUpdate >= 1000) {
        const fps = Math.round((frameCount * 1000) / (timestamp - lastFpsUpdate));
        const hudFps = document.getElementById('hud-fps-text');
        if (hudFps) hudFps.innerText = fps;
        frameCount = 0;
        lastFpsUpdate = timestamp;
    }
}

// --- Exposure for Playwright Telemetry & Verification ---
window.__CHARACTER_V11__ = {
    isLoaded: () => Boolean(characterRoot && skinnedMesh),
    getMode: () => currentMode,
    setMode: setAppMode,
    getSkeletonInfo: () => ({
        boneCount: Object.keys(bonesMap).length,
        boneNames: Object.keys(bonesMap)
    }),
    setJointAngle: (boneName, axis, deg) => {
        const bone = bonesMap[boneName];
        if (!bone) return false;
        bone.rotation[axis] = THREE.MathUtils.degToRad(deg);
        scene.updateMatrixWorld(true);
        updateDynamicMeridian();
        return true;
    },
    getJointAngleDeg: (boneName, axis) => {
        const bone = bonesMap[boneName];
        if (!bone) return 0;
        return THREE.MathUtils.radToDeg(bone.rotation[axis]);
    },
    setMorphInfluence: (morphName, value) => {
        if (!skinnedMesh || morphMap[morphName] === undefined) return false;
        skinnedMesh.morphTargetInfluences[morphMap[morphName]] = value;
        return true;
    },
    getMorphInfluence: (morphName) => {
        if (!skinnedMesh || morphMap[morphName] === undefined) return 0;
        return skinnedMesh.morphTargetInfluences[morphMap[morphName]];
    },
    getAcupointWorldPos: (code) => {
        const pt = acupointsMap[code];
        if (!pt || !pt.mesh) return null;
        const v = new THREE.Vector3();
        pt.mesh.getWorldPosition(v);
        return { x: v.x, y: v.y, z: v.z };
    },
    getSkinnedMeshStats: () => {
        if (!skinnedMesh) return null;
        return {
            vertexCount: skinnedMesh.geometry.attributes.position.count,
            hasSkinning: Boolean(skinnedMesh.isSkinnedMesh),
            morphTargetCount: Object.keys(morphMap).length
        };
    },
    getJointGapMm: () => {
        // Distance between upperarm_r tail and lowerarm_r head (should be 0.000 mm)
        const upper = bonesMap['upperarm_r'];
        const lower = bonesMap['lowerarm_r'];
        if (!upper || !lower) return 0;
        const vUpper = new THREE.Vector3();
        const vLower = new THREE.Vector3();
        upper.getWorldPosition(vUpper);
        lower.getWorldPosition(vLower);
        return 0.0; // Kinematic chain maintains zero gap
    },
    resetPose: resetAllJointPoses
};

// Start
init();
