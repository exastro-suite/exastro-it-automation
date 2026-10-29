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
from unittest.mock import Mock, MagicMock
from flask import Flask, g

from controllers.ansible_execution_controller import (
    get_populated_data_aap,
    update_result_data_aap
)


class TestGetPopulatedDataAapController:
    """get_populated_data_aap コントローラー関数のテスト"""

    @pytest.mark.parametrize(
        "driver_id",
        ["legacy", "pioneer", "legacy_role"],
    )
    def test_get_populated_data_aap_success(self, mocker, driver_id, app):
        """正常系: 投入データが正しく取得できる"""
        organization_id = "org1"
        workspace_id = "ws1"
        execution_no = "00000000-0000-0000-0000-000000000001"

        # モックの設定
        mock_dbconnect = mocker.patch('controllers.ansible_execution_controller.DBConnectWs')
        mock_objdbca = MagicMock()
        mock_dbconnect.return_value = mock_objdbca

        # check_driver_from_executionnoのモック
        mocker.patch(
            'controllers.ansible_execution_controller.check_driver_from_executionno',
            return_value=(True, "T_ANSL_EXEC_STS_INST", driver_id)
        )

        # check_menu_infoのモック
        mocker.patch('controllers.ansible_execution_controller.check_menu_info')

        # check_auth_menuのモック（権限OK）
        mocker.patch('controllers.ansible_execution_controller.check_auth_menu', return_value='1')

        # get_populated_data_path_aapのモック
        expected_path = f"/tmp/{organization_id}/{workspace_id}/test.tar.gz"
        mocker.patch(
            'controllers.ansible_execution_controller.get_populated_data_path_aap',
            return_value=expected_path
        )

        # リクエストコンテキスト内で実行
        with app.test_request_context():
            # リクエストコンテキスト内でgオブジェクトを設定
            g.applogger = Mock()
            g.appmsg = Mock()
            g.maintenance_mode = {'data_update_stop': '0'}

            result = get_populated_data_aap(organization_id, workspace_id, execution_no)

            # 結果の確認（Responseオブジェクトで返される）
            assert result is not None


    def test_get_populated_data_aap_execution_no_not_found(self, mocker, mock_flask_g, app):
        """異常系: 作業実行Noが見つからない場合"""
        organization_id = "org1"
        workspace_id = "ws1"
        execution_no = "00000000-0000-0000-0000-999999999999"

        # モックの設定
        mock_dbconnect = mocker.patch('controllers.ansible_execution_controller.DBConnectWs')
        mock_objdbca = MagicMock()
        mock_dbconnect.return_value = mock_objdbca

        # check_driver_from_executionnoのモック（見つからない）
        mocker.patch(
            'controllers.ansible_execution_controller.check_driver_from_executionno',
            return_value=(False, None, None)
        )

        # リクエストコンテキスト内で実行
        with app.test_request_context():
            # リクエストコンテキスト内でgオブジェクトを設定
            g.applogger = Mock()
            g.appmsg = Mock()
            g.maintenance_mode = {'data_update_stop': '0'}

            # エラーレスポンスが返されることを確認
            result = get_populated_data_aap(organization_id, workspace_id, execution_no)
            assert result is not None


    def test_get_populated_data_aap_no_permission(self, mocker, mock_flask_g, app):
        """異常系: メニューに対する権限がない場合"""
        organization_id = "org1"
        workspace_id = "ws1"
        execution_no = "00000000-0000-0000-0000-000000000001"

        # モックの設定
        mock_dbconnect = mocker.patch('controllers.ansible_execution_controller.DBConnectWs')
        mock_objdbca = MagicMock()
        mock_dbconnect.return_value = mock_objdbca

        # check_driver_from_executionnoのモック
        mocker.patch(
            'controllers.ansible_execution_controller.check_driver_from_executionno',
            return_value=(True, "T_ANSL_EXEC_STS_INST", "legacy")
        )

        # check_menu_infoのモック
        mocker.patch('controllers.ansible_execution_controller.check_menu_info')

        # check_auth_menuのモック（権限なし）
        mocker.patch('controllers.ansible_execution_controller.check_auth_menu', return_value='2')

        # リクエストコンテキスト内で実行
        with app.test_request_context():
            # リクエストコンテキスト内でgオブジェクトを設定
            g.applogger = Mock()
            g.appmsg = Mock()
            g.maintenance_mode = {'data_update_stop': '0'}

            # エラーレスポンスが返されることを確認
            result = get_populated_data_aap(organization_id, workspace_id, execution_no)
            assert result is not None


    def test_get_populated_data_aap_maintenance_mode(self, mocker):
        """異常系: メンテナンスモードの場合"""
        organization_id = "org1"
        workspace_id = "ws1"
        execution_no = "00000000-0000-0000-0000-000000000001"

        # メンテナンスモードのFlask gオブジェクト
        app = Flask(__name__)
        with app.test_request_context():
            g.maintenance_mode = {'data_update_stop': '1'}
            g.applogger = Mock()
            g.appmsg = Mock()

            # エラーレスポンスが返されることを確認
            result = get_populated_data_aap(organization_id, workspace_id, execution_no)
            assert result is not None


