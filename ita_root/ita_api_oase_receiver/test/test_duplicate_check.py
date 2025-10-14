#   Copyright 2025 NEC Corporation
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

import pytest
from unittest.mock import MagicMock, patch
import mongomock
import queue
import time

from common_libs.common.mongoconnect.const import Const as mongoConst

from libs import duplicate_check


# モックオブジェクトのセットアップ
class MockG:
    """gオブジェクトのモック"""
    def __init__(self):
        self.appmsg = MagicMock()
        self.applogger = MagicMock()
        self.applogger.info = MagicMock()
        self.applogger.debug = MagicMock()

    def __getattr__(self, name):
        return MagicMock()


# テスト用のグローバル変数
g = MockG()


@pytest.fixture
def mock_db():
    """データベース接続のモック"""
    return MagicMock()


@pytest.fixture
def mock_mongo():
    """MongoDB接続のモック (mongomockを使用)"""
    client = mongomock.MongoClient()
    db = client["testdb"]
    collection = db[mongoConst.LABELED_EVENT_COLLECTION]
    mock_wsMongo = MagicMock()
    mock_wsMongo.collection.return_value = collection
    return mock_wsMongo


@pytest.fixture(autouse=True)
def mock_globals():
    """gオブジェクトをモックするフィクスチャ"""
    global g
    with patch('libs.duplicate_check.g', new=g):
        yield


def test_duplicate_check_no_settings(mock_db, mock_mongo):
    """
    重複排除設定がない場合のテスト
    duplicate_checkで登録処理されないことを確認

    """
    mock_db.table_select.return_value = []
    labeled_event_list = [
        {
            "event": {
                "file": {},
                "parameter": {},
                "_exastro_oase_event_id": 1754629084041401
            },
            "labels": {
                "_exastro_event_collection_settings_id": "5f6c522f-d87e-4dc2-84a3-7f23ed71da8b",
                "_exastro_fetched_time": 1754629083,
                "_exastro_end_time": 1754629093,
                "_exastro_type": "event",
                "_exastro_checked": "0",
                "_exastro_evaluated": "0",
                "_exastro_undetected": "1",
                "_exastro_timeout": "0",
                "_exastro_agent_name": "Unknown",
                "_exastro_agent_version": "Unknown",
                "_exastro_not_available": "EVENT_ID_KEY not found"
            },
            "exastro_created_at": "2025-08-08T04:58:04.149676+00:00",
            "_id": None
        },
        {
            "event": {
                "file": {},
                "parameter": {},
                "_exastro_oase_event_id": 1754629084041402
            },
            "labels": {
                "_exastro_event_collection_settings_id": "5f6c522f-d87e-4dc2-84a3-7f23ed71da8b",
                "_exastro_fetched_time": 1754629083 + 1,
                "_exastro_end_time": 1754629093 + 1,
                "_exastro_type": "event",
                "_exastro_checked": "0",
                "_exastro_evaluated": "0",
                "_exastro_undetected": "1",
                "_exastro_timeout": "0",
                "_exastro_agent_name": "Unknown",
                "_exastro_agent_version": "Unknown",
                "_exastro_not_available": "EVENT_ID_KEY not found"
            },
            "exastro_created_at": "2025-08-08T04:58:04.149676+00:00",
            "_id": None
        }
    ]

    result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list)

    # 重複排除のレコードなしの場合は、Falseで終了
    assert g.applogger.info.called is True
    assert result is False
    assert len(recieve_notification_list) == 0
    assert len(duplicate_notification_list) == 0


def test_duplicate_check_with_settings_bulk_write(mock_db, mock_mongo):
    """
    重複排除データのラベルキーが削除されたイレギュラーケースの確認 ならびに
    重複排除設定が存在しない場合のテスト
    新規挿入(bulk_write)されることを確認
    """
    mock_db.table_select.return_value = [
        {
            "DEDUPLICATION_SETTING_ID": "dup1",
            "DEDUPLICATION_SETTING_NAME": "test_dup_rule",
            "SETTING_PRIORITY": 1,
            "EVENT_SOURCE_REDUNDANCY_GROUP": '{"id": ["ecs1"]}',
            "CONDITION_EXPRESSION_ID": "1",  # ラベルが「一致」
            "CONDITION_LABEL_KEY_IDS": '{"id": ["labelkey1"]}'
        }
    ]

    labeled_event_list = [
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs1",
                "_exastro_agent_name": "agentA",
                "labelkey1_name": "value1"
            },
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1"},
            "exastro_created_at": 1672531200,
            "labels._exastro_end_time": 9999999999
        }
    ]

    # 重複排除データのラベルキーが削除されたイレギュラーケースの確認
    with patch('libs.duplicate_check.LABEL_KEY_MAP', {}):
        duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list)

    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 1
    doc = collection.find_one({"labels.labelkey1_name": "value1"})
    assert doc is not None
    assert doc["exastro_duplicate_check"] == ["ecs1_agentA"]


def test_duplicate_check_with_settings_insert(mock_db, mock_mongo):
    """
    重複排除設定に一致するドキュメントがない場合のテスト
    新規挿入(find_one_and_update)されることを確認
    """
    mock_db.table_select.return_value = [
        {
            "DEDUPLICATION_SETTING_ID": "dup1",
            "DEDUPLICATION_SETTING_NAME": "test_dup_rule",
            "SETTING_PRIORITY": 1,
            "EVENT_SOURCE_REDUNDANCY_GROUP": '{"id": ["ecs1"]}',
            "CONDITION_EXPRESSION_ID": "1",  # ラベルが「一致」
            "CONDITION_LABEL_KEY_IDS": '{"id": ["labelkey1"]}'
        }
    ]

    labeled_event_list = [
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs1",
                "_exastro_agent_name": "agentA",
                "labelkey1_name": "value1"
            },
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1"},
            "exastro_created_at": 1672531200,
            "labels._exastro_end_time": 9999999999
        }
    ]

    # 新規イベントにおける挿入確認
    with patch('libs.duplicate_check.LABEL_KEY_MAP', {"labelkey1": {"LABEL_KEY_NAME": "labelkey1_name"}}):
        duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list)

    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 1
    doc = collection.find_one({"labels.labelkey1_name": "value1"})
    assert doc is not None
    assert doc["exastro_duplicate_check"] == ["ecs1_agentA"]


