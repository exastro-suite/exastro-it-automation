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
libs/mcp_server_common.py (before_request_handler) のURL判定に関するユニットテスト

api.app のテストクライアント経由で before_request_handler を通す。
ログ・メッセージ・DB接続を伴う共通処理は mocker.patch で差し替える。
"""
import base64

import pytest

import api

ORG_ID = "org1"
WS_ID = "ws1"


@pytest.fixture
def client(mocker):
    mocker.patch("libs.mcp_server_common.set_api_timestamp")
    mocker.patch("libs.mcp_server_common.get_api_timestamp", return_value="ts")
    mocker.patch("libs.mcp_server_common.AppLog")
    mocker.patch("libs.mcp_server_common.MessageTemplate")
    mocker.patch("libs.mcp_server_common.set_service_loglevel")
    mocker.patch("libs.mcp_server_common.check_request_body")
    api.app.config["TESTING"] = True
    return api.app.test_client()


def _auth_headers():
    return {
        "User-Id": "user-1",
        "Roles": base64.b64encode("_ws1-admin".encode()).decode(),
    }


class TestBeforeRequestHandlerUrlResolution:
    @pytest.mark.parametrize("path", ["/", "/mcp", "/rpc"])
    def test_url_without_org_ws_returns_400_fallback(self, client, mocker, path):
        # 異常系: organization_id/workspace_idを含まないURLでも500にならず、
        # api.pyのフォールバックによるJSON-RPCエラー(400, -32600)が返ること
        mock_driver_check = mocker.patch("libs.mcp_server_common._is_ai_assistant_driver_enabled")

        res = client.post(path, json={"jsonrpc": "2.0", "method": "tools/list", "id": 7})

        assert res.status_code == 400
        body = res.get_json()
        assert body["error"]["code"] == -32600
        assert body["id"] == 7
        mock_driver_check.assert_not_called()

    @pytest.mark.parametrize("path", ["/api", "/api/org1", "/api/org1/workspaces", "/unknown/path"])
    def test_unknown_url_returns_404(self, client, mocker, path):
        # 異常系: パス階層が足りないURLや未定義のURLは500にならず404が返ること
        mocker.patch("libs.mcp_server_common._is_ai_assistant_driver_enabled")

        res = client.post(path, json={"jsonrpc": "2.0", "method": "tools/list", "id": 1})

        assert res.status_code == 404

    def test_org_ws_url_resolves_ids_into_payload(self, client, mocker):
        # 正常系: "/api/<org>/workspaces/<ws>/mcp" のURLから
        # organization_id/workspace_idが取得され、payloadに渡されること
        mocker.patch("libs.mcp_server_common._is_ai_assistant_driver_enabled", return_value=True)
        captured = {}

        def _fake_handler(params, payload):
            captured.update(payload)
            return {"tools": []}

        mocker.patch.dict(api.JSONRPC_METHODS, {"tools/list": _fake_handler})

        res = client.post(
            "/api/{}/workspaces/{}/mcp".format(ORG_ID, WS_ID),
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers=_auth_headers(),
        )

        assert res.status_code == 200
        assert captured["organization_id"] == ORG_ID
        assert captured["workspace_id"] == WS_ID
        assert captured["user_id"] == "user-1"

    def test_org_ws_url_with_disabled_driver_returns_403(self, client, mocker):
        # 異常系: ai_assistantドライバが無効なオーガナイゼーションでは403が返ること
        mocker.patch("libs.mcp_server_common._is_ai_assistant_driver_enabled", return_value=False)

        res = client.post(
            "/api/{}/workspaces/{}/mcp".format(ORG_ID, WS_ID),
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers=_auth_headers(),
        )

        assert res.status_code == 403

    @pytest.mark.parametrize("user_id", [None, ""])
    def test_missing_or_empty_user_id_is_rejected(self, client, mocker, user_id):
        # 異常系: User-Idヘッダーが無い、または空文字の場合はヘッダー不正として拒否され、ハンドラまで到達しないこと
        mocker.patch("libs.mcp_server_common._is_ai_assistant_driver_enabled", return_value=True)
        # MessageTemplateをモックしているため、エラー応答の生成もモックしてエラーコードだけを検証する
        mock_app_exception_response = mocker.patch(
            "libs.mcp_server_common.app_exception_response", return_value=("", 400)
        )
        fake_handler = mocker.Mock(return_value={"tools": []})
        mocker.patch.dict(api.JSONRPC_METHODS, {"tools/list": fake_handler})
        headers = _auth_headers()
        if user_id is None:
            del headers["User-Id"]
        else:
            headers["User-Id"] = user_id

        res = client.post(
            "/api/{}/workspaces/{}/mcp".format(ORG_ID, WS_ID),
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers=headers,
        )

        assert res.status_code == 400
        raised = mock_app_exception_response.call_args.args[0]
        assert raised.args[0] == "400-00001"
        assert raised.args[2] == ["User-Id or Roles"]
        fake_handler.assert_not_called()
