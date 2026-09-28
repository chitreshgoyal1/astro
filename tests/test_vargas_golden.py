"""
Golden tests for all sixteen Vargas
-----------------------------------
A Varga rule is definitional, not astronomical, so the independent reference
cannot come from an ephemeris. Instead this module contains a SECOND
implementation of each classical rule, written directly from the textual
statement in BPHS and deliberately structured differently from the engine's:

  * the engine builds its rules from generic combinators (_parity_offset,
    _category_start, _parivritti) parameterised by tables;
  * the reference below writes each rule out longhand, in the words of the
    text — "odd signs count from the sign itself, even signs from the seventh".

Two independent expressions of the same rule agreeing across every division
boundary of every chart is a real check. Comparing the engine to itself would
not be, which is why the reference never imports from engine.vargas.

Boundary coverage: for every Varga the test walks every division boundary in
every one of the twelve rashis and checks the sign immediately below and
immediately above it. For D60 that is 720 boundaries, so the whole suite
exercises a little over two thousand transitions.
"""

# Phase 2 (V1.1).

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.vargas import (
    VARGA_ORDER, VARGA_SPECS, VargaConfig, VargaConfigError,
)

# ── Independent reference implementation ─────────────────────────────────────
# Each function takes (sign, degree_in_sign) and returns the divisional sign
# index, written from the classical statement rather than from a table.

MESHA, VRISHABHA, MITHUNA, KARKA = 0, 1, 2, 3
SIMHA, KANYA, TULA, VRISHCHIKA = 4, 5, 6, 7
DHANU, MAKARA, KUMBHA, MEENA = 8, 9, 10, 11


def _odd(sign: int) -> bool:
    """Mesha, Mithuna, Simha, Tula, Dhanu, Kumbha are the odd (vishama) rashis."""
    return sign in (MESHA, MITHUNA, SIMHA, TULA, DHANU, KUMBHA)


def _part(degree: float, divisions: int) -> int:
    """Which equal part of the rashi a degree falls in, counting from zero."""
    return min(int(degree / (30.0 / divisions)), divisions - 1)


def ref_d1(sign, degree):
    """The rashi itself."""
    return sign


def ref_d2(sign, degree):
    """Hora. Odd rashi: first half Surya's (Simha), second half Chandra's
    (Karka). Even rashi: the reverse."""
    first_half = degree < 15.0
    if _odd(sign):
        return SIMHA if first_half else KARKA
    return KARKA if first_half else SIMHA


def ref_d3(sign, degree):
    """Drekkana. The three parts go to the rashi itself, the 5th from it, and
    the 9th from it."""
    return (sign + (0, 4, 8)[_part(degree, 3)]) % 12


def ref_d4(sign, degree):
    """Chaturthamsha. The four parts go to the rashi, the 4th, the 7th, the
    10th — the four kendras from it."""
    return (sign + (0, 3, 6, 9)[_part(degree, 4)]) % 12


def ref_d7(sign, degree):
    """Saptamsha. Odd rashi: count from the rashi itself. Even rashi: count
    from the seventh from it."""
    start = sign if _odd(sign) else (sign + 6) % 12
    return (start + _part(degree, 7)) % 12


def ref_d9(sign, degree):
    """Navamsha. Fire rashis count from Mesha, earth from Makara, air from
    Tula, water from Karka."""
    start = {
        MESHA: MESHA, SIMHA: MESHA, DHANU: MESHA,                 # fire
        VRISHABHA: MAKARA, KANYA: MAKARA, MAKARA: MAKARA,         # earth
        MITHUNA: TULA, TULA: TULA, KUMBHA: TULA,                  # air
        KARKA: KARKA, VRISHCHIKA: KARKA, MEENA: KARKA,            # water
    }[sign]
    return (start + _part(degree, 9)) % 12


def ref_d10(sign, degree):
    """Dasamsha. Odd rashi: count from the rashi itself. Even rashi: count
    from the ninth from it."""
    start = sign if _odd(sign) else (sign + 8) % 12
    return (start + _part(degree, 10)) % 12


def ref_d12(sign, degree):
    """Dwadashamsha. Twelve parts counted from the rashi itself."""
    return (sign + _part(degree, 12)) % 12


