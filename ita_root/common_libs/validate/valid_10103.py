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
import os
import zipfile

from common_libs.common import *  # noqa: F403


def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''

    # 削除時はチェックしない
    # Do not check when deleting
    if option.get("cmd_type") == "Delete":
        return retBool, msg, option

    # ファイルがある場合バリデーションチェック
    if 'custom_menu_item' in option["entry_parameter"]["parameter"] and 'custom_menu_item' in option["entry_parameter"]["file_path"]:
        file_name = option["entry_parameter"]["parameter"]["custom_menu_item"]
        zip_data_path = option["entry_parameter"]["file_path"]["custom_menu_item"]

        # ファイル名がzip形式か確認
        if not file_name.endswith('.zip'):
            errormsg = g.appmsg.get_api_message("499-00308")
            return False, errormsg, option

        # ファイルがzip形式か確認
        if zipfile.is_zipfile(zip_data_path):
            # 必須ファイルの確認
            errFlg = True
            with zipfile.ZipFile(zip_data_path, "r") as z:
                for info in z.infolist():
                    if 'main.html' == info.filename:
                        errFlg = False
                        break
            if errFlg is True:
                errormsg = g.appmsg.get_api_message("499-00307")
                return False, errormsg, option
        else:
            errormsg = g.appmsg.get_api_message("499-00308")
            return False, errormsg, option

    return retBool, msg, option,
