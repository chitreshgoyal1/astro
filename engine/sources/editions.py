"""
Registered textual witnesses (V1.3 Parts 2, 3, 7)
--------------------------------------------------
Every witness this engine has actually examined, and — just as importantly —
an explicit record of the works it has NOT.

WHAT WAS ACTUALLY OBTAINED

    Bṛhajjātaka of Varāhamihira, in the GRETIL digital text prepared by
    Mizue Sugita from the Oriental Books Reprint Corporation second edition
    (1979). Sanskrit, with the file's SHA-256 recorded. Obtained in V1.3.

    Brihat Parashara Hora Shastra in the R. Santhanam English translation
    (Ranjan Publications). TRANSLATION tier, not Sanskrit. Obtained in V1.4,
    after V1.3 wrongly concluded it was unavailable.

    Bṛhat Parāśara Horā Śāstra IN SANSKRIT, Phaladīpikā and Jātaka Pārijāta,
    as proofread ITRANS transliterations from sanskritdocuments.org. Obtained
    in V1.5, after V1.4 wrongly concluded all three were unavailable.

THE SAME MISTAKE, THREE RELEASES RUNNING

    V1.3 recorded BPHS as unobtainable after one retrieval method failed.
    V1.4 obtained the translation in minutes, and then recorded the Sanskrit
    BPHS, Phaladīpikā and Jātaka Pārijāta as unobtainable — having searched
    archive.org and GRETIL, and not sanskritdocuments.org, which held all
    three. V1.5 retrieved every one of them on the first attempt.

    This is recorded rather than quietly fixed, because the error has a shape
    worth recognising: "we could not find it" is a claim about the search and
    was three times written down as a claim about the text. UNAVAILABLE_WORKS
    carries `retrieval_attempts` for exactly this reason, and
    RESOLVED_UNAVAILABLE_WORKS keeps the overturned claims visible instead of
    deleting them.

STILL NOT READ

    Sārāvalī. A 1928 Sanskrit edition was located and downloaded in full, and
    it is an image scan with no text layer, so not one verse of it has been
    read. It stays in UNAVAILABLE_WORKS: having the file is not having the
    text, and the distinction is the entire subject of this module.

COPYRIGHT AND LICENCE

    The Santhanam translation is in copyright. The sanskritdocuments.org
    files are volunteer-prepared and their own headers restrict them to
    personal study and research and forbid reposting.

    Under both restrictions the engine stores the same thing: metadata,
    edition, locator, checksum, a short incipit for finding the verse, and
    paraphrase in the engine's own words. No running text, no verse
    quotations, nothing redistributable. Every one of these files was read
    outside the repository and none is vendored.

WHY A BARE WORK NAME IS NOT A CITATION (Part 7)

    BPHS is a textual tradition, not one document. Editions differ in chapter
    division, verse numbering, Sanskrit readings and translation. "BPHS
    ch.36" identifies a passage about as well as "chapter 36" identifies a
    passage of the Bible. A citation must name its witness.
"""

from __future__ import annotations

from .models import SourceAuthority, SourceType, SourceWitness

# ── Witnesses actually examined ──────────────────────────────────────────────

BRIHAJJATAKA_GRETIL = SourceWitness(
    id="BJ_GRETIL_SUGITA_1979",
    work="Bṛhajjātaka",
    traditional_author="Varāhamihira",
    authority=SourceAuthority.PRIMARY_SANSKRIT_WITNESS,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (IAST transliteration)",
    edition="Oriental Books Reprint Corporation, 2nd edition, 1979",
    editor_or_translator="Digital text entered by Mizue Sugita (1994)",
    publication_year=1979,
    publisher="Oriental Books Reprint Corporation; digital text via GRETIL, "
              "Niedersächsische Staats- und Universitätsbibliothek Göttingen",
    retrieved_from=("https://gretil.sub.uni-goettingen.de/gretil/corpustei/"
                    "transformations/plaintext/sa_varAhamihira-bRhajjAtaka.txt"),
    retrieved_on="2026-09-27",
    checksum_if_local=(
        "70aa03c16cd4438a61f9d8a21904ebd1c842aae0550a162bf64cafacd4e0ddc7"),
    notes=(
        "GRETIL's own header records the underlying printed edition and the "
        "data-entry provenance. Verse references use the file's own scheme, "
        "BJ_<chapter>.<verse>. Distributed CC BY-NC-SA 4.0, so only short "
        "incipits are reproduced here, never running text."),
)

# Passage-level witnesses. Each is a distinct citation into the text above.
# `incipit` carries only enough Sanskrit to find the verse.

BJ_1_6_NAVAMSHA = SourceWitness(
    id="BJ_1.6_NAVAMSHA",
    work="Bṛhajjātaka",
    traditional_author="Varāhamihira",
    authority=SourceAuthority.PRIMARY_SANSKRIT_WITNESS,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (IAST)",
    edition="Oriental Books Reprint Corporation, 2nd edition, 1979 (GRETIL)",
    publication_year=1979,
    chapter="1",
    verse_start="6",
    locator="BJ_01.06",
    retrieved_from=BRIHAJJATAKA_GRETIL.retrieved_from,
    retrieved_on="2026-09-27",
    checksum_if_local=BRIHAJJATAKA_GRETIL.checksum_if_local,
    incipit="aja.mṛga.tauli.candra.bhavana.ādi.nava.aṃśa.vidhir …",
    notes=("Names four starting rashis for the navāṃśa: aja (Meṣa), mṛga "
           "(Makara), taulī (Tulā) and candra-bhavana (Karka, the Moon's "
           "house)."),
)

BJ_1_7_TRIMSHAMSHA = SourceWitness(
    id="BJ_1.7_TRIMSHAMSHA",
    work="Bṛhajjātaka",
    traditional_author="Varāhamihira",
    authority=SourceAuthority.PRIMARY_SANSKRIT_WITNESS,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (IAST)",
    edition="Oriental Books Reprint Corporation, 2nd edition, 1979 (GRETIL)",
    publication_year=1979,
    chapter="1",
    verse_start="7",
    locator="BJ_01.07",
    retrieved_from=BRIHAJJATAKA_GRETIL.retrieved_from,
    retrieved_on="2026-09-27",
    checksum_if_local=BRIHAJJATAKA_GRETIL.checksum_if_local,
    incipit="kuja.ravija.guru.jña.śukra.bhāgāḥ … ayuji.yuji.tu.bhe.viparyayasthaḥ",
    notes=("Gives the triṃśāṃśa lord order as Kuja (Maṅgala), Ravija "
           "(Śani), Guru, Jña (Budha), Śukra, and states that the order is "
           "reversed in even rashis (ayuji/yuji … viparyayasthaḥ). The "
           "DEGREE spans of the five portions are not transparently readable "
           "in this verse — see the review queue."),
)

BJ_13_2_ADHIYOGA = SourceWitness(
    id="BJ_13.2_ADHIYOGA",
    work="Bṛhajjātaka",
    traditional_author="Varāhamihira",
    authority=SourceAuthority.PRIMARY_SANSKRIT_WITNESS,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (IAST)",
    edition="Oriental Books Reprint Corporation, 2nd edition, 1979 (GRETIL)",
    publication_year=1979,
    chapter="13",
    verse_start="2",
    locator="BJ_13.02",
    retrieved_from=BRIHAJJATAKA_GRETIL.retrieved_from,
    retrieved_on="2026-09-27",
    checksum_if_local=BRIHAJJATAKA_GRETIL.checksum_if_local,
    incipit="saumyaiḥ.smara.ari.nidhaneṣv.adhiyoga.indos …",
    notes=("Benefics (saumyaiḥ) in the smara (7th), ari (6th) and nidhana "
           "(8th) from the Moon (indoḥ) constitute Adhiyoga. The chapter is "
           "titled candra-yoga, so the reference frame is explicit."),
)

BJ_13_3_CANDRA_YOGAS = SourceWitness(
    id="BJ_13.3_CANDRA_YOGAS",
    work="Bṛhajjātaka",
    traditional_author="Varāhamihira",
    authority=SourceAuthority.PRIMARY_SANSKRIT_WITNESS,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (IAST)",
    edition="Oriental Books Reprint Corporation, 2nd edition, 1979 (GRETIL)",
    publication_year=1979,
    chapter="13",
    verse_start="3",
    locator="BJ_13.03",
    retrieved_from=BRIHAJJATAKA_GRETIL.retrieved_from,
    retrieved_on="2026-09-27",
    checksum_if_local=BRIHAJJATAKA_GRETIL.checksum_if_local,
    incipit=("hitvā.arkaṃ.sunaphā.anaphā.durudhurāḥ.sva.antya.ubhayasthair."
             "grahaiḥ.śīta.aṃśoḥ …"),
    notes=("The locus for Sunaphā, Anaphā, Durudhurā and Kemadruma. Contains "
           "the Sun-exclusion (hitvā arkaṃ), the Moon reference frame "
           "(śītāṃśoḥ), and — in its second half — the cancellation of "
           "Kemadruma when the Moon is angular or conjoined, together with an "
           "explicit note that a further opinion is not well established."),
)

