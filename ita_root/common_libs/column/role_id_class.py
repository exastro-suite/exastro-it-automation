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

import os
import sys
from flask import g
from common_libs.common import *  # noqa: F403

# import column_class
from .id_class import IDColumn


class RoleIDColumn(IDColumn):
    """
        カラムクラス個別処理(RoleIDColumn)
    """

    def search_id_data_list(self):
        """
            データリストを検索する
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        values = {}

        # ExastroPlatformからロールの一覧を取得
        roles = util.get_workspace_roles()

        # key=valueの配列をつくる
        for role in roles:
            values[role] = role

        return values

    # def __init__(self, objdbca, objtable, rest_key_name, cmd_type):
    #     # カラムクラス名
    #     self.class_name = self.__class__.__name__
    #     # メッセージ
    #     self.message = ''
    #     # バリデーション閾値
    #     self.dict_valid = {}
    #     # テーブル情報
    #     self.objtable = objtable

    #     # テーブル名
    #     table_name = ''
    #     objmenu = objtable.get('MENUINFO')
    #     if objmenu is not None:
    #         table_name = objmenu.get('TABLE_NAME')
    #     self.table_name = table_name

    #     # カラム名
    #     col_name = ''
    #     objcols = objtable.get('COLINFO')
    #     if objcols is not None:
    #         objcol = objcols.get(rest_key_name)
    #         if objcol is not None:
    #             col_name = objcol.get('COL_NAME')

    #     self.col_name = col_name
        
    #     # rest用項目名
    #     self.rest_key_name = rest_key_name

    #     self.db_qm = "'"

    #     self.objdbca = objdbca
        
    #     self.cmd_type = cmd_type
        
    # def get_values_by_key(self, where_equal=[]):
    #     """
    #         Keyを検索条件に値を取得する
    #         ARGS:
    #             where_equal:一致検索のリスト
    #         RETRUN:
    #             values:検索結果
    #     """

    #     values = {}

    #     roles = util.get_workspace_roles()

    #     # 一致検索
    #     if len(where_equal) > 0:
    #         for where_value in where_equal:
    #             if where_value in roles:
    #                 values[where_value] = where_value
    #     else:
    #         for role in roles:
    #                 values[role] = role

    #     return values

    # def get_values_by_value(self, where_equal=[], where_like=""):
    #     """
    #         valueを検索条件に値を取得する
    #         ARGS:
    #             where_equal:一致検索のリスト(list)
    #             where_like:あいまい検索の値(string)
    #         RETRUN:
    #             values:検索結果
    #     """
    #     tmp_roles = {}
    #     values = {}

    #     roles = util.get_workspace_roles()

    #     # 一致検索
    #     if len(where_equal) > 0:
    #         for where_value in where_equal:
    #             if where_value in roles:
    #                 tmp_roles[where_value] = where_value
    #     else:
    #         for role in roles:
    #             tmp_roles[role] = role

    #     # あいまい検索
    #     if len(where_like) > 0:
    #         for role in tmp_roles:
    #             if where_like in role:
    #                 values[role] = role
    #     else:
    #         values = tmp_roles

    #     return values
