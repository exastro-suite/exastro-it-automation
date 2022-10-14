import base64
import codecs
import os
import subprocess
import sys
from common_libs.ansible_driver.functions.util import *
from common_libs.common import *

"""
  ansible vault関連モジュール
"""


class AnsibleVault: 
    """
      ansible vault関連クラス
    """
    def CreateVaultPasswordFilePath(self, ansiblePlaybookVaultPath=False):
        """
          ansible-vaultパスワードファイルパス生成
          Arguments:
            ansiblePlaybookVaultPath: ansible-playbookコマンドのansible-vaultパスワードファイルパス生成判定
          Returns:
            ansible-vaultパスワードファイルパス
        """
        if ansiblePlaybookVaultPath is False:
            VaultPasswordFilePath = "{}/.vault_{}".format(get_AnsibleDriverTmpPath(), os.getpid())
        else:
            VaultPasswordFilePath = "{}/.tmp/.tmpkey".format(ansiblePlaybookVaultPath)
        return VaultPasswordFilePath

    def CreateVaultPasswordFile(self, VaultPasswordFilePath, vaultPassword):
        """
          ansible-vaultパスワードファイル生成
          Arguments:
            VaultPasswordFilePath: ansible-vaultパスワードファイルパス
            vaultPassword: ansible-vaultパスワード(エンコード文字列)
          Returns:
            True
        """
        self.VaultPasswordFilePath = VaultPasswordFilePath
        fd = open(VaultPasswordFilePath, 'w')
        fd.write(ky_decrypt(vaultPassword))
        fd.close()
        return True

    def RemoveVaultPasswordFile(self):
        """
          ansible-vaultパスワードファイル削除
          Arguments:
            なし
          Returns:
            なし
        """
        os.remove(self.VaultPasswordFilePath)

    def Vault(self, ansible_path, exec_user, password_file, value, indento, engine_virtualenv_path, passwdFileDel=True):
        """
          ansible-vaultで指定文字列を暗号化
          Arguments:
            ansible_path:           ansible-coreインストール先パス
            exec_user:              実行ユーザー(非コンテナ環境用)
            password_file:          ansible-vaultパスワードファイルパス
            value:                  暗号化したい文字列
            indento:                暗号化された文字列に付与するインデント
            engine_virtualenv_path: 仮想環境パス(非コンテナ環境用)
            passwdFileDel:          ansible-vaultパスワードファイルの削除有無
          Returns:
            True/False, mt_encode_value: 暗号化された文字列
        """
        result = True
        mt_encode_value = ""

        strExecshellTemplateName = "{}/{}".format(get_AnsibleDriverShellPath(), "ky_ansible_vault_command_shell_template.sh")

        strExecshellName = "{}/ansible_vault_execute_shell_{}.sh".format(get_AnsibleDriverTmpPath(), os.getpid())

        if engine_virtualenv_path:
            virtualenv_flg = "__define__"
            engine_virtualenv_path += "/bin/activate"
            ansible_path = ""
        else:
            virtualenv_flg = "__undefine__"
            engine_virtualenv_path = "__undefine__"
        # CR+LFをLFに置換
        value = value.replace("\r\n", "\n")

        # ansibel-vault パスワードファイル生成
        vault_value_file = "{}/ansible_vault_value_{}".format(get_AnsibleDriverTmpPath(), os.getpid())
        
        fd = open(vault_value_file, 'w')
        fd.write(value)
        fd.close()

        # ansibleインストールバスが設定されている場合に/を追加
        if ansible_path:
            ansible_path += "/"

        # ansible-vault commad 生成
        VaultCmd = "cat {} | {}ansible-vault encrypt --vault-password-file {}".format(vault_value_file, ansible_path, password_file)

        # sshAgentの設定とPlaybookを実行するshellのテンプレートを読み込み
        fd = open(strExecshellTemplateName, 'r')
        strShell = fd.read(-1)
        fd.close()

        # テンプレート内の変数を実値に置き換え
        strShell = strShell.replace('<<ansible_valut_command>>', VaultCmd)
        strShell = strShell.replace('<<virtualenv_path>>', engine_virtualenv_path)

        # ansible-vaultshell作成
        fd = open(strExecshellName, 'w')
        fd.write(strShell)
        fd.close()

        # パーミッション設定
        os.chmod(strExecshellName, 0o777)
        # Ansible_vault実行Commnad発行
        if exec_user.strip() != "":
            cmd = "sudo -u {} -i {} {}".format(exec_user, strExecshellName, virtualenv_flg)
        else:
            cmd = "{} {}".format(strExecshellName, virtualenv_flg)
        # text=Trueはpython3.6にないので未使用
        ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
        # 一時ファイル削除
        os.remove(vault_value_file)
        os.remove(strExecshellName)
        if passwdFileDel is True:
            self.RemoveVaultPasswordFile()

        # 結果判定
        if ret.returncode != 0:
            # エラー情報退避
            indento = ""
            mt_encode_value = to_str(ret.stderr)
        else:
            # 暗号化文字列取得
            output = to_str(ret.stdout)
            arry_list = output.split("\n") 
        
            # 暗号化文字列加工
            for line in arry_list:
                if line.strip() == 0:
                    continue
                if mt_encode_value.strip() != 0:
                    mt_encode_value += "\n"
                # インデント設定
                mt_encode_value += indento + line

        if ret.returncode != 0:
            result = False
        return result, mt_encode_value

    def setValutPasswdIndento(self, val, indento):
        """
          ansible-vaulで暗号化された文字列に所定のインデントを付加
          Arguments:
            val: 暗号化された文字列
            indento: 所定のインデント文字列
          Returns:
            暗号化された文字列に所定のインデントを付加した文字列
        """
        edit_val = ""
        array_list = val.split("\n")
        for line in array_list:
            if edit_val == "":
                edit_val = line
            else:
                edit_val += "\n" + indento + line
        return edit_val
