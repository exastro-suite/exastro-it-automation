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

from flask import g
import connexion
from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common import menu_excel
from common_libs.api import api_filter, check_request_body, api_filter_download_temporary_file
from libs.organization_common import check_menu_info, check_auth_menu, check_sheet_type


def get_excel_filter(organization_id, workspace_id, menu, file=None):  # noqa: E501
    """get_excel_filter

    全件のExcelを取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param file: ファイルデータの形式指定
    :type file: str

    :rtype: InlineResponse2007
    """
    def main_func(base64_flg):
        # DB接続
        objdbca = DBConnectWs(workspace_id)  # noqa: F405

        try:
            # メニューの存在確認
            menu_record = check_menu_info(menu, objdbca)

            # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
            sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
            # 28 : 作業管理のシートタイプ追加
            sheet_type_list.append('28')
            menu_table_link_record = check_sheet_type(menu, sheet_type_list, objdbca)

            # メニューに対するロール権限をチェック
            check_auth_menu(menu, objdbca)

            filter_parameter = {'discard': {'NORMAL': ''}}
            result_data = menu_excel.collect_excel_filter(objdbca, organization_id, workspace_id, menu, menu_record, menu_table_link_record, filter_parameter, base64_flg=base64_flg)
        except Exception as e:
            raise e
        finally:
            objdbca.db_disconnect()
        return result_data,

    # ファイルをバイナリ or Base64で返すか分岐
    if file == "binary":
        @api_filter_download_temporary_file
        def return_filepath():
            return main_func(False)
        return return_filepath()
    else:
        @api_filter
        def return_base64():
            return main_func(True)
        return return_base64()


def get_excel_format(organization_id, workspace_id, menu, file=None):  # noqa: E501
    """get_excel_format

    新規登録用Excelを取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param file: ファイルデータの形式指定
    :type file: str

    :rtype: InlineResponse2007
    """

    def main_func(base64_flg):
        # DB接続
        objdbca = DBConnectWs(workspace_id)  # noqa: F405

        try:
            # メニューの存在確認
            menu_record = check_menu_info(menu, objdbca)

            # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
            sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
            # 28 : 作業管理のシートタイプ追加
            sheet_type_list.append('28')
            menu_table_link_record = check_sheet_type(menu, sheet_type_list, objdbca)

            # メニューに対するロール権限をチェック
            check_auth_menu(menu, objdbca)

            result_data = menu_excel.collect_excel_filter(objdbca, organization_id, workspace_id, menu, menu_record, menu_table_link_record, base64_flg=base64_flg)
        except Exception as e:
            raise e
        finally:
            objdbca.db_disconnect()
        return result_data,

    # ファイルをバイナリ or Base64で返すか分岐
    if file == "binary":
        print("あっちあっちあっちあっちあっち")
        @api_filter_download_temporary_file
        def return_filepath():
            return main_func(False)
        return return_filepath()
    else:
        print("こっちこっちこっちこっちこっち")
        @api_filter
        def return_base64():
            return main_func(True)
        return return_base64()


def get_excel_journal(organization_id, workspace_id, menu, file=None):  # noqa: E501
    """get_excel_journal

    変更履歴のExcelを取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param file: ファイルデータの形式指定
    :type file: str

    :rtype: InlineResponse2007
    """

    def main_func(base64_flg):
        # DB接続
        objdbca = DBConnectWs(workspace_id)  # noqa: F405

        try:
            # メニューの存在確認
            menu_record = check_menu_info(menu, objdbca)

            # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
            sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
            # 28 : 作業管理のシートタイプ追加
            sheet_type_list.append('28')
            menu_table_link_record = check_sheet_type(menu, sheet_type_list, objdbca)

            # メニューに対するロール権限をチェック
            check_auth_menu(menu, objdbca)

            result_data = menu_excel.collect_excel_journal(objdbca, organization_id, workspace_id, menu, menu_record, menu_table_link_record, base64_flg=base64_flg)
        except Exception as e:
            raise e
        finally:
            objdbca.db_disconnect()
        return result_data,

    # ファイルをバイナリ or Base64で返すか分岐
    if file == "binary":
        @api_filter_download_temporary_file
        def return_filepath():
            return main_func(False)
        return return_filepath()
    else:
        @api_filter
        def return_base64():
            return main_func(True)
        return return_base64()


def post_excel_filter(organization_id, workspace_id, menu, body=None, file=None):  # noqa: E501
    """post_excel_filter

    検索条件を指定し、Excelを取得する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes
    :param file: ファイルデータの形式指定
    :type file: str

    :rtype: InlineResponse2007
    """

    def main_func(base64_flg):
        # DB接続
        objdbca = DBConnectWs(workspace_id)  # noqa: F405

        try:
            # メニューの存在確認
            menu_record = check_menu_info(menu, objdbca)

            # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
            sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
            # 28 : 作業管理のシートタイプ追加
            sheet_type_list.append('28')
            menu_table_link_record = check_sheet_type(menu, sheet_type_list, objdbca)

            # メニューに対するロール権限をチェック
            check_auth_menu(menu, objdbca)

            filter_parameter = {}
            if connexion.request.is_json:
                body = dict(connexion.request.get_json())
                filter_parameter = body

            # メニューのカラム情報を取得
            result_data = menu_excel.collect_excel_filter(objdbca, organization_id, workspace_id, menu, menu_record, menu_table_link_record, filter_parameter, base64_flg=base64_flg)
        except Exception as e:
            raise e
        finally:
            objdbca.db_disconnect()
        return result_data,

    # ファイルをバイナリ or Base64で返すか分岐
    if file == "binary":
        @api_filter_download_temporary_file
        def return_filepath():
            return main_func(False)
        return return_filepath()
    else:
        @api_filter
        def return_base64():
            return main_func(True)
        return return_base64()


@api_filter
def post_excel_maintenance(organization_id, workspace_id, menu, body=None, **kwargs):  # noqa: E501
    """post_excel_maintenance

    Excelでレコードを登録/更新/廃止/復活する # noqa: E501

    :param organization_id: OrganizationID
    :type organization_id: str
    :param workspace_id: WorkspaceID
    :type workspace_id: str
    :param menu: メニュー名
    :type menu: str
    :param body:
    :type body: dict | bytes

    :rtype: InlineResponse2004
    """
    # メンテナンスモードのチェック
    if g.maintenance_mode.get('data_update_stop') == '1':
        status_code = "498-00001"
        raise AppException(status_code, [], [])  # noqa: F405

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # メニューの存在確認
        menu_record = check_menu_info(menu, objdbca)

        # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
        sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
        # 28 : 作業管理のシートタイプ追加
        sheet_type_list.append('28')
        check_sheet_type(menu, sheet_type_list, objdbca)

        # メニューに対するロール権限をチェック
        privilege = check_auth_menu(menu, objdbca)
        if privilege == '2':
            status_code = "401-00001"
            log_msg_args = [menu]
            api_msg_args = [menu]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        # bodyのjson形式チェック
        check_request_body()

        excel_data = {}
        retBool, excel_data, base64_flg = menu_excel.create_upload_parameters(connexion.request, organization_id, workspace_id)

        # メニューのカラム情報を取得
        result_data = menu_excel.execute_excel_maintenance(objdbca, organization_id, workspace_id, menu, menu_record, excel_data, base64_flg=base64_flg)
    except Exception as e:
        raise e
    finally:
        objdbca.db_disconnect()
    return result_data,
