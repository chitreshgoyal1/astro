# RULE_AUDIT_V15.md

Rule-by-rule change log for the V1.5 corpus audit.

Generated from `engine/sources/registry.py` (version 1.5.0). Do not edit by hand — regenerate with `python3 tools/generate_rule_audit.py`.

## What this document is

V1.1 shipped ~110 yoga rules carrying citations like `BPHS ch.36`. Every one of those strings was written from memory by the implementing model. None had been checked against an edition, and V1.3 recorded that as the engine's largest outstanding trust gap.

V1.5 obtained Sanskrit witnesses for Bṛhat Parāśara Horā Śāstra, Phaladīpikā and Jātaka Pārijāta, and checked the corpus against them chapter by chapter. This is what that found.

## The headline

**The doctrine was mostly real. The citations were mostly wrong.**

Of the legacy citations checked, exactly one named the correct chapter: `BPHS ch.75` for the Pañca Mahāpuruṣa yogas. The Raja Yogas cited ch.36 and are at 34.11-15 and 41.28. The Dhana Yogas cited ch.40, which is the rāja-sambandha chapter; the wealth chapter is 41 and does not contain the rule the engine implements. The Moon yogas cited ch.34 and are at 37.7.

**43 of the 110 shipped rules were found to diverge from the text that was located**, described by 11 evidence records — combinatorially generated families such as the 36 Raja Yogas share one record because they share one source and one condition shape.

None was edited. Each keeps its V1.4 behaviour, is marked `IMPLEMENTATION_DIVERGES`, and has a corrected counterpart in the `parashari_textual` profile.

## Why nothing was silently corrected

Part 2 forbids editing yoga logic silently and Part 1 says that where witnesses disagree the answer is separate profiles. Both point the same way, and there is a practical reason beyond obedience: a diff nobody re-runs is not a record. Shipping the located reading beside the original means the difference is observable on any chart, by switching one flag.

```
  python3 main.py ... --rule-profile parashari          # V1.1 reading
  python3 main.py ... --rule-profile parashari_textual  # V1.5 reading
```

## Source acquisition

V1.4 recorded a Sanskrit BPHS, Phaladīpikā and Jātaka Pārijāta as unavailable. All three were retrieved on the first attempt in V1.5, from a repository neither earlier release had tried.

| work | V1.4 claim | what was actually true |
| --- | --- | --- |
| Bṛhat Parāśara Horā Śāstra (Sanskrit original) | 'GRETIL does not hold the text; the Devanagari scans on public archives did not yield usable OCR.' | Both halves were accurate and the conclusion drawn from them was not. V1.4 searched archive.org scans and GRETIL, and never tried sanskritdocuments.org, which has held a proofread ITRANS transliteration of all 97 chapters, split across eleven files, the whole time. It was retrieved on the first attempt. |
| Jātaka Pārijāta | 'No digital witness retrieved.' | Available as ITRANS from sanskritdocuments.org. Retrieved on the first attempt. |
| Phaladīpikā | 'No digital witness retrieved.' | Available as ITRANS from sanskritdocuments.org, and separately as several public-domain English translations on archive.org (V. Subrahmanya Sastri, 1st and 2nd editions). Retrieved on the first attempt. |

This is the third release running in which a previous release's conclusion about a TEXT turned out to be a conclusion about its own SEARCH. V1.3 said BPHS was unavailable; V1.4 found a translation in minutes and then said the Sanskrit was unavailable; V1.5 found the Sanskrit in minutes. The pattern is recorded in `RESOLVED_UNAVAILABLE_WORKS` rather than tidied away.

**Still not read: Sārāvalī.** A 1928 Sanskrit edition was located and downloaded in full. It is an image scan with no text layer and no OCR tool is available here, so not one verse has been read. It stays in `UNAVAILABLE_WORKS`, because having the file is not having the text — which is the distinction that table exists to make.

### Licensing

