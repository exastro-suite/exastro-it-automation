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
from pymongo import InsertOne

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
from libs.duplicate_check import duplicate_check
from common_libs.notification.sub_classes.oase import OASE, OASENotificationType


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

        # エージェント名、バージョンの初期値
        _undefined_agent_name = oaseConst.DF_AGENT_NAME
        _undefined_agent_version = oaseConst.DF_AGENT_VERSION

        # eventsデータを取り出す
        event_group_list = body["events"]
        if "fetched_time" in event_group_list[0]:
            # fetched_timeがあればソートしておく
            event_group_list.sort(key=lambda x: x['fetched_time'])
        for event_group in event_group_list:
            # event_collection_settings_nameもしくは、event_collection_settings_idは必須
            if "event_collection_settings_name" in event_group:
                event_collection_settings_name = event_group["event_collection_settings_name"]
                event_collection_settings = wsDb.table_select(oaseConst.T_OASE_EVENT_COLLECTION_SETTINGS, "WHERE EVENT_COLLECTION_SETTINGS_NAME = %s", [event_collection_settings_name])  # noqa: E501
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
                fetched_time = int(datetime.datetime.now().timestamp())
            else:
                fetched_time = int(event_group["fetched_time"])

            # エージェントの識別情報を取得。無ければ固定値で埋める
            _undefined_exastro_agent = {
                "name": _undefined_agent_name,
                "version": _undefined_agent_version
            }
            if isinstance(event_group.get("agent"), dict):
                exastro_agent = event_group.get("agent", {})
                # 空文字で来た場合も未定義扱い
                for _k, _v in _undefined_exastro_agent.items():
                    exastro_agent[_k] = exastro_agent[_k] or _v
            else:
                exastro_agent =  _undefined_exastro_agent

            # エージェント名またはバージョンが未定義の場合に警告ログを出力
            undefined_items = []
            if exastro_agent.get("name") == _undefined_agent_name:
                undefined_items.append("name")
            if exastro_agent.get("version") == _undefined_agent_version:
                undefined_items.append("version")

            if undefined_items:
                g.applogger.warning(
                    f"agent.{'/'.join(undefined_items)} is _undefined: {event_collection_settings_id=}"
                )

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
                single_event['_exastro_agent_name'] = exastro_agent.get("name")
                single_event['_exastro_agent_version'] = exastro_agent.get("version")
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
        labeled_event_list = label_event(wsDb, wsMongo, events)  # noqa: F841

        try:
            # 重複排除してmongoに書き込む
            duplicate_check_result = duplicate_check(wsDb, wsMongo, labeled_event_list)
            if duplicate_check_result is False:
                # 重複排除を行わなかった場合は、ラベル付きデータを保存
                labeled_event_collection = wsMongo.collection(mongoConst.LABELED_EVENT_COLLECTION)  # ラベル付与したイベントデータを保存するためのコレクション
                labeled_event_collection.bulk_write([InsertOne(x) for x in labeled_event_list])
        except Exception as e:
            g.applogger.error(stacktrace())
            err_code = "499-01803"
            raise AppException(err_code, [e], [e])


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


def add_notification_queue(wsdb, recieve_notification_list, duplicate_notification_list):
    """ スレッド処理で実施するイベント通知キューに追加する\n
        Args:
            wsdb: MariaDBのWSDBコネクション
            recieve_notification_list: 受信時アラート通知用
            duplicate_notification_list: 重複排除アラート通知用
        Returns:
            tuple: 2つの辞書 (recieve_ret, duplicate_ret)
                - recieve_ret (dict): 受信時アラート通知処理の結果
                - duplicate_ret (dict): 重複排除アラート通知処理の結果。

    """
    recieve_ret = {}
    duplicate_ret = {}
    try:
        recieve_decision_information = {"notification_type": OASENotificationType.RECEIVE}
        duplicate_decision_information = {"notification_type": OASENotificationType.DUPLICATE}
        # イベント種別ごとに分けてbulksendを呼び出す（受信時アラート）
        if recieve_notification_list:
            recieve_ret = OASE.bulksend(wsdb, recieve_notification_list, recieve_decision_information)
            # PF通知キューへの追加失敗があればログに出しておく
            if recieve_ret.get("failure", 0) > 0:
                g.applogger.info(f'Notification API call Failed {recieve_ret["failure"]}: {recieve_ret["failure_info"]}')
            g.applogger.debug(g.appmsg.get_log_message("BKY-80018", [recieve_ret]))
        # イベント種別ごとに分けてbulksendを呼び出す（重複排除アラート）
        if duplicate_notification_list:
            duplicate_ret = OASE.bulksend(wsdb, duplicate_notification_list, duplicate_decision_information)
            # PF通知キューへの追加失敗があればログに出しておく
            if duplicate_ret.get("failure", 0) > 0:
                g.applogger.info(f'Notification API call Failed {duplicate_ret["failure"]}: {duplicate_ret["failure_info"]}')
            g.applogger.debug(g.appmsg.get_log_message("BKY-80018", [duplicate_ret]))
    except Exception:
        # 通知処理の中で例外が発生したとしてもイベント自体はmongoに登録されているので、わざわざ例外発生はさせない
        # ロガーのエラーレベルで出しておくくらい
        g.applogger.error(stacktrace())
        g.applogger.error(g.appmsg.get_log_message("BKY-80018", [[recieve_ret, duplicate_ret]]))

    return recieve_ret, duplicate_ret
