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
import sys

from controllers.oase_controller import add_notification_queue
from common_libs.notification.sub_classes.oase import OASENotificationType


class TestBoundaryValuesAndInputValidation:
    """境界値と入力検証の包括的テスト"""

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

    def teardown_method(self):
        """各テストメソッドの後に実行されるクリーンアップ処理"""
        self.app_context.pop()

    # ===== 配列・コレクションの境界値テスト =====

    @pytest.mark.parametrize("list_size", [
        0,      # 空リスト
        1,      # 単一要素
        10,     # 小規模
        100,    # 中規模
        1000,   # 大規模
        10000   # 非常に大規模
    ])
    @patch('controllers.oase_controller.OASE')
    def test_list_size_boundaries(self, mock_oase, list_size):
        """リストサイズの境界値テスト"""
        wsdb_mock = MagicMock()

        # 指定サイズのリストを生成
        notification_list = []
        for i in range(list_size):
            notification_list.append({
                "event_id": f"list_test_{i:06d}",
                "message": f"List boundary test event {i}",
                "index": i
            })

        mock_oase.bulksend.return_value = {"status": "success", "sent": list_size, "failure": 0}

        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, notification_list, []
        )

        if list_size == 0:
            assert recieve_ret == {}
            assert mock_oase.bulksend.call_count == 0
        else:
            assert recieve_ret == {"status": "success", "sent": list_size, "failure": 0}
            assert mock_oase.bulksend.call_count == 1

    # ===== 極端なケースのテスト =====

    @patch('controllers.oase_controller.OASE')
    def test_mixed_valid_invalid_data(self, mock_oase):
        """有効・無効データ混在テスト"""
        wsdb_mock = MagicMock()

        # 有効なデータと問題のあるデータの混在
        mixed_notification_list = [
            # 有効なデータ
            {"event_id": "valid_1", "message": "Valid event 1"},
            {"event_id": "valid_2", "message": "Valid event 2"},

            # 問題のあるデータ（しかし技術的には処理可能）
            {"event_id": "", "message": "Empty ID event"},
            {"missing_event_id": "no_event_id", "message": "Missing event_id"},
            {"event_id": None, "message": "None event_id"},

            # 特殊なデータ
            {"event_id": "special", "message": None},
            {"event_id": "unicode", "message": "🌟Unicode message🌟"},

            # 有効なデータ
            {"event_id": "valid_3", "message": "Valid event 3"}
        ]

        mock_oase.bulksend.return_value = {"status": "partial_success", "sent": 8, "warnings": 3, "failure": 0}

        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, mixed_notification_list, []
        )

        assert recieve_ret == {"status": "partial_success", "sent": 8, "warnings": 3, "failure": 0}
        assert duplicate_ret == {}

        # 混在データがそのまま渡されることを確認
        call_args = mock_oase.bulksend.call_args[0]
        passed_list = call_args[1]
        assert len(passed_list) == 8

    @patch('controllers.oase_controller.OASE')
    def test_performance_critical_boundaries(self, mock_oase):
        """パフォーマンス重要境界のテスト"""
        wsdb_mock = MagicMock()

        # パフォーマンスに影響する可能性のある境界値
        performance_test_cases = [
            # メモリ境界
            {"size": 1024, "description": "1KB data"},
            {"size": 1024 * 1024, "description": "1MB data"},

            # 処理時間境界
            {"count": 1000, "description": "1K events"},
            {"count": 10000, "description": "10K events"}
        ]

        for test_case in performance_test_cases:
            if "size" in test_case:
                # サイズベースのテスト
                large_string = "x" * test_case["size"]
                notification_list = [
                    {
                        "event_id": "performance_size_test",
                        "message": test_case["description"],
                        "large_data": large_string
                    }
                ]
            else:
                # 件数ベースのテスト
                notification_list = [
                    {
                        "event_id": f"performance_count_{i:06d}",
                        "message": f"Performance test event {i}",
                        "index": i
                    }
                    for i in range(test_case["count"])
                ]

            mock_oase.bulksend.return_value = {
                "status": "success",
                "sent": len(notification_list),
                "test_case": test_case["description"],
                "failure": 0
            }

            recieve_ret, duplicate_ret = add_notification_queue(
                wsdb_mock, notification_list, []
            )

            assert recieve_ret["status"] == "success"
            assert recieve_ret["sent"] == len(notification_list)

            # モックをリセット
            mock_oase.bulksend.reset_mock()