BJ_12_NABHASA = SourceWitness(
    id="BJ_12_NABHASA",
    work="Bṛhajjātaka",
    traditional_author="Varāhamihira",
    authority=SourceAuthority.PRIMARY_SANSKRIT_WITNESS,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (IAST)",
    edition="Oriental Books Reprint Corporation, 2nd edition, 1979 (GRETIL)",
    publication_year=1979,
    chapter="12",
    locator="BJ_12",
    retrieved_from=BRIHAJJATAKA_GRETIL.retrieved_from,
    retrieved_on="2026-09-27",
    checksum_if_local=BRIHAJJATAKA_GRETIL.checksum_if_local,
    incipit="nābhasayoga (chapter title)",
    notes=("The Nābhasa yoga chapter. Recorded because the engine does NOT "
           "implement these yogas — a gap worth knowing about, since they are "
           "among the best-attested in the earliest literature."),
)

# ── BPHS, acquired in V1.4 ───────────────────────────────────────────────────
# TRANSLATION tier, deliberately. Santhanam's English is a witness to
# Santhanam's reading of BPHS, which is not the same thing as a witness to
# BPHS. Rules resting on it can reach IMPLEMENTATION_MATCHED but not
# TRADITION_VALIDATED, which needs a Sanskrit-tier witness.

BPHS_SANTHANAM_V1 = SourceWitness(
    id="BPHS_SANTHANAM_V1",
    work="Bṛhat Parāśara Horā Śāstra",
    traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.TRANSLATION,
    source_type=SourceType.DIGITISED_PRINT,
    language="English (translation of Sanskrit)",
    edition="Volume 1, chapters 1-45",
    editor_or_translator="R. Santhanam (translator)",
    publisher="Ranjan Publications, New Delhi",
    volume=1,
    retrieved_from="https://archive.org/download/BPHSEnglish/",
    retrieved_on="2026-09-27",
    checksum_if_local=(
        "a51181de8272db15d135221bd9cd4e5e3135821207f221478d63eeb6d32a9ff9"),
    notes=(
        "Scanned OCR. Verse numbering follows this edition's chapter/sloka "
        "scheme, which is NOT guaranteed to match other BPHS editions — the "
        "reason a citation must name its witness. In copyright: metadata and "
        "paraphrase only, never running text."),
)

BPHS_SANTHANAM_V2 = SourceWitness(
    id="BPHS_SANTHANAM_V2",
    work="Bṛhat Parāśara Horā Śāstra",
    traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.TRANSLATION,
    source_type=SourceType.DIGITISED_PRINT,
    language="English (translation of Sanskrit)",
    edition="Volume 2, chapters 46 onwards",
    editor_or_translator="R. Santhanam (translator)",
    publisher="Ranjan Publications, New Delhi",
    volume=2,
    retrieved_from="https://archive.org/download/BPHSEnglish/",
    retrieved_on="2026-09-27",
    checksum_if_local=(
        "b2ef05b452a6c30bc9b2bfc2bd39d61596b8b3e1280cbcc4999f95b04c740dba"),
    notes="As volume 1. Contains the Ashtakavarga chapters.",
)

BPHS_27_SHADBALA = SourceWitness(
    id="BPHS_27_SHADBALA",
    work="Bṛhat Parāśara Horā Śāstra",
    traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.TRANSLATION,
    source_type=SourceType.DIGITISED_PRINT,
    language="English (translation of Sanskrit)",
    edition="Santhanam, Ranjan Publications, vol. 1",
    editor_or_translator="R. Santhanam (translator)",
    publisher="Ranjan Publications, New Delhi",
    volume=1,
    chapter="27",
    verse_start="1",
    verse_end="33",
    locator="BPHS(Santhanam) 27.1-33",
    retrieved_from="https://archive.org/download/BPHSEnglish/",
    retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANTHANAM_V1.checksum_if_local,
    incipit="Chapter 27, \"Evaluation Of Strengths\"",
    notes=(
        "The Shadbala chapter. Gives Sthana Bala and its five subcomponents "
        "(1-6), Dig Bala (7), Kala Bala and its subdivisions (8-17), Chesta "
        "Bala for the luminaries (18), Drik Bala (19), planetary war (20), "
        "Naisargika Bala (14) and the Shadbala requirements (32-33)."),
)

BPHS_66_ASHTAKAVARGA = SourceWitness(
    id="BPHS_66_ASHTAKAVARGA",
    work="Bṛhat Parāśara Horā Śāstra",
    traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.TRANSLATION,
    source_type=SourceType.DIGITISED_PRINT,
    language="English (translation of Sanskrit)",
    edition="Santhanam, Ranjan Publications, vol. 2",
    editor_or_translator="R. Santhanam (translator)",
    publisher="Ranjan Publications, New Delhi",
    volume=2,
    chapter="66",
    verse_start="1",
    verse_end="68",
    locator="BPHS(Santhanam) 66.1-68",
    retrieved_from="https://archive.org/download/BPHSEnglish/",
    retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANTHANAM_V2.checksum_if_local,
    incipit="Chapter 66, Ashtakavarga: rekhaprada/karanaprada houses",
    notes=(
        "Gives the benefic-point (rekhaprada) houses for each of the seven "
        "grahas and the Ascendant. The Sun's table at verses 43-45 was read "
        "and matches the engine. The remaining tables are present but the OCR "
        "is damaged in places, so per-graha verification is INCOMPLETE — see "
        "the review queue."),
)

# ── V1.5: the Sanskrit corpora ───────────────────────────────────────────────
#
# V1.4 recorded a Sanskrit BPHS, Phaladīpikā and Jātaka Pārijāta as unobtained.
# That was wrong for the same reason V1.3's BPHS entry was wrong: it was a
# statement about the searches that had been run, written as though it were a
# statement about the texts. All three are held by sanskritdocuments.org as
# proofread ITRANS transliterations and were retrieved on the first attempt.
#
# LICENSING — these are NOT vendored. Each file's own header restricts it to
# personal study and research and forbids reposting. The engine therefore
# stores what it is entitled to store and what is actually useful: the
# retrieval URL, the SHA-256 of the file as retrieved, the passage locator, a
# short incipit for finding the verse, and paraphrase in the engine's own
# words. The files themselves were read outside the repository.
#
# AUTHORITY — these are Sanskrit-tier, which is what V1.3 and V1.4 lacked.
# But note the limitation recorded on each corpus witness: the transliterator
# did not name the printed exemplar. A Sanskrit text whose exemplar is
# unidentified is still a Sanskrit witness, and is still not a critical
# edition; the review queue carries that question rather than glossing it.

BPHS_SANSKRIT_SD = SourceWitness(
    id="BPHS_SANSKRIT_SD",
    work="Bṛhat Parāśara Horā Śāstra",
    traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS transliteration)",
    edition="sanskritdocuments.org ITRANS text, 97 chapters in 11 files",
    editor_or_translator="Transliterated and proofread by Ahto Jarve",
    publisher="sanskritdocuments.org (volunteer-maintained)",
    retrieved_from=("https://sanskritdocuments.org/"
                    "doc_z_misc_sociology_astrology/ (par0110 … par9197)"),
    retrieved_on="2026-09-27",
    checksum_if_local=(
        "dcfb34a678410eb5e4a26dba5323470e9ef67fa8acf6216c694d8b1ee52f5f92"),
    notes=(
        "Checksum is of par3140.itx, the file holding the yoga chapters and "
        "the one most of the V1.5 audit rests on; the other ten files were "
        "retrieved in the same session and their checksums are recorded in "
        "`BPHS_SANSKRIT_SD_FILES`. Volunteer licence: personal study and "
        "research, no reposting. Not vendored. See "
        "`BPHS_SANSKRIT_SD_EDITION_IDENTITY` for what is and is not known "
        "about the printed exemplar."),
)

# ── Part 5: the edition identity question, answered as far as it goes ────────
#
# V1.5 raised this as a blocking review item, because every locator in the
# V1.5 and V1.6 audits is a chapter-and-verse reference into this witness,
# and chapter numbering is precisely what varies between BPHS editions.
#
# V1.6 went looking and the answer is: STILL UNRESOLVED, and now unresolved
# with its reasons written down rather than merely unexamined. The brief says
# to mark it explicitly if it stays unresolved, so it is marked here rather
# than softened into a footnote on the witness.
BPHS_SANSKRIT_SD_EDITION_IDENTITY: dict = {
    "witness": "BPHS_SANSKRIT_SD",
    "status": "UNRESOLVED",
    "what_is_known": {
        "transliterator": "Ahto Jarve",
        "proofreaders": "Ahto Jarve; Ginda Lass (chapters 11-20)",
        "repository": "sanskritdocuments.org",
        "encoding": "ITRANS",
        "chapter_count": 97,
        "file_count": 11,
        "latest_update_dates": "March 2026 (par3140); December 2021 (par1120)",
    },
    "what_is_not_known": (
        "The printed exemplar. No edition, editor, publisher, year, volume "
        "or manuscript is named in any of the eleven file headers, nor on "
        "the repository's HTML pages for them, which were checked in V1.6. "
        "The headers credit data entry and proofreading only."),
    "why_it_matters": (
        "BPHS is a textual tradition rather than one document. The Chaukhamba "
        "Kashi Sanskrit Series edition, the Khemraj edition and the "
        "Santhanam translation's underlying text do not agree on chapter "
        "division throughout. Every locator produced by the V1.5 and V1.6 "
        "audits — `BPHS(Sanskrit/SD) 11.2-13`, `34.11-15`, `41.28` — is "
        "stable only with respect to THIS witness. They are reproducible, "
        "because the file is checksummed; they are not portable."),
    "what_was_tried_in_v16": (
        "Fetched the repository's per-file HTML pages looking for "
        "bibliographic metadata: none present. The pages link to archive.org "
        "scans and translations in an index, but none is identified as the "
        "source of the transliteration."),
    "what_would_resolve_it": (
        "A statement from the transliterator or the repository; or a "
        "collation of a sample of chapters against a named printed edition, "
        "which is a scholarly task and not a programming one."),
    "consequence_for_validation": (
        "This is one of the two reasons nothing in the engine is "
        "TRADITION_VALIDATED, the other being the open review queue. A "
        "Sanskrit-tier witness whose exemplar is unidentified can establish "
        "that a reading EXISTS in the tradition. It cannot establish that it "
        "is the reading of any particular edition a reader might hold."),
}

