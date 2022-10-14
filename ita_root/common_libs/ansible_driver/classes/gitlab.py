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
GitLab connection agnet module for Ansible Automation Controller
"""
from flask import g
import requests  # noqa F401
import os
import json
import urllib.parse
from common_libs.common.exception import AppException


class GitLabAgent:
    """
    GitLab connection agnet class for Ansible Automation Controller
    """
    __protocol = ""
    __host = ""
    __port = ""
    __api_base_url = ""
    __user = ""
    __token = ""

    def __init__(self):
        """
        constructor
        """
        self.__protocol = os.environ.get('GITLAB_PROTOCOL')
        self.__host = os.environ.get('GITLAB_HOST')
        self.__port = os.environ.get('GITLAB_PORT')
        self.__api_base_url = "{}://{}:{}/api/v4".format(self.__protocol, self.__host, self.__port)

        organization_id = g.get('ORGANIZATION_ID')
        if not organization_id:
            # organization create controller
            self.__token = os.environ.get('GITLAB_ROOT_TOKEN')
        else:
            # backyard
            self.__user = g.gitlab_connect_info.get('GITLAB_USER')
            self.__token = g.gitlab_connect_info.get('GITLAB_TOKEN')

    def send_api(self, method, resource, data=None, get_params=None, as_row=False):
        """
        request gitlab RESTAPI

        Arguments:
            method: get or post or put or delete
            resource: url resource
            data: request body
            get_params: get query paramater
            as_row: whether return response-object or not
        Returns:
            http response body OR boolean OR response-object
        """
        url = self.__api_base_url + resource
        headers = {
            "PRIVATE-TOKEN": self.__token,
            "Content-Type": "application/json"
        }
        data_json = json.dumps(data)

        g.applogger.debug('gitlab api request: url={}:{}, headers={}, params={}, data={}'.format(method, resource, headers, get_params, data_json))
        response = eval('requests.{}'.format(method.lower()))(url, headers=headers, params=get_params, data=data_json)

        if response.headers.get('Content-Type') == 'application/json':
            if 200 <= response.status_code < 400:
                res = response.json()

                if "error" in res:
                    err_msg = "{}:{} -> {}:{}".format(method, resource, response.status_code, res)
                    raise AppException("999-00004", [err_msg])
                else:
                    g.applogger.debug('gitlab api response: url={}:{} -> {}:{}'.format(method, resource, response.status_code, res))
                    if as_row is True:
                        return response
                    return res
            else:
                err_msg = "{}:{} -> {}:{}".format(method, resource, response.status_code, response.text)
                raise AppException("999-00004", [err_msg])
        else:
            if 200 <= response.status_code < 400:
                g.applogger.debug('gitlab api response: url={}:{} -> {}:{}'.format(method, resource, response.status_code, response.text))
                if as_row is True:
                    return response
                return True
            else:
                err_msg = "{}:{} -> {}:{}".format(method, resource, response.status_code, response.text)
                raise AppException("999-00004", [err_msg])

    def get_http_repo_url(self, project_name):
        """
        get gitlab http repository url

        Arguments:
            project_name: project_name
        Returns:
            (str) url
        """
        return "{protocol}://{user}:{token}@{host}:{port}/{user}/{project_name}.git".format(protocol=self.__protocol, host=self.__host, port=self.__port, user=self.__user, token=urllib.parse.quote(self.__token), project_name=project_name)  # noqa E501

    def get_user_self(self):
        # https://docs.gitlab.com/ee/api/users.html#for-normal-users-1

        res = self.send_api(method="get", resource="/user")
        return res

    def get_user_by_id(self, user_id):
        # 未使用中
        # https://docs.gitlab.com/ee/api/users.html#single-user

        return self.send_api(method="get", resource="/users/{}".format(user_id))

    def get_user_by_username(self, username=""):
        # https://docs.gitlab.com/ee/api/users.html#list-users
        if not username:
            params = {}
        else:
            params = {
                "username": username
            }

        return self.send_api(method="get", resource="/users", get_params=params)

    def create_user(self, username):
        # https://docs.gitlab.com/ee/api/users.html#user-creation
        payload = {
            "name": username,
            "username": username,
            "email": username + "@example.com",
            "can_create_group": False,
            "admin": False,
            "external": False,  # can_create_project
            "force_random_password": True,
            "projects_limit": 10000,
            "skip_confirmation": True
        }

        res = self.send_api(method="post", resource="/users", data=payload)
        return res

    def delete_user(self, user_id):
        # https://docs.gitlab.com/ee/api/users.html#user-deletion
        payload = {
            "id": user_id,
            'hard_delete': True
        }

        return self.send_api(method="delete", resource="/users/{}".format(user_id), data=payload)

    def create_personal_access_tokens(self, user_id, username):
        # https://docs.gitlab.com/ee/api/users.html#create-a-personal-access-token
        payload = {
            "user_id": user_id,
            "name": username,
            # "expires_at": "YYYY-MM-DD",
            "scopes": ["api"]
        }

        res = self.send_api(method="post", resource="/users/{}/personal_access_tokens".format(user_id), data=payload)
        return res.get('token')

    def get_project_by_user_id(self, user_id, page=1):
        # https://docs.gitlab.com/ee/api/projects.html#list-user-projects
        get_params = {
            "page": page,
            "per_page": 100
        }

        return self.send_api(method="get", resource="/users/{}/projects".format(user_id), get_params=get_params, as_row=True)

    def get_all_project_by_user_id(self, user_id):
        res = []

        is_get_all = False
        next_page = 1
        while is_get_all is False:
            response = self.get_project_by_user_id(user_id, next_page)
            project_list = response.json()
            res.extend(project_list)

            current_page = response.headers.get('X-Page')
            total_pages = response.headers.get('X-Total-Pages')
            if current_page == total_pages:
                is_get_all = True
            else:
                next_page = response.headers.get('X-Next-Page')

        return res

    def get_project_by_name(self, project_name):
        """
        get project by project_name

        Arguments:
            project_name: project_name
        Returns:
            (json)http response body
        """
        user = self.get_user_self()
        if user:
            is_get_all = False
            next_page = 1
            while is_get_all is False:
                response = self.get_project_by_user_id(user['id'], next_page)
                project_list = response.json()
                for project in project_list:
                    if project['path'] == project_name:
                        is_get_all = True
                        return project

                current_page = response.headers.get('X-Page')
                total_pages = response.headers.get('X-Total-Pages')
                if current_page == total_pages:
                    is_get_all = True
                else:
                    next_page = response.headers.get('X-Next-Page')

        return False

    def create_project(self, project_name):
        # https://docs.gitlab.com/ee/api/projects.html#create-project
        organization_id = g.get('ORGANIZATION_ID')
        workspace_id = g.get('WORKSPACE_ID')
        payload = {
            "name": project_name,
            "path": project_name,  # Repository name for new project.
            "visibility": "private",
            "emails_disabled": True,
            "initialize_with_readme	": True,  # Allows you to immediately clone this project’s repository. Skip this if you plan to push up an existing repository.  # noqa E501
            "tag_list": [self.__user, "organization_id_" + organization_id, "workspace_id_" + workspace_id]
        }

        return self.send_api(method="post", resource="/projects", data=payload)

    def delete_project(self, project_id):
        # https://docs.gitlab.com/ee/api/projects.html#delete-project

        return self.send_api(method="delete", resource="/projects/{}".format(project_id))
