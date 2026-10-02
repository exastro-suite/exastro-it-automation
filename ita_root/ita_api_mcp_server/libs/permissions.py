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
ツール実行権限チェックモジュール

@tool デコレーターで指定された実行権限の種類に応じて、
「tools/list に含めるかどうか(表示可否)」と
「tools/call を実行してよいかどうか(実行可否)」を判定する。

実行権限には次の3種類がある(tool毎に @tool デコレーターの引数で指定する)。
  1. ロールによる規制(required_roles)
     "Role-Detail" ヘッダー(Base64エンコードされた改行区切りのロール一覧。
     platform_auth が JWTの resource_access.{organization_id}-workspaces.roles
     から、organization/workspaceに分割する前の状態で作成したもの)に、
     指定したロールのいずれか1つでも含まれているかどうかで判定する。
     複数のロールを指定できる(いずれか1つを満たせば使用可)ほか、
     各ロールは正規表現として記述でき、ユーザの持つロールのうち
     1つでもその正規表現にマッチすれば使用可となる。
     tools/list での表示可否・tools/call での実行可否の両方をチェックする。
  2. ITAのメニュー権限による規制(required_menu)
     ITAのAPI( /api/{organization_id}/workspaces/{workspace_id}/ita/user/menus/ )
     を呼び出し、指定した menu_name_rest がレスポンスに含まれているかどうかで
     判定する。複数のmenu_name_restを指定できる(いずれか1つのメニュー権限を
     持っていれば表示可)。tools/list での表示可否のみをチェックし、
     tools/call実行時には再チェックしない(要件どおり)。
  3. 権限チェック無し(required_roles, required_menuのいずれも未指定)
     誰でも表示・実行可能。

--------------------------------------------------------------------------
Tool execution permission checking module.

Depending on the kind of permission requirement specified on the @tool
decorator, this module decides whether a tool should be included in
"tools/list" (visibility) and whether "tools/call" may execute it
(callability).

There are three kinds of permission requirements (specified per tool via the
@tool decorator arguments):
  1. Role based restriction (required_roles)
     Checked by looking for at least one of the given roles in the
     "Role-Detail" header (a Base64-encoded, newline-separated list of
     roles; built by platform_auth from the JWT's
     resource_access.{organization_id}-workspaces.roles, before it is split
     into organization/workspace roles).
     Multiple roles may be specified (satisfying any one of them is enough),
     and each role may be written as a regular expression; if any one of the
     user's roles matches any one of the given regular expressions, the tool
     is usable.
     Checked both when listing tools (tools/list) and when calling a tool
     (tools/call).
  2. ITA menu-permission based restriction (required_menu)
     Checked by calling ITA's API
     ( /api/{organization_id}/workspaces/{workspace_id}/ita/user/menus/ )
     and looking for the given menu_name_rest in the response.
     Multiple menu_name_rest values may be specified (having access to any
     one of them is enough to be visible).
     Only checked when listing tools (tools/list); not re-checked when
     calling the tool (tools/call), as specified.
  3. No permission check (neither required_roles nor required_menu is set)
     Visible and callable by anyone.
