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
from flask import g
import traceback
from common_libs.common.dbconnect import *
from common_libs.api import api_filter_admin
from common_libs.common.exception import AppException


@api_filter_admin
def internal_health_check_liveness():
    try:
        common_db_root = DBConnectCommonRoot()  # noqa: F405
        organization_info_list = common_db_root.sql_execute("SELECT 1 AS DATA", [])
        common_db_root.db_disconnect()
    except AppException as e:
        raise AppException(e)
    except Exception as e:
        raise Exception(e)

    return g.appmsg.get_api_message("000-00000"),


@api_filter_admin
def internal_health_check_readiness():
    return internal_health_check_liveness(),
