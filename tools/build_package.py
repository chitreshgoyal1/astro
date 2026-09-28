#!/usr/bin/env python3
"""
Build a distributable package (V1.8 Parts 33, 34)
---------------------------------------------------
    python3 tools/build_package.py [--output dist] [--clean]

Produces a self-contained directory and a tarball of it, either of which
runs on a machine with nothing but a Python interpreter.

WHY A DIRECTORY AND NOT A ZIPAPP

    A `.pyz` is the tidier artefact and it does not work here. The
    templates, the bundled font and the licence beside it are opened with
    `open()` on a real path, and a zipapp would require either rewriting
    every resource read to go through `importlib.resources` or extracting
    to a cache directory at first run.

    The first is a large change to satisfy a packaging preference. The
    second makes a "self-contained" artefact that writes to somewhere the
    user did not choose the first time it starts, which contradicts what
    this application says about itself.

    So: a directory, plus a tarball of the directory. Both are ordinary,
    both are auditable with `ls`, and neither needs a build system.

WHAT GOES IN, AND WHAT DOES NOT

    In:  the engine, the application, the launcher, the templates, the
         bundled font and its licence, and the documentation.

    Out: the tests, the fixtures, the tools, the source-text corpus, and
         every `__pycache__`. The corpus is the important omission —
         those files are third-party texts that are cited by locator and
         are not this project's to redistribute.

REPRODUCIBLE

    The manifest records every file with its SHA-256, and the tarball is
    written with fixed timestamps and sorted entries, so two builds of
    the same tree produce identical bytes. A build that differs run to
    run cannot be checked against anything.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import sys
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

#: Packages and files the runtime needs. Everything else is excluded.
INCLUDE_PACKAGES = ("engine", "app")
INCLUDE_DATA = ("templates",)
INCLUDE_FILES = ("main.py", "varga_config.json", "sample_consultation.json")
INCLUDE_DOCS = (
    "USER_GUIDE.md", "METHODOLOGY.md", "SOURCE_VALIDATION.md",
    "TECHNICAL_ARCHITECTURE.md", "RELEASE_NOTES.md", "DOCUMENTATION.md",
    "AUDIT.md", "GOCHARA_AUDIT.md", "VARGA_DOMAIN_AUDIT.md",
    "DOMAIN_VALIDATION.md", "RULE_AUDIT_V15.md", "BHAVA_CHALIT_DESIGN.md",
)

#: Never packaged, wherever they appear.
EXCLUDE_NAMES = ("__pycache__", ".pytest_cache", ".DS_Store")
EXCLUDE_SUFFIXES = (".pyc", ".pyo")

LAUNCHER = """#!/bin/sh
# Jyotish — self-contained launcher.
#
# Runs the application from the directory this script sits in, with no
# installation step and no write to anywhere outside it.
here=$(cd "$(dirname "$0")" && pwd)
exec "${PYTHON:-python3}" "$here/main.py" "$@"
"""

README = """Jyotish {version}
{underline}

{description}

RUNNING IT

    ./jyotish --help
    ./jyotish --app                     open the local application
    ./jyotish --self-check              verify this copy is complete
    ./jyotish --privacy                 what is stored and what leaves

    On Windows, or without the launcher:

    python3 main.py --help

REQUIREMENTS

    Python {python_required} or newer. Nothing else. This package has no
    third-party dependencies and makes no network request at any point.

WHAT IS IN HERE

    engine/      the calculation engine
    app/         the application, reports and local interface
    templates/   interpretation text, one directory per language
    app/report/fonts/
                 the bundled Devanagari font and its OFL licence
    *.md         documentation, methodology and the source audits

    The Sanskrit source corpus is NOT included. Passages are cited by
    edition and locator; the texts themselves are third-party works and
    are not redistributed here.

VERIFYING THIS COPY

    manifest.json lists every file with its SHA-256. `./jyotish
    --self-check` verifies the resources the application needs at run
    time, including the font checksum.
