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
import csv
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

    # 単体テスト用
    # connect MongoDB
    MongoDBCA = "DB"
    # connect MariaDB
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # UnImplementLog("処理時間固定")
    # 単体テスト用
    # judgeTime = int(time.time())
    judgeTime = 10000

    ret = JudgeMain(objdbca, MongoDBCA, judgeTime, workspace_path)
    if ret is False:
        g.applogger.debug("JudgeMain False")

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
        # UnImplementLog("ラベルマスタ取得")
        # UnImplementLog("select * from T_EVRL_LABEL_KEY_INPUTとT_EVRL_LABEL_KEY_CONCLUSIONがunionされてView where DISUSE_FLAG = '0'")
        # 単体テスト用
        # LabelObj = T_EVRL_LABEL_KEY_INPUT(self.MariaDBCA, 'csv/T_EVRL_LABEL_KEY_INPUT.csv')

        # self.LabelObj = LabelObj
        self.EventObj = EventObj

    def filterJudge(self, FilterRow, objdbca):
        DebugMode = False
        UseEveventRows = ""
        EventJudgList = []
        # テーブル名
        t_evrl_label_key_input = 'T_EVRL_LABEL_KEY_INPUT'  # ラベルマスタ

        # 「ラベルマスタ」からレコードを取得
        labelList = objdbca.table_select(t_evrl_label_key_input, 'WHERE DISUSE_FLAG = %s', [0])
        if not labelList:
            tmp_msg = "処理対象レコードなし。Table:T_EVRL_LABEL_KEY_INPUT"
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
            # LabelName = self.LabelObj.getIDtoName(LabelKey)
            # DebugLog(DebugMode, "<<LabelName: %s>>" % (LabelName))

            # ラベリングされたイベントからデータを抜出す条件設定
            # EventJudgList.append(self.makeEventJudgList(LabelName, LabelValue, LabelCondition))
            EventJudgList.append(self.makeEventJudgList(LabelKey, LabelValue, LabelCondition))

        ret, UseEventIdList = self.EventJudge(EventJudgList)
        if ret is False:
            return False, UseEventIdList

        return True, UseEventIdList[0]

    def EventJudge(self, EventJudgList):
        DebugMode = False
        # イベント 検索
        tmp_msg = "{} イベント検索 JSON: {}".format(DebugMode, str(EventJudgList))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        ret, UsedEventIdList = self.EventObj.findT_EVRL_EVENT(EventJudgList)
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

    def SummaryofFiltersUsedinRules(self, FilterList, RuleList, EventObj, IncidentDict):
        # FiltersUsedinRulesDictの構造
        # FiltersUsedinRulesDict[フィルタID] = { 'rule_id': RULE_ID, 'rule_priority': RULE_PRIORITY, 'count': フィルタ使用数 }
        FiltersUsedinRulesDict = {}
        for RuleRow in RuleList:
            # for FilterId in RuleRow['RULE_COMBINATION_JSON']['filter_key']:
            rule_combination_json = json.loads(RuleRow.get('RULE_COMBINATION_JSON'))
            for FilterId in rule_combination_json['filter_key']:
                if FilterId in FiltersUsedinRulesDict:
                    FiltersUsedinRulesDict[FilterId]['count'] += 1
                else:
                    FiltersUsedinRulesDict[FilterId] = {}
                    FiltersUsedinRulesDict[FilterId]['rule_id'] = RuleRow['RULE_ID']
                    FiltersUsedinRulesDict[FilterId]['rule_priority'] = RuleRow['RULE_PRIORITY']
                    FiltersUsedinRulesDict[FilterId]['count'] = 1

        return FiltersUsedinRulesDict

    def TargetRuleExtraction(self, TargetLevel, RuleList, FiltersUsedinRulesDict, EventObj, IncidentDict):
        DebugMode = True
        TargetRuleList = []
        defObj = RuleJudgementConst()
        for RuleRow in RuleList:
            hit = True
            rule_combination_json = json.loads(RuleRow.get('RULE_COMBINATION_JSON'))
            for FilterId in rule_combination_json['filter_key']:
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

                # ルール抽出対象: 複数のルールで使用しているフィルタでタイムアウトを迎えるフィルタを使用しているルール※2の場合
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
                            ret, EventRow = self.EventObj.getT_EVRL_EVENT(IncidentDict[FilterId])
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
                    for FilterId in rule_combination_json['filter_key']:
                        if FiltersUsedinRulesDict[FilterId]['count'] != 1:
                            hit = True
                            break
            if hit is True:
                TargetRuleList.append(RuleRow)

        return TargetRuleList

    def RuleJudge(self, RuleRow, IncidentDict):
        UseEventIdList = []
        DebugMode = True

        tmp_msg = "=========================================================================================================================="
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = "ルール判定開始 RULE_ID:{} RULE_NAME:{}  JSON:{}".format(RuleRow['RULE_ID'], RuleRow['RULE_NAME'], str(RuleRow["RULE_COMBINATION_JSON"]))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        # ルール内のフィルタ条件判定用辞書初期化
        FilterResultDict = {}
        FilterResultDict['True'] = 0
        FilterResultDict['False'] = 0
        FilterResultDict['Count'] = 0
        FilterResultDict['EventList'] = []
        FilterResultDict['Operator'] = ''

        rule_combination_json = json.loads(RuleRow.get('RULE_COMBINATION_JSON'))
        if not rule_combination_json['filter_operator']:
            rule_combination_json['filter_operator'] = ''

        FilterResultDict['Operator'] = str(rule_combination_json['filter_operator'])

        # 論理演算子「operator」設定確認
        if self.checkRuleOperatorId(FilterResultDict['Operator']) is False:
            tmp_msg = "ルール管理　論理演算子「operator」が不正 RULE_ID:{} RULE_NAME:{} JSON:{}".format(RuleRow['RULE_ID'], RuleRow['RULE_NAME'], str(RuleRow["RULE_COMBINATION_JSON"]))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # フィルタ毎のループ
        for FilterId in rule_combination_json['filter_key']:
            # TraceLog("フィルタ管理判定開始  FILTER_ID: %s" % (FilterId))
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
            tmp_msg = "ルール判定結果: マッチ RULE_ID:{} RULE_NAME:{} JSON:{}".format(RuleRow['RULE_ID'], RuleRow['RULE_NAME'], str(RuleRow["RULE_COMBINATION_JSON"]))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        else:
            tmp_msg = "ルール判定結果: アンマッチ RULE_ID:{} RULE_NAME:{} JSON:{}".format(RuleRow['RULE_ID'], RuleRow['RULE_NAME'], str(RuleRow["RULE_COMBINATION_JSON"]))
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

        ret, EventRow = self.EventObj.getT_EVRL_EVENT(IncidentDict[FilterId])
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
        for key, value in RuleRow["LABELING_INFORMATION_JSON"].items():
            name = self.LabelObj.getIDtoName(key)
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
        # UnImplementLog("MongoDBに結論イベント登録")
        # TraceLog(RaccEventDict)
        tmp_msg = "MongoDBに結論イベント登録: {}>>".format(RaccEventDict)
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


