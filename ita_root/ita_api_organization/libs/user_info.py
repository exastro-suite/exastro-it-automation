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
import datetime
from common_libs.common import *  # noqa: F403
from flask import g
from libs.organization_common import check_auth_menu, get_auth_menus
from common_libs.common.exception import AppException


def collect_menu_group_panels(objdbca):
    """
        メニューグループの画像を取得する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            panels_data
    """
    # テーブル名
    t_common_menu = 'T_COMN_MENU'
    t_common_menu_group = 'T_COMN_MENU_GROUP'

    # 変数定義
    workspace_id = g.get('WORKSPACE_ID')
    menu_group_list_id = '10102'  # 「メニューグループ管理」メニューのID
    column_name_rest = 'menu_group_icon'  # カラム名

    # 『メニュー管理』テーブルからメニューの一覧を取得
    menu_list = objdbca.table_select(t_common_menu, 'WHERE DISUSE_FLAG = %s ORDER BY MENU_GROUP_ID ASC, DISP_SEQ ASC', [0])

    # 『メニューグループ管理』テーブルからメニューグループの一覧を取得
    menu_group_list = objdbca.table_select(t_common_menu_group, 'WHERE DISUSE_FLAG = %s ORDER BY DISP_SEQ ASC', [0])

    menu_rest_names = []
    for recode in menu_list:
        menu_rest_names.append(recode.get('MENU_NAME_REST'))

    auth_menu_list = get_auth_menus(menu_rest_names, objdbca)

    menu_groups = []
    for menu_item in auth_menu_list:
        # 権限のあるメニューのメニューグループを格納
        menu_group_id = menu_item.get('MENU_GROUP_ID')
        menu_groups.append(menu_group_id)

        # 親メニューグループも格納
        for recode in menu_group_list:
            if menu_group_id == recode.get('MENU_GROUP_ID'):
                if recode.get('PARENT_MENU_GROUP_ID') is not None and len(recode.get('PARENT_MENU_GROUP_ID')) != 0:
                    menu_groups.append(recode.get('PARENT_MENU_GROUP_ID'))
                break

    # 重複を除外
    menu_groups = list(set(menu_groups))

    panels_data = {}
    for recode in menu_group_list:
        # メニューグループに権限のあるメニューが1つもない場合は除外
        menu_group_id = recode.get('MENU_GROUP_ID')
        if menu_group_id not in menu_groups:
            continue

        # 対象ファイルの格納先を取得
        file_name = recode.get('MENU_GROUP_ICON')
        file_paths = get_upload_file_path(workspace_id, menu_group_list_id, menu_group_id, column_name_rest, file_name, '')  # noqa: F405

        # 対象ファイルをbase64エンコード
        encoded = file_encode(file_paths.get('file_path'))  # noqa: F405
        if not encoded:
            encoded = None

        panels_data[menu_group_id] = encoded

    return panels_data


def collect_user_auth(objdbca):
    """
        ユーザの権限情報を取得する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            user_auth_data
    """

    # ユーザIDを取得
    user_id = g.get('USER_ID')

    # ユーザ名を取得
    user_name = util.get_user_name(user_id)

    # workspaceに所属するロールを取得
    workspace_roles = util.get_workspace_roles()

    # ユーザが所属するロールのうち、workspaceに所属するロールを抽出
    roles = []
    for user_role in g.ROLES:
        if user_role in workspace_roles:
            roles.append(user_role)

    # Workspaceを取得
    workspaces = util.get_exastro_platform_workspaces()[0]

    # Webテーブル設定を取得
    ret = objdbca.table_select('T_COMN_WEB_TABLE_SETTINGS', 'WHERE USER_ID = %s', g.USER_ID)

    # メニューグループごとのメニュー一覧を作成
    if len(ret) == 0:
        web_table_settings = None
    else:
        if (ret[0]['WEB_TABLE_SETTINGS'] is None) or (len(ret[0]['WEB_TABLE_SETTINGS']) == 0):
            web_table_settings = None
        else:
            web_table_settings = json.loads(ret[0]['WEB_TABLE_SETTINGS'])

    user_auth_data = {
        "user_id": user_id,
        "user_name": user_name,
        "roles": roles,
        "workspaces": workspaces,
        "web_table_settings": web_table_settings
    }

    return user_auth_data


