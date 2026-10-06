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
ITAパラメータシート作成ツール ("create-menu" / "update-menu" / "get-menu-definition")

指定したパラメータシート(メニュー)定義を元に、パラメータシートの新規作成・
更新・定義情報の取得を行うツール。呼び出し先のITAのAPI(
/api/{organization_id}/workspaces/{workspace_id}/ita/create/define/execute/
および /api/{organization_id}/workspaces/{workspace_id}/ita/create/define/
{menu_create}/ )は、いずれも「パラメータシート定義・作成」メニュー
(menu_name_rest: menu_definition_and_creation)へのロール権限が必要な操作
であるため(ita_api_organizationのcontrollers/menu_create_controller.py の
define_and_execute_menu_create / get_exist_menu_create_data が
check_auth_menu('menu_definition_and_creation') を実行している)、@tool
デコレーターの required_menu に同じmenu_name_restを指定し、このメニューに
アクセスできないユーザーには tools/list に表示しないようにする。

  - create-menu         : menu_definition(パラメータシート定義)を受け取り、
    新規のパラメータシートを作成する。
  - update-menu         : menu_definition(パラメータシート定義。更新対象を
    示すmenu_create_idを含む)を受け取り、既存のパラメータシートを更新する。
  - get-menu-definition : menu_rest_name(パラメータシートのREST名)を受け取り、
    既存のパラメータシートの定義情報(menu・column)を取得する。update-menuの
    実行前に、現在の定義を取得するために使用する。

menu_definition.menu.role_list(このパラメータシートにアクセスできるロール名の
リスト)について:
  - create-menuでは任意項目、update-menuでは必須項目とする(update-menuは
    get-menu-definitionで取得した既存の値をそのまま渡す運用を想定している
    ため)。
  - 指定された場合はその値をそのままAPIに渡す。
  - create-menuで指定が無い場合は、次の方法で自動的に設定する
    (_resolve_default_role_list関数):

    作成者本人の指定workspaceにおける権限 + ワークスペース管理者にアクセス権を付与する

    1. Exastro PlatformのAPI(
       /api/{organization_id}/platform/roles?kind=workspace )を呼び出し、
       ロール一覧(name・workspaces[].id)を取得する。
    2. 呼び出しユーザーの"Roles"ヘッダー(Base64エンコード・改行区切りの
       ロール名一覧)に含まれ、かつworkspacesにこのworkspace_idを含む
       ロールのnameを対象とする。
    3. 2.の結果に "_{workspace_id}-admin" が含まれていなければ、必ず追加する。

--------------------------------------------------------------------------
ITA parameter-sheet creation tools ("create-menu" / "update-menu" / "get-menu-definition")

Creates, updates, or fetches the definition of a parameter sheet (menu) from
the given menu definition. The downstream ITA APIs called here (
/api/{organization_id}/workspaces/{workspace_id}/ita/create/define/execute/
and /api/{organization_id}/workspaces/{workspace_id}/ita/create/define/
{menu_create}/ ) both require role permission on the "Parameter sheet
definition and creation" menu (menu_name_rest: menu_definition_and_creation)
— see define_and_execute_menu_create / get_exist_menu_create_data in
ita_api_organization's controllers/menu_create_controller.py, which call
check_auth_menu('menu_definition_and_creation'). Accordingly, the @tool
decorator's required_menu is set to that same menu_name_rest for all three
tools, so that tools/list hides them from users who cannot access that menu.

  - create-menu         : accepts menu_definition (the parameter sheet
    definition) and creates a new parameter sheet.
  - update-menu         : accepts menu_definition (the parameter sheet
    definition, including menu_create_id identifying the target to update)
    and updates an existing parameter sheet.
  - get-menu-definition : accepts menu_rest_name (the parameter sheet's REST
    name) and fetches the existing parameter sheet's definition (menu and
    column). Used to fetch the current definition before calling update-menu.

