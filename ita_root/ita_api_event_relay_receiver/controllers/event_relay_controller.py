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

from common_libs.api import api_filter
# from common_libs.common import DBConnectWs
from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from libs import event_relay
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

    data = event_relay.get_event_collection_settings(wsDb, body)

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

    event_result = False

    # DB接続
    wsDb = DBConnectWs(workspace_id)  # noqa: F405
    wsMongo = MONGOConnectWs()

    events_moto = {
        "events": [
            {
                "event": [
                    '{"message_id": "<20231004071711.06338770D0A0@ita-event-relay-mailserver.localdomain_1>","envelope_from": "root@ita-event-relay-mailserver.localdomain_1","envelope_to": "user1@localhost_1","header_from": "<root@ita-event-relay-mailserver.localdomain_1>","header_to": "user1@localhost_1","mailaddr_from": "root <root@ita-event-relay-mailserver.localdomain_1>","mailaddr_to": "user1@localhost_1","date": "2023-10-04 16:17:11","lastchange": 1696403830.1,"body": "Lorem1 ipsum dolor sit amet consectetur adipisicing elit. Blanditiis impedit, ipsam consequatur architecto voluptatum minima soluta animi numquam quod odio quae explicabo laudantium nulla? Quia in nesciunt quo quibusdam qui! Lorem ipsum dolor sit amet consectetur adipisicing elit. Blanditiis impedit, ipsam consequatur architecto voluptatum minima soluta animi numquam quod odio quae explicabo laudantium nulla? Quia in nesciunt quo quibusdam qui!\r\n","_exastro_event_collection_settings_id": "c65d5636-73e2-4372-9dc9-9de49c1cde94","_exastro_fetched_time": "1111111112","_exastro_end_time": "1111111113"}',
                    '{"message_id": "<20231004071711.06338770D0A0@ita-event-relay-mailserver.localdomain_2>","envelope_from": "root@ita-event-relay-mailserver.localdomain_2","envelope_to": "user1@localhost_2","header_from": "<root@ita-event-relay-mailserver.localdomain_2>","header_to": "user1@localhost_2","mailaddr_from": "root <root@ita-event-relay-mailserver.localdomain_2>","mailaddr_to": "user1@localhost_2","date": "2023-10-04 16:17:12","lastchange": 1696403830.2,"body": "Lorem2 ipsum dolor sit amet consectetur adipisicing elit. Blanditiis impedit, ipsam consequatur architecto voluptatum minima soluta animi numquam quod odio quae explicabo laudantium nulla? Quia in nesciunt quo quibusdam qui! Lorem ipsum dolor sit amet consectetur adipisicing elit. Blanditiis impedit, ipsam consequatur architecto voluptatum minima soluta animi numquam quod odio quae explicabo laudantium nulla? Quia in nesciunt quo quibusdam qui!\r\n","_exastro_event_collection_settings_id": "c65d5636-73e2-4372-9dc9-9de49c1cde94","_exastro_fetched_time": "1111111112","_exastro_end_time": "1111111113"}'
                ],
                "fetched_time": 11111112,
                "event_collection_settings_id": "c65d5636-73e2-4372-9dc9-9de49c1cde94"
            },
            {
                "event": [
                    '{"message_id": "<20231004071711.06338770D0A0@ita-event-relay-mailserver.localdomain_3>","envelope_from": "root@ita-event-relay-mailserver.localdomain_3","envelope_to": "user1@localhost_3","header_from": "<root@ita-event-relay-mailserver.localdomain_3>","header_to": "user1@localhost_3","mailaddr_from": "root <root@ita-event-relay-mailserver.localdomain_3>","mailaddr_to": "user1@localhost_3","date": "2023-10-04 16:17:13","lastchange": 1696403830.3,"body": "Lorem3 ipsum dolor sit amet consectetur adipisicing elit. Blanditiis impedit, ipsam consequatur architecto voluptatum minima soluta animi numquam quod odio quae explicabo laudantium nulla? Quia in nesciunt quo quibusdam qui! Lorem ipsum dolor sit amet consectetur adipisicing elit. Blanditiis impedit, ipsam consequatur architecto voluptatum minima soluta animi numquam quod odio quae explicabo laudantium nulla? Quia in nesciunt quo quibusdam qui!\r\n","_exastro_event_collection_settings_id": "eb66c6fe-344e-4609-9a56-5798eb3d2859","_exastro_fetched_time": "2222222222","_exastro_end_time": "2222222223"}'
                ],
                "fetched_time": 22222222,
                "event_collection_settings_id": "eb66c6fe-344e-4609-9a56-5798eb3d2859"
            },
            {
                "event": [
                    '{"message_id": "<20231004071711.06338770D0A0@ita-event-relay-mailserver.localdomain_4>","envelope_from": "root@ita-event-relay-mailserver.localdomain_4","envelope_to": "user1@localhost_4","header_from": "<root@ita-event-relay-mailserver.localdomain_4>","header_to": "user1@localhost_4","mailaddr_from": "root <root@ita-event-relay-mailserver.localdomain_4>","mailaddr_to": "user1@localhost_4","date": "2023-10-04 16:17:14","lastchange": 1696403830.4,"body": "Lorem4 ipsum dolor sit amet consectetur adipisicing elit. Blanditiis impedit, ipsam consequatur architecto voluptatum minima soluta animi numquam quod odio quae explicabo laudantium nulla? Quia in nesciunt quo quibusdam qui! Lorem ipsum dolor sit amet consectetur adipisicing elit. Blanditiis impedit, ipsam consequatur architecto voluptatum minima soluta animi numquam quod odio quae explicabo laudantium nulla? Quia in nesciunt quo quibusdam qui!\r\n","_exastro_event_collection_settings_id": "c65d5636-73e2-4372-9dc9-9de49c1cde94","_exastro_fetched_time": "3333333333","_exastro_end_time": "4444444443"}'
                ],
                "fetched_time": 33333333,
                "event_collection_settings_id": "c65d5636-73e2-4372-9dc9-9de49c1cde94"
            }
        ]
    }

    events = []

    data_list = []

    # eventsデータを取り出す
    events_list = events_moto["events"]

    for events_dict in events_list:
        data_dict = {}

        event_list = events_dict["event"]

        data_dict["EVENT_COLLECTION_SETTINGS_ID"] = events_dict["event_collection_settings_id"]
        data_dict["FETCHED_TIME"] = events_dict["fetched_time"]

        data_list.append(data_dict)

        for event_str in event_list:
            # tryの中で辞書化する
            try:
                event_dict = json.loads(event_str, strict=False)
            except Exception as e:
                print(e)
                return event_result

            events.append(event_dict)

    # そのまま/ラベリングしてMongoDBに保存
    res = label_event(wsDb, wsMongo, events)

    # MySQLにevent_collection_settings_idとfetched_timeを保存
    table_name = "T_EVRL_EVENT_COLLECTION_PROGRESS"
    primary_key_name = "EVENT_COLLECTION_ID"

    wsDb.db_transaction_start()

    ret = wsDb.table_insert(table_name, data_list, primary_key_name, True)

    wsDb.db_transaction_end(True)

    event_result = True

    if event_result is False:
        data = {}
        msg = "Error"
        result_code = "000-99999"
        status_code = 777
    else:
        data = {}
        msg = ""
        result_code = "000-00000"
        status_code = 200

    return data, msg, result_code, status_code,