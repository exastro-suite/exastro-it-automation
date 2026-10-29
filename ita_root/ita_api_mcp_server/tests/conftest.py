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

import sys

import pytest
from unittest import mock
from flask import Flask, g

# tools/search_documents.py はimport時(モジュールロード時)にfastembed.TextEmbedding /
# qdrant_client.QdrantClientへ接続しようとする。コンテナ外へのアクセスはテストから一切
# 行わないよう、`tools` パッケージを最初にimportする前に sys.modules へ偽モジュールを
# 差し込んでおく(本物のfastembed/qdrant_clientを実際にimportすると、重い依存関係
# (numpy等)がpytest-covの計測と組み合わさった際に "cannot load module more than
# once per process" を起こすため、mock.patchで本物をimportしてから差し替えるのでは
# なく、importそのものを差し替える)。
# これによりtools.search_documents.model / .clientにはMagicMockが入るが、各テストは
# 個別にmonkeypatch/mocker.patch.objectでmodel・clientを上書きして期待する挙動を設定する。
sys.modules["fastembed"] = mock.MagicMock()
sys.modules["qdrant_client"] = mock.MagicMock()

import tools  # noqa: F401,E402


@pytest.fixture
def app():
    """Flaskアプリケーションのインスタンスを作成"""
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture
def app_context(app):
    """Flaskアプリケーションコンテキスト"""
    with app.test_request_context():
        yield


@pytest.fixture
def mock_flask_g(app_context):
    """Flask g オブジェクトのモック(applogger/appmsgのみ差し替え、リクエストコンテキストは本物)"""
    g.applogger = mock.Mock()
    g.applogger.info = mock.Mock()
    g.applogger.error = mock.Mock()
    g.applogger.debug = mock.Mock()
    g.appmsg = mock.Mock()
    g.appmsg.get_api_message = mock.Mock(side_effect=lambda msg_id, *args: "Message {}".format(msg_id))
    g.appmsg.get_log_message = mock.Mock(side_effect=lambda msg_id, *args: "Log Message {}".format(msg_id))
    g.LANGUAGE = "en"
    yield g


@pytest.fixture
def mock_dbca():
    """DBConnectWsが返すDB操作モックオブジェクト(ワークスペースDB接続の代替)"""
    mock_ws_db = mock.MagicMock()
    mock_ws_db.table_select = mock.Mock(return_value=[])
    mock_ws_db.sql_execute = mock.Mock(return_value=[])
    mock_ws_db.db_transaction_start = mock.Mock()
    mock_ws_db.db_transaction_end = mock.Mock()
    mock_ws_db.db_disconnect = mock.Mock()
    return mock_ws_db
