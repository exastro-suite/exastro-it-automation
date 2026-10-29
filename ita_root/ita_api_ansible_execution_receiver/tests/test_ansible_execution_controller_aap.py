#   Copyright 2024 NEC Corporation
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
from unittest.mock import Mock, MagicMock, mock_open

from libs.ansible_execution import (
    check_driver_from_executionno,
    get_populated_data_path_aap,
    create_file_path_aap,
    update_result_aap
)


class TestCheckDriverFromExecutionno:
    """check_driver_from_executionno関数のテスト"""

    @pytest.mark.parametrize(
        "driver_id, expected_result, expected_table, expected_driver_name",
        [
            ("L", True, "T_ANSL_EXEC_STS_INST", "legacy"),
            ("P", True, "T_ANSP_EXEC_STS_INST", "pioneer"),
            ("R", True, "T_ANSR_EXEC_STS_INST", "legacy_role"),
        ],
    )
    def test_check_driver_from_executionno_success(
        self, mock_dbca, driver_id, expected_result, expected_table, expected_driver_name
    ):
        """正常系: 各ドライバーIDで正しいテーブルとドライバー名が返される"""
        execution_no = "00000000-0000-0000-0000-000000000001"

        # モックデータの設定
        mock_dbca.table_select.return_value = [
            {"DRIVER_ID": driver_id, "EXECUTION_NO": execution_no}
        ]

        result, t_exec_sts_inst, driver_name = check_driver_from_executionno(
            mock_dbca, execution_no
        )

        assert result == expected_result
        assert t_exec_sts_inst == expected_table
        assert driver_name == expected_driver_name

        # table_selectが正しく呼ばれているか確認
        mock_dbca.table_select.assert_called_once_with(
            'V_ANSC_EXEC_STS_INST',
            "WHERE EXECUTION_NO = %s ",
            [execution_no]
        )

    def test_check_driver_from_executionno_not_found(self, mock_dbca):
        """異常系: 作業実行Noが見つからない場合"""
        execution_no = "00000000-0000-0000-0000-999999999999"

        # 空のリストを返す
        mock_dbca.table_select.return_value = []

        result, t_exec_sts_inst, driver_name = check_driver_from_executionno(
            mock_dbca, execution_no
        )

        assert result is False
        assert t_exec_sts_inst is None
        assert driver_name is None

    def test_check_driver_from_executionno_multiple_records(self, mock_dbca):
        """異常系: 複数のレコードが返される場合"""
        execution_no = "00000000-0000-0000-0000-000000000001"

        # 複数レコードを返す
        mock_dbca.table_select.return_value = [
            {"DRIVER_ID": "L", "EXECUTION_NO": execution_no},
            {"DRIVER_ID": "P", "EXECUTION_NO": execution_no}
        ]

        result, t_exec_sts_inst, driver_name = check_driver_from_executionno(
            mock_dbca, execution_no
        )

        assert result is False
        assert t_exec_sts_inst is None
        assert driver_name is None

    def test_check_driver_from_executionno_invalid_driver_id(self, mock_dbca):
        """異常系: 不正なドライバーIDの場合"""
        execution_no = "00000000-0000-0000-0000-000000000001"

        # 不正なドライバーIDを返す
        mock_dbca.table_select.return_value = [
            {"DRIVER_ID": "X", "EXECUTION_NO": execution_no}
        ]

        result, t_exec_sts_inst, driver_name = check_driver_from_executionno(
            mock_dbca, execution_no
        )

        # ドライバーIDが不正な場合、関数はNoneを返す
        assert result is False
        assert t_exec_sts_inst is None
        assert driver_name is None


