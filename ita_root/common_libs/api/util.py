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
import os
from flask import g, request, Response
import traceback
import re
from urllib.parse import quote

from common_libs.common.exception import AppException
from common_libs.common.util import get_iso_datetime, arrange_stacktrace_format, retry_remove, retry_rmdir
from common_libs.common.dbconnect import *

api_timestamp = None


def set_api_timestamp():
    global api_timestamp
    api_timestamp = str(get_iso_datetime())


def get_api_timestamp():
    global api_timestamp
    return api_timestamp


def make_response(data=None, msg="", result_code="000-00000", status_code=200, ts=None):
    """
    make http response

    Argument:
        data: data
        msg: message
        result_code: xxx-xxxxx
        status_code: http status code
    Returns:
        (flask)response
    """
    if result_code == "000-00000" and not msg:
        msg = "SUCCESS"

    res_body = {
        "result": result_code,
        "message": msg,
        "ts": api_timestamp
    }

    if result_code == "000-00000":
        res_body["data"] = data

    log_status = "SUCCESS" if result_code == "000-00000" else "FAILURE"

    # ヘルスチェック用のURLの場合はログを出さない
    ret = re.search("/internal-api/health-check/liveness$|/internal-api/health-check/readiness$", request.url)
    if ret is None:
        g.applogger.debug("[ts={}]response={}".format(api_timestamp, (res_body, status_code)))
        g.applogger.info("[ts={}][api-end][{}][status_code={}]".format(api_timestamp, log_status, status_code))

    return res_body, status_code


def make_response_file_download(data=None, msg="", result_code="000-00000", status_code=200, ts=None, remove_file=False):
    """
    make http response(file download)

    Argument:
        data: data
        msg: message
        result_code: xxx-xxxxx
        status_code: http status code
    Returns:
        (flask)response
    """
    if result_code == "000-00000" and not msg:
        msg = "SUCCESS"

    response_chank_byte = 10000

    if data is None or os.path.isfile(data) is False:
        resp = Response()
        resp.content_length = 0
        resp.content_type = "application/octet-stream"
    else:
        def __make_response():
            with open(data, 'rb') as fp:
                while True:
                    buf = fp.read(response_chank_byte)
                    if len(buf) == 0:
                        break
                    yield buf

        resp = Response(__make_response())
        resp.content_length = os.path.getsize(data)
        resp.content_type = "application/octet-stream"
        file_name = quote(os.path.basename(data))
        resp.headers["Content-Disposition"] = f"attachment; filename={file_name}"


        if remove_file:
            @resp.call_on_close
            def exec_remove():
                remove_temporary_file(data)


    log_status = "SUCCESS" if result_code == "000-00000" else "FAILURE"
    g.applogger.info("[ts={}][api-end][{}][status_code={}]".format(api_timestamp, log_status, status_code))

    return resp, status_code


def app_exception_response(e, exception_log_need=False):
    '''
    make response when AppException occured

    Argument:
        e: AppException
        exception_log_need: True: Exception log output
                                  organization_delete/workspace_delete only
                            False: Exception log not output
                                   default
    Returns:
        (flask)response
    '''
    args = e.args
    is_arg = False
    while is_arg is False:
        if isinstance(args[0], AppException):
            args = args[0].args
        elif isinstance(args[0], Exception):
            return exception_response(args[0])
        else:
            is_arg = True

    # catch - raise AppException("xxx-xxxxx", log_format, msg_format), and get message
    result_code, log_msg_args, api_msg_args = args
    log_msg = g.appmsg.get_log_message(result_code, log_msg_args)
    api_msg = g.appmsg.get_api_message(result_code, api_msg_args)

    # get http status code
    status_code = int(result_code[0:3])
    if 500 <= status_code:
        status_code = 500

    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    if is_db_disuse() is False or exception_log_need is True:
        if status_code == 500:
            g.applogger.error("[ts={}] {}".format(api_timestamp, log_msg))
        else:
            g.applogger.info("[ts={}] {}".format(api_timestamp, log_msg))

    return make_response(None, api_msg, result_code, status_code)


def exception_response(e, exception_log_need=False):
    '''
    make response when Exception occured

    Argument:
        e: Exception
        exception_log_need: True: Exception log output
                                  organization_delete/workspace_delete only
                            False: Exception log not output
                                   default
    Returns:
        (flask)response
    '''
    args = e.args
    is_arg = False
    while is_arg is False:
        if isinstance(args[0], AppException):
            return app_exception_response(args[0], exception_log_need)
        elif isinstance(args[0], Exception):
            args = args[0].args
        else:
            is_arg = True

    # OrganizationとWorkspace削除確認　削除されている場合のエラーログ抑止
    if is_db_disuse() is False or exception_log_need is True:
        # catch - other all error
        t = traceback.format_exc()
        g.applogger.error("[ts={}] {}".format(api_timestamp, arrange_stacktrace_format(t)))

    api_msg = g.appmsg.get_api_message("999-99999")
    return make_response(None, api_msg, "999-99999", 500)