def collect_menus(objdbca, extra_flag=False):
    """
        ユーザがアクセス可能なメニューグループ・メニューの一覧を取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            menus_data
    """
    # テーブル名
    t_common_menu = 'T_COMN_MENU'
    t_common_menu_group = 'T_COMN_MENU_GROUP'

    # 変数定義
    lang = g.get('LANGUAGE')

    # 『メニュー管理』テーブルからメニューの一覧を取得
    ret = objdbca.table_select(t_common_menu, 'WHERE DISUSE_FLAG = %s ORDER BY MENU_GROUP_ID ASC, DISP_SEQ ASC', [0])

    # メニューグループごとのメニュー一覧を作成
    menu_rest_names = []
    for recode in ret:
        menu_rest_names.append(recode.get('MENU_NAME_REST'))

    auth_menu_list = get_auth_menus(menu_rest_names, objdbca)

    menus = {}
    for recode in auth_menu_list:
        menu_group_id = recode.get('MENU_GROUP_ID')
        if menu_group_id not in menus:
            menus[menu_group_id] = []

        add_menu = {}
        add_menu['id'] = recode.get('MENU_ID')
        add_menu['menu_name'] = recode.get('MENU_NAME_' + lang.upper())
        add_menu['menu_name_rest'] = recode.get('MENU_NAME_REST')
        add_menu['disp_seq'] = recode.get('DISP_SEQ')
        menus[menu_group_id].append(add_menu)

    # 『メニューグループ管理』テーブルからメニューグループの一覧を取得
    ret = objdbca.table_select(t_common_menu_group, 'WHERE DISUSE_FLAG = %s ORDER BY DISP_SEQ ASC', [0])

    # メニューグループの一覧を作成し、メニュー一覧も格納する
    menu_group_list = []
    for recode in ret:
        exclusion_flag = False
        # メニューグループに権限のあるメニューが1つもない場合は除外
        menu_group_id = recode.get('MENU_GROUP_ID')
        target_menus = menus.get(menu_group_id)
        if not target_menus:
            # 自分自身を親メニューグループとしているメニューグループを確認し、そのメニューグループに権限のあるメニューがあるかを確認
            for recode2 in ret:
                exclusion_flag = True
                parent_id = recode2.get('PARENT_MENU_GROUP_ID')
                if parent_id == menu_group_id:
                    child_menu_group_id = recode2.get('MENU_GROUP_ID')
                    child_target_menus = menus.get(child_menu_group_id)
                    if child_target_menus:
                        exclusion_flag = False
                        break
                else:
                    continue
        # exclusion_flagがTrueの場合は除外対象とする
        if exclusion_flag:
            continue

        if target_menus is None:
            target_menus = []

        add_menu_group = {}
        add_menu_group['parent_id'] = recode.get('PARENT_MENU_GROUP_ID')
        add_menu_group['id'] = menu_group_id
        add_menu_group['menu_group_name'] = recode.get('MENU_GROUP_NAME_' + lang.upper())
        add_menu_group['disp_seq'] = recode.get('DISP_SEQ')
        add_menu_group['menus'] = target_menus
        if extra_flag:
            add_menu_group['icon'] = recode.get('MENU_GROUP_ICON')
            add_menu_group['remarks'] = recode.get('NOTE')

        menu_group_list.append(add_menu_group)

    menus_data = {
        "menu_groups": menu_group_list,
    }

    return menus_data


