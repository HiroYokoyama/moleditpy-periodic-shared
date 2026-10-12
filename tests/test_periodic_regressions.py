import itertools

import numpy as np
import pytest

from periodic_shared import cell_model as cm
from periodic_shared import cell_preview as cp


def test_unreduced_skew_cell_finds_image_outside_neighbour_cube():
    lattice = np.array([[1., 0, 0], [10, 1, 0], [0, 0, 1]])
    fraction = np.array([0., .49, 0.])
    assert cm.minimum_image_distance(fraction, np.zeros(3), lattice) == pytest.approx(
        np.linalg.norm(np.array([-5., .49, 0]) @ lattice))
    lengths, angles = cm.lattice_parameters(lattice)
    atoms = tuple(cm.CellAtom(str(i), "C", f, f @ lattice)
                  for i, f in enumerate([np.zeros(3), fraction]))
    cell = cm.Cell("skew", lengths, angles, lattice, atoms)
    assert cm.close_contacts(cell)[0][2] == pytest.approx(.500099990002)
    operations = [(np.eye(3), np.zeros(3)), (np.eye(3), fraction)]
    tiny = lattice * .05
    assert len(cm.apply_symmetry(atoms[:1], tiny, operations)) == 1


def test_minimum_images_match_exhaustive_reference():
    rng = np.random.default_rng(120)
    shifts = np.array(list(itertools.product(range(-6, 7), repeat=3)))
    for _ in range(20):
        lattice = np.eye(3) + rng.uniform(-.8, .8, (3, 3))
        if abs(np.linalg.det(lattice)) < .3:
            continue
        delta = rng.uniform(-.5, .5, 3)
        reference = min(np.linalg.norm((delta + shift) @ lattice) for shift in shifts)
        assert cm.minimum_image_distance(delta, np.zeros(3), lattice) == pytest.approx(reference)


@pytest.mark.parametrize("lattice", [np.zeros((3, 3)), np.full((3, 3), np.nan), np.eye(2)])
def test_invalid_distance_lattices_are_rejected(lattice):
    with pytest.raises(ValueError):
        cm.minimum_image_distance([0, 0, 0], [.5, 0, 0], lattice)


def test_nonfinite_fraction_is_rejected():
    with pytest.raises(ValueError):
        cm.minimum_image_distance([np.nan, 0, 0], [0, 0, 0], np.eye(3))


def test_primitive_reduction_preserves_disordered_species_and_occupancies():
    lattice = np.eye(3) * 4
    atoms = tuple(cm.CellAtom(f"{element}{i}", element, np.array(f), np.array(f) @ lattice, .5)
                  for element in ("Fe", "Co") for i, f in enumerate(([0, 0, 0], [.5, .5, .5])))
    cell = cm.Cell("mixed", (4.,) * 3, (90.,) * 3, lattice, atoms)
    primitive = cm.primitive_cell(cell)
    assert len(primitive.atoms) == 2
    assert sorted(primitive.elements) == ["Co", "Fe"]
    assert primitive.volume == pytest.approx(cell.volume / 2)
    assert all(atom.occupancy == .5 for atom in primitive.atoms)


def test_preview_keeps_double_bond_when_ghost_atom_was_removed():
    Chem = pytest.importorskip("rdkit.Chem")
    molecule = Chem.MolFromSmiles("*.C=C")
    molecule.AddConformer(Chem.Conformer(3))
    cell = cm.molecule_to_cell(molecule)
    shown = cp.build_molecule(cell, template=molecule)
    assert shown.GetNumAtoms() == 2
    assert shown.GetBondWithIdx(0).GetBondType() == Chem.BondType.DOUBLE
    assert molecule.GetNumAtoms() == 3


def test_preview_rejects_same_count_template_with_different_elements():
    Chem = pytest.importorskip("rdkit.Chem")
    molecule = Chem.MolFromSmiles("C=C")
    molecule.AddConformer(Chem.Conformer(2))
    cell = cm.cell_from_molecule(["O", "O"], [[0, 0, 0], [1, 0, 0]])
    shown = cp.build_molecule(cell, template=molecule)
    assert [atom.GetSymbol() for atom in shown.GetAtoms()] == ["O", "O"]


def test_preview_updates_every_conformer():
    Chem = pytest.importorskip("rdkit.Chem")
    molecule = Chem.MolFromSmiles("C=C")
    for _ in range(2):
        molecule.AddConformer(Chem.Conformer(2), assignId=True)
    cell = cm.molecule_to_cell(molecule)
    shown = cp.build_molecule(cell, template=molecule)
    for conformer in shown.GetConformers():
        assert list(conformer.GetAtomPosition(0)) == pytest.approx(cell.atoms[0].cart)


def test_translation_requires_a_bijection():
    lattice = np.eye(3) * 4
    atoms = tuple(cm.CellAtom(str(i), "C", np.array(f), np.array(f) @ lattice)
                  for i, f in enumerate(([0, 0, 0], [.5, 0, 0], [.5, 0, 0])))
    cell = cm.Cell("unequal", (4.,) * 3, (90.,) * 3, lattice, atoms)
    assert cm.translation_symmetries(cell) == []
    assert cm.primitive_cell(cell) is cell


@pytest.mark.parametrize("repeats", [[0, 1, 1], [1.5, 1, 1], [1, 1], [np.inf, 1, 1], [1000, 1000, 1]])
def test_invalid_or_excessive_supercell_repeats_are_rejected(repeats):
    cell = cm.cell_from_molecule(["H"], [[0, 0, 0]])
    with pytest.raises(ValueError):
        cm.make_supercell(cell, repeats)


@pytest.mark.parametrize("lengths,angles", [([np.nan, 1, 1], [90, 90, 90]),
                                          ([1, 1, 1], [90, np.inf, 90]),
                                          ([1, 1, 1], [-90, 90, 90]),
                                          ([1, 1, 1], [90, 180, 90])])
def test_invalid_cell_parameters_are_rejected(lengths, angles):
    with pytest.raises(ValueError):
        cm.cell_vectors(lengths, angles)


@pytest.mark.parametrize("kwargs", [{"coords": [[np.nan, 0, 0]]}, {"padding": np.inf},
                                    {"labels": []}, {"source_indices": []}])
def test_invalid_molecule_box_data_is_rejected(kwargs):
    args = {"elements": ["H"], "coords": [[0, 0, 0]]}
    args.update(kwargs)
    with pytest.raises(ValueError):
        cm.cell_from_molecule(**args)
