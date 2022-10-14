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

import json
import os
import re
import subprocess

from flask import g
from abc import ABC, abstractclassmethod
from jinja2 import FileSystemLoader, Environment


class AnsibleAgent(ABC):

    def __init__(self):
        """
        コンストラクタ
        """
        self._organization_id = g.get('ORGANIZATION_ID')
        self._workspace_id = g.get('WORKSPACE_ID')

    @abstractclassmethod
    def container_start_up(self, execution_no, conductor_instance_no, str_shell_command):
        """
        コンテナを立ち上げる
        """
        pass

    @abstractclassmethod
    def is_container_running(self, execution_no):
        """
        コンテナが実行中か確認する
        """
        pass

    @abstractclassmethod
    def container_kill(self, execution_no):
        """
        コンテナを削除する
        """
        pass

    def get_unique_name(self, execution_no):
        """
        コンテナを特定するためのユニークな文字列を生成する
        """
        return "%s_%s_%s" % (self._organization_id, self._workspace_id, execution_no)

    @abstractclassmethod
    def container_clean(self, execution_no):
        """
        実行完了しているコンテナがあれば削除する
        """
        pass


class DockerMode(AnsibleAgent):

    def __init__(self):
        """
        コンストラクタ
        親クラスのコンストラクタを呼ぶ
        """
        super().__init__()

    def container_start_up(self, execution_no, conductor_instance_no, str_shell_command):
        """
        コンテナを立ち上げる
        """
        # print("method: container_start_up")

        # create path string
        driver_path = "{}/{}/driver/ansible/legacy_role/{}".format(self._organization_id, self._workspace_id, execution_no)
        _conductor_instance_no = conductor_instance_no if conductor_instance_no else "dummy"
        conductor_path = "{}/{}/driver/conductor/{}".format(self._organization_id, self._workspace_id, _conductor_instance_no)

        ansible_agent_image = "{}:{}".format(os.environ.get('ANSIBLE_AGENT_IMAGE'), os.environ.get('ANSIBLE_AGENT_IMAGE_TAG'))

        host_mount_path_driver = os.environ.get('HOST_STORAGEPATH') + driver_path
        container_mount_path_driver = os.environ.get('STORAGEPATH') + driver_path
        if not os.path.isdir(container_mount_path_driver):
            os.makedirs(container_mount_path_driver)
        host_mount_path_conductor = os.environ.get('HOST_STORAGEPATH') + conductor_path
        container_mount_path_conductor = os.environ.get('STORAGEPATH') + conductor_path
        project_name = self.get_unique_name(execution_no)

        # generate execute manifest
        fileSystemLoader = FileSystemLoader(searchpath="templates")
        env = Environment(loader=fileSystemLoader)
        template = env.get_template('docker-compose.yml')
        exec_manifest = "%s/.tmp/.docker-compose.yml" % (container_mount_path_driver)

        with open(exec_manifest, 'w') as f:
            f.write(template.render(
                str_shell_command=str_shell_command,
                organization_id=self._organization_id,
                workspace_id=self._workspace_id,
                execution_no=execution_no,
                HTTP_PROXY=os.getenv('HTTP_PROXY', ""),
                HTTPS_PROXY=os.getenv('HTTPS_PROXY', ""),
                ansible_agent_image=ansible_agent_image,
                host_mount_path_driver=host_mount_path_driver,
                container_mount_path_driver=container_mount_path_driver,
                host_mount_path_conductor=host_mount_path_conductor,
                container_mount_path_conductor=container_mount_path_conductor
            ))

        # create command string
        docker_compose_command = ["/usr/local/bin/docker-compose", "-f", exec_manifest, "-p", project_name, "up", "-d"]
        command = ["sudo"] + docker_compose_command

        # docker-compose -f file -p project up
        cp = subprocess.run(command, capture_output=True, text=True)

        if cp.returncode == 0:
            return True, cp.stdout
        else:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"return_code": cp.returncode, "stderr": cp.stderr}

    def is_container_running(self, execution_no):
        """
        コンテナが実行中か確認する
        """
        # print("method: is_container_running")

        # docker-compose -p project ps
        project_name = self.get_unique_name(execution_no)
        docker_compose_command = ["/usr/local/bin/docker-compose", "-p", project_name, "ps", "--format", "json"]
        command = ["sudo"] + docker_compose_command

        cp = subprocess.run(command, capture_output=True, text=True)
        if cp.returncode != 0:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"return_code": cp.returncode, "stderr": cp.stderr}

        # 戻りをjsonデコードして、runningのものが一つだけ存在しているか確認
        result_obj = json.loads(cp.stdout)
        if len(result_obj) > 0 and result_obj[0]['State'] == "running":
            return True, result_obj

        return False, {"return_code": cp.returncode, "stderr": "not running"}

    def container_kill(self, execution_no):
        """
        コンテナを削除する
        """
        # print("method: container_kill")

        # docker-compose -p project kill
        project_name = self.get_unique_name(execution_no)
        docker_compose_command = ["/usr/local/bin/docker-compose", "-p", project_name, "kill"]
        command = ["sudo"] + docker_compose_command

        cp = subprocess.run(command, capture_output=True, text=True)
        if cp.returncode != 0:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"return_code": cp.returncode, "stderr": cp.stderr}

        # docker-compose -p project rm -f
        docker_compose_command = ["/usr/local/bin/docker-compose", "-p", project_name, "rm", "-f"]
        command = ["sudo"] + docker_compose_command

        cp = subprocess.run(command, capture_output=True, text=True)
        if cp.returncode != 0:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"return_code": cp.returncode, "stderr": cp.stderr}

        return True, cp.stdout

    def container_clean(self, execution_no):
        """
        実行完了しているコンテナがあれば削除する
        """
        # docker-compose -p project ps
        project_name = self.get_unique_name(execution_no)
        docker_compose_command = ["/usr/local/bin/docker-compose", "-p", project_name, "ps", "--format", "json"]
        command = ["sudo"] + docker_compose_command

        cp = subprocess.run(command, capture_output=True, text=True)
        if cp.returncode != 0:
            return True, "already not exists"

        # existedしているものを削除
        result_obj = json.loads(cp.stdout)
        if len(result_obj) > 0 and result_obj[0]['State'] in ['existed']:
            # docker-compose -p project rm -f
            docker_compose_command = ["/usr/local/bin/docker-compose", "-p", project_name, "rm", "-f"]
            command = ["sudo"] + docker_compose_command

            cp = subprocess.run(command, capture_output=True, text=True)
            if cp.returncode != 0:
                # cp.check_returncode()  # 例外を発生させたい場合
                return False, {"return_code": cp.returncode, "stderr": cp.stderr}

        return True, cp.stdout

    # def unused_allclean(self):
    #     """
    #     未使用のコンテナー、ネットワーク、イメージをすべて削除
    #     """
    #     g.applogger.debug("unused_allclean")

    #     command = ["/usr/local/bin/docker", "system", "prune", "--force"]
    #     command = ["sudo"] + command

    #     cp = subprocess.run(command, capture_output=True, text=True)
    #     if cp.returncode != 0:
    #         g.applogger.debug("unused_allclean->error:%s" % cp.stderr)
    #         return False, cp.stderr

    #     return True, cp.stdout


