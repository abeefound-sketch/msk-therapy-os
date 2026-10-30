/**
 * MSK-Therapy-OS - 3D Musculoskeletal Education Viewer (Phase P13-C)
 * 
 * Powered by localized Three.js r160.
 * Operates strictly within an isolated WebGL context.
 * Hardware optimized for Intel Core i7-5600U / Intel HD Graphics 5500.
 * 
 * Licensing:
 * - Code: MIT License
 * - Model (anatomy.glb): CC BY-SA 2.1 JP (BodyParts3D via DBCLS & Z-Anatomy)
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
            modelUrl: './models/anatomy.glb',
            onMeshSelected: null,
            onLoadProgress: null,
            onLoadComplete: null,
            onError: null
        }, options);

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.modelRoot = null;
        this.meshes = new Map(); // name -> THREE.Mesh
        this.materials = new Map(); // name -> original THREE.Material

        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2(-999, -999);
        this.hoveredMesh = null;
        this.selectedMeshName = null;

        this.isAnimating = false;
        this.animationFrameId = null;
        this.lastFrameTime = performance.now();
        this.frameCount = 0;
        this.fps = 60;
        this.fpsCallback = null;

        // Default anatomical palette
        this.colors = {
            muscleDefault: 0xb55a5a,
            muscleHighlighted: 0x38bdf8,
            muscleInhibited: 0x94a3b8,
            muscleHypertonic: 0xf43f5e,
            boneDefault: 0xded8ce,
            dimmed: 0x334155
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
        this.camera.position.set(0.0, 1.45, 1.15); // Focused on chest and shoulder complex

        // 3. Renderer with powerPreference: default for integrated Intel HD 5500
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            powerPreference: 'default',
            alpha: false
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5)); // Limit to 1.5x on integrated GPU
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.container.appendChild(this.renderer.domElement);

        // 4. Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
        this.scene.add(ambientLight);

        const dirLightFront = new THREE.DirectionalLight(0xffffff, 1.2);
        dirLightFront.position.set(1.5, 3.0, 2.0);
        this.scene.add(dirLightFront);

        const dirLightBack = new THREE.DirectionalLight(0x90b0e0, 0.6);
        dirLightBack.position.set(-1.5, 2.0, -2.0);
        this.scene.add(dirLightBack);

        // 5. Controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.08;
        this.controls.target.set(0.0, 1.40, 0.0); // Center of thorax / glenohumeral level
        this.controls.minDistance = 0.3;
        this.controls.maxDistance = 3.5;
        this.controls.update();
    }

    _bindEvents() {
        window.addEventListener('resize', () => this._onResize());

        const canvas = this.renderer.domElement;
        canvas.addEventListener('mousemove', (e) => this._onMouseMove(e));
        canvas.addEventListener('click', (e) => this._onClick(e));

        // CPU/GPU throttler: suspend render loop when tab/window is hidden
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

    loadModel() {
        const loader = new GLTFLoader();

        if (typeof this.options.onLoadProgress === 'function') {
            this.options.onLoadProgress(10, 'Initializing 3D GLTF Loader...');
        }

        loader.load(
            this.options.modelUrl,
            (gltf) => {
                this.modelRoot = gltf.scene;

                this.modelRoot.traverse((child) => {
                    if (child.isMesh) {
                        // Recompute vertex normals for stripped GLTF buffers
                        if (!child.geometry.attributes.normal) {
                            child.geometry.computeVertexNormals();
                        }

                        // Clone material to enable per-muscle color highlights
                        const originalMat = child.material.clone();
                        originalMat.roughness = 0.55;
                        originalMat.metalness = 0.10;
                        child.material = originalMat;

                        const name = child.name || child.id.toString();
                        this.meshes.set(name, child);
                        this.materials.set(name, originalMat);
                    }
                });

                // Center model if needed
                this.scene.add(this.modelRoot);

                if (typeof this.options.onLoadComplete === 'function') {
                    this.options.onLoadComplete({
                        meshCount: this.meshes.size,
                        model: this.modelRoot
                    });
                }

                this.startAnimation();
            },
            (xhr) => {
                if (xhr.total && xhr.total > 0) {
                    const pct = Math.round((xhr.loaded / xhr.total) * 100);
                    if (typeof this.options.onLoadProgress === 'function') {
                        this.options.onLoadProgress(pct, `Loading anatomical geometry (${pct}%)...`);
                    }
                }
            },
            (error) => {
                console.error('[AnatomyViewer] GLTF Load Error:', error);
                if (typeof this.options.onError === 'function') {
                    this.options.onError(error);
                }
            }
        );
    }

    startAnimation() {
        if (this.isAnimating) return;
        this.isAnimating = true;
        this.lastFrameTime = performance.now();

        const renderLoop = (time) => {
            if (!this.isAnimating) return;

            // Compute FPS
            this.frameCount++;
            if (time - this.lastFrameTime >= 1000) {
                this.fps = Math.round((this.frameCount * 1000) / (time - this.lastFrameTime));
                this.frameCount = 0;
                this.lastFrameTime = time;
                if (this.fpsCallback) {
                    this.fpsCallback(this.fps);
                }
            }

            // Update controls
            if (this.controls) {
                this.controls.update();
            }

            // Raycasting for interactive hover
            if (this.mouse.x !== -999 && this.camera && this.modelRoot) {
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
            this.camera.position.set(0.25, 1.48, 0.75);
            this.controls.target.set(0.08, 1.40, 0.0);
        } else if (focusArea === 'full') {
            this.camera.position.set(0.0, 1.20, 2.20);
            this.controls.target.set(0.0, 1.0, 0.0);
        } else if (focusArea === 'scapula') {
            this.camera.position.set(0.35, 1.48, -0.70); // View from posterior
            this.controls.target.set(0.12, 1.40, 0.0);
        }
        this.controls.update();
    }

    highlightMuscles(muscleNames, colorHex = null) {
        const highlightColor = new THREE.Color(colorHex || this.colors.muscleHighlighted);
        const targetSet = new Set(muscleNames);

        this.meshes.forEach((mesh, name) => {
            if (targetSet.has(name) || targetSet.has(name.toLowerCase())) {
                mesh.material.color.copy(highlightColor);
                mesh.material.opacity = 1.0;
                mesh.material.transparent = false;
            } else if (name.includes('bone') || name.includes('skeleton') || name.includes('clavicle') || name.includes('scapula')) {
                mesh.material.color.setHex(this.colors.boneDefault);
                mesh.material.opacity = 0.85;
                mesh.material.transparent = true;
            } else {
                mesh.material.color.setHex(this.colors.muscleDefault);
                mesh.material.opacity = targetSet.size > 0 ? 0.30 : 0.95;
                mesh.material.transparent = targetSet.size > 0;
            }
        });
    }

    selectMuscle(muscleName) {
        this.selectedMeshName = muscleName;
        this.highlightMuscles([muscleName], this.colors.muscleHighlighted);
    }

    clearHighlights() {
        this.selectedMeshName = null;
        this.highlightMuscles([]);
    }

    setLayerVisibility(layer) {
        // 'all', 'muscles', 'bones', 'anterior', 'posterior'
        this.meshes.forEach((mesh, name) => {
            const lower = name.toLowerCase();
            const isBone = lower.includes('bone') || lower.includes('clavicle') || lower.includes('scapula') || lower.includes('humerus');
            const isAnterior = lower.includes('pectoralis') || lower.includes('anterior') || lower.includes('rectus');
            const isPosterior = lower.includes('trapezius') || lower.includes('rhomboid') || lower.includes('latissimus') || lower.includes('infraspinatus');

            if (layer === 'all') {
                mesh.visible = true;
            } else if (layer === 'bones') {
                mesh.visible = isBone;
            } else if (layer === 'muscles') {
                mesh.visible = !isBone;
            } else if (layer === 'anterior') {
                mesh.visible = isBone || isAnterior;
            } else if (layer === 'posterior') {
                mesh.visible = isBone || isPosterior;
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
