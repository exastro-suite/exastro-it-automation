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
terraformドライバー（terraform Cloud/EP）に必要な定数定義モジュール
"""
from common_libs.terraform_driver.common.Const import Const as CommonConst


class Const(CommonConst):
    """
    terraformドライバー（terraform Cloud/EP）に必要な定数定義クラス
    """

    # テーブル/ビュー名
    T_IF_INFO = 'T_TERE_IF_INFO'  # インターフェース情報
    T_ORGANIZATION = 'T_TERE_ORGANIZATION'  # Organization管理
    T_WORKSPACE = 'T_TERE_WORKSPACE'  # Workspace管理
    T_MODULE = 'T_TERE_MODULE'  # Module素材集
    T_POLICY = 'T_TERE_POLICY'  # Policy管理
    T_POLICYSET = 'T_TERE_POLICYSET'  # PolicySet管理
    T_POLICYSET_POLICY = 'T_TERE_POLICYSET_POLICY_LINK'  # PolicySet-Policy紐付
    T_POLICYSET_WORKSPACE = 'T_TERE_POLICYSET_WORKSPACE_LINK'  # PolicySet-Workspace紐付
    T_MOVEMENT_MODULE = 'T_TERE_MVMT_MOD_LINK'  # Movement-Module紐付
    T_NESTVARS_MEMBER_MAX = 'T_TERE_NESTVAR_MEMBER_MAX_COL'  # 変数ネスト管理
    T_VALUE_AUTOREG = 'T_TERE_VALUE_AUTOREG'  # 代入値自動登録設定
    T_EXEC_STS_INST = 'T_TERE_EXEC_STS_INST'  # 作業管理
    T_VALUE = 'T_TERE_VALUE'  # 代入値管理
    T_MODULE_VAR = 'T_TERE_MOD_VAR_LINK'  # Module-変数紐付
    T_VAR_MEMBER = 'T_TERE_VAR_MEMBER'  # メンバー変数管理
    T_MOVEMENT_VAR = 'T_TERE_MVMT_VAR_LINK'  # Movement-変数紐付
    T_MOVEMENT_VAR_MEMBER = 'T_TERE_MVMT_VAR_MEMBER_LINK'  # Movement-メンバー変数紐付
    V_MOVEMENT = 'V_TERE_MOVEMENT'  # Movement一覧(VIEW)
    V_VAR_MEMVER = 'V_TERE_VAR_MEMBER'  # メンバー変数管理(VIEW)
    V_MOVEMENT_VAR = 'V_TERE_MVMT_VAR_LINK'  # Movement-変数紐付(VIEW)
    V_MOVEMENT_VAR_MEMBER = 'V_TERE_MVMT_VAR_MEMBER_LINK'  # Movement-メンバー変数紐付(VIEW)
    V_ORGANIZATION_WORKSPACE = 'V_TERE_ORGANIZATION_WORKSPACE_LINK'  # Organizatioin-Workspace紐付(VIEW)

    # メニュー名(REST)
    RN_IF_INFO = 'intarface_info_terraform_cloud_ep'  # インターフェース情報
    RN_ORGANIZATION = 'organization_list_terraform_cloud_ep'  # Organization管理
    RN_WORKSPACE = 'workspace_list_terraform_cloud_ep'  # Workspace管理
    RN_MOVEMENT = 'movement_list_terraform_cloud_ep'  # Movement一覧
    RN_MODULE = 'module_files_terraform_cloud_ep'  # Module素材集
    RN_POLICY = 'policy_list_terraform_cloud_ep'  # Policy管理
    RN_POLICYSET = 'policyset_list_terraform_cloud_ep'  # PolicySet管理
    RN_POLICYSET_POLICY = 'policyset_policy_link_terraform_cloud_ep'  # PolicySet-Policy紐付
    RN_POLICYSET_WORKSPACE = 'policyset_workspace_link_terraform_cloud_ep'  # PolicySet-Workspace紐付
    RN_MOVEMENT_MODULE = 'movement_module_link_terraform_cloud_ep'  # Movement-Module紐付
    RN_NESTVARS_MEMBER_MAX = 'nested_variable_list_terraform_cloud_ep'  # 変数ネスト管理
    RN_VALUE_AUTOREG = 'subst_value_auto_reg_setting_terraform_cloud_ep'  # 代入値自動登録設定
    RN_EXECTION = 'execution_terraform_cloud_ep'  # 作業実行
    RN_EXECUTION_LIST = 'execution_list_terraform_cloud_ep'  # 作業管理
    RN_CHECK_OPERATION = 'check_operation_status_terraform_cloud_ep'  # 作業状態確認
    RN_VALUE = 'subst_value_list_terraform_cloud_ep'  # 代入値管理
    RN_TERRAFORM_MANAGEMENT = 'linked_terraform_management'  # 連携先Terraform管理
    RN_MODULE_VAR = 'module_variable_link_terraform_cloud_ep'  # Module-変数紐付
    RN_VAR_MEMBER = 'member_variable_terraform_cloud_ep'  # メンバー変数管理
    RN_MOVEMENT_VAR = 'movement_variable_link_terraform_cloud_ep'  # Movement-変数紐付
    RN_MOVEMENT_VAR_MEMBER = 'movement_member_variable_link_terraform_cloud_ep'  # Movement-メンバー変数紐付

    # メニューID
    ID_IF_INFO = '80101'  # インターフェース情報
    ID_ORGANIZATION = '80102'  # Organization管理
    ID_WORKSPACE = '80103'  # Workspace管理
    ID_MOVEMENT = '80104'  # Movement一覧
    ID_MODULE = '80105'  # Module素材集
    ID_POLICY = '80106'  # Policy管理
    ID_POLICYSET = '80107'  # PolicySet管理
    ID_POLICYSET_POLICY = '80108'  # PolicySet-Policy紐付
    ID_POLICYSET_WORKSPACE = '80109'  # PolicySet-Workspace紐付
    ID_MOVEMENT_MODULE = '80110'  # Movement-Module紐付
    ID_NESTVARS_MEMBER_MAX = '80111'  # 変数ネスト管理
    ID_VALUE_AUTOREG = '80112'  # 代入値自動登録設定
    ID_EXECTION = '80113'  # 作業実行
    ID_EXECUTION_LIST = '80114'  # 作業管理
    ID_CHECK_OPERATION = '80115'  # 作業状態確認
    ID_VALUE = '80116'  # 代入値管理
    ID_TERRAFORM_MANAGEMENT = '80117'  # 連携先Terraform管理
    ID_MODULE_VAR = '80118'  # Module-変数紐付
    ID_VAR_MEMBER = '80119'  # メンバー変数管理
    ID_MOVEMENT_VAR = '80120'  # Movement-変数紐付
    ID_MOVEMENT_VAR_MEMBER = '80121'  # Movement-メンバー変数紐付

    # 作業実行関連ディレクトリ
    DIR_MODULE = '/uploadfiles/80105/module_file'  # Module素材集
    DIR_POLICY = '/uploadfiles/80106/policy_file'  # Policyファイル
    DIR_POPLATED_DATA = '/uploadfiles/80114/populated_data'  # 投入データ
    DIR_RESILT_DATA = '/uploadfiles/80114/result_data'  # 結果データ
    DIR_EXECUTE = '/driver/terraform_cloud_ep/execute'  # 作業状態確認
    DIR_TEMP = '/tmp/driver/terraform_cloud_ep'  # Temporary

    # Terraform RUN Status
    TF_RUN_CANCEL = 'canceled'

    # Terraform Plan Status
    TF_PLAN_ERROR = 'errored'
    TF_PLAN_FINISH = 'finished'
    TF_PLAN_CANCEL = 'canceled'
    TF_PLAN_RUNNING = 'running'

    # Terraform PolicyCheck Status
    TF_POLICY_CANCEL = 'canceled'

    # Terraform Apply Status
    TF_APPLY_ERROR = 'errored'
    TF_APPLY_FINISH = 'finished'
    TF_APPLY_CANCEL = 'canceled'
    TF_APPLY_UNREACH = 'unreachable'
    TF_APPLY_RUNNING = 'running'
