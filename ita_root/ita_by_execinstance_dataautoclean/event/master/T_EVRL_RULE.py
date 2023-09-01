import json
import csv
rule_json = {}
rule_json['r_01'] = {'operator': "", 'filter_key': ["f_01"]}
rule_json['r_02'] = {'operator': "1", 'filter_key': ["f_02","f_03"]}
rule_json['r_03'] = {'operator': "2", 'filter_key': ["f_04","f_05"]}
rule_json['r_04'] = {'operator': "3", 'filter_key': ["f_06","f_07"]}
rule_json['r_05'] = {'operator': "", 'filter_key': ["f_08"]}
rule_json['r_06'] = {'operator': "1", 'filter_key': ["f_09","f_10"]}
rule_json['r_07'] = {'operator': "2", 'filter_key': ["f_11","f_12"]}
rule_json['r_08'] = {'operator': "3", 'filter_key': ["f_13","f_14"]}
rule_json['r_51'] = {'operator': "", 'filter_key': ["f_51"]}
rule_json['r_52'] = {'operator': "1", 'filter_key': ["f_52","f_53"]}
rule_json['r_53'] = {'operator': "2", 'filter_key': ["f_54","f_55"]}
rule_json['r_54'] = {'operator': "3", 'filter_key': ["f_56","f_57"]}

lable_json = {}
lable_json['r_01'] = {"c_01": "C_01_status", "c_02": "C_02_status"}
lable_json['r_02'] = {"c_03": "C_03_status", "c_04": "C_04_status"}
lable_json['r_03'] = {"c_05": "C_05_status", "c_06": "C_06_status"}
lable_json['r_04'] = {"c_07": "C_07_status", "c_08": "C_08_status"}
lable_json['r_05'] = {"c_09": "C_09_status", "c_10": "C_10_status"}
lable_json['r_06'] = {"c_11": "C_11_status", "c_12": "C_12_status"}
lable_json['r_07'] = {"c_13": "C_13_status", "c_14": "C_14_status"}
lable_json['r_08'] = {"c_15": "C_15_status", "c_16": "C_16_status"}
lable_json['r_51'] = {"c_21": "C_21_status", "c_22": "C_22_status"}
lable_json['r_52'] = {"c_23": "C_23_status", "c_24": "C_24_status"}
lable_json['r_53'] = {"c_25": "C_25_status", "c_26": "C_26_status"}
lable_json['r_54'] = {"c_27": "C_27_status", "c_28": "C_28_status"}

class T_EVRL_RULE():
    def __init__(self, dbObj, filename):
        self.dbObj = dbObj
        self.RuleManagementList = []
        with open(filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row["RULE_CONDITION_JSON"] = json.dumps(rule_json[row["RULE_CONDITION_JSON"]])
                row["LABELING_INFORMATION"] = json.dumps(lable_json[row['LABELING_INFORMATION']])
                self.RuleManagementList.append(row)

    def getT_EVRL_RULE(self):
        return  self.RuleManagementList

#DBobj = ' '
#obj = T_EVRL_RULE(DBobj, '../csv/T_EVRL_RULE.csv')
#print(obj.getT_EVRL_RULE())
