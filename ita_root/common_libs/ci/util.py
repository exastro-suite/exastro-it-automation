# Copyright 2022 NEC Corporation#
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
"""
common_libs api common function module
"""
from flask import g
import os
import time
import traceback

from common_libs.common.dbconnect import *
from common_libs.common.exception import AppException, ValidationException
from common_libs.common.util import arrange_stacktrace_format


def wrapper_job(main_logic, organization_id=None, workspace_id=None, loop_count=500):
    '''
    backyard job wrapper
    '''
    common_db = DBConnectCommon()  # noqa: F405
    g.applogger.debug("ITA_DB is connected")

    # 子プロセスで使われているか否か
    is_child_ps = False if organization_id is None else True

    # pythonでのループ
    interval = int(os.environ.get("EXECUTE_INTERVAL"))
    count = 1
    max = int(loop_count) if is_child_ps is False else 1

    while True:
        # get organization_info_list
        if is_child_ps is False:
            organization_info_list = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE `DISUSE_FLAG`=0 ORDER BY `LAST_UPDATE_TIMESTAMP`")
        else:
            organization_info_list = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE `DISUSE_FLAG`=0 AND `ORGANIZATION_ID`=%s", [organization_id])  # noqa: E501
        # autocommit=falseの場合に、ループ中にorganizationが更新されても、最新データが取得できないバグへの対策
        common_db.db_transaction_start()
        common_db.db_commit()

        # set applogger.set_level: default:INFO / Use ITA_DB config value
        set_service_loglevel(common_db)

        for organization_info in organization_info_list:
            # set applogger.set_level: default:INFO / Use ITA_DB config value
            # set_service_loglevel(common_db)

            organization_id = organization_info['ORGANIZATION_ID']

            g.ORGANIZATION_ID = organization_id
            # set log environ format
            g.applogger.set_env_message()

            # database connect info
            g.db_connect_info = {}
            g.db_connect_info['ORGDB_HOST'] = organization_info.get('DB_HOST')
            g.db_connect_info['ORGDB_PORT'] = str(organization_info.get('DB_PORT'))
            g.db_connect_info['ORGDB_USER'] = organization_info.get('DB_USER')
            g.db_connect_info['ORGDB_PASSWORD'] = organization_info.get('DB_PASSWORD')
            g.db_connect_info['ORGDB_ADMIN_USER'] = organization_info.get('DB_ADMIN_USER')
            g.db_connect_info['ORGDB_ADMIN_PASSWORD'] = organization_info.get('DB_ADMIN_PASSWORD')
            g.db_connect_info['ORGDB_DATABASE'] = organization_info.get('DB_DATABASE')
            g.db_connect_info['INITIAL_DATA_ANSIBLE_IF'] = organization_info.get('INITIAL_DATA_ANSIBLE_IF')
            # gitlab connect info
            g.gitlab_connect_info = {}
            g.gitlab_connect_info['GITLAB_USER'] = organization_info['GITLAB_USER']
            g.gitlab_connect_info['GITLAB_TOKEN'] = organization_info['GITLAB_TOKEN']

            # job for organization
            try:
                organization_job(main_logic, organization_id, workspace_id)
            except AppException as e:
                # catch - raise AppException("xxx-xxxxx", log_format)
                app_exception(e)
            except Exception as e:
                # catch - other all error
                exception(e)

        if count >= max:
            break
        else:
            count = count + 1
            time.sleep(interval)


