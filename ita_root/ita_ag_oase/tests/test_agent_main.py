# PYTEST
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
# from unittest import mock

import pytest
from unittest.mock import patch, MagicMock
from agent_main import get_agent_version, agent_main, collection_logic

from flask import g

# get_agent_version用のpytest


def test_get_agent_version_success(tmp_path, monkeypatch):
    """
    get_agent_version：ファイルからバージョン情報を取得するテスト
    末尾に改行があるファイルからバージョン番号「2.7.0」を正しく取得できることを確認
    """
    version_content = "2.7.0\n"
    version_file = tmp_path / "VERSION.txt"
    version_file.write_text(version_content)

    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    version = get_agent_version()
    assert version == "2.7.0"


def test_get_agent_version_no_newline(tmp_path, monkeypatch):
    """
    get_agent_version：改行がないファイルからバージョン情報を取得するテスト
    末尾に改行がない場合でも、バージョン番号「2.7.0」を正しく取得できることを確認
    """
    version_content = "2.7.0"
    version_file = tmp_path / "VERSION.txt"
    version_file.write_text(version_content)

    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    version = get_agent_version()
    assert version == "2.7.0"


def test_get_agent_version_file_not_found(monkeypatch):
    """
    get_agent_version：ファイルが存在しない場合の例外処理をテスト
    指定されたパスにファイルがない場合にFileNotFoundErrorが発生することを確認
    """
    monkeypatch.setenv("PYTHONPATH", "/non_non_file")

    with pytest.raises(FileNotFoundError):
        get_agent_version()


# agent_main用のpytest


def test_agent_main_with_unpw(setup_test_env, app):
    """
    agent_main：正常終了時のメイン処理をテスト
    collection_logicが指定されたループ回数だけ実行され、処理終了時にSQLiteデータベースのクリーンアップが正しく行われることを確認
    """
    org_id, ws_id, _, _ = setup_test_env
    
    # 外部関数のモック
    with patch("agent_main.sqliteConnect") as mock_sqlite_connect, \
         patch("agent_main.set_dir"), \
         patch("agent_main.Exastro_API") as mock_exastro_api, \
         patch("agent_main.remove_file", return_value=True), \
         patch("agent_main.get_agent_version", return_value="2.7.0"), \
         patch("agent_main.collection_logic") as mock_collection_logic, \
         patch("time.sleep"):
        
        # モック化したクラスのインスタンスの振る舞いを設定
        mock_db_instance = MagicMock()
        mock_sqlite_connect.return_value = mock_db_instance
        
        mock_api_instance = MagicMock()
        mock_exastro_api.return_value = mock_api_instance
        
        # テスト実行
        loop_count = 5
        interval = 3
        agent_main(org_id, ws_id, loop_count, interval)
        
        # sqliteConnectが一度呼び出されたか
        mock_sqlite_connect.assert_called_once_with(org_id, ws_id)
        
        # Exastro_APIが正しく初期化されたか
        mock_exastro_api.assert_called_once_with(
            "http://unittest-pf-auth:8000", "unittest_user", "unittest_password", ""
        )
        
        # collection_logicがループ回数分呼び出されたか
        assert mock_collection_logic.call_count == loop_count
        
        # SQLite DBのクリーンアップが呼び出されたか
        mock_db_instance.db_connect.execute.assert_called_once_with("VACUUM")
        mock_db_instance.db_close.assert_called_once()
        
        # g.AGENT_INFOにエージェント情報が入っているか
        assert g.AGENT_INFO == {'name': 'unittest-ita-oase-agent-01', 'version': '2.7.0'}


