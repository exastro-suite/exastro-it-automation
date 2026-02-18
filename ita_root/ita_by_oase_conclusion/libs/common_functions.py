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

import json
import datetime

from common_libs.oase.const import oaseConst

def addline_msg(msg=''):
    """メッセージへの行追加(ダミー)

    本来はメッセージへの行追加処理だが、処理が重いためダミー化

    Args:
        msg (str, optional): メッセージ。デフォルトは''。

    Returns:
        str: メッセージ。
    """
    return msg

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
    conclusionEvent["exastro_created_at"] = datetime.datetime.now(datetime.timezone.utc)
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
        # No records to process. Table: {}
        tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_FILTER])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False
    # Acquired filter management. Items: {}
    tmp_msg = g.appmsg.get_log_message("BKY-90010", [str(len(filterList))])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # key:value形式に変換して、フィルター設定をIDで引けるようにしておく
    filterIDMap = {}
    for filter in filterList:
        filterIDMap[filter["FILTER_ID"]] = filter

    return filterIDMap


def deduplication_timeout_filter(deduplication_settings, event):
    """ 新規（統合時）イベントのTTL切れを抽出し通知対象であるかどうかを返却する\n
        Args:
            deduplication_settings (list): 重複排除設定のレコードリスト
            event (dict): TTL切れイベントのget_eventsで取得したイベントデータ(EventRow)
        Returns:
            is_alert_target (bool): 新規（統合時）通知対象かどうかの判定結果
    """

    # 重複排除設定で単一の収集先が複数の冗長グループに入っている場合はそもそもアラート通知の対象外と出来るはず（アラート通知で前提条件として複数システムは対象外）
    # _exastro_event_collection_settings_idから重複排除設定の冗長グループを特定する
    # （ただデータパターンとしては一応あるので、エラー落ちしないよう単一の収集先が複数の冗長グループに入っているなら優先順位が一番高いもののみを使用）
    # dedup_to_redundancy_ids-->重複排除設定IDをキーとし、冗長グループ(MultiIDColumn)のidリストを値とする辞書
    dedup_to_redundancy_ids = {}
    # source_to_dedup_id-->収集先設定IDをキーとし、自身が対象の重複排除設定IDを値とする辞書
    source_to_dedup_id = {}
    # 取り扱いしやすくするために収集先IDから冗長グループを特定する辞書を作成する
    for deduplication_setting in deduplication_settings:
        # 重複排除設定ID
        deduplication_setting_id = deduplication_setting["DEDUPLICATION_SETTING_ID"]
        # 冗長グループ
        redundancy_ids = json.loads(deduplication_setting["EVENT_SOURCE_REDUNDANCY_GROUP"])["id"]
        # dedup_to_redundancy_idsの構築-->重複排除設定IDをキーとし、冗長グループ(MultiIDColumn)のidリストを値とする
        dedup_to_redundancy_ids[deduplication_setting_id] = redundancy_ids
        # source_to_dedup_idの構築-->収集先設定IDをキーとし、自身が対象の重複排除設定IDを値とする
        for source_id in redundancy_ids:
            # 優先順位の昇順で回しているので既に入っているならスルー
            if source_id not in source_to_dedup_id:
                source_to_dedup_id[source_id] = deduplication_setting_id
    # イベントから収集先設定IDを特定する
    collection_id = event["labels"]["_exastro_event_collection_settings_id"]
    # イベントから重複排除関連の情報を特定する
    duplicate_ids = event.get("exastro_duplicate_collection_settings_ids", {})
    # 収集先設定IDから自身が対象の重複排除設定を特定する
    dedup_id = source_to_dedup_id.get(collection_id)
    # 該当の重複排除設定から冗長グループを特定する
    redundancy_group = dedup_to_redundancy_ids.get(dedup_id, [])
    # 対象の冗長グループがexastro_duplicate_collection_settings_idsの辞書内に1以上で刻まれているならイベント自体はそろってるはず
    is_alert_target = False
    for target_source_id in redundancy_group:
        # exastro_duplicate_collection_settings_idsにあるべき収集先設定IDがない、もしくは1以上の値を持っていない場合は重複排除アラートのTTL切れとして通知キューに入れる
        if target_source_id not in duplicate_ids or duplicate_ids[target_source_id] < 1:
            # 通知キューに入れるべきイベントとして認識した旨はログに出す
            g.applogger.info(f"EventID:{event['_id']} is an event that should be put into the deduplication timeout notification queue.")
            is_alert_target = True
            # 1つでも冗長グループの収集先が足りていないなら通知キューに入れるべきなのでここでループを抜ける
            break
    # 単純に対象かどうかのフラグを返す
    return is_alert_target
