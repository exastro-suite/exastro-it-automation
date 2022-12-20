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
from common_libs.ansible_driver.classes.WrappedStringReplaceAdmin import WrappedStringReplaceAdmin
from .TableBaseClass import TableBase
from .VariableClass import Variable
from .VariableManagerClass import VariableManager


class DialogTable(TableBase):
    """
    対話ファイル素材集管理のデータを取得し、登録廃止するクラス
    """

    TABLE_NAME = "T_ANSP_MATL_COLL"
    PKEY = "DIALOG_MATTER_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = DialogTable.TABLE_NAME
        self.pkey = DialogTable.PKEY

    def extract_variable(self):
        """
        変数を抽出する（dialog_file）

        Returns:
            dialog_varmgr_dict: { dialog_matter_id: VariableManager }
        """
        g.applogger.debug(f"[Trace] Call {self.__class__.__name__} extract_variable()")

        var_extractor = WrappedStringReplaceAdmin()
        dialog_varmgr_dict = {}
        for dialog_matter_row in self._stored_records.values():
            dialog_matter_id = dialog_matter_row[self.pkey]

            # ファイル読み込み
            #TODO dialog_vars = xxxxx(dialog_matter_row['DIALOG_MATTER_FILE'])
            dialog_vars = {}

            # 変数抽出
            varmgr = VariableManager()
            #TODO
            for var_name, attr_flag in dialog_vars.items():
                var_attr = AnscConst.GC_VARS_ATTR_STD if attr_flag == 0 else AnscConst.GC_VARS_ATTR_LIST
                item = Variable(var_name, var_attr)
                varmgr.add_variable(item)
                # print(f"item: {item}") # debug

            dialog_varmgr_dict[dialog_matter_id] = varmgr

        return dialog_varmgr_dict
