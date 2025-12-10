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

    # バージョンリスト ※新しいバージョンを後ろに記載
    VERSION_MATRIX = {
        "2.5.1": ["2.5.1", "2.5.2", "2.5.3", "2.5.4", "2.6.0", "2.6.1", "2.6.2", "2.7.0", "2.7.1"],
        "2.6.0": ["2.5.1", "2.5.2", "2.5.3", "2.5.4", "2.6.0", "2.6.1", "2.6.2", "2.7.0", "2.7.1"],
        "2.7.0": ["2.5.1", "2.5.2", "2.5.3", "2.5.4", "2.6.0", "2.6.1", "2.6.2", "2.7.0", "2.7.1"]
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
        if agent_version in self.VERSION_MATRIX.keys():
            if ita_version in self.VERSION_MATRIX[agent_version]:
                # エージェントの最新バージョンを確認
                latest_agent_version = ""
                for _agent_version in reversed(self.VERSION_MATRIX.keys()):
                    if latest_agent_version == "" and ita_version in self.VERSION_MATRIX[_agent_version]:
                        latest_agent_version = _agent_version
                        break

                if latest_agent_version != "":
                    if agent_version == latest_agent_version:
                        # 最新
                        return self.COMPATIBLE_NEWEST
                    else:
                        # エージェントのバージョンは対応しているが最新ではない
                        return self.COMPATIBLE
            else:
                # 対応するバージョンリストにない
                return self.NOT_COMPATIBLE_OLD
        else:
            # 対応するバージョンリストにない
            return self.NOT_COMPATIBLE_OLD
