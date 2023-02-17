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

from flask import g

from libs import driver_controll
from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs
from common_libs.common.encrypt import decrypt_str
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.terraform_driver.common.Const import Const as TFCommonConst
from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
from common_libs.terraform_driver.cli.Const import Const as TFCLIConst
from common_libs.ansible_driver.functions.rest_libs import insert_execution_list as a_insert_execution_list
from common_libs.terraform_driver.common.Execute import insert_execution_list as t_insert_execution_list
from common_libs.cicd.classes.cicd_definition import TD_SYNC_STATUS_NAME_DEFINE, TD_B_CICD_MATERIAL_FILE_TYPE_NAME, TD_B_CICD_MATERIAL_TYPE_NAME, TD_C_PATTERN_PER_ORCH, TD_B_CICD_GIT_PROTOCOL_TYPE_NAME, TD_B_CICD_GIT_REPOSITORY_TYPE_NAME, TD_B_CICD_MATERIAL_LINK_LIST
from common_libs.cicd.functions.local_functions import MatlLinkColumnValidator2, MatlLinkColumnValidator3, MatlLinkColumnValidator4, MatlLinkColumnValidator5


################################################################
# 共通処理
################################################################
def makeLogiFileOutputString(file, line, logstr1, logstr2):

    msg = '[FILE]:%s [LINE]:%s %s' % (file, line, logstr1)
    if logstr2:
        msg = '%s\n%s' % (msg, logstr2)

    return msg


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
        self.branch = RepoInfo['BRANCH_NAME'] if 'BRANCH_NAME' in RepoInfo['BRANCH_NAME'] else "__undefine_branch__"
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

        except Exception:
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

            if os.path.exists("/root/.gitconfig"):  # ToDo ファイルパス
                return_var = subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if return_var.returncode == 0:
                    if "core.sshcommand" in return_var.stdout:
                        reg_flg = True

                else:
                    logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1036", [cmd,])  # ToDo
                    logaddstr = '%s\n%s\nexit code:(%s)' % (' '.join(cmd), return_var.stdout, return_var.returncode)
                    FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
                    self.SetGitCommandLastErrorMsg('%s\n%s' % (logstr, logaddstr))
                    self.SetLastErrorMsg(FREE_LOG)
                    return False

            if reg_flg is False:
                cmd = "git config --global core.sshCommand 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'"
                return_var = subprocess.run(cmd, check=True, text=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if return_var.returncode != 0:
                    logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1036", [cmd,])  # ToDo
                    logaddstr = '%s\n%s\nexit code:(%s)' % (' '.join(cmd), return_var.stdout, return_var.returncode)
                    FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
                    self.SetGitCommandLastErrorMsg('%s\n%s' % (logstr, logaddstr))
                    self.SetLastErrorMsg(FREE_LOG)
                    return False

        except subprocess.CalledProcessError as e:
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1036", [cmd,])  # ToDo
            logaddstr = '%s\n%s\nexit code:(%s)' % (' '.join(cmd), e.stdout, e.returncode)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg('%s\n%s' % (logstr, logaddstr))
            self.SetLastErrorMsg(FREE_LOG)
            return False

        except Exception as e:
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1036", [cmd,])  # ToDo
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
            g.applogger.debug(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)

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
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1023")  # ToDo
            logaddstr = "%s\nexit code:(%s)" % (return_var.stdout if return_var else '', return_var.returncode if return_var else '')
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg(return_var.stdout if return_var else '')
            self.SetLastErrorMsg(FREE_LOG)
            return -1

        if cmd_ok is False:
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1022", [self.remortRepoUrl,])  # ToDo
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
                "%s/ky_GitCommand.sh" % (self.libPath),
                self.ProxyURL, Authtype, self.cloneRepoDir,
                "'remote show origin'",
                self.user, self.password, self.sshPassword, self.sshPassphrase,
                self.sshExtraArgsStr
            ]

            # Git コマンドが失敗した場合、指定時間Waitし指定回数リトライする
            for idx in range(self.retryCount):
                return_var = subprocess.run(cmd1, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if return_var.returncode == 0:
                    break

                logaddstr = "%s\nexit code:(%s)\nError retry with git command" % (return_var.stdout, return_var.returncode)
                g.applogger.debug(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)

                if self.retryCount - 1 > idx:
                    time.sleep(self.retryWaitTime)

            if return_var is None or return_var.returncode != 0:
                # Git remote show origin commandに失敗しました
                logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1024")  # ToDo
                logaddstr = "%s\nexit code:(%s)" % (return_var.stdout if return_var else '', return_var.returncode if return_var else '')
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
                self.SetGitCommandLastErrorMsg(return_var.stdout if return_var else '')
                self.SetLastErrorMsg(FREE_LOG)
                return -1

            else:
                output1 = return_var.stdout.split('\n')
                for op in output1:
                    ret = re.match('[\s]+HEAD[\s]branch', op)
                    if ret:
                        DefaultBranch = re.split('[\s]+HEAD[\s]branch', op)[1]
                        break

                    else:
                        ret = re.match('[\s]+HEAD[\s]branch[\s]\(remote HEAD is ambiguous, may be one of the following\):', op)
                        if ret:
                            return True

                        else:
                            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1024")  # ToDo
                            logaddstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1032")  # ToDo
                            logaddstr = '%s\n%s\nexit code:(%s)' % (logaddstr, op, return_var.returncode)
                            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
                            self.SetGitCommandLastErrorMsg(logaddstr)
                            self.SetLastErrorMsg(FREE_LOG)
                            return -1

        # カレントブランチ確認
        return_var = None
        CurrentBranch = ""
        cmd2 = ["git", self.gitOption, "branch"]

        # Git コマンドが失敗した場合、指定時間Waitし指定回数リトライする
        for idx in range(self.retryCount):
            return_var = subprocess.run(cmd2, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if return_var.returncode == 0:
                break

            logaddstr = "%s\nexit code:(%s)\nError retry with git command" % (return_var.stdout, return_var.returncode)
            g.applogger.debug(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)

            if self.retryCount - 1 > idx:
                time.sleep(self.retryWaitTime)

        if return_var is None or return_var.returncode != 0:
            # Git remote show origin commandに失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1024")  # ToDo
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
                CurrentBranch = return_var.stdout[2:]

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
                "%s/ky_GitClone.sh" % (self.libPath),
                self.ProxyURL,
                self.remortRepoUrl, self.cloneRepoDir, self.branch,
                self.user, self.password, self.sshPassword, self.sshPassphrase,
                self.sshExtraArgsStr
            ]

            self.ClearGitCommandLastErrorMsg()
            return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if return_var.returncode == 0:
                comd_ok = True
                break

            else:
                output = return_var.stdout
                return_code = return_var.returncode
                logaddstr = "%s\nexit code:(%s)\nError retry with git command" % (output, return_code)
                g.applogger.debug(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)

                # リトライ中のログは表示しない
                if self.retryCount - 1 > idx:
                    time.sleep(self.retryWaitTime)

        if comd_ok is False:
            # clone失敗時はローカルディレクトリを削除
            cmd = ["/bin/rm", "-rf", self.cloneRepoDir]
            return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            # Git clone commandに失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1021")  # ToDo
            logaddstr = "%s\nexit code:(%s)" % (output, return_code)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg(output)
            self.SetLastErrorMsg(FREE_LOG)
            return False

        # 日本語文字化け対応
        return_var = None
        cmd = ["git", self.gitOption, "config", "--local", "core.quotepath", "false"]
        return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if return_var.returncode != 0:
            # Git config の設定に失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1020")  # ToDo
            logaddstr = "%s\nexit code:(%s)" % (return_var.stdout, return_var.returncode)
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)
            self.SetGitCommandLastErrorMsg(return_var.stdout)
            self.SetLastErrorMsg(FREE_LOG)
            return False

        return True

    def GitLsFiles(self):

        ret_val = []

        # Git コマンドが失敗した場合、指定時間Waitし指定回数リトライする
        cmd = ["git", "ls-files"]
        for idx in range(self.retryCount):
            return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if return_var.returncode == 0:
                break

            logaddstr = "%s\nexit code:(%s)\nError retry with git command" % (return_var.stdout, return_var.returncode)
            g.applogger.debug(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)

            if self.retryCount - 1 > idx:
                time.sleep(self.retryWaitTime)

        if return_var.returncode == 0:
            ret_val = return_var.stdout.split('\n')

        else:
            # Git ls-files commandに失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1026")  # ToDo
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
        for idx in self.retryCount:
            return_var = None
            cmd = [
                "%s/ky_GitCommand.sh" % (self.libPath),
                self.ProxyURL,
                Authtype,
                self.cloneRepoDir,
                "pull", "--rebase", "--ff",
                self.user, self.password, self.sshPassword, self.sshPassphrase,
                self.sshExtraArgsStr
            ]
            return_var = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if return_var.returncode != 0:
                logaddstr = "%s\nexit code:(%s)\nError retry with git command" % (return_var.stdout, return_var.returncode)
                g.applogger.debug(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logaddstr)

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
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1030")  # ToDo
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
        self.DelvExecFlg = DelvFlg

        self.cloneRepoDir = '/storage/%s/%s/driver/cicd/repositories/%s' % (org_id, ws_id, RepoId)

        self.error_flag = 0

        self.UIDelvExecInsNo = ""
        self.UIDelvExecMenuId = ""
        self.UIMatlUpdateStatusID = ""
        self.UIMatlUpdateStatusDisplayMsg = ""
        self.UIDelvStatusDisplayMsg = ""

        self.ansible_driver = True
        self.terraform_driver = True

    def setUIMatlSyncStatus(self, UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId):

        self.UIMatlUpdateStatusDisplayMsg = UIMatlSyncMsg
        if UIDelvMsg == "def":
            if self.DelvExecFlg is True:
                self.UIDelvStatusDisplayMsg = g.appmsg.get_api_message("ITACICDFORIAC-ERR-4001")  # ToDo

            else:
                self.UIDelvStatusDisplayMsg = ""

        else:
            self.UIDelvStatusDisplayMsg = UIDelvMsg

        self.UIMatlUpdateStatusID = SyncSts
        self.UIDelvExecInsNo = DelvExecInsNo
        self.UIDelvExecMenuId = DelvExecMenuId

    def CreateZipFile(self, inRolesDir, outRolesDir, zipFileName):

        outRolesDir = "/storage/%s/%s/tmp/driver/cicd/zipdir_%s" % (self.org_id, self.ws_id, self.RepoId)

        subprocess.run(["/bin/rm", "-rf", outRolesDir], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.run(["/bin/mkdir", "-p", outRolesDir], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        inRolesDir = re.sub(r'/roles$', '', inRolesDir)
        zipFileName = "%s.zip" % (os.path.basename(inRolesDir))

        cmd = "cd %s;zip -r %s/%s *" % (inRolesDir, outRolesDir, zipFileName)
        ret = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if ret.returncode != 0:
            ret = ret.stdout
            return ret, outRolesDir, zipFileName

        return True, outRolesDir, zipFileName

    def getTargetMatlLinkRow(self, tgtMatlLinkRow):

        # 資材紐付管理取得
        sql = (
            "SELECT "
            "  T1.*, "
            #"  T0.HOSTNAME  M_HOSTNAME, "
            #"  T0.PROTOCOL  M_PROTOCOL, "
            #"  T0.PORT      M_PORT, "
            "  T3.MATL_FILE_PATH         M_MATL_FILE_PATH, "
            "  T3.MATL_FILE_TYPE_ROW_ID  M_MATL_FILE_TYPE_ROW_ID, "
            #"  T4.USER_ID   M_REST_USER_ID, "
            #"  T4.LOGIN_PW  M_REST_LOGIN_PW, "
            "  T8.ITA_EXT_STM_ID    M_ITA_EXT_STM_ID, "
            #"  T9.USERNAME          M_REST_USERNAME, "
            #"  T9.USERNAME_JP       M_USERNAME_JP, "
            "  T6.OS_TYPE_ID        M_OS_TYPE_ID, "
            "  T6.OS_TYPE_NAME      M_OS_TYPE_NAME, "
            "  T6.DISUSE_FLAG       OS_DISUSE_FLAG, "
            "  T5.DIALOG_TYPE_ID    M_DIALOG_TYPE_ID, "
            "  T5.DIALOG_TYPE_NAME  M_DIALOG_TYPE_NAME, "
            "  T5.DISUSE_FLAG       DALG_DISUSE_FLAG, "
            "  T2.DISUSE_FLAG       REPO_DISUSE_FLAG, "
            "  T3.DISUSE_FLAG       MATL_DISUSE_FLAG, "
            #"  T4.DISUSE_FLAG       RACCT_DISUSE_FLAG, "
            "  T7.DISUSE_FLAG       OPE_DISUSE_FLAG, "
            "  T8.DISUSE_FLAG       PTN_DISUSE_FLAG "
            #"  T9.DISUSE_FLAG       ACT_DISUSE_FLAG "
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

    def materialsRestAccess(self, materialType, filename, base64file):

        editType = ""
        restExecFlg = False

        table_info = {
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_LEGACY     : {'tn':'T_ANSL_MATL_COLL', 'tk':'PLAYBOOK_MATTER_ID'},
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_PIONEER    : {'tn':'T_ANSP_MATL_COLL', 'tk':'DIALOG_MATTER_ID'},
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_ROLE       : {'tn':'T_ANSR_MATL_COLL', 'tk':'ROLE_PACKAGE_ID'},
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_CONTENT    : {'tn':'T_ANSC_CONTENTS_FILE', 'tk':'CONTENTS_FILE_ID'},
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_TEMPLATE   : {'tn':'T_ANSC_TEMPLATE_FILE', 'tk':'ANS_TEMPLATE_ID'},
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE     : {'tn':'', 'tk':''},  # ToDo
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_POLICY     : {'tn':'', 'tk':''},  # ToDo
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE_CLI : {'tn':'', 'tk':''},  # ToDo
        }

        table_name = table_info[materialType]['tn']
        tgtkey = table_info[materialType]['tk']

        sql = (
            "SELECT * FROM %s WHERE %s=%%s "
        ) % (table_name, tgtkey)
        arrayBind = [filename, ]

        objQuery = self.DBobj.sql_execute(sql, arrayBind)
        RecordLength = len(objQuery)
        if RecordLength == 0:
            editType = g.appmsg.get_api_message("ITAWDCH-STD-12202")  # ToDo

        elif RecordLength > 0:
            editType = g.appmsg.get_api_message("ITAWDCH-STD-12203")  # ToDo

            targetNum = -1
            recentNum = -1
            recent_dt = None

            # 廃止されていないデータを更新対象とする
            for i, tmpval in enumerate(objQuery):
                if tmpval['DISUSE_FLAG'] == '0':
                    targetNum = i

                elif recent_dt is None or recent_dt < tmpval['LAST_UPDATE_TIMESTAMP']:
                    recentNum = i
                    recent_dt = tmpval['LAST_UPDATE_TIMESTAMP']

            # 全て廃止されている場合は最新のデータを更新対象とする
            if targetNum < 0:
                targetNum = recentNum
                restExecFlg = True

            # ファイル差分チェック

        if restExecFlg:
            pass

    def executeMovement(self, run_mode):

        useed = True
        # 予約日時のフォーマットチェック
        # yyyy/mm/dd hh:mmをyyyy/mm/dd hh:mm:ssにしている
        schedule_date = driver_controll.scheduled_format_check(parameter, useed)

        Required = True
        # Movementチェック
        movement_row = driver_controll.movement_registr_check(self.DBobj, parameter, Required)

        # オペレーションチェック
        operation_row = driver_controll.operation_registr_check(self.DBobj, parameter, Required)

        target = {'execution_ansible_legacy': AnscConst.DF_LEGACY_DRIVER_ID,
                  'execution_ansible_pioneer': AnscConst.DF_PIONEER_DRIVER_ID,
                  'execution_ansible_role': AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
                  TFCloudEPConst.RN_EXECTION: TFCommonConst.DRIVER_TERRAFORM_CLOUD_EP,
                  TFCLIConst.RN_EXECTION: TFCommonConst.DRIVER_TERRAFORM_CLI}

        # トランザクション開始
        self.DBobj.db_transaction_start()

        # 作業管理に登録
        conductor_id = None
        conductor_name = None
        run_mode = "3"
        if 'ansible' in menu:
            # Ansible用 作業実行登録
            result = a_insert_execution_list(self.DBobj, run_mode, target[menu], operation_row, movement_row, schedule_date, conductor_id, conductor_name)

        else:
            # Terraform用 作業実行登録
            result = t_insert_execution_list(self.DBobj, run_mode, target[menu], operation_row, movement_row, schedule_date, conductor_id, conductor_name)

        # コミット・トランザクション終了
        self.DBobj.db_transaction_end(True)

    def MailLinkExecute(self):

        # 資材紐付管理より対象レコード取得
        tgtMatlLinkRow = []
        ret, tgtMatlLinkRow = self.getTargetMatlLinkRow(tgtMatlLinkRow)
        if ret is not True:
            # 異常フラグON
            self.error_flag = 1

            LogStr = ""
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, ret)

            # 想定外のエラー
            UIMatlSyncMsg = g.appmsg.get_api_message("ITACICDFORIAC-ERR-4000")  # ToDo
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.ERROR()
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        # 処理対象か判定
        if len(tgtMatlLinkRow) == 0:
            # 異常フラグON
            self.error_flag = 1

            # 資材紐付管理の対象レコードが見つかりません。資材紐付処理をスキップします
            LogStr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-2040", [self.RepoId, self.MatlLinkId])  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, "")
            UIMatlSyncMsg = LogStr
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.ERROR()
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        else:
            row =tgtMatlLinkRow[0]

            # 廃止レコードか判定
            if row['DISUSE_FLAG'] == '1':
                return True

            # 自動同期が無効か判定
            elif row['AUTO_SYNC_FLG'] == TD_B_CICD_MATERIAL_LINK_LIST.C_AUTO_SYNC_FLG_OFF:
                return True

        # 資材紐付管理 紐付先資材タイプとインストール状態をチェック
        LogStr = ""
        ret, LogStr = MatlLinkColumnValidator4(self.RepoId, self.MatlLinkId, row['MATL_TYPE_ROW_ID'], LogStr, self.ansible_driver, self.terraform_driver)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, "")
            UIMatlSyncMsg = LogStr
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.ERROR()
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        # 紐付先資材タイプと資材パスの組み合わせチェック
        LogStr = ""
        ret = MatlLinkColumnValidator2(row['MATL_TYPE_ROW_ID'], row['M_MATL_FILE_TYPE_ROW_ID'], self.RepoId, self.MatlLinkId, LogStr)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, "")
            UIMatlSyncMsg = LogStr
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.ERROR()
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        # 紐付先資材タイプとMovemnetの組み合わせチェック
        LogStr = ""
        ret = MatlLinkColumnValidator5(self.RepoId, self.MatlLinkId, row['M_ITA_EXT_STM_ID'], row['MATL_TYPE_ROW_ID'], LogStr)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, "")
            UIMatlSyncMsg = LogStr
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.ERROR()
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        # 対象レコードのリレーション先確認
        LogStr = ""
        ret = MatlLinkColumnValidator3(row, LogStr)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, "")
            UIMatlSyncMsg = LogStr
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.ERROR()
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
            LogStr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-2043", [self.RepoId, self.MatlLinkId, tgtFileName])  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, "")

            UIMatlSyncMsg = g.appmsg.get_api_message("ITACICDFORIAC-ERR-4000")
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.ERROR()
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

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
                LogStr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-2043", [self.RepoId, self.MatlLinkId, tgtFileName])  # ToDo
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, LogStr, ret)

                UIMatlSyncMsg = g.appmsg.get_api_message("ITACICDFORIAC-ERR-4000")
                UIDelvMsg = "def"
                SyncSts = TD_SYNC_STATUS_NAME_DEFINE.ERROR()
                DelvExecInsNo = ""
                DelvExecMenuId = ""
                self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
                return FREE_LOG

            tgtFileName = "%s/%s" % (outRolesDir, zipFileName)

        tgtFileData = ""
        with open(tgtFileName) as fp:
            tgtFileData = fp.read()

        tgtFileBase64enc = base64.b64encode(tgtFileData)

        subprocess.run(["/bin/rm", "-rf", outRolesDir], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # 資材更新
        ret = self.materialsRestAccess(row['MATL_TYPE_ROW_ID'], row['MATL_LINK_NAME'], tgtFileBase64enc)
        if ret is not True:
            # 異常フラグON
            self.error_flag = 1

            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, ret)
            UIMatlSyncMsg = ret
            UIDelvMsg = "def"
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.ERROR()
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return FREE_LOG

        if DelvExecFlg is False:
            UIMatlSyncMsg = ""
            UIDelvMsg = ""
            SyncSts = TD_SYNC_STATUS_NAME_DEFINE.NORMAL()
            DelvExecInsNo = ""
            DelvExecMenuId = ""
            self.setUIMatlSyncStatus(UIMatlSyncMsg, UIDelvMsg, SyncSts, DelvExecInsNo, DelvExecMenuId)
            return True

        # Movement実行
        ret = self.executeMovement(row['DEL_EXEC_TYPE'])

    def main(self):

        ret = self.MailLinkExecute()

        return 0

