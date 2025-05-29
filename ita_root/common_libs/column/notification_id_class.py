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
from common_libs.notification.notification_base import Notification


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
        values = Notification.fetch_notification_destination_dict()

        self.data_list_set_flg = True

        return values

