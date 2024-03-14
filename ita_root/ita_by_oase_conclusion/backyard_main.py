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
import os
import datetime
import json


from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs

from common_libs.oase.const import oaseConst
from common_libs.oase.manage_events import ManageEvents
from common_libs.notification.sub_classes.oase import OASE, OASENotificationType

from libs.common_functions import addline_msg, generateConclusionLables, InsertConclusionEvent
from libs.judgement import Judgement
from libs.action_run import action_run
from libs.action_status_monitor import ActionStatusMonitor

def backyard_main(organization_id, workspace_id):
    """
        OASE評価機能backyardメイン処理
        ARGS:
            organization_id: Organization ID
            workspace_id: Workspace ID
        RETURN:
    """
    # メイン処理開始
    tmp_msg = g.appmsg.get_log_message("BKY-90000", ['Started'])
    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    strage_path = os.environ.get('STORAGEPATH')
    workspace_path = strage_path + "/".join([organization_id, workspace_id])

    # connect MongoDB
    wsMongo = MONGOConnectWs()
    # connect MariaDB
    wsDb = DBConnectWs(workspace_id)  # noqa: F405

    # 処理時間
    judgeTime = int(datetime.datetime.now().timestamp())
    EventObj = ManageEvents(wsMongo, judgeTime)
    # EventObj.print_event()

    # ①ルールマッチ
    tmp_msg = g.appmsg.get_log_message("BKY-90001", ['Started'])
    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    ret = JudgeMain(wsDb, wsMongo, judgeTime, EventObj)
    if ret is False:
        tmp_msg = g.appmsg.get_log_message("BKY-90003", [])
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    tmp_msg = g.appmsg.get_log_message("BKY-90001", ['Ended'])
    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # ②アクション実行後通知と結論イベント登録
    tmp_msg = g.appmsg.get_log_message("BKY-90002", ['Started'])
    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    obj = ActionStatusMonitor(wsDb, wsMongo, EventObj)
    obj.checkExecuting()
    tmp_msg = g.appmsg.get_log_message("BKY-90002", ['Ended'])
    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # メイン処理終了
    tmp_msg = g.appmsg.get_log_message("BKY-90000", ['Ended'])
    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    return


