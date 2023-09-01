import csv
# ラベルマスタ
class T_EVRL_LABEL_KEY_CONCLUSION():
    def __init__(self, dbObj, filename):
        self.dbObj = dbObj
        self.LabelMasterDict = {}
        with open(filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.LabelMasterDict[str(row['LABEL_KEY_ID'])] = row['LABEL_KEY']

    def getIDtoName(self, uuid):
        uuid = str(uuid)
        if uuid not in self.LabelMasterDict:
            return False
        return self.LabelMasterDict[uuid]

#DBobj = ' '
#obj = T_EVRL_LABEL_KEY_CONCLUSION(DBobj, '../csv/T_EVRL_LABEL_KEY_CONCLUSION.csv')
#print(obj.getIDtoName("c_43"))
