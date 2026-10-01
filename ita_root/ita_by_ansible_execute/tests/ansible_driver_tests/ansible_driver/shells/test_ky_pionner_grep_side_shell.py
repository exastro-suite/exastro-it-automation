#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License")
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
A: ky_pionner_grep_side_Ansible.sh の単体テスト（#3089）

仕様（確定分）:
  - 複数の検索文字列は AND 条件。同一行である必要はなく、
    ファイル内のどこかに全ての検索文字列があれば成功とする。
  - 終了コードは 0（全て検索できた）/ 非0（それ以外）の2区分のみを仕様とする。
    非0 の内訳（1 と 2）は仕様化しない。

旧実装のバグ（このテストが回帰を防ぐ対象）:
  - 2個目以降の検索文字列が grep に渡らず、1個目だけで判定されていた
  - `printf -v ARG "&q"` のタイプミス（"%q" のはず）
  - 後始末の `2&>1` がタイプミスで、カレントに `1` という空ファイルを作っていた
"""
import glob
import os

import pytest

from .conftest import TMP_STDERR_PREFIX

# 検索ファイル f.txt の内容:
#   alpha bravo
#   charlie


class TestSingleKeyword:
    """検索文字列が1個の場合"""

    def test_a01_hit(self, run_grep_shell, grep_fixture_dir):
        """A-01 単一ヒット -> 0"""
        r = run_grep_shell("f.txt", "alpha", cwd=grep_fixture_dir)
        assert r.returncode == 0, r.stderr

    def test_a02_miss(self, run_grep_shell, grep_fixture_dir):
        """A-02 単一ミス -> 非0"""
        r = run_grep_shell("f.txt", "zzz", cwd=grep_fixture_dir)
        assert r.returncode != 0

    def test_a13_keyword_with_space(self, run_grep_shell, grep_fixture_dir):
        """
        A-13 スペースを含む検索文字列 -> 0

        旧実装は変数を引用符無しで展開していたため単語分割で壊れていた。
        """
        r = run_grep_shell("f.txt", "alpha bravo", cwd=grep_fixture_dir)
        assert r.returncode == 0, r.stderr

    def test_a11_keyword_starting_with_hyphen(self, run_grep_shell, grep_fixture_dir):
        """
        A-11 ハイフン始まりの検索文字列 -> 非0

        `grep -c -- "${ARG}"` の `--` が効いてオプションとして解釈されず、
        単に一致しないだけで終わること。grep の usage エラーにならないこと。
        """
        r = run_grep_shell("f.txt", "-alpha", cwd=grep_fixture_dir)
        assert r.returncode != 0
        assert "usage" not in r.stderr.lower()

    def test_a14_basic_regex_is_kept(self, run_grep_shell, grep_fixture_dir):
        """
        A-14 検索文字列は基本正規表現(BRE)として解釈される -> 0

        `-F` を付けていないため `.` は任意1文字。旧実装と同じ仕様であり、
        意図的に固定しておく（将来 -F を足すならこのテストが落ちる）。
        """
        r = run_grep_shell("f.txt", "al.ha", cwd=grep_fixture_dir)
        assert r.returncode == 0, r.stderr


class TestMultipleKeywords:
    """検索文字列が複数の場合（AND 条件）"""

    def test_a03_two_keywords_same_line(self, run_grep_shell, grep_fixture_dir):
        """A-03 2語が同一行にある -> 0"""
        r = run_grep_shell("f.txt", "alpha", "bravo", cwd=grep_fixture_dir)
        assert r.returncode == 0, r.stderr

    def test_a04_two_keywords_different_lines(self, run_grep_shell, grep_fixture_dir):
        """
        A-04 2語が別の行にある -> 0

        AND の判定単位は「ファイル全体」であり「同一行」ではない、という確定仕様。
        旧実装はパイプで grep を繋ぐ意図だったため同一行条件になるはずだったが、
        そもそも起動していなかった。新実装の仕様を正とする。
        """
        r = run_grep_shell("f.txt", "alpha", "charlie", cwd=grep_fixture_dir)
        assert r.returncode == 0, r.stderr

    def test_a05_three_keywords_all_hit(self, run_grep_shell, grep_fixture_dir):
        """A-05 3語すべてヒット -> 0"""
        r = run_grep_shell("f.txt", "alpha", "bravo", "charlie", cwd=grep_fixture_dir)
        assert r.returncode == 0, r.stderr

    def test_a06_three_keywords_last_miss(self, run_grep_shell, grep_fixture_dir):
        """
        A-06 3語のうち最後がミス -> 非0

        旧実装の主バグの回帰テスト。
        旧実装は2個目以降を grep に渡せておらず、1個目がヒットすれば
        成功と判定していたため、このケースが誤って 0 になっていた。
        """
        r = run_grep_shell("f.txt", "alpha", "bravo", "zzz", cwd=grep_fixture_dir)
        assert r.returncode != 0

    def test_a06b_two_keywords_second_miss(self, run_grep_shell, grep_fixture_dir):
        """A-06b 2語のうち2個目がミス -> 非0（同じく旧バグの回帰）"""
        r = run_grep_shell("f.txt", "alpha", "zzz", cwd=grep_fixture_dir)
        assert r.returncode != 0

    def test_a06c_first_miss_short_circuits(self, run_grep_shell, grep_fixture_dir):
        """A-06c 1個目がミスなら以降を見ずに非0"""
        r = run_grep_shell("f.txt", "zzz", "alpha", cwd=grep_fixture_dir)
        assert r.returncode != 0


class TestArgumentValidation:
    """引数の異常系"""

    def test_a07_no_keyword(self, run_grep_shell, grep_fixture_dir):
        """A-07 検索文字列が0個 -> 非0"""
        r = run_grep_shell("f.txt", cwd=grep_fixture_dir)
        assert r.returncode != 0

    def test_a07b_no_argument_at_all(self, run_grep_shell, grep_fixture_dir):
        """A-07b 引数なし -> 非0"""
        r = run_grep_shell(cwd=grep_fixture_dir)
        assert r.returncode != 0

    def test_a08_missing_file(self, run_grep_shell, grep_fixture_dir):
        """A-08 検索ファイルが存在しない -> 非0"""
        r = run_grep_shell("nofile.txt", "alpha", cwd=grep_fixture_dir)
        assert r.returncode != 0

    def test_a09_empty_file(self, run_grep_shell, grep_fixture_dir):
        """A-09 検索ファイルが空 -> 非0"""
        r = run_grep_shell("empty.txt", "alpha", cwd=grep_fixture_dir)
        assert r.returncode != 0

    def test_a10_directory_as_file(self, run_grep_shell, grep_fixture_dir):
        """A-10 検索ファイルがディレクトリ -> 非0"""
        r = run_grep_shell("adir", "alpha", cwd=grep_fixture_dir)
        assert r.returncode != 0


class TestSpecialCharacters:
    """特殊文字を含む引数"""

    @pytest.mark.parametrize(
        "keyword",
        [
            pytest.param("alpha;{canary}", id="semicolon"),
            pytest.param("alpha$({canary})", id="command_substitution"),
            pytest.param("alpha`{canary}`", id="backquote"),
            pytest.param("alpha && {canary}", id="and_list"),
            pytest.param("alpha | {canary}", id="pipe"),
            pytest.param("$({canary})", id="command_substitution_only"),
        ],
    )
    def test_a15_a17_no_command_injection(self, run_grep_shell, grep_fixture_dir, keyword):
        """
        A-15〜A-17 検索文字列に埋め込んだコマンドが実行されないこと

        終了コードだけでは「一致しなかった」のか「注入されなかった」のかを
        区別できないため、副作用のあるコマンド（canary ファイルの作成）を
        埋め込み、ファイルが生まれていないことで判定する。
        """
        canary = grep_fixture_dir / "canary_created"
        injected = keyword.replace("{canary}", f"touch {canary}")

        r = run_grep_shell("f.txt", injected, cwd=grep_fixture_dir)

        assert not canary.exists(), (
            f"コマンドが注入され実行された: 引数={injected!r} rc={r.returncode}"
        )
        # 一致しないので非0。少なくとも「成功扱い」にはならないこと
        assert r.returncode != 0

    def test_a18_single_quote(self, run_grep_shell, grep_fixture_dir):
        """A-18 シングルクォートを含む検索文字列 -> 非0（シェル構文エラーにならない）"""
        r = run_grep_shell("f.txt", "a'b", cwd=grep_fixture_dir)
        assert r.returncode != 0
        assert "unexpected" not in r.stderr.lower()

    def test_a18b_double_quote(self, run_grep_shell, grep_fixture_dir):
        """A-18b ダブルクォートを含む検索文字列 -> 非0"""
        r = run_grep_shell("f.txt", 'a"b', cwd=grep_fixture_dir)
        assert r.returncode != 0
        assert "unexpected" not in r.stderr.lower()

    def test_a19_filename_with_space(self, run_grep_shell, grep_fixture_dir):
        """A-19 検索ファイル名にスペース -> 0"""
        r = run_grep_shell("sp ace.txt", "alpha", cwd=grep_fixture_dir)
        assert r.returncode == 0, r.stderr

    def test_a20_filename_multibyte(self, run_grep_shell, grep_fixture_dir):
        """A-20 検索ファイル名が日本語 -> 0"""
        r = run_grep_shell("日本語.txt", "alpha", cwd=grep_fixture_dir)
        assert r.returncode == 0, r.stderr

    def test_a20b_multibyte_keyword(self, run_grep_shell, tmp_path):
        """A-20b 検索文字列が日本語 -> ヒットすれば 0 / しなければ非0"""
        target = tmp_path / "ja.txt"
        target.write_text("あいうえお\nかきくけこ\n", encoding="utf-8")

        hit = run_grep_shell(target.name, "あいう", cwd=tmp_path)
        assert hit.returncode == 0, hit.stderr

        miss = run_grep_shell(target.name, "さしすせそ", cwd=tmp_path)
        assert miss.returncode != 0


class TestSideEffects:
    """副作用（一時ファイル・カレントディレクトリ汚染）"""

    def test_a22_no_file_named_1_is_created(self, run_grep_shell, grep_fixture_dir):
        """
        A-22 カレントディレクトリに `1` というファイルを作らないこと

        旧実装の後始末は `/bin/rm -rf ... >/dev/null 2&>1` で、
        `2&>1` が `2 &> 1`（引数 2 を rm に渡し、出力をファイル `1` へ）と
        解釈されるため、カレントに空ファイル `1` が生まれていた。
        """
        r = run_grep_shell("f.txt", "alpha", cwd=grep_fixture_dir)
        assert r.returncode == 0, r.stderr
        assert not (grep_fixture_dir / "1").exists(), (
            "カレントに `1` が生成された（2&>1 のタイプミスが再発している）"
        )

    def test_a22b_no_file_named_1_on_failure_path(self, run_grep_shell, grep_fixture_dir):
        """A-22b 失敗経路でもカレントに `1` を作らないこと"""
        run_grep_shell("f.txt", "zzz", cwd=grep_fixture_dir)
        run_grep_shell("nofile.txt", "alpha", cwd=grep_fixture_dir)
        run_grep_shell("f.txt", cwd=grep_fixture_dir)
        assert not (grep_fixture_dir / "1").exists()

    def test_a22c_no_stray_files_in_cwd(self, run_grep_shell, grep_fixture_dir):
        """A-22c 実行前後でカレントの内容が変わらないこと"""
        before = sorted(p.name for p in grep_fixture_dir.iterdir())
        run_grep_shell("f.txt", "alpha", cwd=grep_fixture_dir)
        run_grep_shell("f.txt", "zzz", cwd=grep_fixture_dir)
        after = sorted(p.name for p in grep_fixture_dir.iterdir())
        assert before == after, f"カレントに副作用ファイルが増えた: {set(after) - set(before)}"

    def test_a21_no_stderr_tempfile_left(self, run_grep_shell, grep_fixture_dir):
        """
        A-21 /tmp に stderr 退避ファイルを残さないこと

        シェルは /tmp/ita_stderr.$$ を作って最後に削除する。
        $$ は実行ごとに変わるので、実行前後の差分で判定する。
        """
        before = set(glob.glob(TMP_STDERR_PREFIX + "*"))

        run_grep_shell("f.txt", "alpha", cwd=grep_fixture_dir)
        run_grep_shell("f.txt", "zzz", cwd=grep_fixture_dir)
        run_grep_shell("nofile.txt", "alpha", cwd=grep_fixture_dir)

        after = set(glob.glob(TMP_STDERR_PREFIX + "*"))
        assert after - before == set(), f"一時ファイルが残った: {after - before}"


class TestSpecUndecided:
    """期待値が未確定のケース。現状の挙動を固定して、変わったら気付けるようにする"""

    def test_a12_empty_keyword_currently_succeeds(self, run_grep_shell, grep_fixture_dir):
        """
        A-12 空文字列の検索文字列 -> 現状 0（全行マッチ）

        仕様未確定。対話ファイルに `- ""` と書くと
        CheckDialogfileFormat の空チェック（split("-")[1].strip() が空か）を
        通過し、yaml で空文字列になるため到達可能。
        `grep -c -- "" file` は全行マッチするので「検索成功」と判定される。

        エラーにする方針が決まったら、このテストを非0期待に書き換える。
        """
        r = run_grep_shell("f.txt", "", cwd=grep_fixture_dir)
        assert r.returncode == 0, (
            "空文字列の扱いが変わった。仕様変更なら期待値を更新すること"
        )

    def test_a12b_empty_keyword_in_and_condition(self, run_grep_shell, grep_fixture_dir):
        """A-12b AND 条件に空文字列が混ざった場合 -> 空文字列は判定に影響しない"""
        assert run_grep_shell("f.txt", "alpha", "", cwd=grep_fixture_dir).returncode == 0
        assert run_grep_shell("f.txt", "zzz", "", cwd=grep_fixture_dir).returncode != 0


class TestPosixShellCompatibility:
    """
    A-23 bash 以外の sh でも動くこと

    ITA は `sh <script>` で起動するため shebang(#!/bin/bash) は無視される。
    実行環境の /bin/sh が bash 以外（dash など）の場合に壊れないことを見る。
    このコンテナには dash が無いためスキップされる。
    """

    ALT_SHELLS = ["dash", "ash", "busybox sh"]

    @staticmethod
    def _find_alt_shell():
        for name in ["dash", "ash"]:
            for d in os.environ.get("PATH", "").split(os.pathsep):
                cand = os.path.join(d, name)
                if os.path.isfile(cand) and os.access(cand, os.X_OK):
                    return cand
        return None

    def test_a23_runs_under_non_bash_sh(self, run_grep_shell, grep_fixture_dir):
        alt = self._find_alt_shell()
        if alt is None:
            pytest.skip("bash 以外の sh（dash/ash）が見つからないためスキップ")

        assert run_grep_shell(
            "f.txt", "alpha", cwd=grep_fixture_dir, shell_bin=alt
        ).returncode == 0
        assert run_grep_shell(
            "f.txt", "alpha", "charlie", cwd=grep_fixture_dir, shell_bin=alt
        ).returncode == 0
        assert run_grep_shell(
            "f.txt", "alpha", "zzz", cwd=grep_fixture_dir, shell_bin=alt
        ).returncode != 0
        assert run_grep_shell("f.txt", cwd=grep_fixture_dir, shell_bin=alt).returncode != 0
