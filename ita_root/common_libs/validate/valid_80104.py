# Copyright 2023 NEC Corporation#
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
from flask import g
import json


def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''
    orchestra_id = 4  # Terraform-Cloud/EP オーケストレータID
    proc_load_id = 801  # バックヤード起動フラグのID

    # バックヤード起動フラグ設定
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = {"LOADED_FLG": "0", "ROW_ID": proc_load_id}
    primary_key_name = "ROW_ID"
    objdbca.table_update(table_name, data_list, primary_key_name, False)

    # 入力値取得
    entry_parameter = option.get('entry_parameter').get('parameter')
    # current_parameter = option.get('current_parameter').get('parameter')
    cmd_type = option.get("cmd_type")
    movement_name = entry_parameter.get('movement_name')
    movement_id = entry_parameter.get('movement_id')

    # Movement一覧にMovement名とオーケストレータに同一のレコードがないかを確認(廃止時はスキップ)
    if not cmd_type == "Discard":
        if cmd_type == "Register":
            where_str = 'WHERE MOVEMENT_NAME = %s AND ITA_EXT_STM_ID = %s AND DISUSE_FLAG = %s'
            ret = objdbca.table_select('T_COMN_MOVEMENT', where_str, [movement_name, orchestra_id, 0])
        elif cmd_type == "Update" or cmd_type == "Restore":
            # 「更新」「復活」の場合は自分自身のレコードを除外
            where_str = 'WHERE MOVEMENT_NAME = %s AND ITA_EXT_STM_ID = %s AND MOVEMENT_ID <> %s AND DISUSE_FLAG = %s'
            ret = objdbca.table_select('T_COMN_MOVEMENT', where_str, [movement_name, orchestra_id, movement_id, 0])

        # レコードがある場合は重複エラー
        if ret:
            # オーケストラ名を取得
            orchestra_nama = None
            orchestra_record = objdbca.table_select('T_COMN_ORCHESTRA', 'WHERE ORCHESTRA_ID = %s', [orchestra_id])
            if orchestra_record:
                orchestra_nama = orchestra_record[0].get('ORCHESTRA_NAME')
            # メッセージを作成
            dict_bind_kv = {'movement_name': movement_name, 'orchestrator': orchestra_nama}
            json_dict_bind_kv = json.dumps(dict_bind_kv)
            list_uuids = ret[0].get('MOVEMENT_ID')
            msg_args = [str(json_dict_bind_kv), str(list_uuids)]
            msg = g.appmsg.get_api_message('MSG-00006', msg_args)
            retBool = False

    # オーケストレータIDを設定
    if cmd_type == "Register":
        option["entry_parameter"]["parameter"]["orchestrator"] = orchestra_id

    return retBool, msg, option,
