# Copyright 2025 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
 
import pytest
from unittest.mock import patch, MagicMock
from flask import g, Flask
from common_libs.validate import valid_110102
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
        ("Register", "2", "1", "1", None, None, True, None),
        ("Register", "3", "1", "1", None, None, True, None),
        ("Register", "4", "1", "1", None, None, True, None),

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
        ("Update", "2", "1", "1", None, None, True, None),
        ("Update", "3", "1", "1", None, None, True, None),
        ("Update", "4", "1", "1", None, None, True, None),

        # 登録（Register）通知テンプレートIDが1～4以外の場合、通知先が空は不可
        ("Register", "5", "1", "1", None, None, False, "MSG-170003"),
        # 登録（Register）通知テンプレートIDが1～4以外で通知先がユニークでない
        ("Register", "5", "1", "1", None, '{"id": ["destA","destB","destC"]}', False, "MSG-170004"),
        # 登録（Register）通知テンプレートIDが1～4以外で正常
        ("Register", "5", "1", "1", None, "destZ", True, None),

        # 更新（Update）通知テンプレートIDが1～4以外の場合、通知先が空は不可
        ("Update", "5", "1", "1", None, None, False, "MSG-170003"),
        # 更新（Update）通知テンプレートIDが1～4以外で通知先がユニークでないのはNG
        ("Register", "5", "1", "1", None, '{"id": ["destA","destB","destC"]}', False, "MSG-170004"),
        # 更新（Update）通知テンプレートIDが1～4以外で正常
        ("Update", "5", "1", "1", "destZ", "destZ", True, None),

        # 削除（Delete）通知テンプレートIDが1～4で削除はNG
        ("Delete", "1", "1", "1", None, None, False, "MSG-170005"),
        ("Delete", "2", "1", "1", None, None, False, "MSG-170005"),
        ("Delete", "3", "1", "1", None, None, False, "MSG-170005"),
        ("Delete", "4", "1", "1", None, None, False, "MSG-170005"),
        # 削除（Delete）通知テンプレートIDが1～4以外で削除はOK
        ("Delete", "5", "1", "1", None, None, True, None),

        # 廃止（Discard）通知テンプレートIDが1～4で廃止はNG
        ("Discard", "1", "1", "1", None, None, False, "MSG-170006"),
        ("Discard", "2", "1", "1", None, None, False, "MSG-170006"),
        ("Discard", "3", "1", "1", None, None, False, "MSG-170006"),
        ("Discard", "4", "1", "1", None, None, False, "MSG-170006"),
        # 廃止（Discard）通知テンプレートIDが1～4以外で廃止はOK
        ("Discard", "5", "1", "1", None, None, True, None),

        # 復活（Restore）通知テンプレートIDが1～4で復活はNG
        ("Restore", "1", "1", "1", None, None, False, "MSG-170007"),
        ("Restore", "2", "1", "1", None, None, False, "MSG-170007"),
        ("Restore", "3", "1", "1", None, None, False, "MSG-170007"),
        ("Restore", "4", "1", "1", None, None, False, "MSG-170007"),
        # 復活（Restore）通知テンプレートIDが1～4以外でカレントの通知先がユニークでないのはNG
        ("Restore", "5", "1", "1", '{"id": ["destA","destB","destC"]}', None, False, "MSG-170004"),
        # 復活（Restore）通知テンプレートIDが1～4以外で復活はOK
        ("Restore", "5", "1", "1", "destZ", "destZ", True, None),

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


@pytest.mark.parametrize(
    "notification_template_id, expected",
    [
        ("1", True),
        ("2", True),
        ("3", True),
        ("4", True),
        ("5", False),
        ("", False),
        (None, False),
        ("abc", False),
    ]
)
def test_is_id_in_default_range(notification_template_id, expected):
    """
    通知先のIDが1～4の範囲内かどうかを返す関数のテスト
    
    """
    assert valid_110102.is_id_in_default_range(notification_template_id) == expected


@pytest.mark.parametrize(
    "db_records, notification_template_id, event_type, notification_destination, expected",
    [
        # 一致する通知先IDがある場合
        (
            [{"NOTIFICATION_DESTINATION": '{"id": ["destA","destB","destC"]}'}],
            "5", "1", '{"id": ["destC","destY","destZ"]}', "通知先テストC"
        ),
        # 一致する通知先IDがない場合
        (
            [{"NOTIFICATION_DESTINATION": '{"id": ["destA","destB","destC"]}'}],
            "5", "1", '{"id": ["destY","destZ"]}', ""
        ),
        # 通知先が空の場合
        (
            [{"NOTIFICATION_DESTINATION": '{"id": ["destA","destB","destC"]}'}],
            "5", "1", '', ""
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
        ("5", "2", "WHERE DISUSE_FLAG=0 AND NOTIFICATION_TEMPLATE_ID <> %s AND EVENT_TYPE = %s", [["5"], ["2"]]),
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

