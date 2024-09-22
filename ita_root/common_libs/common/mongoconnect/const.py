# Copyright 2023 NEC Corporation#
# Licensed under the Apache License, Version 2.2 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.2
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from pymongo import ASCENDING, DESCENDING


class Const:
    """
    MongoDBに関連する定数を定義するクラス。
    """
    # MongoDBからデータを取得するシートタイプID
    MONGODB_SHEETTYPE_ID = '26'

    # コレクション名
    LABELED_EVENT_COLLECTION = "labeled_event_collection"

    # テーブル名
    T_OASE_EVENT_HISTORY = "T_OASE_EVENT_HISTORY"

    # テーブル名とコレクション名のマッピング
    NAME_MAP: [str, str] = {
        T_OASE_EVENT_HISTORY: LABELED_EVENT_COLLECTION
    }

    # ソート順
    ASCENDING = ASCENDING
    DESCENDING = DESCENDING
