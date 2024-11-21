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
import traceback

from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.util import arrange_stacktrace_format, get_iso_datetime
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs

from common_libs.oase.const import oaseConst
from common_libs.oase.manage_events import ManageEvents
from common_libs.notification.sub_classes.oase import OASE, OASENotificationType

from libs.common_functions import addline_msg, InsertConclusionEvent, getRuleList, getFilterIDMap
from libs.judgement import Judgement
from libs.action import Action
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
    g.applogger.debug(tmp_msg)  # noqa: F405

    # strage_path = os.environ.get('STORAGEPATH')
    # workspace_path = strage_path + "/".join([organization_id, workspace_id])

    # connect MongoDB
    wsMongo = MONGOConnectWs()
    # connect MariaDB
    wsDb = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # 処理時間
        judgeTime = int(datetime.datetime.now().timestamp())
        # イベント操作クラス
        EventObj = ManageEvents(wsMongo, judgeTime)
        # アクション　クラス生成
        actionObj = Action(wsDb, EventObj)

        # ルール判定
        tmp_msg = g.appmsg.get_log_message("BKY-90001", ['Started'])
        g.applogger.debug(tmp_msg)  # noqa: F405
        ret = JudgeMain(wsDb, judgeTime, EventObj, actionObj)
        if ret is False:
            tmp_msg = g.appmsg.get_log_message("BKY-90001", ['Ended without evaluating events'])
            g.applogger.info(tmp_msg)  # noqa: F405
        else:
            tmp_msg = g.appmsg.get_log_message("BKY-90001", ['Ended'])
            g.applogger.info(tmp_msg)  # noqa: F405

        # 評価結果のステータスを監視するクラス
        action_status_monitor = ActionStatusMonitor(wsDb, EventObj)

        # アクションの実行
        tmp_msg = g.appmsg.get_log_message("BKY-90072", ['Started'])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        action_status_monitor.checkRuleMatch(actionObj)
        tmp_msg = g.appmsg.get_log_message("BKY-90072", ['Ended'])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # アクション実行後の通知と結論イベント登録
        tmp_msg = g.appmsg.get_log_message("BKY-90002", ['Started'])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        action_status_monitor.checkExecuting()
        tmp_msg = g.appmsg.get_log_message("BKY-90002", ['Ended'])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    except Exception as e:
        t = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
        tmp_msg = g.appmsg.get_log_message("BKY-90003", [])
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    finally:
        wsDb.db_transaction_end(False)
        wsDb.db_disconnect()
        wsMongo.disconnect()

    # メイン処理終了
    tmp_msg = g.appmsg.get_log_message("BKY-90000", ['Ended'])
    g.applogger.info(tmp_msg)  # noqa: F405

    return


def JudgeMain(wsDb, judgeTime, EventObj, actionObj):
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
            tmp_msg = g.appmsg.get_log_message("BKY-90008", ['Known(timeout)'])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            OASE.send(wsDb, timeout_notification_list, {"notification_type": OASENotificationType.TIMEOUT})

    # 「フィルター管理」からレコードのリストを取得
    filterIDMap = getFilterIDMap(wsDb)
    if filterIDMap is False:
        return False

    #「ルール管理」からレコードのリストを取得（優先順位のソートあり）
    ret_bool, ruleList = getRuleList(wsDb, True)
    if ret_bool is False:
        g.applogger.debug(addline_msg('{}'.format(ruleList)))  # noqa: F405
        return False

    tmp_msg = g.appmsg.get_log_message("BKY-90011", [str(len(ruleList))])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # ルール判定　クラス生成
    judgeObj = Judgement(wsDb, EventObj)

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

    for filterId, filterRow in filterIDMap.items():
        ret, JudgeEventId = judgeObj.getFilterMatch(filterRow)
        if ret is True:
            tmp_msg = g.appmsg.get_log_message("BKY-90014", [filterId, JudgeEventId])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            IncidentDict[filterId] = JudgeEventId
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

    while True:
        # レベル毎のループ -----
        for TargetLevel in JudgeLevelList:
            newIncidentCount[TargetLevel] = 0

            # 各レベルに対応したルール抽出
            TargetRuleList = judgeObj.TargetRuleExtraction(TargetLevel, ruleList, FiltersUsedinRulesDict, IncidentDict)

            newIncident_Flg = True
            tmp_msg = g.appmsg.get_log_message("BKY-90017", [TargetLevel, 'Started'])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # レベル毎の結論イベント未発生確認のループ -----
            while newIncident_Flg is True:
                newIncident_Flg = False
                # レベル毎のルール判定のループ -----
                for ruleInfo in TargetRuleList:
                    # ルール判定
                    ret, UseEventIdList = judgeObj.RuleJudge(ruleInfo, IncidentDict, actionIdList, filterIDMap)

                    # ルール判定 マッチ
                    if ret is True:
                        # 判定済みの結果を評価結果に登録
                        action_log_row = actionObj.RegisterActionLog(ruleInfo, UseEventIdList, judgeObj.LabelMasterDict)

                        if action_log_row.get("ACTION_ID", ""):
                            # アクションが設定されている場合・・・ループの外での実行処理を待つ
                            pass
                        else:
                            # アクションが設定されていない場合・・・すぐに結論イベントを出す
                            # 結論イベントの登録
                            ret, ConclusionEventRow = InsertConclusionEvent(EventObj, ruleInfo, UseEventIdList, action_log_row['CONCLUSION_EVENT_LABELS'])
                            # 結論イベントに処理で必要なラベル情報を追加
                            ConclusionEventRow = EventObj.add_local_label(ConclusionEventRow, oaseConst.DF_LOCAL_LABLE_NAME, oaseConst.DF_LOCAL_LABLE_STATUS, oaseConst.DF_PROC_EVENT)

                            # 結論イベントに対応するフィルタ確認
                            ret, UsedFilterIdList = judgeObj.ConclusionLabelUsedInFilter(action_log_row["CONCLUSION_EVENT_LABELS"], filterIDMap)

                            tmp_msg = g.appmsg.get_log_message("BKY-90021", [str(ret)])
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                            if ret is True:
                                for UsedFilterId in UsedFilterIdList:
                                    tmp_msg = g.appmsg.get_log_message("BKY-90022", [UsedFilterId, ConclusionEventRow['_id']])
                                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                                    if UsedFilterId in IncidentDict:
                                        if type(IncidentDict[UsedFilterId]) is list:
                                            IncidentDict[UsedFilterId].append(ConclusionEventRow['_id'])
                                        else:
                                            IncidentDict[UsedFilterId] = [IncidentDict[UsedFilterId], ConclusionEventRow['_id']]
                                    else:
                                        IncidentDict[UsedFilterId] = ConclusionEventRow['_id']

                                    EventObj.append_event(ConclusionEventRow)
                                    newIncident_Flg = True
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
                if newIncident_Flg is True:
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
                        newIncident_Flg = False
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
    UnusedEventIdList = EventObj.get_unused_event(IncidentDict, filterIDMap)
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
