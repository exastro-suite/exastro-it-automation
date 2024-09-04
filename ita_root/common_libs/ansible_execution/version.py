#   Copyright 2024 NEC Corporation
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

import os

from common_libs.common import storage_access
from common_libs.common.dbconnect import DBConnectCommon

class AnsibleExexutionVersion:
    """
        エージェントのバージョンに対応する、ITAのバージョンリストを定義する
    """

    def __init__(self):
        # エージェントのバージョン取得
        file_path = "/exastro/common_libs/ansible_execution/VERSION.txt"
        if os.path.exists(file_path):
            obj = storage_access.storage_read()
            obj.open(file_path)
            agent_version = obj.read()
            obj.close()
        else:
            agent_version = ""

        # 『バージョン情報』テーブルからバージョン情報を取得
        common_db = DBConnectCommon()
        ret = common_db.table_select('T_COMN_VERSION', 'WHERE DISUSE_FLAG = %s', [0])

        if len(ret) != 0:
            ita_version = ret[0].get('VERSION')
        else:
            ita_version = ""

        # バージョンリスト
        self.version_list = {agent_version: [ita_version]}

        # ステータス
        self.not_compatible_old = '1' # 古い
        self.compatible_newest = '2' # 最新
        self.compatible = '3' # 最新ではない

    def check_diff_version(self, agent_version):
        """
        エージェントのバージョンチェック
        ARGS:
            agent_version:エージェントのバージョン
        RETRUN:
            比較結果
        """
        # ITAの対応するバージョンと比較
        if agent_version in self.version_list.keys():
            if agent_version in self.version_list[agent_version]:
                for ita_version in self.version_list[agent_version]:
                    # エージェントのバージョンは対応しているが最新ではない
                    if agent_version < ita_version:
                        return self.compatible

                return self.compatible_newest
            else:
                # 対応するバージョンリストにない
                return self.not_compatible_old
        else:
            # 対応するバージョンリストにない
            return self.not_compatible_old