None of these texts is vendored. The sanskritdocuments.org files restrict themselves to personal study and research and forbid reposting; the Santhanam translation is in copyright. Under both, the engine stores the same thing: metadata, edition, locator, SHA-256, a short incipit for finding the verse, and paraphrase in the engine's own words. No running text appears anywhere in this repository or in any output it produces.

## Corpus status after the audit

| status | rules |
| --- | --- |
| `UNVERIFIED` | 54 |
| `IMPLEMENTATION_DIVERGES` | 43 |
| `RULE_INTERPRETATION_MAPPED` | 7 |
| `IMPLEMENTATION_MATCHED` | 3 |
| `VALIDATED_FOR_PROFILE` | 1 |
| `SECOND_WITNESS_CHECKED` | 1 |
| `CONFLICTING_SOURCES` | 1 |

`IMPLEMENTATION_DIVERGES` is not a worse state than `UNVERIFIED`. It is a better-understood one: an unverified rule might be right, and a diverging rule is known not to match the text it cites. The count going up is what a successful audit looks like.

**Nothing is `TRADITION_VALIDATED`,** and nothing can be until a human with the texts closes the review queue. 1 rule(s) reach `VALIDATED_FOR_PROFILE`, the highest status this engine can assert on its own.

## Changed rules

Each entry gives the fields Part 2 requires: the old software condition, the textual condition it was checked against, the difference, the new software condition, the source references, the affected regression charts, and the reason.

### `anapha`

| field | value |
| --- | --- |
| **rule_id** | `anapha` |
| **old software condition** | Any of the five tara grahas occupies the house at inclusive distance 12 from Chandra's house — the nodes excluded. |
| **textual / source condition** | Excluding the Sun, grahas situated in the 12th from the Moon constitute Anaphā. |
| **difference found** | The engine excludes Rahu and Ketu from counting as company for the Moon. Neither witness excludes anything but the Sun. Two independent Sanskrit works were read and both say the same thing, so this is not a gap in the evidence but a difference between the code and the text. |
| **new software condition** | implemented as `anapha_textual` in `parashari_textual`; the rule above is unchanged |
| **source refs** | `BJ_13.3_CANDRA_YOGAS` — Varāhamihira: Bṛhajjātaka BJ_13.03 (Oriental Books Reprint Corporation, 2nd edition, 1979 (GRETIL))<br>`BPHS_SA_37.7_CANDRA_YOGAS` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 37.7 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files)<br>`JP_83_CANDRA_YOGAS_QUOTING_HORA` — Vaidyanātha Dīkṣita: Jātaka Pārijāta Jātaka Pārijāta(SD) v.83 (sanskritdocuments.org ITRANS text) |
| **affected regression charts** | Default profile output unchanged on every regression chart; the corrected reading is in `parashari_textual` only. |
| **reason for change** | See BJ 13.3 and BPHS 37.7, the same rule in both. |
| **prediction eligibility** | `DISABLED` |

### `durudhara`

| field | value |
| --- | --- |
| **rule_id** | `durudhara` |
| **old software condition** | Both houses at inclusive distance 2 and 12 from Chandra are occupied by tara grahas — the nodes excluded. |
| **textual / source condition** | Excluding the Sun, grahas in BOTH the 2nd and the 12th from the Moon constitute Durudharā. |
| **difference found** | The engine excludes Rahu and Ketu from counting as company for the Moon. Neither witness excludes anything but the Sun. Two independent Sanskrit works were read and both say the same thing, so this is not a gap in the evidence but a difference between the code and the text. |
| **new software condition** | implemented as `durudhara_textual` in `parashari_textual`; the rule above is unchanged |
| **source refs** | `BJ_13.3_CANDRA_YOGAS` — Varāhamihira: Bṛhajjātaka BJ_13.03 (Oriental Books Reprint Corporation, 2nd edition, 1979 (GRETIL))<br>`BPHS_SA_37.7_CANDRA_YOGAS` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 37.7 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files)<br>`JP_83_CANDRA_YOGAS_QUOTING_HORA` — Vaidyanātha Dīkṣita: Jātaka Pārijāta Jātaka Pārijāta(SD) v.83 (sanskritdocuments.org ITRANS text) |
| **affected regression charts** | Default profile output unchanged on every regression chart; the corrected reading is in `parashari_textual` only. |
| **reason for change** | Spelling: the engine has 'durudhara', BJ has durudhurā and BPHS 37.7 duradharā. The witnesses do not agree with each other on the spelling either. Not a substantive difference. |
| **prediction eligibility** | `DISABLED` |

