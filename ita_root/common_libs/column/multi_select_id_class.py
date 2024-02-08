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
import json
from flask import g
from common_libs.common import *

# import column_class
from .id_class import IDColumn


class MultiSelectIDColumn(IDColumn):
    """
    マルチ選択プルダウン親クラス
    """
    def json_key_to_keyname_convart(self, column_value, search_candidates, master_row):
        """
            SON形式で格納されているKey(DB)を名称リストに変換
            フィルタのプルダウン検索の表示する内容
            ARGS:
                column_value:  JSON形式で格納されている{"id": ["key1", ..]}"
                search_candidates: 名称リスト
                master_row:    マスタテーブルデータ {key: value, ...}
            RETRUN:
                名称リスト
        """
        try:
            if not column_value:
                column_value = {}
                column_value["id"] = []
                column_value = json.dumps(column_value)
            column_value = json.loads(column_value)
            if type(column_value['id']) != list:
                raise Exception("JSON format is abnormal")
        except Exception as e:
            raise Exception(e)

        if isinstance(column_value["id"], list):
            keys = column_value["id"]
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
                exp_args = "Not in JSON list format data(%s)" % (str(val))
                raise Exception(exp_args)
        except Exception as e:
            # エラーでリターンの処理がないのでException
            status_code = '499-01708'
            msg_args = [str(val)]
            msg = g.appmsg.get_api_message(status_code, msg_args)
            raise Exception(status_code, msg)

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

        # 全角文字対応　ensure_ascii=False
        return True, msg, json.dumps(search_candidates, ensure_ascii=False),

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
            if not valnames:
                return True, '', valnames,
            val_decode = self.is_json_format(valnames)
            if val_decode is False:
                raise Exception("JSON format is abnormal")
            if len(val_decode) == 0:
                return True, '', None,
        except Exception as e:
            retBool = False
            status_code = '499-01701'
            msg_args = []
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return retBool, msg

        if val_decode is not None:
            for val in val_decode:
                return_values = self.get_values_by_value([val])

                if len(return_values) == 1:
                    # val = list(return_values.keys())[0]
                    retdict["id"].append(list(return_values.keys())[0])
                    # ユニーク判定をする為に、Key値をソートしてDBに保存
                    retdict["id"].sort()
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

        val_decode = None
        if valnames:
            try:
                val_decode = self.is_json_format(valnames)
                if val_decode is False:
                    raise Exception("JSON format is abnormal")

            except Exception:
                retBool = False
                status_code = '499-01701'
                msg_args = []
                msg = g.appmsg.get_api_message(status_code, msg_args)
                return retBool, msg

            set_Valses = []
            if len(val_decode) > 0:
                for val in val_decode:
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

        min_length = 0
        max_length = None

        if val_decode:
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
                check_val = len(str(val_decode).encode('utf-8'))
                if check_val != 0:
                    if int(min_length) <= check_val <= int(max_length):
                        retBool = True
                    else:
                        retBool = False
                        msg = g.appmsg.get_api_message('MSG-00008', [max_length, check_val])
                        return retBool, msg

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
                val_decode = self.is_json_format(val)
                if val_decode is False:
                    retBool = False
                    status_code = '499-01701'
                    msg_args = []
                    msg = g.appmsg.get_api_message(status_code, msg_args)
                else:
                    if len(val_decode) == 0:
                        retBool = False
                        status_code = 'MSG-00030'
                        msg_args = []
                        msg = g.appmsg.get_api_message(status_code, msg_args)

        return retBool, msg,

    # jsonフォーマットを確認
    def is_json_format(self, val):
        try:
            val = json.loads(val)
            if type(val) != list:
                raise Exception("JSON format is abnormal")
            return val
        except Exception:
            import inspect, os
            file_name = os.path.basename(inspect.currentframe().f_code.co_filename)
            line_no = str(inspect.currentframe().f_lineno)
            msg = "Exception: {} ({}:{})".format(str(e), file_name, line_no)
            g.applogger.info(msg) # 外部アプリへの処理開始・終了ログ
            return False
