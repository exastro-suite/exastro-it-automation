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
from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg

"""
ライブラリ
"""


def extract_variable_for_movement(mov_records, mov_matl_lnk_records, playbook_vars_dict, ws_db):
    """
    変数を抽出する（movement）

    Arguments:
        mov_records: { pkey: { COL_NAME: value, ... }, ... }
        mov_matl_lnk_records: { pkey: { COL_NAME: value, ... }, ... }
        playbook_vars_dict: { playbook_matter_id: set(var_name), ... }

    Returns:
        mov_vars_dict: { (movement_id): set(var_name), ...  }
    """
    g.applogger.debug("[Trace] Call util.extract_variable_for_movement()")

    mov_vars_dict = {}

    var_extractor = WrappedStringReplaceAdmin(ws_db)
    for matl_lnk in mov_matl_lnk_records.values():
        # Movementごとのplaybook変数の追加
        movement_id = matl_lnk['MOVEMENT_ID']
        playbook_matter_id = matl_lnk['PLAYBOOK_MATTER_ID']

        if movement_id not in mov_vars_dict:
            mov_vars_dict[movement_id] = set()

        if playbook_matter_id in playbook_vars_dict:
            mov_vars_dict[movement_id] |= playbook_vars_dict[playbook_matter_id]

    for movement_id, vars_set in mov_vars_dict.items():

        # Movementが廃止されていないことを確認
        if movement_id in mov_records:
            # Movementの追加オプションの変数の追加
            ans_exec_options = mov_records[movement_id]['ANS_PLAYBOOK_HED_DEF']

            var_heder_id = AnscConst.DF_HOST_VAR_HED  # VAR変数
            vars_line_array = []  # [{行番号:変数名}, ...]
            is_success, vars_line_array = var_extractor.SimpleFillterVerSearch(var_heder_id, ans_exec_options, [], [], [])  # noqa: E501
            for mov_var in vars_line_array:
                for line_no, var_name in mov_var.items():  # forで回すが要素は1つしかない
                    vars_set.add(var_name)

        mov_vars_dict[movement_id] = vars_set

    return mov_vars_dict


def extract_variable_for_execute(mov_vars_dict, tpl_vars_dict, device_vars_dict, ws_db):
    """
    変数を抽出する（実行時相当）

    Arguments:
        mov_vars_dict: { (movement_id): set(var_name), ... }
        tpl_vars_dict: { (tpl_var_name): set(var_name), ... }
        device_vars_dict: { (sytem_id): set(var_name), ... }
        ws_db: DBConnectWs

    Returns:
        mov_vars_dict: { (movement_id): set(var_name) }
    """
    g.applogger.debug("[Trace] Call util.extract_variable_for_execute()")

    driver_type = AnscConst.DF_LEGACY_DRIVER_ID
    sub_value_auto_reg = SubValueAutoReg(driver_type, ws_db)
    _, template_list, host_list = sub_value_auto_reg.get_data_from_all_parameter_sheet()
    # template_list = { MovementID: { TPF変数名: 0 }, … }
    # host_list = { MovementID: { OPERATION_ID: { SYSTEM_ID: 0 }, … }, … }

    for movement_id, tpl_var_set in template_list.items():
        for tpl_var_name in tpl_var_set:
            if tpl_var_name in tpl_vars_dict:
                mov_vars_dict[movement_id] |= tpl_vars_dict[tpl_var_name]
            else:
                debug_msg = g.appmsg.get_log_message("MSG-10531", [tpl_var_name])
                g.applogger.info(debug_msg)

    for movement_id, ope_host_dict in host_list.items():
        for _, system_dict in ope_host_dict.items():
            for system_id in system_dict.keys():

                # 作業ホストに解析すべき変数があれば
                if system_id in device_vars_dict:
                    mov_vars_dict[movement_id] |= device_vars_dict[system_id]

    return mov_vars_dict
