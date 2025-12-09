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
from pymongo import ASCENDING, InsertOne, ReturnDocument
import concurrent.futures
from collections import defaultdict
import queue

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
    """重複排除を行う

    Args:
        wsDb (object): データベース接続オブジェクト
        wsMongo (object): MongoDB接続オブジェクト
        labeled_event_list (list): ラベル付与されたイベントのリスト

    Raises:
        e: _description_

    Returns:
        bool: 重複排除処理を実施したかどうか
        recieve_notification_list (list): 受信通知リスト
        duplicate_notification_list (list): 重複通知リスト

    """
    recieve_notification_list = []
    duplicate_notification_list = []

    # 重複排除の設定を取得
    deduplication_settings = wsDb.table_select(
        oaseConst.T_OASE_DEDUPLICATION_SETTINGS,
        "WHERE DISUSE_FLAG='0' ORDER BY SETTING_PRIORITY, DEDUPLICATION_SETTING_NAME"
    )
    if len(deduplication_settings) == 0:
        # 重複排除の設定設定を取得できませんでした。
        msg = "There are no deduplication settings."
        g.applogger.info(msg)
        return False, recieve_notification_list, duplicate_notification_list

    DEDUPLICATION_SETTINGS_MAP = {}
    DEDUPLICATION_SETTINGS_ECS_MAP = {}

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
        duplicate_check_key = "{}_{}".format(event_collection_settings_id, agent_name)

        # 重複排除設定がなければ、追加決定
        if event_collection_settings_id not in DEDUPLICATION_SETTINGS_ECS_MAP:
            event["exastro_duplicate_check"] = [duplicate_check_key]

            # bulk_writeの初期値対応(find_one_and_updateの$inc対応分)
            event["exastro_duplicate_collection_settings_ids"] = {event["labels"]["_exastro_event_collection_settings_id"]: 1}
            event["exastro_agents"] = {event["labels"]["_exastro_agent_name"]: 1}
            event["exastro_edit_count"] = 1

            bulkwrite_event_list.append(InsertOne(event))
            recieve_notification_list.append(event)
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
                "exastro_duplicate_check": {"$nin": [duplicate_check_key]}  # これから重複する以外のケース（先着イベントor先着イベントに刻まれている）を省くため
            }
            if tmp_user_labels:
                conditions.update(tmp_user_labels)  # ラベルのkey&valueの一致
            # g.applogger.debug(f"{conditions=}")

            # 検索条件を追加（重複排除ごとに検索するのではなく、まとめる）
            conditions_list.append((deduplication_settings_id, conditions))

        # g.applogger.debug(f"{conditions_list=}")
        if len(conditions_list) == 0:
            # insertしかありえない
            event["exastro_duplicate_check"] = [duplicate_check_key]

            # bulk_writeの初期値対応(find_one_and_updateの$inc対応分)
            event["exastro_duplicate_collection_settings_ids"] = {event["labels"]["_exastro_event_collection_settings_id"]: 1}
            event["exastro_agents"] = {event["labels"]["_exastro_agent_name"]: 1}
            event["exastro_edit_count"] = 1

            bulkwrite_event_list.append(InsertOne(event))
            recieve_notification_list.append(event)
            continue

        # upsertする場合は、その場でmongoにクエリを発行する（find_one_and_updateがbulk_writeできないから）
        # タスクをduplicate_check_keyごとにまとめる
        findoneupdate_event_group[duplicate_check_key].append({
            "event": event,
            "conditions_list": conditions_list,
            "duplicate_check_key": duplicate_check_key
        })

    labeled_event_list = None

    if len(bulkwrite_event_list) != 0:
        labeled_event_collection.bulk_write(bulkwrite_event_list)
        g.applogger.info("bulk_write_num={}".format(len(bulkwrite_event_list)))
        bulkwrite_event_list = None

    q_findoneupdate_num = queue.Queue()
    if findoneupdate_event_group:
        # スレッド数。I/Oバウンドな処理なので、CPUコア数より多めに設定するのが一般的
        MAX_WORKERS = int(os.environ.get("MAX_WORKER_THREAD_POOL_SIZE", 12))
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 各グループを処理するタスクを投入
            future_to_group = []
            for duplicate_check_key, event_group in findoneupdate_event_group.items():
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
        recieve_notification_list.extend(item.get("recieve_notification_list", []))
        duplicate_notification_list.extend(item.get("duplicate_notification_list", []))

    g.applogger.info(f"{insert_num=}")
    g.applogger.info(f"{update_num=}")

    return True, recieve_notification_list, duplicate_notification_list


