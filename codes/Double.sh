#!/bin/bash

# 输出文件名
output_file="excitation_double.txt"

# 清空输出文件并写表头
: > "$output_file"
echo -e "File\tS1_R2\tT1_R2" > "$output_file"

# 遍历当前目录及子目录的所有 .out 文件
find . -type f -name "*.out" | while read -r out_file; do
    if [ -f "$out_file" ]; then
        # 用 awk 提取第 1 个和第 2 个 Excitation energy 对应的 R2^2
        awk -v fname="$out_file" '
            /Excitation energy/ {
                exc_count++
                if (exc_count <= 2) seek=1
                next
            }
            seek && /R2\^2/ {
                if (match($0, /R2\^2[[:space:]]*=[[:space:]]*([0-9.+\-Ee]+)/, m)) {
                    if (exc_count == 1) s1 = m[1]
                    else if (exc_count == 2) t1 = m[1]
                }
                seek=0
            }
            END {
                if (s1 == "") s1 = "NA"
                if (t1 == "") t1 = "NA"
                printf "%s\t%s\t%s\n", fname, s1, t1
            }
        ' "$out_file" >> "$output_file"
    fi
done

# 输出结果
cat "$output_file"
