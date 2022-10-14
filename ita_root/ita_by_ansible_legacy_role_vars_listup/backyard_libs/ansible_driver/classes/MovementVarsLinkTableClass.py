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


class MovementVarsLinkTable(TableBase):
    """
    Movement変数管理のデータを取得し、登録廃止するクラス
    """

    TABLE_NAME = "T_ANSR_MVMT_VAR_LINK"
    PKEY = "MVMT_VAR_LINK_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = MovementVarsLinkTable.TABLE_NAME
        self.pkey = MovementVarsLinkTable.PKEY

    def register_and_discard(self, mov_vars_dict):
        """
        既存のMovement変数と解析結果のMovement変数を比較し、登録廃止を行う
        """
        g.applogger.debug(f"[Trace] Call {self.__class__.__name__} register_and_discard()")

        extracted_records_by_tuple_key = {}
        for movement_id, varmng in mov_vars_dict.items():
            mov_vars_list = varmng.export_var_list()
            for mov_vars_item in mov_vars_list:
                tuple_key = (movement_id, mov_vars_item.var_name)
                extracted_records_by_tuple_key[tuple_key] = mov_vars_item

        extracted_keys = extracted_records_by_tuple_key.keys()

        stored_records_by_tuple_key = {}
        for stored_item in self._stored_records.values():
            tuple_key = (stored_item['MOVEMENT_ID'], stored_item['VARS_NAME'])
            stored_records_by_tuple_key[tuple_key] = stored_item

        stored_keys = stored_records_by_tuple_key.keys()

        user_id = g.get('USER_ID')

        # 登録
        for_register_keys = extracted_keys - stored_keys
        register_list = []
        for key in for_register_keys:
            var_item = extracted_records_by_tuple_key[key]
            register_list.append({
                'MOVEMENT_ID': key[0],
                'VARS_NAME': var_item.var_name,
                'VARS_ATTRIBUTE_01': var_item.var_attr,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_USER': user_id
            })

        ret = self._ws_db.table_insert(self.table_name, register_list, self.pkey, False)
        if ret is False:
            result_code = "BKY-30003"
            log_msg_args = [self.table_name]
            raise AppException(result_code, log_msg_args)

        # 復活
        for_restore_keys = stored_keys & extracted_keys
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
        for_discard_keys = stored_keys - extracted_keys
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
