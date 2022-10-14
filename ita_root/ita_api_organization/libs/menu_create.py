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
import ast
from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from flask import g
from libs.organization_common import check_auth_menu  # noqa: F401
from common_libs.api import check_request_body_key


def collect_menu_create_data(objdbca):
    """
        メニュー定義・作成(新規)用の情報取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            create_data
    """
    # 共通部分を取得
    create_data = _collect_common_menu_create_data(objdbca)

    return create_data


def collect_exist_menu_create_data(objdbca, menu_create):  # noqa: C901
    """
        メニュー定義・作成(既存)用の情報取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            create_data
    """
    # テーブル/ビュー名
    t_menu_define = 'T_MENU_DEFINE'
    t_menu_column = 'T_MENU_COLUMN'
    t_menu_column_group = 'T_MENU_COLUMN_GROUP'
    t_menu_unique_constraint = 'T_MENU_UNIQUE_CONSTRAINT'
    t_menu_role = 'T_MENU_ROLE'
    
    # 変数定義
    lang = g.get('LANGUAGE')
    menu_info = {}
    
    # 共通部分を取得
    create_data = _collect_common_menu_create_data(objdbca)
    
    # 対象メニューグループのデータを形成
    format_target_menu_group_list = {}
    for target in create_data['target_menu_group_list']:
        format_target_menu_group_list[target.get('menu_group_id')] = target.get('menu_group_name')
    
    # シートタイプのデータを形成
    format_sheet_type_list = {}
    for target in create_data['sheet_type_list']:
        format_sheet_type_list[target.get('sheet_type_id')] = target.get('sheet_type_name')
        
    # カラムクラスのデータを形成
    format_column_class_list = {}
    for target in create_data['column_class_list']:
        format_column_class_list[target.get('column_class_id')] = {'column_class_name': target.get('column_class_name'), 'column_class_disp_name': target.get('column_class_disp_name')}  # noqa: E501
    
    # 「メニュー定義一覧」から対象のメニューのレコードを取得
    ret = objdbca.table_select(t_menu_define, 'WHERE MENU_NAME_REST = %s AND DISUSE_FLAG = %s', [menu_create, 0])
    if not ret:
        log_msg_args = [menu_create]
        api_msg_args = [menu_create]
        raise AppException("499-00001", log_msg_args, api_msg_args)  # noqa: F405
    
    # 対象のuuidを取得
    menu_create_id = ret[0].get('MENU_CREATE_ID')
    
    # 対象メニューグループについて、名称を取得
    menu_group_for_input_id = ret[0].get('MENU_GROUP_ID_INPUT')
    menu_group_for_subst_id = ret[0].get('MENU_GROUP_ID_SUBST')
    menu_group_for_ref_id = ret[0].get('MENU_GROUP_ID_REF')
    menu_group_for_input = format_target_menu_group_list.get(menu_group_for_input_id)
    menu_group_for_subst = format_target_menu_group_list.get(menu_group_for_subst_id)
    menu_group_for_ref = format_target_menu_group_list.get(menu_group_for_ref_id)
    
    # シートタイプについて、名称を取得
    sheet_type_id = ret[0].get('SHEET_TYPE')
    sheet_type_name = format_sheet_type_list.get(sheet_type_id)
    
    # 最終更新日時のフォーマット
    last_update_timestamp = ret[0].get('LAST_UPDATE_TIMESTAMP')
    last_update_date_time = last_update_timestamp.strftime('%Y/%m/%d %H:%M:%S.%f')
    
    # 最終更新者を取得
    users_list = _get_user_list(objdbca)
    last_updated_user_id = ret[0].get('LAST_UPDATE_USER')
    last_updated_user = users_list.get(last_updated_user_id)
    
    # 縦メニュー利用の有無を取得
    vertical = ret[0].get('VERTICAL')
    
    # 「メニュー-ロール作成情報」から対象のレコードを取得
    selected_role_list = []
    ret_role_list = objdbca.table_select(t_menu_role, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s', [menu_create_id, 0])
    if ret_role_list:
        for record in ret_role_list:
            role_id = record.get('ROLE_ID')
            if role_id:
                selected_role_list.append(role_id)
    
    # メニューデータを格納
    menu = {
        "menu_create_id": menu_create_id,
        "menu_name": ret[0].get('MENU_NAME_' + lang.upper()),
        "menu_name_rest": ret[0].get('MENU_NAME_REST'),
        "sheet_type_id": sheet_type_id,
        "sheet_type_name": sheet_type_name,
        "disp_seq": ret[0].get('DISP_SEQ'),
        "vertical": vertical,
        "menu_group_for_input_id": menu_group_for_input_id,
        "menu_group_for_subst_id": menu_group_for_subst_id,
        "menu_group_for_ref_id": menu_group_for_ref_id,
        "menu_group_for_input": menu_group_for_input,
        "menu_group_for_subst": menu_group_for_subst,
        "menu_group_for_ref": menu_group_for_ref,
        "selected_role_id": selected_role_list,
        "description": ret[0].get('DESCRIPTION_' + lang.upper()),
        "remarks": ret[0].get('NOTE'),
        "menu_create_done_status_id": ret[0].get('MENU_CREATE_DONE_STATUS'),
        "last_update_date_time": last_update_date_time,
        "last_updated_user": last_updated_user
    }
    
    # 「一意制約(複数項目)作成情報」から対象のレコードを取得
    menu['unique_constraint_current'] = None
    ret = objdbca.table_select(t_menu_unique_constraint, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s', [menu_create_id, 0])
    if ret:
        menu['unique_constraint_current'] = ast.literal_eval(ret[0].get('UNIQUE_CONSTRAINT_ITEM'))
    
    # メニュー情報を格納
    menu_info['menu'] = menu
    
    # 「カラムグループ作成情報」からレコードをすべて取得
    column_group_list = {}
    ret = objdbca.table_select(t_menu_column_group, 'WHERE DISUSE_FLAG = %s', [0])
    col_group_record_count = len(ret)  # 「カラムグループ作成情報」のレコード数を格納
    for record in ret:
        add_data = {
            "column_group_id": record.get('CREATE_COL_GROUP_ID'),
            "column_group_name": record.get('COL_GROUP_NAME_' + lang.upper()),
            "full_column_group_name": record.get('FULL_COL_GROUP_NAME_' + lang.upper()),
            "parent_column_group_id": record.get('PA_COL_GROUP_ID')
        }
        column_group_list[record.get('CREATE_COL_GROUP_ID')] = add_data
    
    # 「メニュー項目作成情報」から対象のメニューのレコードを取得
    column_info_data = {}
    column_group_info_data = {}
    tmp_column_group = {}
    column_group_parent_of_child = {}  # カラムグループの親子関係があるとき、子の一番大きい親を結びつける
    ret = objdbca.table_select(t_menu_column, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s ORDER BY DISP_SEQ ASC', [menu_create_id, 0])
    if ret:
        for count, record in enumerate(ret, 1):
            # 最終更新日時のフォーマット
            last_update_timestamp = record.get('LAST_UPDATE_TIMESTAMP')
            last_update_date_time = last_update_timestamp.strftime('%Y/%m/%d %H:%M:%S.%f')
            
            # カラムデータを格納
            col_detail = {
                "create_column_id": record.get('CREATE_COLUMN_ID'),
                "item_name": record.get('COLUMN_NAME_' + lang.upper()),
                "item_name_rest": record.get('COLUMN_NAME_REST'),
                "display_order": record.get('DISP_SEQ'),
                "required": record.get('REQUIRED'),
                "uniqued": record.get('UNIQUED'),
                "column_class_id": "",
                "column_class_name": "",
                "description": record.get('DESCRIPTION_' + lang.upper()),
                "remarks": record.get('NOTE'),
                "last_update_date_time": last_update_date_time
            }
            
            # フルカラムグループ名を格納
            column_group_id = record.get('CREATE_COL_GROUP_ID')
            col_detail['column_group_id'] = column_group_id
            col_detail['column_group_name'] = None
            if column_group_id:
                target_data = column_group_list.get(column_group_id)
                if target_data:
                    col_detail['column_group_name'] = target_data.get('full_column_group_name')
                
            # カラムクラス情報を格納
            column_class_id = record.get('COLUMN_CLASS')
            column_class_name = format_column_class_list.get(column_class_id).get('column_class_name')
            column_class_disp_name = format_column_class_list.get(column_class_id).get('column_class_disp_name')
            col_detail['column_class_id'] = column_class_id
            col_detail['column_class_name'] = column_class_name
            col_detail['column_class_disp_name'] = column_class_disp_name
            
            # カラムクラスに応じて必要な値を格納
            # カラムクラス「文字列(単一行)」用のパラメータを追加
            if column_class_name == "SingleTextColumn":
                col_detail["single_string_maximum_bytes"] = record.get('SINGLE_MAX_LENGTH')  # 文字列(単一行) 最大バイト数
                col_detail["single_string_regular_expression"] = record.get('SINGLE_REGULAR_EXPRESSION')  # 文字列(単一行) 正規表現
                col_detail["single_string_default_value"] = record.get('SINGLE_DEFAULT_VALUE')  # 文字列(単一行) 初期値
            
            # カラムクラス「文字列(複数行)」用のパラメータを追加
            if column_class_name == "MultiTextColumn":
                col_detail["multi_string_maximum_bytes"] = record.get('MULTI_MAX_LENGTH')  # 文字列(複数行) 最大バイト数
                col_detail["multi_string_regular_expression"] = record.get('MULTI_REGULAR_EXPRESSION')  # 文字列(複数行) 正規表現
                col_detail["multi_string_default_value"] = record.get('MULTI_DEFAULT_VALUE')  # 文字列(複数行) 初期値
            
            # カラムクラス「整数」用のパラメータを追加
            if column_class_name == "NumColumn":
                col_detail["integer_maximum_value"] = record.get('NUM_MAX')  # 整数 最大値
                col_detail["integer_minimum_value"] = record.get('NUM_MIN')  # 整数 最小値
                col_detail["integer_default_value"] = record.get('NUM_DEFAULT_VALUE')  # 整数 初期値
            
            # カラムクラス「小数」用のパラメータを追加
            if column_class_name == "FloatColumn":
                col_detail["decimal_maximum_value"] = record.get('FLOAT_MAX')  # 小数 最大値
                col_detail["decimal_minimum_value"] = record.get('FLOAT_MIN')  # 小数 最小値
                col_detail["decimal_digit"] = record.get('decimal_digit')  # 小数 桁数
                col_detail["decimal_default_value"] = record.get('FLOAT_DEFAULT_VALUE')  # 小数 初期値
            
            # カラムクラス「日時」用のパラメータを追加
            if column_class_name == "DateTimeColumn":
                full_datetime_default_value = record.get('DATETIME_DEFAULT_VALUE')
                if full_datetime_default_value:
                    datetime_default_value = full_datetime_default_value.strftime('%Y/%m/%d %H:%M:%S')
                    col_detail["detetime_default_value"] = datetime_default_value  # 日時 初期値
                else:
                    col_detail["detetime_default_value"] = None
            
            # カラムクラス「日付」用のパラメータを追加
            if column_class_name == "DateColumn":
                full_datet_default_value = record.get('DATE_DEFAULT_VALUE')
                if full_datet_default_value:
                    date_default_value = full_datet_default_value.strftime('%Y/%m/%d')
                    col_detail["dete_default_value"] = date_default_value  # 日付 初期値
                else:
                    col_detail["dete_default_value"] = None
            
            # カラムクラス「プルダウン選択」用のパラメータを追加
            if column_class_name == "IDColumn":
                col_detail["pulldown_selection"] = record.get('OTHER_MENU_LINK_ID')  # プルダウン選択 メニューグループ:メニュー:項目
                col_detail["pulldown_selection_default_value"] = record.get('OTHER_MENU_LINK_DEFAULT_VALUE')  # プルダウン選択 初期値
                reference_item = record.get('REFERENCE_ITEM')
                if reference_item:
                    col_detail["reference_item"] = ast.literal_eval(reference_item)  # プルダウン選択 参照項目
                else:
                    col_detail["reference_item"] = None  # プルダウン選択 参照項目
            
            # カラムクラス「パスワード」用のパラメータを追加
            if column_class_name == "PasswordColumn":
                col_detail["password_maximum_bytes"] = record.get('PASSWORD_MAX_LENGTH')  # パスワード 最大バイト数
            
            # カラムクラス「ファイルアップロード」用のパラメータを追加
            if column_class_name == "FileUploadColumn":
                col_detail["file_upload_maximum_bytes"] = record.get('FILE_UPLOAD_MAX_SIZE')  # ファイルアップロード 最大バイト数
            
            # カラムクラス「リンク」用のパラメータを追加
            if column_class_name == "HostInsideLinkTextColumn":
                col_detail["link_maximum_bytes"] = record.get('LINK_MAX_LENGTH')  # リンク 最大バイト数
                col_detail["link_default_value"] = record.get('LINK_DEFAULT_VALUE')  # リンク 初期値
            
            # カラムクラス「パラメータシート参照」用のパラメータを追加 (未実装)
            # if column_class_name == "LinkIDColumn":
            #     col_detail["parameter_sheet_reference"] = record.get('PARAM_SHEET_LINK_ID')  # パラメータシート参照
            
            col_num = 'c{}'.format(count)
            column_info_data[col_num] = col_detail
            
            # カラムグループ利用があれば、カラムグループ管理用配列に追加
            if column_group_id:
                tmp_column_group, column_group_parent_of_child = add_tmp_column_group(column_group_list, col_group_record_count, column_group_id, col_num, tmp_column_group, column_group_parent_of_child)  # noqa: E501
        
        # カラムグループ管理用配列について、カラムグループIDをg1,g2,g3...に変換し、idやnameを格納する。
        column_group_info_data, key_to_id = collect_column_group_sort_order(column_group_list, tmp_column_group, column_group_info_data)
        
        # 大元のカラムの並び順を作成し格納
        menu_info['menu']['columns'] = collect_parent_sord_order(column_info_data, column_group_parent_of_child, key_to_id)
    
    # カラム情報およびカラムグループ情報の個数を取得し、menu_info['menu']に格納
    menu_info['menu']['number_item'] = len(column_info_data)
    menu_info['menu']['number_group'] = len(column_group_info_data)
    
    # カラム情報を格納
    menu_info['column'] = column_info_data
    
    # カラムグループ情報を格納
    menu_info['group'] = column_group_info_data
    
    # 情報を返却値に格納
    create_data['menu_info'] = menu_info
    
    return create_data


def _collect_common_menu_create_data(objdbca):
    """
        【内部呼び出し用】メニュー定義・作成用情報の共通部分取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            common_data
    """
    # テーブル/ビュー名
    t_comn_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'
    t_comn_column_group = 'T_COMN_COLUMN_GROUP'
    v_menu_column_class = 'V_MENU_COLUMN_CLASS'
    v_menu_sheet_type = 'V_MENU_SHEET_TYPE'
    v_menu_target_menu_group = 'V_MENU_TARGET_MENU_GROUP'
    v_menu_other_link = 'V_MENU_OTHER_LINK'

    # 変数定義
    lang = g.get('LANGUAGE')

    # カラムクラスの選択肢一覧
    column_class_list = []
    ret = objdbca.table_select(v_menu_column_class, 'ORDER BY DISP_SEQ ASC')
    for record in ret:
        column_class_id = record.get('COLUMN_CLASS_ID')
        # 「11:パラメータシート参照」は未実装のため除外
        if str(column_class_id) == "11":
            continue
        column_class_name = record.get('COLUMN_CLASS_NAME')
        column_class_disp_name = record.get('COLUMN_CLASS_DISP_NAME_' + lang.upper())
        column_class_list.append({'column_class_id': column_class_id, 'column_class_name': column_class_name, 'column_class_disp_name': column_class_disp_name})  # noqa: E501

    # 対象メニューグループの選択肢一覧
    target_menu_group_list = []
    ret = objdbca.table_select(v_menu_target_menu_group, 'ORDER BY DISP_SEQ ASC')
    for record in ret:
        menu_group_id = record.get('MENU_GROUP_ID')
        menu_group_name = record.get('MENU_GROUP_NAME_' + lang.upper())
        full_menu_group_name = record.get('FULL_MENU_GROUP_NAME_' + lang.upper())
        target_menu_group_list.append({'menu_group_id': menu_group_id, 'menu_group_name': menu_group_name, 'full_menu_group_name': full_menu_group_name})  # noqa: E501

    # シートタイプの選択肢一覧
    sheet_type_list = []
    ret = objdbca.table_select(v_menu_sheet_type, 'ORDER BY DISP_SEQ ASC')
    for record in ret:
        sheet_type_id = record.get('SHEET_TYPE_NAME_ID')
        sheet_type_name = record.get('SHEET_TYPE_NAME_' + lang.upper())
        sheet_type_list.append({'sheet_type_id': sheet_type_id, 'sheet_type_name': sheet_type_name})

    # カラムクラス「プルダウン選択」の選択項目一覧
    pulldown_item_list = []
    ret = objdbca.table_select(v_menu_other_link, 'ORDER BY MENU_GROUP_ID ASC')
    for record in ret:
        link_id = record.get('LINK_ID')
        menu_id = record.get('MENU_ID')
        menu_name_rest = record.get('MENU_NAME_REST')
        column_name_rest = record.get('REF_COL_NAME_REST')
        link_pulldown = record.get('LINK_PULLDOWN_' + lang.upper())
        pulldown_item_list.append({'link_id': link_id, 'menu_id': menu_id, 'menu_name_rest': menu_name_rest, 'column_name_rest': column_name_rest, 'link_pulldown': link_pulldown})  # noqa: E501
    
    # ロールの選択肢一覧
    role_list = util.get_workspace_roles()  # noqa: F405
    
    # カラムグループ一覧を取得
    column_group_list = {}
    ret = objdbca.table_select(t_comn_column_group, 'WHERE DISUSE_FLAG = %s', [0])
    for record in ret:
        col_group_id = record.get('COL_GROUP_ID')
        col_group_name = record.get('COL_GROUP_NAME_' + lang.upper())
        column_group_list[col_group_id] = col_group_name
    
    # バリデーションエラー時のkeyと名称を照らし合わせるための一覧
    name_convert_list = {}
    ret = objdbca.table_select(t_comn_menu_column_link, 'WHERE MENU_ID in ("50102", "50103", "50104", "50106") AND DISUSE_FLAG = %s', [0])
    for record in ret:
        column_name_ret = record.get('COLUMN_NAME_REST')
        column_name = record.get('COLUMN_NAME_' + lang.upper())
        col_group_id = record.get('COL_GROUP_ID')
        if col_group_id:
            name_convert_list[column_name_ret] = str(column_group_list.get(col_group_id)) + "/" + column_name
        else:
            name_convert_list[column_name_ret] = column_name
    
    common_data = {
        "column_class_list": column_class_list,
        "target_menu_group_list": target_menu_group_list,
        "sheet_type_list": sheet_type_list,
        "pulldown_item_list": pulldown_item_list,
        "role_list": role_list,
        "name_convert_list": name_convert_list
    }
    
    return common_data


def collect_pulldown_initial_value(objdbca, menu_name_rest, column_name_rest):
    """
        「プルダウン選択」項目で選択した対象の「初期値」候補一覧取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu_name_rest: 対象のmenu_name_rest
            column_name_rest: 対象のcolumn_name_rest
        RETRUN:
            initial_value_dict
    """
    # テーブル/ビュー名
    v_menu_other_link = 'V_MENU_OTHER_LINK'
    
    # 変数定義
    lang = g.get('LANGUAGE')
    initial_value_dict = {}
    
    # 「他メニュー連携」から対象のレコード一覧を取得
    ret = objdbca.table_select(v_menu_other_link, 'WHERE MENU_NAME_REST = %s AND REF_COL_NAME_REST = %s AND DISUSE_FLAG = %s', [menu_name_rest, column_name_rest, 0])  # noqa: E501
    if not ret:
        log_msg_args = [menu_name_rest, column_name_rest]
        api_msg_args = [menu_name_rest, column_name_rest]
        raise AppException("499-00010", log_msg_args, api_msg_args)  # noqa: F405
    
    ref_table_name = ret[0].get('REF_TABLE_NAME')
    ref_pkey_name = ret[0].get('REF_PKEY_NAME')
    ref_col_name = ret[0].get('REF_COL_NAME')
    ref_multi_lang = ret[0].get('REF_MULTI_LANG')
    ref_col_name_rest = ret[0].get('REF_COL_NAME_REST')
    menu_create_flag = ret[0].get('MENU_CREATE_FLAG')
    
    # 「プルダウン選択」の対象テーブルからレコード一覧を取得
    ret = objdbca.table_select(ref_table_name, 'WHERE DISUSE_FLAG = %s', [0])
    for record in ret:
        key = record.get(ref_pkey_name)
        if str(ref_multi_lang) == "1":
            value = record.get(ref_col_name + "_" + lang.upper())
        else:
            value = record.get(ref_col_name)
        
        # メニュー作成機能で作ったメニューの場合、値がJSON形式なので取り出す。
        if str(menu_create_flag) == "1":
            value_dict = ast.literal_eval(value)
            value = value_dict.get(ref_col_name_rest)
        if value:
            initial_value_dict[key] = value
    
    return initial_value_dict


def collect_pulldown_reference_item(objdbca, menu_name_rest, column_name_rest):
    """
        「プルダウン選択」項目で選択した対象の「参照項目」候補一覧取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu_name_rest: 対象のmenu_name_rest
            column_name_rest: 対象のcolumn_name_rest
        RETRUN:
            initial_value_dict
    """
    # テーブル/ビュー名
    v_menu_other_link = 'V_MENU_OTHER_LINK'
    v_menu_reference_item = 'V_MENU_REFERENCE_ITEM'
    
    # 変数定義
    lang = g.get('LANGUAGE')
    reference_item_list = []
    
    # 「他メニュー連携」から対象のレコード一覧を取得
    ret = objdbca.table_select(v_menu_other_link, 'WHERE MENU_NAME_REST = %s AND REF_COL_NAME_REST = %s AND DISUSE_FLAG = %s', [menu_name_rest, column_name_rest, 0])  # noqa: E501
    if not ret:
        log_msg_args = [menu_name_rest, column_name_rest]
        api_msg_args = [menu_name_rest, column_name_rest]
        raise AppException("499-00010", log_msg_args, api_msg_args)  # noqa: F405
    
    # LINK_IDを特定
    link_id = ret[0].get('LINK_ID')
    
    # 「参照項目情報」からLINK_IDに紐づくレコードを取得
    ret = objdbca.table_select(v_menu_reference_item, 'WHERE LINK_ID = %s AND DISUSE_FLAG = %s ORDER BY DISP_SEQ ASC', [link_id, 0])
    if ret:
        for record in ret:
            reference_id = record.get('REFERENCE_ID')
            column_name = record.get('COLUMN_NAME_' + lang.upper())
            column_name_rest = record.get('COLUMN_NAME_REST')
            add_dict = {'reference_id': reference_id, 'column_name': column_name, 'column_name_rest': column_name_rest}
            reference_item_list.append(add_dict)
    
    return reference_item_list


def menu_create_execute(objdbca, exec_target):
    """
        メニュー作成の実行
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            exec_target: メニュー作成の実行対象
        RETRUN:
            result_data
    """
    
    return {"aaa": "bbb"}


def menu_create_define(objdbca, create_param):
    """
        メニュー定義および作成の実行
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            create_param: メニュー定義用パラメータ
        RETRUN:
            result_data
    """
    # typeを取得 (「新規作成(create_new)」「初期化(initialize)」「編集(edit)」)
    type_name = create_param.get('type')
    if type_name not in ['create_new', 'initialize', 'edit']:
        log_msg_args = ["type"]
        api_msg_args = ["type"]
        raise AppException('499-00703', log_msg_args, api_msg_args)  # 対象keyの値が不正です。(key: {}) # noqa: F405
    
    # menu_create_idの有無を確認
    menu_data = check_request_body_key(create_param, 'menu')
    menu_create_id = menu_data.get('menu_create_id')
    
    if type_name == 'create_new' and not menu_create_id:
        # 「新規作成」かつmenu_create_idが無い場合、レコードの登録処理のみ実行し、「メニュー作成履歴」にレコードを登録
        result = _create_new_execute(objdbca, create_param)
    else:
        # menu_create_idがある場合、レコードの登録/更新/廃止処理を実行し、「メニュー作成履歴」にレコードを登録
        result = _create_exist_execute(objdbca, create_param, type_name)
    
    # 返却用の値を取得
    menu_name_rest = result.get('menu_name_rest')
    history_id = result.get('history_id')
    
    result_data = {'menu_name_rest': menu_name_rest, 'history_id': history_id}
    return result_data


def _create_new_execute(objdbca, create_param):  # noqa: C901
    """
        【内部呼び出し用】「新規作成」時のメニュー作成用メニューに対するレコードをの登録（メニュー定義一覧に対象が存在しない）
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            create_param: メニュー定義用パラメータ
        RETRUN:
            result_data
    """
    # 変数定義
    user_id = g.get('USER_ID')
    
    # 登録するためのデータを抽出
    menu_data = check_request_body_key(create_param, 'menu')  # "menu" keyが無かったら400-00002エラー
    column_data_list = create_param.get('column')
    group_data_list = create_param.get('group')
    menu_name_rest = menu_data.get('menu_name_rest')
    
    try:
        # トランザクション開始
        objdbca.db_transaction_start()
        
        # 登録前バリデーションチェック
        retbool, result_code, msg_args = _check_before_registar_validate(objdbca, menu_data, column_data_list)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # 「メニュー定義一覧」にレコードを登録
        retbool, result_code, msg_args, menu_create_id = _insert_t_menu_define(objdbca, menu_data)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # カラムグループ用データがある場合、「カラムグループ作成情報」にレコードを登録
        if group_data_list:
            retbool, result_code, msg_args = _insert_t_menu_column_group(objdbca, group_data_list)
            if not retbool:
                raise Exception(result_code, msg_args)
        
        # 「メニュー項目作成情報」にレコードを登録
        retbool, result_code, msg_args = _insert_t_menu_column(objdbca, menu_data, column_data_list)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # 「一意制約(複数項目)作成情報」にレコードを登録
        retbool, result_code, msg_args = _insert_t_menu_unique_constraint(objdbca, menu_data)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # 「メニュー-ロール作成情報」にレコードを登録
        menu_name = menu_data.get('menu_name')
        role_list = menu_data.get('role_list')
        retbool, result_code, msg_args = _insert_t_menu_role(objdbca, menu_name, role_list)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # 「メニュー作成履歴」にレコードを登録
        status_id = "1"  # (1:未実行)
        create_type = "1"  # (1:新規作成)
        retbool, result_code, msg_args, history_id = _insert_t_menu_create_history(objdbca, menu_create_id, status_id, create_type, user_id)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # コミット/トランザクション終了
        objdbca.db_transaction_end(True)
        
    except Exception as e:
        # ロールバック トランザクション終了
        objdbca.db_transaction_end(False)
        
        # エラー判定
        if len(e.args) == 2:
            # result_codeとmsg_argsを取得
            result_code = '{}'.format(e.args[0])
            msg_args = eval('{}'.format(e.args[1]))
            log_msg_args = msg_args
            api_msg_args = msg_args
        else:
            # システムエラー
            result_code = '999-99999'
            log_msg_args = []
            api_msg_args = []
        raise AppException(result_code, log_msg_args, api_msg_args)  # noqa: F405

    result_data = {
        'menu_name_rest': menu_name_rest,
        'history_id': history_id
    }
    
    return result_data


def _create_exist_execute(objdbca, create_param, type_name):  # noqa: C901
    """
        【内部呼び出し用】「新規作成」「初期化」「編集」時のメニュー作成用メニューに対するレコードの登録/更新/廃止
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            create_param: メニュー定義用パラメータ
            type_name: create_new, initialize, editのいずれか
        RETRUN:
            result_data
    """
    # テーブル名
    t_menu_define = 'T_MENU_DEFINE'
    t_menu_column = 'T_MENU_COLUMN'
    t_menu_unique_constraint = 'T_MENU_UNIQUE_CONSTRAINT'
    t_menu_role = 'T_MENU_ROLE'
    
    # 変数定義
    user_id = g.get('USER_ID')
    
    # データを抽出
    menu_data = check_request_body_key(create_param, 'menu')  # "menu" keyが無かったら400-00002エラー
    column_data_list = check_request_body_key(create_param, 'column')  # "column" keyが無かったら400-00002エラー
    group_data_list = create_param.get('group')
    menu_name_rest = menu_data.get('menu_name_rest')
    
    try:
        # トランザクション開始
        objdbca.db_transaction_start()
        
        # 登録前バリデーションチェック
        retbool, result_code, msg_args = _check_before_registar_validate(objdbca, menu_data, column_data_list)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # 対象の「メニュー定義一覧」のuuidおよびメニュー名を取得
        menu_create_id = menu_data.get('menu_create_id')
        menu_name = menu_data.get('menu_name')
        
        # 現在の「メニュー定義一覧」のレコードを取得
        current_t_menu_define = objdbca.table_select(t_menu_define, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s', [menu_create_id, 0])
        if not current_t_menu_define:
            # 「メニュー定義一覧」に対象のmenu_create_idのレコードが存在しない場合
            raise Exception("499-00703", ["menu_create_id"])  # 対象keyの値が不正です。(key: {})
        current_t_menu_define = current_t_menu_define[0]
        
        # 「メニュー定義一覧」のレコードを更新
        retbool, result_code, msg_args = _update_t_menu_define(objdbca, current_t_menu_define, menu_data, type_name)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # カラムグループ用データがある場合、「カラムグループ作成情報」にレコードを登録
        if group_data_list:
            retbool, result_code, msg_args = _insert_t_menu_column_group(objdbca, group_data_list)
            if not retbool:
                raise Exception(result_code, msg_args)
        
        # 現在の「メニュー項目作成情報」のレコードを取得
        current_t_menu_column_list = objdbca.table_select(t_menu_column, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s', [menu_create_id, 0])
        
        # 「メニュー項目作成情報」から未使用となる項目のレコードを廃止
        retbool, result_code, msg_args = _disuse_t_menu_column(objdbca, current_t_menu_column_list, column_data_list)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # 「メニュー項目作成情報」から更新対象のレコードを更新
        retbool, result_code, msg_args = _update_t_menu_column(objdbca, current_t_menu_column_list, column_data_list, type_name)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # 「メニュー項目作成情報」に新規追加項目用レコードを登録
        retbool, result_code, msg_args = _insert_t_menu_column(objdbca, menu_data, column_data_list)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # 現在の「一意制約(複数項目)作成情報」のレコードを取得
        current_t_menu_unique_constraint = objdbca.table_select(t_menu_unique_constraint, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s', [menu_create_id, 0])  # noqa: E501
        
        # 「一意制約(複数項目)」の値があり、かつ「一意制約(複数項目)作成情報」にレコードが存在する場合、レコードを更新
        unique_constraint = menu_data.get('unique_constraint')
        if current_t_menu_unique_constraint and unique_constraint:
            target_record = current_t_menu_unique_constraint[0]
            retbool, result_code, msg_args = _update_t_menu_unique_constraint(objdbca, menu_data, target_record)
            if not retbool:
                raise Exception(result_code, msg_args)
        
        # 「一意制約(複数項目)」の値がない、かつ「一意制約(複数項目)作成情報」にレコードが存在する場合、レコードを廃止
        elif current_t_menu_unique_constraint and not unique_constraint:
            target_record = current_t_menu_unique_constraint[0]
            retbool, result_code, msg_args = _disuse_t_menu_unique_constraint(objdbca, target_record)
            if not retbool:
                raise Exception(result_code, msg_args)
        
        # 「一意制約(複数項目)」の値があり、かつ「一意制約(複数項目)作成情報」にレコードが存在しない場合、レコードを登録
        elif not current_t_menu_unique_constraint and unique_constraint:
            retbool, result_code, msg_args = _insert_t_menu_unique_constraint(objdbca, menu_data)
            if not retbool:
                raise Exception(result_code, msg_args)
        
        # 「ロール選択」の値を取得
        role_list = menu_data.get('role_list')
        
        # 現在の「メニュー-ロール作成情報」のレコードを取得
        current_t_menu_role = objdbca.table_select(t_menu_role, 'WHERE MENU_CREATE_ID = %s AND DISUSE_FLAG = %s', [menu_create_id, 0])
        current_role_list = []
        current_role_dict = {}
        if current_t_menu_role:
            for record in current_t_menu_role:
                menu_role_id = record.get('MENU_ROLE_ID')
                role = record.get('ROLE_ID')
                last_update_timestamp = record.get('LAST_UPDATE_TIMESTAMP')
                last_update_date_time = last_update_timestamp.strftime('%Y/%m/%d %H:%M:%S.%f')
                current_role_list.append(role)
                current_role_dict[role] = {"menu_role_id": menu_role_id, 'last_update_date_time': last_update_date_time}
        
        # 新規に登録するロールの対象一覧を取得し、レコードを追加
        add_role_list = set(role_list) - set(current_role_list)
        if list(add_role_list):
            retbool, result_code, msg_args = _insert_t_menu_role(objdbca, menu_name, list(add_role_list))
            if not retbool:
                raise Exception(result_code, msg_args)
        
        # 廃止するロールの対象一覧を取得し、レコードを廃止
        disuse_role_list = set(current_role_list) - set(role_list)
        if list(disuse_role_list):
            retbool, result_code, msg_args = _disuse_t_menu_role(objdbca, list(disuse_role_list), current_role_dict)
            if not retbool:
                raise Exception(result_code, msg_args)
        
        # 「メニュー作成履歴」にレコードを登録
        status_id = "1"  # (1:未実行)
        if type_name == "create_new":
            create_type = "1"  # (1:新規作成)
        elif type_name == "initialize":
            create_type = "2"  # (2:初期化)
        elif type_name == "edit":
            create_type = "3"  # (3:編集)
        retbool, result_code, msg_args, history_id = _insert_t_menu_create_history(objdbca, menu_create_id, status_id, create_type, user_id)
        if not retbool:
            raise Exception(result_code, msg_args)
        
        # コミット/トランザクション終了
        objdbca.db_transaction_end(True)

    except Exception as e:
        # ロールバック トランザクション終了
        objdbca.db_transaction_end(False)
        
        # エラー判定
        if len(e.args) == 2:
            # result_codeとmsg_argsを取得
            result_code = '{}'.format(e.args[0])
            msg_args = eval('{}'.format(e.args[1]))
            log_msg_args = msg_args
            api_msg_args = msg_args
        else:
            # システムエラー
            result_code = '999-99999'
            log_msg_args = []
            api_msg_args = []
        raise AppException(result_code, log_msg_args, api_msg_args)  # noqa: F405

    result_data = {
        'menu_name_rest': menu_name_rest,
        'history_id': history_id
    }
    
    return result_data


def _insert_t_menu_define(objdbca, menu_data):
    """
        【内部呼び出し用】「メニュー定義一覧」にレコードを登録
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu_data: 登録対象のメニュー情報
        RETRUN:
            boolean, result_code, msg_args, menu_create_id
    """
    try:
        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'menu_definition_list')  # noqa: F405
        
        # 縦メニュー利用有無のkeyが無い場合はFalseを指定
        vertical = menu_data.get('vertical')
        if not vertical:
            vertical = "False"
        
        # 登録用パラメータを作成
        parameters = {
            "parameter": {
                "menu_name_ja": menu_data.get('menu_name'),  # メニュー名称(ja)
                "menu_name_en": menu_data.get('menu_name'),  # メニュー名称(en)
                "menu_name_rest": menu_data.get('menu_name_rest'),  # メニュー名称(rest)
                "sheet_type": menu_data.get('sheet_type'),  # シートタイプ名
                "display_order": menu_data.get('display_order'),  # 表示順序
                "description_ja": menu_data.get('description'),  # 説明(ja)
                "description_en": menu_data.get('description'),  # 説明(en)
                "remarks": menu_data.get('remarks'),  # 備考
                "vertical": vertical,  # 縦メニュー利用有無
                "menu_group_for_input": menu_data.get('menu_group_for_input'),  # 入力用メニューグループ名
                "menu_group_for_subst": menu_data.get('menu_group_for_subst'),  # 代入値自動登録用メニューグループ名
                "menu_group_for_ref": menu_data.get('menu_group_for_ref')  # 参照用メニューグループ名
            },
            "type": "Register"
        }

        # 登録を実行
        exec_result = objmenu.exec_maintenance(parameters)  # noqa: F405
        if not exec_result[0]:
            result_msg = _format_loadtable_msg(exec_result[2])
            result_msg = json.dumps(result_msg, ensure_ascii=False)
            raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー
        
        # 登録されたレコードのUUIDを保管
        menu_create_id = exec_result[1].get('uuid')
            
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args, None
    
    return True, None, None, menu_create_id


def _update_t_menu_define(objdbca, current_t_menu_define, menu_data, type_name):
    """
        【内部呼び出し用】「メニュー定義一覧」のレコードを更新
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            current_t_menu_define: 「メニュー定義一覧」の更新対象のレコード
            menu_data: 登録対象のメニュー情報
            type_name: 新規作成(create_new), 初期化(initialize), 編集(edit)のいずれか
        RETRUN:
            boolean, result_code, msg_args
    """
    # テーブル/ビュー名
    v_menu_sheet_type = 'V_MENU_SHEET_TYPE'
    
    # 変数定義
    lang = g.get('LANGUAGE')
    
    try:
        # 更新対象レコードの「メニュー作成状態」が「1:未作成」の場合「初期化」「編集」はできないのでエラー判定
        menu_create_done_status = str(current_t_menu_define.get('MENU_CREATE_DONE_STATUS'))
        if (type_name == 'edit') and menu_create_done_status == "1":
            raise Exception("499-00709", [])  # 「メニュー定義一覧」の更新対象のレコードの「メニュー作成状態」が「未作成」の場合「初期化」および「編集」は実行できません
        
        # 更新対象レコードの「メニュー作成状態」が「2:作成済み」の場合「新規作成」はできないのでエラー判定
        menu_create_done_status = str(current_t_menu_define.get('MENU_CREATE_DONE_STATUS'))
        if type_name == 'create_new' and menu_create_done_status == "2":
            raise Exception("499-00710", [])  # 「メニュー定義一覧」の更新対象のレコードの「メニュー作成状態」が「作成済み」の場合「新規作成」は実行できません
        
        # 各種メニュー名称を取得
        menu_name_ja = menu_data.get('menu_name')
        menu_name_en = menu_data.get('menu_name')
        menu_name_rest = menu_data.get('menu_name_rest')
        
        # 「シートタイプ」「縦メニュー利用」を取得
        sheet_type = str(menu_data.get('sheet_type'))
        vertical = menu_data.get('vertical')
        
        # 縦メニュー利用有無のkeyが無い場合はFalseを指定
        if not vertical:
            vertical = "False"
        
        # 「初期化」「編集」の場合のみチェックするバリデーション
        if type_name == 'initialize' or type_name == 'edit':
            current_menu_name_rest = current_t_menu_define.get('MENU_NAME_REST')
            if not current_menu_name_rest == menu_name_rest:
                raise Exception("499-00704", ["menu_name_rest"])  # 「初期化」「編集」の際は対象の値を変更できません。(対象: {})
        
        # 「編集」の場合のみチェックするバリデーション
        if type_name == 'edit':
            current_sheet_type = str(current_t_menu_define.get('SHEET_TYPE'))
            current_vertical = str(current_t_menu_define.get('VERTICAL'))
            
            # シートタイプのIDと名称の紐付け取得
            sheet_type_list = objdbca.table_select(v_menu_sheet_type, 'ORDER BY DISP_SEQ ASC')
            sheet_type_dict = {}
            for record in sheet_type_list:
                sheet_type_name_id = record.get('SHEET_TYPE_NAME_ID')
                sheet_type_dict[sheet_type_name_id] = record.get('SHEET_TYPE_NAME_' + lang.upper())
            
            current_sheet_type_name = sheet_type_dict[current_sheet_type]  # シートタイプ名称
            if not current_sheet_type_name == sheet_type:
                raise Exception("499-00704", ["sheet_type"])  # 「初期化」「編集」の際は対象の値を変更できません。(対象: {})
            
            vertical_id = "1" if vertical == "True" else "0"
            if not current_vertical == vertical_id:
                raise Exception("499-00704", ["vertical"])  # 「初期化」「編集」の際は対象の値を変更できません。(対象: {})
        
        # 対象のuuidを取得
        menu_create_id = menu_data.get('menu_create_id')
        
        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'menu_definition_list')  # noqa: F405
        
        # 更新用パラメータを作成
        if type_name == "create_new":
            parameters = {
                "parameter": {
                    "menu_name_ja": menu_name_ja,  # メニュー名称(ja)
                    "menu_name_en": menu_name_en,  # メニュー名称(en)
                    "menu_name_rest": menu_name_rest,  # メニュー名称(rest)
                    "sheet_type": sheet_type,  # シートタイプ名
                    "display_order": menu_data.get('display_order'),  # 表示順序
                    "description_ja": menu_data.get('description'),  # 説明(ja)
                    "description_en": menu_data.get('description'),  # 説明(en)
                    "remarks": menu_data.get('remarks'),  # 備考
                    "vertical": vertical,  # 縦メニュー利用有無
                    "menu_group_for_input": menu_data.get('menu_group_for_input'),  # 入力用メニューグループ名
                    "menu_group_for_subst": menu_data.get('menu_group_for_subst'),  # 代入値自動登録用メニューグループ名
                    "menu_group_for_ref": menu_data.get('menu_group_for_ref'),  # 参照用メニューグループ名
                    "last_update_date_time": menu_data.get('last_update_date_time')  # 最終更新日時
                },
                "type": "Update"
            }
        elif type_name == "initialize" or type_name == "edit":
            parameters = {
                "parameter": {
                    "menu_name_ja": menu_name_ja,  # メニュー名称(ja)
                    "menu_name_en": menu_name_en,  # メニュー名称(en)
                    "sheet_type": sheet_type,  # シートタイプ名
                    "display_order": menu_data.get('display_order'),  # 表示順序
                    "description_ja": menu_data.get('description'),  # 説明(ja)
                    "description_en": menu_data.get('description'),  # 説明(en)
                    "remarks": menu_data.get('remarks'),  # 備考
                    "vertical": vertical,  # 縦メニュー利用有無
                    "menu_group_for_input": menu_data.get('menu_group_for_input'),  # 入力用メニューグループ名
                    "menu_group_for_subst": menu_data.get('menu_group_for_subst'),  # 代入値自動登録用メニューグループ名
                    "menu_group_for_ref": menu_data.get('menu_group_for_ref'),  # 参照用メニューグループ名
                    "last_update_date_time": menu_data.get('last_update_date_time')  # 最終更新日時
                },
                "type": "Update"
            }
        
        # 「メニュー定義一覧」のレコードを更新
        exec_result = objmenu.exec_maintenance(parameters, menu_create_id)  # noqa: F405
        if not exec_result[0]:
            result_msg = _format_loadtable_msg(exec_result[2])
            result_msg = json.dumps(result_msg, ensure_ascii=False)
            raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー

    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args
    
    return True, None, None


def _insert_t_menu_column_group(objdbca, group_data_list):
    """
        【内部呼び出し用】「カラムグループ作成情報」にレコードを登録
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            group_data_list: 登録対象のカラムグループ一覧
        RETRUN:
            boolean, result_code, msg_args
    """
    # テーブル名
    t_menu_column_group = 'T_MENU_COLUMN_GROUP'
    
    # 変数定義
    lang = g.get('LANGUAGE')
    
    try:
        # 現在登録されている「カラムグループ作成情報」のレコード一覧を取得
        column_group_list = objdbca.table_select(t_menu_column_group, 'WHERE DISUSE_FLAG = %s', [0])
        
        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'column_group_creation_info')  # noqa: F405
        
        # 「カラムグループ作成情報」登録処理のループスタート
        for num, group_data in group_data_list.items():
            # 登録用パラメータを作成
            col_group_name_ja = group_data.get('col_group_name')
            col_group_name_en = group_data.get('col_group_name')
            parent_full_col_group_name = group_data.get('parent_full_col_group_name')
            
            # 親カラムグループがあれば、対象の「フルカラムグループ名」を取得
            parent_column_group = None
            if parent_full_col_group_name:
                if lang.lower() == 'ja':
                    target_parent = objdbca.table_select(t_menu_column_group, 'WHERE FULL_COL_GROUP_NAME_JA = %s AND DISUSE_FLAG = %s', [parent_full_col_group_name, 0])  # noqa: E501
                elif lang.lower() == 'en':
                    target_parent = objdbca.table_select(t_menu_column_group, 'WHERE FULL_COL_GROUP_NAME_EN = %s AND DISUSE_FLAG = %s', [parent_full_col_group_name, 0])  # noqa: E501
                
                # 対象となる親カラムグループIDが存在しない場合
                if not target_parent:
                    raise Exception("499-00703", ["group"])  # 対象keyの値が不正です。(key: {})
                
                # 『親フルカラムグループ/カラムグループ名』の命名規則でフルカラムグループ名を作成。
                parent_full_name_ja = target_parent[0].get('FULL_COL_GROUP_NAME_JA')
                parent_full_name_en = target_parent[0].get('FULL_COL_GROUP_NAME_EN')
                full_column_group_name_ja = parent_full_name_ja + '/' + col_group_name_ja
                full_column_group_name_en = parent_full_name_en + '/' + col_group_name_en
                
                parent_full_name = target_parent[0].get('FULL_COL_GROUP_NAME_' + lang.upper())
                parent_column_group = parent_full_name
                
            else:
                full_column_group_name_ja = col_group_name_ja
                full_column_group_name_en = col_group_name_en
            
            # 『「フルカラムグループ(ja)」』か『「フルカラムグループ(en)」』ですでに同じレコードがあれば処理をスキップ
            skip_flag = False
            for record in column_group_list:
                if full_column_group_name_ja == record.get('FULL_COL_GROUP_NAME_JA') or full_column_group_name_en == record.get('FULL_COL_GROUP_NAME_EN'):  # noqa: E501
                    skip_flag = True
            
            if skip_flag:
                continue
            
            # 登録用パラメータを作成
            parameters = {
                "parameter": {
                    "parent_column_group": parent_column_group,
                    "column_group_name_ja": col_group_name_ja,
                    "column_group_name_en": col_group_name_en,
                },
                "type": "Register"
            }
            
            # 登録を実行
            exec_result = objmenu.exec_maintenance(parameters)  # noqa: F405
            if not exec_result[0]:
                result_msg = _format_loadtable_msg(exec_result[2])
                result_msg = json.dumps(result_msg, ensure_ascii=False)
                raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー
            
            # 現在登録されている「カラムグループ作成情報」のレコード一覧を更新
            column_group_list = objdbca.table_select(t_menu_column_group, 'WHERE DISUSE_FLAG = %s', [0])
            
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args
    
    return True, None, None


def _insert_t_menu_column(objdbca, menu_data, column_data_list):
    """
        【内部呼び出し用】「メニュー項目作成情報」にレコードを登録
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu_data: 登録対象のメニュー情報
            column_data_list: 登録対象のカラム情報一覧
        RETRUN:
            boolean, result_code, msg_args
    """
    try:
        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'menu_item_creation_info')  # noqa: F405
        
        # menu_dataから登録用のメニュー名を取得
        menu_name = menu_data.get('menu_name')
        
        # 「メニュー項目作成情報」登録処理のループスタート
        for column_data in column_data_list.values():
            # create_column_idが空(null)のもののみ対象とする
            create_column_id = column_data.get('create_column_id')
            if not create_column_id:
                # 登録用パラメータを作成
                column_class = column_data.get('column_class')
                parameter = {
                    "menu_name": menu_name,  # メニュー名(「メニュー定義一覧」のメニュー名)
                    "item_name_ja": column_data.get('item_name'),  # 項目名(ja)
                    "item_name_en": column_data.get('item_name'),  # 項目名(en)
                    "item_name_rest": column_data.get('item_name_rest'),  # 項目名(rest)
                    "description_ja": column_data.get('description'),  # 説明(ja)
                    "description_en": column_data.get('description'),  # 説明(en)
                    "column_class": column_class,  # カラムクラス
                    "display_order": column_data.get('display_order'),  # 表示順序
                    "required": column_data.get('required'),  # 必須
                    "uniqued": column_data.get('uniqued'),  # 一意制約
                    "remarks": column_data.get('remarks'),  # 備考
                }
                
                # カラムグループがある場合
                column_group = column_data.get('column_group')
                if column_group:
                    parameter["column_group"] = column_group  # カラムグループ(「カラムグループ作成情報」のフルカラムグループ名)
                
                # カラムクラス「文字列(単一行)」用のパラメータを追加
                if column_class == "SingleTextColumn":
                    single_string_maximum_bytes = None if not column_data.get('single_string_maximum_bytes') else column_data.get('single_string_maximum_bytes')  # noqa: E501
                    parameter["single_string_maximum_bytes"] = single_string_maximum_bytes  # 文字列(単一行) 最大バイト数
                    parameter["single_string_regular_expression"] = column_data.get('single_string_regular_expression')  # 文字列(単一行) 正規表現
                    parameter["single_string_default_value"] = column_data.get('single_string_default_value')  # 文字列(単一行) 初期値
                
                # カラムクラス「文字列(複数行)」用のパラメータを追加
                if column_class == "MultiTextColumn":
                    multi_string_maximum_bytes = None if not column_data.get('multi_string_maximum_bytes') else column_data.get('multi_string_maximum_bytes')  # noqa: E501
                    parameter["multi_string_maximum_bytes"] = multi_string_maximum_bytes  # 文字列(複数行) 最大バイト数
                    parameter["multi_string_regular_expression"] = column_data.get('multi_string_regular_expression')  # 文字列(複数行) 正規表現
                    parameter["multi_string_default_value"] = column_data.get('multi_string_default_value')  # 文字列(複数行) 初期値
                
                # カラムクラス「整数」用のパラメータを追加
                if column_class == "NumColumn":
                    integer_maximum_value = None if not column_data.get('integer_maximum_value') else column_data.get('integer_maximum_value')
                    integer_minimum_value = None if not column_data.get('integer_minimum_value') else column_data.get('integer_minimum_value')
                    integer_default_value = None if not column_data.get('integer_default_value') else column_data.get('integer_default_value')
                    parameter["integer_maximum_value"] = integer_maximum_value  # 整数 最大値
                    parameter["integer_minimum_value"] = integer_minimum_value  # 整数 最小値
                    parameter["integer_default_value"] = integer_default_value  # 整数 初期値
                
                # カラムクラス「小数」用のパラメータを追加
                if column_class == "FloatColumn":
                    decimal_maximum_value = None if not column_data.get('decimal_maximum_value') else column_data.get('decimal_maximum_value')
                    decimal_minimum_value = None if not column_data.get('decimal_minimum_value') else column_data.get('decimal_minimum_value')
                    decimal_digit = None if not column_data.get('decimal_digit') else column_data.get('decimal_digit')
                    decimal_default_value = None if not column_data.get('decimal_default_value') else column_data.get('decimal_default_value')
                    parameter["decimal_maximum_value"] = decimal_maximum_value  # 小数 最大値
                    parameter["decimal_minimum_value"] = decimal_minimum_value  # 小数 最小値
                    parameter["decimal_digit"] = decimal_digit  # 小数 桁数
                    parameter["decimal_default_value"] = decimal_default_value  # 小数 初期値
                
                # カラムクラス「日時」用のパラメータを追加
                if column_class == "DateTimeColumn":
                    parameter["detetime_default_value"] = None if not column_data.get('detetime_default_value') else column_data.get('detetime_default_value')  # 日時 初期値 # noqa: E501
                
                # カラムクラス「日付」用のパラメータを追加
                if column_class == "DateColumn":
                    parameter["dete_default_value"] = None if not column_data.get('dete_default_value') else column_data.get('dete_default_value')  # 日付 初期値 # noqa: E501
                
                # カラムクラス「プルダウン選択」用のパラメータを追加
                if column_class == "IDColumn":
                    parameter["pulldown_selection"] = column_data.get('pulldown_selection')  # プルダウン選択 メニューグループ:メニュー:項目
                    parameter["pulldown_selection_default_value"] = column_data.get('pulldown_selection_default_value')  # プルダウン選択 初期値
                    reference_item = column_data.get('reference_item')
                    if reference_item:
                        reference_item_dump = json.dumps(reference_item)
                        parameter["reference_item"] = str(reference_item_dump)  # プルダウン選択 参照項目
                    else:
                        parameter["reference_item"] = None
                
                # カラムクラス「パスワード」用のパラメータを追加
                if column_class == "PasswordColumn":
                    password_maximum_bytes = None if not column_data.get('password_maximum_bytes') else column_data.get('password_maximum_bytes')
                    parameter["password_maximum_bytes"] = password_maximum_bytes  # パスワード 最大バイト数
                
                # カラムクラス「ファイルアップロード」用のパラメータを追加
                if column_class == "FileUploadColumn":
                    file_upload_maximum_bytes = None if not column_data.get('file_upload_maximum_bytes') else column_data.get('file_upload_maximum_bytes')  # noqa: E501
                    parameter["file_upload_maximum_bytes"] = file_upload_maximum_bytes  # ファイルアップロード 最大バイト数
                
                # カラムクラス「リンク」用のパラメータを追加
                if column_class == "HostInsideLinkTextColumn":
                    link_maximum_bytes = None if not column_data.get('link_maximum_bytes') else column_data.get('link_maximum_bytes')
                    parameter["link_maximum_bytes"] = link_maximum_bytes  # リンク 最大バイト数
                    parameter["link_default_value"] = column_data.get('link_default_value')  # リンク 初期値
                
                # カラムクラス「パラメータシート参照」用のパラメータを追加 (未実装)
                # if column_class == "LinkIDColumn":
                #     parameter["parameter_sheet_reference"] = column_data.get('parameter_sheet_reference')  # パラメータシート参照
                parameters = {
                    "parameter": parameter,
                    "type": "Register"
                }
                
                # 登録を実行
                exec_result = objmenu.exec_maintenance(parameters)  # noqa: F405
                if not exec_result[0]:
                    result_msg = _format_loadtable_msg(exec_result[2])
                    result_msg = json.dumps(result_msg, ensure_ascii=False)
                    raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー
                
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args
    
    return True, None, None


def _update_t_menu_column(objdbca, current_t_menu_column_list, column_data_list, type_name):  # noqa: C901
    """
        【内部呼び出し用】「メニュー項目作成情報」のレコードを更新する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            current_t_menu_column_list: 「メニュー項目作成情報」の現在登録されているレコード（対象メニューのMENU_CREATE_IDと紐づいているもの）
            column_data_list: 登録対象のカラム情報一覧
            type_name: 初期化(initialize), 編集(edit)のいずれか
        RETRUN:
            boolean, result_code, msg_args
    """
    # テーブル/ビュー名
    v_menu_other_link = 'V_MENU_OTHER_LINK'
    v_menu_column_class = 'V_MENU_COLUMN_CLASS'
    
    # 変数定義
    lang = g.get('LANGUAGE')
    
    try:
        # current_t_menu_column_listのレコードについて、create_column_idをkeyにしたdict型に変換
        current_t_menu_column_dict = {}
        for record in current_t_menu_column_list:
            create_column_id = record.get('CREATE_COLUMN_ID')
            current_t_menu_column_dict[create_column_id] = record
        
        # 現在登録されている「他メニュー連携」のレコードを取得
        other_menu_link_list = objdbca.table_select(v_menu_other_link, 'WHERE DISUSE_FLAG = %s', [0])
        
        # 「他メニュー連携」のレコードをLINK_IDをkeyとしたdict型に変換
        format_other_menu_link_list = {}
        for record in other_menu_link_list:
            link_pulldown_ja = record.get('LINK_PULLDOWN_JA')
            link_pulldown_en = record.get('LINK_PULLDOWN_EN')
            format_other_menu_link_list[record.get('LINK_ID')] = {'link_pulldown_ja': link_pulldown_ja, 'link_pulldown_en': link_pulldown_en}
        
        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'menu_item_creation_info')  # noqa: F405
        
        # 「メニュー項目作成情報」更新処理のループスタート
        for column_data in column_data_list.values():
            # 更新対象のuuidを取得
            create_column_id = column_data.get('create_column_id')
            
            # 更新対象の最終更新日時を取得
            last_update_date_time = column_data.get('last_update_date_time')
            
            if create_column_id:
                # 対象のカラムクラスを取得
                column_class = column_data.get('column_class')
                item_name = column_data.get('item_name')
                
                # 「編集」の場合、登録済みレコードとの差分によるバリデーションチェックを行う
                if type_name == 'edit':
                    # カラムクラスのIDと名称の紐付け取得
                    column_class_list = objdbca.table_select(v_menu_column_class, 'ORDER BY DISP_SEQ ASC')
                    column_class_dict = {}
                    for record in column_class_list:
                        column_class_id = record.get('COLUMN_CLASS_ID')
                        column_class_dict[column_class_id] = record.get('COLUMN_CLASS_NAME')
                    
                    # 更新対象の現在のレコードを取得
                    target_record = current_t_menu_column_dict.get(create_column_id)
                    
                    # 「カラムクラス」が変更されている場合エラー判定
                    current_column_class_id = target_record.get('COLUMN_CLASS')
                    current_column_class_name = column_class_dict.get(current_column_class_id)
                    if not column_class == current_column_class_name:
                        raise Exception("499-00706", [item_name, "column_class"])  # 「編集」の際は既存項目の対象の設定を変更できません。(項目: {}, 対象: {})
                    
                    # 「必須」が変更されている場合エラー判定
                    current_required_id = str(target_record.get('REQUIRED'))
                    update_required_id = "1" if column_data.get('required') == "True" else "0"
                    if not current_required_id == update_required_id:
                        raise Exception("499-00706", [item_name, "required"])  # 「編集」の際は既存項目の対象の設定を変更できません。(項目: {}, 対象: {})
                    
                    # 「一意制約」が変更されている場合エラー判定
                    current_uniqued_id = str(target_record.get('UNIQUED'))
                    update_uniqued_id = "1" if column_data.get('uniqued') == "True" else "0"
                    if not current_uniqued_id == update_uniqued_id:
                        raise Exception("499-00706", [item_name, "uniqued"])  # 「編集」の際は既存項目の対象の設定を変更できません。(項目: {}, 対象: {})
                    
                    # カラムクラス「文字列(単一行)」の場合のバリデーションチェック
                    if column_class == "SingleTextColumn":
                        # 最大バイト数が既存の値よりも下回っている場合エラー判定
                        current_single_string_maximum_bytes = int(target_record.get('SINGLE_MAX_LENGTH'))
                        update_single_string_maximum_bytes = int(column_data.get('single_string_maximum_bytes'))
                        if current_single_string_maximum_bytes > update_single_string_maximum_bytes:
                            raise Exception("499-00707", [item_name, "single_string_maximum_bytes"])  # 「編集」の際は既存項目の対象の値が下回る変更はできません。(項目: {}, 対象: {})
                    
                    # カラムクラス「文字列(複数行)」の場合のバリデーションチェック
                    if column_class == "MultiTextColumn":
                        # 最大バイト数が既存の値よりも下回っている場合エラー判定
                        current_multi_string_maximum_bytes = int(target_record.get('MULTI_MAX_LENGTH'))
                        update_multi_string_maximum_bytes = int(column_data.get('multi_string_maximum_bytes'))
                        if current_multi_string_maximum_bytes > update_multi_string_maximum_bytes:
                            raise Exception("499-00707", [item_name, "multi_string_maximum_bytes"])  # 「編集」の際は既存項目の対象の値が下回る変更はできません。(項目: {}, 対象: {})
                    
                    # カラムクラス「整数」の場合のバリデーションチェック
                    if column_class == "NumColumn":
                        current_integer_minimum_value = None if not target_record.get('NUM_MIN') else int(target_record.get('NUM_MIN'))
                        update_integer_minimum_value = None if not column_data.get('integer_minimum_value') else int(column_data.get('integer_minimum_value'))  # noqa: E501
                        # 最小値が既存の値よりも上回っている場合エラー判定
                        if current_integer_minimum_value and update_integer_minimum_value:
                            if current_integer_minimum_value < update_integer_minimum_value:
                                raise Exception("499-00708", [item_name, "integer_minimum_value"])  # 「編集」の際は既存項目の対象の値が上回る変更はできません。(項目: {}, 対象: {})
                        
                        current_integer_maximum_value = None if not target_record.get('NUM_MAX') else int(target_record.get('NUM_MAX'))
                        update_integer_maximum_value = None if not column_data.get('integer_maximum_value') else int(column_data.get('integer_maximum_value'))  # noqa: E501
                        # 最大値が既存の値よりも下回っている場合エラー判定
                        if current_integer_maximum_value and update_integer_maximum_value:
                            if current_integer_maximum_value > update_integer_maximum_value:
                                raise Exception("499-00707", [item_name, "integer_maximum_value"])  # 「編集」の際は既存項目の対象の値が下回る変更はできません。(項目: {}, 対象: {})
                    
                    # カラムクラス「小数」の場合のバリデーションチェック
                    if column_class == "FloatColumn":
                        current_decimal_minimum_value = None if not target_record.get('FLOAT_MIN') else int(target_record.get('FLOAT_MIN'))
                        update_decimal_minimum_value = None if not column_data.get('decimal_minimum_value') else int(column_data.get('decimal_minimum_value'))  # noqa: E501
                        # 最小値が既存の値よりも上回っている場合エラー判定
                        if current_decimal_minimum_value and update_decimal_minimum_value:
                            if current_decimal_minimum_value < update_decimal_minimum_value:
                                raise Exception("499-00708", [item_name, "decimal_minimum_value"])  # 「編集」の際は既存項目の対象の値が上回る変更はできません。(項目: {}, 対象: {})
                        
                        current_decimal_maximum_value = None if not target_record.get('FLOAT_MAX') else int(target_record.get('FLOAT_MAX'))
                        update_decimal_maximum_value = None if not column_data.get('decimal_maximum_value') else int(column_data.get('decimal_maximum_value'))  # noqa: E501
                        # 最大値が既存の値よりも下回っている場合エラー判定
                        if current_decimal_maximum_value and update_decimal_maximum_value:
                            if current_decimal_maximum_value > update_decimal_maximum_value:
                                raise Exception("499-00707", [item_name, "decimal_maximum_value"])  # 「編集」の際は既存項目の対象の値が下回る変更はできません。(項目: {}, 対象: {})
                        
                        current_decimal_digit = None if not target_record.get('FLOAT_DIGIT') else int(target_record.get('FLOAT_DIGIT'))
                        update_decimal_digit = None if not column_data.get('decimal_digit') else int(column_data.get('decimal_digit'))  # noqa: E501
                        # 桁数が既存の値よりも下回っている場合エラー判定
                        if current_decimal_digit and update_decimal_digit:
                            if current_decimal_digit > update_decimal_digit:
                                raise Exception("499-00707", [item_name, "decimal_digit"])  # 「編集」の際は既存項目の対象の値が下回る変更はできません。(項目: {}, 対象: {})
                    
                    # カラムクラス「プルダウン選択」の場合のバリデーションチェック
                    if column_class == "IDColumn":
                        update_pulldown_selection = column_data.get('pulldown_selection')
                        
                        # 現在設定されているIDのlink_pulldownを取得
                        current_other_menu_link_id = target_record.get('OTHER_MENU_LINK_ID')
                        current_other_menu_link_data = format_other_menu_link_list.get(current_other_menu_link_id)
                        current_pulldown_selection = current_other_menu_link_data.get('link_pulldown_' + lang.lower())
                        
                        # pulldown_selectionが変更されている場合エラー判定
                        if not update_pulldown_selection == current_pulldown_selection:
                            raise Exception("499-00706", [item_name, "pulldown_selection"])  # 「編集」の際は既存項目の対象の設定を変更できません。(項目: {}, 対象: {})
                        
                        # 現在設定されているIDのreference_itemを取得
                        current_reference_item = target_record.get('REFERENCE_ITEM')
                        update_reference_item_list = column_data.get('reference_item')
                        if update_reference_item_list:
                            update_reference_item_dump = json.dumps(update_reference_item_list)
                            update_reference_item = str(update_reference_item_dump)
                        else:
                            update_reference_item = None
                        
                        # reference_itemが変更されている場合エラー判定
                        if not current_reference_item == update_reference_item:
                            raise Exception("499-00706", [item_name, "reference_item"])  # 「編集」の際は既存項目の対象の設定を変更できません。(項目: {}, 対象: {})
                    
                    # カラムクラス「パスワード」の場合のバリデーションチェック
                    if column_class == "PasswordColumn":
                        # 最大バイト数が既存の値よりも下回っている場合エラー判定
                        current_password_maximum_bytes = int(target_record.get('PASSWORD_MAX_LENGTH'))
                        update_password_maximum_bytes = int(column_data.get('password_maximum_bytes'))
                        if current_password_maximum_bytes > update_password_maximum_bytes:
                            raise Exception("499-00707", [item_name, "password_maximum_bytes"])  # 「編集」の際は既存項目の対象の値が下回る変更はできません。(項目: {}, 対象: {})
                    
                    # カラムクラス「ファイルアップロード」の場合のバリデーションチェック
                    if column_class == "FileUploadColumn":
                        # 最大バイト数が既存の値よりも下回っている場合エラー判定
                        current_file_upload_maximum_bytes = int(target_record.get('FILE_UPLOAD_MAX_SIZE'))
                        update_file_upload_maximum_bytes = int(column_data.get('file_upload_maximum_bytes'))
                        if current_file_upload_maximum_bytes > update_file_upload_maximum_bytes:
                            raise Exception("499-00707", [item_name, "file_upload_maximum_bytes"])  # 「編集」の際は既存項目の対象の値が下回る変更はできません。(項目: {}, 対象: {})
                    
                    # カラムクラス「リンク」の場合のバリデーションチェック
                    if column_class == "HostInsideLinkTextColumn":
                        # 最大バイト数が既存の値よりも下回っている場合エラー判定
                        current_link_maximum_bytes = int(target_record.get('LINK_MAX_LENGTH'))
                        update_link_maximum_bytes = int(column_data.get('link_maximum_bytes'))
                        if current_link_maximum_bytes > update_link_maximum_bytes:
                            raise Exception("499-00707", [item_name, "link_maximum_bytes"])  # 「編集」の際は既存項目の対象の値が下回る変更はできません。(項目: {}, 対象: {})
                
                # 更新用パラメータを作成
                parameter = {
                    "item_name_ja": item_name,  # 項目名(ja)
                    "item_name_en": item_name,  # 項目名(en)
                    "item_name_rest": column_data.get('item_name_rest'),  # 項目名(rest)
                    "description_ja": column_data.get('description'),  # 説明(ja)
                    "description_en": column_data.get('description'),  # 説明(en)
                    "column_class": column_class,  # カラムクラス
                    "display_order": column_data.get('display_order'),  # 表示順序
                    "required": column_data.get('required'),  # 必須
                    "uniqued": column_data.get('uniqued'),  # 一意制約
                    "remarks": column_data.get('remarks'),  # 備考
                    "last_update_date_time": last_update_date_time  # 最終更新日時
                }
                
                # カラムグループがある場合
                column_group = column_data.get('column_group')
                if column_group:
                    parameter["column_group"] = column_group  # カラムグループ(「カラムグループ作成情報」のフルカラムグループ名)
                
                # 各カラムクラスに対応するparameterにNoneを挿入
                parameter["single_string_maximum_bytes"] = None  # 文字列(単一行) 最大バイト数
                parameter["single_string_regular_expression"] = None  # 文字列(単一行) 正規表現
                parameter["single_string_default_value"] = None  # 文字列(単一行) 初期値
                parameter["multi_string_maximum_bytes"] = None  # 文字列(複数行) 最大バイト数
                parameter["multi_string_regular_expression"] = None  # 文字列(複数行) 正規表現
                parameter["multi_string_default_value"] = None  # 文字列(複数行) 初期値
                parameter["integer_maximum_value"] = None  # 整数 最大値
                parameter["integer_minimum_value"] = None  # 整数 最小値
                parameter["integer_default_value"] = None  # 整数 初期値
                parameter["decimal_maximum_value"] = None  # 小数 最大値
                parameter["decimal_minimum_value"] = None  # 小数 最小値
                parameter["decimal_digit"] = None  # 小数 桁数
                parameter["decimal_default_value"] = None  # 小数 初期値
                parameter["detetime_default_value"] = None  # 日時 初期値
                parameter["dete_default_value"] = None  # 日付 初期値
                parameter["pulldown_selection"] = None  # プルダウン選択 メニューグループ:メニュー:項目
                parameter["pulldown_selection_default_value"] = None  # プルダウン選択 初期値
                parameter["reference_item"] = None  # プルダウン選択 参照項目
                parameter["password_maximum_bytes"] = None  # パスワード 最大バイト数
                parameter["file_upload_maximum_bytes"] = None  # ファイルアップロード 最大バイト数
                parameter["link_maximum_bytes"] = None  # リンク 最大バイト数
                parameter["link_default_value"] = None  # リンク 初期値
                
                # カラムクラス「文字列(単一行)」用のパラメータを追加
                if column_class == "SingleTextColumn":
                    parameter["single_string_maximum_bytes"] = column_data.get('single_string_maximum_bytes')  # 文字列(単一行) 最大バイト数
                    parameter["single_string_regular_expression"] = column_data.get('single_string_regular_expression')  # 文字列(単一行) 正規表現
                    parameter["single_string_default_value"] = column_data.get('single_string_default_value')  # 文字列(単一行) 初期値
                
                # カラムクラス「文字列(複数行)」用のパラメータを追加
                if column_class == "MultiTextColumn":
                    parameter["multi_string_maximum_bytes"] = column_data.get('multi_string_maximum_bytes')  # 文字列(複数行) 最大バイト数
                    parameter["multi_string_regular_expression"] = column_data.get('multi_string_regular_expression')  # 文字列(複数行) 正規表現
                    parameter["multi_string_default_value"] = column_data.get('multi_string_default_value')  # 文字列(複数行) 初期値
                
                # カラムクラス「整数」用のパラメータを追加
                if column_class == "NumColumn":
                    integer_maximum_value = None if not column_data.get('integer_maximum_value') else column_data.get('integer_maximum_value')
                    integer_minimum_value = None if not column_data.get('integer_minimum_value') else column_data.get('integer_minimum_value')
                    integer_default_value = None if not column_data.get('integer_default_value') else column_data.get('integer_default_value')
                    parameter["integer_maximum_value"] = integer_maximum_value  # 整数 最大値
                    parameter["integer_minimum_value"] = integer_minimum_value  # 整数 最小値
                    parameter["integer_default_value"] = integer_default_value  # 整数 初期値
                
                # カラムクラス「小数」用のパラメータを追加
                if column_class == "FloatColumn":
                    decimal_maximum_value = None if not column_data.get('decimal_maximum_value') else column_data.get('decimal_maximum_value')
                    decimal_minimum_value = None if not column_data.get('decimal_minimum_value') else column_data.get('decimal_minimum_value')
                    decimal_digit = None if not column_data.get('decimal_digit') else column_data.get('decimal_digit')
                    decimal_default_value = None if not column_data.get('decimal_default_value') else column_data.get('decimal_default_value')
                    parameter["decimal_maximum_value"] = decimal_maximum_value  # 小数 最大値
                    parameter["decimal_minimum_value"] = decimal_minimum_value  # 小数 最小値
                    parameter["decimal_digit"] = decimal_digit  # 小数 桁数
                    parameter["decimal_default_value"] = decimal_default_value  # 小数 初期値
                
                # カラムクラス「日時」用のパラメータを追加
                if column_class == "DateTimeColumn":
                    parameter["detetime_default_value"] = None if not column_data.get('detetime_default_value') else column_data.get('detetime_default_value')  # 日時 初期値 # noqa: E501
                
                # カラムクラス「日付」用のパラメータを追加
                if column_class == "DateColumn":
                    parameter["dete_default_value"] = None if not column_data.get('dete_default_value') else column_data.get('dete_default_value')  # 日付 初期値 # noqa: E501
                
                # カラムクラス「プルダウン選択」用のパラメータを追加
                if column_class == "IDColumn":
                    parameter["pulldown_selection"] = column_data.get('pulldown_selection')  # プルダウン選択 メニューグループ:メニュー:項目
                    parameter["pulldown_selection_default_value"] = column_data.get('pulldown_selection_default_value')  # プルダウン選択 初期値
                    reference_item = column_data.get('reference_item')
                    if reference_item:
                        reference_item_dump = json.dumps(reference_item)
                        parameter["reference_item"] = str(reference_item_dump)  # プルダウン選択 参照項目
                    else:
                        parameter["reference_item"] = None
                
                # カラムクラス「パスワード」用のパラメータを追加
                if column_class == "PasswordColumn":
                    parameter["password_maximum_bytes"] = column_data.get('password_maximum_bytes')  # パスワード 最大バイト数
                
                # カラムクラス「ファイルアップロード」用のパラメータを追加
                if column_class == "FileUploadColumn":
                    parameter["file_upload_maximum_bytes"] = column_data.get('file_upload_maximum_bytes')  # ファイルアップロード 最大バイト数
                
                # カラムクラス「リンク」用のパラメータを追加
                if column_class == "HostInsideLinkTextColumn":
                    parameter["link_maximum_bytes"] = column_data.get('link_maximum_bytes')  # リンク 最大バイト数
                    parameter["link_default_value"] = column_data.get('link_default_value')  # リンク 初期値
                
                # カラムクラス「パラメータシート参照」用のパラメータを追加 (未実装)
                # if column_class == "LinkIDColumn":
                #     parameter["parameter_sheet_reference"] = column_data.get('parameter_sheet_reference')  # パラメータシート参照
                
                parameters = {
                    "parameter": parameter,
                    "type": "Update"
                }
                
                # 更新を実行
                exec_result = objmenu.exec_maintenance(parameters, create_column_id)  # noqa: F405
                if not exec_result[0]:
                    result_msg = _format_loadtable_msg(exec_result[2])
                    result_msg = json.dumps(result_msg, ensure_ascii=False)
                    raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー
                
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args
    
    return True, None, None


def _disuse_t_menu_column(objdbca, current_t_menu_column_list, column_data_list):
    """
        【内部呼び出し用】「メニュー項目作成情報」の不要なレコードを調査し廃止する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            current_t_menu_column_list: 「メニュー項目作成情報」の現在登録されているレコード（対象メニューのMENU_CREATE_IDと紐づいているもの）
            column_data_list: 登録対象のカラム情報一覧
        RETRUN:
            boolean, result_code, msg_args
    """
    try:
        # 現在登録されているレコードのIDをlist化
        current_target_create_column_id_list = []
        current_target_id_timestamp = {}
        for record in current_t_menu_column_list:
            # IDをlistに格納
            create_column_id = record.get('CREATE_COLUMN_ID')
            current_target_create_column_id_list.append(create_column_id)
            
            # IDと最終更新日時を紐づけたdictを作成
            last_update_timestamp = record.get('LAST_UPDATE_TIMESTAMP')
            last_update_date_time = last_update_timestamp.strftime('%Y/%m/%d %H:%M:%S.%f')
            current_target_id_timestamp[create_column_id] = last_update_date_time
        
        # 更新対象のIDをlist化
        update_target_create_column_id_list = []
        for target_data in column_data_list.values():
            update_target_create_column_id_list.append(target_data.get('create_column_id'))
        
        # 差分を取得
        disuse_target_id_list = set(current_target_create_column_id_list) - set(update_target_create_column_id_list)
        if disuse_target_id_list:
            # loadTableの呼び出し
            objmenu = load_table.loadTable(objdbca, 'menu_item_creation_info')  # noqa: F405
            
            # # 差分の対象のレコードを廃止
            for disuse_target_id in disuse_target_id_list:
                # 廃止用パラメータを作成
                last_update_date_time = current_target_id_timestamp.get(disuse_target_id)
                parameters = {
                    "parameter": {
                        "last_update_date_time": last_update_date_time
                    },
                    "type": "Discard"
                }
                
                # 廃止を実行
                exec_result = objmenu.exec_maintenance(parameters, disuse_target_id)  # noqa: F405
                if not exec_result[0]:
                    result_msg = _format_loadtable_msg(exec_result[2])
                    result_msg = json.dumps(result_msg, ensure_ascii=False)
                    raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー
    
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args
    
    return True, None, None


def _insert_t_menu_unique_constraint(objdbca, menu_data):
    """
        【内部呼び出し用】「一意制約(複数項目)作成情報」にレコードを登録する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu_data: 登録対象のメニュー情報
        RETRUN:
            boolean, result_code, msg_args
    """
    try:
        # menu_dataから登録用のメニュー名を取得
        menu_name = menu_data.get('menu_name')
        
        # 一意制約(複数項目)用データがある場合、「一意制約(複数項目)作成情報」にレコードを登録
        unique_constraint = menu_data.get('unique_constraint')
        if unique_constraint:
            unique_constraint_dump = json.dumps(unique_constraint)
            # loadTableの呼び出し
            objmenu = load_table.loadTable(objdbca, 'unique_constraint_creation_info')  # noqa: F405
            parameters = {
                "parameter": {
                    "menu_name": menu_name,
                    "unique_constraint_item": str(unique_constraint_dump)
                },
                "type": "Register"
            }
            
            # 登録を実行
            exec_result = objmenu.exec_maintenance(parameters)  # noqa: F405
            if not exec_result[0]:
                result_msg = _format_loadtable_msg(exec_result[2])
                result_msg = json.dumps(result_msg, ensure_ascii=False)
                raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー
            
        else:
            # データが無い場合、登録せずreturn
            return True, None, None
            
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args
    
    return True, None, None


def _update_t_menu_unique_constraint(objdbca, menu_data, target_record):
    """
        【内部呼び出し用】「一意制約(複数項目)作成情報」のレコードを更新する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu_data: 登録対象のメニュー情報
            target_record: 「一意制約(複数項目)作成情報」の更新対象のレコード情報
        RETRUN:
            boolean, result_code, msg_args
    """
    try:
        # menu_dataから登録用のメニュー名を取得
        menu_name = menu_data.get('menu_name')
        
        # 更新対象レコードからuuidと最終更新日時を取得
        unique_constraint_id = target_record.get('UNIQUE_CONSTRAINT_ID')
        last_update_timestamp = target_record.get('LAST_UPDATE_TIMESTAMP')
        last_update_date_time = last_update_timestamp.strftime('%Y/%m/%d %H:%M:%S.%f')
        
        unique_constraint = menu_data.get('unique_constraint')
        unique_constraint_dump = json.dumps(unique_constraint)
        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'unique_constraint_creation_info')  # noqa: F405
        parameters = {
            "parameter": {
                "menu_name": menu_name,
                "unique_constraint_item": str(unique_constraint_dump),
                "last_update_date_time": last_update_date_time
            },
            "type": "Update"
        }
        
        # 更新を実行
        exec_result = objmenu.exec_maintenance(parameters, unique_constraint_id)  # noqa: F405
        if not exec_result[0]:
            result_msg = _format_loadtable_msg(exec_result[2])
            result_msg = json.dumps(result_msg, ensure_ascii=False)
            raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー
        
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args
    
    return True, None, None


