"""
Birth location resolution (Part 2)
----------------------------------
The single most important property under test: an unresolvable birth place
must FAIL, never quietly become another city. A chart computed on the wrong
coordinates is not a degraded answer, it is a confidently wrong one — the
Lagna moves about a degree every four minutes of time, so substituting Delhi
for an unknown place silently produces a different Ascendant, a different
first house, and therefore a different reading of everything.
"""

# Phase 2 (V1.1).

import datetime
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.location import (
    BirthLocation, CITY_TABLE, LocationError, known_cities, lookup_city,
    offset_from_timezone, parse_coordinate, parse_utc_offset, resolve_location,
)


class NoSilentFallbackTest(unittest.TestCase):
    """The behaviour Phase 2 was asked to remove."""

    UNKNOWN_PLACES = [
        "Nowhereville",
        "Sehore",                      # a real Indian town, not in the table
        "Zzzz",
        "Atlantis, Ocean",
        "12345",
    ]

    def test_unknown_place_raises_instead_of_defaulting(self):
        for place in self.UNKNOWN_PLACES:
            with self.subTest(place=place):
                with self.assertRaises(LocationError):
                    resolve_location(place=place)

    def test_unknown_place_never_returns_delhi(self):
        """
        The specific regression: the previous build printed a warning and
        carried on with Delhi's coordinates.
        """
        delhi = CITY_TABLE["delhi"]
        for place in self.UNKNOWN_PLACES:
            with self.subTest(place=place):
                try:
                    location = resolve_location(place=place)
                except LocationError:
                    continue
                self.fail(
                    f"'{place}' resolved to {location.latitude}, "
                    f"{location.longitude} instead of failing"
                    + (" — and it is Delhi"
                       if (location.latitude, location.longitude)
                       == (delhi[0], delhi[1]) else ""))

    def test_error_message_explains_how_to_recover(self):
        with self.assertRaises(LocationError) as caught:
            resolve_location(place="Sehore")
        message = str(caught.exception)
        self.assertIn("Sehore", message)
        self.assertIn("--lat", message)
        self.assertIn("--timezone", message)

    def test_empty_place_without_coordinates_fails(self):
        with self.assertRaises(LocationError):
            resolve_location(place="")
        with self.assertRaises(LocationError):
            resolve_location(place=None)

    def test_substring_match_does_not_leak_between_cities(self):
        """
        The old lookup used `city in key or key in city`, so "York" matched
        "new york" and any string containing "delhi" matched Delhi. Matching
        is now exact or an unambiguous prefix.
        """
        for place in ("York", "elhi", "umbai", "ondon"):
            with self.subTest(place=place):
                self.assertIsNone(lookup_city(place))


class ExplicitCoordinatesTest(unittest.TestCase):
    """An unknown place is usable when coordinates are supplied."""

    def test_explicit_coordinates_with_timezone(self):
        location = resolve_location(
            place="Sehore", latitude=23.2032, longitude=77.0856,
            timezone="Asia/Kolkata",
            local_datetime=datetime.datetime(1988, 8, 30, 20, 18))
        self.assertAlmostEqual(location.latitude, 23.2032)
        self.assertAlmostEqual(location.longitude, 77.0856)
        self.assertAlmostEqual(location.utc_offset_at_birth, 5.5)
        self.assertEqual(location.name, "Sehore")

    def test_explicit_coordinates_with_fixed_offset(self):
        location = resolve_location(
            place="Somewhere", latitude=10.0, longitude=20.0,
            utc_offset="+05:30")
        self.assertAlmostEqual(location.utc_offset_at_birth, 5.5)

    def test_coordinates_without_zone_or_offset_fails(self):
        with self.assertRaises(LocationError):
            resolve_location(place="Somewhere", latitude=10.0, longitude=20.0)

    def test_half_supplied_coordinates_fail(self):
        with self.assertRaises(LocationError):
            resolve_location(place="Somewhere", latitude=10.0)
        with self.assertRaises(LocationError):
            resolve_location(place="Somewhere", longitude=20.0)

    def test_explicit_coordinates_override_the_city_table(self):
        """A named city plus explicit coordinates uses the coordinates."""
        location = resolve_location(
            place="Jaipur", latitude=1.0, longitude=2.0,
            timezone="Asia/Kolkata")
        self.assertAlmostEqual(location.latitude, 1.0)
        self.assertAlmostEqual(location.longitude, 2.0)


class CoordinateParsingTest(unittest.TestCase):

    def test_decimal_and_dms_forms(self):
        cases = [
            ("26.9124", 26.9124),
            ("26 54 45 N", 26 + 54 / 60 + 45 / 3600),
            ("26°54'45\"N", 26 + 54 / 60 + 45 / 3600),
            ("33 52 S", -(33 + 52 / 60)),
            ("-33.8688", -33.8688),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_coordinate(text, "latitude"),
                                       expected, places=6)

    def test_western_longitude_is_negative(self):
        self.assertAlmostEqual(parse_coordinate("74 0 22 W", "longitude"),
                               -(74 + 22 / 3600), places=6)

    def test_rubbish_is_rejected(self):
        for text in ("north", "", "12 34 56 Q x"):
            with self.subTest(text=text):
                with self.assertRaises(LocationError):
                    parse_coordinate(text, "latitude")

    def test_utc_offset_forms(self):
        for text, expected in (("+05:30", 5.5), ("5.5", 5.5), ("-8", -8.0),
                               ("UTC+05:30", 5.5), ("0530", 5.5), ("-0330", -3.5)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_utc_offset(text), expected)

    def test_bad_utc_offset_is_rejected(self):
        for text in ("", "noon", "abc"):
            with self.subTest(text=text):
                with self.assertRaises(LocationError):
                    parse_utc_offset(text)


