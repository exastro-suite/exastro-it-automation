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
C: pioneer_module.py の結合テスト（#3089）

pexpect も subprocess もモックせず、実ホストへ SSH 接続して
実際の標準出力を実際の検索シェルで検査する。
A（シェル単体）と B（モジュール単体）で担保できない
「モジュール → シェル → 判定」の一連の流れを確認する。

実行方法:
    ITA_TEST_SSH_HOST=<接続先> \
    ITA_TEST_SSH_USER=<ユーザー> \
    ITA_TEST_SSH_PASS=<パスワード> \
    python3 -m pytest <このファイル>

または pytest.ini（.gitignore 対象）の env に同じ変数を記載する
（記載例は pytest.ini.sample を参照）。
接続情報が未設定の場合はすべてスキップされる。
認証情報はリポジトリ内のファイルには一切置かない。
テスト中に生成する対話ファイル・暗号化変数ファイルは
すべて pytest の tmp_path 配下（リポジトリ外）に作る。
"""
import concurrent.futures
import glob
import multiprocessing
import os

import pytest

from .conftest import (
    TMP_STDOUT_PREFIX,
    command_block,
    dialog,
    encode_vault_value,
    parse_shell_command,
    run_pioneer_real,
    state_block,
)

pytestmark = pytest.mark.integration

# ----------------------------------------------------------------------
# 実ホストのプロンプト
# ----------------------------------------------------------------------
# ログイン後のシェルプロンプト。`$ ` で終わる一般的な形を想定する
SHELL_PROMPT = r"\$ "

# ログイン（パスワード入力）用の prompt。
# command ブロックは prompt を「送信前」と「送信後」の2回 expect するため、
# パスワード入力プロンプトとログイン後のシェルプロンプトの
# 両方に一致する正規表現を指定する必要がある。
LOGIN_PROMPT = r"[Pp]assword:|" + SHELL_PROMPT

# ----------------------------------------------------------------------
# リモートで実行するコマンド
# ----------------------------------------------------------------------
# 検索対象になるのは「コマンドの標準出力」だが、疑似端末のエコーや
# プロンプト文字列も p.before に混ざりうる。
# そのため「コマンド文字列そのものには現れない語」が出力に出るよう、
# tr で置換してから出力する。
#
#   REMOTE_CMD の出力:
#       YY_one
#       YY_two
REMOTE_CMD = r"echo XX_one,XX_two | tr 'X,' 'Y\n'"
HIT_1 = "YY_one"
HIT_2 = "YY_two"
# 出力にもプロンプトにも現れない語
MISS = "ZZ_missing"


@pytest.fixture
def c_env(pioneer_env, ssh_target):
    """
    実ホストへ接続する設定を pioneer_env に上書きしたもの。

    ログインパスワードは暗号化変数（Vault）として渡す。
    - 平文が対話ファイルに残らない
    - 実行ログでは password_hide によりマスクされる
    という ITA 本来の経路を通せるため。
    """
    pioneer_env.host_name = ssh_target["host"]
    pioneer_env.ssh_user = ssh_target["user"]
    pioneer_env.write_vault(
        f"VAR_LOGIN_PASS: {encode_vault_value(ssh_target['password'])}\n"
    )
    return pioneer_env


def c_params(env, **override):
    """c_env から module.params 相当を組み立てる"""
    base = {"username": env.ssh_user}
    base.update(override)
    return env.params(**base)


def login(prompt=LOGIN_PROMPT):
    """ログイン（パスワード入力）の command ブロック"""
    return command_block(cmd="<< VAR_LOGIN_PASS >>", prompt=prompt)


def remote_state(**kwargs):
    """リモートでコマンドを実行して標準出力を検査する state ブロック"""
    kwargs.setdefault("cmd", REMOTE_CMD)
    kwargs.setdefault("prompt", SHELL_PROMPT)
    return state_block(**kwargs)


def c_dialog(*blocks, timeout=15):
    """ログイン手順を先頭に付けた対話ファイル"""
    return dialog(login(), *blocks, timeout=timeout)


def make_argv_logger(env, out_path, name="argv_logger.sh"):
    """
    user shell 用のスクリプト。受け取った引数を out_path に書き出す。

    ITA から見れば「利用者が用意した任意のシェル」に相当する。
    """
    path = env.root / name
    path.write_text(
        "#!/bin/sh\n"
        "{\n"
        '  echo "count=$#"\n'
        '  for a in "$@"; do echo "arg=[$a]"; done\n'
        f'}} > {out_path}\n'
        "exit 0\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


class TestDefaultShell:
    """C-01〜C-05 デフォルト検索シェルでの判定"""

    def test_c01_single_keyword_hit(self, c_env, run_pioneer_integration):
        """C-01 検索文字列1個がヒットしたら正常終了すること"""
        c_env.write_dialog(c_dialog(remote_state(parameter=[HIT_1])))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        assert res.log_contains("default shell parameter("), res.exec_log
        assert res.log_contains("execute result OK"), res.exec_log

    def test_c02_single_keyword_miss(self, c_env, run_pioneer_integration):
        """C-02 検索文字列1個がミスしたら異常終了すること"""
        c_env.write_dialog(c_dialog(remote_state(parameter=[MISS])))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "fail_json", res.msg
        assert res.log_contains("execute result NG"), res.exec_log

    def test_c03_multiple_keywords_all_hit(self, c_env, run_pioneer_integration):
        """
        C-03 検索文字列が複数で全てヒットしたら正常終了すること

        HIT_1 と HIT_2 は別の行に出力される。
        AND の判定単位はファイル全体（同一行ではない）という確定仕様の確認。
        """
        c_env.write_dialog(c_dialog(remote_state(parameter=[HIT_1, HIT_2])))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        assert res.log_contains("execute result OK"), res.exec_log

        parsed = parse_shell_command(res.shell_command)
        assert parsed["parameters"] == [HIT_1, HIT_2]

    def test_c04_multiple_keywords_second_miss(self, c_env, run_pioneer_integration):
        """
        C-04 2個目の検索文字列がミスなら異常終了すること

        今回の修正で最も重要な結合確認。
        旧実装は検索シェルを起動できておらず、さらに2個目以降の検索文字列を
        渡せていなかったため、このケースが誤って成功扱いになっていた。
        """
        c_env.write_dialog(c_dialog(remote_state(parameter=[HIT_1, MISS])))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "fail_json", (
            "2個目の検索文字列がミスなのに成功扱いになっている（旧バグの再発）"
        )
        assert res.log_contains("execute result NG"), res.exec_log

    def test_c05_no_parameter(self, c_env, run_pioneer_integration):
        """
        C-05 parameter を書かなくても Python 例外にならないこと

        旧実装は parameter_cmd_list が未定義で NameError になっていた。
        現在は検索文字列0個として検索シェルが起動し、シェル側の
        「検索文字列が指定されていない場合は異常終了」で非0が返る。
        ここでは ignore_errors: yes にして対話ファイルを完走させ、
        「例外ではなくシェルの判定結果として NG になる」ことを確認する。
        """
        c_env.write_dialog(c_dialog(remote_state(ignore_errors="yes")))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        assert not res.log_contains("execute error"), (
            f"Python 例外が発生している（NameError の可能性）: {res.exec_log}"
        )
        assert res.log_contains("execute result NG"), res.exec_log
        assert parse_shell_command(res.shell_command)["parameters"] == []


class TestUserShell:
    """C-06 / C-07 利用者が指定したシェルへの引数の渡り方"""

    def test_c06_user_shell_receives_all_arguments(self, c_env, run_pioneer_integration):
        """
        C-06 user shell が $1=stdout_file, $2以降=検索文字列 を受け取ること

        シェル自身に引数を書き出させて確認する。
        旧実装ではシェルが起動しないため、このファイルが作られなかった。
        """
        argv_out = c_env.root / "argv.txt"
        user_shell = make_argv_logger(c_env, argv_out)

        c_env.write_dialog(c_dialog(remote_state(
            shell=str(user_shell), parameter=[HIT_1, HIT_2]
        )))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        assert argv_out.exists(), "user shell が起動していない"

        lines = argv_out.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "count=3", lines
        assert lines[1].startswith("arg=[") and lines[1].endswith("]")
        stdout_file_arg = lines[1][len("arg=["):-1]
        assert stdout_file_arg.startswith(TMP_STDOUT_PREFIX), stdout_file_arg
        assert lines[2] == f"arg=[{HIT_1}]", lines
        assert lines[3] == f"arg=[{HIT_2}]", lines

    def test_c07_user_shell_without_parameter(self, c_env, run_pioneer_integration):
        """C-07 parameter を書かない場合、user shell には $1 だけが渡ること"""
        argv_out = c_env.root / "argv.txt"
        user_shell = make_argv_logger(c_env, argv_out)

        c_env.write_dialog(c_dialog(remote_state(shell=str(user_shell))))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        lines = argv_out.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "count=1", lines


class TestStdoutFile:
    """C-08〜C-10 / C-13 stdout_file の扱い"""

    def test_c08_specified_stdout_file_is_kept_default_shell(
        self, c_env, run_pioneer_integration
    ):
        """
        C-08 stdout_file 指定時、default shell でもファイルが残り中身が入っていること

        旧実装は default shell 分岐で無条件に削除していた（データ消失）。
        """
        stdout_file = c_env.root / "result.txt"

        c_env.write_dialog(c_dialog(remote_state(
            parameter=[HIT_1], stdout_file=str(stdout_file)
        )))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        assert stdout_file.exists(), "指定した stdout_file が削除された"
        content = stdout_file.read_text(encoding="utf-8")
        assert HIT_1 in content, f"標準出力が保存されていない: {content!r}"
        assert HIT_2 in content, f"標準出力が保存されていない: {content!r}"

    def test_c09_specified_stdout_file_is_kept_user_shell(
        self, c_env, run_pioneer_integration
    ):
        """C-09 stdout_file 指定時、user shell でもファイルが残ること"""
        stdout_file = c_env.root / "result.txt"
        argv_out = c_env.root / "argv.txt"
        user_shell = make_argv_logger(c_env, argv_out)

        c_env.write_dialog(c_dialog(remote_state(
            shell=str(user_shell), parameter=[HIT_1], stdout_file=str(stdout_file)
        )))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        assert stdout_file.exists(), "指定した stdout_file が削除された"
        assert HIT_1 in stdout_file.read_text(encoding="utf-8")

        # user shell の $1 は指定した stdout_file になる
        lines = argv_out.read_text(encoding="utf-8").splitlines()
        assert lines[1] == f"arg=[{stdout_file}]", lines

    def test_c10_temp_file_not_left_behind(self, c_env, run_pioneer_integration):
        """
        C-10 stdout_file 未指定時、一時ファイルが残らないこと

        default shell / user shell の両分岐を1つの対話ファイルで通す。
        旧実装は user shell 分岐に削除処理が無く残留していた。
        """
        before = set(glob.glob(TMP_STDOUT_PREFIX + "*"))
        argv_out = c_env.root / "argv.txt"
        user_shell = make_argv_logger(c_env, argv_out)

        c_env.write_dialog(c_dialog(
            remote_state(parameter=[HIT_1]),
            remote_state(shell=str(user_shell), parameter=[HIT_1]),
        ))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        assert len(res.shell_commands) == 2, res.shell_commands
        for cmd in res.shell_commands:
            assert parse_shell_command(cmd)["stdout_file"].startswith(TMP_STDOUT_PREFIX)

        after = set(glob.glob(TMP_STDOUT_PREFIX + "*"))
        assert after - before == set(), f"一時ファイルが残った: {after - before}"

    def test_c13_stdout_file_with_special_characters(self, c_env, run_pioneer_integration):
        """C-13 stdout_file のパスにスペースや日本語が含まれても動作すること"""
        target = c_env.root / "出力 ディレクトリ"
        target.mkdir()
        stdout_file = target / "結果 ファイル.txt"

        c_env.write_dialog(c_dialog(remote_state(
            parameter=[HIT_1], stdout_file=str(stdout_file)
        )))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        assert stdout_file.exists(), "特殊文字を含むパスに出力できていない"
        assert HIT_1 in stdout_file.read_text(encoding="utf-8")


class TestMultipleElements:
    """C-11 exec_list の要素をまたぐ状態の持ち越し"""

    def test_c11_parameter_does_not_leak_to_next_element(
        self, c_env, run_pioneer_integration
    ):
        """
        C-11 1要素目の parameter が2要素目に漏れないこと

        旧実装では2要素目が1要素目の検索文字列で判定され、
        本来 NG になるべきところが OK になっていた。
        2要素目は検索文字列0個なので NG が正しい。
        """
        c_env.write_dialog(c_dialog(
            remote_state(parameter=[HIT_1], ignore_errors="yes"),
            remote_state(ignore_errors="yes"),
        ))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        assert len(res.shell_commands) == 2, res.shell_commands

        first = parse_shell_command(res.shell_commands[0])
        second = parse_shell_command(res.shell_commands[1])
        assert first["parameters"] == [HIT_1]
        assert second["parameters"] == [], (
            f"1要素目の検索文字列が2要素目に漏れている: {second['parameters']!r}"
        )

        results = [
            line for line in (str(x) for x in res.exec_log)
            if "execute result" in line
        ]
        assert len(results) == 2, results
        assert "OK" in results[0], results
        assert "NG" in results[1], results


class TestSecurity:
    """C-12 コマンド注入"""

    def test_c12_no_command_injection(self, c_env, run_pioneer_integration):
        """
        C-12 検索文字列に埋め込んだコマンドが実行されないこと

        検索シェルは shell=True で起動されるため、
        検索文字列が shlex.quote されていないと注入が成立する（#1414）。
        """
        canary = c_env.root / "ita_canary"
        injected = f"{HIT_1};touch {canary}"

        c_env.write_dialog(c_dialog(remote_state(parameter=[injected])))
        res = run_pioneer_integration(c_params(c_env))

        assert not canary.exists(), (
            f"コマンドが注入され実行された: cmd={res.shell_command!r}"
        )
        # 埋め込んだ文字列そのものは出力に無いので不一致（=NG）になる
        assert res.kind == "fail_json", res.msg

    def test_c12b_login_password_is_masked_in_log(self, c_env, run_pioneer_integration, ssh_target):
        """ログインパスワードが実行ログ・プライベートログに平文で出ないこと"""
        c_env.write_dialog(c_dialog(remote_state(parameter=[HIT_1])))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg

        joined = "\n".join(str(line) for line in res.exec_log)
        assert ssh_target["password"] not in joined, "実行ログにパスワードが出ている"

        private_log = c_env.private_log.read_text(encoding="utf-8")
        assert ssh_target["password"] not in private_log, (
            "プライベートログにパスワードが出ている"
        )


class TestKeywordEdgeCases:
    """C-14 / C-15 検索文字列の境界ケース"""

    def test_c14_keyword_starting_with_hyphen(self, c_env, run_pioneer_integration):
        """
        C-14 ハイフン始まりの検索文字列が grep のオプションとして解釈されないこと

        検索シェル側の `grep -c -- "${ARG}"` の `--` が効いていることの確認。
        単に一致しないので NG になる。
        """
        c_env.write_dialog(c_dialog(remote_state(parameter=["-v"])))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "fail_json", res.msg
        assert res.log_contains("execute result NG"), res.exec_log
        assert parse_shell_command(res.shell_command)["parameters"] == ["-v"]

    def test_c15_empty_keyword_currently_succeeds(self, c_env, run_pioneer_integration):
        """
        C-15 空文字列の検索文字列 -> 現状は成功判定（仕様未確定）

        対話ファイルに `- ""` と書くと ITA の書式チェックを通過して
        ここまで到達する。`grep -c -- "" <file>` は全行にマッチするため
        「検索できた」と判定される。
        エラーにする方針が決まったら期待値を反転させる。
        """
        c_env.write_dialog(c_dialog(remote_state(parameter=[""])))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", (
            f"空文字列の扱いが変わった。仕様変更なら期待値を更新すること: {res.msg}"
        )
        assert parse_shell_command(res.shell_command)["parameters"] == [""]


class TestExitConditions:
    """C-16〜C-19 終了条件とドライラン"""

    def test_c16_success_exit_yes_stops_dialog(self, c_env, run_pioneer_integration):
        """C-16 success_exit: yes でヒットしたらその時点で正常終了すること"""
        c_env.write_dialog(c_dialog(
            remote_state(parameter=[HIT_1], success_exit="yes"),
            remote_state(parameter=[HIT_1]),
        ))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        assert "success_exit: yes" in res.msg, res.msg
        assert len(res.shell_commands) == 1, "後続の要素が実行されている"

    def test_c17_ignore_errors_yes_continues(self, c_env, run_pioneer_integration):
        """C-17 ignore_errors: yes ならミスでも後続の要素が続くこと"""
        c_env.write_dialog(c_dialog(
            remote_state(parameter=[MISS], ignore_errors="yes"),
            remote_state(parameter=[HIT_1], ignore_errors="yes"),
        ))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "exit_json", res.msg
        assert len(res.shell_commands) == 2
        assert res.log_contains("ignore_errors: yes"), res.exec_log

    def test_c18_ignore_errors_no_fails_immediately(self, c_env, run_pioneer_integration):
        """C-18 ignore_errors: no ならミスの時点で異常終了すること"""
        c_env.write_dialog(c_dialog(
            remote_state(parameter=[MISS], ignore_errors="no"),
            remote_state(parameter=[HIT_1]),
        ))
        res = run_pioneer_integration(c_params(c_env))

        assert res.kind == "fail_json", res.msg
        assert "ignore_errors: no" in res.msg, res.msg
        assert len(res.shell_commands) == 1, "後続の要素が実行されている"

    def test_c19_check_mode_connects_only(self, c_env, run_pioneer_integration):
        """
        C-19 ドライランでは接続だけ確認して終了し、検索シェルを起動しないこと
        """
        c_env.write_dialog(c_dialog(remote_state(parameter=[HIT_1])))
        res = run_pioneer_integration(c_params(c_env), check_mode=True)

        assert res.kind == "exit_json", res.msg
        assert "check mode" in res.msg, res.msg
        assert res.shell_commands == [], "ドライランで検索シェルを起動している"


# ----------------------------------------------------------------------
# C-20 複数ホスト同時実行
# ----------------------------------------------------------------------
def _concurrent_worker(params):
    """
    子プロセスで main() を1回駆動する（C-20 用）。

    ITA 本体は host ごとにプロセスが分かれるため、一時ファイル名に
    os.getpid() を使う実装でも衝突しない、というのが前提になっている。
    その前提を実際に別プロセスで確認する。
    ProcessPoolExecutor から呼ぶのでモジュールトップレベルに置く。
    """
    res = run_pioneer_real(params)
    return {
        "pid": os.getpid(),
        "kind": res.kind,
        "msg": res.msg,
        "stdout_files": [
            parse_shell_command(cmd)["stdout_file"] for cmd in res.shell_commands
        ],
    }


class TestConcurrency:
    """C-20 複数ホスト（複数プロセス）同時実行"""

    def test_c20_temp_file_does_not_collide_between_processes(
        self, c_env, run_pioneer_integration
    ):
        """
        C-20 同時に複数プロセスで実行しても一時ファイルが衝突・残留しないこと

        一時ファイル名は /tmp/.ita_pioneer_module_stdout.<pid> なので、
        プロセスが分かれていれば別名になる。
        """
        before = set(glob.glob(TMP_STDOUT_PREFIX + "*"))

        c_env.write_dialog(c_dialog(remote_state(parameter=[HIT_1])))
        params = c_params(c_env)

        ctx = multiprocessing.get_context("fork")
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=2, mp_context=ctx
        ) as pool:
            results = list(pool.map(_concurrent_worker, [params, params]))

        for r in results:
            assert r["kind"] == "exit_json", r
            assert r["stdout_files"] == [TMP_STDOUT_PREFIX + str(r["pid"])], r

        assert results[0]["pid"] != results[1]["pid"], "プロセスが分かれていない"
        assert results[0]["stdout_files"] != results[1]["stdout_files"], (
            "別プロセスなのに一時ファイル名が同じになっている"
        )

        after = set(glob.glob(TMP_STDOUT_PREFIX + "*"))
        assert after - before == set(), f"一時ファイルが残った: {after - before}"
