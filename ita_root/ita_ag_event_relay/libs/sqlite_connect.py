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


class sqliteConnect:

    def __init__(self, organization_id, workspace_id):

        self.db_name = f"/sqlite/ag_event_relay_{organization_id}_{workspace_id}"

        # DB接続（作成）
        self.db_connect = sqlite3.connect(self.db_name)

        # DBカーソル作成
        self.db_cursor = self.db_connect.cursor()

    def insert_events(self, events):

        for event in events:
            self.insert_event(event)
            self.insert_timestamp(
                event["_exastro_event_collection_settings_id"],
                event["_exastro_fetched_time"]
            )

        self.db_connect.commit()

    def insert_event(self, event):
        table_name = "events"
        self.db_cursor.execute(
            f"""
                CREATE TABLE IF NOT EXISTS {table_name}(
                    event_collection_settings_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    sent_flag BOOLEAN NOT NULL
                )
            """
        )
        event_string = json.dumps(event)
        self.db_cursor.execute(
            f"INSERT INTO {table_name} (event_collection_settings_id, event, sent_flag) VALUES (?, ?, ?)",
            (event["_exastro_event_collection_settings_id"], event_string, False)
        )
        # self.db_connect.commit()

    def insert_timestamp(self, id, fetched_time):
        table_name = "sent_timestamp"
        self.db_cursor.execute(
            f"""
                CREATE TABLE IF NOT EXISTS {table_name}(
                    event_collection_settings_id TEXT NOT NULL,
                    fetched_time INTEGER NOT NULL,
                    sent_flag BOOLEAN NOT NULL
                )
            """
        )
        self.db_cursor.execute(
            f"INSERT INTO {table_name} (event_collection_settings_id, fetched_time, sent_flag) VALUES (?, ?, ?)",
            (id, fetched_time, False)
        )

        # self.db_connect.commit()

    def insert_last_fetched_time(self, id, fetched_time):
        table_name = "last_fetched_time"
        self.db_cursor.execute(
            f"""
                CREATE TABLE IF NOT EXISTS {table_name}(
                    event_collection_settings_id TEXT NOT NULL,
                    last_fetched_time INTEGER NOT NULL
                )
            """
        )

        self.db_cursor.execute(f"SELECT * FROM {table_name} WHERE event_collection_settings_id=?", (id, ))
        record_exists = self.db_cursor.fetchone()

        if record_exists is None:
            self.db_cursor.execute(
                f"INSERT INTO {table_name} (event_collection_settings_id, last_fetched_time) VALUES (?, ?)",
                (id, fetched_time)
            )
        else:
            self.db_cursor.execute(
                f"UPDATE {table_name} SET last_fetched_time=? WHERE event_collection_settings_id=?",
                (fetched_time, id)
            )

        self.db_connect.commit()

    def select_all(self, table_name, where_str=None, bind_value=None):
        sql_str = f"SELECT * FROM {table_name}"
        if where_str is not None:
            sql_str = sql_str + " " + where_str

        if bind_value is not None:
            self.db_cursor.execute(sql_str, tuple(bind_value))
        self.db_cursor.execute(sql_str)

        records = self.db_cursor.fetchall()

        return records

    # def select(self, table_name, column_name, where_str=None, bind_value=None):

    def db_close(self):
        self.db_cursor.close()
        self.db_connect.close()
