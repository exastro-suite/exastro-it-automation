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
ITAメニューフィルターツール ("menu-filter" / "menu-filter-count")

指定したメニューに対し、検索条件を指定してレコード(またはその件数)を
取得する。ユーザー自身がアクセスできるメニューの情報を返すだけの処理であり、
実行に特別な権限は不要なため、@tool デコレーターの required_roles /
required_menu は指定していない(誰でも実行可能)。
  - menu-filter       : menu(メニュー名)・filter_conditions(検索条件、任意)・
    file(ファイル取得指定、任意)を受け取り、該当レコードを返す。
    file="yes"かつレコード件数がMENU_FILTER_FILE_RECORD_LIMIT以下の場合、
    各レコードのfile列(Base64本体)をT_AI_ATTACHMENT_FILEへ登録した上で
    file_idに置き換えたfileidを返す(maintenance-allツールへそのまま
    渡せる形式)。件数が上限を超える場合はファイル情報を省略する。
  - menu-filter-count : menu(メニュー名)・filter_conditions(検索条件、任意)
    を受け取り、該当レコードの件数を返す。

ita_api_mcp_serverでは前段の認証プロキシが "User-Id" / "Roles" ヘッダーを
付与する方式(ita_api_organization / ita_api_admin と同じ方式)を採用している
ため、ダウンストリームAPI呼び出し時には、リクエストで受け取った
"User-Id" / "Roles" ヘッダーをそのまま転送する。
呼び出し先のAPIパスは "/api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/filter/"
および "/api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/filter/count/" を使用する。

--------------------------------------------------------------------------
ITA menu filter tools ("menu-filter" / "menu-filter-count")

Fetches records (or their count) from a given menu by specifying search
conditions. This only returns information about menus the user can already
access, so no special permission is required to run it; the @tool
decorator's required_roles / required_menu are left unset (callable by
anyone).
  - menu-filter       : accepts menu (menu name), filter_conditions (search
    conditions, optional) and file (file acquisition mode, optional), and
    returns the matching records. When file="yes" and the record count is
    within MENU_FILTER_FILE_RECORD_LIMIT, each record's file column
    (raw Base64 content) is registered into T_AI_ATTACHMENT_FILE and
    replaced by a fileid entry (file_id), in the shape maintenance-all's
    input fileid expects. File information is omitted when the record
    count exceeds the limit.
  - menu-filter-count : accepts menu (menu name) and filter_conditions
    (search conditions, optional), and returns the matching record count.

