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

出典: コミット aa7665ed の
  ita_root/ita_by_ansible_legacy_role_vars_listup/backyard_libs/ansible_driver/classes/NestVarsMemberTableClass.py
  の _a_minus_b / _a_and_b / _same_record（多段変数メンバー管理の総当たり突き合わせ）。
メソッド本体は一字も変えていない。クラス名だけ、製品コードの NestVarsMemberTable と取り違えないよう変えている。
冒頭のライセンス表記は写し元のファイルにあるものを、年・書式ともそのまま写している。

経緯: Issue #3072（結果を変えない性能改善の等価性確認）
"""


class LegacyNestVarsMemberCompare:
    """改修前の突き合わせ 3 メソッドを持つだけのクラス（TableBase は継承しない）"""

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

        # ignore_vars_key_idがFalseの場合、VARS_KEY_IDを追加
        if not ignore_vars_key_id:
            keys_to_compare.append('VARS_KEY_ID')

        # すべてのフィールドで値が一致するかチェック
        for field in keys_to_compare:
            if str(record_a.get(field)) != str(record_b.get(field)):
                return False

        return True
