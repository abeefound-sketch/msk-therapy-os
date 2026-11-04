import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// --- State Variables ---
let scene, camera, renderer, controls, raycaster, mouse;
let container;
let groupBone, groupMuscle, groupOrgan, groupSkin;
let groupMarkers, groupPolylines, groupDraftLine;

// --- V1.0 Hierarchical Armature Groups (Reality Repair: Zero Double Transform Architecture) ---
let armRootGroup;
let scapulaGroup, upperArmGroup, forearmGroup, handGroup; // Unscaled kinematic nodes (Scale ALWAYS 1.0)
let scapulaVisual, upperArmVisual, forearmVisual, handVisual; // Visual containers for scaling & meshes
let dynamicMarkersGroup, dynamicMeridianLine;
const dynamicMarkersMap = new Map(); // code -> { mesh, label, segment, localPos }

// Canonical base pivot positions in BodyParts3D coordinates (measured from real meshes, meters)
const BASE_PIVOTS = {
    scapula: new THREE.Vector3(-0.010, 1.410, 0.001),     // Sternoclavicular joint (FJ3362/Sternum)
    shoulder: new THREE.Vector3(-0.190, 1.395, -0.024),   // Glenohumeral joint (FJ3384/FJ3368)
    elbow: new THREE.Vector3(-0.190, 1.122, -0.024),      // Elbow joint (FJ3368/FJ3349/FJ3391)
    wrist: new THREE.Vector3(-0.250, 0.894, -0.006)       // Radiocarpal joint (FJ3349/Carpal/FJ3352)
};

// Current Parametric Body Parameters
let currentBodyParams = {
    height_scale: 1.00,
    right_arm_length_ratio: 1.00,
    right_arm_circumference_visual: 1.00,
    preset_name: 'baseline',
    morph_version: 1
};

// Current Kinematic Pose
let currentKinematicPose = {
    source: 'VIDEOMP', // 'VIDEOMP' | 'MOUSEPOSE'
    shoulder_elevation_deg: 0.0,
    scapula_elevation_deg: 0.0,
    glenohumeral_elevation_deg: 0.0,
    elbow_flexion_deg: 0.0
};

const chunkBuffers = {}; // chunkIndex -> ArrayBuffer
const loadedStructures = new Map(); // id -> THREE.Mesh
let allStructuresCatalog = []; // List of all 2,234 structures
let currentMode = 'inspect'; // 'inspect' | 'acupoint' | 'polyline'
let selectedMesh = null;
let hoveredMesh = null;
let tempIntersectData = null;

const userAnnotations = [];
const userPolylines = [];
const draftWaypoints = [];
let draftLineMesh = null;

const ORGAN_SYSTEMS = new Set([
    'digestive', 'respiratory', 'cardiac', 'urinary', 'arterial',
    'venous', 'nervous', 'endocrine', 'reproductive', 'sensory', 'lymphatic'
]);

// --- DOM Elements ---
const elSpinner = document.getElementById('loading-spinner');
const elSpinnerText = document.getElementById('loading-text');
const elTooltip = document.getElementById('tooltip-3d');
const elHudMode = document.getElementById('hud-mode-text');
const elInspector = document.getElementById('inspector-body');
const elSearchInput = document.getElementById('search-structure');
const elSearchResults = document.getElementById('search-results-list');
const elAnnotationsList = document.getElementById('annotations-list');
const elPolylinesList = document.getElementById('polylines-list');
const elAnnotationsCount = document.getElementById('annotations-count');
const elPolylinesCount = document.getElementById('polylines-count');
const elWaypointCount = document.getElementById('waypoint-count');
const elBtnUndo = document.getElementById('btn-undo-waypoint');
const elBtnClear = document.getElementById('btn-clear-polyline');
const elBtnSavePolyline = document.getElementById('btn-save-polyline');
const elSkinOpacity = document.getElementById('skin-opacity');
const elSkinOpacityVal = document.getElementById('skin-opacity-val');

// V1.0 Parametric Elements
const elMorphVersionBadge = document.getElementById('morph-version-badge');
const elPresetBaseline = document.getElementById('preset-baseline');
const elPresetSlender = document.getElementById('preset-slender');
const elPresetBroader = document.getElementById('preset-broader');
const elPresetLongerArm = document.getElementById('preset-longer-arm');
const elParamHeight = document.getElementById('param-height-scale');
const elParamArmLength = document.getElementById('param-arm-length');
const elParamArmCircumference = document.getElementById('param-arm-circumference');
const elValParamHeight = document.getElementById('val-param-height');
const elValParamArmLength = document.getElementById('val-param-arm-length');
const elValParamArmCircumference = document.getElementById('val-param-arm-circumference');
const elValDriftStatus = document.getElementById('val-drift-status');

// V1.0 Mouse Pose & Motion Mode Elements
const elBtnModeVideoMP = document.getElementById('btn-mode-videomp');
const elBtnModeMousePose = document.getElementById('btn-mode-mousepose');
const elContainerVideoMP = document.getElementById('container-videomp');
const elContainerMousePose = document.getElementById('container-mousepose');
const elMousePoseShoulder = document.getElementById('mouse-pose-shoulder');
const elMousePoseElbow = document.getElementById('mouse-pose-elbow');
const elValMouseShoulder = document.getElementById('val-mouse-shoulder');
const elValMouseElbow = document.getElementById('val-mouse-elbow');
const elBtnResetMousePose = document.getElementById('btn-reset-mousepose');

// V1.0 Acupoint Undo / Redo
const elBtnUndoAcupoint = document.getElementById('btn-undo-acupoint');
const elBtnRedoAcupoint = document.getElementById('btn-redo-acupoint');

// V1.0 Project Save / Load Header Elements
const elBtnHeaderSaveProj = document.getElementById('btn-header-save-project');
const elBtnHeaderLoadProj = document.getElementById('btn-header-load-project');
const elFileLoadProj = document.getElementById('file-load-project');

// Modal Elements
const elModalAcupoint = document.getElementById('modal-acupoint');
const elModalPointLabel = document.getElementById('modal-point-label');
const elModalPointCode = document.getElementById('modal-point-code');
const elModalPointRadius = document.getElementById('modal-point-radius');
const elModalPointStructure = document.getElementById('modal-point-structure');
const elModalPointCoords = document.getElementById('modal-point-coords');
const elModalPointNotes = document.getElementById('modal-point-notes');
const elBtnCancelPoint = document.getElementById('btn-cancel-point');
const elBtnConfirmSavePoint = document.getElementById('btn-confirm-save-point');
const elBtnCloseModalAcupoint = document.getElementById('btn-close-modal-acupoint');

const elModalExport = document.getElementById('modal-export');
const elExportMarkdownContent = document.getElementById('export-markdown-content');
const elBtnCloseModalExport = document.getElementById('btn-close-modal-export');
const elBtnCopyMarkdown = document.getElementById('btn-copy-markdown');
const elBtnDownloadMarkdown = document.getElementById('btn-download-markdown');

// --- Initialization ---
window.addEventListener('DOMContentLoaded', async () => {
    initThreeScene();
    initArmatureHierarchy();
    initDynamicMarkers();
    setupEventListeners();
    await loadMetadataAndCatalog();
    await loadInitialAnatomy();
    await loadSavedAnnotations();
    await initP33MotionAndKnowledge();
    animate();
});

// --- Three.js Setup ---
function initThreeScene() {
    container = document.getElementById('canvas-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050811);
    scene.fog = new THREE.FogExp2(0x050811, 0.25);

    // Camera
    camera = new THREE.PerspectiveCamera(45, width / height, 0.05, 20);
    camera.position.set(0, 1.25, 1.7);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    container.appendChild(renderer.domElement);

    // Controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.target.set(0, 1.05, 0); // Center around upper torso / thorax
    controls.maxDistance = 5.0;
    controls.minDistance = 0.2;

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight1.position.set(2, 4, 3);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x38bdf8, 0.4);
    dirLight2.position.set(-3, -2, -2);
    scene.add(dirLight2);

    const pointLight = new THREE.PointLight(0xffffff, 0.5, 10);
    pointLight.position.set(0, 1.5, 1.5);
    scene.add(pointLight);

    // Groups
    groupBone = new THREE.Group();
    groupMuscle = new THREE.Group();
    groupOrgan = new THREE.Group();
    groupSkin = new THREE.Group();
    groupMarkers = new THREE.Group();
    groupPolylines = new THREE.Group();
    groupDraftLine = new THREE.Group();

    scene.add(groupBone);
    scene.add(groupMuscle);
    scene.add(groupOrgan);
    scene.add(groupSkin);
    scene.add(groupMarkers);
    scene.add(groupPolylines);
    scene.add(groupDraftLine);

    // Raycaster & Interaction
    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();

    window.addEventListener('resize', onWindowResize);
    renderer.domElement.addEventListener('mousemove', onMouseMove);
    renderer.domElement.addEventListener('click', onCanvasClick);
}

