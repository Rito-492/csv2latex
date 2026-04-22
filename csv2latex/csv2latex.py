import os
import argparse
import sys
import pandas as pd
from typing import Dict, List, Tuple, Optional

__version__ = "0.2.0"


def escape_latex(text: str) -> str:
    """转义 LaTeX 特殊字符"""
    special_chars = {
        '\\': r'\textbackslash ',
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^',
    }
    result = str(text)
    for char, escaped in special_chars.items():
        result = result.replace(char, escaped)
    return result


def find_extreme_values(series: pd.Series,
                       mode: str = 'min',
                       tolerance: float = 1e-9) -> Tuple[List[int], List[int]]:
    """找出数值序列中的极值和次极值的索引"""
    if mode == 'plain':
        return [], []

    try:
        numeric_series = pd.to_numeric(series, errors='coerce')
        valid_mask = ~numeric_series.isna()
        valid_indices = valid_mask[valid_mask].index.tolist()

        if len(valid_indices) == 0:
            return [], []

        unique_values = sorted(numeric_series[valid_indices].unique(),
                              reverse=(mode == 'max' or mode == 'max-only'))

        if len(unique_values) == 0:
            return [], []

        extreme_val = unique_values[0]
        extreme_indices = numeric_series[
            (numeric_series >= extreme_val - tolerance) &
            (numeric_series <= extreme_val + tolerance)
        ].index.tolist()

        if mode in ['min-only', 'max-only']:
            return extreme_indices, []

        second_extreme_indices = []
        if len(unique_values) >= 2:
            second_extreme_val = unique_values[1]
            second_extreme_indices = numeric_series[
                (numeric_series >= second_extreme_val - tolerance) &
                (numeric_series <= second_extreme_val + tolerance)
            ].index.tolist()

        return extreme_indices, second_extreme_indices

    except Exception as e:
        print(f"Warning: there was an error finding extreme values: - {e}")
        return [], []


def analyze_dataframe(df: pd.DataFrame,
                     mode: str = 'min',
                     columns: Optional[List[str]] = None) -> Dict[int, Dict[int, str]]:
    """分析 DataFrame，找出每列需要格式化的单元格"""
    col_format = {}

    for col_idx, col in enumerate(df.columns):
        if columns is not None and col not in columns:
            continue

        col_format[col_idx] = {}
        extreme_indices, second_extreme_indices = find_extreme_values(df[col], mode)

        for idx in extreme_indices:
            col_format[col_idx][idx] = 'bold'

        for idx in second_extreme_indices:
            if idx not in extreme_indices:
                col_format[col_idx][idx] = 'underline'

    return col_format


def format_cell(value, format_type: Optional[str] = None, escape: bool = True,
                precision: Optional[int] = None) -> str:
    """格式化单个单元格"""
    text = str(value)
    if precision is not None:
        try:
            num_val = float(value)
            text = f"{num_val:.{precision}f}"
        except (ValueError, TypeError):
            text = str(value)

    if escape:
        text = escape_latex(text)

    if format_type == 'bold':
        return f"\\textbf{{{text}}}"
    elif format_type == 'underline':
        return f"\\underline{{{text}}}"
    else:
        return text


def generate_latex_table(df: pd.DataFrame,
                         col_format: Dict[int, Dict[int, str]],
                         caption: str = "table of data",
                         label: str = "tab:data",
                         alignment: str = "c",
                         use_booktabs: bool = False,
                         snippet: bool = False,
                         precision: Optional[int] = None) -> str:
    """生成 LaTeX 表格代码"""
    columns = df.columns.tolist()
    num_cols = len(columns)

    latex_lines = []

    if not snippet:
        latex_lines.append("\\documentclass{article}")
        if use_booktabs:
            latex_lines.append("\\usepackage{booktabs}")
        latex_lines.append("\\begin{document}\n")
        latex_lines.append("\\begin{table}[h]\n")
        latex_lines.append("\\centering")

    if use_booktabs:
        latex_lines.append(f"\t\\begin{{tabular}}{{{alignment * num_cols}}}")
        latex_lines.append("\t\t\\toprule")
    else:
        latex_lines.append(f"\t\\begin{{tabular}}{{|{alignment}|" + f"{alignment}|" * (num_cols - 1) + "}")
        latex_lines.append("\t\t\\hline")

    header = '\t\t' + " & ".join(escape_latex(col) for col in columns) + " \\\\"
    latex_lines.append(header)

    if use_booktabs:
        latex_lines.append("\t\t\\midrule")
    else:
        latex_lines.append("\t\t\\hline")

    for row_idx, row in df.iterrows():
        row_data = []
        for col_idx, col in enumerate(columns):
            value = row[col]
            format_type = col_format.get(col_idx, {}).get(row_idx)
            formatted_value = format_cell(value, format_type, precision=precision)
            row_data.append(formatted_value)

        latex_lines.append('\t\t' + " & ".join(row_data) + " \\\\")
        if not use_booktabs:
            latex_lines.append("\t\t\\hline")

    if use_booktabs:
        latex_lines.append("\t\t\\bottomrule")

    latex_lines.append("\t\\end{tabular}")

    if not snippet:
        latex_lines.append(f"\\caption{{{escape_latex(caption)}}}")
        latex_lines.append(f"\\label{{{label}}}")
        latex_lines.append("\\end{table}\n")
        latex_lines.append("\\end{document}")

    return "\n".join(latex_lines)