def test_agent_main_with_refresh_token(setup_test_env, monkeypatch):
    """
    agent_main：リフレッシュトークンを使用するシナリオをテスト
    Exastro_APIがリフレッシュトークンを使って初期化され、get_access_tokenが正しく呼び出されることを確認
    """
    org_id, ws_id, _, _ = setup_test_env
    
    # リフレッシュトークンを設定
    monkeypatch.setenv("EXASTRO_REFRESH_TOKEN", "unittest_refresh_token")
    
    # 外部関数のモック
    with patch("agent_main.sqliteConnect") as mock_sqlite_connect, \
         patch("agent_main.set_dir"), \
         patch("agent_main.Exastro_API") as mock_exastro_api, \
         patch("agent_main.remove_file", return_value=True), \
         patch("agent_main.get_agent_version", return_value="2.7.0"), \
         patch("agent_main.collection_logic") as mock_collection_logic, \
         patch("time.sleep"):
        
        # モック化したクラスのインスタンスの振る舞いを設定
        mock_db_instance = MagicMock()
        mock_sqlite_connect.return_value = mock_db_instance
        
        mock_api_instance = MagicMock()
        mock_exastro_api.return_value = mock_api_instance
        
        # テスト実行
        loop_count = 5
        interval = 3
        agent_main(org_id, ws_id, loop_count, interval)
        
        # Exastro_APIが正しく初期化されたか（リフレッシュトークンが渡されている）
        mock_exastro_api.assert_called_once_with(
            "http://unittest-pf-auth:8000", "unittest_user", "unittest_password", "unittest_refresh_token"
        )
        
        # get_access_tokenが呼び出されたか
        mock_api_instance.get_access_token.assert_called_once_with(org_id, "unittest_refresh_token")
        
        # collection_logicがループ回数分呼び出されたか
        assert mock_collection_logic.call_count == loop_count

        # SQLite DBのクリーンアップが呼び出されたか
        mock_db_instance.db_connect.execute.assert_called_once_with("VACUUM")
        mock_db_instance.db_close.assert_called_once()
        
        # g.AGENT_INFOにエージェント情報が入っているか
        assert g.AGENT_INFO == {'name': 'unittest-ita-oase-agent-01', 'version': '2.7.0'}


def test_agent_main_with_exception_in_loop(setup_test_env, monkeypatch):
    """
    agent_main：ループ内の例外処理をテスト
    collection_logic内で例外が発生した場合でも、ループが継続し、例外ハンドラが呼び出されることを確認
    """
    org_id, ws_id, _, _ = setup_test_env

    # 外部関数のモック
    with patch("agent_main.sqliteConnect") as mock_sqlite_connect, \
         patch("agent_main.set_dir"), \
         patch("agent_main.Exastro_API") as mock_exastro_api, \
         patch("agent_main.remove_file", return_value=True), \
         patch("agent_main.get_agent_version", return_value="2.7.0"), \
         patch("agent_main.collection_logic", side_effect=[Exception("Test Exception"), None, None, None, None]) as mock_collection_logic, \
         patch("agent_main.exception") as mock_exception_handler, \
         patch("time.sleep"):
        
        # モック化したクラスのインスタンスの振る舞いを設定
        mock_db_instance = MagicMock()
        mock_sqlite_connect.return_value = mock_db_instance
        
        mock_api_instance = MagicMock()
        mock_exastro_api.return_value = mock_api_instance
        
        # テスト実行
        loop_count = 5
        interval = 3
        agent_main(org_id, ws_id, loop_count, interval)
        
        # sqliteConnectが一度呼び出されたか
        mock_sqlite_connect.assert_called_once_with(org_id, ws_id)
        
        # Exastro_APIが正しく初期化されたか
        mock_exastro_api.assert_called_once_with(
            "http://unittest-pf-auth:8000", "unittest_user", "unittest_password", ""
        )
        
        # collection_logicがループ回数分呼び出されたか
        assert mock_collection_logic.call_count == loop_count
        
        # exceptionハンドラが1回呼び出されたか
        mock_exception_handler.assert_called_once()

        # SQLite DBのクリーンアップが呼び出されたか
        mock_db_instance.db_connect.execute.assert_called_once_with("VACUUM")
        mock_db_instance.db_close.assert_called_once()


# collection_logic用のpytest


