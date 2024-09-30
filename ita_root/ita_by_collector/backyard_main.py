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
import inspect
import datetime
import base64
import json
import subprocess
import shutil

from flask import g

from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs
from common_libs.common.util import get_upload_file_path, file_encode
from common_libs.loadtable import *
from common_libs.ansible_driver.classes.YamlParseClass import YamlParse
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.CreateAnsibleExecFiles import CreateAnsibleExecFiles
from common_libs.ansible_driver.functions.util import getAnsibleConst, getDataRelayStorageDir
import traceback
from common_libs.common.util import arrange_stacktrace_format
from common_libs.common.util import get_iso_datetime
from common_libs.common.util import print_exception_msg


def addFuncionsPerOrchestrator(varOrchestratorId, strRPathFromOrcLibRoot):

    boolRet = False

    try:
        varOrchestratorId = int(varOrchestratorId)
        if varOrchestratorId < 1:
            raise Exception()

        if isinstance(strRPathFromOrcLibRoot, str) is False:
            raise Exception()

        boolRet = True

    except Exception:
        pass

    return boolRet


def getInfoFromTablename(dbAccess, TableName, strTempForSql="", where_list=[]):

    cols = dbAccess.table_columns_get(TableName)
    cols = (',').join(cols[0])
    sql = (
        "SELECT \n"
        "  %s   \n"
        "FROM   \n"
        "  `%s` \n"
    ) % (cols, TableName)

    if strTempForSql:
        sql = "%s%s\n" % (sql, strTempForSql)

    rset = dbAccess.sql_execute(sql, where_list)

    return rset


def getTargetPath(TargetPath, file_paths):

    if os.path.isdir(TargetPath) is False:
        return False

    filelist = os.listdir(TargetPath)
    for f in filelist:
        filepath = '%s/%s' % (TargetPath.rstrip('/'), f)
        if os.path.isdir(filepath) is True:
            file_paths = getTargetPath(filepath, file_paths)

        else:
            file_paths.append(filepath)

    return file_paths


def is_num(s):
    try:
        float(s)
    except ValueError:
        return False
    else:
        return True


def yamlParseAnalysis(strTargetfile):

    arrVarsList = {}

    obj = YamlParse()
    arrTargetParm = obj.Parse(strTargetfile)
    if not arrTargetParm:
        return False

    php_array = lambda x: x.items() if isinstance(x, dict) else enumerate(x)
    for key1, value1 in php_array(arrTargetParm):
        if type(value1) not in (list, dict):
            if key1 not in arrVarsList:
                arrVarsList[key1] = None

            arrVarsList[key1] = value1

        else:
            for key2, value2 in php_array(value1):
                if type(value2) not in (list, dict) and is_num(key2):
                    if key1 not in arrVarsList:
                        arrVarsList[key1] = {}

                    str_key2 = '[%s]' % (key2)
                    if str(key2) not in arrVarsList[key1]:
                        arrVarsList[key1][str_key2] = None

                    arrVarsList[key1][str_key2] = value2

            in_fastarry_f = ""
            in_var_name = ""
            in_var_name_path = ""
            ina_parent_var_array = value1
            ina_vars_chain_list = {}
            in_error_code = ""
            in_line = ""
            in_col_count = 0
            in_assign_count = 0
            ina_parent_var_key = 0
            in_chl_var_key = 0
            in_nest_lvl = 1

            result, ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count, in_chl_var_key = MakeMultiArrayToFirstVarChainArray(
                in_fastarry_f, in_var_name, in_var_name_path, ina_parent_var_array,
                ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count,
                ina_parent_var_key, in_chl_var_key, in_nest_lvl
            )

            if type(result) in (dict, list):
                for key2, value2 in php_array(result):
                    for key3, value3 in php_array(value2):
                        if type(value3['VAR_VALUE']) not in (list, dict):
                            if key1 not in arrVarsList:
                                arrVarsList[key1] = {}

                            if value3['VAR_NAME_PATH'] not in arrVarsList[key1]:
                                arrVarsList[key1][value3['VAR_NAME_PATH']] = None

                            if arrVarsList[key1][value3['VAR_NAME_PATH']] is not None:
                                arrVarsList[key1][value3['VAR_NAME_PATH']].append(value3['VAR_VALUE'])

                            else:
                                arrVarsList[key1][value3['VAR_NAME_PATH']] = value3['VAR_VALUE']

                        else:
                            for key4, value4 in php_array(value3['VAR_VALUE']):
                                if is_num(key4) and type(value4) not in (list, dict):
                                    keyname = '%s[%s]' % (value3['VAR_NAME_PATH'], key4)
                                    arrVarsList.setdefault(key1, {})
                                    arrVarsList[key1][keyname] = value4

    return arrVarsList


