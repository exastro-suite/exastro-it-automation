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

from common_libs.common import storage_access
from common_libs.common.dbconnect import DBConnectCommon

class AnsibleExexutionVersion:
    """
        エージェントのバージョンに対応する、ITAのバージョンリストを定義する
    """

    # バージョンリスト
    VERSION_MATRIX = {
        "2.5.1": ["2.5.1", "2.5.2", "2.5.3"]
    }

    # ステータス
    NOT_COMPATIBLE_OLD = '1' # 古い
    COMPATIBLE_NEWEST = '2' # 最新
    COMPATIBLE = '3' # 最新ではない

    def check_diff_version(self, agent_version):
        """
        エージェントのバージョンチェック
        ARGS:
            agent_version:エージェントのバージョン
        RETRUN:
            比較結果
        """
        # 『バージョン情報』テーブルからバージョン情報を取得
        common_db = DBConnectCommon()
        ret = common_db.table_select('T_COMN_VERSION', 'WHERE DISUSE_FLAG = %s', [0])

        if len(ret) != 0:
            ita_version = ret[0].get('VERSION')
        else:
            ita_version = ""

        common_db.db_disconnect()

        # ITAの対応するバージョンと比較
        if agent_version in AnsibleExexutionVersion.VERSION_MATRIX.keys():
            if ita_version in AnsibleExexutionVersion.VERSION_MATRIX[agent_version]:
                # エージェントのバージョンは対応しているが最新ではない
                if agent_version < ita_version:
                    return AnsibleExexutionVersion.COMPATIBLE

                return AnsibleExexutionVersion.COMPATIBLE_NEWEST
            else:
                # 対応するバージョンリストにない
                return AnsibleExexutionVersion.NOT_COMPATIBLE_OLD
        else:
            # 対応するバージョンリストにない
            return AnsibleExexutionVersion.NOT_COMPATIBLE_OLD
