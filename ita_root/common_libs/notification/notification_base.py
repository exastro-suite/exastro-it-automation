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
import concurrent.futures

import requests
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.exception import AppException
from flask import g
from jinja2 import Template
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from collections import defaultdict


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
        return cls.__send(objdbca, event_list, decision_information, False)

    @classmethod
    def bulksend(cls, objdbca: DBConnectWs, event_list: list, decision_information: dict):
        """
        通知を送る処理をマルチスレッドでまとめて実施する\n
        Args:
            objdbca (DBConnectWs): MariaDBのコネクション
            event_list (list): 通知の条件を満たしたイベントのlist
            decision_information (dict): 何かしら判定が必要な場合はここに必要な情報を詰めて渡す
        Returns:
            result (dict): 処理結果を含む辞書
        """
        # 基本的に既存処理(__send)を流用してスレッド処理
        g.applogger.info(g.appmsg.get_log_message("BKY-80000"))
        g.applogger.debug(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
        g.applogger.debug(g.appmsg.get_log_message("BKY-80008", [len(event_list)]))
        g.applogger.debug(g.appmsg.get_log_message("BKY-80009", [decision_information]))

        # ITAのWSDBにアクセスし、イベント種別に該当する通知先テンプレートのレコードをfetch_dataに詰める
        # ita_root/common_libs/notification/sub_classes/oase.pyの_fetch_tableを参照
        fetch_data = cls._fetch_table(objdbca, decision_information)
        if fetch_data is None:
            # 通知先テンプレートのレコードが1件も取得できなかった場合は終わり
            # g.applogger.info(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
            # g.applogger.info(g.appmsg.get_log_message("BKY-80009", [decision_information]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80002"))
            return {}

        # fetch_dataに対して、実際のJinja2テンプレートファイルの中身をtemplate_listに詰める
        # ita_root/common_libs/notification/sub_classes/oase.pyの_get_templateを参照
        template_list = cls._get_template(fetch_data, decision_information)
        has_none_template = any(item.get("template") is None for item in template_list)
        if has_none_template:
            # テンプレートファイルが1件も取得できなかった場合は終わり
            # g.applogger.info(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
            # g.applogger.info(g.appmsg.get_log_message("BKY-80009", [decision_information]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80003"))
            return {}

        # 負荷を考慮して通知先は1回のみ取得しそれを流用する
        # fetch_dataから通知先のIDリストだけを抜いてnotification_destinationに詰める
        # ita_root/common_libs/notification/sub_classes/oase.pyの_fetch_notification_destinationを参照
        notification_destination = cls._fetch_notification_destination(fetch_data, decision_information)
        if len(notification_destination) == 0:
            # 通知先のIDが1件も取得できなかった場合は終わり
            # g.applogger.info(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
            # g.applogger.info(g.appmsg.get_log_message("BKY-80009", [decision_information]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80004"))
            return {}

        g.applogger.debug(g.appmsg.get_log_message("BKY-80010", [len(notification_destination) * len(event_list)]))

        result = {
            "success": 0,
            "failure": 0,
            "failure_info": [],
            "success_notification_count": 0,
            "failure_notification_count": 0,
            "failure_create_messages": []
        }

        # 並列処理でJinja2テンプレートの変換をしてAPI実行まで
        def process_event_call_api(items, organization_id, workspace_id, user_id, language):
            message_list = []
            err_list = []
            for item in items:
                for template_item in template_list:
                    tmp_item = copy.deepcopy(item)
                    template = template_item.get("template")
                    message = cls._create_notise_message(tmp_item, template)
                    if message is None:
                        # Jinja2テンプレート変換処理の中で例外が発生した場合は_error_message_listに詰める
                        err_list.append([tmp_item, template])
                        continue
                    message_list.append({
                        "id": template_item.get("id"),
                        "message": message,
                        "IS_DEFAULT": template_item.get("IS_DEFAULT"),
                    })
            # __call_notification_api_threadではAPI送信部分については例外発生させない
            # メッセージ周りの変数の挙動で例外発生した場合は例外として挙がってくる
            return cls.__call_notification_api_thread(message_list, notification_destination, organization_id, workspace_id, user_id, language), err_list

        notification_batch_size = int(os.environ.get("NOTIFICATION_BATCH_SIZE", 100))  # 一度に送る件数
        MAX_WORKERS = int(os.environ.get("MAX_WORKER_THREAD_POOL_SIZE", 12))
        _getenv_keys = ['ORGANIZATION_ID', 'WORKSPACE_ID', 'USER_ID', 'LANGUAGE']
        organization_id, workspace_id, user_id, language = (g.get(key) for key in _getenv_keys)

        # 並列処理でテンプレートの変換、一括送信
        error_message_list = []
        _error_message_list = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(process_event_call_api, event_list[i: i + notification_batch_size], organization_id, workspace_id, user_id, language) for i in range(0, len(event_list), notification_batch_size)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    tmp_result, _error_message_list = future.result()
                    error_message_list = [g.appmsg.get_log_message("BKY-80024", [m[0], m[1]]) for m in _error_message_list] if _error_message_list else []
                    result["success"] = result["success"] + tmp_result["success"]
                    result["failure"] = result["failure"] + tmp_result["failure"]
                    result["failure_info"].extend(tmp_result["failure_info"])
                    result["success_notification_count"] = result["success_notification_count"] + tmp_result["success_notification_count"]
                    result["failure_notification_count"] = result["failure_notification_count"] + tmp_result["failure_notification_count"]
                    result["failure_create_messages"].extend(error_message_list)
                except Exception as e:
                    # スレッドで例外が発生した場合の処理
                    # スレッド処理全体は継続させ、resultに詰めておく
                    g.applogger.error(f"ThreadPoolExecutor failed: {e}")
                    result["failure"] = result["failure"] + 1
                    result["failure_info"].append(f"Thread exception: {e}")

        g.applogger.debug(g.appmsg.get_log_message("BKY-80013", [result]))
        g.applogger.info(g.appmsg.get_log_message("BKY-80001"))
        return result

    @classmethod
    def buffered_send(cls, objdbca: DBConnectWs, event_list: list, decision_information: dict):
        """
        通知を送る処理(バッファリング送信)
        Args:
            objdbca (DBConnectWs): MariaDBのコネクション\n
            event_list (list): 通知の条件を満たしたイベントのlist\n
            decision_information (dict): 何かしら判定が必要な場合はここに必要な情報を詰めて渡す\n
        """
        return cls.__send(objdbca, event_list, decision_information, True)

    @classmethod
    def flush_send_buffer(cls):
        """バッファ上の通知を送信します
        """
        return cls._flush_send_buffer()

    @classmethod
    def __send(cls, objdbca: DBConnectWs, event_list: list, decision_information: dict, buffered_send: bool):
        """
        通知を送る処理
        Args:
            objdbca (DBConnectWs): MariaDBのコネクション\n
            event_list (list): 通知の条件を満たしたイベントのlist\n
            decision_information (dict): 何かしら判定が必要な場合はここに必要な情報を詰めて渡す\n
            buffered_send (bool): バッファリング送信を行うかどうか\n
        """
        g.applogger.info(g.appmsg.get_log_message("BKY-80000"))
        g.applogger.debug(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
        g.applogger.debug(g.appmsg.get_log_message("BKY-80008", [len(event_list)]))
        g.applogger.debug(g.appmsg.get_log_message("BKY-80009", [decision_information]))

        fetch_data = cls._fetch_table(objdbca, decision_information)
        if fetch_data is None:
            # g.applogger.info(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
            # g.applogger.info(g.appmsg.get_log_message("BKY-80009", [decision_information]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80002"))
            return {}

        template_list = cls._get_template(fetch_data, decision_information)
        has_none_template = any(item.get("template") is None for item in template_list)
        if has_none_template:
            # g.applogger.info(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
            # g.applogger.info(g.appmsg.get_log_message("BKY-80009", [decision_information]))
            g.applogger.info(g.appmsg.get_log_message("BKY-80003"))
            return {}

        # 負荷を考慮して通知先は1回のみ取得することとする
        notification_destination = cls._fetch_notification_destination(fetch_data, decision_information)
        if len(notification_destination) == 0:
            # g.applogger.info(g.appmsg.get_log_message("BKY-80007", [cls.__qualname__]))
            # g.applogger.info(g.appmsg.get_log_message("BKY-80009", [decision_information]))
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
            g.applogger.debug(g.appmsg.get_log_message("BKY-80011", [index + 1]))

            found_none_message = False
            message_list = []
            for template_item in template_list:
                # _convert_messageでitemを直接書き換えると再実行時にエラーが発生する可能性があるため、複製したデータをベースに処理を行う。
                tmp_item = copy.deepcopy(item)
                template = template_item.get("template")
                message = cls._create_notise_message(tmp_item, template)

                # messageがNoneの場合、テンプレートの変換に失敗しているので次のループに進む
                if message is None:
                    result["failure_info"].append(g.appmsg.get_log_message("BKY-80024", [tmp_item, template]))
                    result["failure"] = result["failure"] + 1
                    found_none_message = True
                    break

                message_list.append({
                    "id": template_item.get("id"),
                    "message": message,
                    "IS_DEFAULT": template_item.get("IS_DEFAULT"),
                })

            if found_none_message is True:
                continue

            tmp_result = cls.__call_notification_api(message_list, notification_destination, buffered_send)

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

    # 通知先のキャッシュ
    #   _setting_notification_cache_org_id: キャッシュ中のorganization id
    #   _setting_notification_cache_ws_id: キャッシュ中のworkspace id
    #   _setting_notification_cache: キャッシュ本体
    #       _setting_notification_cache["通知先取得URLのクエリパラメータの文字列"] = [通知先のリスト]
    _setting_notification_cache = {}
    _setting_notification_cache_org_id = None
    _setting_notification_cache_ws_id = None

    @classmethod
    def _call_setting_notification_api(cls, event_type_true: list = None, event_type_false: list = None):
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

        # 作業対象のworkspaceが変わったらキャッシュをクリアする
        if not (cls._setting_notification_cache_org_id == organization_id and cls._setting_notification_cache_ws_id == workspace_id):
            cls._setting_notification_cache = {}
            cls._setting_notification_cache_org_id = organization_id
            cls._setting_notification_cache_ws_id = workspace_id

        query_params = {}
        if event_type_true is not None and len(event_type_true) > 0:
            # query_params["event_type_true"] = ",".join(event_type_true)
            # 現状はこの設定だが上で動くように修正される予定（区切り文字が|から,に変わる）
            query_params["event_type_true"] = "|".join(event_type_true)

        if event_type_false is not None and len(event_type_false) > 0:
            # query_params["event_type_false"] = ",".join(event_type_false)
            # 現状はこの設定だが上で動くように修正される予定（区切り文字が|から,に変わる）
            query_params["event_type_false"] = "|".join(event_type_false)

        if json.dumps(query_params) in cls._setting_notification_cache:
            # キャッシュにデータがある場合はキャッシュの情報を返す
            return cls._setting_notification_cache[json.dumps(query_params)]
        else:
            # キャッシュにデータがない場合はAPIを呼び出す

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

            # 通知先の情報をキャッシュに保存する
            cls._setting_notification_cache[json.dumps(query_params)] = response_data

            return response_data

    # 送信バッファ
    #   _send_buffer: 送信バッファ本体
    #   _send_buffer_org_id: キャッシュ中のorganization id
    #   _send_buffer_ws_id: キャッシュ中のworkspace id
    _send_buffer = []
    _send_buffer_org_id = None
    _send_buffer_ws_id = None

    @classmethod
    def __call_notification_api(cls, message_list, notification_destination, buffered_send: bool):
        """
        Platformの通知APIをコールする
        Args:
            message_list: イベントとテンプレートを使って生成したdict
            notification_destination: 通知先のリスト
            buffered_send: バッファリング送信を行うかどうか
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

        # 通知先の件数分データを作成する
        message_map = {}
        for m in message_list:
            msg_id = m.get("id")
            if isinstance(msg_id, list):
                for i in msg_id:
                    message_map[i] = m["message"]
            elif msg_id is not None:
                message_map[msg_id] = m["message"]
        default_message = next((m["message"] for m in message_list if m.get("IS_DEFAULT") == "●"), None)

        body_data_list = [
            {
                **cls._get_data(),
                "destination_id": item,
                "message": message_map.get(item, default_message)
            }
            for item in notification_destination
        ]

        if not buffered_send:
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
                g.applogger.info(g.appmsg.get_log_message("BKY-80026", [data_encode]))
                result["failure"] = 1
                result["failure_info"].append(data_encode)
                result["failure_notification_count"] = len(body_data_list)
            else:
                result["success"] = 1
                result["success_notification_count"] = len(body_data_list)

            g.applogger.debug(g.appmsg.get_log_message("BKY-80018", [result]))
        else:
            if not (organization_id == cls._send_buffer_org_id and workspace_id == cls._send_buffer_ws_id):
                # Workspaceが変わった場合はバッファを送信する
                cls._flush_send_buffer()

            cls._send_buffer_org_id = organization_id
            cls._send_buffer_ws_id = workspace_id
            cls._send_buffer.extend(body_data_list)

            if len(cls._send_buffer) >= int(os.environ.get('NOTIFICATION_BUFFER_SIZE', 100)):
                # バッファサイズを超えた場合はバッファを送信する
                cls._flush_send_buffer()

            # バッファリングの時は成功扱いにする
            result = {
                "success": 1,
                "failure": 0,
                "failure_info": [],
                "success_notification_count": len(body_data_list),
                "failure_notification_count": 0
            }

        return result

    @classmethod
    def __call_notification_api_thread(cls, message_list, notification_destination, organization_id, workspace_id, user_id, language):
        """並列処理用の通知API呼び出しメソッド\n
            失敗時のログは戻り値のresult内に含める\n
            ループ処理であるためその瞬間に例外を発生させず、呼び出し元で処理結果を判断させる\n
            なお、マルチスレッド処理のため、gは使えない前提\n
            Args:
                message_list: イベントとテンプレートを使って生成したdictのリスト
                notification_destination: 通知先のリスト
                organization_id: オーガナイゼーションID
                workspace_id: ワークスペースID
                user_id: ユーザーID
                language: 言語設定
            Returns:
                result (dict): 処理結果を含む辞書
        """

        host_name = os.environ.get('PLATFORM_API_HOST')
        port = os.environ.get('PLATFORM_API_PORT')

        # 返却用の結果辞書を初期化
        result = {
            "success": 0,
            "failure": 0,
            "failure_info": [],
            "success_notification_count": 0,
            "failure_notification_count": 0
        }

        # HTTP通信用のヘッダー作成
        header_para = {
            "Content-Type": "application/json",
            "User-Id": user_id,
            "Language": language
        }

        # message_listには最大で NOTIFICATION_BATCH_SIZE×PFの通知先設定件数 分のメッセージが入っている
        # 通知先設定IDをキーとして、message_mapにまとめる
        message_map = defaultdict(list)  # PFの通知先設定IDをキーとする、デフォルトには空リストを設定
        default_message = []  # 初期データの1件のメッセージのみだが、他のメッセージと型を同じにした方が楽
        for m in message_list:
            # このmsg_idは通知テンプレートの通知先設定を格納してある
            # このIDはPFの通知先設定IDと一致する
            msg_id = m.get("id")
            # 通知テンプレートの通知先設定はMultiSelectIDカラムなのでリスト or Noneで来るはず
            if isinstance(msg_id, list):
                for i in msg_id:
                    message_map[i].append(m["message"])
            # なのでここの処理に来ないと思うが、単体実行側(__call_notification_api)の処理に揃えておく
            elif msg_id is not None:
                message_map[msg_id].append(m["message"])
            # ▼デフォルトメッセージ定義の処理
            # 通知テンプレートの設定で通知先設定に指定されていない通知先に対してはこのメッセージを使う
            # この関数の呼び出し元(OASE.bulksend)がイベント種別ごとに呼ばれているので、
            # IS_DEFAULT="●"に合致するメッセージは初期データの1件のみ
            # (msg_idはNoneで来るので注意)
            if m.get("IS_DEFAULT") == "●":
                default_message.append(m["message"])

        # 通知先設定毎に送信用のbodyを作成
        # 1つのbodyにまとめた方が効率よい
        request_data = []
        for dest_id in notification_destination:
            message = message_map.get(dest_id, default_message)
            for each_m in message:
                if each_m:
                    notification_data = {
                        **cls._get_data(),
                        "destination_id": dest_id,
                        "message": each_m
                    }
                    request_data.append(notification_data)

        # internal-api経由で通知APIを呼び出す準備
        api_url = f"http://{host_name}:{port}/internal-api/{organization_id}/platform/workspaces/{workspace_id}/notifications"
        json_data = json.dumps(request_data)

        try:
            # APIリクエスト設定
            session = requests.Session()
            retries = Retry(total=5, backoff_factor=1)
            session.mount('http://', HTTPAdapter(max_retries=retries))
            session.mount('https://', HTTPAdapter(max_retries=retries))

            # API呼び出し
            response = session.request(
                method='POST',
                url=api_url,
                timeout=30,  # 並列処理のためタイムアウトを長めに設定
                headers=header_para,
                data=json_data
            )

            # レスポンス処理
            if response.status_code != 200:
                result["failure"] = 1
                result["failure_info"].append(f"API Failed: {response.status_code}")
                result["failure_notification_count"] = len(request_data)
            else:
                result["success"] = 1
                result["success_notification_count"] = len(request_data)

        except Exception as e:
            result["failure"] = 1
            result["failure_info"].append(f"Exception: {str(e)}")
            result["failure_notification_count"] = len(request_data)

        return result

    @classmethod
    def _flush_send_buffer(cls):
        """
        送信バッファに溜まっているデータを送信する
        """
        if len(cls._send_buffer) == 0:
            cls._send_buffer = []
            cls._send_buffer_org_id = None
            cls._send_buffer_ws_id = None
            return

        host_name = os.environ.get('PLATFORM_API_HOST')
        port = os.environ.get('PLATFORM_API_PORT')
        user_id = g.get('USER_ID')
        language = g.get('LANGUAGE')

        header_para = {
            "Content-Type": "application/json",
            "User-Id": user_id,
            "Language": language
        }

        data_encode = json.dumps(cls._send_buffer)

        # API呼出
        api_url = f"http://{host_name}:{port}/internal-api/{cls._send_buffer_org_id}/platform/workspaces/{cls._send_buffer_ws_id}/notifications"

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
            g.applogger.info(g.appmsg.get_log_message("BKY-80026", [data_encode]))
            result["failure"] = 1
            result["failure_info"].append(data_encode)
            result["failure_notification_count"] = len(cls._send_buffer)
        else:
            result["success"] = 1
            result["success_notification_count"] = len(cls._send_buffer)

        g.applogger.debug(g.appmsg.get_log_message("BKY-80018", [result]))

        cls._send_buffer = []
        cls._send_buffer_org_id = None
        cls._send_buffer_ws_id = None

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
