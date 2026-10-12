"""Canonical source of the modules the periodic MoleditPy plugins share.

Nothing imports this package at runtime.  Plugins are installed as
self-contained folders and cannot import from one another, so each vendors a
byte-identical copy of the files here — see ``scripts/sync_shared.py``.
"""

from __future__ import annotations

__version__ = "1.0.0"

#: Modules released together under the repository version.
MODULES = (
    "cell_model",
    "elements",
    "cell_preview",
    "structure_panel",
)
