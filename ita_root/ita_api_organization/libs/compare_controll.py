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


from flask import g  # noqa: F401

from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from common_libs.column import *  # noqa: F403

import uuid  # noqa: F401
import textwrap
import sys
import traceback
from distutils.util import strtobool
import mimetypes
import base64
import re

import deepdiff
import dictdiffer
import difflib

"""
TASK
"""


# 比較実行画面用情報取得(リスト情報、パラメータフォーマット)
def get_compares_data(objdbca, menu):
    """
        get compares data
        ARGS:
        RETRUN:
            {
                "list":{"compare":[],"host":[]},
                "dict":{"compare":{},"host":{}},
                "parameter_base_format":{}
                "file_compare_parameter_format":{}
            }
    """

    # get base parameter fromat
    compare_parameter_format, file_compare_parameter_format = _get_base_parameter()

    # set result
    result = {}
    result.setdefault("list", {})
    result.setdefault("dict", {})
    result.setdefault("execute_parameter_format", {})
    result["execute_parameter_format"].setdefault("compare", compare_parameter_format)
    result["execute_parameter_format"].setdefault("file", compare_parameter_format)
    result["list"].setdefault("compare", [])
    result["dict"].setdefault("compare", {})

    # get compare , menu
    table_name = "T_COMPARE_CONFG_LIST"
    where_str = "WHERE DISUSE_FLAG <> 1 ORDER BY COMPARE_NAME ASC "
    bind_list = []

    rows = objdbca.table_select(table_name, where_str, bind_list)

    taget_menu_ids = []
    for row in rows:
        tmp_id = row.get("COMPARE_ID")
        tmp_name = row.get("COMPARE_NAME")
        result["list"]["compare"].append(tmp_name)
        result["dict"]["compare"].setdefault(tmp_id, tmp_name)
        menu_id_1 = row.get("TARGET_MENU_1")
        menu_id_2 = row.get("TARGET_MENU_2")
        taget_menu_ids.append(menu_id_1)
        taget_menu_ids.append(menu_id_2)

    taget_menu_ids = list(set(taget_menu_ids))

    # get table_name
    sql_str = ""
    bind_list = []
    list_sql = []
    for taget_menu_id in taget_menu_ids:
        tmp_sql_str = " SELECT * FROM `T_COMN_MENU_TABLE_LINK` WHERE `DISUSE_FLAG` <> 1 AND `MENU_ID` = %s "
        list_sql.append(tmp_sql_str)
        bind_list.append(taget_menu_id)

    sql_str = " UNION ".join([str(tmp_sql) for tmp_sql in list_sql])
    rows = objdbca.sql_execute(sql_str, bind_list)
    table_names = []
    for row in rows:
        table_name = row.get("TABLE_NAME")
        table_names.append(table_name)

    # get host list
    sql_str = ""
    bind_list = []
    list_sql = []
    for table_name in table_names:
        tmp_sql_str = textwrap.dedent("""
            SELECT
                `TAB_A`.`HOST_ID`,
                `TAB_B`.`HOST_NAME`
            FROM
                `{table_name}` `TAB_A`
            LEFT JOIN `T_ANSC_DEVICE` `TAB_B` ON ( `TAB_A`.`HOST_ID` = `TAB_B`.`SYSTEM_ID` )
            WHERE `TAB_A`.`DISUSE_FLAG` <> 1
            AND `TAB_B`.`DISUSE_FLAG` <> 1
        """).format(table_name=table_name).strip()
        list_sql.append(tmp_sql_str)

    sql_str = " UNION ".join([str(tmp_sql) for tmp_sql in list_sql])

    # set result host data
    rows = objdbca.sql_execute(sql_str, bind_list)
    host_ids = []
    result["dict"].setdefault("host", {})
    for row in rows:
        tmp_id = row.get("HOST_ID")
        tmp_name = row.get("HOST_NAME")
        host_ids.append(tmp_name)
        result["dict"]["host"].setdefault(tmp_id, tmp_name)

    host_ids = list(set(host_ids))
    host_ids.sort()
    result["list"].setdefault("host", host_ids)

    return result


# 比較実行
def compare_execute(objdbca, menu, parameter, options={}):
    """
        compare_execute
        ARGS:
            parameter = {
                "compare": "",
                "base_date_1": "",
                "base_date_2": "",
                "host": [],
                "other_options": {}
            }
            options={}
        RETRUN:
            {"config":{},"compare_data":{},"compare_diff_flg":{}}
    """
    try:

        # set base config
        compare_config = _set_base_config(parameter)

        # parameter chk
        retBool, compare_config = _chk_parameters(objdbca, compare_config, options)
        if retBool is False:
            tmp_msg = _get_msg(compare_config, "parameter_error")
            status_code = "499-01001"
            log_msg_args = [tmp_msg]
            api_msg_args = [tmp_msg]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        # set compare mode , parameter format
        compare_config = _set_compare_mode(compare_config, options)

        # set input order lang
        compare_config = _set_input_order_lang(compare_config, options)

        # get compare config
        retBool, compare_config = _set_compare_config_info(objdbca, compare_config, options)
        if retBool is False:
            tmp_msg = _get_msg(compare_config, "compare_config")
            status_code = "499-01002"
            log_msg_args = [tmp_msg]
            api_msg_args = [tmp_msg]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        # get data
        retBool, compare_config = _get_target_datas(objdbca, compare_config, options)
        if retBool is False:
            tmp_msg = _get_msg(compare_config, "compare_target_menu_error")
            status_code = "499-01004"
            log_msg_args = [tmp_msg]
            api_msg_args = [tmp_msg]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        # compare data execute
        retBool, compare_config = _execute_compare_data(objdbca, compare_config, options)
        if retBool is False:
            tmp_msg = _get_msg(compare_config, "execute_compare")
            status_code = "499-01005"
            log_msg_args = [tmp_msg]
            api_msg_args = [tmp_msg]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        compare_mode = _get_flg(compare_config, "compare_mode")

        # override_column_info_vertical_ver  item1 -> item[input_order:1]
        vertical_compare_flg = _get_flg(compare_config, "vertical_compare_flg")
        if vertical_compare_flg is True:
            retBool, compare_config = _override_column_info_vertical_ver(objdbca, compare_config, options)

        # set return
        result = {}
        result.setdefault("config", {})
        if compare_mode == "normal":
            result.setdefault("compare_data", {})
            result.setdefault("compare_diff_flg", {})
            # set result->config
            result["config"].setdefault("target_menus_rest", list(compare_config.get("target_menus").values()))
            result["config"].setdefault("target_menus", list(compare_config.get("target_menus_lang").values()))
            result["config"].setdefault("target_host_list", compare_config.get("target_host_list"))
            result["config"].setdefault("target_column_info", compare_config.get("column_info"))
            result["config"].setdefault("compare_file", _get_flg(compare_config, "compare_file"))
            # set result->compare_diff_flg
            result["compare_diff_flg"] = compare_config.get("result_compare_host")
            # set result->compare_data
            result["compare_data"] = compare_config.get("compare_data_ptn1")

        else:
            # set result->config
            result["config"].setdefault("target_compare_file_info", compare_config.get("target_compare_file_info"))
            result["config"].setdefault("compare_file", _get_flg(compare_config, "compare_file"))
            # set result->unified_diff
            result.setdefault("unified_diff", {})
            result["unified_diff"] = compare_config.get("unified_diff")

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "execute_compare_error", True)
        retBool = False

    return result


# 比較パラメータフォーマット取得
def _get_base_parameter():
    """
        get base parameter
        ARGS:
        RETRUN:
            compare_parameter_format, file_compare_parameter_format
    """
    # base format compare / file compare
    compare_parameter_format = {
        "compare": "",
        "base_date_1": "",
        "base_date_2": "",
        "host": [],
        # "other_options": {}
    }
    file_compare_parameter_format = {
        "compare": "",
        "base_date_1": "",
        "base_date_2": "",
        "host": "",
        "copmare_target_column": "",
        # "other_options": {}
    }
    return compare_parameter_format, file_compare_parameter_format


