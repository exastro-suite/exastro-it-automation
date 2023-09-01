import json
import csv
class T_EVRL_RULE():
    def __init__(self, dbObj, filename):
        self.dbObj = dbObj
        self.RuleManagementList = []
        with open(filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["RULE_CONDITION_JSON"]   == "csv/rule01_json":
                    json,ljson = self.rule01_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule02_json":
                    json,ljson = self.rule02_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule03_json":
                    json,ljson = self.rule03_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule04_json":
                    json,ljson = self.rule04_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule05_json":
                    json,ljson = self.rule05_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule06_json":
                    json,ljson = self.rule06_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule07_json":
                    json,ljson = self.rule07_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule08_json":
                    json,ljson = self.rule08_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule09_json":
                    json,ljson = self.rule09_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule10_json":
                    json,ljson = self.rule10_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule11_json":
                    json,ljson = self.rule11_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule12_json":
                    json,ljson = self.rule12_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule13_json":
                    json,ljson = self.rule13_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule14_json":
                    json,ljson = self.rule14_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule15_json":
                    json,ljson = self.rule15_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule16_json":
                    json,ljson = self.rule16_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule17_json":
                    json,ljson = self.rule17_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule18_json":
                    json,ljson = self.rule18_json(row["RULE_CONDITION_JSON"])
                elif row["RULE_CONDITION_JSON"] == "csv/rule19_json":
                    json,ljson = self.rule19_json(row["RULE_CONDITION_JSON"])
                else:
                    pass
                    # データエラー
                row["RULE_CONDITION_JSON"] = json
                row["LABELING_INFORMATION"] = ljson
                self.RuleManagementList.append(row)

    def getT_EVRL_RULE(self):
        return  self.RuleManagementList

    def rule01_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = ""
        condition['filter_key'] = ["f_01"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_01'] = 'C_01_status'
        lables['c_02'] = 'C_02_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule02_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_01", "f_02"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_03'] = 'C_03_status'
        lables['c_04'] = 'C_04_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule03_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_03", "f_04"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_05'] = 'C_05_status'
        lables['c_06'] = 'C_06_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule04_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = ""  #0: or 1 :and
        condition['filter_key'] = ["f_05"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '0'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_06", "f_07"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_07'] = 'C_07_status'
        lables['c_08'] = 'C_08_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule05_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = ""  #0: or 1 :and
        condition['filter_key'] = ["f_08"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '0'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_09", "f_10"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_09'] = 'C_09_status'
        lables['c_10'] = 'C_10_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule06_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = ""  #0: or 1 :and
        condition['filter_key'] = ["f_11"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '1'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_12", "f_13"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_11'] = 'C_11_status'
        lables['c_12'] = 'C_12_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule07_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = ""  #0: or 1 :and
        condition['filter_key'] = ["f_14"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '1'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_15", "f_16"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_13'] = 'C_13_status'
        lables['c_14'] = 'C_14_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule08_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_17","f_18"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '0'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = ""  #0: or 1 :and
        condition['filter_key'] = ["f_19"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_15'] = 'C_15_status'
        lables['c_16'] = 'C_16_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule09_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_20","f_21"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '0'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = ""  #0: or 1 :and
        condition['filter_key'] = ["f_22"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_17'] = 'C_17_status'
        lables['c_18'] = 'C_18_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule10_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_23","f_24"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '1'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = ""  #0: or 1 :and
        condition['filter_key'] = ["f_25"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_19'] = 'C_19_status'
        lables['c_20'] = 'C_20_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule11_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_26","f_27"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '1'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = ""  #0: or 1 :and
        condition['filter_key'] = ["f_28"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_21'] = 'C_21_status'
        lables['c_22'] = 'C_22_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule12_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_29","f_30"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '0'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_31","f_32"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_23'] = 'C_23_status'
        lables['c_24'] = 'C_24_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule13_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_33","f_34"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '0'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_35","f_36"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_25'] = 'C_25_status'
        lables['c_26'] = 'C_26_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule14_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_37","f_38"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '1'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_39","f_40"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_27'] = 'C_27_status'
        lables['c_28'] = 'C_28_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule15_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_41","f_42"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '1'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_43","f_44"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_29'] = 'C_29_status'
        lables['c_30'] = 'C_30_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule16_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_45","f_46"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '0'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_47","f_48"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_31'] = 'C_31_status'
        lables['c_32'] = 'C_32_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule17_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_49","f_50"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '0'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_51","f_52"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_33'] = 'C_33_status'
        lables['c_34'] = 'C_34_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr

    def rule18_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_53","f_54"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '1'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_55","f_56"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_35'] = 'C_35_status'
        lables['c_36'] = 'C_36_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr


    def rule19_json(self, name):
        ConditionsList= []

        # G001
        group = {}
        group['operator']  =  ''

        # G001-001
        condition = {}
        condition['operator'] = "1"  #0: or 1 :and
        condition['filter_key'] = ["f_57","f_58"]

        # G001-add
        group['group'] = [condition]
        ConditionsList.append(group)

        # G002
        group = {}
        group['operator']  =  '1'  #0: or 1 :and

        # G002-001
        condition = {}
        condition['operator'] = "0"  #0: or 1 :and
        condition['filter_key'] = ["f_59","f_60"]

        # G002-add
        group['group'] = [condition]
        ConditionsList.append(group)

        jsonStr =  json.dumps(ConditionsList)

        lables = {}
        lables['c_37'] = 'C_37_status'
        lables['c_38'] = 'C_38_status'
        LjsonStr =  json.dumps(lables)
        return jsonStr, LjsonStr


#DBobj = ' '
#obj = T_EVRL_RULE(DBobj, '../csv/T_EVRL_RULE.csv')
#print(obj.getT_EVRL_RULE())
