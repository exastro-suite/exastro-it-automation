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


def collect_ita_version(objdbca):
    """
        ITAのバージョン情報を取得する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
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
        installed_driver = json.loads(ret[0].get('INSTALLED_DRIVER_JA'))
    else:
        installed_driver = json.loads(ret[0].get('INSTALLED_DRIVER_EN'))

    version_data = {
        "version": ret[0].get('VERSION'),
        "installed_driver": installed_driver
    }
    
    return version_data
