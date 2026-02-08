#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# The python code is from Pang Yu in UCAS  https://yu-pang97.github.io/YuPang.github.io/#code

import subprocess
import sys
from pathlib import Path
import csv
import re

# Paths
MULTIWFN_EXE = r"E:\multiwfn\install\Multiwfn_3.8_dev_bin_Win64\Multiwfn.exe"
FCHK_DIR = r"F:\TUM\ML_IST\data\descriptor\fchk"
OUT_CSV = r"homo_lumo_Multiwfn.csv"

MULTIWFN_DIR = str(Path(MULTIWFN_EXE).parent)

if sys.platform.startswith("win"):
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0

LUMO_RE = re.compile(r"Orbital\s+(\d+)\s+is\s+LUMO", re.IGNORECASE)

NUM = r"[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?"
ORB_LINE_RE = re.compile(
    rf"^\s*Orb:\s*(\d+)\s+Ene\(au/eV\):\s*({NUM})\s+({NUM})",
    re.MULTILINE
)


def run_multiwfn_on_fchk(fchk_path: Path) -> str:
    """
    Run Multiwfn on a single .fchk file using functions 0 -> 6 -> 3,
    and return the full stdout text.
    Extra newlines are included to avoid manual ENTER presses.
    """
    # Interactive script:
    # 0\n  -> choose function 0
    # \n   -> press ENTER to return to main menu
    # 6\n  -> choose function 6
    # 3\n  -> choose sub-function 3
    # \n   -> press ENTER if it asks "press ENTER to continue"
    # 0\n  -> return to main menu (safe)
    # q\n  -> quit Multiwfn from main menu
    script = "0\n\n6\n3\n\n0\nq\n"

    print(f"[RUN ] Multiwfn processing: {fchk_path.name}")
    proc = subprocess.run(
        [MULTIWFN_EXE, str(fchk_path)],
        input=script,
        text=True,
        encoding="gbk",   # If garbled text appears, try "gb18030" or "utf-8"
        errors="ignore",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=MULTIWFN_DIR,               # Key: run inside Multiwfn folder to use isilent=1 settings
        creationflags=CREATE_NO_WINDOW, # Key: do not pop up a console window on Windows
    )
    return proc.stdout


def extract_lumo_index(text: str):
    """
    Find the first occurrence of the LUMO orbital index in Multiwfn output.
    Returns int or None.
    """
    m = LUMO_RE.search(text)
    if not m:
        return None
    return int(m.group(1))


def extract_orbital_energies(text: str):
    """
    Parse all lines like:
      "Orb: n Ene(au/eV): E_au E_eV ..."
    Returns a dict: {orb_index: (E_au, E_eV)}.
    """
    energies = {}
    for m in ORB_LINE_RE.finditer(text):
        idx = int(m.group(1))
        e_au = float(m.group(2))
        e_ev = float(m.group(3))
        energies[idx] = (e_au, e_ev)
    return energies


def main():
    root = Path(FCHK_DIR)
    if not root.is_dir():
        print(f"[FATAL] .fchk directory not found: {root}")
        return

    fchk_files = sorted(root.glob("*.fchk"))
    if not fchk_files:
        print(f"[WARN] No .fchk files found in: {root}")
        return

    out_rows = []
    ok = 0

    for fchk in fchk_files:
        try:
            out_text = run_multiwfn_on_fchk(fchk)

            # 1) Locate LUMO orbital index
            lumo_idx = extract_lumo_index(out_text)
            if lumo_idx is None:
                print(f"[WARN] {fchk.name}: LUMO line not found")
                out_rows.append([fchk.name, "", "", "", "", "", "", "", "", "", "", "", "", ""])
                continue

            # 2) Parse all orbital energies
            orb_energies = extract_orbital_energies(out_text)
            if not orb_energies:
                print(f"[WARN] {fchk.name}: No orbital energy lines parsed")
                out_rows.append([fchk.name, lumo_idx, "", "", "", "", "", "", "", "", "", "", "", ""])
                continue

            # Target orbital indices
            idx_HOMO   = lumo_idx - 1
            idx_HOMO_1 = lumo_idx - 2
            idx_HOMO_2 = lumo_idx - 3
            idx_LUMO   = lumo_idx
            idx_LUMO_1 = lumo_idx + 1
            idx_LUMO_2 = lumo_idx + 2

            def get_energy(idx):
                """Return (E_au, E_eV) or ("", "")."""
                if idx in orb_energies:
                    e_au, e_ev = orb_energies[idx]
                    return e_au, e_ev
                return "", ""

            HOMO2_au, HOMO2_ev = get_energy(idx_HOMO_2)
            HOMO1_au, HOMO1_ev = get_energy(idx_HOMO_1)
            HOMO_au,  HOMO_ev  = get_energy(idx_HOMO)
            LUMO_au,  LUMO_ev  = get_energy(idx_LUMO)
            LUMO1_au, LUMO1_ev = get_energy(idx_LUMO_1)
            LUMO2_au, LUMO2_ev = get_energy(idx_LUMO_2)

            out_rows.append([
                fchk.name,
                lumo_idx,
                HOMO2_au, HOMO2_ev,
                HOMO1_au, HOMO1_ev,
                HOMO_au,  HOMO_ev,
                LUMO_au,  LUMO_ev,
                LUMO1_au, LUMO1_ev,
                LUMO2_au, LUMO2_ev,
            ])

            ok += 1
            print(f"[OK  ] {fchk.name}: LUMO={lumo_idx}, energies parsed successfully")

        except Exception as e:
            print(f"[ERROR] Failed to process {fchk.name}: {e}")
            out_rows.append([fchk.name, "", "", "", "", "", "", "", "", "", "", "", "", ""])

    # Write CSV
    out_path = root / OUT_CSV
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "file",
            "LUMO_index",
            "HOMO-2_au", "HOMO-2_eV",
            "HOMO-1_au", "HOMO-1_eV",
            "HOMO_au",  "HOMO_eV",
            "LUMO_au",  "LUMO_eV",
            "LUMO+1_au", "LUMO+1_eV",
            "LUMO+2_au", "LUMO+2_eV",
        ])
        w.writerows(out_rows)

    print(f"\n[SUMMARY] Processed {len(fchk_files)} .fchk files, successfully parsed {ok}")
    print(f"[SAVE] Results written to: {out_path}")


if __name__ == "__main__":
    main()
