#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from flask import g
import sys
from common_libs.common.util import get_timestamp
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.gitlab import GitLabAgent
from common_libs.ansible_driver.classes.ansibletowerlibs.RestApiCaller import RestApiCaller
from common_libs.ansible_driver.classes.ansibletowerlibs.ExecuteDirector import ExecuteDirector
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiConfig import AnsibleTowerRestApiConfig
from common_libs.ansible_driver.functions.ansibletowerlibs import AnsibleTowerCommonLib as FuncCommonLib


def AnsibleTowerExecution(
    driver_id, function, ansibleTowerIfInfo, TowerHostList, toProcessRow, exec_out_dir,
    UIExecLogPath, UIErrorLogPath, MultipleLogMark, MultipleLogFileJsonAry,
    status='', JobTemplatePropertyParameterAry=None, JobTemplatePropertyNameAry=None,
    TowerProjectsScpPath={}, TowerInstanceDirPath={}, dbAccess=None
):
    error_flag = 0
    warning_flag = 0

    # 業務処理開始
    restApiCaller = None
    process_has_error = False

    try:
        tgt_execution_no = toProcessRow['EXECUTION_NO']
        db_access_user_id = '20102'

        if 'ANSTWR_HOSTNAME' not in ansibleTowerIfInfo and 'ANSTWR_HOST_ID' in ansibleTowerIfInfo:
            cols = dbAccess.table_columns_get("T_ANSC_TOWER_HOST")
            pkey = cols[1][0]
            cols = (',').join(cols[0])
            sql = (
                "SELECT              \n"
                "  %s                \n"
                "FROM                \n"
                "  T_ANSC_TOWER_HOST \n"
                "WHERE               \n"
                "  DISUSE_FLAG = '0' \n"
                "AND                 \n"
                "  %s = %%s ;        \n"
            ) % (cols, pkey)
            ifInfoRows = dbAccess.sql_execute(sql, [ansibleTowerIfInfo['ANSTWR_HOST_ID'], ])
            ansibleTowerIfInfo['ANSTWR_HOSTNAME'] = ifInfoRows[0]['ANSTWR_HOSTNAME']

        ################################
        # 接続トークン取得
        ################################
        # トレースメッセージ
        g.applogger.debug("Authorize Ansible Automation Controller.")

        proxySetting = {}
        proxySetting['address'] = ansibleTowerIfInfo["ANSIBLE_PROXY_ADDRESS"]
        proxySetting['port'] = ansibleTowerIfInfo["ANSIBLE_PROXY_PORT"]

        restApiCaller = RestApiCaller(
            ansibleTowerIfInfo['ANSTWR_PROTOCOL'],
            ansibleTowerIfInfo['ANSTWR_HOSTNAME'],
            ansibleTowerIfInfo['ANSTWR_PORT'],
            ansibleTowerIfInfo['ANSTWR_AUTH_TOKEN'],
            proxySetting
        )

        response_array = restApiCaller.authorize()
        if not response_array['success']:
            process_has_error = True
            error_flag = 1

            g.applogger.error("Faild to authorize to Ansible Automation Controller. %s" % (response_array['responseContents']['errorMessage']))

        workflowTplId = -1
        director = None
        if not process_has_error:
            g.applogger.debug("maintenance environment (exec_no: %s)" % (tgt_execution_no))
            director = ExecuteDirector(driver_id, restApiCaller, None, dbAccess, exec_out_dir, ansibleTowerIfInfo, JobTemplatePropertyParameterAry, JobTemplatePropertyNameAry, TowerProjectsScpPath, TowerInstanceDirPath)
            GitObj = GitLabAgent()

        # Tower 接続確認
        if not process_has_error:
            # TowerのRestAPIのv2ページに接続できるか確認
            response_array = restApiCaller.restCall('GET', '')
            if response_array['statusCode'] != 200:
                # TowerのRestAPIのv2ページに接続出来ない場合はインターフェース情報設定ミスとする
                process_has_error = True
                error_flag = 1
                errorMessage = g.appmsg.get_api_message("MSG-10075", [tgt_execution_no])
                director.errorLogOut(errorMessage)

        # Tower version確認
        if not process_has_error:
            response_array = AnsibleTowerRestApiConfig.get(restApiCaller)
            if not response_array['success']:
                # Tower config情報の取得
                process_has_error = True
                error_flag = 1
                errorMessage = g.appmsg.get_api_message("MSG-10074", [tgt_execution_no])
                director.errorLogOut(errorMessage)

            else:
                if 'responseContents' in response_array \
                and 'version' in response_array['responseContents'] and response_array['responseContents']['version'] is not None:
                    version = response_array['responseContents']['version']
                    ary = version.split('.')
                    if len(ary) == 3:
                        if int(ary[0]) < 4:
                            pass
                            """
                            if ansibleTowerIfInfo['ANSIBLE_EXEC_MODE'] != AnscConst.DF_EXEC_MODE_TOWER:
                                process_has_error = True
                                error_flag = 1
                                errorMessage = g.appmsg.get_api_message("MSG-10022", [version])
                                director.errorLogOut(errorMessage)
                            """

                        else:
                            if ansibleTowerIfInfo['ANSIBLE_EXEC_MODE'] != AnscConst.DF_EXEC_MODE_AAC:
                                process_has_error = True
                                error_flag = 1
                                errorMessage = g.appmsg.get_api_message("MSG-10022", [version])
                                director.errorLogOut(errorMessage)

                        version = '%s%s' % (str(ary[0]).zfill(3), str(ary[1]).zfill(3))
                        # Towerのバージョンが3.5以下かを判定する
                        if int(version) <= int("003005"):
                            version = AnscConst.TOWER_VER35

                        else:
                            version = AnscConst.TOWER_VER36

                        # Towerのバージョン退避
                        restApiCaller.setTowerVersion(version)
                        director.setTowerVersion(version)

                    else:
                        process_has_error = True
                        error_flag = 1
                        errorMessage = g.appmsg.get_api_message("MSG-10073", [tgt_execution_no])
                        director.errorLogOut(errorMessage)

                else:
                    # Tower config情報の取得
                    process_has_error = True
                    error_flag = 1
                    errorMessage = g.appmsg.get_api_message("MSG-10073", [tgt_execution_no])
                    director.errorLogOut(errorMessage)

        if function == AnscConst.DF_EXECUTION_FUNCTION:
            if not process_has_error:
                process_was_scrammed = False
                wfId = -1

                ################################################################
                # AnsibleTowerに必要なデータを生成
                ################################################################
                TowerHostList = []

                workflowTplId, TowerHostList = director.build(GitObj, toProcessRow, ansibleTowerIfInfo, TowerHostList)
                if workflowTplId == -1:
                    # メイン処理での異常フラグをON
                    process_has_error = True
                    error_flag = 1
                    g.applogger.error("Faild to create Ansible Automation Controller environment. (exec_no: %s)" % (tgt_execution_no))

                else:
                    # マルチログかを取得する
                    MultipleLogMark = director.getMultipleLogMark()
                    if not process_has_error:
                        # トレースメッセージ
                        g.applogger.debug("launch (exec_no: %s)" % (tgt_execution_no))

                        # 実行直前に緊急停止確認
                        if FuncCommonLib.isScrammedExecution(dbAccess, tgt_execution_no):
                            process_was_scrammed = True

                        else:
                            # ジョブワークフロー実行
                            wfId = director.launchWorkflow(workflowTplId)
                            if wfId == -1:
                                process_has_error = True
                                error_flag = 1
                                g.applogger.error("Faild to launch workflowJob. (exec_no: %s)" % (tgt_execution_no))
                                errorMessage = g.appmsg.get_api_message("MSG-10655")
                                director.errorLogOut(errorMessage)

                            else:
                                g.applogger.debug("execution start up complated. (exec_no: %s)" % (tgt_execution_no))

                # 実行結果登録
                toProcessRow['LAST_UPDATE_USER'] = db_access_user_id
                if process_was_scrammed:
                    # 緊急停止時
                    toProcessRow['TIME_START'] = get_timestamp()
                    toProcessRow['TIME_END'] = get_timestamp()
                    toProcessRow['STATUS_ID'] = AnscConst.SCRAM

                elif process_has_error:
                    # 異常時
                    toProcessRow['TIME_START'] = get_timestamp()
                    toProcessRow['TIME_END'] = get_timestamp()
                    toProcessRow['STATUS_ID'] = AnscConst.FAILURE
                    status = AnscConst.FAILURE

                else:
                    # 正常時
                    toProcessRow['TIME_START'] = get_timestamp()
                    toProcessRow['STATUS_ID'] = AnscConst.PROCESSING
                    status = AnscConst.PROCESSING

                # 実行失敗時にはここで消す、成功時には確認君で確認して消す
                if (process_was_scrammed or process_has_error) \
                and ansibleTowerIfInfo['ANSTWR_DEL_RUNTIME_DATA'] == '1' \
                and director is not None:

                    ret = director.delete(GitObj, tgt_execution_no, TowerHostList)
                    if not ret:
                        warning_flag = 1
                        g.applogger.error("Faild to cleanup Ansible Automation Controller environment. (exec_no: %s)" % (tgt_execution_no))

                    else:
                        g.applogger.debug("Cleanup Ansible Automation Controller environment SUCCEEDED. (exec_no: %s)" % (tgt_execution_no))

        elif function == AnscConst.DF_CHECKCONDITION_FUNCTION:
            if not process_has_error:
                record_status = ''
                execution_finished_flag = False

                # データ準備
                tgt_execution_no = toProcessRow['EXECUTION_NO']

                # この時点で作業実行レコードのステータス再取得して緊急停止ボタンが押されていれば、最後のレコード更新ステータスをSCRAMにする
                # ただし、処理中のステータスはTowerから取得した値を見て処理を分ける
                record_status = ""
                if FuncCommonLib.isScrammedExecution(dbAccess, tgt_execution_no):
                    record_status = AnscConst.SCRAM

                ################################################################
                # AnsibleTower監視
                ################################################################
                # トレースメッセージ
                g.applogger.debug("monitoring environment (exec_no: %s)" % (tgt_execution_no))

                director = ExecuteDirector(driver_id, restApiCaller, None, dbAccess, "", ansibleTowerIfInfo, TowerProjectsScpPath=TowerProjectsScpPath, TowerInstanceDirPath=TowerInstanceDirPath)
                status = director.monitoring(toProcessRow, ansibleTowerIfInfo)

                # マルチログかを取得する
                MultipleLogMark = director.getMultipleLogMark()

                # マルチログかを取得する
                MultipleLogFileJsonAry = director.getMultipleLogFileJsonAry()

                ################################################################
                # 遅延チェック
                ################################################################
                if status not in [AnscConst.PROCESSING, AnscConst.COMPLETE, AnscConst.FAILURE, AnscConst.SCRAM, AnscConst.EXCEPTION]:
                    error_flag = 1
                    status = AnscConst.EXCEPTION

                # 確認前に取得したステータスがSCRAMであれば、どんな結果でもSCRAMにする
                if record_status == AnscConst.SCRAM:
                    status = AnscConst.SCRAM

                ################################################################
                # 実行結果登録
                ################################################################
                if process_has_error:
                    status = AnscConst.FAILURE

                # トレースメッセージ
                g.applogger.debug("Update execution_management row. status=>%s" % (status))

        elif function == AnscConst.DF_RESULTFILETRANSFER_FUNCTION:
            if not process_has_error:
                if director is not None:
                    ret = director.transfer(tgt_execution_no, TowerHostList)
                    if not ret:
                        warning_flag = 1
                        g.applogger.error("Faild to transfer the execution result file from Ansible Automation Controller. (exec_no: %s)" % (tgt_execution_no))

                    else:
                        g.applogger.debug("transfer the execution result file from Ansible Automation Controller environment SUCCEEDED. (exec_no: %s)" % (tgt_execution_no))

        elif function == AnscConst.DF_DELETERESOURCE_FUNCTION:
            if not process_has_error:
                finishedStatusArray = [AnscConst.COMPLETE, AnscConst.FAILURE, AnscConst.EXCEPTION, AnscConst.SCRAM]
                if status in finishedStatusArray:
                    execution_finished_flag = True

                if ansibleTowerIfInfo['ANSTWR_DEL_RUNTIME_DATA'] == '1' and director is not None:
                    ret = director.delete(GitObj, tgt_execution_no, TowerHostList)
                    if not ret:
                        warning_flag = 1
                        g.applogger.error("Faild to clean up Ansible Automation Controller environment. (exec_no: %s)" % (tgt_execution_no))

                    else:
                        g.applogger.debug("Clean up Ansible Automation Controller environment SUCCEEDED. (exec_no: %s)" % (tgt_execution_no))

        dbAccess = None
        restApiCaller = None

        return True, TowerHostList, toProcessRow, MultipleLogMark, MultipleLogFileJsonAry, status, error_flag, warning_flag

    except Exception as e:
        error_flag = 1
        raise e
