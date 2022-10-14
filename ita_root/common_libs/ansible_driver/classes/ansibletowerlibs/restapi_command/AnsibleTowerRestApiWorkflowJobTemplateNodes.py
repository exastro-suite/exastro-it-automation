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


from common_libs.ansible_driver.functions.ansibletowerlibs import AnsibleTowerCommonLib as FuncCommonLib
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiBase import AnsibleTowerRestApiBase
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiWorkflowJobTemplates import AnsibleTowerRestApiWorkflowJobTemplates


class AnsibleTowerRestApiWorkflowJobTemplateNodes(AnsibleTowerRestApiBase):

    """
    【概要】
        AnsibleTower RestApi WorkflowJobTemplateNode系を呼ぶ クラス
    """

    API_PATH = "workflow_job_template_nodes/"
    IDENTIFIED_NAME_PREFIX = ""

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
    def post(cls, RestApiCaller, param):

        # content生成
        content = {}
        response_array = {}

        if  'execution_no' in param and param['execution_no'] \
        and 'loopCount' in param and param['loopCount']:
            content['name'] = cls.createName(cls.IDENTIFIED_NAME_PREFIX, param['execution_no'], param['loopCount'])

        else:
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'execution_no' and 'loopCount'."
            }
            return response_array

        if  'workflowTplId' in param and param['workflowTplId']:
            content['workflow_job_template'] = param['workflowTplId']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'workflow_job_tmplate Id'."
            }
            return response_array

        if  'jobtplId' in param and param['jobtplId']:
            content['unified_job_template'] = param['jobtplId']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'job_template Id'."
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

        # データ絞り込み(親)
        filteringName = AnsibleTowerRestApiWorkflowJobTemplates.IDENTIFIED_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no))
        query = "?name=%s" % (filteringName)
        pickup_response_array = AnsibleTowerRestApiWorkflowJobTemplates.getAll(RestApiCaller, query)
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
                pickup_response_array['responseContents']['errorMessage'] = ""

            pickup_response_array['responseContents']['errorMessage'] = "Exception! More than one workflow job template."
            return pickup_response_array

        wfJobTplId = pickup_response_array['responseContents'][0]['id']

        # データ絞り込み(本体)
        query = "?workflow_job_template=%s" % (wfJobTplId)
        pickup_response_array_2 = cls.getAll(RestApiCaller, query)
        if not pickup_response_array_2['success']:
            return pickup_response_array_2

        for wfJobTplNode in pickup_response_array_2['responseContents']:

            response_array = cls.delete(RestApiCaller, wfJobTplNode['id'])
            if not response_array['success']:
                return response_array

        return pickup_response_array_2  # データ不足しているが、後続の処理はsuccessしか確認しないためこのまま

