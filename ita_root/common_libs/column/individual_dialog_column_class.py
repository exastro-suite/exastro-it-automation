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
from flask import g
from common_libs.common import *
from common_libs.common.util import print_exception_msg, get_iso_datetime, arrange_stacktrace_format

# import column_class
from .id_class import IDColumn


class IndividualDialogColumn(IDColumn):
    """
    個別ダイアログ(親クラス)
    """
    def get_values_by_value(self, where_equal=[], where_like=""):
        """
            valueを検索条件に値を取得する
            ARGS:
                where_equal:一致検索のリスト(list)
                where_like:あいまい検索の値(string)
            RETRUN:
                values:検索結果
        """
        tmp_values = {}
        values = {}

        # データリストを取得
        if self.class_name == 'ConclusionEventSettingColumn':
            id_data_list = self.search_id_data_list()
        elif self.class_name == 'FilterConditionSettingColumn':
            id_data_list = self.get_master_label_name(self.search_id_data_list())

        # 一致検索
        if len(where_equal) > 0:
            for where_value in where_equal:
                for key, value in id_data_list.items():
                    if str(where_value) == str(value):
                        tmp_values[key] = value
        else:
            tmp_values = id_data_list

        # あいまい検索
        if len(where_like) > 0:
            for key, value in tmp_values.items():
                if where_like in value:
                    values[key] = value
        else:
            values = tmp_values

        return values

    def json_key_to_keyname_convart(self, column_value, search_candidates, master_row):
        """
            JSON形式で格納されているKey(DB)を名称リストに変換
            フィルタのプルダウン検索に表示する内容
            ARGS:
                column_value:  JSON形式で格納されている値
                               [{"label_name": uuid, "condition_type": uuid, "condition_value": 値] ... }
                search_candidates: 名称リスト
                master_row:    マスタテーブルデータ {key: value, ...}
            RETRUN:
                名称リスト
        """
        if self.class_name == 'FilterConditionSettingColumn':
            master_row = self.get_master_label_name(master_row)

        try:
            if not column_value:
                column_value = []
                column_value = json.dumps(column_value)
            column_value = json.loads(column_value)
            if len(column_value) > 0:
                for lable_row in column_value:
                    if len(lable_row) != len(self.json_tag):
                        raise Exception("JSON format is (abnormal json data:({}))".format(str(column_value)))
        except Exception as e:
            raise e

        if isinstance(column_value, list):
            for lable_row in column_value:
                key = lable_row[self.tag_label]
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
                bindvalues.setdefault(bindkey, "%{}%".format(bindvalue))
                listno += 1

            str_where = ""
            for bindkey in bindkeys:
                tmp_where = " JSON_UNQUOTE(JSON_EXTRACT(`{col_name}`, \"$[*].{label_name}\")) like {bindkey} ".format(
                    col_name = self.get_col_name(),
                    label_name = self.tag_label,
                    bindkey = bindkey
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


    # [load_table] 値を入力用の値へ変換
    def convert_value_input(self, valnames=''):
        """
            値を出力用の値へ変換 (DB->UI)
            DB: [{"label_key": "key01", "label_value": "True"}....]
            UI: [[key01に対応した名称, "True"]....]
            ARGS:
                val:値
            RETRUN:
                retBool, msg, val
        """
        retBool = True
        retdict = []
        msg = ''

        if not valnames:
            return True, '', valnames,
        val_decode = self.is_json_format(valnames)
        if val_decode is False:
            print_exception_msg("JSON format is abnormal")
            retBool = False
            status_code = '499-01703'
            msg_args = []
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return retBool, msg
        if len(val_decode) == 0:
            return True, '', None,
        if val_decode is not None:
            for val in val_decode:
                ret, msg, return_values = self.get_input_values_by_value(val)
                if ret is False:
                    return False, msg, val,
                else:
                    # val = list(return_values.keys())[0]
                    retdict.append(return_values)

        # ユニーク制約をする為に、Key値をソートしてDBに保存
        sortdict = self.sort_for_unique_constraints(retdict)

        return retBool, msg, json.dumps(sortdict),


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
            val_decode = self.is_json_format(valnames)
            if val_decode is False:
                print_exception_msg("JSON format is abnormal")
                retBool = False
                status_code = '499-01703'
                msg_args = []
                msg = g.appmsg.get_api_message(status_code, msg_args)
                return retBool, msg

            if len(val_decode) > 0:
                for val in val_decode:
                    ret, msg, return_values = self.get_input_values_by_value(val)
                    # 返却値が存在するか確認
                    if ret is False:
                        return False, msg

                    # 同じ値が複数あるか判定

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

        return retBool, msg,

    # jsonフォーマットを確認
    def is_json_format(self, val):
        """
            jsonフォーマットを確認
            ARGS:
                val: jsonフォーマット
                    [[ラベル, 演算子, 値]...]
            RETRUN:
                ( True / False , メッセージ )
        """
        try:
            if val is None:
                raise AppException("JSON format is abnormal (1) json data:{}".format(str(val)))
            val = json.loads(val)
            if type(val) is not list:
                raise AppException("JSON format is abnormal (2) json data:{}".format(str(val)))
            else:
                if len(val) > 0:
                    for val_line in val:
                        if type(val) is not list:
                            raise AppException("JSON format is abnormal (3) json data:{}".format(str(val)))
                        else:
                            if len(val_line) != len(self.json_tag):
                                raise AppException("JSON format is abnormal (4) json data:{}".format(str(val)))
            return val
        except AppException as e:
            msg, arg1, arg2 = e.args
            print_exception_msg(msg)
            return False

    # DBに登録するデータをユニーク制約用にKey値でソートする
    def sort_for_unique_constraints(self, inlist):
        retlist = []
        sortlist = []
        size = len(inlist)
        line = 0
        for row in inlist:
            if self.class_name == 'ConclusionEventSettingColumn':
                pattern = "{}_{}_{:0" + str(size) + "}"
                key = pattern.format(row[self.tag_label], row[self.tag_value], line)
            elif self.class_name == 'FilterConditionSettingColumn':
                pattern = "{}_{}_{}_{:0" + str(size) + "}"
                key = pattern.format(row[self.tag_label], row[self.tag_condition],row[self.tag_value],line)
            line += 1
            sortlist.append(key)
        sortlist.sort()
        for row in sortlist:
            line = row[-size:]
            retlist.append(inlist[int(line)])
        return retlist

