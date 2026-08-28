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
import time
from unittest.mock import patch, MagicMock
from flask import Flask, g

from controllers.oase_controller import add_notification_queue


class TestPerformanceAndStress:
    """パフォーマンスとストレステスト"""

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

    @pytest.mark.slow
    @patch('controllers.oase_controller.OASE')
    def test_massive_data_volume_performance(self, mock_oase):
        """大量データのパフォーマンステスト"""
        wsdb_mock = MagicMock()

        # 50,000件のイベントデータを生成
        massive_recieve_list = []
        massive_duplicate_list = []

        for i in range(25000):
            massive_recieve_list.append({
                "event_id": f"massive_recieve_{i:06d}",
                "message": f"Massive recieve event {i}",
                "timestamp": f"2025-01-01T{i%24:02d}:{i%60:02d}:{i%60:02d}Z",
                "data": {
                    "source": f"source_{i%100}",
                    "category": f"category_{i%50}",
                    "priority": i % 5,
                    "metadata": {
                        "batch_id": i // 1000,
                        "sequence": i % 1000
                    }
                }
            })

        for i in range(25000):
            massive_duplicate_list.append({
                "event_id": f"massive_duplicate_{i:06d}",
                "message": f"Massive duplicate event {i}",
                "timestamp": f"2025-01-01T{i%24:02d}:{i%60:02d}:{i%60:02d}Z",
                "data": {
                    "source": f"duplicate_source_{i%100}",
                    "category": f"duplicate_category_{i%50}",
                    "priority": i % 5
                }
            })

        mock_oase.bulksend.side_effect = [
            {"status": "success", "sent": 25000, "failure": 0, "processing_time_ms": 1500},
            {"status": "success", "sent": 25000, "failure": 0, "processing_time_ms": 1200}
        ]

        # パフォーマンス測定
        start_time = time.time()
        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, massive_recieve_list, massive_duplicate_list
        )
        end_time = time.time()

        execution_time = end_time - start_time

        # 結果検証
        assert recieve_ret["status"] == "success"
        assert recieve_ret["sent"] == 25000
        assert duplicate_ret["status"] == "success"
        assert duplicate_ret["sent"] == 25000

        # パフォーマンス要件の確認（例：10秒以内で完了）
        assert execution_time < 10.0, f"Execution took {execution_time:.2f} seconds, expected < 10.0"

        # OASE.bulksendが2回呼ばれることを確認
        assert mock_oase.bulksend.call_count == 2

    @pytest.mark.stress
    @patch('controllers.oase_controller.OASE')
    def test_memory_usage_with_large_datasets(self, mock_oase):
        """大量データセットでのメモリ使用量テスト"""
        import sys

        wsdb_mock = MagicMock()

        # メモリ使用量測定開始
        initial_size = sys.getsizeof(locals())

        # 非常に大きなデータセットを作成
        huge_data = []
        for i in range(100000):
            huge_data.append({
                "event_id": f"huge_event_{i:07d}",
                "message": f"Huge event message {i} with additional content to increase memory usage",
                "large_field": "x" * 1000,  # 1KB のデータ
                "nested_data": {
                    "level1": {"level2": {"level3": f"deep_value_{i}"}},
                    "array_data": list(range(100)),
                    "string_data": f"Additional string data for event {i}" * 10
                }
            })

        mock_oase.bulksend.return_value = {"status": "success", "sent": 100000, "failure": 0}

        # 関数実行
        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, huge_data, []
        )

        # メモリ使用量測定終了
        final_size = sys.getsizeof(locals())
        memory_increase = final_size - initial_size

        # 結果確認
        assert recieve_ret["status"] == "success"
        assert recieve_ret["sent"] == 100000
        assert duplicate_ret == {}

        # メモリ使用量が妥当な範囲内であることを確認
        # （実際の値は環境により異なるため、大まかな閾値を設定）
        assert memory_increase < 1000000000, f"Memory increase: {memory_increase} bytes"

    @patch('controllers.oase_controller.OASE')
    def test_concurrent_execution_simulation(self, mock_oase):
        """並行実行シミュレーションテスト"""
        wsdb_mock = MagicMock()

        # 複数の同時リクエストをシミュレート
        concurrent_requests = []

        for request_id in range(10):
            recieve_list = [
                {
                    "event_id": f"concurrent_{request_id}_{i}",
                    "message": f"Concurrent event {i} from request {request_id}",
                    "request_id": request_id
                }
                for i in range(100)
            ]
            duplicate_list = [
                {
                    "event_id": f"concurrent_dup_{request_id}_{i}",
                    "message": f"Concurrent duplicate {i} from request {request_id}",
                    "request_id": request_id
                }
                for i in range(50)
            ]
            concurrent_requests.append((recieve_list, duplicate_list))

        # 各リクエストに対する応答を設定
        mock_responses = []
        for i in range(20):  # 10リクエスト × 2回の呼び出し
            mock_responses.append({"status": "success", "sent": 100 if i % 2 == 0 else 50, "failure": 0})

        mock_oase.bulksend.side_effect = mock_responses

        # 全リクエストを順次実行（並行実行のシミュレート）
        results = []
        for recieve_list, duplicate_list in concurrent_requests:
            recieve_ret, duplicate_ret = add_notification_queue(
                wsdb_mock, recieve_list, duplicate_list
            )
            results.append((recieve_ret, duplicate_ret))

        # 全リクエストが成功したことを確認
        assert len(results) == 10
        for recieve_ret, duplicate_ret in results:
            assert recieve_ret["status"] == "success"
            assert recieve_ret["sent"] == 100
            assert duplicate_ret["status"] == "success"
            assert duplicate_ret["sent"] == 50

        # 合計20回の呼び出しが行われたことを確認
        assert mock_oase.bulksend.call_count == 20

    @pytest.mark.stress
    @patch('controllers.oase_controller.OASE')
    @patch('controllers.oase_controller.stacktrace')
    def test_error_rate_under_stress(self, mock_stacktrace, mock_oase):
        """ストレス下でのエラー率テスト"""
        wsdb_mock = MagicMock()

        # 1000回のリクエストで10%のエラー率をシミュレート
        total_requests = 1000
        error_rate = 0.1

        # 応答パターンを設定（成功とエラーの混在）
        responses = []
        for i in range(total_requests * 2):  # 各リクエストで2回の呼び出し
            if i % 10 == 0:  # 10%のエラー率
                responses.append(ConnectionError(f"Simulated error {i}"))
            else:
                responses.append({"status": "success", "sent": 1, "failure": 0})

        mock_oase.bulksend.side_effect = responses
        mock_stacktrace.return_value = "Stress test stack trace"

        # 統計収集
        success_count = 0
        error_count = 0

        # 大量リクエストの実行
        for i in range(total_requests):
            recieve_list = [{"event_id": f"stress_{i}", "message": f"Stress event {i}"}]
            duplicate_list = []

            try:
                recieve_ret, duplicate_ret = add_notification_queue(
                    wsdb_mock, recieve_list, duplicate_list
                )

                # 成功の場合
                if recieve_ret and recieve_ret.get("status") == "success":
                    success_count += 1
                else:
                    error_count += 1

            except Exception:
                error_count += 1

        # エラー率の検証
        actual_error_rate = error_count / total_requests

        # 許容範囲内のエラー率であることを確認（±2%の誤差を許容）
        assert abs(actual_error_rate - error_rate) < 0.02, f"Error rate: {actual_error_rate:.2%}, expected: {error_rate:.2%}"

        # 成功したリクエストもあることを確認
        assert success_count > 0, "No successful requests under stress"

    @patch('controllers.oase_controller.OASE')
    def test_response_time_distribution(self, mock_oase):
        """応答時間分布テスト"""
        wsdb_mock = MagicMock()

        # 様々な応答時間をシミュレート
        response_times = []

        def slow_oase_bulksend(*args, **kwargs):
            """OASE.bulksendの遅延をシミュレート"""
            import random
            # 0.1-2.0秒の遅延をランダムに発生
            delay = random.uniform(0.1, 2.0)
            time.sleep(delay)
            response_times.append(delay)
            return {"status": "success", "sent": 1, "failure": 0, "response_time": delay}

        mock_oase.bulksend.side_effect = slow_oase_bulksend

        # 100回のリクエストを実行
        execution_times = []

        for i in range(100):
            event_list = [{"event_id": f"timing_{i}", "message": f"Timing event {i}"}]

            start_time = time.time()
            recieve_ret, duplicate_ret = add_notification_queue(
                wsdb_mock, event_list, []
            )
            end_time = time.time()

            execution_times.append(end_time - start_time)

            # 各リクエストが成功することを確認
            assert recieve_ret["status"] == "success"

        # 統計計算
        avg_execution_time = sum(execution_times) / len(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)

        # パフォーマンス要件の確認
        assert avg_execution_time < 3.0, f"Average execution time: {avg_execution_time:.2f}s"
        assert max_execution_time < 5.0, f"Maximum execution time: {max_execution_time:.2f}s"
        assert min_execution_time > 0.05, f"Minimum execution time: {min_execution_time:.2f}s"

    @patch('controllers.oase_controller.OASE')
    def test_memory_leak_detection(self, mock_oase):
        """メモリリーク検出テスト"""
        import gc

        wsdb_mock = MagicMock()
        mock_oase.bulksend.return_value = {"status": "success", "sent": 1, "failure": 0}

        # 初期メモリ状態
        gc.collect()
        initial_objects = len(gc.get_objects())

        # 大量の繰り返し実行
        for i in range(1000):
            event_list = [
                {
                    "event_id": f"leak_test_{i}",
                    "message": f"Memory leak test event {i}",
                    "large_data": "x" * 1000  # 1KB のデータ
                }
            ]

            recieve_ret, duplicate_ret = add_notification_queue(
                wsdb_mock, event_list, []
            )

            # 定期的なガベージコレクション
            if i % 100 == 0:
                # MagicMockは呼び出し履歴（引数ごと）を蓄積するため、リーク計測のノイズになる。
                # applogger/appmsgは末尾で検証しないので履歴を破棄する（bulksendはcall_count検証があるため残す）
                g.applogger.reset_mock()
                g.appmsg.reset_mock()
                gc.collect()
                _final_objects = len(gc.get_objects())
                object_increase = _final_objects - initial_objects
                print(f"progress increase: {_final_objects} - {initial_objects} = {object_increase}")

        # 最終メモリ状態
        gc.collect()
        final_objects = len(gc.get_objects())

        # オブジェクト数の増加をチェック
        object_increase = final_objects - initial_objects
        print(f"Object increase: {final_objects} - {initial_objects} = {object_increase}")

        # メモリリークがないことを確認（少しの増加は許容）
        # g.applogger.info 呼ぶだけでも増加するので、閾値を高めに設定(追加:*10*2)
        assert object_increase < 1000 * 10 * 2, f"Potential memory leak detected: {object_increase} objects increased"

        # 全ての呼び出しが成功したことを確認
        assert mock_oase.bulksend.call_count == 1000


