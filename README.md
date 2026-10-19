# MoleditPy periodic shared modules

The single source of truth for the code the four periodic MoleditPy plugins
have in common:

| Module | `SHARED_MODULE_NAME` | Used by |
|---|---|---|
| `cell_model.py` | `periodic-cell-model` | all four |
| `elements.py` | `periodic-elements` | all four |
| `cell_preview.py` | `periodic-cell-preview` | all four |
| `structure_panel.py` | `periodic-structure-panel` | the three input generators |

The plugins:
[VASP](https://github.com/HiroYokoyama/moleditpy_vasp_input_generator) ·
[Quantum ESPRESSO](https://github.com/HiroYokoyama/moleditpy_quantum_espresso_input_generator) ·
[CP2K](https://github.com/HiroYokoyama/moleditpy_cp2k_input_generator) ·
[Slab Builder](https://github.com/HiroYokoyama/moleditpy_slab_builder)

## Why the code is copied rather than imported

A MoleditPy plugin is installed as a self-contained folder in the plugins
directory. It cannot import from another plugin, so **every plugin carries a
byte-identical copy** of the modules above. This repository is where they are
edited and tested; the copies are written by a script and verified by a hash.

## Version and release workflow

All shared modules use one repository version, starting at **1.0.0**.
Keep `VERSION`, `periodic_shared.__version__`, and every
`SHARED_MODULE_VERSION` identical. Releases use `v1.0.0` style tags and
include every module in one archive.

1. Edit the canonical modules and their tests; run `python -m pytest tests/ -v`.
2. Bump the repository version and all module version declarations together.
3. Commit, push main, and wait for CI before pushing the `v<version>` tag.
4. In each of the four plugins, advance `_periodic_shared` to that release
   commit and run `python scripts/materialize_shared.py`.
5. Run each plugin's tests, bump its minor version, push main, wait for CI,
   then push its own `v<version>` release tag.

Never edit materialized copies directly. The submodule pins the shared commit
and materialization records the module versions and hashes.

## Checking without changing anything

```bash
python scripts/sync_shared.py ../moleditpy_slab_builder --check
```

Exits non-zero and names the file if a plugin's copy has drifted. Each plugin
also runs `tests/test_shared_materialized.py`, which compares its vendored files
against the `.shared-versions.json` written by the sync — so a copy edited by
hand in a plugin fails that plugin's own CI.

## What lives where

- Shared modules and **their tests** live here, once. They used to be
  duplicated four times: ~6,300 lines of source and ~5,900 lines of tests.
- Plugin-specific code — writers, dialogs, pseudopotential handling — stays in
  the plugin, and each plugin's coverage now measures only what it owns
  (`.coveragerc` omits the vendored files).

## Licence

LGPL-3.0-or-later, matching the plugins.

## Licensing scope

First-party code in this migration is LGPL-3.0-or-later. See [LICENSE](LICENSE), [COPYING](COPYING) and [dependency/provenance terms](LICENSING.md). Third-party components and historical releases retain their own terms.
