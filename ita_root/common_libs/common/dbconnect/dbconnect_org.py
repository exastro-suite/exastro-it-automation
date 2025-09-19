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

from .dbconnect_common import DBConnectCommon, connect_retry
from common_libs.common.exception import AppException, DBException
from common_libs.common.util import ky_decrypt


class DBConnectOrg(DBConnectCommon):
    """
    database connection agnet class for organization-db on mariadb
    """

    def __init__(self, organization_id=None, retry=None):
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
        common_db.db_disconnect()
        if connect_info is False:
            raise AppException("999-00001", ["ORGANIZATION_ID=" + self.organization_id])

        self._host = connect_info.get('DB_HOST')
        self._port = int(connect_info.get('DB_PORT'))
        self._db_user = connect_info.get('DB_USER')
        self._db_passwd = connect_info.get('DB_PASSWORD')
        self._db_admin_user = connect_info.get('DB_ADMIN_USER')
        self._db_admin_passwd = connect_info.get('DB_ADMIN_PASSWORD')
        self._db = connect_info.get('DB_DATABASE')

        self._mongo_owner = connect_info.get('MONGO_OWNER')
        self._mongo_connection_string = connect_info.get('MONGO_CONNECTION_STRING')
        self._mongo_admin_user = connect_info.get('MONGO_ADMIN_USER')
        self._mongo_admin_password = connect_info.get('MONGO_ADMIN_PASSWORD')

        self._inistial_data_ansible_if = connect_info.get('INITIAL_DATA_ANSIBLE_IF')
        self._no_install_driver = connect_info.get('NO_INSTALL_DRIVER')

        # connect database
        self.db_connect(retry=retry)

    def __del__(self):
        """
        destructor
        """
        self.db_disconnect()

    def get_connect_info(self):
        """
        get infomation for self

        Returns:
            infomation for self: dict
        """
        connect_info = {
            'DB_HOST': self._host,
            'DB_PORT': self._port,
            'DB_USER': self._db_user,
            'DB_PASSWORD': self._db_passwd,
            'DB_DATABASE': self._db,
            'DB_ADMIN_USER': self._db_admin_user,
            'DB_ADMIN_PASSWORD': self._db_admin_passwd,
            'MONGO_OWNER': self._mongo_owner,
            'MONGO_CONNECTION_STRING': self._mongo_connection_string,
            'MONGO_ADMIN_USER': self._mongo_admin_user,
            'MONGO_ADMIN_PASSWORD': self._mongo_admin_password
        }

        return connect_info

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
            "DB_HOST": g.db_connect_info.get("WSDB_HOST"),
            "DB_PORT": g.db_connect_info.get("WSDB_PORT"),
            "DB_USER": g.db_connect_info.get("WSDB_USER"),
            "DB_PASSWORD": g.db_connect_info.get("WSDB_PASSWORD"),
            "DB_DATABASE": g.db_connect_info.get("WSDB_DATABASE"),
            'MONGO_CONNECTION_STRING': g.db_connect_info.get('WS_MONGO_CONNECTION_STRING'),
            'MONGO_DATABASE': g.db_connect_info.get('WS_MONGO_DATABASE'),
            'MONGO_USER': g.db_connect_info.get('WS_MONGO_USER'),
            'MONGO_PASSWORD': g.db_connect_info.get('WS_MONGO_PASSWORD')
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

    def __init__(self, organization_id=None, retry=None):
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
        common_db.db_disconnect()
        if connect_info is False:
            raise AppException("999-00001", ["ORGANIZATION_ID=" + organization_id])

        self._db = None
        self._host = connect_info['DB_HOST']
        self._port = int(connect_info['DB_PORT'])
        self._db_user = connect_info['DB_ADMIN_USER']
        self._db_passwd = connect_info['DB_ADMIN_PASSWORD']

        # connect database
        self.db_connect(retry=retry)

    def __del__(self):
        """
        destructor
        """
        self.db_disconnect()

    @connect_retry
    def db_connect(self, retry=None):
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
                charset='utf8mb4',
                collation='utf8mb4_general_ci',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=self.connect_timeout
            )
        except pymysql.Error as e:
            raise DBException("ORGANIZATION_ID=" + self.organization_id, e)

        return True

    def database_create(self, db_name):
        """
        create database
        """
        sql = "CREATE DATABASE IF NOT EXISTS `{}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin".format(db_name)
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

    def connection_kill(self, db_name, user_name):
        """
        kill connection
        """
        # DBとユーザを指定して、すべてのコネクションを取得する
        sql = "SELECT * FROM INFORMATION_SCHEMA.PROCESSLIST WHERE DB=%s AND USER=%s"
        proccess_list = self.sql_execute(sql, [db_name, user_name])

        # procedureの一覧を取得する
        sql = "SHOW PROCEDURE STATUS WHERE NAME IN (%s, %s)"
        procedure_list = self.sql_execute(sql, ['az_kill', 'rds_kill'])

        # killコマンドを特定する
        kill_sql = "KILL CONNECTION %s"
        for procedure_data in procedure_list:
            if procedure_data.get('Name') == 'az_kill':
                # AzureのMySQL用killコマンド
                kill_sql = "CALL mysql.az_kill(%s)"
                break
            elif procedure_data.get('Name') == 'rds_kill':
                # AWSのMySQL用killコマンド
                kill_sql = "CALL mysql.rds_kill(%s)"
                break

        # コネクションを削除する
        for proccess in proccess_list:
            try:
                self.sql_execute(kill_sql, [proccess['ID']])
            except Exception:
                # プロセスが無くなっている場合はエラーになるので、エラーは無視する
                pass
