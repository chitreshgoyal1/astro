# Varga → domain audit (V1.7 Parts 27, 29)

**What this document is.** An audit of the eleven divisional-chart-to-life-area
mappings the synthesis engine ships, against the one passage located in any
witness this engine holds that assigns subjects to the sixteen divisions.

**What it is not.** A defence of those mappings. Four of the eleven are not in
the passage, and one of the four is contradicted by it.

---

## 1. The finding

V1.6 reported, as its largest open gap:

> 0 of 11 varga→domain mappings are sourced. BPHS ch.6-7 give the ṣoḍaśavarga
> and how to compute them; no passage anywhere assigns a divisional chart to a
> life area. D10-for-career remains convention.

**That was wrong.** The passage is **BPHS chapter 7, `vargavivekādhyāya`,
verses 1-6**, and it does nothing else: eight verses assigning a subject to
each of the sixteen divisions and then closing with Garga's rule about the
ṣaṣṭyaṃśa lord.

It is in `par0110.itx` — a file this engine has held, checksummed, and cited
since V1.5, for chapters 6, 7, 9 and 10. V1.6 read chapter 6, found the
computations, and stopped.

### The pattern, for the third release running

| Release | Declared | Overturned by |
|---|---|---|
| V1.4 | Four works unavailable | V1.5 retrieved three |
| V1.5 | BPHS gives `putraḥ śanaiścarāt`, conflicting with practice | V1.6 found a second kāraka scheme four verses later at 32.22-24 |
| V1.6 | No passage assigns a varga to a life area | V1.7 found it one chapter on, in the same file |

The pattern is not that the sources are hard to find. It is that the search
stops at the first place the answer should have been, and the answer is a few
verses further. `RESOLVED_UNAVAILABLE_WORKS` records this at the scale of a
work; `engine/sources/editions.py` now records it at the scale of a chapter.

---

## 2. The passage

**Witness** `BPHS_SA_7.1-8_VARGAVIVEKA`, Sanskrit (ITRANS),
sanskritdocuments.org, `par0110.itx`,
sha256 `96f788c6…6838a`, retrieved 2026-09-27.

**Translation witness, recorded separately** `BPHS_EN_7.1-8_VARGAVIVEKA`,
Santhanam, Ranjan Publications, vol. 1, ch. 7, "USE OF THE 16 DIVISIONS".

Incipit: `atha ṣoḍaśavargeṣu vivekaṃ ca vadāmyaham …`

| Division | The verse's word | Literal subject |
|---|---|---|
| D1 (lagna) | `dehasya` | the body |
| D2 Horā | `sampadādikam` | wealth and the like |
| D3 Dreṣkāṇa | `bhrātṛjaṃ saukhyam` | happiness arising from brothers |
| D4 Caturthāṃśa | `bhāgyacintanam` | consideration of **fortune** |
| D7 Saptāṃśa | `putrapautrādikānām` | sons, grandsons and the rest |
| D9 Navāṃśa | `kalatrāṇām` | the spouse |
| D10 Daśāṃśa | `mahatphalam` | **"the great fruit"** |
| D12 Dvādaśāṃśa | `pitroḥ` | the parents |
| D16 Ṣoḍaśāṃśa | `sukhāsukhasya … vāhanānām` | comfort and discomfort of vehicles |
| D20 Viṃśāṃśa | `upāsanāyāḥ` | worship |
| D24 Caturviṃśāṃśa | `vidyāyāḥ` | learning |
| D27 Bhāṃśa | `balābalam` | strength and weakness |
| D30 Triṃśāṃśa | `riṣṭaphalam` | the fruit of affliction |
| D40 Khavedāṃśa | `śubhāśubham` | the auspicious and inauspicious |
| D45 Akṣavedāṃśa | `akhilam` | everything |
| D60 Ṣaṣṭyaṃśa | `akhilam` | everything |

Two entries are in bold because they are the ones modern practice reads
differently, and they are the whole reason this audit could not stop at
"the passage exists, so the mappings are sourced".

---

## 3. The engine's eleven, judged

| Domain | Chart | Verse's subject | Verdict | Status |
|---|---|---|---|---|
| MARRIAGE | D9 | `kalatra`, the spouse | **Attested** — same claim | `IMPLEMENTATION_MATCHED` |
| CHILDREN | D7 | `putra-pautra` | **Attested** | `IMPLEMENTATION_MATCHED` |
| EDUCATION | D24 | `vidyā` | **Attested** — the same word BPHS 11.6 puts in the 5th house | `IMPLEMENTATION_MATCHED` |
| SIBLINGS | D3 | `bhrātṛja-saukhya` | **Attested** | `IMPLEMENTATION_MATCHED` |
| SPIRITUALITY | D20 | `upāsanā` | **Attested** | `IMPLEMENTATION_MATCHED` |
| CAREER | D10 | `mahat-phala` | **Located, narrower claim** | `RULE_INTERPRETATION_MAPPED` |
| FAMILY | D12 | `pitṛ`, parents | **Located, wider claim** | `RULE_INTERPRETATION_MAPPED` |
| CAREER | D9 | D9 is the spouse | Not in the verse | `UNVERIFIED` |
| BUSINESS | D10 | `mahat-phala` | Not in the verse | `UNVERIFIED` |
| HEALTH | D6 | D6 is not one of the sixteen | Not in the verse, and not a classical division | `UNVERIFIED` |
| PROPERTY | D4 | `bhāgya`, fortune | **Contradicted** | `UNVERIFIED` |

