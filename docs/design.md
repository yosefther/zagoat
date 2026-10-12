# zagoat design plan

Status: decided by Claude on 2026-10-21 under the "decide it, record it" instruction.
Needs your review. Every value here lives in `web/src/app/globals.css`, so changes happen in one place.

## Principles

- Indigo carries the brand. Lime is a spark used sparingly: the primary button, focus rings
  and success states. It's never used for large fills or body text.
- The page should feel like a calm, well-typeset workbook, not a terminal. Off-white paper
  in light mode and deep indigo, not black, in dark mode.
- Text lines stay under 80 characters (`max-w-prose`, about 65ch).

## Colours

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--bg` | `#FAFAF7` | `#110F2B` | Page background |
| `--surface` | `#FFFFFF` | `#1C1A40` | Cards, panels, editor chrome |
| `--ink` | `#1E1B4B` | `#ECEBF7` | Body text and headings |
| `--muted` | `#55527A` | `#ABA8CC` | Secondary text |
| `--border` | `#DDDBEA` | `#34315E` | Decorative dividers |
| `--field` | `#8B88AE` | `#6E6A9C` | Input borders (at least 3:1 against surface) |
| `--accent` | `#A3E635` | `#A3E635` | Primary button fill, focus halo, success marks |
| `--on-accent` | `#1E1B4B` | `#1E1B4B` | Text on lime (10.6:1) |
| `--link` | `#4338CA` | `#A5B4FC` | Links |
| `--success` | `#3F6212` | `#A3E635` | Success text |
| `--danger` | `#B42318` | `#FDA29B` | Errors |

Measured contrast: all text tokens are at least 6.3:1 on `--bg` and `--surface` in both modes.
Lime on the light background is only 1.44:1, so the light-mode primary button has a 1px
`--ink` border. Focus is a 2px `--ink` outline with a 2px lime halo in light mode, and a 2px
lime outline in dark mode.

Dark mode follows the system setting by default. A toggle in the footer can force light or dark,
and the choice is saved in `localStorage`.

## Type

- **Space Grotesk** (500/700): the wordmark and headings. It's geometric and a little quirky,
  which echoes the logo.
- **IBM Plex Sans** (400/500/600) for body text and UI, and **IBM Plex Mono** (400/500) for code
  and the editor. One superfamily keeps prose and code in step.

Scale (ratio 1.25, base 16px): 13 / 14 / 16 / 20 / 25 / 31 / 39 / 49. Body text is 16/1.6,
headings 1.15–1.25. Sentence case everywhere.

## Logo

There's no clean vector logo yet. The PNG at the repo root has a raster glow with colour
fringing, so it isn't used. Per the brief, the header uses a text wordmark ("zagoat" in Space
Grotesk 700, with lime `{ }` brace marks around the "goat" part as a nod to the horns). Dropping
SVGs into `web/public/brand/` (`mark.svg`, `wordmark.svg`) replaces it.

## Landing page (`/`)

```
┌──────────────────────────────────────────────────────────────┐
│ zagoat            Problems  Pricing             [ Sign in ]  │
├──────────────────────────────────────────────────────────────┤
│  Practice the real tasks                                     │
│  AI interviews give you.                                     │
│  Fix a RAG pipeline, debug a training loop, write an eval.   │
│  30–60 minute tasks, graded by hidden tests and metrics.     │
│                                                              │
│  [ you@example.com        ] [ Join the waitlist ]            │
│  [x] Email me when zagoat launches. Privacy policy.          │
├──────────────────────────────────────────────────────────────┤
│  What you'll practice                                        │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐       │
│  │ RAG · medium  │ │ Evals · easy  │ │ Training · hard│      │
│  │ Title         │ │ Title         │ │ Title          │      │
│  │ two-line brief│ │ ...           │ │ ...            │      │
│  │ code excerpt  │ │ code excerpt  │ │ code excerpt   │      │
│  └───────────────┘ └───────────────┘ └───────────────┘       │
├──────────────────────────────────────────────────────────────┤
│  How it works: 1 Read the brief  2 Fix the code  3 Get graded │
│  See pricing →                                               │
├──────────────────────────────────────────────────────────────┤
│ © zagoat · Privacy · Terms                      Theme: Auto  │
└──────────────────────────────────────────────────────────────┘
```

On mobile, the columns stack, and the waitlist input and button go full width.

## Problem page (`/problems/[id]`, desktop)

```
┌──────────────────────────────────────────────────────────────┐
│ zagoat   Problems  History  Pricing               avatar ▾  │
├──────────────────────┬───────────────────────────────────────┤
│ RAG · medium · 45 min│ [main.py] [retriever.py]   ⏱ Timer ○  │
│ Title                │                                       │
│ Statement (markdown) │          Monaco editor                │
│ ...                  │                                       │
│ Hints (1 of 3) [Show]│                                       │
│ Walkthrough · Ref.   ├───────────────────────────────────────┤
│                      │ Results: verdict, tests, metrics      │
│                      │ 7 of 10 submits left · resets 02:00   │
│                      │        [ Run tests ] [Submit solution]│
└──────────────────────┴───────────────────────────────────────┘
```

Below 1024px, the page shows the statement and a note: "Solving works on desktop. Open this
page on a larger screen to write and run code."

## Motion and accessibility

- Transitions are 150ms colour and opacity changes only, and are disabled under
  `prefers-reduced-motion`.
- Every interactive element has a visible focus state. A skip link goes to the main content.
- Form errors are announced with `aria-live` and linked to their field with `aria-describedby`.
