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
import datetime

from libs import label_event

"""
    mock_wsdb: mariadbのモック
    mock_wsmongo: mongodbのモック
    test_label_event_success_case1: 識別情報あり
    test_label_event_success_case2: 識別情報なし(コントローラーでUnknown付与済み)
    test_label_event_no_labeling_settings: ラベル付与設定がない
    test_label_event_empty_events: 空のイベントリストのテスト
"""


# Flaskアプリケーションのインスタンスを作成
@pytest.fixture(scope="session")
def app_context():
    from flask import Flask
    app = Flask(__name__)
    with app.app_context():
        yield


# gオブジェクトをモックするためのフィクスチャ
@pytest.fixture
def mock_g(mocker):
    """
    gオブジェクトをモックし、appmsgとapploggerを置き換える
    """
    mock_g_object = mocker.MagicMock()
    mock_g_object.appmsg = mocker.MagicMock()
    mock_g_object.applogger = mocker.MagicMock()

    # gオブジェクトを直接モックする
    mocker.patch('libs.label_event.g', new=mock_g_object)

    return mock_g_object


@pytest.fixture
def mock_wsdb(mocker):
    """
    wsDbオブジェクトのモックを作成するフィクスチャ。
    table_selectメソッドの戻り値を定義します。
    """
    wsdb_mock = mocker.MagicMock()

    # wsDb.table_selectが呼び出されるたびに異なる戻り値を返すように設定
    wsdb_mock.table_select.side_effect = [
        # 1回目の呼び出し時の戻り値
        [
            {
                'LABELING_SETTINGS_ID': '378c3edf-ec1c-4d60-a9b4-d69668f393d1',
                'LABELING_SETTINGS_NAME': 'label_1',
                'EVENT_COLLECTION_SETTINGS_ID': '84f81eff-fc46-4afe-bfde-081e76e54d6e',
                'SEARCH_KEY_NAME': '_exastro_event_collection_settings_id',
                'TYPE_ID': '1',
                'COMPARISON_METHOD_ID': '2',
                'SEARCH_VALUE_NAME': '0',
                'LABEL_KEY_ID': 'fd19c160-b35d-42f0-b661-28e45c1d27dc',
                'LABEL_VALUE_NAME': None,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 7, 16, 14, 30, 477218),
                'LAST_UPDATE_USER': '90e06bc4-1b64-457f-9d0e-1cbdd9ad4716'
            }
        ],
        # 2回目の呼び出し時の戻り値
        [
            {
                'LABEL_KEY_ID': 'fd19c160-b35d-42f0-b661-28e45c1d27dc',
                'LABEL_KEY_NAME': 'label_1',
                'COLOR_CODE': None,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 7, 16, 13, 15, 752685),
                'LAST_UPDATE_USER': '90e06bc4-1b64-457f-9d0e-1cbdd9ad4716'
            },
            {
                'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx01',
                'LABEL_KEY_NAME': '_exastro_event_collection_settings_id',
                'COLOR_CODE': None,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 5, 14, 53, 58, 240772),
                'LAST_UPDATE_USER': '1'
            },
            {
                'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx02',
                'LABEL_KEY_NAME': '_exastro_fetched_time',
                'COLOR_CODE': None,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 5, 14, 53, 58, 240772),
                'LAST_UPDATE_USER': '1'
            },
            {
                'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx03',
                'LABEL_KEY_NAME': '_exastro_end_time',
                'COLOR_CODE': None,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 5, 14, 53, 58, 240772),
                'LAST_UPDATE_USER': '1'
            },
            {
                'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx07',
                'LABEL_KEY_NAME': '_exastro_type',
                'COLOR_CODE': None,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 5, 14, 53, 58, 240772),
                'LAST_UPDATE_USER': '1'
            },
            {
                'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx09',
                'LABEL_KEY_NAME': '_exastro_host',
                'COLOR_CODE': None,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 5, 14, 53, 58, 240772),
                'LAST_UPDATE_USER': '1'
            },
            {
                'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx10',
                'LABEL_KEY_NAME': '_exastro_agent_name',
                'COLOR_CODE': None,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 5, 17, 54, 55),
                'LAST_UPDATE_USER': '1'
            }
        ]
    ]
    return wsdb_mock


@pytest.fixture
def mock_wsmongo(mocker):
    """
    wsMongoオブジェクトのモックを作成するフィクスチャ。
    """
    wsmongo_mock = mocker.MagicMock()
    return wsmongo_mock