**5 of 11 source-qualified. 7 of 11 located. 4 not in the passage at all.**

### D10 for career: what the verse does not say

`daśamāṃśe mahatphalam` is "the great fruit from the daśāṃśa". Santhanam
renders it "power (and position)" and adds, in a footnote, "i.e. livelihood
etc." — **the gloss is the translator's, not the verse's.** The verse does not
use `vṛtti`, the word BPHS 11.11 uses for livelihood when it assigns the tenth
*house*.

So D10 is located for a subject *near* career and is not qualified for career.
Strict synthesis declines it, and the standard profile keeps it as documented
convention.

### D4 for property: contradicted, not merely absent

BPHS 7.2 gives the caturthāṃśa `bhāgya`, fortune. It does not give it land or
house. The modern reading of D4 as the property chart appears to come from the
fourth **house**, which BPHS 11.5 does give `kṣetra` and `gṛha`; the division
and the house have been conflated somewhere later than either text.

This is classified differently from D6-for-health. D6 is *absent* from the
passage. D4 is *pointed elsewhere by it*. The mapping ships, because it is
universal practice and removing it would silently change every chart, and its
note says what the verse actually assigns. Part 27's classification:
**MODERN_CONVENTION, contradicted by the located witness.**

### What the passage says that the engine does not use

`horāyāṃ sampadādikam` — **D2 for wealth**. The engine has no D2→WEALTH
mapping at all. This is a sourced mapping the engine does not implement, and it
is recorded here rather than added: adding a factor changes synthesis output,
and V1.7 is a productization release. See §6.

---

## 4. What changed in the engine

**The gate, not the answer.** `varga_confirmation` asked `admits_chart`,
which tests whether the birth time DETERMINES a divisional chart. Nothing asked
whether the link between that chart and that domain has a located source.

V1.6 could not see this. No varga mapping was source-qualified then, so the
missing gate would have changed no result. The moment one qualified, the other
six needed a gate to keep out.

```python
if strict and not spec.qualifies_for_strict(FactorType.VARGA, chart):
    continue
```

That is the Part 7 laundering gate, applied to vargas. Measured on the Jaipur
1988 regression chart at 2026-09-27:

| Profile | Varga evidence admitted |
|---|---|
| strict, before | D10→CAREER, D10→BUSINESS, D7→CHILDREN |
| **strict, after** | **D7→CHILDREN only** |
| standard | D10→CAREER, D10→BUSINESS, D7→CHILDREN |

Strict became **stricter** as a result of finding a source. That is the
correct direction: the audit qualified five links and convicted six, and the
gate now enforces the difference.

---

## 5. Tests

`tests/test_source_audit_v17.py`

- `test_exactly_five_mappings_state_the_verse_s_own_subject`
- `test_a_nearby_subject_is_located_without_being_qualified`
- `test_d4_for_property_is_recorded_as_contradicted_not_merely_absent`
- `test_the_strict_gate_now_asks_the_source_question_of_vargas`
- `VargaGateBehaviourTest` — both profiles, through a real synthesis

`tests/test_synthesis.py::test_varga_mappings_match_the_verse_that_assigns_them`
replaces V1.6's `test_no_varga_mapping_is_source_qualified`. The old assertion
was a correct pin on an incorrect finding; the replacement pins each mapping to
exactly what the verse does and does not say, so widening one later fails.

`tests/test_domain_validation.py::test_varga_coverage_is_partial_and_says_which_part`
replaces `test_no_varga_mapping_anywhere_is_qualified` for the same reason.

---

## 6. What remains

| Open | Why it is still open |
|---|---|
| **D2 → WEALTH is sourced and unimplemented** | `horāyāṃ sampadādikam`. Adding a factor changes synthesis output, which V1.7 is not for. V1.8. |
| **D16, D27, D30, D40, D45, D60 have subjects and no engine mapping** | Vehicles, strength, affliction, and three "everything" charts. Several are not life areas at all. |
| **The five qualified mappings rest on one witness** | No second witness has been checked. `SECOND_WITNESS_CHECKED` is not claimed for any of them. |
| **No mapping is TRADITION_VALIDATED** | A passage has been found and read. No scholar has confirmed that the passage states the rule. |
| **The D4 conflation is undocumented in its history** | The audit established that D4-for-property is not in BPHS 7. It did not establish where it came from. |

---

*Every claim in this document is TEXTUAL SOURCE LOCATED at most. None is
TRADITION/SOURCE VALIDATED. Locating a passage and confirming a reading are
different acts, and only the first has been performed.*
