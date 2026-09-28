"""
Regenerate SOURCE_VALIDATION.md from the source registry.

The report is generated rather than written by hand so it cannot drift away
from what the code actually asserts. Run after any change to
engine/sources/registry.py.

    python3 tools/generate_source_report.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.sources.report import write_report  # noqa: E402


def main() -> int:
    path = write_report(os.path.join(ROOT, "SOURCE_VALIDATION.md"))
    print(f"wrote {path} ({os.path.getsize(path) / 1024:.0f} KiB)")
    from engine.sources import registry_summary
    summary = registry_summary()
    print(f"  rules:  {summary['rules_by_status']}")
    print(f"  vargas: {summary['vargas_by_status']}")
    print(f"  tradition validated: {summary['tradition_validated']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
