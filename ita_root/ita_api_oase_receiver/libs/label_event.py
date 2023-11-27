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
import operator
import re
import jmespath
import json
from common_libs.common.util import stacktrace

# イベントにラベルを付与し、MongDBに保存する
def label_event(wsDb, wsMongo, events):  # noqa: C901
    # 返却値
    err_code = ""

    # ラベル付与設定内target_valueを取得してきたイベントのタイプに合わせて比較するためのマスタ
    target_value_type = {
        "1": str,  # string
        "2": int,  # integer
        "3": float,  # float
        "4": returns_bool,  # bool
        "5": json.loads,  # dict
        "6": json.loads,  # list
        "7": lambda X: X,  # falsey
        "10": lambda X: X  # any
    }

    # ラベル付与の設定を取得
    labeling_settings = wsDb.table_select(
        "T_OASE_LABELING_SETTINGS",
        "WHERE DISUSE_FLAG=0"
    )
    if len(labeling_settings) == 0:
        # ラベル付与設定を取得できませんでした。
        err_code = "499-01804"
        return err_code

    # ラベルのマスタを取得
    label_keys = wsDb.table_select(
        "T_OASE_LABEL_KEY_INPUT",
        "WHERE DISUSE_FLAG=0"
    )
    if len(label_keys) == 0:
        # ラベルのマスタを取得できませんでした。
        err_code = "499-01805"
        return err_code
    # ラベルのマスタデータをIDで引けるように整形
    label_key_map = {}
    for label_key in label_keys:
        label_key_map[label_key["LABEL_KEY_ID"]] = label_key

    # そのままのイベントデータを保存するためのコレクション
    event_collection = wsMongo.collection("event_collection")
    # MongoDBに保存
    event_collection.insert_many(events)

    # ラベル付与したイベントデータを保存するためのコレクション
    labeled_event_collection = wsMongo.collection("labeled_event_collection")
    # ラベル付与されたイベント配列（MongoDBに保存予定）
    labeled_events = []

    # 収集してきたJSONデータをイベント単位でループ（exastro用ラベルのみ付与する）
    for single_event in events:
        labeled_event = {}
        original_event = single_event
        labeled_event["event"] = original_event

        # exastro用ラベルを貼る
        exastro_labels = {
            "_exastro_event_collection_settings_id": single_event["_exastro_event_collection_settings_id"],
            "_exastro_fetched_time": single_event["_exastro_fetched_time"],
            "_exastro_end_time": single_event["_exastro_end_time"],
            "_exastro_type": "event",
            "_exastro_evaluated": "0",
            "_exastro_undetected": "0",
            "_exastro_timeout": "0"
        }
        # 重複して不要なexastro用ラベルを削除
        labeled_event["labels"] = exastro_labels
        del labeled_event["event"]["_exastro_event_collection_settings_id"]
        del labeled_event["event"]["_exastro_fetched_time"]
        del labeled_event["event"]["_exastro_end_time"]
        labeled_events.append(labeled_event)

    # exastro用ラベルを貼った後のデータをイベント単位でループ
    for event_collection_data in labeled_events:
        event_collection_data["exastro_labeling_settings"] = {}
        event_collection_data["exastro_label_key_inputs"] = {}

        # ラベル付与設定に該当するデータにはラベルを追加する
        # パターンの説明
        # パターンA：収集したJSONデータのsearch_key_nameに対応する値とsearch_value_nameをcomparison_methodで比較し、trueの場合、labelのkey: labelのvalueのラベルを追加
        # パターンB：収集したJSONデータのsearch_key_nameに対応する値とsearch_value_nameをcomparison_methodで比較し、trueの場合、labelのkey: targetのvalueのラベルを追加（labelのvalueが空の場合、search_value_nameをlabelのvalueに流用する）# noqa: E501
        # パターンC：すべてのイベントに対してlabelのkey: labelのvalueのラベルを追加
        # パターンD：search_key_nameが存在するデータに対してlabelのkey: labelのvalueのラベルを追加
        # パターンE：type_idが7であり、search_key_nameに対応する値がFalseの値（空文字、[]、{}、0、False）である際、labelのkey: labelのvalueのラベルを追加
        for setting in labeling_settings:
            try:
                # 収集した_exastro_event_collection_settings_idとイベント収集設定IDが一致しないものはスキップ
                if event_collection_data["labels"]["_exastro_event_collection_settings_id"] != setting["EVENT_COLLECTION_SETTINGS_ID"]:
                    continue

                # ラベル付与内search_key_nameが収集したデータの中の"event"と"labels"のどちらの配下に存在するか確認する
                # ラベル付与設定内にsearch_key_nameが存在しない(パターンC用)
                if setting["SEARCH_KEY_NAME"] is None:
                    # ラベル付与設定内type_id、ラベル付与設定内search_key_nameがともに存在しない場合
                    if setting["TYPE_ID"] is None and setting["SEARCH_VALUE_NAME"] is None:
                        event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンC
                        continue

                elif (setting["SEARCH_KEY_NAME"] in event_collection_data["labels"]):
                    event_collection_data_location = event_collection_data["labels"]
                else:
                    event_collection_data_location = event_collection_data["event"]

                # "event"もしくは"labels"配下にラベル付与設定のsearch_key_nameが存在するかどうか
                query = create_jmespath_query(setting["SEARCH_KEY_NAME"])
                try:
                    is_key_exists = get_value_from_jsonpath(query, event_collection_data_location)
                except:  # noqa: E722
                    is_key_exists = False
                # "event"もしくは"labels"配下にラベル付与設定のsearch_key_nameが存在しない場合
                if is_key_exists is False:
                    # ラベル付与内type_idが7("空判定")、かつラベル付与内comparison_method_idが1（==）の場合
                    if setting["TYPE_ID"] == "7" and setting["COMPARISON_METHOD_ID"] == "1":
                        event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンE
                    continue

                # ラベル付与設定内にsearch_key_nameが存在するか確認 [パターンA,B,D,E用]
                # ラベル付与設定内にtarget_type_id、target_valueのどちらも存在しなく、ラベル付与設定内type_idが7("空関数")以外の場合 [パターンD用]
                if ((setting["TYPE_ID"] and setting["SEARCH_VALUE_NAME"]) is None) and setting["TYPE_ID"] != "7":
                    event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンD
                # [パターンA,B,E用]
                else:
                    # label_valueが空の場合、target_valueをlabel_valueに流用する [パターンB,E用]
                    if setting["LABEL_VALUE_NAME"] is None:
                        setting["LABEL_VALUE_NAME"] = setting["SEARCH_VALUE_NAME"]
                    # 取得してきたイベントの"event"もしくは"labels"配下に、ラベル付与設定のsearch_key_nameに該当する値を取得する
                    target_value_collection = get_value_from_jsonpath(setting["SEARCH_KEY_NAME"], event_collection_data_location)
                    if setting["TYPE_ID"] == "7":  # 空判定 [パターンE用]
                        if setting["COMPARISON_METHOD_ID"] == "1":  # ==
                            # ラベル付与設定内search_key_nameが収集してきたイベント内"event"か"labels"配下に存在するものの中でvalueが空判定のものが存在するか確認
                            if (target_value_collection in ["", [], {}, 0, False, None]) is True:
                                event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンE(比較方法が'==')
                        elif setting["COMPARISON_METHOD_ID"] == "2":  # ≠
                            # ラベル付与設定内search_key_nameが収集してきたイベント内"event"か"labels"配下に存在するものの中でvalueが空判定のものが存在しないか確認
                            if (target_value_collection in ["", [], {}, 0, False, None]) is False:
                                event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンE(比較方法が'≠')
                    else:
                        # ラベル付与設定内target_valueをラベル付与設定内target_typeに合わせて変換 [パターンA,B用]
                        target_value_setting = target_value_type[setting["TYPE_ID"]](setting["SEARCH_VALUE_NAME"])
                        # 収集してきたJSONデータのvalueとラベル付与設定内search_value_nameをcomparison_method_idを使用して比較
                        if comparison_values(setting["COMPARISON_METHOD_ID"], target_value_collection, target_value_setting) is True:
                            event_collection_data = add_label(label_key_map, event_collection_data, setting)  # パターンA,B
            except Exception as e:
                # ラベル付与に失敗しました
                err_code = "499-01806"
                g.applogger.error("event=".format(event_collection_data))
                g.applogger.error("label_setting=".format(setting))
                g.applogger.error(stacktrace())
                g.applogger.error(e)
                return err_code

    # ラベル付与したデータをMongoDBに保存
    try:
        labeled_event_collection.insert_many(labeled_events)
    except Exception as e:
        g.applogger.error(stacktrace())
        g.applogger.error(e)
        err_code = "499-01803"
        return err_code

    return err_code


