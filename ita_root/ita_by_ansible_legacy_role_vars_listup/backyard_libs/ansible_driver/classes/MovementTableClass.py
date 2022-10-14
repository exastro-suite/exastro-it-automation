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

from .TableBaseClass import TableBase


class MovementTable(TableBase):
    """
    Movementとそれに関連する変数定義を管理する
    (Movement一覧だけの管理ではない)
    """

    TABLE_NAME = "V_ANSR_MOVEMENT"
    PKEY = "MOVEMENT_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = MovementTable.TABLE_NAME
        self.pkey = MovementTable.PKEY
