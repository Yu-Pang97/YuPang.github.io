from rdkit import Chem
from rdkit.Chem import AllChem
import itertools
from pathlib import Path

# Input SMILES
smiles = "[Si]12=CC=C[Si]3=[Si]1B(C=CC3)C=CO2"

# Output folder
OUT_DIR = Path(r"F:/pythonProject1/BO_N")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# How many carbon atoms to replace by nitrogen
N_REPLACE_COUNT = 8

# Convert SMILES to RDKit molecule
mol = Chem.MolFromSmiles(smiles)
if mol is None:
    raise ValueError("Failed to build molecule from the given SMILES.")

# Collect atom indices
carbon_atoms = [a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() == 6]
silicon_atoms = [a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() == 14]

if len(carbon_atoms) < N_REPLACE_COUNT:
    raise ValueError(f"Not enough carbon atoms to replace: found {len(carbon_atoms)}, need {N_REPLACE_COUNT}.")

# Generate all combinations of N_REPLACE_COUNT carbon atoms
carbon_combinations = itertools.combinations(carbon_atoms, N_REPLACE_COUNT)

# Use a set to remove duplicate SMILES
unique_smiles = set()

for combo in carbon_combinations:
    new_mol = Chem.Mol(mol)

    # Replace selected C -> N
    for idx in combo:
        new_mol.GetAtomWithIdx(idx).SetAtomicNum(7)  # N = 7

    # Replace all Si -> C
    for idx in silicon_atoms:
        new_mol.GetAtomWithIdx(idx).SetAtomicNum(6)  # C = 6

    # Sanitize after atom type changes
    Chem.SanitizeMol(new_mol)

    # Canonical SMILES for de-duplication
    unique_smiles.add(Chem.MolToSmiles(new_mol, canonical=True))

# Generate 3D and save to MOL files
for i, smi in enumerate(sorted(unique_smiles), start=1):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        continue

    m = Chem.AddHs(m)

    # Generate 3D conformer
    status = AllChem.EmbedMolecule(m, useRandomCoords=True)
    if status != 0:
        continue

    # Optional optimization
    AllChem.MMFFOptimizeMolecule(m)

    out_file = OUT_DIR / f"BO_8N_{i}.mol"
    Chem.MolToMolFile(m, str(out_file))

print(f"Saved {len(unique_smiles)} unique .mol files to: {OUT_DIR}")