def test_duplicate_check_with_settings_update(mock_db, mock_mongo):
    """
    既存のドキュメントに一致する場合のテスト
    更新(find_one_and_update)されることを確認
    """
    mock_db.table_select.return_value = [
        {
            "DEDUPLICATION_SETTING_ID": "dup1",
            "DEDUPLICATION_SETTING_NAME": "test_dup_rule",
            "SETTING_PRIORITY": 1,
            "EVENT_SOURCE_REDUNDANCY_GROUP": '{"id": ["ecs3"]}',
            "CONDITION_EXPRESSION_ID": "1",  # 一致を許容
            # "CONDITION_EXPRESSION_ID": "2",  # 無視（不一致を許容）
            "CONDITION_LABEL_KEY_IDS": '{"id": ["labelkey1"]}'
        },
        {
            "DEDUPLICATION_SETTING_ID": "dup2",
            "DEDUPLICATION_SETTING_NAME": "test_dup_rule2",
            "SETTING_PRIORITY": 2,
            "EVENT_SOURCE_REDUNDANCY_GROUP": '{"id": ["ecs1", "ecs2"]}',
            "CONDITION_EXPRESSION_ID": "2",  # 無視（不一致を許容）
            "CONDITION_LABEL_KEY_IDS": '{"id": ["labelkey2"]}'
        }
    ]

    # 既存のドキュメントを挿入
    existing_event = {
        "labels": {
            "_exastro_event_collection_settings_id": "ecs3",
            "_exastro_agent_name": "agentA1",
            "labelkey1_name": "Disk Full",
            "labelkey2_name": "value2",
            "_exastro_end_time": 9999999999
        },
        "exastro_created_at": 1672531000,
        "exastro_label_key_inputs": {"labelkey1_name": "labelkey1"},
        "exastro_duplicate_check": ["ecs3_agentA1"]
    }
    mock_mongo.collection.return_value.insert_one(existing_event)

    labeled_event_list = [
        # 対象2台 x agent2台 相当試験
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs1",
                "_exastro_agent_name": "agentA3",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672031204,
            },
            "exastro_created_at": 1672031204,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs1",
                "_exastro_agent_name": "agentA4",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672031205,
            },
            "exastro_created_at": 1672031205,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs2",
                "_exastro_agent_name": "agentA3",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672031204,
            },
            "exastro_created_at": 1672031204,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs2",
                "_exastro_agent_name": "agentA4",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672031205,
            },
            "exastro_created_at": 1672031205,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        # 対象1台 x agent2台 + 先行情報あり 相当試験
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs3",
                "_exastro_agent_name": "agentA1",
                "labelkey1_name": "Disk Full",
                "labelkey2_name": "value2",
                "_exastro_end_time": 2672531201,
            },
            "exastro_created_at": 1672531201,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs3",
                "_exastro_agent_name": "agentA2",
                "labelkey1_name": "Disk Full",
                "labelkey2_name": "value2",
                "_exastro_end_time": 2672531202,
            },
            "exastro_created_at": 1672531202,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs3",
                "_exastro_agent_name": "agentA2",
                "labelkey1_name": "Disk Full",
                "labelkey2_name": "value2",
                "_exastro_end_time": 2672531203,
            },
            "exastro_created_at": 1672531203,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1"}
        },
        # 重複排除設定なし 相当試験
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs4",
                "_exastro_agent_name": "agentA5",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value2",
                "_exastro_end_time": 2672531206,
            },
            "exastro_created_at": 1672531206,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1"}
        },
        # 対象2台 x agent2台 相当試験２巡目順番違い
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs2",
                "_exastro_agent_name": "agentA3",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672131213,
            },
            "exastro_created_at": 1672131213,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs1",
                "_exastro_agent_name": "agentA4",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672131214,
            },
            "exastro_created_at": 1672131214,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs1",
                "_exastro_agent_name": "agentA3",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672131215,
            },
            "exastro_created_at": 1672131215,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs2",
                "_exastro_agent_name": "agentA4",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672131216,
            },
            "exastro_created_at": 1672131216,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        # 対象2台 x agent2台 相当試験３巡目対象１つの来ないパターン
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs2",
                "_exastro_agent_name": "agentA4",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672231220,
            },
            "exastro_created_at": 1672231220,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs1",
                "_exastro_agent_name": "agentA3",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672231221,
            },
            "exastro_created_at": 1672231221,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs1",
                "_exastro_agent_name": "agentA4",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672231222,
            },
            "exastro_created_at": 1672231222,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        # 対象2台 x agent2台 相当試験４巡目メッセージ違いパターン
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs1",
                "_exastro_agent_name": "agentA4",
                "labelkey1_name": "Httpd Down",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672231230,
            },
            "exastro_created_at": 1672231230,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs1",
                "_exastro_agent_name": "agentA3",
                "labelkey1_name": "Httpd Down",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672231231,
            },
            "exastro_created_at": 1672231231,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs2",
                "_exastro_agent_name": "agentA3",
                "labelkey1_name": "Httpd Down",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672231232,
            },
            "exastro_created_at": 1672231232,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs2",
                "_exastro_agent_name": "agentA4",
                "labelkey1_name": "Httpd Down",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672231233,
            },
            "exastro_created_at": 16722312233,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
    ]

    with patch('libs.duplicate_check.LABEL_KEY_MAP', {"labelkey1": {"LABEL_KEY_NAME": "labelkey1_name"}, "labelkey2": {"LABEL_KEY_NAME": "labelkey2_name"}}):
        duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list)

    collection = mock_mongo.collection.return_value
    # 挿入は1件のみ、残りは更新されたことを確認

    print("ecs1------------------------------")
    filter = {"labels._exastro_event_collection_settings_id": "ecs1"}
    find_doc = collection.find(filter)
    for doc in find_doc:
        print(doc)
    assert collection.count_documents(filter) == 4

    print("ecs2------------------------------")
    filter = {"labels._exastro_event_collection_settings_id": "ecs2"}
    find_doc = collection.find(filter)
    for doc in find_doc:
        print(doc)
    assert collection.count_documents(filter) == 0

    print("ecs3------------------------------")
    filter = {"labels._exastro_event_collection_settings_id": "ecs3"}
    find_doc = collection.find(filter)
    for doc in find_doc:
        print(doc)
    assert collection.count_documents(filter) == 2

    print("ecs4------------------------------")
    filter = {"labels._exastro_event_collection_settings_id": "ecs4"}
    find_doc = collection.find(filter)
    for doc in find_doc:
        print(doc)
    assert collection.count_documents(filter) == 1

    doc = collection.find_one({"labels._exastro_event_collection_settings_id": "ecs1", "labels.labelkey1_name": "Httpd Down"})
    assert doc is not None
    # exastro_duplicate_check配列が更新されていることを確認
    assert len(doc["exastro_duplicate_check"]) == 4


def test_process_event_group_upsert_insert(mock_mongo):
    """_process_event_group関数での新規挿入（upsert=True, matchなし）のテスト"""
    event_group = [
        {
            "event": {
                "labels": {
                    "_exastro_event_collection_settings_id": "ecs_01",
                    "_exastro_agent_name": "agent_01",
                    "_exastro_end_time": 9999999999,
                    "test_label_key": "value_a"
                },
                "exastro_label_key_inputs": {"test_label_key": "lk_01"}
            },
            "conditions_list": [
                ("dup_01", {"labels.test_label_key": "value_a"})
            ],
            "duplicate_check_key": "ecs_01_agent_01"
        }
    ]

    mock_queue = queue.Queue()
    mock_mongo.find_one_and_update.return_value = None  # マッチするドキュメントがない場合を想定
    with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', new={"ecs_01": {}}):
        with patch('libs.duplicate_check.is_new_event', new=MagicMock(return_value=True)):
            duplicate_check._process_event_group(mock_mongo, event_group, mock_queue)

    mock_mongo.find_one_and_update.assert_called_once()
    assert mock_queue.get() == {"insert_num": 1, "update_num": 0, "duplicate_notification_list": [], "recieve_notification_list": [None]}


def test_process_event_group_upsert_update(mock_mongo):
    """_process_event_group関数での更新（upsert=True, matchあり）のテスト"""
    event_group = [
        {
            "event": {
                "labels": {
                    "_exastro_event_collection_settings_id": "ecs_01",
                    "_exastro_agent_name": "agent_01",
                    "_exastro_end_time": 9999999999,
                    "test_label_key": "value_a"
                },
                "exastro_label_key_inputs": {"test_label_key": "lk_01"}
            },
            "conditions_list": [
                ("dup_01", {"labels.test_label_key": "value_a"})
            ],
            "duplicate_check_key": "ecs_01_agent_01"
        }
    ]

    mock_queue = queue.Queue()
    mock_mongo.find_one_and_update.return_value = {"_id": "existing_id"}  # マッチするドキュメントがある場合を想定

    with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', new={"ecs_01": {}}):
        with patch('libs.duplicate_check.is_new_event', new=MagicMock(return_value=False)):
            duplicate_check._process_event_group(mock_mongo, event_group, mock_queue)

    mock_mongo.find_one_and_update.assert_called_once()
    assert mock_queue.get() == {"insert_num": 0, "update_num": 1, 'recieve_notification_list': [], 'duplicate_notification_list': []}


