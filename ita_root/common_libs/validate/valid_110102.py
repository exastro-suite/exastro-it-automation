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


from common_libs.notification import validator
from common_libs.notification import notification_base
from flask import g


def external_valid_menu_before(objdbca, objtable, option):
    """
    メニューバリデーション(更新)

    メニューの登録・更新・削除・廃止・復活時に、入力されたパラメータやファイルの内容を検証する。

    Args:
        objdbca (object): DB接続クラスインスタンス
        objtable (dict): メニュー情報、カラム紐付、関連情報
        option (dict): パラメータ、その他設定値
    Returns:
        retBool (bool): True/False
        msg (list): エラーメッセージ
        option (dict): 受け取ったもの
    """
    target_column_name = {
        "ja": objtable["COLINFO"]["template_file"]["COLUMN_NAME_JA"],
        "en": objtable["COLINFO"]["template_file"]["COLUMN_NAME_EN"],
    }
    target_lang = g.LANGUAGE if g.LANGUAGE is not None else "ja"

    cmd_type = option.get("cmd_type")
    current_parameter = option.get("current_parameter", {}).get("parameter")
    entry_parameter = option.get("entry_parameter", {}).get("parameter")
    notification_template_id = str(current_parameter.get("notification_template_id", None))

    retBool, msg = True, []

    # コマンドタイプごとの処理を分割
    if cmd_type in ["Register", "Update"]:
        retBool, msg = handle_register_update(
            objdbca, current_parameter, entry_parameter, notification_template_id
        )
    elif cmd_type == "Delete":
        retBool, msg = handle_delete(notification_template_id)
    elif cmd_type == "Discard":
        retBool, msg = handle_discard(notification_template_id)
    elif cmd_type == "Restore":
        retBool, msg = handle_restore(
            objdbca, current_parameter, notification_template_id
        )

    # ファイル検証
    if retBool:
        file_path = option.get("entry_parameter", {}).get("file_path", {}).get("template_file")
        if file_path:
            retBool, msg = validate_template_file(file_path, target_column_name, target_lang, msg)

    return retBool, msg, option


def handle_register_update(objdbca, current_parameter, entry_parameter, notification_template_id):
    """
    登録・更新時の処理

    通知テンプレートIDや通知先の内容を検証し、エラーがあればメッセージを返す。

    Args:
        objdbca (object): DB接続クラスインスタンス
        current_parameter (dict): 現在のパラメータ
        entry_parameter (dict): 入力されたパラメータ
        notification_template_id (str): 通知テンプレートID
    Returns:
        retBool (bool): True/False
        msg (list): エラーメッセージ
    """
    retBool, msg = True, []

    if is_id_in_default_range(notification_template_id):
        if current_parameter.get("event_type") != entry_parameter.get("event_type"):
            return False, [g.appmsg.get_api_message("MSG-170001")]
        if entry_parameter.get("notification_destination") is not None:
            return False, [g.appmsg.get_api_message("MSG-170002")]
    else:
        if entry_parameter.get("notification_destination") is None:
            return False, [g.appmsg.get_api_message("MSG-170003")]
        duplicate_notification_destination = check_duplicate_notification_destination(
            objdbca,
            notification_template_id,
            entry_parameter.get("event_type"),
            entry_parameter.get("notification_destination"),
        )
        if duplicate_notification_destination:
            msg_code = g.appmsg.get_api_message(
                "MSG-170004", [notification_template_id or "-", duplicate_notification_destination]
            )
            return False, [msg_code]

    return retBool, msg


def handle_delete(notification_template_id):
    """
    削除時の処理

    通知テンプレートIDが特定の範囲内の場合、削除を許可しない。

    Args:
        notification_template_id (str): 通知テンプレートID
    Returns:
        retBool (bool): True/False
        msg (list): エラーメッセージ
    """
    if is_id_in_default_range(notification_template_id):
        return False, [g.appmsg.get_api_message("MSG-170005")]
    return True, []


