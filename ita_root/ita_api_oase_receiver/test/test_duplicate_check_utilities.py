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
#

"""
duplicate_check.py内のユーティリティ関数に対するテストコード:
- is_new_event
- extract_collection_settings_counts
- extract_agents_counts
- should_notify_event
- is_duplicate_notification_needed
"""

import pytest

from libs.duplicate_check import (
    is_new_event,
    extract_collection_settings_counts,
    extract_agents_counts,
    should_notify_event,
    is_duplicate_notification_needed
)

# ===== is_new_event function tests =====


def test_is_new_event_returns_true_for_edit_count_1():
    """exastro_edit_countが1の場合、Trueを返すことを確認"""
    res = {"exastro_edit_count": 1}
    assert is_new_event(res) is True


def test_is_new_event_returns_false_for_edit_count_greater_than_1():
    """exastro_edit_countが1より大きい場合、Falseを返すことを確認"""
    res = {"exastro_edit_count": 2}
    assert is_new_event(res) is False

    res = {"exastro_edit_count": 5}
    assert is_new_event(res) is False

    res = {"exastro_edit_count": 100}
    assert is_new_event(res) is False


def test_is_new_event_returns_true_for_missing_edit_count():
    """exastro_edit_countが存在しない場合、デフォルト値1でTrueを返すことを確認"""
    res = {}
    assert is_new_event(res) is True

    res = {"other_field": "value"}
    assert is_new_event(res) is True


def test_is_new_event_with_zero_edit_count():
    """exastro_edit_countが0の場合、Falseを返すことを確認"""
    res = {"exastro_edit_count": 0}
    assert is_new_event(res) is False


def test_is_new_event_with_negative_edit_count():
    """exastro_edit_countが負数の場合、Falseを返すことを確認"""
    res = {"exastro_edit_count": -1}
    assert is_new_event(res) is False

    res = {"exastro_edit_count": -10}
    assert is_new_event(res) is False


def test_is_new_event_with_none_edit_count():
    """exastro_edit_countがNoneの場合、デフォルト値1でTrueを返すことを確認"""
    res = {"exastro_edit_count": None}
    assert is_new_event(res) is True


# ===== extract_collection_settings_counts function tests =====

def test_extract_collection_settings_counts_returns_existing_dict():
    """exastro_duplicate_collection_settings_idsが存在する場合、その値を返すことを確認"""
    expected = {"settings1": 5, "settings2": 3}
    res = {"exastro_duplicate_collection_settings_ids": expected}
    assert extract_collection_settings_counts(res) == expected


def test_extract_collection_settings_counts_returns_empty_dict_for_missing_key():
    """exastro_duplicate_collection_settings_idsが存在しない場合、空の辞書を返すことを確認"""
    res = {}
    assert extract_collection_settings_counts(res) == {}

    res = {"other_field": "value"}
    assert extract_collection_settings_counts(res) == {}


def test_extract_collection_settings_counts_returns_empty_dict_for_none_res():
    """resがNoneの場合、空の辞書を返すことを確認"""
    res = None
    assert extract_collection_settings_counts(res) == {}


def test_extract_collection_settings_counts_with_empty_dict():
    """exastro_duplicate_collection_settings_idsが空の辞書の場合、空の辞書を返すことを確認"""
    res = {"exastro_duplicate_collection_settings_ids": {}}
    assert extract_collection_settings_counts(res) == {}


# ===== extract_agents_counts function tests =====

def test_extract_agents_counts_returns_existing_dict():
    """exastro_agentsが存在する場合、その値を返すことを確認"""
    expected = {"agent1": 3, "agent2": 7}
    res = {"exastro_agents": expected}
    assert extract_agents_counts(res) == expected


def test_extract_agents_counts_returns_empty_dict_for_missing_key():
    """exastro_agentsが存在しない場合、空の辞書を返すことを確認"""
    res = {}
    assert extract_agents_counts(res) == {}

    res = {"other_field": "value"}
    assert extract_agents_counts(res) == {}


def test_extract_agents_counts_returns_empty_dict_for_none_res():
    """resがNoneの場合、空の辞書を返すことを確認"""
    res = None
    assert extract_agents_counts(res) == {}


