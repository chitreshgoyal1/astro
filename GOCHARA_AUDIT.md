# Gochara audit (V1.7 Part 28)

**The question Part 28 asks.** The transit mathematics is implemented and
externally benchmarked. What is missing is interpretive authority: by what
rule, stated where, does a transit mean anything?

**The answer.** Two located passages, and neither of them supports the rule
this engine implements. Strict synthesis still refuses transit evidence — for
a narrower and much better documented reason than before.

---

## 1. What V1.6 said, and why it was half right

V1.6's `_gated_transit_evidence` returns nothing in strict, with the note that
*"Gochara has no witness"*.

That was the wrong half of a true statement. Gochara has witnesses; this
engine had not looked for them. What it does not have is a witness for
**"a graha occupying the Nth house from the natal Lagna activates the
domain associated with that house"**, which is the rule the transit layer
actually applies.

---

## 2. What was located

### Phaladīpikā 26, `gocaraphala`

**Witness** `PD_SA_26.1-17_GOCHARAPHALA`, Sanskrit (ITRANS),
sanskritdocuments.org `phaladIpika.itx`, sha256 `6da22e78…81bc`.

The first verse settles the reference frame outright:

> `sarveṣu lagneṣv api satsu candralagnaṃ pradhānaṃ khalu gocareṣu |`
> `tasmāt tadṛkṣād api vartamānagrahendracāraiḥ kathayet phalāni ||1||`

*Although all the lagnas exist, in transits it is the Moon's sign that is
primary; therefore from that sign one should declare the results by the
movements of the current grahas.*

This is explicit textual authority for counting transits **from the natal
Moon**, and for preferring it to the Lagna. The engine computes both
`house_from_natal_lagna` and `house_from_natal_moon` and has never said which
is primary.

**26.2** gives the favourable houses per graha, counted from the Moon.
**26.3-8** make every one of them conditional on **vedha** — obstruction by a
graha standing in a specified counter-house. **26.9 onward** give the effect of
each graha in each of the twelve.

### Phaladīpikā 20.34-37

**Witness** `PD_SA_20.34-37_DASHESHA_GOCHARA`, same file.

> `yadbhāvago gocarato vilagnāt daśeśvaraḥ svoccasuhṛdgṛhasthaḥ |`
> `tadbhāvapuṣṭiṃ kurute tadānīṃ balānvitaścejjanane 'pi tasya ||34||`

*Whichever bhāva, counted from the lagna, the **lord of the running daśā**
reaches in transit — being in its own exaltation or a friend's house — it
nourishes that bhāva at that time, provided it was also strong at birth.*

**20.35** gives the inverse: if that lord was weak at birth, or is combust,
debilitated or in an enemy's house, whichever bhāva it reaches by transit it
destroys.

This is transit counted **from the Lagna**, and it is the closest thing in any
located text to the hierarchy V1.5 built:

- the transiting graha is not any graha — it is the **running daśā lord**;
- its effect is conditioned on its **natal** strength;
- the transit modulates a bhāva, it does not originate anything.

**Natal → Daśā → Transit, stated in a text.** V1.5 built that hierarchy as a
software convention and said so. It turns out a classical text states it.
That is a finding about the engine's *design*, not a validation of its
*implementation* — see below.

### BPHS chapter 66

Already registered as `BPHS_66_ASHTAKAVARGA`. Its transit framework is the
ashtakavarga one: a graha transiting a sign in which it has few bindus gives
unfavourable results. This is a third, independent method, and the engine
implements the bindu arithmetic without applying it to transits.

---

## 3. What the engine actually does

`engine/synthesis/engine.py::_gated_transit_evidence` produces evidence of four
kinds:

| Explanation key | What it records |
|---|---|
| `over_natal_house` | graha occupies the Nth house from the natal Lagna |
| `over_house_from_natal_moon` | graha occupies the Nth house from the natal Moon |
| `conjunct_natal_point` | transiting graha shares a sign with a natal body |
| `graha_drishti_to_natal_point` | transiting graha aspects a natal body |

Against the located passages:

| Located rule | Engine | Gap |
|---|---|---|
| The Moon is the primary frame (PD 26.1) | Computes both, prefers neither | Not applied |
| Favourable houses per graha (PD 26.2) | No list; any house counts | **Not implemented** |
| Vedha cancels a favourable transit (PD 26.3-8) | No vedha check at all | **Not implemented** |
| Per-graha per-house effects (PD 26.9+) | Not used | Not implemented |
| The transiting graha must be the daśā lord (PD 20.34) | Any graha | **Not implemented** |
| Its natal strength conditions the effect (PD 20.34-35) | Not checked | **Not implemented** |
| Ashtakavarga bindus in the transited sign (BPHS 66) | Bindus computed, not applied to transit | Not implemented |

**Every located rule is more specific than what the engine applies.** A rule
that fires on *any* graha in *any* house is not a weaker version of
Phaladīpikā 26 — it is a different rule, and a strictly more permissive one.

---

## 4. The decision

**Strict synthesis continues to refuse transit evidence**, and the refusal is
enforced in `_gated_transit_evidence` rather than left to callers.

This is deliberate, and Part 28 states the rule it follows:

> Do not make strict synthesis use a transit interpretation unless the
> rule/profile qualifies.

It does not qualify. A located source is not permission; it is a specification
the implementation does not meet. Treating "we found a text about gochara" as
grounds to admit the engine's own looser rule would be exactly the laundering
the V1.5 eligibility ladder exists to prevent.

**What changed is the reason, not the behaviour.** V1.6 refused because it
believed no witness existed. V1.7 refuses because the witnesses that exist
describe a rule with a favourable-house list, a vedha check and a daśā-lord
condition, none of which the engine computes.

`tests/test_source_audit_v17.py::test_strict_synthesis_still_refuses_transit_evidence`
pins that, and `PD_26_GOCHARA.notes` says it in the registry itself so that a
reader browsing witnesses is not left to assume otherwise.

---

## 5. Recommended V1.8 scope for this track

In the order the text puts them, which is also the order of increasing risk:

1. **Record the reference frame.** PD 26.1 makes the Moon primary. This is
   a one-line methodology statement, not a calculation, and it can ship
   without changing any result.
2. **Implement the favourable-house lists (PD 26.2).** Per graha, counted
   from the Moon. Deterministic, testable against the verse, and it makes
   the engine's transit evidence *narrower* rather than wider.
3. **Implement vedha (PD 26.3-8).** This is what makes the lists conditional.
   Shipping 2 without 3 would produce a rule the text does not state, which
   is the error this audit found.
4. **Implement the daśā-lord condition (PD 20.34-35).** The largest change
   and the most interesting one: it would let strict admit a transit for the
   first time, on the only rule any located text conditions properly.
5. **Second witness for each.** Sārāvalī has a gochara chapter and has still
   not been read. See `SOURCE_VALIDATION.md`.

Until at least 2, 3 and 4 are done and matched, strict must keep refusing.

---

*Everything above is TEXTUAL SOURCE LOCATED. Nothing here is
TRADITION/SOURCE VALIDATED, and the engine's own transit rule is neither: it
is a SOFTWARE SYNTHESIS HEURISTIC, which is how it is labelled in every record
that carries it.*
