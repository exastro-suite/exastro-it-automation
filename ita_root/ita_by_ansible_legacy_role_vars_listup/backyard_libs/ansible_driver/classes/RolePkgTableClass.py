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

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from .TableBaseClass import TableBase
from .VariableClass import Variable
from .VariableManagerClass import VariableManager


class RolePkgTable(TableBase):
    """
    ロールパッケージ管理のデータを取得し、定義変数を管理するクラス
    """

    TABLE_NAME = "T_ANSR_MATL_COLL"
    PKEY = "ROLE_PACKAGE_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = RolePkgTable.TABLE_NAME
        self.pkey = RolePkgTable.PKEY

    def extract_variable(self):
        """
        変数を抽出する（role_pkg）

        Returns:
            role_name_list: [ {'ROLE_NAME': role_name, 'ROLE_PACKAGE_ID': role_pkg_id}, ... ]
            role_varmgr_dict: { (role_name, role_pkg_id): VariableManager }
        """
        g.applogger.debug(f"[Trace] Call {self.__class__.__name__} extract_variable()")

        role_name_list = []
        role_varmgr_dict = {}
        for role_pkg_row in self._stored_records.values():
            role_pkg_id = role_pkg_row['ROLE_PACKAGE_ID']
            var_struct = json.loads(role_pkg_row['VAR_STRUCT_ANAL_JSON_STRING'])

            # ロール名抽出
            for role_name in var_struct['Role_name_list']:
                role_name_list.append({'ROLE_NAME': role_name, 'ROLE_PACKAGE_ID': role_pkg_id})
                role_varmgr_dict[(role_name, role_pkg_id)] = VariableManager()

            # ロール変数抽出
            # - 一般変数、複数具体値変数
            for role_name, role_vars in var_struct['Vars_list'].items():
                varmgr = role_varmgr_dict[(role_name, role_pkg_id)]
                for var_name, attr_flag in role_vars.items():
                    var_attr = AnscConst.GC_VARS_ATTR_STD if attr_flag == 0 else AnscConst.GC_VARS_ATTR_LIST
                    item = Variable(var_name, var_attr)
                    varmgr.add_variable(item)
                    # print(f"role_name: {role_name}, item: {item}") # debug

            # - 多次元変数
            var_attr = AnscConst.GC_VARS_ATTR_M_ARRAY
            for role_name, role_vars in var_struct['Array_vars_list'].items():
                varmgr = role_varmgr_dict[(role_name, role_pkg_id)]
                for var_name, var_detail in role_vars.items():
                    var_struct = var_detail
                    item = Variable(var_name, var_attr, var_struct)
                    varmgr.add_variable(item)
                    # print(f"role_name: {role_name}, item: {item}") # debug

        return role_name_list, role_varmgr_dict
