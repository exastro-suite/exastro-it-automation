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
import subprocess
import shutil
import collections
import re
import zipfile
import glob
import base64
import datetime
import tarfile
import mimetypes
import secrets
import pathlib
import time
from collections import Counter
from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import *  # noqa: F403
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

        # 親メニューグループ情報を取得
        parent_menu_group = {}
        parent_flg = False
        parent_id = add_menu_group['parent_id']
        if parent_id is not None:
            for data in menu_group_list:
                if parent_id == data['id']:
                    parent_flg = True

            # 親メニューグループがすでに追加されているか確認
            if parent_flg is False:
                parent_menu_group_info = getParentMenuGroupInfo(parent_id, objdbca)
                parent_menu_group['parent_id'] = None
                parent_menu_group['id'] = parent_id
                parent_menu_group['menu_group_name'] = parent_menu_group_info["MENU_GROUP_NAME_" + g.LANGUAGE.upper()]
                parent_menu_group["disp_seq"] = parent_menu_group_info["DISP_SEQ"]
                parent_menu_group['menus'] = []
                menu_group_list.append(parent_menu_group)

        menu_group_list.append(add_menu_group)

    menus_data = {
        "menu_groups": menu_group_list,
    }

    return menus_data

def get_excel_bulk_export_list(objdbca, organization_id, workspace_id):
    """
        EXCELエクスポート対象メニュー一覧取得
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
    # 自分のロールが「メンテナンス可」,「閲覧のみ」
    ret_role_menu_link = objdbca.table_select(t_comn_role_menu_link, 'WHERE MENU_ID IN %s AND ROLE_ID IN %s AND PRIVILEGE IN %s AND DISUSE_FLAG = %s ORDER BY MENU_ID', [menu_id_list, role_id_list, [1, 2], 0])

    # ロールまで絞った対象メニューIDを再リスト化
    menu_id_list = []
    for record in ret_role_menu_link:
        menu_id_list.append(record.get('MENU_ID'))

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

        # 親メニューグループ情報を取得
        parent_menu_group = {}
        parent_flg = False
        parent_id = add_menu_group['parent_id']
        if parent_id is not None:
            for data in menu_group_list:
                if parent_id == data['id']:
                    parent_flg = True

            # 親メニューグループがすでに追加されているか確認
            if parent_flg is False:
                parent_menu_group_info = getParentMenuGroupInfo(parent_id, objdbca)
                parent_menu_group['parent_id'] = None
                parent_menu_group['id'] = parent_id
                parent_menu_group['menu_group_name'] = parent_menu_group_info["MENU_GROUP_NAME_" + g.LANGUAGE.upper()]
                parent_menu_group["disp_seq"] = parent_menu_group_info["DISP_SEQ"]
                parent_menu_group['menus'] = []
                menu_group_list.append(parent_menu_group)

        menu_group_list.append(add_menu_group)

    menus_data = {
        "menu_groups": menu_group_list,
    }

    return menus_data

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
            body_specified_time = body.get('specified_timestamp')

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

        user_name = util.get_user_name(user_id)

        # 登録用パラメータを作成
        parameters = {
            "parameter": {
                "status": status,
                "execution_type": execution_type,
                "mode": mode,
                "abolished_type": abolished_type,
                "specified_time": body_specified_time,
                "file_name": None,
                "execution_user": user_name,
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
        EXCEL一括エクスポート実行
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

        user_name = util.get_user_name(user_id)

        # 登録用パラメータを作成
        parameters = {
            "parameter": {
                "status": status,
                "execution_type": execution_type,
                "abolished_type": abolished_type,
                "language": lang,
                "file_name": None,
                "result_file": None,
                "execution_user": user_name,
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

def execute_excel_bulk_upload(organization_id, workspace_id, body, objdbca):
    """
        Excel一括インポートのアップロード
        ARGS:
            body:リクエストのbody部
        RETRUN:
            result_data
    """

    arrayResult = {}
    msg_args = ""
    intResultCode = ""
    role_id_list = g.get('ROLES')

    body_zipfile = body.get('zipfile')
    # upload_idの作成
    date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    upload_id = date + str(secrets.randbelow(9999999999))

    fileName = upload_id + '_ita_data.zip'

    # ファイル保存
    uploadFilePath = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/tmp/bulk_excel/import/upload/" + fileName
    uploadPath = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/tmp/bulk_excel/import/upload/"
    importPath = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/tmp/bulk_excel/import/import/"
    ret = upload_file(uploadFilePath, body_zipfile['base64'])

    if ret == 0:
        if os.path.exists(uploadPath + fileName):
            os.remove(uploadPath + fileName)

    # zip解凍
    if os.path.exists(uploadPath + fileName):
        os.makedirs(uploadPath + upload_id)
        os.chmod(uploadPath + upload_id, 0o777)

    ret = unzip_file(fileName, uploadPath, upload_id)

    if ret is False:
        unzip_file_cmd(fileName, uploadPath, upload_id)

    # zipファイルの中身確認
    declare_list = checkZipFile(upload_id, organization_id, workspace_id)

    # メニューリストの取得
    tmpRetImportAry = makeImportCheckbox(declare_list, upload_id, organization_id, workspace_id, objdbca)
    if len(tmpRetImportAry) == 0:
        # ファイルの削除
        cmd = "rm -rf " + importPath + upload_id
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        raise AppException("499-01305", [], [])

    retImportAry = {}
    retUnImportAry = {}
    idx = 0
    idx_unimport = 0
    for menuGroupId, menuGroupInfo in tmpRetImportAry.items():
        for k, menuInfo in menuGroupInfo["menu"].items():
            if menuGroupId == "none":
                # メニューが存在しない
                error = menuInfo["error"]
                fileName = menuInfo["file_name"]
                if menuGroupId not in retUnImportAry:
                    retUnImportAry[menuGroupId] = {}
                    retUnImportAry[menuGroupId]["menu"] = {}
                retUnImportAry[menuGroupId]["menu"][idx_unimport] = {"disp_seq": "",
                                                                        "menu_id": "",
                                                                        "menu_name": "",
                                                                        "file_name": fileName,
                                                                        "error": error}
                idx_unimport += 1
                continue

            menuId = menuInfo["menu_id"]
            menuName = menuInfo["menu_name"]
            fileName = menuInfo["file_name"]

            tmpMenuInfo = getMenuInfoByMenuId(menuId, "", objdbca)
            group_disp_seq = tmpMenuInfo["GROUP_DISP_SEQ"]
            parent_id = tmpMenuInfo["PARENT_MENU_GROUP_ID"]
            disp_seq = tmpMenuInfo["DISP_SEQ"]

            # 親メニューグループ情報を取得
            parent_list = {}
            if parent_id is not None:
                parent_menu_group_info = getParentMenuGroupInfo(parent_id, objdbca)
                parent_list["menu_group_name"] = parent_menu_group_info["MENU_GROUP_NAME_" + g.LANGUAGE.upper()]
                parent_list["disp_seq"] = parent_menu_group_info["DISP_SEQ"]

            # 『ロール-メニュー紐付管理』テーブルから対象のデータを取得
            # 自分のロールが「メンテナンス可」
            ret_role_menu_link = objdbca.table_select("T_COMN_ROLE_MENU_LINK", 'WHERE MENU_ID = %s AND ROLE_ID IN %s AND DISUSE_FLAG = %s', [menuId, role_id_list, 0])
            for record in ret_role_menu_link:
                if record["PRIVILEGE"] != "1":
                    # 権限エラー
                    msgstr = g.appmsg.get_api_message("MSG-30033")
                    menuInfo["error"] = msgstr

            # 『メニューテーブル紐付管理』テーブルから対象のデータを取得
            ret_role_menu_link = objdbca.table_select('T_COMN_MENU_TABLE_LINK', 'WHERE MENU_ID = %s AND DISUSE_FLAG = %s ORDER BY MENU_ID', [menuId, 0])

            for record in ret_role_menu_link:
                if record["ROW_INSERT_FLAG"] == "0" and record["ROW_UPDATE_FLAG"] == "0" and record["ROW_DISUSE_FLAG"] == "0" and record["ROW_REUSE_FLAG"] == "0":
                    # 権限エラー
                    msgstr = g.appmsg.get_api_message("MSG-30033")
                    menuInfo["error"] = msgstr

            if "error" in menuInfo:
                error = menuInfo["error"]
                if menuGroupId in retUnImportAry:
                    retUnImportAry[menuGroupId]["menu"][idx_unimport] = {"disp_seq": disp_seq,
                                                                        "menu_id": menuId,
                                                                        "menu_name": menuName,
                                                                        "file_name": fileName,
                                                                        "error": error}

                    idx_unimport += 1
                else:
                    retUnImportAry[menuGroupId] = {"disp_seq": group_disp_seq,
                                                "menu_group_id": menuGroupId,
                                                "menu_group_name": menuGroupInfo["menu_group_name"],
                                                "menu": {idx_unimport: {"disp_seq": disp_seq,
                                                        "menu_id": menuId,
                                                        "menu_name": menuName,
                                                        "file_name": fileName,
                                                        "error": error}},
                                                "parent_id": parent_id}

                    if parent_id is not None:
                        retUnImportAry[parent_id] = {"disp_seq": parent_list["disp_seq"],
                                                    "menu_group_name": parent_list["menu_group_name"]}

                    idx_unimport += 1
            else:
                if menuGroupId in retImportAry:
                    retImportAry[menuGroupId]["menu"][idx] = {"disp_seq": disp_seq,
                                                                "menu_id": menuId,
                                                                "menu_name": menuName,
                                                                "file_name": fileName}

                    idx += 1
                else:
                    retImportAry[menuGroupId] = {"disp_seq": group_disp_seq,
                                                "menu_group_id": menuGroupId,
                                                "menu_group_name": menuGroupInfo["menu_group_name"],
                                                "menu": {idx: {"disp_seq": disp_seq,
                                                        "menu_id": menuId,
                                                        "menu_name": menuName,
                                                        "file_name": fileName}},
                                                "parent_id": parent_id}

                    if parent_id is not None and parent_id not in retImportAry:
                        retImportAry[parent_id] = {"disp_seq": parent_list["disp_seq"],
                                                    "menu_group_name": parent_list["menu_group_name"]}

                    idx += 1

    intResultCode = "000"

    arrayResult["upload_id"] = upload_id
    arrayResult["data_portability_upload_file_name"] = body['zipfile']['name']

    if intResultCode == "000":
        arrayResult["import_list"] = retImportAry
        arrayResult["umimport_list"] = retUnImportAry
    if intResultCode == "002":
        del arrayResult["upload_id"]

    return arrayResult

def execute_excel_bulk_import(objdbca, menu, body):
    """
        EXCEL一括インポート実行
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
        ret_dp_execution_type = objdbca.table_select(t_dp_execution_type, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [2, 0])
        if not ret_dp_execution_type:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

        execution_type = ret_dp_execution_type[0].get('EXECUTION_TYPE_NAME_' + lang.upper())

        user_name = util.get_user_name(user_id)

        # 登録用パラメータを作成
        parameters = {
            "parameter": {
                "status": status,
                "execution_type": execution_type,
                "abolished_type": None,
                "language": lang,
                "file_name": None,
                "result_file": None,
                "execution_user": user_name,
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

def unzip_file(fileName, uploadPath, upload_id):
    """
        zipファイルを解凍する

        args:
            fileName: ファイル名
            uploadPath: 解凍先パス
            upload_id: アップロードID
    """
    try:
        with zipfile.ZipFile(uploadPath + fileName) as z:
            for info in z.infolist():
                info.filename = info.orig_filename.encode('cp437').decode('cp932')
                if os.sep != "/" and os.sep in info.filename:
                    info.filename = info.filename.replace(os.sep, "/")
                z.extract(info, path=uploadPath + upload_id)

    except Exception as e:
        return False

    return True

def unzip_file_cmd(fileName, uploadPath, upload_id):
    """
        zipファイルを解凍する(コマンド)

        args:
            fileName: ファイル名
            uploadPath: 解凍先パス
            upload_id: アップロードID
    """
    to_path = uploadPath + upload_id
    from_path = uploadPath + fileName
    cmd = ["unzip", "-d", to_path, from_path]
    cp = subprocess.run(cmd, capture_output=True, text=True)

    return

def checkZipFile(upload_id, organization_id, workspace_id):
    """
        zipファイルの中身を確認する

        args:
            upload_id: アップロードID
    """
    fileName = upload_id + '_ita_data.zip'
    uploadPath = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/tmp/bulk_excel/import/upload/"
    importPath = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/tmp/bulk_excel/import/import/"

    lst = os.listdir(uploadPath + upload_id)

    fileAry = []
    for value in lst:
        if not value == '.' and not value == '..':
            path = os.path.join(uploadPath + upload_id, value)
            if os.path.isdir(path):
                dir_name = value
                sublst = os.listdir(path)
                for subvalue in sublst:
                    if not subvalue == '.' and not subvalue == '..':
                        fileAry.append(dir_name + "/" + subvalue)
            else:
                fileAry.append(value)

    if len(fileAry) == 0:
        if os.path.exists(uploadPath + fileName):
            os.remove(uploadPath + fileName)
        shutil.rmtree(uploadPath + upload_id)

        raise AppException("499-01301", [], [])

    # 必須ファイルの確認
    errCnt = 0
    errFlg = True
    for value in fileAry:
        if 'MENU_LIST.txt' in value:
            errFlg = False

    if errFlg == 1:
        errCnt += 1
        if os.path.exists(uploadPath + fileName):
            os.remove(uploadPath + fileName)
        shutil.rmtree(uploadPath + upload_id)

        raise AppException("499-01302", [], [])

    if not os.path.exists(uploadPath + upload_id + '/MENU_LIST.txt'):
        errCnt += 1
        if os.path.exists(uploadPath + fileName):
            os.remove(uploadPath + fileName)
        shutil.rmtree(uploadPath + upload_id)

        raise AppException("499-01302", [], [])

    tmp_menu_list = Path(uploadPath + upload_id + '/MENU_LIST.txt').read_text(encoding="utf-8")
    if tmp_menu_list == "":
        if os.path.exists(uploadPath + fileName):
            os.remove(uploadPath + fileName)
        shutil.rmtree(uploadPath + upload_id)

        raise AppException("499-01303", [], [])

    if errCnt > 0:
        if os.path.exists(uploadPath + fileName):
            os.remove(uploadPath + fileName)

        shutil.rmtree(uploadPath + upload_id)

        raise AppException("499-01301", [], [])

    # ファイル移動
    if not os.path.exists(importPath):
        os.makedirs(importPath)
        os.chmod(importPath, 0o777)

    shutil.copy(uploadPath + fileName, importPath + fileName)
    os.makedirs(importPath + upload_id)
    os.chmod(importPath + upload_id, 0o777)
    from_path = uploadPath + upload_id
    to_path = importPath + '.'
    cmd = "cp -frp " + from_path + ' ' + to_path
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)

    errCnt = 0
    declare_check_list = []
    for value in fileAry:
        file = importPath + upload_id + '/' + value
        if not os.path.exists(file):
            errCnt += 1
            break

        if not file == "":
            tmpFileAry = file.split("/")
            tmpfileName = tmpFileAry[len(tmpFileAry) - 1]
            declare_check_list.append(tmpfileName)

    declare_list = collections.Counter(declare_check_list)
    for value in fileAry:
        file = importPath + upload_id + '/' + value
        if value.endswith(".xlsx"):
            continue

        if not os.path.exists(file):
            errCnt += 1
            break

        if not file:
            cmd = "rm -rf " + importPath + upload_id
            ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if ret.returncode != 0:
                return False

    if errCnt > 0:
        if os.path.exists(uploadPath + fileName):
            os.remove(uploadPath + fileName)

        if os.path.exists(importPath + fileName):
            os.remove(importPath + fileName)

        cmd = "rm -rf " + uploadPath + upload_id + " 2>&1"
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if ret.returncode != 0:
            raise AppException("499-01304", [], [])

        cmd = "rm -rf " + importPath + upload_id + " 2>&1"
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if ret.returncode != 0:
            raise AppException("499-01304", [], [])

        raise AppException("499-01301", [], [])

    #アップロードファイル削除
    cmd = "rm " + uploadPath + fileName
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if ret.returncode != 0:
        raise AppException("499-01304", [], [])

    cmd = "rm -rf " + uploadPath + upload_id + " 2>&1"
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if ret.returncode != 0:
        raise AppException("499-01304", [], [])

    return declare_list

def makeImportCheckbox(declare_list, upload_id, organization_id, workspace_id, objdbca):
    """
    インポートするメニューのチェックボックス作成

    Arguments:
        upload_id: アップロードID
        objdbca: DBオブジェクト
    Returns:
        実行結果
    """
    path = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/tmp/bulk_excel/import/import/"

    # 取得したいFILEリストの取得
    menuIdFile = Path(path + upload_id + '/MENU_LIST.txt').read_text(encoding="utf-8")

    tmpMenuIdFileAry = menuIdFile.split("\n")

    if len(tmpMenuIdFileAry) == 0:
        # ファイルの削除
        cmd = "rm -rf " + path + upload_id
        subprocess.run(cmd, capture_output=True, text=True, shell=True)

        raise AppException("499-01303", [], [])

    retImportAry = {}
    idx = 0
    none_idx = 0
    for menuFileInfo in tmpMenuIdFileAry:
        # フォーマットチェック
        result1 = re.match('^#', menuFileInfo)

        if not result1 and not menuFileInfo == "":
            menuIdFileInfo = menuFileInfo.split(":")
            menuNameRest = menuIdFileInfo[0]
            menuFileName = menuIdFileInfo[1]
            menuInfo = getMenuInfoByMenuId("", menuNameRest, objdbca)

            if not len(menuInfo) == 0:
                menuGroupId = menuInfo["MENU_GROUP_ID"]
                menuId = menuInfo["MENU_ID"]
                if g.get('LANGUAGE') == 'ja':
                    menuGroupName = menuInfo["MENU_GROUP_NAME_JA"]
                    menuName = menuInfo["MENU_NAME_JA"]
                else:
                    menuGroupName = menuInfo["MENU_GROUP_NAME_EN"]
                    menuName = menuInfo["MENU_NAME_EN"]

                menuGroupFolderName = menuGroupId + "_" + menuGroupName.replace("/", "_")
            else:
                menuId = ""
                menuGroupId = ""
                menuGroupName = ""
                menuName = ""
                menuGroupFolderName = ""

            if len(retImportAry) == 0 or len(menuInfo) == 0:
                declare_key = False
                declare_file_name_key = False
            else:
                if menuGroupId in retImportAry:
                    tmp_ary = []
                    for key, value in retImportAry[menuGroupId]["menu"].items():
                        if "menu_id" in value:
                            tmp_ary.append(value["menu_id"])
                        if menuId in tmp_ary:
                            declare_key = True
                            break
                    tmp_ary = []
                    for key, value in retImportAry[menuGroupId]["menu"].items():
                        if "file_name" in value:
                            tmp_ary.append(value["file_name"])
                        if menuFileName in tmp_ary:
                            declare_file_name_key = tmp_ary.index(menuFileName)
                            break
                    declare_menu_info = retImportAry[menuGroupId]["menu"][declare_file_name_key]
                else:
                    declare_key = False
                    declare_file_name_key = False

            # メニューの存在チェック
            if menuId == "":
                tmpMenuInfo = {"menu_id": menuId,
                                "menu_name": menuName,
                                "disabled": True,
                                "error": g.appmsg.get_api_message("MSG-30029"),
                                "file_name": menuFileName}

                if menuGroupId in retImportAry:
                    # メニューグループは存在するがメニューがない場合
                    if declare_key == 0:
                        retImportAry[menuGroupId]["menu"][idx] = tmpMenuInfo
                    else:
                        idx = 0
                        retImportAry[menuGroupId] = {"menu_group_name": menuGroupName,
                                                    "menu": {idx: tmpMenuInfo}}

                    idx += 1
                else:
                    if "none" not in retImportAry:
                        retImportAry["none"] = {"menu": {idx: tmpMenuInfo}}
                    else:
                        retImportAry["none"]["menu"][idx] = tmpMenuInfo
                    idx += 1
            # ファイルの拡張子チェック
            elif not menuFileName.endswith(".xlsx") and not menuFileName == "":
                tmpMenuInfo = {"menu_id": menuId,
                                "menu_name": menuName,
                                "disabled": True,
                                "error": g.appmsg.get_api_message("MSG-30029"),
                                "file_name": menuFileName}

                if menuGroupId in retImportAry:
                    # メニューグループは存在するがメニューがない場合
                    if declare_key == 0:
                        retImportAry[menuGroupId]["menu"][idx] = tmpMenuInfo
                    else:
                        idx = 0
                        retImportAry[menuGroupId] = {"menu_group_name": menuGroupName,
                                                    "menu": {idx: tmpMenuInfo}}

                    idx += 1
            # ファイルの有無
            else:
                if os.path.exists(path + upload_id + "/" + menuGroupFolderName + "/" + menuFileName) and not menuFileName == "":
                    # retImportAryのなかに該当メニューグループがあるかどうか
                    if menuGroupId in retImportAry:
                        # メニューグループは存在するがメニューがない場合
                        # 同名ファイルが複数あった場合
                        if declare_list[menuFileName] > 1:
                            tmpMenuInfo = {"menu_id": menuId,
                                "menu_name": menuName,
                                "disabled": True,
                                "error": g.appmsg.get_api_message("MSG-30030"),
                                "file_name": menuFileName}

                            declare_menu_info["disabled"] = True
                            declare_menu_info["error"] = g.appmsg.get_api_message("MSG-30030")

                            retImportAry[menuGroupId]["menu"][idx] = tmpMenuInfo
                            retImportAry[menuGroupId]["menu"][declare_file_name_key] = declare_menu_info
                            idx += 1
                        elif not declare_key == 0:
                            tmpMenuInfo = {"menu_id": menuId,
                                "menu_name": menuName,
                                "disabled": True,
                                "error": g.appmsg.get_api_message("MSG-30031"),
                                "file_name": menuFileName}

                            declare_menu_info["disabled"] = True
                            declare_menu_info["error"] = g.appmsg.get_api_message("MSG-30031")

                            retImportAry[menuGroupId]["menu"][idx] = tmpMenuInfo
                            retImportAry[menuGroupId]["menu"][declare_file_name_key] = declare_menu_info
                            idx += 1
                        else:
                            retImportAry[menuGroupId]["menu"][idx] = {"menu_id": menuId,
                                                            "menu_name": menuName,
                                                            "disabled": False,
                                                            "file_name": menuFileName}
                            idx += 1
                    else:
                        if declare_list[menuFileName] > 1:
                            idx = 0
                            retImportAry[menuGroupId] = {"menu_group_name": menuGroupName,
                                                        "menu": {idx: {"menu_id": menuId,
                                                            "menu_name": menuName,
                                                            "error": g.appmsg.get_api_message("MSG-30030"),
                                                            "disabled": True,
                                                            "file_name": menuFileName}}}

                            idx += 1
                        else:
                            idx = 0
                            retImportAry[menuGroupId] = {"menu_group_name": menuGroupName,
                                                        "menu": {idx: {"menu_id": menuId,
                                                            "menu_name": menuName,
                                                            "disabled": False,
                                                            "file_name": menuFileName}}}

                            idx += 1
                else:
                    tmpMenuInfo = {"menu_id": menuId,
                                "menu_name": menuName,
                                "disabled": True,
                                "error": g.appmsg.get_api_message("MSG-30032"),
                                "file_name": menuFileName}
                    if menuGroupId in retImportAry:
                        # メニューグループは存在するがメニューがない場合
                        if declare_key == 0:
                            retImportAry[menuGroupId]["menu"][idx] = tmpMenuInfo

                        idx += 1
                    else:
                        idx = 0
                        retImportAry[menuGroupId] = {"menu_group_name": menuGroupName,
                                                    "menu": {idx: tmpMenuInfo}}

                        idx += 1

    if len(retImportAry) == 0:
        # ファイルの削除
        cmd = "rm -rf " + path + upload_id
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)

        raise AppException("499-01303", [], [])

    return retImportAry

