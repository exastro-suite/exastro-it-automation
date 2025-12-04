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
# oase
from common_libs.oase.const import oaseConst

# 比較方法のキーから、比較方法を取り出すためのマスタ(正規表現の場合は正規表現オプション値がとれるように)
# t_oase_comparison_methodに対応
COMPARISON_OPERATOR = {
    "1": operator.eq,  # ==
    "2": operator.ne,  # ≠
    "3": operator.lt,  # <
    "4": operator.le,  # <=
    "5": operator.gt,  # >
    "6": operator.ge,  # >=
    "7": 0,  # RegularExpression(No Option)
    "8": re.DOTALL,  # RegularExpression(DOTALL)
    "9": re.MULTILINE  # RegularExpression(MULTILINE)
}


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

# 取得してきたイベントの値のタイプに合わせて型を揃える関数を引き出すマスタ
# t_oase_target_typeに対応
TARGET_VALUE_TYPE = {
    "1": str,  # string
    "2": int,  # integer
    "3": float,  # float
    "4": returns_bool,  # bool
    "5": json.loads,  # dict
    "6": json.loads,  # list
    "7": lambda X: X,  # falsey
    "10": lambda X: X  # any
}

# ラベルのキー名をIDから引けるようにしたマスタ
# T_OASE_LABEL_KEY_INPUT
LABEL_KEY_MAP = {}


