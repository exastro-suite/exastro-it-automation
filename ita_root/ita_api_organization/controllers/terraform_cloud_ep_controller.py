#   Copyright 2023 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import connexion
from common_libs.common import *  # noqa: F403
from common_libs.api import api_filter
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from libs import terraform_cloud_ep


@api_filter
def check_terraform_organization(organization_id, workspace_id, tf_organization_name):  # noqa: E501
    """check_terraform_organization

    対象のOrganizatinoの連携状態を確認する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'organization_list_terraform_cloud_ep'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    data, msg = terraform_cloud_ep.check_organization(objdbca, tf_organization_name)

    return data, msg


@api_filter
def check_terraform_workspace(organization_id, workspace_id, tf_organization_name, tf_workspace_name):  # noqa: E501
    """check_terraform_workspace

    対象のWorkspaceの連携状態を確認する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str
    :param tf_workspace_name: Terraform Workspace Name
    :type tf_workspace_name: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'workspace_list_terraform_cloud_ep'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    data, msg = terraform_cloud_ep.check_workspace(objdbca, tf_organization_name, tf_workspace_name)

    return data, msg


@api_filter
def create_terraform_organization(organization_id, workspace_id, body=None):  # noqa: E501
    """create_terraform_organization

    連携しているTerraform Cloud/EnterpriseにOrganizationを作成する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'organization_list_terraform_cloud_ep'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    parameters = {"tf_organization_name": "", "email_address": ""}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameters = body

    data = terraform_cloud_ep.create_organization(objdbca, parameters)

    return data,


@api_filter
def create_terraform_workspace(organization_id, workspace_id, tf_organization_name, body=None):  # noqa: E501
    """create_terraform_workspace

    連携しているTerraform Cloud/EnterpriseにWorkspaceを作成する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'workspace_list_terraform_cloud_ep'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    parameters = {"workspace_name": "", "terraform_version": ""}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameters = body

    data = terraform_cloud_ep.create_workspace(objdbca, tf_organization_name, parameters)

    return data,


@api_filter
def delete_terraform_organization(organization_id, workspace_id, tf_organization_name):  # noqa: E501
    """delete_terraform_organization

    連携しているTerraform Cloud/Enterpriseに登録されているOrganizationを削除する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'organization_list_terraform_cloud_ep'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    data = terraform_cloud_ep.delete_organization(objdbca, tf_organization_name)

    return data,


@api_filter
def delete_terraform_policy(organization_id, workspace_id, tf_organization_name, policy_name):  # noqa: E501
    """delete_terraform_policy

    連携しているTerraform Cloud/EnterpriseからPolicyを削除する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str
    :param policy_name: Policy Name
    :type policy_name: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'linked_terraform_management'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['24']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # 連携先TerraformからPolicyを削除
    data = terraform_cloud_ep.delete_policy(objdbca, tf_organization_name, policy_name)

    return data,


@api_filter
def delete_terraform_policy_set(organization_id, workspace_id, tf_organization_name, policy_set_name):  # noqa: E501
    """delete_terraform_policy_set

    連携しているTerraform Cloud/EnterpriseからPolicySetを削除する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str
    :param policy_set_name: Policy Name
    :type policy_set_name: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'linked_terraform_management'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['24']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # 連携先TerraformからPolicyを削除
    data = terraform_cloud_ep.delete_policy_set(objdbca, tf_organization_name, policy_set_name)

    return data,


@api_filter
def delete_terraform_policy_set_relationship_policy(organization_id, workspace_id, tf_organization_name, policy_set_name, policy_name):  # noqa: E501
    """delete_terraform_policy_set_relationship_policy

    連携しているTerraform Cloud/EnterpriseからPolicySetとPolicyの紐付けを解除する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str
    :param policy_set_name: Policy Name
    :type policy_set_name: str
    :param policy_name: Terraform Workspace Name
    :type policy_name: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'linked_terraform_management'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['24']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # PolicySetからPolicyの紐付け削除
    data = terraform_cloud_ep.policy_set_remove_policy(objdbca, tf_organization_name, policy_set_name, policy_name)

    return data,