def getMenuInfoByMenuId(menu_id, menuNameRest, objdbca=None):
    """
    メニュー情報取得

    Arguments:
        menuId: メニューREST名
        objdbca: DBオブジェクト
    Returns:
        実行結果
    """
    sql = "SELECT "
    sql += " T_COMN_MENU.MENU_ID, T_COMN_MENU.MENU_NAME_JA, T_COMN_MENU.MENU_GROUP_ID, T_COMN_MENU_GROUP.MENU_GROUP_NAME_JA, T_COMN_MENU_GROUP.MENU_GROUP_NAME_EN, "
    sql += " T_COMN_MENU.DISP_SEQ, T_COMN_MENU_GROUP.PARENT_MENU_GROUP_ID, T_COMN_MENU_GROUP.DISP_SEQ AS GROUP_DISP_SEQ "
    sql += "FROM T_COMN_MENU "
    sql += "LEFT OUTER JOIN "
    sql += " T_COMN_MENU_GROUP "
    sql += "ON T_COMN_MENU.MENU_GROUP_ID = T_COMN_MENU_GROUP.MENU_GROUP_ID "
    if menu_id == "":
        sql += "WHERE T_COMN_MENU.MENU_NAME_REST = %s "
    else:
        sql += "WHERE T_COMN_MENU.MENU_ID = %s "
    sql += "AND T_COMN_MENU.DISUSE_FLAG = 0 "
    sql += "AND T_COMN_MENU_GROUP.DISUSE_FLAG = 0 "

    if menu_id == "":
        data_list = objdbca.sql_execute(sql, [menuNameRest])
    else:
        data_list = objdbca.sql_execute(sql, [menu_id])
    data = []

    for data in data_list:
        if data is None or len(data) == 0:
            return []

    return data

