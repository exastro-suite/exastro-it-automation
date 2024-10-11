# Copyright 2024 NEC Corporation#
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
import datetime
import os
from flask import g
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common import storage_access
"""
ライブラリ
"""


def read_version_list(file_path):
    """
    version.listを読み込む

    Returns:
        list
    """

    with open(file_path) as f:
        lines = f.readlines()

    version_list = []
    for line in lines:
        # 先頭'#' はコメントとして除外
        if line.startswith('#'):
            continue

        line = line.rstrip()  # 末尾の改行除去

        # 空行は除外
        if len(line) == 0:
            continue

        version_list.append(line)

    return version_list


def get_migration_target_versions(current_version, version_list):
    """
    get versions list

    Returns:
        list: versions
    """

    # current_version が含まれていたら、それ以降のversion_listを返す
    if current_version in version_list:
        g.applogger.info(f"Current version=[{current_version}].")
        index = version_list.index(current_version)
        del version_list[:(index + 1)]
    else:
        raise Exception(f"No such version. version:{current_version}")

    return version_list


def set_version(version):
    """
    set version
    """
    common_db = DBConnectCommon()  # noqa: F405
    data = {
        'SERVICE_ID': 1,
        'VERSION': version
    }
    common_db.db_transaction_start()
    common_db.table_update("T_COMN_VERSION", data, "SERVICE_ID")
    common_db.db_commit()

