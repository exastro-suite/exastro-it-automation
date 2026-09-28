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
ITAドライバー実行ツール ("execute-driver" / "dry-run-driver" / "get-driver-status")

Ansible用のパラメータシート(Movement/Operation)に対して、ドライバー作業の
実行・ドライラン実行の開始、および実行状態の取得を行うツール。

  - execute-driver     : menu(メニュー名)・movement_name・operation_name・
    schedule_date(任意)を受け取り、ドライバー作業の実行を開始する。
  - dry-run-driver     : execute-driverと同じ引数を受け取り、ドライランモード
    (AnsibleDriverの場合はDryRun)でドライバー作業の実行を開始する。
  - get-driver-status  : menu(メニュー名)・execution_no(実行No)を受け取り、
    ドライバー作業実行の状態を取得する。

呼び出し先のITAのAPI(ita_api_organization)は、いずれも受け取った
menu(URLパスパラメータ)そのものに対してメニュー権限をチェックしている
(controllers/driver_controll_controller.py の各関数が
libs/organization_common.py の check_auth_menu(menu, objdbca) を実行している)
ため、実際にどのmenu_name_restへのアクセス権限が必要かは、そのAPIを
呼び出す際に指定するmenuの値によって決まる。

  - execute-driver / dry-run-driver
    それぞれ post_driver_excecute (driver_controll_controller.py:378) /
    post_driver_execute_dry_run (同ファイル:613) が check_auth_menu(menu, ...)
    を実行している。これらのAPIにAnsible用のmenuとして指定可能な
    menu_name_restは execution_ansible_legacy / execution_ansible_pioneer /
    execution_ansible_role の3つであるため、@tool デコレーターの
    required_menu にこの3つを列挙し、いずれか1つのメニューにアクセス
    できるユーザーであれば tools/list に表示する。
  - get-driver-status
    get_driver_execute_data (同ファイル:41) が check_auth_menu(menu, ...) を
    実行している。このAPIにAnsible用のmenuとして指定可能なmenu_name_restは、
    実行結果の状態確認用メニューである check_operation_status_ansible_legacy /
    check_operation_status_ansible_pioneer / check_operation_status_ansible_role
    の3つ(同関数内のtarget辞書のキー、行72-80)であるため、@tool デコレーターの
    required_menu にはこちらの3つを列挙する。

--------------------------------------------------------------------------
ITA driver execution tools ("execute-driver" / "dry-run-driver" / "get-driver-status")

Starts a driver-execution / dry-run job, and fetches its execution status,
against a parameter sheet (Movement/Operation) for the Ansible drivers.

  - execute-driver    : accepts menu (menu name), movement_name,
    operation_name and schedule_date (optional), and starts a driver
    execution job.
  - dry-run-driver     : accepts the same arguments as execute-driver, and
    starts a driver execution job in dry-run mode (DryRun for the Ansible
    drivers).
  - get-driver-status : accepts menu (menu name) and execution_no
    (execution number), and fetches the status of a driver execution job.

The downstream ITA API (ita_api_organization) checks menu permission against
the `menu` value itself (a URL path parameter) for all of these endpoints
(each handler function in controllers/driver_controll_controller.py calls
check_auth_menu(menu, objdbca) from libs/organization_common.py), so which
menu_name_rest actually needs to be accessible depends on the value of
`menu` passed to that API call.

  - execute-driver / dry-run-driver
    post_driver_excecute (driver_controll_controller.py:378) and
    post_driver_execute_dry_run (same file:613) respectively call
    check_auth_menu(menu, ...). The menu_name_rest values that may be passed
    as the Ansible `menu` for these APIs are execution_ansible_legacy,
    execution_ansible_pioneer and execution_ansible_role, so the @tool
    decorator's required_menu lists these three, making the tool visible in
    tools/list to any user who can access at least one of them.
  - get-driver-status
    get_driver_execute_data (same file:41) also calls check_auth_menu(menu, ...).
    The menu_name_rest values that may be passed as the Ansible `menu` for
    this API are instead the corresponding status-check menus:
    check_operation_status_ansible_legacy,
    check_operation_status_ansible_pioneer and
    check_operation_status_ansible_role (the keys of the `target` dict in
    that same function, lines 72-80), so the @tool decorator's required_menu
    lists these three instead.