def test_collection_logic_no_settings_and_send_events(setup_test_env, agent_info):
    """
    collection_logic：設定ファイルがない場合のイベント収集をテスト
    ITAのAPIから設定を取得し、イベントを収集して送信する一連の流れが正しく実行されることを確認
    """
    # monkeypatchを使って環境変数を設定
    org_id, ws_id, _, _ = setup_test_env

    # 外部関数のモック
    with patch('agent_main.get_settings') as mock_get_settings, \
         patch('agent_main.create_file') as mock_create_file, \
         patch('agent_main.collect_event', return_value=([], [])) as mock_collect_event:

        # モック化したクラスのインスタンスの振る舞いを設定
        mock_db_instance = MagicMock()

        mock_api_instance = MagicMock()
        
        # SQLiteのfetchallをモック
        # 1.unsent_timestamp setting1
        # 2.unsent_events setting1
        # 3.unsent_timestamp setting2
        # 4.all_records setting1
        # 5.all_records setting2
        mock_db_instance.db_cursor.fetchall.side_effect = [
            [(1, "setting1", 1577804400)],  # setting1 sent_timestamp
            [(101, "setting1", '{"event": "testdataA"}', 1577804400)],  # setting1  events
            [],  # setting2 sent_timestamp -> PASS: setting2 events
            [(101, "setting1", 1577804400), (100, "setting1", 1577804399)],  # setting1 sent_timestamp
            []   # setting2 sent_timestamp -> PASS: setting2 events
        ]
        mock_api_instance.api_request.side_effect = [
            [200, {"data": [{"ACCESS_KEY_ID": None, "AUTH_TOKEN": "", "CONNECTION_METHOD_ID": "2", "DISUSE_FLAG": "0", "EVENT_COLLECTION_SETTINGS_ID": "2b2ee7dc-7499-4ed9-89c0-0adaaf47413c", "EVENT_COLLECTION_SETTINGS_NAME": "setting1", "EVENT_ID_KEY": None, "LAST_UPDATE_TIMESTAMP": "2025-08-18T10:51:07.066703Z", "LAST_UPDATE_USER": "010aaf2c-000e-4abd-b51b-93289454999d", "MAILBOXNAME": None, "NOTE": None, "PARAMETER": None, "PASSWORD": "", "PORT": None, "PROXY": None, "REQUEST_HEADER": None, "REQUEST_METHOD_ID": "1", "RESPONSE_KEY": "data", "RESPONSE_LIST_FLAG": "1", "SECRET_ACCESS_KEY": "", "TTL": 60, "URL": "http://platform-auth:8000/api/unittest_org/workspaces/unittest_ws/ita/menu/operation_list/filter/?file=no", "USERNAME": "unittest_user"}, {"ACCESS_KEY_ID": None, "AUTH_TOKEN": "", "CONNECTION_METHOD_ID": "99", "DISUSE_FLAG": "0", "EVENT_COLLECTION_SETTINGS_ID": "a78373ea-dc66-439a-8fd8-6fe6c57a29be", "EVENT_COLLECTION_SETTINGS_NAME": "setting2", "EVENT_ID_KEY": None, "LAST_UPDATE_TIMESTAMP": "2020-01-01T00:00:00.000000Z", "LAST_UPDATE_USER": "010aaf2c-000e-4abd-b51b-93289454999d", "MAILBOXNAME": None, "NOTE": None, "PARAMETER": None, "PASSWORD": "", "PORT": None, "PROXY": None, "REQUEST_HEADER": None, "REQUEST_METHOD_ID": None, "RESPONSE_KEY": None, "RESPONSE_LIST_FLAG": None, "SECRET_ACCESS_KEY": "", "TTL": 60, "URL": None, "USERNAME": None}], "message": "SUCCESS", "result": "000-00000", "ts": "2020-01-01T00:00:00.000Z"}],
            [200, {"data": [], "message": "SUCCESS", "result": "000-00000", "ts": "2020-01-01T00:00:00.000Z"}]
        ]
        # get_settingsをモック
        mock_get_settings.side_effect = [
            False,
            [{'ACCESS_KEY_ID': None, 'AUTH_TOKEN': '', 'CONNECTION_METHOD_ID': '2', 'DISUSE_FLAG': '0', 'EVENT_COLLECTION_SETTINGS_ID': '2b2ee7dc-7499-4ed9-89c0-0adaaf47413c', 'EVENT_COLLECTION_SETTINGS_NAME': 'setting1', 'EVENT_ID_KEY': None, 'LAST_UPDATE_TIMESTAMP': '2025-08-18T10:51:07.066703Z', 'LAST_UPDATE_USER': '010aaf2c-000e-4abd-b51b-93289454999d', 'MAILBOXNAME': None, 'NOTE': None, 'PARAMETER': None, 'PASSWORD': '', 'PORT': None, 'PROXY': None, 'REQUEST_HEADER': None, 'REQUEST_METHOD_ID': '1', 'RESPONSE_KEY': 'data', 'RESPONSE_LIST_FLAG': '1', 'SECRET_ACCESS_KEY': '', 'TTL': 60, 'URL': 'http://platform-auth:8000/api/unittest_org/workspaces/unittest_ws/ita/menu/operation_list/filter/?file=no', 'USERNAME': 'unittest_user'}]
        ]
        # create_fileをモック
        mock_create_file.return_value = None
        
        collection_logic(
            sqliteDB=mock_db_instance,
            organization_id=org_id,
            workspace_id=ws_id,
            exastro_api=mock_api_instance
        )

    assert mock_get_settings.call_count == 2
    mock_create_file.assert_called_with([{'ACCESS_KEY_ID': None, 'AUTH_TOKEN': '', 'CONNECTION_METHOD_ID': '2', 'DISUSE_FLAG': '0', 'EVENT_COLLECTION_SETTINGS_ID': '2b2ee7dc-7499-4ed9-89c0-0adaaf47413c', 'EVENT_COLLECTION_SETTINGS_NAME': 'setting1', 'EVENT_ID_KEY': None, 'LAST_UPDATE_TIMESTAMP': '2025-08-18T10:51:07.066703Z', 'LAST_UPDATE_USER': '010aaf2c-000e-4abd-b51b-93289454999d', 'MAILBOXNAME': None, 'NOTE': None, 'PARAMETER': None, 'PASSWORD': '', 'PORT': None, 'PROXY': None, 'REQUEST_HEADER': None, 'REQUEST_METHOD_ID': '1', 'RESPONSE_KEY': 'data', 'RESPONSE_LIST_FLAG': '1', 'SECRET_ACCESS_KEY': '', 'TTL': 60, 'URL': 'http://platform-auth:8000/api/unittest_org/workspaces/unittest_ws/ita/menu/operation_list/filter/?file=no', 'USERNAME': 'unittest_user'}])
    mock_collect_event.assert_called_once()
    assert mock_api_instance.api_request.call_count == 2
    assert mock_db_instance.db_cursor.fetchall.call_count == 5
    # SQLiteの削除が呼び出されないことを確認
    mock_db_instance.delete_unnecessary_records.assert_not_called()
    
    # ITAへのイベント送信APIリクエストが正しく呼び出されることを確認
    post_body = {
        "events": [
            {
                "fetched_time": 1577804400,
                "event_collection_settings_name": "setting1",
                "agent": {"name": "unittest-ita-oase-agent-01", "version": "2.7.0"},
                "event": [{"event": "testdataA"}]
            }
        ]
    }
    mock_api_instance.api_request.assert_called_with(
        "POST",
        "/api/unittest_org/workspaces/unittest_ws/oase_agent/events",
        post_body
    )


