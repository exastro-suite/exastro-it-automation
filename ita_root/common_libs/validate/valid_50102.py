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

    entry_parameter = option.get('entry_parameter').get('parameter')
    current_parameter = option.get('current_parameter').get('parameter')
    cmd_type = option.get("cmd_type")

    # シートタイプ取得
    sheet_type = entry_parameter.get("sheet_type")

    # パラメータシート名を取得
    menu_name_ja = entry_parameter.get("menu_name_ja")
    current_menu_name_ja = current_parameter.get("menu_name_ja")
    menu_name_en = entry_parameter.get("menu_name_en")
    current_menu_name_en = current_parameter.get("menu_name_en")

    # 入力用メニューグループを取得
    menu_group_for_input = entry_parameter.get("menu_group_for_input")
    current_menu_group_for_input = current_parameter.get("menu_group_for_input")
    # 代入値自動登録用メニューグループを取得
    menu_group_for_subst = entry_parameter.get("menu_group_for_subst")
    current_menu_group_for_subst = current_parameter.get("menu_group_for_subst")
    # 参照用メニューグループを取得
    menu_group_for_ref = entry_parameter.get("menu_group_for_ref")
    current_menu_group_for_ref = current_parameter.get("menu_group_for_ref")

    # [START]---------パラメータシート名(メニュー名)---------
    # パラメータシート名に「メインメニュー」、「Main menu」使用不可
    if menu_name_ja is not None and menu_name_en is not None:
        disabled_menu_name = g.appmsg.get_api_message("MSG-20001", [])
        if menu_name_ja == disabled_menu_name or menu_name_en == disabled_menu_name:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20002", [])
            return retBool, msg, option

    # 更新時のみ。パラメータシート作成状態が2（作成済み）の場合、パラメータシート名(rest)が変更されていないことをチェック。
    menu_name_rest = entry_parameter.get('menu_name_rest')
    if cmd_type == "Update":
        menu_create_done_status = current_parameter.get("menu_create_done_status")
        before_menu_name = current_parameter.get("menu_name_rest")
        if menu_create_done_status == "2" and menu_name_rest:
            if not before_menu_name == menu_name_rest:
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20004", [])
                return retBool, msg, option

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
            return retBool, msg, option

    # 「メニュー管理」テーブルで「メニューグループ」「パラメータシート名(メニュー名)」で一致があるかどうかをチェック（入力用/代入値自動登録用/参照用でそれぞれ確認）
    if cmd_type == "Register":
        # 「入力用」メニューグループで一致しているパラメータシート名(メニュー名)のレコードがないかチェック
        if menu_group_for_input:
            retBool, msg = check_exist_menu(objdbca, menu_group_for_input, menu_name_ja, menu_name_en)
            if not retBool:
                return retBool, msg, option

        # 「代入値自動登録用」メニューグループで一致しているパラメータシート名(メニュー名)のレコードがないかチェック
        if menu_group_for_subst:
            retBool, msg = check_exist_menu(objdbca, menu_group_for_subst, menu_name_ja, menu_name_en)
            if not retBool:
                return retBool, msg, option

        # 「参照用」メニューグループで一致しているパラメータシート名(メニュー名)のレコードがないかチェック
        if menu_group_for_ref:
            retBool, msg = check_exist_menu(objdbca, menu_group_for_ref, menu_name_ja, menu_name_en)
            if not retBool:
                return retBool, msg, option

    if cmd_type == "Update":
        # パラメータシート名に更新がある場合、全メニューグループをチェックする
        menu_name_ja = menu_name_ja if menu_name_ja else current_menu_name_ja
        menu_name_en = menu_name_en if menu_name_en else current_menu_name_en
        if not menu_name_ja == current_menu_name_ja or not menu_name_en == current_menu_name_en:
            # 「入力用」メニューグループで一致しているパラメータシート名(メニュー名)のレコードがないかチェック
            if menu_group_for_input:
                retBool, msg = check_exist_menu(objdbca, menu_group_for_input, menu_name_ja, menu_name_en)
                if not retBool:
                    return retBool, msg, option

            # 「代入値自動登録用」メニューグループで一致しているパラメータシート名(メニュー名)のレコードがないかチェック
            if menu_group_for_subst:
                retBool, msg = check_exist_menu(objdbca, menu_group_for_subst, menu_name_ja, menu_name_en)
                if not retBool:
                    return retBool, msg, option

            # 「参照用」メニューグループで一致しているパラメータシート名(メニュー名)のレコードがないかチェック
            if menu_group_for_ref:
                retBool, msg = check_exist_menu(objdbca, menu_group_for_ref, menu_name_ja, menu_name_en)
                if not retBool:
                    return retBool, msg, option
        else:
            # 各メニューグループに変更があった場合、変更対象をチェックする
            if not menu_group_for_input == current_menu_group_for_input:
                # 「入力用」メニューグループで一致しているメニュー名のレコードがないかチェック
                if menu_group_for_input:
                    retBool, msg = check_exist_menu(objdbca, menu_group_for_input, menu_name_ja, menu_name_en)
                    if not retBool:
                        return retBool, msg, option

            if not menu_group_for_subst == current_menu_group_for_subst:
                # 「代入値自動登録用」メニューグループで一致しているパラメータシート名(メニュー名)のレコードがないかチェック
                if menu_group_for_subst:
                    retBool, msg = check_exist_menu(objdbca, menu_group_for_subst, menu_name_ja, menu_name_en)
                    if not retBool:
                        return retBool, msg, option

            if not menu_group_for_ref == current_menu_group_for_ref:
                # 「参照用」メニューグループで一致しているパラメータシート名(メニュー名)のレコードがないかチェック
                if menu_group_for_ref:
                    retBool, msg = check_exist_menu(objdbca, menu_group_for_ref, menu_name_ja, menu_name_en)
                    if not retBool:
                        return retBool, msg, option
    # [END]---------パラメータシート名(メニュー名)---------

    # [START]---------作成対象---------
    # 作成対象で「データシート」を選択
    if sheet_type == "2":
        # 代入値自動登録用メニューグループ、参照用メニューグループが選択されている場合、エラー
        if menu_group_for_subst or menu_group_for_ref:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20006", [])
            return retBool, msg, option

        # ---------バンドル---------
        # バンドルが有効の場合、エラー
        vertical = entry_parameter.get("vertical")
        if vertical == '1':
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20007", [])
            return retBool, msg, option
        # ---------バンドル---------

    # 作成対象で「パラメータシート(ホスト/オペレーションあり)」を選択
    elif sheet_type == "1":
        # 代入値自動登録用メニューグループ、または参照用メニューグループが設定されていない場合、エラー
        if not menu_group_for_subst or not menu_group_for_ref:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20008", [])
            return retBool, msg, option
    # 作成対象で「パラメータシート(オペレーションあり)」を選択
    elif sheet_type == "3":
        if not menu_group_for_subst or not menu_group_for_ref:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20009", [])
            return retBool, msg, option
    # [END]---------作成対象---------

    # [START]---------代入値自動登録用メニューグループ---------
    # 作成対象が「パラメータシート(ホスト/オペレーションあり)」、「パラメータシート(オペレーションあり)」選択時のみ
    if sheet_type == "1" or sheet_type == "3":
        # 他のメニューグループと同じ場合、エラー
        if menu_group_for_subst and (menu_group_for_subst == menu_group_for_input or menu_group_for_subst == menu_group_for_ref):
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20010", [])
            return retBool, msg, option
    # [END]---------代入値自動登録用メニューグループ---------

    # [START]---------参照用メニューグループ---------
        # 他のメニューグループと同じ場合、エラー
        if menu_group_for_ref and (menu_group_for_ref == menu_group_for_input or menu_group_for_ref == menu_group_for_subst):
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20010", [])
            return retBool, msg, option
    # [END]---------参照用メニューグループ---------

    # 新規なら「作成状態」を未作成にする
    entry_parameter['menu_create_done_status'] = current_parameter.get('menu_create_done_status')
    if cmd_type == "Register":
        entry_parameter.update([('menu_create_done_status', '1')])

    return retBool, msg, option


