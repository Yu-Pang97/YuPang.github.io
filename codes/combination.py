import rdkit as rd
from rdkit import Chem
from rdkit.Chem import AllChem
import pandas as pd
import os


def read_excel_string(file_path, sheet_name=0, usecols=None):
    """Read an Excel sheet and return a DataFrame."""
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, usecols=usecols)
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None


def combine_molecules(Amol, Bmol, A_symbol="K", B_symbol="Fe"):
    """
    Combine two molecules by connecting the neighbor of A_symbol in Amol
    to the neighbor of B_symbol in Bmol, then remove the A_symbol and B_symbol atoms.
    """
    # Find the atom indices for the specified symbols
    A_ID = get_id_bysymbol(Amol, A_symbol)
    if A_ID is None:
        raise ValueError(f"No atom with symbol '{A_symbol}' found in molecule A.")

    B_ID = get_id_bysymbol(Bmol, B_symbol)
    if B_ID is None:
        raise ValueError(f"No atom with symbol '{B_symbol}' found in molecule B.")

    # Find the first neighbor indices of those atoms
    A_NEI_ID = get_neiid_bysymbol(Amol, A_symbol, A_ID)
    B_NEI_ID = get_neiid_bysymbol(Bmol, B_symbol, B_ID)

    if A_NEI_ID is None or B_NEI_ID is None:
        raise ValueError("Failed to find neighbor atoms for molecule combination.")

    # Combine molecules and add a bond between neighbor atoms
    combo = Chem.CombineMols(Amol, Bmol)
    edcombo = Chem.EditableMol(combo)
    edcombo.AddBond(
        A_NEI_ID,
        B_NEI_ID + Amol.GetNumAtoms(),
        order=Chem.rdchem.BondType.SINGLE,
    )

    # Remove the placeholder atoms (note: indices shift after removals)
    edcombo.RemoveAtom(A_ID)
    edcombo.RemoveAtom(B_ID + Amol.GetNumAtoms() - 1)

    combined_mol = edcombo.GetMol()
    Chem.SanitizeMol(combined_mol)  # Update implicit H counts and properties
    return combined_mol


def get_neiid_bysymbol(mol, symbol, idx=None):
    """Return the index of the first neighbor of an atom with the given symbol (optionally by atom index)."""
    for at in mol.GetAtoms():
        if at.GetSymbol() == symbol and (idx is None or at.GetIdx() == idx):
            neighbors = at.GetNeighbors()
            if neighbors:
                return neighbors[0].GetIdx()
    return None


def get_id_bysymbol(mol, symbol):
    """Return the index of the first atom with the given symbol."""
    for idx, at in enumerate(mol.GetAtoms()):
        if at.GetSymbol() == symbol:
            return idx
    return None


def prepare_for_output(mol):
    """Prepare molecule for output: add Hs, generate a 3D conformer, and optimize with MMFF."""
    mol_with_Hs = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol_with_Hs)
    AllChem.MMFFOptimizeMolecule(mol_with_Hs)
    return mol_with_Hs


if __name__ == "__main__":
    # Fixed donor molecule SMILES
    donor_smiles = "[K]C1=CC=C([K])C=C1C2=NC(C3=CC=CC=C3)=NC(C4=CC=CC=C4)=N2"
    Amol = Chem.MolFromSmiles(donor_smiles)

    # Read acceptor SMILES strings from Excel
    excel_file = r"F:\TSSF\1.xlsx"
    smi_acceptor_df = read_excel_string(excel_file, "Sheet1", ["smi"])
    if smi_acceptor_df is None or "smi" not in smi_acceptor_df.columns:
        print("Failed to load acceptor molecules from the Excel file.")
        raise SystemExit(1)

    acceptor_smiles_list = smi_acceptor_df["smi"].tolist()

    output_directory = r"F:\TSSF\A"
    os.makedirs(output_directory, exist_ok=True)

    first_combinations = []

    # First combination: donor + each acceptor (connect K site with Fe site)
    for i, Bmol_smiles in enumerate(acceptor_smiles_list, start=1):
        Bmol = Chem.MolFromSmiles(Bmol_smiles)
        if Bmol is None:
            print(f"Cannot parse SMILES: {Bmol_smiles}")
            continue

        try:
            combined_mol = combine_molecules(Amol, Bmol, "K", "Fe")
            first_combinations.append(combined_mol)
        except Exception as e:
            print(f"First combination failed (acceptor index {i}): {e}")

    # Second combination: for each first product, combine again with each acceptor
    for i, combined_mol in enumerate(first_combinations, start=1):
        for j, other_Bmol_smiles in enumerate(acceptor_smiles_list, start=1):
            other_Bmol = Chem.MolFromSmiles(other_Bmol_smiles)
            if other_Bmol is None:
                print(f"Cannot parse SMILES: {other_Bmol_smiles}")
                continue

            try:
                second_combined_mol = combine_molecules(combined_mol, other_Bmol, "K", "Fe")
                prepared_mol = prepare_for_output(second_combined_mol)
                output_filename = os.path.join(output_directory, f"A_2b_{i}_{j}.mol")
                Chem.MolToMolFile(prepared_mol, output_filename)
                print(f"Second combination saved: {output_filename}")
            except Exception as e:
                print(f"Second combination failed (first index {i}, acceptor index {j}): {e}")
