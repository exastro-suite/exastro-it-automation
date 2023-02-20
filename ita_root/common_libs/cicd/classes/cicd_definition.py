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


class TD_SYNC_STATUS_NAME_DEFINE():
    """
    リモートリポジトリ・資材紐付  同期状態マスタ
    """

    STS_NONE    = None
    STS_NORMAL  = "1"
    STS_ERROR   = "2"
    STS_RESTART = "3"

    @staticmethod
    def NORMAL():
        # 正常
        return g.appmsg.get_api_message("MSG-90071")

    @staticmethod
    def ERROR():
        # 異常
        return g.appmsg.get_api_message("MSG-90072")

    @staticmethod
    def RESTART():
        # 再開
        return g.appmsg.get_api_message("MSG-90073")


class TD_B_CICD_MATERIAL_FILE_TYPE_NAME():
    """
    Git資材ファイルタイプマスタ
    """

    C_MATL_FILE_TYPE_ROW_ID_FILE  = "1"  # ファイル
    C_MATL_FILE_TYPE_ROW_ID_ROLES = "2"  # Roles


class TD_B_CICD_MATERIAL_TYPE_NAME():
    """
    資材紐付管理  紐付先素材タイプマスタ
    """

    C_MATL_TYPE_ROW_ID_LEGACY     = "1"  # Legacy/Playbook素材集
    C_MATL_TYPE_ROW_ID_PIONEER    = "2"  # Pioneer/対話ファイル素材集
    C_MATL_TYPE_ROW_ID_ROLE       = "3"  # LegacyRole/ロールパッケージ管理
    C_MATL_TYPE_ROW_ID_CONTENT    = "4"  # Ansible共通/ファイル管理
    C_MATL_TYPE_ROW_ID_TEMPLATE   = "5"  # Ansible共通/テンプレート管理
    C_MATL_TYPE_ROW_ID_MODULE     = "6"  # Terraform/Module素材
    C_MATL_TYPE_ROW_ID_POLICY     = "7"  # Terraform/Policy管理
    C_MATL_TYPE_ROW_ID_MODULE_CLI = "8"  # Terraform-CLI/Module素材
class TD_C_PATTERN_PER_ORCH():
    """
    オーケストレータタイプ
    """

    C_EXT_STM_ID_LEGACY        = "1"
    C_EXT_STM_ID_PIONEER       = "2"
    C_EXT_STM_ID_ROLE          = "3"
    C_EXT_STM_ID_TERRAFORM     = "4"
    C_EXT_STM_ID_TERRAFORM_CLI = "5"

    # 作業状態確認　メニュー名(rest_menu_name)
    C_CHECK_OPERATION_STATUS_MENU_NAME = {}
    C_CHECK_OPERATION_STATUS_MENU_NAME[C_EXT_STM_ID_LEGACY] = "check_operation_status_ansible_legacy"
    C_CHECK_OPERATION_STATUS_MENU_NAME[C_EXT_STM_ID_PIONEER] = "check_operation_status_ansible_pioneer"
    C_CHECK_OPERATION_STATUS_MENU_NAME[C_EXT_STM_ID_ROLE] = "check_operation_status_ansible_role"
    C_CHECK_OPERATION_STATUS_MENU_NAME[C_EXT_STM_ID_TERRAFORM] = "check_operation_status_terraform_cloud_ep"
    C_CHECK_OPERATION_STATUS_MENU_NAME[C_EXT_STM_ID_TERRAFORM_CLI] = "check_operation_status_terraform_cli"

class TD_B_CICD_GIT_PROTOCOL_TYPE_NAME():
    """
    Gitプロトコルマスタ
    """

    C_GIT_PROTOCOL_TYPE_ROW_ID_HTTPS          = "1"  # https
    C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_PASS       = "2"  # ssh(パスワード認証)
    C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_KEY        = "3"  # ssh(鍵認証パスフレーズあり)
    C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_KEY_NOPASS = "4"  # ssh(鍵認証パスフレーズなし)


class TD_B_CICD_GIT_REPOSITORY_TYPE_NAME():
    """
    Gitリポジトリタイプマスタ
    """

    C_GIT_REPO_TYPE_ROW_ID_PUBLIC  = "1"  # public
    C_GIT_REPO_TYPE_ROW_ID_PRIVATE = "2"  # private


class TD_B_CICD_MATERIAL_LINK_LIST():
    """
    資材紐付管理  自動同期状態
    """

    C_AUTO_SYNC_FLG_ON  = "1"  # 有効
    C_AUTO_SYNC_FLG_OFF = "2"  # 無効
