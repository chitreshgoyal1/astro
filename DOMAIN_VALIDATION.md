# DOMAIN_VALIDATION.md

Source coverage for the 17 life domains of the synthesis engine.

Generated from `engine/synthesis/domains.py`. Do not edit by hand — regenerate with `python3 tools/generate_domain_report.py`.

## What this closes

V1.5 shipped 17 domains and recorded that **not one** house mapping had a located witness. That was the release's largest remaining gap, and it had a visible consequence: strict synthesis could speak about four domains, because the only source-qualified factor→domain links in the whole engine were kāraka attributions.

V1.6 read BPHS chapter 11 — `bhāvaviveka` — which is the house-signification chapter, and chapters 21 to 24, which give the phala of the tenth, eleventh and twelfth houses and the doctrine of the house lords. Most of the mappings turn out to be attested, several of them in a single word.

| | V1.5 | V1.6 |
| --- | --- | --- |
| House mappings with a witness | 0 | 38 of 43 |
| Kārakas with a witness | 5 | 7 of 24 |
| Domains strict synthesis admits | 4 | 16 of 17 |
| Varga mappings with a witness | 0 | 0 |

The varga row is unchanged and is the gap V1.6 did **not** close. BPHS chapters 6 and 7 give the ṣoḍaśavarga and how to compute them; no passage in any witness this engine holds assigns a divisional chart to a life area. D10-for-career and D9-for-marriage remain modern convention, however universal.

## The five factor types

A domain is not a house plus some kārakas. It is a list of factor→domain links, each making one of five kinds of claim with its own evidence. Collapsing them would hide which is sourced: CAREER has an attested HOUSE link, an attested HOUSE_LORD link and an unsourced VARGA link, and a reader should be able to see that.

| type | meaning | located | source-qualified |
| --- | --- | --- | --- |
| `HOUSE` | The bhāva itself signifies this area of life. | 38/43 | 38/43 |
| `HOUSE_LORD` | The condition of the bhāva's lord bears on the area. | 16/16 | 16/16 |
| `KARAKA` | A graha naturally signifies the area, independently of which house it occupies or rules. | 7/24 | 6/24 |
| `FUNCTIONAL_LORDSHIP` | What the graha ALSO rules for this particular Lagna. | 0/0 | 0/0 |
| `VARGA` | A divisional chart refines the area. | 0/11 | 0/11 |

## Mappings V1.6 corrected

Sourcing a mapping and changing one are different outcomes. These are the changes, as against the much larger set of mappings that were already right and simply had no citation.

### EDUCATION — primary house 4 → 5

BPHS 11.6 places `vidyā` (learning) and `buddhi` (the intellect) in the FIFTH bhāva. The fourth, at 11.5, gets vehicles, relatives, the mother's comfort, treasure, land and house — and no learning. V1.5 had followed a modern convention the text does not support.

### TRAVEL — houses 3, 9, 12 → 3, 7, 9

BPHS 11.4 gives `prayāṇa` from the third, 11.8 `adhva-prayāṇa` (road travel) from the seventh and 11.10 `tīrthayātrā` (pilgrimage) from the ninth. The twelfth, at 11.13, gets expenditure and news of enemies; V1.5's twelfth is dropped.

### SPIRITUALITY — added houses 5 and 12

BPHS 11.6 gives `yantra-mantra` from the fifth and BPHS 23.10 gives `mokṣa` from a well-disposed twelfth.

### RELATIONSHIPS — marked unsourced

BPHS 11.8 gives the seventh `jāyā` — the wife — specifically. No witness supports a general relationships domain distinct from marriage. The domain is retained and excluded from strict synthesis.

### CHILDREN — putrakāraka Saturn → Jupiter, both retained

V1.5 read BPHS 32.20 (`putraḥ śanaiścarāt`) and registered a conflict with modern practice. BPHS 32.23, four verses later, gives a second kāraka scheme and says `devejyāt pañcamāt putro` — the son from Jupiter. The disagreement is between two schemes inside one chapter, not between BPHS and modernity.

## Domain by domain

### CAREER

