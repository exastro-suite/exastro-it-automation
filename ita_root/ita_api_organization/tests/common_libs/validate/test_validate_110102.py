import pytest
from unittest.mock import patch, MagicMock
from flask import g, Flask
from io import BytesIO
from common_libs.validate import valid_110102
from common_libs.validate.valid_110102 import external_valid_menu_before


class DefaultTemplateId:
    """
    OASEのデフォルト通知テンプレートID
    """
    # 新規イベント（判定前）
    NEW = "1"
    # 既知イベント（判定時）
    EVALUATED = "2"
    # 既知イベント（TTL有効期限切れ）
    TIMEOUT = "3"
    # 未知イベント（判定時）
    UNDETECTED = "4"
    # 新規イベント（受信時）
    NEW_RECEIVED = "5"
    # 新規イベント（統合時）
    NEW_CONSOLIDATED = "6"


def create_flask_app_context():
    """
    Flask アプリケーションコンテキストを作成するヘルパー関数
    """
    app = Flask(__name__)
    app_context = app.app_context()
    app_context.push()

    # g.appmsg のモックを設定
    class AppMsgMock:
        def get_api_message(self, code, args=None):
            return code

    g.appmsg = AppMsgMock()
    g.LANGUAGE = "ja"

    return app_context


@pytest.mark.parametrize(
    "cmd_type, notification_template_id, event_type_current, event_type_entry,"
    "notification_destination_current, notification_destination_entry, expected_bool, expected_msg_code",
    [
        # 登録（Register）通知テンプレートIDが1～6の場合、イベント種別変更不可
        ("Register", DefaultTemplateId.NEW, "1", "2", None, None, False, "MSG-170001"),
        ("Register", DefaultTemplateId.EVALUATED, "1", "2", None, None, False, "MSG-170001"),
        ("Register", DefaultTemplateId.TIMEOUT, "1", "2", None, None, False, "MSG-170001"),
        ("Register", DefaultTemplateId.UNDETECTED, "1", "2", None, None, False, "MSG-170001"),
        ("Register", DefaultTemplateId.NEW_RECEIVED, "1", "2", None, None, False, "MSG-170001"),
        ("Register", DefaultTemplateId.NEW_CONSOLIDATED, "1", "2", None, None, False, "MSG-170001"),
        # 登録（Register）通知テンプレートIDが1～6の場合、通知先がNULL以外はNG
        ("Register", DefaultTemplateId.NEW, "1", "1", None, "dest", False, "MSG-170002"),
        ("Register", DefaultTemplateId.EVALUATED, "1", "1", None, "dest", False, "MSG-170002"),
        ("Register", DefaultTemplateId.TIMEOUT, "1", "1", None, "dest", False, "MSG-170002"),
        ("Register", DefaultTemplateId.UNDETECTED, "1", "1", None, "dest", False, "MSG-170002"),
        ("Register", DefaultTemplateId.NEW_RECEIVED, "1", "1", None, "dest", False, "MSG-170002"),
        ("Register", DefaultTemplateId.NEW_CONSOLIDATED, "1", "1", None, "dest", False, "MSG-170002"),
        # 登録（Register）通知テンプレートIDが1～6で正常
        ("Register", DefaultTemplateId.NEW, "1", "1", None, None, True, None),
        ("Register", DefaultTemplateId.EVALUATED, "1", "1", None, None, True, None),
        ("Register", DefaultTemplateId.TIMEOUT, "1", "1", None, None, True, None),
        ("Register", DefaultTemplateId.UNDETECTED, "1", "1", None, None, True, None),
        ("Register", DefaultTemplateId.NEW_RECEIVED, "1", "1", None, None, True, None),
        ("Register", DefaultTemplateId.NEW_CONSOLIDATED, "1", "1", None, None, True, None),

        # 更新（Update）通知テンプレートIDが1～6 の場合 イベント種別変更不可
        ("Update", DefaultTemplateId.NEW, "1", "2", None, None, False, "MSG-170001"),
        ("Update", DefaultTemplateId.EVALUATED, "1", "2", None, None, False, "MSG-170001"),
        ("Update", DefaultTemplateId.TIMEOUT, "1", "2", None, None, False, "MSG-170001"),
        ("Update", DefaultTemplateId.UNDETECTED, "1", "2", None, None, False, "MSG-170001"),
        ("Update", DefaultTemplateId.NEW_RECEIVED, "1", "2", None, None, False, "MSG-170001"),
        ("Update", DefaultTemplateId.NEW_CONSOLIDATED, "1", "2", None, None, False, "MSG-170001"),
        # 更新（Update）通知テンプレートIDが1～6の場合、通知先がNULL以外はNG
        ("Update", DefaultTemplateId.NEW, "1", "1", None, "dest", False, "MSG-170002"),
        ("Update", DefaultTemplateId.EVALUATED, "1", "1", None, "dest", False, "MSG-170002"),
        ("Update", DefaultTemplateId.TIMEOUT, "1", "1", None, "dest", False, "MSG-170002"),
        ("Update", DefaultTemplateId.UNDETECTED, "1", "1", None, "dest", False, "MSG-170002"),
        ("Update", DefaultTemplateId.NEW_RECEIVED, "1", "1", None, "dest", False, "MSG-170002"),
        ("Update", DefaultTemplateId.NEW_CONSOLIDATED, "1", "1", None, "dest", False, "MSG-170002"),
        # 更新（Update）通知テンプレートIDが1～6で正常
        ("Update", DefaultTemplateId.NEW, "1", "1", None, None, True, None),
        ("Update", DefaultTemplateId.EVALUATED, "1", "1", None, None, True, None),
        ("Update", DefaultTemplateId.TIMEOUT, "1", "1", None, None, True, None),
        ("Update", DefaultTemplateId.UNDETECTED, "1", "1", None, None, True, None),
        ("Update", DefaultTemplateId.NEW_RECEIVED, "1", "1", None, None, True, None),
        ("Update", DefaultTemplateId.NEW_CONSOLIDATED, "1", "1", None, None, True, None),

        # 登録（Register）通知テンプレートIDが1～6以外の場合、通知先が空は不可
        ("Register", "XX-XX-XX-XX", "1", "1", None, None, False, "MSG-170003"),
        # 登録（Register）通知テンプレートIDが1～6以外で通知先がユニークでない
        ("Register", "XX-XX-XX-XX", "1", "1", None, '{"id": ["destA","destB","destC"]}', False, "MSG-170004"),
        # 登録（Register）通知テンプレートIDが1～6以外で正常
        ("Register", "XX-XX-XX-XX", "1", "1", None, "destZ", True, None),

        # 更新（Update）通知テンプレートIDが1～6以外の場合、通知先が空は不可
        ("Update", "XX-XX-XX-XX", "1", "1", None, None, False, "MSG-170003"),
        # 更新（Update）通知テンプレートIDが1～6以外で通知先がユニークでないのはNG
        ("Register", "XX-XX-XX-XX", "1", "1", None, '{"id": ["destA","destB","destC"]}', False, "MSG-170004"),
        # 更新（Update）通知テンプレートIDが1～6以外で正常
        ("Update", "XX-XX-XX-XX", "1", "1", "destZ", "destZ", True, None),

        # 削除（Delete）通知テンプレートIDが1～6で削除はNG
        ("Delete", DefaultTemplateId.NEW, "1", "1", None, None, False, "MSG-170005"),
        ("Delete", DefaultTemplateId.EVALUATED, "1", "1", None, None, False, "MSG-170005"),
        ("Delete", DefaultTemplateId.TIMEOUT, "1", "1", None, None, False, "MSG-170005"),
        ("Delete", DefaultTemplateId.UNDETECTED, "1", "1", None, None, False, "MSG-170005"),
        ("Delete", DefaultTemplateId.NEW_RECEIVED, "1", "1", None, None, False, "MSG-170005"),
        ("Delete", DefaultTemplateId.NEW_CONSOLIDATED, "1", "1", None, None, False, "MSG-170005"),
        # 削除（Delete）通知テンプレートIDが1～6以外で削除はOK
        ("Delete", "XX-XX-XX-XX", "1", "1", None, None, True, None),

        # 廃止（Discard）通知テンプレートIDが1～6で廃止はNG
        ("Discard", DefaultTemplateId.NEW, "1", "1", None, None, False, "MSG-170006"),
        ("Discard", DefaultTemplateId.EVALUATED, "1", "1", None, None, False, "MSG-170006"),
        ("Discard", DefaultTemplateId.TIMEOUT, "1", "1", None, None, False, "MSG-170006"),
        ("Discard", DefaultTemplateId.UNDETECTED, "1", "1", None, None, False, "MSG-170006"),
        ("Discard", DefaultTemplateId.NEW_RECEIVED, "1", "1", None, None, False, "MSG-170006"),
        ("Discard", DefaultTemplateId.NEW_CONSOLIDATED, "1", "1", None, None, False, "MSG-170006"),
        # 廃止（Discard）通知テンプレートIDが1～6以外で廃止はOK
        ("Discard", "XX-XX-XX-XX", "1", "1", None, None, True, None),

        # 復活（Restore）通知テンプレートIDが1～6で復活はNG
        ("Restore", DefaultTemplateId.NEW, "1", "1", None, None, False, "MSG-170007"),
        ("Restore", DefaultTemplateId.EVALUATED, "1", "1", None, None, False, "MSG-170007"),
        ("Restore", DefaultTemplateId.TIMEOUT, "1", "1", None, None, False, "MSG-170007"),
        ("Restore", DefaultTemplateId.UNDETECTED, "1", "1", None, None, False, "MSG-170007"),
        ("Restore", DefaultTemplateId.NEW_RECEIVED, "1", "1", None, None, False, "MSG-170007"),
        ("Restore", DefaultTemplateId.NEW_CONSOLIDATED, "1", "1", None, None, False, "MSG-170007"),
        # 復活（Restore）通知テンプレートIDが1～6以外でカレントの通知先がユニークでないのはNG
        ("Restore", "XX-XX-XX-XX", "1", "1", '{"id": ["destA","destB","destC"]}', None, False, "MSG-170004"),
        # 復活（Restore）通知テンプレートIDが1～6以外で復活はOK
        ("Restore", "XX-XX-XX-XX", "1", "1", "destZ", "destZ", True, None),
    ]
)
def test_external_valid_menu_before(cmd_type,
                                    notification_template_id,
                                    event_type_current,
                                    event_type_entry,
                                    notification_destination_current,
                                    notification_destination_entry,
                                    expected_bool,
                                    expected_msg_code,
                                    monkeypatch):
    """
    external_valid_menu_before関数のテスト
    """
    app_context = create_flask_app_context()
    try:
        objdbca = MagicMock()
        objtable = {
            "COLINFO": {
                "template_file": {
                    "COLUMN_NAME_JA": "テンプレートファイル",
                    "COLUMN_NAME_EN": "Template File"
                }
            }
        }

        option = {
            "uuid": "",
            "uuid_jnl": "",
            "cmd_type": cmd_type,
            "current_parameter": {
                "parameter": {
                    "discard": "0",
                    "event_type": event_type_current,
                    "notification_template_id": notification_template_id,
                    "notification_destination": notification_destination_current
                }
            },
            "entry_parameter": {
                "parameter": {
                    "discard": "0",
                    "event_type": event_type_entry,
                    "notification_template_id": notification_template_id,
                    "notification_destination": notification_destination_entry,
                    "remarks": "pytest",
                    "template_file": "テンプレートテスト用.txt"
                },
                "file_path": {}
            }
        }

        # check_duplicate_notification_destination 関数のモックを定義
        def test_check_duplicate_notification_destination(objdbca, notification_template_id, event_type_entry, notification_destination_entry):
            # ユニークでない場合は重複する通知先名称を返す
            if notification_destination_entry == '{"id": ["destA","destB","destC"]}':
                return "通知先テストA"
            # ユニークな場合は空文字
            if notification_destination_entry == "destZ":
                return ""
            # 通知先が空の場合も空文字
            if notification_destination_entry is None:
                return ""
            return ""

        # この関数の動作を、テストの間だけ一時的に変更
        monkeypatch.setattr("common_libs.validate.valid_110102.check_duplicate_notification_destination", test_check_duplicate_notification_destination)

        retBool, msg, _ = external_valid_menu_before(objdbca, objtable, option)
        assert retBool == expected_bool
        if expected_msg_code:
            assert expected_msg_code in msg[0]
        else:
            assert msg == []
    finally:
        app_context.pop()


