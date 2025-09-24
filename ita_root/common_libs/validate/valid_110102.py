# Copyright 2023 NEC Corporation#
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
#

import base64

from common_libs.notification import validator
from common_libs.notification import notification_base
from flask import g

def external_valid_menu_before(objdbca, objtable, option):
    """
    メニューバリデーション(更新)
    ARGS:
        objdbca :DB接続クラスインスタンス
        objtabl :メニュー情報、カラム紐付、関連情報
        option :パラメータ、その他設定値
    RETRUN:
        retBoo :True/ False
        msg :エラーメッセージ
        option :受け取ったもの
    """

    target_column_name = {
        "ja": objtable["COLINFO"]["template_file"]["COLUMN_NAME_JA"],
        "en": objtable["COLINFO"]["template_file"]["COLUMN_NAME_EN"],
    }

    target_lang = g.LANGUAGE if g.LANGUAGE is not None else "ja"

    retBool = True
    msg = []

    cmd_type = option.get("cmd_type")

    current_parameter = option.get("current_parameter", {}).get("parameter")
    entry_parameter = option.get("entry_parameter", {}).get("parameter")
    notification_template_id = str(current_parameter.get("notification_template_id", None))

    # 登録・更新時
    if cmd_type in ["Register", "Update"]:
        # 通知テンプレートIDが1～4の場合
        if is_id_in_default_range(notification_template_id):
            # イベント種別は変更不可
            if current_parameter.get("event_type") != entry_parameter.get("event_type"):
                retBool = False 
                msg.append(g.appmsg.get_api_message("MSG-170001"))
                return retBool, msg, option,

            # 通知先は変更不可（空のみ）
            if entry_parameter.get("notification_destination") is not None:
                retBool = False
                msg.append(g.appmsg.get_api_message("MSG-170002"))
                return retBool, msg, option,

        # 通知テンプレートIDが1～4以外の場合
        else:
            # 通知先が空の場合
            if entry_parameter.get("notification_destination") is None:
                retBool = False
                msg.append(g.appmsg.get_api_message("MSG-170003"))
                return retBool, msg, option,

            # 同一のイベント種別で、同一の通知先の場合
            event_type = entry_parameter.get("event_type")
            notification_destination = entry_parameter.get("notification_destination")
            duplicate_notification_destination = check_duplicate_notification_destination(objdbca,
                                                                                          notification_template_id,
                                                                                          event_type,
                                                                                          notification_destination)
            if duplicate_notification_destination != "":
                retBool = False
                if not notification_template_id or str(notification_template_id).lower() == "none":
                    notification_template_id = "-"
                msg.append(g.appmsg.get_api_message("MSG-170004", [notification_template_id, duplicate_notification_destination]))
                return retBool, msg, option,

    # 削除時
    elif cmd_type == "Delete":
        # 通知テンプレートIDが1～4の場合
        if is_id_in_default_range(notification_template_id):
            retBool = False
            msg.append(g.appmsg.get_api_message("MSG-170005"))
            return retBool, msg, option,

    # 廃止時
    elif cmd_type == "Discard":
        # 通知テンプレートIDが1～4の場合
        if is_id_in_default_range(notification_template_id):
            retBool = False
            msg.append(g.appmsg.get_api_message("MSG-170006"))
            return retBool, msg, option,

    # 復活時
    elif cmd_type == "Restore":
        # 通知テンプレートIDが1～4の場合
        if is_id_in_default_range(notification_template_id):
            retBool = False
            msg.append(g.appmsg.get_api_message("MSG-170007"))
            return retBool, msg, option,

        # 通知テンプレートIDが1～4以外の場合
        else:
            event_type = current_parameter.get("event_type")
            notification_destination = current_parameter.get("notification_destination")
            # 同一のイベント種別で、同一の通知先の場合
            duplicate_notification_destination = check_duplicate_notification_destination(objdbca,
                                                                                          notification_template_id,
                                                                                          event_type,
                                                                                          notification_destination)
            if duplicate_notification_destination != "":
                retBool = False
                msg.append(g.appmsg.get_api_message("MSG-170004", [notification_template_id, duplicate_notification_destination]))
                return retBool, msg, option,

    file_path = option.get('entry_parameter', {}).get('file_path', {}).get('template_file')
    if file_path is None:
        return retBool, msg, option,

    with open(file_path, 'rb') as f:  # バイナリファイルとしてファイルをオープン
        template_data_binary = f.read()

    # 文字コードをチェック バイナリファイルの場合、encode['encoding']はNone
    if validator.is_binary_file(template_data_binary):
        retBool = False
        msg_tmp = g.appmsg.get_api_message("499-01814", [target_column_name[target_lang]])
        msg.append(msg_tmp)

    template_data_decoded = template_data_binary.decode('utf-8', 'ignore')
    if retBool:
        # jinja2の形式として問題無いか確認する
        if not validator.is_jinja2_template(template_data_decoded):
            retBool = False
            msg_tmp = g.appmsg.get_api_message("499-01815", [target_column_name[target_lang]])
            msg.append(msg_tmp)

    if retBool:
        # 特有の構文チェック
        if not validator.contains_title(template_data_decoded):
            retBool = False
            msg_tmp = g.appmsg.get_api_message("499-01816", [target_column_name[target_lang]])
            msg.append(msg_tmp)

        if not validator.contains_body(template_data_decoded):
            retBool = False
            msg_tmp = g.appmsg.get_api_message("499-01817", [target_column_name[target_lang]])
            msg.append(msg_tmp)

    return retBool, msg, option,


