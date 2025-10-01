# Copyright 2025 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from unittest.mock import MagicMock
from common_libs.validate.valid_110107 import external_valid_menu_before, db_filter_unique_check, db_filter_group_unique_check


@pytest.fixture
def mock_objdbca():
    """Fixture to mock objdbca."""
    return MagicMock()


@pytest.fixture
def mock_g(mocker):
    """Fixture to mock Flask's global object g."""
    mock_g_object = mocker.MagicMock()
    mock_g_object.appmsg = mocker.MagicMock()
    mock_g_object.applogger = mocker.MagicMock()

    # gオブジェクトを直接モックする
    mocker.patch('common_libs.validate.valid_110107.g', new=mock_g_object)

    return mock_g_object


@pytest.mark.parametrize(
    "cmd_type, kind_parameter, parameter, table_exists, expected_retBool, expected_msg_code",
    [
        # 登録時の正常系: 登録 (検索方法:ユニーク)
        ("Register", "entry_parameter", {"filter_condition_json": '{"key": "value"}', "search_condition_id": "1", "group_label_key_ids": None, "group_condition_id": None}, False, True, None),
        # 更新時の正常系: 更新 (検索方法:キューイング)
        ("Update", "entry_parameter", {"filter_id": "1", "filter_condition_json": '{"key": "value"}', "search_condition_id": "2", "group_label_key_ids": None, "group_condition_id": None}, False, True, None),
        # 登録時の正常系: グルーピング
        ("Register", "entry_parameter", {"filter_condition_json": '{"key": "value"}', "search_condition_id": "3", "group_label_key_ids": "group_label", "group_condition_id": "group_condition"}, False, True, None),
        # 復活時の正常系
        ("Restore", "current_parameter", {"filter_id": "2", "filter_condition_json": '{"key": "value"}', "search_condition_id": "2", "group_label_key_ids": None, "group_condition_id": None}, False, True, None),
        # 廃止時の正常系
        ("Discard", "entry_parameter", {"filter_id": "2", "filter_condition_json": '{"key": "value"}', "search_condition_id": "2", "group_label_key_ids": None, "group_condition_id": None}, False, True, None),
        # 削除時の正常系
        ("Delete", "entry_parameter", {"filter_id": "2", "filter_condition_json": '{"key": "value"}', "search_condition_id": "2", "group_label_key_ids": None, "group_condition_id": None}, False, True, None),
        # 異常系: 必須チェック失敗 (検索方法:ユニーク)
        ("Register", "entry_parameter", {"filter_condition_json": None, "search_condition_id": "1", "group_label_key_ids": None, "group_condition_id": None}, False, False, "MSG-180001"),
        ("Update", "entry_parameter", {"filter_id": "1", "filter_condition_json": None, "search_condition_id": "1", "group_label_key_ids": None, "group_condition_id": None}, False, False, "MSG-180001"),
        # 異常系: 不要チェック失敗 (検索方法:キューイング)
        ("Register", "entry_parameter", {"filter_condition_json": ["a", "b"], "search_condition_id": "2", "group_label_key_ids": ["a", "b"], "group_condition_id": None}, False, False, "MSG-180002"),
        # 異常系: 不要チェック失敗 (検索方法:ユニーク)
        ("Register", "entry_parameter", {"filter_condition_json": ["a", "b"], "search_condition_id": "1", "group_label_key_ids": [], "group_condition_id": "1"}, False, False, "MSG-180002"),
        # 異常系: 一意制約エラー (検索方法:ユニーク)
        ("Register", "entry_parameter", {"filter_condition_json": ["a", "b"], "search_condition_id": "1", "group_label_key_ids": None, "group_condition_id": None}, True, False, "MSG-180003"),
        # 異常系: 必須チェック失敗 (検索方法:グルーピング)
        ("Register", "entry_parameter", {"filter_condition_json": None, "search_condition_id": "3", "group_label_key_ids": None, "group_condition_id": None}, False, False, "MSG-180004"),
        ("Register", "entry_parameter", {"filter_condition_json": None, "search_condition_id": "3", "group_label_key_ids": ["a"], "group_condition_id": None}, False, False, "MSG-180004"),
        ("Register", "entry_parameter", {"filter_condition_json": ["a", "b"], "search_condition_id": "3", "group_label_key_ids": None, "group_condition_id": "1"}, False, False, "MSG-180004"),
        # 異常系: 一意制約エラー (検索方法:グルーピング)
        ("Register", "entry_parameter", {"filter_condition_json": None, "search_condition_id": "3", "group_label_key_ids": ["a"], "group_condition_id": "2"}, True, False, "MSG-180005"),
        ("Register", "entry_parameter", {"filter_condition_json": ["a", "b"], "search_condition_id": "3", "group_label_key_ids": ["a"], "group_condition_id": "1"}, True, False, "MSG-180005"),
        # 正常系: 検索方法が対象外
        ("Register", "entry_parameter", {"filter_condition_json": None, "search_condition_id": "X", "group_label_key_ids": None, "group_condition_id": None}, False, True, None),
    ]
)
def test_external_valid_menu_before(mock_objdbca, mock_g, cmd_type, kind_parameter, parameter, table_exists, expected_retBool, expected_msg_code):
    """Test external_valid_menu_before with parameterized inputs."""
    option = {
        "cmd_type": cmd_type,
        kind_parameter: {
            "parameter": parameter
        }
    }

    # モックの設定
    mock_objdbca.table_exists.return_value = table_exists

    retBool, msg, _ = external_valid_menu_before(mock_objdbca, None, option)

    assert retBool == expected_retBool
    if expected_msg_code:
        assert mock_g.appmsg.get_api_message.call_args.args[0] == expected_msg_code
    else:
        assert len(msg) == 0


