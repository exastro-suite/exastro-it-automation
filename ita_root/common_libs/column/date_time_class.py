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
from datetime import datetime
from .column_class import Column
from flask import g
from common_libs.common.exception import AppException
import json


class DateTimeColumn(Column):
    """
    カラムクラス個別処理(DateTimeColumn)
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

        # 下限値
        self.min_value = '1000/01/01 00:00:00'
        # 上限値
        self.max_value = '9999/12/31 23:59:59'
        # datetime変換用フォーマット
        self.format_datetime = '%Y/%m/%d %H:%M:%S'
        # ログ出力用フォーマット
        self.format_for_log = 'YYYY/MM/DD hh:mm:ss'

    def check_basic_valid(self, val, option={}):
        """
            バリデーション処理(カラムクラス毎)
            ARGS:
                val:値
            RETRUN:
                True / エラーメッセージ
        """
        retBool = True

        # 閾値(最小値)
        min_datetime = datetime.strptime(self.min_value, self.format_datetime)
        # 閾値(最大値)
        max_datetime = datetime.strptime(self.max_value, self.format_datetime)

        if len(str(val)) == 0:
            return retBool,

        # 日付形式のチェック
        # YYYY/MM/DD hh:mm:ssの場合OK
        if re.match(r'^[0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$', val) is not None:
            retBool = True
        # YYYY/MM/DD hh:mmの場合OK、:ssを補完
        elif re.match(r'^[0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}$', val) is not None:
            val = val + ':00'
        # YYYY/MM/DDの場合OK、:hh:mm:ssを補完
        elif re.match(r'^[0-9]{4}/[0-9]{2}/[0-9]{2}$', val) is not None:
            val = val + ' 00:00:00'
        else:
            msg = g.appmsg.get_api_message("MSG-00002", [self.format_for_log, val])
            retBool = False
            return retBool, msg

        # 日付形式に変換
        try:
            dt_val = datetime.strptime(val, self.format_datetime)
        except ValueError as msg:
            msg = g.appmsg.get_api_message("MSG-00002", [self.format_for_log, val])
            retBool = False
            return retBool, msg

        # 上限、下限チェック
        if min_datetime is not None and max_datetime is not None:
            if min_datetime > dt_val or dt_val > max_datetime:
                retBool = False
                msg = g.appmsg.get_api_message("MSG-00003", [self.min_value, self.max_value, val])
                return retBool, msg

        return retBool,

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

        if val is not None and len(str(val)) > 0:
            val = val[0:19]

        return retBool, msg, val

    # RANGE検索のフォーマットチェック
    def check_range_format(self, val):
        """
            出力用の値へ変換
            ARGS:
                val:値
            RETRUN:
                retBool
        """

        # 日付形式のチェック
        # Noneまたは空文字の場合はエラー
        if val is None or len(val) == 0:
            retBool = False
        # YYYY/MM/DD hh:mm:ssの場合OK
        elif re.match(r'^[0-9]{4}/(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01]) ([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$', val) is not None:
            retBool = True
        # YYYY/MM/DD hh:mmの場合OK
        elif re.match(r'^[0-9]{4}/(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01]) ([01][0-9]|2[0-3]):[0-5][0-9]$', val) is not None:
            retBool = True
        # YYYY/MM/DDの場合OK
        elif re.match(r'^[0-9]{4}/(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])$', val) is not None:
            retBool = True
        else:
            retBool = False

        if retBool is False:
            msg_tmp = {0: {}}
            msg_tmp[0][self.rest_key_name] = [g.appmsg.get_api_message("MSG-00002", [self.format_for_log, val])]
            msg = json.dumps(msg_tmp, ensure_ascii=False)
            raise AppException("499-00201", [msg], [msg])

        return retBool
