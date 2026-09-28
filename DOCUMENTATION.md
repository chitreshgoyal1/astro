# Jyotish Calculator — Software Documentation

**Version:** 1.4
**Date:** 27 September 2026
**Status:** Working build, ready for client review

> **Reading this document.** Four kinds of statement appear throughout, and
> they are labelled wherever they could be confused:
>
> | Label | Meaning |
> |---|---|
> | **ASTRONOMICAL FACT** | Where a body is. Verifiable against any ephemeris. |
> | **CALCULATED ASTROLOGICAL FEATURE** | Follows mechanically from positions plus a named convention (house, lordship, dignity, drishti, varga standing). |
> | **TRADITION-SPECIFIC RULE** | True within a stated school, cited to a source. Other schools may differ. |
> | **SOFTWARE HEURISTIC** | An engine convention with no classical standing — `engine_strength_score`, boundary-warning thresholds. Always labelled as such. |
>
> **V1.3 adds a fourth separation, about evidence rather than content.** These
> four claims are kept apart everywhere, and none is evidence for any other:
>
> | Claim | Status in this build |
> |---|---|
> | COMPUTATIONALLY TESTED | Yes — 748 tests |
> | EXTERNALLY BENCHMARKED | Yes, for astronomy |
> | TEXTUAL SOURCE LOCATED | 5 of 110 yoga rules; **6 of 8 V1.4 calculation modules** |
> | **TRADITION/SOURCE VALIDATED** | **Nothing** |
>
> **95% of the yoga rules in this engine have no examined textual source.**
> The `BPHS ch.36`-style citations they carry were written from memory during
> implementation and have never been checked.
>
> **V1.4 changed the method, not yet the backlog.** The BPHS chapters for
> Shadbala (27) and Ashtakavarga (66) were located and read *before* those
> modules were written, giving them a 75% located ratio against the yoga
> catalog's 5%. The ~100 yoga citations remain unaudited — a named edition
> now exists to check them against. See `SOURCE_VALIDATION.md`.
> | **INTERPRETATION** | What it means for the person. **Not yet implemented.** |
>
> Accuracy figures in section 3 are **measured**, not estimated — see
> `AUDIT.md` and `tests/fixtures/accuracy_profile.json`.

---

## 1. What this software does

A self-contained Vedic astrology (Jyotish) calculation engine. It takes a birth
record — date, exact time, place, and optionally the planetary degrees — and
produces a full sidereal chart, all sixteen divisional charts (Shodashavarga),
and an interpretation report. Output goes to the console and, optionally, to a PDF.

Two principles drive the design:

1. **Entered degrees are authoritative.** If the astrologer supplies planetary
   degrees, those values are used verbatim by the interpretation engine. The
   software never silently overwrites them with its own calculation.
2. **Methodology is explicit, never assumed.** Different traditions compute some
   divisional charts differently. The convention used for each Varga is a
   configuration choice and is printed alongside the results.

No third-party libraries are required. Python 3.10 or newer, standard library only.

---

## 2. Input — the consultation form

### 2.1 Fields collected

| Field | Required | Notes |
|---|---|---|
| Name | Yes | Appears on the report and the PDF filename |
| Date of birth | Yes | `YYYY-MM-DD` |
| Exact time of birth | Yes | `HH:MM`, 24-hour local time |
| Place of birth | Yes | Looked up in the city table (see 2.3) |
| Ascendant degree | Optional | Lagna |
| Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu degrees | Optional | Sanskrit names used internally: Surya, Chandra, Mangal, Budha, Guru, Shukra, Shani, Rahu, Ketu |
| Zodiac / Ayanamsha | Optional | Defaults to sidereal / Lahiri |

### 2.2 Accepted degree formats

The parser accepts any of these for each body:

| Example | Meaning |
|---|---|
| `128.5` | Absolute sidereal longitude, 0–360° |
| `Simha 8 30` | Sign + degrees + minutes |
| `Simha 8°30'15"` | Sign + degrees, minutes, seconds |
| `8°30' Simha` | Degrees before the sign |
| `Leo 8 30` | English sign names also accepted |
| `Dhanu 26 15 R` | Trailing `R` / `retro` marks retrograde |

Sign names accepted in Sanskrit (Mesha, Vrishabha, …), common variants, and
English (Aries, Taurus, …) with abbreviations. Rahu and Ketu are treated as
retrograde unless stated otherwise.

Invalid entries are rejected with a clear message — minutes ≥ 60, a degree above
30° inside a sign, or an unknown sign name will not be silently accepted.

### 2.3 Place of birth

Coordinates and time zone are resolved by `engine/location.py`, which carries
62 built-in places. Matching is exact or by unambiguous prefix.

**An unknown birth place is never guessed at.** It must either resolve to real
coordinates, or be given explicitly, or the run fails:

```bash
python3 main.py --place "Sehore" --lat 23.2032 --lon 77.0856 --timezone Asia/Kolkata
python3 main.py --place "Somewhere" --lat 10 --lon 20 --utc-offset +05:30
python3 main.py --list-cities
```

An unresolvable place exits with status 2 and a message naming the flags that
fix it. No chart is produced.

> **Why this changed in V1.1.** V1 fell back to Delhi's coordinates with a
> printed warning. That is worse than refusing: it produces a confidently
> wrong Lagna rather than an obvious failure.
>
> **The sensitivity is larger than V1 documented.** 1° of geographic longitude
> corresponds to **4 minutes of *time***, and in four minutes the Ascendant
> moves roughly **one degree** — measured at 34–83 arcminutes depending on
> latitude and on the rising rashi, not the "4 minutes of arc" V1 claimed.
> Substituting one city for another can therefore move the Lagna by a whole
> rashi, changing every house and every yoga downstream.

The birth location is modelled explicitly:

```
BirthLocation:
    name, latitude, longitude, timezone_name, utc_offset_at_birth, source
```

Where the IANA time-zone database is available the offset is resolved **for
the birth moment**, so daylight saving and historical rules are applied rather
than a fixed modern offset being assumed. The `source` field records how the
location was resolved and is printed on every report.

### 2.4 Three ways to supply input

| Mode | Command |
|---|---|
| JSON consultation file | `python3 main.py --consultation chitresh_consultation.json` |
| Command-line flags | `python3 main.py --name "..." --dob 1988-08-30 --time 20:18 --place Jaipur` |
| Interactive prompts | `python3 main.py` (asks each question in turn) |

Sample input file:

```json
{
  "name": "Chitresh Goyal",
  "dob": "1988-08-30",
  "tob": "20:18",
  "place": "Jaipur",
  "zodiac": "sidereal",
  "ayanamsha": "Lahiri",
  "positions": {
    "Lagna": "Meena 15 47",
    "Surya": "Simha 13 44",
    "Chandra": "Meena 28 07"
  }
}
```

Leave `positions` empty (`{}`) to have every position calculated.

---

## 3. Calculation engine

### 3.1 Astronomy (`engine/ephemeris.py`)

**ASTRONOMICAL FACT.** Every figure below is the **measured** error against
the Swiss Ephemeris across 1800–2050, produced by `tools/measure_accuracy.py`.
These are not estimates.

| Component | Method | Median | **Worst** |
|---|---|---|---|
| Sun | Meeus, *Astronomical Algorithms* ch. 25 | 8.1″ | **34″ (0.57′)** |
| Moon (longitude) | Meeus ch. 47, 59 periodic terms | 1.8″ | **10″ (0.17′)** |
| Moon (latitude) | Meeus ch. 47 Σb series | 0.6″ | **2.7″** |
| Mercury | JPL Keplerian elements, light-time, aberration | 1.4″ | **12″ (0.21′)** |
| Venus | as above | 4.0″ | **39″ (0.64′)** |
| Mars | **VSOP87A** *(V1.3)* | **0.5″** | **8.0″ (0.13′)** |
| **Jupiter** | **VSOP87A** (Bretagnon & Francou 1988) | **0.5″** | **3.1″ (0.05′)** |
| **Saturn** | **VSOP87A** | **0.8″** | **4.1″ (0.07′)** |
| Earth | **VSOP87A** — underlies every geocentric position | — | — |
| **Rahu / Ketu (true)** | osculating node — **now the limiting body** | 11.3″ | **67″ (1.11′)** |
| Rahu / Ketu (mean) | Meeus ch. 47 mean node | 12.1″ | **18″ (0.30′)** |
| Ayanamsha (all four) | J2000 anchor + IAU precession in longitude | 0.001″ | **0.002″** |
| Ascendant | apparent sidereal time with nutation | 0.5″ | **4.5″** |
| Midheaven | as above | 0.2″ | **1.2″** |
| ΔT, 1800–2026 | interpolated observed values | — | **0.03 s** |
| ΔT, after 2026 | projection — unpredictable | — | **12 s by 2050** |

### 3.1a Mars: the V1.3 upgrade

| | Mars |
|---|---|
| V1.2 (JPL Keplerian elements) | 184.6″ = **3.08′** |
| V1.3 (VSOP87A) | **8.0″ = 0.13′** |
| Improvement | **23×** |

Same pipeline as the others: authoritative IMCCE coefficients, SHA-256
recorded, parse validated against the theory authors' own `vsop87.chk` before
anything was measured. Truncated finer than the rest (10⁻⁷ au, 862 terms)
because Mars is nearest to the Earth, so the same absolute error subtends a
larger angle.

**The limiting body is now Rahu/Ketu at 1.11′.** That is not a planetary-theory
problem — the node is derived from this engine's own lunar series — so scope
was deliberately not widened to chase it.

**The migration changed no astrology.** Across all 74 fixture cases, zero
rashi, nakshatra, pada or varga classifications changed. No expected value was
edited. Reproduce with `python3 tools/mars_migration_report.py`.

### 3.1b Jupiter and Saturn: the V1.2 upgrade

| | Jupiter | Saturn |
|---|---|---|
| V1.1 (JPL Keplerian elements) | 599″ = **10.0′** | 807″ = **13.5′** |
| V1.2 (VSOP87A) | **3.1″** | **4.1″** |
| Improvement | **193×** | **197×** |

**Provenance.** The coefficients are VSOP87 variant A (heliocentric
rectangular, ecliptic J2000), taken directly from IMCCE —
`ftp://ftp.imcce.fr/pub/ephem/planets/vsop87/` — with the source files' SHA-256
hashes recorded in `engine/vsop87_data.py`. Nothing was fitted, rounded or
tuned. The parse was validated against `vsop87.chk`, **the reference values
published by the theory's own authors**, reproducing them to 7.8 × 10⁻¹¹ au.

