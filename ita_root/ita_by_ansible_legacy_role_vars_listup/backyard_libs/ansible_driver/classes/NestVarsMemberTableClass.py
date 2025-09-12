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
import copy

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
                    var_chain_array_copy = copy.deepcopy(var_chain_array)
                    var_chain_array_copy['MVMT_VAR_LINK_ID'] = link_id
                    extracted_records.append(var_chain_array_copy)

        user_id = g.get('USER_ID')

        # 登録：解析した側にのみ存在する変数を登録
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

        # 更新：共通の変数だが、定義されている順番（VARS_KEY_ID）が異なる場合、解析した側に更新
        # 復活：両者に共通する変数が廃止されている場合は復活
        restore_list = self._a_and_b(self._stored_records.values(), extracted_records, marge_vars_key_id=True)
        for record in restore_list:
            if record['DISUSE_FLAG'] == '1':
                record['DISUSE_FLAG'] = '0'
                record['LAST_UPDATE_USER'] = user_id

        ret = self._ws_db.table_update(self.table_name, restore_list, self.pkey, False)
        if ret is False:
            result_code = "BKY-30004"
            log_msg_args = [self.table_name]
            raise AppException(result_code, log_msg_args)

        # 廃止：既存側にのみ存在する変数を廃止
        discard_list = self._a_minus_b(list_a=self._stored_records.values(), list_b=extracted_records)
        for record in discard_list:
            if record['DISUSE_FLAG'] == '0':
                record['DISUSE_FLAG'] = '1'
                record['LAST_UPDATE_USER'] = user_id

        ret = self._ws_db.table_update(self.table_name, discard_list, self.pkey, False)
        if ret is False:
            result_code = "BKY-30005"
            log_msg_args = [self.table_name]
            raise AppException(result_code, log_msg_args)

        # 再読み込み
        self.store_dbdata_in_memory()

    def _a_minus_b(self, list_a, list_b, ignore_vars_key_id=True):
        """list aにのみ存在するレコードのリストを返す

        Args:
            list_a (list): 比較されるリスト
            list_b (list): 比較するリスト
            ignore_vars_key_id (bool, optional): VARS_KEY_IDを比較対象に含むか切り替え。 Defaults to False.

        Returns:
            list:
        """

        result_list = []

        for record_a in list_a:
            for record_b in list_b:
                if self._same_record(record_a, record_b, ignore_vars_key_id):
                    break
            else:
                result_list.append(record_a)

        return result_list

    def _a_and_b(self, list_a, list_b, ignore_vars_key_id=True, marge_vars_key_id=False):
        """list_a, list_bに共通して存在するレコードのリストを返す

        Args:
            list_a (list): 比較されるリスト
            list_b (list): 比較するリスト
            ignore_vars_key_id (bool, optional): VARS_KEY_IDを比較対象に含むか切り替え。Defaults to True.
            marge_vars_key_id (bool, optional): record_bのVARS_KEY_IDをrecord_aにマージするか切り替え。Defaults to False.
        Returns:
            list:
        """

        result_list = []

        for record_a in list_a:
            for record_b in list_b:
                if self._same_record(record_a, record_b, ignore_vars_key_id):
                    if marge_vars_key_id:
                        record_a["VARS_KEY_ID"] = record_b["VARS_KEY_ID"]
                    result_list.append(record_a)
                    break

        return result_list

    def _same_record(self, record_a, record_b, ignore_vars_key_id=True):

        # 共通の比較条件をリストで定義
        keys_to_compare = [
            'MVMT_VAR_LINK_ID',
            'PARENT_VARS_KEY_ID',
            'VARS_NAME',
            'ARRAY_NEST_LEVEL',
            'ASSIGN_SEQ_NEED',
            'COL_SEQ_NEED',
            'MEMBER_DISP',
            'VRAS_NAME_PATH',
            'VRAS_NAME_ALIAS',
            'MAX_COL_SEQ'
        ]

        # ignore_vars_key_idがTrueの場合、VARS_KEY_IDを追加
        if not ignore_vars_key_id:
            keys_to_compare.append('VARS_KEY_ID')

        # すべてのフィールドで値が一致するかチェック
        for field in keys_to_compare:
            if str(record_a.get(field)) != str(record_b.get(field)):
                return False

        return True
