"""
ASTROLOGY FEATURES report section (Part 14)
-------------------------------------------
Renders the calculated feature set. Everything printed here is a fact derived
from the positions and the named conventions; no interpretation is added and
no text is generated. The provenance block at the top states which conventions
were in force, so a reader can tell which tradition produced each column.
"""

from __future__ import annotations

from .models import ChartFeatures

_RULE = "─"
_WIDTH = 100


def _short(name: str, length: int = 3) -> str:
    return name[:length]


def _fit(text: str, width: int) -> str:
    """Pad to width, or truncate with an ellipsis so columns never shift."""
    if len(text) <= width - 1:
        return text.ljust(width)
    return (text[:width - 2] + "…").ljust(width)


def _aspect_summary(features: ChartFeatures, planet: str) -> str:
    given = features.planets[planet].aspects_given
    if not given:
        return "—"
    return ", ".join(f"{a.to_house}{'' if a.full else '~'}" for a in given)


def _received_summary(features: ChartFeatures, planet: str) -> str:
    sources = features.planets[planet].aspecting_planets
    return ", ".join(_short(s) for s in sources) if sources else "—"


def _conjunction_summary(features: ChartFeatures, planet: str) -> str:
    same = features.planets[planet].conjunct_planets
    return ", ".join(_short(s) for s in same) if same else "—"


