# Copyright 2023 NEC Corporation#
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
import os
from flask import g
from common_libs.common.dbconnect import *  # noqa: F403
"""
ライブラリ
"""


def read_version_list(file_path):
    """
    version.listを読み込む

    Returns:
        list
    """

    with open(file_path) as f:
        lines = f.readlines()

    version_list = []
    for line in lines:
        # 先頭'#' はコメントとして除外
        if line.startswith('#'):
            continue

        line = line.rstrip()  # 末尾の改行除去

        # 空行は除外
        if len(line) == 0:
            continue

        version_list.append(line)

    return version_list


def get_migration_target_versions():
    """
    get versions list

    Returns:
        list: versions
    """

    # version.listファイル読み込み
    version_list_path = os.path.join(g.APPPATH, "version.list")
    version_list = read_version_list(version_list_path)

    common_db_root = DBConnectCommonRoot()  # noqa: F405

    # 1. Databaseの存在確認
    sql = "SHOW DATABASES"
    database_list = common_db_root.sql_execute(sql)

    match_flg = False
    for recode in database_list:
        if recode.get('Database').lower() == os.environ.get('DB_DATABASE').lower():
            match_flg = True
            break

    if match_flg is False:
        # Databaseが無い場合
        g.applogger.info("Current version=[None].")
        # シングルコーテーションをエスケープ
        db_database = os.environ.get('DB_DATABASE').replace('\'', '\\\'')
        db_user = os.environ.get('DB_USER').replace('\'', '\\\'')
        db_password = os.environ.get('DB_PASSWORD').replace('\'', '\\\'')
        # Database作成
        sql = f"CREATE DATABASE IF NOT EXISTS `{db_database}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        common_db_root.sql_execute(sql)
        # ユーザ作成
        sql = f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_password}'"
        common_db_root.sql_execute(sql)
        # 権限付与
        sql = f"GRANT ALL PRIVILEGES ON `{db_database}` . * TO '{db_user}'@'%'"
        common_db_root.sql_execute(sql)

        # Database作成した場合＝初期インストールとして全バージョン分対応する
        return version_list

    common_db_root.db_disconnect()

    # 2. T_COMN_VERSION から現在のバージョン取得
    common_db = DBConnectCommon()  # noqa: F405
    sql = "SELECT * FROM `INFORMATION_SCHEMA`.`TABLES` WHERE `TABLE_NAME` = %s"
    table_list = common_db.sql_execute(sql, ['T_COMN_VERSION'])

    if len(table_list) != 1:
        # T_COMN_VERSION テーブルが用意されていない環境＝初期バージョン2.0.6として以降の全バージョン分対応する
        g.applogger.info("Current version=[2.0.6].")
        return version_list[1:]

    data_list = common_db.table_select("T_COMN_VERSION", "WHERE `SERVICE_ID` = 1")
    if len(data_list) != 1:
        raise Exception("Failed to get current version.")

    current_version = data_list[0]['VERSION']

    # current_version が含まれていたら、それ以降のversion_listを返す
    if current_version in version_list:
        g.applogger.info(f"Current version=[{current_version}].")
        index = version_list.index(current_version)
        del version_list[:(index + 1)]
    else:
        raise Exception(f"No such version. version:{current_version}")

    return version_list


def set_version(version):
    """
    set version
    """
    common_db = DBConnectCommon()  # noqa: F405
    data = {
        'SERVICE_ID': 1,
        'VERSION': version
    }
    common_db.db_transaction_start()
    common_db.table_update("T_COMN_VERSION", data, "SERVICE_ID")
    common_db.db_commit()


BACKYARD_STOP_FLAG_FILE_NAME = "skip_all_service"


def stop_all_backyards():
    """
    全backyardを停止させる
    """

    flag_file_path = os.path.join(os.environ.get('STORAGEPATH'), BACKYARD_STOP_FLAG_FILE_NAME)
    with open(flag_file_path, "a") as f:
        current_datetime = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        f.write(current_datetime)


def restart_all_backyards():
    """
    全backyardを再開させる
    """

    flag_file_path = os.path.join(os.environ.get('STORAGEPATH'), BACKYARD_STOP_FLAG_FILE_NAME)
    if os.path.isfile(flag_file_path):
        os.remove(flag_file_path)


def get_organization_ids():
    """
    get organization ids

    Returns:
        list: organization ids
    """

    common_db = DBConnectCommon()  # noqa: F405
    organization_info_list = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE `DISUSE_FLAG`=0 ORDER BY `LAST_UPDATE_TIMESTAMP`")

    return_dict = [x['ORGANIZATION_ID'] for x in organization_info_list]

    return return_dict


def get_workspace_ids(organization_id):
    """
    get organization ids

    Returns:
        list: organization ids
    """

    org_db = DBConnectOrg(organization_id)  # noqa: F405
    workspace_info_list = org_db.table_select("T_COMN_WORKSPACE_DB_INFO", "WHERE `DISUSE_FLAG`=0 ORDER BY `LAST_UPDATE_TIMESTAMP`")

    return_dict = [x['WORKSPACE_ID'] for x in workspace_info_list]

    return return_dict