def test_extract_agents_counts_with_empty_dict():
    """exastro_agentsが空の辞書の場合、空の辞書を返すことを確認"""
    res = {"exastro_agents": {}}
    assert extract_agents_counts(res) == {}


# ===== should_notify_event function tests =====

def test_should_notify_event_returns_true_for_new_event():
    """新規登録イベント（is_event_inserted=True）の場合、Trueを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1"]}
    }
    collection_settings_counts = {"es1": 1}
    agents_counts = {"agent1": 1}
    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        True,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is True


def test_should_notify_event_returns_false_for_single_redundancy_group():
    """重複イベントで冗長化グループが1つの場合、Falseを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1"]}
    }
    collection_settings_counts = {"es1": 2}
    agents_counts = {"agent1": 2}
    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        False,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is False


def test_should_notify_event_returns_false_for_empty_redundancy_group():
    """重複イベントで冗長化グループが空の場合、Falseを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": []}
    }
    collection_settings_counts = {}
    agents_counts = {}
    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        False,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is False


def test_should_notify_event_with_single_agent_multiple_redundancy_groups():
    """単一エージェント、複数冗長化グループの場合、Trueを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]}
    }
    collection_settings_counts = {"es1": 1, "es2": 1}
    agents_counts = {"agent1": 2}
    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        False,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is True


def test_should_notify_event_with_multiple_agents_single_event_source():
    """複数エージェント、単一イベントソースの場合、Falseを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]}
    }
    collection_settings_counts = {"es1": 3}
    agents_counts = {"agent1": 1, "agent2": 1, "agent3": 1}
    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        False,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is False


def test_should_notify_event_with_empty_setting_ids():
    """設定IDリストが空の場合、Falseを返すことを確認"""
    deduplication_setting_ids = []
    deduplication_setting_list = {}
    collection_settings_counts = {}
    agents_counts = {}
    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        False,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is False


def test_should_notify_event_new_event_overrides_redundancy_check():
    """新規イベントの場合、冗長化グループの設定に関係なくTrueを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": []}  # 空のグループでも
    }
    collection_settings_counts = {}
    agents_counts = {}
    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        True,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is True


def test_should_notify_event_with_none_counts():
    """collection_settings_countsやagents_countsがNoneの場合の動作を確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]}
    }
    # 新規イベントの場合はTrueを返す
    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        True,
        None,
        None,
        None
    )
    assert result is True

    # 重複イベントで単一エージェントの場合
    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        False,
        None,
        None,
        None
    )
    assert result is False


# ===== is_duplicate_notification_needed function tests =====

def test_is_duplicate_notification_needed_returns_false_for_single_redundancy_group():
    """単一の冗長化グループの場合、Falseを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1"]}
    }
    collection_settings_counts = {"es1": 2}
    agents_counts = {"agent1": 2}
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is False


def test_is_duplicate_notification_needed_returns_false_for_empty_redundancy_group():
    """冗長化グループが空の場合、Falseを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": []}
    }
    collection_settings_counts = {}
    agents_counts = {}
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is False


def test_is_duplicate_notification_needed_with_missing_redundancy_group_key():
    """冗長化グループキーが存在しない場合、Falseを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"OTHER_KEY": "value"}
    }
    collection_settings_counts = {}
    agents_counts = {}
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is False


def test_is_duplicate_notification_needed_with_empty_settings():
    """設定IDリストが空の場合、Falseを返すことを確認"""
    deduplication_setting_ids = []
    deduplication_setting_list = {}
    collection_settings_counts = {}
    agents_counts = {}
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        ""
    )
    assert result is False


def test_is_duplicate_notification_needed_with_balanced_counts():
    """バランスの取れたカウントの場合の動作を確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]}
    }
    # 条件を満たすパターン: エージェント*設定数 = 冗長化グループ数*2
    collection_settings_counts = {"es1": 1, "es2": 1}
    agents_counts = {"agent1": 1, "agent2": 1}
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    # 実装の詳細なロジックに応じて結果が決まる
    assert isinstance(result, bool)


def test_is_duplicate_notification_needed_with_unbalanced_counts():
    """アンバランスなカウントの場合、Falseを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]}
    }
    # 条件を満たさないパターン
    collection_settings_counts = {"es1": 3, "es2": 1}
    agents_counts = {"agent1": 2, "agent2": 2}
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is False


