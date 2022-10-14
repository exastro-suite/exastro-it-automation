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

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.common.exception import AppException
from .TableBaseClass import TableBase


class NestVarsMemberTable(TableBase):
    """
    多段変数メンバ管理のデータを取得し、登録廃止するクラス
    """

    TABLE_NAME = "T_ANSR_NESTVAR_MEMBER"
    PKEY = "ARRAY_MEMBER_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = NestVarsMemberTable.TABLE_NAME
        self.pkey = NestVarsMemberTable.PKEY

    def register_and_discard(self, mov_vars_dict, mov_vars_link_records):
        """
        既存の多段変数メンバと解析結果の多段変数メンバを比較し、登録廃止を行う
        """
        g.applogger.debug(f"[Trace] Call {self.__class__.__name__} register_and_discard()")

        mov_vars_link_id_dict = {}
        for mov_vars_link_id, record in mov_vars_link_records.items():
            if record['VARS_ATTRIBUTE_01'] != AnscConst.GC_VARS_ATTR_M_ARRAY:
                continue

            mov_vars_link_id_dict[(record['MOVEMENT_ID'], record['VARS_NAME'])] = mov_vars_link_id

        extracted_records = []
        for movement_id, varmng in mov_vars_dict.items():
            mov_vars_list = varmng.export_var_list()
            for mov_vars_item in mov_vars_list:

                if mov_vars_item.var_attr != AnscConst.GC_VARS_ATTR_M_ARRAY:
                    continue

                link_id = mov_vars_link_id_dict[(movement_id, mov_vars_item.var_name)]
                for var_chain_array in mov_vars_item.var_struct['CHAIN_ARRAY']:
                    var_chain_array['MVMT_VAR_LINK_ID'] = link_id
                    extracted_records.append(var_chain_array)

        user_id = g.get('USER_ID')

        # 登録
        register_list = self._a_minus_b(list_a=extracted_records, list_b=self._stored_records.values())
        for record in register_list:
            record.pop('COL_SEQ_MEMBER')
            record['DISUSE_FLAG'] = '0'
            record['LAST_UPDATE_USER'] = user_id

        ret = self._ws_db.table_insert(self.table_name, register_list, self.pkey, False)
        if ret is False:
            result_code = "BKY-30003"
            log_msg_args = [self.table_name]
            raise AppException(result_code, log_msg_args)

        # 復活
        restore_list = self._a_and_b(self._stored_records.values(), extracted_records)
        for record in restore_list:
            if record['DISUSE_FLAG'] == '1':
                record['DISUSE_FLAG'] = '0'
                record['LAST_UPDATE_USER'] = user_id

        ret = self._ws_db.table_update(self.table_name, restore_list, self.pkey, False)
        if ret is False:
            result_code = "BKY-30004"
            log_msg_args = [self.table_name]
            raise AppException(result_code, log_msg_args)

        # 廃止
        discard_list = self._a_minus_b(list_a=self._stored_records.values(), list_b=extracted_records)
        for record in discard_list:
            record['DISUSE_FLAG'] = '1'
            record['LAST_UPDATE_USER'] = user_id

        ret = self._ws_db.table_update(self.table_name, discard_list, self.pkey, False)
        if ret is False:
            result_code = "BKY-30005"
            log_msg_args = [self.table_name]
            raise AppException(result_code, log_msg_args)

        # 再読み込み
        self.store_dbdata_in_memory()

    def _a_minus_b(self, list_a, list_b):

        result_list = []

        for record_a in list_a:
            for record_b in list_b:
                if self._same_record(record_a, record_b):
                    break
            else:
                result_list.append(record_a)

        return result_list

    def _a_and_b(self, list_a, list_b):

        result_list = []

        for record_a in list_a:
            for record_b in list_b:
                if self._same_record(record_a, record_b):
                    result_list.append(record_a)
                    break

        return result_list

    def _same_record(self, record_a, record_b):
        if str(record_a['MVMT_VAR_LINK_ID']) == str(record_b['MVMT_VAR_LINK_ID']) and\
                str(record_a['PARENT_VARS_KEY_ID']) == str(record_b['PARENT_VARS_KEY_ID']) and\
                str(record_a['VARS_KEY_ID']) == str(record_b['VARS_KEY_ID']) and\
                str(record_a['VARS_NAME']) == str(record_b['VARS_NAME']) and\
                str(record_a['ARRAY_NEST_LEVEL']) == str(record_b['ARRAY_NEST_LEVEL']) and\
                str(record_a['ASSIGN_SEQ_NEED']) == str(record_b['ASSIGN_SEQ_NEED']) and\
                str(record_a['COL_SEQ_NEED']) == str(record_b['COL_SEQ_NEED']) and\
                str(record_a['MEMBER_DISP']) == str(record_b['MEMBER_DISP']) and\
                str(record_a['VRAS_NAME_PATH']) == str(record_b['VRAS_NAME_PATH']) and\
                str(record_a['VRAS_NAME_ALIAS']) == str(record_b['VRAS_NAME_ALIAS']) and\
                str(record_a['MAX_COL_SEQ']) == str(record_b['MAX_COL_SEQ']):
            return True

        return False
