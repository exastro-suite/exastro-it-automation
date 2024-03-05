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
    uploadPath = os.environ.get('STORAGEPATH') + "/".join([g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID')]) + "/tmp/custom_menu_item/"

    # ファイルがある場合バリデーションチェック
    if 'custom_menu_item' in option["entry_parameter"]["parameter"] and 'custom_menu_item' in option["entry_parameter"]["file"]:
        file_name = option["entry_parameter"]["parameter"]["custom_menu_item"]
        zip_data = option["entry_parameter"]["file"]["custom_menu_item"]

        if not os.path.exists(uploadPath):
            os.makedirs(uploadPath)
            os.chmod(uploadPath, 0o777)

        # 検証用にアップロード、終了後削除
        ret = upload_file(uploadPath + file_name, zip_data)

        if ret is False:
            if os.path.exists(uploadPath):
                shutil.rmtree(uploadPath)

        try:
            # ファイルがzip形式か確認
            if not file_name.endswith('.zip'):
                if os.path.exists(uploadPath):
                    shutil.rmtree(uploadPath)
                errormsg = g.appmsg.get_api_message("499-00308")
                return False, errormsg, option

            if zipfile.is_zipfile(uploadPath + file_name):
                with zipfile.ZipFile(uploadPath + file_name) as z:
                    for info in z.infolist():
                        info.filename = info.orig_filename.encode('cp437').decode('cp932')
                        if os.sep != "/" and os.sep in info.filename:
                            info.filename = info.filename.replace(os.sep, "/")
                        z.extract(info, path=uploadPath)

                lst = os.listdir(uploadPath)

                fileAry = []
                for value in lst:
                    if not value == '.' and not value == '..':
                        path = os.path.join(uploadPath, value)
                        if os.path.isdir(path):
                            dir_name = value
                            sublst = os.listdir(path)
                            for subvalue in sublst:
                                if not subvalue == '.' and not subvalue == '..':
                                    fileAry.append(dir_name + "/" + subvalue)
                        else:
                            fileAry.append(value)

                # 必須ファイルの確認
                errFlg = True
                for value in fileAry:
                    if 'main.html' == value:
                        errFlg = False

                if errFlg is True:
                    if os.path.exists(uploadPath):
                        shutil.rmtree(uploadPath)
                    errormsg = g.appmsg.get_api_message("499-00307")
                    return False, errormsg, option
            else:
                if os.path.exists(uploadPath):
                    shutil.rmtree(uploadPath)
                errormsg = g.appmsg.get_api_message("499-00308")
                return False, errormsg, option

        except Exception as e:
            if os.path.exists(uploadPath):
                shutil.rmtree(uploadPath)
            errormsg = g.appmsg.get_api_message("499-00308")
            return False, errormsg, option


    # ファイル削除
    if os.path.exists(uploadPath):
        shutil.rmtree(uploadPath)

    return retBool, msg, option,
