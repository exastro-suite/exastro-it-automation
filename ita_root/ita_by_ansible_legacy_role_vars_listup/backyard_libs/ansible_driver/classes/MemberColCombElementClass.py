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
from abc import ABCMeta, abstractmethod
from flask import g


class MemberColCombElement(metaclass=ABCMeta):
    """
    多次元変数メンバー管理から生成する要素オブジェクト

    ->buildした結果、多次元変数配列組合せ管理のレコード(候補)を吐き出す
      ※吐き出したレコード一覧と実際にINSERTするかを比較する処理は別
    """

    def __init__(self, record_data):
        """
        constructor
        """

        self.lower_level_elements = []
        self.record_data = record_data
        self.own_key = f"{record_data['MVMT_VAR_LINK_ID']}-{record_data['VARS_KEY_ID']}"
        self.col_seq_value = ""
        self.comb_mem_alias = ""
        self.mem_col_comb_record = {}

    @abstractmethod
    def build(self) -> dict:
        raise NotImplementedError()

    def set_lower_element(self, element):
        self.lower_level_elements.append(element)

    def has_lower(self):
        return len(self.lower_level_elements) > 0

    def set_col_seq_value(self, col_seq_value):
        self.col_seq_value = col_seq_value

    def set_comb_mem_alias(self, comb_mem_alias):
        self.comb_mem_alias = comb_mem_alias

    def get_lower_records(self):

        result_records = []

        for lower in self.lower_level_elements:
            lower.set_col_seq_value(self.mem_col_comb_record['COL_SEQ_VALUE'])
            lower.set_comb_mem_alias(self.mem_col_comb_record['COL_COMBINATION_MEMBER_ALIAS'])

            records = lower.build()
            for record in records:
                result_records.append(record)

        return result_records

    def create_mem_col_comb_record(self):

        columns = [
            'COL_SEQ_COMBINATION_ID',
            'MVMT_VAR_LINK_ID',
            'ARRAY_MEMBER_ID',
            'COL_COMBINATION_MEMBER_ALIAS',
            'COL_SEQ_VALUE'
        ]

        result = {}
        for column in columns:
            result[column] = self.record_data[column] if column in self.record_data else None

        return result

    def has_key_recursive(self, parent_key):

        if self.own_key == parent_key:
            return True

        for element in self.lower_level_elements:
            if element.has_key_recursive(parent_key):
                return True

        return False

    def set_recursive_lower_element(self, parent_key, element):

        if self.own_key == parent_key:
            self.set_lower_element(element)
            return True
        else:
            for low_ele in self.lower_level_elements:
                if low_ele.set_recursive_lower_element(parent_key, element):
                    return True

        return False
