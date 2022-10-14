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
from datetime import date, datetime

from common_libs.common.exception import AppException


def json_serial(obj):

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f'Type {obj} not serializable')


class TableBase:
    """
    テーブルのデータを取得し、定義変数を管理するクラス
    """

    def __init__(self, ws_db):
        """
        constructor
        """
        self._ws_db = ws_db
        self._stored_records = {}
        self._table_name = None
        self._pkey = None

    @property
    def table_name(self):
        if self._table_name is None:
            raise AppException("BKY-30001")
        return self._table_name

    @table_name.setter
    def table_name(self, table_name):
        self._table_name = table_name

    @property
    def pkey(self):
        if self._pkey is None:
            raise AppException("BKY-30002")
        return self._pkey

    @pkey.setter
    def pkey(self, pkey):
        self._pkey = pkey

    def store_dbdata_in_memory(self, contain_disused_data=False):
        """
        データベースからデータを取得しメモリに格納する

        Returns:
            is success:(bool)
        """
        g.applogger.debug(f"[Trace] Read Table: {self._table_name}, contain_disused_data: {contain_disused_data}")

        where = ""
        if not contain_disused_data:
            where = "WHERE DISUSE_FLAG = '0'"

        data_list = self._ws_db.table_select(self.table_name, where, [])

        for data in data_list:
            self._stored_records[data[self.pkey]] = data

        return True

    def get_stored_records(self):
        """
        格納データから全レコード(dict)を渡す

        Returns:
            record: [ { COL_NAME: value, ... } ... ]
        """
        return self._stored_records

    def get_stored_record_by_id(self, pkey):
        """
        格納データからID指定でレコードを渡す

        Arguments:
            pkey: (int)

        Returns:
            record: { COL_NAME: value, ... }
        """
        return self._stored_records[pkey]
