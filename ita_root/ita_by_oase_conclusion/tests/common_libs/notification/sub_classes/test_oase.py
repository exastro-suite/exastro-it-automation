import os
from datetime import datetime
from common_libs.notification.sub_classes.oase import OASE, OASENotificationType


def test_fetch_table_valid_new_notification(app_context_with_mock_g, mocker):
    """
    _fetch_tableメソッドが、NEWタイプの通知に対して正しくテーブルをフェッチすることを確認
    """
    mock_dbca = mocker.MagicMock()
    mock_dbca.sql_execute.return_value = [{"UUID": "1", "TEMPLATE_FILE": "template.txt", "NOTIFICATION_DESTINATION": None, "IS_DEFAULT": "●"}]

    decision_info = {"notification_type": OASENotificationType.NEW}

    result = OASE._fetch_table(mock_dbca, decision_info)

    expected_query = "SELECT NOTIFICATION_TEMPLATE_ID AS UUID, TEMPLATE_FILE, NOTIFICATION_DESTINATION, IS_DEFAULT FROM T_OASE_NOTIFICATION_TEMPLATE_COMMON WHERE DISUSE_FLAG=0 AND EVENT_TYPE=%s"
    expected_values = ["1"]
    mock_dbca.sql_execute.assert_called_once_with(expected_query, expected_values)

    assert result == {"NOTIFICATION_DESTINATION": [{"id": None, "UUID": "1", "TEMPLATE_FILE": "template.txt", "IS_DEFAULT": "●"}]}


def test_fetch_table_valid_before_action_notification(app_context_with_mock_g, mocker):
    """
    _fetch_tableメソッドが、BEFORE_ACTIONタイプの通知に対して正しくテーブルをフェッチすることを確認
    """
    mock_dbca = mocker.MagicMock()
    mock_dbca.sql_execute.return_value = [{"UUID": "10", "TEMPLATE_FILE": "before.txt", "NOTIFICATION_DESTINATION": '{"id": ["dest1", "dest2"]}'}]

    decision_info = {"notification_type": OASENotificationType.BEFORE_ACTION, "rule_id": "10"}

    result = OASE._fetch_table(mock_dbca, decision_info)

    expected_query = "SELECT RULE_ID AS UUID, BEFORE_NOTIFICATION AS TEMPLATE_FILE, BEFORE_NOTIFICATION_DESTINATION AS NOTIFICATION_DESTINATION FROM T_OASE_RULE WHERE DISUSE_FLAG=0 AND RULE_ID=%s"
    expected_values = ["10"]
    mock_dbca.sql_execute.assert_called_once_with(expected_query, expected_values)

    assert result == {"NOTIFICATION_DESTINATION": [{"id": ["dest1", "dest2"], "UUID": "10", "TEMPLATE_FILE": "before.txt", "IS_DEFAULT": None}]}


def test_fetch_table_missing_rule_id_for_before_action(app_context_with_mock_g, mocker):
    """
    _fetch_tableメソッドが、BEFORE_ACTIONタイプでrule_idがない場合にNoneを返すことを確認
    """
    mock_dbca = mocker.MagicMock()
    decision_info = {"notification_type": OASENotificationType.BEFORE_ACTION, "rule_id": None}

    result = OASE._fetch_table(mock_dbca, decision_info)

    mock_dbca.sql_execute.assert_not_called()
    app_context_with_mock_g.applogger.info.assert_called()
    assert result is None


def test_get_template_valid_file(app_context_with_mock_g, mocker):
    """
    _get_templateメソッドが、有効なテンプレートファイルを正しく読み込むことを確認
    """
    mock_storage_access = mocker.patch('common_libs.common.storage_access.storage_read')
    mock_access_file = mock_storage_access.return_value
    mock_access_file.read.return_value = b'template_content'

    mocker.patch('common_libs.common.util.get_upload_file_path').return_value = {"file_path": os.path.join(os.environ.get('STORAGEPATH'), "mock_org_id/mock_workspace_id/uploadfiles/110102/template_file/mock_uuid/template.txt")}

    fetch_data = {"NOTIFICATION_DESTINATION": [{"UUID": "mock_uuid", "TEMPLATE_FILE": "template.txt"}]}
    decision_info = {"notification_type": OASENotificationType.NEW}

    result = OASE._get_template(fetch_data, decision_info)

    mock_access_file.open.assert_called_once_with(os.path.join(os.environ.get('STORAGEPATH'), "mock_org_id/mock_workspace_id/uploadfiles/110102/template_file/mock_uuid/template.txt"))
    mock_access_file.read.assert_called_once()
    mock_access_file.close.assert_called_once()
    assert result == [{"UUID": "mock_uuid", "TEMPLATE_FILE": "template.txt", "template": b'template_content'}]


