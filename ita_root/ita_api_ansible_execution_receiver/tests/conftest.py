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
import datetime
from unittest.mock import Mock, MagicMock
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
        g.appmsg = Mock()
        g.appmsg.get_api_message = Mock(side_effect=lambda msg_id, *args: f"Message {msg_id}")
        g.appmsg.get_log_message = Mock(side_effect=lambda msg_id, *args: f"Log Message {msg_id}")
        g.maintenance_mode = {'data_update_stop': '0'}
        yield g


@pytest.fixture
def app():
    """Flaskアプリケーションのインスタンスを作成"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    yield app


@pytest.fixture
def app_context():
    """Flaskアプリケーションコンテキスト"""
    app = Flask(__name__)
    with app.app_context():
        yield


@pytest.fixture
def mock_g(mocker):
    """
    gオブジェクトをモックし、appmsgとapploggerを置き換える
    """
    mock_g_object = mocker.MagicMock()
    mock_g_object.appmsg = mocker.MagicMock()
    mock_g_object.applogger = mocker.MagicMock()
    mock_g_object.maintenance_mode = {'data_update_stop': '0'}

    # gオブジェクトを直接モックする
    mocker.patch('libs.ansible_execution.g', new=mock_g_object)

    return mock_g_object


@pytest.fixture
def mock_dbca():
    """
    objdbcaのモックオブジェクトを作成するフィクスチャ
    """
    mock = Mock()
    mock.table_select = Mock(return_value=[])
    mock.table_update = Mock(return_value=True)
    mock.sql_execute = Mock(return_value=[])
    mock.db_transaction_start = Mock()
    mock.db_transaction_end = Mock()
    mock.db_disconnect = Mock()
    mock._is_transaction = True
    return mock


@pytest.fixture
def mock_connexion_request():
    """connexion.requestのモック"""
    mock_request = Mock()
    mock_request.files = {}
    mock_request.headers = Mock()
    mock_request.headers.get = Mock(return_value="1000")
    return mock_request


@pytest.fixture
def sample_execution_data():
    """テスト用の作業実行データ"""
    return {
        'EXECUTION_NO': '00000000-0000-0000-0000-000000000001',
        'RUN_MODE': '1',
        'STATUS_ID': '11',
        'EXEC_MODE': '3',
        'ABORT_EXECUTE_FLAG': '0',
        'CONDUCTOR_NAME': None,
        'EXECUTION_USER': 'test_user',
        'TIME_REGISTER': datetime.datetime(2025, 8, 27, 14, 7, 11),
        'MOVEMENT_ID': '00000000-0000-0000-0000-0000000000mv',
        'I_MOVEMENT_NAME': 'TestMovement',
        'I_TIME_LIMIT': None,
        'I_ANS_HOST_DESIGNATE_TYPE_ID': '1',
        'I_ANS_PARALLEL_EXE': None,
        'I_ANS_WINRM_ID': None,
        'I_ANS_PLAYBOOK_HED_DEF': '- hosts: all\n  remote_user: "{{ __loginuser__ }}"\n  gather_facts: no',
        'I_AG_EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
        'I_AG_BUILDER_OPTIONS': None,
        'I_EXECUTION_ENVIRONMENT_NAME': None,
        'I_ANSIBLE_CONFIG_FILE': None,
        'OPERATION_ID': '00000000-0000-0000-0000-0000000000op',
        'I_OPERATION_NAME': 'TestOperation',
        'FILE_INPUT': 'InputData_00000000-0000-0000-0000-000000000001.zip',
        'FILE_RESULT': None,
        'TIME_BOOK': None,
        'TIME_START': datetime.datetime(2025, 8, 27, 14, 7, 15),
        'TIME_END': None,
        'COLLECT_STATUS': None,
        'COLLECT_LOG': None,
        'CONDUCTOR_INSTANCE_NO': None,
        'I_ANS_EXEC_OPTIONS': None,
        'LOGFILELIST_JSON': None,
        'MULTIPLELOG_MODE': None,
        'EXECUTE_HOST_NAME': 'test_host',
        'NOTE': None,
        'DISUSE_FLAG': '0',
        'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 14, 7, 15, 61810),
        'LAST_UPDATE_USER': '1'
    }


@pytest.fixture
def sample_conductor_execution_data():
    """Conductor経由の作業実行データ"""
    return {
        'EXECUTION_NO': '00000000-0000-0000-0000-000000000002',
        'RUN_MODE': '1',
        'STATUS_ID': '11',
        'EXEC_MODE': '3',
        'ABORT_EXECUTE_FLAG': '0',
        'CONDUCTOR_NAME': 'TestConductor',
        'EXECUTION_USER': 'test_user',
        'TIME_REGISTER': datetime.datetime(2025, 8, 27, 14, 7, 11),
        'MOVEMENT_ID': '00000000-0000-0000-0000-0000000000mv',
        'I_MOVEMENT_NAME': 'TestMovement',
        'CONDUCTOR_INSTANCE_NO': '00000000-0000-0000-0000-000000000cnd',
        'DISUSE_FLAG': '0',
        'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 14, 7, 15, 61810),
        'LAST_UPDATE_USER': '1'
    }
