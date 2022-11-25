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
import json

from backyard_libs.ansible_driver.classes.VariableClass import Variable
from backyard_libs.ansible_driver.classes.VariableManagerClass import VariableManager
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from .TableBaseClass import TableBase


class TemplateTable(TableBase):
    """
    テンプレート管理のデータを取得し、定義変数を管理するクラス
    """

    TABLE_NAME = "T_ANSC_TEMPLATE_FILE"
    PKEY = "ANS_TEMPLATE_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = TemplateTable.TABLE_NAME
        self.pkey = TemplateTable.PKEY

    def extract_variable(self):
        """
        変数を抽出する

        Returns:
            result_dict: { (tpl_var_name): VariableManager }
        """
        g.applogger.debug(f"[Trace] Call {self.__class__.__name__} extract_variable()")

        result_dict = {}
        for row in self._stored_records.values():
            tpl_var_name = row['ANS_TEMPLATE_VARS_NAME']
            var_struct = json.loads(row['VAR_STRUCT_ANAL_JSON_STRING'])

            if tpl_var_name not in result_dict:
                result_dict[tpl_var_name] = VariableManager()

            # 一般変数、複数具体値変数
            for var_name, attr_flag in var_struct['Vars_list'].items():
                var_attr = AnscConst.GC_VARS_ATTR_STD if attr_flag == 0 else AnscConst.GC_VARS_ATTR_LIST
                item = Variable(var_name, var_attr)
                result_dict[tpl_var_name].add_variable(item)

            # 多次元変数
            var_attr = AnscConst.GC_VARS_ATTR_M_ARRAY
            for var_name, var_detail in var_struct['Array_vars_list'].items():
                var_struct = var_detail
                item = Variable(var_name, var_attr, var_struct)
                result_dict[tpl_var_name].add_variable(item)

        return result_dict
