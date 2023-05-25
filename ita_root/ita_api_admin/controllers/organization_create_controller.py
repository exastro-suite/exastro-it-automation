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
"""
controller
organization_create
"""
# import connexion
from flask import g
import os
import shutil
import json

from common_libs.api import api_filter_admin
from common_libs.common.dbconnect import *
from common_libs.common.util import ky_encrypt
from common_libs.ansible_driver.classes.gitlab import GitLabAgent
from common_libs.common.exception import AppException
from common_libs.api import app_exception_response, exception_response


@api_filter_admin
def organization_create(body, organization_id):  # noqa: E501
    """organization_create

    Organizationを作成する # noqa: E501

    :param body:
    :type body: dict | bytes
    :param organization_id: OrganizationID
    :type organization_id: str

    :rtype: InlineResponse200
    """

    # Bodyのチェック
    driver_list = [
        'terraform_cloud_ep',
        'terraform_cli',
        'ci_cd'
    ]

    no_install_driver = None
    if body is not None and len(body) > 0:
        no_install_driver_flg = False
        for key, value in body.items():
            if key != "no_install_driver":
                return '', "Body is invalid.", "499-00003", 499

            no_install_driver_flg = True
            for driver in value:
                if driver not in driver_list:
                    return '', "Value of key[no_install_driver] is invalid.", "499-00004", 499

        if no_install_driver_flg is False:
            return '', "Body is invalid.", "499-00003", 499
        no_install_driver = json.dumps(body['no_install_driver'])

    common_db = DBConnectCommon()  # noqa: F405
    connect_info = common_db.get_orgdb_connect_info(organization_id)
    if connect_info:
        return '', "ALREADY EXISTS", "499-00001", 499

    # make storage directory for organization
    strage_path = os.environ.get('STORAGEPATH')
    organization_dir = strage_path + organization_id + "/"
    if not os.path.isdir(organization_dir):
        os.makedirs(organization_dir)
        g.applogger.debug("made organization_dir")
    else:
        return '', "ALREADY EXISTS", "499-00001", 499

    try:
        # make organization-db connect infomation
        org_db_name, username, user_password = common_db.userinfo_generate("ITA_ORG")

        data = {
            'ORGANIZATION_ID': organization_id,
            'DB_HOST': os.environ.get('DB_HOST'),
            'DB_PORT': int(os.environ.get('DB_PORT')),
            'DB_USER': username,
            'DB_PASSWORD': ky_encrypt(user_password),
            'DB_DATABASE': org_db_name,
            'DB_ADMIN_USER': os.environ.get('DB_ADMIN_USER'),
            'DB_ADMIN_PASSWORD': ky_encrypt(os.environ.get('DB_ADMIN_PASSWORD')),
            'DISUSE_FLAG': 0,
            'LAST_UPDATE_USER': g.get('USER_ID')
        }
        if no_install_driver is not None:
            data['NO_INSTALL_DRIVER'] = no_install_driver

        g.db_connect_info = {}
        g.db_connect_info["ORGDB_HOST"] = data['DB_HOST']
        g.db_connect_info["ORGDB_PORT"] = str(data['DB_PORT'])
        g.db_connect_info["ORGDB_USER"] = data['DB_USER']
        g.db_connect_info["ORGDB_PASSWORD"] = data['DB_PASSWORD']
        g.db_connect_info["ORGDB_ADMIN_USER"] = data['DB_ADMIN_USER']
        g.db_connect_info["ORGDB_ADMIN_PASSWORD"] = data['DB_ADMIN_PASSWORD']
        g.db_connect_info["ORGDB_DATABASE"] = data['DB_DATABASE']
        org_root_db = DBConnectOrgRoot(organization_id)  # noqa: F405
        # create workspace-databse
        org_root_db.database_create(org_db_name)
        # create workspace-user and grant user privileges
        org_root_db.user_create(username, user_password, org_db_name)
        g.applogger.debug("created db and db-user")

        # connect organization-db
        org_db = DBConnectOrg(organization_id)  # noqa: F405
        # create table of organization-db
        org_db.sqlfile_execute("sql/organization.sql")
        g.applogger.debug("executed sql/organization.sql")

        # make gitlab user and token value
        if (os.environ.get('GITLAB_HOST') is not None) and (len(os.environ.get('GITLAB_HOST')) > 0):
            gitlab_agent = GitLabAgent()
            res = gitlab_agent.create_user(org_db_name)
            g.applogger.debug("GitLab create_user : {}".format(res))
            data["GITLAB_USER"] = res['username']
            data["GITLAB_TOKEN"] = gitlab_agent.create_personal_access_tokens(res['id'], res['username'])

        # register organization-db connect infomation and gitlab connect infomation
        common_db.db_transaction_start()
        common_db.table_insert("T_COMN_ORGANIZATION_DB_INFO", data, "PRIMARY_KEY")
        common_db.db_commit()
    except Exception as e:
        shutil.rmtree(organization_dir)
        common_db.db_rollback()

        if 'org_root_db' in locals():
            org_root_db.database_drop(org_db_name)
            org_root_db.user_drop(username)

        if 'gitlab_agent' in locals():
            user_list = gitlab_agent.get_user_by_username(org_db_name)
            for user in user_list:
                gitlab_agent.delete_user(user['id'])

        raise Exception(e)

    return '',