class KubernetesMode(AnsibleAgent):

    NAMESPACE = 'exastro-it-automation'

    def __init__(self):
        """
        コンストラクタ
        親クラスのコンストラクタを呼ぶ
        """
        super().__init__()

    def container_start_up(self, execution_no, conductor_instance_no, str_shell_command):
        '''
        コンテナ(Pod)を立ち上げる
        '''
        # print("method: container_start_up")

        # create path string
        driver_path = "{}/{}/driver/ansible/legacy_role/{}".format(self._organization_id, self._workspace_id, execution_no)
        _conductor_instance_no = conductor_instance_no if conductor_instance_no else "dummy"
        conductor_path = "{}/{}/driver/conducotr/{}".format(self._organization_id, self._workspace_id, _conductor_instance_no)

        ansible_agent_image = "{}:{}".format(os.environ.get('ANSIBLE_AGENT_IMAGE'), os.environ.get('ANSIBLE_AGENT_IMAGE_TAG'))

        host_mount_path_driver = driver_path
        container_mount_path_driver = os.environ.get('STORAGEPATH') + driver_path
        if not os.path.isdir(container_mount_path_driver):
            os.makedirs(container_mount_path_driver)
        host_mount_path_conductor = conductor_path
        container_mount_path_conductor = os.environ.get('STORAGEPATH') + conductor_path
        unique_name = self.get_unique_name(execution_no)
        unique_name = re.sub(r'_', '-', unique_name).lower()

        # generate execute manifest
        fileSystemLoader = FileSystemLoader(searchpath="./templates")
        env = Environment(loader=fileSystemLoader)
        template = env.get_template('k8s_pod.yml')
        exec_manifest = "%s/.tmp/.k8s_pod.yml" % (container_mount_path_driver)

        with open(exec_manifest, 'w') as f:
            f.write(template.render(
                str_shell_command=str_shell_command,
                unique_name=unique_name,
                HTTP_PROXY=os.getenv('HTTP_PROXY', ""),
                HTTPS_PROXY=os.getenv('HTTPS_PROXY', ""),
                ansible_agent_image=ansible_agent_image,
                host_mount_path_driver=host_mount_path_driver,
                container_mount_path_driver=container_mount_path_driver,
                host_mount_path_conductor=host_mount_path_conductor,
                container_mount_path_conductor=container_mount_path_conductor
            ))

        # create command string
        command = ["/usr/local/bin/kubectl", "apply", "-f", exec_manifest, "-n", KubernetesMode.NAMESPACE]

        # kubectl apply -f file -n namespace
        cp = subprocess.run(' '.join(command), capture_output=True, shell=True, text=True)

        if cp.returncode == 0:
            return True, cp.stdout
        else:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"return_code": cp.returncode, "stderr": cp.stderr}

    def is_container_running(self, execution_no):
        """
        コンテナ(Pod)が実行中か確認する
        """
        # print("method: is_container_running")

        # runningのものが一つだけ存在しているか確認
        return_code, status, errmsg = self._check_status(execution_no)
        g.applogger.debug("Container Status=" + status)
