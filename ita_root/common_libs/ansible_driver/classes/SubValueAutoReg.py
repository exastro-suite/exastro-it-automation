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

import json
import os
import subprocess
import inspect
import hashlib
import re

from flask import g
from pathlib import Path
from pprint import pprint

from common_libs.common import *
from common_libs.loadtable import *
from common_libs.common.exception import *
from .AnsibleMakeMessage import AnsibleMakeMessage
from .AnscConstClass import AnscConst
from .WrappedStringReplaceAdmin import WrappedStringReplaceAdmin

# ローカル変数(全体)宣言
lv_val_assign_tbl = 'T_ANSR_VALUE_AUTOREG'
lv_pattern_link_tbl = 'T_ANSR_MVMT_MATL_LINK'
lv_ptn_vars_link_tbl = 'T_ANSR_MVMT_VAR_LINK'
lv_member_col_comb_tbl = 'T_ANSR_NESTVAR_MEMBER_COL_COMB'
lv_array_member_tbl = 'T_ANSR_NESTVAR_MEMBER'
vg_FileUPloadColumnBackupFilePath = ""
db_update_flg = False
g_null_data_handling_def = ""
warning_flag = 0
error_flag = 0
col_filepath = ""

arrayValueTmplOfVarAss = {
    "JOURNAL_SEQ_NO": "",
    "JOURNAL_ACTION_CLASS": "",
    "JOURNAL_REG_DATETIME": "",
    "ASSIGN_ID": "",
    "OPERATION_ID": "",
    "MOVEMENT_ID": "",
    "SYSTEM_ID": "",
    "MVMT_VAR_LINK_ID": "",
    "COL_SEQ_COMBINATION_ID": "",
    "VARS_ENTRY": "",
    "COL_SEQ_COMBINATION_ID": "",
    "SENSITIVE_FLAG": "",
    "VARS_ENTRY_FILE": "",
    "VARS_ENTRY_USE_TPFVARS": "",
    "ASSIGN_SEQ": "",
    "DISP_SEQ": "",
    "DISUSE_FLAG": "",
    "NOTE": "",
    "LAST_UPDATE_TIMESTAMP": "",
    "LAST_UPDATE_USER": ""}

arrayValueTmplOfPhoLnk = {
    "JOURNAL_SEQ_NO": "",
    "JOURNAL_ACTION_CLASS": "",
    "JOURNAL_REG_DATETIME": "",
    "PHO_LINK_ID": "",
    "OPERATION_NO_UAPK": "",
    "PATTERN_ID": "",
    "SYSTEM_ID": "",
    "DISP_SEQ": "",
    "ACCESS_AUTH": "",
    "DISUSE_FLAG": "",
    "NOTE": "",
    "LAST_UPDATE_TIMESTAMP": "",
    "LAST_UPDATE_USER": ""
}

