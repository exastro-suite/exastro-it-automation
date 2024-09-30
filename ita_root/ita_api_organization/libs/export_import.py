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

from flask import g

import json
import subprocess
import shutil
import collections
import re
import zipfile

import base64
import datetime
import tarfile
import mimetypes
import secrets
from packaging import version

from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import DBConnectCommon
from common_libs.loadtable import *  # noqa: F403
from common_libs.common import storage_access
from common_libs.column import *  # noqa: F403
from common_libs.common.util import print_exception_msg, get_ita_version

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
    t_dp_journal_type = 'T_DP_JOURNAL_TYPE'

    try:
        # トランザクション開始
        objdbca.db_transaction_start()

        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'menu_export_import_list')  # noqa: F405
        if objmenu.get_objtable() is False:
            log_msg_args = ["not menu or table"]
            api_msg_args = ["not menu or table"]
            raise AppException("401-00001", log_msg_args, api_msg_args)  # noqa: F405

        body_specified_time = None
        body_mode = body.get('mode')
        body_abolished_type = body.get('abolished_type')
        body_journal_type = body.get('journal_type') if body.get('journal_type') is not None else "1"
        if body_mode == '2':
            # 日付のフォーマットチェック
            chk_date = body.get('specified_timestamp')
            try:
                chk_date = datetime.datetime.strptime(chk_date, '%Y/%m/%d %H:%M')
            except Exception:
                raise AppException("499-01501")  # noqa: F405
            body_specified_time = body.get('specified_timestamp')

        # journal_type 設定時のチェック
        if body_journal_type not in ['1', '2']:
            log_msg_args = "body_journal_type not in ['1', '2']"
            api_msg_args = "body_journal_type not in ['1', '2']"
            raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405 ###

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

        # 『履歴情報マスタ』テーブルから対象のデータを取得
        # 形式名を取得
        ret_dp_journal_type = objdbca.table_select(t_dp_journal_type, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [body_journal_type, 0])
        if not ret_dp_journal_type:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

        journal_type = ret_dp_journal_type[0].get('JOURNAL_TYPE_NAME_' + lang.upper(), "1")

        user_name = util.get_user_name(user_id)

        # 登録用パラメータを作成
        parameters = {
            "parameter": {
                "status": status,
                "execution_type": execution_type,
                "mode": mode,
                "abolished_type": abolished_type,
                "specified_time": body_specified_time,
                "journal_type": journal_type,
                "file_name": None,
                "execution_user": user_name,
                "language": lang,
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
        raise e

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
            raise AppException("499-00701", [result_msg])  # loadTableバリデーションエラー

        # コミット/トランザクション終了
        objdbca.db_transaction_end(True)

    except AppException as e:
        print_exception_msg(e)
        # ロールバック トランザクション終了
        objdbca.db_transaction_end(False)

        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args, None

    # 返却用の値を取得
    execution_no = exec_result[1].get('execution_no')

    result_data = {'execution_no': execution_no}

    return result_data

def execute_excel_bulk_upload(organization_id, workspace_id, body, objdbca, path_data):
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

    upload_id = path_data["upload_id"]

    fileName = upload_id + '_ita_data.zip'

    # ファイル保存
    uploadFilePath = path_data["file_path"]
    uploadPath = path_data["upload_path"]
    importPath = path_data["import_path"]

    # zip解凍
    # 解凍はtmp配下で行う
    tmp_dir_path = "/tmp/{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID')) + "/upload"
    if os.path.isdir(tmp_dir_path) is False:
        os.makedirs(tmp_dir_path)
        os.chmod(tmp_dir_path, 0o777)
    shutil.copy2(uploadPath + fileName, tmp_dir_path)

    ret = unzip_file(fileName, tmp_dir_path, upload_id)

    if ret is False:
        unzip_file_cmd(fileName, tmp_dir_path, upload_id)

    shutil.copytree(tmp_dir_path + "/" + upload_id, uploadPath + upload_id)

    # tmp配下のファイル削除
    shutil.rmtree(tmp_dir_path)

    # zipファイルの中身確認
    declare_list = checkZipFile(upload_id, organization_id, workspace_id)

    # メニューリストの取得
    tmpRetImportAry = makeImportCheckbox(declare_list, upload_id, organization_id, workspace_id, objdbca)
    if len(tmpRetImportAry) == 0:
        # ファイルの削除
        cmd = "rm -rf " + importPath + upload_id
        ret = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        raise AppException("499-01305", [], [])

    # zipファイル削除
    os.remove(importPath + fileName)

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
    arrayResult["data_portability_upload_file_name"] = path_data["upload_file_name"]

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
        print_exception_msg(e)
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

def unzip_file(fileName, tmp_dir_path, upload_id):
    """
        zipファイルを解凍する

        args:
            fileName: ファイル名
            uploadPath: 解凍先パス
            upload_id: アップロードID
    """

    try:
        with zipfile.ZipFile(tmp_dir_path + "/" + fileName) as z:
            for info in z.infolist():
                info.filename = info.orig_filename.encode('cp437').decode('cp932')
                if os.sep != "/" and os.sep in info.filename:
                    info.filename = info.filename.replace(os.sep, "/")
                z.extract(info, path=tmp_dir_path + "/" + upload_id)

    except Exception as e:
        print_exception_msg(e)
        return False

    return True

def unzip_file_cmd(fileName, tmp_dir_path, upload_id):
    """
        zipファイルを解凍する(コマンド)

        args:
            fileName: ファイル名
            uploadPath: 解凍先パス
            upload_id: アップロードID
    """
    # tmp配下で解凍する
    to_path = tmp_dir_path + "/" + upload_id
    from_path = tmp_dir_path + "/" + fileName
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

    file_read = storage_access.storage_read()
    file_read.open(uploadPath + upload_id + "/MENU_LIST.txt")
    tmp_menu_list = file_read.read()
    file_read.close()
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

    # /storage配下のファイルアクセスを/tmp経由で行うモジュール
    file_read_text = storage_access.storage_read_text()

    # 取得したいFILEリストの取得
    menuIdFile = file_read_text.read_text(path + upload_id + '/MENU_LIST.txt')

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

def post_menu_import_upload(objdbca, organization_id, workspace_id, menu, body, path_data):
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
    upload_id = path_data["upload_id"]


    # パスの設定
    upload_dir_name = path_data["upload_dir_name"]
    upload_id_path = path_data["upload_path"]
    import_id_path = path_data["import_path"]
    file_path = path_data['file_path']
    if not os.path.isdir(upload_dir_name):
        os.makedirs(upload_dir_name)
        g.applogger.debug("made import_dir")

    clear_file_list = [
        upload_dir_name,
        upload_id_path,
        import_id_path,
        file_path
    ]

    try:
        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'menu_export_import_list')  # noqa: F405
        if objmenu.get_objtable() is False:
            log_msg_args = ["not menu or table"]
            api_msg_args = ["not menu or table"]
            raise AppException("401-00001", log_msg_args, api_msg_args) # noqa: F405

        objcolumn = FileUploadColumn(objdbca, objmenu.objtable, "file_name", '')

        try:
            # アップロードファイルbase64変換処理

            # zip解凍
            with tarfile.open(file_path, 'r:gz') as tar:
                tar.extractall(path=upload_id_path)
        except Exception as e:
            # アップロードファイルのbase64変換～zip解凍時
            trace_msg = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
            log_msg_args = [path_data['file_name']]
            api_msg_args = [path_data['file_name']]
            raise AppException("499-01503", log_msg_args, api_msg_args)  # noqa: F405

        # zipファイルの中身を確認する
        _check_zip_file(upload_id, organization_id, workspace_id)

        # インストールドライバと、kymのドライバ確認
        # DRIVERSファイル読み込み
        if os.path.isfile(import_id_path + '/DRIVERS') is False:
            log_msg_args = ["DRIVERS", path_data['file_name']]
            api_msg_args = ["DRIVERS", path_data['file_name']]
            # 対象ファイルなし
            raise AppException("499-01504", log_msg_args, api_msg_args)  # noqa: F405

        file_read = storage_access.storage_read()
        file_read.open(import_id_path + '/DRIVERS')
        kym_drivers = json.loads(file_read.read())
        file_read.close()

        # インストールドライバを取得
        common_db = DBConnectCommon()
        version_data = get_ita_version(common_db)
        ita_drivers = list(version_data["installed_driver_en"].keys())
        no_installed_driver = version_data["no_installed_driver"] if "no_installed_driver" in version_data else []
        [ita_drivers.remove(nid) for nid in no_installed_driver if nid in ita_drivers]
        default_installed_driver = version_data["default_installed_driver"] if "default_installed_driver" in version_data else []
        common_db.db_disconnect()

        # ドライバ確認
        no_kym_driver = [_d for _d in kym_drivers if _d not in ita_drivers] \
            if isinstance(kym_drivers, list) and isinstance(ita_drivers, list) else []

        # インストールドライバが不足している場合
        if len(no_kym_driver) != 0:
            [no_kym_driver.remove(_dd) for _dd in default_installed_driver if _dd in no_kym_driver]
            no_kym_driver_log = ",".join(no_kym_driver)
            no_kym_driver_lang = "\n".join([f'・{version_data["installed_driver"].get(ndk)}' for ndk in no_kym_driver])
            log_msg_args = [no_kym_driver_log]
            api_msg_args = [no_kym_driver_lang]
            raise AppException("499-01505",log_msg_args, api_msg_args)  # noqa: F405

        # MENU_GROUPSファイル読み込み
        if os.path.isfile(import_id_path + '/MENU_GROUPS') is False:
            # 対象ファイルなし
            raise AppException("499-00905", [], [])
        file_read = storage_access.storage_read()
        file_read.open(import_id_path + '/MENU_GROUPS')
        menu_group_info = json.loads(file_read.read())
        file_read.close()

        # PARENT_MENU_GROUPSファイル読み込み
        if os.path.isfile(import_id_path + '/PARENT_MENU_GROUPS') is False:
            # 対象ファイルなし
            raise AppException("499-00905", [], [])
        file_read = storage_access.storage_read()
        file_read.open(import_id_path + '/PARENT_MENU_GROUPS')
        parent_menu_group_info = json.loads(file_read.read())
        file_read.close()

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
                        parent_menu_group['parent_id'] = None
                        parent_menu_group['id'] = parent_id
                        parent_menu_group['menu_group_name'] = parent_menu_group_info[parent_id]["MENU_GROUP_NAME_" + lang.upper()]
                        parent_menu_group['menu_group_name_ja'] = parent_menu_group_info[parent_id]["MENU_GROUP_NAME_JA"]
                        parent_menu_group['menu_group_name_en'] = parent_menu_group_info[parent_id]["MENU_GROUP_NAME_EN"]
                        parent_menu_group["disp_seq"] = parent_menu_group_info[parent_id]["DISP_SEQ"]
                        parent_menu_group['menus'] = []

                        menu_groups.append(parent_menu_group)

        if os.path.isfile(import_id_path + '/DP_INFO') is False:
            # 対象ファイルなし
            raise AppException("499-00905", [], [])

        # DP_INFOファイル読み込み
        file_read = storage_access.storage_read()
        file_read.open(import_id_path + '/DP_INFO')
        dp_info_file = json.loads(file_read.read())
        file_read.close()
        dp_mode = dp_info_file['DP_MODE']
        abolished_type = dp_info_file['ABOLISHED_TYPE']
        specified_time = dp_info_file['SPECIFIED_TIMESTAMP']

        result_data = {
            'upload_id': upload_id,
            'file_name': path_data["upload_file_name"],
            'mode': dp_mode,
            'abolished_type': abolished_type,
            'specified_time': specified_time,
            'import_list': menu_group_info
        }

        journal_type = dp_info_file['JOURNAL_TYPE'] if 'JOURNAL_TYPE' in dp_info_file else "1"
        result_data["journal_type"] = journal_type

    except Exception as e:
        trace_msg = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
        # 展開したファイル等削除
        clear_file_list.append(
            upload_dir_name.replace("/driver/import_menu/upload", "/driver/import_menu/import")
        )
        clear_files(clear_file_list, "all")
        raise e
    finally:
        # 展開したファイル等削除
        clear_files(clear_file_list)

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

    clear_file_list = [
        import_path,
        import_path + '_ita_data.tar.gz'
    ]

    import_list = ",".join(menu_name_rest_list)

    try:
        if os.path.isfile(import_path + '/DP_INFO') is False:
            # 対象ファイルなし
            raise AppException("499-00905", [], [])

        # DP_INFOファイル読み込み
        file_read = storage_access.storage_read()
        file_read.open(import_path + '/DP_INFO')
        dp_info_file = json.loads(file_read.read())
        file_read.close()

        dp_info = _check_dp_info(objdbca, menu, dp_info_file)

        result_data = _menu_import_execution_from_rest(objdbca, menu, dp_info, import_path, file_name, import_list)

    except Exception as e:
        trace_msg = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(trace_msg)))
        raise e
    finally:
        # 展開したファイル等削除
        clear_files(clear_file_list, "all")

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

    journal_type_name = dp_info['JOURNAL_TYPE_NAME']

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

        objcolumn = FileUploadColumn(objdbca, objmenu.objtable, "file_name", '')
        tar_file_path = import_path + '_ita_data.tar.gz'
        option = {"file_path": tar_file_path}
        valid_result = objcolumn.check_basic_valid(file_name, option)
        if valid_result[0] is False:
            log_msg_args = [valid_result[1]]
            api_msg_args = [valid_result[1]]
            raise AppException("499-01502", log_msg_args, api_msg_args)  # noqa: F405

        # 登録用パラメータを作成
        parameters = {
            "parameter": {
                "status": status,
                "execution_type": execution_type,
                "mode": dp_mode_name,
                "abolished_type": abolished_type_name,
                "specified_time": specified_time,
                "file_name": file_name,
                "execution_user": user_name,
                "language": lang,
                "json_storage_item": import_list,
                "discard": "0"
            },
            "type": "Register"
        }
        parameters["parameter"]["journal_type"] = journal_type_name
        file_paths = {
            "file_name": tar_file_path
        }
        # 登録を実行
        exec_result = objmenu.exec_maintenance(parameters, "", "", False, False, True, record_file_paths=file_paths)  # noqa: E999
        if not exec_result[0]:
            result_msg = _format_loadtable_msg(exec_result[2])
            result_msg = json.dumps(result_msg, ensure_ascii=False)
            raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー

        # コミット/トランザクション終了
        objdbca.db_transaction_end(True)

    except AppException as e:
        # ロールバック トランザクション終了
        objdbca.db_transaction_end(False)
        raise e
    except Exception as e:
        print_exception_msg(e)
        # ロールバック トランザクション終了
        objdbca.db_transaction_end(False)

        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args, None

    try:
        # import_menu/import/アップロードIDのディレクトリを削除する
        if os.path.isdir(import_path):
            shutil.rmtree(import_path)
    except Exception as e:
        g.applogger.info("Failed to delete: {} ({})".format(e, import_path))

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
    t_dp_journal_type = 'T_DP_JOURNAL_TYPE'

    dp_mode = dp_info_file['DP_MODE']
    abolished_type = dp_info_file['ABOLISHED_TYPE']
    journal_type = dp_info_file['JOURNAL_TYPE'] if 'JOURNAL_TYPE' in dp_info_file else "1"
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

    # 『履歴情報マスタ』テーブルから対象のデータを取得
    # 形式名を取得
    ret_dp_journal_type = objdbca.table_select(t_dp_journal_type, 'WHERE ROW_ID = %s AND DISUSE_FLAG = %s', [journal_type, 0])
    if not ret_dp_journal_type:
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException("499-00005", log_msg_args, api_msg_args)  # noqa: F405

    journal_type_name = ret_dp_journal_type[0].get('JOURNAL_TYPE_NAME_' + lang.upper(), "1")

    if dp_mode != '2':
        specified_time = None

    result_data = {
        'DP_MODE': dp_mode,
        'DP_MODE_NAME': dp_mode_name,
        'ABOLISHED_TYPE': abolished_type,
        'ABOLISHED_TYPE_NAME': abolished_type_name,
        'SPECIFIED_TIMESTAMP': specified_time,
    }
    result_data["JOURNAL_TYPE"] = journal_type
    result_data["JOURNAL_TYPE_NAME"] = journal_type_name

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

    # /storage配下のファイルアクセスを/tmp経由で行うモジュール
    file_read_text = storage_access.storage_read_text()

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
        export_version = file_read_text.read_text(uploadPath + upload_id + '/VERSION')

    # バージョン確認
    ita_version = version_data["version"]
    kym_version = export_version
    # 2.5.0以下の場合
    if not (version.parse("2.5.0") <= version.parse(kym_version)):
        shutil.rmtree(uploadPath + upload_id)
        msgstr = g.appmsg.get_api_message("MSG-140012", [kym_version])
        log_msg_args = [msgstr]
        api_msg_args = [msgstr]
        raise AppException("499-00701", log_msg_args, api_msg_args)
    # KYM > ITAの場合
    if (version.parse(ita_version) < version.parse(kym_version)):
        shutil.rmtree(uploadPath + upload_id)
        raise AppException("499-01506", [kym_version, ita_version], [kym_version, ita_version])

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
    # /storage配下のファイルアクセスを/tmp経由で行うモジュール
    file_write = storage_access.storage_write()

    # アップロードファイルbase64変換処理
    upload_file_decode = base64.b64decode(base64Data.encode('utf-8'))

    # ファイル移動
    file_write.open(file_path, mode="wb")
    file_write.write(upload_file_decode)
    file_write.close()

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

