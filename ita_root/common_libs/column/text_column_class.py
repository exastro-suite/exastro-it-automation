# Copyright 2022 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import re

import os
import sys

from flask import g
from .column_class import Column

"""
カラムクラス個別処理(TextColumn)
"""


class TextColumn(Column):
    """
    テキスト系クラス共通処理
    """
    def __init__(self, objdbca, objtable, rest_key_name, cmd_type):
        # カラムクラス名
        self.class_name = self.__class__.__name__
        # メッセージ
        self.message = ''
        # バリデーション閾値
        self.dict_valid = {}
        # テーブル情報
        self.objtable = objtable

        # テーブル名
        table_name = ''
        objmenu = objtable.get('MENUINFO')
        if objmenu is not None:
            table_name = objmenu.get('TABLE_NAME')
        self.table_name = table_name

        # カラム名
        col_name = ''
        objcols = objtable.get('COLINFO')
        if objcols is not None:
            objcol = objcols.get(rest_key_name)
            if objcol is not None:
                col_name = objcol.get('COL_NAME')

        self.col_name = col_name
        
        # rest用項目名
        self.rest_key_name = rest_key_name

        self.db_qm = "'"

        self.objdbca = objdbca

        self.cmd_type = cmd_type

    def check_basic_valid(self, val, option={}):
        """
            バリデーション処理(カラムクラス毎)
            ARGS:
                val:値
                option:オプション
            RETRUN:
                ( True / False , メッセージ )
        """
        retBool = True
        
        min_length = 0
        max_length = None

        if val is not None:
            val = str(val)
            # カラムの閾値を取得
            objcols = self.get_objcols()
            if objcols is not None:
                if self.get_rest_key_name() in objcols:
                    dict_valid = self.get_dict_valid()
                    # 閾値(文字列長)
                    max_length = dict_valid.get('max_length')
                    min_length = dict_valid.get('min_length')
                    if min_length is None:
                        min_length = 0

            # 文字列長
            if max_length is not None:
                check_val = len(str(val).encode('utf-8'))
                if check_val != 0:
                    if int(min_length) <= check_val <= int(max_length):
                        retBool = True
                    else:
                        retBool = False
                        msg = g.appmsg.get_api_message('MSG-00008', [max_length, check_val])
                        return retBool, msg

            # 正規表現
            preg_match = self.get_reg_exp()
            if preg_match is not None:
                if len(preg_match) != 0:
                    pattern = re.compile(r'{}'.format(preg_match), re.DOTALL)
                    tmp_result = pattern.fullmatch(val)
                    if tmp_result is None:
                        retBool = False
                        msg = g.appmsg.get_api_message('MSG-00009', [preg_match, val])
                        return retBool, msg

        return retBool,
