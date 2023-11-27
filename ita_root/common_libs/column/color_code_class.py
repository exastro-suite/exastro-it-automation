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

import re

from flask import g
from .column_class import Column


class ColorCodeColumn(Column):
    """
    カラムクラス個別処理(ColorCodeColumn)
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

        retBool = False
        msg = ""

        # 値が無ければ処理を終了する
        if val is None:
            retBool = True
        else:
            # regex: カラーコードの正規表現
            regex = "^#([0-9a-fA-F]{6})$"
            regex_pattern = re.compile(regex)
            result = regex_pattern.search(val)
            if result:
                retBool = True
            else:
                status_code = '499-01709'
                msg_args = [val]
                msg = g.appmsg.get_api_message(status_code, msg_args)

        return retBool, msg
