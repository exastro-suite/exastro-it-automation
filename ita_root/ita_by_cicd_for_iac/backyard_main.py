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


import os
import inspect
import time
import datetime
import configparser
import subprocess
import json
import re
import base64
import shutil

from flask import g

from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs
from common_libs.common.encrypt import decrypt_str
from common_libs.loadtable import *
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.terraform_driver.common.Const import Const as TFCommonConst
from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
from common_libs.terraform_driver.cli.Const import Const as TFCLIConst
from common_libs.ansible_driver.functions.util import getDataRelayStorageDir, getLegacyPlaybookUploadDirPath, getPioneerDialogUploadDirPath, getRolePackageContentUploadDirPath, getFileContentUploadDirPath, getTemplateContentUploadDirPath
from common_libs.ansible_driver.functions.rest_libs import insert_execution_list as a_insert_execution_list
from common_libs.terraform_driver.common.Execute import insert_execution_list as t_insert_execution_list
from common_libs.cicd.classes.cicd_definition import TD_SYNC_STATUS_NAME_DEFINE, TD_B_CICD_MATERIAL_FILE_TYPE_NAME, TD_B_CICD_MATERIAL_TYPE_NAME, TD_C_PATTERN_PER_ORCH, TD_B_CICD_GIT_PROTOCOL_TYPE_NAME, TD_B_CICD_GIT_REPOSITORY_TYPE_NAME, TD_B_CICD_MATERIAL_LINK_LIST
from common_libs.cicd.functions.local_functions import MatlLinkColumnValidator2, MatlLinkColumnValidator3, MatlLinkColumnValidator5
from common_libs.common import storage_access
import traceback
from common_libs.common.util import get_iso_datetime, arrange_stacktrace_format


################################################################
# 共通処理
################################################################
def makeLogiFileOutputString(file, line, logstr1, logstr2=''):

    msg = '[FILE]:%s [LINE]:%s %s' % (file, line, logstr1)
    if logstr2:
        msg = '%s\n%s' % (msg, logstr2)

    return msg


################################################################
# CICD例外クラス
################################################################
class CICDException(Exception):

    def __init__(self, RetCode, LogStr, UIMsg):

        self.ary = {}
        self.ary['RetCode'] = RetCode
        self.ary['log'] = LogStr
        self.ary['UImsg'] = UIMsg

    def __str__(self):

        return json.dumps(self.ary)


################################################################
# CICD資材配置パラメーター作成クラス
################################################################
class CICDMakeParamBase():

    def __init__(self, table_name, pkey, fcol_name, menu_name):

        self.table_name = table_name
        self.primary_key = pkey
        self.file_col_name = fcol_name
        self.menu_name = menu_name

    def make_param(self, *args, **kwargs):

        return {}

    def make_rest_param(self, data, *args, **kwargs):

        data['remarks'] = kwargs['note'] if 'note' in kwargs else ''
        data['discard'] = '0'
        data['last_update_date_time'] = kwargs['last_update_date_time'] if 'last_update_date_time' in kwargs else ''
        data['last_updated_user'] = g.USER_ID

    def diff_file(self, tgt_data, cur_filedata, *args, **kwargs):
        # /storage配下のファイルアクセスを/tmp経由で行うモジュール
        file_read1 = storage_access.storage_read()
        file_read2 = storage_access.storage_read()

        file_read_bytes1 = storage_access.storage_read_bytes()
        file_read_bytes2 = storage_access.storage_read_bytes()

        if cur_filedata is None:
            func = None
            if 'func' in kwargs:
                func = kwargs['func']

            subpath = []
            if 'path' in kwargs:
                subpath = kwargs['path']

            if not func and not subpath:
                return True

            cur_filepath = (func() if func else '') + subpath
            if os.path.exists(cur_filepath) is False:
                return True

            tgt_filepath = tgt_data["path"]
            o_mode = "r"
            if 'o_mode' in kwargs:
                o_mode = kwargs['o_mode']

            cur_filedata = ""
            file_read1.open(tgt_filepath)
            file_read2.open(cur_filepath)
            if o_mode == "r":
                chunk_size = 10000
                while True:
                    tgt_chunk = file_read1.chunk_read(chunk_size)
                    cur_chunk = file_read2.chunk_read(chunk_size)
                    if tgt_chunk != cur_chunk:
                        return True
                    if not tgt_chunk:
                        return False
            else:
                tgt_filedata = file_read_bytes1.read_bytes(tgt_filepath)
                cur_filedata = file_read_bytes2.read_bytes(cur_filepath)
                if tgt_filedata == cur_filedata:
                    return False

            file_read1.close()
            file_read2.close()
        return True

    def get_record(self, DBobj, **kwargs):

        sql = ""
        sql_where = ""
        where_list = []

        sql = "SELECT * FROM %s " % (self.table_name)
        for k, v in kwargs.items():
            if sql_where:
                sql_where += "AND "

            if v is None:
                sql_where += "%s IS NULL " % (k)

            else:
                sql_where += "%s=%%s " % (k)
                where_list.append(v)

        if sql_where:
            sql_where = "WHERE %s" % (sql_where)

        sql = "%s %s ORDER BY LAST_UPDATE_TIMESTAMP;" % (sql, sql_where)

        rset = DBobj.sql_execute(sql, where_list)

        return rset


class CICDMakeParamLegacy(CICDMakeParamBase):

    def __init__(self, table_name, pkey, fcol_name, menu_name):

        super(CICDMakeParamLegacy, self).__init__(table_name, pkey, fcol_name, menu_name)

    def make_param(self, row, tgtFileName):

        param = {}
        param['PLAYBOOK_MATTER_NAME'] = row['MATL_LINK_NAME']
        param['PLAYBOOK_MATTER_FILE'] = tgtFileName

        return param

    def make_rest_param(self, editType, linkname, filename, **kwargs):

        data = {}
        data['item_no'] = kwargs['PLAYBOOK_MATTER_ID'] if editType != load_table.CMD_REGISTER else ''
        data['playbook_name'] = linkname
        data['playbook_file'] = filename

        note = kwargs['NOTE'] if 'NOTE' in kwargs else ''
        last_update_date_time = str(kwargs['LAST_UPDATE_TIMESTAMP']) if 'LAST_UPDATE_TIMESTAMP' in kwargs else ''
        super(CICDMakeParamLegacy, self).make_rest_param(data, note=note, last_update_date_time=last_update_date_time)

        param = {}
        param['type'] = editType
        param['parameter'] = data

        return param

    def diff_file(self, mid, name, filedata):

        ret = super(CICDMakeParamLegacy, self).diff_file(
            filedata,
            None,
            func=getLegacyPlaybookUploadDirPath, path=("/%s/%s" % (mid, name))
        )

        return ret


class CICDMakeParamPioneer(CICDMakeParamBase):

    def __init__(self, table_name, pkey, fcol_name, menu_name):

        super(CICDMakeParamPioneer, self).__init__(table_name, pkey, fcol_name, menu_name)

    def make_param(self, row, tgtFileName):

        param = {}
        param['DIALOG_TYPE_ID'] = row['M_DIALOG_TYPE_ID']
        param['OS_TYPE_ID'] = row['M_OS_TYPE_ID']
        param['DIALOG_MATTER_FILE'] = tgtFileName

        return param

    def make_rest_param(self, editType, linkname, filename, **kwargs):

        data = {}
        data['item_no'] = kwargs['DIALOG_MATTER_ID'] if editType != load_table.CMD_REGISTER else ''
        data['dialog_type'] = linkname['DIALOG_TYPE_ID']
        data['os_type'] = linkname['OS_TYPE_ID']
        data['dialog_file'] = filename

        note = kwargs['NOTE'] if 'NOTE' in kwargs else ''
        last_update_date_time = str(kwargs['LAST_UPDATE_TIMESTAMP']) if 'LAST_UPDATE_TIMESTAMP' in kwargs else ''
        super(CICDMakeParamPioneer, self).make_rest_param(data, note=note, last_update_date_time=last_update_date_time)

        param = {}
        param['type'] = editType
        param['parameter'] = data

        return param

    def diff_file(self, mid, name, filedata):

        ret = super(CICDMakeParamPioneer, self).diff_file(
            filedata,
            None,
            func=getPioneerDialogUploadDirPath, path=("/%s/%s" % (mid, name))
        )

        return ret


class CICDMakeParamRole(CICDMakeParamBase):

    def __init__(self, table_name, pkey, fcol_name, menu_name):

        super(CICDMakeParamRole, self).__init__(table_name, pkey, fcol_name, menu_name)

    def make_param(self, row, tgtFileName):

        param = {}
        param['ROLE_PACKAGE_NAME'] = row['MATL_LINK_NAME']
        param['ROLE_PACKAGE_FILE'] = tgtFileName

        return param

    def make_rest_param(self, editType, linkname, filename, **kwargs):

        data = {}
        data['item_no'] = kwargs['ROLE_PACKAGE_ID'] if editType != load_table.CMD_REGISTER else ''
        data['role_package_name'] = linkname
        data['zip_format_role_package_file'] = filename
        data['variable_definition_analysis_result'] = ''

        note = kwargs['NOTE'] if 'NOTE' in kwargs else ''
        last_update_date_time = str(kwargs['LAST_UPDATE_TIMESTAMP']) if 'LAST_UPDATE_TIMESTAMP' in kwargs else ''
        super(CICDMakeParamRole, self).make_rest_param(data, note=note, last_update_date_time=last_update_date_time)

        param = {}
        param['type'] = editType
        param['parameter'] = data

        return param

    def diff_file(self, mid, name, filedata):

        ret = super(CICDMakeParamRole, self).diff_file(
            filedata,
            None,
            func=getRolePackageContentUploadDirPath, path=("/%s/%s" % (mid, name)), o_mode="rb"
        )

        return ret


class CICDMakeParamContent(CICDMakeParamBase):

    def __init__(self, table_name, pkey, fcol_name, menu_name):

        super(CICDMakeParamContent, self).__init__(table_name, pkey, fcol_name, menu_name)

    def make_param(self, row, tgtFileName):

        param = {}
        param['CONTENTS_FILE_VARS_NAME'] = row['MATL_LINK_NAME']
        param['CONTENTS_FILE'] = tgtFileName

        return param

    def make_rest_param(self, editType, linkname, filename, **kwargs):

        data = {}
        data['file_id'] = kwargs['CONTENTS_FILE_ID'] if editType != load_table.CMD_REGISTER else ''
        data['file_embedded_variable_name'] = linkname
        data['files'] = filename

        note = kwargs['NOTE'] if 'NOTE' in kwargs else ''
        last_update_date_time = str(kwargs['LAST_UPDATE_TIMESTAMP']) if 'LAST_UPDATE_TIMESTAMP' in kwargs else ''
        super(CICDMakeParamContent, self).make_rest_param(data, note=note, last_update_date_time=last_update_date_time)

        param = {}
        param['type'] = editType
        param['parameter'] = data

        return param

    def diff_file(self, mid, name, filedata):

        ret = super(CICDMakeParamContent, self).diff_file(
            filedata,
            None,
            func=getFileContentUploadDirPath, path=("/%s/%s" % (mid, name))
        )

        return ret


class CICDMakeParamTemplate(CICDMakeParamBase):

    def __init__(self, table_name, pkey, fcol_name, menu_name):

        self.__vars_list = ""
        super(CICDMakeParamTemplate, self).__init__(table_name, pkey, fcol_name, menu_name)

    def make_param(self, row, tgtFileName):

        param = {}
        param['ANS_TEMPLATE_VARS_NAME'] = row['MATL_LINK_NAME']
        param['ANS_TEMPLATE_FILE'] = tgtFileName
        param['VARS_LIST'] = row['TEMPLATE_FILE_VARS_LIST']
        self.__vars_list = row['TEMPLATE_FILE_VARS_LIST']

        return param

    def make_rest_param(self, editType, linkname, filename, **kwargs):

        data = {}
        data['template_id'] = kwargs['ANS_TEMPLATE_ID'] if editType != load_table.CMD_REGISTER else ''
        data['template_embedded_variable_name'] = linkname
        data['template_files'] = filename
        data['variable_definition'] = self.__vars_list

        note = kwargs['NOTE'] if 'NOTE' in kwargs else ''
        last_update_date_time = str(kwargs['LAST_UPDATE_TIMESTAMP']) if 'LAST_UPDATE_TIMESTAMP' in kwargs else ''
        super(CICDMakeParamTemplate, self).make_rest_param(data, note=note, last_update_date_time=last_update_date_time)

        param = {}
        param['type'] = editType
        param['parameter'] = data

        return param

    def diff_file(self, mid, name, filedata):

        ret = super(CICDMakeParamTemplate, self).diff_file(
            filedata,
            None,
            func=getTemplateContentUploadDirPath, path=("/%s/%s" % (mid, name))
        )

        return ret


