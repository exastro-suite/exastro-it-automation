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
backyard_execute_check_controller
"""
from flask import g
import json

from common_libs.api import api_filter_admin
from common_libs.common.exception import AppException
from common_libs.common.dbconnect import *  # noqa: F403
from libs.admin_common import get_backyard_execute_status_list


@api_filter_admin
def get_backyard_execute_check():  # noqa: E501
    """get_backyard_execute_check

    すべてのバックヤードの実行状態を一括取得する # noqa: E501


    :rtype: InlineResponse2005
    """
    backyard_execute_status_list = get_backyard_execute_status_list()
    return_data = backyard_execute_status_list

    return return_data,
