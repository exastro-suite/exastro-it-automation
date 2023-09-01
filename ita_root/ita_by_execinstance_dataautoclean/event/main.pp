import json
import sys
import time
from master.T_EVRL_EVENT                     import T_EVRL_EVENT
from master.T_EVRL_FILTER                    import T_EVRL_FILTER
from master.T_EVRL_LABEL_KEY_INPUT           import T_EVRL_LABEL_KEY_INPUT
from master.T_EVRL_RULE                      import T_EVRL_RULE

DF_TEST_EQ    = '0' # =
DF_TEST_NE    = '1' # !=
DF_OPE_NONE   = ''  # None
DF_OPE_OR     = '1' # OR
DF_OPE_AND    = '2' # AND
DF_OPE_ORDER  = '3' # ->

def stdin(msg):
    print("[stdin]" + msg)
    print("input key")
    str = input()

def TraceLog(msg):
    print("[Trace]" + str(msg))

def DebugLog(msg):
    ##print("[Debug]" + str(msg))
    pass

def ErrorLog(msg):
    print("[Error]" + str(msg))

class Judgement:
    def __init__(self, DBObj, LabelObj, FilterObj, EventObj):
        self.DBObj = DBObj
        self.LabelObj = LabelObj
        self.FilterObj = FilterObj
        self.EventObj = EventObj

    def FilterJuge(self, FilterRow, EexastroType):
        EventKey = ""
        UseEveventRows = ""
        EventJudgList = []

        for LabelRow in FilterRow["FILTER_CONDITION_JSON"]:
            # ラベル毎のループ
            LabelKey =  str(LabelRow['key'])
            LabelValue = str(LabelRow['value'])
            LabelCondition = str(LabelRow['condition'])
            DebugLog("<<LabelKey: %s>>" % (LabelKey))
            DebugLog("<<LabelValue: %s>>" % (LabelValue))
            DebugLog("<<LabelCondition: %s>>" % (LabelCondition))
            # ルールキーからルールラベル名を取得
            LabelName = self.LabelObj.getIDtoName(LabelKey)
            DebugLog("<<LabelName: %s>>" % (LabelName))

            # ラベリングされたイベントからデータを抜出す条件設定
            EventJudgList.append(self.makeEventJudgList(LabelName, LabelValue, LabelCondition))

        ##if EexastroType:
        ##    EventJudgList.append(self.makeEventJudgList("_exastro_type", EexastroType, '0'))
        
        ret ,UseEventIDList = self.EventJuge(EventJudgList)
        if ret is False:
            return False, []

        return True, UseEventIDList[0]

    def EventJuge(self, EventJudgList):
        # イベント管理 検索
        TraceLog("対象イベント検索 FILTER_JSON:%s" % (EventJudgList))
        ret, UsedEventIDList = self.EventObj.findT_EVRL_EVENT(EventJudgList)
        if len(UsedEventIDList) == 0:
            TraceLog("対象イベントなし FILTER_JSON:%s" % (EventJudgList))
            return False, ""
        if len(UsedEventIDList) == 1:
            return True, UsedEventIDList
        else:
            TraceLog("対象イベント 複数あり FILTER_JSON:%s" % (EventJudgList))
            return False, UsedEventIDList

    def makeEventJudgList(self, LabelName, LabelValue, LabelCondition):
        return {"LabelKey": LabelName , "LabelValue": LabelValue, "LabelCondition": LabelCondition}
        

    def RuleJuge(self, RuleRow, UseEventIdList, IncidentDict):

        if type(RuleRow["RULE_CONDITION_JSON"]) is str:
            RuleRow["RULE_CONDITION_JSON"] = json.loads(RuleRow["RULE_CONDITION_JSON"])
        TraceLog("==========================================================")
        TraceLog("ルール判定開始 RULE_ID:%s RULE_NAME:%s JSON:%s" % (RuleRow['RULE_ID'], RuleRow['RULE_NAME'], str(RuleRow["RULE_CONDITION_JSON"])))
        TraceLog("==========================================================")


        # ルール内のフィルタ条件判定用辞書初期化
        FilterResultDict = {}
        FilterResultDict['True'] = 0
        FilterResultDict['False'] = 0
        FilterResultDict['Count'] = 0
        FilterResultDict['EventList'] = []
        FilterResultDict['Operator'] = ''

        if not RuleRow["RULE_CONDITION_JSON"]['operator']:
            RuleRow["RULE_CONDITION_JSON"]['operator'] = ''

        FilterResultDict['Operator'] = str(RuleRow["RULE_CONDITION_JSON"]['operator'])

        # 論理演算子「operator」設定確認
        if self.checkRuleOperatorId(FilterResultDict['Operator']) is False:

            ErrorLog("ルール管理　論理演算子「operator」が不正 RULE_ID:%s RULE_NAME:%s JSON:%s" % (RuleRow['RULE_ID'], RuleRow['RULE_NAME'], str(RuleRow["RULE_CONDITION_JSON"])))

        # フィルタ毎のループ
        for FilterKey in RuleRow["RULE_CONDITION_JSON"]['filter_key']:

            TraceLog("フィルタ管理判定開始  FILTER_ID: %s" % (FilterKey))

            ret, EventRow = self.MemoryBaseFilterJuge(FilterKey, IncidentDict)

            if ret is True:
                FilterResultDict['EventList'].append(EventRow)
                
            # フィルタ件数 Up
            FilterResultDict['Count'] += 1

            # フィルタ判定結果退避
            FilterResultDict[str(ret)] += 1

            # フィルタ判定に使用したイベントID退避
            if ret is True:
                TraceLog("フィルタ判定結果　マッチ  FILTER_ID: %s" % (FilterKey))
            else:
                TraceLog("フィルタ判定結果　アンマッチ  FILTER_ID: %s" % (FilterKey))

        TraceLog("ルール内　フィルタ判定結果 %s" % (str(ret)))
        ret = self.checkFilterCondition(FilterResultDict)
        TraceLog("ルール管理判定結果 %s" % (str(ret)))
        if ret is False:
            return False
        for EventRow in FilterResultDict['EventList']:
            UseEventIdList.append(EventRow['_id'])
        return True

    def MemoryBaseFilterJuge(self, FilterKey, IncidentDict):

        if FilterKey not in IncidentDict:
            ErrorLog("イベント なし FILTER ID: %s" % (FilterKey))
            return False, {}

        ret, EventRow = self.EventObj.getT_EVRL_EVENT(IncidentDict[FilterKey])
        if ret is False:
            ErrorLog("イベント なし FILTER ID: %s" % (FilterKey))
            return False, {}

        if str(EventRow['labels']['_exastro_evaluated']) == '0':
            return True, EventRow
        else:
            ErrorLog("イベント 使用済み FILTER ID: %s" % (FilterKey))
            return False, {}


    def checkFilterCondition(self, FilterResultDict):
        if FilterResultDict['Operator'] == DF_OPE_OR:
            if FilterResultDict['True'] != 0:
                return True
        elif FilterResultDict['Operator'] == DF_OPE_AND:
            if FilterResultDict['False'] == 0:
                return True
        elif FilterResultDict['Operator'] == DF_OPE_ORDER:
            if FilterResultDict['False'] != 0:
                return False
            f_time = None
            if len(FilterResultDict['EventList']) > 1:
                for EventRow in FilterResultDict['EventList']:
                    if not f_time:
                        f_time = EventRow['labels']['_exastro_fetched_time']
                    else:
                        ## イベント発生順の確認
                        print("timr[0] %s time[1] %s" % (f_time,EventRow['labels']['_exastro_fetched_time']))
                        ## 発生順　A => B
                        if EventRow['labels']['_exastro_fetched_time'] > f_time:
                            return False
            return True
        else:
            if FilterResultDict['True'] != 0:
                return True
        return False

    def checkRuleOperatorId(self, Operator):
        if not Operator:
            return True
        if Operator in (DF_OPE_OR, DF_OPE_AND, DF_OPE_ORDER):
            return True
        return False

    def putRaccEvent(self, RuleRow, UseEventIdList):
        conclusion_ids = {}
        addlabels = {}
        labelsDict = json.loads(RuleRow["LABELING_INFORMATION"])
        for key, value in labelsDict.items():
            name = self.LabelObj.getIDtoName(key)
            if name is False:
                ErrorLog("ラベル結論マスタ 未登録 LABEL_KEY_ID:%s" % (key))
                return False, {}
            addlabels[name] = value
            conclusion_ids[name] = key

        RaccEventDict = {}

        t1 = int(time.time())
        ttl = int(RuleRow['REEVALUATE_TTL'])

        RaccEventDict["_id"] = t1  # 本来はinsert時の戻り値(uuid)を設定
        RaccEventDict["labels"] = {}
        RaccEventDict["labels"]["_exastro_event_collection_settings_id"] = ''
        RaccEventDict["labels"]["_exastro_fetched_time"] = t1
        RaccEventDict["labels"]["_exastro_end_time"] = t1 + ttl
        RaccEventDict["labels"]["_exastro_evaluated"] = "0"
        RaccEventDict["labels"]["_exastro_undetected"] = "0"
