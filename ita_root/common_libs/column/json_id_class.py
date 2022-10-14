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

import json
from flask import g  # noqa: F401
from common_libs.common import *  # noqa: F401,F403

# import column_class
from .id_class import IDColumn


class JsonIDColumn(IDColumn):
    """
    カラムクラス個別処理(JsonIDColumn)
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
        ref_pkey_name = self.get_objcol().get("REF_PKEY_NAME")
        ref_table_name = self.get_objcol().get("REF_TABLE_NAME")
        # REF_COL_NAMEに項目を特定するためのcolumn_name_restが入っている
        column_name_rest = self.get_objcol().get("REF_COL_NAME")
        # カラム名は「DATA_JSON」固定
        ref_col_name = "DATA_JSON"
        where_str = "WHERE `DISUSE_FLAG` = '0' "
        bind_value_list = []

        # 検索
        return_values = self.objdbca.table_select(ref_table_name, where_str, bind_value_list)

        for record in return_values:
            data_json_record = record.get(ref_col_name)
            record_dict = json.loads(data_json_record)
            for key, value in record_dict.items():
                if key == column_name_rest:
                    values[record[ref_pkey_name]] = value
                    break

        return values
