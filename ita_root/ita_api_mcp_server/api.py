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
ita_api_mcp_server のエントリーポイント

ita_api_organization / ita_api_admin と異なり、このサービスは connexion +
swagger(openapi) を使わず、素のFlaskでMCP(Model Context Protocol)の
JSON-RPCリクエストを直接受け付ける構成とする。

一方で、以下の「共通機能」については ita_api_organization / ita_api_admin と
同じ考え方・同じ common_libs の関数を利用する。
  - ログ出力      : common_libs.common.logger.AppLog (libs/mcp_server_common.py 経由)
  - リクエスト共通処理 : before_request_handler (libs/mcp_server_common.py)
  - ヘルスチェック  : common_libs.common.dbconnect.DBConnectCommonRoot ,
                    common_libs.api.api_filter_admin

--------------------------------------------------------------------------
Entry point of ita_api_mcp_server.

Unlike ita_api_organization / ita_api_admin, this service does not use
connexion + swagger(openapi); it accepts MCP (Model Context Protocol)
JSON-RPC requests directly via plain Flask.

On the other hand, the following "common" pieces reuse the same approach and
the same common_libs functions as ita_api_organization / ita_api_admin:
  - logging          : common_libs.common.logger.AppLog (via libs/mcp_server_common.py)
  - common request handling : before_request_handler (libs/mcp_server_common.py)
  - health check      : common_libs.common.dbconnect.DBConnectCommonRoot ,
                        common_libs.api.api_filter_admin
