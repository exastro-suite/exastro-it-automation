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
import json
from common_libs.event_relay import *


######################################################
# イベント収集
######################################################
def collect_event(wsDb, wsMongo):
    debug_msg = ""

    auth_method = {
        "1": BasicAuthAPIClient,  # noqa: F405
        "2": BearerAuthAPIClient,  # noqa: F405
        "3": SharedKeyLiteAuthAPIClient  # noqa: F405
    }

    def get_auth_client(setting):
        auth_class = auth_method[setting["CONNECTION_METHOD_ID"]]
        return auth_class(setting)

    # ドット区切りの文字列でで辞書を指定して値を取得
    def get_value_from_jsonpath(jsonpath, data):
        value = jmespath.search(jsonpath, data)
        return value

    event_settings = wsDb.table_select(
        "T_EVRL_EVENT_COLLECTION_SETTINGS",
        "WHERE DISUSE_FLAG=0"
    )
    print(event_settings)

    # 生データ保存用コレクション
    event_collection = wsMongo.collection("event_collection")

    for setting in event_settings:
        events = []
        fetched_time = datetime.datetime.now()  # API取得時間

        # APIの呼び出し
        api_client = get_auth_client(setting)
        call_result, json_data = api_client.call_api(json.loads(setting["PARAMETER"]))
        if call_result is False:
            debug_msg = f"failed to fetch api. setting_id: {setting['EVENT_COLLECTION_SETTINGS_ID']}"
            print(debug_msg)
            raise Exception

        # 設定で指定したキーの値を取得
        json_data = get_value_from_jsonpath(setting["RESPONSE_KEY"], json_data)
        if json_data is None:
            debug_msg = f"RESPONSE_KEY does not exist. setting_id: {setting['EVENT_COLLECTION_SETTINGS_ID']}"
            print(debug_msg)
            raise Exception

        # RESPONSE_KEYの値がリスト形式ではない場合、そのまま保存する
        if setting["RESPONSE_LIST_FLAG"] == 0:
            event = json_data
            event["_exastro_event_collection_settings_id"] = setting["EVENT_COLLECTION_SETTINGS_ID"]
            event["_exastro_fetched_time"] = fetched_time.timestamp()
            event["_exastro_end_time"] = (fetched_time + datetime.timedelta(seconds=setting["TTL"])).timestamp()
            event["_exastro_type"] = "event"
            events.append(event)

        # RESPONSE_KEYの値がリスト形式の場合、1つずつ保存
        else:
            # 値がリスト形式かチェック
            if isinstance(json_data, list) is False:
                debug_msg = f"the value of RESPONSE_KEY is not array type. setting_id: {setting['EVENT_COLLECTION_SETTINGS_ID']}"
                print(debug_msg)
                raise Exception
            for data in json_data:
                event = data
                event["_exastro_event_collection_settings_id"] = setting["EVENT_COLLECTION_SETTINGS_ID"]
                event["_exastro_fetched_time"] = fetched_time.timestamp()
                event["_exastro_end_time"] = (fetched_time + datetime.timedelta(seconds=setting["TTL"])).timestamp()
                event["_exastro_type"] = "event"
                events.append(event)

        print(events)
        print(len(events))

        # MongoDBに保存　→　イベントをローカルsqliteに保存
        try:
            res = event_collection.insert_many(events)
            if res.acknowledged is False:
                print("failed to insert fetched events")
        except Exception as e:
            print(e)

        # 取得時間（APIごと）を記録（APIに送信）

        # ラベル設定APIに送信（ローカルから未送信のイベントを取り出して、まとめて送信）

        # ラベル設定APIへの送信が成功したら、ローカルに保存したイベントに、送信済みフラグを立てる

    return True
