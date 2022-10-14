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


def menu_define_valid(objdbca, objtable, option):
    retBool = True
    msg = ''
    # 個別処理
    # ---------メニュー定義一覧---------
    entry_parameter = option.get('entry_parameter').get('parameter')
    current_parameter = option.get('current_parameter').get('parameter')

    # ---------メニュー名---------
    menu_name_ja = entry_parameter.get("menu_name_ja")
    menu_name_en = entry_parameter.get("menu_name_en")
    # メニュー名に「メインメニュー」、「Main menu」使用不可
    if menu_name_ja is not None and menu_name_en is not None:
        disabled_menu_name = g.appmsg.get_api_message("MSG-20001", [])
        if menu_name_ja == disabled_menu_name or menu_name_en == disabled_menu_name:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20002", [])
    
    # 更新時のみ。メニュー作成状態が2（作成済み）の場合、メニュー名(rest)が変更されていないことをチェック。
    menu_name_rest = entry_parameter.get('menu_name_rest')
    cmd_type = option.get("cmd_type")
    if cmd_type == "Update":
        menu_create_done_status = entry_parameter.get("menu_create_done_status")
        before_menu_name = current_parameter.get("menu_name_rest")
        if menu_create_done_status == "2":
            if before_menu_name != menu_name_rest:
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20004", [])
    
    # 「メニュー管理」テーブルで使用されているmenu_name_restは使用不可(currentと同じ名前の場合はチェック処理をスキップ)
    menu_name_rest = entry_parameter.get('menu_name_rest')
    current_menu_name_rest = current_parameter.get('menu_name_rest')
    if not menu_name_rest == current_menu_name_rest:
        ret = objdbca.table_select('T_COMN_MENU', 'WHERE DISUSE_FLAG = %s', [0])
        menu_name_rest_list = []
        for recode in ret:
            menu_name_rest_list.append(recode.get('MENU_NAME_REST'))
        if menu_name_rest in (menu_name_rest_list):
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20005", [])

        if not retBool:
            return retBool, msg, option
    # ---------メニュー名---------

    # ---------作成対象---------
    # シートタイプ取得
    sheet_type = entry_parameter.get("sheet_type")
    # 入力用メニューグループを取得
    menu_group_for_input = entry_parameter.get("menu_group_for_input")
    # 代入値自動登録用メニューグループを取得
    menu_group_for_subst = entry_parameter.get("menu_group_for_subst")
    # 参照用メニューグループを取得
    menu_group_for_ref = entry_parameter.get("menu_group_for_ref")
    
    # 作成対象で「データシート」を選択
    if sheet_type == "2":
        # 代入値自動登録用メニューグループ、参照用メニューグループが選択されている場合、エラー
        if menu_group_for_subst or menu_group_for_ref:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20006", [])

        # ---------縦メニュー利用---------
        # 縦メニュー利用が設定されている場合、エラー
        vertical = entry_parameter.get("vertical")
        if vertical == '1':
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20007", [])
        # ---------縦メニュー利用---------

    # 作成対象で「パラメータシート(ホスト/オペレーションあり)」を選択
    elif sheet_type == "1":
        # 代入値自動登録用メニューグループ、または参照用メニューグループが設定されていない場合、エラー
        if not menu_group_for_subst or not menu_group_for_ref:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20008", [])
    # 作成対象で「パラメータシート(オペレーションあり)」を選択
    elif sheet_type == "3":
        if not menu_group_for_subst or not menu_group_for_ref:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20009", [])
    if not retBool:
        return retBool, msg, option
    # ---------作成対象---------

    # ---------代入値自動登録用メニューグループ---------
    # 作成対象が「パラメータシート(ホスト/オペレーションあり)」、「パラメータシート(オペレーションあり)」選択時のみ
    if sheet_type == "1" or sheet_type == "3":
        # 他のメニューグループと同じ場合、エラー
        if menu_group_for_subst and (menu_group_for_subst == menu_group_for_input or menu_group_for_subst == menu_group_for_ref):
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20010", [])
    # ---------代入値自動登録用メニューグループ---------

    # ---------参照用メニューグループ---------
        # 他のメニューグループと同じ場合、エラー
        if menu_group_for_ref and (menu_group_for_ref == menu_group_for_input or menu_group_for_ref == menu_group_for_subst):
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20010", [])
    if not retBool:
        return retBool, msg, option
    # ---------参照用メニューグループ---------
    
    # ---------メニュー定義一覧---------
    # 新規なら未作成にする
    if cmd_type == "Register":
        entry_parameter.update([('menu_create_done_status', '1')])
    # 個別処理
    return retBool, msg, option
