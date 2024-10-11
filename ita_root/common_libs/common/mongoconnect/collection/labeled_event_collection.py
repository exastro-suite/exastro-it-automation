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
from flask import g
import re
from bson.objectid import ObjectId

from common_libs.common.exception import AppException
from common_libs.common.mongoconnect.collection_base import CollectionBase
from common_libs.oase.const import oaseConst


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

    def _create_search_value(self, collection_item_name, value, event_data_dict, column_name_dict=None):
        # tmp_value = super()._create_search_value(collection_item_name, value)
        tmp_value_list = []
        if collection_item_name == "_id":
            try:
                tmp_value = ObjectId(value)
            except Exception:
                msg_tmp = {0: {}}
                # ObjectId: Only exact match search is possible for object ID. (Input value:{})
                msg_tmp[0][column_name_dict["11010401"]] = [g.appmsg.get_api_message("499-01824", [value])]
                msg = json.dumps(msg_tmp, ensure_ascii=False)
                raise AppException("499-00201", [msg], [msg])
            return tmp_value

        elif collection_item_name in ["labels._exastro_fetched_time", "labels._exastro_end_time"]:
            # 日付形式のチェック
            # Noneまたは空文字の場合はエラー
            if value is None or len(value) == 0:
                retBool = False
            # YYYY/MM/DD hh:mm:ssの場合OK
            elif re.match(r'^[0-9]{4}/(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01]) ([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$', value) is not None:
                retBool = True
                format = '%Y/%m/%d %H:%M:%S'
            # YYYY/MM/DD hh:mmの場合OK
            elif re.match(r'^[0-9]{4}/(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01]) ([01][0-9]|2[0-3]):[0-5][0-9]$', value) is not None:
                retBool = True
                format = '%Y/%m/%d %H:%M'
            # YYYY/MM/DD hhの場合OK
            elif re.match(r'^[0-9]{4}/(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01]) ([01][0-9]|2[0-3])$', value) is not None:
                retBool = True
                format = '%Y/%m/%d %H'
            # YYYY/MM/DDの場合OK
            elif re.match(r'^[0-9]{4}/(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])$', value) is not None:
                retBool = True
                format = '%Y/%m/%d'
            else:
                retBool = False

            if retBool is False:
                msg_tmp = {0: {}}
                if collection_item_name == "labels._exastro_fetched_time":
                    # Fetched time: The value format (YYYY/MM/DD hh:mm:ss) is invalid.( input value: {} )
                    msg_tmp[0][column_name_dict["11010403"]] = [g.appmsg.get_api_message("MSG-00002", ['YYYY/MM/DD hh:mm:ss', value])]
                else:
                    # End time: The value format (YYYY/MM/DD hh:mm:ss) is invalid.( input value: {} )
                    msg_tmp[0][column_name_dict["11010404"]] = [g.appmsg.get_api_message("MSG-00002", ['YYYY/MM/DD hh:mm:ss', value])]
                msg = json.dumps(msg_tmp, ensure_ascii=False)
                raise AppException("499-00201", [msg], [msg])

            return int(datetime.datetime.strptime(value, format).timestamp())

        elif collection_item_name == "exastro_events":
            try:
                # ["ObjectId('xxxxxxxxxxxxxxxxxxxxxxxx')"] の場合OK
                if re.match(re.compile(r'''^\["ObjectId\('[a-zA-Z0-9-_]{24}[a-zA-Z0-9-_\[\]"'\(\) ,]*'\)"\]$'''), value):
                    tmp_value_list = json.loads(value)
                # "ObjectId('xxxxxxxxxxxxxxxxxxxxxxxx')" の場合OK
                elif re.match(re.compile(r'''^"ObjectId\('[a-zA-Z0-9-_]{24}[a-zA-Z0-9-_\[\]"'\(\) ,]*'\)"$'''), value):
                    tmp_value = '[{}]'.format(value)
                    tmp_value_list = json.loads(tmp_value)
                # ObjectId('xxxxxxxxxxxxxxxxxxxxxxxx') の場合OK
                elif re.match(re.compile(r'''^ObjectId\('[a-zA-Z0-9-_]{24}[a-zA-Z0-9-_\[\]"'\(\) ,]*'\)$'''), value):
                    value = value.replace(" ", "")
                    value_list = value.split(',')
                    for value in value_list:
                        tmp_value_list.append(value)
                else:
                    value = value.replace(" ", "")
                    value_list = value.split(',')
                    for value in value_list:
                        # xxxxxxxxxxxxxxxxxxxxxxxx の場合OK
                        if re.match(re.compile(r"^[a-zA-Z0-9-_]{24}$"), value):
                            tmp_value = "ObjectId('{}')".format(value)
                            tmp_value_list.append(tmp_value)
                        else:
                            raise Exception
            except Exception:
                msg_tmp = {0: {}}
                # Please search in the format of object ID.
                msg_tmp[0][column_name_dict["11010409"]] = [g.appmsg.get_api_message("499-01825")]
                msg = json.dumps(msg_tmp, ensure_ascii=False)
                raise AppException("499-00201", [msg], [msg])

            return tmp_value_list

        elif collection_item_name in ["labels._exastro_event_collection_settings_id", "labels._exastro_rule_name"]:
            return value

        event_status_dict = event_data_dict['event_status']
        event_name_dict = event_data_dict['event_name']

        if collection_item_name == "labels._exastro_timeout":
            if value in event_status_dict[oaseConst.DF_EVENT_STATUS_TIMEOUT]:  # 時間切れ
                return "1"
            else:
                return "0"

        elif collection_item_name == "labels._exastro_evaluated":
            if value in event_status_dict[oaseConst.DF_EVENT_STATUS_EVALUATED]:  # 判定済み
                return "1"
            else:
                return "0"

        elif collection_item_name == "labels._exastro_undetected":
            if value in event_status_dict[oaseConst.DF_EVENT_STATUS_UNDETECTED]:  # 未知
                return "1"
            else:
                return "0"

        elif collection_item_name == "labels._exastro_type":
            if value == event_name_dict[oaseConst.DF_EVENT_TYPE_CONCLUSION]:  # 結論イベント
                return "conclusion"
            elif value == event_name_dict[oaseConst.DF_EVENT_TYPE_EVENT]:  # イベント
                return "event"

        return tmp_value

    def _create_search_value_list(self, collection_item_name, value, event_data_dict, column_name_dict=None):
        # tmp_value = super()._create_search_value(collection_item_name, value)
        if collection_item_name == "_id":
            try:
                tmp_value = ObjectId(value)
            except Exception:
                msg_tmp = {0: {}}
                # ObjectId: Only exact match search is possible for object ID. (Input value:{})
                msg_tmp[0][column_name_dict["11010401"]] = [g.appmsg.get_api_message("499-01824", [value])]
                msg = json.dumps(msg_tmp, ensure_ascii=False)
                raise AppException("499-00201", [msg], [msg])
            return tmp_value

        elif collection_item_name in ["labels._exastro_fetched_time", "labels._exastro_end_time"]:
            # 日付形式のチェック
            # Noneまたは空文字の場合はエラー
            if value is None or len(value) == 0:
                retBool = False
            # YYYY/MM/DD hh:mm:ssの場合OK
            elif re.match(r'^[0-9]{4}/(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01]) ([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$', value) is not None:
                retBool = True
                format = '%Y/%m/%d %H:%M:%S'
            else:
                retBool = False

            if retBool is False:
                msg_tmp = {0: {}}
                if collection_item_name == "labels._exastro_fetched_time":
                    # Fetched time: The value format (YYYY/MM/DD hh:mm:ss) is invalid.( input value: {} )
                    msg_tmp[0][column_name_dict["11010403"]] = [g.appmsg.get_api_message("MSG-00002", ['YYYY/MM/DD hh:mm:ss', value])]
                else:
                    # End time: The value format (YYYY/MM/DD hh:mm:ss) is invalid.( input value: {} )
                    msg_tmp[0][column_name_dict["11010404"]] = [g.appmsg.get_api_message("MSG-00002", ['YYYY/MM/DD hh:mm:ss', value])]
                msg = json.dumps(msg_tmp, ensure_ascii=False)
                raise AppException("499-00201", [msg], [msg])

            return int(datetime.datetime.strptime(value, format).timestamp())

        elif collection_item_name == "exastro_events":
            try:
                # ["ObjectId('xxxxxxxxxxxxxxxxxxxxxxxx')"] の場合OK
                tmp_value = json.loads(value)
            except Exception:
                msg_tmp = {0: {}}
                # Please search in the format of object ID.
                msg_tmp[0][column_name_dict["11010409"]] = [g.appmsg.get_api_message("499-01825")]
                msg = json.dumps(msg_tmp, ensure_ascii=False)
                raise AppException("499-00201", [msg], [msg])

            return tmp_value

        elif collection_item_name in ["labels._exastro_event_collection_settings_id", "labels._exastro_rule_name"]:
            return value

        elif collection_item_name == "labels._exastro_type":
            event_name_dict = event_data_dict['event_name']
            if value == event_name_dict[oaseConst.DF_EVENT_TYPE_EVENT]:  # イベント
                return "event"
            elif value == event_name_dict[oaseConst.DF_EVENT_TYPE_CONCLUSION]:  # 結論イベント
                return "conclusion"

        return value

    def _create_separated_supported_search_value(self, rest_key_name, type, value, event_data_dict):
        # _exastro_event_statusにLISTが指定された場合$orを使用する必要があるため個別対応とした
        if rest_key_name == "_exastro_event_status" and type == "LIST":
            tmp_list: list = value
            if len(tmp_list) == 1:

                return self.__create_exastro_event_status_search_value(tmp_list[0], event_data_dict)

            elif len(tmp_list) > 1:
                result_list = []
                for item in tmp_list:
                    result_list.append(self.__create_exastro_event_status_search_value(item, event_data_dict))

                return {"$or": result_list}

            else:
                return {}

        if rest_key_name == "labels":
            # labelsのフィルタリングは_format_result_valueで行うため、ここではフィールドへ値の退避のみ行う。
            self.LABELS_PARAMETER = {type: value}
            return {}

        return {rest_key_name: value}

    def __create_exastro_event_status_search_value(self, item, event_data_dict):
        event_status_dict = event_data_dict['event_status']

        if item == event_status_dict[oaseConst.DF_EVENT_STATUS_NEW]:  # 検討中
            return {
                "labels._exastro_timeout": "0",
                "labels._exastro_evaluated": "0",
                "labels._exastro_undetected": "0"
            }

        elif item == event_status_dict[oaseConst.DF_EVENT_STATUS_TIMEOUT]:  # 時間切れ
            return {
                "labels._exastro_timeout": "1",
                "labels._exastro_evaluated": "0",
                "labels._exastro_undetected": "0"
            }

        elif item == event_status_dict[oaseConst.DF_EVENT_STATUS_EVALUATED]:  # 判定済み
            return {
                "labels._exastro_timeout": "0",
                "labels._exastro_evaluated": "1",
                "labels._exastro_undetected": "0"
            }

        elif item == event_status_dict[oaseConst.DF_EVENT_STATUS_UNDETECTED]:  # 未知
            return {
                "labels._exastro_timeout": "0",
                "labels._exastro_evaluated": "0",
                "labels._exastro_undetected": "1"
            }
        else:
            return {
                "labels._exastro_timeout": "2",
                "labels._exastro_evaluated": "2",
                "labels._exastro_undetected": "2"
            }

    def _format_result_value(self, item, event_data_dict):
        format_item = super()._format_result_value(item)

        # # イベント履歴用のイベント状態, イベント種別を取得（言語対応）
        event_status_dict = event_data_dict['event_status']
        event_name_dict = event_data_dict['event_name']

        # イベント状態の判定で使用するマップ。
        # 判定する値は左から_exastro_timeout, _exastro_evaluated, _exastro_undetectedの順に文字列結合する想定。
        event_status_map = {
            "000": event_status_dict[oaseConst.DF_EVENT_STATUS_NEW],  # 検討中
            "001": event_status_dict[oaseConst.DF_EVENT_STATUS_UNDETECTED],  # 未知
            "010": event_status_dict[oaseConst.DF_EVENT_STATUS_EVALUATED],  # 判定済み
            "100": event_status_dict[oaseConst.DF_EVENT_STATUS_TIMEOUT]  # 時間切れ
        }

        # イベント種別の判定で使用するマップ
        event_type_map = {
            "event": event_name_dict[oaseConst.DF_EVENT_TYPE_EVENT],  # イベント
            "conclusion": event_name_dict[oaseConst.DF_EVENT_TYPE_CONCLUSION]  # 結論イベント
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

            # "_exastro_checked"は後から制御用に追加した項目。
            # 画面での取り扱いが決まっていないため、v2.3.0ではlabelsから取り除く対応のみ実施する。
            if "_exastro_checked" in labels:
                labels.pop("_exastro_checked")

            # 残項目はlabelsとして返却するため代入する。
            # 画面返却時、配列やobjectは扱えないため文字列に変更する。
            format_item["labels"] = json.dumps(labels, ensure_ascii=False)

        if "exastro_events" in item:
            exastro_events = list(item["exastro_events"])

            format_item["_exastro_events"] = []
            for item in exastro_events:
                # eventsは再評価イベントを作成するきっかけとなったイベントの_idが格納されている。
                # そのままではJSONとして扱えないため_idと同じように変換する。
                format_item["_exastro_events"].append(str(item))

            # 画面返却時、配列やobjectは扱えないため文字列に変更する。
            format_item["_exastro_events"] = json.dumps(format_item["_exastro_events"], ensure_ascii=False)

        # LABELS_PARAMETERがNoneではない場合、labelsに対する条件が指定されているため確認を行う。
        # labelsの検索の要件をMongoDBの検索時に満たそうとするとサブドキュメントに対してあいまい検索が必要となる。
        # しかし、確認した限りだと文字列型以外にあいまい検索は不可のためpython側での対応とした
        if self.LABELS_PARAMETER is not None:
            tmp_str = str(format_item["labels"])
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
