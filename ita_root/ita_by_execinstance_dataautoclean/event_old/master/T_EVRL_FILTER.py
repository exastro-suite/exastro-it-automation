import json
import csv
class T_EVRL_FILTER():
    def __init__(self, dbObj, filename):
        self.dbObj = dbObj
        self.RuleManagementList = []
        self.m_value = 'down'
        self.h_value = 'sv01'
        with open(filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["FILTER_CONDITION_JSON"] == "csv/filter01_json":
                    json = self.rule01_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter02_json":
                    json = self.rule02_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter03_json":
                    json = self.rule03_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter04_json":
                    json = self.rule04_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter05_json":
                    json = self.rule05_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter06_json":
                    json = self.rule06_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter07_json":
                    json = self.rule07_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter08_json":
                    json = self.rule08_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter09_json":
                    json = self.rule09_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter10_json":
                    json = self.rule10_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter11_json":
                    json = self.rule11_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter12_json":
                    json = self.rule12_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter13_json":
                    json = self.rule13_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter14_json":
                    json = self.rule14_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter15_json":
                    json = self.rule15_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter16_json":
                    json = self.rule16_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter17_json":
                    json = self.rule17_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter18_json":
                    json = self.rule18_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter19_json":
                    json = self.rule19_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter20_json":
                    json = self.rule20_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter21_json":
                    json = self.rule21_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter22_json":
                    json = self.rule22_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter23_json":
                    json = self.rule23_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter24_json":
                    json = self.rule24_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter25_json":
                    json = self.rule25_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter26_json":
                    json = self.rule26_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter27_json":
                    json = self.rule27_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter28_json":
                    json = self.rule28_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter29_json":
                    json = self.rule29_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter30_json":
                    json = self.rule30_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter31_json":
                    json = self.rule31_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter32_json":
                    json = self.rule32_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter33_json":
                    json = self.rule33_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter34_json":
                    json = self.rule34_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter35_json":
                    json = self.rule35_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter36_json":
                    json = self.rule36_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter37_json":
                    json = self.rule37_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter38_json":
                    json = self.rule38_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter39_json":
                    json = self.rule39_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter40_json":
                    json = self.rule40_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter41_json":
                    json = self.rule41_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter42_json":
                    json = self.rule42_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter43_json":
                    json = self.rule43_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter44_json":
                    json = self.rule44_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter45_json":
                    json = self.rule45_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter46_json":
                    json = self.rule46_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter47_json":
                    json = self.rule47_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter48_json":
                    json = self.rule48_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter49_json":
                    json = self.rule49_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter50_json":
                    json = self.rule50_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter51_json":
                    json = self.rule51_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter52_json":
                    json = self.rule52_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter53_json":
                    json = self.rule53_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter54_json":
                    json = self.rule54_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter55_json":
                    json = self.rule55_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter56_json":
                    json = self.rule56_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter57_json":
                    json = self.rule57_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter58_json":
                    json = self.rule58_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter59_json":
                    json = self.rule59_json(row["FILTER_CONDITION_JSON"])
                elif row["FILTER_CONDITION_JSON"] == "csv/filter60_json":
                    json = self.rule60_json(row["FILTER_CONDITION_JSON"])
                else:
                    pass
                    # データエラー
                row["FILTER_CONDITION_JSON"] = json
                self.RuleManagementList.append(row)

    def findT_EVRL_FILTER(self, FilterKey):
        FilterList = self.getT_EVRL_FILTER()
        for row in FilterList:
            if row['FILTER_ID'] == FilterKey:
                return row
        return False

    def getT_EVRL_FILTER(self):
        return  self.RuleManagementList

    def rule01_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        m_key = 'i_01'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr
    def rule02_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = 0   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_01'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-002
        h_key = 'i_100'
        m_key = 'i_02'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr
    def rule03_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = 1   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_03'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-002
        h_key = 'i_100'
        m_key = 'i_04'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr
    def rule04_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_05'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_06'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-002
        h_key = 'i_100'
        m_key = 'i_07'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-add
        rules = {'operator': '0', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr
    def rule05_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_08'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_09'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G002-002
        h_key = 'i_100'
        m_key = 'i_10'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G002-add
        rules = {'operator': '0', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr
    def rule06_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_11'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_12'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G002-002
        h_key = 'i_100'
        m_key = 'i_13'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G002-add
        rules = {'operator': '0', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule07_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_14'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_15'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-002
        h_key = 'i_100'
        m_key = 'i_16'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-add
        rules = {'operator': '1', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr
    def rule08_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_17'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_18'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '0', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_19'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G002-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr
    def rule09_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_20'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_21'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_22'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G002-add
        rules = {'operator': '0', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule10_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_23'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_24'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_25'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G002-add
        rules = {'operator': '1', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule11_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_26'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_27'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_28'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G002-add
        rules = {'operator': '1', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule12_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_29'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_30'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_31'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-001
        h_key = 'i_100'
        m_key = 'i_32'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-add
        rules = {'operator': '0', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)


        return jsonStr

    def rule13_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_33'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_34'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_35'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-001
        h_key = 'i_100'
        m_key = 'i_36'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-add
        rules = {'operator': '0', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule14_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_37'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_38'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_39'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-001
        h_key = 'i_100'
        m_key = 'i_40'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-add
        rules = {'operator': '1', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule15_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_41'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_42'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_43'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-001
        h_key = 'i_100'
        m_key = 'i_44'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-add
        rules = {'operator': '1', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule16_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_45'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_46'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_47'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-001
        h_key = 'i_100'
        m_key = 'i_48'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-add
        rules = {'operator': '0', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule17_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_49'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_50'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_51'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-001
        h_key = 'i_100'
        m_key = 'i_51'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-add
        rules = {'operator': '0', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule18_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_53'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_54'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_55'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-001
        h_key = 'i_100'
        m_key = 'i_56'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-add
        rules = {'operator': '1', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule19_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = '1'   # 0: or 1: and
        rule_group['rules'] = []

        # G001-001
        h_key = 'i_100'
        m_key = 'i_57'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G001-008
        h_key = 'i_100'
        m_key = 'i_58'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList= []
        ConditionsList.append(rules)

        # G002
        rule_group = {}
        rule_group['operator'] = '0'   # 0: or 1: and
        rule_group['rules'] = []

        # G002-001
        h_key = 'i_100'
        m_key = 'i_59'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-001
        h_key = 'i_100'
        m_key = 'i_60'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)

        # G002-add
        rules = {'operator': '1', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule20_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        m_key = 'i_61'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule21_json(self, name):
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        m_key = 'i_62'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule22_json(self, name):
        m_key = 'i_63'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        m_key = 'i_63'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule23_json(self, name):
        m_key = 'i_64'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule24_json(self, name):
        m_key = 'i_65'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule25_json(self, name):
        m_key = 'i_66'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule26_json(self, name):
        m_key = 'i_67'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule27_json(self, name):
        m_key = 'i_68'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule28_json(self, name):
        m_key = 'i_69'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule29_json(self, name):
        m_key = 'i_70'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule30_json(self, name):
        m_key = 'i_71'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule31_json(self, name):
        m_key = 'i_72'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule32_json(self, name):
        m_key = 'i_73'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule33_json(self, name):
        m_key = 'i_74'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule34_json(self, name):
        m_key = 'i_75'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule35_json(self, name):
        m_key = 'i_76'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule36_json(self, name):
        m_key = 'i_77'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule37_json(self, name):
        m_key = 'i_78'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule38_json(self, name):
        m_key = 'i_79'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule39_json(self, name):
        m_key = 'i_80'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule40_json(self, name):
        m_key = 'i_81'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule41_json(self, name):
        m_key = 'i_82'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule42_json(self, name):
        m_key = 'i_83'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule42_json(self, name):
        m_key = 'i_83'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule43_json(self, name):
        m_key = 'i_84'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule43_json(self, name):
        m_key = 'i_84'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule43_json(self, name):
        m_key = 'i_84'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule44_json(self, name):
        m_key = 'i_85'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule45_json(self, name):
        m_key = 'i_86'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule46_json(self, name):
        m_key = 'i_87'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule47_json(self, name):
        m_key = 'i_88'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule48_json(self, name):
        m_key = 'i_89'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule49_json(self, name):
        m_key = 'i_90'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule50_json(self, name):
        m_key = 'i_91'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule51_json(self, name):
        m_key = 'i_92'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule52_json(self, name):
        m_key = 'i_93'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule53_json(self, name):
        m_key = 'i_94'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule54_json(self, name):
        m_key = 'i_95'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule55_json(self, name):
        m_key = 'i_96'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule56_json(self, name):
        m_key = 'i_97'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule57_json(self, name):
        m_key = 'i_98'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule58_json(self, name):
        m_key = 'i_99'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule59_json(self, name):
        m_key = 'i_200'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

    def rule60_json(self, name):
        m_key = 'i_201'
        ConditionsList= []
        # G001
        rule_group = {}
        rule_group['operator'] = ''   # 0: or 1: and
        rule_group['rules'] = []
        # G001-001
        h_key = 'i_100'
        condition = {'key': m_key, 'value': self.m_value, 'condition': '0', 'options': []}
        option = {'key': h_key, 'value': self.h_value, 'condition': '0'}
        condition['options'].append(option)
        rule_group['rules'].append(condition)
        # G001-add
        rules = {'operator': '', 'group': [rule_group]}
        ConditionsList.append(rules)

        jsonStr =  json.dumps(ConditionsList)

        return jsonStr

#DBobj = ' '
#obj = T_EVRL_FILTER(DBobj, '../csv/T_EVRL_FILTER.csv')
#print(obj.findT_EVRL_FILTER("f_60"))
