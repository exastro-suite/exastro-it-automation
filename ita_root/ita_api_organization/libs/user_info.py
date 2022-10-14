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

from common_libs.common import *  # noqa: F403
from flask import g
from libs.organization_common import check_auth_menu
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
    ret = objdbca.table_select(t_common_menu, 'WHERE DISUSE_FLAG = %s ORDER BY MENU_GROUP_ID ASC, DISP_SEQ ASC', [0])
    
    menu_groups = []
    for recode in ret:
        # メニューに対する権限があるかどうかをチェック
        menu_name_rest = recode.get('MENU_NAME_REST')
        try:
            check_auth_menu(menu_name_rest)
        except AppException as e:
            if e.args[0] == '401-00001':
                continue
            else:
                raise e
        
        # 権限のあるメニューのメニューグループを格納
        menu_group_id = recode.get('MENU_GROUP_ID')
        menu_groups.append(menu_group_id)
        
    # 重複を除外
    menu_groups = list(set(menu_groups))
    
    # 『メニューグループ管理』テーブルからメニューグループの一覧を取得
    ret = objdbca.table_select(t_common_menu_group, 'WHERE DISUSE_FLAG = %s ORDER BY DISP_SEQ ASC', [0])
    
    panels_data = {}
    for recode in ret:
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
    
    user_auth_data = {
        "user_id": user_id,
        "user_name": user_name,
        "roles": roles,
        "workspaces": workspaces
    }
    
    return user_auth_data


def collect_menus(objdbca):
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
    menus = {}
    for recode in ret:
        # メニューに対する権限があるかどうかをチェック
        menu_name_rest = recode.get('MENU_NAME_REST')
        try:
            check_auth_menu(menu_name_rest)
        except AppException as e:
            if e.args[0] == '401-00001':
                continue
            else:
                raise e
        
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
        # メニューグループに権限のあるメニューが1つもない場合は除外
        menu_group_id = recode.get('MENU_GROUP_ID')
        target_menus = menus.get(menu_group_id)
        if not target_menus:
            continue
        
        add_menu_group = {}
        add_menu_group['parent_id'] = recode.get('PARENT_MENU_GROUP_ID')
        add_menu_group['id'] = menu_group_id
        add_menu_group['menu_group_name'] = recode.get('MENU_GROUP_NAME_' + lang.upper())
        add_menu_group['disp_seq'] = recode.get('DISP_SEQ')
        add_menu_group['menus'] = target_menus
        
        menu_group_list.append(add_menu_group)
    
    menus_data = {
        "menu_groups": menu_group_list,
    }
    
    return menus_data
