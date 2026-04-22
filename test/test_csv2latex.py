"""Tests for csv2latex"""
import pytest
import os
import tempfile
from csv2latex.csv2latex import (
    escape_latex,
    find_extreme_values,
    format_cell,
    generate_latex_table,
    csv_to_latex,
)
import pandas as pd


class TestEscapeLatex:
    """测试 LaTeX 转义函数"""

    def test_backslash(self):
        assert escape_latex("a\\b") == r"a\textbackslash b"

    def test_ampersand(self):
        assert escape_latex("a&b") == r"a\&b"

    def test_percent(self):
        assert escape_latex("50%") == r"50\%"

    def test_dollar(self):
        assert escape_latex("$100") == r"\$100"

    def test_underscore(self):
        assert escape_latex("a_b") == r"a\_b"

    def test_braces(self):
        assert escape_latex("{test}") == r"\{test\}"

    def test_combined(self):
        assert escape_latex("$100_50%") == r"\$100\_50\%"


class TestFindExtremeValues:
    """测试极值查找函数"""

    def test_min_basic(self):
        series = pd.Series([3, 1, 2, 5, 4])
        extreme, second = find_extreme_values(series, mode='min')
        assert extreme == [1]  # 最小值 1 的索引
        assert second == [2]   # 次小值 2 的索引

    def test_max_basic(self):
        series = pd.Series([3, 1, 2, 5, 4])
        extreme, second = find_extreme_values(series, mode='max')
        assert extreme == [3]  # 最大值 5 的索引
        assert second == [4]   # 次大值 4 的索引

    def test_min_only(self):
        series = pd.Series([3, 1, 2, 5, 4])
        extreme, second = find_extreme_values(series, mode='min-only')
        assert extreme == [1]
        assert second == []

    def test_max_only(self):
        series = pd.Series([3, 1, 2, 5, 4])
        extreme, second = find_extreme_values(series, mode='max-only')
        assert extreme == [3]
        assert second == []

    def test_plain(self):
        series = pd.Series([3, 1, 2, 5, 4])
        extreme, second = find_extreme_values(series, mode='plain')
        assert extreme == []
        assert second == []

    def test_with_nan(self):
        series = pd.Series([3, float('nan'), 1, 2])
        extreme, second = find_extreme_values(series, mode='min')
        assert extreme == [2]  # 最小值 1 的索引

    def test_duplicate_min(self):
        series = pd.Series([3, 1, 2, 1, 4])
        extreme, second = find_extreme_values(series, mode='min')
        assert len(extreme) == 2  # 两个 1 都是最小值


class TestFormatCell:
    """测试单元格格式化函数"""

    def test_plain(self):
        assert format_cell("test") == "test"

    def test_bold(self):
        assert format_cell("test", format_type='bold') == "\\textbf{test}"

    def test_underline(self):
        assert format_cell("test", format_type='underline') == "\\underline{test}"

    def test_precision(self):
        assert format_cell(3.14159, precision=2) == "3.14"

    def test_precision_with_formatting(self):
        result = format_cell(3.14159, format_type='bold', precision=2)
        assert result == "\\textbf{3.14}"

    def test_non_numeric_precision(self):
        assert format_cell("text", precision=2) == "text"


class TestGenerateLatexTable:
    """测试 LaTeX 表格生成"""

    def setup_method(self):
        self.df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        self.col_format = {0: {0: 'bold'}, 1: {2: 'underline'}}

    def test_basic_table(self):
        result = generate_latex_table(self.df, self.col_format)
        assert "\\begin{table}" in result
        assert "\\end{table}" in result
        assert "\\documentclass{article}" in result

    def test_snippet_mode(self):
        result = generate_latex_table(self.df, self.col_format, snippet=True)
        assert "\\begin{table}" not in result
        assert "\\documentclass{article}" not in result
        assert "\\begin{tabular}" in result

    def test_booktabs(self):
        result = generate_latex_table(self.df, self.col_format, use_booktabs=True)
        assert "\\toprule" in result
        assert "\\midrule" in result
        assert "\\bottomrule" in result
        assert "\\hline" not in result


class TestCsvToLatex:
    """测试完整的 CSV 到 LaTeX 转换流程"""

    def setup_method(self):
        self.test_csv_content = "A,B,C\n1,2,3\n4,5,6\n7,8,9\n"

    def test_basic_conversion(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as csv_f:
            csv_f.write(self.test_csv_content)
            csv_path = csv_f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as tex_f:
            tex_path = tex_f.name

        try:
            csv_to_latex(csv_path, tex_path, verbose=False)
            with open(tex_path, 'r') as f:
                content = f.read()
            assert "\\begin{table}" in content
        finally:
            os.unlink(csv_path)
            os.unlink(tex_path)

    def test_stdout_output(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as csv_f:
            csv_f.write(self.test_csv_content)
            csv_path = csv_f.name

        try:
            result = csv_to_latex(csv_path, verbose=False)
            assert result is not None
            assert "\\begin{table}" in result
        finally:
            os.unlink(csv_path)