# config初期設定
def _set_base_config(parameter):
    """
        set base config [caller:compare_execute]
        ARGS:
            parameter
            mode: normal, file
        RETRUN:
            {}
    """

    # not use rest_key
    accept_compare_file_list = [
        "text/plain",
        "application/json",
        "text/csv",
        "text/html",
        "text/javascript",
        "application/ld+json",
    ]

    # not use rest_key
    del_parameter_list = [
        # "uuid",
        # "host_name",
        "operation_name_select",
        # "operation_name_disp",
        # "base_datetime",
        "operation_date",
        "last_execute_timestamp",
        "remarks",
        "discard",
        "last_update_date_time",
        "last_updated_user",
    ]

    # not use rest_key
    no_compare_parameter_list = [
        "menu",
        "uuid",
        "host_name",
        "operation_name_select",
        "operation_name_disp",
        "base_datetime",
        "operation_date",
        "input_order",
        "last_execute_timestamp",
        "remarks",
        "discard",
        "last_update_date_time",
        "last_updated_user",
    ]

    # no_input_order_list
    no_input_order_list = [
        "menu",
        "uuid",
        "host_name",
        "operation_name_select",
        "operation_name_disp",
        "base_datetime",
        "operation_date",
        "input_order",
        "last_execute_timestamp",
        "remarks",
        "discard",
        "last_update_date_time",
        "last_updated_user",
    ]

    # not use rest_key
    vertical_no_use_rest_key = [
        "uuid",
        "operation_name_select",
        "operation_name_disp",
        "base_datetime",
        "operation_date",
        "input_order",
        "last_execute_timestamp",
        "remarks",
        "discard",
        "last_update_date_time",
        "last_updated_user",
    ]

    input_order_langs = {
        "ja": "代入順序",
        "en:": "Input order"
    }

    compare_config = {}

    # parameter設定
    compare_config.setdefault("parameter", parameter)
    # LANGUAGE
    compare_config.setdefault("language", g.get('LANGUAGE'))
    # flg管理
    compare_config.setdefault("_flg_data", {})
    # 比較設定
    compare_config.setdefault("config_compare_list", {})
    # 比較設定詳細
    compare_config.setdefault("config_compare_detail", {})
    # 表示項目順LIST
    compare_config.setdefault("config_compare_disp", [])
    # 項目詳細(表示項目、紐付、カラムクラス等)
    compare_config.setdefault("column_info", {})
    # 比較元データ {"HOST":{"INPUT_ORDER":{"menu_1":{},"menu_2":{}}}}
    compare_config.setdefault("origin_data", {})
    # ホスト一覧(比較元データ)
    compare_config.setdefault("target_host_list", [])
    # 対象メニュー情報 {"menu_1":{"menu_name",,,},"menu_2":{"menu_name",,,}}
    compare_config.setdefault("target_menu_info", {})
    # 対象メニュー {"menu_1":"rest_name","menu_2":"rest_name"}
    compare_config.setdefault("target_menus", {"menu_1": "", "menu_2": ""})
    # 対象メニュー {"menu_1":"rest_name","menu_2":"rest_name"}
    compare_config.setdefault("target_menus_lang", {"menu_1": "", "menu_2": ""})
    # 代入順序リスト {"menu_1":[],"menu_2":[]}
    compare_config.setdefault("input_order_list", [])
    # 対象メニューobjtable　{"menu_1": objtable, "menu_2": objtable}
    compare_config.setdefault("objtable", {})
    # 比較結果(ホスト毎)
    compare_config.setdefault("result_compare_host", {})
    # 比較対象データ無し時の項目補完用 {"menu_1":{"key_name":None},"menu_2":{"key_name":None}}
    compare_config.setdefault("base_parameter", {})
    compare_config.setdefault("base_parameter_all", {})
    # ファイル比較対象結果(unified_diff)
    compare_config.setdefault("unified_diff", {"file_data": {}, "diff_result": {}})
    # 不要項目リスト(rest_key)
    compare_config.setdefault("del_parameter_list", del_parameter_list)
    # 比較対象外項目リスト(rest_key+menu)
    compare_config.setdefault("no_compare_parameter_list", no_compare_parameter_list)
    # 縦型比較不要項目リスト
    compare_config.setdefault("vertical_no_use_rest_key", vertical_no_use_rest_key)
    # ファイル比較対象(mimetype)
    compare_config.setdefault("accept_compare_file_list", accept_compare_file_list)
    # 代入順序対象外リスト
    compare_config.setdefault("no_input_order_list", no_input_order_list)
    # 代入順序表示用言語
    compare_config.setdefault("input_order_langs", input_order_langs)
    # 代入順序付き項目用の代入順序
    compare_config.setdefault("input_order_lang", None)

    return compare_config


# 比較種別、対応フォーマット設定
def _set_compare_mode(compare_config, options):
    """
        set compare mode  [caller:compare_execute]
        ARGS:
            compare_config, flg_key, flg_val
        RETRUN:
            compare_config
    """
    # get parameter
    parameter = compare_config.get("parameter")
    # get base parameter format
    compare_parameter_format, file_compare_parameter_format = _get_base_parameter()

    # compare mode set parameter format marge
    compare_mode = options.get("compare_mode")
    if compare_mode == "normal":
        base_parameter = compare_parameter_format
    elif compare_mode == "file":
        base_parameter = file_compare_parameter_format
        tmp_parameter = compare_config.get("parameter")
        copmare_target_column = tmp_parameter.get("copmare_target_column")
        compare_config["copmare_target_column"] = copmare_target_column
    else:
        compare_mode = "normal"
        base_parameter = compare_parameter_format
    base_parameter.update(parameter)

    # set compare mode
    compare_config = _set_flg(compare_config, "compare_mode", compare_mode)
    # set parameter
    compare_config["parameter"] = base_parameter

    return compare_config


# 代入順序表示名設定
def _set_input_order_lang(compare_config, options):
    """
        set input order lang  [caller:compare_execute]
        ARGS:
            compare_config, options
        RETRUN:
            compare_config
    """
    # get language
    language = compare_config.get("language")

    # get input_order_lang
    input_order_langs = compare_config.get("input_order_langs")
    input_order_lang = input_order_langs.get(language)

    input_order_lang = None

    # set input_order_lang
    compare_config["input_order_lang"] = input_order_lang

    return compare_config


# flg管理 設定 _flg_data
def _set_flg(compare_config, flg_key, flg_val):
    """
        set flg
        ARGS:
            compare_config, flg_key, flg_val
        RETRUN:
            compare_config
    """
    compare_config.setdefault("_flg_data", {})
    if flg_key not in compare_config["_flg_data"]:
        compare_config["_flg_data"].setdefault(flg_key, flg_val)
    else:
        compare_config["_flg_data"][flg_key] = flg_val
    return compare_config


# flg管理 取得 _flg_data
def _get_flg(compare_config, flg_key):
    """
        get flg
        ARGS:
            compare_config, flg_key
        RETRUN:
            flg_val
    """
    flg_val = None
    compare_config.setdefault("_flg_data", {})
    if flg_key in compare_config["_flg_data"]:
        flg_val = compare_config["_flg_data"][flg_key]
    return flg_val


# msg管理 設定 _msg
def _set_msg(compare_config, key, msg):
    """
        set msg
        ARGS:
            compare_config, key, msg
        RETRUN:
            compare_config
    """
    compare_config.setdefault("_msg", {})
    if key not in compare_config["_msg"]:
        compare_config["_msg"].setdefault(key, [])
    compare_config["_msg"][key].append(msg)
    return compare_config


# msg管理 取得 _msg
def _get_msg(compare_config, key):
    """
        get msg
        ARGS:
            compare_config, key
        RETRUN:
            msg
    """
    msg = []
    compare_config.setdefault("_msg", {})
    if key in compare_config["_msg"]:
        msg = compare_config["_msg"][key]
    return msg