def JudgeMain(wsDb, wsMongo, judgeTime, EventObj):
    IncidentDict = {}

    # 対象イベントがない
    count = EventObj.count_events()
    if count == 0:
        tmp_msg = g.appmsg.get_log_message("BKY-90004", [])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False
    tmp_msg = g.appmsg.get_log_message("BKY-90005", [judgeTime, count])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # タイムアウト（TTL*2）の抽出
    timeout_Event_Id_List = EventObj.get_timeout_event()
    tmp_msg = g.appmsg.get_log_message("BKY-90006", [len(timeout_Event_Id_List)])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # タイムアウトイベント有無判定
    if len(timeout_Event_Id_List) > 0:
        # タイムアウトしているイベントの_exastro_timeoutを1に更新
        update_Flag_Dict = {"_exastro_timeout": '1'}
        EventObj.update_label_flag(timeout_Event_Id_List, update_Flag_Dict)
        tmp_msg = g.appmsg.get_log_message("BKY-90007", [str(update_Flag_Dict), str(timeout_Event_Id_List)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # 通知処理（既知(時間切れ)）
        timeout_notification_list = []
        for event_id in timeout_Event_Id_List:
            ret, EventRow = EventObj.get_events(event_id)
            if ret is True:
                timeout_notification_list.append(EventRow)

        if len(timeout_notification_list) > 0:
            tmp_msg = g.appmsg.get_log_message("BKY-90008", ['Known (timeout)'])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            OASE.send(wsDb, timeout_notification_list, {"notification_type": OASENotificationType.TIMEOUT})

    # 「フィルター管理」からレコードのリストを取得
    filterList = wsDb.table_select(oaseConst.T_OASE_FILTER, 'WHERE DISUSE_FLAG = %s AND AVAILABLE_FLAG = %s', [0, 1])
    if not filterList:
        tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_FILTER])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False
    tmp_msg = g.appmsg.get_log_message("BKY-90010", [str(len(filterList))])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    #「ルール管理」からレコードのリストを取得（優先順位のソートあり）
    ret_bool, ruleList = getRuleList(wsDb, True)
    if ret_bool is False:
        g.applogger.debug(addline_msg('{}'.format(ruleList)))  # noqa: F405
        return False

    tmp_msg = g.appmsg.get_log_message("BKY-90011", [str(len(ruleList))])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # ルール判定　クラス生成
    judgeObj = Judgement(wsDb, wsMongo, EventObj)

    new_Event_List = []
    new_Event_id_List = []
    for Event_id, EventRow in EventObj.labeled_events_dict.items():
        # 結論イベントは通知対象外にする。
        if EventRow['labels']['_exastro_type'] == 'conclusion':
            continue
        # 新規イベント通知済みの場合は通知対象外にする。
        if EventRow['labels']['_exastro_checked'] == '1':
            continue
        new_Event_List.append(EventRow)
        new_Event_id_List.append(Event_id)

    # 通知処理（新規）
    if len(new_Event_List) > 0:
        tmp_msg = g.appmsg.get_log_message("BKY-90008", ['new'])
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        OASE.send(wsDb, new_Event_List, {"notification_type": OASENotificationType.NEW})

    # 新規イベント通知済みインシデントフラグを立てる  _exastro_checked='1'
    update_Flag_Dict = {"_exastro_checked": '1'}
    # MongoDBのインシデント情報を更新
    EventObj.update_label_flag(new_Event_id_List, update_Flag_Dict)
    tmp_msg = g.appmsg.get_log_message("BKY-90012", [str(update_Flag_Dict), str(new_Event_id_List)])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # フィルタリング開始
    tmp_msg = g.appmsg.get_log_message("BKY-90013", ['Started'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    newIncident = False
    for filterRow in filterList:
        filterId = filterRow["FILTER_ID"]
        ret, JudgeEventId = judgeObj.getFilterMatch(filterRow)
        if ret is True:
            tmp_msg = g.appmsg.get_log_message("BKY-90014", [filterId, JudgeEventId])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            IncidentDict[filterId] = JudgeEventId
            newIncident = True
        else:
            # 複数のイベントがマッチしている場合
            if len(JudgeEventId) > 0:
                IncidentDict[filterId] = JudgeEventId
            tmp_msg = g.appmsg.get_log_message("BKY-90015", [filterId, str(JudgeEventId)])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    tmp_msg = g.appmsg.get_log_message("BKY-90013", ['Ended'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # ルールで使用しているフィルタを集計
    FiltersUsedinRulesDict = judgeObj.SummaryofFiltersUsedinRules(ruleList)

    tmp_msg = g.appmsg.get_log_message("BKY-90016", ['Started'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # 「アクション」からレコードを取得
    actionIdList = []
    ret_action = wsDb.table_select(oaseConst.T_OASE_ACTION, 'WHERE DISUSE_FLAG = %s', [0])
    if not ret_action:
        tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_ACTION])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    else:
        for actionRow in ret_action:
            actionIdList.append(actionRow['ACTION_ID'])

    # Level1:複数のルールで使用していないフィルタを使用しているルール
    # Level2:複数のルールで使用しているフィルタで優先順位が最上位のルール
    # Level3:複数のルールで使用しているフィルタでタイムアウトを迎えるフィルタを使用しているルール
    JudgeLevelList = ['Level1', 'Level2', 'Level3']

    # 全レベルループ -----
    newIncidentCount = {}
    # newConclusionEventList = []

    while True:
        # レベル毎のループ -----
        for TargetLevel in JudgeLevelList:
            newIncidentCount[TargetLevel] = 0

            # 各レベルに対応したルール抽出
            TargetRuleList = judgeObj.TargetRuleExtraction(TargetLevel, ruleList, FiltersUsedinRulesDict, IncidentDict)

            newIncident = True
            tmp_msg = g.appmsg.get_log_message("BKY-90017", [TargetLevel, 'Started'])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # レベル毎の結論イベント未発生確認のループ -----
            while newIncident is True:
                newIncident = False
                # レベル毎のルール判定のループ -----
                for ruleRow in TargetRuleList:
                    # ルール判定
                    ret, UseEventIdList = judgeObj.RuleJudge(ruleRow, IncidentDict, actionIdList, filterList)

                    # ルール判定 マッチ
                    if ret is True:
                        # アクションに利用 & 結論イベントに付与 するラベルを生成する
                        conclusion_lables = generateConclusionLables(EventObj, UseEventIdList, ruleRow, judgeObj.LabelMasterDict)

                        # 評価結果に登録するアクション情報を取得（ある場合）
                        action_id = ruleRow.get("ACTION_ID")
                        action_name = ""
                        conductor_class_id = None
                        conductor_name = ""
                        operation_id = None
                        operation_name = ""
                        if action_id is not None:
                            # 「アクション」からレコードを取得
                            ret_action = wsDb.table_select(oaseConst.T_OASE_ACTION, 'WHERE DISUSE_FLAG = %s AND ACTION_ID = %s', [0, action_id])
                            if not ret_action:
                                tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_ACTION])
                                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            else:
                                action_name = ret_action[0].get("ACTION_NAME")
                                conductor_class_id = ret_action[0].get("CONDUCTOR_CLASS_ID")
                                operation_id = ret_action[0].get("OPERATION_ID")

                                if conductor_class_id is not None:
                                    # 「コンダクターインスタンス」からレコードを取得
                                    ret_conductor = wsDb.table_select('T_COMN_CONDUCTOR_CLASS', 'WHERE DISUSE_FLAG = %s AND CONDUCTOR_CLASS_ID = %s', [0, conductor_class_id])
                                    if not ret_conductor:
                                        tmp_msg = g.appmsg.get_log_message("BKY-90009", ['T_COMN_CONDUCTOR_CLASS'])
                                        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                    else:
                                        conductor_name = ret_conductor[0].get("CONDUCTOR_NAME")

                                if operation_id is not None:
                                    # 「オペレーション」からレコードを取得
                                    ret_operation = wsDb.table_select('T_COMN_OPERATION', 'WHERE DISUSE_FLAG = %s AND OPERATION_ID = %s', [0, operation_id])
                                    if not ret_operation:
                                        tmp_msg = g.appmsg.get_log_message("BKY-90009", ['T_COMN_OPERATION'])
                                        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                    else:
                                        operation_name = ret_operation[0].get("OPERATION_NAME")

                        # 評価結果へ登録
                        # トランザクション開始
                        wsDb.db_transaction_start()
                        row = {
                            "RULE_ID": ruleRow.get("RULE_ID"),
                            "RULE_NAME": ruleRow.get("RULE_NAME"),
                            "STATUS_ID": oaseConst.OSTS_Rule_Match, # 1:判定済み
                            "ACTION_ID": action_id,
                            "ACTION_NAME": action_name,
                            "CONDUCTOR_INSTANCE_ID": conductor_class_id,
                            "CONDUCTOR_INSTANCE_NAME": conductor_name,
                            "OPERATION_ID": operation_id,
                            "OPERATION_NAME": operation_name,
                            "EVENT_ID_LIST": ','.join(map(repr, UseEventIdList)),
                            "CONCLUSION_LABELS": json.dumps(conclusion_lables),
                            "TIME_REGISTER": datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                            "NOTE": None,
                            "DISUSE_FLAG": "0",
                            "LAST_UPDATE_USER": g.get('USER_ID')
                        }
                        wsDb.table_insert('T_OASE_ACTION_LOG', row, 'ACTION_LOG_ID', True)

                        # 使用済みインシデントフラグを立てる  _exastro_evaluated='1'
                        update_Flag_Dict = {"_exastro_evaluated": '1'}
                        # MongoDBのインシデント情報を更新
                        EventObj.update_label_flag(UseEventIdList, update_Flag_Dict)
                        tmp_msg = g.appmsg.get_log_message("BKY-90018", [str(update_Flag_Dict), str(UseEventIdList)])
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                        NotificationEventList = []
                        for Event_id in UseEventIdList:
                            ret, EventRow = EventObj.get_events(Event_id)
                            if ret is True:
                                NotificationEventList.append(EventRow)

                        # 通知処理（既知（判定済み））
                        if len(NotificationEventList) > 0:
                            tmp_msg = g.appmsg.get_log_message("BKY-90008", ['Known (evaluated)'])
                            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            OASE.send(wsDb, NotificationEventList, {"notification_type": OASENotificationType.EVALUATED})

                        # コミット  トランザクション終了
                        wsDb.db_transaction_end(True)

                        # 評価結果から判定済みのレコードを取得
                        ret_action_log = wsDb.table_select(oaseConst.T_OASE_ACTION_LOG, 'WHERE DISUSE_FLAG = %s AND STATUS_ID = %s', [0, oaseConst.OSTS_Rule_Match])
                        if not ret_action_log:
                            tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_ACTION_LOG])
                            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            return False

                        # ルールにアクションが設定してあるか判定する
                        for action_log_row in ret_action_log:
                            if action_log_row["ACTION_ID"]:
                            # アクションが設定されている場合
                                # 通知処理(事前通知)
                                rule_id = action_log_row["RULE_ID"]
                                # 「ルール管理」から対象レコードを取得
                                ret_rule = wsDb.table_select(oaseConst.T_OASE_RULE, 'WHERE DISUSE_FLAG = %s AND AVAILABLE_FLAG = %s AND RULE_ID = %s', [0, 1, rule_id])
                                if not ret_rule:
                                    tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_RULE])
                                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                    return False

                                if ret_rule[0].get('BEFORE_NOTIFICATION_DESTINATION'):
                                    # 通知先が設定されている場合、通知処理(事前通知)を実行する
                                    # 2.3の時点では、イベントの情報は空にしておく
                                    before_Action_Event_List = [{}]

                                    tmp_msg = g.appmsg.get_log_message("BKY-90008", ['Advance notice'])
                                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                    OASE.send(wsDb, before_Action_Event_List, {"notification_type": OASENotificationType.BEFORE_ACTION, "rule_id": action_log_row["RULE_ID"]})

                                # 評価結果の更新（実行中）
                                data_list = {
                                    "ACTION_LOG_ID": action_log_row["ACTION_LOG_ID"],
                                    "STATUS_ID": oaseConst.OSTS_Executing # "2"
                                }
                                wsDb.table_update(oaseConst.T_OASE_ACTION_LOG, data_list, 'ACTION_LOG_ID')
                                wsDb.db_commit()

                                # action実行
                                retBool, result = action_run(wsDb, action_log_row)
                                if retBool is False:
                                    tmp_msg = g.appmsg.get_log_message("BKY-90019", [result])
                                    g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                    # 評価結果の更新（完了（異常））
                                    data_list = {
                                        "ACTION_LOG_ID": action_log_row["ACTION_LOG_ID"],
                                        "STATUS_ID": oaseConst.OSTS_Completed_Abend # "7"
                                    }
                                    wsDb.table_update(oaseConst.T_OASE_ACTION_LOG, data_list, 'ACTION_LOG_ID')
                                    wsDb.db_commit()
                                else:
                                    conductor_instance_id = result['conductor_instance_id']
                                    tmp_msg = g.appmsg.get_log_message("BKY-90020", [conductor_instance_id])
                                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                    data_list = {
                                        "ACTION_LOG_ID": action_log_row["ACTION_LOG_ID"],
                                        "CONDUCTOR_INSTANCE_ID": conductor_instance_id
                                    }
                                    wsDb.table_update(oaseConst.T_OASE_ACTION_LOG, data_list, 'ACTION_LOG_ID')
                                    wsDb.db_commit()
                            else:
                            # アクションが設定されていない場合
                                # 結論イベント登録
                                ret, ConclusionEventRow = InsertConclusionEvent(EventObj, ruleRow, UseEventIdList, action_log_row['CONCLUSION_LABELS'])

                                # 新規イベントの通知用に結論イベント登録
                                # newConclusionEventList.append(ConclusionEventRow)

                                # 結論イベントに処理で必要なラベル情報を追加
                                ConclusionEventRow = EventObj.add_local_label(ConclusionEventRow, oaseConst.DF_LOCAL_LABLE_NAME, oaseConst.DF_LOCAL_LABLE_STATUS, oaseConst.DF_PROC_EVENT)

                                FilterCheckLabelDict = ruleRow["CONCLUSION_LABEL_SETTINGS"]

                                # 結論イベントに対応するフィルタ確認
                                ret, UsedFilterIdList = judgeObj.ConclusionLabelUsedInFilter(FilterCheckLabelDict, filterList)

                                tmp_msg = g.appmsg.get_log_message("BKY-90021", [str(ret)])
                                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                                if ret is True:
                                    for UsedFilterId in UsedFilterIdList:
                                        tmp_msg = g.appmsg.get_log_message("BKY-90022", [UsedFilterId, ConclusionEventRow['_id']])
                                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                        IncidentDict[UsedFilterId] = ConclusionEventRow['_id']

                                        EventObj.append_event(ConclusionEventRow)
                                        newIncident = True
                                # 評価結果の更新（完了）
                                data_list = {
                                    "ACTION_LOG_ID": action_log_row["ACTION_LOG_ID"],
                                    "STATUS_ID": oaseConst.OSTS_Completed # "6"
                                }
                                wsDb.table_update(oaseConst.T_OASE_ACTION_LOG, data_list, 'ACTION_LOG_ID')
                                wsDb.db_commit()
                    else:
                        # ルール判定 アンマッチ
                        pass

                # ----- レベル毎のルール判定のループ
                # 結論イベントの追加判定
                if newIncident is True:
                    newIncidentCount[TargetLevel] += 1
                    tmp_msg = g.appmsg.get_log_message("BKY-90023", [])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    tmp_msg = g.appmsg.get_log_message("BKY-90024", [TargetLevel])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    # ループ回数判定
                    if (len(ruleList) * 10) < newIncidentCount[TargetLevel]:
                        tmp_msg = g.appmsg.get_log_message("BKY-90025", [])
                        g.applogger.warning(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                        # これ以上ループしない設定
                        newIncident = False
                        newIncidentCount[TargetLevel] = 0
                else:
                    tmp_msg = g.appmsg.get_log_message("BKY-90026", [])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # ----- レベル毎の結論イベント未発生確認のループ
            tmp_msg = g.appmsg.get_log_message("BKY-90017", [TargetLevel, 'Ended'])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # ----- レベル毎のループ
        # 各レベルのルール判定で結論イベントが発生していないか確認
        total = 0
        for TargetLevel in JudgeLevelList:
            total += newIncidentCount[TargetLevel]
        # 発生していなかったらループを終了
        if total == 0:
            break

    # ----- 全レベルループ
    tmp_msg = g.appmsg.get_log_message("BKY-90016", ['Ended'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # 処理後タイムアウトイベント検出
    PostProcTimeoutEventIdList = EventObj.get_post_proc_timeout_event()
    if len(PostProcTimeoutEventIdList) > 0:
        tmp_msg = g.appmsg.get_log_message("BKY-90027", [str(PostProcTimeoutEventIdList)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        # 処理後タイムアウトの_exastro_timeoutを1に更新
        update_Flag_Dict = {"_exastro_timeout": '1'}
        EventObj.update_label_flag(PostProcTimeoutEventIdList, update_Flag_Dict)
        tmp_msg = g.appmsg.get_log_message("BKY-90028", [str(update_Flag_Dict), str(PostProcTimeoutEventIdList)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    else:
        tmp_msg = g.appmsg.get_log_message("BKY-90029", [])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # 未知事象フラグを立てる（一括で行う）
    UnusedEventIdList = EventObj.get_unused_event(IncidentDict, filterList)
    if len(UnusedEventIdList) > 0:
        tmp_msg = g.appmsg.get_log_message("BKY-90030", [str(UnusedEventIdList)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        # MongoDBのインシデント情報を更新（一括で行う）
        # 未知イベントの_exastro_undetectedを1に更新
        update_Flag_Dict = {"_exastro_undetected": '1'}
        EventObj.update_label_flag(UnusedEventIdList, update_Flag_Dict)
        tmp_msg = g.appmsg.get_log_message("BKY-90031", [str(update_Flag_Dict), str(UnusedEventIdList)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    else:
        tmp_msg = g.appmsg.get_log_message("BKY-90032", [])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # # 通知処理（新規イベント）
    # new_notification_list = []
    # for EventRow in newConclusionEventList:
    #     # 新規の結論イベントは通知対象外にする。
    #     if EventRow['labels']['_exastro_type'] == 'conclusion':
    #         continue
    #     new_notification_list.append(EventRow)

    # if len(new_notification_list) > 0:
    #     tmp_msg = g.appmsg.get_log_message("BKY-90008", ['new'])
    #     g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    #     OASE.send(wsDb, new_notification_list, {"notification_type": OASENotificationType.NEW})

    # 通知処理（未知）
    unused_notification_list = []
    for Event_id in UnusedEventIdList:
        ret, EventRow = EventObj.get_events(Event_id)
        if ret is True:
            # 未知の結論イベントは通知対象外にする。
            if EventRow['labels']['_exastro_type'] == 'conclusion':
                continue

            unused_notification_list.append(EventRow)

    if len(unused_notification_list) > 0:
        tmp_msg = g.appmsg.get_log_message("BKY-90008", ['Undetected'])
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        OASE.send(wsDb, unused_notification_list, {"notification_type": OASENotificationType.UNDETECTED})


def getRuleList(wsDb, sort_bv_priority=False):
    # 「ルール管理」からレコードを取得
    # ソート条件変更　ORDER BY AVAILABLE_FLAG DESC, RULE_PRIORITY ASC, FILTER_A ASC, FILTER_B DESC
    _ruleList = wsDb.table_select(oaseConst.T_OASE_RULE, 'WHERE DISUSE_FLAG = %s AND AVAILABLE_FLAG = %s ORDER BY AVAILABLE_FLAG DESC, RULE_PRIORITY ASC, FILTER_A ASC, FILTER_B DESC', [0, 1])
    if not _ruleList:
        msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_RULE])
        return False, msg

    if sort_bv_priority is False:
        return True, _ruleList

    # 優先順位を正規化する
    # 優先順位を入力していない場合があるため、ソート順に並べて優先順位プロパティを更新しておく
    ruleList = []
    Priority = 1
    for rule_row in _ruleList:
        rule_row['RULE_PRIORITY'] = Priority
        Priority += 1
        ruleList.append(rule_row)
    return True, ruleList
