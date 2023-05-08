#   Copyright 2022 NEC Corporation
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

import connexion

from flask import g

from common_libs.common import *  # noqa: F403
from common_libs.api import api_filter
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from libs import driver_controll, menu_filter
from common_libs.common import menu_info
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.AnslConstClass import AnslConst
from common_libs.ansible_driver.classes.AnspConstClass import AnspConst
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst
from common_libs.ansible_driver.functions.rest_libs import insert_execution_list as a_insert_execution_list, execution_scram as a_exectuion_scram
from common_libs.terraform_driver.common.Const import Const as TFCommonConst
from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
from common_libs.terraform_driver.cli.Const import Const as TFCLIConst
from common_libs.terraform_driver.common.Execute import insert_execution_list as t_insert_execution_list, get_execution_info as t_get_execution_info, reserve_cancel as t_reserve_cancel  # noqa: E501
from common_libs.terraform_driver.cloud_ep.Execute import execution_scram as t_cloud_ep_execution_scram
from common_libs.terraform_driver.cli.Execute import execution_scram as t_cli_execution_scram

@api_filter
def get_driver_execute_data(organization_id, workspace_id, menu, execution_no):  # noqa: E501
    """get_driver_execute_data

    Driver作業実行の状態取得 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param execution_no: 実行No
    :type execution_no: str

    :rtype: InlineResponse20011
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['12']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # 作業状態確認メニューと作業実行メニューのRest名、テーブル名の対応
    target = {'check_operation_status_ansible_legacy': {'execution_list': 'execution_list_ansible_legacy',
                                                        'table_name': AnslConst.vg_exe_ins_msg_table_name,
                                                        'ansConstObj': AnslConst()},
              'check_operation_status_ansible_pioneer': {'execution_list': 'execution_list_ansible_pioneer',
                                                         'table_name': AnspConst.vg_exe_ins_msg_table_name,
                                                         'ansConstObj': AnspConst()},
              'check_operation_status_ansible_role': {'execution_list': 'execution_list_ansible_role',
                                                      'table_name': AnsrConst.vg_exe_ins_msg_table_name,
                                                      'ansConstObj': AnsrConst()},
              TFCloudEPConst.RN_CHECK_OPERATION: {'execution_list': TFCloudEPConst.RN_EXECUTION_LIST,
                                                  'table_name': TFCloudEPConst.T_EXEC_STS_INST},
              TFCLIConst.RN_CHECK_OPERATION: {'execution_list': TFCLIConst.RN_EXECUTION_LIST,
                                              'table_name': TFCLIConst.T_EXEC_STS_INST}
              }

    if 'ansible' in menu:
        # Ansible用 作業実行の状態取得
        result = driver_controll.get_execution_info(objdbca, target[menu], execution_no)
    else:
        # Terraform用 作業実行の状態取得
        result = t_get_execution_info(objdbca, target[menu], execution_no)

    return result,


@api_filter
def get_driver_execute_info(organization_id, workspace_id, menu):  # noqa: E501
    """get_driver_execute_info
    Movement,Operationのメニューの基本情報および項目情報を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str

    :rtype: InlineResponse20018
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['11']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # 作業実行メニューとMovement一覧の対応
    movement_target = {'execution_ansible_role': 'movement_list_ansible_role',
                       'execution_ansible_legacy': 'movement_list_ansible_legacy',
                       'execution_ansible_pioneer': 'movement_list_ansible_pioneer',
                       TFCloudEPConst.RN_EXECTION: TFCloudEPConst.RN_MOVEMENT,
                       TFCLIConst.RN_EXECTION: TFCLIConst.RN_MOVEMENT}

    # 作業実行関連のメニューの基本情報および項目情報の取得
    target_menus = ["operation_list", movement_target[menu]]
    data = {}
    for target in target_menus:
        data[target] = menu_info.collect_menu_info(objdbca, target)

    return data,


@api_filter
def get_driver_execute_search_candidates(organization_id, workspace_id, menu, target, column):  # noqa: E501
    """get_driver_execute_search_candidates

    表示フィルタで利用するプルダウン検索の候補一覧を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param target: movement_list or operation_list
    :type target: str
    :param column: REST用項目名
    :type column: str

    :rtype: InlineResponse2003
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['11']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # 作業実行メニューとMovement一覧の対応
    movement_target = {'execution_ansible_role': 'movement_list_ansible_role',
                       'execution_ansible_legacy': 'movement_list_ansible_legacy',
                       'execution_ansible_pioneer': 'movement_list_ansible_pioneer',
                       TFCloudEPConst.RN_EXECTION: TFCloudEPConst.RN_MOVEMENT,
                       TFCLIConst.RN_EXECTION: TFCLIConst.RN_MOVEMENT}

    # targetのチェック
    target_menus = ["operation_list", movement_target[menu]]
    if target not in target_menus:
        log_msg_args = [target]
        api_msg_args = [target]
        raise AppException("499-00008", log_msg_args, api_msg_args)  # noqa: F405

    # 対象項目のプルダウン検索候補一覧を取得
    data = menu_info.collect_search_candidates(objdbca, target, column)
    return data,


@api_filter
def post_driver_cancel(organization_id, workspace_id, menu, execution_no, body=None):  # noqa: E501
    """post_driver_cancel

    Driver作業実行の予約取消 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param execution_no: 実行No
    :type execution_no: str

    :rtype: InlineResponse20011
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['12']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    target = {'check_operation_status_ansible_legacy': AnscConst.DF_LEGACY_DRIVER_ID,
              'check_operation_status_ansible_pioneer': AnscConst.DF_PIONEER_DRIVER_ID,
              'check_operation_status_ansible_role': AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
              TFCloudEPConst.RN_CHECK_OPERATION: TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP,
              TFCLIConst.RN_CHECK_OPERATION: TFCommonConst.DRIVER_TERRAFORM_CLI}

    if 'ansible' in menu:
        # Ansible用 予約取り消し
        result = driver_controll.reserve_cancel(objdbca, target[menu], execution_no)
    else:
        # Terraform用 予約取り消し
        result = t_reserve_cancel(objdbca, target[menu], execution_no)

    return result,


