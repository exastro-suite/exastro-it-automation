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
共通関数 module
"""
from flask import g
import secrets
import string
import base64
import codecs
from pathlib import Path
import pytz
import datetime
import re
import os
import requests
import json
import shutil
import inspect
import traceback
from urllib.parse import urlparse

from common_libs.common.exception import AppException
from common_libs.common.encrypt import *
from common_libs.common.storage_access import storage_base, storage_write, storage_write_text, storage_read_text


def ky_encrypt(lcstr, input_encrypt_key=None):
    """
    Encode a string

    Arguments:
        lcstr: Encoding target value
    Returns:
        Encoded string
    """
    if lcstr is None:
        return ""

    if len(lcstr) == 0:
        return ""

    return encrypt_str(lcstr, input_encrypt_key)


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


def ky_file_encrypt(src_file, dest_file):
    """
    Encode a file

    Arguments:
        src_file: Encoding target file
        dest_file: Encoded file
    Returns:
        is success:(bool)
    """
    try:
        # ファイル読み込み
        # #2079 /storage配下は/tmpを経由してアクセスする
        r_obj = storage_read_text()
        lcstr = r_obj.read_text(src_file, encoding="utf-8")

        # エンコード関数呼び出し
        enc_data = ky_encrypt(lcstr)

        # ファイル書き込み
        # #2079 /storage配下は/tmpを経由してアクセスする
        w_obj = storage_write_text()
        w_obj.write_text(dest_file, enc_data, encoding="utf-8")

    except Exception as e:
        msg = "src_file:{} dest_file:{} err_msg:{}".format(src_file, dest_file, e)
        print_exception_msg(msg)
        return False
    finally:
        pass

    return True


def ky_file_decrypt(src_file, dest_file):
    """
    Decode a file

    Arguments:
        src_file: Decoding target file
        dest_file: Decoded file
    Returns:
        is success:(bool)
    """
    try:
        # ファイル読み込み
        # #2079 /storage配下は/tmpを経由してアクセスする
        r_obj = storage_read_text()
        lcstr = r_obj.read_text(src_file, encoding="utf-8")

        # デコード関数呼び出し
        enc_data = ky_decrypt(lcstr)

        # ファイル書き込み
        # #2079 /storage配下は/tmpを経由してアクセスする
        w_obj = storage_write_text()
        w_obj.write_text(dest_file, enc_data, encoding="utf-8")

    except Exception as e:
        msg = "src_file:{} dest_file:{} err_msg:{}".format(src_file, dest_file, e)
        print_exception_msg(msg)
        return False
    finally:
        pass

    return True


def generate_secrets(length=16, punctuation=''):
    """
    generate secrets

    Arguments:
        length: secrets length
        punctuation: symbol used
    Returns:
        (str)secrets value
    """
    # string.ascii_letters - alfabet lower and upper
    # string.digits - number
    # string.punctuation - symbol  !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
    pass_chars = string.ascii_letters + string.digits + punctuation
    secrets_val = ''.join(secrets.choice(pass_chars) for x in range(length))

    return secrets_val


def get_timestamp(is_utc=True):
    """
    get timestamp

    Returns:
        2022-07-01 07:36:24.551751
    """
    return datetime.datetime.now()


def get_iso_datetime(is_utc=True):
    """
    get timestamp for api response format

    Args:
        is_utc (bool):

    Returns:
        2022-08-02T10:26:18.809Z
    """
    return datetime_to_str(datetime.datetime.now())


def datetime_to_str(p_datetime):
    """datetime to string (ISO format)
    Args:
        p_datetime (datetime): datetime
    Returns:
        str: datetime formated string (UTC)
    """
    if p_datetime is None:
        return None

    if p_datetime.tzinfo is None:
        aware_datetime = pytz.timezone(os.environ.get('TZ', 'UTC')).localize(p_datetime)
    else:
        aware_datetime = p_datetime

    utc_datetime = aware_datetime.astimezone(datetime.timezone.utc)
    return utc_datetime.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def stacktrace():
    t = traceback.format_exc()
    return arrange_stacktrace_format(t)


def arrange_stacktrace_format(t):
    """
    stacktrace

    Arguments:
        t: return traceback.format_exc()
    Returns:
        (str)
    """
    retStr = ""

    exception_block_arr = t.split('Traceback (most recent call last):\n')
    # exception_block = exception_block_arr[1]  # most deep exception called
    exception_block_index = 0
    for exception_block in exception_block_arr:
        exception_block = re.sub(r'\n\nDuring handling of the above exception, another exception occurred:\n\n', '', exception_block.strip())
        if exception_block[0:4] != 'File':
            continue

        retStr = retStr + "\n{} : exception block".format(exception_block_index)
        exception_block_index = exception_block_index + 1

        trace_block_arr = re.split('File ', exception_block)
        for trace_block in trace_block_arr:
            row_arr = re.split('\n', str(trace_block.strip()))
            row_index = 0
            row_str = ""
            length = len(row_arr) - 1
            if length == 0:
                continue

            for row in row_arr:

                if row_index == 0:
                    row_str = "\n -> " + row
                elif row_index == 1:
                    row_str = row_str + ", " + row.strip()
                    retStr = retStr + row_str
                elif row_index == 2:
                    retStr = retStr + "\n " + row.strip()

                row_index = row_index + 1

    return retStr


def file_encode(file_path):
    """
    Encode a file to base64

    Arguments:
        file_path: Encoding target filepath
    Returns:
        Encoded string
    """

    is_file = os.path.isfile(file_path)
    if not is_file:
        return ""

    # #2079 /storage配下は/tmpを経由してアクセスする
    obj = storage_base()
    storage_flg = obj.path_check(file_path)
    if storage_flg is True:
        # /storage
        tmp_file_path = obj.make_temp_path(file_path)
        # /storageから/tmpにコピー
        i = 0
        while True:
            # issue2432対策。azureストレージの初回アクセス時に、不規則に「FileNotFoundError: [Errno 2] No such file or directory」が出るため、一度だけリトライを行う
            i = i + 1
            try:
                shutil.copy2(file_path, tmp_file_path)
                break
            except Exception as e:
                g.applogger.info("copy failed. file_path={}, tmp_file_path={}".format(file_path, tmp_file_path))
                if i == 2:
                    raise e
                t = traceback.format_exc()
                g.applogger.info(arrange_stacktrace_format(t))
    else:
        # not /storage
        tmp_file_path = file_path
    # ファイル読み込み
    with open(tmp_file_path, "rb") as f:
        read_value = base64.b64encode(f.read()).decode()
    f.close()

    if storage_flg is True:
        if os.path.isfile(tmp_file_path) is True:
            os.remove(tmp_file_path)

    return read_value


def file_decode(file_path):
    """
    Encode a file to base64

    Arguments:
        file_path: Encoding target filepath
    Returns:
        Encoded string
    """
    is_file = os.path.isfile(file_path)
    if not is_file:
        return ""

    # #2079 /storage配下は/tmpを経由してアクセスする
    obj = storage_base()
    storage_flg = obj.path_check(file_path)
    if storage_flg is True:
        # /storage
        tmp_file_path = obj.make_temp_path(file_path)
        # /storageから/tmpにコピー
        shutil.copy2(file_path, tmp_file_path)
    else:
        # not /storage
        tmp_file_path = file_path

    with open(tmp_file_path, "rb") as f:
        text = f.read().decode()
    f.close()

    if storage_flg is True:
        # /tmpゴミ掃除
        if os.path.isfile(tmp_file_path) is True:
            os.remove(tmp_file_path)

    text_decrypt = ky_decrypt(text)
    return base64.b64encode(text_decrypt.encode()).decode()


def get_upload_file_path(workspace_id, menu_id, uuid, column_name_rest, file_name, uuid_jnl):
    """
    Get filepath

    Arguments:
        workspace_id: workspace_id
        menu_id: menu_id
        uuid: uuid
        column_name_rest: column_name_rest
        file_name: Target file name
        uuid_jnl: uuid_jnl
    Returns:
        filepath
    """
    organization_id = g.get("ORGANIZATION_ID")
    file_path = "/storage/{}/{}/uploadfiles/{}/{}/{}/{}".format(organization_id, workspace_id, menu_id, column_name_rest, uuid, file_name)
    old_file_path = ""
    if uuid_jnl is not None:
        if len(uuid_jnl) > 0:
            old_file_path = "/storage/{}/{}/uploadfiles/{}/{}/{}/old/{}/{}".format(organization_id, workspace_id, menu_id, column_name_rest, uuid, uuid_jnl, file_name)  # noqa: E501

    return {"file_path": file_path, "old_file_path": old_file_path}


def get_upload_file_path_specify(workspace_id, place, uuid, file_name, uuid_jnl):
    """
    Get filepath

    Arguments:
        workspace_id: workspace_id
        place: Target file place
        uuid: uuid
        file_name: Target file name
        uuid_jnl: uuid_jnl
    Returns:
        filepath
    """
    organization_id = g.get("ORGANIZATION_ID")
    file_path = "/storage/{}/{}{}/{}/{}".format(organization_id, workspace_id, place, uuid, file_name)
    old_file_path = ""
    if uuid_jnl is not None:
        if len(uuid_jnl) > 0:
            old_file_path = "/storage/{}/{}{}/{}/old/{}/{}".format(organization_id, workspace_id, place, uuid, uuid_jnl, file_name)  # noqa: E501

    return {"file_path": file_path, "old_file_path": old_file_path}


def upload_file(file_path, text, mode="bw"):
    """
    Upload a file

    Arguments:
        file_path: Target filepath
        text: file text
    Returns:
        is success:(bool)
    """
    path = os.path.dirname(file_path)

    if type(text) is bytes:
        text = base64.b64decode(text.encode()).decode()

    if isinstance(text, str):
        text = base64.b64decode(text.encode())

    if not os.path.isdir(path):
        os.makedirs(path)

    try:
        # #2079 /storage配下は/tmpを経由してアクセスする
        obj = storage_write()
        fd = obj.open(file_path, mode)
        obj.write(text)
        obj.close()

    except Exception as e:
        msg = "file_path:{} err_msg:{}".format(file_path, e)
        print_exception_msg(msg)
        return False

    return True


def encrypt_upload_file(file_path, text, mode="w"):
    """
    Encode and upload file

    Arguments:
        file_path: Target filepath
        text: file text
    Returns:
        is success:(bool)
    """
    try:
        text = base64.b64decode(text.encode()).decode()
        text = ky_encrypt(text)
    except Exception as e:
        msg = "file_path:{} err_msg:{}".format(file_path, e)
        print_exception_msg(msg)
        return False

    path = os.path.dirname(file_path)

    if not os.path.isdir(path):
        os.makedirs(path)

    try:
        # #2079 /storage配下は/tmpを経由してアクセスする
        obj = storage_write()
        fd = obj.open(file_path, mode)
        obj.write(text)
        obj.close()

    except Exception as e:
        msg = "file_path:{} err_msg:{}".format(file_path, e)
        print_exception_msg(msg)
        return False

    return True


def get_exastro_platform_workspaces():
    """
    ユーザが所属するworkspaceの一覧と、操作中のworkspaceに所属する環境をExastroPlatformに問い合わせて取得する

    Arguments:
        None
    Returns:
        workspaces:(list)
        environments:(list)
    """
    organization_id = g.get('ORGANIZATION_ID')
    workspace_id = g.get('WORKSPACE_ID')
    host_name = os.environ.get('PLATFORM_API_HOST')
    port = os.environ.get('PLATFORM_API_PORT')
    user_id = g.get('USER_ID')
    language = g.get('LANGUAGE')
    workspaces = {}
    environments_list = []
    environments = []

    header_para = {
        "Content-Type": "application/json",
        "User-Id": user_id,
        "Roles": json.dumps(g.ROLES),
        "Language": language
    }

    # 2回目以降の検索はgの値を使用する
    if organization_id == g.get("PLATFORM_WORKSPACES_ORG") and workspace_id == g.get("PLATFORM_WORKSPACES_WS") and user_id == g.get("PLATFORM_WORKSPACES_USER"):  # noqa: E501
        workspaces = g.get('PLATFORM_WORKSPACES')
        environments = g.get('PLATFORM_ENVIRONMENTS')

    else:
        # API呼出
        api_url = "http://{}:{}/internal-api/{}/platform/users/{}/workspaces".format(host_name, port, organization_id, user_id)
        request_response = requests.get(api_url, headers=header_para)

        response_data = json.loads(request_response.text)

        if request_response.status_code != 200:
            raise AppException('999-00005', [api_url, response_data])

        # workspaceの一覧を取得
        for record in response_data['data']:
            workspaces[record['id']] = record['name']
            if workspace_id == record['id']:
                if 'informations' in record and 'environments' in record['informations']:
                    environments_list = record['informations']['environments']

        for value in environments_list:
            environments.append(value['name'])

        # gに値を設定しておく
        g.PLATFORM_WORKSPACES = workspaces
        g.PLATFORM_ENVIRONMENTS = environments

        g.PLATFORM_WORKSPACES_ORG = organization_id
        g.PLATFORM_WORKSPACES_WS = workspace_id
        g.PLATFORM_WORKSPACES_USER = user_id

    return workspaces, environments


def get_workspace_roles():
    """
    workspaceに所属するロールの一覧をExastroPlatformに問い合わせて取得する

    Arguments:
        None
    Returns:
        roles:(list)
    """
    organization_id = g.get('ORGANIZATION_ID')
    workspace_id = g.get('WORKSPACE_ID')
    host_name = os.environ.get('PLATFORM_API_HOST')
    port = os.environ.get('PLATFORM_API_PORT')
    user_id = g.get('USER_ID')
    language = g.get('LANGUAGE')
    roles = []

    header_para = {
        "Content-Type": "application/json",
        "User-Id": user_id,
        "Roles": json.dumps(g.ROLES),
        "Language": language
    }

    # 2回目以降の検索はgの値を使用する
    if organization_id == g.get("WORKSPACE_ROLES_ORG") and workspace_id == g.get("WORKSPACE_ROLES_WS"):
        roles = g.get('WORKSPACE_ROLES')

    else:
        # API呼出
        api_url = "http://{}:{}/internal-api/{}/platform/workspaces/{}/roles".format(host_name, port, organization_id, workspace_id)
        request_response = requests.get(api_url, headers=header_para)

        response_data = json.loads(request_response.text)

        if request_response.status_code != 200:
            raise AppException('999-00005', [api_url, response_data])

        # workspaceの一覧を取得
        for record in response_data['data']:
            roles.append(record['name'])

        # gに値を設定しておく
        g.WORKSPACE_ROLES = roles

        g.WORKSPACE_ROLES_ORG = organization_id
        g.WORKSPACE_ROLES_WS = workspace_id

    return roles


def get_exastro_platform_users():
    """
    workspaceに所属するユーザの一覧をExastroPlatformに問い合わせて取得する

    Arguments:
        None
    Returns:
        users:(list)
    """
    organization_id = g.get('ORGANIZATION_ID')
    workspace_id = g.get('WORKSPACE_ID')
    host_name = os.environ.get('PLATFORM_API_HOST')
    port = os.environ.get('PLATFORM_API_PORT')
    user_id = g.get('USER_ID')
    language = g.get('LANGUAGE')
    users = {}

    if "ROLES" in g:
        roles = g.ROLES
    else:
        roles = ""

    header_para = {
        "Content-Type": "application/json",
        "User-Id": user_id,
        "Roles": json.dumps(roles),
        "Language": language
    }

    # 2回目以降の検索はgの値を使用する
    if organization_id == g.get("PLATFORM_USERS_ORG") and workspace_id == g.get("PLATFORM_USERS_WS"):
        users = g.get('PLATFORM_USERS')

    else:
        # API呼出
        api_url = "http://{}:{}/internal-api/{}/platform/workspaces/{}/users".format(host_name, port, organization_id, workspace_id)
        request_response = requests.get(api_url, headers=header_para)

        response_data = json.loads(request_response.text)

        if request_response.status_code != 200:
            raise AppException('999-00005', [api_url, response_data])

        # workspaceの一覧を取得
        for record in response_data['data']:
            users[record['id']] = record['name']

        # gに値を設定しておく
        g.PLATFORM_USERS = users
        g.PLATFORM_USERS_ORG = organization_id
        g.PLATFORM_USERS_WS = workspace_id

    return users


def get_user_name(user_id):
    """
    ユーザIDを元にユーザ名を取得する

    Arguments:
        user_id: ユーザID
    Returns:
        user_name: (string)
    """
    user_name = ""
    users = get_exastro_platform_users()

    if user_id in users:
        user_name = users[user_id]
    else:
        status_code = 'MSG-00001'
        user_name = g.appmsg.get_api_message(status_code, [user_id])

    return user_name


def get_all_execution_limit(limit_key):
    """
    システム全体の同時実行数最大値取得

    Returns:
        limit値
    """
    host_name = os.environ.get('PLATFORM_API_HOST')
    port = os.environ.get('PLATFORM_API_PORT')

    header_para = {
        "Content-Type": "application/json",
        "User-Id": "dummy",
    }

    # API呼出
    api_url = "http://{}:{}/internal-api/platform/settings/common".format(host_name, port)
    request_response = requests.get(api_url, headers=header_para)

    response_data = json.loads(request_response.text)

    if request_response.status_code != 200:
        raise AppException('999-00005', [api_url, response_data])

    # システム全体の同時実行数最大値取得
    limit = 0
    for record in response_data['data']:
        if record["key"] == limit_key:
            limit = record["value"]

    return limit


def get_org_execution_limit(limit_key):
    """
    Organization毎の同時実行数最大値取得

    Returns:
        limit値
    """
    host_name = os.environ.get('PLATFORM_API_HOST')
    port = os.environ.get('PLATFORM_API_PORT')

    header_para = {
        "Content-Type": "application/json",
        "User-Id": "dummy",
        "Roles": "dummy",
        "Language": g.get('LANGUAGE')
    }

    # API呼出
    api_url = "http://{}:{}/internal-api/platform/limits".format(host_name, port)
    request_response = requests.get(api_url, headers=header_para)

    response_data = json.loads(request_response.text)

    if request_response.status_code != 200:
        raise AppException('999-00005', [api_url, response_data])

    # システム全体の同時実行数最大値取得
    limit_list = {}
    for record in response_data['data']:
        if limit_key in record["limits"]:
            limit_list[record["organization_id"]] = record["limits"][limit_key]
        else:
            limit_list[record["organization_id"]] = 0

    return limit_list


def get_org_upload_file_size_limit():
    """
    Organization毎のアップロードファイルサイズ上限取得

    Returns:
        org_upload_file_size_limit: Organization毎のアップロードファイルサイズ上限
    """

    if 'ORG_UPLOAD_FILE_SIZE_LIMIT' in g:
        org_upload_file_size_limit = g.get('ORG_UPLOAD_FILE_SIZE_LIMIT')

    else:
        host_name = os.environ.get('PLATFORM_API_HOST')
        port = os.environ.get('PLATFORM_API_PORT')
        limit_key = 'ita.organization.common.upload_file_size_limit'

        header_para = {
            "Content-Type": "application/json",
            "User-Id": "dummy",
            "Roles": "dummy",
            "Language": g.get('LANGUAGE')
        }

        # API呼出
        api_url = "http://{}:{}/internal-api/platform/limits".format(host_name, port)
        request_response = requests.get(api_url, headers=header_para)

        response_data = json.loads(request_response.text)

        if request_response.status_code != 200:
            raise AppException('999-00005', [api_url, response_data])

        # Organization毎のアップロードファイルサイズ上限取得
        org_upload_file_size_limit = None
        for record in response_data['data']:
            if g.ORGANIZATION_ID in record['organization_id']:
                if limit_key in record["limits"]:
                    org_upload_file_size_limit = record["limits"][limit_key]
                    break

        # gに値を設定しておく
        g.ORG_UPLOAD_FILE_SIZE_LIMIT = org_upload_file_size_limit

    return org_upload_file_size_limit


def create_dirs(config_file_path, dest_dir):
    """
    config_file_pathのファイルに記載されているディレクトリをdest_dir配下に作成する

    Arguments:
        config_file_path: 設定ファイル
        dest_dir: 作成するディレクトリ
    Returns:
        is success:(bool)
    """
    # #2079 /storage配下ではないので対象外
    with open(config_file_path) as f:
        lines = f.readlines()

    for target_path in lines:
        target_path = target_path.replace("\n", "")
        try:
            os.makedirs(dest_dir + target_path)
        except FileExistsError:
            pass
    return True


def put_uploadfiles(config_file_path, src_dir, dest_dir):
    """
    config_file_pathのファイルに記載されているファイルをdest_dir配下に作成する

    Arguments:
        config_file_path: 設定ファイル
        src_dir: コピー元のファイル格納ディレクトリ
        dest_dir: 作成するディレクトリ
    Returns:
        is success:(bool)
    """
    # #2079 /storage配下ではないので対象外
    with open(config_file_path, 'r') as material_conf_json:
        material_conf = json.load(material_conf_json)
        for menu_id, file_info_list in material_conf.items():
            for file_info in file_info_list:
                for file, copy_cfg in file_info.items():
                    # org_file = src_dir + "/".join([menu_id, file])
                    org_file = os.path.join(os.path.join(src_dir, menu_id), file)
                    old_file_path = os.path.join(dest_dir, menu_id) + copy_cfg[0]
                    file_path = os.path.join(dest_dir, menu_id) + copy_cfg[1]

                    if not os.path.isdir(old_file_path):
                        os.makedirs(old_file_path)

                    shutil.copy(org_file, old_file_path + file)
                    try:
                        os.symlink(old_file_path + file, file_path + file)
                    except FileExistsError:
                        pass

    return True


def get_maintenance_mode_setting():
    """
    メンテナンスモードの状態を取得する

    Returns:
        maintenance_mode
    """
    host_name = os.environ.get('PLATFORM_API_HOST')
    port = os.environ.get('PLATFORM_API_PORT')

    header_para = {
        "Content-Type": "application/json",
        "User-Id": "dummy",
    }

    # API呼出
    api_url = "http://{}:{}/internal-api/platform/maintenance-mode-setting".format(host_name, port)
    request_response = requests.get(api_url, headers=header_para)

    response_data = json.loads(request_response.text)

    if request_response.status_code != 200:
        raise AppException('999-00005', [api_url, response_data])

    # メンテナンスモードの設定値を取得
    maintenance_mode = response_data.get('data')

    return maintenance_mode


def url_check(url_string, scheme='', path=False, params=False, query=False, fragment=False, username=False, password=False, port=False):
    # urlを解析
    try:
        parse_obj = urlparse(url_string, scheme='', allow_fragments=True)

        assert len(parse_obj.scheme) > 0, "scheme"
        assert len(parse_obj.netloc) > 0, "netloc"  # ネットワーク上の位置（hostname:port）
        assert parse_obj.hostname is not None, "hostname"  # ホスト名 (小文字)
        if path is True:
            assert  len(parse_obj.path) > 0, "path"  # 階層的パス
        if params is True:
            assert len(parse_obj.params) > 0, "params"  # 最後のパス要素に対するパラメータ
        if query is True:
            assert len(parse_obj.query) > 0, "query"  # クエリ要素
        if fragment is True:
            assert len(parse_obj.fragment) > 0, "fragment"  # フラグメント識別子
        if username is True:
            assert parse_obj.username is not None, "username"  # ユーザ名
        if password is True:
            assert parse_obj.password is not None, "password"  # パスワード
        if port is True:
            assert parse_obj.port is not None, "port"  # ポート番号を表わす整数 (もしあれば)
    except Exception as e:
        return False, e

    return True, parse_obj


def print_exception_msg(e):
    """
    例外メッセージを、infoログに出力する
    """

    # 例外と、発生したファイ名と行番号を出力
    info = inspect.getouterframes(inspect.currentframe())[1]
    msg_line = "({}:{})".format(os.path.basename(info.filename), info.lineno)
    exception_msg = "exception_msg='{}'".format(e)
    g.applogger.info('[timestamp={}] {} {}'.format(get_iso_datetime(), exception_msg, msg_line))