class CICDMakeParamModule(CICDMakeParamBase):

    def __init__(self, table_name, pkey, fcol_name, menu_name):

        super(CICDMakeParamModule, self).__init__(table_name, pkey, fcol_name, menu_name)

    def make_param(self, row, tgtFileName):

        param = {}
        param['MODULE_MATTER_NAME'] = row['MATL_LINK_NAME']
        param['MODULE_MATTER_FILE'] = tgtFileName

        return param

    def make_rest_param(self, editType, linkname, filename, **kwargs):

        data = {}
        data['item_no'] = kwargs['MODULE_MATTER_ID'] if editType != load_table.CMD_REGISTER else ''
        data['module_file_name'] = linkname
        data['module_file'] = filename

        note = kwargs['NOTE'] if 'NOTE' in kwargs else ''
        last_update_date_time = str(kwargs['LAST_UPDATE_TIMESTAMP']) if 'LAST_UPDATE_TIMESTAMP' in kwargs else ''
        super(CICDMakeParamModule, self).make_rest_param(data, note=note, last_update_date_time=last_update_date_time)

        param = {}
        param['type'] = editType
        param['parameter'] = data

        return param

    def diff_file(self, mid, name, filedata):

        filepath = "%s%s/%s/%s" % (getDataRelayStorageDir(), TFCloudEPConst.DIR_MODULE, mid, name)
        ret = super(CICDMakeParamModule, self).diff_file(filedata, None, path=filepath)
        return ret


class CICDMakeParamPolicy(CICDMakeParamBase):

    def __init__(self, table_name, pkey, fcol_name, menu_name):

        super(CICDMakeParamPolicy, self).__init__(table_name, pkey, fcol_name, menu_name)

    def make_param(self, row, tgtFileName):

        param = {}
        param['POLICY_NAME'] = row['MATL_LINK_NAME']
        param['POLICY_MATTER_FILE'] = tgtFileName

        return param

    def make_rest_param(self, editType, linkname, filename, **kwargs):

        data = {}
        data['item_no'] = kwargs['POLICY_ID'] if editType != load_table.CMD_REGISTER else ''
        data['policy_name'] = linkname
        data['policy_file'] = filename

        note = kwargs['NOTE'] if 'NOTE' in kwargs else ''
        last_update_date_time = str(kwargs['LAST_UPDATE_TIMESTAMP']) if 'LAST_UPDATE_TIMESTAMP' in kwargs else ''
        super(CICDMakeParamPolicy, self).make_rest_param(data, note=note, last_update_date_time=last_update_date_time)

        param = {}
        param['type'] = editType
        param['parameter'] = data

        return param

    def diff_file(self, mid, name, filedata):

        filepath = "%s%s/%s/%s" % (getDataRelayStorageDir(), TFCloudEPConst.DIR_POLICY, mid, name)
        ret = super(CICDMakeParamPolicy, self).diff_file(filedata, None, path=filepath)
        return ret


class CICDMakeParamModuleCLI(CICDMakeParamBase):

    def __init__(self, table_name, pkey, fcol_name, menu_name):

        super(CICDMakeParamModuleCLI, self).__init__(table_name, pkey, fcol_name, menu_name)

    def make_param(self, row, tgtFileName):

        param = {}
        param['MODULE_MATTER_NAME'] = row['MATL_LINK_NAME']
        param['MODULE_MATTER_FILE'] = tgtFileName

        return param

    def make_rest_param(self, editType, linkname, filename, **kwargs):

        data = {}
        data['item_no'] = kwargs['MODULE_MATTER_ID'] if editType != load_table.CMD_REGISTER else ''
        data['module_file_name'] = linkname
        data['module_file'] = filename

        note = kwargs['NOTE'] if 'NOTE' in kwargs else ''
        last_update_date_time = str(kwargs['LAST_UPDATE_TIMESTAMP']) if 'LAST_UPDATE_TIMESTAMP' in kwargs else ''
        super(CICDMakeParamModuleCLI, self).make_rest_param(data, note=note, last_update_date_time=last_update_date_time)

        param = {}
        param['type'] = editType
        param['parameter'] = data

        return param

    def diff_file(self, mid, name, filedata):

        filepath = "%s%s/%s/%s" % (getDataRelayStorageDir(), TFCLIConst.DIR_MODULE, mid, name)
        ret = super(CICDMakeParamModuleCLI, self).diff_file(filedata, None, path=filepath)
        return ret


