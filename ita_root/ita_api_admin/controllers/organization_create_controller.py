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
import re
from pymongo import ASCENDING
import traceback

from common_libs.api import api_filter_admin
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectOrg, MONGOConnectWs
from common_libs.common.mongoconnect.const import Const as mongoConst
from common_libs.common.util import ky_encrypt, ky_decrypt, get_timestamp, url_check, arrange_stacktrace_format, put_uploadfiles
from common_libs.ansible_driver.classes.gitlab import GitLabAgent
from common_libs.common.exception import AppException


@api_filter_admin
def organization_create(body, organization_id):
    """organization_create

    Organizationを作成する

    :param body:
    :type body: dict | bytes
    :param organization_id: OrganizationID
    :type organization_id: str

    :rtype: InlineResponse200
    """
    # Bodyのチェック用
    driver_list = [
        'terraform_cloud_ep',
        'terraform_cli',
        'ci_cd',
        'oase'
    ]

    # driversから適用するドライバを選定する。key(driver名)がない場合はTrueとする。
    additional_drivers = {
        "terraform_cloud_ep": True,
        "terraform_cli": True,
        "ci_cd": True,
        "oase": True
    }
    if body is not None and len(body) > 0:
        drivers = body.get('drivers')
        if drivers is not None:
            for driver_name, driver_bool in drivers.items():
                if driver_name not in driver_list:
                    # Value of key[{}] is invalid.
                    return '', g.appmsg.get_api_message("490-02005", ["drivers"]), "490-02005", 490

                if driver_bool is False:
                    additional_drivers[driver_name] = False

    # OASEが有効な場合
    is_exists_mongo_info = False
    if 'services' in body and 'document_store' in body['services']:
        is_exists_mongo_info = True
    mongo_host = None
    mongo_owner = None
    mongo_connection_string = None
    mongo_admin_user = None
    mongo_admin_password = None
    if additional_drivers["oase"] is True:
        if is_exists_mongo_info is False:
            # 必要な接続情報が足りない
            # Body paramater '{}' is required.
            return '', g.appmsg.get_api_message("490-02006", ["services.document_store"]), "490-02006", 490
        mongodb_info = body['services']['document_store']

        mongo_host = os.environ.get('MONGO_HOST', '')
        mongo_owner = mongodb_info.get('owner', True)
        mongo_connection_string = mongodb_info.get('connection_string', '')
        if mongo_connection_string:
            # 接続文字列の不正チェック
            url_check_bool, url_check_msg, message_num = mongo_url_check(mongo_connection_string)
            if url_check_bool is False:
                return "", url_check_msg, message_num, 490

        # pattern
        # 1. mongo_owner=True   mongo_connection_string=""    WS単位でユーザを作成し、ＤＢと紐づける。内部コンテナを利用。
        # 2. mongo_owner=False  mongo_connection_string="xxx"   ユーザは作成しない。外部のmongoを利用。
        # 3. mongo_owner=True   mongo_connection_string="xxx"   WS単位でユーザを作成し、ＤＢと紐づける。外部のmongoを利用。未実装
        if (mongo_owner is True and not mongo_host) or (mongo_owner is False and not mongo_connection_string):
            # どちらのpatternの接続情報もなく、OASEドライバを追加できない。
            # The OASE driver cannot be added because the connection infomation of mongo is not set.
            return '', g.appmsg.get_api_message("490-02007", []), "490-02007", 490

        # v2.4ではmongo_owner=Trueは、内部コンテナしか許さないので、pattern1に流す
        if mongo_owner is True:
            mongo_connection_string = ''

        if mongo_owner is True and not mongo_connection_string:
            # pattern1
            mongo_admin_user = os.environ.get("MONGO_ADMIN_USER")
            mongo_admin_password = os.environ.get("MONGO_ADMIN_PASSWORD")

    # make no install driver list
    no_install_driver = None
    no_install_driver_list = []
    for driver_name, driver_bool in additional_drivers.items():
        if driver_bool is False:
            no_install_driver_list.append(driver_name)

    if len(no_install_driver_list) > 0:
        no_install_driver = json.dumps(no_install_driver_list)

    common_db = DBConnectCommon()  # noqa: F405
    connect_info = common_db.get_orgdb_connect_info(organization_id)
    if connect_info:
        # Already exists.(target{}: {})
        return '', g.appmsg.get_api_message("490-02008", ["organization_id", organization_id]), "490-02008", 490

    # make storage directory for organization
    strage_path = os.environ.get('STORAGEPATH')
    organization_dir = strage_path + organization_id + "/"
    if not os.path.isdir(organization_dir):
        os.makedirs(organization_dir)
        g.applogger.info("made organization_dir")
    else:
        # Already exists.(target{}: {})
        return '', g.appmsg.get_api_message("490-02008", ["organization_dir", organization_dir]), "490-02008", 490

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
            'MONGO_OWNER': mongo_owner,
            'MONGO_CONNECTION_STRING': ky_encrypt(mongo_connection_string),
            'MONGO_ADMIN_USER': mongo_admin_user,
            'MONGO_ADMIN_PASSWORD': ky_encrypt(mongo_admin_password),
            'NO_INSTALL_DRIVER': no_install_driver,
            'DISUSE_FLAG': 0,
            'LAST_UPDATE_USER': g.get('USER_ID')
        }

        g.db_connect_info = {}
        g.db_connect_info["ORGDB_HOST"] = data['DB_HOST']
        g.db_connect_info["ORGDB_PORT"] = str(data['DB_PORT'])
        g.db_connect_info["ORGDB_USER"] = data['DB_USER']
        g.db_connect_info["ORGDB_PASSWORD"] = data['DB_PASSWORD']
        g.db_connect_info["ORGDB_ADMIN_USER"] = data['DB_ADMIN_USER']
        g.db_connect_info["ORGDB_ADMIN_PASSWORD"] = data['DB_ADMIN_PASSWORD']
        g.db_connect_info["ORGDB_DATABASE"] = data['DB_DATABASE']
        g.db_connect_info["ORG_MONGO_OWNER"] = data['MONGO_OWNER']
        g.db_connect_info["ORG_MONGO_CONNECTION_STRING"] = data['MONGO_CONNECTION_STRING']
        g.db_connect_info["ORG_MONGO_ADMIN_USER"] = data['MONGO_ADMIN_USER']
        g.db_connect_info["ORG_MONGO_ADMIN_PASSWORD"] = data['MONGO_ADMIN_PASSWORD']
        g.db_connect_info["NO_INSTALL_DRIVER"] = data['NO_INSTALL_DRIVER']

        # 試しにmongoクライアントでエラーが出ないかチェックする
        if additional_drivers["oase"] is True:
            org_mongo = MONGOConnectOrg()
            org_mongo.connect_check()

        org_root_db = DBConnectOrgRoot(organization_id)  # noqa: F405
        # create organization-databse
        org_root_db.database_create(org_db_name)
        # create organization-user and grant user privileges
        org_root_db.user_create(username, user_password, org_db_name)
        g.applogger.info("created db and db-user")

        # connect organization-db
        org_db = DBConnectOrg(organization_id)  # noqa: F405
        # create table of organization-db
        org_db.sqlfile_execute("sql/organization.sql")
        g.applogger.info("executed sql/organization.sql")


        # make gitlab user and token value
        if (os.environ.get('GITLAB_HOST') is not None) and (len(os.environ.get('GITLAB_HOST')) > 0):
            try:
                gitlab_agent = GitLabAgent()
                res = gitlab_agent.create_user(org_db_name)
            except Exception as e:
                t = traceback.format_exc()
                g.applogger.error("{}".format(arrange_stacktrace_format(t)))
                raise AppException("490-00001", [e], [])
            g.applogger.info("GitLab create_user")
            g.applogger.debug("GitLab response : {}".format(res))
            data["GITLAB_USER"] = res['username']
            data["GITLAB_TOKEN"] = gitlab_agent.create_personal_access_tokens(res['id'], res['username'])

        # register organization-db connect infomation and gitlab connect infomation
        common_db.db_transaction_start()
        common_db.table_insert("T_COMN_ORGANIZATION_DB_INFO", data, "PRIMARY_KEY")
        common_db.db_commit()
        g.applogger.info("organization is created")

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

        raise e
    finally:
        if 'common_db' in locals():
            common_db.db_disconnect()
        if 'org_root_db' in locals():
            org_root_db.db_disconnect()
        if 'org_db' in locals():
            org_db.db_disconnect()
        if 'org_mongo' in locals():
            org_mongo.disconnect()

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
        # Already deleted.(target{}: {})
        return '', g.appmsg.get_api_message("490-02009", ["organization_id", organization_id]), "490-02009", 490

    g.db_connect_info = {}
    g.db_connect_info["ORGDB_HOST"] = connect_info["DB_HOST"]
    g.db_connect_info["ORGDB_PORT"] = str(connect_info["DB_PORT"])
    g.db_connect_info["ORGDB_USER"] = connect_info["DB_USER"]
    g.db_connect_info["ORGDB_PASSWORD"] = connect_info["DB_PASSWORD"]
    g.db_connect_info["ORGDB_ADMIN_USER"] = connect_info['DB_ADMIN_USER']
    g.db_connect_info["ORGDB_ADMIN_PASSWORD"] = connect_info['DB_ADMIN_PASSWORD']
    g.db_connect_info["ORGDB_DATABASE"] = connect_info["DB_DATABASE"]
    g.db_connect_info["ORG_MONGO_OWNER"] = connect_info['MONGO_OWNER']
    g.db_connect_info["ORG_MONGO_CONNECTION_STRING"] = connect_info['MONGO_CONNECTION_STRING']
    g.db_connect_info["ORG_MONGO_ADMIN_USER"] = connect_info['MONGO_ADMIN_USER']
    g.db_connect_info["ORG_MONGO_ADMIN_PASSWORD"] = connect_info['MONGO_ADMIN_PASSWORD']
    g.db_connect_info["INITIAL_DATA_ANSIBLE_IF"] = connect_info['INITIAL_DATA_ANSIBLE_IF']
    g.db_connect_info["NO_INSTALL_DRIVER"] = connect_info['NO_INSTALL_DRIVER']

    # get ws-db connect infomation
    org_db = DBConnectOrg(organization_id)  # noqa: F405

    # get workspace info
    workspace_data_list = []
    workspace_data_list = org_db.table_select("T_COMN_WORKSPACE_DB_INFO", "WHERE `DISUSE_FLAG`=0")
    g.applogger.info("target workspace_id_list = {}".format([i.get('WORKSPACE_ID') for i in workspace_data_list]))

    # org-db root user connect
    org_root_db = DBConnectOrgRoot(organization_id)  # noqa: F405

    try:
        # OrganizationとWorkspaceが削除されている場合のエラーログ抑止する為、廃止してからデータベース削除
        org_db.db_transaction_start()
        for workspace_data in workspace_data_list:
            db_disuse_set(org_db, workspace_data['PRIMARY_KEY'], 'T_COMN_WORKSPACE_DB_INFO', 1)
        org_db.db_commit()
        g.applogger.info("Workspace is disused")

        common_db.db_transaction_start()
        db_disuse_set(common_db, connect_info['PRIMARY_KEY'], 'T_COMN_ORGANIZATION_DB_INFO', 1)
        common_db.db_commit()
        g.applogger.info("Organization is disused")

        # get driver info
        no_install_driver_tmp = org_db.get_no_install_driver()
        if no_install_driver_tmp is None or len(no_install_driver_tmp) == 0:
            no_install_driver = []
        else:
            no_install_driver = json.loads(no_install_driver_tmp)

        # delete gitlab user and projects
        if (os.environ.get('GITLAB_HOST') is not None) and (len(os.environ.get('GITLAB_HOST')) > 0):
            try:
                gitlab_agent = GitLabAgent()
                user_list = gitlab_agent.get_user_by_username(connect_info['GITLAB_USER'])
                for user in user_list:
                    gitlab_user_id = user['id']
                    projects = gitlab_agent.get_all_project_by_user_id(gitlab_user_id)
                    for project in projects:
                        gitlab_agent.delete_project(project['id'])
                    gitlab_agent.delete_user(gitlab_user_id)
            except Exception as e:
                t = traceback.format_exc()
                g.applogger.error("{}".format(arrange_stacktrace_format(t)))
                raise AppException("490-00001", [e], [])
            g.applogger.info("Gitlab is cleaned")

        # delete storage directory for organization
        strage_path = os.environ.get('STORAGEPATH')
        organization_dir = strage_path + organization_id + "/"
        if os.path.isdir(organization_dir):
            shutil.rmtree(organization_dir)
        g.applogger.info("Storage is cleaned")

        if 'oase' not in no_install_driver:
            org_mongo = MONGOConnectOrg(org_db)
            mongo_owner = bool(connect_info['MONGO_OWNER'])

        for workspace_data in workspace_data_list:
            # drop ws-db and ws-db-user
            org_root_db.connection_kill(workspace_data['DB_DATABASE'], workspace_data['DB_USER'])
            org_root_db.database_drop(workspace_data['DB_DATABASE'])
            org_root_db.user_drop(workspace_data['DB_USER'])
            g.applogger.info("Workspace DB and DB_USER(ws_id={}) is cleaned".format(workspace_data['WORKSPACE_ID']))

            # drop ws-mongodb and ws-mongodb-user
            if 'oase' not in no_install_driver and workspace_data.get('MONGO_DATABASE'):
                org_mongo.drop_database(workspace_data['MONGO_DATABASE'])
                g.applogger.info("Workspace MongoDB(ws_id={}) is cleaned".format(workspace_data['WORKSPACE_ID']))
                if mongo_owner is True:
                    org_mongo.drop_user(workspace_data['MONGO_USER'], workspace_data['MONGO_DATABASE'])
                    g.applogger.info("Workspace MongoDB_USER(ws_id={}) is cleaned".format(workspace_data['WORKSPACE_ID']))

        # drop org-db and org-db-user
        org_root_db.connection_kill(connect_info['DB_DATABASE'], connect_info['DB_USER'])
        org_root_db.database_drop(connect_info['DB_DATABASE'])
        org_root_db.user_drop(connect_info['DB_USER'])
        g.applogger.info("Organization DB and DB_USER(org_id={}) is cleaned".format(organization_id))

    except AppException as e:
        exception_flg = True
        raise AppException(e)
    except Exception as e:
        exception_flg = True
        raise e

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

        if 'common_db' in locals():
            common_db.db_disconnect()
        if 'org_root_db' in locals():
            org_root_db.db_disconnect()
        if 'org_db' in locals():
            org_db.db_disconnect()
        if 'org_mongo' in locals():
            org_mongo.disconnect()

    return '',


