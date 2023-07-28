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
"""
controller
maintenance_mode_setting_controller
"""
from flask import g
import json

from common_libs.api import api_filter_admin
# from common_libs.common.exception import AppException
from common_libs.common.dbconnect import *  # noqa: F403
from libs.admin_common import maintenance_mode_update


@api_filter_admin
def get_maintenance_mode_setting():  # noqa: E501
    """get_maintenance_mode_setting

    メンテナンスモード設定状態を取得する # noqa: E501

    :rtype: InlineResponse2004
    """
    common_db = DBConnectCommon()  # noqa: F405
    where_str = "WHERE `DISUSE_FLAG`='0'"
    maintenance_mode_list = common_db.table_select("T_COMN_MAINTENANCE_MODE", where_str)

    # メンテナンスモードの設定状態を返却
    if len(maintenance_mode_list) == 0:
        result_data = {}
    else:
        result_data = {}
        for maintenance_mode_container in maintenance_mode_list:
            mode_name = maintenance_mode_container.get('MODE_NAME')
            result_data[mode_name] = {}
            result_data[mode_name]["SETTING_VALUE"] = maintenance_mode_container.get('SETTING_VALUE')
            result_data[mode_name]["LAST_UPDATE_USER"] = maintenance_mode_container.get('LAST_UPDATE_USER')
            result_data[mode_name]["LAST_UPDATE_TIMESTAMP"] = maintenance_mode_container.get('LAST_UPDATE_TIMESTAMP')

    return result_data,


@api_filter_admin
def patch_maintenance_mode_setting(body=None):  # noqa: E501
    """patch_maintenance_mode_setting

    メンテナンスモードの設定状態を更新する # noqa: E501

    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse200
    """
    common_db = DBConnectCommon()  # noqa: F405
    parameter = body
    maintenance_mode_update(common_db, parameter)

    return g.appmsg.get_api_message("000-00001"),
