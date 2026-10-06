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
mcp_server common function module

ita_api_organization/libs/organization_common.py および
ita_api_admin/libs/admin_common.py の before_request_handler を参考に、
このサービス(ita_api_mcp_server)用の共通処理(ログ出力・メッセージ管理・
リクエストヘッダーチェック)を実装したモジュール。

ita_api_mcp_server は connexion を使わず、素の Flask で
MCP(Model Context Protocol)の JSON-RPC リクエストを直接受け付ける構成とする。

認証については、ita_api_mcp_server の前段に認証プロキシが配置され、
ita_api_organization / ita_api_admin と同様に "User-Id" と "Roles" が
HTTPヘッダーとして渡ってくる想定のため、ここでは Bearer JWT の検証は行わず、
organization/admin と同じヘッダーチェック方式を採用する。

--------------------------------------------------------------------------
This module implements the common processing (logging / message handling /
request header validation) for this service (ita_api_mcp_server), based on
the before_request_handler implementations found in
ita_api_organization/libs/organization_common.py and
ita_api_admin/libs/admin_common.py.

ita_api_mcp_server does not use connexion; it accepts MCP(Model Context
Protocol) JSON-RPC requests directly via plain Flask.

Regarding authentication: an authentication proxy sits in front of
ita_api_mcp_server, and just like ita_api_organization / ita_api_admin, the
"User-Id" and "Roles" values are injected as HTTP headers by that proxy.
Therefore this module does NOT verify a Bearer JWT itself; instead it reuses
the same header-based check used by organization/admin.
"""
import base64
import os
import re

from flask import request, g, jsonify

# common_libs 配下のファイルは変更しない(既存の共通ライブラリをそのまま利用する)
# Files under common_libs are NOT modified; we simply reuse the existing common library.
from common_libs.common.dbconnect import DBConnectOrg
from common_libs.common.exception import AppException
from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate
from common_libs.api import set_api_timestamp, get_api_timestamp, app_exception_response, exception_response, check_request_body
from common_libs.ci.util import set_service_loglevel

# ヘルスチェック用URLかどうかを判定する正規表現
# (organization_common.py / admin_common.py と同じパターン)
#
# Regex used to detect health-check URLs.
# (Same pattern as organization_common.py / admin_common.py)
HEALTH_CHECK_URL_PATTERN = r"/internal-api/health-check/liveness$|/internal-api/health-check/readiness$"

# organization_id/workspace_idを含むURL("/api/<organization_id>/workspaces/<workspace_id>/...")の正規表現
# Regex for URLs containing organization_id/workspace_id ("/api/<organization_id>/workspaces/<workspace_id>/...")
ORG_WS_URL_PATTERN = re.compile(r"^/api/(?P<organization_id>[^/]+)/workspaces/(?P<workspace_id>[^/]+)(/|$)")

# ai_assistantドライバがインストール対象外(無効)にされているかどうかの判定に
# 使う対象文字列。ita_api_organization/controllers/menu_info_controller.py の
# ai_assistant_enabled判定と同じチェック方式(NO_INSTALL_DRIVERの文字列に
# 含まれるかどうか)を用いる。
#
# Driver name used to determine whether the ai_assistant driver has been
# excluded from installation (disabled). Uses the same check
# (whether the name is contained in NO_INSTALL_DRIVER) as the
# ai_assistant_enabled check in
# ita_api_organization/controllers/menu_info_controller.py.
AI_ASSISTANT_DRIVER_NAME = "ai_assistant"


def _is_ai_assistant_driver_enabled(organization_id):
    """
    オーガナイゼーションでai_assistantドライバが有効かどうかを確認する

    ita_api_mcp_server が提供する機能(MCPのJSON-RPCツール全般・
    attachment_fileのアップロード/ダウンロードAPI)は、いずれもai_assistant
    ドライバに属する機能のため、オーガナイゼーション作成時にこのドライバが
    インストール対象外(無効)にされている場合は、機能自体を無効として扱う。

    Check whether the ai_assistant driver is enabled for the organization.

    Every feature provided by ita_api_mcp_server (all MCP JSON-RPC tools, and
    the attachment_file upload/download API) belongs to the ai_assistant
    driver. So if this driver was excluded from installation (disabled) when
    the organization was created, the feature itself is treated as disabled.

    Args:
        organization_id (str): organization id

    Returns:
        bool: 有効な場合True / True if enabled
    """
    org_db = DBConnectOrg(organization_id)
    try:
        no_install_driver = org_db.get_no_install_driver()
    finally:
        org_db.db_disconnect()

    return no_install_driver is None or AI_ASSISTANT_DRIVER_NAME not in no_install_driver


def before_request_handler():
    """
    called before each request is handled (Flask `before_request` hook)

    Flaskの `before_request` として登録されるフック関数。
    organization/admin と同様に、リクエストごとに以下を行う。
      1. APIタイムスタンプの設定
      2. AppLog(ログ出力クラス)・MessageTemplate(メッセージ管理クラス)の初期化
      3. リクエストボディの形式チェック
      4. ヘルスチェック用URL以外の場合、User-Id/Rolesヘッダーのチェックと
         organization_id/workspace_idの特定

    Registered as Flask's `before_request` hook.
    For every incoming request (mirrors organization/admin), this function:
      1. sets the API timestamp used in log output
      2. initializes AppLog (g.applogger) and MessageTemplate (g.appmsg)
      3. validates the request body content-type/format
      4. for non health-check URLs, validates the "User-Id"/"Roles" headers
         and resolves organization_id / workspace_id from the URL path
    """
    try:
        # APIタイムスタンプをセットする(ログ出力時刻の基準として使用)
        # Set the API timestamp (used as the reference time in log lines)
        set_api_timestamp()

        # デフォルト言語を環境変数から取得する
        # Read the default language from the environment variable
        g.LANGUAGE = os.environ.get("DEFAULT_LANGUAGE")

        # ログ出力クラス・メッセージ管理クラスのインスタンスを生成する
        # Create the log-output class instance and the message-template class instance
        g.applogger = AppLog()
        g.appmsg = MessageTemplate(g.LANGUAGE)

        # T_COMN_LOGLEVEL(SERVICE_NAME単位のログレベル設定)があれば、その値で
        # ログレベルを上書きする(organization/admin と同じ仕組み)。テーブルが
        # 無い、またはこのサービス(SERVICE_NAME)の設定が無い場合は、環境変数
        # LOG_LEVEL(未設定時はINFO)にフォールバックする。
        #
        # Override the log level with the value from T_COMN_LOGLEVEL (the
        # per-SERVICE_NAME log level setting), if present (same mechanism as
        # organization/admin). Falls back to the LOG_LEVEL environment
        # variable (default "INFO") if the table or a row for this service
        # (SERVICE_NAME) does not exist.
        set_service_loglevel()

        # リクエストボディがContent-Typeに応じた正しい形式かどうかをチェックする
        # Check that the request body matches the format implied by its Content-Type
        check_request_body()

        # ヘルスチェック用のURLの場合は、User-Id/Rolesのチェックや
        # organization_id/workspace_idの特定を行わない(healthチェックには不要なため)
        #
        # For health-check URLs, skip the User-Id/Roles validation and the
        # organization_id/workspace_id resolution below (not needed for a health check).
        #
        # MCPのエンドポイントは "/api/<organization_id>/workspaces/<workspace_id>/mcp" の
        # 形式(ita_api_organizationのURL設計を踏襲)なので、正規表現で
        # organization_id・workspace_idを取得する。
        # この形式に一致しないURL("/", "/mcp", "/rpc"等)では、以降のヘッダーチェック等を
        # 行わずにルーティングへ任せ、api.pyのフォールバック(400)またはFlask標準の404を返す。
        #
        # The MCP endpoint URL is shaped like
        # "/api/<organization_id>/workspaces/<workspace_id>/mcp"
        # (following ita_api_organization's URL design), so organization_id /
        # workspace_id are extracted with a regex.
        # For URLs not matching this shape ("/", "/mcp", "/rpc", etc.), the checks
        # below are skipped and routing decides the response: api.py's fallback
        # (400) or Flask's standard 404.
        is_health_check = re.search(HEALTH_CHECK_URL_PATTERN, request.url) is not None
        org_ws_match = ORG_WS_URL_PATTERN.match(request.path)

        if not is_health_check and org_ws_match is None:
            g.applogger.info("[ts={}][api-start] url:{}".format(get_api_timestamp(), request.method + ":" + request.url))

        elif not is_health_check:
            organization_id = org_ws_match.group("organization_id")
            g.ORGANIZATION_ID = organization_id
            workspace_id = org_ws_match.group("workspace_id")
            g.WORKSPACE_ID = workspace_id

            # ita_api_mcp_serverの機能はai_assistantドライバに属するため、
            # このオーガナイゼーションでai_assistantドライバが無効化されている
            # 場合は、全てのツール・APIを対象にHTTP 403で機能無効を返す。
            # ITA共通のメッセージコード(AppException)は使わず、固定の英語
            # メッセージを直接返す。
            #
            # Every feature of ita_api_mcp_server belongs to the ai_assistant
            # driver, so if the ai_assistant driver is disabled for this
            # organization, return an HTTP 403 (feature disabled) for every
            # tool/API. This does not use ITA's common message-code mechanism
            # (AppException); it returns a fixed English message directly.
            if not _is_ai_assistant_driver_enabled(organization_id):
                return jsonify({"message": "This feature is disabled."}), 403

            # 認証プロキシが付与する "User-Id" ヘッダーを取得する
            # Get the "User-Id" header injected by the authentication proxy
            user_id = request.headers.get("User-Id")

            # 認証プロキシが付与する "Roles" ヘッダー(Base64エンコード済み、
            # 改行区切りのロール一覧)を取得し、デコードする
            #
            # Get the "Roles" header injected by the authentication proxy
            # (Base64-encoded, newline-separated list of roles) and decode it
            roles_org = request.headers.get("Roles")
            try:
                roles_decode = base64.b64decode(roles_org.encode()).decode("utf-8")
            except Exception:
                # Base64デコードに失敗した場合はヘッダー不正としてエラーにする
                # If Base64 decoding fails, treat it as an invalid header and raise an error
                raise AppException("400-00001", ["Roles"], ["Roles"])
            roles = roles_decode.split("\n")

            # User-Id または Roles が取得できない場合はリクエストヘッダー不正とする
            # If either User-Id or Roles could not be resolved, the request header is invalid
            if user_id is None or roles is None or type(roles) is not list:
                raise AppException("400-00001", ["User-Id or Roles"], ["User-Id or Roles"])

            # 取得したUser-Id/Rolesをリクエストスコープ(g)に保存する
            # tools/*.py からダウンストリームAPIを呼び出す際にも、
            # 元のHTTPヘッダー(request.headers)から直接参照して転送する。
            #
            # Store the resolved User-Id/Roles on the request-scoped `g` object.
            # When tools/*.py calls a downstream API, it forwards the ORIGINAL
            # HTTP header values (read again from request.headers) as-is.
            g.USER_ID = user_id
            g.ROLES = roles

            # ログ出力の接頭辞([ORGANIZATION_ID:xxx]など)を設定する
            # Configure the log line prefix (e.g. "[ORGANIZATION_ID:xxx]")
            g.applogger.set_env_message()

            # APIリクエスト開始のログを出力する
            # Log that an API request has started
            debug_args = [request.method + ":" + request.url]
            g.applogger.info("[ts={}][api-start] url:{}".format(get_api_timestamp(), *debug_args))

        # リクエストヘッダーに言語指定がある場合、優先してその言語を使用する
        # If the request header specifies a language, prefer that language
        language = request.headers.get("Language")
        if language:
            g.LANGUAGE = language
            g.appmsg.set_lang(language)
            g.applogger.debug("LANGUAGE({}) is set".format(language))

        # NOTE:
        # organization_common.py / admin_common.py ではここで
        # 組織DB・ワークスペースDBへの接続確認(DBConnectOrg/DBConnectWs)や
        # メンテナンスモード確認(get_maintenance_mode_setting)も行っています。
        # ita_api_mcp_serverでは、上記の_is_ai_assistant_driver_enabled呼び出しで
        # DBConnectOrgによる組織DBへの接続(ドライバ有効チェック)のみ行っており、
        # ワークスペースDBへの接続確認・メンテナンスモード確認は現状組み込んでいません
        # (サービス単位のログレベル設定は上記のset_service_loglevel()で対応済み)。
        # 今後これらが必要になった場合は、common_libs.common.dbconnect の
        # DBConnectWs等を用いて organization/admin と同様の処理を追加してください。
        #
        # organization_common.py / admin_common.py additionally connect to the
        # organization/workspace database (DBConnectOrg/DBConnectWs) and check
        # the maintenance mode (get_maintenance_mode_setting) here.
        # ita_api_mcp_server only connects to the organization DB via
        # DBConnectOrg (the driver-enabled check) through the
        # _is_ai_assistant_driver_enabled call above; the workspace DB
        # connectivity check and maintenance mode check are not implemented
        # yet (the per-service log level setting is already handled above via
        # set_service_loglevel()).
        # Add the same processing as organization/admin (using
        # common_libs.common.dbconnect's DBConnectWs etc.) when they become
        # necessary.
    except AppException as e:
        # AppException(業務エラー)を捕捉し、ITA共通のエラーレスポンス形式に変換する
        # Catch AppException (business error) and convert it into ITA's common error response
        return app_exception_response(e)
    except Exception as e:
        # その他の予期しない例外を捕捉し、500エラーのレスポンスに変換する
        # Catch any other unexpected exception and convert it into a 500 error response
        return exception_response(e)


def log_api_end(status_code, is_success=True):
    """
    APIリクエスト終了のログを出力する

    before_request_handler で出力する [api-start] と対になるログ。
    ita_api_mcp_server は make_response (common_libs.api.util) を経由せず
    独自にレスポンスを組み立てているため、通常はafter_request_handlerが
    レスポンスのHTTPステータスコードから自動的にこの関数を呼び出す。

    ただしjsonrpc_handler の "tools/call" 成功パスは、ツール実行が失敗しても
    HTTPステータスは常に200を返し、成否は結果内のisErrorで表現する
    (JSON-RPCの仕様上、トランスポートレベルでは成功のため)。この場合は
    HTTPステータスコードだけでは意味的な成否・ステータスコードを判別できないため、
    api.py側(jsonrpc_handler / create_error_response)から明示的にこの関数を
    呼び出し、after_request_handlerによる重複ログを防ぐ。

    Log that an API request has finished ([api-end]).

    This pairs with the [api-start] log emitted by before_request_handler.
    Because ita_api_mcp_server builds its responses directly instead of going
    through common_libs.api.util.make_response, this is normally called
    automatically by after_request_handler, based on the response's HTTP
    status code.

    However, the "tools/call" success path in jsonrpc_handler always returns
    HTTP 200 even when the tool itself failed (success/failure is instead
    expressed via isError in the result), because JSON-RPC treats this as a
    transport-level success. In that case the HTTP status code alone cannot
    tell us the semantic success/status code, so api.py (jsonrpc_handler /
    create_error_response) calls this function explicitly, which also
    prevents after_request_handler from logging it a second time.
    """
    log_status = "SUCCESS" if is_success else "FAILURE"
    g.applogger.info("[ts={}][api-end][{}][status_code={}]".format(get_api_timestamp(), log_status, status_code))
    g.API_END_LOGGED = True


def after_request_handler(response):
    """
    called after each request is handled (Flask `after_request` hook)

    [api-start]と対になる[api-end]ログを、レスポンスのHTTPステータスコードから
    自動的に出力する。log_api_end()が既に明示的に呼ばれている場合
    (jsonrpc_handler の "tools/call" 成功パスなど、HTTPステータスコードとは
    別の意味的なステータスをログに残す必要がある場合)は、ここでは重複して
    出力しない。ヘルスチェック用URLは、before_request_handlerが[api-start]を
    出力していないため、対になる[api-end]もここで出力しない。

    Automatically emit the [api-end] log (paired with [api-start]) based on
    the response's HTTP status code. If log_api_end() has already been
    called explicitly (e.g. the "tools/call" success path in jsonrpc_handler,
    which needs to log a semantic status code that differs from the HTTP
    status code), this does not log it again. Health-check URLs are skipped
    here too, since before_request_handler does not emit [api-start] for them.

    Args:
        response (flask.Response): このリクエストに対するレスポンス
            / the response for this request

    Returns:
        flask.Response: 引数のresponseをそのまま返す / the response, unchanged
    """
    if re.search(HEALTH_CHECK_URL_PATTERN, request.url) is None and not g.get("API_END_LOGGED"):
        log_api_end(response.status_code, response.status_code < 400)

    return response
