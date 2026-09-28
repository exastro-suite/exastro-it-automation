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
#
"""
添付ファイルzip化ツール ("create-attachment-zip-file")

複数のfile_idをzip化して新しいfile_idを発行するツール。zipに入れる各
ファイルの指定は、file_idの単純なリストではなく {"file_id": "<file_id>",
"path": "zip内の格納ディレクトリ"} のリストで受け取る。これにより、zip内で
ファイルをディレクトリ分けして格納できる。

zipに含める各ファイルはattachment_file.pyのfetch_attachment_file()で
(file_id・user_idを条件に)T_AI_ATTACHMENT_FILEから取得し、作成したzip本体は
attachment_file.pyのcreate_attachment_file()で新しい添付ファイルとして
同テーブルに登録する。

--------------------------------------------------------------------------
Attachment ZIP file creation tool ("create-attachment-zip-file")

Bundles multiple files (referenced by file_id) into a ZIP and issues a new
file_id. Each file to include in the ZIP is specified not as a plain list of
file_id values, but as a list of
{"file_id": "<file_id>", "path": "directory inside the ZIP"} entries. This
lets files be organized into directories inside the ZIP.

Each file to include is fetched from T_AI_ATTACHMENT_FILE (by file_id/user_id)
via attachment_file.py's fetch_attachment_file(), and the resulting ZIP
content is registered as a new attachment file into the same table via
attachment_file.py's create_attachment_file().
"""
import io
import posixpath
import time
import zipfile

from flask import g

from libs import tool
from .attachment_file import create_attachment_file, fetch_attachment_file

DEFAULT_ZIP_FILENAME = "archive.zip"
DEFAULT_FILE_PERMISSIONS = "644"


