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
from unittest.mock import Mock, patch, MagicMock


class TestCreateScmCredential:
    """create_scm_credential関数のテストクラス"""

    def test_create_scm_credential_success(self, create_execute_director_instance, mock_flask_g):
        """
        正常系: SCM認証情報の作成が成功する場合
        期待値: credential IDを返す
        """
        instance = create_execute_director_instance()
        execution_no = "12345"
        organization_id = 1

        # GitLabオブジェクトのモック
        mock_gitlab_obj = Mock()
        mock_gitlab_obj._GitLabAgent__user = "test_user"
        mock_gitlab_obj._GitLabAgent__token = "test_token_xyz"

        # API レスポンスのモック
        mock_response = {
            'success': True,
            'responseContents': {
                'id': 999
            }
        }

        with patch('common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials.AnsibleTowerRestApiCredentials.git_post_basic',
                   return_value=mock_response):
            result = instance.create_scm_credential(execution_no, mock_gitlab_obj, organization_id)

        # 検証
        assert result == 999

    def test_create_scm_credential_api_failure(self, create_execute_director_instance, mock_flask_g):
        """
        異常系: API呼び出しが失敗する場合
        期待値: -1を返す
        """
        instance = create_execute_director_instance()
        execution_no = "12345"
        organization_id = 1

        mock_gitlab_obj = Mock()
        mock_gitlab_obj._GitLabAgent__user = "test_user"
        mock_gitlab_obj._GitLabAgent__token = "test_token_xyz"

        # API 失敗レスポンス
        mock_response = {
            'success': False,
            'responseContents': {}
        }

        with patch('common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials.AnsibleTowerRestApiCredentials.git_post_basic',
                   return_value=mock_response):
            result = instance.create_scm_credential(execution_no, mock_gitlab_obj, organization_id)

        # 検証
        assert result == -1

    def test_create_scm_credential_no_id_in_response(self, create_execute_director_instance, mock_flask_g):
        """
        異常系: APIレスポンスにIDが含まれない場合
        期待値: -1を返す
        """
        instance = create_execute_director_instance()
        execution_no = "12345"
        organization_id = 1

        mock_gitlab_obj = Mock()
        mock_gitlab_obj._GitLabAgent__user = "test_user"
        mock_gitlab_obj._GitLabAgent__token = "test_token_xyz"

        # IDが無いレスポンス
        mock_response = {
            'success': True,
            'responseContents': {
                'name': 'test_credential'
            }
        }

        with patch('common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials.AnsibleTowerRestApiCredentials.git_post_basic',
                   return_value=mock_response):
            result = instance.create_scm_credential(execution_no, mock_gitlab_obj, organization_id)

        # 検証
        assert result == -1


class TestCleanUpSCMCredential:
    """cleanUpSCMCredential関数のテストクラス"""

    def test_cleanup_scm_credential_success(self, create_execute_director_instance, mock_flask_g):
        """
        正常系: SCM認証情報の削除が成功する場合
        期待値: Trueを返す
        """
        instance = create_execute_director_instance()

        # AACCreateObjectIDのモック
        mock_object_id = {"SCMCredentialId": [123]}
        with patch.object(instance, 'getAACCreateObjectID', return_value=mock_object_id):
            # 削除成功レスポンス
            mock_response = {
                'success': True
            }

            with patch('common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials.AnsibleTowerRestApiCredentials.deleteSCM',
                       return_value=mock_response):
                result = instance.cleanUpSCMCredential()

        # 検証
        assert result is True

    def test_cleanup_scm_credential_failure(self, create_execute_director_instance, mock_flask_g):
        """
        異常系: SCM認証情報の削除が失敗する場合
        期待値: Falseを返す
        """
        instance = create_execute_director_instance()

        mock_object_id = {"SCMCredentialId": [123]}
        with patch.object(instance, 'getAACCreateObjectID', return_value=mock_object_id):
            # 削除失敗レスポンス
            mock_response = {
                'success': False
            }

            with patch('common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials.AnsibleTowerRestApiCredentials.deleteSCM',
                       return_value=mock_response):
                result = instance.cleanUpSCMCredential()

        # 検証
        assert result is False


