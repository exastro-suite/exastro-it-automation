# PYTEST
#   Copyright 2024 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
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
# from unittest import mock

import pytest
from agent_main import get_agent_version

# get_agent_version用のpytest


def test_get_agent_version_success(tmp_path, monkeypatch):
    """
    get_agent_version：ファイルからバージョン情報を取得するテスト
    末尾に改行があるファイルからバージョン番号「2.7.0」を正しく取得できることを確認
    """
    version_content = "2.7.0\n"
    version_file = tmp_path / "VERSION.txt"
    version_file.write_text(version_content)

    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    version = get_agent_version()
    assert version == "2.7.0"


def test_get_agent_version_no_newline(tmp_path, monkeypatch):
    """
    get_agent_version：改行がないファイルからバージョン情報を取得するテスト
    末尾に改行がない場合でも、バージョン番号「2.7.0」を正しく取得できることを確認
    """
    version_content = "2.7.0"
    version_file = tmp_path / "VERSION.txt"
    version_file.write_text(version_content)

    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    version = get_agent_version()
    assert version == "2.7.0"


def test_get_agent_version_file_not_found(monkeypatch):
    """
    get_agent_version：ファイルが存在しない場合の例外処理をテスト
    指定されたパスにファイルがない場合にFileNotFoundErrorが発生することを確認
    """
    monkeypatch.setenv("PYTHONPATH", "/non_non_file")

    with pytest.raises(FileNotFoundError):
        get_agent_version()
