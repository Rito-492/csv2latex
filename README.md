# $csv2latex$

一个简单的 $.csv$ 转 $LaTeX$ 表格工具，自动加粗 **最小值** 并为次小值加下划线。

(第一次写论文，填数据的时候只会傻傻的肉眼看最值然后手动加粗。实在是太麻烦了，然后~~奴役~~ $Claude$ 写了这个小脚本。)

## 安装

```bash
pip install -e .
```

## 用法

```bash
# 基本用法
csv2latex data.csv output.tex

# 输出到 stdout
csv2latex data.csv

# 只输出 tabular 环境（嵌入现有文档）
csv2latex data.csv --snippet

# 保留 3 位小数
csv2latex data.csv --precision 3

# 高亮最大值
csv2latex data.csv output.tex --mode max

# 使用 booktabs 样式
csv2latex data.csv output.tex --booktabs

# 指定列和高亮模式
csv2latex data.csv output.tex --columns "Accuracy,Speed" --mode min-only
```

## 命令行选项

| 选项 | 说明 |
| :--- | :--- |
| `input` | 输入 CSV 文件路径 |
| `output` | 输出 LaTeX 文件路径（可选，不指定则输出到 stdout） |
| `--caption` | 表格标题（默认：table of data） |
| `--label` | 表格标签（默认：tab:data） |
| `--alignment` | 列对齐：l/c/r（默认：c） |
| `--mode` | 高亮模式：min/min-only/max/max-only/plain（默认：min） |
| `--columns` | 需要高亮的列名，逗号分隔 |
| `--booktabs` | 使用 booktabs 样式 |
| `--snippet` | 只输出 tabular 环境 |
| `--precision` | 数值精度（小数位数） |
| `--quiet` | 静默模式 |

## 输出示例

输入 CSV：

```csv
Method,Accuracy,Speed
A,92.456,120
B,95.123,115
C,93.789,125
```

输出 LaTeX（默认模式）：

```latex
\begin{table}[h]
\centering
\begin{tabular}{|c|c|c|}
\hline
Method & Accuracy & Speed \\
\hline
A & \underline{92.456} & \underline{120} \\
B & 95.123 & \textbf{115} \\
C & 93.789 & 125 \\
\hline
\end{tabular}
\caption{table of data}
\label{tab:data}
\end{table}
```