# 比較実行処理
def _execute_compare_data(objdbca, compare_config, options):
    """
        execute compare data  [caller:compare_execute]
        ARGS:
            objdbca, compare_config, options
        RETRUN:
            {}
    """
    retBool = True

    try:
        # get column_info
        column_info = compare_config.get("column_info")
        # get origin_data
        origin_data = compare_config.get("origin_data")
        # get compare_mode  normal / file
        compare_mode = _get_flg(compare_config, "compare_mode")
        # get copmare_target_column
        copmare_target_column = compare_config.get("copmare_target_column")
        target_menus = compare_config.get("target_menus_lang")
        # get vertical_compare_flg
        vertical_compare_flg = _get_flg(compare_config, "vertical_compare_flg")

        input_order_lang = compare_config.get("input_order_lang")

        result_ptn1 = {}

        menu_name_1 = target_menus.get("menu_1")
        menu_name_2 = target_menus.get("menu_2")

        # for target host
        for target_host in list(origin_data.keys()):

            target_data_1 = {}
            target_data_2 = {}
            diff_flg_data = {}
            diff_flg_file = {}
            file_compare_info = {}
            origin_data[target_host].setdefault("__no_input_order__", {"menu_1": {}, "menu_2": {}})
            origin_data[target_host]["__no_input_order__"]["menu_1"].setdefault("menu", menu_name_1)
            origin_data[target_host]["__no_input_order__"]["menu_2"].setdefault("menu", menu_name_2)

            # target col
            for tmp_info in column_info:
                file_mimetypes = {}
                other_options = {}
                tmp_file_compare_info = {}

                # set target data
                menu_1_data = {}
                target_uuid_1 = None
                col_val_menu_1 = None
                base_datetime_1 = None
                operation_name_disp_1 = None
                menu_2_data = {}
                target_uuid_2 = None
                col_val_menu_2 = None
                base_datetime_2 = None
                operation_name_disp_2 = None

                # get col name
                col_name = tmp_info.get("col_name")

                # compare target flg
                compare_target_flg = tmp_info.get("compare_target_flg")
                # compare file flg
                file_flg = tmp_info.get("file_flg")
                # no_input_order_flg
                no_input_order_flg = tmp_info.get("no_input_order_flg")

                # menu rest_name
                col_name_menu_1 = tmp_info.get("menu_1")
                col_name_menu_2 = tmp_info.get("menu_2")
                # menu columnclass
                column_class_name_1 = tmp_info.get("column_class_1")
                column_class_name_2 = tmp_info.get("column_class_2")

                # check target column
                target_column_flg = _chk_target_column_flg(copmare_target_column, col_name)

                # target vertical menu
                if vertical_compare_flg is True:
                    input_orders = list(origin_data[target_host].keys())
                    input_orders = list(set(input_orders))
                    # get target input order :column item_1[x] -> x
                    try:
                        copmare_target_column_io = re.findall(r'\[.*\]', copmare_target_column)
                        copmare_target_column_io = copmare_target_column_io[0].replace('[', '').replace(']', '')
                        input_orders = [int(copmare_target_column_io)]
                        target_column_flg = True
                    except Exception:
                        copmare_target_column_io = None
                else:
                    input_orders = ["__no_input_order__"]

                # target filter
                if target_column_flg is True:
                    for tmp_order in input_orders:
                        file_mimetypes = {}
                        other_options = {}
                        tmp_file_compare_info = {}

                        input_order_1 = tmp_order
                        input_order_2 = tmp_order
                        tmp_col_name = "{}".format(col_name)

                        # get target menu data -> uuid value base_datetime operation_name_disp
                        menu_1_data, target_uuid_1, col_val_menu_1, base_datetime_1, operation_name_disp_1 = \
                            _get_line_values("menu_1", origin_data, target_host, input_order_1, col_name_menu_1)
                        menu_2_data, target_uuid_2, col_val_menu_2, base_datetime_2, operation_name_disp_2 = \
                            _get_line_values("menu_2", origin_data, target_host, input_order_2, col_name_menu_2)

                        # vertical menu and comare target parameters
                        tmp_col_name = _override_col_name_io(
                            col_name,
                            tmp_col_name,
                            tmp_order,
                            input_order_lang,
                            no_input_order_flg,
                            vertical_compare_flg
                        )

                        # check target colname
                        if tmp_col_name is not None:
                            # set target key->value
                            target_data_1.setdefault(tmp_col_name, col_val_menu_1)
                            target_data_2.setdefault(tmp_col_name, col_val_menu_2)

                            # get file data
                            if file_flg is True:
                                # get file compare resut: file_compare_info, diff_flg_file
                                compare_config, tmp_file_compare_info, diff_flg_file = _get_compare_file_result(
                                    objdbca,
                                    compare_config,
                                    diff_flg_file,
                                    file_mimetypes,
                                    target_host,
                                    tmp_col_name,
                                    compare_target_flg,
                                    dict_menu1={
                                        "col_name_menu": col_name_menu_1,
                                        "target_uuid": target_uuid_1,
                                        "col_val_menu": col_val_menu_1,
                                        "column_class_name": column_class_name_1,
                                        "operation_name_disp": operation_name_disp_1,
                                        "base_datetime": base_datetime_1,
                                    },
                                    dict_menu2={
                                        "col_name_menu": col_name_menu_2,
                                        "target_uuid": target_uuid_2,
                                        "col_val_menu": col_val_menu_2,
                                        "column_class_name": column_class_name_2,
                                        "operation_name_disp": operation_name_disp_2,
                                        "base_datetime": base_datetime_2,
                                    }
                                )
                            else:
                                diff_flg_file.setdefault(tmp_col_name, False)

                            # set tmp_file_compare_info
                            file_compare_info.setdefault(tmp_col_name, tmp_file_compare_info)
                            other_options.setdefault("file_compare_info", tmp_file_compare_info)

            if compare_mode == "normal":
                # diff 全体
                result_ddiff = deepdiff.DeepDiff(target_data_1, target_data_2)
                result_dictdiffer = list(dictdiffer.diff(target_data_1, target_data_2))
                tmp_compare_result = False
                if len(result_ddiff) != 0:
                    tmp_compare_result = True
                compare_config["result_compare_host"].setdefault(target_host, tmp_compare_result)

                # get target rest_key
                target_data_key = list(target_data_1.keys())
                target_data_key.extend(list(target_data_2.keys()))
                diff_key = [i1 for i0, i1, i2 in result_dictdiffer]

                # set diff flg[value]
                for tmp_key in target_data_key:
                    diff_flg = False
                    if tmp_key in diff_key:
                        diff_flg = True
                    diff_flg_data.setdefault(tmp_key, diff_flg)

                # set result_ptn1
                # {
                #   host_name:{
                #    "target_data_1":{},
                #    "target_data_2":{},
                #    "compare_diff_flg":{},
                #    "_data_diff_flg":{},
                #    "_file_compare_execute_flg":{},
                #    "_file_compare_execute_info":{}
                #    }
                # }
                result_ptn1.setdefault(target_host, {})
                result_ptn1[target_host].setdefault("target_data_1", target_data_1)
                result_ptn1[target_host].setdefault("target_data_2", target_data_2)
                result_ptn1[target_host].setdefault("compare_diff_flg", tmp_compare_result)
                result_ptn1[target_host].setdefault("_data_diff_flg", diff_flg_data)
                result_ptn1[target_host].setdefault("_file_compare_execute_flg", diff_flg_file)
                result_ptn1[target_host].setdefault("_file_compare_execute_info", file_compare_info)
                compare_config["compare_data_ptn1"] = result_ptn1

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "execute_compare_error", True)
        retBool = False

    return retBool, compare_config,


# 比較対象項目判定
def _chk_target_column_flg(copmare_target_column, col_name):
    """
        check compare target
        ARGS:
            copmare_target_column, col_name,
        RETRUN:
            bool
    """
    target_column_flg = True
    if copmare_target_column is None:
        pass
    elif col_name == copmare_target_column:
        pass
    else:
        target_column_flg = False
    return target_column_flg


# 値の比較判定
def _chk_value_compare_flg(compare_target_flg, col_val_menu_1, col_val_menu_2):
    """
        check compare value
        ARGS:
            compare_target_flg, col_val_menu_1, col_val_menu_2
        RETRUN:
            bool
    """
    value_compare_flg = False
    if compare_target_flg is True:
        if col_val_menu_1 != col_val_menu_2:
            value_compare_flg = True
        else:
            value_compare_flg = False
    else:
        value_compare_flg = False
    return value_compare_flg


# 比較対象関連の情報取得[対象行,ID,値,基準日,オペレーション]
def _get_line_values(target_key, origin_data, target_host, input_order, col_name_menu):
    """
        get compare data for target menu line
        ARGS:
            target_key, origin_data, target_host, input_order, col_name_menu
        RETRUN:
            menu_data, target_uuid, col_val_menu, base_datetime, operation_name_disp
    """
    menu_data = {}
    target_uuid = None
    col_val_menu = None
    base_datetime = None
    operation_name_disp = None
    try:
        menu_data = origin_data[target_host][input_order].get(target_key)
        target_uuid = menu_data.get("uuid")
        col_val_menu = menu_data.get(col_name_menu)
        base_datetime = menu_data.get("base_datetime")
        operation_name_disp = menu_data.get("operation_name_disp")
    except Exception:
        pass
    return menu_data, target_uuid, col_val_menu, base_datetime, operation_name_disp,


# ファイル比較結果(string:unified形式)
def _get_unified_diff(accept_compare_file_list, filename_1, filename_2, mimetype_1, mimetype_2, data_1, data_2):
    """
        get unified diff data: format string
        ARGS:
            accept_compare_file_list, filename_1, filename_2, mimetype_1, mimetype_2, data_1, data_2
        RETRUN:
            str_diff
    """
    str_rdiff = ""
    if mimetype_1 in accept_compare_file_list and mimetype_2 in accept_compare_file_list:
        try:
            data_1_dec = base64.b64decode(data_1.encode()).decode().split()
            data_2_dec = base64.b64decode(data_2.encode()).decode().split()
        except Exception:
            # read file is faild
            status_code = "499-01006"
            log_msg_args = [filename_1, filename_2]
            api_msg_args = [filename_1, filename_2]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        rdiff = difflib.unified_diff(
            data_1_dec,
            data_2_dec,
            filename_1,
            filename_2,
            lineterm='')
        str_rdiff = '\n'.join(rdiff)
    return str_rdiff


# 縦型メニュー項目名:代入順序入り変換上書き
def _override_col_name_io(col_name, col_name_io, input_order, input_order_lang, no_input_order_flg, vertical_compare_flg):
    """
        override col_name add input_order
        ARGS:
            col_name, col_name_io, input_order, no_input_order_flg, vertical_compare_flg
        RETRUN:
            col_name_io
    """
    if input_order != "__no_input_order__" and no_input_order_flg is False:
        col_name_io = "{}[{}]".format(col_name, input_order)
        col_name_io = _get_col_name_input_order(col_name, input_order, input_order_lang)
    else:
        # vertical menu no use target colname: tmp_col_name->None
        if no_input_order_flg is False and vertical_compare_flg is True:
            col_name_io = None
    return col_name_io


