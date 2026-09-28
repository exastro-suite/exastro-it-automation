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
添付ファイルアップロードAPI (T_AI_ATTACHMENT_FILEへの登録)

"/api/<organization_id>/workspaces/<workspace_id>/mcp/attachment_file" で
multipart/form-dataの"file"を受け取り、メタ情報を返すインターフェースで、
ワークスペースDBのT_AI_ATTACHMENT_FILEにファイル本体を保存する。

T_AI_ATTACHMENT_FILEのFILE_DATAはMEDIUMBLOB(最大16MiB)であるため、
1レコードに収めるサイズには上限がある。そのため、ファイルサイズが
CHUNK_SIZE(2MiB)を超える場合は、CHUNK_SIZE毎に分割して複数レコードに
分けて登録する。分割した各レコードは以下の関係になる。
  - FILE_ID   : 1つのアップロードファイルに対して共通のID(全チャンクで同じ値)
  - UUID      : レコード(チャンク)毎にランダムに発行する主キー
  - SEQ_NO    : チャンクの順序を示す連番(1始まり)
  - FILE_SIZE : 分割前のファイル全体のサイズ(全チャンクで同じ値)

common_libs.common.dbconnect.DBConnectCommonのtable_insert()は、
呼び出す度に履歴(_JNL)テーブルへのINSERTを前提としており、
T_AI_ATTACHMENT_FILE(その前提を持たないテーブル)には適合しないため、
ここではsql_execute()で直接INSERT文を発行する。

このモジュールはさらに、MCPの"tools/call"から呼び出す
"create-attachment-text-file" ・ "get-attachment-text-file" ツール
(@toolデコレーター付き関数)も提供する。
  - create-attachment-text-file : filename・text(生テキスト)・
    mime_type(任意)を受け取り、アップロードAPIと同じ登録処理
    (create_attachment_file)でT_AI_ATTACHMENT_FILEに登録し、
    file_id等を返す。
  - get-attachment-text-file    : file_id・encoding(任意)を受け取り、
    file_id・user_idを条件にT_AI_ATTACHMENT_FILEを検索し、SEQ_NO順に
    FILE_DATAを連結してテキストとして返す。

なお、このファイル内ではBlueprintルート・@toolデコレーター付き関数を上部に、
続けて他ファイルからも利用できる公開関数(create_attachment_file ・
fetch_attachment_file)、最後にこのファイル内でのみ使う
"_"始まりのヘルパー関数を下部にまとめて配置している。

--------------------------------------------------------------------------
Attachment file upload API (registers rows into T_AI_ATTACHMENT_FILE)

Provides an interface at
"/api/<organization_id>/workspaces/<workspace_id>/mcp/attachment_file" that
accepts a multipart/form-data "file" and returns file metadata, storing the
file content itself in the workspace DB's T_AI_ATTACHMENT_FILE table.

Because T_AI_ATTACHMENT_FILE.FILE_DATA is a MEDIUMBLOB (16MiB max), a single
row cannot hold an arbitrarily large file. When the file size exceeds
CHUNK_SIZE (2MiB), it is therefore split into CHUNK_SIZE pieces and inserted
as multiple rows, related as follows:
  - FILE_ID   : shared across every chunk of the same uploaded file
  - UUID      : primary key, a fresh random value generated per row (chunk)
  - SEQ_NO    : 1-based sequence number indicating chunk order
  - FILE_SIZE : the total size of the file before splitting (same on every chunk row)

common_libs.common.dbconnect.DBConnectCommon's table_insert() always assumes
a history (_JNL) table exists, which does not apply to T_AI_ATTACHMENT_FILE.
So this module issues the INSERT statement directly via sql_execute() instead.

