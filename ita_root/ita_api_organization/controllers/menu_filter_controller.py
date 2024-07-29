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

import connexion
import sys

sys.path.append('../../')
from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import DBConnectWs
from common_libs.api import api_filter, api_filter_download_file
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type
from libs import menu_filter


@api_filter
def get_filter_count(organization_id, workspace_id, menu):  # noqa: E501
    """get_filter_count

    レコード全件の件数を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str

    :rtype: InlineResponse2004
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        # MongoDBからデータを取得するシートタイプを追加。後から追加したことを示すためあえてappendしている。
        # 26 : MongoDBを利用するシートタイプ
        sheet_type_list.append('26')
        # 28 : 作業管理のシートタイプ追加
        sheet_type_list.append('28')
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        filter_parameter = {}
        result_data = menu_filter.rest_count(objdbca, menu, filter_parameter)
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def get_filter(organization_id, workspace_id, menu, file=None):  # noqa: E501
    """get_filter

    レコードを全件取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param file: ファイルデータ指定
    :type file: str

    :rtype: InlineResponse2003
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        # MongoDBからデータを取得するシートタイプを追加。後から追加したことを示すためあえてappendしている。
        # 26 : MongoDBを利用するシートタイプ
        sheet_type_list.append('26')
        # 28 : 作業管理のシートタイプ追加
        sheet_type_list.append('28')
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        base64_file_flg = True;
        if file == 'no':
            base64_file_flg = False;

        filter_parameter = {}
        result_data = menu_filter.rest_filter(objdbca, menu, filter_parameter, base64_file_flg=base64_file_flg)

    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def get_journal(organization_id, workspace_id, menu, uuid, file=None):  # noqa: E501
    """get_journal

    レコードの履歴を取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param uuid: UUID
    :type uuid: str
    :param file: ファイルデータ指定
    :type file: str

    :rtype: InlineResponse2003
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        # 28 : 作業管理のシートタイプ追加
        sheet_type_list.append('28')
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        base64_file_flg = True;
        if file == 'no':
            base64_file_flg = False;

        result_data = menu_filter.rest_filter_journal(objdbca, menu, uuid, base64_file_flg=base64_file_flg)
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def post_filter(organization_id, workspace_id, menu, body=None, file=None):  # noqa: E501
    """post_filter

    検索条件を指定し、レコードを取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes
    :param file: ファイルデータ指定
    :type file: str

    :rtype: InlineResponse2005
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        # MongoDBからデータを取得するシートタイプを追加。後から追加したことを示すためあえてappendしている。
        # 26 : MongoDBを利用するシートタイプ
        sheet_type_list.append('26')
        # 28 : 作業管理のシートタイプ追加
        sheet_type_list.append('28')
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        filter_parameter = {}
        if connexion.request.is_json:
            body = dict(connexion.request.get_json())
            filter_parameter = body

        base64_file_flg = True;
        if file == 'no':
            base64_file_flg = False;

        # メニューのカラム情報を取得
        result_data = menu_filter.rest_filter(objdbca, menu, filter_parameter, base64_file_flg=base64_file_flg)

    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter
def post_filter_count(organization_id, workspace_id, menu, body=None):  # noqa: E501
    """post_filter_count

    検索条件を指定し、レコードの件数する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2005
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        # MongoDBからデータを取得するシートタイプを追加。後から追加したことを示すためあえてappendしている。
        # 26 : MongoDBを利用するシートタイプ
        sheet_type_list.append('26')
        # 28 : 作業管理のシートタイプ追加
        sheet_type_list.append('28')
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        filter_parameter = {}
        if connexion.request.is_json:
            body = dict(connexion.request.get_json())
            filter_parameter = body

        # メニューのカラム情報を取得
        result_data = menu_filter.rest_count(objdbca, menu, filter_parameter)
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter_download_file
def download_file(organization_id, workspace_id, menu, uuid, column):
    """download_file

    アップロードされているファイルをダウンロードする # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param uuid: uuid
    :type uuid: str
    :param column: カラムREST名
    :type column: str

    :rtype: InlineResponse2005
    """
    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6', '28']
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        # ファイルデータ取得
        result_data = menu_filter.get_file_path(objdbca, menu, uuid, column)
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,


@api_filter_download_file
def download_history_file(organization_id, workspace_id, menu, uuid, column, journal_uuid):  # noqa: E501
    """download_history_file

    履歴のアップロードファイルをダウンロードする # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param uuid: UUID
    :type uuid: str
    :param column: カラムREST名
    :type column: str
    :param journal_uuid: 履歴のUUID
    :type journal_uuid: str

    :rtype: InlineResponse2005
    """

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6', '28']
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        check_auth_menu(menu, objdbca)

        # ファイルデータ取得
        result_data = menu_filter.get_history_file_path(objdbca, menu, uuid, column, journal_uuid)
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,
