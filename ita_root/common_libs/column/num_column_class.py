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
カラムクラス個別処理(NumColumn)
"""


class NumColumn(Column):
    """
    数値系クラス共通処理
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
            バリデーション処理
            ARGS:
                val:値
                option:オプション
            RETRUN:
                ( True / False , メッセージ )
        """
        retBool = True
        # 閾値(最小値)
        min_num = None
        # 閾値(最大値)
        max_num = None

        if val is not None:
            try:
                val = int(val)
                # カラムの設定を取得
                objcols = self.get_objcols()
                if objcols is not None:
                    if self.get_rest_key_name() in objcols:
                        dict_valid = self.get_dict_valid()
                        # 閾値(最小値)
                        min_num = dict_valid.get('int_min')
                        # 閾値(最大値)
                        max_num = dict_valid.get('int_max')

                        # Noneの際,int範囲(-2147483648～2147483647)外の場合、設定上書き
                        if min_num is None:
                            min_num = -2147483648
                        if max_num is None:
                            max_num = 2147483647

                if min_num is None and max_num is None:
                    # 最小値、最大値閾値無し
                    retBool = True
                elif min_num is not None and max_num is not None:
                    # 最小値、最大値閾値あり
                    if min_num <= val <= max_num:
                        retBool = True
                    else:
                        retBool = False
                        status_code = 'MSG-00019'
                        msg_args = [min_num, max_num, val]
                        msg = g.appmsg.get_api_message(status_code, msg_args)
                        return retBool, msg

                elif min_num is not None:
                    # 最小値閾値あり
                    if min_num <= val:
                        retBool = True
                    else:
                        retBool = False
                        status_code = 'MSG-00020'
                        msg_args = [min_num, val]
                        msg = g.appmsg.get_api_message(status_code, msg_args)
                        return retBool, msg
                elif max_num is not None:
                    # 最大値閾値あり
                    if val <= max_num:
                        retBool = True
                    else:
                        retBool = False
                        status_code = 'MSG-00021'
                        msg_args = [max_num, val]
                        msg = g.appmsg.get_api_message(status_code, msg_args)
                        return retBool, msg
            except ValueError:
                retBool = False
                status_code = 'MSG-00031'
                msg_args = [val]
                msg = g.appmsg.get_api_message(status_code, msg_args)
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
            if val is not None:
                val = int(val)
        except Exception:
            retBool = False
            status_code = 'MSG-00031'
            msg_args = [val]
            msg = g.appmsg.get_api_message(status_code, msg_args)
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
            if val is not None:
                val = int(val)
        except Exception:
            retBool = False
            status_code = 'MSG-00031'
            msg_args = [val]
            msg = g.appmsg.get_api_message(status_code, msg_args)
        return retBool, msg, val
