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

Publishing to PyPI and depending on it was the obvious alternative and was
rejected deliberately: two installed plugins could then resolve to different
versions of the same module inside one running app, silently. Copying makes
that impossible.

## Changing a shared module

```bash
# 1. edit the module here, and its tests
python -m pytest tests/ -v

# 2. bump SHARED_MODULE_VERSION inside the file you changed
#    (each module is versioned on its own, independently of any plugin)

# 3. commit, then tag that module's release
git tag cell-model-v0.8.0 && git push origin cell-model-v0.8.0

# 4. copy it into every plugin and update their manifests
python scripts/sync_shared.py \
    ../moleditpy_vasp_input_generator \
    ../moleditpy_quantum_espresso_input_generator \
    ../moleditpy_cp2k_input_generator \
    ../moleditpy_slab_builder

# 5. run each plugin's own suite, then release the plugins as usual
```

Tags are per module — `cell-model-v0.8.0`, `cell-preview-v0.6.0` — so each has
its own history and release notes rather than sharing one version number.

## Checking without changing anything

```bash
python scripts/sync_shared.py ../moleditpy_slab_builder --check
```

Exits non-zero and names the file if a plugin's copy has drifted. Each plugin
also runs `tests/test_shared_sync.py`, which compares its vendored files
against the `.shared-versions.json` written by the sync — so a copy edited by
hand in a plugin fails that plugin's own CI.

## What lives where

- Shared modules and **their tests** live here, once. They used to be
  duplicated four times: ~6,300 lines of source and ~5,900 lines of tests.
- Plugin-specific code — writers, dialogs, pseudopotential handling — stays in
  the plugin, and each plugin's coverage now measures only what it owns
  (`.coveragerc` omits the vendored files).

## Licence

GPL-3.0, matching the plugins.
