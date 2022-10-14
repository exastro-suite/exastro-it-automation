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
"""
database connection agent module for workspace-db on mariadb
"""
from flask import g

from .dbconnect_common import DBConnectCommon
from .dbconnect_org import DBConnectOrg
from common_libs.common.exception import AppException


class DBConnectWs(DBConnectCommon):
    """
    database connection agnet class for workspace-db on mariadb
    """

    _workspace_id = ""

    def __init__(self, workspace_id=None, organization_id=None):
        """
        constructor

        Arguments:
            workspace_id: workspace id
        """
        if self._db_con is not None and self._db_con.open is True:
            return True

        if workspace_id is None:
            workspace_id = g.get('WORKSPACE_ID')
        self._workspace_id = workspace_id

        # get db-connect-infomation from organization-db
        org_db = DBConnectOrg(organization_id)
        connect_info = org_db.get_wsdb_connect_info(workspace_id)
        if connect_info is False:
            db_info = "WORKSPACE_ID=" + workspace_id
            db_info = "ORGANIZATION_ID=" + organization_id + "," + db_info if organization_id else db_info
            raise AppException("999-00001", [db_info])

        self._host = connect_info['DB_HOST']
        self._port = int(connect_info['DB_PORT'])
        self._db_user = connect_info['DB_USER']
        self._db_passwd = connect_info['DB_PASSWORD']
        self._db = connect_info['DB_DATADBASE']

        # connect database
        self.db_connect()

    def __del__(self):
        """
        destructor
        """
        self.db_disconnect()

    def table_insert(self, table_name, data_list, primary_key_name, is_register_history=True):
        return super().table_insert(table_name, data_list, primary_key_name, is_register_history)

    def table_update(self, table_name, data_list, primary_key_name, is_register_history=True):
        return super().table_update(table_name, data_list, primary_key_name, is_register_history)
