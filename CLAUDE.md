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
3. Use one repository version, starting at **1.0.0**. Keep `VERSION`,
   `periodic_shared.__version__`, and every file's `SHARED_MODULE_VERSION`
   identical, including modules whose implementation did not change.
4. Commit with `Assisted-by: GPT-6 Sol`, push main, and wait for CI to pass.
   Then push the repository tag `v1.0.0` (or the next version). The release
   contains all shared modules together; do not create per-module tags.
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

6. Update and release **all four dependent plugins**. Bump each plugin's minor
   version, run its tests, commit with `Assisted-by: GPT-6 Sol`, push main,
   wait for CI, then push its `v<version>` tag. Update the local plugin registry
   using its scripts or automated workflow, never by hand.

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
host's PyVista plotter, and `structure_panel` imports PySide6 — all inside
functions where possible, so a plugin's declared dependencies stay honest.

The Slab Builder has its own dialog and does not use `structure_panel.py`;
its `materialize_shared.py` copies only the first three files.

## Testing

```bash
python -m pytest tests/ -v
python -m pytest tests/ --cov=periodic_shared --cov-report=term-missing
```

Real PySide6 and RDKit, offscreen via `QT_QPA_PLATFORM`. RDKit-dependent tests use
`pytest.importorskip("rdkit")` so the suite still runs without it.

## Conventions

- Files are written with `newline="\n"`.
- pymatgen is optional and imported inside a `try` (space-group expansion for
  CIFs that carry no symmetry-operation loop). Do not add hard dependencies:
  everything here must work on numpy alone plus what the host supplies.
- Comments explain why, not what, and only where the reason is not obvious.
