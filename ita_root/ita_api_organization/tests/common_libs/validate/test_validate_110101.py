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
from common_libs.validate.valid_110101 import agent_setting_valid
from common_libs.validate.valid_110101 import is_use_jinja2_variable
from common_libs.validate.valid_110101 import is_jinja2_template

app = Flask(__name__)


class DummyAppMsg:
    def get_api_message(self, code, args=None):
        return code


@pytest.fixture(autouse=True)
def setup_g(monkeypatch):
    with app.app_context():
        # セットアップ処理
        g.appmsg = DummyAppMsg()
        g.LANGUAGE = "ja"
        yield  # ここでテスト本体が実行される


class DummyObjDbca:
    def table_select(self, table, where, params):
        # T_OASE_CONNECTION_METHOD用
        if table == "T_OASE_CONNECTION_METHOD":
            return [{"CONNECTION_METHOD_NAME_JA": "Bearer認証", "CONNECTION_METHOD_NAME_EN": "Bearer Auth"}]
        # T_OASE_EVENT_COLLECTION_SETTINGS用
        if table == "T_OASE_EVENT_COLLECTION_SETTINGS":
            return [{"CONNECTION_METHOD_ID": "1"}]
        return []


@pytest.mark.parametrize(
    "connection_method, request_method, username, password, auth_token, secret_access_key, access_key_id,"
    "request_header, parameter, expected_bool, expected_msgs",
    [
        # IMAPパスワード（接続方式4）※JSON/jinja2判定なし
        ("4", "3", "user", "password", None, None, None, None, None, True, []),

        # エージェント不使用（接続方式99）※JSON/jinja2判定なし
        ("99", None, None, None, None, None, None, None, None, True, []),

        # Bearer認証（接続方式1）
        #  ヘッダーのテスト
        # 　正常なjinja2
        ("1", "1", None, None, "token", None, None, '{ "key": "{{ header_var }}" }', None, True, []),
        #   不正なjinja2構文 （制御構文の閉じタグがない）
        ("1", "1", None, None, "token", None, None, '{% if value %}True', None, False, ["499-01815"]),
        #   正常なJSON
        ("1", "1", None, None, "token", None, None, '{"key": "value"}', None, True, []),
        #   不正なjinja2構文 (カンマ抜け)
        ("1", "1", None, None, "token", None, None, '{"key": "value" "key2": "value2"}', None, False, ["MSG-120011"]),
        #   空文字（JSON扱いになり、不正扱い）
        ("1", "1", None, None, "token", None, None, '', None, False, ["MSG-120011"]),
        #   None（正常扱い）
        ("1", "1", None, None, "token", None, None, None, None, True, []),
        # パラメーターのテスト
        #  正常なjinja2
        ("1", "1", None, None, "token", None, None, None, '{ "key": "{{ header_var }}" }', True, []),
        #  不正なjinja2構文 （制御構文の閉じタグがない）
        ("1", "1", None, None, "token", None, None, None, '{% if value %}True', False, ["499-01815"]),
        #  正常なJSON
        ("1", "1", None, None, "token", None, None, None, '{"key": "value"}', True, []),
        #  不正なjinja2構文 (カンマ抜け)
        ("1", "1", None, None, "token", None, None, None, '{"key": "value" "key2": "value2"}', False, ["MSG-120012"]),
        #  空文字（JSON扱いになり、不正扱い）
        ("1", "1", None, None, "token", None, None, None, '', False, ["MSG-120012"]),
        #  None（正常扱い）
        ("1", "1", None, None, "token", None, None, None, None, True, []),

        # Basic認証（接続方式2）
        #  ヘッダーのテスト
        # 　正常なjinja2
        ("2", "1", "user", "pass", None, None, None, '{ "key": "{{ header_var }}" }', None, True, []),
        #   不正なjinja2構文 （制御構文の閉じタグがない）
        ("2", "1", "user", "pass", None, None, None, '{% if value %}True', None, False, ["499-01815"]),
        #   正常なJSON
        ("2", "1", "user", "pass", None, None, None, '{"key": "value"}', None, True, []),
        #   不正なjinja2構文 (カンマ抜け)
        ("2", "1", "user", "pass", None, None, None, '{"key": "value" "key2": "value2"}', None, False, ["MSG-120011"]),
        #   空文字（JSON扱いになり、不正扱い）
        ("2", "1", "user", "pass", None, None, None, '', None, False, ["MSG-120011"]),
        #   None（正常扱い）
        ("2", "1", "user", "pass", None, None, None, None, None, True, []),
        # パラメーターのテスト
        #  正常なjinja2
        ("2", "1", "user", "pass", None, None, None, None, '{ "key": "{{ header_var }}" }', True, []),
        #  不正なjinja2構文 （制御構文の閉じタグがない）
        ("2", "1", "user", "pass", None, None, None, None, '{% if value %}True', False, ["499-01815"]),
        #  正常なJSON
        ("2", "1", "user", "pass", None, None, None, None, '{"key": "value"}', True, []),
        #  不正なjinja2構文 (カンマ抜け)
        ("2", "1", "user", "pass", None, None, None, None, '{"key": "value" "key2": "value2"}', False, ["MSG-120012"]),
        #  空文字（JSON扱いになり、不正扱い）
        ("2", "1", "user", "pass", None, None, None, None, '', False, ["MSG-120012"]),
        #  None（正常扱い）
        ("2", "1", "user", "pass", None, None, None, None, None, True, []),

        # 共有鍵認証（接続方式3）
        #  ヘッダーのテスト
        # 　正常なjinja2
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", '{ "key": "{{ header_var }}" }', None, True, []),
        #   不正なjinja2構文 （制御構文の閉じタグがない）
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", '{% if value %}True', None, False, ["499-01815"]),
        #   正常なJSON
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", '{"key": "value"}', None, True, []),
        #   不正なjinja2構文 (カンマ抜け)
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", '{"key": "value" "key2": "value2"}', None, False, ["MSG-120011"]),
        #   空文字（JSON扱いになり、不正扱い）
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", '', None, False, ["MSG-120011"]),
        #   None（正常扱い）
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", None, None, True, []),
        # パラメーターのテスト
        #  正常なjinja2
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", None, '{ "key": "{{ header_var }}" }', True, []),
        #  不正なjinja2構文 （制御構文の閉じタグがない）
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", None, '{% if value %}True', False, ["499-01815"]),
        #  正常なJSON
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", None, '{"key": "value"}', True, []),
        #  不正なjinja2構文 (カンマ抜け)
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", None, '{"key": "value" "key2": "value2"}', False, ["MSG-120012"]),
        #  空文字（JSON扱いになり、不正扱い）
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", None, '', False, ["MSG-120012"]),
        #  None（正常扱い）
        ("3", "1", None, None, None, "secret_access_key", "access_key_id", None, None, True, []),

        # オプション認証（接続方式5）
        #  ヘッダーのテスト
        # 　正常なjinja2
        ("5", "1", None, None, None, None, None, '{ "key": "{{ header_var }}" }', None, True, []),
        #   不正なjinja2構文 （制御構文の閉じタグがない）
        ("5", "1", None, None, None, None, None, '{% if value %}True', None, False, ["499-01815"]),
        #   正常なJSON
        ("5", "1", None, None, None, None, None, '{"key": "value"}', None, True, []),
        #   不正なjinja2構文 (カンマ抜け)
        ("5", "1", None, None, None, None, None, '{"key": "value" "key2": "value2"}', None, False, ["MSG-120011"]),
        #   空文字（JSON扱いになり、不正扱い）
        ("5", "1", None, None, None, None, None, '', None, False, ["MSG-120011"]),
        #   None（正常扱い）
        ("5", "1", None, None, None, None, None, None, None, True, []),
        # パラメーターのテスト
        #  正常なjinja2
        ("5", "1", None, None, None, None, None, None, '{ "key": "{{ header_var }}" }', True, []),
        #  不正なjinja2構文 （制御構文の閉じタグがない）
        ("5", "1", None, None, None, None, None, None, '{% if value %}True', False, ["499-01815"]),
        #  正常なJSON
        ("5", "1", None, None, None, None, None, None, '{"key": "value"}', True, []),
        #  不正なjinja2構文 (カンマ抜け)
        ("5", "1", None, None, None, None, None, None, '{"key": "value" "key2": "value2"}', False, ["MSG-120012"]),
        #  空文字（JSON扱いになり、不正扱い）
        ("5", "1", None, None, None, None, None, None, '', False, ["MSG-120012"]),
        #  None（JSON扱いになり、正常扱い）
        ("5", "1", None, None, None, None, None, None, None, True, [])
    ]
)
def test_agent_setting_valid(connection_method, request_method,
                             username, password, auth_token, secret_access_key, access_key_id,
                             request_header, parameter, expected_bool, expected_msgs):
    """
    connection_method別にJinja2バリデーションを実行し、
    期待するメッセージが返ることを確認
    """
    objdbca = DummyObjDbca()
    objtable = {
        "COLINFO": {
            "request_header": {"COLUMN_NAME_JA": "リクエストヘッダー"},
            "parameter": {"COLUMN_NAME_JA": "パラメータ"}
        }
    }
    option = {
        "cmd_type": "Register",
        "entry_parameter": {
            "parameter": {
                "connection_method_name": connection_method,
                "url": "http://dummy",
                "request_method_name": request_method,
                "username": username,
                "password": password,
                "auth_token": auth_token,
                "secret_access_key": secret_access_key,
                "access_key_id": access_key_id,
                "request_header": request_header,
                "parameter": parameter,
                "event_collection_settings_id": "1"
            }
        }
    }
    retBool, msg, _ = agent_setting_valid(objdbca, objtable, option)
    assert retBool == expected_bool
    for expected_msg in expected_msgs:
        assert expected_msg in msg