def _process_event_group(labeled_event_collection, event_group, q_findoneupdate_num):
    """
    同じ重複チェックキーを持つイベントグループを逐次処理するワーカー関数。
    各イベントに対して find_one_and_update を実行する。
    """
    findoneupdate_insert_num = 0
    findoneupdate_update_num = 0
    recieve_notification_list = []
    duplicate_notification_list = []

    try:
        for event_data in event_group:
            # InsertかUpdateかの判定 True: Insert, False: Update
            is_event_inserted = False
            # 新規イベント(受信)の通知対象
            recieve_notification_flag = False
            # 新規イベント(統合)の通知対象
            duplicate_notification_flag = False

            event = event_data["event"]
            conditions_list = event_data["conditions_list"]
            filter = {"$or": [conditions[1] for conditions in conditions_list]} if len(conditions_list) > 1 else conditions_list[0][1]

            # deduplication_settings_id = conditions_list[0][0]
            duplicate_check_key = event_data["duplicate_check_key"]

            # システム情報の追加: エージェント名、重複排除ID・設定、
            _exastro_event_collection_settings_id = event["labels"]["_exastro_event_collection_settings_id"]
            _exastro_agent_name = event["labels"]["_exastro_agent_name"]

            # 関連する重複排除設定を取得
            _deduplication_setting_ids = DEDUPLICATION_SETTINGS_ECS_MAP[_exastro_event_collection_settings_id]
            _deduplication_setting_list = {_dsid: DEDUPLICATION_SETTINGS_MAP[_dsid] for _dsid in _deduplication_setting_ids}

            res = labeled_event_collection.find_one_and_update(
                filter=filter,
                update={
                    "$setOnInsert": event,  # ドキュメントが存在しない場合に挿入する内容
                    "$push": {"exastro_duplicate_check": duplicate_check_key},  # ドキュメントが存在する場合に更新する内容
                    "$inc": {
                        f"exastro_duplicate_collection_settings_ids.{_exastro_event_collection_settings_id}": 1,  # 収集設定ごとの重複イベント数をインクリメント
                        f"exastro_agents.{_exastro_agent_name}": 1,  # エージェントごとの重複イベント数をインクリメント
                        "exastro_edit_count": 1,  # upsertの回数
                    }
                },
                sort={"labels._exastro_fetched_time": ASCENDING, "exastro_created_at": ASCENDING},
                upsert=True,
                return_document=ReturnDocument.AFTER
            )

            # 登録か更新かの判定
            is_event_inserted = is_new_event(res)

            # イベント受信通知対象か判定
            recieve_notification_flag = should_notify_event(
                _deduplication_setting_ids,
                _deduplication_setting_list,
                is_event_inserted,
                extract_collection_settings_counts(res),
                extract_agents_counts(res),
                _exastro_event_collection_settings_id,
            )

            # 更新時、重複排除通知対象か判定
            duplicate_notification_flag = is_duplicate_notification_needed(
                _deduplication_setting_ids,
                _deduplication_setting_list,
                extract_collection_settings_counts(res),
                extract_agents_counts(res),
                _exastro_event_collection_settings_id,
            ) if is_event_inserted is False else False

            # 処理件数のカウント
            if is_event_inserted:
                findoneupdate_insert_num += 1
            else:
                findoneupdate_update_num += 1

            # 通知のテンプレート用: 登録処理後(res:find_one_and_update後)に元データ(event:find_one_and_update前)で一部差し替え
            for uk in [rk for rk in res.keys() if rk in event]:
                res[uk] = event[uk]

            # 受信通知対象ならリストに追加: ReturnDocument.AFTER
            recieve_notification_list.append(res) if recieve_notification_flag else None
            # 重複排除済みならリストに追加: ReturnDocument.AFTER
            duplicate_notification_list.append(res) if duplicate_notification_flag else None

        # ワーカー内で処理した件数を、Queueに格納する
        # Store the number of items processed in the worker in the Queue
        q_findoneupdate_num.put({
            "insert_num": findoneupdate_insert_num,
            "update_num": findoneupdate_update_num,
            "recieve_notification_list": recieve_notification_list,
            "duplicate_notification_list": duplicate_notification_list
        })

    except Exception as e:
        raise e


def is_new_event(res: dict) -> bool:
    """
    ドキュメントの操作回数のカウント総数からイベントの判定を行う。
    1の場合は新規登録、それ以外は更新イベントとみなす。

    Args:
        res: find_one_and_updateの戻り値
    Returns:
        bool: True: 新規登録, False: 更新
    """
    _exastro_edit_count = res.get("exastro_edit_count", 1) if res else 1
    _exastro_edit_count = 1 if _exastro_edit_count is None else _exastro_edit_count
    return (_exastro_edit_count == 1)


def extract_collection_settings_counts(res: dict) -> dict:
    """
    イベントが使用したイベント収集設定IDごとのカウント情報を取得する。
    Args:
        res: find_one_and_updateの戻り値
    Returns:
        dict: key: イベント収集設定ID, value: カウント
    """

    return res.get("exastro_duplicate_collection_settings_ids", {}) if res else {}


