# zagoat design

Approved by the owner on 2026-10-21. The rules for any UI work are in
[`.claude/skills/zagoat-design/SKILL.md`](../.claude/skills/zagoat-design/SKILL.md); this file
records the decisions made under them. Every value lives once in
[`web/src/styles/tokens.css`](../web/src/styles/tokens.css).

## Palette

Sampled from `web/public/brand/logo.png` with Pillow (6-color quantize, transparent pixels
ignored). The logo is one hue: a yellow-green body and lighter facets.

| Token | Dark (default) | Light | Source |
| --- | --- | --- | --- |
| `--brand` | `#96D927` | `#96D927` (fills only) | Logo body |
| `--brand-strong` (links, focus) | `#B4E86A` | `#3D6A06` | Logo body, lightened or darkened for contrast |
| `--brand-soft` (highlights, 3D hero) | `#C6EE83` | `#C6EE83` | Logo facets and glow |
| `--page` / `--panel` / `--raised` | `#0F120B` / `#161B10` / `#20271A` | `#F6F8F0` / `#FFFFFF` / `#EEF2E4` | Neutrals tinted toward the logo hue |
| `--line` / `--field` | `#333D27` / `#66755A` | `#D5DCC6` / `#8A957A` | Same |
| `--ink` / `--muted` | `#E8EDDF` / `#A3AD93` | `#1A2010` / `#575F48` | Same |
| `--success` / `--warning` / `--danger` | `#3DD6C0` / `#F2B84B` / `#FF6B6B` | `#0B7A6B` / `#8A5A00` / `#C02929` | Teal, so success never reads as the brand |
| `--easy` / `--medium` / `--hard` | `#6CB8FF` / `#C3A6FF` / `#FF7AC6` | `#1D6BBE` / `#6B43C6` / `#AD2277` | Magenta "hard", so it never reads as an error |

Measured contrast: every text color is at least 4.5:1 on page, panel and raised surfaces in
both themes (lowest: light success 4.6). Input borders are at least 2.9:1 in dark and 3.1:1
in light. Text on brand fills is `#10140A` at 10.9:1. Light-theme focus rings use
`--brand-strong`, because lime on off-white is only 1.6:1.

The Monaco editor theme is built at runtime from these tokens (`--code-*` for syntax) and
rebuilt when the theme changes.

## Type

- Bricolage Grotesque (500, 700): headings and the hero.
- IBM Plex Sans (400, 500, 600): body and UI.
- JetBrains Mono (400, 500): code only (dotted zero, distinct 1/l/I). Ligatures are off.
- Scale, ratio 1.25 on 16px: 13 / 14 / 16 / 20 / 25 / 31 / 39 / 49.

## Principles

1. Lime is a signal, not a surface: primary actions, focus, links and passing results only.
2. Facets, not pills: primary buttons have one chamfered corner (`--facet`), echoing the
   low-poly goat.
3. The braces carry the brand: the `{ }` from the goat's horns appears in the 3D hero only.
4. Dense and quiet in the app; the 3D hero is the landing page's one bold element.
5. Status is color plus a word or icon, never color alone.

## Pages

- Landing: headline and calls to action on the left, the 3D hero on the right; then the real
  sample tasks, pricing and the waitlist form.
- Problem list: a sortable table (status, title, category, difficulty, time, best result)
  with category, difficulty and status filters, search and a random task button.
- Problem page: its own top bar (navigation, timer, Submits left, Run tests, Submit
  solution, shortcuts, theme, account) over resizable panes: Description / Hints /
  Walkthrough / Submissions on the left; file tabs and the editor over a Sample tests /
  Results console on the right. Pane sizes are saved per browser. On phones the page shows
  the statement only.
- Shortcuts: Ctrl/Cmd+Enter runs, Ctrl/Cmd+Shift+Enter submits; listed in the "?" menu.

## 3D hero

`web/src/components/hero/`. Low-poly polyhedra, a torus and two extruded braces, lit in the
logo's colors, drifting and leaning toward the cursor. three.js through React Three Fiber
and drei, loaded dynamically with server rendering off. The device pixel ratio is capped at
1.5, and rendering pauses when the hero is off-screen or the tab is hidden.

`web/public/brand/hero-static-{dark,light}.png` are renders of the same scene. They show
first, and stay for reduced motion, missing WebGL and screens under 768px. Re-render them
after changing the scene: set the theme, load `/` in a WebGL browser, make the page
background transparent, and screenshot the `[data-hero-mode=live]` element at 1.5x with a
transparent background (Playwright's `omit_background` works).

## Brand files

`web/public/brand/logo.png` is the owner's logo, used as-is. `logo-128.png` and
`favicon-{16,32,180,512}.png` are plain resizes of it.
