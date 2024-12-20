# Copyright 2022 NEC Corporation#
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

import os
from flask import g
import requests
import json
from urllib.parse import urlparse
import datetime
import time
import copy
import jmespath

from common_libs.common.exception import AppException

class APIClientCommon:
    """
        メールおよびAPI呼び出し用共通クラス
    """
    # 必要項目定義
    def __init__(self, event_settings):
        self.event_collection_settings_id = event_settings["EVENT_COLLECTION_SETTINGS_ID"]
        self.event_collection_settings_name = event_settings["EVENT_COLLECTION_SETTINGS_NAME"]

        self.request_methods = {
            "1": "GET",
            "2": "POST"
        }

        self.request_method = self.request_methods[event_settings["REQUEST_METHOD_ID"]] if event_settings["REQUEST_METHOD_ID"] in ["1", "2"] else None
        self.url = event_settings["URL"]
        self.port = event_settings["PORT"]
        self.headers = json.loads(event_settings["REQUEST_HEADER"]) if event_settings["REQUEST_HEADER"] else None
        parsed_url = urlparse(event_settings["PROXY"]) if event_settings["PROXY"] else None
        self.proxy_host = parsed_url.hostname if parsed_url else None
        self.proxy_port = parsed_url.port if parsed_url else None
        self.auth_token = event_settings["AUTH_TOKEN"]
        self.username = event_settings["USERNAME"]
        self.password = event_settings["PASSWORD"]
        self.access_key_id = event_settings["ACCESS_KEY_ID"]
        self.secret_access_key = event_settings["SECRET_ACCESS_KEY"]
        self.mailbox_name = event_settings["MAILBOXNAME"]
        self.parameter = event_settings["PARAMETER"]
        # 前回イベント収集日時（初回イベント収取時は、システム日時が設定されている）
        self.last_fetched_timestamp = event_settings["LAST_FETCHED_TIMESTAMP"] if event_settings["LAST_FETCHED_TIMESTAMP"] else 0
        self.saved_ids = event_settings["SAVED_IDS"] if "SAVED_IDS" in event_settings else None

        # URLのHOST部が、環境変数NO_PROXYに、存在する場合、verify = Falseに設定
        self.verify = None
        parsed_url = urlparse(event_settings["URL"])
        location_parts = parsed_url.netloc.split(':')
        noproxy_host = location_parts[0]
        no_proxy_large = os.environ['NO_PROXY'] if "NO_PROXY" in os.environ else ""
        no_proxy_small = os.environ['no_proxy'] if "no_proxy" in os.environ else ""
        # SSL 証明書の検証無効(verify = False)の設定
        if no_proxy_large.find(noproxy_host) > -1 or \
           no_proxy_small.find(noproxy_host) > -1:
            # 環境変数NO_PROXYに、接続先のドメインが存在していた場合、
            # プロキシ経由だと、Authorizationヘッダーがプロキシで破棄され、接続出来なくなる
            self.verify = False
        elif self.url.find("https") > -1:
            # 接続先のプロトコルが、HTTSの場合
            # SSL照明書の指定がないため、SSLエラーが発生するため
            self.verify = False

        self.response_list_flag = event_settings["RESPONSE_LIST_FLAG"]
        self.response_key = event_settings["RESPONSE_KEY"]
        self.event_id_key = event_settings["EVENT_ID_KEY"]

        # 重複チェック用イベントIDキー名（イベント直下に格納する項目）
        self.event_id_key_name = '_exastro_oase_event_id'

        g.applogger.debug(g.appmsg.get_log_message("AGT-10042", [self.event_collection_settings_name]))

    def call_api(self, parameter):
        API_response = None
        self.parameter = parameter  # APIのパラメータ
        if self.parameter is not None:
            # パラメータ中の"EXASTRO_LAST_FETCHED_TIME"を前回イベント収集日時（初回はシステム日時）に置換
            last_fetched_time = datetime.datetime.fromtimestamp(self.last_fetched_timestamp)
            last_fetched_ymd = last_fetched_time.strftime('%Y/%m/%d %H:%M:%S')
            last_fetched_dmy = last_fetched_time.strftime('%d/%m/%y %H:%M:%S')
            last_fetched_timestamp = str(int(datetime.datetime.timestamp(last_fetched_time)))

            def replace_reserved_variable(value):
                # 予約語を置換する
                value = value.replace("EXASTRO_LAST_FETCHED_YY_MM_DD", last_fetched_ymd)
                value = value.replace("EXASTRO_LAST_FETCHED_DD_MM_YY", last_fetched_dmy)
                value = value.replace("EXASTRO_LAST_FETCHED_TIMESTAMP", last_fetched_timestamp)
                return value

            def search_reserved_variable(parameter):
                # パラメータの中から再帰的に置換する
                parameter_type = type(parameter)
                if parameter_type is dict:
                    for key, value in parameter.items():
                        value_type = type(value)
                        if value_type is dict:
                            parameter[key] = search_reserved_variable(value)
                        elif value_type is list:
                            parameter[key] = list(map(search_reserved_variable, value))
                        elif value_type is str:
                            parameter[key] = replace_reserved_variable(value)
                    return parameter
                elif parameter_type is list:
                    return list(map(search_reserved_variable, parameter))
                elif parameter_type is str:
                    return replace_reserved_variable(parameter)

            self.parameter = search_reserved_variable(self.parameter)

        try:
            proxies = None
            if self.proxy_host is not None and self.proxy_port is not None:
                proxies = {
                    "http": f"{self.proxy_host}:{self.proxy_port}",
                    "https": f"{self.proxy_host}:{self.proxy_port}"
                }

            # g.applogger.debug("METHOD.............{}".format(self.request_method))
            # g.applogger.debug("URL................{}".format(self.url))
            # g.applogger.debug("AUTH_TOKEN.........{}".format(self.auth_token))
            # g.applogger.debug("verify.............{}".format(self.verify))
            # g.applogger.debug("env.NO_PROXY.......{}".format(os.environ['NO_PROXY']))
            # g.applogger.debug("proxies............{}".format(proxies))
            g.applogger.debug("Request Parameter..........{}".format(parameter))

            # deepcode ignore SSLVerificationBypass: <please specify a reason of ignoring this>
            response = requests.request(
                method=self.request_method,
                url=self.url,
                headers=self.headers,
                params=parameter if self.request_method == "GET" else None,
                data=json.dumps(self.parameter).encode() if self.request_method == "POST" else None,
                verify=self.verify,
                proxies=proxies
            )

            if response.status_code < 200 or response.status_code > 299:
                raise AppException("AGT-10029", ["HTTP STATUS = {}".format(response.status_code)])

            API_response = response.json()

            # g.applogger.debug(g.appmsg.get_log_message("AGT-10043", [API_response]))
            result, response_json = self.get_new_events(API_response)
            # g.applogger.debug(g.appmsg.get_log_message("AGT-10044", [response_json]))

            return result, response_json

        except requests.exceptions.InvalidJSONError:
            g.applogger.info(g.appmsg.get_log_message("AGT-10045", []))
            return False, API_response

        except requests.exceptions.JSONDecodeError:
            g.applogger.info(g.appmsg.get_log_message("AGT-10046", []))
            return False, API_response

        except Exception as e:
            raise AppException("AGT-10029", [e, "HTTP-API Request"])

    # 新規イベント取得
    def get_new_events(self, raw_json):

        # 日時（ミリ秒単位）シリアル値
        now_time = int(time.time() * 1000000)

        result_json = copy.deepcopy(raw_json)

        if self.response_key is not None:
            # 設定で指定したキーの値でレスポンスを取得
            response_key_json = self.get_value_from_jsonpath(self.response_key, result_json)
            if response_key_json is None:
            # レスポンスキーの指定が間違っている場合
            # これ以降でIDを正当につけられないはずなので、この時点でつける
                self.setEventIDforEvent(result_json, now_time)
                return False, result_json
            else:
            # レスポンスキーで取得できた場合
                pass
        else:
            # レスポンスキーが未指定の場合
            response_key_json = result_json

        # RESPONSE_LIST_FLAGの値がリスト形式ではない場合
        # 返却するイベントはオブジェクト
        if self.response_list_flag == "0":
            if isinstance(response_key_json, list) is True:
            # 実際の値はリスト（設定間違い）
                # response_key_jsonが、配列の場合、オブジェクトで返却
                self.setEventIDforEvent(result_json, now_time)
                return False, result_json

            event_flg, event = self.get_elements_new_event(response_key_json)
            if event_flg == True and len(event) > 0:
            # 重複チェックで、未登録イベントの場合、追加
                response_key_json = event
            elif event_flg == False and len(event) > 0:
            # イベントIDキーが未指定、または、間違っている場合、IDに日時シリアルを設定し追加
                event[self.event_id_key_name] = now_time
                response_key_json = event
            else:
            # 重複チェックで、重複したイベントのため、空を返却
                response_key_json.clear()

        # RESPONSE_LIST_FLGの値がリスト形式の場合（分割処理して格納）
        # 返却するイベントは配列
        else:
            new_event_list = []
            if isinstance(response_key_json, list) is False:
            # 実際の値はリストではない（設定間違い）
                self.setEventIDforEvent(result_json, now_time)
                return False, result_json

            for element in response_key_json:
                event_flg, event = self.get_elements_new_event(element)
                if event_flg == True and len(event) > 0:
                # イベントIDキーが指定済みで、重複チェックで、重複なしと判定された場合、追加
                    new_event_list.append(event)
                elif event_flg == False and len(event) > 0:
                # イベントIDキーが未指定、または、間違っている場合、IDに日時シリアルを設定し追加
                    event[self.event_id_key_name] = now_time
                    new_event_list.append(event)
                    now_time += 1
                else:
                # 重複チェックで、重複したイベントのため、追加しない
                    pass

            if len(new_event_list) > 0:
                # 全要素を削除
                for i in reversed(range(len(response_key_json))):
                    del response_key_json[i]
                # 対象イベントを設定
                response_key_json.extend(new_event_list)
            else:
                response_key_json.clear()

        return True, result_json

    # 新規イベント要素作成
    def get_elements_new_event(self, event_json):

        # イベントフラグ
        #   True:新しいイベント、
        #   False:重複イベントか、イベントIDキーが未指定または間違っている
        enevt_flg = False
        new_event = {}

        if self.event_id_key is None:
        # イベントIDキーが未指定
            return False, event_json

        event_id = self.get_value_from_jsonpath(self.event_id_key, event_json)
        if event_id is None:
        # イベントIDキーが取得できない場合
            return False, event_json
        else:
        # 過去のイベントidに存在していない場合
            event_id = str(event_id)
            if event_id not in self.saved_ids:
                enevt_flg = True
                new_event = event_json
                new_event[self.event_id_key_name] = event_id

        return enevt_flg, new_event

    # ドット区切りの文字列で辞書を指定して値を取得
    def get_value_from_jsonpath(self, jsonpath=None, data=None):
        if jsonpath is None:
            return data

        value = jmespath.search(jsonpath, data)
        return value


    def setEventIDforEvent(self, result_json, now_time):
        """イベントにイベントキー
            '_exastro_oase_event_id' : <日時シリアル値>
        """
        if isinstance(result_json, list) is False:
            result_json[self.event_id_key_name] = now_time

        else:
            for event in result_json:
                event[self.event_id_key_name] = now_time
