# Bhāva Chalit — Design Document

**Status:** DESIGN ONLY. Nothing in this document is implemented.
**Target:** V1.4 at the earliest, and only after the source-validation work in
`SOURCE_VALIDATION.md` has advanced.
**Version:** V1.3, 27 September 2026

---

## 0. Why this is a design document and not code

The V1.3 brief asked for a design rather than an implementation, and that is
the right call for a reason worth stating plainly.

Bhāva Chalit is not a display option. It changes **which house a graha is in**,
and every yoga rule in this engine is expressed in terms of houses. Shipping it
before the rules have textual provenance would mean changing the answers of a
hundred rules whose correct formulation is not yet established — moving two
unknowns at once.

There is a second reason. The house systems below are not variants of one
calculation; they answer different questions about what a "house" is. Choosing
between them without a textual basis would be exactly the kind of silent
tradition-picking the source layer exists to prevent.

---

## 1. The two representations must coexist

**Whole-sign Rāśi houses stay the default and stay available.** Bhāva Chalit is
an additional representation, never a replacement.

| | Rāśi chart (whole sign) | Bhāva Chalit |
|---|---|---|
| House boundary | The rashi boundary | A computed cusp |
| House 1 | The whole rashi the Lagna falls in | An arc centred on or beginning at the Lagna degree |
| A graha's house | Determined by its rashi alone | Determined by its longitude against cusps |
| Lordship | Sign-based | Sign-based (see §5) |
| Sensitivity to birth time | Low — only the Lagna's rashi matters | High — a few minutes can move a graha between bhāvas |

A graha can sit in the 10th rashi and the 9th bhāva. Both statements are true
in their own frame, and the engine must be able to say both without implying
they disagree.

**The failure to avoid:** silently replacing one with the other, so a user
comparing output against another program cannot tell which model produced it.

---

## 2. Bhāva Madhya and the cusp question

The central modelling decision, and the one the traditions actually differ on:
**is the Lagna degree the START of the first house, or its MIDPOINT?**

| Model | Lagna degree is | House 1 spans |
|---|---|---|
| **Bhāva Madhya (midpoint)** | the *madhya*, the centre | Lagna − half, to Lagna + half |
| **Cusp-start (Porphyry-like)** | the *ārambha*, the beginning | Lagna, to the next cusp |

The Indian tradition predominantly treats the Lagna degree as the **madhya**,
the most sensitive point of the first bhāva, with the bhāva extending either
side of it — the *sandhi* (junction) falling midway between adjacent madhyas.
That is the model this design assumes as its default, and it is precisely the
assumption a source-validation pass must confirm before any code is written.

### Sandhi

Under the madhya model, the junction between bhāva *n* and bhāva *n+1* is the
midpoint between their madhyas. A graha near a sandhi is in neither bhāva
cleanly — which interacts directly with the existing uncertainty machinery
(§7).

---

## 3. Candidate house systems

Each is a distinct claim about how the ecliptic is divided, not a refinement of
the others.

### 3.1 Equal from the Lagna (Samā)

Cusps at Lagna + *n* × 30°. Bhāva madhyas are the cusps; sandhis 15° either
side. Trivial to compute, defined at every latitude.

### 3.2 Sripati

The classical Indian quadrant system. The Lagna–MC quadrant is trisected, and
intermediate cusps are obtained by interpolation between the angular cusps.
Houses are unequal; the four angles are exact.

### 3.3 Porphyry

Simple trisection of each quadrant in ecliptic longitude. Sripati is
essentially Porphyry with a different interpolation of the intermediate cusps,
so the two agree at the angles and differ between them.

### 3.4 Placidus

Time-based division of diurnal and nocturnal semi-arcs. **Undefined above the
polar circles** and numerically unstable approaching them. If offered at all it
must fail loudly at high latitude rather than return a number — the same
discipline `engine/location.py` already applies to unknown birthplaces.

### 3.5 Koch, Campanus, Regiomontanus

Western systems. Out of scope unless a user need appears; listing them here
only to record that they were considered and set aside.

**Recommendation:** implement **Equal-from-Lagna** and **Sripati** first. The
first is unambiguous and always defined; the second is the one with an actual
Indian textual tradition behind it. Placidus only if asked for, and only with a
high-latitude guard.

---

## 4. Proposed architecture

Mirrors the existing convention/profile pattern, so nothing is a special case.

```
engine/houses/
    models.py       BhavaCusp, BhavaChart, HouseSystemProfile
    systems.py      equal_from_lagna(), sripati(), porphyry(), placidus()
    profiles.py     named, source-tagged house-system profiles
    report.py       the BHAVA CHALIT report section
```

```python
@dataclass(frozen=True)
class BhavaCusp:
    house: int
    madhya: float          # bhāva madhya, degrees
    start: float           # sandhi below
    end: float             # sandhi above
    sign: int              # rashi the madhya falls in
    sign_lord: str

@dataclass
class BhavaChart:
    system: str                       # "equal_from_lagna" | "sripati" | …
    profile_id: str                   # names the tradition, per engine.sources
    cusps: dict[int, BhavaCusp]
    placements: dict[str, int]        # graha -> bhāva number
    rashi_placements: dict[str, int]  # graha -> whole-sign house, for comparison
    divergences: list[str]            # grahas whose bhāva differs from rashi
    near_sandhi: list[str]            # grahas within the uncertainty envelope
```

