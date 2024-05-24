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
import json
import base64

from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403


def rest_maintenance_all(objdbca, menu, parameters):
    """
        メニューのレコード登録/更新(更新/廃止/復活)
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu:メニュー名 string
            parameter:パラメータ  {}
            target_uuid: 対象レコードID UUID
            lang: 言語情報 ja / en
        RETRUN:
            statusCode, {}, msg
    """

    result = {}

    objmenu = load_table.loadTable(objdbca, menu)  # noqa: F405
    if objmenu.get_objtable() is False:
        status_code = "401-00003"
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    status_code, result, msg = objmenu.rest_maintenance_all(parameters)

    if status_code != '000-00000':
        if status_code is None:
            status_code = '999-99999'
        elif len(status_code) == 0:
            status_code = '999-99999'
        if isinstance(msg, list):
            log_msg_args = msg
            api_msg_args = msg
        else:
            log_msg_args = [msg]
            api_msg_args = [msg]
        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    return result


def create_maintenance_parameters(connexion_request):
    """
    create_maintenance_parameters
        Use connexion.request
            - application/json
            - multipart/form-data, application/x-www-form-urlencoded
        Parameter generation from xxxx
            - application/json
                connexion.request.get_json()
            - multipart/form-data, application/x-www-form-urlencoded
                connexion.request.form['json_parameters']
                connexion_request.files
            => [{ "parameter":{}, "file":{} }]
    Arguments:
        connexion_request: connexion.request
    Returns:
        bool, parameters,
    """

    parameters = []

    # get parameters
    if connexion_request.is_json:
        # application/json
        parameters = connexion_request.get_json()
    elif connexion_request.form:
        # multipart/form-data, application/x-www-form-urlencoded
        # check key : json_parameters
        if 'json_parameters' in connexion_request.form:
            # json.loads
            try:
                parameters = json.loads(connexion_request.form['json_parameters'])
            except Exception as e:   # noqa: E722
                print_exception_msg(e)

                parameters = connexion_request.form['json_parameters']
                if isinstance(parameters, (list, dict)) is False:
                    return False, [],

            # check key : parameter
            for _parameter in parameters:
                if 'parameter' not in _parameter:
                    return False, [],

            # use check index parameters :0-x
            _cnt_parameters = len(parameters) - 1

            # set parameter['file'][rest_name]
            if connexion_request.files:
                for _file_key in connexion_request.files:
                    # x.rest_key_name -> x , rest_key_name
                    _tmp_keys = _file_key.split(".")
                    _list_num = int(_tmp_keys[0])
                    _list_key = str(_tmp_keys[1])
                    # check parameters index
                    if _cnt_parameters >= _list_num:
                        # set listno->file->rest_key_name->filedata(base64)
                        _file_data = connexion_request.files[_file_key]
                        _str_b64_file_data = base64.b64encode(_file_data.stream.read()).decode()
                        parameters[_list_num].setdefault('file', {})
                        parameters[_list_num]['file'][_list_key] = _str_b64_file_data
        else:
            return False, [],

    # check parameters
    if len(parameters) == 0:
        return False, [],

    return True, parameters,
