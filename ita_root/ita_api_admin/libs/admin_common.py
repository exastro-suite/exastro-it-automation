# Copyright 2022 NEC Corporation#
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
"""
admin common function module
"""
from flask import request, g
import os
import base64
import re
import json
import copy
import traceback

from common_libs.common.util import arrange_stacktrace_format
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.exception import AppException
from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate
from common_libs.api import set_api_timestamp, get_api_timestamp, app_exception_response, exception_response, check_request_body
from common_libs.loadtable import *     # noqa: F403
from common_libs.ci.util import set_service_loglevel


def before_request_handler():
    try:
        set_api_timestamp()

        g.LANGUAGE = os.environ.get("DEFAULT_LANGUAGE")
        # create app log instance and message class instance
        g.applogger = AppLog()
        g.appmsg = MessageTemplate(g.LANGUAGE)
        # set applogger.set_level: default:INFO / Use ITA_DB config value
        set_service_loglevel()

        check_request_body()

        # request-header check
        # ヘルスチェック用のURLの場合にUser-IdとRolesを確認しない
        ret = re.search("/internal-api/health-check/liveness$|/internal-api/health-check/readiness$", request.url)
        if ret is None:
            user_id = request.headers.get("User-Id")
            roles_org = request.headers.get("Roles")
            try:
                roles_decode = base64.b64decode(roles_org.encode()).decode("utf-8")
            except Exception:
                raise AppException("400-00001", ["Roles"], ["Roles"])
            roles = roles_decode.split("\n")
            if user_id is None or roles is None or type(roles) is not list:
                raise AppException("400-00001", ["User-Id or Roles"], ["User-Id or Roles"])

            g.USER_ID = user_id
            g.ROLES = roles

            # set log environ format
            g.applogger.set_env_message()

            debug_args = [request.method + ":" + request.url]
            g.applogger.info("[ts={}][api-start]url: {}".format(get_api_timestamp(), *debug_args))

        # set language
        language = request.headers.get("Language")
        if language:
            g.LANGUAGE = language
            g.appmsg.set_lang(language)
            g.applogger.debug("LANGUAGE({}) is set".format(language))

    except AppException as e:
        # catch - raise AppException("xxx-xxxxx", log_format, msg_format)
        return app_exception_response(e)
    except Exception as e:
        # catch - other all error
        return exception_response(e)