def test_collection_logic_no_settings_and_send_events_and_delete_events(setup_test_env, agent_info):
    """
    collection_logic：設定ファイルがない場合のイベント収集をテスト
    ITAのAPIから設定を取得し、イベントを収集して送信した後、SQLiteのイベントを削除
    """
    # monkeypatchを使って環境変数を設定
    org_id, ws_id, _, _ = setup_test_env

    # 外部関数のモック
    with patch('agent_main.get_settings') as mock_get_settings, \
         patch('agent_main.create_file') as mock_create_file, \
         patch('agent_main.collect_event', return_value=([], [])) as mock_collect_event:

        # モック化したクラスのインスタンスの振る舞いを設定
        mock_db_instance = MagicMock()

        mock_api_instance = MagicMock()
        
        # SQLiteのfetchallをモック
        # 1.unsent_timestamp setting1
        # 2.unsent_events setting1
        # 3.unsent_timestamp setting2
        # 4.all_records setting1
        # 5.all_records setting2
        # 6.rowids setting1
        mock_db_instance.db_cursor.fetchall.side_effect = [
            [(1, "setting1", 1577804400)],  # setting1 sent_timestamp
            [(101, "setting1", '{"event": "testdataA"}', 1577804400)],  # setting1  events
            [],  # setting2 sent_timestamp -> PASS: setting2 events
            [(101, "setting1", 1577804400), (100, "setting1", 1577804399), (99, "setting1", 1577804398), (98, "setting1", 1577804397)],  # setting1 sent_timestamp
            [],  # setting2 sent_timestamp
            [(99, ), (98, )]  # setting1 events
        ]
        mock_api_instance.api_request.side_effect = [
            [200, {"data": [{"ACCESS_KEY_ID": None, "AUTH_TOKEN": "", "CONNECTION_METHOD_ID": "2", "DISUSE_FLAG": "0", "EVENT_COLLECTION_SETTINGS_ID": "2b2ee7dc-7499-4ed9-89c0-0adaaf47413c", "EVENT_COLLECTION_SETTINGS_NAME": "setting1", "EVENT_ID_KEY": None, "LAST_UPDATE_TIMESTAMP": "2025-08-18T10:51:07.066703Z", "LAST_UPDATE_USER": "010aaf2c-000e-4abd-b51b-93289454999d", "MAILBOXNAME": None, "NOTE": None, "PARAMETER": None, "PASSWORD": "", "PORT": None, "PROXY": None, "REQUEST_HEADER": None, "REQUEST_METHOD_ID": "1", "RESPONSE_KEY": "data", "RESPONSE_LIST_FLAG": "1", "SECRET_ACCESS_KEY": "", "TTL": 60, "URL": "http://platform-auth:8000/api/unittest_org/workspaces/unittest_ws/ita/menu/operation_list/filter/?file=no", "USERNAME": "unittest_user"}, {"ACCESS_KEY_ID": None, "AUTH_TOKEN": "", "CONNECTION_METHOD_ID": "99", "DISUSE_FLAG": "0", "EVENT_COLLECTION_SETTINGS_ID": "a78373ea-dc66-439a-8fd8-6fe6c57a29be", "EVENT_COLLECTION_SETTINGS_NAME": "setting2", "EVENT_ID_KEY": None, "LAST_UPDATE_TIMESTAMP": "2020-01-01T00:00:00.000000Z", "LAST_UPDATE_USER": "010aaf2c-000e-4abd-b51b-93289454999d", "MAILBOXNAME": None, "NOTE": None, "PARAMETER": None, "PASSWORD": "", "PORT": None, "PROXY": None, "REQUEST_HEADER": None, "REQUEST_METHOD_ID": None, "RESPONSE_KEY": None, "RESPONSE_LIST_FLAG": None, "SECRET_ACCESS_KEY": "", "TTL": 60, "URL": None, "USERNAME": None}], "message": "SUCCESS", "result": "000-00000", "ts": "2020-01-01T00:00:00.000Z"}],
            [200, {"data": [], "message": "SUCCESS", "result": "000-00000", "ts": "2020-01-01T00:00:00.000Z"}]
        ]
        # get_settingsをモック
        mock_get_settings.side_effect = [
            False,
            [{'ACCESS_KEY_ID': None, 'AUTH_TOKEN': '', 'CONNECTION_METHOD_ID': '2', 'DISUSE_FLAG': '0', 'EVENT_COLLECTION_SETTINGS_ID': '2b2ee7dc-7499-4ed9-89c0-0adaaf47413c', 'EVENT_COLLECTION_SETTINGS_NAME': 'setting1', 'EVENT_ID_KEY': None, 'LAST_UPDATE_TIMESTAMP': '2025-08-18T10:51:07.066703Z', 'LAST_UPDATE_USER': '010aaf2c-000e-4abd-b51b-93289454999d', 'MAILBOXNAME': None, 'NOTE': None, 'PARAMETER': None, 'PASSWORD': '', 'PORT': None, 'PROXY': None, 'REQUEST_HEADER': None, 'REQUEST_METHOD_ID': '1', 'RESPONSE_KEY': 'data', 'RESPONSE_LIST_FLAG': '1', 'SECRET_ACCESS_KEY': '', 'TTL': 60, 'URL': 'http://platform-auth:8000/api/unittest_org/workspaces/unittest_ws/ita/menu/operation_list/filter/?file=no', 'USERNAME': 'unittest_user'}]
        ]
        # create_fileをモック
        mock_create_file.return_value = None
        
        collection_logic(
            sqliteDB=mock_db_instance,
            organization_id=org_id,
            workspace_id=ws_id,
            exastro_api=mock_api_instance
        )

    assert mock_get_settings.call_count == 2
    mock_create_file.assert_called_with([{'ACCESS_KEY_ID': None, 'AUTH_TOKEN': '', 'CONNECTION_METHOD_ID': '2', 'DISUSE_FLAG': '0', 'EVENT_COLLECTION_SETTINGS_ID': '2b2ee7dc-7499-4ed9-89c0-0adaaf47413c', 'EVENT_COLLECTION_SETTINGS_NAME': 'setting1', 'EVENT_ID_KEY': None, 'LAST_UPDATE_TIMESTAMP': '2025-08-18T10:51:07.066703Z', 'LAST_UPDATE_USER': '010aaf2c-000e-4abd-b51b-93289454999d', 'MAILBOXNAME': None, 'NOTE': None, 'PARAMETER': None, 'PASSWORD': '', 'PORT': None, 'PROXY': None, 'REQUEST_HEADER': None, 'REQUEST_METHOD_ID': '1', 'RESPONSE_KEY': 'data', 'RESPONSE_LIST_FLAG': '1', 'SECRET_ACCESS_KEY': '', 'TTL': 60, 'URL': 'http://platform-auth:8000/api/unittest_org/workspaces/unittest_ws/ita/menu/operation_list/filter/?file=no', 'USERNAME': 'unittest_user'}])
    mock_collect_event.assert_called_once()
    assert mock_api_instance.api_request.call_count == 2
    assert mock_db_instance.db_cursor.fetchall.call_count == 6
    # SQLiteの削除が正しく呼び出されることを確認
    mock_db_instance.delete_unnecessary_records.assert_called_once()
    mock_db_instance.delete_unnecessary_records.assert_called_with({'events': [99, 98], 'sent_timestamp': [99, 98]})
    
    # ITAへのイベント送信APIリクエストが正しく呼び出されることを確認
    post_body = {
        "events": [
            {
                "fetched_time": 1577804400,
                "event_collection_settings_name": "setting1",
                "agent": {"name": "unittest-ita-oase-agent-01", "version": "2.7.0"},
                "event": [{"event": "testdataA"}]
            }
        ]
    }
    mock_api_instance.api_request.assert_called_with(
        "POST",
        "/api/unittest_org/workspaces/unittest_ws/oase_agent/events",
        post_body
    )


