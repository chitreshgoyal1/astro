# Release notes — V1.8

**Release candidate for the V1 line.** 1,456 tests, all of V1.7's
retained.

V1.8 is a hardening release. It implements the transit rules V1.7
located, produces a correct Hindi PDF, adds the South Indian chart, and
turns a development checkout into something that can be handed to
somebody else.

---

## The headline

**Strict synthesis admits a transit for the first time.**

Three releases refused, each for a better reason than the last. V1.5
refused because the house→domain mapping had no witness. V1.6 found the
mappings and still refused, because "the tenth house signifies career"
and "a graha transiting the tenth affects career" are different claims.
V1.7 located the second claim — Phaladīpikā 26 and 20.34-35 — and still
refused, because a located source is a specification, not permission.

V1.8 implemented it. And the refusal did not go away; it got narrower
and more precise. Chapter 26 is now **fully implemented — all 36 vedha
pairs, both exemptions — and still cannot reach a life area**, because
it judges a transit in the Moon's frame without naming a bhāva. Only
20.34-35, which names one, gets through.

---

## What changed

### Gochara (Parts 1–7)

- `engine/gochara`: reference frames, declarative rule tables, vedha as
  a first-class layer, daśā-lord activation, natal-strength conditions,
  and a strict-eligibility gate.
- Seven grahas with full vedha tables; 36 pairs; both reciprocal
  exemptions (Sun/Saturn, Moon/Mercury).
- Rāhu and Ketu take the Sun's favourable houses and get **no vedha
  table**, because neither witness gives them one.
- Six located layers recorded as **deliberately not implemented**, each
  with its reason.

### Sources (Parts 8–11)

- **D2 → WEALTH added.** V1.7 found `horāyāṃ sampadādikam` in BPHS 7.1
  and recorded that the engine had no such mapping. V1.8 added it — the
  source was not adjusted to fit the code.
- Domain mappings: 65 → **66 of 95** source-qualified.
- **A second Phaladīpikā edition** (Sastri 1950) resolved two corrupt
  words in the digital witness. One of them was *self-refuting* — it
  paired the 11th house with itself — and could be rejected before
  either edition's authority was weighed.
- **`MappingClassification`** (Part 9): every mapping is now
  `TEXTUALLY_ATTESTED`, `TEXTUALLY_DIFFERENT`, `TRADITIONAL_CONVENTION`,
  `MODERN_CONVENTION`, `UNVERIFIED` or `CONTRADICTED`. Derived from the
  evidence, so a label cannot disagree with its own citation.
- **`WitnessAgreement`** (Part 10) distinguishes a second *edition* from
  a second *work*. Two printings of Phaladīpikā settle a reading; they
  are not independent support for a doctrine.
- **Sārāvalī reclassified** (Part 11). It was never unavailable — it has
  been held in full since V1.5. It is `RETRIEVED_IMAGE_ONLY` /
  `TEXT_NOT_REVIEWED`, and `engine/sources/review.py` carries the
  workflow. OCR may assist discovery and is never evidence.

### Devanagari PDF (Parts 16–18)

V1.7 refused a Hindi PDF and named what was missing. V1.8 built both
halves: an OpenType layout engine (GSUB 1/2/4/5/6, GPOS 1/2/4/6/8) and
an Indic v2 shaper, with an OFL-licensed font subset and embedded.

`कार्य` renders as four shapes with the ra raised into a reph above the
ya; `क्षेत्र` as three, with the क्ष conjunct.

Mixed lines are split by script, because Hindi reports carry
untranslated technical identifiers and the bundled Devanagari face has
no Latin letters — sending a whole line through it drew every English
word as empty boxes.

### Report localisation

V1.7 reported Hindi complete. It was, for the 78 engine keys it
measured. The report's own chrome — headings, table columns, cover text
— is generated below the architecture boundary and had never been in
scope. **The first Hindi PDF had 1,232 English strings in it.**

144 chrome strings now live in `templates/<lang>/report.json`, complete
in both languages, with no silent fallback.

### Charts (Parts 19–21)

- South Indian layout, reading the same `ChartVisualModel`.
- `render_chart` dispatches by style; `east_indian` stays named and
  refused.
- Selectable from the UI, the CLI (`--chart-style`) and the report.
- Equivalence tested: every graha, sign, house and marker identical
  across both styles for four divisional charts.

### Performance (Parts 12–15)

| | V1.7 | V1.8 |
|---|---|---|
| Chart, with sensitivity | 0.407 s | 0.23 s |
| Synthesis (365-day scan) | 4.97 s | 2.67 s |
| Synthesis, no scan | — | **0.011 s** |
| End to end | 5.43 s | **2.98 s** |
| Hindi PDF, 33 pages | refused | 4.1 s cold, 1.4 s warm |

Profiled before optimising, as asked. The hotspot was the VSOP87 series
evaluation — 97,000 calls and 64 million cosines in one scan — and it is
now cached. The cache is safe because it sits **upstream of every
methodology choice**: there is no profile for a value to leak into.

