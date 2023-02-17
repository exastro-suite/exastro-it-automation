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

from flask import g  # noqa: F401
from common_libs.common.dbconnect import DBConnectWs  # noqa: F401

from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from common_libs.column import *  # noqa: F403

import uuid
import textwrap
from pprint import pprint  # noqa: F401


class BaseTable():
    """
    BaseTable class
    """
    def __init__(self, objdbca, table_name, iudr_flg=1):
        self.objdbca = objdbca
        self.table_name = table_name
        column_list, primary_key_list = self.objdbca.table_columns_get(table_name)
        if len(primary_key_list) == 1:
            self.primary_key = primary_key_list[0]
        self.column_names = column_list
        self.iudr_flg = iudr_flg
        self.objmenu = self.get_load_table()

    def exec_query(self, sql, bind_array=[]):
        """
        exec_query: SQL実行
        Args:
            self: self
            sql: sql
            bind_array: bind list
        Returns:
            result: result
        """
        result = self.objdbca.sql_execute(sql, bind_array)
        return result

    def override_set_col_names(self, column_names):
        """
        override_set_col_names: カラム名手動設定
        Args:
            self: self
            column_names: column name list
        Returns:

        """
        self.column_names = column_names

    def create_sselect(self, condition_str='', jnl=False):
        """
        create_sselect: SQL生成(SELECT)
        Args:
            self: self
            condition_str: condition
            jnl: jnl flg
        Returns:
            sql: sql
        """
        columns_str = ''
        jnl_str = ''
        if jnl is True:
            jnl_str = '_JNL '
        columns_str = ",".join(self.column_names)
        sql = 'SELECT {} FROM `{}{}` {}'.format(columns_str, self.table_name, jnl_str, condition_str)
        return sql

    def select_table(self, sql):
        """
        select_table: SQL実行
        Args:
            self: self
            sql: sql
        Returns:
            result: list
        """
        rows = self.exec_query(sql)
        result = []
        for row in rows:
            result.append(row)
        return result

    def update_table(self, update_data):
        """
        update_table: UPDATE: table_name and table_name + _JNL
        Args:
            self: self
            update_data: { key:value }
        Returns:
            result: result
        """
        return self.objdbca.table_update(self.table_name, update_data, self.primary_key)

    def update_record(self, update_data):
        """
        update_record: UPDATE: table_name
        Args:
            self: self
            update_data: { key:value }
        Returns:
            result: result
        """
        return self.objdbca.table_update(self.table_name, update_data, self.primary_key, False)

    def update_record_jnl(self, update_data):
        """
        update_record_jnl: UPDATE: table_name + _JNL
        Args:
            self: self
            update_data: { key:value }
        Returns:
            result: result
        """
        return self.objdbca.table_update('`{}_JNL` '.format(self.table_name), update_data, self.primary_key, False)

    def insert_table(self, insert_data):
        """
        insert_table: INSERT: table_name and table_name + _JNL
        Args:
            self: self
            update_data: { key:value }
        Returns:
            result: result
        """
        insert_primay_id = uuid.uuid4()
        return self.objdbca.table_insert(self.table_name, insert_data, self.primary_key, insert_primay_id)

    def get_menu_names(self):
        """
        get_menu_names: get MENU_NAME_REST
        Args:
            self: self
        Returns:
            result: result
        """
        sql = textwrap.dedent("""
            SELECT `TAB_A`.*, `TAB_B`.*
            FROM `T_COMN_MENU_TABLE_LINK` `TAB_A`
            LEFT JOIN `T_COMN_MENU` TAB_B ON (`TAB_A`.`MENU_ID` = `TAB_B`.`MENU_ID`)
            WHERE `TAB_A`.`TABLE_NAME` = %s
            AND `TAB_A`.`ROW_INSERT_FLAG` = {iudr_flg}
            AND `TAB_A`.`ROW_UPDATE_FLAG` = {iudr_flg}
            AND `TAB_A`.`ROW_DISUSE_FLAG` = {iudr_flg}
            AND `TAB_A`.`ROW_REUSE_FLAG` = {iudr_flg}
            AND `TAB_A`.`DISUSE_FLAG` = 0
            AND `TAB_B`.`DISUSE_FLAG` = 0
        """).format(iudr_flg=self.iudr_flg).strip()
        bind_array = [self.table_name]
        rows = self.exec_query(sql, bind_array)
        result = {}
        result = None
        if len(rows) == 1:
            for row in rows:
                result = row.get('MENU_NAME_REST')
        return result

    def get_load_table(self, menu_name=None):
        """
        get_load_table: get load table object
        Args:
            self: self
        Returns:
            result: load table object
        """
        if menu_name is None:
            menu_name = self.get_menu_names()
        objmenu = load_table.loadTable(self.objdbca, menu_name)  # noqa: F405
        return objmenu

    def get_menu_ids(self):
        """
        get_menu_ids: get MENU_ID
        Args:
            self: self
        Returns:
            result: MENU_ID
        """
        menu_name = self.get_menu_names()
        sql = textwrap.dedent("""
            SELECT *
            FROM `T_COMN_MENU` `TAB_A`
            WHERE `TAB_A`.`MENU_NAME_REST` = %s
            AND `TAB_A`.`DISUSE_FLAG` = 0
        """).format().strip()
        bind_array = [menu_name]
        rows = self.exec_query(sql, bind_array)
        result = {}
        result = None
        if len(rows) == 1:
            for row in rows:
                result = row.get('MENU_ID')
        return result


