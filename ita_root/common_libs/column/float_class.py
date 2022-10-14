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

from flask import g
from .column_class import Column


class FloatColumn(Column):
    """
    カラムクラス個別処理(NumColumn)
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
        preg_match = r'^((-[1-9])?[0-9]{0,}|-0)(\.[0-9]{0,})?$'

        if preg_match is not None:
            if len(preg_match) != 0:
                pattern = re.compile(preg_match, re.DOTALL)
                tmp_result = pattern.fullmatch(str(val))
                if tmp_result is None:
                    retBool = False
                    msg = g.appmsg.get_api_message('MSG-00009', [preg_match, val])
                    return retBool, msg

        if val is not None:
            # カラムの設定を取得
            objcols = self.get_objcols()
            if objcols is not None:
                if self.get_rest_key_name() in objcols:
                    dict_valid = self.get_dict_valid()
                    # 閾値(最小値)
                    min_num = dict_valid.get('float_min')
                    # 閾値(最大値)
                    max_num = dict_valid.get('float_max')
                    # 閾値(桁数）
                    max_digit = dict_valid.get('float_digit')

            # ドットを抜いた桁数を比較
            if max_digit is not None:
                srt_val = str(val)
                if "." in srt_val:
                    srt_val = srt_val.rstrip("0")
                vlen = int(len(srt_val))
                if "." in srt_val or "-" in srt_val:
                    vlen -= 1
                if int(max_digit) < vlen:
                    retBool = False
                    msg = g.appmsg.get_api_message('MSG-00018', [max_digit, vlen])
                    return retBool, msg

            if min_num is None and max_num is None:
                # 最小値、最大値閾値無し
                retBool = True
            elif min_num is not None and max_num is not None:
                # 最小値、最大値閾値あり
                if float(min_num) <= float(val) <= float(max_num):
                    retBool = True
                else:
                    retBool = False
                    msg = g.appmsg.get_api_message('MSG-00019', [min_num, max_num, val])
                    return retBool, msg

            elif min_num is not None:
                # 最小値閾値あり
                if float(min_num) <= float(val):
                    retBool = True
                else:
                    retBool = False
                    msg = g.appmsg.get_api_message('MSG-00020', [min_num, val])
                    return retBool, msg
            elif max_num is not None:
                # 最大値閾値あり
                if float(val) <= float(max_num):
                    retBool = True
                else:
                    retBool = False
                    msg = g.appmsg.get_api_message('MSG-00021', [max_num, val])
                    return retBool, msg

        return retBool,