def organization_job(main_logic, organization_id=None, workspace_id=None):
    '''
    job for organization unit

    Argument:
        organization_id
    '''
    org_db = DBConnectOrg(organization_id)  # noqa: F405
    g.applogger.debug("ORG_DB:{} can be connected".format(organization_id))

    # get workspace_info_list
    if workspace_id is None:
        workspace_info_list = org_db.table_select('T_COMN_WORKSPACE_DB_INFO', 'WHERE `DISUSE_FLAG`=0 ORDER BY `LAST_UPDATE_TIMESTAMP`')
    else:
        workspace_info_list = org_db.table_select("T_COMN_WORKSPACE_DB_INFO", "WHERE `DISUSE_FLAG`=0 AND `WORKSPACE_ID`=%s", [workspace_id])  # noqa: E501

    for workspace_info in workspace_info_list:
        # set applogger.set_level: default:INFO / Use ITA_DB config value
        # set_service_loglevel()

        workspace_id = workspace_info['WORKSPACE_ID']

        g.WORKSPACE_ID = workspace_id
        # set log environ format
        g.applogger.set_env_message()

        # database connect info
        g.db_connect_info["WSDB_HOST"] = workspace_info["DB_HOST"]
        g.db_connect_info["WSDB_PORT"] = str(workspace_info["DB_PORT"])
        g.db_connect_info["WSDB_USER"] = workspace_info["DB_USER"]
        g.db_connect_info["WSDB_PASSWORD"] = workspace_info["DB_PASSWORD"]
        g.db_connect_info["WSDB_DATABASE"] = workspace_info["DB_DATABASE"]

        ws_db = DBConnectWs(workspace_id)  # noqa: F405
        g.applogger.debug("WS_DB:{} can be connected".format(workspace_id))

        # set log-level for user setting
        # g.applogger.set_user_setting(ws_db)

        ws_db.db_disconnect()

        # job for workspace
        try:
            if allow_proc(organization_id, workspace_id) is True:
                main_logic(organization_id, workspace_id)
        except AppException as e:
            # catch - raise AppException("xxx-xxxxx", log_format)
            app_exception(e)
        except Exception as e:
            # catch - other all error
            exception(e)

        # delete environment of workspace
        g.pop('WORKSPACE_ID')
        g.db_connect_info.pop("WSDB_HOST")
        g.db_connect_info.pop("WSDB_PORT")
        g.db_connect_info.pop("WSDB_USER")
        g.db_connect_info.pop("WSDB_PASSWORD")
        g.db_connect_info.pop("WSDB_DATABASE")


def wrapper_job_all_org(main_logic, loop_count=500):
    '''
    backyard job wrapper
    '''

    # pythonでのループ
    interval = int(os.environ.get("EXECUTE_INTERVAL"))
    count = 1
    max = int(loop_count)

    g.applogger.debug("ITA_DB is connected")
    common_db = DBConnectCommon()  # noqa: F405

    while True:
        # get organization_info_list
        # job for organization
        try:
            g.applogger.debug(f"wrapper_job_all_org loop=[{count}]")
            # autocommit=falseの場合に、ループ中にorganizationが更新されても、最新データが取得できないバグへの対策
            common_db.db_transaction_start()
            common_db.db_commit()

            # set applogger.set_level: default:INFO / Use ITA_DB config value
            set_service_loglevel(common_db)

            main_logic(common_db)
        except AppException as e:
            # catch - raise AppException("xxx-xxxxx", log_format)
            app_exception(e)
        except Exception as e:
            # catch - other all error
            exception(e)

        if count >= max:
            break
        else:
            count = count + 1
            time.sleep(interval)


def allow_proc(organization_id, workspace_id):
    """
        check the process is allowed to run.

    Argument:
        organization_id
        workspace_id
    Return:
        bool
    """

    allowed = True
    # ita-migrationのスキップファイル
    migration_skip_file_path = os.environ.get('STORAGEPATH') + "skip_all_service"
    # メニューインポートのスキップファイル
    workspace_path = os.environ.get('STORAGEPATH') + "{}/{}/".format(organization_id, workspace_id)
    import_menu_skip_file_path = workspace_path + "tmp/driver/import_menu/skip_all_service"
    # Workspace削除のスキップファイル
    ws_del_skip_file_path = workspace_path + "skip_all_service_for_ws_del"

    file_list = [migration_skip_file_path, import_menu_skip_file_path, ws_del_skip_file_path]

    for file_path in file_list:
        if os.path.isfile(file_path) is True:
            g.applogger.debug("Skip proc. org:{}, ws:{}, file:{}".format(organization_id, workspace_id, file_path))
            allowed = False

    return allowed