def test_case1(mock_db, mock_mongo):
    """
    収集先冗長構成のテストケース
        エージェント
            ita-oase-agent-03
            ita-oase-agent-04
        収集設定名
            Z3 (ita-oase-agent-03)
            Z4 (ita-oase-agent-04)
        重複排除設定
            E3_E4_match: uuidが一致する
        リクエスト数:5
        期待結果:
            イベント数:4
            重複数:2
            受信通知:6
            重複通知:2
    """
    import datetime #####

    _dtime = datetime.datetime.now()
    _ft_time = int(_dtime.timestamp()) + 5
    recieve_num = 0
    duplicate_num = 0

    # ita-oase-agent-03
    labeled_event_list_1 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c19b-56cd-7821-823c-4ce9e8782bb9',
                'service': 'httpd',
                'collection_name': 'Z3',
                'case': 'case2',
                '_exastro_oase_event_id': 1759889807000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'd76d044c-f5b6-4716-99a7-6783b67aaa7e',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-03',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case2',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'service': 'httpd',
                'value': '0199c19b-56cd-7821-823c-4ce9e8782bb9',
                'collection_name': 'Z3'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '7437ea41-6328-4bb6-9c50-0e538a91a83b',
                'uuid': '8742e141-f352-4039-ac87-206a99ac6f54',
                'service': 'a0e07c0f-6015-4645-865c-6b36eea2079e',
                'value': 'b08df589-9bf5-4321-add4-19f52795acdc',
                'collection_name': 'bafa7128-0936-411d-be7e-670fa1d59a87'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]
    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-04
    labeled_event_list_2 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c19b-549a-7397-87a8-f6d4ced05063',
                'service': 'httpd',
                'collection_name': 'Z4',
                'case': 'case2',
                '_exastro_oase_event_id': 1759889806000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'dc705845-eda1-408b-b3cf-5cf5069444d5',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-04',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'collection_name': 'Z4',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c19b-549a-7397-87a8-f6d4ced05063',
                'case': 'case2'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '58d58877-9d89-4ab6-bf7e-7a7d96453d8d',
                'collection_name': '7f4c65ba-6a53-423f-af47-2d8737ae30e9',
                'uuid': 'aad1615e-42a1-4c1a-b4a5-39ef125e4eae',
                'value': 'ac3db91c-d3cb-488f-a392-bc1f0f4bfc3f',
                'case': 'd221ebb8-15ee-459c-81d2-01884587fd61'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9'
            }
        },
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000002',
                'value': '0199c19b-549a-7397-87a8-f6d4ced05063',
                'service': 'httpd',
                'collection_name': 'Z4',
                'case': 'case2',
                '_exastro_oase_event_id': 1759889806000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'dc705845-eda1-408b-b3cf-5cf5069444d5',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-04',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'collection_name': 'Z4',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c19b-549a-7397-87a8-f6d4ced05063',
                'case': 'case2'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '58d58877-9d89-4ab6-bf7e-7a7d96453d8d',
                'collection_name': '7f4c65ba-6a53-423f-af47-2d8737ae30e9',
                'uuid': 'aad1615e-42a1-4c1a-b4a5-39ef125e4eae',
                'value': 'ac3db91c-d3cb-488f-a392-bc1f0f4bfc3f',
                'case': 'd221ebb8-15ee-459c-81d2-01884587fd61'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9'
            }
        }
    ]
    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-03
    labeled_event_list_3 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000002',
                'value': '0199c19b-56cd-7821-823c-4ce9e8782bb9',
                'service': 'httpd',
                'collection_name': 'Z3',
                'case': 'case2',
                '_exastro_oase_event_id': 1759889807000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'd76d044c-f5b6-4716-99a7-6783b67aaa7e',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-03',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case2',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'service': 'httpd',
                'value': '0199c19b-56cd-7821-823c-4ce9e8782bb9',
                'collection_name': 'Z3'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '7437ea41-6328-4bb6-9c50-0e538a91a83b',
                'uuid': '8742e141-f352-4039-ac87-206a99ac6f54',
                'service': 'a0e07c0f-6015-4645-865c-6b36eea2079e',
                'value': 'b08df589-9bf5-4321-add4-19f52795acdc',
                'collection_name': 'bafa7128-0936-411d-be7e-670fa1d59a87'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]
    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-03
    labeled_event_list_4 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000003',
                'value': '0199c19b-56cd-7821-823c-4ce9e8782bb9',
                'service': 'httpd',
                'collection_name': 'Z3',
                'case': 'case2',
                '_exastro_oase_event_id': 1759889807000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'd76d044c-f5b6-4716-99a7-6783b67aaa7e',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-03',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case2',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'service': 'httpd',
                'value': '0199c19b-56cd-7821-823c-4ce9e8782bb9',
                'collection_name': 'Z3'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '7437ea41-6328-4bb6-9c50-0e538a91a83b',
                'uuid': '8742e141-f352-4039-ac87-206a99ac6f54',
                'service': 'a0e07c0f-6015-4645-865c-6b36eea2079e',
                'value': 'b08df589-9bf5-4321-add4-19f52795acdc',
                'collection_name': 'bafa7128-0936-411d-be7e-670fa1d59a87'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]

    # ita-oase-agent-04
    labeled_event_list_5 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000003',
                'value': '0199c19b-549a-7397-87a8-f6d4ced05063',
                'service': 'httpd',
                'collection_name': 'Z4',
                'case': 'case2',
                '_exastro_oase_event_id': 1759889806000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'dc705845-eda1-408b-b3cf-5cf5069444d5',
                '_exastro_fetched_time': _ft_time, '_exastro_end_time': _ft_time, '_exastro_agent_name': 'ita-oase-agent-04',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'collection_name': 'Z4',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c19b-549a-7397-87a8-f6d4ced05063',
                'case': 'case2'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '58d58877-9d89-4ab6-bf7e-7a7d96453d8d',
                'collection_name': '7f4c65ba-6a53-423f-af47-2d8737ae30e9',
                'uuid': 'aad1615e-42a1-4c1a-b4a5-39ef125e4eae',
                'value': 'ac3db91c-d3cb-488f-a392-bc1f0f4bfc3f',
                'case': 'd221ebb8-15ee-459c-81d2-01884587fd61'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9'
            }
        }
    ]

    label_key_map = {
        '28522b7e-c90a-4ace-832d-9b747251ee8c': {
            'LABEL_KEY_ID': '28522b7e-c90a-4ace-832d-9b747251ee8c',
            'LABEL_KEY_NAME': 'ts',
            'COLOR_CODE': None, 'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 9, 11, 26, 135958),
        },
        '3c25bf29-337d-4b65-ba60-bd0c455157a2': {
            'LABEL_KEY_ID': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
            'LABEL_KEY_NAME': 'uuid',
            'COLOR_CODE': '#FFFF00',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 9, 48, 46, 816860),
        },
        '40998b57-3786-4b46-9e6b-411442818bfc': {
            'LABEL_KEY_ID': '40998b57-3786-4b46-9e6b-411442818bfc',
            'LABEL_KEY_NAME': 'service',
            'COLOR_CODE': '#FF0000',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 9, 48, 46, 809355),
        },
        '67edaf08-ca73-4712-b7fb-bea286ba550b': {
            'LABEL_KEY_ID': '67edaf08-ca73-4712-b7fb-bea286ba550b',
            'LABEL_KEY_NAME': 'collection_name',
            'COLOR_CODE': '#0000FF',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 9, 39, 17, 883735),
        },
        '8d7c0bdc-06f3-41ee-827c-a55d552f75f9': {
            'LABEL_KEY_ID': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
            'LABEL_KEY_NAME': 'case',
            'COLOR_CODE': '#00FF00',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 9, 39, 34, 676339),
        },
        'b3537a94-2152-4ac1-be58-d203bd011743': {
            'LABEL_KEY_ID': 'b3537a94-2152-4ac1-be58-d203bd011743',
            'LABEL_KEY_NAME': 'value',
            'COLOR_CODE': '#FF0000',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 9, 48, 46, 804867),
        },
        'bd5e48a1-9372-4bff-90db-d4d651f3f1cc': {
            'LABEL_KEY_ID': 'bd5e48a1-9372-4bff-90db-d4d651f3f1cc',
            'LABEL_KEY_NAME': 'ip',
            'COLOR_CODE': '#FF0000',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 17, 38, 11, 190326),
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx01': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx01',
            'LABEL_KEY_NAME': '_exastro_event_collection_settings_id',
            'COLOR_CODE': None, 'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513), 'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx02': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx02',
            'LABEL_KEY_NAME': '_exastro_fetched_time',
            'COLOR_CODE': None, 'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513), 'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx03': {
            'LABEL_KEY_NAME': '_exastro_end_time',
            'COLOR_CODE': None, 'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513), 'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx07': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx07',
            'LABEL_KEY_NAME': '_exastro_type',
            'COLOR_CODE': None, 'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513), 'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx09': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx09',
            'LABEL_KEY_NAME': '_exastro_host',
            'COLOR_CODE': None, 'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513), 'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx10': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx10',
            'LABEL_KEY_NAME': '_exastro_agent_name',
            'COLOR_CODE': None, 'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513), 'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx11': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx11',
            'LABEL_KEY_NAME': '_exastro_agent_version',
            'COLOR_CODE': None, 'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513), 'LAST_UPDATE_USER': '1'
        }
    }
    duplication_settings_map = {
        '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d': {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': ['3cd9fde9-ed6a-431f-9eb2-d963aee12a3a'], 'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'], 'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675),
        },
        '90b87686-806f-45f2-b6c7-a22a165d4164': {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': [
                'd76d044c-f5b6-4716-99a7-6783b67aaa7e',
                'dc705845-eda1-408b-b3cf-5cf5069444d5'
            ],
            'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'],
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586),
        },
        'f3407df3-d238-4419-9bda-3181651a464f': {
            'DEDUPLICATION_SETTING_ID': 'f3407df3-d238-4419-9bda-3181651a464f',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_2_match',
            'SETTING_PRIORITY': 50,
            'EVENT_SOURCE_REDUNDANCY_GROUP': [
                '0dfe9922-2387-440f-bac6-1bcc12940a36',
                '298e1dab-47de-4c74-a647-4651a275d720',
                'a41e17d2-daae-4a2d-903a-efb35d87bbbc',
                'ba493fa4-da39-4e20-8228-90c5ae71bc6d'
            ],
            'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'],
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 16, 50, 42, 419883),
        },
        '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a': {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50,
            'EVENT_SOURCE_REDUNDANCY_GROUP': [
                'b56e483a-0409-4186-b2ae-80dc970529f2',
                'cc787f28-6478-45d0-80d7-297c22fbd390'
            ],
            'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'],
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093),
        }
    }
    duplication_settings_ecs_map = {
        '3cd9fde9-ed6a-431f-9eb2-d963aee12a3a': ['9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d'],
        'd76d044c-f5b6-4716-99a7-6783b67aaa7e': ['90b87686-806f-45f2-b6c7-a22a165d4164'],
        'dc705845-eda1-408b-b3cf-5cf5069444d5': ['90b87686-806f-45f2-b6c7-a22a165d4164'],
        '0dfe9922-2387-440f-bac6-1bcc12940a36': ['f3407df3-d238-4419-9bda-3181651a464f'],
        '298e1dab-47de-4c74-a647-4651a275d720': ['f3407df3-d238-4419-9bda-3181651a464f'],
        'a41e17d2-daae-4a2d-903a-efb35d87bbbc': ['f3407df3-d238-4419-9bda-3181651a464f'],
        'ba493fa4-da39-4e20-8228-90c5ae71bc6d': ['f3407df3-d238-4419-9bda-3181651a464f'],
        'b56e483a-0409-4186-b2ae-80dc970529f2': ['9f1ec618-9de5-44dd-9dfc-c6d926c9f39a'],
        'cc787f28-6478-45d0-80d7-297c22fbd390': ['9f1ec618-9de5-44dd-9dfc-c6d926c9f39a']
    }

    # 1回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_1)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 1
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 1

    # 2回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_2)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 2
    assert len(duplicate_notification_list) == 1

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 2

    # 3回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_3)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 1
    assert len(duplicate_notification_list) == 1

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 2

    # 4回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_4)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 1
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 3

    # TTL切れ待ち
    time.sleep(15)

    # 5回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_5)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 1
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 4

    # 通知の総数確認
    assert recieve_num == 6
    assert duplicate_num == 2


