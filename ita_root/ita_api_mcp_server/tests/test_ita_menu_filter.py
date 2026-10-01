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
tools/ita_menu_filter.py (menu-filter / menu-filter-count) のユニットテスト

ダウンストリームAPI(ita_api_organization)へのHTTPアクセスはrequests_mockで
すべてモックし、T_AI_ATTACHMENT_FILEへの登録処理(create_attachment_file)は
tools.ita_menu_filter.create_attachment_file をmonkeypatchで置き換えて
DB接続そのものを行わないようにする。異常系では、g.applogger.info の呼び出し
回数はチェックせず、送出される例外の内容で検証する。
"""

import base64

import pytest

from tools import ita_menu_filter as menu_filter_tool
from libs import HTTPException

ORG_ID = "org1"
WS_ID = "ws1"
USER_ID = "user1"
MENU = "sample_menu"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    """ダウンストリームAPI接続先の環境変数を固定する"""
    monkeypatch.setenv("ITA_API_ORAGANIZATION_HOST", "ita-api-organization")
    monkeypatch.setenv("ITA_API_ORAGANIZATION_PORT", "8080")


def _filter_url(menu=MENU):
    return "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/menu/{}/filter/".format(
        ORG_ID, WS_ID, menu
    )


def _filter_count_url(menu=MENU):
    return "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/menu/{}/filter/count/".format(
        ORG_ID, WS_ID, menu
    )


def _payload():
    return {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": USER_ID}


class TestToolMenuFilter:
    def test_success_default_discard_condition_and_file_no(self, mock_flask_g, requests_mock):
        # 正常系: filter_conditionsにdiscardが未指定の場合、discard=0を除外する
        # デフォルト条件が追加されて送信され、fileパラメータ未指定時はダウンストリーム
        # APIへ file=no がクエリパラメータとして渡されること
        requests_mock.post(_filter_url(), json={"data": []}, status_code=200)

        result = menu_filter_tool.tool_menu_filter({"menu": MENU}, _payload())

        assert result["result"] == {"data": []}
        assert result["message"] == "Menu records fetched successfully."
        assert result["menu"] == MENU
        sent_body = requests_mock.last_request.json()
        assert sent_body["discard"] == {"NORMAL": "0"}
        assert requests_mock.last_request.qs.get("file") == ["no"]

    def test_success_explicit_discard_condition_not_overridden(self, mock_flask_g, requests_mock):
        # 正常系: filter_conditionsで既にdiscardが指定されている場合、デフォルト条件で
        # 上書きされず、指定した値のまま送信されること
        requests_mock.post(_filter_url(), json={"data": []}, status_code=200)

        menu_filter_tool.tool_menu_filter(
            {"menu": MENU, "filter_conditions": {"discard": {"NORMAL": "1"}}},
            _payload()
        )

        sent_body = requests_mock.last_request.json()
        assert sent_body["discard"] == {"NORMAL": "1"}

    def test_missing_menu_raises(self, mock_flask_g):
        # 異常系: menuが指定されていない場合は例外が発生すること
        with pytest.raises(Exception, match="menu is required"):
            menu_filter_tool.tool_menu_filter({}, _payload())

    def test_downstream_error_raises_http_exception(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが発生すること
        requests_mock.post(
            _filter_url(), json={"message": "menu not found", "result": "NG"}, status_code=404
        )

        with pytest.raises(HTTPException) as exc_info:
            menu_filter_tool.tool_menu_filter({"menu": MENU}, _payload())

        assert exc_info.value.status_code == 404
        assert exc_info.value.message == "menu not found (NG)"

    def test_file_yes_within_limit_converts_to_fileid(self, mock_flask_g, requests_mock, monkeypatch):
        # 正常系: file="yes"かつレコード件数が上限以下の場合、各レコードのfile列が
        # create_attachment_fileの戻り値のfile_idに置き換えられ、fileidとして
        # 返されること(file列自体は結果から取り除かれること)
        monkeypatch.setattr(menu_filter_tool, "MENU_FILTER_FILE_RECORD_LIMIT", 5)
        b64_content = base64.b64encode(b"hello world").decode("ascii")
        records = [
            {
                "parameter": {"attach_file_rest": "myfile.txt"},
                "file": {"attach_file_rest": b64_content}
            }
        ]
        requests_mock.post(_filter_url(), json={"data": records}, status_code=200)

        created = {"file_id": "fileid_abc123", "filename": "myfile.txt",
                   "mime_type": "application/octet-stream", "size": 11}
        mock_create = pytest.importorskip("unittest.mock").Mock(return_value=created)
        monkeypatch.setattr(menu_filter_tool, "create_attachment_file", mock_create)

        result = menu_filter_tool.tool_menu_filter({"menu": MENU, "file": "yes"}, _payload())

        returned_record = result["result"]["data"][0]
        assert "file" not in returned_record
        assert returned_record["fileid"] == {"attach_file_rest": "fileid_abc123"}
        mock_create.assert_called_once_with(
            ORG_ID, WS_ID, USER_ID, "myfile.txt", "application/octet-stream", b"hello world"
        )
        # file="yes"の場合はダウンストリームへfile=noを渡さない(paramsが空になる)こと
        assert "file" not in requests_mock.last_request.qs

    def test_file_yes_uses_column_name_as_filename_when_no_parameter(self, mock_flask_g, requests_mock, monkeypatch):
        # 境界値: recordのparameterにfilenameの指定がない場合、列名(column_name_rest)が
        # ファイル名として使われること
        monkeypatch.setattr(menu_filter_tool, "MENU_FILTER_FILE_RECORD_LIMIT", 5)
        b64_content = base64.b64encode(b"data").decode("ascii")
        records = [{"file": {"attach_file_rest": b64_content}}]
        requests_mock.post(_filter_url(), json={"data": records}, status_code=200)

        created = {"file_id": "fileid_xyz", "filename": "attach_file_rest",
                   "mime_type": "application/octet-stream", "size": 4}
        from unittest import mock
        mock_create = mock.Mock(return_value=created)
        monkeypatch.setattr(menu_filter_tool, "create_attachment_file", mock_create)

        result = menu_filter_tool.tool_menu_filter({"menu": MENU, "file": "yes"}, _payload())

        assert result["result"]["data"][0]["fileid"] == {"attach_file_rest": "fileid_xyz"}
        mock_create.assert_called_once_with(
            ORG_ID, WS_ID, USER_ID, "attach_file_rest", "application/octet-stream", b"data"
        )

    def test_file_yes_skips_empty_file_column_content(self, mock_flask_g, requests_mock, monkeypatch):
        # 境界値: file列の値が空(Falsy)の場合、create_attachment_fileは呼ばれず
        # fileidにも含まれないこと
        monkeypatch.setattr(menu_filter_tool, "MENU_FILTER_FILE_RECORD_LIMIT", 5)
        records = [{"file": {"attach_file_rest": ""}}]
        requests_mock.post(_filter_url(), json={"data": records}, status_code=200)

        from unittest import mock
        mock_create = mock.Mock()
        monkeypatch.setattr(menu_filter_tool, "create_attachment_file", mock_create)

        result = menu_filter_tool.tool_menu_filter({"menu": MENU, "file": "yes"}, _payload())

        assert result["result"]["data"][0]["fileid"] == {}
        mock_create.assert_not_called()

    def test_file_yes_missing_file_column_results_in_empty_fileid(self, mock_flask_g, requests_mock, monkeypatch):
        # 境界値: recordにfile列自体が存在しない場合でもエラーとならず、
        # fileidが空辞書として設定されること
        monkeypatch.setattr(menu_filter_tool, "MENU_FILTER_FILE_RECORD_LIMIT", 5)
        records = [{"parameter": {}}]
        requests_mock.post(_filter_url(), json={"data": records}, status_code=200)

        result = menu_filter_tool.tool_menu_filter({"menu": MENU, "file": "yes"}, _payload())

        assert result["result"]["data"][0]["fileid"] == {}

    def test_file_yes_exceeds_limit_omits_file_info(self, mock_flask_g, requests_mock, monkeypatch):
        # 正常系: file="yes"だがレコード件数が上限を超える場合、各レコードのfile列が
        # 空辞書に置き換えられ、messageに件数と上限が反映されること
        monkeypatch.setattr(menu_filter_tool, "MENU_FILTER_FILE_RECORD_LIMIT", 1)
        records = [
            {"file": {"attach_file_rest": "abc"}},
            {"file": {"attach_file_rest": "def"}},
        ]
        requests_mock.post(_filter_url(), json={"data": records}, status_code=200)

        result = menu_filter_tool.tool_menu_filter({"menu": MENU, "file": "yes"}, _payload())

        for record in result["result"]["data"]:
            assert record["file"] == {}
        assert "exceeded the limit (1)" in result["message"]
        assert "record count (2)" in result["message"]

    def test_file_yes_create_attachment_file_failure_raises(self, mock_flask_g, requests_mock, monkeypatch):
        # 異常系: create_attachment_fileが失敗した場合、元のエラー内容を含む例外が
        # 発生すること
        monkeypatch.setattr(menu_filter_tool, "MENU_FILTER_FILE_RECORD_LIMIT", 5)
        b64_content = base64.b64encode(b"hello").decode("ascii")
        records = [{"file": {"attach_file_rest": b64_content}}]
        requests_mock.post(_filter_url(), json={"data": records}, status_code=200)

        from unittest import mock
        mock_create = mock.Mock(side_effect=RuntimeError("db down"))
        monkeypatch.setattr(menu_filter_tool, "create_attachment_file", mock_create)

        with pytest.raises(Exception, match="Failed to store file content for column 'attach_file_rest': db down"):
            menu_filter_tool.tool_menu_filter({"menu": MENU, "file": "yes"}, _payload())


class TestToolMenuFilterCount:
    def test_success(self, mock_flask_g, requests_mock):
        # 正常系: ダウンストリームAPIが200を返した場合、件数情報がresultにそのまま
        # 格納されること
        requests_mock.post(_filter_count_url(), json={"count": 42}, status_code=200)

        result = menu_filter_tool.tool_menu_filter_count(
            {"menu": MENU, "filter_conditions": {"col": {"NORMAL": "v"}}}, _payload()
        )

        assert result["result"] == {"count": 42}
        assert result["message"] == "Menu record count fetched successfully."
        assert result["menu"] == MENU
        sent_body = requests_mock.last_request.json()
        assert sent_body == {"col": {"NORMAL": "v"}}

    def test_default_filter_conditions_empty_body(self, mock_flask_g, requests_mock):
        # 境界値: filter_conditionsが未指定の場合、空のJSONボディが送信されること
        requests_mock.post(_filter_count_url(), json={"count": 0}, status_code=200)

        menu_filter_tool.tool_menu_filter_count({"menu": MENU}, _payload())

        assert requests_mock.last_request.json() == {}

    def test_missing_menu_raises(self, mock_flask_g):
        # 異常系: menuが指定されていない場合は例外が発生すること
        with pytest.raises(Exception, match="menu is required"):
            menu_filter_tool.tool_menu_filter_count({}, _payload())

    def test_downstream_error_raises_http_exception(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが発生すること
        requests_mock.post(_filter_count_url(), text="boom", status_code=500)

        with pytest.raises(HTTPException) as exc_info:
            menu_filter_tool.tool_menu_filter_count({"menu": MENU}, _payload())

        assert exc_info.value.status_code == 500
        assert exc_info.value.message == "menu-filter-count failed: HTTP 500"
