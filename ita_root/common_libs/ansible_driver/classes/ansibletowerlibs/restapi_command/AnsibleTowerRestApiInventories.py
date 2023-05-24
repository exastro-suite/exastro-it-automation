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
from flask import g

from common_libs.ansible_driver.functions.ansibletowerlibs import AnsibleTowerCommonLib as FuncCommonLib
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiBase import AnsibleTowerRestApiBase


class AnsibleTowerRestApiInventories(AnsibleTowerRestApiBase):

    """
    【概要】
        AnsibleTower RestApi Inventory系を呼ぶ クラス
    """

    API_PATH = "inventories/"
    API_SUB_PATH = "instance_groups/"
    IDENTIFIED_NAME_PREFIX_DEL = "ita_%s_executions_inventory_%s"
    IDENTIFIED_NAME_PREFIX = "ita_%s_executions_inventory_%s_%s"

    PREPARE_BUILD_INVENTORY_NAME = "ita_executions_local"

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

        OrchestratorSubId_dir = RestApiCaller.getOrchestratorSubId_dir()

        # content生成
        content = {}
        response_array = {}

        if 'execution_no' in param and param['execution_no'] \
        and 'loopCount' in param and param['loopCount']:
            content['name'] = cls.IDENTIFIED_NAME_PREFIX % (OrchestratorSubId_dir, FuncCommonLib.addPadding(param['execution_no']), FuncCommonLib.addPadding(param['loopCount']))

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage': "Need 'execution_no' and 'loopCount'."
            }
            return response_array

        if 'organization' in param and param['organization']:
            content['organization'] = param['organization']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage': "Need 'organization'."
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

        inventoryId = response_array['responseContents']['id']

        if "instanceGroupId" in param and param['instanceGroupId']:
            content_2 = {}
            content_2['id'] = param['instanceGroupId']

            # REST APIアクセス
            method = "POST"
            response_array_2 = RestApiCaller.restCall(method, '%s%s/%s' % (cls.API_PATH, inventoryId, cls.API_SUB_PATH), content_2)

            # REST失敗
            if response_array_2['statusCode'] != 204:
                response_array_2['success'] = False
                if "errorMessage" not in response_array_2['responseContents']:
                    response_array_2['responseContents']['errorMessage'] = "status_code not 204. =>%s" % (response_array_2['statusCode'])

                return response_array_2

        # REST成功
        response_array['success'] = True

        return response_array

    @classmethod
    def delete(cls, RestApiCaller, id):

        # REST APIアクセス
        method = "DELETE"
        response_array = RestApiCaller.restCall(method, '%s%s/' % (cls.API_PATH, id))

        # REST失敗
        if response_array['statusCode'] != 202:
            response_array['success'] = False
            if "errorMessage" not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = "status_code not 202. =>%s" % (response_array['statusCode'])

            return response_array

        # REST成功
        response_array['success'] = True

        return response_array

    """
    @classmethod
    def deleteRelatedCurrnetExecution(cls, RestApiCaller, execution_no):

        OrchestratorSubId_dir = RestApiCaller.getOrchestratorSubId_dir()

        # データ絞り込み
        filteringName = cls.IDENTIFIED_NAME_PREFIX_DEL % (OrchestratorSubId_dir, FuncCommonLib.addPadding(execution_no)) + '_'
        query = "?name__startswith=%s" % (filteringName)
        pickup_response_array = cls.getAll(RestApiCaller, query)
        if not pickup_response_array['success']:
            return pickup_response_array

        for inventoryData in pickup_response_array['responseContents']:
            response_array = cls.delete(RestApiCaller, inventoryData['id'])
            if not response_array['success']:
                return response_array

        return pickup_response_array  # データ不足しているが、後続の処理はsuccessしか確認しないためこのまま
    """

    @classmethod
    def deleteRelatedCurrnetExecution(cls, RestApiCaller, AACCreateObjectID):

        result_response_array = {}
        result_response_array['success'] = True

        # inventoryが作成されていることを確認
        obj_id = "InventoryId"
        if obj_id not in AACCreateObjectID:
            return result_response_array

        for inventoryData in AACCreateObjectID[obj_id]:
            response_array = cls.delete(RestApiCaller, inventoryData)
            if not response_array['success']:
                # ゴミ掃除時のエラーは作業実行のエラーログは出力しない
                g.applogger.info("AnsibleTowerRestApiInventories:deleteRelatedCurrnetExecution Faild to delete inventory.")
                g.applogger.info(response_array)
                return response_array

        return result_response_array  # データ不足しているが、後続の処理はsuccessしか確認しないためこのまま