def getParentMenuGroupInfo(menu_group_id, objdbca=None):
    """
    親メニューグループ情報取得

    Arguments:
        menuId: メニューグループID
        objdbca: DBオブジェクト
    Returns:
        実行結果
    """
    where = "WHERE MENU_GROUP_ID = %s AND DISUSE_FLAG = %s"
    data_list = objdbca.table_select("T_COMN_MENU_GROUP", where, [menu_group_id, 0])

    for data in data_list:
        if data is None or len(data) == 0:
            return []

    return data

def post_menu_import_upload(objdbca, organization_id, workspace_id, menu, body):
    """
        メニューアップロード
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu:menu_import
            body:リクエストのbody部
        RETRUN:
            result_data
    """
    lang = g.get('LANGUAGE')
    # upload_idの作成
    date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    upload_id = date + str(secrets.randbelow(9999999999))

    # パスの設定
    strage_path = os.environ.get('STORAGEPATH')
    import_menu_dir = strage_path + "/".join([organization_id, workspace_id]) + "/tmp/driver/import_menu"
    upload_dir_name = import_menu_dir + '/' + 'upload'
    import_dir_name = import_menu_dir + '/' + 'import'
    upload_id_path = upload_dir_name + '/' + upload_id
    import_id_path = import_dir_name + '/' + upload_id
    file_name = upload_id + '_ita_data.tar.gz'
    file_path = upload_dir_name + '/' + file_name
    if not os.path.isdir(upload_dir_name):
        os.makedirs(upload_dir_name)
        g.applogger.debug("made import_dir")

    # アップロードファイルbase64変換処理
    _decode_zip_file(file_path, body['base64'])

    # zip解凍
    with tarfile.open(file_path, 'r:gz') as tar:
        tar.extractall(path=upload_id_path)

    # zipファイルの中身を確認する
    _check_zip_file(upload_id, organization_id, workspace_id)

    # MENU_GROUPSファイル読み込み
    if os.path.isfile(import_id_path + '/MENU_GROUPS') is False:
        # 対象ファイルなし
        raise AppException("499-00905", [], [])
    with open(import_id_path + '/MENU_GROUPS') as f:
        menu_group_info = json.load(f)

    # ユーザが使用している言語に合わせてメニューグループ名、メニュー名を設定する
    for menu_groups in menu_group_info.values():
        for menu_group in menu_groups:
            menu_group['menu_group_name'] = menu_group['menu_group_name_' + lang.lower()]
            menus = menu_group['menus']
            for menu in menus:
                menu['menu_name'] = menu['menu_name_' + lang.lower()]

            # 親メニューグループ情報を取得
            parent_menu_group = {}
            parent_flg = False
            parent_id = menu_group['parent_id']
            if parent_id is not None:
                for data in menu_groups:
                    if parent_id == data['id']:
                        parent_flg = True

                # 親メニューグループがすでに追加されているか確認
                if parent_flg is False:
                    parent_menu_group_info = getParentMenuGroupInfo(parent_id, objdbca)
                    parent_menu_group['parent_id'] = None
                    parent_menu_group['id'] = parent_id
                    parent_menu_group['menu_group_name'] = parent_menu_group_info["MENU_GROUP_NAME_" + lang.upper()]
                    parent_menu_group['menu_group_name_ja'] = parent_menu_group_info["MENU_GROUP_NAME_JA"]
                    parent_menu_group['menu_group_name_en'] = parent_menu_group_info["MENU_GROUP_NAME_EN"]
                    parent_menu_group["disp_seq"] = parent_menu_group_info["DISP_SEQ"]
                    parent_menu_group['menus'] = []

                    menu_groups.append(parent_menu_group)

    if os.path.isfile(import_id_path + '/DP_INFO') is False:
        # 対象ファイルなし
        raise AppException("499-00905", [], [])

    # DP_INFOファイル読み込み
    with open(import_id_path + '/DP_INFO') as f:
        dp_info_file = json.load(f)
    dp_mode = dp_info_file['DP_MODE']
    abolished_type = dp_info_file['ABOLISHED_TYPE']
    specified_time = dp_info_file['SPECIFIED_TIMESTAMP']

    result_data = {
        'upload_id': upload_id,
        'file_name': body['name'],
        'mode': dp_mode,
        'abolished_type': abolished_type,
        'specified_time': specified_time,
        'import_list': menu_group_info
    }

    return result_data

