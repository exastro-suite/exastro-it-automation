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

import os
from flask import g

from common_libs.common import *  # noqa: F403
from common_libs.common.mongoconnect.const import Const
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.loadtable import *
from common_libs.loadcollection.load_collection import loadCollection


def rest_count(objdbca, menu, filter_parameter):
    """
        メニューの件数取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu: メニュー string
            filter_parameter: 検索条件  {}
            lang: 言語情報 ja / en
            mode: 本体 / 履歴
        RETRUN:
            statusCode, {}, msg
    """
    check_filter_parameter(filter_parameter)
    mode = 'count'
    objmenu = load_table.loadTable(objdbca, menu)
    if objmenu.get_objtable() is False:
        log_msg_args = ["not menu or table"]
        api_msg_args = ["not menu or table"]
        raise AppException("401-00001", log_msg_args, api_msg_args)  # noqa: F405

    # MongoDB向けの処理はmodeで分岐させているため、対象のシートタイプの場合はmodeを上書き
    # 26 : MongoDBを利用するシートタイプ
    wsMongo = None
    if objmenu.get_sheet_type() == '26':
        mode = 'mongo_count'

        # MariaDBのコネクションはコントローラーで生成しているため、MongoDBも同様にすべきだが、
        # アクセスしない場合もコネクションを生成するのは無駄が多いためここで生成することにした。
        wsMongo = MONGOConnectWs()
        try:
            load_collection = loadCollection(wsMongo, objmenu)
            status_code, result, msg = load_collection.rest_filter(filter_parameter, mode, objdbca)
        finally:
            wsMongo.disconnect()
    else:
        status_code, result, msg = objmenu.rest_filter(filter_parameter, mode)

    if status_code != '000-00000':
        log_msg_args = [msg]
        api_msg_args = [msg]
        raise AppException(status_code, log_msg_args, api_msg_args)

    return result


def rest_filter(objdbca, menu, filter_parameter, base64_file_flg=True):
    """
        メニューのレコード取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu: メニュー string
            filter_parameter: 検索条件  {}
            base64_file_flg: ファイル有無（True:含める、False:含めない）
            wsMongo:DB接続クラス  MONGOConnectWs()
        RETRUN:
            statusCode, {}, msg
    """
    check_filter_parameter(filter_parameter)
    mode = 'nomal'
    objmenu = load_table.loadTable(objdbca, menu)
    if objmenu.get_objtable() is False:
        log_msg_args = ["not menu or table"]
        api_msg_args = ["not menu or table"]
        raise AppException("401-00001", log_msg_args, api_msg_args)  # noqa: F405

    # MongoDB向けの処理はmodeで分岐させているため、対象のシートタイプの場合はmodeを上書き
    wsMongo = None
    if objmenu.get_sheet_type() == '26':
        mode = 'mongo'

        # MariaDBのコネクションはコントローラーで生成しているため、MongoDBも同様にすべきだが、
        # アクセスしない場合もコネクションを生成するのは無駄が多いためここで生成することにした。
        wsMongo = MONGOConnectWs()
        try:
            load_collection = loadCollection(wsMongo, objmenu)
            status_code, result, msg = load_collection.rest_filter(filter_parameter, mode, objdbca)
        finally:
            wsMongo.disconnect()

    else:
        status_code, result, msg = objmenu.rest_filter(filter_parameter, mode, base64_file_flg=base64_file_flg)

    if status_code != '000-00000':
        log_msg_args = [msg]
        api_msg_args = [msg]
        raise AppException(status_code, log_msg_args, api_msg_args)

    return result


def rest_filter_journal(objdbca, menu, uuid, base64_file_flg=True):
    """
        メニューのレコード取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu: メニュー string
            uuid: uuid string
            base64_file_flg: ファイル有無（True:含める、False:含めない） boolean
        RETRUN:
            statusCode, {}, msg
    """

    objmenu = load_table.loadTable(objdbca, menu)
    if objmenu.get_objtable() is False:
        log_msg_args = ["not menu or table"]
        api_msg_args = ["not menu or table"]
        raise AppException("401-00001", log_msg_args, api_msg_args) # noqa: F405

    mode = 'jnl'
    filter_parameter = {}
    filter_parameter.setdefault('JNL', uuid)
    status_code, result, msg = objmenu.rest_filter(filter_parameter, mode, base64_file_flg=base64_file_flg)
    if status_code != '000-00000':
        log_msg_args = [msg]
        api_msg_args = [msg]
        raise AppException(status_code, log_msg_args, api_msg_args)

    return result


