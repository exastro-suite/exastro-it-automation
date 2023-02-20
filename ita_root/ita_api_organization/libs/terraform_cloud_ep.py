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
from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from flask import g  # noqa: F401
from libs.organization_common import check_auth_menu  # noqa: F401
from common_libs.api import check_request_body_key  # noqa: F401
from common_libs.terraform_driver.cloud_ep.RestApiCaller import RestApiCaller


def check_organization(objdbca, tf_organization_name):
    """
        連携先Terraformから対象のOrganizationの連携状態を確認する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = []
    t_tere_organization = 'T_TERE_ORGANIZATION'
    registered_flag = False
    updated_flag = False
    msg = ''

    # 対象のorganiation_nameのレコードを取得
    target_record = objdbca.table_select(t_tere_organization, 'WHERE ORGANIZATION_NAME = %s AND DISUSE_FLAG = %s', [tf_organization_name, 0])
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
    v_tere_organization_workspace_list = 'V_TERE_ORGANIZATION_WORKSPACE_LINK'
    organization_registered_flag = False
    registered_flag = False
    updated_flag = False

    # 対象のorganiation_name, workspace_nameのレコードを取得
    target_record = objdbca.table_select(v_tere_organization_workspace_list, 'WHERE ORGANIZATION_NAME = %s AND WORKSPACE_NAME = %s AND DISUSE_FLAG = %s', [tf_organization_name, tf_workspace_name, 0])  # noqa: E501
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
        raise AppException("499-01106", [tf_organization_name], [tf_organization_name])  # noqa: F405

    # 連携先TerraformからWorkspaceの一覧を取得
    workspace_list = get_workspace_list(objdbca, target_organization_name)
    for workspace_data in workspace_list:
        if target_workspace_name == workspace_data.get('tf_workspace_name'):
            # 一致しているOrganization名があれば登録済みフラグをTrue
            registered_flag = True
            if target_version:
                if target_version != workspace_data.get('terraform_version'):
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

    # インターフェース情報からRESTAPI実行に必要な値を取得
    interface_info_data = get_intarface_info_data(objdbca)
    protocol = interface_info_data.get('protocol')
    hostname = interface_info_data.get('hostname')
    port_no = interface_info_data.get('port_no')
    encrypted_user_token = interface_info_data.get('user_token')
    proxy_address = interface_info_data.get('proxy_address')
    proxy_port = interface_info_data.get('proxy_port')
    proxy_setting = {'address': proxy_address, "port": proxy_port}

    # RESTAPI Call Class呼び出し
    restApiCaller = RestApiCaller(protocol, hostname, port_no, encrypted_user_token, proxy_setting)

    # トークンをセット
    response_array = restApiCaller.authorize()
    if not response_array['success']:
        # システムエラー
        raise AppException("999-99999", [], [])  # noqa: F405

    # RESTAPIコール
    api_uri = '/organizations'
    response_array = restApiCaller.rest_call('GET', api_uri)
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
                organization_data = {'tf_organization_name': tf_organization_name, 'email_address': email_address}
                return_data.append(organization_data)
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

    return return_data


def get_workspace_list(objdbca, tf_organization_name):
    """
        連携先TerraformからWorkspace一覧の取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    return_data = []

    # インターフェース情報からRESTAPI実行に必要な値を取得
    interface_info_data = get_intarface_info_data(objdbca)
    protocol = interface_info_data.get('protocol')
    hostname = interface_info_data.get('hostname')
    port_no = interface_info_data.get('port_no')
    encrypted_user_token = interface_info_data.get('user_token')
    proxy_address = interface_info_data.get('proxy_address')
    proxy_port = interface_info_data.get('proxy_port')
    proxy_setting = {'address': proxy_address, "port": proxy_port}

    # RESTAPI Call Class呼び出し
    restApiCaller = RestApiCaller(protocol, hostname, port_no, encrypted_user_token, proxy_setting)

    # トークンをセット
    response_array = restApiCaller.authorize()
    if not response_array['success']:
        # システムエラー
        raise AppException("999-99999", [], [])  # noqa: F405

    # RESTAPIコール
    api_uri = '/organizations/%s/workspaces' % (tf_organization_name)
    response_array = restApiCaller.rest_call('GET', api_uri)
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
                tf_workspace_name = attributes['name']
                terraform_version = attributes['terraform-version']
                # 返却値を作成
                workspace_data = {'tf_workspace_name': tf_workspace_name, 'terraform_version': terraform_version}
                return_data.append(workspace_data)
    else:
        # 異常系
        raise AppException("499-01101", [], [])  # noqa: F405

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
    interface_info_data = get_intarface_info_data(objdbca)
    protocol = interface_info_data.get('protocol')
    hostname = interface_info_data.get('hostname')
    port_no = interface_info_data.get('port_no')
    encrypted_user_token = interface_info_data.get('user_token')
    proxy_address = interface_info_data.get('proxy_address')
    proxy_port = interface_info_data.get('proxy_port')
    proxy_setting = {'address': proxy_address, "port": proxy_port}

    # RESTAPI Call Class呼び出し
    restApiCaller = RestApiCaller(protocol, hostname, port_no, encrypted_user_token, proxy_setting)

    # トークンをセット
    response_array = restApiCaller.authorize()
    if not response_array['success']:
        # システムエラー
        raise AppException("999-99999", [], [])  # noqa: F405

    # contentsを作成
    tf_organization_name = parameters.get('tf_organization_name')
    email_address = parameters.get('email_address')
    request_contents = {
        "data": {
            "type": "organizations",
            "attributes": {
                "name": tf_organization_name,
                "email": email_address
            }
        }
    }

    # RESTAPIコール
    api_uri = '/organizations'
    response_array = restApiCaller.rest_call('POST', api_uri, request_contents)
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
    interface_info_data = get_intarface_info_data(objdbca)
    protocol = interface_info_data.get('protocol')
    hostname = interface_info_data.get('hostname')
    port_no = interface_info_data.get('port_no')
    encrypted_user_token = interface_info_data.get('user_token')
    proxy_address = interface_info_data.get('proxy_address')
    proxy_port = interface_info_data.get('proxy_port')
    proxy_setting = {'address': proxy_address, "port": proxy_port}

    # RESTAPI Call Class呼び出し
    restApiCaller = RestApiCaller(protocol, hostname, port_no, encrypted_user_token, proxy_setting)

    # トークンをセット
    response_array = restApiCaller.authorize()
    if not response_array['success']:
        # システムエラー
        raise AppException("999-99999", [], [])  # noqa: F405

    # contentsを作成
    execution_mode = True  # リモート実行モードをしようするかどうか。ITAからWorkspaceを作成する際はTrue固定とする
    auto_apply = False  # Planが成功した際に自動でApplyを実行するかどうか。ITAからWorkspaceを作成する際はFalse固定とする
    working_directory = ''  # Terraformが実行される相対パス。ITAからWorkspaceを作成する際は空欄固定とする。
    tf_workspace_name = parameters.get('tf_workspace_name')
    terraform_version = parameters.get('terraform_version') or ''
    request_contents = {
        "data": {
            "type": "workspaces",
            "attributes": {
                "name": tf_workspace_name,
                "operations": execution_mode,
                "auto-apply": auto_apply,
                "terraform-version": terraform_version,
                "working-directory": working_directory
            }
        }
    }

    # RESTAPIコール
    api_uri = '/organizations/%s/workspaces' % (tf_organization_name)
    response_array = restApiCaller.rest_call('POST', api_uri, request_contents)
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
    interface_info_data = get_intarface_info_data(objdbca)
    protocol = interface_info_data.get('protocol')
    hostname = interface_info_data.get('hostname')
    port_no = interface_info_data.get('port_no')
    encrypted_user_token = interface_info_data.get('user_token')
    proxy_address = interface_info_data.get('proxy_address')
    proxy_port = interface_info_data.get('proxy_port')
    proxy_setting = {'address': proxy_address, "port": proxy_port}

    # RESTAPI Call Class呼び出し
    restApiCaller = RestApiCaller(protocol, hostname, port_no, encrypted_user_token, proxy_setting)

    # トークンをセット
    response_array = restApiCaller.authorize()
    if not response_array['success']:
        # システムエラー
        raise AppException("999-99999", [], [])  # noqa: F405

    # contentsを作成
    email_address = parameters.get('email_address')
    request_contents = {
        "data": {
            "type": "organizations",
            "attributes": {
                "name": tf_organization_name,
                "email": email_address
            }
        }
    }

    # RESTAPIコール
    api_uri = '/organizations/%s' % (tf_organization_name)
    response_array = restApiCaller.rest_call('PATCH', api_uri, request_contents)
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
    interface_info_data = get_intarface_info_data(objdbca)
    protocol = interface_info_data.get('protocol')
    hostname = interface_info_data.get('hostname')
    port_no = interface_info_data.get('port_no')
    encrypted_user_token = interface_info_data.get('user_token')
    proxy_address = interface_info_data.get('proxy_address')
    proxy_port = interface_info_data.get('proxy_port')
    proxy_setting = {'address': proxy_address, "port": proxy_port}

    # RESTAPI Call Class呼び出し
    restApiCaller = RestApiCaller(protocol, hostname, port_no, encrypted_user_token, proxy_setting)

    # トークンをセット
    response_array = restApiCaller.authorize()
    if not response_array['success']:
        # システムエラー
        raise AppException("999-99999", [], [])  # noqa: F405

    # contentsを作成
    execution_mode = True  # リモート実行モードをしようするかどうか。ITAからWorkspaceを作成する際はTrue固定とする
    auto_apply = False  # Planが成功した際に自動でApplyを実行するかどうか。ITAからWorkspaceを作成する際はFalse固定とする
    working_directory = ''  # Terraformが実行される相対パス。ITAからWorkspaceを作成する際は空欄固定とする。
    terraform_version = parameters.get('terraform_version') or ''
    request_contents = {
        "data": {
            "type": "workspaces",
            "attributes": {
                "operations": execution_mode,
                "auto-apply": auto_apply,
                "terraform-version": terraform_version,
                "working-directory": working_directory
            }
        }
    }

    # RESTAPIコール
    api_uri = '/organizations/%s/workspaces/%s' % (tf_organization_name, tf_workspace_name)
    response_array = restApiCaller.rest_call('PATCH', api_uri, request_contents)
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

    # インターフェース情報からRESTAPI実行に必要な値を取得
    interface_info_data = get_intarface_info_data(objdbca)
    protocol = interface_info_data.get('protocol')
    hostname = interface_info_data.get('hostname')
    port_no = interface_info_data.get('port_no')
    encrypted_user_token = interface_info_data.get('user_token')
    proxy_address = interface_info_data.get('proxy_address')
    proxy_port = interface_info_data.get('proxy_port')
    proxy_setting = {'address': proxy_address, "port": proxy_port}

    # RESTAPI Call Class呼び出し
    restApiCaller = RestApiCaller(protocol, hostname, port_no, encrypted_user_token, proxy_setting)

    # トークンをセット
    response_array = restApiCaller.authorize()
    if not response_array['success']:
        # システムエラー
        raise AppException("999-99999", [], [])  # noqa: F405

    # contentsを作成'
    request_contents = {}

    # RESTAPIコール
    api_uri = '/organizations/%s' % (tf_organization_name)
    response_array = restApiCaller.rest_call('DELETE', api_uri, request_contents)
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

    # インターフェース情報からRESTAPI実行に必要な値を取得
    interface_info_data = get_intarface_info_data(objdbca)
    protocol = interface_info_data.get('protocol')
    hostname = interface_info_data.get('hostname')
    port_no = interface_info_data.get('port_no')
    encrypted_user_token = interface_info_data.get('user_token')
    proxy_address = interface_info_data.get('proxy_address')
    proxy_port = interface_info_data.get('proxy_port')
    proxy_setting = {'address': proxy_address, "port": proxy_port}

    # RESTAPI Call Class呼び出し
    restApiCaller = RestApiCaller(protocol, hostname, port_no, encrypted_user_token, proxy_setting)

    # トークンをセット
    response_array = restApiCaller.authorize()
    if not response_array['success']:
        # システムエラー
        raise AppException("999-99999", [], [])  # noqa: F405

    # contentsを作成'
    request_contents = {}

    # RESTAPIコール
    api_uri = '/organizations/%s/workspaces/%s/actions/safe-delete' % (tf_organization_name, tf_workspace_name)
    response_array = restApiCaller.rest_call('POST', api_uri, request_contents)
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


def get_intarface_info_data(objdbca):
    """
        インターフェース情報からRESTAPIに利用する登録値を取得する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
        RETRUN:
            return_data
    """
    table_name = "T_TERE_IF_INFO"
    ret = objdbca.table_select(table_name, 'WHERE DISUSE_FLAG = %s', [0])
    if not ret:
        # インターフェース情報にレコードが無い場合はエラー
        raise AppException("499-01103", [], [])  # noqa: F405

    protocol = ret[0].get('TERRAFORM_PROTOCOL')
    hostname = ret[0].get('TERRAFORM_HOSTNAME')
    port = ret[0].get('TERRAFORM_PORT')
    user_token = ret[0].get('TERRAFORM_TOKEN')
    proxy_address = ret[0].get('TERRAFORM_PROXY_ADDRESS')
    proxy_port = ret[0].get('TERRAFORM_PROXY_PORT')

    return_data = {
        'protocol': protocol,
        'hostname': hostname,
        'port_no': port,
        'user_token': user_token,
        'proxy_address': proxy_address,
        'proxy_port': proxy_port
    }

    return return_data