**Earth was upgraded too, and this was measured rather than assumed.**
Geocentric longitude is the direction of the Earth-to-planet vector, so the
Earth's own position error projects onto every planet:

| Configuration | Jupiter worst | Saturn worst |
|---|---|---|
| Keplerian Earth + VSOP Jupiter/Saturn | 7.12″ | 5.81″ |
| **VSOP Earth + VSOP Jupiter/Saturn** | **2.90″** | **4.23″** |

That also improved Mercury (3.4×) and Venus (2.4×) at no extra cost.

**Truncation.** Terms are dropped by amplitude only, at 10⁻⁶ au: 1,874 terms
(110 Earth, 639 Jupiter, 1,125 Saturn), within 0.25″ of the full 15,484-term
series. Everything downstream is unchanged — light-time, aberration,
precession, nutation, ayanamsha, retrogression and station detection all still
apply.

> **Honest limit on this claim.** The residual few arcseconds is *at the
> resolution of the reference*. Swiss Ephemeris in Moshier mode itself differs
> from the JPL DE series by of order an arcsecond for the outer planets. So the
> defensible statement is "agrees with an independent reference to within a few
> arcseconds", not "accurate to 3 arcseconds absolutely".

### 3.1c Numerical uncertainty and boundary safety *(V1.2)*

**SOFTWARE HEURISTIC over an ASTRONOMICAL FACT.** The engine now says when a
classification is *not resolved by its own arithmetic*.

A placement is **UNRESOLVED** when it sits nearer a rashi, nakshatra, pada or
varga boundary than the measured worst-case error for that body. Because the
envelopes differ enormously — 0.05′ for Jupiter, 3.20′ for Mars — the same
longitude can be certain for one graha and a coin toss for another.

This appears in the report as a NUMERICAL CERTAINTY table, and in the snapshot
per graha:

```json
{
  "planet": "Mangal",
  "longitude": 89.983333,
  "accuracy_arcmin": 3.2,
  "boundary_warning": true,
  "boundary_type": "rashi"
}
```

D30 is excluded from varga boundary checks: Trimshamsha has unequal parts, so
one division span does not describe it, and a number that is not true of the
chart is worse than none.

> **Correction to V1.** The previous documentation claimed "1–3 arcmin" for
> Mercury–Saturn and "~1 arcmin" for the nodes. Both were wrong. Jupiter is
> 10′ and Saturn 13.5′ — three to four times the claimed bound — and the V1
> true node was in error by **17.6 arcminutes**, not one. The node has been
> corrected this phase (see below); Jupiter and Saturn have not, and their
> limit is now stated honestly.

> **Practical limit you need to know.** A **Jupiter** placement within ~10
> arcmin, or a **Saturn** placement within ~15 arcmin, of a sign, nakshatra or
> pada boundary is **not resolved by this engine** and should be verified
> externally. Every other body has comfortable margin.

**Rahu/Ketu improved in V1.1.** The true node is now computed geometrically —
two lunar positions a tenth of a day apart span the instantaneous orbital
plane, and the node is where that plane meets the ecliptic — instead of from a
five-term correction series. Worst-case error fell from 17.6′ to 1.1′, a
sixteen-fold improvement, using only this engine's own lunar series.

> **Note:** the **true** node is direct about a quarter of the time. Only the
> **mean** node is unconditionally retrograde. Rahu shown as direct is not
> necessarily an error.

Local birth time is converted to UTC using the resolved offset, then to
Terrestrial Time using ΔT before any position is computed.

**Retrogression is derived, not assumed** — daily motion is measured by central
difference of the computed longitude. Over 10 957 daily samples per body
(1990–2020) the retrograde flag disagreed with the reference on 0 days for the
Sun, Moon, Mercury and Venus, 1 day for Mars and Jupiter, and 7 days for
Saturn — every one of them within a day or two of a station.

Where |speed| < 0.005 °/day the engine reports **stationary** rather than
direct or retrograde. That threshold is an honesty device: below it the
engine's own accuracy cannot resolve the direction of travel. It is not a
classical definition of a stationary period.

Local birth time is converted to UTC using the place's offset, then to
Terrestrial Time using ΔT before any position is computed.

**Retrogression is derived, not assumed** — daily motion is measured by central
difference of the computed longitude, so retrograde and stationary states fall
out of the arithmetic.

### 3.2 Built-in accuracy check

```bash
python3 main.py --selftest
```

Validates the engine against published worked examples:

| Check | Reference | Error |
|---|---|---|
| Sun λ, 1992-10-13 | Meeus example 25.b | 0.03″ |
| Moon λ, 1992-04-12 | Meeus example 47.a | 0.28″ |
| Moon β, 1992-04-12 | Meeus example 47.a | 0.00″ |
| True node libration amplitude | 1.889° over an 18.6-year cycle | 0.002° |
| Venus λ, 1992-12-20 | Meeus example 33.a | 2.06″ |
| Venus β, 1992-12-20 | Meeus example 33.a | 1.80″ |
| Mean obliquity, 1987-04-10 | Meeus example 22.a | 0.00″ |
| Lahiri ayanamsha at J2000 | Swiss Ephemeris | 0.00″ |
| ΔT in 1988 | Observed 56.1 s | 0.02″ |

These are published worked examples and physical invariants. The broader
accuracy measurement — against an independent ephemeris across 250 years — is
a separate exercise; run `python3 -m unittest discover -s tests`.

### 3.3 Selectable settings

| Setting | Options | Default |
|---|---|---|
| Ayanamsha | `lahiri`, `raman`, `krishnamurti`, `fagan_bradley` | `lahiri` |
| Lunar node | `true`, `mean` | `true` |
| House system | Whole sign (Rashi) | fixed |

> **Open item for client:** house system is currently whole-sign only. If Sripati,
> Placidus or Bhava Chalit is expected, that must be added.

### 3.4 Chart assembly (`engine/planets.py`)

For every graha the engine produces: sidereal longitude, rashi and rashi lord,
degree within sign in D°M′S″, nakshatra, nakshatra lord, pada, daily speed,
retrograde flag, stationary flag, ecliptic latitude, combustion flag, and dignity.

**Dignity** (CALCULATED ASTROLOGY FEATURE) is classified as Parama Uchcha,
Uchcha, Moolatrikona, Swa, Neecha, Parama Neecha, or Neutral.

**Combustion** (TRADITION-SPECIFIC RULE) uses a replaceable profile. The
default arcs from the Sun:

| Graha | Direct | Retrograde |
|---|---|---|
| Chandra | 12° | — |
| Mangal | 17° | — |
| Budha | 14° | **12°** |
| Guru | 11° | — |
| Shukra | 10° | **8°** |
| Shani | 15° | — |

The narrower retrograde arcs for Budha and Shukra are new in V1.1: a
retrograde inferior planet meets the Sun at inferior conjunction and is nearer
the Earth, and several sources give it a tighter arc accordingly.

**Rahu and Ketu are never combust.** They are chaya grahas — shadow points,
not bodies that the Sun's rays can burn. Their angular separation from the Sun
is still recorded, so a rule can read the distance without the engine implying
a combustion verdict.

The **angular separation from the Sun is stored for every graha**, combust or
not. V1 computed it and discarded everything but the boolean.

---

## 4. The 16 Vargas (`engine/vargas.py`)

All sixteen charts of the Shodashavarga are produced:

| Chart | Sanskrit | Use |
|---|---|---|
| D1 | Rāśi | Overall life |
| D2 | Horā | Wealth, resources |
| D3 | Drekkāṇa | Siblings, efforts |
| D4 | Chaturthāṁśa | Property, fortune |
| D7 | Saptāṁśa | Children |
| D9 | Navāṁśa | Dharma, marriage, planetary strength |
| D10 | Daśāṁśa | Career, profession |
| D12 | Dvādaśāṁśa | Parents, lineage |
| D16 | Ṣoḍaśāṁśa | Vehicles, comforts |
| D20 | Viṁśāṁśa | Spiritual matters |
| D24 | Chaturviṁśāṁśa | Education, knowledge |
| D27 | Bhāṁśa | Strengths, weaknesses |
| D30 | Triṁśāṁśa | Difficulties, misfortune |
| D40 | Khavedāṁśa | Auspicious / inauspicious influences |
| D45 | Akṣavedāṁśa | Character, influences |
| D60 | Ṣaṣṭyāṁśa | Fine-level karmic analysis |

### 4.1 Configurable conventions

Each Varga is computed by a **named convention**, selected in a JSON file. This
is the mechanism that prevents the software from silently assuming a tradition.

| Chart | Conventions available | Default |
|---|---|---|
| D1 | `standard` | `standard` |
| D2 | `parashari`, `parivritti` | `parashari` |
| D3 | `parashari`, `parivritti` | `parashari` |
| D4 | `parashari`, `parivritti` | `parashari` |
| D7 | `parashari`, `parivritti` | `parashari` |
| D9 | `standard` | `standard` |
| D10 | `parashari`, `parivritti` | `parashari` |
| D12 | `parashari`, `parivritti` | `parashari` |
| D16 | `parashari`, `parivritti` | `parashari` |
| D20 | `parashari`, `parivritti` | `parashari` |
| D24 | `parashari`, `parivritti` | `parashari` |
| D27 | `parashari`, `parivritti` | `parashari` |
| D30 | `parashari`, `movable_lords`, `parivritti` | `parashari` |
| D40 | `parashari`, `parivritti` | `parashari` |
| D45 | `parashari`, `parivritti` | `parashari` |
| D60 | `parashari`, `reverse_even`, `parivritti` | `parashari` |

What each convention means:

- **parashari** — the classical BPHS rule for that chart (trines for D3, kendras
  for D4, parity-based starts for D7/D10/D24/D40, sign-category starts for
  D16/D20/D27/D45, unequal 5/5/8/7/5 parts for D30).
- **parivritti** — cyclic (parivritti-traya) counting, where all 12 × n divisions
  run continuously from Mesha.
- **movable_lords** (D30) — as Parashari, but Shani maps to Makara and Mangal to
  Mesha for both parities.
- **reverse_even** (D60) — counted forward for odd signs, in reverse for even signs.

List them at any time:

```bash
python3 main.py --list-conventions
```

Select them in `varga_config.json`:

```json
{ "conventions": { "D2": "parivritti", "D30": "movable_lords" } }
```

An unknown chart name or convention is **rejected with an error** — never
silently ignored. The active methodology is printed above the Varga grid in
every report, and carried into the PDF.

> **Open item for client:** please confirm the default convention for each chart
> matches your tradition, especially **D2, D16, D20, D24, D30, D40 and D60**,
> which vary most between schools. If your lineage uses a rule not listed, it can
> be registered as a new named convention.

### 4.2 Verification (V1.1)