# Per-file checksums, so a future reader can verify any locator in the audit
# rather than only the three files the passage witnesses happen to cite.
BPHS_SANSKRIT_SD_FILES: dict = {
    "par0110.itx":
        "96f788c6258c5b8405672842d6d2f583b2d75fd7e207dc8d0e09ff76dbf6838a",
    "par1120.itx":
        "b2576534ea1c851a39992440e5a9f6478ecc16d80c325d3c24cdac988e121f26",
    "par2130.itx":
        "3c278b601d32553254214e113a22650541e17ba31b85e383f55f15992d68a446",
    "par3140.itx":
        "dcfb34a678410eb5e4a26dba5323470e9ef67fa8acf6216c694d8b1ee52f5f92",
    "par4145.itx":
        "d10a26a564fc351bdd49a0a49f6c27705150f349b10424c90f9641fb6652cca2",
    "par4650.itx":
        "9bd339943510fdf68274693f788122b11c51307af8470d55ec86cad33e2ee700",
    "par5160.itx":
        "64b595092f9e1ea9c40c6275ae2ed35e0262ef2d09e435a951673f346bf85eeb",
    "par6170.itx":
        "967ed53bcfafcbfb02a7f0f00916f88bc8a069ea770a61d5ff8023cf43019f4c",
    "par7180.itx":
        "99840dfd4a1a6f33bff333f1a8e4a44aeb3e22221805a8e9ccba34a150699a15",
    "par8190.itx":
        "a55cf5f59ebaf3dddb9e528ae40391a8677bf7e15f627879cf37f642f74ba2c4",
    "par9197.itx":
        "f07a600efb5fed9be39b32356620613870222cd723e562c3a7daa0bcbd7ef202",
}

# Which file holds which chapter, so a locator can be checked against the
# right checksum. The split is the repository's, not the text's.
BPHS_SANSKRIT_SD_CHAPTER_FILES: tuple = (
    (1, 10, "par0110.itx"), (11, 20, "par1120.itx"),
    (21, 30, "par2130.itx"), (31, 40, "par3140.itx"),
    (41, 45, "par4145.itx"), (46, 50, "par4650.itx"),
    (51, 60, "par5160.itx"), (61, 70, "par6170.itx"),
    (71, 80, "par7180.itx"), (81, 90, "par8190.itx"),
    (91, 97, "par9197.itx"),
)


def bphs_file_for_chapter(chapter: int) -> str:
    """Which retrieved file a BPHS chapter locator refers into."""
    for first, last, name in BPHS_SANSKRIT_SD_CHAPTER_FILES:
        if first <= chapter <= last:
            return name
    raise KeyError(f"BPHS chapter {chapter} is outside 1-97")


def bphs_checksum_for_chapter(chapter: int) -> str:
    """
    The checksum a witness citing this chapter should carry.

    Derived rather than copied. V1.5 hand-copied these and got three of them
    wrong — chapters 32, 41 and 75 all pointed at the checksum of a file
    that does not contain them, which would send anyone verifying the
    locator to the wrong place. A citation whose checksum points elsewhere
    is worse than one with no checksum, because it looks verified.
    """
    return BPHS_SANSKRIT_SD_FILES[bphs_file_for_chapter(chapter)]

PHALADEEPIKA_SD = SourceWitness(
    id="PHALADEEPIKA_SD",
    work="Phaladīpikā",
    traditional_author="Mantreśvara",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS transliteration)",
    edition="sanskritdocuments.org ITRANS text",
    editor_or_translator="Transliterated and proofread by Radu Canahai",
    publisher="sanskritdocuments.org (volunteer-maintained)",
    retrieved_from=("https://sanskritdocuments.org/"
                    "doc_z_misc_sociology_astrology/phaladIpika.itx"),
    retrieved_on="2026-09-27",
    checksum_if_local=(
        "6da22e782c91d1e0f4455dab333bca0bb81629e75c9eef9c5547a2819b7881bc"),
    notes=("Printed exemplar not named by the transliterator, as with the "
           "BPHS text. Volunteer licence; not vendored."),
)

JATAKA_PARIJATA_SD = SourceWitness(
    id="JATAKA_PARIJATA_SD",
    work="Jātaka Pārijāta",
    traditional_author="Vaidyanātha Dīkṣita",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS transliteration)",
    edition="sanskritdocuments.org ITRANS text",
    publisher="sanskritdocuments.org (volunteer-maintained)",
    retrieved_from=("https://sanskritdocuments.org/"
                    "doc_z_misc_sociology_astrology/jAtakapArijAtaH.itx"),
    retrieved_on="2026-09-27",
    checksum_if_local=(
        "ded534025d7712a135529d94e6f104e1e95ffa8339b715a63fd4065fe6f966d3"),
    notes=(
        "A 15th-century compendium, and it says so: several passages are "
        "explicitly introduced as quotations, e.g. the candra-yoga verse is "
        "headed `horāyām` — 'in the Horā', i.e. Varāhamihira. Where Jātaka "
        "Pārijāta quotes another work it is NOT an independent witness to "
        "that work's rule, and the evidence records which case applies. "
        "Printed exemplar not named. Volunteer licence; not vendored."),
)

# ── V1.5 passage witnesses: Sanskrit BPHS ────────────────────────────────────

# ── V1.6: the bhāva chapters, which the domain model rests on ────────────────
#
# V1.5 shipped 17 life domains with not one house mapping carrying a witness,
# and recorded that as the engine's largest remaining gap. These are the
# passages that close most of it. Chapter 11 is the signification list
# itself; 21-23 give the phala of the 10th, 11th and 12th; 24 gives the
# house-lord doctrine the whole factor type rests on.

BPHS_SA_11_BHAVAVIVEKA = SourceWitness(
    id="BPHS_SA_11.2-13_BHAVAVIVEKA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="11", verse_start="2", verse_end="13",
    locator="BPHS(Sanskrit/SD) 11.2-13",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=(
        "b2576534ea1c851a39992440e5a9f6478ecc16d80c325d3c24cdac988e121f26"),
    incipit="dehaṃ rūpaṃ ca jñānaṃ ca varṇaṃ caiva balābalam …",
    notes=(
        "THE house-signification chapter: twelve verses, one per bhāva, "
        "each listing what is to be examined from it. 11.2 lagna — body, "
        "form, knowledge, strength and weakness, happiness and sorrow, "
        "disposition. 11.3 second — wealth and grain, FAMILY (kuṭumba), the "
        "death-net, enemies, metals and gems. 11.4 third — valour, SIBLINGS "
        "(bhrātṛ), instruction, TRAVEL (prayāṇa). 11.5 fourth — vehicles, "
        "relatives, mother's comfort, treasure, LAND and HOUSE (kṣetra, "
        "gṛha). 11.6 fifth — yantra and mantra, LEARNING (vidyā), the "
        "faculty of intellect, CHILDREN (putra). 11.7 sixth — maternal "
        "uncle, ENEMIES (śatru), WOUNDS (vraṇa), stepmother. 11.8 seventh — "
        "WIFE (jāyā), road travel, TRADE (vāṇijya), recovery of what is "
        "lost. 11.9 eighth — LONGEVITY (āyus), battle, enemies, wealth of "
        "the dead. 11.10 ninth — FORTUNE (bhāgya), DHARMA, PILGRIMAGE "
        "(tīrthayātrā). 11.11 tenth — sovereignty, sky, LIVELIHOOD (vṛtti), "
        "honour, father, RESIDENCE ABROAD (pravāsa), debt. 11.12 eleventh — "
        "various goods, INCOME (āya), increase, cattle. 11.13 twelfth — "
        "EXPENDITURE (vyaya), news of enemies. Checksum is of par0110.itx."),
)