class TestGetPopulatedDataPathAap:
    """get_populated_data_path_aap関数のテスト"""

    @pytest.mark.parametrize(
        "driver_id",
        ["legacy", "pioneer", "legacy_role"],
    )
    def test_get_populated_data_path_aap_with_conductor(
        self, mock_dbca, sample_conductor_execution_data, mocker, driver_id, mock_flask_g
    ):
        """正常系: Conductor経由の実行でtarファイルが正しく作成される"""
        execution_no = sample_conductor_execution_data['EXECUTION_NO']
        organization_id = "org1"
        workspace_id = "ws1"
        t_exec_sts_inst = "T_ANSL_EXEC_STS_INST"

        # モックデータの設定
        mock_dbca.table_select.return_value = [sample_conductor_execution_data]

        # モックの設定
        mocker.patch('libs.ansible_execution.secrets.token_hex', return_value='test1234')
        mocker.patch('libs.ansible_execution.retry_rmtree')
        mocker.patch('libs.ansible_execution.retry_makedirs')
        mocker.patch('libs.ansible_execution.retry_chmod')
        mocker.patch('libs.ansible_execution.retry_copytree')
        mocker.patch('libs.ansible_execution.arrange_stacktrace_format')

        # tarfileのモック
        mock_tar = MagicMock()
        mock_tarfile_open = mocker.patch('libs.ansible_execution.tarfile.open')
        mock_tarfile_open.return_value.__enter__.return_value = mock_tar

        # subprocessのモック
        mocker.patch('libs.ansible_execution.tmp_copy_subprocess_run')

        # os.listdirのモック
        mocker.patch('os.listdir', return_value=[])

        # 環境変数のモック
        mocker.patch.dict(os.environ, {'STORAGEPATH': '/test/storage'})

        result = get_populated_data_path_aap(
            mock_dbca, organization_id, workspace_id, execution_no, t_exec_sts_inst, driver_id
        )

        # 結果の確認
        assert result.startswith(f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}")
        assert result.endswith(".tar.gz")

        # table_selectが正しく呼ばれているか確認
        mock_dbca.table_select.assert_called_once_with(
            t_exec_sts_inst,
            'WHERE DISUSE_FLAG = %s AND EXECUTION_NO = %s',
            ['0', execution_no]
        )

    def test_get_populated_data_path_aap_without_conductor(
        self, mock_dbca, sample_execution_data, mocker, mock_flask_g
    ):
        """異常系: Conductor経由でない実行の場合にエラーが発生"""
        execution_no = sample_execution_data['EXECUTION_NO']
        organization_id = "org1"
        workspace_id = "ws1"
        t_exec_sts_inst = "T_ANSL_EXEC_STS_INST"
        driver_id = "legacy"

        # Conductor経由でないデータ
        mock_dbca.table_select.return_value = [sample_execution_data]

        # モックの設定
        mocker.patch('libs.ansible_execution.secrets.token_hex', return_value='test1234')
        mocker.patch('libs.ansible_execution.retry_rmtree')
        mocker.patch.dict(os.environ, {'STORAGEPATH': '/test/storage'})

        # AppExceptionが発生することを確認
        with pytest.raises(Exception):
            get_populated_data_path_aap(
                mock_dbca, organization_id, workspace_id, execution_no, t_exec_sts_inst, driver_id
            )

    def test_get_populated_data_path_aap_no_record(self, mock_dbca, mocker, mock_flask_g):
        """異常系: レコードが見つからない場合"""
        execution_no = "00000000-0000-0000-0000-999999999999"
        organization_id = "org1"
        workspace_id = "ws1"
        t_exec_sts_inst = "T_ANSL_EXEC_STS_INST"
        driver_id = "legacy"

        # レコードが見つからない
        mock_dbca.table_select.return_value = []

        # モックの設定
        mocker.patch('libs.ansible_execution.secrets.token_hex', return_value='test1234')
        mocker.patch('libs.ansible_execution.retry_rmtree')
        mocker.patch.dict(os.environ, {'STORAGEPATH': '/test/storage'})

        # AppExceptionが発生することを確認
        with pytest.raises(Exception):
            get_populated_data_path_aap(
                mock_dbca, organization_id, workspace_id, execution_no, t_exec_sts_inst, driver_id
            )


