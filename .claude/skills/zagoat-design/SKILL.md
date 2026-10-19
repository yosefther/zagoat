---
name: zagoat-design
description: Design system and UI process for zagoat.io. Use this skill for ANY visual or front-end work on zagoat, including building or changing pages, components, layouts, colors, themes, typography, icons, the logo or favicons, the landing page and its 3D hero, the problem list, and the problem/editor workspace. Use it even for small tweaks like "make this button look better" or "fix the spacing", and whenever reviewing screenshots of the UI.
---

# zagoat design

zagoat.io is a practice platform for AI engineer interviews. The people using it are mid-level to senior engineers, and the interface has two jobs: get them into a realistic task fast, and make the workspace feel like a serious engineering tool they'd happily spend an hour in.

The owner rejected the first UI as generic and disliked its colors. This skill exists so that doesn't happen again: every visual decision should be deliberate, tied to the zagoat brand, and checked with screenshots before it's shown.

If Anthropic's `frontend-design` skill is also available, follow it too. This skill adds zagoat's specifics, and wins where the two disagree.

## Before any UI work

1. Open the logo at `web/public/brand/logo.png` and look at it. If it's missing, stop and ask for it; don't invent a logo or a palette.
2. For a new page or a redesign, write a design plan (format below) and wait for the owner's OK before writing code. Small tweaks can skip the plan but must use the existing tokens.
3. After building, run the review loop at the end of this file before reporting back.

### Design plan format

- Palette: 4–6 named hex values, each with the logo color it came from, plus the semantic and difficulty colors.
- Type: the typefaces, what each is for, and the type scale.
- Layout: one-sentence concepts plus ASCII wireframes for each page in scope.
- Principles: 3–5 short rules that make this design zagoat's and nobody else's.

Then reread the plan and ask whether a similar prompt would have produced the same thing for any other product. Revise whatever reads like a default, and say what you changed.

## Brand

- The name is always "zagoat", in lowercase.
- Use the logo file as-is in the nav, the footer, the favicon set (16, 32, 180 and 512 px) and the social share image. Never redraw, recolor, stretch, crop into a new shape or add effects to it. If a transparent or one-color version is needed, ask the owner.

### Colors come from the logo

The palette exists to make the logo feel at home, so derive it from the logo instead of picking colors you like.

1. Sample the logo's main colors with a script (for example Python with Pillow quantizing to 6 colors, ignoring the background) to get exact hex values rather than eyeballing them.
2. Choose one brand color for primary actions, links and focus rings. If the logo has a second strong color, use it sparingly for highlights and the 3D hero.
3. Build neutrals (backgrounds, panels, borders, text) with a slight tint toward the brand hue, so surfaces feel related to the logo instead of plain grey.
4. Add semantic colors (success, warning, error) and difficulty colors (easy, medium, hard) that are clearly distinct from the brand color, so a red "hard" label is never confused with an error or the brand.
5. The old indigo `#1E1B4B` and lime `#A3E635` palette is retired. Don't bring it back unless the logo actually uses those colors.

### Tokens

- Define every color, font, size, radius, shadow and spacing step once as CSS variables (for example in `web/src/styles/tokens.css`) and map them into the Tailwind theme. Components use tokens only, never raw hex values; that's what keeps a redesign to one file next time.
- Themes: the app (problem list, problem page) is dark by default, like most coding tools, with a light theme toggle. Use three clearly separated surface levels (page, panel, raised) so panes read without heavy borders.
- Contrast: body text at least 4.5:1, large text and UI controls at least 3:1, in both themes. Check pairs with a small script rather than by eye.
- Build a custom Monaco editor theme from the tokens. The default `vs-dark` theme will clash with everything else.

## Layout: LeetCode as a reference, not a template

Engineers already know LeetCode, so reuse its proven layout and interaction patterns; it lowers the learning curve to zero. zagoat must still look like its own product: someone who knows LeetCode should feel at home, but nobody should mistake one for the other.

Never copy LeetCode's logo, name, colors (including its orange and amber accents), icons, illustrations, fonts, wording or pixel-exact layouts, and never use screenshots or assets from its site.

