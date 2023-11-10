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


from flask import g
import time
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.common.util import ky_decrypt, get_timestamp, get_all_execution_limit, get_org_execution_limit
from common_libs.conductor.classes.exec_util import *
from common_libs.ci.util import log_err
from common_libs.oase.manage_events import ManageEvents
import datetime
import inspect
import json

# from libs import common_functions as cm


def backyard_main(organization_id, workspace_id):
    """
    [ita_by_ansible_execute]
    main logicのラッパー
    called 実行君
    """
    g.applogger.debug(g.appmsg.get_log_message("BKY-00001"))

    _rule_matching(organization_id, workspace_id)

    retBool = main_logic(organization_id, workspace_id)
    if retBool is True:
        # 正常終了
        g.applogger.debug(g.appmsg.get_log_message("BKY-00002"))
    else:
        g.applogger.debug(g.appmsg.get_log_message("BKY-00003"))


def main_logic(organization_id, workspace_id):
    """
    main logic
    """
    g.applogger.debug("organization_id=" + organization_id)
    g.applogger.debug("workspace_id=" + workspace_id)
    g.applogger.debug("WSMONGO_PASSWORD=" + ky_decrypt(g.db_connect_info["WSMONGO_PASSWORD"]))

    wsMong = MONGOConnectWs()
    g.applogger.debug("mongodb-ws can connet")

    test_collection = wsMong.collection("test_collection")
    # test_collection.insert_many([
    #     {'名前': '太郎', '住所': '東京'},
    #     {'名前': '次郎', '住所': '千葉'}
    # ])
    data_list = test_collection.find()
    for data in data_list:
        g.applogger.debug(data)

    return True


def _rule_matching(organization_id, workspace_id):
    """
        ルールマッチング機能backyardメイン処理
        ARGS:
            organization_id: Organization ID
            workspace_id: Workspace ID
        RETURN:
    """
    # DB接続
    tmp_msg = 'db connect'
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # メイン処理開始
    debug_msg = g.appmsg.get_log_message("BKY-20001", [])
    g.applogger.debug(debug_msg)

    strage_path = os.environ.get('STORAGEPATH')
    workspace_path = strage_path + "/".join([organization_id, workspace_id])

    # connect MongoDB
    mongodbca = MONGOConnectWs()
    # connect MariaDB
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # UnImplementLog("処理時間固定")
    # 単体テスト用
    # judgeTime = int(time.time())
    judgeTime = 10000

    objdbca.db_transaction_start()
    # ①ルールマッチ
    ret = JudgeMain(objdbca, mongodbca, judgeTime)
    if ret is False:
        g.applogger.debug("JudgeMain False")

    # ②アクション実行後通知と結論イベント登録
    # obj = ActionStatusMonitor(objdbca, mongodbca)
    # obj.Monitor()

    objdbca.db_transaction_end(True)

    # メイン処理終了
    debug_msg = g.appmsg.get_log_message("BKY-20002", [])
    g.applogger.debug(debug_msg)
    return


def addline_msg(msg=''):
    info = inspect.getouterframes(inspect.currentframe())[1]
    msg_line = "{} ({}:{})".format(msg, os.path.basename(info.filename), info.lineno)
    return msg_line


