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
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiInventories import AnsibleTowerRestApiInventories
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiHosts import AnsibleTowerRestApiHosts


class AnsibleTowerRestApiInventoryHosts(AnsibleTowerRestApiBase):

    """
    【概要】
        AnsibleTower RestApi InventoryHost系を呼ぶ クラス
    """

    API_PATH = "inventories/"
    API_SUB_PATH = "hosts/"
    IDENTIFIED_NAME_PREFIX = ""

    @classmethod
    def getAllEachInventory(cls, RestApiCaller, inventoryId, query=""):

        # REST APIアクセス
        method = "GET"
        response_array = RestApiCaller.restCall(method, '%s%s/%s%s' % (cls.API_PATH, inventoryId, cls.API_SUB_PATH, query))

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
    def get(cls, RestApiCaller, inventoryId, hostId):

        # REST APIアクセス
        method = "GET"
        response_array = RestApiCaller.restCall(method, '%s%s/%s%s/' % (cls.API_PATH, inventoryId, cls.API_SUB_PATH, hostId))

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

        response_array = {}

        if 'inventoryId' not in param or not param['inventoryId']:
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'inventory id'."
            }
            return response_array

        # content生成
        content = {}

        if  'name' in param and param['name']:
            content['name'] = param['name']

        else:
            # 必須のためNG返す
            response_array['success'] = False
            response_array['responseContents'] = {
                'errorMessage' : "Need 'name'."
            }
            return response_array

        if  'variables' in param and param['variables']:
            content['variables'] = param['variables']

        # REST APIアクセス
        method = "POST"
        response_array = RestApiCaller.restCall(method, '%s%s/%s' % (cls.API_PATH, param['inventoryId'], cls.API_SUB_PATH), content)

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
    def delete(cls, RestApiCaller, inventoryId, hostId):

        # REST APIアクセス
        method = "DELETE"
        response_array = RestApiCaller.restCall(method, '%s%s/%s%s/' % (cls.API_PATH, inventoryId, cls.API_SUB_PATH, hostId))

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
        filteringName = AnsibleTowerRestApiInventories.IDENTIFIED_NAME_PREFIX % (vg_tower_driver_name, FuncCommonLib.addPadding(execution_no), '')
        query = "?name__startswith=%s" % (filteringName)
        pickup_response_array = AnsibleTowerRestApiInventories.getAll(RestApiCaller, query)
        if not pickup_response_array['success']:
            return pickup_response_array

        for inventoryData in pickup_response_array['responseContents']:

            inventoryId = inventoryData['id']

            # データ絞り込み(本体)
            pickup_response_array_2 = cls.getAllEachInventory(RestApiCaller, inventoryId)
            if not pickup_response_array_2['success']:
                return pickup_response_array_2

            for inventoryHostData in pickup_response_array_2['responseContents']:
                response_array = AnsibleTowerRestApiHosts.delete(RestApiCaller, inventoryHostData['id'])
                if not response_array['success']:
                    response_array

        return pickup_response_array  # データ不足しているが、後続の処理はsuccessしか確認しないためこのまま
