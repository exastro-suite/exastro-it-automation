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


from common_libs.common.util import ky_decrypt
from common_libs.ansible_driver.functions.ansibletowerlibs import AnsibleTowerCommonLib as FuncCommonLib
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiBase import AnsibleTowerRestApiBase

class AnsibleTowerRestApiCredentials(AnsibleTowerRestApiBase):

    """
    【概要】
        AnsibleTower RestApi Credential系を呼ぶ クラス
    """

    API_PATH = "credentials/"
    IDENTIFIED_NAME_PREFIX = "ita_%s_executions_credential_%s_%s"
    PREPARE_BUILD_CREDENTIAL_NAME = "ita_executions_local"
    VAULT_IDENTIFIED_NAME_PREFIX = "ita_%s_executions_vault_credential_%s"

    GIT_IDENTIFIED_NAME_PREFIX = "ita_%s_executions_git_credential_%s"

    MACHINE = 1
    SRC_CONTROL = 2
    VAULT = 3

    @classmethod
    def getAll(cls, RestApiCaller, query=""):

        # REST APIアクセス
        method = "GET"
        response_array = RestApiCaller.restCall(method, '%s%s' % (cls.API_PATH, query))

        # REST失敗
        if response_array['statusCode'] != 200:
            response_array['success'] = False
            return response_array

        # REST成功
        response_array['success'] = True
        response_array['responseContents'] = response_array['responseContents']['results']

        return response_array

    @classmethod
    def get(cls, RestApiCaller, id):

        # REST APIアクセス
        method = "GET"
        response_array = RestApiCaller.restCall(method, '%s%s/' % (cls.API_PATH, id))

        # REST失敗
        if response_array['statusCode'] != 200:
            response_array['success'] = False
            return response_array

        # REST成功
        response_array['success'] = True

        return response_array

    @classmethod
    def post(cls, RestApiCaller, param):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # content生成
        content = {}
        response_array = {}

        if  'execution_no' in param and param['execution_no'] \
        and 'loopCount' in param and param['loopCount']:
            content['name'] = cls.IDENTIFIED_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(param['execution_no']), FuncCommonLib.addPadding(param['loopCount']))

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'execution_no' and 'loopCount'."
            }
            return response_array

        if 'organization' in param and param['organization']:
            content['organization'] = param['organization']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'organization'."
            }
            return response_array

        if 'credential_type_id' in param and param['credential_type_id']:
            content['credential_type'] = param['credential_type_id']

        if 'username' in param and param['username']:
            if 'inputs' not in content:
                content['inputs'] = {}

            content['inputs']['username'] = param['username']

        if 'password' in param and param['password']:
            if 'inputs' not in content:
                content['inputs'] = {}

            content['inputs']['password'] = ky_decrypt(param['password'])

        if 'ssh_private_key' in param and param['ssh_private_key']:
            if 'inputs' not in content:
                content['inputs'] = {}

            content['inputs']['ssh_key_data'] = param['ssh_private_key']

        if 'ssh_private_key_pass' in param and param['ssh_private_key_pass']:
            if 'inputs' not in content:
                content['inputs'] = {}

            content['inputs']['ssh_key_unlock'] = param['ssh_private_key_pass']

        # REST APIアクセス
        method = "POST"
        response_array = RestApiCaller.restCall(method, cls.API_PATH, content)

        # REST失敗
        if response_array['statusCode'] != 201:
            response_array['success'] = False
            if "errorMessage" not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = "status_code not 201. =>%s" % (response_array['statusCode'])

            return response_array

        # REST成功
        response_array['success'] = True

        return response_array

    @classmethod
    def delete(cls, RestApiCaller, id):

        # REST APIアクセス
        method = "DELETE"
        response_array = RestApiCaller.restCall(method, '%s%s/' % (cls.API_PATH, id))

        # REST失敗
        if response_array['statusCode'] != 204:
            response_array['success'] = False
            if "errorMessage" not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = "status_code not 204. =>%s" % (response_array['statusCode'])

            return response_array

        # REST成功
        response_array['success'] = True

        return response_array

    @classmethod
    def deleteRelatedCurrnetExecution(cls, RestApiCaller, execution_no):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # データ絞り込み
        filteringName = cls.IDENTIFIED_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no), '')
        query = "?name__startswith=%s" % (filteringName)
        pickup_response_array = cls.getAll(RestApiCaller, query)
        if not pickup_response_array['success']:
            return pickup_response_array

        for credentialData in pickup_response_array['responseContents']:
            response_array = cls.delete(RestApiCaller, credentialData['id'])
            if not response_array['success']:
                return response_array

        return pickup_response_array  # データ不足しているが、後続の処理はsuccessしか確認しないためこのまま

    @classmethod
    def git_post(cls, RestApiCaller, param):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # content生成
        content = {}
        response_array = {}

        if 'execution_no' in param and param['execution_no']:
            content['name'] = cls.GIT_IDENTIFIED_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(param['execution_no']))

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'execution_no'."
            }
            return response_array

        if 'organization' in param and param['organization']:
            content['organization'] = param['organization']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'organization'."
            }
            return response_array

        content['inputs'] = {}
        if 'username' in param and param['username']:
            content['inputs']['username'] = param['username']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'username'."
            }
            return response_array

        if 'ssh_key_data' in param and param['ssh_key_data']:
            content['inputs']['ssh_key_data'] = param['ssh_key_data']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'ssh_key_data'."
            }
            return response_array

        if 'ssh_key_unlock' in param and param['ssh_key_unlock']:
            content['inputs']['ssh_key_unlock'] = param['ssh_key_unlock']

        content['credential_type'] = cls.SRC_CONTROL  # ソースコントロール

        # REST APIアクセス
        method = "POST"
        response_array = RestApiCaller.restCall(method, cls.API_PATH, content)

        # REST失敗
        if response_array['statusCode'] != 201:
            response_array['success'] = False
            if "errorMessage" not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = "status_code not 201. =>%s" % (response_array['statusCode'])

            return response_array

        # REST成功
        response_array['success'] = True

        return response_array

    @classmethod
    def vault_post(cls, RestApiCaller, param):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # content生成
        content = {}
        response_array = {}

        if 'execution_no' in param and param['execution_no']:
            content['name'] = cls.VAULT_IDENTIFIED_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(param['execution_no']))

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'execution_no'."
            }
            return response_array

        if 'organization' in param and param['organization']:
            content['organization'] = param['organization']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'organization'."
            }
            return response_array

        if 'vault_password' in param and param['vault_password']:
            content['inputs'] = {}
            content['inputs']['vault_password'] = param['vault_password']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'vault_password'."
            }
            return response_array

        content['credential_type'] = cls.VAULT  # vault

        # REST APIアクセス
        method = "POST"
        response_array = RestApiCaller.restCall(method, cls.API_PATH, content)

        # REST失敗
        if response_array['statusCode'] != 201:
            response_array['success'] = False
            if "errorMessage" not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = "status_code not 201. =>%s" % (response_array['statusCode'])

            return response_array

        # REST成功
        response_array['success'] = True

        return response_array

    @classmethod
    def deleteVault(cls, RestApiCaller, execution_no):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # データ絞り込み
        filteringName = cls.VAULT_IDENTIFIED_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no))
        query = "?name__startswith=%s" % (filteringName)
        pickup_response_array = cls.getAll(RestApiCaller, query)
        if not pickup_response_array['success']:
            return pickup_response_array

        for credentialData in pickup_response_array['responseContents']:
            response_array = cls.delete(RestApiCaller, credentialData['id'])
            if not response_array['success']:
                return response_array

        return pickup_response_array  # データ不足しているが、後続の処理はsuccessしか確認しないためこのまま

    @classmethod
    def deleteGit(cls, RestApiCaller, execution_no):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # データ絞り込み
        filteringName = cls.GIT_IDENTIFIED_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no))
        query = "?name__startswith=%s" % (filteringName)
        pickup_response_array = cls.getAll(RestApiCaller, query)
        if not pickup_response_array['success']:
            return pickup_response_array

        for credentialData in pickup_response_array['responseContents']:
            response_array = cls.delete(RestApiCaller, credentialData['id'])
            if not response_array['success']:
                return response_array

        return pickup_response_array  # データ不足しているが、後続の処理はsuccessしか確認しないためこのまま

