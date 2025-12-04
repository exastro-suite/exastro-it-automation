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
import os
from unittest.mock import MagicMock
from flask import Flask
from pymongo import InsertOne

from controllers.oase_controller import post_events


"""
    test_post_events_success: 正常系
    test_post_events_maintenance_mode: 異常系(メンテナンス中)
    test_post_events_permission_error: 異常系(権限なし)
    test_post_events_invalid_settings_name: 異常系(不正なイベント設定名)
    test_post_events_disused_settings: 異常系(イベント設定が廃止)
"""


# テスト用のダミークラスと定数を定義
class DummyAppException(Exception):
    def __init__(self, status_code, log_msg_args, api_msg_args):
        self.status_code = status_code
        self.log_msg_args = log_msg_args
        self.api_msg_args = api_msg_args
        super().__init__(f"AppException: {status_code}")


class DummyOaseConst:
    DF_AGENT_NAME = "undefined_agent_name"
    DF_AGENT_VERSION = "undefined_agent_version"
    T_OASE_EVENT_COLLECTION_SETTINGS = "T_OASE_EVENT_COLLECTION_SETTINGS"
    T_OASE_EVENT_COLLECTION_PROGRESS = "T_OASE_EVENT_COLLECTION_PROGRESS"


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    yield app


# bodyのテンプレート
def get_valid_body():
    return {
        "events": [
            {
                "event": [
                    {
                        "parameter": {
                            "host_name": "localhost",
                            "hw_device_type": "SV",
                            "managed_system_item_number": "1"
                        }
                    }
                ],
                "fetched_time": 1754609518,
                "event_collection_settings_name": "test_name",
                "agent": {
                    "name": "oase_ag_001",
                    "version": "2.7.0"
                }
            }
        ]
    }


