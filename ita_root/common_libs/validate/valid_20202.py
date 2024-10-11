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

from flask import g
import os
import base64
import inspect

from chardet import detect

from common_libs.ansible_driver.classes.YamlParseClass import YamlParse
from common_libs.ansible_driver.classes.WrappedStringReplaceAdmin import WrappedStringReplaceAdmin
from common_libs.ansible_driver.functions.commn_vars_used_list_update import CommnVarsUsedListUpdate, CommnVarsUsedListDisuseSet
from common_libs.ansible_driver.functions.util import get_OSTmpPath
from common_libs.ansible_driver.functions.util import addAnsibleCreateFilesPath
from common_libs.ansible_driver.functions.util import rmAnsibleCreateFiles
from common_libs.common.exception import AppException
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst


def external_valid_menu_after(objDBCA, objtable, option):
    # /tmpに作成したファイル・ディレクトリパスを保存するファイル名
    g.AnsibleCreateFilesPath = "{}/{}_{}".format(get_OSTmpPath(), os.path.basename(inspect.currentframe().f_code.co_filename), os.getpid())

    retBool = True
    msg = ''

    # 入力値取得
    entry_parameter = option.get('entry_parameter').get('parameter')
    current_parameter = option.get('current_parameter').get('parameter')
    cmd_type = option.get("cmd_type")

    try:
        pkey = None
        if cmd_type in ["Discard", "Restore", "Update"]:
            pkey = current_parameter["item_no"]

        elif cmd_type == "Register" and "uuid" in option:
            pkey = option["uuid"]

        playbook_path = None
        if cmd_type in ["Register", "Update"]:
            if "playbook_file" not in option.get("entry_parameter", {}).get("parameter", {}):
                # Excelで更新の場合は処理をスキップ
                pass
            else:
                tmp_playbook_path = os.path.dirname(option.get('entry_parameter', {}).get('file_path', {}).get('playbook_file', ''))
                if cmd_type == "Update":
                    tmp_playbook_path = os.path.dirname(option.get('current_parameter', {}).get('file_path', {}).get('playbook_file', ''))
                playbook_filename = option.get('entry_parameter', {}).get('parameter', {}).get('playbook_file', '')
                playbook_path = tmp_playbook_path + "/" + playbook_filename
        # 廃止/復活時の場合、関連レコードを廃止/復活
        if cmd_type in ["Discard", "Restore"]:
            ret, msg_tmp = CommnVarsUsedListDisuseSet(objDBCA, option, pkey, '1')
            if ret is False:
                retBool = False
                msg = msg_tmp if len(msg) <= 0 else '%s\n%s' % (msg, msg_tmp)

        # 登録/更新時の場合、Playbookの正常性チェック
        elif cmd_type in ["Register", "Update"] and playbook_path is not None:
            # 文字コードをチェック バイナリファイルの場合、encode['encoding']はNone
            with open(playbook_path, 'rb') as f:  # バイナリファイルとしてファイルをオープン
                playbook_data_binary = f.read()
            # 文字コードがUTF-8以外もありうるので'ignore'を付ける
            playbook_data_decoded = playbook_data_binary.decode('utf-8', 'ignore')

            # YAML形式であることをチェック
            obj = YamlParse()
            ret = obj.Parse(playbook_path)

            if ret is False:
                retBool = False
                error_detail = obj.GetLastError()
                msg_tmp = g.appmsg.get_api_message("MSG-10905", [error_detail])
                msg = msg_tmp if len(msg) <= 0 else '%s\n%s' % (msg, msg_tmp)

            if retBool is True:
                # 文字コードをチェック バイナリファイルの場合、encode['encoding']はNone
                encode = detect(playbook_data_binary)
                if encode['encoding'] is None:
                    retBool = False
                    msg_tmp = g.appmsg.get_api_message("MSG-10638")
                    msg = msg_tmp if len(msg) <= 0 else '%s\n%s' % (msg, msg_tmp)

            if retBool is True:
                # 文字コードを取得
                encode = encode['encoding'].upper()
                # BOM有をチェック
                if encode in ["UTF-8-SIG"]:
                    retBool = False
                    msg_tmp = g.appmsg.get_api_message("MSG-10640")
                    msg = msg_tmp if len(msg) <= 0 else '%s\n%s' % (msg, msg_tmp)

                elif encode not in ["ASCII", "UTF-8"]:
                    retBool = False
                    msg_tmp = g.appmsg.get_api_message("MSG-10638")
                    msg = msg_tmp if len(msg) <= 0 else '%s\n%s' % (msg, msg_tmp)

                # 変数抜出
                VarsAry = {}
                VarsAry['1'] = {}  # GBL_
                VarsAry['2'] = {}  # CPF_
                VarsAry['3'] = {}  # TPF_

                vars_line_array = []
                local_vars = []

                size_error_vars = []
                wsra = WrappedStringReplaceAdmin(objDBCA)
                vars_array = []
                _, vars_line_array = wsra.SimpleFillterVerSearch(AnscConst.DF_HOST_VAR_HED, playbook_data_decoded, vars_line_array, vars_array, local_vars, False)
                for v in vars_array:
                    if len(str(v)) > 255:
                        size_error_vars.append(v)

                vars_array = []
                _, vars_line_array = wsra.SimpleFillterVerSearch(AnscConst.DF_HOST_GBL_HED, playbook_data_decoded, vars_line_array, vars_array, local_vars, False)
                for v in vars_array:
                    if len(str(v)) > 255:
                        size_error_vars.append(v)
                    VarsAry['1'][v] = 0

                vars_array = []
                _, vars_line_array = wsra.SimpleFillterVerSearch(AnscConst.DF_HOST_CPF_HED, playbook_data_decoded, vars_line_array, vars_array, local_vars, False)
                for v in vars_array:
                    if len(str(v)) > 255:
                        size_error_vars.append(v)
                    VarsAry['2'][v] = 0

                vars_array = []
                _, vars_line_array = wsra.SimpleFillterVerSearch(AnscConst.DF_HOST_TPF_HED, playbook_data_decoded, vars_line_array, vars_array, local_vars, False)
                for v in vars_array:
                    if len(str(v)) > 255:
                        size_error_vars.append(v)
                    VarsAry['3'][v] = 0

                # 255バイト以上の変数が使用されている場合
                if len(size_error_vars) > 0:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-10901", [str(size_error_vars)])

                if retBool is True:
                    # 変数登録
                    ret, msg_tmp = CommnVarsUsedListUpdate(objDBCA, option, pkey, '1', VarsAry)
                    if ret is False:
                        retBool = False
                        msg = msg_tmp if len(msg) <= 0 else '%s\n%s' % (msg, msg_tmp)

        if retBool is True:
            # バックヤード起動フラグ設定
            table_name = "T_COMN_PROC_LOADED_LIST"
            data_list = {"LOADED_FLG": "0", "ROW_ID": "202"}
            primary_key_name = "ROW_ID"
            objDBCA.table_update(table_name, data_list, primary_key_name, False)

        return retBool, msg, option
    except AppException as e:
        raise AppException(e)
    except Exception as e:
        raise Exception(e)
    finally:
        # /tmpをゴミ掃除
        rmAnsibleCreateFiles()
