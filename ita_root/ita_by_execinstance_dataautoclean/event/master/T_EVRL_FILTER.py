import json
import csv

filter_json = {}
filter_json['f_01'] = [{'key': 'i_01', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap01'}]
filter_json['f_02'] = [{'key': 'i_02', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap02'}]
filter_json['f_03'] = [{'key': 'i_03', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap03'}]
filter_json['f_04'] = [{'key': 'i_04', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap04'}]
filter_json['f_05'] = [{'key': 'i_05', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap05'}]
filter_json['f_06'] = [{'key': 'i_06', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap06'}]
filter_json['f_07'] = [{'key': 'i_07', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap07'}]
filter_json['f_08'] = [{'key': 'i_08', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap08'}]
filter_json['f_09'] = [{'key': 'i_09', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap09'}]
filter_json['f_10'] = [{'key': 'i_10', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap10'}]
filter_json['f_11'] = [{'key': 'i_11', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap11'}]
filter_json['f_12'] = [{'key': 'i_12', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap12'}]
filter_json['f_13'] = [{'key': 'i_13', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap13'}]
filter_json['f_14'] = [{'key': 'i_14', 'condition': '0', 'value': 'down'}, {'key': 'i_100', 'condition': '0', 'value': 'ap14'}]

filter_json['f_51'] = [{'key': 'c_01', 'condition': '0', 'value': 'C_01_status'}, {'key': 'c_02', 'condition': '0', 'value': 'C_02_status'}]
filter_json['f_52'] = [{'key': 'c_03', 'condition': '0', 'value': 'C_03_status'}, {'key': 'c_04', 'condition': '0', 'value': 'C_04_status'}]
filter_json['f_53'] = [{'key': 'c_05', 'condition': '0', 'value': 'C_05_status'}, {'key': 'c_06', 'condition': '0', 'value': 'C_06_status'}]
filter_json['f_54'] = [{'key': 'c_07', 'condition': '0', 'value': 'C_07_status'}, {'key': 'c_08', 'condition': '0', 'value': 'C_08_status'}]
filter_json['f_55'] = [{'key': 'c_09', 'condition': '0', 'value': 'C_09_status'}, {'key': 'c_10', 'condition': '0', 'value': 'C_10_status'}]
filter_json['f_56'] = [{'key': 'c_11', 'condition': '0', 'value': 'C_11_status'}, {'key': 'c_12', 'condition': '0', 'value': 'C_12_status'}]
filter_json['f_57'] = [{'key': 'c_13', 'condition': '0', 'value': 'C_13_status'}, {'key': 'c_14', 'condition': '0', 'value': 'C_14_status'}]
filter_json['f_58'] = [{'key': 'c_15', 'condition': '0', 'value': 'C_15_status'}, {'key': 'c_16', 'condition': '0', 'value': 'C_16_status'}]
class T_EVRL_FILTER():
    def __init__(self, dbObj, filename):
        self.dbObj = dbObj
        self.RuleManagementList = []
        self.m_value = 'down'
        self.h_value = 'sv01'
        with open(filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row["FILTER_CONDITION_JSON"] = json.dumps(filter_json[row["FILTER_CONDITION_JSON"]])
                self.RuleManagementList.append(row)
        print(self.RuleManagementList)

    def findT_EVRL_FILTER(self, FilterKey):
        FilterList = self.getT_EVRL_FILTER()
        for row in FilterList:
            if row['FILTER_ID'] == FilterKey:
                return row
        return False

    def getT_EVRL_FILTER(self):
        return  self.RuleManagementList

#DBobj = ' '
#obj = T_EVRL_FILTER(DBobj, '../csv/T_EVRL_FILTER.csv')
#print(obj.findT_EVRL_FILTER("f_01"))