## __exastro_rule_execute_timeなに入れる
        RaccEventDict["labels"]["__exastro_rule_execute_time"] = "0"
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

        ## DBに結論イベント登録
        TraceLog("--------------------------------------")
        TraceLog("結論イベント登録")
        TraceLog(RaccEventDict)
        TraceLog("--------------------------------------")
        return True, RaccEventDict

    def ConclusionLabelUsedInFilter(self, FilterCheckLabelDict, FilterList):
        #FilterCheckLabelDict = {'i_11': 'down', 'i_100': 'ap11'}
        for FilterRow in FilterList:
            FilterKey = FilterRow["FILTER_ID"]
            ret = self.ConclusionFilterJuge(FilterCheckLabelDict, FilterRow)
            if ret is True:
                DebugLog("-----------------------")
                DebugLog("Filter Hit" + FilterKey)
                DebugLog("-----------------------")
                return True, FilterKey
            else:
                DebugLog("-----------------------")
                DebugLog("Filter Not Hit" + FilterKey)
                DebugLog("-----------------------")
        return False, FilterKey

    def ConclusionFilterJuge(self, FilterCheckLabelDict, FilterRow):
        #FilterRow['FILTER_CONDITION_JSON'] = [{'key': 'c_01_name', 'condition': '0', 'value': 'c_01'}, {'key': 'c_02_name', 'condition': '0', 'value': 'c_02'}]
        DebugLog("ConclusionFilterJuge ---------------------------------")
        DebugLog("in  " + str(FilterCheckLabelDict))
        DebugLog("in " + str(FilterRow['FILTER_CONDITION_JSON']))

        LabelHitCount = 0
        for FilterLabels in FilterRow['FILTER_CONDITION_JSON']:
            FilterName = FilterLabels['key']
            FilterValue = FilterLabels['value']
            FilterCondition = str(FilterLabels['condition'])
            DebugLog("Filter FilterName:%s FilterValues:%s FilterCondition:%s" % (FilterName,FilterValue,FilterCondition))
            LabelHit = False
            for LabelName, LabelValue in FilterCheckLabelDict.items():
                DebugLog("check LabelName:%s LabelValue:%s" % (LabelName,LabelValue))
                if (FilterName == LabelName and FilterValue == LabelValue and FilterCondition == '0') or\
                   (FilterName == LabelName and FilterValue != LabelValue and FilterCondition == '1'):
                    LabelHit = True
                    LabelHitCount += 1
                    DebugLog("hit LabelName:%s LabelValue:%s" % (LabelName,LabelValue))
                    break
            if LabelHit is True:
                pass
                DebugLog("total hit")
            else:
                DebugLog("total not hit")
                break
        DebugLog("LabelHitCount:" + str(LabelHitCount))
        DebugLog("FilterCheckLabelDict:" + str(len(FilterCheckLabelDict)))
        if LabelHitCount != len(FilterRow['FILTER_CONDITION_JSON']):
            DebugLog("Filter no hit")
            return False
        # 結論ラベル数＞フィルタラベル数の場合
        if LabelHitCount != len(FilterCheckLabelDict):
            return False
        DebugLog("Filter hit")
        return True
   
