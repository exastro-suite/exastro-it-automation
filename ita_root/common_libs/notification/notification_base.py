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

import json
import os
import re
from abc import ABC, abstractmethod

import requests
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.exception import AppException
from flask import g
from jinja2 import Template


class Notification(ABC):
    """
    通知に関する共通の振る舞いを定義するクラス
    """
    @classmethod
    def send(cls, objdbca: DBConnectWs, event_list: list, decision_information: dict):
        """
        通知を送る処理
        Args:
            objdbca (DBConnectWs): MariaDBのコネクション\n
            event_list (list): 通知の条件を満たしたイベントのlist\n
            decision_information (dict): 何かしら判定が必要な場合はここに必要な情報を詰めて渡す\n
        """
        g.applogger.info("通知処理開始")
        g.applogger.info(f"通知サブクラス名：{cls.__qualname__}")
        g.applogger.info(f"通知するイベントの件数：{len(event_list)}")
        g.applogger.info(f"通知に関する情報：{decision_information}")

        fetch_data = cls._fetch_table(objdbca, decision_information)
        template = cls._get_template(fetch_data, decision_information)

        # 負荷を考慮して通知先は1回のみ取得することとする
        notification_destination = cls._fetch_notification_destination(fetch_data, decision_information)

        g.applogger.info(f"合計で通知する件数：{len(notification_destination) * len(event_list)}")

        result = {
            "success": 0,
            "failure": 0,
            "failure_info": []
        }

        for index, item in enumerate(event_list):
            g.applogger.info(f"{index + 1}件目のイベントの処理開始")

            message = cls._create_notise_message(item, template)
            tmp_result = cls.__call_notification_api(message, notification_destination)

            result["success"] = result["success"] + tmp_result["success"]
            result["failure"] = result["failure"] + tmp_result["failure"]
            result["failure_info"].extend(tmp_result["failure_info"])

            g.applogger.info(f"{index + 1}件目のイベントの処理終了")

        g.applogger.info(f"最終的な通知APIの呼び出し結果:\n{result}")
        g.applogger.info("通知処理終了")

        return result

    @abstractmethod
    def _fetch_table(objdbca: DBConnectWs, decision_information: dict):
        """
        通知を行うために必要な情報を取得する処理を記載する
        Args:
            objdbca (DBConnectWs): MariaDBのコネクション
            decision_information (dict): 何かしら判定が必要な場合はここに必要な情報を詰めて渡す
        """
        pass

    @abstractmethod
    def _get_template(fetch_data, decision_information: dict):
        """
        DBから取得した情報を用いてテンプレートファイルを取得する
        Args:
            fetch_data: MariaDBから取得したデータ
            decision_information (dict): 何かしら判定が必要な場合はここに必要な情報を詰めて渡す
        """
        pass

    @classmethod
    def _create_notise_message(cls, item, template):
        """
        通知するメッセージを作成する。
        Args:
            item: 通知するイベント
            template: メッセージのテンプレート
        """
        g.applogger.info(f"テンプレートのレンダリングに利用するオブジェクトのID:{item.get('_id')}")

        item = cls._convert_message(item)

        jinja_template = Template(template)
        tmp_message = jinja_template.render(item)
        split_message = re.split(r"\[TITLE\]|\[BODY\]", tmp_message)

        result = {
            "title": split_message[1].strip("\n"),
            "text": split_message[2].strip("\n")
        }

        return result

    @staticmethod
    def _convert_message(item):
        """
        テンプレートに適用する前に変換が必要な項目があればこのメソッドで対応すること
        まとめて受け取って、まとめて返す想定
        Args:
            item : 変換元となる値
        Returns:
            変換後の値
        """
        return item

    @abstractmethod
    def _fetch_notification_destination(fetch_data, decision_information: dict):
        """
        通知先を取得する
        Args:
            fetch_data: MariaDBから取得したデータ
            decision_information (dict): 何かしら判定が必要な場合はここに必要な情報を詰めて渡す
        """
        pass

    @staticmethod
    def call_setting_notification_api():
        """_summary_
        """

        organization_id = g.get('ORGANIZATION_ID')
        workspace_id = g.get('WORKSPACE_ID')
        host_name = os.environ.get('PLATFORM_API_HOST')
        port = os.environ.get('PLATFORM_API_PORT')
        user_id = g.get('USER_ID')
        language = g.get('LANGUAGE')

        header_para = {
            "User-Id": user_id,
            "Roles": json.dumps(g.ROLES),
            "Language": language
        }

        # API呼出
        api_url = f"http://{host_name}:{port}/api/{organization_id}/platform/workspaces/{workspace_id}/settings/notifications"
        request_response = requests.get(api_url, headers=header_para)

        response_data = request_response.json()

        if request_response.status_code != 200:
            raise AppException('999-00005', [api_url, response_data])

        g.applogger.info("通知先取得APIの呼び出し結果")
        g.applogger.info(f"合計取得件数:{len(response_data)}")
        for index, item in enumerate(response_data):
            g.applogger.info(f"{index + 1}件目　id:{item.get('id')}, name:{item.get('name')}")

        return response_data

    @staticmethod
    def __call_notification_api(message, notification_destination):
        """
        Platformの通知APIをコールする
        Args:
            message: イベントとテンプレートを使って生成したdict
            notification_destination: 通知先のリスト
        """

        organization_id = g.get('ORGANIZATION_ID')
        workspace_id = g.get('WORKSPACE_ID')
        host_name = os.environ.get('PLATFORM_API_HOST')
        port = os.environ.get('PLATFORM_API_PORT')
        user_id = g.get('USER_ID')
        language = g.get('LANGUAGE')

        header_para = {
            "Content-Type": "application/json",
            "User-Id": user_id,
            "Roles": json.dumps(g.ROLES),
            "Language": language
        }

        data = {}
        data["message_informations"] = message
        data["func_id"] = "1102"
        data["func_informations"] = {"name": "OASE"}

        # API呼出
        api_url = f"http://{host_name}:{port}/api/{organization_id}/platform/workspaces/{workspace_id}/notifications"

        result = {
            "success": 0,
            "failure": 0,
            "failure_info": []
        }

        # 通知先の件数分Platformの通知APIをコールする
        for item in notification_destination:
            data["destination_id"] = item
            data_encode = json.dumps(data)

            request_response = requests.post(url=api_url, headers=header_para, data=data_encode)

            if request_response.status_code != 200:
                # ループで処理する都合エラーが発生してもその瞬間に例外は発生させない
                # 代わりにエラー件数とエラーが発生した際のリクエスト内容を記録し、呼び出し元に返却するようにする。
                result["failure"] += 1
                result["failure_info"].append(data)
            else:
                result["success"] += 1

        g.applogger.info(f"通知APIの呼び出し結果:\n{result}")

        return result
