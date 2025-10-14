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
from unittest.mock import patch, MagicMock
from flask import Flask, g

from controllers.oase_controller import add_notification_queue
from common_libs.notification.sub_classes.oase import OASENotificationType


class TestAddNotificationQueueEdgeCases:
    """add_notification_queue関数のエッジケーステスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

        g.applogger = MagicMock()
        g.appmsg = MagicMock()
        g.applogger.info = MagicMock()
        g.applogger.warning = MagicMock()
        g.applogger.error = MagicMock()
        g.applogger.debug = MagicMock()

    def teardown_method(self):
        """各テストメソッドの後に実行されるクリーンアップ処理"""
        self.app_context.pop()

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_empty_notification_type_handling(self, mock_oase):
        """通知タイプの処理テスト"""
        wsdb_mock = MagicMock()
        notification_list = [{"event_id": "1", "message": "Event 1"}]

        expected_result = {"status": "success", "sent": 1, "failure": 0}
        mock_oase.bulksend.return_value = expected_result

        recieve_ret, duplicate_ret = add_notification_queue(wsdb_mock, notification_list, [])

        assert recieve_ret == expected_result
        assert duplicate_ret == {}
        mock_oase.bulksend.assert_called_once()

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_oase_returns_none(self, mock_oase):
        """OASE.bulksendがNoneを返す場合のテスト"""
        wsdb_mock = MagicMock()
        notification_list = [{"event_id": "1", "message": "Event 1"}]

        mock_oase.bulksend.return_value = None

        recieve_ret, duplicate_ret = add_notification_queue(wsdb_mock, notification_list, [])

        assert recieve_ret is None
        assert duplicate_ret == {}
        mock_oase.bulksend.assert_called_once()

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_none_wsdb(self, mock_oase):
        """wsdbがNoneの場合のテスト"""
        wsdb_mock = None
        notification_list = [{"event_id": "1", "message": "Event 1"}]

        expected_result = {"status": "success", "sent": 1, "failure": 0}
        mock_oase.bulksend.return_value = expected_result

        recieve_ret, duplicate_ret = add_notification_queue(wsdb_mock, notification_list, [])

        assert recieve_ret == expected_result
        assert duplicate_ret == {}
        mock_oase.bulksend.assert_called_once_with(None, notification_list, {"notification_type": OASENotificationType.NEW})

    @patch('controllers.oase_controller.OASE')
    @patch('controllers.oase_controller.stacktrace')
    def test_add_notification_queue_exception_handling(self, mock_stacktrace, mock_oase):
        """例外処理のテスト"""
        wsdb_mock = MagicMock()
        notification_list = [{"event_id": "1", "message": "Event 1"}]

        # OASE.bulksendで例外を発生させる
        oase_exception = Exception("OASE error")
        mock_oase.bulksend.side_effect = oase_exception
        mock_stacktrace.return_value = "Exception stack trace"

        recieve_ret, duplicate_ret = add_notification_queue(wsdb_mock, notification_list, [])

        assert recieve_ret == {}
        assert duplicate_ret == {}
        mock_oase.bulksend.assert_called_once()
        g.applogger.error.assert_called()

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_invalid_list_types(self, mock_oase):
        """notification_listに辞書以外の要素が含まれる場合のテスト"""
        wsdb_mock = MagicMock()
        notification_list = [
            {"event_id": "1", "message": "Valid Event"},
            "invalid_string",
            123,
            None,
            ["nested", "list"]
        ]

        expected_result = {"status": "success", "sent": 5, "failure": 0}
        mock_oase.bulksend.return_value = expected_result

        recieve_ret, duplicate_ret = add_notification_queue(wsdb_mock, notification_list, [])

        assert recieve_ret == expected_result
        assert duplicate_ret == {}
        mock_oase.bulksend.assert_called_once()

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_extremely_large_list(self, mock_oase):
        """極端に大きなnotification_listでのテスト（10,000件）"""
        wsdb_mock = MagicMock()
        notification_list = [{"event_id": f"event_{i}", "message": f"Event {i}"} for i in range(10000)]

        expected_result = {"status": "success", "sent": 10000, "failure": 0}
        mock_oase.bulksend.return_value = expected_result

        recieve_ret, duplicate_ret = add_notification_queue(wsdb_mock, notification_list, [])

        assert recieve_ret == expected_result
        assert duplicate_ret == {}
        mock_oase.bulksend.assert_called_once()

        # パフォーマンス確認：引数が正しく渡されているか
        called_args = mock_oase.bulksend.call_args[0]
        assert len(called_args[1]) == 10000

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_deep_nested_data(self, mock_oase):
        """深くネストしたデータ構造のテスト"""
        wsdb_mock = MagicMock()

        # 10レベルの深いネスト構造を作成
        deep_nested = {"level": 1}
        current = deep_nested
        for i in range(2, 11):
            current["nested"] = {"level": i}
            current = current["nested"]

        notification_list = [
            {
                "event_id": "deep_nested",
                "message": "Deep nested event",
                "data": deep_nested
            }
        ]

        expected_result = {"status": "success", "sent": 1, "failure": 0}
        mock_oase.bulksend.return_value = expected_result

        recieve_ret, duplicate_ret = add_notification_queue(wsdb_mock, notification_list, [])

        assert recieve_ret == expected_result
        assert duplicate_ret == {}
        mock_oase.bulksend.assert_called_once()

    # ===== 異なる例外タイプのテスト =====

    @pytest.mark.parametrize("exception_type,exception_message", [
        (ValueError, "Value error occurred"),
        (TypeError, "Type error occurred"),
        (ConnectionError, "Connection error occurred"),
        (TimeoutError, "Timeout error occurred"),
        (KeyError, "Key error occurred"),
        (AttributeError, "Attribute error occurred"),
        (ImportError, "Import error occurred"),
        (MemoryError, "Memory error occurred"),
    ])
    @patch('controllers.oase_controller.OASE')
    @patch('controllers.oase_controller.stacktrace')
    def test_add_notification_queue_various_exceptions(self, mock_stacktrace, mock_oase, exception_type, exception_message):
        """様々な例外タイプでのテスト"""
        wsdb_mock = MagicMock()
        notification_list = [{"event_id": "1", "message": "Event 1"}]

        # 指定された例外を発生させる
        test_exception = exception_type(exception_message)
        mock_oase.bulksend.side_effect = test_exception
        mock_stacktrace.return_value = f"Mock stack trace for {exception_type.__name__}"

        recieve_ret, duplicate_ret = add_notification_queue(wsdb_mock, notification_list, [])

        assert recieve_ret == {}
        assert duplicate_ret == {}
        mock_oase.bulksend.assert_called_once()
        g.applogger.error.assert_called()

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_extremely_large_datasets(self, mock_oase):
        """極端に大きなデータセットでのテスト"""
        wsdb_mock = MagicMock()
        recieve_notification_list = [{"event_id": f"r_{i}", "message": f"Recieve Event {i}"} for i in range(5000)]
        duplicate_notification_list = [{"event_id": f"d_{i}", "message": f"Duplicate Event {i}"} for i in range(5000)]

        mock_oase.bulksend.side_effect = [
            {"status": "success", "sent": 5000, "failure": 0},
            {"status": "success", "sent": 5000, "failure": 0}
        ]

        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, recieve_notification_list, duplicate_notification_list
        )

        assert mock_oase.bulksend.call_count == 2
        assert recieve_ret == {"status": "success", "sent": 5000, "failure": 0}
        assert duplicate_ret == {"status": "success", "sent": 5000, "failure": 0}

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_mixed_data_types(self, mock_oase):
        """混合データ型を含むリストのテスト"""
        wsdb_mock = MagicMock()
        recieve_notification_list = [
            {"event_id": "1", "message": "Valid Event"},
            {"event_id": 2, "message": "Numeric ID Event"},
            {"event_id": "", "message": "Empty ID Event"},
            {"special_chars": "特殊文字@#$%", "message": "Special chars event"}
        ]
        duplicate_notification_list = []

        mock_oase.bulksend.return_value = {"status": "success", "sent": 4, "failure": 0}

        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, recieve_notification_list, duplicate_notification_list
        )

        assert mock_oase.bulksend.call_count == 1
        assert recieve_ret == {"status": "success", "sent": 4, "failure": 0}
        assert duplicate_ret == {}

    @patch('controllers.oase_controller.OASE')
    @patch('controllers.oase_controller.stacktrace')
    def test_add_notification_queue_intermittent_failures(self, mock_stacktrace, mock_oase):
        """間欠的な障害のテスト（複数回実行して一部が失敗）"""
        wsdb_mock = MagicMock()
        recieve_notification_list = [{"event_id": "1", "message": "Event 1"}]
        duplicate_notification_list = [{"event_id": "2", "message": "Event 2"}]

        # 1回目は成功、2回目は失敗、3回目は成功のパターンをテスト
        exception = ConnectionError("Intermittent connection error")
        mock_oase.bulksend.side_effect = [
            {"status": "success", "sent": 1, "failure": 0},  # 1回目成功
            exception  # 2回目失敗
        ]
        mock_stacktrace.return_value = "Intermittent failure stack trace"

        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, recieve_notification_list, duplicate_notification_list
        )

        assert mock_oase.bulksend.call_count == 2
        assert recieve_ret == {"status": "success", "sent": 1, "failure": 0}
        assert duplicate_ret == {}

        g.applogger.error.assert_called()

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_bulksend_returns_none(self, mock_oase):
        """OASE.bulksendがNoneを返す場合のテスト"""
        wsdb_mock = MagicMock()
        recieve_notification_list = [{"event_id": "1", "message": "Event 1"}]
        duplicate_notification_list = [{"event_id": "2", "message": "Event 2"}]

        mock_oase.bulksend.side_effect = [None, None]

        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, recieve_notification_list, duplicate_notification_list
        )

        assert mock_oase.bulksend.call_count == 2
        assert recieve_ret is None
        assert duplicate_ret is None

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_unicode_and_special_characters(self, mock_oase):
        """Unicode文字と特殊文字を含むデータのテスト"""
        wsdb_mock = MagicMock()
        recieve_notification_list = [
            {"event_id": "🎯", "message": "絵文字イベント"},
            {"event_id": "αβγδε", "message": "ギリシャ文字イベント"},
            {"event_id": "مرحبا", "message": "アラビア語イベント"},
            {"event_id": "🚀💻🔥", "message": "複数絵文字イベント"}
        ]
        duplicate_notification_list = []

        mock_oase.bulksend.return_value = {"status": "success", "sent": 4, "failure": 0}

        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, recieve_notification_list, duplicate_notification_list
        )

        assert mock_oase.bulksend.call_count == 1
        assert recieve_ret == {"status": "success", "sent": 4, "failure": 0}
        assert duplicate_ret == {}

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_complex_decision_information(self, mock_oase):
        """複雑なdecision_informationのテスト（実際の実装確認）"""
        wsdb_mock = MagicMock()
        recieve_notification_list = [{"event_id": "1", "message": "Event 1"}]
        duplicate_notification_list = []

        mock_oase.bulksend.return_value = {"status": "success", "sent": 1, "failure": 0}

        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, recieve_notification_list, duplicate_notification_list
        )

        # 実際に渡されたdecision_informationを確認
        call_args = mock_oase.bulksend.call_args[0]
        decision_info = call_args[2]

        assert decision_info == {"notification_type": OASENotificationType.NEW}
        assert recieve_ret == {"status": "success", "sent": 1, "failure": 0}
        assert duplicate_ret == {}


class TestConcurrencyAndThreadSafety:
    """並行性とスレッドセーフティのテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

        g.applogger = MagicMock()
        g.appmsg = MagicMock()
        g.applogger.info = MagicMock()
        g.applogger.warning = MagicMock()
        g.applogger.error = MagicMock()
        g.applogger.debug = MagicMock()

    def teardown_method(self):
        """各テストメソッドの後に実行されるクリーンアップ処理"""
        self.app_context.pop()

    @patch('controllers.oase_controller.OASE')
    def test_add_notification_queue_rapid_consecutive_calls(self, mock_oase):
        """連続した高速呼び出しのテスト"""
        wsdb_mock = MagicMock()

        # 複数回の連続呼び出しをシミュレート
        results = []
        mock_oase.bulksend.return_value = {"status": "success", "sent": 1, "failure": 0}

        for i in range(10):
            recieve_list = [{"event_id": f"rapid_{i}", "message": f"Rapid Event {i}"}]
            duplicate_list = []

            recieve_ret, duplicate_ret = add_notification_queue(
                wsdb_mock, recieve_list, duplicate_list
            )
            results.append((recieve_ret, duplicate_ret))

        # 全ての呼び出しが成功していることを確認
        assert len(results) == 10
        for recieve_ret, duplicate_ret in results:
            assert recieve_ret == {"status": "success", "sent": 1, "failure": 0}
            assert duplicate_ret == {}

        assert mock_oase.bulksend.call_count == 10
