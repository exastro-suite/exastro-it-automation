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

import sqlite3
import json
from flask import g
from common_libs.common.exception import AppException


class sqliteConnect:
    def __init__(self, organization_id, workspace_id):
        db_dir = "/storage/{}/{}/sqlite".format(organization_id, workspace_id)
        self.db_name = f"{db_dir}/ag_oase_{g.AGENT_NAME}"

        # DB接続（作成）
        self.db_connect = sqlite3.connect(self.db_name)

        # DBカーソル作成
        self.db_cursor = self.db_connect.cursor()

    def insert_events(self, events, event_collection_result_list):

        timestamp_info = []
        processed = set()
        try:
            for event in events:
                self.insert_event(event)
                # sent_timestampテーブルにデータを重複して保存しないようにリストを作成
                check_key = (event["_exastro_event_collection_settings_name"], event["_exastro_fetched_time"])
                if check_key not in processed:
                    processed.add(check_key)
                    timestamp_info.append(
                        {
                            "name": event["_exastro_event_collection_settings_name"],
                            "timestamp": event["_exastro_fetched_time"]
                        }
                    )
        except Exception as e:
            g.applogger.info('insert_events error')
            raise AppException("AGT-10027", [e, event])

        try:
            # イベントが1件以上ある場合のみ保存
            for info in timestamp_info:
                self.insert_sent_timestamp(
                    info["name"],
                    info["timestamp"]
                )
            # イベント取得で例外の場合は保存しない。(v2.4~)例外じゃなければ、0件でも保存する
            for data in event_collection_result_list:
                if data["is_save"] is True:
                    self.insert_last_fetched_time(
                        data["name"],
                        data["fetched_time"]
                    )

            self.db_connect.commit()
        except Exception as e:
            g.applogger.info('insert_events error')
            raise AppException("AGT-10027", [e, info])

    def update_sent_flag(self, table_name, timestamp_list):
        try:
            self.db_cursor.execute(
                """
                    UPDATE {}
                    SET sent_flag = {}
                    WHERE rowid IN ({})
                """.format(table_name, 1, ", ".join("?" for id in timestamp_list)),
                timestamp_list
            )
            self.db_connect.commit()
        except Exception as e:
            g.applogger.info('update_sent_flag error')
            raise AppException("AGT-10027", [e, timestamp_list])

    def delete_unnecessary_records(self, dict):
        try:
            for table_name, record_info in dict.items():
                rowid_list = [rowid for rowid in record_info]
                delete_placeholders = ", ".join("?" for _ in rowid_list)
                where_str = f"WHERE (rowid IN ({delete_placeholders}) OR sent_flag=0)"
                self.delete(table_name, where_str, rowid_list)
            self.db_connect.commit()
        except Exception as e:
            g.applogger.info('delete_unnecessary_records error')
            raise AppException("AGT-10027", [e, rowid_list])

    def insert_event(self, event):
        table_name = "events"
        unique_id = None
        self.db_cursor.execute(
            f"""
                CREATE TABLE IF NOT EXISTS {table_name}(
                    event_collection_settings_name TEXT NOT NULL,
                    id TEXT,
                    event TEXT NOT NULL,
                    fetched_time INTEGER NOT NULL,
                    sent_flag BOOLEAN NOT NULL
                )
            """
        )
        # イベントがメールの場合、message_idが必ずあるため、message_idを保存（メール重複取得防止のため）
        if "message_id" in event:
            unique_id = event["message_id"]
        elif "_exastro_oase_event_id" in event:
            unique_id = event["_exastro_oase_event_id"]

        event_string = json.dumps(event)
        self.db_cursor.execute(
            f"INSERT INTO {table_name} (event_collection_settings_name, id, event, fetched_time, sent_flag) VALUES (?, ?, ?, ?, ?)",
            (event["_exastro_event_collection_settings_name"], unique_id, event_string, event["_exastro_fetched_time"], False)
        )

    def insert_sent_timestamp(self, id, fetched_time):
        table_name = "sent_timestamp"
        self.db_cursor.execute(
            f"""
                CREATE TABLE IF NOT EXISTS {table_name}(
                    event_collection_settings_name TEXT NOT NULL,
                    fetched_time INTEGER NOT NULL,
                    sent_flag BOOLEAN NOT NULL
                )
            """
        )
        self.db_cursor.execute(
            f"INSERT INTO {table_name} (event_collection_settings_name, fetched_time, sent_flag) VALUES (?, ?, ?)",
            (id, fetched_time, False)
        )

    def insert_last_fetched_time(self, id, fetched_time):
        table_name = "last_fetched_time"
        self.db_cursor.execute(
            f"""
                CREATE TABLE IF NOT EXISTS {table_name}(
                    event_collection_settings_name TEXT NOT NULL,
                    last_fetched_time INTEGER NOT NULL
                )
            """
        )

        self.db_cursor.execute(f"SELECT * FROM {table_name} WHERE event_collection_settings_name=?", (id, ))
        record_exists = self.db_cursor.fetchone()

        if record_exists is None:
            self.db_cursor.execute(
                f"INSERT INTO {table_name} (event_collection_settings_name, last_fetched_time) VALUES (?, ?)",
                (id, fetched_time)
            )
        else:
            self.db_cursor.execute(
                f"UPDATE {table_name} SET last_fetched_time=? WHERE event_collection_settings_name=?",
                (fetched_time, id)
            )

        self.db_connect.commit()

    def select_all(self, table_name, where_str=None, bind_value=None):
        sql_str = f"SELECT * FROM {table_name}"
        if where_str is not None:
            sql_str = sql_str + " " + where_str

        if bind_value is not None:
            self.db_cursor.execute(sql_str, tuple(bind_value))
        else:
            self.db_cursor.execute(sql_str)

        records = self.db_cursor.fetchall()

        return records

    def delete(self, table_name, where_str=None, bind_value=None):
        sql_str = f"DELETE FROM {table_name}"
        if where_str is not None:
            sql_str = sql_str + " " + where_str

        if bind_value is not None:
            result = self.db_cursor.execute(sql_str, tuple(bind_value))
        else:
            result = self.db_cursor.execute(sql_str)

        return result

    def db_close(self):
        self.db_cursor.close()
        self.db_connect.close()
