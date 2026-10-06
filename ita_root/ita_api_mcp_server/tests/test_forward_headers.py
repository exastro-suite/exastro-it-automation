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
libs/forward_headers.py (get_downstream_timeout) のユニットテスト
"""

import pytest

from libs.forward_headers import get_downstream_timeout


class TestGetDownstreamTimeout:
    def test_apache_timeout_plus_30_seconds(self, monkeypatch):
        # 正常系: APACHE_TIMEOUTの値に30秒を加えた値が返ること
        monkeypatch.setenv("APACHE_TIMEOUT", "120")
        assert get_downstream_timeout() == 150

    def test_default_when_unset(self, monkeypatch):
        # 境界値: APACHE_TIMEOUT未設定の場合は既定値(300)+30秒となること
        monkeypatch.delenv("APACHE_TIMEOUT", raising=False)
        assert get_downstream_timeout() == 330

    @pytest.mark.parametrize("value", ["", "abc", "1.5"])
    def test_default_when_invalid(self, monkeypatch, value):
        # 異常系: 整数として解釈できない値の場合は既定値(300)+30秒となること
        monkeypatch.setenv("APACHE_TIMEOUT", value)
        assert get_downstream_timeout() == 330
