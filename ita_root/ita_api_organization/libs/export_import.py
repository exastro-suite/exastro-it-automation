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

import json
from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from common_libs.api import api_filter, check_request_body, check_request_body_key
from flask import g
from common_libs.common.exception import AppException  # noqa: F401


def get_menu_export_list(objdbca, organization_id, workspace_id):
    """
        メニューエクスポート対象メニュー一覧取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            result
    """
    # テーブル名
    t_common_menu = 'T_COMN_MENU'
    t_common_menu_group = 'T_COMN_MENU_GROUP'
    t_common_menu_table_link = 'T_COMN_MENU_TABLE_LINK'
    t_dp_hide_menu_list = 'T_DP_HIDE_MENU_LIST'

    # 変数定義
    lang = g.get('LANGUAGE')

    # 『メニュー-テーブル紐付管理』の対象シートタイプ
    sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']

    # 『メニュー-テーブル紐付管理』テーブルから対象のデータを取得
    ret_menu_table_link = objdbca.table_select(t_common_menu_table_link, 'WHERE SHEET_TYPE IN %s AND DISUSE_FLAG = %s ORDER BY MENU_ID', [sheet_type_list, 0])
    # 対象メニューIDをリスト化
    menu_id_list = []
    for record in ret_menu_table_link:
        menu_id_list.append(record.get('MENU_ID'))

    # 『非表示メニュー』テーブルから対象外にするメニューIDを取得
    ret_dp_hide_menu_list = objdbca.table_select(t_dp_hide_menu_list, 'ORDER BY MENU_ID')

    # 対象メニューリストから対象外のメニューを削除する
    for record in ret_dp_hide_menu_list:
        hide_menu_id = record.get('MENU_ID')
        if hide_menu_id in menu_id_list:
            menu_id_list.remove(hide_menu_id)

    # 『メニュー管理』テーブルから対象メニューを取得
    # メニュー名を取得
    ret_menu = objdbca.table_select(t_common_menu, 'WHERE MENU_ID IN %s AND DISUSE_FLAG = %s', [menu_id_list, 0])

    menu_group_id_list = []
    menus = {}
    for record in ret_menu:
        menu_group_id = record.get('MENU_GROUP_ID')
        menu_group_id_list.append(menu_group_id)
        if menu_group_id not in menus:
            menus[menu_group_id] = []

        add_menu = {}
        add_menu['id'] = record.get('MENU_ID')
        add_menu['menu_name'] = record.get('MENU_NAME_' + lang.upper())
        add_menu['menu_name_rest'] = record.get('MENU_NAME_REST')
        add_menu['disp_seq'] = record.get('DISP_SEQ')
        menus[record.get('MENU_GROUP_ID')].append(add_menu)

    # 『メニューグループ管理』テーブルから対象のデータを取得
    # メニューグループ名を取得
    ret_menu_group = objdbca.table_select(t_common_menu_group, 'WHERE MENU_GROUP_ID IN %s AND DISUSE_FLAG = %s ORDER BY DISP_SEQ', [menu_group_id_list, 0])

    # MENU_GROUP_ID:MENU_GROUP_NAMEのdict
    dict_menu_group_id_name = {}
    # MENU_GROUP_ID:DISP_SEQのdict
    dict_menu_group_id_seq = {}
    # メニューグループの一覧を作成し、メニュー一覧も格納する
    menu_group_list = []
    for record in ret_menu_group:
        menu_group_id = record.get('MENU_GROUP_ID')
        dict_menu_group_id_name[record.get('MENU_GROUP_ID')] = record.get('MENU_GROUP_NAME_' + lang.upper())
        dict_menu_group_id_seq[record.get('MENU_GROUP_ID')] = record.get('DISP_SEQ')

        add_menu_group = {}
        add_menu_group['parent_id'] = record.get('PARENT_MENU_GROUP_ID')
        add_menu_group['id'] = menu_group_id
        add_menu_group['menu_group_name'] = record.get('MENU_GROUP_NAME_' + lang.upper())
        add_menu_group['disp_seq'] = record.get('DISP_SEQ')
        add_menu_group['menus'] = menus.get(menu_group_id)

        menu_group_list.append(add_menu_group)

    menus_data = {
        "menu_groups": menu_group_list,
    }

    return menus_data

