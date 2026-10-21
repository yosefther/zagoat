/**
 * Small isometric dioramas for path cards, one per kind of path, drawn in the faceted
 * style of the logo and the hero. Every color is a design token, so both themes work.
 */

export type PathArtKind = "rag" | "evals" | "training" | "serving" | "mixed";

const U = 11.5; // one unit in SVG pixels
const OX = 100;
const OY = 47;
const COS = Math.cos(Math.PI / 6);

/** Isometric projection: x runs down-right, y down-left, z up. */
function p(x: number, y: number, z: number): string {
  return `${(OX + (x - y) * COS * U).toFixed(1)},${(OY + (x + y) * 0.5 * U - z * U).toFixed(1)}`;
}

type Tone = "rock" | "brand" | "easy" | "medium" | "hard" | "snow";

const FACES: Record<Tone, [top: string, left: string, right: string]> = {
  rock: ["color-mix(in oklab, var(--rock-high) 65%, var(--snow))", "var(--rock-high)", "var(--rock-low)"],
  snow: ["var(--snow)", "color-mix(in oklab, var(--snow) 70%, var(--rock-high))", "color-mix(in oklab, var(--snow) 45%, var(--rock-high))"],
  brand: ["var(--brand-soft)", "var(--brand)", "color-mix(in oklab, var(--brand) 65%, black)"],
  easy: ["color-mix(in oklab, var(--easy) 70%, white)", "var(--easy)", "color-mix(in oklab, var(--easy) 65%, black)"],
  medium: ["color-mix(in oklab, var(--medium) 70%, white)", "var(--medium)", "color-mix(in oklab, var(--medium) 65%, black)"],
  hard: ["color-mix(in oklab, var(--hard) 70%, white)", "var(--hard)", "color-mix(in oklab, var(--hard) 65%, black)"],
};

function Box({ x, y, z = 0, w, d, h, tone = "rock" }: { x: number; y: number; z?: number; w: number; d: number; h: number; tone?: Tone }) {
  const [top, left, right] = FACES[tone];
  const t = z + h;
  return (
    <g>
      <polygon points={[p(x, y + d, z), p(x + w, y + d, z), p(x + w, y + d, t), p(x, y + d, t)].join(" ")} fill={left} />
      <polygon points={[p(x + w, y, z), p(x + w, y + d, z), p(x + w, y + d, t), p(x + w, y, t)].join(" ")} fill={right} />
      <polygon points={[p(x, y, t), p(x + w, y, t), p(x + w, y + d, t), p(x, y + d, t)].join(" ")} fill={top} />
    </g>
  );
}

/** A flat shape drawn on the front (left-facing) side of a panel at depth y. */
function OnPanel({ y, at, ...rest }: { y: number; at: [number, number][] } & Omit<React.SVGProps<SVGPolylineElement>, "points">) {
  return <polyline points={at.map(([u, v]) => p(u, y, v)).join(" ")} fill="none" {...rest} />;
}

function Ground() {
  return <Box x={0} y={0} z={-0.6} w={8} d={8} h={0.6} tone="rock" />;
}

const LINE = { stroke: "var(--brand)", strokeWidth: 2.2, strokeLinecap: "round", strokeLinejoin: "round" } as const;

/** A magnifier floating above a point of the scene, handle down to the left. */
function Lens({ x, y, z }: { x: number; y: number; z: number }) {
  const [cx, cy] = p(x, y, z).split(",").map(Number);
  return (
    <g>
      <line x1={cx - 8} y1={cy + 8} x2={cx - 17} y2={cy + 17} stroke="var(--brand)" strokeWidth={5} strokeLinecap="round" />
      <circle cx={cx} cy={cy} r={11} fill="color-mix(in oklab, var(--brand-soft) 22%, transparent)" stroke="var(--brand)" strokeWidth={3.5} />
    </g>
  );
}

function Rag() {
  return (
    <>
      <Ground />
      {/* The prompt the retrieved text is sent to. */}
      <Box x={4.8} y={1} w={2.6} d={0.35} h={3.6} tone="snow" />
      {[2.9, 2.3, 1.7].map((v, i) => (
        <OnPanel key={v} y={1.35} at={[[5.2, v], [i === 1 ? 6.5 : 7, v]]} stroke="var(--rock-high)" strokeWidth={2} strokeLinecap="round" />
      ))}
      {/* Handbook pages, chunked; the highlighted chunk is the one retrieval should find. */}
      <Box x={0.8} y={1.2} w={2.4} d={2.6} h={0.35} />
      <Box x={0.8} y={1.2} z={0.45} w={2.4} d={2.6} h={0.35} />
      <Box x={1} y={4.4} w={2.8} d={3} h={0.35} />
      <Box x={1} y={4.4} z={0.45} w={2.8} d={3} h={0.35} tone="brand" />
      <Box x={1} y={4.4} z={0.9} w={2.8} d={3} h={0.35} />
      <polyline points={[p(2.4, 5.9, 1.6), p(4, 4.2, 3.2), p(5.6, 1.6, 3.4)].join(" ")} {...LINE} strokeDasharray="1 5" fill="none" />
      {/* The lens, looking for the right chunk. */}
      <Lens x={2.6} y={5.6} z={2.9} />
    </>
  );
}

