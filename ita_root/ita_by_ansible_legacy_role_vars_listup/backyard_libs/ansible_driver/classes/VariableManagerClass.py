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


class VariableManager:
    """
    Variable Manager

    Attributes:
        _vars_list: Array(Variable)
            変数リスト
    """

    def __init__(self):
        """
        constructor
        """
        self._vars_list = []

    def add_variable(self, inserted_item, is_option_var=False):
        """
        既存の変数リストに対して、変数を一つ挿入する
        """

        for stored_item in self._vars_list:
            if stored_item.var_name == inserted_item.var_name:

                # 同名があり型が一致しない場合は、既存のリストからも使用不可に変更する
                # オプションによる変数では無い場合。（オプション変数のときは同名があった場合、既存側を優先する）
                if not stored_item.is_same_struct(inserted_item) and not is_option_var:
                    g.applogger.debug(f"Different structures defined for one variable name. \"{stored_item.var_name}\"")
                    stored_item.set_not_use()
                    return False

                # 同名があり型が一致した場合は、そのまま使用する
                return True

        # 同名が無い場合は追加
        self._vars_list.append(inserted_item)

        return True

    def export_var_list(self):
        """
        既存の変数リストを返す
        """
        return self._vars_list

    def merge_variable_list(self, inserted_list, is_option_var=False):
        """
        既存の変数リストと新しい変数リストを統合する
        """

        for item in inserted_list:
            self.add_variable(item, is_option_var)