BPHS_SA_11_14_BHAVA_LORD = SourceWitness(
    id="BPHS_SA_11.14-16_BHAVA_STRENGTH",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="11", verse_start="14", verse_end="16",
    locator="BPHS(Sanskrit/SD) 11.14-16",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SA_11_BHAVAVIVEKA.checksum_if_local,
    incipit="yo yo śubhair yuto dṛṣṭo bhāvo vā patidṛṣṭayuk …",
    notes=(
        "Immediately after the signification list, and the reason the "
        "engine's house-lord and benefic-influence factors are not merely "
        "conventional: a bhāva conjoined with or aspected by benefics, or "
        "by its own lord, gives its comfort; and where the bhāva lord is "
        "destroyed, or joined with the lords of the trika houses, or "
        "afflicted, the results of that bhāva are declared lost. This is "
        "the textual basis for treating the LORD of a house as evidence "
        "about the house."),
)

BPHS_SA_21_KARMA = SourceWitness(
    id="BPHS_SA_21.1-8_KARMABHAVA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="21", verse_start="1", verse_end="8",
    locator="BPHS(Sanskrit/SD) 21.1-8",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=(
        "3c278b601d32553254214e113a22650541e17ba31b85e383f55f15992d68a446"),
    incipit="sabale karmabhāveśe svocce svāṃśe svarāśige …",
    notes=(
        "The tenth-house chapter. 21.2 is the verse that matters most for "
        "the domain model: when the karma-bhāva lord is STRONG (sabala) and "
        "in exaltation, own navāṃśa or own sign, the native is renowned and "
        "does good works. 21.3 gives the converse — a weak 10th lord means "
        "deficiency in occupation. 21.4 links the 10th lord joined with "
        "benefics to gain at the king's gate and in trade. Together these "
        "source the chain HOUSE LORD → STRENGTH → CAREER, which V1.5 could "
        "compute but could not justify. Checksum is of par2130.itx."),
)

BPHS_SA_23_VYAYA = SourceWitness(
    id="BPHS_SA_23.9-11_VYAYABHAVA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="23", verse_start="9", verse_end="11",
    locator="BPHS(Sanskrit/SD) 23.9-11",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SA_21_KARMA.checksum_if_local,
    incipit="vyayeśe pāpasaṃyukte vyaye pāpasamanvite …",
    notes=(
        "The twelfth-house chapter. 23.11: with the 12th lord joined by "
        "malefics, the 12th occupied by malefics and aspected by a malefic, "
        "one goes `deśād deśāntaraṃ` — from one country to another. That is "
        "the witness for FOREIGN_RESIDENCE at the 12th, which V1.5 assumed "
        "from convention. 23.10 gives mokṣa from a benefic 12th with its "
        "lord exalted, supporting the 12th as a secondary house for "
        "SPIRITUALITY."),
)

BPHS_SA_24_BHAVESHA = SourceWitness(
    id="BPHS_SA_24_BHAVESHAPHALA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="24", verse_start="1",
    locator="BPHS(Sanskrit/SD) 24",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SA_21_KARMA.checksum_if_local,
    incipit="lagneśe lagnage dehasukhabhāg bhujavikramī …",
    notes=(
        "The bhāveśa-phala chapter: each house lord placed in each of the "
        "twelve houses, house by house. This is what makes HOUSE_LORD a "
        "distinct evidence type rather than a restatement of the house. "
        "Examples the domain model uses: 24.5 the Lagna lord in the 5th "
        "gives middling happiness from children and loss of the firstborn; "
        "24.7 the Lagna lord in the 7th with a malefic, the wife does not "
        "live; 24.10 the Lagna lord in the 10th, honoured by the king and "
        "of self-earned wealth; 24.11 the Lagna lord in the 11th, always "
        "with gains."),
)

BPHS_SA_32_BHAVA_KARAKA = SourceWitness(
    id="BPHS_SA_32.22-24_BHAVA_KARAKA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="32", verse_start="22", verse_end="24",
    locator="BPHS(Sanskrit/SD) 32.22-24",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=(
        "dcfb34a678410eb5e4a26dba5323470e9ef67fa8acf6216c694d8b1ee52f5f92"),
    incipit="athāhaṃ kārakān vakṣye kheṭabhāvavaśād dvija …",
    notes=(
        "THE PASSAGE V1.5 MISSED, and it changes the putrakāraka finding. "
        "Introduced in its own words as kārakas `kheṭa-bhāva-vaśāt` — by "
        "graha AND bhāva together, a third scheme distinct from both the "
        "Jaimini cara kārakas of 32.1-17 and the sthira kārakas of "
        "32.18-21. It gives: the Sun in the 9th for the father; the Moon in "
        "the 4th for the mother; Mars in the 3rd for the brother; Mercury "
        "in the 6th for the maternal uncle; JUPITER (devejya) IN THE 5TH "
        "FOR THE SON; Venus in the 7th for the wife; and Saturn in the 8th "
        "for death. So BPHS states the familiar attribution of the "
        "putrakāraka to Jupiter, four verses after the sthira list that "
        "assigns the son to Saturn, and it assigns Saturn to death — which "
        "is also the modern reading."),
)

BPHS_SA_34_YOGAKARAKA = SourceWitness(
    id="BPHS_SA_34.11-15_YOGAKARAKA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="34", verse_start="11", verse_end="15",
    locator="BPHS(Sanskrit/SD) 34.11-15",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANSKRIT_SD.checksum_if_local,
    incipit="kendrakoṇapatī syātāṃ parasparagṛhopagau …",
    notes=(
        "The generic Rājayoga verse, and the one the engine's ~36 generated "
        "raja_yoga rules actually rest on. 34.11-12 enumerate THREE modes of "
        "relationship between a kendra lord and a trikoṇa lord: each in the "
        "other's house (exchange), both in one sign (conjunction), or mutual "
        "FULL aspect (pūrṇa-dṛṣṭyā). 34.13 makes a graha owning both a kendra "
        "and a trikoṇa especially a yogakāraka. 34.15 states an EXCEPTION: "
        "when those same lords also own dusthanas, their mere relationship "
        "does not give the yoga. 34.2-4 give the kendrādhipatya doṣa and the "
        "malefic effect of the 3rd, 6th and 11th lords."),
)

BPHS_SA_32_KARAKA = SourceWitness(
    id="BPHS_SA_32.18-21_STHIRA_KARAKA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="32", verse_start="18", verse_end="21",
    locator="BPHS(Sanskrit/SD) 32.18-21",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    # Chapter 32 lives in par3140.itx. V1.5 recorded par2130's checksum here,
    # which was wrong and would have sent anyone verifying the locator to the
    # wrong file. Caught in V1.6 by the test that cross-checks every witness
    # against BPHS_SANSKRIT_SD_CHAPTER_FILES.
    checksum_if_local=(
        "dcfb34a678410eb5e4a26dba5323470e9ef67fa8acf6216c694d8b1ee52f5f92"),
    incipit="sa pitṛkārako jñeyo yo balī raviśukrayoḥ …",
    notes=(
        "The sthira (fixed) kārakas. NOT the popular naisargika list: what "
        "the verses give is a list of RELATIVES. The stronger of Sun and "
        "Venus is the father-kāraka (32.18); the stronger of Moon and Mars "
        "the mother (32.19); from Mars, sister and brother-in-law (32.19); "
        "from Mercury, maternal kin (32.20); from Jupiter, the paternal "
        "grandfather; from Venus, the spouse; and from Saturn, the son "
        "(32.20, putraḥ śanaiścarāt). The last contradicts the modern "
        "attribution of putrakāraka to Jupiter. Verses 1-17 of the same "
        "chapter give the Jaimini CARA kārakas, assigned by degree, which "
        "this engine does not compute. Checksum is of par2130.itx."),
)

BPHS_SA_36_3_GAJAKESARI = SourceWitness(
    id="BPHS_SA_36.3_GAJAKESARI",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="36", verse_start="3", verse_end="4",
    locator="BPHS(Sanskrit/SD) 36.3",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANSKRIT_SD.checksum_if_local,
    incipit="kendre devagurau lagnāc candrād vā śubhadṛgyute …",
    notes=("Jupiter in a kendra FROM THE LAGNA OR FROM THE MOON, conjoined or "
           "aspected by benefics, and free of debilitation, combustion (asta) "
           "and enemy signs."),
)

BPHS_SA_36_5_AMALA = SourceWitness(
    id="BPHS_SA_36.5_AMALA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="36", verse_start="5", verse_end="6",
    locator="BPHS(Sanskrit/SD) 36.5",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANSKRIT_SD.checksum_if_local,
    incipit="daśame 'ṅgāt tathā candrāt kevalaiś ca śubhair yute …",
    notes=("Benefics ALONE (kevalaiḥ) in the 10th from the Lagna or from the "
           "Moon. The exclusivity is explicit in the word kevalaiḥ."),
)

BPHS_SA_36_27_LAKSHMI = SourceWitness(
    id="BPHS_SA_36.27_LAKSHMI",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="36", verse_start="27", verse_end="28",
    locator="BPHS(Sanskrit/SD) 36.27",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANSKRIT_SD.checksum_if_local,
    incipit="kendre mūlatrikoṇasthe bhāgyeśe vā svoccage …",
    notes=("The 9th lord in a kendra, in moolatrikona, or in own sign or "
           "exaltation, WITH a strong Lagna lord. Note this is a different "
           "rule from Phaladīpikā 6.21, which requires the 9th lord AND "
           "Venus; the two are registered as a conflict, not merged."),
)