**No Varga convention was changed.** The Phase 2 audit found no error in any
of the sixteen rules, so they stand exactly as they were, and the default set
is now pinned by a test so it cannot drift silently.

Each rule was checked against a **second, independent implementation** written
longhand from the classical statement in `tests/test_vargas_golden.py`. The
engine derives its rules from generic combinators driven by tables; the
reference writes each out in the words of the text. The two agree at:

* **138 240** sampled longitudes (16 Vargas × 12 rashis × 720 samples),
* **6 456** division boundaries, each approached from both sides, and
* **70** hand-worked spot values.

### 4.3 Four options that cannot change anything

For **D7, D16, D20 and D27** the `parivritti` convention is **mathematically
identical** to the `parashari` default at every longitude — verified over
36 000 samples each. This is an arithmetic coincidence, not a defect in either
rule:

| Varga | Why they coincide |
|---|---|
| D7 | 7 ≡ 7 (mod 12), and 6s ≡ 0 for odd rashis, 6 for even ones — exactly the rule's offset |
| D16 | 16 ≡ 4 (mod 12); movability has period 3 and 4 × 3 ≡ 0 |
| D20 | 20 ≡ 8 (mod 12); movability has period 3 and 8 × 3 ≡ 0 |
| D27 | 27 ≡ 3 (mod 12); element has period 4 and 3 × 4 ≡ 0 |

Both options remain selectable, but selecting either produces the same chart.
Recorded here so the choice is not mistaken for a meaningful one.

---

## 5. Entered vs calculated comparison (`engine/compare.py`)

When degrees are entered, the report shows both sets side by side:

```
  Body           Entered   Calculated       Delta  Review
  Lagna         72.6667°     74.3531°    -01° 41'  ! > 1°
  Chandra      351.1667°    315.5513°    +35° 37'  ! different rashi
```

- Delta is the signed shortest arc, shown in degrees and minutes.
- A different rashi is always flagged.
- Any difference above the tolerance (default 1°, set with `--tolerance`) is flagged.
- **The entered values are still used for the interpretation.** The comparison is
  advisory only — it exists to catch data-entry errors, wrong time zones and
  ayanamsha mismatches.

If some bodies are left blank, the calculated value is used for those only, and a
warning lists exactly which ones.

---

## 6. Astrology feature engine (`engine/features/`) — new in V1.1

**CALCULATED ASTROLOGY FEATURE.** A reusable layer that derives every fact a
rule might need, once, from the positions and the active conventions. The rule
engine consumes it and never recalculates — that constraint is what stops two
implementations of "is Mangal aspecting the 7th" from drifting apart.

| Module | Provides |
|---|---|
| `lordships.py` | Lord of every bhava; bhavas owned by each graha |
| `aspects.py` | Parashari graha drishti, configurable, incl. node conventions |
| `conjunctions.py` | Same-rashi and orb proximity, kept separate; graha yuddha |
| `dispositors.py` | Dispositor, chain, final dispositor, Parivartana |
| `dignity.py` | Exalted / debilitated / own / moolatrikona / friendly / enemy |
| `functional_nature.py` | Lagna-dependent roles: kendra, trikona, dusthana, maraka, yogakaraka |
| `varga_features.py` | Divisional placements, lords, vargottama, per-varga dignity |
| `relationships.py` | Natural, temporary and compound graha friendship |
| `models.py` | `PlanetFeatures`, `HouseFeatures`, `ChartFeatures` |

### 6.1 Lordship

For the D1 Lagna, the lord of every house and the houses each graha owns:

```json
{ "1": "Guru", "2": "Mangal", "3": "Shukra", "4": "Budha", ... }
```

Rahu and Ketu own no rashi under the Parashari scheme, so they never appear as
a house lord and are returned with an empty ownership list rather than omitted.

### 6.2 Aspects (Graha Drishti)

**TRADITION-SPECIFIC RULE.** Houses are counted inclusively, so a graha's own
house is 1 and the opposite is 7.

| Graha | Aspects |
|---|---|
| All grahas | 7th |
| Mangal | 4th, 7th, 8th |
| Guru | 5th, 7th, 9th |
| Shani | 3rd, 7th, 10th |
| **Rahu / Ketu** | **configurable — the default asserts nothing** |

Node drishti is where traditions disagree most sharply: some give the nodes no
aspect, some Jupiter-like 5/7/9, some the kendras. Rather than pick one
silently, `--node-aspects` selects between `none` (default), `parashari_like`
and `kendra`, and the choice is printed in the report's provenance block. Any
Yoga that depends on a node aspect therefore carries the convention that
produced it.

### 6.3 Conjunctions — two different ideas, never merged

| Concept | Meaning |
|---|---|
| `same_sign` | The grahas share a rashi. **This is what classical Yoga rules mean.** True at 0°01′ apart and at 29°59′ apart within one rashi. |
| `within_orb` | Angular separation within a stated orb (default 8°). A modern refinement. |

```json
{ "planet1": "Chandra", "planet2": "Mangal", "same_sign": true,
  "angular_separation": 10.44, "within_orb": false, "orb_used": 8.0 }
```

Forcing an orb onto a same-rashi rule would silently change what the rule
says, so both are stored and each rule states which it relies on.

### 6.4 Dispositors

Sign dispositor, the full chain, the final dispositor, and mutual reception
(Parivartana, classified `maha` / `dainya` / `khala`). Every chain terminates
either at a self-dispositing graha or in a closed loop — the two-graha loop
being the classical exchange — and loops are detected explicitly rather than
guarded against by a recursion limit.

### 6.5 Functional nature

**Natural** benefic/malefic character (permanent) and **functional** nature
(entirely Lagna-dependent) are reported separately and never conflated. Guru
is a natural benefic in every chart ever cast; from a Vrishabha Lagna it owns
the 8th and 11th, and its functional standing is quite different.

Identified per Lagna: lagna lord, kendra lords, trikona lords, dusthana lords,
maraka lords, and **Yogakaraka** candidates (owning both a kendra and a
trikona, counting the 1st house only once). Facts only — no predictions.

---

## 7. Yoga rule engine (`engine/rules/`) — rebuilt in V1.1

### 7.0 Why it was rebuilt

**The V1 rules did not implement the combinations they were named after.**

| V1 rule | What it actually tested | What the classical rule requires |
|---|---|---|
| "Raja Yoga" | any dignified graha in a kendra | a **relationship** between a kendra lord and a trikona lord |
| "Dhana Yoga" | any exalted graha in the 2nd or 11th | a **relationship** among the lords of the 1st, 2nd, 5th, 9th, 11th |
| "Neecha Bhanga Raja Yoga" | any debilitated graha in a kendra | debility **cancelled** by a named clause, **and** on a kendra or trikona |
| "Kemadruma" | presence only, no cancellation | forms on isolation, but is **cancelled** by any bhanga clause |

The Raja and Dhana rules had no notion of house lordship at all. The Neecha
Bhanga rule inverted its own meaning — it fired on the *absence* of a
cancellation. Kemadruma was the most misleading in practice, because the
bhanga clauses are common: in the documented worked example **four** of them
apply, so reporting bare presence inverts the reading.

### 7.1 A Yoga is not a boolean

Every result resolves to one of five states:

| State | Meaning |
|---|---|
| `ABSENT` | The formation conditions do not hold |
| `PRESENT` | Formed, not cancelled, no strength verdict |
| `PRESENT_BUT_CANCELLED` | Formed, but a classical bhanga clause applies |
| `PRESENT_BUT_WEAKENED` | Formed and operative, but materially weakened |
| `PRESENT_AND_STRONG` | Formed and reinforced |

Evaluation is strictly ordered — **existence, then cancellation, then
strength** — and strength is never computed for a Yoga that does not exist.
Collapsing that order is what produced V1's "Raja Yoga" from a merely
dignified graha.

### 7.2 What each rule carries

```
YogaRule: id, name, category, tradition, source, explanation,
          conditions_all, conditions_any, cancellation_conditions,
          strength_modifiers, planets_involved, houses_involved, variant_of

YogaResult: id, name, status, present, effective, conditions_met,
            conditions_failed, cancellations_found, modifiers,
            planets, houses, strength, source, tradition
```

### 7.3 The rule set (110 rules; 122 with variants)

| Group | Rules | Source |
|---|---|---|
| Pancha Mahapurusha | Ruchaka, Bhadra, Hamsa, Malavya, Shasha | BPHS ch.75; Phaladeepika 6.1 |
| Budha-Aditya | 1 | BPHS ch.34; Phaladeepika 6.15 |
| Chandra-Mangala | 1 (+1 variant) | BPHS ch.40.9 |
| Gajakesari | 1 | BPHS ch.34; Phaladeepika 6.11 |
| Kemadruma + 4 bhanga clauses | 1 | BPHS ch.34.6–7 |
| Neecha Bhanga | 7 (one per graha) | BPHS ch.75 |
| Neecha Bhanga Raja Yoga | 7 (one per graha) | BPHS ch.75 with ch.36 |
| **Raja Yoga** | **33** — each kendra-lord/trikona-lord pair × conjunction, mutual aspect, exchange | BPHS ch.36 |
| Dharma-Karmadhipati | 3 | BPHS ch.36; Phaladeepika 6.36 |
| **Dhana Yoga** | **31** — each pair from houses 1/2/5/9/11 × three modes, plus the classical 2↔11 placement | BPHS ch.40 |
| Vipareeta Raja | 3 — Harsha, Sarala, Vimala *(V1.2)* | BPHS ch.36; PD 6.38 |
| Parivartana | 3 — maha, dainya, khala *(V1.2)* | BPHS ch.36 |
| Chandra-relative | 3 — Sunapha, Anapha, Durudhara *(V1.2)* | BPHS ch.34; PD 6.3 |
| Surya-relative | 3 — Vesi, Vasi, Ubhayachari *(V1.2)* | BPHS ch.34; PD 6.2 |
| Adhi Yoga | 1 *(V1.2)* | BPHS ch.36; PD 6.13 |
| Amala Yoga | 1 *(V1.2)* | BPHS ch.36; PD 6.35 |
| Lakshmi Yoga | 1 *(V1.2)* | PD 6.34; BPHS ch.36 |
| Saraswati Yoga | 1 *(V1.2)* | PD 6.33; Jataka Parijata |
| Kemadruma Bhanga | 4 — each clause findable on its own *(V1.2)* | BPHS ch.34.7 |

**There is no generic Raja Yoga and no generic Dhana Yoga.** Each is a *class*
of combinations, and each member is its own rule with its own id, so a result
names the actual combination that formed rather than a category.

### 7.4 Differing authorities are never merged

