#   Copyright 2025 NEC Corporation
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
from unittest.mock import MagicMock
import copy
import json
import os
import requests
from jinja2 import Template, UndefinedError
from common_libs.notification.notification_base import Notification
from common_libs.common.exception import AppException
import urllib3
from unittest.mock import MagicMock, call
from requests.exceptions import ConnectionError
from common_libs.notification.sub_classes.oase import OASENotificationType


# Notificationクラスの抽象メソッドを実装するモッククラス
class MockNotification(Notification):
    @classmethod
    def _fetch_table(cls, objdbca, decision_information):
        # 新しい想定の戻り値
        return {"NOTIFICATION_DESTINATION": [
            {"id": None, "UUID": 1, "TEMPLATE_FILE": "New00.j2", "IS_DEFAULT": "●"},
            {"id": ["aa"], "UUID": 2, "TEMPLATE_FILE": "New01.j2", "IS_DEFAULT": None},
            {"id": ["bb", "cc"], "UUID": 3, "TEMPLATE_FILE": "New02.j2", "IS_DEFAULT": None}
        ]}

    @classmethod
    def _get_template(cls, fetch_data, decision_information):
        # fetch_dataからテンプレート情報を抽出
        templates = []
        for item in fetch_data.get("NOTIFICATION_DESTINATION", []):
            templates.append({
                "id": item.get("id"),
                "template": f"[TITLE]\n{item.get('TEMPLATE_FILE')} Title\n[BODY]\nThis is the message body for {{ message }}.",
                "IS_DEFAULT": item.get("IS_DEFAULT")
            })
        return templates

    @classmethod
    def _fetch_notification_destination(cls, fetch_data, decision_information):
        # fetch_dataから通知先IDを抽出
        destinations = []
        for item in fetch_data.get("NOTIFICATION_DESTINATION", []):
            if item.get("id"):
                destinations.extend(item.get("id"))
        return destinations

    @staticmethod
    def _convert_message(item):
        return item

    @staticmethod
    def _get_data():
        return {"func_id": "mock_func_id"}


def test_send_success(app_context_with_mock_g, mocker):
    """
    sendメソッドが正常終了し、通知APIが正しくコールされることを確認
    """
    mock_dbca = MagicMock()
    event_list = [{"message": "event1"}, {"message": "event2"}]
    decision_information = {"key": "value"}

    # _fetch_tableのモック化
    mocker.patch.object(MockNotification, '_fetch_table', return_value=MockNotification._fetch_table(None, None))

    # __call_notification_apiメソッドをモック
    mock_call_api = mocker.patch.object(MockNotification, '_Notification__call_notification_api', return_value={
        "success": 1,
        "failure": 0,
        "failure_info": [],
        "success_notification_count": 3,
        "failure_notification_count": 0
    })

    # _create_notise_messageをモック
    mocker.patch.object(MockNotification, '_create_notise_message', return_value={"title": "test", "message": "test"})

    result = MockNotification.send(mock_dbca, event_list, decision_information)

    # 期待されるメソッドが呼び出されたことを確認
    MockNotification._fetch_table.assert_called_once_with(mock_dbca, decision_information)

    # イベントリストの件数分APIが呼ばれたことを確認
    assert mock_call_api.call_count == len(event_list)

    # 戻り値の確認
    expected_result = {
        "success": 2,
        "failure": 0,
        "failure_info": [],
        "success_notification_count": 6,
        "failure_notification_count": 0
    }
    assert result == expected_result


def test_send_fetch_table_none(app_context_with_mock_g, mocker):
    """
    _fetch_tableがNoneを返した場合にsendメソッドが適切に終了することを確認
    """
    mock_dbca = MagicMock()
    mocker.patch.object(MockNotification, '_fetch_table', return_value=None)
    event_list = [{"message": "event1"}]
    decision_information = {"key": "value"}

    result = MockNotification.send(mock_dbca, event_list, decision_information)

    assert result == {}
    app_context_with_mock_g.applogger.info.assert_called()


