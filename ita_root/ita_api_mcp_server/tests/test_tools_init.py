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
"""tools/__init__.py のユニットテスト(全@toolデコレーター関数がTOOL_REGISTRYに登録されること)"""

from flask import Blueprint

import tools
from libs import TOOL_REGISTRY

EXPECTED_TOOL_NAMES = {
    "list-users",
    "create-user",
    "create-attachment-text-file",
    "get-attachment-text-file",
    "create-attachment-zip-file",
    "base64-encode",
    "base64-decode",
    "list-accessible-menus",
    "list-menu-info",
    "list-menu-info-pulldown",
    "menu-filter",
    "menu-filter-count",
    "maintenance-all",
    "create-menu",
    "update-menu",
    "get-menu-definition",
    "execute-driver",
    "dry-run-driver",
    "get-driver-status",
    "search-docs",
    "get-document",
}


class TestToolsPackageInit:
    def test_import_registers_all_expected_tools(self):
        # tools パッケージをimportするだけで、配下の各モジュールの@tool付き関数が
        # TOOL_REGISTRYに登録されていること(登録名の網羅性を確認する)
        registered_names = set(TOOL_REGISTRY.keys())

        missing = EXPECTED_TOOL_NAMES - registered_names
        assert not missing, "Expected tools not registered: {}".format(missing)

    def test_attachment_file_blueprint_is_exposed(self):
        # attachment_file_bp がFlaskのBlueprintとしてtoolsパッケージから公開されていること
        assert isinstance(tools.attachment_file_bp, Blueprint)

    def test_create_and_fetch_attachment_file_are_exposed(self):
        # create_attachment_file / fetch_attachment_file がtoolsパッケージ経由で
        # 呼び出し可能な関数として公開されていること(他モジュールからの再利用のため)
        assert callable(tools.create_attachment_file)
        assert callable(tools.fetch_attachment_file)
