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
B: pioneer_module.py の単体テスト（#3089）

pexpect と subprocess を差し替えて main() を丸ごと駆動し、
検索シェルに渡されるコマンド文字列と一時ファイルの後始末を検証する。

旧実装のバグ（このテストが回帰を防ぐ対象）:
  1. subprocess.run(["sh ", ...], shell=True) はリストの第1要素 "sh " だけを
     実行するため、検索シェルが一度も起動していなかった。
  2. parameter_cmd_list の初期化が「parameter キーがある時だけ」だったため、
     exec_list の要素をまたいで前の要素の検索文字列が漏れていた。
     parameter を一度も書かない対話ファイルでは NameError になっていた。
  3. stdout_file 指定時、default shell 分岐で指定ファイルを無条件に削除していた。
     一方 user shell 分岐では一時ファイルを削除しておらず残留していた。
  4. state に未知キーがあると private_output()（未定義）を呼んで NameError。
"""
import glob
import os

import pytest

from .conftest import (
    TMP_STDOUT_PREFIX,
    dialog,
    encode_vault_value,
    parse_shell_command,
    state_block,
)


def make_user_shell(env, name="user_shell.sh"):
    """user shell 分岐用のダミースクリプトを作る"""
    path = env.root / name
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    return path


class TestShellInvocation:
    """B-01 検索シェルが実際に起動し、引数が渡ること"""

    def test_b01_default_shell_receives_arguments(self, pioneer_env, run_pioneer):
        """
        B-01 default shell（shell 未指定）に stdout_file と parameter が渡る

        旧実装ではリストの第1要素 "sh " だけが実行され、検索シェルは
        起動すらしていなかった。ここが今回の修正の中心。
        """
        pioneer_env.write_dialog(dialog(state_block(parameter=["hello"])))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        parsed = parse_shell_command(res.shell_command)

        assert parsed["script"] == str(pioneer_env.grep_shell), (
            "grep_shell_dir から組み立てたデフォルトシェルが渡されていない"
        )
        assert parsed["parameters"] == ["hello"]

    def test_b01b_user_shell_receives_arguments(self, pioneer_env, run_pioneer):
        """B-01b user shell（shell 指定）に stdout_file と parameter が渡る"""
        user_shell = make_user_shell(pioneer_env)

        pioneer_env.write_dialog(
            dialog(state_block(shell=str(user_shell), parameter=["hello"]))
        )
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        parsed = parse_shell_command(res.shell_command)
        assert parsed["script"] == str(user_shell)
        assert parsed["parameters"] == ["hello"]

    def test_b01c_shell_is_invoked_as_single_string(self, pioneer_env, run_pioneer):
        """
        B-01c subprocess.run にはリストではなく1本の文字列を渡すこと

        shell=True で実行するため、リストを渡すと第1要素しか実行されない。
        """
        pioneer_env.write_dialog(dialog(state_block(parameter=["hello"])))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert isinstance(res.shell_command, str), (
            f"subprocess.run に文字列以外が渡された: {type(res.shell_command)}"
        )
        assert res.shell_command.startswith("sh ")


class TestParameterQuoting:
    """B-02 / B-03 検索文字列のクォートとコマンド注入"""

    @pytest.mark.parametrize(
        "raw",
        [
            pytest.param("plain", id="plain"),
            pytest.param("with space", id="space"),
            pytest.param("a;b", id="semicolon"),
            pytest.param("$(id)", id="command_substitution"),
            pytest.param("`id`", id="backquote"),
            pytest.param("a'b", id="single_quote"),
            pytest.param('a"b', id="double_quote"),
            pytest.param("a|b", id="pipe"),
            pytest.param("a&&b", id="and_list"),
            pytest.param("*", id="glob"),
            pytest.param("-v", id="leading_hyphen"),
            pytest.param("", id="empty"),
            pytest.param("日本語 テスト", id="multibyte"),
        ],
    )
    def test_b02_parameter_is_quoted_and_preserved(self, pioneer_env, run_pioneer, raw):
        """
        B-02 検索文字列がクォートされ、シェルの語として原文のまま復元されること

        shlex.split で分解した結果が元の文字列と一致することで、
        「クォートが効いている」と「値が変質していない」を同時に確認する。
        """
        pioneer_env.write_dialog(dialog(state_block(parameter=[raw])))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        parsed = parse_shell_command(res.shell_command)
        assert parsed["parameters"] == [raw], (
            f"検索文字列が変質した: 期待={[raw]!r} 実際={parsed['parameters']!r} "
            f"cmd={res.shell_command!r}"
        )

    def test_b02b_multiple_parameters_keep_order_and_count(self, pioneer_env, run_pioneer):
        """B-02b 複数の検索文字列が順序と個数を保って渡ること"""
        params = ["p1", "p 2", "a;b", "$(id)", ""]
        pioneer_env.write_dialog(dialog(state_block(parameter=params)))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        parsed = parse_shell_command(res.shell_command)
        assert parsed["parameters"] == params

    def test_b03_no_command_injection_when_really_executed(self, pioneer_env, run_pioneer):
        """
        B-03 実際にシェルを起動しても、検索文字列に埋め込んだコマンドが実行されないこと

        subprocess.run をモックせず本物を通す（shell_returncode=None）。
        終了コードだけでは「一致しなかった」のか「注入されなかった」のかを
        区別できないため、canary ファイルが生まれないことで判定する。
        """
        canary = pioneer_env.root / "canary_created"
        injected = f"alpha;touch {canary}"

        pioneer_env.write_dialog(dialog(state_block(parameter=[injected])))
        res = run_pioneer(
            pioneer_env.params(),
            spawn_outputs=["alpha bravo\n"],
            shell_returncode=None,
        )

        assert not canary.exists(), (
            f"コマンドが注入され実行された: cmd={res.shell_command!r}"
        )

    def test_b03b_real_shell_hits_and_misses_correctly(self, pioneer_env, run_pioneer):
        """
        B-03b 実シェルまで通した AND 判定が正しいこと

        「引数が実際に渡っている」ことの最も直接的な確認。旧実装では
        検索シェルが起動していなかったため常に成功扱いになっていた。
        """
        pioneer_env.write_dialog(dialog(state_block(parameter=["alpha", "charlie"])))
        hit = run_pioneer(
            pioneer_env.params(),
            spawn_outputs=["alpha bravo\ncharlie\n"],
            shell_returncode=None,
        )
        assert hit.kind == "exit_json", hit.msg
        assert hit.log_contains("execute result OK"), hit.exec_log

        pioneer_env.write_dialog(dialog(state_block(parameter=["alpha", "zzz"])))
        miss = run_pioneer(
            pioneer_env.params(),
            spawn_outputs=["alpha bravo\ncharlie\n"],
            shell_returncode=None,
        )
        assert miss.kind == "fail_json", (
            "2個目の検索文字列がミスなのに成功扱いになっている"
            "（旧バグが再発している可能性）"
        )
        assert miss.log_contains("execute result NG"), miss.exec_log

    def test_b03c_stdout_file_path_is_quoted(self, pioneer_env, run_pioneer):
        """B-03c stdout_file のパスにスペースがあってもクォートされること"""
        target = pioneer_env.root / "out dir"
        target.mkdir()
        stdout_file = target / "std out.txt"

        pioneer_env.write_dialog(
            dialog(state_block(parameter=["hello"], stdout_file=str(stdout_file)))
        )
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        parsed = parse_shell_command(res.shell_command)
        assert parsed["stdout_file"] == str(stdout_file)

    def test_b03d_user_shell_path_is_quoted(self, pioneer_env, run_pioneer):
        """B-03d user shell のパスにスペースがあってもクォートされること"""
        target = pioneer_env.root / "shell dir"
        target.mkdir()
        user_shell = target / "my shell.sh"
        user_shell.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

        pioneer_env.write_dialog(
            dialog(state_block(shell=str(user_shell), parameter=["hello"]))
        )
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        parsed = parse_shell_command(res.shell_command)
        assert parsed["script"] == str(user_shell)


class TestParameterReset:
    """B-04 / B-05 / B-06 exec_list の要素をまたぐ parameter の扱い"""

    def test_b04_parameter_does_not_leak_to_next_element(self, pioneer_env, run_pioneer):
        """
        B-04 1要素目の parameter が、parameter を持たない2要素目に漏れないこと

        旧実装は parameter_cmd_list の初期化が
        「parameter キーを読んだ時」だけだったため、
        parameter を書いていない要素が前の要素の値で判定されていた。
        """
        pioneer_env.write_dialog(dialog(
            state_block(cmd="first", parameter=["leaked"]),
            state_block(cmd="second"),
        ))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["output\n"])

        assert res.kind == "exit_json", res.msg
        assert len(res.shell_commands) == 2, res.shell_commands

        first = parse_shell_command(res.shell_commands[0])
        second = parse_shell_command(res.shell_commands[1])

        assert first["parameters"] == ["leaked"]
        assert second["parameters"] == [], (
            f"1要素目の parameter が2要素目に漏れている: {second['parameters']!r}"
        )

    def test_b04b_parameter_is_replaced_not_appended(self, pioneer_env, run_pioneer):
        """B-04b 2要素目が自分の parameter を持つ場合、1要素目の値が残らないこと"""
        pioneer_env.write_dialog(dialog(
            state_block(cmd="first", parameter=["first_kw"]),
            state_block(cmd="second", parameter=["second_kw"]),
        ))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["output\n"])

        assert res.kind == "exit_json", res.msg
        second = parse_shell_command(res.shell_commands[1])
        assert second["parameters"] == ["second_kw"]

    def test_b05_no_parameter_at_all(self, pioneer_env, run_pioneer):
        """
        B-05 parameter を一度も書かない対話ファイルでも動くこと

        旧実装は parameter_cmd_list が未定義のままシェル起動処理に到達し
        NameError になっていた（try/except に拾われ
        'default shell execute error' で fail）。
        """
        pioneer_env.write_dialog(dialog(state_block(cmd="only_state")))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["output\n"])

        assert res.kind == "exit_json", res.msg
        assert not res.log_contains("execute error"), (
            f"NameError 由来のエラーで終了している: {res.exec_log}"
        )
        assert parse_shell_command(res.shell_command)["parameters"] == []

    def test_b06_log_parameter_is_also_reset(self, pioneer_env, run_pioneer):
        """
        B-06 ログ出力用の parameter_cmd も要素ごとにリセットされること

        実行ログの 'parameter(...)' に前の要素の値が混ざらないこと。
        """
        pioneer_env.write_dialog(dialog(
            state_block(cmd="first", parameter=["leaked"]),
            state_block(cmd="second"),
        ))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["output\n"])

        param_logs = [
            str(line) for line in res.exec_log
            if "default shell parameter(" in str(line)
        ]
        assert len(param_logs) == 2, param_logs
        assert "leaked" in param_logs[0]
        assert "leaked" not in param_logs[1], (
            f"ログ用 parameter_cmd がリセットされていない: {param_logs[1]!r}"
        )


class TestStdoutFileLifecycle:
    """B-07〜B-13 stdout_file と一時ファイルの後始末"""

    def test_b07_specified_stdout_file_is_kept_default_shell(self, pioneer_env, run_pioneer):
        """
        B-07 stdout_file 指定時、default shell 分岐でもファイルを消さないこと

        旧実装は default shell 分岐の最後で pass_rep_stdout_file を
        無条件に os.remove していたため、利用者が指定した結果ファイルが
        消えていた（データ消失）。今回の修正の中で最も影響が大きい。
        """
        stdout_file = pioneer_env.root / "keep_me.txt"

        pioneer_env.write_dialog(
            dialog(state_block(parameter=["hello"], stdout_file=str(stdout_file)))
        )
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        assert stdout_file.exists(), "指定した stdout_file が削除された"
        assert "hello world" in stdout_file.read_text(encoding="utf-8")

    def test_b08_specified_stdout_file_is_kept_user_shell(self, pioneer_env, run_pioneer):
        """B-08 stdout_file 指定時、user shell 分岐でもファイルを消さないこと"""
        user_shell = make_user_shell(pioneer_env)
        stdout_file = pioneer_env.root / "keep_me.txt"

        pioneer_env.write_dialog(dialog(state_block(
            shell=str(user_shell), parameter=["hello"], stdout_file=str(stdout_file)
        )))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        assert stdout_file.exists(), "指定した stdout_file が削除された"
        assert "hello world" in stdout_file.read_text(encoding="utf-8")

    def test_b09_temp_file_created_then_removed_default_shell(self, pioneer_env, run_pioneer):
        """
        B-09 stdout_file 未指定時、ITA が一時ファイルを作りシェル実行後に削除すること

        シェル実行中には存在し、main() 終了後には存在しないことを両方確認する。
        """
        observed = {}

        def during_shell(cmd):
            path = parse_shell_command(cmd)["stdout_file"]
            observed["path"] = path
            observed["exists_during"] = os.path.isfile(path)
            observed["content"] = (
                open(path, encoding="utf-8").read() if os.path.isfile(path) else None
            )

        pioneer_env.write_dialog(dialog(state_block(parameter=["hello"])))
        res = run_pioneer(
            pioneer_env.params(),
            spawn_outputs=["hello world\n"],
            shell_side_effect=during_shell,
        )

        assert res.kind == "exit_json", res.msg
        assert observed["path"].startswith(TMP_STDOUT_PREFIX), observed["path"]
        assert observed["exists_during"], "シェル実行時に一時ファイルが存在しない"
        assert "hello world" in observed["content"]
        assert not os.path.isfile(observed["path"]), "一時ファイルが残留した"

    def test_b10_temp_file_removed_user_shell(self, pioneer_env, run_pioneer):
        """
        B-10 user shell 分岐でも一時ファイルが削除されること

        旧実装は user shell 分岐に削除処理が無く、
        /tmp/.ita_pioneer_module_stdout.<pid> が残留していた。
        """
        user_shell = make_user_shell(pioneer_env)
        observed = {}

        def during_shell(cmd):
            observed["path"] = parse_shell_command(cmd)["stdout_file"]
            observed["exists_during"] = os.path.isfile(observed["path"])

        pioneer_env.write_dialog(
            dialog(state_block(shell=str(user_shell), parameter=["hello"]))
        )
        res = run_pioneer(
            pioneer_env.params(),
            spawn_outputs=["hello world\n"],
            shell_side_effect=during_shell,
        )

        assert res.kind == "exit_json", res.msg
        assert observed["path"].startswith(TMP_STDOUT_PREFIX)
        assert observed["exists_during"]
        assert not os.path.isfile(observed["path"]), (
            "user shell 分岐で一時ファイルが残留した"
        )

    def test_b11_temp_file_name_is_pid_based_and_reused(self, pioneer_env, run_pioneer):
        """
        B-11 一時ファイル名は pid 固定なので、exec_list の要素間で同じパスになること

        名前が固定である以上、要素ごとに作り直される。
        最後まで走り切ったあとに残っていないことを確認する。
        """
        pioneer_env.write_dialog(dialog(
            state_block(cmd="first", parameter=["one"]),
            state_block(cmd="second", parameter=["two"]),
        ))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["one two\n"])

        assert res.kind == "exit_json", res.msg
        paths = [parse_shell_command(c)["stdout_file"] for c in res.shell_commands]
        assert len(paths) == 2
        assert paths[0] == paths[1], f"pid 固定の想定が崩れている: {paths}"
        assert paths[0] == TMP_STDOUT_PREFIX + str(os.getpid())
        assert not os.path.isfile(paths[0]), "一時ファイルが残留した"

    def test_b11b_no_temp_file_left_in_tmp(self, pioneer_env, run_pioneer):
        """B-11b 実行前後で /tmp の一時ファイルが増えていないこと"""
        before = set(glob.glob(TMP_STDOUT_PREFIX + "*"))

        pioneer_env.write_dialog(dialog(state_block(parameter=["hello"])))
        run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        after = set(glob.glob(TMP_STDOUT_PREFIX + "*"))
        assert after - before == set(), f"一時ファイルが残った: {after - before}"

    def test_b11c_temp_file_used_after_stdout_file_element(self, pioneer_env, run_pioneer):
        """
        B-11c stdout_file 指定の要素の次に未指定の要素が来ても正しく切り替わること

        stdout_file が要素ごとにリセットされないと、1要素目の指定パスが
        2要素目に漏れ、しかも一時ファイル扱いで削除されてしまう。
        """
        kept = pioneer_env.root / "keep_me.txt"

        pioneer_env.write_dialog(dialog(
            state_block(cmd="first", parameter=["hello"], stdout_file=str(kept)),
            state_block(cmd="second", parameter=["hello"]),
        ))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        paths = [parse_shell_command(c)["stdout_file"] for c in res.shell_commands]
        assert paths[0] == str(kept)
        assert paths[1] == TMP_STDOUT_PREFIX + str(os.getpid())
        assert kept.exists(), "指定した stdout_file が2要素目の処理で削除された"
        assert not os.path.isfile(paths[1]), "一時ファイルが残留した"

    def test_b11d_temp_flag_reset_when_next_element_specifies(
        self, pioneer_env, run_pioneer
    ):
        """
        B-11d 一時ファイル使用の要素の次に stdout_file 指定の要素が来ても消さないこと

        stdout_file_tmp_flg が要素ごとに 0 に戻らないと、
        2要素目の指定ファイルが一時ファイル扱いで削除される。
        """
        kept = pioneer_env.root / "keep_me.txt"

        pioneer_env.write_dialog(dialog(
            state_block(cmd="first", parameter=["hello"]),
            state_block(cmd="second", parameter=["hello"], stdout_file=str(kept)),
        ))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        assert kept.exists(), "指定した stdout_file が一時ファイル扱いで削除された"

    def test_b12_temp_file_removed_when_shell_fails(self, pioneer_env, run_pioneer):
        """
        B-12 シェルが非0で終わっても一時ファイルは削除されること

        削除処理は returncode 判定より前に置かれている。
        exec_list 要素の ignore_errors 既定値は False なので fail で終わる。
        """
        observed = {}

        def during_shell(cmd):
            observed["path"] = parse_shell_command(cmd)["stdout_file"]

        pioneer_env.write_dialog(dialog(state_block(parameter=["hello"])))
        res = run_pioneer(
            pioneer_env.params(),
            spawn_outputs=["hello world\n"],
            shell_returncode=1,
            shell_side_effect=during_shell,
        )

        assert res.kind == "fail_json", res.msg
        assert res.log_contains("execute result NG"), res.exec_log
        assert not os.path.isfile(observed["path"]), "失敗時に一時ファイルが残留した"

    def test_b12b_specified_stdout_file_is_kept_when_shell_fails(
        self, pioneer_env, run_pioneer
    ):
        """B-12b シェルが非0で終わっても、指定された stdout_file は残ること"""
        stdout_file = pioneer_env.root / "keep_me.txt"

        pioneer_env.write_dialog(
            dialog(state_block(parameter=["hello"], stdout_file=str(stdout_file)))
        )
        res = run_pioneer(
            pioneer_env.params(), spawn_outputs=["hello world\n"], shell_returncode=1
        )

        assert res.kind == "fail_json", res.msg
        assert stdout_file.exists(), "失敗時に指定 stdout_file が削除された"

    def test_b13_temp_file_remains_on_exception(self, pioneer_env, run_pioneer):
        """
        B-13 シェル起動が例外になった場合、一時ファイルは残る（現状の挙動）

        削除処理は try/except の後ろにあり、except 節が private_fail_json() で
        抜けるため到達しない。既知の穴として現状を固定しておく。
        finally で消す方針（④）が決まったら期待値を反転させる。
        """
        observed = {}

        def boom(cmd):
            observed["path"] = parse_shell_command(cmd)["stdout_file"]
            raise OSError("シェル起動失敗をシミュレート")

        pioneer_env.write_dialog(dialog(state_block(parameter=["hello"])))
        res = run_pioneer(
            pioneer_env.params(),
            spawn_outputs=["hello world\n"],
            shell_side_effect=boom,
        )

        assert res.kind == "fail_json", res.msg
        assert res.log_contains("default shell execute error"), res.exec_log

        leaked = os.path.isfile(observed["path"])
        if leaked:
            os.remove(observed["path"])
        assert leaked, (
            "例外時に一時ファイルが削除されるようになった。"
            "仕様変更（④）なら期待値を更新すること"
        )


class TestUnknownKey:
    """B-14 未知キーの扱い"""

    def test_b14_unknown_state_key_reports_not_service(self, pioneer_env, run_pioneer):
        """
        B-14 state ブロックに未知キーがあると 'not service' で fail すること

        旧実装は未定義の private_output() を呼んで NameError になり、
        原因の分からないメッセージで終了していた。
        """
        pioneer_env.write_dialog(dialog(
            state_block(parameter=["hello"], extra=['unknown_key: "x"'])
        ))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "fail_json"
        assert "command(state->unknown_key) not service" in res.msg, res.msg
        assert res.shell_commands == [], "エラー時にシェルを起動している"

        private_log = pioneer_env.private_log.read_text(encoding="utf-8")
        assert "command(state->unknown_key) not service" in private_log, (
            "private_log_output() へのログ出力が行われていない"
            "（private_output の修正が効いていない）"
        )


class TestVaultVariable:
    """B-15 / B-16 暗号化変数（Vault）の扱い"""

    def test_b15_vault_value_is_decoded_then_quoted(self, pioneer_env, run_pioneer):
        """
        B-15 検索文字列の Vault 変数は復号後にクォートされること

        復号値にシェルのメタ文字が含まれていても注入されないよう、
        password_replace（復号）→ shlex.quote の順であること。
        """
        secret = "sec;ret $(id)"
        pioneer_env.write_vault(f"VAR_PASS: {encode_vault_value(secret)}\n")

        pioneer_env.write_dialog(dialog(state_block(parameter=["<< VAR_PASS >>"])))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        parsed = parse_shell_command(res.shell_command)
        assert parsed["parameters"] == [secret], (
            f"Vault 変数の復号／クォートが崩れている: cmd={res.shell_command!r}"
        )

    def test_b15b_vault_value_really_not_injected(self, pioneer_env, run_pioneer):
        """B-15b 復号値に埋め込んだコマンドが、実シェル起動でも実行されないこと"""
        canary = pioneer_env.root / "canary_created"
        secret = f"alpha;touch {canary}"
        pioneer_env.write_vault(f"VAR_PASS: {encode_vault_value(secret)}\n")

        pioneer_env.write_dialog(dialog(state_block(parameter=["<< VAR_PASS >>"])))
        res = run_pioneer(
            pioneer_env.params(),
            spawn_outputs=["alpha bravo\n"],
            shell_returncode=None,
        )

        assert not canary.exists(), (
            f"Vault 復号値経由でコマンドが注入された: cmd={res.shell_command!r}"
        )

    def test_b16_vault_value_is_masked_in_log(self, pioneer_env, run_pioneer):
        """B-16 実行ログとプライベートログに復号値が出ず、マスクされること"""
        secret = "topsecret"
        pioneer_env.write_vault(f"VAR_PASS: {encode_vault_value(secret)}\n")

        pioneer_env.write_dialog(dialog(state_block(parameter=["<< VAR_PASS >>"])))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        joined = "\n".join(str(line) for line in res.exec_log)
        assert secret not in joined, "実行ログに復号値が出力されている"
        assert "********" in joined, "マスク文字列が実行ログに出ていない"

        private_log = pioneer_env.private_log.read_text(encoding="utf-8")
        assert secret not in private_log, "プライベートログに復号値が出力されている"


class TestExitConditions:
    """success_exit / ignore_errors とドライラン"""

    def test_success_exit_yes_stops_dialog(self, pioneer_env, run_pioneer):
        """success_exit: yes でヒットした場合、その要素で正常終了すること"""
        pioneer_env.write_dialog(dialog(
            state_block(cmd="first", parameter=["hello"], success_exit="yes"),
            state_block(cmd="second", parameter=["hello"]),
        ))
        res = run_pioneer(pioneer_env.params(), spawn_outputs=["hello world\n"])

        assert res.kind == "exit_json", res.msg
        assert "success_exit: yes" in res.msg, res.msg
        assert len(res.shell_commands) == 1, (
            "success_exit: yes なのに後続の要素が実行されている"
        )

    def test_ignore_errors_yes_continues(self, pioneer_env, run_pioneer):
        """ignore_errors: yes ならシェルが非0でも後続の要素が続くこと"""
        pioneer_env.write_dialog(dialog(
            state_block(cmd="first", parameter=["zzz"], ignore_errors="yes"),
            state_block(cmd="second", parameter=["zzz"], ignore_errors="yes"),
        ))
        res = run_pioneer(
            pioneer_env.params(), spawn_outputs=["hello world\n"], shell_returncode=1
        )

        assert res.kind == "exit_json", res.msg
        assert res.log_contains("ignore_errors: yes"), res.exec_log
        assert len(res.shell_commands) == 2

    def test_ignore_errors_default_fails_immediately(self, pioneer_env, run_pioneer):
        """ignore_errors 省略時（要素ごとの既定は False）は非0で即 fail すること"""
        pioneer_env.write_dialog(dialog(
            state_block(cmd="first", parameter=["zzz"]),
            state_block(cmd="second", parameter=["zzz"]),
        ))
        res = run_pioneer(
            pioneer_env.params(), spawn_outputs=["hello world\n"], shell_returncode=1
        )

        assert res.kind == "fail_json"
        assert "ignore_errors: no" in res.msg, res.msg
        assert len(res.shell_commands) == 1

    def test_ignore_errors_no_fails_immediately(self, pioneer_env, run_pioneer):
        """ignore_errors: no ならシェルが非0の時点で fail すること"""
        pioneer_env.write_dialog(dialog(
            state_block(cmd="first", parameter=["zzz"], ignore_errors="no"),
            state_block(cmd="second", parameter=["zzz"]),
        ))
        res = run_pioneer(
            pioneer_env.params(), spawn_outputs=["hello world\n"], shell_returncode=1
        )

        assert res.kind == "fail_json"
        assert "ignore_errors: no" in res.msg, res.msg
        assert len(res.shell_commands) == 1

    def test_check_mode_does_not_invoke_shell(self, pioneer_env, run_pioneer):
        """ドライランでは接続確認だけで終わり、検索シェルを起動しないこと"""
        pioneer_env.write_dialog(dialog(state_block(parameter=["hello"])))
        res = run_pioneer(
            pioneer_env.params(), spawn_outputs=["hello world\n"], check_mode=True
        )

        assert res.kind == "exit_json", res.msg
        assert "check mode" in res.msg, res.msg
        assert res.shell_commands == [], "ドライランでシェルを起動している"
