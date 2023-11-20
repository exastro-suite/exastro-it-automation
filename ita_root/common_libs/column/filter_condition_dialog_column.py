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
    def __init__(self, objdbca, objtable, rest_key_name, cmd_type):
        super().__init__(objdbca, objtable, rest_key_name, cmd_type)

        ## 個別コンスタント値定義
        self.json_tag = ["label_name","condition_type","condition_value"]
        self.idx_label = 0
        self.tag_label = self.json_tag[self.idx_label]
        self.idx_condition = 1
        self.tag_condition = self.json_tag[self.idx_condition]
        self.idx_value = 2
        self.tag_value = self.json_tag[self.idx_value]


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

    # [load_table] 値を出力用の値へ変換
    def convert_value_output(self, val=''):
        """
            値を出力用の値へ変換 (DB->UI)
            DB: [{"label_name": "key01", "condition_type": "0", "condition_value": "True"}....]
            UI: [[key01に対応した名称, "True"]....]
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
            if type(json_val) is not list:
                exp_args = "Not in JSON list format data(%s)" % (str(val))
                raise Exception(exp_args)
        except Exception as e:
            # エラーでリターンの処理がないのでException
            status_code = '499-01708'
            msg_args = [str(val)]
            msg = g.appmsg.get_api_message(status_code, msg_args)
            raise Exception(status_code, msg)

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
