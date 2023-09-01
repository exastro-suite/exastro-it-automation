import json
import csv

class T_EVRL_EVENT():
    def __init__(self, dbObj, filename):
        self.dbObj = dbObj
        self.filename = filename

    def findT_EVRL_EVENT(self, EventJudgList, JugeTime):
        EventList = []
        # DB find
        with open(self.filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                new_row = {}
                new_row["labels"] = {}
                new_row["exastro_labeling_settings_ids"] = {}
                new_row["exastro_label_key_input_ids"] = {}
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
                    elif key.find("exastro_label_key_input_ids") == 0:
                        for keylist in json.loads(value):
                            for labels_key,labels_val in keylist.items():
                                new_row["exastro_label_key_input_ids"][labels_key] = labels_val
                    elif key.find("exastro_labeling_settings_ids") == 0:
                        for keylist in json.loads(value):
                            for labels_key,labels_val in keylist.items():
                                new_row["exastro_labeling_settings_ids"][labels_key] = labels_val
                    else:
                        new_row[key] = value

                EventList.append(new_row)

            UsedEventList = []
            for EventRow in EventList:
                ##print("Input Event Data=============")
                ##print(EventRow['labels'])
                ##print(int(JugeTime))
                ##print(int(EventRow['labels']['_exastro_end_time']))
                if int(EventRow['labels']['_exastro_end_time']) < int(JugeTime):
                    print("timr ---")
                    break
                if str(EventRow['labels']['_exastro_evaluated']) != '0':
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
                    ## print("key:%s value:%s Condition:%s check " % ( Key, Value, Condition))
                    Hit = False
                    if Key in Lables:
                        ## print("Key ok")
                        if str(Condition) == '0':
                            if Lables[Key] == Value:
                                ## print("hit =")
                                Hit = True
                        else:
                            if Lables[Key] != Value:
                                ## print("hit !=")
                                Hit = True
                    JugeResultDict[str(Hit)] += 1
                    if Hit is False:
                       ## print("Not Key Value")
                       break

                ## print(JugeResultDict)
                if JugeResultDict['count'] == JugeResultDict['True']:
                    UsedEventList.append(EventRow)
                    ## print("Hit Key Value")

        return True, UsedEventList

    def setUsedT_EVRL_EVENT(self, Idlist):
        for id in Idlist:
            # update ["labels"]["_exastro_evaluated"] = "1"
            pass


#DBobj = ' '
#obj = T_EVRL_EVENT(DBobj, '../csv/T_EVRL_EVENT.csv')
#print(obj.findT_EVRL_EVENT())