@pytest.mark.parametrize(
    "filter_id, target_value, expected_result",
    [
        ("1", '{"key": "value"}', True),
        ("2", '{"key": "value"}', False),
    ]
)
def test_db_filter_unique_check(mock_objdbca, filter_id, target_value, expected_result):
    """Test db_filter_unique_check with parameterized inputs."""
    mock_objdbca.table_exists.return_value = expected_result

    result = db_filter_unique_check(mock_objdbca, filter_id, target_value)

    assert result == expected_result
    mock_objdbca.table_exists.assert_called_once_with(
        "T_OASE_FILTER",
        " where `FILTER_CONDITION_JSON` = %s and `FILTER_ID` <> %s and `SEARCH_CONDITION_ID` <> %s and `DISUSE_FLAG` == 0 ",
        [target_value, filter_id, "3"]
    )


@pytest.mark.parametrize(
    "filter_id, target_value, group_label_key_ids, group_condition_id, expected_result",
    [
        ("1", '{"key": "value"}', "group_label", "group_condition", True),
        ("2", '{"key": "value"}', "group_label", "group_condition", False),
    ]
)
def test_db_filter_group_unique_check(mock_objdbca, filter_id, target_value, group_label_key_ids, group_condition_id, expected_result):
    """Test db_filter_group_unique_check with parameterized inputs."""
    mock_objdbca.table_exists.return_value = expected_result

    result = db_filter_group_unique_check(mock_objdbca, filter_id, target_value, group_label_key_ids, group_condition_id)

    if target_value is None:
        where_str = " where `GROUP_LABEL_KEY_IDS` = %s and `GROUP_CONDITION_ID` = %s and `FILTER_ID` <> %s and `SEARCH_CONDITION_ID` = %s and `DISUSE_FLAG` == 0 "
        bind_str = [group_label_key_ids, group_condition_id, filter_id, "3"]
    else:
        where_str = " where `GROUP_LABEL_KEY_IDS` = %s and `GROUP_CONDITION_ID` = %s and `FILTER_CONDITION_JSON` = %s and `FILTER_ID` <> %s and `SEARCH_CONDITION_ID` = %s and `DISUSE_FLAG` == 0 "
        bind_str = [group_label_key_ids, group_condition_id, target_value, filter_id, "3"]

    assert result == expected_result
    mock_objdbca.table_exists.assert_called_once_with(
        "T_OASE_FILTER",
        where_str,
        bind_str
    )