BPHS_SA_36_37_LAGNADHIYOGA = SourceWitness(
    id="BPHS_SA_36.37_LAGNADHIYOGA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="36", verse_start="37",
    locator="BPHS(Sanskrit/SD) 36.37",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANSKRIT_SD.checksum_if_local,
    incipit="lagnān madāṣṭagaiḥ saumyaiḥ pāpadṛgyogavarjitaiḥ …",
    notes=("Lagnādhiyoga: benefics in the 7th (mada) and 8th from the LAGNA, "
           "free of malefic aspect or conjunction. Two houses, where Jātaka "
           "Pārijāta 114 gives three (6th, 7th, 8th) — a genuine variant."),
)

BPHS_SA_37_5_ADHIYOGA = SourceWitness(
    id="BPHS_SA_37.5_ADHIYOGA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="37", verse_start="5",
    locator="BPHS(Sanskrit/SD) 37.5",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANSKRIT_SD.checksum_if_local,
    incipit="candrād randhrārikāmasthai saumyaiḥ syād adhiyogakaḥ …",
    notes=(
        "Benefics in the 8th (randhra), 6th (ari) and 7th (kāma) FROM THE "
        "MOON. Independent of Bṛhajjātaka 13.2, which states the same rule "
        "with different vocabulary (smara/ari/nidhana). Two works, two "
        "wordings, one rule — this is what a genuine second witness looks "
        "like, as against a quotation."),
)

BPHS_SA_37_7_CANDRA_YOGAS = SourceWitness(
    id="BPHS_SA_37.7_CANDRA_YOGAS",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="37", verse_start="7", verse_end="10",
    locator="BPHS(Sanskrit/SD) 37.7",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANSKRIT_SD.checksum_if_local,
    incipit="candrāt svāntyobhayasthe hi grahe sūryaṃ binā kramāt …",
    notes=(
        "Sunaphā, Anaphā and Durudharā, from grahas in the 2nd, 12th or both "
        "from the Moon. THE ONLY EXCLUSION IS THE SUN — sūryaṃ binā. The "
        "wording differs from Bṛhajjātaka 13.3's hitvārkaṃ, so this is an "
        "independent witness to the same exclusion, and it settles a question "
        "left open in V1.3."),
)

BPHS_SA_37_11_KEMADRUMA = SourceWitness(
    id="BPHS_SA_37.11_KEMADRUMA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="37", verse_start="11", verse_end="12",
    locator="BPHS(Sanskrit/SD) 37.11",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANSKRIT_SD.checksum_if_local,
    incipit="candrād ādyadhanāntyastho vinā bhānuṃ na ced grahaḥ …",
    notes=(
        "Kemadruma arises when there is no graha OTHER THAN THE SUN in the "
        "1st, 2nd or 12th from the Moon, AND no graha OTHER THAN THE MOON in "
        "a kendra from the Lagna. Two consequences for the engine, both "
        "recorded in the V1.5 audit: the kendra-from-Lagna clause is "
        "textually supported, and the Moon's own kendra placement is "
        "explicitly EXCLUDED from cancelling — vinā candraṃ — which is the "
        "opposite of what the engine implements."),
)

BPHS_SA_38_1_RAVI_YOGAS = SourceWitness(
    id="BPHS_SA_38.1_RAVI_YOGAS",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="38", verse_start="1", verse_end="3",
    locator="BPHS(Sanskrit/SD) 38.1",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANSKRIT_SD.checksum_if_local,
    incipit="sūryāt svantyobhayasthaiś ca vinā candraṃ kujādibhiḥ …",
    notes=("Veśi, Vośi and Ubhayacarī, from the 2nd, 12th or both from the "
           "SUN. The exclusion here is THE MOON (vinā candraṃ), and the "
           "grahas are enumerated as kujādi — 'Mars and the rest' — which "
           "reads naturally as the five tārā grahas and so does not include "
           "the nodes."),
)

BPHS_SA_39_19_VIPAREETA = SourceWitness(
    id="BPHS_SA_39.19-20_DUSTHANA_LORDS",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="39", verse_start="19", verse_end="20",
    locator="BPHS(Sanskrit/SD) 39.19-20",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=BPHS_SANSKRIT_SD.checksum_if_local,
    incipit="ṣaṣṭhāṣṭamavyayādhīśā nīcasthā ripubhe 'sthagāḥ …",
    notes=(
        "BPHS's own dusthana-lord rule: the lords of the 6th, 8th and 12th "
        "debilitated or in enemy signs, WITH the Lagna lord in own sign or "
        "exaltation aspecting the Lagna, gives royalty. This is NOT the "
        "Harṣa/Sarala/Vimala triad — it is a single combined condition and "
        "the names do not occur anywhere in this witness. Those names are "
        "Phaladīpikā's; see PD_6.57."),
)

BPHS_SA_41_28_RAJAYOGA = SourceWitness(
    id="BPHS_SA_41.28_KENDRA_TRIKONA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="41", verse_start="28",
    locator="BPHS(Sanskrit/SD) 41.28",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=bphs_checksum_for_chapter(41),
    incipit="viṣṇusthānaṃ ca kendraṃ syāl lakṣmīsthānaṃ trikoṇakam …",
    notes=("'The kendra is Viṣṇu's place, the trikoṇa Lakṣmī's; from the "
           "relationship (sambandha) of their lords comes Rājayoga, as "
           "stated before.' The back-reference is to 34.11-13. Together "
           "these two passages are the actual source of the engine's "
           "generated kendra-trikona Raja Yogas."),
)

BPHS_SA_75_1_MAHAPURUSHA = SourceWitness(
    id="BPHS_SA_75.1_MAHAPURUSHA",
    work="Bṛhat Parāśara Horā Śāstra", traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="75", verse_start="1", verse_end="2",
    locator="BPHS(Sanskrit/SD) 75.1-2",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=bphs_checksum_for_chapter(75),
    incipit="svabhoccagatakendrasthair balibhiś ca kujādibhiḥ …",
    notes=(
        "Ruchaka, Bhadra, Haṃsa, Mālavya and Śaśa, from Mars, Mercury, "
        "Jupiter, Venus and Saturn respectively, in OWN SIGN OR EXALTATION, "
        "in a kendra, AND STRONG (balibhiḥ). The engine's ch.75 citation is "
        "the one legacy citation that turned out to name the right chapter. "
        "Checksum is of par7180.itx, the file containing ch.75."),
)

# ── V1.5 passage witnesses: Phaladīpikā ──────────────────────────────────────

PD_6_21_LAKSHMI = SourceWitness(
    id="PD_6.21_LAKSHMI",
    work="Phaladīpikā", traditional_author="Mantreśvara",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=PHALADEEPIKA_SD.edition,
    chapter="6", verse_start="21",
    locator="Phaladīpikā(SD) 6.21",
    retrieved_from=PHALADEEPIKA_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=PHALADEEPIKA_SD.checksum_if_local,
    incipit="svarkṣocce yadi koṇakaṇṭakayutau bhāgyeśaśukrāv ubhau …",
    notes=("Lakṣmī yoga: the 9th lord AND Venus, BOTH in own sign or "
           "exaltation and BOTH in a trikoṇa or kendra. The same verse gives "
           "Gaurī yoga for the Moon so placed and aspected by Jupiter."),
)

PD_6_26_SARASVATI = SourceWitness(
    id="PD_6.26_SARASVATI",
    work="Phaladīpikā", traditional_author="Mantreśvara",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=PHALADEEPIKA_SD.edition,
    chapter="6", verse_start="26",
    locator="Phaladīpikā(SD) 6.26",
    retrieved_from=PHALADEEPIKA_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=PHALADEEPIKA_SD.checksum_if_local,
    incipit="śukravākpatisudhākarātmajaiḥ kendrakoṇasahitair dvitīyagaiḥ …",
    notes=("Sarasvatī yoga: Venus, Jupiter and Mercury in kendras, trikoṇas "
           "or the 2nd, AND Jupiter additionally in own, exalted or friendly "
           "sign and strong (vīryage)."),
)

PD_6_57_VIPAREETA = SourceWitness(
    id="PD_6.57_TWELVE_YOGAS",
    work="Phaladīpikā", traditional_author="Mantreśvara",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=PHALADEEPIKA_SD.edition,
    chapter="6", verse_start="57", verse_end="67",
    locator="Phaladīpikā(SD) 6.57",
    retrieved_from=PHALADEEPIKA_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=PHALADEEPIKA_SD.checksum_if_local,
    incipit="duḥsthair bhāvagṛheśvarair aśubhasaṃyuktekṣitair vā kramād …",
    notes=(
        "The twelve bhāva-lord yogas, named in bhāva order: avayoga (1), "
        "niḥsva (2), mṛti (3), kuhū (4), pāmara (5), HARṢA (6), duṣkṛti (7), "
        "SARALA (8), nirbhāgya (9), duryoga (10), daridra (11), VIMALA (12). "
        "The condition is that the bhāva lord be duḥstha, or conjoined with "
        "or aspected by malefics. The phala verses follow at 6.58-69. This "
        "is the actual home of the three names the engine ships as "
        "'Vipareeta Raja Yoga'; they are not in BPHS under those names."),
)