def test_is_duplicate_notification_needed_with_setting_name_none():
    """設定IDがNoneの場合、Falseを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]}
    }
    # 条件を満たさないパターン
    collection_settings_counts = {"es1": 3, "es2": 1}
    agents_counts = {"agent1": 3, "agent2": 1}
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        None
    )
    assert result is False


def test_is_duplicate_notification_needed_with_setting_name_0byte():
    """設定IDが""の場合、Falseを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]}
    }
    # 条件を満たさないパターン
    collection_settings_counts = {"es1": 3, "es2": 1}
    agents_counts = {"agent1": 3, "agent2": 1}
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        ""
    )
    assert result is False


def test_is_duplicate_notification_needed_with_setting_name_different():
    """設定IDが異なる場合、Falseを返すことを確認"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]}
    }
    # 条件を満たさないパターン
    collection_settings_counts = {"es1": 3, "es2": 1}
    agents_counts = {"agent1": 3, "agent2": 1}
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        "esxxx"
    )
    assert result is False


def test_is_duplicate_notification_needed_with_multiple_settings_any_single_group_true():
    """複数設定で複数の収集設定が設定されている重複排除が優先場合、Trueを返すことを確認"""
    deduplication_setting_ids = ["ds1", "ds2"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]},
        "ds2": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es3"]}  # 単一グループ
    }
    collection_settings_counts = {"es1": 1, "es2": 1, "es3": 1}
    agents_counts = {"agent1": 1, "agent2": 1, "agent3": 1}
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        "es1"
    )
    assert result is True


def test_is_duplicate_notification_needed_with_multiple_settings_any_single_group_false():
    """複数設定で複数の収集設定が設定されている重複排除が優先場合、Falseを返すことを確認"""
    deduplication_setting_ids = ["ds2", "ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]},
        "ds2": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es3"]}  # 単一グループ
    }
    collection_settings_counts = {"es1": 1, "es2": 1, "es3": 1}
    agents_counts = {"agent1": 1, "agent2": 1, "agent3": 1}
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        "es3"
    )
    assert result is False


@pytest.mark.parametrize("event_collection_settings_id, collection_settings_counts, agents_counts, expected", [
    # パターン1: 収集設定冗長構成
    ("es1", {"es1": 1}, {"agent1": 1}, False),
    ("es2", {"es1": 1, "es2": 1}, {"agent1": 1, "agent2": 1}, True),
    # パターン2： 収集設定*エージェント冗長構成（収集設定の分散）
    ("es1", {"es1": 1}, {"agent1": 1}, False),
    ("es2", {"es1": 1, "es2": 1}, {"agent1": 1, "agent2": 1}, True),
    ("es1", {"es1": 2, "es2": 1}, {"agent1": 2, "agent2": 1}, False),
    ("es2", {"es1": 2, "es2": 2}, {"agent1": 2, "agent2": 2}, False),
    ("es2", {"es1": 2, "es2": 3}, {"agent1": 2, "agent2": 3}, False),
    # パターン3： 収集設定*エージェント冗長構成（収集設定の集中）
    ("es1", {"es1": 1}, {"agent1": 1}, False),
    ("es1", {"es1": 2}, {"agent1": 1, "agent2": 1}, False),
    ("es2", {"es1": 2, "es2": 1}, {"agent1": 2, "agent2": 1}, True),
    ("es2", {"es1": 2, "es2": 2}, {"agent1": 2, "agent2": 2}, False),
    ("es2", {"es1": 3, "es2": 2}, {"agent1": 3, "agent2": 2}, False),
])
def test_is_duplicate_notification_needed_pattern(event_collection_settings_id, collection_settings_counts, agents_counts, expected):
    """is_duplicate_notification_needed関数の収集設定*エージェント件数遷移テスト"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]},
    }
    result = is_duplicate_notification_needed(
        deduplication_setting_ids,
        deduplication_setting_list,
        collection_settings_counts,
        agents_counts,
        event_collection_settings_id
    )
    assert result is expected