#        if return_code == 0 and status == "running":
        if return_code == 0 and status.lower() in ["running", "pending"]:
            return True,

        return False, {"return_code": return_code, "stderr": "not running"}

    def container_kill(self, execution_no):
        """
        コンテナ(Pod)を削除する
        """
        # print("method: container_kill")

        # create command string
        ansible_role_driver_middle_path = "driver/ansible/legacy_role"
        container_mount_path_driver = "/storage/%s/%s/%s/%s" % (self._organization_id, self._workspace_id, ansible_role_driver_middle_path, execution_no)  # noqa E501
        exec_manifest = "%s/.tmp/.k8s_pod.yml" % (container_mount_path_driver)

        command = ["/usr/local/bin/kubectl", "delete", "-f", exec_manifest, "-n", KubernetesMode.NAMESPACE, "--force=true", "--grace-period=0"]

        cp = subprocess.run(' '.join(command), capture_output=True, shell=True, text=True)
        if cp.returncode != 0:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"return_code": cp.returncode, "stderr": cp.stderr}

        return True, cp.stdout

    def container_clean(self, execution_no):
        """
        実行完了しているコンテナ(Pod)があれば削除する
        """
        # print("method: container_clean")

        return_code, status, errmsg = self._check_status(execution_no)
        if status in ["Succeeded", "Failed"]:
            return self.container_kill(execution_no)

        g.applogger.debug("not exist completed container, nothing to do.")
        return True,

    def _check_status(self, execution_no):
        """
        コンテナ(Pod)のステータスを確認する
        """
        # print("method: _check_status")

        # create command string
        unique_name = self.get_unique_name(execution_no)
        unique_name = re.sub(r'_', '-', unique_name).lower()
        command = ["/usr/local/bin/kubectl", "get", "pod", "-n", KubernetesMode.NAMESPACE, 'it-ansible-agent-' + unique_name, "-o", "json"]

        cp = subprocess.run(' '.join(command), capture_output=True, shell=True, text=True)
        if cp.returncode != 0:
            # cp.check_returncode()  # 例外を発生
            return cp.returncode, None, cp.stderr

        try:
            result_obj = json.loads(cp.stdout)
            status = result_obj['status']['phase']
        except Exception as e:
            g.applogger.debug(str(e))
            g.applogger.debug("stdout:\n%s" % cp.stdout.decode('utf-8'))

            return 1, None, str(e)

        return cp.returncode, status, ""
