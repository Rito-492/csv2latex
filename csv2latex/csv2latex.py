"""
CSV to LaTeX Table Converter
将CSV文件转换为LaTeX表格，支持自动高亮最小值和次小值
"""

import pandas as pd
import os
import argparse
import json
from typing import Dict, List, Tuple, Optional

__version__ = "1.0.0"

# ==================== 工具函数 ====================

def escape_latex(text: str) -> str:
    """
    转义LaTeX特殊字符
    
    参数:
        text: 需要转义的文本
    返回:
        转义后的文本
    """
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
    """
    找出数值序列中的极值和次极值的索引
    
    参数:
        series: pandas Series对象
        mode: 'min' 或 'max'
        tolerance: 浮点数比较容差
    返回:
        (极值索引列表, 次极值索引列表)
    """
    if mode == 'plain':
        return [], []

    try:
        # 尝试转换为数值类型
        numeric_series = pd.to_numeric(series, errors='coerce')
        
        # 过滤NaN值
        valid_mask = ~numeric_series.isna()
        valid_indices = valid_mask[valid_mask].index.tolist()
        
        if len(valid_indices) == 0:
            return [], []
        
        # 获取唯一值并排序
        unique_values = sorted(numeric_series[valid_indices].unique(), 
                              reverse=(mode == 'max'))
        
        if len(unique_values) == 0:
            return [], []
        
        # 找极值索引
        extreme_val = unique_values[0]
        extreme_indices = numeric_series[
            (numeric_series >= extreme_val - tolerance) & 
            (numeric_series <= extreme_val + tolerance)
        ].index.tolist()
        
        # 找次极值索引
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
    """
    分析DataFrame，找出每列需要格式化的单元格
    
    参数:
        df: pandas DataFrame对象
        mode: 'min' 或 'max'，决定高亮最小值还是最大值
        columns: 需要处理的列名列表，None表示处理所有列
    返回:
        格式化字典 {列索引: {行索引: 格式类型}}
    """
    col_format = {}
    
    for col_idx, col in enumerate(df.columns):
        # 如果指定了列，只处理指定的列
        if columns is not None and col not in columns:
            continue
            
        col_format[col_idx] = {}
        
        extreme_indices, second_extreme_indices = find_extreme_values(df[col], mode)
        
        # 标记极值
        for idx in extreme_indices:
            col_format[col_idx][idx] = 'bold'
        
        # 标记次极值（确保不是极值）
        for idx in second_extreme_indices:
            if idx not in extreme_indices:
                col_format[col_idx][idx] = 'underline'
    
    return col_format


def format_cell(value, format_type: Optional[str] = None, escape: bool = True) -> str:
    """
    格式化单个单元格
    
    参数:
        value: 单元格值
        format_type: 格式类型 ('bold', 'underline', None)
        escape: 是否转义LaTeX特殊字符
    返回:
        格式化后的字符串
    """
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
                         use_booktabs: bool = False) -> str:
    """
    生成LaTeX表格代码
    
    参数:
        df: pandas DataFrame对象
        col_format: 格式化字典
        caption: 表格标题
        label: 表格标签
        alignment: 列对齐方式 ('l', 'c', 'r')
        use_booktabs: 是否使用booktabs样式
    返回:
        LaTeX代码字符串
    """
    columns = df.columns.tolist()
    num_cols = len(columns)
    
    latex_lines = []
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
    
    # 表头
    header = '\t\t' + " & ".join(escape_latex(col) for col in columns) + " \\\\"
    latex_lines.append(header)
    
    if use_booktabs:
        latex_lines.append("\t\t\\midrule")
    else:
        latex_lines.append("\t\t\\hline")
    
    # 数据行
    for row_idx, row in df.iterrows():
        row_data = []
        for col_idx, col in enumerate(columns):
            value = row[col]
            format_type = col_format.get(col_idx, {}).get(row_idx)
            formatted_value = format_cell(value, format_type)
            row_data.append(formatted_value)
        
        latex_lines.append('\t\t' + " & ".join(row_data) + " \\\\")
        if not use_booktabs:
            latex_lines.append("\t\t\\hline\n")
    
    if use_booktabs:
        latex_lines.append("\t\t\\bottomrule")
    
    latex_lines.append("\t\\end{tabular}")
    latex_lines.append(f"\\caption{{{escape_latex(caption)}}}")
    latex_lines.append(f"\\label{{{label}}}")
    latex_lines.append("\\end{table}\n")
    latex_lines.append("\\end{document}")
    
    return "\n".join(latex_lines)


