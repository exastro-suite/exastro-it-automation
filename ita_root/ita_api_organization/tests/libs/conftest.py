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

"""
テスト用の共通フィクスチャ
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_objdbca():
    """DBアクセスオブジェクトのモック"""
    mock = MagicMock()
    mock.table_select = MagicMock()
    return mock


@pytest.fixture
def mock_g_with_roles(app_context_with_mock_g):
    """g.ROLES と g.LANGUAGE を設定するフィクスチャ"""
    from flask import g
    g.ROLES = ['role1']
    g.LANGUAGE = 'ja'
    g.appmsg.get_api_message.return_value = "権限エラーメッセージ"
    g.applogger = MagicMock()
    yield
