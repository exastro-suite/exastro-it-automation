#   Copyright 2023 NEC Corporation
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

class hostGroupConst():
    """
        ホストグループ関連の定数定義クラス
    """
    # ホストグループ親子関係の階層制限値
    HIERARCHY_LIMIT = 15

    # ホストグループ親子関係の階層制限値(backyard用): HIERARCHY_LIMIT + 1
    HIERARCHY_LIMIT_BKY = HIERARCHY_LIMIT + 1

    # 優先順位(最小-最大)
    MIN_PRIORITY = 0
    MAX_PRIORITY = 2147483647