def load_config(config_file: str) -> dict:
    """
    从JSON配置文件加载设置
    
    参数:
        config_file: 配置文件路径
    返回:
        配置字典
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configure file not found: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def csv_to_latex(csv_file: str, 
                 tex_file: str,
                 caption: str = "数据表格",
                 label: str = "tab:data",
                 alignment: str = "c",
                 mode: str = "min",
                 columns: Optional[List[str]] = None,
                 use_booktabs: bool = False,
                 verbose: bool = True) -> None:
    """
    读取CSV文件并生成LaTeX表格文件
    
    参数:
        csv_file: 输入的CSV文件路径
        tex_file: 输出的LaTeX文件路径
        caption: 表格标题
        label: 表格标签
        alignment: 列对齐方式 ('l'=左对齐, 'c'=居中, 'r'=右对齐)
        mode: 'min' 或 'max'，高亮最小值或最大值
        columns: 需要高亮的列名列表，None表示所有列
        use_booktabs: 是否使用booktabs样式
        verbose: 是否打印详细信息
    """
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV文件不存在: {csv_file}")
    
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        raise ValueError(f"读取CSV文件失败: {e}")
    
    if df.empty:
        raise ValueError("CSV文件为空")
    
    # 验证列名
    if columns is not None:
        invalid_cols = [col for col in columns if col not in df.columns]
        if invalid_cols:
            raise ValueError(f"指定的列不存在: {invalid_cols}")
    
    if verbose:
        print(f"✓ 成功读取CSV文件: {csv_file}")
        print(f"✓ 数据维度: {df.shape[0]} 行 × {df.shape[1]} 列")
        print(f"✓ 高亮模式: {mode}")
        if columns:
            print(f"✓ 处理列: {columns}")
    
    # 分析数据并获取格式化信息
    col_format = analyze_dataframe(df, mode, columns)
    
    # 生成LaTeX代码
    latex_content = generate_latex_table(df, col_format, caption, label, alignment, use_booktabs)
    
    # 写入文件
    try:
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        if verbose:
            print(f"✓ LaTeX文件已生成: {tex_file}")
            if use_booktabs:
                print("  Note: Using booktabs style. Add \\usepackage{booktabs} in your LaTeX preamble if not already included.")
    except Exception as e:
        raise IOError(f"写入LaTeX文件失败: {e}")
    
    # 打印格式化信息
    if verbose:
        print("\nFormatting Information:")
        has_formatting = False
        for col_idx, col in enumerate(df.columns):
            if col_idx in col_format and col_format[col_idx]:
                has_formatting = True
                print(f"\n  Col '{col}':")
                for row_idx, format_type in sorted(col_format[col_idx].items()):
                    value = df.iloc[row_idx, col_idx]
                    symbol = "●" if format_type == "bold" else "○"
                    print(f"    {symbol} Row{row_idx}: {value} -> {format_type}")
        
        if not has_formatting:
            print("  (There is no data column that needs formatting.)")


# ==================== 命令行接口 ====================

def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description='将CSV文件转换为LaTeX表格，自动高亮极值',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s data.csv output.tex
  %(prog)s data.csv output.tex --mode max --caption "实验结果"
  %(prog)s data.csv output.tex --columns "准确率,速度" --booktabs
  %(prog)s data.csv output.tex --config config.json
        """
    )
    
    parser.add_argument('input', help='输入CSV文件路径')
    parser.add_argument('output', help='输出LaTeX文件路径')
    parser.add_argument('--caption', default='table of data', help='表格标题 (默认: table of data)')
    parser.add_argument('--label', default='tab:data', help='表格标签 (默认: tab:data)')
    parser.add_argument('--alignment', choices=['l', 'c', 'r'], default='c', 
                       help='列对齐方式: l=左对齐, c=居中, r=右对齐 (默认: c)')
    parser.add_argument('--mode', choices=['min', 'max', 'plain'], default='min',
                       help='高亮模式: min=最小值, max=最大值, plain=无高亮 (默认: min)')
    parser.add_argument('--columns', help='需要高亮的列名，用逗号分隔 (默认: 所有列)')
    parser.add_argument('--booktabs', action='store_true', help='使用booktabs样式')
    parser.add_argument('--config', help='从JSON配置文件读取参数')
    parser.add_argument('--quiet', action='store_true', help='静默模式，不输出详细信息')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    # 如果指定了配置文件，从配置文件加载
    if args.config:
        try:
            config = load_config(args.config)
            # 配置文件中的参数可以被命令行参数覆盖
            for key, value in config.items():
                if not hasattr(args, key) or getattr(args, key) is None:
                    setattr(args, key, value)
        except Exception as e:
            print(f"Error: Failed to load config file - {e}")
            return 1
    
    # 处理列名参数
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
            verbose=not args.quiet
        )
        return 0
    except Exception as e:
        print(f"Error: - {e}")
        return 1


if __name__ == "__main__":
    exit(main())