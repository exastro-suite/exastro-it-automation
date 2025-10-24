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
from jinja2 import Template
import datetime
import time
import copy
import traceback
import jmespath

from common_libs.common.exception import AppException

class APIClientCommon:
    """
        メールおよびAPI呼び出し用共通クラス
    """
    # 必要項目定義
    def __init__(self, setting, last_fetched_event):
        self.event_collection_settings_id = setting["EVENT_COLLECTION_SETTINGS_ID"]
        self.event_collection_settings_name = setting["EVENT_COLLECTION_SETTINGS_NAME"]

        self.request_methods = {
            "1": "GET",
            "2": "POST"
        }

        self.request_method = self.request_methods[setting["REQUEST_METHOD_ID"]] if setting["REQUEST_METHOD_ID"] in ["1", "2"] else None

        self.port = setting["PORT"]
        parsed_url = urlparse(setting["PROXY"]) if setting["PROXY"] else None
        self.proxy_host = parsed_url.hostname if parsed_url else None
        self.proxy_port = parsed_url.port if parsed_url else None
        self.auth_token = setting["AUTH_TOKEN"]
        self.username = setting["USERNAME"]
        self.password = setting["PASSWORD"]
        self.access_key_id = setting["ACCESS_KEY_ID"]
        self.secret_access_key = setting["SECRET_ACCESS_KEY"]
        self.mailbox_name = setting["MAILBOXNAME"]
        # 前回イベント収集日時（初回イベント収取時は、システム日時が設定されている）
        self.last_fetched_timestamp = setting["LAST_FETCHED_TIMESTAMP"] if setting["LAST_FETCHED_TIMESTAMP"] else 0
        self.saved_ids = setting["SAVED_IDS"] if "SAVED_IDS" in setting else None
        self.last_fetched_event = last_fetched_event

        self.response_list_flag = setting["RESPONSE_LIST_FLAG"]
        self.response_key = setting["RESPONSE_KEY"]
        self.event_id_key = setting["EVENT_ID_KEY"]

        # 重複チェック用イベントIDキー名（イベント直下に格納する項目）
        self.event_id_key_name = "_exastro_oase_event_id"
        # イベントとして扱えない（非オブジェクト）データをオブジェクト化するときに使うキー名
        self.raw_data_key_name = "_exastro_raw_data"

        # 予約変数の値を保存しておく
        self.last_fetched_time = datetime.datetime.fromtimestamp(self.last_fetched_timestamp)
        self.last_fetched_Ymd = self.last_fetched_time.strftime('%Y/%m/%d %H:%M:%S')
        self.last_fetched_dmy = self.last_fetched_time.strftime('%d/%m/%y %H:%M:%S')
        self.current_time = datetime.datetime.now()

        # 接続先（url）の値をテンプレートとしてレンダリングする
        self.url = self.render("URL", setting["URL"], setting)

        # URLのHOST部が、環境変数NO_PROXYに、存在する場合、verify = Falseに設定
        self.verify = None
        parsed_url = urlparse(self.url)
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

        # リクエストヘッダーの値をテンプレートとしてレンダリングする
        headers = self.render("REQUEST_HEADER", setting["REQUEST_HEADER"], setting)
        try:
            self.headers = json.loads(headers)
        except Exception:
            self.headers = headers

        self.parameter = self.generate_parameter(setting)

        g.applogger.debug(g.appmsg.get_log_message("AGT-10042", [self.event_collection_settings_name]))

    def render(self, column_name, setting_temaplte, setting):
        if not setting_temaplte:
            return setting_temaplte

        try:
            template = Template(str(setting_temaplte))

            res = template.render(
                EXASTRO_LAST_FETCHED_EVENT_IS_EXIST=True if self.last_fetched_event else False,  # （最新）前回取得イベントの存在フラグ
                EXASTRO_LAST_FETCHED_EVENT=self.last_fetched_event,  # （最新）前回取得イベントのオブジェクト
                EXASTRO_EVENT_COLLECTION_SETTING=setting,  # イベント収集設定メニューのレコードのオブジェクト
                EXASTRO_LAST_FETCHED_TIME=self.last_fetched_time,  # 前回取得日時（日時オブジェクト）
                EXASTRO_LAST_FETCHED_TIMESTAMP=self.last_fetched_timestamp,  # 前回取得日時（1704817434）
                EXASTRO_LAST_FETCHED_YY_MM_DD=self.last_fetched_Ymd,  # 前回取得日時（2024/01/10 01:23:45）
                EXASTRO_LAST_FETCHED_DD_MM_YY=self.last_fetched_dmy,  # 前回取得日時（0/01/24 01:23:45）
                EXASTRO_CURRENT_TIME=self.current_time  # 現在時刻（日時オブジェクト）
            )
            return res
        except Exception as e:
            g.applogger.info("TEMPLATE RENDERING ERROR ({}) column_name={} setting_temaplte={} event_collection_settings_id={} last_fetched_event={}".format(e, column_name, setting_temaplte, self.event_collection_settings_id, self.last_fetched_event))
            t = traceback.format_exc()
            g.applogger.debug(t)
            return setting_temaplte

    def generate_parameter(self, setting):
        _parameter = self.render("PARAMETER", setting["PARAMETER"], setting) if setting["PARAMETER"] else None
        try:
            parameter = json.loads(_parameter)
        except Exception:
            parameter = _parameter

        if parameter is not None:
        # 2.7以前の予約変数の置換処理
            def replace_reserved_variable(value):
                # 予約語を置換する
                value = value.replace("EXASTRO_LAST_FETCHED_YY_MM_DD", str(self.last_fetched_Ymd))
                value = value.replace("EXASTRO_LAST_FETCHED_DD_MM_YY", str(self.last_fetched_dmy))
                value = value.replace("EXASTRO_LAST_FETCHED_TIMESTAMP", str(self.last_fetched_timestamp))
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
                        else:
                            parameter[key] = value
                    return parameter
                elif parameter_type is list:
                    return list(map(search_reserved_variable, parameter))
                elif parameter_type is str:
                    return replace_reserved_variable(parameter)
                else:
                    return parameter

            parameter = search_reserved_variable(parameter)

        return parameter

    def call_api(self):
        api_response = None

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
            g.applogger.debug("Request Parameter..........{}".format(self.parameter))

            # deepcode ignore SSLVerificationBypass: <please specify a reason of ignoring this>
            response = requests.request(
                method=self.request_method,
                url=self.url,
                headers=self.headers,
                params=self.parameter if self.request_method == "GET" else None,
                data=json.dumps(self.parameter).encode() if self.request_method == "POST" else None,
                verify=self.verify,
                proxies=proxies,
                timeout=(12, 30)
            )

            if response.status_code < 200 or response.status_code > 299:
                raise AppException("AGT-10029", ["HTTP STATUS = {}".format(response.status_code)])

            api_response = response.json()

            # g.applogger.debug(g.appmsg.get_log_message("AGT-10043", [api_response]))
            # 日時（ミリ秒単位）シリアル値(idに利用)
            now_time = int(time.time() * 1000000)
            response_json = self.get_new_events(api_response, now_time)
            # g.applogger.debug(g.appmsg.get_log_message("AGT-10044", [response_json]))

            return True, response_json

        except requests.exceptions.InvalidJSONError:
            g.applogger.info(g.appmsg.get_log_message("AGT-10045", []))
            return False, api_response

        except requests.exceptions.JSONDecodeError:
            g.applogger.info(g.appmsg.get_log_message("AGT-10046", []))
            return False, api_response

        except Exception as e:
            raise AppException("AGT-10029", [e, "HTTP-API Request"])

    def get_new_events(self, raw_json, now_time):
        """
        apiのレスポンスを、イベントとして扱うために
        内容のチェックや、属性付与を行う
        """

        result_json = copy.deepcopy(raw_json)

        if self.response_key is not None:
            # 設定で指定したキーの値でレスポンスを取得
            response_key_json = self.get_value_from_jsonpath(self.response_key, result_json)
            if response_key_json is None:
            # レスポンスキーの指定が間違っている場合
            # これ以降でIDを正当につけられないはずなので、この時点でつける
                result_json = self.set_event_id_4event(result_json, now_time)
                return result_json
            else:
            # レスポンスキーで取得できた場合
                pass
        else:
            # レスポンスキーが未指定の場合
            response_key_json = result_json

        # 空の場合、そのまま返す
        if (self.response_list_flag != "1" and response_key_json in [{}, ""]) or (self.response_list_flag == "1" and response_key_json == []):
            return result_json

        # response_key_jsonが、空もしくは辞書型でも配列でもない場合（文字列など？）、イベントとして扱えないため、レスポンスキーを付ける前のオブジェクトにIDをつけて返す
        if  isinstance(response_key_json, dict) is False and isinstance(response_key_json, list) is False:
            result_json = self.set_event_id_4event(result_json, now_time)
            return result_json

        # RESPONSE_LIST_FLAGの値がリスト形式ではない場合
        if self.response_list_flag != "1":
            if isinstance(response_key_json, list) is True:
            # 実際の値は辞書ではなくリスト（設定間違い）
                # 元のレスポンスデータに対してIDを付与して返す
                if isinstance(response_key_json, list) is True:
                    # ただし、元のレスポンスデータ自体がリストの場合はオブジェクト化しておく
                    if isinstance(result_json, list) is True:
                        result_json = {
                            self.raw_data_key_name: result_json
                        }
                result_json = self.set_event_id_4event(result_json, now_time)
                return result_json

            new_event_flg, new_event = self.check_new_formatted_event(response_key_json)
            if new_event_flg == True and new_event is not None:
            # 重複チェックで、未登録イベントの場合、追加
                pass
            elif new_event_flg == False and new_event is not None:
            # イベントIDキーが未指定、または、間違っている場合、IDに日時シリアルを設定し追加
                response_key_json[self.event_id_key_name] = str(now_time)
            else:
            # 重複チェックで、重複したイベントのため、空を返却
                response_key_json.clear()

        # RESPONSE_LIST_FLGの値がリスト形式の場合
        else:
            if isinstance(response_key_json, dict) is True:
            # 実際の値はリストではなく辞書（設定間違い）
                self.set_event_id_4event(response_key_json, now_time)
                return result_json

            new_event_list = []
            for element in response_key_json:
                new_event_flg, new_event = self.check_new_formatted_event(element)
                if new_event_flg == True and new_event is not None:
                # イベントIDキーが指定済みで、重複チェックで、重複なしと判定された場合、追加
                    new_event_list.append(new_event)
                elif new_event_flg == False and new_event is not None:
                # イベントIDキーが未指定、または、間違っている場合、IDに日時シリアルを設定し追加
                    new_event[self.event_id_key_name] = str(now_time)
                    new_event_list.append(new_event)
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

        return result_json

    # 新規イベント要素作成
    def check_new_formatted_event(self, event_json):
        """
        新規イベント要素を作成する。

        イベントIDキーを基に、イベントの形式チェックおよび重複チェックを行う。
        新規イベントの場合は内部用のIDプロパティにイベントIDを付与して返却する。

        ※ イベントIDキーがふられなかったイベントに対しては日時シリアルのIDをふるが、それはset_event_id_4eventで対応する。

        Args:
            event_json (dict): イベントデータのJSONオブジェクト。

        Returns:
            tuple:
                - bool: 正しいイベントIDキーが指定されている新規イベントの場合はTrue、重複イベントまたは正しい形式でないイベントの場合はFalse。
                - dict: 重複イベントの場合はNone、それ以外は引数のイベントデータを返す
        """
        if isinstance(event_json, dict) is False:
            event_json = {
                self.raw_data_key_name: event_json
            }
            return False, event_json

        if self.event_id_key is None:
        # イベントIDキーが未指定
            return False, event_json

        event_id = self.get_value_from_jsonpath(self.event_id_key, event_json)
        if event_id is None:
        # イベントIDキーが取得できない場合
            return False, event_json
        else:
            event_id = str(event_id)
            if event_id in self.saved_ids:
                # 過去のイベントidリストに存在している場合は、空オブジェクトを返す
                return False, None

            # 過去のイベントidリストに存在していないので、新規イベントとして扱う
            event_json[self.event_id_key_name] = str(event_id)

            return True, event_json

    # ドット区切りの文字列で辞書を指定して値を取得
    def get_value_from_jsonpath(self, jsonpath=None, data=None):
        if jsonpath is None:
            return data

        value = jmespath.search(jsonpath, data)
        return value

    def set_event_id_4event(self, result_json, now_time):
        """イベントにイベントキーを付与
            '_exastro_oase_event_id' : str(<日時シリアル値>)
        """
        if isinstance(result_json, list) is False and isinstance(result_json, dict) is False:
            result_json = {
                self.raw_data_key_name: result_json,
                self.event_id_key_name: str(now_time)
            }
            return result_json

        if isinstance(result_json, list) is False:
            result_json[self.event_id_key_name] = str(now_time)
        else:
            for event in result_json:
                event[self.event_id_key_name] = str(now_time)
                now_time += 1
        return result_json