def get_excel_bulk_export_list(objdbca, organization_id, workspace_id):
    """
        メニューエクスポート対象メニュー一覧取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            result
    """
    # テーブル名
    t_common_menu = 'T_COMN_MENU'
    t_common_menu_group = 'T_COMN_MENU_GROUP'
    t_common_menu_table_link = 'T_COMN_MENU_TABLE_LINK'
    t_comn_role_menu_link = 'T_COMN_ROLE_MENU_LINK'

    # 変数定義
    lang = g.get('LANGUAGE')
    role_id_list = g.get('ROLES')

    # 『メニュー-テーブル紐付管理』の対象シートタイプ
    sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']

    # 『メニュー-テーブル紐付管理』テーブルから対象のデータを取得
    ret_menu_table_link = objdbca.table_select(t_common_menu_table_link, 'WHERE SHEET_TYPE IN %s AND DISUSE_FLAG = %s ORDER BY MENU_ID', [sheet_type_list, 0])

    # 対象メニューIDをリスト化
    menu_id_list = []
    for record in ret_menu_table_link:
        menu_id_list.append(record.get('MENU_ID'))

    # 『ロール-メニュー紐付管理』テーブルから対象のデータを取得
    # 自分のロールが「メンテナンス可」または「閲覧のみ」
    ret_role_menu_link = objdbca.table_select(t_comn_role_menu_link, 'WHERE MENU_ID IN %s AND ROLE_ID IN %s AND PRIVILEGE IN %s AND DISUSE_FLAG = %s ORDER BY MENU_ID', [menu_id_list, role_id_list, [1, 2], 0])

    # ロールまで絞った対象メニューIDを再リスト化
    menu_id_list = []
    for record in ret_role_menu_link:
        menu_id_list.append(record.get('MENU_ID'))

    # 『メニュー管理』テーブルから対象メニューを取得
    # メニュー名を取得
    ret_menu = objdbca.table_select(t_common_menu, 'WHERE MENU_ID IN %s AND DISUSE_FLAG = %s', [menu_id_list, 0])

    # MENU_ID:MENU_NAMEのdict
    dict_menu_id_name = {}
    menu_group_id_list = []
    result_id = {}
    for record in ret_menu:
        menu_group_id_list.append(record.get('MENU_GROUP_ID'))
        dict_menu_id_name[record.get('MENU_ID')] = record.get('MENU_NAME_' + lang.upper())
        result_id.setdefault(record.get('MENU_GROUP_ID'), []).append(record.get('MENU_ID'))

    # 『メニューグループ管理』テーブルから対象のデータを取得
    # メニューグループ名を取得
    ret_menu_group = objdbca.table_select(t_common_menu_group, 'WHERE MENU_GROUP_ID IN %s AND DISUSE_FLAG = %s ORDER BY DISP_SEQ', [menu_group_id_list, 0])

    # MENU_GROUP_ID:MENU_GROUP_NAMEのdict
    dict_menu_group_id_name = {}
    # MENU_GROUP_ID:DISP_SEQのdict
    dict_menu_group_id_seq = {}
    for record in ret_menu_group:
        dict_menu_group_id_name[record.get('MENU_GROUP_ID')] = record.get('MENU_GROUP_NAME_' + lang.upper())
        dict_menu_group_id_seq[record.get('MENU_GROUP_ID')] = record.get('DISP_SEQ')

    # DISP_SEQ:{MENU_GROUP_NAME:[MENU_NAME]}の形に整理する
    result = {}
    for menu_group_id, menu_list in result_id.items():
        result_name = {}
        menu_group_name = dict_menu_group_id_name[menu_group_id]
        for menu_id in menu_list:
            menu_name = dict_menu_id_name[menu_id]
            result_name.setdefault(menu_group_name, []).append(menu_name)
        result[dict_menu_group_id_seq[menu_group_id]] = result_name

    return result

def execute_menu_bulk_export(objdbca, menu, body):
    """
        メニュー一括エクスポート実行
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu:menu_export
            body:リクエストのbody部
        RETRUN:
            result_data
    """
    # 変数定義
    lang = g.get('LANGUAGE')
    user_id = g.get('USER_ID')

    # テーブル名
    t_dp_status_master = 'T_DP_STATUS_MASTER'
    t_dp_execution_type = 'T_DP_EXECUTION_TYPE'
    t_dp_mode = 'T_DP_MODE'
    t_dp_abolished_type = 'T_DP_ABOLISHED_TYPE'

    try:
        # トランザクション開始
        objdbca.db_transaction_start()

        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'menu_export_import_list')  # noqa: F405
        if objmenu.get_objtable() is False:
            log_msg_args = ["not menu or table"]
            api_msg_args = ["not menu or table"]
            raise AppException("401-00001", log_msg_args, api_msg_args) # noqa: F405

        body_specified_time = None
        body_mode = body.get('mode')
        body_abolished_type = body.get('abolished_type')
        if body_mode == '2':
            body_specified_time = body.get('specified_time')

        # 『ステータスマスタ』テーブルから対象のデータを取得
        # 形式名を取得
        ret_dp_status = objdbca.table_select(t_dp_status_master, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [1, 0])
        if not ret_dp_status:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

        status = ret_dp_status[0].get('TASK_STATUS_NAME_' + lang.upper())

        # 『処理種別マスタ』テーブルから対象のデータを取得
        # 形式名を取得
        ret_dp_execution_type = objdbca.table_select(t_dp_execution_type, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [1, 0])
        if not ret_dp_execution_type:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

        execution_type = ret_dp_execution_type[0].get('EXECUTION_TYPE_NAME_' + lang.upper())

        # 『モードマスタ』テーブルから対象のデータを取得
        # 形式名を取得
        ret_dp_mode = objdbca.table_select(t_dp_mode, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [body_mode, 0])
        if not ret_dp_mode:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

        mode = ret_dp_mode[0].get('MODE_NAME_' + lang.upper())

        # 『廃止情報マスタ』テーブルから対象のデータを取得
        # 形式名を取得
        ret_dp_abolished_type = objdbca.table_select(t_dp_abolished_type, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [body_abolished_type, 0])
        if not ret_dp_abolished_type:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

        abolished_type = ret_dp_abolished_type[0].get('ABOLISHED_TYPE_NAME_' + lang.upper())

        # 登録用パラメータを作成
        parameters = {
            "parameter": {
                "status": status,
                "execution_type": execution_type,
                "mode": mode,
                "abolished_type": abolished_type,
                "specified_time": body_specified_time,
                "file_name": None,
                "execution_user": user_id,
                "json_storage_item": json.dumps(body),
                "discard": "0"
            },
            "type": "Register"
        }

        # 登録を実行
        exec_result = objmenu.exec_maintenance(parameters, "", "", False, False, True)  # noqa: E999
        if not exec_result[0]:
            result_msg = _format_loadtable_msg(exec_result[2])
            result_msg = json.dumps(result_msg, ensure_ascii=False)
            raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー

        # コミット/トランザクション終了
        objdbca.db_transaction_end(True)

    except Exception as e:
        # ロールバック トランザクション終了
        objdbca.db_transaction_end(False)

        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args, None

    # 返却用の値を取得
    execution_no = exec_result[1].get('execution_no')

    result_data = {'execution_no': execution_no}

    return result_data


