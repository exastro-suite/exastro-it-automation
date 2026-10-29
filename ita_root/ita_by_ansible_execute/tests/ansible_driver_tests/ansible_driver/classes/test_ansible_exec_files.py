#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License")
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
import json
import tempfile
from unittest.mock import Mock, patch, mock_open
from datetime import datetime, timezone, timedelta
from pathlib import Path
from common_libs.common.util import ky_encrypt, ky_decrypt


class TestGetSAToken:
    """getSAToken関数のテストクラス"""

    def test_getSAToken_valid_token_exists(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: 有効なトークンがDBに存在し、internal-apiで確認できる場合
        期待値: DBの既存トークンを復号化して返す
        """
        # 10日以上先の有効期限を設定
        future_date = datetime.now(timezone.utc) + timedelta(days=15)
        token_id = "test_token_id_001"
        refresh_token = "test_refresh_token_123"

        # Ansible Interface情報を設定
        ans_if_info = {
            "SERVICE_ACCOUNT_INFO": json.dumps({
                "id": token_id,
                "expiresdate": future_date.isoformat()
            }),
            "SERVICE_ACCOUNT_TOKEN": ky_encrypt(refresh_token),
            "ANSIBLE_EXEC_MODE": "1"
        }

        instance = create_ansible_exec_files_instance(ans_if_info)

        # refresh_tokens_checkをモック化（トークンが存在することを返す）
        with patch.object(instance, 'refresh_tokens_check', return_value=(True, "exists")):
            result, token = instance.getSAToken()

        # 検証
        assert result is True
        assert token == refresh_token

    def test_getSAToken_token_expired_less_than_10_days(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: トークンの有効期限が10日未満の場合
        期待値: 新しいトークンを作成してDBを更新
        """
        # 5日後の有効期限を設定（10日未満）
        near_future_date = datetime.now(timezone.utc) + timedelta(days=5)
        token_id = "test_token_id_002"
        old_refresh_token = "old_refresh_token_123"
        new_refresh_token = "new_refresh_token_456"

        ans_if_info = {
            "SERVICE_ACCOUNT_INFO": json.dumps({
                "id": token_id,
                "expiresdate": near_future_date.isoformat()
            }),
            "SERVICE_ACCOUNT_TOKEN": ky_encrypt(old_refresh_token),
            "ANSIBLE_EXEC_MODE": "1"
        }

        instance = create_ansible_exec_files_instance(ans_if_info)

        # sa_refresh_tokens_newをモック化
        new_token_data = {
            "id": "new_token_id_001",
            "refresh_token_expire": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "refresh_token": new_refresh_token
        }
        with patch.object(instance, 'sa_refresh_tokens_new', return_value=(True, new_token_data)):
            result, token = instance.getSAToken()

        # 検証
        assert result is True
        assert token == new_refresh_token
        # DBのtable_updateが呼ばれたことを確認
        instance.lv_objDBCA.table_update.assert_called_once()

    def test_getSAToken_token_not_found_in_api(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: トークンがinternal-apiで見つからない場合
        期待値: 新しいトークンを作成してDBを更新
        """
        future_date = datetime.now(timezone.utc) + timedelta(days=15)
        token_id = "test_token_id_003"
        old_refresh_token = "old_refresh_token_789"
        new_refresh_token = "new_refresh_token_101"

        ans_if_info = {
            "SERVICE_ACCOUNT_INFO": json.dumps({
                "id": token_id,
                "expiresdate": future_date.isoformat()
            }),
            "SERVICE_ACCOUNT_TOKEN": ky_encrypt(old_refresh_token),
            "ANSIBLE_EXEC_MODE": "1"
        }

        instance = create_ansible_exec_files_instance(ans_if_info)

        # refresh_tokens_checkをモック化（トークンが見つからない）
        # sa_refresh_tokens_newをモック化
        new_token_data = {
            "id": "new_token_id_002",
            "refresh_token_expire": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "refresh_token": new_refresh_token
        }
        with patch.object(instance, 'refresh_tokens_check', return_value=(False, "token not found")), \
             patch.object(instance, 'sa_refresh_tokens_new', return_value=(True, new_token_data)):
            result, token = instance.getSAToken()

        # 検証
        assert result is True
        assert token == new_refresh_token

    def test_getSAToken_db_initial_state(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: DBが初期状態（SERVICE_ACCOUNT_INFOがNone）の場合
        期待値: 新しいトークンを作成してDBを更新
        """
        new_refresh_token = "new_refresh_token_initial"

        ans_if_info = {
            "SERVICE_ACCOUNT_INFO": None,
            "SERVICE_ACCOUNT_TOKEN": None,
            "ANSIBLE_EXEC_MODE": "1"
        }

        instance = create_ansible_exec_files_instance(ans_if_info)

        # sa_refresh_tokens_newをモック化
        new_token_data = {
            "id": "new_token_id_003",
            "refresh_token_expire": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "refresh_token": new_refresh_token
        }
        with patch.object(instance, 'sa_refresh_tokens_new', return_value=(True, new_token_data)):
            result, token = instance.getSAToken()

        # 検証
        assert result is True
        assert token == new_refresh_token
        instance.lv_objDBCA.table_update.assert_called_once()

    def test_getSAToken_invalid_json_in_db(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: DBの値が不正なJSON形式の場合
        期待値: 新しいトークンを作成してDBを更新
        """
        new_refresh_token = "new_refresh_token_invalid"

        ans_if_info = {
            "SERVICE_ACCOUNT_INFO": "invalid_json_string",
            "SERVICE_ACCOUNT_TOKEN": "invalid_token",
            "ANSIBLE_EXEC_MODE": "1"
        }

        instance = create_ansible_exec_files_instance(ans_if_info)

        # sa_refresh_tokens_newをモック化
        new_token_data = {
            "id": "new_token_id_004",
            "refresh_token_expire": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "refresh_token": new_refresh_token
        }
        with patch.object(instance, 'sa_refresh_tokens_new', return_value=(True, new_token_data)):
            result, token = instance.getSAToken()

        # 検証
        assert result is True
        assert token == new_refresh_token

    def test_getSAToken_sa_refresh_tokens_new_fails(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: sa_refresh_tokens_newが失敗した場合
        期待値: (False, エラーメッセージ)を返す
        """
        ans_if_info = {
            "SERVICE_ACCOUNT_INFO": None,
            "SERVICE_ACCOUNT_TOKEN": None,
            "ANSIBLE_EXEC_MODE": "1"
        }

        instance = create_ansible_exec_files_instance(ans_if_info)

        error_msg = "Failed to create refresh token"
        with patch.object(instance, 'sa_refresh_tokens_new', return_value=(False, error_msg)):
            result, msg = instance.getSAToken()

        # 検証
        assert result is False
        assert msg == error_msg


class TestInternalPost:
    """internalpost関数のテストクラス"""

    def test_internalpost_success(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: POSTリクエストが成功する場合
        期待値: (True, response)を返す
        """
        instance = create_ansible_exec_files_instance()
        uri = "http://localhost:8000/test/endpoint"
        request_data = {"key": "value"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}

        with patch('requests.Session') as mock_session:
            mock_session.return_value.request.return_value = mock_response
            result, response = instance.internalpost(uri, request_data)

        # 検証
        assert result is True
        assert response.status_code == 200
        assert response.json() == {"result": "success"}

    def test_internalpost_exception(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: POSTリクエストで例外が発生する場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        uri = "http://localhost:8000/test/endpoint"
        request_data = {"key": "value"}

        with patch('requests.Session') as mock_session:
            mock_session.return_value.request.side_effect = Exception("Connection error")
            result, msg = instance.internalpost(uri, request_data)

        # 検証
        assert result is False
        assert "Internal API request failed" in msg
        assert "Connection error" in msg


class TestInternalGet:
    """internalget関数のテストクラス"""

    def test_internalget_success(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: GETリクエストが成功する場合
        期待値: (True, response)を返す
        """
        instance = create_ansible_exec_files_instance()
        uri = "http://localhost:8000/test/endpoint"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}

        with patch('requests.Session') as mock_session:
            mock_session.return_value.request.return_value = mock_response
            result, response = instance.internalget(uri)

        # 検証
        assert result is True
        assert response.status_code == 200

    def test_internalget_exception(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: GETリクエストで例外が発生する場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        uri = "http://localhost:8000/test/endpoint"

        with patch('requests.Session') as mock_session:
            mock_session.return_value.request.side_effect = Exception("Timeout error")
            result, msg = instance.internalget(uri)

        # 検証
        assert result is False
        assert "Internal API request failed" in msg
        assert "Timeout error" in msg


class TestSaExistsCheck:
    """sa_exists_check関数のテストクラス"""

    def test_sa_exists_check_user_found(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: サービスアカウントが存在する場合
        期待値: (True, ユーザーID)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "aap_service_account_user"
        user_id = "sa_user_id_001"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": user_id, "username": username},
                {"id": "other_id", "username": "other_user"}
            ]
        }

        with patch.object(instance, 'internalget', return_value=(True, mock_response)):
            result, uid = instance.sa_exists_check(username)

        # 検証
        assert result is True
        assert uid == user_id

    def test_sa_exists_check_user_not_found(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: サービスアカウントが存在しない場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "non_existent_user"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "other_id", "username": "other_user"}
            ]
        }

        with patch.object(instance, 'internalget', return_value=(True, mock_response)):
            result, msg = instance.sa_exists_check(username)

        # 検証
        assert result is False
        assert username in msg
        assert "is not in ServiceAccountList" in msg

    def test_sa_exists_check_api_error(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: internal-apiがエラーを返す場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "test_user"

        with patch.object(instance, 'internalget', return_value=(False, "API connection error")):
            result, msg = instance.sa_exists_check(username)

        # 検証
        assert result is False
        assert msg == "API connection error"

    def test_sa_exists_check_non_200_status(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: internal-apiが200以外のステータスコードを返す場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "test_user"

        mock_response = Mock()
        mock_response.status_code = 500

        with patch.object(instance, 'internalget', return_value=(True, mock_response)):
            result, msg = instance.sa_exists_check(username)

        # 検証
        assert result is False
        assert "non-200 status" in msg
        assert "500" in msg


class TestSaCreate:
    """sa_create関数のテストクラス"""

    def test_sa_create_success(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: サービスアカウント作成が成功する場合
        期待値: (True, ユーザーID)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "new_service_account"
        user_id = "new_sa_id_001"

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(instance, 'internalpost', return_value=(True, mock_response)), \
             patch.object(instance, 'sa_exists_check', return_value=(True, user_id)):
            result, uid = instance.sa_create(username)

        # 検証
        assert result is True
        assert uid == user_id

    def test_sa_create_api_error(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: internalpostがエラーを返す場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "new_service_account"

        with patch.object(instance, 'internalpost', return_value=(False, "POST failed")):
            result, msg = instance.sa_create(username)

        # 検証
        assert result is False
        assert msg == "POST failed"

    def test_sa_create_non_200_status(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: サービスアカウント作成APIが200以外を返す場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "new_service_account"

        mock_response = Mock()
        mock_response.status_code = 400

        with patch.object(instance, 'internalpost', return_value=(True, mock_response)):
            result, msg = instance.sa_create(username)

        # 検証
        assert result is False
        assert "non-200 status" in msg


class TestRefreshTokensCheck:
    """refresh_tokens_check関数のテストクラス"""

    def test_refresh_tokens_check_token_exists(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: トークンIDが存在する場合
        期待値: (True, "exists")を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "aap_service_account_user"
        token_id = "token_id_001"
        user_id = "sa_user_id_001"

        mock_tokenlist_response = Mock()
        mock_tokenlist_response.status_code = 200
        mock_tokenlist_response.json.return_value = {
            "data": [
                {"id": token_id, "description": "test token"},
                {"id": "other_token_id", "description": "other token"}
            ]
        }

        with patch.object(instance, 'sa_exists_check', return_value=(True, user_id)), \
             patch.object(instance, 'internalget', return_value=(True, mock_tokenlist_response)):
            result, msg = instance.refresh_tokens_check(username, token_id)

        # 検証
        assert result is True
        assert msg == "exists"

    def test_refresh_tokens_check_token_not_found(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: トークンIDが存在しない場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "aap_service_account_user"
        token_id = "non_existent_token_id"
        user_id = "sa_user_id_001"

        mock_tokenlist_response = Mock()
        mock_tokenlist_response.status_code = 200
        mock_tokenlist_response.json.return_value = {
            "data": [
                {"id": "other_token_id", "description": "other token"}
            ]
        }

        with patch.object(instance, 'sa_exists_check', return_value=(True, user_id)), \
             patch.object(instance, 'internalget', return_value=(True, mock_tokenlist_response)):
            result, msg = instance.refresh_tokens_check(username, token_id)

        # 検証
        assert result is False
        assert token_id in msg
        assert "is not in ServiceAccount" in msg

    def test_refresh_tokens_check_sa_not_found(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: サービスアカウントが存在しない場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "non_existent_user"
        token_id = "token_id_001"

        with patch.object(instance, 'sa_exists_check', return_value=(False, "SA not found")):
            result, msg = instance.refresh_tokens_check(username, token_id)

        # 検証
        assert result is False
        assert msg == "SA not found"


class TestRefreshTokensCheckFromDate:
    """refresh_tokens_check_fromdate関数のテストクラス"""

    def test_refresh_tokens_check_fromdate_found(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: 有効期限からトークンIDが見つかる場合
        期待値: (True, トークンID)を返す
        """
        instance = create_ansible_exec_files_instance()
        user_id = "sa_user_id_001"
        expire_date = "2026-12-31T23:59:59Z"
        token_id = "token_id_from_date"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": token_id, "expire_timestamp": expire_date},
                {"id": "other_token_id", "expire_timestamp": "2026-01-01T00:00:00Z"}
            ]
        }

        with patch.object(instance, 'internalget', return_value=(True, mock_response)):
            result, tid = instance.refresh_tokens_check_fromdate(user_id, expire_date)

        # 検証
        assert result is True
        assert tid == token_id

    def test_refresh_tokens_check_fromdate_not_found(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: 有効期限に一致するトークンが見つからない場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        user_id = "sa_user_id_001"
        expire_date = "2026-12-31T23:59:59Z"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "other_token_id", "expire_timestamp": "2026-01-01T00:00:00Z"}
            ]
        }

        with patch.object(instance, 'internalget', return_value=(True, mock_response)):
            result, msg = instance.refresh_tokens_check_fromdate(user_id, expire_date)

        # 検証
        assert result is False
        assert expire_date in msg


class TestRefreshTokensNew:
    """refresh_tokens_new関数のテストクラス"""

    def test_refresh_tokens_new_success(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: 新しいリフレッシュトークンの発行に成功する場合
        期待値: (True, トークンデータ)を返す
        """
        instance = create_ansible_exec_files_instance()
        user_id = "sa_user_id_001"
        token_data = {
            "refresh_token": "new_token_xyz",
            "refresh_token_expire": "2026-12-31T23:59:59Z"
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": token_data}

        with patch.object(instance, 'internalpost', return_value=(True, mock_response)):
            result, data = instance.refresh_tokens_new(user_id)

        # 検証
        assert result is True
        assert data == token_data

    def test_refresh_tokens_new_api_error(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: トークン発行APIがエラーを返す場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        user_id = "sa_user_id_001"

        with patch.object(instance, 'internalpost', return_value=(False, "POST failed")):
            result, msg = instance.refresh_tokens_new(user_id)

        # 検証
        assert result is False
        assert msg == "POST failed"


class TestSaRefreshTokensNew:
    """sa_refresh_tokens_new関数のテストクラス"""

    def test_sa_refresh_tokens_new_sa_exists(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: サービスアカウントが存在する場合
        期待値: リフレッシュトークンを発行して返す
        """
        instance = create_ansible_exec_files_instance()
        username = "aap_service_account_user"
        user_id = "sa_user_id_001"
        token_id = "new_token_id"
        token_data = {
            "refresh_token": "new_token_abc",
            "refresh_token_expire": "2026-12-31T23:59:59Z"
        }

        with patch.object(instance, 'sa_exists_check', return_value=(True, user_id)), \
             patch.object(instance, 'refresh_tokens_new', return_value=(True, token_data)), \
             patch.object(instance, 'refresh_tokens_check_fromdate', return_value=(True, token_id)):
            result, return_dict = instance.sa_refresh_tokens_new(username)

        # 検証
        assert result is True
        assert return_dict["id"] == token_id
        assert return_dict["refresh_token"] == token_data["refresh_token"]
        assert return_dict["refresh_token_expire"] == token_data["refresh_token_expire"]

    def test_sa_refresh_tokens_new_sa_not_exists_create_success(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: サービスアカウントが存在せず、作成に成功する場合
        期待値: サービスアカウントを作成してトークンを発行
        """
        instance = create_ansible_exec_files_instance()
        username = "aap_service_account_user"
        user_id = "new_sa_user_id"
        token_id = "new_token_id"
        token_data = {
            "refresh_token": "new_token_def",
            "refresh_token_expire": "2026-12-31T23:59:59Z"
        }

        with patch.object(instance, 'sa_exists_check', return_value=(False, f"{username} is not in ServiceAccountList")), \
             patch.object(instance, 'sa_create', return_value=(True, user_id)), \
             patch.object(instance, 'refresh_tokens_new', return_value=(True, token_data)), \
             patch.object(instance, 'refresh_tokens_check_fromdate', return_value=(True, token_id)):
            result, return_dict = instance.sa_refresh_tokens_new(username)

        # 検証
        assert result is True
        assert return_dict["id"] == token_id
        assert return_dict["refresh_token"] == token_data["refresh_token"]

    def test_sa_refresh_tokens_new_sa_create_fails(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: サービスアカウント作成に失敗する場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "aap_service_account_user"

        with patch.object(instance, 'sa_exists_check', return_value=(False, f"{username} is not in ServiceAccountList")), \
             patch.object(instance, 'sa_create', return_value=(False, "SA creation failed")):
            result, msg = instance.sa_refresh_tokens_new(username)

        # 検証
        assert result is False
        assert msg == "SA creation failed"

    def test_sa_refresh_tokens_new_token_creation_fails(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: トークン発行に失敗する場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "aap_service_account_user"
        user_id = "sa_user_id_001"

        with patch.object(instance, 'sa_exists_check', return_value=(True, user_id)), \
             patch.object(instance, 'refresh_tokens_new', return_value=(False, "Token creation failed")):
            result, msg = instance.sa_refresh_tokens_new(username)

        # 検証
        assert result is False
        assert msg == "Token creation failed"

    def test_sa_refresh_tokens_new_api_error(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: internal-apiでエラーが発生する場合
        期待値: (False, エラーメッセージ)を返す
        """
        instance = create_ansible_exec_files_instance()
        username = "aap_service_account_user"

        with patch.object(instance, 'sa_exists_check', return_value=(False, "API connection error")):
            result, msg = instance.sa_refresh_tokens_new(username)

        # 検証
        assert result is False
        assert msg == "API connection error"


class TestCreateAnsibleWorkingDir:
    """CreateAnsibleWorkingDir関数のテストクラス"""

    def test_create_working_dir_success(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: 作業ディレクトリが正常に作成される場合
        期待値: True, 各種パラメータが返される
        """
        instance = create_ansible_exec_files_instance()

        # テスト用の一時ディレクトリを作成
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            working_dir = base_dir / "ansible" / "legacy" / "12345"
            working_dir.mkdir(parents=True, exist_ok=True)

            # getAnsibleWorkingDirectoriesをモック化
            mock_dirs = [
                str(base_dir / "ansible"),
                str(base_dir / "ansible" / "legacy"),
                str(working_dir),
                str(working_dir / "in"),
                str(working_dir / "out"),
            ]

            with patch.object(instance, 'getAnsibleWorkingDirectories', return_value=mock_dirs), \
                 patch.object(instance, 'getTowerProjectDirPath', return_value="/var/lib/exastro"), \
                 patch.object(instance, 'setTowerProjectsScpPath'), \
                 patch('os.path.isdir', return_value=True), \
                 patch('common_libs.common.util.retry_makedirs'), \
                 patch('common_libs.common.util.retry_chmod'):

                result, rolenames, rolevars, roleglobalvars, role_pkg_id, def_vars, def_array_vars = \
                    instance.CreateAnsibleWorkingDir(
                        in_oct_id="org1",
                        in_execno="12345",
                        in_operation_id="op001",
                        in_hostaddress_type="1",
                        in_winrm_id=None,
                        in_pattern_id="pattern001",
                        mt_rolenames={},
                        mt_rolevars={},
                        mt_roleglobalvars={},
                        mt_role_rolepackage_id={},
                        mt_def_vars_list={},
                        mt_def_array_vars_list={},
                        in_conductor_instance_no=""
                    )

                # 検証
                assert result is True

    def test_create_working_dir_directory_not_exists(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: 必要なディレクトリが存在しない場合
        期待値: False, エラーメッセージ
        """
        instance = create_ansible_exec_files_instance()

        # getAnsibleWorkingDirectoriesをモック化
        mock_dirs = [
            "/nonexistent/ansible",
            "/nonexistent/ansible/legacy",
            "/nonexistent/ansible/legacy/12345",
            "/nonexistent/ansible/legacy/12345/in",
            "/nonexistent/ansible/legacy/12345/out",
        ]

        with patch.object(instance, 'getAnsibleWorkingDirectories', return_value=mock_dirs), \
             patch('os.path.isdir', return_value=False), \
             patch.object(instance, 'LocalLogPrint'):

            result, rolenames, rolevars, roleglobalvars, role_pkg_id, def_vars, def_array_vars = \
                instance.CreateAnsibleWorkingDir(
                    in_oct_id="org1",
                    in_execno="12345",
                    in_operation_id="op001",
                    in_hostaddress_type="1",
                    in_winrm_id=None,
                    in_pattern_id="pattern001",
                    mt_rolenames={},
                    mt_rolevars={},
                    mt_roleglobalvars={},
                    mt_role_rolepackage_id={},
                    mt_def_vars_list={},
                    mt_def_array_vars_list={},
                    in_conductor_instance_no=""
                )

            # 検証
            assert result is False


class TestCreateTransferPlaybookfiles:
    """CreateTransferPlaybookfiles関数のテストクラス"""

    def test_create_transfer_playbook_aap_cloud_success(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: AAP Cloud用のPlaybookファイルを作成（DB正常、ファイル操作モック）
        期待値: True、retry_copyfileが2回呼ばれる
        """
        instance = create_ansible_exec_files_instance()

        # AAP Cloud実行モードを設定
        instance.lv_exec_mode = "4"  # AAP on Cloud

        with tempfile.TemporaryDirectory() as tmpdir:
            instance.lv_Ansible_in_Dir = str(Path(tmpdir) / "in")

            # DBモックデータ
            mock_db_rows_fetch = [{
                "ROW_ID": "test_row_id_1",
                "ASSET_NAME": "__ita_fetch_common__",
                "ASSET_FILE": "receiver.yaml"
            }]
            mock_db_rows_put = [{
                "ROW_ID": "test_row_id_2",
                "ASSET_NAME": "__ita_put_results__",
                "ASSET_FILE": "sender.yaml"
            }]

            def mock_table_select(table, where, params):
                if params[0] == "__ita_fetch_common__":
                    return mock_db_rows_fetch
                elif params[0] == "__ita_put_results__":
                    return mock_db_rows_put
                return []

            with patch.object(instance.lv_objDBCA, 'table_select', side_effect=mock_table_select), \
                 patch('common_libs.ansible_driver.functions.util.getDataRelayStorageDir', return_value="/tmp/storage"), \
                 patch('common_libs.ansible_driver.classes.CreateAnsibleExecFiles.retry_copyfile') as mock_copyfile, \
                 patch.object(instance, 'LocalLogPrint'):

                result = instance.CreateTransferPlaybookfiles(in_exec_mode="4")

                # 検証
                assert result is True
                # retry_copyfileが2回呼ばれたことを確認（fetch用とput用）
                assert mock_copyfile.call_count == 2

    def test_create_transfer_playbook_aap_cloud_no_records(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: AAP Cloud用のPlaybookファイル作成（DBに該当レコードなし）
        期待値: False
        """
        instance = create_ansible_exec_files_instance()

        instance.lv_exec_mode = "4"

        with tempfile.TemporaryDirectory() as tmpdir:
            instance.lv_Ansible_in_Dir = str(Path(tmpdir) / "in")

            # DBモックデータ（レコードなし）
            mock_db_rows_empty = []

            with patch.object(instance.lv_objDBCA, 'table_select', return_value=mock_db_rows_empty), \
                 patch.object(instance, 'LocalLogPrint'):

                result = instance.CreateTransferPlaybookfiles(in_exec_mode="4")

                # 検証
                assert result is False

    def test_create_transfer_playbook_aap_cloud_multiple_records(self, create_ansible_exec_files_instance, mock_g):
        """
        異常系: AAP Cloud用のPlaybookファイル作成（DB に複数レコード）
        期待値: False
        """
        instance = create_ansible_exec_files_instance()

        instance.lv_exec_mode = "4"

        with tempfile.TemporaryDirectory() as tmpdir:
            instance.lv_Ansible_in_Dir = str(Path(tmpdir) / "in")

            # DBモックデータ（複数レコード）
            mock_db_rows_multiple = [
                {"ROW_ID": "test_row_id_1", "ASSET_FILE": "receiver1.yaml"},
                {"ROW_ID": "test_row_id_2", "ASSET_FILE": "receiver2.yaml"}
            ]

            with patch.object(instance.lv_objDBCA, 'table_select', return_value=mock_db_rows_multiple), \
                 patch.object(instance, 'LocalLogPrint'):

                result = instance.CreateTransferPlaybookfiles(in_exec_mode="4")

                # 検証
                assert result is False

    def test_create_transfer_playbook_not_aap_cloud(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: AAP Cloud以外の実行モード
        期待値: True（何もせずに成功）
        """
        instance = create_ansible_exec_files_instance()

        # Ansible実行モードを設定
        instance.lv_exec_mode = "1"  # Ansible

        result = instance.CreateTransferPlaybookfiles(in_exec_mode="1")

        # 検証
        assert result is True


class TestCreategitkeep:
    """Creategitkeep関数のテストクラス"""

    def test_create_gitkeep_aap_cloud(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: AAP Cloud用の.gitkeepファイルを作成
        期待値: True
        """
        instance = create_ansible_exec_files_instance()

        # AAP Cloud実行モードを設定
        instance.lv_exec_mode = "4"

        with tempfile.TemporaryDirectory() as tmpdir:
            instance.lv_Ansible_in_Dir = tmpdir

            with patch('builtins.open', mock_open()), \
                 patch('common_libs.common.util.retry_chmod'):

                result = instance.Creategitkeep(in_exec_mode="4")

                # 検証
                assert result is True

    def test_create_gitkeep_not_aap_cloud(self, create_ansible_exec_files_instance, mock_g):
        """
        正常系: AAP Cloud以外の実行モード
        期待値: True（何もせずに成功）
        """
        instance = create_ansible_exec_files_instance()

        instance.lv_exec_mode = "1"

        result = instance.Creategitkeep(in_exec_mode="1")

        # 検証
        assert result is True
