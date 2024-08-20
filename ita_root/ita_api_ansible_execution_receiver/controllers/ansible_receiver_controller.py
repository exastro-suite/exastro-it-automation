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
import six  # noqa: F401

from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common import menu_info
from common_libs.api import api_filter
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from ita_api_ansible_execution_receiver.libs import ansible_controll
from common_libs.api import api_filter, api_filter_download_file
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
        result_data = ansible_controll.unexecuted_instance(objdbca, organization_id, workspace_id)
        # result_data.setdefault("menu_info", tmp_data[0]["data"])
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def get_execution_status(organization_id, workspace_id, execution_no, start_sh_result):  # noqa: E501
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

        # 作業実行関連のメニューの基本情報および項目情報の取得
        result_data = ansible_controll.get_execution_status(objdbca, organization_id, workspace_id, execution_no, start_sh_result)
        # result_data.setdefault("menu_info", tmp_data[0]["data"])
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter_download_file
def get_populated_data(organization_id, workspace_id, execution_no, start_sh_result):  # noqa: E501
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

        # 作業実行関連のメニューの基本情報および項目情報の取得
        result_data = ansible_controll.get_populated_data(objdbca, organization_id, workspace_id, execution_no, start_sh_result)
        # result_data.setdefault("menu_info", tmp_data[0]["data"])
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,