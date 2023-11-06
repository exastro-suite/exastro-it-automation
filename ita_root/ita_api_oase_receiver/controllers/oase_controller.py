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

from flask import g

from common_libs.api import api_filter
from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.common.exception import AppException
from libs import oase
from libs.label_event import label_event
import json


@api_filter
def post_event_collection_settings(body, organization_id, workspace_id):  # noqa: E501
    """post_event_collection_settings

    対象のイベント収集設定と最新のイベント取得時間を取得 # noqa: E501

    :param body:
    :type body: dict | bytes
    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse200
    """

    wsDb = DBConnectWs(workspace_id)

    data = oase.get_event_collection_settings(wsDb, body)

    return data,


@api_filter
def post_event_collection_events(body, organization_id, workspace_id):  # noqa: E501
    """post_event_collection_events

    イベントを受け取り、ラベリングして保存する # noqa: E501

    :param body:
    :type body: dict | bytes
    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2001
    """
    # DB接続
    wsDb = DBConnectWs(workspace_id)  # noqa: F405
    wsMongo = MONGOConnectWs()

    # メンテナンスモードのチェック
    if g.maintenance_mode.get('data_update_stop') == '1':
        status_code = "498-00004"
        raise AppException(status_code, [], [])  # noqa: F405

    # 保存する、整形したイベント
    events = []
    # 保存するイベント取得時間
    fetched_time_list = []

    # eventsデータを取り出す
    events_list = body["events"]

    for single_event in events_list:
        single_data = {}

        # 文字列化された辞書を取り出す
        event_list = single_event["event"]

        # イベント収集設定IDとfetched_timeをsingle_dataに格納する
        single_data["EVENT_COLLECTION_SETTINGS_ID"] = single_event["event_collection_settings_id"]
        single_data["FETCHED_TIME"] = single_event["fetched_time"]

        event_collection_settings_id = single_data["EVENT_COLLECTION_SETTINGS_ID"]
        fetched_time = single_data["FETCHED_TIME"]

        table_name = "T_OASE_EVENT_COLLECTION_PROGRESS"
        primary_key_name = "EVENT_COLLECTION_ID"

        # イベント収集経過テーブルからイベント収集設定IDを基準にfetched_timeが最新のもの1件を取得する
        collection_progress = wsDb.table_select(table_name, "WHERE EVENT_COLLECTION_SETTINGS_ID = %s ORDER BY `FETCHED_TIME` DESC LIMIT 1", [event_collection_settings_id])  # noqa: E501

        if collection_progress == []:
            fetched_time_list.append(single_data)
        else:
            last_fetched_time = collection_progress[0]["FETCHED_TIME"]

            if fetched_time <= last_fetched_time:
                g.applogger.info("送られてきたfetched_timeは最新ではないため保存されませんでした")
                g.applogger.info(last_fetched_time)
                g.applogger.info(single_event)
                continue
            # イベント収集設定IDとfetched_timeをリストに格納
            fetched_time_list.append(single_data)

        # 辞書型のイベントから文字列型のイベントを取り出す
        for event_str in event_list:
            # tryの中で文字列から辞書化する
            try:
                event_dict = json.loads(event_str, strict=False)
            except Exception as e:
                # "イベントのデータ形式に不備があります"
                err_code = "499-00402"
                log_msg_args = [e, json.dumps(single_event)]
                api_msg_args = [json.dumps(single_event)]
                raise AppException(err_code, log_msg_args, api_msg_args)
            # 辞書化したイベントをリストに格納
            events.append(event_dict)

    if len(events) == 0:
        # "eventsデータが取得できませんでした。"
        err_code = "499-00402"
        raise AppException(err_code)

    # そのまま/ラベリングしてMongoDBに保存
    err_code, err_msg = label_event(wsDb, wsMongo, events)  # noqa: F841
    if err_code != "":
        return "", err_msg, err_code

    # MySQLにイベント収集設定IDとfetched_timeを保存する処理を行う
    wsDb.db_transaction_start()
    ret = wsDb.table_insert(table_name, fetched_time_list, primary_key_name, True)  # noqa: F841
    wsDb.db_transaction_end(True)

    return '',
