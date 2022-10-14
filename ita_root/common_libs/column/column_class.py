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
import importlib


"""
カラムクラス共通処理(カラム)
"""


class Column():
    """
    カラムクラス共通処理(カラム)

        以下のデータ群持っている前提、キー等は変更の可能性あり
            メニュー-テーブル紐付管理
            組み合わせ一意管理
            メニュー-カラム紐付管理

        def set_XXXXX(self) : selfの設定用
        def get_XXXXX(self) : selfの取得用

        maintenance関連
            before_iud_action   :レコード操作前の処理（バリデーション、カラムの個別処理）
                以下を呼び出し
                    before_iud_validate_check   ：カラムクラスのバリデーション
                    before_iud_col_action  ：カラムの個別処理

            after_iud_action    :レコード操作後の処理（バリデーション、個別処理）
                以下を呼び出し
                    after_iud_common_action :カラムクラスの処理
                    after_iud_col_action   :カラムの個別処理

            カラムクラス毎に行うバリデーション処理（クラスの継承でオーバライドさせる）
            check_basic_valid   ：カラムクラスのバリデーション処理

            e.g.作成するカラムクラスのバリデーション、個別処理に関して
            class カラムクラス名(継承元クラス):
                def __init__(self,objtable,col_name):

                # カラムクラス毎のバリデーション処理
                def check_basic_valid(self,val):
                # カラムの個別処理
                def before_iud_col_action(self,val=''):
                def after_iud_col_action(self,val=''):


        filter関連
            # where句の中身を返却 条件文,bind情報
            get_filter_query

        load_table.py関連
            # ID相互変換用のデータ生成
            get_convert_list
            # 内部処理用の値へ変換
            convert_value_input
            #  出力用の値へ変換
            convert_value_output

    """

    # バリデーション閾値キー
    base_valid_list = {
        "min_length": None,  # 最大バイト数
        "max_length": None,  # 最大バイト数
        "int_max": None,  # 最大値(整数)
        "int_min": None,  # 最小値(整数)
        "float_max": None,  # 最大値(小数)
        "float_min": None,  # 最大値(小数)
        "float_digit": None,  # 桁数(小数)
        "upload_max_size": None,  # ファイル最大バイト数
    }

    def __init__(self, objdbca, objtable, rest_key_name, cmd_type=''):
        # カラムクラス名
        self.class_name = self.__class__.__name__
        # バリデーション閾値
        self.dict_valid = {}
        # テーブル情報
        self.objtable = {}
        # テーブル名
        self.table_name = ''
        # カラム名
        self.col_name = ''
        # rest用項目名
        self.rest_key_name = ''

        self.db_qm = "'"

        self.objdbca = objdbca
        
        self.cmd_type = cmd_type

        # デフォルト処理名
        self.encrypt_name = 'ky_encrypt'
        self.decrypt_name = 'ky_decrypt'

    # self 設定、取得関連
    def set_objtable(self, objtable):
        """
            テーブルデータを設定
            ARGS:
                objtable
        """
        self.objtable = objtable

    def get_objtable(self):
        """
            テーブルデータを取得
            RETRUN:
                self.objtable
        """
        return self.objtable

    # column_listの設定,取得
    def set_column_list(self, column_list):
        """
            column_listの設定
            ARGS:
                column_list
        """
        self.column_list = column_list

    def get_column_list(self):
        """
            column_listの取得
            RETUEN:
                self.column_list
        """
        return self.column_list

    # primary_keyの設定,取得
    def set_primary_key(self, primary_key):
        """
            column_listの設定
            ARGS:
                primary_key
        """
        self.primary_key = primary_key

    def get_primary_key(self):
        """
            primary_keyの取得
            RETUEN:
                self.primary_key
        """
        return self.primary_key
    
    def get_menu(self):
        """
            menuを取得
            RETRUN:
                string
        """
        menu_id = self.get_objtable().get('MENUINFO').get('MENU_ID')
        return menu_id

    def get_sheet_type(self):
        """
            シートタイプを取得
            RETRUN:
                {} or [] ?
        """
        try:
            result = self.get_objtable().get('MENUINFO').get('SHEET_TYPE')
        except Exception:
            result = 0
        return result

    def set_encrypt_name(self, encrypt_name):
        """
            encrypt_nameを設定
            ARGS:
                table_name
        """
        self.encrypt_name = encrypt_name

    def get_encrypt_name(self):
        """
            encrypt_nameを取得
            RETRUN:
                self.encrypt_name
        """
        return self.encrypt_name

    def set_decrypt_name(self, decrypt_name):
        """
            decrypt_nameを設定
            ARGS:
                table_name
        """
        self.decrypt_name = decrypt_name

    def get_decrypt_name(self):
        """
            decrypt_nameを取得
            RETRUN:
                self.decrypt_name
        """
        return self.decrypt_name

    def set_table_name(self, table_name):
        """
            テーブル名を設定
            ARGS:
                table_name
        """
        self.table_name = table_name

    def get_table_name(self):
        """
            テーブル名を取得
            RETRUN:
                self.table_name
        """
        return self.table_name

    def set_col_name(self, col_name):
        """
            カラム名を設定
            ARGS:
                col_name
        """
        self.col_name = col_name

    def get_col_name(self):
        """
            カラム名を取得
            RETRUN:
                self.col_name
        """
        return self.col_name

    def set_rest_key_name(self, rest_key_name):
        """
            REST用項目名を設定
            ARGS:
                rest_key_name
        """
        self.rest_key_name = rest_key_name

    def get_rest_key_name(self):
        """
            REST用項目名を取得
            RETRUN:
                self.rest_key_name
        """
        return self.rest_key_name

    def get_objcols(self):
        """
            全カラム設定を取得
            RETRUN:
                {}
        """
        return self.objtable.get('COLINFO')

    def get_objcol(self):
        """
            単一カラム設定を取得
            RETRUN:
                {}
        """
        return self.get_objcols().get(self.get_rest_key_name())

    def set_cmd_type(self, cmd_type):
        """
            cmd_typeを設定
            ARGS:
                cmd_type
        """
        self.cmd_type = cmd_type
        
    def get_save_type(self):
        """
            単一カラムのsave_typeを取得
            RETRUN:
                {}
        """
        return self.get_objcol().get('SAVE_TYPE')

    def get_label(self):
        """
            項目名を取得
            RETRUN:
                {COLUMN_NAME_JA:XXXX,COLUMN_NAME_EN:XXXX,COLUMN_NAME_REST:XXXX}
        """
        tmpcols = self.get_objcol()
        ret_dict = {
            'COLUMN_NAME_JA': tmpcols.get('COLUMN_NAME_JA'),
            'COLUMN_NAME_EN': tmpcols.get('COLUMN_NAME_EN'),
            'COLUMN_NAME_REST': tmpcols.get('COLUMN_NAME_REST')
        }

        return ret_dict

    def get_dict_valid(self):
        """
            単一カラムバリデーション設定取得
            RETRUN:
                {}
        """
        # result = json.loads(self.get_objcol().get('VALIDATE_OPTION'))
        validate_option = {}
        tmp_validate_option = self.get_objcol().get('VALIDATE_OPTION')
        if tmp_validate_option is not None:
            try:
                if isinstance(tmp_validate_option, dict) is False:
                    validate_option = json.loads(tmp_validate_option)
                else:
                    validate_option = tmp_validate_option
            except json.JSONDecodeError:
                validate_option = {}

        return validate_option

    def get_call_before_valid_info(self):
        """
            バリデーション個別処理設定取得(レコード操作前)
            RETRUN:
                {}
        """
        return self.get_objcol().get('BEFORE_VALIDATE_REGISTER')

    def get_call_after_valid_info(self):
        """
            バリデーション個別処理設定取得(レコード操作後)
            RETRUN:
                {}
        """
        return self.get_objcol().get('AFTER_VALIDATE_REGISTER')

    def get_base_valid_list(self):
        """
            単一カラムバリデーション設定取得
            RETRUN:
                self.base_valid_list
        """
        return self.base_valid_list

    def get_required(self):
        """
            カラム名を設定
            RETRUN:
                0 / 1
        """
        return self.get_objcol().get('REQUIRED_ITEM')

    def get_uniqued(self):
        """
            カラム名を設定
            RETRUN:
                0 / 1
        """
        return self.get_objcol().get('UNIQUE_ITEM')

    def get_reg_exp(self):
        """
            正規表現を設定
            RETRUN:
                reg_exp
        """
        return self.get_objcol().get('VALIDATE_REG_EXP')

    def set_valid_value(self):
        """
            バリデーション閾値の設定（テンプレートのキー以外除外）
            RETRUN:
                {}
        """
        tmp_valid_val = {}
        if len(self.get_dict_valid()) != 0:
            # バリデーション閾値のキー取得
            tmp_valid_val = self.get_base_valid_list().copy()
            for valid_key in list(tmp_valid_val.keys()):
                # バリデーション閾値の値を書き込み
                if valid_key in self.get_dict_valid():
                    tmp_valid_val[valid_key] = self.get_dict_valid().get(valid_key)
                else:
                    # 対象外のキーを除外
                    del tmp_valid_val[valid_key]

        self.dict_valid = tmp_valid_val

    def get_cmd_type(self):
        """
            実行種別を取得
            RETRUN:
                self.cmd_type
        """
        return self.cmd_type

    def get_file_upload_place(self):
        """
            file_upload_placeを取得
            RETRUN:
                string / None
        """
        return self.get_objcol().get('FILE_UPLOAD_PLACE')

    ###
    # [maintenance] レコード操作前処理実施
    def before_iud_action(self, val='', option={}):
        """
            レコード操作前処理 (共通バリデーション + 個別処理 )
            ARGS:
                val:値
            RETRUN:
                ( True / False , メッセージ, val , option )
        """
        retBool = True
        msg = ''
        # 標準バリデーションレコード操作前
        result_1 = self.before_iud_validate_check(val, option)
        if result_1[0] is not True:
            return result_1

        # 個別処理レコード操作前
        result_2 = self.before_iud_col_action(option)
        if result_2[0] is not True:
            return result_2
        else:
            retBool = result_2[0]
            msg = result_2[1]
            option = result_2[2]

        return retBool, msg, val, option

    # [maintenance] レコード操作後処理実施
    def after_iud_action(self, val='', option={}):
        """
            共通処理 + 個別処理 レコード操作後
            ARGS:
                val:値
            RETRUN:
                ( True / False , メッセージ, val , option )
        """
        retBool = True
        msg = ''
        # 標準処理レコード操作後
        result_1 = self.after_iud_common_action(val, option)
        if result_1[0] is not True:
            return result_1

        # 個別処理レコード操作後
        result_2 = self.after_iud_col_action(val, option)
        if result_2[0] is not True:
            return result_2
        else:
            retBool = result_2[0]
            msg = result_2[1]
            option = result_2[2]
        return retBool, msg, val, option

    # [maintenance] 共通バリデーション レコード操作前
    def before_iud_validate_check(self, val='', option={}):
        """
            共通バリデーション レコード操作前
            ARGS:
                val:値
            RETRUN:
                ( True / False , メッセージ )
        """
        retBool = True

        cmd_type = self.get_cmd_type()

        if cmd_type != "Discard":
            # バリデーション必須
            result_1 = self.is_valid_required(val, option)
            if result_1[0] is not True:
                return result_1

            # バリデーション一意 DBアクセス
            result_2 = self.get_uniqued()
            if result_2 == '1':
                result_2 = self.is_valid_unique(val, option)
                if result_2[0] is not True:
                    return result_2

            # カラムクラス毎のバリデーション
            result_3 = self.is_valid(val, option)
            if result_3[0] is not True:
                return result_3

        return retBool,

    # [maintenance] カラム個別処理 レコード操作前
    def before_iud_col_action(self, option={}):
        """
            カラム個別処理  レコード操作前
            ARGS:
                val:値
                option:個別バリデーション,個別処理
            RETRUN:
                ( retBool, msg, option )
        """
        retBool = True
        msg = ''
        exec_config = self.get_call_before_valid_info()
        if exec_config is not None:
            if str(self.get_sheet_type()) in ["1", "2", "3", "4"]:
                # メニュー作成機能で作成したメニュー用のファイルを指定
                external_validate_path = 'common_libs.validate.valid_cmdb_menu'
            else:
                external_validate_path = 'common_libs.validate.valid_{}'.format(self.get_menu())
            exec_func = importlib.import_module(external_validate_path)
            eval_str = 'exec_func.{}(self.objdbca, self.objtable, option)'.format(exec_config)
            tmp_exec = eval(eval_str)
            if tmp_exec[0] is not True:
                retBool = False
                msg = tmp_exec[1]
            else:
                option = tmp_exec[2]
        return retBool, msg, option,

    # [maintenance] カラムクラスの個別処理 レコード操作後
    def after_iud_common_action(self, val='', option={}):
        """
            カラムクラス毎の個別処理 レコード操作後
            ARGS:
                val:値
                option:オプション
            RETRUN:
                retBool, msg, parameter, option
        """
        retBool = True
        msg = ''
        # カラムクラス毎の個別処理

        return retBool, msg,

    # [maintenance] カラム個別処理 レコード操作後
    def after_iud_col_action(self, val='', option={}):
        """
            カラム個別処理  レコード操作後
            ARGS:
                val:値
                option:個別処理
            RETRUN:
                retBool, msg, val, parameter, option,
        """
        retBool = True
        msg = ''
        exec_config = self.get_call_after_valid_info()
        if exec_config is not None:
            if str(self.get_sheet_type()) in ["1", "2", "3", "4"]:
                # メニュー作成機能で作成したメニュー用のファイルを指定
                external_validate_path = 'common_libs.validate.valid_cmdb_menu'
            else:
                external_validate_path = 'common_libs.validate.valid_{}'.format(self.get_menu())
            exec_func = importlib.import_module(external_validate_path)  # noqa: F841
            eval_str = 'exec_func.{}(self.objdbca, self.objtable, option)'.format(exec_config)
            tmp_exec = eval(eval_str)
            if tmp_exec[0] is not True:
                retBool = False
                msg = tmp_exec[1]
            else:
                option = tmp_exec[2]
                    
        return retBool, msg, option,
    
    # [maintenance] カラム個別処理 レコード操作後の状態回復処理
    def after_iud_restore_action(self, val="", option={}):
        """
            カラムクラス毎の個別処理 レコード操作後の状態回復処理
            ARGS:
                option:オプション
            RETRUN:
                True / エラーメッセージ
        """
        retBool = True
        msg = ''
        return retBool, msg,
        
    # [maintenance] 共通バリデーション呼び出し
    def is_valid(self, val, option={}):
        """
            バリデーション実施
            ARGS:
                val:値
            RETRUN:
                ( True / False , メッセージ )
        """

        # カラムクラス毎のバリデーション処理の呼び出し

        # バリデーション閾値の設定（テンプレートのキー以外除外）
        self.set_valid_value()
        # バリデーション閾値の設定（テンプレートのキー以外除外）
        self.set_valid_value()
        if val is not None:
            result = self.check_basic_valid(val, option)
        else:
            result = True, ''
        return result

    # [maintenance] 一意バリデーション呼び出し
    def is_valid_unique(self, val='', option={}):
        """
            一意バリデーション実施
            ARGS:
                col_name:カラム名
                val:値
            RETRUN:
                ( True / False , メッセージ )
        """
        ###
        # DBアクセス一意処理を追加
        ###
        retBool = True
        msg = ''
        column_list, primary_key_list = self.objdbca.table_columns_get(self.get_table_name())
        if self.col_name not in primary_key_list:
            if self.col_name == "DATA_JSON":
                # カラム名がDATA_JSON(メニュー作成機能により作られたメニューのカラム)の場合
                where_str = " where DISUSE_FLAG = 0"
                bind_value_list = []
                if 'uuid' in option:
                    if option.get('uuid') is not None:
                        where_str = where_str + " and `{}` <> %s ".format(primary_key_list[0])
                        bind_value_list.append(option.get('uuid'))
                
                result = self.objdbca.table_select(self.table_name, where_str, bind_value_list)
                if result:
                    tmp_uuids = []
                    for tmp_rows in result:
                        data_json = tmp_rows.get("DATA_JSON")
                        if data_json:
                            json_rows = json.loads(data_json)
                            for jsonkey, jsonval in json_rows.items():
                                if jsonkey == self.rest_key_name:
                                    if jsonval == val:
                                        tmp_uuids.append(tmp_rows.get(primary_key_list[0]))
                                        retBool = False
                    
                    if not retBool:
                        status_code = 'MSG-00025'
                        str_uuids = ', '.join(map(str, tmp_uuids))
                        msg_args = [str_uuids, val]
                        msg = g.appmsg.get_api_message(status_code, msg_args)
                        return retBool, msg
                        
            else:
                # 通常のカラムの場合
                where_str = " WHERE `DISUSE_FLAG` = 0 AND `{}` = %s ".format(self.col_name)
                bind_value_list = [val]
                
                if 'uuid' in option:
                    if option.get('uuid') is not None:
                        where_str = where_str + " and `{}` <> %s ".format(primary_key_list[0])
                        bind_value_list.append(option.get('uuid'))
                
                result = self.objdbca.table_select(self.table_name, where_str, bind_value_list)
                tmp_uuids = []
                if len(result) != 0:
                    for tmp_rows in result:
                        tmp_uuids.append(tmp_rows.get(primary_key_list[0]))
                    retBool = False
                    status_code = 'MSG-00025'
                    str_uuids = ', '.join(map(str, tmp_uuids))
                    msg_args = [str_uuids, val]
                    msg = g.appmsg.get_api_message(status_code, msg_args)
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
            elif len(str(val)) == 0:
                retBool = False
                status_code = 'MSG-00030'
                msg_args = []
                msg = g.appmsg.get_api_message(status_code, msg_args)
                    
        return retBool, msg,

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
        return retBool, msg, val

    # [load_table] ファイル[base64 string]を取得
    def get_file_data(self, file_name, target_uuid, target_uuid_jnl=''):
        """
            ファイル(base64)を取得
            ARGS:
                file_name:ファイル名
                target_uuid:uuid
                target_uuid_jnl:uuid
            RETRUN:
                base64 string
        """
        result = '{} base64 string :{}_{}'.format(file_name, target_uuid, target_uuid_jnl)
        return result
    
    # [load_table][filter] ID変換用のリスト取得
    def get_convert_list(self):
        """
            ID相互変換用のリスト取得
            ARGS:

            RETRUN:
                {"ID":{"uuid":"value"},"VALUE":{"value":"uuid"}
        """
        result = {
            "ID": None,
            "VALUE": None
        }
        # DB接続 連携先のテーブル情報から
        ####
        ####
        return result

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
        save_type = self.get_save_type()
        if search_mode == "LIST":
            tmp_conf = search_conf
            listno = 0
            bindkeys = []
            bindvalues = {}
            str_where = ''
            conjunction = ''
            if save_type == 'JSON':
                for bindvalue in tmp_conf:
                    tmp_result = self.convert_value_input(bindvalue)
                    if tmp_result[0] is True:
                        bindvalue = tmp_result[2]
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
                    tmp_result = self.convert_value_input(bindvalue)
                    if tmp_result[0] is True:
                        bindvalue = tmp_result[2]

                    bindkey = "__{}__{}__".format(self.get_col_name(), listno)
                    bindkeys.append(bindkey)
                    bindvalues.setdefault(bindkey, bindvalue)
                    listno = listno + 1

                bindkey = "{}".format(",".join(map(str, bindkeys)))
                str_where = " `{col_name}` IN ( {bindkey} ) ".format(
                    col_name=self.get_col_name(),
                    bindkey=bindkey
                )
            result.setdefault("bindkey", bindkeys)
            result.setdefault("bindvalue", bindvalues)
            result.setdefault("where", str_where)

        elif search_mode == "NORMAL":            # bindvalue = search_conf.get(search_mode)
            bindvalue = search_conf
            tmp_result = self.convert_value_input(bindvalue)
            if tmp_result[0] is True:
                bindvalue = tmp_result[2]
            if save_type == 'JSON':
                bindkey = "__{}__".format(self.get_col_name())
                str_where = ' JSON_UNQUOTE(JSON_EXTRACT(`{}`,"$.{}")) LIKE  {} '.format(self.get_col_name(), self.get_rest_key_name(), bindkey)
            else:
                bindkey = "__{}__".format(self.get_col_name())
                str_where = " `{col_name}` LIKE {bindkey} ".format(
                    col_name=self.get_col_name(),
                    bindkey=bindkey,
                )
            result.setdefault("bindkey", bindkey)
            result.setdefault("bindvalue", {bindkey: "%{}%".format(bindvalue)})
            result.setdefault("where", str_where)

        elif search_mode == "RANGE":
            tmp_conf = search_conf
            bindkeys = []
            bindvalues = {}
            if save_type == 'JSON':
                start_val = tmp_conf.get('START')
                end_val = tmp_conf.get('END')
                bindkey_s = "__{}_S__".format(self.get_col_name())
                bindkey_e = "__{}_E__".format(self.get_col_name())
                str_where_s = ''
                str_where_e = ''
                if start_val is not None:
                    str_where_s = ' JSON_UNQUOTE(JSON_EXTRACT(`{}`,"$.{}")) >=  {} '.format(self.get_col_name(), self.get_rest_key_name(), bindkey_s)
                if end_val is not None:
                    str_where_e = ' JSON_UNQUOTE(JSON_EXTRACT(`{}`,"$.{}")) <=  {} '.format(self.get_col_name(), self.get_rest_key_name(), bindkey_e)
                if len(str_where_e) != 0 and len(str_where_e) != 0:
                    conjunction = 'and'
                else:
                    conjunction = ''
                str_where = '(' + str_where_s + conjunction + str_where_e + ')'
                bindkeys.append(bindkey_s)
                bindkeys.append(bindkey_e)
                bindvalues.setdefault(bindkey_s, start_val)
                bindvalues.setdefault(bindkey_e, end_val)
            else:
                start_val = tmp_conf.get('START')
                end_val = tmp_conf.get('END')
                if start_val is None:
                    start_val = ''
                if end_val is None:
                    end_val = ''
                bindkey_s = "__{}_S__".format(self.get_col_name())
                bindkey_e = "__{}_E__".format(self.get_col_name())
                if start_val is not None and end_val is not None:
                    if len(str(start_val)) > 0 and len(str(end_val)) > 0:
                        str_where = " `{col_name}` >= {bindkey_s} and `{col_name}` <= {bindkey_e} ".format(
                            col_name=self.get_col_name(),
                            bindkey_s=bindkey_s,
                            bindkey_e=bindkey_e,
                        )
                        bindkeys.append(bindkey_s)
                        bindkeys.append(bindkey_e)
                        bindvalues.setdefault(bindkey_s, start_val)
                        bindvalues.setdefault(bindkey_e, end_val)

                    elif len(str(start_val)) > 0 and len(str(end_val)) == 0:
                        str_where = " `{col_name}` >= {bindkey_s} ".format(
                            col_name=self.get_col_name(),
                            bindkey_s=bindkey_s,
                        )
                        bindkeys.append(bindkey_s)
                        bindvalues.setdefault(bindkey_s, start_val)

                    elif len(str(end_val)) > 0 and len(str(start_val)) == 0:
                        str_where = " `{col_name}` <= {bindkey_e} ".format(
                            col_name=self.get_col_name(),
                            bindkey_e=bindkey_e,
                        )
                        bindkeys.append(bindkey_e)
                        bindvalues.setdefault(bindkey_e, end_val)

            result.setdefault("bindkey", bindkeys)
            result.setdefault("bindvalue", bindvalues)
            result.setdefault("where", str_where)
        else:
            result.setdefault("bindkey", None)
            result.setdefault("bindvalue", None)
            result.setdefault("where", None)

        return result

    # バリデーション処理(カラムクラス毎) (バリデーションクラスで上書き)
    def check_basic_valid(self, val, option={}):
        """
            共通バリデーション処理実行(バリデーションクラスで上書き)
            ARGS:
                val:値
            RETRUN:
                ( True / False , メッセージ )
        """
        return True,
