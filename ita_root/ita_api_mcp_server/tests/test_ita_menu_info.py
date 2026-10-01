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
tools/ita_menu_info.py (list-menu-info / list-menu-info-pulldown) のユニットテスト

ダウンストリームAPI(ita_api_organization)へのHTTPアクセスはrequests_mockで
すべてモックする。異常系では、g.applogger.info の呼び出し回数はチェックせず、
送出される例外の内容(HTTPExceptionのメッセージ/status_code)で検証する。
"""

import pytest

from tools import ita_menu_info as menu_info_tool
from libs import HTTPException

ORG_ID = "org1"
WS_ID = "ws1"
MENU = "sample_menu"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    """ダウンストリームAPI接続先の環境変数を固定する"""
    monkeypatch.setenv("ITA_API_ORAGANIZATION_HOST", "ita-api-organization")
    monkeypatch.setenv("ITA_API_ORAGANIZATION_PORT", "8080")


def _info_url(menu=MENU):
    return "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/menu/{}/info/".format(
        ORG_ID, WS_ID, menu
    )


def _pulldown_url(menu=MENU):
    return "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/menu/{}/info/pulldown/".format(
        ORG_ID, WS_ID, menu
    )


class TestToolListMenuInfo:
    def test_success(self, mock_flask_g, requests_mock):
        # 正常系: ダウンストリームAPIが200を返した場合、そのレスポンスがresultに
        # そのまま格納され、organization_id/workspace_id/menuも結果に含まれること
        api_response = {"col1": {"type": "text"}, "col2": {"type": "select"}}
        requests_mock.get(_info_url(), json=api_response, status_code=200)

        result = menu_info_tool.tool_list_menu_info(
            {"menu": MENU},
            {"organization_id": ORG_ID, "workspace_id": WS_ID}
        )

        assert result["result"] == api_response
        assert result["message"] == "Menu info fetched successfully."
        assert result["organization_id"] == ORG_ID
        assert result["workspace_id"] == WS_ID
        assert result["menu"] == MENU

    def test_success_forwards_headers(self, mock_flask_g, requests_mock):
        # 正常系: リクエストに付与されたUser-Id/RolesヘッダーがそのままダウンストリームAPIへ
        # 転送され、GETリクエストなのでContent-Typeは付与されないこと
        requests_mock.get(_info_url(), json={}, status_code=200)

        menu_info_tool.tool_list_menu_info(
            {"menu": MENU},
            {"organization_id": ORG_ID, "workspace_id": WS_ID}
        )

        sent_headers = requests_mock.last_request.headers
        assert sent_headers.get("Language") == "en"
        assert "Content-Type" not in sent_headers

    def test_missing_menu_raises(self, mock_flask_g):
        # 異常系: menuが指定されていない場合は "menu is required" を含む例外が発生すること
        with pytest.raises(Exception, match="menu is required"):
            menu_info_tool.tool_list_menu_info({}, {"organization_id": ORG_ID, "workspace_id": WS_ID})

    def test_empty_menu_raises(self, mock_flask_g):
        # 境界値: menuが空文字の場合も未指定と同様に扱われ例外が発生すること
        with pytest.raises(Exception, match="menu is required"):
            menu_info_tool.tool_list_menu_info(
                {"menu": ""}, {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )

    def test_downstream_error_raises_http_exception(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが発生し、
        # そのメッセージにダウンストリームのmessage/resultが反映されること
        requests_mock.get(
            _info_url(),
            json={"message": "menu not found", "result": "NG"},
            status_code=404
        )

        with pytest.raises(HTTPException) as exc_info:
            menu_info_tool.tool_list_menu_info(
                {"menu": MENU}, {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.message == "menu not found (NG)"

    def test_downstream_error_non_json_body(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIのレスポンスボディがJSONでない場合でも
        # HTTPExceptionが発生し、tool_nameとstatus_codeから組み立てたメッセージになること
        requests_mock.get(_info_url(), text="internal server error", status_code=500)

        with pytest.raises(HTTPException) as exc_info:
            menu_info_tool.tool_list_menu_info(
                {"menu": MENU}, {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.message == "list-menu-info failed: HTTP 500"


class TestToolListMenuInfoPulldown:
    def test_success(self, mock_flask_g, requests_mock):
        # 正常系: ダウンストリームAPIが200を返した場合、プルダウン一覧がresultに
        # そのまま格納されること
        api_response = {"col1_rest": {"1": "value1", "2": "value2"}}
        requests_mock.get(_pulldown_url(), json=api_response, status_code=200)

        result = menu_info_tool.tool_list_menu_info_pulldown(
            {"menu": MENU},
            {"organization_id": ORG_ID, "workspace_id": WS_ID}
        )

        assert result["result"] == api_response
        assert result["message"] == "Menu pulldown list fetched successfully."
        assert result["organization_id"] == ORG_ID
        assert result["workspace_id"] == WS_ID
        assert result["menu"] == MENU

    def test_missing_menu_raises(self, mock_flask_g):
        # 異常系: menuが指定されていない場合は例外が発生すること
        with pytest.raises(Exception, match="menu is required"):
            menu_info_tool.tool_list_menu_info_pulldown(
                {}, {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )

    def test_downstream_error_raises_http_exception(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが発生すること
        requests_mock.get(_pulldown_url(), json={"message": "bad request"}, status_code=400)

        with pytest.raises(HTTPException) as exc_info:
            menu_info_tool.tool_list_menu_info_pulldown(
                {"menu": MENU}, {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.message == "bad request"