def _disuse_t_menu_unique_constraint(objdbca, target_record):
    """
        【内部呼び出し用】「一意制約(複数項目)作成情報」のレコードを廃止する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu_data: 登録対象のメニュー情報
            target_record: 「一意制約(複数項目)作成情報」の更新対象のレコード情報
        RETRUN:
            boolean, result_code, msg_args
    """
    try:
        # 廃止対象レコードからuuidと最終更新日時を取得
        unique_constraint_id = target_record.get('UNIQUE_CONSTRAINT_ID')
        last_update_timestamp = target_record.get('LAST_UPDATE_TIMESTAMP')
        last_update_date_time = last_update_timestamp.strftime('%Y/%m/%d %H:%M:%S.%f')
        
        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'unique_constraint_creation_info')  # noqa: F405
        parameters = {
            "parameter": {
                "last_update_date_time": last_update_date_time
            },
            "type": "Discard"
        }
        
        # 廃止を実行
        exec_result = objmenu.exec_maintenance(parameters, unique_constraint_id)  # noqa: F405
        if not exec_result[0]:
            result_msg = _format_loadtable_msg(exec_result[2])
            result_msg = json.dumps(result_msg, ensure_ascii=False)
            raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー
        
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args
    
    return True, None, None


def _insert_t_menu_role(objdbca, menu_name, role_list):
    """
        【内部呼び出し用】「メニュー-ロール作成情報」にレコードを登録する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu_name: 対象のメニュー名
            role_list: 対象のロール一覧(list)
        RETRUN:
            boolean, result_code, msg_args
    """
    try:
        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'menu_role_creation_info')  # noqa: F405
        for role_name in role_list:
            parameters = {
                "parameter": {
                    "menu_name": menu_name,
                    "role_name": role_name
                },
                "type": "Register"
            }
            
            # 登録を実行
            exec_result = objmenu.exec_maintenance(parameters)  # noqa: F405
            if not exec_result[0]:
                result_msg = _format_loadtable_msg(exec_result[2])
                result_msg = json.dumps(result_msg, ensure_ascii=False)
                raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー
            
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args
    
    return True, None, None


