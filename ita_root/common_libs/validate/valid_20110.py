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
import traceback
import sys
from common_libs.ansible_driver.functions.template_render import TemplateRender
from common_libs.common.util import get_iso_datetime, arrange_stacktrace_format
def external_valid_menu_before(objdbca, objtable, option):

    target_column_name = {
        "ja": objtable["COLINFO"]["template_file"]["COLUMN_NAME_JA"],
        "en": objtable["COLINFO"]["template_file"]["COLUMN_NAME_EN"],
    }

    target_lang = g.LANGUAGE if g.LANGUAGE is not None else "ja"

    retBool = True
    msg = ''

    # 入力値取得
    cmd_type = option.get("cmd_type")

    jinja2_file_path = None
    if cmd_type in ["Register", "Update"]:
        jinja2_file_path = option.get('entry_parameter').get('file_path', {}).get('template_file', '')
        if not jinja2_file_path:
            jinja2_file_path = option.get('current_parameter').get('file_path', {}).get('template_file', '')

    if jinja2_file_path:
        try:
            # jinja2の形式として問題無いか確認する
            ret = TemplateRender(os.path.dirname(jinja2_file_path), os.path.basename(jinja2_file_path), {})
        except Exception as e:
            # バックトレース出力
            t = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(get_iso_datetime(), arrange_stacktrace_format(t)))
            retBool = False
            msg = g.appmsg.get_api_message("MSG-10980", [target_column_name[target_lang], str(e)])

    return retBool, msg, option,