#!/bin/bash

# Define the file pattern to process and the output file
file_type="*.out"
output_file="output.txt"

# Clear or create the output file, and write the header
echo -e "File Name\tData" > "$output_file"

# Loop through matching files
for file in $file_type; do
    echo "Processing $file..."

    # Use awk to find the last line containing the target string,
    # then extract the second-to-last column (NF-1)
    last_match=$(awk '
        /Sum of individual times/ {
            last_match = $(NF-1)
        }
        END {
            if (last_match != "") print last_match
        }' "$file")

    # If a match was found, write filename and extracted value to the output file
    if [ -n "$last_match" ]; then
        echo -e "$file\t$last_match" >> "$output_file"
    fi
done

echo "Data has been written to $output_file"
