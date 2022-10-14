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
exception module for application
"""


class AppException(Exception):
    """
    exception class for application
    """
    def __init__(self, *args):
        """
        constructor
            make AppException args (result_code, log_msg_args, api_msg_args)

        Arguments:
            result_code: "500-0001"
            log_msg_args: list for message args
            api_msg_args: list for message args
        """
        api_msg_args = []
        log_msg_args = []

        if len(args) == 3:
            result_code, log_msg_args, api_msg_args = args
        elif len(args) == 2:
            result_code, log_msg_args = args
        else:
            result_code = args[0]

        # set args
        self.args = result_code, log_msg_args, api_msg_args

    # def __str__(self):


class ValidationException(Exception):
    """
    exception class for application
    """

    def __init__(self, *args):
        """
        constructor
            make class ValidationException args (msg_code, parameter)

        Arguments:
            msg_code: メッセージコード
            parameter: パラメーター
        """
        msg_code = ""
        parameter = []

        if len(args) == 2:
            msg_code, parameter = args
        else:
            msg_code = args[0]

        # set args
        self.args = msg_code, parameter