"""
import base64
import os
import re

import requests
from flask import g, request

from .forward_headers import build_forward_headers


def _decode_role_detail() -> list:
    """
    "Role-Detail" ヘッダーをデコードし、ロール文字列のリストを返す。

    "Role-Detail" は platform_auth の ita_workspace_api_call(function=="mcp"の場合)が、
    JWTの resource_access.{organization_id}-workspaces.roles をそのまま
    (organization/workspaceに分割する前の状態で)"Roles"と同じ形式で
    セットしているヘッダー。

    Decode the "Role-Detail" header and return the list of role strings.

    "Role-Detail" is a header set by platform_auth's ita_workspace_api_call
    (when function == "mcp"), carrying the JWT's
    resource_access.{organization_id}-workspaces.roles as-is
    (before it is split into organization/workspace roles), in the same
    format as "Roles".

    Returns:
        list[str]: ロール文字列のリスト(取得・デコードできない場合は空リスト)
            / list of role strings (empty list if unavailable or invalid)
    """
    role_detail_header = request.headers.get("Role-Detail")

    # ヘッダーが無い場合は空リストを返す(ロールを持たないユーザーとして扱う)
    # If the header is absent, return an empty list (treat as no roles)
    if not role_detail_header:
        return []

    try:
        # "Roles"ヘッダーと同じ形式(Base64エンコード + 改行区切り)でデコードする
        # Decode using the same format as the "Roles" header
        # (Base64-encoded, newline-separated)
        decoded = base64.b64decode(role_detail_header.encode()).decode("utf-8")
    except Exception:
        # デコードできない場合も空リストとして扱う(安全側に倒す)
        # If decoding fails, also treat it as an empty list (fail safe)
        return []

    # 空文字列の要素を除いてリスト化する
    # Split into a list, excluding empty-string elements
    return [role for role in decoded.split("\n") if role]


def has_role(required_roles) -> bool:
    """
    現在のリクエストの "Role-Detail" のいずれかが、指定したロール(正規表現)の
    いずれか1つにマッチするかを判定する。

    required_rolesには文字列(単一ロール)、または文字列のリスト
    (複数ロール、いずれか1つを満たせばよい)を指定できる。各ロールは
    正規表現として扱い、platform_auth の auth_pattern.py と同様に
    "^"+パターン+"$" で完全一致判定する。

    Check whether any of the current request's "Role-Detail" roles matches
    any one of the given roles (regular expressions).

    required_roles may be a single string (one role) or a list of strings
    (multiple roles; satisfying any one is enough). Each role is treated as
    a regular expression and matched with a full-string match
    ("^" + pattern + "$"), the same convention used by platform_auth's
    auth_pattern.py.

    Parameters:
        required_roles (str | list[str]): 判定対象のロール(正規表現)、
            または正規表現のリスト / role (regex), or list of role regexes,
            to check for

    Returns:
        bool: いずれか1つでもマッチすればTrue / True if any one matches
    """
    if not required_roles:
        return False

    # 単一文字列で指定された場合もリストとして扱う
    # Treat a single string the same as a one-element list
    required_role_patterns = required_roles if isinstance(required_roles, list) else [required_roles]

    roles = _decode_role_detail()

    # 指定されたロール(正規表現)のいずれか1つに、ユーザの持つロールの
    # いずれか1つでもマッチすればOKとする
    # If any one of the given role patterns matches any one of the user's
    # roles, permission is granted
    for role_pattern in required_role_patterns:
        role_pattern_re = "^" + role_pattern + "$"
        for role in roles:
            if re.match(role_pattern_re, role):
                return True

    return False


def get_ita_user_menu_name_rests(organization_id: str, workspace_id: str) -> set:
    """
    ITAのAPIを呼び出し、ユーザがアクセス可能なメニューの menu_name_rest 集合を取得する。

    Call ITA's API to fetch the set of menu_name_rest values the user can access.

    Parameters:
        organization_id (str): オーガナイゼーションID / organization id
        workspace_id (str): ワークスペースID / workspace id

    Returns:
        set[str]: アクセス可能な menu_name_rest の集合
            (API呼び出しに失敗した場合は空集合を返す。安全側に倒し、
             メニュー権限が確認できないツールは表示しない)
            / set of accessible menu_name_rest values
            (returns an empty set if the API call fails; fail safe so that a
             tool whose menu permission could not be confirmed is not shown)
    """
    # ITA自身のAPI(ita_api_organization)を呼び出すため、ITA_API_ORAGANIZATION_HOST/PORTを使用する
    # (Exastro Platform APIを呼び出す場合は PLATFORM_API_HOST/PORT を使用するが、
    #  ここではITAのメニュー情報を取得するのでこちらを使用する)
    #
    # Calls ITA's own API (ita_api_organization), so ITA_API_ORAGANIZATION_HOST/PORT
    # is used (PLATFORM_API_HOST/PORT would be used for the Exastro Platform API,
    # but this call fetches ITA menu information, so the ITA host/port is used here)
    ita_api_host = os.getenv("ITA_API_ORAGANIZATION_HOST")
    ita_api_port = os.getenv("ITA_API_ORAGANIZATION_PORT")
    url = "http://{}:{}/api/{}/workspaces/{}/ita/user/menus/".format(
        ita_api_host, ita_api_port, organization_id, workspace_id
    )
    headers = build_forward_headers(method="GET")

    try:
        # ユーザがアクセス可能なメニューグループ・メニューの一覧を取得する
        # Fetch the list of menu groups/menus accessible to the user
        response = requests.get(url, headers=headers)
    except Exception as e:
        g.applogger.error("Failed to call ITA user/menus API: {}".format(e))
        return set()

    # ステータスコードが200以外の場合は、メニュー権限を確認できないため空集合を返す
    # If the status code is not 200, the menu permission cannot be confirmed,
    # so return an empty set
    if response.status_code != 200:
        g.applogger.info("Failed to fetch ITA user menus: {} - {}".format(response.status_code, response.text))
        return set()

    try:
        response_data = response.json().get("data") or {}
    except Exception as e:
        g.applogger.error("Failed to parse ITA user/menus response: {}".format(e))
        return set()

    # レスポンスの menu_groups[].menus[].menu_name_rest を集めて集合にする
    # Collect menu_groups[].menus[].menu_name_rest from the response into a set
    menu_name_rests = set()
    for menu_group in response_data.get("menu_groups") or []:
        for menu in menu_group.get("menus") or []:
            menu_name_rest = menu.get("menu_name_rest")
            if menu_name_rest:
                menu_name_rests.add(menu_name_rest)

    return menu_name_rests


def is_tool_in_profile(tool_config: dict, profile: str) -> bool:
    """
    このツールが指定されたプロファイルで利用可能かどうかを判定する。

    tools/list 呼び出し時のクエリー文字列 `profile` によるツールの絞り込みに
    使用する。profile が指定されていない場合(None・空文字列)は絞り込みを
    行わず常にTrueとする。tool_config["profile"](@toolデコレーターの
    profile引数)が未指定のツールも、絞り込み対象外として常にTrueとする
    (=どのプロファイルでも利用可能)。

    Decide whether this tool is available under the given profile.

    Used to filter tools/list results by the `profile` query string. If
    profile is not specified (None or empty string), no filtering is applied
    and this always returns True. A tool whose tool_config["profile"] (the
    @tool decorator's profile argument) is not set is also excluded from
    filtering and always returns True (i.e. available under every profile).

    Parameters:
        tool_config (dict): ツール設定(TOOL_REGISTRYの値) / tool configuration
        profile (str): クエリー文字列で指定されたプロファイル名
            / the profile name given in the query string

    Returns:
        bool: 利用可能な場合True / True if the tool is available
    """
    if not profile:
        return True

    tool_profiles = tool_config.get("profile")

    if not tool_profiles:
        return True

    # 単一文字列で指定された場合もリストとして扱う
    # Treat a single string the same as a one-element list
    tool_profiles = tool_profiles if isinstance(tool_profiles, list) else [tool_profiles]

    return profile in tool_profiles


def is_tool_visible(tool_config: dict, payload: dict, menu_cache: dict = None) -> bool:
    """
    tools/list にこのツールを含めてよいかどうかを判定する。

    required_roles が指定されている場合は"Role-Detail"を、
    required_menu が指定されている場合はITAのメニュー権限を確認する。
    required_menu は文字列1つ、または文字列のリスト(複数指定時はいずれか
    1つのメニュー権限を持っていればよい)で指定できる。
    どちらも未指定の場合は常に表示可能とする。

    Decide whether this tool should be included in tools/list.

    If required_roles is set, checks "Role-Detail". If required_menu is set,
    checks ITA menu permission. required_menu may be a single string or a
    list of strings (when a list is given, having access to any one of them
    is enough). If neither is set, the tool is always visible.

    Parameters:
        tool_config (dict): ツール設定(TOOL_REGISTRYの値) / tool configuration
        payload (dict): 呼び出しコンテキスト情報(organization_id, workspace_idなど)
            / call context information (organization_id, workspace_id, etc.)
        menu_cache (dict, optional): 1回のtools/list呼び出しの中で
            ITAメニュー情報の取得結果を再利用するためのキャッシュ辞書。
            / cache dict used to reuse the ITA menu information fetched
            within a single tools/list call, avoiding one API call per tool.

    Returns:
        bool: 表示可能な場合True / True if the tool should be visible
    """
    required_roles = tool_config.get("required_roles")
    required_menu = tool_config.get("required_menu")

    if required_roles:
        # 1. ロールによる規制
        # 1. Role based restriction
        return has_role(required_roles)

    if required_menu:
        # 2. ITAのメニュー権限による規制
        # 2. ITA menu-permission based restriction
        organization_id = payload.get("organization_id")
        workspace_id = payload.get("workspace_id")
        cache_key = (organization_id, workspace_id)

        if menu_cache is None:
            menu_cache = {}

        # 同じorganization_id/workspace_idであれば、1回のtools/list処理内で
        # メニュー一覧APIを呼び出すのは1回だけにする
        # For the same organization_id/workspace_id, call the menu-list API
        # at most once within a single tools/list call
        if cache_key not in menu_cache:
            menu_cache[cache_key] = get_ita_user_menu_name_rests(organization_id, workspace_id)

        # 単一文字列で指定された場合もリストとして扱う
        # Treat a single string the same as a one-element list
        required_menus = required_menu if isinstance(required_menu, list) else [required_menu]
        accessible_menu_name_rests = menu_cache[cache_key]

        # 指定されたメニューのいずれか1つでもアクセス可能であれば表示可能とする
        # If the user has access to any one of the specified menus, the tool is visible
        return any(menu in accessible_menu_name_rests for menu in required_menus)

    # 3. 権限チェック無し
    # 3. No permission check
    return True


def check_tool_call_permission(tool_config: dict) -> None:
    """
    tools/call でこのツールを実行してよいかどうかを判定する。

    required_roles が指定されている場合のみチェックする。
    required_menu による規制は tools/list でのみ判定し、
    tools/call実行時には再チェックしない(要件どおり)。

    Decide whether this tool may be executed via tools/call.

    Only required_roles is checked here. required_menu based restriction
    is only evaluated in tools/list and is intentionally not re-checked here.

    Parameters:
        tool_config (dict): ツール設定(TOOL_REGISTRYの値) / tool configuration

    Raises:
        Exception: ロールの条件を満たさない場合
            (エラーメッセージには、必要なロール名などの詳細は含めず、
             権限が不足している旨のみを返す。詳細はログにのみ出力する)
            / if the role condition is not met
            (the exception message does not include details such as the
             required role names; it only states that permission is
             insufficient. The details are logged server-side only)
    """
    required_roles = tool_config.get("required_roles")

    if required_roles and not has_role(required_roles):
        # 必要なロール名などの詳細はログにのみ出力し、呼び出し元(MCPクライアント)には
        # 権限不足である旨だけを返す(必要なロール名を教えない)
        # Log the details (required roles) server-side only; return only a
        # generic "insufficient permission" message to the caller (MCP
        # client), without revealing the required role names
        g.applogger.info(
            "Permission denied: tool={}, required_roles={}".format(tool_config.get("name"), required_roles)
        )
        raise Exception("Permission denied: insufficient permission to call tool '{}'".format(tool_config.get("name")))
