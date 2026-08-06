"""Canonical source of the modules the periodic MoleditPy plugins share.

Nothing imports this package at runtime.  Plugins are installed as
self-contained folders and cannot import from one another, so each vendors a
byte-identical copy of the files here — see ``scripts/sync_shared.py``.
"""

from __future__ import annotations

#: module name -> the version its file declares, kept in step by the tests.
MODULES = (
    "cell_model",
    "elements",
    "cell_preview",
    "structure_panel",
)