def MakeMultiArrayToFirstVarChainArray(
    in_fastarry_f, in_var_name, in_var_name_path, ina_parent_var_array,
    ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count,
    ina_parent_var_key, in_chl_var_key, in_nest_lvl
):

    demiritta_ch = "."
    in_nest_lvl = in_nest_lvl + 1
    parent_var_key = ina_parent_var_key
    ret = is_assoc(ina_parent_var_array)
    if ret == -1:
        in_error_code = "MSG-10302"
        in_line = inspect.currentframe().f_lineno
        return False, ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count, in_chl_var_key

    fastarry_f_on = False
    php_array = lambda x: x.items() if isinstance(x, dict) else enumerate(x)
    for var, val in php_array(ina_parent_var_array):
        col_array_f = ""
        if is_num(var):
            if type(val) not in (list, dict):
                continue

            else:
                col_array_f = "I"

        MultiValueVar_f = chkMultiValueVariableSub(val)
        if len(in_var_name) > 0:
            wk_var_name_path = '%s%s%s' % (in_var_name_path, demiritta_ch, var)
            if is_num(var):
                wk_var_name_path = '%s[%s]' % (in_var_name_path, var)

            if is_num(in_var_name_path):
                wk_var_name_path = '[%s].%s' % (in_var_name_path, var)

            if is_num(var) is False:
                wk_var_name = '%s%s%s' % (in_var_name, demiritta_ch, var)

            else:
                wk_var_name = in_var_name

        else:
            wk_var_name_path = str(var)
            wk_var_name = str(var)

        # 配列の開始かを判定する
        if col_array_f == "I":
            if in_fastarry_f is False:
                in_fastarry_f = True
                fastarry_f_on = True

        in_chl_var_key = in_chl_var_key + 1
        if parent_var_key not in ina_vars_chain_list:
            ina_vars_chain_list[parent_var_key] = {}

        if in_chl_var_key not in ina_vars_chain_list[parent_var_key]:
            ina_vars_chain_list[parent_var_key][in_chl_var_key] = {}

        ina_vars_chain_list[parent_var_key][in_chl_var_key]['VAR_NAME'] = var
        ina_vars_chain_list[parent_var_key][in_chl_var_key]['NEST_LEVEL'] = in_nest_lvl
        ina_vars_chain_list[parent_var_key][in_chl_var_key]['LIST_STYLE'] = "0"
        ina_vars_chain_list[parent_var_key][in_chl_var_key]['VAR_NAME_PATH'] = wk_var_name_path
        ina_vars_chain_list[parent_var_key][in_chl_var_key]['VAR_NAME_ALIAS'] = wk_var_name
        ina_vars_chain_list[parent_var_key][in_chl_var_key]['ARRAY_STYLE'] = "0"
        ina_vars_chain_list[parent_var_key][in_chl_var_key]['VAR_VALUE'] = val

        MultiValueVar_f = chkMultiValueVariableSub(val)
        if MultiValueVar_f is True:
            ina_vars_chain_list[parent_var_key][in_chl_var_key]['LIST_STYLE'] = "5"

        #  配列の中の変数の場合
        if in_fastarry_f is True:
            ina_vars_chain_list[parent_var_key][in_chl_var_key]['ARRAY_STYLE'] = "1"

        if type(val) not in (list, dict):
            continue

        ret, ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count, in_chl_var_key = MakeMultiArrayToFirstVarChainArray(
            in_fastarry_f, wk_var_name, wk_var_name_path, val,
            ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count,
            in_chl_var_key, in_chl_var_key, in_nest_lvl
        )

        if ret is False:
            return False, ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count, in_chl_var_key

        # 配列開始のマークを外す
        if fastarry_f_on is True:
            in_fastarry_f = False

    return ina_vars_chain_list, ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count, in_chl_var_key


def is_assoc(in_array):

    key_int = False
    key_char = False
    if type(in_array) not in (list, dict):
        return -1

    php_keys = lambda x: x.keys() if isinstance(x, dict) else range(len(x))
    keys = php_keys(in_array)
    for value in keys:
        if isinstance(value, int):
            key_int = True

        else:
            key_char = True

    if key_char and key_int:
        return -1

    if key_char:
        return "C"

    return "I"


def chkMultiValueVariableSub(in_var_array):

    if type(in_var_array) in (list, dict):
        if len(in_var_array) <= 0:
            return True

        php_array = lambda x: x.items() if isinstance(x, dict) else enumerate(x)
        for key, chk_array in php_array(in_var_array):
            if is_num(key) is False:
                return False

            if type(chk_array) in (list, dict):
                return False

        return True

    return False


