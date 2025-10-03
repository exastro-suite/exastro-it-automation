# Copyright 2025 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from flask import Flask, g
from common_libs.oase.api_client_common import APIClientCommon

app = Flask(__name__)


class DummyLogger:
    def debug(self, msg): pass
    def info(self, msg): pass


class DummyAppMsg:
    def get_log_message(self, code, args=None): return code


@pytest.fixture(autouse=True)
def setup_g():
    with app.app_context():
        g.applogger = DummyLogger()
        g.appmsg = DummyAppMsg()
        yield


@pytest.fixture
def dummy_setting():
    return {
        "EVENT_COLLECTION_SETTINGS_ID": "1",
        "EVENT_COLLECTION_SETTINGS_NAME": "test",
        "REQUEST_METHOD_ID": "1",
        "PORT": 443,
        "PROXY": None,
        "AUTH_TOKEN": "",
        "USERNAME": "",
        "PASSWORD": "",
        "ACCESS_KEY_ID": "",
        "SECRET_ACCESS_KEY": "",
        "MAILBOXNAME": "",
        "PARAMETER": '{"key": "value"}',
        "LAST_FETCHED_TIMESTAMP": 0,
        "SAVED_IDS": [],
        "RESPONSE_LIST_FLAG": "1",
        "RESPONSE_KEY": None,
        "EVENT_ID_KEY": "id",
        "URL": "https://dummy/api",
        "REQUEST_HEADER": '{"X-Test": "test"}'
    }


def test_render_url(dummy_setting):
    '''
    接続先（url）の値をテンプレートとしてレンダリングするテスト
    '''
    client = APIClientCommon(dummy_setting, last_fetched_event=None)
    # __init__でself.render("URL", ...)が呼ばれる
    assert client.url == "https://dummy/api"


def test_render_request_header(dummy_setting):
    client = APIClientCommon(dummy_setting, last_fetched_event=None)
    # __init__でself.render("REQUEST_HEADER", ...)が呼ばれる
    assert isinstance(client.headers, dict)
    assert client.headers.get("X-Test") == "test"


@pytest.fixture
def mock_requests(monkeypatch):
    '''
    テストで外部APIにアクセスしないよう requests をモック
    '''
    class DummyResponse:
        def __init__(self):
            self.status_code = 200
            self.text = '{"key": "value"}'
            self.content = b'{"key": "value"}'
        def json(self):
            return {"key": "value"}
    def dummy_request(*args, **kwargs):
        return DummyResponse()
    monkeypatch.setattr("requests.request", dummy_request)


def test_render_parameter(dummy_setting, mock_requests):
    client = APIClientCommon(dummy_setting, last_fetched_event=None)
    # call_apiでself.render("PARAMETER", ...)が呼ばれる
    result, events = client.call_api(dummy_setting, last_fetched_event=None)
    assert client.parameter == {"key": "value"}
