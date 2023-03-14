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

from flask import g

from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs
from common_libs.common.util import get_upload_file_path
from common_libs.ansible_driver.classes.YamlParseClass import YamlParse
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.CreateAnsibleExecFiles import CreateAnsibleExecFiles
from common_libs.ansible_driver.functions.util import getAnsibleConst, getDataRelayStorageDir


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


def get_jnl_uuid(dbAccess, TableName, uuid):

    TableName = '%s_JNL' % (TableName)
    sql = "SELECT JOURNAL_SEQ_NO FROM `%s` WHERE ROW_ID = %%s ;" % (TableName)
    rset = dbAccess.sql_execute(sql, [uuid,])

    return rset[0]['JOURNAL_SEQ_NO']


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


def outputLog(logPath, subject="", messages=""):

    now = datetime.datetime.now()
    with open(logPath, 'a') as fp:
        msg = '%s %s\n' % (now.strftime('%Y-%m-%d %H:%M:%S'), subject)
        fp.write(msg)
        if messages:
            fp.write(messages)


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
                    arrVarsList[key1][str(key2)] = value2

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

            for key2, value2 in php_array(result):
                for key3, value3 in php_array(value2):
                    if type(value3['VAR_VALUE']) not in (list, dict):
                        if key1 in arrVarsList and value3['VAR_NAME_PATH'] in arrVarsList[key1] and arrVarsList[key1][value3['VAR_NAME_PATH']] is not None:
                            arrVarsList[key1][value3['VAR_NAME_PATH']].append(value3['VAR_VALUE'])

                        else:
                            arrVarsList[key1][value3['VAR_NAME_PATH']] = value3['VAR_VALUE']

                    else:
                        for key4, value4 in php_array(value3['VAR_VALUE']):
                            if is_num(key4) and type(value4) not in (list, dict):
                                keyname = '%s[%s]' % (value3['VAR_NAME_PATH'], key4)
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
    for var, val in ina_parent_var_array:
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
            wk_var_name_path = var
            wk_var_name = var

        # 配列の開始かを判定する
        if col_array_f == "I":
            if in_fastarry_f is False:
                in_fastarry_f = True
                fastarry_f_on = True

        in_chl_var_key = in_chl_var_key + 1
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

    return True, ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count, in_chl_var_key