def test_send_get_template_none(app_context_with_mock_g, mocker):
    """
    _get_templateがNoneを含むリストを返した場合にsendメソッドが適切に終了することを確認
    """
    mock_dbca = MagicMock()
    mocker.patch.object(MockNotification, '_get_template', return_value=[{"id": ["dest1"], "template": None}])
    event_list = [{"message": "event1"}]
    decision_information = {"key": "value"}
    mocker.patch.object(MockNotification, '_fetch_table', return_value={"data": "mock_data"})

    result = MockNotification.send(mock_dbca, event_list, decision_information)

    assert result == {}
    app_context_with_mock_g.applogger.info.assert_called()


def test_send_fetch_notification_destination_empty(app_context_with_mock_g, mocker):
    """
    _fetch_notification_destinationが空リストを返した場合にsendメソッドが適切に終了することを確認
    """
    mock_dbca = MagicMock()
    mocker.patch.object(MockNotification, '_fetch_notification_destination', return_value=[])
    event_list = [{"message": "event1"}]
    decision_information = {"key": "value"}
    mocker.patch.object(MockNotification, '_fetch_table', return_value=MockNotification._fetch_table(None, None))
    # _get_templateに正しい引数を渡すように修正
    mocker.patch.object(MockNotification, '_get_template', return_value=MockNotification._get_template(MockNotification._fetch_table(None, None), None))

    result = MockNotification.send(mock_dbca, event_list, decision_information)

    assert result == {}
    app_context_with_mock_g.applogger.info.assert_called()


def test_create_notise_message_success(app_context_with_mock_g):
    """
    _create_notise_messageが正しくメッセージを作成することを確認
    """
    item = {"message": "Hello, world!"}
    template = "[TITLE]\nNotification Title\n[BODY]\nThis is the message body for {{ message }}."

    result = MockNotification._create_notise_message(item, template)

    assert "title" in result
    assert "message" in result
    assert result["title"] == "Notification Title"
    assert result["message"] == "This is the message body for Hello, world!."


def test_create_notise_message_template_render_error(app_context_with_mock_g, mocker):
    """
    _create_notise_messageがテンプレートレンダリングエラー時にNoneを返すことを確認
    """
    # UndefinedErrorをモック
    mocker.patch('jinja2.Template.render', side_effect=UndefinedError('test error'))

    item = {"_id": "item1", "message": "Hello"}
    template = "This is a invalid template with a missing tag. {{ undefined_variable }}"

    result = MockNotification._create_notise_message(item, template)

    assert result is None


