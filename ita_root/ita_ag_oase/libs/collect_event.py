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
import sqlite3
from common_libs.oase.get_api_client import get_auth_client
from common_libs.common.exception import AppException
from common_libs.ci.util import app_exception
from common_libs.oase.encrypt import agent_decrypt


######################################################
# イベント収集
######################################################
def collect_event(sqliteDB, event_collection_settings, last_fetched_timestamps=None):
    events = []
    event_collection_settings_enable = []  # イベント収集対象が収集可能な状態かどうか（eventの保存の可否に利用する）
    pass_phrase = g.ORGANIZATION_ID + " " + g.WORKSPACE_ID

    for setting in event_collection_settings:
        setting["LAST_FETCHED_TIMESTAMP"] = last_fetched_timestamps[setting["EVENT_COLLECTION_SETTINGS_NAME"]]
        event_collection_settings_enable_single = {}

        # 重複取得防止のため、event_collection_settings_nameに対応するidリストをDBから取得し、settingsに加える
        try:
            sqliteDB.db_cursor.execute(
                "SELECT id FROM events WHERE event_collection_settings_name=? and id is not null",
                (setting["EVENT_COLLECTION_SETTINGS_NAME"], )
            )
            saved_ids = sqliteDB.db_cursor.fetchall()
            saved_ids = [item[0] for item in saved_ids]
        except sqlite3.OperationalError:  # テーブルがまだ作成されていない時の例外処理
            saved_ids = []
        setting["SAVED_IDS"] = saved_ids

        fetched_time = datetime.datetime.now()  # API取得時間

        # イベント収集設定名とfetched_timeをevent_collection_settings_enable_singleに追加する
        event_collection_settings_enable_single["name"] = setting["EVENT_COLLECTION_SETTINGS_NAME"]
        event_collection_settings_enable_single["fetched_time"] = int(fetched_time.timestamp())
        event_collection_settings_enable_single["is_save"] = True

        # パスワードカラムを複合化しておく
        setting['AUTH_TOKEN'] = agent_decrypt(setting['AUTH_TOKEN'], pass_phrase)
        setting['PASSWORD'] = agent_decrypt(setting['PASSWORD'], pass_phrase)
        setting['SECRET_ACCESS_KEY'] = agent_decrypt(setting['SECRET_ACCESS_KEY'], pass_phrase)

        # APIの呼び出し
        api_client = get_auth_client(setting)  # noqa: F405
        api_parameter = json.loads(setting["PARAMETER"]) if setting["PARAMETER"] else None
        json_data = {}
        try:
            call_api_result, json_data = api_client.call_api(parameter=api_parameter)
        except AppException as e:
            g.applogger.info(g.appmsg.get_log_message("AGT-10001", [setting["EVENT_COLLECTION_SETTINGS_ID"]]))
            app_exception(e)
            event_collection_settings_enable_single["is_save"] = False

        # イベント収集数をevent_collection_settings_enable_singleに追加する
        event_collection_settings_enable_single["len"] = len(json_data)
        event_collection_settings_enable.append(event_collection_settings_enable_single)

        # イベントが0件の場合はスキップ
        if event_collection_settings_enable_single["len"] == 0:
            continue

        # 設定で指定したキーの値を取得
        if call_api_result:
            respons_key_json_data = get_value_from_jsonpath(setting["RESPONSE_KEY"], json_data)
            if respons_key_json_data is None:
                # レスポンスキーが未指定、または間違っている場合、受信したイベントで以降処理する。
                g.applogger.info(g.appmsg.get_log_message("AGT-10002", [setting["RESPONSE_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"]]))
            else:
                # レスポンスキーで取得できた場合、レスポンスキーの値で以降処理する。
                json_data = respons_key_json_data

        # RESPONSE_LIST_FLAGの値がリスト形式ではない場合、そのまま辞書に格納する
        if setting["RESPONSE_LIST_FLAG"] == "0":
            # 値がリスト形式かチェック
            if isinstance(json_data, list) is True:
                g.applogger.info(g.appmsg.get_log_message("AGT-10031", [setting["RESPONSE_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"]]))
                for data in json_data:
                    event = init_label(data, fetched_time, setting)
                    events.append(event)
            else:
                if len(json_data) > 0:
                    event = init_label(json_data, fetched_time, setting)
                    events.append(event)

        # RESPONSE_LIST_FLAの値がリスト形式の場合、1つずつ辞書に格納
        else:
            # 値がリスト形式かチェック
            if isinstance(json_data, list) is False:
                g.applogger.info(g.appmsg.get_log_message("AGT-10003", [setting["RESPONSE_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"]]))
                if len(json_data) > 0:
                    event = init_label(json_data, fetched_time, setting)
                    events.append(event)
            else:
                for data in json_data:
                    event = init_label(data, fetched_time, setting)
                    events.append(event)

    return events, event_collection_settings_enable


def init_label(data, fetched_time, setting):
    event = {}
    event = data
    event["_exastro_event_collection_settings_name"] = setting["EVENT_COLLECTION_SETTINGS_NAME"]
    event["_exastro_event_collection_settings_id"] = setting["EVENT_COLLECTION_SETTINGS_ID"]
    event["_exastro_fetched_time"] = int(fetched_time.timestamp())
    event["_exastro_end_time"] = int((fetched_time + datetime.timedelta(seconds=setting["TTL"])).timestamp())

    return event


# ドット区切りの文字列で辞書を指定して値を取得
def get_value_from_jsonpath(jsonpath=None, data=None):
    if jsonpath is None:
        return data

    value = jmespath.search(jsonpath, data)
    return value