class SubValueAutoReg():
    """
    代入値自動登録とパラメータシートを抜くclass
    """
    
    def GetDataFromParameterSheet(self, exec_type, operation_id="", movement_id="", execution_no="", WS_DB=None):
        """
        代入値自動登録とパラメータシートを抜く
        """
        
        global g_null_data_handling_def
        global warning_flag
        global error_flag
        
        # インターフェース情報からNULLデータを代入値管理に登録するかのデフォルト値を取得する。
        ret = self.getIFInfoDB(WS_DB)

        if ret[0] == 0:
            error_flag = 1
            raise ValidationException(ret[2])
        
        lv_if_info = ret[1]
        g_null_data_handling_def = lv_if_info["NULL_DATA_HANDLING_FLG"]
        
        # 代入値自動登録設定からカラム毎の変数の情報を取得
        # トレースメッセージ
        traceMsg = g.appmsg.get_api_message("MSG-10804")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)
        
        ret = self.readValAssign(movement_id, WS_DB)
        
        if ret[0] == 0:
            error_flag = 1
            raise ValidationException("MSG-10353")
        
        lv_tableNameToMenuIdList = ret[1]
        lv_tabColNameToValAssRowList = ret[2]
        lv_tableNameToPKeyNameList = ret[3]
        lv_tableNameToMenuNameRestList = ret[4]
        
        # 紐付メニューへのSELECT文を生成する。
        ret = self.createQuerySelectCMDB(lv_tableNameToMenuIdList, lv_tabColNameToValAssRowList, lv_tableNameToPKeyNameList)
        # 代入値紐付メニュー毎のSELECT文配列
        lv_tableNameToSqlList = ret
        
        # 紐付メニューから具体値を取得する。
        traceMsg = g.appmsg.get_api_message("MSG-10805")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)
        
        warning_flag = 0
        ret = self.getCMDBdata(lv_tableNameToSqlList, lv_tableNameToMenuIdList, lv_tabColNameToValAssRowList, lv_tableNameToMenuNameRestList, warning_flag, WS_DB)
        lv_varsAssList = ret[0]
        lv_arrayVarsAssList = ret[1]
        warning_flag = ret[2]
        
        # 処理区分が変数抜出処理
        if exec_type == '2':

            template_list = {} # { MovementID: { TPF変数名: 0 }, … }
            host_list = {} # { MovementID: { OPERATION_ID: { SYSTEM_ID: 0 }, … }, … }
            
            var_extractor = WrappedStringReplaceAdmin()
            
            # 一般変数・複数具体値変数を紐付けている紐付メニューの具体値からTPF変数を抽出する
            for varsAssRecord in lv_varsAssList.values():
                template_list, host_list = self.extract_tpl_vars(var_extractor, varsAssRecord, template_list, host_list)

            # 多次元変数を紐付けている紐付メニューの具体値からTPF変数を抽出する
            for varsAssRecord in lv_arrayVarsAssList.values():
                template_list, host_list = self.extract_tpl_vars(var_extractor, varsAssRecord, template_list, host_list)

            return True, template_list, host_list
        
        # トランザクション開始 
        traceMsg = g.appmsg.get_api_message("MSG-10785")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)
        
        WS_DB.db_transaction_start()
        
        # 作業対象ホストに登録が必要な配列初期化
        lv_phoLinkList = {}
        
        # 一般変数・複数具体値変数を紐付けている紐付メニューの具体値を代入値管理に登録
        # トレースメッセージ
        traceMsg = g.appmsg.get_api_message("MSG-10833")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)
        
        for varsAssRecord in lv_varsAssList.values():
            # 処理対象外のデータかを判定
            if len(varsAssRecord) == 0:
                continue
            if varsAssRecord['STATUS'] == 0:
                continue
            if not operation_id == varsAssRecord['OPERATION_ID'] or not movement_id == varsAssRecord['MOVEMENT_ID']:
                continue
            
            # 代入値管理に具体値を登録
            ret = self.addStg1StdListVarsAssign(varsAssRecord, execution_no, WS_DB)
            if ret == 0:
                error_flag = 1
                raise ValidationException("MSG-10466")
            
            # 作業対象ホストに登録が必要な情報を退避
            lv_phoLinkList[varsAssRecord['OPERATION_ID']] = {}
            lv_phoLinkList[varsAssRecord['OPERATION_ID']][varsAssRecord['MOVEMENT_ID']] = {}
            lv_phoLinkList[varsAssRecord['OPERATION_ID']][varsAssRecord['MOVEMENT_ID']][varsAssRecord['SYSTEM_ID']] = {}
            
        # 多次元変数を紐付けている紐付メニューの具体値を代入値管理に登録
        # トレースメッセージ
        traceMsg = g.appmsg.get_api_message("MSG-10834")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)
        
        for varsAssRecord in lv_arrayVarsAssList.values():
            # 処理対象外のデータかを判定
            if len(varsAssRecord) == 0:
                continue
            if varsAssRecord['STATUS'] == 0:
                continue
            
            ret = self.addStg1ArrayVarsAssign(varsAssRecord, lv_tableNameToMenuIdList, execution_no, WS_DB)
            if ret == 0:
                error_flag = 1
                raise ValidationException("MSG-10441")
            
            # 作業対象ホストに登録が必要な情報を退避
            lv_phoLinkList[varsAssRecord['OPERATION_ID']] = {}
            lv_phoLinkList[varsAssRecord['OPERATION_ID']][varsAssRecord['MOVEMENT_ID']] = {}
            lv_phoLinkList[varsAssRecord['OPERATION_ID']][varsAssRecord['MOVEMENT_ID']][varsAssRecord['SYSTEM_ID']] = {}
        
        del lv_tableNameToMenuIdList
        del lv_varsAssList
        del lv_arrayVarsAssList
        
        # コミット(レコードロックを解除)
        WS_DB.db_commit()
        
        # トランザクション終了
        WS_DB.db_transaction_end(True)
        
        # トレースメッセージ
        traceMsg = g.appmsg.get_api_message("MSG-10785")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)
        
        WS_DB.db_transaction_start()
        
        # 対象ホスト管理のデータを全件読込
        lv_PhoLinkRecodes = {}
        ret = self.getPhoLinkRecodes(WS_DB)
        lv_PhoLinkRecodes = ret[1]
        
        # 代入値管理で登録したオペ+作業パターン+ホストが作業対象ホストに登録されているか判定し、未登録の場合は登録する
        # トレースメッセージ
        traceMsg = g.appmsg.get_api_message("MSG-10810")
        frame = inspect.currentframe().f_back
        g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)
        
        for ope_id, ptn_list in lv_phoLinkList.items():
            for ptn_id, host_list in ptn_list.items():
                for host_id, access_auth in host_list.items():
                    lv_phoLinkData = {'OPERATION_ID': ope_id, 'MOVEMENT_ID': ptn_id, 'SYSTEM_ID': host_id}
                    ret = self.addStg1PhoLink(lv_phoLinkData, lv_PhoLinkRecodes, execution_no, WS_DB)
                    lv_PhoLinkRecodes = ret[1]
                    
                    if ret[0] == 0:
                        error_flag = 1
                        raise ValidationException("MSG-10373")
        
        del lv_phoLinkList
        del lv_PhoLinkRecodes
        
        # コミット(レコードロックを解除)
        # トランザクション終了
        WS_DB.db_transaction_end(True)
        
        return True
        
    def getAnsible_RolePackage_file(self, in_dir, in_pkey, in_filename):
        intNumPadding = 10
        
        # sible実行時の子Playbookファイル名は Pkey(10桁)-子Playbookファイル名 する
        file = in_dir + '/' + in_pkey.rjust(intNumPadding, '0') + '/' + in_filename
        return file
    
    def getPhoLinkRecodes(self, WS_DB):
        """
        作業対象ホストの全データ読込
        
        Arguments:
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
            in_PhoLinkRecodes: 作業対象ホストの全データ配列
        """
        in_PhoLinkRecodes = {}
        
        where = "WHERE PHO_LINK_ID <> '0'"
        WS_DB.table_lock(["T_ANSR_TGT_HOST"])
        data_list = WS_DB.table_select("T_ANSR_TGT_HOST", where)
        
        for row in data_list:
            key = row["OPERATION_ID"] + "_"
            key += row["MOVEMENT_ID"] + "_"
            key += row["SYSTEM_ID"] + "_"
            key += row["DISUSE_FLAG"]
            
            in_PhoLinkRecodes[key] = row
        
        return True, in_PhoLinkRecodes
    
    def addStg1PhoLink(self, in_phoLinkData, in_PhoLinkRecodes, execution_no, WS_DB):
        """
        作業対象ホストの廃止レコードを復活または新規レコード追加
        
        Arguments:
            in_phoLinkData: 作業対象ホスト更新情報配列
            in_PhoLinkRecodes: 作業対象ホストの全データ配列
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
            in_PhoLinkRecodes: 作業対象ホストの全データ配列
        """
        global strCurTablePhoLnk
        global strJnlTablePhoLnk
        global strSeqOfCurTablePhoLnk
        global strSeqOfJnlTablePhoLnk
        global arrayConfigOfPhoLnk
        global arrayValueTmplOfPhoLnk
        
        db_valautostup_user_id = g.USER_ID
        
        arrayValue = arrayValueTmplOfPhoLnk
        
        key = in_phoLinkData["OPERATION_ID"] + "_"
        key += in_phoLinkData["MOVEMENT_ID"] + "_"
        key += in_phoLinkData["SYSTEM_ID"] + "_1"
        
        objmenu = load_table.loadTable(WS_DB, "target_host_ansible_role")
        tgt_row = arrayValue
        
        # 更新対象の作業対象ホスト管理主キー値を退避
        inout_phoLinkId = str(WS_DB._uuid_create())
        
        # 登録する情報設定
        tgt_row['PHO_LINK_ID'] = inout_phoLinkId
        tgt_row['OPERATION_ID'] = in_phoLinkData['OPERATION_ID']
        tgt_row['MOVEMENT_ID'] = in_phoLinkData['MOVEMENT_ID']
        tgt_row['SYSTEM_ID'] = in_phoLinkData['SYSTEM_ID']
        
        tgt_row['DISUSE_FLAG'] = "0"
        tgt_row['LAST_UPDATE_USER'] = db_valautostup_user_id
        
        tgt_row = self.getLoadtableRegisterValue(tgt_row, False, WS_DB)
        parameter = {
            "item_no": tgt_row['PHO_LINK_ID'],
            "operation": tgt_row['OPERATION_NAME'],
            "execution_no": execution_no,
            "movement": tgt_row['MOVEMENT_NAME'],
            "host": tgt_row['HOST_NAME'],
            "discard": tgt_row['DISUSE_FLAG'],
            "remarks": tgt_row['NOTE'],
            "last_update_date_time": str(tgt_row['LAST_UPDATE_TIMESTAMP']).replace('-', '/'),
            "last_updated_user": tgt_row['LAST_UPDATE_USER']
        }

        parameters = {
            "parameter": parameter,
            "file": {},
            "type": "Register"
        }
        retAry = objmenu.exec_maintenance(parameters, "", "", False, False)
            
        result = retAry[0]
        if result is False:
            raise AppException("499-00701", [retAry], [retAry])
        
        return True, in_PhoLinkRecodes
    
    def createQuerySelectCMDB(self, in_tableNameToMenuIdList, in_tabColNameToValAssRowList, in_tableNameToPKeyNameList):
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
            pkey_name = in_tableNameToPKeyNameList[table_name]
            
            col_sql = ""
            for col_name in col_list.keys():
                col_sql = col_sql + ", TBL_A." + col_name + " \n"
            
            if col_sql == "":
                # SELECT対象の項目なし
                # エラーがあるのでスキップ
                msgstr = g.appmsg.get_api_message("MSG-10356", [in_tableNameToMenuIdList[table_name]])
                frame = inspect.currentframe().f_back
                g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                # 次のテーブルへ
                continue
            
            # SELECT文を生成
            make_sql = "SELECT \n "
            make_sql += opeid_chk_sql + " \n "
            make_sql += hostid_chk_sql + " \n "
            make_sql += " TBL_A." + pkey_name + " AS %s   \n "
            make_sql += ", TBL_A.HOST_ID \n "
            make_sql += col_sql + " \n "
            make_sql += " FROM `" + table_name + "` TBL_A \n "
            make_sql += " WHERE DISUSE_FLAG = '0' \n "
            
            # メニューテーブルのSELECT SQL文退避
            inout_tableNameToSqlList[table_name] = make_sql
            
        return inout_tableNameToSqlList
    
    def getVarsAssignRecodes(self, WS_DB):
        """
        代入値管理の情報を取得
        
        Arguments:
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
            in_VarsAssignRecodes: 代入値管理に登録されている変数リスト
            in_ArryVarsAssignRecodes: 代入値管理に登録されている多段変数リスト
        """
        
        global warning_flag
        global col_filepath
        
        in_VarsAssignRecodes = {}
        in_ArryVarsAssignRecodes = {}
        
        sqlUtnBody = "SELECT "
        sqlUtnBody += " ASSIGN_ID, "
        sqlUtnBody += " EXECUTION_NO, "
        sqlUtnBody += " OPERATION_ID, "
        sqlUtnBody += " MOVEMENT_ID, "
        sqlUtnBody += " SYSTEM_ID, "
        sqlUtnBody += " MVMT_VAR_LINK_ID, "
        sqlUtnBody += " COL_SEQ_COMBINATION_ID, "
        sqlUtnBody += " VARS_ENTRY, "
        sqlUtnBody += " SENSITIVE_FLAG, "
        sqlUtnBody += " VARS_ENTRY_FILE, "
        sqlUtnBody += " VARS_ENTRY_USE_TPFVARS, "
        sqlUtnBody += " ASSIGN_SEQ, "
        sqlUtnBody += " DISUSE_FLAG, "
        sqlUtnBody += " NOTE, "
        sqlUtnBody += " DATE_FORMAT(LAST_UPDATE_TIMESTAMP,'%Y/%m/%d %H:%i:%s.%f') LAST_UPDATE_TIMESTAMP, "
        sqlUtnBody += " CASE WHEN LAST_UPDATE_TIMESTAMP IS NULL THEN 'VALNULL' ELSE CONCAT('T_',DATE_FORMAT(LAST_UPDATE_TIMESTAMP,'%Y%m%d%H%i%s%f')) END UPD_UPDATE_TIMESTAMP, "
        sqlUtnBody += " LAST_UPDATE_USER "
        sqlUtnBody += " FROM T_ANSR_VALUE "
        sqlUtnBody += " WHERE ASSIGN_ID > '0' "
        
        ret = WS_DB.table_lock(['T_ANSR_VALUE'])
        
        data_list = WS_DB.sql_execute(sqlUtnBody, [])
        
        for row in data_list:
            FileName = row['VARS_ENTRY_FILE']
            row['VARS_ENTRY_FILE_MD5'] = ""
            row['VARS_ENTRY_FILE_PATH'] = ""
            
            if not FileName is None:
                
                row['VARS_ENTRY_FILE_PATH'] = col_filepath
                row['VARS_ENTRY_FILE_MD5'] = self.md5_file(col_filepath)
                
            if row["COL_SEQ_COMBINATION_ID"] is None or len(row["COL_SEQ_COMBINATION_ID"]) == 0:
                key = row["EXECUTION_NO"] + "_"
                key += row["OPERATION_ID"] + "_"
                key += row["MOVEMENT_ID"] + "_"
                key += row["SYSTEM_ID"] + "_"
                key += row["MVMT_VAR_LINK_ID"] + "_"
                key += "" + "_"
                key += str(row["ASSIGN_SEQ"]) + "_"
                key += row["DISUSE_FLAG"]
            else:
                key = row["EXECUTION_NO"] + "_"
                key += row["OPERATION_ID"] + "_"
                key += row["MOVEMENT_ID"] + "_"
                key += row["SYSTEM_ID"] + "_"
                key += row["MVMT_VAR_LINK_ID"] + "_"
                key += row["COL_SEQ_COMBINATION_ID"] + "_"
                key += str(row["ASSIGN_SEQ"]) + "_"
                key += row["DISUSE_FLAG"]
            
            if row["COL_SEQ_COMBINATION_ID"] is None or len(row["COL_SEQ_COMBINATION_ID"]) == 0:
                in_VarsAssignRecodes[key] = row
            else:
                in_ArryVarsAssignRecodes[key] = row
        
        return True, in_VarsAssignRecodes, in_ArryVarsAssignRecodes
    
    def checkVerticalMenuVarsAssignData(self, lv_tableVerticalMenuList, inout_varsAssList):
        """
        縦メニューでまとまり全てNULLの場合、代入値管理への登録・更新を対象外とする
        
        Arguments:
            lv_tableVerticalMenuList: 縦メニューテーブルのカラム情報配列

        Returns:
            is success:(bool)
            defvarsList: 抽出した変数
        """
        
        chk_vertical_col = {}
        chk_vertical_val = {}
        
        for tbl_name, col_list in lv_tableVerticalMenuList.items():
            for col_name in col_list.values():
                for index, vars_ass_list in inout_varsAssList.items():
                    # 縦メニュー以外はチェック対象外
                    if not tbl_name == vars_ass_list['TABLE_NAME']:
                        continue
                    
                    if not tbl_name == vars_ass_list['COL_NAME']:
                        continue
                    
                    # テーブル名とROW_IDをキーとした代入値チェック用の辞書を作成
                    if tbl_name not in chk_vertical_val:
                        chk_vertical_val[tbl_name] = {}
                    
                    chk_vertical_val[tbl_name] = {}
                    chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']] = {}
                    if vars_ass_list['COL_ROW_ID'] not in chk_vertical_val[tbl_name]:
                        chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['CHK_START'] = False
                        chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['NULL_VAL'] = {}
                        
                    # リピート開始カラムをチェック
                    if col_name == vars_ass_list['START_COL_NAME']:
                        chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['CHK_START'] = True
                        if tbl_name not in chk_vertical_col:
                            chk_vertical_val[tbl_name]['COL_CNT'] = 0
                            chk_vertical_val[tbl_name]['REPEAT_CNT'] = 0
                            chk_vertical_val[tbl_name]['COL_CNT_MAX'] = vars_ass_list['COL_CNT']
                            chk_vertical_val[tbl_name]['REPEAT_CNT_MAX'] = vars_ass_list['REPEAT_CNT']
                    
                    # リピート開始前の場合は次のカラムへ以降
                    if chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['CHK_START'] == 0:
                        continue
                    
                    # 具体値が NULL の場合は、代入値管理登録データのインデックスを保持
                    if vars_ass_list['VARS_ENTRY'] == "":
                        chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['NULL_VAL'] = {}
                        chk_vertical_val[tbl_name][vars_ass_list['COL_ROW_ID']]['NULL_VAL']['INDEX'] = index
                
                # リピート開始前の場合は次のカラムへ以降
                if tbl_name not in chk_vertical_col:
                    continue
                
                # チェック完了済みカラムをカウントアップ
                chk_vertical_col[tbl_name]['COL_CNT'] += 1
                
                # まとまり単位のチェック完了時の場合
                if chk_vertical_col[tbl_name]['COL_CNT'] >= chk_vertical_col[tbl_name]['COL_CNT_MAX']:
                    # まとまり単位の具体値が全て NULL の場合は代入値管理への登録対象外とする
                    if tbl_name in chk_vertical_val:
                        for row_id, vertical_val_info in chk_vertical_val[tbl_name]:
                            if len(vertical_val_info['NULL_VAL']) >= chk_vertical_col[tbl_name]['COL_CNT_MAX']:
                                for index in vertical_val_info['NULL_VAL'].values():
                                    inout_varsAssList[index]['STATUS'] = False
                            # 保持している代入値管理登録データのインデックスをリセット
                            del chk_vertical_val[tbl_name][row_id]['NULL_VAL']
                            chk_vertical_val[tbl_name][row_id]['NULL_VAL'] = {}
                    
                    # リピート数をカウントアップ
                    chk_vertical_col[tbl_name]['REPEAT_CNT'] += 1
                    
                    # チェック完了済みカラムのカウントをリセット
                    chk_vertical_col[tbl_name]['COL_CNT'] = 0
                
                # リピート終了済みの場合は以降のカラムはチェックしない
                if chk_vertical_col[tbl_name]['REPEAT_CNT'] >= chk_vertical_col[tbl_name]['REPEAT_CNT_MAX']:
                    break
        
        return inout_varsAssList
    
    def addStg1StdListVarsAssign(self, in_varsAssignList, execution_no, WS_DB):
        """
        代入値管理（一般変数・複数具体値変数）を更新する。
        
        Arguments:
            in_varsAssignList: 代入値管理更新情報配列
            in_tableNameToMenuIdList: テーブル名配列

        Returns:
            is success:(bool)
        """
        
        global vg_FileUPloadColumnBackupFilePath
        global db_update_flg
        global arrayValueTmplOfVarAss
        
        arrayValue = arrayValueTmplOfVarAss
        db_valautostup_user_id = g.USER_ID

        objmenu = load_table.loadTable(WS_DB, "subst_value_list_ansible_role")
        
        tgt_row = arrayValue
        # 登録する情報設定
        tgt_row['ASSIGN_ID'] = str(WS_DB._uuid_create())
        tgt_row['OPERATION_ID'] = in_varsAssignList['OPERATION_ID']
        tgt_row['MOVEMENT_ID'] = in_varsAssignList['MOVEMENT_ID']
        tgt_row['SYSTEM_ID'] = in_varsAssignList['SYSTEM_ID']
        tgt_row['MVMT_VAR_LINK_ID'] = in_varsAssignList['MVMT_VAR_LINK_ID']
        tgt_row['ASSIGN_SEQ'] = in_varsAssignList['ASSIGN_SEQ']
        
        # 具体値にテンプレート変数が記述されているか判定
        VARS_ENTRY_USE_TPFVARS = "0"
        if type(in_varsAssignList['VARS_ENTRY']) is str:
            ret = in_varsAssignList['VARS_ENTRY'].find('TPF_')
            if ret == 0:
                # テンプレート変数が記述されていることを記録
                VARS_ENTRY_USE_TPFVARS = "1"
                db_update_flg = True
        
        # ロール管理ジャーナルに登録する情報設定
        tgt_row['VARS_ENTRY'] = in_varsAssignList['VARS_ENTRY']
        tgt_row['COL_SEQ_COMBINATION_ID'] = in_varsAssignList['COL_SEQ_COMBINATION_ID']
        if in_varsAssignList['COL_FILEUPLOAD_PATH']:
            tgt_row['VARS_ENTRY_FILE'] = file_encode(in_varsAssignList['COL_FILEUPLOAD_PATH'])
        else:
            tgt_row["VARS_ENTRY_FILE"] = ""
        tgt_row["SENSITIVE_FLAG"] = in_varsAssignList['SENSITIVE_FLAG']
        tgt_row["VARS_ENTRY_USE_TPFVARS"] = VARS_ENTRY_USE_TPFVARS
        tgt_row['DISUSE_FLAG'] = "0"
        tgt_row['LAST_UPDATE_USER'] = db_valautostup_user_id

        tgt_row = self.getLoadtableRegisterValue(tgt_row, True, WS_DB)
        parameter = {
            "item_no": tgt_row['ASSIGN_ID'],
            "execution_no": execution_no,
            "operation": tgt_row['OPERATION_NAME'],
            "movement": tgt_row['MOVEMENT_NAME'],
            "host": tgt_row['HOST_NAME'],
            "variable_name": tgt_row['VARS_NAME'],
            "value": tgt_row['VARS_ENTRY'],
            "sensitive_setting": tgt_row['FLAG_NAME'],
            "substitution_order": tgt_row['ASSIGN_SEQ'],
            "template_variables_used": tgt_row['VARS_ENTRY_USE_TPFVARS'],
            "remarks": tgt_row['NOTE'],
            "discard": tgt_row['DISUSE_FLAG'],
            "last_update_date_time": str(tgt_row['LAST_UPDATE_TIMESTAMP']).replace('-', '/'),
            "last_updated_user": tgt_row['LAST_UPDATE_USER']
        }

        parameters = {
            "parameter": parameter,
            "type": "Register"
        }
            
        if not tgt_row['VARS_ENTRY_FILE'] == "":
            parameter["file"] = "VARS_ENTRY_FILE"
            parameters["file"] = {"vars_entry_file": tgt_row['VARS_ENTRY_FILE']}
                
        retAry = objmenu.exec_maintenance(parameters, "", "", False, False)
            
        result = retAry[0]
        if result is False:
            raise AppException("499-00701", [retAry], [retAry])
        
        return True
    
    def addStg1ArrayVarsAssign(self, in_varsAssignList, in_tableNameToMenuIdList, execution_no, WS_DB):
        """
        代入値管理（多次元配列変数）の廃止レコードの復活またき新規レコード追加
        
        Arguments:
            in_varsAssignList: 代入値管理更新情報配列
            in_tableNameToMenuIdList: テーブル名配列
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
        """

        global arrayValueTmplOfVarAss
        global vg_FileUPloadColumnBackupFilePath
        global db_update_flg

        arrayValue = arrayValueTmplOfVarAss
        db_valautostup_user_id = g.USER_ID
        
        objmenu = load_table.loadTable(WS_DB, "subst_value_list_ansible_role")
        
        tgt_row = arrayValue
            
        # DBの項目ではないがFileUploadCloumn用のディレクトリ作成で必要な項目の初期化
        tgt_row['VARS_ENTRY_FILE_PATH'] = ""
            
        # 登録する情報設定
        tgt_row['ASSIGN_ID'] = str(WS_DB._uuid_create())
        tgt_row['OPERATION_ID'] = in_varsAssignList['OPERATION_ID']
        tgt_row['MOVEMENT_ID'] = in_varsAssignList['MOVEMENT_ID']
        tgt_row['SYSTEM_ID'] = in_varsAssignList['SYSTEM_ID']
        tgt_row['MVMT_VAR_LINK_ID'] = in_varsAssignList['MVMT_VAR_LINK_ID']
        tgt_row['ASSIGN_SEQ'] = in_varsAssignList['ASSIGN_SEQ']
        
        # 具体値にテンプレート変数が記述されているか判定
        VARS_ENTRY_USE_TPFVARS = "0"
        if type(in_varsAssignList['VARS_ENTRY']) is str:
            ret = in_varsAssignList['VARS_ENTRY'].find('TPF_')
            if ret == 0:
                # テンプレート変数が記述されていることを記録
                VARS_ENTRY_USE_TPFVARS = "1"
                db_update_flg = True
        
        # ロール管理ジャーナルに登録する情報設定
        tgt_row['VARS_ENTRY'] = in_varsAssignList['VARS_ENTRY']
        tgt_row['COL_SEQ_COMBINATION_ID'] = in_varsAssignList['COL_SEQ_COMBINATION_ID']
        if in_varsAssignList['COL_FILEUPLOAD_PATH']:
            tgt_row['VARS_ENTRY'] = ""
            tgt_row['VARS_ENTRY_FILE'] = file_encode(in_varsAssignList['COL_FILEUPLOAD_PATH'])
        else:
            tgt_row["VARS_ENTRY_FILE"] = ""

        tgt_row["SENSITIVE_FLAG"] = in_varsAssignList['SENSITIVE_FLAG']
        tgt_row["VARS_ENTRY_USE_TPFVARS"] = VARS_ENTRY_USE_TPFVARS
        tgt_row['DISUSE_FLAG'] = "0"
        tgt_row['LAST_UPDATE_USER'] = db_valautostup_user_id
        
        tgt_row = self.getLoadtableRegisterValue(tgt_row, True, WS_DB)
        parameter = {  
            "item_no": tgt_row['ASSIGN_ID'],
            "execution_no": execution_no,
            "operation": tgt_row['OPERATION_NAME'],
            "movement": tgt_row['MOVEMENT_NAME'],
            "host": tgt_row['HOST_NAME'],
            "variable_name": tgt_row['VARS_NAME'],
            "member_variable_name": tgt_row['COL_COMBINATION_MEMBER_ALIAS'],
            "value": tgt_row['VARS_ENTRY'],
            "sensitive_setting": tgt_row['FLAG_NAME'],
            "substitution_order": tgt_row['ASSIGN_SEQ'],
            "template_variables_used": tgt_row['VARS_ENTRY_USE_TPFVARS'],
            "remarks": tgt_row['NOTE'],
            "discard": tgt_row['DISUSE_FLAG'],
            "last_update_date_time": str(tgt_row['LAST_UPDATE_TIMESTAMP']).replace('-', '/'),
            "last_updated_user": tgt_row['LAST_UPDATE_USER']
        }

        parameters = {
            "parameter": parameter,
            "type":"Register"
        }
        
        if not tgt_row['VARS_ENTRY_FILE'] == "":
            parameter["file"] = in_varsAssignList['VARS_ENTRY']
            parameters["file"] = {"file": tgt_row['VARS_ENTRY_FILE']}
        
        retAry = objmenu.exec_maintenance(parameters, "", "", False, False)
        
        result = retAry[0]
        if result is False:
            raise AppException("499-00701", [retAry], [retAry])
        
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
    
    def getCMDBdata(self, in_tableNameToSqlList, in_tableNameToMenuIdList, in_tabColNameToValAssRowList, in_tableNameToMenuNameRestList, warning_flag, WS_DB):
        """
        CMDB代入値紐付対象メニューから具体値を取得する。
        
        Arguments:
            in_tableNameToSqlList: CMDB代入値紐付メニュー毎のSELECT文配列
            in_tableNameToMenuIdList: テーブル名配列
            in_tabColNameToValAssRowList: カラム情報配列
            in_tableNameToMenuNameRestList: メニュー名(REST)配列
            ina_vars_ass_list: 一般変数・複数具体値変数用 代入値登録情報配列
            ina_array_vars_ass_list: 多次元変数配列変数用 代入値登録情報配列
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
            ina_if_info: インターフェース情報
            in_error_msg: エラーメッセージ
        """
        
        global col_filepath
        
        VariableColumnAry = {}
        VariableColumnAry['T_ANSC_TEMPLATE_FILE'] = {}
        VariableColumnAry['T_ANSC_TEMPLATE_FILE']['ANS_TEMPLATE_VARS_NAME'] = 0
        VariableColumnAry['T_ANSC_CONTENTS_FILE'] = {}
        VariableColumnAry['T_ANSC_CONTENTS_FILE']['CONTENTS_FILE_VARS_NAME'] = 0
        
        # オペ+作業+ホスト+変数の組合せの代入順序 重複確認用
        lv_varsAssChkList = {}
        # オペ+作業+ホスト+変数+メンバ変数の組合せの代入順序 重複確認用
        lv_arrayVarsAssChkList = {}
        
        ina_vars_ass_list = {}
        ina_array_vars_ass_list = {}
        
        continue_flg = 0
        idx = 0
        
        for table_name, sql in in_tableNameToSqlList.items():
            if continue_flg == 1:
                continue

            # トレースメッセージ
            traceMsg = g.appmsg.get_api_message("MSG-10806", [in_tableNameToMenuIdList[table_name]])
            frame = inspect.currentframe().f_back
            g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + traceMsg)
            
            data_list = WS_DB.sql_execute(sql, [AnscConst.DF_ITA_LOCAL_HOST_CNT, AnscConst.DF_ITA_LOCAL_PKEY])
            
            # FETCH行数を取得
            if len(data_list) == 0:
                msgstr = g.appmsg.get_api_message("MSG-10368", [in_tableNameToMenuIdList[table_name]])
                frame = inspect.currentframe().f_back
                g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                # 次のテーブルへ
                continue
            
            for row in data_list:
                # 代入値紐付メニューに登録されているオペレーションIDを確認
                if row['OPERATION_ID'] is None or len(row['OPERATION_ID']) == 0:
                    # オペレーションID未登録
                    msgstr = g.appmsg.get_api_message("MSG-10360", [in_tableNameToMenuIdList[table_name], row[AnscConst.DF_ITA_LOCAL_PKEY]])
                    frame = inspect.currentframe().f_back
                    g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                    
                    warning_flag = 1
                    # 次のデータへ
                    continue
                
                operation_id = row['OPERATION_ID']
                
                # 代入値紐付メニューに登録されているホストIDの紐付確認
                if row[AnscConst.DF_ITA_LOCAL_HOST_CNT] == 0:
                    # ホストIDの紐付不正
                    msgstr = g.appmsg.get_api_message("MSG-10359", [in_tableNameToMenuIdList[table_name], row[AnscConst.DF_ITA_LOCAL_PKEY], row['HOST_ID']])
                    frame = inspect.currentframe().f_back
                    g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                    
                    warning_flag = 1
                    # 次のデータへ
                    continue
                
                # 代入値紐付メニューに登録されているホストIDを確認
                if row['HOST_ID'] is None or len(row['HOST_ID']) == 0:
                    msgstr = g.appmsg.get_api_message("MSG-10361", [in_tableNameToMenuIdList[table_name], row[AnscConst.DF_ITA_LOCAL_PKEY]])
                    frame = inspect.currentframe().f_back
                    g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                    
                    warning_flag = 1
                    # 次のデータへ
                    continue
                
                host_id = row['HOST_ID']
                
                # 代入値自動登録設定に登録されている変数に対応する具体値を取得する
                for col_name, col_val in row.items():
                    col_val_key = col_val
                    
                    # パラメータシート側の項番取得
                    if AnscConst.DF_ITA_LOCAL_PKEY == col_name:
                        col_row_id = col_val
                
                # 具体値カラム以外を除外
                search_list = [AnscConst.DF_ITA_LOCAL_OPERATION_CNT, AnscConst.DF_ITA_LOCAL_HOST_CNT, AnscConst.DF_ITA_LOCAL_DUP_CHECK_ITEM, "OPERATION_ID", "HOST_ID", AnscConst.DF_ITA_LOCAL_PKEY]
                if col_name in search_list:
                    continue_flg = 1
                    continue
                
                # 再度カラムをチェック
                if table_name in in_tabColNameToValAssRowList:
                    if col_name not in in_tabColNameToValAssRowList[table_name]:
                        continue
                
                parameter = {}
                col_val = ""
                
                for col_data in in_tabColNameToValAssRowList[table_name][col_name].values():
                    for tmp_table_name, value in in_tableNameToMenuNameRestList.items():
                        if tmp_table_name == table_name:
                            # パラメータシートから値を取得
                            objmenu = load_table.loadTable(WS_DB, value)
                            mode = "inner"
                            filter_parameter = {"discard": {"LIST": ["0"]}}
                            status_code, tmp_result, msg = objmenu.rest_filter(filter_parameter, mode)
                            parameter = tmp_result[0]['parameter']
                            
                            col_val = parameter[col_data['COLUMN_NAME_REST']]
                            
                            # TPF/CPF変数カラム判定
                            if col_data['REF_TABLE_NAME'] in VariableColumnAry:
                                if col_data['REF_COL_NAME'] in VariableColumnAry[col_data['REF_TABLE_NAME']]:
                                    col_val = "'{{" + col_val + "}}'"
                            
                            # オブジェクト解放
                            del objmenu
                    
                    col_class = self.getColumnClass(col_data['COLUMN_CLASS'], WS_DB)
                    col_name_rest = col_data['COLUMN_NAME_REST']
                    col_filepath = ""
                    col_file_md5 = ""
                    if col_data['COLUMN_CLASS'] == "9" or col_data['COLUMN_CLASS'] == "20":
                        # メニューID取得
                        upload_menu_id = self.getUploadfilesMenuID(in_tableNameToMenuIdList[table_name], WS_DB)
                        col_filepath = ""
                        if not col_val == "":
                            storage_path = os.environ.get('STORAGEPATH') + g.get('ORGANIZATION_ID') + "/" + g.get('WORKSPACE_ID')
                            col_filepath = storage_path + "/uploadfiles/" + upload_menu_id + "/" + col_name_rest + "/" + row[AnscConst.DF_ITA_LOCAL_PKEY]
                            if not os.path.exists(col_filepath):
                                msgstr = g.appmsg.get_api_message("MSG-10166", [table_name, col_name, col_row_id, col_filepath])
                                frame = inspect.currentframe().f_back
                                g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                                warning_flag = 1
                                # 次のデータへ
                                continue
                                
                            col_filepath = col_filepath + "/" + col_val
                            col_file_md5 = self.md5_file(col_filepath)

                    # 代入値管理の登録に必要な情報を生成
                    ret = self.makeVarsAssignData(table_name,
                                        col_name,
                                        col_val,
                                        col_row_id,
                                        col_class,
                                        col_filepath,
                                        col_file_md5,
                                        col_data['NULL_DATA_HANDLING_FLG'],
                                        operation_id,
                                        host_id,
                                        col_data,
                                        ina_vars_ass_list,
                                        lv_varsAssChkList,
                                        ina_array_vars_ass_list,
                                        lv_arrayVarsAssChkList,
                                        in_tableNameToMenuIdList[table_name],
                                        row[AnscConst.DF_ITA_LOCAL_PKEY],
                                        WS_DB)
                    
                    ina_vars_ass_list[idx] = ret[0]
                    ina_array_vars_ass_list[idx] = ret[2]
                    
                    idx += 1

        return ina_vars_ass_list, ina_array_vars_ass_list, warning_flag

    def makeVarsAssignData(self,
                            in_table_name,
                            in_col_name,
                            in_col_val,
                            in_col_row_id,
                            in_col_class,
                            in_col_filepath,
                            in_col_file_md5,
                            in_null_data_handling_flg,
                            in_operation_id,
                            in_host_id,
                            in_col_list,
                            ina_vars_ass_list,
                            ina_vars_ass_chk_list,
                            ina_array_vars_ass_list,
                            ina_array_vars_ass_chk_list,
                            in_menu_id,
                            in_row_id,
                            WS_DB):
        """
        CMDB代入値紐付対象メニューの情報から代入値管理に登録する情報を生成
        
        Arguments:
            in_table_name: テーブル名
            in_col_name: カラム名
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
            str: ファイルのMD5ハッシュ値
        """

        if g.LANGUAGE == 'ja':
            col_name = in_col_list['COLUMN_NAME_JA']
        else:
            col_name = in_col_list['COLUMN_NAME_EN']
        
        # カラムタイプを判定
        if in_col_list['COL_TYPE'] == AnscConst.DF_COL_TYPE_VAL:
            # Value型カラムの場合
            # 具体値が空白か判定
            ret = self.validateValueTypeColValue(in_col_val, in_null_data_handling_flg, in_menu_id, in_row_id, in_col_list['COLUMN_NAME_JA'], WS_DB)
            if ret == 0:
                return ina_vars_ass_list, ina_vars_ass_chk_list, ina_array_vars_ass_list, ina_array_vars_ass_chk_list
            
            # checkAndCreateVarsAssignDataの戻りは判定しない。
            ret = self.checkAndCreateVarsAssignData(in_table_name,
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
                                            in_col_file_md5,
                                            in_col_list['VALUE_SENSITIVE_FLAG'],
                                            ina_vars_ass_chk_list,
                                            ina_array_vars_ass_chk_list,
                                            in_menu_id,
                                            in_col_list['COLUMN_ID'],
                                            "Value",
                                            in_row_id)
            
            ina_vars_ass_list = ret[0]
            ina_vars_ass_chk_list = ret[1]
            ina_array_vars_ass_list = ret[2]
            ina_array_vars_ass_chk_list = ret[3]
        
        if in_col_list['COL_TYPE'] == AnscConst.DF_COL_TYPE_KEY:
            # 具体値が空白か判定
            ret = self.validateKeyTypeColValue(in_col_val, in_menu_id, in_row_id, col_name)
            if ret == 0:
                return ina_vars_ass_list, ina_vars_ass_chk_list, ina_array_vars_ass_list, ina_array_vars_ass_chk_list
            
            # checkAndCreateVarsAssignDataの戻りは判定しない。
            ret = self.checkAndCreateVarsAssignData(in_table_name,
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
                                            in_col_file_md5,
                                            in_col_list['KEY_SENSITIVE_FLAG'],
                                            ina_vars_ass_chk_list,
                                            ina_array_vars_ass_chk_list,
                                            in_menu_id,
                                            in_col_list['COLUMN_ID'],
                                            "Key",
                                            in_row_id)
            
            ina_vars_ass_list = ret[0]
            ina_vars_ass_chk_list = ret[1]
            ina_array_vars_ass_list = ret[2]
            ina_array_vars_ass_chk_list = ret[3]
        
        return ina_vars_ass_list, ina_vars_ass_chk_list, ina_array_vars_ass_list, ina_array_vars_ass_chk_list
    
    def getLoadtableRegisterValue(self, row, exe_flag, WS_DB):
        """
        loadtable.py用の登録情報取得
        
        Arguments:
            row: 代入値管理登録情報
            WS_DB: WorkspaceDBインスタンス

        Returns:
            row: 代入値管理登録情報
        """
        
        # オペレーション名
        sql = "SELECT OPERATION_NAME FROM T_COMN_OPERATION WHERE OPERATION_ID = %s"

        data_list = WS_DB.sql_execute(sql, [row['OPERATION_ID']])
        for data in data_list:
            row['OPERATION_NAME'] = data['OPERATION_NAME']
        
        # Movement名
        sql = "SELECT MOVEMENT_NAME FROM V_ANSR_MOVEMENT WHERE MOVEMENT_ID = %s"

        data_list = WS_DB.sql_execute(sql, [row['MOVEMENT_ID']])
        for data in data_list:
            row['MOVEMENT_NAME'] = data['MOVEMENT_NAME']
        
        # ホスト名
        sql = "SELECT HOST_NAME FROM T_ANSC_DEVICE WHERE SYSTEM_ID = %s"

        data_list = WS_DB.sql_execute(sql, [row['SYSTEM_ID']])
        for data in data_list:
            row['HOST_NAME'] = data['HOST_NAME']
        
        # 代入値管理用のデータ取得
        if exe_flag == 1: 
            # 変数名
            sql = "SELECT MOVEMENT_VARS_NAME FROM V_ANSR_VAL_VARS_LINK WHERE MVMT_VAR_LINK_ID = %s"

            data_list = WS_DB.sql_execute(sql, [row['MVMT_VAR_LINK_ID']])
            for data in data_list:
                row['VARS_NAME'] = data['MOVEMENT_VARS_NAME']
            
            if row['COL_SEQ_COMBINATION_ID'] is not None and not row['COL_SEQ_COMBINATION_ID'] == "":
                sql = "SELECT MOVEMENT_VARS_COL_COMBINATION_MEMBER FROM V_ANSR_VAL_COL_SEQ_COMBINATION WHERE COL_SEQ_COMBINATION_ID = %s"
                data_list = WS_DB.sql_execute(sql, [row['COL_SEQ_COMBINATION_ID']])
                for data in data_list:
                    row['COL_COMBINATION_MEMBER_ALIAS'] = data['MOVEMENT_VARS_COL_COMBINATION_MEMBER']
            else:
                row['COL_COMBINATION_MEMBER_ALIAS'] = ""
            
            # Sensitive設定
            sql = "SELECT FLAG_NAME FROM T_COMN_BOOLEAN_FLAG WHERE FLAG_ID = %s"

            data_list = WS_DB.sql_execute(sql, [row['SENSITIVE_FLAG']])
            for data in data_list:
                row['FLAG_NAME'] = data['FLAG_NAME']
        
        return row
    
    def md5_file(self, file):
        """
        指定したファイルのMD5ハッシュ値を計算する
        
        Arguments:
            file (str): Input file.
        Retruns:
            str: ファイルのMD5ハッシュ値
        """
        md5 = hashlib.md5()
        with open(file, 'rb') as f:
            for block in iter(lambda: f.read(65536), b''):
                md5.update(block)
        return md5.hexdigest()
    
    def validateValueTypeColValue(self, in_col_val, in_null_data_handling_flg, in_menu_id, in_row_id, in_menu_title, WS_DB):
        """
        具体値が空白か判定(Value型)
        
        Arguments:
            in_col_val: 具体値
            in_null_data_handling_flg: 代入値自動登録設定のNULL登録フラグ
            in_menu_id: 紐付メニューID
            in_row_id: 紐付テーブル主キー値
            in_menu_title: 紐付メニュー名

        Returns:
            id: '1':有効    '2':無効
        """
        # 具体値が空白の場合
        if not in_col_val:
            # 具体値が空でも代入値管理NULLデータ連携が有効か判定する
            if not self.getNullDataHandlingID(in_null_data_handling_flg, WS_DB) == '1':
                msgstr = g.appmsg.get_api_message("MSG-10375", [in_menu_id, in_row_id, in_menu_title])
                frame = inspect.currentframe().f_back
                g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
                
                return False
        
        return True
    
    def validateKeyTypeColValue(self, in_col_val, in_menu_id, in_row_id, in_menu_title):
        """
        具体値が空白か判定(Key型)
        
        Arguments:
            in_col_val: 具体値
            in_menu_id: 紐付メニューID
            in_row_id: 紐付テーブル主キー値
            in_menu_title: 紐付メニュー名

        Returns:
            is success:(bool)
        """
        # 具体値が空白の場合
        if not in_col_val:
            msgstr = g.appmsg.get_api_message("MSG-10377", [in_menu_id, in_row_id, in_menu_title])
            frame = inspect.currentframe().f_back
            g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
            
            return False
        
        return True

    def getColumnClass(self, in_col_name, WS_DB):
        """
        マスタからカラムクラス名を取得する
        
        Arguments:
            in_menu_id: 紐付メニューID
            in_col_name: カラム名
            WS_DB: WorkspaceDBインスタンス

        Returns:
            column_class: カラムクラス
        """

        column_class = ""

        sql = " SELECT COLUMN_CLASS_NAME "
        sql += " FROM T_COMN_COLUMN_CLASS "
        sql += " WHERE COLUMN_CLASS_ID = %s "
        sql += " AND DISUSE_FLAG = '0'"
        
        data_list = WS_DB.sql_execute(sql, [in_col_name])

        for data in data_list:
            column_class = data['COLUMN_CLASS_NAME']
        
        return column_class

    def getUploadfilesMenuID(self, in_menu_id, WS_DB):
        """
        紐付メニューの入力用メニューのメニューID取得
        
        Arguments:
            in_menu_id: 紐付メニューID
            WS_DB: WorkspaceDBインスタンス

        Returns:
            out_menu_id: 入力用メニューID
        """

        out_menu_id = ""

        sql = " SELECT TBL_A.MENU_ID, "
        sql += "       TBL_A.MENU_NAME_REST "
        sql += " FROM T_COMN_MENU TBL_A "
        sql += " WHERE TBL_A.MENU_NAME_JA = ( "
        sql += "  SELECT TBL_B.MENU_NAME_JA "
        sql += "  FROM T_COMN_MENU TBL_B "
        sql += "  WHERE TBL_B.MENU_ID = %s)"
        sql += " AND TBL_A.MENU_GROUP_ID = '502'"
        
        data_list = WS_DB.sql_execute(sql, [in_menu_id])

        for data in data_list:
            out_menu_id = data['MENU_ID']
        
        return out_menu_id

    def getNullDataHandlingID(self, in_null_data_handling_flg, WS_DB):
        """
        パラメータシートの具体値がNULLの場合でも代入値管理ら登録するかを判定
        
        Arguments:
            in_null_data_handling_flg: 代入値自動登録設定のNULL登録フラグ
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
        """
        
        global g_null_data_handling_def
        
        # 代入値自動登録設定のNULL登録フラグ判定
        if in_null_data_handling_flg == '1':
            id = '1'
        elif in_null_data_handling_flg == '0':
            id = '2'
        else:
            # インターフェース情報のNULL登録フラグ判定
            if g_null_data_handling_def == '1':
                id = '1'
            elif g_null_data_handling_def == '0':
                id = '2'
        
        return id
    
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
                                    in_col_file_md5,
                                    in_sensitive_flg,
                                    ina_vars_ass_chk_list,
                                    ina_array_vars_ass_chk_list,
                                    in_menu_id,
                                    in_column_id,
                                    keyValueType,
                                    in_row_id):
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
            in_menu_id: 紐付メニューID
            in_column_id: 代入値自動登録設定
            keyValueType: Value/Key
            in_row_id: 紐付テーブル主キー値

        Returns:
            is success:(bool)
        """
        
        chk_status = False
        chk_flg = True
        
        ina_vars_ass_list = {}
        ina_array_vars_ass_list = {}
        
        # 変数のタイプを判定
        if in_vars_attr == AnscConst.GC_VARS_ATTR_STD or in_vars_attr == AnscConst.GC_VARS_ATTR_LIST:
            # 一般変数・複数具体値
            # オペ+作業+ホスト+変数の組合せで代入順序が重複していないか判定
            if in_operation_id in ina_vars_ass_chk_list:
                if in_patten_id in ina_vars_ass_chk_list[in_operation_id]:
                    if in_host_id in ina_vars_ass_chk_list[in_operation_id][in_patten_id]:
                        if in_vars_link_id in ina_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id]:
                            if in_vars_assign_seq in ina_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id][in_vars_link_id]:
                                # 既に登録されている
                                dup_info = ina_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id][in_vars_link_id][in_vars_assign_seq]
                                chk_flg = False
                                
                                msgstr = g.appmsg.get_api_message("MSG-10369", [dup_info['COLUMN_ID'], in_column_id, in_column_id, in_operation_id, in_host_id, keyValueType])
                                frame = inspect.currentframe().f_back
                                g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
            if chk_flg == 1:
                chk_status = True
                # オペ+作業+ホスト+変数+メンバ変数の組合せの代入順序退避
                ina_vars_ass_chk_list[in_operation_id] = {}
                ina_vars_ass_chk_list[in_operation_id][in_patten_id] = {}
                ina_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id] = {}
                ina_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id][in_vars_link_id] = {}
                ina_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id][in_vars_link_id][in_vars_assign_seq] = {'COLUMN_ID': in_column_id}
            
            if in_col_class == "FileUploadColumn" and keyValueType == "Key":
                in_col_file_md5 = ""
            # 代入値管理の登録に必要な情報退避
            ina_vars_ass_list = {'TABLE_NAME': in_table_name,
                                'COL_NAME': in_col_name,
                                'COL_ROW_ID': in_col_row_id,
                                'COL_CLASS': in_col_class,
                                'COL_FILEUPLOAD_PATH': in_col_filepath,
                                'COL_FILEUPLOAD_MD5': in_col_file_md5,
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
            if in_operation_id in ina_array_vars_ass_chk_list:
                if in_patten_id in ina_array_vars_ass_chk_list[in_operation_id]:
                    if in_host_id in ina_array_vars_ass_chk_list[in_operation_id][in_patten_id]:
                        if in_vars_link_id in ina_array_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id]:
                            if in_col_seq_combination_id in ina_array_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id][in_vars_link_id]:
                                if in_vars_assign_seq in ina_array_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id][in_vars_link_id][in_col_seq_combination_id]:
                                    # 既に登録されている
                                    dup_info = ina_array_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id][in_vars_link_id][in_col_seq_combination_id][in_vars_assign_seq]
                                    chk_flg = False
                                    
                                    msgstr = g.appmsg.get_api_message("MSG-10369", [dup_info['COLUMN_ID'], in_column_id, in_column_id, in_operation_id, in_host_id, keyValueType])
                                    frame = inspect.currentframe().f_back
                                    g.applogger.debug(os.path.basename(__file__) + str(frame.f_lineno) + msgstr)
            if chk_flg == 1:
                chk_status = True
                # オペ+作業+ホスト+変数+メンバ変数の組合せの代入順序退避
                ina_array_vars_ass_chk_list[in_operation_id] = {}
                ina_array_vars_ass_chk_list[in_operation_id][in_patten_id] = {}
                ina_array_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id] = {}
                ina_array_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id][in_vars_link_id] = {}
                ina_array_vars_ass_chk_list[in_operation_id][in_patten_id][in_host_id][in_vars_link_id][in_vars_assign_seq] = {'COLUMN_ID': in_column_id}
            
            if in_col_class == "FileUploadColumn" and keyValueType == "Key":
                in_col_file_md5 = ""
            # 代入値管理の登録に必要な情報退避
            ina_array_vars_ass_list = {'TABLE_NAME': in_table_name,
                                'COL_NAME': in_col_name,
                                'COL_ROW_ID': in_col_row_id,
                                'COL_CLASS': in_col_class,
                                'COL_FILEUPLOAD_PATH': in_col_filepath,
                                'COL_FILEUPLOAD_MD5': in_col_file_md5,
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
        
        return ina_vars_ass_list, ina_vars_ass_chk_list, ina_array_vars_ass_list, ina_array_vars_ass_chk_list
    
    def readValAssign(self, movement_id, WS_DB):
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
        sql += "   TBL_B.REF_TABLE_NAME                                        ,  \n"
        sql += "   TBL_B.REF_PKEY_NAME                                         ,  \n"
        sql += "   TBL_B.REF_COL_NAME                                          ,  \n"
        sql += "   TBL_B.COLUMN_CLASS                                          ,  \n"
        sql += "   TBL_B.AUTOREG_HIDE_ITEM                                     ,  \n"
        sql += "   TBL_B.AUTOREG_ONLY_ITEM                                     ,  \n"
        sql += "   TBL_B.DISUSE_FLAG  AS COL_DISUSE_FLAG                       ,  \n"
        sql += "   TBL_A.COL_TYPE                                              ,  \n"
        sql += "   TBL_E.VARS_NAME                                             ,  \n"
        sql += "   TBL_E.VARS_ATTRIBUTE_01                                     ,  \n"
        
        # 代入値管理データ連携フラグ
        sql += "   TBL_A.NULL_DATA_HANDLING_FLG                                ,  \n"
        
        # 作業パターン詳細の登録確認
        sql += "   TBL_A.MOVEMENT_ID                                           ,  \n"
        sql += "   (                                                              \n"
        sql += "     SELECT                                                       \n"
        sql += "       COUNT(*)                                                   \n"
        sql += "     FROM                                                         \n"
        sql += lv_pattern_link_tbl + "                                            \n"
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
        sql += lv_ptn_vars_link_tbl + "                                           \n"
        sql += "     WHERE                                                        \n"
        sql += "       MOVEMENT_ID    = TBL_A.MOVEMENT_ID        AND              \n"
        sql += "       MVMT_VAR_LINK_ID  = TBL_A.MVMT_VAR_LINK_ID  AND            \n"
        sql += "       DISUSE_FLAG   = '0'                                        \n"
        sql += "   ) AS VAL_PTN_VARS_LINK_CNT                                  ,  \n"
        
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
        sql += "       COL_SEQ_COMBINATION_ID = TBL_A.COL_SEQ_COMBINATION_ID AND     \n"
        sql += "       DISUSE_FLAG = '0'                                          \n"
        sql += "   ) AS VAL_COL_COMBINATION_MEMBER_ALIAS                       ,  \n"
        
        # (Val)多次元変数メンバー管理
        sql += "   TBL_A.ASSIGN_SEQ                                            ,  \n"
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
        sql += lv_ptn_vars_link_tbl + "                                           \n"
        sql += "     WHERE                                                        \n"
        sql += "       MOVEMENT_ID    = TBL_A.MOVEMENT_ID        AND              \n"
        sql += "       MVMT_VAR_LINK_ID  = TBL_A.MVMT_VAR_LINK_ID  AND            \n"
        sql += "       DISUSE_FLAG   = '0'                                        \n"
        sql += "   ) AS KEY_PTN_VARS_LINK_CNT                                  ,  \n"
        
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
        sql += "       COL_SEQ_COMBINATION_ID = TBL_A.COL_SEQ_COMBINATION_ID AND     \n"
        sql += "       DISUSE_FLAG = '0'                                          \n"
        sql += "   ) AS KEY_COL_COMBINATION_MEMBER_ALIAS                       ,  \n"
        
        # (Key)多次元変数メンバー管理
        sql += "   TBL_A.ASSIGN_SEQ                                            ,  \n"
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
        sql += lv_val_assign_tbl + "  TBL_A                                       \n"
        sql += "   LEFT JOIN T_COMN_MENU_COLUMN_LINK TBL_B ON                     \n"
        sql += "          (TBL_A.COLUMN_LIST_ID = TBL_B.COLUMN_DEFINITION_ID)     \n"
        sql += "          OR (TBL_B.AUTOREG_ONLY_ITEM = 1)                        \n"
        sql += "   LEFT JOIN T_COMN_MENU_TABLE_LINK          TBL_C ON             \n"
        sql += "          (TBL_B.MENU_ID        = TBL_C.MENU_ID)                  \n"
        sql += "   LEFT JOIN T_COMN_MENU   TBL_D ON                               \n"
        sql += "          (TBL_C.MENU_ID        = TBL_D.MENU_ID)                  \n"
        sql += "   LEFT JOIN T_ANSR_MVMT_VAR_LINK TBL_E ON                        \n"
        sql += "          (TBL_A.MVMT_VAR_LINK_ID    = TBL_E.MVMT_VAR_LINK_ID)    \n"
        sql += " WHERE                                                            \n"
        sql += "   TBL_A.DISUSE_FLAG='0'                                          \n"
        sql += "   AND TBL_A.MOVEMENT_ID = %s                                     \n"
        sql += "   AND TBL_C.DISUSE_FLAG='0'                                      \n"
        sql += "   AND TBL_B.AUTOREG_HIDE_ITEM = '0'                              \n"
        sql += " ORDER BY TBL_A.COLUMN_ID                                         \n"

        data_list = WS_DB.sql_execute(sql, [movement_id])

        inout_tableNameToMenuIdList = {}
        inout_tabColNameToValAssRowList = {}
        inout_tableNameToMenuNameRestList = {}
        idx = 0
        for data in data_list:
            # SHEET_TYPEが1(ホスト・オペレーション)で廃止レコードでないかを判定
            if data['ANSIBLE_TARGET_TABLE'] != '0':
                msgstr = g.appmsg.get_api_message("MSG-10437", [data['COLUMN_ID']])
                # 次のカラムへ
                raise ValidationException("MSG-10437", [data['COLUMN_ID']])
            
            # 作業パターン詳細に作業パターンが未登録
            if data['PATTERN_CNT'] == '0':
                msgstr = g.appmsg.get_api_message("MSG-10336", [data['COLUMN_ID']])
                # 次のカラムへ
                raise ValidationException("MSG-10336", [data['COLUMN_ID']])
            
            # CMDB代入値紐付メニューが登録されているか判定
            if data['TABLE_NAME'] is None or len(data['TABLE_NAME']) == 0:
                msgstr = g.appmsg.get_api_message("MSG-10338", [data['COLUMN_ID']])
                # 次のカラムへ
                raise ValidationException("MSG-10338", [data['COLUMN_ID']])
            
            # CMDB代入値紐付メニューのカラムが未登録か判定
            if data['COL_NAME'] is None or len(data['COL_NAME']) == 0:
                msgstr = g.appmsg.get_api_message("MSG-10340", [data['COLUMN_ID']])
                # 次のカラムへ
                raise ValidationException("MSG-10340", [data['COLUMN_ID']])
            
            type_chk = [AnscConst.DF_COL_TYPE_VAL, AnscConst.DF_COL_TYPE_KEY]
            col_type = data['COL_TYPE']
            if col_type not in type_chk:
                msgstr = g.appmsg.get_api_message("MSG-10341", [data['COLUMN_ID']])
                # 次のカラムへ
                raise ValidationException("MSG-10341", [data['COLUMN_ID']])
            
            # Value型変数の変数タイプ
            val_vars_attr = ""
            key_vars_attr = ""
            
            # Key項目・Value項目の検査（当該レコード）
            # カラムタイプにより処理分岐
            
            if col_type == AnscConst.DF_COL_TYPE_VAL:
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
                                                "VAL_ASSIGN_SEQ_NEED")
            
                if ret[0] == 0:
                    continue
                
                val_vars_attr = ret[1]
            
            if col_type == AnscConst.DF_COL_TYPE_KEY:
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
                                                "KEY_ASSIGN_SEQ_NEED")
            
                if ret[0] == 0:
                    continue
                
                key_vars_attr = ret[1]

            inout_tableNameToMenuIdList[data['TABLE_NAME']] = data['MENU_ID']
            inout_tableNameToMenuNameRestList[data['TABLE_NAME']] = data['MENU_NAME_REST']
            
            # PasswordColumnかを判定
            key_sensitive_flg = AnscConst.DF_SENSITIVE_OFF
            value_sensitive_flg = AnscConst.DF_SENSITIVE_OFF
            if data['COLUMN_CLASS'] == '8' or data['COLUMN_CLASS'] == '26':
                value_sensitive_flg = AnscConst.DF_SENSITIVE_ON
            
            if data['TABLE_NAME'] not in inout_tabColNameToValAssRowList:
                inout_tabColNameToValAssRowList[data['TABLE_NAME']] = {}
            if data['COL_NAME'] not in inout_tabColNameToValAssRowList[data['TABLE_NAME']]:
                inout_tabColNameToValAssRowList[data['TABLE_NAME']][data['COL_NAME']] = {}
                idx = 0
            
            inout_tabColNameToValAssRowList[data['TABLE_NAME']][data['COL_NAME']][idx] = {
                                                                            'COLUMN_ID': data['COLUMN_ID'],
                                                                            'COL_TYPE': data['COL_TYPE'],
                                                                            'COLUMN_CLASS': data['COLUMN_CLASS'],
                                                                            'COLUMN_NAME_JA': data['COLUMN_NAME_JA'],
                                                                            'COLUMN_NAME_EN': data['COLUMN_NAME_EN'],
                                                                            'COLUMN_NAME_REST': data['COLUMN_NAME_REST'],
                                                                            'REF_TABLE_NAME': data['REF_TABLE_NAME'],
                                                                            'REF_PKEY_NAME': data['REF_PKEY_NAME'],
                                                                            'REF_COL_NAME': data['REF_COL_NAME'],
                                                                            'MOVEMENT_ID': data['MOVEMENT_ID'],
                                                                            'MVMT_VAR_LINK_ID': data['MVMT_VAR_LINK_ID'],
                                                                            'VAL_VAR_TYPE': val_vars_attr,
                                                                            'COL_SEQ_COMBINATION_ID': data['COL_SEQ_COMBINATION_ID'],
                                                                            'VAL_COL_COMBINATION_MEMBER_ALIAS': data['VAL_COL_COMBINATION_MEMBER_ALIAS'],
                                                                            'ASSIGN_SEQ': data['ASSIGN_SEQ'],
                                                                            'VALUE_SENSITIVE_FLAG': value_sensitive_flg,
                                                                            'KEY_VAR_TYPE': key_vars_attr,
                                                                            'NULL_DATA_HANDLING_FLG': data['NULL_DATA_HANDLING_FLG'],
                                                                            'KEY_SENSITIVE_FLAG': key_sensitive_flg}
        
            # テーブルの主キー名退避
            pk_name = WS_DB.table_columns_get(data['TABLE_NAME'])
            inout_tableNameToPKeyNameList[data['TABLE_NAME']] = {}
            inout_tableNameToPKeyNameList[data['TABLE_NAME']] = pk_name[1][0]
            idx += 1

        return True, inout_tableNameToMenuIdList, inout_tabColNameToValAssRowList, inout_tableNameToPKeyNameList, inout_tableNameToMenuNameRestList
    
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
                            in_assign_seq_need):
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
            g.applogger.debug(msgstr)
            return False, inout_vars_attr
        
        # 変数が作業パターン変数紐付にあるか判定
        if row[in_ptn_vars_link_cnt] is None or len(str(row[in_ptn_vars_link_cnt])) == 0:
            msgstr = g.appmsg.get_api_message("MSG-10348", [row['COLUMN_ID'], in_col_type])
            g.applogger.debug(msgstr)
            return False, inout_vars_attr
        
        # 設定されている変数が変数一覧にあるか判定
        if row[in_vars_name] is None or len(str(row[in_vars_name])) == 0:
            msgstr = g.appmsg.get_api_message("MSG-10345", [row['COLUMN_ID'], in_col_type])
            g.applogger.debug(msgstr)
            return False, inout_vars_attr

        if row[in_vars_attribute_01] in [AnscConst.GC_VARS_ATTR_STD, AnscConst.GC_VARS_ATTR_LIST, AnscConst.GC_VARS_ATTR_M_ARRAY]:
            inout_vars_attr = row[in_vars_attribute_01]
        else:
            msgstr = g.appmsg.get_api_message("MSG-10439", [row['COLUMN_ID'], in_col_type])
            g.applogger.debug(msgstr)
            return False, inout_vars_attr
        
        # メンバー変数がメンバー変数一覧にあるか判定
        if inout_vars_attr == AnscConst.GC_VARS_ATTR_M_ARRAY:
            # メンバー変数の選択判定
            if row[in_col_seq_combination_id] is None or len(row[in_col_seq_combination_id]) == 0:
                msgstr = g.appmsg.get_api_message("MSG-10419", [row['COLUMN_ID'], in_col_type])
                g.applogger.debug(msgstr)
                return False, inout_vars_attr
        
            # カラムタイプ型に設定されているメンバー変数がメンバー変数一覧にあるか判定
            if row[in_col_combination_member_alias] is None or len(row[in_col_combination_member_alias]) == 0:
                msgstr = g.appmsg.get_api_message("MSG-10349", [row['COLUMN_ID'], in_col_type])
                g.applogger.debug(msgstr)
                return False, inout_vars_attr
        else:
            if not row[in_col_seq_combination_id] is None and not len(row[in_col_seq_combination_id]) == 0:
                msgstr = g.appmsg.get_api_message("MSG-10418", [row['COLUMN_ID'], in_col_type])
                g.applogger.debug(msgstr)
                return False, inout_vars_attr
        
        if inout_vars_attr == AnscConst.GC_VARS_ATTR_LIST:
            if row[in_assign_seq] is None or len(str(row[in_assign_seq])) == 0:
                msgstr = g.appmsg.get_api_message("MSG-10350", [row['COLUMN_ID'], in_col_type])
                g.applogger.debug(msgstr)
                return False, inout_vars_attr
        
        elif inout_vars_attr == AnscConst.GC_VARS_ATTR_M_ARRAY:
            if row[in_assign_seq_need] == 1:
                if row[in_assign_seq] is None or row[in_assign_seq] == 0:
                    msgstr = g.appmsg.get_api_message("MSG-10350", [row['COLUMN_ID'], in_col_type])
                    g.applogger.debug(msgstr)
                    return False, inout_vars_attr
        
        return True, inout_vars_attr

    def extract_tpl_vars(self, var_extractor, varsAssRecord, template_list, host_list):

        # 処理対象外のデータかを判定
        if len(varsAssRecord) == 0:
            return template_list, host_list
        if varsAssRecord['STATUS'] == 0:
            return template_list, host_list

        movement_id = varsAssRecord['MOVEMENT_ID']
        vars_line_array = [] # [{行番号:変数名}, ...]
        if type(varsAssRecord['VARS_ENTRY']) is str:
            is_success, vars_line_array = var_extractor.SimpleFillterVerSearch("TPF_", varsAssRecord['VARS_ENTRY'], vars_line_array, [], [])
            if len(vars_line_array) == 1:
                if movement_id not in template_list:
                    template_list[movement_id] = {}
                row_num, tpf_var_name = vars_line_array[0]
                template_list[movement_id][tpf_var_name] = 0

        # 作業対象ホストの情報を退避
        if movement_id not in host_list:
            host_list[movement_id] = {}
        operation_id = varsAssRecord['OPERATION_ID']
        if operation_id not in host_list[movement_id]:
            host_list[movement_id][operation_id] = {}
        host_list[movement_id][operation_id][varsAssRecord['SYSTEM_ID']] = 0

        return template_list, host_list