def test_case2(mock_db, mock_mongo):
    """
    エージェント冗長構成のテストケース
        エージェント
            1. ita-oase-agent-01
            2. ita-oase-agent-02
        収集設定名
            Z1
        重複排除設定
            E1_match: uuidが一致する
        リクエスト数:5
        期待結果:
            イベント数:4
            重複数:0
            受信通知:4
            重複通知:0
    """
    import datetime

    _dtime = datetime.datetime.now()
    _ft_time = int(_dtime.timestamp()) + 5
    recieve_num = 0
    duplicate_num = 0

    # ita-oase-agent-01
    labeled_event_list_1 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199be06-49a9-7dda-a451-fff1c7251538',
                'service': 'httpd',
                'collection_name': 'Z1',
                'case': 'case1',
                '_exastro_oase_event_id': 1759829707000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': '3cd9fde9-ed6a-431f-9eb2-d963aee12a3a',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-01',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'value': '0199be06-49a9-7dda-a451-fff1c7251538',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'service': 'httpd',
                'case': 'case1',
                'collection_name': 'Z1'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'value': '0ca24615-f1d6-4cd2-a69a-c92c82866cd7',
                'uuid': '359277ba-39c1-4c74-805d-79dcc54f42cb',
                'service': 'a75bf573-6432-41c4-944f-2d224cfd6b2b',
                'case': 'ce1ed3af-d5c4-4eae-b4fd-432754c6d746',
                'collection_name': 'df0014bb-809a-4585-99bf-1cfacdd6ea70'
            },
            'exastro_label_key_inputs': {
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]
    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-02
    labeled_event_list_2 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199be09-aa3f-7c4a-9ff2-d6938e28a087',
                'service': 'httpd',
                'collection_name': 'Z1',
                'case': 'case1',
                '_exastro_oase_event_id': 1759829928000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': '3cd9fde9-ed6a-431f-9eb2-d963aee12a3a',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-02',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'value': '0199be09-aa3f-7c4a-9ff2-d6938e28a087',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'service': 'httpd',
                'case': 'case1',
                'collection_name': 'Z1'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'value': '0ca24615-f1d6-4cd2-a69a-c92c82866cd7',
                'uuid': '359277ba-39c1-4c74-805d-79dcc54f42cb',
                'service': 'a75bf573-6432-41c4-944f-2d224cfd6b2b',
                'case': 'ce1ed3af-d5c4-4eae-b4fd-432754c6d746',
                'collection_name': 'df0014bb-809a-4585-99bf-1cfacdd6ea70'
            },
            'exastro_label_key_inputs': {
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000002',
                'value': '0199be09-aa3f-7c4a-9ff2-d6938e28a087',
                'service': 'httpd',
                'collection_name': 'Z1',
                'case': 'case1',
                '_exastro_oase_event_id': 1759829928000002
            },
            'labels': {
                '_exastro_event_collection_settings_id': '3cd9fde9-ed6a-431f-9eb2-d963aee12a3a',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-02',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'value': '0199be09-aa3f-7c4a-9ff2-d6938e28a087',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'service': 'httpd',
                'case': 'case1',
                'collection_name': 'Z1'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'value': '0ca24615-f1d6-4cd2-a69a-c92c82866cd7',
                'uuid': '359277ba-39c1-4c74-805d-79dcc54f42cb',
                'service': 'a75bf573-6432-41c4-944f-2d224cfd6b2b',
                'case': 'ce1ed3af-d5c4-4eae-b4fd-432754c6d746',
                'collection_name': 'df0014bb-809a-4585-99bf-1cfacdd6ea70'
            },
            'exastro_label_key_inputs': {
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]
    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-01
    labeled_event_list_3 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000002',
                'value': '0199be06-49a9-7dda-a451-fff1c7251538',
                'service': 'httpd',
                'collection_name': 'Z1',
                'case': 'case1',
                '_exastro_oase_event_id': 1759829929000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': '3cd9fde9-ed6a-431f-9eb2-d963aee12a3a',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-01',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'value': '0199be06-49a9-7dda-a451-fff1c7251538',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'service': 'httpd',
                'case': 'case1',
                'collection_name': 'Z1'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'value': '0ca24615-f1d6-4cd2-a69a-c92c82866cd7',
                'uuid': '359277ba-39c1-4c74-805d-79dcc54f42cb',
                'service': 'a75bf573-6432-41c4-944f-2d224cfd6b2b',
                'case': 'ce1ed3af-d5c4-4eae-b4fd-432754c6d746',
                'collection_name': 'df0014bb-809a-4585-99bf-1cfacdd6ea70'
            },
            'exastro_label_key_inputs': {
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]
    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-01
    labeled_event_list_4 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000003',
                'value': '0199be09-aa3f-7c4a-9ff2-d6938e28a087',
                'service': 'httpd',
                'collection_name': 'Z1',
                'case': 'case1',
                '_exastro_oase_event_id': 1759829928000002
            },
            'labels': {
                '_exastro_event_collection_settings_id': '3cd9fde9-ed6a-431f-9eb2-d963aee12a3a',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-01',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'value': '0199be09-aa3f-7c4a-9ff2-d6938e28a087',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'service': 'httpd',
                'case': 'case1',
                'collection_name': 'Z1'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'value': '0ca24615-f1d6-4cd2-a69a-c92c82866cd7',
                'uuid': '359277ba-39c1-4c74-805d-79dcc54f42cb',
                'service': 'a75bf573-6432-41c4-944f-2d224cfd6b2b',
                'case': 'ce1ed3af-d5c4-4eae-b4fd-432754c6d746',
                'collection_name': 'df0014bb-809a-4585-99bf-1cfacdd6ea70'
            },
            'exastro_label_key_inputs': {
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]

    # ita-oase-agent-02
    labeled_event_list_5 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000003',
                'value': '0199be06-49a9-7dda-a451-fff1c7251538',
                'service': 'httpd',
                'collection_name': 'Z1',
                'case': 'case1',
                '_exastro_oase_event_id': 1759829707000002
            },
            'labels': {
                '_exastro_event_collection_settings_id': '3cd9fde9-ed6a-431f-9eb2-d963aee12a3a',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-02',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'value': '0199be06-49a9-7dda-a451-fff1c7251538',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'service': 'httpd',
                'case': 'case1',
                'collection_name': 'Z1'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'value': '0ca24615-f1d6-4cd2-a69a-c92c82866cd7',
                'uuid': '359277ba-39c1-4c74-805d-79dcc54f42cb',
                'service': 'a75bf573-6432-41c4-944f-2d224cfd6b2b',
                'case': 'ce1ed3af-d5c4-4eae-b4fd-432754c6d746',
                'collection_name': 'df0014bb-809a-4585-99bf-1cfacdd6ea70'
            },
            'exastro_label_key_inputs': {
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]

    label_key_map = {
        '28522b7e-c90a-4ace-832d-9b747251ee8c': {
            'LABEL_KEY_ID': '28522b7e-c90a-4ace-832d-9b747251ee8c',
            'LABEL_KEY_NAME': 'ts',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 9, 11, 26, 135958),
        },
        '3c25bf29-337d-4b65-ba60-bd0c455157a2': {
            'LABEL_KEY_ID': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
            'LABEL_KEY_NAME': 'uuid',
            'COLOR_CODE': '#FFFF00',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 9, 48, 46, 816860)
        },
        '40998b57-3786-4b46-9e6b-411442818bfc': {
            'LABEL_KEY_ID': '40998b57-3786-4b46-9e6b-411442818bfc',
            'LABEL_KEY_NAME': 'service',
            'COLOR_CODE': '#FF0000',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 9, 48, 46, 809355)
        },
        '67edaf08-ca73-4712-b7fb-bea286ba550b': {
            'LABEL_KEY_ID': '67edaf08-ca73-4712-b7fb-bea286ba550b',
            'LABEL_KEY_NAME': 'collection_name',
            'COLOR_CODE': '#0000FF',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 9, 39, 17, 883735)
        },
        '8d7c0bdc-06f3-41ee-827c-a55d552f75f9': {
            'LABEL_KEY_ID': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
            'LABEL_KEY_NAME': 'case',
            'COLOR_CODE': '#00FF00',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 9, 39, 34, 676339)
        },
        'b3537a94-2152-4ac1-be58-d203bd011743': {
            'LABEL_KEY_ID': 'b3537a94-2152-4ac1-be58-d203bd011743',
            'LABEL_KEY_NAME': 'value',
            'COLOR_CODE': '#FF0000',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 9, 48, 46, 804867)
        },
        'bd5e48a1-9372-4bff-90db-d4d651f3f1cc': {
            'LABEL_KEY_ID': 'bd5e48a1-9372-4bff-90db-d4d651f3f1cc',
            'LABEL_KEY_NAME': 'ip',
            'COLOR_CODE': '#FF0000',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 17, 38, 11, 190326)
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx01': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx01',
            'LABEL_KEY_NAME': '_exastro_event_collection_settings_id',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx02': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx02',
            'LABEL_KEY_NAME': '_exastro_fetched_time',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx03': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx03',
            'LABEL_KEY_NAME': '_exastro_end_time',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx07': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx07',
            'LABEL_KEY_NAME': '_exastro_type',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx09': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx09',
            'LABEL_KEY_NAME': '_exastro_host',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx10': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx10',
            'LABEL_KEY_NAME': '_exastro_agent_name',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx11': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx11',
            'LABEL_KEY_NAME': '_exastro_agent_version',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        }
    }
    duplication_settings_map = {
        '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d': {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50,
            'EVENT_SOURCE_REDUNDANCY_GROUP': ['3cd9fde9-ed6a-431f-9eb2-d963aee12a3a'],
            'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'],
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675)
        },
        '90b87686-806f-45f2-b6c7-a22a165d4164': {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50,
            'EVENT_SOURCE_REDUNDANCY_GROUP': [
                'd76d044c-f5b6-4716-99a7-6783b67aaa7e',
                'dc705845-eda1-408b-b3cf-5cf5069444d5'
            ],
            'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'],
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586)
        },
        'f3407df3-d238-4419-9bda-3181651a464f': {
            'DEDUPLICATION_SETTING_ID': 'f3407df3-d238-4419-9bda-3181651a464f',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_2_match',
            'SETTING_PRIORITY': 50,
            'EVENT_SOURCE_REDUNDANCY_GROUP': [
                '0dfe9922-2387-440f-bac6-1bcc12940a36',
                '298e1dab-47de-4c74-a647-4651a275d720',
                'a41e17d2-daae-4a2d-903a-efb35d87bbbc',
                'ba493fa4-da39-4e20-8228-90c5ae71bc6d'
            ],
            'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'],
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 16, 50, 42, 419883),
        },
        '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a': {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': [
                'b56e483a-0409-4186-b2ae-80dc970529f2',
                'cc787f28-6478-45d0-80d7-297c22fbd390'
            ],
            'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'],
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093),
        }
    }
    duplication_settings_ecs_map = {
        '3cd9fde9-ed6a-431f-9eb2-d963aee12a3a': ['9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d'],
        'd76d044c-f5b6-4716-99a7-6783b67aaa7e': ['90b87686-806f-45f2-b6c7-a22a165d4164'],
        'dc705845-eda1-408b-b3cf-5cf5069444d5': ['90b87686-806f-45f2-b6c7-a22a165d4164'],
        '0dfe9922-2387-440f-bac6-1bcc12940a36': ['f3407df3-d238-4419-9bda-3181651a464f'],
        '298e1dab-47de-4c74-a647-4651a275d720': ['f3407df3-d238-4419-9bda-3181651a464f'],
        'a41e17d2-daae-4a2d-903a-efb35d87bbbc': ['f3407df3-d238-4419-9bda-3181651a464f'],
        'ba493fa4-da39-4e20-8228-90c5ae71bc6d': ['f3407df3-d238-4419-9bda-3181651a464f'],
        'b56e483a-0409-4186-b2ae-80dc970529f2': ['9f1ec618-9de5-44dd-9dfc-c6d926c9f39a'],
        'cc787f28-6478-45d0-80d7-297c22fbd390': ['9f1ec618-9de5-44dd-9dfc-c6d926c9f39a']
    }

    # 1回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_1)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)

    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 1
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 1

    # 2回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_2)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 1
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 2

    # 3回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_3)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 0
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 2

    # 4回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_4)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 1
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 3

    # TTL切れ待ち
    time.sleep(15)

    # 5回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_5)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 1
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 4

    # 通知の総数確認
    assert recieve_num == 4
    assert duplicate_num == 0


