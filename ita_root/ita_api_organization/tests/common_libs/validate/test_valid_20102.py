# Copyright 2026 NEC Corporation
#
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

from common_libs.validate.valid_20102 import _check_aap_host_list_nodes


@pytest.fixture
def mock_objdbca():
    """objdbca をモックする Fixture"""
    return MagicMock()


@pytest.fixture
def mock_g(mocker):
    """Flask のグローバルオブジェクト g をモックする Fixture"""
    mock_g_object = mocker.MagicMock()
    mock_g_object.appmsg = mocker.MagicMock()
    # get_api_message はメッセージコードをそのまま返すようにし、戻り値の伝播を検証可能にする
    mock_g_object.appmsg.get_api_message.side_effect = lambda code, args=None: code
    mock_g_object.applogger = mocker.MagicMock()

    # valid_20102 が参照する g を直接差し替える
    mocker.patch("common_libs.validate.valid_20102.g", new=mock_g_object)

    return mock_g_object


def _make_host_row(host_id, host_name, auth_type, user):
    """t_ansc_tower_host の1レコード(dict)を生成するヘルパー"""
    return {
        "ANSTWR_HOST_ID": host_id,
        "ANSTWR_HOSTNAME": host_name,
        "ANSTWR_LOGIN_AUTH_TYPE": auth_type,
        "ANSTWR_LOGIN_USER": user,
    }


@pytest.mark.parametrize(
    "rows, expected_ret, expected_targets",
    [
        # 正常系: 対象ホストが0件
        ([], True, []),
        # 正常系: 全ホストが認証方式・ユーザともに設定済み
        (
            [
                _make_host_row("1", "host1", "1", "user1"),
                _make_host_row("2", "host2", "2", "user2"),
            ],
            True,
            [],
        ),
        # 異常系: ユーザ未設定(None)
        ([_make_host_row("1", "host1", "1", None)], False, ["host1(1)"]),
        # 異常系: ユーザ未設定(空文字)
        ([_make_host_row("1", "host1", "1", "")], False, ["host1(1)"]),
        # 異常系: 認証方式未設定(None)
        ([_make_host_row("2", "host2", None, "user2")], False, ["host2(2)"]),
        # 異常系: 認証方式未設定(空文字)
        ([_make_host_row("2", "host2", "", "user2")], False, ["host2(2)"]),
        # 異常系: 認証方式・ユーザの両方が未設定
        ([_make_host_row("3", "host3", None, None)], False, ["host3(3)"]),
        # 異常系: 複数ホストが未設定(順序どおりに列挙される)
        (
            [
                _make_host_row("1", "host1", None, "user1"),
                _make_host_row("2", "host2", "2", None),
            ],
            False,
            ["host1(1)", "host2(2)"],
        ),
        # 混在: 正常ホストと未設定ホスト → 未設定ホストのみ検出される
        (
            [
                _make_host_row("1", "host1", "1", "user1"),
                _make_host_row("2", "host2", None, None),
                _make_host_row("3", "host3", "3", "user3"),
            ],
            False,
            ["host2(2)"],
        ),
    ],
)
def test_check_aap_host_list_nodes(mock_objdbca, mock_g, rows, expected_ret, expected_targets):
    """認証方式・ユーザの設定状況に応じて判定結果とメッセージが返ることを確認する"""
    mock_objdbca.table_select.return_value = rows

    ret, msg = _check_aap_host_list_nodes(mock_objdbca)

    assert ret is expected_ret
    if expected_ret:
        # 正常時はメッセージなし・メッセージ生成も呼ばれない
        assert msg == ""
        mock_g.appmsg.get_api_message.assert_not_called()
    else:
        # 未設定ホストを列挙して MSG-11016 でメッセージ生成していることを確認する
        mock_g.appmsg.get_api_message.assert_called_once_with(
            "MSG-11016", [", ".join(expected_targets)]
        )
        # get_api_message の戻り値がそのままメッセージとして返る
        assert msg == "MSG-11016"


def test_check_aap_host_list_nodes_query(mock_objdbca, mock_g):
    """有効(DISUSE_FLAG=0)なホスト一覧を正しい条件で取得していることを確認する"""
    mock_objdbca.table_select.return_value = []

    _check_aap_host_list_nodes(mock_objdbca)

    mock_objdbca.table_select.assert_called_once_with(
        "t_ansc_tower_host", "WHERE DISUSE_FLAG = %s", ["0"]
    )
