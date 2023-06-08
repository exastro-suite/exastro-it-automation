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

import json
import base64
from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from flask import g  # noqa: F401
from libs.organization_common import check_auth_menu  # noqa: F401
from common_libs.api import check_request_body_key  # noqa: F401
# from common_libs.terraform_driver.cloud_ep.RestApiCaller import RestApiCaller
from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
from common_libs.terraform_driver.cloud_ep.terraform_restapi import *  # noqa: F403


def check_organization(objdbca, tf_organization_name):
    """
        連携先Terraformから対象のOrganizationの連携状態を確認する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = []
    registered_flag = False
    updated_flag = False
    msg = ''

    # 対象のorganiation_nameのレコードを取得
    where_str = 'WHERE ORGANIZATION_NAME = %s AND DISUSE_FLAG = %s'
    target_record = objdbca.table_select(TFCloudEPConst.T_ORGANIZATION, where_str, [tf_organization_name, 0])
    if not target_record:
        # 対象のOrganization名のレコードが存在しない（廃止されている）場合
        raise AppException("499-01104", [tf_organization_name], [tf_organization_name])  # noqa: F405
    target_organization_name = tf_organization_name
    target_email = target_record[0].get('EMAIL_ADDRESS')

    # 連携先TerraformからOrganizationの一覧を取得
    organization_list = get_organization_list(objdbca)
    for organization_data in organization_list:
        if target_organization_name == organization_data.get('tf_organization_name'):
            # 一致しているOrganization名があれば登録済みフラグをTrue
            registered_flag = True
            if target_email != organization_data.get('email_address'):
                # メールアドレスが一致していない場合更新済みフラグをTrue
                updated_flag = True

    # 一覧から対象の有無と、登録内容を比較する
    if not registered_flag:
        # 未登録パターンの返却値
        return_data = {'registar_status': 0, 'update_status': 0}
        msg = g.appmsg.get_api_message("MSG-80001", [tf_organization_name])
    else:
        if not updated_flag:
            # 登録済みパターンの返却値
            return_data = {'registar_status': 1, 'update_status': 0}
            msg = g.appmsg.get_api_message("MSG-80002", [tf_organization_name])
        else:
            # 更新ありパターンの返却値
            return_data = {'registar_status': 1, 'update_status': 1}
            msg = g.appmsg.get_api_message("MSG-80003", [tf_organization_name])

    return return_data, msg


def check_workspace(objdbca, tf_organization_name, tf_workspace_name):
    """
        連携先Terraformから対象のWorkspaceの連携状態を確認する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = []
    msg = ""
    organization_registered_flag = False
    registered_flag = False
    updated_flag = False

    # 対象のorganiation_name, workspace_nameのレコードを取得
    where_str = 'WHERE ORGANIZATION_NAME = %s AND WORKSPACE_NAME = %s AND DISUSE_FLAG = %s'
    target_record = objdbca.table_select(TFCloudEPConst.V_ORGANIZATION_WORKSPACE, where_str, [tf_organization_name, tf_workspace_name, 0])  # noqa: E501
    if not target_record:
        # 対象のOrganization名, Workspace名のレコードが存在しない（廃止されている）場合
        raise AppException("499-01105", [tf_organization_name, tf_workspace_name], [tf_organization_name, tf_workspace_name])  # noqa: F405
    target_organization_name = tf_organization_name
    target_workspace_name = tf_workspace_name
    target_version = target_record[0].get('TERRAFORM_VERSION')

    # 連携先TerraformからOrganizationの一覧を取得
    organization_list = get_organization_list(objdbca)
    for organization_data in organization_list:
        if target_organization_name == organization_data.get('tf_organization_name'):
            # 一致しているOrganization名があれば登録済みフラグをTrue
            organization_registered_flag = True

    if not organization_registered_flag:
        # 対象のOrganizationが連携先Terraformに存在しない場合
        raise AppException("499-01108", [tf_organization_name], [tf_organization_name])  # noqa: F405

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # 連携先TerraformからWorkspaceの一覧を取得
    response_array = get_tf_workspace_list(restApiCaller, tf_organization_name)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        # 正常系
        respons_contents_json = response_array.get('responseContents')
        if respons_contents_json:
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                attributes = data.get('attributes')
                if target_workspace_name == attributes.get('name'):
                    registered_flag = True
                    if target_version:
                        if target_version != attributes.get('terraform-version'):
                            updated_flag = True

    # 一覧から対象の有無と、登録内容を比較する
    if not registered_flag:
        # 未登録パターンの返却値
        return_data = {'registar_status': 0, 'update_status': 0}
        msg = g.appmsg.get_api_message("MSG-80004", [tf_workspace_name])
    else:
        if not updated_flag:
            # 登録済みパターンの返却値
            return_data = {'registar_status': 1, 'update_status': 0}
            msg = g.appmsg.get_api_message("MSG-80005", [tf_workspace_name])
        else:
            # 更新ありパターンの返却値
            return_data = {'registar_status': 1, 'update_status': 1}
            msg = g.appmsg.get_api_message("MSG-80006", [tf_workspace_name])

    return return_data, msg