def format_feature_report(features: ChartFeatures) -> str:
    """The ASTROLOGY FEATURES block."""
    lines: list[str] = []
    add = lines.append

    add("")
    add("═" * _WIDTH)
    add("  ASTROLOGY FEATURES  (calculated facts — no interpretation)")
    add("═" * _WIDTH)

    add("")
    add("  Conventions in force")
    add("  " + _RULE * (_WIDTH - 2))
    for key, value in features.provenance.items():
        add(f"    {key.replace('_', ' '):<24} {value}")

    if features.warnings:
        add("")
        add("  Caveats")
        add("  " + _RULE * (_WIDTH - 2))
        for warning in features.warnings:
            add(f"    ! {warning}")

    # ── Lagna and house lords ────────────────────────────────────────────────
    add("")
    add(f"  LAGNA  {features.lagna_sign_name} {features.lagna_degree:.4f}°   "
        f"lord {features.lagna_lord}")
    add("")
    add("  HOUSE LORDS")
    add("  " + _RULE * (_WIDTH - 2))
    add(f"  {'House':<7}{'Sign':<12}{'Lord':<10}{'Lord in':<9}"
        f"{'Occupants':<26}{'Aspected by':<20}Category")
    for number in range(1, 13):
        bhava = features.houses[number]
        categories = [label for flag, label in (
            (bhava.is_kendra, "kendra"), (bhava.is_trikona, "trikona"),
            (bhava.is_dusthana, "dusthana"), (bhava.is_upachaya, "upachaya"),
            (bhava.is_maraka, "maraka"))if flag]
        add(f"  {number:<7}{bhava.sign_name:<12}{bhava.lord:<10}"
            f"{('h' + str(bhava.lord_house)) if bhava.lord_house else '—':<9}"
            f"{', '.join(bhava.occupants) or '—':<26}"
            f"{', '.join(_short(p) for p in bhava.aspecting_planets) or '—':<20}"
            f"{', '.join(categories) or '—'}")

    # ── Per-graha ────────────────────────────────────────────────────────────
    add("")
    add("  GRAHA FEATURES")
    add("  " + _RULE * (_WIDTH - 2))
    add(f"  {'Graha':<9}{'Sign':<12}{'Ho':<4}{'Owns':<8}{'Dignity':<15}"
        f"{'Disp':<9}{'Motion':<12}{'Combust':<20}Nature")
    for name, planet in features.planets.items():
        owns = ",".join(str(h) for h in planet.houses_owned) or "—"
        motion = ("stationary" if planet.stationary
                  else "retrograde" if planet.retrograde else "direct")
        if not planet.speed_is_measured:
            motion += "*"
        if planet.combust:
            combust = (f"yes {planet.sun_separation:.1f}°"
                       f"/{planet.combustion_orb:g}°")
        elif planet.sun_separation is None:
            combust = "— (is the Sun)"
        elif planet.combustion_orb is None:
            combust = f"never ({planet.sun_separation:.1f}° off)"
        else:
            combust = f"no  {planet.sun_separation:.1f}°/{planet.combustion_orb:g}°"
        nature = ("benefic" if planet.natural_benefic
                  else "malefic" if planet.natural_malefic else "neutral")
        add(f"  {name:<9}{planet.sign_name:<12}{planet.house:<4}{owns:<8}"
            f"{planet.dignity:<15}{planet.dispositor or '—':<9}{motion:<12}"
            f"{combust:<20}{nature}/{planet.functional_nature}")

    add("")
    add(f"  {'Graha':<9}{'Aspects houses':<20}{'Aspected by':<22}"
        f"{'Conjunct':<16}{'D9':<12}{'D10':<12}Vargottama")
    for name, planet in features.planets.items():
        d9 = planet.vargas.get("D9")
        d10 = planet.vargas.get("D10")
        add(f"  {name:<9}{_fit(_aspect_summary(features, name), 20)}"
            f"{_fit(_received_summary(features, name), 22)}"
            f"{_fit(_conjunction_summary(features, name), 16)}"
            f"{(d9.sign_name if d9 else '—'):<12}"
            f"{(d10.sign_name if d10 else '—'):<12}"
            f"{'yes' if planet.vargottama else '—'}")

    # ── numerical certainty ─────────────────────────────────────────────────
    add("")
    add("  NUMERICAL CERTAINTY  (is the classification resolved by the "
        "calculation?)")
    add("  " + _RULE * (_WIDTH - 2))
    add(f"  {'Graha':<9}{'Theory':<40}{'Envelope':<11}{'Nearest boundary':<20}"
        f"Verdict")
    for name, planet in features.planets.items():
        uncertainty = planet.uncertainty
        if uncertainty is None:
            continue
        nearest = min(uncertainty.proximities,
                      key=lambda p: p.distance_arcmin)
        verdict = ("UNRESOLVED: " + ", ".join(planet.boundary_types)
                   if planet.boundary_warning else "resolved")
        add(f"  {name:<9}{_fit(planet.theory, 40)}"
            f"{uncertainty.accuracy_arcmin:>6.2f}'    "
            f"{_fit(f'{nearest.boundary_type} {nearest.distance_arcmin:.2f}′',
                    20)}{verdict}")
    if features.lagna_uncertainty is not None:
        add(f"  {'Lagna':<9}{_fit('apparent sidereal time', 40)}"
            f"{features.lagna_uncertainty.accuracy_arcmin:>6.2f}'    "
            f"{'—':<20}"
            f"{'UNRESOLVED' if features.lagna_uncertainty.boundary_warning else 'resolved'}")
    add("  A placement is UNRESOLVED when it sits nearer a boundary than the "
        "engine's own")
    add("  measured worst-case error for that body. Verify those externally.")

    add("")
    add(f"  {'Graha':<9}{'Nakshatra':<20}{'Pada':<6}{'Lord':<9}"
        f"{'D9 dignity':<14}{'D10 dignity':<14}{'D30 dignity':<14}D60 dignity")
    for name, planet in features.planets.items():
        def label(key: str) -> str:
            placement = planet.vargas.get(key)
            return placement.dignity_label() if placement else "—"
        add(f"  {name:<9}{planet.nakshatra:<20}{planet.pada:<6}"
            f"{planet.nakshatra_lord:<9}{label('D9'):<14}{label('D10'):<14}"
            f"{label('D30'):<14}{label('D60')}")

    # ── Functional roles ─────────────────────────────────────────────────────
    add("")
    add("  FUNCTIONAL NATURE  (Lagna-dependent — ownership facts only)")
    add("  " + _RULE * (_WIDTH - 2))
    add(f"  {'Graha':<9}{'Nature':<12}{'Roles':<62}Why")
    for name, role in features.functional_roles.items():
        add(f"  {name:<9}{role.functional_nature:<12}"
            f"{_fit(', '.join(role.roles) or 'no functional role', 62)}"
            f"{role.reason}")

    # ── Dispositors ──────────────────────────────────────────────────────────
    add("")
    add("  DISPOSITOR CHAINS")
    add("  " + _RULE * (_WIDTH - 2))
    for name, chain in features.dispositor_details.items():
        add(f"  {chain.describe()}")

    if features.parivartanas:
        add("")
        add("  PARIVARTANA (mutual reception)")
        add("  " + _RULE * (_WIDTH - 2))
        for swap in features.parivartanas:
            add(f"  {swap.describe()}")

    # ── Conjunctions ─────────────────────────────────────────────────────────
    add("")
    add("  CONJUNCTIONS  (same-rashi and orb proximity kept separate)")
    add("  " + _RULE * (_WIDTH - 2))
    if features.conjunctions:
        add(f"  {'Pair':<22}{'Same rashi':<13}{'Separation':<13}"
            f"{'Within orb':<13}House")
        for conj in features.conjunctions:
            add(f"  {conj.planet1 + '+' + conj.planet2:<22}"
                f"{('yes' if conj.same_sign else 'no'):<13}"
                f"{conj.angular_separation:>8.2f}°    "
                f"{('yes' if conj.within_orb else 'no') + f' ({conj.orb_used:g}°)':<13}"
                f"{conj.house or '—'}")
    else:
        add("  None.")

    if features.graha_yuddha:
        add("")
        add("  GRAHA YUDDHA (planetary war)")
        add("  " + _RULE * (_WIDTH - 2))
        for war in features.graha_yuddha:
            add(f"  {war.describe()}")

    add("")
    add("  * motion marked with an asterisk was not measured — the position "
        "was entered, not calculated.")
    add("  ~ after an aspected house means a partial-strength drishti in the "
        "active profile.")
    add("═" * _WIDTH)
    return "\n".join(lines)