def initial_settings_ansible(ws_db, body):

    # 最終更新者を「初期データ」にする
    g.USER_ID = '1'

    # メニュー-テーブル紐付管理の取得(Ansible Automation Controller ホスト一覧)
    objmenu_mtll = load_table.loadTable(ws_db, 'menu_table_link_list')
    menu_table_link_list = objmenu_mtll.rest_filter({'uuid': {'LIST': ['20103']}})
    menu_table_link = menu_table_link_list[1][0]

    # メニュー-カラム紐付管理の取得(インターフェース情報)
    objmenu_mcll = load_table.loadTable(ws_db, 'menu_column_link_list')
    menu_column_link_list = objmenu_mcll.rest_filter({'uuid': {'LIST': ['2010202',
                                                                        '2010203',
                                                                        '2010204',
                                                                        '2010205',
                                                                        '2010206',
                                                                        '2010207',
                                                                        '2010208',
                                                                        '2010209',
                                                                        '2010210']}})
    menu_column_link_list = menu_column_link_list[1]

    # input_limit_settingがTrueの場合
    if (body.get('input_limit_setting') is True):

        # メニュー-テーブル紐付管理の更新(Ansible Automation Controller ホスト一覧)
        if (menu_table_link['parameter']['row_insert_flag'] != 'False' or
            menu_table_link['parameter']['row_update_flag'] != 'False' or
            menu_table_link['parameter']['row_disuse_flag'] != 'False' or
            menu_table_link['parameter']['row_reuse_flag'] != 'False'):      # noqa: E129

            menu_table_link['parameter']['row_insert_flag'] = 'False'
            menu_table_link['parameter']['row_update_flag'] = 'False'
            menu_table_link['parameter']['row_disuse_flag'] = 'False'
            menu_table_link['parameter']['row_reuse_flag'] = 'False'
            del menu_table_link['parameter']['last_updated_user']

            result = objmenu_mtll.exec_maintenance(menu_table_link, '20103', 'Update', False, False)

            if result[0] is not True:
                raise AppException(result[1], [result[2]], [result[2]])

        # メニュー-カラム紐付管理の更新(インターフェース情報)
        for menu_column_link in menu_column_link_list:
            if menu_column_link['parameter']['input_target_flag'] != '0':
                menu_column_link['parameter']['input_target_flag'] = '0'
                del menu_column_link['parameter']['last_updated_user']
                uuid = menu_column_link['parameter']['uuid']
                result = objmenu_mcll.exec_maintenance(menu_column_link, uuid, 'Update', False, False)

                if result[0] is not True:
                    raise AppException(result[1], [result[2]], [result[2]])

    # input_limit_settingがFalseの場合
    elif (body.get('input_limit_setting') is False):

        # メニュー-テーブル紐付管理の更新(Ansible Automation Controller ホスト一覧)
        if (menu_table_link['parameter']['row_insert_flag'] != 'True' or
            menu_table_link['parameter']['row_update_flag'] != 'True' or
            menu_table_link['parameter']['row_disuse_flag'] != 'True' or
            menu_table_link['parameter']['row_reuse_flag'] != 'True'):       # noqa: E129

            menu_table_link['parameter']['row_insert_flag'] = 'True'
            menu_table_link['parameter']['row_update_flag'] = 'True'
            menu_table_link['parameter']['row_disuse_flag'] = 'True'
            menu_table_link['parameter']['row_reuse_flag'] = 'True'
            del menu_table_link['parameter']['last_updated_user']

            result = objmenu_mtll.exec_maintenance(menu_table_link, '20103', 'Update', False, False)

            if result[0] is not True:
                raise AppException(result[1], [result[2]], [result[2]])

        # メニュー-カラム紐付管理の更新(インターフェース情報)
        for menu_column_link in menu_column_link_list:
            if menu_column_link['parameter']['input_target_flag'] != '1':
                menu_column_link['parameter']['input_target_flag'] = '1'
                del menu_column_link['parameter']['last_updated_user']
                uuid = menu_column_link['parameter']['uuid']
                result = objmenu_mcll.exec_maintenance(menu_column_link, uuid, 'Update', False, False)

                if result[0] is not True:
                    raise AppException(result[1], [result[2]], [result[2]])

    # execution_engine_listの設定がある場合
    if 'execution_engine_list' in body.keys():
        # 実行エンジンの有効/無効を設定
        update_settings = [[], [], []]
        if 'Ansible-Core' in body.get('execution_engine_list'):
            update_settings[0] = ['0', '1']
        else:
            update_settings[0] = ['1', '1']
        if 'Ansible Automation Controller' in body.get('execution_engine_list'):
            update_settings[1] = ['0', '2']
        else:
            update_settings[1] = ['1', '2']
        if 'Ansible Execution Agent' in body.get('execution_engine_list'):
            update_settings[2] = ['0', '3']
        else:
            update_settings[2] = ['1', '3']

        sql = "UPDATE T_ANSC_EXEC_ENGINE SET DISUSE_FLAG=%s WHERE ID=%s"
        for update_setting in update_settings:
            ws_db.sql_execute(sql, update_setting)

    # initial_dataの設定がある場合
    if 'initial_data' in body.keys():
        # ansible_automation_controller_host_listの設定がある場合
        if 'ansible_automation_controller_host_list' in body.get('initial_data').keys():
            initial_data_aac_hosts = body.get('initial_data').get('ansible_automation_controller_host_list')

            objmenu_aach = load_table.loadTable(ws_db, 'ansible_automation_controller_host_list')
            registerd_aac_hosts = objmenu_aach.rest_filter({'discard': {'LIST': ['0']}})

            initial_host_list = []
            for initial_data_aac_host in initial_data_aac_hosts:
                match_flg = False
                host                                = initial_data_aac_host.get('parameter').get('host')                                # noqa: E221
                authentication_method               = initial_data_aac_host.get('parameter').get('authentication_method')               # noqa: E221
                user                                = initial_data_aac_host.get('parameter').get('user')                                # noqa: E221
                password                            = initial_data_aac_host.get('parameter').get('password')                            # noqa: E221
                ssh_private_key_file                = initial_data_aac_host.get('parameter').get('ssh_private_key_file')                # noqa: E221
                ssh_private_key_file_base64         = initial_data_aac_host.get('file').get('ssh_private_key_file')                     # noqa: E221
                passphrase                          = initial_data_aac_host.get('parameter').get('passphrase')                          # noqa: E221
                ansible_automation_controller_port  = initial_data_aac_host.get('parameter').get('ansible_automation_controller_port')  # noqa: E221
                execution_node = None
                if 'isolated_tower' in initial_data_aac_host.get('parameter').keys():
                    execution_node                  = initial_data_aac_host.get('parameter').get('isolated_tower')                      # noqa: E221
                if 'execution_node' in initial_data_aac_host.get('parameter').keys():
                    execution_node                  = initial_data_aac_host.get('parameter').get('execution_node')                      # noqa: E221
                remarks                             = initial_data_aac_host.get('parameter').get('remarks')                             # noqa: E221
                initial_host_list.append(host)

                for registerd_aac_host in registerd_aac_hosts[1]:
                    # 既存データに有る初期データは更新する
                    if host == registerd_aac_host.get('parameter').get('host'):
                        update_aac_host = registerd_aac_host
                        if 'authentication_method' in initial_data_aac_host.get('parameter').keys():
                            update_aac_host["parameter"]["authentication_method"] = authentication_method
                        if 'user' in initial_data_aac_host.get('parameter').keys():
                            update_aac_host["parameter"]["user"] = user
                        if 'password' in initial_data_aac_host.get('parameter').keys():
                            update_aac_host["parameter"]["password"] = password
                        if 'ssh_private_key_file' in initial_data_aac_host.get('parameter').keys():
                            update_aac_host["parameter"]["ssh_private_key_file"] = ssh_private_key_file
                        if 'ssh_private_key_file' in initial_data_aac_host.get('file').keys():
                            update_aac_host["file"]["ssh_private_key_file"] = ssh_private_key_file_base64
                        if 'passphrase' in initial_data_aac_host.get('parameter').keys():
                            update_aac_host["parameter"]["passphrase"] = passphrase
                        if 'ansible_automation_controller_port' in initial_data_aac_host.get('parameter').keys():
                            update_aac_host["parameter"]["ansible_automation_controller_port"] = ansible_automation_controller_port
                        if 'isolated_tower' in initial_data_aac_host.get('parameter').keys():
                            update_aac_host["parameter"]["execution_node"] = execution_node
                        if 'execution_node' in initial_data_aac_host.get('parameter').keys():
                            update_aac_host["parameter"]["execution_node"] = execution_node
                        if 'remarks' in initial_data_aac_host.get('parameter').keys():
                            update_aac_host["parameter"]["remarks"] = remarks

                        del update_aac_host['parameter']['last_updated_user']
                        no = update_aac_host["parameter"]["no"]
                        result = objmenu_aach.exec_maintenance(update_aac_host, no, 'Update', False, False)

                        if result[0] is not True:
                            raise AppException(result[1], [result[2]], [result[2]])

                        match_flg = True
                        break

                # 既存データに無い初期データは登録する
                if match_flg is False:
                    insert_aac_host = {"parameter": {"host": host,
                                                     "authentication_method": authentication_method,
                                                     "user": user,
                                                     "password": password,
                                                     "ssh_private_key_file": ssh_private_key_file,
                                                     "passphrase": passphrase,
                                                     "ansible_automation_controller_port": ansible_automation_controller_port,
                                                     "execution_node": execution_node,
                                                     "remarks": remarks},
                                       "file": {"ssh_private_key_file": ssh_private_key_file_base64}}

                    result = objmenu_aach.exec_maintenance(insert_aac_host, "", 'Insert', False, False)

                    if result[0] is not True:
                        raise AppException(result[1], [result[2]], [result[2]])

            for registerd_aac_host in registerd_aac_hosts[1]:
                # 初期データに無い既存データは廃止する
                if registerd_aac_host.get('parameter').get('host') not in initial_host_list:

                    discard_aac_host = registerd_aac_host
                    no = discard_aac_host["parameter"]["no"]
                    discard_aac_host["parameter"]["discard"] = "1"
                    del discard_aac_host['parameter']['last_updated_user']
                    result = objmenu_aach.exec_maintenance(discard_aac_host, no, 'Discard', False, False)

                    if result[0] is not True:
                        raise AppException(result[1], [result[2]], [result[2]])

        # interface_info_ansibleの設定がある場合
        if 'interface_info_ansible' in body.get('initial_data').keys():
            if 'parameter' in body.get('initial_data').get('interface_info_ansible').keys():

                # インターフェース情報の更新を行う
                initial_iia = body.get('initial_data').get('interface_info_ansible').get('parameter')

                objmenu_iia = load_table.loadTable(ws_db, 'interface_info_ansible')
                registerd_iia = objmenu_iia.rest_filter({'discard': {'LIST': ['0']}})

                update_iia = registerd_iia[1][0]

                execution_engine                        = initial_iia.get('execution_engine')                        # noqa: E221
                representative_server                   = initial_iia.get('representative_server')                   # noqa: E221
                ansible_automation_controller_protocol  = initial_iia.get('ansible_automation_controller_protocol')  # noqa: E221
                ansible_automation_controller_port      = initial_iia.get('ansible_automation_controller_port')      # noqa: E221
                organization_name                       = initial_iia.get('organization_name')                       # noqa: E221
                authentication_token                    = initial_iia.get('authentication_token')                    # noqa: E221
                delete_runtime_data                     = initial_iia.get('delete_runtime_data')                     # noqa: E221
                proxy_address                           = initial_iia.get('proxy_address')                           # noqa: E221
                proxy_port                              = initial_iia.get('proxy_port')                              # noqa: E221

                if 'execution_engine' in initial_iia.keys():
                    update_iia["parameter"]["execution_engine"] = execution_engine
                if 'representative_server' in initial_iia.keys():
                    update_iia["parameter"]["representative_server"] = representative_server
                if 'ansible_automation_controller_protocol' in initial_iia.keys():
                    update_iia["parameter"]["ansible_automation_controller_protocol"] = ansible_automation_controller_protocol
                if 'ansible_automation_controller_port' in initial_iia.keys():
                    update_iia["parameter"]["ansible_automation_controller_port"] = ansible_automation_controller_port
                if 'organization_name' in initial_iia.keys():
                    update_iia["parameter"]["organization_name"] = organization_name
                if 'authentication_token' in initial_iia.keys():
                    update_iia["parameter"]["authentication_token"] = authentication_token
                if 'delete_runtime_data' in initial_iia.keys():
                    update_iia["parameter"]["delete_runtime_data"] = delete_runtime_data
                if 'proxy_address' in initial_iia.keys():
                    update_iia["parameter"]["proxy_address"] = proxy_address
                if 'proxy_port' in initial_iia.keys():
                    update_iia["parameter"]["proxy_port"] = proxy_port

                del update_iia['parameter']['last_updated_user']
                item_number = update_iia["parameter"]["item_number"]
                result = objmenu_iia.exec_maintenance(update_iia, item_number, 'Update', False, False, True, True)

                if result[0] is not True:
                    raise AppException(result[1], [result[2]], [result[2]])

    return ''


