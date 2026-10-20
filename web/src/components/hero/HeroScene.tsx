"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

import { useResolvedTheme } from "@/lib/useResolvedTheme";

type Palette = {
  page: string;
  rockLow: string;
  rockHigh: string;
  snow: string;
  brand: string;
  soft: string;
};

/** Scene colors come from the design tokens, so the hero follows the theme. */
function readPalette(): Palette {
  const css = getComputedStyle(document.documentElement);
  const token = (name: string) => css.getPropertyValue(name).trim();
  return {
    page: token("--page"),
    rockLow: token("--rock-low"),
    rockHigh: token("--rock-high"),
    snow: token("--snow"),
    brand: token("--brand"),
    soft: token("--brand-soft"),
  };
}

// Peaks as (x, z, height, spread). The tallest is the summit the trail climbs to.
const PEAKS: [number, number, number, number][] = [
  [1.5, -0.7, 2.7, 1.15],
  [-1.1, -1.6, 1.85, 1.0],
  [3.7, -1.9, 1.6, 0.95],
  [-3.4, -2.4, 1.3, 1.1],
  [0.2, -3.2, 1.4, 1.3],
];
const SNOW_LINE = 1.85;

function height(x: number, z: number): number {
  let h = 0;
  for (const [px, pz, ph, spread] of PEAKS) {
    const d2 = ((x - px) ** 2 + (z - pz) ** 2) / (spread * spread);
    h = Math.max(h, ph * Math.exp(-d2));
  }
  // Ridges and scree: deterministic ripples, so every render is the same mountain.
  h += 0.12 * Math.sin(x * 2.3 + z * 1.7) * Math.cos(z * 2.9 - x * 0.6);
  h += 0.06 * Math.sin(x * 5.1 - z * 3.3);
  return Math.max(0, h - 0.05);
}

/** A faceted terrain: every triangle one flat color, like the low-poly goat. */
function terrainGeometry(palette: Palette): THREE.BufferGeometry {
  const plane = new THREE.PlaneGeometry(11, 6, 34, 18).toNonIndexed();
  plane.rotateX(-Math.PI / 2);
  plane.translate(0.4, 0, -1.4);
  const position = plane.getAttribute("position");
  for (let i = 0; i < position.count; i++) {
    position.setY(i, height(position.getX(i), position.getZ(i)));
  }
  const low = new THREE.Color(palette.rockLow);
  const high = new THREE.Color(palette.rockHigh);
  const snow = new THREE.Color(palette.snow);
  const colors = new Float32Array(position.count * 3);
  const color = new THREE.Color();
  for (let face = 0; face < position.count; face += 3) {
    const y = (position.getY(face) + position.getY(face + 1) + position.getY(face + 2)) / 3;
    if (y > SNOW_LINE) color.copy(snow);
    else color.copy(low).lerp(high, Math.min(1, y / SNOW_LINE));
    for (let v = 0; v < 3; v++) color.toArray(colors, (face + v) * 3);
  }
  plane.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  plane.computeVertexNormals();
  return plane;
}

/** The route from the valley to the summit, following the ground. */
function trailCurve(): THREE.CatmullRomCurve3 {
  const guide = new THREE.CatmullRomCurve3(
    // Switchbacks up the summit's front face, the way a real trail climbs.
    [
      [-3.4, 1.9],
      [-1.9, 1.5],
      [-0.7, 1.05],
      [0.9, 0.85],
      [1.7, 0.55],
      [0.7, 0.25],
      [0.55, -0.05],
      [1.75, -0.25],
      [1.5, -0.7],
    ].map(([x, z]) => new THREE.Vector3(x, 0, z)),
    false,
    "centripetal", // no overshoot loops at the bends
  );
  const points = guide.getSpacedPoints(160).map((p) => new THREE.Vector3(p.x, height(p.x, p.z) + 0.04, p.z));
  return new THREE.CatmullRomCurve3(points, false, "centripetal");
}

