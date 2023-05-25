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
from common_libs.terraform_driver.common.Hcl2Json import HCL2JSONParse
# from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
import re
import base64
import os


def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''
    proc_load_id = 801  # バックヤード起動フラグのID

    # バックヤード起動フラグ設定
    table_name = "T_COMN_PROC_LOADED_LIST"
    data_list = {"LOADED_FLG": "0", "ROW_ID": proc_load_id}
    primary_key_name = "ROW_ID"
    objdbca.table_update(table_name, data_list, primary_key_name, False)

    # 登録/更新時のみ
    cmd_type = option.get("cmd_type")
    if cmd_type in ["Register", "Update"]:
        # 拡張子が「.tf」の場合、パース処理が実行可能かどうかをチェック
        file_name = option.get('entry_parameter', {}).get('parameter', {}).get('module_file')
        if file_name:
            pattern = r'\.tf$'
            match = re.findall(pattern, file_name)
            if match:
                # 一時利用ディレクトリ(/tmpを使用する)
                # base_dir = os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
                # temp_dir = base_dir + TFCloudEPConst.DIR_TEMP
                temp_dir = '/tmp'

                # ファイルを一時ディレクトリに格納
                tf_data = option.get('entry_parameter', {}).get('file', {}).get('module_file', '')
                tf_data_binary = base64.b64decode(tf_data)
                tf_data_decoded = tf_data_binary.decode('utf-8')
                filepath_tmp = "%s/80105_tf_file_%s.tf" % (temp_dir, os.getpid())
                with open(filepath_tmp, "w") as fd:
                    fd.write(tf_data_decoded)

                # tfファイルパース処理を実行する。
                hcl2json = HCL2JSONParse(filepath_tmp)
                hcl2json.executeParse(True)
                result = hcl2json.getParseResult()
                if result.get('res') is False:
                    # パースに失敗した場合、バリデーションエラーとする
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-80007", [result.get('error_msg')])

                # 一時利用ファイルを削除
                os.remove(filepath_tmp)

    return retBool, msg, option,
