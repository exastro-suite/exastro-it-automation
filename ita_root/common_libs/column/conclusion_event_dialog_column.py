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


class ConclusionEventSettingColumn(IndividualDialogColumn):
    """
    結論イベント設定ダイアログ
    """
    def __init__(self, objdbca, objtable, rest_key_name, cmd_type):
        super().__init__(objdbca, objtable, rest_key_name, cmd_type)

        ## 個別コンスタント値定義
        self.json_tag = ["label_key", "label_value"]
        self.idx_label = 0
        self.tag_label = self.json_tag[self.idx_label]
        self.idx_value = 1
        self.tag_value = self.json_tag[self.idx_value]

    def search_id_data_list(self):
        """
            ラベル名子のデータリストを検索する
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        values = {}
        values = super().search_id_data_list()
        return values

    def get_input_values_by_value(self, val):
        """
            UIで設定された結論イベントのJSON値をマスタデータと付け合わせ
            キー値に変換する。
            ARGS:
                val: ["ラベル名", "値"]
            RETRUN:
                { "label_key": "ラベル名 uuid", "label_value": 値 }
        """

        result_value = {}

        # データリストを取得
        label_name_row = self.search_id_data_list()

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
        result_value["label_key"] = name_key

        if not val[1]:
            status_code = '499-01707'
            msg_args = []
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return False, msg, result_value
        if type(val[1]) is not str:
            status_code = 'MSG-00032'
            msg_args = [str(val[1])] # true/false/数値対策
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return False, msg, result_value
        result_value["label_value"] = val[1]

        return True, None, result_value

    # [load_table] 値を出力用の値へ変換
    def convert_value_output(self, val=''):
        """
            値を出力用の値へ変換 (DB->UI)
            DB: [{"label_key": "key01", "label_value": "True"}....]
            UI: [[key01に対応した名称, 0に対応した名称, "True"]....]
            ARGS:
                val:値
            RETRUN:
                retBool, msg, val
        """
        msg = ''

        master_row = self.search_id_data_list()

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
            # todo
            # JSONフォーマットが不正
            status_code = '499-01703'
            msg_args = []
            msg = g.appmsg.get_api_message(status_code, msg_args)
            raise Exception(status_code, msg)
        search_candidates = []
        if isinstance(json_val, list):
            if len(json_val) > 0:
                for json_row in json_val:
                    output_label_name = "Not Found"
                    output_condition_value = "Not Found"
                    key = json_row["label_key"]
                    if key in master_row.keys():
                        output_label_name = master_row[key]
                    else:
                        # 廃止されているデータをID変換失敗(key)として扱う
                        output_label_name = g.appmsg.get_api_message('MSG-00001', [key])
                    output_condition_value = json_row["label_value"]

                    output_line = [output_label_name, output_condition_value]
                    search_candidates.append(output_line)

        # 全角文字対応　ensure_ascii=False
        return True, msg, json.dumps(search_candidates, ensure_ascii=False),