function Evals() {
  const bars: [number, number, number, Tone][] = [
    [3.6, 3.2, 1.6, "easy"],
    [4.9, 3.2, 3.1, "brand"],
    [3.6, 4.7, 2.4, "medium"],
    [4.9, 4.7, 1.1, "hard"],
  ];
  return (
    <>
      <Ground />
      {/* A scorecard of checks, some passing. */}
      <Box x={0.7} y={0.8} w={2.6} d={0.35} h={4} tone="snow" />
      {[3.2, 2.2, 1.2].map((v, i) => (
        <g key={v}>
          <OnPanel
            y={1.15}
            at={i === 1 ? [[1.05, v + 0.25], [1.55, v - 0.25]] : [[1, v], [1.25, v - 0.3], [1.65, v + 0.3]]}
            stroke={i === 1 ? "var(--hard)" : "var(--brand)"}
            strokeWidth={2.4}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {i === 1 && <OnPanel y={1.15} at={[[1.05, v - 0.25], [1.55, v + 0.25]]} stroke="var(--hard)" strokeWidth={2.4} strokeLinecap="round" />}
          <OnPanel y={1.15} at={[[2, v], [3, v]]} stroke="var(--rock-high)" strokeWidth={2} strokeLinecap="round" />
        </g>
      ))}
      {/* Per-label scores as bars. */}
      {bars.map(([x, y, h, tone]) => (
        <Box key={`${x}-${y}`} x={x} y={y} w={1.1} d={1.1} h={h} tone={tone} />
      ))}
    </>
  );
}

function Training() {
  const train: [number, number][] = [[1.4, 3.9], [2.2, 2.9], [3.1, 2.2], [4.2, 1.7], [5.4, 1.4], [6.6, 1.25]];
  const val: [number, number][] = [[1.4, 3.9], [2.2, 3.2], [3.1, 2.9], [4.2, 2.85], [5.4, 2.95], [6.6, 3]];
  return (
    <>
      <Ground />
      <Box x={0.8} y={1} w={6.4} d={0.35} h={4.4} tone="snow" />
      <OnPanel y={1.35} at={[[1.2, 4.2], [1.2, 0.8], [6.9, 0.8]]} stroke="var(--rock-high)" strokeWidth={2} />
      <OnPanel y={1.35} at={val} stroke="var(--hard)" strokeWidth={2.4} strokeLinejoin="round" strokeDasharray="3 3" />
      <OnPanel y={1.35} at={train} {...LINE} />
      {/* Batches waiting to go in. */}
      <Box x={1.4} y={4.6} w={1.3} d={1.3} h={1.3} />
      <Box x={3.2} y={4.6} w={1.3} d={1.3} h={1.3} tone="brand" />
      <Box x={5} y={4.6} w={1.3} d={1.3} h={1.3} />
    </>
  );
}

function Serving() {
  return (
    <>
      <Ground />
      {[0, 1.25, 2.5].map((z) => (
        <g key={z}>
          <Box x={1.6} y={1.6} z={z} w={3.4} d={3.4} h={1.05} />
          {[2.1, 2.6, 3.1].map((u) => (
            <OnPanel key={u} y={5} at={[[u, z + 0.5], [u + 0.01, z + 0.5]]} stroke={u === 2.1 ? "var(--brand)" : "var(--rock-low)"} strokeWidth={3.5} strokeLinecap="round" />
          ))}
        </g>
      ))}
      {/* Requests arriving. */}
      {[[6.6, 3.2], [6.6, 4.7], [6.6, 6.2]].map(([x, y], i) => (
        <Box key={y} x={x} y={y} w={0.8} d={0.8} h={0.8} tone={i === 0 ? "brand" : "easy"} />
      ))}
      <polyline points={[p(6.4, 3.6, 0.4), p(5.2, 3.6, 0.4)].join(" ")} {...LINE} fill="none" />
    </>
  );
}

function Mixed() {
  return (
    <>
      <Ground />
      {/* A chat window... */}
      <Box x={0.8} y={0.9} w={4.2} d={0.35} h={4.2} tone="snow" />
      {[
        [1.2, 3.4, 3.4, 3.9, "var(--rock-high)"],
        [2.5, 2.2, 4.6, 2.8, "var(--brand)"],
        [1.2, 1, 3, 1.6, "var(--rock-high)"],
      ].map(([u0, v0, u1, v1, color]) => (
        <polygon
          key={String(v0)}
          points={[p(u0 as number, 1.25, v0 as number), p(u1 as number, 1.25, v0 as number), p(u1 as number, 1.25, v1 as number), p(u0 as number, 1.25, v1 as number)].join(" ")}
          fill={color as string}
        />
      ))}
      {/* ...fed by documents and checked by an eval. */}
      <Box x={5.6} y={1.6} w={1.8} d={2.2} h={0.3} />
      <Box x={5.6} y={1.6} z={0.4} w={1.8} d={2.2} h={0.3} tone="brand" />
      <Box x={1.6} y={5} w={0.9} d={0.9} h={1.4} tone="easy" />
      <Box x={2.8} y={5} w={0.9} d={0.9} h={2.3} tone="brand" />
      <Box x={4} y={5} w={0.9} d={0.9} h={1.8} tone="medium" />
    </>
  );
}

const SCENES: Record<PathArtKind, () => React.ReactElement> = {
  rag: Rag,
  evals: Evals,
  training: Training,
  serving: Serving,
  mixed: Mixed,
};

export function PathArt({ kind, className }: { kind: PathArtKind; className?: string }) {
  const Scene = SCENES[kind];
  return (
    <svg viewBox="20 2 160 148" className={className} aria-hidden="true">
      <Scene />
    </svg>
  );
}