"""
import os

from dotenv import load_dotenv  # python-dotenv
from flask import Flask, request, jsonify, g

# common_libs 配下のファイルは変更しない(既存の共通ライブラリをそのまま利用する)
# Files under common_libs are NOT modified; we simply reuse the existing common library.
from common_libs.common.dbconnect import *  # noqa: F403  (DBConnectCommonRoot を利用する / used for DBConnectCommonRoot)
from common_libs.api import api_filter_admin

# このサービス独自の共通処理(before_request_handler)をimportする
# Import this service's own common processing (before_request_handler)
from libs.mcp_server_common import before_request_handler, after_request_handler, log_api_end

# ツール呼び出しに必要な関数・例外クラスをimportする
# Import the functions/exception classes needed to invoke tools
from libs import (
    load_dynamic_tools, get_tool_functions, check_tool_permission, HTTPException,
    is_tool_visible, is_tool_in_profile
)

# tools パッケージをimportすることで、配下の @tool デコレーター付き関数が
# レジストリ(libs.tools_decorator.TOOL_REGISTRY)に登録される。
# また、attachment_file.py のように@toolデコレーターではなく通常のFlaskルート
# (Blueprint)として提供されるものは、tools.attachment_file_bp として
# このimportを通じて参照できるようになる。
#
# Importing the tools package registers every @tool-decorated function found
# in it into the registry (libs.tools_decorator.TOOL_REGISTRY).
# It also makes Blueprints provided as ordinary Flask routes instead of
# @tool-decorated functions (e.g. attachment_file.py) available as
# tools.attachment_file_bp through this import.
import tools


# .env ファイルの環境変数を読み込む(既存値は上書きする)
# Load environment variables from the .env file (override existing ones)
load_dotenv(override=True)

# connexionを使わない素のFlaskアプリケーションを生成する
# (ita_api_organization/admin は connexion.FlaskApp を使うが、本サービスは
#  Flaskをそのまま使う)
#
# Create a plain Flask application without connexion.
# (ita_api_organization/admin use connexion.FlaskApp, but this service uses
#  Flask directly.)
app = Flask(__name__)

# 各リクエストの処理前に共通処理(ログ初期化・ヘッダーチェック等)を実行するよう登録する
# Register the common pre-processing (log init / header validation, etc.)
# to run before every request
app.before_request(before_request_handler)

# 各リクエストの処理後に[api-end]ログを自動出力するよう登録する
# (jsonrpc_handler の "tools/call" 成功パスのように、明示的にlog_api_endを
#  呼んでいる場合は、after_request_handler側で重複ログを防ぐ)
#
# Register automatic [api-end] logging to run after every request.
# (When log_api_end has already been called explicitly — e.g. the
#  "tools/call" success path in jsonrpc_handler — after_request_handler
#  avoids logging it a second time)
app.after_request(after_request_handler)

# tools パッケージが提供するBlueprintを登録する
# Register the Blueprints provided by the tools package
app.register_blueprint(tools.attachment_file_bp)


# ============================================================================
# ヘルスチェック(healthcheck)
# organization/admin の internal_health_check_service_controller.py を参考に、
# ここではconnexionのcontrollerではなく、Flaskのルートとして直接実装する。
#
# Health check.
# Based on organization/admin's internal_health_check_service_controller.py,
# implemented here directly as Flask routes instead of a connexion controller.
# ============================================================================

def _run_health_check_query():
    """
    DBへの接続確認用の簡易クエリ("SELECT 1")を実行する。

    Run a simple query ("SELECT 1") to verify database connectivity.
    """
    # 共通DB(ITAの管理DB)にrootユーザーで接続する
    # Connect to the common DB (ITA's management DB) as the root user
    common_db_root = DBConnectCommonRoot()  # noqa: F405
    try:
        # 接続確認のためだけの軽いクエリを実行する
        # Execute a lightweight query purely to verify connectivity
        common_db_root.sql_execute("SELECT 1 AS DATA", [])
    finally:
        # 成功・失敗にかかわらず必ず切断する
        # Always disconnect regardless of success or failure
        common_db_root.db_disconnect()


#
# NOTE: api_filter_admin でラップした関数は __name__ が "wrapper" になるため、
# Flaskのエンドポイント名が重複してしまう。そのため endpoint= を明示的に指定する。
#
# NOTE: functions wrapped by api_filter_admin all end up with __name__=="wrapper",
# which would otherwise collide as Flask endpoint names. We explicitly pass
# endpoint= to avoid that collision.
@app.route('/internal-api/health-check/liveness', methods=['GET'], endpoint='internal_health_check_liveness')
@api_filter_admin
def internal_health_check_liveness():
    """
    liveness(プロセスが生存しているか)のヘルスチェック

    Liveness health check (whether the process is alive).
    """
    # DBに接続できるかどうかを確認する
    # Verify that the database can be reached
    _run_health_check_query()
    # 成功時は "000-00000"(Success)のAPIメッセージを返す
    # On success, return the "000-00000" (Success) API message
    return g.appmsg.get_api_message("000-00000"),


@app.route('/internal-api/health-check/readiness', methods=['GET'], endpoint='internal_health_check_readiness')
@api_filter_admin
def internal_health_check_readiness():
    """
    readiness(リクエストを受け付けられる状態か)のヘルスチェック

    Readiness health check (whether the service is ready to accept requests).
    """
    # readinessもliveness同様にDB接続確認を行う
    # (connexion経由でliveness関数をそのまま呼び出すことができないため、
    #  同じ確認処理を明示的に呼び直している)
    #
    # readiness performs the same DB connectivity check as liveness.
    # (Because we are not going through connexion, we cannot simply call the
    #  already-decorated liveness function here, so we call the shared check
    #  explicitly instead.)
    _run_health_check_query()
    return g.appmsg.get_api_message("000-00000"),


# ============================================================================
# MCP(Model Context Protocol) JSON-RPC ハンドラ
#
# MCP (Model Context Protocol) JSON-RPC handlers.
# ============================================================================

def create_error_response(error_msg: str, code: int = -32603, request_id=None, status_code: int = 500):
    """
    JSON-RPCエラーレスポンスを作成する

    Build a JSON-RPC error response.

    Parameters:
        error_msg (str): エラーメッセージ / error message
        code (int, optional): JSON-RPCエラーコード(デフォルト: -32603)
            / JSON-RPC error code (default: -32603)
        request_id (optional): リクエストID / request id
        status_code (int, optional): HTTPステータスコード(デフォルト: 500)
            / HTTP status code (default: 500)

    Returns:
        tuple: (jsonifyされたレスポンス, HTTPステータスコード)
            / (jsonified response, HTTP status code)
    """
    response = {
        "jsonrpc": "2.0",
        "error": {
            "code": code,
            "message": error_msg
        },
        "id": request_id
    }

    # APIリクエスト終了のログを出力する([api-start]と対にする)
    # Log that the API request has finished (pairs with [api-start])
    log_api_end(status_code, is_success=False)

    return jsonify(response), status_code


def handle_initialize(params: dict, payload: dict) -> dict:
    """
    MCPの "initialize" メソッドを処理する

    Handle the MCP "initialize" method.
    """
    # 初期化要求を受け付けたことをログに出力する
    # Log that an initialize request has been received
    g.applogger.info("Initialize request received")
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {},
        },
        "serverInfo": {
            "name": "ita-api-mcp-server",
            "version": "1.0.0"
        }
    }


def handle_tools_list(params: dict, payload: dict) -> dict:
    """
    MCPの "tools/list" メソッドを処理する

    クエリー文字列 `profile` が指定されている場合、tool デコレーターの
    profile 引数と一致するツールのみに絞り込む(未指定の場合は絞り込みを
    行わず全ツールを対象とする)。

    Handle the MCP "tools/list" method.

    If the `profile` query string is given, results are narrowed down to
    tools whose @tool decorator `profile` argument matches it (if not given,
    no narrowing is applied and every tool is a candidate).
    """
    profile = payload.get("profile")

    # 登録済みの全ツール設定を取得する
    # Get the configuration of every registered tool
    all_tools = load_dynamic_tools()

    # ITAメニュー権限のチェック結果を1回のtools/list呼び出しの中で再利用するための
    # キャッシュ(organization_id/workspace_id毎に、ITAのメニュー一覧APIを
    # 複数回呼び出さないようにする)
    #
    # Cache used to reuse the ITA menu-permission check result within a single
    # tools/list call (avoids calling ITA's menu-list API more than once per
    # organization_id/workspace_id)
    menu_cache = {}

    # 有効(enabled)であり、かつ実行権限のあるツールのみを一覧に含める。
    # (ロール規制(Role-Detail)・ITAメニュー規制・権限チェック無しの3種類は
    #  libs/permissions.py の is_tool_visible が判定する)
    #
    # Only include tools that are enabled and that the caller has permission
    # to see. (The three permission kinds - role restriction based on
    # "Role-Detail", ITA menu restriction, and no restriction - are decided
    # by is_tool_visible in libs/permissions.py)
    available_tools = [
        {
            "name": t["name"],
            "description": t["description"],
            "inputSchema": t.get("inputSchema", {"type": "object", "properties": {}})
        }
        for t in all_tools
        if t.get("enabled", True)
        and is_tool_in_profile(t, profile)
        and is_tool_visible(t, payload, menu_cache)
    ]

    g.applogger.info("List tools: count={}".format(len(available_tools)))
    return {"tools": available_tools}


# 引数名(小文字)がここに含まれる場合、ログ出力時に値をマスクする
# (create-user の password など、機密情報がログに残らないようにするため)
#
# If an argument's name (lowercased) is in this set, its value is masked
# when logged (e.g. create-user's password, so secrets never end up in logs)
SENSITIVE_ARG_KEYS = {"password"}


def _mask_sensitive_args(arguments: dict) -> dict:
    """
    ログ出力用に、機密情報を含む引数をマスクしたコピーを返す

    Return a copy of `arguments` with sensitive values masked, for logging.
    """
    if not isinstance(arguments, dict):
        return arguments
    return {
        key: ("***" if key.lower() in SENSITIVE_ARG_KEYS else value)
        for key, value in arguments.items()
    }


def handle_tools_call(params: dict, payload: dict) -> dict:
    """
    MCPの "tools/call" メソッドを処理する

    Handle the MCP "tools/call" method.
    """
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    organization_id = payload.get("organization_id", "unknown")
    workspace_id = payload.get("workspace_id", "unknown")

    # ツール名が指定されていない場合はエラーとする
    # If no tool name was specified, raise an error
    if not tool_name:
        raise Exception("Tool name is required")

    g.applogger.info("Tool call: tool={}".format(tool_name))
    g.applogger.debug("Tool call args={}".format(_mask_sensitive_args(arguments)))

    # ツールが存在し、実行可能かどうかを確認する
    # Verify that the tool exists and may be executed
    check_tool_permission(tool_name, payload)

    # レジストリから実処理関数を取得する
    # Get the implementation function from the registry
    tool_functions = get_tool_functions()

    # 実処理関数が見つからない場合はエラーとする(通常は発生しない想定)
    # If the implementation function cannot be found, raise an error
    # (this should not normally happen)
    if tool_name not in tool_functions:
        raise Exception("Tool implementation not found: {}".format(tool_name))

    tool_func = tool_functions[tool_name]

    try:
        # ツールの実処理を呼び出す
        # Invoke the tool's implementation
        result = tool_func(arguments, payload)

        g.applogger.debug(
            "Tool call completed: tool={}".format(tool_name)
        )

        # 結果からメッセージを取り出す(無ければデフォルト文言を使う)
        # Extract the message from the result (fall back to a default if absent)
        message = result.get("message", "処理が完了しました")

        # MCPの標準レスポンス形式で返す
        # Return in the MCP standard response format
        return {
            "structuredContent": {
                "tool_name": tool_name,
                "status_code": 200,
                **result,
                "organization_id": organization_id,
                "workspace_id": workspace_id
            },
            "content": [
                {
                    "type": "text",
                    "text": message
                }
            ],
            "isError": False
        }

    except HTTPException as e:
        # ダウンストリームAPI呼び出しがHTTPエラーになった場合の処理
        # (MCPサーバー自体の異常ではなく呼び出し先APIが返したビジネスエラーのため、
        #  ログレベルはERRORではなくINFOとする)
        #
        # Handle the case where the downstream API call returned an HTTP error.
        # (This is a business error returned by the downstream API, not a
        #  failure of the MCP server itself, so it is logged at INFO rather
        #  than ERROR.)
        g.applogger.info("Tool call failed with HTTP error: {}".format(e.message))
        g.applogger.info("Status code: {}, Tool: {}".format(e.status_code, e.tool_name))

        return {
            "structuredContent": {
                "tool_name": e.tool_name,
                "status_code": e.status_code,
                "result": e.response_body,
                "organization_id": organization_id,
                "workspace_id": workspace_id
            },
            "content": [
                {
                    "type": "text",
                    "text": e.message
                }
            ],
            "isError": True
        }

    except Exception as e:
        # その他予期しないエラーの処理
        # Handle any other unexpected error
        g.applogger.error("Tool call failed: {}".format(str(e)))

        return {
            "structuredContent": {
                "tool_name": tool_name,
                "error": str(e),
                "organization_id": organization_id,
                "workspace_id": workspace_id
            },
            "content": [
                {
                    "type": "text",
                    "text": str(e)
                }
            ],
            "isError": True
        }


# JSON-RPCのメソッド名 -> ハンドラ関数 のマッピング
# (resources/list, resources/read は今回のスコープ外のため未実装)
#
# Mapping from JSON-RPC method name -> handler function.
# (resources/list and resources/read are not implemented, as they are out of
#  scope for this task.)
JSONRPC_METHODS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
}


@app.route('/', methods=['POST'])
@app.route('/mcp', methods=['POST'])
@app.route('/rpc', methods=['POST'])
def jsonrpc_handler_no_params():
    """
    organization_id / workspace_id を含まないURLへのリクエストを処理する

    NOTE: before_request_handler が先に呼ばれるため、User-Id/Rolesヘッダーの
    検証や organization_id/workspace_id の解決がそこで失敗し、実際にはこの
    関数まで到達しないケースが多い。MCPクライアントが誤ったURLでアクセスした
    場合に分かりやすいエラーを返すためのフォールバックとして残している。

    Handle requests to URLs that do not contain organization_id / workspace_id.

    NOTE: because before_request_handler runs first, the User-Id/Roles header
    validation and organization_id/workspace_id resolution performed there
    will often fail before this function is reached. This route is kept as a
    fallback that returns a clearer error when an MCP client accesses the
    wrong URL.
    """
    data = request.get_json(silent=True)
    request_id = data.get("id") if data else None
    g.applogger.info("Request without organization_id and workspace_id specified")
    return create_error_response(
        "Organization ID and Workspace ID are required in URL path. Use /api/<organization_id>/workspaces/<workspace_id>/mcp",
        -32600,
        request_id,
        400
    )


@app.route('/api/<organization_id>/workspaces/<workspace_id>/mcp', methods=['POST'])
def jsonrpc_handler(organization_id, workspace_id):
    """
    MCPクライアントからのJSON-RPCリクエストを処理する単一エンドポイント

    Single endpoint that handles JSON-RPC requests coming from MCP clients.
    """
    try:
        # リクエストボディをJSON-RPCとして解釈する
        # Parse the request body as a JSON-RPC request
        data = request.get_json(silent=True)
        if not data:
            return create_error_response("Invalid JSON-RPC request", -32700, None, 400)

        jsonrpc_version = data.get("jsonrpc")
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")

        # JSON-RPCのバージョンが"2.0"以外の場合はエラーとする
        # If the JSON-RPC version is not "2.0", raise an error
        if jsonrpc_version != "2.0":
            return create_error_response("Invalid JSON-RPC version", -32600, request_id, 400)

        # methodが指定されていない場合はエラーとする
        # If method is not specified, raise an error
        if not method:
            return create_error_response("Method is required", -32600, request_id, 400)

        # 呼び出しコンテキスト(payload)を組み立てる。
        # User-Id/Rolesヘッダーの検証、organization_id/workspace_idの解決は
        # before_request_handler(libs/mcp_server_common.py)側で既に完了している。
        #
        # Build the call context (payload).
        # The User-Id/Roles header validation and organization_id/workspace_id
        # resolution have already been completed by before_request_handler
        # (libs/mcp_server_common.py).
        payload = {
            "organization_id": g.get("ORGANIZATION_ID"),
            "workspace_id": g.get("WORKSPACE_ID"),
            "user_id": g.get("USER_ID"),
            "roles": g.get("ROLES"),
            "profile": request.args.get("profile"),
        }

        # メソッド名がサポート対象外の場合はエラーとする
        # If the method name is not supported, raise an error
        if method not in JSONRPC_METHODS:
            return create_error_response("Method not found: {}".format(method), -32601, request_id, 404)

        # 対応するハンドラ関数を呼び出す
        # Invoke the corresponding handler function
        handler = JSONRPC_METHODS[method]
        result = handler(params, payload)

        # APIリクエスト終了のログを出力する([api-start]と対にする)。
        # tools/call はツール実行が失敗しても例外を投げず、
        # isError:True を含む result を正常応答として返すため、
        # HTTPレベルの成否だけでなくツールの実行結果(isError)も見て
        # SUCCESS/FAILUREを判定する。
        #
        # Log that the API request has finished (pairs with [api-start]).
        # tools/call does not raise on a tool-level failure; instead it
        # returns a normal result containing isError:True. So determine
        # SUCCESS/FAILURE from the tool's own result, not just the fact
        # that the handler returned without raising.
        if isinstance(result, dict) and result.get("isError"):
            error_status_code = result.get("structuredContent", {}).get("status_code", 500)
            log_api_end(error_status_code, is_success=False)
        else:
            log_api_end(200, is_success=True)

        return jsonify({
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        })

    except Exception as e:
        # ハンドラ内で捕捉されなかった例外はここでまとめてJSON-RPCエラーに変換する。
        # ここに到達するのは基本的にリクエスト内容(ツール名不正・権限不足等)が
        # 原因のケースであり、MCPサーバー自体の不具合ではないためINFOログとする。
        #
        # Any exception not caught inside the handler is converted into a
        # JSON-RPC error here. Reaching this point is normally caused by the
        # request content itself (invalid tool name, insufficient permission,
        # etc.), not a bug in the MCP server, so this is logged at INFO.
        g.applogger.info("JSON-RPC error: {}".format(str(e)))
        request_id = None
        request_json = request.get_json(silent=True)
        if request_json:
            request_id = request_json.get("id")
        return create_error_response(str(e), -32603, request_id, 500)


if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=int(os.environ.get('LISTEN_PORT', '8000')),
        threaded=True
    )
