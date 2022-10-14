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

from common_libs.ansible_driver.functions.ansibletowerlibs import AnsibleTowerCommonLib as FuncCommonLib
from common_libs.ansible_driver.classes.AnsrConstClass import AnscConst
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiBase import AnsibleTowerRestApiBase


class AnsibleTowerRestApiJobTemplates(AnsibleTowerRestApiBase):

    """
    【概要】
        AnsibleTower RestApi JobTemplate系を呼ぶ クラス
    """

    API_PATH = "job_templates/"
    IDENTIFIED_NAME_PREFIX = "ita_%s_executions_jobtpl_%s_%s"
    PREPARE_BUILD_NAME_PREFIX = "ita_%s_executions_prepare_build_%s"
    API_SUB_PATH_LAUNCH = "launch/"
    LAUNCH_PLAYBOOK_NAME = "site.yml"
    CLEANUP_PREPARED_BUILD_NAME_PREFIX = "ita_%s_executions_cleanup_%s"
    SEARCH_NAME_PREFIX = "ita_%s_executions_jobtpl_%s_"

    SEARCH_IDENTIFIED_NAME_PREFIX = "ita_%s_executions_jobtpl_%s"

    CREDENTIALS_ADD_API_PATH = "job_templates/%s/credentials/"

    @classmethod
    def getAll(cls, RestApiCaller, query=""):

        # REST APIアクセス
        method = "GET"
        response_array = RestApiCaller.restCall(method, '%s%s' % (cls.API_PATH, query))

        # REST失敗
        if response_array['statusCode'] != 200:
            response_array['success'] = False
            if "errorMessage" not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = "status_code not 200. =>%s" % (response_array['statusCode'])

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
            if "errorMessage" not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = "status_code not 200. =>%s" % (response_array['statusCode'])

            return response_array

        # REST成功
        response_array['success'] = True

        return response_array

    @classmethod
    def post(cls, RestApiCaller, param, addparam={}):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # content生成
        content = {}
        response_array = {}

        if  'execution_no' in param and param['execution_no'] \
        and 'loopCount' in param and param['loopCount']:
            content['name'] = cls.IDENTIFIED_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(param['execution_no']), FuncCommonLib.addPadding(param['loopCount']))

        else:
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'execution_no' and 'loopCount'."
            }
            return response_array

        if  'inventory' in param and param['inventory']:
            content['inventory'] = param['inventory']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'inventory'."
            }
            return response_array

        if  'project' in param and param['project']:
            content['project'] = param['project']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'project'."
            }
            return response_array

        if  'playbook' in param and param['playbook']:
            content['playbook'] = param['playbook']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'playbook'."
            }
            return response_array

        # 実行環境が設定させている場合に設定
        if 'execution_environment' in param and param['execution_environment']:
            if param['execution_environment'] is not False:
                content['execution_environment'] = param['execution_environment']

        # ---- Ansible Tower Version Check (Ver3.5)
        if RestApiCaller.getTowerVersion() == AnscConst.TOWER_VER35:
            if 'credential' in param and param['credential']:
                content['credential'] = param['credential']

            else:
                # 必須のためNG返す
                response_array['success'] = False
                response_array['responseContents'] = {
                    'errorMessage' : "Need 'credential'."
                }
                return response_array

            if 'vault_credential' in param and param['vault_credential']:
                content['vault_credential'] = param['vault_credential']
        # Ansible Tower Version Check (Ver3.5) ----

        if 'job_type' in param and param['job_type']:
            content['job_type'] = param['job_type']

        for key, val in addparam.items():
            content[key] = val

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

        for jobTplData in pickup_response_array['responseContents']:

            response_array = cls.delete(RestApiCaller, jobTplData['id'])
            if not response_array['success']:
                return response_array

        return pickup_response_array  # データ不足しているが、後続の処理はsuccessしか確認しないためこのまま

    @classmethod
    def deleteRelatedCurrnetExecutionForPrepare(cls, RestApiCaller, execution_no):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # データ絞り込み
        filteringName = cls.PREPARE_BUILD_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no))
        query = "?name=%s" % (filteringName)
        pickup_response_array = cls.getAll(RestApiCaller, query)
        if not pickup_response_array['success']:
            return pickup_response_array

        count = 0 if 'responseContents' not in pickup_response_array else len(pickup_response_array['responseContents'])
        if count == 0:  # 対象なし
            return pickup_response_array

        elif count == 1:  # SUCCESS
            pass

        else:  # 2つ以上取得できる場合は異常
            pickup_response_array['success'] = False
            if 'errorMessage' not in pickup_response_array['responseContents']:
                pickup_response_array['responseContents']['errorMessage'] = ''

            pickup_response_array['responseContents']['errorMessage'] = "Exception! More than one prepare job template for one execution."
            return pickup_response_array

        jobTplData = pickup_response_array['responseContents'][0]

        response_array = cls.delete(RestApiCaller, jobTplData['id'])
        if not response_array['success']:
            return response_array

        # データ絞り込み
        filteringName = cls.CLEANUP_PREPARED_BUILD_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no))
        query = "?name=%s" % (filteringName)
        pickup_response_array = cls.getAll(RestApiCaller, query)
        if not pickup_response_array['success']:
            return pickup_response_array

        count = len(pickup_response_array['responseContents'])
        if count == 0:  # 対象なし
            return pickup_response_array

        elif count == 1:  # SUCCESS
            pass

        else:  # 2つ以上取得できる場合は異常
            pickup_response_array['success'] = False
            if 'errorMessage' not in pickup_response_array['responseContents']:
                pickup_response_array['responseContents']['errorMessage'] = ''

            pickup_response_array['responseContents']['errorMessage'] = "Exception! More than one prepare job template for one execution."
            return pickup_response_array

        jobTplData = pickup_response_array['responseContents'][0]

        response_array = cls.delete(RestApiCaller, jobTplData['id'])
        if not response_array['success']:
            return response_array

        return response_array

    @classmethod
    def postForPrepare(cls, RestApiCaller, param):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # content生成
        content = {}
        response_array = {}

        content['verbosity'] = 2

        if 'execution_no' in param and param['execution_no']:
            content['name'] = cls.PREPARE_BUILD_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(param['execution_no']))

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'execution_no'."
            }
            return response_array

        if 'inventory' in param and param['inventory']:
            content['inventory'] = param['inventory']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'inventory'."
            }
            return response_array

        if 'project' in param and param['project']:
            content['project'] = param['project']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'project'."
            }
            return response_array

        if 'playbook' in param and param['playbook']:
            content['playbook'] = param['playbook']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'playbook'."
            }
            return response_array

        # ---- Ansible Tower Version Check (Ver3.5)
        if RestApiCaller.getTowerVersion() == AnscConst.TOWER_VER35:
            if 'credential' in param and param['credential']:
                content['credential'] = param['credential']

            else:
                # 必須のためNG返す
                response_array['success'] = False
                response_array['responseContents'] = {
                    'errorMessage' : "Need 'credential'."
                }
                return response_array
        # Ansible Tower Version Check (Ver3.5) ----

        if  'execution_no' in param and param['execution_no'] \
        and 'dataRelayStorage' in param and param['dataRelayStorage']:
            # 構築用のplaybookと同期させること
            content['extra_vars'] = json.dumps(
                {
                    "execution_no_with_padding" : FuncCommonLib.addPadding(param['execution_no']),
                    "if_info_data_relay_storage" : param['dataRelayStorage'],
                    "driver_type" : param['driver_type'],
                    "driver_id" : param['driver_id'],
                    "driver_name" : param['driver_name']
                }
            )

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'data_relay_storage'."
            }
            return response_array

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
    def postForCleanupPreparedProjectDirectory(cls, RestApiCaller, param):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # content生成
        content = {}
        response_array = {}

        if 'execution_no' in param and param['execution_no']:
            content['name'] = cls.CLEANUP_PREPARED_BUILD_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(param['execution_no']))

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'execution_no'."
            }
            return response_array

        if 'driver_name' in param and param['driver_name']:
            content['driver_name'] = param['driver_name']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'driver_name'."
            }
            return response_array

        # 掃除用のplaybookと同期させること
        content['extra_vars'] = json.dumps(
            {
                "execution_no_with_padding" : FuncCommonLib.addPadding(param['execution_no']),
                "driver_name" : param['driver_name']
            }
        )

        if 'inventory' in param and param['inventory']:
            content['inventory'] = param['inventory']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'inventory'."
            }
            return response_array

        if 'project' in param and param['project']:
            content['project'] = param['project']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'project'."
            }
            return response_array

        if 'playbook' in param and param['playbook']:
            content['playbook'] = param['playbook']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'playbook'."
            }
            return response_array

        # ---- Ansible Tower Version Check (Ver3.5)
        if RestApiCaller.getTowerVersion() == AnscConst.TOWER_VER35:
            if 'credential' in param and param['credential']:
                content['credential'] = param['credential']

            else:
                # 必須のためNG返す
                response_array['success'] = False
                response_array['responseContents'] = {
                    'errorMessage' : "Need 'credential'."
                }
                return response_array
        # Ansible Tower Version Check (Ver3.5) ----

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
    def launch(cls, RestApiCaller, param):

        # prepare実行のみを想定
        # 汎用性は検討していない

        # content生成
        content = {}
        response_array = {}

        if 'jobTplId' not in param or not param['jobTplId']:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'job_template id'."
            }
            return response_array

        # REST APIアクセス
        method = "POST"
        response_array = RestApiCaller.restCall(method, '%s%s/%s' % (cls.API_PATH, param['jobTplId'], cls.API_SUB_PATH_LAUNCH))

        # REST失敗
        if response_array['statusCode'] != 201:
            response_array['success'] = False
            if "errorMessage" not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = "status_code not 201. =>%s" % (response_array['statusCode'])

            return response_array

        # REST成功
        response_array['success'] = True

        return response_array

    # ---- Ansible Tower Version (Ver3.6)
    @classmethod
    def postCredentialsAdd(cls, RestApiCaller, jobTplId, credentialiId):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # content生成
        content = {}

        # REST APIアクセス
        method = "POST"

        content['id'] = credentialiId
        api_path = cls.CREDENTIALS_ADD_API_PATH % (jobTplId)

        response_array = RestApiCaller.restCall(method, api_path, content)

        # REST失敗
        if response_array['statusCode'] != 204:
            response_array['success'] = False
            if "errorMessage" not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = "status_code not 204. =>%s" % (response_array['statusCode'])

            return response_array

        # REST成功
        response_array['success'] = True

        return response_array
    # Ansible Tower Version (Ver3.6) ----



