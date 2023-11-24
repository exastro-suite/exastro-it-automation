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
    sqliteDB = sqliteConnect(organization_id, workspace_id)

    # ループに入る前にevent_collection_settings.jsonを削除
    setting_removed = remove_file()
    if setting_removed is True:
        g.applogger.debug(g.appmsg.get_log_message("AGT-10004", []))
    else:
        g.applogger.debug(g.appmsg.get_log_message("AGT-10005", []))

    while True:
        print("")
        print("")
        # SQLiteモジュール
        try:
            collection_logic(sqliteDB, organization_id, workspace_id)
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

    # SQLiteファイルの空き容量を解放
    try:
        g.applogger.debug(g.appmsg.get_log_message("AGT-10024", []))
        sqliteDB.db_connect.execute("VACUUM")
        sqliteDB.db_close()
        g.applogger.debug(g.appmsg.get_log_message("AGT-10025", []))
    except Exception:
        g.applogger.error(g.appmsg.get_log_message("AGT-10026", []))


def collection_logic(sqliteDB, organization_id, workspace_id):

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

    g.applogger.debug(g.appmsg.get_log_message("AGT-10006", []))

    # イベント収集設定ファイルからイベント収集設定の取得
    settings = get_settings()
    g.applogger.debug(g.appmsg.get_log_message("AGT-10007", []))

    # イベント収集設定ファイルが無い場合、ITAから設定を取得 + 設定ファイル作成
    if settings is False:

        endpoint = f"{baseUrl}/api/{organization_id}/workspaces/{workspace_id}/oase_agent/event_collection/settings"

        g.applogger.info(g.appmsg.get_log_message("AGT-10008", []))
        try:
            status_code, response = exastro_api.api_request(
                "POST",
                endpoint,
                {"event_collection_settings_ids": id_list}
            )
            if status_code == 200:
                create_file(response["data"])
                g.applogger.debug(g.appmsg.get_log_message("AGT-10009", []))
                settings = get_settings()
            else:
                g.applogger.info(g.appmsg.get_log_message("AGT-10010", []))
                g.applogger.debug(status_code)
                g.applogger.debug(response)
                settings = False
        except AppException as e:  # noqa E405
            app_exception(e)

    # 最終取得日時
    current_timestamp = int(datetime.datetime.now().timestamp())
    timestamp_data = {}
    timestamp_dict = {key: current_timestamp for key in id_list}
    try:
        # 各設定の最終取得日時を取得
        timestamp_data = {key: value for key, value in sqliteDB.select_all("last_fetched_time")}
        for id in id_list:
            if id in timestamp_data:
                timestamp_dict[id] = timestamp_data[id]
            else:
                sqliteDB.insert_last_fetched_time(id, current_timestamp)
                sqliteDB.db_connect.commit()
    except sqlite3.OperationalError:
        for id in id_list:
            sqliteDB.insert_last_fetched_time(id, current_timestamp)
            sqliteDB.db_connect.commit()

    # イベント収集
    events = []
    if settings is not False:
        g.applogger.info(g.appmsg.get_log_message("AGT-10011", []))
        events = collect_event(sqliteDB, settings, timestamp_dict)
        g.applogger.info(g.appmsg.get_log_message("AGT-10012", [len(events)]))
    else:
        g.applogger.debug(g.appmsg.get_log_message("AGT-10013", []))

    # 収集したイベント, 取得時間をSQLiteに保存
    if events != []:
        try:
            sqliteDB.db_connect.execute("BEGIN")
            sqliteDB.insert_events(events)
            g.applogger.debug(g.appmsg.get_log_message("AGT-10014", []))
        except AppException as e:  # noqa E405
            sqliteDB.db_connect.rollback()
            g.applogger.error(g.appmsg.get_log_message("AGT-10015", []))
            app_exception(e)

    # ITAに送信するデータを取得
    g.applogger.debug(g.appmsg.get_log_message("AGT-10016", []))
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
                """
                SELECT rowid, event_collection_settings_id, fetched_time FROM sent_timestamp
                WHERE event_collection_settings_id=? AND sent_flag=?
                """,
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
                """
                SELECT rowid, event_collection_settings_id, event, fetched_time FROM events
                WHERE event_collection_settings_id=? AND fetched_time=? AND sent_flag=?
                """,
                (event_collection_settings_id, fetched_time, 0)
            )
            unsent_events = sqliteDB.db_cursor.fetchall()
            unsent_event["event"].extend([row[2] for row in unsent_events])
            for row in unsent_events:
                unsent_event_rowids.append(row[0])
            post_body["events"].append(unsent_event)

    # ITAにデータを送信
    if send_to_ita_flag is True:
        status_code = None
        response = None
        event_count = 0
        for event in post_body["events"]:
            event_count = event_count + len(event["event"])
        g.applogger.info(g.appmsg.get_log_message("AGT-10017", [event_count]))
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
            g.applogger.info(g.appmsg.get_log_message("AGT-10018", []))
            for table_name, list in {"events": unsent_event_rowids, "sent_timestamp": unsent_timestamp_rowids}.items():
                try:
                    sqliteDB.db_connect.execute("BEGIN")
                    sqliteDB.update_sent_flag(table_name, list)
                except AppException as e:  # noqa E405
                    sqliteDB.db_connect.rollback()
                    sqliteDB.db_close()
                    app_exception(e)

            g.applogger.debug(g.appmsg.get_log_message("AGT-10019", []))
        else:
            g.applogger.info(g.appmsg.get_log_message("AGT-10020", []))
            g.applogger.debug(response)

    else:
        g.applogger.info(g.appmsg.get_log_message("AGT-10021", []))

    # レコードのDELETE
    # 最新のレコードと1ループ前のレコードを残す
    remain_timestamp_dict = {}  # sent_timestampテーブルに残すレコードの{rowid: {id: xxx, fetched_time: nnn}}
    remain_event_rowids = []  # eventsテーブルに残すレコードのrowid
    g.applogger.debug(g.appmsg.get_log_message("AGT-10022", []))
    for id in id_list:
        try:
            sqliteDB.db_cursor.execute(
                """
                SELECT rowid, event_collection_settings_id, fetched_time FROM sent_timestamp
                WHERE event_collection_settings_id=? and sent_flag=1
                ORDER BY fetched_time DESC LIMIT 2
                """,
                (id, )
            )
            remain_timestamp = sqliteDB.db_cursor.fetchall()
        except sqlite3.OperationalError:
            # テーブルが作られていない（イベントが無い）場合、処理を終了
            sqliteDB.db_close()
            return

        if len(remain_timestamp) < 2:
            continue
        for item in remain_timestamp:
            remain_timestamp_dict[item[0]] = {"event_collection_settings_id": item[1], "fetched_time": item[2]}

    # 削除対象イベントが無い場合、削除処理をスキップ
    if len(remain_timestamp_dict) >= 1:
        for rowid, item in remain_timestamp_dict.items():
            sqliteDB.db_cursor.execute(
                """
                SELECT rowid FROM events
                WHERE ((event_collection_settings_id=? AND fetched_time=?) OR sent_flag=0)
                """,
                (item["event_collection_settings_id"], item["fetched_time"])
            )
            remain_event = sqliteDB.db_cursor.fetchall()
            for item in remain_event:
                remain_event_rowids.append(item[0])
        try:
            sqliteDB.db_connect.execute("BEGIN")
            sqliteDB.delete_unnecessary_records({"events": remain_event_rowids, "sent_timestamp": remain_timestamp_dict})
            g.applogger.debug(g.appmsg.get_log_message("AGT-10023", []))
        except AppException as e:  # noqa F405
            app_exception(e)

    return
