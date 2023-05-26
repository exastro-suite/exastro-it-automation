#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import json
from common_libs.common import *  # noqa: F403
from flask import g
from common_libs.common.exception import AppException


def collect_ita_version(objdbca, organization_id):
    """
        ITAのバージョン情報を取得する
        ARGS:
            objdbca: DB接クラス  DBConnectWs()
            organization_id: organization id
        RETRUN:
            version_data
    """

    # 変数定義
    lang = g.get('LANGUAGE')

    # 『バージョン情報』テーブルからバージョン情報を取得
    ret = objdbca.table_select('T_COMN_VERSION', 'WHERE DISUSE_FLAG = %s', [0])

    # 件数確認
    if len(ret) != 1:
        raise AppException("499-00601")

    if lang == 'ja':
        installed_driver_tmp = json.loads(ret[0].get('INSTALLED_DRIVER_JA'))
    else:
        installed_driver_tmp = json.loads(ret[0].get('INSTALLED_DRIVER_EN'))

    # Organizationの情報取得
    org_info = objdbca.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE `ORGANIZATION_ID`=%s AND `DISUSE_FLAG`=%s", [organization_id, '0'])
    no_install_driver = org_info[0].get('NO_INSTALL_DRIVER')

    if no_install_driver is None or len(no_install_driver) == 0:
        no_install_driver_list = []
    else:
        no_install_driver_list = json.loads(no_install_driver)

    installed_driver = []
    for key, value in installed_driver_tmp.items():
        if key not in no_install_driver_list:
            installed_driver.append(value)

    version_data = {
        "version": ret[0].get('VERSION'),
        "installed_driver": installed_driver
    }

    return version_data