def test_call_notification_api_success(app_context_with_mock_g, mocker):
    """
    __call_notification_apiが成功ステータスで正常に動作することを確認
    """
    mocker.patch.dict(os.environ, {'PLATFORM_API_HOST': 'localhost', 'PLATFORM_API_PORT': '8080'})
    app_context_with_mock_g.get.side_effect = ["org1", "ws1", "user1", "ja"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mocker.patch('requests.Session.request', return_value=mock_response)

    # _get_dataをモック
    mocker.patch.object(MockNotification, '_get_data', return_value={"func_id": "mock_func_id", "func_informations": {}})

    # 新しいロジックを考慮したメッセージリストと通知先
    message_list = [
        {"id": ["aa"], "message": {"title": "aa_title", "message": "aa_body"}, "IS_DEFAULT": None},
        {"id": ["bb", "cc"], "message": {"title": "bb_cc_title", "message": "bb_cc_body"}, "IS_DEFAULT": None},
        {"id": None, "message": {"title": "default_title", "message": "default_body"}, "IS_DEFAULT": "●"},
    ]
    notification_destination = ["aa", "bb", "dd"]

    result = MockNotification._Notification__call_notification_api(message_list, notification_destination)

    # requests.Session.requestが正しい引数で呼ばれていることを確認
    expected_data = json.dumps([
        {"func_id": "mock_func_id", "func_informations": {}, "destination_id": "aa", "message": {"title": "aa_title", "message": "aa_body"}},
        {"func_id": "mock_func_id", "func_informations": {}, "destination_id": "bb", "message": {"title": "bb_cc_title", "message": "bb_cc_body"}},
        {"func_id": "mock_func_id", "func_informations": {}, "destination_id": "dd", "message": {"title": "default_title", "message": "default_body"}},
    ])

    requests.Session.request.assert_called_once_with(
        method='POST',
        url=mocker.ANY,
        timeout=2,
        headers=mocker.ANY,
        data=expected_data
    )

    assert result["success"] == 1
    assert result["failure"] == 0
    assert result["success_notification_count"] == 3
    assert result["failure_notification_count"] == 0
    assert result["failure_info"] == []


def test_call_notification_api_failure(app_context_with_mock_g, mocker):
    """
    __call_notification_apiが失敗ステータスでエラーを記録することを確認
    """
    mocker.patch.dict(os.environ, {'PLATFORM_API_HOST': 'localhost', 'PLATFORM_API_PORT': '8080'})
    app_context_with_mock_g.get.side_effect = ["org1", "ws1", "user1", "ja"]

    mock_response = MagicMock()
    mock_response.status_code = 500
    mocker.patch('requests.Session.request', return_value=mock_response)

    # _get_dataをモック
    mocker.patch.object(MockNotification, '_get_data', return_value={"func_id": "mock_func_id", "func_informations": {}})

    message_list = [{"id": ["dest1"], "message": {"title": "test1", "message": "body1"}},
                    {"id": ["dest2"], "message": {"title": "test2", "message": "body2"}}]
    notification_destination = ["dest1", "dest2"]

    result = MockNotification._Notification__call_notification_api(message_list, notification_destination)

    assert result["success"] == 0
    assert result["failure"] == 1
    assert result["success_notification_count"] == 0
    assert result["failure_notification_count"] == 2
    assert len(result["failure_info"]) == 1


def test_call_setting_notification_api_success(app_context_with_mock_g, mocker):
    """
    _call_setting_notification_apiが成功時に正常に動作することを確認
    """
    mocker.patch.dict(os.environ, {'PLATFORM_API_HOST': 'localhost', 'PLATFORM_API_PORT': '8080'})
    app_context_with_mock_g.get.side_effect = ["org1", "ws1", "user1", "ja"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"id": "id1", "name": "name1"}, {"id": "id2", "name": "name2"}]}
    mocker.patch('requests.Session.request', return_value=mock_response)

    result = MockNotification._call_setting_notification_api(event_type_true=["type1", "type2"])

    expected_url = "http://localhost:8080/internal-api/org1/platform/workspaces/ws1/settings/notifications"
    # requests.Session.requestが正しい引数で呼ばれていることを確認
    requests.Session.request.assert_called_once_with(
        method='GET',
        url=expected_url,
        timeout=2,
        headers={"User-Id": "user1", "Language": "ja"},
        params={"event_type_true": "type1|type2"}
    )
    assert result["data"][0]["id"] == "id1"