def test_collection_logic_no_settings_and_ita_noresponse(setup_test_env, agent_info):
    """
    collection_logic：設定ファイルがない場合のイベント収集をテスト
    ITAのAPIから設定を取得し、空だった場合イベントの保存や送信が行われないことを確認
    """
    # monkeypatchを使って環境変数を設定
    org_id, ws_id, _, _ = setup_test_env

    # 外部関数のモック
    with patch('agent_main.get_settings', return_value=False) as mock_get_settings, \
         patch('agent_main.create_file', return_value=None) as mock_create_file, \
         patch('agent_main.collect_event') as mock_collect_event:

        # モック化したクラスのインスタンスの振る舞いを設定
        mock_db_instance = MagicMock()

        mock_api_instance = MagicMock()
        
        # SQLiteのfetchallをモック
        # 1.unsent_timestamp setting1
        # 2.unsent_timestamp setting2
        # 3.all_records setting1
        # 4.all_records setting2
        # 5.rowids setting1
        mock_db_instance.db_cursor.fetchall.side_effect = [
            [],  # setting1 sent_timestamp -> PASS: setting1 events
            [],  # setting2 sent_timestamp -> PASS: setting2 events
            [(101, "setting1", 1577804400), (100, "setting1", 1577804399), (99, "setting1", 1577804398), (98, "setting1", 1577804397)],  # setting1 sent_timestamp
            [],  # setting2 sent_timestamp
            [(99, ), (98, )]  # setting1 events
        ]
        
        mock_api_instance.api_request.side_effect = [
            [200, {"data": [], "message": "SUCCESS", "result": "000-00000", "ts": "2020-01-01T00:00:00.000Z"}]
        ]
        
        collection_logic(
            sqliteDB=mock_db_instance,
            organization_id=org_id,
            workspace_id=ws_id,
            exastro_api=mock_api_instance
        )

    assert mock_get_settings.call_count == 2
    mock_create_file.assert_called_once()
    mock_collect_event.assert_not_called()
    mock_api_instance.api_request.assert_called_once()
    mock_db_instance.insert_events.assert_not_called()
    assert mock_db_instance.db_cursor.fetchall.call_count == 5
    # SQLiteの削除が正しく呼び出されることを確認
    mock_db_instance.delete_unnecessary_records.assert_called_once()
    mock_db_instance.delete_unnecessary_records.assert_called_with({'events': [99, 98], 'sent_timestamp': [99, 98]})


