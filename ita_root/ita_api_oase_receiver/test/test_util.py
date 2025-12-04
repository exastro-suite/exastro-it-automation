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
import sys
from unittest.mock import patch, MagicMock

# Flask の g オブジェクトをモックして sys.modules に追加
flask_mock = MagicMock()
g_mock = MagicMock()
flask_mock.g = g_mock
sys.modules['flask'] = flask_mock

from common_libs.common.util import get_tmp_file_path  # noqa: E402


class TestGetTmpFilePath:
    """get_tmp_file_path関数のテストクラス"""

    @patch('common_libs.common.util.uuid_lib.uuid4')
    def test_get_tmp_file_path_success(self, mock_uuid):
        """get_tmp_file_pathの正常系テスト"""
        # モックの設定
        g_mock.get.return_value = "test_org_id"
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(
            return_value="test-uuid-1234")

        # 実行
        result = get_tmp_file_path("workspace_001", "test_file.txt")

        # 検証
        expected = ("/tmp/test_org_id/workspace_001/tmp/"
                    "test-uuid-1234/test_file.txt")
        assert result == {"file_path": expected}
        g_mock.get.assert_called_with("ORGANIZATION_ID")

    @patch('common_libs.common.util.uuid_lib.uuid4')
    def test_get_tmp_file_path_different_inputs(self, mock_uuid):
        """異なる入力パラメータでのテスト"""
        # モックの設定
        g_mock.get.return_value = "org123"
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(
            return_value="abcd-efgh-ijkl")

        # 実行
        result = get_tmp_file_path("ws_999", "document.pdf")

        # 検証
        expected = "/tmp/org123/ws_999/tmp/abcd-efgh-ijkl/document.pdf"
        assert result == {"file_path": expected}

    @patch('common_libs.common.util.uuid_lib.uuid4')
    def test_get_tmp_file_path_none_organization_id(self, mock_uuid):
        """organization_idがNoneの場合のテスト"""
        # モックの設定
        g_mock.get.return_value = None
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(return_value="test-uuid")

        # 実行
        result = get_tmp_file_path("workspace_001", "test.txt")

        # 検証 - Noneは除外されるため、organization_idの部分が省かれる
        expected = "/tmp/workspace_001/tmp/test-uuid/test.txt"
        assert result == {"file_path": expected}

    @patch('common_libs.common.util.uuid_lib.uuid4')
    def test_get_tmp_file_path_special_characters(self, mock_uuid):
        """特殊文字を含むファイル名のテスト"""
        # モックの設定
        g_mock.get.return_value = "test_org"
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(return_value="uuid123")

        # 実行
        result = get_tmp_file_path("workspace_001", "file with spaces.txt")

        # 検証
        expected = ("/tmp/test_org/workspace_001/tmp/uuid123/"
                    "file with spaces.txt")
        assert result == {"file_path": expected}

    @patch('common_libs.common.util.uuid_lib.uuid4')
    def test_get_tmp_file_path_unique_uuid_generation(self, mock_uuid):
        """UUIDが毎回異なることのテスト"""
        # モックの設定
        g_mock.get.return_value = "test_org"

        # 異なるUUIDを返すように設定
        uuid_mock1 = MagicMock()
        uuid_mock1.__str__ = MagicMock(return_value="uuid-001")
        uuid_mock2 = MagicMock()
        uuid_mock2.__str__ = MagicMock(return_value="uuid-002")
        mock_uuid.side_effect = [uuid_mock1, uuid_mock2]

        # 実行
        result1 = get_tmp_file_path("workspace_001", "file1.txt")
        result2 = get_tmp_file_path("workspace_001", "file2.txt")

        # 検証 - 異なるUUIDが使用されていることを確認
        expected1 = "/tmp/test_org/workspace_001/tmp/uuid-001/file1.txt"
        expected2 = "/tmp/test_org/workspace_001/tmp/uuid-002/file2.txt"
        assert result1 == {"file_path": expected1}
        assert result2 == {"file_path": expected2}
        assert result1 != result2

    @patch('common_libs.common.util.uuid_lib.uuid4')
    def test_get_tmp_file_path_empty_strings(self, mock_uuid):
        """空文字列の入力テスト"""
        # モックの設定
        g_mock.get.return_value = "test_org"
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(return_value="test-uuid")

        # 実行
        result = get_tmp_file_path("", "")

        # 検証
        expected = "/tmp/test_org/tmp/test-uuid/"
        assert result == {"file_path": expected}

    @patch('common_libs.common.util.uuid_lib.uuid4')
    def test_get_tmp_file_path_return_format(self, mock_uuid):
        """戻り値の形式テスト"""
        # モックの設定
        g_mock.get.return_value = "test_org"
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(return_value="test-uuid")

        # 実行
        result = get_tmp_file_path("workspace_001", "test.txt")

        # 検証 - 辞書形式で正しいキーを持つことを確認
        assert isinstance(result, dict)
        assert "file_path" in result
        assert len(result) == 1
        assert isinstance(result["file_path"], str)

    def test_get_tmp_file_path_flask_g_error(self):
        """flask.gでエラーが発生した場合のテスト"""
        # モックの設定 - flask.g.getでエラーを発生させる
        g_mock.get.side_effect = Exception("Flask context error")

        # 実行と検証
        with pytest.raises(Exception, match="Flask context error"):
            get_tmp_file_path("workspace_001", "test.txt")

        # テスト後に副作用をリセット
        g_mock.get.side_effect = None
