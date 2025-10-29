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

# リクエストのテスト用のパラメータ（dummy_setting, last_fetched_event, expected_requests）
test_requests_parameters = [
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_problem_get",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"problem.get\",\n    \"params\": {\n        \"output\": \"extend\",\n        {% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}\n          \"eventid_from\": \"{{ EXASTRO_LAST_FETCHED_EVENT.eventid }}\"\n        {% else %}\n          \"time_from\": \"{{ EXASTRO_LAST_FETCHED_TIMESTAMP }}\"\n        {% endif %}\n    },\n  \"auth\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\",\n  \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": "hmvA0mcecB1gG++MFCKg5co6jDn5n2LN7f0E4k2YiBQ=",
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "admin",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
        },
        {
            "acknowledged": "0",
            "clock": "1760434892",
            "correlationid": "0",
            "eventid": "366",
            "name": "error319",
            "ns": "766145658",
            "object": "0",
            "objectid": "24477",
            "opdata": "",
            "r_clock": "0",
            "r_eventid": "0",
            "r_ns": "0",
            "severity": "2",
            "source": "0",
            "suppressed": "0",
            "urls": [],
            "userid": "0"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {
                    "output": "extend",
                    "eventid_from": "366"
                },
                "auth": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
                "id": 1
            }
        }
    ),
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_problem_get",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"problem.get\",\n    \"params\": {\n        \"output\": \"extend\",\n        {% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}\n          \"eventid_from\": \"{{ EXASTRO_LAST_FETCHED_EVENT.eventid }}\"\n        {% else %}\n          \"time_from\": \"{{ EXASTRO_LAST_FETCHED_TIMESTAMP }}\"\n        {% endif %}\n    },\n  \"auth\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\",\n  \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": "hmvA0mcecB1gG++MFCKg5co6jDn5n2LN7f0E4k2YiBQ=",
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "admin",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
        },
        None,
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {
                    "output": "extend",
                    "time_from": "1760599000"
                },
                "auth": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
                "id": 1
            }
        }
    ),
    # 2-接続先(1): EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKENの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "auth_token_check",
            "EVENT_ID_KEY": "event_collection_settings_id",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "data",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php?token={{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN | urlencode() }}",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1729756009,
        },
        None,
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php?token=ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "headers": {
                "content-type": "application/json",
            },
            "parameter": None
        }
    ),
    # 3-接続先(2): EXASTRO_LAST_FETCHED_EVENT.eventidの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_last_fetched_event_check",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php?eventid={{ EXASTRO_LAST_FETCHED_EVENT.eventid | urlencode() }}",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1729756009,
        },
        {
            "eventid": "67890",
            "clock": 1695110400,
            "ns": "dummy",
            "value": "dummy"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php?eventid=67890",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": None
        }
    ),
    # 4-リクエストヘッダー(1): EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKENの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_request_auth_token_check",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "",
            "PASSWORD": "password",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{\n      \"content-type\": \"application/json\",\n      \"Authorization\": \"Bearer {{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\"\n}",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "data",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php?token={{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN | urlencode() }}",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1729756009,
        },
        None,
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php?token=ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "headers": {
                "content-type": "application/json",
                "Authorization": "Bearer ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC"
            },
            "parameter": None
        }
    ),
    # 5-パラメータ(1): EXASTRO_EVENT_COLLECTION_SETTING.USERNAME/PASSWORDの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_user_login_password",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"user.login\",\n    \"params\": {\n      \"username\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.USERNAME }}\",\n      \"password\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.PASSWORD }}\"\n    },\n    \"id\": 1\n  }",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": "hmvA0mcecB1gG++MFCKg5co6jDn5n2LN7f0E4k2YiBQ=",
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1729756009,
        },
        None,
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "username": "user",
                    "password": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4="
                },
                "id": 1
            }
        }
    ),
    # 6-パラメータ(2): EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKENの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_auth_token",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"alert.get\",\n    \"params\": {\n        \"output\": \"extend\",\n        \"actionids\": \"3\"\n    },\n    \"auth\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\",\n    \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": "hmvA0mcecB1gG++MFCKg5co6jDn5n2LN7f0E4k2YiBQ=",
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1729756009,
        },
        None,
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "alert.get",
                "params": {
                    "output": "extend",
                    "actionids": "3"
                },
                "auth": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
                "id": 1
            }
        }
    ),
    # 7-パラメータ(3): EXASTRO_LAST_FETCHED_EVENT.clockの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_last_fetched_event_clock",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"event.get\",\n    \"params\": {\n        \"output\": \"extend\",\n        \"time_from\": \"{{ EXASTRO_LAST_FETCHED_EVENT.clock }}\"\n    },\n    \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": "hmvA0mcecB1gG++MFCKg5co6jDn5n2LN7f0E4k2YiBQ=",
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1729756009,
        },
        {
            "eventid": "12345",
            "clock": "1758731649",
            "ns": "123456789",
            "value": "1"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "event.get",
                "params": {
                    "output": "extend",
                    "time_from": "1758731649"  # EXASTRO_LAST_FETCHED_EVENT.clockの値
                },
                "id": 1
            }
        }
    ),
    # 8-パラメータ(4): EXASTRO_LAST_FETCHED_TIMESTAMPの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_event_get_timestamp",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"event.get\",\n    \"params\": {\n        \"output\": \"extend\",\n        \"time_from\": \"{{ EXASTRO_LAST_FETCHED_TIMESTAMP }}\"\n    },\n    \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1758879732,
        },
        {
            "eventid": "12345",
            "ns": "123456789",
            "value": "1"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "event.get",
                "params": {
                    "output": "extend",
                    "time_from": "1758879732"  # EXASTRO_LAST_FETCHED_TIMESTAMPの値
                },
                "id": 1
            }
        }
    ),
    # 9-パラメータ(5): EXASTRO_LAST_FETCHED_TIMESTAMPの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_event_get_timestamp",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"problem.get\",\n     \"params\": {\n        \"output\": \"extend\",\n             \"time_from\": \"{{ EXASTRO_LAST_FETCHED_TIMESTAMP }}\"\n    },\n    \"auth\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\",\n    \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        {
            "eventid": "12345",
            "ns": "123456789",
            "value": "1"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {
                    "output": "extend",
                    "time_from": "1695110400"
                },
                "auth": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
                "id": 1
            }
        }
    ),
    # 10-パラメータ(6): EXASTRO_LAST_FETCHED_EVENT.clock,EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKENの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_auth_token_check",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\":\"2.0\",\n    \"method\":\"problem.get\",\n     \"params\" : {\n        \"output\":\"extend\",\n        \"time_from\": \"{{ EXASTRO_LAST_FETCHED_EVENT.clock }}\"\n    },\n    \"auth\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\",\n    \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        {
            "eventid": "425",
            "clock": 1695110400,
            "ns": "dummy",
            "value": "dummy"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {
                    "output": "extend",
                    "time_from": "1695110400"
                },
                "auth": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
                "id": 1
            }
        }
    ),
    # 11-パラメータ(7-1): EXASTRO_LAST_FETCHED_EVENT.eventidの変数確認 - 前回取得イベントがある場合
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_last_fetched_true",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"problem.get\",\n    \"params\": {\n        \"output\": \"extend\",\n        {% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}\n          \"eventid_from\": \"{{ EXASTRO_LAST_FETCHED_EVENT.eventid|int + 1  }}\"\n        {% else %}\n          \"time_from\": \"{{ EXASTRO_LAST_FETCHED_TIMESTAMP }}\"\n        {% endif %}\n    },\n  \"auth\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\",\n  \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        {
            "eventid": "450",
            "clock": 1695110400,
            "ns": "dummy",
            "value": "dummy"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {
                    "output": "extend",
                    "eventid_from": "451"  # 前回イベントがある場合はid+1
                },
                "auth": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
                "id": 1
            }
        }
    ),
    # 12-パラメータ(7-2): EXASTRO_LAST_FETCHED_EVENT.eventidの変数確認 - 前回取得イベントが無い場合
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_last_fetched_false",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"problem.get\",\n    \"params\": {\n        \"output\": \"extend\",\n        {% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}\n          \"eventid_from\": \"{{ EXASTRO_LAST_FETCHED_EVENT.eventid|int + 1  }}\"\n        {% else %}\n          \"time_from\": \"{{ EXASTRO_LAST_FETCHED_TIMESTAMP }}\"\n        {% endif %}\n    },\n  \"auth\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\",\n  \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        None,
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {
                    "output": "extend",
                    "time_from": "1695110400"
                },
                "auth": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
                "id": 1
            }
        }
    ),
    # 13-パラメータ(8): EXASTRO_LAST_FETCHED_TIMESTAMPの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_last_fethced_check",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n      \"jsonrpc\": \"2.0\",\n      \"method\": \"problem.get\",\n       \"params\": {\n            \"output\": \"extend\",\n            \"time_from\": \"EXASTRO_LAST_FETCHED_TIMESTAMP\"\n      },\n    \"auth\": \"\",\n    \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        {
            "eventid": "450",
            "clock": 1695110400,
            "ns": "dummy",
            "value": "dummy"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {
                    "output": "extend",
                    "time_from": "1695110400"
                },
                "auth": "",
                "id": 1
            }
        }
    ),
    # 14-1パラメータ(9-1): 条件分岐EXASTRO_LAST_FETCHED_...の変数確認- 前回取得イベントがある場合
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_last_fethced_check",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"problem.get\",\n    \"params\": {\n        \"output\": \"extend\",\n        {% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}\n          \"eventid_from\": \"{{ EXASTRO_LAST_FETCHED_EVENT.eventid|int + 1  }}\"\n        {% else %}\n          \"time_from\": \"EXASTRO_LAST_FETCHED_TIMESTAMP\"\n        {% endif %}\n    },\n  \"auth\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\",\n  \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        {
            "eventid": "450",
            "clock": 1695110400,
            "ns": "dummy",
            "value": "dummy"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {
                    "output": "extend",
                    "eventid_from": "451"
                },
                "auth": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
                "id": 1
            }
        }
    ),
    # 15-パラメータ(9-2): 条件分岐EXASTRO_LAST_FETCHED_...の変数確認- 前回取得イベントがない場合
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_last_fethced_check",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"problem.get\",\n    \"params\": {\n        \"output\": \"extend\",\n        {% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}\n          \"eventid_from\": \"{{ EXASTRO_LAST_FETCHED_EVENT.eventid|int + 1  }}\"\n        {% else %}\n          \"time_from\": \"EXASTRO_LAST_FETCHED_TIMESTAMP\"\n        {% endif %}\n    },\n  \"auth\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\",\n  \"id\": 1\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        None,
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {
                    "output": "extend",
                    "time_from": "1695110400"
                },
                "auth": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
                "id": 1
            }
        }
    ),
    # 16-パラメータ(10): EXASTRO_LAST_FETCHED_EVENTの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "5",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_last_fethced_dummy",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n      \"eventid_from\": \"{{ EXASTRO_LAST_FETCHED_EVENT.dummy }}\"\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
            "REQUEST_METHOD_ID": "2",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        {
            "eventid": "450",
            "clock": 1695110400,
            "ns": "dummy",
            "value": "dummy"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json-rpc",
            },
            "parameter": {
                "eventid_from": ""
            }
        }
    ),
    # 17-パラメータ(11): EXASTRO_LAST_FETCHED_YY_MM_DDの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "1",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "last_fetched_YY_MM_DD_check",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-24T00:20:22.172832Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n      \"discard\": { \"NORMAL\": \"0\" },\n      \"last_update_date_time\": { \"RANGE\": { \"START\": \"{{ EXASTRO_LAST_FETCHED_YY_MM_DD }}\" } }\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json\" }",
            "REQUEST_METHOD_ID": "1",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        {
            "eventid": "450",
            "ns": "dummy",
            "value": "dummy"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json",
            },
            "parameter": {
                "discard": {
                    "NORMAL": "0"
                },
                "last_update_date_time": {
                    "RANGE": {
                        "START": "2023/09/19 17:00:00"
                    }
                }
            }
        }
    ),
    # 18-パラメータ(12): EXASTRO_LAST_FETCHED_YY_MM_DDの変数確認
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "1",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "last_fetched_YY_MM_DD:00:00:00_check",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-28T00:54:09.000000Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n      \"discard\": { \"NORMAL\": \"0\" },\n      \"last_update_date_time\": {\n            \"RANGE\": {\n                  \"START\": \"{{ EXASTRO_LAST_FETCHED_TIME.year }}/{{ '%02d'|format(EXASTRO_LAST_FETCHED_TIME.month) }}/{{ '%02d'|format(EXASTRO_LAST_FETCHED_TIME.day) }} 00:00:00\"\n            }\n      }\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json\" }",
            "REQUEST_METHOD_ID": "1",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        None,
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json",
            },
            "parameter": {
                "discard": {
                    "NORMAL": "0"
                },
                "last_update_date_time": {
                    "RANGE": {
                        "START": "2023/09/19 00:00:00"
                    }
                }
            }
        }
    ),
    # 19-パラメータ(13-1): 条件分岐EXASTRO_LAST_FETCHED_..の変数確認-前回データが廃止ありの場合
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "1",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "last_fetched_check",
            "EVENT_ID_KEY": "eventid",
            "LAST_UPDATE_TIMESTAMP": "2025-10-28T00:54:09.000000Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n  {% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}\n    {% if EXASTRO_LAST_FETCHED_EVENT.parameter.discard == \"1\" %}\n      \"discard\": { \"NORMAL\": \"0\" }\n    {% else %}\n      \"discard\": { \"NORMAL\": \"1\" }\n    {% endif %}\n  {% else %}\n    \"discard\": { \"NORMAL\": \"0\" }\n  {% endif %}\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json\" }",
            "REQUEST_METHOD_ID": "1",
            "RESPONSE_KEY": "data",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        {
            "eventid": "450",
            "clock": 1695110400,
            "parameter": {
                "discard": "1"
            },
            "ns": "dummy",
            "value": "dummy"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json",
            },
            "parameter": {
                "discard": {
                    "NORMAL": "0"
                }
            }
        }
    ),
    # 20-パラメータ(13-2): 条件分岐EXASTRO_LAST_FETCHED_..の変数確認 - 前回データがない場合
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "1",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "last_fetched_check",
            "EVENT_ID_KEY": "id",
            "LAST_UPDATE_TIMESTAMP": "2025-10-28T00:54:09.000000Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n  {% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}\n    {% if EXASTRO_LAST_FETCHED_EVENT.parameter.discard == \"1\" %}\n      \"discard\": { \"NORMAL\": \"0\" }\n    {% else %}\n      \"discard\": { \"NORMAL\": \"1\" }\n    {% endif %}\n  {% else %}\n    \"discard\": { \"NORMAL\": \"0\" }\n  {% endif %}\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json\" }",
            "REQUEST_METHOD_ID": "1",
            "RESPONSE_KEY": "data",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": None,
            "EXASTRO_LAST_FETCHED_EVENT_IS_EXIST": False,
        },
        None,
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json",
            },
            "parameter": {
                "discard": {
                    "NORMAL": "0"
                }
            }
        }
    ),
    # 20-パラメータ(13-3): 条件分岐EXASTRO_LAST_FETCHED_..の変数確認 - 前回データが廃止無しの場合
    (
        {
            "ACCESS_KEY_ID": None,
            "AUTH_TOKEN": "ytkkfvj3EHeXZaO7qN5vD6MSbye1pG0AuLh3lOI6JaOfhbyma1KW0XsVu6bC",
            "CONNECTION_METHOD_ID": "1",
            "DISUSE_FLAG": "0",
            "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
            "EVENT_COLLECTION_SETTINGS_NAME": "last_fetched_check",
            "EVENT_ID_KEY": "id",
            "LAST_UPDATE_TIMESTAMP": "2025-10-28T00:54:09.000000Z",
            "LAST_UPDATE_USER": "7f3ae1a4-c163-40d5-8509-c3881f5e46f1",
            "MAILBOXNAME": None,
            "NOTE": "b",
            "PARAMETER": "{\n  {% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}\n    {% if EXASTRO_LAST_FETCHED_EVENT.parameter.discard == \"1\" %}\n      \"discard\": { \"NORMAL\": \"0\" }\n    {% else %}\n      \"discard\": { \"NORMAL\": \"1\" }\n    {% endif %}\n  {% else %}\n    \"discard\": { \"NORMAL\": \"0\" }\n  {% endif %}\n}",
            "PASSWORD": "4jFT+McKLHwH123J+5UPn337ejPj3PlMUnh2/NPDKl4=",
            "PORT": None,
            "PROXY": None,
            "REQUEST_HEADER": "{ \"content-type\" : \"application/json\" }",
            "REQUEST_METHOD_ID": "1",
            "RESPONSE_KEY": "data",
            "RESPONSE_LIST_FLAG": "1",
            "SECRET_ACCESS_KEY": None,
            "TTL": 60,
            "URL": "http://dummy.hoge.com/api_jsonrpc.php",
            "USERNAME": "user",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1695110400,
        },
        {
            "eventid": "450",
            "clock": 1695110400,
            "parameter": {
                "discard": "0"
            },
            "ns": "dummy",
            "value": "dummy"
        },
        {
            "url": "http://dummy.hoge.com/api_jsonrpc.php",
            "headers": {
                "content-type": "application/json",
            },
            "parameter": {
                "discard": {
                    "NORMAL": "1"
                }
            }
        }
    ),
]

