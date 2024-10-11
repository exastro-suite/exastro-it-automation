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
from common_libs.ansible_driver.functions.ui_util import getColumnValue
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = []

    target_lang = g.LANGUAGE if g.LANGUAGE is not None else "ja"
    if target_lang == "ja":
        lang_col_name = "COLUMN_NAME_JA"
    else:
        lang_col_name = "COLUMN_NAME_EN"
    # 1:手動　2:IAT
    str_build_type = getColumnValue(option, "Execution_environment_build_type", PasswordCol=False)
    str_tag_name = getColumnValue(option, "tag_name", PasswordCol=False)
    str_definition_name = getColumnValue(option, "Execution_environment_definition_name", PasswordCol=False)
    str_template_name = getColumnValue(option, "template_name", PasswordCol=False)
    # 2:その他　1:Redhat
    str_base_image_os_type = getColumnValue(option, "base_image_os_type", PasswordCol=False)
    str_user_name = getColumnValue(option, "user_name", PasswordCol=False)
    str_password = getColumnValue(option, "password", PasswordCol=True)
    str_attach_repository = getColumnValue(option, "attach_repository", PasswordCol=True)

    # Ansible Egent 実行環境構築方法
    DF_AG_BUILD_TYPE_MANUAL = '1'
    DF_AG_BUILD_TYPE_ITA = '2'

    # Ansible Egent ベースイメージOS種別
    DF_AG_BASE_IMAGE_TYPE_REDHAT = '1'
    DF_AG_BASE_IMAGE_TYPE_OTHOR = '2'
    # 実行環境構築方法が手動の場合
    manual_req_col = []
    redhat_req_col = []
    # Ansible Egent 実行環境構築方法が手動の場合の必須入力チェック
    if str_build_type == AnscConst.DF_AG_BUILD_TYPE_ITA:
        if not str_definition_name:
            manual_req_col.append(objtable['COLINFO']["Execution_environment_definition_name"][lang_col_name])
        if not str_template_name:
            manual_req_col.append(objtable['COLINFO']["template_name"][lang_col_name])
        if not str_base_image_os_type:
            manual_req_col.append(objtable['COLINFO']["base_image_os_type"][lang_col_name])
        if not str_user_name:
            # Ansible Egent ベースイメージOS種別がredhatの場合の必須入力チェック
            if str_base_image_os_type == AnscConst.DF_AG_BASE_IMAGE_TYPE_REDHAT:
                redhat_req_col.append(objtable['COLINFO']["user_name"][lang_col_name])
        if not str_password:
            # Ansible Egent ベースイメージOS種別がredhatの場合の必須入力チェック
            if str_base_image_os_type == AnscConst.DF_AG_BASE_IMAGE_TYPE_REDHAT:
                redhat_req_col.append(objtable['COLINFO']["password"][lang_col_name])
        if not str_attach_repository:
            # Ansible Egent ベースイメージOS種別がredhatの場合の必須入力チェック
            if str_base_image_os_type == AnscConst.DF_AG_BASE_IMAGE_TYPE_REDHAT:
                redhat_req_col.append(objtable['COLINFO']["attach_repository"][lang_col_name])

    if len(manual_req_col) != 0:
        retBool = False
        col_list = ", ".join(manual_req_col)
        msg.append(g.appmsg.get_api_message("MSG-10978", [col_list]))
    if len(redhat_req_col) != 0:
        retBool = False
        col_list = ", ".join(redhat_req_col)
        msg.append(g.appmsg.get_api_message("MSG-10979", [col_list]))
    return retBool, msg, option,