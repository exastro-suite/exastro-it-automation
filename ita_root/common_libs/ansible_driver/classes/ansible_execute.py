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
import os
import re
from flask import g
import shlex

from common_libs.ansible_driver.functions.util import getAnsibleExecutDirPath, get_AnsibleDriverShellPath, getAnsibleConst
from common_libs.ansible_driver.functions.util import get_OSTmpPath, addAnsibleCreateFilesPath

from common_libs.ansible_driver.classes.controll_ansible_agent import DockerMode, KubernetesMode
from common_libs.common.util import ky_file_decrypt, ky_decrypt, retry_chmod
from common_libs.ansible_driver.functions.util import loacl_quote
from common_libs.common.storage_access import storage_read, storage_write


"""
Ansible coreコンテナの実行を制御するモジュール
"""


class AnsibleExecute():
    """
    Ansible coreコンテナの実行を制御するクラス
    """

    def __init__(self):
        """
        コンストラクタ
        Arguments:
            なし
        Returns:
            なし
        """
        self.getLastErrormsg = ""
        self.strInFolderName = 'in'
        self.strOutFolderName = 'out'
        self.strTempFolderName = '.tmp'
        # ansible-playbookコマンド実行結果ファイル
        self.Resultfile = 'result.txt'
        # 緊急停止ファイル
        self.forcedfile = 'forced.txt'
        # ansible-playbookコマンドの標準出力ファイル（オリジナル）
        self.orgSTDOUTLogfile = 'exec.log.org'
        # ansible-playbookコマンドの標準出力ファイル（加工後）
        self.STDOUTLogfile = 'exec.log'
        # ansible-playbookコマンドの標準エラー出力ファイル（加工後）
        self.STDERRLogfile = 'error.log'
        self.setLastError("")

    def getLastError(self):
        """
        エラーメッセージ取得
        Arguments:
            なし
        Returns:
            エラーメッセージ
        """
        return self.getLastErrormsg

    def setLastError(self, msg):
        """
        エラーメッセージ退避
        Arguments:
            なし
        Returns:
            エラーメッセージ
        """
        self.getLastErrormsg = msg

    def execute_construct(self, ansConstObj, execute_no, conductor_instance_no, virtualenv_name, execute_user, ansible_path, vault_password, run_mode, forks):  # noqa: E501
        """
        作業実行コンテナよりansible-playbookコマンド実行
        Arguments:
            ansConstObj:    ansible共通定数オブジェクト
            execute_no:     作業番号:
                            T_ANSR_EXEC_STS_INST.EXECUTION_NO
            conductor_instance_no:  コンダクターno:
                            T_ANSR_EXEC_STS_INST.CONDUCTOR_INSTANCE_NO
            virtualenv_name:   仮想環境名
                               空白(2.0以降用)
            execute_user:      実行ユーザー
                               空白(2.0以降用)
            ansible_path:      ansibleインストールパス:
                               /指定無し
            vault_password:    vaultパスワード:
                               T_ANSC_IF_INFO.ANSIBLE_VAULT_PASSWORD
            run_mode:          実行種別:
                               T_ANSR_EXEC_STS_INST.RUN_MODE
            forks:             並列実行数:
                               空白  (2.0以降用)
        Returns:
            True/False
        """
        self.setLastError("")

        strPlayBookFileName = 'playbook.yml'
        strExecshellName = '/.playbook_execute_shell.sh'

        # 作業実行パス取得（作業番号まで）
        execute_path = getAnsibleExecutDirPath(ansConstObj, execute_no)

        # palybook実行に必要なファイルパス生成
        strExecshellTemplateName = "{}/ky_ansible_playbook_command_shell_template.sh".format(get_AnsibleDriverShellPath())
        strSSHAddShellName = "{}/{}/.ky_ansible_ssh_add.exp".format(execute_path, self.strTempFolderName)
        strEncodeSSHAgentconfigFileName = "{}/{}/.sshAgentConfig.txt".format(execute_path, self.strTempFolderName)
        strDecodeSSHAgentconfigFileName = "{}/{}/.sshAgentConfig.dec".format(execute_path, self.strTempFolderName)
        strShellLogFileName = "{}/{}/playbook_execute_shell.log".format(execute_path, self.strTempFolderName)
        strVaultPasswordFileName = "{}/{}/.tmpkey".format(execute_path, self.strTempFolderName)
        strResultFileName = "{}/{}/{}".format(execute_path, self.strOutFolderName, self.Resultfile)
        strCurrentPath = "{}/{}".format(execute_path, self.strInFolderName)
        strExecshellName = "{}/{}/.playbook_execute_shell.sh".format(execute_path, self.strTempFolderName)

        # ansible vault password file作成
        # #2079 /storage配下は/tmpを経由してアクセスする
        obj = storage_write()
        obj.open(strVaultPasswordFileName, 'w')
        obj.write(ky_decrypt(vault_password))
        obj.close()

        # 実行ユーザー確認
        if execute_user:
            execute_user = "-u {}".format(execute_user)
        else:
            execute_user = " "

        # 親playbook取得
        if ansConstObj.vg_driver_id == ansConstObj.DF_LEGACY_ROLE_DRIVER_ID:
            strPlayBookFileName = 'site.yml'

        # ansible-playbookコマンド実行時のオプションパラメータファイルパス
        stroptionfile = "{}/{}/AnsibleExecOption.txt".format(execute_path, self.strInFolderName)
        # ansible-playbookコマンド実行時のオプション取得
        stransibleplaybook_options = ''
        # #2079 /storage配下は/tmpを経由してアクセスする
        obj = storage_read()
        obj.open(stroptionfile)
        stransibleplaybook_options = obj.read()
        obj.close()

        # パラメータ文字列をエスケープする
        stransibleplaybook_options = loacl_quote(stransibleplaybook_options)
        # ドライランモードの場合のansible-playbookのパラメータを設定する。
        if run_mode == '2':
            stransibleplaybook_options += ' --check '

        # 改行をスペースに置換
        stransibleplaybook_options = stransibleplaybook_options.replace('\n', ' ')

        # 並列実行数対応 (pioneerの場合)
        if forks:
            # 数値の場合に文字列に変換
            if isinstance(forks, int):
                forks = str(forks)
            stransibleplaybook_options += ' --forks ' + forks + ' '
        else:
            stransibleplaybook_options += ' '

        # ssh-agentへの秘密鍵ファイルのパスフレーズ登録が必要か判定
        sshAgentExec = "NONE"
        if os.path.isfile(strEncodeSSHAgentconfigFileName):
            if os.path.getsize(strEncodeSSHAgentconfigFileName) != 0:
                sshAgentExec = "RUN"
                # ssh-agentへの秘密鍵ファイルのパスフレーズ登録に必要な情報ファイルの復号化
                ret = ky_file_decrypt(strEncodeSSHAgentconfigFileName, strDecodeSSHAgentconfigFileName)
                if ret is False:
                    # sshAgent用認証ファイル作成失敗
                    msgstr = g.appmsg.get_api_message("MSG-10889", [])
                    self.setLastError(msgstr)
                    return False
                # ssh-agentへの秘密鍵ファイルのパスフレーズ登録されているファイルなのでゴミ掃除リストに追加
                addAnsibleCreateFilesPath(strDecodeSSHAgentconfigFileName)

        # hostsフルパス
        strhosts = "{}/{}/hosts".format(execute_path, self.strInFolderName)
        # playbookフルパス
        strPlaybookPath = "{}/{}/{}".format(execute_path, self.strInFolderName, strPlayBookFileName)

        # virtualenv が設定されている場合、ansible_vaultのパスを空白にする。
        if virtualenv_name:
            virtualenv_flg = "__define__"
            strEngineVirtualenvName = virtualenv_name + "/bin/activate"
            ansible_path = ""
        else:
            virtualenv_flg = "__undefine__"
            strEngineVirtualenvName = "__undefine__"
            ansible_path += "/"

        playbook_command = "ansible-playbook"
        # Ansible実行するshellを作成
        strBuildCommand = "{} -i {} {} --vault-password-file {} {}".format(
            shlex.quote(playbook_command),
            shlex.quote(strhosts),
            stransibleplaybook_options,
            shlex.quote(strVaultPasswordFileName),
            shlex.quote(strPlaybookPath))

        # sshAgentの設定とPlaybookを実行するshellのテンプレートを読み込み
        strShell = ""
        # #2079 /storage配下は/tmpを経由してアクセスする
        obj = storage_read()
        obj.open(strExecshellTemplateName)
        strShell = obj.read()
        obj.close()

        # テンプレート内の変数を実値に置き換え
        strShell = strShell.replace('<<sshAgentConfigFile>>', strDecodeSSHAgentconfigFileName)
        strShell = strShell.replace('<<logFile>>', strShellLogFileName)
        strShell = strShell.replace('<<ssh_add_script_path>>', strSSHAddShellName)
        strShell = strShell.replace('<<in_directory_path>>', strCurrentPath)
        strShell = strShell.replace('<<ansible_playbook_command>>', strBuildCommand)
        strShell = strShell.replace('<<sshAgentExec>>', sshAgentExec)
        strShell = strShell.replace('<<virtualenv_path>>', strEngineVirtualenvName)
        strShell = strShell.replace('<<result_file_path>>', strResultFileName)

        # ansible-playbook実行 shell作成
        # #2079 /storage配下は/tmpを経由してアクセスする
        obj = storage_write()
        obj.open(strExecshellName, 'w')
        obj.write(strShell)
        obj.close()

        retry_chmod(strExecshellName, 0o777)
        # ansible-playbook 標準エラー出力先
        strSTDERRFileName = "{}/{}/{}".format(execute_path, self.strOutFolderName, self.STDERRLogfile)
        # ansible-playbook 標準出力出力先
        strorgSTDOUTFileName = "{}/{}/{}".format(execute_path, self.strOutFolderName, self.orgSTDOUTLogfile)

        # コンテナ内で実行するshell
        str_shell_command = "{} {} 1> {} 2>> {}".format(strExecshellName, virtualenv_flg, strorgSTDOUTFileName, strSTDERRFileName)

        ###########################################
        # コンテナキックの処理
        # return True/False
        ###########################################
        # container software
        container_base = os.getenv('CONTAINER_BASE')
        if container_base == 'docker':
            ansibleAg = DockerMode()
        else:
            ansibleAg = KubernetesMode()

        g.applogger.info("[Trace] container_start_up start.")
        result = ansibleAg.container_start_up(ansConstObj, execute_no, conductor_instance_no, str_shell_command)
        g.applogger.info("[Trace] container_start_up done.")
        if result[0] is True:
            g.applogger.debug(result[1])
            return True
        else:
            self.setLastError(result[1])
            return False

    def execute_statuscheck(self, ansConstObj, execute_no):
        """
        作業実行コンテナの実行状態を確認
        Arguments:
            ansConstObj:    ansible共通定数オブジェクト
            execute_no:     作業番号
                            T_ANSR_EXEC_STS_INST.EXECUTION_NO
        Returns:
            "2"     実行中
            "5"     完了
            "6"     完了(異常)
            "7"     想定外エラー
            "8"     緊急停止
        """
        self.setLastError("")

        retStatus = "2"
        # 作業実行パス取得（作業番号まで）
        execute_path = getAnsibleExecutDirPath(ansConstObj, execute_no)
        # 緊急停止ファイル作成
        strForcedFileName = "{}/{}/{}".format(execute_path, self.strOutFolderName, self.forcedfile)
        # ansible-playbookコマンド実行結果ファイル
        strResultFileName = "{}/{}/{}".format(execute_path, self.strOutFolderName, self.Resultfile)

        # 実行コンテナ操作用クラス
        container_base = os.getenv('CONTAINER_BASE')
        if container_base == 'docker':
            ansibleAg = DockerMode()
        else:
            ansibleAg = KubernetesMode()

        ##########################
        # コンテナの実行状態確認
        #   True: 起動
        #   False: 停止
        res_is_container_running = ansibleAg.is_container_running(execute_no)
        if res_is_container_running[0] is True:
            # 緊急停止ファイルの有無確認
            if os.path.isfile(strForcedFileName):
                # 緊急停止ファイルあり

                ##########################
                # コンテナ停止
                #   True: 停止
                #   False: 停止失敗
                res_container_kill = ansibleAg.container_kill(ansConstObj, execute_no)
                if res_container_kill[0] is True:
                    # ステータス 緊急停止
                    retStatus = "8"
                else:
                    # ステータス 想定外エラー
                    self.setLastError(res_container_kill[1])
                    # msgstr = g.appmsg.get_api_message("", [])
                    # self.setLastError(msgstr)
                    retStatus = "7"
            else:
                # ステータス 実行中
                retStatus = "3"
        else:
            # ansible-playbookコマンド実行結果ファイルより結果を取得
            if os.path.isfile(strResultFileName):
                # ansible-playbookコマンド実行結果ファイルより結果取得
                strStatus = ""
                # #2079 /storage配下は/tmpを経由してアクセスする
                obj = storage_read()
                obj.open(strResultFileName)
                strStatus = obj.read()
                obj.close()

                key = "^COMPLETED"
                match = re.findall(key, strStatus)
                if len(match) == 1:
                    # ステータス 完了
                    retStatus = "5"
                else:
                    # ステータス 完了(異常)
                    retStatus = "6"
            else:
                # ansible-playbookコマンド実行結果ファイルなし
                return_code = res_is_container_running[1]['return_code']
                if return_code != 0:
                    # コンテナの起動確認が正しく行えなかった
                    self.setLastError(res_is_container_running[1])
                else:
                    # ステータス 想定外エラー
                    msgstr = g.appmsg.get_api_message("MSG-10890", [])
                    self.setLastError(msgstr)
                retStatus = "7"

            # 終了済みコンテナの削除
            res_is_container_clean = ansibleAg.container_clean(ansConstObj, execute_no)
            if res_is_container_clean[0] is False:
                # ステータス 想定外エラー
                self.setLastError(res_is_container_clean[1])

        # ansible-playbook 標準出力出力先
        strorgSTDOUTFileName = "{}/{}/{}".format(execute_path, self.strOutFolderName, self.orgSTDOUTLogfile)
        strSTDOUTFileName = "{}/{}/{}".format(execute_path, self.strOutFolderName, self.STDOUTLogfile)

        # 特定のキーワードで改行しansibleのログを見やすくする
        if os.path.isfile(strorgSTDOUTFileName):
            # #2079 /storage配下は/tmpを経由してアクセスする
            obj = storage_read()
            obj.open(strorgSTDOUTFileName, "r")
            log_data = obj.read()
            obj.close()

            if ansConstObj.vg_driver_id == ansConstObj.DF_PIONEER_DRIVER_ID:
                # ログ(", ")  =>  (",\n")を改行する
                log_data = log_data.replace("\", \"", "\",\n\"")
                # 改行文字列\r\nを改行コードに置換える
                log_data = log_data.replace("\\r\\n", "\n")
                # python改行文字列\\nを改行コードに置換える
                log_data = log_data.replace("\\n", "\n")
            else:
                # ログ(", ")  =>  (",\n")を改行する
                log_data = log_data.replace("\", \"", "\",\n\"")
                # ログ(=> {)  =>  (=> {\n)を改行する
                log_data = log_data.replace("=> {", "=> {\n")
                # ログ(, ")  =>  (,\n")を改行する
                log_data = log_data.replace(", \"", ",\n\"")
                # 改行文字列\r\nを改行コードに置換える
                log_data = log_data.replace("\\r\\n", "\n")
                # python改行文字列\\nを改行コードに置換える
                log_data = log_data.replace("\\n", "\n")
        else:
            log_data = ""
        # #2079 /storage配下は/tmpを経由してアクセスする
        obj = storage_write()
        obj.open(strSTDOUTFileName, "w")
        obj.write(log_data)
        obj.close()

        return retStatus

    def execute_abort(self, driver_id, execute_no):
        """
        作業実行コンテナの緊急停止
        Arguments:
            driver_id:      ドライバID:
                            AnscConst.DF_LEGACY_ROLE_DRIVER_ID
            execute_no:     作業番号
                            T_ANSR_EXEC_STS_INST.EXECUTION_NO
        Returns:
            True/False
        """
        self.setLastError("")

        # 作業実行パス取得（作業番号まで）
        ansc_const = getAnsibleConst(driver_id)

        execute_path = getAnsibleExecutDirPath(ansc_const, execute_no)
        # 緊急停止ファイル作成
        strForcedFileName = "{}/{}/{}".format(execute_path, self.strOutFolderName, self.forcedfile)
        # #2079 /storage配下は/tmpを経由してアクセスする
        obj = storage_write()
        obj.open(strForcedFileName, "w")
        obj.write("")
        obj.close()

        return True