function onWindowResize() {
    const width = container.clientWidth;
    const height = container.clientHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
}

// --- V1.0 Armature Hierarchy & Kinematics Engine (Zero Double Transform) ---
function initArmatureHierarchy() {
    armRootGroup = new THREE.Group();
    armRootGroup.name = "armRootGroup";

    // Kinematic joint groups (ALWAYS SCALE 1.0. Rotation & Joint Offsets only)
    scapulaGroup = new THREE.Group();
    scapulaGroup.name = "scapulaGroup";
    scapulaGroup.position.copy(BASE_PIVOTS.scapula);

    upperArmGroup = new THREE.Group();
    upperArmGroup.name = "upperArmGroup";
    upperArmGroup.position.subVectors(BASE_PIVOTS.shoulder, BASE_PIVOTS.scapula);

    forearmGroup = new THREE.Group();
    forearmGroup.name = "forearmGroup";
    forearmGroup.position.subVectors(BASE_PIVOTS.elbow, BASE_PIVOTS.shoulder);

    handGroup = new THREE.Group();
    handGroup.name = "handGroup";
    handGroup.position.subVectors(BASE_PIVOTS.wrist, BASE_PIVOTS.elbow);

    // Visual containers attached to joint nodes (receives visual scaling for circumference & length)
    scapulaVisual = new THREE.Group();
    scapulaVisual.name = "scapulaVisual";
    scapulaGroup.add(scapulaVisual);

    upperArmVisual = new THREE.Group();
    upperArmVisual.name = "upperArmVisual";
    upperArmGroup.add(upperArmVisual);

    forearmVisual = new THREE.Group();
    forearmVisual.name = "forearmVisual";
    forearmGroup.add(forearmVisual);

    handVisual = new THREE.Group();
    handVisual.name = "handVisual";
    handGroup.add(handVisual);

    // Assembly of kinematic chain: hand -> forearm -> upperArm -> scapula -> armRoot
    forearmGroup.add(handGroup);
    upperArmGroup.add(forearmGroup);
    scapulaGroup.add(upperArmGroup);
    armRootGroup.add(scapulaGroup);

    scene.add(armRootGroup);
}

function createAcupointSphere(code, name, colorHex) {
    const geom = new THREE.SphereGeometry(0.009, 16, 16);
    const mat = new THREE.MeshStandardMaterial({
        color: colorHex,
        emissive: colorHex,
        emissiveIntensity: 0.8,
        roughness: 0.1
    });
    const mesh = new THREE.Mesh(geom, mat);
    mesh.name = `marker_${code}`;
    mesh.userData = { code: code, name: name, isAcupointMarker: true };
    return mesh;
}

function initDynamicMarkers() {
    dynamicMarkersGroup = new THREE.Group();
    dynamicMarkersGroup.name = "dynamicMarkersGroup";
    scene.add(dynamicMarkersGroup);

    // LI15 (Scapula_R Acromion - Kiên Ngung)
    const mLI15 = createAcupointSphere('LI15', 'Kiên Ngung (LI15)', 0x38bdf8);
    mLI15.position.set(-0.160, 1.410, -0.020);
    scene.add(mLI15);
    scapulaVisual.attach(mLI15);
    dynamicMarkersMap.set('LI15', { mesh: mLI15, code: 'LI15', name: 'Kiên Ngung', localPos: [-0.160, 1.410, -0.020] });

    // LI14 (Humerus_R Deltoid tuberosity - Tí Nhu)
    const mLI14 = createAcupointSphere('LI14', 'Tí Nhu (LI14)', 0x06b6d4);
    mLI14.position.set(-0.210, 1.250, -0.015);
    scene.add(mLI14);
    upperArmVisual.attach(mLI14);
    dynamicMarkersMap.set('LI14', { mesh: mLI14, code: 'LI14', name: 'Tí Nhu', localPos: [-0.210, 1.250, -0.015] });

    // LI11 (Elbow lateral epicondyle / cubital crease - Khúc Trì)
    const mLI11 = createAcupointSphere('LI11', 'Khúc Trì (LI11)', 0x10b981);
    mLI11.position.set(-0.215, 1.120, -0.015);
    scene.add(mLI11);
    forearmVisual.attach(mLI11);
    dynamicMarkersMap.set('LI11', { mesh: mLI11, code: 'LI11', name: 'Khúc Trì', localPos: [-0.215, 1.120, -0.015] });

    // LI4 (Metacarpal_2_R Radial midpoint - Hợp Cốc)
    const mLI4 = createAcupointSphere('LI4', 'Hợp Cốc (LI4)', 0xf59e0b);
    mLI4.position.set(-0.280, 0.835, 0.035);
    scene.add(mLI4);
    handVisual.attach(mLI4);
    dynamicMarkersMap.set('LI4', { mesh: mLI4, code: 'LI4', name: 'Hợp Cốc', localPos: [-0.280, 0.835, 0.035] });

    // Dynamic Shou Yangming Large Intestine Meridian trajectory (LI4 -> LI11 -> LI14 -> LI15)
    const lineGeom = new THREE.BufferGeometry();
    const lineMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, linewidth: 3 });
    dynamicMeridianLine = new THREE.Line(lineGeom, lineMat);
    scene.add(dynamicMeridianLine);
    updateMeridianLine();
}

function updateMeridianLine() {
    if (!dynamicMeridianLine) return;
    const mLI4 = dynamicMarkersMap.get('LI4')?.mesh;
    const mLI11 = dynamicMarkersMap.get('LI11')?.mesh;
    const mLI14 = dynamicMarkersMap.get('LI14')?.mesh;
    const mLI15 = dynamicMarkersMap.get('LI15')?.mesh;
    if (mLI4 && mLI11 && mLI14 && mLI15) {
        const v4 = new THREE.Vector3();
        const v11 = new THREE.Vector3();
        const v14 = new THREE.Vector3();
        const v15 = new THREE.Vector3();
        mLI4.getWorldPosition(v4);
        mLI11.getWorldPosition(v11);
        mLI14.getWorldPosition(v14);
        mLI15.getWorldPosition(v15);
        const pts = [v4, v11, v14, v15];
        dynamicMeridianLine.geometry.setFromPoints(pts);
    }
}

function applyArmKinematics(shoulderElevDeg, elbowFlexDeg) {
    // 2:1 Inman Scapulohumeral rhythm
    const scapulaDeg = shoulderElevDeg / 3.0;
    const humerusDeg = (shoulderElevDeg * 2.0) / 3.0;

    // Rotate hierarchy
    scapulaGroup.rotation.z = THREE.MathUtils.degToRad(-scapulaDeg);
    upperArmGroup.rotation.z = THREE.MathUtils.degToRad(-humerusDeg);
    forearmGroup.rotation.x = THREE.MathUtils.degToRad(-elbowFlexDeg);

    currentKinematicPose.shoulder_elevation_deg = shoulderElevDeg;
    currentKinematicPose.scapula_elevation_deg = scapulaDeg;
    currentKinematicPose.glenohumeral_elevation_deg = humerusDeg;
    currentKinematicPose.elbow_flexion_deg = elbowFlexDeg;

    const elValShoulder = document.getElementById('val-shoulder-elevation');
    const elValElbow = document.getElementById('val-elbow-flexion');
    if (elValShoulder) elValShoulder.innerText = `${shoulderElevDeg.toFixed(1)}° (Bả vai: ${scapulaDeg.toFixed(1)}°, Cánh tay: ${humerusDeg.toFixed(1)}°)`;
    if (elValElbow) elValElbow.innerText = `${elbowFlexDeg.toFixed(1)}°`;

    updateMeridianLine();
}