@pytest.mark.parametrize(
    "notification_template_id, expected",
    [
        (DefaultTemplateId.NEW, True),
        (DefaultTemplateId.EVALUATED, True),
        (DefaultTemplateId.TIMEOUT, True),
        (DefaultTemplateId.UNDETECTED, True),
        (DefaultTemplateId.NEW_RECEIVED, True),
        (DefaultTemplateId.NEW_CONSOLIDATED, True),
        ("7", False),
        ("", False),
        (None, False),
        ("abc", False),
    ]
)
def test_is_id_in_default_range(notification_template_id, expected):
    """
    通知先のIDが1～6の範囲内かどうかを返す関数のテスト

    """
    assert valid_110102.is_id_in_default_range(notification_template_id) == expected


@pytest.mark.parametrize(
    "db_records, notification_template_id, event_type, notification_destination, expected",
    [
        # 一致する通知先IDがある場合
        (
            [{"NOTIFICATION_DESTINATION": '{"id": ["destA","destB","destC"]}'}],
            "XX-XX-XX-XX", "1", '{"id": ["destC","destY","destZ"]}', "通知先テストC"
        ),
        # 一致する通知先IDがない場合
        (
            [{"NOTIFICATION_DESTINATION": '{"id": ["destA","destB","destC"]}'}],
            "XX-XX-XX-XX", "1", '{"id": ["destY","destZ"]}', ""
        ),
        # 通知先が空の場合
        (
            [{"NOTIFICATION_DESTINATION": '{"id": ["destA","destB","destC"]}'}],
            "XX-XX-XX-XX", "1", '', ""
        ),
    ]
)
def test_check_duplicate_notification_destination(db_records, notification_template_id, event_type, notification_destination, expected):
    """
    通知先の重複チェック関数のテスト

    """
    # 通知先名称辞書のモック
    notification_dest_dict = {
        "destA": "通知先テストA",
        "destB": "通知先テストB",
        "destC": "通知先テストC",
        "destY": "通知先テストY",
        "destZ": "通知先テストZ",
    }

    # get_notification_destinationとfetch_notification_destination_dictをモック
    with patch("common_libs.validate.valid_110102.get_notification_destination", return_value=db_records), \
         patch("common_libs.notification.notification_base.Notification.fetch_notification_destination_dict", return_value=notification_dest_dict):
        result = valid_110102.check_duplicate_notification_destination(
            objdbca=None,
            notification_template_id=notification_template_id,
            event_type=event_type,
            notification_destination=notification_destination
        )
        assert result == expected


