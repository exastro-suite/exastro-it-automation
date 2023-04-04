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
import shutil
import json
import os
from flask import g
from common_libs.common.exception import AppException


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

        # db_migrate
        sql_dir = os.path.join(self._resource_dir_path, "sql")
        if os.path.isdir(sql_dir):
            self._db_migrate(sql_dir)

        # delivery files (uploadfiles only)
        file_dir = os.path.join(self._resource_dir_path, "file")
        if os.path.isdir(file_dir):
            self._delivery_files(file_dir)

        # storage migrate

        # create dir
        dir_file = os.path.join(self._resource_dir_path, "create_dir_list.txt")
        if os.path.isfile(dir_file):
            self._create_dir(dir_file)

        # chmod 755
        chmod_755_file = os.path.join(self._resource_dir_path, "755_list.txt")
        if os.path.isfile(chmod_755_file):
            self._chmod(chmod_755_file, 0o755)

        # chmod 777
        chmod_777_file = os.path.join(self._resource_dir_path, "755_list.txt")
        if os.path.isfile(chmod_777_file):
            self._chmod(chmod_777_file, 0o777)

        # self._specific_logic()

    def _db_migrate(self, sql_dir):
        """
        DB migrate

        Arguments:
            sql_dir: String
        """

        with open(os.path.join(sql_dir, "config.json"), "r") as config_str:
            file_list = json.load(config_str)

        for sql_file in file_list:
            self._db_conn.sqlfile_execute(os.path.join(sql_dir, sql_file))

    def _delivery_files(self, file_dir):
        """
        Delivery files

        Arguments:
            file_dir: String
        """

        with open(os.path.join(file_dir, "config.json"), "r") as config_str:
            config_json = json.load(config_str)

        for menu_id, resource_dict in config_json.items():
            menu_dir = os.path.join(file_dir, menu_id)
            if not os.isdir(menu_dir):
                raise AppException("499-00701", [f"No such directory. resource:{menu_dir}"])  # TODO: Message番号を新規で作ること

            for item, dest_path_list in resource_dict.items():
                item_path = os.path.join(file_dir, menu_id, item)
                if not os.isfile(item_path):
                    raise AppException("499-00701", [f"No such file. resource:{item_path}"])  # TODO: Message番号を新規で作ること

                for dst_dir in dest_path_list:
                    # 現在はuploadfilesのみに対応
                    # TODO: 2系は履歴TBLに実ファイル、更新TBLにはシンボリックリンクだけどそこの対応はどうするか
                    shutil.copy(item_path, os.path.join(self._work_dir_path, "uploadfiles", menu_id, dst_dir))

    def _create_dir(self, file_path):
        """
        Storage file migrate
            (create dir)

        Arguments:
            file_path: String
        """

        with open(file_path) as f:
            lines = f.readlines()

        for target_path in lines:
            os.makedirs(target_path)

    def _chmod(self, file_path, mode):
        """
        Storage file migrate
            (chmod)

        Arguments:
            file_path: str
            mode: int (0o755 or 0o777)
        """

        with open(file_path) as f:
            lines = f.readlines()

        for target_path in lines:
            if os.path.exists(target_path):
                os.chmod(target_path, mode)

    # def _specific_logic(self):
    #     """
    #     execute specific logic (python)
    #     """

    #     # TODO: 新規で何かを実行しなければならないものは発生しないか？