def loglevel_settings_container(common_db, parameter):
    """
        loglevel_settings_container
    Args:
        common_db : DBConnectCommon()
        parameter : { service_name, log_level }
    Returns:
        True
    """
    result_data = True
    # set user_id
    user_id = request.headers.get("User-Id")
    # set table info
    table_name = "T_COMN_LOGLEVEL"
    primary_key_name = "PRIMARY_KEY"
    table_columns_info = common_db.table_columns_get(table_name)
    columns_info = table_columns_info[0]
    primary_key_name = table_columns_info[1][0]

    # set base_data_list
    base_data_list = {}
    for column_name in columns_info:
        base_data_list[column_name] = None
    base_data_list['DISUSE_FLAG'] = 0

    # accept_log_level
    accept_log_level = [
        # "CRITICAL",
        # "ERROR",
        # "WARNING",
        "INFO",
        "DEBUG",
    ]

    # get all data
    where_str = "WHERE `DISUSE_FLAG`='0'"
    loglevel_service_list = common_db.table_select(table_name, where_str)

    # check parameter
    for service_name, log_level in parameter.items():
        # check accept_log_level
        chk_log_level = log_level in accept_log_level
        # check service_name
        pattern = re.compile(r"([^A-Za-z0-9\-]+)")
        chk_service_name = True if service_name is not None and len(service_name) <= 255 else False
        re_result = pattern.findall(service_name)
        chk_service_name = True if chk_service_name is True and len(re_result) == 0 else False
        if chk_log_level is False or chk_service_name is False:
            msg_args = [service_name, log_level]
            raise AppException("499-01401", msg_args, msg_args)

    # service_list
    service_list = {}
    for loglevel_service in loglevel_service_list:
        log_level = loglevel_service.get('LOG_LEVEL')
        if (log_level is not None) and (len(log_level) > 0):
            service_list[loglevel_service['SERVICE_NAME']] = loglevel_service
        else:
            service_list[loglevel_service['SERVICE_NAME']] = None

    try:
        service_name = None
        log_level = None
        # transaction start
        common_db.db_transaction_start()

        for service_name, log_level in parameter.items():

            query_exec_mode = None
            if service_name in service_list:
                # set data_list: update
                data_list = base_data_list.copy()
                data_list.update(service_list.get(service_name))
                if log_level == data_list.get('LOG_LEVEL'):
                    continue
                data_list['LOG_LEVEL'] = log_level
                data_list['LAST_UPDATE_USER'] = user_id
                query_exec_mode = "UPDATE"
            else:
                continue
                # set data_list: insert
                data_list = base_data_list.copy()
                data_list['SERVICE_NAME'] = service_name
                data_list['LOG_LEVEL'] = log_level
                data_list['LAST_UPDATE_USER'] = user_id
                query_exec_mode = "INSERT"

            # common_db.table_xxx
            if query_exec_mode == "INSERT":
                common_db.table_insert(table_name, data_list, primary_key_name, is_register_history=False)
            elif query_exec_mode == "UPDATE":
                common_db.table_update(table_name, data_list, primary_key_name, is_register_history=False)

    except AppException as _app_e:  # noqa: F405
        # transaction end:rollback
        common_db.db_transaction_end(False)
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        # transaction end:rollback
        common_db.db_transaction_end(False)

        t = traceback.format_exc()
        g.applogger.error("[ts={}] {}".format(get_api_timestamp(), arrange_stacktrace_format(t)))

        msg_args = [service_name, log_level]
        raise AppException("499-01401", msg_args, msg_args)

    # transaction end:commit
    common_db.db_transaction_end(True)
    common_db.db_disconnect()

    return result_data,


