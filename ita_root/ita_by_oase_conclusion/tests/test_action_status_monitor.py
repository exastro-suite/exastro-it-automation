#   Copyright 2026 NEC Corporation
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

import json
import pytest
from unittest.mock import MagicMock, Mock
from flask import Flask, g

from common_libs.oase.const import oaseConst
from libs.action_status_monitor import ActionStatusMonitor
from tests.test_double import DummyDB, MockMONGOConnectWs, DummyAppMsg, DummyLogger


@pytest.fixture
def setup_test_environment(monkeypatch):
    """テスト環境のセットアップ"""
    # Flaskアプリのコンテキストを作成
    flask_app = Flask(__name__)
    with flask_app.app_context():
        # gオブジェクトの設定
        g.LANGUAGE = "ja"
        g.USER_ID = "test_user"
        g.WORKSPACE_ID = "test_workspace"
        g.ORGANIZATION_ID = "test_org"
        g.applogger = DummyLogger()
        g.appmsg = DummyAppMsg()

        # データベースとMongoのモック
        ws_db = DummyDB("test_workspace")
        mock_mongo = MockMONGOConnectWs()

        # EventObjのモック
        mock_event_obj = MagicMock()

        yield {
            "g": g,
            "ws_db": ws_db,
            "mock_mongo": mock_mongo,
            "mock_event_obj": mock_event_obj,
        }


