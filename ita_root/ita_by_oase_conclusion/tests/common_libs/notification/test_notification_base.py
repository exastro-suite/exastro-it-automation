import pytest
from unittest.mock import MagicMock
import copy
import json
import os
import requests
from jinja2 import Template, UndefinedError
from common_libs.notification.notification_base import Notification
from common_libs.common.exception import AppException


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