def test_case3(mock_db, mock_mongo):
    """
    エージェント、収集先冗長構成のテストケース
        エージェント
            ita-oase-agent-05
            ita-oase-agent-06
        収集設定名
            Z5
            Z6
        重複排除設定
            E5_E6_match: uuidが一致する
        リクエスト数: 10
        期待結果:
            イベント数: 8
            重複数: 10
            受信通知: 13
            重複通知: 5
    """
    import datetime

    _dtime = datetime.datetime.now()
    _ft_time = int(_dtime.timestamp()) + 5
    recieve_num = 0
    duplicate_num = 0

    # ita-oase-agent-05:
    labeled_event_list_1 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-1169-75f5-af37-21b7515f93fb',
                'service': 'httpd',
                'collection_name': 'Z5',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897391000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'b56e483a-0409-4186-b2ae-80dc970529f2',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-05',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'case': 'case3',
                'value': '0199c20f-1169-75f5-af37-21b7515f93fb',
                'collection_name': 'Z5'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '39dcee82-5ca8-40fc-9e52-45b182f9a3d7',
                'uuid': '436bf638-798d-45a1-ac6a-31f38502e997',
                'case': '47231aad-7fce-4e13-9932-048a7a2f895e',
                'value': '54397eea-b91f-4c74-b3ca-1e30d3dfc62b',
                'collection_name': '955ef4fe-3db5-4854-bbd8-f53c6fd515b8'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-15af-768d-ace9-6347342246c2',
                'service': 'httpd',
                'collection_name': 'Z6',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897392000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'cc787f28-6478-45d0-80d7-297c22fbd390',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-05',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case3',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-15af-768d-ace9-6347342246c2',
                'collection_name': 'Z6'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '28bc80e2-0147-42d0-846b-5b8d750446c1',
                'service': '2df0e854-0871-4840-8ae8-9895fb13709c',
                'uuid': '852f92d1-d519-4172-85e9-8c27f0426feb',
                'value': '91536751-2876-4e46-b048-4717d2a7ea74',
                'collection_name': 'bbcf31f0-2fd2-4387-bbe2-2f4a8daebc7b'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]

    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-06
    labeled_event_list_2 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'service': 'httpd',
                'collection_name': 'Z5',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897392000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'b56e483a-0409-4186-b2ae-80dc970529f2',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'case': 'case3',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'collection_name': 'Z5'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '39dcee82-5ca8-40fc-9e52-45b182f9a3d7',
                'uuid': '436bf638-798d-45a1-ac6a-31f38502e997',
                'case': '47231aad-7fce-4e13-9932-048a7a2f895e',
                'value': '54397eea-b91f-4c74-b3ca-1e30d3dfc62b',
                'collection_name': '955ef4fe-3db5-4854-bbd8-f53c6fd515b8'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'service': 'httpd',
                'collection_name': 'Z6',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897393000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'cc787f28-6478-45d0-80d7-297c22fbd390',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case3',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'collection_name': 'Z6'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '28bc80e2-0147-42d0-846b-5b8d750446c1',
                'service': '2df0e854-0871-4840-8ae8-9895fb13709c',
                'uuid': '852f92d1-d519-4172-85e9-8c27f0426feb',
                'value': '91536751-2876-4e46-b048-4717d2a7ea74',
                'collection_name': 'bbcf31f0-2fd2-4387-bbe2-2f4a8daebc7b'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]

    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-05/06
    labeled_event_list_3 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000002',
                'value': '0199c20f-1169-75f5-af37-21b7515f93fb',
                'service': 'httpd',
                'collection_name': 'Z5',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897391000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'b56e483a-0409-4186-b2ae-80dc970529f2',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-05',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'case': 'case3',
                'value': '0199c20f-1169-75f5-af37-21b7515f93fb',
                'collection_name': 'Z5'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '39dcee82-5ca8-40fc-9e52-45b182f9a3d7',
                'uuid': '436bf638-798d-45a1-ac6a-31f38502e997',
                'case': '47231aad-7fce-4e13-9932-048a7a2f895e',
                'value': '54397eea-b91f-4c74-b3ca-1e30d3dfc62b',
                'collection_name': '955ef4fe-3db5-4854-bbd8-f53c6fd515b8'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000002',
                'value': '0199c20f-15af-768d-ace9-6347342246c2',
                'service': 'httpd',
                'collection_name': 'Z6',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897392000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'cc787f28-6478-45d0-80d7-297c22fbd390',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-05',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case3',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-15af-768d-ace9-6347342246c2',
                'collection_name': 'Z6'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '28bc80e2-0147-42d0-846b-5b8d750446c1',
                'service': '2df0e854-0871-4840-8ae8-9895fb13709c',
                'uuid': '852f92d1-d519-4172-85e9-8c27f0426feb',
                'value': '91536751-2876-4e46-b048-4717d2a7ea74',
                'collection_name': 'bbcf31f0-2fd2-4387-bbe2-2f4a8daebc7b'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000002',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'service': 'httpd',
                'collection_name': 'Z5',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897392000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'b56e483a-0409-4186-b2ae-80dc970529f2',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'case': 'case3',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'collection_name': 'Z5'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '39dcee82-5ca8-40fc-9e52-45b182f9a3d7',
                'uuid': '436bf638-798d-45a1-ac6a-31f38502e997',
                'case': '47231aad-7fce-4e13-9932-048a7a2f895e',
                'value': '54397eea-b91f-4c74-b3ca-1e30d3dfc62b',
                'collection_name': '955ef4fe-3db5-4854-bbd8-f53c6fd515b8'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000002',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'service': 'httpd',
                'collection_name': 'Z6',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897393000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'cc787f28-6478-45d0-80d7-297c22fbd390',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case3',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'collection_name': 'Z6'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '28bc80e2-0147-42d0-846b-5b8d750446c1',
                'service': '2df0e854-0871-4840-8ae8-9895fb13709c',
                'uuid': '852f92d1-d519-4172-85e9-8c27f0426feb',
                'value': '91536751-2876-4e46-b048-4717d2a7ea74',
                'collection_name': 'bbcf31f0-2fd2-4387-bbe2-2f4a8daebc7b'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]

    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-06
    labeled_event_list_4 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000003',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'service': 'httpd',
                'collection_name': 'Z5',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897392000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'b56e483a-0409-4186-b2ae-80dc970529f2',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'case': 'case3',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'collection_name': 'Z5'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '39dcee82-5ca8-40fc-9e52-45b182f9a3d7',
                'uuid': '436bf638-798d-45a1-ac6a-31f38502e997',
                'case': '47231aad-7fce-4e13-9932-048a7a2f895e',
                'value': '54397eea-b91f-4c74-b3ca-1e30d3dfc62b',
                'collection_name': '955ef4fe-3db5-4854-bbd8-f53c6fd515b8'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000003',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'service': 'httpd',
                'collection_name': 'Z6',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897393000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'cc787f28-6478-45d0-80d7-297c22fbd390',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case3',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'collection_name': 'Z6'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '28bc80e2-0147-42d0-846b-5b8d750446c1',
                'service': '2df0e854-0871-4840-8ae8-9895fb13709c',
                'uuid': '852f92d1-d519-4172-85e9-8c27f0426feb',
                'value': '91536751-2876-4e46-b048-4717d2a7ea74',
                'collection_name': 'bbcf31f0-2fd2-4387-bbe2-2f4a8daebc7b'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]

    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-05
    labeled_event_list_5 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000003',
                'value': '0199c20f-1169-75f5-af37-21b7515f93fb',
                'service': 'httpd',
                'collection_name': 'Z5',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897391000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'b56e483a-0409-4186-b2ae-80dc970529f2',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-05',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'case': 'case3',
                'value': '0199c20f-1169-75f5-af37-21b7515f93fb',
                'collection_name': 'Z5'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '39dcee82-5ca8-40fc-9e52-45b182f9a3d7',
                'uuid': '436bf638-798d-45a1-ac6a-31f38502e997',
                'case': '47231aad-7fce-4e13-9932-048a7a2f895e',
                'value': '54397eea-b91f-4c74-b3ca-1e30d3dfc62b',
                'collection_name': '955ef4fe-3db5-4854-bbd8-f53c6fd515b8'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
    ]

    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-06
    labeled_event_list_6 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000004',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'service': 'httpd',
                'collection_name': 'Z5',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897392000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'b56e483a-0409-4186-b2ae-80dc970529f2',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'case': 'case3',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'collection_name': 'Z5'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '39dcee82-5ca8-40fc-9e52-45b182f9a3d7',
                'uuid': '436bf638-798d-45a1-ac6a-31f38502e997',
                'case': '47231aad-7fce-4e13-9932-048a7a2f895e',
                'value': '54397eea-b91f-4c74-b3ca-1e30d3dfc62b',
                'collection_name': '955ef4fe-3db5-4854-bbd8-f53c6fd515b8'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000004',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'service': 'httpd',
                'collection_name': 'Z6',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897393000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'cc787f28-6478-45d0-80d7-297c22fbd390',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case3',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'collection_name': 'Z6'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '28bc80e2-0147-42d0-846b-5b8d750446c1',
                'service': '2df0e854-0871-4840-8ae8-9895fb13709c',
                'uuid': '852f92d1-d519-4172-85e9-8c27f0426feb',
                'value': '91536751-2876-4e46-b048-4717d2a7ea74',
                'collection_name': 'bbcf31f0-2fd2-4387-bbe2-2f4a8daebc7b'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]

    _ft_time = int(_dtime.timestamp()) + 5

    # ita-oase-agent-06
    labeled_event_list_7 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000005',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'service': 'httpd',
                'collection_name': 'Z5',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897392000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'b56e483a-0409-4186-b2ae-80dc970529f2',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'case': 'case3',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'collection_name': 'Z5'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '39dcee82-5ca8-40fc-9e52-45b182f9a3d7',
                'uuid': '436bf638-798d-45a1-ac6a-31f38502e997',
                'case': '47231aad-7fce-4e13-9932-048a7a2f895e',
                'value': '54397eea-b91f-4c74-b3ca-1e30d3dfc62b',
                'collection_name': '955ef4fe-3db5-4854-bbd8-f53c6fd515b8'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000005',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'service': 'httpd',
                'collection_name': 'Z6',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897393000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'cc787f28-6478-45d0-80d7-297c22fbd390',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case3',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'collection_name': 'Z6'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '28bc80e2-0147-42d0-846b-5b8d750446c1',
                'service': '2df0e854-0871-4840-8ae8-9895fb13709c',
                'uuid': '852f92d1-d519-4172-85e9-8c27f0426feb',
                'value': '91536751-2876-4e46-b048-4717d2a7ea74',
                'collection_name': 'bbcf31f0-2fd2-4387-bbe2-2f4a8daebc7b'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000006',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'service': 'httpd',
                'collection_name': 'Z6',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897393000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'cc787f28-6478-45d0-80d7-297c22fbd390',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case3',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-17ed-7d69-90d8-93d2a32d0e9c',
                'collection_name': 'Z6'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '28bc80e2-0147-42d0-846b-5b8d750446c1',
                'service': '2df0e854-0871-4840-8ae8-9895fb13709c',
                'uuid': '852f92d1-d519-4172-85e9-8c27f0426feb',
                'value': '91536751-2876-4e46-b048-4717d2a7ea74',
                'collection_name': 'bbcf31f0-2fd2-4387-bbe2-2f4a8daebc7b'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        }
    ]

    _ft_time = int(_dtime.timestamp()) + 20

    # ita-oase-agent-05
    labeled_event_list_8 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000007',
                'value': '0199c20f-15af-768d-ace9-6347342246c2',
                'service': 'httpd',
                'collection_name': 'Z6',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897392000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'cc787f28-6478-45d0-80d7-297c22fbd390',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-05',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'case': 'case3',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'value': '0199c20f-15af-768d-ace9-6347342246c2',
                'collection_name': 'Z6'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'case': '28bc80e2-0147-42d0-846b-5b8d750446c1',
                'service': '2df0e854-0871-4840-8ae8-9895fb13709c',
                'uuid': '852f92d1-d519-4172-85e9-8c27f0426feb',
                'value': '91536751-2876-4e46-b048-4717d2a7ea74',
                'collection_name': 'bbcf31f0-2fd2-4387-bbe2-2f4a8daebc7b'
            },
            'exastro_label_key_inputs': {
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
    ]

    _ft_time = int(_dtime.timestamp()) + 100

    # ita-oase-agent-05
    labeled_event_list_9 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000007',
                'value': '0199c20f-1169-75f5-af37-21b7515f93fb',
                'service': 'httpd',
                'collection_name': 'Z5',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897391000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'b56e483a-0409-4186-b2ae-80dc970529f2',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-05',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'case': 'case3',
                'value': '0199c20f-1169-75f5-af37-21b7515f93fb',
                'collection_name': 'Z5'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '39dcee82-5ca8-40fc-9e52-45b182f9a3d7',
                'uuid': '436bf638-798d-45a1-ac6a-31f38502e997',
                'case': '47231aad-7fce-4e13-9932-048a7a2f895e',
                'value': '54397eea-b91f-4c74-b3ca-1e30d3dfc62b',
                'collection_name': '955ef4fe-3db5-4854-bbd8-f53c6fd515b8'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
    ]

    _ft_time = int(_dtime.timestamp()) + 100

    # ita-oase-agent-06
    labeled_event_list_10 = [
        {
            'event': {
                'uuid': '00000000-0000-0000-0000-000000000007',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'service': 'httpd',
                'collection_name': 'Z5',
                'case': 'case3',
                '_exastro_oase_event_id': 1759897392000001
            },
            'labels': {
                '_exastro_event_collection_settings_id': 'b56e483a-0409-4186-b2ae-80dc970529f2',
                '_exastro_fetched_time': _ft_time,
                '_exastro_end_time': _ft_time,
                '_exastro_agent_name': 'ita-oase-agent-06',
                '_exastro_agent_version': '2.7.0',
                '_exastro_type': 'event',
                '_exastro_checked': '0',
                '_exastro_evaluated': '0',
                '_exastro_undetected': '0',
                '_exastro_timeout': '0',
                'service': 'httpd',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'case': 'case3',
                'value': '0199c20f-1386-7256-940f-6b1d57996e47',
                'collection_name': 'Z5'
            },
            'exastro_created_at': _dtime,
            'exastro_labeling_settings': {
                'service': '39dcee82-5ca8-40fc-9e52-45b182f9a3d7',
                'uuid': '436bf638-798d-45a1-ac6a-31f38502e997',
                'case': '47231aad-7fce-4e13-9932-048a7a2f895e',
                'value': '54397eea-b91f-4c74-b3ca-1e30d3dfc62b',
                'collection_name': '955ef4fe-3db5-4854-bbd8-f53c6fd515b8'
            },
            'exastro_label_key_inputs': {
                'service': '40998b57-3786-4b46-9e6b-411442818bfc',
                'uuid': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
                'case': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
                'value': 'b3537a94-2152-4ac1-be58-d203bd011743',
                'collection_name': '67edaf08-ca73-4712-b7fb-bea286ba550b'
            }
        },
    ]

    label_key_map = {
        '28522b7e-c90a-4ace-832d-9b747251ee8c': {
            'LABEL_KEY_ID': '28522b7e-c90a-4ace-832d-9b747251ee8c',
            'LABEL_KEY_NAME': 'ts',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 9, 11, 26, 135958)
        },
        '3c25bf29-337d-4b65-ba60-bd0c455157a2': {
            'LABEL_KEY_ID': '3c25bf29-337d-4b65-ba60-bd0c455157a2',
            'LABEL_KEY_NAME': 'uuid',
            'COLOR_CODE': '#FFFF00',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 9, 48, 46, 816860)
        },
        '40998b57-3786-4b46-9e6b-411442818bfc': {
            'LABEL_KEY_ID': '40998b57-3786-4b46-9e6b-411442818bfc',
            'LABEL_KEY_NAME': 'service',
            'COLOR_CODE': '#FF0000',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 9, 48, 46, 809355)
        },
        '67edaf08-ca73-4712-b7fb-bea286ba550b': {
            'LABEL_KEY_ID': '67edaf08-ca73-4712-b7fb-bea286ba550b',
            'LABEL_KEY_NAME': 'collection_name',
            'COLOR_CODE': '#0000FF',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 9, 39, 17, 883735)
        },
        '8d7c0bdc-06f3-41ee-827c-a55d552f75f9': {
            'LABEL_KEY_ID': '8d7c0bdc-06f3-41ee-827c-a55d552f75f9',
            'LABEL_KEY_NAME': 'case',
            'COLOR_CODE': '#00FF00',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 9, 39, 34, 676339)
        },
        'b3537a94-2152-4ac1-be58-d203bd011743': {
            'LABEL_KEY_ID': 'b3537a94-2152-4ac1-be58-d203bd011743',
            'LABEL_KEY_NAME': 'value',
            'COLOR_CODE': '#FF0000',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 9, 48, 46, 804867)
        },
        'bd5e48a1-9372-4bff-90db-d4d651f3f1cc': {
            'LABEL_KEY_ID': 'bd5e48a1-9372-4bff-90db-d4d651f3f1cc',
            'LABEL_KEY_NAME': 'ip',
            'COLOR_CODE': '#FF0000',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 17, 38, 11, 190326)
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx01': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx01',
            'LABEL_KEY_NAME': '_exastro_event_collection_settings_id',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx02': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx02',
            'LABEL_KEY_NAME': '_exastro_fetched_time',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx03': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx03',
            'LABEL_KEY_NAME': '_exastro_end_time',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx07': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx07',
            'LABEL_KEY_NAME': '_exastro_type',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx09': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx09',
            'LABEL_KEY_NAME': '_exastro_host',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx10': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx10',
            'LABEL_KEY_NAME': '_exastro_agent_name',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        },
        'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx11': {
            'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx11',
            'LABEL_KEY_NAME': '_exastro_agent_version',
            'COLOR_CODE': None,
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 25, 11, 36, 40, 936513),
            'LAST_UPDATE_USER': '1'
        }
    }
    duplication_settings_map = {
        '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d': {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50,
            'EVENT_SOURCE_REDUNDANCY_GROUP': ['3cd9fde9-ed6a-431f-9eb2-d963aee12a3a'],
            'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'],
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675)
        },
        '90b87686-806f-45f2-b6c7-a22a165d4164': {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50,
            'EVENT_SOURCE_REDUNDANCY_GROUP': [
                'd76d044c-f5b6-4716-99a7-6783b67aaa7e',
                'dc705845-eda1-408b-b3cf-5cf5069444d5'
            ],
            'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'],
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586)
        },
        'f3407df3-d238-4419-9bda-3181651a464f': {
            'DEDUPLICATION_SETTING_ID': 'f3407df3-d238-4419-9bda-3181651a464f',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_2_match',
            'SETTING_PRIORITY': 50,
            'EVENT_SOURCE_REDUNDANCY_GROUP': [
                '0dfe9922-2387-440f-bac6-1bcc12940a36',
                '298e1dab-47de-4c74-a647-4651a275d720',
                'a41e17d2-daae-4a2d-903a-efb35d87bbbc',
                'ba493fa4-da39-4e20-8228-90c5ae71bc6d'
            ],
            'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'],
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 16, 50, 42, 419883),
        },
        '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a': {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50,
            'EVENT_SOURCE_REDUNDANCY_GROUP': [
                'b56e483a-0409-4186-b2ae-80dc970529f2',
                'cc787f28-6478-45d0-80d7-297c22fbd390'
            ],
            'CONDITION_LABEL_KEY_IDS': ['3c25bf29-337d-4b65-ba60-bd0c455157a2'],
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None,
            'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093),
        }
    }
    duplication_settings_ecs_map = {
        '3cd9fde9-ed6a-431f-9eb2-d963aee12a3a': ['9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d'],
        'd76d044c-f5b6-4716-99a7-6783b67aaa7e': ['90b87686-806f-45f2-b6c7-a22a165d4164'],
        'dc705845-eda1-408b-b3cf-5cf5069444d5': ['90b87686-806f-45f2-b6c7-a22a165d4164'],
        '0dfe9922-2387-440f-bac6-1bcc12940a36': ['f3407df3-d238-4419-9bda-3181651a464f'],
        '298e1dab-47de-4c74-a647-4651a275d720': ['f3407df3-d238-4419-9bda-3181651a464f'],
        'a41e17d2-daae-4a2d-903a-efb35d87bbbc': ['f3407df3-d238-4419-9bda-3181651a464f'],
        'ba493fa4-da39-4e20-8228-90c5ae71bc6d': ['f3407df3-d238-4419-9bda-3181651a464f'],
        'b56e483a-0409-4186-b2ae-80dc970529f2': ['9f1ec618-9de5-44dd-9dfc-c6d926c9f39a'],
        'cc787f28-6478-45d0-80d7-297c22fbd390': ['9f1ec618-9de5-44dd-9dfc-c6d926c9f39a']
    }

    # 1回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_1)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 2
    assert len(duplicate_notification_list) == 1

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 1

    # 2回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_2)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 0
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 1

    # 3回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_3)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 2
    assert len(duplicate_notification_list) == 1

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 2

    # 4回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_4)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 2
    assert len(duplicate_notification_list) == 1

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 3

    # 5回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_5)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 0
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 3

    # 6回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_6)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 2
    assert len(duplicate_notification_list) == 1

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 4

    # 7回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_7)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 3
    assert len(duplicate_notification_list) == 1

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 6

    # TTL切れ待ち
    time.sleep(15)

    # 8回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_8)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 1
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 7

    # TTL切れ待ち
    time.sleep(15)

    # 9回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_9)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 1
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 8

    # 10回目登録
    mock_db.table_select.return_value = [
        {
            'DEDUPLICATION_SETTING_ID': '9ca2fb77-7e00-442f-8d27-f9bf1e3f9f2d',
            'DEDUPLICATION_SETTING_NAME': 'E1_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["3cd9fde9-ed6a-431f-9eb2-d963aee12a3a"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 10, 55, 52, 850675), },
        {
            'DEDUPLICATION_SETTING_ID': '90b87686-806f-45f2-b6c7-a22a165d4164',
            'DEDUPLICATION_SETTING_NAME': 'E3_E4_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["d76d044c-f5b6-4716-99a7-6783b67aaa7e", "dc705845-eda1-408b-b3cf-5cf5069444d5"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 10, 15, 37, 2, 70586), },
        {
            'DEDUPLICATION_SETTING_ID': '9f1ec618-9de5-44dd-9dfc-c6d926c9f39a',
            'DEDUPLICATION_SETTING_NAME': 'E5_E6_match',
            'SETTING_PRIORITY': 50, 'EVENT_SOURCE_REDUNDANCY_GROUP': '{"id": ["b56e483a-0409-4186-b2ae-80dc970529f2", "cc787f28-6478-45d0-80d7-297c22fbd390"]}',
            'CONDITION_LABEL_KEY_IDS': '{"id": ["3c25bf29-337d-4b65-ba60-bd0c455157a2"]}',
            'CONDITION_EXPRESSION_ID': '1',
            'NOTE': None, 'DISUSE_FLAG': '0',
            'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 9, 11, 8, 36, 53, 185093), }
    ]
    with patch('libs.duplicate_check.LABEL_KEY_MAP', label_key_map):
        with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_MAP', duplication_settings_map):
            with patch('libs.duplicate_check.DEDUPLICATION_SETTINGS_ECS_MAP', duplication_settings_ecs_map):
                duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list_10)
                recieve_num += len(recieve_notification_list)
                duplicate_num += len(duplicate_notification_list)
    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 0
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 8

    # 通知の総数確認
    assert recieve_num == 13
    assert duplicate_num == 5


def test_case4_1(mock_db, mock_mongo):
    """
    重複排除設定無し
    duplicate_checkで登録処理されないことを確認
    """
    mock_db.table_select.return_value = [
    ]

    labeled_event_list = [
        # 対象2台 x agent2台 相当試験
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs1",
                "_exastro_agent_name": "agentA3",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672031204,
            },
            "exastro_created_at": 1672031204,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs2",
                "_exastro_agent_name": "agentA3",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672031204,
            },
            "exastro_created_at": 1672031204,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecs3",
                "_exastro_agent_name": "agentA1",
                "labelkey1_name": "Disk Full",
                "labelkey2_name": "value2",
                "_exastro_end_time": 2672531201,
            },
            "exastro_created_at": 1672531201,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1"}
        }
    ]

    with patch('libs.duplicate_check.LABEL_KEY_MAP', {"labelkey1": {"LABEL_KEY_NAME": "labelkey1_name"}, "labelkey2": {"LABEL_KEY_NAME": "labelkey2_name"}}):
        duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list)

    # return値確認
    assert duplicate_check_result is False
    assert len(recieve_notification_list) == 0
    assert len(duplicate_notification_list) == 0


