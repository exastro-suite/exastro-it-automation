import json
import csv
class T_EVRL_EVENT():
    def __init__(self, dbObj, filename):
        self.dbObj = dbObj
        self.EventList = []
        with open(filename, newline='') as csvfile:
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
                    if key.find("exastro_label_key_input_ids") == 0:
                        for keylist in json.loads(value):
                            for labels_key,labels_val in keylist.items():
                                new_row["exastro_label_key_input_ids"][labels_key] = labels_val
                    if key.find("exastro_labeling_settings_ids") == 0:
                        for keylist in json.loads(value):
                            for labels_key,labels_val in keylist.items():
                                new_row["exastro_labeling_settings_ids"][labels_key] = labels_val
                    else:
                        new_row[key] = value

                self.EventList.append(new_row)

    def getT_EVRL_EVENT(self):
        return  self.EventList
    def setUsedT_EVRL_EVENT(self, Idlist):
        for id in Idlist:
            # update ["labels"]["_exastro_evaluated"] = "1"
            pass


#DBobj = ' '
#obj = T_EVRL_EVENT(DBobj, '../csv/T_EVRL_EVENT.csv')
#print(obj.getT_EVRL_EVENT())
