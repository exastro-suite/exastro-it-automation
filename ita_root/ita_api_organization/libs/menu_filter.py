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
import json
from flask import g

from common_libs.common import *  # noqa: F403
from common_libs.common.mongoconnect.const import Const
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.loadtable import *
from common_libs.loadcollection.load_collection import loadCollection
from libs.export_import import check_export_menu_permission, check_import_menu_permission, get_denied_menu_rest_set

# 処理種別（T_DP_EXECUTION_TYPE.ROW_ID）: インポート
EXECUTION_TYPE_IMPORT = '2'


def _check_export_download_permission(objdbca, objmenu, menu, record_id, journal_uuid=None):
    """
        エクスポート管理メニューのファイルダウンロード時の権限チェック

        ARGS:
            objdbca: DB接続クラス DBConnectWs()
            objmenu: メニューオブジェクト
            menu: メニュー名 string
            record_id: レコードのプライマリキー値 string
            journal_uuid: 履歴のJOURNAL_SEQ_NO (履歴の場合のみ) string or None

        RETURN:
            なし（権限がない場合は例外を発生）
    """
    # ログラベル（通常 or 履歴）
    log_label = "Download Permission Check (History)" if journal_uuid else "Download Permission Check"
    log_context = f"record_id={record_id}, journal_uuid={journal_uuid}, menu={menu}" if journal_uuid else f"record_id={record_id}, menu={menu}"

    # DBから直接 json_storage_item を取得
    table_name = objmenu.get_table_name()
    primary_key = objmenu.get_primary_key()

    if journal_uuid:
        # 履歴テーブルから取得
        history_table_name = table_name + '_JNL'
        ret = objdbca.table_select(history_table_name, 'WHERE JOURNAL_SEQ_NO = %s', [journal_uuid])
    else:
        # 通常テーブルから取得（プライマリキーを動的に使用、廃止済みレコードも対象）
        ret = objdbca.table_select(table_name, f'WHERE {primary_key} = %s', [record_id])

    if len(ret) == 0:
        menu_list, reason = None, "Record not found"
    else:
        menu_list, reason = _get_export_record_menu_list(ret[0])

    if menu_list is None:
        # 対象メニューを特定できない場合はエラー
        g.applogger.error(f"[{log_label}] {reason}: {log_context}")
        msg = g.appmsg.get_api_message("MSG-30038", [])
        raise AppException("499-00201", [msg], [msg])

    if str(ret[0].get('EXECUTION_TYPE')) == EXECUTION_TYPE_IMPORT:
        # インポート実行時と同じ条件でチェック（EXPORT_PERMISSION_CHECK_FLG を考慮）
        check_import_menu_permission(objdbca, menu_list)
    else:
        # エクスポート対象メニューへの書き込み権限をチェック（EXPORT_PERMISSION_CHECK_FLG を考慮）
        check_export_menu_permission(objdbca, menu_list)


def _get_export_record_menu_list(record):
    """
        エクスポート管理メニューのレコードから、エクスポート・インポート対象メニューを取得する

        ARGS:
            record: T_MENU_EXPORT_IMPORT(_JNL) のレコード dict
        RETURN:
            (メニューRESTIDリスト, None) または 特定できない場合 (None, 理由)
    """
    json_storage_item = record.get('JSON_STORAGE_ITEM')
    if not json_storage_item:
        return None, "json_storage_item is empty"

    if str(record.get('EXECUTION_TYPE')) == EXECUTION_TYPE_IMPORT:
        # インポート: json_storage_item はメニューRESTIDのカンマ区切り
        menu_list = [menu_rest for menu_rest in json_storage_item.split(',') if menu_rest]
    else:
        # エクスポート: json_storage_item はリクエストボディのJSON
        try:
            storage_data = json.loads(json_storage_item)
        except json.JSONDecodeError as e:
            return None, f"Failed to parse json_storage_item, error={str(e)}"
        menu_list = storage_data.get('menu', []) if isinstance(storage_data, dict) else []

    if not menu_list:
        return None, "menu list is empty"

    return menu_list, None


