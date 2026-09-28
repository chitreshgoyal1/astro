# Calculation Engine Audit — V1.1 through V1.4

**Date:** 27 September 2026
**Scope:** the whole engine and test suite.

> **V1.4 update.** Sections marked **[V1.4]** are new. Two things to read
> first: §21A records that **V1.3's finding that BPHS was unavailable was
> wrong**, and §22A records that the V1.4 calculation modules were built
> *after* obtaining a witness — **6 of 8 have a located source, against 5 of
> 110 for the V1 yoga catalog.**
>
> **V1.3 update.** Sections marked **[V1.3]** are new. The headline finding of
> V1.3 is in §17A and it is not flattering: **95% of the engine's yoga rules
> have no examined textual source**, and the citations they carried since V1.1
> were written from memory by the implementing model and never checked. See
> `SOURCE_VALIDATION.md` for the full audit.
>
> **V1.2 update.** Sections marked **[V1.2]** were added or rewritten in that
> phase. The V1.1 findings below are retained as the record of what was wrong
> and what was done about it; where V1.2 has since superseded a limitation,
> the section says so rather than being quietly edited.

---

## 0A. V1.2 headline: Jupiter and Saturn **[V1.2]**

The largest remaining astronomical limitation has been removed.

| | Jupiter | Saturn |
|---|---|---|
| V1.1 worst case (JPL Keplerian elements) | 599″ = **10.0′** | 807″ = **13.5′** |
| V1.2 worst case (VSOP87A) | **3.1″** | **4.1″** |
| Improvement | **193×** | **197×** |

Median error is now 0.5″ for Jupiter and 0.8″ for Saturn. A separate, purpose-
built fixture of 51 configuration-specific cases (stations, oppositions,
conjunctions, sign crossings, seeded random dates) measures the same upgrade
at 157× and 165× respectively — the factor differs because that fixture is
chosen for coverage, not to hunt the worst case.

Two consequences beyond the two planets:

* **Earth also moved to VSOP87**, because geocentric longitude is the
  direction of the Earth-to-planet vector and an error in the Earth's position
  projects onto every planet. This was measured, not assumed — see §10A. It
  improved Mercury by 3.4× and Venus by 2.4× at no extra cost.
* **Retrograde-flag disagreements with the reference fell from 9 to 0** over
  10,957 daily samples (1990–2020). Saturn alone accounted for 7 of the 9.

**Mars is now the limiting body** at 3.2′; it still uses the Keplerian
elements. See §11A.

Every accuracy number in this document is **measured**, not estimated. The
measurements come from `tools/measure_accuracy.py`, which compares this engine
against the Swiss Ephemeris (Moshier theory) over 1800–2050, and are recorded
in `tests/fixtures/accuracy_profile.json`. Where a claim could not be measured,
it is labelled as unmeasured rather than asserted.

---

## 0. Summary of the verdict

| Area | Verdict |
|---|---|
| Ayanamsha (all four systems) | Correct — agrees with the reference to under 0.002″ |
| Sun, Moon, Mercury, Venus | Correct for all practical Jyotish purposes (≤ 1.6′) |
| Ascendant, Midheaven | Correct (≤ 4.5″) |
| ΔT 1800–2026 | Correct (≤ 0.03 s) |
| **Mars** | **Approximate — 3.2′ worst case. Now the limiting body. [V1.2]** |
| ~~Jupiter, Saturn~~ | ~~Approximate — 10′ and 13.5′~~ → **3.1″ and 4.1″ via VSOP87A [V1.2]** |
| True lunar node | **Was wrong (17.6′). Corrected in V1.1 to 1.1′.** |
| Boundary certainty | **Now exposed explicitly rather than left implicit [V1.2]** |
| Vimshottari timing | **Exact-arithmetic hierarchy to pratyantardasha [V1.2]** |
| Legacy V1 yoga output | **Isolated behind `--legacy-fal` [V1.2]** |
| ΔT after 2026 | Projection only — diverges to 12 s by 2050 |
| All 16 Varga rules | Correct — verified against an independent reimplementation |
| Nakshatra, pada, whole-sign houses | Correct |
| Birth place resolution | **Was unsafe — silently substituted Delhi. Fixed.** |
| Yoga engine | **Was not implementing the classical rules. Replaced.** |

---

## 1. What is mathematically correct

### 1.1 Ayanamsha — correct to under two milliarcseconds

Measured against the Swiss Ephemeris at 1 000 sample dates across 1800–2050:

| System | Median error | Worst error |
|---|---|---|
| Lahiri | 0.001″ | 0.002″ |
| Raman | 0.001″ | 0.002″ |
| Krishnamurti | 0.001″ | 0.002″ |
| Fagan-Bradley | 0.001″ | 0.002″ |

**Important caveat, stated because the number is otherwise misleading.** This
agreement is not independent confirmation that the *definition* of the Lahiri
ayanamsha is right. Both implementations compute the same thing the same way:
a value anchored at J2000 propagated by general precession in longitude. What
this measurement establishes is that the propagation is implemented correctly
and the anchors are accurate. Whether Chitra-paksha *should* be anchored where
it is remains a question for the tradition, not for arithmetic.

The V1 documentation claimed "~15″". That understated the implementation by
four orders of magnitude, but it was an understatement, not an overclaim.

### 1.2 Sun and Moon

| Body | Median | p95 | Worst |
|---|---|---|---|
| Sun (λ) | 8.1″ | 22.4″ | 34.4″ |
| Moon (λ) | 1.8″ | 5.8″ | 10.3″ |
| Moon (β) | 0.6″ | 1.6″ | 2.7″ |

Both are far inside any Jyotish requirement. The Moon's latitude series
(`moon_latitude`, added this phase) reproduces Meeus worked example 47.a
exactly.

### 1.3 Ascendant and Midheaven

Measured at 20 000 samples: five sites from the equator to 64° N, at four
times of day, across 1800–2050:

| Angle | Median | Worst |
|---|---|---|
| Ascendant | 0.5″ | 4.5″ |
| Midheaven | 0.2″ | 1.2″ |

High latitude does not degrade it: Reykjavík at 64° N is no worse than
Singapore. The Ascendant is by far the most accurate quantity the engine
produces, which matters because it is also the one most sensitive to input
error — see §2.6.

### 1.4 ΔT inside the observed record

Between 1800 and 2026 the engine interpolates observed values and agrees with
the Swiss Ephemeris to **0.03 s or better**. This is the correct approach: ΔT
is a measurement of the Earth's rotation, not a model, and interpolating the
record beats fitting a polynomial to it.

### 1.5 The sixteen Varga rules — all correct

Each of the sixteen divisional rules was checked against a **second,
independent implementation** written longhand from the classical statement
(`tests/test_vargas_golden.py`). The engine builds its rules from generic
combinators driven by tables; the reference writes each rule out in the words
of the text. The two agree at:

* 138 240 sampled longitudes (16 Vargas × 12 rashis × 720 samples), and
* 6 456 division boundaries, approached from both sides.

Plus 70 hand-worked spot values written from the rule statements.

**No Varga convention was changed.** The audit found no error in any of them,
so under the Part 9 instruction they stand exactly as they were. The default
convention set is now pinned by a test so it cannot drift.

Individually verified as matching BPHS: D2 Hora (Simha/Karka by parity),
D3 trines, D4 kendras, D7 parity, D9 element starts, D10 parity, D12 from own,
D16/D20/D45 by movability, D24 by parity, D27 by element, D30 unequal
5/5/8/7/5 parts with reversed even-sign lords, D40 by parity, D60 half-degree
parts from the own sign.

### 1.6 Nakshatra, pada and houses

The 13°20′ and 3°20′ arithmetic is exact, and boundary behaviour is verified
by the existing golden boundary fixtures plus the new Varga boundary sweep.
Whole-sign house assignment is exact by construction.

### 1.7 Dispositor chains terminate

Proven by exhaustion in `tests/test_features.py`: every graha in every rashi
for every arrangement terminates either at a self-dispositing graha or in a
detected cycle. Cycle detection is not a guard against a pathological case —
a closed loop is the normal second outcome, and the two-graha loop is the
classical Parivartana.

---

## 2. What is approximate

### 2.1 The planets — the V1.1 position (superseded for Jupiter/Saturn) **[V1.2]**

> **Superseded.** The Jupiter and Saturn figures below were the V1.1 state and
> are now historical: VSOP87A replaced the Keplerian elements for both, and
> for Earth. The current figures are in §10A. The V1.1 numbers are kept here
> because the audit's job is to record what was wrong, not to pretend it never
> was.


| Body | Median | p95 | p99 | **Worst** |
|---|---|---|---|---|
| Mercury | 6.6″ | 21.1″ | 30.9″ | **41.6″ (0.7′)** |
| Venus | 7.9″ | 28.6″ | 52.6″ | **93.9″ (1.6′)** |
| Mars | 16.4″ | 76.4″ | 120.8″ | **203.8″ (3.4′)** |
| **Jupiter** | 142.0″ | 418.6″ | 508.9″ | **599.1″ (10.0′)** |
| **Saturn** | 276.1″ | 629.2″ | 735.8″ | **807.0″ (13.5′)** |

**The V1 documentation claimed "1–3 arcmin" for Mercury through Saturn. That
claim is false.** Mercury and Venus are better than claimed; Mars is marginally
outside it; Jupiter is 3.3× worse and Saturn 4.5× worse than the upper bound
given. The documentation has been corrected to these measured figures.

This is a limitation of the **JPL Keplerian element set**, not a coding error.
Those elements are a two-body approximation with secular rates; they do not
model the mutual perturbations of the giant planets, which is precisely where
Jupiter and Saturn accumulate error. Nothing short of a perturbation theory
(VSOP87 truncated, or a Chebyshev fit to DE440) will improve it.

**Practical consequence, stated plainly.** A Saturn placement within about 15
arcminutes of a sign, nakshatra or pada boundary is **not resolved by this
engine** and must be verified externally. The same applies to Jupiter within
about 10 arcminutes. For every other body the margin is comfortable.

### 2.2 The true lunar node — was wrong, now corrected

This was the largest error in the system and it was undocumented.

| | Median | Worst |
|---|---|---|
| V1 five-term correction series | 185.9″ | **1058.9″ (17.6′)** |
| V1.1 geometric osculating node | 11.3″ | **66.7″ (1.1′)** |

The V1 documentation claimed "~1 arcmin" for the nodes. The measured error was
**17.6 arcminutes** — off by a factor of 17, and large enough to place Rahu in
the wrong pada routinely and in the wrong nakshatra occasionally.

The fix does not add more terms to the series. It computes the node
**geometrically**: two lunar positions a tenth of a day apart span the
instantaneous orbital plane, and the ascending node is where that plane cuts
the ecliptic. This required adding the Moon's latitude series (Meeus ch.47
Σb), which was missing from V1 entirely.

The method is **independent of any external ephemeris** — it uses only this
engine's own lunar longitude and latitude series — so the improvement is
genuine and not a fit to the reference. It is corroborated structurally: the
engine reproduces the lunar node's 18.6-year libration amplitude of 1.889° to
within 0.002°, which is now a self-test.

The **mean** node was already excellent (18.0″ worst) and is unchanged.

> **Note that surprises people:** the true node is **direct about 26 % of the
> time** (measured over 1990–2010). Only the mean node is unconditionally
> retrograde. A chart reporting Rahu as direct is not necessarily in error.

### 2.3 ΔT beyond the observed record

| Year | Engine | Swiss Ephemeris | Difference |
|---|---|---|---|
| 1800–2026 | — | — | ≤ 0.03 s |
| 2030 | 71.4 s | 69.3 s | 2.2 s |
| 2040 | 78.6 s | 71.8 s | 6.8 s |
| 2050 | 86.8 s | 74.6 s | 12.2 s |

Past 2026 both sides are projecting, and the Earth's rotation is not
predictable. The engine uses the older Espenak–Meeus parabola, which runs hot
against the flatter modern extrapolation.