def backyard_main(organization_id, workspace_id):

    g.applogger.debug("backyard_main ita_by_collector called")

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # 実行準備
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    php_array = lambda x: x.items() if isinstance(x, dict) else enumerate(x)
    yml_array = lambda x: php_array(x) if type(x) in (list, dict) else enumerate([x])
    bdl_array = lambda x: x.items() if 'parameter' not in x else enumerate([x])

    intErrorFlag = 0
    intWarningFlag = 0
    menu_restcol_info = {}
    upload_restcol_info = {}
    bandle_menus = []

    NOTICE_FLG = 1  # 1:収集済み

    ansible_driver_id_info = {
        '1' : {
            'id' : 'L',
            'LOGPATH' : '%s/uploadfiles/20210/COLLECT_LOG/%%s' % (getDataRelayStorageDir())
        },
        '2' : {
            'id' : 'P',
            'LOGPATH' : '%s/uploadfiles/20312/COLLECT_LOG/%%s' % (getDataRelayStorageDir())
        },
        '3' : {
            'id' : 'R',
            'LOGPATH' : '%s/uploadfiles/20412/COLLECT_LOG/%%s' % (getDataRelayStorageDir())
        }
    }

    arrCollectOrcList = {
        '1': {'table_name': 'T_ANSL_EXEC_STS_INST', 'rest_name': 'execution_list_ansible_legacy'},
        '2': {'table_name': 'T_ANSP_EXEC_STS_INST', 'rest_name': 'execution_list_ansible_pioneer'},
        '3': {'table_name': 'T_ANSR_EXEC_STS_INST', 'rest_name': 'execution_list_ansible_role'},
    }

    # 環境情報設定
    # 言語情報
    if getattr(g, 'LANGUAGE', None) is None:
        g.LANGUAGE = 'en'

    if getattr(g, 'USER_ID', None) is None:
        g.USER_ID = '20103'

    try:
        ################################
        # DBコネクト
        ################################
        g.applogger.debug("db connect.")
        dbAccess = DBConnectWs()

        condition = 'WHERE `DISUSE_FLAG`=0'
        ans_if_info = dbAccess.table_select('T_ANSC_IF_INFO', condition)
        ans_if_info = ans_if_info[0]

        ################################
        # 各オーケストレータ情報の収集
        ################################
        sql = (
            "SELECT "
            "  ORCHESTRA_ID, "
            "  ORCHESTRA_NAME, "
            "  ORCHESTRA_PATH "
            "FROM "
            "  T_COMN_ORCHESTRA "
            "WHERE "
            "  DISUSE_FLAG = '0' "
            "ORDER BY "
            "  DISP_SEQ ASC "
        )

        aryOrcListRow = dbAccess.sql_execute(sql)
        for arySingleOrcInfo in aryOrcListRow:
            if arySingleOrcInfo['ORCHESTRA_ID'] in arrCollectOrcList:
                strOrcIdNumeric = arySingleOrcInfo['ORCHESTRA_ID']
                strOrcRPath = arySingleOrcInfo['ORCHESTRA_PATH']
                ret = addFuncionsPerOrchestrator(strOrcIdNumeric, strOrcRPath)
                if ret is False:
                    strErrStepIdInFx = "00000200-([FILE]%s,[LINE]%s)" % (os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno)
                    raise Exception(strErrStepIdInFx)

        del aryOrcListRow

        ################################
        # 収取ステータスマスターを抽出
        ################################
        collect_sts_info = {}

        sql = (
            "SELECT "
            "  COLLECT_STATUS_ID, "
            "  COLLECT_STATUS_NAME_JA, "
            "  COLLECT_STATUS_NAME_EN "
            "FROM "
            "  T_ANSC_COLLECT_STATUS "
            "WHERE "
            "  DISUSE_FLAG = '0' "
            "ORDER BY "
            "  DISP_SEQ "
        )

        rset = dbAccess.sql_execute(sql)
        for r in rset:
            sts_id = r['COLLECT_STATUS_ID']
            sts_key = 'COLLECT_STATUS_NAME_%s' % (g.LANGUAGE.upper())

            if sts_id not in collect_sts_info:
                collect_sts_info[sts_id] = ''

            if sts_key in r:
                collect_sts_info[sts_id] = r[sts_key]

        ################################
        # オーケストレータ順に実施
        ################################
        for intCollectOrcNo, dicCollectOrc in sorted(arrCollectOrcList.items(), key=lambda x:int(x[0])):
            strCollectOrcTablename = dicCollectOrc['table_name']
            strCollectOrcRestname = dicCollectOrc['rest_name']
            objmenu_orch = load_table.loadTable(dbAccess, strCollectOrcRestname)

            # 収集対象のMovement一覧を取得
            strTempForSql = (
                "SELECT "
                "  EXECUTION_NO "
                "FROM "
                "  %s "
                "WHERE "
                "  STATUS_ID IN (%%s, %%s, %%s, %%s, %%s) "
                "AND COLLECT_STATUS IS NULL "
                "AND DISUSE_FLAG IN ('0') "
                "ORDER BY "
                "  EXECUTION_NO ASC "
            ) % (strCollectOrcTablename)
            arySqlBind = [AnscConst.COMPLETE, AnscConst.FAILURE, AnscConst.EXCEPTION, AnscConst.SCRAM, AnscConst.RESERVE_CANCEL]
            exec_no_list = dbAccess.sql_execute(strTempForSql, arySqlBind)

            try:
                # Movement毎に実施
                for exec_no in exec_no_list:
                    dbAccess.db_transaction_start()
                    strTempForSql = "WHERE EXECUTION_NO = %s "
                    arySqlBind = [exec_no['EXECUTION_NO'], ]
                    aryMovements = getInfoFromTablename(dbAccess, strCollectOrcTablename, strTempForSql, arySqlBind)
                    aryMovement = aryMovements[0]

                    NOTICE_FLG = 1  # 1:収集済み
                    RESTEXEC_FLG = 0
                    FREE_LOG = ""
                    collection_log = ""

                    driver_id = ansible_driver_id_info[intCollectOrcNo]['id']
                    execNo = aryMovement['EXECUTION_NO']
                    operation_id = aryMovement['OPERATION_ID']
                    last_update_timestamp = str(aryMovement['LAST_UPDATE_TIMESTAMP'])

                    ans_const = getAnsibleConst(driver_id)
                    ansdrv = CreateAnsibleExecFiles(driver_id, ans_if_info, execNo, "", aryMovement['I_ANSIBLE_CONFIG_FILE'], dbAccess)
                    ret_val = ansdrv.getAnsibleWorkingDirectories(ans_const.vg_OrchestratorSubId_dir, execNo)

                    strCollectBasePath = ret_val[0]
                    strCollectTargetPath = ''
                    strCollectTargetPath_in = '%s/_parameters' % (ret_val[3])
                    strCollectTargetPath_out = '%s/_parameters' % (ret_val[4])
                    strCollectTargetFilesPath_in = '%s/_parameters_file' % (ret_val[3])
                    strCollectTargetFilesPath_out = '%s/_parameters_file' % (ret_val[4])
                    tmpCollectlogdir = ansible_driver_id_info[intCollectOrcNo]['LOGPATH'] % (execNo)
                    tmpCollectlogfile = 'CollectData_%s.log' % (execNo)
                    strCollectlogPath = '%s/%s' % (tmpCollectlogdir, tmpCollectlogfile)

                    # 完了以外の場合
                    if aryMovement['STATUS_ID'] != AnscConst.COMPLETE:
                        request_param = {}
                        request_param['type'] = load_table.CMD_UPDATE
                        request_param['file'] = {}
                        request_param['parameter'] = {}
                        request_param['parameter']['execution_no'] = execNo
                        request_param['parameter']['collection_status'] = collect_sts_info['3'] if '3' in collect_sts_info else ''  # 3:対象外
                        request_param['parameter']['last_update_date_time'] = last_update_timestamp
                        if len(collection_log) > 0:
                            request_param['file']['collection_log'] = base64.b64encode(collection_log.encode()).decode()
                            request_param['parameter']['collection_log'] = tmpCollectlogfile

                        ret = objmenu_orch.exec_maintenance(request_param, request_param['parameter']['execution_no'], load_table.CMD_UPDATE, pk_use_flg=False, auth_check=False)
                        if ret[0] is False:
                            dbAccess.db_rollback()
                        else:
                            dbAccess.db_commit()

                    # 完了の場合
                    else:
                        aryRetBody = []
                        strCollectTargetPath = strCollectTargetPath_in
                        arrTargetfiles = getTargetPath(strCollectTargetPath_in, aryRetBody)
                        if not arrTargetfiles:
                            aryRetBody = []
                            strCollectTargetPath = strCollectTargetPath_out
                            arrTargetfiles = getTargetPath(strCollectTargetPath_out, aryRetBody)

                        aryRetBody = []
                        arrTargetUploadfiles = getTargetPath(strCollectTargetFilesPath_in, aryRetBody)
                        if not arrTargetUploadfiles:
                            aryRetBody = []
                            arrTargetUploadfiles = getTargetPath(strCollectTargetFilesPath_out, aryRetBody)

                        # Operationの取得、確認
                        strTempForSql = "WHERE OPERATION_ID = %s AND DISUSE_FLAG IN ('0') ORDER BY OPERATION_ID ASC "
                        arySqlBind = [operation_id, ]
                        aryOperation = getInfoFromTablename(dbAccess, "V_COMN_OPERATION", strTempForSql, arySqlBind)

                        # Operationが廃止済み
                        if len(aryOperation) <= 0:
                            FREE_LOG = g.appmsg.get_api_message("MSG-10854", [operation_id,])
                            g.applogger.debug(FREE_LOG)
                            collection_log = '%s\n%s' % (collection_log, FREE_LOG) if collection_log else FREE_LOG
                            NOTICE_FLG = 4  # 4:収集エラー

                        # 対象のファイル無しの場合
                        elif isinstance(arrTargetfiles, list) is False or len(arrTargetfiles) <= 0:
                            FREE_LOG = g.appmsg.get_api_message("MSG-10857")
                            g.applogger.debug(FREE_LOG)
                            collection_log = '%s\n%s' % (collection_log, FREE_LOG) if collection_log else FREE_LOG
                            NOTICE_FLG = 3  # 3:対象外

                        # 対象のファイル有の場合
                        else:
                            aryOperation = aryOperation[0]

                            resultprm = {}
                            arrTargetLists = {}
                            arrTargetUploadLists = {}
                            arrTargetUploadListFullpath = {}
                            intParseTypeID = 1  # 1:yaml

                            # 対象ホスト、ファイルのリスト作成
                            for strTargetfile in arrTargetfiles:
                                targetHosts = strTargetfile.replace(strCollectTargetPath, "").split('/')
                                if targetHosts[1] not in arrTargetLists:
                                    arrTargetLists[targetHosts[1]] = []

                                arrTargetLists[targetHosts[1]].append(strTargetfile)

                            # パラメータ取得変換
                            for strTargetHost, arrfileslists in arrTargetLists.items():
                                for strTargetfile in arrfileslists:
                                    targetFileName = os.path.splitext(os.path.basename(strTargetfile))[0]
                                    tmpresultprm = yamlParseAnalysis(strTargetfile)

                                    # yaml形式の場合
                                    if type(tmpresultprm) in (list, dict):
                                        if strTargetHost not in resultprm:
                                            resultprm[strTargetHost] = {}

                                        if targetFileName not in resultprm[strTargetHost]:
                                            resultprm[strTargetHost][targetFileName] = None

                                        resultprm[strTargetHost][targetFileName] = tmpresultprm

                                    # 収集対象の形式でない場合
                                    else:
                                        FREE_LOG = g.appmsg.get_api_message("MSG-10858", [strTargetHost, targetFileName])
                                        g.applogger.debug(FREE_LOG)
                                        collection_log = '%s\n%s' % (collection_log, FREE_LOG) if collection_log else FREE_LOG
                                        NOTICE_FLG = 3  # 3:対象外

                            # 対象ホスト、ファイルのリスト作成
                            if isinstance(arrTargetUploadfiles, list) is True:
                                for strTargetUploadfile in arrTargetUploadfiles:
                                    targetHosts = strTargetUploadfile.replace(strCollectTargetPath, "").split('/')
                                    keyname = os.path.splitext(os.path.basename(strTargetUploadfile))[0]
                                    if targetHosts[1] not in arrTargetUploadLists:
                                        arrTargetUploadLists[targetHosts[1]] = {}

                                    if keyname not in arrTargetUploadLists[targetHosts[1]]:
                                        arrTargetUploadLists[targetHosts[1]][keyname] = None

                                    if arrTargetUploadLists[targetHosts[1]][keyname] is None:
                                        arrTargetUploadLists[targetHosts[1]][keyname] = strTargetUploadfile

                                    if targetHosts[1] not in arrTargetUploadListFullpath:
                                        arrTargetUploadListFullpath[targetHosts[1]] = {}

                                    if strTargetUploadfile not in arrTargetUploadListFullpath[targetHosts[1]]:
                                        arrTargetUploadListFullpath[targetHosts[1]][strTargetUploadfile] = None

                                    if arrTargetUploadListFullpath[targetHosts[1]][strTargetUploadfile] is None:
                                        arrTargetUploadListFullpath[targetHosts[1]][strTargetUploadfile] = strTargetUploadfile

                            # ホスト毎に実施
                            for hostname, parmdata in resultprm.items():
                                # ホスト名の取得、確認
                                strTempForSql = "WHERE HOST_NAME = %s AND DISUSE_FLAG IN ('0') ORDER BY SYSTEM_ID ASC "
                                arySqlBind = [hostname, ]
                                aryhostInfo = getInfoFromTablename(dbAccess, "T_ANSC_DEVICE", strTempForSql, arySqlBind)

                                arrTableForMenuInfo = {}

                                # ホストが存在しない
                                if len(aryhostInfo) <= 0:
                                    FREE_LOG = g.appmsg.get_api_message("MSG-10852", [hostname,])
                                    collection_log = '%s\n%s' % (collection_log, FREE_LOG) if collection_log else FREE_LOG
                                    NOTICE_FLG = 4  # 4:収集エラー
                                    if RESTEXEC_FLG == 1:
                                        NOTICE_FLG = 2  # 収集済み(通知あり)

                                else:
                                    aryhostInfo = aryhostInfo[0]
                                    hostid = aryhostInfo['SYSTEM_ID']

                                    arrSqlinsertParm = {}
                                    arrFileUploadList = {}

                                    # ソースファイルからパラメータ整形(ファイル名、メニューID、項目名、値)
                                    for filename, vardata in parmdata.items():
                                        for varname, varvalue in vardata.items():
                                            for varmember, varmembermembervalue in yml_array(varvalue):
                                                strTempForSql = (
                                                    "SELECT "
                                                    "  TAB_C.MENU_ID, "
                                                    "  TAB_D.MENU_NAME_REST, "
                                                    "  TAB_C.TABLE_NAME, "
                                                    "  TAB_C.VERTICAL, "
                                                    "  TAB_A.INPUT_ORDER, "
                                                    "  TAB_B.COLUMN_NAME_REST, "
                                                    "  TAB_B.COLUMN_CLASS "
                                                    "FROM "
                                                    "  T_ANSC_CMDB_LINK TAB_A "
                                                    "LEFT OUTER JOIN "
                                                    "  T_COMN_MENU_COLUMN_LINK TAB_B "
                                                    "ON "
                                                    "  TAB_A.COLUMN_LIST_ID = TAB_B.COLUMN_DEFINITION_ID "
                                                    "LEFT OUTER JOIN "
                                                    "  T_COMN_MENU_TABLE_LINK TAB_C "
                                                    "ON "
                                                    "  TAB_B.MENU_ID = TAB_C.MENU_ID "
                                                    "LEFT OUTER JOIN "
                                                    "  T_COMN_MENU TAB_D "
                                                    "ON "
                                                    "  TAB_B.MENU_ID = TAB_D.MENU_ID "
                                                    "WHERE "
                                                    "  TAB_C.HOSTGROUP = '0' "
                                                    "AND TAB_A.PARSE_TYPE_ID = %s "
                                                    "AND TAB_A.FILE_PREFIX = %s "
                                                    "AND TAB_A.VARS_NAME = %s "
                                                )
                                                arySqlBind = [intParseTypeID, filename, varname]

                                                # 配列、ハッシュ構造の場合(メンバー変数名あり)
                                                if type(varvalue) in (list, dict):
                                                    strTempForSql += "AND TAB_A.VRAS_MEMBER_NAME = %s "
                                                    arySqlBind.append(varmember)

                                                strTempForSql += (
                                                    "AND TAB_A.DISUSE_FLAG IN ('0') "
                                                    "ORDER BY TAB_C.MENU_ID ASC, TAB_A.COLUMN_LIST_ID ASC "
                                                )

                                                retResult = dbAccess.sql_execute(strTempForSql, arySqlBind)
                                                for tmpvalue in retResult:
                                                    menu_id = tmpvalue['MENU_ID']
                                                    menu_name = tmpvalue['MENU_NAME_REST']
                                                    col_name = tmpvalue['COLUMN_NAME_REST']
                                                    vertical_flag = True if tmpvalue['VERTICAL'] != '0' else False
                                                    input_order = tmpvalue['INPUT_ORDER']

                                                    # パラメーターシートへの登録要求フォーマットを作成
                                                    if menu_name not in menu_restcol_info:
                                                        menu_restcol_info[menu_name] = []
                                                        upload_restcol_info[menu_name] = []

                                                        strTempForSql = (
                                                            "SELECT "
                                                            "  COLUMN_NAME_REST, "
                                                            "  COLUMN_CLASS "
                                                            "FROM "
                                                            "  T_COMN_MENU_COLUMN_LINK "
                                                            "WHERE "
                                                            "  MENU_ID = %s "
                                                            "AND "
                                                            "  DISUSE_FLAG = '0' "
                                                            "ORDER BY "
                                                            "  COLUMN_DISP_SEQ ASC "
                                                        )
                                                        arySqlBind = [menu_id, ]
                                                        rset = dbAccess.sql_execute(strTempForSql, arySqlBind)
                                                        for r in rset:
                                                            menu_restcol_info[menu_name].append(r['COLUMN_NAME_REST'])
                                                            if r['COLUMN_CLASS'] in ["9", "20"]:  # 9 or 20:ファイルアップロード
                                                                upload_restcol_info[menu_name].append(r['COLUMN_NAME_REST'])

                                                    if menu_name not in arrSqlinsertParm:
                                                        arrSqlinsertParm[menu_name] = {}

                                                    if vertical_flag and input_order not in arrSqlinsertParm[menu_name]:
                                                        arrSqlinsertParm[menu_name][input_order] = {}

                                                    tmp_param = {}
                                                    if vertical_flag:
                                                        tmp_param = arrSqlinsertParm[menu_name][input_order]

                                                    else:
                                                        tmp_param = arrSqlinsertParm[menu_name]

                                                    if not tmp_param:
                                                        tmp_param['type'] = ''
                                                        tmp_param['file'] = {}
                                                        tmp_param['parameter'] = {}
                                                        tmp_param['input_file'] = []

                                                        if vertical_flag:
                                                            tmp_param['parameter']['input_order'] = input_order

                                                    if filename not in tmp_param['input_file']:
                                                        tmp_param['input_file'].append(filename)

                                                    # パラメーターシートへの登録要求情報をセット
                                                    tmp_param['parameter'][col_name] = varmembermembervalue
                                                    if tmpvalue['COLUMN_CLASS'] in ["9", "20"]:  # 9 or 20:ファイルアップロード
                                                        if col_name not in tmp_param['file']:
                                                            tmp_param['file'][col_name] = ''

                                                        # ファイルアップロード対象リストのファイルデータをセット
                                                        upload_filepath = {}
                                                        if hostname in arrTargetUploadLists and varmembermembervalue in arrTargetUploadLists[hostname]:
                                                            upload_filepath = arrTargetUploadLists[hostname][varmembermembervalue]

                                                        elif hostname in arrTargetUploadListFullpath:
                                                            for tmpfilekey, tmparrfilepath in arrTargetUploadListFullpath[hostname].items():
                                                                if (tmpfilekey == varmembermembervalue) or (tmpfilekey.endswith(varmembermembervalue)):
                                                                    upload_filepath = tmparrfilepath
                                                                    break

                                                        if upload_filepath:
                                                            tmp_param['file'][col_name] = upload_filepath
                                                            # パス指定時、ファイル名で、parameterを上書き
                                                            # parameter /xxxx/filename -> filename
                                                            tmp_param['parameter'][col_name] = os.path.basename(upload_filepath)

                                                    # バンドル使用のメニュー名を保持
                                                    if vertical_flag and menu_name not in bandle_menus:
                                                        bandle_menus.append(menu_name)

                                    if len(arrSqlinsertParm) <= 0:
                                        # 収集項目値管理上の対象ファイル無しの場合
                                        FREE_LOG = g.appmsg.get_api_message("MSG-10856")
                                        collection_log = '%s\n%s' % (collection_log, FREE_LOG) if collection_log else FREE_LOG
                                        NOTICE_FLG = 3  # 3:対象外
                                        if RESTEXEC_FLG == 1:
                                            NOTICE_FLG = 2  # 収集済み(通知あり)

                                    else:
                                        for menu_name, tmparr in arrSqlinsertParm.items():
                                            objmenu = load_table.loadTable(dbAccess, menu_name)
                                            rec_cnt = 0
                                            fail_cnt = 0
                                            output_flag = True
                                            for input_order, tmparr3 in bdl_array(tmparr):
                                                filename = tmparr3.pop('input_file')
                                                uploadFiles = tmparr3["file"]
                                                del tmparr3["file"]
                                                if output_flag is True:
                                                    FREE_LOG1 = g.appmsg.get_api_message("MSG-10849", [hostname, filename])
                                                    collection_log = '%s\n%s' % (collection_log, FREE_LOG1) if collection_log else FREE_LOG1
                                                    output_flag = False

                                                vertical_flag = True if menu_name in bandle_menus else False

                                                # 項目のないパラメーターシートは収集エラー
                                                # 11 or 12: uuid, host, ope_name1, ope_name2, base_dt, ope_dt, last_exe, (order), note, discard, last_dt, last_user
                                                least_item_count = 12 if vertical_flag else 11
                                                req_param_item_count = len(menu_restcol_info[menu_name])
                                                if least_item_count >= req_param_item_count:
                                                    FREE_LOG = g.appmsg.get_api_message("MSG-10850")
                                                    g.applogger.debug(FREE_LOG)
                                                    collection_log = '%s\n%s' % (collection_log, FREE_LOG) if collection_log else FREE_LOG

                                                    FREE_LOG = g.appmsg.get_api_message("MSG-10855", [hostname, menu_name, operation_id])
                                                    g.applogger.debug(FREE_LOG)
                                                    collection_log = '%s\n%s' % (collection_log, FREE_LOG) if collection_log else FREE_LOG
                                                    NOTICE_FLG = 2  # 2:収集エラー

                                                else:
                                                    try:
                                                        # 言語設定を変更:パラメータシートに対する処理中のみ
                                                        op_language = aryOperation.get('LANGUAGE')
                                                        if op_language and op_language in ['ja', 'en']:
                                                            setattr(g, 'LANGUAGE', op_language)

                                                        # now = (datetime.datetime.now()).strftime('%Y/%m/%d %H:%M:%S')

                                                        # 既存のレコードを抽出
                                                        filter_info = {}
                                                        filter_info['discard'] = {'LIST': ['0']}
                                                        filter_info['operation_name_select'] = {'LIST': [aryOperation['OPERATION_DATE_NAME']]}
                                                        filter_info['host_name'] = {'LIST': [hostname]}
                                                        if vertical_flag:
                                                            filter_info['input_order'] = {'RANGE': {'START':input_order, 'END':input_order}}

                                                        sts, params, msg = objmenu.rest_filter(filter_info, 'inner')

                                                        # 既存レコードがなければ「登録」
                                                        if len(params) <= 0 or 'parameter' not in params[0]:
                                                            tmparr3['type'] = load_table.CMD_REGISTER
                                                            tmparr3['parameter']['uuid'] = None
                                                            tmparr3['parameter']['host_name'] = hostname
                                                            tmparr3['parameter']['operation_name_select'] = aryOperation['OPERATION_DATE_NAME']
                                                            tmparr3['parameter']['base_datetime'] = None
                                                            tmparr3['parameter']['operation_date'] = None
                                                            tmparr3['parameter']['last_execute_timestamp'] = None
                                                            tmparr3['parameter']['discard'] = '0'
                                                            tmparr3['parameter']['remarks'] = None
                                                            tmparr3['parameter']['last_update_date_time'] = None
                                                            tmparr3['parameter']['last_updated_user'] = g.USER_ID

                                                        # 既存レコードがあれば「更新」
                                                        else:
                                                            param = params[0]['parameter']

                                                            tmparr3['type'] = load_table.CMD_UPDATE
                                                            tmparr3['parameter']['uuid'] = param['uuid']
                                                            tmparr3['parameter']['host_name'] = param['host_name']
                                                            tmparr3['parameter']['operation_name_select'] = param['operation_name_select']
                                                            tmparr3['parameter']['base_datetime'] = param['base_datetime']
                                                            tmparr3['parameter']['operation_date'] = param['operation_date']
                                                            tmparr3['parameter']['last_execute_timestamp'] = param['last_execute_timestamp']
                                                            tmparr3['parameter']['discard'] = '0'
                                                            tmparr3['parameter']['remarks'] = param['remarks']
                                                            tmparr3['parameter']['last_update_date_time'] = param['last_update_date_time']
                                                            tmparr3['parameter']['last_updated_user'] = g.USER_ID
                                                            for k, v in param.items():
                                                                if k not in tmparr3['parameter']:
                                                                    tmparr3['parameter'][k] = v

                                                        # 登録、更新
                                                        RESTEXEC_FLG = 1
                                                        rec_cnt = rec_cnt + 1

                                                        ret = objmenu.exec_maintenance(tmparr3, tmparr3['parameter']['uuid'], tmparr3['type'], pk_use_flg=False, auth_check=False, record_file_paths=uploadFiles)
                                                        if ret[0] is True:
                                                            dbAccess.db_commit()

                                                        else:
                                                            dbAccess.db_rollback()
                                                            fail_cnt = fail_cnt + 1
                                                            if len(ret) >= 3:
                                                                g.applogger.debug(ret[2])
                                                                collection_log = '%s\n%s' % (collection_log, ret[2]) if collection_log else ret[2]
                                                    except Exception as e:
                                                        t = traceback.format_exc()
                                                        g.applogger.info("[ts={}] {}".format(get_iso_datetime(), arrange_stacktrace_format(t)))
                                                        print_exception_msg(e)

                                                        # 言語設定を変更:デフォルトへ戻す
                                                        setattr(g, 'LANGUAGE', 'en')
                                                        raise Exception()
                                                    else:
                                                        # 言語設定を変更:デフォルトへ戻す
                                                        setattr(g, 'LANGUAGE', 'en')

                                            if fail_cnt > 0:
                                                FREE_LOG = g.appmsg.get_api_message("MSG-10851", ["%s/%s" % (fail_cnt, rec_cnt), ])
                                                g.applogger.debug(FREE_LOG)
                                                collection_log = '%s\n%s' % (collection_log, FREE_LOG) if collection_log else FREE_LOG
                                                NOTICE_FLG = 2

                                            else:
                                                FREE_LOG = g.appmsg.get_api_message("MSG-10855", [hostname, menu_name, operation_id])
                                                g.applogger.debug(FREE_LOG)
                                                collection_log = '%s\n%s' % (collection_log, FREE_LOG) if collection_log else FREE_LOG
                                                if NOTICE_FLG != 1:
                                                    NOTICE_FLG = 2

                                        FREE_LOG = g.appmsg.get_api_message("MSG-10853", [hostname, filename])
                                        collection_log = '%s\n%s' % (collection_log, FREE_LOG) if collection_log else FREE_LOG

                        NOTICE_FLG = str(NOTICE_FLG)

                        # logを一時ファイルに書き込み
                        tmp_log_dir = f"/tmp/{execNo}"
                        os.mkdir(tmp_log_dir)
                        tmp_log_path = f"{tmp_log_dir}/{tmpCollectlogfile}"
                        log_lines = collection_log.splitlines()
                        with open(tmp_log_path, "w") as f:
                            for line in log_lines:
                                f.write(line + "\n")
                        uploadFiles = {'collection_log': tmp_log_path}

                        request_param = {}
                        request_param['type'] = load_table.CMD_UPDATE
                        request_param['file'] = {}
                        request_param['parameter'] = {}
                        request_param['parameter']['execution_no'] = execNo
                        request_param['parameter']['collection_status'] = collect_sts_info[NOTICE_FLG] if NOTICE_FLG in collect_sts_info else ''
                        request_param['parameter']['last_update_date_time'] = last_update_timestamp
                        if len(collection_log) > 0:
                            request_param['parameter']['collection_log'] = tmpCollectlogfile

                        ret = objmenu_orch.exec_maintenance(request_param, request_param['parameter']['execution_no'], load_table.CMD_UPDATE, pk_use_flg=False, auth_check=False, record_file_paths=uploadFiles)

                        # 一時ファイルを削除
                        shutil.rmtree(tmp_log_dir)

                        if ret[0] is False:
                            dbAccess.db_rollback()
                            if len(ret) >= 3:
                                g.applogger.debug(ret[2])
                        else:
                            dbAccess.db_commit()

            except Exception as e:
                dbAccess.db_rollback()
                t = traceback.format_exc()
                g.applogger.info("[ts={}] {}".format(get_iso_datetime(), arrange_stacktrace_format(t)))
                print_exception_msg(e)

    except Exception as e:
        t = traceback.format_exc()
        g.applogger.info("[ts={}] {}".format(get_iso_datetime(), arrange_stacktrace_format(t)))
        print_exception_msg(e)

    ################################
    # 結果出力
    ################################
    if intErrorFlag != 0:
        FREE_LOG = g.appmsg.get_api_message("MSG-10146")
        g.applogger.debug(FREE_LOG)

    elif intWarningFlag != 0:
        FREE_LOG = g.appmsg.get_api_message("MSG-10147")
        g.applogger.debug(FREE_LOG)

    else:
        FREE_LOG = g.appmsg.get_api_message("MSG-10776")
        g.applogger.debug(FREE_LOG)

    g.applogger.debug("backyard_main ita_by_collector end")