def JugeMain(DBObj, FromJugeTime, ToJugeTime):

    EventList = []
    JugeEventDict = {}
    IncidentDict = {}
    
    # ラベルマスタ取得(結論ラベルマスタも含む)
    DebugLog("ラベルマスタ取得")
## 単体テスト用
    LabelObj = T_EVRL_LABEL_KEY_INPUT(DBObj, 'csv/T_EVRL_LABEL_KEY_INPUT.csv')
#############################

    # フィルタ管理取得
    DebugLog("フィルタ管理取得")
## 単体テスト用
    FilterObj = T_EVRL_FILTER(DBObj, 'csv/T_EVRL_FILTER.csv')
    FilterList = FilterObj.getT_EVRL_FILTER()
    if len(FilterList) == 0:
        DebugLog("処理対象レコードなし。Table:T_EVRL_FILTER")
        return False
#############################

    # ルール管理取得
    DebugLog("ルール管理取得")
## 単体テスト用
    RuleObj = T_EVRL_RULE(DBObj, 'csv/T_EVRL_RULE.csv')
    RuleList = RuleObj.getT_EVRL_RULE()
    if len(RuleList) == 0:
        DebugLog("処理対象レコードなし。Table:T_EVRL_RULE")
        return False
#############################

    # イベントデータ取得
    DebugLog("イベントデータ取得 FromJugeTime:%s ToJugeTime:%s" % (FromJugeTime, ToJugeTime))