def test_case4_2(mock_db, mock_mongo):
    """
    重複排除設定有り: 該当無し

    """
    recieve_num = 0
    duplicate_num = 0
    mock_db.table_select.return_value = [
        {
            "DEDUPLICATION_SETTING_ID": "no_dup1",
            "DEDUPLICATION_SETTING_NAME": "no_test_dup_rule",
            "SETTING_PRIORITY": 1,
            "EVENT_SOURCE_REDUNDANCY_GROUP": '{"id": ["ecs3"]}',
            "CONDITION_EXPRESSION_ID": "1",  # 一致を許容
            # "CONDITION_EXPRESSION_ID": "2",  # 無視（不一致を許容）
            "CONDITION_LABEL_KEY_IDS": '{"id": ["no_labelkey1"]}'
        }
    ]

    labeled_event_list = [
        # 対象2台 x agent2台 相当試験
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecsA",
                "_exastro_agent_name": "agentA1",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672031204,
            },
            "exastro_created_at": 1672031204,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecsB",
                "_exastro_agent_name": "agentA2",
                "labelkey1_name": "CPU High",
                "labelkey2_name": "value1",
                "_exastro_end_time": 2672031204,
            },
            "exastro_created_at": 1672031204,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1", "labelkey2_name": "labelkey2"}
        },
        {
            "labels": {
                "_exastro_event_collection_settings_id": "ecsC",
                "_exastro_agent_name": "agentA3",
                "labelkey1_name": "Disk Full",
                "labelkey2_name": "value2",
                "_exastro_end_time": 2672531201,
            },
            "exastro_created_at": 1672531201,
            "exastro_label_key_inputs": {"labelkey1_name": "labelkey1"}
        }
    ]

    with patch('libs.duplicate_check.LABEL_KEY_MAP', {"labelkey1": {"LABEL_KEY_NAME": "labelkey1_name"}, "labelkey2": {"LABEL_KEY_NAME": "labelkey2_name"}}):
        duplicate_check_result, recieve_notification_list, duplicate_notification_list = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list)
        recieve_num += len(recieve_notification_list)
        duplicate_num += len(duplicate_notification_list)

    # return値確認
    assert duplicate_check_result is True
    assert len(recieve_notification_list) == 3
    assert len(duplicate_notification_list) == 0

    # mongoDB確認
    collection = mock_mongo.collection.return_value
    assert collection.count_documents({}) == 3

    # 通知の総数確認
    assert recieve_num == 3
    assert duplicate_num == 0