### `gajakesari`

| field | value |
| --- | --- |
| **rule_id** | `gajakesari` |
| **old software condition** | Guru occupies a kendra counted from Chandra. No dignity, combustion or benefic-association condition is applied. |
| **textual / source condition** | Jupiter in a kendra — from the Moon per JP 116, from the Lagna or the Moon per BPHS 36.3 — conjoined with or aspected by benefics (BPHS), and free of debilitation, combustion and, in BPHS, enemy signs. |
| **difference found** | The engine tests placement only. Both witnesses additionally require Jupiter to be free of debilitation and combustion, and BPHS 36.3 also of enemy signs and requires benefic association. Gajakesari is consequently reported far more often than either text would allow. |
| **new software condition** | implemented as `gajakesari_textual_bphs / gajakesari_textual_jataka_parijata` in `parashari_textual`; the rule above is unchanged |
| **source refs** | `BPHS_SA_36.3_GAJAKESARI` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 36.3 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files)<br>`JP_116_GAJAKESARI` — Vaidyanātha Dīkṣita: Jātaka Pārijāta Jātaka Pārijāta(SD) v.116 (sanskritdocuments.org ITRANS text) |
| **affected regression charts** | Default profile output unchanged on every regression chart; the corrected reading is in `parashari_textual` only. |
| **reason for change** | Legacy citation 'BPHS ch.34' was wrong; the passage is 36.3. |
| **prediction eligibility** | `DISABLED` |

### `kemadruma`

| field | value |
| --- | --- |
| **rule_id** | `kemadruma` |
| **old software condition** | No tara graha in the 2nd or 12th from Chandra; cancelled by any of four clauses, two of which no witness states and one of which BPHS 37.11 contradicts. |
| **textual / source condition** | BPHS 37.11: Kemadruma arises when no graha other than the Sun occupies the 1st, 2nd or 12th from the Moon, AND no graha other than the Moon occupies a kendra from the Lagna. BJ 13.3: not accepted when the Moon is in a kendra or conjoined with a graha; a further kendra/navāṃśa opinion is reported and rejected as ukti-prasiddhā na te. |
| **difference found** | Of the engine's four bhanga clauses: kendra-from-Lagna is supported by BPHS 37.11; conjunction with a graha is supported by BJ 13.3 and by BPHS's inclusion of the 1st house; a graha in a kendra from the MOON is stated by neither; and the Moon itself in a kendra from the Lagna is CONTRADICTED by BPHS 37.11, which excludes the Moon from the grahas that count (vinā candraṃ). The engine also excludes the nodes from the 2nd and 12th, as in the other Moon yogas. |
| **new software condition** | implemented as `kemadruma_textual` in `parashari_textual`; the rule above is unchanged |
| **source refs** | `BJ_13.3_CANDRA_YOGAS` — Varāhamihira: Bṛhajjātaka BJ_13.03 (Oriental Books Reprint Corporation, 2nd edition, 1979 (GRETIL))<br>`BPHS_SA_37.11_KEMADRUMA` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 37.11 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files)<br>`JP_83_CANDRA_YOGAS_QUOTING_HORA` — Vaidyanātha Dīkṣita: Jātaka Pārijāta Jātaka Pārijāta(SD) v.83 (sanskritdocuments.org ITRANS text) |
| **affected regression charts** | Default profile output unchanged on every regression chart; the corrected reading is in `parashari_textual` only. |
| **reason for change** | Kemadruma is the negative case of the preceding three yogas. Both witnesses give cancellations and the two sets do not coincide; BJ additionally records, and dismisses, a third set. |
| **prediction eligibility** | `DISABLED` |

