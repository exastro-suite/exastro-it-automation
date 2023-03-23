# Copyright 2023 NEC Corporation#
# Licensed under the Apache License, Version 2.2 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.2
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import json
import re

from common_libs.terraform_driver.cli.Const import Const as TFCLIConst


# Typeの情報を取得する
def get_type_info(wsDb, type_id):
    type_id = type_id if type_id is not None else "1"
    type_info = {}

    condition = "WHERE DISUSE_FLAG = '0' AND TYPE_ID = %s"
    rows = wsDb.table_select(TFCLIConst.T_TYPE_MASTER, condition, [type_id])
    if len(rows) > 0:
        type_info = rows[0]
    else:
        # 異常
        pass

    return type_info


# 配列からHCLへencodeする
def encode_hcl(arr):
    json_data = json.dumps(arr, ensure_ascii=False)
    res = re.sub(r'\"(.*?)\"\:(.*?)', r'"\1" = \2', json_data)
    return str(res)


# HCL作成のためにメンバー変数一覧を取得
def get_member_vars_ModuleVarsLinkID_for_hcl(wsDb, module_vars_link_id):
    condition = "WHERE DISUSE_FLAG = '0' AND PARENT_VARS_ID = %s ORDER BY ARRAY_NEST_LEVEL, ASSIGN_SEQ ASC"
    rows = wsDb.table_select(TFCLIConst.V_TERC_VAR_MEMBER, condition, [module_vars_link_id])
    if len(rows) > 0:
        # リソース（Module素材)ファイル名格納
        row = rows[0]
        row["VARS_ENTRY_FLAG"] = 0
    else:
        # 異常
        pass

    res = [row]
    return res


# HCL作成のためにメンバー変数一覧を配列に形成
def generate_member_vars_array_for_hcl(memberVarsRecords):
    pass


# 親のインデックスを集めた配列作成
def make_parent_id_map(memberVarsRecords):
    pass


# HCL作成のためにメンバー変数一覧を多次元配列に整形
def generate_member_vars_array(member_vars_array, member_vars_key, member_vars_value, type_info, map):
    res = []

    return res
