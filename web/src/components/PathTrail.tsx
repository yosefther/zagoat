import type { ProblemSummary } from "@/lib/types";

const DIFFICULTY_VAR = { easy: "var(--easy)", medium: "var(--medium)", hard: "var(--hard)" } as const;
const WIDTH = 300;
const HEIGHT = 72;
const R = 8;
const LEFT = R + 3;
const SUMMIT_X = WIDTH - 14;
const LOW_Y = HEIGHT - R - 4;
const HIGH_Y = 14;

/**
 * A path drawn as a climb: one waypoint per task, rising left to right toward a summit.
 * Waypoints use the task's difficulty color: filled when solved, half filled when started,
 * open when untouched. The summit fills in when every task on the path is solved.
 */
export function PathTrail({ tasks }: { tasks: ProblemSummary[] }) {
  const stops = tasks.length + 1; // the tasks, then the summit
  const point = (index: number) => ({
    x: LEFT + ((SUMMIT_X - LEFT) * index) / (stops - 1),
    y: LOW_Y - ((LOW_Y - HIGH_Y) * index) / (stops - 1),
  });
  const summit = point(tasks.length);
  const done = tasks.length > 0 && tasks.every((task) => task.progress === "solved");
  const route = Array.from({ length: stops }, (_, i) => point(i))
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x} ${p.y}`)
    .join(" ");

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      preserveAspectRatio="xMinYMid meet"
      className="h-[4.5rem] w-full max-w-[22rem]"
      aria-hidden="true"
    >
      <path d={route} fill="none" stroke="var(--line)" strokeWidth="2.5" strokeLinejoin="round" />
      {tasks.map((task, index) => {
        const { x, y } = point(index);
        const color = DIFFICULTY_VAR[task.difficulty];
        const solved = task.progress === "solved";
        const started = task.progress === "attempted" || task.progress === "in_progress";
        return (
          <g key={task.id}>
            <circle cx={x} cy={y} r={R} fill={solved ? color : "var(--panel)"} stroke={color} strokeWidth="2.5" />
            {started && <path d={`M${x} ${y - R} a${R} ${R} 0 0 1 0 ${R * 2} z`} fill={color} />}
          </g>
        );
      })}
      <path
        d={`M${summit.x - 11} ${summit.y + 9} L${summit.x} ${summit.y - 10} L${summit.x + 11} ${summit.y + 9} Z`}
        fill={done ? "var(--brand)" : "var(--panel)"}
        stroke={done ? "var(--brand)" : "var(--field)"}
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}
