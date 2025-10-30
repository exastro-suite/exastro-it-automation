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

import datetime

from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.mongoconnect.const import Const as mongoConst
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.api import api_filter
# oase
from common_libs.oase.const import oaseConst
from common_libs.oase.encrypt import agent_encrypt
from libs.oase_receiver_common import check_menu_info, check_auth_menu
from libs.label_event import label_event


@api_filter
def post_event_collection_settings(body, organization_id, workspace_id):  # noqa: E501
    """post_event_collection_settings

    対象のイベント収集設定を取得 # noqa: E501

    :param body:
    :type body: dict | bytes
    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse200
    """
    # メンテナンスモードのチェック
    if g.maintenance_mode.get('data_update_stop') == '1':
        status_code = "498-00004"
        raise AppException(status_code, [], [])  # noqa: F405

    # DB接続
    wsDb = DBConnectWs(workspace_id)

    try:
        menu = 'event_collection'
        # メニューの存在確認
        check_menu_info(menu, wsDb)
        # メニューに対するロール権限をチェック
        check_auth_menu(menu, wsDb)

        # 取得
        where_str = "WHERE DISUSE_FLAG=0 AND EVENT_COLLECTION_SETTINGS_NAME IN ({})".format(", ".join(["%s"] * len(body["event_collection_settings_names"])))  # noqa: E501
        bind_values = tuple(body["event_collection_settings_names"])

        data_list = wsDb.table_select(
            oaseConst.T_OASE_EVENT_COLLECTION_SETTINGS,
            where_str,
            bind_values
        )

        # エージェント用にパスワードカラムを暗号化しなおす
        for data in data_list:
            auth_token = ky_decrypt(data["AUTH_TOKEN"])
            password = ky_decrypt(data['PASSWORD'])
            secret_access_key = ky_decrypt(data['SECRET_ACCESS_KEY'])

            pass_phrase = g.ORGANIZATION_ID + " " + g.WORKSPACE_ID
            data['AUTH_TOKEN'] = agent_encrypt(auth_token, pass_phrase)
            data['PASSWORD'] = agent_encrypt(password, pass_phrase)
            data['SECRET_ACCESS_KEY'] = agent_encrypt(secret_access_key, pass_phrase)
    finally:
        wsDb.db_disconnect()

    return data_list,


