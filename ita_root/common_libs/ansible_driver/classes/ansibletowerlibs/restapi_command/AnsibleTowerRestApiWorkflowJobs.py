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


import os

from common_libs.ansible_driver.functions.ansibletowerlibs import AnsibleTowerCommonLib as FuncCommonLib
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiBase import AnsibleTowerRestApiBase
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiWorkflowJobTemplates import AnsibleTowerRestApiWorkflowJobTemplates


class AnsibleTowerRestApiWorkflowJobs(AnsibleTowerRestApiBase):

    """
    【概要】
        AnsibleTower RestApi WorkflowJob系を呼ぶ クラス
    """

    API_PATH = "workflow_jobs/"
    IDENTIFIED_NAME_PREFIX = "ita_executions_workflow_"
    NAME_SEARCH = "name__startswith=ita_%s_executions&name__contains=%s"
    API_SUB_PATH_CANCEL = "cancel/"

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

        raise Exception("Not implemented.")

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

        response_array = cls.getByExecutionNo(RestApiCaller, execution_no)
        if not response_array['success']:
            return response_array

        if 'responseContents' not in response_array or not response_array['responseContents']:
            return response_array

        wfJobData = response_array['responseContents']

        response_array = cls.delete(RestApiCaller, wfJobData['id'])
        if not response_array['success']:
            return response_array

        return response_array

    @classmethod
    def NameSearch(cls, RestApiCaller, execution_no):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name
        if os.environ.get('TOWER_DRIVER_NAME'):
            vg_tower_driver_name = os.environ.get('TOWER_DRIVER_NAME')

        # ジョブスライスが設定されるとワークフロージョブ名はワークフロージョブ名の場合とテンプレート名の場合がある
        # テンプレート名:ita_(driver_name)_executions_jobtpl_(execution_no)
        # ワークフロージョブ名名:ita_(driver_name)_executions_workflowtpl_(execution_no)
        filteringName = cls.NAME_SEARCH % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no))
        query = "?%s" % (filteringName)
        pickup_response_array = cls.getAll(RestApiCaller, query)
        if not pickup_response_array['success']:
            return pickup_response_array

        return pickup_response_array

    @classmethod
    def getByExecutionNo(cls, RestApiCaller, execution_no):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name
        if os.environ.get('TOWER_DRIVER_NAME'):  # ToDo TOWER_DRIVER_NAME
            vg_tower_driver_name = os.environ.get('TOWER_DRIVER_NAME')

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
            pickup_response_array['responseContents']['errorMessage'] = "Exception! More than one workflow job template."
            return pickup_response_array

        wfJobTplId = pickup_response_array['responseContents'][0]['id']

        # データ絞り込み(本体)
        query = "?workflow_job_template=" % (wfJobTplId)
        pickup_response_array_2 = cls.getAll(RestApiCaller, query)
        if not pickup_response_array_2['success']:
            return pickup_response_array_2

        count = 0 if 'responseContents' not in pickup_response_array_2 else len(pickup_response_array_2['responseContents'])
        if count == 0:  # 対象無しでもそのまま返す(responseContents = 空配列)
            return pickup_response_array_2

        elif count == 1:  # SUCCESS
            pass

        else:  # 2つ以上取得できる場合は異常
            pickup_response_array_2['success'] = False
            pickup_response_array_2['responseContents']['errorMessage'] = "Exception! More than one workflow job."
            return pickup_response_array_2

        pickup_response_array_2['responseContents'] = pickup_response_array_2['responseContents'][0]
        return pickup_response_array_2

    @classmethod
    def cancel(cls, RestApiCaller, id):

        # REST APIアクセス
        method = "POST"
        response_array = RestApiCaller.restCall(method, '%s%s/%s' % (cls.API_PATH, id, cls.API_SUB_PATH_CANCEL))

        # REST失敗
        if response_array['statusCode'] != 202:
            response_array['success'] = False
            if "errorMessage" not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = "status_code not 202. =>%s" % (response_array['statusCode'])

            return response_array

        # REST成功
        response_array['success'] = True

        return response_array

    @classmethod
    def cancelRelatedCurrnetExecution(cls, RestApiCaller, execution_no):

        response_array = cls.getByExecutionNo(RestApiCaller, execution_no)
        if not response_array['success']:
            return response_array

        if 'responseContents' not in response_array or not response_array['responseContents']:
            return response_array

        wfJobData = response_array['responseContents']

        response_array = cls.cancel(RestApiCaller, wfJobData['id'])
        if not response_array['success']:
            return response_array

        return response_array