def test_collection_logic_has_settings_and_send_events(setup_test_env, agent_info):
    """
    collection_logic：設定ファイルが存在する場合のイベント送信をテスト
    ローカルの設定ファイルからイベントを収集し、ITAのAPIにイベントを送信する処理が正しく行われることを確認
    """
    
    # monkeypatchを使って環境変数を設定
    org_id, ws_id, _, _ = setup_test_env

    # 外部関数のモック
    with patch('agent_main.get_settings') as mock_get_settings, \
         patch('agent_main.collect_event') as mock_collect_event:

        # モック化したクラスのインスタンスの振る舞いを設定
        mock_db_instance = MagicMock()

        mock_api_instance = MagicMock()
        
        # SQLiteのfetchallをモック
        # 1.unsent_timestamp setting1
        # 2.unsent_events setting1
        # 3.unsent_timestamp setting2
        # 4.all_records setting1
        # 5.all_records setting2
        mock_db_instance.db_cursor.fetchall.side_effect = [
            [(1, "setting1", 1577804400)],  # setting1 sent_timestamp
            [(101, "setting1", '{"event": "testdataA"}', 1577804400)],  # setting1  events
            [],  # setting2 sent_timestamp -> PASS: setting2 events
            [(101, "setting1", 1577804400), (100, "setting1", 1577804399)],  # setting1 sent_timestamp
            []   # setting2 sent_timestamp -> PASS: setting2 events
        ]
        mock_api_instance.api_request.side_effect = [
            (200, {"data": [], "message": "SUCCESS", "result": "000-00000", "ts": "2020-01-01T00:00:00.000Z"})
        ]
        # get_settingsをモック
        mock_get_settings.side_effect = [
            [{'ACCESS_KEY_ID': None, 'AUTH_TOKEN': '', 'CONNECTION_METHOD_ID': '2', 'DISUSE_FLAG': '0', 'EVENT_COLLECTION_SETTINGS_ID': '2b2ee7dc-7499-4ed9-89c0-0adaaf47413c', 'EVENT_COLLECTION_SETTINGS_NAME': 'setting1', 'EVENT_ID_KEY': None, 'LAST_UPDATE_TIMESTAMP': '2025-08-18T10:51:07.066703Z', 'LAST_UPDATE_USER': '010aaf2c-000e-4abd-b51b-93289454999d', 'MAILBOXNAME': None, 'NOTE': None, 'PARAMETER': None, 'PASSWORD': '', 'PORT': None, 'PROXY': None, 'REQUEST_HEADER': None, 'REQUEST_METHOD_ID': '1', 'RESPONSE_KEY': 'data', 'RESPONSE_LIST_FLAG': '1', 'SECRET_ACCESS_KEY': '', 'TTL': 60, 'URL': 'http://platform-auth:8000/api/unittest_org/workspaces/unittest_ws/ita/menu/operation_list/filter/?file=no', 'USERNAME': 'unittest_user'}]
        ]
        # collect_eventをモック
        mock_collect_event.return_value = [
            [{"event": "testdataA"}],
            [{"name": "setting1", "fetched_time": 1577804400}]
        ]
        
        collection_logic(
            sqliteDB=mock_db_instance,
            organization_id=org_id,
            workspace_id=ws_id,
            exastro_api=mock_api_instance
        )

    mock_get_settings.assert_called_once()
    mock_collect_event.assert_called_once()
    mock_api_instance.api_request.assert_called_once()
    assert mock_db_instance.db_cursor.fetchall.call_count == 5
    # SQLiteの削除が呼び出されないことを確認
    mock_db_instance.delete_unnecessary_records.assert_not_called()
    
    # ITAへのイベント送信APIリクエストが正しく呼び出されることを確認
    post_body = {
        "events": [
            {
                "fetched_time": 1577804400,
                "event_collection_settings_name": "setting1",
                "agent": {"name": "unittest-ita-oase-agent-01", "version": "2.7.0"},
                "event": [{"event": "testdataA"}]
            }
        ]
    }
    mock_api_instance.api_request.assert_called_with(
        "POST",
        "/api/unittest_org/workspaces/unittest_ws/oase_agent/events",
        post_body
    )


