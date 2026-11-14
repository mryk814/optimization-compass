"""記事の ```python ブロックを再実行し、本文に書かれた出力と照らし合わせる。

記事の数値は計算から出したものでなければならない。記事を大量に書き直すとき、
レビュアーが各コードブロックの「書かれた出力」と「実際の出力」を素早く突き合わせるための
補助であり、ゲートではない（食い違いは人が見て判断する）。

使い方::

    uv run python scripts/run_article_code.py content/concepts/linear-least-squares.md
    uv run python scripts/run_article_code.py --json --rtol 1e-3 content/concepts/*.md

実行
    ブロックは記事内の順に、ブロックごとの新しいサブプロセスで走らせる。環境は
    ``uv run --no-project --with numpy --with scipy python -``（プロジェクトの環境には
    SciPy がないため）。ブロックの import に許可リストのパッケージ（cvxpy, scikit-learn,
    networkx, pyomo, optuna, ortools, casadi, pymoo, cma, nlopt, highspy, pandas,
    matplotlib）があれば ``--with`` を足す。許可リストにも標準ライブラリにもない import が
    あるブロックは error ではなく skipped にする。NameError で落ち、前のブロックが走って
    いるときは、動いた前のブロックを前置きして再実行する（その旨を note に出す）。

書かれた出力の集め方（単純な規則）
    1. ``print(...)`` の文の行末コメント、またはその文の直後に続くコメントだけの行を、
       出力の期待行とする（ソースの順）。print 以外の文のコメントは見ない。
    2. python ブロックの直後（空行をはさんでよい）の ```text / ```output ブロックの各行も
       期待行とする。
    3. python ブロックの直後の Markdown の表は、各行の数値列を期待とする（数値が2つ以上ある
       行だけ。先頭の見出し行は見ない）。``3\\times10^{-13}`` や ``10^{9}`` は数値に直す。

照合
    期待行は、実際の標準出力の行に「この順で部分列として」現れればよい（print のうち
    コメントのないものがあってもよい）。1行の一致は、空白を無視し、数値は数値として
    比べ（``0.130`` と ``0.13`` は同じ）、数値以外の部分は文字列として等しいこと。
    ``--rtol`` を与えると数値は相対許容差で比べる。表の行は、その行の数値列が実際の
    どれかの行の数値列の部分列（またはその逆）になっていればよい。
    食い違いは、期待行ごとに、いちばん似ている実際の行を並べて示す。

終了コードは、mismatch か error があれば 1、なければ 0。
"""

from __future__ import annotations

import argparse
import ast
import difflib
import io
import json
import math
import os
import re
import subprocess
import sys
import tokenize
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_TIMEOUT = 120.0
MARKER = "\x1e__ARTICLE_CODE_OUTPUT_STARTS_HERE__"

# import されるモジュール名 -> uv の --with に渡すパッケージ名
BASE_PACKAGES = {"numpy": "numpy", "scipy": "scipy"}
EXTRA_PACKAGES = {
    "cvxpy": "cvxpy",
    "sklearn": "scikit-learn",
    "networkx": "networkx",
    "pyomo": "pyomo",
    "optuna": "optuna",
    "ortools": "ortools",
    "casadi": "casadi",
    "pymoo": "pymoo",
    "cma": "cma",
    "nlopt": "nlopt",
    "highspy": "highspy",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
}

TEXT_FENCE_LANGS = {"text", "output", "console", "plain", "txt", ""}

NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


# ---------------------------------------------------------------------------
# 抽出（純粋）
# ---------------------------------------------------------------------------


@dataclass
class Block:
    index: int  # 記事内の python ブロックの通し番号（1 始まり）
    line: int  # 開きフェンスの行番号（1 始まり）
    code: str
    text_lines: list[str] = field(default_factory=list)  # 直後の text ブロック
    table_rows: list[str] = field(default_factory=list)  # 直後の表（区切り行を除く）


