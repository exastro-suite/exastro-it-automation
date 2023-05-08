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
#

from flask import g  # noqa: F401
import re
import json


# バリデーションチェック
def conductor_notice_valid(objdbca, objtable, option):  # noqa: C901

    retBool = True
    msg = []
    cmd_type = option.get("cmd_type")
    entry_parameter = option.get('entry_parameter').get('parameter')
    if cmd_type == "Restore":
        entry_parameter = option.get("current_parameter").get("parameter")

    if cmd_type in ["Register", "Update", "Restore"]:
        # urlチェック対象
        notice_url = entry_parameter.get("notice_url")
        proxy_url = entry_parameter.get("proxy_url")
        fqdn = entry_parameter.get("fqdn")

        # url正規表現
        url_regex = re.compile(r"https?://[\W\w]+")

        check_notice_url = url_regex.fullmatch(notice_url)
        if check_notice_url is None:
            msg.append(g.appmsg.get_api_message("MSG-40042"))
        if proxy_url:
            check_proxy_url = url_regex.fullmatch(proxy_url)
            if check_proxy_url is None:
                msg.append(g.appmsg.get_api_message("MSG-40043"))
        if fqdn:
            check_fqdn = url_regex.fullmatch(fqdn)
            if check_fqdn is None:
                msg.append(g.appmsg.get_api_message("MSG-40044"))

        # json形式チェック
        message = entry_parameter.get("fields")
        header = entry_parameter.get("header")
        try:
            ret = json.loads(header)
            dict_check = isinstance(ret, dict)
            if dict_check is False:
                raise Exception
        except Exception:
            msg.append(g.appmsg.get_api_message("MSG-40045"))
        try:
            json.loads(message)
        except Exception:
            msg.append(g.appmsg.get_api_message("MSG-40046"))

        if len(msg) >= 1:
            # msg に値がある場合は個別バリデエラー
            retBool = False

    return retBool, msg, option