@api_filter_admin
def organization_delete(organization_id):  # noqa: E501
    """organization_delete

    Organizationを削除する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str

    :rtype: InlineResponse200
    """
    exception_flg = False

    # ITA_DB connect
    common_db = DBConnectCommon()  # noqa: F405
    connect_info = common_db.get_orgdb_connect_info(organization_id)
    if connect_info is False:
        return '', "ALREADY DELETED", "499-00002", 499

    g.db_connect_info = {}
    g.db_connect_info["ORGDB_HOST"] = connect_info["DB_HOST"]
    g.db_connect_info["ORGDB_PORT"] = str(connect_info["DB_PORT"])
    g.db_connect_info["ORGDB_USER"] = connect_info["DB_USER"]
    g.db_connect_info["ORGDB_PASSWORD"] = connect_info["DB_PASSWORD"]
    g.db_connect_info["ORGDB_ADMIN_USER"] = connect_info['DB_ADMIN_USER']
    g.db_connect_info["ORGDB_ADMIN_PASSWORD"] = connect_info['DB_ADMIN_PASSWORD']
    g.db_connect_info["ORGDB_DATABASE"] = connect_info["DB_DATABASE"]

    # get ws-db connect infomation
    org_db = DBConnectOrg(organization_id)

    # get workspace info
    workspace_data_list = []
    workspace_data_list = org_db.table_select("T_COMN_WORKSPACE_DB_INFO", "WHERE `DISUSE_FLAG`=0")

    # org-db root user connect
    org_root_db = DBConnectOrgRoot(organization_id)

    try:
        # OrganizationとWorkspaceが削除されている場合のエラーログ抑止する為、廃止してからデータベース削除
        org_db.db_transaction_start()
        for workspace_data in workspace_data_list:
            db_disuse_set(org_db, workspace_data['PRIMARY_KEY'], 'T_COMN_WORKSPACE_DB_INFO', 1)
        org_db.db_commit()

        common_db.db_transaction_start()
        db_disuse_set(common_db, connect_info['PRIMARY_KEY'], 'T_COMN_ORGANIZATION_DB_INFO', 1)
        common_db.db_commit()

        # delete gitlab user and projects
        if (os.environ.get('GITLAB_HOST') is not None) and (len(os.environ.get('GITLAB_HOST')) > 0):
            gitlab_agent = GitLabAgent()
            user_list = gitlab_agent.get_user_by_username(connect_info['GITLAB_USER'])
            for user in user_list:
                gitlab_user_id = user['id']
                projects = gitlab_agent.get_all_project_by_user_id(gitlab_user_id)
                for project in projects:
                    gitlab_agent.delete_project(project['id'])
                gitlab_agent.delete_user(gitlab_user_id)

        # delete storage directory for organization
        strage_path = os.environ.get('STORAGEPATH')
        organization_dir = strage_path + organization_id + "/"
        if os.path.isdir(organization_dir):
            shutil.rmtree(organization_dir)

        for workspace_data in workspace_data_list:
            # drop ws-db and ws-db-user
            org_root_db.database_drop(workspace_data['DB_DATABASE'])
            org_root_db.user_drop(workspace_data['DB_USER'])

        # drop org-db and org-db-user
        org_root_db.database_drop(connect_info['DB_DATABASE'])
        org_root_db.user_drop(connect_info['DB_USER'])

    except AppException as e:
        # 廃止されているとapp_exceptionはログを抑止するので、ここでログだけ出力
        exception_flg = True
        exception_log_need = True
        result_list = app_exception_response(e, exception_log_need)

    except Exception as e:
        # 廃止されているとexceptionはログを抑止するので、ここでログだけ出力
        exception_flg = True
        exception_log_need = True
        result_list = exception_response(e, exception_log_need)

    finally:
        if exception_flg is True:
            # 廃止を復活
            org_db.db_transaction_start()
            for workspace_data in workspace_data_list:
                db_disuse_set(org_db, workspace_data['PRIMARY_KEY'], 'T_COMN_WORKSPACE_DB_INFO', 0)
            org_db.db_commit()

            common_db.db_transaction_start()
            db_disuse_set(common_db, connect_info['PRIMARY_KEY'], 'T_COMN_ORGANIZATION_DB_INFO', 0)
            common_db.db_commit()

            common_db.db_disconnect()
            org_db.db_disconnect()
            org_root_db.db_disconnect()

            return '', result_list[0]['message'], result_list[0]['result'], result_list[1]
    return '',


def db_disuse_set(db_obj, pkey, table, disuse_flg):
    # disuse org-db connect infomation
    data = {
        'PRIMARY_KEY': pkey,
        'DISUSE_FLAG': disuse_flg
    }
    db_obj.table_update(table, data, "PRIMARY_KEY")