def test_collection_logic_has_settings_and_send_events_and_delete_events(setup_test_env, agent_info):
    """
    collection_logic：イベント送信後の削除処理をテスト
    イベントをITAに送信した後、古いイベントデータがSQLiteデータベースから正しく削除されることを確認
    """
    
    # monkeypatchを使って環境変数を設定
    org_id, ws_id, _, _ = setup_test_env

    # 外部関数のモック
    with patch('agent_main.get_settings') as mock_get_settings, \
         patch('agent_main.collect_event') as mock_collect_event:

        # モック化したクラスのインスタンスの振る舞いを設定
        mock_db_instance = MagicMock()

        mock_api_instance = MagicMock()
        
        # SQLiteのfetchallをモック
        # 1.unsent_timestamp setting1
        # 2.unsent_events setting1
        # 3.unsent_timestamp setting2
        # 4.all_records setting1
        # 5.all_records setting2
        # 6.rowids setting1
        mock_db_instance.db_cursor.fetchall.side_effect = [
            [(1, "setting1", 1577804400)],  # setting1 sent_timestamp
            [(101, "setting1", '{"event": "testdataA"}', 1577804400)],  # setting1  events
            [],  # setting2 sent_timestamp -> PASS: setting2 events
            [(101, "setting1", 1577804400), (100, "setting1", 1577804399), (99, "setting1", 1577804398), (98, "setting1", 1577804397)],  # setting1 sent_timestamp
            [],  # setting2 sent_timestamp
            [(99, ), (98, )]  # setting1 events
        ]
        mock_api_instance.api_request.side_effect = [
            (200, {"data": [], "message": "SUCCESS", "result": "000-00000", "ts": "2020-01-01T00:00:00.000Z"})
        ]
        # get_settingsをモック
        mock_get_settings.side_effect = [
            [{'ACCESS_KEY_ID': None, 'AUTH_TOKEN': '', 'CONNECTION_METHOD_ID': '2', 'DISUSE_FLAG': '0', 'EVENT_COLLECTION_SETTINGS_ID': '2b2ee7dc-7499-4ed9-89c0-0adaaf47413c', 'EVENT_COLLECTION_SETTINGS_NAME': 'setting1', 'EVENT_ID_KEY': None, 'LAST_UPDATE_TIMESTAMP': '2025-08-18T10:51:07.066703Z', 'LAST_UPDATE_USER': '010aaf2c-000e-4abd-b51b-93289454999d', 'MAILBOXNAME': None, 'NOTE': None, 'PARAMETER': None, 'PASSWORD': '', 'PORT': None, 'PROXY': None, 'REQUEST_HEADER': None, 'REQUEST_METHOD_ID': '1', 'RESPONSE_KEY': 'data', 'RESPONSE_LIST_FLAG': '1', 'SECRET_ACCESS_KEY': '', 'TTL': 60, 'URL': 'http://platform-auth:8000/api/unittest_org/workspaces/unittest_ws/ita/menu/operation_list/filter/?file=no', 'USERNAME': 'unittest_user'}]
        ]
        # collect_eventをモック
        mock_collect_event.return_value = [
            [{"event": "testdataA"}],
            [{"name": "setting1", "fetched_time": 1577804400}]
        ]
        
        collection_logic(
            sqliteDB=mock_db_instance,
            organization_id=org_id,
            workspace_id=ws_id,
            exastro_api=mock_api_instance
        )

    mock_get_settings.assert_called_once()
    mock_collect_event.assert_called_once()
    mock_api_instance.api_request.assert_called_once()
    assert mock_db_instance.db_cursor.fetchall.call_count == 6
    # SQLiteの削除が正しく呼び出されることを確認
    mock_db_instance.delete_unnecessary_records.assert_called_once()
    mock_db_instance.delete_unnecessary_records.assert_called_with({'events': [99, 98], 'sent_timestamp': [99, 98]})