def _movable_fixed_dual(sign: int) -> str:
    if sign in (MESHA, KARKA, TULA, MAKARA):
        return "movable"
    if sign in (VRISHABHA, SIMHA, VRISHCHIKA, KUMBHA):
        return "fixed"
    return "dual"


def ref_d16(sign, degree):
    """Shodashamsha. Movable rashis count from Mesha, fixed from Simha, dual
    from Dhanu."""
    start = {"movable": MESHA, "fixed": SIMHA, "dual": DHANU}[
        _movable_fixed_dual(sign)]
    return (start + _part(degree, 16)) % 12


def ref_d20(sign, degree):
    """Vimshamsha. Movable rashis count from Mesha, fixed from Dhanu, dual
    from Simha."""
    start = {"movable": MESHA, "fixed": DHANU, "dual": SIMHA}[
        _movable_fixed_dual(sign)]
    return (start + _part(degree, 20)) % 12


def ref_d24(sign, degree):
    """Chaturvimshamsha. Odd rashis count from Simha, even rashis from Karka."""
    start = SIMHA if _odd(sign) else KARKA
    return (start + _part(degree, 24)) % 12


def _element(sign: int) -> str:
    return ["fire", "earth", "air", "water"][sign % 4]


def ref_d27(sign, degree):
    """Bhamsha. Fire rashis count from Mesha, earth from Karka, air from Tula,
    water from Makara."""
    start = {"fire": MESHA, "earth": KARKA, "air": TULA, "water": MAKARA}[
        _element(sign)]
    return (start + _part(degree, 27)) % 12


def ref_d30(sign, degree):
    """
    Trimshamsha. The one Varga with unequal parts, and the only one whose
    parts are assigned to lords rather than counted round the zodiac.

    Odd rashi: 5° Mangal (Mesha), 5° Shani (Kumbha), 8° Guru (Dhanu),
               7° Budha (Mithuna), 5° Shukra (Tula).
    Even rashi: the order reverses and the other rashi of each lord is used —
               5° Shukra (Vrishabha), 7° Budha (Kanya), 8° Guru (Meena),
               5° Shani (Makara), 5° Mangal (Vrishchika).
    """
    if _odd(sign):
        for limit, result in ((5, MESHA), (10, KUMBHA), (18, DHANU),
                              (25, MITHUNA), (30, TULA)):
            if degree < limit:
                return result
        return TULA
    for limit, result in ((5, VRISHABHA), (12, KANYA), (20, MEENA),
                          (25, MAKARA), (30, VRISHCHIKA)):
        if degree < limit:
            return result
    return VRISHCHIKA


def ref_d40(sign, degree):
    """Khavedamsha. Odd rashis count from Mesha, even rashis from Tula."""
    start = MESHA if _odd(sign) else TULA
    return (start + _part(degree, 40)) % 12


def ref_d45(sign, degree):
    """Akshavedamsha. Movable rashis count from Mesha, fixed from Simha, dual
    from Dhanu."""
    start = {"movable": MESHA, "fixed": SIMHA, "dual": DHANU}[
        _movable_fixed_dual(sign)]
    return (start + _part(degree, 45)) % 12


def ref_d60(sign, degree):
    """Shashtiamsha. Sixty half-degree parts counted from the rashi itself."""
    return (sign + _part(degree, 60)) % 12


REFERENCE = {
    "D1": ref_d1, "D2": ref_d2, "D3": ref_d3, "D4": ref_d4, "D7": ref_d7,
    "D9": ref_d9, "D10": ref_d10, "D12": ref_d12, "D16": ref_d16,
    "D20": ref_d20, "D24": ref_d24, "D27": ref_d27, "D30": ref_d30,
    "D40": ref_d40, "D45": ref_d45, "D60": ref_d60,
}


