#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path

CONVERGED_KEYWORDS = (
    "THE OPTIMIZATION HAS CONVERGED",
    "OPTIMIZATION CONVERGED",
)

COORD_HEADER = "CARTESIAN COORDINATES (ANGSTROEM)"


def _is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except Exception:
        return False


def parse_last_angstrom_block(lines, start_line=0):
    """
    Find the last 'CARTESIAN COORDINATES (ANGSTROEM)' block after start_line.
    Return list of tuples: [(elem, x, y, z), ...] or None.
    """
    blocks = []
    i = start_line
    n = len(lines)

    while i < n:
        if COORD_HEADER in lines[i]:
            # Move forward; ORCA typically has a dashed line after the header
            i += 1
            # Skip separator / empty lines
            while i < n and (lines[i].strip() == "" or set(lines[i].strip()) <= {"-"}):
                i += 1

            coords = []
            # Read until blank line or next section
            while i < n:
                line = lines[i].strip()
                if line == "":
                    break
                if COORD_HEADER in line:
                    # start of a new block
                    i -= 1
                    break

                parts = line.split()
                if len(parts) < 4:
                    break

                elem = parts[0]

                # Usually: Elem x y z
                # But be tolerant: if more columns exist, take the last 3 float-like tokens.
                float_tokens = [p for p in parts[1:] if _is_float(p)]
                if len(float_tokens) >= 3:
                    x, y, z = map(float, float_tokens[-3:])
                    coords.append((elem, x, y, z))
                else:
                    # Not a coordinate line -> end block
                    break

                i += 1

            if coords:
                blocks.append(coords)

        i += 1

    return blocks[-1] if blocks else None


def extract_optimized_geometry(out_path: Path):
    text = out_path.read_text(errors="ignore")
    lines = text.splitlines()

    # Prefer blocks after convergence message (if present)
    conv_pos = None
    for idx, line in enumerate(lines):
        u = line.upper()
        if any(k in u for k in CONVERGED_KEYWORDS):
            conv_pos = idx
            break

    if conv_pos is not None:
        coords = parse_last_angstrom_block(lines, start_line=conv_pos)
        if coords:
            return coords

    # Fallback: last Angstrom block in the whole file
    coords = parse_last_angstrom_block(lines, start_line=0)
    return coords


def write_xyz(coords, xyz_path: Path, comment: str = ""):
    xyz_path.parent.mkdir(parents=True, exist_ok=True)
    with xyz_path.open("w", encoding="utf-8") as f:
        f.write(f"{len(coords)}\n")
        f.write(comment.strip() + "\n")
        for elem, x, y, z in coords:
            f.write(f"{elem:2s}  {x: .8f}  {y: .8f}  {z: .8f}\n")


def iter_input_files(input_path: Path):
    if input_path.is_file():
        yield input_path
        return
    # directory: search common ORCA output extensions
    exts = (".out", ".log", ".orcaout", ".output")
    for p in sorted(input_path.rglob("*")):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def main():
    ap = argparse.ArgumentParser(
        description="Extract optimized geometry from ORCA optimization output and write XYZ."
    )
    ap.add_argument("input", help="ORCA output file (.out) or a directory containing output files.")
    ap.add_argument("-o", "--outdir", default=None, help="Output directory for xyz files (default: alongside input).")
    ap.add_argument("--suffix", default="_opt.xyz", help="Suffix for output xyz filename (default: _opt.xyz).")
    args = ap.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else None

    any_ok = False
    for out_file in iter_input_files(input_path):
        coords = extract_optimized_geometry(out_file)
        if not coords:
            print(f"[WARN] No Angstrom coordinate block found: {out_file}")
            continue

        if outdir:
            xyz_path = outdir / (out_file.stem + args.suffix)
        else:
            xyz_path = out_file.with_name(out_file.stem + args.suffix)

        comment = f"Extracted from {out_file.name}"
        write_xyz(coords, xyz_path, comment=comment)
        print(f"[OK] Wrote: {xyz_path}")
        any_ok = True

    if not any_ok:
        raise SystemExit("No XYZ files written. Please check your ORCA output files.")


if __name__ == "__main__":
    main()
