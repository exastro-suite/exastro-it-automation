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
"""
tools/platform_user.py (list-users / create-user) のユニットテスト

異常系では、g.applogger.info の呼び出し回数はチェックしない
(ログ出力を増減しただけでテストが壊れるのは望ましくないため)。
代わりに、送出される例外のメッセージ・ステータスコードで検証する。
"""

from unittest import mock

import pytest
from flask import g

from tools import platform_user


@pytest.fixture
def platform_env(monkeypatch):
    """PLATFORM_API_HOST / PLATFORM_API_PORT 環境変数を固定する"""
    monkeypatch.setenv("PLATFORM_API_HOST", "platform-host")
    monkeypatch.setenv("PLATFORM_API_PORT", "8080")


def _expected_url(organization_id):
    return "http://platform-host:8080/api/{}/platform/users".format(organization_id)


class TestToolListUsers:
    def test_list_users_success(self, mock_flask_g, platform_env, requests_mock):
        # 正常系: 200応答時にAPIのレスポンスがそのままresultに入り、
        # message / organization_id が正しく設定されること
        organization_id = "org-1"
        api_response = {"users": [{"username": "alice"}, {"username": "bob"}]}
        requests_mock.get(_expected_url(organization_id), json=api_response, status_code=200)

        result = platform_user.tool_list_users({}, {"organization_id": organization_id})

        assert result["result"] == api_response
        assert result["message"] == "User list fetched successfully."
        assert result["organization_id"] == organization_id

    def test_list_users_request_url_and_headers(self, mock_flask_g, platform_env, requests_mock):
        # 正常系: 呼び出し先URLが環境変数から正しく組み立てられ、
        # ヘッダーが転送されること(GETなのでContent-Typeは付与されない)
        organization_id = "org-2"
        requests_mock.get(_expected_url(organization_id), json={}, status_code=200)

        platform_user.tool_list_users({}, {"organization_id": organization_id})

        last_request = requests_mock.last_request
        assert last_request.url == _expected_url(organization_id)
        assert last_request.method == "GET"
        assert "Content-Type" not in last_request.headers

    def test_list_users_forwards_incoming_headers(self, app, platform_env, requests_mock):
        # 正常系: 受信した User-Id / Roles / Org-Roles ヘッダーがそのまま
        # ダウンストリームAPIへ転送されること
        organization_id = "org-3"
        requests_mock.get(_expected_url(organization_id), json={}, status_code=200)

        with app.test_request_context(
            headers={"User-Id": "user-42", "Roles": "role-abc", "Org-Roles": "org-role-xyz"}
        ):
            g.applogger = mock.Mock()
            g.applogger.info = mock.Mock()
            g.LANGUAGE = "en"

            platform_user.tool_list_users({}, {"organization_id": organization_id})

        last_request = requests_mock.last_request
        assert last_request.headers["User-Id"] == "user-42"
        assert last_request.headers["Roles"] == "role-abc"
        assert last_request.headers["Org-Roles"] == "org-role-xyz"

    def test_list_users_http_error_raises(self, mock_flask_g, platform_env, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが
        # 発生し、そのメッセージ・ステータスコードが応答内容から組み立てられること
        organization_id = "org-4"
        requests_mock.get(
            _expected_url(organization_id),
            json={"message": "Internal error", "result": "db_error"},
            status_code=500,
        )

        with pytest.raises(platform_user.HTTPException) as exc_info:
            platform_user.tool_list_users({}, {"organization_id": organization_id})

        assert exc_info.value.status_code == 500
        assert str(exc_info.value) == "Internal error (db_error)"
        assert exc_info.value.tool_name == "list-users"

    def test_list_users_http_error_without_json_body(self, mock_flask_g, platform_env, requests_mock):
        # 異常系: レスポンスボディがJSONとして解釈できない場合でも例外が発生し、
        # tool_nameとstatus_codeからメッセージが組み立てられること
        organization_id = "org-5"
        requests_mock.get(
            _expected_url(organization_id),
            text="not json",
            status_code=503,
        )

        with pytest.raises(platform_user.HTTPException) as exc_info:
            platform_user.tool_list_users({}, {"organization_id": organization_id})

        assert exc_info.value.status_code == 503
        assert str(exc_info.value) == "list-users failed: HTTP 503"

    def test_list_users_missing_organization_id(self, mock_flask_g, platform_env, requests_mock):
        # 境界値: payloadにorganization_idが無い場合はNoneとしてURLに組み込まれること
        requests_mock.get(_expected_url("None"), json={"users": []}, status_code=200)

        result = platform_user.tool_list_users({}, {})

        assert result["organization_id"] is None
        assert result["result"] == {"users": []}


class TestToolCreateUser:
    def test_create_user_success(self, mock_flask_g, platform_env, requests_mock):
        # 正常系: 200応答時にAPIのレスポンスがそのままresultに入り、
        # message / organization_id が正しく設定されること
        organization_id = "org-1"
        api_response = {"username": "newuser", "id": "u-100"}
        requests_mock.post(_expected_url(organization_id), json=api_response, status_code=200)

        arguments = {"username": "newuser", "password": "s3cr3t", "email": "newuser@example.com"}
        result = platform_user.tool_create_user(arguments, {"organization_id": organization_id})

        assert result["result"] == api_response
        assert result["message"] == "User created successfully."
        assert result["organization_id"] == organization_id

    def test_create_user_request_body_and_headers(self, mock_flask_g, platform_env, requests_mock):
        # 正常系: 引数からユーザー情報が正しく組み立てられてPOSTボディに
        # 含まれること、およびPOSTなのでContent-Typeヘッダーが付与されること
        organization_id = "org-2"
        requests_mock.post(_expected_url(organization_id), json={}, status_code=200)

        arguments = {"username": "bob", "password": "pw", "email": "bob@example.com"}
        platform_user.tool_create_user(arguments, {"organization_id": organization_id})

        last_request = requests_mock.last_request
        sent_body = last_request.json()
        assert sent_body["username"] == "bob"
        assert sent_body["password"] == "pw"
        assert sent_body["email"] == "bob@example.com"
        assert sent_body["password_temporary"] is True
        assert sent_body["enabled"] is True
        assert sent_body["firstName"] == ""
        assert sent_body["lastName"] == ""
        assert sent_body["affiliation"] == ""
        assert sent_body["description"] == ""
        assert last_request.headers["Content-Type"] == "application/json"

    def test_create_user_missing_arguments_default_to_empty_string(
        self, mock_flask_g, platform_env, requests_mock
    ):
        # 境界値: argumentsにusername/password/emailが無い場合、
        # それぞれ空文字として送信されること
        organization_id = "org-3"
        requests_mock.post(_expected_url(organization_id), json={}, status_code=200)

        platform_user.tool_create_user({}, {"organization_id": organization_id})

        sent_body = requests_mock.last_request.json()
        assert sent_body["username"] == ""
        assert sent_body["password"] == ""
        assert sent_body["email"] == ""

    def test_create_user_http_error_raises(self, mock_flask_g, platform_env, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが
        # 発生し、そのメッセージ・ステータスコードが応答内容から組み立てられること
        organization_id = "org-4"
        requests_mock.post(
            _expected_url(organization_id),
            json={"message": "Username already exists"},
            status_code=400,
        )

        arguments = {"username": "dup", "password": "pw", "email": "dup@example.com"}
        with pytest.raises(platform_user.HTTPException) as exc_info:
            platform_user.tool_create_user(arguments, {"organization_id": organization_id})

        assert exc_info.value.status_code == 400
        assert str(exc_info.value) == "Username already exists"
        assert exc_info.value.tool_name == "create-user"

    def test_create_user_http_error_without_message_or_json(
        self, mock_flask_g, platform_env, requests_mock
    ):
        # 異常系: レスポンスボディがJSONとして解釈できず、message/resultも
        # 無い場合、tool_nameとstatus_codeからメッセージが組み立てられること
        organization_id = "org-5"
        requests_mock.post(
            _expected_url(organization_id),
            text="internal server error",
            status_code=500,
        )

        arguments = {"username": "x", "password": "pw", "email": "x@example.com"}
        with pytest.raises(platform_user.HTTPException) as exc_info:
            platform_user.tool_create_user(arguments, {"organization_id": organization_id})

        assert exc_info.value.status_code == 500
        assert str(exc_info.value) == "create-user failed: HTTP 500"