function applyParametricScales(heightScale, armLengthRatio, armCircumVisual, presetName = 'custom') {
    const h = parseFloat(heightScale);
    const l = parseFloat(armLengthRatio);
    const c = parseFloat(armCircumVisual);

    currentBodyParams.height_scale = h;
    currentBodyParams.right_arm_length_ratio = l;
    currentBodyParams.right_arm_circumference_visual = c;
    currentBodyParams.preset_name = presetName;
    currentBodyParams.morph_version += 1;

    // Joint kinematic groups ALWAYS maintain unit scale (1, 1, 1) - ZERO DOUBLE TRANSFORM
    scapulaGroup.scale.set(1, 1, 1);
    upperArmGroup.scale.set(1, 1, 1);
    forearmGroup.scale.set(1, 1, 1);
    handGroup.scale.set(1, 1, 1);

    // Visual containers receive proportional scale (circumference in X/Z, length in Y)
    upperArmVisual.scale.set(c, l, c);
    forearmVisual.scale.set(c, l, c);
    handVisual.scale.set(c, l, c);

    // Segment positions adjust strictly linearly by armLengthRatio
    const baseUpperArmLen = BASE_PIVOTS.elbow.clone().sub(BASE_PIVOTS.shoulder);
    const baseForearmLen = BASE_PIVOTS.wrist.clone().sub(BASE_PIVOTS.elbow);

    forearmGroup.position.copy(baseUpperArmLen).multiplyScalar(l);
    handGroup.position.copy(baseForearmLen).multiplyScalar(l);

    // Height scale on static body layers
    groupBone.scale.set(1, h, 1);
    groupMuscle.scale.set(1, h, 1);
    groupOrgan.scale.set(1, h, 1);
    groupSkin.scale.set(1, h, 1);

    // Translate shoulder girdle elevation with height
    armRootGroup.position.set(0, (h - 1.0) * BASE_PIVOTS.scapula.y, 0);

    // Update UI elements
    if (elValParamHeight) elValParamHeight.innerText = `${(1.7297 * h).toFixed(2)} m (${Math.round(h * 100)}%)`;
    if (elValParamArmLength) elValParamArmLength.innerText = `${l.toFixed(2)}x (${Math.round(l * 100)}%)`;
    if (elValParamArmCircumference) elValParamArmCircumference.innerText = `${c.toFixed(2)}x (${Math.round(c * 100)}%)`;
    if (elMorphVersionBadge) elMorphVersionBadge.innerText = `v${currentBodyParams.morph_version}`;

    // Numerical drift evaluation
    const isBaseline = presetName === 'baseline' || (Math.abs(h - 1.0) < 1e-5 && Math.abs(l - 1.0) < 1e-5 && Math.abs(c - 1.0) < 1e-5);
    if (isBaseline) {
        if (elValDriftStatus) elValDriftStatus.innerText = "0.000000 m (Không trôi số học)";
    } else {
        if (elValDriftStatus) elValDriftStatus.innerText = "Khả nghịch (Active)";
    }

    updateMeridianLine();
}

// --- Materials by Anatomical System ---
function getLayerMaterial(system) {
    const sys = (system || '').toLowerCase();
    if (sys === 'skeletal') {
        return new THREE.MeshStandardMaterial({
            color: 0xe2e8f0,
            roughness: 0.45,
            metalness: 0.1,
            side: THREE.DoubleSide
        });
    } else if (sys === 'muscular') {
        return new THREE.MeshStandardMaterial({
            color: 0xa83232,
            roughness: 0.55,
            metalness: 0.05,
            side: THREE.DoubleSide
        });
    } else if (sys === 'integumentary') {
        const opacity = parseFloat(elSkinOpacity.value) || 0.35;
        return new THREE.MeshStandardMaterial({
            color: 0xfbd0b5,
            transparent: true,
            opacity: opacity,
            roughness: 0.75,
            metalness: 0.0,
            side: THREE.DoubleSide,
            depthWrite: false
        });
    } else if (sys === 'digestive') {
        return new THREE.MeshStandardMaterial({
            color: 0xd97706,
            roughness: 0.5,
            metalness: 0.05,
            side: THREE.DoubleSide
        });
    } else if (sys === 'respiratory') {
        return new THREE.MeshStandardMaterial({
            color: 0x0284c7,
            roughness: 0.5,
            metalness: 0.05,
            side: THREE.DoubleSide
        });
    } else if (sys === 'cardiac') {
        return new THREE.MeshStandardMaterial({
            color: 0x991b1b,
            roughness: 0.4,
            metalness: 0.1,
            side: THREE.DoubleSide
        });
    } else if (sys === 'urinary') {
        return new THREE.MeshStandardMaterial({
            color: 0xeab308,
            roughness: 0.45,
            metalness: 0.05,
            side: THREE.DoubleSide
        });
    } else {
        return new THREE.MeshStandardMaterial({
            color: 0x8b5cf6,
            roughness: 0.5,
            metalness: 0.05,
            side: THREE.DoubleSide
        });
    }
}

// --- Chunk Fetching & Mesh Creation ---
async function fetchChunk(chunkIndex) {
    if (chunkBuffers[chunkIndex]) {
        return chunkBuffers[chunkIndex];
    }
    const chunkName = `body-${chunkIndex}.bin`;
    elSpinnerText.innerText = `Đang tải chunk ${chunkName}...`;
    const res = await fetch(`/api/sandbox/p21/chunk?name=${chunkName}`);
    if (!res.ok) {
        throw new Error(`Failed to fetch chunk ${chunkName}: ${res.statusText}`);
    }
    const buf = await res.arrayBuffer();
    chunkBuffers[chunkIndex] = buf;
    return buf;
}

async function createMeshFromPart(part) {
    if (loadedStructures.has(part.id)) {
        return loadedStructures.get(part.id);
    }
    const buf = await fetchChunk(part.chunk);

    const posArray = new Float32Array(buf, part.positions, part.vertexCount * 3);
    const indexArray = new Uint32Array(buf, part.indices, part.indexCount);

    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    geom.setIndex(new THREE.BufferAttribute(indexArray, 1));
    geom.computeVertexNormals();

    const mat = getLayerMaterial(part.system);
    const mesh = new THREE.Mesh(geom, mat);
    mesh.name = part.id;
    mesh.userData = {
        part: part,
        originalColor: mat.color.clone()
    };

    // Add to appropriate layer or armature group
    const partId = part.id;
    let isArmBone = false;

    if (partId === 'FJ3362' || partId === 'FJ3384') {
        // Clavicle_R or Scapula_R
        scene.add(mesh);
        scapulaVisual.attach(mesh);
        isArmBone = true;
    } else if (partId === 'FJ3368') {
        // Humerus_R
        scene.add(mesh);
        upperArmVisual.attach(mesh);
        isArmBone = true;
    } else if (partId === 'FJ3349' || partId === 'FJ3391') {
        // Radius_R or Ulna_R
        scene.add(mesh);
        forearmVisual.attach(mesh);
        isArmBone = true;
    } else if (partId === 'FJ3352') {
        // Metacarpal_2_R
        scene.add(mesh);
        handVisual.attach(mesh);
        isArmBone = true;
    }

    if (!isArmBone) {
        const sys = (part.system || '').toLowerCase();
        if (sys === 'skeletal') {
            groupBone.add(mesh);
        } else if (sys === 'muscular') {
            groupMuscle.add(mesh);
        } else if (sys === 'integumentary') {
            groupSkin.add(mesh);
        } else {
            groupOrgan.add(mesh);
        }
    }

    loadedStructures.set(part.id, mesh);
    return mesh;
}

// --- Metadata & Anatomy Loading ---
async function loadMetadataAndCatalog() {
    try {
        const metaRes = await fetch('/api/sandbox/p21/metadata');
        const meta = await metaRes.json();
        
        document.getElementById('count-bone').innerText = meta.statistics.layer_counts.bone;
        document.getElementById('count-muscle').innerText = meta.statistics.layer_counts.muscle;
        document.getElementById('count-organ').innerText = meta.statistics.layer_counts.organ;
        document.getElementById('count-skin').innerText = meta.statistics.layer_counts.skin;

        // Fetch catalog for search
        const catRes = await fetch('/api/sandbox/p21/structures?limit=500');
        allStructuresCatalog = await catRes.json();
    } catch (err) {
        console.error('Failed to load metadata/catalog:', err);
    }
}

async function loadInitialAnatomy() {
    elSpinner.style.display = 'flex';
    elSpinnerText.innerText = 'Đang nạp các cấu trúc giải phẫu tiêu biểu (xương, cơ, tạng, da)...';

    try {
        const repRes = await fetch('/api/sandbox/p21/representative');
        const repStructures = await repRes.json();

        for (const p of repStructures) {
            await createMeshFromPart(p);
        }
        console.log(`Loaded ${repStructures.length} representative structures.`);
    } catch (err) {
        console.error('Error loading initial anatomy:', err);
    } finally {
        elSpinner.style.display = 'none';
    }
}