################################################################
# Gitクラス
################################################################
class ControlGit():

    def __init__(self, RepoId, RepoInfo, cloneRepoDir, libPath, GitCmdRsltParsAry):

        self.RepoId = RepoId
        self.remortRepoUrl = RepoInfo['REMORT_REPO_URL']
        self.cloneRepoDir = cloneRepoDir
        self.user = RepoInfo['GIT_USER'] if 'GIT_USER' in RepoInfo and RepoInfo['GIT_USER'] else "__undefine_user__"
        self.password = decrypt_str(RepoInfo['GIT_PASSWORD']) if 'GIT_PASSWORD' in RepoInfo and RepoInfo['GIT_PASSWORD'] else "__undefine_password__"
        self.gitOption = "--git-dir %s/.git --work-tree=%s" % (cloneRepoDir, cloneRepoDir)
        self.tmpDir = ""
        ClonecloneDir = '%s/clonecloneRepo/' % (os.path.dirname(cloneRepoDir))
        self.gitOption2 = "--git-dir %s/.git --work-tree=%s" % (ClonecloneDir, ClonecloneDir)
        self.libPath = libPath
        self.ClearGitCommandLastErrorMsg()
        self.ClearLastErrorMsg()
        self.branch = RepoInfo['BRANCH_NAME'] if 'BRANCH_NAME' in RepoInfo and RepoInfo['BRANCH_NAME'] else "__undefine_branch__"
        self.retryCount = self.dict_to_int(RepoInfo, 'RETRAY_COUNT', 3) + 1
        self.retryWaitTime = self.dict_to_int(RepoInfo, 'RETRAY_INTERVAL', 1000) / 1000
        ProxyAddress = RepoInfo['PROXY_ADDRESS'] if 'PROXY_ADDRESS' in RepoInfo else None
        ProxyPort = RepoInfo['PROXY_PORT'] if 'PROXY_PORT' in RepoInfo else None
        self.ProxyURL = '%s:%s' % (ProxyAddress, ProxyPort) if ProxyAddress and ProxyPort else "__undefine__"
        self.GitCmdRsltParsAry = GitCmdRsltParsAry
        self.sshPassword = decrypt_str(RepoInfo['SSH_PASSWORD']) if 'SSH_PASSWORD' in RepoInfo and RepoInfo['SSH_PASSWORD'] else "__undefine_sshPassword__"
        self.sshPassphrase = decrypt_str(RepoInfo['SSH_PASSPHRASE']) if 'SSH_PASSPHRASE' in RepoInfo and RepoInfo['SSH_PASSPHRASE'] else "__undefine_sshPassphrase__"
        self.sshExtraArgs = RepoInfo['SSH_EXTRA_ARGS'] if 'SSH_EXTRA_ARGS' in RepoInfo and RepoInfo['SSH_EXTRA_ARGS'] else ""
        self.sshExtraArgsStr = ""

    def dict_to_int(self, d, k, default_val):

        try:
            return int(d[k])
        except Exception as e:
            # 未設定の場合に初期値を設定しているので例外メッセージを出力する必要なし
            return default_val

    def SetGitCommandLastErrorMsg(self, errorDetail):

        self.GitCommandLastErrorMsg = errorDetail

    def GetGitCommandLastErrorMsg(self):

        return self.GitCommandLastErrorMsg

    def ClearGitCommandLastErrorMsg(self):

        self.GitCommandLastErrorMsg = ""

    def SetLastErrorMsg(self, errorDetail):

        self.LastErrorMsg = errorDetail

    def GetLastErrorMsg(self):

        return self.LastErrorMsg

    def ClearLastErrorMsg(self):

        self.LastErrorMsg = ""

    def LocalCloneDirCheck(self):

        return os.path.exists(self.cloneRepoDir)

    def setSshExtraArgs(self):

        self.sshExtraArgsStr = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no %s" % (self.sshExtraArgs)

        try:
            reg_flg = False
            cmd = ["git", "config", "--global", "-l"]
            os.chdir("/exastro")

            if os.path.exists("/home/app_user/.gitconfig"):
                return_var = subprocess.run(cmd, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if return_var.returncode == 0:
                    if "core.sshcommand" in return_var.stdout:
                        reg_flg = True

                else:
                    logstr = g.appmsg.get_api_message("MSG-90091", [cmd,])
                    logaddstr = '%s\n%s\nexit code:(%s)' % (' '.join(cmd), return_var.stdout, return_var.returncode)
                    FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
                    self.SetGitCommandLastErrorMsg('%s\n%s' % (logstr, logaddstr))
                    self.SetLastErrorMsg(FREE_LOG)
                    return False

            """
            if reg_flg is False:
                cmd = "git config --global core.sshCommand 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'"
                return_var = subprocess.run(cmd, encoding='utf-8', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if return_var.returncode != 0:
                    logstr = g.appmsg.get_api_message("MSG-90091", [cmd,])
                    logaddstr = '%s\n%s\nexit code:(%s)' % (' '.join(cmd), return_var.stdout, return_var.returncode)
                    FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
                    self.SetGitCommandLastErrorMsg('%s\n%s' % (logstr, logaddstr))
                    self.SetLastErrorMsg(FREE_LOG)
                    return False
            """

        except Exception as e:
            logstr = g.appmsg.get_api_message("MSG-90091", [cmd,])
            logaddstr = '%s\n%s' % (' '.join(cmd), str(e.stdout))
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg('%s\n%s' % (logstr, logaddstr))
            self.SetLastErrorMsg(FREE_LOG)
            return False

        return True

    def GitRemoteChk(self):

        cmd_ok = False
        return_var = None
        cmd = "git %s remote -v" % (self.gitOption)

        # Git コマンドが失敗した場合、指定時間Waitし指定回数リトライする
        for idx in range(self.retryCount):
            return_var = subprocess.run(cmd, text=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if return_var.returncode == 0:
                break

            logaddstr = "%s\nexit code:(%s)\nError retry with git command" % (return_var.stdout, return_var.returncode)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)
            g.applogger.info(FREE_LOG)

            if self.retryCount - 1 > idx:
                time.sleep(self.retryWaitTime)

        if return_var and return_var.returncode == 0:
            stdout = (return_var.stdout.split('\n'))[0]
            ret = re.match(r'origin[\s]*', stdout)
            if ret:
                url = self.remortRepoUrl
                url = re.escape(url)
                ret = re.match("origin[\s]*%s" % (url), stdout)
                if ret:
                    cmd_ok = True

        else:
            logstr = g.appmsg.get_api_message("MSG-90085")
            logaddstr = "%s\nexit code:(%s)" % (return_var.stdout if return_var else '', return_var.returncode if return_var else '')
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg(return_var.stdout if return_var else '')
            self.SetLastErrorMsg(FREE_LOG)
            return -1

        if cmd_ok is False:
            logstr = g.appmsg.get_api_message("MSG-90084", [self.remortRepoUrl,])
            logaddstr = "%s\nexit code:(%s)" % (return_var.stdout if return_var else '', return_var.returncode if return_var else '')
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg(return_var.stdout if return_var else '')
            self.SetLastErrorMsg(FREE_LOG)
            return False

        return True

    def GitBranchChk(self, Authtype):

        # デフォルトブランチ確認
        return_var = None
        DefaultBranch = ""
        if self.branch == "__undefine_branch__":
            cmd1 = [
                "sh",
                "%s/ky_GitCommand.sh" % (self.libPath),
                self.ProxyURL, Authtype, self.cloneRepoDir,
                "remote show origin",
                self.user, self.password, self.sshPassword, self.sshPassphrase,
                self.sshExtraArgsStr
            ]

            # Git コマンドが失敗した場合、指定時間Waitし指定回数リトライする
            for idx in range(self.retryCount):
                return_var = subprocess.run(cmd1, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if return_var.returncode == 0:
                    break

                logaddstr = "%s\nexit code:(%s)\nError retry with git command" % (return_var.stdout, return_var.returncode)
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)
                g.applogger.info(FREE_LOG)

                if self.retryCount - 1 > idx:
                    time.sleep(self.retryWaitTime)

            if return_var is None or return_var.returncode != 0:
                # Git remote show origin commandに失敗しました
                logstr = g.appmsg.get_api_message("MSG-90086")
                logaddstr = "%s\nexit code:(%s)" % (return_var.stdout if return_var else '', return_var.returncode if return_var else '')
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
                self.SetGitCommandLastErrorMsg(return_var.stdout if return_var else '')
                self.SetLastErrorMsg(FREE_LOG)
                return -1

            else:
                output1 = return_var.stdout.split('\n')
                for op in output1:
                    # HEAD branch: xxx の確認
                    ret = re.match('[\s]+HEAD[\s]branch', op)
                    if ret:
                        ret = re.match('[\s]+HEAD[\s]branch:[\s]+', op)
                        if ret:
                            DefaultBranch = re.split('[\s]+HEAD[\s]branch:[\s]+', op)[1]
                            break

                        else:
                            ret = re.match('[\s]+HEAD[\s]branch[\s]\(remote HEAD is ambiguous, may be one of the following\):', op)
                            if ret:
                                return True

                            else:
                                logstr = g.appmsg.get_api_message("MSG-90086")
                                logaddstr = g.appmsg.get_api_message("MSG-90089")
                                logaddstr = '%s\n%s\nexit code:(%s)' % (logaddstr, op, return_var.returncode)
                                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
                                self.SetGitCommandLastErrorMsg(logaddstr)
                                self.SetLastErrorMsg(FREE_LOG)
                                return -1

        # カレントブランチ確認
        return_var = None
        CurrentBranch = ""
        cmd2 = []
        cmd2.append("git")
        cmd2.extend(self.gitOption.split(' '))
        cmd2.append("branch")

        # Git コマンドが失敗した場合、指定時間Waitし指定回数リトライする
        for idx in range(self.retryCount):
            return_var = subprocess.run(cmd2, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if return_var.returncode == 0:
                break

            logaddstr = "%s\nexit code:(%s)\nError retry with git command" % (return_var.stdout, return_var.returncode)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)
            g.applogger.info(FREE_LOG)

            if self.retryCount - 1 > idx:
                time.sleep(self.retryWaitTime)

        if return_var is None or return_var.returncode != 0:
            # Git remote show origin commandに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90086")
            logaddstr = "%s\nexit code:(%s)" % (return_var.stdout if return_var else '', return_var.returncode if return_var else '')
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg(return_var.stdout if return_var else '')
            self.SetLastErrorMsg(FREE_LOG)
            return -1

        else:
            # 空リポジトリ対応 空リポジトリの場合はremote show originの結果が(unknown)になるので(unknown)設定
            if len(return_var.stdout) <= 0:
                CurrentBranch = "(unknown)"

            else:
                CurrentBranch = return_var.stdout.split('\n')[0][2:]

        if self.branch == "__undefine_branch__":
            if DefaultBranch == "":
                return True

            if DefaultBranch != CurrentBranch:
                return False

        else:
            if self.branch != CurrentBranch:
                return False

        return True

    def LocalCloneDirClean(self):

        return_var = None
        if os.path.exists(self.cloneRepoDir):
            cmd = ["/bin/rm", "-rf", self.cloneRepoDir]
            return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if return_var.returncode != 0:
                logstr = "Failed to delete clone directory.(%s)\n" % (self.cloneRepoDir)
                logaddstr = return_var.stdout
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
                self.SetLastErrorMsg(FREE_LOG)
                self.SetGitCommandLastErrorMsg("%s\n%s" % (logstr, logaddstr))
                return False

        cmd = ["/bin/mkdir", "-m", "0777", self.cloneRepoDir]
        return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if return_var.returncode != 0:
            logstr = "Failed to create clone directory.(%s)\n" % (self.cloneRepoDir)
            logaddstr = return_var.stdout
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetLastErrorMsg(FREE_LOG)
            self.SetGitCommandLastErrorMsg("%s\n%s" % (logstr, logaddstr))
            return False

        return True

    def GitClone(self, Authtype):

        return_var = None
        return_code = 0
        comd_ok = False
        output = ""

        # Git Cloneコマンドが失敗した場合、指定時間Waitし指定回数リトライする
        for idx in range(self.retryCount):
            cmd = [
                "sh",
                "%s/ky_GitClone.sh" % (self.libPath),
                self.ProxyURL,
                Authtype,
                self.remortRepoUrl, self.cloneRepoDir, self.branch,
                self.user, self.password, self.sshPassword, self.sshPassphrase,
                self.sshExtraArgsStr
            ]

            self.ClearGitCommandLastErrorMsg()
            os.chdir(self.cloneRepoDir)
            return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if return_var.returncode == 0:
                comd_ok = True
                break

            else:
                output = return_var.stdout
                return_code = return_var.returncode
                logaddstr = "%s\nexit code:(%s)\nError retry with git command" % (output, return_code)
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)
                g.applogger.info(FREE_LOG)

                # リトライ中のログは表示しない
                if self.retryCount - 1 > idx:
                    time.sleep(self.retryWaitTime)

        if comd_ok is False:
            # clone失敗時はローカルディレクトリを削除
            cmd = ["/bin/rm", "-rf", self.cloneRepoDir]
            return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            # Git clone commandに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90083")
            logaddstr = "%s\nexit code:(%s)" % (output, return_code)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg(output)
            self.SetLastErrorMsg(FREE_LOG)
            return False

        # 日本語文字化け対応
        return_var = None
        cmd = []
        cmd.append("git")
        cmd.extend(self.gitOption.split(' '))
        cmd.extend(["config", "--local", "core.quotepath", "false"])
        os.chdir(self.cloneRepoDir)
        return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if return_var.returncode != 0:
            # Git config の設定に失敗しました
            logstr = g.appmsg.get_api_message("MSG-90082")
            logaddstr = "%s\nexit code:(%s)" % (return_var.stdout, return_var.returncode)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg(return_var.stdout)
            self.SetLastErrorMsg(FREE_LOG)
            return False

        return True

    def GitLsFiles(self):

        ret_val = []

        # Git コマンドが失敗した場合、指定時間Waitし指定回数リトライする
        os.chdir(self.cloneRepoDir)
        cmd = ["git", "ls-files"]
        for idx in range(self.retryCount):
            return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if return_var.returncode == 0:
                break

            logaddstr = "%s\nexit code:(%s)\nError retry with git command" % (return_var.stdout, return_var.returncode)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)
            g.applogger.info(FREE_LOG)

            if self.retryCount - 1 > idx:
                time.sleep(self.retryWaitTime)

        if return_var.returncode == 0:
            ret_val = return_var.stdout.split('\n')
            ret_val = [val for val in ret_val if val]

        else:
            # Git ls-files commandに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90087")
            logaddstr = "%s\nexit code:(%s)" % (return_var.stdout, return_var.returncode)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg(return_var.stdout)
            self.SetLastErrorMsg(FREE_LOG)
            return False, ret_val

        return True, ret_val

    def GitPull(self, pullResultAry, Authtype, UpdateFlg=True):

        comd_ok = False
        ResultParsStr = self.GitCmdRsltParsAry['pull']['allrady-up-to-date']

        # Git Cloneコマンドが失敗した場合、指定時間Waitし指定回数リトライする
        for idx in range(self.retryCount):
            return_var = None
            cmd = [
                "sh",
                "%s/ky_GitCommand.sh" % (self.libPath),
                self.ProxyURL,
                Authtype,
                self.cloneRepoDir,
                "pull --rebase --ff",
                self.user, self.password, self.sshPassword, self.sshPassphrase,
                self.sshExtraArgsStr
            ]
            return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if return_var.returncode != 0:
                logaddstr = "%s\nexit code:(%s)\nError retry with git command" % (return_var.stdout, return_var.returncode)
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)
                g.applogger.info(FREE_LOG)

                if self.retryCount - 1 > idx:
                    time.sleep(self.retryWaitTime)

            else:
                output = return_var.stdout.split('\n')
                saveoutput = output
                format_ok = False
                for op in output:
                    ret = re.search(ResultParsStr, op)
                    if ret:
                        format_ok = True
                        UpdateFlg = False
                        break

                    ret = re.match("Fast-forward", op)
                    if ret:
                        format_ok = True
                        UpdateFlg = True
                        break

                if format_ok is True:
                    # 結果解析用にindexを0オリジンにする
                    pullResultAry = []
                    for line in output:
                        pullResultAry.append(line)

                    comd_ok = True
                    break

                else:
                    output = saveoutput

        if comd_ok is False:
            # Git pull commandに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90088")
            logaddstr = "%s\nexit code:(%s)" % (return_var.stdout, return_var.returncode)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg(return_var.stdout)
            self.SetLastErrorMsg(FREE_LOG)
            return False, pullResultAry, UpdateFlg

        return True, pullResultAry, UpdateFlg