def get_file_path(objdbca, menu, uuid, column):
    """
        アップロードされているファイルのパスを取得する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu: メニュー string
            uuid: uuid
            column: カラムREST名
        RETRUN:
            ファイルパス
    """

    objmenu = load_table.loadTable(objdbca, menu)

    # FileUploadColumnじゃなければNone
    if objmenu.get_col_class_name(column) != 'FileUploadColumn':
        return None

    # 指定されたuuidで検索
    primary_key = objmenu.get_rest_key(objmenu.get_primary_key())
    filter_parameter = {primary_key: {'LIST': [uuid]}}
    mode = 'nomal'
    status_code, result, msg = objmenu.rest_filter(filter_parameter, mode, base64_file_flg=False)
    # レコードが無ければNone
    if len(result) == 0:
        return None

    # columnの値がなければNone
    file_name = result[0].get('parameter').get(column)
    if file_name is None:
        return None

    objcol = objmenu.get_columnclass(column)
    file_path = objcol.get_file_data_path(file_name, uuid, '', False)

    return file_path


def get_history_file_path(objdbca, menu, uuid, column, journal_uuid):
    """
        アップロードされているファイルのパスを取得する
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu: メニュー string
            uuid: uuid
            column: カラムREST名
            journal_uuid: 履歴のuuid
        RETRUN:
            ファイルパス
    """

    objmenu = load_table.loadTable(objdbca, menu)

    # FileUploadColumnじゃなければNone
    if objmenu.get_col_class_name(column) != 'FileUploadColumn':
        return None

    # 指定されたuuidで検索
    primary_key = objmenu.get_rest_key(objmenu.get_primary_key())
    filter_parameter = {'JNL': uuid}
    mode = 'jnl'
    status_code, result, msg = objmenu.rest_filter(filter_parameter, mode, base64_file_flg=False)
    # レコードが無ければNone
    if len(result) == 0:
        return None

    # 履歴テーブルがない場合はNone
    menu_info = objmenu.get_menu_info()
    if menu_info.get('MENUINFO').get('HISTORY_TABLE_FLAG') != '1':
        return None

    # 履歴データを確認
    mode = 'jnl'
    filter_parameter = {}
    filter_parameter.setdefault('JNL', uuid)
    status_code, result, msg = objmenu.rest_filter(filter_parameter, mode, base64_file_flg=False)
    if status_code != '000-00000':
        log_msg_args = [msg]
        api_msg_args = [msg]
        raise AppException(status_code, log_msg_args, api_msg_args)

    # 0件の場合はNone
    if len(result) == 0:
        return None

    # journal_datetimeの降順にソート
    jounal_list = []
    for data in result:
        jounal_list.append(data.get('parameter'))
    jounal_sort_list = sorted(jounal_list, key=lambda x: x['journal_datetime'], reverse=True)

    # 新しい順に確認してファイルパスを取得
    objcol = objmenu.get_columnclass(column)
    match_flg = False
    file_path = None
    for sort_data in jounal_sort_list:
        tmp_journal_id = sort_data.get('journal_id')
        if match_flg is True or tmp_journal_id == journal_uuid:
            match_flg = True
            if sort_data[column] is None:
                # ファイルカラムにデータが無い場合
                msg = g.appmsg.get_api_message("MSG-30026", [])
                raise AppException("499-00201", [msg], [msg])

            tmp_file_path = objcol.get_file_data_path(sort_data[column], uuid, tmp_journal_id, False)
            if os.path.isfile(tmp_file_path):
                file_path = tmp_file_path
                break
            else:
                # ファイルが存在しない場合
                raise AppException("999-00014", [tmp_file_path], [tmp_file_path])

    return file_path


def check_filter_parameter(parameter):
    """
    filter条件の簡易チェック #2534
    Args:
        parameter: {"key": "mode": filter config }
    Raises:
        AppException: 499-00201 {"no": key:[message,,,]}
    """

    if parameter:
        accept_option = ["NORMAL", "LIST", "RANGE"]
        empty_accept_option = ["NORMAL"]
        str_accept_option = ','.join(accept_option)
        i = 0
        err_msg = ""
        _err_list = {}
        for sk, scs in parameter.items():
            for sm, sc in scs.items():
                # optionの簡易チェック
                _base_msg = g.appmsg.get_api_message("MSG-00034", [str_accept_option, sm])\
                    if sm not in accept_option else ""

                # 検索条件の簡易チェック
                if sc:
                    sc = sc if isinstance(sc, list) or isinstance(sc, dict) else str(sc)
                    if len(sc) == 0 and sm in accept_option and sm not in empty_accept_option:
                        _base_msg += g.appmsg.get_api_message("MSG-00035", [json.dumps(sc)])
                elif sm in accept_option and sm not in empty_accept_option:
                    _base_msg += g.appmsg.get_api_message("MSG-00035", [json.dumps(sc)])

                # エラーメッセージ設定
                if len(_base_msg) != 0:
                    _base_msg.rstrip()
                    _err_list.setdefault(f"{i}", {})
                    _err_list[f"{i}"].setdefault(sk, [])
                    _err_list[f"{i}"][sk].append(f"{_base_msg}")
                    i += 1

        if len(_err_list) != 0:
            err_msg = json.dumps(_err_list, ensure_ascii=False)
            status_code = '499-00201'
            log_msg_args = [err_msg]
            api_msg_args = [err_msg]
            raise AppException(status_code, log_msg_args, api_msg_args)