def get_organization_list(objdbca):
    """
        連携先TerraformからOrganization一覧の取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = []
    ita_organization_data = {}

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # ITAに登録されているOrganization一覧を取得
    where_str = 'WHERE DISUSE_FLAG = %s'
    t_tere_organization_records = objdbca.table_select(TFCloudEPConst.T_ORGANIZATION, where_str, [0])
    for record in t_tere_organization_records:
        tf_organization_name = record.get('ORGANIZATION_NAME')
        email_address = record.get('EMAIL_ADDRESS')
        ita_organization_data[tf_organization_name] = {'tf_organization_name': tf_organization_name, 'email_address': email_address}

    # RESTAPIコール
    response_array = get_tf_organization_list(restApiCaller)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        # 正常系
        respons_contents_json = response_array.get('responseContents')
        if respons_contents_json:
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                # organization名とemailを格納
                attributes = data['attributes']
                tf_organization_name = attributes['name']
                email_address = attributes['email']
                # 返却値を作成
                ita_organization_data_target = ita_organization_data.get(tf_organization_name)
                organization_data = {'tf_organization_name': tf_organization_name, 'email_address': email_address}
                # ITAに登録済みかどうかを判定する
                if ita_organization_data_target:
                    organization_data['ita_registered'] = True
                else:
                    organization_data['ita_registered'] = False

                return_data.append(organization_data)
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    return return_data


def get_workspace_list(objdbca):
    """
        連携先TerraformからWorkspace一覧の取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = []
    ita_workspace_data = {}

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # ITAに登録されているOrganization:Workspace一覧を取得
    where_str = 'WHERE DISUSE_FLAG = %s'
    v_organization_workspace_records = objdbca.table_select(TFCloudEPConst.V_ORGANIZATION_WORKSPACE, where_str, [0])
    for record in v_organization_workspace_records:
        tf_organization_name = record.get('ORGANIZATION_NAME')
        tf_workspace_name = record.get('WORKSPACE_NAME')
        ita_workspace_data[tf_workspace_name] = {'tf_organization_name': tf_organization_name, 'tf_workspace_name': tf_workspace_name}

    # Organization一覧取得RESTAPIコール
    tf_organization_list = []
    response_array = get_tf_organization_list(restApiCaller)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        # 正常系
        respons_contents_json = response_array.get('responseContents')
        if respons_contents_json:
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                # organization名を格納
                attributes = data['attributes']
                tf_organization_name = attributes['name']
                # 返却値を作成
                tf_organization_list.append(tf_organization_name)
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    # Workspace一覧取得RESTAPIコール
    tf_workspace_list = []
    for tf_organization_name in tf_organization_list:
        response_array = get_tf_workspace_list(restApiCaller, tf_organization_name)  # noqa: F405
        response_status_code = response_array.get('statusCode')
        if response_status_code == 200:
            # 正常系
            respons_contents_json = response_array.get('responseContents')
            if respons_contents_json:
                respons_contents = json.loads(respons_contents_json)
                respons_contents_data = respons_contents.get('data')
                for data in respons_contents_data:
                    # workspace名とversionを格納
                    attributes = data['attributes']
                    tf_workspace_name = attributes['name']
                    terraform_version = attributes['terraform-version']
                    # 返却値を作成
                    ita_workspace_data_target = ita_workspace_data.get(tf_workspace_name)
                    workspace_data = {'tf_organization_name': tf_organization_name, 'tf_workspace_name': tf_workspace_name, 'terraform_version': terraform_version}  # noqa: E501
                    # ITAに登録済みかどうかを判定する
                    if ita_workspace_data_target:
                        if ita_workspace_data_target.get('tf_organization_name') == tf_organization_name:
                            workspace_data['ita_registered'] = True
                        else:
                            workspace_data['ita_registered'] = False
                    else:
                        workspace_data['ita_registered'] = False
                    tf_workspace_list.append(workspace_data)

        else:
            # 異常系
            raise AppException("499-01101", [], [])  # noqa: F405

    return_data = tf_workspace_list

    return return_data


