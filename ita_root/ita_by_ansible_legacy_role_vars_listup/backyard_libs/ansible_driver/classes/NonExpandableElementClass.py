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

from .MemberColCombElementClass import MemberColCombElement


class NonExpandableElement(MemberColCombElement):
    """
    膨らまない要素
    """

    def __init__(self, record_data):
        """
        constructor
        """

        super().__init__(record_data)

    def build(self):
        result_record = []

        # 廃止フラグの立っているものは何も処理しない
        if self.record_data['DISUSE_FLAG'] == "1":
            return result_record

        self.mem_col_comb_record = self.create_mem_col_comb_record()
        self.mem_col_comb_record['COL_SEQ_VALUE'] = self.col_seq_value
        dot = '' if len(self.comb_mem_alias) == 0 else '.'
        self.mem_col_comb_record['COL_COMBINATION_MEMBER_ALIAS'] = f"{self.comb_mem_alias}{dot}{self.record_data['VARS_NAME']}"

        if str(self.record_data['MEMBER_DISP']) == "1":
            result_record.append(self.mem_col_comb_record)

        if self.has_lower():
            for record in self.get_lower_records():
                result_record.append(record)

        return result_record
