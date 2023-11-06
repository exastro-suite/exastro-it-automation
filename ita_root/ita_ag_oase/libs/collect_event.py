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

import datetime
import jmespath
import json
from common_libs.event_relay.get_api_client import get_auth_client


######################################################
# イベント収集
######################################################
def collect_event(sqliteDB, event_collection_settings, last_fetched_timestamps=None):
    debug_msg = ""

    # ドット区切りの文字列で辞書を指定して値を取得
    def get_value_from_jsonpath(jsonpath=None, data=None):
        if jsonpath is None:
            return data

        value = jmespath.search(jsonpath, data)
        return value

    events = []
    for setting in event_collection_settings:
        setting["LAST_FETCHED_TIMESTAMP"] = last_fetched_timestamps[setting["EVENT_COLLECTION_SETTINGS_ID"]]
        fetched_time = datetime.datetime.now()  # API取得時間

        # APIの呼び出し
        api_client = get_auth_client(setting)  # noqa: F405
        api_parameter = json.loads(setting["PARAMETER"]) if setting["PARAMETER"] else None
        json_data = api_client.call_api(parameter=api_parameter)

        # 設定で指定したキーの値を取得
        json_data = get_value_from_jsonpath(setting["RESPONSE_KEY"], json_data)
        if json_data is None:
            debug_msg = f"RESPONSE_KEY does not exist. setting_id: {setting['EVENT_COLLECTION_SETTINGS_ID']}"
            print(debug_msg)
            continue

        # RESPONSE_KEYの値がリスト形式ではない場合、そのまま保存する
        if setting["RESPONSE_LIST_FLAG"] == 0:
            event = init_label(json_data, fetched_time, setting)
            events.append(event)

        # RESPONSE_KEYの値がリスト形式の場合、1つずつ保存
        else:
            # 値がリスト形式かチェック
            if isinstance(json_data, list) is False:
                debug_msg = f"the value of RESPONSE_KEY is not array type. setting_id: {setting['EVENT_COLLECTION_SETTINGS_ID']}"
                continue
            for data in json_data:
                event = init_label(data, fetched_time, setting)
                events.append(event)

        # 取得を試みた時間を保存
        sqliteDB.insert_last_fetched_time(
            setting["EVENT_COLLECTION_SETTINGS_ID"],
            int(fetched_time.timestamp())
        )

    return events


def init_label(data, fetched_time, setting):
    event = {}
    event = data
    event["_exastro_event_collection_settings_id"] = setting["EVENT_COLLECTION_SETTINGS_ID"]
    event["_exastro_fetched_time"] = int(fetched_time.timestamp())
    event["_exastro_end_time"] = int((fetched_time + datetime.timedelta(seconds=setting["TTL"])).timestamp())
    event["_exastro_type"] = "event"

    return event