# イベントにラベルを付与する
def label_event(wsDb, wsMongo, events):  # noqa: C901
    # ラベル付与の設定を取得
    labeling_settings = wsDb.table_select(
        oaseConst.T_OASE_LABELING_SETTINGS,
        "WHERE DISUSE_FLAG=0 ORDER BY LABELING_SETTINGS_NAME ASC"
    )
    if len(labeling_settings) == 0:
        # ラベル付与設定を取得できませんでした。
        msg = g.appmsg.get_log_message("499-01804")
        g.applogger.info(msg)

    # ラベルのマスタを取得
    label_keys = wsDb.table_select(
        oaseConst.V_OASE_LABEL_KEY_GROUP,
        "WHERE DISUSE_FLAG=0"
    )
    if len(label_keys) == 0:
        # ラベルのマスタを取得できませんでした。
        msg = g.appmsg.get_log_message("499-01805")
        g.applogger.info(msg)
    else:
        # ラベルのマスタデータをIDで引けるように整形
        for label_key in label_keys:
            LABEL_KEY_MAP[label_key["LABEL_KEY_ID"]] = label_key

    # ラベル付与されたイベント配列（MongoDBに保存予定）
    labeled_events = []

    # イベント単位でループ
    for event in events:
        # exastro用ラベルを付与
        labeled_event = add_exastro_label(event)
        labeled_events.append(labeled_event)

        # 未知に流すことが決まっているものはラベル付け処理をスキップ
        if labeled_event["labels"]["_exastro_undetected"] == "1":
            continue

        labeled_event["exastro_labeling_settings"] = {}
        labeled_event["exastro_label_key_inputs"] = {}

        # ラベル付与設定に該当するデータにはラベルを追加する
        # パターンの説明
        # パターンA：収集したJSONデータのsearch_key_nameに対応する値とsearch_value_nameをcomparison_methodで比較し、trueの場合、labelのkey: labelのvalueのラベルを追加
        # パターンB：収集したJSONデータのsearch_key_nameに対応する値とsearch_value_nameをcomparison_methodで比較し、trueの場合、labelのkey: targetのvalueのラベルを追加（labelのvalueが空の場合、search_value_nameをlabelのvalueに流用する）# noqa: E501
        # パターンC：すべてのイベントに対してlabelのkey: labelのvalueのラベルを追加
        # パターンD-1：search_key_nameが存在するデータに対してlabelのkey: labelのvalueのラベルを追加
        # パターンD-2：search_key_nameが存在するデータに対してlabel_key: target_keyの持つ値のラベルを追加
        # パターンE：type_idが7であり、search_key_nameに対応する値がFalseの値（空文字、[]、{}、0、False）である際、labelのkey: labelのvalueのラベルを追加
        # パターンF: ラベルの正規表現での置換
        for setting in labeling_settings:
            # 収集した_exastro_event_collection_settings_idとイベント収集設定IDが一致しないものはスキップ
            if labeled_event["labels"]["_exastro_event_collection_settings_id"] != setting["EVENT_COLLECTION_SETTINGS_ID"]:
                continue

            try:
                # ラベル付与内search_key_nameが収集したデータの中の"event"と"labels"のどちらの配下に存在するか確認する
                # ラベル付与設定内にsearch_key_nameが存在しない(パターンC用)
                if setting["SEARCH_KEY_NAME"] is None:
                    # ラベル付与設定内type_id、ラベル付与設定内search_key_nameがともに存在しない場合
                    if setting["TYPE_ID"] is None and setting["SEARCH_VALUE_NAME"] is None:
                        labeled_event = add_label(labeled_event, setting)  # パターンC
                        continue

                elif (setting["SEARCH_KEY_NAME"] in labeled_event["labels"]):
                    labeled_event_location = labeled_event["labels"]
                else:
                    labeled_event_location = labeled_event["event"]

                # "event"もしくは"labels"配下にラベル付与設定のsearch_key_nameが存在するかどうか
                query = create_jmespath_query(setting["SEARCH_KEY_NAME"])
                try:
                    is_key_exists = get_value_from_jsonpath(query, labeled_event_location)
                except Exception:  # noqa: E722
                    is_key_exists = False

                # "event"もしくは"labels"配下にラベル付与設定のsearch_key_nameが存在しない場合
                if is_key_exists is False:
                    # ラベル付与内type_idが7("空判定")、かつラベル付与内comparison_method_idが1（==）の場合
                    if setting["TYPE_ID"] == "7" and setting["COMPARISON_METHOD_ID"] == "1":
                        labeled_event = add_label(labeled_event, setting)  # パターンE
                    continue

                # ラベル付与設定内にsearch_key_nameが存在するか確認 [パターンA,B,D,E用]
                # ラベル付与設定内にtarget_type_id、target_valueのどちらも存在しなく、ラベル付与設定内type_idが7("空判定")以外の場合 [パターンD用]
                if not setting["TYPE_ID"] and not setting["SEARCH_VALUE_NAME"] and not setting["COMPARISON_METHOD_ID"]:
                    if setting["LABEL_VALUE_NAME"]:
                        labeled_event = add_label(labeled_event, setting)  # パターンD-1
                    else:
                        target_value_collection = get_value_from_jsonpath(setting["SEARCH_KEY_NAME"], labeled_event_location)
                        labeled_event = add_label(labeled_event, setting, target_value_collection)  # パターンD-2
                # [パターンA,B,E,F用]
                else:
                    # 取得してきたイベントの"event"もしくは"labels"配下に、ラベル付与設定のsearch_key_nameに該当する値を取得する
                    target_value_collection = get_value_from_jsonpath(setting["SEARCH_KEY_NAME"], labeled_event_location)
                    if setting["TYPE_ID"] == "7":  # 空判定 [パターンE用]
                        if setting["COMPARISON_METHOD_ID"] == "1":  # ==
                            # ラベル付与設定内search_key_nameが収集してきたイベント内"event"か"labels"配下に存在するものの中でvalueが空判定のものが存在するか確認
                            if (target_value_collection in ["", [], {}, 0, False, None]) is True:
                                labeled_event = add_label(labeled_event, setting)  # パターンE(比較方法が'==')
                        elif setting["COMPARISON_METHOD_ID"] == "2":  # ≠
                            # ラベル付与設定内search_key_nameが収集してきたイベント内"event"か"labels"配下に存在するものの中でvalueが空判定のものが存在しないか確認
                            if (target_value_collection in ["", [], {}, 0, False, None]) is False:
                                labeled_event = add_label(labeled_event, setting)  # パターンE(比較方法が'≠')
                    else:
                        # ラベル付与設定内target_valueをラベル付与設定内target_type（値の型）に合わせて変換 [パターンA,B,F用]
                        target_value_setting = TARGET_VALUE_TYPE[setting["TYPE_ID"]](setting["SEARCH_VALUE_NAME"])
                        # 収集してきたJSONデータのvalueとラベル付与設定内search_value_nameをcomparison_method_idを使用して比較
                        compare_result, compare_match = comparison_values(setting["COMPARISON_METHOD_ID"], target_value_collection, target_value_setting)  # noqa: E501
                        if compare_result is True:
                            labeled_event = add_label(labeled_event, setting, compare_match)  # パターンA,B,F
            except Exception as e:
                g.applogger.info(stacktrace())
                g.applogger.info("event={}".format(labeled_event))
                g.applogger.info("label_setting={}".format(setting))
                # ラベル付与に失敗しました
                err_msg = g.appmsg.get_log_message("499-01806", [e])
                g.applogger.info(err_msg)
                continue
    events = []

    return labeled_events

# exastro用ラベルを付与して、OASE標準のイベントの形に整形する
def add_exastro_label(event):
    labeled_event = {}
    labeled_event["event"] = event
    # exastro用ラベルを貼る
    labeled_event["labels"] = {
        "_exastro_event_collection_settings_id": event["_exastro_event_collection_settings_id"],
        "_exastro_fetched_time": event["_exastro_fetched_time"],
        "_exastro_end_time": event["_exastro_end_time"],
        "_exastro_agent_name": event["_exastro_agent_name"],
        "_exastro_agent_version": event["_exastro_agent_version"],
        "_exastro_type": "event",
        "_exastro_checked": "0",
        "_exastro_evaluated": "0",
        "_exastro_undetected": "0",
        "_exastro_timeout": "0",
    }
    labeled_event["exastro_created_at"] = event["_exastro_created_at"]
    # 重複して不要なexastro用ラベルを削除
    del labeled_event["event"]["_exastro_event_collection_settings_id"]
    del labeled_event["event"]["_exastro_event_collection_settings_name"]
    del labeled_event["event"]["_exastro_fetched_time"]
    del labeled_event["event"]["_exastro_end_time"]
    del labeled_event["event"]["_exastro_agent_name"]
    del labeled_event["event"]["_exastro_agent_version"]
    del labeled_event["event"]["_exastro_created_at"]
    # （エージェントで無理矢理、取り込んだ）利用できないイベントのフラグ
    if "_exastro_not_available" in event:
        labeled_event["labels"]["_exastro_not_available"] = event["_exastro_not_available"]
        del labeled_event["event"]["_exastro_not_available"]
        # 利用できないイベントは、あらかじめ未知に流す
        labeled_event["labels"]["_exastro_undetected"] = "1"

    return labeled_event


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

