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

from common_libs.api import api_filter, check_request_body_key
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.util import ky_encrypt, get_timestamp


@api_filter
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
        return '', "ALREADY EXISTS"

    # make storage directory for workspace
    strage_path = os.environ.get('STORAGEPATH')
    workspace_dir = strage_path + "/".join([organization_id, workspace_id]) + "/"
    if not os.path.isdir(workspace_dir):
        os.makedirs(workspace_dir)
        g.applogger.debug("made workspace_dir")
    else:
        return '', "ALREADY EXISTS"

    try:
        # make storage directory for workspace job
        dir_list = [
            ['driver', 'ansible', 'legacy'],
            ['driver', 'ansible', 'pioneer'],
            ['driver', 'ansible', 'legacy_role'],
            ['driver', 'ansible', 'git_repositories'],
            ['driver', 'conductor'],
            ['driver', 'terraform'],
            ['uploadfiles'],
            ['tmp', 'driver', 'ansible'],
        ]
        for dir in dir_list:
            abs_dir = workspace_dir + "/".join(dir)
            if not os.path.isdir(abs_dir):
                os.makedirs(abs_dir)

        # set initial material
        with open('files/config.json', 'r') as material_conf_json:
            material_conf = json.load(material_conf_json)
            for menu_id, file_info_list in material_conf.items():
                for file_info in file_info_list:
                    for file, copy_cfg in file_info.items():
                        org_file = os.environ.get('PYTHONPATH') + "/".join(["files", menu_id, file])
                        old_file_path = workspace_dir + "uploadfiles/" + menu_id + copy_cfg[0]
                        file_path = workspace_dir + "uploadfiles/" + menu_id + copy_cfg[1]

                        if not os.path.isdir(old_file_path):
                            os.makedirs(old_file_path)

                        shutil.copy(org_file, old_file_path + file)
                        os.symlink(old_file_path + file, file_path + file)
        g.applogger.debug("set initial material")

        # make workspace-db connect infomation
        username, user_password = org_db.userinfo_generate("ITA_WS")
        ws_db_name = username
        connect_info = org_db.get_connect_info()

        data = {
            'WORKSPACE_ID': workspace_id,
            'DB_HOST': connect_info['DB_HOST'],
            'DB_PORT': int(connect_info['DB_PORT']),
            'DB_USER': username,
            'DB_PASSWORD': ky_encrypt(user_password),
            'DB_DATADBASE': ws_db_name,
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
        g.db_connect_info["WSDB_DATADBASE"] = data["DB_DATADBASE"]
        ws_db = DBConnectWs(workspace_id, organization_id)  # noqa: F405

        sql_list = [
            ['workspace.sql', 'workspace_master.sql'],
            ['menu_create.sql', 'menu_create_master.sql'],
            ['conductor.sql', 'conductor_master.sql'],
            ['ansible.sql', 'ansible_master.sql'],
        ]
        last_update_timestamp = str(get_timestamp())

        for sql_files in sql_list:

            ddl_file = "sql/" + sql_files[0]
            dml_file = "sql/" + sql_files[1]

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


@api_filter
def workspace_delete(organization_id, workspace_id):  # noqa: E501
    """workspace_delete

    Workspaceを削除する # noqa: E501

    :param organization_id: organizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str

    :rtype: InlineResponse200
    """
    # get organization_id
    g.ORGANIZATION_ID = organization_id
    # set log environ format
    g.applogger.set_env_message()

    org_db = DBConnectOrg(organization_id)  # noqa: F405
    connect_info = org_db.get_wsdb_connect_info(workspace_id)
    if connect_info is False:
        return '', "ALREADY DELETED"

    # delete storage directory for workspace
    strage_path = os.environ.get('STORAGEPATH')
    workspace_dir = strage_path + "/".join([organization_id, workspace_id]) + "/"
    if os.path.isdir(workspace_dir):
        shutil.rmtree(workspace_dir)
    else:
        return '', "ALREADY DELETED"

    # drop ws-db and ws-db-user
    org_root_db = DBConnectOrgRoot(organization_id)  # noqa: F405
    org_root_db.database_drop(connect_info['DB_DATADBASE'])
    org_root_db.user_drop(connect_info['DB_USER'])
    org_root_db.db_disconnect()

    # disuse ws-db connect infomation
    data = {
        'PRIMARY_KEY': connect_info['PRIMARY_KEY'],
        'DISUSE_FLAG': 1
    }
    org_db.db_transaction_start()
    org_db.table_update("T_COMN_WORKSPACE_DB_INFO", data, "PRIMARY_KEY")
    org_db.db_commit()

    return '',
