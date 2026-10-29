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
MCP Server Tools (ita_api_mcp_server が提供するMCPツール群)

このパッケージをimportすると、配下の各モジュールに定義された
@tool デコレーター付き関数が libs.tools_decorator.TOOL_REGISTRY に登録される。

platform_user.py のツール(list-users / create-user)に加え、
attachment_file.py のように multipart/form-data のファイルアップロードなど
JSON-RPCに乗せづらい処理は、@toolデコレーターではなく通常のFlaskルート
(Blueprint)として提供する。この場合はTOOL_REGISTRYには登録されないため、
api.py側で個別にBlueprintをimportしてapp.register_blueprint()する必要がある。

今後、別のツール・Blueprintを追加する場合はこのファイルにimport文を追加すること。

--------------------------------------------------------------------------
MCP Server Tools provided by ita_api_mcp_server.

Importing this package causes every @tool-decorated function defined in the
modules below to be registered into libs.tools_decorator.TOOL_REGISTRY.

In addition to the platform_user.py tools (list-users / create-user),
processing that does not fit well into JSON-RPC (such as attachment_file.py's
multipart/form-data file upload) is provided as an ordinary Flask route
(Blueprint) instead of a @tool-decorated function. Such Blueprints are NOT
registered into TOOL_REGISTRY, so api.py must import and
app.register_blueprint() them separately.

Add an import statement here when a new tool module or Blueprint is added in
the future.
"""
# platform_user.py の @tool デコレーター付き関数を登録するためにimportする
# Import platform_user.py so that its @tool-decorated functions get registered
from . import platform_user

# attachment_file.py が定義するBlueprint、および他モジュールからも利用する
# create_attachment_file / fetch_attachment_file をこのパッケージ経由で公開する
# Re-export the Blueprint, as well as create_attachment_file /
# fetch_attachment_file (which other modules also use), defined by
# attachment_file.py through this package
from .attachment_file import attachment_file_bp, create_attachment_file, fetch_attachment_file

# attachment_zip_file.py の @tool デコレーター付き関数を登録するためにimportする
# Import attachment_zip_file.py so that its @tool-decorated function gets registered
from . import attachment_zip_file

# base64.py の @tool デコレーター付き関数を登録するためにimportする
# Import base64.py so that its @tool-decorated functions get registered
from . import base64

# ita_list_accessible_menus.py の @tool デコレーター付き関数を登録するためにimportする
# Import ita_list_accessible_menus.py so that its @tool-decorated function gets registered
from . import ita_list_accessible_menus

# ita_menu_info.py の @tool デコレーター付き関数を登録するためにimportする
# Import ita_menu_info.py so that its @tool-decorated functions get registered
from . import ita_menu_info

# ita_menu_filter.py の @tool デコレーター付き関数を登録するためにimportする
# Import ita_menu_filter.py so that its @tool-decorated functions get registered
from . import ita_menu_filter

# ita_menu_maintenance_all.py の @tool デコレーター付き関数を登録するためにimportする
# Import ita_menu_maintenance_all.py so that its @tool-decorated function gets registered
from . import ita_menu_maintenance_all

# ita_menu_create.py の @tool デコレーター付き関数を登録するためにimportする
# Import ita_menu_create.py so that its @tool-decorated functions get registered
from . import ita_menu_create

# ita_driver_control.py の @tool デコレーター付き関数を登録するためにimportする
# Import ita_driver_control.py so that its @tool-decorated functions get registered
from . import ita_driver_control

# search_documents.py の @tool デコレーター付き関数群を登録するためにimportする
# Import search_documents.py so that its @tool-decorated functions get registered
from . import search_documents

__all__ = [
    "platform_user",
    "attachment_file_bp",
    "create_attachment_file",
    "fetch_attachment_file",
    "attachment_zip_file",
    "base64",
    "ita_list_accessible_menus",
    "ita_menu_info",
    "ita_menu_filter",
    "ita_menu_maintenance_all",
    "ita_menu_create",
    "ita_driver_control",
    "search_documents"
]
