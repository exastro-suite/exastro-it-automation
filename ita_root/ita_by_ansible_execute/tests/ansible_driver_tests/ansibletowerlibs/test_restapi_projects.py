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
from unittest.mock import Mock
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


class TestPost:
    """post関数のテストクラス"""

    def test_post_git_scm_success(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: Git SCMプロジェクトの作成が成功する場合
        期待値: success=True、statusCode=201を含むレスポンスを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        # APIレスポンスのモック
        mock_response = {
            'statusCode': 201,
            'responseContents': {
                'id': 100,
                'name': 'ita_legacy_executions_project_0000000001',
                'scm_type': 'git',
                'scm_url': 'https://github.com/example/repo.git'
            }
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        # テストパラメータ
        param = {
            'execution_no': '1',
            'scm_type': 'git',
            'scm_url': 'https://github.com/example/repo.git',
            'organization': 1
        }

        # テスト実行
        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is True
        assert result['statusCode'] == 201
        assert 'responseContents' in result
        assert result['responseContents']['id'] == 100

        # restCallが正しいパラメータで呼ばれたことを確認
        mock_rest_api_caller.restCall.assert_called_once()
        call_args = mock_rest_api_caller.restCall.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "projects/"
        content = call_args[0][2]
        assert content['name'] == 'ita_legacy_executions_project_0000000001'
        assert content['organization'] == 1
        assert content['scm_type'] == 'git'
        assert content['scm_url'] == 'https://github.com/example/repo.git'

    def test_post_git_scm_with_credential(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: Git SCMプロジェクトをcredentialと一緒に作成する場合
        期待値: success=True、credentialが含まれる
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        mock_response = {
            'statusCode': 201,
            'responseContents': {'id': 100}
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        param = {
            'execution_no': '1',
            'scm_type': 'git',
            'scm_url': 'https://github.com/example/repo.git',
            'organization': 1,
            'credential': 999
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is True

        call_args = mock_rest_api_caller.restCall.call_args
        content = call_args[0][2]
        assert content['credential'] == 999

    def test_post_git_scm_with_custom_virtualenv(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: Git SCMプロジェクトをcustom_virtualenvと一緒に作成する場合
        期待値: success=True、custom_virtualenvが含まれる
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        mock_response = {
            'statusCode': 201,
            'responseContents': {'id': 100}
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        param = {
            'execution_no': '1',
            'scm_type': 'git',
            'scm_url': 'https://github.com/example/repo.git',
            'organization': 1,
            'custom_virtualenv': '/var/lib/awx/venv/ansible'
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is True

        call_args = mock_rest_api_caller.restCall.call_args
        content = call_args[0][2]
        assert content['custom_virtualenv'] == '/var/lib/awx/venv/ansible'

    def test_post_manual_scm_success(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: 手動プロジェクト（scm_type=""）の作成が成功する場合
        期待値: success=True、local_pathが設定される
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        mock_response = {
            'statusCode': 201,
            'responseContents': {
                'id': 100,
                'name': 'ita_legacy_executions_project_0000000001',
                'local_path': 'ita_legacy_executions_0000000001'
            }
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        # 手動プロジェクト
        param = {
            'execution_no': '1',
            'scm_type': '',  # 手動
            'organization': 1
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is True
        assert result['statusCode'] == 201

        call_args = mock_rest_api_caller.restCall.call_args
        content = call_args[0][2]
        assert content['name'] == 'ita_legacy_executions_project_0000000001'
        assert content['local_path'] == 'ita_legacy_executions_0000000001'
        assert 'scm_type' not in content  # 手動の場合はscm_typeが設定されない

    def test_post_missing_scm_type(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: scm_typeが欠けている場合
        期待値: success=False、エラーメッセージを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        param = {
            'execution_no': '1',
            'organization': 1
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is False
        assert 'errorMessage' in result['responseContents']
        assert result['responseContents']['errorMessage'] == "Need 'scm_type'."

    def test_post_scm_type_none(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: scm_typeがNoneの場合
        期待値: success=False、エラーメッセージを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        param = {
            'execution_no': '1',
            'scm_type': None,
            'organization': 1
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is False
        assert 'errorMessage' in result['responseContents']
        assert result['responseContents']['errorMessage'] == "Need 'scm_type'."

    def test_post_missing_organization(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: organizationが欠けている場合
        期待値: success=False、エラーメッセージを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        param = {
            'execution_no': '1',
            'scm_type': 'git',
            'scm_url': 'https://github.com/example/repo.git'
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is False
        assert 'errorMessage' in result['responseContents']
        assert result['responseContents']['errorMessage'] == "Need 'organization'."

    def test_post_git_scm_missing_scm_url(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: Git SCMでscm_urlが欠けている場合
        期待値: success=False、エラーメッセージを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        param = {
            'execution_no': '1',
            'scm_type': 'git',
            'organization': 1
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is False
        assert 'errorMessage' in result['responseContents']
        assert result['responseContents']['errorMessage'] == "Need 'scm_url'."

    def test_post_manual_scm_missing_execution_no(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: 手動プロジェクトでexecution_noが空の場合
        期待値: success=False、エラーメッセージを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        param = {
            'execution_no': '',  # 空文字列
            'scm_type': '',  # 手動
            'organization': 1
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is False
        assert 'errorMessage' in result['responseContents']
        assert result['responseContents']['errorMessage'] == "Need 'execution_no'."

    def test_post_api_failure_not_201(self, mock_rest_api_caller, mock_flask_g):
        """
        異常系: API呼び出しがステータスコード201以外を返す場合
        期待値: success=False、エラーメッセージを返す
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        # APIレスポンスのモック（失敗）
        mock_response = {
            'statusCode': 400,
            'responseContents': {}
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        param = {
            'execution_no': '1',
            'scm_type': 'git',
            'scm_url': 'https://github.com/example/repo.git',
            'organization': 1
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is False
        assert 'errorMessage' in result['responseContents']
        assert result['responseContents']['errorMessage'] == "status_code not 201. =>400"

    def test_post_with_execution_no_padding(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: execution_noが桁数少ない値の場合、パディングされる
        期待値: 名前とlocal_pathに10桁のゼロパディングされたexecution_noが使用される
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        mock_response = {
            'statusCode': 201,
            'responseContents': {'id': 100}
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        param = {
            'execution_no': '42',
            'scm_type': '',  # 手動
            'organization': 1
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is True

        # 名前とlocal_pathが正しくパディングされていることを確認
        call_args = mock_rest_api_caller.restCall.call_args
        content = call_args[0][2]
        assert content['name'] == 'ita_legacy_executions_project_0000000042'
        assert content['local_path'] == 'ita_legacy_executions_0000000042'

    def test_post_credential_none_not_included(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: credentialがNoneの場合、contentに含まれない
        期待値: success=True、credentialキーがcontentに含まれない
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        mock_response = {
            'statusCode': 201,
            'responseContents': {'id': 100}
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        param = {
            'execution_no': '1',
            'scm_type': 'git',
            'scm_url': 'https://github.com/example/repo.git',
            'organization': 1,
            'credential': None
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is True

        call_args = mock_rest_api_caller.restCall.call_args
        content = call_args[0][2]
        assert 'credential' not in content

    def test_post_custom_virtualenv_none_not_included(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: custom_virtualenvがNoneの場合、contentに含まれない
        期待値: success=True、custom_virtualenvキーがcontentに含まれない
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        mock_response = {
            'statusCode': 201,
            'responseContents': {'id': 100}
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        param = {
            'execution_no': '1',
            'scm_type': 'git',
            'scm_url': 'https://github.com/example/repo.git',
            'organization': 1,
            'custom_virtualenv': None
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is True

        call_args = mock_rest_api_caller.restCall.call_args
        content = call_args[0][2]
        assert 'custom_virtualenv' not in content

    def test_post_git_scm_with_all_optional_params(self, mock_rest_api_caller, mock_flask_g):
        """
        正常系: Git SCMプロジェクトを全てのオプションパラメータと共に作成する場合
        期待値: success=True、全てのパラメータが含まれる
        """
        from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects

        mock_response = {
            'statusCode': 201,
            'responseContents': {'id': 100}
        }
        mock_rest_api_caller.restCall.return_value = mock_response

        param = {
            'execution_no': '1',
            'scm_type': 'git',
            'scm_url': 'https://github.com/example/repo.git',
            'organization': 1,
            'credential': 999,
            'custom_virtualenv': '/var/lib/awx/venv/ansible'
        }

        result = AnsibleTowerRestApiProjects.post(mock_rest_api_caller, param)

        # 検証
        assert result['success'] is True

        call_args = mock_rest_api_caller.restCall.call_args
        content = call_args[0][2]
        assert content['name'] == 'ita_legacy_executions_project_0000000001'
        assert content['scm_type'] == 'git'
        assert content['scm_url'] == 'https://github.com/example/repo.git'
        assert content['organization'] == 1
        assert content['credential'] == 999
        assert content['custom_virtualenv'] == '/var/lib/awx/venv/ansible'