**Impact is small and worth stating precisely.** 12 s of ΔT moves the Moon by
about 6.6″ and the slower bodies by far less. It does **not** affect the
Ascendant at all, because the Ascendant is computed from UT (sidereal time)
and uses TT only for nutation and obliquity. So this is a real divergence, but
not a practical one for natal work.

### 2.4 Speed and retrogression

Measured daily over 1990–2020 (10 957 samples per body, so every station in
thirty years is sampled):

| Body | Retrograde-flag mismatches | Rate | Worst speed error |
|---|---|---|---|
| Sun | 0 | 0 % | 0.00055 °/day |
| Moon | 0 | 0 % | 0.00956 °/day |
| Mercury | 0 | 0 % | 0.00258 °/day |
| Venus | 0 | 0 % | 0.00294 °/day |
| Mars | 1 | 0.009 % | 0.00159 °/day |
| Jupiter | 1 | 0.009 % | 0.00129 °/day |
| **Saturn** | **7** | **0.064 %** | 0.00078 °/day |

Retrogression is **derived**, not looked up — daily motion is a central
difference of the computed longitude — so the direction falls out of the
arithmetic. Every mismatch occurs within a day or two of a station, where the
true speed is genuinely near zero.

The engine reports a body as **stationary** when |speed| < 0.005 °/day.
This threshold is an **honesty device, not an astronomical definition**: below
it, the engine's own accuracy cannot resolve the direction of travel. A
classical "stationary" period is a different and longer thing. The regression
chart is the illustrative case — Saturn turned direct on 11 September 1988,
twelve days after the birth, and the engine correctly declines to call its
direction.

### 2.5 Fabricated speeds for entered charts (fixed this phase)

`JyotishChart.from_sidereal_longitudes` assigned every graha a speed of
**±1.0 °/day** as a placeholder. Two consequences, neither previously visible:

* `is_stationary` was always `False` for an entered chart, presented as fact;
* any rule reading speed would have read a fabricated number.

Now: real speeds are carried across from the calculated chart where they are
known, bodies without one are tracked in `speeds_are_measured`, and the feature
report marks their motion with an asterisk and emits an explicit caveat.

### 2.6 Geographic longitude and the Ascendant (documentation error)

V1 documentation, §2.3:

> "A 1° error in longitude shifts the Lagna by about 4 minutes of arc."

**This is wrong, and wrong in the dangerous direction — it understates the
sensitivity by a factor of roughly fifteen.**

The correct statement: **1° of geographic longitude corresponds to 4 minutes
of *time*.** In four minutes the Ascendant moves roughly one degree, varying
with latitude and with which rashi is rising. Measured:

| Latitude | Ascendant shift per 1° of longitude |
|---|---|
| 0° | 56 arcmin |
| 26.9° (Jaipur) | 57 arcmin |
| 45° | 53 arcmin |
| 60° | 40 arcmin |
| 64.1° (Reykjavík) | 34 arcmin |

For the regression chart specifically the shift is **83 arcmin**. So an
imprecise birth place is a far bigger threat to the Lagna than the V1
documentation suggested — which is exactly why the silent Delhi fallback
(§3.1) was the most serious defect found.

---

## 3. What needed correction

### 3.1 Unknown birth places silently became Delhi — **the most serious defect**

`main.py` contained its own `CITY_DATA` table and this fallback:

```python
# Default to Delhi if not found
print(f"  ⚠ City '{place}' not in database — using Delhi coordinates.")
return CITY_DATA["delhi"]
```

A chart computed on the wrong coordinates is not a degraded answer; it is a
confidently wrong one. Combined with §2.6, substituting Delhi for an unknown
place moves the Ascendant by up to a full rashi, which changes every house,
every house lord, and therefore every yoga and every interpretation
downstream. The warning went to stdout among hundreds of other lines.

The matching was also unsafe in its own right:

```python
if city in key or key in city:
```

Substring matching in both directions, so `"York"` matched `"new york"` and
any string containing `"delhi"` matched Delhi.

**Compounding this:** a correct `engine/location.py` already existed, with a
proper `BirthLocation` model, IANA time-zone support and no fallback — and
**nothing imported it**. `main.py` used its own table instead. The module was
dead code.

`engine/input_model.py` had a third instance of the same fault:

```python
place=str(data.get("place", "Delhi")),
```

A consultation JSON with no `place` key silently became a Delhi chart.

**Fixed.** `main.py` now uses `engine.location.resolve_location`; the private
table and the fallback are deleted; a missing `place` in JSON raises; and an
unresolvable place exits with code 2 and an actionable message naming the
flags that fix it. New flags `--lat`, `--lon`, `--timezone`, `--utc-offset`
and `--list-cities` make any birth place usable.

### 3.2 The Yoga engine was not implementing the classical rules

This was not a matter of missing detail. Several rules did not encode the
combination they were named after.

| V1 rule | What it actually tested | What the classical rule requires |
|---|---|---|
| "Raja Yoga" | any graha of strong dignity in a kendra | a **relationship** between a kendra lord and a trikona lord |
| "Dhana Yoga" | any exalted graha in the 2nd or 11th | a **relationship** among the lords of the 1st, 2nd, 5th, 9th, 11th |
| "Neecha Bhanga Raja Yoga" | any debilitated graha in a kendra | debility **cancelled** by a named clause, **and** falling on a kendra or trikona |
| "Kemadruma" | reported present, no cancellation analysis | forms on isolation, but is **cancelled** by any of several bhanga clauses |

The Raja and Dhana rules had no notion of house lordship at all. The Neecha
Bhanga rule inverted its own meaning: it fired on the *absence* of a
cancellation clause, reporting a plain debility as a Raja Yoga.

Kemadruma was the most misleading in practice. The bhanga clauses are common —
in the regression chart **four** of them apply — so reporting bare presence
inverts the reading for most charts that have it.

**Replaced** by `engine/rules/`: 90 declaratively specified, source-tagged
rules with formation, cancellation and strength evaluated as three separate
stages, resolving to five states rather than a boolean. See §5.

### 3.3 Combustion ignored retrograde arcs

`COMBUSTION_ORB` held one arc per graha. Several classical sources give a
narrower arc for retrograde Mercury and Venus, since a retrograde inferior
planet meets the Sun at inferior conjunction and is nearer the Earth.

The angular separation from the Sun was also **computed and discarded** — only
the boolean survived, so no rule could ask how close a graha actually was.

**Fixed.** `CombustionProfile` carries direct and retrograde arcs, is
replaceable, and the separation is stored for every graha whether combust or
not. Rahu and Ketu are now explicitly excluded with a stated reason (shadow
grahas cannot be burnt) rather than by absence from a table.

### 3.4 Four Varga "choices" that cannot change anything

For **D7, D16, D20 and D27** the `parivritti` convention is **mathematically
identical** to the `parashari` default at every longitude. Verified over
36 000 samples each.

The reason is arithmetic coincidence:

| Varga | Why they coincide |
|---|---|
| D7 | 7 ≡ 7 (mod 12); 6s ≡ 0 for odd rashis and 6 for even ones — exactly the rule's offset |
| D16 | 16 ≡ 4 (mod 12); movability has period 3 and 4 × 3 ≡ 0 |
| D20 | 20 ≡ 8 (mod 12); movability has period 3 and 8 × 3 ≡ 0 |
| D27 | 27 ≡ 3 (mod 12); element has period 4 and 3 × 4 ≡ 0 |

These are identities, not defects — neither rule is wrong. But presenting two
named options that cannot produce different output implies a choice that does
not exist. Recorded here, and pinned by a test so a future rule change that
collapses another pair onto each other is caught.

### 3.5 Documented worked example had a wrong ayanamsha

DOCUMENTATION.md §10 stated the Lahiri ayanamsha for 1988-08-30 14:48 UTC as
**23.6946°**. The correct value is **23.6987294°** (Swiss Ephemeris
23.69872943; this engine 23.69872944). The published figure was wrong by
**15 arcseconds**. Corrected, and pinned by a regression test.

### 3.6 Smaller findings

* **`--consultation` accepted a chart with no place.** Now rejected.
* **`detect_yogas` was imported into `main.py` but never called there.**
  Harmless; left in place for backwards compatibility.
* **`compute_vimshottari_dasha` accepts a `birth_date` it never uses.** Periods
  are reported as ages only. Not a defect, but the parameter is misleading and
  calendar dates are an obvious next step.
* **`DashaPeriod.years` holds the full period length even for the first,
  partial mahadasha,** so `str(period)` prints a duration that disagrees with
  its own start and end ages. Cosmetic; not corrected this phase to avoid
  changing existing output.
* **`fal.py` re-implemented `_house_of`** rather than using
  `JyotishChart.house_of`. Exactly the kind of duplication the new feature
  layer exists to prevent. Left untouched so V1 output is byte-identical.

---

## 4. What is tradition-dependent

These are not errors and must not be "fixed". They are points where
authorities genuinely differ, and the engine's obligation is to be explicit
about which reading it used.

| Question | Engine's position |
|---|---|
| **Rahu/Ketu drishti** | **Configurable, default asserts nothing.** Traditions give the nodes 5/7/9, 3/7/11, kendra aspects, or none. `--node-aspects` selects; the default `none` makes no claim, and the choice is printed in the provenance block. |
| **Rahu/Ketu exaltation** | Carried as Vrishabha/Vrishchika (as V1 had it) but flagged tradition-dependent. BPHS assigns the nodes no exaltation rashi; later tables disagree with each other. |
| **Node ownership of rashis** | Not assumed. The nodes own nothing, so they never appear as a house lord and have no functional nature. Co-lordship of Kumbha/Vrishchika is a later view and would be a named profile. |
| **Mahapurusha reckoned from Lagna or Moon** | Both, as **separate rules in separate profiles**. The from-Moon variant carries `variant_of` and exists only in `parashari_extended`. |
| **Chandra-Mangala by conjunction or aspect** | Both, as separate rules. Conjunction is core; aspect is a variant. |
| **Retrograde = strong or frustrated?** | **No side taken.** Retrogression is recorded as a strength modifier with weight **0.0** and a stated reason, so it appears in the report without silently moving a score. |
| **Mercury/Venus retrograde combustion arcs** | Included in the default profile, and the profile is replaceable. |
| **Kemadruma bhanga clauses** | Four clauses implemented, each reported by name. Authorities differ on how many count and on whether the nodes relieve isolation; the engine excludes Surya and the nodes, which is the majority reading, and says so. |
| **Budha's and Chandra's natural nature** | Conditional in the classical scheme. Budha follows its company; Chandra is judged by paksha. When context is unavailable the unmodified default is returned rather than a guess. |
| **Compound (panchadha) friendship** | Natural and temporary friendship are computed **separately** and the compound is derived from both, so a caller can always see which component drove the result. |
| **Varga conventions** | Unchanged from V1. All sixteen remain named, selectable and printed. |
| **House system** | Whole-sign only. Not a tradition choice the engine offers yet — see §7. |

---

## 5. Architecture: why FACT and INTERPRETATION are now separated

The V1 Yoga code recomputed its own facts inline — house positions, dignity
checks, conjunction tests — each in its own way. That is why its rules drifted
from the combinations they were named after: there was no single statement of
what "conjunct" or "aspects" meant.

V1.1 splits this into four layers, and the boundary between the second and
third is enforced by construction:

| Layer | Module | Answers |
|---|---|---|
| **Astronomical fact** | `engine/ephemeris.py` | Where is the body? |
| **Calculated astrology feature** | `engine/features/` | What is its sign, house, lordship, dignity, drishti, dispositor, varga standing? |
| **Tradition-specific rule** | `engine/rules/` | Does a named classical combination form, is it cancelled, how strong is it? |
| **Interpretation** | *not built* | What does it mean for this person? |

**The rule engine never calculates.** It reads a `ChartFeatures` and nothing
else. Every rule that needs a fact must get it from the feature layer, which
is the constraint that stops two implementations of "is Mangal aspecting the
7th" from ever disagreeing again.

