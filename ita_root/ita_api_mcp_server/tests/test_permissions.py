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
libs/permissions.py (is_tool_in_profile / has_role / is_tool_visible /
check_tool_call_permission) のユニットテスト

ITAのメニュー一覧API(/ita/user/menus/)呼び出しはrequests_mockでモックする。
異常系では、g.applogger.info/.error の呼び出し回数はチェックしない。
"""
import base64
from unittest import mock

import pytest
import requests
from flask import g

import tools  # noqa: F401  実際のTOOL_REGISTRYを登録するためimportする
from libs import load_dynamic_tools
from libs.permissions import (
    check_tool_call_permission,
    has_role,
    is_tool_in_profile,
    is_tool_visible,
)

ORG_ID = "org1"
WS_ID = "ws1"


def _encode_roles(roles):
    return base64.b64encode("\n".join(roles).encode("utf-8")).decode("ascii")


def _set_g_mocks():
    g.applogger = mock.Mock()
    g.applogger.info = mock.Mock()
    g.applogger.error = mock.Mock()
    g.applogger.debug = mock.Mock()


class TestIsToolInProfile:
    def test_no_query_profile_means_no_filtering(self):
        # profile未指定(None・空文字)の場合は絞り込みを行わず常にTrue
        assert is_tool_in_profile({"profile": ["LLMEditor"]}, None) is True
        assert is_tool_in_profile({"profile": ["LLMEditor"]}, "") is True

    def test_tool_without_profile_is_available_under_any_profile(self):
        # ツール側のprofileが未指定(None/キー無し/空リスト)の場合は
        # 絞り込み対象外として、どのprofileを指定しても常にTrue
        assert is_tool_in_profile({"profile": None}, "LLMEditor") is True
        assert is_tool_in_profile({}, "AnyProfile") is True
        assert is_tool_in_profile({"profile": []}, "AnyProfile") is True

    def test_single_string_profile_match(self):
        # 正常系: ツール側profileが文字列1つの場合、同じ値のprofileと一致すればTrue
        assert is_tool_in_profile({"profile": "LLMEditor"}, "LLMEditor") is True

    def test_single_string_profile_mismatch(self):
        # 異常系: ツール側profileが文字列1つの場合、異なる値のprofileならFalse
        assert is_tool_in_profile({"profile": "LLMEditor"}, "AgenticAI") is False

    def test_list_profile_matches_any_entry(self):
        # 正常系: ツール側profileがリストの場合、リスト内のいずれか1つと
        # 一致すればTrue(AgenticAI/LLMEditorのどちらでも一致する)
        tool = {"profile": ["AgenticAI", "LLMEditor"]}
        assert is_tool_in_profile(tool, "AgenticAI") is True
        assert is_tool_in_profile(tool, "LLMEditor") is True

    def test_list_profile_no_match_returns_false(self):
        # 異常系: ツール側profileがリストの場合、リストのいずれにも
        # 含まれないprofileを指定するとFalse
        tool = {"profile": ["AgenticAI", "LLMEditor"]}
        assert is_tool_in_profile(tool, "Unknown") is False

    def test_real_registry_matches_llm_editor_reference_table(self):
        # ユーザー提示の「LLMエディタ用ツール一覧」表の○ツールと一致することを
        # 回帰確認する(将来ツールを追加・変更した際に一覧がずれたら検知する)
        expected_llm_editor_tools = {
            "list-accessible-menus",
            "list-menu-info",
            "list-menu-info-pulldown",
            "menu-filter",
            "menu-filter-count",
            "get-driver-status",
            "get-attachment-text-file",
            "base64-encode",
            "base64-decode",
            "search-docs",
            "get-document",
        }
        all_tools = load_dynamic_tools()
        all_names = {t["name"] for t in all_tools}

        assert {t["name"] for t in all_tools if is_tool_in_profile(t, "LLMEditor")} == expected_llm_editor_tools
        # profile未指定 / "AgenticAI" は絞り込み無し(=登録済み全ツール)であること
        assert {t["name"] for t in all_tools if is_tool_in_profile(t, None)} == all_names
        assert {t["name"] for t in all_tools if is_tool_in_profile(t, "AgenticAI")} == all_names


class TestHasRole:
    def test_no_required_roles_returns_false(self, app):
        # 境界値: required_rolesが未指定(None)・空リストの場合は、
        # ユーザーのロールに関わらず常にFalse
        with app.test_request_context("/", headers={"Role-Detail": _encode_roles(["_og-usr-mt"])}):
            assert has_role(None) is False
            assert has_role([]) is False

    def test_matches_exact_role(self, app):
        # 正常系: required_rolesを文字列1つで指定した場合、Role-Detailの
        # ロール一覧に完全一致するロールがあればTrue
        with app.test_request_context(
            "/", headers={"Role-Detail": _encode_roles(["_og-usr-mt", "_ws-role-x"])}
        ):
            assert has_role("_og-usr-mt") is True

    def test_matches_regex_role(self, app):
        # 正常系: required_rolesの各要素は正規表現として扱われ、
        # ユーザーのロールがそのパターンにマッチすればTrue
        with app.test_request_context("/", headers={"Role-Detail": _encode_roles(["mcp-org-manager"])}):
            assert has_role(["mcp-admin", "mcp-.*-manager"]) is True

    def test_no_match_returns_false(self, app):
        # 異常系: ユーザーのロールがrequired_rolesのいずれにも
        # マッチしない場合はFalse
        with app.test_request_context("/", headers={"Role-Detail": _encode_roles(["some-other-role"])}):
            assert has_role(["mcp-admin"]) is False

    def test_missing_header_returns_false(self, app):
        # 異常系: Role-Detailヘッダーが無い場合はロール無しとして扱われ、Falseとなる
        with app.test_request_context("/"):
            assert has_role(["mcp-admin"]) is False

    def test_invalid_base64_header_returns_false(self, app):
        # 異常系: Role-Detailヘッダーが不正なBase64値の場合もロール無しとして扱われ、
        # Falseとなる(安全側に倒す)
        with app.test_request_context("/", headers={"Role-Detail": "not-valid-base64!!"}):
            assert has_role(["mcp-admin"]) is False


class TestIsToolVisible:
    def test_no_restriction_is_always_visible(self, app):
        # 正常系: required_roles・required_menuのいずれも未指定の場合は
        # 権限チェック無しとして常にTrue
        with app.test_request_context("/"):
            tool = {"required_roles": None, "required_menu": None}
            assert is_tool_visible(tool, {}) is True

    def test_required_roles_visible_when_role_matches(self, app):
        # 正常系: required_rolesが指定されたツールは、Role-Detailに
        # マッチするロールがあればTrue(has_roleの判定に委譲される)
        tool = {"required_roles": ["mcp-admin"], "required_menu": None}
        with app.test_request_context("/", headers={"Role-Detail": _encode_roles(["mcp-admin"])}):
            assert is_tool_visible(tool, {}) is True

    def test_required_roles_not_visible_when_role_does_not_match(self, app):
        # 異常系: required_rolesが指定されたツールは、Role-Detailに
        # マッチするロールが無ければFalse
        tool = {"required_roles": ["mcp-admin"], "required_menu": None}
        with app.test_request_context("/", headers={"Role-Detail": _encode_roles(["other-role"])}):
            assert is_tool_visible(tool, {}) is False

    def test_required_menu_visible_when_menu_present(self, app, requests_mock, monkeypatch):
        # 正常系: required_menuが指定されたツールは、ITAのメニュー一覧APIの
        # レスポンスに対象のmenu_name_restが含まれていればTrue
        monkeypatch.setenv("ITA_API_ORAGANIZATION_HOST", "ita-api-organization")
        monkeypatch.setenv("ITA_API_ORAGANIZATION_PORT", "8080")
        url = "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/user/menus/".format(ORG_ID, WS_ID)
        requests_mock.get(
            url,
            json={"data": {"menu_groups": [{"menus": [{"menu_name_rest": "operation_status"}]}]}},
            status_code=200,
        )
        tool = {"required_roles": None, "required_menu": ["operation_status"]}

        with app.test_request_context("/"):
            _set_g_mocks()
            assert is_tool_visible(tool, {"organization_id": ORG_ID, "workspace_id": WS_ID}) is True

    def test_required_menu_not_visible_when_menu_absent(self, app, requests_mock, monkeypatch):
        # 異常系: ITAのメニュー一覧APIのレスポンスに対象のmenu_name_restが
        # 含まれていない場合はFalse
        monkeypatch.setenv("ITA_API_ORAGANIZATION_HOST", "ita-api-organization")
        monkeypatch.setenv("ITA_API_ORAGANIZATION_PORT", "8080")
        url = "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/user/menus/".format(ORG_ID, WS_ID)
        requests_mock.get(
            url,
            json={"data": {"menu_groups": [{"menus": [{"menu_name_rest": "other_menu"}]}]}},
            status_code=200,
        )
        tool = {"required_roles": None, "required_menu": ["operation_status"]}

        with app.test_request_context("/"):
            _set_g_mocks()
            assert is_tool_visible(tool, {"organization_id": ORG_ID, "workspace_id": WS_ID}) is False

    def test_required_menu_api_failure_fails_closed(self, app, requests_mock, monkeypatch):
        # メニュー一覧APIが異常応答の場合、安全側に倒して非表示(False)とする
        monkeypatch.setenv("ITA_API_ORAGANIZATION_HOST", "ita-api-organization")
        monkeypatch.setenv("ITA_API_ORAGANIZATION_PORT", "8080")
        url = "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/user/menus/".format(ORG_ID, WS_ID)
        requests_mock.get(url, status_code=500, text="internal error")
        tool = {"required_roles": None, "required_menu": ["operation_status"]}

        with app.test_request_context("/"):
            _set_g_mocks()
            assert is_tool_visible(tool, {"organization_id": ORG_ID, "workspace_id": WS_ID}) is False

    def test_required_menu_reuses_cache_within_single_call(self, app, requests_mock, monkeypatch):
        # 同一organization_id/workspace_idであれば、menu_cacheにより
        # メニュー一覧APIが複数回呼ばれないこと
        monkeypatch.setenv("ITA_API_ORAGANIZATION_HOST", "ita-api-organization")
        monkeypatch.setenv("ITA_API_ORAGANIZATION_PORT", "8080")
        url = "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/user/menus/".format(ORG_ID, WS_ID)
        mocked = requests_mock.get(
            url,
            json={"data": {"menu_groups": [{"menus": [{"menu_name_rest": "operation_status"}]}]}},
            status_code=200,
        )
        tool = {"required_roles": None, "required_menu": ["operation_status"]}
        payload = {"organization_id": ORG_ID, "workspace_id": WS_ID}
        cache = {}

        with app.test_request_context("/"):
            _set_g_mocks()
            is_tool_visible(tool, payload, cache)
            is_tool_visible(tool, payload, cache)

        assert mocked.call_count == 1

    def test_required_menu_connection_error_fails_closed(self, app, requests_mock, monkeypatch):
        # ITAのメニュー一覧APIへの接続自体が失敗した場合も、安全側に倒して非表示(False)とする
        monkeypatch.setenv("ITA_API_ORAGANIZATION_HOST", "ita-api-organization")
        monkeypatch.setenv("ITA_API_ORAGANIZATION_PORT", "8080")
        url = "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/user/menus/".format(ORG_ID, WS_ID)
        requests_mock.get(url, exc=requests.exceptions.ConnectionError("connection refused"))
        tool = {"required_roles": None, "required_menu": ["operation_status"]}

        with app.test_request_context("/"):
            _set_g_mocks()
            assert is_tool_visible(tool, {"organization_id": ORG_ID, "workspace_id": WS_ID}) is False

    def test_required_menu_invalid_json_response_fails_closed(self, app, requests_mock, monkeypatch):
        # メニュー一覧APIがステータス200だがJSONとして解釈できない応答を返した場合も
        # 安全側に倒して非表示(False)とする
        monkeypatch.setenv("ITA_API_ORAGANIZATION_HOST", "ita-api-organization")
        monkeypatch.setenv("ITA_API_ORAGANIZATION_PORT", "8080")
        url = "http://ita-api-organization:8080/api/{}/workspaces/{}/ita/user/menus/".format(ORG_ID, WS_ID)
        requests_mock.get(url, status_code=200, text="not-json", headers={"Content-Type": "text/plain"})
        tool = {"required_roles": None, "required_menu": ["operation_status"]}

        with app.test_request_context("/"):
            _set_g_mocks()
            assert is_tool_visible(tool, {"organization_id": ORG_ID, "workspace_id": WS_ID}) is False


class TestCheckToolCallPermission:
    def test_no_required_roles_does_not_raise(self, app):
        # 正常系: required_rolesが未指定の場合は権限チェック無しとして
        # 例外を発生させない
        with app.test_request_context("/"):
            _set_g_mocks()
            check_tool_call_permission({"name": "some-tool", "required_roles": None})

    def test_required_roles_satisfied_does_not_raise(self, app):
        # 正常系: required_rolesが指定されていても、Role-Detailに
        # マッチするロールがあれば例外を発生させない
        with app.test_request_context("/", headers={"Role-Detail": _encode_roles(["mcp-admin"])}):
            _set_g_mocks()
            check_tool_call_permission({"name": "some-tool", "required_roles": ["mcp-admin"]})

    def test_required_roles_not_satisfied_raises(self, app):
        # 異常系: required_rolesが指定されていて、Role-Detailに
        # マッチするロールが無い場合は「Permission denied」を含む例外が発生すること
        # (必要なロール名などの詳細はメッセージに含まれない)
        with app.test_request_context("/", headers={"Role-Detail": _encode_roles(["other-role"])}):
            _set_g_mocks()
            with pytest.raises(Exception, match="Permission denied"):
                check_tool_call_permission({"name": "some-tool", "required_roles": ["mcp-admin"]})