@api_filter
def post_driver_excecute(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """post_driver_excecute

    Driver作業実行 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body: リクエストボディ
    :type body: dict | bytes

    :rtype: InlineResponse20017
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['11']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameter = body

    useed = True
    # 予約日時のフォーマットチェック
    # yyyy/mm/dd hh:mmをyyyy/mm/dd hh:mm:ssにしている
    schedule_date = driver_controll.scheduled_format_check(parameter, useed)

    Required = True
    # Movementチェック
    movement_row = driver_controll.movement_registr_check(objdbca, parameter, menu, Required)

    # オペレーションチェック
    operation_row = driver_controll.operation_registr_check(objdbca, parameter, Required)

    target = {'execution_ansible_legacy': AnscConst.DF_LEGACY_DRIVER_ID,
              'execution_ansible_pioneer': AnscConst.DF_PIONEER_DRIVER_ID,
              'execution_ansible_role': AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
              TFCloudEPConst.RN_EXECTION: TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP,
              TFCLIConst.RN_EXECTION: TFCommonConst.DRIVER_TERRAFORM_CLI}

    # トランザクション開始
    objdbca.db_transaction_start()

    # 作業管理に登録
    conductor_id = None
    conductor_name = None
    run_mode = "1"
    if 'ansible' in menu:
        # Ansible用 作業実行登録
        result = a_insert_execution_list(objdbca, run_mode, target[menu], operation_row, movement_row, schedule_date, conductor_id, conductor_name)
    else:
        # Terraform用 作業実行登録
        result = t_insert_execution_list(objdbca, run_mode, target[menu], operation_row, movement_row, schedule_date, conductor_id, conductor_name)
    # コミット・トランザクション終了
    objdbca.db_transaction_end(True)

    return result,


@api_filter
def post_driver_execute_check_parameter(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """post_driver_execute_check_parameter

    Driver作業実行(実行時に使用するパラメータ確認) # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse20017
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['11']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameter = body

    useed = True
    # 予約日時のフォーマットチェック
    # yyyy/mm/dd hh:mmをyyyy/mm/dd hh:mm:ssにしている
    schedule_date = driver_controll.scheduled_format_check(parameter, useed)

    Required = True
    # Movementチェック
    movement_row = driver_controll.movement_registr_check(objdbca, parameter, menu, Required)

    # オペレーションチェック
    operation_row = driver_controll.operation_registr_check(objdbca, parameter, Required)

    target = {'execution_ansible_legacy': AnscConst.DF_LEGACY_DRIVER_ID,
              'execution_ansible_pioneer': AnscConst.DF_PIONEER_DRIVER_ID,
              'execution_ansible_role': AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
              TFCloudEPConst.RN_EXECTION: TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP,
              TFCLIConst.RN_EXECTION: TFCommonConst.DRIVER_TERRAFORM_CLI}

    # トランザクション開始
    objdbca.db_transaction_start()

    # 作業管理に登録
    conductor_id = None
    conductor_name = None
    run_mode = "3"
    if 'ansible' in menu:
        # Ansible用 作業実行登録
        result = a_insert_execution_list(objdbca, run_mode, target[menu], operation_row, movement_row, schedule_date, conductor_id, conductor_name)
    else:
        # Terraform用 作業実行登録
        result = t_insert_execution_list(objdbca, run_mode, target[menu], operation_row, movement_row, schedule_date, conductor_id, conductor_name)
    # コミット・トランザクション終了
    objdbca.db_transaction_end(True)

    return result,

@api_filter
def post_driver_execute_delete_resource(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """post_driver_execute_delete_resource

    Driver作業実行(リソース削除) # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse20018
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['11']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameter = body

    # Terraformメニューであること
    if not menu == TFCloudEPConst.RN_EXECTION and not menu == TFCLIConst.RN_EXECTION:
        # リソース削除はTerraformドライバのみ実施可能です。
        raise AppException("499-00917", [], [])  # noqa: F405

    # トランザクション開始
    objdbca.db_transaction_start()

    # ドライバIDを選定
    if menu == TFCloudEPConst.RN_EXECTION:
        driver_id = TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP
    else:
        driver_id = TFCommonConst.DRIVER_TERRAFORM_CLI

    # パラメータの抽出
    tf_workspace_name = parameter.get('tf_workspace_name')
    if not tf_workspace_name:
        # 必要なパラメータが指定されていません。
        raise AppException("499-00908", ['tf_workspace_name'], ['tf_workspace_name'])  # noqa: F405

    # 作業実行登録
    run_mode = TFCommonConst.RUN_MODE_DESTROY
    result = t_insert_execution_list(objdbca, run_mode, driver_id, None, None, None, None, None, tf_workspace_name)

    # コミット・トランザクション終了
    objdbca.db_transaction_end(True)

    return result,


@api_filter
def post_driver_execute_dry_run(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """post_driver_execute_dry_run

    Driver作業実行（ドライラン）&lt;/br&gt; AnsibleDriverの場合はDryRun、TerraformDriverの場合はPlanのみの実行を行う  # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse20017
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['11']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameter = body

    useed = True
    # 予約日時のフォーマットチェック
    # yyyy/mm/dd hh:mmをyyyy/mm/dd hh:mm:ssにしている
    schedule_date = driver_controll.scheduled_format_check(parameter, useed)

    Required = True
    # Movementチェック
    movement_row = driver_controll.movement_registr_check(objdbca, parameter, menu, Required)

    # オペレーションチェック
    operation_row = driver_controll.operation_registr_check(objdbca, parameter, Required)

    target = {'execution_ansible_legacy': AnscConst.DF_LEGACY_DRIVER_ID,
              'execution_ansible_pioneer': AnscConst.DF_PIONEER_DRIVER_ID,
              'execution_ansible_role': AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
              TFCloudEPConst.RN_EXECTION: TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP,
              TFCLIConst.RN_EXECTION: TFCommonConst.DRIVER_TERRAFORM_CLI}

    # トランザクション開始
    objdbca.db_transaction_start()

    # 作業管理に登録
    conductor_id = None
    conductor_name = None
    run_mode = "2"
    if 'ansible' in menu:
        # Ansible用 作業実行登録
        result = a_insert_execution_list(objdbca, run_mode, target[menu], operation_row, movement_row, schedule_date, conductor_id, conductor_name)
    else:
        # Terraform用 作業実行登録
        result = t_insert_execution_list(objdbca, run_mode, target[menu], operation_row, movement_row, schedule_date, conductor_id, conductor_name)

    # コミット・トランザクション終了
    objdbca.db_transaction_end(True)

    return result,


@api_filter
def post_driver_execute_filter(organization_id, workspace_id, menu, target, body=None):  # noqa: E501
    """post_driver_execute_filter

    Movement,Operationを対象に、検索条件を指定し、レコードを取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param target: movement_list or operation_list
    :type target: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2005
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['11']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # 作業実行メニューとMovement一覧の対応
    movement_target = {'execution_ansible_role': 'movement_list_ansible_role',
                       'execution_ansible_legacy': 'movement_list_ansible_legacy',
                       'execution_ansible_pioneer': 'movement_list_ansible_pioneer',
                       TFCloudEPConst.RN_EXECTION: TFCloudEPConst.RN_MOVEMENT,
                       TFCLIConst.RN_EXECTION: TFCLIConst.RN_MOVEMENT}

    # targetのチェック
    target_menus = ["operation_list", movement_target[menu]]
    if target not in target_menus:
        log_msg_args = []
        api_msg_args = []
        raise AppException("499-00008", log_msg_args, api_msg_args)  # noqa: F405

    filter_parameter = {}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        filter_parameter = body

    # メニューのカラム情報を取得
    result_data = menu_filter.rest_filter(objdbca, target, filter_parameter)
    return result_data,


@api_filter
def post_driver_scram(organization_id, workspace_id, menu, execution_no, body=None):  # noqa: E501
    """post_driver_scram

    Driver作業実行の緊急停止 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param execution_no: 実行No
    :type execution_no: str

    :rtype: InlineResponse20011
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['12']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    objdbca.db_transaction_start()

    target = {'check_operation_status_ansible_legacy': AnscConst.DF_LEGACY_DRIVER_ID,
              'check_operation_status_ansible_pioneer': AnscConst.DF_PIONEER_DRIVER_ID,
              'check_operation_status_ansible_role': AnscConst.DF_LEGACY_ROLE_DRIVER_ID}

    if 'ansible' in menu:
        # Ansible用 緊急停止処理
        # result = a_exectuion_scram(objdbca, target[menu], execution_no)
        a_exectuion_scram(objdbca, target[menu], execution_no)
    else:
        if 'terraform_cloud_ep' in menu:
            # Terraform Cloud/EP用 緊急停止処理
            t_cloud_ep_execution_scram(objdbca, execution_no)
        else:
            # Terraform CLI用 緊急停止処理
            t_cli_execution_scram(objdbca, execution_no)

    objdbca.db_transaction_end(False)  # roleback

    # 緊急停止を受付ました
    result_msg = g.appmsg.get_api_message("MSG-10891", [execution_no])

    return result_msg,
