# Technical architecture

How this application is built, for somebody who is going to change it.

---

## 1. The shape of it

```
main.py                 command line
  │
  ├── app/ui            local web interface       ─┐
  ├── app/report        documents, PDF, HTML       │  may NOT import engine
  ├── app/visual        chart geometry            ─┘
  │
  ├── app/services      THE ONLY ADAPTER          ── may import engine
  │
  └── engine/           calculation
```

`app/services` may import `engine.*`. `app/ui`, `app/report` and
`app/visual` may not.

This is enforced structurally, not by convention:

- `tests/test_app_boundary.py` and `tests/test_release.py` parse every
  file under the three forbidden packages with `ast` and fail on an
  `engine` import.
- A second suite pushes every snapshot through `json.dumps`/`loads`
  before rendering, so a renderer handed a live object still cannot
  reach through it. **A dict cannot answer a question that was not
  written down.**
- `./jyotish --self-check` runs the import audit at startup, so a
  packaging step that rewrote imports cannot break the guarantee
  silently.
- A third test greps the same packages for astrology vocabulary —
  `houses_owned_by(`, `vimshottari(`, `graha_drishti(` — because the
  import test catches the obvious violation and not the one where
  somebody copied a rule rather than importing it.

**Why so much machinery for one rule.** A renderer that can reach the
engine will eventually be asked to decide something, and the decision
will live where nobody looks for it. The one derivation deliberately
kept in the engine is the varga house — `(sign - lagna) % 12 + 1`, three
lines — because two implementations of one rule eventually disagree and
the one in the renderer is the one nobody tests.

---

## 2. Dependencies

**None at runtime.** The packaged build imports nothing outside the
standard library, and `tools/verify_package.py` proves it by parsing the
packaged tree rather than by importing it — an import test passes on any
machine that happens to have the dependency.

`pyswisseph` is imported by six files, all under `tools/`, all of which
generate fixtures. It is never used at runtime and is never packaged.
Swiss Ephemeris is an **external validation reference only**; no
coefficient in this engine was fitted against it.

---

## 3. The engine

| Package | What it owns |
|---|---|
| `ephemeris`, `planets` | VSOP87 and Meeus positions, ayanamsha, houses |
| `vargas`, `varga_metadata` | The sixteen divisions and their conventions |
| `features` | Dignity, aspects, conjunctions, lordships, dispositors |
| `strength` | Shadbala, six components |
| `ashtakavarga` | Bhinna and Sarva, with reductions off by default |
| `rules` | The yoga catalog and its profiles |
| `timing` | Vimshottari, in exact `Fraction` arithmetic |
| `transits` | Positions and geometric relationships — **facts** |
| `gochara` | Whether a located verse calls a transit favourable — **rules** |
| `synthesis` | Natal → Daśā → Transit, and the eligibility gates |
| `interpretation` | Template rendering, per locale |
| `sources` | Witnesses, evidence, conflicts, the review pipeline |

**`transits` and `gochara` are separate on purpose.** The first is
astronomy and has been externally benchmarked; the second is textual
interpretation and has not. One module holding both would let the second
inherit the first's benchmark.

---

## 4. Contracts

Four serialised objects carry everything between layers:

| Object | Schema | Contains |
|---|---|---|
| `ChartSnapshot` | 1.2.0 | The natal chart. True for a lifetime. |
| `PredictionSnapshot` | 1.1.0 | One synthesis run. True for an afternoon. |
| `InterpretationDocument` | 1.0.0 | Rendered sentences, one language |
| `ReportDocument` | 1.1.0 | Sections and blocks, ready to draw |

They are JSON-native. Nothing downstream ever receives an engine object.

Schema versions live **where their schema lives** — `engine/snapshot.py`
owns its own — so that a change to a shape and a change to its version
appear in the same diff. `app/version.py` is the single source for the
*application* version and reads none of them; `app/services/
version_service.py` is the adapter that reports them together.

---

## 5. The gochara layer (V1.8)

The newest and most gated part of the engine.

```
TransitReference   MOON / LAGNA / BOTH / OTHER   — every rule declares one
GocharaRule        favourable houses, vedha pairs, exemptions, sources
GocharaPlacement   where the graha stands, in that rule's frame
VedhaResult        obstructed? by what? was an exemption applied?
NatalStrengthCondition   the text's word AND the software's threshold
GocharaActivation  which daśā levels the graha rules
GocharaJudgement   the verdict, carrying every layer that produced it
```

Two rules are implemented, from two different chapters in two different
reference frames. Part of the design is that **only one of them can
reach a life area**: chapter 26 judges a transit without naming a bhāva,
and this engine's bhāva significations are stated from the Lagna, so
there is no sourced path from one to the other.

Three independent gates stand between a transit and a strict
conclusion — the rule's clauses must all be implemented, the judgement
must name a bhāva, and that bhāva's domain mapping must itself be
source-qualified. `tests/test_gochara.py::StrictEligibilityTest` is the
load-bearing test.

