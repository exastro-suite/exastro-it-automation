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
import os
import tempfile
from unittest.mock import patch, mock_open

from common_libs.common.storage_access import storage_read


class TestStorageRead:
    """storage_readクラスのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.storage_read = storage_read()
        self.test_content = "test file content"
        self.test_binary_content = b"test binary content"

    def teardown_method(self):
        """各テストメソッドの後に実行されるクリーンアップ処理"""
        if hasattr(self.storage_read, 'fd') and self.storage_read.fd:
            try:
                self.storage_read.fd.close()
            except Exception:
                pass

    @pytest.fixture
    def temp_test_file(self):
        """テスト用の一時ファイルを作成するフィクスチャ"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(self.test_content)
            temp_file_path = f.name
        yield temp_file_path
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    @pytest.fixture
    def temp_binary_file(self):
        """テスト用のバイナリファイルを作成するフィクスチャ"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(self.test_binary_content)
            temp_file_path = f.name
        yield temp_file_path
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    @patch.dict(os.environ, {'STORAGEPATH': '/storage'})
    def test_open_non_storage_file(self, temp_test_file):
        """非/storageパスのファイルを開くテスト"""
        # 実行
        fd = self.storage_read.open(temp_test_file)

        # 検証
        assert fd is not None
        assert self.storage_read.storage_file_path == temp_test_file
        assert self.storage_read.tmp_file_path == temp_test_file
        assert self.storage_read.storage_flg is False
        assert self.storage_read.force_file_del is False

        # クリーンアップ
        self.storage_read.close()

    @patch.dict(os.environ, {'STORAGEPATH': '/storage'})
    @patch('shutil.copy2')
    @patch('builtins.open', mock_open(read_data="test content"))
    def test_open_storage_file(self, mock_copy):
        """/storageパスのファイルを開くテスト"""
        storage_file_path = "/storage/test/file.txt"

        # 実行
        fd = self.storage_read.open(storage_file_path)

        # 検証
        assert fd is not None
        assert self.storage_read.storage_file_path == storage_file_path
        assert self.storage_read.tmp_file_path.startswith("/tmp/")
        assert self.storage_read.storage_flg is True
        assert self.storage_read.force_file_del is False
        mock_copy.assert_called_once()

    @patch.dict(os.environ, {'STORAGEPATH': '/storage'})
    @patch('shutil.copy2')
    @patch('builtins.open', mock_open(read_data="test content"))
    def test_open_with_tmp_path(self, mock_copy):
        """tmp_pathを指定してファイルを開くテスト"""
        storage_file_path = "/storage/test/file.txt"
        tmp_path = "/tmp/custom/file.txt"

        with patch('os.makedirs'):
            # 実行
            fd = self.storage_read.open(storage_file_path, tmp_path=tmp_path)

            # 検証
            assert fd is not None
            assert self.storage_read.tmp_file_path == tmp_path
            assert self.storage_read.force_file_del is True
            mock_copy.assert_called_once_with(storage_file_path, tmp_path)

    def test_open_with_mode(self, temp_test_file):
        """モードを指定してファイルを開くテスト"""
        # 実行
        fd = self.storage_read.open(temp_test_file, mode='r')

        # 検証
        assert fd is not None
        assert fd.mode == 'r'

        # クリーンアップ
        self.storage_read.close()

    def test_read(self, temp_test_file):
        """ファイル読み込みテスト"""
        # 実行
        self.storage_read.open(temp_test_file)
        content = self.storage_read.read()

        # 検証
        assert content == self.test_content

        # クリーンアップ
        self.storage_read.close()

    def test_chunk_read(self, temp_test_file):
        """チャンク読み込みテスト"""
        # 実行
        self.storage_read.open(temp_test_file)
        chunk = self.storage_read.chunk_read(4)

        # 検証
        assert chunk == "test"

        # クリーンアップ
        self.storage_read.close()

    @patch.dict(os.environ, {'STORAGEPATH': '/storage'})
    def test_close_non_storage_file(self, temp_test_file):
        """非/storageファイルのクローズテスト"""
        # 実行
        self.storage_read.open(temp_test_file)
        self.storage_read.close()

        # 検証
        assert self.storage_read.fd.closed

    @patch.dict(os.environ, {'STORAGEPATH': '/storage'})
    @patch('shutil.copy2')
    @patch('builtins.open', mock_open(read_data="test content"))
    def test_close_storage_file(self, mock_copy):
        """/storageファイルのクローズテスト（ファイル削除あり）"""
        storage_file_path = "/storage/test/file.txt"

        # 実行
        self.storage_read.open(storage_file_path)

        # removeメソッドを直接モック化
        with patch.object(self.storage_read, 'remove') as mock_remove:
            self.storage_read.close(file_del=True)
            # 検証
            mock_remove.assert_called_once()

    @patch.dict(os.environ, {'STORAGEPATH': '/storage'})
    @patch('shutil.copy2')
    @patch('builtins.open', mock_open(read_data="test content"))
    def test_close_storage_file_no_delete(self, mock_copy):
        """/storageファイルのクローズテスト（ファイル削除なし）"""
        storage_file_path = "/storage/test/file.txt"

        # 実行
        self.storage_read.open(storage_file_path)

        # removeメソッドを直接モック化
        with patch.object(self.storage_read, 'remove') as mock_remove:
            self.storage_read.close(file_del=False)
            # 検証
            mock_remove.assert_not_called()

    @patch.dict(os.environ, {'STORAGEPATH': '/storage'})
    @patch('shutil.copy2')
    @patch('builtins.open', mock_open(read_data="test content"))
    def test_close_with_force_file_del(self, mock_copy):
        """強制ファイル削除フラグありのクローズテスト"""
        storage_file_path = "/storage/test/file.txt"
        tmp_path = "/tmp/custom/file.txt"

        with patch('os.makedirs'):
            # 実行
            self.storage_read.open(storage_file_path, tmp_path=tmp_path)

            # removeとremove_tmpdirメソッドを直接モック化
            with patch.object(self.storage_read, 'remove') as mock_remove, \
                    patch.object(self.storage_read, 'remove_tmpdir') as mock_rmdir:
                self.storage_read.close()

                # 検証
                mock_remove.assert_called()
                mock_rmdir.assert_called()

    @patch('os.path.isfile', return_value=True)
    @patch('os.remove')
    def test_remove(self, mock_remove, mock_isfile):
        """ファイル削除テスト"""
        self.storage_read.tmp_file_path = "/tmp/test_file.txt"

        # 実行
        self.storage_read.remove()

        # 検証
        mock_remove.assert_called_once_with("/tmp/test_file.txt")

    @patch('os.path.isfile', return_value=False)
    @patch('os.remove')
    def test_remove_file_not_exists(self, mock_remove, mock_isfile):
        """存在しないファイルの削除テスト"""
        self.storage_read.tmp_file_path = "/tmp/nonexistent_file.txt"

        # 実行
        self.storage_read.remove()

        # 検証
        mock_remove.assert_called()

    @patch('os.path.isdir', return_value=True)
    @patch('os.rmdir')
    def test_remove_tmpdir(self, mock_rmdir, mock_isdir):
        """一時ディレクトリ削除テスト"""
        self.storage_read.tmp_file_path = "/tmp/test_dir/file.txt"

        # 実行
        self.storage_read.remove_tmpdir()

        # 検証
        mock_rmdir.assert_called_once_with("/tmp/test_dir")

    @patch('os.path.isdir', return_value=False)
    @patch('os.rmdir')
    def test_remove_tmpdir_not_exists(self, mock_rmdir, mock_isdir):
        """存在しない一時ディレクトリの削除テスト"""
        self.storage_read.tmp_file_path = "/tmp/nonexistent_dir/file.txt"

        # 実行
        self.storage_read.remove_tmpdir()

        # 検証
        mock_rmdir.assert_called()

    def test_remove_tmpdir_not_tmp_path(self):
        """/tmp以外のパスでの一時ディレクトリ削除テスト"""
        self.storage_read.tmp_file_path = "/other/path/file.txt"

        with patch('os.rmdir') as mock_rmdir:
            # 実行
            self.storage_read.remove_tmpdir()

            # 検証
            mock_rmdir.assert_not_called()

    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_open_file_not_found(self, mock_open):
        """存在しないファイルを開く場合のテスト"""
        with pytest.raises(FileNotFoundError):
            self.storage_read.open("nonexistent_file.txt")

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_open_permission_error(self, mock_open):
        """権限エラーが発生する場合のテスト"""
        with pytest.raises(PermissionError):
            self.storage_read.open("permission_denied_file.txt")

    def test_context_manager_usage(self, temp_test_file):
        """コンテキストマネージャーとしての使用テスト"""
        # 現在の実装では手動でopen/closeを行う
        self.storage_read.open(temp_test_file)
        content = self.storage_read.read()
        self.storage_read.close()

        assert content == self.test_content

    def test_multiple_read_calls(self, temp_test_file):
        """複数回読み込み呼び出しのテスト"""
        self.storage_read.open(temp_test_file)

        # 最初の読み込み
        content1 = self.storage_read.read()
        # 2回目の読み込み（ファイルポインタは終端にあるため空文字列が返される）
        content2 = self.storage_read.read()

        assert content1 == self.test_content
        assert content2 == ""

        self.storage_read.close()

    @patch.dict(os.environ, {'STORAGEPATH': '/storage'})
    @patch('shutil.copy2', side_effect=Exception("Copy failed"))
    def test_copy_failure(self, mock_copy):
        """ファイルコピーに失敗した場合のテスト"""
        storage_file_path = "/storage/test/file.txt"

        with pytest.raises(Exception, match="Copy failed"):
            self.storage_read.open(storage_file_path)

    def test_initialization(self):
        """初期化テスト"""
        sr = storage_read()

        assert sr.storage_file_path is None
        assert sr.tmp_file_path is None
        assert sr.tmp_dir_path is None
        assert sr.storage_path_flg is False
        assert sr.fd is None
        assert sr.force_file_del is False
