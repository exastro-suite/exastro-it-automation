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

import os
import sys
from flask import g
from common_libs.common import *

# import column_class
from .multi_select_id_class import MultiSelectIDColumn  # noqa: F401


class NotificationIDColumn(MultiSelectIDColumn):
    """
    カラムクラス個別処理(通知先 IDColumn)
    """
    def search_id_data_list(self):
        """
            データリストを検索する
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        values = {}
        values[str(1)] = 'Ｋｅｙ1'
        values[str(2)] = 'Ｋｅｙ2'
        values[str(3)] = 'Ｋｅｙ3'
        values[str(4)] = 'Ｋｅｙ4'
        values[str(5)] = 'Ｋｅｙ5'
        values[str(6)] = 'Ｋｅｙ6'
        values[str(7)] = 'Ｋｅｙ7'
        values[str(8)] = 'Ｋｅｙ8'
        values[str(9)] = 'Ｋｅｙ9'
        values[str(10)] = 'Ｋｅｙ10'

        return values

    def json_key_to_keyname_convart(self, column_value, search_candidates, master_row):
        """
            JSON形式で格納されているKeyを名称リストに変換
            フィルタのプルダウン検索の表示する内容
            ARGS:
                column_value:  JSON形式で格納されている{"id": ["key1", ..]}"
                search_candidates: 名称リスト
                master_row:    マスタテーブルデータ {key: value, ...}
            RETRUN:
                名称リスト
        """
        try:
            json_rows = json.loads(column_value)
            if type(json_rows['id']) != list:
                raise Exception("JSON format is abnormal")
        except Exception as e:
            raise Exception(e)

        if isinstance(json_rows["id"], list):
            keys = json_rows["id"]
            for key in keys:
                if key in master_row.keys():
                    val = master_row[key]
                    if not search_candidates.count(val):
                        search_candidates.append(val)
                    else:
                        pass
                        # 廃止されているデータをID変換失敗(key)として扱わない
                        # val = g.appmsg.get_api_message('MSG-00001', [key])
                        # if not search_candidates.count(val):
                        #     search_candidates.append(val)
        return search_candidates

    # [filter] SQL生成用のwhere句
    def get_filter_query(self, search_mode, search_conf):
        """
            SQL生成用のwhere句関連
            ARGS:
                search_mode: 検索種別[LIST/NOMAL/RANGE]
                search_conf: 検索条件
            RETRUN:
                {"bindkey":XXX,bindvalue :{ XXX: val },where: string }
        """
        result = {}
        tmp_conf = []
        listno = 0
        bindkeys = []
        bindvalues = {}
        str_where = ''

        if search_mode == "LIST":
            # マスタを検索
            return_values = self.get_values_by_value(search_conf)

            if len(return_values) > 0:
                tmp_conf = list(return_values.keys())
            else:
                tmp_conf.append("NOT FOUND")

        elif search_mode == "NORMAL":
            # マスタを検索
            return_values = self.get_values_by_value([], search_conf)

            if len(return_values) > 0:
                tmp_conf = list(return_values.keys())
            else:
                tmp_conf.append("NOT FOUND")

        if search_mode in ["LIST", "NORMAL"]:
            for bindvalue in tmp_conf:
                bindkey = "__{}__{}__".format(self.get_col_name(), listno)
                bindkeys.append(bindkey)
                # 前後にダブルコーテーションが必要
                bindvalues.setdefault(bindkey, "\"{}\"".format(bindvalue))
                listno += 1

            str_where = ""
            for bindkey in bindkeys:
                tmp_where = " JSON_CONTAINS(`{col_name}`, {bindkey}, '$.id') ".format(
                    col_name=self.get_col_name(),
                    bindkey=bindkey
                )
                if len(str_where) > 0:
                    str_where += " OR "
                str_where += tmp_where
            if len(bindkeys) > 0:
                str_where = "(" + str_where + ")"

        result.setdefault("bindkey", bindkeys)
        result.setdefault("bindvalue", bindvalues)
        result.setdefault("where", str_where)

        return result

    # [load_table] 値を出力用の値へ変換
    def convert_value_output(self, val=''):
        """
            値を出力用の値へ変換
            ARGS:
                val:値
            RETRUN:
                retBool, msg, val
        """
        msg = ''

        master_row = self.search_id_data_list()

        try:
            if not val:
                val = {}
                val['id'] = []
                val = json.dumps(val)
            json_val = json.loads(val)
            if type(json_val["id"]) != list:
                status_code = 'MSG-00001'
                msg_args = ["JSON format error(not list) data(%s)" % (str(val))]
                val = g.appmsg.get_api_message(status_code, msg_args)
                return False, msg, val,
        except Exception as e:
            retBool = False
            status_code = '499-01701'
            msg_args = []
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return retBool, msg

        search_candidates = []
        if isinstance(json_val["id"], list):
            keys = json_val["id"]
            for key in keys:
                if key in master_row.keys():
                    val = master_row[key]
                    if not search_candidates.count(val):
                        search_candidates.append(val)
                else:
                    # 廃止されているデータをID変換失敗(key)として扱う
                    val = g.appmsg.get_api_message('MSG-00001', [key])
                    if not search_candidates.count(val):
                        search_candidates.append(val)
        else:
            status_code = 'MSG-00001'
            msg_args = ["JSON format error(not list) data(%s)" % (str(val))]
            val = g.appmsg.get_api_message(status_code, msg_args)
            return False, msg, val,
        value_list = json.dumps(search_candidates, ensure_ascii=False)
        return True, msg, value_list,

    # [load_table] 値を入力用の値へ変換
    def convert_value_input(self, valnames=''):
        """
            値を入力用の値へ変換
            ARGS:
                vallist:値 "key name1, ..."
            RETRUN:
                retBool, msg, val
        """
        retBool = True
        retdict = {"id": []}
        msg = ''
        try:
            if valnames is None:
                 return True, [], valnames,
            val = json.loads(valnames)
            if type(val) != list:
                raise Exception("JSON format is abnormal")
        except Exception as e:
            retBool = False
            status_code = '499-01701'
            msg_args = []
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return retBool, msg

        if valnames is not None:
            for val in json.loads(valnames):
                return_values = self.get_values_by_value([val])

                if len(return_values) == 1:
                    # val = list(return_values.keys())[0]
                    retdict["id"].append(list(return_values.keys())[0])
                else:
                    retBool = False
                    status_code = 'MSG-00032'
                    msg_args = [val]
                    msg = g.appmsg.get_api_message(status_code, msg_args)
                    return retBool, msg, val,

        return retBool, msg, json.dumps(retdict),

    def check_basic_valid(self, valnames, option={}):
        """
            バリデーション処理(カラムクラス毎)
            ARGS:
                val:値
                option:オプション
            RETRUN:
                ( True / False , メッセージ )
        """
        retBool = True

        if valnames is not None:
            try:
                vallist = json.loads(valnames)
            except Exception:
                retBool = False
                status_code = '499-01701'
                msg_args = []
                msg = g.appmsg.get_api_message(status_code, msg_args)
                return retBool, msg

            set_Valses = []
            if len(vallist) > 0:
                for val in vallist:
                    return_values = self.get_values_by_value([val])
                    # 返却値が存在するか確認
                    if len(return_values) == 0:
                        retBool = False
                        status_code = 'MSG-00032'
                        msg_args = [val]
                        msg = g.appmsg.get_api_message(status_code, msg_args)
                        return retBool, msg

                    # 同じ値が複数あるか判定
                    if set_Valses.count(return_values) > 0:
                        retBool = False
                        status_code = '499-01702'
                        msg_args = [val]
                        msg = g.appmsg.get_api_message(status_code, msg_args)
                        return retBool, msg
                    set_Valses.append(return_values)

        return retBool,

    # [maintenance] 必須バリデーション
    def is_valid_required(self, val='', option={}):
        """
            一意バリデーション実施
            ARGS:
                col_name:カラム名
                val:値
            RETRUN:
                ( True / False , メッセージ )
        """
        retBool = True
        result = self.get_required()
        msg = ''
        if result == "1":
            if val is None:
                retBool = False
                status_code = 'MSG-00030'
                msg_args = []
                msg = g.appmsg.get_api_message(status_code, msg_args)
            else:
                val_list = json.loads(val)
                if len(val_list) == 0:
                    retBool = False
                    status_code = 'MSG-00030'
                    msg_args = []
                    msg = g.appmsg.get_api_message(status_code, msg_args)

        return retBool, msg,
