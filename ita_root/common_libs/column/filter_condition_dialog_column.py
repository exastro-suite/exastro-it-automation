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
from .individual_dialog_column_class import IndividualDialogColumn  # noqa: F401


class FilterConditionSettingColumn(IndividualDialogColumn):
    """
    フィルタ条件設定ダイアログ
    """
    def search_id_data_list(self):
        """
            ラベル名と演算子のデータリストを検索する
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        values = {}
        values['label_name'] = self.search_label_id_data_list()
        values['condition_type'] = self.search_comparison_id_data_list()

        return values

    def search_label_id_data_list(self):
        """
            ラベル名のデータリストを検索する
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        values = {}
        values = super().search_id_data_list()

        values = {}
        values["key01"] = 'Ｋｅｙ1'
        values["key02"] = 'Ｋｅｙ2'
        values["key03"] = 'Ｋｅｙ3'
        values["key04"] = 'Ｋｅｙ4'
        values["key05"] = 'Ｋｅｙ5'
        values["key06"] = 'Ｋｅｙ6'
        values["key07"] = 'Ｋｅｙ7'
        values["key08"] = 'Ｋｅｙ8'
        values["key09"] = 'Ｋｅｙ9'
        values["key10"] = 'Ｋｅｙ10'

        return values

    def search_comparison_id_data_list(self):
        """
            演算子のデータリストを検索する
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        ref_table_name = "T_OASE_COMPARISON_METHOD"
        ref_pkey_name = "COMPARISON_METHOD_ID"
        ref_col_name = "COMPARISON_METHOD_SYMBOL"
        where_str = "WHERE `COMPARISON_METHOD_ID` in ('1', '2') AND `DISUSE_FLAG` = '0' "

        return_values = self.objdbca.table_select(ref_table_name, where_str, [])

        values = {}
        for record in return_values:
            values[record[ref_pkey_name]] = record[ref_col_name]

        return values

    def get_input_values_by_value(self, val):
        """
            UIで設定されたファイル条件のJSON値をマスタデータと付け合わせ
            キー値に変換する。
            ARGS:
                val: ["ラベル名", "条件", "値"]
            RETRUN:
                { "label_name": "ラベル名 uuid", "condition_type": "条件 uuid","condition_value": 値 }
        """

        result_value = {}

        # データリストを取得
        master_row = self.search_id_data_list()
        label_name_row = self.get_master_label_name(master_row)
        condition_type_row = self.get_master_condition_type(master_row)

        if not val[0]:
            status_code = '499-01705'
            msg_args = []
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return False, msg, result_value
        name_key = False
        for key, name in label_name_row.items():
            if name == val[0]:
                name_key = key
                break
        if name_key is False:
            status_code = 'MSG-00032'
            msg_args = [str(val[0])]   # true/false/数値対策
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return False, msg, result_value
        result_value["label_name"] = name_key

        if not val[1]:
            status_code = '499-01706'
            msg_args = []
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return False, msg, result_value
        name_key = False
        for key, name in condition_type_row.items():
            if name == val[1]:
                name_key = key
                break
        if name_key is False:
            status_code = 'MSG-00032'
            msg_args = [str(val[1])]  # true/false/数値対策
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return False, msg, result_value
        result_value["condition_type"] = name_key

        if not val[2]:
            status_code = '499-01707'
            msg_args = []
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return False, msg, result_value
        if type(val[2]) is not str:
            status_code = 'MSG-00032'
            msg_args = [str(val[2])] # true/false/数値対策
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return False, msg, result_value
        result_value["condition_value"] = val[2]

        return True, None, result_value

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
        id_data_list = self.get_master_label_name(self.get_id_data_list())

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

    def get_master_label_name(self, master_row):
        """
            ラベル名のデータリストのみを取り出す
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        return master_row['label_name']

    def get_master_condition_type(self, master_row):
        """
            演算子のデータリストのみを取り出す
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        return master_row['condition_type']

    def json_key_to_keyname_convart(self, column_value, search_candidates, master_row):
        """
            JSON形式で格納されているKey(DB)を名称リストに変換
            フィルタのプルダウン検索の表示する内容
            ARGS:
                column_value:  JSON形式で格納されている値
                               [{"label_name": uuid, "condition_type": uuid, "condition_value": 値] ... }
                search_candidates: 名称リスト
                master_row:    マスタテーブルデータ {key: value, ...}
            RETRUN:
                名称リスト
        """
        master_row = self.get_master_label_name(master_row)
        try:
            if not column_value:
                column_value = []
                column_value = json.dumps(column_value)
            column_value = json.loads(column_value)
            if len(column_value) > 0:
                for lable_row in column_value:
                    if len(lable_row) != 3:
                        raise Exception("JSON format is (abnormal json data:({}))".format(str(column_value)))
        except Exception as e:
            raise Exception(e)

        if isinstance(column_value, list):
            for lable_row in column_value:
                key = lable_row["label_name"]
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
                # tmp_where = " JSON_CONTAINS(`{col_name}`, {bindkey}, '$.id') ".format(
                tmp_where = " JSON_EXTRACT(`VARS_DESCRIPTION`, \"$[*].label_name\") like {bindkey} ".format(
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
            値を出力用の値へ変換 (DB->UI)
            DB: [{"label_name": "key01", "condition_type": "0", "condition_value": "True"}....]
            UI: [[key01に対応した名称, 0に対応した名称, "True"]....]
            ARGS:
                val:値
            RETRUN:
                retBool, msg, val
        """
        msg = ''

        master_row = self.search_id_data_list()
        label_name_row = self.get_master_label_name(master_row)
        condition_type_row = self.get_master_condition_type(master_row)

        try:
            if not val:
                val = []
                val = json.dumps(val)
            json_val = json.loads(val)
            # todo 通知先も同じように修正
            if type(json_val) is not list:
                exp_args = "Not in JSON list format data(%s)" % (str(val))
                raise Exception(exp_args)
        except Exception:
            # todo エラーコードを考える
            # JSONフォーマットが不正
            status_code = '499-01703'
            msg_args = []
            msg = g.appmsg.get_api_message(status_code, msg_args)
            raise Exception(status_code, msg)
            # todo 通知先も同じように修正
        search_candidates = []
        if isinstance(json_val, list):
            if len(json_val) > 0:
                for json_row in json_val:
                    output_label_name = "Not Found"
                    output_condition_type = "Not Found"
                    output_condition_value = "Not Found"
                    key = json_row["label_name"]
                    if key in label_name_row.keys():
                        output_label_name = label_name_row[key]
                    else:
                        # 廃止されているデータをID変換失敗(key)として扱う
                        output_label_name = g.appmsg.get_api_message('MSG-00001', [key])
                    key = json_row["condition_type"]
                    if key in condition_type_row.keys():
                        output_condition_type = condition_type_row[key]
                    else:
                        # 廃止されているデータをID変換失敗(key)として扱う
                        output_condition_type = g.appmsg.get_api_message('MSG-00001', [key])
                    output_condition_value = json_row["condition_value"]

                    output_line = [output_label_name, output_condition_type, output_condition_value]
                    search_candidates.append(output_line)

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
        retdict = []
        msg = ''
        try:
            if not valnames:
                return True, '', valnames,
            val_decode = self.is_json_format(valnames)
            if val_decode is False:
                raise Exception("JSON format is abnormal")
            if len(val_decode) == 0:
                return True, '', None,
        except Exception:
            retBool = False
            # todo エラーコード見直し
            status_code = '499-01703'
            msg_args = []
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return retBool, msg

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

        if valnames:
            try:
                val_decode = self.is_json_format(valnames)
                if val_decode is False:
                    raise Exception("JSON format is abnormal")

            except Exception:
                # dodo エラーコード見直し
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
                    # todo エラーコード見直し
                    retBool = False
                    status_code = '499-01703'
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
        """
            jsonフォーマットを確認
            ARGS:
                val: jsonフォーマット
                    [[ラベル, 演算子, 値]...]
            RETRUN:
                ( True / False , メッセージ )
        """
        try:
            val = json.loads(val)
            if type(val) is not list:
                raise Exception("JSON format is abnormal")
            else:
                if len(val) > 0:
                    for val_line in val:
                        if type(val) is not list:
                            raise Exception("JSON format is abnormal")
                        else:
                            if len(val_line) != 3:
                                raise Exception("JSON format is abnormal")
            return val
        except Exception:
            return False

    # DBに登録するデータをユニーク制約用にKey値でソートする
    def sort_for_unique_constraints(self, inlist):
        retlist = []
        sortlist = []
        size = len(inlist)
        line = 0
        for row in inlist:
            pattern = "{}_{}_{}_{:0" + str(size) + "}"
            key = pattern.format(row["label_name"],row["condition_type"],row["condition_value"],line)
            line += 1
            sortlist.append(key)
        sortlist.sort()
        for row in sortlist:
            line = row[-size:]
            retlist.append(inlist[int(line)])
        return retlist

