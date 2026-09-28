"""
Kala Bala — temporal strength (V1.4 Part 6)
--------------------------------------------
The most convention-sensitive of the six, and the one where an implementation
is most tempted to paper over a gap. Six subcomponents, each computed and
reported separately with its own validation status:

    Nathonnatha Bala    diurnal / nocturnal          BPHS 27.8-9
    Paksha Bala         lunar fortnight              BPHS 27.10-11
    Tribhaga Bala       third of day or night        BPHS 27.12
    Varsha-Masa-Dina-Hora Bala                       BPHS 27.13
    Ayana Bala          declination                  BPHS 27.15-17
    Yuddha Bala         planetary war                BPHS 27.20

WHERE THIS IMPLEMENTATION IS HONEST ABOUT ITS LIMITS

    Varsha Bala and Masa Bala depend on an Ahargana — a day count from an
    epoch of creation. The witness describes the method but fixes the epoch
    only through a printed "Speculum of Abbreviated Aharganas" that is part of
    that edition, not of the text. Without that table the year and month lords
    cannot be reproduced exactly, so both are computed from a STATED epoch
    convention and marked as approximations. They are not silently dropped and
    not silently guessed: they carry `is_approximation=True` and the note
    says which epoch was used.

    Ayana Bala needs the graha's declination, which requires ecliptic
    latitude. The engine has latitude for the tara grahas and the Moon but
    treats the Sun's as zero (true by definition) — so Ayana Bala is exact for
    the Sun and near-exact for the rest.

SOURCE
    BPHS ch. 27, R. Santhanam translation (witness BPHS_27_SHADBALA).
"""

from __future__ import annotations

import datetime
import math
from typing import Optional

from .models import BalaComponent

WITNESS = ("BPHS_27_SHADBALA",)
PROFILE = "bphs_santhanam_ch27"

# BPHS 27.8-9. Moon, Mars and Saturn gain by night; Sun, Jupiter and Venus by
# day; Mercury always gains the full rupa.
NIGHT_GRAHAS = ("Chandra", "Mangal", "Shani")
DAY_GRAHAS = ("Surya", "Guru", "Shukra")

# BPHS 27.10-11. Natural benefics share one paksha bala; malefics take the
# complement. Mercury's classification is conditional and the Moon's depends
# on the fortnight, both of which the witness notes explicitly.
NATURAL_BENEFICS = ("Guru", "Shukra")
NATURAL_MALEFICS = ("Surya", "Mangal", "Shani")

# BPHS 27.12. Mercury takes the first third of the day, the Sun the second,
# Saturn the third; the Moon the first third of night, Venus the second, Mars
# the third. Jupiter takes the whole of either.
TRIBHAGA_DAY = ("Budha", "Surya", "Shani")
TRIBHAGA_NIGHT = ("Chandra", "Shukra", "Mangal")

# BPHS 27.13.
VARSHA_MASA_DINA_HORA_VIRUPAS = {
    "varsha": 15.0, "masa": 30.0, "dina": 45.0, "hora": 60.0,
}

# Weekday lords, Sunday first, matching datetime.isoweekday() % 7.
WEEKDAY_LORDS = ("Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra",
                 "Shani")

# The hora sequence: each hour passes to the lord of the 6th weekday onward.
_HORA_SEQUENCE = ("Shani", "Guru", "Mangal", "Surya", "Shukra", "Budha",
                  "Chandra")


def _fold(degrees: float) -> float:
    degrees %= 360.0
    return 360.0 - degrees if degrees > 180.0 else degrees