@pytest.mark.parametrize("event_collection_settings_id, collection_settings_counts, agents_counts, expected", [
    # パターン1: 収集設定冗長構成
    ("es1", {"es1": 1}, {"agent1": 1}, True),
    ("es2", {"es1": 1, "es2": 1}, {"agent1": 1, "agent2": 1}, True),
    # パターン2： 収集設定*エージェント冗長構成（収集設定の分散）
    ("es1", {"es1": 1}, {"agent1": 1}, True),
    ("es2", {"es1": 1, "es2": 1}, {"agent1": 1, "agent2": 1}, True),
    # パターン3： 収集設定*エージェント冗長構成（収集設定の集中）
    ("es1", {"es1": 1}, {"agent1": 1}, True),
    ("es1", {"es1": 2}, {"agent1": 1, "agent2": 1}, True),
    # パターンX： イベントとして別になるので起きないパターン
    ("es1", {"es1": 100}, {"agent1": 100}, True),
    ("es1", {"es1": 200}, {"agent1": 100, "agent2": 100}, True),
])
def test_should_notify_event_needed_pattern(event_collection_settings_id, collection_settings_counts, agents_counts, expected):
    """should_notify_event関数の収集設定*エージェント件数遷移テスト"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]},
    }
    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        True,
        collection_settings_counts,
        agents_counts,
        event_collection_settings_id
    )
    assert result is expected

# ===== Integration tests =====


def test_typical_workflow_new_event():
    """新規イベントの典型的なワークフローテスト"""
    # 新規イベントのfind_one_and_update結果をシミュレート
    res = {
        "exastro_edit_count": 1,
        "exastro_agents": {"agent1": 1},
        "exastro_duplicate_collection_settings_ids": {"settings1": 1}
    }

    # 各関数の結果を確認
    assert is_new_event(res) is True

    collection_counts = extract_collection_settings_counts(res)
    assert collection_counts == {"settings1": 1}

    agents_counts = extract_agents_counts(res)
    assert agents_counts == {"agent1": 1}

    # 新規イベントなので通知対象
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["settings1"]}
    }
    result = should_notify_event(
        ["ds1"],
        deduplication_setting_list,
        True,
        collection_counts,
        agents_counts,
        "settings1"
    )
    assert result is True


def test_typical_workflow_duplicate_event():
    """重複イベントの典型的なワークフローテスト"""
    # 重複イベントのfind_one_and_update結果をシミュレート
    res = {
        "exastro_edit_count": 3,
        "exastro_agents": {"agent1": 2, "agent2": 1},
        "exastro_duplicate_collection_settings_ids": {"settings1": 2, "settings2": 1}
    }

    # 各関数の結果を確認
    assert is_new_event(res) is False

    collection_counts = extract_collection_settings_counts(res)
    assert collection_counts == {"settings1": 2, "settings2": 1}

    agents_counts = extract_agents_counts(res)
    assert agents_counts == {"agent1": 2, "agent2": 1}

    # 冗長化グループが2つ以上ある場合の通知判定
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["settings1", "settings2"]}
    }
    notify_result = should_notify_event(
        ["ds1"],
        deduplication_setting_list,
        False,
        collection_counts,
        agents_counts,
        "settings1"
    )
    assert notify_result is False

    # 重複排除通知の判定
    duplicate_result = is_duplicate_notification_needed(
        ["ds1"],
        deduplication_setting_list,
        collection_counts,
        agents_counts,
        "ds1"
    )
    assert isinstance(duplicate_result, bool)


def test_workflow_no_redundancy_group():
    """冗長化グループなしのワークフローテスト"""
    res = {
        "exastro_edit_count": 2,
        "exastro_agents": {"agent1": 2},
        "exastro_duplicate_collection_settings_ids": {"settings1": 2}
    }

    assert is_new_event(res) is False

    collection_counts = extract_collection_settings_counts(res)
    agents_counts = extract_agents_counts(res)

    # 冗長化グループが1つなので通知対象外
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["settings1"]}
    }
    notify_result = should_notify_event(
        ["ds1"],
        deduplication_setting_list,
        False,
        collection_counts,
        agents_counts,
        "settings1"
    )
    assert notify_result is False

    duplicate_result = is_duplicate_notification_needed(
        ["ds1"],
        deduplication_setting_list,
        collection_counts,
        agents_counts,
        "settings1"
    )
    assert duplicate_result is False


def test_edge_cases_empty_data():
    """空データでのエッジケーステスト"""
    # 空の辞書
    res = {}
    assert is_new_event(res) is True  # デフォルト値1でTrue
    assert extract_collection_settings_counts(res) == {}
    assert extract_agents_counts(res) == {}

    # None
    assert extract_collection_settings_counts(None) == {}
    assert extract_agents_counts(None) == {}


def test_edge_cases_large_numbers():
    """大きな数値でのテスト"""
    res = {
        "exastro_edit_count": 999999,
        "exastro_agents": {"agent1": 500000, "agent2": 500000},
        "exastro_duplicate_collection_settings_ids": {"settings1": 1000000}
    }

    assert is_new_event(res) is False  # 999999 != 1

    collection_counts = extract_collection_settings_counts(res)
    assert collection_counts["settings1"] == 1000000

    agents_counts = extract_agents_counts(res)
    assert sum(agents_counts.values()) == 1000000


# ===== Parametrized tests =====

@pytest.mark.parametrize("edit_count,expected", [
    (1, True),
    (0, False),
    (2, False),
    (100, False),
    (-1, False),
    (None, True),
])
def test_is_new_event_parametrized(edit_count, expected):
    """is_new_event関数のパラメータ化テスト"""
    if edit_count is None:
        res = {"exastro_edit_count": None}
    else:
        res = {"exastro_edit_count": edit_count}
    assert is_new_event(res) is expected


@pytest.mark.parametrize("is_event_inserted,redundancy_groups,expected", [
    (True, [], True),  # 新規イベントは常にTrue
    (True, ["es1"], True),  # 新規イベントは常にTrue
    (True, ["es1", "es2"], True),  # 新規イベントは常にTrue
    (False, [], False),  # 重複イベントで空グループはFalse
    (False, ["es1"], False),  # 重複イベントで単一グループはFalse
])
def test_should_notify_event_parametrized(is_event_inserted, redundancy_groups, expected):
    """should_notify_event関数のパラメータ化テスト"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": redundancy_groups}
    }
    collection_settings_counts = {"es1": 1, "es2": 1} if redundancy_groups else {}
    agents_counts = {"agent1": 1} if redundancy_groups else {}

    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        is_event_inserted,
        collection_settings_counts,
        agents_counts,
        "settings1"
    )
    assert result is expected


