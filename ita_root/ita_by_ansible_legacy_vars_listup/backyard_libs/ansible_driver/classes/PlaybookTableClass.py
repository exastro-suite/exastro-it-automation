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


class PlaybookTable(TableBase):
    """
    Playbook素材集管理のデータを取得し、登録廃止するクラス
    """

    TABLE_NAME = "T_ANSL_MATL_COLL"
    PKEY = "PLAYBOOK_MATTER_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = PlaybookTable.TABLE_NAME
        self.pkey = PlaybookTable.PKEY

    def extract_variable(self, tpl_vars_dict):
        """
        変数を抽出する（playbook_file）

        Arguments:
            tpl_vars_dict: { (tpl_var_name): set(var_name), ... }

        Returns:
            result_dict: { playbook_matter_id: set(var_name), ...  }
        """
        g.applogger.debug(f"[Trace] Call {self.__class__.__name__} extract_variable()")

        playbook_analyzer = MaterialVarsAnalyzer(AnscConst.DF_LEGACY_DRIVER_ID, self._ws_db)

        result_dict = {}
        for playbook_matter_row in self._stored_records.values():
            playbook_matter_id = playbook_matter_row[self.pkey]

            # ファイル読み込み
            result_vars = playbook_analyzer.analyze(playbook_matter_id, playbook_matter_row['PLAYBOOK_MATTER_FILE'])

            if playbook_matter_id not in result_dict:
                result_dict[playbook_matter_id] = set()

            # 変数抽出
            for var_name in result_vars[AnscConst.DF_VAR_TYPE_VAR]:
                result_dict[playbook_matter_id].add(var_name)

            # テンプレート内の変数抽出
            for tpl_var_name in result_vars[AnscConst.DF_VAR_TYPE_TPF]:
                result_dict[playbook_matter_id] |= tpl_vars_dict[tpl_var_name]

        return result_dict