def is_id_in_default_range(notification_template_id):
    """
    通知テンプレートIDが1～4の場合はTrueを返す
    それ以外はFalseを返す
    ARGS:
        notification_template_id：通知テンプレートID
    RETRUN:
        return : True/ False
    """
    if notification_template_id in ["1", "2", "3", "4"]:
        return True
    else:
        return False


def check_duplicate_notification_destination(objdbca, notification_template_id, event_type, notification_destination):
    """
    同一の通知先、その通知先を返す

    ARGS:
        objdbca :DB接続クラスインスタンス
        notification_template_id：通知テンプレートID
        event_type :イベント種別
        notification_destination :通知先ID文字列
    RETRUN:
        通知先名称 / 空文字
    """
    # 引数の通知先ID文字列が空の場合は空文字を返す
    if not notification_destination:
        return ""

    # 引数の通知先ID文字列より {"id": および ]} を取り除きリスト化
    notification_destination = notification_destination.replace('{"id": [', '').replace(']}', '').replace('"', '').strip()
    entry_notification_ids = [item.strip() for item in notification_destination.split(',') if item.strip()]

    # 通知テンプレート(共通)より登録データを取得
    data = get_notification_destination(objdbca, notification_template_id, event_type)

    find_id = ""
    # 取得した通知先ID文字列より {"id": および ]} を取り除きリスト化
    db_notification_ids = set()
    for record in data:
        db_notification = record.get('NOTIFICATION_DESTINATION')
        if db_notification:
            db_notification = db_notification.replace('{"id": [', '').replace(']}', '').replace('"', '').strip()
            db_notification_ids.update([item.strip() for item in db_notification.split(',') if item.strip()])

    # 一致を検索
    for entry_notification_id in entry_notification_ids:
        if entry_notification_id in db_notification_ids:
            find_id = entry_notification_id
            break

    # 一致がない場合は空文字を返す
    if not find_id:
        return ""

    # 通知先名称取得
    notification_dest_dict = notification_base.Notification.fetch_notification_destination_dict()
    notification_name = notification_dest_dict.get(find_id.strip(), "")
    return notification_name


def get_notification_destination(objdbca, notification_template_id, event_type):
    """
    通知テンプレート(共通)より通知先を取得

    ARGS:
        objdbca :DB接続クラスインスタンス
        notification_template_id：通知テンプレートID
        event_type :イベント種別
    RETRUN:
        取得レコード        
    """

    # 通知テンプレート(共通)
    target_type_table = "T_OASE_NOTIFICATION_TEMPLATE_COMMON"
    sql_where = ""
    # 通知テンプレートIDが空の場合
    if notification_template_id is None:
        param = [[event_type]]
        sql_where = "WHERE DISUSE_FLAG=0 AND EVENT_TYPE = %s"
    # 通知テンプレートIDが空でない場合は、自分以外のレコードを対象とする
    else:
        param = [[notification_template_id], [event_type]]
        sql_where = "WHERE DISUSE_FLAG=0 AND NOTIFICATION_TEMPLATE_ID <> %s AND EVENT_TYPE = %s"

    record = objdbca.table_select(
        target_type_table,
        sql_where,
        param
    )

    return record