@api_filter_admin
def organization_info(organization_id):  # noqa: E501
    """organization_info

    Organization情報を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str

    :rtype: InlineResponse200
    """

    try:
        # ITA_DB connect
        common_db = DBConnectCommon()  # noqa: F405
        connect_info = common_db.get_orgdb_connect_info(organization_id)
        if connect_info is False:
            # Organization does not exist.
            return '', g.appmsg.get_api_message("490-02010", []), "490-02010", 490

        # ドライバのインストール状態を取得する
        drivers = {
            "terraform_cloud_ep": True,
            "terraform_cli": True,
            "ci_cd": True,
            "oase": True,
        }
        no_install_driver_json = connect_info.get('NO_INSTALL_DRIVER')
        if no_install_driver_json is not None:
            # no_install_driverの対象をFalseにする。
            no_install_driver = json.loads(no_install_driver_json)
            for driver_name in no_install_driver:
                drivers[driver_name] = False

        services = {}

        document_store = None
        if drivers["oase"] is True:
            # mongo_connection_string パスワードを***にマスキングする
            is_mongo_owner = bool(connect_info.get('MONGO_OWNER'))
            encrypt_mongo_connection_string = connect_info.get('MONGO_CONNECTION_STRING', '')

            mask_mongo_connection_string = ""
            if encrypt_mongo_connection_string:
                mongo_connection_string = ky_decrypt(encrypt_mongo_connection_string)
                url_check_bool, url_parse_obj, message_num = mongo_url_check(mongo_connection_string)
                if url_check_bool is False:
                    return "", url_parse_obj, message_num, 490

                mask_mongo_connection_string = mongo_connection_string.replace(url_parse_obj.password, '***')

            document_store = {
                "name": "mongodb",
                "owner": is_mongo_owner,
                "connection_string": mask_mongo_connection_string
            }

        if document_store is not None:
            services["document_store"] = document_store

        result_data = {
            "optionsita": {
                "drivers": drivers,
                "services": services
            }
        }
    finally:
        if "common_db" in locals():
            common_db.db_disconnect()
    return result_data,