def create_organization(objdbca, parameters):
    """
        連携先TerraformにOrganizationを作成する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = {}

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # parameterを取得
    tf_organization_name = parameters.get('tf_organization_name')
    email_address = parameters.get('email_address')

    # RESTAPIコール
    response_array = create_tf_organization(restApiCaller, tf_organization_name, email_address)  # noqa: F405
    response_status_code = response_array.get('statusCode')

    if response_status_code == 201:
        # 正常系
        respons_contents_json = response_array.get('responseContents')
        if respons_contents_json:
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            attributes = respons_contents_data.get('attributes')
            external_id = attributes.get('external-id')
            created_organization_name = attributes.get('name')
            created_organization_email = attributes.get('email')
            # 返却値を作成
            return_data = {
                'external_id': external_id,
                'tf_organization_name': created_organization_name,
                'email_address': created_organization_email
            }
    elif response_status_code == 404 or response_status_code == 401:
        # 異常系(アクセス・認証系)
        raise AppException("499-01101", [], [])  # noqa: F405
    else:
        # 異常系(その他)
        response_contents = response_array.get('responseContents')
        error_message = response_contents.get('errorMessage')
        raise AppException("499-01102", [error_message], [error_message])  # noqa: F405

    return return_data


def create_workspace(objdbca, tf_organization_name, parameters):
    """
        連携先TerraformにWorkspaceを作成する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = {}

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # parameterを取得
    tf_workspace_name = parameters.get('tf_workspace_name')
    terraform_version = parameters.get('terraform_version') or ''

    # RESTAPIコール
    response_array = create_tf_workspace(restApiCaller, tf_organization_name, tf_workspace_name, terraform_version)  # noqa: F405
    response_status_code = response_array.get('statusCode')

    if response_status_code == 201:
        # 正常系
        respons_contents_json = response_array.get('responseContents')
        if respons_contents_json:
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            attributes = respons_contents_data.get('attributes')
            created_workspace_id = respons_contents_data.get('id')
            created_workspace_name = attributes.get('name')
            created_workspace_version = attributes.get('terraform-version')
            # 返却値を作成
            return_data = {
                'workspace_id': created_workspace_id,
                'tf_workspace_name': created_workspace_name,
                'terraform_version': created_workspace_version
            }
    elif response_status_code == 404 or response_status_code == 401:
        # 異常系(アクセス・認証系)
        raise AppException("499-01101", [], [])  # noqa: F405
    else:
        # 異常系(その他)
        response_contents = response_array.get('responseContents')
        error_message = response_contents.get('errorMessage')
        raise AppException("499-01102", [error_message], [error_message])  # noqa: F405

    return return_data


