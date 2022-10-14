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


class NestVarsMemberColCombTable(TableBase):
    """
    多次元変数配列組合せ管理のデータを取得し、登録廃止するクラス
    """

    TABLE_NAME = "T_ANSR_NESTVAR_MEMBER_COL_COMB"
    PKEY = "COL_SEQ_COMBINATION_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = NestVarsMemberColCombTable.TABLE_NAME
        self.pkey = NestVarsMemberColCombTable.PKEY

    def register_and_discard(self, nominate_record):
        """
        既存の多段変数配列組み合わせと解析結果の多段変数配列組み合わせを比較し、登録廃止を行う
        """
        g.applogger.debug(f"[Trace] Call {self.__class__.__name__} register_and_discard()")

        nominate_dict = {}
        for rec in nominate_record:
            nominate_dict[(rec['MVMT_VAR_LINK_ID'], rec['ARRAY_MEMBER_ID'], rec['COL_COMBINATION_MEMBER_ALIAS'], rec['COL_SEQ_VALUE'])] = 0

        nominate_keys = nominate_dict.keys()

        stored_records_by_tuple_key = {}
        for stored_item in self._stored_records.values():
            tuple_key = (stored_item['MVMT_VAR_LINK_ID'], stored_item['ARRAY_MEMBER_ID'], stored_item['COL_COMBINATION_MEMBER_ALIAS'], stored_item['COL_SEQ_VALUE'])
            stored_records_by_tuple_key[tuple_key] = stored_item

        stored_keys = stored_records_by_tuple_key.keys()

        user_id = g.get('USER_ID')

        # 登録
        for_register_keys = nominate_keys - stored_keys
        register_list = []
        for item in for_register_keys:
            record = {}
            record['MVMT_VAR_LINK_ID'] = item[0]
            record['ARRAY_MEMBER_ID'] = item[1]
            record['COL_COMBINATION_MEMBER_ALIAS'] = item[2]
            record['COL_SEQ_VALUE'] = item[3]
            record['DISUSE_FLAG'] = '0'
            record['LAST_UPDATE_USER'] = user_id
            register_list.append(record)

        ret = self._ws_db.table_insert(self.table_name, register_list, self.pkey, False)
        if ret is False:
            result_code = "BKY-30003"
            log_msg_args = [self.table_name]
            raise AppException(result_code, log_msg_args)

        # 復活
        for_restore_keys = stored_keys & nominate_keys
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
        for_discard_keys = stored_keys - nominate_keys
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
