# Methodology

What this engine computes, on whose authority, and how far that
authority has actually been checked.

Written for a reader who knows Jyotiṣa and wants to know what the
software is claiming. It is not a tutorial and it is not an argument for
any position; where the sources disagree, this document says so rather
than choosing.

---

## 1. Five kinds of statement, kept apart

Every output of this engine is exactly one of these, and the separation
is structural — different objects, different fields, different gates.

| | What it is | Example |
|---|---|---|
| **ASTRONOMICAL FACT** | Where a body is | Guru at 4°17′ Vṛṣabha |
| **ASTROLOGICAL FEATURE** | A derived relationship | Guru in the 3rd, aspecting the 7th |
| **TEXTUAL RULE** | Something a located passage states | BPHS 11.8 gives the 7th `jāyā` |
| **SOFTWARE SYNTHESIS** | This engine's convention for combining them | Activation bands, evidence weights |
| **DETERMINISTIC INTERPRETATION** | A sentence produced by template substitution | "The 7th lord is strong and unafflicted." |

The first two are computed. The third is cited. The fourth is
**invented by this software** and labelled as such wherever it appears.
The fifth is a rendering of the fourth and adds nothing.

A reader who takes an activation band for a textual rule has been
misled; the vocabulary exists so that they cannot be.

---

## 2. Four kinds of evidence, also kept apart

| Claim | What it means here | Status in V1.8 |
|---|---|---|
| **COMPUTATIONALLY TESTED** | The code does what we told it to | 1,456 tests |
| **EXTERNALLY BENCHMARKED** | The numbers match an independent reference | Astronomy only, against Swiss Ephemeris |
| **TEXTUAL SOURCE LOCATED** | A specific passage in a specific edition exists and has been read | 47 witnesses, 39 at Sanskrit tier |
| **MULTI-WITNESS SUPPORTED** | An independent second **work** agrees | 1 rule |
| **TRADITION / SOURCE VALIDATED** | A scholar has confirmed the passage states this rule | **Nothing** |

**None is evidence for another.** A green test suite says nothing about
whether a verse was read correctly. An arcsecond-accurate Jupiter says
nothing about whether the tenth house signifies career.

Nothing in this build is TRADITION_VALIDATED, and four releases of
source work have not produced one. That step needs a human with the
texts, not another search.

---

## 3. Profiles

### Synthesis profiles

These decide how much evidence a conclusion may rest on.

| Profile | Admits | Behaviour |
|---|---|---|
| `strict` | Only rules that are source-qualified | Small, and often silent |
| `standard` | Documented methodology plus located sources | The default |
| `experimental` | Also explicitly unverified rules | Every result carries the profile |

**Strict is not "better strict"; it is narrower.** On the worked example
at 2026-09-27 it reports 16 of 17 life areas as non-inactive, admits one
divisional-chart confirmation where the standard profile admits three,
and produces its transit evidence from exactly one rule.

Silence under strict is a finding. It means the evidence did not reach
the bar — not that nothing is indicated.

### Rule profiles

| Profile | What it is |
|---|---|
| `parashari` | The full mainstream catalog. Most of it is UNVERIFIED. |
| `parashari_extended` | Plus variant readings held by later authorities |
| `parashari_textual` | The located readings substituted for the divergent ones |
| `parashari_vipareeta_strict` | The strict reading of Vipareeta Rāja Yoga |
| `parashari_strict` | Evidence-gated: only rules meeting a documented minimum |

`parashari_textual` exists because seven rule groups were found to
**diverge from the text** the audit located. Those rules were not
edited: the divergent reading stays in `parashari`, the located reading
ships as a separate rule, and both are visible. Silently correcting them
would have hidden the finding.

### Gochara profile

The transit rules are Phaladīpikā's, not BPHS's, and are labelled
`phaladipika_gochara` so that a reader who selected a strictly Pārāśarī
methodology can see that the transit judgement comes from a different
author.

---

## 4. The activation hierarchy

```
Natal promise  →  Daśā activation  →  Transit trigger
```

This is a **constraint, not an ordering**. A lower layer cannot supply
what a higher one lacks. A transit over the natal 10th in a chart with
no career indication produces transit *facts* and no career *evidence*.

The failure it prevents is the standard one in predictive software:
Saturn arrives on the 7th cusp, the engine finds a "marriage transit",
and a reader is told something about a chart that never indicated
marriage.

V1.5 built this hierarchy as a software convention and said so. V1.8
found that Phaladīpikā 20.34 states it — the transiting graha must be
the running daśā lord, and its effect is conditioned on its **natal**
strength. That is a finding about the design, not a validation of the
implementation, and the two are recorded separately.

---

