#   Copyright 2022 NEC Corporation
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

import re
import binascii
import ast
from libs.organization_common import check_auth_menu  # noqa: F401
from flask import g
from common_libs.common import *  # noqa: F403


def menu_column_valid(objdbca, objtable, option):
    lang = g.get('LANGUAGE')
    retBool = True
    msg = ''
    menu_name_rest = objtable.get('MENUINFO').get('MENU_NAME_REST')
    entry_parameter = option.get('entry_parameter').get('parameter')
    column_class = entry_parameter.get("column_class")
    menu_create_id = entry_parameter.get('menu_name')
    item_name_ja = entry_parameter.get('item_name_ja')
    item_name_en = entry_parameter.get('item_name_en')
    item_name_rest = entry_parameter.get('item_name_rest')

    # 文字列(単一行)最大バイト数
    single_string_maximum_bytes = entry_parameter.get("single_string_maximum_bytes")
    # 文字列(単一行)正規表現
    single_string_regular_expression = entry_parameter.get("single_string_regular_expression")
    # 初期値(文字列(単一行))
    single_string_default_value = entry_parameter.get("single_string_default_value")
    # 文字列(複数行)最大バイト数
    multi_string_maximum_bytes = entry_parameter.get("multi_string_maximum_bytes")
    # 文字列(複数行)正規表現
    multi_string_regular_expression = entry_parameter.get("multi_string_regular_expression")
    # 初期値(文字列(複数行))
    multi_string_default_value = entry_parameter.get("multi_string_default_value")
    # 整数最大値
    integer_maximum_value = entry_parameter.get("integer_maximum_value")
    # 整数最小値
    integer_minimum_value = entry_parameter.get("integer_minimum_value")
    # 初期値(整数)
    integer_default_value = entry_parameter.get("integer_default_value")
    # 小数最大値
    decimal_maximum_value = entry_parameter.get("decimal_maximum_value")
    # 小数最小値
    decimal_minimum_value = entry_parameter.get("decimal_minimum_value")
    # 小数桁数
    decimal_digit = entry_parameter.get("decimal_digit")
    # 初期値(小数)
    decimal_default_value = entry_parameter.get("decimal_default_value")
    # 初期値(日時)
    datetime_default_value = entry_parameter.get("datetime_default_value")
    # 初期値(日付)
    date_default_value = entry_parameter.get("date_default_value")
    # メニューグループ：メニュー：項目
    pulldown_selection = entry_parameter.get("pulldown_selection")
    # 初期値(プルダウン選択)
    pulldown_selection_default_value = entry_parameter.get("pulldown_selection_default_value")
    # 参照項目
    reference_item = entry_parameter.get("reference_item")
    # パスワード最大バイト数
    password_maximum_bytes = entry_parameter.get("password_maximum_bytes")
    # ファイルアップロード/ファイル最大バイト数
    file_upload_maximum_bytes = entry_parameter.get("file_upload_maximum_bytes")
    # リンク/最大バイト数
    link_maximum_bytes = entry_parameter.get("link_maximum_bytes")
    # 初期値(リンク)
    link_default_value = entry_parameter.get("link_default_value")
    # パラメータシート参照/メニューグループ：メニュー：項目
    parameter_sheet_reference = entry_parameter.get("parameter_sheet_reference")

    # 入力方式が文字列(単一行)の場合
    if column_class == "1":
        # 文字列(単一行)最大バイト数が設定されていない場合、エラー
        if retBool and single_string_maximum_bytes is None:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20016", [])
        # 文字列(複数行)最大バイト数が設定されている場合、エラー
        if retBool and multi_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20017", [])
        # 文字列(複数行)正規表現が設定されている場合、エラー
        if retBool and multi_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20018", [])
        # 整数最小値が設定されている場合、エラー
        if retBool and integer_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20019", [])
        # 整数最大値が設定されている場合、エラー
        if retBool and integer_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20020", [])
        # 小数最小値が設定されている場合、エラー
        if retBool and decimal_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20021", [])
        # 小数最大値が設定されている場合、エラー
        if retBool and decimal_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20022", [])
        # 小数桁数が設定されている場合、エラー
        if retBool and decimal_digit:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20023", [])
        # メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and pulldown_selection:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20024", [])
        # パスワード最大バイト数が設定されている場合、エラー
        if retBool and password_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20025", [])
        # ファイルアップロード/ファイル最大バイト数が設定されている場合、エラー
        if retBool and file_upload_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20026", [])
        # リンク/最大バイト数が設定されている場合、エラー
        if retBool and link_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20027", [])
        # 参照項目が設定されている場合、エラー
        if retBool and reference_item:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20028", [])
        # 初期値(文字列(複数行))が設定されている場合、エラー
        if retBool and multi_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20029", [])
        # 初期値(整数)が設定されている場合、エラー
        if retBool and integer_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20030", [])
        # 初期値(小数)が設定されている場合、エラー
        if retBool and decimal_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20031", [])
        # 初期値(日時)が設定されている場合、エラー
        if retBool and datetime_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20032", [])
        # 初期値(日付)が設定されている場合、エラー
        if retBool and date_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20033", [])
        # 初期値(リンク)が設定されている場合、エラー
        if retBool and link_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20034", [])
        # 初期値(プルダウン選択)が設定されている場合、エラー
        if retBool and pulldown_selection_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20035", [])
        # パラメータシート参照/メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and parameter_sheet_reference:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20036", [])
        # 最大バイト数と初期値の条件一致をチェック
        if retBool and single_string_default_value:
            hex_value = str(single_string_default_value)
            hex_value = binascii.b2a_hex(hex_value.encode('utf-8'))
            if int(single_string_maximum_bytes) < int(len(hex_value)) / 2:
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20037", [])
        # 正規表現と初期値の条件一致をチェック
        if retBool and single_string_regular_expression:
            pattern = single_string_regular_expression
            try:
                pattern = re.compile(r'{}'.format(pattern), re.DOTALL)
            except Exception:
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20038", [])
                return retBool, msg, option
            if single_string_default_value:
                tmp_result = pattern.fullmatch(single_string_default_value)
                if tmp_result is None:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-20039", [])

    # 入力方式が文字列(複数行)の場合
    elif column_class == "2":
        # 文字列(複数行)最大バイト数が設定されていない場合、エラー
        if retBool and multi_string_maximum_bytes is None:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20040", [])
        # 文字列(単一行)最大バイト数が設定されている場合、エラー
        if retBool and single_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20041", [])
        # 文字列(単一行)正規表現が設定されている場合、エラー
        if retBool and single_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20042", [])
        # 整数最小値が設定されている場合、エラー
        if retBool and integer_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20043", [])
        # 整数最大値が設定されている場合、エラー
        if retBool and integer_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20044", [])
        # 小数最小値が設定されている場合、エラー
        if retBool and integer_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20045", [])
        # 小数最大値が設定されている場合、エラー
        if retBool and integer_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20046", [])
        # 小数桁数が設定されている場合、エラー
        if retBool and decimal_digit:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20047", [])
        # メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and pulldown_selection:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20048", [])
        # パスワード最大バイト数が設定されている場合、エラー
        if retBool and password_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20049", [])
        # ファイルアップロード/ファイル最大バイト数が設定されている場合、エラー
        if retBool and file_upload_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20050", [])
        # リンク/最大バイト数が設定されている場合、エラー
        if retBool and link_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20051", [])
        # 参照項目が設定されている場合、エラー
        if retBool and reference_item:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20052", [])
        # 初期値(文字列(単一行))が設定されている場合、エラー
        if retBool and single_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20053", [])
        # 初期値(整数)が設定されている場合、エラー
        if retBool and integer_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20054", [])
        # 初期値(小数)が設定されている場合、エラー
        if retBool and decimal_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20055", [])
        # 初期値(日時)が設定されている場合、エラー
        if retBool and datetime_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20056", [])
        # 初期値(日付)が設定されている場合、エラー
        if retBool and date_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20057", [])
        # 初期値(リンク)が設定されている場合、エラー
        if retBool and link_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20058", [])
        # 初期値(プルダウン選択)が設定されている場合、エラー
        if retBool and pulldown_selection_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20059", [])
        # パラメータシート参照/メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and parameter_sheet_reference:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20060", [])
        # 最大バイト数と初期値の条件一致をチェック
        if retBool and multi_string_default_value:
            # 改行コードを\r\nに置換(改行は2バイトとして計算する)
            multi_value = re.sub("\n|\r", "\r\n", multi_string_default_value)
            hex_value = str(multi_value)
            hex_value = binascii.b2a_hex(hex_value.encode('utf-8'))
            if int(multi_string_maximum_bytes) < int(len(hex_value)) / 2:
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20061", [])
        # 正規表現と初期値の条件一致をチェック
        if retBool and multi_string_regular_expression:
            pattern = multi_string_regular_expression
            try:
                pattern = re.compile(r'{}'.format(pattern), re.DOTALL)
            except Exception:
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20062", [])
                return retBool, msg, option
            if multi_string_default_value:
                tmp_result = pattern.fullmatch(multi_string_default_value)
                if tmp_result is None:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-20063", [])

    # 入力方式が整数の場合
    elif column_class == "3":
        # 文字列(単一行)最大バイト数が設定されている場合、エラー
        if retBool and single_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20064", [])
        # 文字列(単一行)正規表現が設定されている場合、エラー
        if retBool and single_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20065", [])
        # 文字列(複数行)最大バイト数が設定されている場合、エラー
        if retBool and multi_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20066", [])
        # 文字列(複数行)正規表現が設定されている場合、エラー
        if retBool and multi_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20067", [])
        # 整数最小値が設定されていない場合、一時最小値にする
        if retBool and integer_minimum_value is None:
            integer_minimum_value = -2147483648
        # 整数最大値が設定されていない場合、一時最大値にする(最大値>最小値チェックの時エラー出ないため)
        if retBool and integer_maximum_value is None:
            integer_maximum_value = 2147483648
        # 最大値<最小値になっている場合、エラー
        if retBool and float(integer_minimum_value) > float(integer_maximum_value):
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20068", [integer_minimum_value, integer_maximum_value])
        # 小数最小値が設定されている場合、エラー
        if retBool and decimal_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20069", [])
        # 小数最大値が設定されている場合、エラー
        if retBool and decimal_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20070", [])
        # 小数桁数が設定されている場合、エラー
        if retBool and decimal_digit:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20071", [])
        # メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and pulldown_selection:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20072", [])
        # パスワード最大バイト数が設定されている場合、エラー
        if retBool and password_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20073", [])
        # ファイルアップロード/ファイル最大バイト数が設定されている場合、エラー
        if retBool and file_upload_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20074", [])
        # リンク/最大バイト数が設定されている場合、エラー
        if retBool and link_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20075", [])
        # 参照項目が設定されている場合、エラー
        if retBool and reference_item:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20076", [])
        # 初期値(文字列(単一行))が設定されている場合、エラー
        if retBool and single_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20077", [])
        # 初期値(文字列(複数行))が設定されている場合、エラー
        if retBool and multi_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20078", [])
        # 初期値(小数)が設定されている場合、エラー
        if retBool and decimal_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20079", [])
        # 初期値(日時)が設定されている場合、エラー
        if retBool and datetime_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20080", [])
        # 初期値(日付)が設定されている場合、エラー
        if retBool and date_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20081", [])
        # 初期値(リンク)が設定されている場合、エラー
        if retBool and link_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20082", [])
        # 初期値(プルダウン選択)が設定されている場合、エラー
        if retBool and pulldown_selection_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20083", [])
        # パラメータシート参照/メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and parameter_sheet_reference:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20084", [])
        # 初期値(整数) 最大数、最小数をチェック
        if retBool and integer_default_value:
            if isinstance(integer_default_value, int):
                if float(integer_maximum_value) < float(integer_default_value) or float(integer_default_value) < float(integer_minimum_value):
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-20085", [])

    # 入力方式が小数の場合
    elif column_class == "4":
        # 文字列(単一行)最大バイト数が設定されている場合、エラー
        if retBool and single_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20086", [])
        # 文字列(単一行)正規表現が設定されている場合、エラー
        if retBool and single_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20087", [])
        # 文字列(複数行)最大バイト数が設定されている場合、エラー
        if retBool and multi_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20088", [])
        # 文字列(複数行)正規表現が設定されている場合、エラー
        if retBool and multi_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20089", [])
        # 整数最小値が設定されている場合、エラー
        if retBool and integer_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20090", [])
        # 整数最大値が設定されている場合、エラー
        if retBool and integer_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20091", [])
        # 小数最小値が設定されていない場合、一時最小値にする
        if retBool and decimal_minimum_value is None:
            decimal_minimum_value = -9999999999999
        # 小数最大値が設定されていない場合、一時最大値にする
        if retBool and decimal_maximum_value is None:
            decimal_maximum_value = 9999999999999
        # 最大値<最小値になっている場合、エラー
        if retBool and float(decimal_minimum_value) > float(decimal_maximum_value):
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20092", [decimal_minimum_value, decimal_maximum_value])
        # メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and pulldown_selection:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20093", [])
        # パスワード最大バイト数が設定されている場合、エラー
        if retBool and password_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20094", [])
        # ファイルアップロード/ファイル最大バイト数が設定されている場合、エラー
        if retBool and file_upload_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20095", [])
        # リンク/最大バイト数が設定されている場合、エラー
        if retBool and link_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20096", [])
        # 参照項目が設定されている場合、エラー
        if retBool and reference_item:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20097", [])
        # 初期値(文字列(単一行))が設定されている場合、エラー
        if retBool and single_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20098", [])
        # 初期値(文字列(複数行))が設定されている場合、エラー
        if retBool and multi_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20099", [])
        # 初期値(整数)が設定されている場合、エラー
        if retBool and integer_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20100", [])
        # 初期値(日時)が設定されている場合、エラー
        if retBool and datetime_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20101", [])
        # 初期値(日付)が設定されている場合、エラー
        if retBool and date_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20102", [])
        # 初期値(リンク)が設定されている場合、エラー
        if retBool and link_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20103", [])
        # 初期値(プルダウン選択)が設定されている場合、エラー
        if retBool and pulldown_selection_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20104", [])
        # パラメータシート参照/メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and parameter_sheet_reference:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20105", [])
        # 初期値(小数) 最大数、最小数をチェック
        if retBool and decimal_default_value:
            if float(decimal_maximum_value) < float(decimal_default_value) or float(decimal_default_value) < float(decimal_minimum_value):
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20106", [])
            # 桁数をチェック
            if retBool and decimal_digit:
                srt_val = str(decimal_default_value)
                if "." in srt_val:
                    srt_val = srt_val.rstrip("0")
                vlen = int(len(srt_val))
                if "." in srt_val or "-" in srt_val:
                    vlen -= 1
                if int(decimal_digit) < vlen:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-20107", [])

    # 入力方式が日時の場合
    elif column_class == "5":
        # 文字列(単一行)最大バイト数が設定されている場合、エラー
        if retBool and single_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20108", [])
        # 文字列(単一行)正規表現が設定されている場合、エラー
        if retBool and single_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20109", [])
        # 文字列(複数行)最大バイト数が設定されている場合、エラー
        if retBool and multi_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20110", [])
        # 文字列(複数行)正規表現が設定されている場合、エラー
        if retBool and multi_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20111", [])
        # 整数最小値が設定されている場合、エラー
        if retBool and integer_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20112", [])
        # 整数最大値が設定されている場合、エラー
        if retBool and integer_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20113", [])
        # 小数最小値が設定されている場合、エラー
        if retBool and decimal_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20114", [])
        # 小数最大値が設定されている場合、エラー
        if retBool and decimal_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20115", [])
        # 小数桁数が設定されている場合、エラー
        if retBool and decimal_digit:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20116", [])
        # メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and pulldown_selection:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20117", [])
        # パスワード最大バイト数が設定されている場合、エラー
        if retBool and password_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20118", [])
        # ファイルアップロード/ファイル最大バイト数が設定されている場合、エラー
        if retBool and file_upload_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20119", [])
        # リンク/最大バイト数が設定されている場合、エラー
        if retBool and link_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20120", [])
        # 参照項目が設定されている場合、エラー
        if retBool and reference_item:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20121", [])
        # 初期値(文字列(単一行))が設定されている場合、エラー
        if retBool and single_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20122", [])
        # 初期値(文字列(複数行))が設定されている場合、エラー
        if retBool and multi_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20123", [])
        # 初期値(整数)が設定されている場合、エラー
        if retBool and integer_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20124", [])
        # 初期値(小数)が設定されている場合、エラー
        if retBool and decimal_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20125", [])
        # 初期値(日付)が設定されている場合、エラー
        if retBool and date_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20126", [])
        # 初期値(リンク)が設定されている場合、エラー
        if retBool and link_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20127", [])
        # 初期値(プルダウン選択)が設定されている場合、エラー
        if retBool and pulldown_selection_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20128", [])
        # パラメータシート参照/メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and parameter_sheet_reference:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20129", [])

    # 入力方式が日付の場合
    elif column_class == "6":
        # 文字列(単一行)最大バイト数が設定されている場合、エラー
        if retBool and single_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20130", [])
        # 文字列(単一行)正規表現が設定されている場合、エラー
        if retBool and single_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20131", [])
        # 文字列(複数行)最大バイト数が設定されている場合、エラー
        if retBool and multi_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20132", [])
        # 文字列(複数行)正規表現が設定されている場合、エラー
        if retBool and multi_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20133", [])
        # 整数最小値が設定されている場合、エラー
        if retBool and integer_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20134", [])
        # 整数最大値が設定されている場合、エラー
        if retBool and integer_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20135", [])
        # 小数最小値が設定されている場合、エラー
        if retBool and decimal_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20136", [])
        # 小数最大値が設定されている場合、エラー
        if retBool and decimal_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20137", [])
        # 小数桁数が設定されている場合、エラー
        if retBool and decimal_digit:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20138", [])
        # メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and pulldown_selection:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20139", [])
        # パスワード最大バイト数が設定されている場合、エラー
        if retBool and password_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20140", [])
        # ファイルアップロード/ファイル最大バイト数が設定されている場合、エラー
        if retBool and file_upload_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20141", [])
        # リンク/最大バイト数が設定されている場合、エラー
        if retBool and link_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20142", [])
        # 参照項目が設定されている場合、エラー
        if retBool and reference_item:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20143", [])
        # 初期値(文字列(単一行))が設定されている場合、エラー
        if retBool and single_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20144", [])
        # 初期値(文字列(複数行))が設定されている場合、エラー
        if retBool and multi_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20145", [])
        # 初期値(整数)が設定されている場合、エラー
        if retBool and integer_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20146", [])
        # 初期値(小数)が設定されている場合、エラー
        if retBool and decimal_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20147", [])
        # 初期値(日時)が設定されている場合、エラー
        if retBool and datetime_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20148", [])
        # 初期値(リンク)が設定されている場合、エラー
        if retBool and link_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20149", [])
        # 初期値(プルダウン選択)が設定されている場合、エラー
        if retBool and pulldown_selection_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20150", [])
        # パラメータシート参照/メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and parameter_sheet_reference:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20151", [])

    # 入力方式がプルダウンの場合
    elif column_class == "7":
        # 文字列(単一行)最大バイト数が設定されている場合、エラー
        if retBool and single_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20152", [])
        # 文字列(単一行)正規表現が設定されている場合、エラー
        if retBool and single_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20153", [])
        # 文字列(複数行)最大バイト数が設定されている場合、エラー
        if retBool and multi_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20154", [])
        # 文字列(複数行)正規表現が設定されている場合、エラー
        if retBool and multi_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20155", [])
        # 整数最小値が設定されている場合、エラー
        if retBool and integer_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20156", [])
        # 整数最大値が設定されている場合、エラー
        if retBool and integer_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20157", [])
        # 小数最小値が設定されている場合、エラー
        if retBool and decimal_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20158", [])
        # 小数最大値が設定されている場合、エラー
        if retBool and decimal_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20159", [])
        # 小数桁数が設定されている場合、エラー
        if retBool and decimal_digit:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20160", [])
        # メニューグループ：メニュー：項目が設定されていない場合、エラー
        if retBool and pulldown_selection is None:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20161", [])
        # パスワード最大バイト数が設定されている場合、エラー
        if retBool and password_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20162", [])
        # ファイルアップロード/ファイル最大バイト数が設定されている場合、エラー
        if retBool and file_upload_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20163", [])
        # リンク/最大バイト数が設定されている場合、エラー
        if retBool and link_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20164", [])
        # 初期値(文字列(単一行))が設定されている場合、エラー
        if retBool and single_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20165", [])
        # 初期値(文字列(複数行))が設定されている場合、エラー
        if retBool and multi_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20166", [])
        # 初期値(整数)が設定されている場合、エラー
        if retBool and integer_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20167", [])
        # 初期値(小数)が設定されている場合、エラー
        if retBool and decimal_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20168", [])
        # 初期値(日時)が設定されている場合、エラー
        if retBool and datetime_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20169", [])
        # 初期値(日付)が設定されている場合、エラー
        if retBool and date_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20170", [])
        # 初期値(リンク)が設定されている場合、エラー
        if retBool and link_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20171", [])
        # パラメータシート参照/メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and parameter_sheet_reference:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20172", [])
        # 参照項目
        if retBool and reference_item:
            # プルダウン選択がない場合、エラー
            if not pulldown_selection:
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20252", [])
                return retBool, msg, option

            # list形式であることをチェック
            reference_item_list = ast.literal_eval(reference_item)
            if type(reference_item_list) is not list:
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20253", [])
                return retBool, msg, option

            # 参照項目リストを取得
            table_name = "V_MENU_REFERENCE_ITEM"
            where_str = "WHERE DISUSE_FLAG = '0' AND LINK_ID = %s"
            bind_value_list = [pulldown_selection]
            return_values = objdbca.table_select(table_name, where_str, bind_value_list)

            for ref_column_name_rest in reference_item_list:
                # 入力された値と、「参照項目情報」の値に一致があるかどうかを確認
                check_bool = False
                for record in return_values:
                    check_ref_column_name_rest = record.get('COLUMN_NAME_REST')
                    if ref_column_name_rest == check_ref_column_name_rest:
                        check_bool = True
                        target_record = record
                        break

                if not check_bool:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-20254", [ref_column_name_rest])
                    return retBool, msg, option
                else:
                    ref_column_name_ja = target_record.get('COLUMN_NAME_JA')
                    ref_column_name_en = target_record.get('COLUMN_NAME_EN')
                    # 自身の「項目名」と参照項目の「項目名」が同一の名前かどうかを確認
                    if item_name_ja == ref_column_name_ja:
                        retBool = False
                        msg = g.appmsg.get_api_message("MSG-20255", [ref_column_name_ja])
                        return retBool, msg, option
                    if item_name_en == ref_column_name_en:
                        retBool = False
                        msg = g.appmsg.get_api_message("MSG-20255", [ref_column_name_en])
                        return retBool, msg, option

                    # 参照項目の「項目名」と同一の名前が他の項目名で使用されているかを確認
                    table_name = "T_MENU_COLUMN"
                    where_str = "WHERE DISUSE_FLAG = '0' AND MENU_CREATE_ID = %s AND (COLUMN_NAME_JA = %s OR COLUMN_NAME_EN = %s)"
                    bind_value_list = [menu_create_id, ref_column_name_ja, ref_column_name_en]
                    return_values_2 = objdbca.table_select(table_name, where_str, bind_value_list)
                    if return_values_2:
                        retBool = False
                        if lang == "ja":
                            msg = g.appmsg.get_api_message("MSG-20255", [ref_column_name_ja])
                        else:
                            msg = g.appmsg.get_api_message("MSG-20255", [ref_column_name_en])
                        return retBool, msg, option

        # 初期値(プルダウン選択)
        if retBool and pulldown_selection_default_value:
            # 他メニュー連携から、必要な情報を取得
            table_name = "V_MENU_OTHER_LINK"
            where_str = "WHERE DISUSE_FLAG = '0' AND LINK_ID = %s"
            bind_value_list = [pulldown_selection]
            return_values = objdbca.table_select(table_name, where_str, bind_value_list)
            if not 0 < len(return_values):
                # DBエラー
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20173", [])
                return retBool, msg, option
            else:
                # 必要なデータを取得
                table_name = return_values[0]["REF_TABLE_NAME"]
                pri_name = return_values[0]["REF_PKEY_NAME"]
                other_menu_name_rest = return_values[0]["MENU_NAME_REST"]
            # 対象のテーブルからレコードを取得
            where_str = "WHERE DISUSE_FLAG = '0'"
            return_values = objdbca.table_select(table_name, where_str, [])
            # アクセス許可チェック
            skip_check_auth_list = ["selection_1", "selection_2"]  # チェックスキップ対象のメニュー名(REST)
            if other_menu_name_rest not in skip_check_auth_list:
                privilege = check_auth_menu(other_menu_name_rest, objdbca)
                if not privilege:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-20174", [])
                    return retBool, msg, option
            # 指定した初期値のIDが指定可能なレコードであるかどうかをチェック
            if not 0 < len(return_values):
                # DBエラー
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20175", [])
                return retBool, msg, option
            # 指定した初期値のIDが指定可能なレコードであるかどうかをチェック
            for data in return_values:
                check_flg = False
                if data[pri_name] == pulldown_selection_default_value:
                    check_flg = True
                    break
            if not check_flg:
                # 指定できない初期値を入力した場合
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20176", [])

    # 入力方式がパスワードの場合
    elif column_class == "8":
        # 文字列(単一行)最大バイト数が設定されている場合、エラー
        if retBool and single_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20177", [])
        # 文字列(単一行)正規表現が設定されている場合、エラー
        if retBool and single_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20178", [])
        # 文字列(複数行)最大バイト数が設定されている場合、エラー
        if retBool and multi_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20179", [])
        # 文字列(複数行)正規表現が設定されている場合、エラー
        if retBool and multi_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20180", [])
        # 整数最小値が設定されている場合、エラー
        if retBool and integer_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20181", [])
        # 整数最大値が設定されている場合、エラー
        if retBool and integer_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20182", [])
        # 小数最小値が設定されている場合、エラー
        if retBool and decimal_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20183", [])
        # 小数最大値が設定されている場合、エラー
        if retBool and decimal_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20184", [])
        # 小数桁数が設定されている場合、エラー
        if retBool and decimal_digit:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20185", [])
        # メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and pulldown_selection:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20186", [])
        # パスワード最大バイト数が設定されていない場合、エラー
        if retBool and password_maximum_bytes is None:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20187", [])
        # ファイルアップロード/ファイル最大バイト数が設定されている場合、エラー
        if retBool and file_upload_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20188", [])
        # リンク/最大バイト数が設定されている場合、エラー
        if retBool and link_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20189", [])
        # 参照項目が設定されている場合、エラー
        if retBool and reference_item:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20190", [])
        # 初期値(文字列(単一行))が設定されている場合、エラー
        if retBool and single_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20191", [])
        # 初期値(文字列(複数行))が設定されている場合、エラー
        if retBool and multi_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20192", [])
        # 初期値(整数)が設定されている場合、エラー
        if retBool and integer_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20193", [])
        # 初期値(小数)が設定されている場合、エラー
        if retBool and decimal_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20194", [])
        # 初期値(日時)が設定されている場合、エラー
        if retBool and datetime_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20195", [])
        # 初期値(日付)が設定されている場合、エラー
        if retBool and date_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20196", [])
        # 初期値(リンク)が設定されている場合、エラー
        if retBool and link_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20197", [])
        # 初期値(プルダウン選択)が設定されている場合、エラー
        if retBool and pulldown_selection_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20198", [])
        # パラメータシート参照/メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and parameter_sheet_reference:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20199", [])

    # 入力方式がファイルアップロードの場合
    elif column_class == "9":
        # 文字列(単一行)最大バイト数が設定されている場合、エラー
        if retBool and single_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20200", [])
        # 文字列(単一行)正規表現が設定されている場合、エラー
        if retBool and single_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20201", [])
        # 文字列(複数行)最大バイト数が設定されている場合、エラー
        if retBool and multi_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20202", [])
        # 文字列(複数行)正規表現が設定されている場合、エラー
        if retBool and multi_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20203", [])
        # 整数最小値が設定されている場合、エラー
        if retBool and integer_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20204", [])
        # 整数最大値が設定されている場合、エラー
        if retBool and integer_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20205", [])
        # 小数最小値が設定されている場合、エラー
        if retBool and decimal_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20206", [])
        # 小数最大値が設定されている場合、エラー
        if retBool and decimal_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20207", [])
        # 小数桁数が設定されている場合、エラー
        if retBool and decimal_digit:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20208", [])
        # メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and pulldown_selection:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20209", [])
        # パスワード最大バイト数が設定されている場合、エラー
        if retBool and password_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20210", [])
        # ファイルアップロード/ファイル最大バイト数が設定されていない場合、エラー
        if retBool and file_upload_maximum_bytes is None:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20211", [])
        # リンク/最大バイト数が設定されている場合、エラー
        if retBool and link_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20212", [])
        # 参照項目が設定されている場合、エラー
        if retBool and reference_item:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20213", [])
        # 初期値(文字列(単一行))が設定されている場合、エラー
        if retBool and single_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20214", [])
        # 初期値(文字列(複数行))が設定されている場合、エラー
        if retBool and multi_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20215", [])
        # 初期値(整数)が設定されている場合、エラー
        if retBool and integer_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20216", [])
        # 初期値(小数)が設定されている場合、エラー
        if retBool and decimal_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20217", [])
        # 初期値(日時)が設定されている場合、エラー
        if retBool and datetime_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20218", [])
        # 初期値(日付)が設定されている場合、エラー
        if retBool and date_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20219", [])
        # 初期値(リンク)が設定されている場合、エラー
        if retBool and link_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20220", [])
        # 初期値(プルダウン選択)が設定されている場合、エラー
        if retBool and pulldown_selection_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20221", [])
        # パラメータシート参照/メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and parameter_sheet_reference:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20222", [])

    # 入力方式がリンクの場合
    elif column_class == "10":
        # 文字列(単一行)最大バイト数が設定されている場合、エラー
        if retBool and single_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20223", [])
        # 文字列(単一行)正規表現が設定されている場合、エラー
        if retBool and single_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20224", [])
        # 文字列(複数行)最大バイト数が設定されている場合、エラー
        if retBool and multi_string_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20225", [])
        # 文字列(複数行)正規表現が設定されている場合、エラー
        if retBool and multi_string_regular_expression:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20226", [])
        # 整数最小値が設定されている場合、エラー
        if retBool and integer_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20227", [])
        # 整数最大値が設定されている場合、エラー
        if retBool and integer_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20228", [])
        # 小数最小値が設定されている場合、エラー
        if retBool and decimal_minimum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20229", [])
        # 小数最大値が設定されている場合、エラー
        if retBool and decimal_maximum_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20230", [])
        # 小数桁数が設定されている場合、エラー
        if retBool and decimal_digit:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20231", [])
        # メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and pulldown_selection:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20232", [])
        # パスワード最大バイト数が設定されている場合、エラー
        if retBool and password_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20233", [])
        # ファイルアップロード/ファイル最大バイト数が設定されている場合、エラー
        if retBool and file_upload_maximum_bytes:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20234", [])
        # リンク/最大バイト数が設定されていない場合、エラー
        if retBool and link_maximum_bytes is None:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20235", [])
        # 参照項目が設定されている場合、エラー
        if retBool and reference_item:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20236", [])
        # 初期値(文字列(単一行))が設定されている場合、エラー
        if retBool and single_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20237", [])
        # 初期値(文字列(複数行))が設定されている場合、エラー
        if retBool and multi_string_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20238", [])
        # 初期値(整数)が設定されている場合、エラー
        if retBool and integer_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20239", [])
        # 初期値(小数)が設定されている場合、エラー
        if retBool and decimal_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20240", [])
        # 初期値(日時)が設定されている場合、エラー
        if retBool and datetime_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20241", [])
        # 初期値(日付)が設定されている場合、エラー
        if retBool and date_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20242", [])
        # 初期値(プルダウン選択)が設定されている場合、エラー
        if retBool and pulldown_selection_default_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20243", [])
        # パラメータシート参照/メニューグループ：メニュー：項目が設定されている場合、エラー
        if retBool and parameter_sheet_reference:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-20244", [])
        # 最大バイト数と初期値の条件一致をチェック
        if retBool and link_default_value:
            hex_value = str(link_default_value)
            hex_value = binascii.b2a_hex(hex_value.encode('utf-8'))
            if int(link_maximum_bytes) < int(len(hex_value)) / 2:
                retBool = False
                msg = g.appmsg.get_api_message("MSG-20245", [])

    # 同一メニューでプルダウン選択を利用している項目を取得
    table_name = "T_MENU_COLUMN"
    where_str = "WHERE DISUSE_FLAG = '0' AND MENU_CREATE_ID = %s AND COLUMN_CLASS = '7'"
    bind_value_list = [menu_create_id]
    return_values = objdbca.table_select(table_name, where_str, bind_value_list)
    if return_values:
        # プルダウン選択の参照項目の項目名を確認し、同一の項目名を使用していないかをチェックする
        for record in return_values:
            pulldown_target_column_name_rest = record.get('COLUMN_NAME_REST')
            reference_item = record.get('REFERENCE_ITEM')
            # 参照項目がある場合処理を続行
            if reference_item:
                # 参照項目の値をlist型に変換
                reference_item_list = ast.literal_eval(reference_item)

                # 参照項目リストを取得
                target_pulldown_selection = record.get('OTHER_MENU_LINK_ID')
                table_name = "V_MENU_REFERENCE_ITEM"
                where_str = "WHERE DISUSE_FLAG = '0' AND LINK_ID = %s"
                bind_value_list = [target_pulldown_selection]
                return_values_2 = objdbca.table_select(table_name, where_str, bind_value_list)

                # 項目名が参照項目と一致しているかどうかを確認
                check_bool_1 = False
                for ref_column_name_rest in reference_item_list:
                    for record in return_values_2:
                        if ref_column_name_rest == item_name_rest:
                            check_column_name_ja = record.get('COLUMN_NAME_JA')
                            if item_name_ja == check_column_name_ja:
                                check_bool_1 = True
                                target_column_name = check_column_name_ja
                                break

                            check_column_name_en = record.get('COLUMN_NAME_EN')
                            if item_name_en == check_column_name_en:
                                check_bool_1 = True
                                target_column_name = check_column_name_en
                                break

                if check_bool_1:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-20255", [target_column_name])
                    return retBool, msg, option

                # パラメータシート作成実行時に生成される参照項目用の「項目名(rest)」が他の項目名(rest)で使用されているかを確認
                check_bool_2 = False
                for count, ref_column_name_rest in enumerate(reference_item_list, 1):
                    create_ref_column_name_rest = str(pulldown_target_column_name_rest) + "_ref_" + str(count)
                    if item_name_rest == create_ref_column_name_rest:
                        check_bool_2 = True
                        break

                if check_bool_2:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-20256", [item_name_rest])
                    return retBool, msg, option

    return retBool, msg, option


def file_upload_maximum_bytes_valid_before(objdbca, objtable, option):

    retBool = True
    msg = ''

    if option["cmd_type"] in ["Update", "Register", "Restore"]:
        # 更新後レコードから値を取得
        # ファイルアップロード/最大バイト数
        file_upload_maximum_bytes = option["entry_parameter"]["parameter"]["file_upload_maximum_bytes"]

        # Organization毎のアップロードファイルサイズ上限取得
        org_upload_file_size_limit = get_org_upload_file_size_limit(g.get("ORGANIZATION_ID"))

        if file_upload_maximum_bytes is not None and org_upload_file_size_limit is not None:
            if int(file_upload_maximum_bytes) > org_upload_file_size_limit:
                retBool = False
                status_code = 'MSG-00019'
                msg_args = [1, org_upload_file_size_limit, file_upload_maximum_bytes]
                msg = g.appmsg.get_api_message(status_code, msg_args)

    return retBool, msg, option,

