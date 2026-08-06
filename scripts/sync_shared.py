#!/usr/bin/env python3
"""Copy the shared modules into a plugin, and record what was copied.

Plugins are installed as self-contained folders and cannot import from one
another, so each carries a byte-identical copy of the files in
``periodic_shared/``.  This script is the only sanctioned way to update one: it
writes the file and the plugin's ``.shared-versions.json`` together, so a copy
that has been edited by hand fails the plugin's own hash check.

    python scripts/sync_shared.py ../moleditpy_vasp_input_generator
    python scripts/sync_shared.py ../moleditpy_slab_builder --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(HERE, "periodic_shared")
MANIFEST_NAME = ".shared-versions.json"

#: Not every plugin takes every module — the Slab Builder has its own dialog and
#: so has no use for the structure panel.
ALWAYS = ("cell_model.py", "elements.py", "cell_preview.py")
OPTIONAL = ("structure_panel.py",)

_NAME_RE = re.compile(r'^SHARED_MODULE_NAME\s*=\s*["\'](.+?)["\']', re.M)
_VERSION_RE = re.compile(r'^SHARED_MODULE_VERSION\s*=\s*["\'](.+?)["\']', re.M)


def sha256(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def module_identity(path: str):
    """(SHARED_MODULE_NAME, SHARED_MODULE_VERSION) declared inside a file."""
    text = open(path, encoding="utf-8").read()
    name = _NAME_RE.search(text)
    version = _VERSION_RE.search(text)
    if not name or not version:
        raise SystemExit(f"{path} declares no SHARED_MODULE_NAME/VERSION")
    return name.group(1), version.group(1)


def package_dir(plugin_root: str) -> str:
    """The plugin's package folder — the one holding __init__.py."""
    for entry in sorted(os.listdir(plugin_root)):
        candidate = os.path.join(plugin_root, entry)
        if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, "__init__.py")):
            if entry not in ("tests", "scripts"):
                return candidate
    raise SystemExit(f"no plugin package found in {plugin_root}")


def files_for(target: str):
    """Modules this plugin takes: the mandatory ones plus any it already has."""
    names = list(ALWAYS)
    names += [name for name in OPTIONAL if os.path.isfile(os.path.join(target, name))]
    return names


def sync(plugin_root: str, check_only: bool = False) -> int:
    target = package_dir(plugin_root)
    manifest_path = os.path.join(plugin_root, MANIFEST_NAME)
    manifest = {}
    problems = []

    for filename in files_for(target):
        source = os.path.join(SOURCE_DIR, filename)
        destination = os.path.join(target, filename)
        name, version = module_identity(source)
        digest = sha256(source)
        manifest[filename] = {"module": name, "version": version, "sha256": digest}

        if check_only:
            if not os.path.isfile(destination):
                problems.append(f"{filename}: missing from {target}")
            elif sha256(destination) != digest:
                problems.append(
                    f"{filename}: vendored copy differs from {name} {version}"
                )
            continue

        with open(source, "rb") as handle:
            data = handle.read()
        with open(destination, "wb") as handle:
            handle.write(data)
        print(f"  {filename:22} {name} {version}")

    if check_only:
        for problem in problems:
            print(f"  MISMATCH {problem}", file=sys.stderr)
        return 1 if problems else 0

    with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"  wrote {MANIFEST_NAME}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin", nargs="+", help="path to a plugin repository")
    parser.add_argument(
        "--check",
        action="store_true",
        help="report differences instead of writing anything",
    )
    args = parser.parse_args()

    status = 0
    for plugin in args.plugin:
        print(os.path.basename(os.path.abspath(plugin)) + ":")
        status |= sync(os.path.abspath(plugin), check_only=args.check)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