def test_label_event_success_case1(mock_wsdb, mock_wsmongo, mock_g, app_context):
    """
    正常系：有効なイベントデータが渡された場合に、データベースに正しく挿入されることを確認するテスト。
        '_exastro_agent': {
            'name': 'oase_ag_001',
            'version': '2.7.0'
        },
    """
    _now_time = int(datetime.datetime.now().timestamp())
    events_data = [
        {
            'file': {},
            'parameter': {
                'host_name': 'localhost',
                'managed_system_item_number': '1',
            },
            '_exastro_oase_event_id': 1754555102546647,
            '_exastro_not_available': 'EVENT_ID_KEY not found',
            '_exastro_event_collection_settings_name': 'test_2',
            '_exastro_event_collection_settings_id': '5f6c522f-d87e-4dc2-84a3-7f23ed71da8b',
            '_exastro_fetched_time': int(_now_time),
            '_exastro_end_time': int(_now_time) + 10,
            '_exastro_agent_name': 'oase_ag_001',
            '_exastro_agent_version': '2.7.0',
            '_exastro_created_at': datetime.datetime(2025, 8, 7, 8, 25, 2, 689181, tzinfo=datetime.timezone.utc)
        }
    ]

    labeled_data = [
        {
            "event": {
                "file": {},
                "parameter": {
                },
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
                "_exastro_agent_name": "oase_ag_001",
                "_exastro_agent_version": "2.7.0",
                "_exastro_not_available": "EVENT_ID_KEY not found"
            },
            "exastro_created_at": "2025-08-08T04:58:04.149676+00:00",
            "_id": None
        }
    ]
    # 関数を呼び出し
    result = label_event.label_event(mock_wsdb, mock_wsmongo, events_data)

    # 期待される結果を検証
    assert mock_wsdb.table_select.call_count == 2

    # 正常終了したことを確認
    doc = result[0]["labels"]  # returnのlabel内容
    doc_eq = labeled_data[0]["labels"]  # 確認するlabel内容
    assert doc['_exastro_agent_name'] == doc_eq['_exastro_agent_name']
    assert doc['_exastro_agent_version'] == doc_eq['_exastro_agent_version']
    assert doc['_exastro_event_collection_settings_id'] == doc_eq['_exastro_event_collection_settings_id']
    assert doc['_exastro_type'] == doc_eq['_exastro_type']
    assert doc['_exastro_checked'] == doc_eq['_exastro_checked']
    assert doc['_exastro_evaluated'] == doc_eq['_exastro_evaluated']
    assert doc['_exastro_not_available'] == doc_eq['_exastro_not_available']
    assert doc['_exastro_timeout'] == doc_eq['_exastro_timeout']
    assert doc['_exastro_undetected'] == doc_eq['_exastro_undetected']