def check_exist_menu(objdbca, menu_group_id, menu_name_ja, menu_name_en):
    """
        「メニュー管理」テーブルに「メニューグループ」「パラメータシート名(メニュー名)」が一致するレコードがあるかどうかをチェックする
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            mmenu_group_id: メニューグループID
            menu_name_ja: パラメータシート名(日本語)
            menu_name_en: パラメータシート名(英語)
        RETRUN:
            boolean, msg
    """
    lang = g.get('LANGUAGE')
    retBool = True
    msg = ''

    # メニューグループとパラメータシート名(メニュー名)が一致するレコードを検索
    where_str = 'WHERE MENU_GROUP_ID = %s AND (MENU_NAME_JA = %s OR MENU_NAME_EN = %s) AND DISUSE_FLAG = %s'
    ret = objdbca.table_select('T_COMN_MENU', where_str, [menu_group_id, menu_name_ja, menu_name_en, 0])
    if ret:
        # 返却メッセージ用のメニューグループ名を取得
        menu_group_name = ''
        menu_name = menu_name_ja if lang == 'ja' else menu_name_en
        where_str = 'WHERE MENU_GROUP_ID = %s AND DISUSE_FLAG = %s'
        ret2 = objdbca.table_select('T_COMN_MENU_GROUP', where_str, [menu_group_id, 0])
        if ret2:
            menu_group_name = ret2[0].get('MENU_GROUP_NAME_' + lang.upper())

        msg = g.appmsg.get_api_message("MSG-20257", [menu_group_name, menu_name])
        retBool = False

    return retBool, msg