def update_organization(objdbca, tf_organization_name, parameters):
    """
        連携先TerraformのOrganizationを更新する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = {}

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # parameterを取得
    email_address = parameters.get('email_address')

    # RESTAPIコール
    response_array = update_tf_organization(restApiCaller, tf_organization_name, email_address)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        # 正常系
        respons_contents_json = response_array.get('responseContents')
        if respons_contents_json:
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            attributes = respons_contents_data.get('attributes')
            external_id = attributes.get('external-id')
            updated_organization_name = attributes.get('name')
            updated_organization_email = attributes.get('email')
            # 返却値を作成
            return_data = {
                'external_id': external_id,
                'tf_organization_name': updated_organization_name,
                'email_address': updated_organization_email
            }
    elif response_status_code == 404 or response_status_code == 401:
        # 異常系(アクセス・認証系)
        raise AppException("499-01101", [], [])  # noqa: F405
    else:
        # 異常系(その他)
        response_contents = response_array.get('responseContents')
        error_message = response_contents.get('errorMessage')
        raise AppException("499-01102", [error_message], [error_message])  # noqa: F405

    return return_data


def update_workspace(objdbca, tf_organization_name, tf_workspace_name, parameters):
    """
        連携先TerraformのWorkspaceを更新する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = {}

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # parameterを取得
    terraform_version = parameters.get('terraform_version') or ''

    # RESTAPIコール
    response_array = update_tf_workspace(restApiCaller, tf_organization_name, tf_workspace_name, terraform_version)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        # 正常系
        respons_contents_json = response_array.get('responseContents')
        if respons_contents_json:
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            attributes = respons_contents_data.get('attributes')
            update_workspace_id = respons_contents_data.get('id')
            updated_workspace_name = attributes.get('name')
            updated_workspace_version = attributes.get('terraform-version')
            # 返却値を作成
            return_data = {
                'workspace_id': update_workspace_id,
                'tf_workspace_name': updated_workspace_name,
                'terraform_version': updated_workspace_version
            }
    elif response_status_code == 404 or response_status_code == 401:
        # 異常系(アクセス・認証系)
        raise AppException("499-01101", [], [])  # noqa: F405
    else:
        # 異常系(その他)
        response_contents = response_array.get('responseContents')
        error_message = response_contents.get('errorMessage')
        raise AppException("499-01102", [error_message], [error_message])  # noqa: F405

    return return_data


def delete_organization(objdbca, tf_organization_name):
    """
        連携先TerraformのOrganizationを削除する。
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = {}

    # 対象のorganiation_nameのレコードを取得
    where_str = 'WHERE ORGANIZATION_NAME = %s AND DISUSE_FLAG = %s'
    target_record = objdbca.table_select(TFCloudEPConst.T_ORGANIZATION, where_str, [tf_organization_name, 0])
    if not target_record:
        # 対象のOrganization名のレコードが存在しない（廃止されている）場合
        raise AppException("499-01104", [tf_organization_name], [tf_organization_name])  # noqa: F405

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # RESTAPIコール
    response_array = delete_tf_organization(restApiCaller, tf_organization_name)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 204:
        # 正常系
        return_data = {}
    elif response_status_code == 404 or response_status_code == 401:
        # 異常系(アクセス・認証系)
        raise AppException("499-01101", [], [])  # noqa: F405
    else:
        # 異常系(その他)
        response_contents = response_array.get('responseContents')
        error_message = response_contents.get('errorMessage')
        raise AppException("499-01102", [error_message], [error_message])  # noqa: F405

    return return_data


def delete_workspace(objdbca, tf_organization_name, tf_workspace_name):
    """
        連携先TerraformのWorkspaceを削除する。ただし「Sage Delete」で行うため、Workspaceで作成したリソースが残っている場合は削除できない。
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = {}

    # 対象のorganiation_name, workspace_nameのレコードを取得
    where_str = 'WHERE ORGANIZATION_NAME = %s AND WORKSPACE_NAME = %s AND DISUSE_FLAG = %s'
    target_record = objdbca.table_select(TFCloudEPConst.V_ORGANIZATION_WORKSPACE, where_str, [tf_organization_name, tf_workspace_name, 0])  # noqa: E501
    if not target_record:
        # 対象のOrganization名, Workspace名のレコードが存在しない（廃止されている）場合
        raise AppException("499-01105", [tf_organization_name, tf_workspace_name], [tf_organization_name, tf_workspace_name])  # noqa: F405

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # RESTAPIコール
    response_array = delete_tf_workspace(restApiCaller, tf_organization_name, tf_workspace_name)  # noqa: F405
    response_status_code = response_array.get('statusCode')

    if response_status_code == 204 or response_status_code == 200:
        # 正常系
        return_data = {}
    elif response_status_code == 404 or response_status_code == 401:
        # 異常系(アクセス・認証系)
        raise AppException("499-01101", [], [])  # noqa: F405
    else:
        # 異常系(その他)
        response_contents = response_array.get('responseContents')
        error_message = response_contents.get('errorMessage')
        raise AppException("499-01102", [error_message], [error_message])  # noqa: F405

    return return_data


