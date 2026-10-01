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
エクスポート権限チェック機能のテスト

今回追加した以下の機能をテストします:
- _get_write_permission_menu_id_list(): EXPORT_PERMISSION_CHECK_FLG を考慮した権限フィルタ
- check_export_menu_permission(): メニュー一括エクスポート実行時の権限チェック
- check_import_menu_permission(): メニュー一括インポート実行時の権限チェック
- _check_export_download_permission(): エクスポート管理メニューのファイルダウンロード時の権限チェック

## 重要な仕様

### Excel一括エクスポート vs メニュー一括エクスポート
- **Excel一括エクスポート**: 権限チェック対象外（閲覧権限でOK）
  - 理由: 参照目的のみでインポートしない場合がある（レポート作成など）
  - インポート時に unimport_list 機能で書き込み権限がないメニューを除外する仕組みが既に実装済み
  - **実装要件**:
    - リストAPI (`get_excel_bulk_export_list`): PRIVILEGE IN [0, 1, 2] を表示
    - エクスポート実行: 権限チェックなし
- **メニュー一括エクスポート**: 権限チェック必須（書き込み権限が必要）
  - 理由: エクスポート/インポートは常にセットで使用される（環境移行）
  - エクスポート時に権限チェックすることで、後のインポート実行を保証
  - **実装要件**:
    - リストAPI (`get_menu_export_list`): PRIVILEGE IN ['0', '1'] のみ表示（PRIVILEGE='2'は除外）
    - エクスポート実行 (`check_export_menu_permission`): PRIVILEGE IN ['0', '1'] をチェック
    - **重要**: ユーザーが選択できないメニュー（PRIVILEGE='2'）を選択肢に表示してはいけない

### EXPORT_PERMISSION_CHECK_FLG の意味
- **'0'**: 内部メニュー用、権限チェックをスキップ
  - 対象: workspace, ansible, menu_create, terraform_cloud_ep, terraform_cli, hostgroup, cicd など
  - ワークスペース作成時にロールメニュー紐付で以下のパターンで作成される:
    - パターン1: PRIVILEGE='2'(閲覧のみ) + DISUSE_FLAG='1'(廃止済み)
    - パターン2: PRIVILEGE='1'(メンテナンス可) + DISUSE_FLAG='1'(廃止済み)
    - パターン3: PRIVILEGE='2'(閲覧のみ) + DISUSE_FLAG='0'(有効)
  - 具体的なメニューリストは、マイグレーションスクリプト (ita_migration/versions/2_10_0/WS_level/specific/update_export_permission_check_flag.py) を参照
- **'1' または NULL**: 通常メニュー、書き込み権限（PRIVILEGE IN ['0', '1']）が必要
  - NULL は '1' として扱われる（デフォルトは権限チェック必須）

### PRIVILEGE の意味（T_COMN_ROLE_MENU_LINK）
- **レコードなし**: 権限なし（メニューへのアクセス不可）
- **'0'**: フルメンテナンス権限（追加/更新/削除すべて可能）
- **'1'**: メンテナンス権限（追加/更新は可能、削除は不可）
- **'2'**: 閲覧のみ（読み取り専用）
- **書き込み権限**: PRIVILEGE IN ['0', '1']（'2' や レコードなし は書き込み権限なし）

### 実装チェックリスト（対応漏れ防止）
メニュー一括エクスポートの実装時には、以下の両方を確認すること：
- [ ] リストAPI: `get_menu_export_list()` が PRIVILEGE IN ['0', '1'] のみを返す
- [ ] エクスポート実行API: `check_export_menu_permission()` が PRIVILEGE IN ['0', '1'] をチェックする
- [ ] Excel一括エクスポート: `get_excel_bulk_export_list()` は PRIVILEGE IN [0, 1, 2] を返す（変更しない）
- [ ] テストコード: リストAPIとエクスポート実行APIの両方にテストケースがある

### ロールメニュー紐付のクエリ
- 権限チェック（_get_write_permission_menu_id_list）: DISUSE_FLAG='0' の紐付のみ有効（廃止済みの紐付は権限なし）
- 選択肢一覧（get_menu_export_list）: 通常メニューは DISUSE_FLAG='0' のみ、FLAG='0' の内部メニューは廃止済み紐付も含める
  （ワークスペース作成時に廃止済みで作成される紐付は FLAG='0' のメニューのみ）

### 複数ロールの扱い
- ユーザーが複数ロールを持つ場合、いずれか1つのロールで権限があればOK
- g.ROLES に格納されているすべてのロールIDで検索

### エラーメッセージ
- 権限エラーのコード: 401-00001
- メッセージ: "対象のメニューに対するアクセス権限がありません。(menu: {メニュー名})"
- メニュー名は g.LANGUAGE に基づいて MENU_NAME_JA または MENU_NAME_EN を使用
- 複数メニューがエラーの場合はカンマ区切り

### ファイルダウンロード時の権限チェック
- 対象メニュー: menu_export_import_list のみ
- bulk_excel_export_import_list は対象外（Excel一括エクスポートは閲覧権限で実行できるため、ダウンロードも制限しない）
- エクスポートのレコード: JSON_STORAGE_ITEM（JSON）の menu リストを check_export_menu_permission() でチェック
- インポートのレコード（EXECUTION_TYPE=2）: JSON_STORAGE_ITEM（カンマ区切り）を check_import_menu_permission() でチェック
- 廃止済みレコードもダウンロード対象（DISUSE_FLAG で絞り込まない）
- 対象メニューを特定できない場合は 499-00201（MSG-30038）

### レコード取得（filter）時のファイルデータ除外
- 対象メニュー: menu_export_import_list のみ（file=no 指定時は対象外）
- 書き込み権限のないメニューを含むレコード、対象メニューを特定できないレコードは file を {} にする
- 権限判定は get_denied_menu_rest_set() で全レコード分をまとめて行う
- 通常テーブルと履歴テーブル（_JNL）の両方に対応
- プライマリキーは objmenu.get_primary_key() で動的に取得（ハードコード禁止）

### 関連する他の修正
- **platform-auth**: stream mode でステータスコードが正しく伝播されるように修正（200ではなく401を返す）
- **UI (table.js, common.js)**: バックエンドの詳細なエラーメッセージ（e.message）を優先して表示
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from flask import g