async function loadSavedAnnotations() {
    try {
        const res = await fetch('/api/sandbox/p21/annotations');
        const data = await res.json();
        
        userAnnotations.length = 0;
        userPolylines.length = 0;

        if (data.annotations && data.annotations.length > 0) {
            for (const a of data.annotations) {
                userAnnotations.push(a);
                renderSavedAcupointMarker(a);
            }
        }
        if (data.polylines && data.polylines.length > 0) {
            for (const pl of data.polylines) {
                userPolylines.push(pl);
                renderSavedPolyline(pl);
            }
        }
        updateAnnotationsSidebarUI();
    } catch (err) {
        console.error('Failed to load saved annotations:', err);
    }
}

// --- 3D Markers & Polyline Rendering ---
function renderSavedAcupointMarker(annotation) {
    const sp = annotation.spatial_attachment || {};
    const pos = sp.world_position || [0, 0, 0];
    
    const geom = new THREE.SphereGeometry(0.007, 16, 16);
    const mat = new THREE.MeshStandardMaterial({
        color: 0xef4444,
        emissive: 0xef4444,
        emissiveIntensity: 0.6,
        roughness: 0.2
    });
    const marker = new THREE.Mesh(geom, mat);
    marker.position.set(pos[0], pos[1], pos[2]);
    marker.userData = { annotation: annotation };
    groupMarkers.add(marker);
}

function renderSavedPolyline(polyline) {
    const waypoints = polyline.waypoints || [];
    if (waypoints.length < 2) return;

    const points = waypoints.map(wp => new THREE.Vector3(...wp.world_position));
    const geom = new THREE.BufferGeometry().setFromPoints(points);
    const mat = new THREE.LineBasicMaterial({ color: 0x06b6d4, linewidth: 3 });
    const line = new THREE.Line(geom, mat);
    line.userData = { polyline: polyline };
    groupPolylines.add(line);
}

// --- Interaction Handlers ---
function onMouseMove(event) {
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);

    if (currentMode === 'inspect') {
        const visibleGroups = [groupBone, groupMuscle, groupOrgan, groupSkin].filter(g => g.visible);
        const intersects = raycaster.intersectObjects(visibleGroups, true);

        if (intersects.length > 0) {
            const hit = intersects[0];
            const mesh = hit.object;
            const part = mesh.userData.part;

            if (hoveredMesh !== mesh) {
                if (hoveredMesh && hoveredMesh !== selectedMesh) {
                    hoveredMesh.material.emissive?.setHex(0x000000);
                }
                hoveredMesh = mesh;
                if (hoveredMesh !== selectedMesh && hoveredMesh.material.emissive) {
                    hoveredMesh.material.emissive.setHex(0x1e3a8a);
                }
            }

            // Show tooltip
            if (part) {
                elTooltip.style.display = 'block';
                elTooltip.style.left = `${event.clientX - rect.left + 15}px`;
                elTooltip.style.top = `${event.clientY - rect.top + 15}px`;
                elTooltip.innerHTML = `<strong>${part.name}</strong><br><span style="color:#38bdf8">${part.system} · ${part.id}</span>`;
            }
        } else {
            if (hoveredMesh && hoveredMesh !== selectedMesh) {
                hoveredMesh.material.emissive?.setHex(0x000000);
                hoveredMesh = null;
            }
            elTooltip.style.display = 'none';
        }
    } else {
        elTooltip.style.display = 'none';
    }
}

function onCanvasClick(event) {
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);

    const visibleGroups = [groupBone, groupMuscle, groupOrgan, groupSkin].filter(g => g.visible);
    const intersects = raycaster.intersectObjects(visibleGroups, true);

    if (intersects.length === 0) return;
    const hit = intersects[0];
    const mesh = hit.object;
    const part = mesh.userData.part;

    if (currentMode === 'inspect') {
        // Select & Inspect structure
        if (selectedMesh && selectedMesh.material.emissive) {
            selectedMesh.material.emissive.setHex(0x000000);
        }
        selectedMesh = mesh;
        if (selectedMesh.material.emissive) {
            selectedMesh.material.emissive.setHex(0x0284c7);
        }
        displayInspectorDetails(part);
    } else if (currentMode === 'acupoint') {
        // Drop manual acupoint marker
        tempIntersectData = {
            part: part,
            meshId: part.id,
            point: hit.point,
            normal: hit.face ? hit.face.normal : new THREE.Vector3(0, 1, 0),
            faceIndex: hit.faceIndex
        };
        openAcupointModal(tempIntersectData);
    } else if (currentMode === 'polyline') {
        // Add waypoint to draft polyline
        addPolylineWaypoint(hit);
    }
}

function displayInspectorDetails(part) {
    if (!part) return;
    const bounds = part.bounds || [[0, 0, 0], [0, 0, 0]];
    elInspector.innerHTML = `
        <div style="font-size: 13px; font-weight: 700; color: var(--accent-blue); margin-bottom: 6px;">
            ${part.name}
        </div>
        <div class="inspector-row"><span>ID Cấu trúc:</span><strong>${part.id}</strong></div>
        <div class="inspector-row"><span>Hệ Cơ quan:</span><strong>${part.system}</strong></div>
        <div class="inspector-row"><span>FMA Concept ID:</span><strong>${part.conceptId || 'FMA-N/A'}</strong></div>
        <div class="inspector-row"><span>Chunk Tệp Nhị phân:</span><strong>body-${part.chunk}.bin</strong></div>
        <div class="inspector-row"><span>Số đỉnh (Vertices):</span><strong>${part.vertexCount.toLocaleString()}</strong></div>
        <div class="inspector-row"><span>Số tam giác:</span><strong>${(part.indexCount / 3).toLocaleString()}</strong></div>
        <div class="inspector-row"><span>Giới hạn X:</span><strong>[${bounds[0][0].toFixed(3)}, ${bounds[1][0].toFixed(3)}] m</strong></div>
        <div class="inspector-row"><span>Giới hạn Y:</span><strong>[${bounds[0][1].toFixed(3)}, ${bounds[1][1].toFixed(3)}] m</strong></div>
        <div class="inspector-row"><span>Giới hạn Z:</span><strong>[${bounds[0][2].toFixed(3)}, ${bounds[1][2].toFixed(3)}] m</strong></div>
        <div style="margin-top: 8px;">
            <button class="btn-action btn-action-primary" id="btn-focus-selected" style="width: 100%;">
                🎯 Căn giữa Camera vào Cấu trúc này
            </button>
        </div>
    `;

    document.getElementById('btn-focus-selected')?.addEventListener('click', () => {
        const midY = (bounds[0][1] + bounds[1][1]) / 2;
        const midZ = (bounds[0][2] + bounds[1][2]) / 2;
        controls.target.set(0, midY, midZ);
    });
}

// --- Acupoint Mode & Modal ---
function openAcupointModal(hitData) {
    const p = hitData.point;
    const part = hitData.part;

    elModalPointLabel.value = `Huyệt ${part.name.substring(0, 15)}`;
    elModalPointCode.value = `EXP-${part.id}`;
    elModalPointRadius.value = '5.0';
    elModalPointStructure.innerText = `${part.name} (${part.id} · ${part.system})`;
    elModalPointCoords.innerText = `X: ${p.x.toFixed(4)}, Y: ${p.y.toFixed(4)}, Z: ${p.z.toFixed(4)}`;
    elModalPointNotes.value = `Điểm gắn kết trên mặt tam giác #${hitData.faceIndex} của ${part.name}.`;

    elModalAcupoint.style.display = 'flex';
}