def is_assoc(in_array):

    key_int = False
    key_char = False
    if type(in_array) not in (list, dict):
        return -1

    php_keys = lambda x: x.keys() if isinstance(x, dict) else range(len(x))
    keys = php_keys(in_array)
    for i, value in keys:
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

    print("backyard_main ita_by_collector called")

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # 実行準備
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    intErrorFlag = 0
    intWarningFlag = 0

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
        '1' : 'T_ANSL_EXEC_STS_INST',
        '2' : 'T_ANSP_EXEC_STS_INST',
        '3' : 'T_ANSR_EXEC_STS_INST',
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

        # トランザクション開始
        #dbAccess.db_transaction_start()
        boolInTransactionFlag = True
        #dbAccess.db_transaction_end(True) # コミット
        #dbAccess.db_transaction_end(False) # ロールバック

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
        # オーケストレータ順に実施
        ################################
        for intCollectOrcNo, strCollectOrcTablename in sorted(arrCollectOrcList.items(), key=lambda x:int(x[0])):
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
                    strTempForSql = "WHERE EXECUTION_NO = %s FOR UPDATE "
                    arySqlBind = [exec_no['EXECUTION_NO'], ]
                    aryMovements = getInfoFromTablename(dbAccess, strCollectOrcTablename, strTempForSql, arySqlBind)
                    aryMovement = aryMovements[0]

                    NOTICE_FLG = 1  # 1:収集済み
                    RESTEXEC_FLG = 0
                    FREE_LOG = ""

                    driver_id = ansible_driver_id_info[intCollectOrcNo]['id']
                    execNo = aryMovement['EXECUTION_NO']
                    operation_id = aryMovement['OPERATION_ID']

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

                    ansdrv.makeDir(tmpCollectlogdir)

                    # 完了以外の場合
                    if aryMovement['STATUS_ID'] != AnscConst.COMPLETE:
                        tmpMovement = aryMovement
                        tmpMovement['COLLECT_LOG'] = ''
                        tmpMovement['COLLECT_STATUS'] = "3"  # 3:対象外
                        tmpMovement['LAST_UPDATE_USER'] = g.USER_ID

                        ret = dbAccess.table_update(strCollectOrcTablename, tmpMovement, 'EXECUTION_NO')
                        if ret is False:
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
                        aryOperation = getInfoFromTablename(dbAccess, "T_COMN_OPERATION", strTempForSql, arySqlBind)

                        # Operationが廃止済み
                        if len(aryOperation) <= 0:
                            FREE_LOG = g.appmsg.get_api_message("MSG-10854", [operation_id,])
                            g.applogger.debug(FREE_LOG)
                            outputLog(strCollectlogPath, FREE_LOG)
                            NOTICE_FLG = 4  # 4:収集エラー

                        # 対象のファイル無しの場合
                        elif isinstance(arrTargetfiles, list) is False or len(arrTargetfiles) <= 0:
                            FREE_LOG = g.appmsg.get_api_message("MSG-10857")
                            g.applogger.debug(FREE_LOG)
                            outputLog(strCollectlogPath, FREE_LOG)
                            NOTICE_FLG = 3  # 3:対象外

                        # 対象のファイル有の場合
                        else:
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
                                        outputLog(strCollectlogPath, FREE_LOG)
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

                                arrTableForMenuLists = {}
                                arrTableForMenuType = {}

                                # ホストが存在しない
                                if len(aryhostInfo) <= 0:
                                    FREE_LOG = g.appmsg.get_api_message("MSG-10852", [hostname,])
                                    outputLog(strCollectlogPath, FREE_LOG)
                                    NOTICE_FLG = 4  # 4:収集エラー
                                    if RESTEXEC_FLG == 1:
                                        NOTICE_FLG = 2  # 収集済み(通知あり)

                                else:
                                    aryhostInfo = aryhostInfo[0]
                                    hostid = aryhostInfo['SYSTEM_ID']

                                    arrSqlinsertParm = {}
                                    arrSqlinsertParmDn = {}
                                    arrFileUploadList = {}

                                    # ソースファイルからパラメータ整形(ファイル名、メニューID、項目名、値)
                                    for filename, vardata in parmdata.items():
                                        for varname, varvalue in vardata.items():
                                            # 配列、ハッシュ構造の場合(メンバー変数名あり)
                                            if type(varvalue) in (list, dict):
                                                for varmember, varmembermembervalue in varvalue.items():
                                                    strTempForSql = (
                                                        "SELECT "
                                                        "  TAB_C.MENU_ID, "
                                                        "  TAB_C.TABLE_NAME, "
                                                        "  TAB_C.VERTICAL, "
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
                                                        "WHERE "
                                                        "  TAB_A.PARSE_TYPE_ID = %s "
                                                        "AND TAB_A.FILE_PREFIX = %s "
                                                        "AND TAB_A.VARS_NAME = %s "
                                                        "AND TAB_A.VRAS_MEMBER_NAME = %s "
                                                        "AND TAB_A.DISUSE_FLAG IN ('0') "
                                                        "ORDER BY TAB_A.ROW_ID ASC "
                                                    )
                                                    arySqlBind = [intParseTypeID, filename, varname, varmember]
                                                    retResult = dbAccess.sql_execute(strTempForSql, arySqlBind)
                                                    for tmpkey, tmpvalue in enumerate(retResult):
                                                        writemenuid = tmpvalue['MENU_ID']
                                                        col_name = tmpvalue['COLUMN_NAME_REST']
                                                        if filename not in arrSqlinsertParm:
                                                            arrSqlinsertParm[filename] = {}

                                                        if writemenuid not in arrSqlinsertParm[filename]:
                                                            arrSqlinsertParm[filename][writemenuid] = {}

                                                        if col_name not in arrSqlinsertParm[filename][writemenuid]:
                                                            arrSqlinsertParm[filename][writemenuid][col_name] = None

                                                        arrSqlinsertParm[filename][writemenuid][col_name] = varmembermembervalue
                                                        arrTableForMenuLists[writemenuid] = tmpvalue['TABLE_NAME']
                                                        arrTableForMenuType[writemenuid] = tmpvalue['VERTICAL']

                                                        if tmpvalue['COLUMN_CLASS'] in ["9", "20"]:  # 9 or 20:ファイルアップロード
                                                            if filename not in arrFileUploadList:
                                                                arrFileUploadList[filename] = {}

                                                            if writemenuid not in arrFileUploadList[filename]:
                                                                arrFileUploadList[filename][writemenuid] = {}

                                                            if col_name not in arrFileUploadList[filename][writemenuid]:
                                                                arrFileUploadList[filename][writemenuid][col_name] = None

                                                            arrFileUploadList[filename][writemenuid][col_name] = tmpvalue['COLUMN_CLASS']

                                            # メンバ変数無し
                                            else:
                                                strTempForSql = (
                                                    "SELECT "
                                                    "  TAB_C.MENU_ID, "
                                                    "  TAB_C.TABLE_NAME, "
                                                    "  TAB_C.VERTICAL, "
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
                                                    "WHERE "
                                                    "  TAB_A.PARSE_TYPE_ID = %s "
                                                    "AND TAB_A.FILE_PREFIX = %s "
                                                    "AND TAB_A.VARS_NAME = %s "
                                                    "AND TAB_A.DISUSE_FLAG IN ('0') "
                                                    "ORDER BY TAB_A.ROW_ID ASC "
                                                )
                                                arySqlBind = [intParseTypeID, filename, varname]
                                                retResult = dbAccess.sql_execute(strTempForSql, arySqlBind)
                                                for tmpkey, tmpvalue in enumerate(retResult):
                                                    writemenuid = tmpvalue['MENU_ID']
                                                    col_name = tmpvalue['COLUMN_NAME_REST']
                                                    if filename not in arrSqlinsertParm:
                                                        arrSqlinsertParm[filename] = {}

                                                    if writemenuid not in arrSqlinsertParm[filename]:
                                                        arrSqlinsertParm[filename][writemenuid] = {}

                                                    if col_name not in arrSqlinsertParm[filename][writemenuid]:
                                                        arrSqlinsertParm[filename][writemenuid][col_name] = None

                                                    arrSqlinsertParm[filename][writemenuid][col_name] = varvalue
                                                    arrTableForMenuLists[writemenuid] = tmpvalue['TABLE_NAME']
                                                    arrTableForMenuType[writemenuid] = tmpvalue['VERTICAL']

                                                    if tmpvalue['COLUMN_CLASS'] in ["9", "20"]:  # 9 or 20:ファイルアップロード
                                                        if filename not in arrFileUploadList:
                                                            arrFileUploadList[filename] = {}

                                                        if writemenuid not in arrFileUploadList[filename]:
                                                            arrFileUploadList[filename][writemenuid] = {}

                                                        if col_name not in arrFileUploadList[filename][writemenuid]:
                                                            arrFileUploadList[filename][writemenuid][col_name] = None

                                                        arrFileUploadList[filename][writemenuid][col_name] = tmpvalue['COLUMN_CLASS']

                                    # 代入順序1->X （項目,,,→項目[X],,,)
                                    """
                                    for tmpfn, arrrmenu in arrSqlinsertParmDn.items():
                                        for tmpmid, tmparrprm in arrrmenu.imtes():
                                            if tmpfn in arrSqlinsertParm and arrSqlinsertParm[tmpfn] and tmpmid in arrSqlinsertParm[tmpfn] and arrSqlinsertParm[tmpfn][tmpmid] is not None:
                                                arrSqlinsertParm[tmpfn][tmpmid] = arrSqlinsertParm[tmpfn][tmpmid] + arrSqlinsertParmDn[tmpfn][tmpmid]

                                            else:
                                                arrSqlinsertParm[tmpfn][tmpmid] = arrSqlinsertParmDn[tmpfn][tmpmid]
                                    """

                                    tmpFilter = {}
                                    insert_flag_list = []
                                    if len(arrSqlinsertParm) <= 0:
                                        # 収集項目値管理上の対象ファイル無しの場合
                                        FREE_LOG = g.appmsg.get_api_message("MSG-10856")
                                        outputLog(strCollectlogPath, FREE_LOG)
                                        NOTICE_FLG = 3  # 3:対象外
                                        if RESTEXEC_FLG == 1:
                                            NOTICE_FLG = 2  # 収集済み(通知あり)

                                    for filename, tmparr3 in arrSqlinsertParm.items():
                                        FREE_LOG1 = g.appmsg.get_api_message("MSG-10849", [hostname, filename])
                                        outputLog(strCollectlogPath, FREE_LOG1)
                                        for menuid, tgtSource_row in tmparr3.items():
                                            strMenuType = "" if arrTableForMenuType[menuid] == "0" else "Vertical"
                                            idx_from = 7 if arrTableForMenuType[menuid] == "0" else 8
                                            tablename = arrTableForMenuLists[menuid]
                                            strTempForSql = "WHERE TABLE_NAME = %s AND DISUSE_FLAG IN ('0') ORDER BY MENU_TABLE_LINK_ID DESC "
                                            arySqlBind = [tablename,]
                                            tmpResult = getInfoFromTablename(dbAccess, "T_MENU_TABLE_LINK", strTempForSql, arySqlBind)

                                            # tmpRestInfo = dbAccess.table_columns_get(tablename)
                                            tmpRestInfo = []
                                            strTempForSql = (
                                                "SELECT "
                                                "  COLUMN_NAME_REST "
                                                "FROM "
                                                "  T_COMN_MENU_COLUMN_LINK "
                                                "WHERE "
                                                "  MENU_ID = %s "
                                                "ORDER BY "
                                                "  COLUMN_DISP_SEQ ASC "
                                            )
                                            arySqlBind = [menuid, ]
                                            rset = dbAccess.sql_execute(strTempForSql, arySqlBind)
                                            rset = rset[idx_from:-4]
                                            for r in rset:
                                                tmpRestInfo.append(r['COLUMN_NAME_REST'])

                                            if len(tmpRestInfo) <= 0:
                                                FREE_LOG = g.appmsg.get_api_message("MSG-10850")  # ToDo "Restに失敗した"という文言だがRestは使用していない
                                                g.applogger.debug(FREE_LOG)
                                                outputLog(strCollectlogPath, FREE_LOG)
                                                FREE_LOG = g.appmsg.get_api_message("MSG-10855", [hostname, tablename, operation_id])  # ToDo 同上
                                                g.applogger.debug(FREE_LOG)
                                                outputLog(strCollectlogPath, FREE_LOG)
                                                NOTICE_FLG = 2  # 2:収集エラー

                                            else:
                                                insert_flag = False
                                                tmpFilter = {
                                                    'ROW_ID' : None,
                                                    'HOST_ID' : hostid,
                                                    'OPERATION_ID' : operation_id,
                                                    'DATA_JSON' : None,
                                                    'LAST_UPDATE_USER' : g.USER_ID
                                                }
                                                insertData = {}
                                                UpdateFileData = {}
                                                updatefile_list = {}

                                                strTempForSql = "WHERE HOST_ID = %s AND OPERATION_ID = %s AND DISUSE_FLAG IN ('0') ORDER BY ROW_ID ASC "
                                                arySqlBind = [hostid, operation_id]
                                                tmpResult = getInfoFromTablename(dbAccess, tablename, strTempForSql, arySqlBind)

                                                # 横メニュー
                                                if strMenuType == "":
                                                    for parmNO, pramName in enumerate(tmpRestInfo):
                                                        if pramName not in tgtSource_row:
                                                            insertData[pramName] = None

                                                        else:
                                                            insertData[pramName] = tgtSource_row[pramName]

                                                            if filename in arrFileUploadList \
                                                            and menuid in arrFileUploadList[filename] \
                                                            and pramName in arrFileUploadList[filename][menuid]:
                                                                if hostname in arrTargetUploadLists \
                                                                and tgtSource_row[pramName] in arrTargetUploadLists[hostname] \
                                                                and arrTargetUploadLists[hostname][tgtSource_row[pramName]] is not None:
                                                                    upload_filepath = arrTargetUploadLists[hostname][tgtSource_row[pramName]]
                                                                    if os.path.isfile(upload_filepath):
                                                                        filedata = b""
                                                                        with open(upload_filepath, 'r') as fp:
                                                                            filedata = fp.read()
                                                                            filedata = base64.b64encode(filedata.encode('utf-8'))

                                                                        UpdateFileData[pramName] = filedata

                                                                else:
                                                                    matchflg = ""
                                                                    for tmpfilekey, tmparrfilepath in arrTargetUploadListFullpath[hostname].items():
                                                                        # フルパス完全一致
                                                                        if tmpfilekey == tgtSource_row[pramName]:
                                                                            matchflg = "FULL"
                                                                            upload_filepath = tmparrfilepath
                                                                            if os.path.isfile(upload_filepath) and insertData[pramName] != "":
                                                                                filedata = b""
                                                                                with open(upload_filepath, 'r') as fp:
                                                                                    filedata = fp.read()
                                                                                    filedata = base64.b64encode(filedata.encode('utf-8'))

                                                                                insertData[pramName] = os.path.splitext(os.path.basename(upload_filepath))[0]
                                                                                UpdateFileData[pramName] = filedata

                                                                        # 後方一致
                                                                        elif tmpfilekey.endswith(tgtSource_row[pramName]):
                                                                            matchflg = "AFTER"
                                                                            upload_filepath = tmparrfilepath
                                                                            if os.path.isfile(upload_filepath) and insertData[pramName] != "":
                                                                                filedata = b""
                                                                                with open(upload_filepath, 'r') as fp:
                                                                                    filedata = fp.read()
                                                                                    filedata = base64.b64encode(filedata.encode('utf-8'))

                                                                                insertData[pramName] = os.path.splitext(os.path.basename(upload_filepath))[0]
                                                                                UpdateFileData[pramName] = filedata

                                                                        if matchflg != "":
                                                                            break

                                                                    if matchflg == "":
                                                                        insertData[pramName] = ""
                                                                        UpdateFileData[pramName] = ""

                                                    if len(tmpResult) <= 0:
                                                        insert_flag = True
                                                        # insertData[0] = g.appmsg.get_api_message("MSG-30004")

                                                    else:
                                                        # insertData[0] = g.appmsg.get_api_message("MSG-30005")
                                                        tmpFilter['ROW_ID'] = tmpResult[0]['ROW_ID']

                                                    tmpFilter['DATA_JSON'] = json.dumps(insertData)
                                                    insert_flag_list.append(insert_flag)

                                                    if len(UpdateFileData) > 0:
                                                        idx = len(insert_flag_list) - 1
                                                        updatefile_list[idx] = {
                                                            "colname" : pramName,
                                                            "filename" : tgtSource_row[pramName],
                                                            "filedata" : UpdateFileData[pramName],
                                                        }

                                                # 縦メニュー
                                                else:
                                                    insertData = {}
                                                    UpdateFileData = {}
                                                    updatefile_list = {}
                                                    insert_flag = True
                                                    insert_flag_list = []
                                                    intColmun = 0
                                                    input_order = None
                                                    regData = tmpResult
                                                    tmpFilter = []
                                                    tmpFilter_data = {
                                                        'ROW_ID' : None,
                                                        'HOST_ID' : hostid,
                                                        'OPERATION_ID' : operation_id,
                                                        'INPUT_ORDER' : None,
                                                        'DATA_JSON' : None,
                                                        'LAST_UPDATE_USER' : g.USER_ID
                                                    }

                                                    for pramName in tmpRestInfo:
                                                        insertData[pramName] = None

                                                    for tgtSource_key, value in tgtSource_row.items():
                                                        for parmNO, pramName in enumerate(tmpRestInfo):
                                                            # 項目名：完全一致
                                                            if pramName == tgtSource_key:
                                                                insertData[pramName] = value
                                                                if input_order is None:
                                                                    input_order = 1

                                                                # ファイルアップロードカラムの場合
                                                                if filename in arrFileUploadList and menuid in arrFileUploadList[filename] and arrFileUploadList[filename][menuid] is not None \
                                                                and (pramName == tgtSource_key or pramName in tgtSource_key):
                                                                    if pramName in arrFileUploadList[filename][menuid]:
                                                                        # ファイルアップロード対象リスト（key：ファイル名-valuse:パス）にある場合
                                                                        if value in arrTargetUploadLists[hostname]:
                                                                            upload_filepath = arrTargetUploadLists[hostname][value]
                                                                            if os.path.isfile(upload_filepath) and insertData[pramName] != "":
                                                                                filedata = b""
                                                                                with open(upload_filepath, 'r') as fp:
                                                                                    filedata = fp.read()
                                                                                    filedata = base64.b64encode(filedata.encode('utf-8'))

                                                                                insertData[pramName] = os.path.splitext(os.path.basename(upload_filepath))[0]
                                                                                UpdateFileData[pramName] = filedata

                                                                        # ファイルアップロード対象リスト（key：パス-valuse:パス）にある場合
                                                                        else:
                                                                            matchflg = ""
                                                                            for tmpfilekey, tmparrfilepath in arrTargetUploadListFullpath[hostname].items():
                                                                                matchflg = ""
                                                                                upload_filepath = tmparrfilepath
                                                                                upload_filename = os.path.splitext(os.path.basename(upload_filepath))[0]

                                                                                # フルパス完全一致
                                                                                if tmpfilekey == tgtSource_row[tgtSource_key]:
                                                                                    matchflg = "FULL"

                                                                                # 部分後方一致
                                                                                elif tmpfilekey.endswith(tgtSource_row[tgtSource_key]):
                                                                                    matchflg = "AFTER"

                                                                                if matchflg != "":
                                                                                    if os.path.isfile(upload_filepath) and insertData[pramName] != "":
                                                                                        filedata = b""
                                                                                        with open(upload_filepath, 'r') as fp:
                                                                                            filedata = fp.read()
                                                                                            filedata = base64.b64encode(filedata.encode('utf-8'))

                                                                                        insertData[pramName] = upload_filename
                                                                                        UpdateFileData[pramName] = filedata

                                                                                    break

                                                                            # 不要項目除外
                                                                            if matchflg == "":
                                                                                insertData[pramName] = ""
                                                                                UpdateFileData[pramName] = None

                                                                        if pramName != tgtSource_key \
                                                                        and input_order != 1 and input_order is not None:
                                                                            insertData[pramName] = ""

                                                                    else:
                                                                        # 値がNULLの項目を除外
                                                                        if tgtSource_key in arrFileUploadList[filename][menuid]:
                                                                            if tgtSource_key == pramName:
                                                                                if hostname in arrTargetUploadLists and value in arrTargetUploadLists[hostname] and arrTargetUploadLists[hostname][value] is not None:
                                                                                    upload_filepath = arrTargetUploadLists[hostname][value]
                                                                                    if os.path.isfile(upload_filepath):
                                                                                        filedata = b""
                                                                                        with open(upload_filepath, 'r') as fp:
                                                                                            filedata = fp.read()
                                                                                            filedata = base64.b64encode(filedata.encode('utf-8'))

                                                                                        UpdateFileData[pramName] = filedata

                                                                                else:
                                                                                    insertData[pramName] = ""
                                                                                    UpdateFileData[pramName] = None

                                                    if len(tmpRestInfo) == len(insertData):
                                                        tmpFilter_data['DATA_JSON'] = json.dumps(insertData)
                                                        for arrRegDate in regData:
                                                            if arrRegDate['INPUT_ORDER'] == input_order:
                                                                insert_flag = False
                                                                tmpFilter_data['ROW_ID'] = arrRegDate['ROW_ID']
                                                                tmpFilter_data['INPUT_ORDER'] = arrRegDate['INPUT_ORDER']
                                                                tmpFilter_data['DISUSE_FLAG'] = arrRegDate['DISUSE_FLAG']
                                                                break

                                                        else:
                                                            insert_flag = True
                                                            tmpFilter_data['INPUT_ORDER'] = input_order
                                                            tmpFilter_data['DISUSE_FLAG'] = '0'

                                                        # 同一代入順序、パラメータ結合
                                                        inputorderwflg = 0
                                                        """
                                                        for insertDataNO, tmpinsertData in enumerate(tmpFilter):
                                                            if input_order_list[insertDataNO] is not None:
                                                                if input_order_list[insertDataNO] == input_order:
                                                                    for tmpinsertDatakey, tmpinsertDatavalue in tmpinsertData.items():
                                                                        if tmpinsertDatavalue == "":
                                                                            if tmpFilter[insertDataNO][tmpinsertDatakey] is None:
                                                                                tmpFilter[insertDataNO][tmpinsertDatakey] = insertData[tmpinsertDatakey]

                                                                            if tmpinsertDatakey in UpdateFileData and UpdateFileData[tmpinsertDatakey] is not None:
                                                                                updatefile_list[insertDataNO][tmpinsertDatakey] = UpdateFileData[tmpinsertDatakey]

                                                                            inputorderwflg = 1
                                                        """

                                                        if inputorderwflg == 0:
                                                            # 種別、オペレーション、ホスト、代入順序
                                                            if input_order is not None:
                                                                tmpFilter.append(tmpFilter_data)
                                                                insert_flag_list.append(insert_flag)
                                                                if len(UpdateFileData) > 0:
                                                                    for upfileskey, upfilesval in UpdateFileData.items():
                                                                        if insertData[upfileskey] == "":
                                                                            UpdateFileData[upfileskey] = None

                                                                    idx = len(tmpFilter) - 1
                                                                    updatefile_list[idx] = {
                                                                        "colname" : pramName,
                                                                        "filename" : tgtSource_row[pramName],
                                                                        "filedata" : UpdateFileData[pramName],
                                                                    }

                                                        insertData = {}

                                                # 登録、更新
                                                RESTEXEC_FLG = 1
                                                ret = False
                                                if isinstance(tmpFilter, list) is False:
                                                    tmpFilter = [tmpFilter,]

                                                fail_cnt = 0
                                                rec_cnt = len(tmpFilter)
                                                for idx, tmpData in enumerate(tmpFilter):
                                                    if insert_flag_list[idx]:
                                                        ret = dbAccess.table_insert(tablename, tmpData, 'ROW_ID')

                                                    else:
                                                        ret = dbAccess.table_update(tablename, tmpData, 'ROW_ID')

                                                    if ret is False:
                                                        fail_cnt += 1

                                                    elif idx in updatefile_list:
                                                        uuid = ret[0]['ROW_ID']
                                                        uuid_jnl = get_jnl_uuid(dbAccess, tablename, uuid)
                                                        upfilepath_info = get_upload_file_path(workspace_id, menuid, uuid, updatefile_list[idx]['colname'], updatefile_list[idx]['filename'], uuid_jnl)
                                                        old_file_path = os.path.dirname(upfilepath_info['old_file_path'])

                                                        ansdrv.makeDir(old_file_path)
                                                        with open(upfilepath_info['old_file_path'], 'w') as fp:
                                                            fp.write(base64.b64decode(updatefile_list[idx]['filedata']).decode('utf-8'))

                                                        subprocess.run(["ln", "-nfs", upfilepath_info['old_file_path'], upfilepath_info['file_path']], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                                                insert_flag_list = []
                                                tmpFilter = []

                                                if fail_cnt > 0:
                                                    FREE_LOG = g.appmsg.get_api_message("MSG-10851", ["%s/%s" % (fail_cnt, rec_cnt), ])  # ToDo "Restに失敗した"という文言だがRestは使用していない
                                                    g.applogger.debug(FREE_LOG)
                                                    outputLog(strCollectlogPath, FREE_LOG)
                                                    NOTICE_FLG = 2

                                                else:
                                                    FREE_LOG = g.appmsg.get_api_message("MSG-10855", [hostname, tablename, operation_id])
                                                    g.applogger.debug(FREE_LOG)
                                                    outputLog(strCollectlogPath, FREE_LOG)
                                                    if NOTICE_FLG != 1:
                                                        NOTICE_FLG = 2

                                        FREE_LOG = g.appmsg.get_api_message("MSG-10853", [hostname, filename])
                                        outputLog(strCollectlogPath, FREE_LOG)

                        tmpMovement = aryMovement
                        if os.path.isfile(strCollectlogPath) is False:
                            NOTICE_FLG = 3
                            tmpMovement['COLLECT_LOG'] = ''

                        tmpMovement['COLLECT_STATUS'] = str(NOTICE_FLG)
                        tmpMovement['LAST_UPDATE_USER'] = g.USER_ID

                        ret = dbAccess.table_update(strCollectOrcTablename, tmpMovement, 'EXECUTION_NO')
                        if ret is False:
                            dbAccess.db_rollback()
                        else:
                            dbAccess.db_commit()

            except Exception as e:
                dbAccess.db_rollback()
                g.applogger.debug(e)
                import traceback
                print(traceback.format_exc())

    except Exception as e:
        g.applogger.debug(e)
        import traceback
        print(traceback.format_exc())

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

    print("backyard_main ita_by_collector end")