def get_backyard_execute_status_list():
    """
        get_backyard_execute_status_list
    Args:
    Returns:
        Boolean, backyard_execute_status_list(dict)
    """
    try:
        common_db = DBConnectCommon()  # noqa: F405

        # set language
        language = request.headers.get("Language")
        if not language:
            language = os.environ.get("DEFAULT_LANGUAGE")

        # set return value
        all_exec_count = 0
        backyard_execute_status_list = {}

        # チェック対象の一覧。テーブル名、カラム名、ステータスID等。
        tmp_backyard_check_list = {
            "ansible": {
                "container_name": "ita-by-ansible-execute",
                "table_name": "V_ANSC_EXEC_STS_INST",
                "primary_key": "EXECUTION_NO",
                "column_name": "STATUS_ID",
                "target_status_list": ["2", "3", "4"],  # 2:準備中, 3:実行中, 4:実行中(遅延)
                "status_name_table": "T_ANSC_EXEC_STATUS",
                "status_name_id_column": "EXEC_STATUS_ID",
                "status_name_column": "EXEC_STATUS_NAME",
                "add_count": True
            },
            "conductor": {
                "container_name": "ita-by-conductor-synchronize",
                "table_name": "T_COMN_CONDUCTOR_INSTANCE",
                "primary_key": "CONDUCTOR_INSTANCE_ID",
                "column_name": "STATUS_ID",
                "target_status_list": ["3", "4", "5"],  # 3:実行中, 4:実行中(遅延), 5:一時停止
                "status_name_table": "T_COMN_CONDUCTOR_STATUS",
                "status_name_id_column": "STATUS_ID",
                "status_name_column": "STATUS_NAME",
                "add_count": False  # Conductorは_execute_countに加算をしない。
            },
            "excel_export_import": {
                "container_name": "ita-by-excel-export-import",
                "table_name": "T_BULK_EXCEL_EXPORT_IMPORT",
                "primary_key": "EXECUTION_NO",
                "column_name": "STATUS",
                "target_status_list": ["2"],  # 2:実行中
                "status_name_table": "T_DP_STATUS_MASTER",
                "status_name_id_column": "ROW_ID",
                "status_name_column": "TASK_STATUS_NAME",
                "add_count": True
            },
            "menu_export_import": {
                "container_name": "ita-by-menu-export-import",
                "table_name": "T_MENU_EXPORT_IMPORT",
                "primary_key": "EXECUTION_NO",
                "column_name": "STATUS",
                "target_status_list": ["2"],  # 2:実行中
                "status_name_table": "T_DP_STATUS_MASTER",
                "status_name_id_column": "ROW_ID",
                "status_name_column": "TASK_STATUS_NAME",
                "add_count": True
            },
            "menu_create": {
                "container_name": "ita-by-menu-create",
                "table_name": "T_MENU_CREATE_HISTORY",
                "primary_key": "HISTORY_ID",
                "column_name": "STATUS_ID",
                "target_status_list": ["2"],  # 2:実行中
                "status_name_table": "T_MENU_CREATE_STATUS",
                "status_name_id_column": "STATUS_ID",
                "status_name_column": "STATUS_NAME",
                "add_count": True
            },
            "terraform_cli": {
                "container_name": "ita-by-terraform-cli-execute",
                "table_name": "T_TERC_EXEC_STS_INST",
                "primary_key": "EXECUTION_NO",
                "column_name": "STATUS_ID",
                "target_status_list": ["2", "3", "4"],  # 2:準備中, 3:実行中, 4:実行中(遅延)
                "status_name_table": "T_TERF_EXEC_STATUS",
                "status_name_id_column": "EXEC_STATUS_ID",
                "status_name_column": "EXEC_STATUS_NAME",
                "add_count": True
            },
            "terraform_cloud_ep": {
                "container_name": "ita-by-terraform-cloud-ep-execute",
                "table_name": "T_TERE_EXEC_STS_INST",
                "primary_key": "EXECUTION_NO",
                "column_name": "STATUS_ID",
                "target_status_list": ["2", "3", "4"],  # 2:準備中, 3:実行中, 4:実行中(遅延)
                "status_name_table": "T_TERF_EXEC_STATUS",
                "status_name_id_column": "EXEC_STATUS_ID",
                "status_name_column": "EXEC_STATUS_NAME",
                "add_count": True
            }
        }

        # Organizationの一覧を取得
        organization_list = []
        where_str = "WHERE `DISUSE_FLAG`='0'"
        t_comn_organization_db_info_records = common_db.table_select('T_COMN_ORGANIZATION_DB_INFO', where_str)
        for record in t_comn_organization_db_info_records:
            organization_data = {'organization_id': record.get('ORGANIZATION_ID'), 'db_database': record.get('DB_DATABASE'), 'no_install_driver': record.get('NO_INSTALL_DRIVER')}  # noqa: E501
            organization_list.append(organization_data)

        # Organizationの一覧でループスタート
        backyard_execute_status_list['organizations'] = []
        for org_data in organization_list:
            # 対象一覧をコピー
            backyard_check_list = copy.deepcopy(tmp_backyard_check_list)

            # インストール対象外ドライバについて、ループ対象から削除する
            no_install_driver = org_data.get('no_install_driver')
            if no_install_driver:
                no_install_driver_list = json.loads(no_install_driver)
                for exclusion_target in no_install_driver_list:
                    if exclusion_target in backyard_check_list:
                        del backyard_check_list[exclusion_target]

            org_id = org_data.get('organization_id')
            org_db = DBConnectOrg(org_id)  # noqa: F405
            organization_exec_count = 0

            # 返却値にorganization_idでkeyを作成
            organization_status_data = {}
            organization_status_data['id'] = org_id
            organization_status_data['workspaces'] = []

            # Workspaceの一覧を取得
            workspace_list = []
            where_str = "WHERE `DISUSE_FLAG`='0'"
            t_comn_workspace_db_info_rocords = org_db.table_select("T_COMN_WORKSPACE_DB_INFO", where_str)  # noqa: E501
            for record in t_comn_workspace_db_info_rocords:
                workspace_data = {'workspace_id': record.get('WORKSPACE_ID'), 'db_database': record.get('DB_DATABASE')}
                workspace_list.append(workspace_data)

            # Workspaceの一覧でループスタート
            for ws_data in workspace_list:
                ws_id = ws_data.get('workspace_id')
                ws_db = DBConnectWs(ws_id, org_id)  # noqa: F405
                workspace_exec_count = 0
                workspace_status_data = {}
                workspace_status_data['id'] = ws_id
                workspace_status_data['backyards'] = {}

                for backyard_data in backyard_check_list.values():
                    # 返却値にbackyardコンテナ名でkeyを作成
                    container_name = backyard_data.get('container_name')
                    workspace_status_data['backyards'][container_name] = []

                    # ステータスIDと名称を取得
                    status_name_data = {}
                    status_name_table = backyard_data.get('status_name_table')
                    status_name_table_records = ws_db.table_select(status_name_table)
                    for status_name_record in status_name_table_records:
                        status_id = status_name_record.get(backyard_data.get('status_name_id_column'))
                        status_name_data[status_id] = status_name_record.get(backyard_data.get('status_name_column') + '_' + language.upper())

                    # バックヤード実行管理テーブルから完了形以外のレコードを取得
                    table_name = backyard_data.get('table_name')
                    column_name = backyard_data.get('column_name')
                    status_list_str = ','.join(backyard_data.get('target_status_list'))
                    where_str = "WHERE `DISUSE_FLAG`='0' AND {} IN ({})".format(column_name, status_list_str)
                    backyard_execute_table_records = ws_db.table_select(table_name, where_str)

                    # バックヤード実行管理テーブルのレコードからデータを形成
                    for execute_record in backyard_execute_table_records:
                        primary_key = backyard_data.get('primary_key')
                        id = execute_record.get(primary_key)
                        status_id = execute_record.get(column_name)
                        status_name = status_name_data.get(status_id)
                        last_update_timestamp = execute_record.get('LAST_UPDATE_TIMESTAMP')
                        execute_data = {'id': id, 'status_id': status_id, 'status_name': status_name, 'last_update_timestamp': last_update_timestamp}
                        workspace_status_data['backyards'][container_name].append(execute_data)

                        # Workspace単位の実行中対象数を加算
                        if backyard_data.get('add_count') is True:
                            workspace_exec_count += 1
                ws_db.db_disconnect()

                # Workspace単位の実行中対象数を格納
                workspace_status_data['execute_count'] = workspace_exec_count

                # Organization単位の実行中対象数を加算
                organization_exec_count += workspace_exec_count

                # Workspaceのデータを追加
                organization_status_data['workspaces'].append(workspace_status_data)

            # Organization単位の実行中対象数を格納
            organization_status_data['execute_count'] = organization_exec_count

            # 全体の実行中対象数を加算
            all_exec_count += organization_exec_count

            # Organizationのデータを追加
            backyard_execute_status_list['organizations'].append(organization_status_data)

            org_db.db_disconnect()

        # 全体の実行中対象数を格納
        backyard_execute_status_list['execute_count'] = all_exec_count

        common_db.db_disconnect()

        return backyard_execute_status_list

    except Exception as e:
        if "common_db" in locals():
            common_db.db_disconnect()
        if "org_db" in locals():
            org_db.db_disconnect()
        if "ws_db" in locals():
            ws_db.db_disconnect()

        # catch - other all error
        return exception_response(e, True)
