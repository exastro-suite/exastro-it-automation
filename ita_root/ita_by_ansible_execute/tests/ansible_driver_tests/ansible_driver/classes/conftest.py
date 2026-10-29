import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from flask import Flask, g

# ita_rootをsys.pathに追加（pytest.iniのpythonpathが効かない場合の対策）
ita_root = '/workspace/exastro-it-automation-dev/ita_root'
if ita_root not in sys.path:
    sys.path.insert(0, ita_root)


@pytest.fixture
def flask_app_context():
    """Flaskアプリケーションコンテキストを作成"""
    flask_app = Flask(__name__)
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def mock_g(flask_app_context):
    """グローバル変数gをモック化"""
    g.LANGUAGE = "ja"
    g.USER_ID = "test_user_id"
    g.SERVICE_NAME = "test_service"
    g.WORKSPACE_ID = "test_workspace_id"
    g.ORGANIZATION_ID = "test_org_id"

    g.applogger = MagicMock()
    g.appmsg = MagicMock()
    g.appmsg.get_log_message.return_value = "Mocked log message"

    return g


@pytest.fixture
def mock_db():
    """データベースアクセスクラスのモック"""
    mock = MagicMock()
    mock.table_update.return_value = True
    return mock


@pytest.fixture
def mock_ans_if_info():
    """Ansible Interface情報のモックデータ"""
    return {
        "SERVICE_ACCOUNT_INFO": None,
        "SERVICE_ACCOUNT_TOKEN": None,
        "ANSIBLE_EXEC_MODE": "1"  # 1: Ansible, 2: AAC, 3: AG, 4: AAP on Cloud
    }


@pytest.fixture
def mock_env_vars():
    """環境変数のモック"""
    with patch.dict(os.environ, {
        'PLATFORM_API_HOST': 'localhost',
        'PLATFORM_API_PORT': '8000',
        'EXTERNAL_URL': 'https://example.com'
    }):
        yield


@pytest.fixture
def create_ansible_exec_files_instance(mock_g, mock_db, mock_ans_if_info, mock_env_vars):
    """CreateAnsibleExecFilesインスタンスを作成するファクトリフィクスチャ"""
    from common_libs.ansible_driver.classes.CreateAnsibleExecFiles import CreateAnsibleExecFiles

    def _create_instance(ans_if_info=None):
        if ans_if_info is None:
            ans_if_info = mock_ans_if_info

        instance = CreateAnsibleExecFiles(
            in_driver_id="L",  # "L": Legacy, "R": Legacy-Role, "P": Pioneer
            in_ans_if_info=ans_if_info,
            in_exec_no="12345",
            in_engine_virtualenv_name="",
            in_ansible_cnf_file="",
            in_objDBCA=mock_db
        )
        return instance

    return _create_instance
