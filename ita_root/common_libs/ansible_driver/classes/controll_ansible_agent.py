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
import shutil
import io
import jsonlines

from flask import g
from abc import ABC, abstractclassmethod
from jinja2 import FileSystemLoader, Environment
from common_libs.common.storage_access import storage_write


class AnsibleAgent(ABC):

    def __init__(self):
        """
        コンストラクタ
        """
        self._organization_id = g.get('ORGANIZATION_ID')
        self._workspace_id = g.get('WORKSPACE_ID')

    @abstractclassmethod
    def container_start_up(self, ansConstObj, execution_no, conductor_instance_no, str_shell_command):
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
    def container_kill(self, ansConstObj, execution_no):
        """
        コンテナを削除する
        """
        pass

    def get_unique_name(self, execution_no):
        """
        コンテナを特定するためのユニークな文字列を生成する
        """
        return f"ita-ansible-agent-{execution_no}"

    @abstractclassmethod
    def container_clean(self, ansConstObj, execution_no):
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

    def container_start_up(self, ansConstObj, execution_no, conductor_instance_no, str_shell_command):
        """
        コンテナを立ち上げる
        """
        # create path string
        driver_path = "{}/{}/driver/ansible/{}/{}".format(self._organization_id, self._workspace_id, ansConstObj.vg_OrchestratorSubId_dir, execution_no)
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

        # #2079 /storage配下は/tmpを経由してアクセスする
        obj = storage_write()
        obj.open(exec_manifest, 'w')
        obj.write(template.render(
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
                container_mount_path_conductor=container_mount_path_conductor,
                network_id=os.getenv('NETWORK_ID', "")
            ))
        obj.close()

        dir_tmp = "%s/.tmp/work/" % (container_mount_path_driver)
        shutil.copytree('/exastro/templates/work/', dir_tmp)

        # # create command string
        # command = ["/usr/local/bin/docker-compose", "-f", exec_manifest, "-p", project_name, "build"]

        # # docker-compose -f file -p project build
        # cp = subprocess.run(command, capture_output=True, text=True)

        # if cp.returncode == 0:
        #     pass
        # else:
        #     # cp.check_returncode()  # 例外を発生させたい場合
        #     return False, {"function": "container_build", "return_code": cp.returncode, "stderr": cp.stderr}

        command = ["/usr/local/bin/docker-compose", "-f", exec_manifest, "-p", project_name, "up", "-d"]

        # docker-compose -f file -p project up
        cp = subprocess.run(command, capture_output=True, text=True)

        if cp.returncode == 0:
            return True, cp.stdout
        else:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"function": "container_start_up", "return_code": cp.returncode, "stderr": cp.stderr}

    def is_container_running(self, execution_no):
        """
        コンテナが実行中か確認する
        """
        # docker-compose -p project ps
        project_name = self.get_unique_name(execution_no)
        command = ["/usr/local/bin/docker-compose", "-p", project_name, "ps", "--format", "json"]

        cp = subprocess.run(command, capture_output=True, text=True)
        if cp.returncode != 0:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"function": "is_container_running", "return_code": cp.returncode, "stderr": cp.stderr}

        # 戻りをjsonデコードして、runningのものが一つだけ存在しているか確認

        # docker-compose v2.21.0以降(jsonl形式)
        stdout_io = io.StringIO(cp.stdout)
        with jsonlines.Reader(stdout_io) as reader:
            result_obj = [item for item in reader]

        # # docker-compose v2.21.0未満
        # result_obj = json.loads(cp.stdout)

        if len(result_obj) > 0 and result_obj[0]['State'] == "running":
            return True, result_obj

        return False, {"function": "is_container_running", "return_code": cp.returncode, "stderr": "not running"}

    def container_kill(self, ansConstObj, execution_no):
        """
        コンテナを削除する
        """
        # docker-compose -p project kill
        project_name = self.get_unique_name(execution_no)
        command = ["/usr/local/bin/docker-compose", "-p", project_name, "kill"]

        cp = subprocess.run(command, capture_output=True, text=True)
        if cp.returncode != 0:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"function": "container_kill->kill", "return_code": cp.returncode, "stderr": cp.stderr}

        # docker-compose -p project rm -f
        command = ["/usr/local/bin/docker-compose", "-p", project_name, "rm", "-f"]

        cp = subprocess.run(command, capture_output=True, text=True)
        if cp.returncode != 0:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"function": "container_kill->rm", "return_code": cp.returncode, "stderr": cp.stderr}

        return True, cp.stdout

    def container_clean(self, ansConstObj, execution_no):
        """
        実行完了しているコンテナがあれば削除する
        """
        # docker-compose -p project ps
        project_name = self.get_unique_name(execution_no)
        command = ["/usr/local/bin/docker-compose", "-p", project_name, "ps", "--format", "json", "-a"]

        cp = subprocess.run(command, capture_output=True, text=True)
        if cp.returncode != 0:
            return True, "already not exists"

        # existedしているものを削除

        # docker-compose v2.21.0以降(jsonl形式)
        stdout_io = io.StringIO(cp.stdout)
        with jsonlines.Reader(stdout_io) as reader:
            result_obj = [item for item in reader]

        # # docker-compose v2.21.0未満
        # result_obj = json.loads(cp.stdout)

        if len(result_obj) > 0 and result_obj[0]['State'] in ['exited']:
            # docker-compose -p project rm -f
            command = ["/usr/local/bin/docker-compose", "-p", project_name, "rm", "-f"]

            cp = subprocess.run(command, capture_output=True, text=True)
            if cp.returncode != 0:
                # cp.check_returncode()  # 例外を発生させたい場合
                return False, {"function": "container_clean", "return_code": cp.returncode, "stderr": cp.stderr}

        return True, cp.stdout

    # def unused_allclean(self):
    #     """
    #     未使用のコンテナー、ネットワーク、イメージをすべて削除
    #     """
    #     g.applogger.debug("unused_allclean")

    #     command = ["/usr/local/bin/docker", "system", "prune", "--force"]

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

    def container_start_up(self, ansConstObj, execution_no, conductor_instance_no, str_shell_command):
        '''
        コンテナ(Pod)を立ち上げる
        '''
        # create path string
        driver_path = "{}/{}/driver/ansible/{}/{}".format(self._organization_id, self._workspace_id, ansConstObj.vg_OrchestratorSubId_dir, execution_no)
        _conductor_instance_no = conductor_instance_no if conductor_instance_no else "dummy"
        conductor_path = "{}/{}/driver/conductor/{}".format(self._organization_id, self._workspace_id, _conductor_instance_no)

        ansible_agent_image = "{}:{}".format(os.environ.get('ANSIBLE_AGENT_IMAGE'), os.environ.get('ANSIBLE_AGENT_IMAGE_TAG'))

        host_mount_path_driver = driver_path
        container_mount_path_driver = os.environ.get('STORAGEPATH') + driver_path
        if not os.path.isdir(container_mount_path_driver):
            os.makedirs(container_mount_path_driver)
        host_mount_path_conductor = conductor_path
        container_mount_path_conductor = os.environ.get('STORAGEPATH') + conductor_path
        unique_name = self.get_unique_name(execution_no)

        # generate execute manifest
        fileSystemLoader = FileSystemLoader(searchpath="./templates")
        env = Environment(loader=fileSystemLoader)
        template = env.get_template('k8s_pod.yml')
        exec_manifest = "%s/.tmp/.k8s_pod.yml" % (container_mount_path_driver)

        # #2079 /storage配下は/tmpを経由してアクセスする
        obj = storage_write()
        obj.open(exec_manifest, 'w')
        obj.write(template.render(
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
        obj.close()

        # create command string
        command = ["/usr/local/bin/kubectl", "apply", "-f", exec_manifest]

        # kubectl apply -f file -n namespace
        cp = subprocess.run(' '.join(command), capture_output=True, shell=True, text=True)

        if cp.returncode == 0:
            return True, cp.stdout
        else:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"function": "container_start_up", "return_code": cp.returncode, "stderr": cp.stderr}

    def is_container_running(self, execution_no):
        """
        コンテナ(Pod)が実行中か確認する
        """
        # runningのものが一つだけ存在しているか確認
        return_code, status, errmsg = self._check_status(execution_no)
        g.applogger.debug("Container Status=" + status)
#        if return_code == 0 and status == "running":
        if return_code == 0 and status.lower() in ["running", "pending"]:
            return True,

        return False, {"function": "is_container_running", "return_code": return_code, "stderr": "not running"}

    def container_kill(self, ansConstObj, execution_no):
        """
        コンテナ(Pod)を削除する
        """
        # create command string
        ansible_role_driver_middle_path = "driver/ansible/%s" % (ansConstObj.vg_OrchestratorSubId_dir)
        container_mount_path_driver = os.path.join(os.environ.get("STORAGEPATH"), self._organization_id, self._workspace_id, ansible_role_driver_middle_path, execution_no)  # noqa E501
        exec_manifest = "%s/.tmp/.k8s_pod.yml" % (container_mount_path_driver)

        command = ["/usr/local/bin/kubectl", "delete", "-f", exec_manifest, "--force=true", "--grace-period=0"]

        cp = subprocess.run(' '.join(command), capture_output=True, shell=True, text=True)
        if cp.returncode != 0:
            # cp.check_returncode()  # 例外を発生させたい場合
            return False, {"function": "container_kill", "return_code": cp.returncode, "stderr": cp.stderr}

        return True, cp.stdout

    def container_clean(self, ansConstObj, execution_no):
        """
        実行完了しているコンテナ(Pod)があれば削除する
        """
        return_code, status, errmsg = self._check_status(execution_no)
        if status in ["Succeeded", "Failed"]:
            retBool, retCon = self.container_kill(ansConstObj, execution_no)
            if retBool is False:
                retCon["function"] = "container_clean"
            return retBool, retCon

        g.applogger.debug("not exist completed container, nothing to do.")
        return True,

    def _check_status(self, execution_no):
        """
        コンテナ(Pod)のステータスを確認する
        """
        # create command string
        unique_name = self.get_unique_name(execution_no)
        command = ["/usr/local/bin/kubectl", "get", "pod", unique_name, "-o", "json"]

        cp = subprocess.run(' '.join(command), capture_output=True, shell=True, text=True)
        if cp.returncode != 0:
            # cp.check_returncode()  # 例外を発生
            return cp.returncode, "error", cp.stderr

        try:
            result_obj = json.loads(cp.stdout)
            status = result_obj['status']['phase']
        except Exception as e:
            # Exceptionなのでapplogger.errorで出力
            g.applogger.error(str(e))
            g.applogger.error("stdout:\n%s" % cp.stdout.decode('utf-8'))

            return 1, "error", str(e)

        return cp.returncode, status, ""
