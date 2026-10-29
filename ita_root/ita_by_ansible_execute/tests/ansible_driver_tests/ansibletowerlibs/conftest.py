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
        g.appmsg = Mock()
        g.appmsg.get_api_message = Mock(side_effect=lambda msg_id, *args: f"Message {msg_id}")
        yield g


@pytest.fixture
def create_execute_director_instance(mock_flask_g):
    """ExecuteDirectorインスタンス生成用フィクスチャ"""
    def _create_instance(driver_id="R", ifInfoRow=None):
        from common_libs.ansible_driver.classes.ansibletowerlibs.ExecuteDirector import ExecuteDirector

        # デフォルトのifInfoRow
        if ifInfoRow is None:
            ifInfoRow = {
                "ANSIBLE_EXEC_MODE": "1",
                "ANSTWR_ORGANIZATION": "test_org",
                "ANSIBLE_STORAGE_PATH_LNX": "/test/storage",
                "ANSIBLE_VAULT_PASSWORD": None,
            }

        # モックオブジェクトの作成
        mock_rest_api_caller = Mock()
        mock_rest_api_caller.getRestResultList = Mock(return_value=[])

        mock_logger = Mock()
        mock_db_access = Mock()
        mock_db_access.table_select = Mock(return_value=[])
        mock_db_access.table_update = Mock(return_value=True)
        mock_db_access.sql_execute = Mock(return_value=[])

        exec_out_dir = "/test/exec/out"

        # ExecuteDirectorインスタンスを作成
        instance = ExecuteDirector(
            driver_id=driver_id,
            restApiCaller=mock_rest_api_caller,
            logger=mock_logger,
            dbAccess=mock_db_access,
            exec_out_dir=exec_out_dir,
            ifInfoRow=ifInfoRow,
            JobTemplatePropertyParameterAry={},
            JobTemplatePropertyNameAry={},
            TowerProjectsScpPath={},
            TowerInstanceDirPath={}
        )

        return instance

    return _create_instance