from libs.export_import import (
    _get_write_permission_menu_id_list,
    check_export_menu_permission,
    check_import_menu_permission,
    get_menu_export_list,
    get_denied_menu_rest_set,
    get_excel_bulk_export_list
)
from libs.menu_filter import _check_export_download_permission, _mask_export_file_data, rest_filter, rest_filter_journal
from common_libs.common.exception import AppException


class TestDataBuilder:
    """テストデータを簡潔に構築するビルダー（test_export_permission.py 専用）"""

    @staticmethod
    def menu(menu_id, flag='1'):
        """T_COMN_MENU のレコードを生成"""
        return {'MENU_ID': menu_id, 'EXPORT_PERMISSION_CHECK_FLG': flag}

    @staticmethod
    def link(menu_id, privilege='1', disuse_flag=0):
        """T_COMN_ROLE_MENU_LINK のレコードを生成"""
        return {'MENU_ID': menu_id, 'PRIVILEGE': privilege, 'DISUSE_FLAG': disuse_flag}

    @staticmethod
    def export_record(execution_no, execution_type='1', json_storage_item='{"menu": ["menu1"]}'):
        """T_MENU_EXPORT_IMPORT のレコードを生成"""
        return {
            'EXECUTION_NO': execution_no,
            'EXECUTION_TYPE': execution_type,
            'JSON_STORAGE_ITEM': json_storage_item,
            'DISUSE_FLAG': '0'
        }


# グローバルなビルダーインスタンス
builder = TestDataBuilder()