def app_exception(e):
    '''
    called when AppException occured

    Argument:
        e: AppException
    '''
    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    ret_db_disuse = is_db_disuse()

    args = e.args
    is_arg = False
    while is_arg is False:
        if isinstance(args[0], AppException):
            args = args[0].args
        elif isinstance(args[0], Exception):
            return exception(args[0])
        else:
            is_arg = True

    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    if ret_db_disuse is False:
        # catch - other all error
        t = traceback.format_exc()
        log_err(arrange_stacktrace_format(t))

        # catch - raise AppException("xxx-xxxxx", log_format), and get message
        result_code, log_msg_args, api_msg_args = args
        log_msg = g.appmsg.get_log_message(result_code, log_msg_args)
        log_err(log_msg)


def exception(e, exception_log_need=False):
    '''
    called when Exception occured

    Argument:
        e: Exception
    '''
    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    ret_db_disuse = is_db_disuse()

    args = e.args
    is_arg = False
    while is_arg is False:
        if isinstance(args[0], AppException):
            return app_exception(args[0])
        elif isinstance(args[0], Exception):
            args = args[0].args
        else:
            is_arg = True

    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    if ret_db_disuse is False or exception_log_need is True:
        # catch - other all error
        t = traceback.format_exc()
        log_err(arrange_stacktrace_format(t))


def validation_exception(e):
    '''
    called when AppException occured

    Argument:
        e: AppException
    '''
    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    ret_db_disuse = is_db_disuse()

    args = e.args
    is_arg = False
    while is_arg is False:
        if isinstance(args[0], ValidationException):
            args = args[0].args
        elif isinstance(args[0], AppException):
            args = args[0].args
        elif isinstance(args[0], Exception):
            return exception(args[0])
        else:
            is_arg = True

    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    if ret_db_disuse is False:
        # catch - other all error
        t = traceback.format_exc()
        log_err(arrange_stacktrace_format(t))

        # catch - raise AppException("xxx-xxxxx", log_format), and get message
        result_code, log_msg_args, api_msg_args = args
        log_msg = g.appmsg.get_log_message(result_code, log_msg_args)
        log_err(log_msg)


def app_exception_driver_log(e, logfile=None):
    '''
    called when AppException occured

    Argument:
        e: AppException
        logfile: If you want exception file output
    '''
    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    ret_db_disuse = is_db_disuse()

    args = e.args
    is_arg = False
    while is_arg is False:
        if isinstance(args[0], AppException):
            args = args[0].args
        elif isinstance(args[0], Exception):
            return exception(args[0])
        else:
            is_arg = True

    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    if ret_db_disuse is False:
        # catch - raise AppException("xxx-xxxxx", log_format), and get message
        result_code, log_msg_args, api_msg_args = args
        log_msg = g.appmsg.get_log_message(result_code, log_msg_args)

        if logfile:
            # 作業実行のエラーログ出力
            f = open(logfile, "a")
            t = traceback.format_exc()
            f.write(arrange_stacktrace_format(t) + "\n\n")
            f.write(log_msg + "\n")
            f.close()


def exception_driver_log(e, logfile=None):
    '''
    called when Exception occured

    Argument:
        e: Exception
        logfile: If you want exception file output
    '''
    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    ret_db_disuse = is_db_disuse()

    args = e.args
    is_arg = False
    while is_arg is False:
        if isinstance(args[0], AppException):
            return app_exception(args[0])
        elif isinstance(args[0], Exception):
            args = args[0].args
        else:
            is_arg = True

    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    if ret_db_disuse is False:
        if logfile:
            # 作業実行のエラーログ出力
            f = open(logfile, "a")
            t = traceback.format_exc()
            f.write(arrange_stacktrace_format(t) + "\n\n")
            f.close()