*Career and profession* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 10 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 10 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_21.1-8_KARMABHAVA`<br>`BPHS_SA_11.14-16_BHAVA_STRENGTH`<br>`BPHS_SA_24_BHAVESHAPHALA` |
| 2 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 11 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 6 | `HOUSE` | secondary | — UNVERIFIED | *none* |
| Surya | `KARAKA` | primary | — UNVERIFIED | *none* |
| Shani | `KARAKA` | primary | — UNVERIFIED | *none* |
| D10 | `VARGA` | primary | — UNVERIFIED | *none* |
| D9 | `VARGA` | secondary | — UNVERIFIED | *none* |

Textual terms located: `vṛtti`, `dhana`, `āya`, `śatru`.

Primary house and house lord both sourced; vargas are not.

### FINANCE

*Income and cash flow* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 11 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 11 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.14-16_BHAVA_STRENGTH`<br>`BPHS_SA_24_BHAVESHAPHALA` |
| 2 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 9 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| Guru | `KARAKA` | primary | — UNVERIFIED | *none* |
| Shukra | `KARAKA` | primary | — UNVERIFIED | *none* |

Textual terms located: `āya`, `dhana`, `bhāgya`.

Primary house and house lord sourced.

### WEALTH

*Accumulated wealth* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 2 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 2 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.14-16_BHAVA_STRENGTH`<br>`BPHS_SA_24_BHAVESHAPHALA` |
| 11 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| Guru | `KARAKA` | primary | — UNVERIFIED | *none* |

Textual terms located: `dhana-dhānya`, `āya`.

BPHS 41.16 separately names the lords of the ninth and fifth as wealth-givers. The engine's generic Dhana Yoga lord-pair rule remains unlocated — see the DHANA_YOGA_NOT_LOCATED conflict.

### MARRIAGE

*Marriage and partnership* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 7 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 7 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_24_BHAVESHAPHALA`<br>`BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| Shukra | `KARAKA` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_32.22-24_BHAVA_KARAKA`<br>`BPHS_SA_32.18-21_STHIRA_KARAKA` |
| 2 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| D9 | `VARGA` | primary | — UNVERIFIED | *none* |

Textual terms located: `jāyā`, `dārāḥ`, `kuṭumba`.

The best-sourced domain in the engine: house, house lord and kāraka are each attested, and the kāraka twice in one chapter.

### RELATIONSHIPS

*Relationships generally* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **no**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 7 | `HOUSE` | primary | — UNVERIFIED | *none* |
| 11 | `HOUSE` | secondary | — UNVERIFIED | *none* |
| Shukra | `KARAKA` | primary | — UNVERIFIED | *none* |

A domain with no located house witness. Retained because removing it would silently narrow the engine's output, and excluded from strict synthesis because nothing supports it.

### CHILDREN

*Children and progeny* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 5 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 5 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_24_BHAVESHAPHALA`<br>`BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| Guru | `KARAKA` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_32.22-24_BHAVA_KARAKA` |
| Shani | `KARAKA` | primary | — RULE_INTERPRETATION_MAPPED | `BPHS_SA_32.18-21_STHIRA_KARAKA` |
| 9 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| D7 | `VARGA` | primary | — UNVERIFIED | *none* |

Textual terms located: `putra`, `putra`, `putra`, `bhāgya`.

Conflicts: `PUTRAKARAKA_ATTRIBUTION`.

The challenging houses are the common putra-bhāva reckoning and are NOT in any located verse.

### EDUCATION

*Education and learning* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 5 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 5 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| 4 | `HOUSE` | secondary | — UNVERIFIED | *none* |
| 9 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| Budha | `KARAKA` | primary | — UNVERIFIED | *none* |
| Guru | `KARAKA` | primary | — UNVERIFIED | *none* |
| D24 | `VARGA` | secondary | — UNVERIFIED | *none* |

Textual terms located: `vidyā`, `dharma`.

CORRECTED IN V1.6. The primary house moved from the 4th to the 5th on the evidence of BPHS 11.6.

### PROPERTY

*Land, property and vehicles* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 4 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 4 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| 2 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| Mangal | `KARAKA` | primary | — UNVERIFIED | *none* |
| Shukra | `KARAKA` | primary | — UNVERIFIED | *none* |
| D4 | `VARGA` | secondary | — UNVERIFIED | *none* |

Textual terms located: `kṣetra, gṛha, vāhana`, `dhana`.

House and house lord sourced; vehicles named in the verse.

### HEALTH

*Health and vitality* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 1 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 6 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 1 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_24_BHAVESHAPHALA`<br>`BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| Surya | `KARAKA` | primary | — UNVERIFIED | *none* |
| D6 | `VARGA` | secondary | — UNVERIFIED | *none* |

Textual terms located: `deha, balābala`, `vraṇa`.

Part 24: domain-level activation only. This engine does not and will not output a diagnosis, a disease, a date of death, or a probability of any of them. The underlying house and graha calculations are retained for completeness and are not converted into a claim about a person.

### LONGEVITY

*Longevity factors* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 8 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 8 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| 1 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| Shani | `KARAKA` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_32.22-24_BHAVA_KARAKA` |

