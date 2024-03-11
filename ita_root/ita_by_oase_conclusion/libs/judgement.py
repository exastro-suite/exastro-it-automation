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
import json

from common_libs.oase.const import oaseConst
from libs.common_functions import addline_msg, getLabelGroup, getIDtoLabelName


class Judgement:
    def __init__(self, wsDb, wsMongo, EventObj):
        self.wsDb = wsDb
        self.wsMongo = wsMongo

        # ラベルマスタ取得
        self.LabelMasterDict = getLabelGroup(wsDb)

        self.EventObj = EventObj

    def filterJudge(self, FilterRow, wsDb):
        EventJudgList = []

        # 「ラベルマスタ」からレコードを取得
        labelList = wsDb.table_select(oaseConst.T_OASE_LABEL_KEY_INPUT, 'WHERE DISUSE_FLAG = %s', [0])
        if not labelList:
            tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_LABEL_KEY_INPUT])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False

        if type(FilterRow["FILTER_CONDITION_JSON"]) is str:
            filter_condition_json = json.loads(FilterRow.get('FILTER_CONDITION_JSON'))
        else:
            filter_condition_json = FilterRow.get('FILTER_CONDITION_JSON')

        for LabelRow in filter_condition_json:
            # ラベル毎のループ
            LabelKey = str(LabelRow['label_name'])
            LabelValue = str(LabelRow['condition_value'])
            LabelCondition = str(LabelRow['condition_type'])
            tmp_msg = g.appmsg.get_log_message("BKY-90041", [LabelKey, LabelValue, LabelCondition])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # ルールキーからルールラベル名を取得
            LabelName = getIDtoLabelName(self.LabelMasterDict, LabelKey)

            # ラベリングされたイベントからデータを抜出す条件設定
            EventJudgList.append(self.makeEventJudgList(LabelName, LabelValue, LabelCondition))

        ret, UseEventIdList = self.EventJudge(EventJudgList)
        if ret is False:
            return False, UseEventIdList

        return True, UseEventIdList[0]

    def EventJudge(self, EventJudgList):
        # イベント 検索
        tmp_msg = g.appmsg.get_log_message("BKY-90042", [str(EventJudgList)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        ret, UsedEventIdList = self.EventObj.find_events(EventJudgList)
        if len(UsedEventIdList) == 0:
            # 対象イベントなし
            tmp_msg = g.appmsg.get_log_message("BKY-90043", [str(UsedEventIdList)])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, ""
        elif len(UsedEventIdList) == 1:
            # 対象イベントあり
            tmp_msg = g.appmsg.get_log_message("BKY-90044", [str(UsedEventIdList)])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return True, UsedEventIdList
        else:
            # 対象イベント 複数あり
            tmp_msg = g.appmsg.get_log_message("BKY-90045", [str(UsedEventIdList)])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            # 対象イベントが複数ある場合は[ObjectId('aaa'), ObjectId('bbb'), …]の形式で返す
            return False, UsedEventIdList

    def makeEventJudgList(self, LabelName, LabelValue, LabelCondition):
        return {"LabelKey": LabelName, "LabelValue": LabelValue, "LabelCondition": LabelCondition}

    def SummaryofFiltersUsedinRules(self, RuleList):
        # ルールで使用しているフィルタを集計
        # FiltersUsedinRulesDictの構造
        # FiltersUsedinRulesDict[フィルタID] = { 'rule_id': RULE_ID, 'rule_priority': RULE_PRIORITY, 'count': フィルタ使用数 }
        FiltersUsedinRulesDict = {}
        for RuleRow in RuleList:
            FilterA = RuleRow['FILTER_A']
            if FilterA in FiltersUsedinRulesDict:
                FiltersUsedinRulesDict[FilterA]['count'] += 1
            else:
                FiltersUsedinRulesDict[FilterA] = {}
                FiltersUsedinRulesDict[FilterA]['rule_id'] = RuleRow['RULE_ID']
                FiltersUsedinRulesDict[FilterA]['rule_priority'] = RuleRow['RULE_PRIORITY']
                FiltersUsedinRulesDict[FilterA]['count'] = 1

            FilterB = RuleRow.get('FILTER_B')
            if FilterB is None:
                # FilterBは必須項目ではないのでNoneの場合はスキップする
                continue

            if FilterB in FiltersUsedinRulesDict:
                FiltersUsedinRulesDict[FilterB]['count'] += 1
            else:
                FiltersUsedinRulesDict[FilterB] = {}
                FiltersUsedinRulesDict[FilterB]['rule_id'] = RuleRow['RULE_ID']
                FiltersUsedinRulesDict[FilterB]['rule_priority'] = RuleRow['RULE_PRIORITY']
                FiltersUsedinRulesDict[FilterB]['count'] = 1

        return FiltersUsedinRulesDict

    def TargetRuleExtraction(self, TargetLevel, RuleList, FiltersUsedinRulesDict, IncidentDict):
        TargetRuleList = []
        FilterList = []

        for RuleRow in RuleList:
            hit = True
            FilterList = []
            FilterList.append(RuleRow['FILTER_A'])
            if RuleRow.get('FILTER_B') is not None:
                FilterList.append(RuleRow['FILTER_B'])

            for FilterId in FilterList:
                if FilterId not in FiltersUsedinRulesDict:
                    tmp_msg = g.appmsg.get_log_message("BKY-90046", [RuleRow['RULE_ID'], FilterId])
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
                        tmp_msg = g.appmsg.get_log_message("BKY-90047", [RuleRow['RULE_ID'], FilterId])
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                        hit = False
                    else:
                        if (isinstance(IncidentDict[FilterId], list)):
                            tmp_msg = g.appmsg.get_log_message("BKY-90048", [RuleRow['RULE_ID'], FilterId, IncidentDict[FilterId]])
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            hit = False
                        else:
                            pass
                            ret, EventRow = self.EventObj.get_events(IncidentDict[FilterId])
                            if ret is False:
                                tmp_msg = g.appmsg.get_log_message("BKY-90049", [RuleRow['RULE_ID'], FilterId, IncidentDict[FilterId]])
                                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                hit = False
                            else:
                                if EventRow[oaseConst.DF_LOCAL_LABLE_NAME][oaseConst.DF_LOCAL_LABLE_STATUS] != oaseConst.DF_POST_PROC_TIMEOUT_EVENT:
                                    hit = False
                                else:
                                    hit = True
                                    break

            if TargetLevel == "Level2":
                if hit is True:
                    hit = False
                    # フィルタを利用しているルールが複数ある事を確認
                    for FilterId in FilterList:
                        if FiltersUsedinRulesDict[FilterId]['count'] != 1:
                            hit = True
                            break
            if hit is True:
                TargetRuleList.append(RuleRow)

        return TargetRuleList

    def RuleJudge(self, RuleRow, IncidentDict, actionIdList):
        UseEventIdList = []

        tmp_msg = g.appmsg.get_log_message("BKY-90050", [RuleRow['RULE_ID'], RuleRow['RULE_NAME'], RuleRow['FILTER_A'], RuleRow['FILTER_OPERATOR'], RuleRow['FILTER_B']])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        # ルール内のフィルタ条件判定用辞書初期化
        FilterResultDict = {}
        FilterResultDict['True'] = 0
        FilterResultDict['False'] = 0
        FilterResultDict['Count'] = 0
        FilterResultDict['EventList'] = []
        FilterResultDict['Operator'] = ''

        if not RuleRow['FILTER_OPERATOR']:
            RuleRow['FILTER_OPERATOR'] = ''

        # ルールに設定されているアクションIDが異常ではないかチェック
        action_id = RuleRow['ACTION_ID']
        if action_id is not None and action_id not in actionIdList:
            return False, UseEventIdList

        # ルールに設定されている結論ラベルが異常ではないかチェック
        if type(RuleRow["CONCLUSION_LABEL_SETTINGS"]) is str:
            RuleRow["CONCLUSION_LABEL_SETTINGS"] = json.loads(RuleRow["CONCLUSION_LABEL_SETTINGS"])

        for row in RuleRow["CONCLUSION_LABEL_SETTINGS"]:
            label_key = row.get('label_key')
            name = getIDtoLabelName(self.LabelMasterDict, label_key)
            if name is False:
                return False, UseEventIdList

        FilterResultDict['Operator'] = str(RuleRow['FILTER_OPERATOR'])

        # 論理演算子「operator」設定確認
        if self.checkRuleOperatorId(FilterResultDict['Operator']) is False:
            tmp_msg = g.appmsg.get_log_message("BKY-90051", [RuleRow['RULE_ID'], RuleRow['RULE_NAME'], RuleRow['FILTER_A'], RuleRow['FILTER_OPERATOR'], RuleRow['FILTER_B']])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # フィルタ毎のループ
        FilterList = []
        FilterList.append(RuleRow['FILTER_A'])
        if RuleRow['FILTER_B'] is not None:
            FilterList.append(RuleRow['FILTER_B'])
        for FilterId in FilterList:
            tmp_msg = g.appmsg.get_log_message("BKY-90052", [FilterId])
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
                tmp_msg = g.appmsg.get_log_message("BKY-90053", [FilterId])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            else:
                tmp_msg = g.appmsg.get_log_message("BKY-90054", [FilterId])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        tmp_msg = g.appmsg.get_log_message("BKY-90055", [str(ret)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        ret = self.checkFilterCondition(FilterResultDict, IncidentDict)
        if ret is True:
            tmp_msg = g.appmsg.get_log_message("BKY-90056", [RuleRow['RULE_ID'], RuleRow['RULE_NAME'], RuleRow['FILTER_A'], RuleRow['FILTER_OPERATOR'], RuleRow['FILTER_B']])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        else:
            tmp_msg = g.appmsg.get_log_message("BKY-90057", [RuleRow['RULE_ID'], RuleRow['RULE_NAME'], RuleRow['FILTER_A'], RuleRow['FILTER_OPERATOR'], RuleRow['FILTER_B']])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        if ret is False:
            return False, UseEventIdList

        for EventRow in FilterResultDict['EventList']:
            UseEventIdList.append(EventRow['_id'])

        return True, UseEventIdList

    def MemoryBaseFilterJudge(self, FilterId, IncidentDict):
        if FilterId not in IncidentDict:
            tmp_msg = g.appmsg.get_log_message("BKY-90058", [FilterId])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, {}

        if type(IncidentDict[FilterId]) is list:
            tmp_msg = g.appmsg.get_log_message("BKY-90059", [FilterId])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, {}

        ret, EventRow = self.EventObj.get_events(IncidentDict[FilterId])
        if ret is False:
            tmp_msg = g.appmsg.get_log_message("BKY-90043", [FilterId])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, {}

        if str(EventRow['labels']['_exastro_evaluated']) == '0':
            return True, EventRow
        else:
            tmp_msg = g.appmsg.get_log_message("BKY-90060", [FilterId])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, {}

    def checkFilterCondition(self, FilterResultDict, IncidentDict):
        if FilterResultDict['Operator'] == oaseConst.DF_OPE_OR:
            if FilterResultDict['True'] == 1:
                # or条件の場合、片方がマッチした時のみTrueとする
                return True
            elif FilterResultDict['True'] == 2:
                # 両方のフィルターにマッチした場合は未知とするためIncidentDictから該当の要素を削除する
                for event in FilterResultDict['EventList']:
                    del_key = [key for key, value in IncidentDict.items() if value == event['_id']]
                    del IncidentDict[del_key[0]]
        elif FilterResultDict['Operator'] == oaseConst.DF_OPE_AND:
            if FilterResultDict['False'] == 0:
                return True
        elif FilterResultDict['Operator'] == oaseConst.DF_OPE_ORDER:
            if FilterResultDict['False'] != 0:
                return False
            f_time = None
            if len(FilterResultDict['EventList']) > 1:
                for EventRow in FilterResultDict['EventList']:
                    if not f_time:
                        f_time = EventRow['labels']['_exastro_fetched_time']
                    else:
                        # イベント発生順の確認
                        # 発生順　A => B
                        if EventRow['labels']['_exastro_fetched_time'] > f_time:
                            return True
                        else:
                            return False
            return True
        else:
            if FilterResultDict['True'] != 0:
                return True
        return False

    def checkRuleOperatorId(self, Operator):
        if not Operator:
            return True
        if Operator in (oaseConst.DF_OPE_OR, oaseConst.DF_OPE_AND, oaseConst.DF_OPE_ORDER):
            return True
        return False

    # def putRaccEvent(self, RuleRow, UseEventIdList):
    #     # action.InsertConclusionEventとほとんど同じ関数だからまとめたい
    #     addlabels = {}
    #     label_key_inputs = {}
    #     if type(RuleRow["CONCLUSION_LABEL_SETTINGS"]) is str:
    #         RuleRow["CONCLUSION_LABEL_SETTINGS"] = json.loads(RuleRow["CONCLUSION_LABEL_SETTINGS"])
    #     for row in RuleRow["CONCLUSION_LABEL_SETTINGS"]:
    #         label_key = row.get('label_key')
    #         name = self.getIDtoLabelName(label_key)
    #         if name is False:
    #             tmp_msg = g.appmsg.get_log_message("BKY-90061", [label_key])
    #             g.applogger.info(tmp_msg)
    #             return False, {}
    #         label_key_inputs[name] = label_key
    #         addlabels[name] = row.get('label_value')

    #     RaccEventDict = {}

    #     t1 = int(datetime.datetime.now().timestamp())
    #     ttl = int(RuleRow['TTL'])

    #     RaccEventDict["labels"] = {}
    #     RaccEventDict["labels"]["_exastro_event_collection_settings_id"] = ''
    #     RaccEventDict["labels"]["_exastro_fetched_time"] = t1
    #     RaccEventDict["labels"]["_exastro_end_time"] = t1 + ttl
    #     RaccEventDict["labels"]["_exastro_evaluated"] = "0"
    #     RaccEventDict["labels"]["_exastro_undetected"] = "0"
    #     RaccEventDict["labels"]["_exastro_timeout"] = "0"
    #     RaccEventDict["labels"]["_exastro_checked"] = "1"
    #     RaccEventDict["labels"]["_exastro_type"] = "conclusion"
    #     RaccEventDict["labels"]["_exastro_rule_name"] = RuleRow['RULE_LABEL_NAME']
    #     for name, value in addlabels.items():
    #         RaccEventDict["labels"][name] = value
    #     RaccEventDict["exastro_created_at"] = datetime.datetime.utcnow()
    #     RaccEventDict["exastro_rules"] = []
    #     rule_data = {'id': RuleRow['RULE_ID'], 'name': RuleRow['RULE_NAME']}
    #     RaccEventDict["exastro_rules"].insert(0, rule_data)
    #     RaccEventDict["exastro_events"] = list(map(repr, UseEventIdList))
    #     RaccEventDict["exastro_label_key_inputs"] = {}
    #     RaccEventDict["exastro_label_key_inputs"] = label_key_inputs

    #     # MongoDBに結論イベント登録
    #     _id = self.EventObj.insert_event(RaccEventDict)

    #     tmp_msg = g.appmsg.get_log_message("BKY-90062", [_id])
    #     g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    #     return True, RaccEventDict

    def ConclusionLabelUsedInFilter(self, FilterCheckLabelDict, FilterList):
        UsedFilterIdList = []
        # FilterCheckLabelDict = [{'i_11': 'down', 'i_100': 'ap11'}]
        for FilterRow in FilterList:
            FilterId = FilterRow["FILTER_ID"]
            ret = self.ConclusionFilterJudge(FilterCheckLabelDict, FilterRow)
            if ret is True:
                tmp_msg = g.appmsg.get_log_message("BKY-90063", [FilterId])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                UsedFilterIdList.append(FilterId)
            else:
                tmp_msg = g.appmsg.get_log_message("BKY-90064", [FilterId])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # マッチしたフィルタの数を判定
        if len(UsedFilterIdList) > 0:
            return True, UsedFilterIdList
        return False, UsedFilterIdList

    def ConclusionFilterJudge(self, FilterCheckLabelDict, FilterRow):
        tmp_msg = g.appmsg.get_log_message("BKY-90065", [str(FilterCheckLabelDict)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        # FilterRow['FILTER_CONDITION_JSON'] = [{'key': 'c_01_name', 'condition': '0', 'value': 'c_01'}, {'key': 'c_02_name', 'condition': '0', 'value': 'c_02'}]

        if type(FilterRow["FILTER_CONDITION_JSON"]) is str:
            FilterRow['FILTER_CONDITION_JSON'] = json.loads(FilterRow['FILTER_CONDITION_JSON'])
        LabelHitCount = 0
        for FilterLabels in FilterRow['FILTER_CONDITION_JSON']:
            FilterName = FilterLabels['label_name']
            FilterValue = FilterLabels['condition_value']
            FilterCondition = str(FilterLabels['condition_type'])
            tmp_msg = g.appmsg.get_log_message("BKY-90066", [FilterName, FilterValue, FilterCondition])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            LabelHit = False
            labeldict = {}
            for row in FilterCheckLabelDict:
                label_key = row.get('label_key')
                labeldict[label_key] = row.get('label_value')

            for LabelName, LabelValue in labeldict.items():
                if (FilterName == LabelName and FilterValue == LabelValue and FilterCondition == oaseConst.DF_TEST_EQ) or\
                        (FilterName == LabelName and FilterValue != LabelValue and FilterCondition == oaseConst.DF_TEST_NE):
                    LabelHit = True
                    LabelHitCount += 1
                    tmp_msg = g.appmsg.get_log_message("BKY-90067", [LabelName, LabelValue])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    break
            if LabelHit is True:
                tmp_msg = g.appmsg.get_log_message("BKY-90068", [])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                pass
            else:
                tmp_msg = g.appmsg.get_log_message("BKY-90069", [])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                break

        if LabelHitCount != len(FilterRow['FILTER_CONDITION_JSON']):
            tmp_msg = g.appmsg.get_log_message("BKY-90070", [])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False
        # 結論ラベル数＞フィルタラベル数の場合
        if LabelHitCount != len(FilterCheckLabelDict):
            tmp_msg = g.appmsg.get_log_message("BKY-90071", [])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False

        return True
