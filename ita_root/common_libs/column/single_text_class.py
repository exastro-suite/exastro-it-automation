# Copyright 2022 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either expPress or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import re

# import text_column_class
from flask import g
from .text_column_class import TextColumn

"""
カラムクラス個別処理(SingleText)
"""


class SingleTextColumn(TextColumn):
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
        preg_match = r"^[^\t\r\n]*$"

        if val is not None:
            val = str(val)

            # 親クラスのvalidation確認。
            validate_result = super().check_basic_valid(val)
            if validate_result[0] is not True:
                return validate_result

            # 正規表現
            pattern = re.compile(preg_match, re.DOTALL)
            tmp_result = pattern.fullmatch(val)
            if tmp_result is None:
                retBool = False
                msg = g.appmsg.get_api_message('MSG-00009', [preg_match, val])
                return retBool, msg

        return retBool,

    # [load_table] 内部処理用の値へ変換
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
        if self.col_name == "DATA_JSON":
            # None以外は文字列型とする #2523
            val = str(val) if val is not None else val
        return retBool, msg, val

    # [load_table] 出力用の値へ変換
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
        if self.col_name == "DATA_JSON":
            # None以外は文字列型とする #2523
            val = str(val) if val is not None else val
        return retBool, msg, val