def JudgeMain(objdbca, MongoDBCA, judgeTime, workspace_path):
    EventList = []
    JudgeEventDict = {}
    IncidentDict = {}

    defObj = RuleJudgementConst()

    # テーブル名
    t_evrl_filter = 'T_EVRL_FILTER'  # フィルター管理

    # 「フィルター管理」からレコードを取得
    filterList = objdbca.table_select(t_evrl_filter, 'WHERE DISUSE_FLAG = %s AND AVAILABLE_FLAG = %s', [0, 1])
    if not filterList:
        tmp_msg = "処理対象レコードなし。Table:T_EVRL_FILTER"
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False

    tmp_msg = "フィルター管理取得 件数: {}".format(str(len(filterList)))
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # テーブル名
    t_evrl_rule = 'T_EVRL_RULE'  # ルール管理

    # 「ルール管理」からレコードを取得
    ruleList = objdbca.table_select(t_evrl_rule, 'WHERE DISUSE_FLAG = %s AND AVAILABLE_FLAG = %s ORDER BY RULE_PRIORITY', [0, 1])
    if not ruleList:
        tmp_msg = "処理対象レコードなし。Table:T_EVRL_RULE"
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False

    tmp_msg = "ルール管理取得 件数: {}".format(str(len(ruleList)))
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # イベントデータ取得
    # 単体テスト用
    eventcsv_path = workspace_path + '/tmp/driver/T_EVRL_EVENT.csv'
    if os.path.isfile(eventcsv_path) is False:
        return

    EventObj = T_EVRL_EVENT(MongoDBCA, judgeTime, eventcsv_path)
    count = EventObj.countT_EVRL_EVENT()
    if count == 0:
        tmp_msg = "処理対象イベントなし"
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False

    tmp_msg = "イベント取得 対象時間:{} 取得件数: {}".format(judgeTime, count)
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    ret, timeout_Event_Id_List = EventObj.getTimeOutT_EVRL_EVENT()
    tmp_msg = "有効期限判定　タイムアウト件数: {}".format(len(timeout_Event_Id_List))
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # タイムアウトイベント有無判定
    if len(timeout_Event_Id_List) > 0:
        # タイムアウトしているイベントの_exastro_timeoutを1に更新
        update_Flag_Dict = {"_exastro_timeout": '1'}
        EventObj.updateLablesFlagT_EVRL_EVENT(timeout_Event_Id_List, update_Flag_Dict)
        tmp_msg = "イベント更新  タイムアウト({}) ids: {}".format(str(update_Flag_Dict), str(timeout_Event_Id_List))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    EventObj.printT_EVRL_EVENT()
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
    FiltersUsedinRulesDict = judgeObj.SummaryofFiltersUsedinRules(filterList, ruleList, EventObj, IncidentDict)

    tmp_msg = "ルール判定開始"
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    JudgeLevelList = ['Level1', 'Level2', 'Level3']

    # 全レベルループ -----
    newIncidentCount = {}
    while True:
        # レベル毎のループ -----
        for TargetLevel in JudgeLevelList:

            newIncidentCount[TargetLevel] = 0

            # 各レベルに対応したルール抽出
            TargetRuleList = judgeObj.TargetRuleExtraction(TargetLevel, ruleList, FiltersUsedinRulesDict, EventObj, IncidentDict)

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
                        # 結論イベント登録
                        ret, ConclusionEventRow = judgeObj.putRaccEvent(ruleRow, UseEventIdList)

                        # 結論イベントに処理で必要なラベル情報を追加
                        ConclusionEventRow = EventObj.AddLocalLabel(ConclusionEventRow, defObj.DF_LOCAL_LABLE_NAME, defObj.DF_LOCAL_LABLE_STATUS, defObj.DF_PROC_EVENT)

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
                                EventObj.appendT_EVRL_EVENT(ConclusionEventRow)
                                newIncident = True

                        # アクション履歴の登録
                        if getattr(g, 'USER_ID', None) is None:
                            g.USER_ID = '110101'

                        objdbca = DBConnectWs()

                        objdbca.db_transaction_start()

                        Row = {}
                        Row["CONDUCTOR_INSTANCE_ID"] = "CONDUCTOR_INSTANCE_ID"
                        Row["CONDUCTOR_INSTANCE_NAME"] = "CONDUCTOR_INSTANCE_NAME"
                        # 6:正常終了　7:異常終了
                        Row["STATUS_ID"] = '6'
                        Row["OPERATION_NAME"] = "OPERATION_NAME"
                        Row["RULE_NAME"] = "RULE_NAME"
                        Row["ACTION_NAME"] = "ACTION_NAME"
                        Row["EVENT_ID_LIST"] = json.dumps("['event_id_01', 'event_id_02']")
                        Row["EXECUTION_USER"] = UserIDtoUserName(objdbca, g.USER_ID)
                        Row["TIME_REGISTER"] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                        Row["NOTE"] = None
                        Row["DISUSE_FLAG"] = '0'

                        RegistrActionLog(objdbca, Row)

                        objdbca.db_transaction_end(True)

                        # conductor実行
                        conductor_class_id = '016c76c5-b3a5-4839-81d7-2e159764a070'
                        operation_id = 'eb891309-8ddf-4b35-940f-a2f3098bf783'
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

                        # 使用済みインシデントフラグを立てる  _exastro_evaluated='1'
                        update_Flag_Dict = {"_exastro_evaluated": '1'}
                        EventObj.updateLablesFlagT_EVRL_EVENT(UseEventIdList, update_Flag_Dict)

                        tmp_msg = "使用済みインシデントフラグを立てる ({}) ids: {}".format(str(update_Flag_Dict), str(UseEventIdList))
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

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
        # 各レベルのルール判定で結論イベントを発生していないか確認
        total = 0
        for TargetLevel in JudgeLevelList:
            total += newIncidentCount[TargetLevel]
        if total == 0:
            break

    # ----- 全レベルループ
    tmp_msg = "ルール判定終了"
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # 処理後タイムアウトイベント検出
    PostProcTimeoutEventIdList = EventObj.getPostProcTimeoutEvent(IncidentDict)
    if len(PostProcTimeoutEventIdList) > 0:
        tmp_msg = "処理後タイムアウト検出 EventId: {}".format(str(PostProcTimeoutEventIdList))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        # 処理後タイムアウトの_exastro_timeoutを1に更新
        update_Flag_Dict = {"_exastro_timeout": '1'}
        EventObj.updateLablesFlagT_EVRL_EVENT(PostProcTimeoutEventIdList, update_Flag_Dict)
        tmp_msg = "イベント更新  処理後タイムアウト ({}) ids:{}".format(str(update_Flag_Dict), str(PostProcTimeoutEventIdList))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    else:
        tmp_msg = "処理後タイムアウトイベントなし"
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # 未知イベント検出
    UnusedEventIdList = EventObj.getUnuseEvent(IncidentDict)
    if len(UnusedEventIdList) > 0:
        tmp_msg = "未知イベント検出 EventId: {}>>".format(str(UnusedEventIdList))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        # 未知イベントの_exastro_undetectedを1に更新
        update_Flag_Dict = {"_exastro_undetected": '1'}
        EventObj.updateLablesFlagT_EVRL_EVENT(UnusedEventIdList, update_Flag_Dict)
        tmp_msg = "イベント更新  未知イベント ({}) ids:{}".format(str(update_Flag_Dict), str(UnusedEventIdList))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    else:
        tmp_msg = "未知イベントなし"
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # デバック用　イベント表示
    EventObj.printT_EVRL_EVENT()