### `mahapurusha_bhadra`

| field | value |
| --- | --- |
| **rule_id** | `mahapurusha_bhadra` |
| **old software condition** | Budha is in own sign, moolatrikona or exaltation AND occupies a kendra from the Lagna. Cancelled if combust. |
| **textual / source condition** | Budha in a kendra, in own sign or exaltation (Jātaka Pārijāta 59 adds moolatrikona), AND STRONG — balibhiḥ at BPHS 75.1, baliṣṭhāḥ at JP 59. |
| **difference found** | The strength requirement is missing. Both witnesses state it and they are otherwise independent, so this is the clearest single correctable finding of the V1.5 audit. The engine instead cancels on combustion, which neither witness mentions here. |
| **new software condition** | implemented as `mahapurusha_bhadra_textual` in `parashari_textual`; the rule above is unchanged |
| **source refs** | `BPHS_SA_75.1_MAHAPURUSHA` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 75.1-2 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files)<br>`JP_59_MAHAPURUSHA` — Vaidyanātha Dīkṣita: Jātaka Pārijāta Jātaka Pārijāta(SD) v.59 (sanskritdocuments.org ITRANS text) |
| **affected regression charts** | Default profile output unchanged on every regression chart; the corrected reading is in `parashari_textual` only. |
| **reason for change** | The legacy citation 'BPHS ch.75' is the ONLY one in the whole corpus that named the correct chapter. V1.3 recorded that these yogas are demonstrably absent from Bṛhajjātaka and guessed at Sārāvalī; the answer was BPHS all along. |
| **prediction eligibility** | `DISABLED` |

### `mahapurusha_hamsa`

| field | value |
| --- | --- |
| **rule_id** | `mahapurusha_hamsa` |
| **old software condition** | Guru is in own sign, moolatrikona or exaltation AND occupies a kendra from the Lagna. Cancelled if combust. |
| **textual / source condition** | Guru in a kendra, in own sign or exaltation (Jātaka Pārijāta 59 adds moolatrikona), AND STRONG — balibhiḥ at BPHS 75.1, baliṣṭhāḥ at JP 59. |
| **difference found** | The strength requirement is missing. Both witnesses state it and they are otherwise independent, so this is the clearest single correctable finding of the V1.5 audit. The engine instead cancels on combustion, which neither witness mentions here. |
| **new software condition** | implemented as `mahapurusha_hamsa_textual` in `parashari_textual`; the rule above is unchanged |
| **source refs** | `BPHS_SA_75.1_MAHAPURUSHA` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 75.1-2 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files)<br>`JP_59_MAHAPURUSHA` — Vaidyanātha Dīkṣita: Jātaka Pārijāta Jātaka Pārijāta(SD) v.59 (sanskritdocuments.org ITRANS text) |
| **affected regression charts** | Default profile output unchanged on every regression chart; the corrected reading is in `parashari_textual` only. |
| **reason for change** | The legacy citation 'BPHS ch.75' is the ONLY one in the whole corpus that named the correct chapter. V1.3 recorded that these yogas are demonstrably absent from Bṛhajjātaka and guessed at Sārāvalī; the answer was BPHS all along. |
| **prediction eligibility** | `DISABLED` |

### `mahapurusha_malavya`

