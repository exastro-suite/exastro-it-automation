# Copyright 2023 NEC Corporation#
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

import datetime
import json

from bson.objectid import ObjectId
from common_libs.common.mongoconnect.collection_base import CollectionBase


class LabeledEventCollection(CollectionBase):
    """
    LabeledEventCollection

        labeled_event_collectionの検索条件を生成するクラス

    """

    RANGE_LIST = [
        "_exastro_fetched_time",
        "_exastro_end_time"
    ]

    LABELS_PARAMETER = None

    def _is_separated_supported_item(self, rest_key_name, type):
        # _exastro_event_statusにLISTが指定された場合$orを使用する必要があるため個別対応とした
        if rest_key_name == "_exastro_event_status" and type == "LIST":
            return True

        if rest_key_name == "labels":
            return True

        return False

    def _convert_parameter_item_name_to_collection_item_name(self, rest_key_name, value):
        tmp_item_name = super()._convert_parameter_item_name_to_collection_item_name(rest_key_name, value)

        simple_convert_map = {
            "_exastro_event_collection_settings_id": ["labels._exastro_event_collection_settings_id"],
            "_exastro_fetched_time": ["labels._exastro_fetched_time"],
            "_exastro_end_time": ["labels._exastro_end_time"],
            "_exastro_type": ["labels._exastro_type"],
            "_exastro_rule_name": ["labels._exastro_rule_name"],
            "_exastro_events": ["exastro_events"],
            "_exastro_event_status": ["labels._exastro_timeout", "labels._exastro_evaluated", "labels._exastro_undetected"]
        }

        if rest_key_name in simple_convert_map:
            return simple_convert_map[rest_key_name]

        return tmp_item_name

    def _create_search_value(self, collection_item_name, value):
        tmp_value = super()._create_search_value(collection_item_name, value)

        if collection_item_name == "labels._exastro_fetched_time":
            return str(int(datetime.datetime.strptime(tmp_value, '%Y-%m-%dT%H:%M:%S%z').timestamp()))

        if collection_item_name == "labels._exastro_end_time":
            return str(int(datetime.datetime.strptime(tmp_value, '%Y-%m-%dT%H:%M:%S%z').timestamp()))

        if collection_item_name == "labels._exastro_timeout":
            if value == "時間切れ":
                return "1"
            else:
                return "0"

        if collection_item_name == "labels._exastro_evaluated":
            if value == "ルールマッチ済み":
                return "1"
            else:
                return "0"

        if collection_item_name == "labels._exastro_undetected":
            if value == "未知イベント":
                return "1"
            else:
                return "0"

        if collection_item_name == "labels._exastro_type":
            if value == "イベント":
                return "event"
            elif value == "再評価":
                return "conclusion"

        if collection_item_name == "exastro_events":
            return ObjectId(tmp_value)

        return tmp_value

    def _create_separated_supported_search_value(self, rest_key_name, type, value):
        # _exastro_event_statusにLISTが指定された場合$orを使用する必要があるため個別対応とした
        if rest_key_name == "_exastro_event_status" and type == "LIST":
            tmp_list: list = value
            if len(tmp_list) == 1:

                return self.__create_exastro_event_status_search_value(tmp_list[0])

            elif len(tmp_list) > 1:
                result_list = []
                for item in tmp_list:
                    result_list.append(self.__create_exastro_event_status_search_value(item))

                return {"$or": result_list}

            else:
                return {}

        if rest_key_name == "labels":
            # labelsのフィルタリングは_format_result_valueで行うため、ここではフィールドへ値の退避のみ行う。
            self.LABELS_PARAMETER = {type: value}
            return {}

        return {rest_key_name: value}

    def __create_exastro_event_status_search_value(self, item):
        if item == "検討中":
            return {
                "labels._exastro_timeout": "0",
                "labels._exastro_evaluated": "0",
                "labels._exastro_undetected": "0"
            }

        elif item == "時間切れ":
            return {
                "labels._exastro_timeout": "1",
                "labels._exastro_evaluated": "0",
                "labels._exastro_undetected": "0"
            }

        elif item == "ルールマッチ済み":
            return {
                "labels._exastro_timeout": "0",
                "labels._exastro_evaluated": "1",
                "labels._exastro_undetected": "0"
            }

        elif item == "未知イベント":
            return {
                "labels._exastro_timeout": "0",
                "labels._exastro_evaluated": "0",
                "labels._exastro_undetected": "1"
            }
        else:
            return {}

    def _format_result_value(self, item):
        format_item = super()._format_result_value(item)

        # イベント状態の判定で使用するマップ。
        # 判定する値は左から_exastro_timeout, _exastro_evaluated, _exastro_undetectedの順に文字列結合する想定。
        event_status_map = {
            "000": "検討中",
            "001": "未知イベント",
            "010": "ルールマッチ済み",
            "100": "時間切れ"
        }

        # イベント種別の判定で使用するマップ
        event_type_map = {
            "event": "イベント",
            "conclusion": "再評価"
        }

        # labels配下の特定項目は一段上に引き上げる必要がある。
        # また、該当しない項目もそのままlabelsとして返却する必要がある。
        # そのため、元のオブジェクトからはpopで値を削除し重複して表示されないようにする。
        if "labels" in item:
            labels = dict(item["labels"])

            if "_exastro_event_collection_settings_id" in labels:
                format_item["_exastro_event_collection_settings_id"] = labels.pop("_exastro_event_collection_settings_id")

            if "_exastro_fetched_time" in labels:
                ts = int(labels.pop("_exastro_fetched_time"))
                dt = datetime.datetime.fromtimestamp(ts)
                format_item["_exastro_fetched_time"] = dt.strftime("%Y/%m/%d %H:%M:%S")

            if "_exastro_end_time" in labels:
                ts = int(labels.pop("_exastro_end_time"))
                dt = datetime.datetime.fromtimestamp(ts)
                format_item["_exastro_end_time"] = dt.strftime("%Y/%m/%d %H:%M:%S")

            # イベント状態の判定で使用する値を組み立てる。
            # 3種とも確実に存在する前提だが、dictの存在チェックを利用する都合により取得できない場合は0を設定する。
            tmp_status = labels.pop("_exastro_timeout") if "_exastro_timeout" in labels else '0'
            tmp_status += labels.pop("_exastro_evaluated") if "_exastro_evaluated" in labels else '0'
            tmp_status += labels.pop("_exastro_undetected") if "_exastro_undetected" in labels else '0'

            format_item["_exastro_event_status"] = event_status_map.get(tmp_status)

            if "_exastro_type" in labels:
                format_item["_exastro_type"] = event_type_map[labels.pop("_exastro_type")]

            if "_exastro_rule_name" in labels:
                format_item["_exastro_rule_name"] = labels.pop("_exastro_rule_name")

            # 残項目はlabelsとして返却するため代入する。
            format_item["labels"] = labels

        if "exastro_events" in item:
            exastro_events = list(item["exastro_events"])

            format_item["_exastro_events"] = []
            for item in exastro_events:
                # eventsは再評価イベントを作成するきっかけとなったイベントの_idが格納されている。
                # そのままではJSONとして扱えないため_idと同じように変換する。
                format_item["_exastro_events"].append(str(item))

        # LABELS_PARAMETERがNoneではない場合、labelsに対する条件が指定されているため確認を行う。
        # labelsの検索の要件をMongoDBの検索時に満たそうとするとサブドキュメントに対してあいまい検索が必要となる。
        # しかし、確認した限りだと文字列型以外にあいまい検索は不可のためpython側での対応とした
        if self.LABELS_PARAMETER is not None:
            tmp_str = json.dumps(format_item["labels"])
            for type, value in self.LABELS_PARAMETER.items():
                if type == "NORMAL":
                    value = [value]

                for item in value:
                    if item in tmp_str:
                        return format_item

            # ここまで処理が流れた場合、labelsが条件を満たす内容ではないためNoneを返却する
            # Noneを返却 = 画面に返却しないデータとして処理する
            return None

        return format_item