class Judgement:
    def __init__(self, MariaDBCA, MongoDBCA, EventObj):
        self.MariaDBCA = MariaDBCA
        self.MongoDBCA = MongoDBCA

        # ラベルマスタ取得
        self.getLabelGroup()

        self.EventObj = EventObj

    def filterJudge(self, FilterRow, objdbca):
        DebugMode = False
        EventJudgList = []
        # テーブル名
        t_oase_label_key_input = 'T_OASE_LABEL_KEY_INPUT'  # ラベルマスタ

        # 「ラベルマスタ」からレコードを取得
        labelList = objdbca.table_select(t_oase_label_key_input, 'WHERE DISUSE_FLAG = %s', [0])
        if not labelList:
            tmp_msg = "処理対象レコードなし。Table:T_OASE_LABEL_KEY_INPUT"
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False
        tmp_msg = "ラベルマスタ 件数: {}".format(str(len(labelList)))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        filter_condition_json = json.loads(FilterRow.get('FILTER_CONDITION_JSON'))

        for LabelRow in filter_condition_json:
            # ラベル毎のループ
            LabelKey = str(LabelRow['label_name'])
            LabelValue = str(LabelRow['condition_value'])
            LabelCondition = str(LabelRow['condition_type'])
            tmp_msg = "{} <<LabelKey: {}>> <<LabelValue: {}>> <<LabelCondition: {}>>".format(DebugMode, LabelKey, LabelValue, LabelCondition)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # ルールキーからルールラベル名を取得
            LabelName = self.getIDtoName(LabelKey)
            tmp_msg = "{} <<LabelName: {}>>".format(DebugMode, LabelName)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # ラベリングされたイベントからデータを抜出す条件設定
            EventJudgList.append(self.makeEventJudgList(LabelName, LabelValue, LabelCondition))

        ret, UseEventIdList = self.EventJudge(EventJudgList)
        if ret is False:
            return False, UseEventIdList

        return True, UseEventIdList[0]

    def getLabelGroup(self):
        self.LabelMasterDict = {}
        sql = "SELECT * FROM V_OASE_LABEL_KEY_GROUP WHERE DISUSE_FLAG = '0'"
        Rows = self.MariaDBCA.sql_execute(sql, [])
        for Row in Rows:
            self.LabelMasterDict[str(Row['LABEL_KEY_ID'])] = Row['LABEL_KEY']

    def getIDtoName(self, uuid):
        uuid = str(uuid)
        if uuid not in self.LabelMasterDict:
            return False
        return self.LabelMasterDict[uuid]

    def EventJudge(self, EventJudgList):
        DebugMode = False
        # イベント 検索
        tmp_msg = "{} イベント検索 JSON: {}".format(DebugMode, str(EventJudgList))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        ret, UsedEventIdList = self.EventObj.find_events(EventJudgList)
        if len(UsedEventIdList) == 0:
            # 対象イベントなし
            tmp_msg = "{} イベント なし EventIdList: {}".format(DebugMode, str(UsedEventIdList))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, ""
        elif len(UsedEventIdList) == 1:
            # 対象イベントあり
            tmp_msg = "{} イベント あり EventIdList: {}".format(DebugMode, str(UsedEventIdList))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return True, UsedEventIdList
        else:
            # 対象イベント 複数あり
            tmp_msg = "対象イベント 複数あり EventIdList: {}".format(str(UsedEventIdList))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, UsedEventIdList

    def makeEventJudgList(self, LabelName, LabelValue, LabelCondition):
        return {"LabelKey": LabelName, "LabelValue": LabelValue, "LabelCondition": LabelCondition}

    def SummaryofFiltersUsedinRules(self, RuleList):
        # ルールで使用しているフィルタを集計
        # FiltersUsedinRulesDictの構造
        # FiltersUsedinRulesDict[フィルタID] = { 'rule_id': RULE_ID, 'rule_priority': RULE_PRIORITY, 'count': フィルタ使用数 }
        FiltersUsedinRulesDict = {}
        for RuleRow in RuleList:
            # for FilterId in RuleRow['FILTER_COMBINATION_JSON']['filter_key']:
            filter_combination_json = json.loads(RuleRow.get('FILTER_COMBINATION_JSON'))
            for FilterRow in filter_combination_json:
                for FilterId in FilterRow['filter_key']:
                    if FilterId in FiltersUsedinRulesDict:
                        FiltersUsedinRulesDict[FilterId]['count'] += 1
                    else:
                        FiltersUsedinRulesDict[FilterId] = {}
                        FiltersUsedinRulesDict[FilterId]['rule_id'] = RuleRow['RULE_ID']
                        FiltersUsedinRulesDict[FilterId]['rule_priority'] = RuleRow['RULE_PRIORITY']
                        FiltersUsedinRulesDict[FilterId]['count'] = 1

        return FiltersUsedinRulesDict

    def TargetRuleExtraction(self, TargetLevel, RuleList, FiltersUsedinRulesDict, IncidentDict):
        DebugMode = True
        TargetRuleList = []
        defObj = RuleJudgementConst()
        for RuleRow in RuleList:
            hit = True
            filter_combination_json = json.loads(RuleRow.get('FILTER_COMBINATION_JSON'))
            for FilterRow in filter_combination_json:
                for FilterId in FilterRow['filter_key']:
                    if FilterId not in FiltersUsedinRulesDict:
                        tmp_msg = "対象フィルタ未登録  RULE_ID {} FILTER_ID {}>>".format(RuleRow['RULE_ID'], FilterId)
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                        hit = False
                        continue
                    # ルール抽出対象: 複数のルールで使用していないフィルタを使用しているルール※1の場合
                    if TargetLevel == "Level1":
                        if FiltersUsedinRulesDict[FilterId]['count'] != 1:
                            hit = False

                    # ルール抽出対象: 複数のルールで使用しているフィルタで優先順位が最上位のルール※2の場合
                    elif TargetLevel == "Level2":
                        # で優先順位が最上位のルールか判定
                        if FiltersUsedinRulesDict[FilterId]['rule_id'] != RuleRow['RULE_ID']:
                            hit = False

                    # ルール抽出対象: 複数のルールで使用しているフィルタでタイムアウトを迎えるフィルタを使用しているルール※3の場合
                    elif TargetLevel == "Level3":
                        if FilterId not in IncidentDict:
                            tmp_msg = "{} 対象イベント なし  RULE_ID {} FILTER_ID {}>>".format(DebugMode, RuleRow['RULE_ID'], FilterId)
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            hit = False
                        else:
                            if (isinstance(IncidentDict[FilterId], list)):
                                tmp_msg = "{} 対象イベント 複数あり  RULE_ID:{} FILTER_ID:{} EventId:{}".format(DebugMode, RuleRow['RULE_ID'], FilterId, IncidentDict[FilterId])
                                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                hit = False
                            else:
                                pass
                                ret, EventRow = self.EventObj.get_events(IncidentDict[FilterId])
                                if ret is False:
                                    tmp_msg = "対象イベント取得失敗  RULE_ID:{} FILTER_ID:{} EventId:{}".format(RuleRow['RULE_ID'], FilterId, IncidentDict[FilterId])
                                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                    hit = False
                                else:
                                    if EventRow[defObj.DF_LOCAL_LABLE_NAME][defObj.DF_LOCAL_LABLE_STATUS] != defObj.DF_POST_PROC_TIMEOUT_EVENT:
                                        hit = False
                                    else:
                                        hit = True
                                        break

            if TargetLevel == "Level2":
                if hit is True:
                    hit = False
                    # フィルタを利用しているルールが複数ある事を確認
                    for FilterRow in filter_combination_json:
                        for FilterId in FilterRow['filter_key']:
                            if FiltersUsedinRulesDict[FilterId]['count'] != 1:
                                hit = True
                                break
            if hit is True:
                TargetRuleList.append(RuleRow)

        return TargetRuleList

    def RuleJudge(self, RuleRow, IncidentDict):
        UseEventIdList = []

        tmp_msg = "=========================================================================================================================="
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = "ルール判定開始 RULE_ID:{} RULE_NAME:{}  JSON:{}".format(RuleRow['RULE_ID'], RuleRow['RULE_NAME'], str(RuleRow["FILTER_COMBINATION_JSON"]))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        # ルール内のフィルタ条件判定用辞書初期化
        FilterResultDict = {}
        FilterResultDict['True'] = 0
        FilterResultDict['False'] = 0
        FilterResultDict['Count'] = 0
        FilterResultDict['EventList'] = []
        FilterResultDict['Operator'] = ''

        filter_combination_json = json.loads(RuleRow.get('FILTER_COMBINATION_JSON'))
        for FilterRow in filter_combination_json:
            if not FilterRow['filter_operator']:
                FilterRow['filter_operator'] = ''

            FilterResultDict['Operator'] = str(FilterRow['filter_operator'])

            # 論理演算子「operator」設定確認
            if self.checkRuleOperatorId(FilterResultDict['Operator']) is False:
                tmp_msg = "ルール管理　論理演算子「operator」が不正 RULE_ID:{} RULE_NAME:{} JSON:{}".format(RuleRow['RULE_ID'], RuleRow['RULE_NAME'], str(RuleRow["FILTER_COMBINATION_JSON"]))
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # フィルタ毎のループ
            for FilterId in FilterRow['filter_key']:
                tmp_msg = "フィルタ管理判定開始  FILTER_ID: {}".format(FilterId)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                ret, EventRow = self.MemoryBaseFilterJudge(FilterId, IncidentDict)

                if ret is True:
                    FilterResultDict['EventList'].append(EventRow)

                # フィルタ件数 Up
                FilterResultDict['Count'] += 1

                # フィルタ判定結果退避
                FilterResultDict[str(ret)] += 1

                # フィルタ判定に使用したイベントID退避
                if ret is True:
                    tmp_msg = "フィルタ判定結果　マッチ  FILTER_ID: {}".format(FilterId)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                else:
                    tmp_msg = "フィルタ判定結果　アンマッチ  FILTER_ID: {}".format(FilterId)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            tmp_msg = "ルール内　フィルタ判定結果: {}".format(str(ret))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        ret = self.checkFilterCondition(FilterResultDict)
        if ret is True:
            tmp_msg = "ルール判定結果: マッチ RULE_ID:{} RULE_NAME:{} JSON:{}".format(RuleRow['RULE_ID'], RuleRow['RULE_NAME'], str(RuleRow["FILTER_COMBINATION_JSON"]))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        else:
            tmp_msg = "ルール判定結果: アンマッチ RULE_ID:{} RULE_NAME:{} JSON:{}".format(RuleRow['RULE_ID'], RuleRow['RULE_NAME'], str(RuleRow["FILTER_COMBINATION_JSON"]))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        if ret is False:
            return False, UseEventIdList

        for EventRow in FilterResultDict['EventList']:
            UseEventIdList.append(EventRow['_id'])

        return True, UseEventIdList

    def MemoryBaseFilterJudge(self, FilterId, IncidentDict):
        DebugMode = False
        if FilterId not in IncidentDict:
            tmp_msg = "{} イベント なし FILTER ID:{}>>".format(DebugMode, FilterId)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, {}

        if type(IncidentDict[FilterId]) is list:
            tmp_msg = "複数イベントあり FILTER ID:{}>>".format(FilterId)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, {}

        ret, EventRow = self.EventObj.get_events(IncidentDict[FilterId])
        if ret is False:
            tmp_msg = "イベント なし FILTER ID:{}>>".format(FilterId)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, {}

        if str(EventRow['labels']['_exastro_evaluated']) == '0':
            return True, EventRow
        else:
            tmp_msg = "イベント 使用済み FILTER ID:{}>>".format(FilterId)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, {}

    def checkFilterCondition(self, FilterResultDict):
        DebugMode = False

        defObj = RuleJudgementConst()

        if FilterResultDict['Operator'] == defObj.DF_OPE_OR:
            if FilterResultDict['True'] != 0:
                return True
        elif FilterResultDict['Operator'] == defObj.DF_OPE_AND:
            if FilterResultDict['False'] == 0:
                return True
        elif FilterResultDict['Operator'] == defObj.DF_OPE_ORDER:
            if FilterResultDict['False'] != 0:
                return False
            f_time = None
            if len(FilterResultDict['EventList']) > 1:
                for EventRow in FilterResultDict['EventList']:
                    if not f_time:
                        f_time = EventRow['labels']['_exastro_fetched_time']
                    else:
                        # イベント発生順の確認
                        tmp_msg = "{} timr[0] {} time[1] {}".format(DebugMode, f_time, EventRow['labels']['_exastro_fetched_time'])
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                        # 発生順　A => B
                        if EventRow['labels']['_exastro_fetched_time'] > f_time:
                            return False
            return True
        else:
            if FilterResultDict['True'] != 0:
                return True
        return False

    def checkRuleOperatorId(self, Operator):
        defObj = RuleJudgementConst()
        if not Operator:
            return True
        if Operator in (defObj.DF_OPE_OR, defObj.DF_OPE_AND, defObj.DF_OPE_ORDER):
            return True
        return False

    def putRaccEvent(self, RuleRow, UseEventIdList):
        conclusion_ids = {}
        addlabels = {}
        RuleRow["LABELING_INFORMATION_JSON"] = json.loads(RuleRow["LABELING_INFORMATION_JSON"])
        for key, value in RuleRow["LABELING_INFORMATION_JSON"].items():
            name = self.getIDtoName(key)
            if name is False:
                tmp_msg = "ラベル結論マスタ 未登録 LABEL_KEY_ID:{}>>".format(key)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                return False, {}
            addlabels[name] = value
            conclusion_ids[name] = key

        RaccEventDict = {}

        # 単体テスト用
        # 本来はinsert時の戻り値(uuid)を設定
        id = 'e_' + RuleRow["RULE_ID"]
        t1 = int(time.time())
        ttl = int(RuleRow['REEVALUATE_TTL'])

        RaccEventDict["_id"] = id
        RaccEventDict["labels"] = {}
        RaccEventDict["labels"]["_exastro_event_collection_settings_id"] = ''
        RaccEventDict["labels"]["_exastro_fetched_time"] = t1
        RaccEventDict["labels"]["_exastro_end_time"] = t1 + ttl
        RaccEventDict["labels"]["_exastro_evaluated"] = "0"
        RaccEventDict["labels"]["_exastro_undetected"] = "0"
        RaccEventDict["labels"]["_exastro_timeout"] = "0"
        RaccEventDict["labels"]["_exastro_type"] = "conclusion"
        RaccEventDict["labels"]["_exastro_rule_name"] = RuleRow['RULE_LABEL_NAME']
        for name, value in addlabels.items():
            RaccEventDict["labels"][name] = value
        RaccEventDict["exatsro_rule"] = {}
        RaccEventDict["exatsro_rule"]['id'] = RuleRow['RULE_ID']
        RaccEventDict["exatsro_rule"]['name'] = RuleRow['RULE_NAME']
        RaccEventDict["exastro_events"] = UseEventIdList
        RaccEventDict["exastro_label_key_inputs"] = {}
        RaccEventDict["exastro_label_key_inputs"] = conclusion_ids

        # MongoDBに結論イベント登録
        _id = self.EventObj.insert_event(RaccEventDict)

        tmp_msg = "MongoDBに結論イベント登録 (_id: {})".format(_id)
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return True, RaccEventDict

    def ConclusionLabelUsedInFilter(self, FilterCheckLabelDict, FilterList):
        DebugMode = False
        UsedFilterIdList = []
        # FilterCheckLabelDict = {'i_11': 'down', 'i_100': 'ap11'}
        for FilterRow in FilterList:
            FilterId = FilterRow["FILTER_ID"]
            ret = self.ConclusionFilterJudge(FilterCheckLabelDict, FilterRow)
            if ret is True:
                tmp_msg = "{} フィルター　マッチ FilterId: {}".format(DebugMode, FilterId)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                UsedFilterIdList.append(FilterId)
            else:
                tmp_msg = "{} フィルター　アンマッチ FilterId: {}".format(DebugMode, FilterId)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # マッチしたフィルタの数を判定
        if len(UsedFilterIdList) > 0:
            return True, UsedFilterIdList
        return False, UsedFilterIdList

    def ConclusionFilterJudge(self, FilterCheckLabelDict, FilterRow):
        DebugMode = False

        defObj = RuleJudgementConst()

        tmp_msg = "{} 結論イベント 判定 JSON: {}".format(DebugMode, str(FilterCheckLabelDict))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        FilterRow['FILTER_CONDITION_JSON'] = [{'key': 'c_01_name', 'condition': '0', 'value': 'c_01'}, {'key': 'c_02_name', 'condition': '0', 'value': 'c_02'}]

        LabelHitCount = 0
        for FilterLabels in FilterRow['FILTER_CONDITION_JSON']:
            FilterName = FilterLabels['key']
            FilterValue = FilterLabels['value']
            FilterCondition = str(FilterLabels['condition'])
            tmp_msg = "{} Filter FilterName:{} FilterValues:{} FilterCondition:{}".format(DebugMode, FilterName, FilterValue, FilterCondition)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            LabelHit = False
            for LabelName, LabelValue in FilterCheckLabelDict.items():
                tmp_msg = "{} check LabelName:{} LabelValue:{}".format(DebugMode, LabelName, LabelValue)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                if (FilterName == LabelName and FilterValue == LabelValue and FilterCondition == defObj.DF_TEST_EQ) or\
                        (FilterName == LabelName and FilterValue != LabelValue and FilterCondition == defObj.DF_TEST_NE):
                    LabelHit = True
                    LabelHitCount += 1
                    tmp_msg = "{} hit LabelName:{} LabelValue:{}".format(DebugMode, LabelName, LabelValue)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    break
            if LabelHit is True:
                tmp_msg = "{} Label マッチ".format(DebugMode)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                pass
            else:
                tmp_msg = "{} Label アンマッチ".format(DebugMode)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                break
        tmp_msg = "{} <<LabelHitCount: {}>>".format(DebugMode, str(LabelHitCount))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = "{} <<FilterCheckLabelDict: {}>>".format(DebugMode, str(len(FilterCheckLabelDict)))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        if LabelHitCount != len(FilterRow['FILTER_CONDITION_JSON']):
            tmp_msg = "{} Filter アンマッチ1".format(DebugMode)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False
        # 結論ラベル数＞フィルタラベル数の場合
        if LabelHitCount != len(FilterCheckLabelDict):
            tmp_msg = "{} Filter アンマッチ2".format(DebugMode)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False
        return True


