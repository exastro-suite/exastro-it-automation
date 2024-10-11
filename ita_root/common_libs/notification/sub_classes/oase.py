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

import datetime
import json
from enum import Enum

from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.util import get_upload_file_path
from common_libs.notification.notification_base import Notification
from common_libs.common import storage_access
from flask import g


class OASENotificationType(Enum):
    """
    OASEの通知の種類を定義したEnum
    """
    # 新規
    NEW = 1
    # 既知（判定済み）
    EVALUATED = 2
    # 既知（時間切れ）
    TIMEOUT = 3
    # 未知
    UNDETECTED = 4
    # 事前通知
    BEFORE_ACTION = 5
    # 事後通知
    AFTER_ACTION = 6


class OASE(Notification):
    """
    OASEの通知に関する処理を定義するクラス
    decision_informationに以下の2項目が必要
    ・notification_type：OASENotificationTypeの値
    ・rule_id：ルールのID（ルールに関する通知を行う場合必須）
    """

    # OASENotificationTypeとテンプレートファイルを取得する際に必要な情報の対応表
    TEMPLATE_SEARCH_CONDITION = {
        OASENotificationType.NEW: {
            "menu_id": "110102",
            "rest_name": "template_file"
        },
        OASENotificationType.EVALUATED: {
            "menu_id": "110102",
            "rest_name": "template_file"
        },
        OASENotificationType.TIMEOUT: {
            "menu_id": "110102",
            "rest_name": "template_file"
        },
        OASENotificationType.UNDETECTED: {
            "menu_id": "110102",
            "rest_name": "template_file"
        },
        OASENotificationType.BEFORE_ACTION: {
            "menu_id": "110109",
            "rest_name": "before_notification"
        },
        OASENotificationType.AFTER_ACTION: {
            "menu_id": "110109",
            "rest_name": "after_notification"
        }
    }

    # OASENotificationTypeと通知先取得のAPIに指定する条件の対応表
    DESTINATION_ID_FETCH_CONDITION = {
        OASENotificationType.NEW: "ita.event_type.new",
        OASENotificationType.EVALUATED: "ita.event_type.evaluated",
        OASENotificationType.TIMEOUT: "ita.event_type.timeout",
        OASENotificationType.UNDETECTED: "ita.event_type.undetected",
    }

    DATA_CONVERT_MAP = {
        "_exastro_type": {
            "event": "event",
            "conclusion": "conclusion"
        }
    }

    @classmethod
    def _fetch_table(cls, objdbca: DBConnectWs, decision_information: dict):
        notification_type = decision_information.get("notification_type")
        rule_id = decision_information.get("rule_id")

        if notification_type in [OASENotificationType.BEFORE_ACTION, OASENotificationType.AFTER_ACTION] and rule_id is None:
            g.applogger.info(g.appmsg.get_log_message("BKY-80025"))
            return None

        values = cls.__get_table_search_condition(notification_type, rule_id)

        query = f"SELECT {values['display_column']} FROM {values['table']} WHERE DISUSE_FLAG=0 AND {values['condition_column']}"

        query_result = objdbca.sql_execute(query, values['condition_value'])
        if len(query_result) == 0:
            g.applogger.info(g.appmsg.get_log_message("BKY-80019", [query]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80020", [values['condition_value']]))
            return None

        return query_result.pop()

    @classmethod
    def _get_template(cls, fetch_data, decision_information: dict):
        notification_type = decision_information.get("notification_type")

        values = cls.TEMPLATE_SEARCH_CONDITION[notification_type]

        uuid = fetch_data["UUID"]
        workspace_id = g.get("WORKSPACE_ID")
        menu_id = values["menu_id"]
        rest_name = values["rest_name"]
        file_name = fetch_data["TEMPLATE_FILE"]
        if file_name is None or file_name == '':
            return None

        path = get_upload_file_path(workspace_id, menu_id, uuid, rest_name, file_name, "")

        try:
            access_file = storage_access.storage_read()
            access_file.open(path["file_path"])
            template = access_file.read()
            access_file.close()
        except Exception as e:
            g.applogger.info(g.appmsg.get_log_message("BKY-80021", [path]))
            g.applogger.error(e)
            return None

        return template

    @classmethod
    def _fetch_notification_destination(cls, fetch_data, decision_information: dict):
        notification_type = decision_information.get("notification_type")

        if notification_type in [OASENotificationType.BEFORE_ACTION, OASENotificationType.AFTER_ACTION]:
            notification_destination_str = fetch_data.get("NOTIFICATION_DESTINATION")
            if notification_destination_str is None or notification_destination_str == '':
                return []

            notification_destination_dict = json.loads(notification_destination_str)

            g.applogger.debug(g.appmsg.get_log_message("BKY-80022", [notification_destination_dict['id']]))

            notification_destination_list = cls.__exists_notification_destination(notification_destination_dict["id"])

            g.applogger.debug(g.appmsg.get_log_message("BKY-80023", [notification_destination_list]))

            return notification_destination_list

        event_type_true_list = [cls.DESTINATION_ID_FETCH_CONDITION[notification_type]]
        response = cls._call_setting_notification_api(event_type_true=event_type_true_list)
        filtered_list = [item.get("id") for item in response["data"]]

        return filtered_list

    @classmethod
    def __exists_notification_destination(cls, notification_destination_list):
        """
        引数で渡された通知先が存在するか確認する
        Args:
            notification_destination_dict (_type_): ルールから取得した通知先

        Returns:
            存在しない通知先を間引いた通知先の一覧
        """

        response = cls._call_setting_notification_api()
        feched_notification_destination_list = [item.get("id") for item in response["data"]]

        result = []
        for item in notification_destination_list:
            if item in feched_notification_destination_list:
                result.append(item)
            else:
                g.applogger.info(g.appmsg.get_log_message("BKY-80005", [item]))

        return result

    @classmethod
    def _convert_message(cls, item):

        if "labels" not in item:
            return item

        if "_exastro_fetched_time" in item["labels"]:
            item["labels"]["_exastro_fetched_time"] = datetime.datetime.fromtimestamp(int(
                item["labels"]["_exastro_fetched_time"])).strftime("%Y/%m/%d %H:%M:%S")

        if "_exastro_end_time" in item["labels"]:
            item["labels"]["_exastro_end_time"] = datetime.datetime.fromtimestamp(int(
                item["labels"]["_exastro_end_time"])).strftime("%Y/%m/%d %H:%M:%S")

        if "_exastro_type" in item["labels"]:
            item["labels"]["_exastro_type"] = cls.DATA_CONVERT_MAP["_exastro_type"][item["labels"]["_exastro_type"]]

        return item

    @staticmethod
    def _get_data():
        data = {}
        data["func_id"] = "1102"
        data["func_informations"] = {"menu_group_name": "OASE"}

        return data

    def __get_table_search_condition(notification_type: OASENotificationType, rule_id):
        # OASENotificationTypeとDB検索で必要な情報の対応表
        # テーブル間の差分を吸収するためID列には別名を定義
        # BEFORE_ACTIONおよびAFTER_ACTIONは条件を動的に追加するため、実装の都合でクラス変数として扱わないこととした。

        table_search_condition = {
            OASENotificationType.NEW: {
                "table": "T_OASE_NOTIFICATION_TEMPLATE_COMMON",
                "display_column": "NOTIFICATION_TEMPLATE_ID AS UUID, TEMPLATE_FILE",
                "condition_column": "EVENT_TYPE=%s",
                "condition_value": ["1"]  # 新規
            },
            OASENotificationType.EVALUATED: {
                "table": "T_OASE_NOTIFICATION_TEMPLATE_COMMON",
                "display_column": "NOTIFICATION_TEMPLATE_ID AS UUID, TEMPLATE_FILE",
                "condition_column": "EVENT_TYPE=%s",
                "condition_value": ["2"]  # 既知（判定済み）

            },
            OASENotificationType.TIMEOUT: {
                "table": "T_OASE_NOTIFICATION_TEMPLATE_COMMON",
                "display_column": "NOTIFICATION_TEMPLATE_ID AS UUID, TEMPLATE_FILE",
                "condition_column": "EVENT_TYPE=%s",
                "condition_value": ["3"]  # 既知（時間切れ）

            },
            OASENotificationType.UNDETECTED: {
                "table": "T_OASE_NOTIFICATION_TEMPLATE_COMMON",
                "display_column": "NOTIFICATION_TEMPLATE_ID AS UUID, TEMPLATE_FILE",
                "condition_column": "EVENT_TYPE=%s",
                "condition_value": ["4"]  # 未知

            },
            OASENotificationType.BEFORE_ACTION: {
                "table": "T_OASE_RULE",
                "display_column": """
                RULE_ID AS UUID, BEFORE_NOTIFICATION AS TEMPLATE_FILE, BEFORE_NOTIFICATION_DESTINATION AS NOTIFICATION_DESTINATION
                """,
                "condition_column": "RULE_ID=%s",
                "condition_value": [rule_id]
            },
            OASENotificationType.AFTER_ACTION: {
                "table": "T_OASE_RULE",
                "display_column": "RULE_ID AS UUID, AFTER_NOTIFICATION AS TEMPLATE_FILE, AFTER_NOTIFICATION_DESTINATION AS NOTIFICATION_DESTINATION",
                "condition_column": "RULE_ID=%s",
                "condition_value": [rule_id]
            }
        }

        return table_search_condition[notification_type]
