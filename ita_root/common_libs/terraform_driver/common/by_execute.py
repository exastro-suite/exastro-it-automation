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
from dictknife import deepmerge


# Typeの情報を取得する
def get_type_info(wsDb, TFConst, type_id):
    type_id = type_id if type_id is not None else "1"
    type_info = {}

    condition = "WHERE DISUSE_FLAG = '0' AND TYPE_ID = %s"
    rows = wsDb.table_select(TFConst.T_TYPE_MASTER, condition, [type_id])
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


# HCL形式から配列にデコードする
def decode_hcl(hcl_data):
    res = re.sub(r'\"(.*?)\"\ = \"(.*?)\"', r'"\1": "\2"', hcl_data)
    res = json.loads(res)

    return res


# HCL作成のためにメンバー変数一覧を取得
def get_member_vars_ModuleVarsLinkID_for_hcl(wsDb, TFConst, module_vars_link_id):
    condition = "WHERE DISUSE_FLAG = '0' AND PARENT_VARS_ID = %s ORDER BY ARRAY_NEST_LEVEL, ASSIGN_SEQ ASC"
    records = wsDb.table_select(TFConst.V_VAR_MEMVER, condition, [module_vars_link_id])

    res = []
    for record in records:
        record["VARS_ENTRY_FLAG"] = 0
        res.append(record)

    return res


# HCL作成のためにメンバー変数一覧を配列に形成
def generate_member_vars_array_for_hcl(member_vars_records):
    member_vars_res = []

    # 親リストの取得
    parent_id_map = make_parent_id_map(member_vars_records)

    # 階層リストの作成
    array_nest_level_list = [m.get('ARRAY_NEST_LEVEL') for m in member_vars_records]
    # 降順に並べ替え
    array_nest_level_list.sort(reverse=True)
    # 階層リストから重複の削除
    array_nest_level_list = list(set(array_nest_level_list))

    pattern = r'^\[([0-9]+)\]$'
    for member_vars_record in member_vars_records:
        key = member_vars_record["CHILD_MEMBER_VARS_KEY"]
        # indexが数値の場合は[]を外す
        match = re.findall(pattern, key)
        if len(match) != 0:
            key = match[0]

        # タイプ情報の取得
        type_info = get_type_info(member_vars_record["CHILD_VARS_TYPE_ID"])
        # 配列組み立て
        trg_parent_id_map_id = [m.get('child_member_vars_id') for m in parent_id_map].index(member_vars_record["CHILD_MEMBER_VARS_ID"])
        trg_parent_id_map = parent_id_map[trg_parent_id_map_id]
        # 配列型のものは配列を具体値に代入する
        member_vars_res = generate_member_vars_array(member_vars_res, key, member_vars_record["CHILD_MEMBER_VARS_VALUE"], type_info, trg_parent_id_map["parent_member_keys_list"])  # noqa: E501

    return member_vars_res


# 親のインデックスを集めた配列作成
def make_parent_id_map(member_vars_records):
    res = []

    # 親メンバー変数のキー一覧
    parent_member_keys_list = []

    # ネスト取得
    array_nest_level_list = [m.get('ARRAY_NEST_LEVEL') for m in member_vars_records]
    # 並び替え
    array_nest_level_list.sort()
    # 重複削除
    array_nest_level_list = list(set(array_nest_level_list))

    pattern = r'^\[([0-9]+)\]$'
    for array_nest_level in array_nest_level_list:
        for member_vars_record in member_vars_records:
            # キーの取得
            key = member_vars_record["CHILD_MEMBER_VARS_KEY"]
            # indexが数値の場合は[]を外す
            match = re.findall(pattern, key)
            if len(match) != 0:
                key = match[0]

            if member_vars_record["ARRAY_NEST_LEVEL"] == array_nest_level:
                # 親のネストリストを取得
                # インデックスを検索
                if member_vars_record["PARENT_MEMBER_VARS_ID"] is not None:
                    parent_index = [m.get('child_member_vars_id') for m in res].index(member_vars_record["PARENT_MEMBER_VARS_ID"])

                    parent_member_keys_list = res[parent_index]["parent_member_keys_list"]
                    parent_key = res[parent_index]["child_member_vars_key"]

                    # indexが数値の場合は[]を外す
                    if res[parent_index]["child_member_vars_key"] != "":
                        match2 = re.findall(pattern, res[parent_index]["child_member_vars_key"])
                        if len(match2) != 0:
                            parent_key = match2[0]
                        parent_member_keys_list.append(parent_key)

                res.append({
                    "child_member_vars_id": member_vars_record["CHILD_MEMBER_VARS_ID"],
                    "child_member_vars_key": key,
                    "parent_member_keys_list": parent_member_keys_list
                })

    return res


# HCL作成のためにメンバー変数一覧を多次元配列に整形
def generate_member_vars_array(member_vars_array, member_vars_key, member_vars_value, type_info, map):
    res = []

    if len(map) == 0:
        # 仮配列と返却用配列をマージ
        member_vars_array[member_vars_key] = member_vars_value
        res = member_vars_array
    else:
        # 仮配列
        tmp_array = {}
        ref = tmp_array

        # 多次元配列作成
        index = 0
        for key in map:
            if not index:
                ref = {key: None}
            elif map[index - 1] in ref:
                ref[map[index - 1]] = {key: None}

            index = index + 1

        # メンバー変数を設定・具体値を代入
        if type_info["ENCODE_FLAG"] == '1':
            member_vars_value = decode_hcl(member_vars_value)
        if type_info["MEMBER_VARS_FLAG"] == '1' and type_info["MEMBER_VARS_FLAG"] != '1':
            ref[member_vars_key] = []
            ref[member_vars_key] = member_vars_value

        # 仮配列と返却用配列をマージ
        res = deepmerge(member_vars_array, tmp_array)

    return res
