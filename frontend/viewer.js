import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

let scene, camera, renderer, controls, model;
let modelSize = 50;

init();
animate();

function init() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xffffff);

  camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    5000
  );
  camera.position.set(0, 100, 0);
  camera.lookAt(0, 0, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  document.getElementById('viewer').appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xaaaaaa));
  const dir = new THREE.DirectionalLight(0xffffff, 0.8);
  dir.position.set(30, 40, 30);
  scene.add(dir);

  // CORRECT CONSTRUCTOR
  controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 0, 0);
  controls.update();

  loadModel();
  window.addEventListener('resize', onResize);
}

function loadModel() {
  const loader = new GLTFLoader();
  const draco = new DRACOLoader();
  draco.setDecoderPath('https://www.gstatic.com/draco/v1/decoders/');
  loader.setDRACOLoader(draco);

  loader.load('/output/model.glb', (gltf) => {
    model = gltf.scene;

    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    model.position.sub(center);

    const size = box.getSize(new THREE.Vector3());
    modelSize = Math.max(size.x, size.y, size.z);

    scene.add(model);
    setTopView();
    document.getElementById('loading').style.display = 'none';
  });
}

function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function setTopView() {
  camera.position.set(0, modelSize * 1.6, 0);
  camera.lookAt(0, 0, 0);
  controls.update();
}

function setFrontView() {
  camera.position.set(0, 0, modelSize * 1.6);
  camera.lookAt(0, 0, 0);
  controls.update();
}

function setSideView() {
  camera.position.set(modelSize * 1.6, 0, 0);
  camera.lookAt(0, 0, 0);
  controls.update();
}

function set3DView() {
  camera.position.set(modelSize, modelSize, modelSize);
  camera.lookAt(0, 0, 0);
  controls.update();
}

function setBackView() {
  camera.position.set(0, 0, -modelSize * 1.6);
  camera.lookAt(0, 0, 0);
  controls.update();
}

// Expose functions to global scope for button onclick handlers
window.setTopView = setTopView;
window.setFrontView = setFrontView;
window.setSideView = setSideView;
window.set3DView = set3DView;
window.setBackView = setBackView;
