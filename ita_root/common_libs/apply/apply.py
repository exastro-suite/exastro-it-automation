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

import json
import base64
import time
import datetime
from flask import g  # noqa: F401

from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from common_libs.conductor.classes.exec_util import *  # noqa: F403
import traceback
from common_libs.common.util import get_iso_datetime, arrange_stacktrace_format

def check_params(request_data):
    """
    """

    conductor_class_name = request_data.get('conductor_class_name', None)
    operation_name = request_data.get('operation_name', "")
    schedule_date = request_data.get('schedule_date', None)
    parameter_info = request_data.get('parameter_info', [])
    block = request_data.get('block', False)

    # Conductor確認
    if not conductor_class_name:
        status_code = "499-01901"
        log_msg_args = [conductor_class_name, ]
        api_msg_args = [conductor_class_name, ]
        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    # パラメーター情報確認
    if parameter_info:
        # 型の確認
        if isinstance(parameter_info, dict) is True:
            parameter_info = [parameter_info, ]

        if isinstance(parameter_info, list) is False:
            status_code = "499-01902"
            log_msg_args = [None, type(parameter_info)]
            api_msg_args = [None, type(parameter_info)]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        # フォーマットの確認
        for params in parameter_info:
            # 型の確認
            if isinstance(params, dict) is False:
                status_code = "499-01902"
                log_msg_args = [None, type(parameter_info)]
                api_msg_args = [None, type(parameter_info)]
                raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

            for menu, param in params.items():
                if isinstance(param, dict) is True:
                    param = [param, ]

                if isinstance(param, list) is False:
                    status_code = "499-01902"
                    log_msg_args = [menu, type(parameter_info)]
                    api_msg_args = [menu, type(parameter_info)]
                    raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

                for p in param:
                    # 必須キーが存在すること
                    if 'type' not in p or 'parameter' not in p:
                        status_code = "499-01903"
                        log_msg_args = [menu, ]
                        api_msg_args = [menu, ]
                        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

                    # type が register/update/discard/restore のいずれかであること
                    if isinstance(p['type'], str) is False \
                    or p['type'] not in ['Register', 'Update', 'Restore', 'Discard']:
                        status_code = "499-01904"
                        log_msg_args = [menu, p['type']]
                        api_msg_args = [menu, p['type']]
                        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    return True


def get_specify_menu(request_data):
    """
    """

    menu_list = []

    conductor_class_name = request_data.get('conductor_class_name', None)
    operation_name = request_data.get('operation_name', "")
    schedule_date = request_data.get('schedule_date', None)
    parameter_info = request_data.get('parameter_info', [])
    block = request_data.get('block', False)

    if not parameter_info:
        return menu_list

    if isinstance(parameter_info, dict):
        parameter_info = [parameter_info, ]

    for params in parameter_info:
        if isinstance(params, dict):
            params = [params, ]

        menus = []
        for param in params:
            menus = list(param.keys())

        menu_list.extend(menus)

    menu_list = list(set(menu_list))

    return menu_list


