"""
Stylesheet (V1.7 Parts 5, 8, 36)
==================================
One stylesheet, served from memory. No CDN, no web font, no build step —
the application runs offline and a page that waits on a network request is
a page that does not load.

ACCESSIBILITY DECISIONS MADE HERE, NOT LEFT TO THE BROWSER

    Text scales with the root font size rather than being pinned in
    pixels, so a reader who enlarges type gets larger type rather than a
    broken grid.

    Focus is always visible. The default outline is removed in a great many
    stylesheets and replaced with nothing, which makes a keyboard
    unusable; here it is replaced with something stronger.

    Body text sits at #1d1f23 on #ffffff, about 15:1, and the muted grey at
    #5b6068 is about 6.5:1. Both clear WCAG AA for body text with room to
    spare, which matters because the muted grey carries provenance notes.

    Status colours are decoration. Every badge, every warning and every
    activation level prints its word as well, so the pages are complete in
    greyscale.
"""

STYLESHEET = """
:root {
  --ink: #1d1f23;
  --muted: #5b6068;
  --rule: #d8dade;
  --paper: #ffffff;
  --panel: #f6f6f4;
  --accent: #7a2e0e;
  --warn: #8a4b06;
  --warn-bg: #fdf6ec;
  --limit: #2f3338;
  --ok: #1f5c3d;
  --font-serif: 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia,
                'Noto Serif', serif;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
               'Noto Sans', sans-serif;
}

* { box-sizing: border-box; }

html { font-size: 100%; }

body {
  margin: 0;
  font-family: var(--font-serif);
  font-size: 1rem;
  line-height: 1.55;
  color: var(--ink);
  background: var(--paper);
}

a { color: var(--accent); }
a:focus-visible, button:focus-visible, select:focus-visible,
input:focus-visible, summary:focus-visible {
  outline: 3px solid #1a4d8f;
  outline-offset: 2px;
}

.skip {
  position: absolute; left: -9999px; top: 0; background: var(--ink);
  color: #fff; padding: 0.6rem 1rem; z-index: 10;
}
.skip:focus { left: 0; }

header.masthead {
  border-bottom: 1px solid var(--rule);
  padding: 0.9rem 1.4rem;
  display: flex; flex-wrap: wrap; gap: 1rem;
  align-items: baseline; justify-content: space-between;
}
header.masthead h1 {
  font-size: 1.15rem; margin: 0; font-family: var(--font-sans);
  letter-spacing: 0.01em;
}
header.masthead .subject { color: var(--muted); font-size: 0.95rem; }
header.masthead .actions { display: flex; gap: 0.4rem; align-items: center; }
header.masthead .actions a.pdf-link {
  font-family: var(--font-sans); font-size: 0.8rem;
  padding: 0.3rem 0.75rem; border: 1px solid var(--rule);
  text-decoration: none; color: var(--ink);
  background: var(--paper);
}
header.masthead .actions a.pdf-link:hover { background: var(--ink); color: #fff; }
header.masthead .actions::before {
  content: "PDF:"; font-size: 0.78rem; color: var(--muted);
  font-family: var(--font-sans);
}

nav.screens {
  border-bottom: 1px solid var(--rule); padding: 0 1rem;
  overflow-x: auto; white-space: nowrap;
}
nav.screens a {
  display: inline-block; padding: 0.65rem 0.85rem; text-decoration: none;
  color: var(--muted); font-family: var(--font-sans); font-size: 0.86rem;
  border-bottom: 3px solid transparent;
}
nav.screens a[aria-current="page"] {
  color: var(--ink); border-bottom-color: var(--accent); font-weight: 600;
}
nav.screens a:hover { color: var(--ink); }

main { padding: 1.6rem 1.4rem 4rem; max-width: 62rem; margin: 0 auto; }
main.wide { max-width: 78rem; }

h2 { font-family: var(--font-sans); font-size: 1.35rem; margin: 0 0 0.4rem; }
h3 {
  font-family: var(--font-sans); font-size: 1.02rem;
  margin: 1.6rem 0 0.4rem; padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--rule);
}
h4 { font-family: var(--font-sans); font-size: 0.9rem; margin: 1.1rem 0 0.3rem; }
p { margin: 0 0 0.7rem; }
p.lead { font-size: 1.08rem; }
p.help, p.note, .note { color: var(--muted); font-size: 0.86rem; }

table.data {
  border-collapse: collapse; width: 100%; margin: 0.4rem 0 1.2rem;
  font-size: 0.88rem; font-family: var(--font-sans);
}
table.data caption {
  text-align: left; color: var(--muted); font-size: 0.82rem;
  padding-bottom: 0.35rem;
}
table.data th, table.data td {
  border-bottom: 1px solid var(--rule); padding: 0.35rem 0.5rem;
  text-align: left; vertical-align: top;
}
table.data th {
  background: var(--panel); font-weight: 600; font-size: 0.82rem;
  position: sticky; top: 0;
}
table.data td.right, table.data th.right { text-align: right; }
table.data td.centre, table.data th.centre { text-align: center; }
table.data tbody tr:hover { background: #fafaf8; }

dl.kv { display: grid; grid-template-columns: max-content 1fr; gap: 0.2rem 1rem;
        margin: 0 0 1rem; font-size: 0.92rem; }
dl.kv dt { color: var(--muted); font-family: var(--font-sans);
           font-size: 0.82rem; padding-top: 0.15rem; }
dl.kv dd { margin: 0; }
dl.kv dd .note { color: var(--muted); font-size: 0.82rem; display: block; }

.badge {
  display: inline-block; font-family: var(--font-sans); font-size: 0.75rem;
  padding: 0.1rem 0.45rem; border-radius: 0.7rem; border: 1px solid var(--rule);
  background: var(--panel); color: var(--ink); white-space: nowrap;
}
.badge.strong { border-color: #9ab7a6; background: #eef5f1; }
.badge.active { border-color: #a8b9cd; background: #eef2f7; }
.badge.mixed  { border-color: #cdb79a; background: #f7f2ea; }
.badge.silent { border-color: var(--rule); background: #f2f2f0;
                color: var(--muted); }
.badge.warn   { border-color: #d3b18a; background: var(--warn-bg); }

.callout {
  border-left: 3px solid var(--muted); background: var(--panel);
  padding: 0.7rem 0.9rem; margin: 0.8rem 0; font-size: 0.92rem;
}
.callout.warning { border-left-color: var(--warn); background: var(--warn-bg); }
.callout.limit { border-left-color: var(--limit); }
.callout p:last-child { margin-bottom: 0; }

.grid { display: grid; gap: 1.4rem; }
.grid.two { grid-template-columns: repeat(auto-fit, minmax(19rem, 1fr)); }
.grid.three { grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); }

figure.chart { margin: 0; }
figure.chart svg { width: 100%; height: auto; max-width: 26rem; display: block; }
figure.chart figcaption {
  font-family: var(--font-sans); font-size: 0.82rem; color: var(--muted);
  padding-top: 0.4rem;
}

.panel { border: 1px solid var(--rule); padding: 1rem 1.1rem; }

details { border-bottom: 1px solid var(--rule); padding: 0.45rem 0; }
details summary {
  cursor: pointer; font-family: var(--font-sans); font-size: 0.9rem;
}
details[open] summary { font-weight: 600; }
details .body { padding: 0.5rem 0 0.3rem 1rem; font-size: 0.92rem; }

.field { margin-bottom: 0.9rem; }
.field label {
  display: block; font-family: var(--font-sans); font-size: 0.82rem;
  color: var(--muted); margin-bottom: 0.2rem;
}
.field input, .field select {
  width: 100%; padding: 0.45rem 0.5rem; font-size: 0.95rem;
  font-family: var(--font-sans); border: 1px solid #b6b9bd; background: #fff;
  color: var(--ink);
}
button.primary {
  font-family: var(--font-sans); font-size: 0.95rem; padding: 0.6rem 1.3rem;
  background: var(--ink); color: #fff; border: 0; cursor: pointer;
}
button.primary:hover { background: #000; }

.timeline { border-left: 2px solid var(--rule); margin: 1rem 0 1rem 0.6rem;
            padding-left: 1rem; }
.timeline .event { margin-bottom: 1rem; }
.timeline .event .when {
  font-family: var(--font-sans); font-size: 0.8rem; color: var(--muted);
}
.bar {
  height: 0.5rem; background: var(--panel); border: 1px solid var(--rule);
  position: relative; margin: 0.25rem 0;
}
.bar .fill { position: absolute; top: 0; bottom: 0; background: #b9c4cf; }
.bar .peak { position: absolute; top: -3px; bottom: -3px; width: 2px;
             background: var(--accent); }

footer.notice {
  border-top: 1px solid var(--rule); margin-top: 2.6rem; padding-top: 0.9rem;
  color: var(--muted); font-size: 0.82rem;
}

@media print {
  nav.screens, header.masthead .actions { display: none; }
  body { font-size: 10pt; }
}

@media (prefers-contrast: more) {
  :root { --muted: #3c4046; --rule: #9aa0a6; }
}
"""
