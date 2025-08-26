import os
import pytest
from unittest.mock import MagicMock
from flask import Flask, g
from dotenv import load_dotenv  # python-dotenv
from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate


@pytest.fixture
def app_context_with_mock_g(mocker):
    # Flaskアプリのコンテキストを作成
    flask_app = Flask(__name__)
    with flask_app.app_context():
        # gオブジェクト全体をモックする
        mocker.patch('flask.g', autospec=True)

        # gの属性を個別に設定する
        g.LANGUAGE = "ja"
        g.USER_ID = "mock_user_id"
        g.SERVICE_NAME = "mock_service"
        g.WORKSPACE_ID = "mock_workspace_id"
        g.ORGANIZATION_ID = "mock_org_id"

        # g.apploggerとg.appmsgをモックする
        g.applogger = mocker.MagicMock()
        g.appmsg = mocker.MagicMock()
        g.appmsg.get_log_message.return_value = "Mocked log message"

        # g.get()メソッドをモックし、キーに応じて値を返すようにする
        g.get = mocker.MagicMock(side_effect=lambda key: {
            'ORGANIZATION_ID': g.ORGANIZATION_ID,
            'WORKSPACE_ID': g.WORKSPACE_ID,
            'USER_ID': g.USER_ID,
            'LANGUAGE': g.LANGUAGE
        }.get(key))

        yield g