@pytest.mark.parametrize(
    "dummy_setting, last_fetched_event, expected_requests",
    test_requests_parameters
)
def test_render_requests(dummy_setting, last_fetched_event, expected_requests):
    '''
    接続先（url）の値をテンプレートとしてレンダリングするテスト
    '''
    client = APIClientCommon(dummy_setting, last_fetched_event)
    # __init__でself.render("URL", ...)が呼ばれる
    assert client.url == expected_requests["url"]

    # __init__でself.render("REQUEST_HEADER", ...)が呼ばれる
    assert isinstance(client.headers, dict)
    assert client.headers == expected_requests["headers"]

    # __init__でself.render("PARAMETER", ...)が呼ばれる
    assert isinstance(client.headers, dict)
    assert client.parameter == expected_requests["parameter"]





test_response_parameters = [
    # テストケース:メール→対象外

    # テストケース:レスポンスがzabbixのproblem.get
    ## 0-正常系 - 全て新規（SAVED_IDSなし）
    (
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434895",
                    "correlationid": "0",
                    "eventid": "367",
                    "name": "error320",
                    "ns": "766145699",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "1",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_problem_get",
            "EVENT_COLLECTION_SETTINGS_ID": "1",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "eventid",
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "_exastro_oase_event_id": "366",
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "_exastro_oase_event_id": "367",
                    "acknowledged": "0",
                    "clock": "1760434895",
                    "correlationid": "0",
                    "eventid": "367",
                    "name": "error320",
                    "ns": "766145699",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        [
            {
                "_exastro_oase_event_id": "366",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "acknowledged": "0",
                "clock": "1760434892",
                "correlationid": "0",
                "eventid": "366",
                "name": "error319",
                "ns": "766145658",
                "object": "0",
                "objectid": "24477",
                "opdata": "",
                "r_clock": "0",
                "r_eventid": "0",
                "r_ns": "0",
                "severity": "2",
                "source": "0",
                "suppressed": "0",
                "urls": [],
                "userid": "0"
            },
            {
                "_exastro_oase_event_id": "367",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "acknowledged": "0",
                "clock": "1760434895",
                "correlationid": "0",
                "eventid": "367",
                "name": "error320",
                "ns": "766145699",
                "object": "0",
                "objectid": "24477",
                "opdata": "",
                "r_clock": "0",
                "r_eventid": "0",
                "r_ns": "0",
                "severity": "2",
                "source": "0",
                "suppressed": "0",
                "urls": [],
                "userid": "0"
            }
        ]
    ),
    ## 1-正常系 - 全て新規（SAVED_IDSあり）
    (
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434895",
                    "correlationid": "0",
                    "eventid": "367",
                    "name": "error320",
                    "ns": "766145699",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "1",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_problem_get",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "eventid",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "_exastro_oase_event_id": "366",
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "_exastro_oase_event_id": "367",
                    "acknowledged": "0",
                    "clock": "1760434895",
                    "correlationid": "0",
                    "eventid": "367",
                    "name": "error320",
                    "ns": "766145699",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        [
            {
                "_exastro_oase_event_id": "366",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "acknowledged": "0",
                "clock": "1760434892",
                "correlationid": "0",
                "eventid": "366",
                "name": "error319",
                "ns": "766145658",
                "object": "0",
                "objectid": "24477",
                "opdata": "",
                "r_clock": "0",
                "r_eventid": "0",
                "r_ns": "0",
                "severity": "2",
                "source": "0",
                "suppressed": "0",
                "urls": [],
                "userid": "0"
            },
            {
                "_exastro_oase_event_id": "367",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "acknowledged": "0",
                "clock": "1760434895",
                "correlationid": "0",
                "eventid": "367",
                "name": "error320",
                "ns": "766145699",
                "object": "0",
                "objectid": "24477",
                "opdata": "",
                "r_clock": "0",
                "r_eventid": "0",
                "r_ns": "0",
                "severity": "2",
                "source": "0",
                "suppressed": "0",
                "urls": [],
                "userid": "0"
            }
        ]
    ),
    ## 2-正常系 - 2件が新規、2件が既存
    (
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "acknowledged": "0",
                    "clock": "1760434620",
                    "correlationid": "0",
                    "eventid": "364",
                    "name": "error317",
                    "ns": "677500040",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434622",
                    "correlationid": "0",
                    "eventid": "365",
                    "name": "error318",
                    "ns": "677500047",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434895",
                    "correlationid": "0",
                    "eventid": "367",
                    "name": "error320",
                    "ns": "766145699",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "1",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_problem_get",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "eventid",
            "SAVED_IDS": ["364", "366"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "_exastro_oase_event_id": "365",
                    "acknowledged": "0",
                    "clock": "1760434622",
                    "correlationid": "0",
                    "eventid": "365",
                    "name": "error318",
                    "ns": "677500047",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "_exastro_oase_event_id": "367",
                    "acknowledged": "0",
                    "clock": "1760434895",
                    "correlationid": "0",
                    "eventid": "367",
                    "name": "error320",
                    "ns": "766145699",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        [
            {
                "_exastro_oase_event_id": "365",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "acknowledged": "0",
                "clock": "1760434622",
                "correlationid": "0",
                "eventid": "365",
                "name": "error318",
                "ns": "677500047",
                "object": "0",
                "objectid": "24477",
                "opdata": "",
                "r_clock": "0",
                "r_eventid": "0",
                "r_ns": "0",
                "severity": "2",
                "source": "0",
                "suppressed": "0",
                "urls": [],
                "userid": "0"
            },
            {
                "_exastro_oase_event_id": "367",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "acknowledged": "0",
                "clock": "1760434895",
                "correlationid": "0",
                "eventid": "367",
                "name": "error320",
                "ns": "766145699",
                "object": "0",
                "objectid": "24477",
                "opdata": "",
                "r_clock": "0",
                "r_eventid": "0",
                "r_ns": "0",
                "severity": "2",
                "source": "0",
                "suppressed": "0",
                "urls": [],
                "userid": "0"
            }
        ]
    ),
    ## 3-正常系 - 全て既存
    (
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "acknowledged": "0",
                    "clock": "1760434622",
                    "correlationid": "0",
                    "eventid": "365",
                    "name": "error318",
                    "ns": "677500047",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434895",
                    "correlationid": "0",
                    "eventid": "367",
                    "name": "error320",
                    "ns": "766145699",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "1",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_problem_get",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "eventid",
            "SAVED_IDS": ["365", "366", "367"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": []
        },
        []
    ),
    ## 4-正常系 - 取れたが、中身が空リスト
    (
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": []
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "1",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_problem_get",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "eventid",
            "SAVED_IDS": ["365", "366", "367"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": []
        },
        []
    ),
    ## 5-異常系 - RESPONSE_KEYの指定が間違っている（存在しないものを設定している）
    (
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "acknowledged": "0",
                    "clock": "1760434622",
                    "correlationid": "0",
                    "eventid": "365",
                    "name": "error318",
                    "ns": "677500047",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "1",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_problem_get",
            "RESPONSE_KEY": "aa",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "eventid",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "acknowledged": "0",
                    "clock": "1760434622",
                    "correlationid": "0",
                    "eventid": "365",
                    "name": "error318",
                    "ns": "677500047",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "RESPONSE_KEY not found",
                "id": 1,
                "jsonrpc": "2.0",
                "result": [
                    {
                        "acknowledged": "0",
                        "clock": "1760434622",
                        "correlationid": "0",
                        "eventid": "365",
                        "name": "error318",
                        "ns": "677500047",
                        "object": "0",
                        "objectid": "24477",
                        "opdata": "",
                        "r_clock": "0",
                        "r_eventid": "0",
                        "r_ns": "0",
                        "severity": "2",
                        "source": "0",
                        "suppressed": "0",
                        "urls": [],
                        "userid": "0"
                    },
                    {
                        "acknowledged": "0",
                        "clock": "1760434892",
                        "correlationid": "0",
                        "eventid": "366",
                        "name": "error319",
                        "ns": "766145658",
                        "object": "0",
                        "objectid": "24477",
                        "opdata": "",
                        "r_clock": "0",
                        "r_eventid": "0",
                        "r_ns": "0",
                        "severity": "2",
                        "source": "0",
                        "suppressed": "0",
                        "urls": [],
                        "userid": "0"
                    }
                ]
            }
        ]
    ),
    ## 6-異常系 - RESPONSE_LIST_FLAGの指定が間違っている（配列なのにFalseを設定）
    (
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "acknowledged": "0",
                    "clock": "1760434622",
                    "correlationid": "0",
                    "eventid": "365",
                    "name": "error318",
                    "ns": "677500047",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "1",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_problem_get",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "eventid",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "acknowledged": "0",
                    "clock": "1760434622",
                    "correlationid": "0",
                    "eventid": "365",
                    "name": "error318",
                    "ns": "677500047",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "RESPONSE_LIST_FLAG is incorrect.(List Type)",
                "id": 1,
                "jsonrpc": "2.0",
                "result": [
                    {
                        "acknowledged": "0",
                        "clock": "1760434622",
                        "correlationid": "0",
                        "eventid": "365",
                        "name": "error318",
                        "ns": "677500047",
                        "object": "0",
                        "objectid": "24477",
                        "opdata": "",
                        "r_clock": "0",
                        "r_eventid": "0",
                        "r_ns": "0",
                        "severity": "2",
                        "source": "0",
                        "suppressed": "0",
                        "urls": [],
                        "userid": "0"
                    },
                    {
                        "acknowledged": "0",
                        "clock": "1760434892",
                        "correlationid": "0",
                        "eventid": "366",
                        "name": "error319",
                        "ns": "766145658",
                        "object": "0",
                        "objectid": "24477",
                        "opdata": "",
                        "r_clock": "0",
                        "r_eventid": "0",
                        "r_ns": "0",
                        "severity": "2",
                        "source": "0",
                        "suppressed": "0",
                        "urls": [],
                        "userid": "0"
                    }
                ]
            }
        ]
    ),
    ## 7-異常系 - EVENT_ID_KEYの指定が間違っているので、全て既存だが、新規扱いになる
    (
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "acknowledged": "0",
                    "clock": "1760434622",
                    "correlationid": "0",
                    "eventid": "365",
                    "name": "error318",
                    "ns": "677500047",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "acknowledged": "0",
                    "clock": "1760434895",
                    "correlationid": "0",
                    "eventid": "367",
                    "name": "error320",
                    "ns": "766145699",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "1",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_problem_get",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "abc",
            "SAVED_IDS": ["365", "366", "367"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": [
                {
                    "_exastro_oase_event_id": "1760599000000",
                    "acknowledged": "0",
                    "clock": "1760434622",
                    "correlationid": "0",
                    "eventid": "365",
                    "name": "error318",
                    "ns": "677500047",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "_exastro_oase_event_id": "1760599000001",
                    "acknowledged": "0",
                    "clock": "1760434892",
                    "correlationid": "0",
                    "eventid": "366",
                    "name": "error319",
                    "ns": "766145658",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                },
                {
                    "_exastro_oase_event_id": "1760599000002",
                    "acknowledged": "0",
                    "clock": "1760434895",
                    "correlationid": "0",
                    "eventid": "367",
                    "name": "error320",
                    "ns": "766145699",
                    "object": "0",
                    "objectid": "24477",
                    "opdata": "",
                    "r_clock": "0",
                    "r_eventid": "0",
                    "r_ns": "0",
                    "severity": "2",
                    "source": "0",
                    "suppressed": "0",
                    "urls": [],
                    "userid": "0"
                }
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "EVENT_ID_KEY not found",
                "acknowledged": "0",
                "clock": "1760434622",
                "correlationid": "0",
                "eventid": "365",
                "name": "error318",
                "ns": "677500047",
                "object": "0",
                "objectid": "24477",
                "opdata": "",
                "r_clock": "0",
                "r_eventid": "0",
                "r_ns": "0",
                "severity": "2",
                "source": "0",
                "suppressed": "0",
                "urls": [],
                "userid": "0"
            },
            {
                "_exastro_oase_event_id": "1760599000001",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "EVENT_ID_KEY not found",
                "acknowledged": "0",
                "clock": "1760434892",
                "correlationid": "0",
                "eventid": "366",
                "name": "error319",
                "ns": "766145658",
                "object": "0",
                "objectid": "24477",
                "opdata": "",
                "r_clock": "0",
                "r_eventid": "0",
                "r_ns": "0",
                "severity": "2",
                "source": "0",
                "suppressed": "0",
                "urls": [],
                "userid": "0"
            },
            {
                "_exastro_oase_event_id": "1760599000002",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "EVENT_ID_KEY not found",
                "acknowledged": "0",
                "clock": "1760434895",
                "correlationid": "0",
                "eventid": "367",
                "name": "error320",
                "ns": "766145699",
                "object": "0",
                "objectid": "24477",
                "opdata": "",
                "r_clock": "0",
                "r_eventid": "0",
                "r_ns": "0",
                "severity": "2",
                "source": "0",
                "suppressed": "0",
                "urls": [],
                "userid": "0"
            }
        ]
    ),
    ## 8-異常系 - レスポンスがzabbixのエラー - 通るロジックとしては「5-異常系 - RESPONSE_KEYの指定が間違っている」と同じ
    (
        {
            "error": {
                "code": -32600,
                "data": "The received JSON is not a valid JSON-RPC request.",
                "message": "Invalid request."
            },
            "id": None,
            "jsonrpc": "2.0"
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "1",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_problem_get",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "eventid",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "error": {
                "code": -32600,
                "data": "The received JSON is not a valid JSON-RPC request.",
                "message": "Invalid request."
            },
            "id": None,
            "jsonrpc": "2.0"
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "1",
                "_exastro_event_collection_settings_name": "zabbix_problem_get",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "RESPONSE_KEY not found",
                "error": {
                    "code": -32600,
                    "data": "The received JSON is not a valid JSON-RPC request.",
                    "message": "Invalid request."
                },
                "id": None,
                "jsonrpc": "2.0"
            }
        ]
    ),
    # テストケース:レスポンスがzabbixのuser.login
    # 9-正常系 - bodyそのままを取得し、既存
    (
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": "86af10342a8fdffbff768c31ff2920ac"
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "2",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_user_login",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "result",
            "SAVED_IDS": ["86af10342a8fdffbff768c31ff2920ac"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {},
        []
    ),
    # 10-異常系 - RESPONSE_KEYから取得した結果がオブジェクトではなく文字列
    (
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": "86af10342a8fdffbff768c31ff2920ac"
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "2",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_user_login",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": ["86af10342a8fdffbff768c31ff2920ac"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "id": 1,
            "jsonrpc": "2.0",
            "result": "86af10342a8fdffbff768c31ff2920ac"
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "2",
                "_exastro_event_collection_settings_name": "zabbix_user_login",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "RESPONSE_KEY value is Invalid.(not Object and not List)",
                "id": 1,
                "jsonrpc": "2.0",
                "result": "86af10342a8fdffbff768c31ff2920ac"
            }
        ]
    ),
    # 11-異常系 - RESPONSE_LIST_FLAGの指定が間違っている（文字列なのにTrueを設定）
    (
        {
            "id": 1,
            "jsonrpc": "2.0",
            "result": "86af10342a8fdffbff768c31ff2920ac"
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "2",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_user_login",
            "RESPONSE_KEY": "result",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "eventid",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "id": 1,
            "jsonrpc": "2.0",
            "result": "86af10342a8fdffbff768c31ff2920ac"
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "2",
                "_exastro_event_collection_settings_name": "zabbix_user_login",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "RESPONSE_KEY value is Invalid.(not Object and not List)",
                "id": 1,
                "jsonrpc": "2.0",
                "result": "86af10342a8fdffbff768c31ff2920ac"
            }
        ]
    ),
    # テストケース:レスポンスがカスタム
    ## 12-正常系 - EVENT_ID_KEYがないので全て新規（SAVED_IDSあり）
    (
        {
            "events": [
                {"id": "1", "name": "event1"},
                {"id": "2", "name": "event2"},
                {"id": "3", "name": "event3"}
            ]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": ["1"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "events": [
                {"id": "1", "name": "event1","_exastro_oase_event_id": "1760599000000"},
                {"id": "2", "name": "event2", "_exastro_oase_event_id": "1760599000001"},
                {"id": "3", "name": "event3", "_exastro_oase_event_id": "1760599000002"}
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "id": "1",
                "name": "event1"
            },
            {
                "_exastro_oase_event_id": "1760599000001",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "id": "2",
                "name": "event2"
            },
            {
                "_exastro_oase_event_id": "1760599000002",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "id": "3",
                "name": "event3"
            }
        ]
    ),
    ## 13-正常系 - 中身が空オブジェクト_1
    (
        {},
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": None,
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {},
        []
    ),
    ## 14-正常系 - 中身が空オブジェクト_2
    (
        {
            "event": {}
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "event",
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["1"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "event": {}
        },
        []
    ),
    ## 15-異常系 - 空オブジェクト_3
    (
        {},
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["1"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000"
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "RESPONSE_LIST_FLAG is incorrect.(Not List Type)",
            }
        ]
    ),
    ## 16-正常系 - 空オブジェクト_4（リストの中に空オブジェクト）
    (
        {
            "events": [{}]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "events": [
                {
                    "_exastro_oase_event_id": "1760599000000"
                }
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
            }
        ]
    ),
    ## 17-正常系 - 取れたが、中身が空リスト_1
    (
        [],
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        [],
        []
    ),
    ## 18-異常系 - 中身が空リスト_2
    (
        {
            "events": []
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "events": []
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "RESPONSE_LIST_FLAG is incorrect.(List Type)",
                "events": []
            }
        ]
    ),
    ## 19-正常系 - 取れたが、空文字
    (
        "",
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        "",
        []
    ),
    ## 20-異常系 - 取れたが、中身が文字列
    (
        "message",
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "_exastro_raw_data": "message"
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": "message"
            }
        ]
    ),
    ## 21-異常系 - 取れたが、中身が配列の中に文字列
    (
        ["status", "error"],
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_raw_data": "status"
            },
            {
                "_exastro_oase_event_id": "1760599000001",
                "_exastro_raw_data": "error"
            }
        ],
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": "status"
            },
            {
                "_exastro_oase_event_id": "1760599000001",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": "error"
            }
        ]
    ),
    ## 22-正常系 - idが数値(新規)
    (
        {"status": "error", "id": 123},
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {"status": "error", "id": 123, "_exastro_oase_event_id": "123"},
        [
            {
                "_exastro_oase_event_id": "123",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "status": "error",
                "id": 123
                }
        ]
    ),
    ## 23-正常系 - idが数値(既存)
    (
        {"status": "error", "id": 123},
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["123"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {},
        []
    ),
    ## 24-正常系 - idが空白が含まれる文字列
    (
        {"status": "error", "last_update_timestamp": "2025-10-15 17:17:03.111583"},
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "last_update_timestamp",
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {"status": "error", "last_update_timestamp": "2025-10-15 17:17:03.111583", "_exastro_oase_event_id": "2025-10-15 17:17:03.111583"},
        [
            {
                "_exastro_oase_event_id": "2025-10-15 17:17:03.111583",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "status": "error",
                "last_update_timestamp": "2025-10-15 17:17:03.111583"
            }
        ]
    ),
    ## 25-正常系 - idが配列
    (
        {"msg": ["error1", "error2"], "last_update_timestamp": "2025-10-15 17:17:03.111583"},
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "msg",
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {"msg": ["error1", "error2"], "last_update_timestamp": "2025-10-15 17:17:03.111583", "_exastro_oase_event_id": "['error1', 'error2']"},
        [
            {
                "_exastro_oase_event_id": "['error1', 'error2']",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "msg": ["error1", "error2"],
                "last_update_timestamp": "2025-10-15 17:17:03.111583"
            }
        ]
    ),
    ## 26-正常系 - 直下がリスト（新規・既存）
    (
        [
            {
                "id": "001"
            },
            {
                "id": "002"
            }
        ],
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["001"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        [
            {
                "_exastro_oase_event_id": "002",
                "id": "002"
            }
        ],
        [
            {
                "_exastro_oase_event_id": "002",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "id": "002"
            }
        ]
    ),
    ## 27-正常系 - オブジェクトの中にオブジェクト（新規）
    (
        {
            "events": {
                "id": "1001",
                "detail": {
                    "type": "error",
                    "message": "disk full"
                }
            }
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["1000"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "events": {
                "_exastro_oase_event_id": "1001",
                "id": "1001",
                "detail": {
                    "type": "error",
                    "message": "disk full"
                }
            }
        },
        [
            {
                "_exastro_oase_event_id": "1001",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "id": "1001",
                "detail": {
                    "type": "error",
                    "message": "disk full"
                }
            }
        ]
    ),
    ## 28-正常系 - オブジェクトの中にオブジェクト（既存）
    (
        {
            "events": {
                "id": "1001",
                "detail": {
                    "type": "error",
                    "message": "disk full"
                }
            }
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["1001"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "events": {}
        },
        []
    ),
    ## 29-正常系 - オブジェクトの中にオブジェクト（既存）※jmespathのチェックをかねる
    (
        {
            "events": [
                {
                    "id": "1001",
                    "type": "error"
                },
                {
                    "id": "1002",
                    "type": "warning"
                }
            ]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events[0]",
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["1001"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "events": [
                {},
                {
                    "id": "1002",
                    "type": "warning"
                }
            ]
        },
        []
    ),
    ## 30-異常系 - オブジェクトの中にidが存在しない
    (
        {
            "events": {
                "id": "1001",
                "detail": {
                    "type": "error",
                    "message": "disk full"
                }
            }
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "uid",
            "SAVED_IDS": ["1001"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "events": {
                "_exastro_oase_event_id": "1760599000000",
                "id": "1001",
                "detail": {
                    "type": "error",
                    "message": "disk full"
                }
            }
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "EVENT_ID_KEY not found",
                "id": "1001",
                "detail": {
                    "type": "error",
                    "message": "disk full"
                }
            }
        ]
    ),
    ## 31-異常系 - リストだが、オブジェクトを指定
    (
        [
            {
                "id": "1001",
                "type": "error"
            },
            {
                "id": "1002",
                "type": "warning"
            }
        ],
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["1001"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "_exastro_raw_data": [
                {
                    "id": "1001",
                    "type": "error"
                },
                {
                    "id": "1002",
                    "type": "warning"
                }
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": [
                    {
                        "id": "1001",
                        "type": "error"
                    },
                    {
                        "id": "1002",
                        "type": "warning"
                    }
                ]
            }
        ]
    ),
    ## 32-異常系 -リストの中に空文字
    (
        {
            "events": [""]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "events": [
                {
                    "_exastro_oase_event_id": "1760599000000",
                    "_exastro_raw_data": ""
                }
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": ""
            }
        ]
    ),
    ## 33-正常系 - 取れたが、空文字
    (
        {
            "events": ""
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "events": ""
        },
        []
    ),
    ## 34-正常系 - オブジェクトの中にオブジェクト（新規）
    (
        {
            "events": {
                "id": "1001",
                "detail": {
                    "type": "error",
                    "message": "disk full"
                }
            }
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": ["1001"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "events": {
                "_exastro_oase_event_id": "1760599000000",
                "id": "1001",
                "detail": {
                    "type": "error",
                    "message": "disk full"
                }
            }
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "id": "1001",
                "detail": {
                    "type": "error",
                    "message": "disk full"
                }
            }
        ]
    ),
    ## 35-正常系 - リストの中に空オブジェクト
    (
        [{}],
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": ["1760599000000"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000"
            }
        ],
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
            }
        ]
    ),
    ## 36-正常系 - オブジェクトの中にオブジェクト（新規）
    (
        {
            "id": "1001",
            "detail": {
                "type": "error",
                "message": "disk full"
            }
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": ["1001"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "id": "1001",
            "detail": {
                "type": "error",
                "message": "disk full"
            }
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "id": "1001",
                "detail": {
                    "type": "error",
                    "message": "disk full"
                }
            }
        ]
    ),
    # 37-異常系 - RESPONSE_LIST_FLAGの指定が間違っている（空文字）
    (
        {
            "events": {}
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "2",
            "EVENT_COLLECTION_SETTINGS_NAME": "zabbix_user_login",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["365"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "events": {
                "_exastro_oase_event_id": "1760599000000"
            }
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "2",
                "_exastro_event_collection_settings_name": "zabbix_user_login",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "RESPONSE_LIST_FLAG is incorrect.(Not List Type)",
            }
        ]
    ),
    ## 38-異常系 - リストだが、オブジェクトを指定
    (
        {
            "events": [
                {
                    "id": "1001",
                    "type": "error"
                },
                {
                    "id": "1002",
                    "type": "warning"
                }
            ]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["1001"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "events": [
                {
                    "id": "1001",
                    "type": "error"
                },
                {
                    "id": "1002",
                    "type": "warning"
                }
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "RESPONSE_LIST_FLAG is incorrect.(List Type)",
                "events": [
                    {
                        "id": "1001",
                        "type": "error"
                    },
                    {
                        "id": "1002",
                        "type": "warning"
                    }
                ]
            }
        ]
    ),
    ## 39-異常系 - リストの中に空オブジェクト
    (
        {
            "events": [{}]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "events",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["100"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "events": [
                {
                    "_exastro_oase_event_id": "1760599000000"
                }
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "EVENT_ID_KEY not found"
            }
        ]
    ),
    ## 40-異常系 -リストの中に文字列
    (
        {
            "message": ["error1", "error2"]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "message",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": ["error1"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "message": [
                {
                    "_exastro_oase_event_id": "1760599000000",
                    "_exastro_raw_data": "error1"
                },
                {
                    "_exastro_oase_event_id": "1760599000001",
                    "_exastro_raw_data": "error2"
                },
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": "error1"
            },
            {
                "_exastro_oase_event_id": "1760599000001",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": "error2"
            }
        ]
    ),
    ## 40-異常系 -リストの中にリスト
    (
        {
            "message": [["error1", "error2"], ["error3", "error4", "error5"]]
        },
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": "message",
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": ["error1"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "message": [
                {
                    "_exastro_oase_event_id": "1760599000000",
                    "_exastro_raw_data": ["error1", "error2"]
                },
                {
                    "_exastro_oase_event_id": "1760599000001",
                    "_exastro_raw_data": ["error3", "error4", "error5"]
                },
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": ["error1", "error2"]
            },
            {
                "_exastro_oase_event_id": "1760599000001",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": ["error3", "error4", "error5"]
            }
        ]
    ),
    ## 42-異常系 - 文字列
    (
        "error is occured",
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["1"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "_exastro_raw_data": "error is occured"
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": "error is occured"
            }
        ]
    ),
    ## 43-異常系 - リストだが、オブジェクトを指定（空オブジェクト）
    (
        [
            {}
        ],
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["1001"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "_exastro_raw_data": [
                {}
            ]
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": [
                    {}
                ]
            }
        ]
    ),
    ## 44-異常系 - リストだが、オブジェクトを指定（空リスト）
    (
        [],
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "id",
            "SAVED_IDS": ["1001"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "_exastro_raw_data": []
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": []
            }
        ]
    ),
    ## 45-異常系 - EVENT_ID_KEYがない
    (
        [
            {
                "id": "001"
            },
            {
                "id": "002"
            }
        ],
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": "uid",
            "SAVED_IDS": ["001"],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "id": "001"
            },
            {
                "_exastro_oase_event_id": "1760599000001",
                "id": "002"
            }
        ],
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "EVENT_ID_KEY not found",
                "id": "001"
            },
            {
                "_exastro_oase_event_id": "1760599000001",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "EVENT_ID_KEY not found",
                "id": "002"
            }
        ]
    ),
    ## 46-異常系 - 取れたが、中身が配列の中に配列
    (
        [["error1", "error2"], ["error3", "error4", "error5"]],
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "1",
            "EVENT_ID_KEY": None,
            "SAVED_IDS": ['["error1", "error2"]'],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_raw_data": ["error1", "error2"]
            },
            {
                "_exastro_oase_event_id": "1760599000001",
                "_exastro_raw_data": ["error3", "error4", "error5"]
            }
        ],
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": ["error1", "error2"]
            },
            {
                "_exastro_oase_event_id": "1760599000001",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "event format is Invalid.(not Object)",
                "_exastro_raw_data": ["error3", "error4", "error5"]
            }
        ]
    ),
    ## 47-異常系 - EVENT_ID_KEYがない
    (
        {"status": "error", "id": 123},
        {
            "EVENT_COLLECTION_SETTINGS_ID": "3",
            "EVENT_COLLECTION_SETTINGS_NAME": "custom_simple_json",
            "RESPONSE_KEY": None,
            "RESPONSE_LIST_FLAG": "0",
            "EVENT_ID_KEY": "uid",
            "SAVED_IDS": [],
            "LAST_FETCHED_TIMESTAMP": 1760599000,
            "TTL": 180
        },
        {
            "_exastro_oase_event_id": "1760599000000",
            "id": 123,
            "status": "error"},
        [
            {
                "_exastro_oase_event_id": "1760599000000",
                "_exastro_event_collection_settings_id": "3",
                "_exastro_event_collection_settings_name": "custom_simple_json",
                "_exastro_fetched_time": 0,
                "_exastro_end_time": 180,
                "_exastro_not_available": "EVENT_ID_KEY not found",
                "status": "error",
                "id": 123
            }
        ]
    ),
]

