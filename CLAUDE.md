# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

`moleditpy-periodic-shared` — the canonical copy of the modules the four
periodic MoleditPy plugins share, and the only place their tests live.

Nothing imports this package at runtime. A plugin is installed as a
self-contained folder and cannot import from another plugin. Each plugin vendors
these files via a `_periodic_shared` **git submodule** that points at a specific
commit of this repository. At test and build time, `scripts/materialize_shared.py`
inside each plugin copies the submodule's files into the package directory.

## The workflow, in order

1. Edit the module in `periodic_shared/` and its test in `tests/`.
2. `python -m pytest tests/ -v` — everything here must stay green and near 100%.
3. Bump `SHARED_MODULE_VERSION` **inside the file you changed**. Each module is
   versioned independently of the others and of any plugin.
4. Commit and push. Tag the changed module if releasing a named version:
   `cell-model-v0.8.0`, `elements-v0.3.0`, etc.
5. In each plugin repository that needs the update, advance the submodule pointer:

```bash
cd _periodic_shared
git pull origin main     # or checkout the specific tag
cd ..
git add _periodic_shared
git commit -m "chore: pull latest moleditpy-periodic-shared"
python scripts/materialize_shared.py   # refresh local copies
python -m pytest tests/ -v             # verify the plugin still passes
git push origin main
```

6. Release the plugins as usual.

**Never edit a vendored copy inside a plugin.** The materialized files are
listed in each plugin's `.gitignore` and are overwritten on every
`materialize_shared.py` run — edits there are silently lost.

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

The Slab Builder has its own dialog and does not use `structure_panel.py`;
its `materialize_shared.py` copies only the first three files.

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