################################################################
# リポジトリ同期処理クラス
################################################################
class CICD_ChildWorkflow():

    def __init__(self, org_id, ws_id, DBobj, RepoId, ExecMode, RepoListRow):

        self.error_flag = 0
        self.UIDisplayMsg = ""

        self.org_id = org_id
        self.ws_id = ws_id
        self.DBobj = DBobj
        self.config = configparser.ConfigParser()

        self.RepoId = RepoId
        self.ExecMode = ExecMode
        self.RepoListRow = RepoListRow

        self.MatlListUpdateExeFlg = True
        if ExecMode == "Normal":
            self.MatlListUpdateExeFlg = False

        if RepoListRow['SYNC_STATUS_ROW_ID'] is None or RepoListRow['SYNC_STATUS_ROW_ID'] == TD_SYNC_STATUS_NAME_DEFINE.RESTART():
            self.MatlListUpdateExeFlg = True

        self.cloneRepoDir = '/storage/%s/%s/driver/cicd/repositories/%s' % (org_id, ws_id, RepoId)
        libPath = '/exastro/backyard'
        GitCmdRsltParsStrFileNamePath = '/exastro/backyard/gitCommandResultParsingStringDefinition.ini'
        GitCmdRsltParsAry = self.config.read(GitCmdRsltParsStrFileNamePath)
        self.Gitobj = ControlGit(RepoId, RepoListRow, self.cloneRepoDir, libPath, GitCmdRsltParsAry)

    def setDefaultUIDisplayMsg(self):

        self.UIDisplayMsg = g.appmsg.get_api_message("ITACICDFORIAC-ERR-4000")  # ToDo

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
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1033")  # ToDo
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            self.UIDisplayMsg = '%s\n%s' % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            retary = self.makeReturnArray(False, FREE_LOG, self.UIDisplayMsg)
            raise Exception(retary)

        return True

    def LocalCloneRemoteRepoChk(self):

        ret = self.Gitobj.GitRemoteChk()
        if ret == -1:
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1023")  # ToDo
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            self.UIDisplayMsg = '%s\n%s' % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            retary = self.makeReturnArray(False, FREE_LOG, self.UIDisplayMsg)
            raise Exception(retary)

        return ret

    def LocalCloneBranchChk(self):

        # 認証方式の判定
        AuthTypeName = self.getAuthType()

        # ローカルクローンのブランチ確認
        ret = self.Gitobj.GitBranchChk(AuthTypeName)
        if ret == -1:
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1024")  # ToDo
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
                logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1005")  # ToDo
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
                return False

        return True

    def MatlListRecodeDisuse(self):

        # 資材一覧のレコードを全て廃止
        ret = self.MatlListRecodeDisuseUpdate()

        # トランザクションをコミット・ロールバック
        if ret is True:
            ret = self.DBobj.db_commit()
            if ret is False:
                # Clone異常時の処理なのでログを出力してReturn
                logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1003")  # ToDo
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
                return False

        else:
            ret = self.DBobj.db_rollback()
            if ret is False:
                # Clone異常時の処理なのでログを出力してReturn
                logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1003")  # ToDo
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
                return False

        return True

    def CreateLocalClone(self):

        ret = self.Gitobj.LocalCloneDirClean()
        if ret is False:
            # 該当のリモートリポジトリに紐づいている資材を資材一覧から廃止
            self.MatlListRecodeDisuse()

            # 異常フラグON
            self.error_flag = 1

            # ローカルクローンディレクトリの作成に失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1006", [self.cloneRepoDir, ])  # ToDo
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            # UIに表示するメッセージ
            self.UIDisplayMsg = "%s\n%s" % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            # 戻り値編集
            retary = self.makeReturnArray(False, FREE_LOG, self.UIDisplayMsg)
            raise Exception(retary)

        FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2016", [self.RepoId, ])  # ToDo
        g.applogger.debug(FREE_LOG)

        # 認証方式か判定
        AuthTypeName = self.getAuthType(self.RepoListRow)
        ret = self.Gitobj.GitClone(AuthTypeName)
        if ret is False:
            # 該当のリモートリポジトリに紐づいている資材を資材一覧から廃止
            self.MatlListRecodeDisuse()

            # 異常フラグON
            self.error_flag = 1

            # Git clone commandに失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1019")  # ToDo
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            # UIに表示するメッセージ
            self.UIDisplayMsg = "%s\n%s" % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            # 戻り値編集
            retary = self.makeReturnArray(False, FREE_LOG, self.UIDisplayMsg)
            raise Exception(retary)

        FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2018", [self.RepoId, ])  # ToDo
        g.applogger.debug(FREE_LOG)

        return True

    def getLocalCloneFileList(self):

        ret, GitFiles = self.Gitobj.GitLsFiles()
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            # Git ls-files commandに失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1026")  # ToDo
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            # UIに表示するメッセージ
            self.UIDisplayMsg = "%s\n%s" % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            # 戻り値編集
            retary = self.makeReturnArray(False, FREE_LOG, self.UIDisplayMsg)
            raise Exception(retary)

        return True

    def getRolesPath(self, GitFiles):

        RolesPath = {}
        for FilePath in GitFiles:
            FilePath = "/\n" % (FilePath)
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

        FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2009", [self.RepoId, ])  # ToDo
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
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1030")  # ToDo
            logaddstr = self.Gitobj.GetLastErrorMsg()
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, logaddstr)

            # UIに表示するメッセージ
            self.UIDisplayMsg = "%s\n%s" % (logstr, self.Gitobj.GetGitCommandLastErrorMsg())

            # 戻り値編集
            retary = self.makeReturnArray(-1, FREE_LOG, self.UIDisplayMsg)
            raise Exception(retary)

        FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2023", [self.RepoId, UpdateFlg])  # ToDo
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
            MatlListRecodes[row['MATL_FILE_TYPE_ROW_ID']][row['MATL_FILE_PATH']]

        return True, MatlListRecodes

    def MatlListDisuseUpdate(self, row, Disuse):

        table_name = "T_CICD_MATL_LIST"
        cols = self.DBobj.table_columns_get(table_name)
        cols = (',').join(cols[0])
        sql = (
            "SELECT %s "
            "FROM %s "
            "WHERE MATL_ROW_ID=%%s "
            "AND DISUSE_FLAG='0' "
        ) % (cols, table_name)
        arrayBind = [row['MATL_ROW_ID'], ]

        objQuery = self.DBobj.sql_execute(sql, arrayBind)
        row = objQuery[0]
        row["DISUSE_FLAG"] = Disuse
        ret = self.DBobj.table_update(table_name, row, 'MATL_ROW_ID', is_register_history=False)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            # データベースのアクセスに失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1005")  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)

            # UIに表示するメッセージ
            self.UIDisplayMsg = g.appmsg.get_api_message("ITACICDFORIAC-ERR-4000")  # ToDo

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
            # 異常フラグON
            self.error_flag = 1

            # データベースのアクセスに失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1005")  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)

            # UIに表示するメッセージ
            self.UIDisplayMsg = g.appmsg.get_api_message("ITACICDFORIAC-ERR-4000")  # ToDo

            # 戻り値編集
            retary = self.makeReturnArray(-1, FREE_LOG, self.UIDisplayMsg)
            raise Exception(retary)

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
                MatlListRecodes[FileType][path]['MATL_ROW_ID'] = 0
                MatlListRecodes[FileType][path]['REPO_ROW_ID'] = self.RepoId
                MatlListRecodes[FileType][path]['MATL_FILE_PATH'] = path
                MatlListRecodes[FileType][path]['MATL_FILE_TYPE_ROW_ID'] = FileType
                MatlListRecodes[FileType][path]['RECODE_ACCTION'] = 'Insert'

        # ファイルの増減確認
        for path in GitFiles:
            FileType = TD_B_CICD_MATERIAL_FILE_TYPE_NAME.C_MATL_FILE_TYPE_ROW_ID_FILE
            if FileType in MatlListRecodes and path in MatlListRecodes[FileType] and MatlListRecodes[FileType][path] is not None:
                # 廃止確認
                if MatlListRecodes[FileType][path]['DISUSE_FLAG'] == '0':
                    del MatlListRecodes[FileType][path]

                else:
                    MatlListRecodes[FileType][path]['RECODE_ACCTION'] = 'use'
                    MatlListRecodes[FileType][path]['DISUSE_FLAG'] = '0'

            else:
                # レコードの項目値設定
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
                    FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2022", [path,])  # ToDo
                    g.applogger.debug(FREE_LOG)

                # 資材管理にレコード追加
                elif row['RECODE_ACCTION'] == 'Insert':
                    del row['RECODE_ACCTION']
                    ret = self.MatlListInsert(row)
                    FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2020", [path,])  # ToDo
                    g.applogger.debug(FREE_LOG)


                # 資材管理のレコード復活
                elif row['RECODE_ACCTION'] == 'use':
                    del row['RECODE_ACCTION']
                    ret = self.MatlListDisuseUpdate(row, '0')
                    FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2021", [path,])  # ToDo
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
                    logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1005")  # ToDo
                    FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)

                    # UIに表示するメッセージ
                    self.UIDisplayMsg = g.appmsg.get_api_message("ITACICDFORIAC-ERR-4000")  # ToDo

                    # 戻り値編集
                    retary = self.makeReturnArray(-1, FREE_LOG, self.UIDisplayMsg)
                    raise Exception(retary)

                if Acction == "use":
                    FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2021", [row['MATL_FILE_PATH'], ])  # ToDo
                    g.applogger.debug(FREE_LOG)

                else:
                    FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2022", [row['MATL_FILE_PATH'], ])  # ToDo
                    g.applogger.debug(FREE_LOG)

        return True

    def UpdateSyncStatusRecode(self):

        sql = (
            "UPDATE T_CICD_SYNC_STATUS "
            "SET SYNC_LAST_TIMESTAMP = %s "
            "WHERE ROW_ID = %s "
        )
        arrayBind = [self.RepoId, datetime.datetime.now()]
        self.DBobj.sql_execute(sql, arrayBind)

        FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2026", [self.RepoId, ])  # ToDo
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
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1005")  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
            return FREE_LOG

        row = objQuery[0]
        Update = False
        for column, value in UpdateColumnAry.items():
            # 更新が必要か判定
            if row[column] != value:
                row[column] = value
                Update = True

        if Update is False:
            FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2028", [self.RepoId, ])  # ToDo
            g.applogger.debug(FREE_LOG)

            return True

        ret = self.DBobj.table_update(table_name, row, "REPO_ROW_ID", is_register_history=True)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            # データベースのアクセスに失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1005")  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)

            return FREE_LOG

        FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2027", [self.RepoId, ])  # ToDo
        g.applogger.debug(FREE_LOG)

        return True

    def UpdateRepoListSyncStatus(self, SyncStatus):

        UpdateColumnAry = {}
        UpdateColumnAry['REPO_ROW_ID'] = self.RepoId
        UpdateColumnAry['SYNC_STATUS_ROW_ID'] = SyncStatus
        if SyncStatus == TD_SYNC_STATUS_NAME_DEFINE.NORMAL():
            UpdateColumnAry['SYNC_ERROR_NOTE'] = ""

        else:
            UpdateColumnAry['SYNC_ERROR_NOTE'] = self.UIDisplayMsg

        ret = self.UpdateRepoListRecode(UpdateColumnAry)

        return ret

    def getTargetMatlLinkRow(self, tgtMatlLinkRow):

        # ToDo
        # ansible/terraformのリリースファイル有無確認(インストール状態確認)
        ansible_driver = True
        terraform_driver = True

        # 資材紐付管理取得
        sql = (
            "SELECT "
            "  T1.*, "
            #"  T0.HOSTNAME  M_HOSTNAME, "
            #"  T0.PROTOCOL  M_PROTOCOL, "
            #"  T0.PORT      M_PORT, "
            "  T3.MATL_FILE_PATH         M_MATL_FILE_PATH, "
            "  T3.MATL_FILE_TYPE_ROW_ID  M_MATL_FILE_TYPE_ROW_ID, "
            #"  T4.USER_ID   M_REST_USER_ID, "
            #"  T4.LOGIN_PW  M_REST_LOGIN_PW, "
            "  T8.ITA_EXT_STM_ID    M_ITA_EXT_STM_ID, "
            #"  T9.USERNAME          M_REST_USERNAME, "
            #"  T9.USERNAME_JP       M_USERNAME_JP, "
            "  T6.OS_TYPE_ID        M_OS_TYPE_ID, "
            "  T6.OS_TYPE_NAME      M_OS_TYPE_NAME, "
            "  T6.DISUSE_FLAG       OS_DISUSE_FLAG, "
            "  T5.DIALOG_TYPE_ID    M_DIALOG_TYPE_ID, "
            "  T5.DIALOG_TYPE_NAME  M_DIALOG_TYPE_NAME, "
            "  T5.DISUSE_FLAG       DALG_DISUSE_FLAG, "
            "  T2.DISUSE_FLAG       REPO_DISUSE_FLAG, "
            "  T3.DISUSE_FLAG       MATL_DISUSE_FLAG, "
            #"  T4.DISUSE_FLAG       RACCT_DISUSE_FLAG, "
            "  T7.DISUSE_FLAG       OPE_DISUSE_FLAG, "
            "  T8.DISUSE_FLAG       PTN_DISUSE_FLAG "
            #"  T9.DISUSE_FLAG       ACT_DISUSE_FLAG "
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
            # 異常フラグON
            self.error_flag = 1

            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-2002")  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
            return FREE_LOG

        for row in tgtMatlLinkRow:
            go = False
            if MargeExeFlg is True or self.MatlListUpdateExeFlg is True:
                # 同期状態が異常以外の場合を判定
                if row['SYNC_STATUS_ROW_ID'] != TD_SYNC_STATUS_NAME_DEFINE.ERROR():
                    go = True

            else:
                # 同期状態が再開か空白の場合を判定
                if row['SYNC_STATUS_ROW_ID'] == TD_SYNC_STATUS_NAME_DEFINE.RESTART() \
                or row['SYNC_STATUS_ROW_ID'] is None or len(row['SYNC_STATUS_ROW_ID']) == 0:
                    go = True

            if go is True:
                DelvFlg = 0
                if row['DEL_OPE_ID'] is not None and len(row['DEL_OPE_ID']) > 0 \
                and row['DEL_MOVE_ID'] is not None and len(row['DEL_MOVE_ID']) > 0:
                    DelvFlg = 1

                # 資材紐付を行う孫プロセス起動
                MatlLinkId = row['MATL_LINK_ROW_ID']
                g.appmsg.get_api_message("ITACICDFORIAC-STD-2010", [self.RepoId, MatlLinkId])  # ToDo
                grand_child_obj = CICD_GrandChildWorkflow(self.org_id, self.ws_id, self.DBobj, self.RepoId, MatlLinkId, DelvFlg)
                grand_child_obj.main()

        return True

    def main(self):

        SyncTimeUpdate_Flg = False
        RepoListSyncStatusUpdate_Flg = False

        self.LocalsetSshExtraArgs()

        # ローカルクローンディレクトリ有無判定
        CloneExeFlg = False
        ret = self.Gitobj.LocalCloneDirCheck()
        if ret is False:
            CloneExeFlg = True

        if CloneExeFlg is False:
            FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2007", [self.RepoId,])  # ToDo
            g.applogger.debug(FREE_LOG)

            # ローカルクローンのリモートリポジトリ(URL)が正しいか判定
            ret = self.LocalCloneRemoteRepoChk(self.RepoId)
            if ret is False:
                # リモートリポジトリ不一致
                CloneExeFlg = True
                FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2014", [self.RepoId,])  # ToDo
                g.applogger.debug(FREE_LOG)

        # ローカルクローンのブランチが正しいか判定
        if CloneExeFlg is False:
            ret = self.LocalCloneBranchChk()
            if ret is False:
                # ブランチ不一致
                CloneExeFlg = True
                FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2029", [self.RepoId,])  # ToDo
                g.applogger.debug(FREE_LOG)

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
            # 資材管理にGit ファイル情報を登録
            FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2024", [self.RepoId, ])  # ToDo
            g.applogger.debug(FREE_LOG)

            ret, MatlListRecodes = self.getMatlListRecodes()
            ret, MatlListRecodes = self.MatlListMerge(MatlListRecodes, RolesPath, GitFiles)
            ret = self.MatlListRolesRecodeUpdate()

            # 資材一覧を更新したタイミングでコミット
            ret = self.DBobj.db_commit()
            if ret is False:
                # 異常フラグON
                self.error_flag = 1

                # トランザクション処理に失敗しました
                logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1003")  # ToDo
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)

                # UIに表示するメッセージ
                self.UIDisplayMsg = g.appmsg.get_api_message("ITACICDFORIAC-ERR-4000")  # ToDo

                # 戻り値編集
                retary = self.makeReturnArray(-1, FREE_LOG, self.UIDisplayMsg)
                raise Exception(retary)

            FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2025", [self.RepoId, ])  # ToDo
            g.applogger.debug(FREE_LOG)

        # トランザクション再開
        ret = self.DBobj.db_transaction_end(True)
        if ret is False:
            # UIに表示するエラーメッセージ設定
            self.setDefaultUIDisplayMsg()

            # 異常フラグON
            self.error_flag = 1

            # トランザクション処理に失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1003")  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
            raise Exception(FREE_LOG)

        ret = self.DBobj.db_transaction_start()
        if ret is False:
            # UIに表示するエラーメッセージ設定
            self.setDefaultUIDisplayMsg()

            # 異常フラグON
            self.error_flag = 1

            # トランザクション処理に失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1003")  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
            raise Exception(FREE_LOG)

        # 同期状態テーブル 処理時間更新
        if SyncTimeUpdate_Flg is False:
            ret = self.UpdateSyncStatusRecode()
            if ret is False:
                # 異常フラグON
                self.error_flag = 1

                # UIに表示するエラーメッセージ設定
                self.setDefaultUIDisplayMsg()

                # データベースの更新に失敗しました
                logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1007", [self.RepoId, ])  # ToDo
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, ret)
                raise Exception(FREE_LOG)

        if RepoListSyncStatusUpdate_Flg is False:
            SyncStatus = TD_SYNC_STATUS_NAME_DEFINE.NORMAL()
            ret = self.UpdateRepoListSyncStatus(SyncStatus)
            if ret is not True:
                # 異常フラグON
                self.error_flag = 1

                # UIに表示するエラーメッセージ設定
                self.setDefaultUIDisplayMsg()

                # データベースの更新に失敗しました
                logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1007", [self.RepoId, ])  # ToDo
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, ret)
                raise Exception(FREE_LOG)

        ret = self.DBobj.db_commit()
        if ret is False:
            # UIに表示するエラーメッセージ設定
            self.setDefaultUIDisplayMsg()

            # 異常フラグON
            self.error_flag = 1

            # トランザクション処理に失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1003")  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
            raise Exception(FREE_LOG)

        # commit後に同期状態テーブル 処理時間更新とリモートリポジトリ管理の状態を更新をマーク
        SyncTimeUpdate_Flg = True
        RepoListSyncStatusUpdate_Flg = True

        self.DBobj.db_transaction_end(True)
        ret = self.DBobj.db_transaction_start()
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            # トランザクション処理に失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1003")  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
            raise Exception(FREE_LOG)

        # 資材紐付管理に登録されている資材を展開
        ret = self.MatlLinkExecute(MargeExeFlg)
        if ret is not True:
            # 異常フラグON
            self.error_flag = 1

            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-2003")  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, ret)
            raise Exception(FREE_LOG)

        # トランザクションを終了
        ret = self.DBobj.db_transaction_end(True)
        if ret is False:
            # 異常フラグON
            self.error_flag = 1

            # トランザクション処理に失敗しました
            logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1003")  # ToDo
            FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr)
            raise Exception(FREE_LOG)

        # 例外

        if SyncTimeUpdate_Flg is False:
            ret = self.UpdateSyncStatusRecode()
            if ret is not True:
                # 異常フラグON
                self.error_flag = 1

                # UIに表示するエラーメッセージ設定
                self.setDefaultUIDisplayMsg()

                # データベースの更新に失敗しました
                logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1007", [self.RepoId, ])  # ToDo
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, ret)
                g.applogger.debug(FREE_LOG)

        if RepoListSyncStatusUpdate_Flg is False:
            if len(self.UIDisplayMsg) <= 0:
                SyncStatus = TD_SYNC_STATUS_NAME_DEFINE.NORMAL()

            else:
                SyncStatus = TD_SYNC_STATUS_NAME_DEFINE.ERROR()

            ret = self.UpdateRepoListSyncStatus(SyncStatus)
            if ret is not True:
                # 異常フラグON
                self.error_flag = 1

                # データベースの更新に失敗しました
                logstr = g.appmsg.get_api_message("ITACICDFORIAC-ERR-1007", [self.RepoId, ])  # ToDo
                FREE_LOG = makeLogiFileOutputString(inspect.currentframe().f_code.co_filename, inspect.currentframe().f_lineno, logstr, ret)
                g.applogger.debug(FREE_LOG)

        # 結果出力
        if self.error_flag != 0:
            FREE_LOG = g.appmsg.get_api_message("ITAWDCH-ERR-50001")  # ToDo
            g.applogger.debug(FREE_LOG)
            return 2

        FREE_LOG = g.appmsg.get_api_message("ITAWDCH-STD-50002")  # ToDo
        g.applogger.debug(FREE_LOG)

        return 0