################################################################
# 資材紐付処理クラス
################################################################
class CICD_GrandChildWorkflow():

    def __init__(self, org_id, ws_id, DBobj, RepoId, MatlLinkId, DelvFlg):

        self.org_id = org_id
        self.ws_id = ws_id
        self.DBobj = DBobj

        self.RepoId = RepoId
        self.MatlLinkId = MatlLinkId
        self.DelvExecFlg = True if DelvFlg != 0 else False

        self.cloneRepoDir = '/storage/%s/%s/driver/cicd/repositories/%s' % (org_id, ws_id, RepoId)

        self.error_flag = 0
        self.MatlLinkUpdate_Flg = False

        self.UIDelvExecInsNo = ""
        self.UIDelvExecMenuId = ""
        self.UIMatlUpdateStatusID = ""
        self.UIMatlUpdateStatusDisplayMsg = ""
        self.UIDelvStatusDisplayMsg = ""

        self.AddRepoIdMatlLinkIdStr = g.appmsg.get_api_message("MSG-90074", [RepoId, MatlLinkId])
        self.AddMatlLinkIdStr = g.appmsg.get_api_message("MSG-90075", [RepoId, MatlLinkId])

    def setDefaultUIDisplayMsg(self):

        self.UIMatlUpdateStatusDisplayMsg = g.appmsg.get_api_message("MSG-90109")
        if self.DelvExecFlg is True:
            self.UIDelvStatusDisplayMsg = g.appmsg.get_api_message("MSG-90110")

        else:
            self.UIDelvStatusDisplayMsg = ""

        self.UIMatlUpdateStatusID = TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR
        self.UIDelvExecInsNo = ""
        self.UIDelvExecMenuId = ""

    def setUIMatlSyncStatus(self, UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId):

        self.UIMatlUpdateStatusDisplayMsg = UIMatlSyncMsg
        if UIDelvMsg == "def":
            if self.DelvExecFlg is True:
                self.UIDelvStatusDisplayMsg = g.appmsg.get_api_message("MSG-90110")

            else:
                self.UIDelvStatusDisplayMsg = ""

        else:
            self.UIDelvStatusDisplayMsg = UIDelvMsg

        self.UIMatlUpdateStatusID = SyncSts
        self.UIDelvExecInsNo = DelvExecInsNo
        self.UIDelvExecMenuId = DelvExecMenuId

    def getUIMatlSyncStatus(self):

        return [
            self.UIMatlUpdateStatusDisplayMsg,
            self.UIDelvStatusDisplayMsg,
            self.UIMatlUpdateStatusID,
            self.UIDelvExecInsNo,
            self.UIDelvExecMenuId
        ]

    def CreateZipFile(self, inRolesDir, outRolesDir, zipFileName):

        outRolesDir = "/storage/%s/%s/tmp/driver/cicd/zipdir_%s" % (self.org_id, self.ws_id, self.RepoId)

        subprocess.run(["/bin/rm", "-rf", outRolesDir], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.run(["/bin/mkdir", "-p", outRolesDir], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        inRolesDir = re.sub(r'/roles$', '', inRolesDir)
        zipFileNameBase = os.path.basename(inRolesDir)
        zipFileName = "%s.zip" % (zipFileNameBase)

        cmd = "cd %s && zip -r %s/%s *" % (inRolesDir, outRolesDir, zipFileName)
        ret = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if ret.returncode != 0:
            ret = ret.stdout
            return ret, outRolesDir, zipFileName

        return True, outRolesDir, zipFileName

    def UpdateMatlLinkRecode(self, UpdateColumnAry):

        sql = "SELECT * FROM T_CICD_MATL_LINK WHERE MATL_LINK_ROW_ID=%s"
        objQuery = self.DBobj.sql_execute(sql, [self.MatlLinkId, ])
        if len(objQuery) != 1:
            self.error_flag = 1

            # データベースのアクセスに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90077")
            logstr = "%s%s" % (logstr, self.AddRepoIdMatlLinkIdStr)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
            return FREE_LOG

        row = objQuery[0]
        Update = False
        for column, value in UpdateColumnAry.items():
            if column in row and row[column] != value:
                row[column] = value
                Update = True

        if Update is False:
            FREE_LOG = g.appmsg.get_api_message("MSG-90069", [self.AddMatlLinkIdStr, ])
            g.applogger.debug(FREE_LOG)
            return True

        ret = self.DBobj.table_update('T_CICD_MATL_LINK', row, 'MATL_LINK_ROW_ID', is_register_history=False, last_timestamp=False)
        if ret is False:
            self.error_flag = 1

            # データベースのアクセスに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90077")
            logstr = "%s%s" % (logstr, self.AddRepoIdMatlLinkIdStr)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
            return FREE_LOG

        FREE_LOG = g.appmsg.get_api_message("MSG-90068", [self.AddMatlLinkIdStr, ])
        g.applogger.debug(FREE_LOG)

        return True

    def getTargetMatlLinkRow(self, tgtMatlLinkRow):

        # 資材紐付管理取得
        sql = (
            "SELECT "
            "  T1.*, "
            "  T3.MATL_FILE_PATH         M_MATL_FILE_PATH, "
            "  T3.MATL_FILE_TYPE_ROW_ID  M_MATL_FILE_TYPE_ROW_ID, "
            "  T7.OPERATION_NAME    OPE_OPERATION_NAME, "
            "  T8.ITA_EXT_STM_ID    M_ITA_EXT_STM_ID, "
            "  T8.MOVEMENT_NAME     MV_MOVEMENT_NAME, "
            "  T8.TIME_LIMIT        MV_TIME_LIMIT, "
            "  T8.ANS_WINRM_ID      MV_ANS_WINRM_ID, "
            "  T8.ANS_PLAYBOOK_HED_DEF            MV_ANS_PLAYBOOK_HED_DEF, "
            "  T8.ANS_HOST_DESIGNATE_TYPE_ID      MV_ANS_HOST_DESIGNATE_TYPE_ID, "
            "  T8.ANS_EXECUTION_ENVIRONMENT_NAME  MV_ANS_EXECUTION_ENVIRONMENT_NAME, "
            "  T8.ANS_ANSIBLE_CONFIG_FILE         MV_ANS_ANSIBLE_CONFIG_FILE, "
            "  T8.TERE_WORKSPACE_ID MV_TERE_WORKSPACE_ID, "
            "  T8.TERC_WORKSPACE_ID MV_TERC_WORKSPACE_ID, "
            "  T6.OS_TYPE_ID        M_OS_TYPE_ID, "
            "  T6.OS_TYPE_NAME      M_OS_TYPE_NAME, "
            "  T6.DISUSE_FLAG       OS_DISUSE_FLAG, "
            "  T5.DIALOG_TYPE_ID    M_DIALOG_TYPE_ID, "
            "  T5.DIALOG_TYPE_NAME  M_DIALOG_TYPE_NAME, "
            "  T5.DISUSE_FLAG       DALG_DISUSE_FLAG, "
            "  T2.DISUSE_FLAG       REPO_DISUSE_FLAG, "
            "  T3.DISUSE_FLAG       MATL_DISUSE_FLAG, "
            "  T7.DISUSE_FLAG       OPE_DISUSE_FLAG, "
            "  T8.DISUSE_FLAG       PTN_DISUSE_FLAG "
            "FROM "
            "  T_CICD_MATL_LINK     T1 "
            "LEFT OUTER JOIN T_CICD_REPOSITORY_LIST T2 ON T1.REPO_ROW_ID=T2.REPO_ROW_ID "
            "LEFT OUTER JOIN T_CICD_MATL_LIST       T3 ON T1.MATL_ROW_ID=T3.MATL_ROW_ID "
            "LEFT OUTER JOIN T_ANSP_DIALOG_TYPE     T5 ON T1.DIALOG_TYPE_ID=T5.DIALOG_TYPE_ID "
            "LEFT OUTER JOIN T_ANSP_OS_TYPE         T6 ON T1.OS_TYPE_ID=T6.OS_TYPE_ID "
            "LEFT OUTER JOIN T_COMN_OPERATION       T7 ON T1.DEL_OPE_ID=T7.OPERATION_ID "
            "LEFT OUTER JOIN T_COMN_MOVEMENT        T8 ON T1.DEL_MOVE_ID=T8.MOVEMENT_ID "
            "WHERE T1.MATL_LINK_ROW_ID = %s "
        )
        arrayBind = [self.MatlLinkId, ]
        objQuery = self.DBobj.sql_execute(sql, arrayBind)

        tgtMatlLinkRow = []
        for row in objQuery:
            tgtMatlLinkRow.append(row)

        return True, tgtMatlLinkRow

    def materialsRestAccess(self, row, tgtFilePath, tgt_o_mode, NoUpdateFlg):

        NoUpdateFlg = False
        materialType = row['MATL_TYPE_ROW_ID']
        linkname = row['MATL_LINK_NAME']
        filename = os.path.basename(tgtFilePath)

        # 素材タイプ別のパラメーター作成クラスを生成
        filter_dict = {}
        obj_make_param = None
        if materialType == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_LEGACY:
            filter_dict = {'PLAYBOOK_MATTER_NAME': linkname}
            obj_make_param = CICDMakeParamLegacy('T_ANSL_MATL_COLL', 'PLAYBOOK_MATTER_ID', 'PLAYBOOK_MATTER_FILE', 'playbook_files')
            file_paths = {"playbook_file": tgtFilePath}

        elif materialType == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_PIONEER:
            filter_dict = {'DIALOG_TYPE_ID': row['M_DIALOG_TYPE_ID'], 'OS_TYPE_ID': row['M_OS_TYPE_ID']}
            linkname = {'DIALOG_TYPE_ID': row['M_DIALOG_TYPE_NAME'], 'OS_TYPE_ID': row['M_OS_TYPE_NAME']}
            obj_make_param = CICDMakeParamPioneer('T_ANSP_MATL_COLL', 'DIALOG_MATTER_ID', 'DIALOG_MATTER_FILE', 'dialog_files')
            file_paths = {"dialog_files": tgtFilePath}

        elif materialType == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_ROLE:
            filter_dict = {'ROLE_PACKAGE_NAME': linkname}
            obj_make_param = CICDMakeParamRole('T_ANSR_MATL_COLL', 'ROLE_PACKAGE_ID', 'ROLE_PACKAGE_FILE', 'role_package_list')
            file_paths = {"role_package_list": tgtFilePath}

        elif materialType == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_CONTENT:
            filter_dict = {'CONTENTS_FILE_VARS_NAME': linkname}
            obj_make_param = CICDMakeParamContent('T_ANSC_CONTENTS_FILE', 'CONTENTS_FILE_ID', 'CONTENTS_FILE', 'file_list')
            file_paths = {"file_list": tgtFilePath}

        elif materialType == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_TEMPLATE:
            filter_dict = {'ANS_TEMPLATE_VARS_NAME': linkname}
            obj_make_param = CICDMakeParamTemplate('T_ANSC_TEMPLATE_FILE', 'ANS_TEMPLATE_ID', 'ANS_TEMPLATE_FILE', 'template_list')
            file_paths = {"template_list": tgtFilePath}

        elif materialType == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE:
            filter_dict = {'MODULE_MATTER_NAME': linkname}
            obj_make_param = CICDMakeParamModule('T_TERE_MODULE', 'MODULE_MATTER_ID', 'MODULE_MATTER_FILE', 'module_files_terraform_cloud_ep')
            file_paths = {"module_files_terraform_cloud_ep": tgtFilePath}

        elif materialType == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_POLICY:
            filter_dict = {'POLICY_NAME': linkname}
            obj_make_param = CICDMakeParamPolicy('T_TERE_POLICY', 'POLICY_ID', 'POLICY_MATTER_FILE', 'policy_list_terraform_cloud_ep')
            file_paths = {"policy_list_terraform_cloud_ep": tgtFilePath}

        elif materialType == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE_CLI:
            filter_dict = {'MODULE_MATTER_NAME': linkname}
            obj_make_param = CICDMakeParamModuleCLI('T_TERC_MODULE', 'MODULE_MATTER_ID', 'MODULE_MATTER_FILE', 'module_files_terraform_cli')
            file_paths = {"module_files_terraform_cli": tgtFilePath}

        if obj_make_param is None:
            return True, True

        editType_list = []

        # 素材の登録状況から操作種別を設定
        param = obj_make_param.make_param(row, filename)
        rset = obj_make_param.get_record(self.DBobj, **filter_dict)
        if len(rset) <= 0:
            # 素材が未登録の場合は「登録」
            editType_list.append(load_table.CMD_REGISTER)
            rset = {}

        else:
            # 登録されているレコードから操作対象の要素を1件にしぼる
            targetNum = -1
            for i, tmpval in enumerate(rset):
                if tmpval['DISUSE_FLAG'] == '0':
                    targetNum = i

            if targetNum < 0:
                targetNum = len(rset) - 1

            rset = rset[targetNum]
            tgt_data = {
                "path": tgtFilePath,
                "o_mode": tgt_o_mode
            }

            # 素材ファイルに差分がある場合は「更新」
            diff_flg = obj_make_param.diff_file(rset[obj_make_param.primary_key], rset[obj_make_param.file_col_name], tgt_data)
            if diff_flg is True:
                editType_list.append(load_table.CMD_UPDATE)

            # 廃止レコードが操作対象の場合は「復活」を追加
            if rset['DISUSE_FLAG'] == '1':
                editType_list.insert(0, load_table.CMD_RESTORE)

            # 廃止されていないレコードが操作対象の場合
            else:
                # 素材ファイル差分がなくとも、レコードに変更があれば「更新」
                if diff_flg is False:
                    for tmpkey, tmpval in param.items():
                        if tmpkey in rset and tmpval != rset[tmpkey]:
                            editType_list.append(load_table.CMD_UPDATE)
                            break

        if len(editType_list) <= 0:
            NoUpdateFlg = True

        # 素材ファイルのアップ、および、レコードの操作
        for editType in editType_list:
            uuid = rset[obj_make_param.primary_key] if obj_make_param.primary_key in rset else ''
            req_param = obj_make_param.make_rest_param(editType, linkname, filename, **rset)
            objmenu = load_table.loadTable(self.DBobj, obj_make_param.menu_name)
            result = objmenu.exec_maintenance(req_param, uuid, editType, pk_use_flg=False, auth_check=False, record_file_paths=file_paths)
            if result[0] is False:
                return result, NoUpdateFlg

        return True, NoUpdateFlg

    def executeMovement(self, row, run_mode):

        driver_info = {
            TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_LEGACY: AnscConst.DF_LEGACY_DRIVER_ID,
            TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_PIONEER: AnscConst.DF_PIONEER_DRIVER_ID,
            TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_ROLE: AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
            TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_TERRAFORM: TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP,
            TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_TERRAFORM_CLI: TFCommonConst.DRIVER_TERRAFORM_CLI
        }
        ansible_driver_list = [
            AnscConst.DF_LEGACY_DRIVER_ID, AnscConst.DF_PIONEER_DRIVER_ID, AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
        ]

        DriverType = driver_info[row['M_ITA_EXT_STM_ID']]
        schedule_date = None
        conductor_id = None
        conductor_name = None

        operation_row = {
            "OPERATION_ID": row['DEL_OPE_ID'],
            "OPERATION_NAME": row['OPE_OPERATION_NAME'],
        }

        movement_row = {}
        if DriverType in ansible_driver_list:
            movement_row = {
                "MOVEMENT_ID": row['DEL_MOVE_ID'],
                "MOVEMENT_NAME": row['MV_MOVEMENT_NAME'],
                "TIME_LIMIT": row['MV_TIME_LIMIT'],
                "ANS_WINRM_ID": row['MV_ANS_WINRM_ID'],
                "ANS_PLAYBOOK_HED_DEF": row['MV_ANS_PLAYBOOK_HED_DEF'],
                "ANS_HOST_DESIGNATE_TYPE_ID": row['MV_ANS_HOST_DESIGNATE_TYPE_ID'],
                "ANS_EXECUTION_ENVIRONMENT_NAME": row['MV_ANS_EXECUTION_ENVIRONMENT_NAME'],
                "ANS_ANSIBLE_CONFIG_FILE": row['MV_ANS_ANSIBLE_CONFIG_FILE'],
            }

        else:
            col_name_dst = "%s_WORKSPACE_ID" % (DriverType)
            col_name_src = "MV_%s" % (col_name_dst)
            movement_row = {
                "MOVEMENT_ID": row['DEL_MOVE_ID'],
                "MOVEMENT_NAME": row['MV_MOVEMENT_NAME'],
                "TIME_LIMIT": row['MV_TIME_LIMIT'],
                col_name_dst: row[col_name_src],
            }

        # 作業管理に登録
        if DriverType in ansible_driver_list:
            # Ansible用 作業実行登録
            result = a_insert_execution_list(self.DBobj, run_mode, DriverType, operation_row, movement_row, schedule_date, conductor_id, conductor_name)

        else:
            # Terraform用 作業実行登録
            result = t_insert_execution_list(self.DBobj, run_mode, DriverType, operation_row, movement_row, schedule_date, conductor_id, conductor_name)

        return True, result['execution_no']

    def MailLinkExecute(self):

        # /storage配下のファイルアクセスを/tmp経由で行うモジュール
        file_read = storage_access.storage_read()
        file_read_bytes = storage_access.storage_read_bytes()

        # 資材紐付管理より対象レコード取得
        tgtMatlLinkRow = []
        ret, tgtMatlLinkRow = self.getTargetMatlLinkRow(tgtMatlLinkRow)
        if ret is not True:
            # 異常フラグON
            self.error_flag = 1

            LogStr = ""
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, ret)

            # 想定外のエラー
            UIMatlSyncMsg = g.appmsg.get_api_message("MSG-90109")
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        # 処理対象か判定
        if len(tgtMatlLinkRow) == 0:
            # 異常フラグON
            self.error_flag = 1

            # 資材紐付管理の対象レコードが見つかりません。資材紐付処理をスキップします
            LogStr = g.appmsg.get_api_message("MSG-90095", [self.RepoId, self.MatlLinkId])
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, "")
            UIMatlSyncMsg = LogStr
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        else:
            row = tgtMatlLinkRow[0]

            # 廃止レコードか判定
            if row['DISUSE_FLAG'] == '1':
                return True

            # 自動同期が無効か判定
            elif row['AUTO_SYNC_FLG'] == TD_B_CICD_MATERIAL_LINK_LIST.C_AUTO_SYNC_FLG_OFF:
                return True

        # 紐付先資材タイプと資材パスの組み合わせチェック
        LogStr = ""
        ret, LogStr = MatlLinkColumnValidator2(row['MATL_TYPE_ROW_ID'], row['M_MATL_FILE_TYPE_ROW_ID'], self.RepoId, self.MatlLinkId, LogStr)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, "")
            UIMatlSyncMsg = LogStr
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        # 紐付先資材タイプとMovemnetの組み合わせチェック
        LogStr = ""
        ret, LogStr = MatlLinkColumnValidator5(self.RepoId, self.MatlLinkId, row['M_ITA_EXT_STM_ID'], row['MATL_TYPE_ROW_ID'], LogStr)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, "")
            UIMatlSyncMsg = LogStr
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        # 対象レコードのリレーション先確認
        LogStr = ""
        ret, LogStr = MatlLinkColumnValidator3(row, LogStr)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, "")
            UIMatlSyncMsg = LogStr
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        # 対象資材ファイルをbase64でエンコード
        tgtFileName = "%s/%s" % (self.cloneRepoDir, row['M_MATL_FILE_PATH'])
        if os.path.exists(tgtFileName) is False:
            # 異常フラグON
            self.error_flag = 1

            # 資材ファイルがローカルクローンディレクトリ内に見つかりません
            LogStr = g.appmsg.get_api_message("MSG-90096", [self.RepoId, self.MatlLinkId, tgtFileName])
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, "")

            UIMatlSyncMsg = g.appmsg.get_api_message("MSG-90109")
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        o_mode = "r"
        outRolesDir = ""
        zipFileName = ""

        # ファイルタイプを判定
        if row['M_MATL_FILE_TYPE_ROW_ID'] == TD_B_CICD_MATERIAL_FILE_TYPE_NAME.C_MATL_FILE_TYPE_ROW_ID_ROLES:
            # rolesディレクトリの場合
            rolesDir = "%s/%s" % (self.cloneRepoDir, row['M_MATL_FILE_PATH'])
            ret, outRolesDir, zipFileName = self.CreateZipFile(rolesDir, outRolesDir, zipFileName)
            if ret is not True:
                # 異常フラグON
                self.error_flag = 1

                # zipファイルの作成に失敗しました
                LogStr = g.appmsg.get_api_message("MSG-90096", [self.RepoId, self.MatlLinkId, tgtFileName])
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, ret)

                UIMatlSyncMsg = g.appmsg.get_api_message("MSG-90109")
                UIDelvMsg = "def"
                SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR
                DelvExecInsNo = ""
                DelvExecMenuId = ""
                self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
                return FREE_LOG

            o_mode = "rb"
            tgtFileName = "%s/%s" % (outRolesDir, zipFileName)

        tgtFileData = ""
        if o_mode == "r":
            file_read.open(tgtFileName)
            tgtFileData = file_read.read()
            file_read.close()
        else:
            tgtFileData = file_read_bytes.read_bytes(tgtFileName)

        if isinstance(tgtFileData, str) is True:
            tgtFileData = tgtFileData.encode()

        # 資材更新
        NoUpdateFlg = True
        ret, NoUpdateFlg = self.materialsRestAccess(row, tgtFileName, o_mode, NoUpdateFlg)
        if ret is True:
            if NoUpdateFlg is True:
                if row['SYNC_STATUS_ROW_ID'] == TD_SYNC_STATUS_NAME_DEFINE.STS_NORMAL:
                    self.MatlLinkUpdate_Flg = True

                else:
                    UIMatlSyncMsg = ""
                    UIDelvMsg = ""
                    SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_NORMAL
                    DelvExecInsNo = ""
                    DelvExecMenuId = ""
                    self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)

                return True

        else:
            # 異常フラグON
            self.error_flag = 1

            ErrorMsgHeder = {
                TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_LEGACY: g.appmsg.get_api_message("MSG-90098", [self.RepoId, self.MatlLinkId]),
                TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_PIONEER: g.appmsg.get_api_message("MSG-90099", [self.RepoId, self.MatlLinkId]),
                TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_ROLE: g.appmsg.get_api_message("MSG-90100", [self.RepoId, self.MatlLinkId]),
                TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_CONTENT: g.appmsg.get_api_message("MSG-90101", [self.RepoId, self.MatlLinkId]),
                TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_TEMPLATE: g.appmsg.get_api_message("MSG-90102", [self.RepoId, self.MatlLinkId]),
                TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE: g.appmsg.get_api_message("MSG-90103", [self.RepoId, self.MatlLinkId]),
                TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_POLICY: g.appmsg.get_api_message("MSG-90104", [self.RepoId, self.MatlLinkId]),
                TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE_CLI: g.appmsg.get_api_message("MSG-90103", [self.RepoId, self.MatlLinkId]),
            }

            LogStr = ErrorMsgHeder[row['MATL_TYPE_ROW_ID']] if row['MATL_TYPE_ROW_ID'] in ErrorMsgHeder else ""
            ret = ret[2] if len(ret) >= 3 else ret
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, ret)
            UIMatlSyncMsg = "%s\n%s" % (LogStr, ret)
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        if self.DelvExecFlg is False:
            UIMatlSyncMsg = ""
            UIDelvMsg = ""
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_NORMAL
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return True

        # Movement実行
        runMode = 2
        if row['DEL_EXEC_TYPE'] is None or row['DEL_EXEC_TYPE'] == "" or row['DEL_EXEC_TYPE'] == "0":
            runMode = 1

        ret, exec_no = self.executeMovement(row, runMode)
        if ret is True:
            UIMatlSyncMsg = ""
            UIDelvMsg = ""
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_NORMAL
            DelvExecInsNo = exec_no
            DelvExecMenuId = TD_C_PATTERN_PER_ORCH.C_CHECK_OPERATION_STATUS_MENU_NAME[row['M_ITA_EXT_STM_ID']]
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)

        else:
            self.error_flag = 1

            ErrorMsgHeder = {
                TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_LEGACY: g.appmsg.get_api_message("MSG-90105", [self.RepoId, self.MatlLinkId]),
                TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_PIONEER: g.appmsg.get_api_message("MSG-90106", [self.RepoId, self.MatlLinkId]),
                TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_ROLE: g.appmsg.get_api_message("MSG-90107", [self.RepoId, self.MatlLinkId]),
                TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_TERRAFORM: g.appmsg.get_api_message("MSG-90108", [self.RepoId, self.MatlLinkId]),
                TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_TERRAFORM_CLI: g.appmsg.get_api_message("MSG-90108", [self.RepoId, self.MatlLinkId]),
            }

            LogStr = ErrorMsgHeder[row['M_ITA_EXT_STM_ID']] if row['M_ITA_EXT_STM_ID'] in ErrorMsgHeder else ""
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, ret)
            UIMatlSyncMsg = ""
            UIDelvMsg = "%s\n%s" % (LogStr, ret)
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        return True

    def main(self):

        try:
            self.DBobj.db_transaction_start()

            # リモートリポジトリ管理の情報を取得
            ret = self.MailLinkExecute()
            if ret is not True:
                self.error_flag = 1

                # 紐付資材の更新に失敗しました
                logstr = g.appmsg.get_api_message("MSG-90097", [self.RepoId, self.MatlLinkId])
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, ret)
                raise Exception(FREE_LOG)

            # 資材紐付管理の同期状態・デリバリ状態更新
            if self.MatlLinkUpdate_Flg is False:
                reyAry = self.getUIMatlSyncStatus()

                UpdateColumnAry = {}
                UpdateColumnAry['SYNC_STATUS_ROW_ID'] = reyAry[2]
                UpdateColumnAry['SYNC_ERROR_NOTE'] = reyAry[0]
                UpdateColumnAry['SYNC_LAST_TIME'] = datetime.datetime.now()
                UpdateColumnAry['SYNC_LAST_UPDATE_USER'] = g.USER_ID
                UpdateColumnAry['DEL_ERROR_NOTE'] = reyAry[1]
                UpdateColumnAry['DEL_EXEC_INS_NO'] = reyAry[3]
                UpdateColumnAry['DEL_MENU_NO'] = reyAry[4]

                ret = self.UpdateMatlLinkRecode(UpdateColumnAry)
                if ret is not True:
                    self.error_flag = 1
                    self.setDefaultUIDisplayMsg()

                    # データベースの更新に失敗しました
                    logstr = g.appmsg.get_api_message("MSG-90079", [self.AddMatlLinkIdStr,])
                    FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, ret)
                    raise Exception(FREE_LOG)

            ret = self.DBobj.db_transaction_end(True)
            if ret is not True:
                self.setDefaultUIDisplayMsg()
                self.error_flag = 1

                # ランザクション処理に失敗しました
                logstr = g.appmsg.get_api_message("MSG-90076")
                logstr = "%s%s" % (logstr, self.AddRepoIdMatlLinkIdStr)
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
                raise Exception(FREE_LOG)

            self.MatlLinkUpdate_Flg = True

        except Exception as e:
            FREE_LOG = str(e)
            # Exceptionの処理なのでログレベルはerrorにする
            g.applogger.error(FREE_LOG)
            self.DBobj.db_transaction_end(False)

        if self.MatlLinkUpdate_Flg is False:
            reyAry = self.getUIMatlSyncStatus()

            UpdateColumnAry = {}
            UpdateColumnAry['SYNC_STATUS_ROW_ID'] = reyAry[2]
            UpdateColumnAry['SYNC_ERROR_NOTE'] = reyAry[0]
            UpdateColumnAry['SYNC_LAST_TIME'] = datetime.datetime.now()
            UpdateColumnAry['SYNC_LAST_UPDATE_USER'] = g.USER_ID
            UpdateColumnAry['DEL_ERROR_NOTE'] = reyAry[1]
            UpdateColumnAry['DEL_EXEC_INS_NO'] = reyAry[3]
            UpdateColumnAry['DEL_MENU_NO'] = reyAry[4]

            ret = self.UpdateMatlLinkRecode(UpdateColumnAry)
            if ret is not True:
                self.error_flag = 1
                self.setDefaultUIDisplayMsg()

                # データベースの更新に失敗しました
                logstr = g.appmsg.get_api_message("MSG-90079", [self.AddMatlLinkIdStr,])
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, ret)
                g.applogger.info(FREE_LOG)

            self.DBobj.db_transaction_end(True)

        # 結果出力
        if self.error_flag != 0:
            FREE_LOG = g.appmsg.get_api_message("MSG-90051")
            g.applogger.debug(FREE_LOG)

        else:
            FREE_LOG = g.appmsg.get_api_message("MSG-90050")
            g.applogger.debug(FREE_LOG)

        return 0


