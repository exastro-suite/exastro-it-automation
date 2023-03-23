# Copyright 2023 NEC Corporation#
# Licensed under the Apache License, Version 2.2 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.2
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
terraformドライバー（terraform CLI）に必要な定数定義モジュール
"""
from common_libs.terraform_driver.common.Const import Const as CommonConst


class Const(CommonConst):
    """
    terraformドライバー（terraform CLI）に必要な定数定義クラス
    """

    # テーブル/ビュー名
    T_IF_INFO = 'T_TERC_IF_INFO'  # インターフェース情報
    T_WORKSPACE = 'T_TERC_WORKSPACE'  # Workspace管理
    T_MODULE = 'T_TERC_MODULE'  # Module素材集
    T_MOVEMENT_MODULE = 'T_TERC_MVMT_MOD_LINK'  # Movement-Module紐付
    T_NESTVARS_MEMBER_MAX = 'T_TERC_NESTVAR_MEMBER_MAX_COL'  # 変数ネスト管理
    T_VALUE_AUTOREG = 'T_TERC_VALUE_AUTOREG'  # 代入値自動登録設定
    T_EXEC_STS_INST = 'T_TERC_EXEC_STS_INST'  # 作業管理
    T_VALUE = 'T_TERC_VALUE'  # 代入値管理
    T_MODULE_VAR = 'T_TERC_MOD_VAR_LINK'  # Module-変数紐付
    T_VAR_MEMBER = 'T_TERC_VAR_MEMBER'  # メンバー変数管理
    T_MOVEMENT_VAR = 'T_TERC_MVMT_VAR_LINK'  # Movement-変数紐付
    T_MOVEMENT_VAR_MEMBER = 'T_TERC_MVMT_VAR_MEMBER_LINK'  # Movement-メンバー変数紐付
    V_MOVEMENT = 'V_TERC_MOVEMENT'  # Movement一覧(VIEW)
    V_VAR_MEMVER = 'V_TERC_VAR_MEMBER'  # メンバー変数管理(VIEW)
    V_MOVEMENT_VAR = 'V_TERC_MVMT_VAR_LINK'  # Movement-変数紐付(VIEW)
    V_MOVEMENT_VAR_MEMBER = 'V_TERC_MVMT_VAR_MEMBER_LINK'  # Movement-メンバー変数紐付(VIEW)

    # メニュー名(REST)
    RN_IF_INFO = 'intarface_info_terraform_cli'  # インターフェース情報
    RN_WORKSPACE = 'workspace_list_terraform_cli'  # Workspace管理
    RN_MOVEMENT = 'movement_list_terraform_cli'  # Movement一覧
    RN_MODULE = 'module_files_terraform_cli'  # Module素材集
    RN_MOVEMENT_MODULE = 'movement_module_link_terraform_cli'  # Movement-Module紐付
    RN_NESTVARS_MEMBER_MAX = 'nested_variable_list_terraform_cli'  # 変数ネスト管理
    RN_VALUE_AUTOREG = 'subst_value_auto_reg_setting_terraform_cli'  # 代入値自動登録設定
    RN_EXECTION = 'execution_terraform_cli'  # 作業実行
    RN_EXECUTION_LIST = 'execution_list_terraform_cli'  # 作業管理
    RN_CHECK_OPERATION = 'check_operation_status_terraform_cli'  # 作業状態確認
    RN_VALUE = 'subst_value_list_terraform_cli'  # 代入値管理
    RN_MODULE_VAR = 'module_variable_link_terraform_cli'  # Module-変数紐付
    RN_VAR_MEMBER = 'member_variable_terraform_cli'  # メンバー変数管理
    RN_MOVEMENT_VAR = 'movement_variable_link_terraform_cli'  # Movement-変数紐付
    RN_MOVEMENT_VAR = 'movement_member_variable_link_terraform_cli'  # Movement-変数紐付

    # メニューID
    ID_IF_INFO = '90101'  # インターフェース情報
    ID_WORKSPACE = '90102'  # Workspace管理
    ID_MOVEMENT = '90103'  # Movement一覧
    ID_MODULE = '90104'  # Module素材集
    ID_MOVEMENT_MODULE = '90105'  # Movement-Module紐付
    ID_NESTVARS_MEMBER_MAX = '90106'  # 変数ネスト管理
    ID_VALUE_AUTOREG = '90107'  # 代入値自動登録設定
    ID_EXECTION = '90108'  # 作業実行
    ID_EXECUTION_LIST = '90109'  # 作業管理
    ID_CHECK_OPERATION = '90110'  # 作業状態確認
    ID_VALUE = '90111'  # 代入値管理
    ID_MODULE_VAR = '90112'  # Module-変数紐付
    ID_VAR_MEMBER = '90113'  # メンバー変数管理
    ID_MOVEMENT_VAR = '90114'  # Movement-変数紐付
    ID_MOVEMENT_VAR = '90115'  # Movement-変数紐付

    # 作業実行関連ディレクトリ
    DIR_MODULE = '/uploadfiles/90104/module_file'  # Module素材集
    DIR_POPLATED_DATA = '/uploadfiles/90109/populated_data'  # 投入データ
    DIR_RESILT_DATA = '/uploadfiles/90109/result_data'  # 結果データ
    DIR_EXECUTE = '/driver/terraform_cli/execute'  # 作業状態確認
    DIR_WORK = '/driver/terraform_cli/workspace'  # Terraform CLIコマンド実行用
    DIR_TEMP = '/tmp/driver/terraform_cli'  # Temporary

    # ファイル名
    FILE_EMERGENCY_STOP = 'emergency_stop'  # 緊急停止の検知用ファイル