Five-state Yoga results replace the boolean:

```
ABSENT · PRESENT · PRESENT_BUT_CANCELLED · PRESENT_BUT_WEAKENED · PRESENT_AND_STRONG
```

Evaluation is strictly ordered — **existence, then cancellation, then
strength** — and strength is never computed for a Yoga that does not exist.
This ordering is what the V1 engine collapsed, and collapsing it is what
produced "Raja Yoga" from a merely dignified graha.

**On strength scores.** No classical text scores a Yoga numerically. The
0.0–1.0 figure is an engine convention for ranking results *within one chart*,
it is labelled as such everywhere it appears, and every modifier states its
reason so the number can be audited rather than trusted.

---

## 6. What should remain configurable

| Setting | Mechanism | Why it must stay open |
|---|---|---|
| Ayanamsha | `--ayanamsha` | No consensus; four systems supported |
| Lunar node | `--node true\|mean` | Both are in live use |
| Varga conventions | `--varga-config` | Schools differ, especially D2/D16/D20/D24/D30/D40/D60 |
| Node drishti | `--node-aspects` | Genuine disagreement; default must assert nothing |
| Yoga rule profile | `--rule-profile` | Variant readings must stay separable, never merged |
| Combustion arcs | `CombustionProfile` | Arcs vary by source and by direction of motion |
| Conjunction orb | `build_chart_features(conjunction_orb=…)` | Orb is a modern overlay on a rashi-based rule |
| Comparison tolerance | `--tolerance` | Depends on the provenance of the entered degrees |

---

## 7. Known limits after this phase

| Area | State |
|---|---|
| **Jupiter, Saturn** | 10′ and 13.5′ worst case. **Boundary placements are unresolved.** Needs VSOP87 or a DE-series fit. |
| Mars | 3.4′ worst case — safe except very near a pada boundary |
| Date range | 1800–2050 for planets; ΔT projects beyond 2026 with growing error |
| Stationary detection | Cannot resolve direction below 0.005 °/day; reports "stationary" instead of guessing |
| House system | Whole-sign only. No Bhava Chalit, Sripati or Placidus. |
| Bhava madhya | Not computed, so no cusp-based house strength |
| Shadbala, Ashtakavarga, Vimshopaka | Not implemented. `vimshopaka_inputs()` returns the raw per-varga dignities a calculation would need, but no weighting scheme. |
| Dasha | Mahadasha only; ages, not calendar dates; no antardasha |
| Yoga catalog | 90 rules. Nabhasa, Sankhya, Arishta and most Chandra yogas are not modelled. |
| Outer planets | Not included — outside classical Jyotish |
| Geocoding | 62 built-in places; anything else needs explicit coordinates (which is now possible, and fails loudly when it is not supplied) |
| Historical time zones | IANA data is used and resolves for the birth moment, so pre-1947 Indian local time and DST are handled where tzdata has them. Not independently verified against historical records. |

---

## 8. How the accuracy claims can be re-checked

```bash
# Measure against Swiss Ephemeris (development virtualenv, not the app)
.venv/bin/python tools/measure_accuracy.py

# Regenerate the golden fixtures
.venv/bin/python tools/generate_reference.py

# The application's own checks — no third-party dependency
python3 main.py --selftest
python3 -m unittest discover -s tests
```

The application never imports `swisseph`; a test asserts this. The reference
tooling is development-only, which is what keeps the golden tests meaningful
rather than self-confirming.

---

## 9. Recommended next phase (V1.1 — status in V1.2) **[V1.2]**

1. ~~Replace the planetary theory for Jupiter and Saturn.~~ **Done in V1.2**
   with VSOP87A; Earth was upgraded too, which the benchmark showed to be
   necessary. See §10A.
2. Bhava Chalit / cusp-based houses — **still open.**
3. ~~Antardasha and pratyantardasha, with calendar dates.~~ **Done in V1.2**;
   see §12A.
4. ~~Extend the Yoga catalog.~~ **Partly done in V1.2**: 90 → 110 rules (122
   with variants). Nabhasa and Arishta families remain.
5. Shadbala and Ashtakavarga — **still open.**
6. Transits (Gochar) and the interpretation layer — **still out of scope.**

---

## 10A. VSOP87 for Jupiter, Saturn and Earth **[V1.2]**

### Provenance — and why it matters here

The V1.2 brief warned against implementing "a random truncated VSOP87 formula
found online". It is a real hazard: VSOP87 coefficient tables are widely
copied, frequently mistyped, and almost never accompanied by a way to tell.

What was done instead:

| | |
|---|---|
| **Theory** | VSOP87, Bretagnon P. & Francou G., 1988, *Astron. Astrophys.* **202**, 309–315 |
| **Variant** | VSOP87**A** — heliocentric rectangular, dynamical ecliptic and equinox J2000 |
| **Source** | `ftp://ftp.imcce.fr/pub/ephem/planets/vsop87/` (IMCCE, the theory's home institution) |
| **Files** | `VSOP87A.ear`, `VSOP87A.jup`, `VSOP87A.sat`, SHA-256 recorded in `engine/vsop87_data.py` |
| **Validation** | Against `vsop87.chk` — reference values **published by the theory's own authors** |

Variant A was chosen because the existing pipeline already worked in
heliocentric rectangular J2000 coordinates, so VSOP87 drops in upstream of
light-time with no change to the frame handling.

**The parse was validated before anything else was measured.** Evaluating the
full untruncated series at the 30 dates in `vsop87.chk` reproduces the
published values to a worst error of **7.8 × 10⁻¹¹ au** — which is the
rounding of the published ten-decimal figures. This is a stronger check than
any comparison against another ephemeris, because it isolates *our reading of
the coefficients* from every other source of error.

No coefficient was fitted, rounded or adjusted. The Swiss Ephemeris was used
only to measure the finished result, never to choose a coefficient.

### Answering the brief's question: does Earth need VSOP too?

The brief required benchmarking configuration A against configuration B rather
than assuming. Full untruncated series, 3,117 dates across 1800–2050:

| Configuration | Jupiter worst | Saturn worst |
|---|---|---|
| Baseline: Keplerian everything | 635.5″ | 830.9″ |
| **A**: Keplerian Earth + VSOP Jupiter/Saturn | 7.12″ | 5.81″ |
| **B**: VSOP Earth + VSOP Jupiter/Saturn | **2.90″** | **4.23″** |

**A is 1.7× worse than B**, so Earth is a genuine co-limiting factor and was
upgraded. The reason is geometric: the geocentric direction to a planet is the
direction of the vector *from the Earth*, so the Earth's own positional error
of order 10⁻⁴ au projects onto a body 4–6 au away as several arcseconds.

Upgrading Earth also improved the bodies that were not otherwise touched:

| Body | Before | After | |
|---|---|---|---|
| Mercury | 41.6″ | 12.3″ | 3.4× |
| Venus | 93.9″ | 38.5″ | 2.4× |
| Mars | 203.8″ | 192.2″ | 1.06× |

Mars barely moves because its own Keplerian elements, not the Earth's, are its
limit.

### Choosing the truncation

Terms were dropped by amplitude alone. Measured across the same 3,117 dates:

| Threshold (au) | Terms | Jupiter worst | Saturn worst |
|---|---|---|---|
| 0 (full series) | 15,484 | 2.90″ | 4.23″ |
| 1 × 10⁻⁸ | 10,735 | 2.89″ | 4.23″ |
| 1 × 10⁻⁷ | 4,501 | 2.97″ | 4.24″ |
| **1 × 10⁻⁶ (chosen)** | **1,874** | **3.13″** | **4.15″** |
| 1 × 10⁻⁵ | 737 | 8.15″ | 4.00″ |

**1 × 10⁻⁶ was chosen**: 1,874 terms (110 Earth, 639 Jupiter, 1,125 Saturn,
117 KiB of generated Python) reaching within 0.25″ of the full series. Going
finer buys nothing measurable; the residual is set by other parts of the
pipeline, not by the truncation.

The target was ≤ 1 arcminute. The result is **≤ 4.2 arcseconds**, roughly
fourteen times better than asked.

### An honest limit on the claim

The residual 3–4″ is **at the resolution of the reference being measured
against**. Swiss Ephemeris in Moshier mode itself differs from the JPL DE
series by of order an arcsecond for the outer planets over this span. So the
defensible statement is:

> Jupiter and Saturn agree with an independent reference to within a few
> arcseconds, which is as close as that reference can resolve.

It is **not** "accurate to 3 arcseconds in an absolute sense". Establishing
that would need a DE-series comparison, which has not been done.

### What was preserved

The brief required these to survive the swap, and they did — VSOP87 replaces
only the heliocentric position step:

light-time iteration · coordinate transformation · precession · nutation ·
ayanamsha conversion · retrograde detection · station detection.

Retrograde and station detection in fact *improved*: disagreements with the
reference fell from 9 to 0.

---

## 11A. Boundary safety and numerical uncertainty **[V1.2]**

`engine/uncertainty.py` makes the engine state when a classification is not
resolved by its own arithmetic.

A placement is reported **UNRESOLVED** when it lies nearer a rashi, nakshatra,
pada or varga boundary than the *measured worst-case error for that body*.
The envelopes are not estimates and not shared:

| Body | Envelope | Theory |
|---|---|---|
| Jupiter | 0.05′ | VSOP87A |
| Saturn | 0.07′ | VSOP87A |
| Moon | 0.17′ | Meeus ch.47 |
| Mercury | 0.21′ | Keplerian |
| Sun | 0.57′ | Meeus ch.25 |
| Venus | 0.64′ | Keplerian |
| Rahu / Ketu | 1.11′ | osculating node |
| **Mars** | **3.20′** | **Keplerian — the limiting body** |

The point of per-body envelopes is that the same longitude can be resolved for
one graha and not another: at 1′ from a rashi boundary, Jupiter's placement is
certain and Mars's is a coin toss. A test asserts exactly that.

A test also asserts that these constants still match
`tests/fixtures/accuracy_profile.json`, so an accuracy change cannot leave
stale tolerances silently claiming certainty the engine no longer has.

**D30 is deliberately excluded** from varga boundary checks: Trimshamsha has
unequal parts (5/5/8/7/5°), so a single division span does not describe it,
and reporting a number that is not true of the chart would be worse than
reporting nothing.

---

## 12A. Vimshottari timing engine **[V1.2]**

Moved out of the legacy `fal.py` into `engine/timing/`, which imports neither
the rule layer nor the feature layer — a test enforces that.

**Numerical policy.** Every duration is an exact `Fraction` of days and every
boundary is an offset from its parent's start. Nothing accumulates by repeated
addition of rounded years. The consequences are testable as equalities rather
than approximations, and they are tested that way: children sum to their
parent exactly, the first child starts exactly at the parent's start, the last
ends exactly at the parent's end, and the last pratyantardasha of the 120-year
span ends exactly at the span's end.

**One generic subdivision.** `subdivide(parent, level)` produces any level:

```
child_duration = parent_duration × years[child_lord] / 120
```

Antardasha and pratyantardasha are the same operation at different depths, not
two calculations. Sukshma and Prana already work; they are simply not built by
default.

**Year-length convention — a real choice, made explicit.** The classical texts
state period lengths in years but never define the year in days, and the
choice moves long-period boundaries by months. Four named conventions are
available and the active one is recorded in every result:

| Convention | Days | Note |
|---|---|---|
| **`julian` (default)** | 365.25 | Makes the 120-year cycle exactly 43,830 days |
| `gregorian` | 365.2425 | Mean Gregorian calendar year |
| `sidereal` | 365.25636 | Arguably the most defensible for a sidereal system |
| `savana` | 360 | Used by some traditions; shortens the cycle by ~1.7 years |

**The birth mahadasha begins before birth**, by the elapsed portion of the
Moon's nakshatra, with the balance at birth reported — the figure classical
practice quotes.

---

## 13A. Yoga catalog and score terminology **[V1.2]**

**Catalog: 90 → 110 rules** (122 including variant profiles). Added: Vipareeta
Raja Yoga (Harsha, Sarala, Vimala), Parivartana (maha/dainya/khala), Sunapha,
Anapha, Durudhara, Vesi, Vasi, Ubhayachari, Adhi, Amala, Lakshmi, Saraswati,
the four Kemadruma Bhanga clauses as findable rules, and a stricter Gajakesari
variant.

Three disciplines were applied and are worth recording:

* **Nothing was invented.** Where a source states a condition vaguely — Lakshmi
  Yoga's "strong Lagna lord" — the concrete reading the sources share (own
  rashi or exaltation) was implemented, and the note says so. A broader notion
  of "strength" was *not* invented to widen the rule.
