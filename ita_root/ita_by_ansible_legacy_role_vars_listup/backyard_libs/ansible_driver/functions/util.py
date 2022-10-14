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
from backyard_libs.ansible_driver.classes.ExpandableElementClass import ExpandableElement
from backyard_libs.ansible_driver.classes.NonExpandableElementClass import NonExpandableElement
from backyard_libs.ansible_driver.classes.VariableClass import Variable
from backyard_libs.ansible_driver.classes.VariableManagerClass import VariableManager

"""
ライブラリ
"""


def extract_variable_for_movement(mov_records, mov_matl_lnk_records, registerd_role_records, role_varmgr_dict):
    """
    変数を抽出する（movement）

    Arguments:
        mov_records: { pkey: { COL_NAME: value, ... }, ... }
        mov_matl_lnk_records: { pkey: { COL_NAME: value, ... }, ... }
        registerd_role_records: { pkey: { COL_NAME: value, ... }, ... }
        role_varmgr_dict: { (role_name, role_pkg_id): VariableManager }

    Returns:
        mov_vars_dict: { (movement_id): VariableManager }
    """
    g.applogger.debug("[Trace] Call util.extract_variable_for_movement()")

    mov_vars_dict = {mov_id: VariableManager() for mov_id in mov_records.keys()}

    key_convert_dict = {x['ROLE_ID']: (x['ROLE_NAME'], x['ROLE_PACKAGE_ID']) for x in registerd_role_records.values()}

    var_extractor = WrappedStringReplaceAdmin()
    for matl_lnk in mov_matl_lnk_records.values():
        movement_id = matl_lnk['MOVEMENT_ID']
        mov_vars_mgr = mov_vars_dict[movement_id]

        # ロール変数の追加
        if matl_lnk['ROLE_ID'] in key_convert_dict:
            role_varmgr_key = key_convert_dict[matl_lnk['ROLE_ID']]

            if role_varmgr_key in role_varmgr_dict:
                role_varmgr = role_varmgr_dict[role_varmgr_key]
                mov_vars_mgr.merge_variable_list(role_varmgr.export_var_list())
            else:
                # データ不整合（ロールパッケージ管理のVAR_STRUCT_ANAL_JSON_STRINGカラム内 "Role_name_list" に無いロールがMovementロール紐づけに存在）
                g.applogger.debug("Data mismatch between role_package table(json_string column) and material_link table.")

        else:
            # データ不整合（ロール名管理に無いデータがMovementロール紐づけに存在）
            g.applogger.debug("Data mismatch between role_name table and material_link table.")

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
    exec_type = '2'
    _, template_list, host_list = sub_value_auto_reg.GetDataFromParameterSheet(exec_type, WS_DB=ws_db)
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


def expand_vars_member(nest_vars_mem_records, mem_max_col_records):
    """
    メンバ変数を膨らませたレコードリストを作成する

    Arguments:
        nest_vars_mem_records: { pkey: { COL_NAME: value, ... }, ... }
        mem_max_col_records: { pkey: { COL_NAME: value, ... }, ... }

    Returns:
        mov_vars_dict: { (movement_id): VariableManager }
    """
    g.applogger.debug("[Trace] Call util.expand_vars_member()")

    # 変換用辞書作成
    max_col_dict = {}
    for max_col in mem_max_col_records.values():
        key = (max_col['MVMT_VAR_LINK_ID'], max_col['ARRAY_MEMBER_ID'])
        max_col_dict[key] = max_col['MAX_COL_SEQ']

    # 階層の上のモノから処理
    sorted_vars_mem_records = sorted(nest_vars_mem_records.values(), key=lambda x: x['ARRAY_NEST_LEVEL'])

    top_element_list = []
    for vars_mem in sorted_vars_mem_records:

        # 多段変数最大繰返数メニュー反映要素かどうか
        if vars_mem['VARS_NAME'] == '0':
            taple_key = (vars_mem['MVMT_VAR_LINK_ID'], vars_mem['ARRAY_MEMBER_ID'])
            if taple_key in max_col_dict:
                element = ExpandableElement(vars_mem, max_col_dict[taple_key])
            else:
                # 最大繰返数管理TBLに存在しない＝メンバー変数で廃止されている（全レコードの構造を形成するためだけに取得されている）
                element = ExpandableElement(vars_mem, 0)
        else:
            element = NonExpandableElement(vars_mem)

        # 既に親が生成されている場合は紐付け
        parent_key = f"{vars_mem['MVMT_VAR_LINK_ID']}-{vars_mem['PARENT_VARS_KEY_ID']}"
        for top_ele in top_element_list:
            if top_ele.has_key_recursive(parent_key):
                top_ele.set_recursive_lower_element(parent_key, element)
                break
        # 見つからなければTOP要素としてリストに追加
        else:
            top_element_list.append(element)

    nominate_mem_col_comb = []

    for ele_item in top_element_list:
        # print(ele_item)
        mem_col_comb_record_array = ele_item.build()
        for record in mem_col_comb_record_array:
            # print(record)
            nominate_mem_col_comb.append(record)

    return nominate_mem_col_comb
