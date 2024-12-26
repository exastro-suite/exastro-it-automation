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
import datetime
import time
import sqlite3
import traceback

from common_libs.common import *  # noqa F403
from common_libs.common.util import arrange_stacktrace_format
from common_libs.common.util import get_iso_datetime
from common_libs.common.util import print_exception_msg
from common_libs.ag.util import app_exception, exception
from common_libs.oase.const import oaseConst
from agent.libs.exastro_api import Exastro_API
from libs.collect_event import collect_event
from libs.sqlite_connect import sqliteConnect
from libs.event_collection_settings import set_dir, create_file, remove_file, get_settings


def agent_main(organization_id, workspace_id, loop_count, interval):
    count = 1
    max = int(loop_count)

    # storageにdbの保存場所を作成
    db_dir = "/storage/{}/{}/sqlite".format(organization_id, workspace_id)
    os.makedirs(db_dir, exist_ok=True)
    # tmpに設定の保存場所を作成
    tmp_dir = "/tmp/{}/{}/ag_oase_{}".format(organization_id, workspace_id, g.AGENT_NAME)
    os.makedirs(tmp_dir, exist_ok=True)
    set_dir(tmp_dir)

    # SQLiteモジュール
    sqliteDB = sqliteConnect(organization_id, workspace_id)

    # 環境変数の取得
    base_url = os.environ["EXASTRO_URL"]
    username = os.environ.get("EXASTRO_USERNAME")
    password = os.environ.get("EXASTRO_PASSWORD")
    refresh_token = os.environ.get("EXASTRO_REFRESH_TOKEN")

    # ITAのAPI呼び出しモジュール
    exastro_api = Exastro_API(
        base_url,
        username,
        password,
        refresh_token
    )
    # ITAへの認証がtokenの場合
    if refresh_token is not None:
        exastro_api.get_access_token( organization_id, refresh_token)

    # ループに入る前にevent_collection_settings.jsonを削除
    setting_removed = remove_file()
    if setting_removed is True:
        g.applogger.debug(g.appmsg.get_log_message("AGT-10004", []))
    else:
        g.applogger.debug(g.appmsg.get_log_message("AGT-10005", []))

    while True:
        print("")
        print("")

        try:
            collection_logic(sqliteDB, organization_id, workspace_id, exastro_api)
        except AppException as e:  # noqa F405
            app_exception(e)
        except Exception as e:
            # catch - other all error
            exception(e)

        # インターバルを置いて、max数までループする
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
    except Exception as e:
        t = traceback.format_exc()
        g.applogger.info("[ts={}] {}".format(get_iso_datetime(), arrange_stacktrace_format(t)))
        print_exception_msg(e)
        g.applogger.info(g.appmsg.get_log_message("AGT-10026", []))


