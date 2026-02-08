import os
from rdkit import Chem

# Define the input directory and the output file path
input_directory = r"F:\ucas_science\Python_project\sub_1\28"
output_file_path = r"F:\ucas_science\Python_project\sub_1\28\output.txt"

# Open the output file
with open(output_file_path, "w", encoding="utf-8") as output_file:
    # Iterate through all files in the input directory
    for filename in os.listdir(input_directory):
        if filename.endswith(".mol"):
            file_path = os.path.join(input_directory, filename)

            # Read the .mol file and convert it to an RDKit molecule object
            mol = Chem.MolFromMolFile(file_path)

            if mol is not None:
                # Convert the molecule object to a SMILES string
                smiles = Chem.MolToSmiles(mol)

                # Write the filename and the corresponding SMILES string to the output file
                output_file.write(f"{filename}: {smiles}\n")
            else:
                print(f"Failed to parse molecule from file: {filename}")

print(f"All SMILES strings have been written to {output_file_path}")
