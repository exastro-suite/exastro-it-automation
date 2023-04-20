# Copyright 2023 NEC Corporation#
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
import sys
import json
import os
import re
from flask import g
from common_libs.common.util import create_dirs, put_uploadfiles, get_timestamp
from importlib import import_module


class Migration:
    """
    Migration

    Attributes:
        resource_dir_path: String
        work_dir_path: String
        db_conn: DBConnectCommon
    """

    def __init__(self, resource_dir_path, work_dir_path, db_conn):
        """
        constructor

        Arguments:
            resource_dir_path: String
            work_dir_path: String
            db_conn: DBConnectCommon
        """
        self._resource_dir_path = resource_dir_path
        self._work_dir_path = work_dir_path
        self._db_conn = db_conn

    def migrate(self):
        """
        migrate
        """
        g.applogger.debug(f"[Trace] work_dir_path:{self._work_dir_path}")

        # DBパッチ
        sql_dir = os.path.join(self._resource_dir_path, "sql")
        if os.path.isdir(sql_dir):
            g.applogger.debug("[Trace] migrate db start")
            self._db_migrate(sql_dir)
        g.applogger.debug("[Trace] migrate db complete")

        # ディレクトリ作成
        config_file_path = os.path.join(self._resource_dir_path, "create_dir_list.txt")
        if os.path.isfile(config_file_path):
            create_dirs(config_file_path, self._work_dir_path)
            # self._create_dir(dir_file)
        g.applogger.debug("[Trace] create dir complete")

        # ファイル配置 (uploadfiles only)
        src_dir = os.path.join(self._resource_dir_path, "file")
        dest_dir = os.path.join(self._work_dir_path, "uploadfiles")
        config_file_path = os.path.join(src_dir, "config.json")
        if os.path.isfile(config_file_path):
            put_uploadfiles(config_file_path, src_dir, dest_dir)
            # self._delivery_files(file_dir)
        g.applogger.debug("[Trace] delivery files complete")

        # 特別処理
        # migrationを呼出す
        src_dir = os.path.join(self._resource_dir_path, "specific")
        config_file_path = os.path.join(src_dir, "config.json")
        if os.path.isfile(config_file_path):
            self._specific_logic(config_file_path, src_dir)

    def _db_migrate(self, sql_dir):
        """
        DB migrate

        Arguments:
            sql_dir: String
        """
        config_file_path = os.path.join(sql_dir, "config.json")
        if not os.path.isfile(config_file_path):
            return True

        with open(config_file_path, "r") as config_str:
            file_list = json.load(config_str)

        last_update_timestamp = str(get_timestamp())
        for sql_files in file_list:

            ddl_file = os.path.join(sql_dir,  sql_files[0])
            dml_file = os.path.join(sql_dir,  sql_files[1])

            if os.path.isfile(ddl_file):
                # DDLファイルの実行
                g.applogger.debug(f"[Trace] EXECUTE SQL FILE=[{ddl_file}]")
                self._db_conn.sqlfile_execute(ddl_file)

            if os.path.isfile(dml_file):

                g.applogger.debug(f"[Trace] EXECUTE SQL FILE=[{dml_file}]")
                self._db_conn.db_transaction_start()
                with open(dml_file, "r") as f:
                    sql_list = f.read().split(";\n")
                    for sql in sql_list:
                        if re.fullmatch(r'[\s\n\r]*', sql):
                            continue

                        sql = sql.replace("_____DATE_____", "STR_TO_DATE('" + last_update_timestamp + "','%Y-%m-%d %H:%i:%s.%f')")

                        # DMLファイルの実行
                        self._db_conn.sql_execute(sql)
                self._db_conn.db_commit()

        return True

    def _specific_logic(self, config_file_path, src_dir):
        """
        execute specific logic (python)
        """
        with open(config_file_path, "r") as config_str:
            file_list = json.load(config_str)

        for src_file in file_list:
            sys.path.append(src_dir)
            migration_module = import_module(src_file)
            result = migration_module.main(self._work_dir_path, self._db_conn)