def reference_from_longitude(varga: str, longitude: float) -> int:
    """
    Reference result for an absolute sidereal longitude.

    Both sides must split the longitude into rashi and degree identically,
    otherwise a comparison at an exact division boundary turns into a test of
    floating-point rounding rather than of the rule. The split itself is
    definitional and shared; the RULES are what this module states
    independently.
    """
    longitude %= 360.0
    sign = int(longitude // 30) % 12
    degree = longitude % 30.0
    return REFERENCE[varga](sign, degree)

# Hand-worked spot values, written out from the rule statements above so that
# a shared misreading of a rule would still be caught by an explicit number.
# (varga, sign, degree, expected divisional sign)
SPOT_VALUES = [
    ("D1", MESHA, 0.0, MESHA),
    ("D1", MEENA, 29.99, MEENA),
    # Hora: Mesha is odd, so its first half is Simha.
    ("D2", MESHA, 0.0, SIMHA), ("D2", MESHA, 15.0, KARKA),
    ("D2", VRISHABHA, 0.0, KARKA), ("D2", VRISHABHA, 15.0, SIMHA),
    # Drekkana: own, 5th, 9th.
    ("D3", MESHA, 0.0, MESHA), ("D3", MESHA, 10.0, SIMHA),
    ("D3", MESHA, 20.0, DHANU), ("D3", VRISHCHIKA, 20.0, KARKA),
    # Chaturthamsha: the kendras.
    ("D4", MESHA, 0.0, MESHA), ("D4", MESHA, 7.5, KARKA),
    ("D4", MESHA, 15.0, TULA), ("D4", MESHA, 22.5, MAKARA),
    # Saptamsha: odd from itself, even from the 7th.
    ("D7", MESHA, 0.0, MESHA), ("D7", VRISHABHA, 0.0, VRISHCHIKA),
    ("D7", MEENA, 0.0, KANYA),
    # Navamsha: the four starting points, and the last navamsha of Meena.
    ("D9", MESHA, 0.0, MESHA), ("D9", MESHA, 3.3333334, VRISHABHA),
    ("D9", VRISHABHA, 0.0, MAKARA), ("D9", MITHUNA, 0.0, TULA),
    ("D9", KARKA, 0.0, KARKA), ("D9", MEENA, 29.999, MEENA),
    ("D9", DHANU, 0.0, MESHA),
    # Dasamsha: odd from itself, even from the 9th.
    ("D10", MESHA, 0.0, MESHA), ("D10", MESHA, 3.0, VRISHABHA),
    ("D10", VRISHABHA, 0.0, MAKARA), ("D10", KANYA, 0.0, VRISHABHA),
    # Dwadashamsha from the rashi itself.
    ("D12", MESHA, 0.0, MESHA), ("D12", MESHA, 2.5, VRISHABHA),
    ("D12", MEENA, 27.5, KUMBHA),
    # Shodashamsha starting points.
    ("D16", MESHA, 0.0, MESHA), ("D16", VRISHABHA, 0.0, SIMHA),
    ("D16", MITHUNA, 0.0, DHANU),
    # Vimshamsha starting points.
    ("D20", MESHA, 0.0, MESHA), ("D20", VRISHABHA, 0.0, DHANU),
    ("D20", MITHUNA, 0.0, SIMHA),
    # Chaturvimshamsha: odd from Simha, even from Karka.
    ("D24", MESHA, 0.0, SIMHA), ("D24", VRISHABHA, 0.0, KARKA),
    ("D24", MESHA, 1.25, KANYA),
    # Bhamsha by element.
    ("D27", MESHA, 0.0, MESHA), ("D27", VRISHABHA, 0.0, KARKA),
    ("D27", MITHUNA, 0.0, TULA), ("D27", KARKA, 0.0, MAKARA),
    # Trimshamsha unequal parts, both parities, every boundary.
    ("D30", MESHA, 0.0, MESHA), ("D30", MESHA, 4.99, MESHA),
    ("D30", MESHA, 5.0, KUMBHA), ("D30", MESHA, 9.99, KUMBHA),
    ("D30", MESHA, 10.0, DHANU), ("D30", MESHA, 17.99, DHANU),
    ("D30", MESHA, 18.0, MITHUNA), ("D30", MESHA, 24.99, MITHUNA),
    ("D30", MESHA, 25.0, TULA), ("D30", MESHA, 29.99, TULA),
    ("D30", VRISHABHA, 0.0, VRISHABHA), ("D30", VRISHABHA, 5.0, KANYA),
    ("D30", VRISHABHA, 12.0, MEENA), ("D30", VRISHABHA, 20.0, MAKARA),
    ("D30", VRISHABHA, 25.0, VRISHCHIKA), ("D30", VRISHABHA, 29.99, VRISHCHIKA),
    # Khavedamsha: odd from Mesha, even from Tula.
    ("D40", MESHA, 0.0, MESHA), ("D40", VRISHABHA, 0.0, TULA),
    ("D40", MESHA, 0.75, VRISHABHA),
    # Akshavedamsha starting points.
    ("D45", MESHA, 0.0, MESHA), ("D45", VRISHABHA, 0.0, SIMHA),
    ("D45", MITHUNA, 0.0, DHANU),
    # Shashtiamsha: half-degree parts from the rashi itself.
    ("D60", MESHA, 0.0, MESHA), ("D60", MESHA, 0.5, VRISHABHA),
    ("D60", MESHA, 29.75, MEENA), ("D60", MEENA, 0.5, MESHA),
]


class VargaReferenceTest(unittest.TestCase):
    """The engine against an independent longhand statement of each rule."""

    def setUp(self):
        self.config = VargaConfig()

    def test_all_sixteen_vargas_are_registered(self):
        self.assertEqual(len(VARGA_ORDER), 16)
        self.assertEqual(set(VARGA_ORDER), set(REFERENCE))

    def test_hand_worked_spot_values(self):
        for varga, sign, degree, expected in SPOT_VALUES:
            longitude = sign * 30.0 + degree
            with self.subTest(varga=varga, sign=sign, degree=degree):
                self.assertEqual(
                    self.config.compute(varga, longitude).rashi_index, expected,
                    f"{varga} at sign {sign} {degree}°")

    SWEEP_SAMPLES_PER_SIGN = 720

    def test_engine_matches_reference_across_every_degree(self):
        """
        A fine sweep of the whole zodiac. Samples sit at the midpoint of each
        step so the sweep never lands on a division boundary — boundaries are
        the business of VargaBoundaryTest, which approaches them deliberately
        from both sides.
        """
        step = 30.0 / self.SWEEP_SAMPLES_PER_SIGN
        checked = 0
        for varga in VARGA_ORDER:
            for sign in range(12):
                for index in range(self.SWEEP_SAMPLES_PER_SIGN):
                    longitude = sign * 30.0 + (index + 0.5) * step
                    got = self.config.compute(varga, longitude).rashi_index
                    want = reference_from_longitude(varga, longitude)
                    checked += 1
                    if got != want:
                        self.fail(
                            f"{varga} at {longitude:.6f}° (sign {sign}): "
                            f"engine {got}, reference {want}")
        self.assertEqual(checked, 16 * 12 * self.SWEEP_SAMPLES_PER_SIGN)


class VargaBoundaryTest(unittest.TestCase):
    """
    Every division boundary of every Varga, approached from both sides.

    A Varga with n divisions has n-1 internal boundaries per rashi plus the
    rashi boundary itself, so this walks 12 x n transitions for each chart.
    """

    EPSILON = 1e-7

    def setUp(self):
        self.config = VargaConfig()

    def test_every_division_boundary_in_every_varga(self):
        checked = 0
        for varga in VARGA_ORDER:
            spec = VARGA_SPECS[varga]
            # D30 has unequal parts, so its boundaries are listed explicitly.
            if varga == "D30":
                odd_bounds = (5.0, 10.0, 18.0, 25.0)
                even_bounds = (5.0, 12.0, 20.0, 25.0)
            else:
                width = 30.0 / spec.divisions
                odd_bounds = even_bounds = tuple(
                    width * i for i in range(1, spec.divisions))

            for sign in range(12):
                bounds = odd_bounds if _odd(sign) else even_bounds
                for bound in bounds:
                    for offset, side in ((-self.EPSILON, "below"),
                                         (+self.EPSILON, "above")):
                        degree = bound + offset
                        longitude = sign * 30.0 + degree
                        got = self.config.compute(varga, longitude).rashi_index
                        want = reference_from_longitude(varga, longitude)
                        checked += 1
                        if got != want:
                            self.fail(
                                f"{varga} sign {sign} boundary {bound}° "
                                f"({side}): engine {got}, reference {want}")
        self.assertGreater(checked, 2000,
                           "expected the sweep to cover 2000+ boundaries")

    def test_rashi_boundaries(self):
        """The transition from 29.999...° of one rashi into the next."""
        for varga in VARGA_ORDER:
            for sign in range(12):
                for degree in (0.0, 29.9999999):
                    longitude = sign * 30.0 + degree
                    with self.subTest(varga=varga, sign=sign, degree=degree):
                        self.assertEqual(
                            self.config.compute(varga, longitude).rashi_index,
                            reference_from_longitude(varga, longitude))

    def test_longitude_wraps_at_360(self):
        for varga in VARGA_ORDER:
            with self.subTest(varga=varga):
                self.assertEqual(
                    self.config.compute(varga, 0.0).rashi_index,
                    self.config.compute(varga, 360.0).rashi_index)


class VargaConventionTest(unittest.TestCase):
    """Conventions stay explicit and selectable, and bad input is rejected."""

    def test_default_conventions_unchanged_by_phase_2(self):
        """
        The audit found no error in the existing defaults, so they must not
        have moved. This pins them.
        """
        config = VargaConfig()
        expected = {
            "D1": "standard", "D2": "parashari", "D3": "parashari",
            "D4": "parashari", "D7": "parashari", "D9": "standard",
            "D10": "parashari", "D12": "parashari", "D16": "parashari",
            "D20": "parashari", "D24": "parashari", "D27": "parashari",
            "D30": "parashari", "D40": "parashari", "D45": "parashari",
            "D60": "parashari",
        }
        self.assertEqual(config.conventions, expected)

    def test_every_varga_reports_the_convention_it_used(self):
        config = VargaConfig()
        for varga in VARGA_ORDER:
            with self.subTest(varga=varga):
                position = config.compute(varga, 123.456)
                self.assertTrue(position.convention)
                self.assertIn(position.convention, VARGA_SPECS[varga].conventions)

    # Conventions that are mathematically INDISTINGUISHABLE from the default,
    # found during the Phase 2 audit. In each case the cyclic (parivritti)
    # count and the classical rule coincide for every longitude, because the
    # number of divisions is congruent mod 12 to exactly the offset the
    # classical rule applies:
    #
    #   D7   7 ≡ 7   odd rashis start from themselves, even from the 7th, and
    #                6s mod 12 is 0 for odd rashis and 6 for even ones
    #   D16  16 ≡ 4  movability has period 3, and 4 x 3 ≡ 0
    #   D20  20 ≡ 8  movability has period 3, and 8 x 3 ≡ 0
    #   D27  27 ≡ 3  element has period 4, and 3 x 4 ≡ 0
    #
    # These are identities, not defects — but offering them as two named
    # choices implies a difference that does not exist, which is why they are
    # recorded here and in AUDIT.md rather than left for a user to discover.
    KNOWN_IDENTICAL = {("D7", "parivritti"), ("D16", "parivritti"),
                       ("D20", "parivritti"), ("D27", "parivritti")}

    def test_alternative_conventions_differ_except_where_documented(self):
        """
        Every named alternative either changes a result, or is one of the four
        documented identities. A new identity appearing here means a rule was
        changed and silently collapsed onto another.
        """
        default = VargaConfig()
        identical_found = set()
        for varga in VARGA_ORDER:
            alternatives = [c for c in VARGA_SPECS[varga].conventions
                            if c != default.conventions[varga]]
            for alternative in alternatives:
                other = VargaConfig(conventions={varga: alternative})
                differs = any(
                    default.compute(varga, lon).rashi_index
                    != other.compute(varga, lon).rashi_index
                    for lon in [i * 0.01 for i in range(36000)])
                if not differs:
                    identical_found.add((varga, alternative))
        self.assertEqual(
            identical_found, self.KNOWN_IDENTICAL,
            "the set of conventions indistinguishable from their default has "
            "changed; a Varga rule was probably altered")

    def test_unknown_varga_and_convention_are_rejected(self):
        with self.assertRaises(VargaConfigError):
            VargaConfig(conventions={"D5": "parashari"})
        with self.assertRaises(VargaConfigError):
            VargaConfig(conventions={"D9": "not_a_convention"})

    def test_parivritti_is_cyclic_and_continuous(self):
        """The parivritti conventions must run continuously round the zodiac."""
        for varga in VARGA_ORDER:
            if "parivritti" not in VARGA_SPECS[varga].conventions:
                continue
            divisions = VARGA_SPECS[varga].divisions
            config = VargaConfig(conventions={varga: "parivritti"})
            width = 30.0 / divisions
            with self.subTest(varga=varga):
                for index in range(12 * divisions):
                    longitude = index * width + width / 2
                    self.assertEqual(
                        config.compute(varga, longitude).rashi_index,
                        index % 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