def extract_agents_counts(res: dict) -> dict:
    """
    イベントが使用したエージェントごとのカウント情報を取得する。
    Args:
        res: find_one_and_updateの戻り値
    Returns:
        dict: key: エージェント名, value: カウント
    """
    return res.get("exastro_agents", {}) if res else {}


def should_notify_event(deduplication_setting_ids: list, deduplication_setting_list: dict, is_event_inserted: bool, collection_settings_counts: dict, agents_counts: dict, _exastro_event_collection_settings_id: str) -> bool:
    """
    イベントが通知対象かどうかを判定する。
    新規登録イベントは通知する。重複イベントの場合、いずれかの重複排除設定で
    イベントソース冗長化グループが2つ以上あれば通知対象とする。
    Args:
        deduplication_setting_ids (list): 重複排除設定ID
        deduplication_setting_list (dict): key: 重複排除設定ID, value: 重複排除設定
        is_event_inserted (bool): bool: True: 新規登録, False: 更新
    Returns:
        bool: True: 通知対象, False: 通知対象外
    """

    # 新規登録イベントは通知
    if is_event_inserted:
        return True

    # 収集設定、エージェントの件数が不正な場合は通知対象外
    if not isinstance(collection_settings_counts, dict) or not isinstance(agents_counts, dict):
        return False

    # 今回のイベントでカウントアップしたものを除外して計算
    collection_settings_counts_noself = {}
    for _k, _v in collection_settings_counts.items():
        collection_settings_counts_noself[_k] = _v - 1 if _k == _exastro_event_collection_settings_id and _v > 0 else _v

    # 収集設定で今回のイベント分を除外したカウント
    collection_setting_count_notime = collection_settings_counts_noself[_exastro_event_collection_settings_id] \
        if _exastro_event_collection_settings_id in collection_settings_counts_noself else None

    # 重複イベントは、いずれかの重複排除設定でイベントソース冗長化グループが2つ以上あれば通知
    for dsid in deduplication_setting_ids:
        redundancy_group = deduplication_setting_list[dsid].get('EVENT_SOURCE_REDUNDANCY_GROUP', [])
        if len(redundancy_group) == 1:
            return False
        elif len(redundancy_group) > 1:
            # イベントソースで初回以外は通知しない
            if collection_setting_count_notime is None or collection_setting_count_notime != 0:
                return False
            else:
                # イベントソースに対して初回なら通知
                return True
        else:
            # 重複排除設定のイベントソースが空の場合は通知対象外
            return False
    return False


def is_duplicate_notification_needed(deduplication_setting_ids: list, deduplication_setting_list: dict, collection_settings_counts: dict, agents_counts: dict, _exastro_event_collection_settings_id: str) -> bool:
    """
    重複排除通知が必要かどうかを判定する。
    すべてのイベントソース冗長化グループIDで1回以上イベントが発生していれば通知対象とする。
    Args:
        deduplication_setting_ids (list):重複排除設定ID
        deduplication_setting_list (dict):  重複排除設定ID, value: 重複排除設定
        collection_settings_counts (dict): イベント収集設定ID, value: カウント
        agents_counts (dict): エージェント名, value: カウント
    Returns:
        bool: True: 通知対象, False: 通知対象外
    """

    # 重複排除設定のイベントソースで1回以上イベントが発生しているか
    for dsid in deduplication_setting_ids:
        redundancy_group = deduplication_setting_list[dsid].get('EVENT_SOURCE_REDUNDANCY_GROUP', [])
        # 重複排除設定でイベントソース冗長化グループが1つなら通知対象外
        if len(redundancy_group) == 1:
            return False
        elif len(redundancy_group) > 1:
            _csv_max = max(collection_settings_counts.values())
            _csv_min = min(collection_settings_counts.values())
            _csv_sum = sum(collection_settings_counts.values())

            # 今回のイベントでカウントアップしたものを除外して計算
            collection_settings_counts_noself = {}
            for _k, _v in collection_settings_counts.items():
                collection_settings_counts_noself[_k] = _v - 1 if _k == _exastro_event_collection_settings_id and _v > 0 else _v
            collection_setting_count_notime = collection_settings_counts_noself[_exastro_event_collection_settings_id] if _exastro_event_collection_settings_id in collection_settings_counts_noself else None

            # 冗長化グループ内でのイベント発生状況を確認
            redundancy_check = [True for redundancy_group_id in redundancy_group if redundancy_group_id in collection_settings_counts]

            # 重複排除の全収集設定の全て1回ずつイベントが発生している場合は通知対象
            if _csv_sum == len(redundancy_group) and _csv_max == 1 and _csv_min == 1 and all(redundancy_check):
                return True
            # 重複排除のある収集設定Aに1以上で、収集設定Bに1の場合は通知対象(既に全収集設定の全て1回ずつイベントが発生している場合は対象外)
            if len(collection_settings_counts_noself) >= len(redundancy_group) and collection_setting_count_notime == 0 and all(redundancy_check):
                return True
    return False
