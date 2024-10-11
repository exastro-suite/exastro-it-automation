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
import json
import os

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.WrappedStringReplaceAdmin import WrappedStringReplaceAdmin
from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg

"""
ライブラリ
"""


def extract_variable_for_movement(mov_records, mov_matl_lnk_records, dialog_vars_dict):
    """
    変数を抽出する（movement）

    Arguments:
        mov_records: { pkey: { COL_NAME: value, ... }, ... }
        mov_matl_lnk_records: { pkey: { COL_NAME: value, ... }, ... }
        dialog_vars_dict: { dialog_type_id: set(var_name), ... }

    Returns:
        mov_vars_dict: { (movement_id): set(var_name), ... }
    """
    g.applogger.debug("[Trace] Call util.extract_variable_for_movement()")

    mov_vars_dict = {}

    for matl_lnk in mov_matl_lnk_records.values():
        # Movementごとの対話ファイル変数の追加
        movement_id = matl_lnk['MOVEMENT_ID']
        dialog_type_id = matl_lnk['DIALOG_TYPE_ID']

        if movement_id not in mov_vars_dict:
            mov_vars_dict[movement_id] = set()

        if dialog_type_id in dialog_vars_dict:
            mov_vars_dict[movement_id] |= dialog_vars_dict[dialog_type_id]

    return mov_vars_dict


def extract_variable_for_execute(mov_vars_dict, tpl_vars_dict, ws_db):
    """
    変数を抽出する（実行時相当）

    Arguments:
        mov_vars_dict: { (movement_id): set(var_name), ... }
        tpl_vars_dict: { (tpl_var_name): set(var_name), ... }
        ws_db: DBConnectWs

    Returns:
        mov_vars_dict: { (movement_id): set(var_name) }
    """
    g.applogger.debug("[Trace] Call util.extract_variable_for_execute()")

    driver_type = AnscConst.DF_PIONEER_DRIVER_ID
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

    return mov_vars_dict
