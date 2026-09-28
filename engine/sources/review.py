"""
Scholarly review pipeline (V1.8 Part 11)
------------------------------------------
The path a source takes from "we have the file" to "a rule may cite it",
and the gate that stops it skipping a step.

WHY THIS MODULE EXISTS

    Sārāvalī has sat in `UNAVAILABLE_WORKS` since V1.3 with a note that
    is accurate and misleading in the same breath: the work is not
    unavailable. A 1928 edition was downloaded in full in V1.5 and has
    been held, checksummed, ever since. What is unavailable is a READING
    of it — the scan has no text layer and nobody has looked at a page.

    Part 11: "Do not mark it unavailable." The distinction it asks for
    is between a work nobody could obtain and a work nobody has read,
    and those need different next actions. The first needs a search; the
    second needs an afternoon.

THE RULE ABOUT OCR, WHICH IS THE POINT OF THE WHOLE PIPELINE

    "OCR may assist discovery, but OCR output itself is NOT
    authoritative. Any source location derived through OCR must be
    checked against the scan before being registered as evidence."

    That is not fussiness. OCR of Devanagari on a 1928 print
    systematically confuses conjuncts, and the V1.8 gochara audit
    already found a volunteer TRANSLITERATION — far cleaner input than
    OCR — corrupt in two places, one of which would have silently
    produced a wrong vedha table. A pipeline that let an OCR hit become
    a witness would manufacture exactly the false citations this
    registry was built to eliminate.

    So `ReviewStage` is ordered, `can_register_witness` requires
    `SCAN_VERIFIED`, and there is no argument to it that skips ahead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SourceAvailability(str, Enum):
    """
    What this engine physically has of a work.

    Deliberately separate from whether anybody has READ it. Conflating
    the two is the error Part 11 corrects.
    """

    NOT_LOCATED = "NOT_LOCATED"
    RETRIEVED_TEXT = "RETRIEVED_TEXT"
    RETRIEVED_IMAGE_ONLY = "RETRIEVED_IMAGE_ONLY"
    PRINT_ONLY = "PRINT_ONLY"

    @property
    def is_held(self) -> bool:
        return self in (SourceAvailability.RETRIEVED_TEXT,
                        SourceAvailability.RETRIEVED_IMAGE_ONLY)


class ReviewStage(str, Enum):
    """
    How far a held work has been read. Ordered, and each step needs its
    own evidence.

    OCR_ASSISTED_DISCOVERY sits deliberately BELOW CANDIDATE_LOCATED,
    and CANDIDATE_LOCATED below SCAN_VERIFIED. An OCR hit is a place to
    look, which is genuinely useful and is not a finding.
    """

    TEXT_NOT_REVIEWED = "TEXT_NOT_REVIEWED"
    OCR_ASSISTED_DISCOVERY = "OCR_ASSISTED_DISCOVERY"
    CANDIDATE_LOCATED = "CANDIDATE_LOCATED"
    SCAN_VERIFIED = "SCAN_VERIFIED"
    WITNESS_REGISTERED = "WITNESS_REGISTERED"

    @property
    def rank(self) -> int:
        return _STAGE_RANK[self]

    def at_least(self, other: "ReviewStage") -> bool:
        return self.rank >= other.rank


_STAGE_RANK = {
    ReviewStage.TEXT_NOT_REVIEWED: 0,
    ReviewStage.OCR_ASSISTED_DISCOVERY: 1,
    ReviewStage.CANDIDATE_LOCATED: 2,
    ReviewStage.SCAN_VERIFIED: 3,
    ReviewStage.WITNESS_REGISTERED: 4,
}

STAGE_MEANING = {
    ReviewStage.TEXT_NOT_REVIEWED:
        "The work is held and no page has been read. Nothing may cite it.",
    ReviewStage.OCR_ASSISTED_DISCOVERY:
        "OCR has been run to find WHERE to look. The output is a search "
        "index and is not evidence; no passage located this way may be "
        "registered without a human reading the page image.",
    ReviewStage.CANDIDATE_LOCATED:
        "A specific page and verse are believed to contain the rule. "
        "Still a hypothesis: the belief rests on OCR or on a secondary "
        "reference, not on the scan.",
    ReviewStage.SCAN_VERIFIED:
        "A human has read the page IMAGE at the candidate location and "
        "confirmed what it says. This is the first stage at which a "
        "witness may be registered.",
    ReviewStage.WITNESS_REGISTERED:
        "A SourceWitness exists with an edition, a locator and a "
        "checksum, and rules may cite it.",
}


@dataclass(frozen=True)
class ReviewTask:
    """
    One work, its availability, and how far anybody has read it.

    `blocked_on` is the field that makes this actionable rather than
    decorative: it says what the NEXT person has to do, in a sentence,
    rather than leaving them to infer it from a stage name.
    """

    work: str
    traditional_author: Optional[str] = None
    availability: SourceAvailability = SourceAvailability.NOT_LOCATED
    stage: ReviewStage = ReviewStage.TEXT_NOT_REVIEWED
    edition: str = ""
    retrieved_from: str = ""
    retrieved_on: str = ""
    checksum: str = ""
    bytes_held: Optional[int] = None
    has_text_layer: bool = False
    pages: Optional[int] = None
    wanted_for: tuple[str, ...] = ()
    blocked_on: str = ""
    ocr_notes: str = ""
    history: tuple[str, ...] = ()
    notes: str = ""

    @property
    def can_register_witness(self) -> bool:
        """
        Whether a witness may be registered from this work today.

        The Part 11 gate. `SCAN_VERIFIED` and nothing less: an OCR hit,
        however confident, is not a reading.
        """
        return self.stage.at_least(ReviewStage.SCAN_VERIFIED)

    @property
    def needs_human_reader(self) -> bool:
        return (self.availability.is_held
                and not self.stage.at_least(ReviewStage.SCAN_VERIFIED))

    def to_dict(self) -> dict:
        return {
            "work": self.work,
            "traditional_author": self.traditional_author,
            "availability": self.availability.value,
            "stage": self.stage.value,
            "stage_meaning": STAGE_MEANING[self.stage],
            "edition": self.edition,
            "retrieved_from": self.retrieved_from,
            "retrieved_on": self.retrieved_on,
            "checksum": self.checksum,
            "bytes_held": self.bytes_held,
            "has_text_layer": self.has_text_layer,
            "pages": self.pages,
            "wanted_for": list(self.wanted_for),
            "can_register_witness": self.can_register_witness,
            "needs_human_reader": self.needs_human_reader,
            "blocked_on": self.blocked_on,
            "ocr_notes": self.ocr_notes,
            "history": list(self.history),
            "notes": self.notes,
        }


# ── the queue ───────────────────────────────────────────────────────────────

REVIEW_TASKS: tuple[ReviewTask, ...] = (
    ReviewTask(
        work="Sārāvalī",
        traditional_author="Kalyāṇavarman",
        availability=SourceAvailability.RETRIEVED_IMAGE_ONLY,
        stage=ReviewStage.TEXT_NOT_REVIEWED,
        edition="1928 Sanskrit edition, archive.org "
                "saravaliofkalyan01kalyuoft",
        retrieved_from="https://archive.org/details/"
                       "saravaliofkalyan01kalyuoft",
        retrieved_on="2026-09-27",
        checksum=("3bfd4f7f717798f87b7efd6fa5a3de2e"
                  "28e7e09fc2520f0f05ae12b2e1bf9a58"),
        bytes_held=17_300_000,
        has_text_layer=False,
        wanted_for=(
            "A second, independent witness for the Moon yogas — Sunaphā, "
            "Anaphā, Durudharā and Kemadruma — where the engine currently "
            "diverges from BJ 13.3 and BPHS 37.11 and the divergence is "
            "recorded rather than resolved.",
            "A second witness for the Pañca Mahāpuruṣa yogas, which are "
            "taught everywhere and are located in only one work here.",
            "Its gochara chapter, which would be the first INDEPENDENT "
            "work bearing on the transit rules V1.8 implemented from "
            "Phaladīpikā alone.",
        ),
        blocked_on=(
            "A human with the page images. The scan has no text layer, so "
            "reading it is an act of reading, not of processing. Roughly a "
            "day's work for somebody who reads Devanagari; there is no "
            "technical step that substitutes."),
        ocr_notes=(
            "No OCR has been run. If it is, its output is a search index "
            "and nothing more: every candidate it produces must be checked "
            "against the page image before a witness is registered. "
            "Devanagari OCR of a 1928 print confuses conjuncts "
            "systematically, and the V1.8 gochara audit found a volunteer "
            "TRANSLITERATION — much cleaner input — corrupt in two places, "
            "one of which would have produced a wrong vedha table."),
        history=(
            "V1.3: searched archive.org and GRETIL, nothing obtained.",
            "V1.4: declared unavailable.",
            "V1.5: the 1928 edition retrieved in full from archive.org; "
            "sanskritdocuments.org checked under sArAvalI, saravali and "
            "sArAvali, all 404.",
            "V1.6, V1.7: unchanged, carried as RETRIEVED BUT NOT READ.",
            "V1.8: reclassified. The work is not unavailable — it is held "
            "and unread, which is a different problem with a different "
            "next action.",
        ),
        notes=(
            "The most valuable unread source this engine holds. Every "
            "entry in `wanted_for` is a question currently answered with "
            "'one witness only' or 'unresolved'."),
    ),
    ReviewTask(
        work="Bṛhat Parāśara Horā Śāstra",
        traditional_author="Parāśara (attributed)",
        availability=SourceAvailability.RETRIEVED_TEXT,
        stage=ReviewStage.WITNESS_REGISTERED,
        edition="sanskritdocuments.org ITRANS, chapters 1-10 and others",
        blocked_on=(
            "The printed exemplar the transliteration was made from is "
            "not named, so the engine cites an edition it cannot fully "
            "identify. Resolving it needs somebody to compare the ITRANS "
            "text against a named print."),
        notes=("Read and cited extensively. The open question is edition "
               "identity, not access."),
    ),
    ReviewTask(
        work="Phaladīpikā",
        traditional_author="Mantreśvara",
        availability=SourceAvailability.RETRIEVED_TEXT,
        stage=ReviewStage.WITNESS_REGISTERED,
        edition="sanskritdocuments.org ITRANS; Sastri 1950 printed "
                "translation",
        blocked_on=(
            "The 1950 edition's Devanagari is present in the scan and has "
            "NOT been read — only its English translation survives OCR "
            "legibly. Reading the Sanskrit would upgrade two gochara "
            "readings from translation-corroborated to Sanskrit-tier."),
        ocr_notes=(
            "The 1950 scan's Devanagari OCRs to noise. Its English does "
            "not, which is why the translation is registered and the "
            "Sanskrit of that edition is not."),
        notes=("Two editions held. They disagreed in two words, and the "
               "disagreement was resolved in V1.8 — see "
               "GOCHARA_MERCURY_VEDHA_READING."),
    ),
)


def tasks_needing_a_reader() -> list[ReviewTask]:
    """Works held but unread. The actual queue."""
    return [task for task in REVIEW_TASKS if task.needs_human_reader]


def task_for(work: str) -> Optional[ReviewTask]:
    for task in REVIEW_TASKS:
        if task.work.lower().startswith(work.lower()[:6]):
            return task
    return None


def can_register_witness(work: str) -> bool:
    """
    Whether a witness from `work` may be registered today.

    An unknown work returns False. A work this pipeline has never heard
    of has certainly not been read against its scan.
    """
    task = task_for(work)
    return bool(task and task.can_register_witness)


def review_summary() -> dict:
    """The pipeline's state, for the report and the methodology screen."""
    by_stage: dict = {}
    by_availability: dict = {}
    for task in REVIEW_TASKS:
        by_stage[task.stage.value] = by_stage.get(task.stage.value, 0) + 1
        key = task.availability.value
        by_availability[key] = by_availability.get(key, 0) + 1
    return {
        "works_tracked": len(REVIEW_TASKS),
        "by_stage": dict(sorted(by_stage.items())),
        "by_availability": dict(sorted(by_availability.items())),
        "awaiting_a_reader": [task.work for task in tasks_needing_a_reader()],
        "stage_meaning": {stage.value: meaning
                          for stage, meaning in STAGE_MEANING.items()},
        "ocr_policy": (
            "OCR assists discovery and is never evidence. A passage found "
            "by OCR must be read on the page image before any witness is "
            "registered from it."),
        "note": (
            "Availability and readership are separate axes. A work can be "
            "held in full and completely unread, which is Sārāvalī's "
            "position and is not the same as being unavailable."),
    }
