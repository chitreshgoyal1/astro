#!/usr/bin/env python3
"""
Clean-install verification (V1.8 Part 34)
-------------------------------------------
    python3 tools/verify_package.py [--package dist/jyotish-1.8.0.tar.gz]

Unpacks the built archive into a temporary directory and exercises every
capability Part 34 lists, using a SEPARATE interpreter with a cleared
environment.

WHY A SUBPROCESS AND A CLEARED ENVIRONMENT

    Running the checks in this process would import the development
    checkout: `sys.path` already contains it, `PYTHONPATH` may add more,
    and a package missing a whole directory would pass because the
    modules were already loaded from somewhere else.

    So each check is a subprocess, launched with `env -i` semantics —
    no PYTHONPATH, no PYTHONHOME, no site customisation — with its
    working directory inside the unpacked package. A dependency that is
    only present in the development environment then fails here, which
    is the entire point.

WHAT IS VERIFIED

    Part 34's list, one check each: launch, consultation creation, chart
    calculation, interpretation, SVG charts, English PDF, Hindi PDF,
    save, load, migration, transit query. Plus the negative that matters:
    that the package does not import pyswisseph, which is present in the
    development environment and must not be needed at run time.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import Sequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Environment for every subprocess. Deliberately minimal.
CLEAN_ENV = {
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "HOME": tempfile.gettempdir(),
    "LC_ALL": "C.UTF-8",
    "LANG": "C.UTF-8",
    "PYTHONDONTWRITEBYTECODE": "1",
}

BIRTH = ("--name", "Verification", "--dob", "1988-08-30",
         "--time", "20:18", "--place", "Jaipur")


class Check:
    def __init__(self, name: str, arguments, produces: str = "",
                 expect: Sequence[str] = ()):
        self.name = name
        self.arguments = list(arguments)
        self.produces = produces
        self.expect = list(expect)


def _run(python: str, package: str, arguments, workdir: str):
    return subprocess.run(
        [python, os.path.join(package, "main.py"), *arguments],
        cwd=workdir, env=CLEAN_ENV, capture_output=True, text=True,
        timeout=600)


def verify(archive: str, python: str = "") -> dict:
    python = python or sys.executable
    workdir = tempfile.mkdtemp(prefix="jyotish-verify-")
    try:
        with tarfile.open(archive) as tar:
            tar.extractall(workdir)
        roots = [name for name in os.listdir(workdir)
                 if os.path.isdir(os.path.join(workdir, name))]
        if len(roots) != 1:
            raise RuntimeError(
                f"expected one directory in the archive, found {roots}")
        package = os.path.join(workdir, roots[0])
        output = os.path.join(workdir, "out")
        os.makedirs(output, exist_ok=True)

        checks = [
            Check("launch", ["--help"], expect=["--app"]),
            Check("self check", ["--self-check"], expect=["0 failed"]),
            Check("privacy statement", ["--privacy"],
                  expect=["WHAT LEAVES THE MACHINE"]),
            Check("chart calculation", [*BIRTH],
                  expect=["Lagna", "Chandra"]),
            Check("interpretation",
                  [*BIRTH, "--interpret", "2026-09-27"],
                  expect=["Jyotish"]),
            Check("transit query",
                  [*BIRTH, "--synthesis", "2026-09-27"],
                  expect=["SYNTHESIS"]),
            Check("svg charts",
                  [*BIRTH, "--report-html",
                   os.path.join(output, "report.html")],
                  produces=os.path.join(output, "report.html")),
            Check("english pdf",
                  [*BIRTH, "--report", os.path.join(output, "en.pdf")],
                  produces=os.path.join(output, "en.pdf")),
            Check("hindi pdf",
                  [*BIRTH, "--language", "hi", "--report",
                   os.path.join(output, "hi.pdf")],
                  produces=os.path.join(output, "hi.pdf")),
            Check("south indian charts",
                  [*BIRTH, "--chart-style", "south_indian", "--report",
                   os.path.join(output, "south.pdf")],
                  produces=os.path.join(output, "south.pdf")),
            Check("save",
                  [*BIRTH, "--save-consultation",
                   os.path.join(output, "saved.json")],
                  produces=os.path.join(output, "saved.json")),
            Check("load",
                  ["--open-consultation", os.path.join(output, "saved.json")],
                  expect=["Loaded"]),
            Check("export",
                  [*BIRTH, "--export-consultations",
                   os.path.join(output, "export.json")],
                  produces=os.path.join(output, "export.json")),
            Check("import",
                  ["--import-consultations",
                   os.path.join(output, "export.json")],
                  expect=["Read 1 consultation"]),
            Check("benchmark", [*BIRTH, "--benchmark"],
                  expect=["end to end"]),
        ]

        results = []
        for check in checks:
            try:
                completed = _run(python, package, check.arguments, workdir)
                blob = completed.stdout + completed.stderr
                ok = completed.returncode == 0
                detail = ""
                if not ok:
                    detail = blob.strip().splitlines()[-1] if blob else \
                        f"exit {completed.returncode}"
                for wanted in check.expect:
                    if wanted not in blob:
                        ok, detail = False, f"output lacks {wanted!r}"
                        break
                if ok and check.produces:
                    if not os.path.exists(check.produces):
                        ok, detail = False, "produced no file"
                    else:
                        size = os.path.getsize(check.produces)
                        if size == 0:
                            ok, detail = False, "produced an empty file"
                        else:
                            detail = f"{size:,} bytes"
            except subprocess.TimeoutExpired:
                ok, detail = False, "timed out"
            results.append({"check": check.name, "ok": ok, "detail": detail})

        results.append(_migration_check(python, package, workdir))
        results.append(_dependency_check(package))

        failed = [r for r in results if not r["ok"]]
        return {
            "archive": archive,
            "package": roots[0],
            "python": python,
            "results": results,
            "passed": len(results) - len(failed),
            "failed": len(failed),
            "ok": not failed,
        }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _migration_check(python: str, package: str, workdir: str) -> dict:
    """A v1 consultation, written by hand, must still open."""
    legacy = os.path.join(workdir, "legacy.json")
    with open(legacy, "w", encoding="utf-8") as handle:
        json.dump({
            "schema_version": "1.0.0",
            "application_version": "1.7.0",
            "input": {"name": "Legacy", "date_of_birth": "1988-08-30",
                      "time_of_birth": "20:18", "place": "Jaipur",
                      "birth_time_precision": "EXACT_TO_MINUTE"},
            "settings": {"ayanamsha": "raman", "language": "en"},
            "report": {"mode": "summary"},
        }, handle)
    completed = _run(python, package, ["--open-consultation", legacy],
                     workdir)
    blob = completed.stdout + completed.stderr
    ok = (completed.returncode == 0
          and "migrated 1.0.0 to 2.0.0" in blob
          and "raman ayanamsha" in blob)
    return {
        "check": "migration (v1 file)", "ok": ok,
        "detail": ("v1 split into calculation/presentation, saved "
                   "ayanamsha kept" if ok
                   else (blob.strip().splitlines() or ["failed"])[-1][:90]),
    }


def _dependency_check(package: str) -> dict:
    """
    The packaged tree imports nothing third-party.

    Checked by reading the source rather than by importing, because an
    import test passes on a machine that happens to have the dependency
    — which is every development machine.
    """
    import ast

    third_party = {"swisseph", "numpy", "requests", "reportlab", "PIL",
                   "fontTools", "lxml", "pytz", "dateutil"}
    offenders = []
    for base, directories, files in os.walk(package):
        directories[:] = [d for d in directories if d != "__pycache__"]
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(base, name)
            try:
                with open(path, encoding="utf-8") as handle:
                    tree = ast.parse(handle.read(), filename=path)
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [(node.module or "").split(".")[0]]
                else:
                    continue
                for module in names:
                    if module in third_party:
                        offenders.append(
                            f"{os.path.relpath(path, package)}: {module}")
    return {
        "check": "no third-party imports",
        "ok": not offenders,
        "detail": "; ".join(sorted(set(offenders))) if offenders
                  else "stdlib only",
    }


def format_report(report: dict) -> str:
    lines = ["", "  CLEAN-INSTALL VERIFICATION", "  " + "─" * 72,
             f"  package: {report['package']}",
             f"  python:  {report['python']}", "  " + "─" * 72]
    for result in report["results"]:
        mark = "ok  " if result["ok"] else "FAIL"
        lines.append(f"  {mark}  {result['check']:<26} {result['detail']}")
    lines.append("  " + "─" * 72)
    lines.append(f"  {report['passed']} passed, {report['failed']} failed")
    lines.append("")
    lines.append("  Every check ran in a subprocess with a cleared "
                 "environment, from the")
    lines.append("  unpacked archive — not from the development checkout.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--package", default="", help="Path to the tarball")
    parser.add_argument("--python", default="",
                        help="Interpreter to verify against")
    arguments = parser.parse_args()

    archive = arguments.package
    if not archive:
        sys.path.insert(0, ROOT)
        from app.version import APPLICATION_VERSION

        archive = os.path.join(ROOT, "dist",
                               f"jyotish-{APPLICATION_VERSION}.tar.gz")
    if not os.path.exists(archive):
        print(f"\n  No package at {archive}.")
        print("  Build one first: python3 tools/build_package.py\n")
        return 2

    report = verify(archive, arguments.python)
    print(format_report(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