def generate_path_data(organization_id, workspace_id, excel=False):
    """
    Args:
        organization_id
        workspace_id
        excel

    Returns:
        dict
    """
    storage_path = os.environ.get('STORAGEPATH')
    base_path = f"{storage_path}{organization_id}/{workspace_id}"
    date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    upload_id = date + str(secrets.randbelow(9999999999))


    if excel:
        file_name = upload_id + "_ita_data.zip"
        menu_path = "/tmp/bulk_excel/import"
        upload_path = base_path + menu_path + "/upload/"
        import_path = base_path + menu_path + "/import/"
        file_path = upload_path + file_name
        upload_dir_name = ""
        os.makedirs(upload_path, exist_ok=True)
    else:
        file_name = upload_id + "_ita_data.tar.gz"
        menu_path ="/tmp/driver/import_menu"
        upload_dir_name = base_path + menu_path + "/upload"
        upload_path = upload_dir_name + "/" + upload_id
        import_path = base_path + menu_path + "/import" + "/" + upload_id
        file_path = upload_dir_name + "/" + file_name
        os.makedirs(upload_dir_name, exist_ok=True)


    path_data = {
        "upload_id": upload_id,
        "file_path": file_path,
        "upload_dir_name": upload_dir_name,
        "upload_path": upload_path,
        "import_path": import_path,
        "file_name": file_name
    }

    return path_data