* **Untraced sources say so.** `D30/movable_lords`, `D60/reverse_even` and the
  variant yoga readings carry "exact attribution not established" rather than
  a chapter number that may not contain them.
* **Differing authorities stay apart.** The strict Vipareeta reading (dusthana
  lord must fall into a *different* dusthana) is a separate rule id in a
  separate profile, because a chart can satisfy one and not the other.

**Score terminology.** `strength` became **`engine_strength_score`**, carried
with `score_type: "software_heuristic"` and `classical_measure: false` so the
number cannot travel without its disclaimer. `strength` remains as a read-only
alias for V1.1 callers.

The **existence guarantee** is now tested structurally rather than asserted:
across many charts and every rule, a yoga that is ABSENT always has a failed
condition to point at, and the only route to "present but not effective" is an
explicit cancellation clause. A score can never make or unmake a yoga.

---

## 14A. What is tested, and how strongly **[V1.2]**

The brief asks for this distinction explicitly, because "the tests pass" and
"the astrology is right" are different claims.

| Claim | Established for |
|---|---|
| **Computationally tested** | Everything. 460 tests: structure, invariants, boundaries, serialisation, error paths, robustness across many synthetic charts. |
| **Externally benchmarked** | All planetary positions, the ayanamsha, the Ascendant, ΔT, retrogression and station detection — against Swiss Ephemeris, an independent theory. Plus the VSOP87 parse against the theory authors' own published values, which is stronger still. |
| **Tradition / source validated** | **Nothing.** No Varga convention and no yoga rule has been checked against a primary text or an authority's worked examples. |

That last row is the important one. The Varga test suite compares 138,240
longitudes and 6,456 boundaries between two independent implementations — but
both implement *the same stated rule*, so what it establishes is that the code
is right, not that the rule was read correctly. `engine/varga_metadata.py`
records this on every convention as `implementation_consistency`, and a test
asserts that nothing claims `tradition_source_validated` until that work is
actually done.

The same caveat applies to the yoga catalog: each rule cites a source, but no
independent scholar has confirmed the engine's reading of it.

---

## 15A. Remaining limitations after V1.2 **[V1.2]**

| Area | State |
|---|---|
| **Mars** | 3.2′ worst case — now the limiting body. VSOP87A would fix it; the infrastructure is already built, so it is a fetch-and-regenerate away. |
| Mercury, Venus | 12″ and 39″ — adequate, still on Keplerian elements |
| True node | 1.1′ — the osculating construction is at the limit of the truncated lunar series behind it |
| ΔT after 2026 | Projection; ~12 s by 2050, with no practical effect on the Lagna |
| Date range | 1800–2050. VSOP87 itself is valid far wider; the Keplerian bodies are the constraint. |
| House system | Whole-sign only. No Bhava Chalit, Sripati or Placidus; no bhava madhya. |
| Dasha systems | Vimshottari only. No Ashtottari, Yogini or Chara. |
| Dasha depth | Built to pratyantardasha by default; sukshma and prana work but are not built. |
| Yoga catalog | 110 rules. Nabhasa, Sankhya and most Arishta families absent. |
| Shadbala, Ashtakavarga | Not implemented |
| Source validation | **None, anywhere.** See §14A. |
| Transits, interpretation | Out of scope by instruction |

---

## 16A. Recommended V1.3 scope — status **[V1.3]**

1. ~~Mars to VSOP87A.~~ **Done.** See §17A below; 185" to 8.0".
2. ~~Source validation of the Varga conventions and the highest-traffic yoga
   rules.~~ **Attempted, and the attempt is the finding.** One Sanskrit
   witness was obtainable; 95% of rules remain unverified. See §18A.
3. Bhava Chalit houses — **designed, not implemented.** See
   `BHAVA_CHALIT_DESIGN.md`, and §6 of it for why implementing before the
   rules are sourced would move two unknowns at once.
4. Transit engine — **interfaces designed and feasibility-tested**, no logic.
5. Ashtottari and Yogini dashas — still open.
6. Shadbala and Ashtakavarga — still open.

---

## 17A. Mars to VSOP87A **[V1.3]**

| | Mars |
|---|---|
| V1.2 worst case (JPL Keplerian elements) | 184.6″ = **3.08′** |
| V1.3 worst case (VSOP87A) | **8.0″ = 0.13′** |
| Improvement | **23×** |

Median 0.5″, mean 0.8″, p95 2.4″, measured over 3,117 dates across 1800–2050.