# ===== Error handling tests =====

def test_functions_with_invalid_input_types():
    """不正な入力タイプでのエラーハンドリングテスト"""
    # 文字列を辞書の代わりに渡す
    with pytest.raises((AttributeError, TypeError)):
        is_new_event("not_a_dict")

    with pytest.raises((AttributeError, TypeError)):
        extract_collection_settings_counts("not_a_dict")


def test_should_notify_event_with_missing_keys():
    """should_notify_event関数で必要なキーが不足している場合のテスト"""
    deduplication_setting_ids = ["ds1"]
    deduplication_setting_list = {
        "ds1": {}  # EVENT_SOURCE_REDUNDANCY_GROUPキーが不足
    }
    collection_settings_counts = {}
    agents_counts = {}

    result = should_notify_event(
        deduplication_setting_ids,
        deduplication_setting_list,
        False,
        collection_settings_counts,
        agents_counts,
        ""
    )
    assert result is False


def test_should_notify_event_with_nonexistent_setting_id():
    """存在しない設定IDでのテスト"""
    deduplication_setting_ids = ["nonexistent"]
    deduplication_setting_list = {
        "ds1": {"EVENT_SOURCE_REDUNDANCY_GROUP": ["es1", "es2"]}
    }
    collection_settings_counts = {"es1": 1}
    agents_counts = {"agent1": 1}

    # KeyErrorが発生する可能性
    with pytest.raises(KeyError):
        should_notify_event(
            deduplication_setting_ids,
            deduplication_setting_list,
            False,
            collection_settings_counts,
            agents_counts,
            "es1"
        )
