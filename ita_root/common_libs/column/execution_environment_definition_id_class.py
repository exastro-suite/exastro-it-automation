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
from common_libs.common.util import print_exception_msg, get_iso_datetime, arrange_stacktrace_format

# import column_class
from .id_class import IDColumn

class ExecutionEnvironmentDefinitionIDColumn(IDColumn):
    """
    実行環境名プルダウンクラス
    """
    def search_id_data_list(self):
        ret_values = {}
        lang = g.get('LANGUAGE')
        lang_menu_name_column = {}
        lang_menu_name_column['ja'] = "MENU_NAME_JA"
        lang_menu_name_column['en'] = "MENU_NAME_EN"

        # 実行環境パラメータ定義用パラメータシートのシート名とテーブル名所得
        sql = """
              SELECT
                  TBL_1.{} AS MENU_NAME,
                  TBL_2.TABLE_NAME
              FROM
                  (
                      SELECT
                          *
                      FROM
                          T_COMN_MENU
                      WHERE
                          MENU_NAME_REST LIKE 'execution_environment_parameter_definition_sheet%' AND
                          DISUSE_FLAG = 0
                  ) TBL_1
                  LEFT JOIN T_MENU_TABLE_LINK TBL_2 ON (TBL_1.MENU_ID        = TBL_2.MENU_NAME_REST)
                  LEFT JOIN T_MENU_DEFINE     TBL_3 ON (TBL_1.MENU_NAME_REST = TBL_3.MENU_NAME_REST)
                  LEFT JOIN (
                              SELECT
                                  *
                              FROM
                                  T_MENU_COLUMN
                              WHERE
                                  COLUMN_NAME_REST = 'execution_environment_name' AND
                                  DISUSE_FLAG = '0'
                          ) TBL_4 ON (TBL_3.MENU_CREATE_ID = TBL_4.MENU_CREATE_ID)
              WHERE
                  TBL_2.DISUSE_FLAG = '0' AND
                  TBL_3.DISUSE_FLAG = '0' AND
                  TBL_3.SHEET_TYPE  = '2'
              """.format(lang_menu_name_column[lang])

        # 実行環境パラメータ定義用パラメータシートの実行環境定義名取得
        sql = sql.format(lang_menu_name_column[lang])
        sheet_rows = self.objdbca.sql_execute(sql, bind_value_list=[])
        if len(sheet_rows) == 0:
            #MSG-10973	実行環境パラメータ定義用パラメータシートが未登録
            g.applogger.info(g.appmsg.get_api_message("MSG-10973", []))
            return ret_values
        for sheet_row in sheet_rows:
            # 実行環境パラメータ定義用パラメータシートの実行環境定義名取得
            sql = "SELECT * FROM `{}` WHERE DISUSE_FLAG = '0'".format(sheet_row['TABLE_NAME'])
            table_rows = self.objdbca.sql_execute(sql, bind_value_list=[])
            for table_row in table_rows:
                sheet_cols = json.loads(table_row['DATA_JSON'])
                if "execution_environment_name" in sheet_cols:
                    # プルダウンのキー値
                    key = "{},{}".format(sheet_row["TABLE_NAME"],table_row["ROW_ID"])
                    # プルダウンの表示値
                    value = "{}/{}".format(sheet_row["MENU_NAME"],sheet_cols["execution_environment_name"])
                    ret_values[key] = value
                else:
                    g.applogger.info(g.appmsg.get_api_message("MSG-10974", [sheet_row['TABLE_NAME'], str(sheet_cols)]))

        return ret_values

    # [load_table] 値を出力用の値へ変換
    def convert_value_output(self, key=''):
        """
            値を出力用の値へ変換
            ARGS:
                val:値
            RETRUN:
                retBool, msg, val
        """
        msg = ''
        output_val = ""
        master_row = self.search_id_data_list()
        search_candidates = []
        if key:
            if key in master_row:
                output_val = master_row[key]
            else:
                # 廃止されているデータをID変換失敗(key)として扱う
                output_val = g.appmsg.get_api_message('MSG-00001', [key])

        return True, msg, output_val,

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
        id_data_list = self.search_id_data_list()

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
                bindvalues.setdefault(bindkey, "{}".format(bindvalue))
                listno += 1

            str_where = ""
            for bindkey in bindkeys:
                tmp_where = " `{col_name}` like {bindkey} ".format(
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

    # [FILTER] プルダウン検索ボタンクリック時
    def csv_key_to_keyname_convart(self, column_value, search_candidates, master_row):
        # json_key_to_keyname_convartを真似する
        """
            CSV形式で格納されているKey(DB)を名称リストに変換
            フィルタのプルダウン検索の表示する内容
            ARGS:
                column_value:  CSV形式で格納されている "テーブル名","レコードNo"
                search_candidates: 名称リスト
                master_row:    マスタテーブルデータ {key: value, ...}
            RETRUN:
                名称リスト
        """
        try:
            if not column_value:
                return search_candidates
            ary = column_value.split(",")
            if not ary[0] or len(ary) != 2:
                err_msg = g.appmsg.get_api_message('MSG-01710', [column_value])
                raise Exception(err_msg)
        except Exception as e:
            raise e
        key = column_value
        # key値に該当する名称がない場合は無視
        if key in master_row.keys():
            val = master_row[key]
            if not search_candidates.count(val):
                search_candidates.append(val)
            else:
                pass
        return search_candidates

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
        msg = ""
        conv_value = ""

        lang = g.get('LANGUAGE')
        lang_menu_name_column = {}
        lang_menu_name_column['ja'] = "MENU_NAME_JA"
        lang_menu_name_column['en'] = "MENU_NAME_EN"
        try:
            if not valnames:
                return valnames
            ary = valnames.split("/")
            menu_name = ary[0]
            execution_environment_name = ary[1]
            if not ary[0] or len(ary) != 2:
                err_msg = g.appmsg.get_api_message('MSG-01710', [valnames])
                raise Exception(err_msg)
        except Exception as e:
            raise e
        sql = """
                SELECT
                    TBL_3.TABLE_NAME,
                    TBL_1.DISUSE_FLAG AS T_MENU_DEFINE_USE_FLAG,
                    TBL_2.DISUSE_FLAG AS T_COMN_MENU_USE_FLAG,
                    TBL_3.DISUSE_FLAG AS T_MENU_TABLE_LINKE_USE_FLAG,
                    TBL_4.DISUSE_FLAG AS T_MENU_COLUMN_USE_FLAG
                FROM
                    (
                        SELECT
                            *
                        FROM
                            T_MENU_DEFINE
                        WHERE
                            {}  = '{}'         AND
                            DISUSE_FLAG   = '0'
                    ) TBL_1
                    LEFT JOIN T_COMN_MENU        TBL_2 ON (TBL_1.MENU_NAME_REST = TBL_2.MENU_NAME_REST)
                    LEFT JOIN T_MENU_TABLE_LINK  TBL_3 ON (TBL_2.MENU_ID        = TBL_3.MENU_NAME_REST)
                    LEFT JOIN T_MENU_COLUMN      TBL_4 on (TBL_1.MENU_CREATE_ID = TBL_4.MENU_CREATE_ID)
                WHERE
                    TBL_2.DISUSE_FLAG = '0'  AND
                    TBL_3.DISUSE_FLAG = '0'  AND
                    TBL_4.DISUSE_FLAG = '0'  AND
                    TBL_4.COLUMN_NAME_REST = 'execution_environment_name'
            """.format(lang_menu_name_column[lang], menu_name)
        # 実行環境パラメータ定義用パラメータシートの実行環境定義名取得
        sql = sql.format(lang_menu_name_column[lang])
        sheet_rows = self.objdbca.sql_execute(sql, bind_value_list=[])
        if len(sheet_rows) == 0:
            retBool = False
            mag = g.appmsg.get_api_message("MSG-10973", [])
            return retBool, msg, "",
        row = sheet_rows[0]
        if not row['T_COMN_MENU_USE_FLAG']:
            retBool = False
            mag = g.appmsg.get_api_message("MSG-10975", [menu_name, "T_COMN_MENU"])
            return retBool, msg, "",
        if not row['T_MENU_TABLE_LINKE_USE_FLAG']:
            retBool = False
            mag = g.appmsg.get_api_message("MSG-10975", [menu_name, "T_MENU_TABLE"])
            return retBool, msg, "",
        if not row['T_MENU_COLUMN_USE_FLAG']:
            retBool = False
            mag = g.appmsg.get_api_message("MSG-10975", [menu_name, "T_MENU_COLUMN"])
            return retBool, msg, "",
        table_name = row['TABLE_NAME']

        sql = "SELECT * FROM `{}` WHERE DISUSE_FLAG = '0'".format(table_name)
        table_rows = self.objdbca.sql_execute(sql, bind_value_list=[])
        for table_row in table_rows:
            sheet_cols = json.loads(table_row['DATA_JSON'])
            if "execution_environment_name" in sheet_cols:
                conv_value = "{},{}".format(table_name, table_row["ROW_ID"])
            else:
                g.applogger.info(g.appmsg.get_api_message("MSG-10974", [table_name, str(sheet_cols)]))
        if not conv_value:
            retBool = False
            msg = g.appmsg.get_api_message("MSG-10976", [table_name])

        return retBool, msg, conv_value,

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
                split_val = val.split(",")
                if not split_val[0] or len(split_val) != 2:
                    retBool = False
                    status_code = '499-01710'
                    msg_args = [val]
                    msg = g.appmsg.get_api_message(status_code, msg_args)

        return retBool, msg,

#    def get_values_by_value(self, where_equal=[], where_like=""):
#        # 不要
#        pass
