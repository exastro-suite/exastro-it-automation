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
#3089 pioneer_module.py / ky_pionner_grep_side_Ansible.sh のテスト共通フィクスチャ

テスト対象は common_libs/ansible_driver/shells/ 配下の2ファイル。

  A: ky_pionner_grep_side_Ansible.sh の単体テスト
     -> run_grep_shell フィクスチャでシェルを直接叩く

  B: pioneer_module.py の単体テスト
     -> pexpect / subprocess を差し替えて main() を丸ごと駆動する
        (pioneer_module.py はロジックが全て main() 内にあり、
         かつ末尾で if __name__ ガード無しに main() を呼ぶため、
         importlib でロードすることが即ち実行になる)

  C: 実ホストへの結合テスト
     -> 認証情報は環境変数から読む。リポジトリには置かない。
        ITA_TEST_SSH_HOST / ITA_TEST_SSH_USER / ITA_TEST_SSH_PASS
"""
import base64
import codecs
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import types
from pathlib import Path

import pytest


def pytest_configure(config):
    """
    integration マーカーを登録する。

    pytest.ini は .gitignore 対象（pytest.ini.sample から生成される）なので、
    テストと一緒に配布されるこちらで登録する。
    実ホストへ接続する C のテストだけを外したい場合は
        python3 -m pytest -m "not integration"
    """
    config.addinivalue_line(
        "markers", "integration: 実ホストへ SSH 接続する結合テスト（C）"
    )


# テスト対象ファイル
SHELLS_DIR = Path("/workspace/exastro-it-automation-dev/ita_root/common_libs/ansible_driver/shells")
GREP_SHELL = SHELLS_DIR / "ky_pionner_grep_side_Ansible.sh"
PIONEER_MODULE = SHELLS_DIR / "pioneer_module.py"

# pioneer_module.py が stdout_file 未指定時に作る一時ファイルの接頭辞
TMP_STDOUT_PREFIX = "/tmp/.ita_pioneer_module_stdout."

# ky_pionner_grep_side_Ansible.sh が作る stderr 退避ファイルの接頭辞
TMP_STDERR_PREFIX = "/tmp/ita_stderr."


# ======================================================================
# A: シェル単体テスト用
# ======================================================================
@pytest.fixture(scope="session")
def grep_shell():
    """検索シェルのパス。存在確認も兼ねる"""
    assert GREP_SHELL.is_file(), f"テスト対象が見つからない: {GREP_SHELL}"
    return GREP_SHELL


@pytest.fixture
def run_grep_shell(grep_shell, tmp_path):
    """
    検索シェルを sh で実行する。

    ITA 本体は subprocess で "sh <script> ..." と起動するため、
    shebang(#!/bin/bash) ではなく sh 経由で叩く形に合わせている。

    cwd は tmp_path 固定。カレントに副作用ファイル(`1` など)が
    生まれていないことを検証したいため。
    """
    def _run(*args, cwd=None, shell_bin="sh"):
        return subprocess.run(
            [shell_bin, str(grep_shell), *[str(a) for a in args]],
            cwd=str(cwd or tmp_path),
            capture_output=True,
            text=True,
            timeout=30,
        )
    return _run


@pytest.fixture
def grep_fixture_dir(tmp_path):
    """
    A のテストで共用する検索対象ファイル群。

      f.txt      : alpha bravo / charlie   (2行)
      empty.txt  : 空ファイル
      adir       : ディレクトリ
      sp ace.txt : ファイル名にスペース
      日本語.txt : ファイル名に日本語
    """
    (tmp_path / "f.txt").write_text("alpha bravo\ncharlie\n", encoding="utf-8")
    (tmp_path / "empty.txt").write_text("", encoding="utf-8")
    (tmp_path / "adir").mkdir()
    (tmp_path / "sp ace.txt").write_text("alpha\n", encoding="utf-8")
    (tmp_path / "日本語.txt").write_text("alpha\n", encoding="utf-8")
    return tmp_path


# ======================================================================
# B / C 共用: 対話ファイル(dialog file)の組み立て
# ======================================================================
def y(value):
    """
    Python の文字列を YAML のダブルクォートスカラーとして書き出す。

    JSON の文字列表現は YAML のダブルクォートスカラーとして解釈できるため、
    エスケープ処理を json.dumps に任せる。
    """
    return json.dumps(value, ensure_ascii=False)


# 対話ファイルの prompt に使う既定値。expect_prompt() が正規表現として
# 扱うので `$` はエスケープしておく。
DEFAULT_PROMPT = "prompt\\$ "


def state_block(*, cmd="echo hello", prompt=DEFAULT_PROMPT, parameter=None,
                shell=None, stdout_file=None, success_exit=None,
                ignore_errors=None, extra=None):
    """
    state ブロック1個分の YAML を組み立てる。

    state ブロックは「コマンド実行 → 標準出力を検索シェルで検査」を行う。
    parameter / cmd / shell / stdout_file は素の Python 文字列で渡す。
    success_exit / ignore_errors は YAML のトークン（"yes" / "no"）で渡す。
    """
    lines = [f"  - state: {y(cmd)}", f"    prompt: {y(prompt)}"]
    if parameter is not None:
        lines.append("    parameter:")
        lines.extend(f"      - {y(p)}" for p in parameter)
    if shell is not None:
        lines.append(f"    shell: {y(shell)}")
    if stdout_file is not None:
        lines.append(f"    stdout_file: {y(stdout_file)}")
    if success_exit is not None:
        lines.append(f"    success_exit: {success_exit}")
    if ignore_errors is not None:
        lines.append(f"    ignore_errors: {ignore_errors}")
    if extra:
        lines.extend(f"    {e}" for e in extra)
    return "\n".join(lines) + "\n"


def command_block(*, cmd, prompt=DEFAULT_PROMPT):
    """
    command ブロック1個分の YAML を組み立てる。

    command ブロックは検索シェルを起動しない。ログイン時のパスワード入力など、
    「送るだけ」の手順に使う。
    """
    return f"  - command: {y(cmd)}\n    prompt: {y(prompt)}\n"


def dialog(*blocks, timeout=60):
    """conf ヘッダ付きの対話ファイル全体を組み立てる"""
    return f"conf:\n  timeout: {timeout}\nexec_list:\n" + "".join(blocks)


def parse_shell_command(cmd):
    """
    検索シェル起動コマンド(def_shell_cmd)の文字列を shlex で分解する。

    "sh <script> <stdout_file> <検索文字列...>" の形なので、
    ["sh", script, stdout_file, *parameters] に分かれる。
    shlex で元の値に戻せること自体が「クォートが効いている」ことの確認になる。
    """
    parts = shlex.split(cmd)
    assert parts[0] == "sh", f"想定外のコマンド形式: {cmd!r}"
    return {
        "script": parts[1],
        "stdout_file": parts[2],
        "parameters": parts[3:],
    }


# ======================================================================
# B / C: pioneer_module.py を駆動するための足場
# ======================================================================
def encode_vault_value(plain):
    """
    暗号化変数ファイル（encode_column_encode_value_file）に書く形式に変換する。

    pioneer_module.py 側のデコードは
        base64.b64decode(codecs.encode(value, "rot-13"))
    なので、その逆（base64 化してから rot13）をかける。
    """
    b64 = base64.b64encode(plain.encode("utf-8")).decode("ascii")
    return codecs.encode(b64, "rot-13")


class StubModuleExit(Exception):
    """
    スタブ AnsibleModule の exit_json / fail_json が投げる例外。

    本物の AnsibleModule は sys.exit() するが、テストからは
    「どちらで終わったか」と戻り値を取りたいので例外で受ける。
    """

    def __init__(self, kind, kwargs):
        super().__init__(f"{kind}: {kwargs.get('msg', '')}")
        self.kind = kind          # 'exit_json' | 'fail_json'
        self.kwargs = kwargs


def _make_ansible_stub(params, check_mode):
    """
    pioneer_module.py の `from ansible.module_utils.basic import *` を
    満たす最小のスタブモジュール群を組み立てる。

    pioneer_module.py が AnsibleModule から使うのは
    params / check_mode / exit_json / fail_json のみ。
    """
    class StubAnsibleModule:
        def __init__(self, argument_spec=None, supports_check_mode=False, **kwargs):
            self.argument_spec = argument_spec or {}
            self.supports_check_mode = supports_check_mode
            self.params = dict(params)
            self.check_mode = check_mode

        def exit_json(self, **kwargs):
            raise StubModuleExit("exit_json", kwargs)

        def fail_json(self, **kwargs):
            raise StubModuleExit("fail_json", kwargs)

    basic = types.ModuleType("ansible.module_utils.basic")
    basic.AnsibleModule = StubAnsibleModule

    module_utils = types.ModuleType("ansible.module_utils")
    module_utils.basic = basic

    ansible = types.ModuleType("ansible")
    ansible.module_utils = module_utils

    return {
        "ansible": ansible,
        "ansible.module_utils": module_utils,
        "ansible.module_utils.basic": basic,
    }


class _SysModulesPatch:
    """sys.modules を一時的に差し替える。実 ansible が入っていても上書きする"""

    def __init__(self, entries):
        self._entries = entries
        self._saved = {}

    def __enter__(self):
        for name, mod in self._entries.items():
            self._saved[name] = sys.modules.get(name, None)
            sys.modules[name] = mod
        return self

    def __exit__(self, *exc):
        for name, old in self._saved.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old
        return False


class PioneerResult:
    """pioneer_module.main() を1回走らせた結果"""

    def __init__(self, kind, kwargs, module, shell_commands):
        self.kind = kind                    # 'exit_json' | 'fail_json'
        self.kwargs = kwargs                # exit_json/fail_json に渡された内容
        self.module = module                # ロード済み pioneer_module
        self.shell_commands = shell_commands  # subprocess.run に渡された文字列の履歴

    @property
    def msg(self):
        return self.kwargs.get("msg", "")

    @property
    def exec_log(self):
        return self.kwargs.get("exec_log", []) or []

    def log_contains(self, needle):
        return any(needle in str(line) for line in self.exec_log)

    @property
    def shell_command(self):
        """シェル起動が1回だけであることを前提に、その1件を返す"""
        assert len(self.shell_commands) == 1, (
            f"シェル起動が1回である前提が崩れている: {self.shell_commands}"
        )
        return self.shell_commands[0]


class FakeSpawn:
    """
    pexpect.spawn の代役。

    expect_prompt() / exec_command() が使うのは
    expect / sendline / readline / before / after / buffer のみ。

    outputs に「expect_prompt が返すたびの p.before」を順に並べる。
    足りなくなったら最後の値を使い回す。
    """

    def __init__(self, outputs=None, expect_side_effect=None):
        self._outputs = list(outputs or [""])
        self._idx = 0
        self._expect_side_effect = expect_side_effect
        self.before = self._outputs[0]
        self.after = "prompt$ "
        self.buffer = ""
        self.sent = []
        self.expects = []
        self.closed = False

    def expect(self, pattern, timeout=None):
        self.expects.append((pattern, timeout))
        if self._expect_side_effect is not None:
            self._expect_side_effect(self, pattern, timeout)
        self.before = self._outputs[min(self._idx, len(self._outputs) - 1)]
        self._idx += 1
        return 0

    def sendline(self, s=""):
        self.sent.append(s)
        return len(s) + 1

    def readline(self):
        return ""

    def close(self, force=True):
        self.closed = True


class FakeCompletedProcess:
    """subprocess.run の戻り値の代役"""

    def __init__(self, args, returncode):
        self.args = args
        self.returncode = returncode
        self.stdout = None
        self.stderr = None


@pytest.fixture
def pioneer_env(tmp_path):
    """
    pioneer_module.main() を動かすために必要なファイル一式を tmp_path に用意し、
    module.params 相当の dict を組み立てる。

    ITA 本体（CreateAnsibleExecFiles）が渡す引数の形に合わせている:
      - 未設定を表す番兵は "__undefinesymbol__"
      - grep_shell_dir は library ディレクトリ（本物のシェルをコピーして置く）
    """
    class Env:
        def __init__(self):
            self.root = tmp_path
            self.host_name = "testhost"

            self.library_dir = tmp_path / "library"
            self.library_dir.mkdir()
            # 検索シェルは本物をコピーする（ITA が in/library へ配置するのと同じ形）
            self.grep_shell = self.library_dir / GREP_SHELL.name
            self.grep_shell.write_bytes(GREP_SHELL.read_bytes())
            self.grep_shell.chmod(0o755)

            self.log_dir = tmp_path / "logs"
            self.log_dir.mkdir()

            self.dialog_dir = tmp_path / "dialog_files"
            self.dialog_dir.mkdir()
            self.original_dialog_dir = tmp_path / "original_dialog_files"
            self.original_dialog_dir.mkdir()

            # ホスト変数ファイル / 暗号化変数ファイル
            # 空(yaml.load -> None)にしておくと vault 置換をスキップできる
            self.host_vars_file = tmp_path / "host_vars.yml"
            self.host_vars_file.write_text("", encoding="utf-8")
            self.vault_file = tmp_path / "encode_column_encode_value_file.yml"
            self.vault_file.write_text("", encoding="utf-8")

            self.dialog_file = None

        @property
        def private_log(self):
            return self.log_dir / f"{self.host_name}_private.log"

        def write_dialog(self, text, name="test_dialog.txt"):
            """
            対話ファイルを書く。
            pioneer_module は exec_file と original_exec_dir/<同名> の
            両方を読むので2箇所に置く。
            """
            self.dialog_file = self.dialog_dir / name
            self.dialog_file.write_text(text, encoding="utf-8")
            (self.original_dialog_dir / name).write_text(text, encoding="utf-8")
            return self.dialog_file

        def write_vault(self, text):
            self.vault_file.write_text(text, encoding="utf-8")

        def params(self, **override):
            assert self.dialog_file is not None, "write_dialog() を先に呼ぶこと"
            base = {
                "username": "__undefinesymbol__",
                "protocol": "ssh",
                "inventory_hostname": self.host_name,
                "host_vars_file": str(self.host_vars_file),
                "exec_file": str(self.dialog_file),
                "grep_shell_dir": str(self.library_dir),
                "log_file_dir": str(self.log_dir),
                "ssh_key_file": "__undefinesymbol__",
                "extra_args": "__undefinesymbol__",
                "lang": "utf-8",
                "original_exec_dir": str(self.original_dialog_dir),
                "encode_column_encode_value_file": str(self.vault_file),
                "ssh_phrases": "",
                "ssh_phrases_flg": "No",
            }
            base.update(override)
            return base

    return Env()


def _load_pioneer_module():
    """
    pioneer_module.py をロードする。末尾に main() 呼び出しがあるため、
    このロード自体が「1回の実行」になる。
    sys.modules には入れない（テストごとにグローバルを初期化したいため）。
    """
    spec = importlib.util.spec_from_file_location(
        "pioneer_module_under_test", str(PIONEER_MODULE)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def run_pioneer(monkeypatch):
    """
    pioneer_module.main() を1回駆動する。

    引数:
      params         : module.params 相当の dict（pioneer_env.params() の戻り）
      check_mode     : ドライラン
      spawn_outputs  : FakeSpawn が expect のたびに返す p.before のリスト
                       None なら pexpect を差し替えない（= 実接続。C で使う）
      shell_returncode : subprocess.run の戻り returncode。
                       None なら実際に subprocess.run を通す（注入検証で使う）
      shell_side_effect : subprocess.run が呼ばれた時点で実行するコールバック。
                       引数は def_shell_cmd の文字列。
                       「シェル実行中に一時ファイルが存在したか」の確認や、
                       例外を送出して異常系を作るのに使う。
    戻り: PioneerResult
    """
    def _run(params, *, check_mode=False, spawn_outputs=None,
             shell_returncode=0, expect_side_effect=None,
             shell_side_effect=None):
        shell_commands = []
        spawns = []

        real_run = subprocess.run

        def fake_subprocess_run(cmd, *args, **kwargs):
            shell_commands.append(cmd)
            if shell_side_effect is not None:
                shell_side_effect(cmd)
            if shell_returncode is None:
                # 実際にシェルを起動する（クォート/注入の検証に使う）
                return real_run(cmd, *args, **kwargs)
            return FakeCompletedProcess(cmd, shell_returncode)

        monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

        if spawn_outputs is not None:
            import pexpect

            def fake_spawn(cmd, *args, **kwargs):
                sp = FakeSpawn(spawn_outputs, expect_side_effect=expect_side_effect)
                sp.spawn_cmd = cmd
                spawns.append(sp)
                return sp

            monkeypatch.setattr(pexpect, "spawn", fake_spawn)

        stub = _make_ansible_stub(params, check_mode)
        with _SysModulesPatch(stub):
            try:
                # main() は必ず exit_json / fail_json に到達するため、
                # ロードは常に StubModuleExit で抜ける
                _load_pioneer_module()
            except StubModuleExit as exit_exc:
                result = PioneerResult(
                    exit_exc.kind, exit_exc.kwargs, None, shell_commands
                )
                result.spawns = spawns
                return result

        raise AssertionError(
            "main() が exit_json/fail_json に到達しなかった（想定外）"
        )

    return _run


# ======================================================================
# C: 実ホスト接続用
# ======================================================================
def run_pioneer_real(params, *, check_mode=False):
    """
    pexpect も subprocess もモックせずに main() を1回駆動する（C 用）。

    実ホストへ SSH 接続し、実際に検索シェルを起動する。
    subprocess.run だけは「呼ばれたコマンド文字列を記録する」ラッパで包むが、
    本物の subprocess.run に丸ごと委譲するので挙動は変わらない。

    フィクスチャではなく素の関数にしてあるのは、
    子プロセス（複数ホスト同時実行の検証）からも呼べるようにするため。

    戻り: PioneerResult
    """
    shell_commands = []
    real_run = subprocess.run

    def recording_run(cmd, *args, **kwargs):
        shell_commands.append(cmd)
        return real_run(cmd, *args, **kwargs)

    subprocess.run = recording_run
    try:
        stub = _make_ansible_stub(params, check_mode)
        with _SysModulesPatch(stub):
            try:
                _load_pioneer_module()
            except StubModuleExit as exit_exc:
                return PioneerResult(
                    exit_exc.kind, exit_exc.kwargs, None, shell_commands
                )
    finally:
        subprocess.run = real_run

    raise AssertionError("main() が exit_json/fail_json に到達しなかった（想定外）")


def _ssh_target():
    return (
        os.environ.get("ITA_TEST_SSH_HOST"),
        os.environ.get("ITA_TEST_SSH_USER"),
        os.environ.get("ITA_TEST_SSH_PASS"),
    )


requires_ssh_target = pytest.mark.skipif(
    not all(_ssh_target()),
    reason=(
        "実ホストへの結合テストには接続情報が必要。"
        "ITA_TEST_SSH_HOST / ITA_TEST_SSH_USER / ITA_TEST_SSH_PASS を設定して実行する。"
        "（認証情報はリポジトリに置かない）"
    ),
)


@pytest.fixture
def ssh_target():
    """環境変数から接続先を読む。リポジトリには認証情報を置かない"""
    host, user, password = _ssh_target()
    if not all((host, user, password)):
        pytest.skip("ITA_TEST_SSH_HOST / ITA_TEST_SSH_USER / ITA_TEST_SSH_PASS が未設定")
    return {"host": host, "user": user, "password": password}


@pytest.fixture
def run_pioneer_integration():
    """run_pioneer_real をテストから使いやすくしただけのフィクスチャ"""
    return run_pioneer_real
