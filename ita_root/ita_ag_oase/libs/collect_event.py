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
from common_libs.common.exception import AppException
from common_libs.ag.util import app_exception
from common_libs.oase.get_api_client import get_auth_client
from common_libs.oase.encrypt import agent_decrypt


######################################################
# イベント収集
######################################################
def collect_event(sqliteDB, event_collection_settings, last_fetched_timestamps=None):
    events = []
    event_collection_result_list = []  # イベント収集対象の収集結果（最新収集日時の保存の可否に利用する）
    pass_phrase = g.ORGANIZATION_ID + " " + g.WORKSPACE_ID

    for setting in event_collection_settings:
        setting["LAST_FETCHED_TIMESTAMP"] = last_fetched_timestamps[setting["EVENT_COLLECTION_SETTINGS_NAME"]]
        event_collection_result = {}

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

        # イベント収集設定名とfetched_timeを記録しておく（次回の取得日時に利用するためのdbへの保存の可否に利用する）
        event_collection_result["name"] = setting["EVENT_COLLECTION_SETTINGS_NAME"]
        event_collection_result["fetched_time"] = int(fetched_time.timestamp())
        event_collection_result["is_save"] = True

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
            event_collection_result["is_save"] = False

        # 戻り値のevent_collection_result_listに追加しておく
        event_length = 0
        event_collection_result["len"] = event_length
        event_collection_result_list.append(event_collection_result)

        # レスポンスが空の場合はスキップ
        if len(json_data) == 0:
            continue

        if setting["RESPONSE_KEY"]:
            # 設定で指定したキーの値でレスポンスを取得
            response_key_json_data = get_value_from_jsonpath(setting["RESPONSE_KEY"], json_data)
            if response_key_json_data is None:
                # レスポンスキーの指定が間違っている場合、受信したイベントで以降処理する。
                g.applogger.info(g.appmsg.get_log_message("AGT-10002", [setting["RESPONSE_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"]]))
                # 「利用できない」フラグをonにする
                if isinstance(json_data, list) is False:
                    json_data = setNotAvailable(json_data, "RESPONSE_KEY not found")
                else:
                    for event in json_data:
                        event = setNotAvailable(event, "RESPONSE_KEY not found")
            else:
                # レスポンスキーで取得できた場合、レスポンスキーの値で以降処理する。
                json_data = response_key_json_data
        else:
            # レスポンスキーが未指定の場合
            pass

        # RESPONSE_LIST_FLAGの値がリスト形式ではない場合
        if setting["RESPONSE_LIST_FLAG"] == "0":
            # 実際の値はリスト（設定間違い）
            if isinstance(json_data, list) is True:
                g.applogger.info(g.appmsg.get_log_message("AGT-10031", [setting["RESPONSE_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"]]))
                # 「利用できない」フラグをonにする
                for event in json_data:
                    event = setNotAvailable(event, "RESPONSE_LIST_FLAG is incorrect.(Not Dict Type)")
                    event = init_label(event, fetched_time, setting)
                    events.append(event)
                event_length += len(json_data)
            else:
            # 値がオブジェクト
                if len(json_data) > 0:
                    # イベントIDキーがあるかのチェック
                    event = checkEventIdKey(json_data, setting["EVENT_ID_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"])
                    event = init_label(event, fetched_time, setting)
                    event_length += 1
                    events.append(event)

        # RESPONSE_LIST_FLGの値がリスト形式の場合（分割処理して格納）
        else:
            # 実際の値はリストではない（設定間違い）
            if isinstance(json_data, list) is False:
                g.applogger.info(g.appmsg.get_log_message("AGT-10003", [setting["RESPONSE_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"]]))
                # 「利用できない」フラグをonにする
                if len(json_data) > 0:
                    event = setNotAvailable(json_data, "RESPONSE_LIST_FLAG is incorrect.(Not List Type)")
                    event = init_label(event, fetched_time, setting)
                    event_length += 1
                    events.append(event)
            else:
            # 値がリスト
                for event in json_data:
                    # イベントIDキーがあるかのチェック
                    event = checkEventIdKey(event, setting["EVENT_ID_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"])
                    event = init_label(event, fetched_time, setting)
                    events.append(event)
                event_length += len(json_data)

        # イベント収集数を更新しておく
        event_collection_result_list[len(event_collection_result_list)-1]["len"] = event_length
        g.applogger.debug(f'{event_collection_result_list=}')

    return events, event_collection_result_list


def init_label(data, fetched_time, setting):
    event = {}
    event = data
    event["_exastro_event_collection_settings_name"] = setting["EVENT_COLLECTION_SETTINGS_NAME"]
    event["_exastro_event_collection_settings_id"] = setting["EVENT_COLLECTION_SETTINGS_ID"]
    event["_exastro_fetched_time"] = int(fetched_time.timestamp())
    event["_exastro_end_time"] = int((fetched_time + datetime.timedelta(seconds=setting["TTL"])).timestamp())

    return event

def setNotAvailable(event, reason=True):
    """
    設定が間違っていて、本来取り込めないはずのイベントに、フラグをつけておいて取り込めるようにする
    """
    if "_exastro_not_available" not in event:
        event["_exastro_not_available"] = reason

    return event


def checkEventIdKey(event, event_id_key, event_collection_settings_id):
    """
    設定されたイベントIDキーの値でキーが取得できるか確認し、出来なければ「利用できない」フラグをonにする
    """
    event_id = get_value_from_jsonpath(event_id_key, event)
    if event_id is None:
        # イベントIDキーが取得できない場合
        g.applogger.info(g.appmsg.get_log_message("AGT-10030", [event_id_key, event_collection_settings_id]))
        # 「利用できない」フラグをonにする
        event = setNotAvailable(event, "EVENT_ID_KEY not found")

    return event


# ドット区切りの文字列で辞書を指定して値を取得
def get_value_from_jsonpath(jsonpath=None, data=None):
    if jsonpath is None:
        return data

    value = jmespath.search(jsonpath, data)
    return value