def remove_temporary_file(file_path):

    tmp_path = "/tmp"
    storage_path = os.environ.get('STORAGEPATH')

    try:
        if file_path.startswith(tmp_path) or file_path.startswith(storage_path):
            retry_remove(file_path)
            directory_name = os.path.dirname(file_path)
            retry_rmdir(directory_name)
    except Exception as e:
        raise e


def api_filter(func):
    '''
    wrap api controller

    Argument:
        func: controller(def)
    Returns:
        controller wrapper
    '''

    def wrapper(*args, **kwargs):
        '''
        controller wrapper

        Argument:
            *args, **kwargs: controller args
        Returns:
            (flask)response
        '''
        try:
            g.applogger.debug("[ts={}] controller start -> {}".format(api_timestamp, kwargs))

            # controller execute and make response
            controller_res = func(*args, **kwargs)

            return make_response(*controller_res)
        except AppException as e:
            # catch - raise AppException("xxx-xxxxx", log_format, msg_format)
            return app_exception_response(e)
        except Exception as e:
            # catch - other all error
            return exception_response(e)

    return wrapper


def api_filter_download_file(func):
    '''
    wrap api controller

    Argument:
        func: controller(def)
    Returns:
        controller wrapper
    '''

    def wrapper(*args, **kwargs):
        '''
        controller wrapper

        Argument:
            *args, **kwargs: controller args
        Returns:
            (flask)response
        '''
        try:
            g.applogger.debug("chunk")

            # controller execute and make response
            controller_res = func(*args, **kwargs)

            return make_response_file_download(*controller_res)
        except AppException as e:
            # catch - raise AppException("xxx-xxxxx", log_format, msg_format)
            return app_exception_response(e)
        except Exception as e:
            # catch - other all error
            return exception_response(e)

    return wrapper


def api_filter_download_temporary_file(func):
    '''
    wrap api controller

    Argument:
        func: controller(def)
    Returns:
        controller wrapper
    '''
    def wrapper(*args, **kwargs):
        '''
        controller wrapper

        Argument:
            *args, **kwargs: controller args
        Returns:
            (flask)response
        '''
        try:
            g.applogger.debug("chunk")

            # controller execute and make response
            controller_res = func(*args, **kwargs)

            return make_response_file_download(*controller_res, remove_file=True)
        except AppException as e:
            # catch - raise AppException("xxx-xxxxx", log_format, msg_format)
            return app_exception_response(e)
        except Exception as e:
            # catch - other all error
            return exception_response(e)

    return wrapper


def api_filter_admin(func):
    '''
    wrap api controller

    Argument:
        func: controller(def)
    Returns:
        controller wrapper
    '''

    def wrapper(*args, **kwargs):
        '''
        controller wrapper

        Argument:
            *args, **kwargs: controller args
        Returns:
            (flask)response
        '''
        try:
            g.applogger.debug("[ts={}] controller start -> {}".format(api_timestamp, kwargs))

            # controller execute and make response
            controller_res = func(*args, **kwargs)

            return make_response(*controller_res)
        except AppException as e:
            # catch - raise AppException("xxx-xxxxx", log_format, msg_format)

            # DBが廃止されているとapp_exceptionはログを抑止するので、ここでログだけ出力
            return app_exception_response(e, True)
        except Exception as e:
            # catch - other all error

            # DBが廃止されているとexceptionはログを抑止するので、ここでログだけ出力
            return exception_response(e, True)

    return wrapper


def check_request_body():
    '''
    check wheter request_body is json_format or not
    '''
    if request.content_type:
        request_content_type = request.content_type.lower()
        if request_content_type == "application/json":
            try:
                request.get_json()
            except Exception as e:
                raise AppException("400-00002", ["json_format"], ["json_format"])
        elif "application/x-www-form-urlencoded" == request_content_type:
            if request.form:
                pass
            else:
                raise AppException("400-00003", request_content_type, request_content_type)
        elif "multipart/form-data" in request.content_type:
            if (request.form or request.files):
                pass
            else:
                raise AppException("400-00003", request_content_type, request_content_type)


def check_request_body_key(body, key):
    '''
    check request_body's key for required

    Argument:
        body: (dict) controller arg body
        key:  key for check
    Returns:
        key's value
    '''
    val = body.get(key)
    if val is None:
        raise AppException("400-00002", [key], [key])

    return val