def execute_excel_bulk_export(objdbca, menu, body):
    """
        メニュー一括エクスポート実行
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu:menu_export
            body:リクエストのbody部
        RETRUN:
            result_data
    """
    # 変数定義
    lang = g.get('LANGUAGE')
    user_id = g.get('USER_ID')

    # テーブル名
    t_dp_status_master = 'T_DP_STATUS_MASTER'
    t_dp_execution_type = 'T_DP_EXECUTION_TYPE'
    t_dp_abolished_type = 'T_DP_ABOLISHED_TYPE'

    try:
        # トランザクション開始
        objdbca.db_transaction_start()

        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'bulk_excel_export_import_list')  # noqa: F405
        if objmenu.get_objtable() is False:
            log_msg_args = ["not menu or table"]
            api_msg_args = ["not menu or table"]
            raise AppException("401-00001", log_msg_args, api_msg_args) # noqa: F405

        body_abolished_type = body.get('abolished_type')

        # 『ステータスマスタ』テーブルから対象のデータを取得
        # 形式名を取得
        ret_dp_status = objdbca.table_select(t_dp_status_master, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [1, 0])
        if not ret_dp_status:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

        status = ret_dp_status[0].get('TASK_STATUS_NAME_' + lang.upper())

        # 『処理種別マスタ』テーブルから対象のデータを取得
        # 形式名を取得
        ret_dp_execution_type = objdbca.table_select(t_dp_execution_type, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [1, 0])
        if not ret_dp_execution_type:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

        execution_type = ret_dp_execution_type[0].get('EXECUTION_TYPE_NAME_' + lang.upper())

        # 『廃止情報マスタ』テーブルから対象のデータを取得
        # 形式名を取得
        ret_dp_abolished_type = objdbca.table_select(t_dp_abolished_type, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [body_abolished_type, 0])
        if not ret_dp_abolished_type:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

        abolished_type = ret_dp_abolished_type[0].get('ABOLISHED_TYPE_NAME_' + lang.upper())

        # 登録用パラメータを作成
        parameters = {
            "parameter": {
                "status": status,
                "execution_type": execution_type,
                "abolished_type": abolished_type,
                "file_name": None,
                "result_file": None,
                "execution_user": user_id,
                "json_storage_item": json.dumps(body),
                "discard": "0"
            },
            "type": "Register"
        }

        # 登録を実行
        exec_result = objmenu.exec_maintenance(parameters, "", "", False, False, True)  # noqa: E999
        if not exec_result[0]:
            result_msg = _format_loadtable_msg(exec_result[2])
            result_msg = json.dumps(result_msg, ensure_ascii=False)
            raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー

        # コミット/トランザクション終了
        objdbca.db_transaction_end(True)

    except Exception as e:
        # ロールバック トランザクション終了
        objdbca.db_transaction_end(False)

        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args, None

    # 返却用の値を取得
    execution_no = exec_result[1].get('execution_no')

    result_data = {'execution_no': execution_no}

    return result_data

def _format_loadtable_msg(loadtable_msg):
    """
        【内部呼び出し用】loadTableから受け取ったバリデーションエラーメッセージをフォーマットする
        ARGS:
            loadtable_msg: loadTableから返却されたメッセージ(dict)
        RETRUN:
            format_msg
    """
    result_msg = {}
    for key, value_list in loadtable_msg.items():
        msg_list = []
        for value in value_list:
            msg_list.append(value.get('msg'))
        result_msg[key] = msg_list

    return result_msg