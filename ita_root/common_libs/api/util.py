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
from flask import g, request
import traceback

from common_libs.common.exception import AppException
from common_libs.common.util import get_iso_datetime, arrange_stacktrace_format

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

    log_status = "success" if result_code == "000-00000" else "error"
    g.applogger.debug("[ts={}]response={}".format(api_timestamp, (res_body, status_code)))
    g.applogger.info("[ts={}][api-end][{}][status_code={}]".format(api_timestamp, log_status, status_code))
    return res_body, status_code


def app_exception_response(e):
    '''
    make response when AppException occured
    
    Argument:
        e: AppException
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

    g.applogger.error("[ts={}][error] {}".format(api_timestamp, log_msg))
    return make_response(None, api_msg, result_code, status_code)


def exception_response(e):
    '''
    make response when Exception occured
    
    Argument:
        e: Exception
    Returns:
        (flask)response
    '''
    args = e.args
    is_arg = False
    while is_arg is False:
        if isinstance(args[0], AppException):
            return app_exception_response(args[0])
        elif isinstance(args[0], Exception):
            args = args[0].args
        else:
            is_arg = True

    # catch - other all error
    t = traceback.format_exc()
    # g.applogger.exception("[error][ts={}]".format(api_timestamp))
    g.applogger.error("[ts={}][error] {}".format(api_timestamp, arrange_stacktrace_format(t)))

    api_msg = g.appmsg.get_api_message("999-99999")
    return make_response(None, api_msg, "999-99999", 500)


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


def check_request_body():
    '''
    check wheter request_body is json_format or not
    '''
    if request.content_type == "application/json":
        try:
            request.get_json()
        except Exception:
            raise AppException("400-00002", ["json_format"], ["json_format"])


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
