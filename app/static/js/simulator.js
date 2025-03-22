import * as THREE from "three";
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js"; // Import OrbitControls

// Set up the scene, camera, and renderer
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(
  75,
  window.innerWidth / window.innerHeight,
  0.1,
  1000,
);
const renderer = new THREE.WebGLRenderer({
  canvas: document.getElementById("webglCanvas"),
});

renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Create a cube geometry and material (for the rotating cube)
const geometry = new THREE.SphereGeometry();
const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
const cube = new THREE.Mesh(geometry, material);

// Create a cylinder (the column)
const tether_geometry = new THREE.CylinderGeometry(0.1, 0.1, 1, 32);
const tether_material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
const t1 = new THREE.Mesh(tether_geometry, tether_material);
t1.scale.set(0.15, 1, 0.15);
scene.add(t1);

const h1 = new THREE.Mesh(geometry, material);
h1.scale.set(0.05, 0.05, 0.05);
scene.add(h1);

const p1 = new THREE.Mesh(geometry, material);
p1.scale.set(0.15, 0.15, 0.15);
scene.add(p1);

// Set the camera position
camera.position.z = 5;

// Load the HDR texture using RGBELoader
const loader = new RGBELoader();
loader.setDataType(THREE.HalfFloatType); // Set the HDR data type for better performance
loader.load("static/resources/images/meadow.hdr", function (texture) {
  // Set the texture to be used as the scene's background
  texture.mapping = THREE.EquirectangularRefractionMapping;
  scene.background = texture;
  scene.environment = texture; // Set the environment map (useful for reflections)
});

// Initialize OrbitControls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; // Enable smooth damping
controls.dampingFactor = 0.25; // Damping factor (lower = faster)
controls.screenSpacePanning = false; // Prevents panning in screen space
controls.maxPolarAngle = Math.PI / 2; // Limit vertical rotation to avoid flipping the view

// Create reference lines for the X, Y, and Z axes

// X-axis (Red)
const xAxisGeometry = new THREE.BufferGeometry();
const xAxisVertices = new Float32Array([
  -5,
  0,
  0, // Start point (negative X)
  5,
  0,
  0, // End point (positive X)
]);
xAxisGeometry.setAttribute(
  "position",
  new THREE.BufferAttribute(xAxisVertices, 3),
);
const xAxisMaterial = new THREE.LineBasicMaterial({ color: 0xff0000 }); // Red
const xAxisLine = new THREE.Line(xAxisGeometry, xAxisMaterial);
scene.add(xAxisLine);

// Y-axis (Green)
const yAxisGeometry = new THREE.BufferGeometry();
const yAxisVertices = new Float32Array([
  0,
  -5,
  0, // Start point (negative Y)
  0,
  5,
  0, // End point (positive Y)
]);
yAxisGeometry.setAttribute(
  "position",
  new THREE.BufferAttribute(yAxisVertices, 3),
);
const yAxisMaterial = new THREE.LineBasicMaterial({ color: 0x00ff00 }); // Green
const yAxisLine = new THREE.Line(yAxisGeometry, yAxisMaterial);
scene.add(yAxisLine);

// Z-axis (Blue)
const zAxisGeometry = new THREE.BufferGeometry();
const zAxisVertices = new Float32Array([
  0,
  0,
  -5, // Start point (negative Z)
  0,
  0,
  5, // End point (positive Z)
]);
zAxisGeometry.setAttribute(
  "position",
  new THREE.BufferAttribute(zAxisVertices, 3),
);
const zAxisMaterial = new THREE.LineBasicMaterial({ color: 0x0000ff }); // Blue
const zAxisLine = new THREE.Line(zAxisGeometry, zAxisMaterial);
scene.add(zAxisLine);

let t = 0.0;
// Animation loop for the cube rotation
function animate() {
  requestAnimationFrame(animate);
  t += 0.01;

  // Update the controls
  controls.update(); // Only required if controls.enableDamping = true, or if controls.auto-rotation is enabled

  // Rotate the cube for animation (optional if you want it to spin)
  // Assuming t is predefined, for example, t could be updated like so:

  const head = new THREE.Vector3(
    Math.cos(t) + Math.cos(-3 * t),
    Math.sin(t) + Math.sin(-3 * t),
    0,
  );
  const handle = new THREE.Vector3(Math.cos(t), Math.sin(t), 0);
  // Calculate the direction vector (from handle to head)
  const direction = new THREE.Vector3().subVectors(head, handle);

  // Calculate the distance (height) between handle and head
  const distance = direction.length();

  // Normalize the direction vector
  direction.normalize();

  // Position the column at the midpoint between handle and head
  t1.position.copy(handle).add(head).multiplyScalar(0.5);

  // To correctly orient the column, we need to rotate it so that it aligns with the direction vector
  // First, find the axis of rotation (the cross product of the z-axis and the direction vector)
  const axis = new THREE.Vector3(0, 1, 0); // This assumes the cylinder's "up" direction should be along the Y-axis (default for CylinderGeometry)
  const cross = new THREE.Vector3().crossVectors(axis, direction);

  // Calculate the angle between the z-axis and the direction vector
  const angle = Math.acos(axis.dot(direction));

  // Alternatively, if the axis is already correct (i.e., you don't need a cross product), you can use lookAt as a simpler approach:
  t1.lookAt(head); // This will directly orient the column towards the 'head' point
  t1.rotateOnAxis(new THREE.Vector3(1, 0, 0), Math.PI / 2);

  h1.position.set(Math.cos(t), Math.sin(t), 0);
  p1.position.set(
    Math.cos(t) + Math.cos(-3 * t),
    Math.sin(t) + Math.sin(-3 * t),
    0,
  );

  renderer.render(scene, camera);
}

// Start the animation
animate();

// Adjust canvas size on window resize
window.addEventListener("resize", () => {
  renderer.setSize(window.innerWidth, window.innerHeight);
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
});
