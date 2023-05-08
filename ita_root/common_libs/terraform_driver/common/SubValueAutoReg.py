# Copyright 2023 NEC Corporation#
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
# import os
# import inspect
# import hashlib
import json
from flask import g
from common_libs.common import *  # noqa F403
from common_libs.loadtable import *  # noqa F403
from common_libs.common.exception import *  # noqa F403


class SubValueAutoReg():
    """
    代入値自動登録設定とパラメータシートから、代入値管理にレコードを反映させるClass
    """
    def __init__(self, ws_db=None, TFConst=None, operation_id=None, movement_id=None, execution_no=None):

        """
        処理内容
            コンストラクタ
        パラメータ
            ws_db: WorkspaceDBインスタンス
            TFConset: 定数クラス
            operation_id: オペレーションID
            movement_id: MovementID
            execution_id: 作業実行ID
        戻り値
            なし
        """
        self.TFConst = TFConst
        self.ws_db = ws_db
        self.if_null_data_handling_flg = 0
        self.operation_id = operation_id
        self.movement_id = movement_id
        self.execution_no = execution_no

    def set_assigned_value_from_parameter_sheet(self):
        """
        代入値自動登録設定とパラメータシートから、代入値管理にレコードを反映させる
        """
        # 返却値定義
        result = True
        msg = ''

        try:
            # インターフェース情報からNULLデータを代入値管理に登録するかどうかのデフォルト値selfにセットする
            result, msg = self.set_if_null_data_handling_flag()
            if not result:
                # 想定外エラーのためraise
                raise Exception(msg)

            # 代入値自動登録設定のレコードから、代入値管理に登録するレコードのデータを生成する
            result, msg, var_assign_data_list = self.create_val_assign_data()
            if not result:
                # 想定外エラーのためraise
                raise Exception(msg)

            # トランザクション開始
            self.ws_db.db_transaction_start()

            # 代入値管理テーブルにレコードを登録する
            for insert_data in var_assign_data_list:
                primary_key_name = 'ASSIGN_ID'
                ret = self.ws_db.table_insert(self.TFConst.T_VALUE, insert_data, primary_key_name)
                if not ret:
                    # 代入値管理テーブルへのレコード登録に失敗
                    log_msg = g.appmsg.get_log_message("MSG-81002", [])
                    g.applogger.error(log_msg)
                    msg = g.appmsg.get_api_message("MSG-81002", [])
                    result = False
                    break

            # トランザクション終了
            self.ws_db.db_transaction_end(True)

        except Exception as e:
            g.applogger.error(str(e))
            result = False
            msg = e

            # トランザクション終了(異常)
            self.ws_db.db_transaction_end(False)

        return result, msg

    def create_val_assign_data(self):
        """
        代入値自動登録設定のレコードから、代入値管理に登録するレコードのデータを生成する
        """
        # 返却値定義
        result = True
        msg = ''
        var_assign_data_list = []

        try:
            # Movement-変数紐付から対象のMovementのレコードを取得
            where_str = 'WHERE MOVEMENT_ID = %s AND DISUSE_FLAG = %s'
            t_movement_var_records = self.ws_db.table_select(self.TFConst.T_MOVEMENT_VAR, where_str, [self.movement_id, 0])

            # 「MVMT_VAR_LINK_ID」をkeyにしたdictに変換
            dict_movement_var_records = {}
            for record in t_movement_var_records:
                dict_movement_var_records[record.get('MVMT_VAR_LINK_ID')] = record

            # Movement-メンバー変数紐付から対象のMovementのレコードを取得
            where_str = 'WHERE MOVEMENT_ID = %s AND DISUSE_FLAG = %s'
            t_movement_var_member_records = self.ws_db.table_select(self.TFConst.T_MOVEMENT_VAR_MEMBER, where_str, [self.movement_id, 0])

            # 「MVMT_VAR_MEMBER_LINK_ID」をkeyにしたdictに変換
            dict_movement_var_member_records = {}
            for record in t_movement_var_member_records:
                dict_movement_var_member_records[record.get('MVMT_VAR_MEMBER_LINK_ID')] = record

            # 代入値自動登録設定から対象のMovementのレコードを取得
            where_str = 'WHERE MOVEMENT_ID = %s AND DISUSE_FLAG = %s'
            t_value_autoreg_records = self.ws_db.table_select(self.TFConst.T_VALUE_AUTOREG, where_str, [self.movement_id, 0])

            # 代入値自動登録設定のレコードをループし、代入値管理に登録するための情報を作成する。
            for value_autoreg_record in t_value_autoreg_records:
                # 対象のカラムのメニュー(パラメータシート)が存在しているかのチェック
                # 「メニューグループ:メニュー:項目」で選択した値の詳細なカラム情報を取得
                column_list_id = value_autoreg_record.get('COLUMN_LIST_ID')
                ret, column_data = self.get_column_list_data(column_list_id)
                if not ret:
                    # 対象項目のメニューもしくは項目が存在しない(廃止されている)ためスキップ
                    continue

                # 変数名(MVMT_VAR_LINK_ID)がMovement-変数紐付メニューに存在しているかのチェック
                mvmt_var_link_id = value_autoreg_record.get('MVMT_VAR_LINK_ID')
                if not dict_movement_var_records.get(mvmt_var_link_id):
                    # Movement-変数紐付に対象のレコードがない(廃止されている)ためスキップ
                    continue

                # メンバー変数名(MVMT_VAR_MEMBER_LINK_ID)がMovement-メンバー変数紐付メニューに存在しているかのチェック
                mvmt_var_member_link_id = value_autoreg_record.get('MEMBER_VARS_ID')
                if mvmt_var_member_link_id:
                    if not dict_movement_var_member_records.get(mvmt_var_member_link_id):
                        # Movement-変数紐付に対象のレコードがない(廃止されている)ためスキップ
                        continue

                # パラメータシートから具体値を取得する
                col_type = value_autoreg_record.get('COL_TYPE')
                if str(col_type) == (self.TFConst.COL_TYPE_VAL):
                    # value型の場合
                    ret, vars_entry, register_flag = self.get_vars_entry_value(column_data, value_autoreg_record)
                else:
                    # key型の場合
                    ret, vars_entry, register_flag = self.get_vars_entry_key(column_data, value_autoreg_record)

                if not ret:
                    # 具体値の取得処理がFalseで返却された場合はcontinue
                    continue

                # register_flagがTrueの場合は代入値管理に登録するデータを生成
                if register_flag:
                    # value型かつ、パラメータシートのカラムクラスがパスワードカラム(ID:8)の場合Sensitive設定をTrue(1)に設定する
                    column_class = column_data.get('COLUMN_CLASS')
                    sensitive_flag = "0"
                    if str(col_type) == (self.TFConst.COL_TYPE_VAL) and str(column_class) == "8":
                        sensitive_flag = "1"

                    insert_data = {
                        "EXECUTION_NO": self.execution_no,
                        "OPERATION_ID": self.operation_id,
                        "MOVEMENT_ID": self.movement_id,
                        "MVMT_VAR_LINK_ID": mvmt_var_link_id,
                        "HCL_FLAG": value_autoreg_record.get('HCL_FLAG'),
                        "MEMBER_VARS_ID": mvmt_var_member_link_id,
                        "ASSIGN_SEQ": value_autoreg_record.get('ASSIGN_SEQ'),
                        "SENSITIVE_FLAG": sensitive_flag,
                        "VARS_ENTRY": vars_entry,
                        "DISUSE_FLAG": "0",
                        "LAST_UPDATE_USER": g.get('USER_ID')
                    }

                    var_assign_data_list.append(insert_data)

        except Exception as e:
            result = False
            msg = e

        return result, msg, var_assign_data_list

    def set_if_null_data_handling_flag(self):
        """
        インターフェース情報からNULL連携の設定値をselfに反映させる
        """
        # 返却値定義
        result = True
        msg = ''

        try:
            # インターフェース情報からレコードを取得
            where_str = 'WHERE DISUSE_FLAG = %s'
            t_if_info_records = self.ws_db.table_select(self.TFConst.T_IF_INFO, where_str, [0])

            # 「インターフェース情報」レコードが1つではない場合エラー
            if not len(t_if_info_records) == 1:
                log_msg = g.appmsg.get_log_message("MSG-81001", [])
                g.applogger.error(log_msg)
                msg = g.appmsg.get_api_message("MSG-81001", [])
                result = False
            else:
                # 「インターフェース情報」のレコードをセット
                self.if_null_data_handling_flg = t_if_info_records[0].get('NULL_DATA_HANDLING_FLG')

        except Exception as e:
            result = False
            msg = e

        return result, msg

    def get_column_list_data(self, column_list_id):
        """
        代入値自動登録設定の「メニューグループ:メニュー:項目」の値がアクティブかどうかをチェックする(メニューや項目が廃止されている場合はFalseを返却)
        """
        # 返却値定義
        result = True
        column_data = None

        try:
            # パラメータシート(オペレーションあり)の項目一覧VIEWから、対象のメニューIDを特定する
            where_str = 'WHERE COLUMN_DEFINITION_ID = %s AND DISUSE_FLAG = %s'
            v_terf_column_list_record = self.ws_db.table_select(self.TFConst.V_COLUMN_LIST, where_str, [column_list_id, 0])
            if not v_terf_column_list_record:
                # 対象のレコードが存在しない場合はFalseを設定
                result = False
            else:
                column_data = v_terf_column_list_record[0]

        except Exception as e:
            g.applogger.error(str(e))
            result = False

        return result, column_data

    def get_vars_entry_value(self, column_data, value_autoreg_record):
        """
        パラメータシートから具体値を取得して返却する(value型)
        """
        # 返却値定義
        result = True
        vars_entry = None
        register_flag = False
        try:
            menu_id = column_data.get('MENU_ID')
            column_name_rest = column_data.get('COLUMN_NAME_REST')

            # 対象のメニューIDをもとに「メニュー-テーブル紐付管理」から対象のテーブルを取得する
            where_str = 'WHERE MENU_ID = %s AND DISUSE_FLAG = %s'
            t_comn_menu_table_link_record = self.ws_db.table_select('T_COMN_MENU_TABLE_LINK', where_str, [menu_id, 0])
            if not t_comn_menu_table_link_record:
                # 対象のメニュー-テーブル紐付管理のレコードが存在しない場合終了(正常)
                return result, vars_entry, register_flag

            # テーブル名を取得
            cmdb_table_name = t_comn_menu_table_link_record[0].get('TABLE_NAME')

            # バンドルが有効かどうかを取得
            vertical_flag = True if str(t_comn_menu_table_link_record[0].get('VERTICAL')) == '1' else False

            # 対象のテーブルからOPERATION_IDが一致しているレコードを取得
            if vertical_flag:
                # 代入順序とオペレーションIDの一致を取得する
                column_assign_seq = value_autoreg_record.get('COLUMN_ASSIGN_SEQ')
                where_str = 'WHERE OPERATION_ID = %s AND INPUT_ORDER = %s AND DISUSE_FLAG = %s'
                t_cmdb_record = self.ws_db.table_select(cmdb_table_name, where_str, [self.operation_id, column_assign_seq, 0])
            else:
                # オペレーションIDの一致を取得する
                where_str = 'WHERE OPERATION_ID = %s AND DISUSE_FLAG = %s'
                t_cmdb_record = self.ws_db.table_select(cmdb_table_name, where_str, [self.operation_id, 0])

            if not t_cmdb_record:
                # 対象のレコードが存在しない場合はreturn(正常)
                return result, vars_entry, register_flag

            # DATA_JSONカラムからcolumn_name_restがkeyとなっている値を取得し、vars_entryとして設定する
            data_json = t_cmdb_record[0].get('DATA_JSON')
            data_dict = json.loads(data_json)
            vars_entry = data_dict.get(column_name_rest)

            # NULL連携の設定値を取得する
            null_data_handling_flg = value_autoreg_record.get('NULL_DATA_HANDLING_FLG')
            if not null_data_handling_flg:
                # 代入値自動登録設定のNULL連携の値が空の場合、インターフェース情報の設定値を採用する
                null_data_handling_flg = self.if_null_data_handling_flg

            # 登録フラグ判定
            if vars_entry:
                # vars_entryに値がある場合はregister_flagをTrueにする
                register_flag = True
            elif str(null_data_handling_flg) == '1':
                # vars_entryが空(None)でもNULL連携が有効(1)の場合はregister_flagをTrueにする
                register_flag = True
            else:
                # vars_entryに値がない場合や、NULL連携が有効(1)ではない場合はregister_flagをFalseにする
                register_flag = False

        except Exception as e:
            g.applogger.error(str(e))
            result = False
            vars_entry = None
            register_flag = False

        return result, vars_entry, register_flag

    def get_vars_entry_key(self, column_data, value_autoreg_record):
        """
        パラメータシートから具体値を取得して返却する(key型)
        """
        # 返却値定義
        result = True
        vars_entry = None
        register_flag = True
        try:
            if g.LANGUAGE == 'ja':
                col_name = column_data['COLUMN_NAME_JA']
            else:
                col_name = column_data['COLUMN_NAME_EN']

            # 項目名を具体値に設定
            vars_entry = col_name

            # NULL連携の設定値を取得する
            null_data_handling_flg = value_autoreg_record.get('NULL_DATA_HANDLING_FLG')
            if not null_data_handling_flg:
                # 代入値自動登録設定のNULL連携の値が空の場合、インターフェース情報の設定値を採用する
                null_data_handling_flg = self.if_null_data_handling_flg

            # 登録フラグ判定(key型の場合、項目名が空になるケースは基本的に起こりえないため、register_flagはTrueになるケースしか通らない)
            if vars_entry:
                # vars_entryに値がある場合はregister_flagをTrueにする
                register_flag = True
            elif str(null_data_handling_flg) == '1':
                # vars_entryが空(None)でもNULL連携が有効(1)の場合はregister_flagをTrueにする
                register_flag = True
            else:
                # vars_entryに値がない場合や、NULL連携が有効(1)ではない場合はregister_flagをFalseにする
                register_flag = False

        except Exception as e:
            g.applogger.error(str(e))
            result = False
            vars_entry = None
            register_flag = False

        return result, vars_entry, register_flag
