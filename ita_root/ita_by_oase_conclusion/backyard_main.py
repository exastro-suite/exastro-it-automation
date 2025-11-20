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

from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.util import arrange_stacktrace_format, get_iso_datetime
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs

from common_libs.oase.const import oaseConst
from common_libs.oase.manage_events import ManageEvents
from common_libs.notification.sub_classes.oase import OASENotificationType

from libs.common_functions import addline_msg, InsertConclusionEvent, getLabelGroup, getRuleList, getFilterIDMap, deduplication_timeout_filter
from libs.judgement import Judgement
from libs.action import Action
from libs.action_status_monitor import ActionStatusMonitor
from libs.notification_process import NotificationProcessManager
from libs.writer_process import WriterProcessManager


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

    NotificationProcessManager.start_workspace_processing(organization_id, workspace_id)
    WriterProcessManager.start_workspace_processing(organization_id, workspace_id)
    
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

        # WriterProcessManagerに遅延書き込みはここまでに完了させる
        #   T_OASE_ACTION_LOGへの参照がここ以降で発生するため、ここまでに書き込みを完了させる
        WriterProcessManager.flush_buffer()

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
    except Exception:
        t = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
        tmp_msg = g.appmsg.get_log_message("BKY-90003", [])
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    finally:
        WriterProcessManager.finish_workspace_processing()
        NotificationProcessManager.finish_workspace_processing()
        wsDb.db_transaction_end(False)
        wsDb.db_disconnect()
        wsMongo.disconnect()

    # メイン処理終了
    tmp_msg = g.appmsg.get_log_message("BKY-90000", ['Ended'])
    g.applogger.info(tmp_msg)  # noqa: F405

    return


