# Copyright 2025 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import g
import json
from common_libs.oase.const import oaseConst

# メニュー「OASE - フィルター」設定のバリデーション

def external_valid_menu_before(objdbca, objtable, option):
    """メニューフィルターバリデーション / Menu Filter Validation

    Args:
        objdbca (obj): DB接続クラスインスタンス / DB connection class instance
        objtable (obj): メニュー情報、カラム紐付、関連情報 / Menu information, column linkage, related information
        option (json): パラメータ、その他設定値 / Parameters, other settings

    Returns:
        retBool: True: Normal / False: Abnormal
        msg: エラーメッセージ / Error message
        option: 受け取ったもの / Received items
    """

    retBool = True
    msg = []
    cmd_type = option.get('cmd_type')

    if cmd_type == 'Register' or cmd_type == 'Update':
        # 「登録」「更新」の場合、entry_parameterから各値を取得
        # In the case of "Register" or "Update", retrieve each value from entry_parameter.
        parameter = option.get('entry_parameter', {}).get('parameter')
    elif cmd_type == 'Restore':
        # 「復活」の場合、currrent_parameterから各値を取得
        # In the case of "Restore", retrieve each value from current_parameter.
        parameter = option.get('current_parameter', {}).get('parameter')
    else:
        # 「登録」「修正」「復活」以外（「廃止」「削除」の場合）は、バリデーションチェックを行わない。
        # For cases other than "Register", "Update", or "Restore" (such as "Discard" or "Delete"), validation checks are not performed.
        return retBool, msg, option

    # フィルターID / Filter ID
    filter_id = parameter.get('filter_id')

    # フィルター条件 / Filter condition
    filter_condition_json_str = parameter.get('filter_condition_json')
    try:
        filter_condition_json = json.loads(filter_condition_json_str) if filter_condition_json_str is not None else [] # 実際には必須項目なのでNoneは来ない想定
    except:
        retBool = False
        msg = g.appmsg.get_api_message("MSG-20261")
        return retBool, msg, option,

    # フィルター条件は必須とする
    # The filter condition is required
    if not filter_condition_json_str or len(filter_condition_json_str) == 0:
        retBool = False
        msg = g.appmsg.get_api_message("MSG-180001")
        return retBool, msg, option,
    for filter_condition in filter_condition_json:
        if "condition_type" not in filter_condition or "condition_value" not in filter_condition or filter_condition["condition_value"] == "":
            retBool = False
            msg = g.appmsg.get_api_message("MSG-180001")
            return retBool, msg, option,

    # 検索条件 / Search condition
    try:
        search_condition_id = parameter.get("search_condition_id")
    except Exception:
        search_condition_id = ""

    # グルーピング条件ラベル / Group label
    group_label_key_ids = parameter.get('group_label_key_ids')
    # グルーピング条件 / Group condition
    group_condition_id = parameter.get('group_condition_id')

    # 検索方式が「1:ユニーク」「2:キューイング」の場合
    # If the search method is "1: Unique" or "2: Queuing"
    if search_condition_id in [oaseConst.DF_SEARCH_CONDITION_UNIQUE, oaseConst.DF_SEARCH_CONDITION_QUEUING]:
        # グルーピング条件ラベル、条件は入力不可とする
        # Group labels and conditions cannot be entered
        if group_label_key_ids or group_condition_id or (group_label_key_ids and len(group_label_key_ids) > 0):
            retBool = False
            msg = g.appmsg.get_api_message("MSG-180002")
            return retBool, msg, option,

        # 同一フィルターのチェック
        # Check for identical filters
        if db_filter_unique_check(objdbca, filter_id, filter_condition_json_str):
            retBool = False
            msg = g.appmsg.get_api_message("MSG-180003")
            return retBool, msg, option,

        # 条件値に*（ワイルドカード）が含まれている場合はエラーとする
        if '"condition_value": "*"' in filter_condition_json_str:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-180006")
            return retBool, msg, option,
    elif search_condition_id in [oaseConst.DF_SEARCH_CONDITION_GROUPING, oaseConst.DF_SEARCH_CONDITION_GROUPING_NO_PERIOD_EXTENSION]:
        # 検索方式が「3:グルーピング」の場合
        # If the search method is 3 or 4: Grouping (Period Extension) or Grouping (No Period Extension)

        # グルーピング条件ラベル、条件は必須とする
        # Group labels and conditions are required
        if not (group_label_key_ids and group_condition_id):
            retBool = False
            msg = g.appmsg.get_api_message("MSG-180004")
            return retBool, msg, option,

        # 同一フィルター、グルーピング対象のチェック
        # Check for identical filters and group targets
        if db_filter_group_unique_check(objdbca, filter_id, filter_condition_json_str, group_label_key_ids, group_condition_id):
            retBool = False
            msg = g.appmsg.get_api_message("MSG-180005")
            return retBool, msg, option,

        # 条件値に*（ワイルドカード）が含まれている場合は、演算子に!=は許可しない
        is_allowed_wildcard = True
        for filter_condition in filter_condition_json:
            if filter_condition["condition_type"] == "2" and filter_condition["condition_value"] == "*":
                is_allowed_wildcard = False
        if is_allowed_wildcard is False:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-180007")
            return retBool, msg, option,
    else:
        # 検索方式が未選択、または「その他」の場合は、ここ以外でエラーとなるためここは、処理しない
        # If the search method is unselected or "Other", it will result in an error elsewhere, so do not process here.
        return retBool, msg, option,

    # エラーなし / No errors
    return retBool, msg, option


