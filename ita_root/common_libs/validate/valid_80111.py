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

def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''
    proc_load_id = 801  # バックヤード起動フラグのID
    maximum_iteration_limit = 1024  # 最大繰返数の上限値
    minimum_iteration_limit = 1  # 最大繰返数の下限値

    # 入力値を取得
    maximum_iteration_count = option.get('entry_parameter', {}).get('parameter', {}).get('maximum_iteration_count', {})
    if maximum_iteration_count is None or type(maximum_iteration_count) is not int:
        return retBool, msg, option,

    # バックヤード起動フラグ設定
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = {"LOADED_FLG": "0", "ROW_ID": proc_load_id}
    primary_key_name = "ROW_ID"
    objdbca.table_update(table_name, data_list, primary_key_name, False)

    # システム設定メニューの最大繰返数から値を取得
    system_settings = objdbca.table_select("T_COMN_SYSTEM_CONFIG", "WHERE CONFIG_ID=%s", ["MAXIMUM_ITERATION_TERRAFORM-CLOUD-EP"])
    if system_settings is None:
        system_maximum_iteration = maximum_iteration_limit
    else:
        system_maximum_iteration = system_settings[0]["VALUE"]
        if system_maximum_iteration.isdigit() is False:
            system_maximum_iteration = maximum_iteration_limit
        if minimum_iteration_limit > int(system_maximum_iteration) or int(system_maximum_iteration) > maximum_iteration_limit:
            system_maximum_iteration = maximum_iteration_limit

    # 入力した値が上限値を超えていないかチェック
    if int(maximum_iteration_count) > int(system_maximum_iteration) or int(minimum_iteration_limit) > int(maximum_iteration_count):
        retBool = False
        msg = g.appmsg.get_api_message('MSG-10938', [minimum_iteration_limit, system_maximum_iteration, maximum_iteration_count])

    return retBool, msg, option,
