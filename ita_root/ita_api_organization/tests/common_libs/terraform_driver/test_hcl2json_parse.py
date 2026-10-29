#   Copyright 2023 NEC Corporation
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

from types import SimpleNamespace
from unittest.mock import patch
import re as std_re

import pytest
from flask import Flask, g

from common_libs.terraform_driver.common.Hcl2Json import HCL2JSONParse


class DummyReader:
    def __init__(self, content):
        self.content = content

    def open(self, path):
        self.path = path

    def read(self):
        return self.content

    def close(self):
        pass


HCL_SAMPLE_ALLTYPES = '''
variable "string_var" {
  type = string
  default = "default_value"
}
variable "number_var" {
  type = number
  default = 10
}
variable "bool_var" {
  type = bool
  default = true
}
variable "list_var" {
  type = list(string)
  default = ["item1", "item2"]
}
variable "set_var" {
  type = set(string)
  default = ["item1", "item2"]
}
variable "map_var" {
  type = map(string)
  default = {
    key1 = "value1"
    key2 = "value2"
  }
}
variable "object_var" {
  type = object({
    name = string
    age = number
  })
  default = {
    name = "John"
    age = 30
  }
}
variable "tuple_var" {
  type = tuple([string, number, bool])
  default = ["item1", 10, true]
}
variable "any_var" {
  type = any
  default = "free_value"
}
variable "no_default_var" {
  type = string
}
variable "list_list_var" {
  type = list(list(string))
}
variable "list_tuple_var" {
  type = list(tuple([string, number]))
}
variable "list_object_var" {
  type = list(object({
    name = string
    age  = number
  }))
}
'''


# Terraform変数タイプごとの分類（Exastroマニュアル準拠）
#   https://ita-docs.exastro.org/ja/2.7/manuals/terraform_driver/terraform_common.html#terraform-common-variable-type
#   メンバー変数対象  : object, tuple  -> typeはdict形式で展開され、type_strにタイプ名が入る
#   代入順序対象      : list, set      -> typeは '${...}' 文字列、type_strにタイプ名が入る
#   どちらも対象外    : string, number, bool, map, any, タイプ記載なし -> typeは '${...}' 文字列、type_strにタイプ名が入る
#
# python-hcl2 v4.3.4 での出力形式を正とする
#   v4.3.4: 各タイプ要素は '${string}' 形式（例: object の値は '${string}'、tuple の要素は '${string}'）
EXPECTED_VARIABLES = [
    {
        # string: メンバー変数対象外 / 代入順序対象外
        'type': '${string}',
        'type_str': 'string',
        'variable': 'string_var',
        'default': 'default_value',
    },
    {
        # number: メンバー変数対象外 / 代入順序対象外
        'type': '${number}',
        'type_str': 'number',
        'variable': 'number_var',
        'default': 10,
    },
    {
        # bool: メンバー変数対象外 / 代入順序対象外
        'type': '${bool}',
        'type_str': 'bool',
        'variable': 'bool_var',
        'default': True,
    },
    {
        # list: 代入順序対象（メンバー変数対象外）
        'type': '${list(string)}',
        'type_str': 'list(string)',
        'variable': 'list_var',
        'default': ['item1', 'item2'],
    },
    {
        # set: 代入順序対象（メンバー変数対象外）
        'type': '${set(string)}',
        'type_str': 'set(string)',
        'variable': 'set_var',
        'default': ['item1', 'item2'],
    },
    {
        # map: メンバー変数対象外 / 代入順序対象外
        'type': '${map}',
        'type_str': 'map',
        'variable': 'map_var',
        'default': {'key1': 'value1', 'key2': 'value2'},
    },
    {
        # object: メンバー変数対象（typeはdictへ展開し、リーフは '${タイプ名}' 形式）
        'type': {'${object}': {'name': '${string}', 'age': '${number}'}},
        'type_str': 'object',
        'variable': 'object_var',
        'default': {'name': 'John', 'age': 30},
    },
    {
        # tuple: メンバー変数対象（typeはdictへ展開し、リーフは '${タイプ名}' 形式）
        'type': {'${tuple}': ['${string}', '${number}', '${bool}']},
        'type_str': 'tuple',
        'variable': 'tuple_var',
        'default': ['item1', 10, True],
    },
    {
        # any: メンバー変数対象外 / 代入順序対象外
        'type': '${any}',
        'type_str': 'any',
        'variable': 'any_var',
        'default': 'free_value',
    },
    {
        # string指定・default無し: メンバー変数対象外 / 代入順序対象外
        'type': '${string}',
        'type_str': 'string',
        'variable': 'no_default_var',
        'default': None,
    },
    {
        # list(list(string)): 代入順序対象（メンバー変数対象外）。typeはdictへ展開され、type_strに 'list(list)' が入る
        'type': {'${list(list)}': ['${list(string)}']},
        'type_str': 'list(list)',
        'variable': 'list_list_var',
        'default': None,
    },
    {
        # list(tuple([string, number])): 代入順序対象（メンバー変数対象外）
        'type': {'${list(tuple)}': [{'${tuple}': ['${string}', '${number}']}]},
        'type_str': 'list(tuple)',
        'variable': 'list_tuple_var',
        'default': None,
    },
    {
        # list(object({...})): 代入順序対象（メンバー変数対象外）
        'type': {'${list(object)}': [{'${object}': {'name': '${string}', 'age': '${number}'}}]},
        'type_str': 'list(object)',
        'variable': 'list_object_var',
        'default': None,
    },
]