def db_filter_unique_check(objdbca, filter_id, target_value):
    """ 同一フィルター条件のチェック / Check for identical filter conditions

    Args:
        objdbca (obj): db connection
        filter_id (str): filter id (update only)
        target_value (str): filter condition json

    Returns:
        boolean: true: exists / false: not exists
    """

    bind_value_list = []
    where_str = ''

    # フォルター条件の同一有無チェック
    # Check for identical filter conditions
    where_str = ' where `FILTER_CONDITION_JSON` = %s'
    bind_value_list.append(target_value)

    # 更新時自身のIDを除外
    # Exclude own ID when updating
    if filter_id is not None:
        if len(filter_id) != 0:
            where_str = where_str + ' and `FILTER_ID` <> %s'
            bind_value_list.append(filter_id)

    # 検索方法「グルーピング」を対象外
    # Exclude search method "Grouping"
    grouping_values = [
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        oaseConst.DF_SEARCH_CONDITION_GROUPING_NO_PERIOD_EXTENSION
    ]
    placeholders = ', '.join(['%s'] * len(grouping_values))
    where_str = where_str + f" and `SEARCH_CONDITION_ID` NOT IN ({placeholders})"
    bind_value_list.extend(grouping_values)

    # 廃止を対象外
    # Exclude abolition
    where_str = where_str + " and `{}` = 0 ".format("DISUSE_FLAG")

    # 該当レコードの存在チェック
    # Check for the existence of the relevant record
    result = objdbca.table_exists(oaseConst.T_OASE_FILTER, where_str, bind_value_list)

    return result


def db_filter_group_unique_check(objdbca, filter_id, target_value, group_label_key_ids, group_condition_id):
    """ 同一フィルター条件のチェック / Check for identical filter conditions

    Args:
        objdbca (obj): db connection
        filter_id (str): filter id (update only)
        target_value (str): filter condition json
        group_label_key_ids (str): group label key ids
        group_condition_id (str): group condition id

    Returns:
        boolean: true: exists / false: not exists
    """

    bind_value_list = []
    where_str = ''

    # ・グルーピング条件の同一有無チェック
    # Check for identical filter conditions and group conditions
    where_str = ' where `GROUP_LABEL_KEY_IDS` = %s' + \
                ' and `GROUP_CONDITION_ID` = %s'
    bind_value_list.append(group_label_key_ids)
    bind_value_list.append(group_condition_id)

    # フォルター条件が設定されていたら除外
    # Exclude if filter condition is set
    where_str = where_str + ' and `FILTER_CONDITION_JSON` = %s'
    bind_value_list.append(target_value)

    # 更新時自身のIDを除外
    # Exclude own ID when updating
    if filter_id is not None:
        if len(filter_id) != 0:
            where_str = where_str + ' and `FILTER_ID` <> %s'
            bind_value_list.append(filter_id)

    # 検索方法「グルーピング」を対象
    # Target search method "Grouping"
    grouping_values = [
        oaseConst.DF_SEARCH_CONDITION_GROUPING,
        oaseConst.DF_SEARCH_CONDITION_GROUPING_NO_PERIOD_EXTENSION
    ]
    placeholders = ', '.join(['%s'] * len(grouping_values))
    where_str = where_str + f" and `SEARCH_CONDITION_ID` IN ({placeholders})"
    bind_value_list.extend(grouping_values)

    # 廃止を対象外
    # Exclude abolition
    where_str = where_str + " and `{}` = 0 ".format("DISUSE_FLAG")

    # 該当レコードの存在チェック
    # Check for the existence of the relevant record
    result = objdbca.table_exists(oaseConst.T_OASE_FILTER, where_str, bind_value_list)

    return result