Built through the same pipeline as Earth, Jupiter and Saturn: authoritative
IMCCE coefficients, SHA-256 recorded, parse validated against `vsop87.chk`
(the theory authors' own published values) to 7.8 × 10⁻¹¹ au before anything
was measured. No coefficient transcribed by hand.

**Truncation is finer for Mars than for the others** — 10⁻⁷ au, 862 terms,
against 10⁻⁶ for Earth/Jupiter/Saturn. Mars is the nearest of these bodies to
the Earth, so the same absolute position error subtends a larger angle: at
10⁻⁶ it reaches 11.7″, at 10⁻⁷ it reaches 8.0″. The other three are already at
their floor by 10⁻⁶ and gain nothing from going finer.

### The limiting body is now Rahu/Ketu

| Body | Worst | Theory |
|---|---|---|
| **Rahu / Ketu (true node)** | **67″ = 1.11′** | osculating node |
| Venus | 39″ = 0.64′ | Keplerian |
| Sun | 34″ = 0.57′ | Meeus ch.25 |
| Mercury | 12″ = 0.21′ | Keplerian |
| Moon | 10″ = 0.17′ | Meeus ch.47 |
| Mars | 8″ = 0.13′ | VSOP87A |
| Saturn | 4.1″ | VSOP87A |
| Jupiter | 3.1″ | VSOP87A |

**Scope was deliberately not widened to chase it.** The true node is not a
planetary-theory problem: it is already derived geometrically from this
engine's own lunar series, so improving it means improving the truncated
ELP2000 series behind it. That is not trivial and not clearly justified, which
is the condition the V1.3 brief set for widening scope.

### Regression: nothing changed

Across all 74 fixture cases the Mars migration changed **zero** rashi,
nakshatra, pada or varga classifications. Median longitude shift 0.196′, worst
2.341′ — real, but never across a boundary in any fixture.

A broader sweep at 7-day steps over 1800–2050 found 3 of 13,045 samples
(0.023%) where the rashi would change, consistent with a ~2′ shift against a
30° sign. **No expected value was edited**, which is the outcome the brief
asked for: fixtures must not be adjusted until tests pass.

Reproduce with `python3 tools/mars_migration_report.py`.

### Wording

Every figure above is **agreement with a reference**, not absolute accuracy.
Swiss Ephemeris in Moshier mode itself differs from the JPL DE series by of
order an arcsecond for the outer bodies, so residuals at that level mean
"indistinguishable from the reference", not "correct to that tolerance".

---

## 18A. The source audit — the V1.3 headline **[V1.3]**

Full detail in `SOURCE_VALIDATION.md`. The summary:

| Claim | Status |
|---|---|
| COMPUTATIONALLY TESTED | Yes — 560 tests |
| EXTERNALLY BENCHMARKED | Yes, for astronomy |
| TEXTUAL SOURCE LOCATED | **5 of 110 rules; 2 of 32 Varga conventions** |
| TRADITION/SOURCE VALIDATED | **Nothing** |

### What was actually obtained

**One work.** Varāhamihira's *Bṛhajjātaka*, in the GRETIL digital text from the
Oriental Books Reprint Corporation second edition (1979), SHA-256 recorded.
Five passages located:

| Passage | Establishes |
|---|---|
| BJ 1.6 | The navāṃśa (D9) rule — names all four starting rashis |
| BJ 1.7 | The triṃśāṃśa (D30) lord order and parity reversal |
| BJ 13.2 | Adhi Yoga: benefics in the 6th/7th/8th **from the Moon** |
| BJ 13.3 | Sunaphā, Anaphā, Durudhurā, Kemadruma — with the Sun-exclusion and the Kemadruma cancellations |
| BJ 12 | The Nābhasa chapter — recorded because the engine does *not* implement these |

### What was not obtained, and why it matters most

**Brihat Parashara Hora Shastra.** Roughly a hundred rules cite it. No witness
could be retrieved: GRETIL does not hold the text, and the scanned Devanagari
editions on public archives could not be obtained in usable OCR.

Those citations — `BPHS ch.36` and the like — **were written from memory by the
implementing model in V1.1 and V1.2 and have never been checked.** Several are
probably wrong. A bare work name does not identify a passage in any case: BPHS
is a textual tradition whose chapter division, verse numbering and readings
differ between editions.

They are recorded as UNVERIFIED and **not deleted**. An untraced rule is not a
wrong rule, and most are in common use.

### Three findings from the one witness we did have

1. **BJ 13.3 excludes only the Sun** (`hitvā arkaṃ`) from the Moon yogas. The
   engine also excludes Rahu and Ketu, on no located authority. Registered as
   conflict `SUNAPHA_NODE_EXCLUSION`; behaviour left unchanged pending a
   second witness, but the divergence is recorded on every affected rule.
2. **BJ 13.3 gives two Kemadruma cancellations** plainly (Moon angular; Moon
   conjoined) and reports a further opinion it appears to set aside. The
   engine implements four. Registered as `KEMADRUMA_BHANGA_EXTENT`. The
   primary text is itself a witness to a disagreement that was already live.
3. **BJ 13.2 confirms Adhi Yoga is reckoned from the Moon**, which is what the
   engine does — and confirms that holding the from-the-Lagna reading in a
   separate profile was the right structure.

Because of finding 1, Sunaphā/Anaphā/Durudhurā were **downgraded** from
IMPLEMENTATION_MATCHED to RULE_INTERPRETATION_MAPPED. A known divergence,
however small, means the implementation does not match the located text.

### Enforcement, not labelling

Every validation status has a stated evidence requirement checked in
`engine/sources/validation.py`, and a test asserts no recorded evidence
overclaims. A WEB_SUMMARY can never support validation, by construction.

`parashari_strict` was redefined from "the strict Vipareeta reading" to
**evidence-gated**: membership is computed from the registry, so a rule cannot
be admitted by editing the catalog, only by producing evidence. It now contains
**1 rule of 110** (`adhi_yoga`). The V1.2 meaning survives as
`parashari_vipareeta_strict`.

**That the strict profile is nearly empty is the finding, not a defect in it.**

### Eleven questions queued for human review

Recorded in `engine/sources/registry.py`, reported in §9 of
`SOURCE_VALIDATION.md`. They include the reading of `sva` in BJ 13.3, whether
BJ 1.7 encodes the 5/5/8/7/5 triṃśāṃśa division, and where the Pañca
Mahāpuruṣa yogas are first attested — they are **not** in Bṛhajjātaka.

These were queued rather than answered. A model that resolves a Sanskrit
ambiguity by choosing the reading that makes its own code correct has validated
nothing; it has laundered a guess.

---

## 19A. Remaining limitations after V1.3 **[V1.3]**

| Area | State |
|---|---|
| **Source validation** | **95% of rules unverified; nothing tradition-validated.** The dominant limitation of this engine, and it is now measured rather than unexamined. |
| Rahu/Ketu | 1.11′ — the limiting astronomical body. Needs a better lunar series. |
| Venus, Mercury, Sun | 0.64′, 0.21′, 0.57′ — adequate, still Keplerian for the first two |
| ΔT after 2026 | Projection; ~12 s by 2050, no practical Lagna effect |
| Date range | 1800–2050, constrained by the Keplerian bodies |
| House system | Whole-sign only. Bhava Chalit designed, not built. |
| Dasha systems | Vimshottari only |
| Yoga catalog | 110 rules. Nābhasa absent — and now known to be absent, since BJ 12 was located. |
| Transits | Interfaces only |
| Shadbala, Ashtakavarga | Not implemented |

---

## 20A. Recommended V1.4 scope **[V1.3]**

1. **Obtain a named BPHS edition.** Single highest-value action available:
   would put ~100 rules within reach of TEXT_LOCATED. The edition must be
   identified, since the numbering is not stable.
2. **Sārāvalī and Phaladīpikā** — the usual attribution for the Pañca
   Mahāpuruṣa and the Sun yogas, neither of which is in Bṛhajjātaka.
3. **A Sanskritist** for the eleven queued questions. Several are cheap to
   answer and unblock whole rule families.
4. **Bhava Chalit**, reporting-only under Policy A of the design document.
5. **Birth-time confidence as an input**, propagated through the uncertainty
   layer — a prerequisite for honest Bhava Chalit, and useful alone.
6. Transit engine against the V1.3 interfaces, still without prediction.
7. Rahu/Ketu accuracy, if a better lunar series is worth the size.


---

## 21A. V1.3 was wrong about BPHS **[V1.4]**

V1.3 recorded Brihat Parashara Hora Shastra as unobtainable and wrote that
conclusion into `UNAVAILABLE_WORKS`. It was wrong, and the way it was wrong is
worth recording.

**What actually happened.** V1.3 tried GRETIL (which does not hold the text)
and one archive.org identifier whose download failed, then concluded the work
was unavailable. V1.4 searched thirteen identifiers and reached the **R.
Santhanam translation** (Ranjan Publications) in usable OCR within minutes.

**The error was of category, not of effort.** "We could not find it" is a
claim about the search. V1.3 recorded it as a claim about the text. Those are
different statements and only the first was supported.

`UNAVAILABLE_WORKS` now carries a `retrieval_attempts` field on every entry,
and a test requires it, so the next reader can see what was tried rather than
inferring that everything was.

**What was obtained.**

| Witness | Tier | Covers |
|---|---|---|
| `BPHS_SANTHANAM_V1` | TRANSLATION | chapters 1-45 |
| `BPHS_SANTHANAM_V2` | TRANSLATION | chapters 46 onward |
| `BPHS_27_SHADBALA` | TRANSLATION | ch. 27, the Shadbala chapter |
| `BPHS_66_ASHTAKAVARGA` | TRANSLATION | ch. 66, the Ashtakavarga chapter |

**What is still missing: a SANSKRIT BPHS.** The Santhanam volumes are an
English translation, and a translator's choice among readings is an
interpretation. So `BPHS_SANSKRIT` remains in `UNAVAILABLE_WORKS`, and nothing
resting on these witnesses can reach TRADITION_VALIDATED, which requires
Sanskrit tier.

**Copyright.** The translation is in copyright. Only metadata, locators,
checksums and short paraphrases in the engine's own words are stored. The
volumes were read outside the repository and are not vendored.

---

## 22A. Sourcing first, implementing second **[V1.4]**

The V1 yoga catalog was written from memory and given citations afterwards.
V1.4 inverted that: the BPHS chapters were located and read *before* Shadbala
and Ashtakavarga were written.

The difference is measurable:

| | Located witness | Total | Ratio |
|---|---|---|---|
| V1 yoga catalog (written from memory) | 5 | 110 | **5%** |
| V1.4 calculation modules (sourced first) | 6 | 8 | **75%** |

A test asserts the second ratio exceeds the first by at least five-fold, so
the discipline cannot quietly lapse.

### What the witness actually settled

* **Uchcha Bala.** BPHS 27.1 gives a worked example — the Sun at Pisces
  12°15′ against a debilitation point of Libra 10°, yielding 50.75 virupas.
  The implementation reproduces that number exactly, and the test asserts it.
* **Dig Bala.** BPHS 27.7 gives two more: Saturn on the 7th cusp scores one
  rupa, on the ascendant zero. Both reproduced.
* **Naisargika Bala.** BPHS 27.14 states the formula outright — one rupa
  divided by seven, multiplied by 1 to 7 for Saturn through the Sun.
* **Shadbala requirements.** BPHS 27.32-33: 390, 360, 300, 420, 390, 330, 300
  virupas.
* **Ashtakavarga.** BPHS 66.43-45 gives the Sun's bindu table house by house.
  Transposed, it matches the standard table exactly.

### Findings the witness produced

1. **An internal contradiction in the witness.** BPHS 27.4.5 says Ojhayugma
   Bala is "a quarter of Rupa (i.e. 15 Virupas)"; Santhanam's note beneath it
   says 35. Fifteen is a quarter of sixty and thirty-five is not, so the note
   is an error and the verse is followed. Registered as
   `OJHAYUGMA_VIRUPA_VALUE`, resolved on arithmetic rather than preference.
2. **An epoch the text does not fix.** Varsha and Masa Bala need an Ahargana
   counted from an epoch of creation, which the witness supplies through a
   printed speculum belonging to that edition rather than through the text.
   Both are computed from a stated proxy epoch and flagged
   `is_approximation`. Registered as `AHARGANA_EPOCH_UNFIXED`.
3. **Six Ashtakavarga tables located but unread.** The chapter contains all
   eight, but the OCR of six is damaged. Those are implemented from the
   standard tables and NOT claimed as verified — though the classical totals
   (48/49/39/54/56/52/39, sarva 337) provide an independent arithmetic check
   that all seven pass.

### Where the modules stand

| Module | Status |
|---|---|
| `shadbala/sthana_bala` | IMPLEMENTATION_MATCHED |
| `shadbala/dig_bala` | IMPLEMENTATION_MATCHED |
| `shadbala/naisargika_bala` | IMPLEMENTATION_MATCHED |
| `shadbala/kala_bala` | RULE_INTERPRETATION_MAPPED — two subcomponents rest on unfixed conventions |
| `shadbala/drik_bala` | RULE_INTERPRETATION_MAPPED |
| `ashtakavarga/bhinna` | RULE_INTERPRETATION_MAPPED — one table verified of seven |
| `ashtakavarga/reductions` | UNVERIFIED — implemented, not applied by default |
| `houses/sripati` | UNVERIFIED — no witness located for any house system |

**Still nothing is TRADITION_VALIDATED.** The BPHS witness is a translation.

---

## 23A. Mars regression held **[V1.4]**

Part 24 required confirming the V1.3 Mars migration remained stable. It did:
the accuracy fixtures and the eight regression charts are unchanged, and no
Mars classification moved. `tools/mars_migration_report.py` reproduces the
finding — zero classification changes across all 74 fixture cases.

---

## 24A. What V1.4 added, and its limits **[V1.4]**

| Module | State | Limit |
|---|---|---|
| Shadbala | Six components, each separately sourced and scored | Varsha/Masa on an assumed epoch; Tribhaga on assumed 06:00/18:00 sunrise |
| Ashtakavarga | Bhinna and Sarva, totals verified by invariant | Six of seven tables not read against the witness; reductions unverified and off by default |
| Bhava Chalit | Sripati, Porphyry, equal and Placidus; Rashi/Bhava strictly separate | No house system has a located witness |
| Birth-time sensitivity | Windows of ±1/2/5/10 minutes, crossings bisected to the second | Does not model the ephemeris's own error, only the clock's |
| Transits | Positions, relationships, ingresses, stations, exact conjunctions | No Gochara rules — they need sources first |
| TimingContext | Natal, dasha and transit in one object | No synthesis, by instruction |

**A finding worth quoting.** The documented regression chart is NOT stable in
time: its D60 Lagna changes 39 seconds after the stated birth time, and the
Lagna nakshatra, Lagna pada and D9 Lagna all change at +2m 34s. Any reading of
that chart which leans on the D9 Lagna is resting on the clock.

---

## 25A. Remaining limitations after V1.4 **[V1.4]**

| Area | State |
|---|---|
| **The ~100 BPHS yoga citations** | **Still unchecked.** A named edition now exists to check them against; the chapter-by-chapter audit has not been done. This is the largest single piece of outstanding provenance work. |
| Sanskrit BPHS | Not obtained. Caps everything resting on BPHS below TRADITION_VALIDATED. |
| Phaladeepika, Saravali, Jataka Parijata | Not obtained |
| Rahu/Ketu | 1.11′ — the limiting astronomical body |
| Kala Bala | Two subcomponents on assumed conventions |
| Ashtakavarga reductions | Unverified, off by default |
| House systems | None source-validated |
| Sunrise/sunset | Not computed, which limits Tribhaga Bala and the hora |
| Gochara | Not implemented — needs sources |
| Interpretation | Not implemented, by instruction |

---

## 26A. Recommended V1.5 scope **[V1.4]**

1. **Audit the ~100 BPHS yoga citations against the Santhanam witness.** Now
   possible and now the biggest gap. Expect some to be wrong.
2. **A Sanskrit BPHS**, without which nothing can be TRADITION_VALIDATED.
3. **Sunrise and sunset**, which unblocks Tribhaga Bala and the hora and is
   small work.
4. **Read the six remaining Ashtakavarga tables** against the witness.
5. **Sources for the house systems**, which would let Bhava Chalit move above
   UNVERIFIED.
6. Only then: Gochara rules, and the interpretation layer.

---

## 27A. V1.4 was wrong about the Sanskrit sources, exactly as V1.3 was about BPHS **[V1.5]**

V1.4 recorded, with its reasons stated:

> "GRETIL does not hold the text; the Devanagari scans on public archives did
> not yield usable OCR."

Both halves were true. The conclusion drawn from them was not. V1.4 had
searched archive.org and GRETIL, and had never tried sanskritdocuments.org,
which has held a proofread ITRANS transliteration of all 97 chapters of
Bṛhat Parāśara Horā Śāstra, split across eleven files, the whole time.
Phaladīpikā and Jātaka Pārijāta are there too. All three were retrieved on
the first attempt in V1.5.

This is the third consecutive release in which a claim about a TEXT was
really a claim about a SEARCH:

| release | claim | overturned by |
|---|---|---|
| V1.3 | BPHS unavailable | V1.4, in minutes |
| V1.4 | Sanskrit BPHS, Phaladīpikā, Jātaka Pārijāta unavailable | V1.5, in minutes |

The engine now carries `RESOLVED_UNAVAILABLE_WORKS`, which keeps each
overturned claim beside what turned out to be true, rather than deleting it.
A test asserts the three works are absent from `UNAVAILABLE_WORKS` and
present in the resolved table.

**What is still not read: Sārāvalī.** A 1928 Sanskrit edition was located and
downloaded in full — 17.3 MB, checksum recorded. It is an image scan with no
text layer and no OCR tool is available in this environment, so not one verse
of it has been read. It stays in `UNAVAILABLE_WORKS` with `why_unavailable`
beginning "RETRIEVED BUT NOT READ", because having the file is not having the
text, and that distinction is the entire subject of the table.

---

## 28A. The citations were wrong, and the doctrine mostly was not **[V1.5]**

The V1.5 audit checked all 110 shipped rules against the new Sanskrit
witnesses. The result splits more sharply than expected.

**The combinations are real.** Nearly every rule describes something a text
does contain. The Raja Yoga doctrine the engine generates — kendra lord in
relationship with trikoṇa lord, by conjunction, mutual aspect or exchange —
is squarely at BPHS 34.11-12, which enumerates exactly those three modes, and
is glossed at 41.28 with "the kendra is Viṣṇu's place and the trikoṇa
Lakṣmī's".

**The citations pointing at them were not.** Of the legacy chapter numbers
checked, exactly one was right:

| rule group | cited | actually at | chapter cited is really |
|---|---|---|---|
| Raja Yogas | BPHS ch.36 | 34.11-15, 41.28 | vividha-yoga |
| Dhana Yogas | BPHS ch.40 | not located | rāja-sambandha-yoga |
| Moon yogas | BPHS ch.34 | 37.7 | yogakāraka |
| Kemadruma | BPHS ch.34.6 | 37.11 | yogakāraka |
| Adhi Yoga | BPHS ch.36 | 37.5 | vividha-yoga |
| Gajakesari | BPHS ch.34 | 36.3 | yogakāraka |
| Vipareeta triad | BPHS ch.36 | **not in BPHS at all** — Phaladīpikā 6.57 | vividha-yoga |
| Neecha Bhanga | BPHS ch.75 | not located | pañca-mahāpuruṣa |
| Pañca Mahāpuruṣa | BPHS ch.75 | **75.1-2 — correct** | pañca-mahāpuruṣa |

The single correct citation is worth as much as the wrong ones: it shows the
citations were not uniformly fabricated, they were unchecked, and an
unchecked citation is sometimes right. That is exactly why checking was
necessary rather than merely tidy.

### A new status: read and absent

`UNVERIFIED` had been covering two very different states — "nobody looked"
and "we looked and it is not there". V1.5 separates them. Five rule groups
had their cited chapter read in full and do not appear in it; their evidence
now begins `NEGATIVE RESULT` and names what the chapter actually contains.
BPHS ch.41, the wealth chapter, gives specific grahas in specific houses in
their own signs, not relationships among house lords.

---

## 29A. Eleven divergences, none of them fixed in place **[V1.5]**

Forty-three of the 110 shipped rules were found to do something the located
text does not, described by eleven evidence records. Not one was edited.

The clearest case is the Pañca Mahāpuruṣa group. BPHS 75.1 requires the graha
to be `balibhiḥ`; Jātaka Pārijāta 59 requires `baliṣṭhāḥ`. Both mean strong,
both state it as a condition of formation alongside the dignity and the
kendra, and the two works agree while disagreeing about the dignity set —
Jātaka Pārijāta includes moolatrikona and BPHS does not. The engine has never
tested strength at all.

That correction was only possible because V1.4 built Shadbala. Reading
`balibhiḥ` as "Shadbala at or above the BPHS 27.32 requirement" is an engine
convention and is flagged as one in the review queue, but it is at least a
measure from the same tradition, out of the same work.

The most consequential is BPHS 34.15, which states an exception the engine
has never applied: when the kendra and trikoṇa lords **also own dusthanas**,
their relationship alone does not give the yoga. On most ascendants at least
one participating lord owns the 6th, 8th or 12th, so this suppresses a great
many Raja Yogas. It does not fire on the Jaipur 1988 regression chart — Meena
lagna puts no dusthana lordship on any participating graha — which is why it
needed a constructed Mesha chart to demonstrate.

### Why a separate profile rather than a fix

Part 2 forbids editing yoga logic silently. Beyond obedience there is a
practical reason: a diff nobody re-runs is not a record. Both readings ship,
and the difference is observable on any chart by changing one flag.

```
  --rule-profile parashari           # the V1.1 reading, unchanged
  --rule-profile parashari_textual   # the located reading
```

**No V1.4 result changed in this release.** The textual profile is *smaller*
than the default — 108 rules against 110 — which inverts the intuitive
expectation that more sourcing means more rules. Every correction narrowed
something.

---

## 30A. Where two witnesses disagree, V1.5 ships both **[V1.5]**

Four new conflicts are registered rather than resolved. Two are worth naming.

**Lakṣmī Yoga** has two definitions under one name. BPHS 36.27 wants the 9th
lord dignified with a strong Lagna lord. Phaladīpikā 6.21 wants the 9th lord
**and Venus**, both dignified and both angular or trinal. These are not
variant phrasings; they fire on different charts. Both ship as separate
rules, and the V1.1 rule — which matched neither — is retained, marked, and
excluded from strict synthesis.

**The putrakāraka.** Reading BPHS ch.32 to source the domain model's kārakas
produced an unwelcome result. The sthira kārakas of 32.18-21 are a list of
*relatives*, not the popular list of significations, and 32.20 reads
`guroḥ pitāmahaḥ śukrāt patiḥ putraḥ śanaiścarāt` — from Jupiter the paternal
grandfather, from Venus the spouse, from **Saturn** the son. Modern practice
makes Jupiter the putrakāraka near-universally.

The engine carries both and prefers neither. Two cautions are recorded with
the conflict: the sthira kārakas may be intended for a narrower purpose than
the general significators they are being compared against, and the exemplar
behind this transliteration is unidentified, which is exactly the condition
under which a single-word variant is most likely. A Sanskritist with two
printed editions settles this quickly; this engine should not settle it at
all.

### The strict profile grew from 1 rule to 41, and the gate did not change

`strict_profile_eligible` has not been touched since V1.3. The entire growth
is the arrival of evidence. What is admitted is instructive: the three Sun
yogas, Adhi Yoga, Amala Yoga, the three corrected Moon yogas, and 33 corrected
Raja Yogas.

What is *refused* is more instructive. Every rule whose formation condition
two witnesses state differently is excluded — Gajakesari, the Mahāpuruṣa
yogas, Lakṣmī, Kemadruma — however carefully each was sourced. Good sourcing
is not settled sourcing, and a profile that claims settled provenance cannot
contain a rule whose definition is in dispute without hiding the dispute.

---

## 31A. The laundering bug, caught in the synthesis layer **[V1.5]**

The first working build of the synthesis engine reported 17 active life
domains under the **strict** profile — the same 17 as under experimental.

The cause is worth recording because it is subtle and would have been easy to
ship. Strict synthesis was admitting any factor whose own evidence was
sound, and a Shadbala measurement of the 10th lord is about as well sourced
as anything in this engine: computed from BPHS ch.27, a located witness whose
worked examples the code reproduces exactly.

None of which is evidence that **the 10th house signifies career**. That is
the step carrying the prediction, and no text has been located for it.

The fix changed the question the gate asks, from "is this factor sourced" to
"is the link from this factor to this domain sourced". Under that criterion
the surviving factors are kāraka attributions with a locator — BPHS 32.20
says `śukrāt patiḥ`, and that sentence *is* the link from Venus to marriage —
and nothing else. Strict synthesis can now speak about four domains out of
seventeen, and is silent on the rest.

This is the same shape of finding as the V1.3 strict rule profile containing
one rule, and it arrived the same way: by asking what the evidence actually
supports rather than what the chain looks like end to end.

---

## 32A. Remaining limitations after V1.5 **[V1.5]**

| area | state |
|---|---|
| Tradition-validated rules | **Still zero.** Needs human review closed. |
| Printed exemplar of the Sanskrit BPHS | **Unidentified** — the whole audit's locators depend on this witness's chapter numbering |
| Sārāvalī | Retrieved, not readable, not read |
| BPHS 34.15 reading | Wide reading implemented; may over-cancel. In the review queue. |
| `balibhiḥ` as Shadbala | Engine convention, not textual |
| Domain house mappings | **0 of 17** have a located witness |
| Kāraka attributions | 5 of 30 located; one of those contradicts modern practice |
| Gochara | Still no located source; strict synthesis admits no transit evidence at all |
| Ashtakavarga thresholds | Engine conventions; ch.66 gives tables, not thresholds |
| Dhana Yogas | Read and absent from the cited chapter; Sārāvalī unsearched |
| Neecha Bhanga | Not located anywhere; `nīcabhaṅga` does not occur in the Sanskrit BPHS |
| Synthesis weights | Every one is SOFTWARE_HEURISTIC and arbitrary |
| Empirical validation | **None, of anything.** No output has been tested against an outcome. |

---

## 33A. Recommended V1.6 scope **[V1.5]**

1. **Identify the exemplar** behind the sanskritdocuments BPHS, or obtain a
   named printed edition. Every locator in the V1.5 audit rests on it, and
   chapter numbering is precisely what varies between editions.
2. **Audit BPHS chapters 12-20** (bhāva-phala) against the domain house
   mappings. Currently 0 of 17 have any witness, and this is now the largest
   single gap — it is what keeps strict synthesis silent on 13 domains.
3. **OCR the Sārāvalī scan.** It is the obvious home for the Dhana Yogas and
   the Neecha Bhanga rules, neither of which is in BPHS.
4. **Settle the putrakāraka question** with a second printed edition.
5. **Sunrise and sunset** — still unblocked work, still blocking Tribhaga
   Bala and the hora, still small.
6. **Human review of the 21 blocking queued items.** Nothing reaches
   TRADITION_VALIDATED until this happens, and no amount of further coding
   substitutes for it.
7. Only then: Gochara with sources, and a verbalisation layer over the
   structured synthesis output.

---

## 34A. The domain layer had no sources, and now mostly does **[V1.6]**

V1.5 shipped 17 life domains and recorded that **not one** house mapping
carried a located witness. That was the release's largest remaining gap and
it had a visible consequence: strict synthesis could speak about four
domains, because the only source-qualified factor→domain links anywhere in
the engine were kāraka attributions.

The fix was not more code. It was reading BPHS chapter 11.

`bhāvaviveka` is the house-signification chapter: twelve verses, one per
bhāva, each naming what is to be examined from it. It had been sitting in a
file the engine already held and had been checksummed since V1.5. Most of
the mappings turn out to be attested, and several in a single word:

| verse | term | domain |
|---|---|---|
| 11.11 | `vṛtti` — livelihood | CAREER, 10th |
| 11.8 | `jāyā` — wife | MARRIAGE, 7th |
| 11.6 | `putra` — children | CHILDREN, 5th |
| 11.12 | `āya` — income | FINANCE, 11th |
| 11.3 | `kuṭumba` — family | FAMILY, 2nd |
| 11.4 | `bhrātṛ` — brother | SIBLINGS, 3rd |
| 11.5 | `kṣetra`, `gṛha` — land, house | PROPERTY, 4th |
| 11.9 | `āyus` — longevity | LONGEVITY, 8th |
| 11.10 | `dharma` | SPIRITUALITY, 9th |
| 11.8 | `vāṇijya` — trade | BUSINESS, 7th |

Three further chapters closed the rest. BPHS 21.2 makes the **strength** of
the tenth lord bear on occupation, which is the verse that had been missing
under the V1.5 Shadbala factor. BPHS 23.11 gives `deśād deśāntaraṃ gataḥ`
for an afflicted twelfth, which sources FOREIGN_RESIDENCE. BPHS 24 works the
house-lord doctrine out lord by lord, which is what makes HOUSE_LORD a
distinct evidence type rather than a restatement of the house.

| | V1.5 | V1.6 |
|---|---|---|
| House mappings with a witness | 0 of 17 | 38 of 43 |
| Kārakas with a witness | 5 of 30 | 7 of 24 |
| Domains strict synthesis admits | 4 | **16 of 17** |
| Varga mappings with a witness | 0 | **0** |

### Two mappings were wrong, not merely uncited

**EDUCATION was at the 4th house.** BPHS 11.6 puts `vidyā` — learning — and
`buddhi` — the intellect — at the **fifth**, alongside children. The fourth,
at 11.5, gets vehicles, relatives, the mother's comfort, treasure, land and
house, and no learning at all. The engine had followed a modern convention
the text does not support. The primary house moved; the fourth is retained as
an unsourced secondary because the modern association is widespread.

**TRAVEL had the 12th.** BPHS gives travel three houses — `prayāṇa` from the
3rd, `adhva-prayāṇa` from the 7th, `tīrthayātrā` from the 9th — and the 12th
gets expenditure and news of enemies. The 12th was dropped and the 7th added.

**RELATIONSHIPS turned out to have no basis at all.** BPHS 11.8 gives the
seventh `jāyā`, the wife, specifically. No witness supports a general
relationships domain distinct from marriage. It is retained, marked as
having no located house witness, and is the one domain of seventeen that
strict synthesis still declines.

### The gap that did not close

Every varga mapping is still unsourced. BPHS chapters 6 and 7 give the
ṣoḍaśavarga and how to compute them, and no passage in any witness this
engine holds assigns a divisional chart to a life area. D10-for-career and
D9-for-marriage remain modern convention, however universal — and they
therefore cannot carry a strict prediction.

---

## 35A. V1.5 was wrong about the putrakāraka, and the correction is to a reading **[V1.6]**

V1.5 read BPHS 32.18-21, found `putraḥ śanaiścarāt` — the son from Saturn —
and registered a conflict between BPHS and the near-universal modern
attribution of the putrakāraka to Jupiter. It recorded two cautions and
declined to resolve it, which was the right posture given what it had read.

What it had read was incomplete. Four verses later, at **32.22-24**, the same
chapter introduces a **third** kāraka scheme in its own words —
`kārakān vakṣye kheṭa-bhāva-vaśāt`, kārakas by graha and bhāva together — and
says `devejyāt pañcamāt putro`: the son from Jupiter, in the fifth. The same
passage gives `mandād aṣṭamato mṛtyuḥ`, death from Saturn in the eighth,
which is also where modern practice puts Saturn.

So the disagreement was never between BPHS and modernity. It is between two
schemes inside one chapter, and the second agrees with modern practice.

Both readings still ship. Jupiter is source-qualified for CHILDREN on 32.23;
Saturn is retained with its verse, carries the conflict, and cannot enter
strict synthesis. The conflict record was rewritten rather than deleted,
because the shape of the error is the useful part: V1.5 stopped reading at
the end of a list that had a second list after it.

### A related defect the new tests caught

Three V1.5 witnesses recorded the checksum of a file that does not contain
the chapter they cite — chapters 32, 41 and 75 all pointed at the wrong one
of the eleven retrieved files. Anyone verifying those locators would have
been sent to the wrong place, and a citation whose checksum points elsewhere
is worse than one with no checksum because it looks verified.

Checksums are now **derived** from the chapter rather than copied, and a test
cross-checks every BPHS witness against the chapter-to-file table.

---

## 36A. The laundering gate held, and the answer changed **[V1.6]**

V1.5 introduced the rule that a factor may carry a strict prediction only if
the link FROM that factor TO that domain has a witness — not merely if the
factor itself is well computed. The example it was built around: a Shadbala
figure for the tenth lord is computed from BPHS ch.27 and reproduces that
chapter's worked examples exactly, and none of that is evidence that the
tenth house has anything to do with career.

**The gate is unchanged in V1.6.** `qualifies_for_strict` asks the same
question. What changed is that BPHS 11.11 and 21.2 now answer it for career,
so the Shadbala factor is admitted — on evidence, not by relaxation.

It still refuses inside sourced domains, which is the part worth checking:
CAREER's tenth house passes and its **sixth** does not, because BPHS 11.7
gives the sixth enemies and wounds and its relevance to employment is a
modern reading. Both refusals and admissions happen in the same domain in the
same run.

### Transits are still refused, for a narrower reason

V1.5 excluded transit evidence from strict synthesis because the house→domain
mapping had no witness. That reason is gone. The exclusion is not.

"The tenth house signifies livelihood" and "a graha transiting the tenth
house affects livelihood" are different claims, and only the first has been
located. The second is Gochara, for which this engine has no source — V1.4
put Gochara, Vedha and Sade Sati out of scope for exactly this reason.
Finding the house mappings narrowed what is missing without supplying it.

---

## 37A. Interpretation, and what a renderer is not allowed to do **[V1.6]**

V1.6 adds `engine/interpretation/`, the first layer in the project that
produces prose. It consumes a serialised `PredictionSnapshot` and produces an
`InterpretationDocument`.

**No model, no network, no randomness.** Template substitution over a key and
a dictionary of already-computed values. A test asserts the package imports
nothing that could reach a network or a model, and a second asserts
byte-identical output for identical input.

The renderer is prevented from deciding anything **by construction**: its
only input is a dict. It is never shown a chart, so it cannot judge a yoga,
a strength, an activation or a confidence — every one of those was settled
upstream. A test round-trips the snapshot through JSON before rendering, so
nothing but plain data remains.

### The three things the prose layer must get right

**Contradictions survive.** Where supporting and challenging evidence both
exist, both lists are rendered and a sentence says neither cancels the other.
Summary mode, which prints no lists, uses a different sentence rather than
promising lists it will not show.

**Silence is an answer, and there are three kinds.** A domain with no
admissible evidence, a domain with a natal indication and nothing activating
it, and — the one that matters — a domain where transits are touching the
right houses and the chart carries no indication for them to activate. That
third case is where a naive engine announces a finding, and it renders as an
explicit refusal rather than as nothing at all.

**No peak is invented.** The window-with-peak sentence is used only when the
engine identified one by bisection. Dates render to month and year: the
boundaries are computed to the second, and printing that would imply a
precision about the *event* that the arithmetic only has about the sky.

### The disclaimer problem, for the third release running

V1.4 had a test fail on its own note containing the word "score". V1.5 had
one fail on a field named `confidence_is_not_probability`. V1.6 had two fail
on the health scope limit, which contains the word "diagnosis" in order to
promise there is none.

The pattern is now explicit in the tests: a scan for forbidden language must
know which sentences are disclaimers, because a disclaimer has to use the
word it excludes. The fix each time is to scan the *claims* rather than the
document — and the temptation each time is to weaken the disclaimer instead.

---

## 38A. Remaining limitations after V1.6 **[V1.6]**

| area | state |
|---|---|
| Tradition-validated anything | **Still zero.** Needs human review closed. |
| Printed exemplar of the Sanskrit BPHS | **Still unidentified.** V1.6 checked the repository's own pages; no bibliographic metadata exists. Every locator in two audits depends on this witness's numbering. |
| Varga → domain mappings | **0 of 11 sourced.** The largest remaining domain gap. |
| Kāraka attributions | 7 of 24 located. Sun-for-authority, Jupiter-for-wealth, Mercury-for-intellect are in no scheme read. |
| RELATIONSHIPS domain | No located house witness; excluded from strict |
| Gochara | Still no source; strict admits no transit evidence |
| Sārāvalī | Retrieved, image-only, still unread |
| Dhana Yogas, Neecha Bhanga | Read and absent from cited chapters; Sārāvalī unsearched |
| Synthesis weights | Every one SOFTWARE_HEURISTIC and arbitrary |
| Interpretation templates | English only; architecture supports more, none written |
| Empirical validation | **None, of anything.** No output tested against an outcome. |

---

## 39A. Recommended V1.7 scope **[V1.6]**

1. **Identify the BPHS exemplar,** or collate a sample of chapters against a
   named printed edition. Raised in V1.5, unresolved in V1.6, and now
   load-bearing for two audits.
2. **Source the varga assignments,** or mark them permanently conventional.
   Sārāvalī and Phaladīpikā are the places to look, and Phaladīpikā is
   already in hand and only partly read.
3. **OCR the Sārāvalī scan.** Still the obvious home for the Dhana Yogas and
   the Neecha Bhanga rules, neither of which is in BPHS.
4. **Human review of the 21 blocking queue items.** Nothing reaches
   TRADITION_VALIDATED until this happens, and no further coding substitutes.
5. **A second locale,** to prove the localisation architecture on something
   other than English. The keys and grammar hooks exist and are untested
   against a language that conjoins differently.
6. **Sunrise and sunset** — unblocked since V1.4, still blocking Tribhaga
   Bala and the hora, still small.
7. Only then: Gochara with sources.

---

## 40A. The engine boundary, drawn structurally **[V1.7]**

V1.7 is the release where a user interface, a chart renderer and a report
writer arrive at once. Each of those is a place where a second astrology
engine grows — not deliberately, but through one reasonable-looking line at a
time. A template needs a house number and works it out with
`(sign - lagna) % 12`. A report needs a dignity and asks a chart object for
one. The second implementation then drifts from the first, silently, because
nothing compares them.

So the rule is enforced by the import graph rather than by review:

| Package | May import `engine` | Why |
|---|---|---|
| `app/services` | yes | it is the adapter layer; this is its job |
| `app/benchmark.py` | yes | it times engine entry points directly |
| `app/visual` | **no** | |
| `app/report` | **no** | |
| `app/ui` | **no** | |

`tests/test_app_boundary.py` parses every file under `app/` and fails on a
violation. Parsing catches `from engine…`; it does not catch a renderer handed
a live object by a caller and reaching through it. So a second set of tests
passes every snapshot through `json.dumps`/`json.loads` before rendering. A
dict cannot be asked a question that was not written down, and a renderer that
had come to depend on a method call fails on the round trip rather than in
production.

`ChartVisualModel` is frozen for the same reason as `NatalResult`: Part 30 asks
that a settings change never mutate a computed object, and freezing is how that
becomes structural rather than a convention.

**One derivation deliberately did not move into the renderer.** A varga
placement's house is `(sign - varga_lagna) % 12 + 1`. That is three lines, and
it is `engine.features.varga_features.varga_house_of`, called from the service
layer. Two implementations of one rule eventually disagree, and the one in the
renderer would be the one nobody tests.

---

## 41A. What the transit scan cost, and what it cost to fix **[V1.7]**

The first end-to-end run of the application took 58 seconds, of which 55 were
one call: `get_transit_events_between` over a one-year window for five grahas.

The cause was visible once measured. `_position_at` asks for ONE graha from
`compute_transit_positions`, which computes all nine. Guru, Śani, Rāhu and
Ketu share a 48-hour scan step, so they sample exactly the same instants — the
engine was computing each of those charts four times over, and bisection then
re-sampled instants the coarse pass had already visited.

The fix is a bounded cache in `engine/transits/query.py`, keyed on the instant
and the two settings that affect it. `compute_transit_positions` is a pure
function, so two calls with the same key must return the same values and
caching cannot change an answer. The cache is local to the scanner rather than
on the calculator, so nothing outside it can be handed a dict another caller
might mutate.

**58s → 3.6s, with byte-identical events.** `app/benchmark.py` records the
measurement and `--benchmark` reproduces it.

This is the one change V1.7 made inside the engine for a performance reason,
and it was made where the waste was — not by reducing the scan, which would
have made timing windows looser.

---

## 42A. Hindi found four things English could not **[V1.7]**

V1.6 put the list conjunctions in the locale and considered the localisation
architecture done. It was not, and an English-only build could not show it.
The first rendered Hindi document showed all four in one page:

**1. `{ordinal} house` is not a pattern Hindi has.** `सातवें भाव` puts a
distinct ordinal WORD before the noun, in the oblique form the following
postposition needs. A locale that could only supply a suffix could not write it
at all. The ordinals and the assembly pattern both moved into the locale.

**2. `sentence()` was doing two English-specific things unconditionally.**
Devanagari has no letter case, so capitalising its first character is a no-op;
its terminator is the danda `।`, and appending a full stop to a Hindi sentence
is wrong punctuation. Both are now locale properties.

**3. A dozen words reached the templates as ARGUMENTS, not templates.**
"debilitated", "combust", "mahadasha", "standard", "its sign". They are
substituted INTO a sentence and so never appear in a template file, which is
exactly why they were missed. A fully translated template set still produced
Hindi with English nouns inside it. `TemplateSet.term` is now the one place
they are looked up — Part 25's "centralised terminology mapping".

**4. The document headings were English literals in Python** while
`section.*` keys for them existed and were never used. Five more keys were
added (`heading.*`) and `format_interpretation` now reloads the template set
from `document.language`, so a document read back from a file formats in its
own language with nothing else supplied.

Every one is fixed in the engine rather than worked around in the templates.
The completeness test is what stops a third locale inheriting any of them.

**What Hindi did not change:** the findings. `LanguageNeutralityTest` asserts
that the two languages report identical activation and confidence for every
domain and share no sentence — if Hindi fell back to English for any key, the
two documents would share one.

---

## 43A. A PDF that refuses, and why that is the right answer **[V1.7]**

The PDF writer produces a professional English report: A4, measured
proportional text, tables that break at row boundaries and repeat their
headers, running heads, page numbers, vector kundlis, and a source appendix.
It uses the base-14 faces, which are not embedded, so a report is ~50 KB and
opens on a machine with no fonts installed.

**Those faces are Latin.** Devanagari has no glyphs in them, and there are two
reasons a Hindi PDF is not a matter of embedding a font:

1. The font would have to be embedded, which this build does not do.
2. Devanagari needs **shaping**. `कार्य` reorders the i-matra before the
   consonant it follows in the encoding, forms a conjunct, and raises the ra
   into a reph. Correct code points in encoding order still render visibly
   wrong.

So `render_pdf` scans the document and **refuses** above a threshold, naming
the alternative. A page of question marks reads as a broken program rather
than as an unsupported feature, and a reader who asked for Hindi would get a
document that looks wrong without being told why.

The alternative is complete, not a consolation: `app/report/html_report.py`
renders the same `ReportDocument` as one self-contained HTML file — inline
SVG charts, inlined stylesheet, no script, no font request, no network. The
browser supplies both the font and the shaping. It prints.

**What is lost in the English PDF and not in the HTML:** the Sanskrit
diacritics. `Bṛhat Pārāśara Horā Śāstra` becomes `Brhat Parasara Hora Sastra`,
because WinAnsi has glyphs for almost none of them and `B?hat P?r???ara` is
worse. `śa` and `ṣa` are different sounds and this spelling cannot tell them
apart; that is a real cost, recorded here rather than hidden. HTML keeps them.

---

## 44A. The disclaimer trap, fourth release running **[V1.7]**

V1.4 failed a test on the word "score", inside its own note about scores. V1.5
failed on a field NAME, `confidence_is_not_probability`. V1.6 failed on the
health scope limit, which contains "diagnosis" in order to disclaim one. V1.7
failed on three sentences that exist to say the engine emits no probability.

Four releases, four times, same shape. The tempting fix each time is to soften
the disclaimer, and each time that would have made the product worse to pass a
test.

The fix that has now been generalised: **scan claims, not documents.** A claim
is a body paragraph, a bullet, a heading or a table cell. A limit is a callout
or a small-print note, and a limit is obliged to name the thing it rules out.
`tests/test_golden_report.py::_claim_text` is the one implementation, and
`test_the_limits_do_name_what_they_rule_out` is its other half — a release that
weakened the callouts to pass the first test fails the second.

---

## 45A. Remaining limitations after V1.7 **[V1.7]**

**Astronomy and calculation** — unchanged from V1.6. No new calculation was
added; the one engine change was a cache.

**Sources**
- D2 → WEALTH is attested at BPHS 7.1 and not implemented. Adding a factor
  changes synthesis output and V1.7 is not for that.
- The five newly qualified varga mappings rest on ONE witness each.
  `SECOND_WITNESS_CHECKED` is claimed for none of them.
- Gochara has located witnesses and no matching implementation. Strict still
  refuses transits. See `GOCHARA_AUDIT.md`.
- Sārāvalī: still `RETRIEVED BUT NOT READ`, for the second release running.
- The BPHS printed exemplar is still `UNRESOLVED`.
- **Nothing is TRADITION_VALIDATED.** Four releases of source work have not
  produced a single confirmed reading, and will not: that requires a scholar,
  not a search.

**Application**
- One consultation at a time. The server holds a single `Application`.
- North Indian chart style only. South and East Indian are named and refused.
- Hindi PDF is refused (see 43A). Hindi HTML is complete.
- Two locales. A third would be the real test of the V1.7 grammar work; Hindi
  and English happen to share numeral direction and both read left to right.
- No authentication on the local server. It binds to loopback, which is the
  protection; a shared machine is not addressed.
- Saved consultations are files. No index, no search, no versioned history.

**What V1.7 deliberately did not do**
- No LLM, no generative component, no ML weights, no probabilities.
- No remedies, gemstones or mantras.
- No birth-time rectification. The precision input WIDENS uncertainty and has
  no setting that narrows it.
- No astrology formula was changed to make a UI requirement easier.

---

## 46A. Recommended V1.8 scope **[V1.7]**

**1. Gochara, properly, in the order the text states it.** Reference frame,
then the favourable-house lists (PD 26.2), then vedha (PD 26.3-8), then the
daśā-lord condition (PD 20.34-35). Shipping any one of the first three without
the next produces a rule no text states. The fourth would let strict admit a
transit for the first time.

**2. D2 → WEALTH, and the other located-but-unimplemented mappings.** The
smallest honest piece of source-driven growth available.

**3. A third locale, chosen to break something.** Tamil or Bengali would test a
different script through the same grammar block. An RTL language would test the
chart layout, which currently assumes left-to-right label stacking.

**4. Devanagari PDF.** Embedded TrueType with Identity-H, plus a Devanagari
shaper. Substantial — reordering, conjuncts, reph, rakar — and the honest
precondition for saying the report system is language-complete.

**5. Second witnesses.** Every qualified mapping in the domain layer rests on
one. Sārāvalī is the obvious second reader for the yoga corpus and has been
retrieved twice without being read.

**6. South Indian chart style.** The model already carries everything a second
layout needs; this is a renderer, and proving that is worth doing while the
boundary is fresh.

---

## 47A. The refusal that finally became a rule **[V1.8]**

Three releases refused transit evidence in strict synthesis, each for a
better reason than the last, and the sequence is worth keeping because
it shows what "a located source is not permission" costs to honour.

| Release | Refused because |
|---|---|
| V1.5 | The house→domain mapping had no witness |
| V1.6 | Found the mappings; "the 10th signifies career" and "a graha transiting the 10th affects career" are different claims |
| V1.7 | Located the second claim — Phaladīpikā 26 and 20.34-35 — and refused anyway: a located source is a specification the implementation does not meet |
| V1.8 | Implemented it |

**And the refusal survived.** Phaladīpikā 26 is now completely
implemented — all seven grahas, all 36 vedha pairs, both reciprocal
exemptions — and still cannot reach a life area. It judges a transit in
the Chandra's frame and never names a bhāva; this engine's bhāva
significations are stated from the Lagna in BPHS 11. There is no sourced
path from one to the other, and manufacturing one would have been the
laundering the eligibility ladder exists to prevent.

Only 20.34-35 gets through, because `yadbhāvago gocarato vilagnāt` names
the bhāva and the rest of the chain — the daśā-lord condition, the natal
strength condition — is stated in the same verse.

So the larger and more famous passage narrowed what the engine claims,
and the smaller one widened it. That is the correct direction for
sources to push a result, and it is the fourth consecutive release in
which reading a text produced a more restrictive engine rather than a
more confident one.

---

## 48A. What the second edition caught **[V1.8]**

V1.7 located the gochara verses. V1.8 had to READ them, and reading
them exposed something locating them could not.

Phaladīpikā 26.6 pairs Mercury's six favourable houses with six vedha
houses positionally. The ITRANS witness ends the list with `prApti`, the
11th — **which would pair the 11th with itself**, asserting that
Mercury's transit of the 11th is obstructed by a graha standing where
Mercury already is.

That reading is self-refuting. It can be rejected on internal grounds
before any second witness is consulted, and the arithmetic that rejects
it is now a test: `test_no_graha_is_ever_its_own_vedha_house` runs over
every row of every table.

A 1950 printed edition then supplied the correct reading (the 12th) and
a second, smaller repair at 26.8. Both editions are Phaladīpikā, so this
settles a READING and is not independent support for the doctrine — a
distinction `WitnessAgreement.SAME_WORK_SECOND_EDITION` now carries,
because collapsing it either way would have misreported the evidence.

The general lesson is the uncomfortable one: a source can be located,
checksummed, cited and **wrong**, and the only thing that catches it is
reading it closely enough to notice the arithmetic does not close.

---

## 49A. A completeness test measures what it was pointed at **[V1.8]**

V1.7 reported Hindi localisation complete, with a test asserting that no
English sentence survived into a Hindi document. Both were true.

The first Hindi PDF V1.8 produced had **1,232 English strings in it**.

The completeness test covered the engine's 78 interpretation keys. The
report's own chrome — every section heading, every table column, the
cover, the callout titles — is generated in `app/report/builder.py`,
which sits below the architecture boundary and was therefore outside the
engine's template system entirely. Nobody had pointed a test at it
because nobody had noticed it was a separate system.

It was found by building the PDF and looking at it.

The fix is 144 strings in `templates/<lang>/report.json`, loaded by
`app/report/strings.py` without importing the engine, with a
completeness check per language and no silent fallback. The lesson is
not about Hindi: **a green completeness test is evidence about the thing
it enumerates, and nothing else.**

---

## 50A. The optimisation that had to prove it changed nothing **[V1.8]**

Synthesis was 4.97 s and 98% of the pipeline. Profiling first — as Part
12 requires and as is easy to skip — put 97,000 calls and 64 million
cosines inside one function, `vsop87_xyz`.

Caching it was obvious. Proving it safe was the work:

- The cache sits **upstream of every methodology choice**. Ayanamsha,
  node mode, house system and rule profile are all applied later, so
  there is no profile for a value to leak into — the one failure Part 15
  names. A test casts the same moment under two ayanamshas, shares every
  cached series value, and asserts the positions differ.
- Flattening the series data for speed required preserving iteration
  order **exactly**, because floating-point addition is not associative
  and a reordering would move the last digits of every position in the
  engine and every accuracy figure with them.
  `_vsop87_xyz_reference` is retained as a test oracle and the two are
  asserted bit-identical.

A second measurement saved more work than it created: restricting the
transit scan to the five watched bodies was measured at **1.03×** before
being implemented. The watched bodies are the expensive ones.

The same discipline applied to the shaper. A per-lookup first-glyph
filter took Hindi PDF generation from 23 s to 1.4 s, and a test shapes
every golden word with the filter disabled and asserts an identical
glyph stream — because a filter that is not a pure optimisation drops
substitutions rather than raising.

---

## 51A. Remaining limitations after V1.8 **[V1.8]**

1. **Nothing is TRADITION_VALIDATED.** Four releases of source work have
   not produced one, and none will: the step needs a scholar with the
   texts, not another search.
2. **Sārāvalī is held and unread.** 17.3 MB, checksummed since V1.5, an
   image scan with no text layer. It is the second witness for the Moon
   yogas, the Pañca Mahāpuruṣa yogas and gochara, and it is blocked on a
   person rather than a tool.
3. **43 rules diverge from their located text.** Recorded, not edited.
4. **Six varga mappings are unqualified**, one contradicted by the verse
   that assigns the divisions.
5. **Phaladīpikā 26.9-24 is unimplemented**, so a transit verdict is
   favourable-or-obstructed rather than a per-house effect.
6. **`balānvita` is operationalised with a different work's threshold.**
   Recorded in two fields, queued for review.
7. **No third locale.** The mechanism is complete and proven for two.
8. **Chart captions remain English in a Hindi report.** The chrome and
   the findings are translated; the caption line from the visual
   builder is not.
9. **The first Hindi PDF in a process costs ~4 s** while the OpenType
   caches warm.
10. **The East Indian chart is refused**, by name.

---

## 52A. Recommended V1.9 scope **[V1.8]**

1. **A reader for Sārāvalī.** Not a tool. Everything else on this list
   is smaller than the questions one afternoon with those page images
   would close.
2. **Phaladīpikā 26.9-24**, which would make a transit verdict specific
   rather than binary — and which needs a decision about how to hold
   sixteen verses of effects without becoming a second astrology engine.
3. **A third locale**, chosen to break something. Tamil would test
   whether the OpenType layer is genuinely script-neutral, since its
   split vowel signs decompose in a way Devanagari's do not.
4. **Chart-label localisation**, the last English in a Hindi document.
5. **The `balānvita` question**, and the other 23 in the review queue.
6. **Second witnesses**, which is item 1 again from a different angle.