def _disuse_t_menu_role(objdbca, role_list, current_role_dict):
    """
        【内部呼び出し用】「メニュー-ロール作成情報」のレコードを廃止する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu_name: 対象のメニュー名
            role_list: 廃止対象のロール一覧(list)
            current_role_dict: 廃止対象を指定するためのdict
        RETRUN:
            boolean, result_code, msg_args
    """
    try:
        # loadTableの呼び出し
        objmenu = load_table.loadTable(objdbca, 'menu_role_creation_info')  # noqa: F405
        for role_name in role_list:
            role_data = current_role_dict.get(role_name)
            menu_role_id = role_data.get('menu_role_id')
            last_update_date_time = role_data.get('last_update_date_time')
            parameters = {
                "parameter": {
                    "last_update_date_time": last_update_date_time
                },
                "type": "Discard"
            }
            
            # 廃止を実行
            exec_result = objmenu.exec_maintenance(parameters, menu_role_id)  # noqa: F405
            if not exec_result[0]:
                result_msg = _format_loadtable_msg(exec_result[2])
                result_msg = json.dumps(result_msg, ensure_ascii=False)
                raise Exception("499-00701", [result_msg])  # loadTableバリデーションエラー
            
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args
    
    return True, None, None


def _insert_t_menu_create_history(objdbca, menu_create_id, status_id, create_type, user_id):
    """
        【内部呼び出し用】「メニュー作成履歴」にレコードを登録
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu_create_id: 「メニュー定義一覧」の対象レコードのUUID
            status_id: 「メニュー作成履歴」のステータスID
            create_type: 「メニュー作成履歴」の作成タイプ
            user_id: ユーザID
        RETRUN:
            boolean, result_code, msg_args, history_id
    """
    # テーブル名
    t_menu_create_history = 'T_MENU_CREATE_HISTORY'
    
    try:
        data_list = {
            "MENU_CREATE_ID": menu_create_id,
            "STATUS_ID": status_id,
            "CREATE_TYPE": create_type,
            "DISUSE_FLAG": "0",
            "LAST_UPDATE_USER": user_id
        }
        primary_key_name = 'HISTORY_ID'
        ret = objdbca.table_insert(t_menu_create_history, data_list, primary_key_name)
        history_id = ret[0].get('HISTORY_ID')
        
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args, None
    
    return True, None, None, history_id


