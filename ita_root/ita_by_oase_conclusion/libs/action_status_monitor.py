# Copyright 2024 NEC Corporation#
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

from flask import g

from common_libs.oase.const import oaseConst
from common_libs.notification.sub_classes.oase import OASE, OASENotificationType
from libs.common_functions import addline_msg, InsertConclusionEvent, getLabelGroup
from libs.notification_data import Notification_data

class ActionStatusMonitor():
    def __init__(self, wsDb, EventObj):
        self.wsDb = wsDb
        self.EventObj = EventObj

        # ラベルマスタ取得
        self.LabelMasterDict = getLabelGroup(wsDb)

    def checkRuleMatch(self, actionObj):
        # 判定済みと承認済みを抽出
        status_list = [oaseConst.OSTS_Rule_Match, oaseConst.OSTS_Approved]
        action_log_row_info_list = self.getActionLogInfo(status_list)

        for action_log_row_info in action_log_row_info_list:
            # 評価結果の更新（ステータスを「実行中」）
            data_list = {
                "ACTION_LOG_ID": action_log_row_info["ACTION_LOG_ID"],
                "STATUS_ID": oaseConst.OSTS_Executing # "2"
            }
            self.wsDb.table_update(oaseConst.T_OASE_ACTION_LOG, data_list, 'ACTION_LOG_ID')
            self.wsDb.db_commit()

            # action実行
            retBool, result = actionObj.run(action_log_row_info)
            if retBool is False:
                # Actionのセットに失敗
                tmp_msg = g.appmsg.get_log_message("BKY-90019", [result])
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                # 評価結果の更新（ステータスを「完了（異常）」）
                data_list = {
                    "ACTION_LOG_ID": action_log_row_info["ACTION_LOG_ID"],
                    "STATUS_ID": oaseConst.OSTS_Completed_Abend # "7"
                }
                self.wsDb.table_update(oaseConst.T_OASE_ACTION_LOG, data_list, 'ACTION_LOG_ID')
                self.wsDb.db_commit()
            else:
                # Actionのセットに成功
                conductor_instance_id = result['conductor_instance_id']
                tmp_msg = g.appmsg.get_log_message("BKY-90020", [conductor_instance_id])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                # 評価結果の更新（コンダクター情報のみをセット）
                data_list = {
                    "ACTION_LOG_ID": action_log_row_info["ACTION_LOG_ID"],
                    "CONDUCTOR_INSTANCE_ID": conductor_instance_id
                }
                self.wsDb.table_update(oaseConst.T_OASE_ACTION_LOG, data_list, 'ACTION_LOG_ID')
                self.wsDb.db_commit()

    def checkExecuting(self):
        # 実行中と完了確認済みを抽出
        status_list = [oaseConst.OSTS_Executing, oaseConst.OSTS_Completion_Conf]
        action_log_row_info_list = self.getActionLogInfo(status_list)

        for action_log_row_info in action_log_row_info_list:
            # 「完了確認済み」なら結論イベント登録のみ
            # if action_log_row_info['STATUS_ID'] == oaseConst.OSTS_Completion_Conf:
            #     InsertConclusionEvent(self.EventObj, self.LabelMasterDict, action_log_row_info, action_log_row_info['EVENT_ID_LIST'], action_log_row_info['CONCLUSION_LABELS'])
            #     # ここでステータスを更新しないと結論イベントを登録しつづけてしまう
            #     continue

            action_log_id = action_log_row_info["ACTION_LOG_ID"]
            rule_id = action_log_row_info["RULE_ID"]

            Data_Error = False
            if not action_log_row_info['JOIN_CONDUCTOR_INSTANCE_ID']:
                # T_COMN_CONDUCTOR_INSTANCEに対象レコードなし
                tmp_msg = g.appmsg.get_log_message("BKY-90034", [action_log_id, action_log_row_info["CONDUCTOR_INSTANCE_ID"]])
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))
                Data_Error = True
            else:
                if action_log_row_info['TAB_B_DISUSE_FLAG'] != '0':
                    # T_COMN_CONDUCTOR_INSTANCEの対象レコードが廃止
                    tmp_msg = g.appmsg.get_log_message("BKY-90035", [action_log_id, action_log_row_info["CONDUCTOR_INSTANCE_ID"]])
                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))
                    Data_Error = True

            if not action_log_row_info['JOIN_RULE_ID']:
                # T_OASE_RULEに対象レコードなし
                tmp_msg = g.appmsg.get_log_message("BKY-90036", [action_log_id, rule_id])
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))
                Data_Error = True
            else:
                if action_log_row_info['TAB_C_DISUSE_FLAG'] != '0':
                    # T_OASE_RULEの対象レコードが廃止
                    tmp_msg = g.appmsg.get_log_message("BKY-90037", [action_log_id, rule_id])
                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))
                    Data_Error = True
                elif action_log_row_info['RULE_AVAILABLE_FLAG'] != '1':
                    # T_OASE_RULEの対象レコードが無効
                    tmp_msg = g.appmsg.get_log_message("BKY-90037", [action_log_id, rule_id])
                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    Data_Error = True

            # 評価結果にリンクするデータベースのレコードが不正の場合
            if Data_Error is True:
                action_log_row_info['STATUS_ID'] = oaseConst.OSTS_Completed_Abend  # "7"完了（異常）
            else:
                TargetStatusList = []
                TargetStatusList.append(oaseConst.CSTS_Completed)         # 正常終了
                TargetStatusList.append(oaseConst.CSTS_Abend)             # 異常終了
                TargetStatusList.append(oaseConst.CSTS_Warning_end)       # 警告終了
                TargetStatusList.append(oaseConst.CSTS_Emergency_stop)    # 緊急停止
                TargetStatusList.append(oaseConst.CSTS_Schedule_Cancel)   # 予約取消
                TargetStatusList.append(oaseConst.CSTS_Unexpected_Error)  # 想定外エラー

                # CONDUCTORの状態判定
                if action_log_row_info['CONDUCTOR_STATUS_ID'] not in TargetStatusList:
                    continue

                if action_log_row_info['CONDUCTOR_STATUS_ID'] == oaseConst.CSTS_Completed:
                    action_log_row_info['STATUS_ID'] = oaseConst.OSTS_Completed  # "6"完了
                else:
                    action_log_row_info['STATUS_ID'] = oaseConst.OSTS_Completed_Abend  # "7"完了（異常）

            # 評価結果を更新（完了か完了異常）
            UpdateRow = {}
            for colname in ['ACTION_LOG_ID', 'STATUS_ID']:
                UpdateRow[colname] = action_log_row_info[colname]

            tmp_msg = g.appmsg.get_log_message("BKY-90038", [action_log_row_info["ACTION_LOG_ID"], action_log_row_info["STATUS_ID"]])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))

            self.wsDb.table_update(oaseConst.T_OASE_ACTION_LOG, UpdateRow, 'ACTION_LOG_ID', True)
            self.wsDb.db_commit()

            # # 事後承認が必要
            # if action_log_row_info.get('AFTER_APPROVAL_PENDING'):
            #     data_list = {
            #         "ACTION_LOG_ID": action_log_id,
            #         "STATUS_ID": oaseConst.OSTS_Wait_For_Comp_Conf # "8"完了確認待ち
            #     }
            #     self.wsDb.table_update(oaseConst.T_OASE_ACTION_LOG, data_list, 'ACTION_LOG_ID')
            #     self.wsDb.db_commit()

            # 通知先が設定されている場合、通知処理(事後通知)を実行する
            if action_log_row_info.get('AFTER_NOTIFICATION_DESTINATION'):

                notification_data = Notification_data(self.wsDb, self.EventObj)
                after_Action_Event_List = notification_data.getAfterActionEventList(action_log_row_info)

                tmp_msg = g.appmsg.get_log_message("BKY-90008", ['Post-event notification'])
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                OASE.send(self.wsDb, after_Action_Event_List, {"notification_type": OASENotificationType.AFTER_ACTION, "rule_id": rule_id})

            # 結論イベント登録
            if UpdateRow['STATUS_ID'] == oaseConst.OSTS_Completed:
                # if not action_log_row_info.get('AFTER_APPROVAL_PENDING') and UpdateRow['STATUS_ID'] == oaseConst.OSTS_Completed:
                # 結論イベント登録
                InsertConclusionEvent(self.EventObj, action_log_row_info, action_log_row_info['EVENT_ID_LIST'], action_log_row_info['CONCLUSION_EVENT_LABELS'])

    def getActionLogInfo(self, status_list):
        status_list_str = ",".join(list(map(lambda s: '"{}"'.format(s), status_list)))
        sql = """
            SELECT
                TAB_A.*,
                TAB_B.CONDUCTOR_INSTANCE_ID            AS JOIN_CONDUCTOR_INSTANCE_ID,
                TAB_B.STATUS_ID                        AS CONDUCTOR_STATUS_ID,
                TAB_B.DISUSE_FLAG                      AS TAB_B_DISUSE_FLAG,
                TAB_C.RULE_ID                          AS JOIN_RULE_ID,
                TAB_C.RULE_NAME                        AS RULE_NAME,
                TAB_C.RULE_PRIORITY                    AS RULE_PRIORITY,
                TAB_C.FILTER_A                         AS FILTER_A,
                TAB_C.FILTER_OPERATOR                  AS FILTER_OPERATOR,
                TAB_C.FILTER_B                         AS FILTER_B,
                TAB_C.BEFORE_NOTIFICATION              AS BEFORE_NOTIFICATION,
                TAB_C.BEFORE_APPROVAL_PENDING          AS BEFORE_APPROVAL_PENDING,
                TAB_C.BEFORE_NOTIFICATION_DESTINATION  AS BEFORE_NOTIFICATION_DESTINATION,
                TAB_C.ACTION_ID                        AS ACTION_ID,
                TAB_C.ACTION_LABEL_INHERITANCE_FLAG    AS ACTION_LABEL_INHERITANCE_FLAG,
                TAB_C.EVENT_LABEL_INHERITANCE_FLAG     AS EVENT_LABEL_INHERITANCE_FLAG,
                TAB_C.CONCLUSION_LABEL_SETTINGS        AS CONCLUSION_LABEL_SETTINGS,
                TAB_C.RULE_LABEL_NAME                  AS RULE_LABEL_NAME,
                TAB_C.EVENT_ID_LIST                    AS EVENT_ID_LIST,
                TAB_C.TTL                              AS TTL,
                TAB_C.AFTER_APPROVAL_PENDING           AS AFTER_APPROVAL_PENDING,
                TAB_C.AFTER_NOTIFICATION               AS AFTER_NOTIFICATION,
                TAB_C.AFTER_NOTIFICATION_DESTINATION   AS AFTER_NOTIFICATION_DESTINATION,
                TAB_C.AVAILABLE_FLAG                   AS RULE_AVAILABLE_FLAG,
                TAB_C.DISUSE_FLAG                      AS TAB_C_DISUSE_FLAG
            FROM
                T_OASE_ACTION_LOG                       TAB_A
                LEFT JOIN T_COMN_CONDUCTOR_INSTANCE     TAB_B ON (TAB_A.CONDUCTOR_INSTANCE_ID = TAB_B.CONDUCTOR_INSTANCE_ID)
                LEFT JOIN T_OASE_RULE                   TAB_C ON (TAB_A.RULE_ID = TAB_C.RULE_ID )
            WHERE
                TAB_A.STATUS_ID in ({})
                AND TAB_A.DISUSE_FLAG = '0'
            """.format(status_list_str)

        action_log_row_info_list = self.wsDb.sql_execute(sql, [])

        tmp_msg = g.appmsg.get_log_message("BKY-90033", [len(action_log_row_info_list)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))

        return action_log_row_info_list
