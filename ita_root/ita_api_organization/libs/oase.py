#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
from flask import g

from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.loadtable import *
from datetime import datetime
from pymongo import ASCENDING


def rest_filter(objdbca, menu, filter_parameter):
    """
        メニューのレコード取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu: メニュー string
            filter_parameter: 検索条件  {}
            lang: 言語情報 ja / en
            mode: 本体 / 履歴
        RETRUN:
            statusCode, {}, msg
    """

    mode = 'inner'
    objmenu = load_table.loadTable(objdbca, menu)
    if objmenu.get_objtable() is False:
        log_msg_args = ["not menu or table"]
        api_msg_args = ["not menu or table"]
        raise AppException("401-00001", log_msg_args, api_msg_args) # noqa: F405

    status_code, result, msg = objmenu.rest_filter(filter_parameter, mode)
    if status_code != '000-00000':
        log_msg_args = [msg]
        api_msg_args = [msg]
        raise AppException(status_code, log_msg_args, api_msg_args)

    return result


def collect_event_history(wsMongo: MONGOConnectWs, parameter: dict):
    """
    検索条件を指定し、イベント履歴を取得する
    ARGS:
        wsMongo:DB接続クラス  MONGOConnectWs()
        parameter:bodyの中身
    RETRUN:
        data
    """

    # イベント履歴のコレクション名
    COLLECTION_NAME = "labeled_event_collection"

    # MongoDBから取得するデータのソート条件
    SORT_KEY = [
        ("labels._exastro_fetched_time", ASCENDING),
        ("labels._exastro_end_time", ASCENDING),
        ("_id", ASCENDING)
    ]

    def create_filter():
        """
        イベント履歴の検索に使用する条件を取得する
        RETRUN:
            filter
        """

        # APIのリクエストパラメータとmongoDBのイベント履歴の項目の対応表。
        PARAM_MAP = {
            "start_time": "labels._exastro_end_time",
            "end_time": "labels._exastro_fetched_time",
            "evaluted": "labels._exastro_evaluated",
            "undetected": "labels._exastro_undetected",
            "timeouted": "labels._exastro_timeout"
        }

        # UNIX時間への変換処理を行うパラメータ。
        TIME_PARAM = ["start_time", "end_time"]

        # boolから0,1への変換処理を行うパラメータ。
        BOOL_PARAM = ["evaluted", "undetected", "timeouted"]

        filter = {}
        for key, value in parameter.items():
            # 想定していないパラメータを渡された場合は次のパラメータにスキップする。
            param_key = PARAM_MAP.get(key)
            if param_key is None:
                continue

            fix_value = None
            # MongoDBのデータに合わせるため、時刻項目の場合UNIX時間に変換する。
            if key in TIME_PARAM:
                dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z')
                fix_value = str(int(dt.timestamp()))
            # MongoDBのデータに合わせるため、Bool値の場合は一旦intに変換し、その後文字に変換する。
            elif key in BOOL_PARAM:
                fix_value = str(int(value))
            # 初期化漏れを防ぐため定義。扱うパラメータを考慮すると通ることはない。
            else:
                fix_value = value

            # UNIX時間は範囲を条件とするため値の設定方法を変える
            if key == "start_time":
                filter[param_key] = {"$gte": fix_value}
            elif key == "end_time":
                filter[param_key] = {"$lte": fix_value}
            else:
                filter[param_key] = fix_value

        return filter

    event_history = (wsMongo.collection(COLLECTION_NAME)
                     .find(create_filter())
                     .sort(SORT_KEY))

    # MongoDBから取得した値をそのまま返却するとエラーになるため原因となる項目（_id）を変換する
    result = []
    for item in event_history:
        item["_id"] = str(item["_id"])
        result.append(item)

    return result


def collect_action_log(wsDb: DBConnectWs, parameter: dict):
    """
    検索条件を指定し、アクション履歴を取得する
    ARGS:
        wsDb:DB接続クラス  DBConnectWs()
        parameter:bodyの中身
    RETRUN:
        data
    """

    # アクション履歴テーブルの物理名
    TABLE_NAME = "T_OASE_ACTION_LOG"

    # 取得するアクション履歴のソート条件
    SORT_KEY = "ORDER BY TIME_REGISTER, ACTION_LOG_ID"

    def create_where():
        """
        アクション履歴の検索に使用する条件を取得する
        RETRUN:
            where: where句の文字列
            bind_value: 検索で指定する値
        """

        TARGET_PARAM = ["start_time", "end_time"]

        # 後にORDER BY句の文字列を結合することを考慮して予め末尾にスペースを仕込んでおく。
        where = "WHERE DISUSE_FLAG=0 "
        bind_value = []
        for key, value in parameter.items():
            # 想定していないパラメータを渡された場合は次のパラメータにスキップする。
            if key not in TARGET_PARAM:
                continue

            # 片落ちで指定されることを想定してBetweenは使わない。
            if key == "start_time":
                where += "AND TIME_REGISTER >= %s "
            elif key == "end_time":
                where += "AND TIME_REGISTER <= %s "

            bind_value.append(value)

        return where, bind_value

    where, bind_value = create_where()
    action_log = wsDb.table_select(
        TABLE_NAME,
        where + SORT_KEY,
        bind_value
    )

    return action_log


def create_history_list(event_history: list, action_log: list):
    """
    イベント履歴とアクション履歴をまとめて日時の昇順でソートしたリストを作成する
    ARGS:
        event_history:イベント履歴のリスト
        action_log:アクション履歴のリスト
    RETRUN:
        history_list
    """

    history_list = []

    for event in event_history:
        append_data = {}
        append_data["id"] = event["_id"]
        append_data["type"] = "event"

        ts = int(event["labels"]["_exastro_fetched_time"])
        dt = datetime.fromtimestamp(ts)
        append_data["datetime"] = dt.strftime("%Y-%m-%d %H:%M:%S")

        append_data["item"] = event

        history_list.append(append_data)

    for action in action_log:
        append_data = {}
        append_data["id"] = action["ACTION_LOG_ID"]
        append_data["type"] = "action"

        tr = action["TIME_REGISTER"]
        append_data["datetime"] = tr.strftime("%Y-%m-%d %H:%M:%S")

        append_data["item"] = action

        history_list.append(append_data)

    # 毎回同じ順序で取得できるようにidをソートキーに加える
    # （UUIDなので追加されると順番が崩れ可能性はあるが、過去データを参照する場合は問題ない認識）
    # またイベントの結果アクションが発生するという流れを考慮しイベントが先に来るようにtypeをソートキーに指定
    history_list.sort(key=lambda x: x["id"], reverse=False)
    history_list.sort(key=lambda x: x["type"], reverse=True)
    history_list.sort(key=lambda x: x["datetime"], reverse=False)

    return history_list
