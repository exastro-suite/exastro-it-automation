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

import json
import base64
from flask import g  # noqa: F401

from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403


def rest_maintenance(objdbca, menu, parameter, target_uuid, file_paths={}):
    """
        メニューのレコード登録/更新(更新/廃止/復活)
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu:メニュー名 string
            parameter:パラメータ  {}
            target_uuid: 対象レコードID UUID
            file_paths:ファイルのパス
        RETRUN:
            statusCode, {}, msg
    """

    mode = 'nomal'  # noqa: F841
    objmenu = load_table.loadTable(objdbca, menu)  # noqa: F405
    if objmenu.get_objtable() is False:
        status_code = "401-00003"
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    status_code, result, msg = objmenu.rest_maintenance(parameter, target_uuid, file_paths)
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


def create_maintenance_parameters(connexion_request, cmd_type='Register', tmp_path=""):
    """
    create_maintenance_parameters
        Use connexion.request
            - application/json
            -  multipart/form-data, application/x-www-form-urlencoded
        Parameter generation from xxxx
            - application/json
                connexion.request.get_json()
            -  multipart/form-data, application/x-www-form-urlencoded
                connexion.request.form['json_parameters']
                connexion_request.files
            => { "parameter":{}, "file":{} }
    Arguments:
        connexion_request: connexion.request
        cmd_type: cmd_type(Register/Update/Discard/Restore)
    Returns:
        bool, parameters,
    """

    parameters = []
    file_paths = {}

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
            except:   # noqa: E722
                parameters = connexion_request.form['json_parameters']
                if isinstance(parameters, (list, dict)) is False:
                    return False, [], file_paths
            # check key : parameter
            if 'parameter' not in parameters:
                return False, [], file_paths

            # set cmd_type
            parameters.setdefault('type', cmd_type)

            # set parameter['file'][rest_name]
            if connexion_request.files:
                for _file_key in connexion_request.files:
                    _file_data = connexion_request.files[_file_key]
                    file_name = _file_data.filename
                    tmp_file_path = os.path.join(tmp_path, _file_key)
                    retry_makedirs(tmp_file_path)  # noqa: F405
                    file_path = os.path.join(tmp_file_path, file_name)
                    file_paths[_file_key] = file_path

                    f = open(file_path, 'wb')
                    while True:
                        # fileの読み込み
                        buf = _file_data.stream.read(1000000)
                        if len(buf) == 0:
                            break
                        # yield buf
                        # fileの書き込み
                        f.write(buf)
                    f.close()

        else:
            return False, [], file_paths
    else:
        msg_args = [f"Content-Type: {connexion_request.content_type}"]
        raise AppException("400-00001", msg_args, msg_args)
    # check parameters
    if len(parameters) == 0:
        return False, [], file_paths

    return True, parameters, file_paths
