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


class MovementMaterialLinkTable(TableBase):
    """
    Movementロール管理のデータを取得し、定義変数を管理するクラス
    """

    TABLE_NAME = "T_ANSR_MVMT_MATL_LINK"
    PKEY = "MVMT_MATL_LINK_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = MovementMaterialLinkTable.TABLE_NAME
        self.pkey = MovementMaterialLinkTable.PKEY