def _mask_export_file_data(objdbca, objmenu, result, journal=False):
    """
        エクスポート管理メニューのレコード取得時、書き込み権限のないメニューを含むレコードのファイルデータを除外する
        （ファイルダウンロード時の権限チェックと同じ条件）

        ARGS:
            objdbca: DB接続クラス DBConnectWs()
            objmenu: メニューオブジェクト
            result: rest_filter の結果 [{'parameter': {}, 'file': {}}] (直接書き換える)
            journal: 履歴の場合 True
        RETURN:
            なし
    """
    if not result:
        return

    table_name = objmenu.get_table_name()
    if journal:
        table_name = table_name + '_JNL'
        key_col = 'JOURNAL_SEQ_NO'
        key_rest = 'journal_id'
    else:
        key_col = objmenu.get_primary_key()
        key_rest = objmenu.get_rest_key(key_col)

    record_id_list = [item.get('parameter', {}).get(key_rest) for item in result]
    ret = objdbca.table_select(table_name, f'WHERE {key_col} IN %s', [record_id_list])

    # レコードごとの対象メニュー（特定できない場合は None）
    record_menu_map = {}
    for record in ret:
        menu_list, reason = _get_export_record_menu_list(record)
        if menu_list is None:
            g.applogger.info(f"[Filter Permission Check] {reason}: record_id={record.get(key_col)}")
        record_menu_map[str(record.get(key_col))] = menu_list

    # 全レコードの対象メニューをまとめて権限チェック
    all_menu_list = list({menu_rest for menu_list in record_menu_map.values() if menu_list for menu_rest in menu_list})
    denied_menu_set = get_denied_menu_rest_set(objdbca, all_menu_list)

    for item in result:
        record_id = str(item.get('parameter', {}).get(key_rest))
        menu_list = record_menu_map.get(record_id)
        if menu_list is None or any(menu_rest in denied_menu_set for menu_rest in menu_list):
            # file=no 指定時と同じ形式にする
            item['file'] = {}


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

    # エクスポート管理メニューの場合、書き込み権限のないメニューを含むレコードのファイルデータを除外
    if menu == 'menu_export_import_list' and base64_file_flg:
        _mask_export_file_data(objdbca, objmenu, result)

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

    # エクスポート管理メニューの場合、書き込み権限のないメニューを含むレコードのファイルデータを除外
    if menu == 'menu_export_import_list' and base64_file_flg:
        _mask_export_file_data(objdbca, objmenu, result, journal=True)

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

    # エクスポート管理メニューの場合、エクスポート対象メニューへの書き込み権限をチェック
    # Excel一括エクスポートは閲覧権限でエクスポート可能なため対象外
    if menu == 'menu_export_import_list':
        _check_export_download_permission(objdbca, objmenu, menu, uuid)

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

    # エクスポート管理メニューの場合、エクスポート対象メニューへの書き込み権限をチェック
    # Excel一括エクスポートは閲覧権限でエクスポート可能なため対象外
    if menu == 'menu_export_import_list':
        _check_export_download_permission(objdbca, objmenu, menu, uuid, journal_uuid)

    # journal_datetimeの降順にソート
    jounal_list = []
    for data in result:
        jounal_list.append(data.get('parameter'))
    jounal_sort_list = sorted(jounal_list, key=lambda x: x['journal_datetime'], reverse=True)

    # 新しい順に確認してファイルパスを取得
    objcol = objmenu.get_columnclass(column)
    match_flg = False
    file_path = None
    file_name = ""
    for index, sort_data in enumerate(jounal_sort_list):
        tmp_journal_id = sort_data.get('journal_id')
        if match_flg is True or tmp_journal_id == journal_uuid:

            if match_flg is False:
                file_name = sort_data[column]

            # 連続する同名ファイルに実体がない場合はシステムエラー
            if file_name != sort_data[column]:
                raise AppException("999-00014", [tmp_file_path], [tmp_file_path])

            # ファイルパス取得
            tmp_file_path = objcol.get_file_data_path(sort_data[column], uuid, tmp_journal_id, False)

            match_flg = True
            if sort_data[column] is None:
                # ファイルカラムにデータが無い場合
                msg = g.appmsg.get_api_message("MSG-30026", [])
                raise AppException("499-00201", [msg], [msg])

            # 対象のファイルが見つかった場合はループを抜ける
            if os.path.isfile(tmp_file_path):
                file_path = tmp_file_path
                break

            # 履歴の最後のレコードまでファイルの実体が無い場合はシステムエラー
            elif index == len(jounal_sort_list) - 1:
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

