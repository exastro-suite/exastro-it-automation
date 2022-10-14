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

from common_libs.common.exception import AppException
from .TableBaseClass import TableBase


class RoleNameTable(TableBase):
    """
    ロール名管理のデータを取得し、登録廃止するクラス
    """

    TABLE_NAME = "T_ANSR_ROLE_NAME"
    PKEY = "ROLE_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = RoleNameTable.TABLE_NAME
        self.pkey = RoleNameTable.PKEY

    def register_and_discard(self, analyzed_list):
        """
        既存のロール名と解析結果のロール名を比較し、登録廃止を行う
        """
        g.applogger.debug(f"[Trace] Call {self.__class__.__name__} register_and_discard()")

        analyzed_keys = [(x['ROLE_NAME'], x['ROLE_PACKAGE_ID']) for x in analyzed_list]
        stored_records_by_tuple_key = {}
        for stored_item in self._stored_records.values():
            tuple_key = (stored_item['ROLE_NAME'], stored_item['ROLE_PACKAGE_ID'])
            stored_records_by_tuple_key[tuple_key] = stored_item

        stored_keys = stored_records_by_tuple_key.keys()

        user_id = g.get('USER_ID')

        # 登録
        for_register_keys = analyzed_keys - stored_keys
        register_list = [{'ROLE_NAME': item[0], 'ROLE_PACKAGE_ID': item[1], 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': user_id} for item in for_register_keys]

        ret = self._ws_db.table_insert(self.table_name, register_list, self.pkey, False)
        if ret is False:
            result_code = "BKY-30003"
            log_msg_args = [self.table_name]
            raise AppException(result_code, log_msg_args)

        # 復活
        for_restore_keys = stored_keys & analyzed_keys
        restore_list = []
        for key in for_restore_keys:
            restore_item = stored_records_by_tuple_key[key]
            if restore_item['DISUSE_FLAG'] == '1':
                restore_item['DISUSE_FLAG'] = '0'
                restore_item['LAST_UPDATE_USER'] = user_id
                restore_list.append(restore_item)

        ret = self._ws_db.table_update(self.table_name, restore_list, self.pkey, False)
        if ret is False:
            result_code = "BKY-30004"
            log_msg_args = [self.table_name]
            raise AppException(result_code, log_msg_args)

        # 廃止
        for_discard_keys = stored_keys - analyzed_keys
        discard_list = []
        for key in for_discard_keys:
            discard_item = stored_records_by_tuple_key[key]
            discard_item['DISUSE_FLAG'] = '1'
            discard_item['LAST_UPDATE_USER'] = user_id
            discard_list.append(discard_item)

        ret = self._ws_db.table_update(self.table_name, discard_list, self.pkey, False)
        if ret is False:
            result_code = "BKY-30005"
            log_msg_args = [self.table_name]
            raise AppException(result_code, log_msg_args)

        # 再読み込み
        self.store_dbdata_in_memory()