def _check_before_registar_validate(objdbca, menu_data, column_data_list):
    """
        【内部呼び出し用】レコード登録前バリデーションチェックの実施
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu_data: 登録対象のメニュー情報
            column_data_list: 登録対象のカラム情報一覧
        RETRUN:
            boolean, result_code, msg_arg
    """
    # テーブル/ビュー名
    v_menu_sheet_type = 'V_MENU_SHEET_TYPE'
    
    # 変数定義
    lang = g.get('LANGUAGE')
    sheet_id = None
    
    try:
        # シートタイプのIDを取得
        sheet_type_name = menu_data.get('sheet_type')
        
        # シートタイプ一覧情報を取得
        ret = objdbca.table_select(v_menu_sheet_type, 'WHERE DISUSE_FLAG = %s', [0])
        for record in ret:
            check_sheet_type_name = record.get('SHEET_TYPE_NAME_' + lang.upper())
            if sheet_type_name == check_sheet_type_name:
                sheet_id = str(record.get('SHEET_TYPE_NAME_ID'))
        
        # シートタイプが「2: データシート」かつ、登録する項目が無い場合エラー判定
        if sheet_id == "2" and not column_data_list:
            raise Exception("499-00711", [])  # シートタイプが「データシート」の場合、項目数が0件のメニューを作成できません。
        
        # ロールを取得
        role_list = menu_data.get('role_list')
        if not role_list:
            raise Exception("499-00703", ["role_list"])  # 対象keyの値が不正です。(key: {})
        
    except Exception as e:
        result_code = e.args[0]
        msg_args = e.args[1]
        return False, result_code, msg_args
    
    return True, None, None


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


