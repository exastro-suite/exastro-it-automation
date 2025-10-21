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
import datetime
import jmespath
from common_libs.oase.api_client_common import APIClientCommon
from tests.common_libs.oase.test_api_client_common import test_parameters
from libs.collect_event import extract_events

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


@pytest.mark.parametrize(
    "raw_json, dummy_setting, expected_response, expected_events", test_parameters
)

def test_extract_events(raw_json, dummy_setting, expected_response, expected_events):
    # 必要な設定を追加(zabbix_problem_get用)
    dummy_setting.update({
        "URL": "http://10.197.18.228/api_jsonrpc.php",
        "PORT": None,
        "PROXY": None,
        "CONNECTION_METHOD_ID": "5",
        "REQUEST_METHOD_ID": "2",
        "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
        "AUTH_TOKEN": "u/9aLZZSn5Ua66S+SBqz3z59XK9SMyLXukvSVsuQno09pjWdbTyx8EA7DsRBJ14tNLrlFbobedc/B6UThxcCBQ88nRNv/yGhaBmvJ8eErXN09WZJxTkXAdBmJp6WYwwn",
        "USERNAME": "",
        "PASSWORD": "",
        "ACCESS_KEY_ID": "",
        "SECRET_ACCESS_KEY": "",
        "MAILBOXNAME": "",
		"PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"problem.get\",\n    \"params\": {\n        \"output\": \"extend\",\n        {% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}\n          \"eventid_from\": \"{{ EXASTRO_LAST_FETCHED_EVENT.eventid|int + 1  }}\"\n        {% else %}\n          \"time_from\": \"{{ EXASTRO_LAST_FETCHED_TIMESTAMP }}\"\n        {% endif %}\n    },\n  \"auth\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\",\n  \"id\": 1\n}",
		"MAILBOXNAME": None,
        "NOTE": "b",
        "DISUSE_FLAG": "0",
		"LAST_UPDATE_TIMESTAMP": "2025-10-15T19:38:45.663876Z",
		"LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1"
    })

    # クライアントを初期化
    client = APIClientCommon(dummy_setting, last_fetched_event=None)

    # 日時（ミリ秒単位）シリアル値
    now_time = int(dummy_setting["LAST_FETCHED_TIMESTAMP"]) * 1000
    result_json = client.get_new_events(raw_json, now_time)

    # テスト結果の検証
    assert result_json == expected_response  # 新規イベントのリストを確認

    fetched_time = datetime.datetime(1970, 1, 1, 9)  # Unix時間0の日時（東京）を代入
    events, event_length = extract_events(dummy_setting, fetched_time, result_json)

    # テスト結果の検証
    assert event_length == len(expected_events)
    assert events == expected_events