class TestActionStatusMonitorCheckRuleMatch:
    """ActionStatusMonitor.checkRuleMatch メソッドのテストクラス"""

    def test_check_rule_match_success(self, setup_test_environment):
        """正常系: アクション実行成功のテスト"""
        env = setup_test_environment
        ws_db = env["ws_db"]
        mock_event_obj = env["mock_event_obj"]

        # テストデータの準備
        action_log_data = {
            "ACTION_LOG_ID": "log001",
            "RULE_ID": "rule001",
            "STATUS_ID": oaseConst.OSTS_Rule_Match,
            "EVENT_ID_LIST": "event001,event002",
            "DISUSE_FLAG": "0",
        }

        rule_data = {
            "RULE_ID": "rule001",
            "RULE_NAME": "Test Rule",
            "RULE_PRIORITY": "1",
            "FILTER_A": "filter001",
            "FILTER_OPERATOR": "",
            "FILTER_B": "",
            "ACTION_ID": "action001",
            "ACTION_LABEL_INHERITANCE_FLAG": "1",
            "EVENT_LABEL_INHERITANCE_FLAG": "1",
            "CONCLUSION_LABEL_SETTINGS": "[]",
            "RULE_LABEL_NAME": "test",
            "EVENT_ID_LIST": "event001,event002",
            "TTL": "300",
            "AVAILABLE_FLAG": "1",
            "DISUSE_FLAG": "0",
        }

        # DBデータの設定
        ws_db.table_data[oaseConst.T_OASE_ACTION_LOG] = [action_log_data]
        ws_db.table_data[oaseConst.T_OASE_RULE] = [rule_data]

        # ActionStatusMonitorのインスタンス作成
        monitor = ActionStatusMonitor(ws_db, mock_event_obj)

        # アクションオブジェクトのモック（成功パターン）
        mock_action = MagicMock()
        mock_action.run.return_value = (
            True,
            {"conductor_instance_id": "conductor001"},
        )

        # テスト実行
        monitor.checkRuleMatch(mock_action)

        # 検証
        # 1. アクションが実行されたことを確認
        assert mock_action.run.called
        assert mock_action.run.call_count == 1

        # 2. ステータスが「実行中」に更新されたことを確認
        updated_log = ws_db.table_data[oaseConst.T_OASE_ACTION_LOG][0]
        assert updated_log["STATUS_ID"] == oaseConst.OSTS_Executing

        # 3. CONDUCTOR_INSTANCE_IDが設定されたことを確認
        assert updated_log["CONDUCTOR_INSTANCE_ID"] == "conductor001"

        # 4. ACTION_RESULTが成功時に記録されていることを確認
        # 注: 成功時は実行中ステータス更新時にACTION_RESULTがセットされるが、
        #     その後のCONDUCTOR_INSTANCE_ID更新時にはACTION_RESULTは更新されないため、
        #     msgはNoneのままになる
        action_result = json.loads(updated_log["ACTION_RESULT"])
        assert action_result["action"]["type"] == "Conductor"
        assert action_result["action"]["result"] is True
        assert action_result["action"]["msg"] is None

    def test_check_rule_match_failure(self, setup_test_environment):
        """異常系: アクション実行失敗のテスト"""
        env = setup_test_environment
        ws_db = env["ws_db"]
        mock_event_obj = env["mock_event_obj"]

        # テストデータの準備
        action_log_data = {
            "ACTION_LOG_ID": "log002",
            "RULE_ID": "rule002",
            "STATUS_ID": oaseConst.OSTS_Rule_Match,
            "EVENT_ID_LIST": "event003",
            "DISUSE_FLAG": "0",
        }

        rule_data = {
            "RULE_ID": "rule002",
            "RULE_NAME": "Test Rule 2",
            "RULE_PRIORITY": "1",
            "FILTER_A": "filter002",
            "FILTER_OPERATOR": "",
            "FILTER_B": "",
            "ACTION_ID": "action002",
            "ACTION_LABEL_INHERITANCE_FLAG": "1",
            "EVENT_LABEL_INHERITANCE_FLAG": "1",
            "CONCLUSION_LABEL_SETTINGS": "[]",
            "RULE_LABEL_NAME": "test2",
            "EVENT_ID_LIST": "event003",
            "TTL": "300",
            "AVAILABLE_FLAG": "1",
            "DISUSE_FLAG": "0",
        }

        # DBデータの設定
        ws_db.table_data[oaseConst.T_OASE_ACTION_LOG] = [action_log_data]
        ws_db.table_data[oaseConst.T_OASE_RULE] = [rule_data]

        # ActionStatusMonitorのインスタンス作成
        monitor = ActionStatusMonitor(ws_db, mock_event_obj)

        # アクションオブジェクトのモック（失敗パターン）
        mock_action = MagicMock()
        mock_action.run.return_value = (False, "Action execution failed")

        # テスト実行
        monitor.checkRuleMatch(mock_action)

        # 検証
        # 1. アクションが実行されたことを確認
        assert mock_action.run.called

        # 2. ステータスが「起動失敗」に更新されたことを確認
        updated_log = ws_db.table_data[oaseConst.T_OASE_ACTION_LOG][0]
        assert updated_log["STATUS_ID"] == oaseConst.OSTS_Launch_Failed

        # 3. ACTION_RESULTにエラー情報が記録されたことを確認
        action_result = json.loads(updated_log["ACTION_RESULT"])
        assert action_result["action"]["type"] == "Conductor"
        assert action_result["action"]["result"] is False
        assert action_result["action"]["msg"] == "Action execution failed"

    def test_check_rule_match_with_existing_action_result_failure(self, setup_test_environment):
        """正常系: 既存のACTION_RESULTがある場合のテスト（新しいテンプレートで上書き）"""
        env = setup_test_environment
        ws_db = env["ws_db"]
        mock_event_obj = env["mock_event_obj"]

        # 既存のACTION_RESULT（この値は無視され、新しいテンプレートで上書きされる）
        existing_action_result = json.dumps({
            "action": {
                "type": "OldType",
                "result": None,
                "msg": "Previous attempt"
            }
        }, ensure_ascii=False)

        # テストデータの準備
        action_log_data = {
            "ACTION_LOG_ID": "log003",
            "RULE_ID": "rule003",
            "STATUS_ID": oaseConst.OSTS_Rule_Match,
            "EVENT_ID_LIST": "event004",
            "ACTION_RESULT": existing_action_result,
            "DISUSE_FLAG": "0",
        }

        rule_data = {
            "RULE_ID": "rule003",
            "RULE_NAME": "Test Rule 3",
            "RULE_PRIORITY": "1",
            "FILTER_A": "filter003",
            "FILTER_OPERATOR": "",
            "FILTER_B": "",
            "ACTION_ID": "action003",
            "ACTION_LABEL_INHERITANCE_FLAG": "1",
            "EVENT_LABEL_INHERITANCE_FLAG": "1",
            "CONCLUSION_LABEL_SETTINGS": "[]",
            "RULE_LABEL_NAME": "test3",
            "EVENT_ID_LIST": "event004",
            "TTL": "300",
            "AVAILABLE_FLAG": "1",
            "DISUSE_FLAG": "0",
        }

        # DBデータの設定
        ws_db.table_data[oaseConst.T_OASE_ACTION_LOG] = [action_log_data]
        ws_db.table_data[oaseConst.T_OASE_RULE] = [rule_data]

        # ActionStatusMonitorのインスタンス作成
        monitor = ActionStatusMonitor(ws_db, mock_event_obj)

        # アクションオブジェクトのモック（失敗パターン）
        mock_action = MagicMock()
        mock_action.run.return_value = (False, "Failed to launch")

        # テスト実行
        monitor.checkRuleMatch(mock_action)

        # 検証
        # 1. ACTION_RESULTが新しいテンプレートで上書きされていることを確認
        updated_log = ws_db.table_data[oaseConst.T_OASE_ACTION_LOG][0]
        action_result = json.loads(updated_log["ACTION_RESULT"])
        assert action_result["action"]["type"] == "Conductor"  # 既存の "OldType" ではなく "Conductor"
        assert action_result["action"]["result"] is False
        assert action_result["action"]["msg"] == "Failed to launch"

    def test_check_rule_match_with_invalid_action_result(self, setup_test_environment):
        """正常系: 不正なACTION_RESULT形式がある場合のテスト（既存値は無視され新しいテンプレートで上書き）"""
        env = setup_test_environment
        ws_db = env["ws_db"]
        mock_event_obj = env["mock_event_obj"]

        # 不正なJSON形式のACTION_RESULT（この値は無視され、新しいテンプレートで上書きされる）
        invalid_action_result = "Invalid JSON format"

        # テストデータの準備
        action_log_data = {
            "ACTION_LOG_ID": "log004",
            "RULE_ID": "rule004",
            "STATUS_ID": oaseConst.OSTS_Rule_Match,
            "EVENT_ID_LIST": "event005",
            "ACTION_RESULT": invalid_action_result,
            "DISUSE_FLAG": "0",
        }

        rule_data = {
            "RULE_ID": "rule004",
            "RULE_NAME": "Test Rule 4",
            "RULE_PRIORITY": "1",
            "FILTER_A": "filter004",
            "FILTER_OPERATOR": "",
            "FILTER_B": "",
            "ACTION_ID": "action004",
            "ACTION_LABEL_INHERITANCE_FLAG": "1",
            "EVENT_LABEL_INHERITANCE_FLAG": "1",
            "CONCLUSION_LABEL_SETTINGS": "[]",
            "RULE_LABEL_NAME": "test4",
            "EVENT_ID_LIST": "event005",
            "TTL": "300",
            "AVAILABLE_FLAG": "1",
            "DISUSE_FLAG": "0",
        }

        # DBデータの設定
        ws_db.table_data[oaseConst.T_OASE_ACTION_LOG] = [action_log_data]
        ws_db.table_data[oaseConst.T_OASE_RULE] = [rule_data]

        # ActionStatusMonitorのインスタンス作成
        monitor = ActionStatusMonitor(ws_db, mock_event_obj)

        # アクションオブジェクトのモック（失敗パターン）
        mock_action = MagicMock()
        mock_action.run.return_value = (False, "Action failed")

        # テスト実行
        monitor.checkRuleMatch(mock_action)

        # 検証
        # checkRuleMatchでは既存のACTION_RESULTを読まないため、警告ログは出力されない
        # 新しいテンプレートで処理が継続され、ACTION_RESULTが正しく更新されることを確認
        updated_log = ws_db.table_data[oaseConst.T_OASE_ACTION_LOG][0]
        action_result = json.loads(updated_log["ACTION_RESULT"])
        assert action_result["action"]["type"] == "Conductor"
        assert action_result["action"]["result"] is False
        assert action_result["action"]["msg"] == "Action failed"

    def test_check_rule_match_multiple_action_logs(self, setup_test_environment):
        """正常系: 複数のアクションログがある場合のテスト"""
        env = setup_test_environment
        ws_db = env["ws_db"]
        mock_event_obj = env["mock_event_obj"]

        # 複数のテストデータの準備
        action_logs = [
            {
                "ACTION_LOG_ID": f"log00{i}",
                "RULE_ID": f"rule00{i}",
                "STATUS_ID": oaseConst.OSTS_Rule_Match,
                "EVENT_ID_LIST": f"event00{i}",
                "DISUSE_FLAG": "0",
            }
            for i in range(1, 4)
        ]

        rules = [
            {
                "RULE_ID": f"rule00{i}",
                "RULE_NAME": f"Test Rule {i}",
                "RULE_PRIORITY": "1",
                "FILTER_A": f"filter00{i}",
                "FILTER_OPERATOR": "",
                "FILTER_B": "",
                "ACTION_ID": f"action00{i}",
                "ACTION_LABEL_INHERITANCE_FLAG": "1",
                "EVENT_LABEL_INHERITANCE_FLAG": "1",
                "CONCLUSION_LABEL_SETTINGS": "[]",
                "RULE_LABEL_NAME": f"test{i}",
                "EVENT_ID_LIST": f"event00{i}",
                "TTL": "300",
                "AVAILABLE_FLAG": "1",
                "DISUSE_FLAG": "0",
            }
            for i in range(1, 4)
        ]

        # DBデータの設定
        ws_db.table_data[oaseConst.T_OASE_ACTION_LOG] = action_logs
        ws_db.table_data[oaseConst.T_OASE_RULE] = rules

        # ActionStatusMonitorのインスタンス作成
        monitor = ActionStatusMonitor(ws_db, mock_event_obj)

        # アクションオブジェクトのモック
        mock_action = MagicMock()
        mock_action.run.side_effect = [
            (True, {"conductor_instance_id": f"conductor00{i}"})
            for i in range(1, 4)
        ]

        # テスト実行
        monitor.checkRuleMatch(mock_action)

        # 検証
        # 1. 全てのアクションが実行されたことを確認
        assert mock_action.run.call_count == 3

        # 2. 全てのアクションログが更新されたことを確認
        for i, log in enumerate(ws_db.table_data[oaseConst.T_OASE_ACTION_LOG], 1):
            assert log["STATUS_ID"] == oaseConst.OSTS_Executing
            assert log["CONDUCTOR_INSTANCE_ID"] == f"conductor00{i}"

            # 3. 各ログでACTION_RESULTが記録されていることを確認
            # 注: 成功時はmsgがNoneのまま（CONDUCTOR_INSTANCE_ID更新時にACTION_RESULTは更新されない）
            action_result = json.loads(log["ACTION_RESULT"])
            assert action_result["action"]["type"] == "Conductor"
            assert action_result["action"]["result"] is True
            assert action_result["action"]["msg"] is None

    def test_check_rule_match_with_approved_status(self, setup_test_environment):
        """正常系: 承認済みステータスのアクションログのテスト"""
        env = setup_test_environment
        ws_db = env["ws_db"]
        mock_event_obj = env["mock_event_obj"]

        # 承認済みステータスのテストデータ
        action_log_data = {
            "ACTION_LOG_ID": "log005",
            "RULE_ID": "rule005",
            "STATUS_ID": oaseConst.OSTS_Approved,  # 承認済み
            "EVENT_ID_LIST": "event006",
            "DISUSE_FLAG": "0",
        }

        rule_data = {
            "RULE_ID": "rule005",
            "RULE_NAME": "Test Rule 5",
            "RULE_PRIORITY": "1",
            "FILTER_A": "filter005",
            "FILTER_OPERATOR": "",
            "FILTER_B": "",
            "ACTION_ID": "action005",
            "ACTION_LABEL_INHERITANCE_FLAG": "1",
            "EVENT_LABEL_INHERITANCE_FLAG": "1",
            "CONCLUSION_LABEL_SETTINGS": "[]",
            "RULE_LABEL_NAME": "test5",
            "EVENT_ID_LIST": "event006",
            "TTL": "300",
            "AVAILABLE_FLAG": "1",
            "DISUSE_FLAG": "0",
        }

        # DBデータの設定
        ws_db.table_data[oaseConst.T_OASE_ACTION_LOG] = [action_log_data]
        ws_db.table_data[oaseConst.T_OASE_RULE] = [rule_data]

        # ActionStatusMonitorのインスタンス作成
        monitor = ActionStatusMonitor(ws_db, mock_event_obj)

        # アクションオブジェクトのモック
        mock_action = MagicMock()
        mock_action.run.return_value = (
            True,
            {"conductor_instance_id": "conductor005"},
        )

        # テスト実行
        monitor.checkRuleMatch(mock_action)

        # 検証
        # 承認済みステータスのアクションも処理されることを確認
        assert mock_action.run.called
        updated_log = ws_db.table_data[oaseConst.T_OASE_ACTION_LOG][0]
        assert updated_log["STATUS_ID"] == oaseConst.OSTS_Executing

        # ACTION_RESULTが記録されていることを確認
        # 注: 成功時はmsgがNoneのまま（CONDUCTOR_INSTANCE_ID更新時にACTION_RESULTは更新されない）
        action_result = json.loads(updated_log["ACTION_RESULT"])
        assert action_result["action"]["type"] == "Conductor"
        assert action_result["action"]["result"] is True
        assert action_result["action"]["msg"] is None