def delete_policy(objdbca, tf_organization_name, policy_name):
    """
        連携先TerraformからPolicyを削除する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = []
    tf_manage_policy_id = None

    # 対象のpolicy_nameのレコードを取得
    where_str = 'WHERE POLICY_NAME = %s AND DISUSE_FLAG = %s'
    target_record = objdbca.table_select(TFCloudEPConst.T_POLICY, where_str, [policy_name, 0])
    if not target_record:
        # 対象のPolicy名のレコードが存在しない（廃止されている）場合
        raise AppException("499-01106", [policy_name], [policy_name])  # noqa: F405

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # Policy一覧を取得し、対象のIDを特定
    response_array = get_tf_policy_list(restApiCaller, tf_organization_name)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        respons_contents_json = response_array.get('responseContents')
        respons_contents = json.loads(respons_contents_json)
        respons_contents_data = respons_contents.get('data')
        for data in respons_contents_data:
            policy_attributest = data.get('attributes')
            name = policy_attributest.get('name')
            if name == policy_name:
                tf_manage_policy_id = data.get('id')
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    if not tf_manage_policy_id:
        # 対象のPolicyが連携先Terraformに存在しない
        raise AppException("499-01100", [policy_name], [policy_name])  # noqa: F405

    # Policy削除RESTAPIを実行
    response_array = delete_tf_policy(restApiCaller, tf_manage_policy_id)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 204:
        return_data = []
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    return return_data


def delete_policy_set(objdbca, tf_organization_name, policy_set_name):
    """
        連携先TerraformからPolicySetを削除する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = []
    tf_manage_policy_set_id = None

    # 対象のpolicy_set_nameのレコードを取得
    where_str = 'WHERE POLICY_SET_NAME = %s AND DISUSE_FLAG = %s'
    target_record = objdbca.table_select(TFCloudEPConst.T_POLICYSET, where_str, [policy_set_name, 0])
    if not target_record:
        # 対象のPolicySet名のレコードが存在しない（廃止されている）場合
        raise AppException("499-01107", [tf_organization_name], [tf_organization_name])  # noqa: F405

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # PolicySet一覧を取得し、対象のIDを特定
    response_array = get_tf_policy_set_list(restApiCaller, tf_organization_name)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        respons_contents_json = response_array.get('responseContents')
        respons_contents = json.loads(respons_contents_json)
        respons_contents_data = respons_contents.get('data')
        for data in respons_contents_data:
            policy_attributest = data.get('attributes')
            name = policy_attributest.get('name')
            if name == policy_set_name:
                tf_manage_policy_set_id = data.get('id')
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    if not tf_manage_policy_set_id:
        # 対象のPolicySetが連携先Terraformに存在しない
        raise AppException("499-01111", [policy_set_name], [policy_set_name])  # noqa: F405

    # Policy削除RESTAPIを実行
    response_array = delete_tf_policy_set(restApiCaller, tf_manage_policy_set_id)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 204:
        return_data = []
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    return return_data