Where two authorities define a combination differently, they are **separate
rules in separate profiles**, and the variant carries `variant_of` pointing at
the combination it extends.

| Profile | Contents |
|---|---|
| `parashari` (default) | BPHS mainstream readings only |
| `parashari_extended` | Adds Mahapurusha from the Moon, Chandra-Mangala by aspect, Adhi and Amala from the alternate reference point, and a stricter Gajakesari |
| `parashari_strict` *(V1.2)* | Mainstream, but with the strict Vipareeta reading — a dusthana lord must fall into a **different** dusthana, not its own |

Selected with `--rule-profile`.

**Two disciplines applied when extending the catalog in V1.2:**

* **Nothing was invented.** Where a source words a condition vaguely — Lakshmi
  Yoga's "strong Lagna lord" — the concrete reading the sources share (own
  rashi or exaltation) is implemented, and the rule's note says so. No broader
  notion was invented to widen it.
* **Untraced attributions say so.** Variant rules whose source could not be
  traced to a chapter carry "exact attribution not established" rather than a
  citation that may not contain them.

### 7.5 On strength scores — `engine_strength_score`

**SOFTWARE HEURISTIC. No classical text scores a Yoga numerically.**

Renamed in V1.2 so the number cannot be mistaken for doctrine. It is carried
with its own disclaimer attached:

```json
{
  "engine_strength_score": 78,
  "score_type": "software_heuristic",
  "classical_measure": false
}
```

`strength` remains as a read-only alias for V1.1 callers.

**The existence guarantee.** A Yoga's presence NEVER depends on this score.
Formation is decided by the rule's own conditions; the score is computed
afterwards and can only choose between `PRESENT`, `PRESENT_AND_STRONG` and
`PRESENT_BUT_WEAKENED` — all of which are present. The only thing that makes a
formed Yoga ineffective is an explicit cancellation clause belonging to that
rule.

This is tested structurally, not by example: across many charts and every rule,
an ABSENT yoga always has a failed condition to point at, and every
"present but not effective" result has a cancellation.

Retrogression is recorded as a modifier with **weight 0.0** and a stated
reason: authorities split on whether a retrograde graha is strengthened
(cheshta bala) or frustrated, and taking a side silently would be wrong.

---

## 8. Timing engine (`engine/timing/`) — rebuilt in V1.2

**TRADITION-SPECIFIC RULE** resting on an **ASTRONOMICAL FACT** (the Moon's
longitude). Deterministic, exact, and independent of the rule and feature
layers — a test enforces that it imports neither.

### 8.1 Hierarchy

```
Mahadasha          9 periods over 120 years
  Antardasha       81
    Pratyantardasha  729
      Sukshma        supported, not built by default
        Prana        supported, not built by default
```

Every level comes from **one generic subdivision**:

```
child_duration = parent_duration × years[child_lord] / 120
```

Antardasha and pratyantardasha are the same operation at different depths, not
two calculations, so Sukshma and Prana need only a deeper `--dasha-depth`.

### 8.2 The birth balance

The Moon's position within its nakshatra gives the fraction of the first
mahadasha already elapsed, so **that mahadasha starts before birth**. The
balance remaining at birth — the figure classical practice quotes — is
reported explicitly.

### 8.3 Year-length convention — an explicit choice

The classical texts state period lengths in years but never define the year in
days. The choice shifts long-period boundaries by months, so it is named,
selectable with `--dasha-year`, and recorded in every result.

| Convention | Days | Note |
|---|---|---|
| **`julian` (default)** | 365.25 | Makes the 120-year cycle exactly 43,830 days |
| `gregorian` | 365.2425 | Mean Gregorian calendar year |
| `sidereal` | 365.25636 | Arguably the most defensible for a sidereal system |
| `savana` | 360 | Some traditions; shortens the cycle by ~1.7 years |

### 8.4 Precision

Durations are exact `Fraction`s of days and every boundary is an offset from
its parent's start — nothing accumulates by repeated rounded arithmetic. The
consequences are equalities, and are tested as such:

* children sum to their parent **exactly**;
* the first child starts **exactly** at the parent's start;
* the last child ends **exactly** at the parent's end;
* the last pratyantardasha of the 120-year span ends **exactly** at its end.

Intervals are half-open: the instant a period ends belongs to the next period,
never to both and never to neither.

### 8.5 Query API

```python
dasha = compute_vimshottari(moon_longitude, birth, depth=3)

dasha.get_mahadasha_at(when)
dasha.get_antardasha_at(when)
dasha.get_pratyantardasha_at(when)
dasha.get_dasha_stack_at(when)
dasha.get_periods_between(start, end, level="antardasha")
```

```json
{
  "date": "2030-06-10T00:00:00",
  "mahadasha": "Chandra",
  "antardasha": "Budha",
  "pratyantardasha": "Surya"
}
```

This is what the transit engine will drive.

---

## 8A. Legacy V1 interpretation (`engine/fal.py`) — isolated in V1.2

The V1 interpretation code is retained **unchanged** so anyone depending on
its exact output still has a path to it. It is **not** part of the normal
report.

> **Why it is opt-in.** It contains a second, superseded yoga system. Printing
> it beside the rule engine's would put two contradictory answers in one
> document — "Raja Yoga" there means a dignified graha in a kendra, and
> Kemadruma is reported with no cancellation analysis.

```bash
python3 main.py --consultation chart.json --legacy-fal
```

The output carries its own banner:

```
  LEGACY V1 INTERPRETATION
  NOT USED BY THE CURRENT RULE ENGINE
```

**Legacy results are never merged into the new ones**, and never appear in the
`ChartSnapshot`. Tests assert all three properties.

The V1 graha-fal text has no replacement yet; it is house-wise boilerplate and
belongs to the interpretation layer, which is out of scope.

---

## 8B. Canonical chart snapshot (`engine/snapshot.py`) — new in V1.2

One versioned, serialisable object holding everything the engine knows. This
is the **formal contract** for the transit engine, timing rules, an
interpretation layer, an API, a UI and the PDF generator.

```bash
python3 main.py --consultation chart.json --json-output chart.json
python3 main.py --consultation chart.json --json-output chart.json --json-compact
```

```json
{
  "schema_version": "1.0.0",
  "birth": { "name": "...", "datetime_local": "...", "location": {...} },
  "calculation_settings": {
      "zodiac": "sidereal", "ayanamsha": "Lahiri",
      "node": "true", "house_system": "whole_sign"
  },
  "accuracy": { "envelopes_arcmin": {...}, "theories": {...},
                "vsop87": {...}, "boundary_warnings": {...} },
  "lagna":    {...},
  "planets":  {...},
  "houses":   {...},
  "vargas":   { "conventions": {...}, "lagna": {...}, "bodies": {...} },
  "features": {...},
  "yogas":    [...],
  "timing":   { "vimshottari": {...} }
}
```

**It contains facts, not prose.** A test asserts that no predictive phrasing
appears anywhere in it.

**Versioning.** `schema_version` is semantic: major for a removal or a changed
meaning, minor for an addition, patch for a value change. Everything is
JSON-native — `json.dumps()` works with no custom encoder, and a test asserts
every leaf is a JSON primitive.

---

## 9. Output

### 9.1 Console report sections

1. Birth details with the resolved coordinates, UTC time, offset and **how the
   place was resolved**
2. Entered degrees table (if supplied)
3. Entered vs calculated comparison (if supplied)
4. Main chart — Lagna, MC, nine grahas with full detail
5. North Indian style kundli (ASCII diamond chart)
6. All 16 Vargas in one grid, with the methodology table above it
7. **ASTROLOGY FEATURES** *(new in V1.1)*
8. **YOGA ANALYSIS** *(new in V1.1)*
9. Fal report — yogas, graha fal, Vimshottari dasha (V1 output, unchanged)

### 9.2 ASTROLOGY FEATURES

CALCULATED ASTROLOGY FEATURE only — no interpretation, no generated prose.
Opens with a **provenance block** stating every convention in force (house
system, aspect profile, node convention, conjunction orb, Varga conventions,
combustion profile, ayanamsha, and whether positions were entered or
calculated), followed by any caveats that apply to this chart.

Then, for each graha: sign, house, houses owned, dignity, dispositor,
combustion (with the separation and the arc applied), motion, natural and
functional nature, aspects given and received, conjunctions, D9 and D10
placements, vargottama, nakshatra and pada, and per-varga dignity for
D9/D10/D30/D60.

Plus: the house-lord table with occupants and aspecting grahas, functional
roles with the reason for each, dispositor chains, any Parivartana, all
conjunctions with same-rashi and orb shown separately, and graha yuddha.

### 9.3 YOGA ANALYSIS

For every combination that formed:

```
  ++ Bhadra Yoga (Pancha Mahapurusha)
       status     : PRESENT_AND_STRONG
       category   : mahapurusha
       source     : BPHS ch.75; Phaladeepika ch.6.1  [Parashari]
       rule id    : mahapurusha_bhadra
       condition  : Budha stands in its own rashi or in exaltation while
                    occupying a kendra from the Lagna.
       matched    :
           ✓ Budha in Kanya is own sign, exalted
           ✓ Budha is in the 7th (a required house: 1st, 4th, 7th, 10th)
       cancellations: none apply
       strength   : 1.00 (strong) — engine ranking, not a classical quantity
       modifiers  :
           +0.20 dignity — Budha exalted or in moolatrikona
           +0.12 own rashi — Budha in own rashi
           +0.16 benefic drishti — Chandra aspects Budha, Guru aspects Budha
```

Combinations that did **not** form are summarised by category, since the
catalog evaluates every kendra-trikona and dhana pair and the absent list is
long. `--show-absent-yogas` prints each one with the clause that failed, which
is what makes a negative result auditable.

**No LLM-generated text is produced.** Each entry states the classical
condition and stops.

### 9.4 PDF (`engine/report.py`)

```bash
python3 main.py --consultation chitresh_consultation.json --pdf
```

Produces `kundli_<name>_<date>.pdf`, or pass a filename. Written by a
purpose-built PDF writer — no external library — using a monospaced Courier base
font so the kundli grid and Varga tables keep their alignment. Pages are
auto-paginated with a footer, and the font size shrinks automatically if a table
would otherwise run off the page. Portrait A4 by default; `--landscape` and
`--page-size letter` are available.

> **Open item for client:** the PDF is currently a faithful text rendering of the
> report. If a typeset presentation is wanted — vector-drawn kundli diamonds,
> colour, letterhead, client branding — that is a separate piece of work.

---

## 10. Command reference