@tool(
    name="create-attachment-zip-file",
    description=(
        "Bundle one or more existing attachment files (referenced by their file_id) into a single "
        "ZIP archive, optionally placing each file under a given directory path inside the "
        "archive, and register the resulting archive as a new attachment file, returning a new "
        "file_id. Use this when you need to deliver multiple attachment files as one downloadable "
        "file, or when you need to produce a ZIP archive for registering files into Exastro IT "
        "Automation (ITA) — for example a custom menu and similar resources that must be uploaded "
        "to ITA as a ZIP. Duplicate filenames within the same directory path are automatically "
        "disambiguated."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": "file_id of the attachment file to include."
                        },
                        "path": {
                            "type": "string",
                            "description": (
                                "Directory path inside the ZIP archive to store the file under "
                                "(e.g. 'docs/sub'). Optional; defaults to the archive root."
                            )
                        },
                        "permissions": {
                            "type": "string",
                            "description": (
                                "Unix permission bits (octal, e.g. '644' or '755') to set on this "
                                "specific file inside the ZIP archive. Optional; defaults to the "
                                "top-level file_permissions."
                            )
                        }
                    },
                    "required": ["file_id"]
                },
                "description": (
                    "List of {file_id, path, permissions} entries specifying which attachment files "
                    "to include in the ZIP archive, which directory inside the archive to place each "
                    "one under, and (optionally) a per-file unix permission overriding file_permissions."
                ),
                "minItems": 1
            },
            "zip_filename": {
                "type": "string",
                "description": "File name for the resulting ZIP file (e.g. 'archive.zip'). Optional; defaults to 'archive.zip'."
            },
            "file_permissions": {
                "type": "string",
                "description": (
                    "Default unix permission bits (octal, e.g. '644' or '755') to set on each file "
                    "stored inside the ZIP archive, used for files that don't specify their own "
                    "'permissions' in the files list. Optional; defaults to '644'."
                )
            }
        },
        "required": ["files"]
    }
)
def tool_create_attachment_zip_file(arguments: dict, payload: dict) -> dict:
    """
    複数の添付ファイルをzip化し、新しい添付ファイルとしてT_AI_ATTACHMENT_FILEに登録する

    Bundle multiple attachment files into a ZIP and register it as a new
    attachment file into T_AI_ATTACHMENT_FILE.

    Parameters:
        arguments (dict): ツールの引数
            - files (list[dict]): zip化対象。各要素は以下を持つ
                - file_id (str): 対象ファイルのID / id of the file to include
                - path (str, optional): zip内の格納ディレクトリ
                    (デフォルト: zipのルート) / directory inside the ZIP
                    to store the file under (default: the archive root)
                - permissions (str, optional): このファイル個別のUnix
                    パーミッション(8進数の文字列、例: '644')。未指定の場合は
                    file_permissionsを使う / unix permission bits (octal
                    string) for this specific file. Falls back to
                    file_permissions when not specified.
            - zip_filename (str, optional): 出力するzipファイル名
                (デフォルト: 'archive.zip') / output zip file name
                (default: 'archive.zip')
            - file_permissions (str, optional): permissionsを指定しない
                ファイルに使うデフォルトのUnixパーミッション(8進数の文字列、
                例: '644')(デフォルト: '644') / default unix permission bits
                (octal string, e.g. '644') used for files that don't specify
                their own permissions (default: '644')
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
            - user_id (str): 呼び出しユーザーのID / calling user's id

    Returns:
        dict: 作成結果
            - file_id (str): 発行されたzipファイルのID / issued file id of the zip file
            - filename (str): zipファイル名 / zip file name
            - mime_type (str): MIMEタイプ("application/zip") / mime type ("application/zip")
            - size (int): zipファイルサイズ(バイト) / zip file size (bytes)
            - included_files (list): アーカイブに含めたファイルの一覧
                (file_id/filename/size) / list of files included in the
                archive (file_id/filename/size)
            - message (str): 処理結果メッセージ / result message

    Raises:
        Exception: filesが指定されていない、各要素にfile_idが無い、
            file_permissions/permissionsが8進数のパーミッション文字列として
            解釈できない、または対象ファイルが存在しない場合 / if files is
            missing, an entry is missing file_id, file_permissions/
            permissions cannot be parsed as an octal permission string, or a
            referenced file cannot be found
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")
    user_id = payload.get("user_id")
    files = arguments.get("files") or []
    zip_filename = arguments.get("zip_filename") or DEFAULT_ZIP_FILENAME
    file_permissions = arguments.get("file_permissions") or DEFAULT_FILE_PERMISSIONS

    if not isinstance(files, list) or len(files) == 0:
        raise Exception("files is required and must be a non-empty list")

    default_file_mode = _parse_permission_mode(file_permissions, "file_permissions")

    if not zip_filename.lower().endswith(".zip"):
        zip_filename = "{}.zip".format(zip_filename)

    buffer = io.BytesIO()
    included_files = []
    used_names = set()

    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for entry in files:
            if not isinstance(entry, dict) or not entry.get("file_id"):
                raise Exception("each entry in files must be an object containing file_id")

            file_id = entry["file_id"]
            path = entry.get("path") or ""
            entry_permissions = entry.get("permissions")
            entry_mode = (
                _parse_permission_mode(entry_permissions, "permissions for file_id '{}'".format(file_id))
                if entry_permissions
                else default_file_mode
            )

            file_data = fetch_attachment_file(organization_id, workspace_id, user_id, file_id)
            if file_data is None:
                g.applogger.info("create-attachment-zip-file: file not found (file_id={})".format(file_id))
                raise Exception("File not found: {}".format(file_id))

            arcname = _unique_arcname(path, file_data.get("filename") or file_id, used_names)
            zinfo = zipfile.ZipInfo(arcname, date_time=time.localtime(time.time())[:6])
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            zinfo.external_attr = entry_mode << 16
            zf.writestr(zinfo, file_data["content"])

            included_files.append({
                "file_id": file_id,
                "filename": arcname,
                "size": len(file_data["content"]),
            })

    zip_bytes = buffer.getvalue()

    meta = create_attachment_file(organization_id, workspace_id, user_id, zip_filename, "application/zip", zip_bytes)

    g.applogger.info("Attachment zip file created: file_id={}, size={}, included={}".format(
        meta["file_id"], meta["size"], len(included_files)))

    return {
        "file_id": meta["file_id"],
        "filename": meta["filename"],
        "mime_type": meta["mime_type"],
        "size": meta["size"],
        "included_files": included_files,
        "message": "ZIP file created successfully with {} file(s).".format(len(included_files))
    }


def _parse_permission_mode(value, param_name):
    """
    8進数のパーミッション文字列をintのmodeに変換する

    Parse an octal permission string into an int mode.

    Args:
        value (str): パーミッションを表す8進数文字列(例: '644')
            / octal permission string (e.g. '644')
        param_name (str): 解析に失敗した際のエラーメッセージに使う
            パラメータ名 / parameter name used in the error message on
            parse failure

    Returns:
        int: パーミッションのmode(例: 0o644) / permission mode (e.g. 0o644)

    Raises:
        Exception: valueが8進数のパーミッション文字列として解釈できない場合
            / if value cannot be parsed as an octal permission string
    """
    try:
        return int(str(value), 8)
    except ValueError:
        raise Exception("{} must be an octal permission string, e.g. '644'".format(param_name))


def _sanitize_zip_path(path):
    """
    zip内の格納ディレクトリを正規化する

    "\\"は"/"に統一し、先頭の"/"(絶対パス化)や"."・".."を含むセグメントを
    除去することで、zip展開時にアーカイブ外へ書き込まれる(いわゆる
    zip slip)パスが作られないようにする。

    Normalize a directory path to store inside the ZIP archive.

    "\\" is unified to "/", and any leading "/" (which would make the path
    absolute) or "."/".." segments are stripped, so that extracting the
    archive later can never write outside of it (the so-called zip slip
    issue).

    Args:
        path (str): 呼び出し元が指定した格納ディレクトリ
            / the directory path given by the caller

    Returns:
        str: 正規化後のディレクトリパス(空文字はルート)
            / the normalized directory path ("" means the archive root)
    """
    if not path:
        return ""

    normalized = path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part not in ("", ".", "..")]
    return "/".join(parts)


def _unique_arcname(path, filename, used_names):
    """
    zip内でパスが重複しないよう一意なアーカイブ内パスを返す

    Return a unique in-archive path so that entries never collide inside the ZIP.

    Args:
        path (str): zip内の格納ディレクトリ(_sanitize_zip_pathで正規化する)
            / directory inside the ZIP (normalized via _sanitize_zip_path)
        filename (str): 元のファイル名 / the original file name
        used_names (set): 既に使用済みのアーカイブ内パスの集合
            (この関数内で更新される) / set of already-used in-archive paths
            (updated in place by this function)

    Returns:
        str: zip内で一意なパス / a unique in-archive path
    """
    directory = _sanitize_zip_path(path)
    base_name = filename or "file"
    arcname = posixpath.join(directory, base_name) if directory else base_name

    if arcname not in used_names:
        used_names.add(arcname)
        return arcname

    if "." in base_name:
        stem, ext = base_name.rsplit(".", 1)
        ext = ".{}".format(ext)
    else:
        stem, ext = base_name, ""

    counter = 1
    while True:
        candidate_name = "{}_{}{}".format(stem, counter, ext)
        candidate = posixpath.join(directory, candidate_name) if directory else candidate_name
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        counter += 1
