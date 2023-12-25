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

import copy
import json
import os
import re
from abc import ABC, abstractmethod

import requests
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.exception import AppException
from flask import g
from jinja2 import Template
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


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
        g.applogger.info(g.appmsg.get_log_message("BKY-80000"))
        g.applogger.debug(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
        g.applogger.debug(g.appmsg.get_log_message("BKY-80008", [len(event_list)]))
        g.applogger.debug(g.appmsg.get_log_message("BKY-80009", [decision_information]))

        fetch_data = cls._fetch_table(objdbca, decision_information)
        if fetch_data is None:
            g.applogger.info(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80009", [decision_information]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80002"))
            return {}

        template = cls._get_template(fetch_data, decision_information)
        if template is None:
            g.applogger.info(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80009", [decision_information]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80003"))
            return {}

        # 負荷を考慮して通知先は1回のみ取得することとする
        notification_destination = cls._fetch_notification_destination(fetch_data, decision_information)
        if len(notification_destination) == 0:
            g.applogger.info(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80009", [decision_information]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80004"))
            return {}

        g.applogger.debug(g.appmsg.get_log_message("BKY-80010", [len(notification_destination) * len(event_list)]))

        result = {
            "success": 0,
            "failure": 0,
            "failure_info": [],
            "success_notification_count": 0,
            "failure_notification_count": 0
        }

        for index, item in enumerate(event_list):
            # _convert_messageでitemを直接書き換えると再実行時にエラーが発生する可能性があるため、複製したデータをベースに処理を行う。
            tmp_item = copy.deepcopy(item)
            g.applogger.debug(g.appmsg.get_log_message("BKY-80011", [index + 1]))

            message = cls._create_notise_message(tmp_item, template)
            # messageがNoneの場合、テンプレートの変換に失敗しているので次のループに進む
            if message is None:
                result["failure_info"].append(g.appmsg.get_log_message("BKY-80024", [tmp_item, template]))
                result["failure"] = result["failure"] + 1
                continue

            tmp_result = cls.__call_notification_api(message, notification_destination)

            result["success"] = result["success"] + tmp_result["success"]
            result["failure"] = result["failure"] + tmp_result["failure"]
            result["failure_info"].extend(tmp_result["failure_info"])
            result["success_notification_count"] = result["success_notification_count"] + tmp_result["success_notification_count"]
            result["failure_notification_count"] = result["failure_notification_count"] + tmp_result["failure_notification_count"]

            g.applogger.debug(g.appmsg.get_log_message("BKY-80012", [index + 1]))

        g.applogger.debug(g.appmsg.get_log_message("BKY-80013", [result]))
        g.applogger.info(g.appmsg.get_log_message("BKY-80001"))

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
        item = cls._convert_message(item)

        jinja_template = Template(template)
        try:
            tmp_message = jinja_template.render(item)
        except Exception as e:
            g.applogger.info(g.appmsg.get_log_message("BKY-80014", [item.get('_id')]))
            g.applogger.error(e)
            g.applogger.error(g.appmsg.get_log_message("BKY-80006"))
            return None

        # [TITLE]の次の1行をtitleとして抽出する
        # バリデーションチェックで[TITLE]無しは弾くので、存在チェックは不要
        search_title = re.search(r"\[TITLE\]\s(.*)", tmp_message)
        title = search_title.group(1) if search_title is not None else ""

        # [BODY]の次の1行から終端をmessageとして抽出する
        # バリデーションチェックで[BODY]無しは弾くので、存在チェックは不要
        search_body = re.search(r"\[BODY\]\s([\s\S]*)", tmp_message)
        text = search_body.group(1) if search_body is not None else ""

        # [BODY]と[TITLE]の記載位置で結果が変わるのを防ぐため、
        # [TITLE]が[BODY]の後に定義された場合を考慮して、取り除く処理を実施
        # [TITLE]に関しては次の1行を抽出するため対処不要
        text = re.sub(r"\[TITLE\]([\s\S]*)", "", text)

        result = {
            "title": title.strip("\n"),
            "message": text.strip("\n")
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
    def _call_setting_notification_api(event_type_true: list = None, event_type_false: list = None):
        """
        通知先取得APIを呼び出し、結果を返却する
        Args:
            event_type_true (list, optional): 指定したevent_typeがtrueのデータを抽出したい場合に指定する。 Defaults to None.
            event_type_false (list, optional): 指定したevent_typeがfalseのデータを抽出したい場合に指定する。 Defaults to None.

        Raises:
            AppException: _description_

        Returns:
            _type_: _description_
        """

        organization_id = g.get('ORGANIZATION_ID')
        workspace_id = g.get('WORKSPACE_ID')
        host_name = os.environ.get('PLATFORM_API_HOST')
        port = os.environ.get('PLATFORM_API_PORT')
        user_id = g.get('USER_ID')
        language = g.get('LANGUAGE')

        header_para = {
            "User-Id": user_id,
            "Language": language
        }

        query_params = {}
        if event_type_true is not None and len(event_type_true) > 0:
            # query_params["event_type_true"] = ",".join(event_type_true)
            # 現状はこの設定だが上で動くように修正される予定（区切り文字が|から,に変わる）
            query_params["event_type_true"] = "|".join(event_type_true)

        if event_type_false is not None and len(event_type_false) > 0:
            # query_params["event_type_false"] = ",".join(event_type_false)
            # 現状はこの設定だが上で動くように修正される予定（区切り文字が|から,に変わる）
            query_params["event_type_false"] = "|".join(event_type_false)

        # API呼出
        api_url = f"http://{host_name}:{port}/internal-api/{organization_id}/platform/workspaces/{workspace_id}/settings/notifications"

        s = requests.Session()

        retries = Retry(total=5,
                        backoff_factor=1)

        s.mount('http://', HTTPAdapter(max_retries=retries))
        s.mount('https://', HTTPAdapter(max_retries=retries))

        request_response = s.request(method='GET', url=api_url, timeout=2, headers=header_para, params=query_params)

        response_data = request_response.json()

        if request_response.status_code != 200:
            raise AppException('999-00005', [api_url, response_data])

        g.applogger.debug(g.appmsg.get_log_message("BKY-80015"))
        g.applogger.debug(g.appmsg.get_log_message("BKY-80016", [len(response_data['data'])]))
        for index, item in enumerate(response_data["data"]):
            g.applogger.debug(g.appmsg.get_log_message("BKY-80017", [index + 1, item.get('id'), item.get('name')]))

        return response_data

    @classmethod
    def __call_notification_api(cls, message, notification_destination):
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
            "Language": language
        }

        body_data_list = []
        # 通知先の件数分データを作成する
        for item in notification_destination:
            data = cls._get_data()
            data["message"] = message
            data["destination_id"] = item
            body_data_list.append(data)

        data_encode = json.dumps(body_data_list)

        # API呼出
        api_url = f"http://{host_name}:{port}/internal-api/{organization_id}/platform/workspaces/{workspace_id}/notifications"

        s = requests.Session()

        retries = Retry(total=5,
                        backoff_factor=1)

        s.mount('http://', HTTPAdapter(max_retries=retries))
        s.mount('https://', HTTPAdapter(max_retries=retries))

        request_response = s.request(method='POST', url=api_url, timeout=2, headers=header_para, data=data_encode)

        result = {
            "success": 0,
            "failure": 0,
            "failure_info": [],
            "success_notification_count": 0,
            "failure_notification_count": 0
        }

        if request_response.status_code != 200:
            # ループで処理する都合エラーが発生してもその瞬間に例外は発生させない
            # 代わりにエラー件数とエラーが発生した際のリクエスト内容を記録し、呼び出し元に返却するようにする。
            g.applogger.info(g.appmsg.get_log_message("BKY-80026", [data]))
            result["failure"] = 1
            result["failure_info"].append(data)
            result["failure_notification_count"] = len(body_data_list)
        else:
            result["success"] = 1
            result["success_notification_count"] = len(body_data_list)

        g.applogger.debug(g.appmsg.get_log_message("BKY-80018", [result]))

        return result

    @staticmethod
    def _get_data():
        """
        通知APIに個別の値を設定する場合、オーバーライドして必要な設定を記載すること
        Returns:
            必要な設定を施したdict
        """
        return {}

    @classmethod
    def fetch_notification_destination_dict(cls):
        """
        通知先IDと通知先名称のdictを取得する
        Returns:
           Key: 通知先ID, Value: 通知先名のdict
        """
        fetch_data = cls._call_setting_notification_api()
        data = fetch_data["data"]

        result = {}
        for item in data:
            result[item["id"]] = item["name"]

        return result
