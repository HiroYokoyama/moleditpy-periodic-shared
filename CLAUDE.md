# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

`moleditpy-periodic-shared` — the canonical copy of the modules the four
periodic MoleditPy plugins share, and the only place their tests live.

Nothing imports this package at runtime. A plugin is installed as a
self-contained folder and cannot import from another plugin, so each **vendors
a byte-identical copy** of these files.

## The workflow, in order

1. Edit the module in `periodic_shared/` and its test in `tests/`.
2. `python -m pytest tests/ -v` — everything here must stay green and near 100%.
3. Bump `SHARED_MODULE_VERSION` **inside the file you changed**. Each module is
   versioned independently of the others and of any plugin.
4. Commit, then tag that module alone: `cell-model-v0.8.0`, `elements-v0.3.0`,
   `cell-preview-v0.6.0`, `structure-panel-v0.12.0`.
5. `python scripts/sync_shared.py ../moleditpy_*` — writes the copies **and**
   each plugin's `.shared-versions.json` together.
6. Run every plugin's own suite, then release the plugins.

Never edit a vendored copy inside a plugin. `tests/test_shared_sync.py` there
compares the file's hash against the manifest and fails if you do — that is the
point of the manifest, and it replaces the old convention of remembering to
update a version pin by hand in four places.

## Modules

| File | `SHARED_MODULE_NAME` | Vendored into |
|---|---|---|
| `cell_model.py` | `periodic-cell-model` | all four plugins |
| `elements.py` | `periodic-elements` | all four plugins |
| `cell_preview.py` | `periodic-cell-preview` | all four plugins |
| `structure_panel.py` | `periodic-structure-panel` | the three input generators |

`cell_model` imports `elements` for the element table and covalent radii, so
those two always travel together. `cell_preview` imports RDKit and drives the
host's PyVista plotter, and `structure_panel` imports PyQt6 — all inside
functions where possible, so a plugin's declared dependencies stay honest.

`scripts/sync_shared.py` decides what a plugin takes: `cell_model`, `elements`
and `cell_preview` always, `structure_panel` only if the plugin already has one
(the Slab Builder has its own dialog instead).

## Testing

```bash
python -m pytest tests/ -v
python -m pytest tests/ --cov=periodic_shared --cov-report=term-missing
```

Real PyQt6 and RDKit, offscreen via `QT_QPA_PLATFORM`. RDKit-dependent tests use
`pytest.importorskip("rdkit")` so the suite still runs without it.

## Conventions

- Files are written with `newline="\n"`.
- pymatgen is optional and imported inside a `try` (space-group expansion for
  CIFs that carry no symmetry-operation loop). Do not add hard dependencies:
  everything here must work on numpy alone plus what the host supplies.
- Comments explain why, not what, and only where the reason is not obvious.