@api_filter
def delete_terraform_policy_set_relationship_workspace(organization_id, workspace_id, tf_organization_name, policy_set_name, tf_workspace_name):  # noqa: E501
    """delete_terraform_policy_set_relationship_workspace

    連携しているTerraform Cloud/EnterpriseからPolicySetとWorkspaceの紐付けを解除する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str
    :param policy_set_name: Policy Name
    :type policy_set_name: str
    :param tf_workspace_name: Terraform Workspace Name
    :type tf_workspace_name: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'linked_terraform_management'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['24']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # PolicySetからWorkspaceの紐付け削除
    data = terraform_cloud_ep.policy_set_remove_workspace(objdbca, tf_organization_name, policy_set_name, tf_workspace_name)

    return data,


@api_filter
def delete_terraform_workspace(organization_id, workspace_id, tf_organization_name, tf_workspace_name):  # noqa: E501
    """delete_terraform_workspace

    連携しているTerraform Cloud/Enterpriseに登録されているWorkspaceを削除する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str
    :param tf_workspace_name: Terraform Workspace Name
    :type tf_workspace_name: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'workspace_list_terraform_cloud_ep'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    data = terraform_cloud_ep.delete_workspace(objdbca, tf_organization_name, tf_workspace_name)

    return data,


@api_filter
def get_terraform_organization_list(organization_id, workspace_id):  # noqa: E501
    """get_terraform_organization_list

    連携しているTerraform Cloud/EnterpriseからOrganizationの一覧を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'linked_terraform_management'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['24']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # Organization一覧の取得
    data = terraform_cloud_ep.get_organization_list(objdbca)

    return data,


@api_filter
def get_terraform_policy_file(organization_id, workspace_id, tf_organization_name, policy_name, body=None):  # noqa: E501
    """get_terraform_policy_file

    連携しているTerraform Cloud/EnterpriseからPolicyコードをダウンロードする # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str
    :param policy_name: Policy Name
    :type policy_name: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'linked_terraform_management'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['24']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    parameters = {"download_path": ""}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameters = body

    # Policyコードの取得
    data = terraform_cloud_ep.get_policy_file(objdbca, tf_organization_name, policy_name, parameters)

    return data,


@api_filter
def get_terraform_policy_list(organization_id, workspace_id):  # noqa: E501
    """get_terraform_policy_list

    連携しているTerraform Cloud/EnterpriseからPolicyの一覧を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'linked_terraform_management'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['24']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # Policy一覧の取得
    data = terraform_cloud_ep.get_policy_list(objdbca)

    return data,


@api_filter
def get_terraform_policy_set_list(organization_id, workspace_id):  # noqa: E501
    """get_terraform_policy_set_list

    連携しているTerraform Cloud/EnterpriseからPolicySetの一覧を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'linked_terraform_management'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['24']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # PolicySet一覧の取得
    data = terraform_cloud_ep.get_policy_set_list(objdbca)

    return data,


@api_filter
def get_terraform_workspace_list(organization_id, workspace_id):  # noqa: E501
    """get_terraform_workspace_list

    連携しているTerraform Cloud/EnterpriseからWorkspaceの一覧を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'workspace_list_terraform_cloud_ep'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # Workspace一覧の取得
    data = terraform_cloud_ep.get_workspace_list(objdbca)

    return data,


@api_filter
def update_terraform_organization(organization_id, workspace_id, tf_organization_name, body=None):  # noqa: E501
    """update_terraform_organization

    連携しているTerraform Cloud/Enterpriseに登録されているOrganizationを更新する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'organization_list_terraform_cloud_ep'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    parameters = {"email_address": ""}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameters = body

    data = terraform_cloud_ep.update_organization(objdbca, tf_organization_name, parameters)
    return data,


@api_filter
def update_terraform_workspace(organization_id, workspace_id, tf_organization_name, tf_workspace_name, body=None):  # noqa: E501
    """update_terraform_workspace

    連携しているTerraform Cloud/Enterpriseに登録されているWorkspaceを更新する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param tf_organization_name: Terraform Organization Name
    :type tf_organization_name: str
    :param tf_workspace_name: Terraform Workspace Name
    :type tf_workspace_name: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2006
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メニューの存在確認
    menu = 'workspace_list_terraform_cloud_ep'
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    parameters = {"terraform_version": ""}
    if connexion.request.is_json:
        body = dict(connexion.request.get_json())
        parameters = body

    data = terraform_cloud_ep.update_workspace(objdbca, tf_organization_name, tf_workspace_name, parameters)
    return data,
