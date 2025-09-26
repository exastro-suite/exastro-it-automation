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
database connection agnet module for ita-common-db on mariadb
"""
import pymysql.cursors  # https://pymysql.readthedocs.io/en/latable_name/
import pymysql
import uuid
import os
import re
import time

from flask import g

from common_libs.common.exception import AppException, DBException
from common_libs.common.util import get_timestamp, ky_decrypt, ky_encrypt, generate_secrets


def connect_retry(db_connect):
    def wrapper(*args, **kwargs):
        # retryしたときのインターバル
        sleep_time = float(os.environ.get("DB_CONNECT_RETRY_SLEEP_TIME", 0.5))
        # retry回数 優先順位は、db_connectに直接引数としてコードで指定がある場合 -> 環境変数 -> コードのデフォルト値
        retry = kwargs["retry"] if "retry" in kwargs else None
        retry_limit = int(os.environ.get("DB_CONNECT_RETRY_LIMIT", 2)) if retry is None else retry
        retry_count = 0

        while True:
            try:
                retBool = db_connect(*args, **kwargs)

                if retBool is True:
                    g.dbConnectError = False
                    break
            except DBException as e:
                apl_msg_arg = e.args[0]
                error_code = e.args[1]  # DBのエラーコード

                retry_error_list = [
                    -2, # Name or service not known
                    2003 # Can't connect to MySQL server (timed out / Connection refused)
                ]
                if error_code in retry_error_list:
                    if retry_count == retry_limit:
                        g.dbConnectError = True
                        raise AppException("999-00002", [apl_msg_arg, e])

                    g.applogger.warning(e)
                    retry_count += 1

                    time.sleep(sleep_time)
                    continue

                g.dbConnectError = True
                raise AppException("999-00002", [apl_msg_arg, e])

    return wrapper

class DBConnectCommon:
    """
    database connection agnet class for ita-common-db on mariadb
    """
    _db_con = None  # database connection

    _is_transaction = False  # state of transaction
    _COLUMN_NAME_TIMESTAMP = 'LAST_UPDATE_TIMESTAMP'

    connect_timeout = int(os.environ.get("DB_CONNECT_TIMEOUT", 10))
    retry = None

    def __init__(self, mode_ss=None, retry=None):
        """
        constructor
        """
        if self._db_con is not None and self._db_con.open is True:
            return True

        self._db = os.environ.get('DB_DATABASE')
        self._host = os.environ.get('DB_HOST')
        self._port = int(os.environ.get('DB_PORT'))
        self._db_user = os.environ.get('DB_USER')
        self._db_passwd = ky_encrypt(os.environ.get('DB_PASSWORD'))

        # connect database
        self.db_connect(mode_ss=mode_ss, retry=retry)

    def __del__(self):
        """
        destructor
        """
        self.db_disconnect()

    @connect_retry
    def db_connect(self, mode_ss=None, retry=None):
        """
        connect database

        Returns:
            is success:(bool)
        """
        if self._db_con is not None and self._db_con.open is True:
            return True

        try:
            _cursorclass = pymysql.cursors.SSDictCursor if mode_ss is True else pymysql.cursors.DictCursor
            self._db_con = pymysql.connect(
                host=self._host,
                port=self._port,
                user=self._db_user,
                passwd=ky_decrypt(self._db_passwd),
                database=self._db,
                charset='utf8mb4',
                collation='utf8mb4_general_ci',
                cursorclass=_cursorclass,
                local_infile=True,
                connect_timeout=self.connect_timeout,
            )
        except pymysql.Error as e:
            raise DBException(self._db, e)

        return True

    def db_disconnect(self):
        """
        disconnect database
        """
        if self._db_con is not None and self._db_con.open is True:
            self._db_con.close()

        self._db_con = None
        self._is_transaction = False

    def db_transaction_start(self):
        """
        begin

        Returns:
            is success:(bool)
        """
        res = False
        if self._db_con.open is True and self._is_transaction is False:
            try:
                self._db_con.begin()
                res = True
            except pymysql.Error as e:
                raise AppException("999-00003", [self._db, "BEGIN", e])

            if res is True:
                self._is_transaction = True

        return res

    def db_transaction_end(self, flg):
        """
        transaction end

        Arguments:
            flg: True(1):commit, False(0):rollback
        Returns:
            is success:(bool)
        """
        res = False
        if self._db_con.open is True:
            if flg is True:
                res = self.db_commit()
            else:
                res = self.db_rollback()
        return res

    def db_commit(self):
        """
        commit

        Returns:
            is success:(bool)
        """
        res = False
        if self._db_con.open is True and self._is_transaction is True:
            try:
                self._db_con.commit()
                res = True
            except pymysql.Error as e:
                raise AppException("999-00003", [self._db, "COMMIT", e])

            if res is True:
                self._is_transaction = False

        return res

    def db_rollback(self):
        """
        rollback

        Returns:
            is success:(bool)
        """
        res = False
        if self._db_con.open is True and self._is_transaction is True:
            try:
                self._db_con.rollback()
                res = True
            except pymysql.Error as e:
                raise AppException("999-00003", [self._db, "ROLLBACK", e])

            if res is True:
                self._is_transaction = False
        return res

    def sqlfile_execute(self, file_name):
        """
        read sql file and execute sql

        Arguments:
            file_name: sql file path
        """
        # #2079 /storage配下ではないので対象外
        with open(file_name, "r") as f:
            sql_list = f.read().split(";\n")
            for sql in sql_list:
                if re.fullmatch(r'[\s\n\r]*', sql) is None:
                    self.sql_execute(sql)

    def sql_execute(self, sql, bind_value_list=[]):
        """
        execute sql

        Arguments:
            sql: sql statement ex."SELECT * FROM table_name WHERE name = %s and number = %s"
            bind_value_list: list or tuple or dict ex.["hoge taro", 5]
        Returns:
            table data list: list(tuple)
        """
        db_cursor = self._db_con.cursor()

        # escape
        if len(bind_value_list) == 0:
            sql = self.prepared_val_escape(sql)
        else:
            # convert list→tupple
            if isinstance(bind_value_list, list):
                bind_value_list = tuple(bind_value_list)

        try:
            db_cursor.execute(sql, bind_value_list)
            self.__sql_debug(db_cursor, sql, bind_value_list)
        except pymysql.Error as e:
            last_executed = sql % (bind_value_list)
            if self._db_con.open is True and db_cursor is not None and db_cursor._executed is not None:
                last_executed = db_cursor._executed
            raise AppException("999-00003", [self._db, last_executed, e])

        data_list = list(db_cursor.fetchall())  # counter plan for 0 data
        db_cursor.close()

        return data_list

    def __sql_debug(self, db_cursor, sql, bind_value_list=[]):
        """
        print last_execute_sql

        Arguments:
            db_cursor: db cursor
        """
        if os.environ.get("DEBUUG_SQL") != "1":
            return

        last_executed = sql % (bind_value_list)
        if self._db_con.open is True and db_cursor is not None and db_cursor._executed is not None:
            last_executed = db_cursor._executed
        print(last_executed)

    def table_columns_get(self, table_name):
        """
        get table column name list

        Arguments:
            table_name: table name
        Returns:
            tupple(column_name_list, primary_key_name)
                column name list: ex.['id', 'name', 'number']
                primary_key list: ex.['id']
        """
        sql = "SHOW COLUMNS FROM `{}`".format(table_name)
        data_list = self.sql_execute(sql)

        column_list = []
        primary_key_list = []
        for data in data_list:
            # print(data)
            column_list.append(data['Field'])
            if data['Key'] == 'PRI':
                primary_key_list.append(data['Field'])

        return (column_list, primary_key_list)

    def table_select(self, table_name, where_str="", bind_value_list=[]):
        """
        select table

        Arguments:
            table_name: table name
            where_str: sql statement of WHERE sentence ex."WHERE name = %s and number = %s"
            bind_value_list: value list ex.["hoge taro", 5]
        Returns:
            table data list: list(tuple)
        """
        where_str = " {}".format(where_str) if where_str else ""
        sql = "SELECT * FROM `{}`{}".format(table_name, where_str)
        data_list = self.sql_execute(sql, bind_value_list)

        return data_list

    def table_count(self, table_name, where_str="", bind_value_list=[]):
        """
        select count table

        Arguments:
            table_name: table name
            where_str: sql statement of WHERE sentence ex."WHERE name = %s and number = %s"
            bind_value_list: value list ex.["hoge taro", 5]
        Returns:
            data count: int
        """
        where_str = " {}".format(where_str) if where_str else ""
        sql = "SELECT COUNT(*) FROM `{}`{}".format(table_name, where_str)
        data_list = self.sql_execute(sql, bind_value_list)

        for data in data_list:
            for res in data.values():
                return res

    def table_exists(self, table_name, where_str="", bind_value_list=[]):
        """
        select exists table

        Arguments:
            table_name: table name
            where_str: sql statement of WHERE sentence ex."WHERE name = %s and number = %s"
            bind_value_list: value list ex.["hoge taro", 5]
        Returns:
            boolean: true: exists / false: not exists
        """
        where_str = " {}".format(where_str) if where_str else ""
        sql = "SELECT EXISTS (SELECT 1 FROM `{}`{}) AS RET".format(table_name, where_str)
        result = self.sql_execute(sql, bind_value_list)

        # 結果確認 / Check results
        if result[0]["RET"] == 1:
            return True
        else:
            return False

    def table_insert(self, table_name, data_list, primary_key_name, is_register_history=False):
        """
        insert table

        Arguments:
            data_list: data list for insert ex.[{"name":"なまえ", "number":"3"}]
            primary_key_name: primary key column name
            is_register_history: (bool)is register history table
        Returns:
            table data list: list(tuple)
            or
            update failure: (bool)False
        """
        if isinstance(data_list, dict):
            data_list = [data_list]

        self.db_transaction_start()

        is_last_res = True
        for data in data_list:
            # auto set
            timestamp = get_timestamp()
            if primary_key_name not in data or not data[primary_key_name]:
                data[primary_key_name] = str(self._uuid_create())
            data[self._COLUMN_NAME_TIMESTAMP] = timestamp

            # make sql statement
            column_list = list(data.keys())
            prepared_list = ["%s"]*len(column_list)
            value_list = list(data.values())

            sql = "INSERT INTO `{}` ({}) VALUES ({})".format(table_name, ','.join(column_list), ','.join(prepared_list))
            res = self.sql_execute(sql, value_list)
            if res is False:
                is_last_res = False
                break

            if is_register_history is False:
                continue
            # insert history table
            history_table_name = table_name + "_JNL"
            add_data = self._get_history_table_data("INSERT", timestamp)
            # make history data
            history_data = dict(data, **add_data)

            # make sql statement
            column_list = list(history_data.keys())
            prepared_list = ["%s"]*len(column_list)
            value_list = list(history_data.values())

            sql = "INSERT INTO `{}` ({}) VALUES ({})".format(history_table_name, ','.join(column_list), ','.join(prepared_list))
            res = self.sql_execute(sql, value_list)
            if res is False:
                is_last_res = False
                break

        return data_list if is_last_res is True else is_last_res

    def table_update(self, table_name, data_list, primary_key_name, is_register_history=False, last_timestamp=True):
        """
        update table

        Arguments:
            data_list: data list for update ex.[{primary_key_name:"{uuid}", "name":"なまえ", "number":"3"}]
            primary_key_name: primary key column name
            is_register_history: (bool)is register history table
        Returns:
            table data list: list(tuple)
            or
            update failure: (bool)False
        """
        if isinstance(data_list, dict):
            data_list = [data_list]

        self.db_transaction_start()

        is_last_res = True
        for data in data_list:
            # auto set
            if last_timestamp is True:
                timestamp = get_timestamp()
                data[self._COLUMN_NAME_TIMESTAMP] = timestamp

            # make sql statement
            prepared_list = list(map(lambda k: "`" + k + "`=%s", data.keys()))
            value_list = list(data.values())
            primary_key_value = data[primary_key_name]

            # key値もbindように最後に値を付加する
            value_list.append(primary_key_value)
            sql = "UPDATE `{}` SET {} WHERE `{}`=%s".format(table_name, ','.join(prepared_list), primary_key_name)
            res = self.sql_execute(sql, value_list)
            if res is False:
                is_last_res = False
                break

            if is_register_history is False:
                continue
            # insert history table
            history_table_name = table_name + "_JNL"
            add_data = self._get_history_table_data("UPDATE", timestamp)

            # re-get all column data
            data = self.table_select(table_name, "WHERE `{}` = %s".format(primary_key_name), [primary_key_value])
            if len(data) == 0:
                return False
            data = dict(data[0])
            # make history data
            history_data = dict(data, **add_data)

            # make sql statement
            column_list = list(history_data.keys())
            prepared_list = ["%s"]*len(column_list)
            value_list = list(history_data.values())

            sql = "INSERT INTO `{}` ({}) VALUES ({})".format(history_table_name, ','.join(column_list), ','.join(prepared_list))
            res = self.sql_execute(sql, value_list)
            if res is False:
                is_last_res = False
                break

        return data_list if is_last_res is True else is_last_res


    def table_delete(self, table_name, data_list, primary_key_name, is_register_history=False):
        """
        delete table

        Arguments:
            data_list (dict): data list for delete ex.[{primary_key_name:"{uuid}"}]
            table_name (str): delete table name
            primary_key_name (str): primary key column name
            is_register_history (bool): is register history table (default: False)

        Returns:
            delete failure: (bool)False
        """
        if isinstance(data_list, dict):
            data_list = [data_list]

        is_last_res = True
        for data in data_list:

            # make sql statement
            prepared_list = list(map(lambda k: "`" + k + "`=%s", data.keys()))
            value_list = list(data.values())
            primary_key_value = data[primary_key_name]

            sql = "DELETE FROM `{}` WHERE `{}`=%s".format(table_name, primary_key_name)
            res = self.sql_execute(sql, [primary_key_value])
            if res is False:
                is_last_res = False

            # 履歴無しの場合は、履歴テーブル削除は実行しない
            # If there is no history, history table deletion is not executed.
            if not is_register_history:
                continue

            # delete history table
            history_table_name = table_name + "_JNL"

            sql = "DELETE FROM `{}` WHERE `{}`=%s".format(history_table_name, primary_key_name)
            res = self.sql_execute(sql, [primary_key_value])
            if res is False:
                is_last_res = False

        # １回でも失敗したらFalseを返却
        # If it fails even once, return False
        return is_last_res


    def table_permanent_delete(self, table_name, where_str="", bind_value_list=[], is_delete_history=False):
        """
        delete permanently from table

        Arguments:
            table_name: table name
            where_str: sql statement of WHERE sentence ex."WHERE name = %s and number = %s"
            bind_value_list: value list ex.["hoge taro", 5]
            is_delete_history: whether delete jnl table or not
        Returns:

        """
        where_str = " {}".format(where_str) if where_str else ""
        sql = "DELETE FROM `{}`{}".format(table_name, where_str)
        ret = self.sql_execute(sql, bind_value_list)

        if is_delete_history is True:
            history_table_name = table_name + "_JNL"
            sql = "DELETE FROM `{}`{}".format(history_table_name, where_str)
            ret = self.sql_execute(sql, bind_value_list)

    def table_lock(self, table_name_list=[]):
        """
        lock table of table-list-table

        Arguments:
            table_name_list: table_name list
        Returns:
            is success:(bool)
        """
        if isinstance(table_name_list, str):
            table_name_list = [table_name_list]

        prepared_list = ['%s']*len(table_name_list)

        sql = "SELECT `TABLE_NAME` FROM `T_COMN_RECODE_LOCK_TABLE` WHERE `TABLE_NAME` IN ({}) FOR UPDATE".format(",".join(prepared_list))
        res = self.sql_execute(sql, table_name_list)

        res_table_name_list = [ _r.get("TABLE_NAME") for _r in res]
        # select for update no data: insert `t_comn_recode_lock_table` and retry select for update
        if len(res) != len(table_name_list):
            # create insert sql and sql_execute
            target_table_name = [_tn for _tn in table_name_list if _tn not in res_table_name_list] if res_table_name_list else table_name_list
            prepared_list = ['(%s)']*len(target_table_name)
            sql = "INSERT INTO `T_COMN_RECODE_LOCK_TABLE` (`TABLE_NAME`) VALUES " + "{};".format(",".join(prepared_list))
            res = self.sql_execute(sql, target_table_name)

            # retry select for update
            prepared_list = ['%s']*len(target_table_name)
            sql = "SELECT `TABLE_NAME` FROM `T_COMN_RECODE_LOCK_TABLE` WHERE `TABLE_NAME` IN ({}) FOR UPDATE".format(",".join(prepared_list))
            res = self.sql_execute(sql, target_table_name)
        return res

    def prepared_val_escape(self, val):
        """
        escape sql statement

        Arguments:
            val: str
        Returns:
            val: str
        """
        if isinstance(val, str):
            return val.replace("%", "%%")

        return val

    def prepared_list_escape(self, str_list):
        """
        escape list of sql statement

        Arguments:
            str_list: list of str
        Returns:
            str_list: list of str
        """
        return list(map(lambda s: self.prepared_val_escape(s), str_list))

    def _uuid_create(self):
        """
        make uuid of version4

        Returns:
            uuid
        """
        return uuid.uuid4()

    @classmethod
    def genarate_primary_key_value(cls):
        """
        make uuid of version4

        Returns:
            uuid
        """
        return str(uuid.uuid4())

    def _get_history_table_data(self, action_class, timestamp):
        """
        get addtinal data for history JNL table

        Arguments:
            action_class: "INSERT" or "UPDATE"
            timestamp: timestamp
        Returns:
            addtinal data for history JNL table: tupple
        """
        return {
            'JOURNAL_SEQ_NO': str(self._uuid_create()),
            'JOURNAL_REG_DATETIME': timestamp,
            'JOURNAL_ACTION_CLASS': action_class
        }

    def userinfo_generate(self, prefix=""):
        """
        create user for workspace

        Arguments:
            db_name: database name(uuid)
        Returns:
            db_name, user_name, user_password: tuple
        """
        db_name = prefix + "_" + str(self._uuid_create()).upper()
        # mysql>=5.7はユーザ名32文字まで
        # 利用可能文字 https://dev.mysql.com/doc/refman/8.0/en/identifiers.html
        user_name = prefix + "_" + generate_secrets(20, "-_$+")
        user_password = self.password_generate()
        return db_name, user_name, user_password

    def password_generate(self):
        """
        generate password

        Arguments:
            escape or not: bool
        Returns:
            password string: str
        """
        length = 16
        mysql_available_symbol = "!#%&()*+,-./;<=>?@[]^_{|}~"
        password = generate_secrets(length, mysql_available_symbol)

        return password

    def get_connect_info(self):
        """
        get database connect infomation for self

        Returns:
            database connect infomation for self: dict
        """
        connect_info = {
            'DB_HOST': self._host,
            'DB_PORT': self._port,
            'DB_USER': self._db_user,
            'DB_PASSWORD': self._db_passwd
        }
        if self._db:
            connect_info['DB_DATABASE'] = self._db

        return connect_info

    def get_orgdb_connect_info(self, organization_id):
        """
        get database connect infomation for organization

        Arguments:
            organization_id: organization_id
        Returns:
            database connect infomation for organization: dict
            or
            get failure: (bool)False
        """
        isnot_register_db_connect_info = "db_connect_info" not in g or "ORGDB_DATABASE" not in g.db_connect_info
        isnot_same_organization = g.get('ORGANIZATION_ID') and g.get('ORGANIZATION_ID') != organization_id
        if isnot_register_db_connect_info or isnot_same_organization:
            where = "WHERE `ORGANIZATION_ID`=%s and `DISUSE_FLAG`=0 LIMIT 1"
            data_list = self.table_select("T_COMN_ORGANIZATION_DB_INFO", where, [organization_id])

            if len(data_list) == 0:
                return False

            return data_list[0]

        return {
            'DB_HOST': g.db_connect_info.get('ORGDB_HOST'),
            'DB_PORT': g.db_connect_info.get('ORGDB_PORT'),
            'DB_USER': g.db_connect_info.get('ORGDB_USER'),
            'DB_PASSWORD': g.db_connect_info.get('ORGDB_PASSWORD'),
            'DB_ADMIN_USER': g.db_connect_info.get('ORGDB_ADMIN_USER'),
            'DB_ADMIN_PASSWORD': g.db_connect_info.get('ORGDB_ADMIN_PASSWORD'),
            'DB_DATABASE': g.db_connect_info.get('ORGDB_DATABASE'),
            'MONGO_OWNER': g.db_connect_info.get('ORG_MONGO_OWNER'),
            'MONGO_CONNECTION_STRING': g.db_connect_info.get('ORG_MONGO_CONNECTION_STRING'),
            'MONGO_ADMIN_USER': g.db_connect_info.get('ORG_MONGO_ADMIN_USER'),
            'MONGO_ADMIN_PASSWORD': g.db_connect_info.get('ORG_MONGO_ADMIN_PASSWORD'),
            'INITIAL_DATA_ANSIBLE_IF': g.db_connect_info.get('INITIAL_DATA_ANSIBLE_IF'),
            'NO_INSTALL_DRIVER': g.db_connect_info.get('NO_INSTALL_DRIVER')
        }

    def sql_execute_cursor(self, sql, bind_value_list=[]):
        """
        execute sql:cursor

        Arguments:
            sql: sql statement ex."SELECT * FROM table_name WHERE name = %s and number = %s"
            bind_value_list: list or tuple or dict ex.["hoge taro", 5]
        Returns:
            db_cursor: self._db_con.cursor()
        """
        db_cursor = self._db_con.cursor()

        # escape
        if len(bind_value_list) == 0:
            sql = self.prepared_val_escape(sql)
        else:
            # convert list→tupple
            if isinstance(bind_value_list, list):
                bind_value_list = tuple(bind_value_list)

        try:
            db_cursor.execute(sql, bind_value_list)
            self.__sql_debug(db_cursor, sql, bind_value_list)
        except pymysql.Error as e:
            last_executed = sql % (bind_value_list)
            if self._db_con.open is True and db_cursor is not None and db_cursor._executed is not None:
                last_executed = db_cursor._executed
            raise AppException("999-00003", [self._db, last_executed, e])
        return db_cursor

    def table_select_cursor(self, table_name, where_str="", bind_value_list=[]):
        """
        select table:cursor

        Arguments:
            table_name: table name
            where_str: sql statement of WHERE sentence ex."WHERE name = %s and number = %s"
            bind_value_list: value list ex.["hoge taro", 5]
        Returns:
            db_cursor: self._db_con.cursor()
        """
        where_str = " {}".format(where_str) if where_str else ""
        sql = "SELECT * FROM `{}`{}".format(table_name, where_str)
        return self.sql_execute_cursor(sql, bind_value_list)

class DBConnectCommonRoot(DBConnectCommon):
    """
    database connection agnet class on mariadb
    """
    def __init__(self, retry=None):
        """
        constructor
        """
        if self._db_con is not None and self._db_con.open is True:
            return True

        self._host = os.environ.get('DB_HOST')
        self._port = int(os.environ.get('DB_PORT'))
        self._db_user = os.environ.get('DB_ADMIN_USER')
        self._db_passwd = os.environ.get('DB_ADMIN_PASSWORD')

        # connect database
        self.db_connect(retry=retry)

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
                passwd=self._db_passwd,
                charset='utf8mb4',
                collation='utf8mb4_general_ci',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=self.connect_timeout,
            )
        except pymysql.Error as e:
            raise DBException(f"{self._host}:{self._port}", e)

        return True
