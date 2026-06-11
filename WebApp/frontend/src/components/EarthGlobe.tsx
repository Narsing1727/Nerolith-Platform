import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function EarthGlobe() {
  const mountRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    const scene = new THREE.Scene();

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    const camera = new THREE.PerspectiveCamera(
      45,
      width / height,
      0.1,
      1000
    );

    camera.position.z = 3;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
    });

    renderer.setSize(width, height);

    renderer.setPixelRatio(window.devicePixelRatio);

    renderer.setClearColor(0x000000, 0);

    mountRef.current.appendChild(renderer.domElement);

    // =========================
    // WIREFRAME GLOBE
    // =========================

    const radius = 1;
    const segments = 42;
    const rings = 24;

    const positions: number[] = [];
    const indices: number[] = [];

    for (let lat = 0; lat <= rings; lat++) {
      const theta = (lat / rings) * Math.PI;

      const sinTheta = Math.sin(theta);
      const cosTheta = Math.cos(theta);

      for (let lon = 0; lon <= segments; lon++) {
        const phi = (lon / segments) * Math.PI * 2;

        const x = radius * sinTheta * Math.cos(phi);
        const y = radius * cosTheta;
        const z = radius * sinTheta * Math.sin(phi);

        positions.push(x, y, z);
      }
    }

    for (let lat = 0; lat < rings; lat++) {
      for (let lon = 0; lon < segments; lon++) {
        const a = lat * (segments + 1) + lon;

        const b = a + segments + 1;

        indices.push(a, b);
        indices.push(a, a + 1);
      }
    }

    const globeGeometry = new THREE.BufferGeometry();

    globeGeometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3)
    );

    globeGeometry.setIndex(indices);

    const globeMaterial = new THREE.LineBasicMaterial({
      color: 0x93c5fd,
      transparent: true,
      opacity: 0.9,
    });

    const globe = new THREE.LineSegments(
      globeGeometry,
      globeMaterial
    );

    scene.add(globe);

    // =========================
    // PARTICLE DOTS
    // =========================

    const particleGeometry = new THREE.BufferGeometry();

    const particlePositions: number[] = [];

    const particleCount = 350;

    const phi = Math.PI * (3 - Math.sqrt(5));

    for (let i = 0; i < particleCount; i++) {
      const y = 1 - (i / (particleCount - 1)) * 2;

      const radiusAtY = Math.sqrt(1 - y * y);

      const theta = phi * i;

      const x = Math.cos(theta) * radiusAtY;
      const z = Math.sin(theta) * radiusAtY;

      particlePositions.push(
        x * 1.01,
        y * 1.01,
        z * 1.01
      );
    }

    particleGeometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(
        particlePositions,
        3
      )
    );

    const particleMaterial = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.015,
      transparent: true,
      opacity: 1,
    });

    const particles = new THREE.Points(
      particleGeometry,
      particleMaterial
    );

    scene.add(particles);

    // =========================
    // MOUSE MOVEMENT
    // =========================

    let mouseX = 0;
    let mouseY = 0;

    let targetX = 0;
    let targetY = 0;

    const onMouseMove = (event: MouseEvent) => {
      mouseX = (event.clientX / window.innerWidth - 0.5) * 2;

      mouseY = (event.clientY / window.innerHeight - 0.5) * 2;
    };

    window.addEventListener("mousemove", onMouseMove);

    // =========================
    // RESIZE
    // =========================

    const onResize = () => {
      if (!mountRef.current) return;

      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;

      camera.aspect = w / h;

      camera.updateProjectionMatrix();

      renderer.setSize(w, h);
    };

    window.addEventListener("resize", onResize);

    // =========================
    // ANIMATION
    // =========================

    let t = 0;

    const animate = () => {
      requestAnimationFrame(animate);

      t += 0.003;

      targetX += (mouseX * 0.4 - targetX) * 0.03;

      targetY += (-mouseY * 0.25 - targetY) * 0.03;

      globe.rotation.y = t + targetX;
      globe.rotation.x = targetY;

      particles.rotation.y = t + targetX;
      particles.rotation.x = targetY;

      // floating animation
      const floatY = Math.sin(t * 2) * 0.04;

      globe.position.y = floatY;
      particles.position.y = floatY;

      renderer.render(scene, camera);
    };

    animate();

    // =========================
    // CLEANUP
    // =========================

    return () => {
      window.removeEventListener(
        "mousemove",
        onMouseMove
      );

      window.removeEventListener(
        "resize",
        onResize
      );

      mountRef.current?.removeChild(
        renderer.domElement
      );

      globeGeometry.dispose();
      particleGeometry.dispose();

      globeMaterial.dispose();
      particleMaterial.dispose();

      renderer.dispose();
    };
  }, []);

  return (
    <div className="w-full h-[520px] flex items-center justify-center overflow-hidden">
      <div
        ref={mountRef}
        className="w-full h-full"
      />
    </div>
  );
}