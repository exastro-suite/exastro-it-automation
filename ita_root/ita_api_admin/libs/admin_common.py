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

from common_libs.common.exception import AppException
from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate
from common_libs.api import set_api_timestamp, get_api_timestamp, app_exception_response, exception_response, check_request_body
from common_libs.loadtable import *     # noqa: F403


def before_request_handler():
    try:
        set_api_timestamp()

        g.LANGUAGE = os.environ.get("DEFAULT_LANGUAGE")
        # create app log instance and message class instance
        g.applogger = AppLog()
        g.applogger.set_level(os.environ.get("LOG_LEVEL"))
        g.appmsg = MessageTemplate(g.LANGUAGE)

        check_request_body()

        # request-header check
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
            g.applogger.info("LANGUAGE({}) is set".format(language))
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

            result = objmenu_mtll.exec_maintenance(menu_table_link, '20103', 'Update', False, False)

            if result[0] is not True:
                raise AppException(result[1], [result[2]], [result[2]])

        # メニュー-カラム紐付管理の更新(インターフェース情報)
        for menu_column_link in menu_column_link_list:
            if menu_column_link['parameter']['input_target_flag'] != '0':
                menu_column_link['parameter']['input_target_flag'] = '0'
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

            result = objmenu_mtll.exec_maintenance(menu_table_link, '20103', 'Update', False, False)

            if result[0] is not True:
                raise AppException(result[1], [result[2]], [result[2]])

        # メニュー-カラム紐付管理の更新(インターフェース情報)
        for menu_column_link in menu_column_link_list:
            if menu_column_link['parameter']['input_target_flag'] != '1':
                menu_column_link['parameter']['input_target_flag'] = '1'
                uuid = menu_column_link['parameter']['uuid']
                result = objmenu_mcll.exec_maintenance(menu_column_link, uuid, 'Update', False, False)

                if result[0] is not True:
                    raise AppException(result[1], [result[2]], [result[2]])

    # execution_engine_listの設定がある場合
    if 'execution_engine_list' in body.keys():
        # 実行エンジンの有効/無効を設定
        update_settings = [[], []]
        if 'Ansible-Core' in body.get('execution_engine_list'):
            update_settings[0] = ['0', '1']
        else:
            update_settings[0] = ['1', '1']
        if 'Ansible Automation Controller' in body.get('execution_engine_list'):
            update_settings[1] = ['0', '2']
        else:
            update_settings[1] = ['1', '2']

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
                host                        = initial_data_aac_host.get('parameter').get('host')                    # noqa: E221
                authentication_method       = initial_data_aac_host.get('parameter').get('authentication_method')   # noqa: E221
                user                        = initial_data_aac_host.get('parameter').get('user')                    # noqa: E221
                password                    = initial_data_aac_host.get('parameter').get('password')                # noqa: E221
                ssh_private_key_file        = initial_data_aac_host.get('parameter').get('ssh_private_key_file')    # noqa: E221
                ssh_private_key_file_base64 = initial_data_aac_host.get('file').get('ssh_private_key_file')         # noqa: E221
                passphrase                  = initial_data_aac_host.get('parameter').get('passphrase')              # noqa: E221
                isolated_tower              = initial_data_aac_host.get('parameter').get('isolated_tower')          # noqa: E221
                remarks                     = initial_data_aac_host.get('parameter').get('remarks')                 # noqa: E221
                initial_host_list.append(host)

                for registerd_aac_host in registerd_aac_hosts[1]:
                    # 既存データに無い初期データは更新する
                    if host == registerd_aac_host.get('parameter').get('host'):
                        update_aac_host = registerd_aac_host
                        if 'check_authentication_method' in initial_data_aac_host.get('parameter').keys():
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
                        if 'isolated_tower' in initial_data_aac_host.get('parameter').keys():
                            update_aac_host["parameter"]["isolated_tower"] = isolated_tower
                        if 'remarks' in initial_data_aac_host.get('parameter').keys():
                            update_aac_host["parameter"]["remarks"] = remarks

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
                                                     "isolated_tower": isolated_tower,
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

                item_number = update_iia["parameter"]["item_number"]
                result = objmenu_iia.exec_maintenance(update_iia, item_number, 'Update', False, False, True, True)

                if result[0] is not True:
                    raise AppException(result[1], [result[2]], [result[2]])

    return ''
