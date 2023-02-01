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

from flask import g # noqa: F401
from common_libs.common.dbconnect import DBConnectWs  # noqa: F401

from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from common_libs.column import *  # noqa: F403

import textwrap
from datetime import datetime
from pprint import pprint  # noqa: F401


class BaseTable():
    def __init__(self, objdbca, table_name):
        self.objdbca = objdbca
        self.table_name = table_name
        column_list, primary_key_list = self.objdbca.table_columns_get(table_name)
        self.primary_key = primary_key_list[0]
        self.column_names = column_list
        self.objmenu = self.get_load_table()

    def execQuery(self, sql, bind_array=[]):
        """
        SQL実行
        Args:
            sql (_type_): _description_
            bind_array (_type_): _description_
        Returns:
            _type_: _description_
        """
        result = self.objdbca.sql_execute(sql, bind_array)
        return result

    def override_set_col_names(self, column_names):
        """
        カラム名手動設定
        """
        self.column_names = column_names

    def create_sselect(self, condition_str='', jnl=False):
        columns_str = ''
        jnl_str = ''
        if jnl is True:
            jnl_str = '_JNL '
        columns_str = ",".join(self.column_names)
        sql = 'SELECT {} FROM {}{} {}'.format(columns_str, self.table_name, jnl_str, condition_str)
        return sql

    def select_table(self, sql):
        rows = self.execQuery(sql)
        result = []
        for row in rows:
            result.append(row)
        return result

    def update_table(self, update_data):
        self.objdbca.table_update(self.table_name, update_data, self.primary_key)

    def update_record(self, update_data):
        self.objdbca.table_update(self.table_name, update_data, self.primary_key, False)

    def update_record_jnl(self, update_data):
        self.objdbca.table_update('{}_JNL '.format(self.table_name), update_data, self.primary_key, False)

    def insert_table(self, insert_data):
        self.objdbca.table_update(self.table_name, insert_data, self.primary_key)

    def truncate(self):
        sql = "TRUNCATE TABLE {}".format(self.table_name)
        self.execQuery(sql)

        sql = "TRUNCATE TABLE {}{}".format(self.table_name, '_JNL')
        self.execQuery(sql)

    def get_menu_names(self):
        sql = textwrap.dedent("""
            SELECT `TAB_A`.*, `TAB_B`.*
            FROM `T_COMN_MENU_TABLE_LINK` `TAB_A`
            LEFT JOIN `T_COMN_MENU` TAB_B ON (`TAB_A`.`MENU_ID` = `TAB_B`.`MENU_ID`)
            WHERE `TAB_A`.`TABLE_NAME` = %s
            AND `TAB_A`.`ROW_INSERT_FLAG` = 1
            AND `TAB_A`.`ROW_UPDATE_FLAG` = 1
            AND `TAB_A`.`ROW_DISUSE_FLAG` = 1
            AND `TAB_A`.`ROW_REUSE_FLAG` = 1
            AND `TAB_A`.`DISUSE_FLAG` = 0
            AND `TAB_B`.`DISUSE_FLAG` = 0
        """).format().strip()
        bind_array = [self.table_name]
        rows = self.execQuery(sql, bind_array)
        result = {}
        result = None
        if len(rows) == 1:
            for row in rows:
                tmp_row = {
                    'MENU_ID': row.get('MENU_ID'),
                    'TABLE_NAME': row.get('TABLE_NAME'),
                    'MENU_NAME_REST': row.get('MENU_NAME_REST'),
                    'ROW_INSERT_FLAG': row.get('ROW_INSERT_FLAG'),
                    'ROW_UPDATE_FLAG': row.get('ROW_UPDATE_FLAG'),
                    'ROW_DISUSE_FLAG': row.get('ROW_DISUSE_FLAG'),
                    'ROW_REUSE_FLAG': row.get('ROW_REUSE_FLAG'),
                }
                # result.setdefault(row.get('MENU_NAME_REST'), tmp_row)
                result = row.get('MENU_NAME_REST')
        return result

    def get_load_table(self, menu_name=None):
        if menu_name is None:
            menu_name = self.get_menu_names()
        objmenu = load_table.loadTable(self.objdbca, menu_name)  # noqa: F405
        return objmenu


### ホストグループ関連
class HostgroupListTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "T_HGSP_HOSTGROUP_LIST"
        super().__init__(objdbca, table_name)


class HostLinkListTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "T_HGSP_HOST_LINK_LIST"
        super().__init__(objdbca, table_name)


class HostLinkTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "T_HGSP_HOST_LINK"
        super().__init__(objdbca, table_name)


class SplitTargetTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "T_HGSP_SPLIT_TARGET"
        super().__init__(objdbca, table_name)


# メニュー関連
class MenuListTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "T_COMN_MENU"
        super().__init__(objdbca, table_name)


class MenuTableLinkTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "T_COMN_MENU_TABLE_LINK"
        super().__init__(objdbca, table_name)


# Ansible共通
class StmListTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "T_ANSC_DEVICE"
        super().__init__(objdbca, table_name)

### 未整理
class HostgroupVarTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "F_HOSTGROUP_VAR"
        super().__init__(objdbca, table_name)
class HgVarLinkLegacyTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "F_HG_VAR_LINK_LEGACY"
        super().__init__(objdbca, table_name)
class AnsibleLnsVarsMasterTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "B_ANSIBLE_LNS_VARS_MASTER"
        super().__init__(objdbca, table_name)
class AnsLnsPtnVarsLinkTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "B_ANS_LNS_PTN_VARS_LINK"
        super().__init__(objdbca, table_name)
class AnsibleLnsPhoLinkTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "B_ANSIBLE_LNS_PHO_LINK"
        super().__init__(objdbca, table_name)
class AnsibleLnsVarsAssignTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "B_ANSIBLE_LNS_VARS_ASSIGN"
        super().__init__(objdbca, table_name)
class HgVarLinkLegacyRoleTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "F_HG_VAR_LINK_LEGACYROLE"
        super().__init__(objdbca, table_name)
class AnsibleLrlVarsMasterTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "B_ANSIBLE_LRL_VARS_MASTER"
        super().__init__(objdbca, table_name)
class AnsLrlPtnVarsLinkTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "B_ANS_LRL_PTN_VARS_LINK"
        super().__init__(objdbca, table_name)
class AnsibleLrlPhoLinkTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "B_ANSIBLE_LRL_PHO_LINK"
        super().__init__(objdbca, table_name)
class AnsibleLrlVarsAssignTable(BaseTable):
    def __init__(self, objdbca):
        table_name = "B_ANSIBLE_LRL_VARS_ASSIGN"
        super().__init__(objdbca, table_name)


# 共通Lib
def get_now_datetime(format='%Y/%m/%d %H:%M:%S', type='str'):
    dt = datetime.now().strftime(format)
    if type == 'str':
        return '{}'.format(dt)
    else:
        return dt


def addline_msg(msg=''):
    import inspect, os
    info = inspect.getouterframes(inspect.currentframe())[1]
    msg_line = "{} ({}:{})".format(msg, os.path.basename(info.filename), info.lineno)
    return msg_line


def load_objcolumn(objdbca, objtable, rest_key, col_class_name='TextColumn', ):

    try:
        eval_class_str = "{}(objdbca,objtable,rest_key,'')".format(col_class_name)
        objcolumn = eval(eval_class_str)
    except Exception:
        return False
    return objcolumn
