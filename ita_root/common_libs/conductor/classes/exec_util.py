#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from flask import g
from common_libs.common.dbconnect import DBConnectWs  # noqa: F401

from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from common_libs.column import *  # noqa: F403

from common_libs.conductor.classes.util import ConductorCommonLibs  # noqa: F401

from common_libs.ansible_driver.functions.rest_libs import *  # noqa: F403
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst

import json
import uuid
import copy
import textwrap
import sys
import traceback

from pprint import pprint  # noqa: F401
import shutil

from datetime import datetime


bool_master_true = 'True'
bool_master_false = 'False'


class ConductorExecuteLibs():
    """
        ConductorExecuteLibs
        COnductor編集、作業実行関連
    """

    def __init__(self, objdbca, menu, objmenus, cmd_type='Register', target_uuid=''):

        # メニューID
        self.menu = menu
        
        # DB接続
        self.objdbca = objdbca

        # 環境情報
        self.lang = g.LANGUAGE
        
        # 各loadtableクラス
        self.objmenus = objmenus

        # 実行種別
        self.cmd_type = cmd_type

        # 対象conductorID
        self.target_uuid = target_uuid

        # orchestras_info
        self.orchestras_info = None
        self.set_orchestra_info()

    # conductor 編集,作業実行 関連
    def get_class_info_data(self, mode=""):
        """
            Conductor基本情報の取得
            ARGS:
                mode: "" (list key:[{id,name}] and dict key:{id:name}) or "all"  dict key:{rest_key:db rows})
            RETRUN:
                statusCode, {}, msg
        """

        try:
            lang_upper = self.lang.upper()
            
            dict_target_table = {
                "conductor_status": {
                    "table_name": "T_COMN_CONDUCTOR_STATUS",
                    "pk": "STATUS_ID",
                    "name": "STATUS_NAME_" + lang_upper,
                },
                "node_status": {
                    "table_name": "T_COMN_CONDUCTOR_NODE_STATUS",
                    "pk": "STATUS_ID",
                    "name": "STATUS_NAME_" + lang_upper,
                },
                "node_type": {
                    "table_name": "T_COMN_CONDUCTOR_NODE",
                    "pk": "NODE_TYPE_ID",
                    "name": "NODE_TYPE_NAME"
                },
                "movement": {
                    "table_name": "T_COMN_MOVEMENT",
                    "sql": '',
                    "pk": "MOVEMENT_ID",
                    "name": "MOVEMENT_NAME",
                    "sortkey": "TAB_A.MOVEMENT_NAME",
                    "orc_id": "ORCHESTRA_ID",
                    "orc_name": "ORCHESTRA_NAME"
                },
                "orchestra": {
                    "table_name": "T_COMN_ORCHESTRA",
                    "pk": "ORCHESTRA_ID",
                    "name": "ORCHESTRA_NAME",
                },
                "operation": {
                    "table_name": "T_COMN_OPERATION",
                    "pk": "OPERATION_ID",
                    "name": "OPERATION_NAME",
                    "sortkey": "OPERATION_NAME",
                },
                "conductor": {
                    "table_name": "T_COMN_CONDUCTOR_CLASS",
                    "pk": "CONDUCTOR_CLASS_ID",
                    "name": "CONDUCTOR_NAME",
                    "sortkey": "CONDUCTOR_NAME",
                },
                "refresh_interval": {
                    "table_name": "T_COMN_CONDUCTOR_IF_INFO",
                    "pk": "CONDUCTOR_IF_INFO_ID",
                    "refresh_interval": "CONDUCTOR_REFRESH_INTERVAL",
                    "sortkey": "CONDUCTOR_IF_INFO_ID",
                }
            }

            movement_sql = textwrap.dedent("""
                SELECT `TAB_A`.*, `TAB_B`.*
                FROM `T_COMN_MOVEMENT` `TAB_A`
                LEFT JOIN `T_COMN_ORCHESTRA` TAB_B ON (`TAB_A`.`ITA_EXT_STM_ID` = `TAB_B`.`ORCHESTRA_ID`)
                WHERE `TAB_A`.`DISUSE_FLAG` = 0 AND `TAB_B`.`DISUSE_FLAG` = 0
            """).format().strip()
            dict_target_table['movement']['sql'] = movement_sql

            result = {}
            result.setdefault('list', {})
            result.setdefault('dict', {})
            result.setdefault('dict_name', {})
            for target_key, target_table_info in dict_target_table.items():
                table_name = target_table_info.get('table_name')
                sortkey = target_table_info.get('sortkey')
                if sortkey is None:
                    sortkey = 'DISP_SEQ'
                sql_str = target_table_info.get('sql')

                pk_col = target_table_info.get('pk')
                name_col = target_table_info.get('name')
                refresh_interval = target_table_info.get('refresh_interval')
                orc_id = target_table_info.get('orc_id')
                orc_name = target_table_info.get('orc_name')

                where_str = target_table_info.get('join')
                if where_str is None:
                    where_str = ' WHERE `DISUSE_FLAG` = 0 ORDER BY `' + sortkey + '` ASC '
                else:
                    sql_str = sql_str + ' ORDER BY `' + sortkey + '` ASC '

                if sql_str is None:
                    rows = self.objdbca.table_select(table_name, where_str, [])
                else:
                    rows = self.objdbca.sql_execute(sql_str, [])

                if mode == '':
                    if target_key == 'refresh_interval':
                        result.setdefault('refresh_interval', rows[0].get(refresh_interval))
                    else:
                        result['dict'].setdefault(target_key, {})
                        result['list'].setdefault(target_key, [])
                        result['dict_name'].setdefault(target_key, {})
                        for row in rows:
                            id = row.get(pk_col)
                            name = row.get(name_col)
                            tmp_arr = {"id": id, "name": name}
                            if target_key == 'movement':
                                orchestra_id = row.get(orc_id)
                                orchestra_name = row.get(orc_name)
                                tmp_arr = {"id": id, "name": name}
                                tmp_arr.setdefault("orchestra_id", orchestra_id)
                                tmp_arr.setdefault("orchestra_name", orchestra_name)
                            result['dict'][target_key].setdefault(id, name)
                            result['list'][target_key].append(tmp_arr)
                            result['dict_name'][target_key].setdefault(name, id)
                else:
                    result.setdefault(target_key, {})
                    for row in rows:
                        id = row.get(pk_col)
                        result[target_key].setdefault(id, row)
                        name = row.get(name_col)
                        result[target_key].setdefault(name, row)
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)

            status_code = "499-00803"
            log_msg_args = []
            api_msg_args = []
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        return result

    def chk_execute_parameter_format(self, parameter):
        """
            Conductor 作業実行前のフォーマットチェック, (補完)
            ARGS:
                parameter: {'conductor_class_id':'', 'operation_id':'', schedule_date:'', 'conductor_data':{}}
            RETRUN:
                retBool, result, parameter
        """
        retBool = True
        result = None
        msg_ags = []
        try:
            # 優先順位 [conductor_class_name and operation_name] > [conductor_class_id and operation_id]
            # id and name は不正
            if 'conductor_class_name' in parameter and 'operation_name' in parameter:
                conductor_class_name = parameter.get('conductor_class_name')
                operation_name = parameter.get('operation_name')
                schedule_date = parameter.get('schedule_date')
                conductor_data = parameter.get('conductor_data')
                # conductor_class_name
                if conductor_class_name is not None:
                    table_name = 'T_COMN_CONDUCTOR_CLASS'
                    where_str = "where `CONDUCTOR_NAME` in (%s) and `DISUSE_FLAG` = 0 "
                    bind_value_list = [conductor_class_name]
                    tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
                    if len(tmp_result) != 1:
                        retBool = False
                        tmp_msg_ags = '{}:{}'.format('conductor_class_name', conductor_class_name)
                        msg_ags.append(tmp_msg_ags)
                    else:
                        parameter['conductor_class_id'] = tmp_result[0].get('CONDUCTOR_CLASS_ID')
                else:
                    retBool = False
                    tmp_msg_ags = '{}:{}'.format('conductor_class_name', conductor_class_name)
                    msg_ags.append(tmp_msg_ags)

                # operation_name
                if operation_name is not None:
                    table_name = 'T_COMN_OPERATION'
                    where_str = "where `OPERATION_NAME` in (%s) and `DISUSE_FLAG` = 0"
                    bind_value_list = [operation_name]
                    tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
                    if len(tmp_result) != 1:
                        retBool = False
                        tmp_msg_ags = '{}:{}'.format('operation_name', operation_name)
                        msg_ags.append(tmp_msg_ags)
                    else:
                        parameter['operation_id'] = tmp_result[0].get('OPERATION_ID')
                else:
                    tmp_msg_ags = '{}:{}'.format('operation_name', operation_name)
                    msg_ags.append(tmp_msg_ags)

            elif 'conductor_class_id' in parameter and 'operation_id' in parameter:
                conductor_class_id = parameter.get('conductor_class_id')
                operation_id = parameter.get('operation_id')
                schedule_date = parameter.get('schedule_date')
                conductor_data = parameter.get('conductor_data')

                # conductor_class_id
                if conductor_class_id is not None:
                    table_name = 'T_COMN_CONDUCTOR_CLASS'
                    where_str = "where `CONDUCTOR_CLASS_ID` in (%s) and `DISUSE_FLAG` = 0"
                    bind_value_list = [parameter.get('conductor_class_id')]
                    tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
                    if len(tmp_result) != 1:
                        retBool = False
                        tmp_msg_ags = '{}:{}'.format('conductor_class_id', conductor_class_id)
                        msg_ags.append(tmp_msg_ags)
                    else:
                        parameter['conductor_class_name'] = tmp_result[0].get('CONDUCTOR_NAME')
                else:
                    retBool = False
                    tmp_msg_ags = '{}:{}'.format('conductor_class_id', conductor_class_id)
                    msg_ags.append(tmp_msg_ags)

                # operation_id
                if operation_id is not None:
                    table_name = 'T_COMN_OPERATION'
                    where_str = "where `OPERATION_ID` in (%s) "
                    bind_value_list = [parameter.get('operation_id')]
                    tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
                    if len(tmp_result) != 1:
                        retBool = False
                        tmp_msg_ags = '{}:{}'.format('operation_id', operation_id)
                        msg_ags.append(tmp_msg_ags)
                    else:
                        parameter['operation_name'] = tmp_result[0].get('OPERATION_NAME')
                else:
                    tmp_msg_ags = '{}:{}'.format('operation_id', operation_id)
                    msg_ags.append(tmp_msg_ags)
            else:
                tmp_msg_ags = '{}'.format(parameter)
                msg_ags.append(tmp_msg_ags)
                raise Exception()

            # schedule_date
            if schedule_date is not None:
                if len(schedule_date) != 0:
                    try:
                        pattern = r'\b\d{4}/\d{2}/\d{2}\b \b\d{2}:\b\d{2}:\b\d{2}'
                        tmp_result = re.findall(pattern, schedule_date)  # noqa: F405
                        if len(tmp_result) != 1:
                            pattern = r'\b\d{4}/\d{2}/\d{2}\b \b\d{2}:\b\d{2}'
                            tmp_result = re.findall(pattern, schedule_date)  # noqa: F405
                            if len(tmp_result) != 1:
                                raise Exception()
                            else:
                                tmp_schedule_date = tmp_result[0] + ':00'
                        else:
                            tmp_schedule_date = tmp_result[0]
                        datetime.strptime(tmp_schedule_date, '%Y/%m/%d %H:%M:%S')
                    except Exception:
                        retBool = False
                        tmp_msg_ags = '{}:{}'.format('schedule_date', schedule_date)
                        msg_ags.append(tmp_msg_ags)
                        
            # conductor_data
            if conductor_data is not None:
                if isinstance(conductor_data, dict) is not True:
                    retBool = False
                    tmp_msg_ags = '{}'.format('conductor_data')
                    msg_ags.append(tmp_msg_ags)
            if len(msg_ags) != 0:
                raise Exception()
        except Exception:
            result = [', '.join(msg_ags)]
            status_code = '499-00814'
            log_msg_args = result
            api_msg_args = result
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        return retBool, result, parameter,

    def create_execute_register_parameter(self, parameter, parent_conductor_instance_id=None):
        """
            Conductor実行(パラメータ生成)
            ARGS:
                parameter:パラメータ  {}
                parent_conductor_instance_id:親conductorID string
            RETRUN:
                data
        """
        
        try:
            status_code = "000-00000"
            lang = g.LANGUAGE
            lang_upper = lang.upper()
            
            conductor_instance_id = ''
            conductor_parameter = {}
            node_parameters = []
            
            objmovement = self.objmenus.get('objmovement')
            objcclass = self.objmenus.get('objcclass')
            objconductor = self.objmenus.get('objconductor')

            # Conductor基本情報取得
            mode = "all"
            get_list_data = self.get_class_info_data(mode)
            # maintenance用パラメータ値生成
            # user_id = g.USER_ID
            user_name = g.USER_ID

            # 作業実行ユーザー名
            objcolumn = load_objcolumn(self.objdbca, objconductor.objtable, 'execution_user', 'LastUpdateUserColumn')
            if objcolumn is not False:
                tmp_result = objcolumn.convert_value_output(g.USER_ID)
                if tmp_result[0] is True:
                    user_name = tmp_result[2]
            else:
                raise Exception()

            # conductor_instance_id 発番
            conductor_instance_id = str(uuid.uuid4())
            # parameterから取得
            conductor_class_id = parameter.get('conductor_class_id')
            operation_id = parameter.get('operation_id')
            conductor_class_name = parameter.get('conductor_class_name')
            operation_name = parameter.get('operation_name')
            schedule_date = parameter.get('schedule_date')
            p_conductor_data = parameter.get('conductor_data')
            
            # DB上のconductor_data取得
            db_conductor_data = json.loads(get_list_data.get('conductor').get(conductor_class_id).get('SETTING'))

            # conductor_data 要素数チェック+上書き設定
            conductor_data = self.override_conductor_data(p_conductor_data, db_conductor_data)

            # conductor_dataのバリデーション + IDから名称を現時点に最新化
            cclibs = ConductorCommonLibs()
            tmp_result = cclibs.override_node_idlink(copy.deepcopy(conductor_data))
            if tmp_result[0] is False:
                raise Exception()
            conductor_data = tmp_result[1]

            if 'id' in conductor_data.get('conductor'):
                tmp_conductor_data_id = conductor_data.get('conductor').get('id')
            if conductor_class_id != tmp_conductor_data_id:
                raise Exception()
            
            # schedule_date 簡易チェック
            if schedule_date is not None:
                schedule_date_len = len(str(schedule_date))
                if schedule_date_len == 0:
                    schedule_date = None

            # operation_id 簡易チェック
            if operation_id in get_list_data.get('operation'):
                operation_name = get_list_data.get('operation').get(operation_id).get('OPERATION_NAME')
            else:
                raise Exception()

            # conductor_class_id 簡易チェック, conductor名, 備考(作業実行画面優先)
            if conductor_class_id in get_list_data.get('conductor'):
                conductor_name = get_list_data.get('conductor').get(conductor_class_id).get('CONDUCTOR_NAME')
                conductor_remarks = get_list_data.get('conductor').get(conductor_class_id).get('NOTE')
                if 'note' in conductor_data.get('conductor'):
                    conductor_remarks = conductor_data.get('conductor').get('note')
            else:
                raise Exception()

            # Conductor初期ステータス設定(未実行,未実行(予約))
            if schedule_date is None:
                conductor_status_name = get_list_data.get('conductor_status').get('1').get('STATUS_NAME_' + lang_upper)
            else:
                conductor_status_name = get_list_data.get('conductor_status').get('2').get('STATUS_NAME_' + lang_upper)

            # Node初期ステータス設定(未実行,未実行(予約))
            node_status_name = get_list_data.get('node_status').get('1').get('STATUS_NAME_' + lang_upper)

            # 変更前(conductor_class)のconductor_data
            org_conductor_data = json.loads(get_list_data.get('conductor').get(conductor_class_id).get('SETTING'))

            # 登録日時
            time_register = get_now_datetime()
            
            # callされている場合
            if parent_conductor_instance_id is not None:
                # Conductor instance id / name 取得
                # id / name 取得(親)
                tmp_result = self.get_filter_conductor(parent_conductor_instance_id)
                if tmp_result[0] is not True:
                    raise Exception()
                parent_conductor_instance_name = tmp_result[1].get('parameter').get('instance_source_class_name')
                tmp_result = self.get_filter_conductor_parent(parent_conductor_instance_id)
                if tmp_result[0] is not True:
                    raise Exception()
                # id / name 取得(最上位)
                tmp_result = self.get_filter_conductor_top_parent(parent_conductor_instance_id, parent_conductor_instance_name)
                if tmp_result[0] is not True:
                    raise Exception()
                top_conductor_instance_id = tmp_result[1].get('parent_id')
                top_conductor_instance_name = tmp_result[1].get('parent_name')
                user_name = tmp_result[1].get('execution_user')
            else:
                # 通常実行時
                parent_conductor_instance_id = None
                parent_conductor_instance_name = None
                top_conductor_instance_id = None
                top_conductor_instance_name = None

            bool_master_true = 'True'
            bool_master_false = 'False'

            # load_table用(conductor_instance_list)パラメータ生成
            c_parameter = {
                "conductor_instance_id": conductor_instance_id,
                "conductor_instance_name": conductor_name,
                "instance_source_class_id": conductor_class_id,
                "instance_source_class_name": conductor_name,
                "instance_source_settings": org_conductor_data,
                "instance_source_remarks": conductor_remarks,
                "class_settings": conductor_data,
                "operation_id": operation_id,
                "operation_name": operation_name,
                "execution_user": user_name,
                "parent_conductor_instance_id": parent_conductor_instance_id,
                "parent_conductor_instance_name": parent_conductor_instance_name,
                "top_conductor_instance_id": top_conductor_instance_id,
                "top_conductor_instance_name": top_conductor_instance_name,
                # "notice_info": None,
                # "notice_definition": None,
                "status_id": conductor_status_name,
                "abort_execute_flag": bool_master_false,
                "time_register": time_register,
                "time_book": schedule_date,
                # "time_start": None,
                # "time_end": None,
                "execution_log": [],
                # "notification_log": None,
                "remarks": conductor_remarks
                # "discard": 0,
                # "last_updated_user": user_id,
            }

            conductor_parameter = {
                'file': {},
                'parameter': c_parameter,
                "type": "Register"
            }
            # load_table用(conductor_node_instance_list)パラメータ生成
            # node用ベースパラメータ
            base_node_parameter = {
                "node_instance_id": None,
                "instance_source_node_name": None,
                "instance_source_remarks": None,
                "node_type": None,
                # "movement_type": None,
                # "instance_source_movement_id": None,
                # "instance_source_movement_name": None,
                # "instance_source_movement_info": None,
                # "instance_source_conductor_id": None,
                # "instance_source_conductor_name": None,
                # "instance_source_conductor_info": None,
                "conductor_instance_id": conductor_instance_id,
                "parent_conductor_instance_id": parent_conductor_instance_id,
                "parent_conductor_instance_name": parent_conductor_instance_name,
                "top_conductor_instance_id": top_conductor_instance_id,
                "top_conductor_instance_name": top_conductor_instance_name,
                "execution_id": None,
                "status_id": node_status_name,
                # "status_file": None,
                "released_flag": bool_master_false,
                "skip": bool_master_false,
                # "end_type": None,
                # "operation_id": None,
                # "operation_name": None,
                "time_register": time_register,
                # "time_start": None,
                # "time_end": None,
                "remarks": None,
                "discard": "0",
                # "last_update_date_time": None,
                # "last_updated_user": None,
            }

            # 各nodeのパラメータ
            node_data = copy.deepcopy(conductor_data)
            node_parameters = []
            for node_name, node_info in node_data.items():
                # nodeのみ対象(line conductor config 除く)
                if 'node-' in node_name:
                    # 共通項目
                    n_parameter = copy.deepcopy(base_node_parameter)
                    node_type = node_info.get('type')
                    n_parameter["node_instance_id"] = str(uuid.uuid4())
                    n_parameter["instance_source_node_name"] = node_name
                    n_parameter["instance_source_remarks"] = node_info.get('note')
                    n_parameter["node_type"] = node_type
                    n_parameter["remarks"] = node_info.get('note')
                    
                    # Movement項目
                    if node_type in ["movement"]:
                        orchestra_id = get_list_data.get('orchestra').get(node_info.get('orchestra_id')).get('ORCHESTRA_NAME')
                        movement_id = node_info.get('movement_id')
                        movement_name = get_list_data.get('movement').get(movement_id).get('MOVEMENT_NAME')
                        filter_parameter = {"movement_id": {"LIST": [movement_id]}}
                        tmp_movement = objmovement.rest_filter(filter_parameter)
                        if tmp_movement[0] == '000-00000':
                            movement_class_json = tmp_movement[1][0]
                        else:
                            movement_class_json = []
                        n_parameter["movement_type"] = orchestra_id
                        n_parameter["instance_source_movement_id"] = movement_id
                        n_parameter["instance_source_movement_name"] = movement_name
                        n_parameter["instance_source_movement_info"] = movement_class_json
                    # Call項目
                    if node_type in ["call"]:
                        if isinstance(node_info.get('call_conductor_id'), list):
                            n_conductor_class_id = node_info.get('call_conductor_id')[0]
                        else:
                            n_conductor_class_id = node_info.get('call_conductor_id')
                        n_conductor_class_name = get_list_data.get('conductor').get(n_conductor_class_id).get('CONDUCTOR_NAME')
                        filter_parameter = {"conductor_class_id": {"LIST": [n_conductor_class_id]}}
                        tmp_conductor = objcclass.rest_filter(filter_parameter)
                        if tmp_conductor[0] == '000-00000':
                            conductor_class_json = tmp_conductor[1][0]
                        else:
                            conductor_class_json = []
                        n_parameter["instance_source_conductor_id"] = n_conductor_class_id
                        n_parameter["instance_source_conductor_name"] = n_conductor_class_name
                        n_parameter["instance_source_conductor_info"] = conductor_class_json

                    # 個別OP,SKIP
                    if node_type in ["movement", "call"]:
                        skip_flag = node_info.get('skip_flag')
                        if skip_flag is not None:
                            if skip_flag in [1, '1']:
                                n_parameter["skip"] = bool_master_true
                        
                        node_operation_id = node_info.get('operation_id')
                        if isinstance(node_info.get('operation_id'), list):
                            node_operation_id = node_info.get('operation_id')[0]
                        else:
                            node_operation_id = node_info.get('operation_id')
                        if node_operation_id is not None:
                            if node_operation_id in get_list_data.get('operation'):
                                node_operation_name = get_list_data.get('operation').get(node_operation_id).get('OPERATION_NAME')
                        else:
                            node_operation_id = None
                            node_operation_name = None
                        n_parameter["operation_id"] = node_operation_id
                        n_parameter["operation_name"] = node_operation_name

                    # 終了タイプ
                    if node_type in ["end"]:
                        end_type = node_info.get('end_type')
                        if end_type is not None:
                            if end_type in get_list_data.get('conductor_status'):
                                end_type_name = get_list_data.get('conductor_status').get(end_type).get('STATUS_NAME_' + lang_upper)
                                n_parameter["end_type"] = end_type_name
                        else:
                            end_type_name = get_list_data.get('conductor_status').get('6').get('STATUS_NAME_' + lang_upper)
                            n_parameter["end_type"] = end_type_name

                    node_parameter = {
                        'file': {},
                        'parameter': copy.deepcopy(n_parameter),
                        "type": "Register"
                    }
                    node_parameters.append(node_parameter)

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            if parameter.get('conductor_class_name') is None:
                conductor_class_id = parameter.get('conductor_class_name')
                operation_id = parameter.get('operation_name')
            else:
                conductor_class_id = parameter.get('conductor_class_id')
                operation_id = parameter.get('operation_id')
            schedule_date = parameter.get('schedule_date')
            status_code = "499-00804"
            log_msg_args = [conductor_class_id, operation_id, schedule_date]
            api_msg_args = [conductor_class_id, operation_id, schedule_date]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        status_code = "000-00000"

        result = {
            "conductor_instance_id": conductor_instance_id,
            "conductor": conductor_parameter,
            "node": node_parameters
        }

        return status_code, result,

    def override_conductor_data(self, p_conductor_data, db_conductor_data):
        """
            conductor_dataの設定上書き
            ARGS:
                p_conductor_data:from parameter
                db_conductor_data:from db
            RETRUN:
                conductor_data
        """
        try:
            # 上書き無し
            if p_conductor_data is None or p_conductor_data == '':
                conductor_data = db_conductor_data
            elif len(p_conductor_data) == 0:
                conductor_data = db_conductor_data
            else:
                if len(p_conductor_data) != len(db_conductor_data):
                    chk_or_mode = 'accept_or_key'
                else:
                    chk_or_mode = 'all'

                if chk_or_mode == 'accept_or_key':
                    # dbのデータに,上書き対象のみ上書き+不許可は、対象外,エラー
                    accept_or_key_list = ['note', 'operation_id', 'call_conductor_id']
                    for cnodeid, cinfo in p_conductor_data.items():
                        if 'node' in cnodeid:
                            if cnodeid in db_conductor_data:
                                if cnodeid == db_conductor_data.get(cnodeid).get('id'):
                                    if (cinfo.get('id') is not None) and (cinfo.get('id') != db_conductor_data.get(cnodeid).get('id')):
                                        # node-id変更による不整合回避
                                        raise Exception()
                                    else:
                                        for ck, cv in cinfo.items():
                                            if ck in accept_or_key_list and ck != 'id':
                                                db_conductor_data[cnodeid][ck] = cv
                                else:
                                    # node-id変更による不整合回避
                                    raise Exception()
                            else:
                                # node-id変更による不整合回避
                                raise Exception()
                    conductor_data = db_conductor_data
                else:
                    # dbのデータに、パラメータを上書き
                    db_conductor_data.update(p_conductor_data)
                    conductor_data = db_conductor_data
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            raise e

        return conductor_data

    # maintenance関連
    def conductor_class_exec_maintenance(self, conductor_parameter, target_uuid='', cmd_type=''):
        """
            Conductor登録, 更新(conductorclassの登録,更新)
            ARGS:
                conductor_parameter:conductorパラメータ
            RETRUN:
                bool, data
        """
        tmp_result = None
        msg = ''
        try:
            if target_uuid == '':
                target_uuid = self.target_uuid
            if cmd_type == '':
                cmd_type = self.cmd_type
                
            objcclass = self.objmenus.get('objcclass')
            # maintenance呼び出し(pk uuid.uuid()を外部実行 )
            tmp_result = objcclass.exec_maintenance(conductor_parameter, target_uuid, cmd_type, True, False)
            objcclass.set_error_message()
            if tmp_result[0] is not True:
                raise Exception()

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            tmp_result = False,
        return tmp_result

    def conductor_instance_exec_maintenance(self, conductor_parameter, target_uuid='', cmd_type=''):
        """
            Conductor実行(conductorinstanceの登録,更新)
            ARGS:
                conductor_parameter:conductorパラメータ
            RETRUN:
                bool, data
        """
        try:
            if target_uuid == '':
                target_uuid = self.target_uuid
            if cmd_type == '':
                cmd_type = self.cmd_type
                
            objconductor = self.objmenus.get('objconductor')
            # maintenance呼び出し(pk uuid.uuid()を外部実行 )
            tmp_result = objconductor.exec_maintenance(conductor_parameter, target_uuid, cmd_type, True, False)
            objconductor.set_error_message()
            if tmp_result[0] is not True:
                return tmp_result
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            tmp_result = False,
        return tmp_result

    def node_instance_exec_maintenance(self, node_parameters, cmd_type=''):
        """
            Conductor実行(node instanceの登録,更新)
            ARGS:
                node_parameters:nodeパラメータ list
            RETRUN:
                bool, data
        """

        try:
            objnode = self.objmenus.get('objnode')

            for tmp_parameters in node_parameters:
                parameters = tmp_parameters
                target_uuid = ''
                if 'node_instance_id' in parameters.get('parameter'):
                    target_uuid = parameters.get('parameter').get('node_instance_id')
                    if target_uuid is None:
                        target_uuid = ''
                        
                if cmd_type == '':
                    cmd_type = self.cmd_type

                # maintenance呼び出し
                tmp_result = objnode.exec_maintenance(parameters, target_uuid, cmd_type, False, False)
                objnode.set_error_message()
                if tmp_result[0] is not True:
                    return tmp_result
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            tmp_result = False,

        return tmp_result

    def maintenance_error_message_format(self, msg):
        """
            Conductor登録, 更新のエラーメッセージフォーマット
            ARGS:
                msg:message
            RETRUN:
                bool, msg
        """
        result = {}
        try:
            try:
                msg_json = {}
                tmp_msg_json = json.loads(msg)
                for eno, errinfo in tmp_msg_json.items():
                    for ekey, einfo in errinfo.items():
                        if ekey != g.appmsg.get_api_message("MSG-00004", []):
                            msg_json.setdefault(ekey, einfo)
                        else:
                            for node_err in einfo:
                                try:
                                    node_err_json = json.loads(node_err)
                                    for tmp_node_err in node_err_json:
                                        try:
                                            tmp_node_err_json = json.loads(tmp_node_err)
                                            for node_name, node_msg in tmp_node_err_json.items():
                                                msg_json.setdefault(node_name, node_msg.splitlines())
                                        except Exception:
                                            msg_json.setdefault(g.appmsg.get_api_message("MSG-00004", []), tmp_node_err)
                                except Exception:
                                    msg_json.setdefault(g.appmsg.get_api_message("MSG-00004", []), node_err)
                result = json.dumps(msg_json, ensure_ascii=False)
            except Exception:
                result = msg
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            result = False,
        return result

    # conductor 作業関連
    def get_instance_info_data(self, conductor_instance_id='', mode=''):
        """
            Conductor作業確認用の基本情報の取得
            ARGS:
                conductor_instance_id:作業id
                    conductor_instance_id=''の時 conductor,operation,movement以外取得
                mode: "" (list key:[{id,name}] and dict key:{id:name}) or "all"  dict key:{rest_key:rows})
            RETRUN:
                {}
        """

        try:
            lang_upper = self.lang.upper()
                
            dict_target_table = {
                "conductor_status": {
                    "table_name": "T_COMN_CONDUCTOR_STATUS",
                    "pk": "STATUS_ID",
                    "name": "STATUS_NAME_" + lang_upper,
                },
                "node_status": {
                    "table_name": "T_COMN_CONDUCTOR_NODE_STATUS",
                    "pk": "STATUS_ID",
                    "name": "STATUS_NAME_" + lang_upper,
                },
                "node_type": {
                    "table_name": "T_COMN_CONDUCTOR_NODE",
                    "pk": "NODE_TYPE_ID",
                    "name": "NODE_TYPE_NAME"
                },
                "orchestra": {
                    "table_name": "T_COMN_ORCHESTRA",
                    "pk": "ORCHESTRA_ID",
                    "name": "ORCHESTRA_NAME",
                },
                "refresh_interval": {
                    "table_name": "T_COMN_CONDUCTOR_IF_INFO",
                    "pk": "CONDUCTOR_IF_INFO_ID",
                    "refresh_interval": "CONDUCTOR_REFRESH_INTERVAL",
                    "sortkey": "CONDUCTOR_IF_INFO_ID",
                }
            }

            result = {}
            result.setdefault('list', {})
            result.setdefault('dict', {})
            result.setdefault('dict_name', {})
            for target_key, target_table_info in dict_target_table.items():
                table_name = target_table_info.get('table_name')
                sortkey = target_table_info.get('sortkey')
                if sortkey is None:
                    sortkey = 'DISP_SEQ'
                sql_str = target_table_info.get('sql')

                pk_col = target_table_info.get('pk')
                name_col = target_table_info.get('name')
                refresh_interval = target_table_info.get('refresh_interval')
                orc_id = target_table_info.get('orc_id')
                orc_name = target_table_info.get('orc_name')

                where_str = target_table_info.get('join')
                if where_str is None:
                    where_str = ' WHERE `DISUSE_FLAG` = 0 ORDER BY `' + sortkey + '` ASC '
                else:
                    sql_str = sql_str + ' ORDER BY `' + sortkey + '` ASC '

                if sql_str is None:
                    rows = self.objdbca.table_select(table_name, where_str, [])
                else:
                    rows = self.objdbca.sql_execute(sql_str, [])

                if mode == '':
                    if target_key == 'refresh_interval':
                        result.setdefault('refresh_interval', rows[0].get(refresh_interval))
                    else:
                        result['dict'].setdefault(target_key, {})
                        result['list'].setdefault(target_key, [])
                        result['dict_name'].setdefault(target_key, {})
                        for row in rows:
                            id = row.get(pk_col)
                            name = row.get(name_col)
                            tmp_arr = {"id": id, "name": name}
                            if target_key == 'movement':
                                orchestra_id = row.get(orc_id)
                                orchestra_name = row.get(orc_name)
                                tmp_arr = {"id": id, "name": name}
                                tmp_arr.setdefault("orchestra_id", orchestra_id)
                                tmp_arr.setdefault("orchestra_name", orchestra_name)
                            result['dict'][target_key].setdefault(id, name)
                            result['list'][target_key].append(tmp_arr)
                            result['dict_name'].setdefault(target_key, {})
                            result['dict_name'][target_key].setdefault(name, id)
                else:
                    result.setdefault(target_key, {})
                    for row in rows:
                        id = row.get(pk_col)
                        result[target_key].setdefault(id, row)
                        name = row.get(name_col)
                        result[target_key].setdefault(name, row)
            # 作業に関連する、Conductor、Movement、Operationのリスト
            objconductor = self.objmenus.get('objconductor')
            objnode = self.objmenus.get('objnode')

            # conductor instanceから一覧生成
            filter_parameter = {
                "conductor_instance_id": {"LIST": [conductor_instance_id]}
            }
            result['dict'].setdefault('conductor', {})
            result['list'].setdefault('conductor', [])
            result['dict'].setdefault('operation', {})
            result['list'].setdefault('operation', [])
            result['dict'].setdefault('movement', {})
            result['list'].setdefault('movement', [])
            result['dict_name'].setdefault('conductor', {})
            result['dict_name'].setdefault('operation', {})
            result['dict_name'].setdefault('movement', {})
            if conductor_instance_id != '':
                result_ci_filter = objconductor.rest_filter(filter_parameter)
                if result_ci_filter[0] == '000-00000':
                    for tmp_ci in result_ci_filter[1]:
                        ci_p = tmp_ci.get('parameter')
                        # conductor
                        id = ci_p.get('instance_source_class_id')
                        name = ci_p.get('instance_source_class_name')
                        tmp_arr = {"id": id, "name": name}
                        result['dict']['conductor'].setdefault(id, name)
                        result['list']['conductor'].append(tmp_arr)
                        p_id = ci_p.get('parent_conductor_instance_id')
                        p_name = ci_p.get('parent_conductor_instance_name')
                        if p_id is not None and p_name is not None:
                            tmp_arr = {"id": p_id, "name": p_name}
                            result['dict']['conductor'].setdefault(p_id, p_name)
                            result['list']['conductor'].append(tmp_arr)
                            result['dict_name']['conductor'].setdefault(name, id)

                        # operation
                        id = ci_p.get('operation_id')
                        name = ci_p.get('operation_name')
                        tmp_arr = {"id": id, "name": name}
                        result['dict']['operation'].setdefault(id, name)
                        result['list']['operation'].append(tmp_arr)
                        result['dict_name']['operation'].setdefault(name, id)
                # node instanceからクラス一覧生成
                filter_parameter = {
                    "conductor_instance_id": {"LIST": [conductor_instance_id]}
                }
                result_ni_filter = objnode.rest_filter(filter_parameter)
                if result_ni_filter[0] == '000-00000':
                    for tmp_ni in result_ni_filter[1]:
                        ni_p = tmp_ni.get('parameter')

                        # movement
                        id = ni_p.get('instance_source_movement_id')
                        name = ni_p.get('instance_source_movement_name')
                        if id is not None and name is not None:
                            tmp_arr = {"id": id, "name": name}
                            result['dict']['movement'].setdefault(id, name)
                            result['list']['movement'].append(tmp_arr)
                            result['dict_name']['movement'].setdefault(name, id)
                            
                        # conductor
                        id = ni_p.get('instance_source_conductor_id')
                        name = ni_p.get('instance_source_conductor_name')
                        if id is not None and name is not None:
                            tmp_arr = {"id": id, "name": name}
                            result['dict']['conductor'].setdefault(id, name)
                            result['list']['conductor'].append(tmp_arr)
                            result['dict_name']['conductor'].setdefault(name, id)

                        # operation
                        id = ni_p.get('operation_id')
                        name = ni_p.get('operation_name')
                        if id is not None and name is not None:
                            tmp_arr = {"id": id, "name": name}
                            result['dict']['operation'].setdefault(id, name)
                            result['list']['operation'].append(tmp_arr)
                            result['dict_name']['operation'].setdefault(name, id)
                        
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            status_code = "499-00803"
            log_msg_args = []
            api_msg_args = []
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        return result

    def get_instance_data(self, conductor_instance_id):
        """
            対象のConductor作業の設定、ステータス取得
            ARGS:
                conductor_instance_id:作業id
            RETRUN:
                {}
        """

        try:

            result = {}
            result.setdefault('conductor_class', {})
            result.setdefault('conductor', {})
            result.setdefault('node', {})
            
            objconductor = self.objmenus.get('objconductor')
            objnode = self.objmenus.get('objnode')

            instance_info_data = self.get_instance_info_data(conductor_instance_id)
            c_status_names = instance_info_data.get('dict_name').get('conductor_status')
            n_status_names = instance_info_data.get('dict_name').get('node_status')

            conductor_status = {}
            class_settings = {}
            node_status = {}

            tmp_result = self.is_conductor_instance_id(conductor_instance_id)
            if tmp_result is False:
                raise Exception()

            orchestra_info = self.get_orchestra_info()
            # conductor
            filter_parameter = {
                "conductor_instance_id": {"LIST": [conductor_instance_id]}
            }
            result_ci_filter = objconductor.rest_filter(filter_parameter)
            if result_ci_filter[0] == '000-00000':
                if len(result_ci_filter[1]) == 1:
                    for tmp_ci in result_ci_filter[1]:
                        ci_p = tmp_ci.get('parameter')
                        class_settings = ci_p.get('class_settings')
                        conductor_status = {
                            "conductor_instance_id": ci_p.get('conductor_instance_id'),
                            "conductor_name": ci_p.get('instance_source_class_name'),
                            "status": ci_p.get('status_id'),
                            "status_id": c_status_names.get(ci_p.get('status_id')),
                            "execution_user": ci_p.get('execution_user'),
                            "abort_execute_flag": ci_p.get('abort_execute_flag'),
                            "operation_id": ci_p.get('operation_id'),
                            "operation_name": ci_p.get('operation_name'),
                            "time_book": ci_p.get('time_book'),
                            "time_start": ci_p.get('time_start'),
                            "time_end": ci_p.get('time_end'),
                            "execution_log": ci_p.get('execution_log'),
                            "remarks": ci_p.get('remarks'),
                        }

            # node instanceからクラス一覧生成
            filter_parameter = {
                "conductor_instance_id": {"LIST": [conductor_instance_id]}
            }
            result_ni_filter = objnode.rest_filter(filter_parameter)
            if result_ni_filter[0] == '000-00000':
                for tmp_ni in result_ni_filter[1]:
                    ni_p = tmp_ni.get('parameter')
                    node_name = ni_p.get('instance_source_node_name')
                    # 各作業確認のメニュー
                    jump_menu_id = None
                    jump_url = None
                    tmp_orchestra = instance_info_data.get('dict').get('orchestra')
                    movement_type = ni_p.get('movement_type')
                    execution_id = ni_p.get('execution_id')
                    if movement_type is not None:
                        tmp_orchestra_id = [k for k, v in tmp_orchestra.items() if v == movement_type]
                        tmp_orchestra_id = tmp_orchestra_id[0]
                        jump_menu_id = orchestra_info.get('id').get(tmp_orchestra_id).get('menu')
                        if execution_id is not None:
                            jump_url = "menu={}&execution_no={}".format(jump_menu_id, execution_id)
                    else:
                        jump_menu_id = 'conductor_confirmation'
                        if execution_id is not None:
                            jump_url = "menu={}&conductor_instance_id={}".format(jump_menu_id, execution_id)

                    tmp_node_status = {
                        "node_instance_id": ni_p.get('node_instance_id'),
                        "node_name": ni_p.get('instance_source_node_name'),
                        "node_type": ni_p.get('node_type'),
                        "status": ni_p.get('status_id'),
                        "status_id": n_status_names.get(ni_p.get('status_id')),
                        "status_file": ni_p.get('status_file'),
                        "skip": ni_p.get('skip'),
                        "remarks": ni_p.get('remarks'),
                        "time_start": ni_p.get('time_start'),
                        "time_end": ni_p.get('time_end'),
                        "operation_id": ni_p.get('operation_id'),
                        "operation_name": ni_p.get('operation_name'),
                        "jump": {
                            "menu_id": jump_menu_id,
                            "execution_id": execution_id,
                        },
                        "jump_url": jump_url,
                    }

                    node_status.setdefault(node_name, tmp_node_status)

            result['conductor_class'] = class_settings
            result['conductor'] = conductor_status
            result['node'] = node_status
            
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            status_code = "499-00803"
            log_msg_args = []
            api_msg_args = []
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        return result

    def is_conductor_instance_id(self, conductor_instance_id):
        """
            作業対象のConductorの確認
            ARGS:
                conductor_instance_id: conductor_instance_id
            RETRUN:
                retBool
        """
        retBool = True
        result = {}
        try:
            retBool, result = self.get_filter_conductor(conductor_instance_id)
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool

    def get_filter_conductor(self, conductor_instance_id):
        """
            作業対象のConductorを取得(FILTER)
            ARGS:
                conductor_instance_id: conductor_instance_id
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        try:
            objconductor = self.objmenus.get('objconductor')
            filter_parameter = {
                "conductor_instance_id": {"LIST": [conductor_instance_id]}
            }
            tmp_result = objconductor.rest_filter(filter_parameter)
            if tmp_result[0] != '000-00000':
                retBool = False
            if len(tmp_result[1]) == 1:
                result = tmp_result[1][0]
            else:
                retBool = False
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_filter_conductor_parent(self, parent_conductor_instance_id):
        """
            作業対象の親Conductorを取得(FILTER)
            ARGS:
                conductor_instance_id: conductor_instance_id
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        try:
            tmp_result = self.get_filter_conductor(parent_conductor_instance_id)
            if tmp_result[0] is not True:
                retBool = False
            parent_id = tmp_result[1].get('parameter').get('parent_conductor_instance_id')
            parent_name = tmp_result[1].get('parameter').get('parent_conductor_instance_name')
            execution_user = tmp_result[1].get('parameter').get('execution_user')
            result.setdefault('parent_id', parent_id)
            result.setdefault('parent_name', parent_name)
            result.setdefault('execution_user', execution_user)
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_filter_conductor_top_parent(self, parent_conductor_instance_id=None, parent_conductor_instance_name=None):
        """
            作業対象の最上位のConductorを取得(FILTER)
            ARGS:
                parent_conductor_instance_id: conductor_instance_id
                parent_conductor_instance_name: conductor_instance_name
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        parent_id = parent_conductor_instance_id
        parent_name = parent_conductor_instance_name
        execution_user = ""

        try:
            while parent_id is not None:
                tmp_result = self.get_filter_conductor_parent(parent_id)
                if tmp_result[0] is True:
                    tmp_parent_id = tmp_result[1].get('parent_id')
                    tmp_parent_name = tmp_result[1].get('parent_name')
                    execution_user = tmp_result[1].get('execution_user')
                    if tmp_parent_id is None:
                        result.setdefault('parent_id', parent_id)
                        result.setdefault('parent_name', parent_name)
                        result.setdefault('execution_user', execution_user)
                        break
                    else:
                        parent_id = tmp_parent_id
                        parent_name = tmp_parent_name
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def execute_action(self, mode='', conductor_instance_id='', node_instance_id=''):
        """
            Conductor作業に対する個別処理(cancel,scram,relese)
            ARGS:
                mode: "" (list key:[{id,name}] and dict key:{id:name}) or "all"  dict key:{rest_key:rows})
                conductor_instance_id: string
                node_instance_id: string
            RETRUN:
                retBool, status_code, msg_args,
        """

        try:
            retBool = True
            status_code = '000-00000'
            msg_args = []

            bool_master_true = 'True'
            bool_master_false = 'False'

            instance_info_data = self.get_instance_info_data(conductor_instance_id)
            
            objconductor = self.objmenus.get('objconductor')
            objnode = self.objmenus.get('objnode')
            tmp_parameter = {}
            
            if conductor_instance_id != '':
                filter_parameter = {
                    "conductor_instance_id": {"LIST": [conductor_instance_id]}
                }
                result_ci_filter = objconductor.rest_filter(filter_parameter)
                if result_ci_filter[0] == '000-00000':
                    if len(result_ci_filter[1]) == 1:
                        ci_p = result_ci_filter[1][0].get('parameter')
                        ci_last_update_date_time = ci_p.get('last_update_date_time')
                        ci_status_id = ci_p.get('status_id')
                        ci_abort_execute_flag = ci_p.get('abort_execute_flag')
            if node_instance_id != '':
                # node instanceからクラス一覧生成
                filter_parameter = {
                    "conductor_instance_id": {"LIST": [conductor_instance_id]},
                    "node_instance_id": {"LIST": [node_instance_id]}
                    # "node_type": {"LIST": ["pause"]},
                }
                result_ni_filter = objnode.rest_filter(filter_parameter)
                
                if result_ni_filter[0] == '000-00000':
                    if len(result_ni_filter[1]) == 1:
                        ni_p = result_ni_filter[1][0].get('parameter')
                        ni_released_flag = ni_p.get('released_flag')
                        ni_node_type = ni_p.get('node_type')
                        ni_last_update_date_time = ni_p.get('last_update_date_time')
                        ni_status_id = ni_p.get('status_id')
                    else:
                        status_code = "499-00807"
                        msg_args = ["", conductor_instance_id, node_instance_id]
                        raise Exception()  # noqa: F405
                else:
                    status_code = "499-00807"
                    msg_args = ["", conductor_instance_id, node_instance_id]
                    raise Exception()  # noqa: F405

            if mode == 'cancel':
                # ステータス変更(未実行(予約)→予約取消)
                status_id = instance_info_data.get('dict').get('conductor_status').get('10')
                cancel_accept_status = instance_info_data.get('dict').get('conductor_status').get('2')
                # 未実行(予約)の時のみ
                if ci_status_id == cancel_accept_status:
                    tmp_parameter.setdefault('conductor_instance_id', conductor_instance_id)
                    tmp_parameter.setdefault('last_update_date_time', ci_last_update_date_time)
                    tmp_parameter.setdefault('status_id', status_id)
                    conductor_parameter = {
                        "file": {},
                        "parameter": tmp_parameter
                    }
                    tmp_result = objconductor.exec_maintenance(conductor_parameter, conductor_instance_id, 'Update', False, False)
                    objconductor.set_error_message()
                    if tmp_result[0] is not True:
                        status_code = "499-00807"
                        msg_args = [mode, conductor_instance_id, ci_status_id]
                        raise Exception()  # noqa: F405
                else:
                    status_code = "499-00808"
                    msg_args = [conductor_instance_id, ci_status_id]
                    raise Exception()  # noqa: F405

            elif mode == 'scram':
                # 緊急停止フラグON
                scram_accept_status = [
                    instance_info_data.get('dict').get('conductor_status').get('3'),
                    instance_info_data.get('dict').get('conductor_status').get('4'),
                    instance_info_data.get('dict').get('conductor_status').get('5')
                ]
                if ci_status_id in scram_accept_status:
                    if ci_abort_execute_flag != bool_master_false:
                        status_code = "499-00810"
                        msg_args = [conductor_instance_id, ci_status_id, ci_abort_execute_flag]
                        raise Exception()  # noqa: F405
                    tmp_parameter.setdefault('conductor_instance_id', conductor_instance_id)
                    tmp_parameter.setdefault('last_update_date_time', ci_last_update_date_time)
                    tmp_parameter.setdefault('abort_execute_flag', bool_master_true)
                    conductor_parameter = {
                        "file": {},
                        "parameter": tmp_parameter
                    }
                    tmp_result = objconductor.exec_maintenance(conductor_parameter, conductor_instance_id, 'Update', False, False)
                    objconductor.set_error_message()
                    if tmp_result[0] is not True:
                        status_code = "499-00807"
                        msg_args = [mode, conductor_instance_id, ci_status_id]
                        raise Exception()  # noqa: F405
                else:
                    status_code = "499-00809"
                    msg_args = [conductor_instance_id, ci_status_id]
                    raise Exception()  # noqa: F405

            elif mode == 'relese':
                if ni_node_type == "pause":
                    if ni_released_flag == bool_master_false:
                        released_accept_status = instance_info_data.get('dict').get('node_status').get('11')
                        if ni_status_id == released_accept_status:
                            status_id = instance_info_data.get('dict').get('node_status').get('3')
                            tmp_parameter.setdefault('last_update_date_time', ni_last_update_date_time)
                            tmp_parameter.setdefault('status_id', status_id)
                            tmp_parameter.setdefault('released_flag', bool_master_true)
                            tmp_parameter.setdefault('node_instance_id', node_instance_id)
                            node_parameter = {
                                "file": {},
                                "parameter": tmp_parameter
                            }
                            tmp_result = objnode.exec_maintenance(node_parameter, node_instance_id, 'Update', False, False)
                            objconductor.set_error_message()
                            if tmp_result[0] is not True:
                                status_code = "499-00807"
                                msg_args = [mode, node_instance_id, ci_status_id]
                                raise Exception()  # noqa: F405
                        else:
                            status_code = "499-00813"
                            msg_args = [conductor_instance_id, node_instance_id, ni_status_id]
                            raise Exception()  # noqa: F405
                    else:
                        status_code = "499-00812"
                        msg_args = [conductor_instance_id, node_instance_id]
                        raise Exception()  # noqa: F405
                else:
                    status_code = "499-00811"
                    msg_args = [conductor_instance_id, node_instance_id, ni_node_type]
                    raise Exception()  # noqa: F405

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False

        return retBool, status_code, msg_args,

    # orchestra関連
    def set_orchestra_info(self):
        """
            storage path 設定
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        try:
            tmp_result = self.get_orchestra_data()
            if tmp_result[0] is not True:
                raise Exception()
            self.orchestras_info = tmp_result[1]
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_orchestra_info(self):
        """
            storage path 設定
            RETRUN:
                retBool, result,
        """
        return self.orchestras_info

    def get_orchestra_data(self):
        """
            orchestra情報取得
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        result.setdefault('id', {})
        result.setdefault('name', {})

        try:
            tmp_result = self.get_orchestra_action_info()
            if tmp_result[0] is False:
                raise Exception()
            orchestra_action_info = tmp_result[1]
            
            table_name = 'T_COMN_ORCHESTRA'
            where_str = ""
            bind_value_list = []
            tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
            for row in tmp_result:
                orchestra_id = row.get('ORCHESTRA_ID')
                orchestra_name = row.get('ORCHESTRA_NAME')
                orchestra_path = row.get('ORCHESTRA_PATH')
                # orchestra_id->driver_idの紐付
                if orchestra_id in ["1", "Ansible Legacy"]:
                    driver_id = AnscConst.DF_LEGACY_DRIVER_ID
                    manu_id = ""
                if orchestra_id in ["2", "Ansible Pioneer"]:
                    driver_id = AnscConst.DF_PIONEER_DRIVER_ID
                    manu_id = ""
                if orchestra_id in ["3", "Ansible Legacy Role"]:
                    driver_id = AnscConst.DF_LEGACY_ROLE_DRIVER_ID
                    manu_id = "20412"

                result['id'].setdefault(
                    orchestra_id,
                    {
                        "id": orchestra_id,
                        "name": orchestra_name,
                        "path": orchestra_path,
                        "driver_id": driver_id,
                        "manu_id": manu_id,
                    }
                )

                result['name'].setdefault(
                    orchestra_name,
                    {
                        "id": orchestra_id,
                        "name": orchestra_name,
                        "path": orchestra_path,
                        "driver_id": driver_id,
                        "manu_id": manu_id,
                    }
                )
                action_info = orchestra_action_info.get(orchestra_id)
                result['id'][orchestra_id].update(action_info)
                result['name'][orchestra_name].update(action_info)
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_orchestra_action_info(self):
        """
            各orchestraの実行処理毎の設定
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}

        try:
            result = {
                "1": {
                    'menu': 'check_operation_status_ansible',
                    'path': 'ansible/legacy',
                    'execute': 'T_COMN_MOVEMENT',
                    'abort': '',
                    'status': ''
                },
                "2": {
                    'menu': 'check_operation_status_ansible_pioneer',
                    'path': 'ansible/pioneer',
                    'execute': 'T_COMN_MOVEMENT',
                    'post_abort': '',
                    'status': ''
                },
                "3": {
                    'menu': 'check_operation_status_ansible_role',
                    'path': 'ansible/legacy_role',
                    'execute': 'T_COMN_MOVEMENT',
                    'abort': '',
                    'status': 'T_ANSR_EXEC_STS_INST'
                },
                "4": {
                    'menu': '',
                    'execute': 'T_COMN_MOVEMENT',
                    'abort': '',
                    'status': ''
                }
            }

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,


