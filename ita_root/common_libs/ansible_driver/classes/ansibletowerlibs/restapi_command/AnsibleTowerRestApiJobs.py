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
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiJobTemplates import AnsibleTowerRestApiJobTemplates


class AnsibleTowerRestApiJobs(AnsibleTowerRestApiBase):

    """
    【概要】
        AnsibleTower RestApi Job系を呼ぶ クラス
    """

    API_PATH = "jobs/"
    IDENTIFIED_NAME_PREFIX = "ita_executions_job_"
    API_SUB_PATH_STDOUT = "stdout/?format=txt_download"
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
    def post(cls, RestApiCaller, param, addparam={}):

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

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # データ絞り込み(親)
        filteringName = AnsibleTowerRestApiJobTemplates.SEARCH_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no))
        query = "?name__startswith=%s" % (filteringName)
        pickup_response_array = AnsibleTowerRestApiJobTemplates.getAll(RestApiCaller, query)
        if not pickup_response_array['success']:
            return pickup_response_array

        for jobTplData in pickup_response_array['responseContents']:
            # データ絞り込み(本体)
            query = "?job_template=%s" % (jobTplData['id'])
            pickup_response_array_2 = cls.getAll(RestApiCaller, query)
            if not pickup_response_array_2['success']:
                return pickup_response_array_2

            for jobData in pickup_response_array_2['responseContents']:

                response_array = cls.delete(RestApiCaller, jobData['id'])
                if not response_array['success']:
                    return response_array

        return pickup_response_array  # データ不足しているが、後続の処理はsuccessしか確認しないためこのまま

    @classmethod
    def deleteRelatedCurrnetExecutionForPrepare(cls, RestApiCaller, execution_no):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # データ絞り込み(親)
        filteringName = AnsibleTowerRestApiJobTemplates.PREPARE_BUILD_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no))
        query = "?name=%s" % (filteringName)
        pickup_response_array = AnsibleTowerRestApiJobTemplates.getAll(RestApiCaller, query)
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

        jobTplId = pickup_response_array['responseContents'][0]['id']

        # データ絞り込み(本体)
        query = "?job_template=%s" % (jobTplId)
        pickup_response_array_2 = cls.getAll(RestApiCaller, query)
        if not pickup_response_array_2['success']:
            return pickup_response_array_2

        for jobData in pickup_response_array_2['responseContents']:

            response_array = cls.delete(RestApiCaller, jobData['id'])
            if not response_array['success']:
                return response_array

        # データ絞り込み(親)
        filteringName = AnsibleTowerRestApiJobTemplates.CLEANUP_PREPARED_BUILD_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no))
        query = "?name=%s" % (filteringName)
        pickup_response_array = AnsibleTowerRestApiJobTemplates.getAll(RestApiCaller, query)
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

            pickup_response_array['responseContents']['errorMessage'] = "Exception! More than one cleanup job template for one execution."
            return pickup_response_array

        jobTplId = pickup_response_array['responseContents'][0]['id']

        # データ絞り込み(本体)
        query = "?job_template=%s" % (jobTplId)
        pickup_response_array_2 = cls.getAll(RestApiCaller, query)
        if not pickup_response_array_2['success']:
            return pickup_response_array_2

        for jobData in pickup_response_array_2['responseContents']:

            response_array = cls.delete(RestApiCaller, jobData['id'])
            if not response_array['success']:
                return response_array

        return pickup_response_array_2  # データ不足しているが、後続の処理はsuccessしか確認しないためこのまま

    @classmethod
    def getStdOut(cls, RestApiCaller, id):

        # REST APIアクセス
        method = "GET"
        response_array = RestApiCaller.restCall(method, '%s%s/%s' % (cls.API_PATH, id, cls.API_SUB_PATH_STDOUT), {}, {}, True)

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
    def cancelRelatedCurrnetExecutionForPrepare(cls, RestApiCaller, execution_no):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # データ絞り込み(親)
        filteringName = AnsibleTowerRestApiJobTemplates.CLEANUP_PREPARED_BUILD_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no))
        query = "?name=%s" % (filteringName)
        pickup_response_array = AnsibleTowerRestApiJobTemplates.getAll(RestApiCaller, query)
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

            pickup_response_array['responseContents']['errorMessage'] = "Exception! More than one cleanup job template for one execution."
            return pickup_response_array

        jobTplId = pickup_response_array['responseContents'][0]['id']

        # データ絞り込み(本体)
        query = "?job_template=%s" % (jobTplId)
        response_array = cls.getAll(RestApiCaller, query)
        if not response_array['success']:
            return response_array

        count = 0 if 'responseContents' not in response_array else len(response_array['responseContents'])
        if count == 0:  # 対象なし
            return response_array

        elif count == 1:  # SUCCESS
            pass

        else:  # 2つ以上取得できる場合は異常
            response_array['success'] = False
            if 'errorMessage' not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = ''

            response_array['responseContents']['errorMessage'] = "Exception! More than one cleanup job template for one execution."
            return response_array

        jobData = response_array['responseContents'][0]

        response_array = cls.cancel(RestApiCaller, jobData['id'])
        if not response_array['success']:
            return response_array

        return response_array