@pytest.mark.parametrize(
    "notification_template_id, event_type, expected_sql, expected_param",
    [
        (None, "1", "WHERE DISUSE_FLAG=0 AND EVENT_TYPE = %s", [["1"]]),
        ("XX-XX-XX-XX", "2", "WHERE DISUSE_FLAG=0 AND NOTIFICATION_TEMPLATE_ID <> %s AND EVENT_TYPE = %s", [["XX-XX-XX-XX"], ["2"]]),
    ]
)
def test_get_notification_destination(notification_template_id, event_type, expected_sql, expected_param):
    """
    通知先取得関数のテスト
    """

    # objdbcaのtable_selectをモック
    mock_objdbca = MagicMock()
    mock_objdbca.table_select.return_value = [{"NOTIFICATION_DESTINATION": "dummy"}]

    result = valid_110102.get_notification_destination(mock_objdbca, notification_template_id, event_type)

    # SQLとパラメータが正しく渡されているか検証
    mock_objdbca.table_select.assert_called_once_with(
        "T_OASE_NOTIFICATION_TEMPLATE_COMMON",
        expected_sql,
        expected_param
    )
    # 戻り値がtable_selectの返り値と一致するか
    assert result == [{"NOTIFICATION_DESTINATION": "dummy"}]


@pytest.mark.parametrize(
    "file_content, is_binary, is_jinja2, contains_title, contains_body, expected_bool, expected_msg_codes",
    [
        # 正常なテンプレートファイル
        (b"{{ title }}\n{{ body }}", False, True, True, True, True, []),
        # バイナリファイルの場合
        (b"\x00\x01\x02", True, False, False, False, False, ["499-01814"]),
        # Jinja2形式でない場合
        (b"Invalid Template", False, False, False, False, False, ["499-01815"]),
        # タイトルが含まれない場合
        (b"{{ body }}", False, True, False, True, False, ["499-01816"]),
        # 本文が含まれない場合
        (b"{{ title }}", False, True, True, False, False, ["499-01817"]),
        # 複数のエラーが発生する場合（Jinja2形式だがタイトルと本文が不足）
        (b"{{ invalid }}", False, True, False, False, False, ["499-01816", "499-01817"]),
    ]
)
def test_validate_template_file(file_content, is_binary, is_jinja2, contains_title, contains_body, expected_bool, expected_msg_codes, monkeypatch):
    """
    validate_template_file関数のテスト
    """
    app_context = create_flask_app_context()
    try:
        # モックの設定
        def mock_is_binary_file(content):
            return is_binary

        def mock_is_jinja2_template(content):
            return is_jinja2

        def mock_contains_title(content):
            return contains_title

        def mock_contains_body(content):
            return contains_body

        monkeypatch.setattr("common_libs.notification.validator.is_binary_file", mock_is_binary_file)
        monkeypatch.setattr("common_libs.notification.validator.is_jinja2_template", mock_is_jinja2_template)
        monkeypatch.setattr("common_libs.notification.validator.contains_title", mock_contains_title)
        monkeypatch.setattr("common_libs.notification.validator.contains_body", mock_contains_body)

        # テスト対象の関数を呼び出し
        target_column_name = {"ja": "テンプレートファイル", "en": "Template File"}
        target_lang = "ja"
        msg = []

        # open をモックしてファイル内容を返す
        with patch("builtins.open", return_value=BytesIO(file_content)):
            retBool, msg = valid_110102.validate_template_file("dummy_path", target_column_name, target_lang, msg)

        # 結果の検証
        assert retBool == expected_bool
        assert len(msg) == len(expected_msg_codes)
        for code in expected_msg_codes:
            assert code in msg
    finally:
        app_context.pop()
