#   Copyright 2026 NEC Corporation
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
"""
tools/ita_menu_create.py (create-menu / update-menu / get-menu-definition) の
ユニットテスト

ダウンストリームAPI(ita_api_organization / Exastro Platform)へのHTTP
アクセスはrequests_mockで全てモックし、実際のネットワークアクセスは一切
行わない。異常系では、g.applogger.info の呼び出し回数はチェックせず、
送出される例外のメッセージ・ステータスコード・戻り値の内容で検証する。
"""

import base64

import pytest
from flask import g

from tools import ita_menu_create as menu_create_tool
from libs import HTTPException

ORG_ID = "org1"
WS_ID = "ws1"
ITA_HOST = "ita-api-organization"
ITA_PORT = "8080"
PLATFORM_HOST = "platform-host"
PLATFORM_PORT = "9090"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    """ダウンストリームAPI接続先の環境変数を固定する"""
    monkeypatch.setenv("ITA_API_ORAGANIZATION_HOST", ITA_HOST)
    monkeypatch.setenv("ITA_API_ORAGANIZATION_PORT", ITA_PORT)
    monkeypatch.setenv("PLATFORM_API_HOST", PLATFORM_HOST)
    monkeypatch.setenv("PLATFORM_API_PORT", PLATFORM_PORT)


def _create_url(organization_id=ORG_ID, workspace_id=WS_ID):
    return "http://{}:{}/api/{}/workspaces/{}/ita/create/define/execute/".format(
        ITA_HOST, ITA_PORT, organization_id, workspace_id
    )


def _get_menu_definition_url(menu_rest_name, organization_id=ORG_ID, workspace_id=WS_ID):
    return "http://{}:{}/api/{}/workspaces/{}/ita/create/define/{}/".format(
        ITA_HOST, ITA_PORT, organization_id, workspace_id, menu_rest_name
    )


def _platform_roles_url(organization_id=ORG_ID):
    return "http://{}:{}/api/{}/platform/roles".format(PLATFORM_HOST, PLATFORM_PORT, organization_id)


def _payload(organization_id=ORG_ID, workspace_id=WS_ID):
    return {"organization_id": organization_id, "workspace_id": workspace_id}


def _menu(overrides=None):
    menu = {
        "menu_name": "Menu1",
        "menu_name_rest": "menu1",
        "description": "desc",
        "hostgroup": "0",
    }
    if overrides:
        menu.update(overrides)
    return menu


def _menu_definition(menu_overrides=None, column=None):
    return {
        "menu": _menu(menu_overrides),
        "column": column if column is not None else {},
    }


def _encode_roles(role_names):
    return base64.b64encode("\n".join(role_names).encode("utf-8")).decode("ascii")


