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


from genericpath import isfile
import os
import pathlib
import shutil
import inspect
import subprocess
import time
import json
import re
import asyncio
import datetime
import sys

from flask import g

from common_libs.common.util import ky_decrypt, ky_file_decrypt
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst
from common_libs.ansible_driver.classes.menu_required_check import AuthTypeParameterRequiredCheck
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiConfig import AnsibleTowerRestApiConfig
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiExecutionEnvironment import AnsibleTowerRestApiExecutionEnvironment
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiOrganizations import AnsibleTowerRestApiOrganizations
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiInstanceGroups import AnsibleTowerRestApiInstanceGroups
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiCredentials import AnsibleTowerRestApiCredentials
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiProjects import AnsibleTowerRestApiProjects
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApirPassThrough import AnsibleTowerRestApirPassThrough
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiInventories import AnsibleTowerRestApiInventories
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiInventoryHosts import AnsibleTowerRestApiInventoryHosts
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiJobTemplates import AnsibleTowerRestApiJobTemplates
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiWorkflowJobTemplates import AnsibleTowerRestApiWorkflowJobTemplates
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiWorkflowJobTemplateNodes import AnsibleTowerRestApiWorkflowJobTemplateNodes
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiWorkflowJobs import AnsibleTowerRestApiWorkflowJobs
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiJobs import AnsibleTowerRestApiJobs
from common_libs.ansible_driver.functions.ansibletowerlibs import AnsibleTowerCommonLib as FuncCommonLib
from common_libs.ansible_driver.functions.util import getFileupLoadColumnPath, getInputDataTempDir, getDataRelayStorageDir, get_AnsibleDriverTmpPath, get_AnsibleDriverShellPath, getAnsibleExecutDirPath, getAACListSSHPrivateKeyUploadDirPath