def JudgeMain(wsDb: DBConnectWs, judgeTime: int, EventObj: ManageEvents, actionObj: Action):
    IncidentDict = {}

    # 対象イベントがない
    count = EventObj.count_events()
    if count == 0:
        # No events to process
        tmp_msg = g.appmsg.get_log_message("BKY-90004", [])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False

    # Event collected. Time: {} Acquired items: {}
    tmp_msg = g.appmsg.get_log_message("BKY-90005", [judgeTime, count])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # タイムアウト（TTL*2）の抽出
    # Expiration verdict. Timeout number: {}
    timeout_Event_Id_List = EventObj.get_timeout_event()
    tmp_msg = g.appmsg.get_log_message("BKY-90006", [len(timeout_Event_Id_List)])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # タイムアウトイベント有無判定
    if len(timeout_Event_Id_List) > 0:
        # タイムアウトしているイベントの_exastro_timeoutを1に更新
        update_Flag_Dict = {"_exastro_timeout": '1'}
        EventObj.set_timeout(timeout_Event_Id_List)
        # Event updated. Timeout({}) ids: {}
        tmp_msg = g.appmsg.get_log_message("BKY-90007", [str(update_Flag_Dict), str(timeout_Event_Id_List)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        timeout_notification_list = []  # 通知処理（既知(時間切れ)）
        timeout_consolidated_notification_list = []  # 通知処理（新規(統合時) TTL切れ）

        # 新規(統合時) TTL切れ用に予め重複排除設定を取っておく
        deduplication_settings = wsDb.table_select(
            oaseConst.T_OASE_DEDUPLICATION_SETTINGS,
            "WHERE DISUSE_FLAG='0' ORDER BY SETTING_PRIORITY, DEDUPLICATION_SETTING_NAME"
        )
        for event_id in timeout_Event_Id_List:
            ret, EventRow = EventObj.get_events(event_id)
            if ret is True:
                # 通知処理（既知(時間切れ)）用にリストに入れる
                timeout_notification_list.append(EventRow)
                # 通知処理（新規(統合時) TTL切れ）用にリストに入れる
                if len(deduplication_settings) > 0 and deduplication_timeout_filter(deduplication_settings, EventRow) is True:
                    timeout_consolidated_notification_list.append(EventRow)

        # 通知処理（既知(時間切れ)）通知キューに入れる
        if len(timeout_notification_list) > 0:
            tmp_msg = g.appmsg.get_log_message("BKY-90008", ['Known(timeout)'])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            NotificationProcessManager.send_notification(timeout_notification_list, {"notification_type": OASENotificationType.TIMEOUT})

        # 通知処理（新規(統合時) TTL切れ）通知キューに入れる
        if len(timeout_consolidated_notification_list) > 0:
            tmp_msg = g.appmsg.get_log_message("BKY-90008", ['New(consolidated)'])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            # 通知キューに入れておく
            NotificationProcessManager.send_notification(timeout_consolidated_notification_list, {"notification_type": OASENotificationType.DUPLICATE})

    # 「フィルター管理」からレコードのリストを取得
    filterIDMap = getFilterIDMap(wsDb)
    if filterIDMap is False:
        return False

    # 「ルール管理」からレコードのリストを取得（優先順位のソートあり）
    ret_bool, ruleList = getRuleList(wsDb, True)
    if ret_bool is False:
        g.applogger.debug(addline_msg('{}'.format(ruleList)))  # noqa: F405
        return False

    # Acquired rule management. Items: {}
    tmp_msg = g.appmsg.get_log_message("BKY-90011", [str(len(ruleList))])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # ラベルマスタの取得
    label_master = getLabelGroup(wsDb)
    EventObj.init_label_master(label_master)
    # グルーピングの初期化
    EventObj.init_grouping(judgeTime, filterIDMap)
    # ルール判定　クラス生成
    judgeObj = Judgement(wsDb, EventObj, label_master)

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
        NotificationProcessManager.send_notification(new_Event_List, {"notification_type": OASENotificationType.NEW})

    # 新規イベント通知済みインシデントフラグを立てる  _exastro_checked='1'
    update_Flag_Dict = {"_exastro_checked": '1'}
    # MongoDBのインシデント情報を更新
    EventObj.update_label_flag(new_Event_id_List, update_Flag_Dict)
    if len(new_Event_id_List) > 0:
        # Creating new event notification incident flag({}) ids: {}
        tmp_msg = g.appmsg.get_log_message("BKY-90012", [str(update_Flag_Dict), str(new_Event_id_List)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # Filtering process Started
    tmp_msg = g.appmsg.get_log_message("BKY-90013", ['Started'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    for filterId, filterRow in filterIDMap.items():
        ret, JudgeEventId = judgeObj.getFilterMatch(filterRow)
        if ret is True:
            # Filtering verdict results. Matched FILTER_ID: {} EVENT_ID: <<{}>>
            tmp_msg = g.appmsg.get_log_message("BKY-90014", [filterId, JudgeEventId])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            IncidentDict[filterId] = JudgeEventId
        else:
            # Filtering verdict results. No Match FILTER_ID: {} EVENT_ID: <<{}>>
            tmp_msg = g.appmsg.get_log_message("BKY-90015", [filterId, None])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # Filtering process Ended
    tmp_msg = g.appmsg.get_log_message("BKY-90013", ['Ended'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # ルールで使用しているフィルタを集計
    FiltersUsedinRulesDict = judgeObj.SummaryofFiltersUsedinRules(ruleList)

    # Rule match loop process Started
    tmp_msg = g.appmsg.get_log_message("BKY-90016", ['Started'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # 「アクション」からレコードを取得
    actionIdList = []
    ret_action = wsDb.table_select(oaseConst.T_OASE_ACTION, 'WHERE DISUSE_FLAG = %s', [0])
    if not ret_action:
        # No records to process. Table: T_OASE_ACTION
        tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_ACTION])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    else:
        for actionRow in ret_action:
            actionIdList.append(actionRow['ACTION_ID'])

    # Level1:複数のルールで使用していないフィルタを使用しているルール
    # Level2:複数のルールで使用しているフィルタで優先順位が最上位のルール
    # Level3:複数のルールで使用しているフィルタでタイムアウトを迎えるフィルタを使用しているルール
    JudgeLevelList = ['Level1', 'Level2', 'Level3']

    # region 全レベルループ
    newIncidentCount = {}

    # 無限ループ対策用のループ上限値を環境変数から取得
    evaluate_latent_infinite_loop_limit = int(os.environ.get("EVALUATE_LATENT_INFINITE_LOOP_LIMIT", 1000))

    while True:
        # region レベル毎のループ
        for TargetLevel in JudgeLevelList:
            # Level{} Rule verdict Started
            tmp_msg = g.appmsg.get_log_message("BKY-90017", [TargetLevel, 'Started'])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            newIncidentCount[TargetLevel] = 0

            # 各レベルに対応したルール抽出
            TargetRuleList = judgeObj.TargetRuleExtraction(TargetLevel, ruleList, FiltersUsedinRulesDict, IncidentDict)
            g.applogger.debug(addline_msg('TargetRuleList={}'.format(TargetRuleList)))  # noqa: F405

            newIncident_Flg = True
            preserved_events = set()

            # region レベル毎の結論イベント未発生確認のループ
            while newIncident_Flg is True:
                newIncident_Flg = False

                # region レベル毎のルール判定のループ
                for ruleInfo in TargetRuleList:
                    # ルール判定
                    ret, UseEventIdList, judged_result_has_subsequent_event = (
                        judgeObj.RuleJudge(
                            ruleInfo,
                            IncidentDict,
                            actionIdList,
                            filterIDMap,
                            preserved_events,
                        )
                    )

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
                            # キャッシュに保存
                            EventObj.append_event(ConclusionEventRow)

                            # 結論イベントに対応するフィルタ確認
                            ret, UsedFilterIdList = judgeObj.ConclusionLabelUsedInFilter(ConclusionEventRow["labels"], filterIDMap)
                            # Verifying conclusion event filters{}
                            tmp_msg = g.appmsg.get_log_message("BKY-90021", [str(ret)])
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                            if ret is True:
                                for UsedFilterId in UsedFilterIdList:
                                    # Registering link between conclusion event filter and event. FILTER_ID: {} EVENT_ID: {}
                                    tmp_msg = g.appmsg.get_log_message("BKY-90022", [UsedFilterId, ConclusionEventRow['_id']])

                                    if UsedFilterId in IncidentDict:
                                        if len(IncidentDict[UsedFilterId]) > 0:
                                            if filterIDMap[UsedFilterId]["SEARCH_CONDITION_ID"] == '1':
                                                # ユニークのフィルターに既にイベントがある場合
                                                judged_events = []  # 何かしら判定済みのイベントのリスト
                                                unevaluated_events = []  # 未評価のイベントのリスト
                                                for event_id in IncidentDict[UsedFilterId]:
                                                    ret, EventRow = EventObj.get_events(event_id)
                                                    if ret is True:
                                                        if (
                                                            EventRow['labels']['_exastro_evaluated'] == '0' and
                                                            EventRow['labels']['_exastro_timeout'] == '0' and
                                                            EventRow['labels']['_exastro_undetected'] == '0'
                                                        ):
                                                            unevaluated_events.append(event_id)
                                                        else:
                                                            judged_events.append(event_id)
                                                    else:
                                                        # 見つからないものは破棄
                                                        pass

                                                if len(unevaluated_events) == 0:
                                                    # 判定済みのものしかなかったので、結論イベントを追加する
                                                    IncidentDict[UsedFilterId] = judged_events + [ConclusionEventRow['_id']]
                                                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                                    # 結論イベントを抽出対象とするフィルターを含むルールのマッチ候補となるイベントも予約済みにする
                                                    for rule in (
                                                        rule
                                                        for rule in ruleList
                                                        if UsedFilterId
                                                        in (rule["FILTER_A"], rule["FILTER_B"])
                                                    ):
                                                        preserved_events.update(
                                                            IncidentDict.get(rule["FILTER_A"], ()),
                                                            IncidentDict.get(rule["FILTER_B"], ()),
                                                        )
                                                else:
                                                    # 破棄するイベントを予約済みから取り除く
                                                    preserved_events.difference_update(IncidentDict[UsedFilterId])
                                                    # 複数合致することになるので、未評価のもの（結論イベント含む）は破棄する→未知におとす予定
                                                    IncidentDict[UsedFilterId] = judged_events
                                            else:
                                                # キューイングの場合
                                                IncidentDict[UsedFilterId].append(ConclusionEventRow['_id'])
                                                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                                # 結論イベントを抽出対象とするフィルターを含むルールのマッチ候補となるイベントも予約済みにする
                                                for rule in (
                                                    rule
                                                    for rule in ruleList
                                                    if UsedFilterId
                                                    in (rule["FILTER_A"], rule["FILTER_B"])
                                                ):
                                                    preserved_events.update(
                                                        IncidentDict.get(rule["FILTER_A"], ()),
                                                        IncidentDict.get(rule["FILTER_B"], ()),
                                                    )
                                        else:
                                            # 空配列。既に未知判定（ユニーク検索かつ複数イベント合致）されているため、結論イベントも破棄する→未知におとす予定
                                            pass
                                    else:
                                        # 初めてフィルターにかかった
                                        IncidentDict[UsedFilterId] = [ConclusionEventRow['_id']]
                                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                        # 結論イベントを抽出対象とするフィルターを含むルールのマッチ候補となるイベントも予約済みにする
                                        for rule in (
                                            rule
                                            for rule in ruleList
                                            if UsedFilterId
                                            in (rule["FILTER_A"], rule["FILTER_B"])
                                        ):
                                            preserved_events.update(
                                                IncidentDict.get(rule["FILTER_A"], ()),
                                                IncidentDict.get(rule["FILTER_B"], ()),
                                            )

                            newIncident_Flg = True

                            # 評価結果の更新（完了）
                            data_list = {
                                "ACTION_LOG_ID": action_log_row["ACTION_LOG_ID"],
                                "STATUS_ID": oaseConst.OSTS_Completed  # "6"
                            }
                            WriterProcessManager.update_oase_action_log(data_list)
                    else:
                        # ルール判定 アンマッチ
                        if judged_result_has_subsequent_event:
                            # 判定結果が後続イベントを含む場合は、ループ継続のために結論イベントが生じたものとして扱う
                            newIncident_Flg = True

                # endregion レベル毎のルール判定のループ

                # 結論イベントの追加判定
                if newIncident_Flg is True:
                    newIncidentCount[TargetLevel] += 1
                    tmp_msg = g.appmsg.get_log_message("BKY-90023", [])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    tmp_msg = g.appmsg.get_log_message("BKY-90024", [TargetLevel])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                    if newIncidentCount[TargetLevel] > evaluate_latent_infinite_loop_limit:
                        # 未判定イベントが一定回数以上繰り返した場合は抜ける
                        # ※無限ループ（ルール⇒結論イベント⇒ルール）の発生を回避するための条件
                        # Reached maximum amount of loops.
                        tmp_msg = g.appmsg.get_log_message("BKY-90025", [])
                        g.applogger.warning(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                        # これ以上ループしない設定
                        newIncident_Flg = False
                        newIncidentCount[TargetLevel] = 0
                else:
                    tmp_msg = g.appmsg.get_log_message("BKY-90026", [])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # endregion レベル毎の結論イベント未発生確認のループ
            tmp_msg = g.appmsg.get_log_message("BKY-90017", [TargetLevel, 'Ended'])  # {} Rule verdict {}
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # endregion レベル毎のループ

        # 各レベルのルール判定で結論イベントが発生していないか確認
        total = 0
        for TargetLevel in JudgeLevelList:
            total += newIncidentCount[TargetLevel]
        # 発生していなかったらループを終了
        if total == 0:
            break

    # endregion 全レベルループ
    tmp_msg = g.appmsg.get_log_message("BKY-90016", ['Ended'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # 処理後タイムアウトイベント検出
    PostProcTimeoutEventIdList = EventObj.get_post_proc_timeout_event()
    if len(PostProcTimeoutEventIdList) > 0:
        tmp_msg = g.appmsg.get_log_message("BKY-90027", [str(PostProcTimeoutEventIdList)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        # 処理後タイムアウトの_exastro_timeoutを1に更新
        update_Flag_Dict = {"_exastro_timeout": '1'}
        EventObj.set_timeout(PostProcTimeoutEventIdList)
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
        EventObj.set_undetected(UnusedEventIdList)
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
        NotificationProcessManager.send_notification(unused_notification_list, {"notification_type": OASENotificationType.UNDETECTED})


def on_start_process(*args, **kwargs):
    NotificationProcessManager.start_process()
    WriterProcessManager.start_process()


def on_exit_process(*args, **kwargs):
    NotificationProcessManager.stop_process()
    WriterProcessManager.stop_process()