def JudgeMain(objdbca, MongoDBCA, judgeTime):
    IncidentDict = {}

    defObj = RuleJudgementConst()

    # イベントデータ取得
    EventObj = ManageEvents(MongoDBCA, judgeTime)

    count = EventObj.count_events()
    if count == 0:
        tmp_msg = "処理対象イベントなし"
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False

    tmp_msg = "イベント取得 対象時間:{} 取得件数: {}".format(judgeTime, count)
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    timeout_Event_Id_List = EventObj.get_timeout_event()
    tmp_msg = "有効期限判定　タイムアウト件数: {}".format(len(timeout_Event_Id_List))
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # タイムアウトイベント有無判定
    if len(timeout_Event_Id_List) > 0:
        # タイムアウトしているイベントの_exastro_timeoutを1に更新
        update_Flag_Dict = {"_exastro_timeout": '1'}
        EventObj.update_label_flag(timeout_Event_Id_List, update_Flag_Dict)
        tmp_msg = "イベント更新  タイムアウト({}) ids: {}".format(str(update_Flag_Dict), str(timeout_Event_Id_List))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # PFから通知先一覧取得（既知(時間切れ)がTrue）

    # PFから通知先一覧取得（新規がTrue）

    # テーブル名
    t_oase_filter = 'T_OASE_FILTER'  # フィルター管理
    # 「フィルター管理」からレコードを取得
    filterList = objdbca.table_select(t_oase_filter, 'WHERE DISUSE_FLAG = %s AND AVAILABLE_FLAG = %s', [0, 1])
    if not filterList:
        tmp_msg = "処理対象レコードなし。Table:T_OASE_FILTER"
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False

    tmp_msg = "フィルター管理取得 件数: {}".format(str(len(filterList)))
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # テーブル名
    t_oase_rule = 'T_OASE_RULE'  # ルール管理
    # 「ルール管理」からレコードを取得
    ruleList = objdbca.table_select(t_oase_rule, 'WHERE DISUSE_FLAG = %s AND AVAILABLE_FLAG = %s ORDER BY RULE_PRIORITY', [0, 1])
    if not ruleList:
        tmp_msg = "処理対象レコードなし。Table:T_OASE_RULE"
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False

    tmp_msg = "ルール管理取得 件数: {}".format(str(len(ruleList)))
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # ルール判定　クラス生成
    judgeObj = Judgement(objdbca, MongoDBCA, EventObj)

    tmp_msg = "フィルタリング開始"
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    # フィルタリング開始
    newIncident = False
    for filterRow in filterList:
        filterId = filterRow["FILTER_ID"]
        ret, JudgeEventId = judgeObj.filterJudge(filterRow, objdbca)
        if ret is True:
            tmp_msg = "フィルタリング判定結果　マッチ  FILTER_ID: {} EVENT_ID: <<{}>>".format(filterId, JudgeEventId)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            IncidentDict[filterId] = JudgeEventId
            newIncident = True
        else:
            # 複数のイベントがマッチしている場合
            if len(JudgeEventId) > 0:
                IncidentDict[filterId] = JudgeEventId
            tmp_msg = "フィルタリング判定結果　アンマッチ  FILTER_ID: {} EVENT_ID: <<{}>>".format(filterId, str(JudgeEventId))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    tmp_msg = "フィルタリング終了"
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # ルールで使用しているフィルタを集計
    FiltersUsedinRulesDict = judgeObj.SummaryofFiltersUsedinRules(ruleList)

    tmp_msg = "ルールマッチ開始"
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

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

            newIncident = True
            tmp_msg = "{} ルール判定開始".format(TargetLevel)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # レベル毎の結論イベント未発生確認のループ -----
            while newIncident is True:
                newIncident = False
                # レベル毎のルール判定のループ -----
                for ruleRow in TargetRuleList:

                    # ルール判定
                    ret, UseEventIdList = judgeObj.RuleJudge(ruleRow, IncidentDict)

                    if ret is True:
                        # ルール判定 マッチ
                        # 評価結果へ登録
                        if getattr(g, 'USER_ID', None) is None:
                            g.USER_ID = '110101'
                        # objdbca = DBConnectWs()
                        # objdbca.db_transaction_start()
                        Row = {
                            "RULE_ID": "RULE_ID",
                            "RULE_NAME": "RULE_NAME",
                            # 1:ルールマッチング済み
                            "STATUS_ID": "1",
                            # "ACTION_ID": "ACTION_ID",
                            "ACTION_ID": None,
                            "ACTION_NAME": "ACTION_NAME",
                            "CONDUCTOR_INSTANCE_ID": "CONDUCTOR_INSTANCE_ID",
                            "CONDUCTOR_INSTANCE_NAME": "CONDUCTOR_INSTANCE_NAME",
                            "OPERATION_ID": "OPERATION_ID",
                            "OPERATION_NAME": "OPERATION_NAME",
                            "EVENT_ID_LIST": json.dumps("['event_id_01', 'event_id_02']"),
                            # Row["EXECUTION_USER"] = UserIDtoUserName(objdbca, g.USER_ID)
                            "TIME_REGISTER": datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                            "NOTE": None,
                            "DISUSE_FLAG": "0"
                        }
                        RegistrActionLog(objdbca, Row)
                        # objdbca.db_transaction_end(True)

                        # 使用済みインシデントフラグを立てる  _exastro_evaluated='1'
                        update_Flag_Dict = {"_exastro_evaluated": '1'}
                        # MongoDBのインシデント情報を更新
                        EventObj.update_label_flag(UseEventIdList, update_Flag_Dict)
                        tmp_msg = "使用済みインシデントフラグを立てる ({}) ids: {}".format(str(update_Flag_Dict), str(UseEventIdList))
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                        # 評価結果からルールマッチング済みのレコードを取得
                        # テーブル名
                        t_oase_action_log = 'T_OASE_ACTION_LOG'  # 評価結果
                        # 「評価結果」からレコードを取得
                        ret_action_log = objdbca.table_select(t_oase_action_log, 'WHERE DISUSE_FLAG = %s AND STATUS_ID = %s', [0, 1])
                        if not ret_action_log:
                            tmp_msg = "処理対象レコードなし。Table:T_OASE_ACTION_LOG"
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            return False

                        # ルールにアクションが設定してあるか判定する
                        for action_log_row in ret_action_log:
                            if action_log_row["ACTION_ID"]:
                                # アクションが設定されている場合
                                # 通知処理
                                # 評価結果の更新（実行中）
                                data_list = {
                                    "ACTION_LOG_ID": action_log_row["ACTION_LOG_ID"],
                                    "STATUS_ID": "2"
                                }
                                objdbca.table_update(t_oase_action_log, data_list, 'ACTION_LOG_ID')

                                # conductor実行
                                conductor_class_id = '80565c65-fe58-4a5c-abb5-34db406f8b51'
                                operation_id = 'd7572d97-07c4-4e37-bb36-8ec4606eec82'
                                retBool, result = conductor_execute(objdbca, conductor_class_id, operation_id)
                                if retBool is False:
                                    tmp_msg = "error [{}]".format(result)
                                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                    objdbca.db_rollback()
                                else:
                                    conductor_instance_id = result['conductor_instance_id']
                                    tmp_msg = "conductor_instance_id [{}]".format(conductor_instance_id)
                                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                    objdbca.db_commit()
                            else:
                                # アクションが設定されていない場合
                                # 結論イベント登録
                                ret, ConclusionEventRow = judgeObj.putRaccEvent(ruleRow, UseEventIdList)

                                # 結論イベントに処理で必要なラベル情報を追加
                                ConclusionEventRow = EventObj.add_local_label(ConclusionEventRow, defObj.DF_LOCAL_LABLE_NAME, defObj.DF_LOCAL_LABLE_STATUS, defObj.DF_PROC_EVENT)

                                FilterCheckLabelDict = ruleRow["LABELING_INFORMATION_JSON"]

                                # 結論イベントに対応するフィルタ確認
                                ret, UsedFilterIdList = judgeObj.ConclusionLabelUsedInFilter(FilterCheckLabelDict, filterList)

                                tmp_msg = "結論イベントに対応するフィルタ確認 {}".format(str(ret))
                                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                                if ret is True:
                                    for UsedFilterId in UsedFilterIdList:
                                        tmp_msg = "結論イベントに対応するフィルタとイベント紐づけ登録  FILTER_ID: {} EVENT_ID: {}".format(UsedFilterId, ConclusionEventRow['_id'])
                                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                        IncidentDict[UsedFilterId] = ConclusionEventRow['_id']

                                        tmp_msg = "結論イベントをメモリに追加 {}".format(ConclusionEventRow)
                                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                        EventObj.append_event(ConclusionEventRow)
                                        newIncident = True
                                # 評価結果の更新（完了）
                                data_list = {
                                    "ACTION_LOG_ID": action_log_row["ACTION_LOG_ID"],
                                    "STATUS_ID": "6"
                                }
                                objdbca.table_update(t_oase_action_log, data_list, 'ACTION_LOG_ID')

                    else:
                        # ルール判定 アンマッチ
                        pass
                    tmp_msg = "ルール判定確認"
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                # ----- レベル毎のルール判定のループ
                # 結論イベントの追加判定
                if newIncident is True:
                    newIncidentCount[TargetLevel] += 1
                    tmp_msg = "結論イベント 追加あり"
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    tmp_msg = "{} 再ルール判定終了".format(TargetLevel)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                else:
                    tmp_msg = "結論イベント 追加なし"
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # ----- レベル毎の結論イベント未発生確認のループ
            tmp_msg = "{} ルール判定終了".format(TargetLevel)
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
    tmp_msg = "ルールマッチ終了"
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # 未知事象フラグを立てる（一括で行う）
    UnusedEventIdList = EventObj.get_unused_event(IncidentDict)
    if len(UnusedEventIdList) > 0:
        tmp_msg = "未知イベント検出 EventId: {}>>".format(str(UnusedEventIdList))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        # MongoDBのインシデント情報を更新（一括で行う）
        # 未知イベントの_exastro_undetectedを1に更新
        update_Flag_Dict = {"_exastro_undetected": '1'}
        EventObj.update_label_flag(UnusedEventIdList, update_Flag_Dict)
        tmp_msg = "イベント更新  未知イベント ({}) ids:{}".format(str(update_Flag_Dict), str(UnusedEventIdList))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    else:
        tmp_msg = "未知イベントなし"
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # PFから通知先一覧取得（未知がTrue）
    # 最後の通知先ではない or 通知先が0件ではない
    # TrueでPFへ通知メッセージ送付（未知）