class TestActionStatusMonitorCheckExecuting:
    """ActionStatusMonitor.checkExecuting メソッドのテストクラス"""

    def test_check_executing_completed_success(self, setup_test_environment):
        """正常系: Conductor正常終了のテスト"""
        env = setup_test_environment
        ws_db = env["ws_db"]
        mock_event_obj = env["mock_event_obj"]

        # 実行中ステータスのACTION_RESULTを含むテストデータ
        action_result = json.dumps({
            "action": {
                "type": "Conductor",
                "result": True,
                "msg": None
            }
        }, ensure_ascii=False)

        action_log_data = {
            "ACTION_LOG_ID": "log001",
            "RULE_ID": "rule001",
            "STATUS_ID": oaseConst.OSTS_Executing,
            "CONDUCTOR_INSTANCE_ID": "conductor001",
            "EVENT_ID_LIST": "event001",
            "ACTION_RESULT": action_result,
            "DISUSE_FLAG": "0",
            "CONCLUSION_EVENT_LABELS": '{"labels": {}, "exastro_label_key_inputs": []}',
        }

        rule_data = {
            "RULE_ID": "rule001",
            "RULE_NAME": "Test Rule",
            "RULE_PRIORITY": "1",
            "FILTER_A": "filter001",
            "FILTER_OPERATOR": "",
            "FILTER_B": "",
            "ACTION_ID": "action001",
            "ACTION_LABEL_INHERITANCE_FLAG": "1",
            "EVENT_LABEL_INHERITANCE_FLAG": "1",
            "CONCLUSION_LABEL_SETTINGS": "[]",
            "RULE_LABEL_NAME": "test",
            "EVENT_ID_LIST": "event001",
            "TTL": "300",
            "AVAILABLE_FLAG": "1",
            "DISUSE_FLAG": "0",
        }

        # DummyDB のモックデータを設定（sql_execute が JOIN した結果を返すために必要）
        # sql_execute は T_COMN_CONDUCTOR_INSTANCE と JOIN するため、モックIDを設定
        ws_db.table_data[oaseConst.T_OASE_ACTION_LOG] = [action_log_data]
        ws_db.table_data[oaseConst.T_OASE_RULE] = [rule_data]

        # ActionStatusMonitorのインスタンス作成
        monitor = ActionStatusMonitor(ws_db, mock_event_obj)

        # sql_execute が返す JOIN 結果を上書き（DummyDB のデフォルトに CONDUCTOR_STATUS_ID を追加）
        original_sql_execute = ws_db.sql_execute
        def custom_sql_execute(sql, params=None):
            result = original_sql_execute(sql, params)
            # CONDUCTOR_STATUS_ID を正常終了に設定
            for row in result:
                row["JOIN_CONDUCTOR_INSTANCE_ID"] = row.get("CONDUCTOR_INSTANCE_ID")
                row["CONDUCTOR_STATUS_ID"] = oaseConst.CSTS_Completed
                row["TAB_B_DISUSE_FLAG"] = "0"
            return result
        ws_db.sql_execute = custom_sql_execute

        # テスト実行
        monitor.checkExecuting()

        # 検証
        # 1. ステータスが「完了」に更新されたことを確認
        updated_log = ws_db.table_data[oaseConst.T_OASE_ACTION_LOG][0]
        assert updated_log["STATUS_ID"] == oaseConst.OSTS_Completed

        # 2. ACTION_RESULTは更新されない（正常終了の場合）
        # 元のACTION_RESULTがそのまま残る
        action_result_after = json.loads(updated_log["ACTION_RESULT"])
        assert action_result_after["action"]["result"] is True  # Falseに更新されていない

    def test_check_executing_completed_abend(self, setup_test_environment):
        """正常系: Conductor異常終了のテスト（ACTION_RESULT更新）"""
        env = setup_test_environment
        ws_db = env["ws_db"]
        mock_event_obj = env["mock_event_obj"]

        # 実行中ステータスのACTION_RESULTを含むテストデータ
        action_result = json.dumps({
            "action": {
                "type": "Conductor",
                "result": True,
                "msg": None
            }
        }, ensure_ascii=False)

        action_log_data = {
            "ACTION_LOG_ID": "log002",
            "RULE_ID": "rule002",
            "STATUS_ID": oaseConst.OSTS_Executing,
            "CONDUCTOR_INSTANCE_ID": "conductor002",
            "EVENT_ID_LIST": "event002",
            "ACTION_RESULT": action_result,
            "DISUSE_FLAG": "0",
            "CONCLUSION_EVENT_LABELS": '{"labels": {}, "exastro_label_key_inputs": []}',
        }

        rule_data = {
            "RULE_ID": "rule002",
            "RULE_NAME": "Test Rule 2",
            "RULE_PRIORITY": "1",
            "FILTER_A": "filter002",
            "FILTER_OPERATOR": "",
            "FILTER_B": "",
            "ACTION_ID": "action002",
            "ACTION_LABEL_INHERITANCE_FLAG": "1",
            "EVENT_LABEL_INHERITANCE_FLAG": "1",
            "CONCLUSION_LABEL_SETTINGS": "[]",
            "RULE_LABEL_NAME": "test2",
            "EVENT_ID_LIST": "event002",
            "TTL": "300",
            "AVAILABLE_FLAG": "1",
            "DISUSE_FLAG": "0",
        }

        # DummyDB のモックデータを設定
        ws_db.table_data[oaseConst.T_OASE_ACTION_LOG] = [action_log_data]
        ws_db.table_data[oaseConst.T_OASE_RULE] = [rule_data]

        # ActionStatusMonitorのインスタンス作成
        monitor = ActionStatusMonitor(ws_db, mock_event_obj)

        # sql_execute が返す JOIN 結果を上書き（CONDUCTOR_STATUS_ID を異常終了に設定）
        original_sql_execute = ws_db.sql_execute
        def custom_sql_execute(sql, params=None):
            result = original_sql_execute(sql, params)
            for row in result:
                row["JOIN_CONDUCTOR_INSTANCE_ID"] = row.get("CONDUCTOR_INSTANCE_ID")
                row["CONDUCTOR_STATUS_ID"] = oaseConst.CSTS_Abend  # 異常終了
                row["TAB_B_DISUSE_FLAG"] = "0"
            return result
        ws_db.sql_execute = custom_sql_execute

        # テスト実行
        monitor.checkExecuting()

        # 検証
        # 1. ステータスが「完了（異常）」に更新されたことを確認
        updated_log = ws_db.table_data[oaseConst.T_OASE_ACTION_LOG][0]
        assert updated_log["STATUS_ID"] == oaseConst.OSTS_Completed_Abend

        # 2. ACTION_RESULTのresultがFalseに更新されたことを確認
        updated_action_result = json.loads(updated_log["ACTION_RESULT"])
        assert updated_action_result["action"]["type"] == "Conductor"
        assert updated_action_result["action"]["result"] is False
        assert updated_action_result["action"]["msg"] is None  # msg は保持される

    def test_check_executing_data_error(self, setup_test_environment):
        """異常系: データエラーの場合のテスト（ACTION_RESULT更新）"""
        env = setup_test_environment
        ws_db = env["ws_db"]
        mock_event_obj = env["mock_event_obj"]

        # 実行中ステータスのACTION_RESULTを含むテストデータ
        action_result = json.dumps({
            "action": {
                "type": "Conductor",
                "result": True,
                "msg": None
            }
        }, ensure_ascii=False)

        action_log_data = {
            "ACTION_LOG_ID": "log003",
            "RULE_ID": "rule003",
            "STATUS_ID": oaseConst.OSTS_Executing,
            "CONDUCTOR_INSTANCE_ID": "conductor003",
            "EVENT_ID_LIST": "event003",
            "ACTION_RESULT": action_result,
            "DISUSE_FLAG": "0",
            "CONCLUSION_EVENT_LABELS": '{"labels": {}, "exastro_label_key_inputs": []}',
        }

        rule_data = {
            "RULE_ID": "rule003",
            "RULE_NAME": "Test Rule 3",
            "RULE_PRIORITY": "1",
            "FILTER_A": "filter003",
            "FILTER_OPERATOR": "",
            "FILTER_B": "",
            "ACTION_ID": "action003",
            "ACTION_LABEL_INHERITANCE_FLAG": "1",
            "EVENT_LABEL_INHERITANCE_FLAG": "1",
            "CONCLUSION_LABEL_SETTINGS": "[]",
            "RULE_LABEL_NAME": "test3",
            "EVENT_ID_LIST": "event003",
            "TTL": "300",
            "AVAILABLE_FLAG": "1",
            "DISUSE_FLAG": "0",
        }

        # DummyDB のモックデータを設定
        ws_db.table_data[oaseConst.T_OASE_ACTION_LOG] = [action_log_data]
        ws_db.table_data[oaseConst.T_OASE_RULE] = [rule_data]

        # ActionStatusMonitorのインスタンス作成
        monitor = ActionStatusMonitor(ws_db, mock_event_obj)

        # sql_execute が返す JOIN 結果を上書き（データエラー: CONDUCTORレコードなし）
        original_sql_execute = ws_db.sql_execute
        def custom_sql_execute(sql, params=None):
            result = original_sql_execute(sql, params)
            for row in result:
                row["JOIN_CONDUCTOR_INSTANCE_ID"] = None  # データエラー
                row["CONDUCTOR_STATUS_ID"] = None
                row["TAB_B_DISUSE_FLAG"] = None
            return result
        ws_db.sql_execute = custom_sql_execute

        # テスト実行
        monitor.checkExecuting()

        # 検証
        # 1. ステータスが「完了（異常）」に更新されたことを確認
        updated_log = ws_db.table_data[oaseConst.T_OASE_ACTION_LOG][0]
        assert updated_log["STATUS_ID"] == oaseConst.OSTS_Completed_Abend

        # 2. ACTION_RESULTのresultがFalseに更新されたことを確認
        updated_action_result = json.loads(updated_log["ACTION_RESULT"])
        assert updated_action_result["action"]["type"] == "Conductor"
        assert updated_action_result["action"]["result"] is False

    def test_check_executing_with_invalid_action_result(self, setup_test_environment):
        """異常系: 不正なACTION_RESULT形式での完了（異常）のテスト"""
        env = setup_test_environment
        ws_db = env["ws_db"]
        mock_event_obj = env["mock_event_obj"]

        # 不正なJSON形式のACTION_RESULT
        invalid_action_result = "Invalid JSON format"

        action_log_data = {
            "ACTION_LOG_ID": "log004",
            "RULE_ID": "rule004",
            "STATUS_ID": oaseConst.OSTS_Executing,
            "CONDUCTOR_INSTANCE_ID": "conductor004",
            "EVENT_ID_LIST": "event004",
            "ACTION_RESULT": invalid_action_result,
            "DISUSE_FLAG": "0",
            "CONCLUSION_EVENT_LABELS": '{"labels": {}, "exastro_label_key_inputs": []}',
        }

        rule_data = {
            "RULE_ID": "rule004",
            "RULE_NAME": "Test Rule 4",
            "RULE_PRIORITY": "1",
            "FILTER_A": "filter004",
            "FILTER_OPERATOR": "",
            "FILTER_B": "",
            "ACTION_ID": "action004",
            "ACTION_LABEL_INHERITANCE_FLAG": "1",
            "EVENT_LABEL_INHERITANCE_FLAG": "1",
            "CONCLUSION_LABEL_SETTINGS": "[]",
            "RULE_LABEL_NAME": "test4",
            "EVENT_ID_LIST": "event004",
            "TTL": "300",
            "AVAILABLE_FLAG": "1",
            "DISUSE_FLAG": "0",
        }

        # DummyDB のモックデータを設定
        ws_db.table_data[oaseConst.T_OASE_ACTION_LOG] = [action_log_data]
        ws_db.table_data[oaseConst.T_OASE_RULE] = [rule_data]

        # ActionStatusMonitorのインスタンス作成
        monitor = ActionStatusMonitor(ws_db, mock_event_obj)

        # sql_execute が返す JOIN 結果を上書き（CONDUCTOR_STATUS_ID を異常終了に設定）
        original_sql_execute = ws_db.sql_execute
        def custom_sql_execute(sql, params=None):
            result = original_sql_execute(sql, params)
            for row in result:
                row["JOIN_CONDUCTOR_INSTANCE_ID"] = row.get("CONDUCTOR_INSTANCE_ID")
                row["CONDUCTOR_STATUS_ID"] = oaseConst.CSTS_Abend  # 異常終了
                row["TAB_B_DISUSE_FLAG"] = "0"
            return result
        ws_db.sql_execute = custom_sql_execute

        # テスト実行
        monitor.checkExecuting()

        # 検証
        # 1. 警告ログが出力されていることを確認
        warning_logs = [log for log in g.applogger.logs if log[0] == "warning"]
        assert len(warning_logs) > 0
        assert "Invalid ACTION_RESULT format" in warning_logs[0][1]

        # 2. ステータスが「完了（異常）」に更新されたことを確認
        updated_log = ws_db.table_data[oaseConst.T_OASE_ACTION_LOG][0]
        assert updated_log["STATUS_ID"] == oaseConst.OSTS_Completed_Abend

        # 3. テンプレートを使用してACTION_RESULTが更新されたことを確認
        updated_action_result = json.loads(updated_log["ACTION_RESULT"])
        assert updated_action_result["action"]["type"] is None  # テンプレートのデフォルト値
        assert updated_action_result["action"]["result"] is False
