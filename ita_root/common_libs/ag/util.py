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
common_libs agent common function module
"""
from flask import g
import traceback

from common_libs.common.exception import AppException
from common_libs.common.util import arrange_stacktrace_format, print_exception_msg
from common_libs.common.encrypt import *


def app_exception(e):
    '''
    called when AppException occured

    Argument:
        e: AppException
    '''
    args = e.args
    is_arg = False
    while is_arg is False:
        if isinstance(args[0], AppException):
            args = args[0].args
        elif isinstance(args[0], Exception):
            return exception(args[0])
        else:
            is_arg = True

    # catch - other all error
    t = traceback.format_exc()
    g.applogger.info(arrange_stacktrace_format(t))

    # catch - raise AppException("xxx-xxxxx", log_format), and get message
    result_code, log_msg_args, api_msg_args = args
    log_msg = g.appmsg.get_log_message(result_code, log_msg_args)
    g.applogger.info(log_msg)


def exception(e):
    '''
    called when Exception occured

    Argument:
        e: Exception
    '''
    args = e.args
    is_arg = False
    while is_arg is False:
        if isinstance(args[0], AppException):
            return app_exception(args[0])
        elif isinstance(args[0], Exception):
            args = args[0].args
        else:
            is_arg = True

    # catch - other all error
    t = traceback.format_exc()
    g.applogger.error(arrange_stacktrace_format(t))

def ky_decrypt(lcstr, input_encrypt_key=None):
    """
    Decode a string

    Arguments:
        lcstr: Decoding target value
    Returns:
        Decoded string
    """

    if lcstr is None:
        return ""

    if len(str(lcstr)) == 0:
        return ""

    # パラメータシート更新で任意の項目からパスワード項目に変更した場合システムエラーになるので、
    # try~exceptで対応する
    try:
        return decrypt_str(lcstr, input_encrypt_key)
    except Exception as e:
        print_exception_msg(e)
        return ""