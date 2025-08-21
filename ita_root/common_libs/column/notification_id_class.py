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

# import column_class
from .multi_select_id_class import MultiSelectIDColumn  # noqa: F401
from common_libs.notification.notification_base import Notification


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
        values = Notification.fetch_notification_destination_dict()
        # values["1"] = "default"

        self.data_list_set_flg = True

        return values

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
            print_exception_msg(e)
            status_code = '499-01708'
            msg_args = [str(val)]
            msg = g.appmsg.get_api_message(status_code, msg_args)
            raise Exception(status_code, msg)

        master_row = self.get_values_by_key(json_val["id"])

        search_candidates = []
        if isinstance(json_val["id"], list):
            keys = json_val["id"]
            for key in keys:
                if key in master_row.keys():
                    val = master_row[key]
                    if not search_candidates.count(val):
                        search_candidates.append(val)
                else:
                    if key == "1":
                    # OASE管理->通知テンプレート(共通)の、デフォルトレコード用
                        search_candidates.append("default")
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
        if not valnames:
            return True, '', valnames,
        val_decode = self.is_json_format(valnames)
        if val_decode is False:
            return False, 'JSON format is abnormal', valnames,
        if len(val_decode) == 0:
            return True, '', None,

        if val_decode is not None:
            for val in val_decode:
                return_values = self.get_values_by_value([val]) if val != "default" else {"1": "default"}

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
            val_decode = self.is_json_format(valnames)
            if val_decode is False:
                print_exception_msg("JSON format is abnormal")
                retBool = False
                status_code = '499-01701'
                msg_args = []
                msg = g.appmsg.get_api_message(status_code, msg_args)
                return retBool, msg

            set_Valses = []
            if len(val_decode) > 0:
                for val in val_decode:
                    return_values = self.get_values_by_value([val]) if val != "default" else {"1": "default"}
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