# ドット区切りの文字列で辞書を指定して値を取得
# 1.get_value_from_jsonpath(setting["SEARCH_KEY_NAME"], event_collection_data_location) →　条件に合わせて値を返却
# 2.get_value_from_jsonpath(query, event_collection_data_location) → 条件に合わせて真偽値を返却
def get_value_from_jsonpath(jsonpath, data):
    value = jmespath.search(jsonpath, data)
    return value


def comparison_values(comparison_method_id="1", collect_value=None, compare_value=None):
    """
    収集してきたイベントの(target_keyに対応する)値と、ラベル付与設定のtarget_valueを比較
    compare value of collected event and target value of label settings

    Arguments:
        comparison_method_id: 比較方法
        collect_value: 収集した値
        compare_value: 比較値
    Returns: tupple
        compare_result: 比較結果(該当すればtrue)
        compare_match: 正規表現比較の場合、マッチした結果
    """
    compare_result = False
    compare_match = ""

    try:
        # 正規表現での比較
        if comparison_method_id in ["7", "8", "9"]:
            regex_option = COMPARISON_OPERATOR[comparison_method_id]  # 正規表現オプションを取り出す
            regex_pattern = re.compile(compare_value, regex_option)
            regex_result = regex_pattern.search(collect_value)
            # g.applogger.debug("comparison by regular expression")
            # g.applogger.debug("compare_value={}, regex_option={}".format(compare_value, regex_option))
            # g.applogger.debug("collect_value={}".format(collect_value))
            if regex_result:
                compare_result = True
                # マッチした全体を格納
                compare_match = regex_result.group(0)
        else:
            comparison = COMPARISON_OPERATOR[comparison_method_id]  # 比較メソッドを取り出す
            compare_result = comparison(collect_value, compare_value)
    except Exception as e:
        # 収集した値{collect_value}に対して、比較方法{comparison_method_id}と比較値{compare_value}を実行し、エラーが{e}が発生したので、処理をスキップします。
        err_msg = g.appmsg.get_log_message("499-01807", [collect_value, comparison_method_id, compare_value, e])
        g.applogger.info(err_msg)

    return compare_result, compare_match

# ラベル付与処理
def add_label(event, setting, compare_match=""):
    """
    設定に従ってラベルを付与する

    Arguments:
        event: 収集したイベントデータ
        setting: ラベル付与の設定
        compare_match: 正規表現で検索マッチした値 or 検索キーに対応する値
    Returns:
        event: イベントデータ
    """
    # 比較方法
    comparison_method_id = setting["COMPARISON_METHOD_ID"]
    # ラベルのマスタを引く
    label_key_data = LABEL_KEY_MAP[setting["LABEL_KEY_ID"]]

    label_key_id = label_key_data["LABEL_KEY_ID"]
    label_key_string = label_key_data["LABEL_KEY_NAME"]
    # ラベルの値を決める
    if comparison_method_id in ["7", "8", "9"]:
        # 正規表現での比較および置換
        if setting["LABEL_VALUE_NAME"] is None or not setting["LABEL_VALUE_NAME"]:
            # [パターンB] label_valueが空の場合、matchした文字列をlabel_valueに代入
            label_value = compare_match
        else:
            regex_option = COMPARISON_OPERATOR[comparison_method_id]  # 正規表現オプションを取り出す
            regex_pattern = re.compile(setting["SEARCH_VALUE_NAME"], regex_option)
            label_value = regex_pattern.sub(setting["LABEL_VALUE_NAME"], compare_match)
    else:
        if setting["LABEL_VALUE_NAME"] is None or not setting["LABEL_VALUE_NAME"]:

            if setting["SEARCH_VALUE_NAME"]:
                # [パターンB] label_valueが空の場合、target_valueをlabel_valueに流用する
                label_value = setting["SEARCH_VALUE_NAME"]
            else:
                # [パターンD-2] label_valueが空の場合、target_keyに対応する値をlabel_valueに流用する
                # 型に関わらず、文字列化する
                label_value = str(compare_match)
        else:
            label_value = setting["LABEL_VALUE_NAME"]

    event["labels"][label_key_string] = label_value
    event["exastro_labeling_settings"][label_key_string] = setting["LABELING_SETTINGS_ID"]
    event["exastro_label_key_inputs"][label_key_string] = label_key_id
    return event