Textual terms located: `āyus`, `deha`, `mṛtyu`.

Part 24: domain-level activation only. This engine does not and will not output a diagnosis, a disease, a date of death, or a probability of any of them. The underlying house and graha calculations are retained for completeness and are not converted into a claim about a person.

### FAMILY

*Family and domestic life* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 2 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 2 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| 4 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| Chandra | `KARAKA` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_32.22-24_BHAVA_KARAKA` |
| Surya | `KARAKA` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_32.22-24_BHAVA_KARAKA`<br>`BPHS_SA_32.18-21_STHIRA_KARAKA` |
| D12 | `VARGA` | secondary | — UNVERIFIED | *none* |

Textual terms located: `kuṭumba`, `bandhu`, `mātā`, `tāta`.

House, house lord and two karakas sourced.

### SIBLINGS

*Siblings* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 3 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 3 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| Mangal | `KARAKA` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_32.22-24_BHAVA_KARAKA`<br>`BPHS_SA_32.18-21_STHIRA_KARAKA` |
| 11 | `HOUSE` | secondary | — UNVERIFIED | *none* |
| D3 | `VARGA` | secondary | — UNVERIFIED | *none* |

Textual terms located: `bhrātṛ`, `bhrātā`, `āya`.

House, house lord and kāraka all sourced.

### TRAVEL

*Travel and movement* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 3 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 7 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 9 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 3 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| Chandra | `KARAKA` | primary | — UNVERIFIED | *none* |

Textual terms located: `prayāṇa`, `adhva-prayāṇa`, `tīrthayātrā`.

Three houses attested, which is more than V1.5 assigned: the 3rd for travel generally, the 7th for road travel and the 9th for pilgrimage. V1.5's 12th is not supported here.

### FOREIGN_RESIDENCE

*Foreign residence* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 12 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_23.9-11_VYAYABHAVA` |
| 12 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_23.9-11_VYAYABHAVA`<br>`BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| 10 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 9 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| Shani | `KARAKA` | primary | — UNVERIFIED | *none* |
| Rahu | `KARAKA` | primary | — UNVERIFIED | *none* |

Textual terms located: `deśāntara`, `pravāsa`, `tīrthayātrā`.

V1.5 mapped this to the 12th from convention. BPHS 23.11 turns out to support it in so many words, and BPHS 11.11 adds the 10th via pravāsa — so the mapping was right and the engine had not known why.

### SPIRITUALITY

*Dharma and spiritual life* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 9 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 9 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_24_BHAVESHAPHALA`<br>`BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| 12 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_23.9-11_VYAYABHAVA` |
| 5 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| Guru | `KARAKA` | primary | — UNVERIFIED | *none* |
| D20 | `VARGA` | secondary | — UNVERIFIED | *none* |

Textual terms located: `dharma`, `mokṣa`, `yantra-mantra`.

Four houses attested, including the fifth for yantra and mantra, which V1.5 did not have.

### BUSINESS

*Business and enterprise* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 7 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 7 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| 10 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA`<br>`BPHS_SA_21.1-8_KARMABHAVA` |
| 11 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| Budha | `KARAKA` | primary | — UNVERIFIED | *none* |
| D10 | `VARGA` | primary | — UNVERIFIED | *none* |

Textual terms located: `vāṇijya`, `vṛtti`, `āya`.

`vāṇijya` appears twice — at the seventh house in BPHS 11.8 and at the tenth lord in BPHS 21.4 — which is why both are mapped.

### LITIGATION

*Disputes and litigation* — reference space `RASHI`, profile `parashari_textual_v16`, strict eligible: **yes**

