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
tools/attachment_file.py (attachment_file_bp のルート・create-attachment-text-file /
get-attachment-text-file ツール・内部ヘルパー関数) のユニットテスト

異常系では、g.applogger.info / .error の呼び出し回数はチェックしない
(ログ出力を増減しただけでテストが壊れるのは望ましくないため)。
代わりに、送出される例外のメッセージ・レスポンス内容(ステータスコード/JSON本文)で検証する。

DBアクセスは common_libs.common.dbconnect.DBConnectWs をモックし、実際のDB接続・
ファイルシステムアクセスは一切行わない。ダウンロードAPIの send_file も
モックし、実ファイルを扱わない。
"""
import io

import pytest
from unittest import mock
from flask import g

from tools import attachment_file


ORG_ID = "org1"
WS_ID = "ws1"


def _set_g_mocks(user_id=None):
    """g.applogger / g.appmsg / g.LANGUAGE / g.USER_ID をテスト用に設定する"""
    g.applogger = mock.Mock()
    g.applogger.info = mock.Mock()
    g.applogger.error = mock.Mock()
    g.applogger.debug = mock.Mock()
    g.appmsg = mock.Mock()
    g.appmsg.get_api_message = mock.Mock(side_effect=lambda msg_id, *args: "Message {}".format(msg_id))
    g.appmsg.get_log_message = mock.Mock(side_effect=lambda msg_id, *args: "Log Message {}".format(msg_id))
    g.LANGUAGE = "en"
    if user_id is not None:
        g.USER_ID = user_id


@pytest.fixture
def mock_db_ws(mocker, mock_dbca):
    """tools.attachment_file.DBConnectWs をモックし、インスタンス化した際の戻り値を mock_dbca にする"""
    mock_cls = mocker.patch("tools.attachment_file.DBConnectWs")
    mock_cls.return_value = mock_dbca
    mock_cls.genarate_primary_key_value = mock.Mock(return_value="generated-uuid")
    return mock_cls


class TestUploadAttachmentFile:
    def test_upload_success(self, app, mocker):
        # 正常系: fileが含まれる場合、create_attachment_fileの結果がそのまま201で返ること
        meta = {"file_id": "fileid_abc", "filename": "test.txt", "mime_type": "text/plain", "size": 5}
        mock_create = mocker.patch("tools.attachment_file.create_attachment_file", return_value=meta)

        with app.test_request_context(
            "/api/{}/workspaces/{}/mcp/attachment_file".format(ORG_ID, WS_ID),
            method="POST",
            data={"file": (io.BytesIO(b"hello"), "test.txt")},
            content_type="multipart/form-data",
        ):
            _set_g_mocks(user_id="user-1")
            response, status = attachment_file.upload_attachment_file(ORG_ID, WS_ID)

        assert status == 201
        assert response.get_json() == meta
        mock_create.assert_called_once()
        call_args = mock_create.call_args[0]
        assert call_args[0] == ORG_ID
        assert call_args[1] == WS_ID
        assert call_args[2] == "user-1"
        assert call_args[3] == "test.txt"
        assert call_args[5] == b"hello"

    def test_upload_missing_file_returns_400(self, app):
        # 異常系: multipart/form-dataにfileが含まれない場合、400 FileRequiredを返すこと
        with app.test_request_context(
            "/api/{}/workspaces/{}/mcp/attachment_file".format(ORG_ID, WS_ID),
            method="POST",
            data={},
            content_type="multipart/form-data",
        ):
            _set_g_mocks()
            response, status = attachment_file.upload_attachment_file(ORG_ID, WS_ID)

        assert status == 400
        body = response.get_json()
        assert body["error"] == "FileRequired"

    def test_upload_empty_file_size_zero(self, app, mocker):
        # 境界値: 0byteファイルでもアップロードでき、sizeが0として返ること
        meta = {"file_id": "fileid_empty", "filename": "empty.txt", "mime_type": "text/plain", "size": 0}
        mocker.patch("tools.attachment_file.create_attachment_file", return_value=meta)

        with app.test_request_context(
            "/api/{}/workspaces/{}/mcp/attachment_file".format(ORG_ID, WS_ID),
            method="POST",
            data={"file": (io.BytesIO(b""), "empty.txt")},
            content_type="multipart/form-data",
        ):
            _set_g_mocks()
            response, status = attachment_file.upload_attachment_file(ORG_ID, WS_ID)

        assert status == 201
        assert response.get_json()["size"] == 0

    def test_upload_no_user_id_defaults_to_none(self, app, mocker):
        # 境界値: g.USER_IDが未設定の場合、user_idはNoneとしてcreate_attachment_fileに渡ること
        meta = {"file_id": "fileid_x", "filename": "x.txt", "mime_type": "text/plain", "size": 1}
        mock_create = mocker.patch("tools.attachment_file.create_attachment_file", return_value=meta)

        with app.test_request_context(
            "/api/{}/workspaces/{}/mcp/attachment_file".format(ORG_ID, WS_ID),
            method="POST",
            data={"file": (io.BytesIO(b"x"), "x.txt")},
            content_type="multipart/form-data",
        ):
            _set_g_mocks()
            attachment_file.upload_attachment_file(ORG_ID, WS_ID)

        assert mock_create.call_args[0][2] is None


class TestGetAttachmentFileMeta:
    def test_get_meta_success(self, app, mocker):
        # 正常系: メタ情報が見つかった場合、file_id/filename/mime_type/sizeを含むJSONを返すこと
        meta = {"filename": "a.txt", "mime_type": "text/plain", "size": 123}
        mocker.patch("tools.attachment_file._fetch_attachment_meta", return_value=meta)

        with app.test_request_context("/x"):
            _set_g_mocks(user_id="user-1")
            response = attachment_file.get_attachment_file_meta(ORG_ID, WS_ID, "fileid_abc")

        body = response.get_json()
        assert body == {
            "file_id": "fileid_abc",
            "filename": "a.txt",
            "mime_type": "text/plain",
            "size": 123,
        }

    def test_get_meta_not_found_returns_404(self, app, mocker):
        # 異常系: 対象file_idが存在しない場合、404 FileNotFoundを返すこと
        mocker.patch("tools.attachment_file._fetch_attachment_meta", return_value=None)

        with app.test_request_context("/x"):
            _set_g_mocks()
            response, status = attachment_file.get_attachment_file_meta(ORG_ID, WS_ID, "no-such-file")

        assert status == 404
        assert response.get_json()["error"] == "FileNotFound"


class TestDownloadAttachmentFile:
    def test_download_success(self, app, mocker):
        # 正常系: ファイルが見つかった場合、send_fileがBytesIO/mimetype/download_name付きで
        # 呼ばれ、その戻り値がそのまま返ること
        file_data = {"filename": "a.txt", "mime_type": "text/plain", "content": b"file-content"}
        mocker.patch("tools.attachment_file.fetch_attachment_file", return_value=file_data)
        sentinel_response = mock.Mock(name="send_file_response")
        mock_send_file = mocker.patch("tools.attachment_file.send_file", return_value=sentinel_response)

        with app.test_request_context("/x"):
            _set_g_mocks(user_id="user-1")
            response = attachment_file.download_attachment_file(ORG_ID, WS_ID, "fileid_abc")

        assert response is sentinel_response
        mock_send_file.assert_called_once()
        call_args, call_kwargs = mock_send_file.call_args
        assert isinstance(call_args[0], io.BytesIO)
        assert call_args[0].getvalue() == b"file-content"
        assert call_kwargs["mimetype"] == "text/plain"
        assert call_kwargs["as_attachment"] is True
        assert call_kwargs["download_name"] == "a.txt"

    def test_download_not_found_returns_404(self, app, mocker):
        # 異常系: 対象file_idが存在しない場合、404 FileNotFoundを返し、send_fileは呼ばれないこと
        mocker.patch("tools.attachment_file.fetch_attachment_file", return_value=None)
        mock_send_file = mocker.patch("tools.attachment_file.send_file")

        with app.test_request_context("/x"):
            _set_g_mocks()
            response, status = attachment_file.download_attachment_file(ORG_ID, WS_ID, "no-such-file")

        assert status == 404
        assert response.get_json()["error"] == "FileNotFound"
        mock_send_file.assert_not_called()


class TestToolCreateAttachmentTextFile:
    def test_create_success(self, mock_flask_g, mocker):
        # 正常系: text/filenameからcreate_attachment_fileが呼ばれ、その結果を元に
        # message付きのdictが返ること
        meta = {"file_id": "fileid_1", "filename": "note.txt", "mime_type": "text/plain", "size": 11}
        mock_create = mocker.patch("tools.attachment_file.create_attachment_file", return_value=meta)

        result = attachment_file.tool_create_attachment_text_file(
            {"filename": "note.txt", "text": "hello world"},
            {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": "user-1"},
        )

        assert result["file_id"] == "fileid_1"
        assert result["filename"] == "note.txt"
        assert result["mime_type"] == "text/plain"
        assert result["size"] == 11
        assert result["message"] == "Attachment text file created successfully."
        mock_create.assert_called_once_with(
            ORG_ID, WS_ID, "user-1", "note.txt", "text/plain", b"hello world"
        )

    def test_create_custom_mime_type(self, mock_flask_g, mocker):
        # 正常系: mime_typeを指定した場合、指定したmime_typeがそのまま使われること
        meta = {"file_id": "fileid_2", "filename": "a.html", "mime_type": "text/html", "size": 5}
        mock_create = mocker.patch("tools.attachment_file.create_attachment_file", return_value=meta)

        attachment_file.tool_create_attachment_text_file(
            {"filename": "a.html", "text": "<p/>", "mime_type": "text/html"},
            {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": "user-1"},
        )

        assert mock_create.call_args[0][4] == "text/html"

    def test_create_missing_filename_raises(self, mock_flask_g, mocker):
        # 異常系: filenameが指定されていない場合、例外が発生すること
        mocker.patch("tools.attachment_file.create_attachment_file")

        with pytest.raises(Exception, match="filename is required"):
            attachment_file.tool_create_attachment_text_file(
                {"text": "hello"}, {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": "user-1"}
            )

    def test_create_missing_text_defaults_to_empty_string(self, mock_flask_g, mocker):
        # 境界値: textが未指定の場合は空文字として登録されること
        meta = {"file_id": "fileid_3", "filename": "empty.txt", "mime_type": "text/plain", "size": 0}
        mock_create = mocker.patch("tools.attachment_file.create_attachment_file", return_value=meta)

        attachment_file.tool_create_attachment_text_file(
            {"filename": "empty.txt"}, {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": "user-1"}
        )

        assert mock_create.call_args[0][5] == b""


class TestToolGetAttachmentTextFile:
    def test_get_success(self, mock_flask_g, mocker):
        # 正常系: fetch_attachment_fileが返す内容がutf-8としてデコードされ返ること
        file_data = {"filename": "note.txt", "mime_type": "text/plain", "content": "hello".encode("utf-8")}
        mocker.patch("tools.attachment_file.fetch_attachment_file", return_value=file_data)

        result = attachment_file.tool_get_attachment_text_file(
            {"file_id": "fileid_1"}, {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": "user-1"}
        )

        assert result["file_id"] == "fileid_1"
        assert result["filename"] == "note.txt"
        assert result["mime_type"] == "text/plain"
        assert result["text"] == "hello"
        assert result["message"] == "Attachment text file content fetched successfully."

    def test_get_custom_encoding(self, mock_flask_g, mocker):
        # 正常系: encodingを指定した場合、そのエンコーディングでデコードされること
        file_data = {"filename": "note.txt", "mime_type": "text/plain", "content": "hello".encode("utf-16")}
        mocker.patch("tools.attachment_file.fetch_attachment_file", return_value=file_data)

        result = attachment_file.tool_get_attachment_text_file(
            {"file_id": "fileid_1", "encoding": "utf-16"},
            {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": "user-1"},
        )

        assert result["text"] == "hello"

    def test_get_missing_file_id_raises(self, mock_flask_g):
        # 異常系: file_idが指定されていない場合、例外が発生すること
        with pytest.raises(Exception, match="file_id is required"):
            attachment_file.tool_get_attachment_text_file(
                {}, {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": "user-1"}
            )

    def test_get_file_not_found_raises(self, mock_flask_g, mocker):
        # 異常系: fetch_attachment_fileがNoneを返す場合、file_idを含む例外が発生すること
        mocker.patch("tools.attachment_file.fetch_attachment_file", return_value=None)

        with pytest.raises(Exception, match="File not found: fileid_missing"):
            attachment_file.tool_get_attachment_text_file(
                {"file_id": "fileid_missing"},
                {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": "user-1"},
            )

    def test_get_unknown_encoding_raises(self, mock_flask_g, mocker):
        # 異常系: 存在しないエンコーディング名を指定した場合(LookupError)、
        # デコード失敗の例外が発生すること
        file_data = {"filename": "note.txt", "mime_type": "text/plain", "content": b"hello"}
        mocker.patch("tools.attachment_file.fetch_attachment_file", return_value=file_data)

        with pytest.raises(Exception, match="Failed to decode file content as 'no-such-encoding'"):
            attachment_file.tool_get_attachment_text_file(
                {"file_id": "fileid_1", "encoding": "no-such-encoding"},
                {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": "user-1"},
            )

    def test_get_invalid_utf8_raises(self, mock_flask_g, mocker):
        # 異常系: バイナリ内容がutf-8としてデコードできない場合(UnicodeDecodeError)、
        # デコード失敗の例外が発生すること
        file_data = {"filename": "note.bin", "mime_type": "application/octet-stream", "content": b"\xff\xfe"}
        mocker.patch("tools.attachment_file.fetch_attachment_file", return_value=file_data)

        with pytest.raises(Exception, match="Failed to decode file content as 'utf-8'"):
            attachment_file.tool_get_attachment_text_file(
                {"file_id": "fileid_1"},
                {"organization_id": ORG_ID, "workspace_id": WS_ID, "user_id": "user-1"},
            )


class TestCreateAttachmentFile:
    def test_create_attachment_file_success(self, mock_db_ws, mock_dbca):
        # 正常系: file_idが"fileid_"始まりで発行され、DB接続がdisconnectされ、
        # メタ情報が正しく返ること
        meta = attachment_file.create_attachment_file(
            ORG_ID, WS_ID, "user-1", "a.txt", "text/plain", b"hello"
        )

        assert meta["file_id"] == "fileid_generated-uuid"
        assert meta["filename"] == "a.txt"
        assert meta["mime_type"] == "text/plain"
        assert meta["size"] == 5
        mock_dbca.db_disconnect.assert_called_once()
        mock_dbca.sql_execute.assert_called_once()

    def test_create_attachment_file_disconnects_on_error(self, mock_db_ws, mock_dbca):
        # 異常系: sql_executeが例外を発生させた場合でも、db_disconnectが呼ばれ、
        # 元の例外がそのまま伝播すること
        mock_dbca.sql_execute.side_effect = RuntimeError("db down")

        with pytest.raises(RuntimeError, match="db down"):
            attachment_file.create_attachment_file(
                ORG_ID, WS_ID, "user-1", "a.txt", "text/plain", b"hello"
            )

        mock_dbca.db_disconnect.assert_called_once()

    def test_create_attachment_file_multiple_chunks(self, mock_db_ws, mock_dbca):
        # 境界値: CHUNK_SIZEを超えるファイルは複数レコードに分割してINSERTされること
        content = b"a" * (attachment_file.CHUNK_SIZE + 1)

        meta = attachment_file.create_attachment_file(
            ORG_ID, WS_ID, "user-1", "big.bin", "application/octet-stream", content
        )

        assert meta["size"] == attachment_file.CHUNK_SIZE + 1
        assert mock_dbca.sql_execute.call_count == 2


class TestFetchAttachmentFile:
    def test_fetch_success_concatenates_chunks(self, mock_db_ws, mock_dbca):
        # 正常系: SEQ_NO順の複数チャンクがFILE_DATAとして連結されること
        mock_dbca.table_select.return_value = [
            {"SEQ_NO": 1, "FILE_NAME": "a.txt", "MIME_TYPE": "text/plain", "FILE_DATA": b"hello "},
            {"SEQ_NO": 2, "FILE_NAME": "a.txt", "MIME_TYPE": "text/plain", "FILE_DATA": b"world"},
        ]

        result = attachment_file.fetch_attachment_file(ORG_ID, WS_ID, "user-1", "fileid_1")

        assert result == {"filename": "a.txt", "mime_type": "text/plain", "content": b"hello world"}
        mock_dbca.db_disconnect.assert_called_once()

    def test_fetch_no_rows_returns_none(self, mock_db_ws, mock_dbca):
        # 異常系: 該当行が無い場合はNoneを返すこと
        mock_dbca.table_select.return_value = []

        result = attachment_file.fetch_attachment_file(ORG_ID, WS_ID, "user-1", "fileid_missing")

        assert result is None
        mock_dbca.db_disconnect.assert_called_once()

    def test_fetch_missing_first_chunk_returns_none(self, mock_db_ws, mock_dbca):
        # 境界値: 先頭行(SEQ_NO=1)が無い場合は、行があってもNoneを返すこと
        mock_dbca.table_select.return_value = [
            {"SEQ_NO": 2, "FILE_NAME": "a.txt", "MIME_TYPE": "text/plain", "FILE_DATA": b"world"},
        ]

        result = attachment_file.fetch_attachment_file(ORG_ID, WS_ID, "user-1", "fileid_1")

        assert result is None

    def test_fetch_disconnects_on_error(self, mock_db_ws, mock_dbca):
        # 異常系: table_selectが例外を発生させた場合でも、db_disconnectが呼ばれ、
        # 元の例外がそのまま伝播すること
        mock_dbca.table_select.side_effect = RuntimeError("db down")

        with pytest.raises(RuntimeError, match="db down"):
            attachment_file.fetch_attachment_file(ORG_ID, WS_ID, "user-1", "fileid_1")

        mock_dbca.db_disconnect.assert_called_once()


class TestInsertAttachmentChunks:
    def test_insert_single_chunk(self, mock_dbca):
        # 正常系: CHUNK_SIZE以下のファイルは1レコードのみ登録され、
        # トランザクションがcommitされること
        count = attachment_file._insert_attachment_chunks(
            mock_dbca, "user-1", "fileid_1", "a.txt", "text/plain", b"hello"
        )

        assert count == 1
        mock_dbca.sql_execute.assert_called_once()
        mock_dbca.db_transaction_start.assert_called_once()
        mock_dbca.db_transaction_end.assert_called_once_with(True)

    def test_insert_empty_content_inserts_one_row(self, mock_dbca):
        # 境界値: 0byteのファイルでも1レコードだけ登録されること
        count = attachment_file._insert_attachment_chunks(
            mock_dbca, "user-1", "fileid_1", "empty.txt", "text/plain", b""
        )

        assert count == 1
        mock_dbca.sql_execute.assert_called_once()
        inserted_values = mock_dbca.sql_execute.call_args[0][1]
        assert inserted_values[5] == 0  # FILE_SIZE
        assert inserted_values[6] == b""  # FILE_DATA

    def test_insert_multiple_chunks_exact_boundary(self, mock_dbca):
        # 境界値: ちょうどCHUNK_SIZEのファイルは1レコード、CHUNK_SIZE+1byteは2レコードになること
        exact = b"a" * attachment_file.CHUNK_SIZE
        count_exact = attachment_file._insert_attachment_chunks(
            mock_dbca, "user-1", "fileid_1", "a.bin", "application/octet-stream", exact
        )
        assert count_exact == 1

        mock_dbca.reset_mock()
        over = b"a" * (attachment_file.CHUNK_SIZE + 1)
        count_over = attachment_file._insert_attachment_chunks(
            mock_dbca, "user-1", "fileid_1", "a.bin", "application/octet-stream", over
        )
        assert count_over == 2
        assert mock_dbca.sql_execute.call_count == 2

    def test_insert_rolls_back_and_reraises_on_error(self, mock_dbca):
        # 異常系: sql_execute失敗時、db_transaction_end(False)が呼ばれ、
        # 元の例外がそのまま伝播すること
        mock_dbca.sql_execute.side_effect = RuntimeError("insert failed")

        with pytest.raises(RuntimeError, match="insert failed"):
            attachment_file._insert_attachment_chunks(
                mock_dbca, "user-1", "fileid_1", "a.txt", "text/plain", b"hello"
            )

        mock_dbca.db_transaction_end.assert_called_once_with(False)

    def test_insert_sql_contains_table_name(self, mock_dbca):
        # 正常系: 発行されるSQLにテーブル名・INSERT対象カラムが含まれること
        attachment_file._insert_attachment_chunks(
            mock_dbca, "user-1", "fileid_1", "a.txt", "text/plain", b"hello"
        )

        sql_arg = mock_dbca.sql_execute.call_args[0][0]
        assert "T_AI_ATTACHMENT_FILE" in sql_arg
        assert "FILE_ID" in sql_arg
        assert "FILE_DATA" in sql_arg


class TestFetchAttachmentMeta:
    def test_meta_found(self, mock_db_ws, mock_dbca):
        # 正常系: 該当行がある場合、filename/mime_type/sizeを返すこと
        mock_dbca.sql_execute.return_value = [
            {"FILE_NAME": "a.txt", "MIME_TYPE": "text/plain", "FILE_SIZE": 5},
        ]

        result = attachment_file._fetch_attachment_meta(ORG_ID, WS_ID, "user-1", "fileid_1")

        assert result == {"filename": "a.txt", "mime_type": "text/plain", "size": 5}
        mock_dbca.db_disconnect.assert_called_once()

    def test_meta_not_found_returns_none(self, mock_db_ws, mock_dbca):
        # 異常系: 該当行が無い場合はNoneを返すこと
        mock_dbca.sql_execute.return_value = []

        result = attachment_file._fetch_attachment_meta(ORG_ID, WS_ID, "user-1", "fileid_missing")

        assert result is None
        mock_dbca.db_disconnect.assert_called_once()

    def test_meta_disconnects_on_error(self, mock_db_ws, mock_dbca):
        # 異常系: sql_executeが例外を発生させた場合でも、db_disconnectが呼ばれ、
        # 元の例外がそのまま伝播すること
        mock_dbca.sql_execute.side_effect = RuntimeError("db down")

        with pytest.raises(RuntimeError, match="db down"):
            attachment_file._fetch_attachment_meta(ORG_ID, WS_ID, "user-1", "fileid_1")

        mock_dbca.db_disconnect.assert_called_once()


class TestGetLastUpdateTimestampNow:
    def test_returns_naive_datetime_default_tz(self, monkeypatch):
        # 正常系: TZ未設定の場合でも、tzinfoを持たないnaiveなdatetimeが返ること
        monkeypatch.delenv("TZ", raising=False)

        result = attachment_file._get_last_update_timestamp_now()

        assert result.tzinfo is None

    def test_returns_naive_datetime_custom_tz(self, monkeypatch):
        # 境界値: TZ環境変数を指定した場合でも、tzinfoを持たないnaiveなdatetimeが返ること
        monkeypatch.setenv("TZ", "Asia/Tokyo")

        result = attachment_file._get_last_update_timestamp_now()

        assert result.tzinfo is None
