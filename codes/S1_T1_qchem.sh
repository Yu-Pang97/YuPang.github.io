#!/bin/bash

# 输出文件名
output_file="excitation_energies.txt"

# 清空输出文件
> "$output_file"

# 添加表头
echo -e "File\tS1\tT1\tS1-T1" > "$output_file"

# 遍历当前目录下的所有 .out 文件
for out_file in *.out; do
    if [ -f "$out_file" ]; then
        # 提取S1
        s1=$(grep -m 1 "Excitation energy" "$out_file" | awk '{print $(NF-1)}')
        
        # 提取T1
        t1=$(grep -m 2 "Excitation energy" "$out_file" | tail -1 | awk '{print $(NF-1)}')
        
        # 计算S1 - T1
        s1_minus_t1=$(echo "$s1 - $t1" | bc)
        
        # 将结果写入输出文件
        echo -e "${out_file}\t${s1}\t${t1}\t${s1_minus_t1}" >> "$output_file"
    fi
done

# 输出结果到终端
cat "$output_file"