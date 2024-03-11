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

class ActionStatusMonitor():
    def __init__(self, wsDb, wsMongo, EventObj):
        self.wsDb = wsDb
        self.wsMongo = wsMongo
        self.EventObj = EventObj

        # ラベルマスタ取得
        self.LabelMasterDict = getLabelGroup(wsDb)

    def checkExecuting(self):
        sql = """
            SELECT
                TAB_A.*,
                TAB_B.CONDUCTOR_INSTANCE_ID       AS JOIN_CONDUCTOR_INSTANCE_ID,
                TAB_B.STATUS_ID                   AS CONDUCTOR_STATUS_ID,
                TAB_B.DISUSE_FLAG                 AS TAB_B_DISUSE_FLAG,
                TAB_C.RULE_ID                     AS JOIN_RULE_ID,
                TAB_C.RULE_NAME                   AS RULE_NAME,
                TAB_C.CONCLUSION_LABEL_SETTINGS   AS CONCLUSION_LABEL_SETTINGS,
                TAB_C.RULE_LABEL_NAME             AS RULE_LABEL_NAME,
                TAB_C.EVENT_ID_LIST               AS EVENT_ID_LIST,
                TAB_C.TTL                         AS TTL,
                TAB_C.DISUSE_FLAG                 AS TAB_C_DISUSE_FLAG
            FROM
                T_OASE_ACTION_LOG                   TAB_A
                LEFT JOIN T_COMN_CONDUCTOR_INSTANCE TAB_B ON (TAB_A.CONDUCTOR_INSTANCE_ID = TAB_B.CONDUCTOR_INSTANCE_ID)
                LEFT JOIN T_OASE_RULE               TAB_C ON (TAB_A.RULE_ID               = TAB_C.RULE_ID )
            WHERE
                TAB_A.STATUS_ID in ("{}", "{}") AND
                TAB_A.DISUSE_FLAG = '0'
            """.format(oaseConst.OSTS_Executing, oaseConst.OSTS_Completion_Conf)
        Rows = self.wsDb.sql_execute(sql, [])

        tmp_msg = g.appmsg.get_log_message("BKY-90033", [len(Rows)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))
        for Row in Rows:
            Data_Error = False
            if not Row['JOIN_CONDUCTOR_INSTANCE_ID']:
                # T_COMN_CONDUCTOR_INSTANCEに対象レコードなし
                tmp_msg = g.appmsg.get_log_message("BKY-90034", [Row["ACTION_LOG_ID"], Row["CONDUCTOR_INSTANCE_ID"]])
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))
                Data_Error = True
            else:
                if Row['TAB_B_DISUSE_FLAG'] != '0':
                    # T_COMN_CONDUCTOR_INSTANCEの対象レコードが廃止
                    tmp_msg = g.appmsg.get_log_message("BKY-90035", [Row["ACTION_LOG_ID"], Row["CONDUCTOR_INSTANCE_ID"]])
                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))
                    Data_Error = True

            if not Row['JOIN_RULE_ID']:
                # T_OASE_RULEに対象レコードなし
                tmp_msg = g.appmsg.get_log_message("BKY-90036", [Row["ACTION_LOG_ID"], Row["RULE_ID"]])
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))
                Data_Error = True
            else:
                if Row['TAB_C_DISUSE_FLAG'] != '0':
                    # T_OASE_RULEの対象レコードが廃止
                    tmp_msg = g.appmsg.get_log_message("BKY-90037", [Row["ACTION_LOG_ID"], Row["RULE_ID"]])
                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))
                    Data_Error = True

            TargetStatusList = []
            TargetStatusList.append(oaseConst.CSTS_Completed)         # 正常終了
            TargetStatusList.append(oaseConst.CSTS_Abend)             # 異常終了
            TargetStatusList.append(oaseConst.CSTS_Warning_end)       # 警告終了
            TargetStatusList.append(oaseConst.CSTS_Emergency_stop)    # 緊急停止
            TargetStatusList.append(oaseConst.CSTS_Schedule_Cancel)   # 予約取消
            TargetStatusList.append(oaseConst.CSTS_Unexpected_Error)  # 想定外エラー
            # CONDUCTORの状態判定
            if Row['CONDUCTOR_STATUS_ID'] in TargetStatusList:
                # 通知処理(作業後)
                rule_id = Row["RULE_ID"]
                # 「ルール管理」からレコードを取得
                # ソート条件不要
                ret_rule = self.wsDb.table_select('T_OASE_RULE', 'WHERE DISUSE_FLAG = %s AND AVAILABLE_FLAG = %s AND RULE_ID = %s', [0, 1, rule_id])
                if not ret_rule:
                    tmp_msg = g.appmsg.get_log_message("BKY-90009", ['T_OASE_RULE'])
                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                elif ret_rule[0].get('AFTER_NOTIFICATION_DESTINATION'):
                    # 通知先が設定されている場合、通知処理(作業後)を実行する
                    # 2.3の時点では、イベントの情報は空にしておく
                    after_Action_Event_List = [{}]

                    tmp_msg = g.appmsg.get_log_message("BKY-90008", ['Post-event notification'])
                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    OASE.send(self.wsDb, after_Action_Event_List, {"notification_type": OASENotificationType.AFTER_ACTION, "rule_id": Row["RULE_ID"]})

                if Row['CONDUCTOR_STATUS_ID'] == oaseConst.CSTS_Completed:
                    Row['STATUS_ID'] = oaseConst.OSTS_Completed
                else:
                    Row['STATUS_ID'] = oaseConst.OSTS_Completed_Abend
            else:
                continue

            # 評価結果にリンクするデータベースのレコードが不正の場合
            if Data_Error is True:
                Row['STATUS_ID'] = oaseConst.OSTS_Completed_Abend

            # 評価結果更新
            UpdateRow = {}
            for colname in ['ACTION_LOG_ID', 'STATUS_ID']:
                UpdateRow[colname] = Row[colname]

            tmp_msg = g.appmsg.get_log_message("BKY-90038", [Row["ACTION_LOG_ID"], Row["STATUS_ID"]])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))

            self.wsDb.table_update('T_OASE_ACTION_LOG', UpdateRow, 'ACTION_LOG_ID', True)
            self.wsDb.db_commit()

            # 結論イベント登録
            if UpdateRow['STATUS_ID'] in [oaseConst.OSTS_Completed]:
                # 結論イベント登録
                InsertConclusionEvent(self.EventObj, self.LabelMasterDict, Row, Row['EVENT_ID_LIST'], Row[''])

