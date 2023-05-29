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
database connection agnet class for organization-db on mariadb
"""

import pymysql.cursors  # https://pymysql.readthedocs.io/en/latable_name/

from flask import g

from .dbconnect_common import DBConnectCommon
from common_libs.common.exception import AppException
from common_libs.common.util import ky_decrypt


class DBConnectOrg(DBConnectCommon):
    """
    database connection agnet class for organization-db on mariadb
    """

    def __init__(self, organization_id=None):
        """
        constructor
        """
        if self._db_con is not None and self._db_con.open is True:
            return True

        if organization_id is None:
            organization_id = g.get('ORGANIZATION_ID')
        self.organization_id = organization_id

        # get db-connect-infomation from organization-db
        common_db = DBConnectCommon()
        connect_info = common_db.get_orgdb_connect_info(organization_id)
        if connect_info is False:
            raise AppException("999-00001", ["ORGANIZATION_ID=" + self.organization_id])

        self._host = connect_info.get('DB_HOST')
        self._port = int(connect_info.get('DB_PORT'))
        self._db_user = connect_info.get('DB_USER')
        self._db_passwd = connect_info.get('DB_PASSWORD')
        self._db = connect_info.get('DB_DATABASE')
        self._inistial_data_ansible_if = connect_info.get('INITIAL_DATA_ANSIBLE_IF')
        self._no_install_driver = connect_info.get('NO_INSTALL_DRIVER')

        # connect database
        self.db_connect()

    def __del__(self):
        """
        destructor
        """
        self.db_disconnect()

    def get_wsdb_connect_info(self, workspace_id):
        """
        get database connect infomation for workspace

        Arguments:
            workspace_id: workspace_id name
        Returns:
            database connect infomation for workspace: dict
            or
            get failure: (bool)False
        """
        isnot_register_db_connect_info = "db_connect_info" not in g or "WSDB_DATABASE" not in g.db_connect_info
        isnot_same_workspace = g.get('WORKSPACE_ID') and g.get('WORKSPACE_ID') != workspace_id
        if isnot_register_db_connect_info or isnot_same_workspace:
            where = "WHERE `WORKSPACE_ID`=%s and `DISUSE_FLAG`=0 LIMIT 1"
            data_list = self.table_select("T_COMN_WORKSPACE_DB_INFO", where, [workspace_id])

            if len(data_list) == 0:
                return False

            return data_list[0]

        return {
            "DB_HOST": g.db_connect_info["WSDB_HOST"],
            "DB_PORT": g.db_connect_info["WSDB_PORT"],
            "DB_USER": g.db_connect_info["WSDB_USER"],
            "DB_PASSWORD": g.db_connect_info["WSDB_PASSWORD"],
            "DB_DATABASE": g.db_connect_info["WSDB_DATABASE"]
        }

    def get_inistial_data_ansible_if(self):
        """
        get inistial_data_ansible_if
        """
        return self._inistial_data_ansible_if

    def get_no_install_driver(self):
        """
        get inistial_data_ansible_if
        """
        return self._no_install_driver


class DBConnectOrgRoot(DBConnectOrg):
    """
    database connection root user agnet class for organization-db on mariadb
    """

    def __init__(self, organization_id=None):
        """
        constructor
        """
        if self._db_con is not None and self._db_con.open is True:
            return True

        if organization_id is None:
            organization_id = g.get('ORGANIZATION_ID')
        self.organization_id = organization_id

        # get db-connect-infomation from ita-common-db
        common_db = DBConnectCommon()
        connect_info = common_db.get_orgdb_connect_info(organization_id)
        if connect_info is False:
            raise AppException("999-00001", ["ORGANIZATION_ID=" + organization_id])

        self._host = connect_info['DB_HOST']
        self._port = int(connect_info['DB_PORT'])
        self._db_user = connect_info['DB_ADMIN_USER']
        self._db_passwd = connect_info['DB_ADMIN_PASSWORD']

        # connect database
        self.db_connect()

    def __del__(self):
        """
        destructor
        """
        self.db_disconnect()

    def db_connect(self):
        """
        connect database

        Returns:
            is success:(bool)
        """
        if self._db_con is not None and self._db_con.open is True:
            return True

        try:
            self._db_con = pymysql.connect(
                host=self._host,
                port=self._port,
                user=self._db_user,
                passwd=ky_decrypt(self._db_passwd),
                charset='utf8',
                cursorclass=pymysql.cursors.DictCursor
            )
        except pymysql.Error as e:
            raise AppException("999-00002", ["ORGANIZATION_ID=" + self.organization_id, e])
        except Exception:
            raise AppException("999-00002", ["ORGANIZATION_ID=" + self.organization_id, "cannot access. connect info may be incorrect"])

        return True

    def database_create(self, db_name):
        """
        create database
        """
        sql = "CREATE DATABASE `{}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin".format(db_name)
        self.sql_execute(sql)

    def database_drop(self, db_name):
        """
        drop database
        """
        sql = "DROP DATABASE IF EXISTS `{}`".format(db_name)
        self.sql_execute(sql)

    def user_create(self, user_name, user_password, db_name):
        """
        create user

        Arguments:
            user_name: user name
            user_password: user_password
            db_name: database name
        """
        sql = "CREATE USER IF NOT EXISTS '{user_name}'@'%' IDENTIFIED BY '{user_password}'".format(user_name=user_name, user_password=user_password)
        self.sql_execute(sql)

        sql = "GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{user_name}'@'%' WITH GRANT OPTION".format(user_name=user_name, db_name=db_name)
        self.sql_execute(sql)

    def user_drop(self, user_name):
        """
        drop user
        """
        sql = "DROP USER IF EXISTS '{}'@'%'".format(user_name)
        self.sql_execute(sql)
