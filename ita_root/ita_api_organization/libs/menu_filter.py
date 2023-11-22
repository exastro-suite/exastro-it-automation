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

    mode = 'count'
    objmenu = load_table.loadTable(objdbca, menu)
    if objmenu.get_objtable() is False:
        log_msg_args = ["not menu or table"]
        api_msg_args = ["not menu or table"]
        raise AppException("401-00001", log_msg_args, api_msg_args) # noqa: F405

    # MongoDB向けの処理はmodeで分岐させているため、対象のシートタイプの場合はmodeを上書き
    # 26 : MongoDBを利用するシートタイプ
    wsMongo = None
    if objmenu.get_sheet_type() == '26':
        mode = 'mongo_count'

        # MariaDBのコネクションはコントローラーで生成しているため、MongoDBも同様にすべきだが、
        # アクセスしない場合もコネクションを生成するのは無駄が多いためここで生成することにした。
        wsMongo = MONGOConnectWs()
        load_collection = loadCollection(wsMongo, objmenu)
        status_code, result, msg = load_collection.rest_filter(filter_parameter, mode)
    else:
        status_code, result, msg = objmenu.rest_filter(filter_parameter, mode)

    if status_code != '000-00000':
        log_msg_args = [msg]
        api_msg_args = [msg]
        raise AppException(status_code, log_msg_args, api_msg_args)

    return result


def rest_filter(objdbca, menu, filter_parameter):
    """
        メニューのレコード取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu: メニュー string
            filter_parameter: 検索条件  {}
            lang: 言語情報 ja / en
            mode: 本体 / 履歴
            wsMongo:DB接続クラス  MONGOConnectWs()
        RETRUN:
            statusCode, {}, msg
    """

    mode = 'nomal'
    objmenu = load_table.loadTable(objdbca, menu)
    if objmenu.get_objtable() is False:
        log_msg_args = ["not menu or table"]
        api_msg_args = ["not menu or table"]
        raise AppException("401-00001", log_msg_args, api_msg_args) # noqa: F405

    # MongoDB向けの処理はmodeで分岐させているため、対象のシートタイプの場合はmodeを上書き
    wsMongo = None
    if objmenu.get_sheet_type() == '26':
        mode = 'mongo'

        # MariaDBのコネクションはコントローラーで生成しているため、MongoDBも同様にすべきだが、
        # アクセスしない場合もコネクションを生成するのは無駄が多いためここで生成することにした。
        wsMongo = MONGOConnectWs()
        load_collection = loadCollection(wsMongo, objmenu)
        status_code, result, msg = load_collection.rest_filter(filter_parameter, mode)

    else:
        status_code, result, msg = objmenu.rest_filter(filter_parameter, mode)

    if status_code != '000-00000':
        log_msg_args = [msg]
        api_msg_args = [msg]
        raise AppException(status_code, log_msg_args, api_msg_args)

    return result


def rest_filter_journal(objdbca, menu, uuid):
    """
        メニューのレコード取得
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu: メニュー string
            filter_parameter: 検索条件  {}
            lang: 言語情報 ja / en
            mode: 本体 / 履歴
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
    status_code, result, msg = objmenu.rest_filter(filter_parameter, mode)
    if status_code != '000-00000':
        log_msg_args = [msg]
        api_msg_args = [msg]
        raise AppException(status_code, log_msg_args, api_msg_args)

    return result


def get_file_data(objdbca, menu, filter_parameter, uuid, column):
    """
        アップロードされているファイルをダウンロードする
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu: メニュー string
            uuid: uuid
            column: カラムREST名
        RETRUN:
            ファイルデータ
    """
    
    mode = 'nomal'
    objmenu = load_table.loadTable(objdbca, menu)
    if objmenu.get_objtable() is False:
        log_msg_args = ["not menu or table"]
        api_msg_args = ["not menu or table"]
        raise AppException("401-00001", log_msg_args, api_msg_args) # noqa: F405

    # MongoDB向けの処理はmodeで分岐させているため、対象のシートタイプの場合はmodeを上書き
    wsMongo = None
    if objmenu.get_sheet_type() == '26':
        mode = 'mongo'

        # MariaDBのコネクションはコントローラーで生成しているため、MongoDBも同様にすべきだが、
        # アクセスしない場合もコネクションを生成するのは無駄が多いためここで生成することにした。
        wsMongo = MONGOConnectWs()
        load_collection = loadCollection(wsMongo, objmenu)
        status_code, result, msg = load_collection.rest_filter(filter_parameter, mode)

    else:
        status_code, result, msg = objmenu.rest_filter(filter_parameter, mode)

    if status_code != '000-00000':
        log_msg_args = [msg]
        api_msg_args = [msg]
        raise AppException(status_code, log_msg_args, api_msg_args)
    
    # ファイルデータ取得
    primary_key = objmenu.get_primary_key()
    for value in result:
        if value['parameter'][primary_key.lower()] == uuid:
            result = value['file'][column]

    return result