```
python3 main.py [options]

  --name NAME              Name of person
  --dob YYYY-MM-DD         Date of birth
  --time HH:MM             Exact time of birth, 24-hour
  --place PLACE            Place of birth

  --lat VALUE              Birth latitude, e.g. 26.9124 or "26 54 45 N"   [new]
  --lon VALUE              Birth longitude, e.g. 75.7873 or "75 47 14 E"  [new]
  --timezone IANA          IANA zone, e.g. Asia/Kolkata                   [new]
  --utc-offset OFFSET      Fixed offset at birth, e.g. +05:30             [new]
  --list-cities            List the built-in birth places and exit        [new]

  --consultation FILE      JSON consultation form including entered degrees
  --enter-degrees          Prompt for Lagna + 9 graha degrees
  --varga-config FILE      JSON file selecting the convention for each Varga
  --ayanamsha NAME         lahiri | raman | krishnamurti | fagan_bradley
  --node {true,mean}       Rahu/Ketu from the true or mean lunar node
  --tolerance DEGREES      Difference tolerated in the comparison (default 1.0)

  --rule-profile NAME      parashari | parashari_extended | parashari_strict
  --node-aspects NAME      none | parashari_like | kendra                 [new]
  --show-absent-yogas      List every combination that did not form       [new]
  --no-features            Skip ASTROLOGY FEATURES and YOGA ANALYSIS      [new]

  --legacy-fal             Also print the superseded V1 interpretation  [1.2]
  --no-dasha               Skip the Vimshottari dasha section            [1.2]
  --dasha-depth {1..5}     1 maha, 2 +antar, 3 +pratyantar (default 3)   [1.2]
  --dasha-year NAME        julian | gregorian | sidereal | savana        [1.2]
  --all-antardashas        Antardashas for every mahadasha               [1.2]
  --json-output FILE       Write the canonical ChartSnapshot JSON        [1.2]
  --json-compact           Write the snapshot without indentation        [1.2]

  --house-system NAME      whole_sign | sripati | porphyry |             [1.4]
                           equal_from_lagna | placidus
  --no-strength            Skip the PLANETARY STRENGTH section           [1.4]
  --shadbala-detail        Show every Shadbala subcomponent              [1.4]
  --no-ashtakavarga        Skip the ASHTAKAVARGA section                 [1.4]
  --ashtakavarga-reductions  Apply Trikona/Ekadhipatya (UNVERIFIED)      [1.4]
  --birth-time-sensitivity   Report what changes near the birth time     [1.4]

  --synthesis DATE         Run deterministic synthesis for a date        [1.5]
  --synthesis-profile P    strict | standard | experimental              [1.5]
  --domain NAME            Restrict synthesis to a domain (repeatable)   [1.5]
  --synthesis-evidence     Show every contributing factor                [1.5]
  --birth-time-precision S How precisely the birth time is known, in     [1.5]
                           seconds (default 60, matching an HH:MM entry)
  --prediction-json FILE   Write the PredictionSnapshot                  [1.5]

  --interpret DATE         Render a deterministic interpretation         [1.6]
  --interpret-profile P    Synthesis profile for the interpretation      [1.6]
  --report-mode M          summary | detailed | technical                [1.6]
  --language LANG          Interpretation language (default en)          [1.6]
  --interpretation-json F  Write the InterpretationDocument              [1.6]

  --pdf [FILE]             Save the report as a PDF
  --page-size {a4,letter}  PDF page size
  --landscape              Landscape PDF pages instead of portrait
  --list-conventions       List all Varga conventions and exit
  --selftest               Check the ephemeris against reference values and exit
  -h, --help               Show help
```

---

## 11. File structure

```
main.py                      CLI, chart printing, PDF orchestration
AUDIT.md                     Phase 2 calculation audit — measured accuracy
RULE_AUDIT_V15.md            V1.5 rule change log (generated)            [1.5]
DOMAIN_VALIDATION.md         V1.6 domain source coverage (generated)      [1.6]
templates/en/                Interpretation templates, one per domain     [1.6]
varga_config.json            Varga methodology selection
sample_consultation.json     Example input with entered degrees
chitresh_consultation.json   Live example input

engine/
  ephemeris.py               Astronomy: time scales, Sun, Moon, planets, nodes,
                             precession, nutation, ayanamsha, Ascendant, MC
  planets.py                 Chart assembly: rashi, nakshatra, pada, dignity,
                             combustion profile, speed, retrogression
  location.py                Birth place resolution — no fallback city
  vargas.py                  16 divisional charts with configurable conventions
  compare.py                 Entered vs calculated difference report
  input_model.py             Consultation form, degree parsing, validation
  fal.py                     V1 yogas, graha fal, Vimshottari dasha
  report.py                  Dependency-free PDF writer

  ephemeris.py               ... now dispatches Earth/Jupiter/Saturn to VSOP87
  vsop87_data.py             VSOP87A series — GENERATED, do not edit     [1.2]
  uncertainty.py             Boundary safety and error envelopes         [1.2]
  snapshot.py                Canonical versioned ChartSnapshot           [1.2]
  varga_metadata.py          Varga provenance and validation status      [1.2]

  strength/                  SHADBALA — six components                   [1.4]
    models.py                BalaComponent, ShadbalaResult, requirements
    sthana_bala.py           Uchcha, Saptavargaja, Ojhayugma, Kendradi,
                             Drekkana
    dig_bala.py              Directional strength
    kala_bala.py             Six temporal subcomponents
    chesta_bala.py           Motional, from measured ephemeris speed
    naisargika_bala.py       Natural strength, constant per graha
    drik_bala.py             Aspectual, consuming the feature layer
    shadbala.py              Assembly and the planetary-war adjustment
    report.py                PLANETARY STRENGTH section

  ashtakavarga/              BINDU COUNTING                              [1.4]
    models.py                The eight tables and the classical invariants
    bhinna.py                Individual charts
    sarva.py                 The combined chart
    reductions.py            Trikona/Ekadhipatya — UNVERIFIED, off by default
    report.py                ASHTAKAVARGA section

  houses/                    BHAVA REPRESENTATIONS                       [1.4]
    models.py                BhavaCusp, PlanetPlacement, BhavaChart
    systems.py               sripati, porphyry, equal, placidus
    profiles.py              Named profiles; ReferenceSpace
    report.py                RASHI VS BHAVA section

  sensitivity/               BIRTH-TIME SENSITIVITY                      [1.4]
    birth_time.py            Window scan, bisected to the second
    models.py                SensitivityReport
    report.py                BIRTH-TIME SENSITIVITY section

  transits/                  TRANSIT ENGINE                              [1.4]
    models.py                TransitPosition, relationships, events
    calculator.py            Positions, reusing the natal ephemeris
    relationships.py         Transit-to-natal facts
    query.py                 Ranges and event detection
    timing_context.py        Natal + dasha + transit for one moment
    report.py                TRANSITS section

  timing/                    TIMING ENGINE                               [1.2]
    models.py                Canonical cycle, year-length conventions
    vimshottari.py           Exact hierarchy, generic subdivision, queries
    report.py                VIMSHOTTARI DASHA output section

  interpretation/            DETERMINISTIC INTERPRETATION               [1.6]
    models.py                InterpretationDocument, DomainSection, modes
    keys.py                  The semantic key vocabulary
    renderer.py              Template loading and strict resolution
    grammar.py               Lists, dates, ordinals, planet names
    evidence_formatter.py    One evidence record to one sentence
    domain_renderer.py       Domain sections, contradictions, silence
    timing_renderer.py       Windows and event candidates
    warnings_renderer.py     Confidence and birth-time language
    report.py                Document assembly and text output

  synthesis/                 DETERMINISTIC SYNTHESIS                    [1.5]
    models.py                Eligibility, direction, confidence, activation
    domains.py               17 life domains, declarative mappings
    domain_evidence.py       Factor-to-domain provenance (5 factor types) [1.6]
    eligibility.py           Which rules may influence a prediction
    reliability.py           Birth-time precision gating
    natal_promise.py         Structured natal evidence, and the strict gate
    activation.py            Dasha and transit activation facts
    scoring.py               Activation and confidence bands (heuristic)
    engine.py                The Natal -> Dasha -> Transit hierarchy
    events.py                Event candidates and timing windows
    evidence.py              Lineage and the evidence appendix
    snapshot.py              PredictionSnapshot, schema 1.0.0
    report.py                The seven Part 26 output sections

  features/                  CALCULATED ASTROLOGICAL FEATURES           [1.1]
    models.py                PlanetFeatures, HouseFeatures, ChartFeatures
    builder.py               One-pass assembly from a JyotishChart
    lordships.py             House lords, houses owned, house categories
    aspects.py               Parashari drishti, configurable node conventions
    conjunctions.py          Same-rashi vs orb; graha yuddha
    dispositors.py           Chains, final dispositor, Parivartana
    dignity.py               Exaltation, debilitation, own, moolatrikona
    functional_nature.py     Lagna-dependent roles, Yogakaraka
    varga_features.py        Divisional placements, vargottama, varga dignity
    relationships.py         Natural, temporary, compound friendship
    report.py                ASTROLOGY FEATURES output section

  rules/                     TRADITION-SPECIFIC RULES                   [1.1]
    engine.py                YogaRule, YogaResult, five-state evaluation
    conditions.py            Declarative clause vocabulary
    catalog.py               Core sourced classical combinations
    catalog_extended.py      V1.2 additions (110 rules total)           [1.2]
    modifiers.py             Strength modifiers, each with its reason
    report.py                YOGA ANALYSIS output section

tools/                       DEVELOPMENT ONLY — never imported by the app
  generate_reference.py      Golden fixtures from Swiss Ephemeris
  measure_accuracy.py        Accuracy measurement across 1800-2050      [1.1]
  build_vsop87.py            Parse, validate and emit VSOP87 data       [1.2]
  vsop_benchmark.py          Earth-needed? and truncation benchmark     [1.2]
  generate_accuracy_fixture.py  Configuration-specific accuracy cases   [1.2]
  generate_regression_charts.py Astronomical values for 8 charts        [1.2]

tests/
  test_reference_positions.py  Golden positions, boundaries
  test_vargas_golden.py        All 16 Vargas vs independent reference    [new]
  test_location.py             Birth place resolution                    [new]
  test_features.py             Feature engine                            [new]
  test_yoga_engine.py          Rule engine and catalog                   [new]
  test_regression_jaipur_1988.py  Documented worked example             [1.1]
  test_cli_backcompat.py       V1 compatibility + legacy isolation       [1.1]
  test_accuracy_fixtures.py    VSOP87 provenance, accuracy, boundaries   [1.2]
  test_timing.py               Dasha hierarchy, queries, boundaries      [1.2]
  test_snapshot.py             Schema, score terms, varga metadata       [1.2]
  test_yoga_catalog_v12.py     The V1.2 yoga additions                   [1.2]
  test_regression_charts.py    Eight unrelated charts                    [1.2]
  fixtures/
    reference_positions.json
    accuracy_profile.json                                                [1.1]
    planetary_accuracy.json                                              [1.2]
    regression_charts.json                                               [1.2]
```