---

## 6. Text rendering

The PDF writer is hand-built: object table, content streams, xref, a
two-pass layout for "Page N of M". Base-14 Type1 fonts with
WinAnsiEncoding, and committed AFM-derived width tables.

Devanagari needed considerably more.

```
opentype.py    sfnt, cmap, hmtx, glyf/loca, GDEF, GSUB/GPOS parsing
otlayout.py    GSUB types 1,2,4,5,6; GPOS types 1,2,4,6,8
devanagari.py  Indic v2: categorise, segment, find base, reorder
embed.py       subset, CIDFontType2, Identity-H, ToUnicode
```

The lookup types implemented are **exactly what the bundled font uses**,
measured by walking its lookup list rather than guessed. An
unimplemented type is skipped *and counted*, so `unsupported_lookups`
can be asserted empty and would fill the moment the font changed.

Three performance notes, because the naive version took 23 seconds for a
nine-page document:

- Coverage and class-definition tables are parsed once per offset. They
  were being rebuilt for every glyph of every subtable.
- Chaining-context subtable headers are parsed once.
- Each lookup precomputes the union of its subtables' first-glyph
  coverages, so one set membership decides whether the lookup can apply
  at all. A test shapes every golden word with the filter disabled and
  asserts the glyph stream is identical, because a filter that is not
  a pure optimisation drops substitutions rather than raising.

Subsetting keeps glyph ids stable and empties unused outlines. That is
the simple form deliberately: renumbering would mean rewriting every
shaped run, and a renumbering bug produces a document full of the wrong
letters rather than a crash.

---

## 7. Chart geometry

```
ChartVisualModel  →  Scene (Line/Polygon/Rect/Text)  →  SVG or PDF
```

One description, two backends, so the kundli in the report is the kundli
on screen. `Scene.content_hash()` is a sha256 of sorted JSON with no
timestamp, which is what makes visual regression testable.

Two layouts read the same model. `render_chart` dispatches; each layout
refuses the other's style rather than approximating it. `east_indian` is
named in `CHART_STYLES` and absent from `IMPLEMENTED_STYLES`, so asking
for it produces a named refusal rather than a `KeyError`.

`tests/test_visual.py::StyleEquivalenceTest` compares every graha's
sign, house and markers across both styles for four divisional charts.
"Presentation only" is a claim, and a claim about drawing code is worth
what its test is worth.

---

## 8. Localisation

```
templates/<lang>/common.json     79 interpretation keys + grammar
templates/<lang>/<domain>.json   17 domain overrides
templates/<lang>/report.json     144 report chrome strings
```

Three lessons are baked into the structure:

**Hindi found four defects English could not** (V1.7): `{ordinal} house`
is not a pattern Hindi has; `sentence()` was capitalising and appending
`.` unconditionally; a dozen words reached templates as *arguments* and
so were never translated; and document headings were English literals in
Python while `section.*` keys sat unused.

**A completeness test measures what it was pointed at** (V1.8). V1.7
reported Hindi complete, and it was — for the 78 engine keys it checked.
The report's own chrome, generated in `app/report/builder.py` below the
boundary, had never been in scope. The first Hindi PDF had 1,232 English
strings in it.

**A missing key raises.** No silent fallback, in either system. An
English heading in a Hindi document is a defect that looks like a design
decision.

`app/report/strings.py` reads `templates/<lang>/report.json` directly
from disk. Reading a JSON file is not importing the engine, so the
boundary holds and there is still one translation directory per
language.

---

## 9. Storage

Schema 2.0.0 splits the saved file into `calculation` and `presentation`
because one of them can change a chart and the other cannot. A v1 file
had them in one block, with `language` sitting beside `ayanamsha` as
though they were the same kind of thing.

```python
ApplicationSettings.CALCULATION_FIELDS    # 11 fields
ApplicationSettings.PRESENTATION_FIELDS   # language
```

A test asserts every dataclass field is in exactly one list, so a new
setting has to be classified deliberately.

Migrations are explicit, keyed by version, and run in a loop:

```python
MIGRATIONS = {"": _migrate_pre_schema, "1.0.0": _migrate_1_to_2}
```

`_migrate_1_to_2` is deterministic and consults **nothing outside its
payload** — no clock, no current defaults. A test checks that
structurally, by reading the function's source: a migration that applied
today's defaults would silently re-methodologise yesterday's chart.

Unknown keys are kept in `unrecognised_settings` and reported, rather
than dropped. A reader that silently discards what it does not
understand turns an unknown setting into a default without saying so.

---

## 10. Caching

Three caches, all keyed so that nothing can leak:

