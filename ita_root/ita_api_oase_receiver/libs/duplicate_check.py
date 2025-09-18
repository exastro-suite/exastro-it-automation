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
import os
import json
import datetime
import copy
from pymongo import ASCENDING, InsertOne
import concurrent.futures
from collections import defaultdict
import queue

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
        "WHERE DISUSE_FLAG='0' ORDER BY SETTING_PRIORITY, DEDUPLICATION_SETTING_NAME"
    )
    if len(deduplication_settings) == 0:
        # 重複排除の設定設定を取得できませんでした。
        msg = g.appmsg.get_log_message("重複排除の設定設定を取得できませんでした。")
        g.applogger.info(msg)
        return False

    labeled_event_collection = wsMongo.collection(mongoConst.LABELED_EVENT_COLLECTION)  # ラベル付与したイベントデータを保存するためのコレクション

    # IDとイベント収集設定IDから引けるように整形しておく
    for deduplication_setting in deduplication_settings:
        deduplication_setting_id = deduplication_setting["DEDUPLICATION_SETTING_ID"]

        # multi_select_id_columnのものをすぐに配列として利用できるように整形
        try:
            event_source_redundancy_group = json.loads(deduplication_setting["EVENT_SOURCE_REDUNDANCY_GROUP"])['id']
        except Exception:
            event_source_redundancy_group = []
        deduplication_setting["EVENT_SOURCE_REDUNDANCY_GROUP"] = event_source_redundancy_group
        try:
            deduplication_setting["CONDITION_LABEL_KEY_IDS"] = json.loads(deduplication_setting["CONDITION_LABEL_KEY_IDS"])['id']
        except Exception:
            deduplication_setting["CONDITION_LABEL_KEY_IDS"] = []

        DEDUPLICATION_SETTINGS_MAP[deduplication_setting_id] = deduplication_setting

        for event_collection_settings_id in event_source_redundancy_group:
            if event_collection_settings_id not in DEDUPLICATION_SETTINGS_ECS_MAP:
                DEDUPLICATION_SETTINGS_ECS_MAP[event_collection_settings_id] = []
            if deduplication_setting_id not in DEDUPLICATION_SETTINGS_ECS_MAP[event_collection_settings_id]:
                DEDUPLICATION_SETTINGS_ECS_MAP[event_collection_settings_id].append(deduplication_setting_id)
    # g.applogger.debug("DEDUPLICATION_SETTINGS_MAP={}".format(DEDUPLICATION_SETTINGS_MAP))
    g.applogger.debug(f"{DEDUPLICATION_SETTINGS_ECS_MAP=}")

    # mongoにbulkで発行できるものはここにためておく
    bulkwrite_event_list = []
    # key: dupulicate_check_key, value: list of event data (find_one_updateを実行するためのデータ)
    findoneupdate_event_group = defaultdict(list)

    # イベント単位でループ
    # labeled_event_listは、既にfetched_time->exastro_created_atでソート済みの前提
    for event in labeled_event_list:
        event_collection_settings_id = event["labels"]["_exastro_event_collection_settings_id"]
        agent_name = event["labels"]["_exastro_agent_name"]
        # 重複チェックキーの生成
        dupulicate_check_key = "{}_{}".format(event_collection_settings_id, agent_name)

        # 重複排除設定がなければ、追加決定
        if event_collection_settings_id not in DEDUPLICATION_SETTINGS_ECS_MAP:
            event["exastro_dupulicate_check"] = [dupulicate_check_key]
            bulkwrite_event_list.append(InsertOne(event))
            continue

        # ここから重複排除の判定に入っていく
        # ユーザがつけたラベルのkey&valueを抜き出す
        user_labels = {}
        for label_key_name, label_key_id in event["exastro_label_key_inputs"].items():
            user_labels["labels.{}".format(label_key_name)] = event["labels"][label_key_name]

        # 含まれている重複排除設定でループ
        conditions_list = []
        for deduplication_settings_id in DEDUPLICATION_SETTINGS_ECS_MAP[event_collection_settings_id]:
            deduplication_setting = DEDUPLICATION_SETTINGS_MAP[deduplication_settings_id]  # 重複排除設定
            event_source_redundancy_group = deduplication_setting["EVENT_SOURCE_REDUNDANCY_GROUP"]
            if len(event_source_redundancy_group) == 0:
                break

            # ラベルでの同一性確認の判定条件を生成 = 一致するラベルのkey&valueを作る
            condition_label_key_ids = deduplication_setting["CONDITION_LABEL_KEY_IDS"]
            condition_expression = deduplication_setting["CONDITION_EXPRESSION_ID"]
            tmp_user_labels = copy.deepcopy(user_labels)

            is_skip = False  # 重複排除の対象外（判定不能）
            if condition_expression == "1":
                # 設定したラベルが「一致」する場合
                match_label_key_name_list = []   # 一致するラベルの名前のリスト（idのリストから名前のリストを作る）
                for match_label_key_id in condition_label_key_ids:
                    if match_label_key_id not in LABEL_KEY_MAP:
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
                for label_key_name, label_key_id in user_labels.items():
                    if label_key_name not in match_label_key_name_list:
                        del tmp_user_labels[label_key_name]
            elif condition_expression == "2":
                # 設定したラベルを「無視（不一致を許容）」する場合
                for ignore_label_key_id in condition_label_key_ids:
                    if ignore_label_key_id not in LABEL_KEY_MAP:
                        # ラベルが廃止or削除されている？
                        is_skip = True
                        break

                    ignore_label_key_name = "labels.{}".format(LABEL_KEY_MAP[ignore_label_key_id]["LABEL_KEY_NAME"])
                    if ignore_label_key_name in tmp_user_labels:
                        # 無視対象のラベルがあれば除外
                        del tmp_user_labels[ignore_label_key_name]
            if is_skip is True:
                continue

            # 検索条件を作成
            conditions = {
                "labels._exastro_end_time": {"$gte": int(datetime.datetime.now().timestamp())},  # 現在時刻より未来（TTL範囲内）
                "labels._exastro_event_collection_settings_id": {"$in": event_source_redundancy_group},  # 重複排除設定のイベント収集範囲
                "exastro_dupulicate_check": {"$nin": [dupulicate_check_key]}  # これから重複する以外のケース（先着イベントor先着イベントに刻まれている）を省くため
            }
            if tmp_user_labels:
                conditions.update(tmp_user_labels)  # ラベルのkey&valueの一致
            # g.applogger.debug(f"{conditions=}")

            # 検索条件を追加（重複排除ごとに検索するのではなく、まとめる）
            conditions_list.append((deduplication_settings_id, conditions))

        # g.applogger.debug(f"{conditions_list=}")
        if len(conditions_list) == 0:
            # insertしかありえない
            event["exastro_dupulicate_check"] = [dupulicate_check_key]
            bulkwrite_event_list.append(InsertOne(event))
            continue

        # upsertする場合は、その場でmongoにクエリを発行する（find_one_and_updateがbulk_writeできないから）
        # タスクをdupulicate_check_keyごとにまとめる
        findoneupdate_event_group[dupulicate_check_key].append({
            "event": event,
            "conditions_list": conditions_list,
            "dupulicate_check_key": dupulicate_check_key
        })

    labeled_event_list = None

    if len(bulkwrite_event_list) != 0:
        labeled_event_collection.bulk_write(bulkwrite_event_list)
        g.applogger.info("bulk_write_num={}".format(len(bulkwrite_event_list)))
        bulkwrite_event_list = None

    q_findoneupdate_num = queue.Queue()
    if findoneupdate_event_group:
        # スレッド数。I/Oバウンドな処理なので、CPUコア数より多めに設定するのが一般的
        MAX_WORKERS = int(os.environ.get("MAX_WORKER_DUPLICATE_CHECK", 12))
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 各グループを処理するタスクを投入
            future_to_group = []
            for dupulicate_check_key, event_group in findoneupdate_event_group.items():
                future_to_group.append(executor.submit(_process_event_group, labeled_event_collection, event_group, q_findoneupdate_num))
            findoneupdate_event_group = None
            # 全てのタスクの完了を待ち、例外が発生した場合はログに出力
            for future in concurrent.futures.as_completed(future_to_group):
                try:
                    future.result()  # result()を呼び出すことでワーカー関数内の例外を再発生させる
                except Exception as e:
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise e
            future_to_group = None

    # スレッド毎に処理されたワーカーでの件数を集計する
    # ＃Aggregate the number of items processed by workers for each thread
    insert_num = 0
    update_num = 0
    while not q_findoneupdate_num.empty():
        item = q_findoneupdate_num.get()
        insert_num += item.get("insert_num", 0)
        update_num += item.get("update_num", 0)

    g.applogger.info(f"{insert_num=}")
    g.applogger.info(f"{update_num=}")

    return True