def UserIDtoUserName(objdbca, UserId):
    UserName = ""
    UserEnv = g.LANGUAGE.upper()
    UserNameCol = "USER_NAME_{}".format(UserEnv)
    TableName = "T_COMN_BACKYARD_USER"
    WhereStr = "WHERE USER_ID = '%s' AND DISUSE_FLAG='0'" % (UserId)

    Rows = objdbca.table_select(TableName, WhereStr, [])
    for Row in Rows:
        UserName = Row[UserNameCol]
    return UserName


def RegistrActionLog(objdbca, Row):
    """
    評価結果に登録する
    ARGS:
        objdbca:DB接続クラス  DBConnectWs()
        Row:登録するパラメータ
    RETURN:
    """
    is_RegisterHistory = True
    TableName = 'T_OASE_ACTION_LOG'
    PrimaryKey = 'ACTION_LOG_ID'
    ret = objdbca.table_insert(TableName, Row, PrimaryKey, is_RegisterHistory)
    if ret is False:
        print("False")


def conductor_execute(objdbca, conductor_class_id, operation_id):
    """
    conductorを実行する（関数を呼ぶ）
    ARGS:
        objdbca:DB接続クラス  DBConnectWs()
        conductor_class_id:
        operation_id:
    RETURN:
    """
    objcbkl = ConductorExecuteBkyLibs(objdbca)  # noqa: F405
    # parameter = {"conductor_class_name": "test", "operation_name": "ope"}
    parameter = {"conductor_class_id": conductor_class_id, "operation_id": operation_id}
    _res = objcbkl.conductor_execute_no_transaction(parameter)
    return _res


