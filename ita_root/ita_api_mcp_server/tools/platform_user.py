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
プラットフォームユーザー管理ツール

このモジュールは、MCPクライアントから呼び出せる2つのツールを提供する。
  - list-users  : 組織内のユーザー一覧を取得する
  - create-user : 組織内に新規ユーザーを作成する

ita_api_mcp_serverでは前段の認証プロキシが "User-Id" / "Roles" ヘッダーを
付与する方式(ita_api_organization / ita_api_admin と同じ方式)を採用している
ため、ダウンストリームAPI呼び出し時には、リクエストで受け取った
"User-Id" / "Roles" ヘッダーをそのまま転送する。
呼び出し先のAPIパスは "/api/{organization_id}/platform/users" を使用する。

--------------------------------------------------------------------------
Platform user management tools.

This module provides two tools that can be invoked from an MCP client:
  - list-users  : get the list of users in the organization
  - create-user : create a new user in the organization

ita_api_mcp_server relies on the authentication proxy in front of it, which
injects "User-Id" / "Roles" headers (the same scheme used by
ita_api_organization / ita_api_admin). Therefore, when calling the
downstream API, we forward the "User-Id" / "Roles" headers received on the
incoming request as-is.
The downstream API path used is "/api/{organization_id}/platform/users".
"""
import os

import requests
from flask import g

from libs import tool, HTTPException, build_forward_headers


@tool(
    name="list-users",
    description="Get list of all users in the organization",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    },
    required_roles=["_.*-admin", "_og-usr-mt", "_og-ws-role-usr"],
    profile=["AgenticAI"]
)
def tool_list_users(arguments: dict, payload: dict) -> dict:
    """
    組織内のユーザーリストを取得する

    Get the list of users in the organization.

    Parameters:
        arguments (dict): ツールの引数(このツールでは未使用)
            / tool arguments (unused by this tool)
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id

    Returns:
        dict: ユーザーリスト取得結果
            - result: APIレスポンスのユーザーリスト / the user list returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id

    Raises:
        HTTPException: ユーザーリストの取得に失敗した場合 / if fetching the user list fails
    """
    # payloadからオーガナイゼーションIDを取り出す(URLパスから解決済みのもの)
    # Extract the organization id from the payload (already resolved from the URL path)
    organization_id = payload.get("organization_id")

    # このツールが呼び出すのは "/platform/users" というExastro Platform API側の
    # エンドポイントであるため、環境変数 PLATFORM_API_HOST / PLATFORM_API_PORT を使用する
    #
    # This tool calls the "/platform/users" endpoint of the Exastro Platform
    # API, so it uses the PLATFORM_API_HOST / PLATFORM_API_PORT environment
    # variables
    platform_api_host = os.getenv("PLATFORM_API_HOST")
    platform_api_port = os.getenv("PLATFORM_API_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/platform/users".format(platform_api_host, platform_api_port, organization_id)

    # 転送用ヘッダーを組み立てる
    # Build the headers to forward
    headers = build_forward_headers(method="GET")

    # プラットフォームAPIへユーザー一覧取得のGETリクエストを送信する
    # Send a GET request to the platform API to fetch the user list
    req = requests.get(url, headers=headers)

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        g.applogger.info("Failed to fetch user lists: {} - {}".format(req.status_code, req.text))
        raise HTTPException("list-users", req)

    # 正常時はAPIのレスポンスをそのまま結果として返す
    # On success, return the API response as the result
    return {
        "result": req.json(),
        "message": "User list fetched successfully.",
        "organization_id": organization_id
    }


@tool(
    name="create-user",
    description="Create a new user in the organization",
    input_schema={
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "description": "Username for the new user"
            },
            "password": {
                "type": "string",
                "description": "Password for the new user"
            },
            "email": {
                "type": "string",
                "description": "Email address for the new user"
            }
        },
        "required": ["username", "password", "email"]
    },
    required_roles="_og-usr-mt",
    profile=["AgenticAI"]
)
def tool_create_user(arguments: dict, payload: dict) -> dict:
    """
    組織内に新規ユーザーを作成する

    Create a new user in the organization.

    Parameters:
        arguments (dict): ツールの引数
            - username (str): 新規ユーザーのユーザー名 / username for the new user
            - password (str): 新規ユーザーのパスワード / password for the new user
            - email (str): 新規ユーザーのメールアドレス / email address for the new user
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id

    Returns:
        dict: ユーザー作成結果
            - result: APIレスポンスの作成されたユーザー情報 / the created user info returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id

    Raises:
        HTTPException: ユーザーの作成に失敗した場合 / if creating the user fails
    """
    # payloadからオーガナイゼーションIDを取り出す
    # Extract the organization id from the payload
    organization_id = payload.get("organization_id")

    # ツール呼び出し時の引数から、作成するユーザーの情報を組み立てる
    # Build the new user's data from the tool call arguments
    user_data = {
        "username": arguments.get("username", ""),
        "password": arguments.get("password", ""),
        "email": arguments.get("email", ""),
        "password_temporary": True,
        "enabled": True,
        "firstName": "",
        "lastName": "",
        "affiliation": "",
        "description": "",
    }

    g.applogger.info(f'Parameter username={user_data["username"]}')

    # このツールが呼び出すのは "/platform/users" というExastro Platform API側の
    # エンドポイントであるため、環境変数 PLATFORM_API_HOST / PLATFORM_API_PORT を使用する
    #
    # This tool calls the "/platform/users" endpoint of the Exastro Platform
    # API, so it uses the PLATFORM_API_HOST / PLATFORM_API_PORT environment
    # variables
    platform_api_host = os.getenv("PLATFORM_API_HOST")
    platform_api_port = os.getenv("PLATFORM_API_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/platform/users".format(platform_api_host, platform_api_port, organization_id)

    # 転送用ヘッダーを組み立てる(POSTでボディを送るため"Content-Type"も付与する)
    # Build the headers to forward (also adds "Content-Type" since this is a POST with a body)
    headers = build_forward_headers(method="POST")

    # プラットフォームAPIへユーザー作成のPOSTリクエストを送信する
    # Send a POST request to the platform API to create the user
    req = requests.post(url, json=user_data, headers=headers)

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        g.applogger.info("Failed to create user: {} - {}".format(req.status_code, req.text))
        raise HTTPException("create-user", req)

    # 正常時はAPIのレスポンスをそのまま結果として返す
    # On success, return the API response as the result
    return {
        "result": req.json(),
        "message": "User created successfully.",
        "organization_id": organization_id
    }