class TestSplitExecLog:
    """split_exec_log関数のテストクラス"""

    def test_split_exec_log_with_receiver_and_sender(self, create_execute_director_instance, mock_flask_g):
        """
        正常系: receiverとsenderの両方が含まれるログ
        期待値: 3つのカテゴリに正しく分類される
        """
        instance = create_execute_director_instance()

        log_content = """PLAY [all] *************
TASK [Gathering Facts] *************
ok: [host1]

TASK [include_tasks] *************
included: /path/to/ky_ansible_receiver.yaml

TASK [Receiver task 1] *************
ok: [host1]

TASK [Receiver task 2] *************
changed: [host1]

PLAY RECAP *************
host1 : ok=4    changed=1    unreachable=0    failed=0

TASK [include_tasks] *************
included: /path/to/ky_ansible_sender.yaml

TASK [Sender task 1] *************
ok: [host1]

TASK [Sender task 2] *************
changed: [host1]

PLAY RECAP *************
host1 : ok=3    changed=1    unreachable=0    failed=0"""

        result = instance.split_exec_log(log_content)

        # 検証
        assert 'receiver' in result
        assert 'sender' in result
        assert 'other' in result

        # receiverセクションにreceiver関連のタスクが含まれていること
        assert 'ky_ansible_receiver.yaml' in result['receiver']
        assert 'Receiver task 1' in result['receiver']
        assert 'Receiver task 2' in result['receiver']

        # senderセクションにsender関連のタスクが含まれていること
        assert 'ky_ansible_sender.yaml' in result['sender']
        assert 'Sender task 1' in result['sender']
        assert 'Sender task 2' in result['sender']

        # otherセクションに最初のPLAYが含まれていること
        assert 'PLAY [all]' in result['other']
        assert 'Gathering Facts' in result['other']

    def test_split_exec_log_receiver_terminated_by_role(self, create_execute_director_instance, mock_flask_g):
        """
        正常系: receiverセクションがRole実行で終了する場合
        期待値: receiverセクションがRole開始前で終了する
        """
        instance = create_execute_director_instance()

        log_content = """TASK [include_tasks] *************
included: /path/to/ky_ansible_receiver.yaml

TASK [Receiver task 1] *************
ok: [host1]

TASK [my_role : role task 1] *************
ok: [host1]

TASK [my_role : role task 2] *************
changed: [host1]

PLAY RECAP *************"""

        result = instance.split_exec_log(log_content)

        # 検証
        assert 'Receiver task 1' in result['receiver']
        assert 'my_role : role task 1' not in result['receiver']
        assert 'my_role : role task 1' in result['other']

    def test_split_exec_log_receiver_terminated_by_pioneer(self, create_execute_director_instance, mock_flask_g):
        """
        正常系: receiverセクションがpioneer_module execで終了する場合
        期待値: receiverセクションがpioneer実行前で終了する
        """
        instance = create_execute_director_instance()

        log_content = """TASK [include_tasks] *************
included: /path/to/ky_ansible_receiver.yaml

TASK [Receiver task 1] *************
ok: [host1]

TASK [pioneer_module exec] *************
ok: [host1]

PLAY RECAP *************"""

        result = instance.split_exec_log(log_content)

        # 検証
        assert 'Receiver task 1' in result['receiver']
        assert 'pioneer_module exec' not in result['receiver']
        assert 'pioneer_module exec' in result['other']

    def test_split_exec_log_with_child_playbooks(self, create_execute_director_instance, mock_flask_g):
        """
        正常系: child_playbooksが含まれる場合
        期待値: child_playbooksはotherに分類される
        """
        instance = create_execute_director_instance()

        log_content = """TASK [include_tasks] *************
included: /path/to/ky_ansible_receiver.yaml

TASK [Receiver task 1] *************
ok: [host1]

PLAY RECAP *************

TASK [include_tasks] *************
included: /path/to/child_playbooks/child1.yaml

TASK [Child task 1] *************
ok: [host1]

PLAY RECAP *************"""

        result = instance.split_exec_log(log_content)

        # 検証
        assert 'Receiver task 1' in result['receiver']
        assert 'child_playbooks/child1.yaml' not in result['receiver']
        assert 'child_playbooks/child1.yaml' in result['other']
        assert 'Child task 1' in result['other']

    def test_split_exec_log_empty_content(self, create_execute_director_instance, mock_flask_g):
        """
        正常系: 空のログ内容
        期待値: 全てのカテゴリが空文字列
        """
        instance = create_execute_director_instance()

        log_content = ""

        result = instance.split_exec_log(log_content)

        # 検証
        assert result['receiver'] == ''
        assert result['sender'] == ''
        assert result['other'] == ''

    def test_split_exec_log_no_receiver_or_sender(self, create_execute_director_instance, mock_flask_g):
        """
        正常系: receiverもsenderも含まれないログ
        期待値: 全てotherに分類される
        """
        instance = create_execute_director_instance()

        log_content = """PLAY [all] *************
TASK [Gathering Facts] *************
ok: [host1]

TASK [Some task] *************
changed: [host1]

PLAY RECAP *************
host1 : ok=3    changed=1    unreachable=0    failed=0"""

        result = instance.split_exec_log(log_content)

        # 検証
        assert result['receiver'] == ''
        assert result['sender'] == ''
        assert 'PLAY [all]' in result['other']
        assert 'Some task' in result['other']

    def test_split_exec_log_only_receiver(self, create_execute_director_instance, mock_flask_g):
        """
        正常系: receiverのみが含まれるログ
        期待値: receiverに正しく分類され、senderは空
        """
        instance = create_execute_director_instance()

        log_content = """TASK [include_tasks] *************
included: /path/to/ky_ansible_receiver.yaml

TASK [Receiver task 1] *************
ok: [host1]

PLAY RECAP *************
host1 : ok=2    changed=0    unreachable=0    failed=0"""

        result = instance.split_exec_log(log_content)

        # 検証
        assert 'ky_ansible_receiver.yaml' in result['receiver']
        assert 'Receiver task 1' in result['receiver']
        assert result['sender'] == ''

    def test_split_exec_log_only_sender(self, create_execute_director_instance, mock_flask_g):
        """
        正常系: senderのみが含まれるログ
        期待値: senderに正しく分類され、receiverは空
        """
        instance = create_execute_director_instance()

        log_content = """TASK [include_tasks] *************
included: /path/to/ky_ansible_sender.yaml

TASK [Sender task 1] *************
ok: [host1]

PLAY RECAP *************
host1 : ok=2    changed=0    unreachable=0    failed=0"""

        result = instance.split_exec_log(log_content)

        # 検証
        assert result['receiver'] == ''
        assert 'ky_ansible_sender.yaml' in result['sender']
        assert 'Sender task 1' in result['sender']
