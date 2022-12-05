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
    t_hide_menu_list = 'T_HIDE_MENU_LIST'

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
    ret_hide_menu_list = objdbca.table_select(t_hide_menu_list, 'ORDER BY MENU_ID')

    # 対象メニューリストから対象外のメニューを削除する
    for record in ret_hide_menu_list:
        hide_menu_id = record.get('MENU_ID')
        if hide_menu_id in menu_id_list:
            menu_id_list.remove(hide_menu_id)

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

def execute_excel_bulk_export(objdbca, organization_id, workspace_id):
    """
        Excel一括エクスポート実行
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            result_data
    """
    # 変数定義
    lang = g.get('LANGUAGE')

    # typeを取得 (「新規作成(create_new)」「初期化(initialize)」「編集(edit)」)
    # type_name = create_param.get('type')
    # if type_name not in ['create_new', 'initialize', 'edit']:
    #     log_msg_args = ["type"]
    #     api_msg_args = ["type"]
    #     raise AppException('499-00703', log_msg_args, api_msg_args)  # 対象keyの値が不正です。(key: {}) # noqa: F405

    # menu_create_idの有無を確認
    # menu_data = check_request_body_key(create_param, 'menu')
    # menu_create_id = menu_data.get('menu_create_id')

    try:
        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'bulk_excel_export_import_list')  # noqa: F405

        # 登録用パラメータを作成
        parameters = {
            "parameter": {
                # "execution_no": execution_no,
                "status": "未実行",
                "process_type": "エクスポート",
                # "discard_information": discard_information,
                "execute_user": "操作ユーザ",
                # "file_name": file_name,
                # "result": result,
                # "discard": discard,
                # "last_update_date_time": last_update_date_time,
                # "last_updated_user": last_updated_user,
            },
            "type": "Register"
        }

        # 登録を実行
        exec_result = objmenu.exec_maintenance(parameters)  # noqa: E999
        if not exec_result[0]:
            result_msg = _format_loadtable_msg(exec_result[2])
            result_msg = json.dumps(result_msg, ensure_ascii=False)
            raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー

    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args

    # # 返却用の値を取得
    # menu_name_rest = result.get('menu_name_rest')
    # history_id = result.get('history_id')

    # result_data = {'menu_name_rest': menu_name_rest, 'history_id': history_id}
    # return result_data
    return 'do some magic!'

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