## 5. Provenance, rung by rung

A rule climbs this ladder, and each rung needs its own evidence:

```
UNVERIFIED
  → TEXT_LOCATED              somebody says it is in BPHS 36
  → WITNESS_RECORDED          this edition, this chapter, this verse
  → TRANSLATION_CHECKED       a translation witness recorded too
  → RULE_INTERPRETATION_MAPPED  what the passage states, written out
  → IMPLEMENTATION_MATCHED    the code matches it, and a test says so
  → SECOND_WITNESS_CHECKED    an independent WORK agrees
  → VALIDATED_FOR_PROFILE     as far as this engine can take it
  → TRADITION_VALIDATED       a human has confirmed the reading
```

Two statuses are **off the ladder** — they are findings, not progress:

- `CONFLICTING_SOURCES` — reputable witnesses disagree and no reading
  has been adopted.
- `IMPLEMENTATION_DIVERGES` — a witness was located and read, and the
  software does not do what it says. This is the most informative status
  in the vocabulary and the least comfortable. 43 rules carry it.

The step people skip is between TEXT_LOCATED and WITNESS_RECORDED. "A
website says this is in BPHS 36" and "this edition, at chapter 36 verse
3, contains this" are different claims, and most astrology software
stops at the first.

---

## 6. What the sources actually support

### Houses and house lords

| Factor | Total | Source-qualified |
|---|---|---|
| House → domain | 43 | 38 |
| House lord → domain | 16 | 16 |
| Kāraka → domain | 24 | 6 |
| Varga → domain | 12 | 6 |

BPHS chapter 11 states the house significations as a list, which is why
that row is strong. The kāraka row is weak for a specific reason: BPHS
chapter 32 gives **three different kāraka schemes** and they do not
agree with each other.

### Divisional charts

BPHS 7.1-6, the `vargavivekādhyāya`, assigns a subject to each of the
sixteen divisions. It was located in V1.7 — one chapter after the
chapter V1.6 read and declared empty.

Locating it **convicted as much as it qualified**:

| Domain | Chart | The verse's word | Verdict |
|---|---|---|---|
| MARRIAGE | D9 | `kalatra` | Attested |
| CHILDREN | D7 | `putra-pautra` | Attested |
| EDUCATION | D24 | `vidyā` | Attested |
| SIBLINGS | D3 | `bhrātṛja-saukhya` | Attested |
| SPIRITUALITY | D20 | `upāsanā` | Attested |
| WEALTH | D2 | `sampad` | Attested — **added in V1.8** |
| CAREER | D10 | `mahat-phala` | Located, narrower |
| FAMILY | D12 | `pitṛ` | Located, wider |
| CAREER | D9 | — | Not in the verse |
| BUSINESS | D10 | — | Not in the verse |
| HEALTH | D6 | — | Not one of the sixteen |
| PROPERTY | D4 | `bhāgya` | **Contradicted** |

D10 for career is the case worth understanding. `daśamāṃśe mahatphalam`
is "the great fruit from the daśāṃśa". A translator renders it "power
(and position)" and glosses it "i.e. livelihood etc." in a footnote —
**the gloss is the translator's**. The verse does not use `vṛtti`, the
word BPHS 11.11 uses for livelihood when it assigns the tenth *house*.
So D10 is located for a subject *near* career and is not qualified for
career.

D4 for property is not merely unattested: BPHS 7.2 gives the
caturthāṃśa `bhāgya`, fortune. The modern reading appears to come from
the fourth **house**, which BPHS 11.5 does give `kṣetra` and `gṛha`. The
mapping ships, because removing it would silently change every chart,
and it ships labelled `CONTRADICTED`.

**One caveat on D2.** The horā maps the whole zodiac onto two rashis,
Karka and Siṃha, so its lagna lord is always Chandra or Sūrya and
neither can be exalted or debilitated there. D2 can therefore *confirm*
and can never *challenge*. That is a property of the division, it is
measured rather than assumed, and it is printed beside any conclusion
that rests on it.

### Transits

Phaladīpikā 26.1 settles the reference frame outright: *of all the
lagnas, in transits it is the Moon's sign that is primary.* 26.2 gives
each graha's favourable houses from it; 26.3-8 make every one of them
conditional on **vedha**, obstruction by a graha in a specified
counter-house.

All 36 vedha pairs are implemented, with both stated exemptions — the
Sun suffers no vedha from Saturn and the Moon none from Mercury, each
reciprocally. Rāhu and Ketu take the Sun's favourable houses (26.2,
`tigmāṃśuvad bhoginau`) and get **no vedha table**, because neither
witness gives them one and copying the Sun's row across would be an
invention.

