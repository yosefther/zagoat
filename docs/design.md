# zagoat design

Second direction, approved by the owner on 2026-10-21 after the first (olive-black with lime)
was rejected as generic. Rules for any UI work: [`.claude/skills/frontend-design/SKILL.md`](../.claude/skills/frontend-design/SKILL.md)
and [`.claude/skills/zagoat-design/SKILL.md`](../.claude/skills/zagoat-design/SKILL.md).
Every value lives once in [`web/src/styles/tokens.css`](../web/src/styles/tokens.css).

## Concept

zagoat is a goat, and goats climb. Each task is an ascent; a path is a route up the
mountain. The visuals come from that world: low-poly ridgelines in the logo's faceted style,
trail signage type, grades. The copy stays plain.

## Palette: alpine dusk

| Token | Dark (default) | Light | Role |
| --- | --- | --- | --- |
| `--page` (dusk) | `#1B1E33` | `#F2F4F8` | Evening sky, roughly the complement of the logo's lime |
| `--panel` / `--raised` | `#232742` / `#2E3353` | `#FFFFFF` / `#E6E9F1` | Ridge and scree surfaces |
| `--ink` / `--muted` | `#F1F3EC` / `#A6ABC4` | `#1B1E33` / `#555B78` | Snow and haze text |
| `--brand` | `#96D927` | `#96D927` (fills) | Logo body: actions, focus, the trail, passed results |
| `--brand-strong` | `#B4E86A` | `#3E6C08` | Links and focus rings |
| `--brand-soft` | `#C6EE83` | `#C6EE83` | Logo facets: highlights in the 3D hero |
| `--easy` / `--medium` / `--hard` | `#7FD3FF` / `#E0A8FF` / `#FF7EA6` | `#1767B0` / `#7A3FC2` / `#B02060` | Glacier, lavender, rose |
| `--success` / `--warning` / `--danger` | `#4FD8B0` / `#F7C35C` / `#FF7D7D` | `#0A6E58` / `#8A5A00` / `#B8282E` | Teal success never reads as the brand |

The neutrals are deliberately not tinted toward lime (the zagoat-design skill's default):
that produced the green-black "hacker" look. Measured contrast on page, panel and raised in
both themes: text tokens at least 4.8:1 (code comments 4.5:1), input borders at least 3.0:1,
text on lime 9.6:1.

## Type

- Barlow Condensed (600/700): headlines, from road and trail signage. Large and tight,
  sentence case, never all caps. The landing headline is the one 88px moment.
- Barlow (400–600): body and UI, tabular figures.
- Martian Mono: code only. Ligatures are off.
- Scale: 14 / 16 / 20 / 25 / 32 / 48, plus 88 for the landing headline.

## Principles

1. One bold thing: the mountain-and-trail hero. Everything else is quiet.
2. Structure carries information: peak glyphs grade difficulty (▲▲△ Medium), trail
   waypoints are real tasks, numbers appear only where order matters (a path's tasks).
3. No template chrome: no dot-joined meta strings, no monospace labels, no uppercase
   eyebrows, no uniform rounded cards with shadows, no "→".
4. Lime marks only what you act on or passed.

## Pages

- Landing: headline left on open sky; the 3D range on the right; two real tasks as rows with
  code excerpts; pricing in two columns; the waitlist.
- Tasks (`/tasks`): a grid of paths. Each tile is a path drawn as a climb (waypoints in the
  task's difficulty color, filled when solved, toward a summit that fills when the path is
  done), with progress, the next task and "Start / Continue this path".
- Path (`/paths/[id]`): the tasks in order on a vertical trail, with grade, time, progress
  and a "Continue with …" button. Opening a task from here makes the workspace's previous
  and next arrows follow the path.
- All tasks (`/tasks/all`): the sortable, filterable table.
- Task workspace: the skill's wireframe (top bar, resizable panes, console), on the dusk
  surfaces.

## 3D hero

`web/src/components/hero/`. A faceted terrain (flat-shaded triangles colored rock to snow by
height, `--rock-low`, `--rock-high`, `--snow`), fogged into the page color, with a lime
trail of switchbacks that draws itself to the summit once on load, passing a waypoint per
task. Afterwards it only leans slightly toward the cursor. Edges fade into the sky with a
CSS mask. DPR is capped at 1.5; rendering pauses off-screen and in hidden tabs.

`web/public/brand/hero-static-{dark,light}.png` are renders of the finished scene, shown
first and kept for reduced motion, no WebGL and screens under 768px. Re-render after
changing the scene: load `/` per theme in a WebGL browser, wait for the trail, make the page
background transparent and screenshot `[data-hero-mode=live]` at 1.5x with a transparent
background.

## Brand files

`web/public/brand/logo.png` is the owner's logo, used as-is; `logo-128.png` and
`favicon-{16,32,180,512}.png` are plain resizes.
