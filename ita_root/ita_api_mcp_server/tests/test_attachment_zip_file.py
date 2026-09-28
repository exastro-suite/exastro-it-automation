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
tools/attachment_zip_file.py (create-attachment-zip-file) のユニットテスト

attachment_file.py の create_attachment_file / fetch_attachment_file は
tools.attachment_zip_file モジュール内の参照を mocker.patch で差し替え、
実際のDB/ファイルシステムアクセスは発生させない(zipfile自体は標準ライブラリを
そのまま使う)。

異常系では、g.applogger.info の呼び出し回数はチェックしない(ログ出力を
増減しただけでテストが壊れるのは望ましくないため)。代わりに、送出される
例外のメッセージ・戻り値の内容で検証する。
"""
import io
import zipfile

import pytest

from tools import attachment_zip_file


def _fetch_side_effect(files_by_id):
    """fetch_attachment_file のside_effectを作る簡易ヘルパー"""
    def _fetch(organization_id, workspace_id, user_id, file_id):
        return files_by_id.get(file_id)
    return _fetch


class TestToolCreateAttachmentZipFile:
    def test_create_zip_success_single_file(self, mock_flask_g, mocker):
        # 正常系: 1ファイルをzip化し、create_attachment_fileへ渡されるzip本体に
        # 対象ファイルが正しく格納され、戻り値のメタ情報がそのまま反映されること
        mock_fetch = mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            return_value={"filename": "hello.txt", "mime_type": "text/plain", "content": b"hello world"},
        )
        mock_create = mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={
                "file_id": "fileid_zip-1",
                "filename": "archive.zip",
                "mime_type": "application/zip",
                "size": 999,
            },
        )

        arguments = {"files": [{"file_id": "file-1"}]}
        payload = {"organization_id": "org-1", "workspace_id": "ws-1", "user_id": "user-1"}

        result = attachment_zip_file.tool_create_attachment_zip_file(arguments, payload)

        # fetch_attachment_fileが正しい引数で呼ばれていること
        mock_fetch.assert_called_once_with("org-1", "ws-1", "user-1", "file-1")

        # create_attachment_fileに渡されたzip本体を検証する
        assert mock_create.call_count == 1
        call_args = mock_create.call_args[0]
        assert call_args[0] == "org-1"
        assert call_args[1] == "ws-1"
        assert call_args[2] == "user-1"
        assert call_args[3] == "archive.zip"
        assert call_args[4] == "application/zip"
        zip_bytes = call_args[5]

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert zf.namelist() == ["hello.txt"]
            assert zf.read("hello.txt") == b"hello world"

        assert result["file_id"] == "fileid_zip-1"
        assert result["filename"] == "archive.zip"
        assert result["mime_type"] == "application/zip"
        assert result["size"] == 999
        assert result["included_files"] == [
            {"file_id": "file-1", "filename": "hello.txt", "size": len(b"hello world")}
        ]
        assert result["message"] == "ZIP file created successfully with 1 file(s)."

    def test_create_zip_success_multiple_files_with_paths(self, mock_flask_g, mocker):
        # 正常系: 複数ファイルをpath指定付きでzip化し、それぞれのディレクトリに
        # 格納されること、included_filesに全件反映されること
        files_by_id = {
            "file-1": {"filename": "a.txt", "mime_type": "text/plain", "content": b"AAA"},
            "file-2": {"filename": "b.png", "mime_type": "image/png", "content": b"\x89PNG"},
        }
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            side_effect=_fetch_side_effect(files_by_id),
        )
        mock_create = mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={
                "file_id": "fileid_zip-2",
                "filename": "bundle.zip",
                "mime_type": "application/zip",
                "size": 111,
            },
        )

        arguments = {
            "files": [
                {"file_id": "file-1", "path": "docs"},
                {"file_id": "file-2", "path": "images/sub"},
            ],
            "zip_filename": "bundle.zip",
        }
        payload = {"organization_id": "org-2", "workspace_id": "ws-2", "user_id": "user-2"}

        result = attachment_zip_file.tool_create_attachment_zip_file(arguments, payload)

        zip_bytes = mock_create.call_args[0][5]
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = set(zf.namelist())
            assert names == {"docs/a.txt", "images/sub/b.png"}
            assert zf.read("docs/a.txt") == b"AAA"
            assert zf.read("images/sub/b.png") == b"\x89PNG"

        assert len(result["included_files"]) == 2
        assert result["included_files"][0] == {"file_id": "file-1", "filename": "docs/a.txt", "size": 3}
        assert result["included_files"][1] == {"file_id": "file-2", "filename": "images/sub/b.png", "size": 4}
        assert result["message"] == "ZIP file created successfully with 2 file(s)."

    def test_zip_filename_defaults_to_archive_zip(self, mock_flask_g, mocker):
        # 境界値: zip_filenameを指定しない場合、DEFAULT_ZIP_FILENAME("archive.zip")が使われること
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            return_value={"filename": "f.txt", "mime_type": "text/plain", "content": b"x"},
        )
        mock_create = mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "archive.zip", "mime_type": "application/zip", "size": 1},
        )

        attachment_zip_file.tool_create_attachment_zip_file(
            {"files": [{"file_id": "file-1"}]}, {"organization_id": "o", "workspace_id": "w", "user_id": "u"}
        )

        assert mock_create.call_args[0][3] == "archive.zip"

    def test_zip_filename_extension_is_appended_when_missing(self, mock_flask_g, mocker):
        # 境界値: zip_filenameに".zip"拡張子が無い場合は自動的に付与されること
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            return_value={"filename": "f.txt", "mime_type": "text/plain", "content": b"x"},
        )
        mock_create = mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "mybundle.zip", "mime_type": "application/zip", "size": 1},
        )

        attachment_zip_file.tool_create_attachment_zip_file(
            {"files": [{"file_id": "file-1"}], "zip_filename": "mybundle"},
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        assert mock_create.call_args[0][3] == "mybundle.zip"

    def test_zip_filename_extension_not_duplicated_case_insensitive(self, mock_flask_g, mocker):
        # 境界値: 既に大文字/小文字を含む".zip"/".ZIP"拡張子が付いている場合は
        # 二重に付与されないこと
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            return_value={"filename": "f.txt", "mime_type": "text/plain", "content": b"x"},
        )
        mock_create = mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "MyBundle.ZIP", "mime_type": "application/zip", "size": 1},
        )

        attachment_zip_file.tool_create_attachment_zip_file(
            {"files": [{"file_id": "file-1"}], "zip_filename": "MyBundle.ZIP"},
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        assert mock_create.call_args[0][3] == "MyBundle.ZIP"

    def test_file_permissions_default_is_644(self, mock_flask_g, mocker):
        # 境界値: file_permissionsを指定しない場合、zip内の各ファイルの
        # unixパーミッションが644になること
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            return_value={"filename": "f.txt", "mime_type": "text/plain", "content": b"x"},
        )
        mock_create = mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "archive.zip", "mime_type": "application/zip", "size": 1},
        )

        attachment_zip_file.tool_create_attachment_zip_file(
            {"files": [{"file_id": "file-1"}]},
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        zip_bytes = mock_create.call_args[0][5]
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert zf.getinfo("f.txt").external_attr >> 16 == 0o644

    def test_file_permissions_custom_value_applied(self, mock_flask_g, mocker):
        # 正常系: file_permissionsを指定した場合、zip内の各ファイルの
        # unixパーミッションに反映されること
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            return_value={"filename": "f.sh", "mime_type": "text/plain", "content": b"x"},
        )
        mock_create = mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "archive.zip", "mime_type": "application/zip", "size": 1},
        )

        attachment_zip_file.tool_create_attachment_zip_file(
            {"files": [{"file_id": "file-1"}], "file_permissions": "755"},
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        zip_bytes = mock_create.call_args[0][5]
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert zf.getinfo("f.sh").external_attr >> 16 == 0o755

    def test_file_permissions_invalid_value_raises(self, mock_flask_g, mocker):
        # 異常系: file_permissionsが8進数として解釈できない場合は例外が発生すること
        mock_fetch = mocker.patch("tools.attachment_zip_file.fetch_attachment_file")
        mocker.patch("tools.attachment_zip_file.create_attachment_file")

        with pytest.raises(Exception) as exc_info:
            attachment_zip_file.tool_create_attachment_zip_file(
                {"files": [{"file_id": "file-1"}], "file_permissions": "abc"},
                {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
            )

        assert str(exc_info.value) == "file_permissions must be an octal permission string, e.g. '644'"
        mock_fetch.assert_not_called()

    def test_per_file_permissions_override_default(self, mock_flask_g, mocker):
        # 正常系: filesの各要素にpermissionsを指定した場合、そのファイルだけに
        # 個別のパーミッションが反映され、指定の無いファイルはfile_permissions
        # (またはデフォルトの644)が使われること
        files_by_id = {
            "file-1": {"filename": "script.sh", "mime_type": "text/plain", "content": b"#!/bin/sh"},
            "file-2": {"filename": "plain.txt", "mime_type": "text/plain", "content": b"x"},
        }
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            side_effect=_fetch_side_effect(files_by_id),
        )
        mock_create = mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "archive.zip", "mime_type": "application/zip", "size": 1},
        )

        attachment_zip_file.tool_create_attachment_zip_file(
            {
                "files": [
                    {"file_id": "file-1", "permissions": "755"},
                    {"file_id": "file-2"},
                ]
            },
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        zip_bytes = mock_create.call_args[0][5]
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert zf.getinfo("script.sh").external_attr >> 16 == 0o755
            assert zf.getinfo("plain.txt").external_attr >> 16 == 0o644

    def test_per_file_permissions_override_custom_file_permissions_default(self, mock_flask_g, mocker):
        # 境界値: file_permissionsでデフォルトを変更していても、
        # permissionsを指定したファイルはそちらが優先されること
        files_by_id = {
            "file-1": {"filename": "a.txt", "mime_type": "text/plain", "content": b"a"},
            "file-2": {"filename": "b.txt", "mime_type": "text/plain", "content": b"b"},
        }
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            side_effect=_fetch_side_effect(files_by_id),
        )
        mock_create = mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "archive.zip", "mime_type": "application/zip", "size": 1},
        )

        attachment_zip_file.tool_create_attachment_zip_file(
            {
                "files": [
                    {"file_id": "file-1", "permissions": "600"},
                    {"file_id": "file-2"},
                ],
                "file_permissions": "755",
            },
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        zip_bytes = mock_create.call_args[0][5]
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert zf.getinfo("a.txt").external_attr >> 16 == 0o600
            assert zf.getinfo("b.txt").external_attr >> 16 == 0o755

    def test_per_file_invalid_permissions_raises_with_file_id(self, mock_flask_g, mocker):
        # 異常系: filesの要素のpermissionsが8進数として解釈できない場合、
        # file_idを含む例外メッセージが発生すること
        mock_fetch = mocker.patch("tools.attachment_zip_file.fetch_attachment_file")
        mocker.patch("tools.attachment_zip_file.create_attachment_file")

        with pytest.raises(Exception) as exc_info:
            attachment_zip_file.tool_create_attachment_zip_file(
                {"files": [{"file_id": "file-1", "permissions": "xyz"}]},
                {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
            )

        assert str(exc_info.value) == (
            "permissions for file_id 'file-1' must be an octal permission string, e.g. '644'"
        )
        mock_fetch.assert_not_called()

    def test_files_missing_raises(self, mock_flask_g, mocker):
        # 異常系: filesが指定されていない場合は例外が発生すること
        mock_fetch = mocker.patch("tools.attachment_zip_file.fetch_attachment_file")
        mocker.patch("tools.attachment_zip_file.create_attachment_file")

        with pytest.raises(Exception) as exc_info:
            attachment_zip_file.tool_create_attachment_zip_file({}, {})

        assert str(exc_info.value) == "files is required and must be a non-empty list"
        mock_fetch.assert_not_called()

    def test_files_empty_list_raises(self, mock_flask_g, mocker):
        # 異常系: filesが空リストの場合は例外が発生すること
        mocker.patch("tools.attachment_zip_file.fetch_attachment_file")
        mocker.patch("tools.attachment_zip_file.create_attachment_file")

        with pytest.raises(Exception) as exc_info:
            attachment_zip_file.tool_create_attachment_zip_file({"files": []}, {})

        assert str(exc_info.value) == "files is required and must be a non-empty list"

    def test_files_not_a_list_raises(self, mock_flask_g, mocker):
        # 異常系: filesがリストでない場合は例外が発生すること
        mocker.patch("tools.attachment_zip_file.fetch_attachment_file")
        mocker.patch("tools.attachment_zip_file.create_attachment_file")

        with pytest.raises(Exception) as exc_info:
            attachment_zip_file.tool_create_attachment_zip_file({"files": "file-1"}, {})

        assert str(exc_info.value) == "files is required and must be a non-empty list"

    def test_entry_not_dict_raises(self, mock_flask_g, mocker):
        # 異常系: filesの要素がdictでない場合は例外が発生すること
        mock_fetch = mocker.patch("tools.attachment_zip_file.fetch_attachment_file")
        mocker.patch("tools.attachment_zip_file.create_attachment_file")

        with pytest.raises(Exception) as exc_info:
            attachment_zip_file.tool_create_attachment_zip_file({"files": ["file-1"]}, {})

        assert str(exc_info.value) == "each entry in files must be an object containing file_id"
        mock_fetch.assert_not_called()

    def test_entry_missing_file_id_raises(self, mock_flask_g, mocker):
        # 異常系: filesの要素にfile_idが無い場合は例外が発生すること
        mocker.patch("tools.attachment_zip_file.fetch_attachment_file")
        mocker.patch("tools.attachment_zip_file.create_attachment_file")

        with pytest.raises(Exception) as exc_info:
            attachment_zip_file.tool_create_attachment_zip_file({"files": [{"path": "docs"}]}, {})

        assert str(exc_info.value) == "each entry in files must be an object containing file_id"

    def test_second_entry_missing_file_id_raises_after_first_processed(self, mock_flask_g, mocker):
        # 境界値: 1件目は正常に処理されるが、2件目でfile_idが無い場合はそこで例外になり、
        # create_attachment_fileは呼ばれないこと
        mock_fetch = mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            return_value={"filename": "a.txt", "mime_type": "text/plain", "content": b"AAA"},
        )
        mock_create = mocker.patch("tools.attachment_zip_file.create_attachment_file")

        with pytest.raises(Exception) as exc_info:
            attachment_zip_file.tool_create_attachment_zip_file(
                {"files": [{"file_id": "file-1"}, {"path": "docs"}]}, {}
            )

        assert str(exc_info.value) == "each entry in files must be an object containing file_id"
        assert mock_fetch.call_count == 1
        mock_create.assert_not_called()

    def test_file_not_found_raises(self, mock_flask_g, mocker):
        # 異常系: fetch_attachment_fileがNoneを返す(対象ファイルが存在しない)場合、
        # file_idを含む例外メッセージが発生すること
        mocker.patch("tools.attachment_zip_file.fetch_attachment_file", return_value=None)
        mock_create = mocker.patch("tools.attachment_zip_file.create_attachment_file")

        with pytest.raises(Exception) as exc_info:
            attachment_zip_file.tool_create_attachment_zip_file(
                {"files": [{"file_id": "missing-file"}]},
                {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
            )

        assert str(exc_info.value) == "File not found: missing-file"
        mock_create.assert_not_called()

    def test_duplicate_filenames_are_disambiguated(self, mock_flask_g, mocker):
        # 正常系: 同一ディレクトリ内で同名ファイルが複数ある場合、
        # "_1", "_2"...のように連番でリネームされzipに一意に格納されること
        files_by_id = {
            "file-1": {"filename": "report.txt", "mime_type": "text/plain", "content": b"one"},
            "file-2": {"filename": "report.txt", "mime_type": "text/plain", "content": b"two"},
            "file-3": {"filename": "report.txt", "mime_type": "text/plain", "content": b"three"},
        }
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            side_effect=_fetch_side_effect(files_by_id),
        )
        mock_create = mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "archive.zip", "mime_type": "application/zip", "size": 1},
        )

        result = attachment_zip_file.tool_create_attachment_zip_file(
            {"files": [{"file_id": "file-1"}, {"file_id": "file-2"}, {"file_id": "file-3"}]},
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        names = [f["filename"] for f in result["included_files"]]
        assert names == ["report.txt", "report_1.txt", "report_2.txt"]

        zip_bytes = mock_create.call_args[0][5]
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert set(zf.namelist()) == {"report.txt", "report_1.txt", "report_2.txt"}
            assert zf.read("report.txt") == b"one"
            assert zf.read("report_1.txt") == b"two"
            assert zf.read("report_2.txt") == b"three"

    def test_duplicate_filenames_without_extension(self, mock_flask_g, mocker):
        # 境界値: 拡張子の無いファイル名が重複する場合も"_1"サフィックスのみで
        # 一意化されること
        files_by_id = {
            "file-1": {"filename": "README", "mime_type": "text/plain", "content": b"one"},
            "file-2": {"filename": "README", "mime_type": "text/plain", "content": b"two"},
        }
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            side_effect=_fetch_side_effect(files_by_id),
        )
        mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "archive.zip", "mime_type": "application/zip", "size": 1},
        )

        result = attachment_zip_file.tool_create_attachment_zip_file(
            {"files": [{"file_id": "file-1"}, {"file_id": "file-2"}]},
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        names = [f["filename"] for f in result["included_files"]]
        assert names == ["README", "README_1"]

    def test_filename_falls_back_to_file_id_when_missing(self, mock_flask_g, mocker):
        # 境界値: fetch_attachment_fileが返すデータにfilenameが無い/空の場合、
        # アーカイブ内のファイル名としてfile_idが使われること
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            return_value={"filename": "", "mime_type": "text/plain", "content": b"data"},
        )
        mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "archive.zip", "mime_type": "application/zip", "size": 1},
        )

        result = attachment_zip_file.tool_create_attachment_zip_file(
            {"files": [{"file_id": "file-xyz"}]},
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        assert result["included_files"][0]["filename"] == "file-xyz"

    def test_zip_slip_path_traversal_is_sanitized(self, mock_flask_g, mocker):
        # 異常系/境界値: pathに".."や絶対パス("/etc")、"\\"区切りが混ざっていても、
        # アーカイブ外へ出るパスは作られず正規化されること(zip slip対策)
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            return_value={"filename": "evil.txt", "mime_type": "text/plain", "content": b"payload"},
        )
        mock_create = mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "archive.zip", "mime_type": "application/zip", "size": 1},
        )

        result = attachment_zip_file.tool_create_attachment_zip_file(
            {"files": [{"file_id": "file-1", "path": "../../etc\\passwd_dir/../sub"}]},
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        arcname = result["included_files"][0]["filename"]
        assert not arcname.startswith("/")
        assert ".." not in arcname.split("/")
        assert arcname == "etc/passwd_dir/sub/evil.txt"

        zip_bytes = mock_create.call_args[0][5]
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert zf.namelist() == ["etc/passwd_dir/sub/evil.txt"]

    def test_empty_string_path_uses_archive_root(self, mock_flask_g, mocker):
        # 境界値: pathが空文字/未指定の場合はzipのルートに格納されること
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            return_value={"filename": "root.txt", "mime_type": "text/plain", "content": b"x"},
        )
        mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={"file_id": "fid", "filename": "archive.zip", "mime_type": "application/zip", "size": 1},
        )

        result = attachment_zip_file.tool_create_attachment_zip_file(
            {"files": [{"file_id": "file-1", "path": ""}]},
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        assert result["included_files"][0]["filename"] == "root.txt"

    def test_create_attachment_file_called_with_zip_bytes_and_metadata_reflected(self, mock_flask_g, mocker):
        # 正常系: create_attachment_fileの戻り値(メタ情報)がそのままresultに反映され、
        # includedファイル数を含むメッセージが生成されること
        mocker.patch(
            "tools.attachment_zip_file.fetch_attachment_file",
            return_value={"filename": "a.txt", "mime_type": "text/plain", "content": b"data"},
        )
        mocker.patch(
            "tools.attachment_zip_file.create_attachment_file",
            return_value={
                "file_id": "fileid_custom",
                "filename": "custom.zip",
                "mime_type": "application/zip",
                "size": 12345,
            },
        )

        result = attachment_zip_file.tool_create_attachment_zip_file(
            {"files": [{"file_id": "file-1"}], "zip_filename": "custom.zip"},
            {"organization_id": "o", "workspace_id": "w", "user_id": "u"},
        )

        assert result == {
            "file_id": "fileid_custom",
            "filename": "custom.zip",
            "mime_type": "application/zip",
            "size": 12345,
            "included_files": [{"file_id": "file-1", "filename": "a.txt", "size": 4}],
            "message": "ZIP file created successfully with 1 file(s).",
        }


class TestSanitizeZipPath:
    def test_empty_path_returns_empty_string(self):
        assert attachment_zip_file._sanitize_zip_path("") == ""
        assert attachment_zip_file._sanitize_zip_path(None) == ""

    def test_backslashes_are_normalized_to_slashes(self):
        assert attachment_zip_file._sanitize_zip_path("a\\b\\c") == "a/b/c"

    def test_leading_slash_and_dot_segments_are_stripped(self):
        assert attachment_zip_file._sanitize_zip_path("/a/./b/../c") == "a/b/c"

    def test_only_dot_segments_returns_empty_string(self):
        assert attachment_zip_file._sanitize_zip_path("../..") == ""

    def test_mixed_double_slashes_are_collapsed(self):
        assert attachment_zip_file._sanitize_zip_path("a//b///c") == "a/b/c"


class TestUniqueArcname:
    def test_first_use_returns_plain_name(self):
        used = set()
        assert attachment_zip_file._unique_arcname("", "a.txt", used) == "a.txt"
        assert used == {"a.txt"}

    def test_directory_is_joined_with_filename(self):
        used = set()
        assert attachment_zip_file._unique_arcname("docs/sub", "a.txt", used) == "docs/sub/a.txt"

    def test_collision_appends_counter_with_extension_preserved(self):
        used = {"a.txt"}
        assert attachment_zip_file._unique_arcname("", "a.txt", used) == "a_1.txt"

    def test_multiple_collisions_increment_counter(self):
        used = {"a.txt", "a_1.txt", "a_2.txt"}
        assert attachment_zip_file._unique_arcname("", "a.txt", used) == "a_3.txt"

    def test_falls_back_to_file_when_filename_is_empty(self):
        used = set()
        assert attachment_zip_file._unique_arcname("", "", used) == "file"