class RuleJudgementConst():
    # イベントデータに一時的に追加する項目定期
    # 親ラベル
    DF_LOCAL_LABLE_NAME = "__local_labels__"
    # 子ラベル イベント状態
    DF_LOCAL_LABLE_STATUS = "status"
    # イDF_LOCAL_LABLE_STATUSの状態
    DF_PROC_EVENT = '0'             # 処理対象:〇
    DF_POST_PROC_TIMEOUT_EVENT = '1'    # 処理対象　処理後タイムアウト:●
    DF_TIMEOUT_EVENT = '2'           # タイムアウト
    DF_NOT_PROC_EVENT = '3'       # 対象外

    # ルール・フィルタ管理　JSON内の演算子・条件
    # 条件
    DF_TEST_EQ = '0'    # =
    DF_TEST_NE = '1'    # !=
    # 演算子
    DF_OPE_NONE = ''    # None
    DF_OPE_OR = '1'     # OR
    DF_OPE_AND = '2'    # AND
    DF_OPE_ORDER = '3'  # ->


class ActionStatusMonitor():
    def __init__(self, MariaDBCA, MongoEvts):
        self.MariaDBCA = MariaDBCA
        self.MongoEvts = MongoEvts
        # ラベルマスタ取得
        self.getLabelGroup()
        # OASE 評価履歴　ステータス値
        self.OSTS_Rule_Match = "1"               # ルールマッチング済み
        self.OSTS_Executing = "2"                # 実行中
        self.OSTS_Wait_Approval = "3"            # 承認待ち
        self.OSTS_Approved = "4"                 # 承認済み
        self.OSTS_Rejected = "5"                 # 承認却下済み
        self.OSTS_Completed = "6"                # 完了
        self.OSTS_Completed_Abend = "7"          # 完了（異常）
        self.OSTS_Wait_For_Comp_Conf = "8"       # 完了確認待ち
        self.OSTS_Completion_Conf = "9"          # 完了確認済み
        self.OSTS_Completion_Conf_Reject = "10"  # 完了確認却下済み

        # Conductor ステータス値
        self.CSTS_Unexecuted = "1"               # 未実行
        self.CSTS_Unexecuted_Schedule = "2"      # 未実行(予約)
        self.CSTS_Executing = "3"                # 実行中
        self.CSTS_Executing_Delay = "4"          # 実行中(遅延)
        self.CSTS_Pause = "5"                    # 一時停止
        self.CSTS_Completed = "6"                # 正常終了
        self.CSTS_Abend = "7"                    # 異常終了
        self.CSTS_Warning_end = "8"              # 警告終了
        self.CSTS_Emergency_stop = "9"           # 緊急停止
        self.CSTS_Schedule_Cancel = "10"         # 予約取消
        self.CSTS_Unexpected_Error = "11"        # 想定外エラー

    def getLabelGroup(self):
        self.LabelMasterDict = {}
        sql = "SELECT * FROM V_EVRL_LABEL_KEY_GROUP WHERE DISUSE_FLAG = '0'"
        Rows = self.MariaDBCA.sql_execute(sql, [])
        for Row in Rows:
            self.LabelMasterDict[str(Row['LABEL_KEY_ID'])] = Row['LABEL_KEY']

    def getIDtoName(self, uuid):
        uuid = str(uuid)
        if uuid not in self.LabelMasterDict:
            return False
        return self.LabelMasterDict[uuid]

    def Monitor(self):
        sql = """
            SELECT
                TAB_A.*,
                TAB_B.CONDUCTOR_INSTANCE_ID       AS JOIN_CONDUCTOR_INSTANCE_ID,
                TAB_B.STATUS_ID                   AS CONDUCTOR_STATUS_ID,
                TAB_B.DISUSE_FLAG                 AS TAB_B_DISUSE_FLAG,
                TAB_C.RULE_ID                     AS JOIN_RULE_ID,
                TAB_C.RULE_NAME                   AS RULE_NAME,
                TAB_C.LABELING_INFORMATION_JSON   AS LABELING_INFORMATION_JSON,
                TAB_C.RULE_LABEL_NAME             AS RULE_LABEL_NAME,
                TAB_C.EVENT_ID_JSON               AS EVENT_ID_JSON,
                TAB_C.REEVALUATE_TTL              AS REEVALUATE_TTL,
                TAB_C.DISUSE_FLAG                 AS TAB_C_DISUSE_FLAG
            FROM
                T_EVRL_ACTION_LOG                   TAB_A
                LEFT JOIN T_COMN_CONDUCTOR_INSTANCE TAB_B ON (TAB_A.CONDUCTOR_INSTANCE_ID = TAB_B.CONDUCTOR_INSTANCE_ID)
                LEFT JOIN T_EVRL_RULE               TAB_C ON (TAB_A.RULE_ID               = TAB_C.RULE_ID )
            WHERE
                TAB_A.STATUS_ID in ("{}", "{}") AND
                TAB_A.DISUSE_FLAG = '0'
            """.format(self.OSTS_Executing, self.OSTS_Completion_Conf)
        Rows = self.MariaDBCA.sql_execute(sql, [])

        Log = "処理対象のT_EVRL_ACTION_LOG ({}件)".format(len(Rows))
        g.applogger.info(Log)
        for Row in Rows:
            Data_Error = False
            if not Row['JOIN_CONDUCTOR_INSTANCE_ID']:
                # T_COMN_CONDUCTOR_INSTANCEに対象レコードなし
                Log = "T_COMN_CONDUCTOR_INSTANCEに対象レコードなし。(ACTION_LOG_ID: {} CONDUCTOR_INSTANCE_ID: {})".format(Row["ACTION_LOG_ID"], Row["CONDUCTOR_INSTANCE_ID"])
                g.applogger.info(Log)
                Data_Error = True
            else:
                if Row['TAB_B_DISUSE_FLAG'] != '0':
                    # T_COMN_CONDUCTOR_INSTANCEの対象レコードが廃止
                    Log = "T_COMN_CONDUCTOR_INSTANCEの対象レコードが廃止。(ACTION_LOG_ID: {} CONDUCTOR_INSTANCE_ID: {})".format(Row["ACTION_LOG_ID"], Row["CONDUCTOR_INSTANCE_ID"])
                    g.applogger.info(Log)
                    Data_Error = True

            if not Row['JOIN_RULE_ID']:
                # T_EVRL_RULEに対象レコードなし
                Log = "T_EVRL_RULEに対象レコードなし。(ACTION_LOG_ID: {} RULE_ID: {})".format(Row["ACTION_LOG_ID"], Row["RULE_ID"])
                g.applogger.info(Log)
                Data_Error = True
            else:
                if Row['TAB_C_DISUSE_FLAG'] != '0':
                    # T_EVRL_RULEの対象レコードが廃止
                    Log = "T_EVRL_RULEの対象レコードが廃止。(ACTION_LOG_ID: {} RULE_ID: {})".format(Row["ACTION_LOG_ID"], Row["RULE_ID"])
                    g.applogger.info(Log)
                    Data_Error = True

            TargetStatusList = []
            TargetStatusList.append(self.CSTS_Completed)         # 正常終了
            TargetStatusList.append(self.CSTS_Abend)             # 異常終了
            TargetStatusList.append(self.CSTS_Warning_end)       # 警告終了
            TargetStatusList.append(self.CSTS_Emergency_stop)    # 緊急停止
            TargetStatusList.append(self.CSTS_Schedule_Cancel)   # 予約取消
            TargetStatusList.append(self.CSTS_Unexpected_Error)  # 想定外エラー
            # CONDUCTORの状態判定
            if Row['CONDUCTOR_STATUS_ID'] in TargetStatusList:
                if Row['CONDUCTOR_STATUS_ID'] == self.CSTS_Completed:
                    Row['STATUS_ID'] = self.OSTS_Completed
                else:
                    Row['STATUS_ID'] = self.OSTS_Completed_Abend
            else:
                continue

            # 結論履歴にリンクするデータベースのレコードが不正の場合
            if Data_Error is True:
                Row['STATUS_ID'] = self.OSTS_Completed_Abend

            # アクション履歴更新
            UpdateRow = {}
            for colname in ['ACTION_LOG_ID', 'STATUS_ID']:
                UpdateRow[colname] = Row[colname]

            Log = "T_EVRL_ACTION_LOG更新 (ACTION_LOG_ID: {} STATUS_ID: {})".format(Row["ACTION_LOG_ID"], Row["STATUS_ID"])
            g.applogger.info(Log)
            print(UpdateRow[colname])

            self.MariaDBCA.table_update('T_EVRL_ACTION_LOG', UpdateRow, 'ACTION_LOG_ID', True)

            # 結論イベント登録
            if Row['STATUS_ID'] in [self.OSTS_Completed, self.OSTS_Completed_Abend]:
                # 結論イベント登録
                self.InsertConclusionEvent(Row)

    def InsertConclusionEvent(self, RuleInfo):
        conclusion_ids = {}
        addlabels = {}
        RuleInfo["LABELING_INFORMATION_JSON"] = json.loads(RuleInfo["LABELING_INFORMATION_JSON"])
        for key, value in RuleInfo["LABELING_INFORMATION_JSON"].items():
            name = self.getIDtoName(key)
            if name is False:
                Log = "ラベルマスタ 未登録 (LABEL_KEY_ID: {})".format(key)
                g.applogger.info(Log)
                return False, {}
            addlabels[name] = value
            conclusion_ids[name] = key

        NowTime = int(datetime.now().timestamp())
        RaccEventDict = {}

        # RaccEventDict["_id"] = id
        RaccEventDict["labels"] = {}
        RaccEventDict["labels"]["_exastro_event_collection_settings_id"] = ''
        RaccEventDict["labels"]["_exastro_fetched_time"] = NowTime
        RaccEventDict["labels"]["_exastro_end_time"] = NowTime + int(RuleInfo['REEVALUATE_TTL'])
        RaccEventDict["labels"]["_exastro_evaluated"] = "0"
        RaccEventDict["labels"]["_exastro_undetected"] = "0"
        RaccEventDict["labels"]["_exastro_timeout"] = "0"
        RaccEventDict["labels"]["_exastro_type"] = "conclusion"
        RaccEventDict["labels"]["_exastro_rule_name"] = RuleInfo['RULE_LABEL_NAME']
        for name, value in addlabels.items():
            RaccEventDict["labels"][name] = value
        RaccEventDict["exatsro_rule"] = {}
        RaccEventDict["exatsro_rule"]['id'] = RuleInfo['RULE_ID']
        RaccEventDict["exatsro_rule"]['name'] = RuleInfo['RULE_NAME']
        RaccEventDict["exastro_events"] = json.loads(RuleInfo['EVENT_ID_JSON'])
        RaccEventDict["exastro_label_key_inputs"] = {}
        RaccEventDict["exastro_label_key_inputs"] = conclusion_ids

        _id = self.MongoEvts.insert_event(RaccEventDict)

        Log = "結論イベント登録 (_id: {})".format(_id)
        g.applogger.info(Log)

        return True