This module also provides the "create-attachment-text-file" and
"get-attachment-text-file" tools (@tool-decorated functions invoked via
MCP's "tools/call").
  - create-attachment-text-file : accepts filename/text (raw text)/
    mime_type (optional), registers it into T_AI_ATTACHMENT_FILE using the
    same registration logic (create_attachment_file) as the upload API
    above, and returns file_id etc.
  - get-attachment-text-file    : accepts file_id/encoding (optional), looks
    up T_AI_ATTACHMENT_FILE by file_id/user_id, concatenates FILE_DATA in
    SEQ_NO order, and returns it as text.

Within this file, the Blueprint route and @tool-decorated functions are
placed at the top, followed by the functions also usable from other modules
(create_attachment_file / fetch_attachment_file), and finally the
"_"-prefixed helper functions used only within this file are grouped at the
bottom.
"""
import datetime
import io
import os

import pytz
from flask import Blueprint, request, jsonify, g, send_file

from common_libs.common.dbconnect import DBConnectWs
from libs import tool

attachment_file_bp = Blueprint("attachment_file", __name__)

# 1チャンクあたりの最大サイズ(2MiB)。これを超えるファイルはこの単位で分割する。
# Maximum size per chunk (2MiB). Files larger than this are split into pieces of this size.
CHUNK_SIZE = 2 * 1024 * 1024

_TABLE_NAME = "T_AI_ATTACHMENT_FILE"
_PRIMARY_KEY_NAME = "UUID"


@attachment_file_bp.post('/api/<organization_id>/workspaces/<workspace_id>/mcp/attachment_file')
def upload_attachment_file(organization_id, workspace_id):
    """
    添付ファイルをアップロードし、T_AI_ATTACHMENT_FILEに登録する

    Upload an attachment file and register it into T_AI_ATTACHMENT_FILE.

    Args:
        organization_id (str): organization id
        workspace_id (str): workspace id

    Returns:
        Response: アップロード結果(file_id/filename/mime_type/size)を含むJSON
            / JSON response containing the upload result (file_id/filename/mime_type/size)
    """
    if "file" not in request.files:
        return jsonify({
            "error": "FileRequired",
            "message": "multipart/form-data の file が必要です。"
        }), 400

    file = request.files["file"]
    file_name = file.filename
    mime_type = file.mimetype
    content = file.read()

    # User-Idは認証プロキシが付与し、before_request_handlerがgに保存済み
    # User-Id is injected by the authentication proxy and already stored on
    # g by before_request_handler
    user_id = g.get("USER_ID")

    meta = create_attachment_file(organization_id, workspace_id, user_id, file_name, mime_type, content)

    g.applogger.info("Attachment file uploaded: file_id={}, size={}".format(meta["file_id"], meta["size"]))

    return jsonify(meta), 201


@attachment_file_bp.get('/api/<organization_id>/workspaces/<workspace_id>/mcp/attachment_file/<file_id>')
def get_attachment_file_meta(organization_id, workspace_id, file_id):
    """
    添付ファイルのメタ情報を取得する(ファイル本体は取得しない)

    Get an attachment file's metadata (does not fetch the file content itself).

    Args:
        organization_id (str): organization id
        workspace_id (str): workspace id
        file_id (str): 取得対象のファイルID / file id to fetch

    Returns:
        Response: メタ情報(file_id/filename/mime_type/size)を含むJSON。
            対象が無い場合は404 / JSON response containing the metadata
            (file_id/filename/mime_type/size); 404 if not found
    """
    user_id = g.get("USER_ID")
    meta = _fetch_attachment_meta(organization_id, workspace_id, user_id, file_id)

    if meta is None:
        return jsonify({
            "error": "FileNotFound",
            "message": "file_id が存在しません。"
        }), 404

    return jsonify({
        "file_id": file_id,
        "filename": meta["filename"],
        "mime_type": meta["mime_type"],
        "size": meta["size"],
    })


@attachment_file_bp.get('/api/<organization_id>/workspaces/<workspace_id>/mcp/attachment_file/<file_id>/download')
def download_attachment_file(organization_id, workspace_id, file_id):
    """
    添付ファイルの本体をダウンロードする

    Download an attachment file's content.

    Args:
        organization_id (str): organization id
        workspace_id (str): workspace id
        file_id (str): 取得対象のファイルID / file id to fetch

    Returns:
        Response: ファイル本体(Content-Type: mime_type、
            Content-Disposition: attachment付き)。
            対象が無い場合は404 / the file content (with Content-Type set to
            mime_type and Content-Disposition: attachment); 404 if not found
    """
    user_id = g.get("USER_ID")
    file_data = fetch_attachment_file(organization_id, workspace_id, user_id, file_id)

    if file_data is None:
        return jsonify({
            "error": "FileNotFound",
            "message": "file_id が存在しません。"
        }), 404

    return send_file(
        io.BytesIO(file_data["content"]),
        mimetype=file_data["mime_type"],
        as_attachment=True,
        download_name=file_data["filename"],
    )


@tool(
    name="create-attachment-text-file",
    description=(
        "Create a text file (e.g. HTML/CSS/JS/plain text) from raw text content and register it "
        "as an attachment file, returning a file_id. Use this instead of Base64-encoding when you "
        "need to store text content you generated yourself: passing the raw text here avoids "
        "re-emitting it as a huge Base64 string, which is slow and wastes tokens."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "File name to save (e.g. 'weather.html')"
            },
            "text": {
                "type": "string",
                "description": "Raw text content of the file (not Base64-encoded)"
            },
            "mime_type": {
                "type": "string",
                "description": "MIME type of the file (e.g. 'text/html'). Optional."
            }
        },
        "required": ["filename", "text"]
    }
)
def tool_create_attachment_text_file(arguments: dict, payload: dict) -> dict:
    """
    テキスト内容から添付ファイルを作成し、T_AI_ATTACHMENT_FILEに登録する

    Create an attachment file from raw text content and register it into
    T_AI_ATTACHMENT_FILE.

    Parameters:
        arguments (dict): ツールの引数
            - filename (str): 保存するファイル名 / file name to save
            - text (str): ファイルの実体(生テキスト) / raw text content of the file
            - mime_type (str, optional): MIMEタイプ(デフォルト: 'text/plain')
                / mime type (default: 'text/plain')
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
            - user_id (str): 呼び出しユーザーのID / calling user's id

    Returns:
        dict: 作成結果
            - file_id (str): 発行されたファイルID / issued file id
            - filename (str): ファイル名 / file name
            - mime_type (str): MIMEタイプ / mime type
            - size (int): ファイルサイズ(バイト) / file size (bytes)
            - message (str): 処理結果メッセージ / result message

    Raises:
        Exception: filenameが指定されていない場合 / if filename is not specified
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")
    user_id = payload.get("user_id")
    filename = arguments.get("filename", "")
    text = arguments.get("text", "")
    mime_type = arguments.get("mime_type") or "text/plain"

    if not filename:
        raise Exception("filename is required")

    meta = create_attachment_file(organization_id, workspace_id, user_id, filename, mime_type, text.encode("utf-8"))

    g.applogger.info("Attachment text file created: file_id={}, size={}".format(meta["file_id"], meta["size"]))

    return {
        "file_id": meta["file_id"],
        "filename": meta["filename"],
        "mime_type": meta["mime_type"],
        "size": meta["size"],
        "message": "Attachment text file created successfully."
    }


@tool(
    name="get-attachment-text-file",
    description=(
        "Retrieve the raw text content of a previously uploaded attachment file by its file_id. "
        "Use this instead of downloading and Base64-decoding when you need to read back text "
        "(e.g. HTML/CSS/JS/plain text) content that was uploaded through the attachment file "
        "upload API."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "file_id": {
                "type": "string",
                "description": "file_id of the attachment file to retrieve."
            },
            "encoding": {
                "type": "string",
                "description": "Text encoding to decode the file content with. Optional; defaults to 'utf-8'."
            }
        },
        "required": ["file_id"]
    }
)
def tool_get_attachment_text_file(arguments: dict, payload: dict) -> dict:
    """
    file_id・user_idを条件に添付ファイルのテキスト内容を取得する

    Retrieve the text content of an attachment file by file_id/user_id.

    Parameters:
        arguments (dict): ツールの引数
            - file_id (str): 取得するファイルのID / id of the file to retrieve
            - encoding (str, optional): デコードに使う文字エンコーディング
                (デフォルト: 'utf-8') / text encoding to decode with (default: 'utf-8')
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
            - user_id (str): 呼び出しユーザーのID / calling user's id

    Returns:
        dict: 取得結果
            - file_id (str): ファイルID / file id
            - filename (str): ファイル名 / file name
            - mime_type (str): MIMEタイプ / mime type
            - text (str): ファイルの内容(生テキスト) / file content (raw text)
            - message (str): 処理結果メッセージ / result message

    Raises:
        Exception: file_idが指定されていない、対象ファイルが存在しない、
            またはテキストとしてデコードできない場合 / if file_id is missing,
            the file cannot be found, or the content cannot be decoded as text
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")
    user_id = payload.get("user_id")
    file_id = arguments.get("file_id", "")
    encoding = arguments.get("encoding") or "utf-8"

    if not file_id:
        raise Exception("file_id is required")

    file_data = fetch_attachment_file(organization_id, workspace_id, user_id, file_id)
    if file_data is None:
        g.applogger.info("get-attachment-text-file: file not found (file_id={})".format(file_id))
        raise Exception("File not found: {}".format(file_id))

    try:
        text = file_data["content"].decode(encoding)
    except (LookupError, UnicodeDecodeError) as e:
        g.applogger.info("get-attachment-text-file failed to decode file content (file_id={}): {}".format(file_id, e))
        raise Exception("Failed to decode file content as '{}': {}".format(encoding, str(e)))

    return {
        "file_id": file_id,
        "filename": file_data["filename"],
        "mime_type": file_data["mime_type"],
        "text": text,
        "message": "Attachment text file content fetched successfully."
    }


def create_attachment_file(organization_id, workspace_id, user_id, file_name, mime_type, content):
    """
    ファイル本体をT_AI_ATTACHMENT_FILEに登録する
    (アップロードAPI・create-attachment-text-fileツール共通の登録処理)

    Register file content into T_AI_ATTACHMENT_FILE (shared by both the
    upload API and the create-attachment-text-file tool).

    Args:
        organization_id (str): organization id
        workspace_id (str): workspace id
        user_id (str): 登録するユーザーのID / id of the registering user
        file_name (str): ファイル名 / file name
        mime_type (str): MIMEタイプ / mime type
        content (bytes): ファイル本体 / file content

    Returns:
        dict: {"file_id": str, "filename": str, "mime_type": str, "size": int}
    """
    # file_idは"fileid_"を先頭に付けたUUIDとする(生のUUIDのままでは、他の種類の
    # ID文字列と見分けがつかないため、種別を判別できるようにプレフィックスを付与する)
    # Prefix file_id with "fileid_" (a bare UUID alone would be indistinguishable
    # from other kinds of id strings, so a prefix is added to make the id's kind
    # identifiable at a glance)
    file_id = "fileid_" + DBConnectWs.genarate_primary_key_value()

    ws_db = DBConnectWs(workspace_id=workspace_id, organization_id=organization_id)
    try:
        _insert_attachment_chunks(ws_db, user_id, file_id, file_name, mime_type, content)
    finally:
        ws_db.db_disconnect()

    return {
        "file_id": file_id,
        "filename": file_name,
        "mime_type": mime_type,
        "size": len(content),
    }


def fetch_attachment_file(organization_id, workspace_id, user_id, file_id):
    """
    file_id・user_idを条件にT_AI_ATTACHMENT_FILEからチャンクを取得し、
    SEQ_NO順に連結して1つのファイル本体に復元する

    Fetch the chunk rows from T_AI_ATTACHMENT_FILE by file_id/user_id and
    reassemble them (ordered by SEQ_NO) into a single file content.

    Args:
        organization_id (str): organization id
        workspace_id (str): workspace id
        user_id (str): このファイルをアップロードしたユーザーのID
            / id of the user who uploaded the file
        file_id (str): 取得対象のファイルID / file id to fetch

    Returns:
        dict | None: {"filename": str, "mime_type": str, "content": bytes}
            対象が見つからない場合はNone
            / None if no matching rows are found
    """
    ws_db = DBConnectWs(workspace_id=workspace_id, organization_id=organization_id)
    try:
        rows = ws_db.table_select(
            _TABLE_NAME,
            "WHERE `FILE_ID` = %s AND `LAST_UPDATE_USER` = %s ORDER BY `SEQ_NO` ASC",
            [file_id, user_id]
        )
    finally:
        ws_db.db_disconnect()

    # SEQ_NO=1(先頭チャンク)が無い場合はデータなしとして扱う
    # Treat as "no data" if the first chunk (SEQ_NO=1) is missing
    if not rows or rows[0]["SEQ_NO"] != 1:
        return None

    content = b"".join(row["FILE_DATA"] for row in rows)

    return {
        "filename": rows[0]["FILE_NAME"],
        "mime_type": rows[0]["MIME_TYPE"],
        "content": content,
    }


def _insert_attachment_chunks(ws_db, user_id, file_id, file_name, mime_type, content):
    """
    ファイル本体をCHUNK_SIZE毎に分割し、T_AI_ATTACHMENT_FILEに登録する

    Split the file content into CHUNK_SIZE pieces and insert them into
    T_AI_ATTACHMENT_FILE.

    Args:
        ws_db (DBConnectWs): ワークスペースDBへの接続 / workspace DB connection
        user_id (str): アップロードしたユーザーのID / id of the uploading user
        file_id (str): このファイルに共通のID / id shared by every chunk of this file
        file_name (str): ファイル名 / file name
        mime_type (str): MIMEタイプ / mime type
        content (bytes): ファイル本体 / file content

    Returns:
        int: 登録したチャンク数(レコード数) / number of chunk rows inserted
    """
    file_size = len(content)
    now = _get_last_update_timestamp_now()

    # 空ファイル(0byte)でも1レコードは登録する
    # Insert exactly one row even for an empty (0-byte) file
    offsets = range(0, file_size, CHUNK_SIZE) if file_size > 0 else [0]

    sql = (
        "INSERT INTO `{}` "
        "(`UUID`, `FILE_ID`, `SEQ_NO`, `FILE_NAME`, `MIME_TYPE`, `FILE_SIZE`, `FILE_DATA`, `LAST_UPDATE_TIMESTAMP`, `LAST_UPDATE_USER`) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    ).format(_TABLE_NAME)

    ws_db.db_transaction_start()
    try:
        chunk_count = 0
        for seq_no, offset in enumerate(offsets, start=1):
            chunk = content[offset:offset + CHUNK_SIZE]
            ws_db.sql_execute(sql, [
                DBConnectWs.genarate_primary_key_value(),
                file_id,
                seq_no,
                file_name,
                mime_type,
                file_size,
                chunk,
                now,
                user_id,
            ])
            chunk_count = seq_no
    except Exception:
        ws_db.db_transaction_end(False)
        raise
    else:
        ws_db.db_transaction_end(True)

    return chunk_count


def _fetch_attachment_meta(organization_id, workspace_id, user_id, file_id):
    """
    file_id・user_idを条件にT_AI_ATTACHMENT_FILEからメタ情報のみを取得する

    FILE_NAME・MIME_TYPE・FILE_SIZEはどのチャンク行にも同じ値が入っているため、
    FILE_DATA(本体)を取得せずSEQ_NOが最小の1行だけ見れば十分。
    fetch_attachment_file と異なり、大きなBLOBを読み込まない軽量版。

    Fetch only the metadata of an attachment file by file_id/user_id.

    FILE_NAME/MIME_TYPE/FILE_SIZE are duplicated on every chunk row, so it is
    enough to look at the single row with the smallest SEQ_NO, without
    fetching FILE_DATA (the content). Unlike fetch_attachment_file, this is
    a lightweight version that never reads the large BLOB.

    Args:
        organization_id (str): organization id
        workspace_id (str): workspace id
        user_id (str): このファイルをアップロードしたユーザーのID
            / id of the user who uploaded the file
        file_id (str): 取得対象のファイルID / file id to fetch

    Returns:
        dict | None: {"filename": str, "mime_type": str, "size": int}
            対象が見つからない場合はNone
            / None if no matching rows are found
    """
    # SEQ_NO=1(先頭チャンク)が無い場合はデータなしとして扱うため、SEQ_NO=1を直接条件にする
    # Condition directly on SEQ_NO=1 so a missing first chunk is treated as "no data"
    sql = (
        "SELECT `FILE_NAME`, `MIME_TYPE`, `FILE_SIZE` FROM `{}` "
        "WHERE `FILE_ID` = %s AND `LAST_UPDATE_USER` = %s AND `SEQ_NO` = 1"
    ).format(_TABLE_NAME)

    ws_db = DBConnectWs(workspace_id=workspace_id, organization_id=organization_id)
    try:
        rows = ws_db.sql_execute(sql, [file_id, user_id])
    finally:
        ws_db.db_disconnect()

    if not rows:
        return None

    row = rows[0]
    return {
        "filename": row["FILE_NAME"],
        "mime_type": row["MIME_TYPE"],
        "size": row["FILE_SIZE"],
    }


def _get_last_update_timestamp_now():
    """
    LAST_UPDATE_TIMESTAMP用に、TZ環境変数で指定されたタイムゾーンの現在時刻を取得する

    common_libs.common.util.get_timestamp()はtzinfoを考慮せずdatetime.now()を
    そのまま返すため、OS側がTZ環境変数の変更を確実に反映しているとは限らない。
    そのため、common_libs.common.util.datetime_to_str() / storage_access.pyと
    同様にpytzでTZ環境変数のタイムゾーンを明示的に解釈する。
    DATETIME型カラムはtzinfoを保持しないため、最後にtzinfoを外したnaiveな
    datetimeとして返す。

    Get the current time in the timezone specified by the TZ environment
    variable, for use as LAST_UPDATE_TIMESTAMP.

    common_libs.common.util.get_timestamp() simply returns datetime.now()
    without considering tzinfo, so it is not guaranteed to reflect a change
    to the TZ environment variable at the OS level. So, just like
    common_libs.common.util.datetime_to_str() / storage_access.py, this
    explicitly interprets the TZ environment variable's timezone via pytz.
    Because a DATETIME column does not retain tzinfo, the tzinfo is stripped
    before returning, yielding a naive datetime.

    Returns:
        datetime.datetime: TZ環境変数のタイムゾーンでの現在時刻(naive)
            / the current time in the TZ environment variable's timezone (naive)
    """
    tz = pytz.timezone(os.environ.get('TZ', 'UTC'))
    return datetime.datetime.now(tz).replace(tzinfo=None)