class TestGetWritePermissionMenuIdList:
    """_get_write_permission_menu_id_list() のテスト"""

    def test_empty_list(self, mock_objdbca, mock_g_with_roles):
        """空リストを渡した場合、空リストが返る"""
        result = _get_write_permission_menu_id_list(mock_objdbca, [])
        assert result == []

    def test_all_flag_0_menus(self, mock_objdbca, mock_g_with_roles):
        """すべて EXPORT_PERMISSION_CHECK_FLG='0' のメニューは権限チェックをスキップ"""
        menu_id_list = ['10203', '10204', '50102']

        # T_COMN_MENU から EXPORT_PERMISSION_CHECK_FLG を取得
        mock_objdbca.table_select.return_value = [
            {'MENU_ID': '10203', 'EXPORT_PERMISSION_CHECK_FLG': '0'},
            {'MENU_ID': '10204', 'EXPORT_PERMISSION_CHECK_FLG': '0'},
            {'MENU_ID': '50102', 'EXPORT_PERMISSION_CHECK_FLG': '0'},
        ]

        result = _get_write_permission_menu_id_list(mock_objdbca, menu_id_list)

        # FLAG=0 なので全部返る（権限チェックなし）
        assert result == ['10203', '10204', '50102']
        # table_select は T_COMN_MENU のみ（T_COMN_ROLE_MENU_LINK は呼ばれない）
        assert mock_objdbca.table_select.call_count == 1

    def test_all_flag_1_with_write_permission(self, mock_objdbca, mock_g_with_roles):
        """すべて EXPORT_PERMISSION_CHECK_FLG='1' かつ書き込み権限あり"""
        menu_id_list = ['10101', '10102', '10201']

        # T_COMN_MENU から EXPORT_PERMISSION_CHECK_FLG を取得
        # 2回目の呼び出しは T_COMN_ROLE_MENU_LINK
        mock_objdbca.table_select.side_effect = [
            # 1回目: T_COMN_MENU
            [
                {'MENU_ID': '10101', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': '10102', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': '10201', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
            ],
            # 2回目: T_COMN_ROLE_MENU_LINK (書き込み権限あり)
            [
                {'MENU_ID': '10101', 'PRIVILEGE': '1'},
                {'MENU_ID': '10102', 'PRIVILEGE': '0'},
                {'MENU_ID': '10201', 'PRIVILEGE': '1'},
            ],
        ]

        result = _get_write_permission_menu_id_list(mock_objdbca, menu_id_list)

        # 全部書き込み権限があるので全部返る
        assert result == ['10101', '10102', '10201']
        assert mock_objdbca.table_select.call_count == 2

    def test_flag_1_without_write_permission(self, mock_objdbca, mock_g_with_roles):
        """EXPORT_PERMISSION_CHECK_FLG='1' で書き込み権限なし"""
        menu_id_list = ['10101', '10102']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_COMN_MENU
            [
                {'MENU_ID': '10101', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': '10102', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
            ],
            # 2回目: T_COMN_ROLE_MENU_LINK (10101のみ権限あり)
            [
                {'MENU_ID': '10101', 'PRIVILEGE': '1'},
            ],
        ]

        result = _get_write_permission_menu_id_list(mock_objdbca, menu_id_list)

        # 10101 のみ権限があるので返る
        assert result == ['10101']
        # 廃止済みの紐付は権限なし（DISUSE_FLAG='0' のみ検索）
        where, bind = mock_objdbca.table_select.call_args[0][1:]
        assert 'DISUSE_FLAG = %s' in where
        assert bind[-1] == 0

    def test_mixed_flag_0_and_flag_1(self, mock_objdbca, mock_g_with_roles):
        """FLAG=0 と FLAG=1 が混在"""
        menu_id_list = ['10203', '10101', '50102', '10102']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_COMN_MENU
            [
                {'MENU_ID': '10203', 'EXPORT_PERMISSION_CHECK_FLG': '0'},  # チェックスキップ
                {'MENU_ID': '10101', 'EXPORT_PERMISSION_CHECK_FLG': '1'},  # チェック必要
                {'MENU_ID': '50102', 'EXPORT_PERMISSION_CHECK_FLG': '0'},  # チェックスキップ
                {'MENU_ID': '10102', 'EXPORT_PERMISSION_CHECK_FLG': '1'},  # チェック必要
            ],
            # 2回目: T_COMN_ROLE_MENU_LINK (10101のみ権限あり)
            [
                {'MENU_ID': '10101', 'PRIVILEGE': '1'},
            ],
        ]

        result = _get_write_permission_menu_id_list(mock_objdbca, menu_id_list)

        # FLAG=0 の 10203, 50102 と、権限ありの 10101 が返る
        # 10102 は FLAG=1 で権限なしなので除外
        assert result == ['10203', '10101', '50102']

    def test_preserve_order(self, mock_objdbca, mock_g_with_roles):
        """入力の順序が維持される"""
        menu_id_list = ['50102', '10203', '10101']

        mock_objdbca.table_select.side_effect = [
            [
                {'MENU_ID': '50102', 'EXPORT_PERMISSION_CHECK_FLG': '0'},
                {'MENU_ID': '10203', 'EXPORT_PERMISSION_CHECK_FLG': '0'},
                {'MENU_ID': '10101', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
            ],
            [
                {'MENU_ID': '10101', 'PRIVILEGE': '1'},
            ],
        ]

        result = _get_write_permission_menu_id_list(mock_objdbca, menu_id_list)

        # 入力順序が維持される
        assert result == ['50102', '10203', '10101']


class TestCheckExportMenuPermission:
    """
    check_export_menu_permission() のテスト

    注意: この関数はメニュー一括エクスポートでのみ使用されます。
    Excel一括エクスポートは権限チェック対象外（閲覧権限でOK）のため、この関数を呼びません。
    """

    def test_empty_menu_list(self, mock_objdbca, mock_g_with_roles):
        """空リストの場合は何もしない"""
        # 例外が投げられないことを確認
        check_export_menu_permission(mock_objdbca, [])

    def test_all_menus_have_write_permission(self, mock_objdbca, mock_g_with_roles):
        """すべてのメニューに書き込み権限がある場合"""
        menu_rest_list = ['menu1', 'menu2']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_COMN_MENU
            [
                {'MENU_ID': '10101', 'MENU_NAME_REST': 'menu1', 'MENU_NAME_JA': 'メニュー1', 'MENU_NAME_EN': 'Menu 1'},
                {'MENU_ID': '10102', 'MENU_NAME_REST': 'menu2', 'MENU_NAME_JA': 'メニュー2', 'MENU_NAME_EN': 'Menu 2'},
            ],
            # 2回目: T_COMN_MENU (EXPORT_PERMISSION_CHECK_FLG)
            [
                {'MENU_ID': '10101', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': '10102', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK
            [
                {'MENU_ID': '10101', 'PRIVILEGE': '1'},
                {'MENU_ID': '10102', 'PRIVILEGE': '0'},
            ],
        ]

        # 例外が投げられないことを確認
        check_export_menu_permission(mock_objdbca, menu_rest_list)

    def test_no_write_permission_raises_exception(self, mock_objdbca, mock_g_with_roles):
        """書き込み権限がないメニューがある場合、例外が投げられる"""
        menu_rest_list = ['menu1', 'menu2']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_COMN_MENU
            [
                {'MENU_ID': '10101', 'MENU_NAME_REST': 'menu1', 'MENU_NAME_JA': 'メニュー1', 'MENU_NAME_EN': 'Menu 1'},
                {'MENU_ID': '10102', 'MENU_NAME_REST': 'menu2', 'MENU_NAME_JA': 'メニュー2', 'MENU_NAME_EN': 'Menu 2'},
            ],
            # 2回目: T_COMN_MENU (EXPORT_PERMISSION_CHECK_FLG)
            [
                {'MENU_ID': '10101', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': '10102', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK (10101のみ権限あり)
            [
                {'MENU_ID': '10101', 'PRIVILEGE': '1'},
            ],
        ]

        with pytest.raises(AppException) as exc_info:
            check_export_menu_permission(mock_objdbca, menu_rest_list)

        # エラーコードが 401-00001 であることを確認
        assert exc_info.value.args[0] == "401-00001"
        # メニュー名が含まれていることを確認
        assert 'メニュー2' in exc_info.value.args[2][0]

    def test_flag_0_menu_skip_permission_check(self, mock_objdbca, mock_g_with_roles):
        """EXPORT_PERMISSION_CHECK_FLG='0' のメニューは権限チェックをスキップ"""
        menu_rest_list = ['menu1', 'menu2']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_COMN_MENU
            [
                {'MENU_ID': '10203', 'MENU_NAME_REST': 'menu1', 'MENU_NAME_JA': 'メニュー-テーブル紐付管理', 'MENU_NAME_EN': 'Menu-Table link'},
                {'MENU_ID': '10102', 'MENU_NAME_REST': 'menu2', 'MENU_NAME_JA': 'メニュー2', 'MENU_NAME_EN': 'Menu 2'},
            ],
            # 2回目: T_COMN_MENU (EXPORT_PERMISSION_CHECK_FLG)
            [
                {'MENU_ID': '10203', 'EXPORT_PERMISSION_CHECK_FLG': '0'},  # チェックスキップ
                {'MENU_ID': '10102', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK (10102の権限あり)
            [
                {'MENU_ID': '10102', 'PRIVILEGE': '1'},
            ],
        ]

        # 例外が投げられないことを確認（10203 は FLAG=0 なのでチェックスキップ）
        check_export_menu_permission(mock_objdbca, menu_rest_list)

    def test_all_flag_0_menus(self, mock_objdbca, mock_g_with_roles):
        """すべて EXPORT_PERMISSION_CHECK_FLG='0' の場合、権限チェック自体がスキップ"""
        menu_rest_list = ['menu1', 'menu2']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_COMN_MENU
            [
                {'MENU_ID': '10203', 'MENU_NAME_REST': 'menu1', 'MENU_NAME_JA': 'メニュー1', 'MENU_NAME_EN': 'Menu 1'},
                {'MENU_ID': '50102', 'MENU_NAME_REST': 'menu2', 'MENU_NAME_JA': 'メニュー2', 'MENU_NAME_EN': 'Menu 2'},
            ],
            # 2回目: T_COMN_MENU (EXPORT_PERMISSION_CHECK_FLG)
            [
                {'MENU_ID': '10203', 'EXPORT_PERMISSION_CHECK_FLG': '0'},
                {'MENU_ID': '50102', 'EXPORT_PERMISSION_CHECK_FLG': '0'},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK は呼ばれない（全部 FLAG=0）
        ]

        # 例外が投げられないことを確認
        check_export_menu_permission(mock_objdbca, menu_rest_list)
        # T_COMN_ROLE_MENU_LINK へのクエリは実行されない
        assert mock_objdbca.table_select.call_count == 2


class TestCheckImportMenuPermission:
    """check_import_menu_permission() のテスト"""

    def test_empty_menu_list(self, mock_objdbca, mock_g_with_roles):
        """空リストの場合は何もしない"""
        check_import_menu_permission(mock_objdbca, [])

    def test_all_new_menus(self, mock_objdbca, mock_g_with_roles):
        """すべて新規メニュー（存在しない）の場合は権限チェックしない"""
        menu_rest_list = ['new_menu1', 'new_menu2']

        # T_COMN_MENU に該当メニューが存在しない
        mock_objdbca.table_select.return_value = []

        # 例外が投げられないことを確認
        check_import_menu_permission(mock_objdbca, menu_rest_list)

    def test_existing_menu_with_flag_0(self, mock_objdbca, mock_g_with_roles):
        """既存メニューで FLAG=0 の場合は権限チェックしない"""
        menu_rest_list = ['menu1', 'menu2']

        # T_COMN_MENU から既存メニューを取得（すべて FLAG=0）
        mock_objdbca.table_select.return_value = [
            {
                'MENU_ID': '10203',
                'MENU_NAME_REST': 'menu1',
                'MENU_NAME_JA': 'メニュー-テーブル紐付管理',
                'MENU_NAME_EN': 'Menu-Table link',
                'EXPORT_PERMISSION_CHECK_FLG': '0'
            },
            {
                'MENU_ID': '50102',
                'MENU_NAME_REST': 'menu2',
                'MENU_NAME_JA': 'パラメータシート定義一覧',
                'MENU_NAME_EN': 'Parameter sheet definition list',
                'EXPORT_PERMISSION_CHECK_FLG': '0'
            },
        ]

        # 例外が投げられないことを確認（FLAG=0 なので権限チェックスキップ）
        check_import_menu_permission(mock_objdbca, menu_rest_list)
        # T_COMN_MENU のみ呼ばれる（_get_write_permission_menu_id_list は呼ばれない）
        assert mock_objdbca.table_select.call_count == 1

    def test_existing_menu_with_flag_1_and_write_permission(self, mock_objdbca, mock_g_with_roles):
        """既存メニューで FLAG=1 かつ書き込み権限あり"""
        menu_rest_list = ['menu1', 'menu2']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_COMN_MENU
            [
                {
                    'MENU_ID': '10101',
                    'MENU_NAME_REST': 'menu1',
                    'MENU_NAME_JA': 'メニュー1',
                    'MENU_NAME_EN': 'Menu 1',
                    'EXPORT_PERMISSION_CHECK_FLG': '1'
                },
                {
                    'MENU_ID': '10102',
                    'MENU_NAME_REST': 'menu2',
                    'MENU_NAME_JA': 'メニュー2',
                    'MENU_NAME_EN': 'Menu 2',
                    'EXPORT_PERMISSION_CHECK_FLG': '1'
                },
            ],
            # 2回目: T_COMN_MENU (_get_write_permission_menu_id_list 内)
            [
                {'MENU_ID': '10101', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': '10102', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK
            [
                {'MENU_ID': '10101', 'PRIVILEGE': '1'},
                {'MENU_ID': '10102', 'PRIVILEGE': '0'},
            ],
        ]

        # 例外が投げられないことを確認
        check_import_menu_permission(mock_objdbca, menu_rest_list)

    def test_existing_menu_with_flag_1_without_write_permission(self, mock_objdbca, mock_g_with_roles):
        """既存メニューで FLAG=1 だが書き込み権限なし → 例外"""
        menu_rest_list = ['menu1', 'menu2']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_COMN_MENU
            [
                {
                    'MENU_ID': '10101',
                    'MENU_NAME_REST': 'menu1',
                    'MENU_NAME_JA': 'メニュー1',
                    'MENU_NAME_EN': 'Menu 1',
                    'EXPORT_PERMISSION_CHECK_FLG': '1'
                },
                {
                    'MENU_ID': '10102',
                    'MENU_NAME_REST': 'menu2',
                    'MENU_NAME_JA': 'メニュー2',
                    'MENU_NAME_EN': 'Menu 2',
                    'EXPORT_PERMISSION_CHECK_FLG': '1'
                },
            ],
            # 2回目: T_COMN_MENU (_get_write_permission_menu_id_list 内)
            [
                {'MENU_ID': '10101', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': '10102', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK (10101のみ権限あり)
            [
                {'MENU_ID': '10101', 'PRIVILEGE': '1'},
            ],
        ]

        with pytest.raises(AppException) as exc_info:
            check_import_menu_permission(mock_objdbca, menu_rest_list)

        # エラーコードが 401-00001 であることを確認
        assert exc_info.value.args[0] == "401-00001"
        # メニュー名が含まれていることを確認
        assert 'メニュー2' in exc_info.value.args[2][0]

    def test_mixed_new_and_existing_menus(self, mock_objdbca, mock_g_with_roles):
        """新規メニューと既存メニューが混在"""
        menu_rest_list = ['new_menu', 'existing_menu_flag0', 'existing_menu_flag1']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_COMN_MENU (new_menu は存在しない、他2つは既存)
            [
                {
                    'MENU_ID': '10203',
                    'MENU_NAME_REST': 'existing_menu_flag0',
                    'MENU_NAME_JA': 'メニュー-テーブル紐付管理',
                    'MENU_NAME_EN': 'Menu-Table link',
                    'EXPORT_PERMISSION_CHECK_FLG': '0'
                },
                {
                    'MENU_ID': '10101',
                    'MENU_NAME_REST': 'existing_menu_flag1',
                    'MENU_NAME_JA': 'メニュー1',
                    'MENU_NAME_EN': 'Menu 1',
                    'EXPORT_PERMISSION_CHECK_FLG': '1'
                },
            ],
            # 2回目: T_COMN_MENU (_get_write_permission_menu_id_list 内、10101のみ)
            [
                {'MENU_ID': '10101', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK
            [
                {'MENU_ID': '10101', 'PRIVILEGE': '1'},
            ],
        ]

        # 例外が投げられないことを確認
        # new_menu: 新規なのでチェックスキップ
        # existing_menu_flag0: FLAG=0 なのでチェックスキップ
        # existing_menu_flag1: FLAG=1 で書き込み権限あり
        check_import_menu_permission(mock_objdbca, menu_rest_list)


class TestCheckExportDownloadPermission:
    """
    _check_export_download_permission() のテスト

    メニューエクスポート・インポート管理（menu_export_import_list）の
    ファイルダウンロード時に、エクスポート対象メニューへの書き込み権限をチェックする機能
    """

    def test_record_not_found(self, mock_objdbca, mock_g_with_roles):
        """レコードが存在しない場合、例外が投げられる"""
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'

        # レコードが存在しない
        mock_objdbca.table_select.return_value = []

        with pytest.raises(AppException) as exc_info:
            _check_export_download_permission(mock_objdbca, mock_objmenu, 'menu_export_import_list', '999')

        assert exc_info.value.args[0] == "499-00201"
        g.appmsg.get_api_message.assert_called_with("MSG-30038", [])

    def test_json_storage_item_is_none(self, mock_objdbca, mock_g_with_roles):
        """JSON_STORAGE_ITEM が NULL の場合、例外が投げられる"""
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'

        # JSON_STORAGE_ITEM が NULL
        mock_objdbca.table_select.return_value = [
            {'JSON_STORAGE_ITEM': None}
        ]

        with pytest.raises(AppException) as exc_info:
            _check_export_download_permission(mock_objdbca, mock_objmenu, 'menu_export_import_list', '1')

        assert exc_info.value.args[0] == "499-00201"
        g.appmsg.get_api_message.assert_called_with("MSG-30038", [])

    def test_menu_list_is_empty(self, mock_objdbca, mock_g_with_roles):
        """menu リストが空の場合、例外が投げられる"""
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'

        # menu リストが空
        json_storage_item = json.dumps({'menu': []})
        mock_objdbca.table_select.return_value = [
            {'JSON_STORAGE_ITEM': json_storage_item}
        ]

        with pytest.raises(AppException) as exc_info:
            _check_export_download_permission(mock_objdbca, mock_objmenu, 'menu_export_import_list', '1')

        assert exc_info.value.args[0] == "499-00201"
        g.appmsg.get_api_message.assert_called_with("MSG-30038", [])

    @patch('libs.menu_filter.check_export_menu_permission')
    def test_valid_permission(self, mock_check_permission, mock_objdbca, mock_g_with_roles):
        """正常な権限チェック（権限あり）"""
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'

        # 有効な JSON_STORAGE_ITEM
        json_storage_item = json.dumps({
            'menu': ['menu1', 'menu2']
        })
        mock_objdbca.table_select.return_value = [
            {'JSON_STORAGE_ITEM': json_storage_item}
        ]

        # check_export_menu_permission が例外を投げない（権限あり）
        mock_check_permission.return_value = None

        # 例外が投げられないことを確認
        _check_export_download_permission(mock_objdbca, mock_objmenu, 'menu_export_import_list', '1')

        # check_export_menu_permission が呼ばれたことを確認
        mock_check_permission.assert_called_once_with(mock_objdbca, ['menu1', 'menu2'])

    @patch('libs.menu_filter.check_export_menu_permission')
    def test_no_permission(self, mock_check_permission, mock_objdbca, mock_g_with_roles):
        """権限がない場合、例外が伝播される"""
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'

        # 有効な JSON_STORAGE_ITEM
        json_storage_item = json.dumps({
            'menu': ['menu1', 'menu2']
        })
        mock_objdbca.table_select.return_value = [
            {'JSON_STORAGE_ITEM': json_storage_item}
        ]

        # check_export_menu_permission が例外を投げる（権限なし）
        mock_check_permission.side_effect = AppException("401-00001", ["メニュー2"], ["メニュー2"])

        with pytest.raises(AppException) as exc_info:
            _check_export_download_permission(mock_objdbca, mock_objmenu, 'menu_export_import_list', '1')

        assert exc_info.value.args[0] == "401-00001"

    @patch('libs.menu_filter.check_export_menu_permission')
    def test_history_table_access(self, mock_check_permission, mock_objdbca, mock_g_with_roles):
        """履歴テーブルからのファイルダウンロード"""
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'

        # 履歴テーブルから取得
        json_storage_item = json.dumps({
            'menu': ['menu1', 'menu2']
        })
        mock_objdbca.table_select.return_value = [
            {'JSON_STORAGE_ITEM': json_storage_item}
        ]

        # journal_uuid を指定
        _check_export_download_permission(mock_objdbca, mock_objmenu, 'menu_export_import_list', '1', journal_uuid='journal-123')

        # 履歴テーブルが呼ばれたことを確認
        call_args = mock_objdbca.table_select.call_args[0]
        assert 'T_MENU_EXPORT_IMPORT_JNL' in call_args[0]
        assert 'JOURNAL_SEQ_NO' in call_args[1]

    def test_json_parse_error(self, mock_objdbca, mock_g_with_roles):
        """JSON パースエラーの場合、例外が投げられる"""
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'

        # 不正な JSON
        mock_objdbca.table_select.return_value = [
            {'JSON_STORAGE_ITEM': 'invalid json'}
        ]

        with pytest.raises(AppException) as exc_info:
            _check_export_download_permission(mock_objdbca, mock_objmenu, 'menu_export_import_list', '1')

        assert exc_info.value.args[0] == "499-00201"
        g.appmsg.get_api_message.assert_called_with("MSG-30038", [])

    def test_disused_record_is_not_filtered(self, mock_objdbca, mock_g_with_roles):
        """廃止済みレコードもダウンロード対象のため、DISUSE_FLAG で絞り込まない"""
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'

        mock_objdbca.table_select.return_value = []

        with pytest.raises(AppException):
            _check_export_download_permission(mock_objdbca, mock_objmenu, 'menu_export_import_list', '1')

        call_args = mock_objdbca.table_select.call_args[0]
        assert call_args[0] == 'T_MENU_EXPORT_IMPORT'
        assert 'DISUSE_FLAG' not in call_args[1]
        assert call_args[2] == ['1']

    @patch('libs.menu_filter.check_export_menu_permission')
    @patch('libs.menu_filter.check_import_menu_permission')
    def test_import_record_valid_permission(self, mock_check_import, mock_check_export, mock_objdbca, mock_g_with_roles):
        """インポートのレコードは、カンマ区切りのメニューRESTIDを check_import_menu_permission でチェックする"""
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'

        # インポートのレコード（EXECUTION_TYPE=2、JSON_STORAGE_ITEM はカンマ区切り）
        mock_objdbca.table_select.return_value = [
            {'EXECUTION_TYPE': '2', 'JSON_STORAGE_ITEM': 'menu1,menu2'}
        ]

        _check_export_download_permission(mock_objdbca, mock_objmenu, 'menu_export_import_list', '1')

        mock_check_import.assert_called_once_with(mock_objdbca, ['menu1', 'menu2'])
        mock_check_export.assert_not_called()

    @patch('libs.menu_filter.check_import_menu_permission')
    def test_import_record_no_permission(self, mock_check_import, mock_objdbca, mock_g_with_roles):
        """インポートのレコードで権限がない場合、例外が伝播される"""
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'

        mock_objdbca.table_select.return_value = [
            {'EXECUTION_TYPE': 2, 'JSON_STORAGE_ITEM': 'menu1'}
        ]
        mock_check_import.side_effect = AppException("401-00001", ["メニュー1"], ["メニュー1"])

        with pytest.raises(AppException) as exc_info:
            _check_export_download_permission(mock_objdbca, mock_objmenu, 'menu_export_import_list', '1')

        assert exc_info.value.args[0] == "401-00001"

    @patch('libs.menu_filter.check_import_menu_permission')
    def test_import_record_menu_list_is_empty(self, mock_check_import, mock_objdbca, mock_g_with_roles):
        """インポートのレコードでメニューが取り出せない場合、例外が投げられる"""
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'

        mock_objdbca.table_select.return_value = [
            {'EXECUTION_TYPE': '2', 'JSON_STORAGE_ITEM': ','}
        ]

        with pytest.raises(AppException) as exc_info:
            _check_export_download_permission(mock_objdbca, mock_objmenu, 'menu_export_import_list', '1')

        assert exc_info.value.args[0] == "499-00201"
        mock_check_import.assert_not_called()


class TestExecuteMenuImportPermission:
    """execute_menu_import() がインポート実行前に check_import_menu_permission() を呼ぶことを確認"""

    @patch('libs.export_import.clear_files')
    @patch('libs.export_import.check_import_menu_permission')
    def test_permission_denied_stops_import_and_cleans_up(self, mock_check, mock_clear, mock_objdbca, mock_g_with_roles, monkeypatch):
        from libs.export_import import execute_menu_import
        monkeypatch.setenv('STORAGEPATH', '/storage/')
        mock_check.side_effect = AppException("401-00001", ["メニュー1"], ["メニュー1"])
        body = {'menu': ['menu1'], 'upload_id': 'A_123', 'file_name': 'a.kym'}

        with pytest.raises(AppException) as exc_info:
            execute_menu_import(mock_objdbca, 'org', 'ws', 'menu_import', body)

        assert exc_info.value.args[0] == "401-00001"
        mock_check.assert_called_once_with(mock_objdbca, ['menu1'])
        mock_clear.assert_called_once()


class TestFilePathDownloadPermissionTarget:
    """
    get_file_path() / get_history_file_path() で権限チェックを行う対象メニューのテスト
    Excel一括エクスポート・インポート管理には影響を与えないことを確認
    """

    def _make_objmenu(self):
        objmenu = MagicMock()
        objmenu.get_col_class_name.return_value = 'FileUploadColumn'
        objmenu.get_rest_key.return_value = 'execution_no'
        objmenu.rest_filter.return_value = (
            '000-00000',
            [{'parameter': {'file_name': 'a.kym', 'journal_id': 'j1', 'journal_datetime': '2026/01/01 00:00:00'}}],
            ''
        )
        objmenu.get_menu_info.return_value = {'MENUINFO': {'HISTORY_TABLE_FLAG': '1'}}
        objmenu.get_columnclass.return_value.get_file_data_path.return_value = '/path/a.kym'
        return objmenu

    @pytest.mark.parametrize('menu, expected_called', [
        ('menu_export_import_list', True),
        ('bulk_excel_export_import_list', False),
    ])
    @patch('libs.menu_filter._check_export_download_permission')
    @patch('libs.menu_filter.load_table')
    def test_get_file_path(self, mock_load_table, mock_check, menu, expected_called, mock_objdbca, mock_g_with_roles):
        from libs.menu_filter import get_file_path
        mock_load_table.loadTable.return_value = self._make_objmenu()

        get_file_path(mock_objdbca, menu, '1', 'file_name')

        assert mock_check.called is expected_called

    @pytest.mark.parametrize('menu, expected_called', [
        ('menu_export_import_list', True),
        ('bulk_excel_export_import_list', False),
    ])
    @patch('libs.menu_filter.os.path.isfile', return_value=True)
    @patch('libs.menu_filter._check_export_download_permission')
    @patch('libs.menu_filter.load_table')
    def test_get_history_file_path(self, mock_load_table, mock_check, mock_isfile, menu, expected_called, mock_objdbca, mock_g_with_roles):
        from libs.menu_filter import get_history_file_path
        mock_load_table.loadTable.return_value = self._make_objmenu()

        get_history_file_path(mock_objdbca, menu, '1', 'file_name', 'j1')

        assert mock_check.called is expected_called


class TestGetMenuExportList:
    """
    get_menu_export_list() のテスト

    メニュー一括エクスポートの対象メニューリスト取得
    書き込み権限（PRIVILEGE='0' or '1'）を持つメニューのみを返すことを確認
    """

    @patch('libs.export_import._get_target_menu_id_list')
    @patch('libs.export_import._create_export_menu_data')
    def test_only_write_permission_menus(self, mock_create_data, mock_get_target, mock_objdbca, mock_g_with_roles):
        """書き込み権限（PRIVILEGE='0', '1'）のメニューのみが返される"""
        mock_get_target.return_value = ['menu1', 'menu2', 'menu3', 'menu4']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_DP_HIDE_MENU_LIST
            [],
            # 2回目: T_COMN_MENU（全メニューのFLAG）
            [
                {'MENU_ID': 'menu1', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': 'menu2', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': 'menu3', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': 'menu4', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK（全紐付）
            [
                {'MENU_ID': 'menu1', 'PRIVILEGE': '0', 'DISUSE_FLAG': 0},
                {'MENU_ID': 'menu2', 'PRIVILEGE': '1', 'DISUSE_FLAG': 0},
            ],
        ]

        mock_create_data.return_value = {'menu_groups': []}

        get_menu_export_list(mock_objdbca, 'org1', 'ws1')

        call_args = mock_create_data.call_args[0]
        permitted_menu_ids = call_args[1]

        # PRIVILEGE='0', '1' のメニューのみが含まれる
        assert permitted_menu_ids == ['menu1', 'menu2']

    @patch('libs.export_import._get_target_menu_id_list')
    @patch('libs.export_import._create_export_menu_data')
    def test_excludes_readonly_permission_menus(self, mock_create_data, mock_get_target, mock_objdbca, mock_g_with_roles):
        """閲覧のみ（PRIVILEGE='2'）のメニューが除外される"""
        mock_get_target.return_value = ['menu1', 'menu2', 'menu3']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_DP_HIDE_MENU_LIST
            [],
            # 2回目: T_COMN_MENU（全メニューのFLAG）
            [
                {'MENU_ID': 'menu1', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': 'menu2', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': 'menu3', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK（全紐付）
            [
                {'MENU_ID': 'menu1', 'PRIVILEGE': '1', 'DISUSE_FLAG': 0},
                {'MENU_ID': 'menu2', 'PRIVILEGE': '2', 'DISUSE_FLAG': 0},  # 閲覧のみ
            ],
        ]

        mock_create_data.return_value = {'menu_groups': []}

        get_menu_export_list(mock_objdbca, 'org1', 'ws1')

        call_args = mock_create_data.call_args[0]
        permitted_menu_ids = call_args[1]

        # PRIVILEGE='1' のメニューのみが含まれる
        assert 'menu1' in permitted_menu_ids
        # PRIVILEGE='2' のメニューは除外されている（menu2は含まれない）
        assert 'menu2' not in permitted_menu_ids
        # 紐付のないmenu3も含まれない
        assert 'menu3' not in permitted_menu_ids

    @patch('libs.export_import._get_target_menu_id_list')
    @patch('libs.export_import._create_export_menu_data')
    def test_flag0_menus_include_readonly_and_disused_link(self, mock_create_data, mock_get_target, mock_objdbca, mock_g_with_roles):
        """内部メニュー（FLAG='0'）は、閲覧のみ・廃止済みの紐付でも表示され、紐付がなければ表示されない"""
        mock_get_target.return_value = ['menu1', 'flag0_readonly', 'flag0_no_link']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_DP_HIDE_MENU_LIST
            [],
            # 2回目: T_COMN_MENU（全メニューのFLAG）
            [
                {'MENU_ID': 'menu1', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': 'flag0_readonly', 'EXPORT_PERMISSION_CHECK_FLG': '0'},
                {'MENU_ID': 'flag0_no_link', 'EXPORT_PERMISSION_CHECK_FLG': '0'},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK（全紐付）
            [
                {'MENU_ID': 'menu1', 'PRIVILEGE': '1', 'DISUSE_FLAG': 0},
                {'MENU_ID': 'flag0_readonly', 'PRIVILEGE': '2', 'DISUSE_FLAG': '1'},
            ],
        ]

        mock_create_data.return_value = {'menu_groups': []}

        get_menu_export_list(mock_objdbca, 'org1', 'ws1')

        permitted_menu_ids = mock_create_data.call_args[0][1]
        assert permitted_menu_ids == ['menu1', 'flag0_readonly']

    @patch('libs.export_import._get_target_menu_id_list')
    @patch('libs.export_import._create_export_menu_data')
    def test_flag_null_not_treated_as_internal_menu(self, mock_create_data, mock_get_target, mock_objdbca, mock_g_with_roles):
        """FLAG=NULL のメニューは内部メニュー（FLAG='0'）として扱わない"""
        mock_get_target.return_value = ['menu1', 'menu_null']

        mock_objdbca.table_select.side_effect = [
            # 1回目: T_DP_HIDE_MENU_LIST
            [],
            # 2回目: T_COMN_MENU（全メニューのFLAG取得）
            [
                {'MENU_ID': 'menu1', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': 'menu_null', 'EXPORT_PERMISSION_CHECK_FLG': None},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK（全紐付取得）
            [
                {'MENU_ID': 'menu1', 'PRIVILEGE': '1', 'DISUSE_FLAG': 0},
            ],
        ]

        mock_create_data.return_value = {'menu_groups': []}

        get_menu_export_list(mock_objdbca, 'org1', 'ws1')

        permitted_menu_ids = mock_create_data.call_args[0][1]
        # menu_null は FLAG=NULL（通常メニュー扱い）で権限がないので含まれない
        assert permitted_menu_ids == ['menu1']


class TestGetExcelBulkExportList:
    """
    get_excel_bulk_export_list() のテスト

    Excel一括エクスポートの対象メニューリスト取得
    すべての権限レベル（PRIVILEGE='0', '1', '2'）のメニューを返すことを確認
    """

    @patch('libs.export_import._get_target_menu_id_list')
    @patch('libs.export_import._create_export_menu_data')
    def test_includes_all_permission_levels(self, mock_create_data, mock_get_target, mock_objdbca, mock_g_with_roles):
        """すべての権限レベル（PRIVILEGE='0', '1', '2'）のメニューが返される"""
        mock_get_target.return_value = ['menu1', 'menu2', 'menu3']

        # T_COMN_ROLE_MENU_LINK: PRIVILEGE IN [0, 1, 2] すべて
        mock_objdbca.table_select.return_value = [
            {'MENU_ID': 'menu1', 'PRIVILEGE': 0},
            {'MENU_ID': 'menu2', 'PRIVILEGE': 1},
            {'MENU_ID': 'menu3', 'PRIVILEGE': 2},  # 閲覧のみも含まれる
        ]

        mock_create_data.return_value = {'menu_groups': []}

        get_excel_bulk_export_list(mock_objdbca, 'org1', 'ws1')

        call_args = mock_create_data.call_args[0]
        menu_ids = call_args[1]

        # すべての権限レベルのメニューが含まれる
        assert 'menu1' in menu_ids
        assert 'menu2' in menu_ids
        assert 'menu3' in menu_ids  # PRIVILEGE='2' も含まれる
        assert len(menu_ids) == 3


class TestGetDeniedMenuRestSet:
    """get_denied_menu_rest_set() のテスト"""

    def test_empty_list(self, mock_objdbca, mock_g_with_roles):
        """空リストの場合は空setを返し、DBアクセスしない"""
        assert get_denied_menu_rest_set(mock_objdbca, []) == set()
        mock_objdbca.table_select.assert_not_called()

    def test_denied_menus(self, mock_objdbca, mock_g_with_roles):
        """書き込み権限のないメニューのみ返す（存在しないメニュー、FLAG=0 のメニューは対象外）"""
        mock_objdbca.table_select.side_effect = [
            # 1回目: T_COMN_MENU（new_menu は存在しない）
            [
                {'MENU_ID': '10101', 'MENU_NAME_REST': 'menu1'},
                {'MENU_ID': '10102', 'MENU_NAME_REST': 'menu2'},
                {'MENU_ID': '10203', 'MENU_NAME_REST': 'menu_flag0'},
            ],
            # 2回目: T_COMN_MENU (_get_write_permission_menu_id_list 内)
            [
                {'MENU_ID': '10101', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': '10102', 'EXPORT_PERMISSION_CHECK_FLG': '1'},
                {'MENU_ID': '10203', 'EXPORT_PERMISSION_CHECK_FLG': '0'},
            ],
            # 3回目: T_COMN_ROLE_MENU_LINK（10101のみ権限あり）
            [
                {'MENU_ID': '10101', 'PRIVILEGE': '1'},
            ],
        ]

        result = get_denied_menu_rest_set(mock_objdbca, ['menu1', 'menu2', 'menu_flag0', 'new_menu'])

        assert result == {'menu2'}


class TestMaskExportFileData:
    """_mask_export_file_data() のテスト"""

    @staticmethod
    def _objmenu():
        mock_objmenu = MagicMock()
        mock_objmenu.get_table_name.return_value = 'T_MENU_EXPORT_IMPORT'
        mock_objmenu.get_primary_key.return_value = 'EXECUTION_NO'
        mock_objmenu.get_rest_key.return_value = 'execution_no'
        return mock_objmenu

    @staticmethod
    def _item(key, record_id):
        return {'parameter': {key: record_id}, 'file': {'file_name': 'base64data', 'execution_log': 'base64log'}}

    @patch('libs.menu_filter.get_denied_menu_rest_set')
    def test_mask_denied_and_unidentified_records(self, mock_denied, mock_objdbca, mock_g_with_roles):
        """権限のないメニューを含むレコード、対象メニューを特定できないレコードのファイルデータを除外する"""
        mock_objdbca.table_select.return_value = [
            {'EXECUTION_NO': 'e1', 'EXECUTION_TYPE': '1', 'JSON_STORAGE_ITEM': json.dumps({'menu': ['menu1']})},
            {'EXECUTION_NO': 'e2', 'EXECUTION_TYPE': '1', 'JSON_STORAGE_ITEM': json.dumps({'menu': ['menu1', 'menu2']})},
            {'EXECUTION_NO': 'i1', 'EXECUTION_TYPE': '2', 'JSON_STORAGE_ITEM': 'menu1'},
            {'EXECUTION_NO': 'i2', 'EXECUTION_TYPE': '2', 'JSON_STORAGE_ITEM': 'menu2'},
            {'EXECUTION_NO': 'x1', 'EXECUTION_TYPE': '1', 'JSON_STORAGE_ITEM': None},
        ]
        mock_denied.return_value = {'menu2'}
        result = [self._item('execution_no', rid) for rid in ['e1', 'e2', 'i1', 'i2', 'x1']]

        _mask_export_file_data(mock_objdbca, self._objmenu(), result)

        assert [bool(item['file']) for item in result] == [True, False, True, False, False]
        # 全レコードの対象メニューをまとめて1回で判定する
        mock_denied.assert_called_once()
        assert sorted(mock_denied.call_args[0][1]) == ['menu1', 'menu2']
        # 廃止済みレコードも対象（DISUSE_FLAG で絞り込まない）
        call_args = mock_objdbca.table_select.call_args[0]
        assert call_args[0] == 'T_MENU_EXPORT_IMPORT'
        assert 'DISUSE_FLAG' not in call_args[1]
        assert call_args[2] == [['e1', 'e2', 'i1', 'i2', 'x1']]

    @patch('libs.menu_filter.get_denied_menu_rest_set')
    def test_journal(self, mock_denied, mock_objdbca, mock_g_with_roles):
        """履歴の場合は _JNL テーブルを JOURNAL_SEQ_NO で検索する"""
        mock_objdbca.table_select.return_value = [
            {'JOURNAL_SEQ_NO': 'j1', 'EXECUTION_TYPE': '1', 'JSON_STORAGE_ITEM': json.dumps({'menu': ['menu2']})},
        ]
        mock_denied.return_value = {'menu2'}
        result = [self._item('journal_id', 'j1')]

        _mask_export_file_data(mock_objdbca, self._objmenu(), result, journal=True)

        assert result[0]['file'] == {}
        call_args = mock_objdbca.table_select.call_args[0]
        assert call_args[0] == 'T_MENU_EXPORT_IMPORT_JNL'
        assert 'JOURNAL_SEQ_NO' in call_args[1]

    def test_empty_result(self, mock_objdbca, mock_g_with_roles):
        """結果が0件の場合はDBアクセスしない"""
        _mask_export_file_data(mock_objdbca, self._objmenu(), [])
        mock_objdbca.table_select.assert_not_called()


class TestRestFilterMaskTarget:
    """rest_filter() / rest_filter_journal() でファイルデータ除外を行う対象の確認"""

    @pytest.mark.parametrize('menu, base64_file_flg, expected', [
        ('menu_export_import_list', True, True),
        ('menu_export_import_list', False, False),
        ('bulk_excel_export_import_list', True, False),
    ])
    @patch('libs.menu_filter._mask_export_file_data')
    @patch('libs.menu_filter.load_table')
    def test_rest_filter(self, mock_load_table, mock_mask, menu, base64_file_flg, expected, mock_objdbca, mock_g_with_roles):
        mock_objmenu = mock_load_table.loadTable.return_value
        mock_objmenu.get_sheet_type.return_value = '0'
        mock_objmenu.rest_filter.return_value = ('000-00000', [{'parameter': {}, 'file': {}}], '')

        rest_filter(mock_objdbca, menu, {}, base64_file_flg=base64_file_flg)

        assert mock_mask.called is expected

    @pytest.mark.parametrize('menu, base64_file_flg, expected', [
        ('menu_export_import_list', True, True),
        ('menu_export_import_list', False, False),
        ('bulk_excel_export_import_list', True, False),
    ])
    @patch('libs.menu_filter._mask_export_file_data')
    @patch('libs.menu_filter.load_table')
    def test_rest_filter_journal(self, mock_load_table, mock_mask, menu, base64_file_flg, expected, mock_objdbca, mock_g_with_roles):
        mock_objmenu = mock_load_table.loadTable.return_value
        mock_objmenu.rest_filter.return_value = ('000-00000', [{'parameter': {}, 'file': {}}], '')

        rest_filter_journal(mock_objdbca, menu, 'uuid1', base64_file_flg=base64_file_flg)

        assert mock_mask.called is expected
        if expected:
            assert mock_mask.call_args.kwargs.get('journal') is True
