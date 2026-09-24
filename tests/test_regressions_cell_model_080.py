"""Regressions fixed in cell-model 0.8.0; every test here fails on 0.7.0."""

import numpy as np
import pytest

from periodic_shared import cell_model as cm

HEAD = """data_{name}
_cell_length_a {a}
_cell_length_b {a}
_cell_length_c {a}
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
"""
LOOP = """loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
"""


def _head(name="x", a=10):
    return HEAD.format(name=name, a=a)


# --------------------------------------------------------------------------
# CIF reading
# --------------------------------------------------------------------------


def test_primed_labels_parse():
    """Nucleotide labels (C1', O5'') are ordinary values, not open strings."""
    cell = cm.parse_cif(_head() + LOOP + "C1' C 0.1 0.1 0.1\nO5'' O 0.2 0.2 0.2\n")
    assert [atom.label for atom in cell.atoms] == ["C1'", "O5''"]


def test_quoted_values_still_parse():
    tokens = cm._split_cif_line("_symmetry_space_group_name_H-M 'P 21/c'  # comment")
    assert tokens == ["_symmetry_space_group_name_H-M", "P 21/c"]


def test_quote_inside_a_quoted_value():
    assert cm._split_cif_line("'it's here' next") == ["it's here", "next"]


def test_comment_after_a_primed_label_is_stripped():
    assert cm._strip_comment("C1' C 0 0 0 # note").strip() == "C1' C 0 0 0"


def test_two_data_blocks_are_not_mixed():
    """The cell used to come from the last block and the atoms from the first."""
    text = _head("first", 10) + LOOP + "Na1 Na 0 0 0\n" + _head("second", 4) + LOOP + "K1 K 0 0 0\n"
    cell = cm.parse_cif(text)
    assert cell.name == "first"
    assert cell.lengths[0] == pytest.approx(10.0)
    assert [atom.element for atom in cell.atoms] == ["Na"]


def test_a_leading_block_without_a_structure_is_skipped():
    text = "data_global\n_journal_year 2020\n" + _head("real", 5) + LOOP + "Si1 Si 0 0 0\n"
    cell = cm.parse_cif(text)
    assert cell.name == "real" and len(cell.atoms) == 1


def test_aniso_loop_before_the_atom_loop():
    aniso = "loop_\n_atom_site_aniso_label\n_atom_site_aniso_U_11\nNa1 0.01\n"
    cell = cm.parse_cif(_head() + aniso + LOOP + "Na1 Na 0 0 0\n")
    assert len(cell.atoms) == 1


# --------------------------------------------------------------------------
# molecules with ghost atoms
# --------------------------------------------------------------------------


class _Atom:
    def __init__(self, symbol, number, custom=None):
        self.symbol, self.number, self.custom = symbol, number, custom

    def HasProp(self, key):
        return self.custom is not None

    def GetProp(self, key):
        return self.custom

    def GetSymbol(self):
        return self.symbol

    def GetAtomicNum(self):
        return self.number

    def GetFormalCharge(self):
        return 0

    def GetNumRadicalElectrons(self):
        return 0


class _Point:
    def __init__(self, x):
        self.x, self.y, self.z = x, 0.0, 0.0


class _Conformer:
    def GetAtomPosition(self, index):
        return _Point(float(index))


class _Mol:
    def __init__(self, atoms):
        self.atoms = atoms

    def GetConformer(self):
        return _Conformer()

    def GetNumAtoms(self):
        return len(self.atoms)

    def GetAtomWithIdx(self, index):
        return self.atoms[index]


def _probe_molecule():
    return _Mol(
        [
            _Atom("C", 6),
            _Atom("*", 0, "Bq"),  # NICS probe for Gaussian
            _Atom("C", 6),
            _Atom("*", 0, "H:"),  # NICS probe for ORCA
            _Atom("H", 1, "H:"),  # XYZ Editor ghost hydrogen
            _Atom("*", 0),  # bare dummy
            _Atom("O", 8),
        ]
    )


def test_ghosts_are_not_written_as_atoms():
    """Bq used to become boron and H: a real hydrogen."""
    assert cm.molecule_arrays(_probe_molecule())[1] == ["C", "C", "O"]


def test_boxed_molecule_counts_and_reports_dropped_ghosts():
    cell = cm.molecule_to_cell(_probe_molecule(), padding=5.0)
    assert cell.ghosts_dropped == 4
    assert any("ghost" in message for message in cm.structure_warnings(cell))


def test_source_indices_survive_dropping_and_supercells():
    cell = cm.molecule_to_cell(_probe_molecule(), padding=5.0)
    assert [atom.source_index for atom in cell.atoms] == [0, 2, 6]
    bigger = cm.make_supercell(cell, [2, 1, 1])
    assert [atom.source_index for atom in bigger.atoms] == [0, 2, 6, 0, 2, 6]
    assert bigger.ghosts_dropped == 4
    assert cm.cell_with_lattice(cell, cell.lengths, cell.angles).ghosts_dropped == 4


def test_a_molecule_of_only_ghosts_is_refused():
    with pytest.raises(ValueError, match="ghost"):
        cm.molecule_arrays(_Mol([_Atom("*", 0, "Bq")]))


@pytest.mark.parametrize("symbol", ["Bq", "bq", "H-Bq", "C:", "H:"])
def test_ghost_symbols(symbol):
    assert cm.is_ghost_symbol(symbol)


@pytest.mark.parametrize("symbol", ["B", "H", "Ba", ""])
def test_real_symbols(symbol):
    assert not cm.is_ghost_symbol(symbol)


# --------------------------------------------------------------------------
# vacuum across the cell boundary
# --------------------------------------------------------------------------


def _slab(fractions, c=20.0):
    lattice = np.diag([3.0, 3.0, c])
    atoms = tuple(
        cm.CellAtom("Cu", "Cu", np.array([0.0, 0.0, f]), np.array([0.0, 0.0, f]) @ lattice)
        for f in fractions
    )
    return cm.Cell("slab", (3.0, 3.0, c), (90.0, 90.0, 90.0), lattice, atoms)


def test_slab_straddling_c_zero_has_its_vacuum():
    cell = _slab([0.95, 0.0, 0.05])
    assert cm.vacuum_gap(cell) == pytest.approx(18.0)
    assert cm.looks_like_slab(cell)


def test_centred_slab_is_unchanged():
    assert cm.vacuum_gap(_slab([0.45, 0.5, 0.55])) == pytest.approx(18.0)