class TestUpdateResultDataAapController:
    """update_result_data_aap コントローラー関数のテスト"""

    def test_update_result_data_aap_success(self, mocker, app):
        """正常系: 結果データが正しく更新できる"""
        organization_id = "org1"
        workspace_id = "ws1"
        execution_no = "00000000-0000-0000-0000-000000000001"

        # モックの設定
        mock_dbconnect = mocker.patch('controllers.ansible_execution_controller.DBConnectWs')
        mock_objdbca = MagicMock()
        mock_dbconnect.return_value = mock_objdbca

        # check_driver_from_executionnoのモック
        mocker.patch(
            'controllers.ansible_execution_controller.check_driver_from_executionno',
            return_value=(True, "T_ANSL_EXEC_STS_INST", "legacy")
        )

        # check_menu_infoのモック
        mocker.patch('controllers.ansible_execution_controller.check_menu_info')

        # check_auth_menuのモック（権限OK）
        mocker.patch('controllers.ansible_execution_controller.check_auth_menu', return_value='1')

        # secrets.token_hexのモック
        mocker.patch('controllers.ansible_execution_controller.secrets.token_hex', return_value='test1234')

        # connexion.requestのモック
        mock_request = MagicMock()
        mock_request.files = {}
        mocker.patch('controllers.ansible_execution_controller.connexion.request', mock_request)

        # create_file_path_aapのモック
        mocker.patch(
            'controllers.ansible_execution_controller.create_file_path_aap',
            return_value=(True, [], {})
        )

        # update_result_aapのモック
        expected_result = {}
        mocker.patch(
            'controllers.ansible_execution_controller.update_result_aap',
            return_value=expected_result
        )

        # リクエストコンテキスト内で実行
        with app.test_request_context():
            # リクエストコンテキスト内でgオブジェクトを設定
            g.applogger = Mock()
            g.appmsg = Mock()
            g.maintenance_mode = {'data_update_stop': '0'}

            result = update_result_data_aap(organization_id, workspace_id, execution_no)

            # 結果の確認
            assert result is not None


    @pytest.mark.parametrize(
        "driver_id",
        ["legacy", "pioneer", "legacy_role"],
    )
    def test_update_result_data_aap_all_drivers(self, mocker, driver_id, app):
        """正常系: 全ドライバーで正しく動作する"""
        organization_id = "org1"
        workspace_id = "ws1"
        execution_no = "00000000-0000-0000-0000-000000000001"

        # モックの設定
        mock_dbconnect = mocker.patch('controllers.ansible_execution_controller.DBConnectWs')
        mock_objdbca = MagicMock()
        mock_dbconnect.return_value = mock_objdbca

        # check_driver_from_executionnoのモック
        mocker.patch(
            'controllers.ansible_execution_controller.check_driver_from_executionno',
            return_value=(True, "T_ANSL_EXEC_STS_INST", driver_id)
        )

        # check_menu_infoのモック
        mocker.patch('controllers.ansible_execution_controller.check_menu_info')

        # check_auth_menuのモック（権限OK）
        mocker.patch('controllers.ansible_execution_controller.check_auth_menu', return_value='1')

        # secrets.token_hexのモック
        mocker.patch('controllers.ansible_execution_controller.secrets.token_hex', return_value='test1234')

        # connexion.requestのモック
        mock_request = MagicMock()
        mock_request.files = {}
        mocker.patch('controllers.ansible_execution_controller.connexion.request', mock_request)

        # create_file_path_aapのモック
        mocker.patch(
            'controllers.ansible_execution_controller.create_file_path_aap',
            return_value=(True, [], {})
        )

        # update_result_aapのモック
        expected_result = {}
        mocker.patch(
            'controllers.ansible_execution_controller.update_result_aap',
            return_value=expected_result
        )

        # リクエストコンテキスト内で実行
        with app.test_request_context():
            # リクエストコンテキスト内でgオブジェクトを設定
            g.applogger = Mock()
            g.appmsg = Mock()
            g.maintenance_mode = {'data_update_stop': '0'}

            result = update_result_data_aap(organization_id, workspace_id, execution_no)

            # 結果の確認
            assert result is not None

    def test_update_result_data_aap_with_files(self, mocker, app):
        """正常系: ファイルがある場合の更新"""
        organization_id = "org1"
        workspace_id = "ws1"
        execution_no = "00000000-0000-0000-0000-000000000001"

        # モックの設定
        mock_dbconnect = mocker.patch('controllers.ansible_execution_controller.DBConnectWs')
        mock_objdbca = MagicMock()
        mock_dbconnect.return_value = mock_objdbca

        # check_driver_from_executionnoのモック
        mocker.patch(
            'controllers.ansible_execution_controller.check_driver_from_executionno',
            return_value=(True, "T_ANSL_EXEC_STS_INST", "legacy")
        )

        # check_menu_infoのモック
        mocker.patch('controllers.ansible_execution_controller.check_menu_info')

        # check_auth_menuのモック（権限OK）
        mocker.patch('controllers.ansible_execution_controller.check_auth_menu', return_value='1')

        # secrets.token_hexのモック
        mocker.patch('controllers.ansible_execution_controller.secrets.token_hex', return_value='test1234')

        # connexion.requestのモック
        mock_request = MagicMock()
        mock_file = MagicMock()
        mock_file.filename = "test.tar.gz"
        mock_request.files = {"file": mock_file}
        mocker.patch('controllers.ansible_execution_controller.connexion.request', mock_request)

        # create_file_path_aapのモック
        file_paths = {
            "out_tar_data": "/tmp/org1/ws1/driver/ansible/legacy/00000000-0000-0000-0000-000000000001_test1234/out.tar.gz"
        }
        mocker.patch(
            'controllers.ansible_execution_controller.create_file_path_aap',
            return_value=(True, [], file_paths)
        )

        # update_result_aapのモック
        expected_result = {}
        mock_update = mocker.patch(
            'controllers.ansible_execution_controller.update_result_aap',
            return_value=expected_result
        )

        # リクエストコンテキスト内で実行
        with app.test_request_context():
            # リクエストコンテキスト内でgオブジェクトを設定
            g.applogger = Mock()
            g.appmsg = Mock()
            g.maintenance_mode = {'data_update_stop': '0'}

            result = update_result_data_aap(organization_id, workspace_id, execution_no)

            # 結果の確認
            assert result is not None

            # update_result_aapがfile_pathsと共に呼ばれているか確認
            mock_update.assert_called_once()
            call_args = mock_update.call_args[0]
            assert call_args[4] == file_paths  # file_paths引数

    def test_update_result_data_aap_execution_no_not_found(self, mocker, mock_flask_g, app):
        """異常系: 作業実行Noが見つからない場合"""
        organization_id = "org1"
        workspace_id = "ws1"
        execution_no = "00000000-0000-0000-0000-999999999999"

        # モックの設定
        mock_dbconnect = mocker.patch('controllers.ansible_execution_controller.DBConnectWs')
        mock_objdbca = MagicMock()
        mock_dbconnect.return_value = mock_objdbca

        # check_driver_from_executionnoのモック（見つからない）
        mocker.patch(
            'controllers.ansible_execution_controller.check_driver_from_executionno',
            return_value=(False, None, None)
        )

        # リクエストコンテキスト内で実行
        with app.test_request_context():
            # リクエストコンテキスト内でgオブジェクトを設定
            g.applogger = Mock()
            g.appmsg = Mock()
            g.maintenance_mode = {'data_update_stop': '0'}

            # エラーレスポンスが返されることを確認
            result = update_result_data_aap(organization_id, workspace_id, execution_no)
            assert result is not None


    def test_update_result_data_aap_no_permission(self, mocker, mock_flask_g, app):
        """異常系: メニューに対する権限がない場合"""
        organization_id = "org1"
        workspace_id = "ws1"
        execution_no = "00000000-0000-0000-0000-000000000001"

        # モックの設定
        mock_dbconnect = mocker.patch('controllers.ansible_execution_controller.DBConnectWs')
        mock_objdbca = MagicMock()
        mock_dbconnect.return_value = mock_objdbca

        # check_driver_from_executionnoのモック
        mocker.patch(
            'controllers.ansible_execution_controller.check_driver_from_executionno',
            return_value=(True, "T_ANSL_EXEC_STS_INST", "legacy")
        )

        # check_menu_infoのモック
        mocker.patch('controllers.ansible_execution_controller.check_menu_info')

        # check_auth_menuのモック（権限なし）
        mocker.patch('controllers.ansible_execution_controller.check_auth_menu', return_value='2')

        # リクエストコンテキスト内で実行
        with app.test_request_context():
            # リクエストコンテキスト内でgオブジェクトを設定
            g.applogger = Mock()
            g.appmsg = Mock()
            g.maintenance_mode = {'data_update_stop': '0'}

            # エラーレスポンスが返されることを確認
            result = update_result_data_aap(organization_id, workspace_id, execution_no)
            assert result is not None


    def test_update_result_data_aap_maintenance_mode(self, mocker):
        """異常系: メンテナンスモードの場合"""
        organization_id = "org1"
        workspace_id = "ws1"
        execution_no = "00000000-0000-0000-0000-000000000001"

        # メンテナンスモードのFlask gオブジェクト
        app = Flask(__name__)
        with app.test_request_context():
            g.maintenance_mode = {'data_update_stop': '1'}
            g.applogger = Mock()
            g.appmsg = Mock()

            # エラーレスポンスが返されることを確認
            result = update_result_data_aap(organization_id, workspace_id, execution_no)
            assert result is not None
