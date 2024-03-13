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
import inspect
import os

import json
import datetime
from jinja2 import Template

from common_libs.oase.const import oaseConst

def addline_msg(msg=''):
    info = inspect.getouterframes(inspect.currentframe())[1]
    msg_line = "{} ({}:{})".format(msg, os.path.basename(info.filename), info.lineno)
    return msg_line

# def UserIDtoUserName(objdbca, UserId):
#     UserName = ""
#     UserEnv = g.LANGUAGE.upper()
#     UserNameCol = "USER_NAME_{}".format(UserEnv)
#     TableName = "T_COMN_BACKYARD_USER"
#     WhereStr = "WHERE USER_ID = '%s' AND DISUSE_FLAG='0'" % (UserId)

#     Rows = objdbca.table_select(TableName, WhereStr, [])
#     for Row in Rows:
#         UserName = Row[UserNameCol]
#     return UserName

def generateConclusionLables(wsDb, wsMongo, UseEventIdList, ruleRow):
    # アクションに利用 & 結論イベントに付与 するラベルを生成する
    conclusion_lables = {"labels": {}}

    # フィルターA, Bそれぞれに対応するイベント取得_exastroを含むラベルを除外
    labeled_event_collection = wsMongo.collection("labeled_event_collection")
    event_A = labeled_event_collection.find_one({"_id": UseEventIdList[0]})
    event_B = labeled_event_collection.find_one({"_id": UseEventIdList[1]})
    # _exastroを含むラベルを除外
    event_A_labels = {key: value for key, value in event_A["labels"].items() if "_exastro" not in key}
    event_B_labels = {key: value for key, value in event_B["labels"].items() if "_exastro" not in key}
    # jinja2テンプレート参照用
    event_A_reference = event_A_labels.copy()
    event_B_reference = event_B_labels.copy()


    # A, Bそれぞれkeyの部分をidに変換
    for name, id in event_A["exastro_label_key_inputs"].items():
        event_A_labels[id] = event_A_labels.pop(name)
    for name, id in event_B["exastro_label_key_inputs"].items():
        event_B_labels[id] = event_B_labels.pop(name)

    # ラベルのマージ
    merged_labels = event_B_labels

    # Aのラベルを優先して上書き
    for label in event_A_labels:
        merged_labels[label] = event_A_labels[label]

    conc_label_settings = ruleRow["CONCLUSION_LABEL_SETTINGS"]  # LIST
    for setting in conc_label_settings:

        # label_valueに変数ブロックが含まれている場合、jinja2テンプレートで値を変換
        template = Template(setting["label_value"])
        label_value = template.render(A=event_A_reference, B=event_B_reference)
        merged_labels[setting["label_key"]] = label_value

    conclusion_lables["labels"] = merged_labels

    return conclusion_lables


def InsertConclusionEvent(EventObj, LabelMaster, RuleInfo, UseEventIdList, ConclusionLables):
    # 結論イベント登録
    label_key_inputs = {}
    addlabels = {}

    # 結論ラベル
    for label_key, label_name in json.loads(ConclusionLables).items():
        key = getIDtoLabelName(LabelMaster, label_key)
        if key is False:
            tmp_msg = g.appmsg.get_log_message("BKY-90039", [label_key])
            g.applogger.info(tmp_msg)
            return False, {}
        label_key_inputs[key] = label_key
        addlabels[key] = label_name

    conclusionEvent = {}
    NowTime = int(datetime.datetime.now().timestamp())

    conclusionEvent["labels"] = {}
    conclusionEvent["labels"]["_exastro_event_collection_settings_id"] = ''
    conclusionEvent["labels"]["_exastro_fetched_time"] = NowTime
    conclusionEvent["labels"]["_exastro_end_time"] = NowTime + int(RuleInfo['TTL'])
    conclusionEvent["labels"]["_exastro_evaluated"] = "0"
    conclusionEvent["labels"]["_exastro_undetected"] = "0"
    conclusionEvent["labels"]["_exastro_timeout"] = "0"
    conclusionEvent["labels"]["_exastro_checked"] = "1"
    conclusionEvent["labels"]["_exastro_type"] = "conclusion"
    conclusionEvent["labels"]["_exastro_rule_name"] = RuleInfo['RULE_LABEL_NAME']
    for name, value in addlabels.items():
        conclusionEvent["labels"][name] = value
    conclusionEvent["exastro_created_at"] = datetime.datetime.utcnow()
    conclusionEvent["exastro_rules"] = []
    rule_data = {'id': RuleInfo['RULE_ID'], 'name': RuleInfo['RULE_NAME']}
    conclusionEvent["exastro_rules"].insert(0, rule_data)
    if type(UseEventIdList) == str:
        conclusionEvent["exastro_events"] = UseEventIdList.split(',')
    else:
        conclusionEvent["exastro_events"] = list(map(repr, UseEventIdList))
    conclusionEvent["exastro_label_key_inputs"] = {}
    conclusionEvent["exastro_label_key_inputs"] = label_key_inputs

    # MongoDBに結論イベント登録
    _id = EventObj.insert_event(conclusionEvent)

    tmp_msg = g.appmsg.get_log_message("BKY-90040", [_id])
    g.applogger.debug(tmp_msg)

    return True, conclusionEvent

def getLabelGroup(wsDb):
    retDict = {}

    Rows = wsDb.table_select(oaseConst.V_OASE_LABEL_KEY_GROUP, 'WHERE DISUSE_FLAG = %s', [0])
    for Row in Rows:
        retDict[str(Row['LABEL_KEY_ID'])] = Row['LABEL_KEY_NAME']

    return retDict

def getIDtoLabelName(LabelMasterDict, uuid):
    uuid = str(uuid)
    if uuid not in LabelMasterDict:
        return False
    return LabelMasterDict[uuid]