class TestToolCreateMenu:
    def test_success_minimal(self, mock_flask_g, requests_mock):
        # 正常系: role_list指定済みの最小構成でメニュー作成が成功し、
        # APIレスポンスがそのままresultに入ること
        api_response = {"menu_create_id": "mc-1"}
        requests_mock.post(_create_url(), json=api_response, status_code=200)

        menu_definition = _menu_definition(menu_overrides={"role_list": ["role-a"]})
        result = menu_create_tool.tool_create_menu(
            {"menu_definition": menu_definition}, _payload()
        )

        assert result["result"] == api_response
        assert result["message"] == "Menu created successfully."
        assert result["organization_id"] == ORG_ID
        assert result["workspace_id"] == WS_ID

    def test_request_body_and_headers(self, mock_flask_g, requests_mock):
        # 正常系: 送信ボディにtype="create_new"、group={}、
        # menu.columnsが列名のリストとして含まれ、POSTなので
        # Content-Typeヘッダーが付与されること
        requests_mock.post(_create_url(), json={}, status_code=200)

        menu_definition = _menu_definition(
            menu_overrides={"role_list": ["role-a"]},
            column={"c1": {"column_class": "SingleTextColumn"}, "c2": {"column_class": "NumColumn"}},
        )
        menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        last_request = requests_mock.last_request
        sent_body = last_request.json()
        assert sent_body["type"] == "create_new"
        assert sent_body["group"] == {}
        assert sent_body["menu"]["columns"] == ["c1", "c2"]
        assert last_request.headers["Content-Type"] == "application/json"

    def test_sheet_type_id_default_is_1_and_adds_extra_fields(self, mock_flask_g, requests_mock):
        # 正常系: sheet_type_id未指定時はデフォルト"1"となり、
        # sheet_type及びhostgroup/vertical等の追加項目が設定されること
        requests_mock.post(_create_url(), json={}, status_code=200)

        menu_definition = _menu_definition(menu_overrides={"role_list": ["role-a"]})
        menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        sent_menu = requests_mock.last_request.json()["menu"]
        assert sent_menu["sheet_type_id"] == "1"
        assert sent_menu["sheet_type"] == "Parameter Sheet(Host/Operation)"
        assert sent_menu["hostgroup"] == "0"
        assert sent_menu["vertical"] == "0"
        assert sent_menu["menu_group_for_subst"] == "Substitution value"
        assert sent_menu["menu_group_for_ref"] == "Reference"

    def test_sheet_type_id_2_sets_data_sheet(self, mock_flask_g, requests_mock):
        # 正常系: sheet_type_id="2"の場合、sheet_type="Data Sheet"が設定され、
        # sheet_type_id=1の場合の追加項目(hostgroup等)は追加されないこと
        requests_mock.post(_create_url(), json={}, status_code=200)

        menu_definition = _menu_definition(
            menu_overrides={"role_list": ["role-a"], "sheet_type_id": "2"}
        )
        menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        sent_menu = requests_mock.last_request.json()["menu"]
        assert sent_menu["sheet_type"] == "Data Sheet"
        assert "menu_group_for_subst" not in sent_menu

    def test_sheet_type_id_3_sets_parameter_sheet_operation(self, mock_flask_g, requests_mock):
        # 正常系: sheet_type_id="3"の場合、sheet_type="Parameter
        # Sheet(Operation)"及びvertical/menu_group_for_subst/refが
        # 追加されるが、hostgroupは追加されないこと
        requests_mock.post(_create_url(), json={}, status_code=200)

        menu_definition = _menu_definition(
            menu_overrides={"role_list": ["role-a"], "sheet_type_id": "3"}
        )
        menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        sent_menu = requests_mock.last_request.json()["menu"]
        assert sent_menu["sheet_type"] == "Parameter Sheet(Operation)"
        assert sent_menu["vertical"] == "0"
        assert sent_menu["menu_group_for_subst"] == "Substitution value"
        # sheet_type_id="3"の分岐自体はhostgroupを追加しない(ここでの
        # hostgroupの値は_menu()ヘルパーがユーザー入力として与えたもの)
        assert sent_menu["hostgroup"] == "0"

    def test_sheet_type_id_unknown_sets_no_sheet_type(self, mock_flask_g, requests_mock):
        # 境界値: sheet_type_idが未知の値の場合、sheet_typeは設定されないこと
        requests_mock.post(_create_url(), json={}, status_code=200)

        menu_definition = _menu_definition(
            menu_overrides={"role_list": ["role-a"], "sheet_type_id": "99"}
        )
        menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        sent_menu = requests_mock.last_request.json()["menu"]
        assert "sheet_type" not in sent_menu

    def test_column_classes_all_variants(self, mock_flask_g, requests_mock):
        # 正常系: 各column_classに応じたcolumn_class_idおよび追加項目が
        # 設定されること
        requests_mock.post(_create_url(), json={}, status_code=200)

        column = {
            "c1": {"column_class": "SingleTextColumn"},
            "c2": {"column_class": "MultiTextColumn"},
            "c3": {"column_class": "NumColumn"},
            "c4": {"column_class": "FloatColumn"},
            "c5": {"column_class": "DateTimeColumn"},
            "c6": {"column_class": "DateColumn"},
            "c7": {"column_class": "IDColumn", "pulldown_selection": "Parameter sheet create:Selection 1:*-(blank)"},
            "c8": {"column_class": "PasswordColumn"},
            "c9": {"column_class": "FileUploadColumn"},
            "c10": {},
        }
        menu_definition = _menu_definition(
            menu_overrides={"role_list": ["role-a"]}, column=column
        )
        menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        sent_column = requests_mock.last_request.json()["column"]
        assert sent_column["c1"]["column_class_id"] == "1"
        assert sent_column["c1"]["single_string_maximum_bytes"] == "256"
        assert sent_column["c2"]["column_class_id"] == "2"
        assert sent_column["c2"]["multi_string_maximum_bytes"] == "4096"
        assert sent_column["c3"]["column_class_id"] == "3"
        assert sent_column["c3"]["integer_minimum_value"] == ""
        assert sent_column["c4"]["column_class_id"] == "4"
        assert sent_column["c4"]["decimal_digit"] == ""
        assert sent_column["c5"]["column_class_id"] == "5"
        assert sent_column["c5"]["datetime_default_value"] == ""
        assert sent_column["c6"]["column_class_id"] == "6"
        assert sent_column["c6"]["date_default_value"] == ""
        assert sent_column["c7"]["column_class_id"] == "7"
        assert sent_column["c7"]["pulldown_selection_id"] == "5011008"
        assert sent_column["c7"]["reference_item"] == ""
        assert sent_column["c8"]["column_class_id"] == "8"
        assert sent_column["c8"]["password_maximum_bytes"] == "1024"
        assert sent_column["c9"]["column_class_id"] == "9"
        assert sent_column["c9"]["file_upload_maximum_bytes"] == "1024000"
        # column_classが指定されていない場合はcolumn_class_idが付与されないこと
        assert "column_class_id" not in sent_column["c10"]
        # 共通デフォルト項目が付与されていること
        assert sent_column["c10"]["required"] == "0"
        assert sent_column["c10"]["unique"] == "0"

    def test_id_column_pulldown_selection_variants(self, mock_flask_g, requests_mock):
        # 境界値: pulldown_selectionの各値に応じてpulldown_selection_idが
        # 正しく解決され、未知の値の場合は空文字になること
        requests_mock.post(_create_url(), json={}, status_code=200)

        column = {
            "c1": {"column_class": "IDColumn", "pulldown_selection": "Parameter sheet create:Selection 2:Yes-No"},
            "c2": {"column_class": "IDColumn", "pulldown_selection": "Parameter sheet create:Selection 2:True-False"},
            "c3": {"column_class": "IDColumn"},
        }
        menu_definition = _menu_definition(
            menu_overrides={"role_list": ["role-a"]}, column=column
        )
        menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        sent_column = requests_mock.last_request.json()["column"]
        assert sent_column["c1"]["pulldown_selection_id"] == "5011009"
        assert sent_column["c2"]["pulldown_selection_id"] == "5011010"
        assert sent_column["c3"]["pulldown_selection_id"] == ""

    def test_column_order_sorted_by_c_prefixed_numeric_key(self, mock_flask_g, requests_mock):
        # 正常系: column dictの並び順が、"c"+数字のキーは数値順、それ以外は
        # 文字列順でその後に配置されるよう並べ替えられること。かつ
        # display_orderが並べ替え後の順に0から連番で振られること
        requests_mock.post(_create_url(), json={}, status_code=200)

        column = {
            "extra": {},
            "c10": {},
            "c2": {},
            "c1": {},
        }
        menu_definition = _menu_definition(
            menu_overrides={"role_list": ["role-a"]}, column=column
        )
        menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        sent_column = requests_mock.last_request.json()["column"]
        assert list(sent_column.keys()) == ["c1", "c2", "c10", "extra"]
        assert sent_column["c1"]["display_order"] == 0
        assert sent_column["c2"]["display_order"] == 1
        assert sent_column["c10"]["display_order"] == 2
        assert sent_column["extra"]["display_order"] == 3

    def test_menu_columns_field_uses_original_unsorted_keys(self, mock_flask_g, requests_mock):
        # 境界値: menu.columnsは並び替え前の元のcolumn dictのキー順で
        # 設定されること
        requests_mock.post(_create_url(), json={}, status_code=200)

        column = {"extra": {}, "c10": {}, "c2": {}}
        menu_definition = _menu_definition(
            menu_overrides={"role_list": ["role-a"]}, column=column
        )
        menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        sent_menu = requests_mock.last_request.json()["menu"]
        assert sent_menu["columns"] == ["extra", "c10", "c2"]

    def test_menu_definition_missing_column_defaults_empty(self, mock_flask_g, requests_mock):
        # 境界値: menu_definitionにcolumnが無い場合でも空のcolumnとして
        # 処理が完了すること
        requests_mock.post(_create_url(), json={}, status_code=200)

        menu_definition = {"menu": _menu({"role_list": ["role-a"]})}
        menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        sent_body = requests_mock.last_request.json()
        assert sent_body["column"] == {}
        assert sent_body["menu"]["columns"] == []

    def test_menu_definition_not_a_dict_raises(self, mock_flask_g):
        # 異常系: menu_definitionがdict以外の場合は例外が発生すること
        with pytest.raises(Exception, match="menu_definition must be an object"):
            menu_create_tool.tool_create_menu({"menu_definition": "not-a-dict"}, _payload())

    def test_menu_definition_missing_defaults_empty_dict(self, mock_flask_g, requests_mock):
        # 境界値: argumentsにmenu_definition自体が無い場合、空dictとして
        # 扱われ、role_listは自動解決処理が呼ばれること(admin roleのみ)
        requests_mock.post(_create_url(), json={}, status_code=200)
        requests_mock.get(_platform_roles_url(), json={"data": []}, status_code=200)

        result = menu_create_tool.tool_create_menu({}, _payload())

        sent_body = requests_mock.last_request.json()
        assert sent_body["menu"]["role_list"] == ["_{}-admin".format(WS_ID)]
        assert result["message"] == "Menu created successfully."

    def test_role_list_auto_resolved_when_missing(self, app, requests_mock):
        # 正常系: role_list未指定の場合、Exastro PlatformのAPIから取得した
        # ロール一覧のうち、呼び出しユーザーが持ち、かつこのworkspace_idに
        # アクセス可能なロールが採用され、admin roleが自動的に追加されること
        requests_mock.post(_create_url(), json={}, status_code=200)
        roles_data = {
            "data": [
                {"name": "role-a", "workspaces": [{"id": WS_ID}]},
                {"name": "role-b", "workspaces": [{"id": "other-ws"}]},
                {"name": "role-c", "workspaces": [{"id": WS_ID}]},
            ]
        }
        requests_mock.get(_platform_roles_url(), json=roles_data, status_code=200)

        from unittest import mock
        with app.test_request_context(headers={"Roles": _encode_roles(["role-a", "role-b"])}):
            g.applogger = mock.Mock()
            g.applogger.info = mock.Mock()
            g.LANGUAGE = "en"

            menu_definition = _menu_definition()
            menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        sent_body = requests_mock.last_request.json()
        assert sent_body["menu"]["role_list"] == ["role-a", "_{}-admin".format(WS_ID)]

    def test_http_error_raises_http_exception(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが
        # 発生し、tool_nameが"create-menu"になること
        requests_mock.post(
            _create_url(), json={"message": "invalid definition", "result": "NG"}, status_code=400
        )

        menu_definition = _menu_definition(menu_overrides={"role_list": ["role-a"]})
        with pytest.raises(HTTPException) as exc_info:
            menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        assert exc_info.value.status_code == 400
        assert exc_info.value.tool_name == "create-menu"
        assert str(exc_info.value) == "invalid definition (NG)"

    def test_http_error_without_json_body(self, mock_flask_g, requests_mock):
        # 異常系: レスポンスボディがJSONとして解釈できない場合でも例外が発生し、
        # tool_nameとstatus_codeからメッセージが組み立てられること
        requests_mock.post(_create_url(), text="server error", status_code=500)

        menu_definition = _menu_definition(menu_overrides={"role_list": ["role-a"]})
        with pytest.raises(HTTPException) as exc_info:
            menu_create_tool.tool_create_menu({"menu_definition": menu_definition}, _payload())

        assert exc_info.value.status_code == 500
        assert str(exc_info.value) == "create-menu failed: HTTP 500"


class TestToolUpdateMenu:
    def test_success(self, mock_flask_g, requests_mock):
        # 正常系: role_list指定済みでメニュー更新が成功し、type="edit"が
        # 送信され、message="Menu updated successfully."が返ること
        api_response = {"menu_create_id": "mc-1", "updated": True}
        requests_mock.post(_create_url(), json=api_response, status_code=200)

        menu_definition = _menu_definition(
            menu_overrides={"menu_create_id": "mc-1", "role_list": ["role-a", "role-b"]}
        )
        result = menu_create_tool.tool_update_menu(
            {"menu_definition": menu_definition}, _payload()
        )

        assert result["result"] == api_response
        assert result["message"] == "Menu updated successfully."
        sent_body = requests_mock.last_request.json()
        assert sent_body["type"] == "edit"

    def test_provided_role_list_not_auto_modified(self, mock_flask_g, requests_mock):
        # 正常系: update-menuではrole_listが指定されている場合、
        # 自動解決処理(admin role追加等)は行われず、そのまま送信されること
        requests_mock.post(_create_url(), json={}, status_code=200)

        menu_definition = _menu_definition(
            menu_overrides={"menu_create_id": "mc-1", "role_list": ["role-only"]}
        )
        menu_create_tool.tool_update_menu({"menu_definition": menu_definition}, _payload())

        sent_body = requests_mock.last_request.json()
        assert sent_body["menu"]["role_list"] == ["role-only"]

    def test_missing_role_list_raises(self, mock_flask_g):
        # 異常系: update-menuでrole_listが指定されていない場合は例外が
        # 発生すること
        menu_definition = _menu_definition(menu_overrides={"menu_create_id": "mc-1"})
        with pytest.raises(
            Exception, match="menu_definition.menu.role_list is required for update-menu"
        ):
            menu_create_tool.tool_update_menu({"menu_definition": menu_definition}, _payload())

    def test_empty_role_list_raises(self, mock_flask_g):
        # 境界値: role_listが空リストの場合も未指定と同様に例外が発生すること
        menu_definition = _menu_definition(
            menu_overrides={"menu_create_id": "mc-1", "role_list": []}
        )
        with pytest.raises(Exception, match="role_list is required for update-menu"):
            menu_create_tool.tool_update_menu({"menu_definition": menu_definition}, _payload())

    def test_http_error_raises_with_update_menu_tool_name(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionの
        # tool_nameが"update-menu"になること
        requests_mock.post(_create_url(), json={"message": "not found"}, status_code=404)

        menu_definition = _menu_definition(
            menu_overrides={"menu_create_id": "mc-1", "role_list": ["role-a"]}
        )
        with pytest.raises(HTTPException) as exc_info:
            menu_create_tool.tool_update_menu({"menu_definition": menu_definition}, _payload())

        assert exc_info.value.tool_name == "update-menu"
        assert exc_info.value.status_code == 404
        assert str(exc_info.value) == "not found"


class TestDecodeRolesHeader:
    def test_no_header_returns_empty_list(self, app):
        # 境界値: Rolesヘッダーが無い場合は空リストを返すこと
        with app.test_request_context():
            assert menu_create_tool._decode_roles_header() == []

    def test_valid_header_decodes_and_filters_empty_entries(self, app):
        # 正常系: base64エンコードされた改行区切りのロール一覧が正しく
        # デコードされ、空文字のエントリは除外されること
        header_value = _encode_roles(["role-a", "role-b", ""])
        with app.test_request_context(headers={"Roles": header_value}):
            assert menu_create_tool._decode_roles_header() == ["role-a", "role-b"]

    def test_invalid_base64_returns_empty_list(self, app):
        # 異常系: base64デコードに失敗する値が指定された場合は空リストを
        # 返すこと(例外を伝播させない)
        with app.test_request_context(headers={"Roles": "!!!not-valid-base64!!!"}):
            assert menu_create_tool._decode_roles_header() == []


class TestResolveDefaultRoleList:
    def test_filters_by_user_roles_and_workspace_and_appends_admin(self, app, requests_mock):
        # 正常系: ユーザーが保持し、かつ対象workspace_idにアクセス可能な
        # ロールのみが採用され、admin roleが末尾に追加されること
        roles_data = {
            "data": [
                {"name": "role-a", "workspaces": [{"id": WS_ID}]},
                {"name": "role-b", "workspaces": [{"id": "other-ws"}]},
                {"name": "role-c", "workspaces": [{"id": WS_ID}]},
                {"name": "role-d", "workspaces": [{"id": WS_ID}]},
            ]
        }
        requests_mock.get(_platform_roles_url(), json=roles_data, status_code=200)

        from unittest import mock
        with app.test_request_context(headers={"Roles": _encode_roles(["role-a", "role-c"])}):
            g.applogger = mock.Mock()
            g.applogger.info = mock.Mock()
            g.LANGUAGE = "en"

            result = menu_create_tool._resolve_default_role_list(ORG_ID, WS_ID)

        assert result == ["role-a", "role-c", "_{}-admin".format(WS_ID)]

    def test_admin_role_already_present_not_duplicated(self, app, requests_mock):
        # 境界値: 取得したロールに既にadmin roleが含まれている場合は
        # 重複して追加されないこと
        admin_role = "_{}-admin".format(WS_ID)
        roles_data = {"data": [{"name": admin_role, "workspaces": [{"id": WS_ID}]}]}
        requests_mock.get(_platform_roles_url(), json=roles_data, status_code=200)

        from unittest import mock
        with app.test_request_context(headers={"Roles": _encode_roles([admin_role])}):
            g.applogger = mock.Mock()
            g.applogger.info = mock.Mock()
            g.LANGUAGE = "en"

            result = menu_create_tool._resolve_default_role_list(ORG_ID, WS_ID)

        assert result == [admin_role]
        assert result.count(admin_role) == 1

    def test_missing_data_key_defaults_to_empty_list(self, mock_flask_g, requests_mock):
        # 境界値: レスポンスにdataキーが無い場合でも空リストとして扱われ、
        # admin roleのみが返されること
        requests_mock.get(_platform_roles_url(), json={}, status_code=200)

        result = menu_create_tool._resolve_default_role_list(ORG_ID, WS_ID)

        assert result == ["_{}-admin".format(WS_ID)]

    def test_role_without_workspaces_key_is_excluded(self, app, requests_mock):
        # 境界値: roleにworkspacesキーが無い場合は対象workspace_idに
        # アクセス不可として除外されること
        roles_data = {"data": [{"name": "role-a"}]}
        requests_mock.get(_platform_roles_url(), json=roles_data, status_code=200)

        from unittest import mock
        with app.test_request_context(headers={"Roles": _encode_roles(["role-a"])}):
            g.applogger = mock.Mock()
            g.applogger.info = mock.Mock()
            g.LANGUAGE = "en"

            result = menu_create_tool._resolve_default_role_list(ORG_ID, WS_ID)

        assert result == ["_{}-admin".format(WS_ID)]

    def test_role_without_name_is_excluded(self, mock_flask_g, requests_mock):
        # 境界値: roleにnameキーが無い場合は除外されること
        roles_data = {"data": [{"workspaces": [{"id": WS_ID}]}]}
        requests_mock.get(_platform_roles_url(), json=roles_data, status_code=200)

        result = menu_create_tool._resolve_default_role_list(ORG_ID, WS_ID)

        assert result == ["_{}-admin".format(WS_ID)]

    def test_query_params_and_no_content_type_header(self, mock_flask_g, requests_mock):
        # 正常系: GETリクエストにkind=workspaceがクエリパラメータとして
        # 渡され、Content-Typeヘッダーは付与されないこと
        requests_mock.get(_platform_roles_url(), json={"data": []}, status_code=200)

        menu_create_tool._resolve_default_role_list(ORG_ID, WS_ID)

        last_request = requests_mock.last_request
        assert last_request.qs.get("kind") == ["workspace"]
        assert "Content-Type" not in last_request.headers

    def test_http_error_raises_http_exception(self, mock_flask_g, requests_mock):
        # 異常系: Exastro PlatformのAPIが200以外を返した場合、
        # HTTPExceptionが発生し、tool_nameが"create-menu"になること
        requests_mock.get(
            _platform_roles_url(), json={"message": "forbidden", "result": "NG"}, status_code=403
        )

        with pytest.raises(HTTPException) as exc_info:
            menu_create_tool._resolve_default_role_list(ORG_ID, WS_ID)

        assert exc_info.value.status_code == 403
        assert exc_info.value.tool_name == "create-menu"
        assert str(exc_info.value) == "forbidden (NG)"


class TestColumnDictKeySort:
    def test_c_prefixed_numeric_keys_sorted_numerically(self):
        # 正常系: "c"+数字のキーは数値としての順序でソートされること
        items = [("c10", None), ("c2", None), ("c1", None)]
        sorted_items = sorted(items, key=menu_create_tool._column_dict_key_sort)
        assert [k for k, _ in sorted_items] == ["c1", "c2", "c10"]

    def test_non_c_keys_sorted_after_c_keys(self):
        # 正常系: "c"+数字以外のキーは、"c"+数字のキーより後に配置されること
        items = [("extra", None), ("c1", None), ("another", None)]
        sorted_items = sorted(items, key=menu_create_tool._column_dict_key_sort)
        assert [k for k, _ in sorted_items] == ["c1", "another", "extra"]

    def test_key_with_c_prefix_non_digit_treated_as_non_c_key(self):
        # 境界値: "c"に続く部分が数字でない場合は"c"+数字のキーとして
        # 扱われないこと
        assert menu_create_tool._column_dict_key_sort(("cabc", None)) == (1, "cabc")
        assert menu_create_tool._column_dict_key_sort(("c1", None)) == (0, 1)


class TestToolGetMenuDefinition:
    def test_missing_menu_rest_name_raises(self, mock_flask_g):
        # 異常系: menu_rest_nameが指定されていない場合は例外が発生すること
        with pytest.raises(Exception, match="menu_rest_name is required"):
            menu_create_tool.tool_get_menu_definition({}, _payload())

    def test_empty_menu_rest_name_raises(self, mock_flask_g):
        # 境界値: menu_rest_nameが空文字の場合も未指定と同様に例外が
        # 発生すること
        with pytest.raises(Exception, match="menu_rest_name is required"):
            menu_create_tool.tool_get_menu_definition({"menu_rest_name": ""}, _payload())

    def test_success_returns_menu_and_column_and_removes_columns_field(
        self, mock_flask_g, requests_mock
    ):
        # 正常系: 取得したmenu_info.menu/columnがそのまま返され、
        # menu内のcolumns項目(内部項目)が取り除かれること
        menu_rest_name = "menu1"
        api_response = {
            "data": {
                "menu_info": {
                    "menu": {
                        "menu_name": "Menu1",
                        "menu_name_rest": menu_rest_name,
                        "columns": ["c1", "c2"],
                    },
                    "column": {"c1": {"column_class": "SingleTextColumn"}},
                }
            }
        }
        requests_mock.get(_get_menu_definition_url(menu_rest_name), json=api_response, status_code=200)

        result = menu_create_tool.tool_get_menu_definition(
            {"menu_rest_name": menu_rest_name}, _payload()
        )

        assert result["message"] == "Menu definition fetched successfully."
        assert result["organization_id"] == ORG_ID
        assert result["workspace_id"] == WS_ID
        menu_definition = result["result"]["menu_definition"]
        assert "columns" not in menu_definition["menu"]
        assert menu_definition["menu"]["menu_name_rest"] == menu_rest_name
        assert menu_definition["column"] == {"c1": {"column_class": "SingleTextColumn"}}

    def test_success_missing_menu_info_defaults_to_empty_dicts(self, mock_flask_g, requests_mock):
        # 境界値: レスポンスにmenu_info自体が無い場合でも、menu/columnは
        # 空dictとして返されること
        menu_rest_name = "menu2"
        requests_mock.get(_get_menu_definition_url(menu_rest_name), json={"data": {}}, status_code=200)

        result = menu_create_tool.tool_get_menu_definition(
            {"menu_rest_name": menu_rest_name}, _payload()
        )

        menu_definition = result["result"]["menu_definition"]
        assert menu_definition["menu"] == {}
        assert menu_definition["column"] == {}

    def test_request_url_and_no_content_type_header(self, mock_flask_g, requests_mock):
        # 正常系: 呼び出し先URLがmenu_rest_nameを含めて正しく組み立てられ、
        # GETなのでContent-Typeヘッダーは付与されないこと
        menu_rest_name = "menu3"
        requests_mock.get(_get_menu_definition_url(menu_rest_name), json={"data": {}}, status_code=200)

        menu_create_tool.tool_get_menu_definition({"menu_rest_name": menu_rest_name}, _payload())

        last_request = requests_mock.last_request
        assert last_request.url == _get_menu_definition_url(menu_rest_name)
        assert last_request.method == "GET"
        assert "Content-Type" not in last_request.headers

    def test_http_error_raises_http_exception(self, mock_flask_g, requests_mock):
        # 異常系: ダウンストリームAPIが200以外を返した場合、HTTPExceptionが
        # 発生し、tool_nameが"get-menu-definition"になること
        menu_rest_name = "menu4"
        requests_mock.get(
            _get_menu_definition_url(menu_rest_name),
            json={"message": "not found", "result": "NG"},
            status_code=404,
        )

        with pytest.raises(HTTPException) as exc_info:
            menu_create_tool.tool_get_menu_definition(
                {"menu_rest_name": menu_rest_name}, _payload()
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.tool_name == "get-menu-definition"
        assert str(exc_info.value) == "not found (NG)"

    def test_http_error_without_json_body(self, mock_flask_g, requests_mock):
        # 異常系: レスポンスボディがJSONとして解釈できない場合でも例外が
        # 発生し、tool_nameとstatus_codeからメッセージが組み立てられること
        menu_rest_name = "menu5"
        requests_mock.get(_get_menu_definition_url(menu_rest_name), text="boom", status_code=503)

        with pytest.raises(HTTPException) as exc_info:
            menu_create_tool.tool_get_menu_definition(
                {"menu_rest_name": menu_rest_name}, _payload()
            )

        assert exc_info.value.status_code == 503
        assert str(exc_info.value) == "get-menu-definition failed: HTTP 503"