class ConductorExecuteBkyLibs(ConductorExecuteLibs):
    """
        ConductorExecuteLibs
        COnductor作業実行処理関連
    """
    def __init__(self, objdbca=''):
        
        # DB接続
        self.objdbca = objdbca

        # 環境情報
        self.lang = g.LANGUAGE

        # 各loadtableクラス
        self.objmenus = False
        self.set_objmenus()

        # Conductor変更後のステータス
        self.conductor_update_status = {}

        # Conductor変更後のmsg
        self.conductor_update_msg = {}

        # メニューID
        self.menu = ''

        # 実行種別
        self.cmd_type = ''

        # 対象conductorID
        self.target_uuid = ''
        
        # user id
        self.user_id = g.USER_ID

        # organization_id
        self.organization_id = g.ORGANIZATION_ID

        # workspace_id
        self.workspace_id = g.WORKSPACE_ID
        
        # conductor_storage_path
        self.conductor_storage_path = None
        # base path
        self.base_storage_path = None

        # orchestras_info
        self.orchestras_info = None
        self.set_orchestra_info()

    # self関連
    def set_objmenus(self):
        """
            objmenus初期設定
                loadtable関連
                    conductor_interface_information
                    conductor_instance_list
                    conductor_node_instance_list
                    conductor_class_edit
                    movement_list
        """
        try:
            if_menu = 'conductor_interface_information'
            c_menu = 'conductor_instance_list'
            n_menu = 'conductor_node_instance_list'
            cc_menu = 'conductor_class_edit'
            m_menu = 'movement_list'
            
            objconductorif = load_table.loadTable(self.objdbca, if_menu)  # noqa: F405
            objconductor = load_table.loadTable(self.objdbca, c_menu)  # noqa: F405
            objnode = load_table.loadTable(self.objdbca, n_menu)  # noqa: F405
            objcclass = load_table.loadTable(self.objdbca, cc_menu)  # noqa: F405
            objmovement = load_table.loadTable(self.objdbca, m_menu)  # noqa: F405
            if (objconductor.get_objtable() is False or
                    objnode.get_objtable() is False or
                    objconductorif.get_objtable() is False or
                    objcclass.get_objtable() is False or
                    objmovement.get_objtable() is False):
                raise Exception()

            objmenus = {
                "objconductor": objconductor,
                "objnode": objnode,
                "objconductorif": objconductorif,
                "objcclass": objcclass,
                "objmovement": objmovement,
            }
            self.objmenus = objmenus
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            self.objmenus = False

    def get_objmenus(self):
        """
            objmenus取得
            RETRUN:
                self.objmenus
        """
        return self.objmenus

    def set_conductor_update_status(self, conductor_instance_id, status_id):
        """
            conductor_update_status を設定
            ARGS:
                conductor_instance_id:
                status_id:
        """
        if conductor_instance_id in self.conductor_update_status:
            self.conductor_update_status[conductor_instance_id] = status_id
        else:
            self.conductor_update_status.setdefault(conductor_instance_id, status_id)

    def get_conductor_update_status(self, conductor_instance_id):
        """
            conductor_update_status取得
            ARGS:
                conductor_instance_id:
            RETRUN:
                self.conductor_update_status.get(conductor_instance_id)
        """
        return self.conductor_update_status.get(conductor_instance_id)

    def set_conductor_update_msg(self, conductor_instance_id, rest_key, msg):
        """
            conductor_update_msg を設定
            ARGS:
                conductor_instance_id:
                status_id:
        """
        if conductor_instance_id in self.conductor_update_status:
            if rest_key in self.conductor_update_status[conductor_instance_id]:
                if isinstance(self.conductor_update_msg[conductor_instance_id][rest_key], list):
                    self.conductor_update_msg[conductor_instance_id][rest_key].append(msg)
                else:
                    self.conductor_update_msg[conductor_instance_id][rest_key] = [msg]
            else:
                self.conductor_update_msg.setdefault(conductor_instance_id, {})
                self.conductor_update_msg[conductor_instance_id].setdefault(rest_key, [])
                self.conductor_update_msg[conductor_instance_id][rest_key].append(msg)
        else:
            self.conductor_update_msg.setdefault(conductor_instance_id, {})
            self.conductor_update_msg[conductor_instance_id].setdefault(rest_key, [])
            self.conductor_update_msg[conductor_instance_id][rest_key].append(msg)

    def get_conductor_update_msg(self, conductor_instance_id, rest_key):
        """
            conductor_update_msg取得
            ARGS:
                conductor_instance_id:
            RETRUN:
                self.conductor_update_msg.get(conductor_instance_id)
        """
        try:
            msg = self.conductor_update_msg.get(conductor_instance_id).get(rest_key)
        except Exception:
            msg = []
        return msg

    def get_storage_path(self):
        """
            storage path 生成
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        try:
            tmp_result = self.get_conductor_interface()
            if tmp_result[0] is not True:
                raise Exception()
            strage_path = os.environ.get('STORAGEPATH')  # noqa: F405
            tmp_conductor_storage_path = '%%%%%ITA_DRIVER_DIRECTORY%%%%%/driver/conductor'
            # tmp_result[1].get('CONDUCTOR_STORAGE_PATH_ITA')
            base_storage_path = "{}/{}/{}/".format(strage_path, self.organization_id, self.workspace_id).replace('//', '/')
            conductor_storage_path = tmp_conductor_storage_path.replace('%%%%%ITA_DRIVER_DIRECTORY%%%%%', base_storage_path).replace('//', '/')
            base_conductor_storage_path = "{}".format(conductor_storage_path).replace('//', '/')
            result.setdefault('base_storage_path', base_storage_path)
            result.setdefault('base_conductor_storage_path', base_conductor_storage_path)

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def set_storage_path(self):
        """
            storage path 設定
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        try:
            tmp_result = self.get_storage_path()
            if tmp_result[0] is not True:
                raise Exception()
            base_storage_path = tmp_result[1].get('base_storage_path')
            base_conductor_storage_path = tmp_result[1].get('base_conductor_storage_path')
            self.base_storage_path = base_storage_path
            self.conductor_storage_path = base_conductor_storage_path
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_conductor_storage_path(self):
        """
            conductor_storage_path 取得
            RETRUN:
                self.conductor_storage_path
        """
        return self.conductor_storage_path

    def get_base_storage_path(self):
        """
            base_storage_path 取得
            RETRUN:
                self.base_storage_path
        """
        return self.base_storage_path
    
    # Conductor instance 関連(取得,判定)
    def get_conductor_interface(self):
        """
            conductor interface情報取得
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        try:
            table_name = 'T_COMN_CONDUCTOR_IF_INFO'
            where_str = ""
            bind_value_list = []
            tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
            if len(tmp_result) == 1:
                result = tmp_result[0]
            else:
                retBool = False
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def create_data_storage_path(self, data_storage_path, status_id=''):
        """
            conductor data_storage_pathの作成
            ARGS:
                data_storage_path:
                status_id:
            RETRUN:
                retBool
        """
        retBool = True
        try:
            tmp_isdir = os.path.isdir(data_storage_path)  # noqa: F405
            if tmp_isdir is False:
                # パスにディレクトリ無ければ作成
                os.makedirs(data_storage_path, exist_ok=True)  # noqa: F405
                tmp_msg = 'makedirs {}'.format(data_storage_path)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            elif tmp_isdir is True and status_id in ['1', '2']:
                # 未実行、未実行(予約)時　and パスにディレクトリがあれば、空にしてディレクトリ作成
                shutil.rmtree(data_storage_path)
                os.makedirs(data_storage_path, exist_ok=True)  # noqa: F405
                tmp_msg = 'rmtree -> makedirs {}'.format(data_storage_path)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool

    def get_execute_conductor_list(self, limit=''):
        """
            作業対象のID、ステータスを取得
            ARGS:
                limit:num
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        try:
            table_name = 'T_COMN_CONDUCTOR_INSTANCE'
            where_str = "where `STATUS_ID` in ( %s,%s,%s,%s,%s ) "
            and_str = " AND ( `TIME_BOOK` <= %s OR `TIME_BOOK` IS NULL )"
            order_str = " ORDER BY `TIME_REGISTER` ASC "
            where_str = where_str + and_str + order_str
            bind_value_list = [1, 2, 3, 4, 5, get_now_datetime()]

            if limit != '':
                if str(limit).isnumeric() is True:
                    where_str = where_str + ' LIMIT %s'
                    bind_value_list.append(limit)
            
            tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
            for row in tmp_result:
                result.setdefault(
                    row.get('CONDUCTOR_INSTANCE_ID'),
                    {
                        "id": row.get('CONDUCTOR_INSTANCE_ID'),
                        "status": row.get('STATUS_ID')
                    }
                )
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def chk_conductor_start(self, node_instance_id, target_all_node_list):
        """
            作業対象のSTARTNode開始済みか判定
            ARGS:
                node_instance_id: node_instance_id
                target_all_node_list: {status_id:[node_instance_id,,,,,]}
            RETRUN:
                retBool, result,
        """
        retBool = True
        try:
            if node_instance_id in target_all_node_list['status']['1']:
                retBool = True
            else:
                retBool = False
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool

    def chk_conductor_end(self, conductor_instance_id):
        """
            作業対象Conductorの終了チェック
            ARGS:
                conductor_instance_id: conductor_instance_id
            RETRUN:
                retBool
        """
        retBool = True

        try:
            # 参照系リスト取得
            instance_info_data = self.get_instance_info_data()
            instance_data = self.get_instance_data(conductor_instance_id)
            # 正常終了
            conductor_end_status = '6'

            # 全ENDNodeのステータス取得
            tmp_result = self.get_all_end_node(conductor_instance_id)
            if tmp_result[0] is not True:
                raise Exception()
            # all_end_node_list = tmp_result[1]
            # ENDNodeの終了タイプ
            # end_types = all_end_node_list.get('end_types')

            # 全Nodeからの終了ステータスを判定
            # 全Nodeのステータス取得
            tmp_result = self.chk_all_node_status_info(conductor_instance_id)
            if tmp_result[0] is not True:
                raise Exception()
            all_node_status_info = tmp_result[1]
            node_cnt = all_node_status_info.get('node_cnt')
            status_count = all_node_status_info.get('status_count')
            exec_node_cnt = all_node_status_info.get('exec_node_cnt')
            nomal_end_cnt = all_node_status_info.get('nomal_end_cnt')
            end_node_type_list = all_node_status_info.get('end_node_type_list')
            error_node_conditional_flg = all_node_status_info.get('error_node_conditional_flg')
            exec_node = all_node_status_info.get('exec_node')

            # 実施中Node数
            exec_node_cnt = len(status_count.get('2')) + len(status_count.get('3')) + len(status_count.get('4')) + len(status_count.get('11'))
            # 正常終了Node数
            nomal_end_cnt = len(status_count.get('5')) + len(status_count.get('13'))
            # 異常終了系Node数
            # error_node_cnt = len(status_count.get('6')) + len(status_count.get('7')) + len(status_count.get('8')) + len(status_count.get('12'))

            # 実施中なら終了させない
            if exec_node_cnt != 0:
                if error_node_conditional_flg is True:
                    retBool = False
                    return retBool,
                else:
                    # conditional無しで異常系終了時の待ち
                    for node_name in exec_node:
                        node_instance_id = instance_data.get('node').get(node_name).get('node_instance_id')
                        node_type = instance_data.get('node').get(node_name).get('node_type')
                        # 実行中のNodeを異常終了に変更(movement, call以外)
                        if node_type not in ['call', 'movement']:
                            # 最新再取得
                            tmp_result = self.get_filter_node_one(conductor_instance_id, node_instance_id)
                            if tmp_result[0] is False:
                                raise Exception()
                            node_filter_data = tmp_result[1]
                            
                            n_status_id = instance_info_data.get('dict').get('node_status').get('6')
                            # Node更新
                            node_filter_data['parameter']['status_id'] = n_status_id
                            # Node Update
                            tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                            if tmp_result[0] is not True:
                                raise Exception()
                        else:
                            # 実行中のmovement, callのステータス反映待ち
                            retBool = False
                            return retBool,

            if nomal_end_cnt == node_cnt:
                # START->END 完走
                retBool = True
            elif nomal_end_cnt <= node_cnt:
                abort_execute_flag = instance_data.get('conductor').get('abort_execute_flag')
                # 緊急停止発令時
                if abort_execute_flag == bool_master_true:
                    conductor_end_status = '9'
                # START->終了系
                elif len(status_count.get('12')) != 0 or len(status_count.get('6')) != 0:
                    # 異常終了へ(異常終了、準備エラー)
                    conductor_end_status = '7'
                elif len(status_count.get('8')) != 0:
                    # 緊急停止へ
                    conductor_end_status = '9'
                elif len(status_count.get('7')) != 0:
                    # 想定外エラーへ
                    conductor_end_status = '11'

            # 正常終了時、ENDNodeのend_typeで上書き
            if len(end_node_type_list) != 0:
                if conductor_end_status in ['6', '7', '8', '9', '11']:
                    if '9' in end_node_type_list:
                        conductor_end_status = '9'
                    elif '7' in end_node_type_list:
                        conductor_end_status = '7'
                    elif '8' in end_node_type_list:
                        conductor_end_status = '8'
                    elif '6' in end_node_type_list:
                        conductor_end_status = '6'

            # Conductor終了ステータス設定
            c_status_id = instance_info_data.get('dict').get('conductor_status').get(conductor_end_status)
            self.set_conductor_update_status(conductor_instance_id, c_status_id)

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool,

    def chk_all_node_status_info(self, conductor_instance_id):
        """
            全ノードのステータス集計チェック
            ARGS:
                conductor_instance_id: conductor_instance_id
            RETRUN:
                retBool, result
        """
        retBool = True
        result = {}
        try:
            # 参照系リスト取得
            instance_info_data = self.get_instance_info_data()
            instance_data = self.get_instance_data(conductor_instance_id)
                        
            # 全Nodeからの終了ステータスを判定
            # 全Nodeのステータス取得
            tmp_result = self.get_execute_all_node_list(conductor_instance_id)
            if tmp_result[0] is not True:
                raise Exception()
            target_all_node_list = tmp_result[1]
            status_count = {}
            status_count.setdefault("1", [])
            status_count.setdefault("2", [])
            status_count.setdefault("3", [])
            status_count.setdefault("4", [])
            status_count.setdefault("5", [])
            status_count.setdefault("6", [])
            status_count.setdefault("7", [])
            status_count.setdefault("8", [])
            status_count.setdefault("11", [])
            status_count.setdefault("12", [])
            status_count.setdefault("13", [])
            
            # ステータス毎振り分け
            node_cnt = 0
            end_node_type_list = []
            error_node_conditional_flg = True
            for node_id, node_info in target_all_node_list.get('node_list').items():
                status_id = node_info.get('status')
                status_count[status_id].append(node_id)
                node_type = node_info.get('node_type')
                end_type = node_info.get('end_type')
                # 完了(正常終了以外)のMomvent,call で次がconditional
                if status_id in ['6', '7', '8', '12', '14'] and node_type in ['movement', 'call']:
                    node_name = node_info.get('node_name')
                    target_in_out_node = self.get_in_out_node(conductor_instance_id, node_name)
                    if target_in_out_node is not False:
                        # 次のNodeにConditional含むか判定
                        for tname, tinfo in target_in_out_node.get('out').items():
                            tnode = tinfo.get('targetNode')
                            tnode_type = instance_data.get('conductor_class').get(tnode).get('type')
                            if tnode_type == 'conditional-branch':
                                error_node_conditional_flg = True
                            else:
                                error_node_conditional_flg = False

                if status_id in ['5'] and node_type == 'end':
                    end_node_type_list.append(end_type)
                
                # Node総数
                node_cnt = node_cnt + 1

            # 実施中Node数
            exec_node_cnt = len(status_count.get('2')) + len(status_count.get('3')) + len(status_count.get('4')) + len(status_count.get('11'))
            # 正常終了Node数
            nomal_end_cnt = len(status_count.get('5')) + len(status_count.get('13'))
            # 異常終了系Node数
            # error_node_cnt = len(status_count.get('6')) + len(status_count.get('7')) + len(status_count.get('8')) + len(status_count.get('12'))
            
            # 実施中Node
            exec_node = []
            exec_node.extend(status_count.get('3'))
            exec_node.extend(status_count.get('4'))
            exec_node = set(exec_node)

            result.setdefault("node_cnt", node_cnt)
            result.setdefault("status_count", status_count)
            result.setdefault("exec_node_cnt", exec_node_cnt)
            result.setdefault("nomal_end_cnt", nomal_end_cnt)
            result.setdefault("end_node_type_list", end_node_type_list)
            result.setdefault("error_node_conditional_flg", error_node_conditional_flg)
            result.setdefault("exec_node", exec_node)

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_abort_status(self, conductor_instance_id):
        """
            緊急停止済みか判定
            ARGS:
                conductor_instance_id: conductor_instance_id
            RETRUN:
                'False' / 'True'
        """
        abort_flag = 'False'
        try:
            table_name = 'T_COMN_CONDUCTOR_INSTANCE'
            where_str = "where `CONDUCTOR_INSTANCE_ID` in (%s) "
            bind_value_list = [conductor_instance_id]
            tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
            if len(tmp_result) == 1:
                abort_flag = tmp_result[0].get('ABORT_EXECUTE_FLAG')
                if abort_flag is None:
                    abort_flag = 'False'
                else:
                    if abort_flag in [1, "1"]:
                        abort_flag = 'True'
        except Exception:
            abort_flag = 'False'
        return abort_flag

    def get_system_config(self):
        """
            system stttings 情報取得
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        try:
            table_name = 'T_COMN_SYSTEM_CONFIG'
            where_str = ""
            bind_value_list = []
            tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
            for row in tmp_result:
                result.setdefault(row.get('CONFIG_ID'), row.get('VALUE'))

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def add_execution_log(self, parameter, str_msg=''):
        """
            execution_logへのmsg追加
            ARGS:
                parameter:
                msg:
            RETRUN:
            parameter
        """
        retBool = True
        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))
            tmp_str_execution_log = parameter['parameter']['execution_log']
            tmp_execution_log_list = []
            if tmp_str_execution_log is None:
                tmp_execution_log_list = [str_msg]
            elif isinstance(tmp_str_execution_log, list):
                tmp_execution_log_list = tmp_str_execution_log.append(str_msg)
            elif isinstance(tmp_str_execution_log, str):
                try:
                    tmp_execution_log_list = json.loads(tmp_str_execution_log)
                    if isinstance(tmp_execution_log_list, list):
                        tmp_execution_log_list.append(str_msg)
                    else:
                        tmp_execution_log_list = [str_msg]
                except Exception:
                    tmp_execution_log_list = [str_msg]
            if tmp_execution_log_list is not None:
                if len(tmp_execution_log_list) != 0:
                    # parameter['parameter']['execution_log'] = json.dumps(tmp_execution_log_list, ensure_ascii=False)
                    parameter['parameter']['execution_log'] = tmp_execution_log_list
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, parameter,

    def get_execute_mv_node_list(self, conductor_instance_id):
        """
            作業対象ConductorのMovementの作業IDを取得
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}

        try:
            # 作業実行している+処理終了しているNode(call/movement)
            table_name = 'T_COMN_CONDUCTOR_NODE_INSTANCE'
            where_str = textwrap.dedent("""
                WHERE `CONDUCTOR_INSTANCE_ID` = %s
                AND `NODE_TYPE_ID` IN ('call', 'movement')
                AND `STATUS_ID` IN ('5', '6', '7', '8', '12', '13', '14')
                AND `EXECUTION_ID` IS NOT NULL
            """)
            
            bind_value_list = [conductor_instance_id]
            tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)

            for row in tmp_result:
                node_type = row.get('NODE_TYPE_ID')
                execution_id = row.get('EXECUTION_ID')
                orchestra_id = row.get('ORCHESTRA_ID')
                if node_type == 'movement' and execution_id is not None:
                    # 実行済みMovement
                    result.setdefault(
                        execution_id,
                        {
                            "orchestra_id": orchestra_id,
                            "execution_id": execution_id
                        }
                    )
                elif node_type == 'call' and execution_id is not None:
                    # 実行済みcallは、関連Conductor先まで
                    tmp_result = self.get_execute_mv_node_list(execution_id)
                    if tmp_result[0] is True:
                        if len(tmp_result[1]) != 0:
                            result.update(tmp_result[1])
            # result = list(set(result))

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def create_zip_data(self, conductor_instance_id, data_type='', execution_data={}):
        """
        作業対象のファイル取得+ZIP化+base64
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        driver_name = 'Conductor'
        ext = 'zip'
        tmp_work_dir_path = ''
        
        try:
            # data_typeから取得対象判別
            if data_type == 'input':
                target_datatype = {'input': {"prefix": "InputData", "target_dir": "in"}}
            elif data_type == 'result':
                target_datatype = {'result': {"prefix": "ResultData", "target_dir": "out"}}
            else:
                raise Exception()

            # 一時作業ディレクトリ指定
            tmp_work_dir = uuid.uuid4()
            strage_path = os.environ.get('STORAGEPATH')  # noqa: F405
            tmp_work_dir_path = "{}/{}/{}/tmp/{}".format(
                strage_path,
                self.organization_id,
                self.workspace_id,
                tmp_work_dir
            ).replace('//', '/')
            
            for tmp_data_type, tmp_data_info in target_datatype.items():
                # prefix
                tmp_data_prefix = tmp_data_info.get('prefix')
                tmp_target_dir = tmp_data_info.get('target_dir')
                # ZIP対象ディレクトリ
                tmp_work_path = "{}/{}/".format(
                    tmp_work_dir_path,
                    tmp_data_type
                ).replace('//', '/')
                
                # 出力ファイル名 prefix_Conductor_id
                tmp_file_name = "{}_{}_{}".format(
                    tmp_data_prefix,
                    driver_name,
                    conductor_instance_id
                ).replace('//', '/')
                
                # 出力ファイルパス path_prefix_Conductor_id
                tmp_work_path_filename = "{}/{}".format(
                    tmp_work_dir_path,
                    tmp_file_name
                ).replace('//', '/')
                
                # ZIPファイル path/name
                zip_file_path = "{}.{}".format(tmp_work_path_filename, ext)
                zip_file_name = "{}.{}".format(tmp_file_name, ext)
                
                # 一時作業ディレクトリ作成、掃除
                tmp_isdir = os.path.isdir(tmp_work_path)  # noqa: F405
                if tmp_isdir is False:
                    os.makedirs(tmp_work_path, exist_ok=True)  # noqa: F405
                else:
                    shutil.rmtree(tmp_work_path)
                    os.makedirs(tmp_work_path, exist_ok=True)  # noqa: F405

                # 対象MVの作業関連ファイルを一時作業ディレクトリへCP
                for execution_id, execution_info in execution_data.items():
                    orchestra_id = execution_info.get('orchestra_id')
                    movement_path = self.get_movement_path(orchestra_id, execution_id)
                    target_movement_path = movement_path[1].get(tmp_target_dir)
                    target_mv_zip = "{}/{}_{}.zip".format(target_movement_path, tmp_data_prefix, execution_id)
                    if os.path.isfile(target_mv_zip) is True:  # noqa: F405
                        shutil.copy2(target_mv_zip, tmp_work_path + '/')

                # 全MVをzip化,base64
                tmp_result = shutil.make_archive(tmp_work_path_filename, ext, root_dir=tmp_work_path)

                with open(tmp_result, "rb") as f:
                    zip_base64_str = base64.b64encode(f.read()).decode('utf-8')  # noqa: F405

                result.setdefault('file_name', zip_file_name)
                result.setdefault('file_data', zip_base64_str)

                if os.path.isfile(zip_file_path) is True:  # noqa: F405
                    os.remove(zip_file_path)  # noqa: F405

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False

        finally:
            # 一時作業ディレクトリ掃除
            if tmp_work_dir_path != '':
                if os.path.isdir(tmp_work_dir_path) is True:  # noqa: F405
                    shutil.rmtree(tmp_work_dir_path)

        return retBool, result,

    def create_movement_zip(self, conductor_instance_id, data_type=''):
        """
            作業対象ConductorのMVのZIPファイルbase64化
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        try:
            tmp_result = self.is_conductor_instance_id(conductor_instance_id)
            if tmp_result is False:
                raise Exception()
            
            # 対象MV取得
            tmp_result = self.get_execute_mv_node_list(conductor_instance_id)
            if tmp_result[0] is not True:
                raise Exception()
            
            execution_data = tmp_result[1]
            if len(execution_data) == 0:
                raise Exception()
            
            # ZIPファイル生成＋base64化
            tmp_result = self.create_zip_data(conductor_instance_id, data_type, execution_data)
            if tmp_result[0] is not True:
                raise Exception()

            zipdata = tmp_result[1]
            result = zipdata
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    # Node instance 関連(取得,判定)
    def get_execute_all_node_list(self, conductor_instance_id):
        """
            作業対象ConductorのNodeを取得
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        result.setdefault('node', {})
        result.setdefault('status', {})
        result['status'].setdefault("1", [])
        result['status'].setdefault("2", [])
        result['status'].setdefault("3", [])
        result['status'].setdefault("4", [])
        result['status'].setdefault("5", [])
        result['status'].setdefault("6", [])
        result['status'].setdefault("7", [])
        result['status'].setdefault("8", [])
        result['status'].setdefault("11", [])
        result['status'].setdefault("12", [])
        result['status'].setdefault("13", [])

        try:
            table_name = 'T_COMN_CONDUCTOR_NODE_INSTANCE'
            where_str = "where `CONDUCTOR_INSTANCE_ID` = %s "
            bind_value_list = [conductor_instance_id]
            tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
            result.setdefault('node_list', {})
            for row in tmp_result:
                result['node'].setdefault(
                    row.get('NODE_INSTANCE_ID'),
                    {
                        "id": row.get('NODE_INSTANCE_ID'),
                        "node_name": row.get('I_NODE_NAME'),
                        "status": row.get('STATUS_ID'),
                        "node_type": row.get('NODE_TYPE_ID'),
                        "end_type": row.get('END_TYPE')
                    }
                )
                result['status'][row.get('STATUS_ID')].append(row.get('NODE_INSTANCE_ID'))

                result['node_list'].setdefault(
                    row.get('I_NODE_NAME'),
                    {
                        "id": row.get('NODE_INSTANCE_ID'),
                        "node_name": row.get('I_NODE_NAME'),
                        "status": row.get('STATUS_ID'),
                        "node_type": row.get('NODE_TYPE_ID'),
                        "end_type": row.get('END_TYPE')
                    }
                )
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_start_node(self, conductor_instance_id):
        """
            作業対象のSTARTNodeを取得
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        try:
            table_name = 'T_COMN_CONDUCTOR_NODE_INSTANCE'
            where_str = "where `CONDUCTOR_INSTANCE_ID` = %s and `NODE_TYPE_ID` = %s "
            bind_value_list = [conductor_instance_id, "start"]
            tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
            if len(tmp_result) == 1:
                result = tmp_result[0]['NODE_INSTANCE_ID']
            else:
                retBool = False
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_filter_node(self, conductor_instance_id):
        """
            作業対象のNodeを取得(FILTER)
            ARGS:
                conductor_instance_id: conductor_instance_id
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        result.setdefault('id', {})
        result.setdefault('name', {})
        try:
            objnode = self.objmenus.get('objnode')
            filter_parameter = {
                "conductor_instance_id": {"LIST": [conductor_instance_id]}
            }
            tmp_result = objnode.rest_filter(filter_parameter)
            if tmp_result[0] != '000-00000':
                raise Exception()
            result_ni_filter = tmp_result[1]
            # node_instance_id , node名でまとめる
            for ni_filter in result_ni_filter:
                node_name = ni_filter.get('parameter').get('instance_source_node_name')
                node_id = ni_filter.get('parameter').get('node_instance_id')
                result['id'].setdefault(node_id, ni_filter)
                result['name'].setdefault(node_name, ni_filter)

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_filter_node_one(self, conductor_instance_id, node_instance_id):
        """
            指定したNodeを取得(FILTER)
            ARGS:
                conductor_instance_id: conductor_instance_id
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        result.setdefault('id', {})
        result.setdefault('name', {})
        try:
            objnode = self.objmenus.get('objnode')
            filter_parameter = {
                "conductor_instance_id": {"LIST": [conductor_instance_id]},
                "node_instance_id": {"LIST": [node_instance_id]}
            }
            tmp_result = objnode.rest_filter(filter_parameter)
            if tmp_result[0] != '000-00000':
                retBool = False
                return retBool, result,
            result_ni_filter = tmp_result[1]
            # node_instance_id , node名でまとめる
            if len(result_ni_filter) != 1:
                retBool = False
                return retBool, result,
            result = result_ni_filter[0]
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_node_skip(self, conductor_instance_id, node_name):
        """
            conductor_dataからNodeの処理がSKIPか判定
            ARGS:
                start_node_instance_id: node_instance_id
                target_all_node_list: {status_id:[node_instance_id,,,,,]}
            RETRUN:
                'False' / 'True'
        """
        node_skip = 'False'
        try:
            instance_data = self.get_instance_data(conductor_instance_id)
            conductor_class = instance_data.get('conductor_class')
            node_skip = conductor_class.get(node_name).get('skip_flag')
            if node_skip is None:
                node_skip = 'False'
            elif node_skip in [1, '1']:
                node_skip = 'True'
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            node_skip = 'False'
        return node_skip

    def get_in_out_node(self, conductor_instance_id, node_name):
        """
            前後のNodeを取得
            ARGS:
                start_node_instance_id: node_instance_id
                node_name: node_name
            RETRUN:
                {'in':{}, 'out':{}}
        """
        result = {}
        result.setdefault('in', {})
        result.setdefault('out', {})
        try:
            instance_data = self.get_instance_data(conductor_instance_id)
            conductor_class = instance_data.get('conductor_class')
            target_node_terminals = conductor_class.get(node_name).get('terminal')
            for terminal_name, target_terminal in target_node_terminals.items():
                terminal_type = target_terminal.get('type')
                result[terminal_type].setdefault(terminal_name, target_terminal)
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            result = False

        return result

    def get_all_end_node(self, conductor_instance_id):
        """
            全ENDNodeを取得
            ARGS:
                conductor_instance_id: conductor_instance_id
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        result.setdefault('node', {})
        result.setdefault('end_types', [])
        try:
            table_name = 'T_COMN_CONDUCTOR_NODE_INSTANCE'
            where_str = "where `CONDUCTOR_INSTANCE_ID` = %s and `NODE_TYPE_ID` = %s "
            bind_value_list = [conductor_instance_id, 'end']
            tmp_result = self.objdbca.table_select(table_name, where_str, bind_value_list)
            tmp_ent_type = []
            for row in tmp_result:
                result['node'].setdefault(
                    row.get('NODE_INSTANCE_ID'),
                    {
                        "id": row.get('NODE_INSTANCE_ID'),
                        "node_name": row.get('I_NODE_NAME'),
                        "status": row.get('STATUS_ID'),
                        "end_type": row.get('END_TYPE')
                    }
                )
                tmp_ent_type.append(row.get('END_TYPE'))
            
            result['end_types'] = list(set(tmp_ent_type))

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_movement_path(self, orchestra_id, execution_id=None):
        """
            movement instance 関連のパス作成
            ARGS:
                orchestra_id:
                execution_id:
            RETRUN:
                retBool,result
        """
        retBool = True
        result = {}
        result.setdefault('base', None)
        result.setdefault('in', None)
        result.setdefault('out', None)
        result.setdefault('status_file_path', None)

        try:
            orchestra_path = None
            if orchestra_path is None:
                try:
                    orchestra_path = self.get_orchestra_info().get('name').get(orchestra_id).get('path')
                    manu_id = self.get_orchestra_info().get('name').get(orchestra_id).get('manu_id')
                except Exception:
                    pass
            if orchestra_path is None:
                try:
                    orchestra_path = self.get_orchestra_info().get('id').get(orchestra_id).get('path')
                    manu_id = self.get_orchestra_info().get('id').get(orchestra_id).get('manu_id')
                except Exception:
                    pass

            if orchestra_path is None or execution_id is None:
                retBool = False
                return retBool, result,
            
            if self.get_base_storage_path() is None:
                self.set_storage_path()

            movement_stprage_path = '{}/driver/{}/{}/'.format(
                self.get_base_storage_path(),
                orchestra_path,
                execution_id
            ).replace('//', '/')
            
            dl_data_stprage_path = '{}/uploadfiles/{}/'.format(
                self.get_base_storage_path(),
                manu_id,
            ).replace('//', '/')

            result['base'] = '{}'.format(movement_stprage_path).replace('//', '/')
            result['in'] = '{}/populated_data/{}/'.format(dl_data_stprage_path, execution_id).replace('//', '/')
            result['out'] = '{}/result_data/{}/'.format(dl_data_stprage_path, execution_id).replace('//', '/')
            result['status_file_path'] = '{}/out/MOVEMENT_STATUS_FILE'.format(movement_stprage_path).replace('//', '/')

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_status_file(self, status_file_path):
        """
            movement instance 関連のパス作成
            ARGS:
                status_file_path:
            RETRUN:
                retBool,result
        """
        retBool = True
        result = {}
        result.setdefault('status_file_path', None)
        result.setdefault('str_row', None)
        result.setdefault('status_file_value', None)
        try:
            status_file_val = None
            tmp_f_str_line = None
            if os.path.isfile(status_file_path) is True:  # noqa: F405
                with open(status_file_path) as f:
                    tmp_f_str = f.read()
                    tmp_f_str_line = tmp_f_str.splitlines()
                    status_file_val = tmp_f_str_line[0]
                result['status_file_path'] = status_file_path
                result['str_row'] = tmp_f_str
                result['status_file_value'] = status_file_val
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_conditional_node_info(self, node_options, in_node_status_id):
        """
            conditional branch の使用,不使用対象取得
            ARGS:
                node_options:
                in_node_status_id:
            RETRUN:
                retBool,result
        """
        retBool = True
        result = {}
        result.setdefault('target_node', None)
        result.setdefault('skip_node', None)
        try:
            # 実行Terminalを判定 + 不使用terminal先のNodeを取得
            node_name = node_options.get('node_name')
            tmp_node_status = node_options.get('instance_info_data').get('dict').get('node_status')
            tmp_node_status_keys = [k for k, v in tmp_node_status.items() if k == str(in_node_status_id)]
            in_node_status_key = tmp_node_status_keys[0]

            node_terminals = node_options.get('instance_data').get('conductor_class').get(node_name).get('terminal')
            # 実行Terminalを判定
            target_node = None
            skip_node = []
            for tname, tinfo in node_terminals.items():
                conditions = tinfo.get('condition')
                terminal_type = tinfo.get('type')
                if terminal_type == 'out':
                    if in_node_status_key in conditions:
                        target_node = tinfo.get('targetNode')
                    else:
                        skip_node.append(tinfo.get('targetNode'))
            # else
            if target_node is None:
                for tname, tinfo in node_terminals.items():
                    conditions = tinfo.get('condition')
                    terminal_type = tinfo.get('type')
                    if terminal_type == 'out':
                        if '__else__' in conditions:
                            target_node = tinfo.get('targetNode')
                        if '9999' in conditions:
                            target_node = tinfo.get('targetNode')

                if target_node in skip_node:
                    skip_node.remove(target_node)

            result['target_node'] = target_node
            result['skip_node'] = skip_node
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def get_status_file_node_info(self, node_options, in_node_status_file):
        """
            status file branch の使用,不使用対象取得
            ARGS:
                node_options:
                in_node_status_file:
            RETRUN:
                retBool,result
        """
        retBool = True
        result = {}
        result.setdefault('target_node', None)
        result.setdefault('skip_node', None)
        try:
            # 実行Terminalを判定 + 不使用terminal先のNodeを取得
            node_name = node_options.get('node_name')
            # tmp_node_status = node_options.get('instance_info_data').get('dict').get('node_status')
            node_terminals = node_options.get('instance_data').get('conductor_class').get(node_name).get('terminal')
            
            # 実行Terminalを判定
            target_node = None
            skip_node = []
            if in_node_status_file is not None:
                for tname, tinfo in node_terminals.items():
                    case = tinfo.get('case')
                    conditions = tinfo.get('condition')
                    terminal_type = tinfo.get('type')
                    tmp_target_node = tinfo.get('targetNode')
                    if terminal_type == 'out':
                        if case != 'else':
                            if conditions is not None:
                                if in_node_status_file in conditions:
                                    target_node = tmp_target_node
                                else:
                                    skip_node.append(tmp_target_node)
                # else
                for tname, tinfo in node_terminals.items():
                    case = tinfo.get('case')
                    terminal_type = tinfo.get('type')
                    tmp_target_node = tinfo.get('targetNode')
                    if terminal_type == 'out':
                        if case == 'else':
                            if target_node is None:
                                target_node = tmp_target_node
                            else:
                                if tmp_target_node not in skip_node:
                                    skip_node.append(tmp_target_node)
                        else:
                            if target_node is None:
                                if target_node != tmp_target_node:
                                    if tmp_target_node not in skip_node:
                                        skip_node.append(tmp_target_node)
            else:
                # else
                for tname, tinfo in node_terminals.items():
                    case = tinfo.get('case')
                    terminal_type = tinfo.get('type')
                    tmp_target_node = tinfo.get('targetNode')
                    if terminal_type == 'out':
                        if case == 'else':
                            if target_node is None:
                                target_node = tmp_target_node
                            else:
                                if tmp_target_node not in skip_node:
                                    skip_node.append(tmp_target_node)
                        else:
                            if tmp_target_node is not None:
                                if target_node != tmp_target_node:
                                    if tmp_target_node not in skip_node:
                                        skip_node.append(tmp_target_node)
            result['target_node'] = target_node
            result['skip_node'] = skip_node
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,
    
    def target_node_skip(self, node_options, node_name_list=[]):
        """
            対象NodeをSKIPへ変更
            ARGS:
                node_options:
                node_list:
            RETRUN:
                retBool,result
        """
        retBool = True
        result = {}
        # result.setdefault('target_node', None)
        # result.setdefault('skip_node', None)
        try:
            for node_name in node_name_list:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('13')
                # filter
                node_filter_data = node_options.get('all_node_filter').get('name').get(node_name)
                conductor_instance_id = node_filter_data.get('parameter').get('conductor_instance_id')
                node_instance_id = node_filter_data.get('parameter').get('node_instance_id')

                # 最新再取得
                tmp_result = self.get_filter_node_one(conductor_instance_id, node_instance_id)
                if tmp_result[0] is False:
                    raise Exception()
                node_filter_data = tmp_result[1]
                
                # Node更新
                node_filter_data['parameter']['status_id'] = n_status_id
                tmp_time = get_now_datetime()
                node_filter_data['parameter']['time_start'] = tmp_time
                node_filter_data['parameter']['time_end'] = tmp_time
                # Node Update
                tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                if tmp_result[0] is not True:
                    raise Exception()
                node_terminals = node_options.get('instance_data').get('conductor_class').get(node_name).get('terminal')
                node_type = node_options.get('instance_data').get('conductor_class').get(node_name).get('type')
                
                # end node まで
                tmp_skip_node = []
                if node_type != 'end':
                    for tname, tinfo in node_terminals.items():
                        targetNode = tinfo.get('targetNode')
                        terminal_type = tinfo.get('type')
                        if terminal_type == 'out':
                            tmp_skip_node.append(targetNode)
                    
                    if len(tmp_skip_node) >= 0:
                        tmp_result = self.target_node_skip(node_options, tmp_skip_node)
                        if tmp_result[0] is False:
                            raise Exception()
                
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    def orchestra_action(self, action_type, orchestra_id, action_options={}):
        """
            Movmentnへの各処理の振り分け
            ARGS:
                action_type: execute / abort / status
                orchestra_id:
                execution_id:
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        tmp_result = None
        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))
            # orchestra 取得
            orchestra_info = self.get_orchestra_info()
            action_config = orchestra_info.get('name').get(orchestra_id).get(action_type)
            driver_id = orchestra_info.get('name').get(orchestra_id).get('driver_id')
            if action_type == 'execute':
                operation_id = action_options.get('operation_id')
                # operation_name = action_options.get('operation_name')
                movement_id = action_options.get('movement_id')
                # movement_name = action_options.get('movement_name')
                conductor_id = action_options.get('conductor_id')
                conductor_name = action_options.get('conductor_name')
                movement_row = {}
                where_str = textwrap.dedent("""
                    WHERE `DISUSE_FLAG` = 0 AND `MOVEMENT_ID` = %s
                """).format().strip()
                table_name = action_config
                rows = self.objdbca.table_select(table_name, where_str, [movement_id])
                for row in rows:
                    movement_row = row

                operation_row = {}
                where_str = textwrap.dedent("""
                    WHERE `DISUSE_FLAG` = 0 AND `OPERATION_ID` = %s
                """).format().strip()
                table_name = "T_COMN_OPERATION"
                rows = self.objdbca.table_select(table_name, where_str, [operation_id])
                
                for row in rows:
                    operation_row = row

                # 作業実行
                tmp_execute = insert_execution_list(self.objdbca, 1, driver_id, operation_row, movement_row, None, conductor_id, conductor_name)  # noqa: F405 E501
                tmp_result = tmp_execute.get('execution_no')

            elif action_type == 'abort':
                execution_id = action_options.get('execution_id')
                # 緊急停止
                try:
                    tmp_result = execution_scram(self.objdbca, orchestra_id, execution_id)  # noqa: F405
                except Exception:
                    pass

            elif action_type == 'status':
                # ステータス取得
                execution_id = action_options.get('execution_id')
                where_str = textwrap.dedent("""
                    WHERE `DISUSE_FLAG` = 0 AND `EXECUTION_NO` = %s
                """).format().strip()
                table_name = action_config
                rows = self.objdbca.table_select(table_name, where_str, [execution_id])
                for row in rows:
                    status_id = row.get('STATUS_ID')
                tmp_result = status_id
            result.setdefault(action_type, tmp_result)
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    # conductor instanceの更新
    def conductor_status_update(self, conductor_instance_id):
        """
            Conductor instanceの更新処理
            ARGS:
                conductor_instance_id:
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        try:

            # 参照系リスト取得
            instance_info_data = self.get_instance_info_data()

            # 開始、終了ステータスリスト
            start_status = []
            for tmp_status in ['1', '2']:
                start_status.append(instance_info_data.get('dict').get('conductor_status').get(tmp_status))
            end_status = []
            for tmp_status in ['6', '7', '8', '11', '9']:
                end_status.append(instance_info_data.get('dict').get('conductor_status').get(tmp_status))
            
            c_status_id_3 = instance_info_data.get('dict').get('conductor_status').get('3')
            c_status_id_4 = instance_info_data.get('dict').get('conductor_status').get('4')
            
            # Conductor instance取得
            tmp_result = self.get_filter_conductor(conductor_instance_id)
            if tmp_result[0] is not True:
                raise Exception()
            conductor_filter = tmp_result[1]
            
            conductor_update_status = self.get_conductor_update_status(conductor_instance_id)
            current_status_id = conductor_filter['parameter']['status_id']
            
            # execution_log
            if 'execution_log' in conductor_filter['parameter']:
                execution_logs = self.get_conductor_update_msg(conductor_instance_id, 'execution_log')
                for execution_log in execution_logs:
                    tmp_ret, conductor_filter = self.add_execution_log(conductor_filter, execution_log)

            # 未実行、未実行(予約)時、実行中+開始時刻
            if current_status_id in start_status:
                conductor_update_status = instance_info_data.get('dict').get('conductor_status').get('3')
                conductor_filter['parameter']['time_start'] = get_now_datetime()
            # 終了時、終了時刻
            if current_status_id in end_status:
                conductor_filter['parameter']['time_end'] = get_now_datetime()
            
            # 実行中(遅延)→実行中への対応
            if current_status_id == c_status_id_4 and conductor_update_status == c_status_id_3:
                conductor_update_status = c_status_id_4
            
            # ステータス変更時のみ更新
            if conductor_update_status is not None:
                if current_status_id != conductor_update_status:
                    if conductor_update_status not in end_status:
                        conductor_filter['parameter']['status_id'] = conductor_update_status
                        tmp_result = self.conductor_instance_exec_maintenance(conductor_filter, conductor_instance_id, 'Update')
                        if tmp_result[0] is not True:
                            tmp_msg = 'Update Conductor instance Error'
                            # tmp_msg = g.appmsg.get_log_message(status_code, [msg_args])
                            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))
                            raise Exception()
                    else:
                        # 終了ステータス(正常終了,異常終了,警告終了,緊急停止,定外エラー)Node待ちあり
                        # 変更後の全Nodeのステータス取得
                        tmp_result = self.chk_conductor_end(conductor_instance_id)
                        if tmp_result[0] is True:
                            conductor_update_status = self.get_conductor_update_status(conductor_instance_id)
                            conductor_filter['parameter']['status_id'] = conductor_update_status
                            conductor_filter['parameter']['time_end'] = get_now_datetime()  # noqa: F405
                            tmp_result = self.conductor_instance_exec_maintenance(conductor_filter, conductor_instance_id, 'Update')
                            if tmp_result[0] is not True:
                                tmp_msg = 'Update Conductor instance Error'
                                # tmp_msg = g.appmsg.get_log_message(status_code, [msg_args])
                                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))
                                raise Exception()
            else:
                # """
                # 終了ステータス(正常終了,異常終了,警告終了,緊急停止,定外エラー)Node待ちあり
                # 変更後の全Nodeのステータス取得
                tmp_result = self.chk_conductor_end(conductor_instance_id)
                if tmp_result[0] is True:
                    conductor_update_status = self.get_conductor_update_status(conductor_instance_id)
                    conductor_filter['parameter']['status_id'] = conductor_update_status
                    conductor_filter['parameter']['time_end'] = get_now_datetime()  # noqa: F405
                    tmp_result = self.conductor_instance_exec_maintenance(conductor_filter, conductor_instance_id, 'Update')
                    if tmp_result[0] is not True:
                        tmp_msg = 'Update Conductor instance Error'
                        # tmp_msg = g.appmsg.get_log_message(status_code, [msg_args])
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))
                        raise Exception()
                # """

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        return retBool, result,

    # node instanceの個別処理,更新
    def execute_node_action(self, conductor_instance_id, node_instance_id, all_node_filter):
        """
            Node共通処理+Node毎の処理を振り分け
            ARGS:
                all_node_filter: { "id":{"node_instance_id":{"file":{},"parameter":{}}}}
            RETRUN:
                retBool, result,
        """
        retBool = True
        result = {}
        node_options = {}
        end_status_list = []
        nomal_status_list = []
        error_status_list = []
        try:
            # 対象NodeのFILTER
            node_filter_data = all_node_filter.get('id').get(node_instance_id)
            # Node type
            node_type = node_filter_data.get('parameter').get('node_type')
            # 参照系リスト取得
            instance_info_data = self.get_instance_info_data(conductor_instance_id)
            instance_data = self.get_instance_data(conductor_instance_id)
            tmp_result = self.get_execute_all_node_list(conductor_instance_id)
            if tmp_result[0] is not True:
                raise Exception()
            target_all_node_list = tmp_result[1]

            # Node名
            node_name = target_all_node_list.get('node').get(node_instance_id).get('node_name')
            
            # 各Node毎の処理の基本情報
            # conductor_instance_id
            node_options.setdefault('conductor_instance_id', conductor_instance_id)
            # node_instance_id
            node_options.setdefault('node_instance_id', node_instance_id)
            # node名
            node_options.setdefault('node_name', node_name)
            # nodeのFILTER
            node_options.setdefault('node_filter_data', node_filter_data)
            # 次のNodeの起動判定フラグ
            node_options.setdefault('next_node_exec_flg', None)
            # 次のNodeがconditional_branch判定フラグ
            node_options.setdefault('conditional_branch_flg', None)
            # 次のNodeがmerge判定フラグ
            node_options.setdefault('merge_flg', None)

            # 他参照データ
            node_options.setdefault('instance_info_data', instance_info_data)
            node_options.setdefault('instance_data', instance_data)
            node_options.setdefault('target_all_node_list', target_all_node_list)
            node_options.setdefault('all_node_filter', all_node_filter)
            
            # 終了ステータス
            for tmp_status in ['5', '6', '7', '8', '12', '13', '14']:
                end_status_list.append(instance_info_data.get('dict').get('node_status').get(tmp_status))
            node_options.setdefault('end_status_list', end_status_list)
            # 正常系ステータス
            for tmp_status in ['5', '13']:
                nomal_status_list.append(instance_info_data.get('dict').get('node_status').get(tmp_status))
            node_options.setdefault('nomal_status_list', nomal_status_list)
            
            # 異常系ステータス
            for tmp_status in ['6', '7', '8', '12']:
                error_status_list.append(instance_info_data.get('dict').get('node_status').get(tmp_status))
            node_options.setdefault('error_status_list', error_status_list)
            
            # 更新ステータス
            node_options.setdefault('node_status_id', '')
            # 次のNode関連
            node_options.setdefault('next_node_list', {})

            # SKIP
            node_skip = self.get_node_skip(conductor_instance_id, node_name)
            if node_skip == bool_master_true:
                n_status_id = instance_info_data.get('dict').get('node_status').get('13')
                node_options['node_status_id'] = n_status_id
                node_options.setdefault('skip', bool_master_true)

            # 緊急停止
            abort_status = self.get_abort_status(conductor_instance_id)
            if abort_status == bool_master_true:
                node_options.setdefault('abort_status', abort_status)

            # 前後のNode取得
            target_in_out_node = self.get_in_out_node(conductor_instance_id, node_name)
            if target_in_out_node is not False:
                node_options.setdefault('in_node', target_in_out_node.get('in'))
                node_options.setdefault('out_node', target_in_out_node.get('out'))
                # 次のNodeにConditional含むか判定
                for tname, tinfo in target_in_out_node.get('out').items():
                    tnode = tinfo.get('targetNode')
                    tnode_type = instance_data.get('conductor_class').get(tnode).get('type')
                    if tnode_type == 'conditional-branch':
                        node_options['conditional_branch_flg'] = '1'
                    if tnode_type == 'merge':
                        node_options['merge_flg'] = '1'

            tmp_msg = 'node_type:{}, node_name:{}, node_instance_id:{} '.format(node_type, node_name, node_instance_id)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                
            # node個別処理振り分け
            if node_type == 'start':
                tmp_result = self.start_node_action(node_options)
            elif node_type == 'end':
                tmp_result = self.end_node_action(node_options)
            elif node_type == 'movement':
                tmp_result = self.movement_node_action(node_options)
            elif node_type == 'call':
                tmp_result = self.call_node_action(node_options)
            elif node_type == 'parallel-branch':
                tmp_result = self.parallel_branch_node_action(node_options)
            elif node_type == 'conditional-branch':
                tmp_result = self.conditional_branch_node_action(node_options)
            elif node_type == 'merge':
                tmp_result = self.merge_node_action(node_options)
            elif node_type == 'pause':
                tmp_result = self.pause_node_action(node_options)
            elif node_type == 'status-file-branch':
                tmp_result = self.status_file_branch_node_action(node_options)
            else:
                raise Exception()

            if tmp_result[0] is False:
                raise Exception()

            # 次のNode実行
            next_node_exec_flg = node_options.get('next_node_exec_flg')
            if next_node_exec_flg is not None:
                node_options = tmp_result[1]
                tmp_result = self.next_node_exec(node_options)
                if tmp_result[0] is False:
                    raise Exception()

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
            g.applogger.error(addline_msg(e))
        return retBool, result,

    def next_node_exec(self, node_options):
        """
            次のNodeを実行中へ
            ARGS:
                node_options:{}
            RETRUN:
                retBool, node_options,
        """
        retBool = True
        result = {}

        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))
            # conductor instance id
            conductor_instance_id = node_options.get('conductor_instance_id')
            # 次のNode関連
            next_node_list = node_options.get('next_node_list')

            for next_node_name, next_node_info in next_node_list.items():
                # node instance id
                next_node_instance_id = next_node_info.get('node_instance_id')
                # filter
                node_filter_data = node_options.get('all_node_filter').get('id').get(next_node_instance_id)
                # status
                next_n_status_id = next_node_info.get('status_id')
                
                # 最新再取得
                tmp_result = self.get_filter_node_one(conductor_instance_id, next_node_instance_id)
                if tmp_result[0] is False:
                    raise Exception()
                node_filter_data = tmp_result[1]
                current_node_status_id = node_filter_data['parameter']['status_id']
                # ステータス変更時のみ実施、Nodeへの重複更新させない
                if current_node_status_id != next_n_status_id:
                    # Node更新
                    node_filter_data['parameter']['status_id'] = next_n_status_id
                    node_filter_data['parameter']['time_start'] = get_now_datetime()
                    tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                    if tmp_result[0] is not True:
                        raise Exception()
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False

        result = node_options
        return retBool, result,
    
    # Node毎の処理
    def start_node_action(self, node_options):
        """
            StartNodeの処理
                StartNode完了+次のNode実行中へ
            ARGS:
                node_options:{}
            RETRUN:
                retBool, node_options,
        """
        retBool = True
        result = {}

        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))

            # conductor instance id
            conductor_instance_id = node_options.get('conductor_instance_id')
            # filter
            node_filter_data = node_options.get('node_filter_data')
            # skip
            skip = node_options.get('skip')
            # abort_status
            abort_status = node_options.get('abort_status')

            # 正常終了
            n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('5')

            # Conductor実行中
            c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')
            node_options['next_node_exec_flg'] = '1'

            # 緊急停止(Nodeのステータス変更のみ)
            if abort_status == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                self.set_conductor_update_status(conductor_instance_id, c_status_id)
                node_options['next_node_exec_flg'] = None
            elif skip == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('13')
            else:
                pass

            # Node Update
            node_filter_data['parameter']['status_id'] = n_status_id
            node_filter_data['parameter']['time_start'] = get_now_datetime()
            node_filter_data['parameter']['time_end'] = get_now_datetime()

            tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
            if tmp_result[0] is not True:
                raise Exception()
            
            # Conductor status 設定
            self.set_conductor_update_status(conductor_instance_id, c_status_id)

            # next node
            next_n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
            for terminal_name, target_node_info in node_options.get('out_node').items():
                targetNode = target_node_info.get('targetNode')
                next_node_instance_id = node_options.get('target_all_node_list').get('node_list').get(targetNode).get('id')
                next_target_node_info = {
                    "node_instance_id": next_node_instance_id,
                    "node_name": targetNode,
                    "status_id": next_n_status_id
                }
                node_options['next_node_list'].setdefault(targetNode, next_target_node_info)

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False

        result = node_options
        return retBool, result,

    def end_node_action(self, node_options):
        """
            endNodeの処理
                EndNode完了へ+終了タイプ設定
            ARGS:
                node_options:{}
            RETRUN:
                retBool, node_options,
        """
        retBool = True
        result = {}

        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))

            # conductor instance id
            conductor_instance_id = node_options.get('conductor_instance_id')
            # filter
            node_filter_data = node_options.get('node_filter_data')
            # skip
            skip = node_options.get('skip')
            # abort_status
            abort_status = node_options.get('abort_status')

            # 正常終了
            n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('5')
            end_type = node_filter_data.get('parameter').get('end_type')

            # Conductor終了,endtype設定
            if end_type is None:
                c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('6')
            else:
                c_status_id = end_type
            
            # 緊急停止(Nodeのステータス変更のみ)
            if abort_status == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                self.set_conductor_update_status(conductor_instance_id, c_status_id)
                node_options['next_node_exec_flg'] = None
            elif skip == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('13')
            else:
                pass

            # Node Update
            node_filter_data['parameter']['status_id'] = n_status_id
            node_filter_data['parameter']['time_end'] = get_now_datetime()
            tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
            if tmp_result[0] is not True:
                raise Exception()

            self.set_conductor_update_status(conductor_instance_id, c_status_id)

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False

        result = node_options
        return retBool, result,

    def movement_node_action(self, node_options):
        """
            movementNodeの処理
                各Movementの作業実行、問い合わせ
                Nodeへのステータス反映
            ARGS:
                node_options:{}
            RETRUN:
                retBool, node_options,
        """
        retBool = True
        result = {}

        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))

            # conductor instance id
            conductor_instance_id = node_options.get('conductor_instance_id')
            # filter
            node_filter_data = node_options.get('node_filter_data')
            # skip
            skip = node_options.get('skip')
            # abort_status
            abort_status = node_options.get('abort_status')
            # execution_id
            execution_id = node_filter_data.get('parameter').get('execution_id')

            # end_status_list
            end_status_list = node_options.get('end_status_list')
            # error_status_list
            error_status_list = node_options.get('error_status_list')
            # conditional_branch_flg
            conditional_branch_flg = node_options.get('conditional_branch_flg')
            # merge_flg
            merge_flg = node_options.get('merge_flg')

            orchestrator_id = node_filter_data.get('parameter').get('movement_type')

            movement_path = self.get_movement_path(orchestrator_id, execution_id)
            status_file_path = movement_path[1].get('status_file_path')

            # Conductor実行中
            c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')

            # movement
            movement_id = node_filter_data.get('parameter').get('instance_source_movement_id')
            movement_name = node_filter_data.get('parameter').get('instance_source_movement_name')
            
            # conductor
            conductor_id = node_options.get('instance_data').get('conductor').get('conductor_instance_id')
            conductor_name = node_options.get('instance_data').get('conductor').get('conductor_name')
            
            # operation
            operation_id = node_options.get('instance_data').get('conductor').get('operation_id')
            operation_name = node_options.get('instance_data').get('conductor').get('operation_name')
            tmp_operation_id = node_filter_data.get('parameter').get('operation_id')
            tmp_operation_name = node_filter_data.get('parameter').get('operation_name')
            # operation 個別
            if tmp_operation_id is not None:
                operation_id = tmp_operation_id
                operation_name = tmp_operation_name

            # execution_id / movement / operation / conductor instance
            action_options = {}
            action_options.setdefault("execution_id", execution_id)
            action_options.setdefault("movement_id", movement_id)
            action_options.setdefault("movement_name", movement_name)
            action_options.setdefault("operation_id", operation_id)
            action_options.setdefault("operation_name", operation_name)
            action_options.setdefault("conductor_id", conductor_id)
            action_options.setdefault("conductor_name", conductor_name)

            execute_flg = False
            # 作業未実行時
            if execution_id is None:
                # 緊急停止(Nodeのステータス変更のみ)
                if abort_status == bool_master_true:
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                    self.set_conductor_update_status(conductor_instance_id, c_status_id)
                    node_options['next_node_exec_flg'] = None
                # SKIP時
                elif skip == bool_master_true:
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('13')
                else:
                    try:
                        n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                        c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')
                        # MV作業実行
                        action_type = 'execute'
                        tmp_result = self.orchestra_action(action_type, orchestrator_id, action_options)
                        if tmp_result[0] is not True:
                            raise Exception()
                        execution_id = tmp_result[1].get(action_type)
                        if execution_id is not None:
                            execute_flg = True
                            node_filter_data['parameter']['execution_id'] = execution_id
                        else:
                            raise Exception()

                    except Exception as e:
                        g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
                        type_, value, traceback_ = sys.exc_info()
                        msg = traceback.format_exception(type_, value, traceback_)
                        g.applogger.error(msg)
                        msg_code = 'MSG-40026'
                        msg_args = [movement_id, operation_id]
                        err_msg = g.appmsg.get_api_message(msg_code, msg_args)
                        self.set_conductor_update_msg(conductor_instance_id, 'execution_log', err_msg)
                        n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('6')
                        c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('7')
            else:
                # 緊急停止
                if abort_status == bool_master_true:
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                    node_options['next_node_exec_flg'] = None
                    # 緊急停止発令
                    self.set_conductor_update_status(conductor_instance_id, c_status_id)
                    action_type = 'abort'
                    tmp_result = self.orchestra_action(action_type, orchestrator_id, action_options)

                # ステータス問い合わせ
                action_type = 'status'
                action_options["execution_id"] = execution_id
                tmp_result = self.orchestra_action(action_type, orchestrator_id, action_options)
                if tmp_result[0] is not True:
                    raise Exception()
                
                # ステータス反映 MV->Node
                mv_status_id = tmp_result[1].get(action_type)
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get(mv_status_id)
                if mv_status_id in ['1', '2', '3']:
                    # 1:未実行,3:実行中->3:実行中
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                    # 3:実行中->3:実行中
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')
                    
                elif mv_status_id in ['4']:
                    # 4:実行中(遅延)->4:実行中(遅延)
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('4')
                elif mv_status_id in ['5']:
                    # 5:完了->6:正常終了
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('6')
                elif mv_status_id in ['6']:

                    # 6:完了(異常)->7:異常終了
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('7')
                elif mv_status_id in ['7']:
                    # 7:想定外エラー->->7:異常終了
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('7')
                elif mv_status_id in ['8']:
                    # 8:緊急停止->9:緊急停止
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                else:
                    # Conductor使用時に扱わないので異常終了扱い
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('8')

                # ステータスファイル取得
                if status_file_path is not None:
                    status_file_info = self.get_status_file(status_file_path)
                    if status_file_info[0] is True:
                        node_filter_data['parameter']['status_file'] = status_file_info[1].get('status_file_value')
                        
            # ステータス変更時のみ更新
            now_status_id = node_filter_data['parameter']['status_id']
            if n_status_id != now_status_id or execute_flg is True:
                # Node更新
                node_filter_data['parameter']['status_id'] = n_status_id
                
                # 終了時のみ
                if n_status_id in end_status_list:
                    node_filter_data['parameter']['time_end'] = get_now_datetime()

                tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                if tmp_result[0] is not True:
                    raise Exception()

                self.set_conductor_update_status(conductor_instance_id, c_status_id)

                # 他完了ノードの状況取得
                tmp_result = self.chk_all_node_status_info(conductor_instance_id)
                if tmp_result[0] is not True:
                    raise Exception()
                all_node_status_info = tmp_result[1]
                error_node_conditional_flg = all_node_status_info.get('error_node_conditional_flg')

                # next node
                if n_status_id in end_status_list:
                    if n_status_id in error_status_list and conditional_branch_flg is None:
                        # 異常終了系で、次がConditionalでない場合、実行させない
                        pass
                    elif error_node_conditional_flg is False:
                        # 他の異常終了系ノードで、次がConditionalでない場合、実行させない
                        pass
                    elif merge_flg is not None:
                        node_options['next_node_exec_flg'] = '1'
                        next_n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                        for terminal_name, target_node_info in node_options.get('out_node').items():
                            targetNode = target_node_info.get('targetNode')
                            next_node_instance_id = node_options.get('target_all_node_list').get('node_list').get(targetNode).get('id')
                            next_target_node_info = {
                                "node_instance_id": next_node_instance_id,
                                "node_name": targetNode,
                                "status_id": next_n_status_id
                            }
                            node_options['next_node_list'].setdefault(targetNode, next_target_node_info)
                    else:
                        node_options['next_node_exec_flg'] = '1'
                        next_n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                        for terminal_name, target_node_info in node_options.get('out_node').items():
                            targetNode = target_node_info.get('targetNode')
                            next_node_instance_id = node_options.get('target_all_node_list').get('node_list').get(targetNode).get('id')
                            next_target_node_info = {
                                "node_instance_id": next_node_instance_id,
                                "node_name": targetNode,
                                "status_id": next_n_status_id
                            }
                            node_options['next_node_list'].setdefault(targetNode, next_target_node_info)

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False

        result = node_options
        return retBool, result,

    def call_node_action(self, node_options):
        """
            callNodeの処理
            ARGS:
                node_options:{}
            RETRUN:
                retBool, node_options,
        """
        retBool = True
        result = {}

        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))

            # conductor instance id
            conductor_instance_id = node_options.get('conductor_instance_id')
            # filter
            node_filter_data = node_options.get('node_filter_data')
            # skip
            skip = node_options.get('skip')
            # abort_status
            abort_status = node_options.get('abort_status')
            # execution_id
            execution_id = node_filter_data.get('parameter').get('execution_id')
        
            # end_status_list
            end_status_list = node_options.get('end_status_list')
            # error_status_list
            error_status_list = node_options.get('error_status_list')
            # conditional_branch_flg
            conditional_branch_flg = node_options.get('conditional_branch_flg')
            # merge_flg
            merge_flg = node_options.get('merge_flg')

            # Conductor実行中
            c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')
            self.set_conductor_update_status(conductor_instance_id, c_status_id)
            n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
            
            call_execute_flg = False

            # 作業未実行時
            if execution_id is None:
                # 緊急停止(Nodeのステータス変更のみ)
                if abort_status == bool_master_true:
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                    self.set_conductor_update_status(conductor_instance_id, c_status_id)
                    node_options['next_node_exec_flg'] = None
                # SKIP時
                elif skip == bool_master_true:
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('13')
                else:
                    
                    # 作業実行するConductorの情報設定
                    # conductor class id
                    call_caonductor_class_id = node_filter_data.get('parameter').get('instance_source_conductor_id')
                    # operation id
                    call_operation_id = node_options.get('instance_data').get('conductor').get('operation_id')
                    
                    # 個別指定の場合上書き
                    tmp_call_operation_id = node_filter_data.get('parameter').get('operation_id')
                    if tmp_call_operation_id is not None:
                        call_operation_id = tmp_call_operation_id
                    # conductor data 取得
                    # call_conductor_data = node_filter_data.get('parameter').get('instance_source_conductor_info')
                    call_parameter = {
                        'conductor_class_id': call_caonductor_class_id,
                        'operation_id': call_operation_id,
                        'schedule_date': '',
                        'conductor_data': {},
                    }
                    try:
                        parent_conductor_instance_id = conductor_instance_id
                        call_create_parameter = self.create_execute_register_parameter(call_parameter, parent_conductor_instance_id)
                        if call_create_parameter[0] != '000-00000':
                            raise Exception()
                        call_conductor_parameter = call_create_parameter[1].get('conductor')
                        call_node_parameters = call_create_parameter[1].get('node')
                        call_conductor_instance_id = call_create_parameter[1].get('conductor_instance_id')
                        
                        # conductor instanceテーブルへのレコード追加
                        iem_result = self.conductor_instance_exec_maintenance(call_conductor_parameter)
                        if iem_result[0] is not True:
                            raise Exception()
                        # node instanceテーブルへのレコード追加
                        iem_result = self.node_instance_exec_maintenance(call_node_parameters)
                        if iem_result[0] is not True:
                            raise Exception()
                        
                        node_filter_data['parameter']['execution_id'] = call_conductor_instance_id
                        call_execute_flg = True
                    except Exception:
                        msg_code = 'MSG-40027'
                        msg_args = [call_caonductor_class_id, call_operation_id]
                        err_msg = g.appmsg.get_api_message(msg_code, msg_args)
                        self.set_conductor_update_msg(conductor_instance_id, 'execution_log', err_msg)
                        n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('6')
                        c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('7')
            else:
                # 緊急停止
                if abort_status == bool_master_true:
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                    self.set_conductor_update_status(conductor_instance_id, c_status_id)

                    # 緊急停止発令
                    action_result = self.execute_action('scram', execution_id)

                # ##################### Conductor問い合わせ #####################
                # Conductor instance取得
                tmp_result = self.get_filter_conductor(execution_id)
                if tmp_result[0] is not True:
                    raise Exception()
                conductor_filter = tmp_result[1]
                call_status_id = conductor_filter.get('parameter').get('status_id')
                
                """
                C->N
                        1:未実行:->1:未実行
                        2:未実行(予約):->2:準備中
                        3:実行中:->3:実行中
                        4:実行中(遅延):->4:実行中(遅延)
                    *   6:正常終了->5:正常終了
                    *   7:異常終了->6:異常終了
                    *   11:想定外エラー->7:想定外エラー
                    *   9:緊急停止->8:緊急停止
                    (*   5:一時停止->3:実行中)
                """
                if call_status_id == node_options.get('instance_info_data').get('dict').get('conductor_status').get('1'):
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')
                elif call_status_id == node_options.get('instance_info_data').get('dict').get('conductor_status').get('2'):
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')
                elif call_status_id == node_options.get('instance_info_data').get('dict').get('conductor_status').get('3'):
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')
                elif call_status_id == node_options.get('instance_info_data').get('dict').get('conductor_status').get('4'):
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('4')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('4')
                elif call_status_id == node_options.get('instance_info_data').get('dict').get('conductor_status').get('5'):
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')
                elif call_status_id == node_options.get('instance_info_data').get('dict').get('conductor_status').get('6'):
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('5')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('6')
                elif call_status_id == node_options.get('instance_info_data').get('dict').get('conductor_status').get('7'):
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('6')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('7')
                elif call_status_id == node_options.get('instance_info_data').get('dict').get('conductor_status').get('8'):
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('5')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('8')
                elif call_status_id == node_options.get('instance_info_data').get('dict').get('conductor_status').get('9'):
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                elif call_status_id == node_options.get('instance_info_data').get('dict').get('conductor_status').get('11'):
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('7')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('11')
                else:
                    raise Exception()

            # ステータス変更時のみ更新
            now_status_id = node_filter_data['parameter']['status_id']
            if n_status_id != now_status_id or call_execute_flg is True:
                # Node更新
                node_filter_data['parameter']['status_id'] = n_status_id
                
                # 終了時のみ
                if n_status_id in end_status_list:
                    node_filter_data['parameter']['time_end'] = get_now_datetime()

                tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                if tmp_result[0] is not True:
                    raise Exception()

                self.set_conductor_update_status(conductor_instance_id, c_status_id)

                # 他完了ノードの状況取得
                tmp_result = self.chk_all_node_status_info(conductor_instance_id)
                if tmp_result[0] is not True:
                    raise Exception()
                all_node_status_info = tmp_result[1]
                error_node_conditional_flg = all_node_status_info.get('error_node_conditional_flg')

                # next node
                if n_status_id in end_status_list:
                    if n_status_id in error_status_list and conditional_branch_flg is None:
                        # 異常終了系で、次がConditionalでない場合、実行させない
                        pass
                    elif error_node_conditional_flg is False:
                        # 他の異常終了系ノードで、次がConditionalでない場合、実行させない
                        pass
                    elif merge_flg is not None:
                        node_options['next_node_exec_flg'] = '1'
                        next_n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                        for terminal_name, target_node_info in node_options.get('out_node').items():
                            targetNode = target_node_info.get('targetNode')
                            next_node_instance_id = node_options.get('target_all_node_list').get('node_list').get(targetNode).get('id')
                            next_target_node_info = {
                                "node_instance_id": next_node_instance_id,
                                "node_name": targetNode,
                                "status_id": next_n_status_id
                            }
                            node_options['next_node_list'].setdefault(targetNode, next_target_node_info)
                    else:
                        node_options['next_node_exec_flg'] = '1'
                        next_n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                        for terminal_name, target_node_info in node_options.get('out_node').items():
                            targetNode = target_node_info.get('targetNode')
                            next_node_instance_id = node_options.get('target_all_node_list').get('node_list').get(targetNode).get('id')
                            next_target_node_info = {
                                "node_instance_id": next_node_instance_id,
                                "node_name": targetNode,
                                "status_id": next_n_status_id
                            }
                            node_options['next_node_list'].setdefault(targetNode, next_target_node_info)

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
            
        result = node_options
        return retBool, result,

    def parallel_branch_node_action(self, node_options):
        """
            parallel_branchNodeの処理
            ARGS:
                node_options:{}
            RETRUN:
                retBool, node_options,
        """
        retBool = True
        result = {}

        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))

            # conductor instance id
            conductor_instance_id = node_options.get('conductor_instance_id')
            # filter
            node_filter_data = node_options.get('node_filter_data')
            # skip
            skip = node_options.get('skip')
            # abort_status
            abort_status = node_options.get('abort_status')
            
            # end_status_list
            end_status_list = node_options.get('end_status_list')
            
            # 正常終了
            n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('5')
            node_options['next_node_exec_flg'] = '1'
            # Conductor実行中
            c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')

            # 緊急停止(Nodeのステータス変更のみ)
            if abort_status == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                self.set_conductor_update_status(conductor_instance_id, c_status_id)
                node_options['next_node_exec_flg'] = None
            elif skip == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('13')
            else:
                pass

            # Node更新
            node_filter_data['parameter']['status_id'] = n_status_id
            # 終了時のみ
            if n_status_id in end_status_list:
                node_filter_data['parameter']['time_end'] = get_now_datetime()
            # Node Update
            tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
            if tmp_result[0] is not True:
                raise Exception()

            self.set_conductor_update_status(conductor_instance_id, c_status_id)

            # next node
            if n_status_id in end_status_list:
                next_n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                for terminal_name, target_node_info in node_options.get('out_node').items():
                    targetNode = target_node_info.get('targetNode')
                    next_node_instance_id = node_options.get('target_all_node_list').get('node_list').get(targetNode).get('id')
                    next_target_node_info = {
                        "node_instance_id": next_node_instance_id,
                        "node_name": targetNode,
                        "status_id": next_n_status_id
                    }
                    node_options['next_node_list'].setdefault(targetNode, next_target_node_info)

        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
        result = node_options
        return retBool, result,

    def conditional_branch_node_action(self, node_options):
        """
            conditional_branchNodeの処理
            ARGS:
                node_options:{}
            RETRUN:
                retBool, node_options,
        """
        retBool = True
        result = {}
        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))

            # conductor instance id
            conductor_instance_id = node_options.get('conductor_instance_id')
            # filter
            node_filter_data = node_options.get('node_filter_data')
            # skip
            skip = node_options.get('skip')
            # abort_status
            abort_status = node_options.get('abort_status')
            # in node
            in_node = node_options.get('in_node')
            # instance_data list
            instance_data = node_options.get('instance_data')
            # nomal_status_list
            nomal_status_list = node_options.get('nomal_status_list')

            # 正常終了
            n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('5')

            # Conductor実行中
            c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')

            # 緊急停止(Nodeのステータス変更のみ)
            if abort_status == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                self.set_conductor_update_status(conductor_instance_id, c_status_id)
                node_options['next_node_exec_flg'] = None
            elif skip == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('13')
            else:
                pass

                # in nodeのステータスを取得
                if len(in_node) == 1:
                    for tname, tinfo in in_node.items():
                        in_node_name = tinfo.get('targetNode')
                        in_node_info = instance_data.get('node').get(in_node_name)
                        in_node_status_id = in_node_info.get('status_id')

                tmp_result = self.get_conditional_node_info(node_options, in_node_status_id)
                if tmp_result[0] is False:
                    raise Exception()
                self.set_conductor_update_status(conductor_instance_id, c_status_id)
                targetNode = tmp_result[1].get('target_node')
                skip_node = tmp_result[1].get('skip_node')
            
            if n_status_id in nomal_status_list:
                # Node更新
                node_filter_data['parameter']['status_id'] = n_status_id
                node_filter_data['parameter']['time_end'] = get_now_datetime()
                tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                if tmp_result[0] is not True:
                    raise Exception()
                
                if targetNode is not None:
                    node_options['next_node_exec_flg'] = '1'
                    next_n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                    next_node_instance_id = node_options.get('target_all_node_list').get('node_list').get(targetNode).get('id')
                    next_target_node_info = {
                        "node_instance_id": next_node_instance_id,
                        "node_name": targetNode,
                        "status_id": next_n_status_id
                    }
                    node_options['next_node_list'].setdefault(targetNode, next_target_node_info)

                if skip_node is not None:
                    if len(skip_node) != 0:
                        tmp_result = self.target_node_skip(node_options, skip_node)
                        if tmp_result[0] is False:
                            raise Exception()
            elif abort_status == bool_master_true:
                # Node更新
                node_filter_data['parameter']['status_id'] = n_status_id
                node_filter_data['parameter']['time_end'] = get_now_datetime()
                tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                if tmp_result[0] is not True:
                    raise Exception()
            else:
                pass
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False

        result = node_options
        return retBool, result,

    def merge_node_action(self, node_options):
        """
            mergeNodeの処理
            ARGS:
                node_options:{}
            RETRUN:
                retBool, node_options,
        """
        retBool = True
        result = {}

        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))

            # conductor instance id
            conductor_instance_id = node_options.get('conductor_instance_id')
            # filter
            node_filter_data = node_options.get('node_filter_data')
            # skip
            skip = node_options.get('skip')
            # abort_status
            abort_status = node_options.get('abort_status')
            # in node
            in_node = node_options.get('in_node')
            # instance_data list
            instance_data = node_options.get('instance_data')
            # nomal_status_list
            nomal_status_list = node_options.get('nomal_status_list')

            # 正常終了
            n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('5')

            # Conductor実行中
            c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')

            # 緊急停止(Nodeのステータス変更のみ)
            if abort_status == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                self.set_conductor_update_status(conductor_instance_id, c_status_id)
                node_options['next_node_exec_flg'] = None
            elif skip == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('13')
            else:
                pass

            # in nodeのステータスカウント
            in_node_cnt = len(in_node)
            in_node_nomal_end_cnt = 0
            for tname, tinfo in in_node.items():
                in_node_name = tinfo.get('targetNode')
                in_node_info = instance_data.get('node').get(in_node_name)
                in_node_status_id = in_node_info.get('status')

                if in_node_status_id in nomal_status_list:
                    in_node_nomal_end_cnt = in_node_nomal_end_cnt + 1

            # in node が全て完了していれば、正常終了+次のNode実行へ
            if in_node_cnt == in_node_nomal_end_cnt:

                # Node更新
                node_filter_data['parameter']['status_id'] = n_status_id
                node_filter_data['parameter']['time_end'] = get_now_datetime()
                tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                if tmp_result[0] is not True:
                    raise Exception()
                
                node_options['next_node_exec_flg'] = '1'
                next_n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                for terminal_name, target_node_info in node_options.get('out_node').items():
                    targetNode = target_node_info.get('targetNode')
                    next_node_instance_id = node_options.get('target_all_node_list').get('node_list').get(targetNode).get('id')
                    next_target_node_info = {
                        "node_instance_id": next_node_instance_id,
                        "node_name": targetNode,
                        "status_id": next_n_status_id
                    }
                    node_options['next_node_list'].setdefault(targetNode, next_target_node_info)
            elif abort_status == bool_master_true:
                # Node更新
                node_filter_data['parameter']['status_id'] = n_status_id
                node_filter_data['parameter']['time_end'] = get_now_datetime()
                tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                if tmp_result[0] is not True:
                    raise Exception()
            else:
                pass
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
            
        result = node_options
        return retBool, result,

    def pause_node_action(self, node_options):
        """
            pauseNodeの処理
            ARGS:
                node_options:{}
            RETRUN:
                retBool, node_options,
        """
        retBool = True
        result = {}
        bool_master_true = 'True'
        bool_master_false = 'False'
        
        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))
            conductor_instance_id = node_options.get('conductor_instance_id')
            node_filter_data = node_options.get('node_filter_data')
            n_status_id = node_options.get('node_status_id')
            abort_status = node_options.get('abort_status')
            end_status_list = node_options.get('end_status_list')

            work_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
            now_status_id = node_filter_data['parameter']['status_id']

            # Conductor実行中
            c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')
            self.set_conductor_update_status(conductor_instance_id, c_status_id)

            # 緊急停止
            if abort_status == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                self.set_conductor_update_status(conductor_instance_id, c_status_id)
            else:
                if now_status_id == work_status_id:
                    # 一時停止へ
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('11')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('5')
                    self.set_conductor_update_status(conductor_instance_id, c_status_id)
                else:
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('5')
                    released_flag = node_filter_data['parameter']['released_flag']
                    n_status_id = node_filter_data['parameter']['status_id']
                    # 解除済みの場合Node＋実行中へ
                    if released_flag == bool_master_true:
                        n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('5')
                        # Conductor実行中へ
                        c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')
                        node_options['next_node_exec_flg'] = '1'
                    self.set_conductor_update_status(conductor_instance_id, c_status_id)

            # ステータス変更時のみ更新
            now_status_id = node_filter_data['parameter']['status_id']
            if n_status_id != now_status_id:
                # Node更新
                node_filter_data['parameter']['status_id'] = n_status_id

                # 終了時のみ
                if n_status_id in end_status_list:
                    node_filter_data['parameter']['time_end'] = get_now_datetime()
                    
                tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                if tmp_result[0] is not True:
                    raise Exception()

                next_n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                for terminal_name, target_node_info in node_options.get('out_node').items():
                    targetNode = target_node_info.get('targetNode')
                    next_node_instance_id = node_options.get('target_all_node_list').get('node_list').get(targetNode).get('id')
                    next_target_node_info = {
                        "node_instance_id": next_node_instance_id,
                        "node_name": targetNode,
                        "status_id": next_n_status_id
                    }
                    node_options['next_node_list'].setdefault(targetNode, next_target_node_info)
            elif abort_status == bool_master_true:
                # Node更新
                node_filter_data['parameter']['status_id'] = n_status_id
                node_filter_data['parameter']['time_end'] = get_now_datetime()
                tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                if tmp_result[0] is not True:
                    raise Exception()
            else:
                pass
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False
            
        result = node_options
        return retBool, result,

    def status_file_branch_node_action(self, node_options):
        """
            status_file_branchNodeの処理
            ARGS:
                node_options:{}
            RETRUN:
                retBool, node_options,
        """
        retBool = True
        result = {}
        try:
            g.applogger.debug(addline_msg('{}'.format(sys._getframe().f_code.co_name)))

            # conductor instance id
            conductor_instance_id = node_options.get('conductor_instance_id')
            # filter
            node_filter_data = node_options.get('node_filter_data')
            # skip
            skip = node_options.get('skip')
            # abort_status
            abort_status = node_options.get('abort_status')
            # in node
            in_node = node_options.get('in_node')
            # instance_data list
            instance_data = node_options.get('instance_data')
            # nomal_status_list
            nomal_status_list = node_options.get('nomal_status_list')

            # 正常終了
            n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('5')

            # Conductor実行中
            c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('3')

            if skip == bool_master_true:
                n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('13')
            else:
                # 緊急停止(Nodeのステータス変更のみ)
                if abort_status == bool_master_true:
                    n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('8')
                    c_status_id = node_options.get('instance_info_data').get('dict').get('conductor_status').get('9')
                    self.set_conductor_update_status(conductor_instance_id, c_status_id)
                    node_options['next_node_exec_flg'] = None

            # in nodeのステータスを取得
            if len(in_node) == 1:
                for tname, tinfo in in_node.items():
                    in_node_name = tinfo.get('targetNode')
                    in_node_info = instance_data.get('node').get(in_node_name)
                    in_node_status_file = in_node_info.get('status_file')
            
            tmp_result = self.get_status_file_node_info(node_options, in_node_status_file)
            if tmp_result[0] is False:
                raise Exception()
            self.set_conductor_update_status(conductor_instance_id, c_status_id)
            targetNode = tmp_result[1].get('target_node')
            skip_node = tmp_result[1].get('skip_node')
            
            if n_status_id in nomal_status_list:
                # Node更新
                node_filter_data['parameter']['status_id'] = n_status_id
                node_filter_data['parameter']['time_end'] = get_now_datetime()
                tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                if tmp_result[0] is not True:
                    raise Exception()
                
                if targetNode is not None:
                    node_options['next_node_exec_flg'] = '1'
                    next_n_status_id = node_options.get('instance_info_data').get('dict').get('node_status').get('3')
                    next_node_instance_id = node_options.get('target_all_node_list').get('node_list').get(targetNode).get('id')
                    next_target_node_info = {
                        "node_instance_id": next_node_instance_id,
                        "node_name": targetNode,
                        "status_id": next_n_status_id
                    }
                    node_options['next_node_list'].setdefault(targetNode, next_target_node_info)

                if skip_node is not None:
                    if len(skip_node) != 0:
                        tmp_result = self.target_node_skip(node_options, skip_node)
                        if tmp_result[0] is False:
                            raise Exception()
            elif abort_status == bool_master_true:
                # Node更新
                node_filter_data['parameter']['status_id'] = n_status_id
                node_filter_data['parameter']['time_end'] = get_now_datetime()
                tmp_result = self.node_instance_exec_maintenance([node_filter_data], 'Update')
                if tmp_result[0] is not True:
                    raise Exception()
            else:
                pass
            # raise Exception()
        except Exception as e:
            g.applogger.debug(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
            type_, value, traceback_ = sys.exc_info()
            msg = traceback.format_exception(type_, value, traceback_)
            g.applogger.error(msg)
            retBool = False

        result = node_options
        return retBool, result,


# 共通Lib
def get_now_datetime(format='%Y/%m/%d %H:%M:%S', type='str'):
    dt = datetime.now().strftime(format)
    if type == 'str':
        return '{}'.format(dt)
    else:
        return dt


def addline_msg(msg=''):
    import inspect, os
    info = inspect.getouterframes(inspect.currentframe())[1]
    msg_line = "{} ({}:{})".format(msg, os.path.basename(info.filename), info.lineno)
    return msg_line


def load_objcolumn(objdbca, objtable, rest_key, col_class_name='TextColumn', ):
    
    try:
        eval_class_str = "{}(objdbca,objtable,rest_key,'')".format(col_class_name)
        objcolumn = eval(eval_class_str)
    except Exception:
        return False
    return objcolumn

