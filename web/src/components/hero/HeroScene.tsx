"use client";

import { Float } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

import { useResolvedTheme } from "@/lib/useResolvedTheme";

type Palette = { brand: string; soft: string; neutral: string; deep: string; light: string };

/** Scene colors come from the design tokens, so the hero follows the theme. */
function readPalette(): Palette {
  const css = getComputedStyle(document.documentElement);
  const token = (name: string) => css.getPropertyValue(name).trim();
  return {
    brand: token("--brand"),
    soft: token("--brand-soft"),
    neutral: token("--field"),
    deep: token("--raised"),
    // Lights must be bright in both themes: the lighter of the ink and page colors.
    light: token(document.documentElement.getAttribute("data-theme") === "light" ? "--page" : "--ink"),
  };
}

/** A curly brace as a low-poly tube, echoing the goat's horns in the logo. */
function braceGeometry(): THREE.TubeGeometry {
  const points = [
    [0.42, 1.05],
    [0.12, 0.98],
    [0.04, 0.72],
    [0.04, 0.3],
    [-0.08, 0.08],
    [-0.32, 0],
    [-0.08, -0.08],
    [0.04, -0.3],
    [0.04, -0.72],
    [0.12, -0.98],
    [0.42, -1.05],
  ].map(([x, y]) => new THREE.Vector3(x, y, 0));
  return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), 40, 0.1, 6, false);
}

function Shapes({ palette }: { palette: Palette }) {
  const group = useRef<THREE.Group>(null);
  const brace = useMemo(() => braceGeometry(), []);

  // Lean gently toward the cursor.
  useFrame((state, delta) => {
    if (!group.current) return;
    const ease = 1 - Math.exp(-delta * 2.5);
    group.current.rotation.y += (state.pointer.x * 0.35 - group.current.rotation.y) * ease;
    group.current.rotation.x += (-state.pointer.y * 0.2 - group.current.rotation.x) * ease;
  });

  const matte = (color: string) => (
    <meshStandardMaterial color={color} roughness={0.62} metalness={0.05} flatShading />
  );

  return (
    <group ref={group}>
      <Float speed={1.1} rotationIntensity={0.35} floatIntensity={0.5}>
        <group position={[-0.45, 0.15, 0.4]} rotation={[0.1, 0.35, 0.08]}>
          <mesh geometry={brace} position={[-0.55, 0, 0]}>
            {matte(palette.brand)}
          </mesh>
          <mesh geometry={brace} position={[0.55, 0, 0]} scale={[-1, 1, 1]}>
            {matte(palette.brand)}
          </mesh>
        </group>
      </Float>
      <Float speed={0.8} rotationIntensity={0.6} floatIntensity={0.7}>
        <mesh position={[1.55, 0.95, -0.6]} rotation={[0.4, 0.2, 0]}>
          <icosahedronGeometry args={[0.62, 0]} />
          {matte(palette.soft)}
        </mesh>
      </Float>
      <Float speed={0.9} rotationIntensity={0.5} floatIntensity={0.6}>
        <mesh position={[1.35, -1.05, 0.1]} rotation={[0.9, 0.3, 0.2]}>
          <torusGeometry args={[0.46, 0.15, 6, 14]} />
          {matte(palette.neutral)}
        </mesh>
      </Float>
      <Float speed={0.7} rotationIntensity={0.4} floatIntensity={0.5}>
        <mesh position={[-1.9, -1.0, -0.8]}>
          <dodecahedronGeometry args={[0.5, 0]} />
          {matte(palette.neutral)}
        </mesh>
      </Float>
      <Float speed={1.0} rotationIntensity={0.7} floatIntensity={0.5}>
        <mesh position={[-1.75, 1.15, -1.2]} rotation={[0.5, 0.5, 0]}>
          <octahedronGeometry args={[0.38, 0]} />
          {matte(palette.soft)}
        </mesh>
      </Float>
    </group>
  );
}

export default function HeroScene({ active }: { active: boolean }) {
  const theme = useResolvedTheme();
  // Re-read the tokens whenever the theme changes.
  const palette = useMemo(() => {
    void theme;
    return readPalette();
  }, [theme]);

  return (
    <Canvas
      frameloop={active ? "always" : "never"}
      dpr={[1, 1.5]}
      camera={{ position: [0, 0, 6.2], fov: 42 }}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
      aria-hidden="true"
    >
      <ambientLight intensity={0.55} color={palette.light} />
      <directionalLight position={[-3, 4, 5]} intensity={1.6} color={palette.light} />
      <pointLight position={[3, -1, 3]} intensity={18} color={palette.soft} />
      <pointLight position={[-4, -2, -2]} intensity={10} color={palette.brand} />
      <Shapes palette={palette} />
    </Canvas>
  );
}
