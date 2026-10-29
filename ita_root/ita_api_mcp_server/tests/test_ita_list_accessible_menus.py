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
tools/ita_list_accessible_menus.py (list-accessible-menus) のユニットテスト

異常系では、g.applogger.info の呼び出し回数はチェックしない
(ログ出力を増減しただけでテストが壊れるのは望ましくないため)。
代わりに、送出される例外のメッセージ・ステータスコードで検証する。
"""

from unittest import mock

import pytest
from flask import g

from tools import ita_list_accessible_menus


@pytest.fixture
def ita_org_env(monkeypatch):
    """ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT 環境変数を固定する
    (変数名の "ORAGANIZATION" というスペルは実際のソースコードのタイプミスと同一であり、
    意図的にそのまま使用している)
    """
    monkeypatch.setenv("ITA_API_ORAGANIZATION_HOST", "ita-org-host")
    monkeypatch.setenv("ITA_API_ORAGANIZATION_PORT", "9090")


def _expected_url(organization_id, workspace_id):
    return "http://ita-org-host:9090/api/{}/workspaces/{}/ita/user/menus/".format(
        organization_id, workspace_id
    )


class TestToolListAccessibleMenus:
    def test_list_accessible_menus_success(self, mock_flask_g, ita_org_env, requests_mock):
        # 正常系: 200応答時にAPIのレスポンスがそのままresultに入り、
        # message / organization_id / workspace_id が正しく設定されること
        organization_id = "org-1"
        workspace_id = "ws-1"
        api_response = {"menu_groups": [{"menu_group_name": "System"}]}
        requests_mock.get(_expected_url(organization_id, workspace_id), json=api_response, status_code=200)

        result = ita_list_accessible_menus.tool_list_accessible_menus(
            {}, {"organization_id": organization_id, "workspace_id": workspace_id}
        )

        assert result["result"] == api_response
        assert result["message"] == "Accessible menus fetched successfully."
        assert result["organization_id"] == organization_id
        assert result["workspace_id"] == workspace_id

    def test_list_accessible_menus_request_url_and_headers(self, mock_flask_g, ita_org_env, requests_mock):
        # 正常系: 呼び出し先URLが環境変数から正しく組み立てられ(組織/ワークスペース
        # 両方を含む)、GETリクエストのためContent-Typeが付与されないこと
        organization_id = "org-2"
        workspace_id = "ws-2"
        requests_mock.get(_expected_url(organization_id, workspace_id), json={}, status_code=200)

        ita_list_accessible_menus.tool_list_accessible_menus(
            {}, {"organization_id": organization_id, "workspace_id": workspace_id}
        )

        last_request = requests_mock.last_request
        assert last_request.url == _expected_url(organization_id, workspace_id)
        assert last_request.method == "GET"
        assert "Content-Type" not in last_request.headers

    def test_list_accessible_menus_forwards_incoming_headers(self, app, ita_org_env, requests_mock):
        # 正常系: 受信した User-Id / Roles / Org-Roles ヘッダーがそのまま
        # ダウンストリームAPIへ転送されること
        organization_id = "org-3"
        workspace_id = "ws-3"
        requests_mock.get(_expected_url(organization_id, workspace_id), json={}, status_code=200)

        with app.test_request_context(
            headers={"User-Id": "user-7", "Roles": "role-1", "Org-Roles": "org-role-9"}
        ):
            g.applogger = mock.Mock()
            g.applogger.info = mock.Mock()
            g.LANGUAGE = "en"

            ita_list_accessible_menus.tool_list_accessible_menus(
                {}, {"organization_id": organization_id, "workspace_id": workspace_id}
            )

        last_request = requests_mock.last_request
        assert last_request.headers["User-Id"] == "user-7"
        assert last_request.headers["Roles"] == "role-1"
        assert last_request.headers["Org-Roles"] == "org-role-9"

    def test_list_accessible_menus_http_error_raises(self, mock_flask_g, ita_org_env, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが
        # 発生し、そのメッセージ・ステータスコードが応答内容から組み立てられること
        organization_id = "org-4"
        workspace_id = "ws-4"
        requests_mock.get(
            _expected_url(organization_id, workspace_id),
            json={"message": "Workspace not found", "result": "no_such_workspace"},
            status_code=404,
        )

        with pytest.raises(ita_list_accessible_menus.HTTPException) as exc_info:
            ita_list_accessible_menus.tool_list_accessible_menus(
                {}, {"organization_id": organization_id, "workspace_id": workspace_id}
            )

        assert exc_info.value.status_code == 404
        assert str(exc_info.value) == "Workspace not found (no_such_workspace)"
        assert exc_info.value.tool_name == "list-accessible-menus"

    def test_list_accessible_menus_http_error_without_json_body(
        self, mock_flask_g, ita_org_env, requests_mock
    ):
        # 異常系: レスポンスボディがJSONとして解釈できない場合でも例外が発生し、
        # tool_nameとstatus_codeからメッセージが組み立てられること
        organization_id = "org-5"
        workspace_id = "ws-5"
        requests_mock.get(
            _expected_url(organization_id, workspace_id),
            text="internal error",
            status_code=500,
        )

        with pytest.raises(ita_list_accessible_menus.HTTPException) as exc_info:
            ita_list_accessible_menus.tool_list_accessible_menus(
                {}, {"organization_id": organization_id, "workspace_id": workspace_id}
            )

        assert exc_info.value.status_code == 500
        assert str(exc_info.value) == "list-accessible-menus failed: HTTP 500"

    def test_list_accessible_menus_missing_ids(self, mock_flask_g, ita_org_env, requests_mock):
        # 境界値: payloadにorganization_id/workspace_idが無い場合はNoneとして
        # URLに組み込まれること
        requests_mock.get(_expected_url("None", "None"), json={"menu_groups": []}, status_code=200)

        result = ita_list_accessible_menus.tool_list_accessible_menus({}, {})

        assert result["organization_id"] is None
        assert result["workspace_id"] is None
        assert result["result"] == {"menu_groups": []}
