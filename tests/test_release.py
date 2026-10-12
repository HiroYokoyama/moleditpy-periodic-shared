from pathlib import Path
from zipfile import ZipFile

import pytest

from periodic_shared import MODULES, __version__
from scripts.package_release import build_release

ROOT = Path(__file__).resolve().parent.parent


def test_all_modules_share_repository_version():
    import importlib

    assert (ROOT / "VERSION").read_text().strip() == __version__ == "1.0.0"
    for module in MODULES:
        assert importlib.import_module(f"periodic_shared.{module}").SHARED_MODULE_VERSION == __version__


def test_release_archive(tmp_path):
    import shutil

    shutil.copytree(ROOT / "periodic_shared", tmp_path / "periodic_shared")
    for filename in ("VERSION", "LICENSE", "README.md"):
        shutil.copyfile(ROOT / filename, tmp_path / filename)
    archive = build_release("v1.0.0", tmp_path)
    with ZipFile(archive) as package:
        assert set(package.namelist()) == {
            "periodic_shared/__init__.py", *(f"periodic_shared/{name}.py" for name in MODULES),
            "VERSION", "LICENSE", "README.md",
        }
    with pytest.raises(ValueError, match="tag"):
        build_release("v2.0.0", tmp_path)
    (tmp_path / "periodic_shared" / "elements.py").write_text('SHARED_MODULE_VERSION = "0.2.0"')
    with pytest.raises(ValueError, match="elements"):
        build_release("v1.0.0", tmp_path)
