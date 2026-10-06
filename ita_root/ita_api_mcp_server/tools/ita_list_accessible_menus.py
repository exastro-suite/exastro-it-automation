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
ITAアクセス可能メニュー一覧取得ツール ("list-accessible-menus")

呼び出しユーザーがアクセス可能なメニューグループ・メニューの一覧を、
ITAのAPI( /api/{organization_id}/workspaces/{workspace_id}/ita/user/menus/ )
を呼び出して取得するツール。ユーザー自身がアクセスできるメニューを返すだけの
処理であり、実行に特別な権限は不要なため、@tool デコレーターの
required_roles / required_menu は指定していない(誰でも実行可能)。

ita_api_mcp_serverでは前段の認証プロキシが "User-Id" / "Roles" ヘッダーを
付与する方式(ita_api_organization / ita_api_admin と同じ方式)を採用している
ため、ダウンストリームAPI呼び出し時には、リクエストで受け取った
"User-Id" / "Roles" ヘッダーをそのまま転送する。
呼び出し先のAPIパスは "/api/{organization_id}/workspaces/{workspace_id}/ita/user/menus/" を使用する。

--------------------------------------------------------------------------
ITA accessible-menu list tool ("list-accessible-menus")

Fetches the list of menu groups/menus accessible to the calling user by
calling ITA's API
( /api/{organization_id}/workspaces/{workspace_id}/ita/user/menus/ ).
This only returns the menus the user can already access, so no special
permission is required to run it; the @tool decorator's required_roles /
required_menu are left unset (callable by anyone).

ita_api_mcp_server relies on the authentication proxy in front of it, which
injects "User-Id" / "Roles" headers (the same scheme used by
ita_api_organization / ita_api_admin). Therefore, when calling the
downstream API, we forward the "User-Id" / "Roles" headers received on the
incoming request as-is.
The downstream API path used is
"/api/{organization_id}/workspaces/{workspace_id}/ita/user/menus/".
"""
import os

import requests
from flask import g

from libs import tool, HTTPException, build_forward_headers, get_downstream_timeout


@tool(
    name="list-accessible-menus",
    description="Get the list of accessible menu groups and menus for the calling user",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    },
    profile=["AgenticAI", "LLMEditor"]
)
def tool_list_accessible_menus(arguments: dict, payload: dict) -> dict:
    """
    アクセス可能なメニューグループ・メニューの一覧を取得する

    Get the list of accessible menu groups and menus for the calling user.

    Parameters:
        arguments (dict): ツールの引数(このツールでは未使用)
            / tool arguments (unused by this tool)
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Returns:
        dict: メニュー一覧取得結果
            - result: APIレスポンスのメニュー一覧 / the menu list returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Raises:
        HTTPException: メニュー一覧の取得に失敗した場合 / if fetching the menu list fails
    """
    # payloadからオーガナイゼーションID・ワークスペースIDを取り出す(URLパスから解決済みのもの)
    # Extract the organization id / workspace id from the payload (already
    # resolved from the URL path)
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")

    # このツールが呼び出すのは "/ita/user/menus/" というITA自身のAPI
    # (ita_api_organization)側のエンドポイントであるため、環境変数
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT を使用する
    #
    # This tool calls the "/ita/user/menus/" endpoint of ITA's own API
    # (ita_api_organization), so it uses the ITA_API_ORAGANIZATION_HOST /
    # ITA_API_ORAGANIZATION_PORT environment variables
    ita_api_host = os.getenv("ITA_API_ORAGANIZATION_HOST")
    ita_api_port = os.getenv("ITA_API_ORAGANIZATION_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/workspaces/{}/ita/user/menus/".format(
        ita_api_host, ita_api_port, organization_id, workspace_id
    )

    # 転送用ヘッダーを組み立てる
    # Build the headers to forward
    headers = build_forward_headers(method="GET")

    # ITAのAPIへメニュー一覧取得のGETリクエストを送信する
    # Send a GET request to ITA's API to fetch the menu list
    req = requests.get(url, headers=headers, timeout=get_downstream_timeout())

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        g.applogger.info("Failed to fetch accessible menus: {} - {}".format(req.status_code, req.text))
        raise HTTPException("list-accessible-menus", req)

    # 正常時はAPIのレスポンスをそのまま結果として返す
    # On success, return the API response as the result
    return {
        "result": req.json(),
        "message": "Accessible menus fetched successfully.",
        "organization_id": organization_id,
        "workspace_id": workspace_id
    }