# json構造を検索するためのクエリを生成
def create_jmespath_query(json_path):
    # .に合わせて分割
    key_list = json_path.split(".")
    query = "contains(keys({}), '{}')"
    # key_listの中身が1階層の場合
    if len(key_list) == 1:
        return query.format("@", key_list[0])

    # 要素を連結する
    parent_key = ".".join(key_list[:-1])
    key_to_find = key_list[-1]
    return query.format(parent_key, key_to_find)


# ラベル付与設定内で比較方法として真偽値を使用した場合に、値をpythonで解釈できるようにする
# _value: ラベル付与設定内でのsearch_value_name
def returns_bool(_value):
    value = _value.lower()
    if value == "true":
        return True
    elif value == "false":
        return False
    else:
        return None


def comparison_values(comparison_method_id="1", comparative=None, referent=None):
    """
    収集してきたイベントの(target_keyに対応する)値と、ラベル付与設定のtarget_valueを比較
    compare value of collected event and target value of label settings

    Arguments:
        comparison_method_id: 比較方法
        comparative: 収集した値
        referent: 比較値(target_value)
    Returns:
        boolean: 比較結果(該当すればtrue)
    """
    result = False

    comparison_operator = {
        "1": operator.eq,  # ==
        "2": operator.ne,  # ≠
        "3": operator.lt,  # <
        "4": operator.le,  # <=
        "5": operator.gt,  # >
        "6": operator.ge,  # >=
        "7": "Regular expression"
    }

    # 上記comparison_operatorをリストとして取得
    key_list = list(comparison_operator.keys())

    # リストの中にcomparison_method_idが存在するか確認
    if comparison_method_id in key_list:
        try:
            # 正規表現処理
            if comparison_method_id == "7":
                regex_pattern = re.compile(referent)
                result = regex_pattern.search(comparative)
                if result:
                    result = True
            else:
                comparison = comparison_operator[comparison_method_id]
                result = comparison(comparative, referent)
        except Exception as e:
            # 収集した値{comparative}に対して、比較方法{comparison_method_id}と比較値{referent}を実行し、エラーが{e}が発生したので、処理をスキップします。
            err_msg = g.appmsg.get_log_message("499-01807", [comparative, comparison_method_id, referent, e])
            g.applogger.info(err_msg)

    return result


# ドット区切りの文字列で辞書を指定して値を取得
# 1.get_value_from_jsonpath(setting["SEARCH_KEY_NAME"], event_collection_data_location) →　条件に合わせて値を返却
# 2.get_value_from_jsonpath(query, event_collection_data_location) → 条件に合わせて真偽値を返却
def get_value_from_jsonpath(jsonpath, data):
    value = jmespath.search(jsonpath, data)
    return value


# ラベル付与処理
def add_label(label_key_map, event_collection_data, setting):
    # ラベルのマスタを引く
    label_key_data = label_key_map[setting["LABEL_KEY_ID"]]

    label_key_id = label_key_data["LABEL_KEY_ID"]
    label_key_string = label_key_data["LABEL_KEY_NAME"]

    event_collection_data["labels"][label_key_string] = setting["LABEL_VALUE_NAME"]
    event_collection_data["exastro_labeling_settings"][label_key_string] = setting["LABELING_SETTINGS_ID"]
    event_collection_data["exastro_label_key_inputs"][label_key_string] = label_key_id
    return event_collection_data