The application depends on the standard library only. `tools/` uses
`pyswisseph` to generate fixtures, and a test asserts that no application
module imports it — which is what keeps the golden tests independent rather
than self-confirming.

---

## 12. Worked example

**Input:** Chitresh Goyal, 30 August 1988, 20:18, Jaipur.
No degrees entered, so all positions calculated. Local time converted to
1988-08-30 14:48 UTC, ΔT 56.1 s applied, Lahiri ayanamsha **23.698729°**.

> **Correction to V1.** The previous documentation gave the ayanamsha here as
> 23.6946°. That was wrong by 15 arcseconds. The Swiss Ephemeris value is
> 23.69872943 and this engine gives 23.69872944.

This example is a **regression test** (`tests/test_regression_jaipur_1988.py`,
35 assertions), so every value below is pinned. Since V1.2 it is no longer the
only one: seven further unrelated charts, spanning 1901–2033 and both
hemispheres, are pinned in `tests/test_regression_charts.py`, so no formula can
be tuned to suit this chart without breaking the others.

> **Corrected in V1.2.** Guru and Shani moved when VSOP87A replaced the
> Keplerian elements. The V1.1 figures (Vrishabha 11°31′42″, Dhanu 02°11′17″)
> were wrong by 6.6′ and 2.6′. The values below match the Swiss Ephemeris to
> 0.3″ and 1.1″.

**Lagna:** Meena 15°47′01″, Uttara Bhadrapada pada 4, lord Guru. MC Dhanu 12.55°.

| Graha | Rashi | Degree | Nakshatra | House | Speed | Dignity |
|---|---|---|---|---|---|---|
| Surya | Simha | 13°44′35″ | P. Phalguni P1 | 6 | +0.967 | Moolatrikona |
| Chandra | Meena | 28°07′26″ | Revati P4 | 1 | +14.577 | — |
| Mangal | Meena | 17°40′52″ | Revati P1 | 1 | −0.057 | retrograde |
| Budha | Kanya | 05°58′01″ | U. Phalguni P3 | 7 | +1.452 | Uchcha |
| Guru | Vrishabha | 11°25′03″ | Rohini P1 | 3 | +0.079 | — |
| Shukra | Mithuna | 28°09′37″ | Punarvasu P3 | 4 | +1.014 | — |
| Shani | Dhanu | 02°13′51″ | Mula P1 | 10 | ~0.000 | stationary |
| Rahu | Kumbha | 20°27′20″ | P. Bhadrapada P1 | 12 | +0.012 | — |
| Ketu | Simha | 20°27′20″ | P. Phalguni P3 | 6 | +0.012 | — |

Independent confirmations: Mars was retrograde in Pisces (opposition 28
September 1988); Saturn was within days of its station (turned direct 11
September 1988), so the engine correctly declines to call its direction;
Jupiter was in Taurus; Mercury near greatest eastern elongation.

**Vargottama:** Surya, Chandra, Shukra. **No graha is combust** — Ketu is
6.65° from the Sun but is a shadow graha and never burns.

### 12.1 The V1 Yoga claims, re-evaluated

V1 reported: *"Bhadra Mahapurusha, Raja Yoga, Chandra-Mangal Yoga, Kemadruma
Yoga."* Through the rebuilt engine, 90 rules produce **9 combinations formed,
1 of them cancelled**:

| V1 claim | V1.1 verdict |
|---|---|
| Bhadra Mahapurusha | **Confirmed — PRESENT_AND_STRONG.** Budha is exalted *and* in its own rashi (Kanya is both) in the 7th, a kendra. Not combust. |
| "Raja Yoga" | **Re-derived on the correct basis.** V1 fired because a dignified graha sat in a kendra, which is not a Raja Yoga. Four genuine ones exist: Budha, owning the 4th and 7th (both kendras), is in mutual 7th aspect with Chandra (5th lord) and with Mangal (9th lord) — real kendra-lord/trikona-lord relationships, each reported by name. |
| Chandra-Mangal Yoga | **Confirmed.** Both share Meena in the 1st, 10.44° apart. |
| Kemadruma Yoga | **PRESENT_BUT_CANCELLED — the reading is inverted.** The Moon is isolated, so it forms; but **four** bhanga clauses cancel it: grahas occupy a kendra from the Lagna; grahas occupy a kendra from Chandra; Chandra itself holds the 1st, a kendra; and Chandra receives Budha's drishti. V1 reported bare presence, which reads as an affliction that is not operative here. |
| — | Two Dhana Yogas also form (2nd lord with 5th lord, and 5th lord with 9th lord, both by conjunction), which V1's "exalted graha in the 2nd or 11th" rule could not detect. |

**Gajakesari is absent** — Guru is the 3rd from Chandra, not a kendra.
**Budha-Aditya is absent** — Surya is in Simha, Budha in Kanya.
**No Neecha Bhanga applies** — nothing in this chart is debilitated.

---

## 12A. What is verified, and how strongly *(V1.2, extended in V1.3)*

"The tests pass" and "the astrology is right" are different claims. This table
keeps them apart.

| Claim | Established for |
|---|---|
| **Computationally tested** | Everything. 460 tests covering structure, invariants, boundaries, serialisation, error paths and robustness across many synthetic charts. |
| **Externally benchmarked** | All planetary positions, the ayanamsha, the Ascendant, ΔT, retrogression and station detection — against the Swiss Ephemeris, an independent theory. The VSOP87 parse additionally against the theory authors' own published check values, which is stronger. |
| **Tradition / source validated** | **Nothing.** |

That last row is the one that matters most and is easiest to lose sight of.
The Varga suite compares 138,240 longitudes and 6,456 boundaries between two
independent implementations — but both implement *the same stated rule*. It
confirms the code is right; it says nothing about whether the rule was read
correctly from the source.

`engine/varga_metadata.py` records this on every convention:

```json
{
  "chart": "D9",
  "convention_id": "standard",
  "tradition": "Parashari",
  "source": "Brihat Parashara Hora Shastra, Vargas Adhyaya",
  "validation": "implementation_consistency",
  "validation_meaning": "Two independent implementations of the stated rule
     agree ... This confirms the code, not the reading of the source.",
  "algorithm_version": "1.0.0"
}
```

A test asserts that **nothing** claims `tradition_source_validated` until that
work is actually done. The same caveat applies to the yoga catalog: each rule
cites a source, but no independent scholar has confirmed the engine's reading.

Explicit metadata is carried for every convention of D2, D3, D7, D10, D16,
D20, D24, D30, D40, D45 and D60, as well as the rest.

---

## 12B. Source and provenance layer *(new in V1.3)*

`engine/sources/` records, for every shipped rule, what textual evidence
actually stands behind it.

### Why a bare citation is not provenance

Until V1.3 every rule carried a string like `BPHS ch.36`. **Those strings were
written from memory by the implementing model and never checked.** Worse, a
bare work name cannot identify a passage even in principle: BPHS is a textual
tradition whose chapter division, verse numbering, Sanskrit readings and
translations all differ between editions.

### Witness model

A `SourceWitness` names its work, author, **edition**, editor or translator,
publication year, volume, chapter, verse range, page, retrieval URL and
checksum. **A Sanskrit text and a translation of it are two witnesses, never
one** — a translator's choice among readings is an interpretation.

Authority levels, strongest first: `PRIMARY_SANSKRIT_WITNESS`,
`PRINTED_SANSKRIT_EDITION`, `CLASSICAL_COMMENTARY`, `TRANSLATION`,
`MODERN_COMMENTARY`, `SECONDARY_REFERENCE`, `WEB_SUMMARY`.

**A `WEB_SUMMARY` can never make a rule tradition-validated.** Modern sites
help locate a passage; they are downstream of the text and repeat each other's
errors.

### Validation lifecycle

```
UNVERIFIED → TEXT_LOCATED → WITNESS_RECORDED → TRANSLATION_CHECKED
→ RULE_INTERPRETATION_MAPPED → IMPLEMENTATION_MATCHED
→ SECOND_WITNESS_CHECKED → TRADITION_VALIDATED        (CONFLICTING_SOURCES)
```

**Every status has a stated evidence requirement enforced in code**, and a test
asserts that nothing overclaims. A status is a checked claim, not a label.

### What this build actually has

| | |
|---|---|
| Witnesses obtained | **1 work** — Bṛhajjātaka (GRETIL, Oriental Books Reprint Corp. 2nd ed. 1979), 5 passages |
| Rules with a located source | **5 of 110** |
| Varga conventions with one | **2 of 32** (D9, D30) |
| **Tradition validated** | **0** |
| Registered conflicts | 3 |
| Queued for human review | 11 |

BPHS, Phaladīpikā, Sārāvalī and Jātaka Pārijāta could not be obtained. The
absence is recorded as data in `UNAVAILABLE_WORKS`, not left as a gap.

### `parashari_strict` is now evidence-gated

The word "strict" means something enforceable: a Sanskrit-tier witness with an
edition and locator, a written textual condition, a written software condition,
a named test, and no conflict saying the implementation diverges.

Membership is **computed from the registry**, so a rule cannot be admitted by
editing the catalog — only by producing evidence. It currently contains **1
rule**. That is the finding, not a defect. The V1.2 meaning survives as
`parashari_vipareeta_strict`.

### Human review queue

Eleven questions that cannot safely be settled by a model — Sanskrit
ambiguities, unresolved numeric encodings, missing witnesses. They are queued
rather than answered, because a model that resolves an ambiguity by choosing
the reading which makes its own code correct has validated nothing.

Full report: **`SOURCE_VALIDATION.md`**, regenerated with
`python3 tools/generate_source_report.py`.

---

## 12C. What V1.4 added *(calculation release)*

| Module | Package | Source | Status |
|---|---|---|---|
| **Shadbala** | `engine/strength/` | BPHS ch.27 (Santhanam) | 3 of 6 components IMPLEMENTATION_MATCHED |
| **Ashtakavarga** | `engine/ashtakavarga/` | BPHS ch.66 (Santhanam) | RULE_INTERPRETATION_MAPPED |
| **Bhava Chalit** | `engine/houses/` | none located | UNVERIFIED |
| **Birth-time sensitivity** | `engine/sensitivity/` | n/a — a software tool | n/a |
| **Transits** | `engine/transits/` | n/a — astronomy | externally benchmarked |