class TestCreateFilePathAap:
    """create_file_path_aap関数のテスト"""

    def test_create_file_path_aap_with_files(self, mock_connexion_request, mocker):
        """正常系: ファイルが存在する場合"""
        tmp_path = "/tmp/test"
        execution_no = "00000000-0000-0000-0000-000000000001"
        driver_id = "legacy"
        para_id = "test1234"

        # ファイルのモックを設定
        mock_file = MagicMock()
        mock_file.filename = "test.tar.gz"
        mock_file.stream.read = Mock(side_effect=[b"test data", b""])
        mock_connexion_request.files = {"file": mock_file}
        mock_connexion_request.headers.get.return_value = "1000"

        # モックの設定
        mocker.patch('libs.ansible_execution.storage_base')
        mock_storage = mocker.patch('libs.ansible_execution.storage_base').return_value
        mock_storage.validate_disk_space.return_value = (True, 1000000)

        mocker.patch('libs.ansible_execution.retry_makedirs')
        mocker.patch('builtins.open', mock_open())

        retBool, parameters, file_paths = create_file_path_aap(
            mock_connexion_request, tmp_path, execution_no, driver_id, para_id
        )

        assert retBool is True
        assert parameters == []
        assert "file" in file_paths
        assert file_paths["file"].endswith("test.tar.gz")

    def test_create_file_path_aap_without_files(self, mock_connexion_request, mocker):
        """正常系: ファイルが存在しない場合"""
        tmp_path = "/tmp/test"
        execution_no = "00000000-0000-0000-0000-000000000001"
        driver_id = "legacy"
        para_id = "test1234"

        # ファイルがない場合
        mock_connexion_request.files = None

        retBool, parameters, file_paths = create_file_path_aap(
            mock_connexion_request, tmp_path, execution_no, driver_id, para_id
        )

        assert retBool is True
        assert parameters == []
        assert file_paths == {}

    def test_create_file_path_aap_insufficient_disk_space(self, mock_connexion_request, mocker):
        """異常系: ディスク容量が不足している場合"""
        tmp_path = "/tmp/test"
        execution_no = "00000000-0000-0000-0000-000000000001"
        driver_id = "legacy"
        para_id = "test1234"

        # ファイルのモックを設定
        mock_file = MagicMock()
        mock_file.filename = "test.tar.gz"
        mock_connexion_request.files = {"file": mock_file}
        mock_connexion_request.headers.get.return_value = "10000000000"

        # ディスク容量不足のモック
        mock_storage = mocker.patch('libs.ansible_execution.storage_base').return_value
        mock_storage.validate_disk_space.return_value = (False, 1000)

        # AppExceptionが発生することを確認
        with pytest.raises(Exception):
            create_file_path_aap(
                mock_connexion_request, tmp_path, execution_no, driver_id, para_id
            )