def regist_table_settings(objdbca, parameter):
    """
        Webのテーブル設定を登録する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            parameter: bodyの中身
        RETRUN:
            data
    """
    # DBコネクション開始
    objdbca.db_transaction_start()

    # Webテーブル設定を取得
    ret = objdbca.table_select('T_COMN_WEB_TABLE_SETTINGS', 'WHERE USER_ID = %s', g.USER_ID)

    # メニューグループごとのメニュー一覧を作成

    data_list = {
        'USER_ID': g.USER_ID,
        'WEB_TABLE_SETTINGS': str(json.dumps(parameter)),
    }
    if len(ret) == 0:

        # Webテーブル設定にINSERT
        ret = objdbca.table_insert('T_COMN_WEB_TABLE_SETTINGS', data_list, 'ROW_ID', False)
    else:
        data_list['ROW_ID'] = ret[0]['ROW_ID']
        # Webテーブル設定にUPDATE
        ret = objdbca.table_update('T_COMN_WEB_TABLE_SETTINGS', data_list, 'ROW_ID', False)

    # DBコネクション終了
    objdbca.db_transaction_end(True)

    return g.appmsg.get_api_message("000-00001")


def collect_widget_settings(objdbca):
    """
        Dashboardのwidget設定を取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            widget_data
    """

    def get_conductor_info(objdbca, status_list, lang, days=None):

        if isinstance(lang, str) is False:
            lang = 'EN'

        lang = lang.upper()

        sql = (
            "SELECT TAB_A.CONDUCTOR_INSTANCE_ID, "
            "       IFNULL(TAB_A.TIME_END, TAB_A.LAST_UPDATE_TIMESTAMP) TIME_END, "
            "       TAB_A.I_CONDUCTOR_NAME, "
            "       TAB_A.I_OPERATION_NAME, "
            "       TAB_A.TIME_BOOK, "
            "       TAB_B.STATUS_NAME_%s STATUS_NAME "
            "FROM T_COMN_CONDUCTOR_INSTANCE TAB_A "
            "LEFT OUTER JOIN T_COMN_CONDUCTOR_STATUS TAB_B "
            "ON TAB_A.STATUS_ID=TAB_B.STATUS_ID "
            "WHERE TAB_A.DISUSE_FLAG='0' "
            "AND TAB_B.DISUSE_FLAG='0' "
        ) % (lang)

        if len(status_list) > 0:
            sql += "AND TAB_A.STATUS_ID IN ("
            for sts in status_list:
                sql += '%s,'

            sql = sql.rstrip(',')
            sql += ") "

        if isinstance(days, int):
            now = datetime.datetime.now()
            sql += "AND TAB_A.TIME_BOOK>=%s "
            status_list.append(now)

            if days > 0:
                to_datetime = now + datetime.timedelta(days=days)
                to_datetime = datetime.datetime(
                    to_datetime.year, to_datetime.month, to_datetime.day, 23, 59, 59, 999999
                )
                sql += "AND TAB_A.TIME_BOOK<=%s "
                status_list.append(to_datetime)

        rset = objdbca.sql_execute(sql, status_list)

        return rset

    lang = g.get('LANGUAGE')

    # 応答情報の初期化
    widget_data = {}
    widget_data['data'] = []
    widget_data['menu'] = {}
    widget_data['widget'] = []
    widget_data['movement'] = {}
    widget_data['work_info'] = {}
    widget_data['work_result'] = {}
    widget_data['work_reserve'] = {}

    # Widget情報を取得
    current_widget = {}
    rset = objdbca.table_select('T_COMN_WEB_TABLE_SETTINGS', 'WHERE USER_ID = %s', g.USER_ID)
    if len(rset) > 0 and 'WIDGET_SETTINGS' in rset[0] and rset[0]['WIDGET_SETTINGS'] is not None:
        current_widget = json.loads(rset[0]['WIDGET_SETTINGS'])

    # メニュー情報を取得
    menus = {}
    menu_groups = []
    menu_list = collect_menus(objdbca, extra_flag=True)['menu_groups']
    for mg in menu_list:
        mgid = mg['id']
        menu_groups.append(mgid)
        for m in mg['menus']:
            menus[m['id']] = m['menu_name_rest']

        file_name = mg['icon']
        file_paths = get_upload_file_path(g.get('WORKSPACE_ID'), '10102', mgid, 'menu_group_icon', file_name, '')  # noqa: F405
        encoded = file_encode(file_paths.get('file_path'))  # noqa: F405
        if not encoded:
            encoded = None

        mg['icon'] = encoded

        mg['position'] = ''
        if 'menu' in current_widget:
            for cur_mg in current_widget['menu']:
                if 'id' in cur_mg and mgid == cur_mg['id']:
                    if 'position' in cur_mg:
                        mg['position'] = cur_mg['position']

                    if 'disp_seq' in cur_mg:
                        mg['disp_seq'] = cur_mg['disp_seq']

                    break

    # widget情報の取得
    widget_list = []
    if 'widget' in current_widget:
        widget_list = current_widget['widget']

    # Movement情報の取得
    movement_info = {}

    sql = (
        "SELECT TAB_A.ORCHESTRA_ID, TAB_A.ORCHESTRA_NAME, TAB_C.MENU_ID, COUNT(*) CNT "
        "FROM T_COMN_ORCHESTRA TAB_A "
        "LEFT OUTER JOIN T_COMN_MOVEMENT TAB_B "
        "ON TAB_A.ORCHESTRA_ID=TAB_B.ITA_EXT_STM_ID "
        "LEFT OUTER JOIN ("
        "  SELECT '1' ORCHESTRA_ID, '20201' MENU_ID "
        "  UNION "
        "  SELECT '2' ORCHESTRA_ID, '20301' MENU_ID "
        "  UNION "
        "  SELECT '3' ORCHESTRA_ID, '20402' MENU_ID "
        "  UNION "
        "  SELECT '4' ORCHESTRA_ID, '80104' MENU_ID "
        "  UNION "
        "  SELECT '5' ORCHESTRA_ID, '90103' MENU_ID "
        ") TAB_C "
        "ON TAB_A.ORCHESTRA_ID=TAB_C.ORCHESTRA_ID "
        "WHERE TAB_A.DISUSE_FLAG='0' "
        "AND TAB_B.DISUSE_FLAG='0' "
        "GROUP BY TAB_A.ORCHESTRA_ID, TAB_A.ORCHESTRA_NAME, TAB_C.MENU_ID "
        "ORDER BY TAB_A.DISP_SEQ "
    )

    rset = objdbca.sql_execute(sql)
    for r in rset:
        orch_id = r['ORCHESTRA_ID']
        if orch_id not in movement_info:
            movement_info[orch_id] = {}

        movement_info[orch_id]['name'] = r['ORCHESTRA_NAME']
        movement_info[orch_id]['menu_id'] = r['MENU_ID']
        movement_info[orch_id]['number'] = r['CNT'] if r['MENU_ID'] in menus else '0'
        movement_info[orch_id]['menu_name_rest'] = menus[r['MENU_ID']] if r['MENU_ID'] in menus else ''

    # 作業状況の取得
    work_info = {}
    work_info['conductor'] = []

    if '30105' in menus:  # 30105:Conductor作業一覧
        status_list = ['1', '2', '3', '4', '5']  # 1:未実行, 2:未実行(予約), 3:実行中, 4:実行中(遅延), 5:一時停止
        rset = get_conductor_info(objdbca, status_list, lang)
        for r in rset:
            cond_ins_id = r['CONDUCTOR_INSTANCE_ID']
            conductor_info = {}
            conductor_info[cond_ins_id] = {}
            conductor_info[cond_ins_id]['status'] = r['STATUS_NAME']
            conductor_info[cond_ins_id]['end'] = r['TIME_END'].strftime('%Y/%m/%d %H:%M:%S.%f') if isinstance(r['TIME_END'], datetime.datetime) else r['TIME_END']
            conductor_info[cond_ins_id]['menu_name_rest'] = menus['30105']

            work_info['conductor'].append(conductor_info)

    # 作業結果の取得
    work_result_info = {}
    work_result_info['conductor'] = []

    if '30105' in menus:  # 30105:Conductor作業一覧
        status_list = ['6', '7', '8', '9', '10', '11']  # 6:正常, 7:異常, 8:警告, 9:緊急停止, 10:予約取消, 11:想定外
        rset = get_conductor_info(objdbca, status_list, lang)
        for r in rset:
            cond_ins_id = r['CONDUCTOR_INSTANCE_ID']
            conductor_info = {}
            conductor_info[cond_ins_id] = {}
            conductor_info[cond_ins_id]['status'] = r['STATUS_NAME']
            conductor_info[cond_ins_id]['end'] = r['TIME_END'].strftime('%Y/%m/%d %H:%M:%S.%f') if isinstance(r['TIME_END'], datetime.datetime) else r['TIME_END']
            conductor_info[cond_ins_id]['menu_name_rest'] = menus['30105']

            work_result_info['conductor'].append(conductor_info)

    # 予約作業確認
    work_reserve_info = {}
    work_reserve_info['conductor'] = []

    if '30105' in menus:  # 30105:Conductor作業一覧
        days = 0
        if 'widget' in current_widget:
            for k, v in current_widget['widget'].items():
                if k == 'w5' and 'period' in v:
                    try:
                        days = int(v['period'])
                        days = days if days >= 0 and days <= 365 else 0
                    except Exception:
                        days = 0

                    break

        status_list = ['2', ]  # 2:未実行(予約)
        rset = get_conductor_info(objdbca, status_list, lang, days=days)
        for r in rset:
            cond_ins_id = r['CONDUCTOR_INSTANCE_ID']
            conductor_info = {}
            conductor_info[cond_ins_id] = {}
            conductor_info[cond_ins_id]['conductor_name'] = r['I_CONDUCTOR_NAME']
            conductor_info[cond_ins_id]['operation_name'] = r['I_OPERATION_NAME']
            conductor_info[cond_ins_id]['time_book'] = r['TIME_BOOK'].strftime('%Y/%m/%d %H:%M:%S.%f') if isinstance(r['TIME_BOOK'], datetime.datetime) else r['TIME_BOOK']
            conductor_info[cond_ins_id]['status'] = r['STATUS_NAME']
            conductor_info[cond_ins_id]['menu_name_rest'] = menus['30106'] if '30106' in menus else ''

            work_reserve_info['conductor'].append(conductor_info)

    # 応答情報の作成
    widget_data['menu'] = menu_list
    widget_data['widget'] = widget_list
    widget_data['movement'] = movement_info
    widget_data['work_info'] = work_info
    widget_data['work_result'] = work_result_info
    widget_data['work_reserve'] = work_reserve_info

    return widget_data


def regist_widget_settings(objdbca, parameter):
    """
        Dashboardのwidget設定を登録する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            parameter: bodyの中身
        RETRUN:
            data
    """
    # DBコネクション開始
    objdbca.db_transaction_start()

    # 要求情報を取得
    data_list = {
        'USER_ID': g.USER_ID,
        'WIDGET_SETTINGS': str(json.dumps(parameter)),
    }

    # Webテーブル設定を取得
    ret = objdbca.table_select('T_COMN_WEB_TABLE_SETTINGS', 'WHERE USER_ID = %s', g.USER_ID)

    if len(ret) == 0:
        # Webテーブル設定にINSERT
        ret = objdbca.table_insert('T_COMN_WEB_TABLE_SETTINGS', data_list, 'ROW_ID', False)
    else:
        data_list['ROW_ID'] = ret[0]['ROW_ID']
        # Webテーブル設定にUPDATE
        ret = objdbca.table_update('T_COMN_WEB_TABLE_SETTINGS', data_list, 'ROW_ID', False)

    # DBコネクション終了
    objdbca.db_transaction_end(True)

    return g.appmsg.get_api_message("000-00001")