### Problem list

```
+--------------------------------------------------------------------+
| logo   Problems   Pricing                      search   theme  avatar|
+--------------------------------------------------------------------+
| [category v] [difficulty v] [status v]   search...      Random task |
+----+------------------------------+----------+--------+------+------+
| ✓  | Fix the chunking in a RAG... | RAG      | Medium | 45 m | 0.84 |
| ○  | Write evals for a summari... | Evals    | Hard   | 60 m |  —   |
+----+------------------------------+----------+--------+------+------+
```

- Columns: status, title, category, difficulty, estimated time, best result. Sortable, with dense rows; this is a scanning surface, not a card gallery.
- Difficulty is colored text, not a filled pill. Status is a small icon (solved, attempted, not started) with an accessible label.
- Locked paid tasks show a small lock and stay readable, since their statements are public.

### Problem page (desktop workspace)

```
+--------------------------------------------------------------------+
| logo  < prev  next >  Task title      timer   3 submits left  Run  Submit|
+-----------------------------+--------------------------------------+
| Description | Hints |       | file tabs: main.py  retriever.py     |
| Walkthrough | Submissions   |                                      |
|                             |  editor (Monaco, token theme)        |
| statement, data notes,      |                                      |
| sample tests                +--------------------------------------+
|                             | Sample tests | Results               |
|                             |  console / test results / metrics    |
+-----------------------------+--------------------------------------+
```

- Full-height workspace with resizable split panes (for example the `react-resizable-panels` library); remember each user's pane sizes.
- Run is a secondary button and Submit the primary one; the top bar holds the timer, remaining Submits and previous/next navigation.
- Shortcuts: Ctrl/Cmd+Enter runs, Ctrl/Cmd+Shift+Enter submits; list them in a help menu.
- On phones the problem page shows the statement only, with a clear note to solve on desktop.

## Landing page and the 3D hero

The 3D hero is the page's one bold element. Keep everything around it quiet: real sample tasks, pricing, the waitlist form.

- Scene: a few geometric shapes floating in space, such as low-poly polyhedra, tori and one or two extruded curly braces echoing the logo, lit in the logo's colors. They drift slowly and lean slightly toward the cursor. Matte or softly glossy materials; no neon glow, bloom or heavy post-processing.
- Composition: headline and call to action on the left, scene on the right on desktop. The text never sits on top of busy geometry.
- Build: three.js through React Three Fiber and drei, imported dynamically with server-side rendering off, so it loads after the page is interactive.
- Performance: cap the device pixel ratio at 1.5, and pause rendering when the hero is off-screen (IntersectionObserver) or the tab is hidden. Target a Lighthouse performance score of 90+ on desktop.
- Fallbacks: render the scene once to a static image and show that instead when the user prefers reduced motion, WebGL is unavailable, or the screen is phone-sized.

## Type and copy

- Choose one or two typefaces on purpose, plus a monospace face for code only. Pick the code font for legibility (clear 0/O and 1/l/I). Load fonts with `next/font` and define the scale as tokens.
- Keep text lines under 80 characters.
- Copy is plain, specific and in sentence case. Buttons say what they do ("Run tests", "Submit solution") and keep the same name through the flow. Errors say what happened and how to fix it. Empty states tell people what to do next.
- Avoid template tells: all-caps eyebrow labels above headings, "→" appended to buttons, identical rounded cards with the same soft shadow, gradient washes as decoration, and a single headline word in a different color.

## Review loop

Before reporting UI work as done:

1. Run the app and take screenshots with Playwright of every page you changed, in both themes, at 1440×900 and 390×844.
2. Look at each screenshot and check it against this list:
   - Every color comes from the tokens, and the palette clearly relates to the logo.
   - Contrast passes in both themes; keyboard focus is visible.
   - The page has one bold element and no template tells.
   - The problem page panes resize, the shortcuts work, and the editor theme matches the app.
   - The 3D hero pauses off-screen, and the reduced-motion and mobile fallbacks show the static image.
3. Fix what's off, retake the screenshots, and share the final set with a short note on what you changed and why.