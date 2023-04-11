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
loglevel_settings_controller
"""
from flask import g
import json

from common_libs.api import api_filter_admin
from common_libs.common.exception import AppException
from common_libs.common.dbconnect import *  # noqa: F403
from libs.admin_common import loglevel_settings_container


@api_filter_admin
def get_all_loglevel_settings():  # noqa: E501
    """get_all_loglevel_settings

    すべてのServiceのログレベルを取得する # noqa: E501

    :rtype: InlineResponse2003
    """

    common_db = DBConnectCommon()  # noqa: F405
    where_str = "WHERE `DISUSE_FLAG`='0'"
    loglevel_service_list = common_db.table_select("T_COMN_LOGLEVEL", where_str)

    if len(loglevel_service_list) == 0:
        result_data = {}
    else:
        result_data = {}
        for loglevel_container in loglevel_service_list:
            log_level = loglevel_container.get('LOG_LEVEL')
            if (log_level is not None) and (len(log_level) > 0):
                result_data[loglevel_container['SERVICE_NAME']] = log_level
            else:
                result_data[loglevel_container['SERVICE_NAME']] = None

    return result_data,


@api_filter_admin
def post_all_setting_loglevel(body=None):  # noqa: E501
    """post_all_setting_loglevel

    複数のServiceのログレベルを更新する # noqa: E501

    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse200
    """

    common_db = DBConnectCommon()  # noqa: F405
    parameter = body
    loglevel_settings_container(common_db, parameter)

    return g.appmsg.get_api_message("000-00001"),