def _get_user_list(objdbca):
    """
        【内部呼び出し用】ユーザ一覧を取得する
        ARGS:
        RETRUN:
            users_list
    """
    users_list = {}
    lang = g.get('LANGUAGE')
    usr_name_col = "USER_NAME_{}".format(lang.upper())
    table_name = "T_COMN_BACKYARD_USER"
    return_values = objdbca.table_select(table_name, 'WHERE DISUSE_FLAG = %s', [0])

    for bk_user in return_values:
        users_list[bk_user['USER_ID']] = bk_user[usr_name_col]

    user_id = g.get('USER_ID')
    if user_id not in users_list:
        pf_users = util.get_exastro_platform_users()  # noqa: F405

        users_list.update(pf_users)
    
    return users_list


def add_tmp_column_group(column_group_list, col_group_record_count, column_group_id, col_num, tmp_column_group, column_group_parent_of_child):
    """
        カラムグループ管理用配列にカラムグループの親子関係の情報を格納する
        ARGS:
            column_group_list: カラムグループのレコード一覧
            col_group_record_count: カラムグループのレコード数
            column_group_id: 対象のカラムグループID
            col_num: カラムの並び順をc1, c2, c3...という名称に変換した値
            tmp_colmn_group: カラムグループ管理用配列
            column_group_parent_of_child: カラムグループの親子関係があるとき、子の一番大きい親を結びつけるための配列
        RETRUN:
            tmp_colmn_group, column_group_parent_of_child
    """
    if column_group_id not in tmp_column_group:
        tmp_column_group[column_group_id] = []
    
    tmp_column_group[column_group_id].append(col_num)
    
    # カラムグループの親をたどり格納
    end_flag = False
    target_column_group_id = column_group_id
    first_column_group_id = column_group_id
    loop_count = 0
    max_loop = int(col_group_record_count) ** 2  # 「カラムグループ作成情報」のレコード数の二乗がループ回数の上限
    while not end_flag:
        for target in column_group_list.values():
            if target.get('column_group_id') == target_column_group_id:
                parent_column_group_id = target.get('parent_column_group_id')
                if not parent_column_group_id:
                    end_flag = True
                    break
                
                if parent_column_group_id not in tmp_column_group:
                    tmp_column_group[parent_column_group_id] = []
                
                if target_column_group_id not in tmp_column_group[parent_column_group_id]:
                    tmp_column_group[parent_column_group_id].append(target_column_group_id)
                
                target_column_group_id = parent_column_group_id
                column_group_parent_of_child[first_column_group_id] = parent_column_group_id
        
        # ループ数がmax_loopを超えたら無限ループの可能性が高いため強制終了
        loop_count += 1
        if loop_count > max_loop:
            end_flag = True
    
    return tmp_column_group, column_group_parent_of_child


