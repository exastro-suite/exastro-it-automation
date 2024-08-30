#   Copyright 2024 NEC Corporation
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
from common_libs.common.dbconnect import DBConnectWs
from common_libs.api import api_filter, api_filter_download_file, check_request_body, check_request_body_key
from libs.ansible_execution import * # noqa: F403
from flask import g


@api_filter
def get_unexecuted_instance(organization_id, workspace_id):  # noqa: E501
    """get_unexecuted_instance

    未実行インスタンス確認 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2006
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:

        # 作業実行関連のメニューの基本情報および項目情報の取得
        result_data = unexecuted_instance(objdbca)
        # result_data.setdefault("menu_info", tmp_data[0]["data"])
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def execution_status_notification(organization_id, workspace_id, execution_no, body):  # noqa: E501
    """get_unexecuted_instance

    作業状態通知 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2006
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # bodyのjson形式チェック
        check_request_body()

        if connexion.request.is_json:
            body = dict(connexion.request.get_json())
            check_request_body_key(body, 'driver_id')  # keyが無かったら400-00002エラー
            check_request_body_key(body, 'status')

        # 作業実行関連のメニューの基本情報および項目情報の取得
        result_data = get_execution_status(objdbca, execution_no, body)
        # result_data.setdefault("menu_info", tmp_data[0]["data"])
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter_download_file
def get_populated_data(organization_id, workspace_id, execution_no, driver_id):  # noqa: E501
    """get_populated_data

    投入データ取得 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param execution_no: 作業番号
    :type execution_no: str

    :rtype: InlineResponse2006
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # 作業実行関連のメニューの基本情報および項目情報の取得
        result_data = get_populated_data_path(objdbca, organization_id, workspace_id, execution_no, driver_id)
        # result_data.setdefault("menu_info", tmp_data[0]["data"])
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,

@api_filter_download_file
def update_result_data(organization_id, workspace_id, execution_no, body):  # noqa: E501
    """update_result_data

    結果データ更新 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param execution_no: 作業番号

    :rtype: InlineResponse2006
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # bodyのjson形式チェック
        check_request_body()

        if connexion.request.is_json:
            body = dict(connexion.request.get_json())
            check_request_body_key(body, 'driver_id')  # keyが無かったら400-00002エラー
            check_request_body_key(body, 'status')

        # 作業実行関連のメニューの基本情報および項目情報の取得
        result_data = update_result_data(organization_id, workspace_id, execution_no, body)
        # result_data.setdefault("menu_info", tmp_data[0]["data"])
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def agent_version(organization_id, workspace_id, body):  # noqa: E501
    """update_result_data

    バージョン通知 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2006
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # DB接続
        objdbca = DBConnectWs(workspace_id)  # noqa: F405

        # bodyのjson形式チェック
        check_request_body()

        if connexion.request.is_json:
            body = dict(connexion.request.get_json())
            check_request_body_key(body, 'agent_name')  # keyが無かったら400-00002エラー
            check_request_body_key(body, 'version')

        # エージェント名とバージョン情報を取得
        result_data = get_agent_version(objdbca, body)
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,

@api_filter
def execution_notification(organization_id, workspace_id, body):  # noqa: E501
    """execution_notification

    作業中通知 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2006
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        result_data = update_ansible_agent_status_file(organization_id, workspace_id, body)
        # result_data.setdefault("menu_info", tmp_data[0]["data"])
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,