`divergences` is the field that matters. A consumer should be able to ask "what
does this representation change?" and get a direct answer instead of diffing
two dictionaries.

### Selection

```bash
python3 main.py --consultation chart.json --house-system sripati
```

Default remains `whole_sign`. The active system is recorded in
`calculation_settings` and in `methodology`, exactly as the rule and Varga
profiles already are.

---

## 5. Lordship stays sign-based

**Recommendation: yes, lordship remains sign-based.**

House lordship derives from the *rashi* on a house, and the rashi is a property
of the zodiac rather than of the house-division scheme. Under Bhāva Chalit a
bhāva may span parts of two rashis, which raises the question of which one
rules it. The proposal:

* the lord of a bhāva is the lord of the rashi its **madhya** falls in;
* where the bhāva spans two rashis, the second is recorded as
  `secondary_sign` and reported, never silently dropped.

This keeps `engine/features/lordships.py` working unchanged for the Rāśi chart
and adds a parallel, explicitly-labelled lordship view for the bhāva chart.

**This is a modelling choice, not a sourced one.** It needs textual support
before it ships.

---

## 6. Effect on the Yoga rules — the hard part

This is the part that could go badly wrong, so it should be decided before any
code is written.

Every rule in `engine/rules/` speaks of houses. Under Bhāva Chalit some of
those house numbers change. Three possible policies:

| Policy | Behaviour | Assessment |
|---|---|---|
| **A. Rules stay on the Rāśi chart** | Bhāva Chalit is reporting only | Safest. Rules keep the meaning they were written with. |
| **B. Rules follow the active house system** | Yoga results change with `--house-system` | Most flexible, most dangerous — silently alters a hundred unvalidated rules. |
| **C. Per-rule declaration** | Each rule declares its frame | Most correct, most work. |

**Recommendation: A for V1.4, with C as the eventual target.**

The reason is the one the source audit exposed. The engine's rules are
overwhelmingly UNVERIFIED; their intended reference frame has not been
established from any text. Until a rule's frame is *sourced*, changing the
frame it is evaluated in would be changing an answer on the strength of an
assumption.

Policy C fits the existing architecture directly: `RuleEvidence` already has a
`reference_frame` field, currently recording Lagna/Moon/Sun. It would extend to
record *rāśi houses* against *bhāva houses* as the sourcing work establishes
which each rule means.

---

## 7. Interaction with numerical uncertainty

Bhāva Chalit **amplifies** the boundary problem `engine/uncertainty.py` exists
for, because it adds a second family of boundaries that move with birth time.

* A sandhi is a boundary like a rashi edge, and a graha near one is unresolved
  in the same sense.
* Unlike rashi boundaries, sandhi positions depend on the **birth time and
  latitude**, so birth-time uncertainty propagates into house placement. A
  four-minute error moves the Lagna by roughly a degree, which can move a graha
  across a sandhi.
* Therefore `BhavaChart.near_sandhi` must be populated using the same measured
  envelopes, **plus** a birth-time uncertainty term the engine does not
  currently model at all.

Recording a new input: **birth-time confidence**. Without it the engine cannot
honestly say whether a bhāva placement is resolved.

---

## 8. Effect on ChartSnapshot

Backward-compatible addition, `schema_version` → **1.2.0**:

```json
"houses": { ...unchanged whole-sign houses... },

"bhava_chalit": {
    "system": "sripati",
    "profile_id": "sripati_classical",
    "source_validation_status": "UNVERIFIED",
    "cusps": { "1": { "madhya": 345.78, "start": 330.4, "end": 1.2 } },
    "placements": { "Surya": 6 },
    "divergences": ["Shani: rashi house 10, bhava 9"],
    "near_sandhi": ["Guru"]
}
```

Rules:

* `houses` keeps its present meaning — whole-sign — permanently. A consumer
  reading `houses` must never find bhāva numbers there.
* `bhava_chalit` is absent entirely when the feature is off, rather than
  present and empty.
* `methodology.house_system` records the active system.

---

## 9. What must be settled before implementation

| # | Question | Blocks |
|---|---|---|
| 1 | Is the Lagna degree the bhāva **madhya** or the bhāva **start**? | Everything |
| 2 | Which house system, with which textual witness? | System choice |
| 3 | Is bhāva lordship the madhya's rashi lord? | §5 |
| 4 | Do the shipped yoga rules mean rāśi houses or bhāva houses? | §6 — and this cannot be answered until the rules themselves are sourced |
| 5 | How is birth-time confidence supplied and propagated? | §7 |

Questions 1–4 are **textual**, not technical. They belong in the review queue
in `engine/sources/registry.py` alongside the rest, and they cannot be settled
by the implementing model.

---

## 10. Recommended sequence

1. Source-validate the reference frames of the existing yoga rules. *(V1.4)*
2. Add birth-time confidence as an input, and propagate it through
   `engine/uncertainty.py`. *(independent, useful on its own)*
3. Implement `engine/houses/` with Equal-from-Lagna and Sripati, reporting
   only, under Policy A. *(V1.4)*
4. Add `bhava_chalit` to the snapshot at schema 1.2.0.
5. Move to Policy C per rule, only as each rule's frame becomes sourced.

Step 1 gates step 5. That ordering is the whole point of doing the design
first.