# T_TERF_TYPE_MASTER の内容（ita_api_admin/sql/terraform_common_master.sql より）
# TYPE_NAME の末尾スペースは MySQL PAD_SPACE collation で無視されるため strip して管理する
_TYPE_MASTER = {
    'string': 1, 'number': 2, 'bool': 3, 'null': 4,
    'list': 5, 'tuple': 6, 'map': 7, 'object': 8, 'set': 9,
    'list(list)': 10, 'list(set)': 11, 'set(list)': 12, 'set(set)': 13,
    'list(tuple)': 14, 'list(object)': 15, 'set(tuple)': 16, 'set(object)': 17,
    'any': 18,
}


def _resolve_type_id_without_db(type_str):
    """
    get_variable_type_id() の DB検索ロジックをインメモリで再現。
    type_str は executeParse 後の値（${} なし）を想定。
    完全一致がなければ 'list(string)' -> 'list' のようにプレフィックスで再検索する。
    """
    if not type_str:
        return None
    if type_str in _TYPE_MASTER:
        return _TYPE_MASTER[type_str]
    match = std_re.findall(r'^([a-z]+)\(', type_str)
    if match:
        return _TYPE_MASTER.get(match[0])
    return None


@pytest.fixture(scope='function')
def hcl2json_dependencies():
    app = Flask(__name__)
    app_context = app.app_context()
    app_context.push()

    g.applogger = SimpleNamespace(info=lambda *args, **kwargs: None)
    g.appmsg = SimpleNamespace(get_api_message=lambda code, args=None: code)

    yield

    app_context.pop()


def make_variable(name, type_value, default=None):
    return {name: {'type': type_value, 'default': default}}


def make_mocked_parse_result(*variables):
    return {'variable': list(variables)}


def assert_parse_success(result, parse_result):
    assert result is True
    assert parse_result['error_msg'] == ''


def run_parser(hcl_text, valid_check=False):
    with patch(
        'common_libs.terraform_driver.common.Hcl2Json.storage_access.storage_read',
        return_value=DummyReader(hcl_text),
    ):
        parser = HCL2JSONParse('dummy.tf')
        result = parser.executeParse(valid_check)
        return result, parser.getParseResult()


def run_parser_with_mocked_loads(parse_result, valid_check=False):
    with patch(
        'common_libs.terraform_driver.common.Hcl2Json.storage_access.storage_read',
        return_value=DummyReader('ignored'),
    ):
        with patch(
            'common_libs.terraform_driver.common.Hcl2Json.hcl2.loads',
            return_value=parse_result,
        ):
            parser = HCL2JSONParse('dummy.tf')
            result = parser.executeParse(valid_check)
            return result, parser.getParseResult()