# ファイル比較結果のフラグ、詳細
def _get_compare_file_result(objdbca, compare_config, diff_flg_file, file_mimetypes, target_host, tmp_col_name, target_flg, dict_menu1, dict_menu2):
    """
        get compare file file_compare_info and set diff_flg_file
        ARGS:
            objdbca, compare_config, diff_flg_file, file_mimetypes, target_host, tmp_col_name, target_flg, dict_menu1, dict_menu2
        RETRUN:
            compare_config, tmp_file_compare_info, diff_flg_file
    """
    # objtable
    objtable_1 = compare_config["objtable"]["menu_1"]
    objtable_2 = compare_config["objtable"]["menu_2"]

    compare_mode = _get_flg(compare_config, "compare_mode")
    accept_compare_file_list = compare_config.get("accept_compare_file_list")
    tmp_file_data_1 = None
    tmp_file_data_2 = None
    tmp_file_mimetype_1 = None
    tmp_file_mimetype_2 = None
    col_val_menu_1 = dict_menu1.get("col_val_menu")
    col_name_menu_1 = dict_menu1.get("col_name_menu")
    target_uuid_1 = dict_menu1.get("target_uuid")
    column_class_name_1 = dict_menu1.get("column_class_name")
    operation_name_disp_1 = dict_menu1.get("operation_name_disp")
    base_datetime_1 = dict_menu1.get("base_datetime")

    col_val_menu_2 = dict_menu2.get("col_val_menu")
    col_name_menu_2 = dict_menu2.get("col_name_menu")
    target_uuid_2 = dict_menu2.get("target_uuid")
    column_class_name_2 = dict_menu2.get("column_class_name")
    operation_name_disp_2 = dict_menu2.get("operation_name_disp")
    base_datetime_2 = dict_menu2.get("base_datetime")

    file_mimetypes.setdefault(tmp_col_name, {"target_data_1": {}, "target_data_2": {}})

    # compare result[value]
    value_compare_flg = _chk_value_compare_flg(target_flg, col_val_menu_1, col_val_menu_2)

    # get file base64 string  file mimetype
    if col_val_menu_1 is not None:
        tmp_file_data_1, tmp_file_mimetype_1 = _get_file_data_columnclass(
            objdbca,
            objtable_1,
            col_name_menu_1,
            col_val_menu_1,
            target_uuid_1,
            column_class_name_1)
        file_mimetypes[tmp_col_name]["target_data_1"].setdefault(col_val_menu_1, tmp_file_mimetype_1)
    if col_val_menu_2 is not None:
        tmp_file_data_2, tmp_file_mimetype_2 = _get_file_data_columnclass(
            objdbca,
            objtable_2,
            col_name_menu_2,
            col_val_menu_2,
            target_uuid_2,
            column_class_name_2)
        file_mimetypes[tmp_col_name]["target_data_2"].setdefault(col_val_menu_2, tmp_file_mimetype_2)

    # compare result[file]
    if tmp_file_data_1 != tmp_file_data_2:
        value_compare_flg = True
        file_compare_flg = True
        diff_flg_file.setdefault(tmp_col_name, file_compare_flg)
    else:
        file_compare_flg = False
        diff_flg_file.setdefault(tmp_col_name, file_compare_flg)

    # compare file
    if compare_mode == "file":
        str_rdiff = _get_unified_diff(
            accept_compare_file_list,
            col_val_menu_1,
            col_val_menu_2,
            tmp_file_mimetype_1,
            tmp_file_mimetype_2,
            tmp_file_data_1,
            tmp_file_data_2)

        if str_rdiff == "":
            compare_config = _set_flg(compare_config, "compare_file", False)

        compare_config["unified_diff"]["file_data"].setdefault(
            "menu_1",
            {"name": col_val_menu_1, "data": tmp_file_data_1}
        )
        compare_config["unified_diff"]["file_data"].setdefault(
            "menu_2",
            {"name": col_val_menu_2, "data": tmp_file_data_2}
        )
        compare_config["unified_diff"]["diff_result"] = str_rdiff
        target_compare_file_info = {}
        target_compare_file_info.setdefault("target_host", target_host)
        target_compare_file_info.setdefault("operation_1", operation_name_disp_1)
        target_compare_file_info.setdefault("base_datetime_1", base_datetime_1)
        target_compare_file_info.setdefault("operation_2", operation_name_disp_2)
        target_compare_file_info.setdefault("base_datetime_2", base_datetime_2)

        compare_config["target_compare_file_info"] = target_compare_file_info

    # set compare file endpoin + parameter
    endpoint = ("/api/{organization_id}/workspaces/{workspace_id}/ita/menu/{menu}/compare/execute/file/".format(
                organization_id=g.get("ORGANIZATION_ID"),
                workspace_id=g.get("WORKSPACE_ID"),
                menu="compare_execute",
                ))
    file_compare_parameter = compare_config.get("parameter").copy()
    file_compare_parameter.setdefault("copmare_file_data", True)
    file_compare_parameter.setdefault("copmare_target_column", tmp_col_name)
    # file_compare_parameter.setdefault("host", target_host)
    file_compare_parameter["host"] = target_host

    # set compare result detail[file]
    tmp_file_compare_info = {}
    tmp_file_compare_info["file_name_diff_flg"] = value_compare_flg
    tmp_file_compare_info["file_data_diff_flg"] = file_compare_flg
    tmp_file_compare_info.setdefault("file_mimetype", file_mimetypes)
    tmp_file_compare_info.setdefault("file_name_diff_flg", value_compare_flg)
    tmp_file_compare_info.setdefault("file_data_diff_flg", file_compare_flg)
    tmp_file_compare_info.setdefault("method", "POST")
    tmp_file_compare_info.setdefault("endpoint", endpoint)
    tmp_file_compare_info.setdefault("parameter", file_compare_parameter)

    del tmp_file_data_1
    del tmp_file_data_2

    return compare_config, tmp_file_compare_info, diff_flg_file


# 対象メニューデータ取得
def _get_target_datas(objdbca, compare_config, options):
    """
        get target datas  [caller:compare_execute]
        ARGS:
            objdbca, compare_config, options
        RETRUN:
            {}
    """
    retBool = True

    try:
        target_parameter = {}
        target_host_list = []
        target_menus = compare_config.get("target_menus")
        tmp_accept_host_list = compare_config.get("parameter").get("host")
        if isinstance(tmp_accept_host_list, list):
            accept_host_list = tmp_accept_host_list
        elif isinstance(tmp_accept_host_list, str):
            accept_host_list = [tmp_accept_host_list]
        else:
            accept_host_list = []

        target_menu_info = compare_config.get("target_menu_info")

        input_order_list = {}
        host_filter_flg = False
        if len(accept_host_list) != 0:
            host_filter_flg = True
        compare_config = _set_flg(compare_config, "host_filter_flg", host_filter_flg)

        for target_key, target_menu in target_menus.items():
            # load load_table
            try:
                objmenu = load_table.loadTable(objdbca, target_menu)  # noqa: F405
            except Exception:
                # loadTable is faild
                status_code = "401-00003"
                log_msg_args = [target_menu]
                api_msg_args = [target_menu]
                raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

            # set objtable base_parameters
            restkey_list = objmenu.get_restkey_list()
            compare_config["objtable"].setdefault(target_key, objmenu.get_objtable())
            compare_config = _set_base_parameters(compare_config, restkey_list, target_key)

            input_order_list.setdefault(target_key, {})
            vertical = target_menu_info.get(target_key).get("vertical")

            # set filter parameter
            rest_mode = "excel"
            filter_parameter = {}
            operation_date = None
            # set base_date
            if target_key == "menu_1":
                operation_date = compare_config.get("parameter").get("base_date_1")
            if target_key == "menu_2":
                operation_date = compare_config.get("parameter").get("base_date_2")

            if operation_date:
                filter_parameter.setdefault("base_datetime", {"RANGE": {"END": operation_date}})
            # set host
            if host_filter_flg is True:
                filter_parameter.setdefault("host_name", {"LIST": accept_host_list})
            # execute filter
            status_code, tmp_result, msg = objmenu.rest_filter(filter_parameter, rest_mode)

            # target_parameter SET
            compare_config.setdefault("_target_parameter", {})
            compare_config = _set_target_parameter(compare_config, target_key, vertical, tmp_result)
            target_parameter = compare_config.get("_target_parameter")

            # get target host list
            if len(target_host_list) == 0:
                target_host_list = list(target_parameter.keys())
                target_host_list.sort()
            else:
                target_host_list.extend(list(target_parameter.keys()))
                target_host_list = list(set(target_host_list))
        target_host_list.sort()
        for host_name in target_host_list:
            tmp_input_order = list(target_parameter.get(host_name).keys())
            tmp_input_order = list(set(tmp_input_order))
            input_order_list["menu_1"].setdefault(host_name, tmp_input_order)
            input_order_list["menu_2"].setdefault(host_name, tmp_input_order)

        # set target_host_list input_order_list
        compare_config["target_host_list"] = target_host_list
        compare_config["input_order_list"] = input_order_list

        # complement target_parameter
        compare_config = _complement_target_parameter(compare_config, target_parameter)

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "compare_target_menu_error", True)
        retBool = False

    return retBool, compare_config,


# 補完用対象項目設定(rest_name)
def _set_base_parameters(compare_config, restkey_list, target_key):
    """
        set base parameters [caller:_get_target_datas]
        ARGS:
            compare_config, restkey_list, target_key
        RETRUN:
            {}
    """

    del_parameter_list = compare_config.get("del_parameter_list")

    # all rest_key
    base_parameter_all = {}
    for rest_key in restkey_list:
        base_parameter_all.setdefault(rest_key, None)
    compare_config["base_parameter_all"].setdefault(target_key, base_parameter_all)

    # id + parameter  rest_key
    base_parameter = {}
    for del_key in del_parameter_list:
        restkey_list.remove(del_key)
    for rest_key in restkey_list:
        base_parameter.setdefault(rest_key, None)
        compare_config["base_parameter"].setdefault(target_key, base_parameter)

    return compare_config