@api_filter
def post_events(body, organization_id, workspace_id):  # noqa: E501
    """post_events

    イベントを受け取り、ラベリングして保存する # noqa: E501

    :param body:
    :type body: dict | bytes
    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse2001
    """
    # メンテナンスモードのチェック
    if g.maintenance_mode.get('data_update_stop') == '1':
        status_code = "498-00004"
        raise AppException(status_code, [], [])  # noqa: F405

    # DB接続
    wsDb = DBConnectWs(workspace_id)  # noqa: F405
    wsMongo = MONGOConnectWs()

    try:
        menu = 'event_history'
        # メニューの存在確認
        check_menu_info(menu, wsDb)
        # メニューに対するロール権限をチェック
        privilege = check_auth_menu(menu, wsDb)
        if privilege == '2':
            status_code = "401-00001"
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        # 保存する、整形したイベント
        events = []
        # 保存する、収集単位（ベント収集設定ID×取得時間（fetched_time）のリストを作る）
        collection_group_list = []
        # 保存できないイベント情報のメッセージを格納
        not_available_event_msg_list = []
        # エラーレスポンスを返す場合
        is_err_res = False

        # eventsデータを取り出す
        event_group_list = body["events"]
        for event_group in event_group_list:
            # event_collection_settings_nameもしくは、event_collection_settings_idは必須
            if "event_collection_settings_name" in event_group:
                event_collection_settings_name = event_group["event_collection_settings_name"]
                event_collection_settings = wsDb.table_select(oaseConst.T_OASE_EVENT_COLLECTION_SETTINGS, "WHERE EVENT_COLLECTION_SETTINGS_NAME = %s ORDER BY DISUSE_FLAG", [event_collection_settings_name])  # noqa: E501
                # 受信したデータに不備があるため、イベントは保存されませんでした。({})
                if len(event_collection_settings) == 0:
                    is_err_res = True
                    msg = g.appmsg.get_log_message("499-01801", [f"{event_collection_settings_name=}"])
                    not_available_event_msg_list.append(msg)
                    g.applogger.info(msg)
                    continue
                # 設定が廃止済みのため、イベントは保存されませんでした。({})
                elif event_collection_settings[0]['DISUSE_FLAG'] == '1':
                    msg = g.appmsg.get_log_message("499-01827", [f"{event_collection_settings_name=}"])
                    not_available_event_msg_list.append(msg)
                    g.applogger.info(msg)
                    continue

                event_collection_settings_id = event_collection_settings[0]["EVENT_COLLECTION_SETTINGS_ID"]
            elif "event_collection_settings_id" in event_group:
                event_collection_settings_id = event_group["event_collection_settings_id"]
                event_collection_settings = wsDb.table_select(oaseConst.T_OASE_EVENT_COLLECTION_SETTINGS, "WHERE EVENT_COLLECTION_SETTINGS_ID = %s", [event_collection_settings_id])  # noqa: E501
                # 受信したデータに不備があるため、イベントは保存されませんでした。({})
                if len(event_collection_settings) == 0:
                    msg = g.appmsg.get_log_message("499-01801", [f"{event_collection_settings_id=}"])
                    is_err_res = True
                    not_available_event_msg_list.append(msg)
                    g.applogger.info(msg)
                    continue
                # 設定が廃止済みのため、イベントは保存されませんでした。({})
                elif event_collection_settings[0]['DISUSE_FLAG'] == '1':
                    msg = g.appmsg.get_log_message("499-01827", [f"{event_collection_settings_id=}"])
                    not_available_event_msg_list.append(msg)
                    g.applogger.info(msg)
                    continue

                event_collection_settings_name = event_collection_settings[0]["EVENT_COLLECTION_SETTINGS_NAME"]
            else:
                # 受信したデータに不備があるため、イベントは保存されませんでした。({})
                # # event_collection_settings_idもしくはevent_collection_settings_nameが必要です
                is_err_res = True
                msg = g.appmsg.get_log_message("499-01801", ["'event_collection_settings_name' or 'event_collection_settings_id' is a required property - 'events.0'"])
                not_available_event_msg_list.append(msg)
                g.applogger.info(msg)
                continue

            # 取得時間がなければ、受信時刻を埋める
            if not "fetched_time" in event_group:
                fetched_time =int(datetime.datetime.now().timestamp())
            else:
                fetched_time = int(event_group["fetched_time"])

            # イベント収集設定ID × 取得時間（fetched_time）をイベント収集経過テーブルに保存するためにcollection_group_listに追加する
            collection_group_data = {}
            collection_group_data["EVENT_COLLECTION_SETTINGS_ID"] = event_collection_settings_id
            collection_group_data["FETCHED_TIME"] = fetched_time

            # イベント収集経過テーブルからイベント収集設定IDを基準にfetched_timeの最新1件を取得し、送信されてきたfetched_timeと比較
            collection_progress = wsDb.table_select(oaseConst.T_OASE_EVENT_COLLECTION_PROGRESS, "WHERE EVENT_COLLECTION_SETTINGS_ID = %s ORDER BY `FETCHED_TIME` DESC LIMIT 1", [event_collection_settings_id])  # noqa: E501
            if len(collection_progress) == 0:
                collection_group_list.append(collection_group_data)
            else:
                last_fetched_time = int(collection_progress[0]["FETCHED_TIME"])
                if collection_group_data["FETCHED_TIME"] > last_fetched_time:
                    # リストに格納
                    collection_group_list.append(collection_group_data)
                else:
                    # fetched_timeが最新ではないため、イベントは保存されませんでした。(イベント収集設定id:{}, 最新のfetched_time:{}）
                    msg = g.appmsg.get_log_message("499-01818", [event_collection_settings_id, collection_group_data["FETCHED_TIME"], last_fetched_time])
                    not_available_event_msg_list.append(msg)
                    g.applogger.info(msg)
                    continue

            # イベント収集設定名 × 取得時間（fetched_time）ごとに格納された、イベントのリストを取り出す
            event_list = event_group["event"]
            event_collection_ttl = event_collection_settings[0]["TTL"]
            end_time = fetched_time + int(event_collection_ttl)
            for single_event in event_list:
                # 必要なプロパティを一旦、なければ追加する
                if not "_exastro_event_collection_settings_name" in single_event:
                    single_event['_exastro_event_collection_settings_name'] = event_collection_settings_name

                if not "_exastro_event_collection_settings_id" in single_event:
                    single_event['_exastro_event_collection_settings_id'] = event_collection_settings_id

                if not "_exastro_fetched_time" in single_event:
                    single_event['_exastro_fetched_time'] = fetched_time

                if not "_exastro_end_time" in single_event:
                    single_event['_exastro_end_time'] = end_time

                # 未来の削除用に生成時刻をもたせておく
                single_event['_exastro_created_at'] = datetime.datetime.now(datetime.timezone.utc)

                # 辞書化したイベントをリストに格納
                events.append(single_event)

        if len(events) == 0:
            # 保存可能なeventsデータがありません。（{}）
            if is_err_res is False:
                msg = g.appmsg.get_log_message("499-01802", [", ".join(not_available_event_msg_list)])
                g.applogger.info(msg)
                return not_available_event_msg_list,
            else:
                # 不正データ受信と判断し、エラーレスポンス
                raise AppException("499-01802", [", ".join(not_available_event_msg_list)], [", ".join(not_available_event_msg_list)])

        # ラベリングしてMongoDBに保存
        label_event(wsDb, wsMongo, events)  # noqa: F841

        # MySQLにイベント収集設定IDとfetched_timeを保存する処理を行う
        wsDb.db_transaction_start()
        insert_data_list = wsDb.table_insert(oaseConst.T_OASE_EVENT_COLLECTION_PROGRESS, collection_group_list, "EVENT_COLLECTION_ID", False)  # noqa: F841
        wsDb.db_transaction_end(True)

        # T_OASE_EVENT_COLLECTION_PROGRESSにinsertしたデータのEVENT_COLLECTION_SETTINGS_IDを抽出
        event_collection_settings_id_list = []
        event_collection_settings_id_list = [insert_data['EVENT_COLLECTION_SETTINGS_ID'] for insert_data in insert_data_list if insert_data['EVENT_COLLECTION_SETTINGS_ID'] not in event_collection_settings_id_list]

        # T_OASE_EVENT_COLLECTION_PROGRESSの古いデータを削除
        # 挿入したデータのEVENT_COLLECTION_SETTINGS_IDの中で、指定の期間を過ぎたものを抽出し、あれば削除
        event_collections_progress_ttl = int(float(os.getenv("EVENT_COLLECTION_PROGRESS_TTL", 72)) * 60 * 60)
        fetched_time_limit = int(datetime.datetime.now().timestamp()) - event_collections_progress_ttl

        values_list = [fetched_time_limit] + event_collection_settings_id_list
        ret = wsDb.table_count(oaseConst.T_OASE_EVENT_COLLECTION_PROGRESS, "WHERE `FETCHED_TIME` < %s and `EVENT_COLLECTION_SETTINGS_ID` in ({})".format(','.join(["%s"]*len(event_collection_settings_id_list))), values_list)  # noqa: F841

        if ret > 0:
            wsDb.db_transaction_start()
            ret = wsDb.table_permanent_delete(oaseConst.T_OASE_EVENT_COLLECTION_PROGRESS, "WHERE `FETCHED_TIME` < %s and `EVENT_COLLECTION_SETTINGS_ID` in ({})".format(','.join(["%s"]*len(event_collection_settings_id_list))), values_list)  # noqa: F841
            wsDb.db_transaction_end(True)

    finally:
        wsDb.db_transaction_end(False)
        wsDb.db_disconnect()
        wsMongo.disconnect()

    return not_available_event_msg_list,