_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([^\s`]*)")


def extract_blocks(markdown: str) -> list[Block]:
    lines = markdown.splitlines()
    # まず全フェンスを (lang, 開き行, 閉じ行) として拾う。他言語のフェンスの中は見ない。
    fences: list[tuple[str, int, int]] = []
    i = 0
    while i < len(lines):
        m = _FENCE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        marker, lang = m.group(1), m.group(2).lower()
        j = i + 1
        while j < len(lines):
            s = lines[j].strip()
            if len(s) >= len(marker) and set(s) == {marker[0]}:
                break
            j += 1
        fences.append((lang, i, j))
        i = j + 1

    blocks: list[Block] = []
    for k, (lang, start, end) in enumerate(fences):
        if lang not in ("python", "py", "python3"):
            continue
        block = Block(index=len(blocks) + 1, line=start + 1, code="\n".join(lines[start + 1 : end]))
        p = end + 1
        while p < len(lines) and not lines[p].strip():
            p += 1
        if p < len(lines):
            if k + 1 < len(fences) and fences[k + 1][1] == p:
                nlang, nstart, nend = fences[k + 1]
                if nlang in TEXT_FENCE_LANGS:
                    block.text_lines = [x for x in lines[nstart + 1 : nend] if x.strip()]
            elif lines[p].lstrip().startswith("|"):
                q = p
                while q < len(lines) and lines[q].lstrip().startswith("|"):
                    row = lines[q].strip()
                    if not re.fullmatch(r"\|[\s:|-]+\|?", row):
                        block.table_rows.append(row)
                    q += 1
        blocks.append(block)
    return blocks


def expected_from_comments(code: str) -> list[str]:
    """print 文の行末コメントと、直後のコメントだけの行を、ソース順に返す。"""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    comments: dict[int, tuple[str, bool]] = {}  # 行 -> (本文, 行末コメントか)
    src_lines = code.splitlines()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type == tokenize.COMMENT:
                row, col = tok.start
                inline = bool(src_lines[row - 1][:col].strip())
                comments[row] = (tok.string[1:].strip(), inline)
    except (tokenize.TokenError, IndentationError):
        pass

    prints = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Name)
        and n.value.func.id == "print"
    ]
    prints.sort(key=lambda n: n.lineno)
    out: list[str] = []
    for node in prints:
        end = node.end_lineno or node.lineno
        got = comments.get(end)
        if got and got[1] and got[0]:
            out.append(got[0])
        row = end + 1
        while row in comments and not comments[row][1]:
            if comments[row][0]:
                out.append(comments[row][0])
            row += 1
    return out


def imported_modules(code: str) -> set[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    return mods


def plan_packages(code: str) -> tuple[list[str], list[str]]:
    """(追加で --with するパッケージ, 未知の import) を返す。"""
    extra: list[str] = []
    unknown: list[str] = []
    for mod in sorted(imported_modules(code)):
        if mod in sys.stdlib_module_names or mod in BASE_PACKAGES:
            continue
        if mod in EXTRA_PACKAGES:
            extra.append(EXTRA_PACKAGES[mod])
        else:
            unknown.append(mod)
    return extra, unknown


# ---------------------------------------------------------------------------
# 照合（純粋）
# ---------------------------------------------------------------------------


def _split_numbers(s: str) -> tuple[str, list[float]]:
    """数値以外の部分（空白を除く）と、数値の列に分ける。"""
    nums = [float(x) for x in NUMBER_RE.findall(s)]
    skeleton = re.sub(r"\s+", "", NUMBER_RE.sub("#", s))
    return skeleton, nums


def _num_equal(a: float, b: float, rtol: float) -> bool:
    if a == b:
        return True
    if rtol <= 0:
        return False
    return math.isclose(a, b, rel_tol=rtol, abs_tol=0.0)


def lines_match(expected: str, actual: str, rtol: float = 0.0) -> bool:
    es, en = _split_numbers(expected)
    a_s, an = _split_numbers(actual)
    if es != a_s or len(en) != len(an):
        # 「出力: …（説明）」のように前後に散文がついた期待行は、実際の行を含んでいれば一致とする
        flat_e = re.sub(r"\s+", "", expected)
        flat_a = re.sub(r"\s+", "", actual)
        # 数の途中で切れた一致（3.6e-11 の中の 6e-11）は除く
        pattern = r"(?<![\w.+\-])" + re.escape(flat_a) + r"(?![\w.])"
        return len(flat_a) >= 4 and re.search(pattern, flat_e) is not None
    return all(_num_equal(x, y, rtol) for x, y in zip(en, an, strict=True))


def _closest(expected: str, candidates: list[str]) -> str | None:
    if not candidates:
        return None
    flat = re.sub(r"\s+", " ", expected)

    def score(c: str) -> float:
        return difflib.SequenceMatcher(None, flat, re.sub(r"\s+", " ", c)).ratio()

    return max(candidates, key=score)


def actual_lines(stdout: str) -> list[str]:
    return [x.strip() for x in stdout.splitlines() if x.strip()]


@dataclass
class Unmatched:
    expected: str
    closest_actual: str | None


def compare_lines(expected: list[str], actual: list[str], rtol: float = 0.0) -> list[Unmatched]:
    """期待行が、実際の行に順序つきの部分列として現れるかを調べる。現れなかった期待行を返す。"""
    unmatched: list[Unmatched] = []
    pos = 0
    for e in expected:
        hit = next((i for i in range(pos, len(actual)) if lines_match(e, actual[i], rtol)), None)
        if hit is None:
            unmatched.append(Unmatched(e, _closest(e, actual[pos:] or actual)))
        else:
            pos = hit + 1
    return unmatched


_TEX_EXP_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\\times\s*10\^\{?\s*(-?\d+)\s*\}?")
_TEX_POW_RE = re.compile(r"10\^\{?\s*(-?\d+)\s*\}?")


def table_numbers(row: str) -> list[float]:
    s = row.replace("−", "-").replace("$", "").replace("\\,", "")
    s = _TEX_EXP_RE.sub(r"\1e\2", s)
    s = _TEX_POW_RE.sub(r"1e\1", s)
    s = re.sub(r"_\{[^}]*\}|_\w", "", s)  # \log_{10} の添字の 10 を数値として拾わない
    s = re.sub(r"\\[A-Za-z]+", "", s)
    return [float(x) for x in NUMBER_RE.findall(s)]


def _subsequence(needle: list[float], hay: list[float], rtol: float) -> bool:
    pos = 0
    for x in needle:
        while pos < len(hay) and not _num_equal(x, hay[pos], rtol):
            pos += 1
        if pos == len(hay):
            return False
        pos += 1
    return True


def compare_table(rows: list[str], actual: list[str], rtol: float = 0.0) -> list[Unmatched]:
    """表のデータ行（先頭の見出し行は見ない）が、実際のどれかの行と数値列で対応するかを調べる。

    行の数値列が実際の行の数値列を含むか、その逆（行に「種0」のような余分な数がある場合）
    であれば対応するとみなす。表は print の出力そのものではないので、数値が2つ以上ある行だけ見る。
    """
    actual_nums = [[float(x) for x in NUMBER_RE.findall(a)] for a in actual]
    unmatched: list[Unmatched] = []
    for row in rows[1:]:
        nums = table_numbers(row)
        if len(nums) < 2:
            continue
        if any(
            len(an) >= 2 and (_subsequence(nums, an, rtol) or _subsequence(an, nums, rtol))
            for an in actual_nums
        ):
            continue
        best = None
        best_score = -1
        for a, an in zip(actual, actual_nums, strict=True):
            score = sum(any(_num_equal(x, y, rtol) for y in an) for x in nums)
            if score > best_score:
                best, best_score = a, score
        unmatched.append(Unmatched(row, best))
    return unmatched


# ---------------------------------------------------------------------------
# 実行
# ---------------------------------------------------------------------------


@dataclass
class RunOutput:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


Runner = Callable[[str, list[str], float], RunOutput]


def run_python(code: str, extra_packages: list[str], timeout: float) -> RunOutput:
    cmd = ["uv", "run", "--no-project", "-q"]
    for pkg in [*BASE_PACKAGES.values(), *sorted(set(extra_packages))]:
        cmd += ["--with", pkg]
    cmd += ["python", "-X", "utf8", "-"]
    env = {**os.environ, "MPLBACKEND": "Agg", "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        out, err = proc.communicate(code.encode("utf-8"), timeout=timeout)
    except subprocess.TimeoutExpired:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.kill()
        out, err = proc.communicate()
        return RunOutput(-1, out.decode("utf-8", "replace"), err.decode("utf-8", "replace"), True)
    return RunOutput(
        proc.returncode, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")
    )


@dataclass
class BlockResult:
    index: int
    line: int
    status: str  # ok / mismatch / no-expected-output / error / skipped
    note: str = ""
    expected_count: int = 0
    unmatched: list[Unmatched] = field(default_factory=list)
    error_tail: str = ""


def _tail(text: str, n: int = 6) -> str:
    return "\n".join(text.strip().splitlines()[-n:])


def judge(block: Block, actual_stdout: str, rtol: float) -> BlockResult:
    """実行結果（標準出力）と、ブロックに書かれた期待を照らして結果を作る。"""
    actual = actual_lines(actual_stdout)
    expected = expected_from_comments(block.code) + [x.strip() for x in block.text_lines]
    bad = compare_lines(expected, actual, rtol) + compare_table(block.table_rows, actual, rtol)
    count = len(expected) + sum(1 for r in block.table_rows[1:] if len(table_numbers(r)) >= 2)
    if bad:
        return BlockResult(block.index, block.line, "mismatch", expected_count=count, unmatched=bad)
    if count == 0:
        return BlockResult(block.index, block.line, "no-expected-output")
    return BlockResult(block.index, block.line, "ok", expected_count=count)


def run_article(
    markdown: str,
    timeout: float = DEFAULT_TIMEOUT,
    rtol: float = 0.0,
    runner: Runner = run_python,
) -> list[BlockResult]:
    results: list[BlockResult] = []
    good_codes: list[str] = []  # ここまでに動いたブロックのコード（前置き用）
    chained = False  # 前置きが要ったブロックが出たら、以降は最初から前置きして走らせる
    broken_before = False  # 走らなかった（skipped / error の）ブロックが前にある
    for block in extract_blocks(markdown):
        extra, unknown = plan_packages(block.code)
        if unknown:
            reason = "未知の import: " + ", ".join(unknown)
            results.append(BlockResult(block.index, block.line, "skipped", note=reason))
            broken_before = True
            continue
        note = ""
        if chained and good_codes:
            run = RunOutput(1, "", "NameError (前置きして再実行)")
        else:
            run = runner(block.code, extra, timeout)
        if run.returncode != 0 and not run.timed_out and "NameError" in run.stderr and good_codes:
            prefix = "\n\n".join(good_codes)
            combined = f"{prefix}\n\nprint({MARKER!r}, flush=True)\n\n{block.code}"
            extra2, unknown2 = plan_packages(combined)
            if unknown2:
                reason = "前のブロックの未知の import: " + ", ".join(unknown2)
                results.append(BlockResult(block.index, block.line, "skipped", note=reason))
                broken_before = True
                continue
            run2 = runner(combined, extra2, timeout)
            run = RunOutput(
                run2.returncode, run2.stdout.split(MARKER, 1)[-1], run2.stderr, run2.timed_out
            )
            note = f"NameError のため、前の {len(good_codes)} ブロックを前置きして実行"
            chained = True
        if (
            run.returncode != 0
            and not run.timed_out
            and "NameError" in run.stderr
            and broken_before
        ):
            note = "NameError。走らなかった前のブロックに依存している可能性があり、判定できない"
            results.append(BlockResult(block.index, block.line, "skipped", note=note))
            continue
        if run.timed_out:
            broken_before = True
            tail = f"timeout ({timeout:g} s)"
            results.append(
                BlockResult(block.index, block.line, "error", note=note, error_tail=tail)
            )
            continue
        if run.returncode != 0:
            broken_before = True
            tail = _tail(run.stderr)
            results.append(
                BlockResult(block.index, block.line, "error", note=note, error_tail=tail)
            )
            continue
        result = judge(block, run.stdout, rtol)
        result.note = note
        results.append(result)
        good_codes.append(block.code)
    return results


# ---------------------------------------------------------------------------
# 表示
# ---------------------------------------------------------------------------


def format_report(path: str, results: list[BlockResult]) -> str:
    out = [f"== {path}"]
    if not results:
        out.append("  (python ブロックなし)")
    for r in results:
        head = f"  [{r.status}] block {r.index} (line {r.line})"
        if r.note:
            head += f"  -- {r.note}"
        out.append(head)
        for u in r.unmatched:
            actual = u.closest_actual if u.closest_actual is not None else "-"
            out.append(f"      expected: {u.expected}")
            out.append(f"      actual:   {actual}")
        if r.error_tail:
            out.extend("      " + x for x in r.error_tail.splitlines())
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="記事の python ブロックを再実行して出力を照合する")
    parser.add_argument("articles", nargs="+", type=Path)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="ブロックごとの秒数")
    parser.add_argument("--rtol", type=float, default=0.0, help="数値の相対許容差（既定は厳密）")
    parser.add_argument("--json", action="store_true", help="機械可読な出力")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    failed = False
    payload: dict[str, list[dict]] = {}
    for path in args.articles:
        results = run_article(path.read_text(encoding="utf-8"), args.timeout, args.rtol)
        failed |= any(r.status in ("mismatch", "error") for r in results)
        if args.json:
            payload[str(path)] = [asdict(r) for r in results]
        else:
            print(format_report(str(path), results), flush=True)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
