import datetime
import pytest
from unittest.mock import Mock
from flask import Flask, g

import common_libs.oase.manage_events as clome
import backyard_main as bm
import libs.action as la
import libs.common_functions as cf
from tests.test_double import DummyAppMsg, DummyConductorExecuteBkyLibs, DummyDB, DummyLogger, DummyNotificationPM, DummyWriterPM, MockMONGOConnectWs


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


# ===== フィクスチャー =====


@pytest.fixture
def patch_global_g(monkeypatch):
    """グローバル変数gをパッチ（Flaskアプリケーションコンテキスト付き）"""
    # Flaskアプリのコンテキストを作成
    flask_app = Flask(__name__)
    with flask_app.app_context():
        # gオブジェクト全体をモックする
        monkeypatch.setattr("flask.g", g, raising=False)

        # gの属性を個別に設定する
        g.LANGUAGE = "ja"
        g.USER_ID = "mock_user_id"
        g.SERVICE_NAME = "mock_service"
        g.WORKSPACE_ID = "mock_workspace_id"
        g.ORGANIZATION_ID = "mock_org_id"

        # g.apploggerとg.appmsgをモックする
        g.applogger = DummyLogger()
        g.appmsg = DummyAppMsg()

        # g.get()メソッドをモックし、キーに応じて値を返すようにする
        def mock_get(key):
            match key:
                case "ORGANIZATION_ID":
                    return g.ORGANIZATION_ID
                case "WORKSPACE_ID":
                    return g.WORKSPACE_ID
                case "USER_ID":
                    return g.USER_ID
                case "LANGUAGE":
                    return g.LANGUAGE
                case "SERVICE_NAME":
                    return g.SERVICE_NAME
                case _:
                    return None

        g.get = mock_get

        yield g


@pytest.fixture
def patch_datetime(monkeypatch):
    """datetime.datetime.nowをパッチして固定値を返す"""
    mock_datetime = Mock()
    mock_datetime.judge_time = 1640995200  # 2022-01-01 00:00:00
    mock_datetime.timezone = datetime.timezone
    
    def get_judge_time_as_datetime(tz=None):
        return datetime.datetime.fromtimestamp(mock_datetime.judge_time, tz)
    mock_datetime.datetime.now = get_judge_time_as_datetime
    monkeypatch.setattr(bm, "datetime", mock_datetime)
    monkeypatch.setattr(cf, "datetime", mock_datetime)
    return mock_datetime


@pytest.fixture
def patch_database_connections(monkeypatch):
    """データベース接続関数をパッチ"""

    mock_mongo = MockMONGOConnectWs()
    ws_db = DummyDB("ws1")

    monkeypatch.setattr(bm, "DBConnectWs", lambda workspace_id: ws_db)
    monkeypatch.setattr(bm, "MONGOConnectWs", lambda: mock_mongo)

    return (ws_db, mock_mongo)


@pytest.fixture
def patch_notification_and_writer(monkeypatch, patch_database_connections):
    """通知とライタープロセスをパッチ"""

    ws_db, mock_mongo = patch_database_connections
    calls = {
        "notification_start_ws": 0,
        "notification_finish_ws": 0,
        "writer_start_ws": 0,
        "writer_finish_ws": 0,
        "notifications": [],
        "insert_action_log": [],
        "update_action_log": [],
        "insert_events": [],
        "update_events": {},
    }

    dummy_notification_pm = DummyNotificationPM(calls)
    dummy_writer_pm = DummyWriterPM(calls, ws_db, mock_mongo)
    monkeypatch.setattr(bm, "NotificationProcessManager", dummy_notification_pm)
    monkeypatch.setattr(la, "NotificationProcessManager", dummy_notification_pm)
    monkeypatch.setattr(bm, "WriterProcessManager", dummy_writer_pm)
    monkeypatch.setattr(clome, "WriterProcessManager", dummy_writer_pm)
    monkeypatch.setattr(la, "WriterProcessManager", dummy_writer_pm)

    return calls


@pytest.fixture
def patch_common_functions(monkeypatch):
    """共通関数をパッチ"""

    def dummy_addline_msg(msg):
        return msg

    monkeypatch.setattr(bm, "addline_msg", dummy_addline_msg)

    return {
        "addline_msg": dummy_addline_msg,
    }


@pytest.fixture
def patch_action_using_modules(monkeypatch):
    """Actionクラスで使用するモジュールをパッチ"""

    apply = Mock()
    apply.rest_apply_parameter.return_value = "000-00000", {}
    apply.return_value = __import__("common_libs.apply")
    monkeypatch.setattr(la, "ConductorExecuteBkyLibs", DummyConductorExecuteBkyLibs)
    monkeypatch.setattr(la, "apply", apply)

    return {}


@pytest.fixture(autouse=True)
def patch_manage_events_using_modules(monkeypatch):
    """manage_eventsモジュールで使用するモジュールをパッチ"""

    requests = Mock()
    requests.Session.request.return_value.status_code = 200
    requests.Session.request.return_value.json.return_value = {"data": []}
    monkeypatch.setattr(clome, "requests", requests)

    return {}
