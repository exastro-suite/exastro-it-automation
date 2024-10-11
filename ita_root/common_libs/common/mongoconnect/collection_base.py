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

import json

from flask import g
from common_libs.common.exception import AppException
from .const import Const


class CollectionBase():
    """
    Collection

        MongoDBのコレクションに対する以下の操作を統一するための抽象クラス\n
        ・検索条件組み立て\n
        ・返却値整形

    """

    # RANGEによる検索を許可するMongoDBの項目名を保持するリスト
    RANGE_LIST = []

    def create_where(self, parameter: dict, objdbca) -> dict:
        """
        コレクションの検索条件を作成する。
        Arguments:
            parameter (dict): リクエストBody

        Raises:
            NotImplementedError:

        Returns:
            dict:MongoDBの検索で使用可能な状態のDict
        """

        event_status_dict = {}
        event_name_dict = {}
        event_data_dict = {}
        event_status_list_search = []
        event_name_list_search = []
        column_name_dict = {}
        result_list = []

        # イベント履歴用のイベント状態, イベント種別, カラム名を取得（言語対応）
        lang = g.LANGUAGE
        if lang == "ja":
            event_status_name_lang = "EVENT_STATUS_NAME" + "_JA"
            event_name_lang = "EVENT_NAME" + "_JA"
            column_name_lang = "COLUMN_NAME" + "_JA"
        else:
            event_status_name_lang = "EVENT_STATUS_NAME" + "_EN"
            event_name_lang = "EVENT_NAME" + "_EN"
            column_name_lang = "COLUMN_NAME" + "_EN"

        event_status_list = objdbca.table_select("T_OASE_EVENT_STATUS", "WHERE DISUSE_FLAG = %s", [0])
        for event_status in event_status_list:
            event_status_dict[event_status["EVENT_STATUS_ID"]] = event_status[event_status_name_lang]
            event_status_list_search.append(event_status[event_status_name_lang])

        event_name_list = objdbca.table_select("T_OASE_EVENT", "WHERE DISUSE_FLAG = %s", [0])
        for event_name in event_name_list:
            event_name_dict[event_name["EVENT_ID"]] = event_name[event_name_lang]
            event_name_list_search.append(event_name[event_name_lang])

        event_data_dict["event_status"] = event_status_dict
        event_data_dict["event_name"] = event_name_dict

        # 検索の際のバリデーション用に言語設定に合わせてカラム名を取得
        # 11010401: オブジェクトID, 11010403: イベント収集日時, 11010404: イベント有効日時, 11010409: 利用イベント
        column_name_list = objdbca.table_select("T_COMN_MENU_COLUMN_LINK", "WHERE COLUMN_DEFINITION_ID IN ('{}', '{}', '{}', '{}') AND `DISUSE_FLAG` = {}".format("11010401", "11010403", "11010404", "11010409", 0))  # noqa: E501
        for column_name in column_name_list:
            column_name_dict[column_name['COLUMN_DEFINITION_ID']] = column_name[column_name_lang]

        result = {}
        for rest_key_name, setting in parameter.items():
            for type, value in setting.items():

                # 特殊な流れで処理が必要な場合の分岐
                if self._is_separated_supported_item(rest_key_name, type):
                    result.update(self._create_separated_supported_search_value(rest_key_name, type, value, event_data_dict))

                else:
                    # 通常の流れで処理できる場合の分岐
                    collection_item_name = self._convert_parameter_item_name_to_collection_item_name(rest_key_name, value)

                    # 1つの条件で複数のカラムに条件指定が必要な場合を考慮してループで処理する。
                    for item_name in collection_item_name:
                        event_status_exectute_flag = False
                        if type == "NORMAL":
                            if rest_key_name == "_exastro_event_status":
                                for event_status in event_status_list_search:
                                    if event_status_exectute_flag:
                                        continue
                                    if value in event_status:
                                        result[item_name] = self._create_search_value(item_name, value, event_data_dict)
                                        event_status_exectute_flag = True
                            elif rest_key_name == "_exastro_type":
                                for event_name in event_name_list_search:
                                    if value in event_name:
                                        value = event_name
                                        result_tmp = self._create_search_value(item_name, value, event_data_dict)
                                        result_list.append(result_tmp)
                                    result[item_name] = {"$in": result_list}
                            elif rest_key_name == "_id":
                                result[item_name] = self._create_search_value(item_name, value, event_data_dict, column_name_dict)
                            elif rest_key_name == "_exastro_events":
                                tmp_list = self._create_search_value(item_name, value, event_data_dict, column_name_dict)
                                for tmp in tmp_list:
                                    result = {item_name: {"$in": [tmp]}}
                                    result_list.append(result)
                                result = {"$and": result_list}
                            else:
                                tmp_list = self._create_search_value(item_name, value, event_data_dict)
                                result[item_name] = {"$regex": tmp_list}

                        elif type == "LIST":
                            tmp_list = []
                            for item in value:
                                tmp_list.append(self._create_search_value_list(item_name, item, event_data_dict, column_name_dict))

                                result[item_name] = {"$in": tmp_list}

                        elif type == "RANGE":
                            # RANGEに対応していない項目の場合例外として処理する。
                            if not self.is_supported_range(rest_key_name):
                                status_code = '499-00101'
                                log_msg_args = [rest_key_name]
                                api_msg_args = [rest_key_name]
                                raise AppException(status_code, log_msg_args, api_msg_args)

                            # RANGEの場合開始（START）終了（END）を指定するため、対応した比較演算子を定義する。
                            kind_map = {
                                "START": "$gte",
                                "END": "$lte"
                            }

                            tmp_dict = {}
                            for kind, item in dict(value).items():
                                tmp_dict[kind_map[kind]] = self._create_search_value(item_name, item, event_data_dict, column_name_dict)
                            result[item_name] = tmp_dict

                # イベント状態カラムかイベント種別カラムが検索条件にヒットしない場合はダミーの値を渡す
                if (rest_key_name == "_exastro_event_status" or rest_key_name == "_exastro_type") and result == {}:
                    result = json.loads('{"labels._exastro_timeout": "2", "labels._exastro_evaluated": "2", "labels._exastro_undetected": "2"}')

        return result

    def _convert_parameter_item_name_to_collection_item_name(self, rest_key_name, value):
        """
        パラメータのKEYをMongoDBの項目名に変換する
        特殊な変換が必要な場合はオーバーライドすること。
        Args:
            rest_key_name: パラメータに対応するmongoDBの項目名
        """

        return [rest_key_name]

    # def _create_search_value(self, collection_item_name, value):
    #     """
    #     受け取った値をMongoDBで検索する際に適した値に変換する。
    #     共通的に処理できるのは_idのみ。
    #     クラス独自の変換処理を実装する場合はオーバーライドすること。
    #     Args:
    #         rest_key_name: RESTAPIで返却する際のKEY
    #         value: パラメータから受け取った値

    #     Returns:
    #         変換が必要な場合は変換後の値。変換が不要な場合は引数valueの値をそのまま返却する。
    #     """

    #     if collection_item_name == "_id":
    #         return ObjectId(value)

    #     return value

    def _is_separated_supported_item(self, rest_key_name, type):
        """
        個別対応が必要な項目かどうかを確認する
        確認はリクエストパラメータの名前とパラメータのタイプの組み合わせで行う。
        必要に応じてオーバーライドしてTrueを返却するパターンを実装すること。
        また項目を追加する場合は「_create_separated_supported_search_value」に同様の判定を追加すること

        Args:
            rest_key_name: パラメータ名
            type: パラメータのタイプ（NORMAL, LIST, RANGE）

        Returns:
            _type_: _description_
        """
        return False

    def _create_separated_supported_search_value(self, rest_key_name, type, value):
        """
        個別に処理が必要な検索値生成処理を定義するためのメソッド
        必要に応じてオーバーライドして各検索値を生成する処理を実装すること。
        また項目を追加する場合は「_create_separated_supported_search_value」に同様の判定を追加すること
        Args:
            rest_key_name: パラメータ名
            type: パラメータのタイプ（NORMAL, LIST, RANGE）
            value: パラメータの値
        """

        return {rest_key_name: value}

    def is_supported_range(self, rest_key_name):
        """
        引数で指定された項目がRANGEの検索に対応しているかチェックする
        Args:
            rest_key_name: リクエストパラメータ名
        """

        return rest_key_name in self.RANGE_LIST

    def create_result(self, result: list[dict], objdbca) -> dict:
        """
        MongoDBから取得したデータを返却するために整形する。
        実際の値の整形は__format_result_valueで行い、ここでは流れのみを定義する。

        Args:
            parameter (dict): _description_

        Returns:
            dict: _description_
        """

        format_result = []
        event_status_dict = {}
        event_name_dict = {}
        event_data_dict = {}

        # イベント履歴用のイベント状態, イベント種別を取得（言語対応）
        lang = g.LANGUAGE
        if lang == "ja":
            event_status_name_lang = "EVENT_STATUS_NAME" + "_JA"
            event_name_lang = "EVENT_NAME" + "_JA"
        else:
            event_status_name_lang = "EVENT_STATUS_NAME" + "_EN"
            event_name_lang = "EVENT_NAME" + "_EN"

        event_status_list = objdbca.table_select("T_OASE_EVENT_STATUS", "WHERE DISUSE_FLAG = %s", [0])
        for event_status in event_status_list:
            event_status_dict[event_status["EVENT_STATUS_ID"]] = event_status[event_status_name_lang]

        event_name_list = objdbca.table_select("T_OASE_EVENT", "WHERE DISUSE_FLAG = %s", [0])
        for event_name in event_name_list:
            event_name_dict[event_name["EVENT_ID"]] = event_name[event_name_lang]

        event_data_dict["event_status"] = event_status_dict
        event_data_dict["event_name"] = event_name_dict

        for item in result:
            tmp = self._format_result_value(item, event_data_dict)
            if tmp is not None:
                format_result.append(
                    {
                        "file": {},
                        "parameter": tmp
                    }
                )

        return format_result

    def _format_result_value(self, item):
        """
        受け取った値を画面で表示する際に適した値に変換する。
        共通的に処理できるのは_idのみ。
        クラス独自の変換処理を実装する場合はオーバーライドすること。
        Args:
            rest_key_name: RESTAPIで返却する際のKEY
            value: パラメータから受け取った値

        Returns:
            変換が必要な場合は変換後の値。変換が不要な場合は引数valueの値をそのまま返却する。
        """

        # オブジェクトの構造も変わるため、受け入れ用のオブジェクトを別途定義
        format_item = {}

        # _idについてはstrに変換（ObjectId()が無くなる）で問題ないことを確認済み。
        format_item["_id"] = str(item["_id"])

        return format_item

    def create_sort_key(self, sort_key: str) -> list[tuple]:
        """
        ソートキーを生成する
        コレクションを問わずこのまま使用できる想定。
        扱う値はメニュー管理のSORT_KEYの値に依存する。
        MariaDBのテーブルに対して設定する内容と同じ内容を設定してもらえば問題なく処理できるようになっている。
        Arguments:
            sort_key (str): loadTable.get_sort_key()で取得した値

        Returns:
            list[tuple]: 検索条件を設定したタプル（カラム名、ソート順）を格納したリスト
        """
        result = []
        sort_key_json: list[dict] = json.loads(sort_key)
        for item in sort_key_json:
            for key, value in item.items():
                if key == 'ASC':
                    result.append((value, Const.ASCENDING))
                elif key == 'DESC':
                    result.append((value, Const.DESCENDING))

        return result
