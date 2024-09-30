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
from pymongo import ASCENDING
import traceback

from common_libs.api import api_filter_admin, check_request_body_key
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectOrg, MONGOConnectWs
from common_libs.common.mongoconnect.const import Const as mongoConst
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.util import ky_decrypt, ky_encrypt, get_timestamp, create_dirs, put_uploadfiles, arrange_stacktrace_format
from libs.admin_common import initial_settings_ansible
from common_libs.common.exception import AppException


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
    ws_connect_info = org_db.get_wsdb_connect_info(workspace_id)
    if ws_connect_info:
        org_db.db_disconnect()
        # Already exists.(target{}: {})
        return '', g.appmsg.get_api_message("490-02008", ["workspace_id", workspace_id]), "490-02008", 490

    inistial_data_ansible_if = org_db.get_inistial_data_ansible_if()
    # get no install driver list
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
        g.applogger.info("made workspace_dir")
    else:
        org_db.db_disconnect()
        # Already exists.(target{}: {})
        return '', g.appmsg.get_api_message("490-02008", ["workspace_dir", workspace_dir]), "490-02008", 490

    try:
        # make workspace-db connect infomation
        ws_db_name, db_username, db_user_password = org_db.userinfo_generate("ITA_WS")

        orgdb_connect_info = org_db.get_connect_info()

        org_root_db = DBConnectOrgRoot(organization_id)  # noqa: F405
        # create workspace-databse
        org_root_db.database_create(ws_db_name)
        # create workspace-user and grant user privileges
        org_root_db.user_create(db_username, db_user_password, ws_db_name)
        # print(db_username, db_user_password)
        g.applogger.info("created db and db-user")

        # OrganizationにてOASEがインストールされている場合のMongo接続情報
        mongo_host = None
        mongo_connection_string = None
        ws_mongo_name = None
        ws_mongo_user = None
        ws_mongo_password = None
        if 'oase' not in no_install_driver:
            mongo_host = mongo_host = os.environ.get('MONGO_HOST', '')
            mongo_owner = bool(orgdb_connect_info['MONGO_OWNER'])
            mongo_connection_string = ky_decrypt(orgdb_connect_info['MONGO_CONNECTION_STRING'])
            if not mongo_host and not mongo_connection_string:
                # OASEが有効かつ、環境変数「MONGO_HOST」と「MONGO_CONNECTION_STRING」両方に値が無い場合は、workspace作成をできないようにする。
                org_db.db_disconnect()
                org_root_db.db_disconnect()
                # The OASE driver cannot be added because the MongoDB host is not set in the environment variables.
                return '', g.appmsg.get_api_message("490-02015", []), "490-02015", 490

            # make workspace-mongo connect infomation
            org_mongo = MONGOConnectOrg(org_db)
            ws_mongo_name, ws_mongo_user, ws_mongo_password = org_mongo.userinfo_generate("ITA_WS")
            g.applogger.info("mongo-db-name is decided")

            # pattern1 pattern3
            if mongo_owner is True:
                try:
                    # create workspace-mongodb-user
                    org_mongo.create_user(
                        ws_mongo_user,
                        ws_mongo_password,
                        ws_mongo_name
                    )
                    g.applogger.info("created mongo-db-user")
                except Exception as e:
                    t = traceback.format_exc()
                    g.applogger.error(arrange_stacktrace_format(t))
                    raise AppException("490-00002", [e], [])
            # pattern2
            else:
                ws_mongo_user = None
                ws_mongo_password = None

        data = {
            'WORKSPACE_ID': workspace_id,
            'DB_HOST': orgdb_connect_info['DB_HOST'],
            'DB_PORT': int(orgdb_connect_info['DB_PORT']),
            'DB_USER': db_username,
            'DB_PASSWORD': ky_encrypt(db_user_password),
            'DB_DATABASE': ws_db_name,
            'MONGO_CONNECTION_STRING': ky_encrypt(mongo_connection_string),
            'MONGO_DATABASE': ws_mongo_name,
            'MONGO_USER': ws_mongo_user,
            'MONGO_PASSWORD': ky_encrypt(ws_mongo_password),
            'NO_INSTALL_DRIVER': no_install_driver_tmp,
            'DISUSE_FLAG': 0,
            'LAST_UPDATE_USER': g.get('USER_ID')
        }

        # connect workspace-db
        g.db_connect_info = {}
        g.db_connect_info["ORGDB_HOST"] = orgdb_connect_info['DB_HOST']
        g.db_connect_info["ORGDB_PORT"] = orgdb_connect_info['DB_PORT']
        g.db_connect_info["ORGDB_USER"] = orgdb_connect_info['DB_USER']
        g.db_connect_info["ORGDB_PASSWORD"] = orgdb_connect_info['DB_PASSWORD']
        g.db_connect_info["ORGDB_ADMIN_USER"] = orgdb_connect_info['DB_ADMIN_USER']
        g.db_connect_info["ORGDB_ADMIN_PASSWORD"] = orgdb_connect_info['DB_ADMIN_PASSWORD']
        g.db_connect_info["ORGDB_DATABASE"] = orgdb_connect_info['DB_DATABASE']
        g.db_connect_info["ORG_MONGO_OWNER"] = orgdb_connect_info['MONGO_OWNER']
        g.db_connect_info["ORG_MONGO_CONNECTION_STRING"] = orgdb_connect_info['MONGO_CONNECTION_STRING']
        g.db_connect_info["ORG_MONGO_ADMIN_USER"] = orgdb_connect_info['MONGO_ADMIN_USER']
        g.db_connect_info["ORG_MONGO_ADMIN_PASSWORD"] = orgdb_connect_info['MONGO_ADMIN_PASSWORD']
        g.db_connect_info["NO_INSTALL_DRIVER"] = no_install_driver_tmp

        g.db_connect_info["WSDB_HOST"] = data["DB_HOST"]
        g.db_connect_info["WSDB_PORT"] = str(data["DB_PORT"])
        g.db_connect_info["WSDB_USER"] = data["DB_USER"]
        g.db_connect_info["WSDB_PASSWORD"] = data["DB_PASSWORD"]
        g.db_connect_info["WSDB_DATABASE"] = data["DB_DATABASE"]
        g.db_connect_info["WS_MONGO_CONNECTION_STRING"] = data['MONGO_CONNECTION_STRING']
        g.db_connect_info["WS_MONGO_DATABASE"] = data['MONGO_DATABASE']
        g.db_connect_info["WS_MONGO_USER"] = data['MONGO_USER']
        g.db_connect_info["WS_MONGO_PASSWORD"] = data['MONGO_PASSWORD']

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
            ['oase.sql', 'oase_master.sql'],
        ]
        last_update_timestamp = str(get_timestamp())

        for sql_files in sql_list:
            ddl_file = os.environ.get('PYTHONPATH') + "sql/" + sql_files[0]
            dml_file = os.environ.get('PYTHONPATH') + "sql/" + sql_files[1]

            # インストールしないドライバに指定されているSQLは実行しない
            if (sql_files[0] == 'terraform_common.sql' and 'terraform_cloud_ep' in no_install_driver and 'terraform_cli' in no_install_driver) or \
                    (sql_files[0] == 'terraform_cloud_ep.sql' and 'terraform_cloud_ep' in no_install_driver) or \
                    (sql_files[0] == 'terraform_cli.sql' and 'terraform_cli' in no_install_driver) or \
                    (sql_files[0] == 'cicd.sql' and 'ci_cd' in no_install_driver) or \
                    (sql_files[0] == 'oase.sql' and 'oase' in no_install_driver):
                continue

            # create table of workspace-db
            g.applogger.info("execute " + ddl_file)
            ws_db.sqlfile_execute(ddl_file)

            # insert initial data of workspace-db
            ws_db.db_transaction_start()
            # #2079 /storage配下ではないので対象外
            g.applogger.info("execute " + dml_file)
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
            ws_db.db_commit()

        # make storage directory for workspace job
        create_dir_list = os.path.join(os.environ.get('PYTHONPATH'), "config", "create_dir_list.txt")
        create_dirs(create_dir_list, workspace_dir)
        g.applogger.info("make storage directory for workspace job")

        # set initial material files
        src_dir = os.path.join(os.environ.get('PYTHONPATH'), "files")
        g.applogger.info(f"[Trace] src_dir={src_dir}")
        if os.path.isdir(src_dir):
            config_file_list = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
            g.applogger.info(f"[Trace] config_file_list={config_file_list}")

            for config_file_name in config_file_list:
                if config_file_name != "config.json":
                    # 対象のconfigファイルがインストール必要なドライバのものか判断
                    driver_name = config_file_name.replace('_config.json', '')
                    if driver_name in no_install_driver:
                        g.applogger.info(f"[Trace] SKIP CONFIG FILE NAME=[{config_file_name}] BECAUSE {driver_name} IS NOT INSTALLED.")
                        continue

                dest_dir = os.path.join(workspace_dir, "uploadfiles")
                config_file_path = os.path.join(src_dir, config_file_name)
                g.applogger.info(f"[Trace] dest_dir={dest_dir}")
                g.applogger.info(f"[Trace] config_file_path={config_file_path}")
                put_uploadfiles(config_file_path, src_dir, dest_dir)
        g.applogger.info("set initial material files")

        # 初期データ設定(ansible)
        if (inistial_data_ansible_if is not None) and (len(inistial_data_ansible_if) != 0):
            ws_db.db_transaction_start()
            g.WORKSPACE_ID = workspace_id
            initial_settings_ansible(ws_db, json.loads(inistial_data_ansible_if))
            ws_db.db_commit()
            g.applogger.info("def'initial_settings_ansible' is executed")

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
        g.applogger.info("sql of ansible-execute is executed")

        # 権限付与
        view_sql = "GRANT SELECT ,UPDATE ON TABLE `{ws_db_name}`.`V_ANSL_EXEC_STS_INST2` TO '{db_user}'@'%'".format(ws_db_name=ws_db_name, db_user=os.getenv("DB_USER"))
        org_root_db.sql_execute(view_sql, [])
        view_sql = "GRANT SELECT ,UPDATE ON TABLE `{ws_db_name}`.`V_ANSP_EXEC_STS_INST2` TO '{db_user}'@'%'".format(ws_db_name=ws_db_name, db_user=os.getenv("DB_USER"))
        org_root_db.sql_execute(view_sql, [])
        view_sql = "GRANT SELECT ,UPDATE ON TABLE `{ws_db_name}`.`V_ANSR_EXEC_STS_INST2` TO '{db_user}'@'%'".format(ws_db_name=ws_db_name, db_user=os.getenv("DB_USER"))
        org_root_db.sql_execute(view_sql, [])
        g.applogger.info("view of ansible-execute is granted")

        # register workspace-db connect infomation
        org_db.db_transaction_start()
        org_db.table_insert("T_COMN_WORKSPACE_DB_INFO", data, "PRIMARY_KEY")
        org_db.db_commit()
        g.applogger.info("The data of workspace infomation is made")

        if 'oase' not in no_install_driver:
        # OASEのmongo設定（インデックスなど）
            ws_mongo = MONGOConnectWs()
            try:
                # db.labeled_event_collection.createIndex({"labels._exastro_fetched_time":1,"labels._exastro_end_time":1,"_id":1}, {"name": "default_sort"})
                ws_mongo.collection(mongoConst.LABELED_EVENT_COLLECTION).create_index([("labels._exastro_fetched_time", ASCENDING), ("labels._exastro_end_time", ASCENDING), ("_id", ASCENDING)], name="default_sort")
                # # イベントデータの保持期限 90日
                # ws_mongo.collection(mongoConst.LABELED_EVENT_COLLECTION).create_index([("exastro_created_at", ASCENDING)], expireAfterSeconds=7776000)
                g.applogger.info("Index of mongo is made")
            except Exception as e:
                t = traceback.format_exc()
                g.applogger.error(arrange_stacktrace_format(t))
                raise AppException("490-01002", [e], [e])

    except Exception as e:
        shutil.rmtree(workspace_dir)
        if 'ws_db' in locals():
            ws_db.db_rollback()
        org_db.db_rollback()

        if 'org_root_db' in locals():
            org_root_db.database_drop(ws_db_name)
            org_root_db.user_drop(db_username)

        if 'oase' not in no_install_driver and 'org_mongo' in locals():
            org_mongo = MONGOConnectOrg(org_db)
            org_mongo.drop_database(ws_mongo_name)
            if mongo_owner is True:
                org_mongo.drop_user(ws_mongo_user, ws_mongo_name)

        raise e
    finally:
        if 'org_root_db' in locals():
            org_root_db.db_disconnect()

        if 'org_db' in locals():
            org_db.db_disconnect()

        if 'ws_db' in locals():
            ws_db.db_disconnect()

        if 'org_mongo' in locals():
            org_mongo.disconnect()

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
        org_db.db_disconnect()
        # Already deleted.(target{}: {})
        return '', g.appmsg.get_api_message("490-02009", ["workspace_id", workspace_id]), "490-02009", 490

    # get no install driver list
    no_install_driver_tmp = org_db.get_no_install_driver()
    if no_install_driver_tmp is None or len(no_install_driver_tmp) == 0:
        no_install_driver = []
    else:
        no_install_driver = json.loads(no_install_driver_tmp)

    # organization connection infomation
    org_connect_info = org_db.get_connect_info()

    # OrganizationとWorkspaceが削除されている場合のエラーログ抑止する為、廃止してからデータベース削除
    data = {
        'PRIMARY_KEY': connect_info['PRIMARY_KEY'],
        'DISUSE_FLAG': 1
    }
    org_db.db_transaction_start()
    org_db.table_update("T_COMN_WORKSPACE_DB_INFO", data, "PRIMARY_KEY")
    org_db.db_commit()
    g.applogger.info("Workspace is disused")

    try:
        strage_path = os.environ.get('STORAGEPATH')
        workspace_dir = strage_path + "/".join([organization_id, workspace_id]) + "/"

        if os.path.isdir(workspace_dir):
            # サービススキップファイルを配置する
            # #2079 /storageにアクセスしているがファイルを作成しているだけなのでそのまま
            f = Path(workspace_dir + '/skip_all_service_for_ws_del')
            f.touch()
            time.sleep(3)

        # drop ws-db and ws-db-user
        org_root_db = DBConnectOrgRoot(organization_id)
        org_root_db.connection_kill(connect_info['DB_DATABASE'], connect_info['DB_USER'])
        org_root_db.database_drop(connect_info['DB_DATABASE'])
        org_root_db.user_drop(connect_info['DB_USER'])
        org_root_db.db_disconnect()
        g.applogger.info("Workspace DB and DB_USER is cleaned")

        if 'oase' not in no_install_driver and connect_info.get('MONGO_DATABASE'):
            org_mongo = MONGOConnectOrg(org_db)
            org_mongo.drop_database(connect_info['MONGO_DATABASE'])
            g.applogger.info("Workspace MongoDB is cleaned")
            if bool(org_connect_info['MONGO_OWNER']) is True:
                org_mongo.drop_user(connect_info['MONGO_USER'], connect_info['MONGO_DATABASE'])
                g.applogger.info("Workspace MongoDB_USER is cleaned")

        # delete storage directory for workspace
        while os.path.isdir(workspace_dir):
            try:
                shutil.rmtree(workspace_dir)
                break
            except FileNotFoundError:
                # 削除時にFileNotFoundErrorが出る場合があるので、その場合は再度削除を行う
                time.sleep(1)
                continue
        g.applogger.info("Storage is cleaned")

    except AppException as e:
        # スキップファイルが存在する場合は削除する
        if os.path.exists(workspace_dir + '/skip_all_service_for_ws_del'):
            os.remove(workspace_dir + '/skip_all_service_for_ws_del')

        exception_flg = True
        raise AppException(e)
    except Exception as e:
        # スキップファイルが存在する場合は削除する
        if os.path.exists(workspace_dir + '/skip_all_service_for_ws_del'):
            os.remove(workspace_dir + '/skip_all_service_for_ws_del')

        exception_flg = True
        raise e
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
            g.applogger.info("Workspace is reused")

        org_db.db_disconnect()

    return '',
