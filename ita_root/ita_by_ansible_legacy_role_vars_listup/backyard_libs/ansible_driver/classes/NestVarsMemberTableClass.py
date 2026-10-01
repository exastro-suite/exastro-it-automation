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

    # レコードの同一性判定に使うカラム（_record_key で使用）
    COMPARE_KEYS = (
        'MVMT_VAR_LINK_ID',
        'VARS_NAME',
        'ARRAY_NEST_LEVEL',
        'ASSIGN_SEQ_NEED',
        'COL_SEQ_NEED',
        'MEMBER_DISP',
        'VRAS_NAME_PATH',
        'VRAS_NAME_ALIAS',
        'MAX_COL_SEQ'
    )

    # ignore_vars_key_id=Falseのときに使う比較カラム
    COMPARE_KEYS_WITH_VARS_KEY_ID = COMPARE_KEYS + ('VARS_KEY_ID',)

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
                    var_chain_array_copy = dict(var_chain_array)
                    var_chain_array_copy['MVMT_VAR_LINK_ID'] = link_id
                    extracted_records.append(var_chain_array_copy)

        user_id = g.get('USER_ID')

        # 同一性判定キーは既存側・解析側それぞれ1回だけ計算し、登録・復活・廃止の3回の突き合わせで使い回す。
        keyed_stored = self._keyed_records(self._stored_records.values())
        keyed_extracted = self._keyed_records(extracted_records)
        stored_by_key = self._index_by_record_key(keyed_stored)
        extracted_by_key = self._index_by_record_key(keyed_extracted)

        # 登録：解析した側にのみ存在する変数を登録
        register_list = self._a_minus_b(keyed_a=keyed_extracted, index_b=stored_by_key)
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
        restore_list = self._a_and_b(keyed_a=keyed_stored, index_b=extracted_by_key, marge_vars_key_id=True)
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
        discard_list = self._a_minus_b(keyed_a=keyed_stored, index_b=extracted_by_key)
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

    def _record_key(self, record, ignore_vars_key_id=True):
        """レコードの同一性判定に使う値をタプルにして返す

        Args:
            record (dict): 対象レコード
            ignore_vars_key_id (bool, optional): VARS_KEY_IDを比較対象に含むか切り替え。Defaults to True.

        Returns:
            tuple:
        """

        keys_to_compare = NestVarsMemberTable.COMPARE_KEYS if ignore_vars_key_id else NestVarsMemberTable.COMPARE_KEYS_WITH_VARS_KEY_ID

        # 既存データと解析結果で型が異なる場合があるため、str()に揃えてから比較する
        key_values = []
        for field in keys_to_compare:
            key_values.append(str(record.get(field)))

        return tuple(key_values)

    def _keyed_records(self, records, ignore_vars_key_id=True):
        """レコードに同一性判定キーを付けたリストを返す

        元の順序・重複・レコードオブジェクトはそのまま保つ（_a_minus_b / _a_and_b の keyed_a 側に使う）。
        キー計算はここで1回だけ行い、以降の突き合わせでは計算し直さない。

        Args:
            records (iterable): 対象レコードの集まり
            ignore_vars_key_id (bool, optional): VARS_KEY_IDを比較対象に含むか切り替え。Defaults to True.

        Returns:
            list: [(同一性判定キー, レコード), ...]
        """

        keyed_records = []
        for record in records:
            keyed_records.append((self._record_key(record, ignore_vars_key_id), record))

        return keyed_records

    def _index_by_record_key(self, keyed_records):
        """キー付きレコードのリストを同一性判定キーで引ける辞書にして返す

        同一キーのレコードが複数ある場合は先に現れたものを採用する。
        修正前の実装が「先頭から線形探索してbreak」だったため、先勝ちでないと結果が変わる。
        （辞書内包表記にすると後勝ちになるのでここはループで書く）

        Args:
            keyed_records (list): _keyed_records() の戻り値

        Returns:
            dict: {同一性判定キー: レコード}
        """

        index = {}
        for key, record in keyed_records:
            index.setdefault(key, record)

        return index

    def _a_minus_b(self, keyed_a, index_b):
        """a側にのみ存在するレコードのリストを返す

        Args:
            keyed_a (list): 比較されるキー付きレコードのリスト（_keyed_records() の戻り値）
            index_b (dict): 比較する側の索引（_index_by_record_key() の戻り値）

        Returns:
            list:
        """

        result_list = []

        for key, record_a in keyed_a:
            if key in index_b:
                continue

            result_list.append(record_a)

        return result_list

    def _a_and_b(self, keyed_a, index_b, marge_vars_key_id=False):
        """a側, b側に共通して存在するレコードのリストを返す

        Args:
            keyed_a (list): 比較されるキー付きレコードのリスト（_keyed_records() の戻り値）
            index_b (dict): 比較する側の索引（_index_by_record_key() の戻り値）
            marge_vars_key_id (bool, optional): record_bのVARS_KEY_IDをrecord_aにマージするか切り替え。Defaults to False.
        Returns:
            list:
        """

        result_list = []

        for key, record_a in keyed_a:
            record_b = index_b.get(key)
            if record_b is None:
                continue

            if marge_vars_key_id:
                record_a["VARS_KEY_ID"] = record_b["VARS_KEY_ID"]
                record_a["PARENT_VARS_KEY_ID"] = record_b["PARENT_VARS_KEY_ID"]
            result_list.append(record_a)

        return result_list
