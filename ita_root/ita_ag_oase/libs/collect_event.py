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
from common_libs.oase.get_api_client import get_auth_client
from common_libs.common.exception import AppException
from common_libs.ci.util import app_exception
from common_libs.oase.encrypt import agent_decrypt


######################################################
# イベント収集
######################################################
def collect_event(sqliteDB, event_collection_settings, last_fetched_timestamps=None):
    events = []
    pass_phrase = g.ORGANIZATION_ID + " " + g.WORKSPACE_ID

    for setting in event_collection_settings:
        setting["LAST_FETCHED_TIMESTAMP"] = last_fetched_timestamps[setting["EVENT_COLLECTION_SETTINGS_ID"]]
        fetched_time = datetime.datetime.now()  # API取得時間

        # パスワードカラムを複合化しておく
        setting['AUTH_TOKEN'] = agent_decrypt(setting['AUTH_TOKEN'], pass_phrase)
        setting['PASSWORD'] = agent_decrypt(setting['PASSWORD'], pass_phrase)
        setting['SECRET_ACCESS_KEY'] = agent_decrypt(setting['SECRET_ACCESS_KEY'], pass_phrase)

        # APIの呼び出し
        api_client = get_auth_client(setting)  # noqa: F405
        api_parameter = json.loads(setting["PARAMETER"]) if setting["PARAMETER"] else None
        json_data = {}
        try:
            json_data = api_client.call_api(parameter=api_parameter)
        except AppException as e:
            g.applogger.info(g.appmsg.get_log_message("AGT-10001", [setting["EVENT_COLLECTION_SETTINGS_ID"]]))
            app_exception(e)

        # イベントが0件の場合はスキップ
        if json_data in [{}, []]:
            continue

        # 設定で指定したキーの値を取得
        json_data = get_value_from_jsonpath(setting["RESPONSE_KEY"], json_data)
        if json_data is None:
            g.applogger.info(g.appmsg.get_log_message("AGT-10002", [setting["RESPONSE_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"]]))
            continue

        # RESPONSE_KEYの値がリスト形式ではない場合、そのまま辞書に格納する
        if setting["RESPONSE_LIST_FLAG"] == 0:
            event = init_label(json_data, fetched_time, setting)
            events.append(event)

        # RESPONSE_KEYの値がリスト形式の場合、1つずつ辞書に格納
        else:
            # 値がリスト形式かチェック
            if isinstance(json_data, list) is False:
                g.applogger.info(g.appmsg.get_log_message("AGT-10003", [setting["RESPONSE_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"]]))
                continue
            for data in json_data:
                event = init_label(data, fetched_time, setting)
                events.append(event)

    return events


def init_label(data, fetched_time, setting):
    event = {}
    event = data
    event["_exastro_event_collection_settings_id"] = setting["EVENT_COLLECTION_SETTINGS_ID"]
    event["_exastro_fetched_time"] = int(fetched_time.timestamp())
    event["_exastro_end_time"] = int((fetched_time + datetime.timedelta(seconds=setting["TTL"])).timestamp())
    event["_exastro_type"] = "event"

    return event


# ドット区切りの文字列で辞書を指定して値を取得
def get_value_from_jsonpath(jsonpath=None, data=None):
    if jsonpath is None:
        return data

    value = jmespath.search(jsonpath, data)
    return value