class TestSpecialInputPatterns:
    """特殊な入力パターンのテスト"""

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

    @patch('controllers.oase_controller.OASE')
    def test_binary_data_handling(self, mock_oase):
        """バイナリデータ処理テスト"""
        wsdb_mock = MagicMock()

        # バイナリデータを含むイベント
        binary_events = [
            {
                "event_id": "binary_test",
                "message": "Event with binary data",
                "binary_field": b'\x00\x01\x02\x03\x04\x05',
                "base64_data": "SGVsbG8gV29ybGQ="  # "Hello World" in base64
            }
        ]

        mock_oase.bulksend.return_value = {"status": "success", "sent": 1, "failure": 0}

        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, binary_events, []
        )

        assert recieve_ret["status"] == "success"
        assert duplicate_ret == {}

        # バイナリデータが正しく渡されることを確認
        call_args = mock_oase.bulksend.call_args[0]
        passed_data = call_args[1][0]
        assert passed_data["binary_field"] == b'\x00\x01\x02\x03\x04\x05'
        assert passed_data["base64_data"] == "SGVsbG8gV29ybGQ="

    @patch('controllers.oase_controller.OASE')
    def test_circular_reference_handling(self, mock_oase):
        """循環参照処理テスト"""
        wsdb_mock = MagicMock()

        # 循環参照を含むデータ構造
        circular_data = {"id": "circular_test"}
        circular_data["self_ref"] = circular_data  # 循環参照

        events_with_circular_ref = [
            {
                "event_id": "circular_ref_test",
                "message": "Event with circular reference",
                "circular_data": circular_data
            }
        ]

        mock_oase.bulksend.return_value = {"status": "success", "sent": 1, "failure": 0}

        # 循環参照があってもクラッシュしないことを確認
        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, events_with_circular_ref, []
        )

        assert recieve_ret["status"] == "success"
        assert duplicate_ret == {}

    @patch('controllers.oase_controller.OASE')
    def test_extreme_unicode_handling(self, mock_oase):
        """極端なUnicode文字処理テスト"""
        wsdb_mock = MagicMock()

        # 様々なUnicode文字を含むデータ
        unicode_events = [
            {
                "event_id": "unicode_test",
                "message": "🌈🦄💫✨🎭🎪🎨🎯🎲🎮🎤🎧🎼🎹🎸🎺🎷",
                "emoji_field": "👨‍👩‍👧‍👦👮‍♀️👷‍♂️💂‍♀️🕵️‍♂️👩‍⚕️👨‍🌾👩‍🍳👨‍🎓",
                "mathematical": "∑∏∫∆∇∂∞≈≠≤≥±∓×÷√∛∜∠∟⊥∥⊕⊗⊙⊆⊇⊂⊃",
                "currency": "₿₹₽₴₨₩₪₫₦₡₨₱₵₸₼₽₾₿＄￠￡￢￣￤￥￦",
                "arrows": "←↑→↓↔↕↖↗↘↙⇐⇑⇒⇓⇔⇕⇖⇗⇘⇙⟵⟶⟷⟸⟹⟺",
                "chinese": "中文测试数据包含各种汉字字符集",
                "arabic": "اختبار البيانات العربية مع مجموعات الأحرف المختلفة",
                "cyrillic": "Тестовые данные на кириллице с различными наборами символов"
            }
        ]

        mock_oase.bulksend.return_value = {"status": "success", "sent": 1, "failure": 0}

        recieve_ret, duplicate_ret = add_notification_queue(
            wsdb_mock, unicode_events, []
        )

        assert recieve_ret["status"] == "success"
        assert duplicate_ret == {}

        # Unicode文字が正しく保持されることを確認
        call_args = mock_oase.bulksend.call_args[0]
        passed_data = call_args[1][0]
        assert "🌈🦄💫✨" in passed_data["message"]
        assert "中文测试" in passed_data["chinese"]