"""
import os

import requests
from flask import g

from libs import tool, HTTPException, build_forward_headers

# execute-driver / dry-run-driverが対象とするAnsible用menuのmenu_name_rest
# menu_name_rest values of the Ansible menus targeted by execute-driver / dry-run-driver
_REQUIRED_MENU_EXECUTE = [
    "execution_ansible_legacy",
    "execution_ansible_pioneer",
    "execution_ansible_role",
]

# get-driver-statusが対象とする、状態確認用menuのmenu_name_rest
# menu_name_rest values of the status-check menus targeted by get-driver-status
_REQUIRED_MENU_STATUS = [
    "check_operation_status_ansible_legacy",
    "check_operation_status_ansible_pioneer",
    "check_operation_status_ansible_role",
]


def _build_execute_data(arguments: dict) -> dict:
    """
    ドライバー実行/ドライラン実行APIへ送信するリクエストボディを組み立てる

    Build the request body sent to the driver execute / dry-run execute API.

    Parameters:
        arguments (dict): ツールの引数
            - movement_name (str): 実行するMovement名 / movement name to execute
            - operation_name (str): 実行するOperation名 / operation name to execute
            - schedule_date (str, optional): スケジュール日時
              (形式: YYYY/MM/DD hh:mm) / schedule date and time (format: YYYY/MM/DD hh:mm)

    Returns:
        dict: リクエストボディ / the request body
    """
    execute_data = {
        "movement_name": arguments.get("movement_name", ""),
        "operation_name": arguments.get("operation_name", "")
    }

    # schedule_dateがある場合のみ追加
    # Only add schedule_date when it is given
    if arguments.get("schedule_date"):
        execute_data["schedule_date"] = arguments["schedule_date"]

    return execute_data


_EXECUTE_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "menu": {
            "type": "string",
            "description": "Menu name (REST name)"
        },
        "movement_name": {
            "type": "string",
            "description": "Movement name to execute"
        },
        "operation_name": {
            "type": "string",
            "description": "Operation name to execute"
        },
        "schedule_date": {
            "type": "string",
            "description": "Schedule date and time (format: YYYY/MM/DD hh:mm). Optional."
        }
    },
    "required": ["menu", "movement_name", "operation_name"]
}


@tool(
    name="execute-driver",
    description="Start executing ITA driver operation with specified movement and operation.",
    input_schema=_EXECUTE_INPUT_SCHEMA,
    required_menu=_REQUIRED_MENU_EXECUTE
)
def tool_execute_driver(arguments: dict, payload: dict) -> dict:
    """
    ITAドライバー作業の実行を開始する

    Start executing an ITA driver operation.

    Parameters:
        arguments (dict): ツールの引数
            - menu (str): メニュー名(REST名) / menu name (REST name)
            - movement_name (str): 実行するMovement名 / movement name to execute
            - operation_name (str): 実行するOperation名 / operation name to execute
            - schedule_date (str, optional): スケジュール日時
              (形式: YYYY/MM/DD hh:mm) / schedule date and time (format: YYYY/MM/DD hh:mm)
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Returns:
        dict: ドライバー実行結果
            - result: APIレスポンスの実行情報 / the execution info returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
            - menu (str): メニュー名 / menu name

    Raises:
        Exception: menuが指定されていない場合 / if menu is not specified
        HTTPException: ドライバー実行の開始に失敗した場合 / if starting the driver execution fails
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")
    menu = arguments.get("menu", "")

    if not menu:
        raise Exception("menu is required")

    execute_data = _build_execute_data(arguments)
    g.applogger.info(f"Parameter {execute_data}")

    # このツールが呼び出すのは "/ita/menu/{menu}/driver/execute/" というITA自身のAPI
    # (ita_api_organization)側のエンドポイントであるため、環境変数
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT を使用する
    #
    # This tool calls the "/ita/menu/{menu}/driver/execute/" endpoint of ITA's
    # own API (ita_api_organization), so it uses the
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT environment
    # variables
    ita_api_host = os.getenv("ITA_API_ORAGANIZATION_HOST")
    ita_api_port = os.getenv("ITA_API_ORAGANIZATION_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/{}/driver/execute/".format(
        ita_api_host, ita_api_port, organization_id, workspace_id, menu
    )

    # 転送用ヘッダーを組み立てる(POSTでボディを送るため"Content-Type"も付与する)
    # Build the headers to forward (also adds "Content-Type" since this is a POST with a body)
    headers = build_forward_headers(method="POST")

    # ITAのAPIへドライバー実行開始のPOSTリクエストを送信する
    # Send a POST request to ITA's API to start the driver execution
    req = requests.post(url, json=execute_data, headers=headers)

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        g.applogger.info("Failed to execute driver: {} - {}".format(req.status_code, req.text))
        raise HTTPException("execute-driver", req)

    return {
        "result": req.json(),
        "message": "Driver execution started successfully.",
        "organization_id": organization_id,
        "workspace_id": workspace_id,
        "menu": menu
    }


@tool(
    name="dry-run-driver",
    description="Start executing ITA driver operation in dry-run mode (Ansible: DryRun).",
    input_schema=_EXECUTE_INPUT_SCHEMA,
    required_menu=_REQUIRED_MENU_EXECUTE
)
def tool_dry_run_driver(arguments: dict, payload: dict) -> dict:
    """
    ITAドライバー作業のドライランモードでの実行を開始する
    AnsibleDriverの場合はDryRunの実行を行う

    Start executing an ITA driver operation in dry-run mode (DryRun for the
    Ansible drivers).

    Parameters:
        arguments (dict): ツールの引数
            - menu (str): メニュー名(REST名) / menu name (REST name)
            - movement_name (str): 実行するMovement名 / movement name to execute
            - operation_name (str): 実行するOperation名 / operation name to execute
            - schedule_date (str, optional): スケジュール日時
              (形式: YYYY/MM/DD hh:mm) / schedule date and time (format: YYYY/MM/DD hh:mm)
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Returns:
        dict: ドライラン実行結果
            - result: APIレスポンスの実行情報 / the execution info returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
            - menu (str): メニュー名 / menu name

    Raises:
        Exception: menuが指定されていない場合 / if menu is not specified
        HTTPException: ドライラン実行の開始に失敗した場合 / if starting the dry-run execution fails
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")
    menu = arguments.get("menu", "")

    if not menu:
        raise Exception("menu is required")

    execute_data = _build_execute_data(arguments)

    # このツールが呼び出すのは "/ita/menu/{menu}/driver/execute_dry_run/" という
    # ITA自身のAPI(ita_api_organization)側のエンドポイントであるため、環境変数
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT を使用する
    #
    # This tool calls the "/ita/menu/{menu}/driver/execute_dry_run/" endpoint
    # of ITA's own API (ita_api_organization), so it uses the
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT environment
    # variables
    ita_api_host = os.getenv("ITA_API_ORAGANIZATION_HOST")
    ita_api_port = os.getenv("ITA_API_ORAGANIZATION_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/{}/driver/execute_dry_run/".format(
        ita_api_host, ita_api_port, organization_id, workspace_id, menu
    )

    # 転送用ヘッダーを組み立てる(POSTでボディを送るため"Content-Type"も付与する)
    # Build the headers to forward (also adds "Content-Type" since this is a POST with a body)
    headers = build_forward_headers(method="POST")

    # ITAのAPIへドライラン実行開始のPOSTリクエストを送信する
    # Send a POST request to ITA's API to start the dry-run execution
    req = requests.post(url, json=execute_data, headers=headers)

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        g.applogger.info("Failed to execute driver dry-run: {} - {}".format(req.status_code, req.text))
        raise HTTPException("dry-run-driver", req)

    return {
        "result": req.json(),
        "message": "Driver dry-run execution started successfully.",
        "organization_id": organization_id,
        "workspace_id": workspace_id,
        "menu": menu
    }


@tool(
    name="get-driver-status",
    description="Get the status of a driver execution by execution number.",
    input_schema={
        "type": "object",
        "properties": {
            "menu": {
                "type": "string",
                "description": "Menu name (REST name)"
            },
            "execution_no": {
                "type": "string",
                "description": "Execution number to check status"
            }
        },
        "required": ["menu", "execution_no"]
    },
    required_menu=_REQUIRED_MENU_STATUS
)
def tool_get_driver_status(arguments: dict, payload: dict) -> dict:
    """
    ITAドライバー作業実行の状態を取得する

    Get the status of an ITA driver execution.

    Parameters:
        arguments (dict): ツールの引数
            - menu (str): メニュー名(REST名) / menu name (REST name)
            - execution_no (str): 実行No / execution number
        payload (dict): 呼び出しコンテキスト情報
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id

    Returns:
        dict: ドライバー実行状態
            - result: APIレスポンスの実行状態情報 / the execution status info returned by the API
            - message (str): 処理結果メッセージ / result message
            - organization_id (str): オーガナイゼーションID / organization id
            - workspace_id (str): ワークスペースID / workspace id
            - menu (str): メニュー名 / menu name
            - execution_no (str): 実行No / execution number

    Raises:
        Exception: menuまたはexecution_noが指定されていない場合
            / if menu or execution_no is not specified
        HTTPException: 状態取得に失敗した場合 / if fetching the status fails
    """
    organization_id = payload.get("organization_id")
    workspace_id = payload.get("workspace_id")
    menu = arguments.get("menu", "")
    execution_no = arguments.get("execution_no", "")

    if not menu:
        raise Exception("menu is required")
    if not execution_no:
        raise Exception("execution_no is required")

    # このツールが呼び出すのは "/ita/menu/{menu}/driver/{execution_no}/" という
    # ITA自身のAPI(ita_api_organization)側のエンドポイントであるため、環境変数
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT を使用する
    #
    # This tool calls the "/ita/menu/{menu}/driver/{execution_no}/" endpoint
    # of ITA's own API (ita_api_organization), so it uses the
    # ITA_API_ORAGANIZATION_HOST / ITA_API_ORAGANIZATION_PORT environment
    # variables
    ita_api_host = os.getenv("ITA_API_ORAGANIZATION_HOST")
    ita_api_port = os.getenv("ITA_API_ORAGANIZATION_PORT")
    # プロトコルは常にhttp固定とする(ITAサービス間通信はhttpを使用する)
    # Protocol is always fixed to http (inter-service communication within ITA uses http)
    url = "http://{}:{}/api/{}/workspaces/{}/ita/menu/{}/driver/{}/".format(
        ita_api_host, ita_api_port, organization_id, workspace_id, menu, execution_no
    )

    # 転送用ヘッダーを組み立てる
    # Build the headers to forward
    headers = build_forward_headers(method="GET")

    # ITAのAPIへドライバー実行状態取得のGETリクエストを送信する
    # Send a GET request to ITA's API to fetch the driver execution status
    req = requests.get(url, headers=headers)

    # ステータスコードが200以外の場合は異常終了として例外を発生させる
    # If the status code is not 200, treat it as a failure and raise an exception
    if req.status_code != 200:
        g.applogger.info("Failed to get driver status: {} - {}".format(req.status_code, req.text))
        raise HTTPException("get-driver-status", req)

    return {
        "result": req.json(),
        "message": "Driver status retrieved successfully.",
        "organization_id": organization_id,
        "workspace_id": workspace_id,
        "menu": menu,
        "execution_no": execution_no
    }
