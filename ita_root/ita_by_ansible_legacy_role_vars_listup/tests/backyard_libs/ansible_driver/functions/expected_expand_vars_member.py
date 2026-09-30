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

"""展開処理（多段変数メンバー管理の行を親子の木に組み、多段変数配列組合せ管理の代入欄の候補を作る処理）の期待値

test_expand_vars_member_equivalence.py が使う。シナリオ名はテストのシナリオ名と同じ。
- input: nest_vars_mem_records（多段変数メンバー管理の行）/ mem_max_col_records（変数ネスト管理の行）
- result: 改修前の実装が作った代入欄の候補の一覧（順序込み）

改修前の実装（コミット aa7665ed）の出力を、移行時に 1 回だけ書き出したもの。比較の基準。
**製品コードに合わせて直してはいけない**（直すと比較の基準としての意味が無くなる）。仕様を変えるときだけ手で直す。
書き出し元: 改修前の実装の写しを含んでいた最後の tests（コミット 63c57a36 / rebase 後 f2089e42）で等価性テストを実行し、
テストが改修前の実装を呼ぶ入口で入力と結果を記録した。書き出し日: 2026-09-29。
各エントリの input は、テストが作る入力と同じであることをテストの最初に確かめる（入力を作るヘルパーが変わったら、ここが古いと分かる）。

経緯: Issue #3072
"""
import copy