def nathonnatha_bala(planet: str, birth: datetime.datetime) -> BalaComponent:
    """
    BPHS 27.8-9. Strength by distance from midnight or noon.

    The witness gives a simplified method directly: convert the time since
    apparent midnight at 15 degrees per hour, so midnight is 0 and noon is
    180. Night-gaining grahas score (180 - x) / 3; day-gaining grahas score
    x / 3; Mercury always scores 60.
    """
    minutes = birth.hour * 60 + birth.minute + birth.second / 60.0
    degrees_from_midnight = minutes * 0.25          # 15 degrees per hour
    unnata = _fold(degrees_from_midnight)           # 0 at midnight, 180 at noon

    if planet == "Budha":
        value = 60.0
        detail = "Mercury always receives the full rupa, day or night"
    elif planet in NIGHT_GRAHAS:
        value = (180.0 - unnata) / 3.0
        detail = f"nocturnal graha; {180.0 - unnata:.3f}° from noon, / 3"
    else:
        value = unnata / 3.0
        detail = f"diurnal graha; {unnata:.3f}° from midnight, / 3"

    return BalaComponent(
        name="nathonnatha_bala", value_virupa=value,
        calculation_profile=PROFILE, source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED", detail=detail)


def paksha_bala(planet: str, sun_longitude: float, moon_longitude: float,
                conjunct_malefic: bool = False) -> BalaComponent:
    """
    BPHS 27.10-11. Elongation of the Moon from the Sun, divided by 3, to the
    benefics; the complement to the malefics.

    Two qualifications the witness states and this implementation honours:
    Mercury counts as a malefic when conjunct one, and the Moon's own paksha
    bala is doubled.
    """
    elongation = _fold(moon_longitude - sun_longitude)
    benefic_value = elongation / 3.0

    if planet in NATURAL_BENEFICS:
        is_benefic = True
    elif planet in NATURAL_MALEFICS:
        is_benefic = False
    elif planet == "Budha":
        is_benefic = not conjunct_malefic
    else:                                            # Chandra
        is_benefic = elongation >= 90.0              # waxing half

    value = benefic_value if is_benefic else 60.0 - benefic_value
    detail = (f"elongation {elongation:.3f}°; treated as "
              f"{'benefic' if is_benefic else 'malefic'}")

    if planet == "Chandra":
        value *= 2.0
        detail += "; doubled for the Moon"

    return BalaComponent(
        name="paksha_bala", value_virupa=value,
        calculation_profile=PROFILE, source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED", detail=detail)


def tribhaga_bala(planet: str, birth: datetime.datetime,
                  sunrise_hour: float = 6.0,
                  sunset_hour: float = 18.0) -> BalaComponent:
    """
    BPHS 27.12. One rupa to the lord of the third of day or night in which
    birth falls; Jupiter always receives it.

    APPROXIMATION, declared. Sunrise and sunset default to 06:00 and 18:00
    local. Real sunrise varies by latitude and season by hours, which shifts
    the thirds. The engine does not yet compute rise and set times; when it
    does, the defaults are replaced and this flag clears.
    """
    hour = birth.hour + birth.minute / 60.0 + birth.second / 3600.0
    approximate = (sunrise_hour, sunset_hour) == (6.0, 18.0)

    if sunrise_hour <= hour < sunset_hour:
        span = (sunset_hour - sunrise_hour) / 3.0
        index = min(int((hour - sunrise_hour) / span), 2)
        lord = TRIBHAGA_DAY[index]
        which = f"day third {index + 1}"
    else:
        night_hour = hour if hour >= sunset_hour else hour + 24.0
        span = (sunrise_hour + 24.0 - sunset_hour) / 3.0
        index = min(int((night_hour - sunset_hour) / span), 2)
        lord = TRIBHAGA_NIGHT[index]
        which = f"night third {index + 1}"

    gains = planet == lord or planet == "Guru"
    return BalaComponent(
        name="tribhaga_bala",
        value_virupa=60.0 if gains else 0.0,
        calculation_profile=PROFILE, source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail=f"{which}, ruled by {lord}"
               + ("; Jupiter always gains" if planet == "Guru" else ""),
        is_approximation=approximate,
        approximation_note=(
            "Sunrise and sunset assumed at 06:00 and 18:00 local. The engine "
            "does not yet compute rise/set times, so the thirds are only "
            "approximate away from the equinox or the equator."
            if approximate else ""),
    )


def _hora_lord(birth: datetime.datetime, sunrise_hour: float) -> str:
    """
    Lord of the planetary hour. BPHS 27.13.

    Each day from sunrise to sunrise holds 24 horas. The first belongs to the
    weekday lord, and each subsequent hora passes to the lord of the 6th
    weekday from the last.
    """
    weekday = birth.isoweekday() % 7                 # 0 = Sunday
    hour = birth.hour + birth.minute / 60.0
    elapsed = hour - sunrise_hour
    if elapsed < 0:
        elapsed += 24.0
        weekday = (weekday - 1) % 7
    index = int(elapsed) % 24

    day_lord = WEEKDAY_LORDS[weekday]
    start = _HORA_SEQUENCE.index(day_lord)
    return _HORA_SEQUENCE[(start + index) % 7]


def varsha_masa_dina_hora_bala(planet: str, birth: datetime.datetime,
                               sunrise_hour: float = 6.0) -> BalaComponent:
    """
    BPHS 27.13. Fifteen virupas to the year lord, thirty to the month lord,
    forty-five to the weekday lord and sixty to the hora lord.

    DINA and HORA are computed exactly: the weekday is unambiguous and the
    hora follows from it.

    VARSHA and MASA are APPROXIMATIONS, declared. Both depend on an Ahargana
    counted from an epoch of creation, which the witness supplies through a
    printed speculum belonging to that edition rather than through the text.
    This implementation uses a stated proxy epoch (Julian day 588,465.5,
    Kali Yuga) so the arithmetic is reproducible, but the resulting lords will
    not match an edition using a different speculum.
    """
    parts: list[BalaComponent] = []

    # Dina — exact.
    weekday = birth.isoweekday() % 7
    if birth.hour + birth.minute / 60.0 < sunrise_hour:
        weekday = (weekday - 1) % 7                  # the day begins at sunrise
    dina_lord = WEEKDAY_LORDS[weekday]
    parts.append(BalaComponent(
        name="dina_bala",
        value_virupa=VARSHA_MASA_DINA_HORA_VIRUPAS["dina"]
        if planet == dina_lord else 0.0,
        calculation_profile=PROFILE, source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail=f"weekday lord is {dina_lord} (day reckoned from sunrise)"))

    # Hora — exact given the weekday.
    hora_lord = _hora_lord(birth, sunrise_hour)
    parts.append(BalaComponent(
        name="hora_bala",
        value_virupa=VARSHA_MASA_DINA_HORA_VIRUPAS["hora"]
        if planet == hora_lord else 0.0,
        calculation_profile=PROFILE, source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail=f"hora lord is {hora_lord}"))

    # Varsha and Masa — approximate.
    from ..planets import jde_from_datetime
    ahargana = int(jde_from_datetime(birth) - 588465.5)

    varsha_index = ((ahargana // 360) * 3 + 1) % 7
    varsha_lord = WEEKDAY_LORDS[varsha_index]
    parts.append(BalaComponent(
        name="varsha_bala",
        value_virupa=VARSHA_MASA_DINA_HORA_VIRUPAS["varsha"]
        if planet == varsha_lord else 0.0,
        calculation_profile=PROFILE + "/ahargana_kali_epoch",
        source_ref_ids=WITNESS, validation_status="RULE_INTERPRETATION_MAPPED",
        detail=f"year lord is {varsha_lord} (ahargana {ahargana})",
        is_approximation=True,
        approximation_note=(
            "The Ahargana epoch is not fixed by the text, only by the "
            "edition's printed speculum. A Kali Yuga epoch (JD 588465.5) is "
            "used so the arithmetic is reproducible; another edition's "
            "speculum will give a different year lord.")))

    masa_index = ((ahargana // 30) * 2 + 1) % 7
    masa_lord = WEEKDAY_LORDS[masa_index]
    parts.append(BalaComponent(
        name="masa_bala",
        value_virupa=VARSHA_MASA_DINA_HORA_VIRUPAS["masa"]
        if planet == masa_lord else 0.0,
        calculation_profile=PROFILE + "/ahargana_kali_epoch",
        source_ref_ids=WITNESS, validation_status="RULE_INTERPRETATION_MAPPED",
        detail=f"month lord is {masa_lord}",
        is_approximation=True,
        approximation_note="As varsha_bala: the Ahargana epoch is assumed."))

    return BalaComponent(
        name="varsha_masa_dina_hora_bala",
        value_virupa=sum(p.value_virupa for p in parts),
        calculation_profile=PROFILE, source_ref_ids=WITNESS,
        validation_status="RULE_INTERPRETATION_MAPPED",
        detail="varsha + masa + dina + hora",
        subcomponents=tuple(parts))


def ayana_bala(planet: str, longitude: float, latitude: float,
               obliquity: float) -> BalaComponent:
    """
    BPHS 27.15-17. Strength from the graha's declination relative to the
    celestial equator, the Sun's being doubled.

    Declination is computed from the graha's own longitude and latitude:

        sin(delta) = sin(beta) cos(eps) + cos(beta) sin(eps) sin(lambda)

    and the bala is (23.45 +/- delta) scaled so that the full swing spans
    60 virupas.
    """
    lam = math.radians(longitude)
    beta = math.radians(latitude)
    eps = math.radians(obliquity)
    declination = math.degrees(math.asin(
        max(-1.0, min(1.0, math.sin(beta) * math.cos(eps)
                      + math.cos(beta) * math.sin(eps) * math.sin(lam)))))

    # Grahas that gain in northern declination, and those that gain in
    # southern. The Sun, Mars, Jupiter and Venus gain north; the Moon and
    # Saturn gain south; Mercury gains in either.
    if planet in ("Surya", "Mangal", "Guru", "Shukra"):
        signed = declination
    elif planet in ("Chandra", "Shani"):
        signed = -declination
    else:                                            # Budha
        signed = abs(declination)

    value = (obliquity + signed) * (60.0 / (2.0 * obliquity))
    value = max(0.0, min(60.0, value))
    detail = f"declination {declination:+.4f}°, obliquity {obliquity:.4f}°"

    if planet == "Surya":
        value *= 2.0
        detail += "; doubled for the Sun"

    return BalaComponent(
        name="ayana_bala", value_virupa=value,
        calculation_profile=PROFILE, source_ref_ids=WITNESS,
        validation_status="RULE_INTERPRETATION_MAPPED",
        detail=detail,
        approximation_note=(
            "The scaling of declination to virupas is the standard reading, "
            "but the witness states it through a kranti table rather than a "
            "formula; the mapping has not been checked against that table."))


def yuddha_bala(planet: str, wars: list) -> BalaComponent:
    """
    BPHS 27.20. In a planetary war the difference between the two Shadbalas
    is added to the victor and deducted from the loser.

    Returned as zero here and applied afterwards in shadbala.py, because the
    adjustment needs both totals and therefore cannot be computed while one
    of them is still being assembled.
    """
    involved = [w for w in wars if planet in (w.planet1, w.planet2)]
    return BalaComponent(
        name="yuddha_bala", value_virupa=0.0,
        calculation_profile=PROFILE, source_ref_ids=WITNESS,
        validation_status="IMPLEMENTATION_MATCHED",
        detail=("no planetary war" if not involved
                else f"in war with "
                     f"{involved[0].planet2 if involved[0].planet1 == planet else involved[0].planet1}"
                     f"; adjustment applied to the total"))


def kala_bala(planet: str, birth: datetime.datetime,
              sun_longitude: float, moon_longitude: float,
              longitude: float, latitude: float, obliquity: float,
              conjunct_malefic: bool = False,
              wars: Optional[list] = None,
              sunrise_hour: float = 6.0,
              sunset_hour: float = 18.0) -> BalaComponent:
    """All six temporal subcomponents, summed. BPHS 27.8-20."""
    parts = (
        nathonnatha_bala(planet, birth),
        paksha_bala(planet, sun_longitude, moon_longitude, conjunct_malefic),
        tribhaga_bala(planet, birth, sunrise_hour, sunset_hour),
        varsha_masa_dina_hora_bala(planet, birth, sunrise_hour),
        ayana_bala(planet, longitude, latitude, obliquity),
        yuddha_bala(planet, wars or []),
    )
    return BalaComponent(
        name="kala_bala",
        value_virupa=sum(p.value_virupa for p in parts),
        calculation_profile=PROFILE, source_ref_ids=WITNESS,
        validation_status="RULE_INTERPRETATION_MAPPED",
        detail="nathonnatha + paksha + tribhaga + varsha/masa/dina/hora "
               "+ ayana + yuddha",
        subcomponents=parts)
