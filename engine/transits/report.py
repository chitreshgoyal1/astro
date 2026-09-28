"""
TRANSIT report section (V1.4 Part 22)
---------------------------------------
Positions and relationships. No judgement of any kind.
"""

from __future__ import annotations

from .models import TransitSnapshot

_WIDTH = 100
_RULE = "─"


def format_transit_report(snapshot: TransitSnapshot,
                          max_relationships: int = 20) -> str:
    lines: list[str] = []
    add = lines.append

    add("")
    add("═" * _WIDTH)
    add("  TRANSITS  (calculated positions and relationships — no prediction)")
    add("═" * _WIDTH)
    add(f"  Moment   : {snapshot.moment.isoformat()}")
    settings = snapshot.calculation_settings
    add(f"  Settings : {settings.get('ayanamsha')} ayanamsha, "
        f"{settings.get('node')} node, node aspects "
        f"{settings.get('node_aspects')}, orb {settings.get('orb_deg')}°")

    add("")
    add("  TRANSITING POSITIONS")
    add("  " + _RULE * (_WIDTH - 2))
    add(f"  {'Graha':<9}{'Sign':<12}{'Degree':>9}  {'Nakshatra':<20}{'P':>2}"
        f"{'Motion':>12}{'H/Lagna':>9}{'H/Moon':>8}")
    for name, position in snapshot.positions.items():
        motion = ("stationary" if position.stationary
                  else "retrograde" if position.retrograde else "direct")
        add(f"  {name:<9}{position.sign_name:<12}"
            f"{position.degree_in_sign:>8.3f}°  {position.nakshatra:<20}"
            f"{position.pada:>2}{motion:>12}"
            f"{str(position.house_from_natal_lagna or '—'):>9}"
            f"{str(position.house_from_natal_moon or '—'):>8}")

    if snapshot.relationships:
        held = [r for r in snapshot.relationships
                if r.same_sign or r.graha_drishti or r.within_orb]
        add("")
        add(f"  TRANSIT TO NATAL — relationships that hold ({len(held)})")
        add("  " + _RULE * (_WIDTH - 2))
        add(f"  {'Transit':<9}{'Natal':<10}{'Same rashi':<12}"
            f"{'Separation':>12}{'Drishti':<16}Within orb")
        for relationship in held[:max_relationships]:
            add(f"  {relationship.transit_planet:<9}"
                f"{relationship.natal_target:<10}"
                f"{('yes' if relationship.same_sign else 'no'):<12}"
                f"{relationship.angular_separation:>11.3f}°"
                f"  {(relationship.drishti_type or '—'):<14}"
                f"{'yes' if relationship.within_orb else 'no'}")
        if len(held) > max_relationships:
            add(f"  … and {len(held) - max_relationships} more")

    add("")
    add("  Same-rashi and angular separation are SEPARATE facts: two grahas "
        "can share a")
    add("  rashi while 29° apart, or sit 1° apart across a rashi boundary.")
    add("  No Gochara rule, no benefic or malefic judgement, no prediction.")
    add("═" * _WIDTH)
    return "\n".join(lines)


def format_events(events: list) -> str:
    lines: list[str] = []
    add = lines.append
    add("")
    add("  TRANSIT EVENTS  (astronomical state changes only)")
    add("  " + _RULE * (_WIDTH - 2))
    if not events:
        add("  None in the window.")
        return "\n".join(lines)
    add(f"  {'When':<22}{'Kind':<22}{'Graha':<9}Detail")
    for event in events:
        add(f"  {event.moment.strftime('%Y-%m-%d %H:%M'):<22}"
            f"{event.kind:<22}{event.planet:<9}{event.detail}")
    add("")
    add("  An ingress is an ingress. Nothing here is labelled good or bad.")
    return "\n".join(lines)
