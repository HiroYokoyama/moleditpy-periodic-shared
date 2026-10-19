"""Verify the unified version and package the canonical shared modules."""

import os
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent


def build_release(tag: str, root: Path = ROOT) -> Path:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version) or tag != f"v{version}":
        raise ValueError("Release tag must match VERSION.")
    modules = sorted((root / "periodic_shared").glob("*.py"))
    for module in modules:
        variable = "__version__" if module.name == "__init__.py" else "SHARED_MODULE_VERSION"
        match = re.search(rf'^{variable}\s*=\s*"([^"]+)"', module.read_text(encoding="utf-8"), re.M)
        if match is None or match.group(1) != version:
            raise ValueError(f"{module.name} does not declare version {version}.")
    destination = root / "dist" / f"periodic-shared-{tag}.zip"
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in modules + [root / "VERSION", root / "LICENSE", root / "COPYING", root / "LICENSING.md", root / "README.md"]:
            archive.write(path, path.relative_to(root))
    return destination


if __name__ == "__main__":
    print(build_release(os.environ["RELEASE_TAG"]))