def collect_column_group_sort_order(column_group_list, tmp_column_group, column_group_info_data):
    """
        カラムグループ管理用配列(tmp_column_group)を元に、カラムグループIDをg1,g2,g3...に変換し、idやnameを格納した配列を返す
        ARGS:
            column_group_list: カラムグループのレコード一覧
            tmp_colmn_group: カラムグループ管理用配列
            column_group_info_data: カラムグループ情報格納用配列
        RETRUN:
            column_group_info_data, key_to_id
    """
    # カラムグループIDと対応のg番号配列を作成
    key_to_id = {}
    group_num = 1
    for group_id in tmp_column_group.keys():
        key_to_id[group_id] = 'g' + str(group_num)
        group_num += 1
    
    # カラムグループ管理用配列について、カラムグループIDをg1,g2,g3...に変換し、idやnameを格納する。
    for group_id, value_list in tmp_column_group.items():
        add_data = {}
        columns = []
        for col in value_list:
            if col in key_to_id:
                columns.append(key_to_id[col])
            else:
                columns.append(col)
        
        add_data['columns'] = columns
        add_data['column_group_id'] = group_id
        add_data['column_group_name'] = None
        add_data['parent_column_group_id'] = None
        add_data['parent_column_group_name'] = None
        target_data = column_group_list.get(group_id)
        if target_data:
            add_data['column_group_name'] = target_data.get('column_group_name')
            parent_id = target_data.get('parent_column_group_id')
            if parent_id:
                add_data['parent_column_group_id'] = parent_id
                add_data['parent_column_group_name'] = column_group_list.get(parent_id).get('column_group_name')
        
        column_group_info_data[key_to_id[group_id]] = add_data
    
    return column_group_info_data, key_to_id


def collect_parent_sord_order(column_info_data, column_group_parent_of_child, key_to_id):
    """
        大元のカラムの並び順を作成
        ARGS:
            column_info_data: 対象のカラム情報
            column_group_parent_of_child: カラムグループの親子関係があるとき、子の一番大きい親を結びつけるための配列
            key_to_id: カラムグループIDと対応のg番号配列
        RETRUN:
            columns
    """
    columns = []
    for col_num, col_data in column_info_data.items():
        column_group_id = col_data['column_group_id']
        if not column_group_id:
            # カラムグループが無い場合はcol_num(c1, c2, c3...)を格納
            columns.append(col_num)
            continue
        
        if column_group_id in column_group_parent_of_child:
            # 大親のカラムグループIDをg番号(g1, g2, g3...)に変換した値を格納
            parent_column_group_id = column_group_parent_of_child.get(column_group_id)
            if key_to_id[parent_column_group_id] not in columns:
                columns.append(key_to_id[parent_column_group_id])
            continue
        else:
            # カラムグループIDをg番号(g1, g2, g3...)に変換した値を格納
            if key_to_id[column_group_id] not in columns:
                columns.append(key_to_id[column_group_id])
            continue

    return columns
