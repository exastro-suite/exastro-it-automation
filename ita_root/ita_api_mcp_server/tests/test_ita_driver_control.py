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
tools/ita_driver_control.py (execute-driver / dry-run-driver / get-driver-status) の
ユニットテスト

異常系では、g.applogger.info の呼び出し回数はチェックしない
(ログ出力を増減しただけでテストが壊れるのは望ましくないため)。
代わりに、送出される例外のメッセージに元のエラー内容が含まれているかどうかで検証する。
ダウンストリームAPI呼び出しは requests_mock で全てモック化する。
"""

import pytest

from libs import HTTPException
from tools import ita_driver_control as driver_tool

ORG_ID = "org1"
WS_ID = "ws1"
HOST = "ita-api-organization"
PORT = "8000"


@pytest.fixture(autouse=True)
def ita_env(monkeypatch):
    """ITA_API_ORAGANIZATION_HOST / PORT を固定値に設定する(呼び出しURLを決定的にするため)"""
    monkeypatch.setenv("ITA_API_ORAGANIZATION_HOST", HOST)
    monkeypatch.setenv("ITA_API_ORAGANIZATION_PORT", PORT)


class TestToolExecuteDriver:
    def test_missing_menu_raises(self, mock_flask_g):
        # 異常系: menuが未指定の場合は例外が発生すること
        with pytest.raises(Exception, match="menu is required"):
            driver_tool.tool_execute_driver(
                {"movement_name": "mv", "operation_name": "op"},
                {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )

    def test_success_without_schedule_date(self, mock_flask_g, requests_mock):
        # 正常系: schedule_date未指定の場合、リクエストボディにschedule_dateが含まれず、
        # 成功レスポンスがそのまま結果として返ること
        url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/menuA/driver/execute/".format(
            HOST, PORT, ORG_ID, WS_ID
        )
        requests_mock.post(url, json={"execution_no": "1"}, status_code=200)

        result = driver_tool.tool_execute_driver(
            {"menu": "menuA", "movement_name": "mv", "operation_name": "op"},
            {"organization_id": ORG_ID, "workspace_id": WS_ID}
        )

        assert result["result"] == {"execution_no": "1"}
        assert result["message"] == "Driver execution started successfully."
        assert result["organization_id"] == ORG_ID
        assert result["workspace_id"] == WS_ID
        assert result["menu"] == "menuA"
        sent_body = requests_mock.last_request.json()
        assert sent_body == {"movement_name": "mv", "operation_name": "op"}
        assert "schedule_date" not in sent_body

    def test_success_with_schedule_date(self, mock_flask_g, requests_mock):
        # 正常系: schedule_dateを指定した場合、リクエストボディにそのまま含まれること
        url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/menuA/driver/execute/".format(
            HOST, PORT, ORG_ID, WS_ID
        )
        requests_mock.post(url, json={"execution_no": "2"}, status_code=200)

        driver_tool.tool_execute_driver(
            {
                "menu": "menuA",
                "movement_name": "mv",
                "operation_name": "op",
                "schedule_date": "2026/01/01 00:00"
            },
            {"organization_id": ORG_ID, "workspace_id": WS_ID}
        )

        sent_body = requests_mock.last_request.json()
        assert sent_body["schedule_date"] == "2026/01/01 00:00"

    def test_http_failure_raises_httpexception(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが
        # 元のエラー内容(message/result)を含んで発生すること
        url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/menuA/driver/execute/".format(
            HOST, PORT, ORG_ID, WS_ID
        )
        requests_mock.post(url, json={"message": "boom", "result": "NG"}, status_code=500)

        with pytest.raises(HTTPException) as exc_info:
            driver_tool.tool_execute_driver(
                {"menu": "menuA", "movement_name": "mv", "operation_name": "op"},
                {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )

        assert "boom (NG)" in str(exc_info.value)
        assert exc_info.value.tool_name == "execute-driver"
        assert exc_info.value.status_code == 500


class TestToolDryRunDriver:
    def test_missing_menu_raises(self, mock_flask_g):
        # 異常系: menuが未指定の場合は例外が発生すること
        with pytest.raises(Exception, match="menu is required"):
            driver_tool.tool_dry_run_driver(
                {"movement_name": "mv", "operation_name": "op"},
                {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )

    def test_success(self, mock_flask_g, requests_mock):
        # 正常系: ドライラン実行が成功レスポンスをそのまま返すこと
        url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/menuA/driver/execute_dry_run/".format(
            HOST, PORT, ORG_ID, WS_ID
        )
        requests_mock.post(url, json={"execution_no": "3"}, status_code=200)

        result = driver_tool.tool_dry_run_driver(
            {"menu": "menuA", "movement_name": "mv", "operation_name": "op"},
            {"organization_id": ORG_ID, "workspace_id": WS_ID}
        )

        assert result["result"] == {"execution_no": "3"}
        assert result["message"] == "Driver dry-run execution started successfully."
        assert result["menu"] == "menuA"

    def test_http_failure_raises_httpexception(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが発生すること
        url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/menuA/driver/execute_dry_run/".format(
            HOST, PORT, ORG_ID, WS_ID
        )
        requests_mock.post(url, json={"message": "dry run failed"}, status_code=400)

        with pytest.raises(HTTPException, match="dry run failed"):
            driver_tool.tool_dry_run_driver(
                {"menu": "menuA", "movement_name": "mv", "operation_name": "op"},
                {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )


class TestToolGetDriverStatus:
    def test_missing_menu_raises(self, mock_flask_g):
        # 異常系: menuが未指定の場合は例外が発生すること
        with pytest.raises(Exception, match="menu is required"):
            driver_tool.tool_get_driver_status(
                {"execution_no": "1"},
                {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )

    def test_missing_execution_no_raises(self, mock_flask_g):
        # 異常系: execution_noが未指定の場合は例外が発生すること
        with pytest.raises(Exception, match="execution_no is required"):
            driver_tool.tool_get_driver_status(
                {"menu": "menuA"},
                {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )

    def test_success(self, mock_flask_g, requests_mock):
        # 正常系: 実行状態取得の成功レスポンスがそのまま結果として返ること
        url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/menuA/driver/10/".format(
            HOST, PORT, ORG_ID, WS_ID
        )
        requests_mock.get(url, json={"status": "COMPLETE"}, status_code=200)

        result = driver_tool.tool_get_driver_status(
            {"menu": "menuA", "execution_no": "10"},
            {"organization_id": ORG_ID, "workspace_id": WS_ID}
        )

        assert result["result"] == {"status": "COMPLETE"}
        assert result["message"] == "Driver status retrieved successfully."
        assert result["menu"] == "menuA"
        assert result["execution_no"] == "10"

    def test_http_failure_raises_httpexception(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが発生すること
        url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/menuA/driver/10/".format(
            HOST, PORT, ORG_ID, WS_ID
        )
        requests_mock.get(url, text="not json", status_code=404)

        with pytest.raises(HTTPException) as exc_info:
            driver_tool.tool_get_driver_status(
                {"menu": "menuA", "execution_no": "10"},
                {"organization_id": ORG_ID, "workspace_id": WS_ID}
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.tool_name == "get-driver-status"