def get_policy_list(objdbca):
    """
        連携先TerraformからPolicy一覧の取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = []

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # Organization一覧取得RESTAPIコール
    tf_organization_list = []
    response_array = get_tf_organization_list(restApiCaller)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        # 正常系
        respons_contents_json = response_array.get('responseContents')
        if respons_contents_json:
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                # organization名を格納
                attributes = data['attributes']
                tf_organization_name = attributes['name']
                # 返却値を作成
                tf_organization_list.append(tf_organization_name)
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    # ITAに登録されているPolicy一覧を取得
    where_str = 'WHERE DISUSE_FLAG = %s'
    ret = objdbca.table_select(TFCloudEPConst.T_POLICY, where_str, [0])
    ita_policy_list = []
    for record in ret:
        ita_policy_list.append(record.get('POLICY_NAME'))

    # Organizationに紐づくPolicy一覧を取得
    tf_policy_list = []
    for tf_organization_name in tf_organization_list:
        response_array = get_tf_policy_list(restApiCaller, tf_organization_name)  # noqa: F405
        response_status_code = response_array.get('statusCode')
        if response_status_code == 200:
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                policy_detail = {}
                policy_attributest = data.get('attributes')
                policy_links = data.get('links')
                name = policy_attributest.get('name')
                download = policy_links.get('download')
                policy_detail = {'tf_organization_name': tf_organization_name, 'policy_name': name}
                if name in ita_policy_list:
                    policy_detail['ita_registered'] = True
                    policy_detail['download_path'] = download
                else:
                    policy_detail['ita_registered'] = False
                    policy_detail['download_path'] = None
                tf_policy_list.append(policy_detail)
        else:
            # 異常系
            raise AppException("499-01101", [], [])  # noqa: F405

    return_data = tf_policy_list

    return return_data


def get_policy_file(objdbca, tf_organization_name, policy_name, parameters):
    """
        連携先TerraformからPolicyコードを取得する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = {}
    file = None

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # download
    download_path = parameters.get('download_path')
    if not download_path:
        raise AppException("400-00002", ['download_path'], ['download_path'])  # noqa: F405

    # policyファイルを取得
    responseContents = policy_file_download(restApiCaller, download_path, False)  # noqa: F405

    # ファイル名を作成
    file_name = str(policy_name) + '.sentinel'

    # ファイルをエンコード
    if responseContents:
        file = base64.b64encode(responseContents.encode('utf-8')).decode()

    return_data = {'file_name': file_name, 'file': file}

    return return_data


