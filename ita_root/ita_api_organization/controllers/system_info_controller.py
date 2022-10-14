#   Copyright 2022 NEC Corporation
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

from common_libs.common import *  # noqa: F403
from libs import system_info
from common_libs.api import api_filter


@api_filter
def get_ita_version(organization_id, workspace_id):  # noqa: E501
    """get_ita_version

    ITAのバージョン情報を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse20011
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405
    
    # バージョン情報を取得
    data = system_info.collect_ita_version(objdbca)
    
    return data,
