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
from common_libs.ansible_driver.classes.MaterialVarsAnalyzerClass import MaterialVarsAnalyzer
from .TableBaseClass import TableBase


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

    def extract_variable(self, tpl_vars_dict):
        """
        変数を抽出する（dialog_file）

        Arguments:
            tpl_vars_dict: { (tpl_var_name): set(var_name), ... }

        Returns:
            result_dict: { dialog_type_id: set(var_name), ... }
        """
        g.applogger.debug(f"[Trace] Call {self.__class__.__name__} extract_variable()")

        dialog_analyzer = MaterialVarsAnalyzer(AnscConst.DF_PIONEER_DRIVER_ID, self._ws_db)

        result_dict = {}
        for dialog_matter_row in self._stored_records.values():
            dialog_matter_id = dialog_matter_row[self.pkey]
            dialog_type_id = dialog_matter_row["DIALOG_TYPE_ID"]  # このテーブルのみDIALOG_TYPE_IDでグルーピングする

            # ファイル読み込み
            file_name = dialog_matter_row['DIALOG_MATTER_FILE']
            result_vars = dialog_analyzer.analyze(dialog_matter_id, file_name)
            if result_vars is None:
                debug_msg = g.appmsg.get_log_message("MSG-10100", [f"{dialog_matter_id}:{file_name}"])
                g.applogger.info(debug_msg)
                continue

            if dialog_type_id not in result_dict:
                result_dict[dialog_type_id] = set()

            # 変数抽出
            for var_name in result_vars[AnscConst.DF_VAR_TYPE_VAR]:
                result_dict[dialog_type_id].add(var_name)

            # テンプレート内の変数抽出
            for tpf_var_name, line_array in result_vars[AnscConst.DF_VAR_TYPE_TPF].items():
                if tpf_var_name in tpl_vars_dict:
                    result_dict[dialog_type_id] |= tpl_vars_dict[tpf_var_name]
                else:
                    dialog_name_with_pkey = f"{dialog_matter_id}:{dialog_matter_row['DIALOG_MATTER_FILE']}"
                    debug_msg = g.appmsg.get_log_message("MSG-10123", [dialog_name_with_pkey, ','.join([str(line_no) for line_no in line_array]), tpf_var_name])
                    g.applogger.info(debug_msg)

        return result_dict
