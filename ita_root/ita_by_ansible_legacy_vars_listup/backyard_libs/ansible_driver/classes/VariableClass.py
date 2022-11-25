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

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.CheckAnsibleRoleFiles import DefaultVarsFileAnalysis


class Variable:
    """
    Variable

    Attributes:
        _var_name: String
            変数名
        _var_attr: String
            変数属性（一般変数: 1 / 複数具体値変数: 2 / 多次元変数: 3）
        _var_struct: Dictionary
            変数構造（多次元変数のみ）
        _is_active: bool
            使用可/不可判定
    """

    def __init__(self, var_name, var_attr, var_struct=None):
        """
        constructor

        Arguments:
            var_name: String
                変数名
            var_attr: String
                変数属性（一般変数: 1 / 複数具体値変数: 2 / 多次元変数: 3）
            var_struct: Dictionary
                変数構造（多次元変数のみ）
        """
        self._var_name = var_name
        self._var_attr = var_attr
        self._var_struct = var_struct
        self._is_active = True

    def __str__(self):
        return f"name: {self.var_name}, is_active: {self._is_active}, attr: {self._var_attr}, struct: {self._var_struct}"

    @property
    def var_name(self):
        """
        変数名を返す

        Returns:
            self._var_name: String
                変数名
        """
        return self._var_name

    @property
    def var_attr(self):
        """
        変数属性（一般変数 / 複数具体値変数 / 多次元変数）を返す

        Returns:
            self._var_attr: String
                変数属性（一般変数 / 複数具体値変数 / 多次元変数）
        """
        return self._var_attr

    @property
    def var_struct(self):
        """
        変数構造を返す

        Returns:
            self._var_struct: String
                変数構造
        """
        return self._var_struct

    def is_same_struct(self, other):
        """
        変数が同じ構造であるか

        Returns:
            is same: bool
        """

        if self.var_name != other.var_name:
            return False

        if self.var_attr != other.var_attr:
            return False

        # 多次元変数の場合、構造の比較も行う
        if self.var_attr == AnscConst.GC_VARS_ATTR_M_ARRAY:
            chkObj = DefaultVarsFileAnalysis(None)

            diff_vars_list = []
            diff_vars_list.append(self.var_struct['DIFF_ARRAY'])
            diff_vars_list.append(other.var_struct['DIFF_ARRAY'])

            error_code = ""
            line = ""
            ret, error_code, line = chkObj.InnerArrayDiff(diff_vars_list, error_code, line)
            if not ret:
                # 変数構造が一致しない
                return False

        return True

    @property
    def is_active(self):
        """
        変数が使用可能かどうか
        """
        return self._is_active

    def set_not_use(self):
        """
        変数を使用不可にする
        """
        self._is_active = False