def execute_menu_import(objdbca, organization_id, workspace_id, menu, body):
    """
        メニューインポート実行
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu:menu_import
            body:リクエストのbody部
        RETRUN:
            result_data
    """
    # パスの設定
    strage_path = os.environ.get('STORAGEPATH')
    import_menu_dir = strage_path + "/".join([organization_id, workspace_id]) + "/tmp/driver/import_menu"
    dir_name = import_menu_dir + '/import'

    menu_name_rest_list = body['menu']
    upload_id = body['upload_id']
    file_name = body['file_name']

    upload_dir_name = upload_id.replace('A_', '')
    import_path = dir_name + '/' + upload_dir_name

    import_list = ",".join(menu_name_rest_list)

    if os.path.isfile(import_path + '/DP_INFO') is False:
        # 対象ファイルなし
        raise AppException("499-00905", [], [])

    # DP_INFOファイル読み込み
    with open(import_path + '/DP_INFO') as f:
        dp_info_file = json.load(f)

    dp_info = _check_dp_info(objdbca, menu, dp_info_file)

    result_data = _menu_import_execution_from_rest(objdbca, menu, dp_info, import_path, file_name, import_list)

    return result_data

def _menu_import_execution_from_rest(objdbca, menu, dp_info, import_path, file_name, import_list):
    # メニューインポート登録処理
    # データインポート管理テーブル更新処理
    # 変数定義
    lang = g.get('LANGUAGE')
    user_id = g.get('USER_ID')

    # テーブル名
    t_dp_status_master = 'T_DP_STATUS_MASTER'
    t_dp_execution_type = 'T_DP_EXECUTION_TYPE'

    specified_time = dp_info['SPECIFIED_TIMESTAMP']
    dp_mode_name = dp_info['DP_MODE_NAME']
    abolished_type_name = dp_info['ABOLISHED_TYPE_NAME']

    try:
        # トランザクション開始
        objdbca.db_transaction_start()

        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'menu_export_import_list')  # noqa: F405
        if objmenu.get_objtable() is False:
            log_msg_args = ["not menu or table"]
            api_msg_args = ["not menu or table"]
            raise AppException("401-00001", log_msg_args, api_msg_args) # noqa: F405

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
        ret_dp_execution_type = objdbca.table_select(t_dp_execution_type, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [2, 0])
        if not ret_dp_execution_type:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

        execution_type = ret_dp_execution_type[0].get('EXECUTION_TYPE_NAME_' + lang.upper())

        user_name = util.get_user_name(user_id)

        # 登録用パラメータを作成
        parameters = {
            "file": {
                "file_name": file_encode(import_path + '_ita_data.tar.gz')
            },
            "parameter": {
                "status": status,
                "execution_type": execution_type,
                "mode": dp_mode_name,
                "abolished_type": abolished_type_name,
                "specified_time": specified_time,
                "file_name": file_name,
                "execution_user": user_name,
                "json_storage_item": import_list,
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

    # import_menu/import/アップロードIDのディレクトリを削除する
    if os.path.isdir(import_path):
        shutil.rmtree(import_path)

    is_file = os.path.isfile(import_path + '_ita_data.tar.gz')
    if is_file is True:
        os.remove(import_path + '_ita_data.tar.gz')

    # 返却用の値を取得
    execution_no = exec_result[1].get('execution_no')

    result_data = {'execution_no': execution_no}

    return result_data

def _check_dp_info(objdbca, menu, dp_info_file):
    # DP_INFOファイルの中身が正常がチェックする
    # 変数定義
    lang = g.get('LANGUAGE')

    # テーブル名
    t_dp_mode = 'T_DP_MODE'
    t_dp_abolished_type = 'T_DP_ABOLISHED_TYPE'

    dp_mode = dp_info_file['DP_MODE']
    abolished_type = dp_info_file['ABOLISHED_TYPE']
    specified_time = dp_info_file['SPECIFIED_TIMESTAMP']

    # 『モードマスタ』テーブルから対象のデータを取得
    # 形式名を取得
    ret_dp_status = objdbca.table_select(t_dp_mode, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [dp_mode, 0])
    if not ret_dp_status:
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

    dp_mode_name = ret_dp_status[0].get('MODE_NAME_' + lang.upper())

    # 『廃止情報マスタ』テーブルから対象のデータを取得
    # 形式名を取得
    ret_dp_abolished_type = objdbca.table_select(t_dp_abolished_type, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [abolished_type, 0])
    if not ret_dp_abolished_type:
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

    abolished_type_name = ret_dp_abolished_type[0].get('ABOLISHED_TYPE_NAME_' + lang.upper())

    if dp_mode != 2:
        specified_time = None

    result_data = {
        'DP_MODE': dp_mode,
        'DP_MODE_NAME': dp_mode_name,
        'ABOLISHED_TYPE': abolished_type,
        'ABOLISHED_TYPE_NAME': abolished_type_name,
        'SPECIFIED_TIMESTAMP': specified_time,
    }

    return result_data

def _create_import_list(objdbca, menu_name_rest_list):
    # テーブル名
    t_common_menu = 'T_COMN_MENU'
    t_common_menu_group = 'T_COMN_MENU_GROUP'

    # 変数定義
    lang = g.get('LANGUAGE')

    # 『メニュー管理』テーブルから対象メニューを取得
    ret_menu = objdbca.table_select(t_common_menu, 'WHERE MENU_NAME_REST IN %s AND DISUSE_FLAG = %s', [menu_name_rest_list, 0])

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

def _check_zip_file(upload_id, organization_id, workspace_id):
    """
        zipファイルの中身を確認する

        args:
            upload_id: アップロードID
    """
    fileName = upload_id + '_ita_data.tar.gz'
    uploadPath = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/tmp/driver/import_menu/upload/"
    importPath = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/tmp/driver/import_menu/import/"

    lst = os.listdir(uploadPath + upload_id)

    fileAry = []
    for value in lst:
        if not value == '.' and not value == '..':
            path = os.path.join(uploadPath + upload_id, value)
            if os.path.isdir(path):
                dir_name = value
                sublst = os.listdir(path)
                for subvalue in sublst:
                    if not subvalue == '.' and not subvalue == '..':
                        fileAry.append(dir_name + "/" + subvalue)
            else:
                fileAry.append(value)

    if len(fileAry) == 0:
        if os.path.exists(uploadPath + fileName):
            os.remove(uploadPath + fileName)

        msgstr = g.appmsg.get_api_message("MSG-30030")
        log_msg_args = [msgstr]
        api_msg_args = [msgstr]
        raise AppException("499-00005", log_msg_args, api_msg_args)

    # 必須ファイルの確認
    errCnt = 0
    errFlg = True
    needleAry = ['MENU_NAME_REST_LIST', 'DP_INFO']
    for value in fileAry:
        if value in needleAry:
            errFlg = False

    if errFlg:
        errCnt += 1
        msgstr = g.appmsg.get_api_message("MSG-30031")
        log_msg_args = [msgstr]
        api_msg_args = [msgstr]
        raise AppException("499-00005", log_msg_args, api_msg_args)

    if errCnt > 0:
        if os.path.exists(uploadPath + fileName):
            os.remove(uploadPath + fileName)

        shutil.rmtree(uploadPath + upload_id)

        msgstr = g.appmsg.get_api_message("MSG-30030")
        log_msg_args = [msgstr]
        api_msg_args = [msgstr]
        raise AppException("499-00005", log_msg_args, api_msg_args)

    # バージョン差異チェック
    common_db = DBConnectCommon()
    version_data = _collect_ita_version(common_db)

    export_version = ''
    if os.path.isfile(uploadPath + upload_id + '/VERSION'):
        # エクスポート時のバージョンを取得
        export_version = Path(uploadPath + upload_id + '/VERSION').read_text(encoding='utf-8')

    if version_data["version"] != export_version:
        # エクスポート時のバージョンとインポートする環境のバージョンが違う場合はエラー
        shutil.rmtree(uploadPath + upload_id)
        msgstr = g.appmsg.get_api_message("MSG-30035")
        log_msg_args = [msgstr]
        api_msg_args = [msgstr]
        raise AppException("499-00701", log_msg_args, api_msg_args)

    # ファイル移動
    if not os.path.exists(importPath):
        os.makedirs(importPath)
        os.chmod(importPath, 0o777)

    shutil.copy(uploadPath + fileName, importPath + fileName)
    os.makedirs(importPath + upload_id)
    os.chmod(importPath + upload_id, 0o777)
    from_path = uploadPath + upload_id
    to_path = importPath + '.'
    cmd = "cp -frp " + from_path + ' ' + to_path
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)

    errCnt = 0
    declare_check_list = []
    for value in fileAry:
        file = importPath + upload_id + '/' + value
        if not os.path.exists(file):
            errCnt += 1
            break

        if not file == "":
            tmpFileAry = file.split("/")
            tmpFileName = tmpFileAry[len(tmpFileAry) - 1]
            declare_check_list.append(tmpFileName)

    declare_list = collections.Counter(declare_check_list)
    for value in fileAry:
        file = importPath + upload_id + '/' + value
        if value.endswith(".xlsx"):
            continue

        if not os.path.exists(file):
            errCnt += 1
            break

        if not file:
            cmd = "rm -rf " + importPath + upload_id
            ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if ret.returncode != 0:
                return False

    if errCnt > 0:
        if os.path.exists(uploadPath + fileName):
            os.remove(uploadPath + fileName)

        if os.path.exists(importPath + fileName):
            os.remove(importPath + fileName)

        cmd = "rm -rf " + uploadPath + upload_id + " 2>&1"
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if ret.returncode != 0:
            msgstr = g.appmsg.get_api_message("MSG-30029")
            log_msg_args = [msgstr]
            api_msg_args = [msgstr]
            raise AppException("499-00005", log_msg_args, api_msg_args)

        cmd = "rm -rf " + importPath + upload_id + " 2>&1"
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if ret.returncode != 0:
            msgstr = g.appmsg.get_api_message("MSG-30029")
            log_msg_args = [msgstr]
            api_msg_args = [msgstr]
            raise AppException("499-00005", log_msg_args, api_msg_args)

        msgstr = g.appmsg.get_api_message("MSG-30030")
        log_msg_args = [msgstr]
        api_msg_args = [msgstr]
        raise AppException("499-00005", log_msg_args, api_msg_args)

    # アップロードファイル削除
    cmd = "rm " + uploadPath + fileName
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if ret.returncode != 0:
        raise AppException("499-01301", [], [])

    cmd = "rm -rf " + uploadPath + upload_id + " 2>&1"
    ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if ret.returncode != 0:
        raise AppException("499-01301", [], [])

    return declare_list

def _collect_ita_version(common_db):
    """
        ITAのバージョン情報を取得する
        ARGS:
            common_db:DB接クラス  DBConnectCommon()
        RETRUN:
            version_data
    """

    # 変数定義
    lang = g.get('LANGUAGE')

    # 『バージョン情報』テーブルからバージョン情報を取得
    ret = common_db.table_select('T_COMN_VERSION', 'WHERE DISUSE_FLAG = %s', [0])

    # 件数確認
    if len(ret) != 1:
        raise AppException("499-00601")

    if lang == 'ja':
        installed_driver = json.loads(ret[0].get('INSTALLED_DRIVER_JA'))
    else:
        installed_driver = json.loads(ret[0].get('INSTALLED_DRIVER_EN'))

    version_data = {
        "version": ret[0].get('VERSION'),
        "installed_driver": installed_driver
    }

    return version_data

def _decode_zip_file(file_path, base64Data):
    # アップロードファイルbase64変換処理
    upload_file_decode = base64.b64decode(base64Data.encode('utf-8'))

    # ファイル移動
    Path(file_path).write_bytes(upload_file_decode)

    # ファイルタイプの取得、判定
    file_mimetype, encoding = mimetypes.guess_type(file_path)
    if file_mimetype != 'application/x-gzip':
        return False

    return True

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