**Chapter 26 is fully implemented and still cannot reach a life area.**
It judges a transit favourable or obstructed in the Moon's frame; it
does not say which affairs the transit bears on, and this engine's bhāva
significations are stated from the Lagna. There is no sourced path from
one to the other.

Phaladīpikā 20.34-35 is different. It names the bhāva —
`yadbhāvago gocarato vilagnāt` — and conditions the result on the
transiting graha being the running daśā lord and on its natal strength.
That is a complete chain, and it is the **only route by which a transit
reaches strict synthesis**, for the first time in this engine's history.

---

## 7. Where a number stands in for a word

Phaladīpikā 20.34 requires the daśā lord to be `balānvita`, endowed with
strength at birth. It names no measure.

This engine substitutes BPHS 27's own required-virūpa threshold —
Shadbala ratio ≥ 1.0 — and **records the substitution rather than
hiding it**. Every such judgement carries two separate fields: what the
text says, and what the software tested. The measure comes from a
different work than the rule, and that is stated in the record.

This is queued for human review. It is the kind of question that cannot
be settled by reading more code.

---

## 8. What is deliberately not implemented

Located and left out, with the reason:

| Passage | Subject | Why not |
|---|---|---|
| Phaladīpikā 26.9-24 | Per-graha per-house transit effects | Prose effects; paraphrasing sixteen verses would make a second astrology engine |
| Phaladīpikā 26.25 | Which third of a rashi a graha acts in | Would move event timing; deferred |
| Phaladīpikā 26.26-48 | Nakṣatra gochara, laṭṭā, sarvatobhadra | A separate transit system, not a refinement |
| Phaladīpikā 26.41 / BPHS 66 | Ashtakavarga applied to transits | A third method; two implemented halves are not an implemented rule |
| Phaladīpikā 20.36 | The Moon relative to the daśā lord | Produces no bhāva, so it could not reach a domain anyway |
| BPHS 7.1 | D16, D27, D30, D40, D45, D60 subjects | Several are not life areas |

Recording these is the point. An omission nobody wrote down is an
omission nobody can act on.

---

## 9. Known divergences and conflicts

12 conflicts are registered. Two are worth naming here.

**The Moon yogas.** Bṛhajjātaka 13.3 and BPHS 37.7 both exclude only
the Sun from counting as company for the Moon. This engine also excludes
Rāhu and Ketu. Two independent Sanskrit works say the same thing, so
this is not a gap in the evidence but a difference between the code and
the text. The rules are marked `IMPLEMENTATION_DIVERGES`, they were not
edited, and `*_textual` rules implement the located reading.

**A transmission variant.** The two Phaladīpikā editions this engine
holds disagree about two words in the vedha table. One reading is
*self-refuting* — it would pair the 11th house with itself — so it is
rejected on internal grounds before either edition's authority is
weighed. Both editions are the same work, so this settles a **reading**
and is not independent doctrinal support.

---

## 10. Sources held and not read

Sārāvalī is held in full: a 1928 Sanskrit edition, 17.3 MB, checksummed
since V1.5. It is an image scan with no text layer and **not one verse
of it has been read**.

That is not the same as unavailable, and V1.8 stopped calling it that.
It is `RETRIEVED_IMAGE_ONLY` / `TEXT_NOT_REVIEWED`, and what it is
blocked on is a person who reads Devanagari, not a search.

If OCR is ever run over it, the output is a **search index and not
evidence**. A passage found that way must be read on the page image
before any witness is registered from it. The reason is concrete: the
V1.8 gochara audit found a volunteer *transliteration* — far cleaner
input than OCR — corrupt in two places, one of which would have produced
a wrong vedha table.

---

## 11. Open questions for a human

24 items are queued. They are questions that cannot be answered by
reading more code, and resolving one by picking the reading that makes
the implementation correct would be laundering a guess.

A representative three:

- Does BJ 13.3's `sva` mean the 2nd house from the Moon? The engine
  reads it that way.
- Is BPHS 27's strength threshold an acceptable reading of
  Phaladīpikā's `balānvita`?
- Do Rāhu and Ketu cause vedha? The verses say `grahaiḥ` and do not
  enumerate. The engine says yes, as a named and defaulted decision.

---

## 12. The standing limits

- No LLM, no model, no fitted coefficient, no machine learning. Every
  decision in this engine is deterministic code a reader can follow.
- No probabilities. Activation and confidence are ordinal bands.
- No remedies, gemstones, mantras, or birth-time rectification.
- No medical, death or pregnancy claims.
- Swiss Ephemeris is used **only** as an external validation reference.
  No coefficient was ever fitted against it.
- Nothing is TRADITION_VALIDATED.
