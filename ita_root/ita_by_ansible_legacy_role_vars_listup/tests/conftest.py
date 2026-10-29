#   Copyright 2026 NEC Corporation
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

"""ita_by_ansible_legacy_role_vars_listup のテスト共通 fixture

当モジュールのテストは DB に接続しないため、DB コンテナは不要。
"""
import pytest
from unittest.mock import MagicMock
from flask import Flask, g

from tests.common import TEST_USER_ID
from tests.dummy_db import DummyDB


@pytest.fixture
def flask_app_context():
    """Flaskアプリケーションコンテキストを作成"""
    flask_app = Flask(__name__)
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def mock_g(flask_app_context):
    """グローバル変数gをモック化"""
    g.LANGUAGE = "ja"
    g.USER_ID = TEST_USER_ID
    g.SERVICE_NAME = "test_service"
    g.WORKSPACE_ID = "test_workspace_id"
    g.ORGANIZATION_ID = "test_org_id"

    g.applogger = MagicMock()
    g.appmsg = MagicMock()
    g.appmsg.get_log_message.return_value = "Mocked log message"

    return g


@pytest.fixture
def dummy_db():
    """DBConnectWs のダミー（中身は空）"""
    return DummyDB()


@pytest.fixture
def run_backyard(monkeypatch, mock_g):
    """刈取メイン処理を本物のまま 1 回実行する関数を返す（DB の代役と解析結果を渡す）"""
    from tests.common import run_backyard_main

    def _run(dummy_db, mov_vars_dict=None):
        run_backyard_main(monkeypatch, dummy_db, mov_vars_dict)

    return _run
