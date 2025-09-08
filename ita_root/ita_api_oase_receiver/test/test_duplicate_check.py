import pytest
from unittest.mock import MagicMock, patch
import mongomock
import queue

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
    全イベントが新規挿入されることを確認
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
                "_exastro_event_collection_settings_id": "5f6c522f-d87e-4dc2-84a3-7f23ed71da8c",
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

    result = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list)

    # 重複排除のレコードなしの場合は、Falseで終了
    assert g.applogger.info.called is True
    assert result is False

    # result = duplicate_check.duplicate_check(mock_db, mock_mongo, labeled_event_list)

    # # データベースに2件のドキュメントが挿入されたことを確認
    # collection = mock_mongo.collection.return_value
    # assert collection.count_documents({}) == 2
    
    # doc1 = collection.find_one({"labels._exastro_event_collection_settings_id": "ecs1"})
    # assert "exastro_dupulicate_check" in doc1
    # assert doc1["exastro_dupulicate_check"] == ["ecs1_agentA"]


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
    assert doc["exastro_dupulicate_check"] == ["ecs1_agentA"]


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
    assert doc["exastro_dupulicate_check"] == ["ecs1_agentA"]


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
        "exastro_dupulicate_check": ["ecs3_agentA1"]
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
    # exastro_dupulicate_check配列が更新されていることを確認
    assert len(doc["exastro_dupulicate_check"]) == 4


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
            "dupulicate_check_key": "ecs_01_agent_01"
        }
    ]

    mock_queue = queue.Queue()
    mock_mongo.find_one_and_update.return_value = None  # マッチするドキュメントがない場合を想定

    duplicate_check._process_event_group(mock_mongo, event_group, mock_queue)

    mock_mongo.find_one_and_update.assert_called_once()
    assert mock_queue.get() == {"insert_num": 1, "update_num": 0}


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
            "dupulicate_check_key": "ecs_01_agent_01"
        }
    ]

    mock_queue = queue.Queue()
    mock_mongo.find_one_and_update.return_value = {"_id": "existing_id"}  # マッチするドキュメントがある場合を想定

    duplicate_check._process_event_group(mock_mongo, event_group, mock_queue)

    mock_mongo.find_one_and_update.assert_called_once()
    assert mock_queue.get() == {"insert_num": 0, "update_num": 1}
