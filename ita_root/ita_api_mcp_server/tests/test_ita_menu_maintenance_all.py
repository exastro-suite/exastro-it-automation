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
tools/ita_menu_maintenance_all.py (maintenance-all) のユニットテスト

ダウンストリームAPI(ita_api_organization)へのHTTPアクセスはrequests_mockで
すべてモックする。T_AI_ATTACHMENT_FILEからのファイル取得処理
(attachment_file.fetch_attachment_file)は、tools.attachment_file自体には
一切手を加えず、tools.ita_menu_maintenance_all モジュール内の参照を
mocker.patchで置き換えることでDB接続を行わないようにする。
異常系では、g.applogger.info の呼び出し回数はチェックせず、送出される
例外の内容(メッセージ・ステータスコード)で検証する。
"""

import base64

import pytest

from tools import ita_menu_maintenance_all as maintenance_tool
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


def _payload():
    return {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": USER_ID}


def _maintenance_url(menu=MENU):
    return "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/menu/{}/maintenance/all/".format(
        ORG_ID, WS_ID, menu
    )


def _filter_url(menu="operation_list"):
    return "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/menu/{}/filter/".format(
        ORG_ID, WS_ID, menu
    )


def _basic_record():
    return {"parameter": {"col1": "value1"}, "type": "Register"}


class TestToolMaintenanceAllValidation:
    def test_missing_menu_raises(self, mock_flask_g):
        # 異常系: menuが指定されていない場合は例外が発生すること
        with pytest.raises(Exception, match="menu is required"):
            maintenance_tool.tool_maintenance_all({"records": [_basic_record()]}, _payload())

    def test_missing_records_raises(self, mock_flask_g):
        # 異常系: recordsが指定されていない場合は例外が発生すること
        with pytest.raises(Exception, match="records is required and must be a non-empty array"):
            maintenance_tool.tool_maintenance_all({"menu": MENU}, _payload())

    def test_empty_records_raises(self, mock_flask_g):
        # 異常系: recordsが空配列の場合は例外が発生すること
        with pytest.raises(Exception, match="records is required and must be a non-empty array"):
            maintenance_tool.tool_maintenance_all({"menu": MENU, "records": []}, _payload())

    def test_records_not_list_raises(self, mock_flask_g):
        # 異常系: recordsがリストでない(単一オブジェクト)場合は例外が発生すること
        with pytest.raises(Exception, match="records is required and must be a non-empty array"):
            maintenance_tool.tool_maintenance_all(
                {"menu": MENU, "records": {"parameter": {}, "type": "Register"}}, _payload()
            )

    def test_record_not_object_raises(self, mock_flask_g):
        # 異常系: recordsの要素がオブジェクトでない場合、対象indexを含む例外が発生すること
        with pytest.raises(Exception, match=r"Record at index 0 must be an object"):
            maintenance_tool.tool_maintenance_all({"menu": MENU, "records": ["not-a-dict"]}, _payload())

    def test_record_missing_parameter_raises(self, mock_flask_g):
        # 異常系: recordの要素に'parameter'フィールドが無い場合、
        # 対象indexを含む例外が発生すること
        records = [{"type": "Register"}]
        with pytest.raises(Exception, match=r"Record at index 0 is missing 'parameter' field"):
            maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())

    def test_record_missing_type_raises(self, mock_flask_g):
        # 異常系: recordの要素に'type'フィールドが無い場合、
        # 対象indexを含む例外が発生すること
        records = [{"parameter": {"col1": "v"}}]
        with pytest.raises(Exception, match=r"Record at index 0 is missing 'type' field"):
            maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())

    def test_record_invalid_type_raises(self, mock_flask_g):
        # 異常系: 'type'フィールドが許可された操作種別以外の場合、
        # 指定値・対象indexを含む例外が発生すること
        records = [{"parameter": {"col1": "v"}, "type": "Bogus"}]
        with pytest.raises(Exception, match=r"Record at index 0 has invalid type 'Bogus'"):
            maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())

    def test_fileid_not_object_raises(self, mock_flask_g):
        # 異常系: 'fileid'フィールドがオブジェクトでない場合、
        # 対象indexを含む例外が発生すること
        records = [{"parameter": {}, "type": "Register", "fileid": "not-a-dict"}]
        with pytest.raises(Exception, match=r"Record at index 0 has invalid 'fileid' field"):
            maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())

    def test_fileid_value_not_string_raises(self, mock_flask_g):
        # 異常系: 'fileid'内の値(file_id)が文字列でない場合、
        # 対象のcolumn_name_restを含む例外が発生すること
        records = [{"parameter": {}, "type": "Register", "fileid": {"col_rest": 123}}]
        with pytest.raises(Exception, match=r"Record at index 0 has invalid file ID for column 'col_rest'"):
            maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())

    def test_multiple_records_reports_correct_index(self, mock_flask_g):
        # 境界値: 複数recordのうち後方の要素が不正な場合、
        # そのrecordの正しいindexを例外メッセージに含めること
        records = [_basic_record(), {"parameter": {}}]
        with pytest.raises(Exception, match=r"Record at index 1 is missing 'type' field"):
            maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())


class TestToolMaintenanceAllFileId:
    def test_fileid_not_found_raises(self, mock_flask_g, mocker):
        # 異常系: fetch_attachment_fileがNoneを返す(対象ファイルが存在しない)場合、
        # column_name_rest・file_idを含む例外が発生すること
        mock_fetch = mocker.patch(
            "tools.ita_menu_maintenance_all.fetch_attachment_file", return_value=None
        )
        records = [{"parameter": {}, "type": "Register", "fileid": {"attach_rest": "file-123"}}]

        with pytest.raises(Exception, match=r"File not found for column 'attach_rest': file-123"):
            maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())

        mock_fetch.assert_called_once_with(ORG_ID, WS_ID, USER_ID, "file-123")

    def test_fileid_success_converts_to_base64_file_entry(self, mock_flask_g, mocker, requests_mock):
        # 正常系: fileidで指定したファイルの内容がBase64エンコードされ、
        # 送信ボディの'file'フィールドに変換されること('fileid'フィールド自体は
        # 送信ボディから除去される)
        mocker.patch(
            "tools.ita_menu_maintenance_all.fetch_attachment_file",
            return_value={"filename": "a.txt", "mime_type": "text/plain", "content": b"hello world"}
        )
        requests_mock.post(_maintenance_url(), json={"data": {"IdList": []}}, status_code=200)

        records = [{"parameter": {"col1": "v"}, "type": "Register", "fileid": {"attach_rest": "file-123"}}]
        result = maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())

        sent_body = requests_mock.last_request.json()
        assert "fileid" not in sent_body[0]
        expected_b64 = base64.b64encode(b"hello world").decode("utf-8")
        assert sent_body[0]["file"] == {"attach_rest": expected_b64}
        assert result["record_count"] == 1

    def test_fileid_success_merges_into_existing_file_dict(self, mock_flask_g, mocker, requests_mock):
        # 正常系: recordに既に'file'フィールド(別カラムのBase64データ)がある場合、
        # fileidから変換したデータがそこに追記される(既存の値は保持される)こと
        mocker.patch(
            "tools.ita_menu_maintenance_all.fetch_attachment_file",
            return_value={"filename": "b.txt", "mime_type": "text/plain", "content": b"data"}
        )
        requests_mock.post(_maintenance_url(), json={"data": {"IdList": []}}, status_code=200)

        records = [{
            "parameter": {"col1": "v"},
            "type": "Register",
            "fileid": {"attach_rest": "file-123"},
            "file": {"other_col": "already-b64"}
        }]
        maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())

        sent_body = requests_mock.last_request.json()
        assert sent_body[0]["file"]["other_col"] == "already-b64"
        assert sent_body[0]["file"]["attach_rest"] == base64.b64encode(b"data").decode("utf-8")

    def test_multiple_fileid_columns_in_one_record(self, mock_flask_g, mocker, requests_mock):
        # 正常系: 1つのrecordのfileidに複数のcolumn_name_restを指定した場合、
        # それぞれ個別にファイルを取得してBase64変換すること
        mocker.patch(
            "tools.ita_menu_maintenance_all.fetch_attachment_file",
            side_effect=lambda org, ws, user, file_id: {
                "filename": file_id, "mime_type": "text/plain", "content": file_id.encode("utf-8")
            }
        )
        requests_mock.post(_maintenance_url(), json={"data": {"IdList": []}}, status_code=200)

        records = [{
            "parameter": {"col1": "v"},
            "type": "Register",
            "fileid": {"col_a": "file-a", "col_b": "file-b"}
        }]
        maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())

        sent_body = requests_mock.last_request.json()
        assert sent_body[0]["file"]["col_a"] == base64.b64encode(b"file-a").decode("utf-8")
        assert sent_body[0]["file"]["col_b"] == base64.b64encode(b"file-b").decode("utf-8")


class TestToolMaintenanceAllRequest:
    def test_success_returns_expected_result(self, mock_flask_g, requests_mock):
        # 正常系: ダウンストリームAPIが200を返した場合、そのレスポンスがresultに
        # そのまま格納され、organization_id/workspace_id/menu/record_countも
        # 結果に含まれること
        api_response = {"data": {"IdList": ["op-1"]}}
        requests_mock.post(_maintenance_url(), json=api_response, status_code=200)

        records = [_basic_record()]
        result = maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())

        assert result["result"] == api_response
        assert result["message"] == "Maintenance all completed successfully for 1 record(s)."
        assert result["organization_id"] == ORG_ID
        assert result["workspace_id"] == WS_ID
        assert result["menu"] == MENU
        assert result["record_count"] == 1

    def test_request_url_body_and_headers(self, mock_flask_g, requests_mock):
        # 正常系: ダウンストリームAPIへのリクエストURL・メソッド・
        # Content-Typeヘッダー・送信ボディ(records)が期待通りであること
        requests_mock.post(_maintenance_url(), json={"data": {}}, status_code=200)

        records = [_basic_record(), {"parameter": {"col2": "v2"}, "type": "Update"}]
        maintenance_tool.tool_maintenance_all({"menu": MENU, "records": records}, _payload())

        last_request = requests_mock.last_request
        assert last_request.url == _maintenance_url()
        assert last_request.method == "POST"
        assert last_request.headers["Content-Type"] == "application/json"
        assert last_request.json() == records

    def test_downstream_error_raises_http_exception(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIがエラー応答(JSON本文あり)を返した場合、
        # そのmessage/resultからHTTPExceptionのメッセージが組み立てられること
        requests_mock.post(
            _maintenance_url(), json={"message": "menu not found", "result": "NG"}, status_code=404
        )

        with pytest.raises(HTTPException) as exc_info:
            maintenance_tool.tool_maintenance_all({"menu": MENU, "records": [_basic_record()]}, _payload())

        assert exc_info.value.status_code == 404
        assert exc_info.value.message == "menu not found (NG)"

    def test_downstream_error_without_json_body(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIがJSONとして解釈できない応答を返した場合でも、
        # ステータスコードから汎用メッセージのHTTPExceptionが発生すること
        requests_mock.post(_maintenance_url(), text="internal error", status_code=500)

        with pytest.raises(HTTPException) as exc_info:
            maintenance_tool.tool_maintenance_all({"menu": MENU, "records": [_basic_record()]}, _payload())

        assert exc_info.value.status_code == 500
        assert exc_info.value.message == "maintenance-all failed: HTTP 500"


class TestOperationListLanguageUpdate:
    def test_operation_list_language_en_skips_update(self, mock_flask_g, requests_mock):
        # g.LANGUAGEが"en"の場合は、追加のfilter/update呼び出しは発生しない
        mock_flask_g.LANGUAGE = "en"
        requests_mock.post(
            _maintenance_url("operation_list"), json={"data": {"IdList": ["op-1"]}}, status_code=200
        )

        result = maintenance_tool.tool_maintenance_all(
            {"menu": "operation_list", "records": [_basic_record()]}, _payload()
        )

        assert result["record_count"] == 1
        # filter APIへのリクエストは発生していないこと(履行されたリクエストは1件のみ)
        assert len(requests_mock.request_history) == 1

    def test_operation_list_language_ja_no_id_list_skips_update(self, mock_flask_g, requests_mock):
        # 境界値: g.LANGUAGEが"ja"でも、レスポンスのIdListが空の場合は
        # 更新対象が無いためfilter/update呼び出しは発生しないこと
        mock_flask_g.LANGUAGE = "ja"
        requests_mock.post(
            _maintenance_url("operation_list"), json={"data": {"IdList": []}}, status_code=200
        )

        maintenance_tool.tool_maintenance_all(
            {"menu": "operation_list", "records": [_basic_record()]}, _payload()
        )

        assert len(requests_mock.request_history) == 1

    def test_operation_list_language_missing_data_key_skips_update(self, mock_flask_g, requests_mock):
        # 境界値: レスポンスに'data'キー自体が無い場合もIdList空扱いとなり、
        # filter/update呼び出しは発生しないこと
        mock_flask_g.LANGUAGE = "ja"
        requests_mock.post(_maintenance_url("operation_list"), json={}, status_code=200)

        maintenance_tool.tool_maintenance_all(
            {"menu": "operation_list", "records": [_basic_record()]}, _payload()
        )

        assert len(requests_mock.request_history) == 1

    def test_operation_list_language_ja_updates_records(self, mock_flask_g, requests_mock):
        # 正常系: g.LANGUAGEが"ja"かつ登録済みIdListがある場合、
        # filter APIで該当レコードを取得し、discard済みでないレコードのみ
        # language="ja"で更新(Update)されること
        mock_flask_g.LANGUAGE = "ja"
        # 同一URL(operation_listのmaintenance/all/)への1回目(初期登録)・2回目(language更新)
        # の呼び出しに、それぞれ異なるレスポンスを順番に返すようリスト形式で登録する
        requests_mock.post(
            _maintenance_url("operation_list"),
            [
                {"json": {"data": {"IdList": ["op-1", "op-2"]}}, "status_code": 200},
                {"json": {"data": {}}, "status_code": 200},
            ]
        )
        filtered_records = [
            {"parameter": {"operation_id": "op-1", "language": "en", "discard": "0"}},
            {"parameter": {"operation_id": "op-2", "language": "en", "discard": "1"}},
        ]
        requests_mock.post(_filter_url(), json={"data": filtered_records}, status_code=200)

        result = maintenance_tool.tool_maintenance_all(
            {"menu": "operation_list", "records": [_basic_record()]}, _payload()
        )

        assert result["record_count"] == 1
        # filter -> maintenance(update) の2回、合計で最初のmaintenanceも含め3回のリクエストが発生する
        assert len(requests_mock.request_history) == 3

        filter_request = requests_mock.request_history[1]
        assert filter_request.url == _filter_url() + "?file=no"
        assert filter_request.json() == {"operation_id": {"LIST": ["op-1", "op-2"]}}
        assert filter_request.headers["Language"] == "ja"
        assert filter_request.qs.get("file") == ["no"]

        update_request = requests_mock.request_history[2]
        assert update_request.headers["Language"] == "ja"
        sent_update_body = update_request.json()
        # discard="1"のop-2は更新対象から除外され、op-1のみ送信されること
        assert len(sent_update_body) == 1
        assert sent_update_body[0]["type"] == "Update"
        assert sent_update_body[0]["parameter"]["operation_id"] == "op-1"

    def test_operation_list_language_all_discarded_skips_update(self, mock_flask_g, requests_mock):
        # 境界値: filter結果の全レコードがdiscard="1"(廃止済み)の場合、
        # 更新対象が残らずupdate呼び出しは発生しないこと
        mock_flask_g.LANGUAGE = "ja"
        requests_mock.post(
            _maintenance_url("operation_list"), json={"data": {"IdList": ["op-1"]}}, status_code=200
        )
        filtered_records = [{"parameter": {"operation_id": "op-1", "discard": "1"}}]
        requests_mock.post(_filter_url(), json={"data": filtered_records}, status_code=200)

        maintenance_tool.tool_maintenance_all(
            {"menu": "operation_list", "records": [_basic_record()]}, _payload()
        )

        # filterまでは呼ばれるが、全レコード廃止済みのためupdateは呼ばれない(合計2回)
        assert len(requests_mock.request_history) == 2

    def test_operation_list_language_filter_empty_data_skips_update(self, mock_flask_g, requests_mock):
        # 境界値: filter APIのレスポンスが空配列(該当レコード無し)の場合、
        # update呼び出しは発生しないこと
        mock_flask_g.LANGUAGE = "ja"
        requests_mock.post(
            _maintenance_url("operation_list"), json={"data": {"IdList": ["op-1"]}}, status_code=200
        )
        requests_mock.post(_filter_url(), json={"data": []}, status_code=200)

        maintenance_tool.tool_maintenance_all(
            {"menu": "operation_list", "records": [_basic_record()]}, _payload()
        )

        assert len(requests_mock.request_history) == 2

    def test_operation_list_filter_api_error_raises_http_exception(self, mock_flask_g, requests_mock):
        # 異常系: language更新のためのfilter API呼び出しがエラー応答を返した場合、
        # そのmessage/resultからHTTPExceptionが発生すること
        mock_flask_g.LANGUAGE = "ja"
        requests_mock.post(
            _maintenance_url("operation_list"), json={"data": {"IdList": ["op-1"]}}, status_code=200
        )
        requests_mock.post(_filter_url(), json={"message": "boom", "result": "NG"}, status_code=500)

        with pytest.raises(HTTPException) as exc_info:
            maintenance_tool.tool_maintenance_all(
                {"menu": "operation_list", "records": [_basic_record()]}, _payload()
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.message == "boom (NG)"

    def test_operation_list_update_api_error_raises_http_exception(self, mock_flask_g, requests_mock):
        # 異常系: language更新のためのmaintenance-all(Update)呼び出しが
        # エラー応答を返した場合、そのmessageからHTTPExceptionが発生すること
        mock_flask_g.LANGUAGE = "ja"
        requests_mock.post(
            _maintenance_url("operation_list"),
            [
                {"json": {"data": {"IdList": ["op-1"]}}, "status_code": 200},
                {"json": {"message": "update failed"}, "status_code": 400},
            ]
        )
        filtered_records = [{"parameter": {"operation_id": "op-1", "discard": "0"}}]
        requests_mock.post(_filter_url(), json={"data": filtered_records}, status_code=200)

        with pytest.raises(HTTPException) as exc_info:
            maintenance_tool.tool_maintenance_all(
                {"menu": "operation_list", "records": [_basic_record()]}, _payload()
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.message == "update failed"

    def test_update_operation_list_language_direct_call_no_language(self, mock_flask_g):
        # 直接呼び出し: LANGUAGE未設定(空文字)の場合は何もしないこと
        mock_flask_g.LANGUAGE = ""
        # 例外が発生しないことを確認する(戻り値もNone)
        assert maintenance_tool._update_operation_list_language(
            ORG_ID, WS_ID, {"data": {"IdList": ["op-1"]}}
        ) is None

    def test_update_operation_list_language_direct_call_none_response(self, mock_flask_g):
        # 境界値: _update_operation_list_languageを直接呼び出し、
        # response_jsonがNoneでも例外にならないこと(id_listが空とみなされる)
        mock_flask_g.LANGUAGE = "ja"
        assert maintenance_tool._update_operation_list_language(ORG_ID, WS_ID, None) is None


class TestMenuPathEncoding:
    def test_menu_is_url_encoded(self, mock_flask_g, requests_mock):
        # menuに "/" "?" ".." を含めても、別のエンドポイントへ到達せず1つのパスセグメントとして送られること
        encoded = "..%2F..%2F..%2Fws2%2Fita%2Fmenu%2Fx%3Fa%3D"
        requests_mock.post(_maintenance_url(encoded), json={"data": {}}, status_code=200)

        maintenance_tool.tool_maintenance_all(
            {"menu": "../../../ws2/ita/menu/x?a=", "records": [_basic_record()]}, _payload()
        )

        assert requests_mock.last_request.url == _maintenance_url(encoded)
