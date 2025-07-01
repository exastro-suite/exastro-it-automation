# Copyright 2024 NEC Corporation#
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
database connection agnet class for temporary workspace db on mariadb
"""
from flask import g

from .dbconnect_common import DBConnectCommon
from .dbconnect_org import DBConnectOrg
from .dbconnect_ws import DBConnectWs
from common_libs.common.exception import AppException


class DBConnectWsSandbox(DBConnectWs):
    """
    database connection agnet class for temporary workspace db on mariadb
    """

    _workspace_id = ""

    def __init__(self, user=None, passwd=None, database=None, mode_ss=None, retry=None):
        """
        constructor

        Arguments:
            user: login user
            passwd: login password
            database: database name
        """
        if self._db_con is not None and self._db_con.open is True:
            return True

        organization_id = g.get('ORGANIZATION_ID')
        self.organization_id = organization_id

        workspace_id = g.get('WORKSPACE_ID')
        self._workspace_id = workspace_id

        # get db-connect-infomation from organization-db
        org_db = DBConnectOrg(organization_id)
        connect_info = org_db.get_wsdb_connect_info(workspace_id)
        org_db.db_disconnect()
        if connect_info is False:
            db_info = "WORKSPACE_ID=" + workspace_id
            db_info = "ORGANIZATION_ID=" + organization_id + "," + db_info if organization_id else db_info
            raise AppException("999-00001", [db_info])

        self._host = connect_info['DB_HOST']
        self._port = int(connect_info['DB_PORT'])
        self._db_user = connect_info['DB_USER'] if user is None else user
        self._db_passwd = connect_info['DB_PASSWORD'] if passwd is None else passwd
        self._db = connect_info['DB_DATABASE'] if database is None else database

        # connect database
        self.db_connect(mode_ss=mode_ss, retry = retry)
