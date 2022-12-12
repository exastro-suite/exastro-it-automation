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
from backyard_libs.ansible_driver.classes.VariableClass import Variable
from backyard_libs.ansible_driver.classes.VariableManagerClass import VariableManager

"""
ライブラリ
"""


def extract_variable_for_movement(mov_records, mov_matl_lnk_records):
    """
    変数を抽出する（movement）

    Arguments:
        mov_records: { pkey: { COL_NAME: value, ... }, ... }
        mov_matl_lnk_records: { pkey: { COL_NAME: value, ... }, ... }

    Returns:
        mov_vars_dict: { (movement_id): VariableManager }
    """
    g.applogger.debug("[Trace] Call util.extract_variable_for_movement()")

    mov_vars_dict = {mov_id: VariableManager() for mov_id in mov_records.keys()}

    var_extractor = WrappedStringReplaceAdmin()
    for matl_lnk in mov_matl_lnk_records.values():
        movement_id = matl_lnk['MOVEMENT_ID']
        mov_vars_mgr = mov_vars_dict[movement_id]

        # Movementの追加オプションの変数の追加
        ans_exec_options = mov_records[movement_id]['ANS_EXEC_OPTIONS']

        var_heder_id = AnscConst.DF_HOST_VAR_HED  # VAR変数
        mt_varsLineArray = []  # [{行番号:変数名}, ...]
        mt_varsArray = []  # 不要
        arrylocalvars = []  # 不要
        is_success, mt_varsLineArray = var_extractor.SimpleFillterVerSearch(var_heder_id, ans_exec_options, mt_varsLineArray, mt_varsArray, arrylocalvars)  # noqa: E501
        for mov_var in mt_varsLineArray:
            for line_no, var_name in mov_var.items():  # forで回すが要素は1つしかない
                var_attr = AnscConst.GC_VARS_ATTR_STD
                item = Variable(var_name, var_attr)

                # item を add するがオプション変数扱い
                mov_vars_mgr.add_variable(item, is_option_var=True)

        mov_vars_dict[movement_id] = mov_vars_mgr

    return mov_vars_dict


def extract_variable_for_execute(mov_vars_dict, tpl_varmng_dict, device_varmng_dict, ws_db):
    """
    変数を抽出する（実行時相当）

    Arguments:
        mov_vars_dict: { (movement_id): VariableManager, ... }
        tpl_varmng_dict: { (tpl_var_name): VariableManager, ... }
        device_varmng_dict: { (sytem_id): VariableManager, ... }
        ws_db: DBConnectWs

    Returns:
        mov_vars_dict: { (movement_id): VariableManager }
    """
    g.applogger.debug("[Trace] Call util.extract_variable_for_execute()")

    sub_value_auto_reg = SubValueAutoReg()
    driver_type = AnscConst.DF_LEGACY_DRIVER_ID
    _, template_list, host_list = sub_value_auto_reg.get_data_from_all_parameter_sheet(driver_type, WS_DB=ws_db)
    # template_list = { MovementID: { TPF変数名: 0 }, … }
    # host_list = { MovementID: { OPERATION_ID: { SYSTEM_ID: 0 }, … }, … }

    for movement_id, tpl_var_set in template_list.items():
        tpl_var_name = tpl_var_set.keys()[0]
        mov_vars_dict[movement_id].merge_variable_list(tpl_varmng_dict[tpl_var_name].export_var_list())

    for movement_id, ope_host_dict in host_list.items():
        for _, system_dict in ope_host_dict.items():
            for system_id in system_dict.keys():

                # 作業ホストに解析すべき変数があれば
                if system_id in device_varmng_dict:
                    mov_vars_dict[movement_id].merge_variable_list(device_varmng_dict[system_id].export_var_list(), is_option_var=True)

    return mov_vars_dict