| field | value |
| --- | --- |
| **rule_id** | `mahapurusha_malavya` |
| **old software condition** | Shukra is in own sign, moolatrikona or exaltation AND occupies a kendra from the Lagna. Cancelled if combust. |
| **textual / source condition** | Shukra in a kendra, in own sign or exaltation (Jātaka Pārijāta 59 adds moolatrikona), AND STRONG — balibhiḥ at BPHS 75.1, baliṣṭhāḥ at JP 59. |
| **difference found** | The strength requirement is missing. Both witnesses state it and they are otherwise independent, so this is the clearest single correctable finding of the V1.5 audit. The engine instead cancels on combustion, which neither witness mentions here. |
| **new software condition** | implemented as `mahapurusha_malavya_textual` in `parashari_textual`; the rule above is unchanged |
| **source refs** | `BPHS_SA_75.1_MAHAPURUSHA` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 75.1-2 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files)<br>`JP_59_MAHAPURUSHA` — Vaidyanātha Dīkṣita: Jātaka Pārijāta Jātaka Pārijāta(SD) v.59 (sanskritdocuments.org ITRANS text) |
| **affected regression charts** | Default profile output unchanged on every regression chart; the corrected reading is in `parashari_textual` only. |
| **reason for change** | The legacy citation 'BPHS ch.75' is the ONLY one in the whole corpus that named the correct chapter. V1.3 recorded that these yogas are demonstrably absent from Bṛhajjātaka and guessed at Sārāvalī; the answer was BPHS all along. |
| **prediction eligibility** | `DISABLED` |

### `mahapurusha_ruchaka`

| field | value |
| --- | --- |
| **rule_id** | `mahapurusha_ruchaka` |
| **old software condition** | Mangal is in own sign, moolatrikona or exaltation AND occupies a kendra from the Lagna. Cancelled if combust. |
| **textual / source condition** | Mangal in a kendra, in own sign or exaltation (Jātaka Pārijāta 59 adds moolatrikona), AND STRONG — balibhiḥ at BPHS 75.1, baliṣṭhāḥ at JP 59. |
| **difference found** | The strength requirement is missing. Both witnesses state it and they are otherwise independent, so this is the clearest single correctable finding of the V1.5 audit. The engine instead cancels on combustion, which neither witness mentions here. |
| **new software condition** | implemented as `mahapurusha_ruchaka_textual` in `parashari_textual`; the rule above is unchanged |
| **source refs** | `BPHS_SA_75.1_MAHAPURUSHA` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 75.1-2 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files)<br>`JP_59_MAHAPURUSHA` — Vaidyanātha Dīkṣita: Jātaka Pārijāta Jātaka Pārijāta(SD) v.59 (sanskritdocuments.org ITRANS text) |
| **affected regression charts** | Default profile output unchanged on every regression chart; the corrected reading is in `parashari_textual` only. |
| **reason for change** | The legacy citation 'BPHS ch.75' is the ONLY one in the whole corpus that named the correct chapter. V1.3 recorded that these yogas are demonstrably absent from Bṛhajjātaka and guessed at Sārāvalī; the answer was BPHS all along. |
| **prediction eligibility** | `DISABLED` |

### `mahapurusha_shasha`

| field | value |
| --- | --- |
| **rule_id** | `mahapurusha_shasha` |
| **old software condition** | Shani is in own sign, moolatrikona or exaltation AND occupies a kendra from the Lagna. Cancelled if combust. |
| **textual / source condition** | Shani in a kendra, in own sign or exaltation (Jātaka Pārijāta 59 adds moolatrikona), AND STRONG — balibhiḥ at BPHS 75.1, baliṣṭhāḥ at JP 59. |
| **difference found** | The strength requirement is missing. Both witnesses state it and they are otherwise independent, so this is the clearest single correctable finding of the V1.5 audit. The engine instead cancels on combustion, which neither witness mentions here. |
| **new software condition** | implemented as `mahapurusha_shasha_textual` in `parashari_textual`; the rule above is unchanged |
| **source refs** | `BPHS_SA_75.1_MAHAPURUSHA` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 75.1-2 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files)<br>`JP_59_MAHAPURUSHA` — Vaidyanātha Dīkṣita: Jātaka Pārijāta Jātaka Pārijāta(SD) v.59 (sanskritdocuments.org ITRANS text) |
| **affected regression charts** | Default profile output unchanged on every regression chart; the corrected reading is in `parashari_textual` only. |
| **reason for change** | The legacy citation 'BPHS ch.75' is the ONLY one in the whole corpus that named the correct chapter. V1.3 recorded that these yogas are demonstrably absent from Bṛhajjātaka and guessed at Sārāvalī; the answer was BPHS all along. |
| **prediction eligibility** | `DISABLED` |

