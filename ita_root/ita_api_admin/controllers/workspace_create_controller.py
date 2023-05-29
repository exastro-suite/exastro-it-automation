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
controller
workspace_create
"""
# import connexion
from flask import g
import os
import re
import json
import shutil
import time
from pathlib import Path

from common_libs.api import api_filter_admin, check_request_body_key
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.util import ky_encrypt, get_timestamp, create_dirs, put_uploadfiles
from libs.admin_common import initial_settings_ansible
from common_libs.common.exception import AppException
from common_libs.api import app_exception_response, exception_response


@api_filter_admin
def workspace_create(organization_id, workspace_id, body=None):  # noqa: E501
    """workspace_create

    Workspaceを作成する # noqa: E501

    :param organization_id: organizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse200
    """
    g.ORGANIZATION_ID = organization_id
    # set log environ format
    g.applogger.set_env_message()

    role_id = check_request_body_key(body, 'role_id')

    org_db = DBConnectOrg(organization_id)  # noqa: F405
    connect_info = org_db.get_wsdb_connect_info(workspace_id)
    if connect_info:
        return '', "ALREADY EXISTS", "499-00001", 499

    inistial_data_ansible_if = org_db.get_inistial_data_ansible_if()
    no_install_driver_tmp = org_db.get_no_install_driver()
    if no_install_driver_tmp is None or len(no_install_driver_tmp) == 0:
        no_install_driver = []
    else:
        no_install_driver = json.loads(no_install_driver_tmp)

    # make storage directory for workspace
    strage_path = os.environ.get('STORAGEPATH')
    workspace_dir = strage_path + "/".join([organization_id, workspace_id]) + "/"
    if not os.path.isdir(workspace_dir):
        os.makedirs(workspace_dir)
        g.applogger.debug("made workspace_dir")
    else:
        return '', "ALREADY EXISTS", "499-00001", 499

    try:
        # make storage directory for workspace job
        create_dir_list = os.path.join(os.environ.get('PYTHONPATH'), "config", "create_dir_list.txt")
        create_dirs(create_dir_list, workspace_dir)
        g.applogger.debug("make storage directory for workspace job")

        # set initial material
        src_dir = os.path.join(os.environ.get('PYTHONPATH'), "files")
        dest_dir = os.path.join(workspace_dir, "uploadfiles")
        config_file_path = os.path.join(src_dir, "config.json")
        put_uploadfiles(config_file_path, src_dir, dest_dir)
        g.applogger.debug("set initial material")

        # make workspace-db connect infomation
        ws_db_name, username, user_password = org_db.userinfo_generate("ITA_WS")
        connect_info = org_db.get_connect_info()

        data = {
            'WORKSPACE_ID': workspace_id,
            'DB_HOST': connect_info['DB_HOST'],
            'DB_PORT': int(connect_info['DB_PORT']),
            'DB_USER': username,
            'DB_PASSWORD': ky_encrypt(user_password),
            'DB_DATABASE': ws_db_name,
            'DISUSE_FLAG': 0,
            'LAST_UPDATE_USER': g.get('USER_ID')
        }

        org_root_db = DBConnectOrgRoot(organization_id)  # noqa: F405
        # create workspace-databse
        org_root_db.database_create(ws_db_name)
        # create workspace-user and grant user privileges
        org_root_db.user_create(username, user_password, ws_db_name)
        # print(username, user_password)
        g.applogger.debug("created db and db-user")

        # connect workspace-db
        g.db_connect_info = {}
        g.db_connect_info["WSDB_HOST"] = data["DB_HOST"]
        g.db_connect_info["WSDB_PORT"] = str(data["DB_PORT"])
        g.db_connect_info["WSDB_USER"] = data["DB_USER"]
        g.db_connect_info["WSDB_PASSWORD"] = data["DB_PASSWORD"]
        g.db_connect_info["WSDB_DATABASE"] = data["DB_DATABASE"]
        ws_db = DBConnectWs(workspace_id, organization_id)  # noqa: F405

        sql_list = [
            ['workspace.sql', 'workspace_master.sql'],
            ['menu_create.sql', 'menu_create_master.sql'],
            ['conductor.sql', 'conductor_master.sql'],
            ['ansible.sql', 'ansible_master.sql'],
            ['export_import.sql', 'export_import_master.sql'],
            ['compare.sql', 'compare_master.sql'],
            ['terraform_common.sql', 'terraform_common_master.sql'],
            ['terraform_cloud_ep.sql', 'terraform_cloud_ep_master.sql'],
            ['terraform_cli.sql', 'terraform_cli_master.sql'],
            ['hostgroup.sql', 'hostgroup_master.sql'],
            ['cicd.sql', 'cicd_master.sql'],
        ]
        last_update_timestamp = str(get_timestamp())

        for sql_files in sql_list:

            ddl_file = os.environ.get('PYTHONPATH') + "sql/" + sql_files[0]
            dml_file = os.environ.get('PYTHONPATH') + "sql/" + sql_files[1]

            # インストールしないドライバに指定されているSQLは実行しない
            if (sql_files[0] == 'terraform_common.sql' and 'terraform_cloud_ep' in no_install_driver and 'terraform_cli' in no_install_driver) or \
                    (sql_files[0] == 'terraform_cloud_ep.sql' and 'terraform_cloud_ep' in no_install_driver) or \
                    (sql_files[0] == 'terraform_cli.sql' and 'terraform_cli' in no_install_driver) or \
                    (sql_files[0] == 'cicd.sql' and 'ci_cd' in no_install_driver):
                continue

            # create table of workspace-db
            ws_db.sqlfile_execute(ddl_file)
            g.applogger.debug("executed " + ddl_file)

            # insert initial data of workspace-db
            ws_db.db_transaction_start()
            with open(dml_file, "r") as f:
                sql_list = f.read().split(";\n")
                for sql in sql_list:
                    if re.fullmatch(r'[\s\n\r]*', sql):
                        continue

                    sql = sql.replace("_____DATE_____", "STR_TO_DATE('" + last_update_timestamp + "','%Y-%m-%d %H:%i:%s.%f')")

                    prepared_list = []
                    trg_count = sql.count('__ROLE_ID__')
                    if trg_count > 0:
                        prepared_list = list(map(lambda a: role_id, range(trg_count)))
                        sql = ws_db.prepared_val_escape(sql).replace('\'__ROLE_ID__\'', '%s')
                        # print(sql)
                        # print(prepared_list)

                    ws_db.sql_execute(sql, prepared_list)
            g.applogger.debug("executed " + dml_file)
            ws_db.db_commit()

        # 初期データ設定(ansible)
        if (inistial_data_ansible_if is not None) and (len(inistial_data_ansible_if) != 0):
            ws_db.db_transaction_start()
            g.WORKSPACE_ID = workspace_id
            initial_settings_ansible(ws_db, json.loads(inistial_data_ansible_if))
            ws_db.db_commit()

        # 同時実行数制御用のVIEW作成
        ws_db.db_transaction_start()
        view_sql = "CREATE VIEW V_ANSL_EXEC_STS_INST2 AS "
        view_sql += "SELECT %s as ORGANIZATION_ID, %s as WORKSPACE_ID, %s as WORKSPACE_DB, 'V_ANSL_EXEC_STS_INST2' AS VIEW_NAME, EXECUTE_HOST_NAME, "
        view_sql += "'Legacy' as DRIVER_NAME, 'L' as DRIVER_ID, EXECUTION_NO, STATUS_ID, TIME_BOOK, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, TIME_REGISTER "
        view_sql += "FROM T_ANSL_EXEC_STS_INST "
        view_sql += "WHERE DISUSE_FLAG = %s "
        ws_db.sql_execute(view_sql, [organization_id, workspace_id, ws_db_name, 0])
        view_sql = "CREATE VIEW V_ANSP_EXEC_STS_INST2 AS "
        view_sql += "SELECT %s as ORGANIZATION_ID, %s as WORKSPACE_ID, %s as WORKSPACE_DB, 'V_ANSP_EXEC_STS_INST2' AS VIEW_NAME, EXECUTE_HOST_NAME, "
        view_sql += "'Pioneer' as DRIVER_NAME, 'P' as DRIVER_ID, EXECUTION_NO, STATUS_ID, TIME_BOOK, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, TIME_REGISTER "
        view_sql += "FROM T_ANSP_EXEC_STS_INST "
        view_sql += "WHERE DISUSE_FLAG = %s "
        ws_db.sql_execute(view_sql, [organization_id, workspace_id, ws_db_name, 0])
        view_sql = "CREATE VIEW V_ANSR_EXEC_STS_INST2 AS "
        view_sql += "SELECT %s as ORGANIZATION_ID, %s as WORKSPACE_ID, %s as WORKSPACE_DB, 'V_ANSR_EXEC_STS_INST2' AS VIEW_NAME, EXECUTE_HOST_NAME, "
        view_sql += "'Legacy-Role' as DRIVER_NAME, 'R' as DRIVER_ID, EXECUTION_NO, STATUS_ID, TIME_BOOK, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, TIME_REGISTER "
        view_sql += "FROM T_ANSR_EXEC_STS_INST "
        view_sql += "WHERE DISUSE_FLAG = %s "
        ws_db.sql_execute(view_sql, [organization_id, workspace_id, ws_db_name, 0])
        ws_db.db_commit()

        # 権限付与
        view_sql = "GRANT SELECT ,UPDATE ON TABLE `{ws_db_name}`.`V_ANSL_EXEC_STS_INST2` TO '{db_user}'@'%'".format(ws_db_name=ws_db_name, db_user=os.getenv("DB_USER"))
        org_root_db.sql_execute(view_sql, [])
        view_sql = "GRANT SELECT ,UPDATE ON TABLE `{ws_db_name}`.`V_ANSP_EXEC_STS_INST2` TO '{db_user}'@'%'".format(ws_db_name=ws_db_name, db_user=os.getenv("DB_USER"))
        org_root_db.sql_execute(view_sql, [])
        view_sql = "GRANT SELECT ,UPDATE ON TABLE `{ws_db_name}`.`V_ANSR_EXEC_STS_INST2` TO '{db_user}'@'%'".format(ws_db_name=ws_db_name, db_user=os.getenv("DB_USER"))
        org_root_db.sql_execute(view_sql, [])

        # register workspace-db connect infomation
        org_db.db_transaction_start()
        org_db.table_insert("T_COMN_WORKSPACE_DB_INFO", data, "PRIMARY_KEY")
        org_db.db_commit()
    except Exception as e:
        shutil.rmtree(workspace_dir)
        if 'ws_db' in locals():
            ws_db.db_rollback()
        org_db.db_rollback()

        if 'org_root_db' in locals():
            org_root_db.database_drop(ws_db_name)
            org_root_db.user_drop(username)

        raise Exception(e)

    return '',


@api_filter_admin
def workspace_delete(organization_id, workspace_id):  # noqa: E501
    """workspace_delete

    Workspaceを削除する # noqa: E501

    :param organization_id: organizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse200
    """
    exception_flg = False
    # get organization_id
    g.ORGANIZATION_ID = organization_id
    # set log environ format
    g.applogger.set_env_message()

    org_db = DBConnectOrg(organization_id)  # noqa: F405
    connect_info = org_db.get_wsdb_connect_info(workspace_id)
    if connect_info is False:
        return '', "ALREADY DELETED", "499-00002", 499

    # OrganizationとWorkspaceが削除されている場合のエラーログ抑止する為、廃止してからデータベース削除
    data = {
        'PRIMARY_KEY': connect_info['PRIMARY_KEY'],
        'DISUSE_FLAG': 1
    }
    org_db.db_transaction_start()
    org_db.table_update("T_COMN_WORKSPACE_DB_INFO", data, "PRIMARY_KEY")
    org_db.db_commit()

    try:
        strage_path = os.environ.get('STORAGEPATH')
        workspace_dir = strage_path + "/".join([organization_id, workspace_id]) + "/"

        # サービススキップファイルを配置する
        f = Path(workspace_dir + '/skip_all_service_for_ws_del')
        f.touch()
        time.sleep(3)

        # delete storage directory for workspace
        if os.path.isdir(workspace_dir):
            shutil.rmtree(workspace_dir)

        # drop ws-db and ws-db-user
        org_root_db = DBConnectOrgRoot(organization_id)
        org_root_db.database_drop(connect_info['DB_DATABASE'])
        org_root_db.user_drop(connect_info['DB_USER'])
        org_root_db.db_disconnect()

    except AppException as e:
        # スキップファイルが存在する場合は削除する
        if os.path.exists(workspace_dir + '/skip_all_service_for_ws_del'):
            os.remove(workspace_dir + '/skip_all_service_for_ws_del')
        # 廃止されているとapp_exceptionはログを抑止するので、ここでログだけ出力
        exception_flg = True
        exception_log_need = True
        result_list = app_exception_response(e, exception_log_need)

    except Exception as e:
        # スキップファイルが存在する場合は削除する
        if os.path.exists(workspace_dir + '/skip_all_service_for_ws_del'):
            os.remove(workspace_dir + '/skip_all_service_for_ws_del')
        # 廃止されているとexceptionはログを抑止するので、ここでログだけ出力
        exception_flg = True
        exception_log_need = True
        result_list = exception_response(e, exception_log_need)

    finally:
        if exception_flg is True:
            # 廃止を復活
            data = {
                'PRIMARY_KEY': connect_info['PRIMARY_KEY'],
                'DISUSE_FLAG': 0
            }
            org_db.db_transaction_start()
            org_db.table_update("T_COMN_WORKSPACE_DB_INFO", data, "PRIMARY_KEY")
            org_db.db_commit()

            return '', result_list[0]['message'], result_list[0]['result'], result_list[1]

    return '',
