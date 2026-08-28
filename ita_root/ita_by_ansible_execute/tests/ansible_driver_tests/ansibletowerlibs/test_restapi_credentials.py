#   Copyright 2022 NEC Corporation
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
from unittest.mock import Mock, patch
from flask import Flask, g


@pytest.fixture
def mock_flask_g():
    """Flask g オブジェクトのモック"""
    app = Flask(__name__)
    with app.app_context():
        g.applogger = Mock()
        g.applogger.info = Mock()
        g.applogger.error = Mock()
        g.applogger.debug = Mock()
        yield g


@pytest.fixture
def mock_rest_api_caller():
    """RestApiCallerのモック"""
    mock_caller = Mock()
    mock_caller.getOrchestratorSubId_dir.return_value = "legacy"
    mock_caller.restCall = Mock()
    return mock_caller


class TestGitPostBasic:
    """git_post_basic関数のテストクラス"""

    def test_git_post_basic_success(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: Git Basic認証情報の作成が成功する場合
        期待値: success=True、statusCode=201を含むレスポンスを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        # APIレスポンスのモック
        mock_response = {
            'statusCode': 201,
            'responseContents': {
                'id': 100,
                'name': 'ita_legacy_executions_git_credential_0000000001'
            }
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        # テストパラメータ
        param = {
            'execution_no': '1',
            'organization': 1,
            'username': 'git_user',
            'token': 'ghp_test_token_123456789'
        }

        # テスト実行
        result = AnsibleTowerRestApiCredentials.git_post_basic(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is True
        assert result['statusCode'] == 201
        assert 'responseContents' in result
        assert result['responseContents']['id'] == 100

        # restCallが正しいパラメータで呼ばれたことを確認
        mock_rest_api_caller.restCall.assert_called_once()
        call_args = mock_rest_api_caller.restCall.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "credentials/"
        content = call_args[0][2]
        assert content['name'] == 'ita_legacy_executions_git_credential_0000000001'
        assert content['organization'] == 1
        assert content['inputs']['username'] == 'git_user'
        assert content['inputs']['password'] == 'ghp_test_token_123456789'
        assert content['credential_type'] == 2  # SRC_CONTROL

    def test_git_post_basic_missing_execution_no(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: execution_noが欠けている場合
        期待値: success=False、エラーメッセージを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        param = {
            'organization': 1,
            'username': 'git_user',
            'token': 'ghp_test_token_123456789'
        }

        result = AnsibleTowerRestApiCredentials.git_post_basic(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is False
        assert 'errorMessage' in result['responseContents']
        assert result['responseContents']['errorMessage'] == "Need 'execution_no'."

    def test_git_post_basic_missing_organization(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: organizationが欠けている場合
        期待値: success=False、エラーメッセージを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        param = {
            'execution_no': '1',
            'username': 'git_user',
            'token': 'ghp_test_token_123456789'
        }

        result = AnsibleTowerRestApiCredentials.git_post_basic(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is False
        assert 'errorMessage' in result['responseContents']
        assert result['responseContents']['errorMessage'] == "Need 'organization'."

    def test_git_post_basic_missing_username(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: usernameが欠けている場合
        期待値: success=False、エラーメッセージを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        param = {
            'execution_no': '1',
            'organization': 1,
            'token': 'ghp_test_token_123456789'
        }

        result = AnsibleTowerRestApiCredentials.git_post_basic(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is False
        assert 'errorMessage' in result['responseContents']
        assert result['responseContents']['errorMessage'] == "Need 'username'."

    def test_git_post_basic_missing_token(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: tokenが欠けている場合
        期待値: success=False、エラーメッセージを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        param = {
            'execution_no': '1',
            'organization': 1,
            'username': 'git_user'
        }

        result = AnsibleTowerRestApiCredentials.git_post_basic(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is False
        assert 'errorMessage' in result['responseContents']
        assert result['responseContents']['errorMessage'] == "Need 'token'."

    def test_git_post_basic_api_failure_not_201(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: API呼び出しがステータスコード201以外を返す場合
        期待値: success=False、エラーメッセージを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        # APIレスポンスのモック（失敗）
        mock_response = {
            'statusCode': 400,
            'responseContents': {}
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        param = {
            'execution_no': '1',
            'organization': 1,
            'username': 'git_user',
            'token': 'ghp_test_token_123456789'
        }

        result = AnsibleTowerRestApiCredentials.git_post_basic(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is False
        assert 'errorMessage' in result['responseContents']
        assert result['responseContents']['errorMessage'] == "status_code not 201. =>400"

    def test_git_post_basic_with_execution_no_padding(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: execution_noが桁数少ない値の場合、パディングされる
        期待値: 名前に10桁のゼロパディングされたexecution_noが使用される
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        mock_response = {
            'statusCode': 201,
            'responseContents': {'id': 100}
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        param = {
            'execution_no': '42',
            'organization': 1,
            'username': 'git_user',
            'token': 'ghp_test_token_123456789'
        }

        result = AnsibleTowerRestApiCredentials.git_post_basic(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is True

        # 名前が正しくパディングされていることを確認
        call_args = mock_rest_api_caller.restCall.call_args
        content = call_args[0][2]
        assert content['name'] == 'ita_legacy_executions_git_credential_0000000042'


class TestDeleteSCM:
    """deleteSCM関数のテストクラス"""

    def test_delete_scm_success(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: SCM認証情報の削除が成功する場合
        期待値: success=Trueを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        # deleteメソッドのモック（成功）
        with patch.object(AnsibleTowerRestApiCredentials, 'delete') as mock_delete:
            mock_delete.return_value = {
                'success': True,
                'statusCode': 204
            }

            # テストパラメータ
            AAC_create_object_id = {
                'SCMCredentialId': [100, 101, 102]
            }

            # テスト実行
            result = AnsibleTowerRestApiCredentials.deleteSCM(mock_rest_api_caller, AAC_create_object_id)

            # 検証
            assert result['success'] is True
            assert mock_delete.call_count == 3
            mock_delete.assert_any_call(mock_rest_api_caller, 100)
            mock_delete.assert_any_call(mock_rest_api_caller, 101)
            mock_delete.assert_any_call(mock_rest_api_caller, 102)

    def test_delete_scm_no_credential_id(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: SCMCredentialIdが存在しない場合
        期待値: success=Trueを返す（何もせず成功）
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        with patch.object(AnsibleTowerRestApiCredentials, 'delete') as mock_delete:
            # SCMCredentialIdが含まれていないオブジェクト
            AAC_create_object_id = {
                'CredentialId': [200, 201]
            }

            result = AnsibleTowerRestApiCredentials.deleteSCM(mock_rest_api_caller, AAC_create_object_id)

            # 検証
            assert result['success'] is True
            mock_delete.assert_not_called()

    def test_delete_scm_empty_credential_id_list(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: SCMCredentialIdが空のリストの場合
        期待値: success=Trueを返す（何もせず成功）
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        with patch.object(AnsibleTowerRestApiCredentials, 'delete') as mock_delete:
            AAC_create_object_id = {
                'SCMCredentialId': []
            }

            result = AnsibleTowerRestApiCredentials.deleteSCM(mock_rest_api_caller, AAC_create_object_id)

            # 検証
            assert result['success'] is True
            mock_delete.assert_not_called()

    def test_delete_scm_failure(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: 削除処理が失敗する場合
        期待値: success=False、失敗時のレスポンスを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        with patch.object(AnsibleTowerRestApiCredentials, 'delete') as mock_delete:
            # 2番目の削除で失敗
            mock_delete.side_effect = [
                {'success': True, 'statusCode': 204},  # 1番目成功
                {'success': False, 'statusCode': 404, 'responseContents': {'errorMessage': 'Not found'}},  # 2番目失敗
            ]

            AAC_create_object_id = {
                'SCMCredentialId': [100, 101, 102]
            }

            result = AnsibleTowerRestApiCredentials.deleteSCM(mock_rest_api_caller, AAC_create_object_id)

            # 検証
            assert result['success'] is False
            assert result['statusCode'] == 404
            assert 'errorMessage' in result['responseContents']
            # 2回目の呼び出しで失敗したため、合計2回のみ呼ばれる
            assert mock_delete.call_count == 2

    def test_delete_scm_single_credential(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: 単一のSCM認証情報を削除する場合
        期待値: success=Trueを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        with patch.object(AnsibleTowerRestApiCredentials, 'delete') as mock_delete:
            mock_delete.return_value = {
                'success': True,
                'statusCode': 204
            }

            AAC_create_object_id = {
                'SCMCredentialId': [999]
            }

            result = AnsibleTowerRestApiCredentials.deleteSCM(mock_rest_api_caller, AAC_create_object_id)

            # 検証
            assert result['success'] is True
            mock_delete.assert_called_once_with(mock_rest_api_caller, 999)

    def test_delete_scm_logs_on_failure(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: 削除失敗時にログが記録される
        期待値: applogger.infoが呼ばれる
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials

        with patch.object(AnsibleTowerRestApiCredentials, 'delete') as mock_delete:
            mock_delete.return_value = {
                'success': False,
                'statusCode': 500,
                'responseContents': {'errorMessage': 'Internal Server Error'}
            }

            AAC_create_object_id = {
                'SCMCredentialId': [100]
            }

            result = AnsibleTowerRestApiCredentials.deleteSCM(mock_rest_api_caller, AAC_create_object_id)

            # 検証
            assert result['success'] is False
            # ログが2回呼ばれる（エラーメッセージとレスポンス内容）
            assert g.applogger.info.call_count == 2
            assert "Faild to delete vault credential" in str(g.applogger.info.call_args_list[0])