def create_upload_parameters(connexion_request, key_name, organization_id, workspace_id, excel=False):
    """
    create_upload_parameters
        Use connexion.request
            - application/json
            - multipart/form-data
        Parameter generation from xxxx
            - application/json
                connexion.request.get_json()
            - multipart/form-data
                connexion_request.files
            => { "key_name": { "name":"", "base64":"" }}
    Arguments:
        connexion_request: connexion.request
    Returns:
        bool, upload_data,
    """

    upload_data = {}
    # if connexion_request:
    if connexion_request.is_json:
        # application/json
        upload_data = dict(connexion_request.get_json())
    elif connexion_request.files:
        # get files & set parameter['file'][rest_name]
        # ファイルが保存できる容量があるか確認
        file_size = connexion_request.headers.get("Content-Length")
        file_size_str = f"{int(file_size):,} byte(s)"
        storage = storage_base()
        can_save, free_space = storage.validate_disk_space(file_size)
        if can_save is False:
            status_code = "499-00222"
            log_msg_args = [file_size_str]
            api_msg_args = [file_size_str]
            raise AppException(status_code, log_msg_args, api_msg_args)

        for _file_key in connexion_request.files:
            # set key_name -> name, base64
            _file_data = connexion_request.files[_file_key]
            upload_data.setdefault(key_name, {})

            path_data = generate_path_data(organization_id, workspace_id, excel)
            path_data["upload_file_name"] = _file_data.filename
            file_path = path_data["file_path"]
            f = open(file_path, "wb")
            while True:
                # fileの読み込み
                buf = _file_data.stream.read(1000000)
                if len(buf) == 0:
                    break
                # yield buf
                # fileの書き込み
                f.write(buf)
            f.close()


    else:
        return False, {},

    return True, upload_data, path_data

def clear_files(clear_path_list, mode="tmp_only"):
    if mode == "tmp_only":
        clear_path_list = [_path.replace("/storage/", "/tmp/") for _path in clear_path_list]
    else:
        # add /storage -> /tmp
        _clear_path_list = []
        [_clear_path_list.append(_path.replace("/storage/", "/tmp/")) for _path in clear_path_list]
        clear_path_list.extend(_clear_path_list)

    for _path in clear_path_list:
        try:
            if os.path.isfile(_path):
                os.remove(_path)
                g.applogger.debug(f"delete file: {_path}")
            elif os.path.isdir(_path):
                shutil.rmtree(_path)
                g.applogger.debug(f"delete dir: {_path}")
        except Exception as e:
            g.applogger.info(f"Failed to delete: {e} ({_path})")