"""


def _skip(name: str) -> bool:
    return (name in EXCLUDE_NAMES
            or name.endswith(EXCLUDE_SUFFIXES))


def _copy_tree(source: str, destination: str) -> list[str]:
    copied = []
    for base, directories, files in os.walk(source):
        directories[:] = sorted(d for d in directories if not _skip(d))
        relative = os.path.relpath(base, source)
        target = (destination if relative == "."
                  else os.path.join(destination, relative))
        os.makedirs(target, exist_ok=True)
        for name in sorted(files):
            if _skip(name):
                continue
            shutil.copy2(os.path.join(base, name),
                         os.path.join(target, name))
            copied.append(os.path.normpath(
                os.path.join(os.path.basename(destination), relative, name)))
    return copied


def _digest(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def build(output: str = "dist", clean: bool = False) -> dict:
    from app.version import (
        APPLICATION_VERSION, RELEASE_DESCRIPTION, RELEASE_NAME,
    )

    name = f"jyotish-{APPLICATION_VERSION}"
    base = os.path.join(ROOT, output)
    target = os.path.join(base, name)

    if clean and os.path.isdir(base):
        shutil.rmtree(base)
    if os.path.isdir(target):
        shutil.rmtree(target)
    os.makedirs(target, exist_ok=True)

    for package in INCLUDE_PACKAGES:
        _copy_tree(os.path.join(ROOT, package), os.path.join(target, package))
    for data in INCLUDE_DATA:
        _copy_tree(os.path.join(ROOT, data), os.path.join(target, data))
    for filename in INCLUDE_FILES:
        source = os.path.join(ROOT, filename)
        if os.path.exists(source):
            shutil.copy2(source, os.path.join(target, filename))
    missing_docs = []
    for filename in INCLUDE_DOCS:
        source = os.path.join(ROOT, filename)
        if os.path.exists(source):
            shutil.copy2(source, os.path.join(target, filename))
        else:
            missing_docs.append(filename)

    launcher = os.path.join(target, "jyotish")
    with open(launcher, "w", encoding="utf-8") as handle:
        handle.write(LAUNCHER)
    os.chmod(launcher, 0o755)

    heading = f"Jyotish {APPLICATION_VERSION}"
    with open(os.path.join(target, "README.txt"), "w",
              encoding="utf-8") as handle:
        handle.write(README.format(
            version=APPLICATION_VERSION, underline="=" * len(heading),
            description=RELEASE_DESCRIPTION,
            python_required="3.10"))

    # Manifest last, so it covers everything above it.
    entries = []
    for walk_base, directories, files in os.walk(target):
        directories[:] = sorted(d for d in directories if not _skip(d))
        for filename in sorted(files):
            if filename == "manifest.json" or _skip(filename):
                continue
            path = os.path.join(walk_base, filename)
            entries.append({
                "path": os.path.relpath(path, target).replace(os.sep, "/"),
                "bytes": os.path.getsize(path),
                "sha256": _digest(path),
            })
    entries.sort(key=lambda item: item["path"])

    manifest = {
        "name": name,
        "application_version": APPLICATION_VERSION,
        "release": RELEASE_NAME,
        "python_required": "3.10",
        "third_party_dependencies": [],
        "files": entries,
        "file_count": len(entries),
        "total_bytes": sum(item["bytes"] for item in entries),
        "excluded": [
            "tests/ and tests/fixtures/ — not needed to run",
            "tools/ — build and fixture generation only; these are the "
            "only files that import pyswisseph",
            "the Sanskrit source corpus — third-party texts, cited by "
            "locator and not redistributed",
        ],
        "note": ("Every file with its SHA-256. `--self-check` verifies the "
                 "resources the application needs at run time."),
    }
    with open(os.path.join(target, "manifest.json"), "w",
              encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    archive = _tarball(target, os.path.join(base, f"{name}.tar.gz"))
    manifest["directory"] = target
    manifest["archive"] = archive
    manifest["archive_bytes"] = os.path.getsize(archive)
    manifest["missing_docs"] = missing_docs
    return manifest


def _tarball(directory: str, path: str) -> str:
    """
    A gzip tarball with fixed metadata, so two builds are identical.

    Ownership, timestamps and the gzip header's own mtime all vary
    between machines and would make every build differ from every other
    for no reason anybody could act on.
    """
    import gzip

    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.GNU_FORMAT) as tar:
        for base, directories, files in os.walk(directory):
            directories[:] = sorted(directories)
            for name in sorted(files):
                full = os.path.join(base, name)
                info = tar.gettarinfo(full, arcname=os.path.join(
                    os.path.basename(directory),
                    os.path.relpath(full, directory)))
                info.uid = info.gid = 0
                info.uname = info.gname = "root"
                info.mtime = 0
                with open(full, "rb") as handle:
                    tar.addfile(info, handle)
    with open(path, "wb") as handle:
        handle.write(gzip.compress(raw.getvalue(), 9, mtime=0))
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--output", default="dist",
                        help="Directory to build into (default: dist)")
    parser.add_argument("--clean", action="store_true",
                        help="Remove the output directory first")
    arguments = parser.parse_args()

    manifest = build(arguments.output, clean=arguments.clean)
    print(f"\n  Built {manifest['name']}")
    print(f"    {manifest['file_count']} files, "
          f"{manifest['total_bytes']:,} bytes")
    print(f"    directory: {manifest['directory']}")
    print(f"    archive:   {manifest['archive']} "
          f"({manifest['archive_bytes']:,} bytes)")
    if manifest["missing_docs"]:
        print("    documents not found and therefore not packaged:")
        for name in manifest["missing_docs"]:
            print(f"      - {name}")
    print("\n  Verify with:")
    print(f"    {manifest['directory']}/jyotish --self-check\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