def handle_discard(notification_template_id):
    """
    廃止時の処理

    通知テンプレートIDが特定の範囲内の場合、廃止を許可しない。

    Args:
        notification_template_id (str): 通知テンプレートID
    Returns:
        retBool (bool): True/False
        msg (list): エラーメッセージ
    """
    if is_id_in_default_range(notification_template_id):
        return False, [g.appmsg.get_api_message("MSG-170006")]
    return True, []


def handle_restore(objdbca, current_parameter, notification_template_id):
    """
    復活時の処理

    通知テンプレートIDや通知先の内容を検証し、エラーがあればメッセージを返す。

    Args:
        objdbca (object): DB接続クラスインスタンス
        current_parameter (dict): 現在のパラメータ
        notification_template_id (str): 通知テンプレートID
    Returns:
        retBool (bool): True/False
        msg (list): エラーメッセージ
    """
    if is_id_in_default_range(notification_template_id):
        return False, [g.appmsg.get_api_message("MSG-170007")]

    duplicate_notification_destination = check_duplicate_notification_destination(
        objdbca,
        notification_template_id,
        current_parameter.get("event_type"),
        current_parameter.get("notification_destination"),
    )
    if duplicate_notification_destination:
        msg_code = g.appmsg.get_api_message(
            "MSG-170004", [notification_template_id, duplicate_notification_destination]
        )
        return False, [msg_code]

    return True, []


def validate_template_file(file_path, target_column_name, target_lang, msg):
    """
    テンプレートファイルの検証

    ファイルがバイナリ形式でないか、Jinja2形式として正しいか、必要な構文が含まれているかを検証する。

    Args:
        file_path (str): ファイルパス
        target_column_name (dict): カラム名（日本語・英語）
        target_lang (str): 言語設定
        msg (list): エラーメッセージリスト
    Returns:
        retBool (bool): True/False
        msg (list): エラーメッセージ
    """
    retBool = True
    with open(file_path, "rb") as f:
        template_data_binary = f.read()

    if validator.is_binary_file(template_data_binary):
        msg.append(g.appmsg.get_api_message("499-01814", [target_column_name[target_lang]]))
        return False, msg

    template_data_decoded = template_data_binary.decode("utf-8", "ignore")
    if not validator.is_jinja2_template(template_data_decoded):
        msg.append(g.appmsg.get_api_message("499-01815", [target_column_name[target_lang]]))
        return False, msg

    if not validator.contains_title(template_data_decoded):
        msg.append(g.appmsg.get_api_message("499-01816", [target_column_name[target_lang]]))
        retBool = False

    if not validator.contains_body(template_data_decoded):
        msg.append(g.appmsg.get_api_message("499-01817", [target_column_name[target_lang]]))
        retBool = False

    return retBool, msg


def is_id_in_default_range(notification_template_id):
    """
    通知テンプレートIDが1～6の場合はTrueを返す

    Args:
        notification_template_id (str): 通知テンプレートID
    Returns:
        bool: True/False
    """
    if notification_template_id in ["1", "2", "3", "4", "5", "6"]:
        return True
    else:
        return False


def check_duplicate_notification_destination(objdbca, notification_template_id, event_type, notification_destination):
    """
    同一の通知先、その通知先を返す

    通知先が他の通知テンプレートと重複していないかを確認する。

    Args:
        objdbca (object): DB接続クラスインスタンス
        notification_template_id (str): 通知テンプレートID
        event_type (str): イベント種別
        notification_destination (str): 通知先ID文字列
    Returns:
        str: 通知先名称 / 空文字
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

    指定された通知テンプレートIDとイベント種別に基づいて、通知先のデータを取得する。

    Args:
        objdbca (object): DB接続クラスインスタンス
        notification_template_id (str): 通知テンプレートID
        event_type (str): イベント種別
    Returns:
        list: 取得レコード
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