# ── V1.5 passage witnesses: Jātaka Pārijāta ──────────────────────────────────

JP_59_MAHAPURUSHA = SourceWitness(
    id="JP_59_MAHAPURUSHA",
    work="Jātaka Pārijāta", traditional_author="Vaidyanātha Dīkṣita",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=JATAKA_PARIJATA_SD.edition,
    verse_start="59", locator="Jātaka Pārijāta(SD) v.59",
    retrieved_from=JATAKA_PARIJATA_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=JATAKA_PARIJATA_SD.checksum_if_local,
    incipit="mūlatrikoṇanijatuṅgagṛhopagātā … baliṣṭhāḥ kendrasthitā yadā …",
    notes=(
        "The Pañca Mahāpuruṣa yogas, introduced under its own heading rather "
        "than as a quotation. Gives THREE dignities — mūlatrikoṇa, own sign "
        "and exaltation — where BPHS 75.1 gives two, so the engine's "
        "inclusion of moolatrikona is attested here. Agrees with BPHS on the "
        "strength requirement: baliṣṭhāḥ here, balibhiḥ there."),
)

JP_114_LAGNADHIYOGA = SourceWitness(
    id="JP_113-114_ADHIYOGA",
    work="Jātaka Pārijāta", traditional_author="Vaidyanātha Dīkṣita",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=JATAKA_PARIJATA_SD.edition,
    verse_start="113", verse_end="114",
    locator="Jātaka Pārijāta(SD) vv.113-114",
    retrieved_from=JATAKA_PARIJATA_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=JATAKA_PARIJATA_SD.checksum_if_local,
    incipit="saumyaiḥ smarārinidhaneṣv adhiyoga … lagnād aridyūnagṛhāṣṭamasthaiḥ …",
    notes=(
        "Distinguishes the two explicitly, by heading: candrādhiyoga (113, "
        "benefics in the 6th/7th/8th from the Moon) and lagnādhiyoga (114, "
        "the same three houses from the Lagna, with the added requirement "
        "that the benefics not be conjoined with or aspected by malefics). "
        "The vocabulary of 113 — smara, ari, nidhana — is Bṛhajjātaka 13.2's "
        "word for word, so for the candra form this is a quotation and NOT "
        "an independent witness. For the lagna form it differs from BPHS "
        "36.37, which gives only two houses."),
)

JP_116_GAJAKESARI = SourceWitness(
    id="JP_116_GAJAKESARI",
    work="Jātaka Pārijāta", traditional_author="Vaidyanātha Dīkṣita",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=JATAKA_PARIJATA_SD.edition,
    verse_start="116", locator="Jātaka Pārijāta(SD) v.116",
    retrieved_from=JATAKA_PARIJATA_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=JATAKA_PARIJATA_SD.checksum_if_local,
    incipit="kendrasthite devagurau mṛgāṅkād … nīcāstahīnair gajakesarī syāt",
    notes=("Jupiter in a kendra FROM THE MOON only, where BPHS 36.3 allows "
           "the Lagna as well. Both require freedom from debilitation and "
           "combustion; BPHS adds enemy signs."),
)

JP_83_CANDRA_YOGAS = SourceWitness(
    id="JP_83_CANDRA_YOGAS_QUOTING_HORA",
    work="Jātaka Pārijāta", traditional_author="Vaidyanātha Dīkṣita",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=JATAKA_PARIJATA_SD.edition,
    verse_start="83", locator="Jātaka Pārijāta(SD) v.83",
    retrieved_from=JATAKA_PARIJATA_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=JATAKA_PARIJATA_SD.checksum_if_local,
    incipit="horāyām | hitvārkaṃ sunaphānaphādurudhurā svāntyobhayatthair grahaḥ …",
    notes=(
        "REGISTERED AS A QUOTATION, NOT AS AN INDEPENDENT WITNESS. The verse "
        "is introduced by the word horāyām, 'in the Horā', and reproduces "
        "Bṛhajjātaka 13.3 including its closing judgement that the kendra/"
        "navāṃśa opinion is ukti-prasiddhā na te — not well established. "
        "Its value is that it confirms how the Bṛhajjātaka verse was read by "
        "a later authority, which is exactly the question the V1.3 review "
        "queue raised about the Kemadruma cancellations."),
)

# ── V1.7 Parts 27-29: the varga-domain and gochara passages ─────────────────
#
# V1.6 reported "0 of 11 varga→domain mappings sourced" and, in its own
# words, "no passage anywhere assigns a divisional chart to a life area".
#
# THAT WAS WRONG, AND WRONG IN THE NOW-FAMILIAR WAY. The passage is BPHS
# chapter 7, `vargavivekādhyāya`, eight verses that do nothing else. It sits
# in par0110.itx — a file this engine has held, checksummed, since V1.5 —
# one chapter after the ṣoḍaśavarga chapter V1.6 did read and correctly
# reported as giving only the computations.
#
# The pattern is the same one RESOLVED_UNAVAILABLE_WORKS records for whole
# works, at the scale of a chapter: the search stopped at the chapter whose
# title matched, and the answer was in the next one.

BPHS_SA_7_VARGAVIVEKA = SourceWitness(
    id="BPHS_SA_7.1-8_VARGAVIVEKA",
    work="Bṛhat Parāśara Horā Śāstra",
    traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=BPHS_SANSKRIT_SD.edition,
    chapter="7", verse_start="1", verse_end="8",
    locator="BPHS(Sanskrit/SD) 7.1-8",
    retrieved_from=BPHS_SANSKRIT_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=bphs_checksum_for_chapter(7),
    incipit="atha ṣoḍaśavargeṣu vivekaṃ ca vadāmyaham …",
    notes=(
        "THE varga-signification passage, and the answer to V1.6's largest "
        "open gap. Each division is assigned a subject in a single "
        "compound: lagne dehasya (D1 — the body), horāyāṃ sampadādikam "
        "(D2 — WEALTH), dreṣkāṇe bhrātṛjaṃ saukhyam (D3 — happiness from "
        "SIBLINGS), turyāṃśe bhāgyacintanam (D4 — FORTUNE, bhāgya), "
        "putrapautrādikānāṃ cintanaṃ saptamāṃśake (D7 — CHILDREN and "
        "grandchildren), navamāṃśe kalatrāṇām (D9 — the SPOUSE), "
        "daśamāṃśe mahatphalam (D10 — 'great fruit'), dvādaśāṃśe pitroḥ "
        "(D12 — PARENTS), ṣoḍaśāṃśake sukhāsukhasya vijñānaṃ vāhanānām "
        "(D16 — comfort and discomfort of VEHICLES), upāsanāyā vijñānaṃ "
        "viṃśatibhāgake (D20 — WORSHIP), vidyāyā vedabāhvaṃśe (D24 — "
        "LEARNING), bhāṃśe balābalam (D27 — strength and weakness), "
        "triṃśāṃśake riṣṭaphalam (D30 — the fruit of AFFLICTION), "
        "khavedāṃśe śubhāśubham (D40 — the auspicious and inauspicious), "
        "akṣavedāṃśake caiva ṣaṣṭyaṃśe akhilam īkṣayet (D45 and D60 — one "
        "should examine EVERYTHING). Verses 6-8 add Garga's rule that a "
        "bhāva whose lord falls in a cruel ṣaṣṭyaṃśa is destroyed, and one "
        "whose lord falls in a benefic kalāṃśa grows. "
        "TWO OF THE ASSIGNMENTS ARE NOT WHAT MODERN PRACTICE USES. D4 is "
        "given for bhāgya, fortune, not for property; D10 is given for "
        "mahat-phala, 'great fruit', which Santhanam renders 'power and "
        "position' and which is not the same claim as 'profession'. See "
        "VARGA_DOMAIN_AUDIT.md."),
)

BPHS_EN_7_VARGAVIVEKA = SourceWitness(
    id="BPHS_EN_7.1-8_VARGAVIVEKA",
    work="Bṛhat Parāśara Horā Śāstra",
    traditional_author="Parāśara (attributed)",
    authority=SourceAuthority.TRANSLATION,
    source_type=BPHS_SANTHANAM_V1.source_type,
    language="English", edition=BPHS_SANTHANAM_V1.edition,
    editor_or_translator=BPHS_SANTHANAM_V1.editor_or_translator,
    publisher=BPHS_SANTHANAM_V1.publisher,
    volume=1, chapter="7", verse_start="1", verse_end="8",
    locator="BPHS(Santhanam) 7.1-8",
    retrieved_on="2026-09-27",
    incipit="USE OF THE 16 DIVISIONS: I now explain the use of these …",
    notes=(
        "The translation of the passage above, recorded SEPARATELY because "
        "a translator's reading of an ambiguous compound is an "
        "interpretation. Two readings matter here. Santhanam renders "
        "daśamāṃśe mahatphalam as 'power (and position)' and glosses it in "
        "a note as 'i.e. livelihood etc.' — the gloss is the translator's, "
        "not the verse's. He renders turyāṃśe bhāgyacintanam as 'fortunes "
        "from Chaturthamsa', which is literal; the modern reading of D4 as "
        "the property chart appears in neither."),
)