class TestUpdateResultAap:
    """update_result_aap関数のテスト"""

    def test_update_result_aap_with_conductor(
        self, mock_dbca, sample_conductor_execution_data, mocker, mock_flask_g
    ):
        """正常系: Conductor経由で全ファイルが正しく更新される"""
        execution_no = sample_conductor_execution_data['EXECUTION_NO']
        organization_id = "org1"
        workspace_id = "ws1"
        t_exec_sts_inst = "T_ANSL_EXEC_STS_INST"
        driver_id = "legacy"
        para_id = "test1234"

        file_path = {
            "out_tar_data": f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}_{para_id}/out.tar.gz",
            "parameters_tar_data": f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}_{para_id}/parameter.tar.gz",
            "parameters_file_tar_data": f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}_{para_id}/parameters_file.tar.gz",
            "conductor_tar_data": f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}_{para_id}/conductor.tar.gz"
        }

        # モックデータの設定
        mock_dbca.table_select.return_value = [sample_conductor_execution_data]

        # モックの設定

        mocker.patch('libs.ansible_execution.retry_makedirs')
        mocker.patch('libs.ansible_execution.retry_extract')
        mocker.patch('libs.ansible_execution.retry_copytree')
        mocker.patch('libs.ansible_execution.retry_rmtree')
        mocker.patch('libs.ansible_execution.print_exception_msg')
        mocker.patch.dict(os.environ, {'STORAGEPATH': '/test/storage'})

        result = update_result_aap(
            mock_dbca, organization_id, workspace_id, execution_no, file_path, t_exec_sts_inst, driver_id, para_id
        )

        assert result == {}

        # table_selectが正しく呼ばれているか確認
        mock_dbca.table_select.assert_called_once_with(
            t_exec_sts_inst,
            'WHERE DISUSE_FLAG = %s AND EXECUTION_NO = %s',
            ['0', execution_no]
        )

    def test_update_result_aap_without_conductor(
        self, mock_dbca, sample_execution_data, mocker, mock_flask_g
    ):
        """正常系: Conductor経由でない場合、Conductorファイルは更新されない"""
        execution_no = sample_execution_data['EXECUTION_NO']
        organization_id = "org1"
        workspace_id = "ws1"
        t_exec_sts_inst = "T_ANSL_EXEC_STS_INST"
        driver_id = "legacy"
        para_id = "test1234"

        file_path = {
            "out_tar_data": f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}_{para_id}/out.tar.gz",
            "conductor_tar_data": f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}_{para_id}/conductor.tar.gz"
        }

        # Conductor経由でないデータ
        mock_dbca.table_select.return_value = [sample_execution_data]

        # モックの設定

        mock_retry_copytree = mocker.patch('libs.ansible_execution.retry_copytree')
        mocker.patch('libs.ansible_execution.retry_makedirs')
        mocker.patch('libs.ansible_execution.retry_extract')
        mocker.patch('libs.ansible_execution.retry_rmtree')
        mocker.patch('libs.ansible_execution.print_exception_msg')
        mocker.patch.dict(os.environ, {'STORAGEPATH': '/test/storage'})

        result = update_result_aap(
            mock_dbca, organization_id, workspace_id, execution_no, file_path, t_exec_sts_inst, driver_id, para_id
        )

        assert result == {}

        # retry_copytreeの呼び出し回数を確認（Conductorファイルは除外される）
        call_count = mock_retry_copytree.call_count

        # conductor_tar_dataは処理されないので、out_tar_dataの1回だけ呼ばれる
        assert call_count == 1

    def test_update_result_aap_empty_file_path(self, mock_dbca, sample_execution_data, mocker, mock_flask_g):
        """正常系: ファイルパスが空の場合"""
        execution_no = sample_execution_data['EXECUTION_NO']
        organization_id = "org1"
        workspace_id = "ws1"
        t_exec_sts_inst = "T_ANSL_EXEC_STS_INST"
        driver_id = "legacy"
        para_id = "test1234"

        file_path = {}

        # モックデータの設定
        mock_dbca.table_select.return_value = [sample_execution_data]

        # モックの設定

        mocker.patch('libs.ansible_execution.retry_rmtree')
        mocker.patch('libs.ansible_execution.print_exception_msg')
        mocker.patch.dict(os.environ, {'STORAGEPATH': '/test/storage'})

        result = update_result_aap(
            mock_dbca, organization_id, workspace_id, execution_no, file_path, t_exec_sts_inst, driver_id, para_id
        )

        assert result == {}

    @pytest.mark.parametrize(
        "file_key, expected_dir",
        [
            ("out_tar_data", "out"),
            ("parameters_tar_data", "in/_parameters"),
            ("parameters_file_tar_data", "in/_parameters_file"),
        ],
    )
    def test_update_result_aap_specific_file_types(
        self, mock_dbca, sample_execution_data, mocker, file_key, expected_dir, mock_flask_g
    ):
        """正常系: 各ファイルタイプが正しいディレクトリにコピーされる"""
        execution_no = sample_execution_data['EXECUTION_NO']
        organization_id = "org1"
        workspace_id = "ws1"
        t_exec_sts_inst = "T_ANSL_EXEC_STS_INST"
        driver_id = "legacy"
        para_id = "test1234"

        file_path = {
            file_key: f"/tmp/{organization_id}/{workspace_id}/driver/ansible/{driver_id}/{execution_no}_{para_id}/test.tar.gz"
        }

        # モックデータの設定
        mock_dbca.table_select.return_value = [sample_execution_data]

        # モックの設定

        mock_retry_copytree = mocker.patch('libs.ansible_execution.retry_copytree')
        mocker.patch('libs.ansible_execution.retry_makedirs')
        mocker.patch('libs.ansible_execution.retry_extract')
        mocker.patch('libs.ansible_execution.retry_rmtree')
        mocker.patch('libs.ansible_execution.print_exception_msg')
        mocker.patch.dict(os.environ, {'STORAGEPATH': '/test/storage'})

        result = update_result_aap(
            mock_dbca, organization_id, workspace_id, execution_no, file_path, t_exec_sts_inst, driver_id, para_id
        )

        assert result == {}

        # retry_copytreeが正しいディレクトリで呼ばれているか確認
        mock_retry_copytree.assert_called_once()
        args = mock_retry_copytree.call_args[0]
        assert expected_dir in args[1]
