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
api.py の "tools/list" 関連処理(handle_tools_list / jsonrpc_handlerの
profileクエリー文字列の取り扱い)のユニットテスト

handle_tools_list のテストでは、load_dynamic_tools / is_tool_visible を
mocker.patchで置き換え、実際のTOOL_REGISTRY・ITAメニューAPI呼び出しには
依存しない架空のツール一覧で、enabled/profile/is_tool_visibleの組み合わせによる
絞り込みロジックのみを検証する。

jsonrpc_handler のテストでは、before_request_handler(DB接続を伴う共通処理)を
経由せず、attachment_file.py の既存テストと同様にビューア関数を直接呼び出し、
リクエストコンテキストのg属性を手動で設定する。
"""
from unittest import mock

import pytest
from flask import g

import api

ORG_ID = "org1"
WS_ID = "ws1"

FAKE_TOOLS = [
    {"name": "a", "description": "A", "inputSchema": {"type": "object"}, "enabled": True, "profile": ["AgenticAI"]},
    {"name": "b", "description": "B", "inputSchema": {"type": "object"}, "enabled": True, "profile": ["LLMEditor"]},
    {"name": "c", "description": "C", "inputSchema": {"type": "object"}, "enabled": False, "profile": None},
    {"name": "d", "description": "D", "inputSchema": {"type": "object"}, "enabled": True, "profile": None},
]


def _set_g_mocks():
    g.applogger = mock.Mock()
    g.applogger.info = mock.Mock()
    g.applogger.error = mock.Mock()
    g.applogger.debug = mock.Mock()


class TestHandleToolsList:
    def test_no_profile_returns_all_enabled_visible_tools(self, mock_flask_g, mocker):
        # profile未指定: 絞り込みなし。disabled(c)のみ除外される
        mocker.patch("api.load_dynamic_tools", return_value=FAKE_TOOLS)
        mocker.patch("api.is_tool_visible", return_value=True)

        result = api.handle_tools_list({}, {"organization_id": ORG_ID, "workspace_id": WS_ID})

        assert [t["name"] for t in result["tools"]] == ["a", "b", "d"]

    def test_profile_agenticai_filters_by_tool_profile(self, mock_flask_g, mocker):
        # 正常系: profile="AgenticAI"の場合、ツール側profileに"AgenticAI"を
        # 含むもの(a)と、profile未指定で絞り込み対象外のもの(d)が返ること
        # (b は profile=["LLMEditor"]なので不一致で除外される)
        mocker.patch("api.load_dynamic_tools", return_value=FAKE_TOOLS)
        mocker.patch("api.is_tool_visible", return_value=True)

        result = api.handle_tools_list({}, {"profile": "AgenticAI"})

        assert [t["name"] for t in result["tools"]] == ["a", "d"]

    def test_profile_llmeditor_filters_by_tool_profile(self, mock_flask_g, mocker):
        # 正常系: profile="LLMEditor"の場合、ツール側profileに"LLMEditor"を
        # 含むもの(b)と、profile未指定で絞り込み対象外のもの(d)が返ること
        mocker.patch("api.load_dynamic_tools", return_value=FAKE_TOOLS)
        mocker.patch("api.is_tool_visible", return_value=True)

        result = api.handle_tools_list({}, {"profile": "LLMEditor"})

        assert [t["name"] for t in result["tools"]] == ["b", "d"]

    def test_unknown_profile_only_returns_tools_without_profile_restriction(self, mock_flask_g, mocker):
        # 境界値: どのツールのprofileにも含まれない値を指定した場合、
        # profile未指定で絞り込み対象外のツール(d)のみが返ること
        mocker.patch("api.load_dynamic_tools", return_value=FAKE_TOOLS)
        mocker.patch("api.is_tool_visible", return_value=True)

        result = api.handle_tools_list({}, {"profile": "SomeOtherProfile"})

        assert [t["name"] for t in result["tools"]] == ["d"]

    def test_disabled_tool_excluded_even_when_profile_matches(self, mock_flask_g, mocker):
        # 異常系: enabled=Falseのツールは、profileが一致していても
        # 結果に含まれないこと
        tools_with_disabled_llm_tool = FAKE_TOOLS + [
            {"name": "e", "description": "E", "inputSchema": {}, "enabled": False, "profile": ["LLMEditor"]}
        ]
        mocker.patch("api.load_dynamic_tools", return_value=tools_with_disabled_llm_tool)
        mocker.patch("api.is_tool_visible", return_value=True)

        result = api.handle_tools_list({}, {"profile": "LLMEditor"})

        assert "e" not in [t["name"] for t in result["tools"]]

    def test_permission_restricted_tool_excluded_even_when_profile_matches(self, mock_flask_g, mocker):
        # 異常系: is_tool_visible が False を返すツール("a")は、
        # enabled/profileの条件を満たしていても結果に含まれないこと
        mocker.patch("api.load_dynamic_tools", return_value=FAKE_TOOLS)
        mocker.patch("api.is_tool_visible", side_effect=lambda t, payload, cache: t["name"] != "a")

        result = api.handle_tools_list({}, {"profile": "AgenticAI"})

        assert [t["name"] for t in result["tools"]] == ["d"]

    def test_result_shape_only_exposes_name_description_input_schema(self, mock_flask_g, mocker):
        # 正常系: レスポンスの各ツールには name/description/inputSchema のみが
        # 含まれ、enabled/profile/required_roles等の内部情報は含まれないこと
        mocker.patch("api.load_dynamic_tools", return_value=[FAKE_TOOLS[0]])
        mocker.patch("api.is_tool_visible", return_value=True)

        result = api.handle_tools_list({}, {})

        assert result == {"tools": [{"name": "a", "description": "A", "inputSchema": {"type": "object"}}]}

    def test_missing_input_schema_defaults_to_empty_object_schema(self, mock_flask_g, mocker):
        # 境界値: ツール設定にinputSchemaが無い場合、空のobjectスキーマが
        # デフォルト値として使われること
        tool = {"name": "x", "description": "X", "enabled": True, "profile": None}
        mocker.patch("api.load_dynamic_tools", return_value=[tool])
        mocker.patch("api.is_tool_visible", return_value=True)

        result = api.handle_tools_list({}, {})

        assert result["tools"][0]["inputSchema"] == {"type": "object", "properties": {}}


class TestJsonrpcHandlerProfileQueryString:
    """
    jsonrpc_handler がクエリー文字列 `profile` を payload["profile"] として
    ハンドラに渡すことを確認する(before_request_handlerは経由せず、
    ビュー関数を直接呼び出してg属性を手動で設定する)。
    """

    def _call(self, app, mocker, url, captured):
        def _fake_handler(params, payload):
            captured["profile"] = payload.get("profile")
            return {"tools": []}

        mocker.patch.dict(api.JSONRPC_METHODS, {"tools/list": _fake_handler})

        with app.test_request_context(
            url,
            method="POST",
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
        ):
            _set_g_mocks()
            g.ORGANIZATION_ID = ORG_ID
            g.WORKSPACE_ID = WS_ID
            g.USER_ID = "user-1"
            g.ROLES = []
            api.jsonrpc_handler(ORG_ID, WS_ID)

    def test_profile_query_string_is_forwarded_to_handler(self, app, mocker):
        # 正常系: URLのクエリー文字列 ?profile=LLMEditor が、
        # handle_tools_listに渡すpayload["profile"]にそのまま反映されること
        captured = {}
        url = "/api/{}/workspaces/{}/mcp?profile=LLMEditor".format(ORG_ID, WS_ID)

        self._call(app, mocker, url, captured)

        assert captured["profile"] == "LLMEditor"

    def test_missing_profile_query_string_forwards_none(self, app, mocker):
        # 境界値: クエリー文字列にprofileが無い場合、payload["profile"]は
        # Noneとしてハンドラに渡ること(絞り込み無し=全ツールを意味する)
        captured = {}
        url = "/api/{}/workspaces/{}/mcp".format(ORG_ID, WS_ID)

        self._call(app, mocker, url, captured)

        assert captured["profile"] is None


class TestHandleInitialize:
    def test_returns_expected_protocol_metadata(self, mock_flask_g):
        # 正常系: MCPの"initialize"メソッドが、プロトコルバージョン・
        # サーバー情報・tools capabilityを含む固定のメタデータを返すこと
        result = api.handle_initialize({}, {})

        assert result["protocolVersion"] == "2024-11-05"
        assert result["serverInfo"]["name"] == "ita-api-mcp-server"
        assert "tools" in result["capabilities"]
