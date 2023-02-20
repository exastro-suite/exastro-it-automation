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
from common_libs.terraform_driver.cli.Const import Const as TFCLIConst
import re

def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''
    orchestra_id = 4  # Terraform-Cloud/EP オーケストレータID
    proc_load_id = 801  # バックヤード起動フラグのID

    # バックヤード起動フラグ設定
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = {"LOADED_FLG": "0", "ROW_ID": proc_load_id}
    primary_key_name = "ROW_ID"
    objdbca.table_update(table_name, data_list, primary_key_name, False)

    # 入力値取得
    # entry_parameter = option.get('entry_parameter').get('parameter')
    # current_parameter = option.get('current_parameter').get('parameter')
    cmd_type = option.get("cmd_type")

    # オーケストレータIDを設定
    if cmd_type == "Register":
        option["entry_parameter"]["parameter"]["orchestrator"] = orchestra_id

    return retBool, msg, option,
