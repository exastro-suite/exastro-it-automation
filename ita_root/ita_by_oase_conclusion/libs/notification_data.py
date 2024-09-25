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
from bson.objectid import ObjectId
import datetime
from flask import g
import json
from jinja2 import Template
from typing import Optional, Dict, List
import re

# oase
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.common.mongoconnect.const import Const as mongoConst
from common_libs.oase.const import oaseConst
from libs.common_functions import addline_msg

class Notification_data():
    """事前通知・事後通知のテンプレートに適用するデータを作成するクラス
    """

    # マッチした結果のステータスのメッセージマップ
    action_log_status_map = {
        oaseConst.OSTS_Rule_Match : [ '判定済み', 'Rule matched' ],
        oaseConst.OSTS_Executing : [ '実行中', 'Executing' ],
        oaseConst.OSTS_Wait_Approval : [ '承認待ち', 'Waiting for approval' ],
        oaseConst.OSTS_Approved : [ '承認済み', 'Approved' ],
        oaseConst.OSTS_Rejected : [ '承認却下済み', 'Approval rejected' ],
        oaseConst.OSTS_Completed : [ '完了', 'Completed' ],
        oaseConst.OSTS_Completed_Abend : [ '完了（異常）', 'Completed (abnormal)' ],
        oaseConst.OSTS_Wait_For_Comp_Conf : [ '完了確認待ち', 'Waiting for completion confirmation' ],
        oaseConst.OSTS_Completion_Conf : [ '完了確認済み', 'Completion confirmed' ],
        oaseConst.OSTS_Completion_Conf_Reject : [ '完了確認却下済み', 'Completion confirmation rejected' ]
    }

    # ルールのフィルター演算子のメッセージマップ
    rule_filter_operator_map = {
        oaseConst.DF_OPE_OR : [ 'A or B', ' A or B' ],
        oaseConst.DF_OPE_AND : [ 'A and B', 'A and B' ],
        oaseConst.DF_OPE_ORDER : [ 'A -> B', 'A -> B' ]
    }

    # アクション（結論イベントのメッセージマップ
    rule_action_label_inheritance_flag_map = {
        '1': [ 'パラメータとして利用する', 'Used as a parameter' ],
        '0': [ 'パラメータとして利用しない', 'Not use as a parameter' ]
    }

    # イベント（結論イベントのメッセージマップ
    rule_event_label_inheritance_flag_map = {
        '1': [ '結論イベントに継承する', 'Inheriting Conclusion Events' ],
        '0': [ '結論イベントに継承しない', 'Not Inheriting Conclusion Events' ]
    }

    # アクション情報のイベント連携
    action_event_collaboration_map = {
        '1' : [ '有効', 'Enabled' ],
        '0' : [ '無効', 'Disabled']
    }

    # Conductor情報のステータスのメッセージマップ
    conductor_status_map = {
        oaseConst.CSTS_Unexecuted : [ '未実行', 'Unexecuted' ],
        oaseConst.CSTS_Unexecuted_Schedule : [ '未実行(予約)', 'Unexecuted (scheduled)' ],
        oaseConst.CSTS_Executing : [ '実行中', 'Executing' ],
        oaseConst.CSTS_Executing_Delay : [ '実行中(遅延)', 'Executing (delayed)' ],
        oaseConst.CSTS_Pause : [ '一時停止', 'Paused' ],
        oaseConst.CSTS_Completed : [ '正常終了', 'Completed' ],
        oaseConst.CSTS_Abend : [ '異常終了', 'Abend' ],
        oaseConst.CSTS_Warning_end : [ '警告終了', 'Ended with warning' ],
        oaseConst.CSTS_Emergency_stop : [ '緊急停止', 'Emergency stop' ],
        oaseConst.CSTS_Schedule_Cancel : [ '予約取消', 'Cancelled schedule' ],
        oaseConst.CSTS_Unexpected_Error : [ '想定外エラー', 'Unexpected error' ]
    }

    # Conductor情報の緊急停止フラグ
    conductor_abort_execute_flag_map = {
        '1' : [ '発令済み', 'Issued' ],
        '0' : [ '未発令', 'not issued']
    }

    def __init__(self, wsDb, EventObj):
        """コンストラクタ

        Args:
            wsDb (database): DBコネクション
            EventObj (ManageEvents): イベント・マネージャー
        """
        self.wsDb = wsDb
        self.EventObj = EventObj

    def getBeforeActionEventList(self, UseEventIdList: List, action_log_entity: Dict, rule_entiry: Dict, action_entity: Optional[Dict]):
        """事前通知に適用するデータを生成する。

        Args:
            UseEventIdList (List): 利用イベントIDリスト(UseEventIdList)
            action_log_entity (dict): 取得済みのマッチした結果(action_log_row)
            rule_entity (dict): 取得済みのルール情報(ruleInfo)
            action_entity (dict): 取得済みのアクション情報(ret_action[0])

        Returns:
            list<dict>: 事前通知データ
        """
        before_action_list = []
        before_action = {}

        # イベント
        events = []
        if UseEventIdList and len(UseEventIdList) > 0:
            events = self.geEventList(UseEventIdList)
        if len(events) > 0:
            before_action['events'] = events
        else:
            before_action['events'] = self.getDefaultForEvents()

        # マッチした結果
        action_log = {}
        if action_log_entity and any(action_log_entity):
            action_log = self.geActionLog(action_log_entity)
        if any(action_log):
            before_action['action_log'] = action_log
        else:
            before_action['action_log'] = self.getDefaultForActionLog()

        # ルール情報
        rule = {}
        if rule_entiry and any(rule_entiry):
            rule = self.getPreRule(rule_entiry)
        if any(rule):
            before_action['rule'] = rule
        else:
            before_action['rule'] = self.getDefaultForRule()

        # アクション情報
        action = {}
        if action_entity and any(action_entity):
            if rule_entiry and any(rule_entiry):
                action_id = rule_entiry.get('ACTION_ID', '')
                if action_id and len(action_id) > 0:
                    action = self.getPreAction(action_entity)
        if any(action):
            before_action['action'] = action
        else:
            before_action['action'] = self.getDefaultForAction()

        # 承認情報
        before_action['approval'] = self.approval()

        # リストに追加
        before_action_list.append(before_action)

        return before_action_list


    def getAfterActionEventList(self, action_log_entity: Dict):
        """事後通知に適用するデータを生成する。

        Args:
            action_log_entity (dict): 取得済みアクションログ

        Returns:
            list<dict>: 事後通知データ
        """
        after_action_list = []
        after_action = {}

        # イベント
        events = []
        if action_log_entity and any(action_log_entity):
            event_id_list = action_log_entity.get('EVENT_ID_LIST', '')
            if event_id_list and len(event_id_list) > 0:
                objectId_list = []
                event_id_array = event_id_list.split(',')
                for event_id in event_id_array:
                    id = re.sub("ObjectId\('|'\)", '', event_id)
                    try:
                        objectId_list.append(ObjectId(id))
                    except Exception:
                        pass
                events = self.geEventList(objectId_list)
        if len(events) > 0:
            after_action['events'] = events
        else:
            after_action['events'] = self.getDefaultForEvents()

        # マッチした結果
        action_log = {}
        if action_log_entity and any(action_log_entity):
            action_log = self.geActionLog(action_log_entity)
        if any(action_log):
            after_action['action_log'] = action_log
        else:
            after_action['action_log'] = self.getDefaultForActionLog()

        # ルール情報
        rule = {}
        if action_log_entity and any(action_log_entity):
            rule_id = action_log_entity.get('RULE_ID', '')
            if rule_id and len(rule_id) > 0:
                rule = self.getPostRule(rule_id)
        if any(rule):
            after_action['rule'] = rule
        else:
            after_action['rule'] = self.getDefaultForRule()

        # アクション情報
        action = {}
        if action_log_entity and any(action_log_entity):
            action_id = action_log_entity.get('ACTION_ID', '')
            if action_id and len(action_id) > 0:
                action = self.getPostAction(action_id)
        if any(action):
            after_action['action'] = action
        else:
            after_action['action'] = self.getDefaultForAction()

        # Conductor情報
        conductor = {}
        if action_log_entity and any(action_log_entity):
            conductor_instance_id = action_log_entity.get('CONDUCTOR_INSTANCE_ID', '')
            if conductor_instance_id and len(conductor_instance_id) > 0:
                conductor = self.getPostConductor(conductor_instance_id)
        if any(conductor):
            after_action['conductor'] = conductor
        else:
            after_action['conductor'] = self.getDefaultForConductor()

        # 承認情報
        after_action['approval'] = self.approval()

        # リストに追加
        after_action_list.append(after_action)

        return after_action_list

    def geEventList(self, eventIdList):
        """イベント情報取得

        Args:
            eventIdList (List): イベントIDリスト

        Returns:
            dict: イベント情報
        """
        events = []
        where_str = {}
        if len(eventIdList) > 0:
            where_str["_id"] = {"$in": eventIdList}
            labeled_events = self.EventObj.labeled_event_collection.find(where_str)

            # イベント
            for event_row in labeled_events:
                event = {}
                if 'event' in event_row:
                    event['_exastro_events'] = event_row['event']
                    # Noneを空文字に置換
                    for key, value in event['_exastro_events'].items():
                        event['_exastro_events'][key] = value or ""
                if 'labels' in event_row:
                    event['labels'] = event_row['labels']
                    event['labels']['_id'] = str(event_row['_id'])
                    event['labels']['_exastro_fetched_time'] = self.formatDateTime(event['labels']['_exastro_fetched_time'])
                    event['labels']['_exastro_end_time'] = self.formatDateTime(event['labels']['_exastro_end_time'])

                    # イベント収集設定名
                    event['labels']['_exastro_event_collection_settings_name'] = ''
                    event_collection_settings_id = event['labels']['_exastro_event_collection_settings_id']
                    _settingList = self.wsDb.table_select(oaseConst.T_OASE_EVENT_COLLECTION_SETTINGS, 'WHERE DISUSE_FLAG = %s AND EVENT_COLLECTION_SETTINGS_ID = %s', [0, event_collection_settings_id])
                    if not _settingList:
                        tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_FILTER])
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    else:
                        event['labels']['_exastro_event_collection_settings_name'] = _settingList[0]['EVENT_COLLECTION_SETTINGS_NAME']

                    # Noneを空文字に置換
                    for key, value in event['labels'].items():
                        event['labels'][key] = value or ""

                if any(event):
                    events.append(event)

        return events

    def geActionLog(self, action_log_entity):
        """アクションログ取得

        Args:
            action_log_entity (dict): 取得済みアクションログ

        Returns:
            dict: アクションログ
        """
        action_log = {}
        action_log['status'] = action_log_entity.get('STATUS_ID', '') or ""
        action_log['time_register'] = self.formatDateTime(action_log_entity.get('TIME_REGISTER', ''))
        action_log['conductor_instance_id'] = action_log_entity.get('CONDUCTOR_INSTANCE_ID', '') or ""
        action_log['conductor_instance_name'] = action_log_entity.get('CONDUCTOR_INSTANCE_NAME', '') or ""
        action_log['conclusion_event_labels'] = action_log_entity.get('CONCLUSION_EVENT_LABELS', '') or ""

        # ステータス
        code = action_log['status']
        action_log['status'] = self.getCategorName(self.action_log_status_map, code)

        return action_log

    def getPreRule(self, rule_entity):
        """事前ルール情報取得

        Args:
            rule_entity (dict): 取得済みルール情報

        Returns:
            dict: 事前ルール情報
            int : 通知タイプ（初期値=5.事前通知）
        """
        rule = {}
        rule['rule_id'] = rule_entity.get('RULE_ID', '') or ""
        rule['rule_name'] = rule_entity.get('RULE_NAME', '') or ""
        rule['filter_a'] = rule_entity.get('FILTER_A', '') or ""
        rule['filter_a_name'] = ''
        rule['filter_a_condition_json'] =  ''
        if rule['filter_a']:
            _filterList = self.wsDb.table_select(oaseConst.T_OASE_FILTER, 'WHERE DISUSE_FLAG = %s AND FILTER_ID = %s', [0, rule['filter_a']])
            if not _filterList:
                tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_FILTER])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            else:
                rule['filter_a_name'] = _filterList[0]['FILTER_NAME'] or ""
                rule['filter_a_condition_json'] = _filterList[0]['FILTER_CONDITION_JSON'] or ""
        rule['filter_operator'] = rule_entity.get('FILTER_OPERATOR', '') or ""
        rule['filter_b'] = rule_entity.get('FILTER_B', '') or ""
        rule['filter_b_name'] = ''
        rule['filter_b_condition_json'] = ''
        if rule['filter_b']:
            _filterList = self.wsDb.table_select(oaseConst.T_OASE_FILTER, 'WHERE DISUSE_FLAG = %s AND FILTER_ID = %s', [0, rule['filter_b']])
            if not _filterList:
                tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_FILTER])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            else:
                rule['filter_b_name'] = _filterList[0]['FILTER_NAME'] or ""
                rule['filter_b_condition_json'] = _filterList[0]['FILTER_CONDITION_JSON'] or ""
        rule['action_label_inheritance_flag'] = rule_entity.get('ACTION_LABEL_INHERITANCE_FLAG', '') or ""
        rule['event_label_inheritance_flag'] = rule_entity.get('EVENT_LABEL_INHERITANCE_FLAG', '') or ""
        rule['conclusion_label_settings'] = rule_entity.get('CONCLUSION_LABEL_SETTINGS', '') or ""
        rule['ttl'] = rule_entity.get('TTL', '') or ""
        rule['note'] = rule_entity.get('NOTE', '') or ""

        # フィルター演算子
        code = rule['filter_operator']
        rule['filter_operator'] = self.getCategorName(self.rule_filter_operator_map, code)

        # アクション
        code = rule['action_label_inheritance_flag']
        rule['action_label_inheritance_flag'] = self.getCategorName(self.rule_action_label_inheritance_flag_map, code)

        # イベント
        code = rule['event_label_inheritance_flag']
        rule['event_label_inheritance_flag'] = self.getCategorName(self.rule_event_label_inheritance_flag_map, code)

        return rule

    def getPreAction(self, action_entity):
        """事前アクション情報取得

        Args:
            action_entity (dict): 取得済みアクション情報

        Returns:
            dict: 事前アクション
        """
        action = {}
        action['action_id'] = action_entity.get('ACTION_ID', '') or ""
        action['action_name'] = action_entity.get('ACTION_NAME', '') or ""
        action['operation_id'] = action_entity.get('OPERATION_ID', '') or ""
        action['operation_name'] = ''
        if action['operation_id']:
            _opeationList = self.wsDb.table_select('T_COMN_OPERATION', 'WHERE DISUSE_FLAG = %s AND OPERATION_ID = %s ', [0, action['operation_id']])
            if not _opeationList:
                tmp_msg = g.appmsg.get_log_message("BKY-90009", ['T_COMN_OPERATION'])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            else:
                action['operation_name'] = _opeationList[0]['OPERATION_NAME'] or ""
        action['conductor_class_id'] = action_entity.get('CONDUCTOR_CLASS_ID', '') or ""
        action['conductor_name'] = ''
        if action['conductor_class_id']:
            _opeationList = self.wsDb.table_select('T_COMN_CONDUCTOR_CLASS', 'WHERE DISUSE_FLAG = %s AND CONDUCTOR_CLASS_ID = %s ', [0, action['conductor_class_id']])
            if not _opeationList:
                tmp_msg = g.appmsg.get_log_message("BKY-90009", ['T_COMN_CONDUCTOR_CLASS'])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            else:
                action['conductor_name'] = _opeationList[0]['CONDUCTOR_NAME'] or ""

        action['event_collaboration'] = action_entity.get('EVENT_COLLABORATION', '') or ""
        action['host_id'] = action_entity.get('HOST_ID', '') or ""
        action['parameter_sheet_id'] = action_entity.get('PARAMETER_SHEET_ID', '') or ""
        action['note'] = action_entity.get('NOTE', '') or ""

        # イベント連携
        action['event_collaboration'] = self.getCategorName(self.action_event_collaboration_map,action['event_collaboration'] )

        return action

    def getPostRule(self, rule_id):
        """事後ルール情報取得

        Args:
            rule_id (string): ルールID

        Returns:
            dict: 事後ルール情報
            int : 通知タイプ(初期値=6.事後通知）)
        """
        rule = {}

        _ruleList = self.wsDb.table_select(oaseConst.T_OASE_RULE, 'WHERE DISUSE_FLAG = %s AND RULE_ID = %s ', [0, rule_id])
        if not _ruleList:
            tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_RULE])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        else:
            rule_entity = _ruleList[0]
            rule = self.getPreRule(rule_entity)

        return rule

    def getPostAction(self, action_id):
        """事後アクション情報取得

        Args:
            action_id (string): アクションID

        Returns:
            dict: 事後アクション情報
        """
        action = {}
        _actionList = self.wsDb.table_select(oaseConst.T_OASE_ACTION, 'WHERE DISUSE_FLAG = %s AND ACTION_ID = %s ', [0, action_id])
        if not _actionList:
            tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_ACTION])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        else:
            action_entity = _actionList[0]
            action = self.getPreAction(action_entity)

        return action

    def getPostConductor(self, conductor_instance_id):
        """事後Conductor情報取得

        Args:
            conductor_instance_id (string):  conductorインスタンスid

        Returns:
            dict: 事後Conductor情報取得
        """
        conductor = {}
        _list = self.wsDb.table_select('T_COMN_CONDUCTOR_INSTANCE', 'WHERE DISUSE_FLAG = %s AND CONDUCTOR_INSTANCE_ID = %s ', [0, conductor_instance_id])
        if not _list:
            tmp_msg = g.appmsg.get_log_message("BKY-90009", ['T_COMN_CONDUCTOR_INSTANCE'])
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        else:
            conductor_instance_entity = _list[0]
            conductor['status'] = conductor_instance_entity.get('STATUS_ID', '') or ""
            conductor['operation_id'] = conductor_instance_entity.get('OPERATION_ID', '') or ""
            conductor['operation_name'] = conductor_instance_entity.get('I_OPERATION_NAME', '') or ""
            conductor['time_register'] = self.formatDateTime(conductor_instance_entity.get('TIME_REGISTER', ''))
            conductor['time_book'] = self.formatDateTime(conductor_instance_entity.get('TIME_BOOK', ''))
            conductor['time_start'] = self.formatDateTime(conductor_instance_entity.get('TIME_START', ''))
            conductor['time_end'] = self.formatDateTime(conductor_instance_entity.get('TIME_END', ''))
            conductor['abort_execute_flag'] = conductor_instance_entity.get('ABORT_EXECUTE_FLAG', '') or ""
            conductor['note'] = conductor_instance_entity.get('NOTE', '') or ""

            # ステータス
            code = conductor['status']
            conductor['status'] = self.getCategorName(self.conductor_status_map, code)

            # 緊急停止フラグ
            code = conductor['abort_execute_flag']
            conductor['abort_execute_flag'] = self.getCategorName(self.conductor_abort_execute_flag_map, code)

        return conductor

    def approval(self):
        """承認情報取得

        Returns:
            Dict: 承認情報
        """
        approval = {}
        # 事前承認したユーザー
        approval['pre-approved_user'] = ''

        return approval

    def getDefaultForEvents(self):
        """イベント規定値取得

        Returns:
            List<Dict>: イベント規定値
        """
        events = []
        return events


    def getDefaultForActionLog(self):
        """評価結果規定値取得

        Returns:
            dict_: 評価結果規定値
        """
        action_log = {}
        action_log['status'] = ''
        action_log['time_register'] = ''
        action_log['conductor_instance_id'] = ''
        action_log['conductor_instance_name'] = ''
        action_log['conclusion_event_labels'] = ''
        return action_log


    def getDefaultForRule(self):
        """ルール規定値取得

        Returns:
            dict: ルール規定値
        """
        rule = {}
        rule['rule_id'] = ''
        rule['rule_name'] = ''
        rule['filter_a'] = ''
        rule['filter_a_name'] = ''
        rule['filter_a_condition_json'] = ''
        rule['filter_operator'] = ''
        rule['filter_b'] = ''
        rule['filter_b_name'] = ''
        rule['filter_b_condition_json'] = ''
        rule['action_label_inheritance_flag'] = ''
        rule['event_label_inheritance_flag'] = ''
        rule['conclusion_label_settings'] = ''
        rule['ttl'] = ''
        rule['note'] = ''
        return rule


    def getDefaultForAction(self):
        """アクション規定値取得

        Returns:
            dict: アクション規定値
        """
        action = {}
        action['action_id'] = ''
        action['action_name'] = ''
        action['operation_id'] = ''
        action['operation_name'] = ''
        action['conductor_class_id'] = ''
        action['conductor_name'] = ''
        action['event_collaboration'] = ''
        action['host_id'] = ''
        action['parameter_sheet_id'] = ''
        action['note'] = ''

        return action

    def getDefaultForConductor(self):
        """conductorインスタンス規定値取得

        Returns:
            dict: conductorインスタンス規定値
        """
        conductor = {}
        conductor['status'] = ''
        conductor['operation_id'] = ''
        conductor['operation_name'] = ''
        conductor['time_register'] = ''
        conductor['time_book'] = ''
        conductor['time_start'] = ''
        conductor['time_end'] = ''
        conductor['abort_execute_flag'] = ''
        conductor['note'] = ''
        return conductor

    def getCategorName(self, categoryMap, category_id):
        """区分名称取得

        Args:
            categoryMap (Dict): カテゴリマップ
            category_id (string): 区分ID

        Returns:
            string: 区分名称
        """
        category_name = ""
        if category_id and category_id in categoryMap:
            category_names = categoryMap[category_id]
            if g.LANGUAGE == 'ja':
                category_name = category_names[0]
            else:
                category_name = category_names[1]

        return category_name

    def formatDateTime(self, ymdhms):
        """日付書式変換

        Args:
            ymdhms (int or datetime): 日付

        Returns:
            string: 日付書式変換した文字列
        """
        try:
            if not ymdhms:
                return ''
            elif type(ymdhms) is int:
                return datetime.datetime.fromtimestamp(int(ymdhms)).strftime("%Y/%m/%d %H:%M:%S")
            elif type(ymdhms) is datetime:
                return ymdhms.strftime("%Y/%m/%d %H:%M:%S")
            elif type(ymdhms) is datetime.datetime:
                return ymdhms.strftime("%Y/%m/%d %H:%M:%S")
            else:
                return ymdhms
        except Exception:
            return ymdhms