About menu_definition.menu.role_list (the list of role names allowed to
access this parameter sheet):
  - Optional for create-menu, required for update-menu (update-menu is
    expected to be called with the existing value as fetched via
    get-menu-definition).
  - When given, it is passed to the API as-is.
  - When omitted (create-menu only), it is determined automatically (see
    _resolve_default_role_list):

    the creator's own permissions on the specified workspace, plus granting
    access to the workspace admin role.

    1. Call the Exastro Platform API (
       /api/{organization_id}/platform/roles?kind=workspace ) to fetch the
       role list (name / workspaces[].id).
    2. Keep the roles whose name is present in the calling user's "Roles"
       header (a Base64-encoded, newline-separated list of role names) and
       whose workspaces include this workspace_id.
    3. Always ensure "_{workspace_id}-admin" is included, adding it if the
       result of step 2 does not already contain it.
"""
import base64
import os
import re

import requests
from flask import g, request

from libs import tool, HTTPException, build_forward_headers, get_downstream_timeout

# 権限チェック対象のメニュー(「パラメータシート定義・作成」)のmenu_name_rest
# menu_name_rest of the permission-gating menu ("Parameter sheet definition and creation")
_REQUIRED_MENU = "menu_definition_and_creation"


@tool(
    name="create-menu",
    description="Create a new parameter sheet (menu) with the specified definition. For details, Please refer to `tool-reference/create-menu.md` using `get-document`.",
    input_schema={
        "type": "object",
        "properties": {
            "menu_definition": {
                "type": "object",
                "description": "Parameter sheet definition.",
                "properties": {
                    "column": {
                        "type": "object",
                        "description": "patternProperties is `c` followed by a sequential number starting from 1."
                    },
                    "menu": {
                        "type": "object",
                        "description": "Minimum parameters for menu definition.",
                        "properties": {
                            "menu_name": {"type": "string", "description": "Menu display name."},
                            "menu_name_rest": {"type": "string", "description": "Menu name for REST API."},
                            "description": {"type": "string", "description": "Menu description."},
                            "hostgroup": {"type": "string", "enum": ["0", "1"], "description": "Whether to use host group (0: No, 1: Yes)."},
                            "vertical": {"type": "string", "enum": ["0", "1"], "description": "Bundle-format parameter sheet (0: No, 1: Yes)."},
                            "role_list": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of role names allowed to access this menu. Optional; auto-determined if omitted."
                            }
                        },
                        "required": ["menu_name", "menu_name_rest", "description", "hostgroup"]
                    }
                },
                "required": ["menu", "column"]
            }
        },
        "required": ["menu_definition"]
    },
    required_menu=_REQUIRED_MENU,
    profile=["AgenticAI"]
)
def tool_create_menu(arguments: dict, payload: dict) -> dict:
    """
    パラメータシート定義および新規作成を実行する

    Create a new parameter sheet from the given definition.

    Parameters:
        arguments (dict): ツールの引数
            - menu_definition (dict): パラメータシート定義用パラメータ
              / the parameter sheet definition
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Returns:
        dict: メニュー作成結果
            - result: APIレスポンスの作成されたメニュー情報 / the menu info returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Raises:
        Exception: menu_definitionが不正な場合 / if menu_definition is invalid
        HTTPException: メニューの作成に失敗した場合 / if creating the menu fails
    """
    return _register_menu(arguments, payload, new=True)


@tool(
    name="update-menu",
    description="Update the existing parameter sheet (menu) using the specified definition. Please retrieve the definition prior to the update using `get-menu-definition`. , Please refer to `tool-reference/update-menu.md` using `get-document`.",
    input_schema={
        "type": "object",
        "properties": {
            "menu_definition": {
                "type": "object",
                "description": "Parameter sheet definition.",
                "properties": {
                    "column": {
                        "type": "object",
                        "description": "patternProperties is `c` followed by a sequential number starting from 1."
                    },
                    "menu": {
                        "type": "object",
                        "description": "Minimum parameters for menu definition.",
                        "properties": {
                            "menu_create_id": {"type": "string", "description": "Specify the UUID of the menu to update."},
                            "menu_name": {"type": "string", "description": "Menu display name."},
                            "menu_name_rest": {"type": "string", "description": "Menu name for REST API."},
                            "description": {"type": "string", "description": "Menu description."},
                            "hostgroup": {"type": "string", "enum": ["0", "1"], "description": "Whether to use host group (0: No, 1: Yes)."},
                            "vertical": {"type": "string", "enum": ["0", "1"], "description": "Bundle-format parameter sheet (0: No, 1: Yes)."},
                            "role_list": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of role names allowed to access this menu. Required; pass the value currently registered (see get-menu-definition)."
                            }
                        },
                        "required": ["menu_create_id", "menu_name", "menu_name_rest", "description", "hostgroup", "role_list"]
                    }
                },
                "required": ["menu", "column"]
            }
        },
        "required": ["menu_definition"]
    },
    required_menu=_REQUIRED_MENU,
    profile=["AgenticAI"]
)
def tool_update_menu(arguments: dict, payload: dict) -> dict:
    """
    パラメータシート定義および更新を実行する

    Update an existing parameter sheet from the given definition.

    Parameters:
        arguments (dict): ツールの引数
            - menu_definition (dict): パラメータシート定義用パラメータ
              (更新対象を示すmenu_create_idを含む) / the parameter sheet
              definition (including menu_create_id identifying the target to update)
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Returns:
        dict: メニュー更新結果
            - result: APIレスポンスの更新されたメニュー情報 / the menu info returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Raises:
        Exception: menu_definitionが不正な場合 / if menu_definition is invalid
        HTTPException: メニューの更新に失敗した場合 / if updating the menu fails
    """
    return _register_menu(arguments, payload, new=False)


def _register_menu(arguments: dict, payload: dict, new: bool) -> dict:
    """
    パラメータシート定義を組み立て、作成/更新APIを呼び出す

    Build a parameter sheet definition and call the create/update API.

    Parameters:
        arguments (dict): ツールの引数
            - menu_definition (dict): パラメータシート定義用パラメータ
              / the parameter sheet definition
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
        new (bool): 新規作成の場合True、更新の場合False
            / True when creating a new menu, False when updating an existing one

    Returns:
        dict: メニュー作成/更新結果
            - result: APIレスポンスの作成/更新されたメニュー情報
              / the menu info returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Raises:
        Exception: menu_definitionが不正な場合 / if menu_definition is invalid
        HTTPException: メニューの作成/更新に失敗した場合 / if the create/update call fails
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")

    # menuのパラメータ設定
    # Default values for the "menu" fields
    default_menu_definition_menu_fields = {
        "create_menu_id": None,
        "sheet_type_id": "1",
        "remarks": "",
        "display_order": "1",
        "unique_constraint": None,
        "menu_group_for_input": "Input",
        "menu_group_for_input_id": "502",
    }

    menu_definition = arguments.get("menu_definition", {})
    if not isinstance(menu_definition, dict):
        raise Exception("menu_definition must be an object")

    menu_definition["group"] = {}
    menu_definition["menu"] = default_menu_definition_menu_fields | menu_definition.get("menu", {})

    g.applogger.info(f'Parameter menu_name={menu_definition["menu"].get("menu_name")} menu_name_rest={menu_definition["menu"].get("menu_name_rest")}')

    # role_listの解決。update-menuでは必須項目とし、未指定ならエラーとする。
    # create-menuでは未指定の場合に自動設定する。
    # Resolve role_list. It is required for update-menu (raise if missing).
    # For create-menu, auto-determine it when omitted.
    role_list = menu_definition["menu"].get("role_list")
    if not new and not role_list:
        raise Exception("menu_definition.menu.role_list is required for update-menu")
    if not role_list:
        role_list = _resolve_default_role_list(organization_id, workspace_id)
    menu_definition["menu"]["role_list"] = role_list

    menu_definition["menu"]["columns"] = list(menu_definition.get("column", {}).keys())
    menu_definition["type"] = "create_new" if new else "edit"

    # sheet_type_idに応じてmenuのパラメータを追加
    # Add extra "menu" fields depending on sheet_type_id
    if menu_definition["menu"].get("sheet_type_id") == "1":
        menu_definition["menu"]["sheet_type"] = "Parameter Sheet(Host/Operation)"
        menu_definition["menu"] = {
            "hostgroup": "0",
            "vertical": "0",
            "menu_group_for_subst": "Substitution value",
            "menu_group_for_subst_id": "503",
            "menu_group_for_ref": "Reference",
            "menu_group_for_ref_id": "504",
        } | menu_definition["menu"]
    elif menu_definition["menu"].get("sheet_type_id") == "2":
        menu_definition["menu"]["sheet_type"] = "Data Sheet"

    elif menu_definition["menu"].get("sheet_type_id") == "3":
        menu_definition["menu"]["sheet_type"] = "Parameter Sheet(Operation)"
        menu_definition["menu"] = {
            "vertical": "0",
            "menu_group_for_subst": "Substitution value",
            "menu_group_for_subst_id": "503",
            "menu_group_for_ref": "Reference",
            "menu_group_for_ref_id": "504",
        } | menu_definition["menu"]

    # columnのパラメータ設定
    # Build the "column" fields
    display_order = 0
    column_definitions = {}

    for column_key, column_definition in sorted(menu_definition.get("column", {}).items(), key=_column_dict_key_sort):
        column_definition = {
            "required": "0",
            "unique": "0",
            "description": "",
            "remarks": "",
            "column_group": None,
            "display_order": display_order,
            "column_group_id": None,
            "create_column_id": None
        } | column_definition

        if column_definition.get("column_class") == "SingleTextColumn":
            column_definition["column_class_id"] = "1"
            column_definition = {
                "single_string_maximum_bytes": "256",
                "single_string_regular_expression": "",
                "single_string_default_value": ""
            } | column_definition

        elif column_definition.get("column_class") == "MultiTextColumn":
            column_definition["column_class_id"] = "2"
            column_definition = {
                "multi_string_maximum_bytes": "4096",
                "multi_string_regular_expression": "",
                "multi_string_default_value": ""
            } | column_definition

        elif column_definition.get("column_class") == "NumColumn":
            column_definition["column_class_id"] = "3"
            column_definition = {
                "integer_minimum_value": "",
                "integer_maximum_value": "",
                "integer_default_value": ""
            } | column_definition

        elif column_definition.get("column_class") == "FloatColumn":
            column_definition["column_class_id"] = "4"
            column_definition = {
                "decimal_minimum_value": "",
                "decimal_maximum_value": "",
                "decimal_digit": "",
                "decimal_default_value": ""
            } | column_definition

        elif column_definition.get("column_class") == "DateTimeColumn":
            column_definition["column_class_id"] = "5"
            column_definition = {
                "datetime_default_value": ""
            } | column_definition

        elif column_definition.get("column_class") == "DateColumn":
            column_definition["column_class_id"] = "6"
            column_definition = {
                "date_default_value": ""
            } | column_definition

        elif column_definition.get("column_class") == "IDColumn":
            column_definition["column_class_id"] = "7"
            column_definition["pulldown_selection_id"] = {
                "Parameter sheet create:Selection 1:*-(blank)": "5011008",
                "Parameter sheet create:Selection 2:Yes-No": "5011009",
                "Parameter sheet create:Selection 2:True-False": "5011010"
            }.get(column_definition.get("pulldown_selection", ""), "")

            column_definition = {
                "pulldown_selection_default_value": "",
                "reference_item": "",
            } | column_definition

        elif column_definition.get("column_class") == "PasswordColumn":
            column_definition["column_class_id"] = "8"
            column_definition = {
                "password_maximum_bytes": "1024",
            } | column_definition

        elif column_definition.get("column_class") == "FileUploadColumn":
            column_definition["column_class_id"] = "9"
            column_definition = {
                "file_upload_maximum_bytes": "1024000",
            } | column_definition

        column_definitions[column_key] = column_definition
        display_order += 1

    menu_definition["column"] = column_definitions

    # このツールが呼び出すのは "/ita/create/define/execute/" というITA自身のAPI
    # (ita_api_organization)側のエンドポイントであるため、環境変数
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT を使用する
    #
    # This tool calls the "/ita/create/define/execute/" endpoint of ITA's own
    # API (ita_api_organization), so it uses the ITA_API_ORAGANIZATION_HOST /
    # ITA_API_ORAGANIZATION_PORT environment variables
    ita_api_host = os.getenv("ITA_API_ORAGANIZATION_HOST")
    ita_api_port = os.getenv("ITA_API_ORAGANIZATION_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/workspaces/{}/ita/create/define/execute/".format(
        ita_api_host, ita_api_port, organization_id, workspace_id
    )

    # 転送用ヘッダーを組み立てる(POSTでボディを送るため"Content-Type"も付与する)
    # Build the headers to forward (also adds "Content-Type" since this is a POST with a body)
    headers = build_forward_headers(method="POST")

    # ITAのAPIへメニュー作成/更新のPOSTリクエストを送信する
    # Send a POST request to ITA's API to create/update the menu
    req = requests.post(url, json=menu_definition, headers=headers, timeout=get_downstream_timeout())

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        tool_name = "create-menu" if new else "update-menu"
        g.applogger.info("Failed to {} menu: {} - {}".format(
            "create" if new else "update", req.status_code, req.text
        ))
        raise HTTPException(tool_name, req)

    # 正常時はAPIのレスポンスをそのまま結果として返す
    # On success, return the API response as the result
    return {
        "result": req.json(),
        "message": "Menu created successfully." if new else "Menu updated successfully.",
        "organization_id": organization_id,
        "workspace_id": workspace_id
    }


def _decode_roles_header() -> list:
    """
    "Roles" ヘッダーをデコードし、ロール文字列のリストを返す。

    Decode the "Roles" header and return the list of role strings.

    Returns:
        list[str]: ロール文字列のリスト(取得・デコードできない場合は空リスト)
            / list of role strings (empty list if unavailable or invalid)
    """
    roles_header = request.headers.get("Roles")

    if not roles_header:
        return []

    try:
        decoded = base64.b64decode(roles_header.encode()).decode("utf-8")
    except Exception:
        return []

    return [role for role in decoded.split("\n") if role]


def _resolve_default_role_list(organization_id: str, workspace_id: str) -> list:
    """
    role_list未指定時に自動的に設定するロール一覧を組み立てる

    Build the role list to use automatically when role_list is not specified.

    Exastro PlatformのAPI(/platform/roles?kind=workspace)から取得したロール
    一覧のうち、呼び出しユーザーが持つロール("Roles"ヘッダー)かつ、この
    workspace_idにアクセス可能なロールのnameを対象とする。加えて、
    "_{workspace_id}-admin" が含まれていなければ必ず追加する。

    Of the role list fetched from the Exastro Platform API
    (/platform/roles?kind=workspace), keep the names of the roles that the
    calling user holds (the "Roles" header) and that can access this
    workspace_id. In addition, always ensure "_{workspace_id}-admin" is
    included, adding it if missing.

    Parameters:
        organization_id (str): オーガナイゼーションID / organization id
        workspace_id (str): ワークスペースID / workspace id

    Returns:
        list[str]: 自動設定されたロール名のリスト / the automatically determined list of role names

    Raises:
        HTTPException: ロール一覧の取得に失敗した場合 / if fetching the role list fails
    """
    # このAPIが呼び出すのは "/platform/roles" というExastro Platform API側の
    # エンドポイントであるため、環境変数 PLATFORM_API_HOST / PLATFORM_API_PORT を使用する
    #
    # This calls the "/platform/roles" endpoint of the Exastro Platform API,
    # so it uses the PLATFORM_API_HOST / PLATFORM_API_PORT environment variables
    platform_api_host = os.getenv("PLATFORM_API_HOST")
    platform_api_port = os.getenv("PLATFORM_API_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/platform/roles".format(platform_api_host, platform_api_port, organization_id)

    headers = build_forward_headers(method="GET")

    req = requests.get(url, headers=headers, params={"kind": "workspace"}, timeout=get_downstream_timeout())
    if req.status_code != 200:
        g.applogger.info("Failed to fetch platform roles: {} - {}".format(req.status_code, req.text))
        raise HTTPException("create-menu", req)

    roles_data = req.json().get("data") or []
    user_roles = set(_decode_roles_header())

    # ユーザーが持つロールのうち、このworkspace_idにアクセス可能なものを抽出する
    # Keep the roles the user holds that can access this workspace_id
    role_list = []
    for role in roles_data:
        role_name = role.get("name")
        if not role_name or role_name not in user_roles:
            continue

        workspace_ids = {ws.get("id") for ws in (role.get("workspaces") or [])}
        if workspace_id in workspace_ids:
            role_list.append(role_name)

    # "_{workspace_id}-admin" が含まれていなければ必ず追加する
    # Always ensure "_{workspace_id}-admin" is included
    admin_role = "_{}-admin".format(workspace_id)
    if admin_role not in role_list:
        role_list.append(admin_role)

    return role_list


def _column_dict_key_sort(item):
    """
    columnのdictをkeyでソートするための関数

    Sort key function used to sort the "column" dict by key.

    "c" に続く連番のキー(例: c1, c2, ...)は数値としてその順序で並べ、
    それ以外のキーは文字列としてその後に並べる。

    Keys of the form "c" followed by a sequential number (e.g. c1, c2, ...)
    are ordered numerically, and any other keys are ordered as strings after
    those.

    Parameters:
        item (tuple): ソート対象のキーと値のタプル / (key, value) tuple to sort

    Returns:
        tuple: ソート用のキー / the sort key
    """
    key = item[0]
    if re.fullmatch(r"c\d+", key):
        return (0, int(key[1:]))
    else:
        return (1, key)


@tool(
    name="get-menu-definition",
    description="Get the definition information for the parameter sheet (menu).",
    input_schema={
        "type": "object",
        "properties": {
            "menu_rest_name": {"type": "string", "description": "Parameter sheet's REST name (menu_name_rest)."},
        },
        "required": ["menu_rest_name"]
    },
    required_menu=_REQUIRED_MENU,
    profile=["AgenticAI"]
)
def tool_get_menu_definition(arguments: dict, payload: dict) -> dict:
    """
    パラメータシート定義情報を取得する

    Get the definition information for a parameter sheet (menu).

    Parameters:
        arguments (dict): ツールの引数
            - menu_rest_name (str): パラメータシートのREST名(menu_name_rest)
              / the parameter sheet's REST name (menu_name_rest)
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Returns:
        dict: メニュー定義情報取得結果
            - result: 取得したメニュー定義情報(menu_definition.menu / menu_definition.column)
              / the fetched menu definition (menu_definition.menu / menu_definition.column)
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Raises:
        Exception: menu_rest_nameが指定されていない場合 / if menu_rest_name is not specified
        HTTPException: メニュー定義情報の取得に失敗した場合 / if fetching the menu definition fails
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")
    menu_rest_name = arguments.get("menu_rest_name", "")

    if not menu_rest_name:
        raise Exception("menu_rest_name is required")

    g.applogger.info(f'Parameter menu_rest_name={menu_rest_name}')

    # このツールが呼び出すのは "/ita/create/define/{menu_create}/" というITA自身のAPI
    # (ita_api_organization)側のエンドポイントであるため、環境変数
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT を使用する
    #
    # This tool calls the "/ita/create/define/{menu_create}/" endpoint of
    # ITA's own API (ita_api_organization), so it uses the
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT environment
    # variables
    ita_api_host = os.getenv("ITA_API_ORAGANIZATION_HOST")
    ita_api_port = os.getenv("ITA_API_ORAGANIZATION_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/workspaces/{}/ita/create/define/{}/".format(
        ita_api_host, ita_api_port, organization_id, workspace_id, menu_rest_name
    )

    # 転送用ヘッダーを組み立てる
    # Build the headers to forward
    headers = build_forward_headers(method="GET")

    # ITAのAPIへメニュー定義情報取得のGETリクエストを送信する
    # Send a GET request to ITA's API to fetch the menu definition
    req = requests.get(url, headers=headers, timeout=get_downstream_timeout())

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        g.applogger.info("Failed to get menu definition: {} - {}".format(req.status_code, req.text))
        raise HTTPException("get-menu-definition", req)

    menu_info = req.json().get("data", {}).get("menu_info", {})
    result = {
        "menu_definition": {
            "menu": menu_info.get("menu", {}),
            "column": menu_info.get("column", {})
        }
    }

    # columnsは作成/更新APIへの入力には不要な内部項目のため取り除く
    # columns are internal fields not needed as input to the
    # create/update API, so they are removed
    result["menu_definition"]["menu"].pop("columns", None)

    return {
        "result": result,
        "message": "Menu definition fetched successfully.",
        "organization_id": organization_id,
        "workspace_id": workspace_id
    }
