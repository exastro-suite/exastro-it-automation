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
import re


def external_valid_menu_before(objdbca, objtable, option):
    retBool = True
    msg = ''

    try:
        cmd_type = option.get("cmd_type")
        if cmd_type in ["Register", "Update", "Restore"]:
            entry_parameter = option.get('entry_parameter')
            directories_to_delete = entry_parameter.get('parameter').get('directories_to_delete')
            chk_path = '{}/{}'.format(get_base_path(), directories_to_delete)
            # 使用禁止: ..
            pattern = re.compile(r"^(.*)\.{2}(.*)$", re.DOTALL)
            tmp_result = pattern.findall(chk_path)
            if len(tmp_result) != 0:
                msg = '.. path error'  ### MSG
                raise Exception()
    except Exception:
        retBool = False
    return retBool, msg, option,


# ファイル削除機能対象パス生成
def get_base_path(organization_id=None, workspace_id=None):
    if organization_id is None or workspace_id is None:
        base_path = "{}{}/{}/".format(os.environ.get('STORAGEPATH'), g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))   # noqa: F405
    else:
        base_path = "{}{}/{}/".format(os.environ.get('STORAGEPATH'), organization_id, workspace_id)   # noqa: F405
    return base_path