class ExecuteDirector():

    """
    【概要】
        AnsibleTower 作業実行管理(Tower側) クラス
    """

    def __init__(self, driver_id, restApiCaller, logger, dbAccess, exec_out_dir, ifInfoRow, JobTemplatePropertyParameterAry={}, JobTemplatePropertyNameAry={}, TowerProjectsScpPath={}, TowerInstanceDirPath={}):

        self.version = None

        self.restApiCaller = restApiCaller
        self.dbAccess = dbAccess
        self.exec_out_dir = exec_out_dir
        self.JobTemplatePropertyParameterAry = JobTemplatePropertyParameterAry
        self.JobTemplatePropertyNameAry = JobTemplatePropertyNameAry

        self.dataRelayStoragePath = ""
        self.MultipleLogFileJsonAry = ""
        self.MultipleLogMark = ""
        self.JobDetailAry = {}
        self.workflowJobNodeAry = {}
        self.workflowJobAry = {}
        self.workflowJobNodeIdAry = {}
        self.jobFileList = {}
        self.jobLogFileList = []
        self.jobOrgLogFileList = {}
        self.restinfo = {}
        self.AnsibleExecMode = ifInfoRow["ANSIBLE_EXEC_MODE"]

        self.vg_TowerProjectsScpPathArray = TowerProjectsScpPath
        self.vg_TowerInstanceDirPath = TowerInstanceDirPath

        self.php_array = lambda x: x.items() if isinstance(x, dict) else enumerate(x)

        self.driver_id = driver_id
        if driver_id == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
            self.AnsConstObj = AnsrConst()

    def setTowerVersion(self, version):

        self.version = version

    def getTowerVersion(self):

        return self.version

    def build(self, GitObj, exeInsRow, ifInfoRow, TowerHostList):
        vg_tower_driver_name = AnsrConst.vg_tower_driver_name
        execution_no = exeInsRow['EXECUTION_NO']
        proj_name = '%s_%s' % (vg_tower_driver_name, execution_no)
        virtualenv_name = ''  # exeInsRow['I_VIRTUALENV_NAME']
        # AACの実行環境確認
        # 実行エンジンがAAC以外はI_EXECUTION_ENVIRONMENT_NAMEは空なので、実行エンジンのチェックはしない
        execution_environment_id = False
        execution_environment_name = exeInsRow['I_EXECUTION_ENVIRONMENT_NAME']
        if execution_environment_name:
            response_array = AnsibleTowerRestApiExecutionEnvironment().get(self.restApiCaller)

            if not response_array['success']:
                errorMessage = g.appmsg.get_api_message("MSG-10685", [execution_environment_name])
                self.errorLogOut(errorMessage)
                return -1, TowerHostList

            if 'responseContents' not in response_array:
                errorMessage = g.appmsg.get_api_message("MSG-10685", [execution_environment_name])
                self.errorLogOut(errorMessage)
                return -1, TowerHostList

            if 'results' not in response_array['responseContents']:
                errorMessage = g.appmsg.get_api_message("MSG-10685", [execution_environment_name])
                self.errorLogOut(errorMessage)
                return -1, TowerHostList

            if response_array['responseContents']['results'] is not None:
                for no, paramList in self.php_array(response_array['responseContents']['results']):
                    if paramList['name'] == execution_environment_name:
                        execution_environment_id = paramList['id']
                        break

            if execution_environment_id is False:
                errorMessage = g.appmsg.get_api_message("MSG-10686", [execution_environment_name])
                self.errorLogOut(errorMessage)
                return -1, TowerHostList

        OrganizationName = ifInfoRow['ANSTWR_ORGANIZATION']
        if len(OrganizationName) > 0:
            # 組織情報取得
            #    [[Inventory]]
            query = "?name=%s" % (OrganizationName)
            response_array = AnsibleTowerRestApiOrganizations().getAll(self.restApiCaller, query)
            if not response_array['success']:
                g.applogger.error(response_array['responseContents']['errorMessage'])
                errorMessage = g.appmsg.get_api_message("MSG-10671", [OrganizationName])
                self.errorLogOut(errorMessage)
                return -1, TowerHostList

            if ('responseContents' not in response_array or response_array['responseContents'] is None 
                or (type(response_array['responseContents']) in (list, dict) and len(response_array['responseContents']) <= 0)) \
            or ("id" not in response_array['responseContents'][0]):
                g.applogger.error("No inventory id. (prepare)")
                errorMessage = g.appmsg.get_api_message("MSG-10672", [OrganizationName])
                self.errorLogOut(errorMessage)
                return -1, TowerHostList

            OrganizationId = response_array['responseContents'][0]['id']

        else:
            # 組織名未登録
            errorMessage = g.appmsg.get_api_message("MSG-10677")
            self.errorLogOut(errorMessage)
            return -1, TowerHostList

        # Host情報取得
        inventoryForEachCredentials = {}
        ret, inventoryForEachCredentials = self.getHostInfo(exeInsRow, inventoryForEachCredentials)
        if not ret:
            # MSG-10649 = "ホスト情報の取得に失敗しました。"
            errorMessage = g.appmsg.get_api_message("MSG-10649")
            self.errorLogOut(errorMessage)
            return -1, TowerHostList

        # 複数の認証情報によりログが分割されるか確認
        if len(inventoryForEachCredentials) != 1:
            self.settMultipleLogMark(execution_no, ifInfoRow['ANSIBLE_STORAGE_PATH_LNX'])

        # AnsibleTowerHost情報取得
        self.dataRelayStoragePath = ifInfoRow['ANSIBLE_STORAGE_PATH_LNX']
        TowerHostList = []
        ret, TowerHostList = self.getTowerHostInfo(execution_no, ifInfoRow['ANSTWR_HOST_ID'], ifInfoRow['ANSIBLE_STORAGE_PATH_LNX'], TowerHostList)
        if not ret:
            # AnsibleTowerホスト一覧の取得に失敗しました
            errorMessage = g.appmsg.get_api_message("MSG-10680")
            self.errorLogOut(errorMessage)
            return -1, TowerHostList

        if len(TowerHostList) <= 0:
            # AnsibleTowerホスト一覧に有効なホスト情報が登録されていません。
            errorMessage = g.appmsg.get_api_message("MSG-10681")
            self.errorLogOut(errorMessage)
            return -1, TowerHostList

        # Gitリポジトリに展開する資材を作業ディレクトリに作成
        # tmp_path_ary["DIR_NAME"]: /storage/org1/workspace-1/tmp/driver/ansible/legacy_role_作業番号
        tmp_path_ary = getInputDataTempDir(execution_no, vg_tower_driver_name)
        ret = self.createMaterialsTransferTempDir(execution_no, ifInfoRow, TowerHostList, tmp_path_ary["DIR_NAME"])
        if not ret:
            return -1, TowerHostList

        # 実行エンジンを判定  AACの場合にAnsible Automation Controllerと連携するGitリポジトリを作成
        if self.AnsibleExecMode == AnscConst.DF_EXEC_MODE_AAC:

            srcFiles = '%s/*' % (tmp_path_ary["DIR_NAME"])
            ret = self.createGitRepo(GitObj, srcFiles, execution_no)
            if ret is False:
                return -1, TowerHostList

        tmp_path_ary = getInputDataTempDir(execution_no, vg_tower_driver_name)
        ret = self.MaterialsTransferToTower(execution_no, ifInfoRow, TowerHostList, tmp_path_ary['DIR_NAME'])
        if not ret:
            errorMessage = g.appmsg.get_api_message("MSG-10683")
            self.errorLogOut(errorMessage)
            return -1, TowerHostList

        # project生成
        # Git連携用 認証情報生成
        if self.AnsibleExecMode == AnscConst.DF_EXEC_MODE_AAC:
            # 不要だから消した
            # # Git連携用 認証情報生成
            # # 間違っている
            # credential = {}
            # credential['username'] = ifInfoRow["ANS_GIT_USER"]
            # credential['ssh_key_data'] = self.getGitSshKeyFileContent(ifInfoRow["ANSIBLE_IF_INFO_ID"], ifInfoRow["ANS_GIT_SSH_KEY_FILE"])
            # credential['ssh_key_unlock'] = ky_decrypt(ifInfoRow["ANS_GIT_SSH_KEY_FILE_PASSPHRASE"])

            # 不要だから消した
            # print("Git連携用 認証情報生成")
            # git_credentialId = self.createGitCredential(execution_no, credential, OrganizationId)
            # if git_credentialId == -1:
            #     errorMessage = g.appmsg.get_api_message("MSG-10687")
            #     self.errorLogOut(errorMessage)
            #     return -1, TowerHostList

            # project生成  scmタイプ:git
            addParam = {}
            addParam["scm_type"] = AnsibleTowerRestApiProjects.SCMTYPE_GIT
            addParam["scm_url"] = GitObj.get_http_repo_url(proj_name)
            # 不要だから消した
            # addParam["credential"] = git_credentialId

            response_array = self.createProject(execution_no, OrganizationId, virtualenv_name, addParam)
            if response_array == -1:
                errorMessage = g.appmsg.get_api_message("MSG-10650")
                self.errorLogOut(errorMessage)
                return -1, TowerHostList

            projectId = response_array['responseContents']['id']
            # project_updatesオブジェクトは明示的に削除する必要なし
            ret = self.createProjectStatusCheck(response_array)
            if ret is not True:
                # エラーログはcreateProjectStatusCheckで出力
                return -1, TowerHostList

        # ansible vault認証情報生成
        vault_credentialId = -1
        vault_password = ky_decrypt(ifInfoRow["ANSIBLE_VAULT_PASSWORD"])
        vault_credentialId = self.createVaultCredential(execution_no, vault_password, OrganizationId)
        if vault_credentialId == -1:
            errorMessage = g.appmsg.get_api_message("MSG-10678")
            self.errorLogOut(errorMessage)
            return -1, TowerHostList

        jobTemplateIds = []
        loopCount = 1
        for dummy, data in inventoryForEachCredentials.items():
            # 認証情報生成
            credentialId = self.createEachCredential(execution_no, loopCount, data['credential'], OrganizationId)
            if credentialId == -1:
                errorMessage = g.appmsg.get_api_message("MSG-10651")
                self.errorLogOut(errorMessage)
                return -1, TowerHostList

            # インベントリ生成
            inventoryId = self.createEachInventory(execution_no, loopCount, data['inventory'], OrganizationId)
            if inventoryId == -1:
                errorMessage = g.appmsg.get_api_message("MSG-10652")
                self.errorLogOut(errorMessage)
                return -1, TowerHostList

            # ジョブテンプレート生成
            jobTemplateId = self.createEachJobTemplate(execution_no, loopCount, projectId, credentialId, vault_credentialId, inventoryId, exeInsRow['RUN_MODE'], execution_environment_id)
            if jobTemplateId == -1:
                errorMessage = g.appmsg.get_api_message("MSG-10653")
                self.errorLogOut(errorMessage)
                return -1, TowerHostList

            #######################################################################
            # JobTemplateにcredentialIdを紐づけ(Ansible Tower3.6～)
            #######################################################################
            # ---- Ansible Tower Version Check (Not Ver3.5)
            if self.getTowerVersion() not in [AnscConst.TOWER_VER35, str(AnscConst.TOWER_VER35)]:

                response_array = AnsibleTowerRestApiJobTemplates.postCredentialsAdd(self.restApiCaller, jobTemplateId, credentialId)
                if not response_array['success']:
                    errorMessage = g.appmsg.get_api_message("MSG-10679")
                    self.errorLogOut(errorMessage)
                    return -1, TowerHostList

                response_array = AnsibleTowerRestApiJobTemplates.postCredentialsAdd(self.restApiCaller, jobTemplateId, vault_credentialId)
                if not response_array['success']:
                    errorMessage = g.appmsg.get_api_message("MSG-10679")
                    self.errorLogOut(errorMessage)
                    return -1, TowerHostList
            # Ansible Tower Version Check (Not Ver3.5) ----

            jobTemplateIds.append(jobTemplateId)
            loopCount = loopCount + 1

        # ジョブテンプレートをワークフローに結合
        workflowTplId = self.createWorkflowJobTemplate(execution_no, jobTemplateIds, OrganizationId)
        if workflowTplId == -1:
            errorMessage = g.appmsg.get_api_message("MSG-10654")
            self.errorLogOut(errorMessage)
            return -1, TowerHostList

        return workflowTplId, TowerHostList

    def transfer(self, execution_no, TowerHostList):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name
        allResult = True

        ret = self.ResultFileTransfer(execution_no, TowerHostList)
        if not ret:
            allResult = False

        return allResult

    def delete(self, GitObj, execution_no, TowerHostList):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name
        allResult = True

        # Gitリポジトリ削除
        try:
            project_id = self.getGitProjectId(self.driver_id, execution_no)
            GitObj.delete_project(project_id)
        except Exception as e:
            # Gitリポジトリ削除に失敗した場合、ログを出力してエラーとして扱わない
            log = str(e)
            g.applogger.error(log)
            
        # Ansible Automation Controller側の/var/lib/exastro配下の該当ディレクトリ削除
        ret = self.MaterialsDelete("ExastroPath", execution_no, TowerHostList)
        if not ret:
            allResult = False

        # Gitリポジトリに展開する資材を作業ディレクトリを削除
        ret = self.deleteMaterialsTransferTempDir(execution_no)

        # Ansible Automation Controllerと連携するGitリポジトリを削除
        if self.AnsibleExecMode == AnscConst.DF_EXEC_MODE_AAC:
            repositories_base_path = "%s/driver/ansible/git_repositories/%s_%s" % (getDataRelayStorageDir(), self.AnsConstObj.vg_tower_driver_name, execution_no)
            self.GitRepoDirDelete(repositories_base_path)

        # ジョブテンプレート名でジョブテンプレートを抽出
        # 抽出したジョブテンプレートIDでジョブテンプレートの情報取得
        # ジョブテンプレートに紐づいているジョブを削除
        # /api/v2/job_templates/?name__startswith=ita_(driver_name)_executions_jobtpl_(execution_no)
        # /api/v2/jobs/?job_template=(job template id)
        # /api/v2/jobs/(job id)/
        ret = self.cleanUpJob(execution_no)
        if not ret:
            allResult = False

        # ジョブテンプレート名に紐づくジョブテンプレートを抽出
        # 抽出したジョブテンプレートのIDでジョブテンプレートを削除
        # /api/v2/job_templates/?name__startswith=ita_(driver name)_executions_jobtpl_(execution_no)
        # /api/v2/job_templates/(job template id)/
        ret = self.cleanUpJobTemplate(execution_no)
        if not ret:
            allResult = False

        # ワークフロージョブテンプレート名でワークフロージョブテンプレートを抽出
        # ワークフロージョブテンプレートIDに紐づくワークフロージョブノードを抽出
        # 抽出されたワークフロージョブノードを削除
        # /api/v2/workflow_job_templates/?name=ita_legacy_executions_workflowtpl_0000010442
        # /api/v2/workflow_job_template_nodes/?workflow_job_template=2689
        # /api/v2/workflow_job_template_nodes/828/
        # ワークフロージョブテンプレート名でワークフロージョブテンプレートを抽出
        # 抽出されたワークフロージョブテンプレートを削除
        # /api/v2/workflow_job_templates/?name=ita_legacy_executions_workflowtpl_0000010442
        # /api/v2/workflow_job_templates/2293/
        ret = self.cleanUpWorkflowJobTemplate(execution_no)
        if not ret:
            allResult = False

        # ワークフローとテンプレート名(Job slice)ワークフローを抽出
        # 抽出したワークフローを削除
        # ワークフローノードは削除不要
        # /api/v2/workflow_jobs/?name__startswith=ita_(driver_name)_executions&name__contains=(execution_no)
        # /api/v2/workflow_jobs/(work flow id)/
        ret = self.cleanUpWorkflowJobs(execution_no)
        if not ret:
            allResult = False

        # Git連携用 認証情報を抽出
        # 抽出したワークフローを削除
        if self.AnsibleExecMode == AnscConst.DF_EXEC_MODE_AAC:
            ret = self.cleanUpGitCredential(execution_no)
            if not ret:
                allResult = False

        # /api/v2/projects/?name=ita_legacy_executions_project_(execution_no)
        # /api/v2/projects/2666/
        ret = self.cleanUpProject(execution_no)
        if not ret:
            allResult = False

        # /api/v2/credentials/?name__startswith=ita_legacy_executions_vault_credential_0000010436
        # /api/v2/credentials/1612/
        ret = self.cleanUpCredential(execution_no)
        if not ret:
            allResult = False

        # /api/v2/credentials/?name__startswith=ita_legacy_executions_vault_credential_0000010436
        # /api/v2/credentials/1612/
        ret = self.cleanUpVaultCredential(execution_no)
        if not ret:
            allResult = False

        # /api/v2/inventories/?name__startswith=ita_legacy_executions_inventory_0000010436
        # /api/v2/inventories/1030/hosts/
        # /api/v2/hosts/1622/
        # /api/v2/inventories/?name__startswith=ita_legacy_executions_inventory_0000010436
        # /api/v2/inventories/1030/
        ret = self.cleanUpInventory(execution_no)
        if not ret:
            allResult = False

        return allResult

    def launchWorkflow(self, wfJobTplId):

        param = {"wfJobTplId" : wfJobTplId}
        response_array = AnsibleTowerRestApiWorkflowJobTemplates.launch(self.restApiCaller, param)
        if not response_array['success']:
            g.applogger.error(response_array['responseContents']['errorMessage'])
            return -1

        if "id" not in response_array['responseContents']:
            g.applogger.error("No workflow-job id.")
            return -1

        wfJobId = response_array['responseContents']['id']

        return wfJobId

    def createMaterialsTransferTempDir(self, execution_no, ifInfoRow, TowerHostList, tmp_path):

        result_code = True

        ###########################################################
        # 一時ディレクトリを削除
        # src path: /storage/org1/workspace-1/tmp/driver/ansible/legacy_role_作業番号
        ###########################################################
        src_path = tmp_path
        if os.path.exists(src_path):
            cmd = ["/bin/rm", "-rf", src_path]
            try:
                ret = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            except Exception as e:
                log = str(e)
                log = '%s\n%s' % (log, g.appmsg.get_api_message("MSG-10017", [cmd]))
                self.errorLogOut(log)
                g.applogger.error(log)
                return False

        ###########################################################
        # in配下を一時ディレクトリにコピー
        # src  path: /storage/org1/workspace-1/driver/ansible/legacy_role/作業番号/in
        # dest path: /storage/org1/workspace-1/tmp/driver/ansible/legacy_role_作業番号
        ###########################################################
        src_path = getAnsibleExecutDirPath(self.driver_id, execution_no) + "/in"
        dest_path = tmp_path
        cmd = ["/bin/cp", "-rfp", src_path, dest_path]
        try:
            ret = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except Exception as e:
            log = str(e)
            log = '%s\n%s' % (log, g.appmsg.get_api_message("MSG-10017", [cmd]))
            self.errorLogOut(log)
            g.applogger.error(log)
            return False

        ###########################################################
        # out配下を一時ディレクトリ配下にコピー
        # src  path: /storage/org1/workspace-1/driver/ansible/legacy_role/作業番号/out
        # dest path: /storage/org1/workspace-1/tmp/driver/ansible/legacy_role_作業番号/__ita_out_dir__
        ###########################################################
        src_path = self.vg_TowerProjectsScpPathArray[AnscConst.DF_SCP_OUT_ITA_PATH]
        dest_path = self.vg_TowerProjectsScpPathArray[AnscConst.DF_GITREPO_OUT_PATH]
        cmd = ["/bin/cp", "-rfp", src_path, dest_path]
        try:
            ret = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except Exception as e:
            log = str(e)
            log = '%s\n%s' % (log, g.appmsg.get_api_message("MSG-10017", [cmd]))
            self.errorLogOut(log)
            g.applogger.error(log)
            return False

        ###########################################################
        # tmp配下を一時ディレクトリ配下にコピー
        # src  path: /storage/org1/workspace-1/driver/ansible/legacy_role/作業番号/tmp'
        # dest path: /storage/org1/workspace-1/tmp/driver/ansible/legacy_role_作業番号/__ita_tmp_dir__
        ###########################################################
        src_path = self.vg_TowerProjectsScpPathArray[AnscConst.DF_SCP_TMP_ITA_PATH]
        dest_path = self.vg_TowerProjectsScpPathArray[AnscConst.DF_GITREPO_TMP_PATH]
        cmd = ["/bin/cp", "-rfp", src_path, dest_path]
        try:
            ret = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except Exception as e:
            log = str(e)
            log = '%s\n%s' % (log, g.appmsg.get_api_message("MSG-10017", [cmd]))
            self.errorLogOut(log)
            g.applogger.error(log)
            return False

        ###########################################################
        # conductor/インスタンス番号配下を一時ディレクトリ配下にコピー
        # src  path:  /storage/org1/workspace-1/driver/conductor/conductorインスタンス番号
        # dest path:  /storage/org1/workspace-1/tmp/driver/ansible/legacy_role_作業番号/__ita_tmp_dir__/__ita_conductor_dir__/conductorインスタンス番号
        ###########################################################
        if AnscConst.DF_SCP_CONDUCTOR_ITA_PATH in self.vg_TowerProjectsScpPathArray:
            src_path = self.vg_TowerProjectsScpPathArray[AnscConst.DF_SCP_CONDUCTOR_ITA_PATH]
            dest_path = self.vg_TowerProjectsScpPathArray[AnscConst.DF_GITREPO_CONDUCTOR_PATH]
            cmd = ["/bin/cp", "-rfp", src_path, dest_path]
            try:
                ret = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            except Exception as e:
                log = str(e)
                log = '%s\n%s' % (log, g.appmsg.get_api_message("MSG-10017", [cmd]))
                self.errorLogOut(log)
                g.applogger.error(log)
                return False
        return result_code

    def MaterialsTransferToTower(self, execution_no, ifInfoRow, TowerHostList, srcBasePath):

        tmp_TowerInfo_File = '%s/.ky_ansible_materials_transfer_TowerInfo_%s.log' % (get_AnsibleDriverTmpPath(), os.getpid())
        if os.path.isfile(tmp_TowerInfo_File):
            os.unlink(tmp_TowerInfo_File)

        tmp_log_file = '%s/.ky_ansible_materials_transfer_logfile_%s.log' % (get_AnsibleDriverTmpPath(), os.getpid())
        if os.path.isfile(tmp_log_file):
            os.unlink(tmp_log_file)

        result_code = True
        for credential in TowerHostList:

            ###########################################################
            # exastro用Towerプロジェクトディレクトリ配下(/var/lib/exastro)に資材コピー
            ###########################################################
            src_path = srcBasePath
            dest_path = self.getMaterialsTransferDestinationPath("ExastroPath", execution_no)
            info = (
                "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\n"
            ) % (
                credential['host_name'],
                credential['auth_type'],
                credential['username'],
                credential['password'],
                credential['ssh_key_file'],
                src_path,
                dest_path,
                credential['ssh_key_file_pass'],
                os.environ.get("PYTHONPATH", "/exastro"),
                "ITA"
            )

            try:
                pathlib.Path(tmp_TowerInfo_File).write_text(info)

            except Exception:
                errorMessage = g.appmsg.get_api_message("MSG-10570")
                self.errorLogOut(errorMessage)
                g.applogger.error(errorMessage)
                return False

            cmd = ["sh", "%s/%s" % (get_AnsibleDriverShellPath(), "ky_ansible_materials_transfer.sh"), tmp_TowerInfo_File]
            try:
                with open(tmp_log_file, 'a') as fp:
                    
                    ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)

            except Exception:
                log = pathlib.Path(tmp_log_file).read_text()
                self.errorLogOut(log)
                g.applogger.error(log)
                errorMessage = g.appmsg.get_api_message("MSG-10682", [credential['host_name']])
                self.errorLogOut(errorMessage)
                g.applogger.error(errorMessage)
                return False

            if os.path.isfile(tmp_log_file):
                os.unlink(tmp_log_file)

            if os.path.isfile(tmp_TowerInfo_File):
                os.unlink(tmp_TowerInfo_File)

            if credential['node_type'] == AnscConst.DF_CONTROL_NODE:
                # 実行エンジンを判定  Towerの場合にTowerプロジェクトディレクトリ(/var/lib/awx/projects)に資材展開
                """
                if self.AnsibleExecMode == AnscConst.DF_EXEC_MODE_TOWER:
                    ###########################################################
                    # 制御ノードの場合にTowerプロジェクトディレクトリ配下(/var/lib/awx/projects)に資材コピー
                    ###########################################################
                    src_path = self.getMaterialsTransferDestinationPath("ExastroPath", execution_no)
                    dest_path = self.getMaterialsTransferDestinationPath("TowerPath", execution_no)
                    info = (
                        "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\n"
                    ) % (
                        credential['host_name'],
                        credential['auth_type'],
                        credential['username'],
                        credential['password'],
                        credential['ssh_key_file'],
                        src_path,
                        dest_path,
                        credential['ssh_key_file_pass'],
                        os.environ.get("PYTHONPATH", "/exastro")
                    )

                    try:
                        pathlib.Path(tmp_TowerInfo_File).write_text(info)

                    except Exception as e:
                        errorMessage = g.appmsg.get_api_message("MSG-10570")
                        self.errorLogOut(errorMessage)
                        g.applogger.error(errorMessage)
                        return False

                    cmd = ["sh", "%s/%s" % (get_AnsibleDriverShellPath(), "ky_ansible_materials_remotecopy.sh"), tmp_TowerInfo_File]
                    try:
                        with open(tmp_log_file, 'a') as fp:
                            ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)

                    except Exception:
                        log = pathlib.Path(tmp_log_file).read_text()
                        self.errorLogOut(log)
                        g.applogger.error(log)
                        errorMessage = g.appmsg.get_api_message("MSG-10682", [credential['host_name']])
                        self.errorLogOut(errorMessage)
                        g.applogger.error(errorMessage)
                        return False
                """

                if os.path.isfile(tmp_log_file):
                    os.unlink(tmp_log_file)

                if os.path.isfile(tmp_TowerInfo_File):
                    os.unlink(tmp_TowerInfo_File)

        return result_code

    def MaterialsDelete(self, PathId, execution_no, TowerHostList):

        root_dir_path = os.environ.get("PYTHONPATH", "/exastro")

        dest_path = self.getMaterialsTransferDestinationPath(PathId, execution_no)
        tmp_log_file = '%s/.ky_ansible_materials_delete_logfile_%s.log' % (get_AnsibleDriverTmpPath(), os.getpid())

        result_code = True
        for credential in TowerHostList:

            # 実行ノードの場合、Towerプロジェクトディレクトリ配下(/var/lib/awx/projects)は無いので削除対象外
            if (credential['node_type'] != AnscConst.DF_CONTROL_NODE) and (PathId == "TowerPath"):
                continue

            tmp_TowerInfo_File = '%s/.ky_ansible_materials_delete_TowerInfo_%s.log' % (get_AnsibleDriverTmpPath(), os.getpid())
            if os.path.isfile(tmp_TowerInfo_File):
                os.unlink(tmp_TowerInfo_File)

            info = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\n" % (
                credential['host_name'],
                credential['auth_type'],
                credential['username'],
                credential['password'],
                credential['ssh_key_file'],
                dest_path, credential['ssh_key_file_pass'],
                root_dir_path
            )

            try:
                pathlib.Path(tmp_TowerInfo_File).write_text(info)

            except Exception as e:
                errorMessage = g.appmsg.get_api_message("MSG-10570")
                self.errorLogOut(errorMessage)
                g.applogger.error(errorMessage)
                result_code = False

            else:
                cmd = ["sh", "%s/%s" % (get_AnsibleDriverShellPath(), "ky_ansible_materials_delete.sh"), tmp_TowerInfo_File]
                try:
                    with open(tmp_log_file, 'a') as fp:
                        ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)

                except Exception as e:
                    log = pathlib.Path(tmp_log_file).read_text()
                    g.applogger.error(log)
                    errorMessage = g.appmsg.get_api_message("MSG-10684", [credential['host_name'], dest_path])
                    self.errorLogOut(errorMessage)
                    g.applogger.error(errorMessage)
                    result_code = False

                if os.path.isfile(tmp_log_file):
                    os.unlink(tmp_log_file)

                if os.path.isfile(tmp_TowerInfo_File):
                    os.unlink(tmp_TowerInfo_File)

        return result_code

    def ResultFileTransfer(self, execution_no, TowerHostList):

        root_dir_path = os.environ.get("PYTHONPATH", "/exastro")

        tmp_TowerInfo_File = '%s/.ky_ansible_resultfile_transfer_TowerInfo_%s.log' % (get_AnsibleDriverTmpPath(), os.getpid())
        if os.path.isfile(tmp_TowerInfo_File):
            os.unlink(tmp_TowerInfo_File)

        tmp_log_file = '%s/.ky_ansible_resultfile_transfer_delete_logfile_%s.log' % (get_AnsibleDriverTmpPath(), os.getpid())
        if os.path.isfile(tmp_log_file):
            os.unlink(tmp_log_file)

        result_code = True
        for credential in TowerHostList:
            ########################################################################################################
            # ITA作業ディレクトリ配下のconductorディレクトリをITAに転送
            # src  path:  /var/lib/exastro/ita_legacy_executions_0000050063/__ita_tmp_dir__/__ita_conductor_dir__/conductorインスタンス番号
            # dest path:  conductor data_relay_storage path(ita)/conductorインスタンス番号
            ########################################################################################################
            if AnscConst.DF_SCP_CONDUCTOR_ITA_PATH in self.vg_TowerProjectsScpPathArray:
                src_path = self.vg_TowerProjectsScpPathArray[AnscConst.DF_SCP_CONDUCTOR_TOWER_PATH]
                dest_path = os.path.dirname(self.vg_TowerProjectsScpPathArray[AnscConst.DF_SCP_CONDUCTOR_ITA_PATH])
                info = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\n" % (
                    credential['host_name'],
                    credential['auth_type'],
                    credential['username'],
                    credential['password'],
                    credential['ssh_key_file'],
                    src_path,
                    dest_path,
                    credential['ssh_key_file_pass'],
                    root_dir_path,
                    "TOWER"
                )

                try:
                    pathlib.Path(tmp_TowerInfo_File).write_text(info)

                except Exception as e:
                    errorMessage = g.appmsg.get_api_message("MSG-10570")
                    self.errorLogOut(errorMessage)
                    g.applogger.error(errorMessage)
                    return False

                else:
                    cmd = ["sh", "%s/%s" % (get_AnsibleDriverShellPath(), "ky_ansible_materials_transfer.sh"), tmp_TowerInfo_File]
                    try:
                        with open(tmp_log_file, 'a') as fp:
                            ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)

                    except Exception as e:
                        log = pathlib.Path(tmp_log_file).read_text()
                        self.errorLogOut(log)
                        g.applogger.error(log)
                        errorMessage = g.appmsg.get_api_message("MSG-10067", [credential['host_name']])
                        self.errorLogOut(errorMessage)
                        g.applogger.error(errorMessage)
                        return False

            if os.path.isfile(tmp_log_file):
                os.unlink(tmp_log_file)

            if os.path.isfile(tmp_TowerInfo_File):
                os.unlink(tmp_TowerInfo_File)

            ########################################################################################################
            # ITA作業ディレクトリ配下のoutディレクトリ(__ita_out_dir__)をITAに転送
            # src   path: /var/lib/exastro/ita_legacy_role_executions_作業番号/__ita_out_dir__
            # dest  path: /storage/org1/workspace-1/driver/ansible/legacy_role/作業番号/out
            ########################################################################################################
            src_path = self.vg_TowerProjectsScpPathArray[AnscConst.DF_SCP_OUT_TOWER_PATH]
            dest_path = self.vg_TowerProjectsScpPathArray[AnscConst.DF_SCP_OUT_ITA_PATH]
            info = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\n" % (
                credential['host_name'],
                credential['auth_type'],
                credential['username'],
                credential['password'],
                credential['ssh_key_file'],
                src_path,
                dest_path,
                credential['ssh_key_file_pass'],
                root_dir_path,
                "TOWER"
            )

            try:
                pathlib.Path(tmp_TowerInfo_File).write_text(info)

            except Exception as e:
                errorMessage = g.appmsg.get_api_message("MSG-10570")
                self.errorLogOut(errorMessage)
                g.applogger.error(errorMessage)
                return False

            else:
                cmd = ["sh", "%s/%s" % (get_AnsibleDriverShellPath(), "ky_ansible_materials_transfer.sh"), tmp_TowerInfo_File]
                try:
                    with open(tmp_log_file, 'a') as fp:
                        ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)

                except Exception as e:
                    log = pathlib.Path(tmp_log_file).read_text()
                    self.errorLogOut(log)
                    g.applogger.error(log)
                    errorMessage = g.appmsg.get_api_message("MSG-10067", [credential['host_name']])
                    self.errorLogOut(errorMessage)
                    g.applogger.error(errorMessage)
                    return False

            if os.path.isfile(tmp_log_file):
                os.unlink(tmp_log_file)

            if os.path.isfile(tmp_TowerInfo_File):
                os.unlink(tmp_TowerInfo_File)

            ########################################################################################################
            # ITA作業ディレクトリ配下の_parameters配下をITAに転送
            # src   path: /var/lib/exastro/ita_legacy_role_executions_作業番号/_parameters
            # dest  path: /storage/org1/workspace-1/driver/ansible/legacy_role/作業番号/in
            ########################################################################################################
            src_path = self.vg_TowerProjectsScpPathArray[AnscConst.DF_SCP_IN_PARAMATERS_TOWER_PATH]
            dest_path = os.path.dirname(self.vg_TowerProjectsScpPathArray[AnscConst.DF_SCP_IN_PARAMATERS_ITA_PATH])
            info = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\n" % (
                credential['host_name'],
                credential['auth_type'],
                credential['username'],
                credential['password'],
                credential['ssh_key_file'],
                src_path,
                dest_path,
                credential['ssh_key_file_pass'],
                root_dir_path,
                "TOWER"
            )

            try:
                pathlib.Path(tmp_TowerInfo_File).write_text(info)

            except Exception as e:
                errorMessage = g.appmsg.get_api_message("MSG-10570")
                self.errorLogOut(errorMessage)
                g.applogger.error(errorMessage)
                return False

            else:
                cmd = ["sh", "%s/%s" % (get_AnsibleDriverShellPath(), "ky_ansible_materials_transfer.sh"), tmp_TowerInfo_File]
                try:
                    with open(tmp_log_file, 'a') as fp:
                        ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)

                except Exception as e:
                    log = pathlib.Path(tmp_log_file).read_text()
                    self.errorLogOut(log)
                    g.applogger.error(log)
                    errorMessage = g.appmsg.get_api_message("MSG-10067", [credential['host_name']])
                    self.errorLogOut(errorMessage)
                    g.applogger.error(errorMessage)
                    return False

            if os.path.isfile(tmp_log_file):
                os.unlink(tmp_log_file)

            if os.path.isfile(tmp_TowerInfo_File):
                os.unlink(tmp_TowerInfo_File)

            ########################################################################################################
            # Towerプロジェクトディレクトリ配下の_parameters_file配下をITAに転送
            # src   path: /var/lib/exastro/ita_legacy_role_executions_作業番号/_parameters_file
            # dest  path: /storage/org1/workspace-1/driver/ansible/legacy_role/作業番号/in
            ########################################################################################################
            src_path = self.vg_TowerProjectsScpPathArray[AnscConst.DF_SCP_IN_PARAMATERS_FILE_TOWER_PATH]
            dest_path = os.path.dirname(self.vg_TowerProjectsScpPathArray[AnscConst.DF_SCP_IN_PARAMATERS_FILE_ITA_PATH])
            info = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\n" % (
                credential['host_name'],
                credential['auth_type'],
                credential['username'],
                credential['password'],
                credential['ssh_key_file'],
                src_path,
                dest_path,
                credential['ssh_key_file_pass'],
                root_dir_path,
                "TOWER"
            )

            try:
                pathlib.Path(tmp_TowerInfo_File).write_text(info)

            except Exception as e:
                errorMessage = g.appmsg.get_api_message("MSG-10570")
                self.errorLogOut(errorMessage)
                g.applogger.error(errorMessage)
                return False

            else:
                cmd = ["sh", "%s/%s" % (get_AnsibleDriverShellPath(), "ky_ansible_materials_transfer.sh"), tmp_TowerInfo_File]
                try:
                    with open(tmp_log_file, 'a') as fp:
                        ret = subprocess.run(cmd, check=True, stdout=fp, stderr=subprocess.STDOUT)

                except Exception as e:
                    log = pathlib.Path(tmp_log_file).read_text()
                    self.errorLogOut(log)
                    g.applogger.error(log)
                    errorMessage = g.appmsg.get_api_message("MSG-10067", [credential['host_name']])
                    self.errorLogOut(errorMessage)
                    g.applogger.error(errorMessage)
                    return False

            if os.path.isfile(tmp_log_file):
                os.unlink(tmp_log_file)

            if os.path.isfile(tmp_TowerInfo_File):
                os.unlink(tmp_TowerInfo_File)

        return result_code

    def getTowerHostInfo(self, execution_no, anstwr_host_id, dataRelayStoragePath, TowerHostList):

        TowerHostList = []

        cols = self.dbAccess.table_columns_get("T_ANSC_TOWER_HOST")
        cols = (',').join(cols[0])

        sql = (
            "SELECT \n"
            "  %s \n"
            "FROM \n"
            "  T_ANSC_TOWER_HOST \n"
            "WHERE \n"
            "  DISUSE_FLAG = '0' \n"
            "FOR UPDATE; \n"
        ) % (cols)

        rows = self.dbAccess.sql_execute(sql)

        chkobj = AuthTypeParameterRequiredCheck()
        for row in rows:
            if 'ANSTWR_ISOLATED_TYPE' in row and row['ANSTWR_ISOLATED_TYPE'] is not None and row['ANSTWR_ISOLATED_TYPE'] > 0:
                node_type = AnscConst.DF_EXECUTE_NODE

            else:
                node_type = AnscConst.DF_CONTROL_NODE

            username = row['ANSTWR_LOGIN_USER']
            password = "undefine"
            if row['ANSTWR_LOGIN_AUTH_TYPE'] == AnscConst.DF_LOGIN_AUTH_TYPE_PW:
                if row['ANSTWR_LOGIN_PASSWORD'] is not None and len(row['ANSTWR_LOGIN_PASSWORD'].strip()) > 0:
                    password = ky_decrypt(row['ANSTWR_LOGIN_PASSWORD'])
                    if len(password) <= 0:
                        password = "undefine"

            sshKeyFile = "undefine"
            if row['ANSTWR_LOGIN_AUTH_TYPE'] in [AnscConst.DF_LOGIN_AUTH_TYPE_KEY, AnscConst.DF_LOGIN_AUTH_TYPE_KEY_PP_USE]:
                sshKeyFile = row['ANSTWR_LOGIN_SSH_KEY_FILE']
                if not sshKeyFile:
                    sshKeyFile = "undefine"

                else:
                    src_file = self.getAnsibleTowerSshKeyFileContent(row['ANSTWR_HOST_ID'], row['ANSTWR_LOGIN_SSH_KEY_FILE'])
                    sshKeyFile = (
                        '%s/in/ssh_key_files/AnsibleTower_%s_%s'
                    ) % getAnsibleExecutDirPath(self.driver_id, execution_no), row['ANSTWR_HOST_ID'], row['ANSTWR_LOGIN_SSH_KEY_FILE']

                    try:
                        shutil.copy(src_file, sshKeyFile)

                    except Exception:
                        errorMessage = g.appmsg.get_api_message("MSG-10636", [os.path.basename(src_file)])
                        self.errorLogOut(errorMessage)
                        return False, TowerHostList

                    # ky_encryptで中身がスクランブルされているので復元する
                    ret = ky_file_decrypt(sshKeyFile, sshKeyFile)
                    if not ret:
                        errorMessage = g.appmsg.get_api_message("MSG-10647", ['',])
                        self.errorLogOut(errorMessage)
                        return False, TowerHostList

                    try:
                        os.chmod(sshKeyFile, 0o600)

                    except Exception:
                        errorMessage = g.appmsg.get_api_message("MSG-10085", [inspect.currentframe().f_lineno])
                        self.errorLogOut(errorMessage)
                        return False, TowerHostList

            sshKeyFilePass = "undefine"
            if row['ANSTWR_LOGIN_AUTH_TYPE'] == AnscConst.DF_LOGIN_AUTH_TYPE_KEY_PP_USE:
                sshKeyFilePass = ky_decrypt(row['ANSTWR_LOGIN_SSH_KEY_FILE_PASS'])
                if len(sshKeyFilePass.strip()) <= 0:
                    sshKeyFilePass = "undefine"

            # 鍵認証(パスフレーズなし)、鍵認証(パスフレーズあり)
            if row['ANSTWR_LOGIN_AUTH_TYPE'] in [AnscConst.DF_LOGIN_AUTH_TYPE_KEY, AnscConst.DF_LOGIN_AUTH_TYPE_KEY_PP_USE]:
                auth_type = "key"

            # 鍵認証(鍵交換済み)
            elif row['ANSTWR_LOGIN_AUTH_TYPE'] == AnscConst.DF_LOGIN_AUTH_TYPE_KEY_EXCH:
                auth_type = "none"

            # パスワード認証
            elif row['ANSTWR_LOGIN_AUTH_TYPE'] == AnscConst.DF_LOGIN_AUTH_TYPE_PW:
                auth_type = "pass"

            credential = {
                "id" : row['ANSTWR_HOST_ID'],
                "host_name" : row['ANSTWR_HOSTNAME'],
                "auth_type" : auth_type,
                "username" : username,
                "password" : password,
                "ssh_key_file" : sshKeyFile,
                "ssh_key_file_pass" : sshKeyFilePass,
                "node_type" : node_type
            }

            TowerHostList.append(credential)

        return True, TowerHostList

    def getHostInfo(self, exeInsRow, inventoryForEachCredentials):

        vg_ansible_pho_linkDB = AnsrConst.vg_ansible_pho_linkDB  # "T_ANSR_TGT_HOST"
        condition = [exeInsRow['OPERATION_ID'], exeInsRow['MOVEMENT_ID']]
        cols = self.dbAccess.table_columns_get(vg_ansible_pho_linkDB)
        cols = (',').join(cols[0])

        sql = (
            "SELECT \n"
            "  %s \n"
            "FROM \n"
            "  %s \n"
            "WHERE \n"
            "  DISUSE_FLAG = '0' \n"
            "  AND OPERATION_ID=%%s \n"
            "  AND MOVEMENT_ID=%%s \n"
            "FOR UPDATE; \n"
        ) % (cols, vg_ansible_pho_linkDB)

        rows = self.dbAccess.sql_execute(sql, condition)
        for ptnOpHostLink in rows:
            hostInfo = self.dbAccess.table_select(
                "T_ANSC_DEVICE",
                "WHERE DISUSE_FLAG='0' AND SYSTEM_ID=%s",
                [ptnOpHostLink['SYSTEM_ID']]
            )

            if len(hostInfo) >= 2:
                raise Exception("There are multiple rows returned for the primary key specification.: %s: %s" % ("T_ANSC_DEVICE", ptnOpHostLink['SYSTEM_ID']))

            if not hostInfo:
                g.applogger.error("Not exists or disabled host. SYSTEM_ID: %s" % (ptnOpHostLink['SYSTEM_ID']))
                return False, inventoryForEachCredentials

            hostInfo = hostInfo[0]
            username = hostInfo['LOGIN_USER']

            # 認証方式:パスワード認証、パスワード認証(winrm)
            password = ""
            if hostInfo['LOGIN_AUTH_TYPE'] in [AnscConst.DF_LOGIN_AUTH_TYPE_PW, AnscConst.DF_LOGIN_AUTH_TYPE_PW_WINRM]:
                password = hostInfo['LOGIN_PW']

            # 認証方式:鍵認証(パスフレーズなし)、鍵認証(パスフレーズあり)
            sshPrivateKey = ""
            if hostInfo['LOGIN_AUTH_TYPE'] in [AnscConst.DF_LOGIN_AUTH_TYPE_KEY, AnscConst.DF_LOGIN_AUTH_TYPE_KEY_PP_USE]:
                if 'SSH_KEY_FILE' in hostInfo and hostInfo['SSH_KEY_FILE']:
                    sshPrivateKey = self.getDeviceListSshKeyFileContent(hostInfo['SYSTEM_ID'], hostInfo['CONN_SSH_KEY_FILE'])
                    # ky_encrptのスクランブルを復号
                    sshPrivateKey = ky_decrypt(sshPrivateKey)

            # 認証方式:鍵認証(パスフレーズあり)
            sshPrivateKeyPass = ""
            if hostInfo['LOGIN_AUTH_TYPE'] == AnscConst.DF_LOGIN_AUTH_TYPE_KEY_PP_USE:
                if 'SSH_KEY_FILE_PASSPHRASE' in hostInfo and hostInfo['SSH_KEY_FILE_PASSPHRASE']:
                    sshPrivateKeyPass = hostInfo['SSH_KEY_FILE_PASSPHRASE']
                    # ky_encrptのスクランブルを復号
                    sshPrivateKeyPass = ky_decrypt(sshPrivateKeyPass)

            instanceGroupId = None
            if 'ANSTWR_INSTANCE_GROUP_NAME' in hostInfo and hostInfo['ANSTWR_INSTANCE_GROUP_NAME']:
                # Towerのインスタンスグループ情報取得
                response_array = AnsibleTowerRestApiInstanceGroups().getAll(self.restApiCaller)
                if not response_array['success']:
                    # 組織名未登録
                    errorMessage = g.appmsg.get_api_message("MSG-10675", [hostInfo['ANSTWR_INSTANCE_GROUP_NAME']])
                    self.errorLogOut(errorMessage)
                    return False, inventoryForEachCredentials

                for info in response_array['responseContents']:
                    if info['name'] == hostInfo['ANSTWR_INSTANCE_GROUP_NAME']:
                        instanceGroupId = info['id']

                if instanceGroupId is None:
                    # インスタンスグループ未登録
                    errorMessage = g.appmsg.get_api_message("MSG-10676", [hostInfo['ANSTWR_INSTANCE_GROUP_NAME']])
                    self.errorLogOut(errorMessage)
                    return False, inventoryForEachCredentials

            credential_type_id = hostInfo['CREDENTIAL_TYPE_ID']

            # 配列のキーに使いたいだけ
            key = (
                'username_%s_password_%s_sshPrivateKey_%s_sshPrivateKeyPass_%s_instanceGroupId_%s_credential_type_id_%s'
            ) % (username, password, sshPrivateKey, sshPrivateKeyPass, instanceGroupId, credential_type_id)
            credential = {
                "username" : username,
                "password" : password,
                "ssh_private_key" : sshPrivateKey,
                "ssh_private_key_pass" : sshPrivateKeyPass,
                "credential_type_id" : credential_type_id,
            }

            inventory = {}
            if key in inventoryForEachCredentials:
                inventory = inventoryForEachCredentials[key]['inventory']

            else:
                # 初回のみインベントリグループ指定
                inventory['instanceGroupId'] = instanceGroupId

            # ホスト情報
            hostData = {}

            # ホストアドレス指定方式
            # null or 1 がIP方式 2 がホスト名方式
            if 'I_ANS_HOST_DESIGNATE_TYPE_ID' not in exeInsRow \
            or not exeInsRow['I_ANS_HOST_DESIGNATE_TYPE_ID'] \
            or exeInsRow['I_ANS_HOST_DESIGNATE_TYPE_ID'] == '1':
                hostData['ansible_ssh_host'] = hostInfo['IP_ADDRESS']
            else:
                hostData['ansible_ssh_host'] = hostInfo['HOST_DNS_NAME']
                
            # WinRM接続
            # 認証方式:パスワード認証(winrm)
            hostData['winrm'] = 0
            if hostInfo['LOGIN_AUTH_TYPE'] == AnscConst.DF_LOGIN_AUTH_TYPE_PW_WINRM:
                hostData['winrm'] = 1
                if not hostInfo['WINRM_PORT']:
                    hostInfo['WINRM_PORT'] = AnscConst.LC_WINRM_PORT

                hostData['winrmPort'] = hostInfo['WINRM_PORT']

                # username/password delete
                if 'WINRM_SSL_CA_FILE' in hostInfo and hostInfo['WINRM_SSL_CA_FILE'] is not None and len(hostInfo['WINRM_SSL_CA_FILE']) > 0:
                    filePath = "winrm_ca_files/%s-%s" % (FuncCommonLib.addPadding(hostInfo['SYSTEM_ID']), hostInfo['WINRM_SSL_CA_FILE'])
                    hostData['ansible_winrm_ca_trust_path'] = filePath

            hostData['hosts_extra_args'] = hostInfo['HOSTS_EXTRA_ARGS']
            hostData['ansible_ssh_extra_args'] = hostInfo['SSH_EXTRA_ARGS']
            if 'hosts' not in inventory:
                inventory['hosts'] = {}

            if hostInfo['HOST_NAME'] not in inventory['hosts']:
                inventory['hosts'][hostInfo['HOST_NAME']] = None

            inventory['hosts'][hostInfo['HOST_NAME']] = hostData

            inventoryForEachCredentials[key] = {
                "credential" : credential,
                "inventory" : inventory,
            }

        return True, inventoryForEachCredentials

    def createProject(self, execution_no, OrganizationId, virtualenv_name, addParam):

        param = addParam
        param['organization'] = OrganizationId
        param['execution_no'] = execution_no

        if len(virtualenv_name) > 0:
            param['custom_virtualenv'] = virtualenv_name

        response_array = AnsibleTowerRestApiProjects.post(self.restApiCaller, param)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return -1

        if "id" not in response_array['responseContents']:
            g.applogger.debug("No project id.")
            return -1

        return response_array

    def createGitCredential(self, execution_no, credential, OrganizationId):

        param = {}
        param['organization'] = OrganizationId
        param['execution_no'] = execution_no

        if 'username' in credential and credential['username']:
            param['username'] = credential['username']

        if 'ssh_key_data' in credential and credential['ssh_key_data']:
            param['ssh_key_data'] = credential['ssh_key_data']

        if 'ssh_key_unlock' in credential and credential['ssh_key_unlock']:
            param['ssh_key_unlock'] = credential['ssh_key_unlock']

        response_array = AnsibleTowerRestApiCredentials.git_post(self.restApiCaller, param)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return -1

        if "id" not in response_array['responseContents']:
            g.applogger.debug("No credential id.")
            return -1

        credentialId = response_array['responseContents']['id']

        return credentialId

    def createEachCredential(self, execution_no, loopCount, credential, OrganizationId):

        param = {}
        param['organization'] = OrganizationId
        param['execution_no'] = execution_no
        param['loopCount'] = loopCount

        if "username" in credential:
            param['username'] = credential['username']

        if "password" in credential:
            param['password'] = credential['password']

        if "ssh_private_key" in credential:
            param['ssh_private_key'] = credential['ssh_private_key']

        if "credential_type_id" in credential:
            param['credential_type_id'] = credential['credential_type_id']

        if "ssh_private_key_pass" in credential:
            param['ssh_private_key_pass'] = credential['ssh_private_key_pass']

        response_array = AnsibleTowerRestApiCredentials.post(self.restApiCaller, param)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return -1

        if "id" not in response_array['responseContents']:
            g.applogger.debug("No credential id.")
            return -1

        credentialId = response_array['responseContents']['id']

        return credentialId

    def createVaultCredential(self, execution_no, vault_password, OrganizationId):

        param = {}
        param['organization'] = OrganizationId
        param['execution_no'] = execution_no
        param['vault_password'] = vault_password

        response_array = AnsibleTowerRestApiCredentials.vault_post(self.restApiCaller, param)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return -1

        if "id" not in response_array['responseContents']:
            g.applogger.debug("No vault credential id.")
            return -1

        vault_credentialId = response_array['responseContents']['id']
        return vault_credentialId

    def createEachInventory(self, execution_no, loopCount, inventory, OrganizationId):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        if "hosts" not in inventory or not inventory['hosts']:
            g.applogger.debug("%s no hosts." % (inspect.currentframe().f_code.co_name))
            return -1

        # inventory
        param = {}
        param['organization'] = OrganizationId
        param['execution_no'] = execution_no
        param['loopCount'] = loopCount

        if "instanceGroupId" in inventory and inventory['instanceGroupId']:
            param['instanceGroupId'] = inventory['instanceGroupId']

        response_array = AnsibleTowerRestApiInventories.post(self.restApiCaller, param)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return -1

        if "id" not in response_array['responseContents']:
            g.applogger.debug("No inventory id.")
            return -1

        inventoryId = response_array['responseContents']['id']

        param['inventoryId'] = inventoryId
        for hostname, hostData in inventory['hosts'].items():
            param['variables'] = None
            param['name'] = hostname

            variables_array = []

            # ホスト名がlocalhostでpioneer実行の場合、インベントリオプションにansible_connection: localを追加
            if hostname == 'localhost' and vg_tower_driver_name == "pioneer":
                variables_array.append("ansible_connection: local")

            variables_array.append("ansible_ssh_host: %s" % hostData['ansible_ssh_host'])

            if hostData['winrm'] == '1':
                variables_array.append("ansible_connection: winrm")
                variables_array.append("ansible_ssh_port: %s" % (hostData['winrmPort']))
                if 'ansible_winrm_ca_trust_path' in hostData and hostData['ansible_winrm_ca_trust_path'] is not None:
                    variables_array.append("ansible_winrm_ca_trust_path: %s" % (hostData['ansible_winrm_ca_trust_path']))

            if 'ansible_ssh_extra_args' in hostData and hostData['ansible_ssh_extra_args'] is not None and len(hostData['ansible_ssh_extra_args'].strip()) > 0:
                variables_array.append("ansible_ssh_extra_args: %s" % (hostData['ansible_ssh_extra_args'].strip()))

            # インベントリファイル追加オプションの空白行を取り除く
            yaml_array = ['',] if hostData['hosts_extra_args'] is None else hostData['hosts_extra_args'].split('\n')
            for record in yaml_array:
                if len(record.strip()) <= 0:
                    continue

                variables_array.append(record)

            # インベントリファイル追加オプションを設定
            if len(variables_array) > 0:
                param['variables'] = '\n'.join(variables_array)

            response_array = AnsibleTowerRestApiInventoryHosts.post(self.restApiCaller, param)
            if not response_array['success']:
                g.applogger.debug(response_array['responseContents']['errorMessage'])
                return -1

        return inventoryId

    def createEachJobTemplate(self, execution_no, loopCount, projectId, credentialId, vault_credentialId, inventoryId, runMode, execution_environment_id):

        vg_parent_playbook_name = AnsrConst.vg_parent_playbook_name

        param = {}
        param['execution_no'] = execution_no
        param['loopCount'] = loopCount
        param['inventory'] = inventoryId
        param['project'] = projectId
        param['playbook'] = vg_parent_playbook_name
        param['credential'] = credentialId

        if execution_environment_id:
            param['execution_environment'] = execution_environment_id

        if vault_credentialId != -1:
            param['vault_credential'] = vault_credentialId

        addparam = {}
        for key, val in self.JobTemplatePropertyParameterAry.items():
            addparam[key] = val

        if runMode == AnscConst.DRY_RUN:
            param['job_type'] = "check"

        response_array = AnsibleTowerRestApiJobTemplates.post(self.restApiCaller, param, addparam)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return -1

        if "id" not in response_array['responseContents']:
            g.applogger.debug("No job-template id.")
            return -1

        jobTemplateId = response_array['responseContents']['id']

        return jobTemplateId

    def createWorkflowJobTemplate(self, execution_no, jobTemplateIds, OrganizationId):

        if not jobTemplateIds:
            g.applogger.debug("%s no job templates." % (inspect.currentframe().f_code.co_name))
            return -1

        param = {}
        param['organization'] = OrganizationId
        param['execution_no'] = execution_no

        response_array = AnsibleTowerRestApiWorkflowJobTemplates.post(self.restApiCaller, param)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return -1

        if "id" not in response_array['responseContents']:
            g.applogger.debug("No workflow-job-template id.")
            return -1

        workflowTplId = response_array['responseContents']['id']
        param['workflowTplId'] = workflowTplId

        loopCount = 1
        for jobtplId in jobTemplateIds:

            param['jobtplId'] = jobtplId
            param['loopCount'] = loopCount

            response_array = AnsibleTowerRestApiWorkflowJobTemplateNodes.post(self.restApiCaller, param)
            if not response_array['success']:
                g.applogger.debug(response_array['responseContents']['errorMessage'])
                return -1

            loopCount = loopCount + 1

        return workflowTplId

    def cleanUpWorkflowJobs(self, execution_no):

        self.workflowJobAry = {}
        ret = self.getworkflowJobs(execution_no)
        if not ret:
            g.applogger.error("Faild to get workflow jobs.")
            return False

        for wfJobId, workflowJobData in self.workflowJobAry.items():
            response_array = AnsibleTowerRestApiWorkflowJobs.delete(self.restApiCaller, wfJobId)
            if not response_array['success']:
                g.applogger.error("Faild to delete workflow job node.")
                g.applogger.error(response_array)
                return False

        return True

    def cleanUpProject(self, execution_no):

        response_array = AnsibleTowerRestApiProjects.deleteRelatedCurrnetExecution(self.restApiCaller, execution_no)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return False

        return True

    def cleanUpCredential(self, execution_no):

        response_array = AnsibleTowerRestApiCredentials.deleteRelatedCurrnetExecution(self.restApiCaller, execution_no)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return False

        return True

    def cleanUpVaultCredential(self, execution_no):

        response_array = AnsibleTowerRestApiCredentials.deleteVault(self.restApiCaller, execution_no)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return False

        return True

    def cleanUpGitCredential(self, execution_no):

        response_array = AnsibleTowerRestApiCredentials.deleteGit(self.restApiCaller, execution_no)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return False

        return True

    def cleanUpInventory(self, execution_no):

        response_array = AnsibleTowerRestApiInventoryHosts.deleteRelatedCurrnetExecution(self.restApiCaller, execution_no)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return False

        response_array = AnsibleTowerRestApiInventories.deleteRelatedCurrnetExecution(self.restApiCaller, execution_no)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return False

        return True

    def cleanUpJobTemplate(self, execution_no):

        response_array = AnsibleTowerRestApiJobTemplates.deleteRelatedCurrnetExecution(self.restApiCaller, execution_no)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return False

        return True

    def cleanUpWorkflowJobTemplate(self, execution_no):

        response_array = AnsibleTowerRestApiWorkflowJobTemplateNodes.deleteRelatedCurrnetExecution(self.restApiCaller, execution_no)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return False

        response_array = AnsibleTowerRestApiWorkflowJobTemplates.deleteRelatedCurrnetExecution(self.restApiCaller, execution_no)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return False

        return True

    def cleanUpJob(self, execution_no):

        response_array = AnsibleTowerRestApiJobs.deleteRelatedCurrnetExecution(self.restApiCaller, execution_no)
        if not response_array['success']:
            g.applogger.debug(response_array['responseContents']['errorMessage'])
            return False

        return True

    def monitoring(self, toProcessRow, ansibleTowerIfInfo):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name
        execution_no = toProcessRow['EXECUTION_NO']
        self.dataRelayStoragePath = ansibleTowerIfInfo['ANSIBLE_STORAGE_PATH_LNX']

        # ジョブワークフローの情報取得
        self.workflowJobAry = {}
        ret = self.getworkflowJobs(execution_no)
        if not ret:
            g.applogger.error("Faild to get workflow jobs.")
            return AnscConst.EXCEPTION

        result_code = {}
        self.JobDetailAry = {}
        self.workflowJobNodeAry = {}

        # ジョブワークフローの状態を確認
        for wfJobId, workflowJobData in self.workflowJobAry.items():
            ret = self.searchworkflowJobNodesJobDetail(execution_no, wfJobId)
            if not ret:
                return AnscConst.EXCEPTION

            # AnsibleTower Status チェック
            status = self.checkWorkflowJobStatus(execution_no, wfJobId)
            result_code[wfJobId] = status

            # Ansibleログ書き出し
            ret = self.createAnsibleLogs(execution_no, wfJobId)
            if not ret:
                result_code[wfJobId] = AnscConst.EXCEPTION

        # ジョブワークフローの状態をマージ
        ststus = self.workflowStatusMerge(result_code)
        name = "エラー"
        if ststus == AnscConst.PREPARE:
            name = "準備中"

        elif ststus == AnscConst.PROCESSING:
            name = "実行中"

        elif ststus == AnscConst.PROCESS_DELAYED:
            name = "実行中(遅延)"

        elif ststus == AnscConst.COMPLETE:
            name = "完了"

        elif ststus == AnscConst.FAILURE:
            name = "完了(異常)"

        elif ststus == AnscConst.EXCEPTION:
            name = "想定外エラー"

        elif ststus == AnscConst.SCRAM:
            name = "緊急停止"

        elif ststus == AnscConst.RESERVE:
            name = "未実行(予約中)"

        elif ststus == AnscConst.RESERVE_CANCEL:
            name = "予約取消"

        return ststus

    def workflowStatusMerge(self, result_code):

        comp_job_count = 0
        run_job_count = 0
        scram_job_count = 0
        exce_job_count = 0
        fail_job_count = 0
        status_error_job_count = 0

        for wfJobId, status in result_code.items():
            if status == AnscConst.COMPLETE:  # 状態:完了のワークフローをカウント
                comp_job_count = comp_job_count + 1

            elif status == AnscConst.PROCESSING:  # 状態:処理中のワークフローをカウント
                run_job_count = run_job_count + 1

            elif status == AnscConst.SCRAM:  # 緊急停止のワークフローをカウント
                scram_job_count = scram_job_count + 1

            elif status == AnscConst.EXCEPTION:  # 想定外エラーのワークフローをカウント
                exce_job_count = exce_job_count + 1

            elif status == AnscConst.FAILURE:  # 異常終了のワークフローをカウント
                fail_job_count = fail_job_count + 1

            else:  # 状態不明のワークフローをカウント
                status_error_job_count = status_error_job_count + 1

        # 状態:処理中のワークフローが1件でもあれば、状態は処理中
        if run_job_count > 0:
            return AnscConst.PROCESSING

        # 全てのワークフローの状態が完了か判定
        if len(result_code) == comp_job_count:
            return AnscConst.COMPLETE

        # 全てのワークフローの状態が緊急停止か判定
        if len(result_code) == scram_job_count:
            return AnscConst.SCRAM

        # 全てのワークフローの状態が想定外エラーか判定
        if len(result_code) == exce_job_count:
            return AnscConst.EXCEPTION

        # 全てのワークフローの状態が異常終了か判定
        if len(result_code) == fail_job_count:
            return AnscConst.FAILURE

        # 状態:完了のワークフローが1件でもあれば、状態:完了(異常)
        if comp_job_count > 0:
            return AnscConst.FAILURE

        # 状態:完了と緊急停止の場合、状態:緊急停止
        if len(result_code) == (comp_job_count + scram_job_count):
            return AnscConst.SCRAM

        # その他、状態が混在している場合、状態:完了(異常)
        g.applogger.error(result_code)

        return AnscConst.FAILURE

    def searchworkflowJobNodesJobDetail(self, execution_no, wfJobId, nodeId_only=False):

        self.workflowJobNodeAry[wfJobId] = []

        # workflow job idに紐づくworkflow job nodeを取得
        # /api/v2/workflow_jobs/(workflow job id)/workflow_nodes/
        query = "%s/workflow_nodes/" % (wfJobId)
        response_array = AnsibleTowerRestApiWorkflowJobs.getAll(self.restApiCaller, query)
        if not response_array['success']:
            g.applogger.error("Faild to rest api access get workflow job nodes.")
            g.applogger.error(response_array)
            return False

        for workflowJobNodeData in response_array['responseContents']:
            wfJobNodeId = workflowJobNodeData['id']
            if wfJobId not in self.JobDetailAry:
                self.JobDetailAry[wfJobId] = {}

            if wfJobNodeId not in self.JobDetailAry[wfJobId]:
                self.JobDetailAry[wfJobId][wfJobNodeId] = None

            self.JobDetailAry[wfJobId][wfJobNodeId] = []
            self.workflowJobNodeAry[wfJobId].append(workflowJobNodeData)

            if nodeId_only is True:
                if wfJobId not in self.workflowJobNodeIdAry:
                    self.workflowJobNodeIdAry[wfJobId] = None

                if not isinstance(self.workflowJobNodeIdAry[wfJobId], list):
                    self.workflowJobNodeIdAry[wfJobId] = []

                self.workflowJobNodeIdAry[wfJobId].append(wfJobNodeId)
                continue

            jobtype = workflowJobNodeData['summary_fields']['job']['type']
            # ジョブスライスが設定されているとスライスされた workfolw job (jobtype = workfolw job)
            # の情報がJob情報として表示される
            # typeが workfolw job のjobの情報はworkfolw jobで取得出来ているので無視
            # typeがjobのデータだけを処理する
            if jobtype == "job":
                JobId = workflowJobNodeData['job']
                # workflow job node IDに紐づくJobを取得
                # /api/v2/jobs/(job id)/
                response_array = AnsibleTowerRestApiJobs.get(self.restApiCaller, JobId)
                if not response_array['success']:
                    g.applogger.error("Faild to rest api access get job detail.")
                    g.applogger.error(response_array)
                    return False

                # データがなくてもエラーにしない
                JobDetail = response_array['responseContents']
                if type(JobDetail) in (list, dict):
                    if len(JobDetail) <= 0:
                        JobDetail = {}

                response_array = AnsibleTowerRestApiJobs.getStdOut(self.restApiCaller, JobId)
                if not response_array['success']:
                    g.applogger.error("Faild to get job stdout. (job id:%s)" % (JobId))
                    g.applogger.error(response_array)
                    return False

                stdout = response_array['responseContents']

                self.JobDetailAry[wfJobId][wfJobNodeId].append(
                    {
                        'JobData' : JobDetail,
                        'stdout' : stdout
                    }
                )

        return True

    def getworkflowJobs(self, execution_no):

        self.workflowJobAry = {}

        # 作業番号に紐づくworkflow jobを取得
        # /api/v2/workflow_jobs/?name__startswith=ita_(drive_name)_executions&name__contains=(execution_no)
        response_array = AnsibleTowerRestApiWorkflowJobs.NameSearch(self.restApiCaller, execution_no)
        if not response_array['success']:
            g.applogger.error("Faild to rest api access get workflow job.")
            g.applogger.error(response_array)
            return False

        for workflowJobData in response_array['responseContents']:
            wfJobId = workflowJobData['id']
            self.workflowJobAry[wfJobId] = workflowJobData

        # workflow jobが取得出来ない場合はエラー
        if len(self.workflowJobAry) <= 0:
            g.applogger.error("Not found to workflow jobs.")
            g.applogger.error(response_array)
            return False

        return True

    def checkWorkflowJobStatus(self, execution_no, wfJobId):

        workflowJobData = self.workflowJobAry[wfJobId]
        if "id" not in workflowJobData or "status" not in workflowJobData or "failed" not in workflowJobData:
            g.applogger.debug("Not expected data.")
            return AnscConst.EXCEPTION

        wfJobId = workflowJobData['id']
        wfJobStatus = workflowJobData['status']
        wfJobFailed = workflowJobData['failed']
        if wfJobStatus in ["new", "pending", "waiting", "running"]:
            status = AnscConst.PROCESSING

        elif wfJobStatus == "successful":
            status = self.checkAllJobsStatus(wfJobId)

        elif wfJobStatus in ["failed", "error"]:
            status = AnscConst.FAILURE

        elif wfJobStatus == "canceled":
            # 子Jobのステータスは感知しない（100%キャンセルはできない）
            status = AnscConst.SCRAM

        else:
            status = AnscConst.EXCEPTION

        return status

    def checkAllJobsStatus(self, wfJobId):

        for workflowJobNodeData in self.workflowJobNodeAry[wfJobId]:
            wfJobNodeId = workflowJobNodeData['id']
            for JobDetail in self.JobDetailAry[wfJobId][wfJobNodeId]:
                JobData = JobDetail['JobData']
                JobId = JobData['id']
                if "id" not in JobData or "status" not in JobData or "failed" not in JobData:
                    g.applogger.debug("Not expected data.")
                    return AnscConst.EXCEPTION

                if JobData['status'] != "successful":
                    return AnscConst.FAILURE

        # 全て成功
        return AnscConst.COMPLETE

    def createAnsibleLogs(self, execution_no, wfJobId):

        execlogFilename = "exec.log"
        joblistFilename = "joblist.txt"
        outDirectoryPath = '%s/out' % getAnsibleExecutDirPath(self.driver_id, execution_no)

        execlogFullPath = '%s/%s' % (outDirectoryPath, execlogFilename)
        joblistFullPath = '%s/%s' % (outDirectoryPath, joblistFilename)

        # ログファイル生成
        ret = self.CreateLogs(execution_no, wfJobId, joblistFullPath, outDirectoryPath, execlogFullPath)
        return ret

    def CreateLogs(self, execution_no, wfJobId, joblistFullPath, outDirectoryPath, execlogFullPath):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        # ワークフローの情報取得
        workflow_contentArray = {}
        workflowJobData = self.workflowJobAry[wfJobId]
        workflow_contentArray[wfJobId] = "  workflow_name: %s" % (workflowJobData['name'])
        if 'result_traceback' in workflowJobData and len(workflowJobData['result_traceback']) > 0:
            workflow_contentArray[wfJobId] = '%s\n    status: %s' % (workflow_contentArray[wfJobId], workflowJobData['status'])
            workflow_contentArray[wfJobId] = '%s\n    result_traceback: %s' % (workflow_contentArray[wfJobId], workflowJobData['result_traceback'])

        jobSummaryAry = {}
        for workflowJobNodeData in self.workflowJobNodeAry[wfJobId]:
            wfJobNodeId = workflowJobNodeData['id']
            for JobDetail in self.JobDetailAry[wfJobId][wfJobNodeId]:
                JobData = JobDetail['JobData']
                JobId = JobData['id']
                jobName = JobData['name']

                contentArray = []
                contentArray.append("------------------------------------------------------------------------------------------------------------------------")
                contentArray.append(workflow_contentArray[wfJobId])
                contentArray.append("  job_name: %s" % (jobName))
                if 'result_traceback' in JobData and JobData['result_traceback'] is not None and len(JobData['result_traceback']) > 0:
                    contentArray.append("    status: %s" % (JobData['status']))
                    contentArray.append("    result_traceback: %s" % (JobData['result_traceback']))

                response_array = AnsibleTowerRestApiProjects.get(self.restApiCaller, JobData['project'])
                if not response_array['success']:
                    g.applogger.error("Faild to get project. %s" % (response_array['responseContents']['errorMessage']))
                    return False

                projectData = response_array['responseContents']

                contentArray.append("  project_name: %s" % (projectData['name']))
                contentArray.append("  project_local_path: %s" % (projectData['local_path']))

                # ---- Ansible Tower Version Check
                if self.getTowerVersion() in [AnscConst.TOWER_VER35, str(AnscConst.TOWER_VER35)]:
                    response_array = AnsibleTowerRestApiCredentials.get(self.restApiCaller, JobData['credential'])
                    if not response_array['success']:
                        g.applogger.error("Faild to get credential. %s" % (response_array['responseContents']['errorMessage']))
                        return False

                    credentialData = response_array['responseContents']

                else:
                    for CredentialArray in JobData['summary_fields']['credentials']:
                        if CredentialArray['kind'] != 'vault':
                            response_array = AnsibleTowerRestApiCredentials.get(self.restApiCaller, CredentialArray['id'])
                            if not response_array['success']:
                                g.applogger.error("Faild to get credential. %s" % (response_array['responseContents']['errorMessage']))

                            credentialData = response_array['responseContents']

                    if credentialData is None:
                        g.applogger.error("non set to get credential. %s" % (response_array['responseContents']))
                        return False
                # ---- Ansible Tower Version Check

                contentArray.append("  credential_name: %s" % (credentialData['name']))
                contentArray.append("  credential_type: %s" % (credentialData['credential_type']))
                contentArray.append("  credential_inputs: %s" % (json.dumps(credentialData['inputs'])))
                contentArray.append("  virtualenv: %s" % (projectData['custom_virtualenv']))
                if self.workflowJobAry[wfJobId]['is_sliced_job'] is True:
                    contentArray.append("  job_slice_count: %s" % (JobData["job_slice_count"]))

                query = "%s/instance_groups/" % (JobData['inventory'])
                response_array = AnsibleTowerRestApiInventories.getAll(self.restApiCaller, query)
                if not response_array['success']:
                    g.applogger.error("Faild to get inventory. %s" % (response_array['responseContents']['errorMessage']))
                    return False

                instance_group = ""
                if  'responseContents' in response_array and len(response_array['responseContents']) > 0 \
                and 'name' in response_array['responseContents'][0] and response_array['responseContents'][0]['name'] is True:
                    instance_group = response_array['responseContents'][0]['name']

                contentArray.append("  instance_group: %s" % (instance_group))

                response_array = AnsibleTowerRestApiInventories.get(self.restApiCaller, JobData['inventory'])
                if not response_array['success']:
                    g.applogger.error("Faild to get inventory. %s" % (response_array['responseContents']['errorMessage']))
                    return False

                inventoryData = response_array['responseContents']

                response_array = AnsibleTowerRestApiInventoryHosts.getAllEachInventory(self.restApiCaller, JobData['inventory'])

                if not response_array['success']:
                    g.applogger.error("Faild to get hosts. %s" % (response_array['responseContents']['errorMessage']))
                    return False

                hostsData = response_array['responseContents']

                contentArray.append("  inventory_name: %s" % (inventoryData['name']))

                for hostData in hostsData:
                    contentArray.append("    host_name: %s" % (hostData['name']))
                    contentArray.append("    host_variables: %s" % (hostData['variables']))

                contentArray.append("------------------------------------------------------------------------------------------------------------------------")
                contentArray.append("")
                jobSummaryAry[JobId] = '\n'.join(contentArray)

            contentArray.append("")

        ################################################################
        # 各WorkflowJobNode分のstdoutをファイル化
        ################################################################
        for workflowJobNodeData in self.workflowJobNodeAry[wfJobId]:
            wfJobNodeId = workflowJobNodeData['id']
            for JobDetail in self.JobDetailAry[wfJobId][wfJobNodeId]:
                JobData = JobDetail['JobData']
                stdout = JobDetail['stdout']
                JobId = JobData['id']
                jobName = JobData['name']
                if self.workflowJobAry[wfJobId]['is_sliced_job'] is True:
                    # ジョブスライス数
                    job_slice_count = JobData['job_slice_count']
                    job_slice_number = JobData['job_slice_number']
                    job_slice_number_str = str(job_slice_number).zfill(10)
                    page = "\n(%s/%s)\n" % (JobData['job_slice_number'], JobData['job_slice_count'])

                else:
                    job_slice_number = 0
                    job_slice_number_str = str(job_slice_number).zfill(10)
                    page = ""

                # jobサマリ出力
                result_stdout = jobSummaryAry[JobId]

                # jobログ出力
                result_stdout += page
                result_stdout += stdout

                # オリジナルログファイル
                jobFileFullPath = "%s/%s_%s.txt.org" % (outDirectoryPath, JobData['name'], job_slice_number_str)
                try:
                    pathlib.Path(jobFileFullPath).write_text(result_stdout)

                except Exception as e:
                    g.applogger.error("Faild to write file. %s" % (jobFileFullPath))
                    return False

                if JobData['name'] not in self.jobOrgLogFileList:
                    self.jobOrgLogFileList[JobData['name']] = None

                if not isinstance(self.jobOrgLogFileList[JobData['name']], list):
                    self.jobOrgLogFileList[JobData['name']] = []

                self.jobOrgLogFileList[JobData['name']].append(jobFileFullPath)

                # jobログを加工
                result_stdout = self.LogReplacement(result_stdout)
                jobFileFullPath = '%s/%s_%s.txt' % (outDirectoryPath, JobData['name'], job_slice_number_str)
                try:
                    pathlib.Path(jobFileFullPath).write_text(result_stdout)

                except Exception as e:
                    g.applogger.error("Faild to write file. %s" % (jobFileFullPath))
                    return False

                # 加工ログファイル
                if JobData['name'] not in self.jobFileList:
                    self.jobFileList[JobData['name']] = None

                if not isinstance(self.jobFileList[JobData['name']], list):
                    self.jobFileList[JobData['name']] = []

                self.jobFileList[JobData['name']].append(jobFileFullPath)
                self.jobLogFileList.append(os.path.basename(jobFileFullPath))

        # ジョブスライなどでファイルが複数に分かれた場合にファイルのリスト
        if len(self.jobLogFileList) > 0:
            self.setMultipleLogFileJsonAry(execution_no, self.jobLogFileList)

        # ジョブスライなどでファイルが複数に分かれた場合のマーク
        if len(self.jobLogFileList) > 1:
            self.settMultipleLogMark(execution_no, outDirectoryPath)

        ################################################################
        # 結合 & exec.log差し替え
        ################################################################
        # ファイル入出力排他処理
        loop = asyncio.get_event_loop()
        ret = loop.run_until_complete(self.CreateLogsWithSemaphore(execlogFullPath))

        return ret

    async def CreateLogsWithSemaphore(self, execlogFullPath):

        tryCount = 0
        semaphore = asyncio.Semaphore(1)
        while True:
            if not semaphore.locked():
                break

            time.sleep(0.1)
            tryCount = tryCount + 1
            if tryCount > 50:
                g.applogger.error("Faild to lock file.")
                return False

        await semaphore.acquire()
        try:
            # 全ジョブのオリジナルログファイル
            execlogContent = ""
            for jobName, jobFileFullPathAry in self.jobOrgLogFileList.items():
                for jobFileFullPath in jobFileFullPathAry:
                    jobFileContent = pathlib.Path(jobFileFullPath).read_text()
                    if not jobFileContent:
                        g.applogger.error("Faild to read file. %s" % (jobFileFullPath))
                        return False

                    execlogContent = '%s%s\n' % (execlogContent, jobFileContent)

            execlogFullPath_org = '%s.org' % (execlogFullPath)
            try:
                pathlib.Path(execlogFullPath_org).write_text(execlogContent)

            except Exception as e:
                g.applogger.error("Faild to write file. %s" % (execlogFullPath))
                return False

            # 全ジョブの加工ログファイル
            execlogContent = ""
            for jobName, jobFileFullPathAry in self.jobFileList.items():
                for jobFileFullPath in jobFileFullPathAry:
                    jobFileContent = pathlib.Path(jobFileFullPath).read_text()
                    if not jobFileContent:
                        g.applogger.error("Faild to read file. %s" % (jobFileFullPath))
                        return False

                    execlogContent = '%s%s\n' % (execlogContent, jobFileContent)

            try:
                pathlib.Path(execlogFullPath).write_text(execlogContent)

            except Exception as e:
                g.applogger.error("Faild to write file. %s" % (execlogFullPath))
                return False

        finally:
            semaphore.release()

        return True

    def errorLogOut(self, message):

        if self.exec_out_dir and os.path.isdir(self.exec_out_dir):
            errorLogfile = '%s/error.log' % (self.exec_out_dir)
            if not message.endswith('\n'):
                message += '\n'

            try:
                with open(errorLogfile, 'a') as fp:
                    fp.write(message)

            except Exception as e:
                g.applogger.error("Error. Faild to write message. %s" % (message))

    def getMaterialsTransferDestinationPath(self, PathId, execution_no):

        return self.vg_TowerInstanceDirPath[PathId]

    def LogReplacement(self, log_data):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name

        if vg_tower_driver_name == "pioneer":
            # ログ(", ")  =>  (",\n")を改行する
            log_data = re.sub('", "', '",\n"', log_data)

            # 改行文字列\\r\\nを改行コードに置換える
            log_data = re.sub('\\\\\\\\r\\\\\\\\n', '\n', log_data)

            # 改行文字列\r\nを改行コードに置換える
            log_data = re.sub('\\\\r\\\\n', '\n', log_data)

            # python改行文字列\\nを改行コードに置換える
            log_data = re.sub('\\\\\\\\n', '\n', log_data)

            # python改行文字列\nを改行コードに置換える
            log_data = re.sub('\\\\n', '\n', log_data)

        else:
            # ログ(", ")  =>  (",\n")を改行する
            log_data = re.sub('", "', '",\n"', log_data)

            # ログ(=> {)  =>  (=> {\n)を改行する
            log_data = re.sub('=> {', '=> {\n', log_data)

            # ログ(, ")  =>  (,\n")を改行する
            log_data = re.sub(', "', ',\n"', log_data)

            # 改行文字列\\r\\nを改行コードに置換える
            log_data = re.sub('\\\\\\\\r\\\\\\\\n', '\n', log_data)

            # 改行文字列\r\nを改行コードに置換える
            log_data = re.sub('\\\\r\\\\n', '\n', log_data)

            # python改行文字列\\nを改行コードに置換える
            log_data = re.sub('\\\\\\\\n', '\n', log_data)

            # python改行文字列\nを改行コードに置換える
            log_data = re.sub('\\\\n', '\n', log_data)

        return log_data

    def getMultipleLogMark(self):

        return self.MultipleLogMark

    def settMultipleLogMark(self, execution_no, dataRelayStoragePath):

        self.MultipleLogMark = "1"

    def getMultipleLogFileJsonAry(self):

        return self.MultipleLogFileJsonAry

    def setMultipleLogFileJsonAry(self, execution_no, MultipleLogFileNameList):

        self.MultipleLogFileJsonAry = json.dumps(MultipleLogFileNameList)
        return True

    def createGitRepo(self, GitObj, SrcFilePath, execution_no):

        repositories_base_path = "%s/driver/ansible/git_repositories/" % (getDataRelayStorageDir())
        proj_name = os.path.basename(pathlib.Path(SrcFilePath).parent)
        repositories_path = "%s%s" % (repositories_base_path, proj_name)

        # git clone用のディレトクリ削除
        # repositories_path: /storage/org1/workspace-1/driver/ansible/git_repositories/legacy_role_作業番号
        ret, msg = self.GitRepoDirDelete(repositories_path)
        if ret is False:
            log = g.appmsg.get_api_message("MSG-10018", [msg])
            self.errorLogOut(log)
            g.applogger.error(log)

            return False

        # GitLab にプロジェクトを作成
        try:
            response = GitObj.create_project(proj_name)

            # gitlab プロジェクトID退避
            if 'id' in response:
                # 文字列に変換して保存
                project_id  = str(response['id'])
                self.saveGitProjectId(self.driver_id, execution_no, project_id)

        except Exception as e:
            log = g.appmsg.get_api_message("MSG-10018", [str(e)])
            self.errorLogOut(log)
            g.applogger.error(log)

            return False

        # git clone ～ git push
        http_repo_url = GitObj.get_http_repo_url(proj_name)
        commit_comment = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        cmd = ["git", "clone", http_repo_url]
        try:
            os.chdir(repositories_base_path)
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            cmd = "/bin/cp -rfp %s %s" % (SrcFilePath, repositories_path)
            subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            os.chdir(repositories_path)
            git_username = g.gitlab_connect_info.get('GITLAB_USER')
            cmd = ["git", "config", "--local", "user.name", git_username]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            git_email = '%s@example.com' % (git_username.lower())
            cmd = ["git", "config", "--local", "user.email", git_email]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            cmd = ["git", "add", "."]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            cmd = ["git", "commit", "-m", '"%s"' % (commit_comment)]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            cmd = ["git", "push", "origin", "main"]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            log = e.stdout.decode()
            log = '%s\n%s' % (log, g.appmsg.get_api_message("MSG-10018", [cmd]))
            self.errorLogOut(log)
            g.applogger.error(log)
            return False

        except Exception as e:
            log = str(e)
            log = '%s\n%s' % (log, g.appmsg.get_api_message("MSG-10018", [cmd]))
            self.errorLogOut(log)
            g.applogger.error(log)
            return False

        return True

    def saveGitProjectId(self, driver_id, execution_no, project_id):
        execute_path = getAnsibleExecutDirPath(driver_id, execution_no)
        filePath = "{}/tmp/GitlabProjectId.txt".format(execute_path)
        with open(filePath, 'w') as fd:
            fd.write(project_id)

    def getGitProjectId(self, driver_id, execution_no):
        execute_path = getAnsibleExecutDirPath(driver_id, execution_no)
        filePath = "{}/tmp/GitlabProjectId.txt".format(execute_path)
        with open(filePath) as fd:
            project_id = fd.read()
        return project_id
    
    def deleteMaterialsTransferTempDir(self, execution_no):

        vg_tower_driver_name = AnsrConst.vg_tower_driver_name
        tmp_path_ary = getInputDataTempDir(execution_no, vg_tower_driver_name)
        src_path = tmp_path_ary["DIR_NAME"]

        # Gitリポジトリ用の一時ディレクトリを削除
        if os.path.exists(src_path):
            cmd = ["/bin/rm", "-rf", src_path]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            except Exception as e:
                log = str(e)
                log = '%s\n%s' % (log, g.appmsg.get_api_message("MSG-10017", [cmd]))
                self.errorLogOut(log)
                g.applogger.error(log)
                return False

        return True

    def createProjectStatusCheck(self, response_array):

        projectId = response_array['responseContents']['id']
        # Git連携の状態を確認する
        while True:
            if response_array['responseContents']['status'] in ["new", "pending", "waiting", "running"]:
                time.sleep(5)
                response_array = AnsibleTowerRestApiProjects.get(self.restApiCaller, projectId)
                if not response_array['success']:
                    errorMessage = g.appmsg.get_api_message("MSG-10021")
                    self.errorLogOut(errorMessage)
                    g.applogger.error(response_array)
                    return -1

            elif response_array['responseContents']['status'] == "successful":
                return True

            elif response_array['responseContents']['status'] in ["failed", "error"]:
                # プロジェクト更新用のURL退避
                updateUurl = response_array['responseContents']['related']['update']

                # Git連携に失敗した場合、エラー情報を取得する
                url = response_array['responseContents']['related']['project_updates']
                response_array = AnsibleTowerRestApirPassThrough.get(self.restApiCaller, url)
                if not response_array['success']:
                    errorMessage = g.appmsg.get_api_message("MSG-10021")
                    self.errorLogOut(errorMessage)
                    g.applogger.error(response_array)
                    return -1

                url = "%s?format=txt" % (response_array['responseContents']['results'][0]['related']['stdout'])
                response_array = AnsibleTowerRestApirPassThrough.get(self.restApiCaller, url, True)
                if not response_array['success']:
                    errorMessage = g.appmsg.get_api_message("MSG-10021")
                    self.errorLogOut(errorMessage)
                    g.applogger.error(response_array)
                    return -1

                # 制御ノードにコンテナイメージがロードされていないと、プロジェクト作成でGit連携が失敗する
                # プロジェクトの更新だとコンテナイメージがロードていなくても問題ないので、プロジェクトを更新する
                response_array = AnsibleTowerRestApirPassThrough.post(self.restApiCaller, updateUurl)
                if not response_array['success']:
                    errorMessage = g.appmsg.get_api_message("MSG-10021")
                    self.errorLogOut(errorMessage)
                    g.applogger.error(response_array)
                    return -1

                ret = self.projectUpdate(response_array)
                if ret is True:
                    return True

                return -1

            else:
                errorMessage = g.appmsg.get_api_message("MSG-10021")
                self.errorLogOut(errorMessage)
                g.applogger.error(response_array)
                return -1

    def projectUpdate(self, response_array):

        url = response_array['responseContents']['url']

        # プロジェクト更新の結果判定
        while True:
            response_array = AnsibleTowerRestApirPassThrough.get(self.restApiCaller, url)
            if not response_array['success']:
                errorMessage = g.appmsg.get_api_message("MSG-10021")
                self.errorLogOut(errorMessage)
                g.applogger.error(response_array)
                return response_array

            if response_array['responseContents']['status'] in ["new", "pending", "waiting", "running"]:
                time.sleep(5)

            elif response_array['responseContents']['status'] == "successful":
                return True

            elif response_array['responseContents']['status'] in ["failed", "error"]:
                url = "%s?format=txt" % (response_array['responseContents']['related']['stdout'])
                response_array = AnsibleTowerRestApirPassThrough.get(self.restApiCaller, url, True)
                ProjectUpdateStdout = response_array['responseContents']
                if not response_array['success']:
                    errorMessage = g.appmsg.get_api_message("MSG-10021")
                    self.errorLogOut(errorMessage)
                    g.applogger.error(response_array)
                    return -1

                errorMessage = g.appmsg.get_api_message("MSG-10020", [ProjectUpdateStdout])
                self.errorLogOut(errorMessage)
                return -1

            else:
                errorMessage = g.appmsg.get_api_message("MSG-10021")
                self.errorLogOut(errorMessage)
                g.applogger.error(response_array)
                return -1

    def GitRepoDirDelete(self, SrcFilePath):

        if os.path.exists(SrcFilePath):
            cmd = ["/bin/rm", "-rf", SrcFilePath]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            except Exception as e:
                log = str(e)
                log = '%s\nFailed to delete Git repository.(%s)' % (log, str(cmd))
                return False, log

        return True, ''

    @staticmethod
    def getGitSshKeyFileContent(systemId, sshKeyFileName):

        ssh_key_file_dir = getFileupLoadColumnPath('2100040702', 'ANS_GIT_SSH_KEY_FILE')

        filePath = '%s/%s/%s' % (ssh_key_file_dir, FuncCommonLib.addPadding(systemId), sshKeyFileName)
        content = pathlib.Path(filePath).read_text()
        content = ky_decrypt(content)

        return content

    @staticmethod
    def getDeviceListSshKeyFileContent(systemId, sshKeyFileName):
        filePath = '%s/%s/%s' % (getDeviceListSSHPrivateKeyUploadDirPath(), systemId, sshKeyFileName)
        content = pathlib.Path(filePath).read_text()

        return content

    @staticmethod
    def getAnsibleTowerSshKeyFileContent(TowerHostID, sshKeyFileName):
        filePath = '%s/%s/%s' % ( getAACListSSHPrivateKeyUploadDirPath(), TowerHostID, sshKeyFileName)

        return filePath