# 対象データ非対称補完
def _complement_target_parameter(compare_config, target_parameter):
    """
        complement target parameter [caller:_get_target_datas]
        ARGS:
            compare_config, restkey_list, target_key
        RETRUN:
            {}
    """
    target_host_list = compare_config.get("target_host_list")
    input_order_list = compare_config.get("input_order_list")
    base_parameter_all_1 = compare_config["base_parameter_all"]["menu_1"]
    base_parameter_all_2 = compare_config["base_parameter_all"]["menu_2"]

    for host_name in target_host_list:
        if host_name in target_parameter:
            tmp_io_list_1 = input_order_list["menu_1"][host_name]
            tmp_io_list_2 = input_order_list["menu_2"][host_name]
            # complement base menu1 input_order
            for tmp_io in tmp_io_list_1:
                if tmp_io in target_parameter[host_name]:
                    target_parameter[host_name].setdefault(tmp_io, {})
                    if "menu_1" not in target_parameter[host_name][tmp_io]:
                        target_parameter[host_name][tmp_io].setdefault("menu_1", base_parameter_all_1)
                    elif target_parameter[host_name][tmp_io]["menu_1"] is None:
                        target_parameter[host_name][tmp_io].setdefault("menu_1", base_parameter_all_1)
                    if "menu_2" not in target_parameter[host_name][tmp_io]:
                        target_parameter[host_name][tmp_io].setdefault("menu_2", base_parameter_all_2)
                    elif target_parameter[host_name][tmp_io]["menu_2"] is None:
                        target_parameter[host_name][tmp_io].setdefault("menu_2", base_parameter_all_2)
            # complement base menu2 input_order
            for tmp_io in tmp_io_list_2:
                if tmp_io not in target_parameter[host_name]:
                    target_parameter[host_name].setdefault(tmp_io, {})
                    if "menu_1" not in target_parameter[host_name][tmp_io]:
                        target_parameter[host_name][tmp_io].setdefault("menu_1", base_parameter_all_1)
                    elif target_parameter[host_name][tmp_io]["menu_1"] is None:
                        target_parameter[host_name][tmp_io].setdefault("menu_1", base_parameter_all_1)
                    if "menu_2" not in target_parameter[host_name][tmp_io]:
                        target_parameter[host_name][tmp_io].setdefault("menu_2", base_parameter_all_2)
                    elif target_parameter[host_name][tmp_io]["menu_2"] is None:
                        target_parameter[host_name][tmp_io].setdefault("menu_2", base_parameter_all_2)

    compare_config["origin_data"] = target_parameter

    return compare_config


# 対象データ整形
def _set_target_parameter(compare_config, target_key, vertical, filter_result):
    """
        set target parameter [caller:_get_target_datas]
        ARGS:
            compare_config, restkey_list, target_key
        RETRUN:
            {}
    """
    target_parameter = compare_config.get("_target_parameter")
    target_menu_info = compare_config.get("target_menu_info")

    if len(filter_result) >= 1:
        for row in filter_result:
            override_flg = False
            insert_flg = False
            tmp_parameter = row.get("parameter")
            host_name = tmp_parameter.get("host_name")
            target_menu_info.get(target_key).get("vertical")
            base_datetime = tmp_parameter.get("base_datetime")

            # vertical off
            input_order = "__no_input_order__"
            # vertical on
            if vertical == "1":
                input_order = tmp_parameter.get("input_order")

            # set insert_flg
            # set override_flg: input_order重複時, base_datetimeが最新のものを優先してSET
            target_parameter.setdefault(host_name, {})
            if input_order in target_parameter[host_name]:
                if target_key in target_parameter[host_name][input_order]:
                    p_base_datetime = target_parameter[host_name][input_order][target_key].get("base_datetime")
                    if base_datetime > p_base_datetime:
                        override_flg = True
                else:
                    insert_flg = True
            else:
                insert_flg = True

            # data set or override
            if insert_flg is True:
                target_parameter.setdefault(host_name, {})
                target_parameter[host_name].setdefault(input_order, {})
                target_parameter[host_name][input_order].setdefault(target_key, tmp_parameter)
            if override_flg is True:
                target_parameter[host_name][input_order][target_key] = tmp_parameter

        compare_config["_target_parameter"] = target_parameter

    return compare_config


# 比較設定取得
def _set_compare_config_info(objdbca, compare_config, options):
    """
        set compare_config_info  [caller:compare_execute]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    retBool = True

    try:
        # set compare_config
        retBool, compare_config = _set_compare_config(objdbca, compare_config, options)
        detail_flg = _get_flg(compare_config, "detail_flg")

        # set compare_detail_config
        if detail_flg is True:
            retBool, compare_config = _set_compare_detail_config(objdbca, compare_config, options)

        # set column_info
        retBool, compare_config = _set_column_info(objdbca, compare_config, options)

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "compare_target_menu_error", True)
        retBool = False

    return retBool, compare_config,


# 比較設定取得
def _set_compare_config(objdbca, compare_config, options):
    """
        set compare_config [caller:_set_compare_config_info]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    retBool = True

    try:
        # get language
        language = compare_config.get("language")
        # get compare_list
        compare_name = compare_config.get("parameter").get("compare")
        sql_str = textwrap.dedent("""
            SELECT
                `TAB_A`.*,
                `TAB_B`.`MENU_NAME_JA` AS `TARGET_MENU_NAME_1_JA`,
                `TAB_B`.`MENU_NAME_EN` AS `TARGET_MENU_NAME_1_EN`,
                `TAB_B`.`MENU_NAME_REST` AS `TARGET_MENU_NAME_1_REST`,
                `TAB_D`.`VERTICAL` AS `TARGET_MENU_1_VERTICAL`,
                `TAB_C`.`MENU_NAME_JA` AS `TARGET_MENU_NAME_2_JA`,
                `TAB_C`.`MENU_NAME_EN` AS `TARGET_MENU_NAME_2_EN`,
                `TAB_C`.`MENU_NAME_REST` AS `TARGET_MENU_NAME_2_REST`,
                `TAB_E`.`VERTICAL` AS `TARGET_MENU_2_VERTICAL`
            FROM
                `T_COMPARE_CONFG_LIST` `TAB_A`
            LEFT JOIN `T_COMN_MENU` `TAB_B` ON ( `TAB_A`.`TARGET_MENU_1` = `TAB_B`.`MENU_ID` )
            LEFT JOIN `T_COMN_MENU` `TAB_C` ON ( `TAB_A`.`TARGET_MENU_2` = `TAB_C`.`MENU_ID` )
            LEFT JOIN `T_COMN_MENU_TABLE_LINK` `TAB_D` ON ( `TAB_A`.`TARGET_MENU_1` = `TAB_D`.`MENU_ID` )
            LEFT JOIN `T_COMN_MENU_TABLE_LINK` `TAB_E` ON ( `TAB_A`.`TARGET_MENU_2` = `TAB_E`.`MENU_ID` )
            WHERE `TAB_A`.`COMPARE_NAME` = %s
            AND `TAB_A`.`DISUSE_FLAG` <> 1
            AND `TAB_B`.`DISUSE_FLAG` <> 1
            AND `TAB_C`.`DISUSE_FLAG` <> 1
            AND `TAB_D`.`DISUSE_FLAG` <> 1
            AND `TAB_E`.`DISUSE_FLAG` <> 1
        """).format().strip()
        bind_list = [compare_name]

        rows = objdbca.sql_execute(sql_str, bind_list)
        if len(rows) == 1:
            config_compare_list = rows[0]

            detail_flg = bool(strtobool(config_compare_list.get("DETAIL_FLAG")))
            compare_config = _set_flg(compare_config, "detail_flg", detail_flg)
            compare_config["config_compare_list"] = config_compare_list
            compare_config["target_menus"]["menu_1"] = config_compare_list.get("TARGET_MENU_NAME_1_REST")
            compare_config["target_menus"]["menu_2"] = config_compare_list.get("TARGET_MENU_NAME_2_REST")
            compare_config["target_menus_lang"]["menu_1"] = config_compare_list.get("TARGET_MENU_NAME_1_" + language.upper())
            compare_config["target_menus_lang"]["menu_2"] = config_compare_list.get("TARGET_MENU_NAME_2_" + language.upper())

            target_menu_info = {}
            target_menu_info.setdefault("menu_1", {})
            target_menu_info.setdefault("menu_2", {})
            target_menu_info["menu_1"].setdefault("menu_id", config_compare_list.get("TARGET_MENU_1"))
            target_menu_info["menu_2"].setdefault("menu_id", config_compare_list.get("TARGET_MENU_2"))
            target_menu_info["menu_1"].setdefault("menu_name_ja", config_compare_list.get("TARGET_MENU_NAME_1_JA"))
            target_menu_info["menu_2"].setdefault("menu_name_ja", config_compare_list.get("TARGET_MENU_NAME_2_JA"))
            target_menu_info["menu_1"].setdefault("menu_name_en", config_compare_list.get("TARGET_MENU_NAME_1_EN"))
            target_menu_info["menu_2"].setdefault("menu_name_en", config_compare_list.get("TARGET_MENU_NAME_2_EN"))
            target_menu_info["menu_1"].setdefault("menu_name_rest", config_compare_list.get("TARGET_MENU_NAME_1_REST"))
            target_menu_info["menu_2"].setdefault("menu_name_rest", config_compare_list.get("TARGET_MENU_NAME_2_REST"))
            target_menu_info["menu_1"].setdefault("vertical", config_compare_list.get("TARGET_MENU_1_VERTICAL"))
            target_menu_info["menu_2"].setdefault("vertical", config_compare_list.get("TARGET_MENU_2_VERTICAL"))
            compare_config["target_menu_info"] = target_menu_info

            vertical_1 = target_menu_info.get("menu_1").get("vertical")
            vertical_2 = target_menu_info.get("menu_2").get("vertical")
            # set vertical_compare_flg　
            if vertical_1 == "1" and vertical_2 == "1":
                compare_config = _set_flg(compare_config, "vertical_compare_flg", True)
            elif vertical_1 == "1" and vertical_1 != vertical_2:
                # compare_config faild nomal * vertical
                target_key = "compare_config"
                msg_code = "MSG-60001"
                err_msg = g.appmsg.get_api_message(msg_code, [])
                compare_config = _set_msg(compare_config, target_key, err_msg)
                status_code = "499-01002"
                log_msg_args = [compare_name]
                api_msg_args = [compare_name]
                raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        else:
            target_key = "compare_config"
            err_msg = "compare_config faild"
            compare_config = _set_msg(compare_config, target_key, err_msg)
            status_code = "499-01002"
            log_msg_args = [compare_name]
            api_msg_args = [compare_name]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405
    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "compare_config_error", True)
        retBool = False

    return retBool, compare_config,