def _process_event_group(labeled_event_collection, event_group, q_findoneupdate_num):
    """
    同じ重複チェックキーを持つイベントグループを逐次処理するワーカー関数。
    各イベントに対して find_one_and_update を実行する。
    """
    findoneupdate_insert_num = 0
    findoneupdate_update_num = 0

    try:
        for event_data in event_group:
            event = event_data["event"]
            conditions_list = event_data["conditions_list"]
            filter = {"$or": [conditions[1] for conditions in conditions_list]} if len(conditions_list) > 1 else conditions_list[0][1]

            # deduplication_settings_id = conditions_list[0][0]
            dupulicate_check_key = event_data["dupulicate_check_key"]

            res = labeled_event_collection.find_one_and_update(
                filter=filter,
                update={
                    "$setOnInsert": event,  # ドキュメントが存在しない場合に挿入する内容
                    "$push": {"exastro_dupulicate_check": dupulicate_check_key}  # ドキュメントが存在する場合に更新する内容
                },
                sort={"labels._exastro_fetched_time": ASCENDING, "exastro_created_at": ASCENDING},
                upsert=True
            )
            if res is None:
                findoneupdate_insert_num += 1
            else:
                findoneupdate_update_num += 1

        # ワーカー内で処理した件数を、Queueに格納する
        # Store the number of items processed in the worker in the Queue
        q_findoneupdate_num.put({"insert_num": findoneupdate_insert_num, "update_num": findoneupdate_update_num})

    except Exception as e:
        raise e
