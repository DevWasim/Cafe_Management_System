// Scene, Camera, Renderer
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const canvas = document.querySelector('#webgl-bg');
const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });

renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);

// Particles
const geometry = new THREE.BufferGeometry();
const particlesCount = 700;
const posArray = new Float32Array(particlesCount * 3);

for (let i = 0; i < particlesCount * 3; i++) {
    // Spread particles in a wide area
    posArray[i] = (Math.random() - 0.5) * 15;
}

geometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));

// Material - Gold Dust
const material = new THREE.PointsMaterial({
    size: 0.03,
    color: 0xc5a059, // Gold
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending
});

// Mesh
const particlesMesh = new THREE.Points(geometry, material);
scene.add(particlesMesh);

// Lighting (Ambient)
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

camera.position.z = 3;

// Mouse Interaction
let mouseX = 0;
let mouseY = 0;

document.addEventListener('mousemove', (event) => {
    mouseX = event.clientX;
    mouseY = event.clientY;
});

// Animation Loop
const clock = new THREE.Clock();

function animate() {
    const elapsedTime = clock.getElapsedTime();

    // Constant smooth rotation
    particlesMesh.rotation.y = -0.05 * elapsedTime;
    particlesMesh.rotation.x = 0.02 * elapsedTime; // Slight tilt

    // Interactive subtle movement based on mouse
    // We map mouse position to rotation offsets
    const targetX = mouseY * 0.0001;
    const targetY = mouseX * 0.0001;

    particlesMesh.rotation.x += 0.05 * (targetX - particlesMesh.rotation.x);
    particlesMesh.rotation.y += 0.05 * (targetY - particlesMesh.rotation.y);

    renderer.render(scene, camera);
    window.requestAnimationFrame(animate);
}

animate();

// Resize Handler
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
