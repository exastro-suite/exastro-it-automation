import pytest
from unittest.mock import MagicMock
from flask import g, Flask

from common_libs.validate.valid_110102 import external_valid_menu_before


@pytest.mark.parametrize(
    "cmd_type, notification_template_id, event_type_current, event_type_entry,"
    "notification_destination_current, notification_destination_entry, expected_bool, expected_msg_code",
    [
        # 登録（Register）通知テンプレートIDが1～4の場合、イベント種別変更不可
        ("Register", "1", "1", "2", None, None, False, "MSG-170001"),
        ("Register", "2", "1", "2", None, None, False, "MSG-170001"),
        ("Register", "3", "1", "2", None, None, False, "MSG-170001"),
        ("Register", "4", "1", "2", None, None, False, "MSG-170001"),
        # 登録（Register）通知テンプレートIDが1～4の場合、通知先がNULL以外はNG
        ("Register", "1", "1", "1", None, "dest", False, "MSG-170002"),
        ("Register", "2", "1", "1", None, "dest", False, "MSG-170002"),
        ("Register", "3", "1", "1", None, "dest", False, "MSG-170002"),
        ("Register", "4", "1", "1", None, "dest", False, "MSG-170002"),
        # 登録（Register）通知テンプレートIDが1～4で正常
        ("Register", "1", "1", "1", None, None, True, None),

        # 更新（Update）通知テンプレートIDが1～4 の場合 イベント種別変更不可
        ("Update", "1", "1", "2", None, None, False, "MSG-170001"),
        ("Update", "2", "1", "2", None, None, False, "MSG-170001"),
        ("Update", "3", "1", "2", None, None, False, "MSG-170001"),
        ("Update", "4", "1", "2", None, None, False, "MSG-170001"),
        # 更新（Update）通知テンプレートIDが1～4の場合、通知先がNULL以外はNG
        ("Update", "1", "1", "1", None, "dest", False, "MSG-170002"),
        ("Update", "2", "1", "1", None, "dest", False, "MSG-170002"),
        ("Update", "3", "1", "1", None, "dest", False, "MSG-170002"),
        ("Update", "4", "1", "1", None, "dest", False, "MSG-170002"),
        # 更新（Update）通知テンプレートIDが1～4で正常
        ("Update", "1", "1", "1", None, None, True, None),

        # 登録（Register）通知テンプレートIDが1～4以外の場合、通知先が空は不可
        ("Register", "5", "1", "1", None, None, False, "MSG-170003"),
        # 登録（Register）通知テンプレートIDが1～4以外で通知先がユニークでない
        ("Register", "5", "1", "1", None, "destA", False, "MSG-170004"),
        # 登録（Register）通知テンプレートIDが1～4以外で正常
        ("Register", "1", "1", "1", None, None, True, None),

        # 更新（Update）通知テンプレートIDが1～4以外の場合、通知先が空は不可
        ("Update", "5", "1", "1", None, None, False, "MSG-170003"),
        # 更新（Update）通知テンプレートIDが1～4以外で通知先がユニークでないのはNG
        ("Update", "5", "1", "1", None, "destA", False, "MSG-170004"),
        # 更新（Update）通知テンプレートIDが1～4以外で正常
        ("Update", "1", "1", "1", None, None, True, None),

        # 削除（Delete）通知テンプレートIDが1～4で削除はNG
        ("Delete", "1", "1", "1", None, None, False, "MSG-170005"),
        ("Delete", "2", "1", "1", None, None, False, "MSG-170005"),
        ("Delete", "3", "1", "1", None, None, False, "MSG-170005"),
        ("Delete", "4", "1", "1", None, None, False, "MSG-170005"),
        # 削除（Delete）通知テンプレートIDが1～4以外で削除はOK
        ("Delete", "5", "1", "1", None, None, True, None),

        # 廃止（Discard）通知テンプレートIDが1～4で削除はNG
        ("Discard", "1", "1", "1", None, None, False, "MSG-170006"),
        ("Discard", "2", "1", "1", None, None, False, "MSG-170006"),
        ("Discard", "3", "1", "1", None, None, False, "MSG-170006"),
        ("Discard", "4", "1", "1", None, None, False, "MSG-170006"),
        # 廃止（Discard）通知テンプレートIDが1～4以外で削除はOK
        ("Discard", "5", "1", "1", None, None, True, None),

        # 復活（Restore）通知テンプレートIDが1～4で削除はNG
        ("Restore", "1", "1", "1", None, None, False, "MSG-170007"),
        ("Restore", "2", "1", "1", None, None, False, "MSG-170007"),
        ("Restore", "3", "1", "1", None, None, False, "MSG-170007"),
        ("Restore", "4", "1", "1", None, None, False, "MSG-170007"),
        # 復活（Restore）通知テンプレートIDが1～4以外でカレントの通知先がユニークでないのはNG
        ("Restore", "5", "1", "1", "destA", None, False, "MSG-170004"),
        # 復活（Restore）通知テンプレートIDが1～4以外で削除はOK
        ("Restore", "5", "1", "1", None, None, True, None),

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
    app = Flask(__name__)
    with app.app_context():
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

        class AppMsgMock:
            def get_api_message(self, code, args=None):
                return code

        g.appmsg = AppMsgMock()
        g.LANGUAGE = "ja"

        # get_notification_destination 関数のモックを定義
        def mock_get_notification_destination(objdbca, notification_template_id, event_type_entry, notification_destination_entry):
            if notification_destination_entry == "destA":
                return 1
            return 0

        # この関数の動作を、テストの間だけ一時的に変更
        monkeypatch.setattr("common_libs.validate.valid_110102.get_notification_destination", mock_get_notification_destination)

        retBool, msg, _ = external_valid_menu_before(objdbca, objtable, option)
        assert retBool == expected_bool
        if expected_msg_code:
            assert expected_msg_code in msg[0]
        else:
            assert msg == []