| Cache | Key | Why it is safe |
|---|---|---|
| `_VSOP_CACHE` | (body, jd_tt) | Pure, and **upstream of every methodology choice** — there is no profile to leak into |
| `_POSITION_CACHE` | moment + every kwarg | V1.7 keyed on three of its kwargs; a latitude would have been ignored |
| `_width_cache` | the string | Greedy wrap measures the same prefix once per word |

The middle one is the instructive case. Nothing passed the other kwargs,
so nothing was wrong — and the first caller who asked for a transiting
Lagna would have received a chart computed for the equator. Keying on
everything removes the class rather than the instance.

---

## 11. Performance

Measured with `--benchmark`, cold, both caches cleared.

| | V1.7 | V1.8 |
|---|---|---|
| Chart, with sensitivity | 0.407 s | 0.23 s |
| Synthesis (full year scan) | 4.97 s | 2.67 s |
| Synthesis, no scan | — | **0.011 s** |
| End to end | 5.43 s | **2.98 s** |

The scan is essentially the whole cost. `event_horizon_days=0` disables
it and the two runs differ in `event_candidates` **and nothing else** —
a test compares every other section byte for byte. Disabling it emits a
warning into the document, because a quietly coarser answer is worse
than a slower one.

`end to end` is now the sum of the pipeline stages only. V1.7's figure
summed the diagnostic re-runs too, so the note under the table said the
rows do not sum to the total while the total was computed by summing
them.

---

## 12. Diagnostics

`app/diagnostics.py` writes one JSON object per line, redacting personal
fields by default and **replacing rather than deleting** them — a
diagnostic that cannot distinguish "absent" from "hidden" sends the
reader after a bug that is not there.

Crash reports carry the traceback, the build, and the methodology. They
never carry birth details unless `--debug` was used, in which case
`personal_data_included` is true. Frame locals are never captured: a
local in the ephemeris is a longitude and a local three frames up is a
person's name, and nothing can tell them apart automatically.

---

## 13. Packaging

```
python3 tools/build_package.py --clean     dist/jyotish-1.8.0{,.tar.gz}
python3 tools/verify_package.py            17 checks, clean environment
```

A directory plus a tarball, not a zipapp: the templates, the font and
its licence are opened by path, and a zipapp would need either
`importlib.resources` throughout or a cache directory written at first
run — which would contradict what this application says about itself.

The tarball is byte-reproducible: sorted entries, zeroed ownership and
timestamps, and a gzip header with `mtime=0`.

`verify_package.py` runs every check in a **subprocess with a cleared
environment**, from the unpacked archive. Running them in-process would
import the development checkout, and a package missing a whole directory
would pass.

---

## 14. Testing

1,456 tests. The ones worth knowing about:

| File | What it guards |
|---|---|
| `test_app_boundary`, `test_release` | The architecture boundary, three ways |
| `test_gochara` | The verses, transcribed, and the Part 7 gate |
| `test_properties` | Invariants over 60 charts, fixed seed |
| `test_regression_corpus` | 200 charts, and that the awkward cases are *covered* |
| `test_rc_goldens` | Four charts frozen at every stage |
| `test_security` | Hostile input through HTML, PDF and the file format |
| `test_performance` | That the optimisations changed no answer |

Three conventions that have earned themselves:

**Replaced, never deleted.** When a finding is overturned, the old
assertion is replaced with one that pins the new finding, and the
docstring says what changed. V1.8 replaced five: four that pinned the
Hindi PDF refusal, and one that pinned "5 of 11 vargas are attested".

**A corpus asserts its own coverage.** `test_regression_corpus`
classifies every chart and requires each of Part 40's categories to
appear. A corpus that claims to cover high latitudes is worth nothing if
the generator stopped producing them.

**Fixed seeds, always.** A property test that draws different inputs
each run is a test that fails for somebody else and passes for you, and
the first response to that is to disable it.

---

## 15. Things that will bite you

- **`Page.text` routes by script.** A mixed line is split into runs and
  each goes to the face that can draw it. The bundled Devanagari font
  has no Latin letters at all; sending a whole mixed line through it
  draws every English word as empty boxes.

- **`to_winansi` must stay idempotent.** Several paths convert, wrap,
  then measure again. Measure what is drawn: `text_width` converts
  before measuring, because the metrics table is indexed by byte value
  and an em-dash otherwise measures as zero.

- **`reset_embedded_fonts()` per document.** Glyph usage accumulates on
  a module-level object, and a second render of the same report would
  otherwise embed a larger subset than the first and break determinism.

- **Floating-point summation order is load-bearing.** The VSOP87 series
  was flattened from dicts to tuples for speed; iteration order had to
  be preserved exactly, because addition is not associative and a
  reordering moves the last digits of every position in the engine.
  `_vsop87_xyz_reference` is kept as a test oracle.

- **`AUDIT_RELEASE` is not stamped on anything.** A constant that moves
  with each release, written into a record, makes the *next* release
  claim to have audited this one's work. Every `audited_in` takes a
  frozen per-release constant.
