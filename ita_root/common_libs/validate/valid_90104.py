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
from flask import g
from common_libs.terraform_driver.common.Hcl2Json import HCL2JSONParse
# from common_libs.terraform_driver.cli.Const import Const as TFCLIEPConst
import re
import base64
import os


def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''
    proc_load_id = 901  # バックヤード起動フラグのID

    # バックヤード起動フラグ設定
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = {"LOADED_FLG": "0", "ROW_ID": proc_load_id}
    primary_key_name = "ROW_ID"
    objdbca.table_update(table_name, data_list, primary_key_name, False)

    # 登録/更新時のみ
    cmd_type = option.get("cmd_type")
    if cmd_type in ["Register", "Update"]:
        # 拡張子が「.tf」の場合、パース処理が実行可能かどうかをチェック
        file_name = option.get('entry_parameter', {}).get('parameter', {}).get('module_file')
        file_path = option.get('entry_parameter', {}).get('file_path', {}).get('module_file')
        if file_name:
            pattern = r'\.tf$'
            match = re.findall(pattern, file_name)
            if match:
                if file_path:
                    # tfファイルパース処理を実行する。
                    hcl2json = HCL2JSONParse(file_path)
                    hcl2json.executeParse(True)
                    result = hcl2json.getParseResult()
                    if result.get('res') is False:
                        # パースに失敗した場合、バリデーションエラーとする
                        retBool = False
                        msg = g.appmsg.get_api_message("MSG-80007", [result.get('error_msg')])

    return retBool, msg, option,
