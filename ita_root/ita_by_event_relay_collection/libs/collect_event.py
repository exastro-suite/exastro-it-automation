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

from flask import g
import datetime
import jmespath
from common_libs.event_relay import *


######################################################
# イベント収集
######################################################
def collect_event(mariaDB, mongoDB):
    events = []
    debug_msg = ""

    auth_method = {
        "1": BasicAuthAPIClient,  # noqa: F405
        "2": BearerAuthAPIClient,  # noqa: F405
        "3": SharedKeyLiteAuthAPIClient  # noqa: F405
    }

    def get_auth_client(setting):
        auth_class = auth_method[setting["authentication_method_id"]]
        return auth_class(setting)

    # ドット区切りの文字列でで辞書を指定して値を取得
    def get_value_from_jsonpath(jsonpath, data):
        value = jmespath.search(jsonpath, data)
        return value

    # 仮のイベント収集設定
    tmp_header = '{"Content-Type": "application/json"}'
    gathering_event_settings = [
        {
            "event_collection_settings_id": "a1a1a1",
            "gathering_event_name": "Zabbix Host",
            "authentication_method_id": "2",
            "request_method": "POST",
            "api_url": "",
            "header": tmp_header,
            "proxy": None,
            "auth_token": "",
            "username": None,
            "password": None,
            "parameter": {
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {},
                "id": 1
            },
            "RESPONSE_LIST_FLAG": "1",
            "list_key": "result",
            "ttl": 300
        },
        {
            "event_collection_settings_id": "b1b1b1",
            "gathering_event_name": "Zabbix Problem",
            "authentication_method_id": "2",
            "request_method": "POST",
            "api_url": "",
            "header": tmp_header,
            "proxy": None,
            "auth_token": "",
            "username": None,
            "password": None,
            "parameter": {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {},
                "id": 1
            },
            "RESPONSE_LIST_FLAG": "1",
            "list_key": "result",
            "ttl": 300
        }
    ]

    wsMongoDB = mongoDB
    g.applogger.debug("mongodb-ws can connet")

    # 生データ保存用コレクション
    event_collection = wsMongoDB.collection("event_collection")

    for setting in gathering_event_settings:
        try:
            # APIの呼び出し
            api_client = get_auth_client(setting)
            call_result, json_data = api_client.call_api(setting["parameter"])
            fetched_time = datetime.datetime.now()
            if call_result is False:
                debug_msg = f"failed to fetch api. setting_id: {setting['event_collection_settings_id']}"
                print(debug_msg)
                raise Exception

            # 設定で指定したキーの値を取得
            json_data = get_value_from_jsonpath(setting["list_key"], json_data)
            if json_data is None:
                debug_msg = f"RESPONSE_KEY does not exist. setting_id: {setting['event_collection_settings_id']}"
                print(debug_msg)
                raise Exception

            # RESPONSE_KEYの値がリスト形式ではない場合、そのまま保存する
            if setting["RESPONSE_LIST_FLAG"] == 0:
                event = json_data
                event["_exastro_event_collection_settings_id"] = setting["event_collection_settings_id"]
                event["_exastro_fetched_time"] = fetched_time.timestamp()
                event["_exastro_end_time"] = (fetched_time + datetime.timedelta(seconds=setting["ttl"])).timestamp()
                events.append(event)

            # RESPONSE_KEYの値がリスト形式の場合、1つずつ保存
            else:
                # 値がリスト形式かチェック
                if isinstance(json_data, list) is False:
                    debug_msg = f"the value of RESPONSE_KEY is not array type. setting_id: {setting['event_collection_settings_id']}"
                    print(debug_msg)
                    raise Exception
                for data in json_data:
                    event = data
                    event["_exastro_event_collection_settings_id"] = setting["event_collection_settings_id"]
                    event["_exastro_fetched_time"] = fetched_time.timestamp()
                    event["_exastro_end_time"] = (fetched_time + datetime.timedelta(seconds=setting["ttl"])).timestamp()
                    events.append(event)

        except Exception as e:
            # import traceback
            # print(traceback.format_exc())
            print(debug_msg)
            print(e)

    # MongoDBに保存
    try:
        res = event_collection.insert_many(events)
        if res.acknowledged is False:
            print("failed to insert fetched events")
    except Exception as e:
        print(e)

    # print(events)
    # print(len(events))
    return events
