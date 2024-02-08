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
#

import base64

from common_libs.notification import validator
from flask import g


def external_valid_menu_before(objdbca, objtable, option):
    """
    メニューバリデーション(更新)
    ARGS:
        objdbca :DB接続クラスインスタンス
        objtabl :メニュー情報、カラム紐付、関連情報
        option :パラメータ、その他設定値
    RETRUN:
        retBoo :True/ False
        msg :エラーメッセージ
        option :受け取ったもの
    """

    target_column_name = {
        "ja": objtable["COLINFO"]["template_file"]["COLUMN_NAME_JA"],
        "en": objtable["COLINFO"]["template_file"]["COLUMN_NAME_EN"],
    }

    target_lang = g.LANGUAGE if g.LANGUAGE is not None else "ja"

    retBool = True
    msg = []

    # 対象のメニューは更新の操作のみ実施可能なため「cmd_type」はチェックしない

    template_data = option.get('entry_parameter', {}).get('file', {}).get('template_file', '')
    template_data_binary = base64.b64decode(template_data)

    # 文字コードをチェック バイナリファイルの場合、encode['encoding']はNone
    if validator.is_binary_file(template_data_binary):
        retBool = False
        msg_tmp = g.appmsg.get_api_message("499-01814", [target_column_name[target_lang]])
        msg.append(msg_tmp)

    template_data_decoded = template_data_binary.decode('utf-8', 'ignore')
    if retBool:
        # jinja2の形式として問題無いか確認する
        if not validator.is_jinja2_template(template_data_decoded):
            retBool = False
            msg_tmp = g.appmsg.get_api_message("499-01815", [target_column_name[target_lang]])
            msg.append(msg_tmp)

    if retBool:
        # 特有の構文チェック
        if not validator.contains_title(template_data_decoded):
            retBool = False
            msg_tmp = g.appmsg.get_api_message("499-01816", [target_column_name[target_lang]])
            msg.append(msg_tmp)

        if not validator.contains_body(template_data_decoded):
            retBool = False
            msg_tmp = g.appmsg.get_api_message("499-01817", [target_column_name[target_lang]])
            msg.append(msg_tmp)

    return retBool, msg, option,
