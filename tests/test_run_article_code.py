"""scripts/run_article_code.py の抽出と照合（uv は実行しない）。"""

from __future__ import annotations

from scripts.run_article_code import (
    MARKER,
    RunOutput,
    compare_lines,
    compare_table,
    expected_from_comments,
    extract_blocks,
    judge,
    lines_match,
    plan_packages,
    run_article,
    table_numbers,
)

ARTICLE = """\
# 題

```python
print(1 + 1)  # 2
```

```text
2
```

```python
x = 3
print(x)
# 3
# 4
```

| a | b |
|---|---:|
| 1 | $2\\times10^{-3}$ |
"""


def test_extract_blocks_finds_python_text_and_table() -> None:
    blocks = extract_blocks(ARTICLE)
    assert [b.index for b in blocks] == [1, 2]
    assert blocks[0].text_lines == ["2"]
    assert blocks[1].table_rows[-1] == "| 1 | $2\\times10^{-3}$ |"
    assert len(blocks[1].table_rows) == 2  # 区切り行は除く


def test_extract_ignores_python_inside_other_fence() -> None:
    md = "````markdown\n```python\nprint(1)\n```\n````\n"
    assert extract_blocks(md) == []


def test_expected_from_inline_and_following_comments() -> None:
    code = "print(1)  # 1 2\nx = 5  # 説明\nprint(x)\n# 5\n# 6\n# unrelated"
    assert expected_from_comments(code) == ["1 2", "5", "6", "unrelated"]


def test_expected_ignores_non_print_comments() -> None:
    assert expected_from_comments("x = 1  # not output\n# also not\n") == []


def test_expected_inside_loop_with_comment_lines() -> None:
    code = "for i in range(2):\n    print(i)\n    # 0\n    # 1\n"
    assert expected_from_comments(code) == ["0", "1"]


def test_lines_match_compares_numbers_as_numbers() -> None:
    assert lines_match("[ 0.1  0.2 -0.7]", "[0.1 0.2 -0.7]")
    assert lines_match("0.130", "0.13")
    assert not lines_match("0.137", "0.138")
    assert lines_match("0.137", "0.1371", rtol=1e-2)
    assert not lines_match("a 1", "b 1")


def test_lines_match_allows_prose_around_expected_output() -> None:
    assert lines_match("出力: (13, 7, (1, 1, 0, 0))（価値、重さ）", "(13, 7, (1, 1, 0, 0))")
    # 数の途中で切れた一致は認めない
    assert not lines_match("3.6e-11 4.75e+04 1.07e+05", "6e-11 4.75e+04 1.07e+05")


def test_compare_lines_is_ordered_subsequence() -> None:
    actual = ["header", "1 2", "noise", "3 4"]
    assert compare_lines(["1 2", "3 4"], actual) == []
    bad = compare_lines(["3 4", "1 2"], actual)  # 順序が逆
    assert [u.expected for u in bad] == ["1 2"]
    wrong = compare_lines(["1 9"], actual)
    assert wrong[0].closest_actual == "1 2"


def test_table_numbers_reads_tex() -> None:
    assert table_numbers("| 3 | $10^{2}$ | $3\\times10^{-13}$ |") == [3.0, 100.0, 3e-13]
    assert table_numbers("| (3, $-3.5$) | 0.137 |") == [3.0, -3.5, 0.137]


def test_compare_table_matches_row_numbers_in_a_printed_line() -> None:
    rows = ["| 次数 | 誤差 |", "| 3 | $3\\times10^{-13}$ |", "| 6 | $3\\times10^{-9}$ |"]
    actual = ["3 1e+02 3e-13", "6 2e+04 4e-09"]
    bad = compare_table(rows, actual)
    assert [u.expected for u in bad] == [rows[2]]
    assert bad[0].closest_actual == "6 2e+04 4e-09"


def test_judge_statuses() -> None:
    block = extract_blocks(ARTICLE)[0]
    assert judge(block, "2\n2\n", 0.0).status == "ok"
    assert judge(block, "3\n", 0.0).status == "mismatch"
    silent = extract_blocks("```python\nx = 1\n```\n")[0]
    assert judge(silent, "", 0.0).status == "no-expected-output"


def test_plan_packages_allowlist_and_unknown() -> None:
    extra, unknown = plan_packages("import numpy\nimport json\nfrom sklearn import svm\nimport foo")
    assert extra == ["scikit-learn"]
    assert unknown == ["foo"]


def test_run_article_retries_with_earlier_blocks_on_name_error() -> None:
    md = "```python\nx = 2\nprint(x)  # 2\n```\n\n```python\nprint(x * 2)  # 4\n```\n"
    calls: list[str] = []

    def fake_runner(code: str, extra: list[str], timeout: float) -> RunOutput:
        calls.append(code)
        if "OUTPUT_STARTS_HERE" in code:
            return RunOutput(0, f"2\n{MARKER}\n4\n", "")
        if "x = 2" in code:
            return RunOutput(0, "2\n", "")
        return RunOutput(1, "", "Traceback\nNameError: name 'x' is not defined")

    results = run_article(md, runner=fake_runner)
    assert [r.status for r in results] == ["ok", "ok"]
    assert "前置き" in results[1].note
    assert len(calls) == 3


def test_run_article_reports_error_skipped_and_timeout() -> None:
    md = (
        "```python\nimport foo\n```\n\n"
        "```python\nraise ValueError('x')\n```\n\n"
        "```python\nwhile True: pass\n```\n"
    )

    def fake_runner(code: str, extra: list[str], timeout: float) -> RunOutput:
        if "ValueError" in code:
            return RunOutput(1, "", "Traceback\nValueError: x")
        return RunOutput(-1, "", "", timed_out=True)

    results = run_article(md, timeout=5, runner=fake_runner)
    assert [r.status for r in results] == ["skipped", "error", "error"]
    assert "ValueError: x" in results[1].error_tail
    assert "timeout" in results[2].error_tail
