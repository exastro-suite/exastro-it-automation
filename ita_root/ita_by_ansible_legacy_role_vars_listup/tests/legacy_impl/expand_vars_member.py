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
"""改修前の実装の写し。比較の基準。原文のまま（内包表記の規約は適用外）

出典: コミット aa7665ed の ita_root/ita_by_ansible_legacy_role_vars_listup/backyard_libs/ansible_driver/ 配下
  - classes/MemberColCombElementClass.py（要素の基底。木を根から掘る has_key_recursive / set_recursive_lower_element を持つ）
  - classes/ExpandableElementClass.py / classes/NonExpandableElementClass.py
  - functions/util.py の expand_vars_member（展開処理＝多段変数メンバー管理の行を親子の木に組み、変数ネスト管理の繰返数で代入欄を作る処理。親探しは根のリストを順に掘る総当たり）
関数・クラスの本体は一字も変えていない。変えたのは、別ファイルだった 4 つを 1 ファイルにまとめたことによる import 行だけ。
冒頭のライセンス表記は写し元の各ファイルにあるものを、年・書式ともそのまま写している。

経緯: Issue #3072（結果を変えない性能改善の等価性確認）
"""
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


class ExpandableElement(MemberColCombElement):
    """
    膨らます要素
    """

    def __init__(self, record_data, expand_times):
        """
        constructor
        """

        super().__init__(record_data)
        self._expand_times = expand_times

    def build(self):
        result_record = []

        # 廃止フラグの立っているものは何も処理しない
        if self.record_data['DISUSE_FLAG'] == "1":
            return result_record

        index = list(range(self._expand_times))
        for seq in index:

            self.mem_col_comb_record = self.create_mem_col_comb_record()
            self.mem_col_comb_record['COL_SEQ_VALUE'] = f"{self.col_seq_value}{seq:08}"
            self.mem_col_comb_record['COL_COMBINATION_MEMBER_ALIAS'] = f"{self.comb_mem_alias}[{seq}]"

            if str(self.record_data['MEMBER_DISP']) == "1":
                result_record.append(self.mem_col_comb_record)

            if self.has_lower():
                for record in self.get_lower_records():
                    result_record.append(record)

        return result_record


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


def expand_vars_member(nest_vars_mem_records, mem_max_col_records):
    """
    メンバ変数を膨らませたレコードリストを作成する

    Arguments:
        nest_vars_mem_records: { pkey: { COL_NAME: value, ... }, ... }
        mem_max_col_records: { pkey: { COL_NAME: value, ... }, ... }

    Returns:
        mov_vars_dict: { (movement_id): VariableManager }
    """
    g.applogger.debug("[Trace] Call util.expand_vars_member()")

    # 変換用辞書作成
    max_col_dict = {}
    for max_col in mem_max_col_records.values():
        key = (max_col['MVMT_VAR_LINK_ID'], max_col['ARRAY_MEMBER_ID'])
        max_col_dict[key] = max_col['MAX_COL_SEQ']

    # 階層の上のモノから処理
    sorted_vars_mem_records = sorted(nest_vars_mem_records.values(), key=lambda x: x['ARRAY_NEST_LEVEL'])

    top_element_list = []
    for vars_mem in sorted_vars_mem_records:

        # 多段変数最大繰返数メニュー反映要素かどうか
        if vars_mem['VARS_NAME'] == '0':
            taple_key = (vars_mem['MVMT_VAR_LINK_ID'], vars_mem['ARRAY_MEMBER_ID'])
            if taple_key in max_col_dict:
                element = ExpandableElement(vars_mem, max_col_dict[taple_key])
            else:
                # 最大繰返数管理TBLに存在しない＝メンバー変数で廃止されている（全レコードの構造を形成するためだけに取得されている）
                element = ExpandableElement(vars_mem, 0)
        else:
            element = NonExpandableElement(vars_mem)

        # 既に親が生成されている場合は紐付け
        parent_key = f"{vars_mem['MVMT_VAR_LINK_ID']}-{vars_mem['PARENT_VARS_KEY_ID']}"
        for top_ele in top_element_list:
            if top_ele.has_key_recursive(parent_key):
                top_ele.set_recursive_lower_element(parent_key, element)
                break
        # 見つからなければTOP要素としてリストに追加
        else:
            top_element_list.append(element)

    nominate_mem_col_comb = []

    for ele_item in top_element_list:
        # print(ele_item)
        mem_col_comb_record_array = ele_item.build()
        for record in mem_col_comb_record_array:
            # print(record)
            nominate_mem_col_comb.append(record)

    return nominate_mem_col_comb