def validation_exception_driver_log(e, logfile=None):
    '''
    called when AppException occured

    Argument:
        e: AppException
        logfile: If you want exception file output
    '''
    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    ret_db_disuse = is_db_disuse()

    args = e.args
    is_arg = False
    while is_arg is False:
        if isinstance(args[0], ValidationException):
            args = args[0].args
        elif isinstance(args[0], AppException):
            args = args[0].args
        elif isinstance(args[0], Exception):
            return exception(args[0])
        else:
            is_arg = True

    # catch - raise AppException("xxx-xxxxx", log_format), and get message
    result_code, log_msg_args, api_msg_args = args
    log_msg = g.appmsg.get_log_message(result_code, log_msg_args) + "\n\n"
    log_msg += g.appmsg.get_api_message("MSG-10903", [])

    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    if ret_db_disuse is False:
        if logfile:
            # 作業実行のエラーログ出力
            f = open(logfile, "a")
            t = traceback.format_exc()
            f.write(arrange_stacktrace_format(t) + "\n\n")
            f.write(log_msg + "\n")
            f.close()


def log_err(msg=""):
    g.applogger.error("[error]{}".format(msg))


def is_service_loglevel_table(common_db):
    """
        is_service_loglevel_table:
            SHOW TABLES LIKE `T_COMN_LOGLEVEL`
        ARGS:
            common_db, service_loglevel_flg=None
        RETURN:
            bool
    """

    if g.get("SERVICE_LOGLEVEL_FLG") is not None:
        # use g[SERVICE_LOGLEVEL_FLG]
        return g.get("SERVICE_LOGLEVEL_FLG")
    else:
        # first time check `T_COMN_LOGLEVEL` and SET g[SERVICE_LOGLEVEL_FLG]
        service_loglevel_flg = False
        rows_table_list = common_db.sql_execute(
            "SHOW TABLES LIKE %s;",
            ["T_COMN_LOGLEVEL"]
        )
        if len(rows_table_list) == 1:
            service_loglevel_flg = True
        g.setdefault("SERVICE_LOGLEVEL_FLG", service_loglevel_flg)
        return service_loglevel_flg


def set_service_loglevel(common_db=None):
    """
        set_service_loglevel:
            use common_db / new connect common_db and db_disconnect
            default:
                g.applogger.set_level("INFO")
            is service_loglevel table:
                g.applogger.set_level(loglevel)
        ARGS:
            common_db=None
    """
    loglevel = "INFO"
    try:
        # service_name
        service_name = os.environ.get("SERVICE_NAME")

        # use common_db or new connect common_db
        if common_db is None:
            tmp_common_db = DBConnectCommon()  # noqa: F405
        else:
            tmp_common_db = common_db

        # check service_loglevel table
        service_loglevel_flg = is_service_loglevel_table(tmp_common_db)

        # is service_loglevel table: T_COMN_LOGLEVEL
        if service_loglevel_flg is True and service_name is not None:
            # get service_loglevel for SERVICE_NAME
            service_loglevel_list = tmp_common_db.table_select(
                "T_COMN_LOGLEVEL",
                "WHERE `DISUSE_FLAG`=0 AND `SERVICE_NAME`=%s ",
                [service_name]
            )
            # match service_name->loglevel
            if len(service_loglevel_list) == 1:
                loglevel = service_loglevel_list[0].get('LOG_LEVEL')
                # is loglevel
                if loglevel is None:
                    raise Exception()
    except Exception:
        loglevel = "INFO"
        if "SERVICE_LOGLEVEL_FLG" in g:
            g.SERVICE_LOGLEVEL_FLG = None
    finally:
        # applogger.set_level
        g.applogger.set_level(loglevel)

        # connect inside function
        if common_db is None:
            tmp_common_db.db_disconnect()
