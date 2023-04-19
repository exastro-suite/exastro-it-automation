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
# import connexion
# import six
import datetime
from flask import g
from common_libs.common import *
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from common_libs.api import api_filter
from common_libs.cicd.classes.cicd_definition import TD_SYNC_STATUS_NAME_DEFINE


@api_filter
def post_cicd_for_iac_resume_filelink(organization_id, workspace_id, uuid, body=None):  # noqa: E501
    """post_cicd_for_iac_resume_filelink

    資材紐付の再開 # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param uuid: uuid
    :type uuid: str

    :rtype: InlineResponse20011
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)

    # メニューの存在確認
    menu = "file_link"
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # トランザクション開始
    objdbca.db_transaction_start()

    # 再開対象資材紐付確認
    sql = (
        "SELECT "
        "  T1.*, "
        "  T2.DISUSE_FLAG DISUSE_FLAG_REPO, "
        "  T3.DISUSE_FLAG DISUSE_FLAG_MATL "
        "FROM T_CICD_MATL_LINK    T1 "
        "LEFT OUTER JOIN "
        "  T_CICD_REPOSITORY_LIST T2 "
        "ON T1.REPO_ROW_ID = T2.REPO_ROW_ID "
        "LEFT OUTER JOIN "
        "  T_CICD_MATL_LIST       T3 "
        "ON T1.MATL_ROW_ID = T3.MATL_ROW_ID "
        "WHERE MATL_LINK_ROW_ID = %s "
    )
    rows = objdbca.sql_execute(sql, [uuid])
    if len(rows) == 0:
        log_msg_args = [uuid]
        api_msg_args = [uuid]
        # 再開する資材紐付のレコードが特定できませんでした。(資材紐付 項番:{})
        raise AppException("499-01204", log_msg_args, api_msg_args)
    else:
        row = rows[0]
        # 廃止レコード確認
        if row['DISUSE_FLAG'] == '1':
            # 廃止レコードは再開できません。(資材紐付 項番:{})
            log_msg_args = [uuid]
            api_msg_args = [uuid]
            raise AppException("499-01205", log_msg_args, api_msg_args)

        # 同期状態が異常確認
        if row['SYNC_STATUS_ROW_ID'] != TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR:
            # 同期状態が異常ではないので再開は受け付けられません。一覧を更新して、同期状態を確認して下さい。(資材紐付 項番:{})
            log_msg_args = [uuid]
            api_msg_args = [uuid]
            raise AppException("499-01206", log_msg_args, api_msg_args)

        # 廃止レコード確認(リポジトリ)
        if row['DISUSE_FLAG_REPO'] != '0':
            # 対象のリモートリポジトリが登録されていません。(資材紐付 項番:{} リモートリポジトリ項番:{})
            log_msg_args = [uuid, row['REPO_ROW_ID']]
            api_msg_args = [uuid, row['REPO_ROW_ID']]
            raise AppException("499-01208", log_msg_args, api_msg_args)

        # 廃止レコード確認(リポジトリ資材)
        if row['DISUSE_FLAG_MATL'] != '0':
            # 対象のリモートリポジトリ資材が登録されていません。(資材紐付 項番:{} リモートリポジトリ資材項番:{})
            log_msg_args = [uuid, row['MATL_ROW_ID']]
            api_msg_args = [uuid, row['MATL_ROW_ID']]
            raise AppException("499-01207", log_msg_args, api_msg_args)

    # リモートリポジトリの同期状態を再開に設定
    table_name = "T_CICD_MATL_LINK"
    data_list = {}
    data_list["MATL_LINK_ROW_ID"] = uuid
    data_list["SYNC_STATUS_ROW_ID"] = TD_SYNC_STATUS_NAME_DEFINE.STS_RESTART                    # 同期状態:　再開
    data_list["SYNC_ERROR_NOTE"] = None                                                         # 詳細情報:　クリア
    data_list["SYNC_LAST_TIME"] = None                                                          # 最終日時:　クリア
    data_list["DEL_ERROR_NOTE"] = None                                                          # デリバリ詳細情報:　クリア
    data_list["DEL_EXEC_INS_NO"] = None                                                         # デリバリ作業インスタンスNo:　クリア
    data_list["SYNC_LAST_TIME"] = None                                                          # デリバリ対象メニュー:　クリア
    data_list["LAST_UPDATE_TIMESTAMP"] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    data_list["LAST_UPDATE_USER"] = g.USER_ID
    primary_key_name = "MATL_LINK_ROW_ID"
    objdbca.table_update(table_name, data_list, primary_key_name, True)

    # トランザクション終了(commit)
    objdbca.db_transaction_end(True)

    result_msg = g.appmsg.get_api_message("MSG-90042", [uuid])
    return result_msg,


@api_filter
def post_cicd_for_iac_resume_repository(organization_id, workspace_id, uuid, body=None):  # noqa: E501
    """post_cicd_for_iac_resume_repository

    リモートリポジトリの再開

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param uuid: uuid
    :type uuid: str

    :rtype: InlineResponse20011
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)

    # メニューの存在確認
    menu = "remote_repository"
    check_menu_info(menu, objdbca)

    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
    sheet_type_list = ['0']
    check_sheet_type(menu, sheet_type_list, objdbca)

    # メニューに対するロール権限をチェック
    check_auth_menu(menu, objdbca)

    # トランザクション開始
    objdbca.db_transaction_start()

    # 再開対象リモートリポジトリ確認
    sql = "SELECT * FROM T_CICD_REPOSITORY_LIST WHERE REPO_ROW_ID = %s"
    rows = objdbca.sql_execute(sql, [uuid])
    if len(rows) == 0:
        log_msg_args = [uuid]
        api_msg_args = [uuid]
        # 再開するリモートリポジトリのレコードが特定できませんでした。(リモートリポジトリ 項番:{})
        raise AppException("499-01201", log_msg_args, api_msg_args)
    else:
        row = rows[0]
        # 廃止レコード確認
        if row['DISUSE_FLAG'] == '1':
            # 廃止レコードは再開できません。(リモートリポジトリ 項番:{})
            log_msg_args = [uuid]
            api_msg_args = [uuid]
            raise AppException("499-01202", log_msg_args, api_msg_args)

        # 同期状態が異常確認
        if row['SYNC_STATUS_ROW_ID'] != TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR:
            # 同期状態が異常ではないので再開は受け付けられません。一覧を更新して、同期状態を確認して下さい。(リモート リポジトリ 項番:{})
            log_msg_args = [uuid]
            api_msg_args = [uuid]
            raise AppException("499-01203", log_msg_args, api_msg_args)

    # リモートリポジトリの同期状態を再開に設定
    table_name = "T_CICD_REPOSITORY_LIST"
    data_list = {}
    data_list["REPO_ROW_ID"] = uuid
    data_list["SYNC_STATUS_ROW_ID"] = TD_SYNC_STATUS_NAME_DEFINE.STS_RESTART                    # 同期状態:　再開
    data_list["SYNC_ERROR_NOTE"] = None                                                         # 詳細情報:　クリア
    data_list["SYNC_LAST_TIMESTAMP"] = None                                                     # 最終日時:　クリア
    data_list["LAST_UPDATE_TIMESTAMP"] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    data_list["LAST_UPDATE_USER"] = g.USER_ID
    primary_key_name = "REPO_ROW_ID"
    objdbca.table_update(table_name, data_list, primary_key_name, True)

    # トランザクション終了(commit)
    objdbca.db_transaction_end(True)

    result_msg = g.appmsg.get_api_message("MSG-90041", [uuid])
    return result_msg,