@api_filter_admin
def organization_update(organization_id, body=None):  # noqa: E501
    """organization_update

    Organizationへドライバを追加・削除する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param body: 追加でインストールするドライバはtrue、アンインストールするドライバはfalseを設定する
    :type body: dict | bytes

    :rtype: InlineResponse2001
    """
    g.db_connect_info = {}
    # Bodyのチェック用
    driver_list = [
        'terraform_cloud_ep',
        'terraform_cli',
        'ci_cd',
        'oase'
    ]

    try:
        # Common DB connect
        common_db = DBConnectCommon()  # noqa: F405
        org_connect_info = common_db.get_orgdb_connect_info(organization_id)

        # インストールされていないドライバ一覧を取得
        no_install_driver_json = org_connect_info.get('NO_INSTALL_DRIVER')
        if no_install_driver_json:
            no_install_driver = json.loads(no_install_driver_json)
        else:
            no_install_driver = []
        update_no_install_driver = no_install_driver.copy()

        # bodyから「drivers」keyの値を取得
        if body is not None and len(body) > 0:
            drivers = body.get('drivers')
            for driver_name, driver_bool in drivers.items():
                # bodyのdriversに指定のドライバ名以外のkeyがある際にエラーとする。
                if driver_name not in driver_list:
                    # Value of key[{}] is invalid.
                    return '', g.appmsg.get_api_message("490-02005", ["drivers"]), "490-02005", 490
        else:
            # body内でdriverが指定されていないためエラーとする。
            # Body paramater '{}' is required.
            return '', g.appmsg.get_api_message("490-02006", ["drivers"]), "490-02006", 490

        # 追加するドライバの対象が、no_install_driverに含まれていない（すでにインストール済み）場合は追加対象から除外する
        # 削除するドライバの対象が、no_install_driverに含まれている場合は削除対象から除外する
        add_drivers = []
        remove_drivers = []
        for driver_name, driver_bool in drivers.items():
            if driver_name in no_install_driver and driver_bool is True:
                add_drivers.append(driver_name)
                update_no_install_driver.remove(driver_name)
            elif driver_name not in no_install_driver and driver_bool is False:
                remove_drivers.append(driver_name)
                update_no_install_driver.append(driver_name)
        g.applogger.info("plan to add these drivers({})".format(add_drivers))
        g.applogger.info("plan to remove these drivers({})".format(remove_drivers))

        # インストール時に利用するSQLファイル名の一覧
        add_driver_sql = {
            "terraform_cloud_ep": [['terraform_cloud_ep.sql', 'terraform_cloud_ep_master.sql']],
            "terraform_cli": [['terraform_cli.sql', 'terraform_cli_master.sql']],
            "ci_cd": [['cicd.sql', 'cicd_master.sql']],
            "oase": [['oase.sql', 'oase_master.sql']],
        }

        # インストール時に利用する削除対象ディレクトリのパスの一覧
        add_driver_files = {
            "terraform_cloud_ep": [''],
            "terraform_cli": [''],
            "ci_cd": [''],
            "oase": ['/uploadfiles/110102'],
        }

        # アンインストール時に利用するSQLファイル名の一覧
        remove_driver_sql = {
            "terraform_cloud_ep": [['terraform_cloud_ep.drop.sql', 'terraform_cloud_ep_master.delete.sql']],
            "terraform_cli": [['terraform_cli.drop.sql', 'terraform_cli_master.delete.sql']],
            "ci_cd": [['cicd.drop.sql', 'cicd_master.delete.sql']],
            "oase": [['oase.drop.sql', 'oase_master.delete.sql']],
        }

        # アンインストール時に利用する削除対象ディレクトリのパスの一覧
        remove_driver_files = {
            "terraform_cloud_ep": [['/driver/terraform_cloud_ep/', '/uploadfiles/80105'], ['', '/uploadfiles/80106'], ['', '/uploadfiles/80114']],
            "terraform_cli": [['/driver/terraform_cli/', '/uploadfiles/90104'], ['', '/uploadfiles/90109']],
            "ci_cd": [['/driver/cicd/repositories/', '']],
            "oase": [['', '/uploadfiles/110109']],
        }

        # terraform_commonの追加について
        if "terraform_cli" in add_drivers and ("terraform_cloud_ep" in no_install_driver):
            add_driver_sql["terraform_cli"].append(['terraform_common.sql', 'terraform_common_master.sql'])
        elif "terraform_cloud_ep" in add_drivers and "terraform_cli" in no_install_driver:
            add_driver_sql["terraform_cloud_ep"].append(['terraform_common.sql', 'terraform_common_master.sql'])
        # terraform_commonの削除について
        elif "terraform_cli" in remove_drivers and ("terraform_cloud_ep" in no_install_driver or "terraform_cloud_ep" in remove_drivers):
            remove_driver_sql["terraform_cli"].append(['terraform_common.drop.sql', ''])
        elif "terraform_cloud_ep" in remove_drivers and "terraform_cli" in no_install_driver:
            remove_driver_sql["terraform_cloud_ep"].append(['terraform_common.drop.sql', ''])

        # Organization DB connect
        org_db = DBConnectOrg(organization_id)  # noqa: F405

        # OASEが有効な場合
        is_exists_mongo_info = False
        if 'services' in body and 'document_store' in body['services']:
            is_exists_mongo_info = True
        mongo_host = None
        mongo_owner = None
        mongo_connection_string = None
        mongo_admin_user = None
        mongo_admin_password = None

        if "oase" in add_drivers or ("oase" not in no_install_driver and is_exists_mongo_info is True):
            if is_exists_mongo_info is False:
                # 必要な接続情報が足りない
                # Body paramater '{}' is required.
                return '', g.appmsg.get_api_message("490-02006", ["document_store"]), "490-02006", 490
            mongodb_info = body['services']['document_store']

            mongo_host = os.environ.get('MONGO_HOST', '')
            mongo_owner = mongodb_info.get('owner', True)
            mongo_connection_string = mongodb_info.get('connection_string', '')
            if mongo_connection_string:
                # 接続文字列の不正チェック
                url_check_bool, url_check_msg, message_num = mongo_url_check(mongo_connection_string)
                if url_check_bool is False:
                    return "", url_check_msg, message_num, 490

            # pattern
            # 1. mongo_owner=True   mongo_connection_string=""    WS単位でユーザを作成し、ＤＢと紐づける。内部コンテナを利用。
            # 2. mongo_owner=False  mongo_connection_string="xxx"   ユーザは作成しない。外部のmongoを利用。
            # 3. mongo_owner=True   mongo_connection_string="xxx"   WS単位でユーザを作成し、ＤＢと紐づける。外部のmongoを利用。未実装
            if (mongo_owner is True and not mongo_host) or (mongo_owner is False and not mongo_connection_string):
                # どちらのpatternの接続情報もなく、OASEドライバを追加できない。
                # The OASE driver cannot be added because the connection infomation of mongo is not set.
                return '', g.appmsg.get_api_message("490-02007", []), "490-02007", 490

            if "oase" not in no_install_driver:
            # インストール済みの場合（接続情報のみを変更する）
                g.applogger.info("oase is already installed. Connection infocation of mongo will be updated.(oase update pattern 2)")
                # v2.4ではpattern2→pattern2しか許さない
                if mongo_owner is True or not mongo_connection_string or bool(org_connect_info['MONGO_OWNER']) is True or not org_connect_info['MONGO_CONNECTION_STRING']:
                    # This change of mongo connection infomation is not allowed.
                    return '', g.appmsg.get_api_message("490-02011", []), "490-02011", 490
                # 同じ文字列の送信は許さない
                if mongo_connection_string == ky_decrypt(org_connect_info.get('MONGO_CONNECTION_STRING')):
                    # This mongo connection infomation is already changed.
                    return '', g.appmsg.get_api_message("490-02012", []), "490-02012", 490

            # v2.4ではmongo_owner=Trueは、内部コンテナしか許さないので、pattern1に流す
            if mongo_owner is True:
                g.applogger.info("oase update pattern 1-force")
                mongo_connection_string = ''

            if mongo_owner is True and not mongo_connection_string:
                # pattern1
                g.applogger.info("oase update pattern 1")
                mongo_admin_user = os.environ.get("MONGO_ADMIN_USER")
                mongo_admin_password = os.environ.get("MONGO_ADMIN_PASSWORD")

            data = {
                'PRIMARY_KEY': org_connect_info['PRIMARY_KEY'],
                'MONGO_OWNER': mongo_owner,
                'MONGO_CONNECTION_STRING': ky_encrypt(mongo_connection_string),
                'MONGO_ADMIN_USER': mongo_admin_user,
                'MONGO_ADMIN_PASSWORD': ky_encrypt(mongo_admin_password),
            }
            # 試しにmongoクライアントでエラーが出ないかチェックする
            g.db_connect_info["ORG_MONGO_OWNER"] = data['MONGO_OWNER']
            g.db_connect_info["ORG_MONGO_CONNECTION_STRING"] = data['MONGO_CONNECTION_STRING']
            g.db_connect_info["ORG_MONGO_ADMIN_USER"] = data['MONGO_ADMIN_USER']
            g.db_connect_info["ORG_MONGO_ADMIN_PASSWORD"] = data['MONGO_ADMIN_PASSWORD']
            org_mongo = MONGOConnectOrg()
            org_mongo.connect_check()

            common_db.db_transaction_start()
            common_db.table_update('T_COMN_ORGANIZATION_DB_INFO', data, 'PRIMARY_KEY')
            common_db.db_commit()

        # MongoのDB削除用情報
        elif 'oase' in remove_drivers:
            g.db_connect_info["ORG_MONGO_OWNER"] = org_connect_info['MONGO_OWNER']
            g.db_connect_info["ORG_MONGO_CONNECTION_STRING"] = org_connect_info['MONGO_CONNECTION_STRING']
            g.db_connect_info["ORG_MONGO_ADMIN_USER"] = org_connect_info['MONGO_ADMIN_USER']
            g.db_connect_info["ORG_MONGO_ADMIN_PASSWORD"] = org_connect_info['MONGO_ADMIN_PASSWORD']
            org_mongo = MONGOConnectOrg(org_db)
            mongo_owner = bool(org_connect_info['MONGO_OWNER'])

        # OrganizationのWorkspace一覧を取得
        workspace_data_list = org_db.table_select("T_COMN_WORKSPACE_DB_INFO", "WHERE `DISUSE_FLAG`=0")
        g.applogger.info("target workspace_id = {}".format([i.get('WORKSPACE_ID') for i in workspace_data_list]))

        # mongoのインデックス設定が一つでも失敗したら、Falseにする（失敗してもインストールを続行する）
        mongo_index_flg = True

        config_file_list = []
        config_file_dict = {}
        if len(add_drivers) != 0:
            # files配下のconfigファイルを取得する
            src_dir = os.path.join(os.environ.get('PYTHONPATH'), "files")
            g.applogger.info(f"[Trace] src_dir={src_dir}")
            if os.path.isdir(src_dir):
                config_file_list = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
                g.applogger.info(f"[Trace] config_file_list={config_file_list}")
                for config_file_name in config_file_list:
                    if config_file_name != "config.json":
                        driver_name = config_file_name.replace('_config.json', '')
                        config_file_dict[driver_name] = config_file_name

        # 対象のワークスペースをループし、追加するドライバについてのデータベース処理（SQLを実行しテーブルやレコードを作成）を行う
        for workspace_data in workspace_data_list:
            workspace_id = workspace_data['WORKSPACE_ID']
            g.applogger.info("Updating on workspace(workspace_id = {})".format(workspace_id))
            role_id = f'_{workspace_id}-admin'
            workspace_dir = os.environ.get('STORAGEPATH') + "{}/{}".format(organization_id, workspace_id)

            # Workspace DB connect
            ws_db = DBConnectWs(workspace_id, organization_id)  # noqa: F405
            ws_no_install_driver = workspace_data["NO_INSTALL_DRIVER"]
            if ws_no_install_driver is None:
                ws_no_install_driver = []
            else:
                ws_no_install_driver = json.loads(ws_no_install_driver)

            last_update_timestamp = str(get_timestamp())

            # 追加対象のドライバをループし、SQLファイルを実行する。
            for install_driver in add_drivers:
                # 既に対象ws内に追加対象ドライバがインストールされていたらスキップする
                if install_driver not in ws_no_install_driver:
                    g.applogger.info(f" SKIP INSTALL DRIVER BECAUSE {install_driver} IS ALREADY INSTALLED.")
                    continue
                g.applogger.info(" INSTALLING {} START".format(install_driver))
                # SQLファイルを特定する。
                sql_files_list = add_driver_sql[install_driver]
                for sql_files in sql_files_list:
                    ddl_file = os.environ.get('PYTHONPATH') + "sql/" + sql_files[0]
                    dml_file = os.environ.get('PYTHONPATH') + "sql/" + sql_files[1]

                    # create table of workspace-db
                    g.applogger.info(" execute " + ddl_file)
                    ws_db.sqlfile_execute(ddl_file)

                    # insert initial data of workspace-db
                    ws_db.db_transaction_start()
                    # #2079 /storage配下ではないので対象外
                    g.applogger.info(" execute " + dml_file)
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

                            ws_db.sql_execute(sql, prepared_list)
                    ws_db.db_commit()

                # 対象ドライバのディレクトリの削除を実行してから再作成を行う
                remove_files_list = add_driver_files[install_driver]
                for remove_files in remove_files_list:
                    # /uploadfiles配下
                    if remove_files != '':
                        remove_path_uploadfiles = workspace_dir + remove_files
                        if os.path.isdir(remove_path_uploadfiles):
                            g.applogger.info(" remove " + remove_path_uploadfiles)
                            shutil.rmtree(remove_path_uploadfiles)

                # files配下のconfigファイルを取得し、インストール中のドライバと一致していたら実行する
                if install_driver in config_file_dict:
                    dest_dir = os.path.join(workspace_dir, "uploadfiles")
                    config_file_path = os.path.join(src_dir, config_file_dict[install_driver])
                    g.applogger.info(f" [Trace] dest_dir={dest_dir}")
                    g.applogger.info(f" [Trace] config_file_path={config_file_path}")
                    put_uploadfiles(config_file_path, src_dir, dest_dir)
                g.applogger.info(" set initial material files")

                # t_comn_workspace_db_infoテーブルのNO_INSTALL_DRIVERを更新する
                ws_no_install_driver.remove(install_driver)
                if len(ws_no_install_driver) > 0:
                    ws_no_install_driver_json = json.dumps(ws_no_install_driver)
                else:
                    ws_no_install_driver_json = None
                org_db.db_transaction_start()
                data = {
                    'PRIMARY_KEY': workspace_data['PRIMARY_KEY'],
                    'NO_INSTALL_DRIVER': ws_no_install_driver_json,
                }
                org_db.table_update('T_COMN_WORKSPACE_DB_INFO', data, 'PRIMARY_KEY')
                org_db.db_commit()

                g.applogger.info(" INSTALLING {} IS ENDED".format(install_driver))

            # 削除対象のドライバをループし、SQLファイルを実行・必要のないディレクトリの削除・MongoDBの削除を実行する。
            for uninstall_driver in remove_drivers:
                # 既に対象ws内に削除対象ドライバがアンインストールされていたらスキップする
                if uninstall_driver in ws_no_install_driver:
                    g.applogger.info(f" SKIP UNINSTALL DRIVER BECAUSE {uninstall_driver} IS ALREADY UNINSTALLED.")
                    continue
                g.applogger.info(" UNINSTALLING {} START".format(uninstall_driver))
                # SQLファイルを特定する。
                sql_files_list = remove_driver_sql[uninstall_driver]
                for sql_files in sql_files_list:
                    dml_file = os.environ.get('PYTHONPATH') + "sql/uninstall/" + sql_files[1]
                    ddl_file = os.environ.get('PYTHONPATH') + "sql/uninstall/" + sql_files[0]

                    if sql_files[1] != '':
                        # delete data in workspace-db
                        ws_db.db_transaction_start()
                        g.applogger.info(" execute " + dml_file)
                        with open(dml_file, "r") as f:
                            sql_list = f.read().split(";\n")
                            for sql in sql_list:
                                if re.fullmatch(r'[\s\n\r]*', sql):
                                    continue
                                prepared_list = []
                                ws_db.sql_execute(sql, prepared_list)
                        ws_db.db_commit()

                    # delete tables in workspace-db
                    g.applogger.info(" execute " + ddl_file)
                    ws_db.sqlfile_execute(ddl_file)

                # ディレクトリの削除を実行する
                remove_files_list = remove_driver_files[uninstall_driver]
                for remove_files in remove_files_list:
                    # /driver配下
                    if remove_files[0] != '':
                        remove_path = workspace_dir + remove_files[0]
                        if os.path.isdir(remove_path):
                            # /driver配下のディレクトリを作成する
                            g.applogger.info(" remove " + remove_path)
                            shutil.rmtree(remove_path)
                            g.applogger.info(" remake " + remove_path)
                            os.mkdir(remove_path)

                    # /uploadfiles配下
                    if remove_files[1] != '':
                        remove_path_uploadfiles = workspace_dir + remove_files[1]
                        if os.path.isdir(remove_path_uploadfiles):
                            g.applogger.info(" remove " + remove_path_uploadfiles)
                            shutil.rmtree(remove_path_uploadfiles)

                    # MongoのDBがあれば削除
                    if uninstall_driver == "oase":
                        if workspace_data.get('MONGO_DATABASE'):
                            # drop ws-mongodb and ws-mongodb-user
                            org_mongo.drop_database(workspace_data['MONGO_DATABASE'])
                            g.applogger.info(" Workspace MongoDB(ws_id={}) is cleaned".format(workspace_data['WORKSPACE_ID']))
                            if mongo_owner is True:
                                org_mongo.drop_user(workspace_data['MONGO_USER'], workspace_data['MONGO_DATABASE'])
                                g.applogger.info(" Workspace MongoDB_USER(ws_id={}) is cleaned".format(workspace_data['WORKSPACE_ID']))
                            ws_primary_key = workspace_data['PRIMARY_KEY']
                            data = {
                                "PRIMARY_KEY": ws_primary_key,
                                "MONGO_CONNECTION_STRING": '',
                                "MONGO_DATABASE": None,
                                "MONGO_USER": None,
                                "MONGO_PASSWORD": ''
                            }

                            org_db.db_transaction_start()
                            org_db.table_update("T_COMN_WORKSPACE_DB_INFO", data, "PRIMARY_KEY")
                            org_db.db_commit()

                            g.applogger.info(" Updating infomation of mongo on workspace(workspace_id = {})".format(workspace_id))

                # t_comn_workspace_db_infoテーブルのNO_INSTALL_DRIVERを更新する
                ws_no_install_driver.append(uninstall_driver)
                if len(ws_no_install_driver) > 0:
                    ws_no_install_driver_json = json.dumps(ws_no_install_driver)
                else:
                    ws_no_install_driver_json = None
                org_db.db_transaction_start()
                data = {
                    'PRIMARY_KEY': workspace_data['PRIMARY_KEY'],
                    'NO_INSTALL_DRIVER': ws_no_install_driver_json,
                }
                org_db.table_update('T_COMN_WORKSPACE_DB_INFO', data, 'PRIMARY_KEY')
                org_db.db_commit()

                g.applogger.info(" UNINSTALLING {} IS ENDED".format(uninstall_driver))

            # OASEがインストールされる場合 or インストール済みで接続情報を変更したい場合
            if "oase" in add_drivers or ("oase" not in no_install_driver and is_exists_mongo_info is True):
                g.applogger.info(" Updating connection infomation of mongo start")
                if "oase" in add_drivers:
                    # 初めてインストールするときは、DB名とユーザ名を払い出す
                    ws_mongo_name, ws_mongo_user, ws_mongo_password = org_mongo.userinfo_generate("ITA_WS")
                else:
                    # 接続情報の変更はDB名を継続利用
                    # v2.4ではpattern2のみ
                    ws_mongo_name = workspace_data['MONGO_DATABASE']
                g.applogger.info(" MONGO_DATABASE={}".format(ws_mongo_name))

                # pattern1 pattern3
                if mongo_owner is True:
                    try:
                        # create workspace-mongodb-user
                        org_mongo.create_user(
                            ws_mongo_user,
                            ws_mongo_password,
                            ws_mongo_name
                        )
                    except Exception as e:
                        t = traceback.format_exc()
                        g.applogger.error(arrange_stacktrace_format(t))
                        raise AppException("490-00002", [e], [])
                # pattern2
                else:
                    ws_mongo_user = None
                    ws_mongo_password = None

                # get workspace-db connect infomation
                ws_info_primary_key = workspace_data["PRIMARY_KEY"]

                # update workspace-db connect infomation
                update_data = {
                    "PRIMARY_KEY": ws_info_primary_key,
                    "MONGO_DATABASE": ws_mongo_name,
                    "MONGO_USER": ws_mongo_user,
                    "MONGO_PASSWORD": ky_encrypt(ws_mongo_password)
                }
                # 新規インストールの場合の接続文字列の埋め込み
                # もしくは
                # organizationの接続文字列を継承しているものだけ、変更を反映する
                if mongo_connection_string and ("oase" in add_drivers or ky_decrypt(org_connect_info.get('MONGO_CONNECTION_STRING')) == ky_decrypt(workspace_data.get('MONGO_CONNECTION_STRING'))):
                    update_data['MONGO_CONNECTION_STRING'] = ky_encrypt(mongo_connection_string)

                g.db_connect_info["WS_MONGO_CONNECTION_STRING"] = update_data.get('MONGO_CONNECTION_STRING')
                g.db_connect_info["WS_MONGO_DATABASE"] = update_data['MONGO_DATABASE']
                g.db_connect_info["WS_MONGO_USER"] = update_data.get('MONGO_USER')
                g.db_connect_info["WS_MONGO_PASSWORD"] = update_data.get('MONGO_PASSWORD')

                org_db.db_transaction_start()
                org_db.table_update("T_COMN_WORKSPACE_DB_INFO", update_data, "PRIMARY_KEY")
                org_db.db_commit()
                g.applogger.info(" Updating connection infomation of mongo is ended")

                # OASEのmongo設定（インデックスなど）
                ws_mongo = MONGOConnectWs()
                try:
                    # db.labeled_event_collection.createIndex({"labels._exastro_fetched_time":1,"labels._exastro_end_time":1,"_id":1}, {"name": "default_sort"})
                    ws_mongo.collection(mongoConst.LABELED_EVENT_COLLECTION).create_index([("labels._exastro_fetched_time", ASCENDING), ("labels._exastro_end_time", ASCENDING), ("_id", ASCENDING)], name="default_sort")
                    g.applogger.info(" Index of mongo is made")
                except Exception as e:
                    # mongoのインデックス設定に失敗してもインストール作業は続ける
                    mongo_index_flg = False
                    mongo_error = e
                    t = traceback.format_exc()
                    g.applogger.error("The problem is occured in MongoDB.See below logs...(organization_id='{}' workspace_id='{}')".format(organization_id, workspace_id))
                    g.applogger.error(arrange_stacktrace_format(t))

                g.db_connect_info.pop("WS_MONGO_CONNECTION_STRING")
                g.db_connect_info.pop("WS_MONGO_DATABASE")
                g.db_connect_info.pop("WS_MONGO_USER")
                g.db_connect_info.pop("WS_MONGO_PASSWORD")

        # t_comn_organization_db_infoテーブルのMONGODB接続情報, NO_INSTALL_DRIVERを更新する
        if len(update_no_install_driver) > 0:
            update_no_install_driver_json = json.dumps(update_no_install_driver)
        else:
            update_no_install_driver_json = None

        common_db.db_transaction_start()
        data = {
            'PRIMARY_KEY': org_connect_info['PRIMARY_KEY'],
            'NO_INSTALL_DRIVER': update_no_install_driver_json,
        }
        if "oase" in remove_drivers:
            data["MONGO_OWNER"] = None
            data["MONGO_CONNECTION_STRING"] = ""
            data['MONGO_ADMIN_USER'] = None
            data["MONGO_ADMIN_PASSWORD"] = ""
        common_db.table_update('T_COMN_ORGANIZATION_DB_INFO', data, 'PRIMARY_KEY')
        common_db.db_commit()
    finally:
        if 'common_db' in locals():
            common_db.db_disconnect()
        if 'org_db' in locals():
            org_db.db_disconnect()
        if 'org_mongo' in locals():
            org_mongo.disconnect()
        if 'ws_mongo' in locals():
            ws_mongo.disconnect()

    if mongo_index_flg is False:
        raise AppException("490-01001", [mongo_error], [mongo_error])

    return '',


def db_disuse_set(db_obj, pkey, table, disuse_flg):
    # disuse org-db connect infomation
    data = {
        'PRIMARY_KEY': pkey,
        'DISUSE_FLAG': disuse_flg
    }
    db_obj.table_update(table, data, "PRIMARY_KEY")


def mongo_url_check(mongo_connection_string):
    # 接続文字列の不正チェック
    url_check_bool, url_parse_obj = url_check(mongo_connection_string, username=True, password=True, port=True)
    if url_check_bool is False:
        # Body paramater '{}' is invalid. ({})
        return False, g.appmsg.get_api_message("490-02013", ["services.document_store.connection_string", url_parse_obj]), "490-02013"

    if url_parse_obj.scheme not in ['mongodb', 'mongodb+srv']:
        # URI must begin with 'mongodb://' or 'mongodb+srv://'.
        return False, g.appmsg.get_api_message("490-02014", []), "490-02014"

    return True, url_parse_obj, None
