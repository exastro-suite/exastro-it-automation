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
import sys
import traceback

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.WrappedStringReplaceAdmin import WrappedStringReplaceAdmin
from common_libs.ansible_driver.functions.util import getLegacyPlaybookUploadDirPath, getPioneerDialogUploadDirPath
from common_libs.conductor.classes.exec_util import addline_msg
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

        try:
            data_string = self._read_material_file(uuid, file_name)
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.debug(msg)
            return None

        var_extractor = WrappedStringReplaceAdmin(self._ws_db)
        FillterVars = True  # Fillterを含む変数の抜き出しあり
        result_vars = {}

        # VAR変数
        is_success, vars_line_array = var_extractor.SimpleFillterVerSearch(AnscConst.DF_HOST_VAR_HED, data_string, [], [], [], FillterVars)
        vars_array = set()
        for var_dict in vars_line_array:
            for line_no, var_name in var_dict.items():  # forで回すが要素は1つしかない
                vars_array.add(var_name)
        result_vars[AnscConst.DF_VAR_TYPE_VAR] = list(vars_array)

        # TPF変数
        is_success, vars_line_array = var_extractor.SimpleFillterVerSearch(AnscConst.DF_HOST_TPF_HED, data_string, [], [], [], FillterVars)
        tpf_vars_dict = {}
        for var_dict in vars_line_array:
            for line_no, var_name in var_dict.items():  # forで回すが要素は1つしかない
                if var_name not in tpf_vars_dict:
                    tpf_vars_dict[var_name] = []
                tpf_vars_dict[var_name].append(line_no)
        result_vars[AnscConst.DF_VAR_TYPE_TPF] = tpf_vars_dict

        return result_vars

    def _read_material_file(self, uuid, file_name):

        if AnscConst.DF_LEGACY_DRIVER_ID == self._driver_id:
            upload_column_path = getLegacyPlaybookUploadDirPath()
        elif AnscConst.DF_PIONEER_DRIVER_ID == self._driver_id:
            upload_column_path = getPioneerDialogUploadDirPath()
        else:
            raise NotImplementedError()

        file_path = "{}/{}/{}".format(upload_column_path, uuid, file_name)

        with open(file_path, "rb") as f:
            result = f.read().decode('utf-8')

        return result

    def _vars_line_array_to_vars_array(self, vars_line_array):

        vars_array = set()
        for var_dict in vars_line_array:
            for line_no, var_name in var_dict.items():  # forで回すが要素は1つしかない
                vars_array.add(var_name)

        return list(vars_array)
