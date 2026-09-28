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
MCPサーバー用ツールデコレーターモジュール

tools/*.py の各関数に @tool デコレーターを付けることで、
MCPの "tools/list" ・ "tools/call" から呼び出せるように登録する。

@tool デコレーターでは、ツール毎に実行権限の種類を指定できる
(詳細は libs/permissions.py を参照)。
  - required_roles : "Role-Detail" ヘッダーのロールによる規制
  - required_menu  : ITAのメニュー権限による規制
  - どちらも未指定  : 権限チェック無し(誰でも実行可能)

NOTE: ログ出力について
  Flask標準の `logging.getLogger(__name__)` を使うと、
  common_libs.common.logger.AppLog がリクエスト単位で
  logging.config.dictConfig(...) を呼び出す際に
  (disable_existing_loggers のデフォルト動作により)既存のロガーが
  無効化されてしまい、ログが出力されなくなる。
  そのため、このモジュールでは ita_api_organization / ita_api_admin と同様に
  Flaskのリクエストスコープ変数 `g.applogger` (AppLogのインスタンス) を
  使ってログを出力する。

--------------------------------------------------------------------------
Tool decorator module for the MCP server.

Attaching the @tool decorator to a function in tools/*.py registers it so
that it can be invoked via the MCP "tools/list" and "tools/call" methods.

The @tool decorator lets each tool specify the kind of permission
requirement it has (see libs/permissions.py for details):
  - required_roles : restriction based on the roles in the "Role-Detail" header
  - required_menu  : ITA menu-permission based restriction
  - neither specified : no permission check (callable by anyone)

NOTE about logging:
  If we used the standard `logging.getLogger(__name__)` logger, its output
  would be silently dropped once common_libs.common.logger.AppLog calls
  logging.config.dictConfig(...) on the first request (because
  dictConfig's default `disable_existing_loggers` behavior disables loggers
  created before it runs). Therefore, just like ita_api_organization /
  ita_api_admin, this module logs through the Flask request-scoped
  `g.applogger` (an AppLog instance) instead.
"""
from flask import g

from .permissions import check_tool_call_permission

# ツールレジストリ: デコレーターで登録されたツールの情報を保持する辞書
# Tool registry: dict holding metadata for every tool registered via the decorator
TOOL_REGISTRY = {}


def tool(name: str, description: str, input_schema: dict = None, enabled: bool = True,
         required_roles=None, required_menu=None):
    """
    MCPツールをメタデータとともに登録するデコレーター

    Decorator that registers an MCP tool together with its metadata.

    Parameters:
        name (str): ツール名 / tool name
        description (str): ツールの説明 / tool description
        input_schema (dict, optional): ツールの入力スキーマ(JSON Schema形式)
            / the tool's input schema (JSON Schema format)
        enabled (bool, optional): ツールの有効/無効状態(デフォルト: True)
            / whether the tool is enabled (default: True)
        required_roles (str | list[str], optional): このツールの実行に
            必要なロール(正規表現)。文字列1つ、または文字列の
            リスト(複数指定時はいずれか1つを満たせばよい)で指定する。
            各ロールは正規表現として扱われ、"Role-Detail" ヘッダー
            (platform_auth がJWTの resource_access.{organization_id}-workspaces.roles
            から作成するロール一覧)のロールのいずれか1つでもマッチすれば、
            tools/list での表示・tools/call での実行が許可される。
            / the role(s) (regular expressions) required to use this tool.
            May be a single string or a list of strings (when a list is
            given, satisfying any one of them is enough). Each role is
            treated as a regular expression; if any one of the roles in the
            "Role-Detail" header (the role list platform_auth builds from
            the JWT's resource_access.{organization_id}-workspaces.roles)
            matches any one of them, both tools/list visibility and
            tools/call callability are granted.
        required_menu (str | list[str], optional): このツールの表示に必要な
            ITAメニューのmenu_name_rest。文字列1つ、または文字列のリスト
            (複数指定時はいずれか1つのメニュー権限を持っていればよい)で
            指定する。指定した場合、ITAのメニュー一覧API
            ( /api/{organization_id}/workspaces/{workspace_id}/ita/user/menus/ )
            のレスポンスにこのmenu_name_restのいずれか1つでも含まれているか
            どうかで、tools/list での表示可否を判定する(tools/call実行時には
            再チェックしない)。
            / the ITA menu_name_rest(s) required for this tool to be listed.
            May be a single string or a list of strings (when a list is
            given, having access to any one of them is enough). If set,
            tools/list visibility is determined by whether any one of these
            menu_name_rest values is present in the response of ITA's
            menu-list API
            ( /api/{organization_id}/workspaces/{workspace_id}/ita/user/menus/ ).
            Not re-checked when the tool is actually called via tools/call.

    Returns:
        function: デコレートされた関数 / the decorated function

    Usage:
        @tool(
            name="my-tool",
            description="便利な処理を実行する",
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "..."}
                },
                "required": ["param1"]
            },
            required_roles=["mcp-admin", "mcp-.*-manager"]
        )
        def tool_my_tool(arguments: dict, payload: dict) -> dict:
            ...
    """
    def decorator(func):
        # レジストリにツールのメタデータと実処理関数を登録する
        # Register the tool's metadata and its implementation function in the registry
        TOOL_REGISTRY[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema or {"type": "object", "properties": {}},
            "enabled": enabled,
            "required_roles": required_roles,
            "required_menu": required_menu,
            "function": func
        }
        # 元の関数はそのまま返す(呼び出し方法は変えない)
        # Return the original function unchanged (calling convention is preserved)
        return func
    return decorator


def load_dynamic_tools() -> list:
    """
    デコレーターレジストリからツール設定を読み込む

    Load the tool configuration list from the decorator registry.

    Returns:
        list[dict]: ツール設定のリスト
            各要素には name, description, inputSchema, enabled,
            required_roles, required_menu が含まれる
            / list of tool configuration dicts, each containing
            name, description, inputSchema, enabled, required_roles
            and required_menu
    """
    tools = [
        {
            "name": t["name"],
            "description": t["description"],
            "inputSchema": t["inputSchema"],
            "enabled": t["enabled"],
            "required_roles": t["required_roles"],
            "required_menu": t["required_menu"]
        }
        for t in TOOL_REGISTRY.values()
    ]
    return tools


def get_tool_functions() -> dict:
    """
    レジストリから呼び出し可能なツール関数を取得する

    Get the callable tool functions from the registry.

    Returns:
        dict: ツール名をキー、関数オブジェクトを値とする辞書
            / dict mapping tool name -> function object
    """
    functions = {}

    # レジストリに登録済みの全ツールについて、関数オブジェクトを詰め直す
    # For every tool registered so far, collect its function object
    for name, config in TOOL_REGISTRY.items():
        functions[name] = config["function"]

    return functions


def check_tool_permission(tool_name: str, payload: dict) -> bool:
    """
    ツールを実行してよいかどうかを確認する。

    「対象ツールが存在し、有効(enabled)であるか」に加えて、
    required_roles が指定されている場合はロールの条件も確認する
    (required_menu による規制はtools/listでのみ判定するため、ここでは
    再チェックしない)。

    Check whether the given tool is allowed to be executed.

    In addition to checking that the target tool exists and is enabled,
    also checks the role condition when required_roles is set
    (required_menu based restriction is only evaluated in tools/list and is
    intentionally not re-checked here).

    Parameters:
        tool_name (str): ツール名 / tool name
        payload (dict): 呼び出しコンテキスト情報(organization_id, user_idなど)
            / call context information (organization_id, user_id, etc.)

    Returns:
        bool: 実行可能な場合True / True if the tool may be executed

    Raises:
        Exception: ツールが見つからない、無効、またはロールの条件を
            満たさない場合 / if the tool is not found, is disabled, or the
            role condition is not met
    """
    # 登録済みツール一覧から対象ツールの設定を探す
    # Look up the target tool's configuration from the registered tool list
    tools_config = load_dynamic_tools()
    tool_config = next((t for t in tools_config if t["name"] == tool_name), None)

    # 対象ツールがレジストリに存在しない場合はエラー
    # If the tool is not found in the registry, raise an error
    if not tool_config:
        g.applogger.info("Tool not found: {}".format(tool_name))
        raise Exception("Tool '{}' not found".format(tool_name))

    # 対象ツールが無効化されている場合はエラー
    # If the tool has been disabled, raise an error
    if not tool_config.get("enabled", True):
        g.applogger.info("Tool disabled: {}".format(tool_name))
        raise Exception("Tool '{}' is disabled".format(tool_name))

    # ロールによる実行権限を確認する(条件を満たさない場合は例外が発生する)
    # Check the role based execution permission (raises if not satisfied)
    check_tool_call_permission(tool_config)

    # ここまで到達すれば、実行を許可する
    # If we reach this point, allow execution
    g.applogger.debug("Tool authorized: tool={}".format(tool_name))
    return True
