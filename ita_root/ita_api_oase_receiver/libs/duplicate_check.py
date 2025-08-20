# Copyright 2025 NEC Corporation#
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
import json
import datetime
import copy
from bson.objectid import ObjectId
from pymongo import ASCENDING, InsertOne, UpdateOne

# from common_libs.common.exception import AppException
# from common_libs.common.util import stacktrace
from common_libs.common.mongoconnect.const import Const as mongoConst
from common_libs.oase.const import oaseConst
from libs.label_event import LABEL_KEY_MAP


# T_OASE_DEDUPLICATION_SETTINGS
# 重複排除の設定をIDから引けるようにしたもの
DEDUPLICATION_SETTINGS_MAP = {}
# イベント収集設定から、重複排除の設定を引けるようにしたもの
DEDUPLICATION_SETTINGS_ECS_MAP = {}


# 重複排除
def duplicate_check(wsDb, wsMongo, labeled_event_list):  # noqa: C901
    # 重複排除の設定を取得
    deduplication_settings = wsDb.table_select(
        oaseConst.T_OASE_DEDUPLICATION_SETTINGS,
        "WHERE DISUSE_FLAG=0 ORDER BY SETTING_PRIORITY, DEDUPLICATION_SETTING_NAME"
    )
    if len(deduplication_settings) == 0:
        # 重複排除の設定設定を取得できませんでした。
        msg = g.appmsg.get_log_message("499-01804")
        g.applogger.info(msg)
        return

    # IDとイベント収集設定IDから引けるように整形しておく
    for deduplication_setting in deduplication_settings:
        deduplication_setting_id = deduplication_setting["DEDUPLICATION_SETTING_ID"]
        event_source_redundancy_group = json.loads(deduplication_setting["EVENT_SOURCE_REDUNDANCY_GROUP"])
        deduplication_setting["EVENT_SOURCE_REDUNDANCY_GROUP"] = event_source_redundancy_group
        deduplication_setting["CONDITION_LABEL_KEY_IDS"] = json.loads(deduplication_setting.get("CONDITION_LABEL_KEY_IDS", []))
        # リストのものなどを適切な形に整形しておく
        DEDUPLICATION_SETTINGS_MAP[deduplication_setting_id] = deduplication_setting

        for event_collection_settings_id in event_source_redundancy_group:
            if event_collection_settings_id not in DEDUPLICATION_SETTINGS_ECS_MAP:
                DEDUPLICATION_SETTINGS_ECS_MAP[event_collection_settings_id] = []
            if deduplication_setting_id not in DEDUPLICATION_SETTINGS_ECS_MAP[event_collection_settings_id]:
                DEDUPLICATION_SETTINGS_ECS_MAP[event_collection_settings_id].append(deduplication_setting_id)
    # g.applogger.debug("DEDUPLICATION_SETTINGS_MAP={}".format(DEDUPLICATION_SETTINGS_MAP))
    g.applogger.debug("DEDUPLICATION_SETTINGS_ECS_MAP={}".format(DEDUPLICATION_SETTINGS_ECS_MAP))

    # mongoに保存する用に整形している、updateするイベントデータ
    save_update_event_list = []
    # 登録予定の先着イベントのリスト（検索&あとでまとめて登録するためにキャッシュ）
    first_event_list = []
    # 件数
    mongo_update = 0  # 既にmongoに入っている先着イベントと重複している
    request_update = 0  # 同じリクエストの中の先着イベントと重複している

    # イベント単位でループ
    # labeled_event_listは、既にfetched_time->exastro_created_atでソート済みの前提
    for event in labeled_event_list:
        event_collection_settings_id = event["labels"]["_exastro_event_collection_settings_id"]

        # 重複排除設定がなければスキップ
        if event_collection_settings_id not in DEDUPLICATION_SETTINGS_ECS_MAP:
            continue

        # ユーザがつけたラベルのkey&valueを抜き出す
        user_labels = {}
        for label_key_name, label_key_id in event["exastro_label_key_inputs"].items():
            user_labels["labels.{}".format(label_key_name)] = event["labels"][label_key_name]

        # 重複チェックキーの生成
        agent_name = event["labels"]["_exastro_agent_name"]
        dupulicate_check_key = "{}_{}".format(event_collection_settings_id, agent_name)

        # 含まれている重複排除設定でループ
        is_update = False
        for deduplication_settings_id in DEDUPLICATION_SETTINGS_ECS_MAP[event_collection_settings_id]:
            deduplication_setting = DEDUPLICATION_SETTINGS_MAP[deduplication_settings_id]  # 重複排除設定

            # ラベルでの同一性確認の判定条件を生成 = 一致するラベルのkey&valueを作る
            condition_label_key_ids = deduplication_setting["CONDITION_LABEL_KEY_IDS"]
            condition_expression = deduplication_setting["CONDITION_EXPRESSION_ID"]
            tmp_user_labels = copy.deepcopy(user_labels)

            is_skip = False # 重複排除の対象外（判定不能）
            if condition_expression == "1":
            # 設定したラベルが「一致」する場合
                match_label_key_name_list = []   # 一致するラベルの名前のリスト（idのリストから名前のリストを作る）
                for match_label_key_id in condition_label_key_ids:
                    if not match_label_key_id in LABEL_KEY_MAP:
                    # ラベルが廃止or削除されている？
                        is_skip = True
                        break

                    match_label_key_name = "labels.{}".format(LABEL_KEY_MAP[match_label_key_id]["LABEL_KEY_NAME"])
                    if match_label_key_name not in tmp_user_labels:
                    # 一致条件のラベルがついていない場合は、重複排除の対象外
                        is_skip = True
                        break
                    match_label_key_name_list.append(match_label_key_name)

                # 「一致するラベルの名前のリスト」に含まれないものを除外する
                for label_key_name, label_key_id in tmp_user_labels.items():
                    if label_key_name not in match_label_key_name_list:
                        del tmp_user_labels[label_key_name]
            elif condition_expression == "2":
            # 設定したラベルを「無視（不一致を許容）」する場合
                for ignore_label_key_id in condition_label_key_ids:
                    if not ignore_label_key_id in LABEL_KEY_MAP:
                    # ラベルが廃止or削除されている？
                        is_skip = True
                        break

                    ignore_label_key_name = "labels.{}".format(LABEL_KEY_MAP[ignore_label_key_id]["LABEL_KEY_NAME"])
                    if ignore_label_key_name in tmp_user_labels:
                    # 無視対象のラベルがあれば除外
                        del tmp_user_labels[ignore_label_key_name]
            if is_skip is True:
                break

            # 検索条件を作成し、mongoから検索
            event_source_redundancy_group = deduplication_setting["EVENT_SOURCE_REDUNDANCY_GROUP"]
            conditions = {
                "labels._exastro_end_time": {"$gte": int(datetime.datetime.now().timestamp())},  # 現在時刻より未来（TTL範囲内）
                "labels._exastro_event_collection_settings_id": {"$in": event_source_redundancy_group},  # 重複排除設定のイベント収集範囲
                "exastro_dupulicate_check": {"$nin": [dupulicate_check_key]}  # これから重複する以外のケース（先着イベントor先着イベントに刻まれている）を省くため
            }
            conditions.update(tmp_user_labels)  # ラベルのkey&valueの一致

            g.applogger.debug("conditions={}".format(conditions))
            mongo_results = wsMongo.collection(mongoConst.LABELED_EVENT_COLLECTION).find(conditions).sort([("labels._exastro_fetched_time", ASCENDING), ("exastro_created_at", ASCENDING), ("_id", ASCENDING)]).limit(1)

            for mongo_result in mongo_results:
                # 既に先着イベントがあるので、重複イベントが来た履歴を先着イベントに残して、イベントの新規登録はしない（=重複排除）
                dupulicate_check_list = list(mongo_result["exastro_dupulicate_check"]) + [dupulicate_check_key]
                # 先着イベントを更新
                save_update_event_list.append(UpdateOne(
                    {"_id": ObjectId(mongo_result["_id"])},
                    {"$set" :{"exastro_dupulicate_check": dupulicate_check_list}}
                ))
                mongo_update += 1
                g.applogger.debug("first event(_id={}) is to be updated".format(mongo_result["_id"]))
                is_update = True
                break
            # 更新（重複排除）が行われた場合は、（該当イベントに関する）処理終了
            if is_update is True:
                break

            # save_update_event_listに先着イベントがないか探す
            for first_event in first_event_list:
                if first_event["labels"]["_exastro_event_collection_settings_id"] not in event_source_redundancy_group:  # 重複排除設定のイベント収集範囲
                    break
                if dupulicate_check_key in first_event["exastro_dupulicate_check"]:  # これから重複する以外のケース（先着イベントor先着イベントに刻まれている）を省くため
                    break
                match_label = True  # ラベルのkey&valueの一致
                for _key, value in tmp_user_labels.items():
                    key = _key.replace("labels.", "")
                    if first_event["labels"][key] != value:
                        match_label = False
                        break
                if match_label is False:
                    break
                # ソート済のリストを検索しているので、先着イベントがみつかった時点で抜けて重複イベント対象とみなす
                # 先着イベントを更新
                first_event["exastro_dupulicate_check"].append(dupulicate_check_key)
                request_update += 1
                g.applogger.debug("first event(dupulicate_check_key={}, exastro_created_at={}, exastro_dupulicate_check={}) is to be updated".format(dupulicate_check_key, first_event["exastro_created_at"], first_event["exastro_dupulicate_check"]))
                is_update = True
                break
            # 更新（重複排除）が行われた場合は、（該当イベントに関する）処理終了
            if is_update is True:
                break

        # いずれの場合でも重複排除が行われなかった場合に、「新規登録」と判断 ※先着イベント or 重複排除判定をする必要がないイベントを指す
        if is_update is False:
            g.applogger.debug("first event(dupulicate_check_key={}, exastro_created_at={}) is to be inserted".format(dupulicate_check_key, event["exastro_created_at"]))
            first_event_list.append(event)

    # 登録するイベントのリストをmongoに保存するために整形
    save_insert_event_list = [InsertOne(x) for x in first_event_list]

    g.applogger.info("duplicate check result is below: all={}, insert={}, mongo_update={}, request_update={}".format(len(labeled_event_list), len(first_event_list), mongo_update, request_update))

    return save_insert_event_list + save_update_event_list
