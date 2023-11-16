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
import os
import time
import sqlite3
import datetime
from common_libs.common import *  # noqa F403
from common_libs.ci.util import app_exception, exception
from agent.libs.exastro_api import Exastro_API
from libs.collect_event import collect_event
from libs.sqlite_connect import sqliteConnect
from libs.event_collection_settings import create_file, remove_file, get_settings


def agent_main(organization_id, workspace_id, loop_count, interval):
    count = 1
    max = int(loop_count)

    # ループに入る前にevent_collection_settings.jsonを削除
    setting_removed = remove_file()
    if setting_removed is True:
        g.applogger.debug("Removed JSON file 'event_collection_settings.json'.")
    else:
        g.applogger.debug("No Json file to remove.")

    while True:
        print("")
        print("")
        try:
            collection_logic(organization_id, workspace_id)
        except AppException as e:  # noqa F405
            app_exception(e)
        except Exception as e:
            # catch - other all error
            exception(e)
        time.sleep(interval)
        if count >= max:
            break
        else:
            count = count + 1


def collection_logic(organization_id, workspace_id):

    # 環境変数の取得
    username = os.environ["USERNAME"]
    password = os.environ["PASSWORD"]
    roles = os.environ["ROLES"]
    user_id = os.environ["USER_ID"]
    id_list = os.environ["EVENT_COLLECTION_SETTINGS_IDS"].split(",")
    baseUrl = os.environ["URL"]

    # ITAのAPI呼び出しモジュール
    exastro_api = Exastro_API(
        username,
        password,
        roles,
        user_id
    )

    # SQLiteモジュール
    sqliteDB = sqliteConnect(organization_id, workspace_id)
    g.applogger.debug("Connected to the SQLite database.")

    # イベント収集設定ファイルからイベント収集設定の取得
    settings = get_settings()
    g.applogger.debug("Getting event collection settings from JSON file 'event_collection_settings.json'.")

    # イベント収集設定ファイルが無い場合、ITAから設定を取得 + 設定ファイル作成
    if settings is False:

        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/oase_agent/event_collection/settings"

        g.applogger.info("Getting settings from IT Automation. (Organization ID: {}, Workspace ID: {})".format(organization_id, workspace_id))
        try:
            status_code, response = exastro_api.api_request(
                "POST",
                endpoint,
                {"event_collection_settings_ids": id_list}
            )
            if status_code == 200:
                create_file(response["data"])
                g.applogger.debug("Created the JSON file 'event_collection_settings.json'.")
                settings = get_settings()
            else:
                g.applogger.info("Failed to get event collection settings from Exastro IT Automation.")
                g.applogger.debug(response)
                settings = False
        except AppException as e:  # noqa E405
            # g.applogger.error("Failed to establish a connection with Exastro IT Automation. ({})".format(baseUrl))
            app_exception(e)
            # g.applogger.debug(status_code)
            # g.applogger.debug(response)

    # 最終取得日時
    # current_timestamp = int(datetime.datetime.now().timestamp())
    current_timestamp = 1111111111
    timestamp_data = {}
    timestamp_dict = {key: current_timestamp for key in id_list}
    try:
        # 各設定の最終取得日時を取得
        timestamp_data = {key: value for key, value in sqliteDB.select_all("last_fetched_time")}
        for key, value in timestamp_data.items():
            if key in timestamp_dict:
                timestamp_dict[key] = value
            else:
                timestamp_dict[key] = current_timestamp
    except sqlite3.OperationalError:
        pass

    # イベント収集
    events = []
    if settings is not False:
        g.applogger.info("Collecting events.")
        events = collect_event(sqliteDB, settings, timestamp_dict)
        g.applogger.info(f"Retrived {len(events)} events.")
    else:
        g.applogger.debug("Cannot collect events as no event collection settings exists.")

    # 収集したイベント, 取得時間をSQLiteに保存
    if events != []:
        try:
            sqliteDB.db_connect.execute("BEGIN")
            sqliteDB.insert_events(events)
            g.applogger.debug("Events and fetched time saved to SQLite database.")
        except AppException as e:  # noqa E405
            sqliteDB.db_connect.rollback()
            g.applogger.error("Failed to save events and fetched time to SQLite database.")
            app_exception(e)

    # ITAに送信するデータを取得
    g.applogger.debug("Searching unsent events.")
    post_body = {
        "events": []
    }
    unsent_event_rowids = []  # アップデート用rowidリスト
    unsent_timestamp_rowids = []  # アップデート用rowidリスト
    send_to_ita_flag = False

    # event_collection_settings_idとfetched_timeの組み合わせで辞書を作成
    for id in id_list:
        try:
            sqliteDB.db_cursor.execute(
                "SELECT rowid, event_collection_settings_id, fetched_time FROM sent_timestamp WHERE event_collection_settings_id=? AND sent_flag=?",
                (id, 0)
            )
            unsent_timestamp = sqliteDB.db_cursor.fetchall()
            unsent_timestamp_rowids.extend([row[0] for row in unsent_timestamp])
        except sqlite3.OperationalError:
            continue

        if unsent_timestamp == []:
            continue
        else:
            send_to_ita_flag = True

        # 作成した辞書を使用してイベントを検索
        for item in unsent_timestamp:
            unsent_event = {}
            event_collection_settings_id = item[1]
            fetched_time = item[2]
            unsent_event["fetched_time"] = fetched_time
            unsent_event["event_collection_settings_id"] = event_collection_settings_id
            unsent_event["event"] = []

            sqliteDB.db_cursor.execute(
                "SELECT rowid, event_collection_settings_id, event, fetched_time FROM events WHERE event_collection_settings_id=? AND fetched_time=? AND sent_flag=?",  # noqa E501
                (event_collection_settings_id, fetched_time, 0)
            )
            unsent_events = sqliteDB.db_cursor.fetchall()

            unsent_event["event"].extend([row[2] for row in unsent_events])
            unsent_event_rowids.extend([row[0] for row in unsent_event])
            post_body["events"].append(unsent_event)

    # ITAにデータを送信
    if send_to_ita_flag is True:
        status_code = None
        response = None
        event_count = 0
        for event in post_body["events"]:
            event_count = event_count + len(event["event"])
        g.applogger.info(f"Sending {event_count} events to IT Automation")
        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/oase_agent/events"
        try:
            status_code, response = exastro_api.api_request(
                "POST",
                endpoint,
                post_body
            )
        except AppException as e:  # noqa E405
            app_exception(e)

        # データ送信に成功した場合、sent_flagカラムの値をtrueにアップデート
        if status_code == 200:
            g.applogger.info("Successfully sent events to Exastro IT Automation")
            for table_name, list in {"events": unsent_event_rowids, "sent_timestamp": unsent_timestamp_rowids}.items():
                try:
                    sqliteDB.db_connect.execute("BEGIN")
                    sqliteDB.update_sent_flag(table_name, list)
                except AppException as e:  # noqa E405
                    sqliteDB.db_connect.rollback()
                    sqliteDB.db_close()
                    app_exception(e)

            g.applogger.debug("Updated sent status flag in SQLite database.")
        else:
            g.applogger.info("Failed to send events to IT Automamtion")
            g.applogger.debug(response)
        sqliteDB.db_close()

    else:
        g.applogger.info("No events sent to IT Automation")

    return