def test_call_setting_notification_api_with_event_type_false(app_context_with_mock_g, mocker):
    """
    _call_setting_notification_apiがevent_type_false引数を正しく処理することを確認
    """
    # モックのセットアップ
    mocker.patch.dict(os.environ, {'PLATFORM_API_HOST': 'localhost', 'PLATFORM_API_PORT': '8080'})
    app_context_with_mock_g.get.side_effect = ["org1", "ws1", "user1", "ja"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mocker.patch('requests.Session.request', return_value=mock_response)

    # テスト実行
    event_type_false_list = ["type_a", "type_b"]
    MockNotification._call_setting_notification_api(event_type_false=event_type_false_list)

    # アサーション
    expected_url = "http://localhost:8080/internal-api/org1/platform/workspaces/ws1/settings/notifications"
    expected_params = {"event_type_false": "type_a|type_b"}

    # requests.Session.requestが正しい引数で呼ばれたことを検証
    requests.Session.request.assert_called_once_with(
        method='GET',
        url=expected_url,
        timeout=2,
        headers={"User-Id": "user1", "Language": "ja"},
        params=expected_params
    )


def test_call_setting_notification_api_raises_app_exception(app_context_with_mock_g, mocker):
    """
    _call_setting_notification_apiが500エラーでAppExceptionを発生させることを確認
    """
    mocker.patch.dict(os.environ, {'PLATFORM_API_HOST': 'localhost', 'PLATFORM_API_PORT': '8080'})
    app_context_with_mock_g.get.side_effect = ["org1", "ws1", "user1", "ja"]

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": "Internal Server Error"}
    mocker.patch('requests.Session.request', return_value=mock_response)

    with pytest.raises(AppException):
        MockNotification._call_setting_notification_api()


def test_fetch_notification_destination_dict(app_context_with_mock_g, mocker):
    """
    fetch_notification_destination_dictが正しい辞書を返すことを確認
    """
    mocker.patch.object(
        MockNotification, '_call_setting_notification_api',
        return_value={"data": [{"id": "id1", "name": "name1"}, {"id": "id2", "name": "name2"}]}
    )

    result = MockNotification.fetch_notification_destination_dict()

    expected_dict = {"id1": "name1", "id2": "name2"}
    assert result == expected_dict


# __call_notification_api_threadのテスト
def test_call_notification_api_thread_complex_message_mapping(app_context_with_mock_g, mocker):
    """
    __call_notification_api_threadの正常系で通知テンプレート設定で複数の通知先を指定している場合、単一の通知先を指定している場合、デフォルトメッセージが混在する複雑なケースを確認
    それぞれの通知先に正しいメッセージが送信されることを確認
    """
    # 環境変数のモック
    mocker.patch.dict(os.environ, {'PLATFORM_API_HOST': 'localhost', 'PLATFORM_API_PORT': '8080'})

    # requestsのモック
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_request = mocker.patch('requests.Session.request', return_value=mock_response)

    # _get_dataのモック(モックするまでもなく固定値だけど)
    mocker.patch.object(MockNotification, '_get_data', return_value={"func_id": "1102", "func_informations": {"menu_group_name": "OASE"}})

    # 複雑なテストデータ
    message_list = [
        {"id": ["AA", "BB"], "message": {"title": "Title AA/BB", "message": "Message AA/BB"}, "IS_DEFAULT": None},  # 複数通知先が入っている
        {"id": ["CC"], "message": {"title": "Title CC", "message": "Message CC"}, "IS_DEFAULT": None},  # 単一の通知先が入っている
        {"id": None, "message": {"title": "Default Title", "message": "Default Message"}, "IS_DEFAULT": "●"},  # デフォルトメッセージ
        {"id": "DD", "message": {"title": "Title DD", "message": "Message DD"}, "IS_DEFAULT": None},  # 原則来ないと思うけど一応条件分岐には入るので入れる
    ]
    notification_destination = ["AA", "BB", "CC", "DD", "EE"]  # 通知先EEはデフォルトメッセージを使用されることを期待
    organization_id = "org1"
    workspace_id = "ws1"
    user_id = "user1"
    language = "ja"

    # テスト実行
    result = MockNotification._Notification__call_notification_api_thread(
        message_list, notification_destination, organization_id, workspace_id, user_id, language
    )

    # request.data から JSON データを抽出して検証
    args, kwargs = mock_request.call_args
    request_data = json.loads(kwargs['data'])

    # 検証
    assert result["success"] == 1
    assert result["success_notification_count"] == len(request_data)

    # 通知先ごとのメッセージが正しく設定されていることを確認
    dest_messages = {}
    for item in request_data:
        dest_id = item["destination_id"]
        if dest_id not in dest_messages:
            dest_messages[dest_id] = []
        dest_messages[dest_id].append(item["message"])

    # AA宛てのメッセージは1つ
    assert len(dest_messages.get("AA", [])) == 1
    # AAのメッセージ確認
    assert dest_messages.get("AA")[0]["title"] == "Title AA/BB"
    assert dest_messages.get("AA")[0]["message"] == "Message AA/BB"
    # BB宛てのメッセージは1つ
    assert len(dest_messages.get("BB", [])) == 1
    # BB宛てのメッセージはAA宛てのメッセージと同じ
    assert dest_messages.get("BB")[0]["title"] == dest_messages.get("AA")[0]["title"]
    assert dest_messages.get("BB")[0]["message"] == dest_messages.get("AA")[0]["message"]
    # CC宛てのメッセージは1つ
    assert len(dest_messages.get("CC", [])) == 1
    # CC宛てのメッセージ確認
    assert dest_messages.get("CC")[0]["title"] == "Title CC"
    assert dest_messages.get("CC")[0]["message"] == "Message CC"
    # DD宛てのメッセージは1つ
    assert len(dest_messages.get("DD", [])) == 1
    # DD宛てのメッセージ確認
    assert dest_messages.get("DD")[0]["title"] == "Title DD"
    assert dest_messages.get("DD")[0]["message"] == "Message DD"
    # EE宛てのメッセージは1つ
    assert len(dest_messages.get("EE", [])) == 1
    # EE宛てのメッセージはデフォルトメッセージを使用
    assert dest_messages.get("EE")[0]["title"] == "Default Title"
    assert dest_messages.get("EE")[0]["message"] == "Default Message"


def test_call_notification_api_thread_api_error(mocker):
    """
    __call_notification_api_threadがAPIエラー(非200ステータス)を適切に処理することを確認
    """
    # 環境変数のモック
    mocker.patch.dict(os.environ, {'PLATFORM_API_HOST': 'localhost', 'PLATFORM_API_PORT': '8080'})

    # requestsのモック - 500エラーを返す
    mock_response = MagicMock()
    mock_response.status_code = 500
    mocker.patch('requests.Session.request', return_value=mock_response)

    # _get_dataのモック(モックするまでもなく固定値だけど)
    mocker.patch.object(MockNotification, '_get_data', return_value={"func_id": "1102", "func_informations": {"menu_group_name": "OASE"}})

    # テストデータ
    message_list = [
        {"id": ["CC"], "message": {"title": "Title CC", "message": "Message CC"}, "IS_DEFAULT": None},  # 単一の通知先が入っている
        {"id": None, "message": {"title": "Default Title", "message": "Default Message"}, "IS_DEFAULT": "●"}  # デフォルトメッセージ
    ]
    notification_destination = ["CC"]
    organization_id = "org1"
    workspace_id = "ws1"
    user_id = "user1"
    language = "ja"

    # テスト実行
    result = MockNotification._Notification__call_notification_api_thread(
        message_list, notification_destination, organization_id, workspace_id, user_id, language
    )

    # 検証
    assert result["success"] == 0
    assert result["failure"] == 1
    assert len(result["failure_info"]) == 1
    assert "API Error: 500" in result["failure_info"][0]
    assert result["failure_notification_count"] > 0
    assert result["success_notification_count"] == 0


def test_call_notification_api_thread_exception(mocker):
    """
    __call_notification_api_threadが例外を適切に処理することを確認
    """
    # 環境変数のモック
    mocker.patch.dict(os.environ, {'PLATFORM_API_HOST': 'localhost', 'PLATFORM_API_PORT': '8080'})

    # requestsのモック - 例外を発生させる
    mocker.patch('requests.Session.request', side_effect=ConnectionError("Connection refused"))

    # _get_dataのモック(モックするまでもなく固定値だけど)
    mocker.patch.object(MockNotification, '_get_data', return_value={"func_id": "1102", "func_informations": {"menu_group_name": "OASE"}})

    # テストデータ
    message_list = [
        {"id": ["CC"], "message": {"title": "Title CC", "message": "Message CC"}, "IS_DEFAULT": None},  # 単一の通知先が入っている
        {"id": None, "message": {"title": "Default Title", "message": "Default Message"}, "IS_DEFAULT": "●"}  # デフォルトメッセージ
    ]
    notification_destination = ["CC"]
    organization_id = "org1"
    workspace_id = "ws1"
    user_id = "user1"
    language = "ja"

    # テスト実行
    result = MockNotification._Notification__call_notification_api_thread(
        message_list, notification_destination, organization_id, workspace_id, user_id, language
    )

    # 検証
    assert result["success"] == 0
    assert result["failure"] == 1
    assert len(result["failure_info"]) == 1
    assert "Exception: Connection refused" in result["failure_info"][0]
    assert result["failure_notification_count"] > 0
    assert result["success_notification_count"] == 0


def test_call_notification_api_thread_default_message_only(mocker):
    """
    __call_notification_api_threadがデフォルトメッセージのみで通知先が指定されていない（PFの通知先設定があるが、通知テンプレート設定は初期データ）場合の処理を確認
    """
    # 環境変数のモック
    mocker.patch.dict(os.environ, {'PLATFORM_API_HOST': 'localhost', 'PLATFORM_API_PORT': '8080'})

    # requestsのモック
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_request = mocker.patch('requests.Session.request', return_value=mock_response)

    # _get_dataのモック(モックするまでもなく固定値だけど)
    mocker.patch.object(MockNotification, '_get_data', return_value={"func_id": "1102", "func_informations": {"menu_group_name": "OASE"}})

    # テストデータ - デフォルトメッセージのみ
    message_list = [
        {"id": None, "message": {"title": "Default Title", "message": "Default Message"}, "IS_DEFAULT": "●"}
    ]
    notification_destination = ["CC", "DD"]
    organization_id = "org1"
    workspace_id = "ws1"
    user_id = "user1"
    language = "ja"

    # テスト実行
    result = MockNotification._Notification__call_notification_api_thread(
        message_list, notification_destination, organization_id, workspace_id, user_id, language
    )

    # APIが呼び出され、全ての通知先にデフォルトメッセージが送信されることを確認
    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    request_data = json.loads(kwargs['data'])
    assert len(request_data) == 2

    # 結果の検証
    assert result["success"] == 1
    assert result["failure"] == 0
    assert result["success_notification_count"] == 2

    # 通知先ごとのメッセージが正しく設定されていることを確認
    dest_messages = {}
    for item in request_data:
        dest_id = item["destination_id"]
        if dest_id not in dest_messages:
            dest_messages[dest_id] = []
        dest_messages[dest_id].append(item["message"])

    # CC宛てのメッセージは1つ
    assert len(dest_messages.get("CC", [])) == 1
    # CC宛てのメッセージはデフォルトメッセージを使用
    assert dest_messages.get("CC")[0]["title"] == "Default Title"
    assert dest_messages.get("CC")[0]["message"] == "Default Message"
    # DD宛てのメッセージは1つ
    assert len(dest_messages.get("DD", [])) == 1
    # DD宛てのメッセージはデフォルトメッセージを使用
    assert dest_messages.get("DD")[0]["title"] == "Default Title"
    assert dest_messages.get("DD")[0]["message"] == "Default Message"


# bulksendのテスト
def test_bulksend_success(app_context_with_mock_g, mocker):
    """
    bulksendメソッドが正常終了し、通知APIが正しく呼ばれることを確認
    """
    mock_dbca = MagicMock()
    event_list = [{"_id": "0000", "labels": {"labelA": "01"}, "event": {"EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": "2.7.0"}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}, {"_id": "0001", "labels": {"labelA": "02"}, "event": { "EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": 1}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}]
    decision_information = {"notification_type": OASENotificationType.RECEIVE}

    # Mock environment variables
    mocker.patch.dict(os.environ, {
        'NOTIFICATION_BATCH_SIZE': '100',
        'MAX_WORKER_THREAD_POOL_SIZE': '12',
        'PLATFORM_API_HOST': 'localhost',
        'PLATFORM_API_PORT': '8080'
    })

    # Set up g values
    app_context_with_mock_g.get.side_effect = lambda key: {
        'ORGANIZATION_ID': 'org1',
        'WORKSPACE_ID': 'ws1',
        'USER_ID': 'user1',
        'LANGUAGE': 'ja'
    }.get(key)

    # Mock required methods
    mocker.patch.object(MockNotification, '_fetch_table', return_value={'NOTIFICATION_DESTINATION': [{'id': None, 'UUID': '11', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': '●'}, {'id': ['AA'], 'UUID': '4c9d73d2-4f21-4afe-bb5f-794da5398579', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': None}]})
    mocker.patch.object(MockNotification, '_get_template', return_value=[{'id': None, 'UUID': '11', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': '●', 'template': '[TITLE]\nDefault Title\n[BODY]\nDefault Message'}, {'id': ['AA'], 'UUID': '4c9d73d2-4f21-4afe-bb5f-794da5398579', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': None, 'template': '[TITLE]\nTitle AA\n[BODY]\nMessage AA'}])
    mocker.patch.object(MockNotification, '_fetch_notification_destination', return_value=['AA', 'BB'])
    mocker.patch.object(MockNotification, '_create_notise_message', side_effect=[{"id": None, "message": {"title": "Default Title", "message": "Default Message"}, "IS_DEFAULT": "●"}, {"id": "4c9d73d2-4f21-4afe-bb5f-794da5398579", "message":{"title": "Title AA", "message": "Message AA"}, "IS_DEFAULT": None}, {"id": None, "message":{"title": "Default Title", "message": "Default Message"}, "IS_DEFAULT": "●"}, {"id": "4c9d73d2-4f21-4afe-bb5f-794da5398579", "message":{"title": "Title AA", "message": "Message AA"}, "IS_DEFAULT": None}])

    # Mock the thread execution method
    mock_api_thread = mocker.patch.object(
        MockNotification,
        '_Notification__call_notification_api_thread',
        return_value={
            "success": 1,
            "failure": 0,
            "failure_info": [],
            "success_notification_count": 4,
            "failure_notification_count": 0
        }
    )

    # Execute the method
    result = MockNotification.bulksend(mock_dbca, event_list, decision_information)

    # Verify the method calls
    MockNotification._fetch_table.assert_called_once_with(mock_dbca, decision_information)
    MockNotification._get_template.assert_called_once()
    MockNotification._fetch_notification_destination.assert_called_once()

    assert mock_api_thread.call_count == 1

    # Check the result
    assert result["success"] == 1
    assert result["failure"] == 0
    assert result["success_notification_count"] == 4
    assert result["failure_notification_count"] == 0
    assert result["failure_info"] == []


def test_bulksend_fetch_table_none(app_context_with_mock_g, mocker):
    """
    _fetch_tableがNoneを返した場合にbulksendメソッドが適切に終了することを確認
    """
    mock_dbca = MagicMock()
    mocker.patch.object(MockNotification, '_fetch_table', return_value=None)
    event_list = [{"_id": "0000", "labels": {"labelA": "01"}, "event": {"EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": "2.7.0"}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}, {"_id": "0001", "labels": {"labelA": "02"}, "event": { "EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": 1}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}]
    decision_information = {"notification_type": OASENotificationType.RECEIVE}
    g = app_context_with_mock_g

    result = MockNotification.bulksend(mock_dbca, event_list, decision_information)

    assert result == {}
    app_context_with_mock_g.applogger.info.assert_any_call(g.appmsg.get_log_message("BKY-80002"))


def test_bulksend_get_template_none(app_context_with_mock_g, mocker):
    """
    _get_templateがNoneを含むリストを返した場合にbulksendメソッドが適切に終了することを確認
    """
    mock_dbca = MagicMock()
    mocker.patch.object(MockNotification, '_fetch_table', return_value={'NOTIFICATION_DESTINATION': [{'id': None, 'UUID': '11', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': '●'}, {'id': ['AA'], 'UUID': '4c9d73d2-4f21-4afe-bb5f-794da5398579', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': None}]})
    mocker.patch.object(MockNotification, '_get_template', return_value=[{'id': None, 'UUID': '11', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': '●', 'template': None}, {'id': ['AA'], 'UUID': '4c9d73d2-4f21-4afe-bb5f-794da5398579', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': None, 'template': None}])
    event_list = [{"_id": "0000", "labels": {"labelA": "01"}, "event": {"EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": "2.7.0"}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}, {"_id": "0001", "labels": {"labelA": "02"}, "event": { "EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": 1}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}]
    decision_information = {"notification_type": OASENotificationType.RECEIVE}
    g = app_context_with_mock_g

    result = MockNotification.bulksend(mock_dbca, event_list, decision_information)

    assert result == {}
    app_context_with_mock_g.applogger.info.assert_any_call(g.appmsg.get_log_message("BKY-80003"))


def test_bulksend_fetch_notification_destination_empty(app_context_with_mock_g, mocker):
    """
    _fetch_notification_destinationが空リストを返した場合にbulksendメソッドが適切に終了することを確認
    """
    mock_dbca = MagicMock()
    mocker.patch.object(MockNotification, '_fetch_table', return_value={'NOTIFICATION_DESTINATION': [{'id': None, 'UUID': '11', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': '●'}, {'id': ['AA'], 'UUID': '4c9d73d2-4f21-4afe-bb5f-794da5398579', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': None}]})
    mocker.patch.object(MockNotification, '_get_template', return_value=[{'id': None, 'UUID': '11', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': '●', 'template': '[TITLE]\nDefault Title\n[BODY]\nDefault Message'}, {'id': ['AA'], 'UUID': '4c9d73d2-4f21-4afe-bb5f-794da5398579', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': None, 'template': '[TITLE]\nTitle AA\n[BODY]\nMessage AA'}])
    mocker.patch.object(MockNotification, '_fetch_notification_destination', return_value=[])
    event_list = [{"_id": "0000", "labels": {"labelA": "01"}, "event": {"EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": "2.7.0"}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}, {"_id": "0001", "labels": {"labelA": "02"}, "event": { "EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": 1}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}]
    decision_information = {"notification_type": OASENotificationType.RECEIVE}
    g = app_context_with_mock_g

    result = MockNotification.bulksend(mock_dbca, event_list, decision_information)

    assert result == {}
    app_context_with_mock_g.applogger.info.assert_any_call(g.appmsg.get_log_message("BKY-80004"))


def test_bulksend_process_event_call_api_error(app_context_with_mock_g, mocker):
    """
    イベント処理中にエラーが発生した場合、エラー情報が正しく収集されることを確認
    """
    mock_dbca = MagicMock()
    event_list = [{"_id": "0000", "labels": {"labelA": "01"}, "event": {"EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": "2.7.0"}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}, {"_id": "0001", "labels": {"labelA": "02"}, "event": { "EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": 1}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}]
    decision_information = {"notification_type": OASENotificationType.RECEIVE}

    # Mock environment variables
    mocker.patch.dict(os.environ, {
        'NOTIFICATION_BATCH_SIZE': '100',
        'MAX_WORKER_THREAD_POOL_SIZE': '12',
        'PLATFORM_API_HOST': 'localhost',
        'PLATFORM_API_PORT': '8080'
    })

    # Set up g values
    app_context_with_mock_g.get.side_effect = lambda key: {
        'ORGANIZATION_ID': 'org1',
        'WORKSPACE_ID': 'ws1',
        'USER_ID': 'user1',
        'LANGUAGE': 'ja'
    }.get(key)

    # Mock required methods
    mocker.patch.object(MockNotification, '_fetch_table', return_value={'NOTIFICATION_DESTINATION': [{'id': None, 'UUID': '11', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': '●'}, {'id': ['AA'], 'UUID': '4c9d73d2-4f21-4afe-bb5f-794da5398579', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': None}]})
    mocker.patch.object(MockNotification, '_get_template', return_value=[{'id': None, 'UUID': '11', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': '●', 'template': '[TITLE]\nDefault Title\n[BODY]\nDefault Message'}, {'id': ['AA'], 'UUID': '4c9d73d2-4f21-4afe-bb5f-794da5398579', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': None, 'template': '[TITLE]\nTitle AA\n[BODY]\nMessage AA'}])
    mocker.patch.object(MockNotification, '_fetch_notification_destination', return_value=['AA', 'BB'])

    # Mock _create_notise_message to return None for one event (simulating error)
    def side_effect(item, template):
        if item["_id"] == "0000":
            return {'id': None, 'UUID': '11', 'TEMPLATE_FILE': 'Receive.j2', 'IS_DEFAULT': '●', 'template': '[TITLE]\nDefault Title\n[BODY]\nDefault Message'}
        return None

    mocker.patch.object(MockNotification, '_create_notise_message', side_effect=side_effect)

    # Mock the thread execution method
    mocker.patch.object(
        MockNotification,
        '_Notification__call_notification_api_thread',
        return_value={
            "success": 0,
            "failure": 0,
            "failure_info": [],
            "success_notification_count": 0,
            "failure_notification_count": 0
        }
    )

    # Execute the method
    result = MockNotification.bulksend(mock_dbca, event_list, decision_information)

    # Check that failure_create_messages has been populated
    assert len(result["failure_create_messages"]) > 0