def test_execute_parse_output_for_terraform_types(hcl2json_dependencies):
    result, parse_result = run_parser(HCL_SAMPLE_ALLTYPES)

    assert_parse_success(result, parse_result)
    actual_by_name = {v['variable']: v for v in parse_result['variables']}
    for expected in EXPECTED_VARIABLES:
        name = expected['variable']
        actual = actual_by_name.get(name)
        assert actual is not None, f"{name}: 変数がパース結果に存在しません"
        assert actual['type'] == expected['type'], (
            f"{name}: type が期待値と異なります\n"
            f"  actual  : {actual['type']!r}\n"
            f"  expected: {expected['type']!r}\n"
            f"  ヒント: python-hcl2 のバージョンが変わると ${{}} ラッパーの有無が変化します"
        )
        assert actual['type_str'] == expected['type_str'], (
            f"{name}: type_str が期待値と異なります\n"
            f"  actual  : {actual['type_str']!r}\n"
            f"  expected: {expected['type_str']!r}"
        )
        assert actual['default'] == expected['default'], (
            f"{name}: default が期待値と異なります\n"
            f"  actual  : {actual['default']!r}\n"
            f"  expected: {expected['default']!r}"
        )


def test_execute_parse_converts_null_type_to_legacy_marker(hcl2json_dependencies):
    hcl_text = '''
variable "nullable_var" {
  type = null
}
'''

    result, parse_result = run_parser(hcl_text)

    assert_parse_success(result, parse_result)
    assert parse_result['variables'] == [
        {
            'type': '${null}',
            'type_str': 'null',
            'variable': 'nullable_var',
            'default': None,
        }
    ]


def test_execute_parse_returns_true_when_variable_block_is_missing(hcl2json_dependencies):
    hcl_text = '''
locals {
  sample = "value"
}
'''

    result, parse_result = run_parser(hcl_text)

    assert_parse_success(result, parse_result)
    assert parse_result['variables'] == []


def test_execute_parse_rejects_too_long_variable_name(hcl2json_dependencies):
    variable_name = 'a' * 129
    hcl_text = f'''
variable "{variable_name}" {{
  type = string
}}
'''

    result, parse_result = run_parser(hcl_text, valid_check=True)

    assert result is False
    assert parse_result['variables'] == []
    assert parse_result['error_msg'] == 'MSG-80025'


def test_execute_parse_normalizes_slash_and_single_quoted_type_strings(hcl2json_dependencies):
    parse_result = make_mocked_parse_result(
        make_variable('slash_quote_var', '${object({path = /"tmp"/, note = \'string\'})}')
    )

    result, normalized = run_parser_with_mocked_loads(parse_result)

    assert_parse_success(result, normalized)
    assert normalized['variables'] == [
        {
            'type': '{"${object}": {path = \\"tmp\\", note = "string"}}',
            'type_str': None,
            'variable': 'slash_quote_var',
            'default': None,
        }
    ]


@pytest.mark.parametrize(
    "block_type, expected",
    [
        (['${map(string)}'], True),
        ([{'nested': '${map(string)}'}], True),
        (['${list(string)}'], False),
        ({'${map(string)}': 'value'}, True),
        ({'outer': {'inner': '${map(string)}'}}, True),
        ({'outer': {'inner': '${list(string)}'}}, False),
    ],
)
def test_is_map_check_patterns(block_type, expected):
    parser = HCL2JSONParse('dummy.tf')
    assert parser.isMapCheck(block_type, False) is expected


def test_execute_parse_removes_backslash_from_type_string(hcl2json_dependencies):
    # バックスラッシュ除去正規表現 (r'\\' -> '') のパスを通ることを確認する。
    # None regex (r'"(.*?)\\:\\s(None)"') はバックスラッシュ除去の後に実行されるため、
    # "\\: None" を含む入力であってもバックスラッシュが先に除去されると None regex は発火しない。
    parse_result = make_mocked_parse_result(
        make_variable('backslash_var', '${string\\type}')
    )

    result, normalized = run_parser_with_mocked_loads(parse_result)

    assert_parse_success(result, normalized)
    var = normalized['variables'][0]
    assert var['variable'] == 'backslash_var'
    # バックスラッシュが除去されて type / type_str が設定されること
    assert var['type'] == '${stringtype}'
    assert var['type_str'] == 'stringtype'


def test_execute_parse_normalizes_redundant_comma_before_closing_parenthesis(hcl2json_dependencies):
    parse_result = make_mocked_parse_result(make_variable('comma_fix_var', '${tuple([string]),)}'))

    result, normalized = run_parser_with_mocked_loads(parse_result)

    assert_parse_success(result, normalized)
    normalized_type = normalized['variables'][0]['type']
    assert normalized['variables'][0]['variable'] == 'comma_fix_var'
    assert '),)' not in normalized_type
    assert '))' in normalized_type


