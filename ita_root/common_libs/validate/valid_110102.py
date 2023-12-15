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
import re

import chardet
import jinja2
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

    retBool = True
    msg = ''

    # 対象のメニューは更新の操作のみ実施可能なため「cmd_type」はチェックしない

    template_data = option.get('entry_parameter', {}).get('file', {}).get('template_file', '')
    template_data_binary = base64.b64decode(template_data)

    # 文字コードをチェック バイナリファイルの場合、encode['encoding']はNone
    encode = chardet.detect(template_data_binary)
    if encode['encoding'] is None:
        retBool = False
        msg_tmp = g.appmsg.get_api_message("499-01901")
        msg = msg_tmp if len(msg) <= 0 else '%s\n%s' % (msg, msg_tmp)

    template_data_decoded = template_data_binary.decode('utf-8', 'ignore')
    if retBool:
        # jinja2の形式として問題無いか確認する
        try:
            jinja2.Template(template_data_decoded)
        except Exception:
            retBool = False
            msg_tmp = g.appmsg.get_api_message("499-01902")
            msg = msg_tmp if len(msg) <= 0 else '%s\n%s' % (msg, msg_tmp)

    if retBool:
        # 特有の構文チェック
        title_count = len(re.findall(r'\[TITLE\]', template_data_decoded))
        if title_count != 1:
            retBool = False
            msg_tmp = g.appmsg.get_api_message("499-01903")
            msg = msg_tmp if len(msg) <= 0 else '%s\n%s' % (msg, msg_tmp)

        title_body = len(re.findall(r'\[BODY\]', template_data_decoded))
        if title_body != 1:
            retBool = False
            msg_tmp = g.appmsg.get_api_message("499-01904")
            msg = msg_tmp if len(msg) <= 0 else '%s\n%s' % (msg, msg_tmp)

    return retBool, msg, option,
