import os
import subprocess

#Copyright (c) 2025 University of Chinese Academy of Sciences
#The file is from Yu Pang from Qian Peng group

# definition of path
multiwfn_path = r'B:\Multiwfn_3.8_dev_bin_Win64\Multiwfn.exe' # the pathway of  multiwfn
input_dir = r'F:\ucas_science\Python_project\test' #the pathway in your file
output_file = 'Orb_Val_Sum.txt'

# Create the output file and write to the table header
with open(output_file, 'w') as f:
    f.write('mol_No., H_val, L_val, K_HL (eV), O_D (eV), IST Candidate\n')

# reading the .fchk document
for inf in [f for f in os.listdir(input_dir) if f.endswith('.fchk')]:
    print(f"The file being processed is {inf}")

    # using Multiwfn, save as tmp.mf
    tmp_file = os.path.join(input_dir, inf.replace('.fchk', '.tmp'))
    with open(tmp_file, 'w') as tmp_out:
        proc = subprocess.run(
            [multiwfn_path, os.path.join(input_dir, inf), '-silent'],
            input="0\nq\n",
            stdout=tmp_out,
            stderr=subprocess.PIPE,
            text=True
        )

    # Fetch rows with the is HOMO and is LUMO fields and extract the data
    h = None
    l = None
    with open(tmp_file, 'r') as tmp_in:
        content = tmp_in.read()
        for line in content.splitlines():
            if "is HOMO" in line:
                h = line.split()[2]
            elif "is LUMO" in line:
                l = line.split()[1]

    if h and l:
        with open(output_file, 'a') as f:
            f.write(f"{inf.replace('.fchk', ', ')}, {h}, {l}, ")

        #  tmp2.mf
        tmp2_mf = os.path.join(input_dir, 'tmp2.mf')
        with open(tmp2_mf, 'w') as mf:
            mf.write("200\n")
            mf.write("17\n")
            mf.write(f"{h},{l}\n")
            mf.write("1\n")
            mf.write("3\n")
            mf.write("q\n")

        # using Multiwfn, save as out.txt
        out_txt = os.path.join(input_dir, 'out.txt')
        with open(out_txt, 'w') as out:
            subprocess.run(
                [multiwfn_path, os.path.join(input_dir, inf)],
                stdin=open(tmp2_mf),
                stdout=out,
                stderr=subprocess.PIPE,
                text=True
            )

        # Extract the Exchange integral (ij|ji) value and transform it
        gapthis_au = None
        with open(out_txt, 'r') as out_in:
            content = out_in.read()
            for line in content.splitlines():
                if "Exchange integral (ij|ji)" in line:
                    gapthis_au = line.split()[3]
                    break

        if gapthis_au:
            try:
                # Convert K_S_au to eV
                K_S_eV = float(gapthis_au) * 27.2114
                print(f"K_HL={K_S_eV:.4f} eV")

                # Create a new temporary file tmp3.mf for further calculations
                tmp3_mf = os.path.join(input_dir, 'tmp3.mf')
                with open(tmp3_mf, 'w') as mf:
                    mf.write("6\n")  # function 6
                    mf.write("3\n")  # function 3
                    mf.write("q\n")  # end

                # Use Multiwfn for further calculations and save the results to out2.txt
                out2_txt = os.path.join(input_dir, 'out2.txt')
                with open(out2_txt, 'w') as out:
                    subprocess.run(
                        [multiwfn_path, os.path.join(input_dir, inf)],
                        stdin=open(tmp3_mf),
                        stdout=out,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                # Grab the row containing h and l numbers and extract the value of the fifth column
                HOMO = None
                HOMO_minus_1 = None
                LUMO = None
                LUMO_plus_1 = None

                with open(out2_txt, 'r') as out_in:
                    content = out_in.read()
                    for line in content.splitlines():
                        if 'Ene(au/eV)' in line:
                            columns = line.split()
                            try:
                                orbital_num = int(columns[1])
                                energy = float(columns[4])
                                if orbital_num == int(h):
                                    HOMO = energy
                                elif orbital_num == int(h) - 1:
                                    HOMO_minus_1 = energy
                                elif orbital_num == int(l):
                                    LUMO = energy
                                elif orbital_num == int(l) + 1:
                                    LUMO_plus_1 = energy
                            except (ValueError, IndexError):
                                continue

                # calculating O_D
                if all([HOMO, HOMO_minus_1, LUMO, LUMO_plus_1]):
                    O_D_eV = (LUMO - LUMO_plus_1) + (HOMO_minus_1 - HOMO)
                    O_D_eV = round(O_D_eV, 3)
                    print(f"O_D: {O_D_eV:.3f} eV")

                    with open(output_file, 'a') as f:
                        f.write(f"{K_S_eV:.4f}, {O_D_eV:.4f}, ")

                        # Determine the condition and output the result
                        if K_S_eV <= 0.4 and O_D_eV <= -0.3:
                            f.write("IST Candidate\n")
                            print("IST Candidate")
                        else:
                            f.write("No IST Candidate\n")
                            print("No IST Candidate")
                else:
                    print("Failed to find all required orbital energy values")
                    with open(output_file, 'a') as f:
                        f.write("N/A, N/A, No IST Candidate\n")

            except ValueError:
                print(f"{gapthis_au} Failed to convert to floating point。")
                with open(output_file, 'a') as f:
                    f.write("N/A, N/A, No IST Candidate\n")

    # Delete temporary files
    for temp_file in [tmp_file, tmp2_mf, tmp3_mf, out_txt, out2_txt]:
        if os.path.exists(temp_file):
            os.remove(temp_file)

print("Processing completed.")