def csv_to_latex(csv_file: str,
                 tex_file: Optional[str] = None,
                 caption: str = "table of data",
                 label: str = "tab:data",
                 alignment: str = "c",
                 mode: str = "min",
                 columns: Optional[List[str]] = None,
                 use_booktabs: bool = False,
                 verbose: bool = True,
                 snippet: bool = False,
                 precision: Optional[int] = None) -> Optional[str]:
    """读取 CSV 文件并生成 LaTeX 表格"""
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")

    if df.empty:
        raise ValueError("CSV file is empty")

    if columns is not None:
        invalid_cols = [col for col in columns if col not in df.columns]
        if invalid_cols:
            raise ValueError(f"Invalid columns: {invalid_cols}")

    if verbose:
        print(f"✓ Successfully read the CSV file: {csv_file}", file=sys.stderr)
        print(f"✓ Data dimensions: {df.shape[0]} rows × {df.shape[1]} columns", file=sys.stderr)
        print(f"✓ Highlighting mode: {mode}", file=sys.stderr)
        if columns:
            print(f"✓ Processing columns: {columns}", file=sys.stderr)

    col_format = analyze_dataframe(df, mode, columns)
    latex_content = generate_latex_table(df, col_format, caption, label, alignment,
                                         use_booktabs, snippet=snippet, precision=precision)

    if tex_file:
        try:
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            if verbose:
                print(f"✓ LaTeX file has been generated: {tex_file}", file=sys.stderr)
                if use_booktabs:
                    print("  Note: Using booktabs style. Add \\usepackage{booktabs} in your LaTeX preamble if not already included.", file=sys.stderr)
        except Exception as e:
            raise IOError(f"Failed to write LaTeX file: {e}")
    else:
        print(latex_content)
        return latex_content

    if verbose and tex_file:
        print("\nFormatting Information:", file=sys.stderr)
        has_formatting = False
        for col_idx, col in enumerate(df.columns):
            if col_idx in col_format and col_format[col_idx]:
                has_formatting = True
                print(f"\n  Col '{col}':", file=sys.stderr)
                for row_idx, format_type in sorted(col_format[col_idx].items()):
                    value = df.iloc[row_idx, col_idx]
                    symbol = "●" if format_type == "bold" else "○"
                    print(f"    {symbol} Row{row_idx}: {value} -> {format_type}", file=sys.stderr)

        if not has_formatting:
            print("  (There is no data column that needs formatting.)", file=sys.stderr)

    return None


def main():
    parser = argparse.ArgumentParser(
        description='将 CSV 文件转换为 LaTeX 表格，自动高亮极值',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s data.csv output.tex
  %(prog)s data.csv output.tex --mode max --caption "experiment result"
  %(prog)s data.csv output.tex --columns "accuracy,velocity" --booktabs
  %(prog)s data.csv                    # 输出到 stdout
  %(prog)s data.csv --snippet          # 只输出 tabular 环境
  %(prog)s data.csv --precision 3      # 保留 3 位小数
        """
    )

    parser.add_argument('input', help='输入 CSV 文件路径')
    parser.add_argument('output', nargs='?', default=None, help='输出 LaTeX 文件路径 (可选，不指定则输出到 stdout)')
    parser.add_argument('--caption', default='table of data', help='表格标题 (默认：table of data)')
    parser.add_argument('--label', default='tab:data', help='表格标签 (默认：tab:data)')
    parser.add_argument('--alignment', choices=['l', 'c', 'r'], default='c',
                       help='列对齐方式：l=左对齐，c=居中，r=右对齐 (默认：c)')
    parser.add_argument('--mode', choices=['min', 'min-only', 'max', 'max-only', 'plain'], default='min',
                       help='高亮模式：min=最小值加粗次小值下划线，min-only=仅最小值加粗，max=最大值加粗次大值下划线，max-only=仅最大值加粗，plain=无高亮 (默认：min)')
    parser.add_argument('--columns', help='需要高亮的列名，用逗号分隔 (默认：所有列)')
    parser.add_argument('--booktabs', action='store_true', help='使用 booktabs 样式')
    parser.add_argument('--snippet', action='store_true', help='只输出 tabular 环境，不包含 document 和 table 包装')
    parser.add_argument('--precision', type=int, default=None, help='数值精度（小数位数），不指定则保持原样')
    parser.add_argument('--quiet', action='store_true', help='静默模式，不输出详细信息')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    args = parser.parse_args()

    columns = None
    if args.columns:
        columns = [col.strip() for col in args.columns.split(',')]

    try:
        csv_to_latex(
            csv_file=args.input,
            tex_file=args.output,
            caption=args.caption,
            label=args.label,
            alignment=args.alignment,
            mode=args.mode,
            columns=columns,
            use_booktabs=args.booktabs,
            verbose=not args.quiet,
            snippet=args.snippet,
            precision=args.precision
        )
        return 0
    except Exception as e:
        print(f"Error: - {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit(main())
