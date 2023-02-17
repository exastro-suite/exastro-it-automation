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

from flask import g  # noqa: F401

from common_libs.hostgroup.classes.hostgroup_table_class import *  # noqa: F403
from common_libs.hostgroup.functions.split_function import *  # noqa: F403
from common_libs.hostgroup.classes.hostgroup_const import *  # noqa: F403


def external_valid_menu_after(objdbca, objtable, option):
    retBool = True
    msg = ''

    # ホストグループ分割対象を全てのDIVIDED_FLG=0にする
    result = reset_split_target_flg(objdbca)  # noqa: F405
    if result is False:
        raise Exception()

    return retBool, msg, option, False
