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
    def __init__(self, wsDb, EventObj):
        self.wsDb = wsDb
        self.EventObj = EventObj

        # ラベルマスタ取得
        self.LabelMasterDict = getLabelGroup(wsDb)

    def getFilterMatch(self, FilterRow):
        """指定フィルターに合致するイベントを取得します / Gets events that match the specified filter.

        Args:
            FilterRow (_type_): フィルター

        Returns:
            boolean: True = 合致イベントあり / False = 合致イベントなし
            Optional[Union[List[ObjectId], ObjectId]]: ルールに利用する予定のイベント（合致しない0件=None / 複数件=List[ObjectId]）/ 検索方法がユニークだが複数合致した場合=[]
        """

        # フィルターに合致したイベントを返す

        # イベント検索用のパラメータ
        EventJudgList = []

        # 検索方法（1はユニーク、2はキューイング）
        search_condition_Id = FilterRow["SEARCH_CONDITION_ID"]

        if type(FilterRow["FILTER_CONDITION_JSON"]) is str:
            filter_condition_json = json.loads(FilterRow.get('FILTER_CONDITION_JSON'))
        else:
            filter_condition_json = FilterRow.get('FILTER_CONDITION_JSON')

        for LabelRow in filter_condition_json:
            # ラベル毎のループ
            LabelKeyId = str(LabelRow['label_name'])
            LabelValue = str(LabelRow['condition_value'])
            LabelCondition = str(LabelRow['condition_type'])
            # tmp_msg = g.appmsg.get_log_message("BKY-90041", [LabelKeyId, LabelValue, LabelCondition])
            # g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # ルールキーからルールラベル名を取得
            LabelKeyName = getIDtoLabelName(self.LabelMasterDict, LabelKeyId)

            # ラベリングされたイベントからデータを抜出す条件設定
            EventJudgList.append(self.makeEventJudgList(LabelKeyName, LabelValue, LabelCondition))

        ret, UsedEventIdList = self.EventJudge(EventJudgList)
        if search_condition_Id == '1' and ret is True and len(UsedEventIdList) > 1:
            # 検索方法がユニークでかつ複数件イベントが合致した時
            return True, []
        else:
            return ret, UsedEventIdList


    def EventJudge(self, EventJudgList):
        """指定のラベル条件に合致するイベントを返します / Returns events that match the specified label condition.

        Args:
            EventJudgList (list[dict]): ラベル条件

        Returns:
            boolean: True = 合致イベントあり / False = 合致イベントなし
            Optional[Union[List[ObjectId], ObjectId]]: 合致したイベント（0件=None / 1件=ObjectId / 2件以上=List[ObjectId]）
        """
        # イベント 検索　Searching for events JSON:{}
        tmp_msg = g.appmsg.get_log_message("BKY-90042", [str(EventJudgList)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        ret, UsedEventIdList = self.EventObj.find_events(EventJudgList)
        if len(UsedEventIdList) == 0:
            # 対象イベントなし
            tmp_msg = g.appmsg.get_log_message("BKY-90043", [str(UsedEventIdList)])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, None
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
            return True, UsedEventIdList

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
        TargetRuleIdList = []
        FilterList = []

        # g.applogger.debug(addline_msg('{}'.format("TargetRuleExtraction")))
        for RuleRow in RuleList:
            # g.applogger.debug('RULE_ID={}'.format(RuleRow['RULE_ID']))
            hit = True
            FilterList = []
            FilterList.append(RuleRow['FILTER_A'])
            if RuleRow.get('FILTER_B') is not None:
                FilterList.append(RuleRow['FILTER_B'])

            for FilterId in FilterList:
                if FilterId not in FiltersUsedinRulesDict:
                    # Target filter is not registered RULE_ID {} FILTER_ID {}>>
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
                    # g.applogger.debug('FilterId({})=Level2'.format(FilterId))
                    # で優先順位が最上位のルールか判定
                    if FiltersUsedinRulesDict[FilterId]['rule_id'] != RuleRow['RULE_ID']:
                        # g.applogger.debug('FilterId({})=Level2 hit=False'.format(FilterId))
                        hit = False

                # ルール抽出対象: 複数のルールで使用しているフィルタでタイムアウトを迎えるフィルタを使用しているルール※3の場合
                elif TargetLevel == "Level3":
                    if FilterId not in IncidentDict:
                        # Target event not found RULE_ID {} FILTER_ID {}>>
                        tmp_msg = g.appmsg.get_log_message("BKY-90047", [RuleRow['RULE_ID'], FilterId])
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                        hit = False
                        break
                    else:
                        if len(IncidentDict[FilterId]) == 0:
                            # イベント配列に空がセットされている場合（検索方法がユニークで複数合致した場合）
                            # 下のループは通らない
                            hit = False
                            break
                        for event_id in IncidentDict[FilterId]:
                            ret, EventRow = self.EventObj.get_events(event_id)

                            if ret is False:
                                # Failed to acquire target events RULE_ID:{} FILTER_ID:{} EventId:{}
                                # tmp_msg = g.appmsg.get_log_message("BKY-90049", [RuleRow['RULE_ID'], FilterId, IncidentDict[FilterId]])
                                # g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                hit = False
                            else:
                                if EventRow['labels']['_exastro_evaluated'] != '0' \
                                or EventRow['labels']['_exastro_timeout'] != '0' \
                                or EventRow['labels']['_exastro_undetected'] != '0':
                                    # 判定済みは無視
                                    # g.applogger.debug('FilterId({}), event_id({})=Level3 hit=False1'.format(FilterId, event_id))
                                    hit = False
                                    continue

                                if FilterId == RuleRow['FILTER_B'] and hit is True:
                                    # FILTER_Aのフィルタがタイムアウトを迎えていることを確認済み(hit = True)
                                    break

                                if FiltersUsedinRulesDict[FilterId]['rule_id'] in TargetRuleIdList:
                                    # 自分より優先順位の高いルールが、既に使われる予定
                                    # g.applogger.debug('FilterId({}), event_id({})=Level3 hit=False2'.format(FilterId, event_id))
                                    hit = False
                                    break

                                if EventRow[oaseConst.DF_LOCAL_LABLE_NAME][oaseConst.DF_LOCAL_LABLE_STATUS] != oaseConst.DF_POST_PROC_TIMEOUT_EVENT:
                                    # g.applogger.debug('FilterId({}), event_id({})=Level3 hit=False3'.format(FilterId, event_id))
                                    hit = False
                                else:
                                    hit = True
                                    # g.applogger.debug('FilterId({}), event_id({})=Level3 True'.format(FilterId, event_id))
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
                TargetRuleIdList.append(RuleRow['RULE_ID'])
                TargetRuleList.append(RuleRow)

        return TargetRuleList

    def RuleJudge(self, RuleRow, IncidentDict, actionIdList, filterIDMap):
        UseEventIdList = []

        # Rule verdict process started RULE_ID:{} RULE_NAME:{} FILTER_A:{} FILTER_OPERATOR:{} FILTER_B:{}
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
        Filter_AB_List = []
        Filter_AB_List.append(RuleRow['FILTER_A'])
        if RuleRow['FILTER_B'] is not None:
            Filter_AB_List.append(RuleRow['FILTER_B'])
        for FilterId in Filter_AB_List:
            tmp_msg = g.appmsg.get_log_message("BKY-90052", [FilterId])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            ret, EventRow = self.getFilterJudge(FilterId, IncidentDict, filterIDMap)

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

    def getFilterJudge(self, FilterId, IncidentDict, filterIDMap):
        # メモリーに保持しているIncidentDict[フィルターID:イベント]形式のリストの中から、これから判定に使うべきイベントを選ぶ
        # 判定につかうイベントは一つを想定している
        # 複数イベントがヒットしている場合はフィルターの「検索方法」項目を見て適切な値を返す。
        if FilterId not in IncidentDict:
            tmp_msg = g.appmsg.get_log_message("BKY-90058", [FilterId])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False, {}

        # 未評価のイベントを取得
        ret, EventRow = self.get_first_unevaluated_event(IncidentDict, FilterId)
        if ret is True:
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
                # or条件で両方のフィルターにマッチしていた場合は未知とするためIncidentDictから該当の要素を削除する
                remove_key_list = []
                for event in FilterResultDict['EventList']:
                    for key, value_list in IncidentDict.items():
                        if event["_id"] in value_list:
                            remove_key_list.append(key)

                for key in remove_key_list:
                    del IncidentDict[key]

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

    def ConclusionLabelUsedInFilter(self, ConclusionLablesDict, filterIDMap):
        UsedFilterIdList = []
        # ConclusionLablesDict = {'httpd': 'down', 'server': 'web01'}  # labelsプロパティの中身

        # Conclusion event Verdict JSON: {}
        tmp_msg = g.appmsg.get_log_message("BKY-90065", [str(ConclusionLablesDict)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        for FilterId, FilterRow in filterIDMap.items():
            ret = self.ConclusionFilterJudge(ConclusionLablesDict, FilterRow)
            if ret is True:
                # Filter matched FilterId: {}
                tmp_msg = g.appmsg.get_log_message("BKY-90063", [FilterId])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                UsedFilterIdList.append(FilterId)
            else:
                # Filter did not match FilterId: {}
                tmp_msg = g.appmsg.get_log_message("BKY-90064", [FilterId])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # マッチしたフィルタの数を判定
        if len(UsedFilterIdList) > 0:
            return True, UsedFilterIdList
        return False, UsedFilterIdList

    def ConclusionFilterJudge(self, ConclusionLablesDict, FilterRow):
        # ConclusionLablesDict = {'labels': {'httpd': 'down', 'server': 'web01'}}
        # FilterRow['FILTER_CONDITION_JSON'] = [{'key': 'c_01_name', 'condition': '0', 'value': 'c_01'}, {'key': 'c_02_name', 'condition': '0', 'value': 'c_02'}]

        if type(FilterRow["FILTER_CONDITION_JSON"]) is str:
            filter_condition_json = json.loads(FilterRow.get('FILTER_CONDITION_JSON'))
        else:
            filter_condition_json = FilterRow.get('FILTER_CONDITION_JSON')

        LabelHitCount = 0
        for LabelRow in filter_condition_json:
            LabelKeyName = getIDtoLabelName(self.LabelMasterDict, LabelRow['label_name'])
            LabelValue = LabelRow['condition_value']
            LabelCondition = str(LabelRow['condition_type'])
            # # FILTER_CONDITION_JSON FilterName:{} FilterValues:{} FilterCondition:{}
            # tmp_msg = g.appmsg.get_log_message("BKY-90066", [LabelKeyName, LabelValue, LabelCondition])
            # g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            LabelHit = False
            for cLabelKeyName, cLabelValue in ConclusionLablesDict.items():
                if (LabelKeyName == cLabelKeyName and LabelValue == cLabelValue and LabelCondition == oaseConst.DF_TEST_EQ) or\
                        (LabelKeyName == cLabelKeyName and LabelValue != cLabelValue and LabelCondition == oaseConst.DF_TEST_NE):
                    LabelHit = True
                    LabelHitCount += 1
                    # tmp_msg = g.appmsg.get_log_message("BKY-90067", [LabelKeyName, LabelValue])
                    # g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    break

            if LabelHit is True:
                pass
                # tmp_msg = g.appmsg.get_log_message("BKY-90068", []) # Label matched
                # g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            else:
                # tmp_msg = g.appmsg.get_log_message("BKY-90069", []) # Label did not match
                # g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                break

        if LabelHitCount != len(filter_condition_json):
            tmp_msg = g.appmsg.get_log_message("BKY-90070", [])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return False

        return True

    def get_first_unevaluated_event(self, IncidentDict, FilterId):
        """指定フィルターの最初の未評価イベントを返します / Returns the first unevaluated event for the specified filter

        Args:
            IncidentDict (_type_): _description_
            FilterId (_type_): _description_

        Returns:
            boolean: True=exists event, False=not exists event
            Optional[dict]: EventRow (not exists event=None)
        """
        if FilterId not in IncidentDict:
            return False, None

        # 複数件イベントが存在する時は、先頭から未評価のイベントを探して、未評価のイベントがイベントが見つかったら、それを返す
        # １件のイベントの場合、該当イベントが未評価イベントの場合、それを返す
        for event_id in IncidentDict[FilterId]:
            ret, EventRow = self.EventObj.get_events(event_id)
            if ret is True \
            and EventRow['labels']['_exastro_evaluated'] == '0' \
            and EventRow['labels']['_exastro_timeout'] == '0' \
            and EventRow['labels']['_exastro_undetected'] == '0':
                return True, EventRow

        # 未評価イベントが見つからなかった場合
        return False, None
