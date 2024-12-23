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

from common_libs.oase.const import oaseConst

def addline_msg(msg=''):
    info = inspect.getouterframes(inspect.currentframe())[1]
    msg_line = "{} ({}:{})".format(msg, os.path.basename(info.filename), info.lineno)
    return msg_line

def InsertConclusionEvent(EventObj, RuleInfo, UseEventIdList, ConclusionLablesStr):
    # 結論イベント登録

    conclusionEvent = {}
    NowTime = int(datetime.datetime.now().timestamp())
    ConclusionLablesDict = json.loads(ConclusionLablesStr)

    conclusionEvent["labels"] = ConclusionLablesDict["labels"]
    conclusionEvent["labels"]["_exastro_event_collection_settings_id"] = ''
    conclusionEvent["labels"]["_exastro_fetched_time"] = NowTime
    conclusionEvent["labels"]["_exastro_end_time"] = NowTime + int(RuleInfo['TTL'])
    conclusionEvent["labels"]["_exastro_evaluated"] = "0"
    conclusionEvent["labels"]["_exastro_undetected"] = "0"
    conclusionEvent["labels"]["_exastro_timeout"] = "0"
    conclusionEvent["labels"]["_exastro_checked"] = "1"
    conclusionEvent["labels"]["_exastro_type"] = "conclusion"
    conclusionEvent["labels"]["_exastro_rule_name"] = RuleInfo['RULE_LABEL_NAME']
    conclusionEvent["exastro_created_at"] = datetime.datetime.now()
    conclusionEvent["exastro_rules"] = []
    conclusionEvent["exastro_rules"].insert(0, {'id': RuleInfo['RULE_ID'], 'name': RuleInfo['RULE_NAME']})
    if type(UseEventIdList) == str:
        conclusionEvent["exastro_events"] = UseEventIdList.split(',')
    else:
        conclusionEvent["exastro_events"] = list(map(repr, UseEventIdList))
    conclusionEvent["exastro_label_key_inputs"] = ConclusionLablesDict["exastro_label_key_inputs"]

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

def getRuleList(wsDb, sort_bv_priority=False):
    # 「ルール管理」からレコードを取得
    # ソート条件変更　ORDER BY AVAILABLE_FLAG DESC, RULE_PRIORITY ASC, FILTER_A ASC, FILTER_B DESC
    _ruleList = wsDb.table_select(oaseConst.T_OASE_RULE, 'WHERE DISUSE_FLAG = %s AND AVAILABLE_FLAG = %s ORDER BY AVAILABLE_FLAG DESC, RULE_PRIORITY ASC, FILTER_A ASC, FILTER_B DESC', [0, 1])
    if not _ruleList:
        msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_RULE])
        return False, msg

    if sort_bv_priority is False:
        return True, _ruleList

    # 優先順位を正規化する
    # 優先順位を入力していない場合があるため、ソート順に並べて優先順位プロパティを更新しておく
    ruleList = []
    Priority = 1
    for rule_row in _ruleList:
        rule_row['RULE_PRIORITY'] = Priority
        Priority += 1
        ruleList.append(rule_row)
    return True, ruleList

def getFilterIDMap(wsDb):
    filterList = wsDb.table_select(oaseConst.T_OASE_FILTER, 'WHERE DISUSE_FLAG = %s AND AVAILABLE_FLAG = %s', [0, 1])
    if not filterList:
        tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_FILTER])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False
    tmp_msg = g.appmsg.get_log_message("BKY-90010", [str(len(filterList))])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # key:value形式に変換して、フィルター設定をIDで引けるようにしておく
    filterIDMap = {}
    for filter in filterList:
        filterIDMap[filter["FILTER_ID"]] = filter

    return filterIDMap
