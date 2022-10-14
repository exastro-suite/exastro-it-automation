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
from common_libs.common import *  # noqa: F403

# import column_class
from .id_class import IDColumn


class LastUpdateUserColumn(IDColumn):
    """
    カラムクラス個別処理(LastUpdateUserColumn)
    """

    def search_id_data_list(self):
        """
            データリストを検索する
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        users_list = {}
        user_env = g.LANGUAGE.upper()
        usr_name_col = "USER_NAME_{}".format(user_env)
        table_name = "T_COMN_BACKYARD_USER"
        where_str = "WHERE DISUSE_FLAG='0'"
        bind_value_list = []

        return_values = self.objdbca.table_select(table_name, where_str, bind_value_list)

        for bk_user in return_values:
            users_list[bk_user['USER_ID']] = bk_user[usr_name_col]

        user_id = g.get('USER_ID')
        if user_id not in users_list:
            pf_users = util.get_exastro_platform_users()

            users_list.update(pf_users)
        
        return users_list
