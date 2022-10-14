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


from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiBase import AnsibleTowerRestApiBase


class AnsibleTowerRestApirPassThrough(AnsibleTowerRestApiBase):

    """
    【概要】
        AnsibleTower RestApi Project系を呼ぶ クラス
    """

    @classmethod
    def get(cls, RestApiCaller, query, Rest_stdout_flg=False):

        # REST APIアクセス
        method = "GET"
        content = {}
        header = {}
        DirectUrl = True

        response_array = RestApiCaller.restCall(method, query, content, header, Rest_stdout_flg, DirectUrl)

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
    def post(cls, RestApiCaller, query, Rest_stdout_flg=False):

        # REST APIアクセス
        method = "POST"
        content = {}
        header = {}
        DirectUrl = True

        response_array = RestApiCaller.restCall(method, query, content, header, Rest_stdout_flg, DirectUrl)

        # REST失敗
        if response_array['statusCode'] != 202:
            response_array['success'] = False
            if "errorMessage" not in response_array['responseContents']:
                response_array['responseContents']['errorMessage'] = "status_code not 202. =>%s" % (response_array['statusCode'])

            return response_array

        # REST成功
        response_array['success'] = True

        return response_array