@pytest.mark.parametrize(
    "template_data_decoded, expected",
    [
        # jinja2変数（{{ variable }}）が含まれる場合
        ("{{ my_var }}", True),
        # jinja2制御構文（{% if ... %}）が含まれる場合
        ("{% if value %}True{% endif %}", True),
        # jinja2変数（空白あり）
        ("{{  my_var  }}", True),
        # jinja2制御構文（空白あり）
        ("{%  for item in list %}{{ item }}{% endfor %}", True),
        # jinja2構文が含まれない場合
        ("これは通常の文字列です", False),
        # 似ているがjinja2構文でない場合
        ("{ my_var }", False),
        # 空文字
        ("", False),
        # jinja2構文と通常文字列混在
        ("abc {{ var }} def", True),
    ]
)
def test_is_use_jinja2_variable(template_data_decoded, expected):
    """
    jinja2の構文が使われているかをチェックする関数のテスト
    """
    assert is_use_jinja2_variable(template_data_decoded) == expected


def raises_jinja2_template_error_with_none(func):
    """
    例外が発生することをテストするための関数
    """
    with pytest.raises(TypeError):
        func(None)


def test_jinja2_template_none():
    """
    jinja2の構文が使われているかをチェックする関数にNoneを渡した場合の例外発生テスト
    """
    import jinja2
    raises_jinja2_template_error_with_none(jinja2.Template)
        

@pytest.mark.parametrize(
    "template_data_decoded, expected",
    [
        # 正常なjinja2テンプレート
        ("{{ my_var }}", True),
        ("{% if value %}True{% endif %}", True),
        ("Hello {{ name }}!", True),
        # 不正なjinja2テンプレート（構文エラー）
        ("{{ my_var ", False),
        ("{% if value %}True", False),
        ("{{", False),
        # 通常の文字列（jinja2構文なしでもTrueになる場合あり）
        ("これは通常の文字列です", True),
        # 空文字（正常）
        ("", True),
        # None （不正）
        (None, False),
    ]
)
def test_is_jinja2_template(template_data_decoded, expected):
    """
    jinja2のテンプレートとして問題無いかチェックする関数のテスト
    """
    assert is_jinja2_template(template_data_decoded) == expected