| factor | type | primary | status | witness |
| --- | --- | --- | --- | --- |
| 6 | `HOUSE` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 6 | `HOUSE_LORD` | primary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.14-16_BHAVA_STRENGTH` |
| 8 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| 12 | `HOUSE` | secondary | ✓ IMPLEMENTATION_MATCHED | `BPHS_SA_11.2-13_BHAVAVIVEKA` |
| Mangal | `KARAKA` | primary | — UNVERIFIED | *none* |

Textual terms located: `śatru`, `raṇa, ripu`, `vairi-vṛttānta`.

Three houses attested for enemies and disputes. Note this domain is about conflict as the texts describe it, not about courts, which no verse mentions.

## What remains unsourced

| domain | factor | type | why |
| --- | --- | --- | --- |
| CAREER | 6 | `HOUSE` | BPHS 11.7: enemies and wounds from the sixth. Its relevance to service and employment is a modern reading and is NOT in the verse. |
| CAREER | Surya | `KARAKA` | Authority and station. Not in any located kāraka scheme; BPHS 32.22 gives the Sun in the 9th for the FATHER, which is a different claim. |
| CAREER | Shani | `KARAKA` | Labour and service. Not located; BPHS 32.24 gives Saturn in the 8th for death. |
| CAREER | D10 | `VARGA` | The assignment of this divisional chart to this topic is standard modern practice. BPHS ch.6-7 give the shodashavarga and how to compute them; no passage located in any witness … |
| CAREER | D9 | `VARGA` | The assignment of this divisional chart to this topic is standard modern practice. BPHS ch.6-7 give the shodashavarga and how to compute them; no passage located in any witness … |
| FINANCE | Guru | `KARAKA` | Expansion and fortune. Not in a located kāraka scheme. |
| FINANCE | Shukra | `KARAKA` | Assets and comfort. BPHS 32.23 gives Venus in the 7th for the WIFE, which is a different claim. |
| WEALTH | Guru | `KARAKA` | Wealth. Not in a located kāraka scheme. |
| MARRIAGE | D9 | `VARGA` | The assignment of this divisional chart to this topic is standard modern practice. BPHS ch.6-7 give the shodashavarga and how to compute them; no passage located in any witness … |
| RELATIONSHIPS | 7 | `HOUSE` | NOT LOCATED. BPHS 11.8 gives the seventh as `jāyā` — the wife — specifically. No witness has been located for a general 'relationships' domain distinct from marriage, and this d… |
| RELATIONSHIPS | 11 | `HOUSE` | NOT LOCATED. BPHS 11.12 gives the eleventh income, increase and cattle. Its modern association with friends and social circles is not in the verse. |
| RELATIONSHIPS | Shukra | `KARAKA` | Attraction and union. The located Venus attributions are to the WIFE specifically, not to relationships in general. |
| CHILDREN | Shani | `KARAKA` | BPHS 32.20: `putraḥ śanaiścarāt` — the son from Saturn, in the sthira kāraka list. Retained as a second reading; see the PUTRAKARAKA_ATTRIBUTION conflict, which V1.6 resolved in… |
| CHILDREN | D7 | `VARGA` | The assignment of this divisional chart to this topic is standard modern practice. BPHS ch.6-7 give the shodashavarga and how to compute them; no passage located in any witness … |
| EDUCATION | 4 | `HOUSE` | V1.5 made the FOURTH the primary house for education. BPHS 11.5 gives the fourth vehicles, relatives, the mother's comfort, treasure, land and house — and no learning. The fourt… |
| EDUCATION | Budha | `KARAKA` | Intellect and articulation. BPHS 32.23 gives Mercury in the 6th for the MATERNAL UNCLE, a different claim. |
| EDUCATION | Guru | `KARAKA` | Higher learning. Not in a located kāraka scheme. |
| EDUCATION | D24 | `VARGA` | The assignment of this divisional chart to this topic is standard modern practice. BPHS ch.6-7 give the shodashavarga and how to compute them; no passage located in any witness … |
| PROPERTY | Mangal | `KARAKA` | Land. BPHS 32.23 gives Mars in the 3rd for the BROTHER, a different claim. |
| PROPERTY | Shukra | `KARAKA` | Vehicles and comfort. Not located for this. |
| PROPERTY | D4 | `VARGA` | The assignment of this divisional chart to this topic is standard modern practice. BPHS ch.6-7 give the shodashavarga and how to compute them; no passage located in any witness … |
| HEALTH | Surya | `KARAKA` | Vitality. Not in a located kāraka scheme. |
| HEALTH | D6 | `VARGA` | The assignment of this divisional chart to this topic is standard modern practice. BPHS ch.6-7 give the shodashavarga and how to compute them; no passage located in any witness … |
| FAMILY | D12 | `VARGA` | The assignment of this divisional chart to this topic is standard modern practice. BPHS ch.6-7 give the shodashavarga and how to compute them; no passage located in any witness … |
| SIBLINGS | 11 | `HOUSE` | BPHS 11.12: the eleventh. Its association with elder siblings is a modern reading not in the verse. |
| SIBLINGS | D3 | `VARGA` | The assignment of this divisional chart to this topic is standard modern practice. BPHS ch.6-7 give the shodashavarga and how to compute them; no passage located in any witness … |
| TRAVEL | Chandra | `KARAKA` | Movement. Not in a located kāraka scheme. |
| FOREIGN_RESIDENCE | Shani | `KARAKA` | Distance and separation. Not located for this. |
| FOREIGN_RESIDENCE | Rahu | `KARAKA` | The foreign and unfamiliar. Not located; the nodes appear in no kāraka scheme this engine has read. |
| SPIRITUALITY | Guru | `KARAKA` | Dharma and the teacher. Not in a located kāraka scheme for this. |
| SPIRITUALITY | D20 | `VARGA` | The assignment of this divisional chart to this topic is standard modern practice. BPHS ch.6-7 give the shodashavarga and how to compute them; no passage located in any witness … |
| BUSINESS | Budha | `KARAKA` | Trade. Not in a located kāraka scheme. |
| BUSINESS | D10 | `VARGA` | The assignment of this divisional chart to this topic is standard modern practice. BPHS ch.6-7 give the shodashavarga and how to compute them; no passage located in any witness … |
| LITIGATION | Mangal | `KARAKA` | Conflict. Not in a located kāraka scheme for this. |

## The edition question (Part 5)

**Status: UNRESOLVED.**

Every locator in this document is a chapter-and-verse reference into one witness, and BPHS chapter numbering is precisely what varies between editions. V1.6 went looking for the printed exemplar behind the transliteration and did not find it.

| | |
| --- | --- |
| chapter count | 97 |
| encoding | ITRANS |
| file count | 11 |
| latest update dates | March 2026 (par3140); December 2021 (par1120) |
| proofreaders | Ahto Jarve; Ginda Lass (chapters 11-20) |
| repository | sanskritdocuments.org |
| transliterator | Ahto Jarve |

**Not known:** The printed exemplar. No edition, editor, publisher, year, volume or manuscript is named in any of the eleven file headers, nor on the repository's HTML pages for them, which were checked in V1.6. The headers credit data entry and proofreading only.

**Why it matters:** BPHS is a textual tradition rather than one document. The Chaukhamba Kashi Sanskrit Series edition, the Khemraj edition and the Santhanam translation's underlying text do not agree on chapter division throughout. Every locator produced by the V1.5 and V1.6 audits — `BPHS(Sanskrit/SD) 11.2-13`, `34.11-15`, `41.28` — is stable only with respect to THIS witness. They are reproducible, because the file is checksummed; they are not portable.

**Tried in V1.6:** Fetched the repository's per-file HTML pages looking for bibliographic metadata: none present. The pages link to archive.org scans and translations in an index, but none is identified as the source of the transliteration.

**Consequence:** This is one of the two reasons nothing in the engine is TRADITION_VALIDATED, the other being the open review queue. A Sanskrit-tier witness whose exemplar is unidentified can establish that a reading EXISTS in the tradition. It cannot establish that it is the reading of any particular edition a reader might hold.

## The four claims, kept separate

| claim | status for the domain layer |
| --- | --- |
| COMPUTATIONALLY TESTED | The mappings are exercised by the suite, including a test that the strict gate refuses an unsourced factor inside a sourced domain. |
| EXTERNALLY BENCHMARKED | Nothing. No domain mapping has been tested against any outcome, and none could be by this engine. |
| TEXTUAL SOURCE LOCATED | Substantially improved — this document. |
| TRADITION/SOURCE VALIDATED | **Nothing.** A located passage is not a confirmed reading, and the exemplar behind the witness is still unidentified. |

Finding that BPHS 11.11 gives the tenth house `vṛtti` establishes that the mapping has a textual basis. It does not establish that the engine's use of it is what the tradition intends, and no amount of further reading by this engine could.

