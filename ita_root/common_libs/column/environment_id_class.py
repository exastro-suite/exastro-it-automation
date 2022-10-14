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

import os
import sys
from flask import g
from common_libs.common import *  # noqa: F403

# import column_class
from .id_class import IDColumn


class EnvironmentIDColumn(IDColumn):
    """
    カラムクラス個別処理(EnvironmentIDColumn)
    """
    def search_id_data_list(self):
        """
            データリストを検索する
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        values = {}

        # ExastroPlatformから環境の一覧を取得
        environments = util.get_exastro_platform_workspaces()[1]

        # key=valueの配列をつくる
        for environment in environments:
            values[environment] = environment

        return values
