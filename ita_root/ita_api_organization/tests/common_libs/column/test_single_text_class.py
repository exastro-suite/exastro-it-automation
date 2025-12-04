import pytest
from unittest.mock import patch
import copy
from flask import g

from common_libs.column.single_text_class import SingleTextColumn
from common_libs.column import text_column_class


@pytest.fixture(scope='function')
def objtable_dict_fixture():
    """
    TextColumnのコンストラクタに必要なobjtableの辞書を返すフィクスチャ
    """
    return {
        'MENUINFO': {'TABLE_NAME': 'test_table'},
        'COLINFO': {'rest_key': {'COL_NAME': 'test_col'}}
    }


@pytest.fixture(scope='function')
def single_text_column(objtable_dict_fixture, request):
    """
    テスト用のSingleTextColumnインスタンスを生成するフィクスチャ
    COL_NAMEをパラメータとして受け取る
    """
    table_dict = copy.deepcopy(objtable_dict_fixture)

    # request.paramからCOL_NAMEを取得し、フィクスチャ内で動的に設定
    col_name = request.param if hasattr(request, 'param') else 'test_col_value'

    table_dict['COLINFO']['rest_key']['COL_NAME'] = col_name
    return SingleTextColumn('test_col_value', table_dict, 'rest_key', 'cmd_test')


@pytest.mark.parametrize(
    "single_text_column, value, expected_msg",
    [
        ('test_col_value', "invalid\ttext", "テスト用エラーメッセージ"),
        ('test_col_value', "invalid\ntext", "テスト用エラーメッセージ"),
        ('test_col_value', "invalid\rtext", "テスト用エラーメッセージ"),
    ],
    ids=[
        "invalid_with_tab",
        "invalid_with_newline",
        "invalid_with_cr",
    ],
    indirect=['single_text_column']  # フィクスチャを間接的に呼び出す
)
def test_check_basic_valid_failure_with_invalid_chars(app_context_with_mock_g, single_text_column, value, expected_msg, monkeypatch):
    """
    check_basic_validの失敗ケース（不正な文字）をテスト
    """
    def mock_get_api_message(msg_id, args=None):
        """g.appmsg.get_api_messageの代替関数"""
        assert msg_id == 'MSG-00009'
        return expected_msg

    monkeypatch.setattr(g.appmsg, 'get_api_message', mock_get_api_message)

    with patch.object(text_column_class.TextColumn, 'check_basic_valid', return_value=(True,)):
        result = single_text_column.check_basic_valid(value)
        assert result[0] is False
        assert result[1] == expected_msg


# check_basic_validのテスト
@pytest.mark.parametrize(
    "single_text_column, value, expected_result",
    [
        ('test_col_value', "valid_text", (True,)),
        ('test_col_value', "", (True,)),
        ('test_col_value', None, (True,)),
        ('test_col_value', "12345", (True,)),
    ],
    ids=[
        "valid_string",
        "empty_string",
        "None_value",
        "numeric_string",
    ],
    indirect=['single_text_column']
)
def test_check_basic_valid_success(single_text_column, value, expected_result):
    """
    check_basic_validの成功ケースをテスト
    """
    with patch.object(text_column_class.TextColumn, 'check_basic_valid', return_value=(True,)):
        result = single_text_column.check_basic_valid(value)
        assert result == expected_result


# convert_value_inputのテスト
@pytest.mark.parametrize(
    "single_text_column, value, expected_value",
    [
        ("DATA_JSON", "some_data", "some_data"),
        ("DATA_JSON", 123, '123'),
        ("DATA_JSON", None, None),
        ("other_col", "some_data", "some_data"),
    ],
    ids=[
        "DATA_JSON_string_input",
        "DATA_JSON_int_input",
        "DATA_JSON_None_input",
        "other_col_input",
    ],
    indirect=['single_text_column']
)
def test_convert_value_input(single_text_column, value, expected_value):
    """
    convert_value_inputのテスト
    """
    ret_bool, msg, val = single_text_column.convert_value_input(value)
    assert ret_bool is True
    assert msg == ''
    assert val == expected_value


# convert_value_outputのテスト
@pytest.mark.parametrize(
    "single_text_column, value, expected_value",
    [
        ("DATA_JSON", "some_data", "some_data"),
        ("DATA_JSON", 123, '123'),
        ("DATA_JSON", None, None),
        ("other_col", "some_data", "some_data"),
    ],
    ids=[
        "DATA_JSON_string_output",
        "DATA_JSON_int_output",
        "DATA_JSON_None_output",
        "other_col_output",
    ],
    indirect=['single_text_column']
)
def test_convert_value_output(single_text_column, value, expected_value):
    """
    convert_value_outputのテスト
    """
    ret_bool, msg, val = single_text_column.convert_value_output(value)
    assert ret_bool is True
    assert msg == ''
    assert val == expected_value
