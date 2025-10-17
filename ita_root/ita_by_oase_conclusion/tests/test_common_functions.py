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
import json
from unittest import mock
from libs.common_functions import deduplication_timeout_filter


class TestDeduplicationTimeoutFilter:

    @pytest.fixture
    def mock_db(self):
        """DBモックの作成"""
        mock_db = mock.MagicMock()
        return mock_db

    # データ上はあり得るケース
    def test_event_missing_required_source(self, app_context_with_mock_g):
        """重複排除設定の冗長グループの内、片方がイベントのexastro_duplicate_collection_settings_idsに含まれていない場合"""
        # Set up mock deduplication settings
        deduplication_settings = [
            {
                "DEDUPLICATION_SETTING_ID": "dedup1",
                "DEDUPLICATION_SETTING_NAME": "Test Setting",
                "SETTING_PRIORITY": 1,
                "EVENT_SOURCE_REDUNDANCY_GROUP": json.dumps({"id": ["source1", "source2"]})
            }
        ]

        # Sample event list with an event missing source2
        event = {
            "_id": "event123",
            "labels": {"_exastro_event_collection_settings_id": "source1"},
            "exastro_duplicate_collection_settings_ids": {"source1": 1}
        }

        # Call the function
        result_flg = deduplication_timeout_filter(deduplication_settings, event)

        # Assertions
        assert result_flg is True  # アラート対象であること
        app_context_with_mock_g.applogger.debug.assert_any_call("EventID:event123 is an event that should be put into the deduplication timeout notification queue.")  # ログに出ていること

    def test_event_with_source_value_zero(self, app_context_with_mock_g):
        """重複排除設定の冗長グループの内、片方がイベントのexastro_duplicate_collection_settings_idsに値0で含まれている場合"""
        # Set up mock deduplication settings
        deduplication_settings = [
            {
                "DEDUPLICATION_SETTING_ID": "dedup1",
                "DEDUPLICATION_SETTING_NAME": "Test Setting",
                "SETTING_PRIORITY": 1,
                "EVENT_SOURCE_REDUNDANCY_GROUP": json.dumps({"id": ["source1", "source2"]})
            }
        ]

        # Sample event list with source2 having value 0
        event = {
            "_id": "event123",
            "labels": {"_exastro_event_collection_settings_id": "source1"},
            "exastro_duplicate_collection_settings_ids": {"source1": 1, "source2": 0}
        }

        # Call the function
        result_flg = deduplication_timeout_filter(deduplication_settings, event)

        # Assertions
        assert result_flg is True  # アラート対象であること
        app_context_with_mock_g.applogger.debug.assert_any_call("EventID:event123 is an event that should be put into the deduplication timeout notification queue.")  # ログに出ていること

    def test_event_with_all_sources_present(self, mock_db, app_context_with_mock_g):
        """重複排除設定の冗長グループの内、全てがイベントのexastro_duplicate_collection_settings_idsに値1以上で含まれている場合"""
        # Set up mock deduplication settings
        deduplication_settings = [
            {
                "DEDUPLICATION_SETTING_ID": "dedup1",
                "DEDUPLICATION_SETTING_NAME": "Test Setting",
                "SETTING_PRIORITY": 1,
                "EVENT_SOURCE_REDUNDANCY_GROUP": json.dumps({"id": ["source1", "source2"]})
            }
        ]

        # Sample event list with all sources having values >= 1
        event = {
            "_id": "event123",
            "labels": {"_exastro_event_collection_settings_id": "source1"},
            "exastro_duplicate_collection_settings_ids": {"source1": 1, "source2": 2}
        }

        # Call the function
        result_flg = deduplication_timeout_filter(deduplication_settings, event)

        # Assertions
        assert result_flg is False  # アラート対象でないこと

    def test_multiple_deduplication_settings(self, mock_db, app_context_with_mock_g):
        """重複排除設定の冗長グループの内、単一の収集先が複数の冗長グループに入っている場合"""
        # Set up mock deduplication settings
        deduplication_settings = [
            {
                "DEDUPLICATION_SETTING_ID": "dedup1",
                "DEDUPLICATION_SETTING_NAME": "High Priority Setting",
                "SETTING_PRIORITY": 1,
                "EVENT_SOURCE_REDUNDANCY_GROUP": json.dumps({"id": ["source1", "source2"]})
            },
            {
                "DEDUPLICATION_SETTING_ID": "dedup2",
                "DEDUPLICATION_SETTING_NAME": "Low Priority Setting",
                "SETTING_PRIORITY": 2,
                "EVENT_SOURCE_REDUNDANCY_GROUP": json.dumps({"id": ["source1", "source3"]})
            }
        ]

        # Sample event list - source1 should use the higher priority setting (dedup1)
        event = {
            "_id": "event123",
            "labels": {"_exastro_event_collection_settings_id": "source1"},
            "exastro_duplicate_collection_settings_ids": {"source1": 1, "source3": 1}
            # source2 is missing
        }

        # Call the function
        result_flg = deduplication_timeout_filter(deduplication_settings, event)

        # Assertions
        assert result_flg is True  # アラート対象であること
        app_context_with_mock_g.applogger.debug.assert_any_call("EventID:event123 is an event that should be put into the deduplication timeout notification queue.")  # ログに出ていること

    def test_collection_id_not_in_settings(self, mock_db, app_context_with_mock_g):
        """重複排除設定の冗長グループに含まれない収集先からのイベントの場合"""
        # Set up mock deduplication settings
        deduplication_settings = [
            {
                "DEDUPLICATION_SETTING_ID": "dedup1",
                "DEDUPLICATION_SETTING_NAME": "Test Setting",
                "SETTING_PRIORITY": 1,
                "EVENT_SOURCE_REDUNDANCY_GROUP": json.dumps({"id": ["source1", "source2"]})
            }
        ]

        # Sample event list with unknown collection ID
        event = {
            "_id": "event123",
            "labels": {"_exastro_event_collection_settings_id": "source99"}
        }

        # Call the function
        result_flg = deduplication_timeout_filter(deduplication_settings, event)

        # Assertions
        assert result_flg is False  # アラート対象でないこと

    def test_single_source_redundancy_group(self, mock_db, app_context_with_mock_g):
        """重複排除設定の冗長グループに単一の収集先のみが含まれている場合"""
        # Set up mock deduplication settings with single source in redundancy group
        deduplication_settings = [
            {
                "DEDUPLICATION_SETTING_ID": "dedup1",
                "DEDUPLICATION_SETTING_NAME": "Single Source Setting",
                "SETTING_PRIORITY": 1,
                "EVENT_SOURCE_REDUNDANCY_GROUP": json.dumps({"id": ["source1"]})
            }
        ]

        # テストケース1: ソースが存在し値が1以上の場合
        event = {
            "_id": "event1",
            "labels": {"_exastro_event_collection_settings_id": "source1"},
            "exastro_duplicate_collection_settings_ids": {"source1": 1}
        }

        # Call the function
        result_flg = deduplication_timeout_filter(deduplication_settings, event)

        # Assertions
        assert result_flg is False  # アラート対象でないこと
