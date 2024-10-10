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
"""
代入値自動登録とパラメータシートを抜くmodule
"""

import os
import inspect
import copy

from flask import g

from common_libs.common import *  # noqa F403
from common_libs.loadtable import *  # noqa F403
from common_libs.common.exception import *  # noqa F403
from .AnscConstClass import AnscConst
from .WrappedStringReplaceAdmin import WrappedStringReplaceAdmin
from common_libs.common.storage_access import storage_base

# ローカル変数(全体)宣言
lv_val_assign_tbl = 'T_ANSR_VALUE_AUTOREG'
lv_l_val_assign_tbl = 'T_ANSL_VALUE_AUTOREG'
lv_p_val_assign_tbl = 'T_ANSP_VALUE_AUTOREG'
lv_pattern_link_tbl = 'T_ANSR_MVMT_MATL_LINK'
lv_l_pattern_link_tbl = 'T_ANSL_MVMT_MATL_LINK'
lv_p_pattern_link_tbl = 'T_ANSP_MVMT_MATL_LINK'
lv_ptn_vars_link_tbl = 'T_ANSR_MVMT_VAR_LINK'
lv_l_ptn_vars_link_tbl = 'T_ANSL_MVMT_VAR_LINK'
lv_p_ptn_vars_link_tbl = 'T_ANSP_MVMT_VAR_LINK'
lv_member_col_comb_tbl = 'T_ANSR_NESTVAR_MEMBER_COL_COMB'
lv_array_member_tbl = 'T_ANSR_NESTVAR_MEMBER'


