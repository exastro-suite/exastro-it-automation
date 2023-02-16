# Copyright 2023 NEC Corporation#
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

import os

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.WrappedStringReplaceAdmin import WrappedStringReplaceAdmin
from common_libs.ansible_driver.functions.util import getLegacyPlaybookUploadDirPath, getPioneerDialogUploadDirPath
from flask import g


class MaterialVarsAnalyzer():

    def __init__(self, driver_id, ws_db):
        """
        コンストラクタ
        """
        self._driver_id = driver_id
        self._ws_db = ws_db

    def analyze(self, uuid, file_name):
        """
        変数を抽出する（playbook_file）

        Arguments:
            tpl_vars_dict: { (tpl_var_name): set(var_name), ... }

        Returns:
            result_vars: { playbook_matter_id: set(var_name) }
        """

        data_string = self._read_material_file(uuid, file_name)
        print(f"MaterialVarsAnalyzerClass.py Line43: {data_string}")
        var_extractor = WrappedStringReplaceAdmin()
        result_vars = {}

        # VAR変数
        is_success, vars_line_array = var_extractor.SimpleFillterVerSearch(AnscConst.DF_HOST_VAR_HED, data_string, [], [], [])
        vars_array = self._vars_line_array_to_vars_array(vars_line_array)
        result_vars[AnscConst.DF_VAR_TYPE_VAR] = vars_array

        if AnscConst.DF_LEGACY_DRIVER_ID == self._driver_id:
            # TPF変数
            FillterVars = True  # Fillterを含む変数の抜き出しあり
            is_success, vars_line_array = var_extractor.SimpleFillterVerSearch(AnscConst.DF_HOST_TPF_HED, data_string, [], [], [], FillterVars)
            vars_array = self._vars_line_array_to_vars_array(vars_line_array)
            result_vars[AnscConst.DF_VAR_TYPE_TPF] = vars_array

        return result_vars

    def _read_material_file(self, uuid, file_name):

        if AnscConst.DF_LEGACY_DRIVER_ID == self._driver_id:
            upload_column_path = getLegacyPlaybookUploadDirPath()
        elif AnscConst.DF_PIONEER_DRIVER_ID == self._driver_id:
            upload_column_path = getPioneerDialogUploadDirPath()
        else:
            raise NotImplementedError()

        file_path = "{}/{}/{}".format(upload_column_path, uuid, file_name)
        print(file_path)

        with open(file_path, "rb") as f:
            result = f.read().decode('utf-8')

        return result

    def _vars_line_array_to_vars_array(self, vars_line_array):

        vars_array = set()
        for var_dict in vars_line_array:
            for line_no, var_name in var_dict.items():  # forで回すが要素は1つしかない
                vars_array.add(var_name)

        return list(vars_array)
