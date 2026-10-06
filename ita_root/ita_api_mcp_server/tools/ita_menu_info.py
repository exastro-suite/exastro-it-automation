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
ITAメニュー情報取得ツール ("list-menu-info" / "list-menu-info-pulldown")

指定したメニューの基本情報・項目情報、およびIDColumn項目の指定可能な値
(プルダウン)一覧を、ITAのAPIを呼び出して取得するツール。ユーザー自身が
アクセスできるメニューの情報を返すだけの処理であり、実行に特別な権限は
不要なため、@tool デコレーターの required_roles / required_menu は
指定していない(誰でも実行可能)。
  - list-menu-info          : menu(メニュー名)を受け取り、そのメニューの
    基本情報・項目情報を返す。
  - list-menu-info-pulldown : menu(メニュー名)を受け取り、そのメニューの
    IDColumn項目について指定可能な値(id: nameの辞書)一覧を返す。

ita_api_mcp_serverでは前段の認証プロキシが "User-Id" / "Roles" ヘッダーを
付与する方式(ita_api_organization / ita_api_admin と同じ方式)を採用している
ため、ダウンストリームAPI呼び出し時には、リクエストで受け取った
"User-Id" / "Roles" ヘッダーをそのまま転送する。
呼び出し先のAPIパスは "/api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/info/"
および "/api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/info/pulldown/" を使用する。

--------------------------------------------------------------------------
ITA menu information tools ("list-menu-info" / "list-menu-info-pulldown")

Fetches a given menu's basic information/column information, and the list
of allowable values (pulldown) for its IDColumn fields, by calling ITA's
API. This only returns information about menus the user can already
access, so no special permission is required to run it; the @tool
decorator's required_roles / required_menu are left unset (callable by
anyone).
  - list-menu-info          : accepts menu (menu name) and returns that
    menu's basic information/column information.
  - list-menu-info-pulldown : accepts menu (menu name) and returns the list
    of allowable values (an id: name dict) for that menu's IDColumn fields.