class SubValueAutoReg():
    """
    代入値自動登録とパラメータシートを抜くclass
    """

    # カラムクラスのマスタ
    ColumnClassMaster_IDMap = {}

    def __init__(self, in_driver_name="", ws_db=None):

        """
        処理内容
            コンストラクタ
        パラメータ
            ansible_driver: ansibleドライバ名
            ws_db: WorkspaceDBインスタンス
        戻り値
            なし
        """

        self.in_driver_name = in_driver_name
        self.ws_db = ws_db

        self.getFromColumnClassMaster(None, ws_db)

    def get_data_from_parameter_sheet(self, operation_id="", movement_id="", execution_no=""):
        """
        代入値自動登録とパラメータシートを抜く
        """

        # インターフェース情報からNULLデータを代入値管理に登録するかのデフォルト値を取得する。
        ret = self.getIFInfoDB(self.ws_db)
        if ret[0] is False:
            raise ValidationException(ret[2])

        lv_if_info = ret[1]
        g_null_data_handling_def = lv_if_info["NULL_DATA_HANDLING_FLG"]

        # 代入値自動登録設定からカラム毎の変数の情報を取得
        # トレースメッセージ
        traceMsg = g.appmsg.get_api_message("MSG-10804")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)

        ret = self.read_val_assign(self.in_driver_name, self.ws_db, movement_id)
        if ret[0] is False:
            raise ValidationException("MSG-10353")

        lv_tableNameToMenuIdList = ret[1]
        lv_tabColNameToValAssRowList = ret[2]
        lv_tableNameToPKeyNameList = ret[3]
        # lv_tableNameToMenuNameRestList = ret[4]
        # data_cnt_ary = ret[5]

        # 紐付メニューへのSELECT文を生成する。
        ret = self.createQuerySelectCMDB(lv_tableNameToMenuIdList, lv_tabColNameToValAssRowList, lv_tableNameToPKeyNameList, self.ws_db)
        # 代入値紐付メニュー毎のSELECT文配列
        lv_tableNameToSqlList = ret

        # 紐付メニューから具体値を取得する。
        traceMsg = g.appmsg.get_api_message("MSG-10805")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)

        ret = self.getCMDBdata(lv_tableNameToSqlList, lv_tableNameToMenuIdList, lv_tabColNameToValAssRowList, operation_id, self.ws_db, g_null_data_handling_def)
        lv_varsAssList = ret[0]
        lv_arrayVarsAssList = ret[1]

        # トランザクション開始
        traceMsg = g.appmsg.get_api_message("MSG-10785")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)

        self.ws_db.db_transaction_start()

        # 作業対象ホストに登録が必要な配列初期化
        lv_phoLinkList = {}

        # 一般変数・複数具体値変数を紐付けている紐付メニューの具体値を代入値管理に登録
        # トレースメッセージ
        traceMsg = g.appmsg.get_api_message("MSG-10833")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)

        # 代入値管理レコードのテンプレート
        subst_value_tpl_row = {
            # "ASSIGN_ID": "",
            "EXECUTION_NO": "",
            "OPERATION_ID": "",
            "MOVEMENT_ID": "",
            "SYSTEM_ID": "",
            "MVMT_VAR_LINK_ID": "",
            "SENSITIVE_FLAG": "",
            "VARS_ENTRY": "",
            "VARS_ENTRY_FILE": "",
            "ASSIGN_SEQ": "",
            "VARS_ENTRY_USE_TPFVARS": "",
            "NOTE": "",
            "DISUSE_FLAG": "",
            "LAST_UPDATE_TIMESTAMP": "",
            "LAST_UPDATE_USER": ""
        }
        if self.in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            subst_value_list_menu_id = "20409"
            subst_value_list_table = "T_ANSR_VALUE"
            # ROLEは多次元配列変数がある
            subst_value_tpl_row = {
                # "ASSIGN_ID": "",
                "EXECUTION_NO": "",
                "OPERATION_ID": "",
                "MOVEMENT_ID": "",
                "SYSTEM_ID": "",
                "MVMT_VAR_LINK_ID": "",
                "COL_SEQ_COMBINATION_ID": "", # role
                "SENSITIVE_FLAG": "",
                "VARS_ENTRY": "",
                "VARS_ENTRY_FILE": "",
                "ASSIGN_SEQ": "",
                "VARS_ENTRY_USE_TPFVARS": "",
                "NOTE": "",
                "DISUSE_FLAG": "",
                "LAST_UPDATE_TIMESTAMP": "",
                "LAST_UPDATE_USER": ""
            }
        elif self.in_driver_name == AnscConst.DF_LEGACY_DRIVER_ID:
            subst_value_list_menu_id = "20207"
            subst_value_list_table = "T_ANSL_VALUE"
        elif self.in_driver_name == AnscConst.DF_PIONEER_DRIVER_ID:
            subst_value_list_menu_id = "20309"
            subst_value_list_table = "T_ANSP_VALUE"

        # 変数抜出及び変数具体値置き換モジュール
        var_extractor = WrappedStringReplaceAdmin(self.ws_db)

        for varsAssRecord in lv_varsAssList:
            # 処理対象外のデータかを判定
            if 'TABLE_NAME' not in varsAssRecord:
                continue
            if varsAssRecord['STATUS'] is False:
                continue
            if not operation_id == varsAssRecord['OPERATION_ID'] or not movement_id == varsAssRecord['MOVEMENT_ID']:
                continue

            # 代入値管理に具体値を登録
            # 項目なしの場合はスキップ
            if not varsAssRecord['STATUS'] == 'skip':
                ret = self.addStg1StdListVarsAssign(varsAssRecord, execution_no, subst_value_tpl_row.copy(), subst_value_list_table, subst_value_list_menu_id, var_extractor, self.ws_db)
                if ret is False:
                    msgstr = g.appmsg.get_api_message("MSG-10466")
                    g.applogger.info(os.path.basename(__file__) + " " + msgstr + " " + varsAssRecord)
                    continue

            # 作業対象ホストに登録が必要な情報を退避
            if varsAssRecord['OPERATION_ID'] not in lv_phoLinkList:
                lv_phoLinkList[varsAssRecord['OPERATION_ID']] = {}
            if varsAssRecord['MOVEMENT_ID'] not in lv_phoLinkList[varsAssRecord['OPERATION_ID']]:
                lv_phoLinkList[varsAssRecord['OPERATION_ID']][varsAssRecord['MOVEMENT_ID']] = {}
            if varsAssRecord['SYSTEM_ID'] not in lv_phoLinkList[varsAssRecord['OPERATION_ID']][varsAssRecord['MOVEMENT_ID']]:
                lv_phoLinkList[varsAssRecord['OPERATION_ID']][varsAssRecord['MOVEMENT_ID']][varsAssRecord['SYSTEM_ID']] = {}

        # 多次元変数を紐付けている紐付メニューの具体値を代入値管理に登録
        # トレースメッセージ
        traceMsg = g.appmsg.get_api_message("MSG-10834")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)

        for varsAssRecord in lv_arrayVarsAssList:
            # 処理対象外のデータかを判定
            if 'TABLE_NAME' not in varsAssRecord:
                continue
            if varsAssRecord['STATUS'] is False:
                continue

            # 代入値管理に具体値を登録
            # 項目なしの場合はスキップ
            if not varsAssRecord['STATUS'] == 'skip':
                ret = self.addStg1ArrayVarsAssign(varsAssRecord, execution_no, subst_value_tpl_row.copy(), subst_value_list_table, subst_value_list_menu_id, var_extractor, self.ws_db)
                if ret is False:
                    msgstr = g.appmsg.get_api_message("MSG-10441")
                    g.applogger.info(os.path.basename(__file__) + " " + msgstr + " " + varsAssRecord)
                    continue

            # 作業対象ホストに登録が必要な情報を退避
            if varsAssRecord['OPERATION_ID'] not in lv_phoLinkList:
                lv_phoLinkList[varsAssRecord['OPERATION_ID']] = {}
            if varsAssRecord['MOVEMENT_ID'] not in lv_phoLinkList[varsAssRecord['OPERATION_ID']]:
                lv_phoLinkList[varsAssRecord['OPERATION_ID']][varsAssRecord['MOVEMENT_ID']] = {}
            if varsAssRecord['SYSTEM_ID'] not in lv_phoLinkList[varsAssRecord['OPERATION_ID']][varsAssRecord['MOVEMENT_ID']]:
                lv_phoLinkList[varsAssRecord['OPERATION_ID']][varsAssRecord['MOVEMENT_ID']][varsAssRecord['SYSTEM_ID']] = {}

        del lv_tableNameToMenuIdList
        del lv_varsAssList
        del lv_arrayVarsAssList

        # コミット(レコードロックを解除)
        # トランザクション終了
        self.ws_db.db_transaction_end(True)

        # トレースメッセージ
        traceMsg = g.appmsg.get_api_message("MSG-10785")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)

        self.ws_db.db_transaction_start()

        # 代入値管理で登録したオペ+作業パターン+ホストが作業対象ホストに登録されているか判定し、未登録の場合は登録する
        # トレースメッセージ
        traceMsg = g.appmsg.get_api_message("MSG-10810")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)

        # 作業対象ホストレコードのテンプレート
        trg_host_tpl_row = {
            # "PHO_LINK_ID": "",
            "EXECUTION_NO": "",
            "OPERATION_ID": "",
            "MOVEMENT_ID": "",
            "SYSTEM_ID": "",
            "NOTE": "",
            "DISUSE_FLAG": "",
            "LAST_UPDATE_TIMESTAMP": "",
            "LAST_UPDATE_USER": ""
        }
        if self.in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            trg_host_table = "T_ANSR_TGT_HOST"
        elif self.in_driver_name == AnscConst.DF_LEGACY_DRIVER_ID:
            trg_host_table = "T_ANSL_TGT_HOST"
        elif self.in_driver_name == AnscConst.DF_PIONEER_DRIVER_ID:
            trg_host_table = "T_ANSP_TGT_HOST"

        for ope_id, ptn_list in lv_phoLinkList.items():
            for ptn_id, host_list in ptn_list.items():
                for host_id, access_auth in host_list.items():
                    lv_phoLinkData = {'OPERATION_ID': ope_id, 'MOVEMENT_ID': ptn_id, 'SYSTEM_ID': host_id}
                    ret = self.addStg1PhoLink(lv_phoLinkData, execution_no, trg_host_tpl_row.copy(), trg_host_table, self.ws_db)

                    if ret is False:
                        raise ValidationException("MSG-10373")

        del lv_phoLinkList

        # コミット(レコードロックを解除)
        # トランザクション終了
        self.ws_db.db_transaction_end(True)

        return True

    def get_data_from_all_parameter_sheet(self):
        """
        代入値自動登録とパラメータシートを抜く
        """

        # インターフェース情報からNULLデータを代入値管理に登録するかのデフォルト値を取得する。
        ret = self.getIFInfoDB(self.ws_db)
        if ret[0] is False:
            raise ValidationException(ret[2])

        lv_if_info = ret[1]
        g_null_data_handling_def = lv_if_info["NULL_DATA_HANDLING_FLG"]

        # 代入値自動登録設定からカラム毎の変数の情報を取得
        # トレースメッセージ
        traceMsg = g.appmsg.get_api_message("MSG-10804")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)

        ret = self.read_val_assign(self.in_driver_name, self.ws_db)
        if ret[0] is False:
            raise ValidationException("MSG-10353")

        lv_tableNameToMenuIdList = ret[1]
        lv_tabColNameToValAssRowList = ret[2]
        lv_tableNameToPKeyNameList = ret[3]
        # lv_tableNameToMenuNameRestList = ret[4]
        # data_cnt_ary = ret[5]

        # 紐付メニューへのSELECT文を生成する。
        ret = self.createQuerySelectCMDB(lv_tableNameToMenuIdList, lv_tabColNameToValAssRowList, lv_tableNameToPKeyNameList, self.ws_db)
        # 代入値紐付メニュー毎のSELECT文配列
        lv_tableNameToSqlList = ret

        # 紐付メニューから具体値を取得する。
        traceMsg = g.appmsg.get_api_message("MSG-10805")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)

        ret = self.getCMDBdata(lv_tableNameToSqlList, lv_tableNameToMenuIdList, lv_tabColNameToValAssRowList, None, self.ws_db, g_null_data_handling_def)
        lv_varsAssList = ret[0]
        lv_arrayVarsAssList = ret[1]

        template_list = {} # { MovementID: { TPF変数名: 0 }, … }
        host_list = {} # { MovementID: { OPERATION_ID: { SYSTEM_ID: 0 }, … }, … }

        var_extractor = WrappedStringReplaceAdmin()

        # 一般変数・複数具体値変数を紐付けている紐付メニューの具体値からTPF変数を抽出する
        for varsAssRecord in lv_varsAssList:
            template_list, host_list = self.extract_tpl_vars(var_extractor, varsAssRecord, template_list, host_list)

        # 多次元変数を紐付けている紐付メニューの具体値からTPF変数を抽出する
        for varsAssRecord in lv_arrayVarsAssList:
            template_list, host_list = self.extract_tpl_vars(var_extractor, varsAssRecord, template_list, host_list)

        return True, template_list, host_list

    def addStg1PhoLink(self, in_phoLinkData, execution_no, tgt_row, trg_host_table, WS_DB):
        """
        作業対象ホストの廃止レコードを復活または新規レコード追加

        Arguments:
            in_phoLinkData: 作業対象ホスト更新情報配列
            execution_no
            tgt_row
            trg_host_table: 作業対象ホストテーブル
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
        """

        # 登録する情報設定
        tgt_row['EXECUTION_NO'] = execution_no
        tgt_row['OPERATION_ID'] = in_phoLinkData['OPERATION_ID']
        tgt_row['MOVEMENT_ID'] = in_phoLinkData['MOVEMENT_ID']
        tgt_row['SYSTEM_ID'] = in_phoLinkData['SYSTEM_ID']
        tgt_row['DISUSE_FLAG'] = "0"
        # tgt_row['LAST_UPDATE_TIMESTAMP']
        tgt_row['LAST_UPDATE_USER'] = g.USER_ID

        ret = self.exec_maintenance(WS_DB, trg_host_table, 'PHO_LINK_ID', tgt_row)

        if ret[0] is False:
            raise AppException("499-00701", [ret[1]], [ret[1]])

        return True

    def createQuerySelectCMDB(self, in_tableNameToMenuIdList, in_tabColNameToValAssRowList, in_tableNameToPKeyNameList, WS_DB):
        """
        代入値紐付メニューへのSELECT文を生成する。

        Arguments:
            in_tableNameToMenuIdList: テーブル名配列
            in_tabColNameToValAssRowList: テーブル名+カラム名配列
            in_tableNameToPKeyNameList: テーブル主キー名配列

        Returns:
            is success:(bool)
            defvarsList: 抽出した変数
        """

        inout_tableNameToSqlList = {}

        opeid_chk_sql = "( SELECT \n"
        opeid_chk_sql += " OPERATION_ID \n"
        opeid_chk_sql += " FROM T_COMN_OPERATION \n"
        opeid_chk_sql += " WHERE OPERATION_ID = TBL_A.OPERATION_ID AND \n"
        opeid_chk_sql += " DISUSE_FLAG = '0' \n"
        opeid_chk_sql += ") AS  OPERATION_ID , \n"

        # 機器一覧にホストが登録されているかを判定するSQL
        hostid_chk_sql = "( SELECT \n"
        hostid_chk_sql += "   COUNT(*) \n"
        hostid_chk_sql += " FROM T_ANSC_DEVICE \n"
        hostid_chk_sql += " WHERE SYSTEM_ID = TBL_A.HOST_ID AND \n"
        hostid_chk_sql += " DISUSE_FLAG = '0' \n"
        hostid_chk_sql += " ) AS %s, \n"

        # テーブル名+カラム名配列からテーブル名と配列名を取得
        inout_tableNameToSqlList = {}
        for table_name, col_list in in_tabColNameToValAssRowList.items():
            input_order_flg = False
            data_cnt = 0
            pkey_name = in_tableNameToPKeyNameList[table_name]

            col_sql = ""
            for col_name, col_value in col_list.items():
                col_sql = col_sql + ", TBL_A." + col_name + " \n"

            if col_sql == "":
                # SELECT対象の項目なし
                # エラーがあるのでスキップ
                msgstr = g.appmsg.get_api_message("MSG-10356", [in_tableNameToMenuIdList[table_name]])
                frame = inspect.currentframe().f_back
                g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                # 次のテーブルへ
                continue

            # パラメータシートのテーブル構成確認
            where = "WHERE DISUSE_FLAG = '0'"
            ret = WS_DB.table_select(table_name, where, [])
            for value in ret:
                if "INPUT_ORDER" in value:
                    input_order_flg = True

            # SELECT文を生成
            make_sql = "SELECT \n "
            make_sql += opeid_chk_sql + " \n "
            make_sql += hostid_chk_sql + " \n "
            make_sql += " TBL_A." + pkey_name + " AS %s   \n "
            make_sql += ", TBL_A.HOST_ID \n "
            for tmp_col_value in col_value.values():
                # 代入値自動登録管理とパラメータシートで縦メニュー用代入順序の差異がある場合ログを出してスキップする。
                if tmp_col_value["COLUMN_ASSIGN_SEQ"] is not None and input_order_flg is False:
                    msgstr = g.appmsg.get_api_message("MSG-10939", [tmp_col_value["COLUMN_ID"]])
                    frame = inspect.currentframe().f_back
                    g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                    continue
                elif tmp_col_value["COLUMN_ASSIGN_SEQ"] is None and input_order_flg is True:
                    msgstr = g.appmsg.get_api_message("MSG-10940", [tmp_col_value["COLUMN_ID"]])
                    frame = inspect.currentframe().f_back
                    g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                    continue

                # パラメータシートに縦メニュー用代入順序があるか判定
                if tmp_col_value["COLUMN_ASSIGN_SEQ"] is not None and input_order_flg is True:
                    make_sql += ", TBL_A.INPUT_ORDER \n "
                else:
                    make_sql += ", '' AS INPUT_ORDER \n "

                data_cnt += 1

            # 代入値自動登録管理とパラメータシートで縦メニュー用代入順序の差異がある場合ログを出してスキップする。
            if data_cnt == 0:
                if tmp_col_value["COLUMN_ASSIGN_SEQ"] is not None and input_order_flg is False:
                    continue
                elif tmp_col_value["COLUMN_ASSIGN_SEQ"] is None and input_order_flg is True:
                    continue

            make_sql += col_sql + " \n "
            make_sql += " FROM `" + table_name + "` TBL_A \n "
            make_sql += " WHERE DISUSE_FLAG = '0' \n "

            # メニューテーブルのSELECT SQL文退避
            inout_tableNameToSqlList[table_name] = make_sql

        return inout_tableNameToSqlList

    # def getVarsAssignRecodes(self, WS_DB):
    #     """
    #     代入値管理の情報を取得

    #     Arguments:
    #         WS_DB: WorkspaceDBインスタンス

    #     Returns:
    #         is success:(bool)
    #         in_VarsAssignRecodes: 代入値管理に登録されている変数リスト
    #         in_ArryVarsAssignRecodes: 代入値管理に登録されている多段変数リスト
    #     """

    #     global col_filepath

    #     in_VarsAssignRecodes = {}
    #     in_ArryVarsAssignRecodes = {}

    #     sqlUtnBody = "SELECT "
    #     sqlUtnBody += " ASSIGN_ID, "
    #     sqlUtnBody += " EXECUTION_NO, "
    #     sqlUtnBody += " OPERATION_ID, "
    #     sqlUtnBody += " MOVEMENT_ID, "
    #     sqlUtnBody += " SYSTEM_ID, "
    #     sqlUtnBody += " MVMT_VAR_LINK_ID, "
    #     sqlUtnBody += " COL_SEQ_COMBINATION_ID, "
    #     sqlUtnBody += " VARS_ENTRY, "
    #     sqlUtnBody += " SENSITIVE_FLAG, "
    #     sqlUtnBody += " VARS_ENTRY_FILE, "
    #     sqlUtnBody += " VARS_ENTRY_USE_TPFVARS, "
    #     sqlUtnBody += " ASSIGN_SEQ, "
    #     sqlUtnBody += " DISUSE_FLAG, "
    #     sqlUtnBody += " NOTE, "
    #     sqlUtnBody += " DATE_FORMAT(LAST_UPDATE_TIMESTAMP,'%Y/%m/%d %H:%i:%s.%f') LAST_UPDATE_TIMESTAMP, "
    #     sqlUtnBody += " CASE WHEN LAST_UPDATE_TIMESTAMP IS NULL THEN 'VALNULL' ELSE CONCAT('T_',DATE_FORMAT(LAST_UPDATE_TIMESTAMP,'%Y%m%d%H%i%s%f')) END UPD_UPDATE_TIMESTAMP, "
    #     sqlUtnBody += " LAST_UPDATE_USER "
    #     sqlUtnBody += " FROM T_ANSR_VALUE "
    #     sqlUtnBody += " WHERE ASSIGN_ID > '0' "

    #     ret = WS_DB.table_lock(['T_ANSR_VALUE'])

    #     data_list = WS_DB.sql_execute(sqlUtnBody, [])

    #     for row in data_list:
    #         FileName = row['VARS_ENTRY_FILE']
    #         row['VARS_ENTRY_FILE_MD5'] = ""
    #         row['VARS_ENTRY_FILE_PATH'] = ""

    #         if not FileName is None:

    #             row['VARS_ENTRY_FILE_PATH'] = col_filepath
    #             row['VARS_ENTRY_FILE_MD5'] = self.md5_file(col_filepath)

    #         if row["COL_SEQ_COMBINATION_ID"] is None or len(row["COL_SEQ_COMBINATION_ID"]) == 0:
    #             key = row["EXECUTION_NO"] + "_"
    #             key += row["OPERATION_ID"] + "_"
    #             key += row["MOVEMENT_ID"] + "_"
    #             key += row["SYSTEM_ID"] + "_"
    #             key += row["MVMT_VAR_LINK_ID"] + "_"
    #             key += "" + "_"
    #             key += str(row["ASSIGN_SEQ"]) + "_"
    #             key += row["DISUSE_FLAG"]
    #         else:
    #             key = row["EXECUTION_NO"] + "_"
    #             key += row["OPERATION_ID"] + "_"
    #             key += row["MOVEMENT_ID"] + "_"
    #             key += row["SYSTEM_ID"] + "_"
    #             key += row["MVMT_VAR_LINK_ID"] + "_"
    #             key += row["COL_SEQ_COMBINATION_ID"] + "_"
    #             key += str(row["ASSIGN_SEQ"]) + "_"
    #             key += row["DISUSE_FLAG"]

    #         if row["COL_SEQ_COMBINATION_ID"] is None or len(row["COL_SEQ_COMBINATION_ID"]) == 0:
    #             in_VarsAssignRecodes[key] = row
    #         else:
    #             in_ArryVarsAssignRecodes[key] = row

    #     return True, in_VarsAssignRecodes, in_ArryVarsAssignRecodes

    # def checkVerticalMenuVarsAssignData(self, lv_tableVerticalMenuList, inout_varsAssList):
    #     """
    #     縦メニューでまとまり全てNULLの場合、代入値管理への登録・更新を対象外とする

    #     Arguments:
    #         lv_tableVerticalMenuList: 縦メニューテーブルのカラム情報配列

    #     Returns:
    #         is success:(bool)
    #         defvarsList: 抽出した変数
    #     """

    #     chk_vertical_col = {}
    #     chk_vertical_val = {}

    #     for tbl_name, col_list in lv_tableVerticalMenuList.items():
    #         for col_name in col_list.values():
    #             for index, vars_ass_list in inout_varsAssList.items():
    #                 # 縦メニュー以外はチェック対象外
    #                 if not tbl_name == vars_ass_list['TABLE_NAME']:
    #                     continue

    #                 if not tbl_name == vars_ass_list['COL_NAME']:
    #                     continue

    #                 # テーブル名とROW_IDをキーとした代入値チェック用の辞書を作成
    #                 if tbl_name not in chk_vertical_val:
    #                     chk_vertical_val[tbl_name] = {}

    #                 chk_vertical_val[tbl_name] = {}
    #                 chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']] = {}
    #                 if vars_ass_list['COL_ROW_ID'] not in chk_vertical_val[tbl_name]:
    #                     chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['CHK_START'] = False
    #                     chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['NULL_VAL'] = {}

    #                 # リピート開始カラムをチェック
    #                 if col_name == vars_ass_list['START_COL_NAME']:
    #                     chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['CHK_START'] = True
    #                     if tbl_name not in chk_vertical_col:
    #                         chk_vertical_val[tbl_name]['COL_CNT'] = 0
    #                         chk_vertical_val[tbl_name]['REPEAT_CNT'] = 0
    #                         chk_vertical_val[tbl_name]['COL_CNT_MAX'] = vars_ass_list['COL_CNT']
    #                         chk_vertical_val[tbl_name]['REPEAT_CNT_MAX'] = vars_ass_list['REPEAT_CNT']

    #                 # リピート開始前の場合は次のカラムへ以降
    #                 if chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['CHK_START'] == 0:
    #                     continue

    #                 # 具体値が NULL の場合は、代入値管理登録データのインデックスを保持
    #                 if vars_ass_list['VARS_ENTRY'] == "":
    #                     chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['NULL_VAL'] = {}
    #                     chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['NULL_VAL']['INDEX'] = index

    #             # リピート開始前の場合は次のカラムへ以降
    #             if tbl_name not in chk_vertical_col:
    #                 continue

    #             # チェック完了済みカラムをカウントアップ
    #             chk_vertical_col[tbl_name]['COL_CNT'] += 1

    #             # まとまり単位のチェック完了時の場合
    #             if chk_vertical_col[tbl_name]['COL_CNT'] >= chk_vertical_col[tbl_name]['COL_CNT_MAX']:
    #                 # まとまり単位の具体値が全て NULL の場合は代入値管理への登録対象外とする
    #                 if tbl_name in chk_vertical_val:
    #                     for row_id, vertical_val_info in chk_vertical_val[tbl_name]:
    #                         if len(vertical_val_info['NULL_VAL']) >= chk_vertical_col[tbl_name]['COL_CNT_MAX']:
    #                             for index in vertical_val_info['NULL_VAL'].values():
    #                                 inout_varsAssList[index]['STATUS'] = False
    #                         # 保持している代入値管理登録データのインデックスをリセット
    #                         del chk_vertical_val[tbl_name][row_id]['NULL_VAL']
    #                         chk_vertical_val[tbl_name][row_id]['NULL_VAL'] = {}

    #                 # リピート数をカウントアップ
    #                 chk_vertical_col[tbl_name]['REPEAT_CNT'] += 1

    #                 # チェック完了済みカラムのカウントをリセット
    #                 chk_vertical_col[tbl_name]['COL_CNT'] = 0

    #             # リピート終了済みの場合は以降のカラムはチェックしない
    #             if chk_vertical_col[tbl_name]['REPEAT_CNT'] >= chk_vertical_col[tbl_name]['REPEAT_CNT_MAX']:
    #                 break

    #     return inout_varsAssList

    def addStg1StdListVarsAssign(self, in_varsAssignList, execution_no, tgt_row, table, menu_id, var_extractor, WS_DB):
        """
        代入値管理（一般変数・複数具体値変数）を更新する。

        Arguments:
            in_varsAssignList: 代入値管理更新情報配列
            execution_no
            tgt_row
            table: 代入値管理テーブル
            menu_id
            var_extractor: WrappedStringReplaceAdminインスタンス
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
        """
        # 登録する情報設定
        tgt_row['EXECUTION_NO'] = execution_no
        tgt_row['OPERATION_ID'] = in_varsAssignList['OPERATION_ID']
        tgt_row['MOVEMENT_ID'] = in_varsAssignList['MOVEMENT_ID']
        tgt_row['SYSTEM_ID'] = in_varsAssignList['SYSTEM_ID']
        tgt_row['MVMT_VAR_LINK_ID'] = in_varsAssignList['MVMT_VAR_LINK_ID']
        if 'COL_SEQ_COMBINATION_ID' in tgt_row:
            if in_varsAssignList['COL_SEQ_COMBINATION_ID'] is not None and not in_varsAssignList['COL_SEQ_COMBINATION_ID'] == "":
                tgt_row['COL_SEQ_COMBINATION_ID'] = in_varsAssignList['COL_SEQ_COMBINATION_ID']
        tgt_row['SENSITIVE_FLAG'] = in_varsAssignList['SENSITIVE_FLAG']
        tgt_row['ASSIGN_SEQ'] = in_varsAssignList['ASSIGN_SEQ']

        tgt_row['DISUSE_FLAG'] = "0"
        # tgt_row['LAST_UPDATE_TIMESTAMP']
        tgt_row['LAST_UPDATE_USER'] = g.USER_ID

        tgt_row['VARS_ENTRY'] = in_varsAssignList['VARS_ENTRY']

        # ファイル有無
        org_fil_path = in_varsAssignList['COL_FILEUPLOAD_PATH']
        if org_fil_path:
            tgt_row['VARS_ENTRY_FILE'] = in_varsAssignList['VARS_ENTRY']  # ファイル名
            tgt_row['VARS_ENTRY'] = ""
        else:
            tgt_row["VARS_ENTRY_FILE"] = ""

        # 具体値にテンプレート変数が記述されているか判定
        VARS_ENTRY_USE_TPFVARS = "0"
        if type(in_varsAssignList['VARS_ENTRY']) is str:
            vars_line_array = []
            # var_extractor = WrappedStringReplaceAdmin(WS_DB)
            is_success, vars_line_array = var_extractor.SimpleFillterVerSearch("TPF_", in_varsAssignList['VARS_ENTRY'], vars_line_array, [], [])
            if len(vars_line_array) == 1:
                # テンプレート変数が記述されていることを記録
                VARS_ENTRY_USE_TPFVARS = "1"
        tgt_row["VARS_ENTRY_USE_TPFVARS"] = VARS_ENTRY_USE_TPFVARS

        ret = self.exec_maintenance(WS_DB, table, 'ASSIGN_ID', tgt_row, org_fil_path, menu_id)

        if ret[0] is False:
            raise AppException("499-00701", [ret[1]], [ret[1]])

        return True

    def addStg1ArrayVarsAssign(self, in_varsAssignList, execution_no, tgt_row, table, menu_id, var_extractor, WS_DB):
        """
        代入値管理（多次元配列変数）の廃止レコードの復活またき新規レコード追加

        Arguments:
            in_varsAssignList: 代入値管理更新情報配列
            execution_no
            tgt_row
            table: 代入値管理テーブル
            menu_id
            var_extractor: WrappedStringReplaceAdminインスタンス
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
        """
        # 登録する情報設定
        tgt_row['EXECUTION_NO'] = execution_no
        tgt_row['OPERATION_ID'] = in_varsAssignList['OPERATION_ID']
        tgt_row['MOVEMENT_ID'] = in_varsAssignList['MOVEMENT_ID']
        tgt_row['SYSTEM_ID'] = in_varsAssignList['SYSTEM_ID']
        tgt_row['MVMT_VAR_LINK_ID'] = in_varsAssignList['MVMT_VAR_LINK_ID']
        if 'COL_SEQ_COMBINATION_ID' in tgt_row:
            if in_varsAssignList['COL_SEQ_COMBINATION_ID'] is not None and not in_varsAssignList['COL_SEQ_COMBINATION_ID'] == "":
                tgt_row['COL_SEQ_COMBINATION_ID'] = in_varsAssignList['COL_SEQ_COMBINATION_ID']
        tgt_row['SENSITIVE_FLAG'] = in_varsAssignList['SENSITIVE_FLAG']
        tgt_row['ASSIGN_SEQ'] = in_varsAssignList['ASSIGN_SEQ']

        tgt_row['DISUSE_FLAG'] = "0"
        # tgt_row['LAST_UPDATE_TIMESTAMP']
        tgt_row['LAST_UPDATE_USER'] = g.USER_ID

        tgt_row['VARS_ENTRY'] = in_varsAssignList['VARS_ENTRY']

        # ファイル有無
        org_fil_path = in_varsAssignList['COL_FILEUPLOAD_PATH']
        if org_fil_path:
            tgt_row['VARS_ENTRY_FILE'] = in_varsAssignList['VARS_ENTRY']  # ファイル名
            tgt_row['VARS_ENTRY'] = ""
        else:
            tgt_row["VARS_ENTRY_FILE"] = ""

        # 具体値にテンプレート変数が記述されているか判定
        VARS_ENTRY_USE_TPFVARS = "0"
        if type(in_varsAssignList['VARS_ENTRY']) is str:
            vars_line_array = []
            # var_extractor = WrappedStringReplaceAdmin(WS_DB)
            is_success, vars_line_array = var_extractor.SimpleFillterVerSearch("TPF_", in_varsAssignList['VARS_ENTRY'], vars_line_array, [], [])
            if len(vars_line_array) == 1:
                # テンプレート変数が記述されていることを記録
                VARS_ENTRY_USE_TPFVARS = "1"
        tgt_row["VARS_ENTRY_USE_TPFVARS"] = VARS_ENTRY_USE_TPFVARS

        ret = self.exec_maintenance(WS_DB, table, 'ASSIGN_ID', tgt_row, org_fil_path, menu_id)

        if ret[0] is False:
            raise AppException("499-00701", [ret[1]], [ret[1]])

        return True

    def getIFInfoDB(self, WS_DB):
        """
        インターフェース情報を取得する。

        Arguments:
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
            ina_if_info: インターフェース情報
            err_code: メッセージコード
        """

        where = "WHERE DISUSE_FLAG = '0'"
        data_list = WS_DB.table_select("T_ANSC_IF_INFO", where, [])

        ina_if_info = None
        err_code = ""

        if data_list is None:
            err_code = "MSG-10176"
            return False, ina_if_info, err_code

        for data in data_list:
            ina_if_info = data

        return True, ina_if_info, err_code

    def getCMDBdata(self, in_tableNameToSqlList, in_tableNameToMenuIdList, in_tabColNameToValAssRowList, reg_operation_id, WS_DB, g_null_data_handling_def):
        """
        CMDB代入値紐付対象メニューから具体値を取得する。

        Arguments:
            in_tableNameToSqlList: CMDB代入値紐付メニュー毎のSELECT文配列
            in_tableNameToMenuIdList: テーブル名配列
            in_tabColNameToValAssRowList: カラム情報配列


            WS_DB: WorkspaceDBインスタンス

        Returns:
            ina_vars_ass_list: 一般変数・複数具体値変数用 代入値登録情報配列
            ina_array_vars_ass_list: 多次元変数配列変数用 代入値登録情報配列
        """

        load_table_count = 0
        load_table_cache_count = 0
        a = 0
        b = 0
        c = 0
        d = 0
        e = 0

        VariableColumnAry = {}
        VariableColumnAry['T_ANSC_TEMPLATE_FILE'] = {}
        VariableColumnAry['T_ANSC_TEMPLATE_FILE']['ANS_TEMPLATE_VARS_NAME'] = 0
        VariableColumnAry['T_ANSC_CONTENTS_FILE'] = {}
        VariableColumnAry['T_ANSC_CONTENTS_FILE']['CONTENTS_FILE_VARS_NAME'] = 0

        # オペ+作業+ホスト+変数の組合せの代入順序 重複確認用
        lv_varsAssChkList = {}
        # オペ+作業+ホスト+変数+メンバ変数の組合せの代入順序 重複確認用
        lv_arrayVarsAssChkList = {}

        # 一般変数・複数具体値変数用 代入値登録情報配列
        ina_vars_ass_list = []
        ina_vars_ass_list_append = ina_vars_ass_list.append
        # 多次元変数配列変数用 代入値登録情報配列
        ina_array_vars_ass_list = []
        ina_array_vars_ass_list_append = ina_array_vars_ass_list.append

        # 紐付メニューの入力用メニューのメニューID取得用の辞書を作成
        in_MenuIdList = set(list(in_tableNameToMenuIdList.values()))
        upload_menu_id_map = {}
        sql = """SELECT \
                    TBL_A.MENU_ID AS MENU_ID, \
                    TBL_A.MENU_NAME_REST, \
                    TBL_B.MENU_ID AS OUT_MENU_ID, \
                    TBL_B.OUT_MENU_NAME_REST \
                FROM \
                    T_COMN_MENU TBL_A \
                INNER JOIN \
                    (SELECT \
                        MENU_ID, \
                        CONCAT(MENU_NAME_REST, '_subst') AS OUT_MENU_NAME_REST \
                    FROM \
                        T_COMN_MENU \
                    WHERE \
                        DISUSE_FLAG = '0' ) AS TBL_B \
                ON \
                    TBL_B.OUT_MENU_NAME_REST = TBL_A.MENU_NAME_REST \
                WHERE \
                    TBL_A.DISUSE_FLAG = '0'"""
        data_list = WS_DB.sql_execute(sql, [])
        for data in data_list:
            if data['MENU_ID'] not in in_MenuIdList:
                continue
            upload_menu_id_map[data['MENU_ID']] = data['OUT_MENU_ID']
        data_list = []

        col_name_data_json = 'DATA_JSON'  # 2系からデータの持ち方変わった

        host_ary = []
        dict_objmenu = {} # パラシ情報（load_tableの取得結果のキャッシュ）
        for table_name, sql in in_tableNameToSqlList.items():
            # トレースメッセージ
            traceMsg = g.appmsg.get_api_message("MSG-10806", [in_tableNameToMenuIdList[table_name]])
            frame = inspect.currentframe().f_back
            g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)

            if reg_operation_id is not None:
                sql += " AND OPERATION_ID = %s \n "
                data_list = WS_DB.sql_execute(sql, [AnscConst.DF_ITA_LOCAL_HOST_CNT, AnscConst.DF_ITA_LOCAL_PKEY, reg_operation_id])
            else:
                data_list = WS_DB.sql_execute(sql, [AnscConst.DF_ITA_LOCAL_HOST_CNT, AnscConst.DF_ITA_LOCAL_PKEY])

            # FETCH行数を取得
            if len(data_list) == 0:
                msgstr = g.appmsg.get_api_message("MSG-10368", [in_tableNameToMenuIdList[table_name]])
                frame = inspect.currentframe().f_back
                g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                # 次のテーブルへ
                continue

            tmp_ary_data = {}
            index = 0
            for row in data_list:
                # 代入値紐付メニューに登録されているオペレーションIDを確認
                if row['OPERATION_ID'] is None or len(row['OPERATION_ID']) == 0:
                    # オペレーションID未登録
                    msgstr = g.appmsg.get_api_message("MSG-10360", [in_tableNameToMenuIdList[table_name], row[AnscConst.DF_ITA_LOCAL_PKEY]])
                    frame = inspect.currentframe().f_back
                    g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)

                    # 次のデータへ
                    continue

                operation_id = row['OPERATION_ID']

                # 代入値紐付メニューに登録されているホストIDの紐付確認
                if row[AnscConst.DF_ITA_LOCAL_HOST_CNT] == 0:
                    # ホストIDの紐付不正
                    msgstr = g.appmsg.get_api_message("MSG-10359", [in_tableNameToMenuIdList[table_name], row[AnscConst.DF_ITA_LOCAL_PKEY], row['HOST_ID']])
                    frame = inspect.currentframe().f_back
                    g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)

                    # 次のデータへ
                    continue

                # 代入値紐付メニューに登録されているホストIDを確認
                if row['HOST_ID'] is None or len(row['HOST_ID']) == 0:
                    msgstr = g.appmsg.get_api_message("MSG-10361", [in_tableNameToMenuIdList[table_name], row[AnscConst.DF_ITA_LOCAL_PKEY]])
                    frame = inspect.currentframe().f_back
                    g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)

                    # 次のデータへ
                    continue

                # 代入値自動登録設定に登録されている変数に対応する具体値を取得する
                # パラメータシート側の項番取得
                col_row_id = row[AnscConst.DF_ITA_LOCAL_PKEY]

                if table_name not in tmp_ary_data:
                    tmp_ary_data[table_name] = {}
                tmp_ary_data[table_name][index] = row
                index += 1

                if row['HOST_ID'] not in host_ary:
                    host_ary.append(row['HOST_ID'])
            # 初期化
            data_list = []

            for tmp_table_name, tmp_value in tmp_ary_data.items():
                registered_host_ary = []
                for row in tmp_value.values():
                    for table_name, ary_col_data in in_tabColNameToValAssRowList.items():
                        # パラメータシートごとの処理
                        for col_data in ary_col_data[col_name_data_json].values():
                            # 代入値自動登録のレコードごとの処理
                            col_val = ""
                            exec_flag = False
                            menu_name_rest = col_data["MENU_NAME_REST"]
                            host_id = row['HOST_ID']

                            # パラメータシートから値を取得
                            if menu_name_rest not in dict_objmenu:
                                load_table_count += 1
                                obj_load_table = load_table.loadTable(WS_DB, menu_name_rest)
                                tmp_result = self.rest_filter(WS_DB, obj_load_table)
                                dict_objmenu[menu_name_rest] = tmp_result
                            else:
                                load_table_cache_count += 1
                                # キャッシュあり
                                tmp_result = dict_objmenu[menu_name_rest]

                            if tmp_table_name == table_name:
                                # 縦メニューの場合
                                if row["INPUT_ORDER"] is not None and not row["INPUT_ORDER"] == "":
                                    if row["INPUT_ORDER"] == col_data["COLUMN_ASSIGN_SEQ"]:
                                        for parameter in tmp_result:
                                            if row[AnscConst.DF_ITA_LOCAL_PKEY] == parameter["uuid"] \
                                                and row["INPUT_ORDER"] == parameter["input_order"]:
                                                # 項目なしは対象外
                                                if col_data['COL_GROUP_ID'] is None:
                                                    ina_vars_ass_list_append({'TABLE_NAME': table_name,
                                                                            'OPERATION_ID': operation_id,
                                                                            'MOVEMENT_ID': col_data['MOVEMENT_ID'],
                                                                            'SYSTEM_ID': host_id,
                                                                            'VARS_ENTRY': None,
                                                                            'MVMT_VAR_LINK_ID': None,
                                                                            'STATUS': 'skip'})
                                                    a += 1
                                                    continue
                                                else:
                                                    # 項目が削除されていないか確認
                                                    exit_flag = False
                                                    if col_data['COLUMN_NAME_REST'] in parameter:
                                                        col_val = parameter[col_data['COLUMN_NAME_REST']]
                                                    else:
                                                        exit_flag = True
                                                        continue

                                                # TPF/CPF変数カラム判定
                                                if col_data['REF_TABLE_NAME'] in VariableColumnAry and col_data['REF_COL_NAME'] in VariableColumnAry[col_data['REF_TABLE_NAME']]:
                                                    if 'ID変換失敗' not in col_val and 'Failed to exchange ID' not in col_val:
                                                        col_val = "'{{ " + col_val + " }}'"
                                                    else:
                                                        continue
                                        # 項目が削除されていないか確認
                                        if exit_flag is True:
                                            continue

                                        exec_flag = True
                                elif col_data["COLUMN_ASSIGN_SEQ"] is None:
                                    for parameter in tmp_result:
                                        if parameter["HOST_ID"] == row['HOST_ID'] and parameter["OPERATION_ID"] == row['OPERATION_ID']:
                                            break
                                        else:
                                            parameter = {}

                                    # 項目なしは対象外
                                    if col_data['COL_GROUP_ID'] is None:
                                        ina_vars_ass_list_append({'TABLE_NAME': table_name,
                                                                'OPERATION_ID': operation_id,
                                                                'MOVEMENT_ID': col_data['MOVEMENT_ID'],
                                                                'SYSTEM_ID': host_id,
                                                                'VARS_ENTRY': None,
                                                                'MVMT_VAR_LINK_ID': None,
                                                                'STATUS': 'skip'})
                                        b += 1
                                        continue
                                    else:
                                        # 項目が削除されていないか確認
                                        if col_data['COLUMN_NAME_REST'] in parameter:
                                            col_val = parameter[col_data['COLUMN_NAME_REST']]
                                        else:
                                            continue

                                    # TPF/CPF変数カラム判定
                                    if col_data['REF_TABLE_NAME'] in VariableColumnAry \
                                        and col_data['REF_COL_NAME'] in VariableColumnAry[col_data['REF_TABLE_NAME']] \
                                            and col_val is not None:
                                        if 'ID変換失敗' not in col_val and 'Failed to exchange ID' not in col_val:
                                            col_val = "'{{ " + col_val + " }}'"
                                        else:
                                            continue

                                    exec_flag = True

                            col_class = self.getFromColumnClassMaster(col_data['COLUMN_CLASS'])
                            col_name_rest = col_data['COLUMN_NAME_REST']
                            col_filepath = ""
                            if col_data['COL_TYPE'] == AnscConst.DF_COL_TYPE_VAL and (col_data['COLUMN_CLASS'] == "9" or col_data['COLUMN_CLASS'] == "20"):
                                # メニューID取得
                                upload_menu_id = upload_menu_id_map[in_tableNameToMenuIdList[table_name]] if in_tableNameToMenuIdList[table_name] in upload_menu_id_map else ""

                                if col_val is not None and not col_val == "":
                                    storage_path = os.environ.get('STORAGEPATH') + g.get('ORGANIZATION_ID') + "/" + g.get('WORKSPACE_ID')
                                    col_filepath = storage_path + "/uploadfiles/" + upload_menu_id + "/" + col_name_rest + "/" + row[AnscConst.DF_ITA_LOCAL_PKEY]
                                    if not os.path.exists(col_filepath):
                                        msgstr = g.appmsg.get_api_message("MSG-10166", [table_name, col_name_rest, col_row_id, col_filepath])
                                        frame = inspect.currentframe().f_back
                                        g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                                        # 次のデータへ
                                        continue

                                    col_filepath = col_filepath + "/" + col_val

                            # 代入値管理の登録に必要な情報を生成
                            if exec_flag is True:
                                c += 1
                                ina_vars_ass, ina_array_vars_ass = self.makeVarsAssignData(table_name,
                                                    col_name_data_json,
                                                    col_val,
                                                    col_row_id,
                                                    col_class,
                                                    col_filepath,
                                                    col_data['NULL_DATA_HANDLING_FLG'],
                                                    operation_id,
                                                    host_id,
                                                    col_data,
                                                    lv_varsAssChkList,
                                                    lv_arrayVarsAssChkList,
                                                    in_tableNameToMenuIdList[table_name],
                                                    row[AnscConst.DF_ITA_LOCAL_PKEY],
                                                    g_null_data_handling_def
                                                    )

                                # NULL連携無効で処理対象外になった場合は追加しない
                                if not ina_vars_ass is False:
                                    if ina_vars_ass is not None:
                                        ina_vars_ass_list_append(ina_vars_ass)
                                    if host_id not in registered_host_ary:
                                        registered_host_ary.append(host_id)
                                if not ina_array_vars_ass is False and ina_array_vars_ass is not None:
                                    ina_array_vars_ass_list_append(ina_array_vars_ass)

                    if host_ary == len(registered_host_ary):
                        break

            # 縦メニューの代入順序に対応したレコードが紐付対象メニューに登録されているか確認
            if 'col_name' in locals():
                for col_data in in_tabColNameToValAssRowList[table_name][col_name_data_json].values():
                    chk_flag = False
                    for row in data_list:
                        if col_data["COLUMN_ASSIGN_SEQ"] is not None:
                            if col_data["COLUMN_ASSIGN_SEQ"] == row["INPUT_ORDER"]:
                                chk_flag = True
                        else:
                            chk_flag = True

                    if chk_flag is False:
                        msgstr = g.appmsg.get_api_message("MSG-10902", [col_data["COLUMN_ID"]])
                        frame = inspect.currentframe().f_back
                        g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)

        # g.applogger.debug(f"{load_table_count=}")
        # g.applogger.debug(f"{load_table_cache_count=}")
        # g.applogger.debug(f"{a=}")
        # g.applogger.debug(f"{b=}")
        # g.applogger.debug(f"{c=}")
        # g.applogger.debug(f"{d=}")
        # g.applogger.debug(f"{e=}")
        # 代入値
        g.applogger.debug("ina_vars_ass_list={}".format(len(ina_vars_ass_list)))
        g.applogger.debug("ina_array_vars_ass_list={}".format(len(ina_array_vars_ass_list)))
        # オペ+作業+ホスト+変数の組合せの代入順序 重複確認用
        g.applogger.debug("lv_varsAssChkList={}".format(len(lv_varsAssChkList)))
        g.applogger.debug("lv_arrayVarsAssChkList={}".format(len(lv_arrayVarsAssChkList)))

        # オブジェクト解放
        del dict_objmenu
        del lv_varsAssChkList
        del lv_arrayVarsAssChkList

        return ina_vars_ass_list, ina_array_vars_ass_list

    def makeVarsAssignData(self,
                            in_table_name,
                            in_col_name,
                            in_col_val,
                            in_col_row_id,
                            in_col_class,
                            in_col_filepath,
                            in_null_data_handling_flg,
                            in_operation_id,
                            in_host_id,
                            in_col_list,
                            ina_vars_ass_chk_list,
                            ina_array_vars_ass_chk_list,
                            in_menu_id,
                            in_row_id,
                            g_null_data_handling_def
                            ):
        """
        CMDB代入値紐付対象メニューの情報から代入値管理に登録する情報を生成

        Arguments:
            in_table_name: テーブル名
            in_col_name: カラム名 'DATA_JSON'
            in_col_val: カラムの具体値
            in_col_row_id: パラメータシートの項番
            in_col_class: カラムのクラス名
            in_col_filepath: パターンID
            in_vars_link_id: 変数ID
            in_col_seq_combination_id: メンバー変数ID
            in_vars_assign_seq: 代入順序
            in_col_val: 具体値
            in_col_row_id: パラメータシートの項番
            in_col_class: カラムのクラス名
            in_col_filepath: FileUpLoadColumnのファイルパス
            in_sensitive_flg: sensitive設定
            ina_vars_ass_chk_list: 一般変数・複数具体値変数用 代入順序重複チェック配列
            ina_array_vars_ass_chk_list: 多次元変数配列変数用 列順序重複チェック配列
            in_menu_id: 紐付メニューID
            in_column_id: 代入値自動登録設定
            keyValueType: Value/Key
            in_row_id: 紐付テーブル主キー値
        Retruns:

        """

        col_name = in_col_list['COLUMN_NAME_JA'] if g.LANGUAGE == 'ja' else in_col_list['COLUMN_NAME_EN']

        # カラムタイプを判定
        if in_col_list['COL_TYPE'] == AnscConst.DF_COL_TYPE_VAL:
            # Value型カラムの場合
            # 具体値が空でも代入値管理NULLデータ連携が有効か判定する
            if in_col_val is None \
                and not self.getNullDataHandlingID(in_null_data_handling_flg, g_null_data_handling_def) == '1':
                msgstr = g.appmsg.get_api_message("MSG-10375", [in_menu_id, in_row_id, col_name])
                frame = inspect.currentframe().f_back
                g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)

                return False, False

            # checkAndCreateVarsAssignDataの戻りは判定しない。
            ina_vars_ass, ina_array_vars_ass = self.checkAndCreateVarsAssignData(in_table_name,
                                            in_col_name,
                                            in_col_list['VAL_VAR_TYPE'],
                                            in_operation_id,
                                            in_host_id,
                                            in_col_list['MOVEMENT_ID'],
                                            in_col_list['MVMT_VAR_LINK_ID'],
                                            in_col_list['COL_SEQ_COMBINATION_ID'],
                                            in_col_list['ASSIGN_SEQ'],
                                            in_col_val,
                                            in_col_row_id,
                                            in_col_class,
                                            in_col_filepath,
                                            in_col_list['VALUE_SENSITIVE_FLAG'],
                                            ina_vars_ass_chk_list,
                                            ina_array_vars_ass_chk_list,
                                            in_col_list['COLUMN_ID'],
                                            "Value"
                                            )

        elif in_col_list['COL_TYPE'] == AnscConst.DF_COL_TYPE_KEY:
            # 具体値が空白か判定
            if in_col_val is None:
                msgstr = g.appmsg.get_api_message("MSG-10377", [in_menu_id, in_row_id, col_name])
                frame = inspect.currentframe().f_back
                g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)

                return False, False

            # checkAndCreateVarsAssignDataの戻りは判定しない。
            ina_vars_ass, ina_array_vars_ass = self.checkAndCreateVarsAssignData(
                                            in_table_name,
                                            in_col_name,
                                            in_col_list['KEY_VAR_TYPE'],
                                            in_operation_id,
                                            in_host_id,
                                            in_col_list['MOVEMENT_ID'],
                                            in_col_list['MVMT_VAR_LINK_ID'],
                                            in_col_list['COL_SEQ_COMBINATION_ID'],
                                            in_col_list['ASSIGN_SEQ'],
                                            col_name,
                                            in_col_row_id,
                                            in_col_class,
                                            in_col_filepath,
                                            in_col_list['KEY_SENSITIVE_FLAG'],
                                            ina_vars_ass_chk_list,
                                            ina_array_vars_ass_chk_list,
                                            in_col_list['COLUMN_ID'],
                                            "Key"
                                            )

        return ina_vars_ass, ina_array_vars_ass

    def getFromColumnClassMaster(self, column_class, WS_DB=None):
        """
        カラムクラス名のマスタから名前をひく

        Arguments:
            column_class
            WS_DB: WorkspaceDBインスタンス

        """
        if WS_DB is None:
        # 取得済みとみなす
            return self.ColumnClassMaster_IDMap[column_class]

        # マスタがなければ保持しておく
        data_dict = {}

        sql = "SELECT COLUMN_CLASS_ID, COLUMN_CLASS_NAME"
        sql += " FROM T_COMN_COLUMN_CLASS"
        sql += " WHERE DISUSE_FLAG = '0'"

        data_list = WS_DB.sql_execute(sql)

        for data in data_list:
            data_dict[data['COLUMN_CLASS_ID']] = data['COLUMN_CLASS_NAME']

        self.ColumnClassMaster_IDMap = data_dict

    def getNullDataHandlingID(self, in_null_data_handling_flg, g_null_data_handling_def):
        """
        パラメータシートの具体値がNULLの場合でも代入値管理ら登録するかを判定

        Arguments:
            in_null_data_handling_flg: 代入値自動登録設定のNULL登録フラグ

        Returns:
            is success:(bool)
        """

        # 代入値自動登録設定のNULL登録フラグ判定
        if in_null_data_handling_flg == '1':
            return '1'
        elif in_null_data_handling_flg == '0':
            return '2'
        else:
            # インターフェース情報のNULL登録フラグ判定
            if g_null_data_handling_def == '1':
                return '1'
            elif g_null_data_handling_def == '0':
                return '2'

    def checkAndCreateVarsAssignData(self,
                                    in_table_name,
                                    in_col_name,
                                    in_vars_attr,
                                    in_operation_id,
                                    in_host_id,
                                    in_patten_id,
                                    in_vars_link_id,
                                    in_col_seq_combination_id,
                                    in_vars_assign_seq,
                                    in_col_val,
                                    in_col_row_id,
                                    in_col_class,
                                    in_col_filepath,
                                    in_sensitive_flg,
                                    ina_vars_ass_chk_list,
                                    ina_array_vars_ass_chk_list,
                                    in_column_id,
                                    keyValueType
                                    ):
        """
        CMDB代入値紐付対象メニューの情報から代入値管理に登録する情報を生成

        Arguments:
            in_table_name: テーブル名
            in_col_name: カラム名
            in_vars_attr: 変数区分 (1:一般変数, 2:複数具体値, 3:多次元変数)
            in_operation_id: オペレーションID
            in_host_id: ホスト名
            in_patten_id: パターンID
            in_vars_link_id: 変数ID
            in_col_seq_combination_id: メンバー変数ID
            in_vars_assign_seq: 代入順序
            in_col_val: 具体値
            in_col_row_id: パラメータシートの項番
            in_col_class: カラムのクラス名
            in_col_filepath: FileUpLoadColumnのファイルパス
            in_sensitive_flg: sensitive設定
            ina_vars_ass_chk_list: 一般変数・複数具体値変数用 代入順序重複チェック配列
            ina_array_vars_ass_chk_list: 多次元変数配列変数用 列順序重複チェック配列
            in_column_id: 代入値自動登録設定
            keyValueType: Value/Key

        Returns:

        """

        chk_status = False
        chk_flg = True

        ina_vars_ass = None
        ina_array_vars_ass = None

        # 変数のタイプを判定
        if in_vars_attr == AnscConst.GC_VARS_ATTR_STD or in_vars_attr == AnscConst.GC_VARS_ATTR_LIST:
            # 一般変数・複数具体値
            # オペ+作業+ホスト+変数の組合せで代入順序が重複していないか判定
            chk_key = "{}__{}__{}__{}__{}".format(in_vars_link_id, in_patten_id, in_host_id, in_operation_id, in_vars_assign_seq)
            if chk_key in ina_vars_ass_chk_list:
                # 既に登録されている
                chk_flg = False

                dup_column_id = ina_vars_ass_chk_list[chk_key]
                msgstr = g.appmsg.get_api_message("MSG-10369", [dup_column_id, in_column_id, in_column_id, in_operation_id, in_host_id, keyValueType])
                frame = inspect.currentframe().f_back
                g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)

            if chk_flg is True:
                chk_status = True
                # オペ+作業+ホスト+変数+メンバ変数の組合せの代入順序退避
                key = "{}__{}__{}__{}__{}".format(in_vars_link_id, in_patten_id, in_host_id, in_operation_id, in_vars_assign_seq)
                ina_vars_ass_chk_list[key] = in_column_id
            # 代入値管理の登録に必要な情報退避
            ina_vars_ass = {'TABLE_NAME': in_table_name,
                                'COL_NAME': in_col_name,
                                'COL_ROW_ID': in_col_row_id,
                                'COL_CLASS': in_col_class,
                                'COL_FILEUPLOAD_PATH': in_col_filepath,
                                'REG_TYPE': keyValueType,
                                'OPERATION_ID': in_operation_id,
                                'MOVEMENT_ID': in_patten_id,
                                'SYSTEM_ID': in_host_id,
                                'MVMT_VAR_LINK_ID': in_vars_link_id,
                                'ASSIGN_SEQ': in_vars_assign_seq,
                                'VARS_ENTRY': in_col_val,
                                'COL_SEQ_COMBINATION_ID': in_col_seq_combination_id,
                                'SENSITIVE_FLAG': in_sensitive_flg,
                                'VAR_TYPE': in_vars_attr,
                                'STATUS': chk_status}

        elif in_vars_attr == AnscConst.GC_VARS_ATTR_M_ARRAY:
            # 多次元変数
            # オペ+作業+ホスト+変数+メンバ変数の組合せで代入順序が重複していないか判定
            chk_key = "{}__{}__{}__{}__{}__{}".format(in_vars_link_id, in_patten_id, in_host_id, in_operation_id, in_col_seq_combination_id, in_vars_assign_seq)
            if chk_key in ina_array_vars_ass_chk_list:
                # 既に登録されている
                chk_flg = False

                dup_column_id = ina_array_vars_ass_chk_list[chk_key]
                msgstr = g.appmsg.get_api_message("MSG-10369", [dup_column_id, in_column_id, in_column_id, in_operation_id, in_host_id, keyValueType])
                frame = inspect.currentframe().f_back
                g.applogger.info(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)

            if chk_flg is True:
                chk_status = True
                # オペ+作業+ホスト+変数+メンバ変数の組合せの代入順序退避
                key = "{}__{}__{}__{}__{}__{}".format(in_vars_link_id, in_patten_id, in_host_id, in_operation_id, in_col_seq_combination_id, in_vars_assign_seq)
                ina_array_vars_ass_chk_list[key] = in_column_id

            # 代入値管理の登録に必要な情報退避
            ina_array_vars_ass = {'TABLE_NAME': in_table_name,
                                'COL_NAME': in_col_name,
                                'COL_ROW_ID': in_col_row_id,
                                'COL_CLASS': in_col_class,
                                'COL_FILEUPLOAD_PATH': in_col_filepath,
                                'REG_TYPE': keyValueType,
                                'OPERATION_ID': in_operation_id,
                                'MOVEMENT_ID': in_patten_id,
                                'SYSTEM_ID': in_host_id,
                                'MVMT_VAR_LINK_ID': in_vars_link_id,
                                'ASSIGN_SEQ': in_vars_assign_seq,
                                'VARS_ENTRY': in_col_val,
                                'COL_SEQ_COMBINATION_ID': in_col_seq_combination_id,
                                'SENSITIVE_FLAG': in_sensitive_flg,
                                'VAR_TYPE': in_vars_attr,
                                'STATUS': chk_status}

        return ina_vars_ass, ina_array_vars_ass

    def read_val_assign(self, in_driver_name, WS_DB, movement_id = None):
        """
        代入値自動登録設定からカラム情報を取得する。

        Arguments:
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
            inout_tableNameToMenuIdList: テーブル名配列
            inout_tabColNameToValAssRowList: カラム情報配列
            inout_tableNameToPKeyNameList: テーブル主キー名配列
        """

        global lv_val_assign_tbl
        global lv_pattern_link_tbl
        global lv_array_member_tbl
        global lv_member_col_comb_tbl
        global lv_ptn_vars_link_tbl

        inout_tableNameToPKeyNameList = {}

        sql = " SELECT                                                            \n"
        sql += "   TBL_A.COLUMN_ID                                             ,  \n"
        sql += "   TBL_A.MENU_ID                                               ,  \n"
        sql += "   TBL_D.MENU_NAME_REST                                        ,  \n"
        sql += "   TBL_C.TABLE_NAME                                            ,  \n"
        sql += "   TBL_A.COLUMN_LIST_ID                                        ,  \n"
        sql += "   TBL_B.COL_NAME                                              ,  \n"
        sql += "   TBL_B.COLUMN_NAME_JA                                        ,  \n"
        sql += "   TBL_B.COLUMN_NAME_EN                                        ,  \n"
        sql += "   TBL_B.COLUMN_NAME_REST                                      ,  \n"
        sql += "   TBL_B.COL_GROUP_ID                                          ,  \n"
        sql += "   TBL_B.REF_TABLE_NAME                                        ,  \n"
        sql += "   TBL_B.REF_PKEY_NAME                                         ,  \n"
        sql += "   TBL_B.REF_COL_NAME                                          ,  \n"
        sql += "   TBL_B.COLUMN_CLASS                                          ,  \n"
        sql += "   TBL_B.AUTOREG_HIDE_ITEM                                     ,  \n"
        sql += "   TBL_B.AUTOREG_ONLY_ITEM                                     ,  \n"
        sql += "   TBL_B.DISUSE_FLAG  AS COL_DISUSE_FLAG                       ,  \n"
        sql += "   TBL_A.COL_TYPE                                              ,  \n"
        sql += "   TBL_A.COLUMN_ASSIGN_SEQ                                     ,  \n"
        sql += "   TBL_A.DISUSE_FLAG                                           ,  \n"
        sql += "   TBL_E.VARS_NAME                                             ,  \n"
        if in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            sql += "   TBL_E.VARS_ATTRIBUTE_01                                 ,  \n"
        elif in_driver_name == AnscConst.DF_LEGACY_DRIVER_ID or in_driver_name == AnscConst.DF_PIONEER_DRIVER_ID:
            # Legacy/Pioneerには必要ない
            sql += "   NULL AS VARS_ATTRIBUTE_01                               ,  \n"
            sql += "   NULL AS COL_SEQ_COMBINATION_ID                          ,  \n"
            sql += "   NULL AS VAL_COL_COMBINATION_MEMBER_ALIAS                ,  \n"
            sql += "   NULL AS KEY_COL_COMBINATION_MEMBER_ALIAS                ,  \n"

        sql += "   TBL_A.NULL_DATA_HANDLING_FLG                                ,  \n"

        # 作業パターン詳細の登録確認
        sql += "   TBL_A.MOVEMENT_ID                                           ,  \n"
        sql += "   (                                                              \n"
        sql += "     SELECT                                                       \n"
        sql += "       COUNT(*)                                                   \n"
        sql += "     FROM                                                         \n"
        if in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            sql += lv_pattern_link_tbl + "                                        \n"
        elif in_driver_name == AnscConst.DF_LEGACY_DRIVER_ID:
            sql += lv_l_pattern_link_tbl + "                                      \n"
        elif in_driver_name == AnscConst.DF_PIONEER_DRIVER_ID:
            sql += lv_p_pattern_link_tbl + "                                      \n"
        sql += "     WHERE                                                        \n"
        sql += "       MOVEMENT_ID  = TBL_A.MOVEMENT_ID AND                       \n"
        sql += "       DISUSE_FLAG = '0'                                          \n"
        sql += "   ) AS PATTERN_CNT                                            ,  \n"
        sql += "                                                                  \n"

        # (Val)作業パターン変数紐付の登録確認
        sql += "   TBL_A.MVMT_VAR_LINK_ID                                      ,  \n"
        sql += "   (                                                              \n"
        sql += "     SELECT                                                       \n"
        sql += "       COUNT(*)                                                   \n"
        sql += "     FROM                                                         \n"
        if in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            sql += lv_ptn_vars_link_tbl + "                                       \n"
        elif in_driver_name == AnscConst.DF_LEGACY_DRIVER_ID:
            sql += lv_l_ptn_vars_link_tbl + "                                     \n"
        elif in_driver_name == AnscConst.DF_PIONEER_DRIVER_ID:
            sql += lv_p_ptn_vars_link_tbl + "                                     \n"
        sql += "     WHERE                                                        \n"
        sql += "       MOVEMENT_ID    = TBL_A.MOVEMENT_ID        AND              \n"
        sql += "       MVMT_VAR_LINK_ID  = TBL_A.MVMT_VAR_LINK_ID  AND            \n"
        sql += "       DISUSE_FLAG   = '0'                                        \n"
        sql += "   ) AS VAL_PTN_VARS_LINK_CNT                                  ,  \n"

        if in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            # (Val)多次元変数配列組合せ管理
            sql += "   TBL_A.COL_SEQ_COMBINATION_ID                                ,  \n"
            sql += "   (                                                              \n"
            sql += "     SELECT                                                       \n"
            sql += "       COL_COMBINATION_MEMBER_ALIAS                               \n"
            sql += "     FROM                                                         \n"
            sql += lv_member_col_comb_tbl + "                                         \n"
            sql += "     WHERE                                                        \n"
            sql += "       MVMT_VAR_LINK_ID IN (                                      \n"
            sql += "         SELECT                                                   \n"
            sql += "           MVMT_VAR_LINK_ID                                       \n"
            sql += "         FROM                                                     \n"
            sql += lv_ptn_vars_link_tbl + "                                           \n"
            sql += "         WHERE                                                    \n"
            sql += "           MOVEMENT_ID    = TBL_A.MOVEMENT_ID        AND          \n"
            sql += "           MVMT_VAR_LINK_ID  = TBL_A.MVMT_VAR_LINK_ID  AND        \n"
            sql += "           DISUSE_FLAG   = '0'                                    \n"
            sql += "         )                                                        \n"
            sql += "       AND                                                        \n"
            sql += "       COL_SEQ_COMBINATION_ID = TBL_A.COL_SEQ_COMBINATION_ID AND  \n"
            sql += "       DISUSE_FLAG = '0'                                          \n"
            sql += "   ) AS VAL_COL_COMBINATION_MEMBER_ALIAS                       ,  \n"

        # (Val)多次元変数メンバー管理
        sql += "   TBL_A.ASSIGN_SEQ                                                ,  \n"
        if in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            sql += "   (                                                              \n"
            sql += "     SELECT                                                       \n"
            sql += "       ASSIGN_SEQ_NEED                                            \n"
            sql += "     FROM                                                         \n"
            sql += lv_array_member_tbl + "                                            \n"
            sql += "     WHERE                                                        \n"
            sql += "       MVMT_VAR_LINK_ID IN (                                      \n"
            sql += "         SELECT                                                   \n"
            sql += "           MVMT_VAR_LINK_ID                                       \n"
            sql += "         FROM                                                     \n"
            sql += lv_ptn_vars_link_tbl + "                                           \n"
            sql += "         WHERE                                                    \n"
            sql += "           MOVEMENT_ID    = TBL_A.MOVEMENT_ID        AND          \n"
            sql += "           MVMT_VAR_LINK_ID  = TBL_A.MVMT_VAR_LINK_ID  AND        \n"
            sql += "           DISUSE_FLAG   = '0'                                    \n"
            sql += "         )                                                        \n"
            sql += "       AND                                                        \n"
            sql += "       ARRAY_MEMBER_ID IN (                                       \n"
            sql += "         SELECT                                                   \n"
            sql += "           ARRAY_MEMBER_ID                                        \n"
            sql += "         FROM                                                     \n"
            sql += lv_member_col_comb_tbl + "                                         \n"
            sql += "         WHERE                                                    \n"
            sql += "           COL_SEQ_COMBINATION_ID = TBL_A.COL_SEQ_COMBINATION_ID AND \n"
            sql += "           DISUSE_FLAG   = '0'                                    \n"
            sql += "         )                                                        \n"
            sql += "       AND                                                        \n"
            sql += "       DISUSE_FLAG = '0'                                          \n"
            sql += "   ) AS VAL_ASSIGN_SEQ_NEED                                    ,  \n"

        # (Key)作業パターン変数紐付の登録確認
        sql += "   TBL_A.MVMT_VAR_LINK_ID                                      ,  \n"
        sql += "   (                                                              \n"
        sql += "     SELECT                                                       \n"
        sql += "       COUNT(*)                                                   \n"
        sql += "     FROM                                                         \n"
        if in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            sql += lv_ptn_vars_link_tbl + "                                       \n"
        elif in_driver_name == AnscConst.DF_LEGACY_DRIVER_ID:
            sql += lv_l_ptn_vars_link_tbl + "                                     \n"
        elif in_driver_name == AnscConst.DF_PIONEER_DRIVER_ID:
            sql += lv_p_ptn_vars_link_tbl + "                                     \n"
        sql += "     WHERE                                                        \n"
        sql += "       MOVEMENT_ID    = TBL_A.MOVEMENT_ID        AND              \n"
        sql += "       MVMT_VAR_LINK_ID  = TBL_A.MVMT_VAR_LINK_ID  AND            \n"
        sql += "       DISUSE_FLAG   = '0'                                        \n"
        sql += "   ) AS KEY_PTN_VARS_LINK_CNT                                  ,  \n"

        if in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            # (Key)多次元変数配列組合せ管理
            sql += "   TBL_A.COL_SEQ_COMBINATION_ID                                ,  \n"
            sql += "   (                                                              \n"
            sql += "     SELECT                                                       \n"
            sql += "       COL_COMBINATION_MEMBER_ALIAS                               \n"
            sql += "     FROM                                                         \n"
            sql += lv_member_col_comb_tbl + "                                         \n"
            sql += "     WHERE                                                        \n"
            sql += "       MVMT_VAR_LINK_ID IN (                                      \n"
            sql += "         SELECT                                                   \n"
            sql += "           MVMT_VAR_LINK_ID                                       \n"
            sql += "         FROM                                                     \n"
            sql += lv_ptn_vars_link_tbl + "                                           \n"
            sql += "         WHERE                                                    \n"
            sql += "           MOVEMENT_ID    = TBL_A.MOVEMENT_ID        AND          \n"
            sql += "           MVMT_VAR_LINK_ID  = TBL_A.MVMT_VAR_LINK_ID  AND        \n"
            sql += "           DISUSE_FLAG   = '0'                                    \n"
            sql += "         )                                                        \n"
            sql += "       AND                                                        \n"
            sql += "       COL_SEQ_COMBINATION_ID = TBL_A.COL_SEQ_COMBINATION_ID AND  \n"
            sql += "       DISUSE_FLAG = '0'                                          \n"
            sql += "   ) AS KEY_COL_COMBINATION_MEMBER_ALIAS                       ,  \n"

        # (Key)多次元変数メンバー管理
        sql += "   TBL_A.ASSIGN_SEQ                                            ,  \n"
        if in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            sql += "   (                                                              \n"
            sql += "     SELECT                                                       \n"
            sql += "       ASSIGN_SEQ_NEED                                            \n"
            sql += "     FROM                                                         \n"
            sql += lv_array_member_tbl + "                                            \n"
            sql += "     WHERE                                                        \n"
            sql += "       MVMT_VAR_LINK_ID IN (                                      \n"
            sql += "         SELECT                                                   \n"
            sql += "           MVMT_VAR_LINK_ID                                       \n"
            sql += "         FROM                                                     \n"
            sql += lv_ptn_vars_link_tbl + "                                           \n"
            sql += "         WHERE                                                    \n"
            sql += "           MOVEMENT_ID    = TBL_A.MOVEMENT_ID        AND          \n"
            sql += "           MVMT_VAR_LINK_ID  = TBL_A.MVMT_VAR_LINK_ID  AND        \n"
            sql += "           DISUSE_FLAG   = '0'                                    \n"
            sql += "         )                                                        \n"
            sql += "       AND                                                        \n"
            sql += "       ARRAY_MEMBER_ID IN (                                       \n"
            sql += "         SELECT                                                   \n"
            sql += "           ARRAY_MEMBER_ID                                        \n"
            sql += "         FROM                                                     \n"
            sql += lv_member_col_comb_tbl + "                                         \n"
            sql += "         WHERE                                                    \n"
            sql += "           COL_SEQ_COMBINATION_ID = TBL_A.COL_SEQ_COMBINATION_ID AND \n"
            sql += "           DISUSE_FLAG   = '0'                                    \n"
            sql += "         )                                                        \n"
            sql += "       AND                                                        \n"
            sql += "       DISUSE_FLAG = '0'                                          \n"
            sql += "   ) AS KEY_ASSIGN_SEQ_NEED,                                      \n"
        sql += "   TBL_D.DISUSE_FLAG AS ANSIBLE_TARGET_TABLE                      \n"
        sql += " FROM                                                             \n"
        if in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            sql += lv_val_assign_tbl + "  TBL_A                                   \n"
        if in_driver_name == AnscConst.DF_LEGACY_DRIVER_ID:
            sql += lv_l_val_assign_tbl + " TBL_A                                  \n"
        elif in_driver_name == AnscConst.DF_PIONEER_DRIVER_ID:
            sql += lv_p_val_assign_tbl + " TBL_A                                  \n"
        sql += "   LEFT JOIN T_COMN_MENU_COLUMN_LINK TBL_B ON                     \n"
        sql += "          (TBL_A.COLUMN_LIST_ID = TBL_B.COLUMN_DEFINITION_ID)     \n"
        sql += "   LEFT JOIN T_COMN_MENU_TABLE_LINK          TBL_C ON             \n"
        sql += "          (TBL_B.MENU_ID        = TBL_C.MENU_ID)                  \n"
        sql += "   LEFT JOIN T_COMN_MENU   TBL_D ON                               \n"
        sql += "          (TBL_C.MENU_ID        = TBL_D.MENU_ID)                  \n"
        if in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            sql += "   LEFT JOIN T_ANSR_MVMT_VAR_LINK TBL_E ON                    \n"
        if in_driver_name == AnscConst.DF_LEGACY_DRIVER_ID:
            sql += "   LEFT JOIN T_ANSL_MVMT_VAR_LINK TBL_E ON                    \n"
        elif in_driver_name == AnscConst.DF_PIONEER_DRIVER_ID:
            sql += "   LEFT JOIN T_ANSP_MVMT_VAR_LINK TBL_E ON                    \n"
        sql += "          (TBL_A.MVMT_VAR_LINK_ID    = TBL_E.MVMT_VAR_LINK_ID)    \n"
        sql += " WHERE                                                            \n"
        sql += "   TBL_A.DISUSE_FLAG='0'                                          \n"
        if movement_id is not None:
            sql += "   AND TBL_A.MOVEMENT_ID = %s                                 \n"
        sql += "   AND TBL_C.DISUSE_FLAG='0'                                      \n"
        sql += "   AND TBL_B.AUTOREG_HIDE_ITEM = '0'                              \n"
        sql += " ORDER BY TBL_A.COLUMN_ID                                         \n"

        if movement_id is not None:
            data_list = WS_DB.sql_execute(sql, [movement_id])
        else:
            data_list = WS_DB.sql_execute(sql)

        inout_tableNameToMenuIdList = {}
        inout_tabColNameToValAssRowList = {}
        inout_tableNameToMenuNameRestList = {}
        data_cnt_ary = {}
        idx = 0

        for data in data_list:
            # SHEET_TYPEが1(ホスト・オペレーション)で廃止レコードでないかを判定
            if data['ANSIBLE_TARGET_TABLE'] != '0':
                msgstr = g.appmsg.get_api_message("MSG-10437", [data['COLUMN_ID']])
                g.applogger.info(os.path.basename(__file__) + " " + msgstr)
                # 次のカラムへ
                continue

            # 作業パターン詳細に作業パターンが未登録
            if data['PATTERN_CNT'] == '0':
                msgstr = g.appmsg.get_api_message("MSG-10336", [data['COLUMN_ID']])
                g.applogger.info(os.path.basename(__file__) + " " + msgstr)
                # 次のカラムへ
                continue

            # CMDB代入値紐付メニューが登録されているか判定
            if data['TABLE_NAME'] is None or len(data['TABLE_NAME']) == 0:
                msgstr = g.appmsg.get_api_message("MSG-10338", [data['COLUMN_ID']])
                g.applogger.info(os.path.basename(__file__) + " " + msgstr)
                # 次のカラムへ
                continue

            # CMDB代入値紐付メニューのカラムが未登録か判定
            if data['COL_NAME'] is None or len(data['COL_NAME']) == 0:
                msgstr = g.appmsg.get_api_message("MSG-10340", [data['COLUMN_ID']])
                g.applogger.info(os.path.basename(__file__) + " " + msgstr)
                # 次のカラムへ
                continue

            type_chk = [AnscConst.DF_COL_TYPE_VAL, AnscConst.DF_COL_TYPE_KEY]
            col_type = data['COL_TYPE']
            if col_type not in type_chk:
                msgstr = g.appmsg.get_api_message("MSG-10342", [data['COLUMN_ID']])
                g.applogger.info(os.path.basename(__file__) + " " + msgstr)
                # 次のカラムへ
                continue

            # Value型変数の変数タイプ
            val_vars_attr = ""
            key_vars_attr = ""

            # Key項目・Value項目の検査（当該レコード）
            # カラムタイプにより処理分岐

            if col_type == AnscConst.DF_COL_TYPE_VAL:
                # 項目なしはスキップ
                if data['COL_GROUP_ID'] is not None:
                    ret = self.valAssColumnValidate("Value",
                                                val_vars_attr,
                                                data,
                                                "MVMT_VAR_LINK_ID",
                                                "VARS_NAME",
                                                "VAL_PTN_VARS_LINK_CNT",
                                                "VARS_ATTRIBUTE_01",
                                                "COL_SEQ_COMBINATION_ID",
                                                "VAL_COL_COMBINATION_MEMBER_ALIAS",
                                                "ASSIGN_SEQ",
                                                "VAL_ASSIGN_SEQ_NEED",
                                                in_driver_name)

                    if ret[0] is False:
                        continue

                    val_vars_attr = ret[1]
                else:
                    # 代入値自動登録選択項目フラグがOFFの場合はスキップ
                    if data['AUTOREG_ONLY_ITEM'] == '0':
                        continue
                    if data['VARS_ATTRIBUTE_01'] in [AnscConst.GC_VARS_ATTR_STD, AnscConst.GC_VARS_ATTR_LIST, AnscConst.GC_VARS_ATTR_M_ARRAY]:
                        val_vars_attr = data['VARS_ATTRIBUTE_01']

            if col_type == AnscConst.DF_COL_TYPE_KEY:
                # 項目なしはスキップ
                if data['COL_GROUP_ID'] is not None:
                    ret = self.valAssColumnValidate("Key",
                                                key_vars_attr,
                                                data,
                                                "MVMT_VAR_LINK_ID",
                                                "VARS_NAME",
                                                "KEY_PTN_VARS_LINK_CNT",
                                                "VARS_ATTRIBUTE_01",
                                                "COL_SEQ_COMBINATION_ID",
                                                "KEY_COL_COMBINATION_MEMBER_ALIAS",
                                                "ASSIGN_SEQ",
                                                "KEY_ASSIGN_SEQ_NEED",
                                                in_driver_name)

                    if ret[0] is False:
                        continue

                    key_vars_attr = ret[1]
                else:
                    # 代入値自動登録選択項目フラグがOFFの場合はスキップ
                    if data['AUTOREG_ONLY_ITEM'] == '0':
                        continue
                    if data['VARS_ATTRIBUTE_01'] in [AnscConst.GC_VARS_ATTR_STD, AnscConst.GC_VARS_ATTR_LIST, AnscConst.GC_VARS_ATTR_M_ARRAY]:
                        key_vars_attr = data['VARS_ATTRIBUTE_01']

            inout_tableNameToMenuIdList[data['TABLE_NAME']] = data['MENU_ID']
            inout_tableNameToMenuNameRestList[data['TABLE_NAME']] = data['MENU_NAME_REST']

            # PasswordColumnかを判定
            key_sensitive_flg = AnscConst.DF_SENSITIVE_OFF
            value_sensitive_flg = AnscConst.DF_SENSITIVE_OFF
            if data['COLUMN_CLASS'] == '8' or data['COLUMN_CLASS'] == '25' or data['COLUMN_CLASS'] == '26':
                value_sensitive_flg = AnscConst.DF_SENSITIVE_ON

            if data['TABLE_NAME'] not in inout_tabColNameToValAssRowList:
                inout_tabColNameToValAssRowList[data['TABLE_NAME']] = {}
            if data['COL_NAME'] not in inout_tabColNameToValAssRowList[data['TABLE_NAME']]:
                inout_tabColNameToValAssRowList[data['TABLE_NAME']][data['COL_NAME']] = {}

            # 各パラメータシートごとのデータ数
            if data['TABLE_NAME'] not in data_cnt_ary:
                data_cnt_ary[data['TABLE_NAME']] = 1
            else:
                data_cnt_ary[data['TABLE_NAME']] += 1

            inout_tabColNameToValAssRowList[data['TABLE_NAME']][data['COL_NAME']][idx] = {
                                                                            'COLUMN_ID': data['COLUMN_ID'],
                                                                            'COL_TYPE': data['COL_TYPE'],
                                                                            'COLUMN_CLASS': data['COLUMN_CLASS'],
                                                                            'COLUMN_NAME_JA': data['COLUMN_NAME_JA'],
                                                                            'COLUMN_NAME_EN': data['COLUMN_NAME_EN'],
                                                                            'COLUMN_NAME_REST': data['COLUMN_NAME_REST'],
                                                                            'COL_GROUP_ID': data['COL_GROUP_ID'],
                                                                            'REF_TABLE_NAME': data['REF_TABLE_NAME'],
                                                                            'REF_PKEY_NAME': data['REF_PKEY_NAME'],
                                                                            'REF_COL_NAME': data['REF_COL_NAME'],
                                                                            'MOVEMENT_ID': data['MOVEMENT_ID'],
                                                                            'MVMT_VAR_LINK_ID': data['MVMT_VAR_LINK_ID'],
                                                                            'VAL_VAR_TYPE': val_vars_attr,
                                                                            'COLUMN_ASSIGN_SEQ': data['COLUMN_ASSIGN_SEQ'],
                                                                            'COL_SEQ_COMBINATION_ID': data['COL_SEQ_COMBINATION_ID'],
                                                                            'VAL_COL_COMBINATION_MEMBER_ALIAS': data['VAL_COL_COMBINATION_MEMBER_ALIAS'],
                                                                            'ASSIGN_SEQ': data['ASSIGN_SEQ'],
                                                                            'VALUE_SENSITIVE_FLAG': value_sensitive_flg,
                                                                            'KEY_VAR_TYPE': key_vars_attr,
                                                                            'NULL_DATA_HANDLING_FLG': data['NULL_DATA_HANDLING_FLG'],
                                                                            'KEY_SENSITIVE_FLAG': key_sensitive_flg,
                                                                            'MENU_NAME_REST': data['MENU_NAME_REST']}

            # テーブルの主キー名退避
            pk_name = WS_DB.table_columns_get(data['TABLE_NAME'])
            inout_tableNameToPKeyNameList[data['TABLE_NAME']] = {}
            inout_tableNameToPKeyNameList[data['TABLE_NAME']] = pk_name[1][0]
            idx += 1

        return True, inout_tableNameToMenuIdList, inout_tabColNameToValAssRowList, inout_tableNameToPKeyNameList, inout_tableNameToMenuNameRestList, data_cnt_ary

    def valAssColumnValidate(self,
                            in_col_type,
                            inout_vars_attr,
                            row,
                            in_vars_link_id,
                            in_vars_name,
                            in_ptn_vars_link_cnt,
                            in_vars_attribute_01,
                            in_col_seq_combination_id,
                            in_col_combination_member_alias,
                            in_assign_seq,
                            in_assign_seq_need,
                            in_driver_name=AnscConst.DF_LEGACY_ROLE_DRIVER_ID):
        """
        代入値自動登録設定のカラム情報を検査する。

        Arguments:
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
            ina_if_info: インターフェース情報
            in_error_msg: エラーメッセージ
        """

        # 変数の選択判定
        if row[in_vars_link_id] is None or len(row[in_vars_link_id]) == 0:
            msgstr = g.appmsg.get_api_message("MSG-10354", [row['COLUMN_ID'], in_col_type])
            g.applogger.info(msgstr)
            return False, inout_vars_attr

        # 変数が作業パターン変数紐付にあるか判定
        if row[in_ptn_vars_link_cnt] is None or row[in_ptn_vars_link_cnt] == 0:
            msgstr = g.appmsg.get_api_message("MSG-10348", [row['COLUMN_ID'], in_col_type])
            g.applogger.info(msgstr)
            return False, inout_vars_attr

        # 設定されている変数が変数一覧にあるか判定
        if row[in_vars_name] is None or len(str(row[in_vars_name])) == 0:
            msgstr = g.appmsg.get_api_message("MSG-10345", [row['COLUMN_ID'], in_col_type])
            g.applogger.info(msgstr)
            return False, inout_vars_attr

        # ロールのみ変数タイプの判定
        if in_driver_name == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            if row[in_vars_attribute_01] in [AnscConst.GC_VARS_ATTR_STD, AnscConst.GC_VARS_ATTR_LIST, AnscConst.GC_VARS_ATTR_M_ARRAY]:
                inout_vars_attr = row[in_vars_attribute_01]
            else:
                msgstr = g.appmsg.get_api_message("MSG-10439", [row['COLUMN_ID'], in_col_type])
                g.applogger.info(msgstr)
                return False, inout_vars_attr

            # メンバー変数がメンバー変数一覧にあるか判定
            if inout_vars_attr == AnscConst.GC_VARS_ATTR_M_ARRAY:
                # メンバー変数の選択判定
                if row[in_col_seq_combination_id] is None or len(row[in_col_seq_combination_id]) == 0:
                    msgstr = g.appmsg.get_api_message("MSG-10419", [row['COLUMN_ID'], in_col_type])
                    g.applogger.info(msgstr)
                    return False, inout_vars_attr

                # カラムタイプ型に設定されているメンバー変数がメンバー変数一覧にあるか判定
                if row[in_col_combination_member_alias] is None or len(row[in_col_combination_member_alias]) == 0:
                    msgstr = g.appmsg.get_api_message("MSG-10349", [row['COLUMN_ID'], in_col_type])
                    g.applogger.info(msgstr)
                    return False, inout_vars_attr
            else:
                if not row[in_col_seq_combination_id] is None and not len(row[in_col_seq_combination_id]) == 0:
                    msgstr = g.appmsg.get_api_message("MSG-10418", [row['COLUMN_ID'], in_col_type])
                    g.applogger.info(msgstr)
                    return False, inout_vars_attr

            if inout_vars_attr == AnscConst.GC_VARS_ATTR_LIST:
                if row[in_assign_seq] is None or len(str(row[in_assign_seq])) == 0:
                    msgstr = g.appmsg.get_api_message("MSG-10350", [row['COLUMN_ID'], in_col_type])
                    g.applogger.info(msgstr)
                    return False, inout_vars_attr

            elif inout_vars_attr == AnscConst.GC_VARS_ATTR_M_ARRAY:
                if row[in_assign_seq_need] == 1:
                    if row[in_assign_seq] is None or row[in_assign_seq] == 0:
                        msgstr = g.appmsg.get_api_message("MSG-10350", [row['COLUMN_ID'], in_col_type])
                        g.applogger.info(msgstr)
                        return False, inout_vars_attr
        else:
            # Legacy・Pioneerは一般変数として処理
            inout_vars_attr = AnscConst.GC_VARS_ATTR_STD

        return True, inout_vars_attr

    def extract_tpl_vars(self, var_extractor, varsAssRecord, template_list, host_list):

        # 処理対象外のデータかを判定
        if len(varsAssRecord) == 0:
            return template_list, host_list
        if varsAssRecord['STATUS'] is False:
            return template_list, host_list

        movement_id = varsAssRecord['MOVEMENT_ID']
        vars_line_array = [] # [{行番号:変数名}, ...]
        if type(varsAssRecord['VARS_ENTRY']) is str:
            is_success, vars_line_array = var_extractor.SimpleFillterVerSearch("TPF_", varsAssRecord['VARS_ENTRY'], vars_line_array, [], [])
            if len(vars_line_array) == 1:
                if movement_id not in template_list:
                    template_list[movement_id] = {}
                tpf_var_name = list(vars_line_array[0].values())[0]
                template_list[movement_id][tpf_var_name] = 0

        # 作業対象ホストの情報を退避
        if movement_id not in host_list:
            host_list[movement_id] = {}
        operation_id = varsAssRecord['OPERATION_ID']
        if operation_id not in host_list[movement_id]:
            host_list[movement_id][operation_id] = {}
        host_list[movement_id][operation_id][varsAssRecord['SYSTEM_ID']] = 0

        return template_list, host_list

    def rest_filter(self, WS_DB, obj_load_table):
        res = []

        view_name = obj_load_table.get_view_name()
        if view_name:
            l_table_name = view_name
        else:
            l_table_name = obj_load_table.get_table_name()
        tmp_result = WS_DB.table_select(l_table_name, "WHERE DISUSE_FLAG = '0'", [])

        for tmp_result_child in tmp_result:
            parameter = {
                "uuid": tmp_result_child["ROW_ID"],
                "HOST_ID": tmp_result_child["HOST_ID"],
                "OPERATION_ID": tmp_result_child["OPERATION_ID"]
            }

            # 縦メニュー
            if "INPUT_ORDER" in tmp_result_child:
                parameter["input_order"] = tmp_result_child["INPUT_ORDER"]

            # 作成したカラム
            data_json_parameter = self.convert_colname_restkey(obj_load_table, tmp_result_child["DATA_JSON"])

            parameter.update(data_json_parameter)  # マージ
            res.append(parameter)

        return res

    def convert_colname_restkey(self, obj_load_table, data_json):
        data_json_parameter = obj_load_table.get_json_cols_base()

        json_cols_base_key = set(list(data_json_parameter.keys()))

        json_rows = data_json if data_json is None else json.loads(data_json)
        if json_rows:
            for jsonkey, jsonval in json_rows.items():
                if jsonkey in json_cols_base_key:
                    objcolumn = obj_load_table.get_columnclass(jsonkey)
                    # ID → VALUE 変換処理不要ならVALUE変更無し
                    if obj_load_table.get_col_class_name(jsonkey) in ['PasswordColumn']:
                        if jsonval is not None:
                            pass
                    elif obj_load_table.get_col_class_name(jsonkey) in ['PasswordIDColumn', 'JsonPasswordIDColumn']:
                        if jsonval is not None:
                            # base64した値をそのまま返却
                            result = objcolumn.get_values_by_key([jsonval])
                            jsonval = result.get(jsonval)
                    else:
                        tmp_exec = objcolumn.convert_value_output(jsonval)
                        if tmp_exec[0] is True:
                            jsonval = tmp_exec[2]

                    data_json_parameter[jsonkey] = jsonval

        return data_json_parameter

    def exec_maintenance(self, WS_DB, subst_value_list_table, primary_key, row={}, org_fil_path='', menu_id=None):
        retBool = True
        msg = ""

        # 登録・更新処理
        result = WS_DB.table_insert(subst_value_list_table, row, primary_key, False)

        if result is False:
            retBool = False
            msg = ''
            return retBool, msg

        # ファイル無 の場合は、処理終了
        if not org_fil_path:
            return retBool, msg

        # ファイル有 の場合は、保管
        uuid = result[0][primary_key]
        path = get_upload_file_path(g.WORKSPACE_ID, menu_id, uuid, 'file', row["VARS_ENTRY_FILE"], uuid)

        dir_path = path["file_path"]
        old_dir_path = path["old_file_path"]

        # オリジナルのファイルをold配下にコピー
        os.makedirs(os.path.dirname(old_dir_path), exist_ok=True)
        shutil.copy2(org_fil_path, old_dir_path)

        # シンボリックリンク作成
        try:
            os.symlink(old_dir_path, dir_path)
        except Exception:
            retBool = False
            msg = ""

        return retBool, msg