################################################################
# リポジトリ同期処理クラス
################################################################
class CICD_ChildWorkflow():

    def __init__(self, org_id, ws_id, DBobj, RepoId, ExecMode, RepoListRow):

        self.error_flag = 0
        self.warning_flag = 0
        self.UIDisplayMsg = ""

        self.org_id = org_id
        self.ws_id = ws_id
        self.DBobj = DBobj

        config = configparser.ConfigParser()

        self.RepoId = RepoId
        self.ExecMode = ExecMode
        self.RepoListRow = RepoListRow

        self.MatlListUpdateExeFlg = True
        if ExecMode == "Normal":
            self.MatlListUpdateExeFlg = False

        if RepoListRow['SYNC_STATUS_ROW_ID'] is None or RepoListRow['SYNC_STATUS_ROW_ID'] == TD_SYNC_STATUS_NAME_DEFINE.STS_RESTART:
            self.MatlListUpdateExeFlg = True

        self.cloneRepoDir = '/storage/%s/%s/driver/cicd/repositories/%s' % (org_id, ws_id, RepoId)
        libPath = '/exastro/common_libs/cicd/shells'
        GitCmdRsltParsStrFileNamePath = '/exastro/common_libs/cicd/shells/gitCommandResultParsingStringDefinition.ini'
        config.read(GitCmdRsltParsStrFileNamePath)
        self.Gitobj = ControlGit(RepoId, RepoListRow, self.cloneRepoDir, libPath, config)

    def setDefaultUIDisplayMsg(self):

        self.UIDisplayMsg = g.appmsg.get_api_message("MSG-90109")

    def makeReturnArray(self, RetCode, LogStr, UIMsg):

        ary = {}
        ary['RetCode'] = RetCode
        ary['log'] = LogStr
        ary['UImsg'] = UIMsg

        return json.dumps(ary)

    def getAuthType(self):

        PassAuth = ""

        # httpsの場合
        if self.RepoListRow["GIT_PROTOCOL_TYPE_ROW_ID"] == TD_B_CICD_GIT_PROTOCOL_TYPE_NAME.C_GIT_PROTOCOL_TYPE_ROW_ID_HTTPS:
            PassAuth = "httpNoUserAuth"
            if self.RepoListRow["GIT_REPO_TYPE_ROW_ID"] == TD_B_CICD_GIT_REPOSITORY_TYPE_NAME.C_GIT_REPO_TYPE_ROW_ID_PUBLIC:
                PassAuth = "httpNoUserAuth"

            elif self.RepoListRow["GIT_REPO_TYPE_ROW_ID"] == TD_B_CICD_GIT_REPOSITORY_TYPE_NAME.C_GIT_REPO_TYPE_ROW_ID_PRIVATE:
                PassAuth = "httpUserAuth"

        # ssh(パスワード認証)の場合
        elif self.RepoListRow["GIT_PROTOCOL_TYPE_ROW_ID"] == TD_B_CICD_GIT_PROTOCOL_TYPE_NAME.C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_PASS:
            PassAuth = "sshPassAuth"

        # ssh(パスフレーズあり)の場合
        elif self.RepoListRow["GIT_PROTOCOL_TYPE_ROW_ID"] == TD_B_CICD_GIT_PROTOCOL_TYPE_NAME.C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_KEY:
            PassAuth = "sshKeyAuthPass"

        # ssh(パスフレーズなし)の場合
        elif self.RepoListRow["GIT_PROTOCOL_TYPE_ROW_ID"] == TD_B_CICD_GIT_PROTOCOL_TYPE_NAME.C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_KEY_NOPASS:
            PassAuth = "sshKeyAuthNoPass"

        return PassAuth

    def LocalsetSshExtraArgs(self):

        ret = self.Gitobj.setSshExtraArgs()
        if ret is False:
            self.error_flag = 1

            logstr = g.appmsg.get_api_message("MSG-90090")
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            self.UIDisplayMsg = '%s\n%s' % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            raise CICDException(False, FREE_LOG, self.UIDisplayMsg)

        return True

    def LocalCloneRemoteRepoChk(self):

        # ローカルクローンのリモートリポジトリ確認
        ret = self.Gitobj.GitRemoteChk()
        if ret == -1:
            self.error_flag = 1

            logstr = g.appmsg.get_api_message("MSG-90085")
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            self.UIDisplayMsg = '%s\n%s' % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            raise CICDException(False, FREE_LOG, self.UIDisplayMsg)

        return ret

    def LocalCloneBranchChk(self):

        # 認証方式の判定
        AuthTypeName = self.getAuthType()

        # ローカルクローンのブランチ確認
        ret = self.Gitobj.GitBranchChk(AuthTypeName)
        if ret == -1:
            logstr = g.appmsg.get_api_message("MSG-90086")
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            self.UIDisplayMsg = '%s\n%s' % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            retary = self.makeReturnArray(False, FREE_LOG, self.UIDisplayMsg)
            raise Exception(retary)

        return ret

    def MatlListRecodeDisuseUpdate(self):

        table_name = "T_CICD_MATL_LIST"
        cols = self.DBobj.table_columns_get(table_name)
        cols = (',').join(cols[0])
        sql = (
            "SELECT %s "
            "FROM %s "
            "WHERE REPO_ROW_ID=%%s "
            "AND DISUSE_FLAG='0' "
        ) % (cols, table_name)
        arrayBind = [self.RepoId, ]

        objQuery = self.DBobj.sql_execute(sql, arrayBind)
        for row in objQuery:
            row['DISUSE_FLAG'] = '1'
            ret = self.DBobj.table_update(table_name, row, 'MATL_ROW_ID', is_register_history=False)
            if ret is False:
                # Clone異常時の処理なのでログを出力してReturn
                logstr = g.appmsg.get_api_message("MSG-90077")
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
                g.applogger.info(FREE_LOG)
                return False

        return True

    def MatlListRecodeDisuse(self):

        # 資材一覧のレコードを全て廃止
        self.DBobj.db_transaction_start()
        ret = self.MatlListRecodeDisuseUpdate()

        # トランザクションをコミット・ロールバック
        if ret is True:
            ret = self.DBobj.db_transaction_end(True)
            if ret is False:
                # Clone異常時の処理なのでログを出力してReturn
                logstr = g.appmsg.get_api_message("MSG-90076")
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
                return False

        else:
            ret = self.DBobj.db_transaction_end(False)
            if ret is False:
                # Clone異常時の処理なのでログを出力してReturn
                logstr = g.appmsg.get_api_message("MSG-90076")
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
                return False

        return True

    def CreateLocalClone(self):

        ret = self.Gitobj.LocalCloneDirClean()
        if ret is False:
            # 該当のリモートリポジトリに紐づいている資材を資材一覧から廃止
            self.MatlListRecodeDisuse()
            self.error_flag = 1

            # ローカルクローンディレクトリの作成に失敗しました
            logstr = g.appmsg.get_api_message("MSG-90078", [self.cloneRepoDir, ])
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            self.UIDisplayMsg = "%s\n%s" % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            raise CICDException(False, FREE_LOG, self.UIDisplayMsg)

        FREE_LOG = g.appmsg.get_api_message("MSG-90058", [self.RepoId, ])
        g.applogger.debug(FREE_LOG)

        # 認証方式か判定
        AuthTypeName = self.getAuthType()
        # 外部ソフトアクセス時のログを残す
        g.applogger.info("Git clone start")
        ret = self.Gitobj.GitClone(AuthTypeName)
        if ret is False:
            # 該当のリモートリポジトリに紐づいている資材を資材一覧から廃止
            self.MatlListRecodeDisuse()

            self.error_flag = 1

            # Git clone commandに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90081")
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            self.UIDisplayMsg = "%s\n%s" % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            raise CICDException(False, FREE_LOG, self.UIDisplayMsg)

        # 外部ソフトアクセス時のログを残す
        g.applogger.info("Git clone end")
        FREE_LOG = g.appmsg.get_api_message("MSG-90059", [self.RepoId, ])
        g.applogger.debug(FREE_LOG)

        return True

    def getLocalCloneFileList(self):

        ret, GitFiles = self.Gitobj.GitLsFiles()
        if ret is False:
            self.error_flag = 1

            # Git ls-files commandに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90087")
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            self.UIDisplayMsg = "%s\n%s" % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            raise CICDException(False, FREE_LOG, self.UIDisplayMsg)

        return True, GitFiles

    def getRolesPath(self, GitFiles):

        RolesPath = {}
        for FilePath in GitFiles:
            FilePath = "/%s" % (FilePath)
            if "/roles/" not in FilePath:
                continue

            pathNestAry = FilePath.split('/')
            pathNestAry[0] = "/"
            path = ""
            for idx in range(len(pathNestAry)):
                if idx in [0, 1]:
                    path = "%s%s" % (path, pathNestAry[idx])

                else:
                    path = "%s/%s" % (path, pathNestAry[idx])
                    if pathNestAry[idx] == 'roles':
                        if idx + 1 != len(pathNestAry):
                            addPath = path[1:]
                            RolesPath[addPath] = 0

        FREE_LOG = g.appmsg.get_api_message("MSG-90054", [self.RepoId, ])
        g.applogger.debug(FREE_LOG)

        return RolesPath

    def GitPull(self):

        pullResultAry = {}
        UpdateFiles = {}
        UpdateFlg = False

        # 認証方式か判定
        AuthTypeName = self.getAuthType()

        ret, pullResultAry, UpdateFlg = self.Gitobj.GitPull(pullResultAry, AuthTypeName, UpdateFlg)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            # Git pull commandに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90088")
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            # UIに表示するメッセージ
            self.UIDisplayMsg = "%s\n%s" % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            # 戻り値編集
            retary = self.makeReturnArray(-1, FREE_LOG, self.UIDisplayMsg)
            raise Exception(retary)

        FREE_LOG = g.appmsg.get_api_message("MSG-90064", [self.RepoId, UpdateFlg])
        g.applogger.debug(FREE_LOG)

        return True, pullResultAry, UpdateFiles, UpdateFlg

    def getMatlListRecodes(self):

        MatlListRecodes = {}

        table_name = "T_CICD_MATL_LIST"
        cols = self.DBobj.table_columns_get(table_name)
        cols = (',').join(cols[0])
        sql = (
            "SELECT %s "
            "FROM %s "
            "WHERE REPO_ROW_ID=%%s "
        ) % (cols, table_name)
        arrayBind = [self.RepoId, ]

        objQuery = self.DBobj.sql_execute(sql, arrayBind)
        for row in objQuery:
            if row['DISUSE_FLAG'] == '1':
                row['RECODE_ACCTION'] = 'none'

            else:
                row['RECODE_ACCTION'] = 'disuse'

            # 資材一覧更新状態
            if row['MATL_FILE_TYPE_ROW_ID'] not in MatlListRecodes:
                MatlListRecodes[row['MATL_FILE_TYPE_ROW_ID']] = {}

            if row['MATL_FILE_PATH'] not in MatlListRecodes[row['MATL_FILE_TYPE_ROW_ID']]:
                MatlListRecodes[row['MATL_FILE_TYPE_ROW_ID']][row['MATL_FILE_PATH']] = None

            MatlListRecodes[row['MATL_FILE_TYPE_ROW_ID']][row['MATL_FILE_PATH']] = row

        return True, MatlListRecodes

    def MatlListDisuseUpdate(self, row, Disuse):
        where_disuse_flag = '1' if Disuse == '0' else '0'
        table_name = "T_CICD_MATL_LIST"
        cols = self.DBobj.table_columns_get(table_name)
        cols = (',').join(cols[0])
        sql = (
            "SELECT %s "
            "FROM %s "
            "WHERE MATL_ROW_ID=%%s "
            "AND DISUSE_FLAG='%s' "
        ) % (cols, table_name, where_disuse_flag)
        arrayBind = [row['MATL_ROW_ID'], ]

        objQuery = self.DBobj.sql_execute(sql, arrayBind)
        row = objQuery[0]
        row["DISUSE_FLAG"] = Disuse
        ret = self.DBobj.table_update(table_name, row, 'MATL_ROW_ID', is_register_history=False)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            # データベースのアクセスに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90077")
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)

            # UIに表示するメッセージ
            self.UIDisplayMsg = g.appmsg.get_api_message("MSG-90109")

            # 戻り値編集
            retary = self.makeReturnArray(-1, FREE_LOG, self.UIDisplayMsg)
            raise Exception(retary)

        return True

    def MatlListInsert(self, row):

        table_name = "T_CICD_MATL_LIST"
        cols = self.DBobj.table_columns_get(table_name)

        ColumnValueArray = {}
        for colname in cols[0]:
            ColumnValueArray[colname] = None

        ColumnValueArray["REPO_ROW_ID"] = row['REPO_ROW_ID']
        ColumnValueArray["MATL_FILE_PATH"] = row['MATL_FILE_PATH']
        ColumnValueArray["MATL_FILE_TYPE_ROW_ID"] = row['MATL_FILE_TYPE_ROW_ID']
        ColumnValueArray["DISUSE_FLAG"] = "0"

        ret = self.DBobj.table_insert(table_name, ColumnValueArray, 'MATL_ROW_ID', is_register_history=False)
        if ret is False:
            self.error_flag = 1

            # データベースのアクセスに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90077")
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)

            self.UIDisplayMsg = g.appmsg.get_api_message("MSG-90109")

            # 戻り値編集
            raise CICDException(-1, FREE_LOG, self.UIDisplayMsg)

        row['MATL_ROW_ID'] = ret[0]['MATL_ROW_ID']

        return True

    def MatlListMerge(self, MatlListRecodes, RolesPath, GitFiles):

        # rolesディレクトリの増減確認
        for path, dummy in RolesPath.items():
            FileType = TD_B_CICD_MATERIAL_FILE_TYPE_NAME.C_MATL_FILE_TYPE_ROW_ID_ROLES
            if FileType in MatlListRecodes and path in MatlListRecodes[FileType] and MatlListRecodes[FileType][path] is not None:
                # 廃止確認
                if MatlListRecodes[FileType][path]['DISUSE_FLAG'] == '0':
                    del MatlListRecodes[FileType][path]

                else:
                    MatlListRecodes[FileType][path]['RECODE_ACCTION'] = 'use'
                    MatlListRecodes[FileType][path]['DISUSE_FLAG'] = '0'

            else:
                # レコードの項目値設定
                if FileType not in MatlListRecodes:
                    MatlListRecodes[FileType] = {}

                if path not in MatlListRecodes[FileType]:
                    MatlListRecodes[FileType][path] = {}

                MatlListRecodes[FileType][path]['MATL_ROW_ID'] = 0
                MatlListRecodes[FileType][path]['REPO_ROW_ID'] = self.RepoId
                MatlListRecodes[FileType][path]['MATL_FILE_PATH'] = path
                MatlListRecodes[FileType][path]['MATL_FILE_TYPE_ROW_ID'] = FileType
                MatlListRecodes[FileType][path]['RECODE_ACCTION'] = 'Insert'

        # ファイルの増減確認
        for path in GitFiles:
            FileType = TD_B_CICD_MATERIAL_FILE_TYPE_NAME.C_MATL_FILE_TYPE_ROW_ID_FILE
            if FileType in MatlListRecodes and path in MatlListRecodes[FileType] and MatlListRecodes[FileType][path]:
                # 廃止確認
                if MatlListRecodes[FileType][path]['DISUSE_FLAG'] == '0':
                    del MatlListRecodes[FileType][path]

                else:
                    MatlListRecodes[FileType][path]['RECODE_ACCTION'] = 'use'
                    MatlListRecodes[FileType][path]['DISUSE_FLAG'] = '0'

            else:
                # レコードの項目値設定
                if FileType not in MatlListRecodes:
                    MatlListRecodes[FileType] = {}

                if path not in MatlListRecodes[FileType]:
                    MatlListRecodes[FileType][path] = {}

                MatlListRecodes[FileType][path]['MATL_ROW_ID'] = 0
                MatlListRecodes[FileType][path]['REPO_ROW_ID'] = self.RepoId
                MatlListRecodes[FileType][path]['MATL_FILE_PATH'] = path
                MatlListRecodes[FileType][path]['MATL_FILE_TYPE_ROW_ID'] = FileType
                MatlListRecodes[FileType][path]['RECODE_ACCTION'] = 'Insert'

        # 増減分を資材管理に反映
        for FileType, Recodes in MatlListRecodes.items():
            for path, row in Recodes.items():
                # 資材管理のレコード廃止
                if row['RECODE_ACCTION'] == 'disuse':
                    del row['RECODE_ACCTION']
                    ret = self.MatlListDisuseUpdate(row, '1')
                    FREE_LOG = g.appmsg.get_api_message("MSG-90063", [path,])
                    g.applogger.debug(FREE_LOG)

                # 資材管理にレコード追加
                elif row['RECODE_ACCTION'] == 'Insert':
                    del row['RECODE_ACCTION']
                    ret = self.MatlListInsert(row)
                    FREE_LOG = g.appmsg.get_api_message("MSG-90061", [path,])
                    g.applogger.debug(FREE_LOG)

                # 資材管理のレコード復活
                elif row['RECODE_ACCTION'] == 'use':
                    del row['RECODE_ACCTION']
                    ret = self.MatlListDisuseUpdate(row, '0')
                    FREE_LOG = g.appmsg.get_api_message("MSG-90062", [path,])
                    g.applogger.debug(FREE_LOG)

        return True, MatlListRecodes

    def MatlListRolesRecodeUpdate(self):

        sql = (
            "SELECT "
            "  TAB_A.*, ( "
            "    SELECT COUNT(*) "
            "    FROM T_CICD_MATL_LIST TAB_B "
            "    WHERE TAB_B.MATL_FILE_PATH LIKE CONCAT(TAB_A.MATL_FILE_PATH, '/%%') "
            "    AND TAB_B.MATL_FILE_TYPE_ROW_ID = %s "
            "    AND TAB_B.REPO_ROW_ID = %s "
            "    AND TAB_B.DISUSE_FLAG = '0' "
            "  ) AS FILE_COUNTT "
            "FROM "
            "  T_CICD_MATL_LIST TAB_A "
            "WHERE "
            "      TAB_A.MATL_FILE_TYPE_ROW_ID = %s "
            "  AND TAB_A.REPO_ROW_ID = %s "
        )
        arrayBind = [
            TD_B_CICD_MATERIAL_FILE_TYPE_NAME.C_MATL_FILE_TYPE_ROW_ID_FILE,
            self.RepoId,
            TD_B_CICD_MATERIAL_FILE_TYPE_NAME.C_MATL_FILE_TYPE_ROW_ID_ROLES,
            self.RepoId
        ]

        objQuery = self.DBobj.sql_execute(sql, arrayBind)
        for row in objQuery:
            Acction = ""

            # 有効レコードでroles配下にファイルなし
            if row['DISUSE_FLAG'] == '0' and row['FILE_COUNTT'] == 0:
                row['DISUSE_FLAG'] = '1'
                Acction = "disuse"

            # 廃止レコードでroles配下にファイルあり
            elif row['DISUSE_FLAG'] == '1' and row['FILE_COUNTT'] != 0:
                row['DISUSE_FLAG'] = '0'
                Acction = "use"

            if Acction != "":
                del row['FILE_COUNTT']
                ColumnValueArray = row
                ret = self.DBobj.table_update("T_CICD_MATL_LIST", ColumnValueArray, 'MATL_ROW_ID', is_register_history=False)
                if ret is False:
                    # 異常フラグON
                    self.error_flag = 1

                    # データベースのアクセスに失敗しました
                    logstr = g.appmsg.get_api_message("MSG-90077")
                    FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)

                    # UIに表示するメッセージ
                    self.UIDisplayMsg = g.appmsg.get_api_message("MSG-90109")

                    # 戻り値編集
                    retary = self.makeReturnArray(-1, FREE_LOG, self.UIDisplayMsg)
                    raise Exception(retary)

                if Acction == "use":
                    FREE_LOG = g.appmsg.get_api_message("MSG-90062", [row['MATL_FILE_PATH'], ])
                    g.applogger.debug(FREE_LOG)

                else:
                    FREE_LOG = g.appmsg.get_api_message("MSG-90063", [row['MATL_FILE_PATH'], ])
                    g.applogger.debug(FREE_LOG)

        return True

    def UpdateSyncStatusRecode(self):

        sql = (
            "UPDATE T_CICD_REPOSITORY_LIST "
            "SET SYNC_LAST_TIMESTAMP = %s "
            "WHERE REPO_ROW_ID = %s "
        )
        arrayBind = [datetime.datetime.now(), self.RepoId]
        self.DBobj.sql_execute(sql, arrayBind)

        FREE_LOG = g.appmsg.get_api_message("MSG-90067", [self.RepoId, ])
        g.applogger.debug(FREE_LOG)

        return True

    def UpdateRepoListRecode(self, UpdateColumnAry):

        table_name = "T_CICD_REPOSITORY_LIST"
        cols = self.DBobj.table_columns_get(table_name)
        cols = (',').join(cols[0])

        sql = (
            "SELECT %s "
            "FROM %s "
            "WHERE REPO_ROW_ID=%%s "
        ) % (cols, table_name)
        arrayBind = [UpdateColumnAry['REPO_ROW_ID'], ]

        objQuery = self.DBobj.sql_execute(sql, arrayBind)
        if len(objQuery) != 1:
            # 異常フラグON
            self.error_flag = 1

            # データベースのアクセスに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90077")
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
            return FREE_LOG

        row = objQuery[0]
        Update = False
        for column, value in UpdateColumnAry.items():
            if row[column] != value:
                row[column] = value
                Update = True

        if Update is False:
            FREE_LOG = g.appmsg.get_api_message("MSG-90069", [self.RepoId, ])
            g.applogger.debug(FREE_LOG)

            return True

        ret = self.DBobj.table_update(table_name, row, "REPO_ROW_ID", is_register_history=False, last_timestamp=False)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            # データベースのアクセスに失敗しました
            logstr = g.appmsg.get_api_message("MSG-90077")
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)

            return FREE_LOG

        FREE_LOG = g.appmsg.get_api_message("MSG-90068", [self.RepoId, ])
        g.applogger.debug(FREE_LOG)

        return True

    def UpdateRepoListSyncStatus(self, SyncStatus):

        UpdateColumnAry = {}
        UpdateColumnAry['REPO_ROW_ID'] = self.RepoId
        UpdateColumnAry['SYNC_STATUS_ROW_ID'] = SyncStatus
        UpdateColumnAry['SYNC_LAST_TIMESTAMP'] = datetime.datetime.now()
        if SyncStatus == TD_SYNC_STATUS_NAME_DEFINE.STS_NORMAL:
            UpdateColumnAry['SYNC_ERROR_NOTE'] = ""

        else:
            UpdateColumnAry['SYNC_ERROR_NOTE'] = self.UIDisplayMsg

        ret = self.UpdateRepoListRecode(UpdateColumnAry)

        return ret

    def getTargetMatlLinkRow(self, tgtMatlLinkRow):

        # 資材紐付管理取得
        sql = (
            "SELECT "
            "  T1.*, "
            "  T3.MATL_FILE_PATH         M_MATL_FILE_PATH, "
            "  T3.MATL_FILE_TYPE_ROW_ID  M_MATL_FILE_TYPE_ROW_ID, "
            "  T8.ITA_EXT_STM_ID    M_ITA_EXT_STM_ID, "
            "  T6.OS_TYPE_ID        M_OS_TYPE_ID, "
            "  T6.OS_TYPE_NAME      M_OS_TYPE_NAME, "
            "  T6.DISUSE_FLAG       OS_DISUSE_FLAG, "
            "  T5.DIALOG_TYPE_ID    M_DIALOG_TYPE_ID, "
            "  T5.DIALOG_TYPE_NAME  M_DIALOG_TYPE_NAME, "
            "  T5.DISUSE_FLAG       DALG_DISUSE_FLAG, "
            "  T2.DISUSE_FLAG       REPO_DISUSE_FLAG, "
            "  T3.DISUSE_FLAG       MATL_DISUSE_FLAG, "
            "  T7.DISUSE_FLAG       OPE_DISUSE_FLAG, "
            "  T8.DISUSE_FLAG       PTN_DISUSE_FLAG "
            "FROM "
            "  T_CICD_MATL_LINK     T1 "
            "LEFT OUTER JOIN T_CICD_REPOSITORY_LIST T2 ON T1.REPO_ROW_ID=T2.REPO_ROW_ID "
            "LEFT OUTER JOIN T_CICD_MATL_LIST       T3 ON T1.MATL_ROW_ID=T3.MATL_ROW_ID "
            "LEFT OUTER JOIN T_ANSP_DIALOG_TYPE     T5 ON T1.DIALOG_TYPE_ID=T5.DIALOG_TYPE_ID "
            "LEFT OUTER JOIN T_ANSP_OS_TYPE         T6 ON T1.OS_TYPE_ID=T6.OS_TYPE_ID "
            "LEFT OUTER JOIN T_COMN_OPERATION       T7 ON T1.DEL_OPE_ID=T7.OPERATION_ID "
            "LEFT OUTER JOIN T_COMN_MOVEMENT        T8 ON T1.DEL_MOVE_ID=T8.MOVEMENT_ID "
            "WHERE T1.REPO_ROW_ID   = %s "
            "AND   T1.DISUSE_FLAG   = '0' "
            "AND   T1.AUTO_SYNC_FLG = %s "
        )
        arrayBind = [self.RepoId, TD_B_CICD_MATERIAL_LINK_LIST.C_AUTO_SYNC_FLG_ON]

        tgtMatlLinkRow = []
        objQuery = self.DBobj.sql_execute(sql, arrayBind)
        for row in objQuery:
            tgtMatlLinkRow.append(row)

        return True, tgtMatlLinkRow

    def MatlLinkExecute(self, MargeExeFlg):

        tgtMatlLinkRow = []
        ret, tgtMatlLinkRow = self.getTargetMatlLinkRow(tgtMatlLinkRow)
        if ret is not True:
            self.error_flag = 1

            logstr = g.appmsg.get_api_message("MSG-90093")
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
            return FREE_LOG

        for row in tgtMatlLinkRow:
            go = False
            if MargeExeFlg is True or self.MatlListUpdateExeFlg is True:
                # 同期状態が異常以外の場合を判定
                if row['SYNC_STATUS_ROW_ID'] != TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR:
                    go = True

            else:
                # 同期状態が再開か空白の場合を判定
                if row['SYNC_STATUS_ROW_ID'] == TD_SYNC_STATUS_NAME_DEFINE.STS_RESTART \
                or row['SYNC_STATUS_ROW_ID'] is None or len(row['SYNC_STATUS_ROW_ID']) == 0:
                    go = True

            if go is True:
                DelvFlg = 0
                if row['DEL_OPE_ID'] is not None and len(row['DEL_OPE_ID']) > 0 \
                and row['DEL_MOVE_ID'] is not None and len(row['DEL_MOVE_ID']) > 0:
                    DelvFlg = 1

                # 資材紐付を行う孫プロセス起動
                MatlLinkId = row['MATL_LINK_ROW_ID']
                g.appmsg.get_api_message("MSG-90055", [self.RepoId, MatlLinkId])
                grand_child_obj = CICD_GrandChildWorkflow(self.org_id, self.ws_id, self.DBobj, self.RepoId, MatlLinkId, DelvFlg)
                ret = grand_child_obj.main()
                if ret == 0:
                    FREE_LOG = g.appmsg.get_api_message("MSG-90060", [self.RepoId, MatlLinkId])
                    g.applogger.debug(FREE_LOG)

                else:
                    self.warning_flag = 1
                    logaddstr = ret
                    FREE_LOG = g.appmsg.get_api_message("MSG-90092", [self.RepoId, MatlLinkId, logaddstr])

        return True

    def main(self):

        SyncTimeUpdate_Flg = False
        RepoListSyncStatusUpdate_Flg = False
        CloneExeFlg = False
        MargeExeFlg = True

        try:
            try:
                self.LocalsetSshExtraArgs()

                # ローカルクローンディレクトリ有無判定
                ret = self.Gitobj.LocalCloneDirCheck()
                if ret is False:
                    CloneExeFlg = True

                # ローカルクローンのリモートリポジトリ(URL)が正しいか判定
                if CloneExeFlg is False:
                    FREE_LOG = g.appmsg.get_api_message("MSG-90053", [self.RepoId,])
                    g.applogger.debug(FREE_LOG)

                    ret = self.LocalCloneRemoteRepoChk()
                    if ret is False:
                        # リモートリポジトリ不一致
                        CloneExeFlg = True
                        FREE_LOG = g.appmsg.get_api_message("MSG-90057", [self.RepoId,])
                        g.applogger.debug(FREE_LOG)

                # ローカルクローンのブランチが正しいか判定
                if CloneExeFlg is False:
                    ret = self.LocalCloneBranchChk()
                    if ret is False:
                        # ブランチ不一致
                        CloneExeFlg = True
                        FREE_LOG = g.appmsg.get_api_message("MSG-90070", [self.RepoId,])
                        g.applogger.debug(FREE_LOG)

                # ローカルクローン作成
                if CloneExeFlg is True:
                    # ローカルクローン作成
                    ret = self.CreateLocalClone()

                    # Git ファイル一覧取得
                    ret, GitFiles = self.getLocalCloneFileList()

                    # rolesディレクトリ取得
                    RolesPath = self.getRolesPath(GitFiles)

                else:
                    # Git差分抽出(git pull)
                    ret, pullResultAry, UpdateFiles, MargeExeFlg = self.GitPull()
                    if MargeExeFlg is True or self.MatlListUpdateExeFlg is True:
                        # Git ファイル一覧取得
                        ret, GitFiles = self.getLocalCloneFileList()

                        # rolesディレクトリ取得
                        RolesPath = self.getRolesPath(GitFiles)

                #  資材管理更新
                if MargeExeFlg is True or self.MatlListUpdateExeFlg is True:
                    self.DBobj.db_transaction_start()

                    # 資材管理にGit ファイル情報を登録
                    FREE_LOG = g.appmsg.get_api_message("MSG-90065", [self.RepoId, ])
                    g.applogger.debug(FREE_LOG)

                    ret, MatlListRecodes = self.getMatlListRecodes()
                    ret, MatlListRecodes = self.MatlListMerge(MatlListRecodes, RolesPath, GitFiles)
                    ret = self.MatlListRolesRecodeUpdate()

                    # 資材一覧を更新したタイミングでコミット
                    ret = self.DBobj.db_transaction_end(True)
                    if ret is False:
                        # 異常フラグON
                        self.error_flag = 1

                        # トランザクション処理に失敗しました
                        logstr = g.appmsg.get_api_message("MSG-90076")
                        FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)

                        # UIに表示するメッセージ
                        self.UIDisplayMsg = g.appmsg.get_api_message("MSG-90109")

                        # 戻り値編集
                        retary = self.makeReturnArray(-1, FREE_LOG, self.UIDisplayMsg)
                        raise Exception(retary)

                    FREE_LOG = g.appmsg.get_api_message("MSG-90066", [self.RepoId, ])
                    g.applogger.debug(FREE_LOG)

            except CICDException as e:
                self.error_flag = 1
                self.UIDisplayMsg = e.ary['UImsg']
                logstr = g.appmsg.get_api_message("MSG-90080", [self.RepoId, ])
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, e.ary['log'])
                raise Exception(FREE_LOG)

            except Exception as e:
                self.error_flag = 1
                self.UIDisplayMsg = str(e)
                logstr = g.appmsg.get_api_message("MSG-90080", [self.RepoId, ])
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, e)
                raise Exception(FREE_LOG)

            # トランザクション再開
            if self.DBobj._db_con.open is True and self.DBobj._is_transaction is False:
                ret = self.DBobj.db_transaction_start()
                if ret is False:
                    # UIに表示するエラーメッセージ設定
                    self.setDefaultUIDisplayMsg()

                    # 異常フラグON
                    self.error_flag = 1

                    # トランザクション処理に失敗しました
                    logstr = g.appmsg.get_api_message("MSG-90076")
                    FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
                    raise Exception(FREE_LOG)

            # 同期状態テーブル 処理時間更新
            if RepoListSyncStatusUpdate_Flg is False:
                SyncStatus = TD_SYNC_STATUS_NAME_DEFINE.STS_NORMAL
                ret = self.UpdateRepoListSyncStatus(SyncStatus)
                if ret is not True:
                    self.error_flag = 1
                    self.setDefaultUIDisplayMsg()

                    # データベースの更新に失敗しました
                    logstr = g.appmsg.get_api_message("MSG-90079", [self.RepoId, ])
                    FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, ret)
                    raise Exception(FREE_LOG)

            ret = self.DBobj.db_transaction_end(True)
            if ret is False:
                # UIに表示するエラーメッセージ設定
                self.setDefaultUIDisplayMsg()

                # 異常フラグON
                self.error_flag = 1

                # トランザクション処理に失敗しました
                logstr = g.appmsg.get_api_message("MSG-90076")
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
                raise Exception(FREE_LOG)

            # commit後に同期状態テーブル 処理時間更新とリモートリポジトリ管理の状態を更新をマーク
            SyncTimeUpdate_Flg = True
            RepoListSyncStatusUpdate_Flg = True

            # 資材紐付管理に登録されている資材を展開
            self.DBobj.db_transaction_start()
            ret = self.MatlLinkExecute(MargeExeFlg)
            if ret is not True:
                self.error_flag = 1

                logstr = g.appmsg.get_api_message("MSG-90094")
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, ret)
                raise Exception(FREE_LOG)
            self.DBobj.db_transaction_end(True)

        except CICDException as e:
            self.DBobj.db_transaction_end(False)
            t = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))

        except Exception as e:
            self.DBobj.db_transaction_end(False)
            t = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))

        if RepoListSyncStatusUpdate_Flg is False:
            if len(self.UIDisplayMsg) <= 0:
                SyncStatus = TD_SYNC_STATUS_NAME_DEFINE.STS_NORMAL

            else:
                SyncStatus = TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR

            self.DBobj.db_transaction_start()
            ret = self.UpdateRepoListSyncStatus(SyncStatus)
            if ret is not True:
                # 異常フラグON
                self.error_flag = 1

                # データベースの更新に失敗しました
                logstr = g.appmsg.get_api_message("MSG-90079", [self.RepoId, ])
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, ret)
                g.applogger.info(FREE_LOG)

            self.DBobj.db_transaction_end(True)

        # 結果出力
        if self.error_flag != 0:
            FREE_LOG = g.appmsg.get_api_message("MSG-90051")
            g.applogger.debug(FREE_LOG)
            return 2

        elif self.warning_flag != 0:
            FREE_LOG = g.appmsg.get_api_message("MSG-90052")
            g.applogger.debug(FREE_LOG)
            return 2

        FREE_LOG = g.appmsg.get_api_message("MSG-90050")
        g.applogger.debug(FREE_LOG)

        return 0


