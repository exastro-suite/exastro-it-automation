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
import json

from flask import g
from .column_class import Column

"""
カラムクラス個別処理(JsonColmun)
"""


class JsonColumn(Column):
    """
    JsonColmun
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
        tmp_val = ''
        if isinstance(val, dict):
            tmp_val = json.dumps(val, ensure_ascii=False)

        if tmp_val is not None:
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
                    if max_length is None:
                        min_length = 1024 * 10
            # 文字列長
            if max_length is not None:
                check_val = len(str(tmp_val).encode('utf-8'))
                if check_val != 0:
                    if int(min_length) <= check_val <= int(max_length):
                        retBool = True
                    else:
                        retBool = False
                        msg = g.appmsg.get_api_message('MSG-00008', [max_length, check_val])
                        return retBool, msg
        
        return retBool,

    def convert_value_input(self, val=''):
        """
            内部処理用の値へ変換
            ARGS:
                val:値
            RETRUN:
                retBool, msg, val
        """
        retBool = True
        msg = ''
        try:
            if self.get_save_type() == "JSON":
                str_val = val
            else:
                if isinstance(val, str):
                    str_val = val
                else:
                    str_val = json.dumps(val, ensure_ascii=False)
        except Exception:
            str_val = val
        finally:
            val = str_val

        return retBool, msg, val
        
    def convert_value_output(self, val=''):
        """
            出力用の値へ変換
            ARGS:
                val:値
            RETRUN:
                retBool, msg, val
        """
        retBool = True
        msg = ''
        try:
            if self.get_save_type() == "JSON":
                if isinstance(val, str):
                    json_val = json.loads(val)
                else:
                    json_val = val
            else:
                json_val = json.loads(val)
        except Exception:
            json_val = val
        finally:
            val = json_val
        return retBool, msg, val