def UserIDtoUserName(objdbca, UserId):
    UserEnv = g.LANGUAGE.upper()
    UserNameCol = "USER_NAME_{}".format(UserEnv)
    TableName = "T_COMN_BACKYARD_USER"
    WhereStr = "WHERE USER_ID = '%s' AND DISUSE_FLAG='0'" % (UserId)

    Rows = objdbca.table_select(TableName, WhereStr, [])
    for Row in Rows:
        UserName = Row[UserNameCol]
    return UserName


def RegistrActionLog(objdbca, Row):
    is_RegisterFistory = True
    TableName = 'T_EVRL_ACTION_LOG'
    PrimaryKey = 'ACTION_LOG_ID'
    objdbca.table_insert(TableName, Row, PrimaryKey, is_RegisterFistory)


def conductor_execute(objdbca, conductor_class_id, operation_id):
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


class T_EVRL_EVENT():
    def __init__(self, MongoDBCA, JudgeTime, filename):
        self.MongoDBCA = MongoDBCA
        self.filename = filename
        self.EventDict = {}
        DebugMode = False   # 単体テスト用
        # DB find select * from T_EVRL_EVENT where labels._exastro_timeout = '0' and labels._exastro_undetected = '0' and labels._exastro_evaluated = '0'
        #  Now: インシデント判定開始時間
        #  TTL: Now -  (イベント:_exastro_end_time - _exastro_fetched_time)
        #  f  : _exastro_fetched_time
        #  e  : _exastro_end_time
        #
        #                         TTL*2                    Now     イベント検索条件  _exastro_evaluate": "0"
        #                          |                        |                        _exastro_undetected": "0"
        #  〇:     f--------------------------------------------e                    _exastro_timeout": "0"
        #  ●:                            f----------e             各イベントのTTL全て同値
        #  〇:                                       f----------e
        #  ●:                               f----------e
        #  ●:                       f----------e
        #  □:       f----------e
        #  ×:                                                  f----------e
        #  結論イベント:                                    f----------e
        #
        #  〇: 処理対象イベント
        #  ●: 処理対象イベント    ルール判定後に利用がない場合、
        #      ※一回はルール判定  タイムアウトイベントへ
        #      で使用する          "_exastro_evaluate": "0"
        #                          "_exastro_undetected": "0"
        #                          "_exastro_timeout": "1"
        #  □: 処理対象外イベント  タイムアウトイベントへ
        #                          "_exastro_evaluate": "0"
        #                          "_exastro_undetected": "0"
        #                          "_exastro_timeout": "1"
        #  ×: 処理対象外イベント
        #  Now: インシデント判定開始時間
        #  TTL: Now -  (イベント:_exastro_end_time - _exastro_fetched_time)
        #  f  : _exastro_fetched_time
        #  e  : _exastro_end_time

        # イベント有効期限設定
        # 対象外×：                      (now  < _exastro_fetched_time)
        # タイムアウト□:                 (_exastro_end_time < TTL*2)
        # 処理対象　処理後タイムアウト●: (TTL*2 <= _exastro_end_time < Now)
        # 処理対象〇:                     (Now <= _exastro_end_time)

        # MongoDB検索
        # UnImplementLog("MongoDB検索処理")
        # UnImplementLog("find T_EVRL_EVENT where labels._exastro_timeout = '0' and labels._exastro_undetected = '0' and labels._exastro_evaluated = '0'")
        ##########################

        defObj = RuleJudgementConst()

        # 単体テスト用
        with open(self.filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                new_row = {}
                new_row["labels"] = {}
                new_row["exastro_labeling_settings"] = {}
                new_row["exastro_label_key_inputs"] = {}
                for key, value in row.items():
                    if key.find("labels.") == 0:
                        if "labels" not in new_row:
                            new_row["labels"] = {}
                        key = key.replace("labels.", "")
                        if key == "array":
                            for keylist in json.loads(value):
                                for labels_key, labels_val in keylist.items():
                                    new_row["labels"][labels_key] = labels_val
                        else:
                            new_row["labels"][key] = value
                    elif key.find("exastro_label_key_inputs") == 0:
                        for keylist in json.loads(value):
                            for labels_key, labels_val in keylist.items():
                                new_row["exastro_label_key_inputs"][labels_key] = labels_val
                    elif key.find("exastro_labeling_settings") == 0:
                        for keylist in json.loads(value):
                            for labels_key, labels_val in keylist.items():
                                new_row["exastro_labeling_settings"][labels_key] = labels_val
                    else:
                        new_row[key] = value

                # 内部処理で必要な項目追加
                new_row[defObj.DF_LOCAL_LABLE_NAME] = {}
                new_row[defObj.DF_LOCAL_LABLE_NAME]["status"] = None

                # イベント有効期間判定
                JudgeTime = int(JudgeTime)
                FatchTime = int(new_row["labels"]['_exastro_fetched_time'])
                EndTime = int(new_row["labels"]['_exastro_end_time'])
                TTL = EndTime - FatchTime
                TTL = JudgeTime - (TTL * 2)
                TmpLabels = {defObj.DF_LOCAL_LABLE_NAME: {defObj.DF_LOCAL_LABLE_STATUS: None}}

                tmp_msg = "{} EventId {} JudgeTime {} FatchTime {} EndTime {} TTL {}".format(DebugMode, new_row['_id'], JudgeTime, FatchTime, EndTime, TTL)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                if FatchTime > EndTime:
                    tmp_msg = "不正なイベント(_exastro_fetched_time > _exastro_end_time)  EventId {}".format(new_row['_id'])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    continue

                # 対象外:×
                elif (JudgeTime < FatchTime):
                    EventStatus = defObj.DF_NOT_PROC_EVENT
                    tmp_msg = "{} 処理対象外イベント:× EventId {}".format(DebugMode, new_row['_id'])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    continue

                # タイムアウト:□
                elif (EndTime < TTL):
                    EventStatus = defObj.DF_TIMEOUT_EVENT
                    tmp_msg = "{} タイムアウト:□ EventId {}".format(DebugMode, new_row['_id'])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                # 処理対象　処理後タイムアウト:●
                elif (TTL <= EndTime < JudgeTime):
                    EventStatus = defObj.DF_POST_PROC_TIMEOUT_EVENT
                    tmp_msg = "{} 処理対象　処理後タイムアウト:● EventId {}".format(DebugMode, new_row['_id'])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                # 処理対象:〇
                elif (JudgeTime <= EndTime):
                    EventStatus = defObj.DF_PROC_EVENT
                    tmp_msg = "{} 処理対象:〇 EventId {}".format(DebugMode, new_row['_id'])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                # その他　想定外のイベントデータ
                else:
                    tmp_msg = "想定外のイベントデータ EventId {} JudgeTime {} FatchTime {} EndTime {} TTL {}".format(new_row['_id'], JudgeTime, FatchTime, EndTime, TTL)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    continue

                # 処理で必要なラベル情報を追加
                new_row = self.AddLocalLabel(new_row, defObj.DF_LOCAL_LABLE_NAME, defObj.DF_LOCAL_LABLE_STATUS, EventStatus)

                # 処理対象のイベント記録
                self.EventDict[new_row['_id']] = new_row

    # 処理で必要なラベル情報を追加
    def AddLocalLabel(self, EventRow, ParentLabel, MemberLabel, Value):
        if ParentLabel not in EventRow:
            EventRow[ParentLabel] = {}
        EventRow[ParentLabel][MemberLabel] = Value
        return EventRow

    def findT_EVRL_EVENT(self, EventJudgList):
        DebugMode = False  ## 単体テスト用
        UsedEventIdList = []
        defObj = RuleJudgementConst()
        for EventId, EventRow in self.EventDict.items():
            tmp_msg = "{} {}".format(DebugMode, str(EventRow))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            # タイムアウトイベント判定
            if str(EventRow['labels']['_exastro_timeout']) != '0':
                tmp_msg = "{} _exastro_timeout not 0".format(DebugMode)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                continue
            # 処理済みイベント判定
            if str(EventRow['labels']['_exastro_evaluated']) != '0':
                tmp_msg = "{} _exastro_evaluated not 0".format(DebugMode)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                continue
            Lables = EventRow['labels']
            JugeResultDict = {}
            JugeResultDict['count'] = 0
            JugeResultDict['True'] = 0
            JugeResultDict['False'] = 0
            for JugeList in EventJudgList:
                JugeResultDict['count'] += 1
                Key = JugeList['LabelKey']
                Value = JugeList['LabelValue']
                Condition = JugeList['LabelCondition']
                tmp_msg = "{} key:{} value:{} Condition:{} check ".format(DebugMode, Key, Value, Condition)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                Hit = False
                if Key in Lables:
                    tmp_msg = "{} Key ok".format(DebugMode)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    if str(Condition) == defObj.DF_TEST_EQ:     # =
                        if Lables[Key] == Value:
                            tmp_msg = "{} hit =".format(DebugMode)
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            Hit = True
                    else:
                        if Lables[Key] != Value:
                            tmp_msg = "{} hit !=".format(DebugMode)
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            Hit = True
                JugeResultDict[str(Hit)] += 1
                if Hit is False:
                    tmp_msg = "{} Not Key Value".format(DebugMode)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    break

            tmp_msg = "{} {}".format(DebugMode, JugeResultDict)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            if JugeResultDict['count'] == JugeResultDict['True']:
                UsedEventIdList.append(EventRow['_id'])
                tmp_msg = "{} Hit Key Value".format(DebugMode)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        return True, UsedEventIdList

    # デバック用
    def printT_EVRL_EVENT(self):
        DebugMode = True
        defObj = RuleJudgementConst()
        tmp_msg = "{} イベント状態".format(DebugMode)
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        for EventId, EventRow in self.EventDict.items():
            id = str(EventRow['_id'])
            eva = str(EventRow['labels']['_exastro_evaluated'])
            und = str(EventRow['labels']['_exastro_undetected'])
            tim = str(EventRow['labels']['_exastro_timeout'])
            localsts = str(EventRow[defObj.DF_LOCAL_LABLE_NAME][defObj.DF_LOCAL_LABLE_STATUS])
            sts = "不明"
            if eva == '0' and und == '1' and tim == '0':
                sts = "未知        "
            elif eva == '0' and und == '0' and tim == '1':
                sts = "タイムアウト"
            elif eva == '0' and und == '0' and tim == '0':
                sts = "今は対応不要"
            elif eva == '1' and und == '0' and tim == '0':
                sts = "要対応      "
            if localsts == defObj.DF_PROC_EVENT:
                localsts = "処理対象:〇"
            elif localsts == defObj.DF_POST_PROC_TIMEOUT_EVENT:
                localsts = "処理対象　処理後タイムアウト:●"
            elif localsts == defObj.DF_TIMEOUT_EVENT:
                localsts = "タイムアウト"
            elif localsts == defObj.DF_NOT_PROC_EVENT:
                localsts = "対象外"
            tmp_msg = "{} id:{} 状態:{}  _exastro_evaluated:{}  _exastro_undetected:{}  _exastro_timeout:{} local_status:{}".format(DebugMode, id, sts, EventRow['labels']['_exastro_evaluated'], EventRow['labels']['_exastro_undetected'], EventRow['labels']['_exastro_timeout'], localsts)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    def countT_EVRL_EVENT(self):
        return (len(self.EventDict))

    def appendT_EVRL_EVENT(self, EventRow):
        self.EventDict[EventRow['_id']] = EventRow

    def getT_EVRL_EVENT(self, EventId):
        if EventId not in self.EventDict:
            return False, {}
        return True, self.EventDict[EventId]

    def getTimeOutT_EVRL_EVENT(self):
        TimeOutEventiIdList = []
        defObj = RuleJudgementConst()
        for EventId, row in self.EventDict.items():
            if row[defObj.DF_LOCAL_LABLE_NAME][defObj.DF_LOCAL_LABLE_STATUS] == defObj.DF_TIMEOUT_EVENT:
                TimeOutEventiIdList.append(EventId)
        return True, TimeOutEventiIdList

    def updateLablesFlagT_EVRL_EVENT(self, EventIdlist, UpdateFlagDict):
        DebugMode = False   # 単体テスト用
        for EventId in EventIdlist:
            if EventId not in self.EventDict:
                tmp_msg = "イベント未登録 EventId = {}".format(EventId)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                return False

            tmp_msg = "{} 更新前: {}".format(DebugMode, str(self.EventDict[EventId]))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            for Key, Value in UpdateFlagDict.items():
                self.EventDict[EventId]['labels'][Key] = Value

            tmp_msg = "{} DB更新: {}".format(DebugMode, str(self.EventDict[EventId]))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # MongoDB 更新
            # self.EventDict[EventId])には、処理用のKey(defObj.DF_LOCAL_LABLE_NAME)が付加されているので注意
            # UnImplementLog("self.EventDict[EventId])には、処理用のKey(defObj.DF_LOCAL_LABLE_NAME)が付加されているので注意")
            # UnImplementLog("MongoDB更新処理 EventId: %s" % (EventId))   # 単体テスト用

        return True

    def getPostProcTimeoutEvent(self, IncidentDict):
        defObj = RuleJudgementConst()
        PostProcTimeoutEventIdList = []
        # 処理後にタイムアウトにするイベントを抽出
        for EventId, EventRow in self.EventDict.items():
            # タイムアウトしたイベントも登録されているのでスキップ
            if str(EventRow['labels']['_exastro_timeout']) != '0':
                continue
            # ルールにマッチしているイベント
            if str(EventRow['labels']['_exastro_evaluated']) != '0':
                continue
            # 処理後にタイムアウトにするイベント
            if EventRow[defObj.DF_LOCAL_LABLE_NAME][defObj.DF_LOCAL_LABLE_STATUS] == defObj.DF_POST_PROC_TIMEOUT_EVENT:
                PostProcTimeoutEventIdList.append(EventRow['_id'])

        return PostProcTimeoutEventIdList

    def getUnuseEvent(self, IncidentDict):
        UnusedEventIdList = []
        # フィルタにマッチしていないイベントを抽出
        for EventId, EventRow in self.EventDict.items():
            # タイムアウトしたイベントも登録されているのでスキップ
            if str(EventRow['labels']['_exastro_timeout']) != '0':
                continue
            # ルールにマッチしているイベント
            if str(EventRow['labels']['_exastro_evaluated']) != '0':
                continue
            # フィルタにマッチしていないイベント
            if EventRow['_id'] not in IncidentDict.values():
                UnusedEventIdList.append(EventRow['_id'])
        return UnusedEventIdList