# 比較設定詳細取得
def _set_compare_detail_config(objdbca, compare_config, options):
    """
        set compare_detail_config  [caller:_set_compare_config_info]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    retBool = True

    try:
        # get compare_detail
        compare_name = compare_config.get("parameter").get("compare")
        sql_str = textwrap.dedent("""
            SELECT
                `TAB_A`.*,
                `TAB_C`.`COLUMN_NAME_JA` AS `TARGET_COLUMN_NAME_1_JA`,
                `TAB_C`.`COLUMN_NAME_EN` AS `TARGET_COLUMN_NAME_1_EN`,
                `TAB_C`.`COLUMN_NAME_REST` AS `TARGET_COLUMN_NAME_1_REST`,
                `TAB_C`.`COLUMN_CLASS` AS `TARGET_COLUMN_CLASS_1`,
                `TAB_E`.`COLUMN_CLASS_NAME` AS `TARGET_COLUMN_CLASS_NAME_1`,
                `TAB_D`.`COLUMN_NAME_JA` AS `TARGET_COLUMN_NAME_2_JA`,
                `TAB_D`.`COLUMN_NAME_EN` AS `TARGET_COLUMN_NAME_2_EN`,
                `TAB_D`.`COLUMN_NAME_REST` AS `TARGET_COLUMN_NAME_2_REST`,
                `TAB_D`.`COLUMN_CLASS` AS `TARGET_COLUMN_CLASS_2`,
                `TAB_F`.`COLUMN_CLASS_NAME` AS `TARGET_COLUMN_CLASS_NAME_2`
            FROM
                `T_COMPARE_DETAIL_LIST` `TAB_A`
            LEFT JOIN `T_COMPARE_CONFG_LIST` `TAB_B` ON ( `TAB_A`.`COMPARE_ID` = `TAB_B`.`COMPARE_ID` )
            LEFT JOIN `T_COMN_MENU_COLUMN_LINK` `TAB_C` ON ( `TAB_A`.`TARGET_COLUMN_ID_1` = `TAB_C`.`COLUMN_DEFINITION_ID` )
            LEFT JOIN `T_COMN_MENU_COLUMN_LINK` `TAB_D` ON ( `TAB_A`.`TARGET_COLUMN_ID_2` = `TAB_D`.`COLUMN_DEFINITION_ID` )
            LEFT JOIN `T_COMN_COLUMN_CLASS` `TAB_E` ON ( `TAB_E`.`COLUMN_CLASS_ID` = `TAB_C`.`COLUMN_CLASS` )
            LEFT JOIN `T_COMN_COLUMN_CLASS` `TAB_F` ON ( `TAB_F`.`COLUMN_CLASS_ID` = `TAB_D`.`COLUMN_CLASS` )
            WHERE `TAB_B`.`COMPARE_NAME` = %s
            AND `TAB_A`.`DISUSE_FLAG` <> 1
            AND `TAB_B`.`DISUSE_FLAG` <> 1
            AND `TAB_C`.`DISUSE_FLAG` <> 1
            AND `TAB_D`.`DISUSE_FLAG` <> 1
            ORDER BY `TAB_A`.`DISP_SEQ` ASC
        """).format().strip()
        bind_list = [compare_name]

        rows = objdbca.sql_execute(sql_str, bind_list)
        config_compare_detail = {}
        config_compare_disp = []

        if len(rows) >= 1:
            row = {
                'COMPARE_DETAIL_ID': 'menu',
                'COMPARE_ID': 'menu',
                'COMPARE_COL_TITLE': 'メニュー名',
                'TARGET_COLUMN_ID_1': 'menu',
                'TARGET_INPUT_ORDER_1': None,
                'TARGET_COLUMN_ID_2': 'menu',
                'TARGET_INPUT_ORDER_2': None,
                'DISP_SEQ': 0,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'TARGET_COLUMN_NAME_1_JA': 'メニュー名',
                'TARGET_COLUMN_NAME_1_EN': 'menu',
                'TARGET_COLUMN_NAME_1_REST': 'menu',
                'TARGET_COLUMN_CLASS_1': '1',
                'TARGET_COLUMN_CLASS_NAME_1': 'SingleTextColumn',
                'TARGET_COLUMN_NAME_2_JA': 'メニュー名',
                'TARGET_COLUMN_NAME_2_EN': 'menu',
                'TARGET_COLUMN_NAME_2_REST': 'menu',
                'TARGET_COLUMN_CLASS_2': '1',
                'TARGET_COLUMN_CLASS_NAME_2': 'SingleTextColumn'
            }
            compare_col_title = row.get("COMPARE_COL_TITLE")
            config_compare_detail.setdefault(compare_col_title, row)
            config_compare_disp.append(row)
            row = {
                'COMPARE_DETAIL_ID': 'uuid',
                'COMPARE_ID': 'uuid',
                'COMPARE_COL_TITLE': '項番',
                'TARGET_COLUMN_ID_1': 'uuid',
                'TARGET_INPUT_ORDER_1': None,
                'TARGET_COLUMN_ID_2': 'uuid',
                'TARGET_INPUT_ORDER_2': None,
                'DISP_SEQ': 0,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'TARGET_COLUMN_NAME_1_JA': '項番',
                'TARGET_COLUMN_NAME_1_EN': 'uuid',
                'TARGET_COLUMN_NAME_1_REST': 'uuid',
                'TARGET_COLUMN_CLASS_1': '1',
                'TARGET_COLUMN_CLASS_NAME_1': 'SingleTextColumn',
                'TARGET_COLUMN_NAME_2_JA': '項番',
                'TARGET_COLUMN_NAME_2_EN': 'uuid',
                'TARGET_COLUMN_NAME_2_REST': 'uuid',
                'TARGET_COLUMN_CLASS_2': '1',
                'TARGET_COLUMN_CLASS_NAME_2': 'SingleTextColumn'
            }
            compare_col_title = row.get("COMPARE_COL_TITLE")
            config_compare_detail.setdefault(compare_col_title, row)
            config_compare_disp.append(row)
            row = {
                'COMPARE_DETAIL_ID': 'operation_name_disp',
                'COMPARE_ID': 'operation_name_disp',
                'COMPARE_COL_TITLE': 'オペレーション名',
                'TARGET_COLUMN_ID_1': 'operation_name_disp',
                'TARGET_INPUT_ORDER_1': None,
                'TARGET_COLUMN_ID_2': 'operation_name_disp',
                'TARGET_INPUT_ORDER_2': None,
                'DISP_SEQ': 0,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'TARGET_COLUMN_NAME_1_JA': 'オペレーション名',
                'TARGET_COLUMN_NAME_1_EN': 'operation_name_disp',
                'TARGET_COLUMN_NAME_1_REST': 'operation_name_disp',
                'TARGET_COLUMN_CLASS_1': '1',
                'TARGET_COLUMN_CLASS_NAME_1': 'SingleTextColumn',
                'TARGET_COLUMN_NAME_2_JA': 'オペレーション名',
                'TARGET_COLUMN_NAME_2_EN': 'operation_name_disp',
                'TARGET_COLUMN_NAME_2_REST': 'operation_name_disp',
                'TARGET_COLUMN_CLASS_2': '1',
                'TARGET_COLUMN_CLASS_NAME_2': 'SingleTextColumn'
            }
            compare_col_title = row.get("COMPARE_COL_TITLE")
            config_compare_detail.setdefault(compare_col_title, row)
            config_compare_disp.append(row)
            row = {
                'COMPARE_DETAIL_ID': 'base_datetime',
                'COMPARE_ID': 'base_datetime',
                'COMPARE_COL_TITLE': '基準日時',
                'TARGET_COLUMN_ID_1': 'base_datetime',
                'TARGET_INPUT_ORDER_1': None,
                'TARGET_COLUMN_ID_2': 'base_datetime',
                'TARGET_INPUT_ORDER_2': None,
                'DISP_SEQ': 0,
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'TARGET_COLUMN_NAME_1_JA': '基準日時',
                'TARGET_COLUMN_NAME_1_EN': 'base_datetime',
                'TARGET_COLUMN_NAME_1_REST': 'base_datetime',
                'TARGET_COLUMN_CLASS_1': '1',
                'TARGET_COLUMN_CLASS_NAME_1': 'SingleTextColumn',
                'TARGET_COLUMN_NAME_2_JA': '基準日時',
                'TARGET_COLUMN_NAME_2_EN': 'base_datetime',
                'TARGET_COLUMN_NAME_2_REST': 'base_datetime',
                'TARGET_COLUMN_CLASS_2': '1',
                'TARGET_COLUMN_CLASS_NAME_2': 'SingleTextColumn'
            }
            compare_col_title = row.get("COMPARE_COL_TITLE")
            config_compare_detail.setdefault(compare_col_title, row)
            config_compare_disp.append(row)
            for row in rows:
                # disq_seq = row.get("DISP_SEQ")
                compare_col_title = row.get("COMPARE_COL_TITLE")
                config_compare_detail.setdefault(compare_col_title, row)
                config_compare_disp.append(row)
            compare_config["config_compare_detail"] = config_compare_detail
            compare_config["config_compare_disp"] = config_compare_disp
        else:
            target_key = "compare_config"
            err_msg = "compare_config_detail faild"
            compare_config = _set_msg(compare_config, target_key, err_msg)
            status_code = "499-01003"
            log_msg_args = []
            api_msg_args = []
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "compare_config_error", True)
        retBool = False

    return retBool, compare_config,


# 比較項目設定
def _set_column_info(objdbca, compare_config, options):
    """
        set column_info  [caller:_set_compare_config_info]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    retBool = True
    language = compare_config.get("language")

    try:
        column_info = []
        file_column_list = [9, "9", "FileUploadColumn", "FileUploadEncryptColumn"]
        detail_flg = _get_flg(compare_config, "detail_flg")
        target_menu_info = compare_config.get("target_menu_info")
        del_parameter_list = compare_config.get("del_parameter_list")
        no_compare_parameter_list = compare_config.get("no_compare_parameter_list")
        no_input_order_list = compare_config.get("no_input_order_list")
        vertical_no_use_rest_key = compare_config.get("vertical_no_use_rest_key")

        compare_config = _set_flg(compare_config, "compare_file", False)

        # detail_flg: True: use T_COMPARE_DETAIL_LIST / False: use T_COMN_MENU_COLUMN_LINK
        if detail_flg is False:
            menu_id = target_menu_info.get("menu_1").get("menu_id")
            sql_str = textwrap.dedent("""
                SELECT
                    `TAB_A`.*,
                    `TAB_B`.`COLUMN_CLASS_NAME`
                FROM
                    `T_COMN_MENU_COLUMN_LINK` `TAB_A`
                LEFT JOIN `T_COMN_COLUMN_CLASS` `TAB_B` ON ( `TAB_A`.`COLUMN_CLASS` = `TAB_B`.`COLUMN_CLASS_ID` )
                WHERE `TAB_A`.`MENU_ID` = %s
                AND `TAB_A`.`DISUSE_FLAG` <> 1
                ORDER BY  `TAB_A`.`COLUMN_DISP_SEQ` ASC
            """).format().strip()
            bind_list = [menu_id]
            # compare_list
            rows = objdbca.sql_execute(sql_str, bind_list)
            if len(rows) >= 1:
                for row in rows:
                    compare_col_title = row.get("COLUMN_NAME_" + language.upper())
                    col_key = row.get("COLUMN_NAME_REST")
                    if col_key not in del_parameter_list:
                        column_class = row.get("COLUMN_CLASS")
                        column_class = row.get("COLUMN_CLASS_NAME")
                        # file comapre target flg
                        file_flg = False
                        if column_class in file_column_list:
                            compare_config = _set_flg(compare_config, "compare_file", True)
                            file_flg = True

                        # comapre target flg
                        compare_target_flg = False
                        if col_key not in no_compare_parameter_list:
                            compare_target_flg = True

                        # no input order flg
                        no_input_order_flg = False
                        if col_key in no_input_order_list:
                            no_input_order_flg = True

                        # vertical no use flg
                        vertical_no_use_flg = False
                        if col_key in vertical_no_use_rest_key:
                            vertical_no_use_flg = True

                        tmp_column_info = {
                            "col_name": compare_col_title,
                            "menu_1": col_key,
                            "menu_2": col_key,
                            "file_flg": file_flg,
                            "compare_target_flg": compare_target_flg,
                            "no_input_order_flg": no_input_order_flg,
                            "vertical_no_use_flg": vertical_no_use_flg,
                            "column_class_1": column_class,
                            "column_class_2": column_class
                        }
                        column_info.append(tmp_column_info)
        else:
            config_compare_disp = compare_config.get("config_compare_disp")
            if len(config_compare_disp) >= 1:
                for column_row in config_compare_disp:
                    compare_col_title = column_row.get("COMPARE_COL_TITLE")
                    col_key_1 = column_row.get("TARGET_COLUMN_NAME_1_REST")
                    col_key_2 = column_row.get("TARGET_COLUMN_NAME_2_REST")
                    column_class_1 = column_row.get("TARGET_COLUMN_CLASS_1")
                    column_class_2 = column_row.get("TARGET_COLUMN_CLASS_2")
                    column_class_1 = column_row.get("TARGET_COLUMN_CLASS_NAME_1")
                    column_class_2 = column_row.get("TARGET_COLUMN_CLASS_NAME_2")
                    input_order_1 = column_row.get("TARGET_INPUT_ORDER_1")
                    input_order_2 = column_row.get("TARGET_INPUT_ORDER_2")
                    if input_order_1 is None and input_order_2 is None:
                        input_order_1 = "__no_input_order__"
                        input_order_2 = "__no_input_order__"

                    # file comapre target flg
                    file_flg = False
                    if column_class_1 in file_column_list or column_class_2 in file_column_list:
                        compare_config = _set_flg(compare_config, "compare_file", True)
                        file_flg = True

                    # comapre target flg
                    compare_target_flg = True
                    no_input_order_flg = False
                    vertical_no_use_flg = False
                    if col_key_1 is None and col_key_2 is None:
                        compare_target_flg = False
                    else:
                        # comapre target flg
                        if col_key_1 in no_compare_parameter_list and col_key_2 in no_compare_parameter_list:
                            compare_target_flg = False
                        # no input order flg
                        if col_key_1 in no_input_order_list and col_key_2 in no_input_order_list:
                            no_input_order_flg = True
                        # vertical no use flg
                        if col_key_1 in vertical_no_use_rest_key and col_key_2 in vertical_no_use_rest_key:
                            vertical_no_use_flg = True

                    tmp_column_info = {
                        "col_name": compare_col_title,
                        "menu_1": col_key_1,
                        "menu_2": col_key_2,
                        "file_flg": file_flg,
                        "compare_target_flg": compare_target_flg,
                        "no_input_order_flg": no_input_order_flg,
                        "vertical_no_use_flg": vertical_no_use_flg,
                        "column_class_1": column_class_1,
                        "column_class_2": column_class_2,
                        "input_order_1": input_order_1,
                        "input_order_2": input_order_2,
                    }
                    column_info.append(tmp_column_info)

        # set column_info
        compare_config["column_info"] = column_info
    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "compare_target_menu_error", True)
        retBool = False

    return retBool, compare_config,