### Shadbala

Six components, each in its own module with its own provenance:

| Component | Source | Notes |
|---|---|---|
| Sthana Bala | BPHS 27.1-6 | Five subcomponents; the witness's worked example is reproduced exactly |
| Dig Bala | BPHS 27.7 | Two worked examples reproduced |
| Kala Bala | BPHS 27.8-20 | Six subcomponents; two rest on conventions the text does not fix |
| Chesta Bala | BPHS 27.18 | Reads measured speed and stationary state from the ephemeris |
| Naisargika Bala | BPHS 27.14 | Formula stated outright in the witness |
| Drik Bala | BPHS 27.19 | Consumes the feature layer's aspects; does not recompute them |

Values are kept in **virupas** and **rupas** (1 rupa = 60 virupas), and every
intermediate is retained. A total inherits the **weakest** validation status
among its components, so a Shadbala figure never looks better attested than
the shakiest thing it rests on.

Two approximations are declared rather than hidden: **Varsha and Masa Bala**
need an Ahargana epoch the witness supplies through a printed table rather
than through the text, and **Tribhaga Bala** assumes 06:00/18:00 sunrise and
sunset because the engine does not yet compute them.

### Ashtakavarga

Bhinnashtakavarga for the seven grahas and Sarvashtakavarga, with bindus by
sign and by house. Totals are an arithmetic invariant — 48, 49, 39, 54, 56,
52, 39, summing to 337 — and a test asserts all eight, which catches a
mistyped table without needing a reference.

The **Sun's table was read from BPHS 66.43-45** and matches exactly. The other
six are in the same chapter but their OCR is damaged, so they are implemented
from the standard tables and **not claimed as verified**.

**No interpretation is attached.** A bindu count is a count; the report says
so explicitly.

Trikona and Ekadhipatya **reductions are implemented but off by default** and
marked UNVERIFIED — the relevant verses are among the damaged ones and
traditions differ on the edge cases.

### Bhava Chalit — a separate representation

```bash
python3 main.py --consultation chart.json --house-system sripati
```

Systems: `whole_sign` (default), `sripati`, `porphyry`, `equal_from_lagna`,
`placidus`. Placidus **raises above the polar circles** rather than returning
a number.

The Lagna degree is the bhava **madhya**; sandhis fall midway between adjacent
madhyas.

**The Rashi and Bhava charts never merge.** A graha carries `rashi_house` and
`bhava_house` as separate fields, and `moved` says whether they differ. Sign,
sign lord, dignity, houses owned and every varga are properties of the ZODIAC
and are untouched by the house system — a test recomputes the entire feature
set after building bhava charts in three systems and requires it unchanged.

**Yoga rules always run in RASHI space.** `reference_space` (RASHI / BHAVA /
BOTH / CONFIGURABLE) exists for when a rule is sourced as meaning bhavas; none
is yet, so none has moved.

### Birth-time sensitivity

```bash
python3 main.py --consultation chart.json --birth-time-sensitivity
```

Reports which classifications change within ±1, 2, 5 and 10 minutes of the
stated time, bisected to the second. Watches the Lagna sign, nakshatra and
pada, the D1/D9/D10/D30/D60 Lagnas, and every graha's house or bhava.

**This is not rectification.** No time is suggested, preferred or scored.

> **On the documented example:** its D60 Lagna changes **39 seconds** after
> the stated birth time, and the Lagna nakshatra, Lagna pada and D9 Lagna all
> change at **+2m 34s**. Any reading leaning on its D9 Lagna rests on the
> clock as much as on the sky.

### Transits

```python
snapshot = get_transit_snapshot(moment, natal_chart=chart)
events   = get_transit_events_between(start, end)
context  = build_timing_context(moment, natal_snapshot, dasha, chart)
```

Positions reuse the natal ephemeris — not a second implementation — so they
inherit the same VSOP87 accuracy and the same uncertainty envelopes.

Relationships keep **same-rashi** and **angular separation** as separate
facts, for the same reason the natal conjunction engine does. Drishti uses the
shared aspect profile.

Events are astronomical state changes only: sign and nakshatra ingress,
stations, exact conjunctions. **None is labelled good or bad**, and no
Gochara rule is implemented — those need sources first.

`TimingContext` assembles the natal chart, the dasha stack and the transit
snapshot for one moment. **No synthesis and no score.**

---

## 12D. What V1.5 added *(audit and synthesis release)*

V1.5 has two halves that pull in opposite directions, deliberately. The first
audits the rule corpus and **removes** claims. The second builds the first
synthesis layer, which **makes** them. The order matters: the audit ran first
so that the synthesis layer had something honest to gate against.

### 12D.1 The audit

Sanskrit witnesses were obtained for Bṛhat Parāśara Horā Śāstra, Phaladīpikā
and Jātaka Pārijāta, and all 110 shipped rules were checked against them.

**The doctrine was mostly real; the citations were mostly wrong.** Of the
legacy chapter numbers checked, exactly one — `BPHS ch.75` for the Pañca
Mahāpuruṣa yogas — named the right chapter. The Raja Yogas are at 34.11-15
and 41.28, not ch.36. The Moon yogas are at 37.7, not ch.34. The Vipareeta
triad is not in BPHS at all; Harṣa, Sarala and Vimala are three of twelve
bhāva-lord yogas at Phaladīpikā 6.57.

Forty-three rules were found to diverge from the text located for them.
**None was edited.** Each keeps its V1.4 behaviour and gains a corrected
counterpart in a new profile:

```
  --rule-profile parashari           # the V1.1 reading, unchanged
  --rule-profile parashari_textual   # the located reading
```

The full change log is `RULE_AUDIT_V15.md`, generated from the registry by
`tools/generate_rule_audit.py` so it cannot drift from what the code records.

The evidence-gated `parashari_strict` profile grew from **1 rule to 41**
without any change to the gate. That growth is entirely the arrival of
evidence.

### 12D.2 The synthesis layer

`engine/synthesis/` combines facts for the first time. It produces structured
evidence and **no prose**: there is no field anywhere in it for a verdict, a
recommendation, or a sentence about a person.

```
  --synthesis 2026-09-27
  --synthesis-profile strict|standard|experimental
  --domain career
  --prediction-json FILE
```

Three guarantees hold it together:

1. **A transit cannot create a natal promise.** The hierarchy is
   Natal → Dasha → Transit, and a lower layer can never supply what a higher
   one lacks. A transit over an empty 10th house produces a recorded fact and
   no career evidence.
2. **An unverified rule cannot influence strict synthesis.** Eligibility is
   computed from the source registry, so a rule is promoted by producing
   evidence and by nothing else. A rule known to diverge from its witness is
   `DISABLED` in *every* profile, including experimental.
3. **No probability is emitted.** Activation and confidence are ordinal
   bands, and a test walks every serialised field name to enforce it.

Activation and confidence are independent axes. `STRONGLY_ACTIVE` with `LOW`
confidence is valid and common: it means the rules fire loudly on inputs that
are not firm.

### 12D.3 What strict synthesis will say

Very little, and that is the finding.

A sourced Shadbala number attached to an unsourced house→domain mapping does
not make a conclusion sourced. So the strict gate asks whether the link *from
the factor to the domain* has a witness — and in V1.5 that means kāraka
attributions with a locator, and nothing else. BPHS 32.20 says `śukrāt patiḥ`,
"from Venus the spouse", and that sentence is the link from Venus to
marriage. No text has been located that says the 10th house signifies career.

Strict synthesis therefore speaks about **4 domains out of 17** and is silent
on the rest. Standard and experimental use the house mappings, say so in
every result, and carry the warning.

### 12D.4 Birth-time gating

V1.4 measured that the regression chart's D60 Lagna changes 39 seconds after
the stated birth time. The stated time came from a field reading `HH:MM`.

V1.5 acts on that: an entered `HH:MM` resolves to 60 seconds, the instability
falls inside it, so the D60 Lagna of that chart is **not determined by the
input**. D60 evidence is marked LOW and dropped from strict. Pass
`--birth-time-precision 1` if the time really is known to the second and the
same chart's D60 becomes firm.

This is not rectification. No time is proposed, preferred or scored.

---

## 12E. What V1.6 added *(domain validation and interpretation)*

Two halves, pulling opposite ways again. The first **sources** the domain
layer, which had none. The second builds the layer that turns structure into
sentences — and the order matters, because prose about an unsourced mapping
is the most convincing wrong output this engine could produce.

### 12E.1 The domain audit

V1.5 shipped 17 domains with **no** house mapping carrying a witness. V1.6
read BPHS ch.11 (`bhāvaviveka`), the house-signification chapter, plus
ch.21, 23 and 24. Most mappings turn out to be attested in a single word —
`vṛtti` for the 10th, `jāyā` for the 7th, `putra` for the 5th.

| | V1.5 | V1.6 |
|---|---|---|
| House mappings sourced | 0 of 17 | 38 of 43 |
| Kārakas sourced | 5 of 30 | 7 of 24 |
| Domains strict synthesis admits | 4 | **16 of 17** |
| Varga mappings sourced | 0 | **0** |

Full coverage per domain is in `DOMAIN_VALIDATION.md`, generated by
`tools/generate_domain_report.py`.

**Two mappings were wrong, not merely uncited.** EDUCATION moved from the
4th house to the 5th, where BPHS 11.6 puts `vidyā`. TRAVEL lost the 12th and
gained the 7th. RELATIONSHIPS turned out to have no basis distinct from
marriage and is the one domain strict still declines.

**Five factor types are kept independent** — HOUSE, HOUSE_LORD, KARAKA,
FUNCTIONAL_LORDSHIP, VARGA — because they are different claims with
different evidence. CAREER has a sourced house, a sourced house lord and an
unsourced D10, and the report shows which is which.

### 12E.2 The strict gate, unchanged

The V1.5 rule still holds: a factor may carry a strict prediction only if the
link **from that factor to that domain** has a witness, not merely if the
factor is well computed. `qualifies_for_strict` is untouched. What changed is
that BPHS 11.11 and 21.2 now answer the question for career, so the Shadbala
factor is admitted on evidence.

It still refuses inside sourced domains: CAREER's 10th house passes and its
6th does not, because BPHS 11.7 gives the 6th enemies and wounds.

Transits remain excluded from strict for a narrower reason than before — the
house mapping is sourced now, but "a graha transiting the 10th affects
livelihood" is Gochara, and the engine has no witness for that.

### 12E.3 The interpretation layer

```
  --interpret 2026-09-27
  --interpret-profile strict|standard|experimental
  --report-mode summary|detailed|technical
  --language en
  --interpretation-json FILE
```

