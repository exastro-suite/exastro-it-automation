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

"""突き合わせの部品（_a_minus_b / _a_and_b）と展開処理の期待値

test_nest_vars_member_table_equivalence.py が使う。キーは「テスト関数名から test_ を除いたもの（パラメータ付き）:呼んだ処理」。
- input: list_a / list_b / options（突き合わせの部品）、または nest_vars_mem_records / mem_max_col_records（展開処理）
- result: 改修前の実装の結果

改修前の実装（コミット aa7665ed）の出力を、移行時に 1 回だけ書き出したもの。比較の基準。
**製品コードに合わせて直してはいけない**（直すと比較の基準としての意味が無くなる）。仕様を変えるときだけ手で直す。
書き出し元: 改修前の実装の写しを含んでいた最後の tests（コミット 63c57a36 / rebase 後 f2089e42）で等価性テストを実行し、
テストが改修前の実装を呼ぶ入口で入力と結果を記録した。書き出し日: 2026-09-29。
各エントリの input は、テストが作る入力と同じであることをテストの最初に確かめる（入力を作るヘルパーが変わったら、ここが古いと分かる）。

経緯: Issue #3072
"""
import copy


# ケースごとの入力と改修前の結果
EXPECTED = {
    'a_and_b_matches_legacy_for_intersection:_a_and_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '2', 'VARS_NAME': 'member2', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member2', 'VRAS_NAME_ALIAS': 'alias_member2', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm2', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '3', 'VARS_NAME': 'member3', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member3', 'VRAS_NAME_ALIAS': 'alias_member3', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm3', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '2', 'VARS_NAME': 'member2', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member2', 'VRAS_NAME_ALIAS': 'alias_member2', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm2', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '9', 'VARS_NAME': 'member9', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member9', 'VRAS_NAME_ALIAS': 'alias_member9', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm9', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '2', 'VARS_NAME': 'member2', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member2', 'VRAS_NAME_ALIAS': 'alias_member2', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm2', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'a_and_b_merge_takes_first_match_like_legacy:_a_and_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '5', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'x1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '6', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'x2', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True, 'marge_vars_key_id': True},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '5', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'a_and_b_merges_same_vars_key_id_value_as_legacy:_a_and_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '7', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'x1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True, 'marge_vars_key_id': True},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '7', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'a_and_b_without_merge_does_not_touch_vars_key_id:_a_and_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '7', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'x1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'a_minus_b_keeps_duplicated_records_like_legacy:_a_minus_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm2', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm2', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'a_minus_b_matches_legacy_when_a_has_extra_records:_a_minus_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '2', 'VARS_NAME': 'member2', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member2', 'VRAS_NAME_ALIAS': 'alias_member2', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm2', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '3', 'VARS_NAME': 'member3', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member3', 'VRAS_NAME_ALIAS': 'alias_member3', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm3', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '4', 'VARS_NAME': 'member4', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member4', 'VRAS_NAME_ALIAS': 'alias_member4', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm4', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '2', 'VARS_NAME': 'member2', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member2', 'VRAS_NAME_ALIAS': 'alias_member2', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm2', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '3', 'VARS_NAME': 'member3', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member3', 'VRAS_NAME_ALIAS': 'alias_member3', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm3', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '4', 'VARS_NAME': 'member4', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member4', 'VRAS_NAME_ALIAS': 'alias_member4', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm4', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'a_minus_b_matches_legacy_when_b_has_extra_records:_a_minus_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '9', 'VARS_NAME': 'member9', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member9', 'VRAS_NAME_ALIAS': 'alias_member9', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm9', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [],
    },
    'a_minus_b_matches_legacy_when_nothing_matches:_a_minus_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '2', 'VARS_NAME': 'member2', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member2', 'VRAS_NAME_ALIAS': 'alias_member2', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm2', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '8', 'VARS_NAME': 'other8', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/other8', 'VRAS_NAME_ALIAS': 'alias_other8', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm8', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '2', 'VARS_NAME': 'member2', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member2', 'VRAS_NAME_ALIAS': 'alias_member2', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm2', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'expand_vars_member_matches_legacy_for_multiple_links:expand_vars_member': {
        'input': {
            'nest_vars_mem_records': {
                'array-0': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                            'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                            'ARRAY_MEMBER_ID': 'array-0', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                            'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'member-0-0': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '2',
                               'ASSIGN_SEQ_NEED': '0', 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1',
                               'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'member-0-0',
                               'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                               'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'member-0-1': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '3', 'VARS_NAME': 'member2', 'ARRAY_NEST_LEVEL': '2',
                               'ASSIGN_SEQ_NEED': '0', 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member2',
                               'VRAS_NAME_ALIAS': 'alias_member2', 'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'member-0-1',
                               'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                               'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'array-1': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                            'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                            'ARRAY_MEMBER_ID': 'array-1', 'MVMT_VAR_LINK_ID': 'link-0002', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                            'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'member-1-0': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '2',
                               'ASSIGN_SEQ_NEED': '0', 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1',
                               'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'member-1-0',
                               'MVMT_VAR_LINK_ID': 'link-0002', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                               'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'member-1-1': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '3', 'VARS_NAME': 'member2', 'ARRAY_NEST_LEVEL': '2',
                               'ASSIGN_SEQ_NEED': '0', 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member2',
                               'VRAS_NAME_ALIAS': 'alias_member2', 'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'member-1-1',
                               'MVMT_VAR_LINK_ID': 'link-0002', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                               'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'array-0': {'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'array-0', 'MAX_COL_SEQ': 2},
                'array-1': {'MVMT_VAR_LINK_ID': 'link-0002', 'ARRAY_MEMBER_ID': 'array-1', 'MAX_COL_SEQ': 2},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'member-0-0',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].member1', 'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'member-0-1',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].member2', 'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'member-0-0',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].member1', 'COL_SEQ_VALUE': '00000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'member-0-1',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].member2', 'COL_SEQ_VALUE': '00000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0002', 'ARRAY_MEMBER_ID': 'member-1-0',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].member1', 'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0002', 'ARRAY_MEMBER_ID': 'member-1-1',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].member2', 'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0002', 'ARRAY_MEMBER_ID': 'member-1-0',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].member1', 'COL_SEQ_VALUE': '00000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0002', 'ARRAY_MEMBER_ID': 'member-1-1',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].member2', 'COL_SEQ_VALUE': '00000001'},
        ],
    },
    'expand_vars_member_matches_legacy_for_three_levels:expand_vars_member': {
        'input': {
            'nest_vars_mem_records': {
                'array-0': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                            'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                            'ARRAY_MEMBER_ID': 'array-0', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                            'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'array-1': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                            'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                            'ARRAY_MEMBER_ID': 'array-1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                            'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'leaf-0': {'PARENT_VARS_KEY_ID': '2', 'VARS_KEY_ID': '3', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '3', 'ASSIGN_SEQ_NEED': '0',
                           'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1',
                           'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'leaf-0', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0',
                           'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'array-0': {'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'array-0', 'MAX_COL_SEQ': 2},
                'array-1': {'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'array-1', 'MAX_COL_SEQ': 2},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'leaf-0',
             'COL_COMBINATION_MEMBER_ALIAS': '[0][0].member1', 'COL_SEQ_VALUE': '0000000000000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'leaf-0',
             'COL_COMBINATION_MEMBER_ALIAS': '[0][1].member1', 'COL_SEQ_VALUE': '0000000000000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'leaf-0',
             'COL_COMBINATION_MEMBER_ALIAS': '[1][0].member1', 'COL_SEQ_VALUE': '0000000100000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'leaf-0',
             'COL_COMBINATION_MEMBER_ALIAS': '[1][1].member1', 'COL_SEQ_VALUE': '0000000100000001'},
        ],
    },
    'expand_vars_member_matches_legacy_for_two_levels:expand_vars_member': {
        'input': {
            'nest_vars_mem_records': {
                'array-0': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                            'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0', 'MAX_COL_SEQ': '0',
                            'ARRAY_MEMBER_ID': 'array-0', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                            'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'member-0-0': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '2',
                               'ASSIGN_SEQ_NEED': '0', 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1',
                               'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'member-0-0',
                               'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                               'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'member-0-1': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '3', 'VARS_NAME': 'member2', 'ARRAY_NEST_LEVEL': '2',
                               'ASSIGN_SEQ_NEED': '0', 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member2',
                               'VRAS_NAME_ALIAS': 'alias_member2', 'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'member-0-1',
                               'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                               'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'array-0': {'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'array-0', 'MAX_COL_SEQ': 2},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'member-0-0',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].member1', 'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'member-0-1',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].member2', 'COL_SEQ_VALUE': '00000000'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'member-0-0',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].member1', 'COL_SEQ_VALUE': '00000001'},
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'member-0-1',
             'COL_COMBINATION_MEMBER_ALIAS': '[1].member2', 'COL_SEQ_VALUE': '00000001'},
        ],
    },
    'expand_vars_member_picks_first_element_on_own_key_collision:expand_vars_member': {
        'input': {
            'nest_vars_mem_records': {
                'array-first': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                                'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0',
                                'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'array-first', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0',
                                'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'array-second': {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': '0', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '0', 'VRAS_NAME_PATH': 'path/0', 'VRAS_NAME_ALIAS': 'alias_0',
                                 'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'array-second', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0',
                                 'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
                'leaf-0': {'PARENT_VARS_KEY_ID': '1', 'VARS_KEY_ID': '2', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '2', 'ASSIGN_SEQ_NEED': '0',
                           'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1',
                           'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'leaf-0', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0',
                           'LAST_UPDATE_USER': 'old_user_id', 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            },
            'mem_max_col_records': {
                'array-first': {'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'array-first', 'MAX_COL_SEQ': 1},
                'array-second': {'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'array-second', 'MAX_COL_SEQ': 3},
            },
        },
        'result': [
            {'COL_SEQ_COMBINATION_ID': None, 'MVMT_VAR_LINK_ID': 'link-0001', 'ARRAY_MEMBER_ID': 'leaf-0',
             'COL_COMBINATION_MEMBER_ALIAS': '[0].member1', 'COL_SEQ_VALUE': '00000000'},
        ],
    },
    'matches_legacy_with_ignore_vars_key_id_false[_a_and_b]:_a_and_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '7', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'x1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': False},
        },
        'result': [],
    },
    'matches_legacy_with_ignore_vars_key_id_false[_a_minus_b]:_a_minus_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '7', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'x1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': False},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'missing_column_is_treated_as_none_like_legacy:_a_minus_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'MAX_COL_SEQ': '0', 'ARRAY_MEMBER_ID': 'x1',
                 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '0',
             'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'type_difference_is_absorbed_like_legacy[both_int]:_a_and_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': 10,
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': 10,
                 'ARRAY_MEMBER_ID': 'x1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': 10,
             'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'type_difference_is_absorbed_like_legacy[both_int]:_a_minus_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': 10,
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': 10,
                 'ARRAY_MEMBER_ID': 'x1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [],
    },
    'type_difference_is_absorbed_like_legacy[db_int_vs_str]:_a_and_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': 1,
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '1',
                 'ARRAY_MEMBER_ID': 'x1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': 1,
             'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'type_difference_is_absorbed_like_legacy[db_int_vs_str]:_a_minus_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': 1,
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '1',
                 'ARRAY_MEMBER_ID': 'x1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [],
    },
    'type_difference_is_absorbed_like_legacy[str_vs_db_int]:_a_and_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '1',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': 1,
                 'ARRAY_MEMBER_ID': 'x1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [
            {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
             'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '1',
             'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
             'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
        ],
    },
    'type_difference_is_absorbed_like_legacy[str_vs_db_int]:_a_minus_b': {
        'input': {
            'list_a': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': '1',
                 'ARRAY_MEMBER_ID': 'm1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'list_b': [
                {'PARENT_VARS_KEY_ID': '0', 'VARS_KEY_ID': '1', 'VARS_NAME': 'member1', 'ARRAY_NEST_LEVEL': '1', 'ASSIGN_SEQ_NEED': '0',
                 'COL_SEQ_NEED': '0', 'MEMBER_DISP': '1', 'VRAS_NAME_PATH': 'path/member1', 'VRAS_NAME_ALIAS': 'alias_member1', 'MAX_COL_SEQ': 1,
                 'ARRAY_MEMBER_ID': 'x1', 'MVMT_VAR_LINK_ID': 'link-0001', 'DISUSE_FLAG': '0', 'LAST_UPDATE_USER': 'old_user_id',
                 'LAST_UPDATE_TIMESTAMP': '2026-01-01 00:00:00'},
            ],
            'options': {'ignore_vars_key_id': True},
        },
        'result': [],
    },
}


def get_expected(case):
    """ケースの期待値（入力と改修前の結果）を深いコピーで返す（テストが書き換えても次のテストに漏れないように）"""
    return copy.deepcopy(EXPECTED[case])