# 比較項目設定(縦メニュー変換 item_1 -> item_1[input_order:X]
def _override_column_info_vertical_ver(objdbca, compare_config, options):
    """
        override column_info vertical ver  [caller:compare_execute]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    retBool = True
    base_column_info = compare_config.get("column_info")
    input_order_lang = compare_config.get("input_order_lang")

    try:
        column_info = []
        origin_data = compare_config.get("origin_data")
        vertical_compare_flg = _get_flg(compare_config, "vertical_compare_flg")

        if vertical_compare_flg is True:
            input_orders = []
            for target_host in origin_data:
                tmp_input_orders = list(origin_data[target_host].keys())
                tmp_input_orders = list(set(tmp_input_orders))
                input_orders.extend(tmp_input_orders)
                input_orders = list(set(input_orders))

            if "__no_input_order__" in input_orders:
                input_orders.remove("__no_input_order__")
            input_orders.sort()
            for base_column in base_column_info:
                col_name = base_column["col_name"]
                no_input_order_flg = base_column["no_input_order_flg"]
                vertical_no_use_flg = base_column["vertical_no_use_flg"]
                if no_input_order_flg is False:
                    for input_order in input_orders:
                        tmp_base_column = base_column.copy()
                        tmp_base_column["col_name"] = "{}[{}:{}]".format(col_name, input_order_lang, input_order)
                        tmp_base_column["col_name"] = _get_col_name_input_order(col_name, input_order, input_order_lang)
                        # set column_info
                        column_info.append(tmp_base_column)
                elif vertical_no_use_flg is True:
                    pass
                else:
                    # set column_info
                    column_info.append(base_column)
            compare_config["column_info"] = column_info

        else:
            pass

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "compare_target_menu_error", True)
        retBool = False

    return retBool, compare_config,


# パラメータチェック
def _chk_parameters(objdbca, compare_config, options):
    """
        check parameters: compare,base_date,other_options  [caller:compare_execute]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    retBool = True

    try:
        # _chk_parameter_compare
        compare_config = _chk_parameter_compare(objdbca, compare_config, options)
        # _chk_parameter_base_date
        compare_config = _chk_parameter_base_date(objdbca, compare_config, options)
        # _chk_parameter_host
        compare_config = _chk_parameter_host(objdbca, compare_config, options)
        # _chk_parameter_copmare_target_column
        compare_config = _chk_parameter_copmare_target_column(objdbca, compare_config, options)
        # chk_compare
        compare_config = _chk_parameter_other_options(objdbca, compare_config, options)

        # error flg check
        tmp_err_flg = _get_flg(compare_config, "parameter_error")
        if tmp_err_flg is True:
            err_msg = _get_msg(compare_config, "parameter_error")
            status_code = "499-01000"
            log_msg_args = [err_msg]
            api_msg_args = [err_msg]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        retBool = False

    return retBool, compare_config,


