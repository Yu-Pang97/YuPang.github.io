#!/bin/bash

# Folders for categorized log files (relative to current directory)
IM_FREQ_DIR="./im_freq"
NO_SCF_DIR="./no_SCF"

# Create folders if they don't exist
mkdir -p "$IM_FREQ_DIR" "$NO_SCF_DIR"

echo "[INFO] Working directory: $(pwd)"
echo "[INFO] Imaginary-frequency logs -> $IM_FREQ_DIR"
echo "[INFO] Abnormal-termination logs -> $NO_SCF_DIR"
echo

# Process all .log files in the current directory (no recursion)
find . -maxdepth 1 -type f -name "*.log" | while read -r log_file; do
  # Remove leading ./ for nicer printing
  file_name=$(basename "$log_file")

  # 1) Check whether the job terminated normally (Gaussian)
  if ! tail -n 1 "$log_file" | grep -q "Normal termination"; then
    mv "$log_file" "$NO_SCF_DIR/$file_name"
    echo "[MOVE] $file_name -> $NO_SCF_DIR (no Normal termination)"
    continue
  fi

  # 2) If normal, check for imaginary frequencies (case-insensitive)
  if grep -qi "imaginary frequencies" "$log_file"; then
    mv "$log_file" "$IM_FREQ_DIR/$file_name"
    echo "[MOVE] $file_name -> $IM_FREQ_DIR (imaginary frequencies found)"
    continue
  fi

  echo "[OK  ] $file_name"
done

echo
echo "[DONE] Finished processing .log files."
