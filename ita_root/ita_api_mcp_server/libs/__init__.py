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
#
"""
MCP Server Libraries (ita_api_mcp_server 用の共通ライブラリ集約モジュール)

tools/*.py から `from libs import tool, ...` のように簡潔に import できるように、
このパッケージ内の各モジュールが提供する関数・定数をここでまとめて再エクスポートする。
ファイルアップロード関連の機能は今回のスコープ対象外のため、このモジュールでは提供しない。

--------------------------------------------------------------------------
MCP Server Libraries (aggregated common library module for ita_api_mcp_server)

Re-exports the functions/constants provided by the modules in this package so
that tools/*.py can simply do `from libs import tool, ...`.
File-upload related functionality is out of scope for this task and is not
provided by this module.
"""
from .tools_decorator import (
    tool,
    TOOL_REGISTRY,
    load_dynamic_tools,
    get_tool_functions,
    check_tool_permission
)
from .exceptions import HTTPException
from .forward_headers import build_forward_headers, get_downstream_timeout
from .permissions import is_tool_visible, is_tool_in_profile

# `from libs import *` した際に公開される名前一覧
# Names exposed when someone does `from libs import *`
__all__ = [
    "tool",
    "TOOL_REGISTRY",
    "load_dynamic_tools",
    "get_tool_functions",
    "check_tool_permission",
    "HTTPException",
    "build_forward_headers",
    "get_downstream_timeout",
    "is_tool_visible",
    "is_tool_in_profile"
]
