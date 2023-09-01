import json
import csv

class T_EVRL_EVENT():
    def __init__(self, dbObj, FromJugeTime, ToJugeTime, filename):
        self.dbObj = dbObj
        self.filename = filename
        self.EventDict = {}

# DB find
#               TTL          Now
#                |            |
#3 ●:     f------------------------e
#1 ●:     f-----------e
#2 ●:                 f------------e
#1 ●:             f--------e
#  ×:     f--e
#  ×:                           f--e
#
#Now: インシデント判定開始時間
#TTL: Now - (イベント:_exastro_end_time - _exastro_end_time)
#f  : _exastro_fetched_time
#e  : _exastro_end_time
#
# find 1: (TTL <= _exastro_end_time <= Now) or
#      2: (TTL <= _exastro_fetched_time <= Now) and (Now <= _exastro_end_time) or
#      3: (_exastro_fetched_time <= TTL) and  (Now <= _exastro_end_time)

        ## 単体テスト用
        with open(self.filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # From - Toの時間判定はDB検索条件なのでチェックはしない
                new_row = {}
                new_row["labels"] = {}
                new_row["exastro_labeling_settings"] = {}
                new_row["exastro_label_key_inputs"] = {}
                for key, value in row.items():
                    if key.find("labels.") == 0:
                        if "labels" not in new_row:
                            new_row["labels"] = {}
                        key = key.replace("labels.","")
                        if key == "array":
                            for keylist in json.loads(value):
                                for labels_key,labels_val in keylist.items():
                                    new_row["labels"][labels_key] = labels_val
                        else:
                            new_row["labels"][key] = value
                    elif key.find("exastro_label_key_inputs") == 0:
                        for keylist in json.loads(value):
                            for labels_key,labels_val in keylist.items():
                                new_row["exastro_label_key_inputs"][labels_key] = labels_val
                    elif key.find("exastro_labeling_settings") == 0:
                        for keylist in json.loads(value):
                            for labels_key,labels_val in keylist.items():
                                new_row["exastro_labeling_settings"][labels_key] = labels_val
                    else:
                        new_row[key] = value
                self.EventDict[new_row['_id']] = new_row

    def findT_EVRL_EVENT(self, EventJudgList):
        DebugMode = False  ## 単体テスト用
        UsedEventIDList = []
        for EventKey, EventRow in self.EventDict.items():
            self.DebugLog(DebugMode, str(EventRow))  ## 単体テスト用
            if str(EventRow['labels']['_exastro_evaluated']) != '0':
                self.DebugLog(DebugMode, "_exastro_evaluated not 0") ## 単体テスト用
                break
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
                self.DebugLog(DebugMode, "key:%s value:%s Condition:%s check " % ( Key, Value, Condition)) ## 単体テスト用
                Hit = False
                if Key in Lables:
                    self.DebugLog(DebugMode, "Key ok")  ## 単体テスト用
                    if str(Condition) == '0':
                        if Lables[Key] == Value:
                            self.DebugLog(DebugMode, "hit =")  ## 単体テスト用
                            Hit = True
                    else:
                        if Lables[Key] != Value:
                            self.DebugLog(DebugMode, "hit !=")  ## 単体テスト用
                            Hit = True
                JugeResultDict[str(Hit)] += 1
                if Hit is False:
                    self.DebugLog(DebugMode, "Not Key Value")  ## 単体テスト用
                    break

            self.DebugLog(DebugMode, JugeResultDict)  ## 単体テスト用
            if JugeResultDict['count'] == JugeResultDict['True']:
                UsedEventIDList.append(EventRow['_id'])
                self.DebugLog(DebugMode, "Hit Key Value")  ## 単体テスト用

        return True, UsedEventIDList

    def countT_EVRL_EVENT(self):
        return(len(self.EventDict))

    def putT_EVRL_EVENT(self, EventRow):
        self.EventDict[EventRow['_id']] = EventRow

    def getT_EVRL_EVENT(self, EventID):
        if EventID not in self.EventDict:
            return False, {}
        return True, self.EventDict[EventID]

    def updateLablesFlagT_EVRL_EVENT(self, EventIdlist, UpdateFlagDict):
        DebugMode = True   ## 単体テスト用
        for EventID in EventIdlist:
            if EventID not in  self.EventDict:
                self.ErrorLog(DebugMode, "イベント未登録 EventID = %s" % (EventID))  ## 単体テスト用
                return False
            self.DebugLog(DebugMode, "更新前:" + str(self.EventDict[EventID])) ## 単体テスト用
            for Key, Value in UpdateFlagDict.items():
                self.EventDict[EventID]['labels'][Key] = Value

                ### DB Updateを追加
                print(DebugMode, "DB Updateを追加")   ## 単体テスト用

            self.DebugLog(DebugMode, "更新後:" + str(self.EventDict[EventID])) ## 単体テスト用
        return True

    def getUnuseEvent(self, IncidentDict):
        UnusedEventIDList = []
        for EventKey, EventRow in self.EventDict.items():
            if str(EventRow['labels']['_exastro_evaluated']) == '0':
                UnusedEventIDList.append(EventRow['_id'])
        print(UnusedEventIDList)
        for FilterKey, EventID in IncidentDict.items():
            if UnusedEventIDList.count(EventID) == 0:
                print(EventID)

# 単体テスト用
    def DebugLog(self, DebugMode, log):
        if DebugMode is True:
            print("[Debug]" + str(log))
    def ErrorLog(self, log):
        print("[Error]" + str(log))

#DBobj = ' '
#obj = T_EVRL_EVENT(DBobj, 100, 200, '../csv/T_EVRL_EVENT.csv')
#print(obj.findT_EVRL_EVENT())