Every optimisation is verified to change no answer. The flattened series
is bit-identical to a retained reference implementation; the shaping
filter is verified to produce an identical glyph stream with it
disabled; the no-scan path differs from the full path in
`event_candidates` and nothing else.

One cache-key bug was found and fixed: `_positions_at` accepted
arbitrary kwargs and keyed on three of them.

### Storage and settings (Parts 23–27)

- **Consultation schema 2.0.0**: `calculation` and `presentation` are
  separate blocks, because one can change a chart and the other cannot.
- An explicit, tested `1.0.0 → 2.0.0` migration that consults nothing
  outside its payload.
- Unknown settings are **kept and reported**, not dropped.
- Export/import, with no cached calculation — input plus methodology
  reproduces the chart, and a cache is the part guaranteed to go stale.
- **The cache in a saved consultation is now opt-in.** It made a saved
  file two megabytes; the input and methodology are about one kilobyte.

### Production hardening (Parts 28–35, 43–48)

- `--privacy` states what is stored, where, and what leaves the machine.
- Structured JSON-lines logging, redacting personal fields by default
  and **replacing rather than deleting** them.
- Local crash reports: the traceback, the build, the methodology, and no
  birth details unless `--debug` was used.
- `--self-check`: ten integrity checks, including the font checksum, the
  shaper, and the architecture boundary.
- `tools/build_package.py` and `tools/verify_package.py`: a
  reproducible tarball and 17 checks run in a cleared environment.
- **One version source.** V1.8 found the PDF writer stamping "V1.7" into
  every document it produced.
- Release mode: departures from the conservative defaults are
  classified, and a document produced under an experimental setting
  **says so, beside the findings**.
- Security review: PDF metadata sanitised, download filenames
  whitelisted, and every malformed-consultation case verified to produce
  a message rather than a traceback.

### Tests

1,382 → **1,456**, plus 74 in V1.7's own files.

| New file | Covers |
|---|---|
| `test_gochara.py` (47) | The verses, transcribed; the strict gate |
| `test_release.py` (62) | Versions, storage, diagnostics, a11y, the frozen API |
| `test_properties.py` (26) | Invariants over 60 charts, fixed seed |
| `test_security.py` (21) | Hostile input through every path |
| `test_performance.py` (18) | That the optimisations changed no answer |
| `test_regression_corpus.py` (12) | 200 charts, coverage asserted |
| `test_rc_goldens.py` (12) | Four charts frozen at every stage |

---

## Breaking changes

**Consultation schema 1.0.0 → 2.0.0.** Old files open and migrate
automatically; the migration is reported. Files written by V1.8 cannot
be read by V1.7.

**Prediction schema 1.0.0 → 1.1.0.** Additive — a `gochara` section.
Every 1.0.0 key keeps its meaning.

**`render_north_indian` is no longer the entry point.** Use
`render_chart(model)`, which dispatches by style. The old function still
exists and now refuses a model asking for another style.

**Strict synthesis output has changed.** It admits transit evidence
where the daśā-lord rule qualifies. This is the intended change and it
is the reason for the release.

---

## Five tests were replaced, not deleted

The project's standing rule. When a finding is overturned, the old
assertion is replaced with one pinning the new finding, and the
docstring says what changed.

- Four pinned "the Hindi PDF is refused". They now pin that Hindi
  renders **and** that an unshapeable script is still refused by name —
  a release that removed the refusal without keeping it for the next
  script would have traded a documented limit for a silent one.
- One pinned "5 of 11 varga mappings are attested". Now six of twelve,
  because the engine changed to match a verse the audit had already
  read.

---

## Known limitations

- **Nothing is TRADITION_VALIDATED.** Four releases of source work have
  not produced one. That step needs a scholar.
- **Sārāvalī is held and unread.** The most valuable unread source here;
  it would give second witnesses for the Moon yogas, the Pañca
  Mahāpuruṣa yogas, and gochara.
- **43 rules diverge from their located text.** Recorded, not edited;
  the located readings ship as separate `*_textual` rules.
- **Six varga mappings are unqualified**, one of them contradicted.
- **Phaladīpikā 26.9-24 is not implemented**, so a transit verdict is
  favourable-or-obstructed and not a per-house effect.
- **`balānvita` is operationalised with BPHS 27's threshold** — a
  different work's measure applied to this work's condition. Queued for
  review.
- **No third locale.** The mechanism is in place and complete for two;
  a third was scoped and not delivered.
- **The East Indian chart is refused.**
- **The first Hindi PDF in a process costs about four seconds** while
  the OpenType caches warm.
- **Chart captions and Sanskrit proper nouns remain English** in a Hindi
  report. The chrome and the findings are translated; the chart's own
  caption line is not.

---

## Upgrading

Nothing to do. Old consultation files open and migrate, and the
migration is printed. Run `--self-check` after unpacking a new build.