def rest_apply_parameter(objdbca, request_data, menu_list, parameter_sheet_list, conductor_menu_list):
    """
    """

    def _analyse_error_info(obj, func, menu):

        tmp = obj
        if isinstance(tmp, str) is True:
            try:
                tmp = json.loads(tmp)
            except json.JSONDecodeError:
                obj = '%s, menu:%s' % (obj, menu)
                return obj

        if type(tmp) in (list, dict):
            for k, v in func(tmp):
                tmp[k] = _analyse_error_info(v, func, menu)

        return tmp

    def _generate_operation_name(obj, ope_name, now):

        # オペレーション名の存在確認
        data = {}
        data['discard'] = {'NORMAL': '0'}
        data['operation_name'] = {'LIST': [ope_name, ]}

        status_code, rset, msg = obj.rest_filter(data, 'nomal')
        if status_code != '000-00000':
            log_msg_args = [msg]
            api_msg_args = [msg]
            raise AppException(status_code, log_msg_args, api_msg_args)

        if len(rset) > 0:
            return False

        # オペレーション生成
        data = {}
        data['type'] = 'Register'
        data['file'] = {}
        data['parameter'] = {}
        data['parameter']['environment'] = None
        data['parameter']['language'] = g.LANGUAGE
        data['parameter']['last_run_date'] = None
        data['parameter']['operation_name'] = ope_name
        data['parameter']['scheduled_date_for_execution'] = now.strftime('%Y/%m/%d %H:%M:%S')

        rset = obj.exec_maintenance(data, '', 'Register')
        if rset[0] is not True:
            list_exec_result = obj.get_exec_result()
            for tmp_exec_result in list_exec_result:
                entry_parameter = tmp_exec_result.get('parameter')
                obj.exec_restore_action(entry_parameter, tmp_exec_result)

            # 集約エラーメッセージ(JSON化)
            status_code, msg = obj.get_error_message_str()
            if status_code is None:
                status_code = '999-99999'

            elif len(status_code) == 0:
                status_code = '999-99999'

            if isinstance(msg, list):
                log_msg_args = msg
                api_msg_args = msg

            else:
                log_msg_args = [msg]
                api_msg_args = [msg]

            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        return True


    result_data = {}
    status_code = "000-00000"

    conductor_class_name = request_data.get('conductor_class_name', None)
    operation_name = request_data.get('operation_name', "")
    schedule_date = request_data.get('schedule_date', None)
    parameter_info = request_data.get('parameter_info', [])
    block = request_data.get('block', False)

    # loadTableオブジェクト生成
    loadtable_obj_dict = {}
    for menu in menu_list:
        if menu in loadtable_obj_dict:
            continue

        loadtable_obj_dict[menu] = load_table.loadTable(objdbca, menu)
        if loadtable_obj_dict[menu].get_objtable() is False:
            status_code = "401-00003"
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    # テーブルロック
    locktable_list = []
    if isinstance(parameter_info, dict):
        parameter_info = [parameter_info, ]
    for params in parameter_info:
        if isinstance(params, dict):
            params = [params, ]
        for param in params:
            for menu, val in param.items():
                if isinstance(val, dict):
                    val = [val, ]
                for v in val:
                    # 更新系の操作の場合のみ、ロック対象とする
                    if v['type'] in ['Update', 'Restore', 'Discard']:
                        tmp_list = loadtable_obj_dict[menu].get_locktable()
                        if tmp_list is None:
                            tmp_list = [loadtable_obj_dict[menu].get_table_name()]
                        else:
                            tmp_list = json.loads(tmp_list)
                            tmp_list.append(loadtable_obj_dict[menu].get_table_name())
                        locktable_list = list(set(locktable_list) | set(tmp_list))

    if len(locktable_list) > 0:
        locktable_list.sort()
        objdbca.table_lock(locktable_list)

    # オペレーション確認
    now = None
    ope_gen_flag = False
    if operation_name:
        now = datetime.datetime.now()
        ope_gen_flag = _generate_operation_name(loadtable_obj_dict['operation_list'], operation_name, now)

    else:
        while ope_gen_flag is False:
            now = datetime.datetime.now()
            for i in range(10):
                operation_name = now.strftime('%Y%m%d%H%M%S%f') + str(i)
                ope_gen_flag = _generate_operation_name(loadtable_obj_dict['operation_list'], operation_name, now)
                if ope_gen_flag is True:
                    break

    # パラメーター確認
    if ope_gen_flag is True and not parameter_info:
        status_code = "499-01905"
        log_msg_args = []
        api_msg_args = []
        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    # オペレーション自動払い出しの自動設定が必要な標準メニューの定義
    std_menu_list = {}
    if ope_gen_flag is True:
        std_menu_list = {
            # Conductor定期作業実行
            "conductor_regularly_execution": {
                "col_name_rest" : "operation_name",
                "value"         : operation_name
            },
            # ホスト紐付管理
            "host_link_list": {
                "col_name_rest" : "operation",
                "value"         : operation_name
            },
        }

    # パラメーター適用
    if isinstance(parameter_info, dict):
        parameter_info = [parameter_info, ]

    for params in parameter_info:
        if isinstance(params, dict):
            params = [params, ]

        for param in params:
            for menu, val in param.items():
                if isinstance(val, dict):
                    val = [val, ]

                for v in val:
                    # オペレーションを生成した場合、生成したオペレーション名を適用する
                    if ope_gen_flag is True and menu in parameter_sheet_list:
                        if 'operation_name_select' not in v['parameter'] \
                        or not v['parameter']['operation_name_select']:
                            v['parameter']['operation_name_select'] = '%s_%s' % (
                                now.strftime('%Y/%m/%d %H:%M'), operation_name
                            )

                    if ope_gen_flag is True and menu in std_menu_list:
                        col_name_rest = std_menu_list[menu]['col_name_rest']
                        if col_name_rest not in v['parameter'] \
                        or not v['parameter'][col_name_rest]:
                            v['parameter'][col_name_rest] = std_menu_list[menu]['value']

                    # テーブル情報（カラム、PK取得）
                    target_uuid = ''
                    column_list = loadtable_obj_dict[menu].get_column_list()
                    primary_key = loadtable_obj_dict[menu].get_primary_key()
                    target_uuid_key = loadtable_obj_dict[menu].get_rest_key(primary_key)
                    if 'parameter' in v:
                        target_uuid = v.get('parameter').get(target_uuid_key)

                    # 更新系の操作の場合、最終更新日時を取得
                    if target_uuid and v['type'] in ['Update', 'Restore', 'Discard'] \
                    and ('last_update_date_time' not in v['parameter'] or not v['parameter']['last_update_date_time']):
                        filter_parameter = {}
                        filter_parameter[target_uuid_key] = {'LIST': [target_uuid]}
                        status_code, rset, msg = loadtable_obj_dict[menu].rest_filter(filter_parameter, 'nomal')
                        if status_code == '000-00000' and len(rset) > 0:
                            v['parameter']['last_update_date_time'] = rset[0]['parameter']['last_update_date_time']

                    # maintenance呼び出し
                    rset = loadtable_obj_dict[menu].exec_maintenance(v, target_uuid, v['type'])
                    loadtable_obj_dict[menu].set_error_message()

                if loadtable_obj_dict[menu].get_error_message_count() > 0:
                    # 想定内エラーの切り戻し処理
                    list_exec_result = loadtable_obj_dict[menu].get_exec_result()
                    for tmp_exec_result in list_exec_result:
                        entry_parameter = tmp_exec_result.get('parameter')
                        loadtable_obj_dict[menu].exec_restore_action(entry_parameter, tmp_exec_result)

                    # 集約エラーメッセージ(JSON化)
                    status_code, msg = loadtable_obj_dict[menu].get_error_message_str()
                    if status_code is None:
                        status_code = '999-99999'

                    elif len(status_code) == 0:
                        status_code = '999-99999'

                    # エラーメッセージにメニュー名(REST)を付与
                    func = lambda x: x.items() if isinstance(x, dict) else enumerate(x)
                    msg = _analyse_error_info(msg, func, menu)

                    if isinstance(msg, list):
                        log_msg_args = msg
                        api_msg_args = msg

                    else:
                        log_msg_args = [msg]
                        api_msg_args = [msg]

                    raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    # 10秒スリープ(適用データの反映待ち)
    # time.sleep(10)

    # Conductor作業実行の要求情報を作成
    data = {}
    data['conductor_class_name'] = conductor_class_name
    data['operation_name'] = operation_name
    data['schedule_date'] = schedule_date

    objmenus = {}
    for menu in conductor_menu_list:
        if menu == "conductor_instance_list":
            objmenus["objconductor"] = loadtable_obj_dict[menu]

        elif menu == "conductor_node_instance_list":
            objmenus["objnode"] = loadtable_obj_dict[menu]

        elif menu == "movement_list":
            objmenus["objmovement"] = loadtable_obj_dict[menu]

        elif menu == "conductor_class_edit":
            objmenus["objcclass"] = loadtable_obj_dict[menu]

        elif menu == "conductor_notice_definition":
            objmenus["objcnotice"] = loadtable_obj_dict[menu]

    try:
        # 入力パラメータ フォーマットチェック
        objCexec = ConductorExecuteLibs(objdbca, 'conductor_class_edit', objmenus)  # noqa: F405
        chk_parameter = objCexec.chk_execute_parameter_format(data)
        data = chk_parameter[2]

        # Conductor実行　パラメータ生成
        create_parameter = objCexec.create_execute_register_parameter(data)
        if create_parameter[0] != '000-00000':
            raise Exception()

        # conducror_instance_id発番、load_table用パラメータ
        conductor_parameter = create_parameter[1].get('conductor')
        node_parameters = create_parameter[1].get('node')
        conductor_instance_id = create_parameter[1].get('conductor_instance_id')

        # conductor instanceテーブルへのレコード追加
        iem_result = objCexec.conductor_instance_exec_maintenance(conductor_parameter)
        if iem_result[0] is not True:
            raise Exception()

        # node instanceテーブルへのレコード追加
        iem_result = objCexec.node_instance_exec_maintenance(node_parameters)
        if iem_result[0] is not True:
            raise Exception()

        result_data["conductor_instance_id"] = conductor_instance_id

    except Exception:
        t = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
        status_code = "499-00804"
        log_msg_args = [conductor_class_name, operation_name, schedule_date]
        api_msg_args = [conductor_class_name, operation_name, schedule_date]
        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    return status_code, result_data


