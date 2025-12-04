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

import datetime
import json
import textwrap
import traceback

from flask import g
from jinja2 import Template

# action
from common_libs.apply import apply
from common_libs.common.exception import AppException
from common_libs.common.util import arrange_stacktrace_format, get_iso_datetime
from common_libs.conductor.classes.exec_util import ConductorExecuteBkyLibs
# notification
from common_libs.notification.sub_classes.oase import OASENotificationType
# oase
from common_libs.oase.const import oaseConst
from libs.common_functions import addline_msg, getIDtoLabelName
from libs.notification_data import Notification_data
from libs.notification_process import NotificationProcessManager
from libs.writer_process import WriterProcessManager


class Action():
    def __init__(self, wsDb, EventObj):
        self.wsDb = wsDb
        self.EventObj = EventObj
        self.template_cache = {}

    def RegisterActionLog(self, ruleInfo, UseEventIdList, LabelMasterDict):
        rule_id = ruleInfo.get("RULE_ID")

        # アクションに利用 & 結論イベントに付与 するラベルを生成する
        action_label_inheritance_flg = ruleInfo.get("ACTION_LABEL_INHERITANCE_FLAG", "1")
        event_label_inheritance_flg = ruleInfo.get("EVENT_LABEL_INHERITANCE_FLAG", "0")
        action_parameters, conclusion_event_lables = self.generateConclusionLables(UseEventIdList, ruleInfo, LabelMasterDict, action_label_inheritance_flg, event_label_inheritance_flg)

        # 評価結果に登録するアクション情報を取得（ある場合）
        action_id = ruleInfo.get("ACTION_ID", "")
        action_name = ""
        conductor_class_id = None
        conductor_name = ""
        operation_id = None
        operation_name = ""

        event_collaboration = None
        host_id = None
        host_name = ""
        parameter_sheet_id = ""
        parameter_sheet_name = ""
        parameter_sheet_name_rest = ""
        if action_id:
            # 「アクション」からレコードを取得
            ret_action = self.wsDb.table_select(oaseConst.T_OASE_ACTION, 'WHERE DISUSE_FLAG = %s AND ACTION_ID = %s', [0, action_id])
            if not ret_action:
                tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_ACTION])
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            else:
                action_name = ret_action[0].get("ACTION_NAME")
                conductor_class_id = ret_action[0].get("CONDUCTOR_CLASS_ID", "")
                operation_id = ret_action[0].get("OPERATION_ID", "")

                event_collaboration = ret_action[0].get("EVENT_COLLABORATION", "0")  # 未入力はFalse
                host_id = ret_action[0].get("HOST_ID", "")
                parameter_sheet_id = ret_action[0].get("PARAMETER_SHEET_ID", "")

                if conductor_class_id:
                    # 「コンダクタークラス」からレコードを取得
                    ret_conductor = self.wsDb.table_select('T_COMN_CONDUCTOR_CLASS', 'WHERE DISUSE_FLAG = %s AND CONDUCTOR_CLASS_ID = %s', [0, conductor_class_id])
                    if not ret_conductor:
                        tmp_msg = g.appmsg.get_log_message("BKY-90009", ['T_COMN_CONDUCTOR_CLASS'])
                        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    else:
                        conductor_name = ret_conductor[0].get("CONDUCTOR_NAME")

                if operation_id:
                    # 「オペレーション」からレコードを取得
                    ret_operation = self.wsDb.table_select('T_COMN_OPERATION', 'WHERE DISUSE_FLAG = %s AND OPERATION_ID = %s', [0, operation_id])
                    if not ret_operation:
                        tmp_msg = g.appmsg.get_log_message("BKY-90009", ['T_COMN_OPERATION'])
                        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    else:
                        operation_name = ret_operation[0].get("OPERATION_NAME")

                if host_id:
                    # 「ホスト一覧」からレコードを取得
                    # V_HGSP_UQ_HOST_LIST
                    # T_ANSC_DEVICE         HOST_NAME
                    # T_HGSP_HOSTGROUP_LIST HOSTGROUP_NAME
                    ret_host = self.wsDb.table_select('V_HGSP_UQ_HOST_LIST', 'WHERE DISUSE_FLAG = %s AND KY_KEY = %s', [0, host_id])
                    if not ret_host:
                        tmp_msg = g.appmsg.get_log_message("BKY-90009", ['V_HGSP_UQ_HOST_LIST'])
                        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    else:
                        _host = ret_host[0].get("KY_VALUE")
                        if _host.startswith("[HG]"):
                            # ホストグループ
                            ret_host = self.wsDb.table_select('T_HGSP_HOSTGROUP_LIST', 'WHERE DISUSE_FLAG = %s AND ROW_ID = %s', [0, host_id])
                            if not ret_host:
                                tmp_msg = g.appmsg.get_log_message("BKY-90009", ['T_HGSP_HOSTGROUP_LIST'])
                                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            host_name = _host
                        # elif _host.startswith("[H]"):
                        else:
                            ret_host = self.wsDb.table_select('T_ANSC_DEVICE', 'WHERE DISUSE_FLAG = %s AND SYSTEM_ID = %s', [0, host_id])
                            if not ret_host:
                                tmp_msg = g.appmsg.get_log_message("BKY-90009", ['T_ANSC_DEVICE'])
                                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                            host_name = ret_host[0].get('HOST_NAME')

                if parameter_sheet_id:
                    # 「メニュー管理」からレコードを取得
                    ret_parameter = self.wsDb.table_select('T_COMN_MENU', 'WHERE DISUSE_FLAG = %s AND MENU_ID = %s', [0, parameter_sheet_id])
                    if not ret_parameter:
                        tmp_msg = g.appmsg.get_log_message("BKY-90009", ['T_COMN_MENU'])
                        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    else:
                        parameter_sheet_name = ret_parameter[0].get("MENU_NAME_EN")
                        parameter_sheet_name_rest = ret_parameter[0].get("MENU_NAME_REST")

        # 評価結果へ登録
        # トランザクション開始
        # ⇒ T_OASE_ACTION_LOGへの書き込みは子プロセス（WriterProcess）で行うため、書き込みは行わなくなったためコメントアウト
        # self.wsDb.db_transaction_start()
        action_log_row = {
            "RULE_ID": rule_id,
            "RULE_NAME": ruleInfo.get("RULE_NAME"),
            "STATUS_ID": oaseConst.OSTS_Rule_Match,  # 1:判定済み
            "ACTION_ID": action_id,
            "ACTION_NAME": action_name,
            "CONDUCTOR_INSTANCE_ID": conductor_class_id,
            "CONDUCTOR_INSTANCE_NAME": conductor_name,
            "OPERATION_ID": operation_id,
            "OPERATION_NAME": operation_name,
            "EVENT_COLLABORATION": event_collaboration,
            "HOST_ID": host_id,
            "HOST_NAME": host_name,
            "PARAMETER_SHEET_ID": parameter_sheet_id,
            "PARAMETER_SHEET_NAME": parameter_sheet_name,
            "PARAMETER_SHEET_NAME_REST": parameter_sheet_name_rest,
            "EVENT_ID_LIST": ','.join(map(repr, UseEventIdList)),
            "ACTION_LABEL_INHERITANCE_FLAG": action_label_inheritance_flg,
            "EVENT_LABEL_INHERITANCE_FLAG": event_label_inheritance_flg,
            "ACTION_PARAMETERS": json.dumps(action_parameters),
            "CONCLUSION_EVENT_LABELS": json.dumps(conclusion_event_lables),
            "TIME_REGISTER": datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
            "NOTE": None,
            "DISUSE_FLAG": "0",
            "LAST_UPDATE_USER": g.get('USER_ID')
        }
        # T_OASE_ACTION_LOGへの書き込みは子プロセス（WriterProcess）で行う
        # action_log_row_list = self.wsDb.table_insert(oaseConst.T_OASE_ACTION_LOG, action_log_row, 'ACTION_LOG_ID')
        action_log_row_list = WriterProcessManager.insert_oase_action_log(action_log_row)
        action_log_row = action_log_row_list[0]

        # 判定済みインシデントフラグを立てる  _exastro_evaluated='1'
        update_Flag_Dict = {"_exastro_evaluated": '1'}
        # MongoDBに反映
        self.EventObj.update_label_flag(UseEventIdList, update_Flag_Dict)
        tmp_msg = g.appmsg.get_log_message("BKY-90018", [str(update_Flag_Dict), str(UseEventIdList)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        NotificationEventList = []
        for Event_id in UseEventIdList:
            ret, EventRow = self.EventObj.get_events(Event_id)
            if ret is True:
                NotificationEventList.append(EventRow)
        # 通知処理（既知（判定済み））
        if len(NotificationEventList) > 0:
            tmp_msg = g.appmsg.get_log_message("BKY-90008", ['Known(evaluated)'])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            NotificationProcessManager.send_notification(NotificationEventList, {"notification_type": OASENotificationType.EVALUATED})

        # コミット  トランザクション終了
        # ⇒ T_OASE_ACTION_LOGへの書き込みは子プロセス（WriterProcess）で行うため、書き込みは行わなくなったためコメントアウト
        # self.wsDb.db_transaction_end(True)

        # アクションの事前処理（通知と承認）
        if action_id:
            # 事前承認が必要
            # if ruleInfo.get('BEFORE_APPROVAL_PENDING'):
            #     data_list = {
            #         "ACTION_LOG_ID": action_log_id,
            #         "STATUS_ID": oaseConst.OSTS_Wait_Approval # "3"承認待ち
            #     }
            #     self.wsDb.table_update(oaseConst.T_OASE_ACTION_LOG, data_list, 'ACTION_LOG_ID')
            #     self.wsDb.db_commit()

            # 通知先が設定されている場合、通知処理(事前通知)を実行する
            if ruleInfo.get('BEFORE_NOTIFICATION_DESTINATION'):
                # 2.3の時点では、イベントの情報は空にしておく
                notification_data = Notification_data(self.wsDb, self.EventObj)
                before_Action_Event_List = notification_data.getBeforeActionEventList(UseEventIdList, action_log_row, ruleInfo, ret_action[0])

                tmp_msg = g.appmsg.get_log_message("BKY-90008", ['Advance notice'])
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                NotificationProcessManager.send_notification(before_Action_Event_List, {"notification_type": OASENotificationType.BEFORE_ACTION, "rule_id": rule_id})

        return action_log_row

    def generateConclusionLables(self, UseEventIdList, ruleRow, labelMaster, action_label_inheritance_flg, event_label_inheritance_flg):
        # アクションに利用 & 結論イベントに付与 するラベルを生成する
        action_parameters = {}
        conclusion_event_lables = {"labels": {}, "exastro_label_key_inputs": {}}

        ab_merged_labels = {}  # 元イベントのラベルを継承するラベル
        setting_only_labels = {}  # 結論ラベル設定のみのラベル

        # フィルターA, Bそれぞれに対応するイベント取得
        ret_bool_A, event_A = self.EventObj.get_events(UseEventIdList[0])
        if len(UseEventIdList) == 2:
            ret_bool_B, event_B = self.EventObj.get_events(UseEventIdList[1])
        else:
            event_B = {"labels": {}}

        # labelsのマージ
        event_A_labels = event_A["labels"]
        event_B_labels = event_B["labels"]

        if action_label_inheritance_flg == "1" or event_label_inheritance_flg == "1":
            ab_merged_labels = event_B_labels

            # システム用のラベルは除外
            key_name_to_exclude = [
                "_exastro_event_collection_settings_id",
                "_exastro_fetched_time",
                "_exastro_end_time",
                "_exastro_evaluated",
                "_exastro_undetected",
                "_exastro_timeout",
                "_exastro_checked",
                "_exastro_type",
                "_exastro_rule_name"
            ]
            # フィルターAに該当するイベントのラベルを優先して上書き
            for label_key_name in event_A_labels:
                if label_key_name not in key_name_to_exclude:
                    ab_merged_labels[label_key_name] = event_A_labels[label_key_name]

        # 結論ラベル設定で上書き
        conc_label_settings = ruleRow["CONCLUSION_LABEL_SETTINGS"]  # LIST
        for setting in conc_label_settings:
            # label_key_idをlabel_key_nameに変換
            label_key_name = getIDtoLabelName(labelMaster, setting["label_key"])
            # label_valueに変数ブロックが含まれている場合、jinja2テンプレートで値を変換
            template_string = setting["label_value"]
            template = self.template_cache.get(template_string)
            if template is None:
                template = Template(template_string)
                self.template_cache[template_string] = template
            try:
                label_value = template.render(A=event_A_labels, B=event_B_labels)
            except Exception as e:
                t = traceback.format_exc()
                g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))

                label_value = "CONCLUSION LABELS jinja2TEMPLATE ERROR ({})".format(e)

            ab_merged_labels[label_key_name] = label_value
            setting_only_labels[label_key_name] = label_value

        # アクションパラメータに使うラベル
        if action_label_inheritance_flg == "1":
            action_parameters = ab_merged_labels
        else:
            action_parameters = setting_only_labels
        # 結論イベントにつけるラベル
        if event_label_inheritance_flg == "1":
            conclusion_event_lables["labels"] = ab_merged_labels
        else:
            conclusion_event_lables["labels"] = setting_only_labels

        # exastro_label_key_inputs
        if event_label_inheritance_flg == "0":
            for label_key_name in setting_only_labels:
                for master_label_id, master_label_key_name in labelMaster.items():
                    if label_key_name == master_label_key_name:
                        conclusion_event_lables["exastro_label_key_inputs"][label_key_name] = master_label_id
        else:
            for label_key_name in ab_merged_labels:
                for master_label_id, master_label_key_name in labelMaster.items():
                    if label_key_name == master_label_key_name:
                        conclusion_event_lables["exastro_label_key_inputs"][label_key_name] = master_label_id

        return action_parameters, conclusion_event_lables

    def run(self, action_log_row):
        """
        Actionの実行

        Arguments:
            action_log_row: 評価結果のレコード
        Returns:
            dict
                bool
                    True or False
                dict
                    {"conductor_instance_id": conductor_instance_id}
        """
        action_log_id = action_log_row['ACTION_LOG_ID']
        conductor_class_id = action_log_row.get("CONDUCTOR_INSTANCE_ID")
        conductor_class_name = action_log_row.get("CONDUCTOR_INSTANCE_NAME")
        operation_id = action_log_row.get("OPERATION_ID")
        operation_name = action_log_row.get("OPERATION_NAME")

        parameter_sheet_name_rest = action_log_row.get("PARAMETER_SHEET_NAME_REST")
        if not parameter_sheet_name_rest:
            # パラメータシートの指定がないパターン
            msg = g.appmsg.get_log_message("BKY-90073", [action_log_id])
            g.applogger.info(msg)
            res = self.conductor_execute(conductor_class_id, operation_id)
            return res

        # パラメータシートの指定があるパターン
        msg = g.appmsg.get_log_message("BKY-90074", [action_log_id])
        g.applogger.info(msg)

        action_parameters = json.loads(action_log_row.get("ACTION_PARAMETERS", "{}"))

        # ホスト名
        host_name = None
        is_use_event_host_name = action_log_row.get("EVENT_COLLABORATION", '0')

        if is_use_event_host_name != '0':
            host_name = action_parameters.get("_exastro_host", "")
        else:
            host_name = action_log_row.get("HOST_NAME", "")
        if not host_name:
            msg = g.appmsg.get_log_message("BKY-90075", ['host_name', action_log_id])
            return False, msg

        # パラメータを生成してAPIに投げる
        ret_bool, request_data = self.generate_parameter_4apply_api(action_log_id, conductor_class_name, operation_name, parameter_sheet_name_rest, host_name, action_parameters)
        if ret_bool is False:
            return ret_bool, request_data

        g.applogger.debug("request_parameters for apply_api: {}".format(request_data))
        res = self.apply_api(action_log_id, request_data)
        return res

    def conductor_execute(self, conductor_class_id, operation_id):
        """
        conductorを実行する（関数を呼ぶ）
        ARGS:
            wsDb:DB接続クラス  DBConnectWs()
            conductor_class_id:
            operation_id:
        RETURN:
        """
        objcbkl = ConductorExecuteBkyLibs(self.wsDb)  # noqa: F405
        parameter = {
            "conductor_class_id": conductor_class_id,
            "operation_id": operation_id
        }
        _res = objcbkl.conductor_execute_no_transaction(parameter)
        return _res

    def generate_parameter_4apply_api(self, action_log_id, conductor_class_name, operation_name, parameter_sheet_name_rest, host_name, action_parameters):
        ret_bool = False
        request_data = {}

        # メニュー（パラメータシート）のカラム情報を取得
        menu_record = self.wsDb.table_select('T_COMN_MENU', 'WHERE `MENU_NAME_REST` = %s AND `DISUSE_FLAG` = %s', [parameter_sheet_name_rest, 0])
        if len(menu_record) == 0:
            msg = g.appmsg.get_log_message("BKY-90075", ['parameter_sheet_name_rest', action_log_id])
            return ret_bool, msg

        menu_id = menu_record[0].get('MENU_ID')
        col_info_list = self.wsDb.table_select('T_COMN_MENU_COLUMN_LINK', 'WHERE  DISUSE_FLAG=%s AND MENU_ID = %s', ['0', menu_id])
        if len(col_info_list) == 0:
            msg = g.appmsg.get_log_message("BKY-90075", ['parameter_sheet_name_rest→menu_id', action_log_id])
            return ret_bool, msg

        # パラメータを作成
        parameter = {}
        for col_info in col_info_list:
            col_name_rest = col_info['COLUMN_NAME_REST']
            if col_info['COL_GROUP_ID'] in [None, '0000001']:
                continue

            # ラベルのキー名とパラメータシートのカラム名が一致するときのみ、値をセットする
            if col_name_rest in action_parameters.keys():
                # ラベルの値をセット
                parameter[col_name_rest] = action_parameters[col_name_rest]
            # else:
            #     msg = g.appmsg.get_log_message("BKY-90075", ['col_name_rest[{}]'.format(col_name_rest), action_log_id])
            #     return ret_bool, msg
        # ホスト名
        parameter['host_name'] = host_name

        parameter_info = {}
        parameter_info[parameter_sheet_name_rest] = {
            'type': "Register",
            'parameter': parameter
        }

        request_data = {
            "conductor_class_name": conductor_class_name,
            "parameter_info": parameter_info
        }
        if operation_name:
            request_data["operation_name"] = operation_name

        return True, request_data

    def apply_api(self, action_log_id, request_data):
        ret_bool = False

        try:
            apply.check_params(request_data)

            # チェック対象のメニューを抽出
            check_menu_list = ["operation_list", "conductor_class_edit"]
            specify_menu_list = apply.get_specify_menu(request_data)
            check_menu_list = list(set(check_menu_list) | set(specify_menu_list))

            # チェック項目の定義
            check_items = {}
            for menu in check_menu_list:
                if menu not in check_items:
                    check_items[menu] = {
                        "sheet_type": None,
                        "privilege": None,
                    }

                if menu == "conductor_class_edit":
                    check_items[menu]["sheet_type"] = ["14", "15"]
                    check_items[menu]["privilege"] = ["0", "1", "2"]

                elif menu == "operation_list":
                    check_items[menu]["sheet_type"] = ["0", ]
                    check_items[menu]["privilege"] = ["0", "1"]

                elif menu in specify_menu_list:
                    check_items[menu]["sheet_type"] = ["0", "1", "2", "3", "4"]
                    check_items[menu]["privilege"] = ["0", "1"]

            # トランザクション開始
            self.wsDb.db_transaction_start()

            # シートチェック
            parameter_sheet_list = []
            for menu, v in check_items.items():
                sheet_type = self.check_sheet_type(menu, v["sheet_type"])

                if sheet_type in ['1', '3', '4']:
                    parameter_sheet_list.append(menu)

            # loadTable生成用のメニュー一覧を作成
            loadtable_list = [
                "operation_list", "conductor_instance_list", "conductor_class_edit",
                "conductor_node_instance_list", "movement_list", "conductor_notice_definition",
            ]
            loadtable_list = list(set(specify_menu_list) | set(loadtable_list))

            # ロック対象の一覧を作成
            locktable_list = ["conductor_instance_list", "conductor_node_instance_list"]
            locktable_list = list(set(specify_menu_list) | set(locktable_list))

            # Conductor作業実行用のメニューのリストを作成
            conductor_menu_list = [
                "conductor_instance_list", "conductor_class_edit",
                "conductor_node_instance_list", "movement_list", "conductor_notice_definition",
            ]

            # パラメーター適用、および、Conductor作業実行
            status_code, result_data = apply.rest_apply_parameter(
                self.wsDb, request_data,
                loadtable_list, locktable_list, parameter_sheet_list, conductor_menu_list
            )
            if status_code == "000-00000":
                ret_bool = True
                self.wsDb.db_transaction_end(True)
            else:
                self.wsDb.db_transaction_end(False)
        except AppException as e:
            result_code, log_msg_args, api_msg_args = e.args
            log_msg = g.appmsg.get_log_message(result_code, log_msg_args)
            result_data = addline_msg('{}'.format(log_msg))
        except Exception as e:
            t = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
            log_msg = g.appmsg.get_log_message("BKY-90076", [action_log_id, e])
            result_data = addline_msg('{}'.format(log_msg))
        finally:
            self.wsDb.db_transaction_end(False)

        return ret_bool, result_data

    def check_sheet_type(self, menu, sheet_type_list):
        """
        check_sheet_type

        Arguments:
            menu: menu_name_rest
            sheet_type_list: (list)許容するシートタイプのリスト,falseの場合はシートタイプのチェックを行わない
        Returns:
            (dict)T_COMN_MENU_TABLE_LINKの該当レコード
        """

        query_str = textwrap.dedent("""
            SELECT * FROM `T_COMN_MENU_TABLE_LINK` TAB_A
                LEFT JOIN `T_COMN_MENU` TAB_B ON ( TAB_A.`MENU_ID` = TAB_B.`MENU_ID`)
            WHERE TAB_B.`MENU_NAME_REST` = %s AND
                TAB_A.`DISUSE_FLAG`='0' AND
                TAB_B.`DISUSE_FLAG`='0'
        """).strip()

        menu_table_link_record = self.wsDb.sql_execute(query_str, [menu])

        if not menu_table_link_record:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00003", log_msg_args, api_msg_args)  # noqa: F405

        sheet_type = menu_table_link_record[0].get('SHEET_TYPE')

        if sheet_type_list and sheet_type not in sheet_type_list:
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException("499-00001", log_msg_args, api_msg_args)  # noqa: F405

        return sheet_type