### `raja_yoga_generated`

| field | value |
| --- | --- |
| **rule_id** | `raja_yoga_generated` |
| **old software condition** | 36 generated rules, one per (kendra, trikoṇa, mode) with the 1st house not paired with itself, where mode is conjunction, mutual aspect or exchange. No exception is applied. |
| **textual / source condition** | BPHS 34.11-12: a kendra lord and a trikoṇa lord in each other's houses, together in one sign, or in mutual FULL aspect (pūrṇa-dṛṣṭyā), become yogakāraka. BPHS 34.15: not when those lords also own dusthanas. BPHS 41.28: kendra is Viṣṇu's place, trikoṇa Lakṣmī's, and Rājayoga comes from their lords' sambandha. |
| **difference found** | Two differences. The exception at BPHS 34.15 is not implemented at all, and it is not a marginal clause: on most ascendants at least one kendra or trikoṇa lord also owns a dusthana. And the witness says pūrṇa-dṛṣṭyā, full aspect, where the engine's mutual_aspect mode accepts any graha drishti including the partial special aspects. |
| **new software condition** | implemented as `raja_yoga_*_textual` in `parashari_textual`; the rule above is unchanged |
| **source refs** | `BPHS_SA_34.11-15_YOGAKARAKA` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 34.11-15 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files)<br>`BPHS_SA_41.28_KENDRA_TRIKONA` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 41.28 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files) |
| **affected regression charts** | tests/test_regression_jaipur_1988.py (Meena lagna) — forms 4 Raja Yogas; BPHS 34.15 does not fire there (no participating lord owns a dusthana). Demonstrated instead on a constructed Mesha chart in tests/test_rule_audit.py. |
| **reason for change** | Legacy citation 'BPHS ch.36 (Raja Yoga Adhyaya)' is wrong twice over: ch.36 is vividha-yoga, and ch.39, which IS titled rājayogādhyāya, is largely Jaimini material — kārakāṃśa, ātmakāraka, ārūḍha — and not the source of this rule either. This one evidence record covers all 36 generated rules; they share a condition shape and a source. |
| **prediction eligibility** | `DISABLED` |

### `sunapha`

| field | value |
| --- | --- |
| **rule_id** | `sunapha` |
| **old software condition** | Any of Mangal, Budha, Guru, Shukra, Shani occupies the house at inclusive distance 2 from Chandra's house — the nodes excluded. |
| **textual / source condition** | Excluding the Sun, grahas situated in the 2nd from the Moon constitute Sunaphā. BJ 13.3 hitvārkaṃ; BPHS 37.7 sūryaṃ binā. |
| **difference found** | The engine excludes Rahu and Ketu from counting as company for the Moon. Neither witness excludes anything but the Sun. Two independent Sanskrit works were read and both say the same thing, so this is not a gap in the evidence but a difference between the code and the text. |
| **new software condition** | implemented as `sunapha_textual` in `parashari_textual`; the rule above is unchanged |
| **source refs** | `BJ_13.3_CANDRA_YOGAS` — Varāhamihira: Bṛhajjātaka BJ_13.03 (Oriental Books Reprint Corporation, 2nd edition, 1979 (GRETIL))<br>`BPHS_SA_37.7_CANDRA_YOGAS` — Parāśara (attributed): Bṛhat Parāśara Horā Śāstra BPHS(Sanskrit/SD) 37.7 (sanskritdocuments.org ITRANS text, 97 chapters in 11 files)<br>`JP_83_CANDRA_YOGAS_QUOTING_HORA` — Vaidyanātha Dīkṣita: Jātaka Pārijāta Jātaka Pārijāta(SD) v.83 (sanskritdocuments.org ITRANS text) |
| **affected regression charts** | Default profile output unchanged on every regression chart; the corrected reading is in `parashari_textual` only. |
| **reason for change** | The legacy citation was 'BPHS ch.34'. The passage is at BPHS 37.7; ch.34 is the yogakāraka chapter and contains no Moon yoga. |
| **prediction eligibility** | `DISABLED` |