## 単体テスト用
    EventObj = T_EVRL_EVENT(DBObj, FromJugeTime, ToJugeTime, 'csv/T_EVRL_EVENT.csv')
    ret = EventObj.countT_EVRL_EVENT()
    if ret == 0:
        ErrorLog("対象イベントなし")
        return False
#############################

    JugeObj = Judgement(DBObj, LabelObj, FilterObj, EventObj)

    # フィルタリング
    newIncident = False
    for FilterRow in FilterList:
        FilterRow["FILTER_CONDITION_JSON"] = json.loads(FilterRow["FILTER_CONDITION_JSON"])
        FilterKey = FilterRow["FILTER_ID"]
        TraceLog("フィルタリング判定開始  FILTER_ID: %s" % (FilterKey))
        EexastroType = "event"
        ret, JugeEventID = JugeObj.FilterJuge(FilterRow, EexastroType)
        if ret is True:
            TraceLog("フィルタリング判定結果　マッチ  FILTER_ID: %s EVENT_ID: %s" % (FilterKey, JugeEventID))
            IncidentDict[FilterKey] = JugeEventID
            newIncident = True
        else:
            TraceLog("フィルタリング判定結果　アンマッチ  FILTER_ID: %s" % (FilterKey))

    while newIncident is True:
        print("loop in-----------------------")
        newIncident = False
        RuleJudgInfoList = []
        for RuleRow in RuleList:
            # ルール判定

            UseEventIdList = []
            ret = JugeObj.RuleJuge(RuleRow, UseEventIdList, IncidentDict)
            if ret is True:
                TraceLog("ルール判定 マッチ")
                
                ret, ConclusionEventRow = JugeObj.putRaccEvent(RuleRow, UseEventIdList)

                UpdateFlagDict = {"_exastro_evaluated": '1'}
                TraceLog("---------------------------------------------------------")
                TraceLog("イベント管理更新  %s ids:%s" % (str(UpdateFlagDict), str(UseEventIdList)))
                TraceLog("---------------------------------------------------------")
                EventObj.updateLablesFlagT_EVRL_EVENT(UseEventIdList, UpdateFlagDict)

                FilterCheckLabelDict = json.loads(RuleRow["LABELING_INFORMATION"])

                # 結論イベントに対応するフィルタがあるか確認
                ret, FilterKey = JugeObj.ConclusionLabelUsedInFilter(FilterCheckLabelDict, FilterList)
                TraceLog("---------------------------------------------------------")
                TraceLog("結論イベントに対応するフィルタがあるか確認 " + str(ret))
                TraceLog("---------------------------------------------------------")
                if ret is True:
                    TraceLog("結論イベントに対応するフィルタとイベント紐づけ登録  FILTER_ID: %s EVENT_ID: %s" % (FilterKey, ConclusionEventRow['_id']))
                    IncidentDict[FilterKey] = ConclusionEventRow['_id']

                    TraceLog("---------------------------------------------------------")
                    TraceLog("結論イベントをメモリに登録")
                    TraceLog(ConclusionEventRow)
                    TraceLog("---------------------------------------------------------")
                    EventObj.putT_EVRL_EVENT(ConclusionEventRow)
                    newIncident = True
            else:
                TraceLog("ルール判定 アンマッチ")
            stdin("ルール判定確認")
        if newIncident is True:
            print("----------------------------")
            print("Next------------------------")
            print("----------------------------")
            
        stdin('loop end') 
            ##sys.exit(1)

    EventObj.getUnuseEvent(IncidentDict)


def main():
    DBObj = "DB"

    SleepTime = 10

##  単体テスト用
##    ToJugeTime = int(time.time())
##    FromJugeTime = ToJugeTime - SleepTime
    ToJugeTime = 200001000000 
    FromJugeTime = 2000010100000
####################################

    while True:
        DebugLog("イベント抽出時間 FromTime %s ToTime %s" % (FromJugeTime, ToJugeTime))
        DebugLog("ルール判定開始")
        ret = JugeMain(DBObj, FromJugeTime, ToJugeTime)
        if ret is False:
            DebugLog("ルール判定異常")
    
        DebugLog("ルール判定完了")
## 単体テスト用
##        time.sleep(SleepTime)
##        FromJugeTime = ToJugeTime
##        ToJugeTime = int(time.time())

        ToJugeTime = 200001000000 #int(time.time())
        FromJugeTime = 2000010100000
        break
####################################

main()