# ホストグループ関連
class HostgroupListTable(BaseTable):
    """
    HostgroupListTable class: ホストグループ一覧
    """
    def __init__(self, objdbca):
        table_name = "T_HGSP_HOSTGROUP_LIST"
        super().__init__(objdbca, table_name)


class HostLinkListTable(BaseTable):
    """
    HostLinkListTable class: ホストグループ親子紐付
    """
    def __init__(self, objdbca):
        table_name = "T_HGSP_HOST_LINK_LIST"
        super().__init__(objdbca, table_name)


class HostLinkTable(BaseTable):
    """
    HostLinkTable class: ホスト紐付管理
    """
    def __init__(self, objdbca):
        table_name = "T_HGSP_HOST_LINK"
        super().__init__(objdbca, table_name)


class SplitTargetTable(BaseTable):
    """
    SplitTargetTable class: ホストグループ分割対象
    """
    def __init__(self, objdbca):
        table_name = "T_HGSP_SPLIT_TARGET"
        super().__init__(objdbca, table_name)


# メニュー関連
class MenuListTable(BaseTable):
    """
    MenuListTable class: メニュー一覧
    """
    def __init__(self, objdbca):
        table_name = "T_COMN_MENU"
        super().__init__(objdbca, table_name)


class MenuTableLinkTable(BaseTable):
    """
    MenuTableLinkTable class: メニュー-テーブル紐付管理
    """
    def __init__(self, objdbca):
        table_name = "T_COMN_MENU_TABLE_LINK"
        super().__init__(objdbca, table_name)


# 共通
class VersionTable(BaseTable):
    """
    VersionTable class: バージョン情報
    """
    def __init__(self, objdbca):
        table_name = "T_COMN_VERSION"
        super().__init__(objdbca, table_name)


class PlocLoadedTable(BaseTable):
    """
    PlocLoadedTable class:
    """
    def __init__(self, objdbca):
        table_name = "T_COMN_PROC_LOADED_LIST"
        super().__init__(objdbca, table_name)


# Ansible共通
class StmListTable(BaseTable):
    """
    StmListTable class: 機器一覧
    """
    def __init__(self, objdbca):
        table_name = "T_ANSC_DEVICE"
        super().__init__(objdbca, table_name)
