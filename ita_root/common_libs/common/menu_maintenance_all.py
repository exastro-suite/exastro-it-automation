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


def rest_maintenance_all(objdbca, menu, parameters, file_paths={}):
    """
        メニューのレコード登録/更新(更新/廃止/復活)
        ARGS:
            objdbca:DB接クラス  DBConnectWs()
            menu:メニュー名 string
            parameter:パラメータ  {}
            file_paths:ファイルのパス
        RETRUN:
            statusCode, {}, msg
    """

    result = {}
    result_uuid_list = []

    objmenu = load_table.loadTable(objdbca, menu)  # noqa: F405
    if objmenu.get_objtable() is False:
        status_code = "401-00003"
        log_msg_args = [menu]
        api_msg_args = [menu]
        raise AppException(status_code, log_msg_args, api_msg_args)  # noqa: F405

    status_code, result, msg = objmenu.rest_maintenance_all(parameters, file_paths)

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
    else:
        # 追加・更新データのuuidを返却する #2521
        data_list = objmenu.get_exec_result()
        result_uuid_list = [data['uuid'] for data in data_list if 'uuid' in data]
        result["IdList"] = result_uuid_list

    return result


def create_maintenance_parameters(connexion_request, tmp_path):
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
        bool, parameters, file_paths
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
            except Exception as e:   # noqa: E722
                print_exception_msg(e)

                parameters = connexion_request.form['json_parameters']
                if isinstance(parameters, (list, dict)) is False:
                    return False, [], file_paths

            # check key : parameter
            for _parameter in parameters:
                if 'parameter' not in _parameter:
                    return False, [], file_paths

            # use check index parameters :0-x
            _cnt_parameters = len(parameters) - 1

            # set parameter['file'][rest_name]
            if connexion_request.files:

                # ファイルサイズ確認用変数
                files_count = 0
                args_dict = {}
                check_msg = g.appmsg.get_api_message("MSG-00004", [])

                for _file_key in connexion_request.files:
                    # x.rest_key_name -> x , rest_key_name
                    _tmp_keys = _file_key.split(".")
                    _list_num = int(_tmp_keys[0])
                    _list_key = str(_tmp_keys[1])
                    # check parameters index
                    if _cnt_parameters >= _list_num:
                        _file_data = connexion_request.files[_file_key]
                        file_name = _file_data.filename
                        if _list_num not in file_paths:
                            file_paths[_list_num] = {}
                        tmp_file_path = os.path.join(tmp_path, str(_list_num), _list_key)
                        os.makedirs(tmp_file_path)
                        file_path = os.path.join(tmp_file_path, file_name)
                        file_paths[_list_num][_list_key] = file_path

                        # ファイルを保存できる容量があるかどうか確認
                        _file_data.seek(0,2)
                        file_size = _file_data.tell()
                        _file_data.seek(0)
                        storage = storage_base()
                        can_save, free_space = storage.validate_disk_space(file_size)
                        if can_save is False:
                            file_size_str = f"{int(file_size):,} byte(s)"
                            msg = g.appmsg.get_api_message("499-00222", [file_size_str])
                            args_dict.setdefault(str(files_count), {check_msg: [msg]})
                            args = json.dumps(args_dict)
                            status_code = "499-00201"
                            raise AppException(status_code, [args], [args])

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

    # check parameters
    if len(parameters) == 0:
        return False, [], file_paths

    return True, parameters, file_paths