# ── Gochara (Part 28) ───────────────────────────────────────────────────────
#
# V1.6 refused transit evidence in strict synthesis on the ground that
# "Gochara has no witness". It has two, in a text this engine already holds.
# What it does NOT have is a witness for the rule the engine implements,
# which is a different and much more precise finding. See GOCHARA_AUDIT.md.

PD_26_GOCHARA = SourceWitness(
    id="PD_SA_26.1-17_GOCHARAPHALA",
    work="Phaladīpikā", traditional_author="Mantreśvara",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=PHALADEEPIKA_SD.edition,
    chapter="26", verse_start="1", verse_end="17",
    locator="Phaladīpikā(SD) 26.1-17",
    retrieved_from=PHALADEEPIKA_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=PHALADEEPIKA_SD.checksum_if_local,
    incipit="sarveṣu lagneṣv api satsu candralagnaṃ pradhānaṃ khalu "
            "gocareṣu …",
    notes=(
        "The gocara chapter, and its first verse settles the reference "
        "frame outright: though all the lagnas exist, in transits the "
        "CANDRA-LAGNA is primary, and the results are to be declared from "
        "that sign. 26.2 gives the favourable houses per graha counted from "
        "it; 26.3-8 make each of them conditional on VEDHA, obstruction by "
        "a graha in a specified counter-house; 26.9 onward give the effect "
        "of each graha in each of the twelve. "
        "The engine implements none of this. Its transit evidence records "
        "that a graha occupies a house, with no favourable-house list and "
        "no vedha check, so this passage locates a SOURCE without "
        "validating the IMPLEMENTATION."),
)

PD_20_GOCHARA_FROM_LAGNA = SourceWitness(
    id="PD_SA_20.34-37_DASHESHA_GOCHARA",
    work="Phaladīpikā", traditional_author="Mantreśvara",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=PHALADEEPIKA_SD.edition,
    chapter="20", verse_start="34", verse_end="37",
    locator="Phaladīpikā(SD) 20.34-37",
    retrieved_from=PHALADEEPIKA_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=PHALADEEPIKA_SD.checksum_if_local,
    incipit="yadbhāvago gocarato vilagnāt daśeśvaraḥ svoccasuhṛdgṛhasthaḥ …",
    notes=(
        "Transit counted from the LAGNA rather than the Moon, and the "
        "closest thing in any located text to the hierarchy V1.5 built. "
        "20.34: whichever bhāva the DAŚĀ LORD reaches by transit from the "
        "lagna, being in its own sign, exaltation or a friend's house, it "
        "nourishes that bhāva — provided it was also strong at birth. "
        "20.35: if that same lord was weak at birth, or is combust, "
        "debilitated or in an enemy's house, whichever bhāva it reaches by "
        "transit it destroys. "
        "The transiting graha is not any graha: it is the running daśā "
        "lord, and its effect is conditioned on its NATAL strength. That is "
        "Natal → Daśā → Transit, stated in a text. The engine's transit "
        "layer applies neither condition, so this is a source located "
        "AGAINST the current implementation rather than for it."),
)

# ── Gochara, second edition (V1.8 Parts 1, 10, 11) ──────────────────────────
#
# V1.7 located the gochara verses and stopped. V1.8 had to READ them, and
# reading them exposed something locating them could not: the digital witness
# is corrupt in two places, both inside the vedha table.
#
# Phaladīpikā 26.6 pairs Mercury's six favourable houses with six vedha
# houses positionally. The ITRANS text ends the list with `prApti`, the 11th
# — which would pair the 11th with itself and assert that Mercury's transit
# of the 11th is obstructed by a graha in the 11th, where Mercury already is.
# THE CORRUPT READING IS SELF-REFUTING, and it can be excluded on internal
# grounds before any second witness is consulted. 26.8 has a lesser slip,
# `vari` (water, the 4th) where the sense requires `ari` (enemy, the 6th).
#
# The second edition supplies both correct readings. It is a second edition
# of the SAME WORK, so it settles a READING and does not constitute
# independent doctrinal support — a distinction `WitnessAgreement` exists to
# carry, because collapsing it either way would misreport the evidence.

PD_SASTRI_1950 = SourceWitness(
    id="PD_SASTRI_1950",
    work="Phaladīpikā", traditional_author="Mantreśvara",
    authority=SourceAuthority.TRANSLATION,
    source_type=SourceType.DIGITISED_PRINT,
    language="Sanskrit (Devanāgarī) with English translation",
    edition="Adhyāyas I-XXVIII, 2nd edition",
    editor_or_translator="Paṇḍitabhūṣaṇa V. Subrahmanya Sastri",
    publication_year=1950,
    retrieved_from=("https://archive.org/details/"
                    "Phaladeepika2ndEd.1950ByVSubrahmanyaSastri"),
    retrieved_on="2026-09-28",
    checksum_if_local=(
        "930352963e4fa4a793bad3d17a842489443f313d280691623d5fe156f78749c2"),
    notes=(
        "Scanned print, public domain. The scan carries BOTH the Devanāgarī "
        "and a facing English translation; only the translation survives "
        "OCR legibly, as the Devanāgarī OCRs to noise. So this witness is "
        "registered at TRANSLATION authority and not at Sanskrit tier: the "
        "Sanskrit is physically present in the scan and has NOT been read, "
        "which is a different claim from it being unavailable. Reading it "
        "requires a human with the page images — see the Part 11 review "
        "workflow in SOURCE_REVIEW.md. "
        "Only locators and short paraphrases are taken into the engine; no "
        "translated passage is reproduced at length."),
)

PD_26_VEDHA_TABLE = SourceWitness(
    id="PD_SA_26.2-8_GOCHARA_VEDHA",
    work="Phaladīpikā", traditional_author="Mantreśvara",
    authority=SourceAuthority.PRINTED_SANSKRIT_EDITION,
    source_type=SourceType.DIGITAL_CRITICAL_TEXT,
    language="Sanskrit (ITRANS)", edition=PHALADEEPIKA_SD.edition,
    chapter="26", verse_start="2", verse_end="8",
    locator="Phaladīpikā(SD) 26.2-8",
    retrieved_from=PHALADEEPIKA_SD.retrieved_from, retrieved_on="2026-09-27",
    checksum_if_local=PHALADEEPIKA_SD.checksum_if_local,
    incipit="sūryaḥ ṣaṭtridaśasthitas tridaśaṣaṭsaptādyagaś candramāḥ …",
    notes=(
        "The transit table itself. 26.2 lists each graha's favourable "
        "houses from the Moon and closes with two general clauses: "
        "`sarve 'py upāntasthitāḥ`, ALL grahas are favourable in the 11th, "
        "and `tigmāṃśuvad bhoginau`, the two nodes behave as the Sun. "
        "26.3-8 then restate each list and append its vedha houses "
        "POSITIONALLY, so verse 2 and verses 3-8 cross-check each other — "
        "which is how the ambiguous syllable in 26.2's Mercury list was "
        "resolved to the 2nd without guessing. "
        "Two vedha exemptions are stated and both are reciprocal pairs: "
        "the Sun suffers no vedha from Saturn and Saturn none from the Sun "
        "(26.3, 26.5 — `vyarkibhiḥ`, father and son), the Moon none from "
        "Mercury and Mercury none from the Moon (26.4, 26.6 — `vibudhaiḥ`, "
        "`vividhubhiḥ`). Nothing generalises these to other pairs."),
)

PD_EN_26_SASTRI = SourceWitness(
    id="PD_EN_26.1-8_SASTRI",
    work="Phaladīpikā", traditional_author="Mantreśvara",
    authority=SourceAuthority.TRANSLATION,
    source_type=SourceType.DIGITISED_PRINT,
    language="English", edition=PD_SASTRI_1950.edition,
    editor_or_translator=PD_SASTRI_1950.editor_or_translator,
    publication_year=1950, chapter="26", verse_start="1", verse_end="8",
    locator="Phaladīpikā (Sastri 1950) 26.1-8",
    retrieved_from=PD_SASTRI_1950.retrieved_from, retrieved_on="2026-09-28",
    checksum_if_local=PD_SASTRI_1950.checksum_if_local,
    notes=(
        "Agrees with the ITRANS witness on the reference frame, on all "
        "seven favourable-house lists, on 39 of the 41 vedha pairs and on "
        "both exemptions. It differs at exactly the two points where the "
        "ITRANS reading is defective, giving the 12th for Mercury's last "
        "vedha and the 6th for Venus's eighth. "
        "Sastri also states the nodes' favourable houses by reference to "
        "the Sun, as 26.2 does, and gives them NO vedha table — so the gap "
        "in the engine's node rules is a gap in both witnesses, not a "
        "failure to read one of them."),
)

