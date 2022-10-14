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

# import column_class
from .column_class import Column


class IDColumn(Column):
    """
    カラムクラス個別処理(IDColumn)
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

        self.id_data_list = {}

        self.data_list_set_flg = False
        
    def get_id_data_list(self):
        """
            データリストを取得する
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        
        if self.data_list_set_flg:
            return self.id_data_list
        else:
            id_data_list = self.search_id_data_list()
            self.set_id_data_list(id_data_list)
            return id_data_list

    def set_id_data_list(self, id_data_list):
        """
            データリストを設定する
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        self.id_data_list = id_data_list

    def search_id_data_list(self):
        """
            データリストを検索する
            ARGS:
                なし
            RETRUN:
                データリスト
        """
        values = {}
        language = g.LANGUAGE.upper()
        ref_malti_lang = self.get_objcol().get("REF_MULTI_LANG")
        ref_pkey_name = self.get_objcol().get("REF_PKEY_NAME")
        ref_table_name = self.get_objcol().get("REF_TABLE_NAME")
        where_str = "WHERE `DISUSE_FLAG` = '0' "
        bind_value_list = []

        # 連携先のテーブルが言語別のカラムを持つか判定
        if ref_malti_lang == '1':
            ref_col_name = "{}_{}".format(self.get_objcol().get("REF_COL_NAME"), language)
        else:
            ref_col_name = "{}".format(self.get_objcol().get("REF_COL_NAME"))

        # 検索
        return_values = self.objdbca.table_select(ref_table_name, where_str, bind_value_list)

        for record in return_values:
            values[record[ref_pkey_name]] = record[ref_col_name]
        
        # 自テーブル名と参照先テーブル名が同一の場合、data_list_set_flgをFalseに設定する
        if self.table_name == ref_table_name:
            self.data_list_set_flg = False
        else:
            self.data_list_set_flg = True

        return values

    def get_values_by_key(self, where_equal=[]):
        """
            Keyを検索条件に値を取得する
            ARGS:
                where_equal:一致検索のリスト
            RETRUN:
                values:検索結果
        """

        values = {}

        # データリストを取得
        id_data_list = self.get_id_data_list()

        # 一致検索
        if len(where_equal) > 0:
            for where_value in where_equal:
                if where_value in id_data_list:
                    values[where_value] = id_data_list[where_value]
        else:
            for key, value in id_data_list.items():
                values[key] = value

        return values

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
        id_data_list = self.get_id_data_list()

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

        return_values = self.get_values_by_value([val])
        
        # 返却値が存在するか確認
        if len(return_values) == 0:
            retBool = False
            status_code = 'MSG-00032'
            msg_args = [val]
            msg = g.appmsg.get_api_message(status_code, msg_args)
            return retBool, msg
        
        return retBool,

    # [load_table] 値を入力用の値へ変換
    def convert_value_input(self, val=''):
        """
            値を入力用の値へ変換
            ARGS:
                val:値
            RETRUN:
                retBool, msg, val
        """
        retBool = True
        msg = ''
        if val is not None:

            return_values = self.get_values_by_value([val])

            if len(return_values) == 1:
                val = list(return_values.keys())[0]
            else:
                retBool = False
                status_code = 'MSG-00032'
                msg_args = [val]
                msg = g.appmsg.get_api_message(status_code, msg_args)

        return retBool, msg, val,

    # [load_table] 値を出力用の値へ変換
    def convert_value_output(self, val=''):
        """
            値を出力用の値へ変換
            ARGS:
                val:値
            RETRUN:
                retBool, msg, val
        """

        retBool = True
        msg = ''
        
        if val is not None:

            return_values = self.get_values_by_key([val])

            if len(return_values) == 1:
                val = return_values[val]
            else:
                status_code = 'MSG-00001'
                msg_args = [val]
                val = g.appmsg.get_api_message(status_code, msg_args)
                
        return retBool, msg, val,

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
        conjunction = ''
        save_type = self.get_save_type()

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
            if save_type == 'JSON':
                for bindvalue in tmp_conf:

                    if len(str_where) != 0:
                        conjunction = 'or'
                    str_where = str_where + ' ' + conjunction + ' JSON_CONTAINS(`{}`, \'"{}"\', "$.{}")'.format(
                        self.get_col_name(),
                        bindvalue,
                        self.get_rest_key_name()
                    )
                if len(str_where) != 0:
                    str_where = '(' + str_where + ')'
            else:
                for bindvalue in tmp_conf:

                    bindkey = "__{}__{}__".format(self.get_col_name(), listno)
                    bindkeys.append(bindkey)
                    bindvalues.setdefault(bindkey, bindvalue)
                    listno += 1

                bindkey = "{}".format(",".join(map(str, bindkeys)))
                str_where = " `{col_name}` IN ( {bindkey} ) ".format(
                    col_name=self.get_col_name(),
                    bindkey=bindkey
                )

        result.setdefault("bindkey", bindkeys)
        result.setdefault("bindvalue", bindvalues)
        result.setdefault("where", str_where)

        return result
