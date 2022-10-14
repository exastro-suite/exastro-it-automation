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


class AnsibleTowerRestApiProjects(AnsibleTowerRestApiBase):

    """
    【概要】
        AnsibleTower RestApi Project系を呼ぶ クラス
    """

    API_PATH = "projects/"
    SCM_LOCALPATH_PREFIX = "ita_%s_executions_%s"
    IDENTIFIED_NAME_PREFIX = "ita_%s_executions_project_%s"
    PREPARE_BUILD_PROJECT_NAME = "ita_executions_prepare_build"
    CLEANUP_PREPARED_BUILD_PROJECT_NAME = "ita_executions_cleanup"

    SCMTYPE_GIT = "git"

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

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # content生成
        content = {}
        response_array = {}

        if 'scm_type' in param and param['scm_type'] is not None:
            content['name'] = cls.IDENTIFIED_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(param['execution_no']))
            if param['scm_type'] == cls.SCMTYPE_GIT:  # SCM_TYPE = git
                content['scm_type'] = param['scm_type']
                if 'scm_url' in param and param['scm_url']:
                    content['scm_url'] = param['scm_url']

                else:
                    # 必須のためNG返す
                    response_array['success'] = False
                    response_array['responseContents'] = {
                        'errorMessage' : "Need 'scm_url'."
                    }
                    return response_array
            else:
                # SCM_TYPE = "" (手動) 
                if 'execution_no' in param and param['execution_no']:
                    content['local_path'] = cls.SCM_LOCALPATH_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(param['execution_no']))

                else:
                    # 必須のためNG返す
                    response_array['success'] = False
                    response_array['responseContents'] = {
                        'errorMessage' : "Need 'execution_no'."
                    }
                    return response_array

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'scm_type'."
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

        if 'custom_virtualenv' in param and param['custom_virtualenv'] is not None:
            content['custom_virtualenv'] = param['custom_virtualenv']

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
        filteringName = cls.IDENTIFIED_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no))
        query = "?name=%s" % (filteringName)
        pickup_response_array = cls.getAll(RestApiCaller, query)
        if not pickup_response_array['success']:
            return pickup_response_array

        for projectData in pickup_response_array['responseContents']:
            response_array = cls.delete(RestApiCaller, projectData['id'])
            if not response_array['success']:
                return response_array

        return pickup_response_array  # データ不足しているが、後続の処理はsuccessしか確認しないためこのまま