def get_policy_set_list(objdbca):  # noqa: C901
    """
        連携先TerraformからPolicyeSet一覧の取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = []

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # Organization一覧取得RESTAPIコール
    tf_organization_list = []
    response_array = get_tf_organization_list(restApiCaller)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        # 正常系
        respons_contents_json = response_array.get('responseContents')
        if respons_contents_json:
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                # organization名を格納
                attributes = data['attributes']
                tf_organization_name = attributes['name']
                # 返却値を作成
                tf_organization_list.append(tf_organization_name)
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    # Organizationに紐づくWorkspace一覧を取得(idを名前に変換する目的)
    tf_workspace_dict = {}
    for tf_organization_name in tf_organization_list:
        response_array = get_tf_workspace_list(restApiCaller, tf_organization_name)  # noqa: F405
        response_status_code = response_array.get('statusCode')
        if response_status_code == 200:
            # 正常系
            respons_contents_json = response_array.get('responseContents')
            if respons_contents_json:
                respons_contents = json.loads(respons_contents_json)
                respons_contents_data = respons_contents.get('data')
                for data in respons_contents_data:
                    workspace_attributes = data['attributes']
                    id = data.get('id')
                    name = workspace_attributes['name']
                    tf_workspace_dict[id] = name
        else:
            # 異常系
            raise AppException("499-01101", [], [])  # noqa: F405

    # Organizationに紐づくPolicy一覧を取得(idを名前に変換する目的)
    tf_policy_dict = {}
    for tf_organization_name in tf_organization_list:
        response_array = get_tf_policy_list(restApiCaller, tf_organization_name)  # noqa: F405
        response_status_code = response_array.get('statusCode')
        if response_status_code == 200:
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                policy_attributest = data.get('attributes')
                id = data.get('id')
                name = policy_attributest.get('name')
                tf_policy_dict[id] = name
        else:
            # 異常系
            raise AppException("499-01101", [], [])  # noqa: F405

    # ITAに登録されているWorkspace一覧を取得
    where_str = 'WHERE DISUSE_FLAG = %s'
    ret = objdbca.table_select(TFCloudEPConst.T_WORKSPACE, where_str, [0])
    ita_workspace_list = []
    for record in ret:
        ita_workspace_list.append(record.get('WORKSPACE_NAME'))

    # ITAに登録されているPolicy一覧を取得
    where_str = 'WHERE DISUSE_FLAG = %s'
    ret = objdbca.table_select(TFCloudEPConst.T_POLICY, where_str, [0])
    ita_policy_list = []
    for record in ret:
        ita_policy_list.append(record.get('POLICY_NAME'))

    # ITAに登録されているPolicySet一覧を取得
    where_str = 'WHERE DISUSE_FLAG = %s'
    ret = objdbca.table_select(TFCloudEPConst.T_POLICYSET, where_str, [0])
    ita_policy_set_list = []
    for record in ret:
        ita_policy_set_list.append(record.get('POLICY_SET_NAME'))

    # Organizationに紐づくPolicySet一覧を取得
    tf_policy_set_list = []
    for tf_organization_name in tf_organization_list:
        response_array = get_tf_policy_set_list(restApiCaller, tf_organization_name)  # noqa: F405
        response_status_code = response_array.get('statusCode')
        if response_status_code == 200:
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                policy_set_detail = {}
                policy_set_attributest = data.get('attributes')
                relationships = data.get('relationships')
                name = policy_set_attributest.get('name')
                policy_set_detail = {'tf_organization_name': tf_organization_name, 'policy_set_name': name}

                # policySetがITAに登録されているかどうかの判定
                if name in ita_policy_set_list:
                    policy_set_detail['ita_registered'] = True
                else:
                    policy_set_detail['ita_registered'] = False

                # policySetに紐づくWorkspaceの情報
                ps_ws_dict = {}
                policy_set_workspace = relationships.get('workspaces')
                for ps_ws_data in policy_set_workspace.get('data'):
                    ws_id = ps_ws_data.get('id')
                    ws_name = tf_workspace_dict.get(ws_id)
                    # workspaceがITAに登録されているかどうかの判定
                    if ws_name in ita_workspace_list:
                        ps_ws_dict[ws_name] = {'ita_registered': True}
                    else:
                        ps_ws_dict[ws_name] = {'ita_registered': False}
                policy_set_detail['workspace'] = ps_ws_dict

                # policySetに紐づくPolicyの情報
                ps_pl_dict = {}
                policy_set_policy = relationships.get('policies')
                for ps_pl_data in policy_set_policy.get('data'):
                    pl_id = ps_pl_data.get('id')
                    pl_name = tf_policy_dict.get(pl_id)
                    # policyがITAに登録されているかどうかの判定
                    if pl_name in ita_policy_list:
                        ps_pl_dict[pl_name] = {'ita_registered': True}
                    else:
                        ps_pl_dict[pl_name] = {'ita_registered': False}
                policy_set_detail['policy'] = ps_pl_dict

                tf_policy_set_list.append(policy_set_detail)

        else:
            # 異常系
            raise AppException("499-01101", [], [])  # noqa: F405

    return_data = tf_policy_set_list

    return return_data


def policy_set_remove_policy(objdbca, tf_organization_name, policy_set_name, policy_name):
    """
        連携先TerraformのPolicyeSetからPolicyの紐付けを解除する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = {}
    tf_manage_policy_set_id = None
    tf_manage_policy_id = None

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # PolicySet一覧を取得し、対象のPolicySetIDを特定する
    response_array = get_tf_policy_set_list(restApiCaller, tf_organization_name)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        respons_contents_json = response_array.get('responseContents')
        respons_contents = json.loads(respons_contents_json)
        respons_contents_data = respons_contents.get('data')
        for data in respons_contents_data:
            policy_set_attributest = data.get('attributes')
            name = policy_set_attributest.get('name')
            if name == policy_set_name:
                tf_manage_policy_set_id = data.get('id')
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    if not tf_manage_policy_set_id:
        # 対象のPolicySetが連携先Terraformに存在しない
        raise AppException("499-01111", [policy_set_name], [policy_set_name])  # noqa: F405

    # Policy一覧を取得し、対象のPolicyIDを特定する
    response_array = get_tf_policy_list(restApiCaller, tf_organization_name)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        respons_contents_json = response_array.get('responseContents')
        respons_contents = json.loads(respons_contents_json)
        respons_contents_data = respons_contents.get('data')
        for data in respons_contents_data:
            policy_attributest = data.get('attributes')
            name = policy_attributest.get('name')
            if name == policy_name:
                tf_manage_policy_id = data.get('id')
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    if not tf_manage_policy_id:
        # 対象のPolicyが連携先Terraformに存在しない
        raise AppException("499-01110", [policy_name], [policy_name])  # noqa: F405

    # policy用のbodyを作成
    policy_data = {"data": [{"id": tf_manage_policy_id, "type": "policies"}]}

    # policySetからWorkspaceの紐付けを解除する
    response_array = delete_relationships_policy(restApiCaller, tf_manage_policy_set_id, policy_data)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 204 or response_status_code == 200:
        # 正常系
        return_data = {}
    elif response_status_code == 404 or response_status_code == 401:
        # 異常系(アクセス・認証系)
        raise AppException("499-01101", [], [])  # noqa: F405
    else:
        # 異常系(その他)
        response_contents = response_array.get('responseContents')
        error_message = response_contents.get('errorMessage')
        raise AppException("499-01102", [error_message], [error_message])  # noqa: F405

    return return_data