def test_label_event_success_case2(mock_wsdb, mock_wsmongo, mock_g, app_context):
    """
    正常系：有効なイベントデータが渡された場合に、データベースに正しく挿入されることを確認するテスト。
        '_exastro_agent': {
            'name': 'Unknown',
            'version': 'Unknown'
        },
    """
    _now_time = int(datetime.datetime.now().timestamp())
    events_data = [
        {
            'file': {},
            'parameter': {
                'host_name': 'localhost',
                'managed_system_item_number': '1',
            },
            '_exastro_oase_event_id': 1754555102546647,
            '_exastro_not_available': 'EVENT_ID_KEY not found',
            '_exastro_event_collection_settings_name': 'test_2',
            '_exastro_event_collection_settings_id': '5f6c522f-d87e-4dc2-84a3-7f23ed71da8b',
            '_exastro_fetched_time': int(_now_time),
            '_exastro_end_time': int(_now_time) + 10,
            '_exastro_agent_name': 'Unknown',
            '_exastro_agent_version': 'Unknown',
            '_exastro_created_at': datetime.datetime(2025, 8, 7, 8, 25, 2, 689181, tzinfo=datetime.timezone.utc)
        }
    ]

    labeled_data = [
        {
            "event": {
                "file": {},
                "parameter": {
                },
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
        }
    ]
    # 関数を呼び出し
    result = label_event.label_event(mock_wsdb, mock_wsmongo, events_data)

    # 期待される結果を検証
    assert mock_wsdb.table_select.call_count == 2

    # 正常終了したことを確認
    doc = result[0]["labels"]  # returnのlabel内容
    doc_eq = labeled_data[0]["labels"]  # 確認するlabel内容
    assert doc['_exastro_agent_name'] == doc_eq['_exastro_agent_name']
    assert doc['_exastro_agent_version'] == doc_eq['_exastro_agent_version']
    assert doc['_exastro_event_collection_settings_id'] == doc_eq['_exastro_event_collection_settings_id']
    assert doc['_exastro_type'] == doc_eq['_exastro_type']
    assert doc['_exastro_checked'] == doc_eq['_exastro_checked']
    assert doc['_exastro_evaluated'] == doc_eq['_exastro_evaluated']
    assert doc['_exastro_not_available'] == doc_eq['_exastro_not_available']
    assert doc['_exastro_timeout'] == doc_eq['_exastro_timeout']
    assert doc['_exastro_undetected'] == doc_eq['_exastro_undetected']

    # 正常終了したことを確認
    assert result is not None


def test_label_event_no_labeling_settings(mock_wsdb, mock_wsmongo, mock_g, app_context):
    """
    ラベル付与設定がない場合に、ログが出力されることを確認
    """
    # wsDb.table_selectが、1回目は空リスト、2回目はラベルキーを返すように設定
    mock_wsdb.table_select.side_effect = [
        [],  # labeling_settingsが空
        [
            {
                'LABEL_KEY_ID': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx01',
                'LABEL_KEY_NAME': '_exastro_event_collection_settings_id'
            }
        ]
    ]
    _now_time = int(datetime.datetime.now().timestamp())
    events_data = [
        {
            "file": {},
            "parameter": {},
            '_exastro_oase_event_id': 1754555102546647,
            '_exastro_not_available': 'EVENT_ID_KEY not found',
            '_exastro_event_collection_settings_name': 'test_2',
            '_exastro_event_collection_settings_id': '5f6c522f-d87e-4dc2-84a3-7f23ed71da8b',
            '_exastro_fetched_time': int(_now_time),
            '_exastro_end_time': int(_now_time) + 10,
            '_exastro_agent_name': 'Unknown',
            '_exastro_agent_version': 'Unknown',
            '_exastro_created_at': datetime.datetime(2025, 8, 7, 8, 25, 2, 689181, tzinfo=datetime.timezone.utc)
        }
    ]
    labeled_data = [
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
        }
    ]

    # 関数を実行
    result = label_event.label_event(mock_wsdb, mock_wsmongo, events_data)

    # 期待される結果を検証
    doc = result[0]["labels"]  # returnのlabel内容
    doc_eq = labeled_data[0]["labels"]  # 確認するlabel内容
    assert doc['_exastro_agent_name'] == doc_eq['_exastro_agent_name']
    assert doc['_exastro_agent_version'] == doc_eq['_exastro_agent_version']
    assert doc['_exastro_event_collection_settings_id'] == doc_eq['_exastro_event_collection_settings_id']
    assert doc['_exastro_type'] == doc_eq['_exastro_type']
    assert doc['_exastro_checked'] == doc_eq['_exastro_checked']
    assert doc['_exastro_evaluated'] == doc_eq['_exastro_evaluated']
    assert doc['_exastro_not_available'] == doc_eq['_exastro_not_available']
    assert doc['_exastro_timeout'] == doc_eq['_exastro_timeout']
    assert doc['_exastro_undetected'] == doc_eq['_exastro_undetected']

    # "ラベル付与設定を取得できませんでした" のログメッセージが呼ばれたことを確認
    mock_g.appmsg.get_log_message.assert_any_call("499-01804")
    mock_g.applogger.info.assert_called_with(mock_g.appmsg.get_log_message.return_value)


def test_label_event_empty_events(mock_wsdb, mock_wsmongo, mock_g, app_context):
    """
    ラベル付与するイベントが空の場合のテスト
    """
    mock_wsdb.table_select.side_effect = [
        [],  # labeling_settings
        [],  # label_keys
    ]
    events_data = []

    result = label_event.label_event(mock_wsdb, mock_wsmongo, events_data)

    # 戻り値が空リストであることを確認
    assert result == []

    # データベースが呼び出されていることを確認
    assert mock_wsdb.table_select.call_count == 2

    # ラベル付与設定なしとラベルマスタなしのログが出力されることを確認
    mock_g.appmsg.get_log_message.assert_any_call("499-01804")
    mock_g.appmsg.get_log_message.assert_any_call("499-01805")
    mock_g.applogger.info.assert_called()