class BirthLocationModelTest(unittest.TestCase):
    """The model validates its own fields — Part 2's structural requirement."""

    def make(self, **overrides) -> BirthLocation:
        fields = dict(name="Test", latitude=26.9, longitude=75.8,
                      timezone_name="Asia/Kolkata", utc_offset_at_birth=5.5,
                      source="test")
        fields.update(overrides)
        return BirthLocation(**fields)

    def test_has_every_required_field(self):
        location = self.make()
        for attribute in ("name", "latitude", "longitude", "timezone_name",
                          "utc_offset_at_birth"):
            self.assertTrue(hasattr(location, attribute), attribute)

    def test_out_of_range_values_are_rejected(self):
        for overrides in ({"latitude": 91.0}, {"latitude": -91.0},
                          {"longitude": 181.0}, {"longitude": -181.0},
                          {"utc_offset_at_birth": 15.0},
                          {"utc_offset_at_birth": -13.0}):
            with self.subTest(**overrides):
                with self.assertRaises(LocationError):
                    self.make(**overrides)

    def test_utc_conversion_is_explicit_and_reversible(self):
        location = self.make()
        local = datetime.datetime(1988, 8, 30, 20, 18)
        self.assertEqual(location.to_utc(local),
                         datetime.datetime(1988, 8, 30, 14, 48))

    def test_offset_text(self):
        self.assertEqual(self.make().offset_text(), "UTC+05:30")
        self.assertEqual(
            self.make(utc_offset_at_birth=-3.5).offset_text(), "UTC-03:30")


class TimezoneTest(unittest.TestCase):
    """
    Historical time zone support goes through the IANA database, so daylight
    saving and pre-modern offsets are resolved for the birth moment rather
    than assumed from a fixed number.
    """

    def test_iana_zone_resolves_for_the_birth_moment(self):
        offset = offset_from_timezone(
            "Asia/Kolkata", datetime.datetime(1988, 8, 30, 20, 18))
        self.assertIsNotNone(offset)
        self.assertAlmostEqual(offset, 5.5)

    def test_daylight_saving_is_applied_where_it_applies(self):
        summer = offset_from_timezone(
            "Europe/London", datetime.datetime(1988, 7, 1, 12, 0))
        winter = offset_from_timezone(
            "Europe/London", datetime.datetime(1988, 1, 1, 12, 0))
        self.assertIsNotNone(summer)
        self.assertIsNotNone(winter)
        self.assertAlmostEqual(summer, 1.0)
        self.assertAlmostEqual(winter, 0.0)

    def test_historical_offset_differs_from_the_modern_one(self):
        """
        India used UTC+05:53 in Kolkata before standardisation. Resolving the
        zone for the actual birth moment is the mechanism that makes such
        cases correct later; this asserts the mechanism is live.
        """
        old = offset_from_timezone(
            "Asia/Kolkata", datetime.datetime(1900, 1, 1, 12, 0))
        modern = offset_from_timezone(
            "Asia/Kolkata", datetime.datetime(2000, 1, 1, 12, 0))
        self.assertIsNotNone(old)
        self.assertNotAlmostEqual(old, modern,
                                  msg="historical zone rules are not being used")

    def test_unknown_zone_is_rejected(self):
        self.assertIsNone(offset_from_timezone("Mars/Olympus", datetime.datetime.now()))


class CityTableTest(unittest.TestCase):

    def test_known_cities_resolve(self):
        for city in ("jaipur", "delhi", "london", "sydney", "new york"):
            with self.subTest(city=city):
                location = resolve_location(
                    place=city,
                    local_datetime=datetime.datetime(1988, 8, 30, 20, 18))
                self.assertTrue(-90 <= location.latitude <= 90)
                self.assertTrue(-180 <= location.longitude <= 180)

    def test_place_with_region_suffix_resolves(self):
        location = resolve_location(
            place="Jaipur, Rajasthan, India",
            local_datetime=datetime.datetime(1988, 8, 30, 20, 18))
        self.assertAlmostEqual(location.latitude, 26.9124, places=3)

    def test_every_table_entry_is_valid(self):
        for name, (lat, lon, zone, offset) in CITY_TABLE.items():
            with self.subTest(city=name):
                self.assertTrue(-90 <= lat <= 90)
                self.assertTrue(-180 <= lon <= 180)
                self.assertTrue(-12 <= offset <= 14)
                self.assertIn("/", zone)

    def test_known_cities_is_sorted_and_non_empty(self):
        cities = known_cities()
        self.assertTrue(cities)
        self.assertEqual(cities, sorted(cities))


class CommandLineTest(unittest.TestCase):
    """The CLI must surface the failure rather than producing a chart."""

    def run_main(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "main.py", *args],
            cwd=ROOT, capture_output=True, text=True, timeout=120)

    def test_unknown_place_exits_non_zero_and_prints_no_chart(self):
        result = self.run_main("--name", "Test", "--dob", "1988-08-30",
                               "--time", "20:18", "--place", "Nowhereville")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("JYOTISH CHART", result.stdout)
        self.assertIn("Nowhereville", result.stdout + result.stderr)

    def test_unknown_place_with_coordinates_succeeds(self):
        result = self.run_main("--name", "Test", "--dob", "1988-08-30",
                               "--time", "20:18", "--place", "Sehore",
                               "--lat", "23.2032", "--lon", "77.0856",
                               "--timezone", "Asia/Kolkata", "--no-features")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JYOTISH CHART", result.stdout)

    def test_list_cities(self):
        result = self.run_main("--list-cities")
        self.assertEqual(result.returncode, 0)
        self.assertIn("jaipur", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
