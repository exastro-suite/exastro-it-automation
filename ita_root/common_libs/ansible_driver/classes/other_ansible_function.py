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
Ansible functionまとめmodule
"""

from flask import g
import inspect
from common_libs.common.dbconnect import *


class OtherAnsibleFunction():
    """
    Ansibleで使用するfunctionをまとめたクラス
    """

    def chkSubstitutionValueListRecodedifference(BefInfo, AftInfo):
        """
        代入値管理・パラメータシートの具体値判定
        
        Arguments:
            BefInfo:
            AftInfo: 

        returns:
            diff:
            befFileDel:
            AftFileCpy:
        """
        diff = False
        befFileDel = False
        AftFileCpy = False
        
        if AftInfo['COL_CLASS'] == 'FileUploadColumn' and AftInfo['REG_TYPE'] == 'Value':
            AftInfo['VARS_ENTRY_FILE'] = AftInfo['VARS_ENTRY']
            AftInfo['VARS_ENTRY'] = ""
        else:
            AftInfo['VARS_ENTRY_FILE'] = ""
        
        if BefInfo['SENSITIVE_FLAG'] != AftInfo['SENSITIVE_FLAG'] or \
            BefInfo['VARS_ENTRY_FILE'] != AftInfo['VARS_ENTRY_FILE'] or \
            BefInfo['VARS_ENTRY_FILE_MD5'] != AftInfo['COL_FILEUPLOAD_MD5'] or \
            BefInfo['VARS_ENTRY'] != AftInfo['VARS_ENTRY']:
                diff = True
        
        if diff == 1:
            # 代入値管理の具体値がファイルの場合
            if BefInfo['VARS_ENTRY_FILE'] != AftInfo['VARS_ENTRY_FILE'] or \
                BefInfo['VARS_ENTRY_FILE_MD5'] != AftInfo['COL_FILEUPLOAD_MD5']:
                    if BefInfo['VARS_ENTRY_FILE'] != "":
                        befFileDel = True
        
            # パラメータシートの具体値がファイルの場合
            if BefInfo['VARS_ENTRY_FILE'] != AftInfo['VARS_ENTRY_FILE'] or \
                BefInfo['VARS_ENTRY_FILE_MD5'] != AftInfo['COL_FILEUPLOAD_MD5']:
                    if AftInfo['VARS_ENTRY_FILE'] != "" and AftInfo['REG_TYPE'] == 'Value':
                        AftFileCpy = True

        return diff, befFileDel, AftFileCpy

    def chkSpecificsValueInput(arrayRegData, arrayVariant, UpLoadFile, DelFlag, ordMode, tgtTableName, WS_DB):
        retBool = False
        boolSystemErrorFlag = False
        retStrBody = g.appmsg.get_api_message("ITAANSIBLEH-ERR-55294")
        
        strModeId = ""
        if "TCA_PRESERVED" in arrayVariant:
            if "TCA_ACTION" in arrayVariant["TCA_PRESERVED"]:
                aryTcaAction = arrayVariant["TCA_PRESERVED"]["TCA_ACTION"]
                strModeId = aryTcaAction["ACTION_MODE"]
        
        modeValue_sub = ""
        if strModeId == "DTUP_singleRecDelete":
            modeValue_sub = arrayVariant["TCA_PRESERVED"]["TCA_ACTION"]["ACTION_SUB_MODE"]
        
        if arrayVariant['edit_target_row']['VARS_ENTRY']:
            BefVarsEntry = arrayVariant['edit_target_row']['VARS_ENTRY']
        else:
            BefVarsEntry = None
        
        if arrayVariant['edit_target_row']['VARS_ENTRY_FILE']:
            BefVarsEntryFile = arrayVariant['edit_target_row']['VARS_ENTRY_FILE']
        else:
            BefVarsEntryFile = None
        
        if arrayVariant['edit_target_row']['SENSITIVE_FLAG']:
            BefSensitiveFlag = arrayVariant['edit_target_row']['SENSITIVE_FLAG']
        else:
            BefSensitiveFlag = None
        
        if "VARS_ENTRY" in arrayRegData:
            AftVarsEntry = arrayRegData['VARS_ENTRY']
        else:
            AftVarsEntry = None
        
        if "VARS_ENTRY_FILE" in arrayRegData:
            AftVarsEntryFile = arrayRegData['VARS_ENTRY_FILE']
        else:
            AftVarsEntryFile = None
        
        if "SENSITIVE_FLAG" in arrayRegData:
            AftSensitiveFlag = arrayRegData['SENSITIVE_FLAG']
        else:
            AftSensitiveFlag = None
        
        if UpLoadFile in arrayRegData:
            AftUpLoadFile = arrayRegData[UpLoadFile]
        else:
            AftUpLoadFile = None
        
        if DelFlag in arrayRegData:
            AftDelFlag = arrayRegData[DelFlag]
        else:
            AftDelFlag = None
        
        # Excelからの場合、該当レコードの具体値にファイルがアップロードされているか確認
        if ordMode == 1:
            if strModeId == "DTUP_singleRecUpdate" or \
            (strModeId == "DTUP_singleRecUpdate" and modeValue_sub == "off"):
                if arrayVariant['edit_target_row']['ASSIGN_ID']:
                    Pkey = arrayVariant['edit_target_row']['ASSIGN_ID']
                else:
                    Pkey = None
                
                query = "SELECT "
                query += "TBL_A.VARS_ENTRY_FILE "
                query += "FROM "
                query += tgtTableName + " TBL_A "
                query += "WHERE "
                query += "TBL_A.ASSIGN_ID = %ASSIGN_ID "
                
                aryForBind = {}
                aryForBind['ASSIGN_ID'] = Pkey
                
                data_list = WS_DB.sql_execute(query, aryForBind)

                for data in data_list:
                    if data['VARS_ENTRY_FILE'] != '':
                        retStrBody = g.appmsg.get_api_message("ITAANSIBLEH-ERR-55296")
                        retBool = True
                        boolSystemErrorFlag = True
                        return retBool, boolSystemErrorFlag, retStrBody
        
        # 0:[ブラウザからの新規登録
        # 1:[EXCEL]からの新規登録
        # 2:[CSV]からの新規登録
        # 3:[JSON]からの新規登録
        # 4:[ブラウザからの新規登録(SQLトランザクション無し)
        if ordMode == 0:
            if strModeId == "DTUP_singleRecRegister" or strModeId == "DTUP_singleRecUpdate":
                FileSet = False
                StrSet = False
                # ファイル削除がチェックされているか判定
                if AftDelFlag == "on":
                    FileSet = False
                else:
                    # 新規ファイルがアップロードされているか判定
                    if AftUpLoadFile == "":
                        # 変更前にファイルがアップロードされているか判定
                        if BefVarsEntryFile == "":
                            FileSet = False
                        else:
                            FileSet = True
                    else:
                        FileSet = True
                
                # 具体値が設定されているか判定
                if AftVarsEntry == "":
                    # SENSITIVE設定がONか判定
                    if AftSensitiveFlag == 2:
                        # 変更前のSENSITIVE設定がONか判定
                        if BefSensitiveFlag == 2:
                            # 変更前の具体値が設定されているか判定
                            if BefVarsEntry == "":
                                StrSet = False
                            else:
                                StrSet = True
                        else:
                            # 具体値は空白になる
                            StrSet = False
                    else:
                        StrSet = False
                else:
                    StrSet = True
                
                if FileSet == 1 and StrSet == 1:
                    return retBool, boolSystemErrorFlag, retStrBody
            
            elif strModeId == "DTUP_singleRecDelete":
                if modeValue_sub == "off":
                    if BefVarsEntry != "" and BefVarsEntryFile != "":
                        retStrBody = g.appmsg.get_api_message("ITAANSIBLEH-ERR-55295")
                        return retBool, boolSystemErrorFlag, retStrBody
        elif ordMode == 1 or ordMode == 2 or ordMode == 3 or ordMode == 4:
            if strModeId == "DTUP_singleRecRegister":
                if AftVarsEntry != "" and AftVarsEntryFile != "":
                    return retBool, boolSystemErrorFlag, retStrBody
            
            if strModeId == "DTUP_singleRecUpdate":
                FileSet = False
                StrSet = False
                # ファイル削除がチェックされているか判定
                if AftDelFlag == "on":
                    FileSet = False
                else:
                    # 新規ファイルがアップロードされているか判定
                    if AftUpLoadFile == "":
                        # 変更前にファイルがアップロードされているか判定
                        if BefVarsEntryFile == "":
                            FileSet = False
                        else:
                            FileSet = True
                    else:
                        FileSet = True
                
                # 具体値が設定されているか判定
                if AftVarsEntry == "":
                    # SENSITIVE設定がONか判定
                    if AftSensitiveFlag == 2:
                        # 変更前のSENSITIVE設定がONか判定
                        if BefSensitiveFlag == 2:
                            # 変更前の具体値が設定されているか判定
                            if BefVarsEntry == "":
                                StrSet = False
                            else:
                                StrSet = True
                        else:
                            # 具体値は空白になる
                            StrSet = False
                    else:
                        StrSet = False
                else:
                    StrSet = True
                
                if FileSet == 1 and StrSet == 1:
                    return retBool, boolSystemErrorFlag, retStrBody
            
            if strModeId == "DTUP_singleRecDelete":
                if modeValue_sub == "off" and BefVarsEntry != "":
                    retStrBody = g.appmsg.get_api_message("ITAANSIBLEH-ERR-55295")
                    return retBool, boolSystemErrorFlag, retStrBody
        else:
            frame = inspect.currentframe().f_back
            retStrBody = "Illegal value for ModeType. file:" + (__file__) + " line:" + str(frame.f_lineno)
            g.applogger.error(retStrBody)
            retBool = False
            boolSystemErrorFlag = True
            retStrBody = ""
            return retBool, boolSystemErrorFlag, retStrBody
        
        retBool = True
        boolSystemErrorFlag = False
        retStrBody = "" 
        return retBool, boolSystemErrorFlag, retStrBody