def test_execute_parse_handles_object_join_pattern_if_match_branch(hcl2json_dependencies):
    parse_result = make_mocked_parse_result(
        make_variable('obj_join_var', 'x${aaa({x=y})}""${bbb({p=q})')
    )

    result, normalized = run_parser_with_mocked_loads(parse_result)

    assert_parse_success(result, normalized)
    assert normalized['variables'][0]['variable'] == 'obj_join_var'
    assert '{"${bbb}": {p=q})' in normalized['variables'][0]['type']


def test_execute_parse_covers_additional_regex_match_branches(hcl2json_dependencies):
    # hcl2 が通常出力しないエッジケース入力（実際の HCL からは到達不可能なコードパス）
    # list(tuple) / list(object) は HCL_SAMPLE_ALLTYPES の実データでカバー済み
    parse_result = make_mocked_parse_result(
        make_variable('v3', '${([a])}'),
        make_variable('v4', '${_([a])}"x"${([b])'),
        make_variable('v5', '${({a=b})}'),
        make_variable('v6', '${_({a=b})}"x"${({c=d})'),
    )

    result, normalized = run_parser_with_mocked_loads(parse_result)

    assert_parse_success(result, normalized)
    actual = {item['variable']: item['type'] for item in normalized['variables']}

    assert actual['v3'] == '{"${}": [a]}'
    assert '{"${}": [b]' in actual['v4']
    assert actual['v5'] == '{"${}": {a=b}}'
    assert '{"${}": {c=d}' in actual['v6']


def test_execute_parse_covers_hard_to_reach_regex_branches_with_mocked_findall(hcl2json_dependencies):
    # list(tuple) / list(object) のパターン3・4は、pattern2 が先に一致するため実際には発火しない dead code。
    # unquoted tuple / None pattern も同様に dead code（前段の処理で先に変換される）。
    # これら 4 パターンの if/while ボディ行をカバーするためだけに findall をモックする。
    parse_result = make_mocked_parse_result(make_variable('forced_branch_var', 'dummy_type'))

    target_patterns = {
        r'\"\$\{([a-z]+?)\(([a-z]+?)\(\[(.*)\]\)\)\}\"',
        r'\"\$\{([a-z]+?)\(([a-z]+?)\(\{(.*)\}\)\)\}\"',
        r'\$\{([a-z]+?)\(\[(.*)\]\)\}',
        r'\"(.*?)\\:\s(None)\"',
    }
    hit_counter = {}
    original_findall = std_re.findall

    def mocked_findall(pattern, text):
        if pattern in target_patterns:
            hit_counter[pattern] = hit_counter.get(pattern, 0) + 1
            return ['forced_match'] if hit_counter[pattern] == 1 else []
        return original_findall(pattern, text)

    with patch('common_libs.terraform_driver.common.Hcl2Json.re.findall', side_effect=mocked_findall):
        result, normalized = run_parser_with_mocked_loads(parse_result)

    assert_parse_success(result, normalized)
    assert normalized['variables'][0]['variable'] == 'forced_branch_var'


def test_execute_parse_returns_false_when_hcl2_loads_raises(hcl2json_dependencies):
    # 無効な HCL を渡すと hcl2.loads が UnexpectedToken を raise し result=False になることを確認
    result, parse_result = run_parser('this is not valid hcl ===@@@')

    assert result is False
    assert parse_result['res'] is False
    assert parse_result['variables'] == []


def test_type_str_is_resolvable_to_type_master(hcl2json_dependencies):
    # type_str が T_TERF_TYPE_MASTER に解決できる形式であることを確認する。
    # 余分な引用符（' や "）や ${} の残留があると TYPE_ID = None になりバックヤード処理が壊れる。
    result, parse_result = run_parser(HCL_SAMPLE_ALLTYPES)

    assert_parse_success(result, parse_result)
    for var in parse_result['variables']:
        type_str = var['type_str']
        # HCL_SAMPLE_ALLTYPES の全変数は type 宣言あり → type_str が None になるのは異常
        # v7 のように ${} ラッパーが消えると type_str = None になりここで検知できる
        assert type_str is not None, (
            f"{var['variable']}: type_str=None — ${{}} ラッパーが消えている可能性があります。"
        )
        type_id = _resolve_type_id_without_db(type_str)
        assert type_id is not None, (
            f"{var['variable']}: type_str={type_str!r} が T_TERF_TYPE_MASTER に解決できません。"
            f"余分な引用符や ${{}} の残留がないか確認してください。"
        )