ita_api_mcp_server relies on the authentication proxy in front of it, which
injects "User-Id" / "Roles" headers (the same scheme used by
ita_api_organization / ita_api_admin). Therefore, when calling the
downstream API, we forward the "User-Id" / "Roles" headers received on the
incoming request as-is.
The downstream API paths used are
"/api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/filter/"
and
"/api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/filter/count/".
"""
import base64
import os

import requests
from flask import g

from libs import tool, HTTPException, build_forward_headers
from .attachment_file import create_attachment_file

# menu-filterでfile="yes"を指定した際、file列をfile_idに変換する処理を行う
# レコード件数の上限。この件数を超える場合はファイル情報を省略する
# (レコード数に比例してファイル変換のオーバーヘッドが増えるための安全弁)。
# 環境変数MENU_FILTER_FILE_RECORD_LIMITで上書き可能。
#
# Maximum record count for converting the file column into file_id entries
# when menu-filter is called with file="yes". File information is omitted
# once the record count exceeds this limit (a safety valve, since the
# file-conversion overhead grows with the record count).
# Overridable via the MENU_FILTER_FILE_RECORD_LIMIT environment variable.
MENU_FILTER_FILE_RECORD_LIMIT = int(os.getenv("MENU_FILTER_FILE_RECORD_LIMIT", "5"))

# ファイルの実MIMEタイプが不明な場合(menu-filterのfile列から復元する場合)に使う既定値
# Default MIME type used when the actual MIME type is unknown (when
# restoring a file from menu-filter's file column)
_DEFAULT_FILE_MIME_TYPE = "application/octet-stream"


@tool(
    name="menu-filter",
    description=(
        "Get records from an ITA menu by specifying search conditions. Discarded records "
        "(discard=1) are excluded by default unless a 'discard' condition is explicitly given."
        "When specifying filter_conditions, refer to `tool-reference/menu-filter.md` using the `get-document` tool."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "menu": {
                "type": "string",
                "description": "Menu name (REST name)"
            },
            "filter_conditions": {
                "type": "object",
                "description": (
                    "Search conditions to filter records. "
                    "ex: partial match - {\"column_name_rest\": {\"NORMAL\": \"exact_value\"}} / "
                    "multiple values (exact match) - {\"column_name_rest\": {\"LIST\": [\"value1\", \"value2\"]}}"
                )
            },
            "file": {
                "type": "string",
                "description": (
                    "File acquisition specification (e.g. 'no' for no file acquisition). "
                    "When 'yes' and the record count is within the configured limit, each record's 'file' field "
                    "is replaced by a 'fileid' field (column_name_rest -> file_id, same shape as maintenance-all's "
                    "input 'fileid') instead of raw Base64 content; otherwise file information is omitted."
                ),
                "enum": ["yes", "no"]
            }
        },
        "required": ["menu"]
    }
)
def tool_menu_filter(arguments: dict, payload: dict) -> dict:
    """
    検索条件を指定してメニューのレコードを取得する

    Get records from an ITA menu by specifying search conditions.

    Parameters:
        arguments (dict): ツールの引数
            - menu (str): メニュー名(REST名) / menu name (REST name)
            - filter_conditions (dict, optional): レコードを絞り込むための
                検索条件 / search conditions to filter records
            - file (str, optional): ファイル取得指定("yes"/"no"、
                デフォルト: "no") / file acquisition mode ("yes"/"no",
                default: "no")
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
            - user_id (str): 呼び出しユーザーのID / calling user's id

    Returns:
        dict: レコード取得結果
            - result: APIレスポンスの取得されたレコード / the records returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
            - menu (str): メニュー名 / menu name

    Raises:
        Exception: menuが指定されていない、またはファイル内容の登録に
            失敗した場合 / if menu is not specified, or storing a file's
            content fails
        HTTPException: レコードの取得に失敗した場合 / if fetching the records fails
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")
    user_id = payload.get("user_id")
    menu = arguments.get("menu", "")
    filter_conditions = arguments.get("filter_conditions") or {}
    file_param = arguments.get("file")

    if not menu:
        raise Exception("menu is required")

    # discard条件が未指定の場合は、論理削除(discard=1)されたレコードを
    # 除外するデフォルト条件を追加する
    # If a 'discard' condition is not given, add a default condition that
    # excludes logically-deleted (discard=1) records
    if "discard" not in filter_conditions:
        filter_conditions["discard"] = {"NORMAL": "0"}

    # このツールが呼び出すのは "/ita/menu/{menu}/filter/" というITA自身のAPI
    # (ita_api_organization)側のエンドポイントであるため、環境変数
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT を使用する
    #
    # This tool calls the "/ita/menu/{menu}/filter/" endpoint of ITA's own
    # API (ita_api_organization), so it uses the ITA_API_ORAGANIZATION_HOST /
    # ITA_API_ORAGANIZATION_PORT environment variables
    ita_api_host = os.getenv("ITA_API_ORAGANIZATION_HOST")
    ita_api_port = os.getenv("ITA_API_ORAGANIZATION_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/{}/filter/".format(
        ita_api_host, ita_api_port, organization_id, workspace_id, menu
    )

    # 転送用ヘッダーを組み立てる(POSTでボディを送るため"Content-Type"も付与する)
    # Build the headers to forward (also adds "Content-Type" since this is a POST with a body)
    headers = build_forward_headers(method="POST")

    # file="yes"以外の場合は、ダウンストリームAPIにfile=noを明示してファイル本体の
    # 取得自体を抑制する(file="yes"の場合はfile_paramの変換をこの関数側で行うため、
    # ダウンストリームAPIには生のBase64本体を含めて返してもらう)
    #
    # Unless file="yes", explicitly pass file=no to the downstream API so it
    # suppresses fetching the file content itself. When file="yes", the raw
    # Base64 content is requested from the downstream API so it can be
    # converted into fileid entries by this function
    params = {}
    if file_param != "yes":
        params["file"] = "no"

    # ITAのAPIへレコード取得のPOSTリクエストを送信する
    # Send a POST request to ITA's API to fetch the records
    req = requests.post(url, json=filter_conditions, headers=headers, params=params)

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        g.applogger.info("Failed to get menu records: {} - {}".format(req.status_code, req.text))
        raise HTTPException("menu-filter", req)

    result = req.json()
    message = "Menu records fetched successfully."

    records = result.get("data", [])
    if file_param == "yes":
        if len(records) > MENU_FILTER_FILE_RECORD_LIMIT:
            # 件数が上限を超える場合はファイル情報を省略する
            # If the record count exceeds the limit, omit file information
            for record in records:
                record["file"] = {}
            message = (
                "Menu records fetched successfully. File information was omitted because "
                "the record count ({}) exceeded the limit ({}).".format(len(records), MENU_FILTER_FILE_RECORD_LIMIT)
            )
        else:
            # 各レコードのfile列(Base64本体)をT_AI_ATTACHMENT_FILEへ登録し、
            # file_idに置き換えたfileidを組み立てる
            # Register each record's file column (raw Base64 content) into
            # T_AI_ATTACHMENT_FILE, and build a fileid entry with the file_id
            for record in records:
                file_data = record.pop("file", None) or {}
                fileid_data = {}
                for col_name, b64_content in file_data.items():
                    if not b64_content:
                        continue
                    filename = (record.get("parameter") or {}).get(col_name) or col_name
                    try:
                        meta = create_attachment_file(
                            organization_id, workspace_id, user_id, filename,
                            _DEFAULT_FILE_MIME_TYPE, base64.b64decode(b64_content)
                        )
                    except Exception as e:
                        g.applogger.info(
                            "menu-filter failed to store file content: column={}, error={}".format(col_name, e)
                        )
                        raise Exception("Failed to store file content for column '{}': {}".format(col_name, str(e)))
                    fileid_data[col_name] = meta["file_id"]
                record["fileid"] = fileid_data

    return {
        "result": result,
        "message": message,
        "organization_id": organization_id,
        "workspace_id": workspace_id,
        "menu": menu
    }


@tool(
    name="menu-filter-count",
    description="Get the count of records from an ITA menu by specifying search conditions",
    input_schema={
        "type": "object",
        "properties": {
            "menu": {
                "type": "string",
                "description": "Menu name (REST name)"
            },
            "filter_conditions": {
                "type": "object",
                "description": "Search conditions to filter records"
            }
        },
        "required": ["menu"]
    }
)
def tool_menu_filter_count(arguments: dict, payload: dict) -> dict:
    """
    検索条件を指定してメニューのレコード件数を取得する

    Get the count of records from an ITA menu by specifying search conditions.

    Parameters:
        arguments (dict): ツールの引数
            - menu (str): メニュー名(REST名) / menu name (REST name)
            - filter_conditions (dict, optional): レコードを絞り込むための
                検索条件 / search conditions to filter records
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Returns:
        dict: レコード件数取得結果
            - result: APIレスポンスのレコード件数 / the record count returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
            - menu (str): メニュー名 / menu name

    Raises:
        Exception: menuが指定されていない場合 / if menu is not specified
        HTTPException: レコード件数の取得に失敗した場合 / if fetching the record count fails
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")
    menu = arguments.get("menu", "")
    filter_conditions = arguments.get("filter_conditions") or {}

    if not menu:
        raise Exception("menu is required")

    # menu-filterと同じITA自身のAPI(ita_api_organization)を呼び出すため、
    # 同じ環境変数 ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT を使用する
    #
    # Calls the same ITA's own API (ita_api_organization) as menu-filter, so
    # the same ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT
    # environment variables are used
    ita_api_host = os.getenv("ITA_API_ORAGANIZATION_HOST")
    ita_api_port = os.getenv("ITA_API_ORAGANIZATION_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/{}/filter/count/".format(
        ita_api_host, ita_api_port, organization_id, workspace_id, menu
    )

    # 転送用ヘッダーを組み立てる(POSTでボディを送るため"Content-Type"も付与する)
    # Build the headers to forward (also adds "Content-Type" since this is a POST with a body)
    headers = build_forward_headers(method="POST")

    # ITAのAPIへレコード件数取得のPOSTリクエストを送信する
    # Send a POST request to ITA's API to fetch the record count
    req = requests.post(url, json=filter_conditions, headers=headers)

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        g.applogger.info("Failed to get menu record count: {} - {}".format(req.status_code, req.text))
        raise HTTPException("menu-filter-count", req)

    # 正常時はAPIのレスポンスをそのまま結果として返す
    # On success, return the API response as the result
    return {
        "result": req.json(),
        "message": "Menu record count fetched successfully.",
        "organization_id": organization_id,
        "workspace_id": workspace_id,
        "menu": menu
    }