def test_get_template_file_read_error(app_context_with_mock_g, mocker):
    """
    _get_templateメソッドが、ファイルの読み込みエラー時にNoneを返すことを確認
    """
    mock_storage_access = mocker.patch('common_libs.common.storage_access.storage_read')
    mock_access_file = mock_storage_access.return_value
    mock_access_file.open.side_effect = Exception("File read error")

    mocker.patch('common_libs.common.util.get_upload_file_path').return_value = {"file_path": "/mock/path/to/template.txt"}

    fetch_data = {"NOTIFICATION_DESTINATION": [{"UUID": "mock_uuid", "TEMPLATE_FILE": "template.txt"}]}
    decision_info = {"notification_type": OASENotificationType.NEW}

    result = OASE._get_template(fetch_data, decision_info)

    assert result == [{"UUID": "mock_uuid", "TEMPLATE_FILE": "template.txt", "template": None}]
    app_context_with_mock_g.applogger.info.assert_called()
    app_context_with_mock_g.applogger.error.assert_called()


def test_fetch_notification_destination_before_action_valid(app_context_with_mock_g, mocker):
    """
    _fetch_notification_destinationメソッドが、BEFORE_ACTIONタイプで通知先を正しくフェッチすることを確認
    """
    # fetch_dataから直接 'id' リストを取得する形に修正
    fetch_data = {"NOTIFICATION_DESTINATION": [{"id": ["dest1", "dest2"]}]}
    decision_info = {"notification_type": OASENotificationType.BEFORE_ACTION}

    # _call_setting_notification_apiのモック設定
    mocker.patch.object(OASE, '_call_setting_notification_api', return_value={"data": [{"id": "dest1"}, {"id": "dest2"}, {"id": "dest3"}]})

    # 修正後のメソッド呼び出し
    result = OASE._fetch_notification_destination(fetch_data, decision_info)
    assert result == ["dest1", "dest2"]


def test_fetch_notification_destination_new_valid(app_context_with_mock_g, mocker):
    """
    _fetch_notification_destinationメソッドが、NEWタイプで通知先を正しくフェッチすることを確認
    """
    fetch_data = {"NOTIFICATION_DESTINATION": [{"id": ["dest1", "dest2"]}]}
    decision_info = {"notification_type": OASENotificationType.NEW}

    mocker.patch.object(OASE, '_call_setting_notification_api', return_value={"data": [{"id": "dest1"}, {"id": "dest2"}]})

    result = OASE._fetch_notification_destination(fetch_data, decision_info)

    OASE._call_setting_notification_api.assert_called_once_with(event_type_true=["ita.event_type.new"])
    assert result == ["dest1", "dest2"]


def test_convert_message_valid(app_context_with_mock_g):
    """
    _convert_messageメソッドが、タイムスタンプとタイプを正しく変換することを確認
    """
    timestamp = 1625097600
    item = {
        "labels": {
            "_exastro_fetched_time": str(timestamp),
            "_exastro_end_time": str(timestamp),
            "_exastro_type": "event"
        }
    }

    result = OASE._convert_message(item)

    expected_fetched_time = datetime.fromtimestamp(timestamp).strftime("%Y/%m/%d %H:%M:%S")
    expected_end_time = datetime.fromtimestamp(timestamp).strftime("%Y/%m/%d %H:%M:%S")
    expected_type = "event"

    assert result["labels"]["_exastro_fetched_time"] == expected_fetched_time
    assert result["labels"]["_exastro_end_time"] == expected_end_time
    assert result["labels"]["_exastro_type"] == expected_type


def test_get_data_method():
    """
    _get_dataメソッドが、定義済みの辞書を正しく返すことを確認
    """
    result = OASE._get_data()

    expected_data = {
        "func_id": "1102",
        "func_informations": {"menu_group_name": "OASE"}
    }

    assert result == expected_data