################################################################
# 親
################################################################
def getTargetRepoListRow(DBobj):

    # リポジトリ管理抽出(廃止レコードではない、自動同期が有効、(同期状態が異常ではない or 同期実行状態が未実施))
    sql = (
        "SELECT "
        "  TAB_A.* "
        "FROM "
        "  T_CICD_REPOSITORY_LIST TAB_A "
        "WHERE "
        "  TAB_A.DISUSE_FLAG = '0' "
        "  AND TAB_A.AUTO_SYNC_FLG = %s "
        "  AND (TAB_A.SYNC_STATUS_ROW_ID <> %s OR TAB_A.SYNC_LAST_TIMESTAMP IS NULL) "
    )

    tgtRepoListRow = DBobj.sql_execute(sql, ['1', TD_SYNC_STATUS_NAME_DEFINE.STS_ERROR])

    return tgtRepoListRow


def backyard_main(organization_id, workspace_id):

    g.applogger.debug("backyard_main called")
    error_flag = 0
    if getattr(g, 'LANGUAGE', None) is None:
        g.LANGUAGE = 'en'

    if getattr(g, 'USER_ID', None) is None:
        g.USER_ID = '100101'

    try:
        DBobj = DBConnectWs()

        # リポジトリ管理から処理対象のリポジトリ取得
        tgtRepoListRow = getTargetRepoListRow(DBobj)
        for row in tgtRepoListRow:
            ExecuteTime = datetime.datetime.now()
            RepoId = row['REPO_ROW_ID']
            ExecMode = "Remake"
            if row['SYNC_STATUS_ROW_ID'] == TD_SYNC_STATUS_NAME_DEFINE.STS_NORMAL:
                ExecMode = "Normal"

            sync_last_timestamp = row['SYNC_LAST_TIMESTAMP']
            if sync_last_timestamp is None:
                sync_last_timestamp = datetime.datetime.fromtimestamp(0)

            if row['SYNC_INTERVAL'] is None or row['SYNC_INTERVAL'] == "":
                row['SYNC_INTERVAL'] = 60

            # 前回同期から指定秒を経過しているかチェック
            sync_interval = int(row['SYNC_INTERVAL'])
            if ExecuteTime >= sync_last_timestamp + datetime.timedelta(seconds=sync_interval):
                FREE_LOG = g.appmsg.get_api_message("MSG-90056", [RepoId, ])
                g.applogger.debug(FREE_LOG)

                child_obj = CICD_ChildWorkflow(organization_id, workspace_id, DBobj, RepoId, ExecMode, row)
                child_obj.main()

    except Exception as e:
        error_flag = 1
        raise Exception(e)

    # 結果出力
    FREE_LOG = ""
    if error_flag != 0:
        FREE_LOG = g.appmsg.get_api_message("MSG-90051")

    else:
        FREE_LOG = g.appmsg.get_api_message("MSG-90050")

    g.applogger.debug(FREE_LOG)

    g.applogger.debug("backyard_main end")