## Read and absent

A category that did not exist before V1.5. `UNVERIFIED` covers both "we never looked" and "we looked and it is not there", and those leave a reader in very different positions. These rules had their cited chapter read in full in a Sanskrit witness, and the rule was not in it.

| rule | cited | what the chapter actually contains |
| --- | --- | --- |
| `budha_aditya` | see rule `source` | Cited as 'BPHS ch.34'. Chapter 34 is yogakāraka and contains no such combination; chapter 38, the ravi-yoga chapter, gives Veśi, Vośi and Ubhayacarī and not this. |
| `chandra_mangala` | see rule `source` | Cited as 'BPHS ch.40.9'. BPHS 40.9 concerns the amātyakāraka and the lord of the janma rāśi. The combination is not in the chandra-yoga chapter (37) either, which was read in full. |
| `dhana_yoga_2_11_placement` | see rule `source` | Cited as 'BPHS ch.40.4'. BPHS 40.4 concerns the amātyakāraka being strong and well-placed, and says nothing about the 2nd or 11th lords. |
| `dhana_yoga_generated` | see rule `source` | BPHS ch.41, viśeṣa-dhana-yoga, was read in full. It gives wealth combinations as specific grahas in specific houses in their own signs (41.2-15), not as relationships among house lords. The single point of contact is 41.16, where the lords of the 9th and 5th are called wealth-givers. Chapter 40, which the engine cited, is rāja-sambandha-yoga and concerns royal patronage. |
| `neecha_bhanga_family` | see rule `source` | Cited as 'BPHS ch.75', which is the pañca-mahāpuruṣa chapter and has nothing to do with debilitation cancellation. The full Sanskrit BPHS was searched for nīcabhaṅga and the compound does not occur; chapters 9 and 10 are ariṣṭa and ariṣṭabhaṅga, which concern early death, not debilitation. |

## Conflicts

Where two reputable witnesses disagree, V1.5 models the disagreement rather than choosing. A rule carrying an unresolved conflict is barred from the evidence-gated strict profile and from strict synthesis, however well sourced it otherwise is.

| id | topic | status |
| --- | --- | --- |
| `AHARGANA_EPOCH_UNFIXED` | The epoch for Varsha and Masa Bala | UNRESOLVED |
| `BPHS_EDITION_UNIDENTIFIED` | Which BPHS the engine's ~100 yoga citations refer to | RESOLVED_BY_AUDIT |
| `DHANA_YOGA_NOT_LOCATED` | Whether BPHS states the engine's generic Dhana Yoga rule | UNRESOLVED_ABSENCE |
| `GAJAKESARI_REFERENCE_FRAME` | Whether Gajakesari is counted from the Lagna or only the Moon | MODELLED_AS_TWO_RULES |
| `KEMADRUMA_BHANGA_EXTENT` | Which conditions cancel Kemadruma | RESOLVED_AGAINST_IMPLEMENTATION |
| `LAKSHMI_YOGA_DEFINITION` | What Lakṣmī Yoga requires | MODELLED_AS_TWO_RULES |
| `MAHAPURUSHA_DIGNITY_SET` | Which dignities qualify a graha for a Mahāpuruṣa yoga | UNRESOLVED |
| `MAHAPURUSHA_STRENGTH_REQUIREMENT` | Whether a Mahāpuruṣa graha must additionally be strong | PARTIALLY_RESOLVED |
| `OJHAYUGMA_VIRUPA_VALUE` | Whether Ojhayugma Bala is 15 or 35 virupas per placement | RESOLVED_BY_ARITHMETIC |
| `PUTRAKARAKA_ATTRIBUTION` | Which graha is the natural significator of children | UNRESOLVED |
| `SUNAPHA_NODE_EXCLUSION` | Whether Rahu and Ketu count as company for the Moon yogas | RESOLVED_AGAINST_IMPLEMENTATION |