PD_EN_20_SASTRI = SourceWitness(
    id="PD_EN_20.34-37_SASTRI",
    work="Phaladīpikā", traditional_author="Mantreśvara",
    authority=SourceAuthority.TRANSLATION,
    source_type=SourceType.DIGITISED_PRINT,
    language="English", edition=PD_SASTRI_1950.edition,
    editor_or_translator=PD_SASTRI_1950.editor_or_translator,
    publication_year=1950, chapter="20", verse_start="34", verse_end="37",
    locator="Phaladīpikā (Sastri 1950) 20.34-37",
    retrieved_from=PD_SASTRI_1950.retrieved_from, retrieved_on="2026-09-28",
    checksum_if_local=PD_SASTRI_1950.checksum_if_local,
    notes=(
        "Confirms every clause of 20.34-35 that the rule depends on: the "
        "transiting graha must be the lord of the daśā in progress; its "
        "transited sign must be its own, its exaltation or a friend's; the "
        "bhāva nourished is counted FROM THE LAGNA; and the whole result "
        "is conditioned on the graha being `endowed with full strength at "
        "the birth time as well`. "
        "20.35's destructive form carries NO transit-dignity condition — a "
        "daśā lord weak, combust, debilitated or in an enemy's sign AT "
        "BIRTH damages whichever bhāva it transits. That asymmetry is in "
        "both witnesses and is implemented as stated rather than made "
        "symmetric for tidiness."),
)

ALL_WITNESSES: tuple[SourceWitness, ...] = (
    BRIHAJJATAKA_GRETIL,
    BPHS_SANTHANAM_V1,
    BPHS_SANTHANAM_V2,
    BPHS_27_SHADBALA,
    BPHS_66_ASHTAKAVARGA,
    BJ_1_6_NAVAMSHA,
    BJ_1_7_TRIMSHAMSHA,
    BJ_13_2_ADHIYOGA,
    BJ_13_3_CANDRA_YOGAS,
    BJ_12_NABHASA,
    # V1.5 corpora
    BPHS_SANSKRIT_SD,
    PHALADEEPIKA_SD,
    JATAKA_PARIJATA_SD,
    # V1.5 passages
    BPHS_SA_11_BHAVAVIVEKA,
    BPHS_SA_11_14_BHAVA_LORD,
    # V1.7 passages (Parts 27-29)
    BPHS_SA_7_VARGAVIVEKA,
    BPHS_EN_7_VARGAVIVEKA,
    PD_26_GOCHARA,
    PD_20_GOCHARA_FROM_LAGNA,
    # V1.8 gochara: the table, and the second edition that repaired it
    PD_SASTRI_1950,
    PD_26_VEDHA_TABLE,
    PD_EN_26_SASTRI,
    PD_EN_20_SASTRI,
    BPHS_SA_21_KARMA,
    BPHS_SA_23_VYAYA,
    BPHS_SA_24_BHAVESHA,
    BPHS_SA_32_KARAKA,
    BPHS_SA_32_BHAVA_KARAKA,
    BPHS_SA_34_YOGAKARAKA,
    BPHS_SA_36_3_GAJAKESARI,
    BPHS_SA_36_5_AMALA,
    BPHS_SA_36_27_LAKSHMI,
    BPHS_SA_36_37_LAGNADHIYOGA,
    BPHS_SA_37_5_ADHIYOGA,
    BPHS_SA_37_7_CANDRA_YOGAS,
    BPHS_SA_37_11_KEMADRUMA,
    BPHS_SA_38_1_RAVI_YOGAS,
    BPHS_SA_39_19_VIPAREETA,
    BPHS_SA_41_28_RAJAYOGA,
    BPHS_SA_75_1_MAHAPURUSHA,
    PD_6_21_LAKSHMI,
    PD_6_26_SARASVATI,
    PD_6_57_VIPAREETA,
    JP_59_MAHAPURUSHA,
    JP_114_LAGNADHIYOGA,
    JP_116_GAJAKESARI,
    JP_83_CANDRA_YOGAS,
)

# Witnesses that reproduce another work's verse rather than attesting the rule
# independently. `_has_two_independent_witnesses` judges independence by work,
# which is right in general and wrong for a compendium that quotes its
# sources by name — so the quotations are listed and excluded explicitly.
QUOTATION_WITNESSES: dict[str, str] = {
    JP_83_CANDRA_YOGAS.id: BJ_13_3_CANDRA_YOGAS.id,
}


# ── Works the engine cites but has NO witness for ────────────────────────────
# This table is the honest counterpart to the one above. It exists so that the
# absence of evidence is itself recorded data, rather than something a reader
# has to notice by the citation not being there.

UNAVAILABLE_WORKS: dict[str, dict] = {
    "SARAVALI": {
        "work": "Sārāvalī",
        "traditional_author": "Kalyāṇavarman",
        "cited_by_rules": False,
        # V1.8 Part 11: RECLASSIFIED. The work is not unavailable — it is
        # held in full and unread. `engine.sources.review` carries the real
        # state (RETRIEVED_IMAGE_ONLY / TEXT_NOT_REVIEWED) and the workflow
        # that would change it. This entry stays so that a reader who
        # arrives here is sent there rather than concluding the work could
        # not be obtained.
        "superseded_by": "engine.sources.review.REVIEW_TASKS['Sārāvalī']",
        "availability": "RETRIEVED_IMAGE_ONLY",
        "review_stage": "TEXT_NOT_REVIEWED",
        "why_unavailable": (
            "RETRIEVED BUT NOT READ. A 1928 Sanskrit edition was located and "
            "downloaded in full from archive.org (17.3 MB, SHA-256 "
            "3bfd4f7f717798f87b7efd6fa5a3de2e28e7e09fc2520f0f05ae12b2e1bf9a58). "
            "It is an image-only scan with no text layer, and no OCR tool is "
            "available in this environment, so not one verse has been read. "
            "That is a different situation from the three works resolved in "
            "V1.5, and the distinction is the whole point of this table: "
            "possession of a file is not possession of a text."),
        "consequence": (
            "Referenced in rule notes only. No rule may cite it, because "
            "nothing in it has been read. Registering it as a witness on the "
            "strength of having downloaded it would be precisely the error "
            "this registry exists to prevent."),
        "what_would_resolve_it": (
            "An OCR pass over the retrieved scan, or a transliterated "
            "digital text. sanskritdocuments.org does not hold this work — "
            "checked under three spellings."),
        "retrieval_attempts": (
            "V1.3 and V1.4: archive.org and GRETIL searched, nothing "
            "obtained. V1.5: sanskritdocuments.org tried under sArAvalI, "
            "saravali and sArAvali (all 404); archive.org "
            "saravaliofkalyan01kalyuoft.pdf retrieved successfully but has "
            "no extractable text layer."),
    },
}

# Works V1.4 listed as unavailable and V1.5 actually obtained. Kept as data
# rather than deleted, because the pattern is the recurring finding of this
# project: in V1.3 for BPHS, in V1.4 for the Sanskrit BPHS, and again here.
# Each time, the previous release stated a conclusion about a TEXT that was
# only ever a conclusion about a SEARCH, and each time one more attempt
# overturned it within minutes.
RESOLVED_UNAVAILABLE_WORKS: dict[str, dict] = {
    "BPHS_SANSKRIT": {
        "work": "Bṛhat Parāśara Horā Śāstra (Sanskrit original)",
        "resolved_in": "V1.5",
        "now_registered_as": BPHS_SANSKRIT_SD.id,
        "v14_claim": (
            "'GRETIL does not hold the text; the Devanagari scans on public "
            "archives did not yield usable OCR.'"),
        "what_was_actually_true": (
            "Both halves were accurate and the conclusion drawn from them was "
            "not. V1.4 searched archive.org scans and GRETIL, and never tried "
            "sanskritdocuments.org, which has held a proofread ITRANS "
            "transliteration of all 97 chapters, split across eleven files, "
            "the whole time. It was retrieved on the first attempt."),
    },
    "PHALADEEPIKA": {
        "work": "Phaladīpikā",
        "resolved_in": "V1.5",
        "now_registered_as": PHALADEEPIKA_SD.id,
        "v14_claim": "'No digital witness retrieved.'",
        "what_was_actually_true": (
            "Available as ITRANS from sanskritdocuments.org, and separately "
            "as several public-domain English translations on archive.org "
            "(V. Subrahmanya Sastri, 1st and 2nd editions). Retrieved on the "
            "first attempt."),
    },
    "JATAKA_PARIJATA": {
        "work": "Jātaka Pārijāta",
        "resolved_in": "V1.5",
        "now_registered_as": JATAKA_PARIJATA_SD.id,
        "v14_claim": "'No digital witness retrieved.'",
        "what_was_actually_true": (
            "Available as ITRANS from sanskritdocuments.org. Retrieved on "
            "the first attempt."),
    },
}


def witness_by_id(witness_id: str) -> SourceWitness:
    for witness in ALL_WITNESSES:
        if witness.id == witness_id:
            return witness
    raise KeyError(f"No registered witness with id '{witness_id}'")


def sanskrit_tier_witnesses() -> tuple[SourceWitness, ...]:
    return tuple(w for w in ALL_WITNESSES if w.authority.is_sanskrit_tier)