#  パラメータチェック:compare
def _chk_parameter_compare(objdbca, compare_config, options):
    """
        check parameter:compare [caller:_chk_parameters]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    try:
        tmp_parameter = compare_config.get("parameter")
        compare = tmp_parameter.get("compare")

        if compare:
            sql_str = textwrap.dedent("""
                SELECT * FROM `T_COMPARE_CONFG_LIST` `TAB_A`
                WHERE `TAB_A`.`COMPARE_NAME` = %s
                AND `TAB_A`.`DISUSE_FLAG` <> 1
            """).format().strip()
            bind_list = [compare]
            rows = objdbca.sql_execute(sql_str, bind_list)
            if len(rows) != 1:
                target_key = "compare"
                # compare faild
                msg_code = "MSG-60005"
                msg_args = [target_key, compare]
                err_msg = g.appmsg.get_api_message(msg_code, msg_args)
                compare_config = _set_msg(compare_config, target_key, err_msg)

                status_code = "499-01001"
                log_msg_args = [err_msg]
                api_msg_args = [err_msg]
                raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405
        else:
            target_key = "compare"
            # compare faild
            msg_code = "MSG-60005"
            msg_args = [target_key, compare]
            err_msg = g.appmsg.get_api_message(msg_code, msg_args)
            compare_config = _set_msg(compare_config, target_key, err_msg)
            status_code = "499-01001"
            log_msg_args = [err_msg]
            api_msg_args = [err_msg]
            raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "parameter_error", True)

    return compare_config


# パラメータチェック:base_date
def _chk_parameter_base_date(objdbca, compare_config, options):
    """
        check parameter:base_date [caller:_chk_parameters]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    try:
        tmp_parameter = compare_config.get("parameter")
        base_date_1 = tmp_parameter.get("base_date_1")
        base_date_2 = tmp_parameter.get("base_date_2")
        if base_date_1:
            base_date_1 = _chk_date_time_format("base_date_1", base_date_1)
            compare_config["parameter"]["base_date_1"] = base_date_1
        else:
            pass

        if base_date_2:
            base_date_2 = _chk_date_time_format("base_date_2", base_date_2)
            compare_config["parameter"]["base_date_2"] = base_date_2
        else:
            pass

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "parameter_error", True)

    return compare_config


# 日付形式のチェック
def _chk_date_time_format(key_name, val):
    """
        check datetime format [caller:_chk_parameters]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    # YYYY/MM/DD hh:mm:ssの場合OK
    if re.match(r'^[0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$', val) is not None:
        pass
    # YYYY/MM/DD hh:mmの場合OK、:ssを補完
    elif re.match(r'^[0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}$', val) is not None:
        val = val + ':00'
    # YYYY/MM/DDの場合OK、:hh:mm:ssを補完
    elif re.match(r'^[0-9]{4}/[0-9]{2}/[0-9]{2}$', val) is not None:
        val = val + ' 00:00:00'
    else:
        # date_time format error
        msg_code = "MSG-60006"
        msg_args = [key_name, val]
        err_msg = g.appmsg.get_api_message(msg_code, msg_args)
        status_code = "499-01001"
        log_msg_args = [err_msg]
        api_msg_args = [err_msg]
        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405
    return val


# パラメータチェック:host
def _chk_parameter_host(objdbca, compare_config, options):
    """
        check parameter:host [caller:_chk_parameters]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    try:
        tmp_parameter = compare_config.get("parameter")
        host = tmp_parameter.get("host")

        serch_hosts = []
        if isinstance(host, list):
            serch_hosts = host
        elif isinstance(host, str):
            if host:
                serch_hosts.append(host)
        else:
            if host is not None:
                target_key = "host"
                # host format error
                msg_code = "MSG-60006"
                msg_args = [target_key, host]
                err_msg = g.appmsg.get_api_message(msg_code, msg_args)
                compare_config = _set_msg(compare_config, target_key, err_msg)
                compare_config = _set_flg(compare_config, "parameter_error", True)
                status_code = "499-01001"
                log_msg_args = [err_msg]
                api_msg_args = [err_msg]
                raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

        if len(serch_hosts) >= 1:
            for tmp_host in serch_hosts:
                sql_str = textwrap.dedent("""
                    SELECT * FROM `T_ANSC_DEVICE` `TAB_A`
                    WHERE `TAB_A`.`HOST_NAME` = %s
                    AND `TAB_A`.`DISUSE_FLAG` <> 1
                """).format().strip()
                bind_list = [tmp_host]
                rows = objdbca.sql_execute(sql_str, bind_list)
                if len(rows) != 1:
                    target_key = "host"
                    # host value error
                    msg_code = "MSG-60005"
                    msg_args = [target_key, tmp_host]
                    err_msg = g.appmsg.get_api_message(msg_code, msg_args)
                    compare_config = _set_msg(compare_config, target_key, err_msg)
                    status_code = "499-01001"
                    log_msg_args = [err_msg]
                    api_msg_args = [err_msg]
                    raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "parameter_error", True)

    return compare_config


# パラメータチェック:copmare_target_column
def _chk_parameter_copmare_target_column(objdbca, compare_config, options):
    """
        check parameter:copmare_target_column [caller:_chk_parameters]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    try:
        tmp_parameter = compare_config.get("parameter")
        copmare_target_column = tmp_parameter.get("copmare_target_column")

        if copmare_target_column is None:
            pass
        elif isinstance(copmare_target_column, str):
            pass
        else:
            if copmare_target_column is not None:
                target_key = "copmare_target_column"
                # copmare_target_column value error
                msg_code = "MSG-60005"
                msg_args = [target_key, copmare_target_column]
                err_msg = g.appmsg.get_api_message(msg_code, msg_args)
                compare_config = _set_msg(compare_config, target_key, err_msg)
                compare_config = _set_flg(compare_config, "parameter_error", True)
                status_code = "499-01001"
                log_msg_args = [err_msg]
                api_msg_args = [err_msg]
                raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "parameter_error", True)

    return compare_config


# パラメータチェック:other_options
def _chk_parameter_other_options(objdbca, compare_config, options):
    """
        check parameter:other_options [caller:_chk_parameters]
        ARGS:
            compare_config, compare_config, options
        RETRUN:
            {}
    """
    try:
        tmp_parameter = compare_config.get("parameter")
        other_options = tmp_parameter.get("other_options")
        if isinstance(other_options, dict):
            # output_language
            if "output_language" in other_options:
                output_language = other_options.get("output_language")
                if output_language:
                    if output_language in ["en", "ja"]:
                        pass
                    else:
                        target_key = "other_options.output_language"
                        # language value error
                        msg_code = "MSG-60005"
                        msg_args = [target_key, output_language]
                        err_msg = g.appmsg.get_api_message(msg_code, msg_args)

                        status_code = "499-01001"
                        log_msg_args = [err_msg]
                        api_msg_args = [err_msg]
                        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405
                else:
                    pass
            pass
            # check other options
        else:
            if other_options is not None:
                target_key = "other_options"
                # other_options format error
                msg_code = "MSG-60006"
                msg_args = [target_key, other_options]
                err_msg = g.appmsg.get_api_message(msg_code, msg_args)
                compare_config = _set_msg(compare_config, target_key, err_msg)
                compare_config = _set_flg(compare_config, "parameter_error", True)
                status_code = "499-01001"
                log_msg_args = [err_msg]
                api_msg_args = [err_msg]
                raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
        compare_config = _set_flg(compare_config, "parameter_error", True)

    return compare_config


# ファイルデータ、mimetype取得
def _get_file_data_columnclass(objdbca, objtable, rest_key, file_name, target_uuid, col_class_name='TextColumn'):
    """
        get file_data file_mimetype
        ARGS:
            objdbca, objtable, rest_key, file_name, target_uuid, col_class_name
        RETRUN:
            file_data, file_mimetype
    """
    file_data = None
    file_mimetype = None
    try:
        eval_class_str = "{}(objdbca,objtable,rest_key,'')".format(col_class_name)
        objcolumn = eval(eval_class_str)
        file_data = objcolumn.get_file_data(file_name, target_uuid, None)
        file_path = objcolumn.get_file_data_path(file_name, target_uuid, None)
        file_mimetype, encoding = mimetypes.guess_type(file_path)

    except AppException as _app_e:  # noqa: F405
        raise AppException(_app_e)  # noqa: F405
    except Exception:
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.debug(addline_msg('{}{}'.format(msg, sys._getframe().f_code.co_name)))
    return file_data, file_mimetype


# 代入順序付き項目名
def _get_col_name_input_order(col_name, input_order, input_order_lang=None):
    """
        get col_name add input_order
        ARGS:
            col_name, input_order, input_order_lang=None
        RETRUN:
            col_name_io
    """
    if input_order_lang is not None:
        col_name_io = "{}[{}:{}]".format(col_name, input_order_lang, input_order)
    elif isinstance(input_order, int):
        col_name_io = "{}[{}]".format(col_name, input_order)
    else:
        col_name_io = "{}".format(col_name)
    return col_name_io


# add filename lineno
def addline_msg(msg=''):
    import os
    import inspect
    info = inspect.getouterframes(inspect.currentframe())[1]
    msg_line = "{} ({}:{})".format(msg, os.path.basename(info.filename), info.lineno)
    return msg_line