# シナリオごとの入力と改修前の結果
EXPECTED = {
    'discarded_parent': {
        'input': {
            'nest_vars_mem_records': {
                'root': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'root', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '1', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'leaf': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'x', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/x', 'VRAS_NAME_ALIAS': 'alias_x', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'leaf', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'mc-0': {'MAX_COL_SEQ_ID': 'mc-0', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'root', 'MAX_COL_SEQ': 2, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
        },
        'result': [],
    },
    'dup_roots': {
        'input': {
            'nest_vars_mem_records': {
                'root-a': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                           'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                           'ARRAY_MEMBER_ID': 'root-a', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                           'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'root-b': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                           'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                           'ARRAY_MEMBER_ID': 'root-b', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                           'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'leaf': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'x', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/x', 'VRAS_NAME_ALIAS': 'alias_x', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'leaf', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'mc-0': {'MAX_COL_SEQ_ID': 'mc-0', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'root-a', 'MAX_COL_SEQ': 2, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'mc-1': {'MAX_COL_SEQ_ID': 'mc-1', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'root-b', 'MAX_COL_SEQ': 5, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf', 'COL_COMBINATION_MEMBER_ALIAS': '[0].x',
             'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf', 'COL_COMBINATION_MEMBER_ALIAS': '[1].x',
             'COL_SEQ_VALUE': '00000001'},
        ],
    },
    'dup_same_parent': {
        'input': {
            'nest_vars_mem_records': {
                'root': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'root', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'grp-a': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'grp', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/grp', 'VRAS_NAME_ALIAS': 'alias_grp', 'MAX_COL_SEQ': '0',
                          'ARRAY_MEMBER_ID': 'grp-a', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                          'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'grp-b': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'grp', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/grp', 'VRAS_NAME_ALIAS': 'alias_grp', 'MAX_COL_SEQ': '0',
                          'ARRAY_MEMBER_ID': 'grp-b', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                          'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'leaf': {'PARENT_VARS_KEY_ID': '2', 'VARS_KEY_ID': '3', 'VARS_NAME': 'leaf', 'ARRAY_NEST_LEVEL': '3', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/leaf', 'VRAS_NAME_ALIAS': 'alias_leaf', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'leaf', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'mc-0': {'MAX_COL_SEQ_ID': 'mc-0', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'root', 'MAX_COL_SEQ': 1, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf', 'COL_COMBINATION_MEMBER_ALIAS': '[0].grp.leaf',
             'COL_SEQ_VALUE': '00000000'},
        ],
    },
    'hidden_and_discarded': {
        'input': {
            'nest_vars_mem_records': {
                'root': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'root', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'hidden': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'hidden', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                           'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/hidden', 'VRAS_NAME_ALIAS': 'alias_hidden',
                           'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'hidden', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                           'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'shown': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '3', 'VARS_NAME': 'shown', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/shown', 'VRAS_NAME_ALIAS': 'alias_shown',
                          'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'shown', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                          'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'gone': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '4', 'VARS_NAME': 'gone', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/gone', 'VRAS_NAME_ALIAS': 'alias_gone', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'gone', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '1', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'mc-0': {'MAX_COL_SEQ_ID': 'mc-0', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'root', 'MAX_COL_SEQ': 1, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'shown', 'COL_COMBINATION_MEMBER_ALIAS': '[0].shown',
             'COL_SEQ_VALUE': '00000000'},
        ],
    },
    'insert_upper_member_after': {
        'input': {
            'nest_vars_mem_records': {
                'member-1': {'PARENT_VARS_KEY_ID': 0, 'VARS_KEY_ID': 1, 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': 1, 'ASSIGN_SEQ_NEED': 0,
                             'COL_SEQ_NEED': 0, 'MEMBER_DISP': 0, 'VRAS_NAME_PATH': '0', 'VRAS_NAME_ALIAS': '0', 'MAX_COL_SEQ': 1,
                             'ARRAY_MEMBER_ID': 'member-1', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'member-2': {'PARENT_VARS_KEY_ID': 1, 'VARS_KEY_ID': 2, 'VARS_NAME': 'name', 'ARRAY_NEST_LEVEL': 2, 'ASSIGN_SEQ_NEED': 0,
                             'COL_SEQ_NEED': 1, 'MEMBER_DISP': 1, 'VRAS_NAME_PATH': '0.name', 'VRAS_NAME_ALIAS': '0.name', 'MAX_COL_SEQ': 0,
                             'ARRAY_MEMBER_ID': 'member-2', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'member-3': {'PARENT_VARS_KEY_ID': 1, 'VARS_KEY_ID': 3, 'VARS_NAME': 'os', 'ARRAY_NEST_LEVEL': 2, 'ASSIGN_SEQ_NEED': 0,
                             'COL_SEQ_NEED': 1, 'MEMBER_DISP': 1, 'VRAS_NAME_PATH': '0.os', 'VRAS_NAME_ALIAS': '0.os', 'MAX_COL_SEQ': 0,
                             'ARRAY_MEMBER_ID': 'member-3', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'member-4': {'PARENT_VARS_KEY_ID': 1, 'VARS_KEY_ID': 4, 'VARS_NAME': 'ports', 'ARRAY_NEST_LEVEL': 2, 'ASSIGN_SEQ_NEED': 0,
                             'COL_SEQ_NEED': 0, 'MEMBER_DISP': 0, 'VRAS_NAME_PATH': '0.ports', 'VRAS_NAME_ALIAS': '0.ports', 'MAX_COL_SEQ': 0,
                             'ARRAY_MEMBER_ID': 'member-4', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'member-5': {'PARENT_VARS_KEY_ID': 4, 'VARS_KEY_ID': 5, 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': 3, 'ASSIGN_SEQ_NEED': 0,
                             'COL_SEQ_NEED': 0, 'MEMBER_DISP': 0, 'VRAS_NAME_PATH': '0.ports.0', 'VRAS_NAME_ALIAS': '0.ports', 'MAX_COL_SEQ': 1,
                             'ARRAY_MEMBER_ID': 'member-5', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'member-6': {'PARENT_VARS_KEY_ID': 5, 'VARS_KEY_ID': 6, 'VARS_NAME': 'http', 'ARRAY_NEST_LEVEL': 4, 'ASSIGN_SEQ_NEED': 0,
                             'COL_SEQ_NEED': 1, 'MEMBER_DISP': 1, 'VRAS_NAME_PATH': '0.ports.0.http', 'VRAS_NAME_ALIAS': '0.ports.http',
                             'MAX_COL_SEQ': 0, 'ARRAY_MEMBER_ID': 'member-6', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                             'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'mc-0': {'MAX_COL_SEQ_ID': 'mc-0', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-1', 'MAX_COL_SEQ': 2, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'mc-1': {'MAX_COL_SEQ_ID': 'mc-1', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-5', 'MAX_COL_SEQ': 3, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-2', 'COL_COMBINATION_MEMBER_ALIAS': '[0].name',
             'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-3', 'COL_COMBINATION_MEMBER_ALIAS': '[0].os',
             'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-6',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].ports[0].http', 'COL_SEQ_VALUE': '0000000000000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-6',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].ports[1].http', 'COL_SEQ_VALUE': '0000000000000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-6',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].ports[2].http', 'COL_SEQ_VALUE': '0000000000000002'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-2', 'COL_COMBINATION_MEMBER_ALIAS': '[1].name',
             'COL_SEQ_VALUE': '00000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-3', 'COL_COMBINATION_MEMBER_ALIAS': '[1].os',
             'COL_SEQ_VALUE': '00000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-6',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].ports[0].http', 'COL_SEQ_VALUE': '0000000100000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-6',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].ports[1].http', 'COL_SEQ_VALUE': '0000000100000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'member-6',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].ports[2].http', 'COL_SEQ_VALUE': '0000000100000002'},
        ],
    },
    'level1': {
        'input': {
            'nest_vars_mem_records': {
                'arr-0': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                          'ARRAY_MEMBER_ID': 'arr-0', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                          'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'leaf': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'value', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/value', 'VRAS_NAME_ALIAS': 'alias_value',
                         'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'leaf', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'mc-0': {'MAX_COL_SEQ_ID': 'mc-0', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'arr-0', 'MAX_COL_SEQ': 2, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf', 'COL_COMBINATION_MEMBER_ALIAS': '[0].value',
             'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf', 'COL_COMBINATION_MEMBER_ALIAS': '[1].value',
             'COL_SEQ_VALUE': '00000001'},
        ],
    },
    'level2': {
        'input': {
            'nest_vars_mem_records': {
                'arr-0': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                          'ARRAY_MEMBER_ID': 'arr-0', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                          'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'grp-0': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'items', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/items', 'VRAS_NAME_ALIAS': 'alias_items',
                          'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'grp-0', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                          'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'arr-1': {'PARENT_VARS_KEY_ID': '2', 'VARS_KEY_ID': '3', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '3', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                          'ARRAY_MEMBER_ID': 'arr-1', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                          'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'leaf': {'PARENT_VARS_KEY_ID': '3', 'VARS_KEY_ID': '4', 'VARS_NAME': 'value', 'ARRAY_NEST_LEVEL': '4', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/value', 'VRAS_NAME_ALIAS': 'alias_value',
                         'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'leaf', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'mc-0': {'MAX_COL_SEQ_ID': 'mc-0', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'arr-0', 'MAX_COL_SEQ': 2, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'mc-1': {'MAX_COL_SEQ_ID': 'mc-1', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'arr-1', 'MAX_COL_SEQ': 3, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[0].value', 'COL_SEQ_VALUE': '0000000000000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[1].value', 'COL_SEQ_VALUE': '0000000000000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[2].value', 'COL_SEQ_VALUE': '0000000000000002'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[0].value', 'COL_SEQ_VALUE': '0000000100000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[1].value', 'COL_SEQ_VALUE': '0000000100000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[2].value', 'COL_SEQ_VALUE': '0000000100000002'},
        ],
    },
    'level3': {
        'input': {
            'nest_vars_mem_records': {
                'arr-0': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                          'ARRAY_MEMBER_ID': 'arr-0', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                          'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'grp-0': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'items', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/items', 'VRAS_NAME_ALIAS': 'alias_items',
                          'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'grp-0', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                          'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'arr-1': {'PARENT_VARS_KEY_ID': '2', 'VARS_KEY_ID': '3', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '3', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                          'ARRAY_MEMBER_ID': 'arr-1', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                          'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'grp-1': {'PARENT_VARS_KEY_ID': '3', 'VARS_KEY_ID': '4', 'VARS_NAME': 'items', 'ARRAY_NEST_LEVEL': '4', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/items', 'VRAS_NAME_ALIAS': 'alias_items',
                          'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'grp-1', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                          'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'arr-2': {'PARENT_VARS_KEY_ID': '4', 'VARS_KEY_ID': '5', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '5', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                          'ARRAY_MEMBER_ID': 'arr-2', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                          'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'leaf': {'PARENT_VARS_KEY_ID': '5', 'VARS_KEY_ID': '6', 'VARS_NAME': 'value', 'ARRAY_NEST_LEVEL': '6', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/value', 'VRAS_NAME_ALIAS': 'alias_value',
                         'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'leaf', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'mc-0': {'MAX_COL_SEQ_ID': 'mc-0', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'arr-0', 'MAX_COL_SEQ': 2, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'mc-1': {'MAX_COL_SEQ_ID': 'mc-1', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'arr-1', 'MAX_COL_SEQ': 3, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'mc-2': {'MAX_COL_SEQ_ID': 'mc-2', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'arr-2', 'MAX_COL_SEQ': 4, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[0].items[0].value', 'COL_SEQ_VALUE': '000000000000000000000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[0].items[1].value', 'COL_SEQ_VALUE': '000000000000000000000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[0].items[2].value', 'COL_SEQ_VALUE': '000000000000000000000002'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[0].items[3].value', 'COL_SEQ_VALUE': '000000000000000000000003'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[1].items[0].value', 'COL_SEQ_VALUE': '000000000000000100000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[1].items[1].value', 'COL_SEQ_VALUE': '000000000000000100000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[1].items[2].value', 'COL_SEQ_VALUE': '000000000000000100000002'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[1].items[3].value', 'COL_SEQ_VALUE': '000000000000000100000003'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[2].items[0].value', 'COL_SEQ_VALUE': '000000000000000200000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[2].items[1].value', 'COL_SEQ_VALUE': '000000000000000200000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[2].items[2].value', 'COL_SEQ_VALUE': '000000000000000200000002'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].items[2].items[3].value', 'COL_SEQ_VALUE': '000000000000000200000003'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[0].items[0].value', 'COL_SEQ_VALUE': '000000010000000000000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[0].items[1].value', 'COL_SEQ_VALUE': '000000010000000000000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[0].items[2].value', 'COL_SEQ_VALUE': '000000010000000000000002'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[0].items[3].value', 'COL_SEQ_VALUE': '000000010000000000000003'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[1].items[0].value', 'COL_SEQ_VALUE': '000000010000000100000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[1].items[1].value', 'COL_SEQ_VALUE': '000000010000000100000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[1].items[2].value', 'COL_SEQ_VALUE': '000000010000000100000002'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[1].items[3].value', 'COL_SEQ_VALUE': '000000010000000100000003'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[2].items[0].value', 'COL_SEQ_VALUE': '000000010000000200000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[2].items[1].value', 'COL_SEQ_VALUE': '000000010000000200000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[2].items[2].value', 'COL_SEQ_VALUE': '000000010000000200000002'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].items[2].items[3].value', 'COL_SEQ_VALUE': '000000010000000200000003'},
        ],
    },
    'no_max_col_row': {
        'input': {
            'nest_vars_mem_records': {
                'root': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'root', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'leaf': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'x', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/x', 'VRAS_NAME_ALIAS': 'alias_x', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'leaf', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {},
        },
        'result': [],
    },
    'none_order': {
        'input': {
            'nest_vars_mem_records': {
                'root': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': None, 'VARS_NAME': 'r', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/r', 'VRAS_NAME_ALIAS': 'alias_r', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'root', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'leaf': {'PARENT_VARS_KEY_ID': None, 'VARS_KEY_ID': '2', 'VARS_NAME': 'child', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/child', 'VRAS_NAME_ALIAS': 'alias_child',
                         'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'leaf', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {},
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf', 'COL_COMBINATION_MEMBER_ALIAS': 'r.child',
             'COL_SEQ_VALUE': ''},
        ],
    },
    'orphan': {
        'input': {
            'nest_vars_mem_records': {
                'm-1': {'PARENT_VARS_KEY_ID': '99', 'VARS_KEY_ID': '5', 'VARS_NAME': 'lonely', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                        'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/lonely', 'VRAS_NAME_ALIAS': 'alias_lonely',
                        'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'm-1', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                        'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {},
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'm-1', 'COL_COMBINATION_MEMBER_ALIAS': 'lonely',
             'COL_SEQ_VALUE': ''},
        ],
    },
    'parent_deeper': {
        'input': {
            'nest_vars_mem_records': {
                'child': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'child', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                          'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/child', 'VRAS_NAME_ALIAS': 'alias_child',
                          'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'child', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                          'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'parent': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'parent', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                           'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/parent', 'VRAS_NAME_ALIAS': 'alias_parent',
                           'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'parent', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0',
                           'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {},
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'child', 'COL_COMBINATION_MEMBER_ALIAS': 'child',
             'COL_SEQ_VALUE': ''},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'parent', 'COL_COMBINATION_MEMBER_ALIAS': 'parent',
             'COL_SEQ_VALUE': ''},
        ],
    },
    'skipped_level': {
        'input': {
            'nest_vars_mem_records': {
                'root': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'root', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'leaf': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'x', 'ARRAY_NEST_LEVEL': '3', 'ASSIGN_SEQ_NEED': '0',
                         'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/x', 'VRAS_NAME_ALIAS': 'alias_x', 'MAX_COL_SEQ': '0',
                         'ARRAY_MEMBER_ID': 'leaf', 'MVMT_VAR_LINK_ID': 'link-1', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                         'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'mc-0': {'MAX_COL_SEQ_ID': 'mc-0', 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'root', 'MAX_COL_SEQ': 2, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf', 'COL_COMBINATION_MEMBER_ALIAS': '[0].x',
             'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-1', 'ARRAY_MEMBER_ID': 'leaf', 'COL_COMBINATION_MEMBER_ALIAS': '[1].x',
             'COL_SEQ_VALUE': '00000001'},
        ],
    },
    'two_links': {
        'input': {
            'nest_vars_mem_records': {
                'a-root': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                           'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                           'ARRAY_MEMBER_ID': 'a-root', 'MVMT_VAR_LINK_ID': 'link-a', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                           'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'a-leaf': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'x', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                           'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/x', 'VRAS_NAME_ALIAS': 'alias_x', 'MAX_COL_SEQ': '0',
                           'ARRAY_MEMBER_ID': 'a-leaf', 'MVMT_VAR_LINK_ID': 'link-a', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                           'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'b-root': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                           'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                           'ARRAY_MEMBER_ID': 'b-root', 'MVMT_VAR_LINK_ID': 'link-b', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                           'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'b-leaf': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'y', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                           'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/y', 'VRAS_NAME_ALIAS': 'alias_y', 'MAX_COL_SEQ': '0',
                           'ARRAY_MEMBER_ID': 'b-leaf', 'MVMT_VAR_LINK_ID': 'link-b', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                           'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'mc-0': {'MAX_COL_SEQ_ID': 'mc-0', 'MVMT_VAR_LINK_ID': 'link-a', 'ARRAY_MEMBER_ID': 'a-root', 'MAX_COL_SEQ': 1, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'mc-1': {'MAX_COL_SEQ_ID': 'mc-1', 'MVMT_VAR_LINK_ID': 'link-b', 'ARRAY_MEMBER_ID': 'b-root', 'MAX_COL_SEQ': 2, 'DISUSE_FLAG': '0',
                         'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-a', 'ARRAY_MEMBER_ID': 'a-leaf', 'COL_COMBINATION_MEMBER_ALIAS': '[0].x',
             'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-b', 'ARRAY_MEMBER_ID': 'b-leaf', 'COL_COMBINATION_MEMBER_ALIAS': '[0].y',
             'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-b', 'ARRAY_MEMBER_ID': 'b-leaf', 'COL_COMBINATION_MEMBER_ALIAS': '[1].y',
             'COL_SEQ_VALUE': '00000001'},
        ],
    },
}


def get_expected(scenario):
    """シナリオの期待値（入力と改修前の結果）を深いコピーで返す（テストが書き換えても次のテストに漏れないように）"""
    return copy.deepcopy(EXPECTED[scenario])