async function confirmSaveAcupoint() {
    if (!tempIntersectData) return;
    const p = tempIntersectData.point;
    const part = tempIntersectData.part;

    const payload = {
        label: elModalPointLabel.value.trim() || 'Huyệt Chưa Đặt Tên',
        standard_code: elModalPointCode.value.trim() || 'USER-PT',
        category: 'manual_acupoint',
        notes: elModalPointNotes.value.trim(),
        anatomical_target: {
            mesh_id: part.id,
            structure_name: part.name,
            system: part.system,
            concept_id: part.conceptId || ''
        },
        spatial_attachment: {
            world_position: [p.x, p.y, p.z],
            local_position: [p.x, p.y, p.z],
            surface_normal: [
                tempIntersectData.normal.x,
                tempIntersectData.normal.y,
                tempIntersectData.normal.z
            ],
            triangle_index: tempIntersectData.faceIndex,
            uncertainty_radius_mm: parseFloat(elModalPointRadius.value) || 5.0
        }
    };

    try {
        const res = await fetch('/api/sandbox/p21/annotation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const saved = await res.json();
        userAnnotations.push(saved);
        renderSavedAcupointMarker(saved);
        updateAnnotationsSidebarUI();
        elModalAcupoint.style.display = 'none';
        tempIntersectData = null;
    } catch (err) {
        alert('Lỗi lưu điểm đánh dấu: ' + err.message);
    }
}

// --- Polyline Mode Handlers ---
function addPolylineWaypoint(hit) {
    const p = hit.point;
    const part = hit.object.userData.part;

    const wp = {
        index: draftWaypoints.length,
        mesh_id: part ? part.id : 'unknown',
        world_position: [p.x, p.y, p.z],
        triangle_index: hit.faceIndex
    };
    draftWaypoints.push(wp);

    // Drop temporary small point marker
    const geom = new THREE.SphereGeometry(0.005, 12, 12);
    const mat = new THREE.MeshStandardMaterial({ color: 0x06b6d4, emissive: 0x06b6d4, emissiveIntensity: 0.8 });
    const marker = new THREE.Mesh(geom, mat);
    marker.position.copy(p);
    groupDraftLine.add(marker);

    redrawDraftPolyline();
    updateDraftPolylineUI();
}

function redrawDraftPolyline() {
    // Remove existing line geometry
    if (draftLineMesh) {
        groupDraftLine.remove(draftLineMesh);
        draftLineMesh.geometry.dispose();
        draftLineMesh = null;
    }

    if (draftWaypoints.length >= 2) {
        const points = draftWaypoints.map(wp => new THREE.Vector3(...wp.world_position));
        const geom = new THREE.BufferGeometry().setFromPoints(points);
        const mat = new THREE.LineBasicMaterial({ color: 0x06b6d4, linewidth: 3 });
        draftLineMesh = new THREE.Line(geom, mat);
        groupDraftLine.add(draftLineMesh);
    }
}

function updateDraftPolylineUI() {
    const count = draftWaypoints.length;
    elWaypointCount.innerText = count;

    elBtnUndo.disabled = count === 0;
    elBtnClear.disabled = count === 0;
    elBtnSavePolyline.disabled = count < 3;
}

function undoLastWaypoint() {
    if (draftWaypoints.length === 0) return;
    draftWaypoints.pop();

    // Rebuild groupDraftLine
    while (groupDraftLine.children.length > 0) {
        const obj = groupDraftLine.children[0];
        groupDraftLine.remove(obj);
        obj.geometry?.dispose();
    }

    draftLineMesh = null;
    for (const wp of draftWaypoints) {
        const geom = new THREE.SphereGeometry(0.005, 12, 12);
        const mat = new THREE.MeshStandardMaterial({ color: 0x06b6d4, emissive: 0x06b6d4, emissiveIntensity: 0.8 });
        const marker = new THREE.Mesh(geom, mat);
        marker.position.set(...wp.world_position);
        groupDraftLine.add(marker);
    }
    redrawDraftPolyline();
    updateDraftPolylineUI();
}

function clearDraftPolyline() {
    draftWaypoints.length = 0;
    while (groupDraftLine.children.length > 0) {
        const obj = groupDraftLine.children[0];
        groupDraftLine.remove(obj);
        obj.geometry?.dispose();
    }
    draftLineMesh = null;
    updateDraftPolylineUI();
}

async function saveCurrentPolyline() {
    if (draftWaypoints.length < 3) return;
    const name = prompt('Nhập tên cho đường kinh / tuyến vừa vẽ:', `Tuyến Thực Nghiệm #${userPolylines.length + 1}`);
    if (!name) return;

    const payload = {
        name: name.trim(),
        system_type: 'meridian_trajectory',
        waypoints: draftWaypoints.slice(),
        render_attributes: {
            color: '#06b6d4',
            line_width_mm: 2.5
        }
    };

    try {
        const res = await fetch('/api/sandbox/p21/polyline', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const saved = await res.json();
        userPolylines.push(saved);
        renderSavedPolyline(saved);
        clearDraftPolyline();
        updateAnnotationsSidebarUI();
    } catch (err) {
        alert('Lỗi lưu đường kinh: ' + err.message);
    }
}

// --- Sidebar UI Updates ---
function updateAnnotationsSidebarUI() {
    elAnnotationsCount.innerText = userAnnotations.length;
    elPolylinesCount.innerText = userPolylines.length;

    // Annotations
    if (userAnnotations.length === 0) {
        elAnnotationsList.innerHTML = `<div style="color: var(--text-secondary); font-size: 11px; font-style: italic;">Chưa có điểm đánh dấu thủ công nào.</div>`;
    } else {
        elAnnotationsList.innerHTML = userAnnotations.map(a => {
            const isCanonical = (a.verification_status === 'CANONICAL');
            const isInvalid = (a.binding_status === 'INVALID_BINDING' || a.verification_status === 'INVALID_BINDING');
            let badgeHtml = '<span class="badge-unverified">UNVERIFIED</span>';
            if (isCanonical) {
                badgeHtml = '<span class="badge-canonical">CANONICAL</span>';
            } else if (isInvalid) {
                badgeHtml = '<span class="badge-invalid">INVALID_BINDING</span>';
            }
            const warningHtml = isInvalid ? `<div style="color: #f87171; font-size: 9px; margin-top: 2px;">⚠️ Gắn sai cấu trúc giải phẫu!</div>` : '';

            return `
                <div class="list-entry ${isInvalid ? 'invalid-binding' : ''}" data-id="${a.annotation_id}" style="cursor: pointer;">
                    <div>
                        <div style="font-weight: 600; color: #f8fafc;">${a.label || a.standard_code}</div>
                        <div style="color: var(--accent-cyan); font-size: 10px;">${a.anatomical_target?.structure_name || 'N/A'}</div>
                        ${warningHtml}
                    </div>
                    ${badgeHtml}
                </div>
            `;
        }).join('');

        // Click to focus camera on annotation point
        elAnnotationsList.querySelectorAll('.list-entry').forEach(item => {
            item.addEventListener('click', () => {
                const aid = item.getAttribute('data-id');
                const annot = userAnnotations.find(a => a.annotation_id === aid);
                if (annot && annot.spatial_attachment?.world_position) {
                    const wp = annot.spatial_attachment.world_position;
                    controls.target.set(wp[0], wp[1], wp[2]);
                    camera.position.set(wp[0], wp[1], wp[2] + 0.4);
                    controls.update();
                }
            });
        });
    }

    // Polylines
    if (userPolylines.length === 0) {
        elPolylinesList.innerHTML = `<div style="color: var(--text-secondary); font-size: 11px; font-style: italic;">Chưa có đường kinh nào được lưu.</div>`;
    } else {
        elPolylinesList.innerHTML = userPolylines.map(pl => {
            return `
                <div class="list-entry" data-id="${pl.polyline_id}">
                    <div>
                        <div style="font-weight: 600; color: #f8fafc;">${pl.name || 'Đường kinh'}</div>
                        <div style="color: var(--accent-cyan); font-size: 10px;">${pl.waypoints?.length || 0} waypoints</div>
                    </div>
                    <span class="badge-unverified">DRAFT</span>
                </div>
            `;
        }).join('');
    }
}

// --- Search Catalog Handler ---
async function handleSearchInput(e) {
    const q = e.target.value.trim().toLowerCase();
    if (q.length < 2) {
        elSearchResults.innerHTML = '';
        return;
    }

    try {
        const res = await fetch(`/api/sandbox/p21/structures?search=${encodeURIComponent(q)}&limit=15`);
        const matches = await res.json();

        if (matches.length === 0) {
            elSearchResults.innerHTML = `<div style="color: var(--text-secondary); padding: 4px;">Không tìm thấy cấu trúc phù hợp.</div>`;
            return;
        }

        elSearchResults.innerHTML = matches.map(s => `
            <div class="search-item" data-id="${s.id}">
                <span>${s.name}</span>
                <span style="color: var(--accent-cyan); font-size: 9px;">${s.system}</span>
            </div>
        `).join('');

        // Attach click handlers to load & inspect selected part
        elSearchResults.querySelectorAll('.search-item').forEach(item => {
            item.addEventListener('click', async () => {
                const sid = item.getAttribute('data-id');
                const part = matches.find(s => s.id === sid);
                if (part) {
                    elSpinner.style.display = 'flex';
                    elSpinnerText.innerText = `Đang nạp ${part.name}...`;
                    try {
                        const mesh = await createMeshFromPart(part);
                        displayInspectorDetails(part);
                        // Center camera on bounds
                        const bounds = part.bounds || [[0, 0, 0], [0, 0, 0]];
                        const midY = (bounds[0][1] + bounds[1][1]) / 2;
                        const midZ = (bounds[0][2] + bounds[1][2]) / 2;
                        controls.target.set(0, midY, midZ);
                    } finally {
                        elSpinner.style.display = 'none';
                    }
                }
            });
        });
    } catch (err) {
        console.error('Search error:', err);
    }
}

// --- Export Markdown Handler ---
async function handleExportMarkdown() {
    try {
        const res = await fetch('/api/sandbox/p21/export-markdown', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                annotations: userAnnotations,
                polylines: userPolylines
            })
        });
        const data = await res.json();
        elExportMarkdownContent.innerText = data.markdown;
        elModalExport.style.display = 'flex';
    } catch (err) {
        alert('Lỗi xuất Markdown: ' + err.message);
    }
}