### Resolved against the implementation

Two V1.3 conflicts were recorded as source disagreements and turned out to be defects in the code. The distinction matters: a source conflict is a fact about the tradition and nobody's fault, and a divergence is something to fix.

**`KEMADRUMA_BHANGA_EXTENT`** — Which conditions cancel Kemadruma

V1.5 settles the part that was actually open. The V1.3 note asked what Bṛhajjātaka 13.3's second half concedes and what it rejects. Jātaka Pārijāta 83 quotes the verse in full, under the heading horāyām, and preserves the closing judgement: ukti-prasiddhā na te — 'those are not well established'. The kendra/navāṃśa opinion is therefore REPORTED AND REJECTED by the witness, not endorsed. Independently, BPHS 37.11 gives its own two conditions and explicitly excludes the Moon itself from counting (vinā candraṃ). The engine's four cancellation clauses are wider than either witness, and one of them — the Moon in a kendra from the Lagna — is contradicted outright. Behaviour is unchanged; `kemadruma_textual` implements the located reading.

**`SUNAPHA_NODE_EXCLUSION`** — Whether Rahu and Ketu count as company for the Moon yogas

V1.5 reclassifies this. It was registered in V1.3 as a conflict between a witness and the engine, on one witness and no counter-witness. A second independent Sanskrit witness has now been read and agrees with the first, and no witness anywhere supports excluding the nodes. That makes this not a disagreement among sources but a DEFECT IN THE CODE, and the affected rules are marked IMPLEMENTATION_DIVERGES accordingly. The legacy rules keep their behaviour so that no V1.4 result changes without notice; `sunapha_textual`, `anapha_textual` and `durudhara_textual` implement the located reading.

## Profile sizes

| profile | rules | note |
| --- | --- | --- |
| `parashari` | 110 | unchanged from V1.4 |
| `parashari_textual` | 108 | 48 rules substituted, not added |
| `parashari_strict` | 41 | evidence-gated; was 1 in V1.4 |

The textual profile is **smaller** than the default, which is the opposite of the intuitive expectation. More sourcing produced fewer and stricter rules: the located Gajakesari requires Jupiter unafflicted, the located Mahāpuruṣa yogas require strength, and the located Raja Yogas carry an exception that the default has never applied.

The strict profile grew from 1 rule to 41 **without a single change to the gate**. `strict_profile_eligible` is untouched since V1.3; the growth is entirely the arrival of evidence.

## The four claims, kept separate

| claim | status after V1.5 |
| --- | --- |
| COMPUTATIONALLY TESTED | The suite passes, including tests that pin each finding below. This says the code does what it was told to, and nothing more. |
| EXTERNALLY BENCHMARKED | Astronomical positions only. No rule, mapping or synthesis output has been benchmarked against anything. |
| TEXTUAL SOURCE LOCATED | Substantially improved: Sanskrit witnesses now exist for four works and the corpus has been checked against them. |
| TRADITION/SOURCE VALIDATED | **Nothing.** Unchanged since V1.3. |

No one of these is evidence for another. A passing test says nothing about a text; a located passage says nothing about whether the code implements it; and the audit above exists precisely because those two were being confused.