def policy_set_remove_workspace(objdbca, tf_organization_name, policy_set_name, tf_workspace_name):
    """
        連携先TerraformのPolicyeSetからWorkspaceの紐付けを解除する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = {}
    tf_manage_workspace_id = None
    tf_manage_policy_set_id = None

    # インターフェース情報からRESTAPI実行に必要な値を取得
    ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
    if not ret:
        raise AppException("499-01103", [], [])  # noqa: F405

    # RESTAPIコールクラス
    ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
    if not ret:
        raise AppException("999-99999", [], [])  # noqa: F405

    # Workspace一覧を取得し、対象のWorkspaceIDを特定する
    response_array = get_tf_workspace_list(restApiCaller, tf_organization_name)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        # 正常系
        respons_contents_json = response_array.get('responseContents')
        if respons_contents_json:
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                workspace_attributes = data['attributes']
                name = workspace_attributes['name']
                if name == tf_workspace_name:
                    tf_manage_workspace_id = data.get('id')
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    if not tf_manage_workspace_id:
        # 対象のWorkspaceが連携先Terraformに存在しない
        raise AppException("499-01109", [tf_workspace_name], [tf_workspace_name])  # noqa: F405

    # PolicySet一覧を取得し、対象のPolicySetIDを特定する
    response_array = get_tf_policy_set_list(restApiCaller, tf_organization_name)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 200:
        respons_contents_json = response_array.get('responseContents')
        respons_contents = json.loads(respons_contents_json)
        respons_contents_data = respons_contents.get('data')
        for data in respons_contents_data:
            policy_set_attributest = data.get('attributes')
            name = policy_set_attributest.get('name')
            if name == policy_set_name:
                tf_manage_policy_set_id = data.get('id')
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    if not tf_manage_policy_set_id:
        # 対象のPolicySetが連携先Terraformに存在しない
        raise AppException("499-01111", [policy_set_name], [policy_set_name])  # noqa: F405

    # policySetからWorkspaceの紐付けを解除する
    response_array = delete_relationships_workspace(restApiCaller, tf_manage_policy_set_id, tf_manage_workspace_id)  # noqa: F405
    response_status_code = response_array.get('statusCode')
    if response_status_code == 204 or response_status_code == 200:
        # 正常系
        return_data = {}
    elif response_status_code == 404 or response_status_code == 401:
        # 異常系(アクセス・認証系)
        raise AppException("499-01101", [], [])  # noqa: F405
    else:
        # 異常系(その他)
        response_contents = response_array.get('responseContents')
        error_message = response_contents.get('errorMessage')
        raise AppException("499-01102", [error_message], [error_message])  # noqa: F405

    return return_data
