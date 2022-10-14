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

from backyard_libs.ansible_driver.classes.VariableClass import Variable
from backyard_libs.ansible_driver.classes.VariableManagerClass import VariableManager
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.WrappedStringReplaceAdmin import WrappedStringReplaceAdmin
from .TableBaseClass import TableBase


class DeviceTable(TableBase):
    """
    機器一覧のデータを取得し、インベントリファイル追加オプションに登録されている定義変数を管理するクラス
    """

    TABLE_NAME = "T_ANSC_DEVICE"
    PKEY = "SYSTEM_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = DeviceTable.TABLE_NAME
        self.pkey = DeviceTable.PKEY

    def extract_variable(self):
        """
        変数を抽出する

        Returns:
            result_dict: { (system_id): VariableManager }
        """
        g.applogger.debug(f"[Trace] Call {self.__class__.__name__} extract_variable()")

        var_extractor = WrappedStringReplaceAdmin()
        result_dict = {}
        for row in self._stored_records.values():
            system_id = row["SYSTEM_ID"]

            vars_line_array = []  # [{行番号:変数名}, ...]
            is_success, vars_line_array = var_extractor.SimpleFillterVerSearch(AnscConst.DF_HOST_VAR_HED, row["HOSTS_EXTRA_ARGS"], vars_line_array, [], [])  # noqa: E501
            for var_info in vars_line_array:
                if system_id not in result_dict:
                    result_dict[system_id] = VariableManager()

                for line_no, var_name in var_info.items():  # forで回すが要素は1つしかない
                    var_attr = AnscConst.GC_VARS_ATTR_STD
                    item = Variable(var_name, var_attr)
                    result_dict[system_id].add_variable(item)

        return result_dict