################################################################
# 親
################################################################
def chkRepoListAndSyncStatusRow(DBobj):

    # リポジトリ管理、同期状態管理のいずれかにしか存在しないIDを抽出
    SyncStatusAdd = []
    SyncStatusDel = []

    sql = (
        "SELECT TAB_A.REPO_ROW_ID, TAB_B.ROW_ID AS SYNC_STATUS_ROW_ID "
        "FROM ("
        "  SELECT REPO_ROW_ID AS ROW_ID FROM T_CICD_REPOSITORY_LIST "
        "  UNION "
        "  SELECT ROW_ID FROM T_CICD_SYNC_STATUS "
        ") L "
        "LEFT OUTER JOIN T_CICD_REPOSITORY_LIST TAB_A "
        "ON L.ROW_ID=TAB_A.REPO_ROW_ID "
        "LEFT OUTER JOIN T_CICD_SYNC_STATUS TAB_B "
        "ON L.ROW_ID=TAB_B.ROW_ID "
    )

    rset = DBobj.sql_execute(sql, [])
    for row in rset:
        if row['REPO_ROW_ID'] is not None and row['SYNC_STATUS_ROW_ID'] is None:
            SyncStatusAdd.append(row['REPO_ROW_ID'])

        elif row['REPO_ROW_ID'] is None and row['SYNC_STATUS_ROW_ID'] is not None:
            SyncStatusDel.append(row['SYNC_STATUS_ROW_ID'])

    # リポジトリ管理にのみ存在するIDを同期状態管理に追加
    for repoId in SyncStatusAdd:
        sql = (
            "INSERT INTO T_CICD_SYNC_STATUS (ROW_ID, SYNC_LAST_TIMESTAMP) "
            "VALUES (%s, %s) "
        )

        DBobj.sql_execute(sql, [repoId, None])

    # 同期状態管理にのみ存在するIDを同期状態管理から削除
    if len(SyncStatusDel) > 0:
        sql = ""
        for repoId in SyncStatusDel:
            if sql:
                sql += " ,%s"

            else:
                sql += "%s"

        sql = "DELETE FROM T_CICD_SYNC_STATUS WHERE ROW_ID IN (%s) " % (sql)
        DBobj.sql_execute(sql, SyncStatusDel)

    return True

