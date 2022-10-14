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
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

"""
  legacyRoleの実行に必要な定数定義モジュール
"""


class AnsrConst(AnscConst):
    """
      legacyRoleの実行に必要な定数定義クラス
    """
    vg_driver_id = AnscConst.DF_LEGACY_ROLE_DRIVER_ID
    vg_info_table_name = "T_ANSC_IF_INFO"
    vg_exe_ins_msg_table_name = "T_ANSR_EXEC_STS_INST"
    vg_ansible_roleDB = "T_ANSR_ROLE_NAME"
    vg_ansible_role_varsDB = "T_ANSR_ROLE_VAR"
    vg_ansible_pattern_listDB = "V_ANSR_MOVEMENT"
    # vg_ansible_role_packageDB = "T_ANSR_MATL_COLL"
    vg_ansible_master_fileDB = "T_ANSR_MATL_COLL"
    vg_ansible_master_file_pkeyITEM = "ROLE_PACKAGE_ID"
    vg_ansible_master_file_nameITEM = "ROLE_PACKAGE_NAME"
    vg_ansible_vars_masterDB = ""
    vg_ansible_pattern_linkDB = "T_ANSR_MVMT_MATL_LINK"
    vg_ansible_pattern_vars_linkDB = "T_ANSR_MVMT_VAR_LINK"
    vg_ansible_nestvar_member_max_colDB = "T_ANSR_NESTVAR_MEMBER_MAX_COL"
    vg_ansible_vaule_autoregDB = "T_ANSR_VALUE_AUTOREG"
    vg_ansible_pho_linkDB = "T_ANSR_TGT_HOST"
    vg_ansible_vars_assignDB = "T_ANSR_VALUE"
    vg_ansible_nestvar_memberDB = "T_ANSR_NESTVAR_MEMBER"
    vg_ansible_nestvar_member_col_combDB = "T_ANSR_NESTVAR_MEMBER_COL_COMB"
    
    # AnsibleTowerのita_executions_prepare_buildで使用している変数
    vg_tower_driver_name = "legacy_role"
    # 親Playbookのファイル名
    vg_parent_playbook_name = "site.yml"
    
    vg_OrchestratorSubId_dir = vg_tower_driver_name