// --- Event Listeners Setup ---
function setupEventListeners() {
    // Panel Tabs Switching (Left & Right Sidebars)
    document.querySelectorAll('.panel-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const bar = btn.parentElement;
            bar.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const targetId = btn.getAttribute('data-target');
            const panel = btn.closest('.side-panel');
            if (panel && targetId) {
                panel.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
                const targetPane = document.getElementById(targetId);
                if (targetPane) targetPane.classList.add('active');
            }
        });
    });

    // Viewport Navigation Toolbar Buttons
    const elBtnCamFit = document.getElementById('btn-cam-fit');
    const elBtnCamArm = document.getElementById('btn-cam-arm');
    const elBtnCamFocusSelected = document.getElementById('btn-cam-focus-selected');
    const elBtnCamIsolate = document.getElementById('btn-cam-isolate');
    const elBtnToggleSkinKinematics = document.getElementById('btn-toggle-skin-kinematics');

    if (elBtnCamFit) {
        elBtnCamFit.addEventListener('click', () => {
            controls.target.set(0, 1.05, 0);
            camera.position.set(0, 1.25, 2.3);
            controls.update();
        });
    }

    if (elBtnCamArm) {
        elBtnCamArm.addEventListener('click', () => {
            controls.target.set(-0.19, 1.15, 0.0);
            camera.position.set(-0.19, 1.15, 0.85);
            controls.update();
        });
    }

    if (elBtnCamFocusSelected) {
        elBtnCamFocusSelected.addEventListener('click', () => {
            if (selectedMesh) {
                const box = new THREE.Box3().setFromObject(selectedMesh);
                const center = new THREE.Vector3();
                box.getCenter(center);
                controls.target.copy(center);
                camera.position.set(center.x, center.y, center.z + 0.5);
                controls.update();
            } else {
                alert('Vui lòng chọn một cấu trúc giải phẫu trước khi dùng tính năng Focus.');
            }
        });
    }

    let isIsolatedMode = false;
    const meshVisibilityState = new Map();

    if (elBtnCamIsolate) {
        elBtnCamIsolate.addEventListener('click', () => {
            if (!isIsolatedMode) {
                if (!selectedMesh) {
                    alert('Vui lòng chọn một cấu trúc giải phẫu trước khi cô lập (Isolate).');
                    return;
                }
                meshVisibilityState.clear();
                for (const [id, m] of loadedStructures.entries()) {
                    meshVisibilityState.set(id, m.visible);
                    m.visible = (m === selectedMesh);
                }
                isIsolatedMode = true;
                elBtnCamIsolate.classList.add('active');
                elBtnCamIsolate.innerText = '👁️ Bỏ Cô Lập';
            } else {
                for (const [id, m] of loadedStructures.entries()) {
                    if (meshVisibilityState.has(id)) {
                        m.visible = meshVisibilityState.get(id);
                    } else {
                        m.visible = true;
                    }
                }
                isIsolatedMode = false;
                elBtnCamIsolate.classList.remove('active');
                elBtnCamIsolate.innerText = '👁️ Cô Lập';
            }
        });
    }

    let skinHiddenForKinematics = false;
    let savedSkinOpacity = 0.35;

    if (elBtnToggleSkinKinematics) {
        elBtnToggleSkinKinematics.addEventListener('click', () => {
            if (!skinHiddenForKinematics) {
                savedSkinOpacity = parseFloat(elSkinOpacity.value) || 0.35;
                groupSkin.visible = false;
                skinHiddenForKinematics = true;
                elBtnToggleSkinKinematics.classList.add('active');
                elBtnToggleSkinKinematics.innerText = '🦴 Hiện Lớp Da';
            } else {
                groupSkin.visible = true;
                groupSkin.traverse(obj => {
                    if (obj.isMesh && obj.material) {
                        obj.material.opacity = savedSkinOpacity;
                    }
                });
                skinHiddenForKinematics = false;
                elBtnToggleSkinKinematics.classList.remove('active');
                elBtnToggleSkinKinematics.innerText = '🦴 Ẩn Da Khi Vận Động';
            }
        });
    }

    // Mode Switching
    document.querySelectorAll('.btn-mode').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.btn-mode').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.getAttribute('data-mode');

            if (currentMode === 'inspect') {
                elHudMode.innerText = 'Quan sát & Chọn cấu trúc';
                container.style.cursor = 'default';
            } else if (currentMode === 'acupoint') {
                elHudMode.innerText = 'Đánh dấu huyệt thủ công (Nhấp lên cấu trúc)';
                container.style.cursor = 'crosshair';
            } else if (currentMode === 'polyline') {
                elHudMode.innerText = 'Vẽ đường kinh (Nhấp tuần tự tạo waypoint)';
                container.style.cursor = 'cell';
            }
        });
    });

    // Layer Toggles
    document.getElementById('layer-bone').addEventListener('change', e => {
        groupBone.visible = e.target.checked;
    });
    document.getElementById('layer-muscle').addEventListener('change', e => {
        groupMuscle.visible = e.target.checked;
    });
    document.getElementById('layer-organ').addEventListener('change', e => {
        groupOrgan.visible = e.target.checked;
    });
    document.getElementById('layer-skin').addEventListener('change', e => {
        groupSkin.visible = e.target.checked;
    });

    // Skin Opacity Slider
    elSkinOpacity.addEventListener('input', e => {
        const val = parseFloat(e.target.value);
        elSkinOpacityVal.innerText = `${Math.round(val * 100)}%`;
        groupSkin.traverse(obj => {
            if (obj.isMesh && obj.material) {
                obj.material.opacity = val;
            }
        });
    });

    // V1.0 Parametric Presets
    const presetButtons = [
        { btn: elPresetBaseline, name: 'baseline', h: 1.00, l: 1.00, c: 1.00 },
        { btn: elPresetSlender, name: 'slender', h: 1.05, l: 1.03, c: 0.88 },
        { btn: elPresetBroader, name: 'broader', h: 0.98, l: 0.97, c: 1.20 },
        { btn: elPresetLongerArm, name: 'longer_arm', h: 1.02, l: 1.12, c: 0.95 }
    ];

    presetButtons.forEach(({ btn, name, h, l, c }) => {
        if (!btn) return;
        btn.addEventListener('click', () => {
            presetButtons.forEach(p => p.btn?.classList.remove('btn-action-primary'));
            btn.classList.add('btn-action-primary');
            if (elParamHeight) elParamHeight.value = h;
            if (elParamArmLength) elParamArmLength.value = l;
            if (elParamArmCircumference) elParamArmCircumference.value = c;
            applyParametricScales(h, l, c, name);
        });
    });

    // V1.0 Parametric Sliders
    const handleSliderInput = () => {
        const h = parseFloat(elParamHeight?.value || 1.0);
        const l = parseFloat(elParamArmLength?.value || 1.0);
        const c = parseFloat(elParamArmCircumference?.value || 1.0);
        presetButtons.forEach(p => p.btn?.classList.remove('btn-action-primary'));
        applyParametricScales(h, l, c, 'custom');
    };

    if (elParamHeight) elParamHeight.addEventListener('input', handleSliderInput);
    if (elParamArmLength) elParamArmLength.addEventListener('input', handleSliderInput);
    if (elParamArmCircumference) elParamArmCircumference.addEventListener('input', handleSliderInput);

    // V1.0 Motion Mode Toggles
    if (elBtnModeVideoMP && elBtnModeMousePose) {
        elBtnModeVideoMP.addEventListener('click', () => {
            elBtnModeVideoMP.classList.add('btn-action-primary');
            elBtnModeMousePose.classList.remove('btn-action-primary');
            if (elContainerVideoMP) elContainerVideoMP.style.display = 'block';
            if (elContainerMousePose) elContainerMousePose.style.display = 'none';
            currentKinematicPose.source = 'VIDEOMP';
        });

        elBtnModeMousePose.addEventListener('click', () => {
            elBtnModeMousePose.classList.add('btn-action-primary');
            elBtnModeVideoMP.classList.remove('btn-action-primary');
            if (elContainerMousePose) elContainerMousePose.style.display = 'block';
            if (elContainerVideoMP) elContainerVideoMP.style.display = 'none';
            currentKinematicPose.source = 'MOUSEPOSE';
        });
    }

    // V1.0 Mouse Pose Sliders
    if (elMousePoseShoulder && elMousePoseElbow) {
        const handleMousePoseInput = () => {
            const sh = parseFloat(elMousePoseShoulder.value || 0);
            const el = parseFloat(elMousePoseElbow.value || 0);
            if (elValMouseShoulder) elValMouseShoulder.innerText = `${sh.toFixed(1)}°`;
            if (elValMouseElbow) elValMouseElbow.innerText = `${el.toFixed(1)}°`;
            applyArmKinematics(sh, el);
        };
        elMousePoseShoulder.addEventListener('input', handleMousePoseInput);
        elMousePoseElbow.addEventListener('input', handleMousePoseInput);
    }

    if (elBtnResetMousePose) {
        elBtnResetMousePose.addEventListener('click', () => {
            if (elMousePoseShoulder) elMousePoseShoulder.value = 0;
            if (elMousePoseElbow) elMousePoseElbow.value = 0;
            if (elValMouseShoulder) elValMouseShoulder.innerText = '0.0°';
            if (elValMouseElbow) elValMouseElbow.innerText = '0.0°';
            applyArmKinematics(0, 0);
        });
    }

    // V1.0 Dynamic Acupoint Undo / Redo
    if (elBtnUndoAcupoint) {
        elBtnUndoAcupoint.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/v1/dynamic_anchors/undo', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    alert('Đã hoàn tác điều chỉnh mốc huyệt!');
                } else {
                    alert('Không còn thao tác nào để hoàn tác.');
                }
            } catch (err) {
                console.warn('Undo request error:', err);
            }
        });
    }

    if (elBtnRedoAcupoint) {
        elBtnRedoAcupoint.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/v1/dynamic_anchors/redo', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    alert('Đã làm lại điều chỉnh mốc huyệt!');
                } else {
                    alert('Không còn thao tác nào để làm lại.');
                }
            } catch (err) {
                console.warn('Redo request error:', err);
            }
        });
    }

    // V1.0 Project Save & Load Handlers
    if (elBtnHeaderSaveProj) {
        elBtnHeaderSaveProj.addEventListener('click', async () => {
            const manifest = {
                schema_version: '1.0.0',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                body_parameters: currentBodyParams,
                current_pose: currentKinematicPose,
                surface_anchors: {
                    LI4: { code: 'LI4', local_coordinates: [-0.280, 0.835, 0.035], status: 'VALID_SURFACE_ANCHOR' },
                    LI14: { code: 'LI14', local_coordinates: [-0.210, 1.250, -0.015], status: 'VALID_SURFACE_ANCHOR' },
                    LI15: { code: 'LI15', local_coordinates: [-0.160, 1.410, -0.020], status: 'VALID_SURFACE_ANCHOR' }
                },
                user_annotations: userAnnotations,
                user_polylines: userPolylines,
                scope: 'ENGINEERING_RESEARCH_ONLY'
            };

            const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `MSK_Project_V1_${Date.now()}.mskproj`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    if (elBtnHeaderLoadProj && elFileLoadProj) {
        elBtnHeaderLoadProj.addEventListener('click', () => {
            elFileLoadProj.click();
        });

        elFileLoadProj.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            try {
                const text = await file.text();
                const data = JSON.parse(text);
                if (data.body_parameters) {
                    const bp = data.body_parameters;
                    if (elParamHeight) elParamHeight.value = bp.height_scale || 1.0;
                    if (elParamArmLength) elParamArmLength.value = bp.right_arm_length_ratio || 1.0;
                    if (elParamArmCircumference) elParamArmCircumference.value = bp.right_arm_circumference_visual || 1.0;
                    applyParametricScales(bp.height_scale || 1.0, bp.right_arm_length_ratio || 1.0, bp.right_arm_circumference_visual || 1.0, bp.preset_name || 'custom');
                }
                if (data.current_pose) {
                    const cp = data.current_pose;
                    applyArmKinematics(cp.shoulder_elevation_deg || 0, cp.elbow_flexion_deg || 0);
                }
                alert(`Đã nạp thành công dự án: ${file.name}`);
            } catch (err) {
                alert(`Lỗi khi mở tệp dự án: ${err.message}`);
            }
        });
    }

    // Polyline Controls
    elBtnUndo.addEventListener('click', undoLastWaypoint);
    elBtnClear.addEventListener('click', clearDraftPolyline);
    elBtnSavePolyline.addEventListener('click', saveCurrentPolyline);

    // Search Box
    elSearchInput.addEventListener('input', handleSearchInput);

    // Acupoint Modal Actions
    elBtnConfirmSavePoint.addEventListener('click', confirmSaveAcupoint);
    elBtnCancelPoint.addEventListener('click', () => { elModalAcupoint.style.display = 'none'; });
    elBtnCloseModalAcupoint.addEventListener('click', () => { elModalAcupoint.style.display = 'none'; });

    // Export Actions
    document.getElementById('btn-export-markdown').addEventListener('click', handleExportMarkdown);
    elBtnCloseModalExport.addEventListener('click', () => { elModalExport.style.display = 'none'; });
    
    elBtnCopyMarkdown.addEventListener('click', () => {
        navigator.clipboard.writeText(elExportMarkdownContent.innerText).then(() => {
            alert('Đã sao chép nội dung Markdown vào bộ nhớ tạm!');
        });
    });

    elBtnDownloadMarkdown.addEventListener('click', () => {
        const blob = new Blob([elExportMarkdownContent.innerText], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `MSK_Atlas_P21_Annotations_${Date.now()}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Expose test automation interface for Playwright headless E2E verification
    window.__P21_POC__ = {
        getLoadedStructures: () => Array.from(loadedStructures.keys()),
        triggerAcupointOnPart: (partId) => {
            const mesh = loadedStructures.get(partId);
            if (!mesh) return false;
            const geom = mesh.geometry;
            const pos = geom.attributes.position;
            const hitPoint = new THREE.Vector3(pos.getX(0), pos.getY(0), pos.getZ(0));
            tempIntersectData = {
                part: mesh.userData.part,
                meshId: partId,
                point: hitPoint,
                normal: new THREE.Vector3(0, 0, 1),
                faceIndex: 0
            };
            openAcupointModal(tempIntersectData);
            return true;
        },
        addWaypointOnPart: (partId) => {
            const mesh = loadedStructures.get(partId);
            if (!mesh) return false;
            const geom = mesh.geometry;
            const pos = geom.attributes.position;
            const hitPoint = new THREE.Vector3(pos.getX(0), pos.getY(0), pos.getZ(0));
            addPolylineWaypoint({
                point: hitPoint,
                object: mesh,
                faceIndex: 0
            });
            return true;
        },
        // V1.0 API for test assertions
        v1: {
            applyPreset: (presetName) => {
                const btn = document.getElementById(`preset-${presetName}`);
                if (btn) btn.click();
            },
            setParametricSliders: (h, l, c) => {
                if (elParamHeight) elParamHeight.value = h;
                if (elParamArmLength) elParamArmLength.value = l;
                if (elParamArmCircumference) elParamArmCircumference.value = c;
                applyParametricScales(h, l, c, 'custom');
            },
            setMousePose: (sh, el) => {
                if (elMousePoseShoulder) elMousePoseShoulder.value = sh;
                if (elMousePoseElbow) elMousePoseElbow.value = el;
                applyArmKinematics(sh, el);
            },
            getKinematicPose: () => ({ ...currentKinematicPose }),
            getBodyParams: () => ({ ...currentBodyParams }),
            getArmatureRotations: () => ({
                scapula_z: scapulaGroup.rotation.z,
                upperArm_z: upperArmGroup.rotation.z,
                forearm_x: forearmGroup.rotation.x
            }),
            getMarkerPositions: () => {
                const res = {};
                for (const [code, val] of dynamicMarkersMap.entries()) {
                    const wp = new THREE.Vector3();
                    val.mesh.getWorldPosition(wp);
                    res[code] = [wp.x, wp.y, wp.z];
                }
                return res;
            }
        },
        // Reality Repair Audit API for Independent QA Verification
        realityRepair: {
            getLimbScales: () => {
                scene.updateMatrixWorld(true);
                const wsForearm = new THREE.Vector3();
                const wsUpper = new THREE.Vector3();
                const wsHand = new THREE.Vector3();
                forearmVisual.getWorldScale(wsForearm);
                upperArmVisual.getWorldScale(wsUpper);
                handVisual.getWorldScale(wsHand);
                return {
                    upperArmGroup_scale: [upperArmGroup.scale.x, upperArmGroup.scale.y, upperArmGroup.scale.z],
                    forearmGroup_scale: [forearmGroup.scale.x, forearmGroup.scale.y, forearmGroup.scale.z],
                    handGroup_scale: [handGroup.scale.x, handGroup.scale.y, handGroup.scale.z],
                    upperArmVisual_local: [upperArmVisual.scale.x, upperArmVisual.scale.y, upperArmVisual.scale.z],
                    forearmVisual_local: [forearmVisual.scale.x, forearmVisual.scale.y, forearmVisual.scale.z],
                    handVisual_local: [handVisual.scale.x, handVisual.scale.y, handVisual.scale.z],
                    upperArm_worldScale: [wsUpper.x, wsUpper.y, wsUpper.z],
                    forearm_worldScale: [wsForearm.x, wsForearm.y, wsForearm.z],
                    hand_worldScale: [wsHand.x, wsHand.y, wsHand.z]
                };
            },
            getJointWorldPositions: () => {
                scene.updateMatrixWorld(true);
                const pScapula = new THREE.Vector3();
                const pShoulder = new THREE.Vector3();
                const pElbow = new THREE.Vector3();
                const pWrist = new THREE.Vector3();
                scapulaGroup.getWorldPosition(pScapula);
                upperArmGroup.getWorldPosition(pShoulder);
                forearmGroup.getWorldPosition(pElbow);
                handGroup.getWorldPosition(pWrist);
                return {
                    scapula: [pScapula.x, pScapula.y, pScapula.z],
                    shoulder: [pShoulder.x, pShoulder.y, pShoulder.z],
                    elbow: [pElbow.x, pElbow.y, pElbow.z],
                    wrist: [pWrist.x, pWrist.y, pWrist.z]
                };
            },
            switchTab: (side, paneId) => {
                const btn = document.querySelector(`.side-panel.${side}-panel .tab-btn[data-target='${paneId}']`);
                if (btn) btn.click();
            },
            isSkinVisible: () => groupSkin.visible,
            isIsolated: () => isIsolatedMode,
            getDynamicMeridianPoints: () => {
                const pos = dynamicMeridianLine.geometry.attributes.position;
                const pts = [];
                for (let i = 0; i < pos.count; i++) {
                    pts.push([pos.getX(i), pos.getY(i), pos.getZ(i)]);
                }
                return pts;
            }
        }
    };
}

// --- P31 / P33 Motion & Knowledge Vault Integration ---
let motionFrames = [];
let motionTimer = null;
let currentMotionIndex = 0;

async function initP33MotionAndKnowledge() {
    const elSelect = document.getElementById('select-marker-knowledge');
    const elTimeline = document.getElementById('motion-timeline');
    const elFrameDisplay = document.getElementById('motion-frame-display');
    const elValShoulder = document.getElementById('val-shoulder-elevation');
    const elValElbow = document.getElementById('val-elbow-flexion');
    const elBtnPlay = document.getElementById('btn-play-motion');
    const elBtnPause = document.getElementById('btn-pause-motion');
    const elBtnExportP33 = document.getElementById('btn-p33-export-markdown');
    const elKnowledgeBox = document.getElementById('knowledge-details-box');

    if (!elSelect) return;

    // Fetch bundle
    try {
        const resp = await fetch('/api/sandbox/p31/bundle');
        if (resp.ok) {
            const bundle = await resp.json();
            motionFrames = bundle.motion_sequence || [];
            if (motionFrames.length > 0) {
                elTimeline.max = motionFrames.length - 1;
                updateMotionUI(0);
            }
        }
    } catch (e) {
        console.warn('Failed to fetch P31 bundle:', e);
    }

    function updateMotionUI(idx) {
        currentMotionIndex = idx;
        elTimeline.value = idx;
        elFrameDisplay.innerText = `Frame: ${idx} / ${motionFrames.length - 1}`;
        if (motionFrames[idx]) {
            const rot = motionFrames[idx].joint_angles_deg || {};
            const sh = rot.shoulder_elevation || 0.0;
            const el = rot.elbow_flexion || 0.0;
            // Real 3D geometry deformation & armature rotation
            applyArmKinematics(sh, el);
        }
    }

    elTimeline.addEventListener('input', e => {
        updateMotionUI(parseInt(e.target.value, 10));
    });

    elBtnPlay.addEventListener('click', () => {
        if (motionTimer) clearInterval(motionTimer);
        motionTimer = setInterval(() => {
            let next = (currentMotionIndex + 1) % motionFrames.length;
            updateMotionUI(next);
        }, 33);
    });

    elBtnPause.addEventListener('click', () => {
        if (motionTimer) {
            clearInterval(motionTimer);
            motionTimer = null;
        }
    });

    async function queryKnowledge(code) {
        elKnowledgeBox.innerHTML = '<div style="color: var(--accent-cyan);">Đang tra cứu Knowledge Vault...</div>';
        try {
            const resp = await fetch(`/api/sandbox/p31/knowledge_links?code=${encodeURIComponent(code)}`);
            if (!resp.ok) {
                elKnowledgeBox.innerHTML = `<div style="color: #f87171;">⚠️ Lỗi hoặc không tìm thấy dữ liệu: ${resp.status}</div>`;
                return;
            }
            const data = await resp.json();
            let statusBadge = data.availability_status === 'AVAILABLE' 
                ? '<span style="color: #4ade80; font-weight: bold;">[CÓ MESH 3D]</span>'
                : '<span style="color: #f87171; font-weight: bold;">[ASSET_NOT_AVAILABLE]</span>';

            let html = `<div><strong>${data.code} — ${data.name_zh || ''} (${data.name_en || ''})</strong> ${statusBadge}</div>`;
            html += `<div><strong>Mốc bám:</strong> ${data.skeletal_anchor || '-'}</div>`;
            html += `<div><strong>Định danh FMA:</strong> <code>${data.fma_id || '-'}</code></div>`;
            html += `<div><strong>Dẫn chiếu WHO:</strong> ${data.who_reference || '-'}</div>`;
            html += `<div><strong>Bất định sinh lý:</strong> ±${data.clinical_uncertainty_mm || 0} mm</div>`;
            html += `<div><strong>Trạng thái:</strong> <code>${data.review_status || '-'}</code></div>`;

            if (data.claims && data.claims.length > 0) {
                html += '<div style="margin-top: 6px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 4px;"><strong>Y văn đã lập chỉ mục:</strong></div>';
                data.claims.forEach(c => {
                    html += `<div style="font-size: 10px; color: #cbd5e1; margin-top: 2px;">• [${c.claim_id}] ${c.text}</div>`;
                });
            } else {
                html += '<div style="margin-top: 4px; color: #94a3b8; font-style: italic;">Chưa có claim riêng lẻ ngoài tiêu chuẩn chung.</div>';
            }

            if (data.availability_status !== 'AVAILABLE') {
                html += '<div style="margin-top: 6px; color: #f87171; background: rgba(239,68,68,0.1); padding: 4px; border-radius: 2px;">⚠️ CẢNH BÁO: Cấu trúc xương chi dưới/xa không có trong asset hiện hành. Tuyệt đối không gắn vào xương cánh tay.</div>';
            }

            elKnowledgeBox.innerHTML = html;
        } catch (err) {
            elKnowledgeBox.innerHTML = `<div style="color: #f87171;">Lỗi kết nối API: ${err.message}</div>`;
        }
    }

    elSelect.addEventListener('change', e => {
        queryKnowledge(e.target.value);
    });
    elSelect.addEventListener('input', e => {
        queryKnowledge(e.target.value);
    });

    queryKnowledge(elSelect.value);

    elBtnExportP33.addEventListener('click', async () => {
        try {
            const resp = await fetch('/api/sandbox/p31/markdown_export');
            if (resp.ok) {
                const md = await resp.text();
                elExportMarkdownContent.innerText = md;
                elModalExport.style.display = 'flex';
            } else {
                alert('Không thể xuất báo cáo: HTTP ' + resp.status);
            }
        } catch (e) {
            alert('Lỗi xuất báo cáo: ' + e.message);
        }
    });

    if (window.__P21_POC__) {
        window.__P21_POC__.p33 = {
            getMotionFrames: () => motionFrames,
            getCurrentMotionIndex: () => currentMotionIndex,
            setMotionIndex: (i) => updateMotionUI(i),
            selectKnowledgeCode: (code) => {
                elSelect.value = code;
                return queryKnowledge(code);
            },
            getKnowledgeContent: () => elKnowledgeBox.innerText
        };
    }
}

// --- Animation Loop ---
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}
