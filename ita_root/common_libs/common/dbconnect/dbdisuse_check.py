# Copyright 2022 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from flask import g

from common_libs.common.dbconnect import *
from common_libs.common.exception import AppException


def is_db_disuse():
    '''
       databace (workspace/organization) disuse check
       Arguments:
       Returns:
         True:  database disuse
         False: database use
    '''
    organization_id = g.get('ORGANIZATION_ID')
    workspace_id = g.get('WORKSPACE_ID')

    try:

        ita_db = DBConnectCommon()
        org_rows = ita_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE `DISUSE_FLAG`=0 AND `ORGANIZATION_ID`=%s", [organization_id])

        if org_rows is None:
            org_rows = []
        if len(org_rows) == 0:
            g.applogger.debug(org_rows)
            return True
        ita_db.db_disconnect

        org_db = DBConnectOrg(organization_id)
        wk_rows = org_db.table_select("T_COMN_WORKSPACE_DB_INFO", "WHERE `DISUSE_FLAG`=0 AND `WORKSPACE_ID`=%s", [workspace_id])
        if wk_rows is None:
            wk_rows = []
        if len(wk_rows) == 0:
            g.applogger.debug(wk_rows)
            return True
        org_db.db_disconnect

        return False

    except AppException as e:
        # 例外は無視
        return False
    except Exception as e:
        # 例外は無視
        return False