const TRAIL_SEGMENTS = 320;
const RADIAL = 5;
const DRAW_SECONDS = 2.6;
// Where the waypoints sit along the trail: the two open tasks, then the summit.
const WAYPOINTS = [0.3, 0.62, 1];

function Mountain({ palette }: { palette: Palette }) {
  const group = useRef<THREE.Group>(null);
  const trail = useRef<THREE.Mesh>(null);
  const markers = useRef<(THREE.Mesh | null)[]>([]);
  const started = useRef<number | null>(null);
  const terrain = useMemo(() => terrainGeometry(palette), [palette]);
  const curve = useMemo(() => trailCurve(), []);
  const tube = useMemo(() => new THREE.TubeGeometry(curve, TRAIL_SEGMENTS, 0.022, RADIAL, false), [curve]);
  const markerPoints = useMemo(() => WAYPOINTS.map((t) => curve.getPointAt(t)), [curve]);

  useFrame((state, delta) => {
    // The one orchestrated moment: the trail draws itself to the summit, once.
    if (started.current === null) started.current = state.clock.elapsedTime;
    const progress = Math.min(1, (state.clock.elapsedTime - started.current) / DRAW_SECONDS);
    const eased = 1 - (1 - progress) ** 3;
    tube.setDrawRange(0, Math.floor(eased * TRAIL_SEGMENTS) * RADIAL * 6);
    markers.current.forEach((marker, i) => {
      if (marker) marker.visible = eased >= WAYPOINTS[i] - 0.01;
    });
    // Then only a slight lean toward the cursor.
    if (group.current) {
      const ease = 1 - Math.exp(-delta * 2);
      group.current.rotation.y += (state.pointer.x * 0.12 - group.current.rotation.y) * ease;
      group.current.rotation.x += (-state.pointer.y * 0.03 - group.current.rotation.x) * ease;
    }
  });

  return (
    <group ref={group}>
      <mesh geometry={terrain}>
        <meshStandardMaterial vertexColors flatShading roughness={0.92} metalness={0} />
      </mesh>
      <mesh ref={trail} geometry={tube}>
        <meshStandardMaterial color={palette.brand} emissive={palette.brand} emissiveIntensity={0.35} roughness={0.5} />
      </mesh>
      {markerPoints.map((point, i) => (
        <mesh
          key={i}
          ref={(mesh) => {
            markers.current[i] = mesh;
          }}
          position={[point.x, point.y + (i === WAYPOINTS.length - 1 ? 0.2 : 0.1), point.z]}
          visible={false}
        >
          <octahedronGeometry args={[i === WAYPOINTS.length - 1 ? 0.13 : 0.085, 0]} />
          <meshStandardMaterial
            color={i === WAYPOINTS.length - 1 ? palette.soft : palette.brand}
            emissive={palette.brand}
            emissiveIntensity={0.25}
            flatShading
          />
        </mesh>
      ))}
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
  const light = theme === "light";

  return (
    <Canvas
      frameloop={active ? "always" : "never"}
      dpr={[1, 1.5]}
      camera={{ position: [-0.4, 2.7, 6.2], fov: 36 }}
      onCreated={({ camera }) => camera.lookAt(0.6, 0.85, -1)}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
      aria-hidden="true"
    >
      {/* Distant ridges fade into the sky. */}
      <fog attach="fog" args={[palette.page, 6.5, 13]} />
      <ambientLight intensity={light ? 0.75 : 0.45} color={palette.snow} />
      <directionalLight position={[4, 6, 4]} intensity={light ? 1.5 : 1.25} color={palette.snow} />
      {/* Low evening light from behind the range, tinted by the logo's facets. */}
      <directionalLight position={[-5, 2.5, -6]} intensity={1.1} color={palette.soft} />
      <Mountain palette={palette} />
    </Canvas>
  );
}