def collection_logic(sqliteDB, organization_id, workspace_id, exastro_api):

    setting_name_list = os.environ["EVENT_COLLECTION_SETTINGS_NAMES"].split(",")

    g.applogger.debug(g.appmsg.get_log_message("AGT-10006", []))

    # イベント収集設定ファイルからイベント収集設定の取得
    settings = get_settings()
    nodata = "(no data)" if settings == [] or not settings else ""
    g.applogger.debug(g.appmsg.get_log_message("AGT-10007", [nodata]))

    # イベント収集設定ファイルが無い場合、ITAから設定を取得 + 設定ファイル作成
    if settings is False:
        endpoint = f"/api/{organization_id}/workspaces/{workspace_id}/oase_agent/event_collection/settings"
        g.applogger.info(g.appmsg.get_log_message("AGT-10008", []))
        try:
            status_code, response = exastro_api.api_request(
                "POST",
                endpoint,
                {"event_collection_settings_names": setting_name_list}
            )
            if status_code == 200:
                # CONNECTION_METHOD_ID="99"(エージェント不使用)のものを省く
                setting_list = [i for i in response["data"] if i["CONNECTION_METHOD_ID"] != oaseConst.DF_CON_METHOD_NOT_AGENT]
                create_file(setting_list)
                nodata = "(no data)" if response["data"] == [] else ""
                g.applogger.debug(g.appmsg.get_log_message("AGT-10009", [nodata]))
                settings = get_settings()
            else:
                g.applogger.info(g.appmsg.get_log_message("AGT-10010", [status_code, response]))
                settings = False
        except AppException as e:  # noqa E405
            app_exception(e)

    # 最終取得日時
    current_timestamp = int(datetime.datetime.now().timestamp())
    timestamp_data = {}
    timestamp_dict = {key: current_timestamp for key in setting_name_list}
    try:
        # 各設定の最終取得日時を取得
        timestamp_data = {key: value for key, value in sqliteDB.select_all("last_fetched_time")}
        for name in setting_name_list:
            if name in timestamp_data:
                timestamp_dict[name] = timestamp_data[name]
            else:
                sqliteDB.insert_last_fetched_time(name, current_timestamp)
                sqliteDB.db_connect.commit()
    except sqlite3.OperationalError:
        # 最終取得日時テーブルが存在しない場合、最終取得日時テーブル作成語、再度、登録する
        for name in setting_name_list:
            sqliteDB.insert_last_fetched_time(name, current_timestamp)
            sqliteDB.db_connect.commit()

    # イベント収集
    events = []
    event_collection_result_list = []  # 収集結果のサマリ（最新収集日時の保存の可否に利用する）
    if settings is not False:
        g.applogger.info(g.appmsg.get_log_message("AGT-10011", []))
        events, event_collection_result_list = collect_event(sqliteDB, settings, timestamp_dict)
        g.applogger.info(g.appmsg.get_log_message("AGT-10012", [len(events)]))
    else:
        g.applogger.debug(g.appmsg.get_log_message("AGT-10013", []))

    # 収集したイベント, 取得時間をSQLiteに保存
    if settings is not False:
        try:
            sqliteDB.db_connect.execute("BEGIN")
            sqliteDB.insert_events(events, event_collection_result_list)
            # イベントが1件以上なら、イベントの中身・取得時間・最終取得時間をsqliteに保存する
            if len(events) != 0:
                g.applogger.debug(g.appmsg.get_log_message("AGT-10014", []))
            # イベントが0件なら、最終取得時間をsqliteに保存する
            else:
                g.applogger.debug(g.appmsg.get_log_message("AGT-10032", []))
        except AppException as e:  # noqa E405
            sqliteDB.db_connect.rollback()
            g.applogger.info(g.appmsg.get_log_message("AGT-10015", []))
            app_exception(e)

    # ITAに送信するデータを取得
    g.applogger.debug(g.appmsg.get_log_message("AGT-10016", []))
    post_body = {
        "events": []
    }
    unsent_event_rowids = []  # アップデート用rowidリスト
    unsent_timestamp_rowids = []  # アップデート用rowidリスト
    send_to_ita_flag = False

    # event_collection_settings_nameとfetched_timeの組み合わせで辞書を作成
    # 設定名ごとに未送信の「取得回」を取得
    for name in setting_name_list:
        try:
            sqliteDB.db_cursor.execute(
                """
                SELECT rowid, event_collection_settings_name, fetched_time FROM sent_timestamp
                WHERE event_collection_settings_name=? AND sent_flag=?
                """,
                (name, 0)
            )
            unsent_timestamp = sqliteDB.db_cursor.fetchall()
            unsent_timestamp_rowids.extend([row[0] for row in unsent_timestamp])
        except sqlite3.OperationalError:
            continue

        if unsent_timestamp == []:
            continue
        else:
            send_to_ita_flag = True

        # 作成した辞書を使用して「イベント」をDBから検索
        for item in unsent_timestamp:
            unsent_event = {}
            event_collection_settings_name = item[1]
            fetched_time = item[2]
            unsent_event["fetched_time"] = fetched_time
            unsent_event["event_collection_settings_name"] = event_collection_settings_name
            unsent_event["event"] = []

            sqliteDB.db_cursor.execute(
                """
                SELECT rowid, event_collection_settings_name, event, fetched_time FROM events
                WHERE event_collection_settings_name=? AND fetched_time=? AND sent_flag=?
                """,
                (event_collection_settings_name, fetched_time, 0)
            )
            unsent_events = sqliteDB.db_cursor.fetchall()
            for row in unsent_events:
                unsent_event_rowids.append(row[0])
                # 文字列で保存されていたイベントをJSON形式に再変換
                json_event = json.loads(row[2])
                unsent_event["event"].append(json_event)

            post_body["events"].append(unsent_event)

    # ITAにデータを送信
    if send_to_ita_flag is True:
        status_code = None
        response = None
        event_count = 0
        for event in post_body["events"]:
            event_count = event_count + len(event["event"])
        # "Sending {} events to Exastro IT Automation"
        g.applogger.info(g.appmsg.get_log_message("AGT-10017", [event_count]))
        endpoint = f"/api/{organization_id}/workspaces/{workspace_id}/oase_agent/events"
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
            # "Successfully sent events to Exastro IT Automation."
            g.applogger.info(g.appmsg.get_log_message("AGT-10018", []))
            for table_name, list in {"events": unsent_event_rowids, "sent_timestamp": unsent_timestamp_rowids}.items():
                try:
                    sqliteDB.db_connect.execute("BEGIN")
                    sqliteDB.update_sent_flag(table_name, list)
                except AppException as e:  # noqa E405
                    sqliteDB.db_connect.rollback()
                    app_exception(e)

            g.applogger.debug(g.appmsg.get_log_message("AGT-10019", []))
        else:
            g.applogger.info(g.appmsg.get_log_message("AGT-10020", [status_code, response]))
            g.applogger.info("post_body={}".format(post_body))

    else:
        g.applogger.info(g.appmsg.get_log_message("AGT-10021", []))

    # 不要なレコードのDELETE（1世代前までのイベントは残す）
    g.applogger.debug(g.appmsg.get_log_message("AGT-10022", []))
    to_delete_timestamp_rowids = []  # sent_timestampテーブルから削除するレコードのrowids
    to_delete_events_rowids = []  # eventsテーブルから削除するレコードのrowids
    remain_events_dict = {}  # eventsテーブルに残すレコードの{event_collection_settings_name: [...fetched_time]}

    for name in setting_name_list:
        try:
            # sent_timestampテーブルから送信済みフラグが1のレコードを全件取得
            sqliteDB.db_cursor.execute(
                """
                SELECT rowid, event_collection_settings_name, fetched_time FROM sent_timestamp
                WHERE event_collection_settings_name=? and sent_flag=1
                ORDER BY fetched_time DESC
                """,
                (name, )
            )
            all_records = sqliteDB.db_cursor.fetchall()

            # sent_timestampテーブルでnameあたりのレコードが2世代分以下の場合、処理をスキップ
            if len(all_records) <= 2:
                continue

            remain_events_dict[name] = [all_records[0][2], all_records[1][2]]

            # fetched_timeが最大値とその次の値の（テーブルに残す）レコードを排除したリストを作成
            to_delete_timestamp = all_records[2:]
            # rowidのみを抜き出したリスト
            rowids = [item[0] for item in to_delete_timestamp]
            to_delete_timestamp_rowids.extend(rowids)


        except sqlite3.OperationalError as e:
            # テーブルが作られていない（イベントが無い）場合、処理を終了
            # t = traceback.format_exc()
            # g.applogger.info("[ts={}] {}".format(get_iso_datetime(), arrange_stacktrace_format(t)))
            print_exception_msg(e)
            return

    # 削除対象イベントが無い場合、削除処理をスキップ
    if len(remain_events_dict) >= 1:
        #  eventsテーブルから削除対象のレコードを全件取得（remain_events_dictの情報に一致しないレコード）
        for name, time_list in remain_events_dict.items():
            target_placeholders = ",".join(f"'{time}'" for time in time_list)
            where_str = f"""
                SELECT rowid FROM events
                WHERE event_collection_settings_name = ? AND fetched_time NOT IN ({target_placeholders}) AND sent_flag != ?
            """
            sqliteDB.db_cursor.execute(where_str, (name, 0))
            rowids = sqliteDB.db_cursor.fetchall()
            to_delete_events_rowids.extend([item[0] for item in rowids])
        try:
            sqliteDB.db_connect.execute("BEGIN")
            sqliteDB.delete_unnecessary_records({"events": to_delete_events_rowids, "sent_timestamp": to_delete_timestamp_rowids})
            g.applogger.debug(g.appmsg.get_log_message("AGT-10023", []))
        except AppException as e:  # noqa F405
            app_exception(e)

    return