`engine/interpretation/` consumes a serialised `PredictionSnapshot` and
produces an `InterpretationDocument`. **No model, no network, no
randomness** — template substitution over a key and already-computed values.

The renderer is prevented from deciding anything by construction: its only
input is a dict, so it is never shown a chart it could judge. A test
round-trips the snapshot through JSON before rendering to prove it.

**Three modes, one source.** SUMMARY, DETAILED and TECHNICAL differ in how
much they show and never in what they claim; a test asserts every domain's
activation and confidence are identical across all three.

**Templates live outside Python** in `templates/en/`, one shared
`common.json` plus a file per domain. Conjunctions and month names come from
the locale's grammar block, so a new language needs no code change — a test
builds one and renders from it.

**Determinism is tested by hash.** Identical input gives byte-identical
output, excluding only the wall-clock `generated` field.

### 12E.4 What the prose will not say

No probability, no medical or mortality language, no false specificity — a
CAREER_CHANGE candidate stays a candidate and does not become a promotion.
Contradictions render both sides. A domain the profile cannot speak about
says so, in one of three distinct sentences depending on why.

---

## 12F. What V1.7 added *(productization release)*

V1.7 adds an application, not astrology. No formula changed; one cache was
added to the transit scanner, and one gate was tightened because a source was
found. Everything else is a new layer above the engine.

### The application layer

```
app/
    services/        the ONLY place that may import engine.*
        chart_service.py        calculate_chart(consultation, settings)
        prediction_service.py   calculate_prediction, render_interpretation
        report_service.py       generate_report, generate_pdf, generate_html
        settings_service.py     available_options, describe_methodology
        visual_builder.py       snapshot -> ChartVisualModel
    visual/          geometry and SVG. Imports no engine.
    report/          ReportDocument, PDF writer, HTML writer. No engine.
    ui/              local server and screens. No engine.
    models.py        ConsultationRecord, ApplicationSettings, NatalResult,
                     PredictionResult, ReportPreferences, BirthTimePrecision
    storage.py       save / load / migrate
    errors.py        one error family, user message and debug detail apart
    benchmark.py     per-stage timing
```

`tests/test_app_boundary.py` parses the import graph and fails if a
presentation layer reaches the engine. See AUDIT.md §40A.

### Running it

```bash
python main.py --app                       # local UI at 127.0.0.1:8713
python main.py --app --port 9000 --debug   # another port, with detail

python main.py --name X --dob 1988-08-30 --time 20:18 --place Jaipur \
    --report kundli.pdf --report-mode detailed
python main.py ... --report-html kundli.html --language hi
python main.py ... --report-json report.json
python main.py ... --save-consultation chart.json
python main.py --open-consultation chart.json --report out.pdf
python main.py ... --benchmark
python main.py ... --precision APPROX_15_MIN
```

The console report is unchanged and remains the default. Every V1.6 flag still
works; `tests/test_cli_backcompat.py` is the check.

### Screens

Overview, Birth Chart, Vargas, Planetary Strength, Yogas, Dasha, Transits,
Life Areas, Timeline, Reliability, Sources and Methodology. Each answers one
question and states the methodology that answered it.

### Birth-time precision

`EXACT_TO_SECOND` (1s), `EXACT_TO_MINUTE` (60s), `APPROX_5_MIN` (300s),
`APPROX_15_MIN` (900s), `UNKNOWN` (3600s).

The value reaches the V1.5 reliability gate, and it only ever WIDENS
uncertainty. There is no setting that makes the engine treat a time as better
than entered. `UNKNOWN` is the widest band, not the absence of one.

### Charts

`ChartVisualModel` -> `Scene` -> SVG or PDF. One description of the picture,
two backends, so the kundli in the report is the kundli on the screen.

North Indian style. Markers are ASCII and printed, never colour alone:
`R` retrograde, `c` combust, `^` exalted, `v` debilitated, `mt` moolatrikona,
`sv` own sign. Every chart carries a text equivalent in `Scene.description`
and in the SVG's `<desc>`.

Detail levels `COMPACT`, `STANDARD`, `DETAILED` change labels and never
placements.

### Reports

`ReportDocument` -> blocks -> PDF or HTML. Three modes:

| Mode | Sections | Typical length |
|---|---|---|
| summary | cover, birth, summary, charts, life areas, reliability | ~9 pages |
| detailed | + planets, strengths, yogas, dasha, transits, timing, methodology | ~32 pages |
| technical | + source appendix | ~33 pages |

Modes SELECT sections. They never rephrase: every sentence comes from one
InterpretationDocument rendered once at the requested mode.

The PDF is written without a third-party library — object table, content
streams, cross-reference table — using the base-14 faces with committed
metrics (`app/report/metrics.py`, generated by
`tools/generate_font_metrics.py`).

**A Hindi PDF is refused**, because those faces are Latin and Devanagari also
needs shaping. `--report-html` is the complete alternative. See AUDIT.md §43A.

### Hindi

`templates/hi/` — common.json plus seventeen domain files, all 78 keys.

What moved into the locale to make it possible: ordinals, the house-name
pattern, the sentence terminator, capitalisation, month names, planet and sign
names, domain titles, and the shared vocabulary that arrives as template
ARGUMENTS (`TemplateSet.term`). See AUDIT.md §42A.

### Saved consultations

Input, precision and methodology — never the answer. A cached snapshot may sit
beside it and is marked as non-authoritative. Files carry `schema_version`
and `application_version`; gaps in an old file are filled from the defaults in
force WHEN IT WAS WRITTEN, and a changed default is reported rather than
silently applied.

### Performance

`--benchmark`, one cold run, Jaipur 1988 at 2026-09-27, technical report:

| Stage | Seconds |
|---|---|
| chart (positions, features, yogas, dasha, strength, ashtakavarga) | 0.02 |
| sensitivity scan (when enabled) | 0.36 |
| synthesis (incl. one-year transit event scan) | 5.08 |
| interpretation | 0.01 |
| visuals (three charts to SVG) | 0.001 |
| report document | 0.003 |
| PDF render (33 pages) | 0.03 |

Synthesis dominates, and the transit event scan dominates synthesis. It was
58 seconds before V1.7 cached the scanner's samples. See AUDIT.md §41A.


## 13. Known limits

| Area | Current state |
|---|---|
| ~~Jupiter, Saturn~~ | **Fixed in V1.2** — VSOP87A brings them to 3.1″ and 4.1″ |
| ~~Mars accuracy~~ | **Fixed in V1.3** — VSOP87A brings it to 8.0″ (0.13′) |
| **Rahu/Ketu accuracy** | **1.11′ — now the limiting body.** Needs a better lunar series, not a planetary one. |
| Mercury, Venus, Sun, Moon, nodes, Lagna | Comfortably accurate; see §3.1 |
| Boundary certainty | Now **reported explicitly** per graha rather than left to the reader — see §3.1c |
| Dasha systems | Vimshottari only. No Ashtottari, Yogini or Chara. |
| Dasha depth | Pratyantardasha by default; sukshma and prana work but are not built |
| **Source validation** | **5 of 110 yoga rules, 2 of 32 Varga conventions and 6 of 8 V1.4 calculation modules have a located witness. Nothing is tradition-validated.** |
| **The ~100 BPHS yoga citations** | **Still unaudited.** V1.4 obtained a named edition to check them against; the chapter-by-chapter audit has not been done. |
| Sanskrit BPHS | Not obtained. Caps everything resting on BPHS below TRADITION_VALIDATED. |
| ~~Bhava Chalit~~ | **Implemented in V1.4** — Sripati, Porphyry, equal, Placidus |
| ~~Transits~~ | **Implemented in V1.4** — positions, relationships, events, TimingContext. No Gochara rules. |
| Shadbala | Two Kala Bala subcomponents rest on assumed conventions |
| Ashtakavarga | Six of seven tables unread against the witness; reductions unverified |
| House systems | None source-validated |
| Sunrise/sunset | Not computed — limits Tribhaga Bala and the hora |
| Saturn near station | Daily motion can fall below the engine's resolution, so direction reads "stationary" rather than resolving. This is stated honestly rather than guessed. |
| Date range | 1800–2050 for planets; ΔT interpolated to 2026 then projected, diverging to ~12 s by 2050 (no practical effect on the Lagna) |
| Uranus, Neptune, Pluto | Not included — outside classical Jyotish |
| Place database | 62 built-in places. **Unknown places now fail loudly** and can be supplied with `--lat/--lon/--timezone`. |
| Time zone | IANA database, resolved for the birth moment, so DST and historical rules are applied where tzdata has them. Not independently verified against historical records. |
| Entered charts | Entered degrees carry direction but not speed; their motion is marked unmeasured rather than presented as observed |
| House system | Whole sign only. No Bhava Chalit, Sripati or Placidus; no bhava madhya. |
| ~~Dasha~~ | **Rebuilt in V1.2**: mahadasha, antardasha and pratyantardasha with exact calendar dates |
| Yoga catalog | 110 rules (122 with variants). Nabhasa, Sankhya and most Arishta families not modelled. |
| Ashtakavarga, Shadbala, Vimshopaka | Not implemented. `vimshopaka_inputs()` returns the per-varga dignities such a calculation needs, but no weighting scheme. |
| Transits (Gochar) | Not implemented |
| Interpretation / narrative | Not implemented — V1.1 returns facts and rule verdicts only |

---

## 14. Questions for the client

1. Are the **default Varga conventions** correct for your tradition — particularly
   D2, D16, D20, D24, D30, D40 and D60?
2. Which **ayanamsha** should be the standard? Lahiri is the current default.
3. **True node or mean node** for Rahu and Ketu?
4. Is **whole-sign houses** correct, or is Bhava Chalit / Sripati expected?
5. Do you need **antardasha and pratyantardasha**, and should periods be shown as
   calendar dates rather than ages?
6. Is the plain-text PDF acceptable, or is a **typeset, branded chart** required?
7. How precise must **birth places** be? This determines whether we need a proper
   geocoding database.
8. Which further modules are in scope — **Ashtakavarga, Shadbala, transits,
   muhurta, matchmaking (Guna Milan)**?
9. **Which Rahu/Ketu drishti convention** should be the default? The engine
   currently asserts none, because traditions differ — see §6.2.
10. **Do you accept the Rahu/Ketu exaltation rashis** as Vrishabha/Vrishchika?
   BPHS assigns the nodes none, and later tables disagree with each other.
11. **Which Yoga rule profile** — `parashari` or `parashari_extended`?
12. For **Jupiter and Saturn**, is 10–13 arcmin acceptable, or should Phase 3
   prioritise a perturbation theory to bring them to arcseconds?