def test_collection_logic_has_settings_empty_and_delete_events(setup_test_env, agent_info):
    """
    collection_logic：イベント送信後の削除処理をテスト
    収集設定が存在せずITAには送信しない、古いイベントデータがSQLiteデータベースから正しく削除されることを確認
    """
    
    # monkeypatchを使って環境変数を設定
    org_id, ws_id, _, _ = setup_test_env

    # 外部関数のモック
    with patch('agent_main.get_settings') as mock_get_settings, \
         patch('agent_main.collect_event') as mock_collect_event:

        # モック化したクラスのインスタンスの振る舞いを設定
        mock_db_instance = MagicMock()

        mock_api_instance = MagicMock()
        
        # SQLiteのfetchallをモック
        # 1.unsent_timestamp setting1
        # 2.unsent_timestamp setting2
        # 3.all_records setting1
        # 4.all_records setting2
        # 5.rowids setting1
        mock_db_instance.db_cursor.fetchall.side_effect = [
            [],  # setting1 sent_timestamp -> PASS: setting1 events
            [],  # setting2 sent_timestamp -> PASS: setting2 events
            [(101, "setting1", 1577804400), (100, "setting1", 1577804399), (99, "setting1", 1577804398), (98, "setting1", 1577804397)],  # setting1 sent_timestamp
            [],  # setting2 sent_timestamp
            [(99, ), (98, )]  # setting1 events
        ]
        # get_settingsをモック
        mock_get_settings.return_value = []
        # collect_eventをモック
        mock_collect_event.return_value = [
            [],
            []
        ]
        
        collection_logic(
            sqliteDB=mock_db_instance,
            organization_id=org_id,
            workspace_id=ws_id,
            exastro_api=mock_api_instance
        )

    mock_get_settings.assert_called_once()
    mock_collect_event.assert_called_once()
    mock_api_instance.api_request.assert_not_called()
    assert mock_db_instance.db_cursor.fetchall.call_count == 5
    # SQLiteの削除が正しく呼び出されることを確認
    mock_db_instance.delete_unnecessary_records.assert_called_once()
    mock_db_instance.delete_unnecessary_records.assert_called_with({'events': [99, 98], 'sent_timestamp': [99, 98]})
