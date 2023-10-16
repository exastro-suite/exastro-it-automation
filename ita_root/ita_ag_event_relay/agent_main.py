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
from agent.libs.platform_token import get_access_token
from agent.libs.exastro_api import Exastro_API
from libs.collect_event import collect_event
from libs.sqlite_connect import sqliteConnect
from libs.event_collection_settings import create_file, remove_file, get_settings


def agent_main(organization_id, workspace_id, loop_count):

    interval = int(os.environ.get("INTERVAL"))
    # interval = 5
    count = 1
    max = int(loop_count)

    while True:
        print("")
        print("")
        print("")
        g.applogger.info("loop starts")
        try:
            collection_logic(organization_id, workspace_id)
        except Exception:
            g.applogger.info("")
            import traceback
            traceback.print_exc()

        if count >= max:
            break
        else:
            count = count + 1
            time.sleep(interval)

        g.applogger.info(f"loop count: {count}")

    # ループ終了後に設定ファイルを削除
    remove_file()
    g.applogger.info("remove json file")
    g.applogger.info("loop ends")


def collection_logic(organization_id, workspace_id):

    username = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")
    roles = os.environ.get("ROLES")
    user_id = os.environ.get("USER_ID")

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

    id_list = os.environ.get("EVENT_COLLECTION_SETTINGS_IDS").split(",")

    # イベント収集設定ファイルが無い場合、ITAから設定を取得 + 設定ファイル作成
    if settings is False:
        g.applogger.info("no json file exists")

        baseUrl = os.environ.get("URL")
        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/event_relay_agent/event_collection/settings"

        response = exastro_api.api_request(
            "POST",
            endpoint,
            {
                "event_collection_settings_ids": id_list
            }
        )
        g.applogger.info("getting settings from ita")
        create_file(response["data"])
        g.applogger.info("json file created")
        settings = get_settings()

    # 最終取得日時
    # current_timestamp = int(datetime.datetime.now().timestamp())
    current_timestamp = 1688137200
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
    except Exception as e:
        g.applogger.error(e)

    # イベント収集
    g.applogger.info("getting events")
    events = collect_event(sqliteDB, settings, timestamp_dict)
    g.applogger.info(f"got {len(events)} events")

    # 収集したイベント, 取得時間をSQLiteに保存
    sqliteDB.insert_events(events)
    g.applogger.info("events saved")

    # ITAに送信するデータを取得
    g.applogger.info("searching unsent events")
    post_body = []
    unsent_event_rowids = []  # アップデート用rowidリスト
    unsent_timestamp_rowids = []  # アップデート用rowidリスト
    for id in id_list:
        event_dict = {}
        sqliteDB.db_cursor.execute(
            "SELECT rowid, event FROM events WHERE event_collection_settings_id=? AND sent_flag=?",
            (id, 0)
        )
        unsent_event = sqliteDB.db_cursor.fetchall()
        unsent_event_rowids.extend([row[0] for row in unsent_event])
        sqliteDB.db_cursor.execute(
            "SELECT rowid, fetched_time FROM sent_timestamp WHERE event_collection_settings_id=? AND sent_flag=?",
            (id, 0)
        )
        unsent_timestamp = sqliteDB.db_cursor.fetchall()
        unsent_timestamp_rowids.extend([row[0] for row in unsent_timestamp])

        event_dict["event"] = [row[1] for row in unsent_event]
        event_dict["fetched_time"] = [row[1] for row in unsent_timestamp]
        event_dict["event_collection_settings_id"] = id
        post_body.append(event_dict)

    # ITAにデータを送信
    g.applogger.info("sending events to IT Automation")
    def tmp_post_ita():  # noqa: E306
        return True
    ita_post_result = tmp_post_ita()

    # データ送信に成功した場合、sent_flagカラムをtrueにアップデート
    if ita_post_result is True:
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

    sqliteDB.db_close()

    return
