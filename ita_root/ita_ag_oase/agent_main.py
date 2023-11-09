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
from common_libs.common.exception import AppException
from common_libs.ci.util import app_exception, exception
from agent.libs.exastro_api import Exastro_API
from libs.collect_event import collect_event
from libs.sqlite_connect import sqliteConnect
from libs.event_collection_settings import create_file, remove_file, get_settings


def agent_main(organization_id, workspace_id, loop_count, interval):
    count = 1
    max = int(loop_count)

    g.applogger.info("loop starts")
    while True:
        print("")
        print("")
        try:
            collection_logic(organization_id, workspace_id)
            g.applogger.info(f"loop count: {count}")
        except AppException as e:
            app_exception(e)
        except Exception as e:
            # catch - other all error
            exception(e)

        time.sleep(interval)
        if count >= max:
            g.applogger.info("loop ends")
            break
        else:
            count = count + 1

    # ループ終了後に設定ファイルを削除
    remove_file()
    g.applogger.info("json file removed")


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
    g.applogger.info("sqlite connected")

    # イベント収集設定ファイルからイベント収集設定の取得
    settings = get_settings()
    g.applogger.info("getting settings from json file")

    # イベント収集設定ファイルが無い場合、ITAから設定を取得 + 設定ファイル作成
    if settings is False:
        g.applogger.info("no json file exists")

        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/oase_agent/event_collection/settings"

        status_code, response = exastro_api.api_request(
            "POST",
            endpoint,
            {
                "event_collection_settings_ids": id_list
            }
        )
        g.applogger.info("getting settings from ita")
        # g.applogger.debug(status_code)
        # g.applogger.debug(response)
        create_file(response["data"])
        g.applogger.info("json file created")
        settings = get_settings()

    # 最終取得日時
    current_timestamp = int(datetime.datetime.now().timestamp())
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
    g.applogger.info("getting events")
    events = collect_event(sqliteDB, settings, timestamp_dict)
    g.applogger.info(f"got {len(events)} events")

    # 収集したイベント, 取得時間をSQLiteに保存
    if events != []:
        sqliteDB.insert_events(events)
        g.applogger.info("events saved")

    # ITAに送信するデータを取得
    g.applogger.info("searching unsent events")
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
        g.applogger.info("sending events to IT Automation")
        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/oase_agent/events"
        status_code, response = exastro_api.api_request(
            "POST",
            endpoint,
            post_body
        )

        # データ送信に成功した場合、sent_flagカラムの値をtrueにアップデート
        if status_code == 200:
            g.applogger.info("events sent to ITA")
            for table_name, list in {"events": unsent_event_rowids, "sent_timestamp": unsent_timestamp_rowids}.items():
                sqliteDB.db_cursor.execute(
                    """
                        UPDATE {}
                        SET sent_flag = {}
                        WHERE rowid IN ({})
                    """.format(table_name, 1, ", ".join("?" for id in list)),
                    list
                )
                sqliteDB.db_connect.commit()
            g.applogger.info("sent flag updated")
        sqliteDB.db_close()

    else:
        g.applogger.info("No events sent to ITA")

    return