@pytest.mark.parametrize(
    "api_response_raw_json, dummy_setting, expected_response_json, expected_response", test_response_parameters
)

def test_get_new_events(api_response_raw_json, dummy_setting, expected_response_json, expected_response):
    """
    get_new_eventsメソッドのパラメータ化テスト
    """
    # 必要な設定を追加(zabbix_problem_get用)
    dummy_setting.update({
        "EVENT_COLLECTION_SETTINGS_ID": "41086c31-6c24-41f2-aa30-741082642bfc",
        "URL": "http://dummy.hoge.com/api_jsonrpc.php",
        "PORT": None,
        "PROXY": None,
        "CONNECTION_METHOD_ID": "5",
        "REQUEST_METHOD_ID": "2",
        "REQUEST_HEADER": "{ \"content-type\" : \"application/json-rpc\" }",
        "AUTH_TOKEN": "u/9aLZZSn5Ua66S+a/B6UThxcCBQ88nRNv/yGhaBmvJ8eErXN09WZJxTkXAdBmJp6WYwwn",
        "USERNAME": "",
        "PASSWORD": "",
        "ACCESS_KEY_ID": "",
        "SECRET_ACCESS_KEY": "",
        "MAILBOXNAME": "",
        "PARAMETER": "{\n    \"jsonrpc\": \"2.0\",\n    \"method\": \"problem.get\",\n    \"params\": {\n        \"output\": \"extend\",\n        {% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}\n          \"eventid_from\": \"{{ EXASTRO_LAST_FETCHED_EVENT.eventid|int + 1  }}\"\n        {% else %}\n          \"time_from\": \"{{ EXASTRO_LAST_FETCHED_TIMESTAMP }}\"\n        {% endif %}\n    },\n  \"auth\": \"{{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN }}\",\n  \"id\": 1\n}",
        "TTL": 60,
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
    result_json = client.get_new_events(api_response_raw_json, now_time)

    # テスト結果の検証
    assert result_json == expected_response_json  # 新規イベントのリストを確認