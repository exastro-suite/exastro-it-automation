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
import os
import inspect
from flask import g
import json

from common_libs.ansible_driver.classes.YamlParseClass import YamlParse
from common_libs.ansible_driver.functions.util import get_OSTmpPath
from common_libs.ansible_driver.functions.util import addAnsibleCreateFilesPath
from common_libs.ansible_driver.functions.util import rmAnsibleCreateFiles
from common_libs.common.exception import AppException


def external_valid_menu_before(objdbca, objtable, option):
    # /tmpに作成したファイル・ディレクトリパスを保存するファイル名
    g.AnsibleCreateFilesPath = "{}/{}_{}".format(get_OSTmpPath(), os.path.basename(inspect.currentframe().f_code.co_filename), os.getpid())

    retBool = True
    msg = ''

    # 入力値取得
    entry_parameter = option.get('entry_parameter').get('parameter')
    current_parameter = option.get('current_parameter').get('parameter')
    cmd_type = option.get("cmd_type")

    orchestrator_id = 3  # Legacy-Role
    if cmd_type == "Register":
        option["entry_parameter"]["parameter"]["orchestrator"] = orchestrator_id
        in_string = entry_parameter.get('header_section')

    if cmd_type == "Update":
        in_string = entry_parameter.get('header_section')

    if cmd_type == "Restore" or cmd_type == "Discard":
        in_string = current_parameter.get('header_section')

    if in_string is None:
        in_string = ""
    try:
        # YAMLチェック
        tmpFile = "{}/HeaderSectionYamlParse_{}".format(get_OSTmpPath(), os.getpid())
        # /tmpに作成したファイルはゴミ掃除リストに追加
        addAnsibleCreateFilesPath(tmpFile)
        fd = open(tmpFile, 'w')
        fd.write(in_string)
        fd.close()
        obj = YamlParse()
        ret = obj.Parse(tmpFile)
        os.remove(tmpFile)
        if ret is False:
            retBool = False
            error_detail = obj.GetLastError()
            if len(msg) != 0:
                msg += "\n"
            msg = g.appmsg.get_api_message("MSG-10888", [error_detail])

        # Movement一覧にMovement名とオーケストレータに同一のレコードがないかを確認(廃止時はスキップ)
        if retBool is True:
            movement_name = entry_parameter.get('movement_name')
            movement_id = entry_parameter.get('movement_id')
            if not cmd_type == "Discard":
                if cmd_type == "Register":
                    where_str = 'WHERE MOVEMENT_NAME = %s AND ITA_EXT_STM_ID = %s AND DISUSE_FLAG = %s'
                    ret = objdbca.table_select('T_COMN_MOVEMENT', where_str, [movement_name, orchestrator_id, 0])
                elif cmd_type == "Update" or cmd_type == "Restore":
                    # 「更新」「復活」の場合は自分自身のレコードを除外
                    where_str = 'WHERE MOVEMENT_NAME = %s AND ITA_EXT_STM_ID = %s AND MOVEMENT_ID <> %s AND DISUSE_FLAG = %s'
                    ret = objdbca.table_select('T_COMN_MOVEMENT', where_str, [movement_name, orchestrator_id, movement_id, 0])

                # レコードがある場合は重複エラー
                if ret:
                    # オーケストラ名を取得
                    orchestra_nama = None
                    orchestra_record = objdbca.table_select('T_COMN_ORCHESTRA', 'WHERE ORCHESTRA_ID = %s', [orchestrator_id])
                    if orchestra_record:
                        orchestra_nama = orchestra_record[0].get('ORCHESTRA_NAME')
                    # メッセージを作成
                    dict_bind_kv = {'movement_name': movement_name, 'orchestrator': orchestra_nama}
                    json_dict_bind_kv = json.dumps(dict_bind_kv)
                    list_uuids = ret[0].get('MOVEMENT_ID')
                    msg_args = [str(json_dict_bind_kv), str(list_uuids)]
                    msg = g.appmsg.get_api_message('MSG-00006', msg_args)
                    retBool = False

        if retBool is True:
            # バックヤード起動フラグ設定
            table_name = "T_COMN_PROC_LOADED_LIST"
            data_list = {"LOADED_FLG": "0", "ROW_ID": "204"}
            primary_key_name = "ROW_ID"
            ret = objdbca.table_update(table_name, data_list, primary_key_name, False)
            if ret is False:
                msg = g.appmsg.get_api_message("MSG-10888", [os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno])
                retBool = False

        return retBool, msg, option,
    except AppException as e:
        raise AppException(e)
    except Exception as e:
        raise Exception(e)
    finally:
        # /tmpをゴミ掃除
        rmAnsibleCreateFiles()
