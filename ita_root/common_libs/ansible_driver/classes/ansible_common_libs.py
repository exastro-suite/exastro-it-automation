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
Ansible共通module
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


class AnsibleCommonLibs():
    """
    Ansible共通class
    F0001  set_run_mode
    F0002  GetRunMode
    F0003  getCPFVarsMaster
    F0004  chkCPFVarsMasterReg
    F0005  getTPFVarsMaster
    F0006  chkTPFVarsMasterReg
    F0007  getGBLVarsMaster
    F0008  chkGBLVarsMasterReg
    F0009  CommonVarssAanalys
    F0010  selectDBRecodes
    """
    
    # 定数定義
    LV_RUN_MODE = ""
    
    # ローカル変数(全体)宣言
    lv_val_assign_tbl = 'T_ANSR_VALUE_AUTOREG'
    lv_pattern_link_tbl = 'T_ANSR_MVMT_MATL_LINK'
    lv_ptn_vars_link_tbl = 'T_ANSR_MVMT_VAR_LINK'
    lv_member_col_comb_tbl = 'T_ANSR_NESTVAR_MEMBER_COL_COMB'
    lv_array_member_tbl = 'T_ANSR_NESTVAR_MEMBER'
    strCurTableVarsAss = 'T_ANSR_VALUE'
    strJnlTableVarsAss = strCurTableVarsAss + "_JNL"
    strSeqOfCurTableVarsAss = strCurTableVarsAss + "_RIC"
    strSeqOfJnlTableVarsAss = strCurTableVarsAss + "_JSQ"
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
        "VAL_COL_SEQ_COMBINATION_ID": "",
        "SENSITIVE_FLAG": "",
        "VARS_ENTRY_FILE": "",
        "VARS_ENTRY_USE_TPFVARS": "",
        "ASSIGN_SEQ": "",
        "DISP_SEQ": "",
        "DISUSE_FLAG": "",
        "NOTE": "",
        "LAST_UPDATE_TIMESTAMP": "",
        "LAST_UPDATE_USER": ""}

    def __init__(self, run_mode=AnscConst.LC_RUN_MODE_STD):
        global LV_RUN_MODE
        LV_RUN_MODE = run_mode

    def set_run_mode(self, run_mode):
        """
        処理モードを変数定義ファイルチェックに設定

        Arguments:
            run_mode: 処理モード　LC_RUN_MODE_STD/LC_RUN_MODE_VARFILE
        """
        global LV_RUN_MODE
        LV_RUN_MODE = run_mode

    def get_run_mode(self):
        """
        処理モード取得

        returns:
            処理モード　LC_RUN_MODE_STD/LC_RUN_MODE_VARFILE
        """
        return LV_RUN_MODE

    def get_cpf_vars_master(self, in_cpf_var_name, WS_DB):
        """
        ファイル管理の情報をデータベースより取得する。
        
        Arguments:
            in_cpf_var_name: CPF変数名
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
            in_cpf_key: PKey格納変数
            in_cpf_file_name: ファイル格納変数
        """
        
        in_cpf_key = ""
        in_cpf_file_name = ""
        
        where = "WHERE  CONTENTS_FILE_VARS_NAME = '" + in_cpf_var_name + "' and DISUSE_FLAG = '0'"
        
        data_list = WS_DB.table_select("T_ANSC_CONTENTS_FILE", where, [])

        if len(data_list) < 1:
            return True, in_cpf_key, in_cpf_file_name
        
        for data in data_list:
            in_cpf_key = data["CONTENTS_FILE_ID"]
            in_cpf_file_name = data["CONTENTS_FILE"]
        
        return True, in_cpf_key, in_cpf_file_name

    def chk_cpf_vars_master_reg(self, ina_cpf_vars_list, WS_DB):
        """
        CPF変数がファイル管理に登録されているか判定
        
        Arguments:
            ina_cpf_vars_list: CPF変数リスト
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
            tmp_ina_cpf_vars_list: CPF変数リスト
            in_errmsg: エラーメッセージ
        """
        bool_ret = True
        fatal_error = False
        in_errmsg = ""
        tmp_ina_cpf_vars_list = {}
        
        ams = AnsibleMakeMessage()
        
        # CPF変数がファイル管理に登録されているか判定
        for role_name, tgt_file_list in ina_cpf_vars_list.items():
            for tgt_file, line_no_list in tgt_file_list.items():
                for line_no, cpf_var_name_list in line_no_list.items():
                    for cpf_var_name, dummy in cpf_var_name_list.items():
                        
                        # CPF変数名からファイル管理とPkeyを取得する。
                        ret = self.get_cpf_vars_master(cpf_var_name, WS_DB)
                        
                        # CPF変数名が未登録の場合
                        if ret[1] == "":
                            if in_errmsg != "":
                                in_errmsg = in_errmsg + "\n"
                            
                            in_errmsg = in_errmsg + ams.AnsibleMakeMessage(self.get_run_mode(), "MSG-10408", [role_name, tgt_file, line_no, cpf_var_name])
                            bool_ret = False
                            break
                        else:
                            # ファイル名が未登録の場合
                            if ret[2] == "":
                                if in_errmsg != "":
                                    in_errmsg = in_errmsg + "\n"
                            
                                in_errmsg = in_errmsg + ams.AnsibleMakeMessage(self.get_run_mode(), "MSG-10409", [role_name, tgt_file, line_no, cpf_var_name])
                                bool_ret = False
                                continue
                        
                        if role_name not in tmp_ina_cpf_vars_list:
                            tmp_ina_cpf_vars_list[role_name] = {}
                        if tgt_file not in tmp_ina_cpf_vars_list[role_name]:
                            tmp_ina_cpf_vars_list[role_name][tgt_file] = {}
                        if line_no not in tmp_ina_cpf_vars_list[role_name][tgt_file]:
                            tmp_ina_cpf_vars_list[role_name][tgt_file][line_no] = {}
                        if cpf_var_name not in tmp_ina_cpf_vars_list[role_name][tgt_file][line_no]:
                            tmp_ina_cpf_vars_list[role_name][tgt_file][line_no][cpf_var_name] = {}

                        tmp_ina_cpf_vars_list[role_name][tgt_file][line_no][cpf_var_name]['CONTENTS_FILE_ID'] = ret[1]
                        tmp_ina_cpf_vars_list[role_name][tgt_file][line_no][cpf_var_name]['CONTENTS_FILE'] = ret[2]
                        
                    if fatal_error:
                        break
                    
                if fatal_error:
                    break
            
            if fatal_error:
                break

        return bool_ret, tmp_ina_cpf_vars_list, in_errmsg
    
    def get_tpf_vars_master(self, in_tpf_var_name, WS_DB):
        """
        テンプレート管理の情報をデータベースより取得する。
        
        Arguments:
            in_cpf_var_name: TPF変数名
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
            ina_row: 登録情報
        """
        
        where = "WHERE  ANS_TEMPLATE_VARS_NAME = '" + in_tpf_var_name + "' AND DISUSE_FLAG = '0'"
        
        data_list = WS_DB.table_select("T_ANSC_TEMPLATE_FILE", where, [])
        
        ina_row = []
        
        if len(data_list) < 1:
            return True, ina_row
        
        for data in data_list:
            ina_row.append(data)
        
        return True, ina_row
    
    def chk_tpf_vars_master_reg(self, ina_tpf_vars_list, WS_DB):
        """
        TPF変数がテンプレート管理に登録されているか判定
        
        Arguments:
            ina_tpf_vars_list: TPF変数リスト
            WS_DB: WorkspaceDBインスタンス

        Returns:
            is success:(bool)
            ina_tpf_vars_list: TPF変数リスト
            in_errmsg: エラーメッセージ
        """
        
        bool_ret = True
        in_errmsg = ""
        fatal_error = False
        tmp_ina_tpf_vars_list = {}
        
        ams = AnsibleMakeMessage()
        
        # TPF変数にファイル管理に登録されているか判定
        for role_name, tgt_file_list in ina_tpf_vars_list.items():
            for tgt_file, line_no_list in tgt_file_list.items():
                for line_no, tpf_var_name_list in line_no_list.items():
                    for tpf_var_name, dummy in tpf_var_name_list.items():
                        ret = self.get_tpf_vars_master(tpf_var_name, WS_DB)
                        
                        tpf_key = ""
                        tpf_file_name = ""
                        role_only_flag = ""
                        vars_list = ""
                        var_struct_anal_json_string = ""
                        
                        if len(ret[1]) != 0:
                            tpf_key = ret[1][0]['ANS_TEMPLATE_ID']
                            tpf_file_name = ret[1][0]['ANS_TEMPLATE_FILE']
                            role_only_flag = ret[1][0]['ROLE_ONLY_FLAG']
                            vars_list = ret[1][0]['VARS_LIST']
                            var_struct_anal_json_string = ret[1][0]['VAR_STRUCT_ANAL_JSON_STRING']
                        
                        # TPF変数名が未登録の場合
                        if tpf_key == "":
                            if in_errmsg != "":
                                in_errmsg = in_errmsg + "\n"
                            
                            in_errmsg = in_errmsg + ams.AnsibleMakeMessage(self.get_run_mode(), "MSG-10559", [role_name, tgt_file, line_no, tpf_var_name])
                            bool_ret = False
                            continue
                        
                        else:
                            if tpf_var_name == "":
                                if in_errmsg != "":
                                    in_errmsg = in_errmsg + "\n"
                            
                                in_errmsg = in_errmsg + ams.AnsibleMakeMessage(self.get_run_mode(), "MSG-10557", [role_name, tgt_file, line_no, tpf_var_name])
                                bool_ret = False
                                continue
                        
                        if role_name not in tmp_ina_tpf_vars_list:
                            tmp_ina_tpf_vars_list[role_name] = {}
                        if tgt_file not in tmp_ina_tpf_vars_list[role_name]:
                            tmp_ina_tpf_vars_list[role_name][tgt_file] = {}
                        if line_no not in tmp_ina_tpf_vars_list[role_name][tgt_file]:
                            tmp_ina_tpf_vars_list[role_name][tgt_file][line_no] = {}
                        if tpf_var_name not in tmp_ina_tpf_vars_list[role_name][tgt_file][line_no]:
                            tmp_ina_tpf_vars_list[role_name][tgt_file][line_no][tpf_var_name] = {}
                        
                        tmp_ina_tpf_vars_list[role_name][tgt_file][line_no][tpf_var_name]['CONTENTS_FILE_ID'] = tpf_key
                        tmp_ina_tpf_vars_list[role_name][tgt_file][line_no][tpf_var_name]['CONTENTS_FILE'] = tpf_file_name
                        tmp_ina_tpf_vars_list[role_name][tgt_file][line_no][tpf_var_name]['ROLE_ONLY_FLAG'] = role_only_flag
                        tmp_ina_tpf_vars_list[role_name][tgt_file][line_no][tpf_var_name]['VARS_LIST'] = vars_list
                        tmp_ina_tpf_vars_list[role_name][tgt_file][line_no][tpf_var_name]['VAR_STRUCT_ANAL_JSON_STRING'] = var_struct_anal_json_string
                        
                        if fatal_error:
                            break
                        
                    if fatal_error:
                        break
                
                if fatal_error:
                    break
                
        return bool_ret, tmp_ina_tpf_vars_list, in_errmsg
    
    def get_gbl_vars_master(self, in_gbl_var_name, WS_DB):
        """
        グローバル管理の情報をデータベースより取得する。
        
        Arguments:
            in_gbl_var_name: GBL変数名
            WS_DB: WorkspaceDBインスタンス
    
        Returns:
            is success:(bool)
            in_gbl_key: PKey格納変数
        """

        in_gbl_key = ""
        
        where = "WHERE VARS_NAME = '" + in_gbl_var_name + "' AND DISUSE_FLAG = '0'"
        
        data_list = WS_DB.table_select("T_ANSC_GLOBAL_VAR", where, [])
        
        if len(data_list) < 1:
            return True, in_gbl_key
        
        for data in data_list:
            in_gbl_key = data['GBL_VARS_NAME_ID']
        
        return True, in_gbl_key
        
    def chk_gbl_vars_master_reg(self, ina_gbl_vars_list, WS_DB):
        """
        GBL変数がファイル管理に登録されているか判定
        
        Arguments:
            ina_gbl_vars_list: GBL変数リスト
            WS_DB: WorkspaceDBインスタンス
    
        Returns:
            is success:(bool)
            ina_gbl_vars_list: GBL変数リスト
            in_errmsg: エラーメッセージ
        """
        
        bool_ret = True
        fatal_error = False
        in_errmsg = ""
        tmp_ina_gbl_vars_list = {}
        
        ams = AnsibleMakeMessage()
        
        # GBL変数にファイル管理に登録されているか判定
        for role_name, tgt_file_list in ina_gbl_vars_list.items():
            for tgt_file, line_no_list in tgt_file_list.items():
                for line_no, gbl_var_name_list in line_no_list.items():
                    for gbl_var_name, dummy in gbl_var_name_list.items():
                        
                        ret = self.get_gbl_vars_master(gbl_var_name, WS_DB)
                        
                        # GBL変数名が未登録の場合
                        if ret[1] == "":
                            if in_errmsg != "":
                                in_errmsg = in_errmsg + "\n"
                            
                            in_errmsg = in_errmsg + ams.AnsibleMakeMessage(self.get_run_mode(), "MSG-10571", [role_name, tgt_file, line_no, gbl_var_name])
                            bool_ret = False
                            break
                        
                        if role_name not in tmp_ina_gbl_vars_list:
                            tmp_ina_gbl_vars_list[role_name] = {}
                        if tgt_file not in tmp_ina_gbl_vars_list[role_name]:
                            tmp_ina_gbl_vars_list[role_name][tgt_file] = {}
                        if line_no not in tmp_ina_gbl_vars_list[role_name][tgt_file]:
                            tmp_ina_gbl_vars_list[role_name][tgt_file][line_no] = {}
                        if line_no not in tmp_ina_gbl_vars_list[role_name][tgt_file][line_no]:
                            tmp_ina_gbl_vars_list[role_name][tgt_file][line_no][gbl_var_name] = {}
    
                        tmp_ina_gbl_vars_list[role_name][tgt_file][line_no][gbl_var_name]['CONTENTS_FILE_ID'] = ret[1]
                        
                    if fatal_error:
                        break
                    
                if fatal_error:
                    break
            
            if fatal_error:
                break
        
        return bool_ret, ina_gbl_vars_list, in_errmsg
    
    def common_varss_aanalys(self, in_filename, out_filename, fillter_vars=False):
        """
        Legacy/PioneerでアップロードされるPlaybook素材よの共通変数を抜き出す
        FileUploadColumn:checkTempFileBeforeMoveOnPreLoadイベント用
        
        Arguments:
            in_filename: アップロードされたデータが格納されているファイル名

        Returns:
            ret_array: is success, エラーメッセージ
        """

        bool_ret = True
        
        playbook_data_string = open(in_filename)
        
        local_vars = []
        vars_line_array = []
        vars_array = []
        str_err_msg = None
        
        wsra = WrappedStringReplaceAdmin()
        # インベントリ追加オプションに定義されている変数を抜き出す。
        ret = wsra.SimpleFillterVerSearch("CPF_", playbook_data_string, vars_line_array, vars_array, local_vars, fillter_vars)

        cpf_vars_list = []
        for vars_info, no in ret[1]:
            for var_name, line_no in vars_info:
                cpf_vars_list['dummy']['Upload file'][line_no][var_name] = 0
                
        ret = wsra.SimpleFillterVerSearch("TPF_", playbook_data_string, vars_line_array, vars_array, local_vars, fillter_vars)
        
        tpf_vars_list = []
        for vars_info, no in ret[1]:
            for var_name, line_no in vars_info:
                tpf_vars_list['dummy']['Upload file'][line_no][var_name] = 0
        
        ret = wsra.SimpleFillterVerSearch("GBL_", playbook_data_string, vars_line_array, vars_array, local_vars, fillter_vars)
        
        gbl_vars_list = []
        for vars_info, no in ret[1]:
            for var_name, line_no in vars_info:
                gbl_vars_list['dummy']['Upload file'][line_no][var_name] = 0
        
        gbl_vars = '1'
        cpf_vars = '2'
        tpf_vars = '3'
        save_vars_list = []
        save_vars_list[gbl_vars] = []
        save_vars_list[cpf_vars] = []
        save_vars_list[tpf_vars] = []
        
        if bool_ret:
            for tgt_file_list, role_name in cpf_vars_list:
                for line_no_list, tgt_file in tgt_file_list:
                    for cpf_var_name_list, line_no in line_no_list:
                        for dummy, cpf_var_name in cpf_var_name_list:
                            save_vars_list[cpf_vars][cpf_var_name] = 0
        
        if bool_ret:
            for tgt_file_list, tgt_file_list in tpf_vars_list:
                for line_no_list, tgt_file in tgt_file_list:
                    for tpf_var_name_list, line_no in line_no_list:
                        for dummy, tpf_var_name in tpf_var_name_list:
                            save_vars_list[tpf_vars][tpf_var_name] = 0
        
        if bool_ret:
            for tgt_file_list, tgt_file_list in gbl_vars_list:
                for line_no_list, tgt_file in tgt_file_list:
                    for gbl_var_name_list, line_no in line_no_list:
                        for dummy, gbl_var_name in gbl_var_name_list:
                            save_vars_list[gbl_var_name][tpf_var_name] = 0
                            
        if bool_ret:
            json_encode = json.dump(save_vars_list)
            path = out_filename
            
            try:
                Path(path).write_text(json_encode, encoding="utf-8")
            except Exception:
                bool_ret = False
                str_err_msg = g.appmsg.get_api_message('MSG-10570', [])
        
        if len(str_err_msg) != 0:
            str_err_msg.replace('\n', '<BR>')
        
        ret_array = list[bool_ret, str_err_msg]
        
        return ret_array
    
    def select_db_recodes(self, in_sql, in_key, WS_DB):
        """
        指定されたデータベースの全有効レコードを取得する。
        
        Arguments:
            in_sql: SQL
            in_key: 登録レコードの配列のキー項目
            WS_DB: WorkspaceDBインスタンス

        Returns:
            ina_row: 取得レコードの配列
        """
        
        data_list = WS_DB.sql_execute(in_sql, [])
        
        ina_row = {}
        for data in data_list:
            ina_row[data[in_key]] = data
        
        return ina_row
    
    def GetDataFromParameterSheet(self, WS_DB, exec_type, operation_id="", movement_id="", execution_no=""):
        """
        代入値自動登録とパラメータシートを抜く
        
        定義のみ
        """
        
        return True