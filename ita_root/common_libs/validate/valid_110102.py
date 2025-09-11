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

    # 既存データ
    current_parameter = option.get("current_parameter", {}).get("parameter")
    # 入力データ
    entry_parameter = option.get("entry_parameter", {}).get("parameter")
    # 通知テンプレートID
    notification_template_id = current_parameter.get("notification_template_id", None)
    
    # 登録・更新時
    if cmd_type in ["Register", "Update"]:
        # 通知テンプレートIDが1～4の場合
        if notification_template_id in ["1", "2", "3", "4"]:
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

            # 入力した通知先がイベント種別内でユニークでない場合
            data_cnt = get_notification_destination(objdbca,
                                                    notification_template_id,
                                                    entry_parameter.get("event_type"),
                                                    entry_parameter.get("notification_destination"))
            if (data_cnt >= 1):
                retBool = False
                msg.append(g.appmsg.get_api_message("MSG-170004"))
                return retBool, msg, option,

    # 削除時
    elif cmd_type == "Delete":
        # 通知テンプレートIDが1～4の場合
        if notification_template_id in ["1", "2", "3", "4"]:
            retBool = False
            msg.append(g.appmsg.get_api_message("MSG-170005"))
            return retBool, msg, option,

    # 廃止時
    elif cmd_type == "Discard":
        # 通知テンプレートIDが1～4の場合
        if notification_template_id in ["1", "2", "3", "4"]:
            retBool = False
            msg.append(g.appmsg.get_api_message("MSG-170006"))
            return retBool, msg, option,

    # 復活時
    elif cmd_type == "Restore":
        # 通知テンプレートIDが1～4の場合
        if notification_template_id in ["1", "2", "3", "4"]:
            retBool = False
            msg.append(g.appmsg.get_api_message("MSG-170007"))
            return retBool, msg, option,

        # 通知テンプレートIDが1～4以外の場合
        else:
            # カレントの通知先がイベント種別内でユニークでない場合
            data_cnt = get_notification_destination(objdbca,
                                                    notification_template_id,
                                                    current_parameter.get("event_type"),
                                                    current_parameter.get("notification_destination"))
            if (data_cnt >= 1):
                retBool = False
                msg.append(g.appmsg.get_api_message("MSG-170004"))
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


def get_notification_destination(objdbca, notification_template_id, event_type, notification_destination):
    """
    通知テンプレートID、イベント種別、通知先を条件に
    通知テンプレート(共通)に登録されているレコード件数を取得
    ARGS:
        objdbca :DB接続クラスインスタンス
        notification_template_id：通知テンプレートID
        event_type :イベント種別
        notification_destination :通知先
    RETRUN:
        return :レコード件数
    """

    # 通知テンプレート(共通)
    target_type_table = "T_OASE_NOTIFICATION_TEMPLATE_COMMON"
    record = []
    # 通知テンプレートIDが空の場合
    if notification_template_id is None:
        param = [[event_type], [notification_destination]]
        record = objdbca.table_select(
            target_type_table,
            "WHERE DISUSE_FLAG=0 AND EVENT_TYPE = %s AND NOTIFICATION_DESTINATION = %s",
            param
        )
    # 通知テンプレートIDが空でない場合
    else:
        param = [[notification_template_id], [event_type], [notification_destination]]
        record = objdbca.table_select(
            target_type_table,
            "WHERE DISUSE_FLAG=0 AND NOTIFICATION_TEMPLATE_ID <> %s AND EVENT_TYPE = %s AND NOTIFICATION_DESTINATION = %s",
            param
        )

    # レコード件数を取得
    return len(record)