class TestPostEvents:
    # クラスのセットアップメソッド
    def setup_class(self):
        self.body = get_valid_body()
        self.organization_id = "org1"
        self.workspace_id = "ws1"
        os.environ['ORGANIZATION_ID'] = 'org1'
        os.environ['NEW_KEY'] = 'test'

    @pytest.fixture(autouse=True)
    def _setup_mocks(self, mocker, monkeypatch):
        """
        各テスト実行前に依存関係をモックする
        """
        # gオブジェクトの属性をモック
        mock_g = MagicMock()
        mock_g.maintenance_mode.get.return_value = '0'
        mock_g.appmsg.get_log_message.return_value = "dummy log message"
        mock_g.dbConnectError = False
        mock_g.applogger = MagicMock()

        # gにアクセスするすべてのモジュールをパッチする
        # `post_events`がgをインポートしているモジュール
        mocker.patch('controllers.oase_controller.g', new=mock_g)
        # エラーログから特定されたgにアクセスしているモジュール
        mocker.patch('common_libs.api.util.g', new=mock_g)

        # その他の依存関係をモック
        self.mock_db_ws = MagicMock()
        self.mock_mongo_ws = MagicMock()
        mocker.patch('common_libs.common.exception.AppException', side_effect=DummyAppException)
        mocker.patch('common_libs.oase.const.oaseConst', new=DummyOaseConst)
        mocker.patch('libs.label_event.label_event')
        mocker.patch('os.getenv', return_value="72")
        mocker.patch('datetime.datetime')

        mocker.patch('common_libs.common.dbconnect.dbdisuse_check.is_db_disuse', return_value=False)
        mocker.patch('controllers.oase_controller.DBConnectWs', return_value=self.mock_db_ws)
        mocker.patch('controllers.oase_controller.MONGOConnectWs', return_value=self.mock_mongo_ws)
        mocker.patch('controllers.oase_controller.check_menu_info', return_value=True)
        mocker.patch('controllers.oase_controller.check_auth_menu', return_value='1')
        mocker.patch('controllers.oase_controller.duplicate_check', return_value=False)
        mocker.patch('controllers.oase_controller.label_event', return_value='1')

    # 正常系のテスト ##
    def test_post_events_success(self, app, mocker):
        """正常な入力でイベントが正しく保存されることを確認する"""

        # table_selectの戻り値を設定
        self.mock_db_ws.table_select.side_effect = [
            [{
                "EVENT_COLLECTION_SETTINGS_ID": "12345",
                "EVENT_COLLECTION_SETTINGS_NAME": "test_name",
                "DISUSE_FLAG": "0",
                "TTL": "3600"
            }],
            []  # event_collection_progressは空
        ]
        # table_insertの戻り値を設定
        self.mock_db_ws.table_insert.return_value = [{
            "EVENT_COLLECTION_ID": "1",
            "EVENT_COLLECTION_SETTINGS_ID": "12345"
        }]

        self.mock_db_ws.db_transaction_start.return_value = True
        self.mock_db_ws.db_transaction_end.return_value = True
        self.mock_db_ws.table_permanent_delete.return_value = True
        self.mock_db_ws.table_count.return_value = 0

        expected_labeled_events = [
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
        expected_labeled_events_add_meta = [
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
                "_id": None,
                "exastro_duplicate_collection_settings_ids": {
                    "5f6c522f-d87e-4dc2-84a3-7f23ed71da8b": 1
                },
                "exastro_agents": {
                    "Unknown": 1
                },
                "exastro_edit_count": 1
            }
        ]

        expected_bulk_writes = []
        for labeled_event in expected_labeled_events_add_meta:
            expected_bulk_writes.append(InsertOne(labeled_event))

        mocker.patch('controllers.oase_controller.label_event', return_value=expected_labeled_events)
        mocker.patch('controllers.oase_controller.duplicate_check', return_value=(True, expected_labeled_events_add_meta, []))

        # アプリケーションコンテキストとリクエストコンテキストを両方有効にする: URLはダミー
        with app.test_request_context('/oase/api/v1/event_collection/event_list/'):
            result, status_code = post_events(self.body, self.organization_id, self.workspace_id)

        # ステータスコードの検証
        assert status_code == 200
        assert result.get("message") == "SUCCESS"
        assert result.get("data") == []
        assert result.get("result") == "000-00000"
        # bulk_write→find_one_and_update(モック)なので廃止。./test_duplicate_check.py 側のテスト

    # 正常系のテスト # 重複排除0件
    def test_post_events_success_bulk_no_deduplication_settings(self, app, mocker):
        """正常な入力でイベントが正しく保存されることを確認する"""

        # table_selectの戻り値を設定
        self.mock_db_ws.table_select.side_effect = [
            [{
                "EVENT_COLLECTION_SETTINGS_ID": "12345",
                "EVENT_COLLECTION_SETTINGS_NAME": "test_name",
                "DISUSE_FLAG": "0",
                "TTL": "3600"
            }],
            []  # event_collection_progressは空
        ]
        # table_insertの戻り値を設定
        self.mock_db_ws.table_insert.return_value = [{
            "EVENT_COLLECTION_ID": "1",
            "EVENT_COLLECTION_SETTINGS_ID": "12345"
        }]

        self.mock_db_ws.db_transaction_start.return_value = True
        self.mock_db_ws.db_transaction_end.return_value = True
        self.mock_db_ws.table_permanent_delete.return_value = True
        self.mock_db_ws.table_count.return_value = 0

        expected_labeled_events = [
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
        expected_labeled_events_add_meta = [
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
                "_id": None,
            }
        ]

        expected_bulk_writes = []
        for labeled_event in expected_labeled_events_add_meta:
            expected_bulk_writes.append(InsertOne(labeled_event))

        mocker.patch('controllers.oase_controller.label_event', return_value=expected_labeled_events)
        mocker.patch('controllers.oase_controller.duplicate_check', return_value=(False, [], []))

        # アプリケーションコンテキストとリクエストコンテキストを両方有効にする: URLはダミー
        with app.test_request_context('/oase/api/v1/event_collection/event_list/'):
            result, status_code = post_events(self.body, self.organization_id, self.workspace_id)

        # ステータスコードの検証
        assert status_code == 200
        assert result.get("message") == "SUCCESS"
        assert result.get("data") == []
        assert result.get("result") == "000-00000"

        # bulk_write の呼び出し引数を検証
        labeled_event_collection = self.mock_mongo_ws.collection.return_value
        labeled_event_collection.bulk_write.assert_called_once_with(expected_bulk_writes)
        args, kwargs = labeled_event_collection.bulk_write.call_args
        assert args == (expected_bulk_writes,)

    # 異常系のテスト ##
    def test_post_events_maintenance_mode(self, mocker, app):
        """メンテナンスモード時にAppExceptionがraiseされることを確認する"""
        # gオブジェクトの属性をモック
        mock_g = MagicMock()
        mock_g.dbConnectError = False
        mock_g.applogger = MagicMock()
        mocker.patch('controllers.oase_controller.g.maintenance_mode.get', return_value='1')

        # アプリケーションコンテキストとリクエストコンテキストを両方有効にする: URLはダミー
        with app.test_request_context('/oase/api/v1/event_collection/event_list/'):
            result, status_code = post_events(self.body, self.organization_id, self.workspace_id)

        assert status_code == 498
        assert "498-00004" in result["result"]

    def test_post_events_permission_error(self, mocker, app):
        """権限エラー時にAppExceptionがraiseされることを確認する"""

        mocker.patch('controllers.oase_controller.check_auth_menu', return_value='2')

        # アプリケーションコンテキストとリクエストコンテキストを両方有効にする: URLはダミー
        with app.test_request_context('/oase/api/v1/event_collection/event_list/'):
            result, status_code = post_events(self.body, self.organization_id, self.workspace_id)

        assert status_code == 401
        assert "401-00001" in result["result"]

    def test_post_events_invalid_settings_name(self, app):
        """event_collection_settings_nameがDBに存在しない場合にAppExceptionがraiseされることを確認する"""

        self.mock_db_ws.table_select.return_value = []

        # アプリケーションコンテキストとリクエストコンテキストを両方有効にする: URLはダミー
        with app.test_request_context('/oase/api/v1/event_collection/event_list/'):
            result, status_code = post_events(self.body, self.organization_id, self.workspace_id)

        assert status_code == 499
        assert "499-01802" in result["result"]

    def test_post_events_disused_settings(self, app, mocker):
        """収集設定が廃止済みの場合、イベントが保存されないことを確認する"""

        self.mock_db_ws.table_select.return_value = [{
            "EVENT_COLLECTION_SETTINGS_ID": "12345",
            "EVENT_COLLECTION_SETTINGS_NAME": "test_name",
            "DISUSE_FLAG": "1",  # 廃止済み
            "TTL": "3600"
        }]

        expected_labeled_events = [
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
        mocker.patch('controllers.oase_controller.label_event', return_value=expected_labeled_events)

        # アプリケーションコンテキストとリクエストコンテキストを両方有効にする: URLはダミー
        with app.test_request_context('/oase/api/v1/event_collection/event_list/'):
            result, status_code = post_events(self.body, self.organization_id, self.workspace_id)

        assert status_code == 200
        assert "000-00000" in result["result"]

        # 登録されていない事の検証
        labeled_event_collection = self.mock_mongo_ws.collection.return_value
        assert labeled_event_collection.bulk_write.called is False