def getTargetRepoListRow(DBobj):

    # リポジトリ管理抽出(廃止レコードではない、自動同期が有効、(同期状態が異常ではない or 同期実行状態が未実施))
    sql = (
        "SELECT "
        "  TAB_A.*, "
        "  TAB_B.* "
        "FROM "
        "  T_CICD_REPOSITORY_LIST TAB_A "
        "INNER JOIN "
        "  T_CICD_SYNC_STATUS TAB_B "
        "ON "
        "  TAB_A.REPO_ROW_ID = TAB_B.ROW_ID "
        "WHERE "
        "  TAB_A.DISUSE_FLAG = '0' "
        "  AND TAB_A.AUTO_SYNC_FLG = %s "
        "  AND (TAB_A.SYNC_STATUS_ROW_ID <> %s OR TAB_A.SYNC_STATUS_ROW_ID IS NULL) "
    )

    tgtRepoListRow = DBobj.sql_execute(sql, ['1', TD_SYNC_STATUS_NAME_DEFINE.ERROR()])

    return tgtRepoListRow

def backyard_main(organization_id, workspace_id):

    print("backyard_main called")

    DBobj = DBConnectWs()
    DBobj.db_transaction_start()

    # リポジトリ管理と同期状態管理テーブルのレコード紐付確認
    chkRepoListAndSyncStatusRow(DBobj)

    # リポジトリ管理から処理対象のリポジトリ取得
    tgtRepoListRow = getTargetRepoListRow(DBobj)
    print(tgtRepoListRow)
    for row in tgtRepoListRow:
        ExecuteTime = datetime.datetime.now()
        RepoId = row['REPO_ROW_ID']
        ExecMode = "Remake"
        if row['SYNC_STATUS_ROW_ID'] == TD_SYNC_STATUS_NAME_DEFINE.NORMAL():
            ExecMode = "Normal"

        sync_last_timestamp = row['SYNC_LAST_TIMESTAMP']
        if sync_last_timestamp is None:
            sync_last_timestamp = datetime.datetime.fromtimestamp(0)

        if row['SYNC_INTERVAL'] is None or row['SYNC_INTERVAL'] == "":
            row['SYNC_INTERVAL'] = 60

        # 前回同期から指定秒を経過しているかチェック
        sync_interval = int(row['SYNC_INTERVAL'])
        if ExecuteTime >= sync_last_timestamp + datetime.timedelta(seconds=sync_interval):
            FREE_LOG = g.appmsg.get_api_message("ITACICDFORIAC-STD-2013", [RepoId, ])
            g.applogger.debug(FREE_LOG)

            child_obj = CICD_ChildWorkflow(organization_id, workspace_id, DBobj, RepoId, ExecMode, row)
            child_obj.main()


    DBobj.db_commit()

    print("backyard_main end")

