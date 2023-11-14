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

from flask import g
from common_libs.common import *

# import column_class
from .multi_select_id_class import MultiSelectIDColumn  # noqa: F401


class NotificationIDColumn(MultiSelectIDColumn):
    """
    カラムクラス個別処理(通知先 IDColumn)
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
        values[str(1)] = 'Ｋｅｙ1'
        values[str(2)] = 'Ｋｅｙ2'
        values[str(3)] = 'Ｋｅｙ3'
        values[str(4)] = 'Ｋｅｙ4'
        values[str(5)] = 'Ｋｅｙ5'
        values[str(6)] = 'Ｋｅｙ6'
        values[str(7)] = 'Ｋｅｙ7'
        values[str(8)] = 'Ｋｅｙ8'
        values[str(9)] = 'Ｋｅｙ9'
        values[str(10)] = 'Ｋｅｙ10'

        return values