ita_api_mcp_server relies on the authentication proxy in front of it, which
injects "User-Id" / "Roles" headers (the same scheme used by
ita_api_organization / ita_api_admin). Therefore, when calling the
downstream API, we forward the "User-Id" / "Roles" headers received on the
incoming request as-is.
The downstream API paths used are
"/api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/info/"
and
"/api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/info/pulldown/".
"""
import os
from urllib.parse import quote

import requests
from flask import g

from libs import tool, HTTPException, build_forward_headers, get_downstream_timeout


@tool(
    name="list-menu-info",
    description="Get basic information and column information for a specific ITA menu",
    input_schema={
        "type": "object",
        "properties": {
            "menu": {
                "type": "string",
                "description": "Menu name to retrieve information for"
            }
        },
        "required": ["menu"]
    },
    profile=["AgenticAI", "LLMEditor"]
)
def tool_list_menu_info(arguments: dict, payload: dict) -> dict:
    """
    メニューの基本情報・項目情報を取得する

    Get basic information and column information for a specific menu.

    Parameters:
        arguments (dict): ツールの引数
            - menu (str): メニュー名 / menu name to retrieve information for
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Returns:
        dict: メニュー情報取得結果
            - result: APIレスポンスのメニュー情報 / the menu info returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
            - menu (str): メニュー名 / menu name

    Raises:
        Exception: menuが指定されていない場合 / if menu is not specified
        HTTPException: メニュー情報の取得に失敗した場合 / if fetching the menu info fails
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")
    menu = arguments.get("menu", "")

    if not menu:
        raise Exception("menu is required")

    g.applogger.info(f'Parameter menu={menu}')

    # このツールが呼び出すのは "/ita/menu/{menu}/info/" というITA自身のAPI
    # (ita_api_organization)側のエンドポイントであるため、環境変数
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT を使用する
    #
    # This tool calls the "/ita/menu/{menu}/info/" endpoint of ITA's own API
    # (ita_api_organization), so it uses the ITA_API_ORAGANIZATION_HOST /
    # ITA_API_ORAGANIZATION_PORT environment variables
    ita_api_host = os.getenv("ITA_API_ORAGANIZATION_HOST")
    ita_api_port = os.getenv("ITA_API_ORAGANIZATION_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/{}/info/".format(
        ita_api_host, ita_api_port, organization_id, workspace_id, quote(str(menu), safe="")
    )

    # 転送用ヘッダーを組み立てる
    # Build the headers to forward
    headers = build_forward_headers(method="GET")

    # ITAのAPIへメニュー情報取得のGETリクエストを送信する
    # Send a GET request to ITA's API to fetch the menu info
    req = requests.get(url, headers=headers, timeout=get_downstream_timeout())

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        g.applogger.info("Failed to fetch menu info: {} - {}".format(req.status_code, req.text))
        raise HTTPException("list-menu-info", req)

    # 正常時はAPIのレスポンスをそのまま結果として返す
    # On success, return the API response as the result
    return {
        "result": req.json(),
        "message": "Menu info fetched successfully.",
        "organization_id": organization_id,
        "workspace_id": workspace_id,
        "menu": menu
    }


@tool(
    name="list-menu-info-pulldown",
    description=(
        "Get the list of allowable values for the IDColumn fields of a specific ITA menu; returns "
        "each column_name_rest as a dict mapping id to name. When using the returned values with "
        "the maintenance-all tool, specify the name side."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "menu": {
                "type": "string",
                "description": "Menu name to retrieve the pulldown list for"
            }
        },
        "required": ["menu"]
    },
    profile=["AgenticAI", "LLMEditor"]
)
def tool_list_menu_info_pulldown(arguments: dict, payload: dict) -> dict:
    """
    IDColumn項目の指定可能な値の一覧を取得する(nameを指定する)

    - returns形式
        - .column_name_rest(dict): 指定可能な値の辞書形式(id: name)
          `maintenance-all`ツールには、name側を指定します

    Get the list of allowable values for the IDColumn fields of a menu
    (specified by name).

    - return format
        - .column_name_rest (dict): allowable values as an id: name dict;
          when using this with the `maintenance-all` tool, specify the name side.

    Parameters:
        arguments (dict): ツールの引数
            - menu (str): メニュー名 / menu name to retrieve the pulldown list for
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Returns:
        dict: プルダウン一覧取得結果
            - result: APIレスポンスのプルダウン一覧 / the pulldown list returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
            - menu (str): メニュー名 / menu name

    Raises:
        Exception: menuが指定されていない場合 / if menu is not specified
        HTTPException: プルダウン一覧の取得に失敗した場合 / if fetching the pulldown list fails
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")
    menu = arguments.get("menu", "")

    if not menu:
        raise Exception("menu is required")

    g.applogger.info(f'Parameter menu={menu}')

    # list-menu-info と同じITA自身のAPI(ita_api_organization)を呼び出すため、
    # 同じ環境変数 ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT を使用する
    #
    # Calls the same ITA's own API (ita_api_organization) as list-menu-info,
    # so the same ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT
    # environment variables are used
    ita_api_host = os.getenv("ITA_API_ORAGANIZATION_HOST")
    ita_api_port = os.getenv("ITA_API_ORAGANIZATION_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/{}/info/pulldown/".format(
        ita_api_host, ita_api_port, organization_id, workspace_id, quote(str(menu), safe="")
    )

    # 転送用ヘッダーを組み立てる
    # Build the headers to forward
    headers = build_forward_headers(method="GET")

    # ITAのAPIへプルダウン一覧取得のGETリクエストを送信する
    # Send a GET request to ITA's API to fetch the pulldown list
    req = requests.get(url, headers=headers, timeout=get_downstream_timeout())

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        g.applogger.info("Failed to fetch menu pulldown list: {} - {}".format(req.status_code, req.text))
        raise HTTPException("list-menu-info-pulldown", req)

    # 正常時はAPIのレスポンスをそのまま結果として返す
    # On success, return the API response as the result
    return {
        "result": req.json(),
        "message": "Menu pulldown list fetched successfully.",
        "organization_id": organization_id,
        "workspace_id": workspace_id,
        "menu": menu
    }
