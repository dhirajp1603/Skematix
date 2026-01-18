/**
 * FLOOR PLAN 3D VIEWER
 * 
 * Three.js-based 3D rendering of floor plans from binary masks.
 * 
 * Features:
 * - ES Module imports (proper Three.js setup)
 * - OrbitControls for navigation
 * - Proper lighting (ambient + directional)
 * - BufferGeometry for performance
 * - Responsive canvas sizing
 * 
 * Usage:
 * - Supply image path to FloorPlanViewer
 * - Call viewer.init() to set up scene
 * - Viewer handles rendering automatically
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import FloorPlanGeometryGenerator from './geometry-generator.js';

export class FloorPlanViewer {
    constructor(containerSelector, options = {}) {
        this.container = document.querySelector(containerSelector);
        this.options = {
            imageSource: options.imageSource || 'output/test_plan_walls_mask_final.png',
            backgroundColor: options.backgroundColor || 0x1a1a2e,
            wallColor: options.wallColor || 0x4a9eff,
            floorColor: options.floorColor || 0x2c3e50,
            ...options
        };
        
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.wallMesh = null;
        this.generator = null;
        this.isInitialized = false;
    }

    /**
     * Initialize the 3D scene
     */
    async init() {
        try {
            console.log('[FloorPlanViewer] Initializing...');
            
            // Create scene
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(this.options.backgroundColor);
            
            // Create camera
            this._setupCamera();
            
            // Create renderer
            this._setupRenderer();
            
            // Setup lighting
            this._setupLighting();
            
            // Setup controls
            this._setupControls();
            
            // Load and generate geometry
            await this._generateAndAddWalls();
            
            // Add reference grid
            this._addGrid();
            
            // Handle window resize
            window.addEventListener('resize', () => this._onWindowResize());
            
            // Start render loop
            this._startRenderLoop();
            
            this.isInitialized = true;
            console.log('[FloorPlanViewer] Initialization complete!');
            
        } catch (error) {
            console.error('[FloorPlanViewer] Initialization failed:', error);
            this._showError(error.message);
            throw error;
        }
    }

    /**
     * Setup perspective camera
     */
    _setupCamera() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        // Use isometric view with slight angle
        const fov = 60;
        const aspect = width / height;
        const near = 0.1;
        const far = 1000;
        
        this.camera = new THREE.PerspectiveCamera(fov, aspect, near, far);
        
        // Position camera above and angled down
        this.camera.position.set(15, 12, 15);
        this.camera.lookAt(0, 0, 0);
        
        console.log('[FloorPlanViewer] Camera setup complete');
    }

    /**
     * Setup WebGL renderer
     */
    _setupRenderer() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: false,
            precision: 'highp'
        });
        
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFShadowShadowMap;
        
        this.container.appendChild(this.renderer.domElement);
        
        console.log('[FloorPlanViewer] Renderer setup complete');
    }

    /**
     * Setup lighting
     */
    _setupLighting() {
        // Ambient light (fills shadows)
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);
        
        // Directional light (sun-like)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 20, 10);
        directionalLight.target.position.set(0, 0, 0);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.left = -50;
        directionalLight.shadow.camera.right = 50;
        directionalLight.shadow.camera.top = 50;
        directionalLight.shadow.camera.bottom = -50;
        
        this.scene.add(directionalLight);
        
        // Add a fill light from opposite side (reduces contrast)
        const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
        fillLight.position.set(-10, 10, -10);
        this.scene.add(fillLight);
        
        console.log('[FloorPlanViewer] Lighting setup complete');
    }

    /**
     * Setup OrbitControls
     */
    _setupControls() {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        
        // Configure controls
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.enableRotate = true;
        this.controls.enableZoom = true;
        this.controls.enablePan = true;
        this.controls.autoRotate = false;
        this.controls.autoRotateSpeed = 0;
        
        // Limit rotation
        this.controls.minPolarAngle = Math.PI / 6; // 30 degrees from bottom
        this.controls.maxPolarAngle = Math.PI - 0.1; // Just above horizon
        
        // Limit zoom
        this.controls.minDistance = 5;
        this.controls.maxDistance = 100;
        
        console.log('[FloorPlanViewer] Controls setup complete');
    }

    /**
     * Load geometry and add walls to scene
     */
    async _generateAndAddWalls() {
        console.log('[FloorPlanViewer] Generating geometry from image...');
        
        this.generator = new FloorPlanGeometryGenerator(
            this.options.imageSource,
            {
                wallHeight: 2.5,
                scale: 0.01,
                wallThickness: 0.2
            }
        );
        
        const geometry = await this.generator.generate();
        
        if (!geometry) {
            throw new Error('Failed to generate geometry');
        }
        
        // Create material
        const material = new THREE.MeshPhongMaterial({
            color: this.options.wallColor,
            emissive: 0x333333,
            shininess: 30,
            side: THREE.DoubleSide
        });
        
        // Create mesh
        this.wallMesh = new THREE.Mesh(geometry, material);
        this.wallMesh.castShadow = true;
        this.wallMesh.receiveShadow = true;
        this.scene.add(this.wallMesh);
        
        // Add floor plane
        this._addFloorPlane();
        
        console.log('[FloorPlanViewer] Walls added to scene');
    }

    /**
     * Add floor reference plane
     */
    _addFloorPlane() {
        const floorGeometry = new THREE.PlaneGeometry(100, 100);
        const floorMaterial = new THREE.MeshStandardMaterial({
            color: this.options.floorColor,
            emissive: 0x000000,
            roughness: 0.8,
            metalness: 0.1
        });
        
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = -0.01; // Slightly below to avoid z-fighting
        floor.receiveShadow = true;
        
        this.scene.add(floor);
    }

    /**
     * Add grid helper for reference
     */
    _addGrid() {
        const gridSize = 50;
        const gridDivisions = 50;
        const gridHelper = new THREE.GridHelper(gridSize, gridDivisions, 0x444444, 0x222222);
        gridHelper.position.y = -0.02;
        this.scene.add(gridHelper);
    }

    /**
     * Handle window resize
     */
    _onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
    }

    /**
     * Render loop
     */
    _startRenderLoop() {
        const animate = () => {
            requestAnimationFrame(animate);
            
            // Update controls
            if (this.controls) {
                this.controls.update();
            }
            
            // Render scene
            this.renderer.render(this.scene, this.camera);
        };
        
        animate();
    }

    /**
     * Display error message
     */
    _showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: absolute;
            top: 10px;
            left: 10px;
            background: #ff4444;
            color: white;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            max-width: 400px;
            z-index: 1000;
        `;
        errorDiv.textContent = `Error: ${message}`;
        this.container.appendChild(errorDiv);
    }

    /**
     * Get scene statistics
     */
    getStats() {
        return {
            renderer: {
                size: this.renderer.getSize(new THREE.Vector2()),
                pixelRatio: window.devicePixelRatio
            },
            camera: {
                position: this.camera.position,
                fov: this.camera.fov
            },
            wallMesh: this.wallMesh ? {
                vertices: this.wallMesh.geometry.getAttribute('position').count,
                triangles: this.wallMesh.geometry.getIndex().count / 3
            } : null
        };
    }

    /**
     * Set camera to different presets
     */
    setCameraPreset(preset) {
        const presets = {
            topDown: { pos: [0, 25, 0.1], target: [0, 0, 0] },
            isometric: { pos: [20, 15, 20], target: [0, 0, 0] },
            sideView: { pos: [30, 10, 0], target: [0, 0, 0] },
            frontView: { pos: [0, 10, 30], target: [0, 0, 0] }
        };
        
        if (presets[preset]) {
            const { pos, target } = presets[preset];
            this.camera.position.set(...pos);
            this.camera.lookAt(...target);
            this.controls.target.set(...target);
            this.controls.update();
        }
    }
}

export default FloorPlanViewer;
