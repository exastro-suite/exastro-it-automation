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
#############################################################
# __init__
# getAnsibleWorkingDirectories
# lineno
# setITALocalVars
# getAnsibleDriverCommonShellPath
# CreateAnsibleWorkingDir
# CreateAnsibleWorkingFiles
# CreateHostsfile
# DeleteUnuseData
# InventryFileAddOptionCheckFormat
# CreateRoleHostvarsfiles
# CreateRoleHostvarsfile
# CreatePlaybookfile
# setAnsibleDriverID
# getAnsibleDriverID
# setAnsibleBaseDir
# getAnsibleBaseDir
# setAnsible_in_Dir
# getAnsible_in_Dir
# setAnsible_child_playbooks_Dir
# getAnsible_child_playbooks_Dir
# setPlaybook_child_playbooks_Dir
# getPlaybook_child_playbooks_Dir
# setAnsible_dialog_files_Dir
# getAnsible_dialog_files_Dir
# setAnsible_host_vars_Dir
# getAnsible_host_vars_Dir
# setAnsible_out_Dir
# getAnsible_out_Dir
# setAnsible_tmp_Dir
# getAnsible_tmp_Dir
# setAnsible_original_dialog_files_Dir
# getAnsible_original_dialog_files_Dir
# setAnsible_in_original_dialog_files_Dir
# getAnsible_in_original_dialog_files_Dir
# setAnsible_original_hosts_vars_Dir
# getAnsible_original_hosts_vars_Dir
# setAnsible_vault_hosts_vars_Dir
# getAnsible_vault_hosts_vars_Dir
# setAnsible_pioneer_template_hosts_vars_Dir
# getAnsible_pioneer_template_hosts_vars_Dir
# getAnsible_hosts_file
# getAnsible_playbook_file
# getAnsible_pioneer_template_host_var_file
# getAnsible_host_var_file
# getAnsible_org_host_var_file
# LocalLogPrint
# getDBHostList
# getDBRoleVarList
# getDBVarList
# MultiArrayVarsToYamlFormatMain
# getDBVarMultiArrayVarsList
# getDBLegacyPlaybookList
# getDBPioneerDialogFileList
# addSystemvars
# getDBTemplateMaster
# setHostvarsfile_template_file_Dir
# getHostvarsfile_template_file_Dir
# setTemporary_file_Dir
# getTemporary_file_Dir
# setAnsible_template_files_Dir
# getAnsible_template_files_Dir
# getITA_template_file
# getHostvarsfile_template_file_path
# getAnsible_template_file
# CreateTemplatefiles
# getDBPatternList
# getDBRolePackage
# getDBLegactRoleList
# CreateLegacyRolePlaybookfiles
# CheckLegacyRolePlaybookfilesrs):
# getAnsible_RolePlaybook_file
# getRolePackageFile
# getAnsible_RolePackage_file
# setHostvarsfile_copy_file_Dir
# getHostvarsfile_copy_file_Dir
# setAnsible_copy_files_Dir
# getAnsible_copy_files_Dir
# getITA_copy_file
# getHostvarsfile_copy_file_value
# getAnsible_copy_file
# CreateCopyfiles
# getDBCopyMaster
# makeHostVarsPath
# makeHostVarsArray
# MultiArrayVarsToYamlFormatSub
# is_assoc
# getDBGlobalVarsMaster
# CreateLegacyRoleCopyFiles
# setAnsible_upload_files_Dir
# getAnsible_upload_files_Dir
# setAnsible_ssh_key_files_Dir
# getAnsible_ssh_key_files_Dir
# getITA_ssh_key_file
# getIN_ssh_key_file
# CreateSSH_key_file
# setAnsible_win_ca_files_Dir
# getAnsible_win_ca_files_Dir
# getITA_win_ca_file
# getIN_win_ca_file
# CreateWIN_cs_file
# LegacyRoleCheckConcreteValueIsVarTemplatefile
# LegacyRoleCheckConcreteValueIsVar
# CreateLegacyRoleTemplateFiles
# makeAnsibleVaultPassword
# makeAnsibleVaultValue
# getAnsibleExecuteUser
# setAnsibleExecuteUser
# HostVarEdit
# MultilineValueEdit
# chkMultilineValue
# makeMultilineValue
# ArrayTypeValue_encode
# MultiValueEdit
# isJsonString
# getAnsible_vault_host_var_file
# CreateDirectoryForCollectionProcess
# makeDir
# CreateMovementStatusFileVariables
# CreatePioneerLANGVariables
# CreateOperationVariables
# CreateSSHAgentConfigInfoFile
# setFileUploadCloumnFileEnv
# AnsibleEnginVirtualenvPathCheck
# getTowerProjectDirPath
# getTowerInstanceDirPath
# setTowerProjectDirPath
# setAnsibleSideFilePath
# setAnsibleTowerSideFilePath
# setTowerProjectsScpPath
# getTowerProjectsScpPath
# CopyAnsibleConfigFile
# CopysshAgentExpectfile
#############################################################
import os
import shutil
import re
import inspect
import json
import sys
from dictknife import deepmerge
from flask import g

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst
from common_libs.ansible_driver.classes.ansible_common_libs import AnsibleCommonLibs
from common_libs.ansible_driver.classes.YamlParseClass import YamlParse
from common_libs.ansible_driver.classes.AnsibleVaultClass import AnsibleVault
from common_libs.ansible_driver.classes.VarStructAnalJsonConvClass import VarStructAnalJsonConv
from common_libs.ansible_driver.classes.CheckAnsibleRoleFiles import CheckAnsibleRoleFiles, DefaultVarsFileAnalysis
from common_libs.ansible_driver.classes.WrappedStringReplaceAdmin import WrappedStringReplaceAdmin

from common_libs.ansible_driver.functions.util import getMovementAnsibleCnfUploadDirPath
from common_libs.ansible_driver.functions.util import getRolePackageContentUploadDirPath
from common_libs.ansible_driver.functions.util import getFileContentUploadDirPath
from common_libs.ansible_driver.functions.util import getTemplateContentUploadDirPath
from common_libs.ansible_driver.functions.util import getDeviceListSSHPrivateKeyUploadDirPath
from common_libs.ansible_driver.functions.util import getDeviceListServerCertificateUploadDirPath
from common_libs.ansible_driver.functions.util import get_AnsibleDriverTmpPath
from common_libs.ansible_driver.functions.util import getFileupLoadColumnPath
from common_libs.ansible_driver.functions.util import getDataRelayStorageDir
from common_libs.ansible_driver.functions.util import getInputDataTempDir
from common_libs.common.util import ky_encrypt, ky_decrypt, ky_file_encrypt, ky_file_decrypt
"""
Ansibleの実行に必要な情報をデータベースから取得しAnsible実行ディレクトリを作成するモジュール
"""


class CreateAnsibleExecFiles():
    """
    Ansibleの実行に必要な情報をデータベースから取得しAnsible実行ディレクトリを作成するクラス
    """

    def __init__(self, in_driver_id, in_ans_if_info, in_exec_no, in_engine_virtualenv_name, in_ansible_cnf_file, in_objDBCA):
        """
        コンストラクタ
        Arguments:
            in_driver_id:                     ドライバ区分
            in_ans_if_info:                   ansibleインターフェース情報
            in_exec_no:                       作業番号
            in_engine_virtualenv_name:        Ansible Engine virtualenv path
            in_ansible_cnf_file:              Ansible config file name
            in_objDBCA:                       データベースアクセスクラス変数
        Returns:
            なし
        """
        self.LC_ANS_IN_DIR = "in"
        self.LC_ANS_OUT_DIR = "out"
        self.LC_ANS_TMP_DIR = "tmp"

        self.LC_ANS_CHILD_PLAYBOOKS_DIR = "child_playbooks"
        self.LC_ANS_DIALOG_FILES_DIR = "dialog_files"
        self.LC_ANS_HOST_VARS_DIR = "host_vars"

        self.LC_VARS_ATTR_STD = '1'      # 一般変数
        self.LC_VARS_ATTR_LIST = '2'     # 複数具体値
        self.LC_VARS_ATTR_STRUCT = '3'   # 多次元変数

        self.LC_ANS_GROUP_VARS_DIR = "group_vars"
        self.LC_ANS_ORG_DIALOG_FILES_DIR = "original_dialog_files"
        self.LC_ANS_ORG_HOST_VARS_DIR = "original_host_vars"
        self.LC_ANS_VAULT_HOST_VARS_DIR = "vault_host_vars"
        self.LC_ANS_PIONEER_TEMPLATE_HOST_VARS_DIR = "pioneer_template_host_vars"
        self.LC_ANS_TEMPLATE_FILES_DIR = "template_files"
        self.LC_ANS_UPLOAD_FILES_DIR = "upload_files"
        self.LC_ANS_OUTDIR_DIR = "user_files"
        self.LC_ANS_PIONEER_LIBRARY_DIR = "library"

        self.LC_ANS_UNDEFINE_NAME = "__undefinesymbol__"

        self.LC_ANS_HOSTS_FILE = "hosts"
        self.LC_ANS_PLAYBOOK_FILE = "playbook.yml"
        self.LC_ANS_ROLE_PLAYBOOK_FILE = "site.yml"

        self.LC_ANS_SSHAGENTCONFIG_FILE = ".sshAgentConfig.txt"
        self.LC_ANS_SSHAGENTEXPECT_FILE = "ky_ansible_ssh_add.exp"

        self.LC_WINRM_PORT = 5985

        self.lv_Ansible_driver_id = ""
        self.lv_hostaddress_type = ""

        self.lv_Ansible_base_Dir = {}
        self.lv_Ansible_in_Dir = ""
        self.lv_Ansible_child_playbooks_Dir = ""
        self.lv_Ansible_dialog_files_Dir = ""
        self.lv_Ansible_host_vars_Dir = ""
        self.lv_Ansible_out_Dir = ""
        self.lv_Ansible_tmp_Dir = ""
        self.lv_Ansible_original_dialog_files_Dir = ""
        self.lv_Ansible_original_hosts_vars_Dir = ""
        self.lv_Ansible_template_files_Dir = ""
        self.lv_Ansible_vault_hosts_vars_Dir = ""
        self.lv_Ansible_pioneer_template_hosts_vars_Dir = ""
        self.lv_Ansible_in_original_dialog_files_Dir = ""
        self.lv_Ansible_temporary_files_Dir = ""
        self.lv_GitRepo_temporary_DirAry = ""
        self.lv_Playbook_child_playbooks_Dir = ""
        self.lv_Hostvarsfile_template_file_Dir = ""
        self.lv_winrm_id = ""
        self.lv_ita_template_files_Dir = ""
        self.lv_Ansible_upload_files_Dir = ""
        self.lv_ansible_master_file_pkeyITEM = ""
        self.lv_ansible_master_file_nameITEM = ""
        self.LC_ANS_COPY_FILES_DIR = "copy_files"
        self.lv_ita_copy_files_Dir = ""
        self.run_operation_id = ""
        self.run_pattern_id = ""
        self.lv_objDBCA = ""
        self.lva_global_vars_list = ""
        self.lva_cpf_vars_list = {}
        self.lva_tpf_vars_list = {}
        self.lv_user_out_Dir = ""
        self.lv_conductor_instance_Dir = ""
        self.lv_conductor_instance_no = ""
        self.LC_ANS_SSH_KEY_FILES_DIR = "ssh_key_files"
        self.LC_ANS_SSH_KEY_FILE_VAR_NAME = "__ssh_key_file__"
        self.LC_ANS_SSH_EXTRA_ARGS_VAR_NAME = "__ssh_extra_args__"
        self.LC_ANS_PIONEER_LANG_VAR_NAME = "__pioneer_lang__"
        self.v_Ansible_ssh_key_files_Dir = ""
        self.LC_ANS_WIN_CA_FILES_DIR = "winrm_ca_files"
        self.lv_Ansible_win_ca_files_Dir = ""
        self.lv_legacy_Role_cpf_vars_list = {}
        self.lv_legacy_Role_tpf_vars_list = {}
        self.lv_tpf_vars_list = {}
        self.lv_cpf_vars_list = {}
        self.lv_use_gbl_vars_list = {}
        self.lv_parent_vars_list = {}
        self.lv_tpf_var_file_path_list = {}
        self.lv_cpf_var_file_path_list = {}
        self.ansible_vault_password_file_dir = ""
        self.lv_hostinfolist = {}
        self.ansible_exec_user = ""
        self.lv_ans_if_info = {}
        self.lv_exec_no = ""
        self.lv_vault_pass_list = {}
        self.lv_vault_pass_update_list = {}
        self.lv_vault_value_list = {}
        self.lv_vault_value_update_list = {}

        self.lv_engine_virtualenv_name = ""
        self.lv_ansible_cnf_file = ""

        self.LegacyRoleCheckConcreteValueIsVar_use_host_name = ""
        self.LegacyRoleCheckConcreteValueIsVar_use_var_list = ""

        # Tower 作業インスタンス毎 Project Path
        # lv_TowerInstanceDirPath["TowerPath"]   "/var/lib/awx/projects"
        # lv_TowerInstanceDirPath["ExastroPath"] "/var/lib/exastro"
        self.lv_TowerInstanceDirPath = {}

        self.lv_exec_mode = ""

        self.LC_ITA_OUT_DIR = "__ita_out_dir__"
        self.LC_ITA_IN_DIR = "__ita_in_dir__"
        self.LC_ITA_CONDUCTOR_DIR = "__ita_conductor_dir__"
        self.LC_ITA_SYMPHONY_DIR = "__ita_symphony_dir__"
        self.LC_ITA_TMP_DIR = "__ita_tmp_dir__"
        # Tower(/var/lib/awx/projects)ディレクトリへのファイル転送パス配列
        self.vg_TowerProjectsScpPathArray = {}

        # 実行エンジンを退避
        self.lv_exec_mode = in_ans_if_info['ANSIBLE_EXEC_MODE']

        self.AnscObj = AnscConst()
        self.setAnsibleDriverID(in_driver_id)
        if in_driver_id == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
            del self.AnscObj
            self.AnscObj = AnsrConst()
        # elif in_driver_id == self.AnscObj.DF_LEGACY_DRIVER_ID:
        #    del self.AnscObj
        #    self.AnscObj = AnslConst()
        # elif in_driver_id == self.AnscObj.DF_PIONEER_DRIVER_ID:
        #    del self.AnspObj
        #    self.AnscObj = AnslConst()
        # else:
        #    msgstr = g.appmsg.get_api_message("MSG-10082", [os.path.basename(__file__), self.lineno()])
        #    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename) + str(inspect.currentframe().f_lineno), msgstr)
        #    return False

        # ansible作業実行用ベースディレクトリ
        # ansible_ita_base_dir: /storage/{organization_id}/{workspace_id}/driver
        ansible_ita_base_dir = getDataRelayStorageDir() + "/driver"
        ansible_ans_base_dir = ansible_ita_base_dir
        self.setAnsibleBaseDir('ANSIBLE_SH_PATH_ITA', ansible_ita_base_dir)
        self.setAnsibleBaseDir('ANSIBLE_SH_PATH_ANS', ansible_ans_base_dir)

        # Conductor作業実行用ベースディレクトリ
        # Conductor_ita_base_dir: /storage/{organization_id}/{workspace_id}/driver/conductor
        Conductor_ans_base_dir = getDataRelayStorageDir() + "/driver/conductor"
        Conductor_ita_base_dir = Conductor_ans_base_dir
        self.setAnsibleBaseDir('CONDUCTOR_STORAGE_PATH_ANS', Conductor_ans_base_dir)
        self.setAnsibleBaseDir('CONDUCTOR_STORAGE_PATH_ITA', Conductor_ita_base_dir)

        # outディレクトリ
        self.lv_Ansible_out_Dir = ""

        self.lv_objDBCA = in_objDBCA
        self.lv_objMTS = ""

        self.lv_legacy_Role_cpf_vars_list = {}
        self.lv_legacy_Role_tpf_vars_list = {}
        self.lv_tpf_vars_list = {}
        self.lv_cpf_vars_list = {}
        self.lv_use_gbl_vars_list = {}
        self.lv_parent_vars_list = {}
        self.lv_tpf_var_file_path_list = {}
        self.lv_cpf_var_file_path_list = {}
        self.lv_ans_if_info = in_ans_if_info
        self.lv_exec_no = in_exec_no
        self.lv_vault_pass_list = {}
        self.lv_vault_pass_update_list = {}
        self.lv_vault_value_list = {}
        self.lv_vault_value_update_list = {}
        
        self.lv_engine_virtualenv_name = in_engine_virtualenv_name

        self.lv_ansible_cnf_file = in_ansible_cnf_file

        self.LegacyRoleCheckConcreteValueIsVar_use_host_name = ""
        self.LegacyRoleCheckConcreteValueIsVar_use_var_list = {}

        # AAC Projectディレクトリパス取得
        self.setTowerProjectDirPath()

        # Gitリポジトリ用ディレクトリ取得
        self.lv_GitRepo_temporary_DirAry = getInputDataTempDir(in_exec_no, self.AnscObj.vg_tower_driver_name)

    def getAnsibleWorkingDirectories(self, in_oct_id, in_execno):
        """
        ansible用作業ディレクトリパス取得
        Arguments:
            in_oct_id: オケストレータID
        Returns:
            ansible用作業ディレクトリパス
        """
        aryRetAnsibleWorkingDir = []

        # /{storage}/{organization_id}/{workspace_id}/driver/ansible
        c_dir_per_ans_orc_type_id = "{}/ansible".format(self.getAnsibleBaseDir('ANSIBLE_SH_PATH_ITA'))

        aryRetAnsibleWorkingDir.append(c_dir_per_ans_orc_type_id)

        # /{storage}/{organization_id}/{workspace_id}/driver/ansible/{legacy / pioneer / legacy_role}
        c_dir_per_orc_id = "{}/{}".format(c_dir_per_ans_orc_type_id, in_oct_id)
        aryRetAnsibleWorkingDir.append(c_dir_per_orc_id)

        # /{storage}/{organization_id}/{workspace_id}/driver/ansible/{legacy / pioneer / legacy_role}/作業番号
        c_dir_per_exe_no = "{}/{}".format(c_dir_per_orc_id, in_execno)
        aryRetAnsibleWorkingDir.append(c_dir_per_exe_no)

        # /{storage}/{organization_id}/{workspace_id}/driver/ansible/{legacy / pioneer / legacy_role}/作業番号/in
        c_dir_in_per_exe_no = "{}/{}".format(c_dir_per_exe_no, self.LC_ANS_IN_DIR)
        aryRetAnsibleWorkingDir.append(c_dir_in_per_exe_no)

        # /{storage}/{organization_id}/{workspace_id}/driver/ansible/{legacy / pioneer / legacy_role}/作業番号/out
        c_dir_out_per_exe_no = "{}/{}".format(c_dir_per_exe_no, self.LC_ANS_OUT_DIR)
        aryRetAnsibleWorkingDir.append(c_dir_out_per_exe_no)

        return aryRetAnsibleWorkingDir

    def lineno(self):
        """
        行番号取得
        Arguments:
            なし
        Returns:
            行番号
        """
        frame = inspect.currentframe().f_back
        return frame.f_lineno

    def setITALocalVars(self):
        """
        ITA独自変数名リスト生成
        Arguments:
            なし
        Returns:
            ITA独自変数名リスト
        """
        system_vars = []
        system_vars.append(self.AnscObj.ITA_SP_VAR_ANS_PROTOCOL_VAR_NAME)
        system_vars.append(self.AnscObj.ITA_SP_VAR_ANS_USERNAME_VAR_NAME)
        system_vars.append(self.AnscObj.ITA_SP_VAR_ANS_PASSWD_VAR_NAME)
        system_vars.append(self.AnscObj.ITA_SP_VAR_ANS_LOGINHOST_VAR_NAME)
        system_vars.append(self.AnscObj.ITA_SP_VAR_ANS_OUTDIR_VAR_NAME)
        system_vars.append(self.AnscObj.ITA_SP_VAR_CONDUCTO_DIR_VAR_NAME)
        return system_vars

    def getAnsibleDriverCommonShellPath(self):
        path = "{}{}/{}/{}".format(os.environ["PYTHONPATH"], g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'), "/common_libs/ansible_driver/shells")
        return path

    def CreateAnsibleWorkingDir(self,
                                in_oct_id,
                                in_execno,
                                in_operation_id,
                                in_hostaddress_type,
                                in_winrm_id,
                                in_pattern_id,
                                mt_rolenames,
                                mt_rolevars,
                                mt_roleglobalvars,
                                mt_role_rolepackage_id,
                                mt_def_vars_list,
                                mt_def_array_vars_list,
                                in_conductor_instance_no):
        """
        ansible用作業ディレクトリを作成
        Arguments:
            in_execno                   作業実行番号
            in_operation_id             オペレーションID
            in_hostaddress_type         ホストアドレス方式
                                        null or 1:IP方式  2:ホスト名方式
            in_winrm_id                 対象ホストがwindowsかを判別
                                        1: windows 他:windows以外
            in_pattern_id               作業パターンID
                                        Legacy-Role時のみ必須
            ina_rolenames               Legacy-Role role名リスト
                                        Legacy-Role時のみ必須
                                        ina_rolename[role名]
            ina_rolevars                Legacy-Role role内変数リスト
                                        Legacy-Role時のみ必須
                                        ina_rolevars[role名][変数名]=0
            mt_roleglobalvars           Legacy-Role role内グローバル変数リスト
                                        Legacy-Role時のみ必須
                                        mt_roleglobalvars[role名][グローバル変数名]=0
            mt_role_rolepackage_id      ロールパッケージ管理 Pkey 返却
                                        Legacy-Role時のみ必須
            mt_def_vars_list:          各ロールのデフォルト変数ファイル内に定義されている変数リスト
            mt_def_array_vars_list:    各ロールのデフォルト変数ファイル内に定義されている多次元変数の情報
            in_conductor_instance_no:   conductorから起動された場合のconductorインスタンスID
                                        作業実行の場合は空白
        Returns:
            True/False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list
        """
        self.lv_exec_no = in_execno

        self.lv_conductor_instance_no = in_conductor_instance_no

        self.run_operation_id = in_operation_id

        self.run_pattern_id = in_pattern_id

        self.lv_hostaddress_type = in_hostaddress_type

        self.lv_winrm_id = in_winrm_id

        # ドライバ区分ディレクトリ作成
        aryRetAnsibleWorkingDir = self.getAnsibleWorkingDirectories(in_oct_id, in_execno)

        # /{storage}/{organization_id}/{workspace_id}/driver/ansibleまでのディレクトリ作成
        c_dir = aryRetAnsibleWorkingDir[0]
        
        # /{storage}/{organization_id}/{workspace_id}/driver/ansible/{legacy / pioneer / legacy_role}
        # 作業番号ディレクトリ作成
        c_dir = aryRetAnsibleWorkingDir[1]
        if os.path.isdir(c_dir) is False:
            msgstr = g.appmsg.get_api_message("MSG-10120", [in_execno, c_dir])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list
        else:
            os.chmod(c_dir, 0o777)

        # /{storage}/{organization_id}/{workspace_id}/driver/ansible/{legacy / pioneer / legacy_role}/作業番号
        # 作業番号作成
        c_dir = aryRetAnsibleWorkingDir[2]
        if os.path.isdir(c_dir) is False:
            os.mkdir(c_dir)
        os.chmod(c_dir, 0o777)
        
        # /{storage}/{organization_id}/{workspace_id}/driver/ansible/{legacy / pioneer / legacy_role}/作業番号/out
        # outディレクトリ作成
        c_outdir = aryRetAnsibleWorkingDir[4]
        if os.path.isdir(c_outdir) is False:
            os.mkdir(c_outdir)
        os.chmod(c_outdir, 0o777)

        # outディレクトリ名を記憶
        self.setAnsible_out_Dir(c_outdir)

        # Tower(/var/lib/awx/projects)ディレクトリへのファイル転送パス退避
        # /var/lib/exastro/ita_legacy_executions_0000040099/__ita_out_dir__
        Tower_out_Dir = "{}/{}".format(self.getTowerProjectDirPath("ExastroPath"), self.LC_ITA_OUT_DIR)
        self.setTowerProjectsScpPath(self.AnscObj.DF_SCP_OUT_TOWER_PATH, Tower_out_Dir)

        # /{storage}/{organization_id}/{workspace_id}/driver/ansible/{legacy / pioneer / legacy_role}/{ 作業番号 }/out
        self.setTowerProjectsScpPath(self.AnscObj.DF_SCP_OUT_ITA_PATH, self.getAnsible_out_Dir())

        # Gitリポジトリ作業用 ディレクトリバス
        # /{storage}/{organization_id}/{workspace_id}/tmp/driver/ansible/legacy_0000040099/__ita_out_dir__
        path = "{}/{}".format(self.lv_GitRepo_temporary_DirAry["DIR_NAME"], self.LC_ITA_OUT_DIR)
        self.setTowerProjectsScpPath(self.AnscObj.DF_GITREPO_OUT_PATH, path)

        # ユーザー公開用データリレイストレージパス
        # /{storage}/{organization_id}/{workspace_id}/driver/ansible/{legacy / pioneer / legacy_role}/作業番号/out/user_files
        user_out_Dir = "{}/{}".format(c_outdir, self.LC_ANS_OUTDIR_DIR)
        os.mkdir(user_out_Dir)
        os.chmod(user_out_Dir, 0o777)

        # ホスト変数定義ファイルに記載するパスなのでAnsible側のストレージパスに変更
        self.lv_user_out_Dir = self.setAnsibleSideFilePath(user_out_Dir, self.LC_ITA_OUT_DIR)

        # conductorからの起動か判定 ディレクトリはconductorバックヤードで作成済み
        if in_conductor_instance_no:
            ins_Path = in_conductor_instance_no
            # ユーザー公開用conductorインスタンス作業用 データリレイストレージパス
            if self.lv_exec_mode == self.AnscObj.DF_EXEC_MODE_ANSIBLE:
                self.lv_conductor_instance_Dir = "{}/{}".format(self.getAnsibleBaseDir('CONDUCTOR_STORAGE_PATH_ANS'), ins_Path)
            else:
                # Tower(/var/lib/awx/projects)ディレクトリへのファイル転送パス退避
                self.lv_conductor_instance_Dir = "{}/{}/{}/{}".format(self.getTowerProjectDirPath("ExastroPath"),
                                                                      self.LC_ITA_TMP_DIR, self.LC_ITA_CONDUCTOR_DIR, ins_Path)
                self.setTowerProjectsScpPath(self.AnscObj.DF_SCP_CONDUCTOR_TOWER_PATH, self.lv_conductor_instance_Dir)

                ita_conductor_instance_Dir = "{}/{}".format(self.getAnsibleBaseDir('CONDUCTOR_STORAGE_PATH_ITA'), ins_Path)
                self.setTowerProjectsScpPath(self.AnscObj.DF_SCP_CONDUCTOR_ITA_PATH, ita_conductor_instance_Dir)

                # Gitリポジトリ作業用 ディレクトリバス
                path = "{}/{}/{}/{}".format(self.lv_GitRepo_temporary_DirAry["DIR_NAME"], self.LC_ITA_TMP_DIR, self.LC_ITA_CONDUCTOR_DIR, ins_Path)
                self.setTowerProjectsScpPath(self.AnscObj.DF_GITREPO_CONDUCTOR_PATH, path)
        else:
            self.lv_conductor_instance_Dir = self.lv_user_out_Dir
        
        # /{storage}/{organization_id}/{workspace_id}/driver/ansible/{legacy / pioneer / legacy_role}/作業番号/in
        # inディレクトリ作成
        c_indir = aryRetAnsibleWorkingDir[3]
        if os.path.isdir(c_indir) is False:
            os.mkdir(c_indir)
        # ansible.cfgを配置した場合の考慮
        os.chmod(c_indir, 0o755)

        # INディレクトリ名を記憶
        self.setAnsible_in_Dir(c_indir)

        # ドライバ区分がLEGACYの場合にchild_playbooksディレクトリ作成
        if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID:
            # child_playbooksディレクトリ作成
            c_dirwk = c_indir + "/" + self.LC_ANS_CHILD_PLAYBOOKS_DIR
            os.mkdir(c_dirwk)
            os.chmod(c_dirwk, 0o777)

            # child_playbooksディレクトリ名を記憶
            self.setAnsible_child_playbooks_Dir(c_dirwk)

            #  PlayBook内 子PlayBookパスを記憶
            self.setPlaybook_child_playbooks_Dir(self.LC_ANS_CHILD_PLAYBOOKS_DIR)

        # template_filesディレクトリ作成
        c_dirwk = c_indir + "/" + self.LC_ANS_TEMPLATE_FILES_DIR
        os.mkdir(c_dirwk)
        os.chmod(c_dirwk, 0o777)
        self.setAnsible_template_files_Dir(c_dirwk)

        # ホスト変数ファイル内 template_filesディレクトリパスを記憶
        self.setHostvarsfile_template_file_Dir(c_dirwk)

        # ドライバ区分がLEGACYかPioneer、ROLEの場合にcopy_filesディレクトリを作成する。
        # copy_filesディレクトリ作成
        c_dirwk = c_indir + "/" + self.LC_ANS_COPY_FILES_DIR
        os.mkdir(c_dirwk)
        os.chmod(c_dirwk, 0o777)
        self.setAnsible_copy_files_Dir(c_dirwk)
        
        self.setHostvarsfile_copy_file_Dir(c_dirwk)

        # upload_filesディレクトリ作成
        c_dirwk = c_indir + "/" + self.LC_ANS_UPLOAD_FILES_DIR
        os.mkdir(c_dirwk)
        os.chmod(c_dirwk, 0o777)
        self.setAnsible_upload_files_Dir(c_dirwk)

        # ssh_key_filesディレクトリ作成
        c_dirwk = c_indir + "/" + self.LC_ANS_SSH_KEY_FILES_DIR
        os.mkdir(c_dirwk)
        os.chmod(c_dirwk, 0o777)
        self.setAnsible_ssh_key_files_Dir(c_dirwk)

        # win_ca_filesディレクトリ作成
        c_dirwk = c_indir + "/" + self.LC_ANS_WIN_CA_FILES_DIR
        os.mkdir(c_dirwk)
        os.chmod(c_dirwk, 0o777)
        self.setAnsible_win_ca_files_Dir(c_dirwk)

        # ドライバ区分がPIONEERの場合にdialog_filesディレクトリ作成
        if self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
            # Pioneerの処理を追加
            pass

        # グローバル変数管理からグローバル変数の情報を取得
        self.lva_global_vars_list = {}
        retAry = self.getDBGlobalVarsMaster(self.lva_global_vars_list)
        ret = retAry[0]
        self.lva_global_vars_list = retAry[1]
        if ret is False:
            # ITAANSIBLEH-ERR-90235
            msgstr = g.appmsg.get_api_message("MSG-10458", [])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list

        # ドライバ区分がLegacy-Roleの場合
        # 作業パターンIDに紐づくパッケージファイルを取得
        # パッケージファイルをZIPファイルをinディレクトリに解凍し
        # 不要なファイルを削除する。
        if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
            # 作業パターンIDに紐づくパッケージファイルを取得
            retAry = self.getRolePackageFile(in_pattern_id)
            ret = retAry[0]
            mt_role_rolepackage_id = retAry[1]
            role_package_file = retAry[2]
            if ret is False:
                return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list

            roleObj = CheckAnsibleRoleFiles(self.lv_objMTS)

            # ロールパッケージファイル名(ZIP)を取得
            zipfile = self.getAnsible_RolePackage_file(mt_role_rolepackage_id, role_package_file)
            # del pkey = ""

            # ロールパッケージファイル名(ZIP)の存在確認
            if os.path.isfile(zipfile) is False:
                #
                msgstr = g.appmsg.get_api_message("MSG-10262", [mt_role_rolepackage_id, role_package_file])
                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                   str(inspect.currentframe().f_lineno), msgstr)
                return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list

            # inディレクトリにロールパッケージファイル(ZIP)展開
            del_flag = False
            if roleObj.ZipextractTo(zipfile, self.getAnsible_in_Dir(), del_flag) is False:
                arryErrMsg = roleObj.getlasterror()
                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                   str(inspect.currentframe().f_lineno), arryErrMsg[0])
                return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list
            else:
                # ローカル変数のリスト作成
                system_vars = self.setITALocalVars()

                mt_def_vars_list = {}
                err_vars_list = {}
                def_varsval_list = {}
                self.lva_cpf_vars_list = {}
                self.lva_tpf_vars_list = {}
                ITA2User_var_list = {}
                User2ITA_var_list = {}
                comb_err_vars_list = {}

                # self.lva_cpf/tpf_vars_listの構造
                # lva_cpf_vars_list[ロール名][ロール名/--/Playbook名][行番号][変数名] = 1
                # lva_tpf_vars_list[ロール名][ロール名/--/Playbook名][行番号][変数名] = 1
                retList = roleObj.chkRolesDirectory(self.getAnsible_in_Dir(),
                                                    system_vars,
                                                    "",
                                                    mt_def_vars_list,
                                                    err_vars_list,
                                                    def_varsval_list,
                                                    mt_def_array_vars_list,
                                                    # ロール内のplaybookからcopy変数を抽出する。
                                                    True,
                                                    self.lva_cpf_vars_list,
                                                    True,
                                                    self.lva_tpf_vars_list,
                                                    ITA2User_var_list,
                                                    User2ITA_var_list,
                                                    comb_err_vars_list,
                                                    True)
                ret = retList[0]
                mt_def_vars_list = retList[1]
                err_vars_list = retList[2]
                def_varsval_list = retList[3]
                mt_def_array_vars_list = retList[4]
                self.lva_cpf_vars_list = retList[5]
                self.lva_tpf_vars_list = retList[6]
                ITA2User_var_list = retList[7]
                User2ITA_var_list = retList[8]
                comb_err_vars_list = retList[9]

                if ret is False:
                    # ロール内の読替表で読替変数と任意変数の組合せが一致していない
                    if len(comb_err_vars_list) != 0:
                        msgObj = DefaultVarsFileAnalysis(self.objMTS)
                        strErrMsg = msgObj.TranslationTableCombinationErrmsgEdit(False, comb_err_vars_list)
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), strErrMsg)
                        return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list
                    # defaults定義ファイルに定義されている変数で属性が違う変数がある場合
                    elif len(err_vars_list) != 0:
                        msgObj = DefaultVarsFileAnalysis(self.objMTS)
                        strErrMsg = msgObj.VarsStructErrmsgEdit(err_vars_list)
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), strErrMsg)
                        return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list
                    else:
                        arryErrMsg = roleObj.getlasterror()
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), arryErrMsg[0])
                        return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list
                
                # 作業パターンIDに紐づけられているロール名取得
                w_RoleInfoList = []
                w_RoleNameList = []
                retAry = self.getDBLegactRoleList(in_pattern_id, w_RoleInfoList)
                ret = retAry[0]
                w_RoleInfoList = retAry[1]
                if ret is False:
                    return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list
                    
                w_RoleNameList = []
                for seq_no, role_info in w_RoleInfoList.items():
                    for role_id, role_name in role_info.items():
                        w_RoleNameList.append(role_name)
                
                # 紐づけされていないロールで使用しているCopy変数を
                # self.lva_cpf_vars_listから取り除く
                self.lva_cpf_vars_list = self.DeleteUnuseData(self.lva_cpf_vars_list, w_RoleNameList)

                # 紐づけされていないロールで使用しているTemplate変数を
                # self.lva_tpf_vars_listから取り除く
                self.lva_tpf_vars_list = self.DeleteUnuseData(self.lva_tpf_vars_list, w_RoleNameList)

                # 紐づけされていないロールで使用しているグローバル変数を
                # mt_roleglobalvarsから取り除く
                mt_roleglobalvars = roleObj.getglobalvarname()
                if len(mt_roleglobalvars) == 0:
                    mt_roleglobalvars = {}
                mt_roleglobalvars = self.DeleteUnuseData(mt_roleglobalvars, w_RoleNameList)

                chkObj = DefaultVarsFileAnalysis(self.lv_objMTS)
                msgstr = ""
                # ロールパッケージ内のPlaybookで定義しているグローバル変数がグローバル変数管理にあるか
                retAry = chkObj.chkDefVarsListPlayBookGlobalVarsList(mt_roleglobalvars, self.lva_global_vars_list, msgstr)
                ret = retAry[0]
                msgstr = retAry[1]
                if ret is False:
                    #
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list

                del chkObj

                # copy変数がファイル管理に登録されているか判定
                strErrMsg = ""
                objLibs = AnsibleCommonLibs(self.AnscObj.LC_RUN_MODE_STD)

                # self.lva_cpf_vars_listの構造 CONTENTS_FILE_ID/CONTENTS_FILEはchkCPFVarsMasterRegの戻り値
                # lva_cpf_vars_list[ロール名][ロール名/--/Playbook名][行番号][変数名]['CONTENTS_FILE_ID'] = Pkey
                # lva_cpf_vars_list[ロール名][ロール名/--/Playbook名][行番号][変数名]['CONTENTS_FILE'] = ファイル名
                
                retAry = objLibs.chk_cpf_vars_master_reg(self.lva_cpf_vars_list, self.lv_objDBCA)
                ret = retAry[0]
                self.lva_cpf_vars_list = retAry[1]
                strErrMsg = retAry[2]
                if ret is False:
                    #
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), strErrMsg)
                    return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list

                # template変数がファイル管理に登録されているか判定
                strErrMsg = ""

                retAry = objLibs.chk_tpf_vars_master_reg(self.lva_tpf_vars_list, self.lv_objDBCA)
                ret = retAry[0]
                self.lva_tpf_vars_list = retAry[1]
                strErrMsg = retAry[2]
                if ret is False:
                    #
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), strErrMsg)
                    return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list

                # テンプレート管理に登録されている変数情報取得
                # ina_tpf_vars_list[role_name][tgt_file][line_no][tpf_var_name]['VAR_STRUCT_ANAL_JSON_STRING']
                temlate_ctl_gbl_vars_list = {}
                for rolename, tpfinfo_1 in self.lva_tpf_vars_list.items():
                    for filename, tpfinfo_2 in tpfinfo_1.items():
                        for line_no, tpfinfo_3 in tpfinfo_2.items():
                            for tpf_var_name, tpfinfo_4 in tpfinfo_3.items():
                                if 'VAR_STRUCT_ANAL_JSON_STRING' in tpfinfo_4:
                                    pass
                                else:
                                    continue

                                JsonObj = VarStructAnalJsonConv()

                                # Jsonでエンコードされている変数情報をデコードする
                                retAry = JsonObj.TemplateVarStructAnalJsonLoads(tpfinfo_4['VAR_STRUCT_ANAL_JSON_STRING'])

                                # unuse Vars_list = retAry[0]
                                # unuse Array_vars_list = retAry[1]
                                # unuse LCA_vars_use = retAry[2]
                                # unuse Array_vars_use = retAry[3]
                                # unuse VarVal_list = retAry[5]
                                GBL_vars_info = retAry[4]
                                if len(GBL_vars_info) == 0:
                                    GBL_vars_info = {}
                                
                                # ロール内で使用しているTPF変数で、テンプレート管理の変数定義に登録されているグローバル変数を抜き出す。
                                for dummy, gblinfo_1 in GBL_vars_info.items():
                                    for gbl_var_name, dummy in gblinfo_1.items():
                                        # テンプレート管理の変数定義に登録されているグローバル変数をマーク
                                        if rolename not in temlate_ctl_gbl_vars_list:
                                            temlate_ctl_gbl_vars_list[rolename] = {}
                                        if gbl_var_name not in temlate_ctl_gbl_vars_list[rolename]:
                                            temlate_ctl_gbl_vars_list[rolename][gbl_var_name] = 0
                                        if gbl_var_name not in self.lv_use_gbl_vars_list:
                                            self.lv_use_gbl_vars_list[gbl_var_name] = 0

                # ロール内で使用しているTPF変数で、テンプレート管理の変数定義に登録されているグローバル変数がグローバル変数管理に登録されているか判定
                chkObj = DefaultVarsFileAnalysis(self.lv_objMTS)
                msgstr = ""
                
                retAry = chkObj.chkDefVarsListPlayBookGlobalVarsList(temlate_ctl_gbl_vars_list, self.lva_global_vars_list, msgstr)
                ret = retAry[0]
                msgstr = retAry[1]
                if ret is False:
                    #
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    return False, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list

                # ロール名取得
                # ina_rolename[role名]
                mt_rolenames = roleObj.getrolename()
                # ロール内の変数取得
                # ina_varname[role名][変数名]=0
                mt_rolevars = roleObj.getvarname()

            # 展開先にhostsファイルがあれば削除する。
            path = "{}/{}".format(c_indir, self.LC_ANS_HOSTS_FILE)
            is_file = os.path.isfile(path)
            if is_file is True:
                os.remove(path)

            # 展開先にホスト変数ディレクトリがあれば削除する。
            path = "{}/{}".format(c_indir, self.LC_ANS_HOST_VARS_DIR)
            is_dir = os.path.isdir(path)
            if is_dir is True:
                shutil.rmtree(path)

            # 展開先にホストグループ変数ディレクトリがあれば削除する。
            path = "{}/{}".format(c_indir, self.LC_ANS_GROUP_VARS_DIR)
            is_dir = os.path.isdir(path)
            if is_dir is True:
                shutil.rmtree(path)

            # ITA独自ディレクトリの存在を確認し削除
            path = "{}/{}".format(c_indir, self.LC_ITA_OUT_DIR)
            is_dir = os.path.isdir(path)
            if is_dir is True:
                shutil.rmtree(path)

            path = "{}/{}".format(c_indir, self.LC_ITA_TMP_DIR)
            is_dir = os.path.isdir(path)
            if is_dir is True:
                shutil.rmtree(path)

        # host_varsディレクトリ作成
        c_dirwk = "{}/{}".format(c_indir, self.LC_ANS_HOST_VARS_DIR)
        os.mkdir(c_dirwk)
        os.chmod(c_dirwk, 0o777)

        # host_varsディレクトリ名を記憶
        self.setAnsible_host_vars_Dir(c_dirwk)

        # tmpディレクトリ作成
        c_tmpdir = "{}/{}".format(c_dir, self.LC_ANS_TMP_DIR)
        if os.path.isdir(c_tmpdir) is False:
            os.mkdir(c_tmpdir)
        os.chmod(c_tmpdir, 0o777)

        # tmpディレクトリ名を記憶
        self.setAnsible_tmp_Dir(c_tmpdir)

        # Tower(/var/lib/awx/projects)ディレクトリへのファイル転送パス退避
        Tower_tmp_Dir = "{}/{}".format(self.getTowerProjectDirPath("ExastroPath"), self.LC_ITA_TMP_DIR)
        self.setTowerProjectsScpPath(self.AnscObj.DF_SCP_TMP_TOWER_PATH, Tower_tmp_Dir)
        self.setTowerProjectsScpPath(self.AnscObj.DF_SCP_TMP_ITA_PATH, self.getAnsible_tmp_Dir())

        # Gitリポジトリ作業用 ディレクトリバス
        path = "{}/{}".format(self.lv_GitRepo_temporary_DirAry["DIR_NAME"], self.LC_ITA_TMP_DIR)
        self.setTowerProjectsScpPath(self.AnscObj.DF_GITREPO_TMP_PATH, path)

        # Tower用のconductorディレクトリ生成
        if in_conductor_instance_no:
            if self.lv_exec_mode == self.AnscObj.DF_EXEC_MODE_ANSIBLE:
                pass
            else:
                c_dirwk = "{}/{}".format(c_tmpdir, self.LC_ITA_CONDUCTOR_DIR)
                os.mkdir(c_dirwk)
                os.chmod(c_dirwk, 0o777)
                c_dirwk = "{}/{}/{}".format(c_tmpdir, self.LC_ITA_CONDUCTOR_DIR, in_conductor_instance_no)
                os.mkdir(c_dirwk)
                os.chmod(c_dirwk, 0o777)

        # ドライバ区分がPIONEERの場合にPIONEER用作業ディレクトリ作成処理は未実装

        # ansible-vault用ディレクトリ作成
        self.ansible_vault_password_file_dir = c_dir
        c_tmpdir = c_dir + "/.tmp"

        is_dir = os.path.isdir(c_tmpdir)
        if is_dir is False:
            os.mkdir(c_tmpdir)
            os.chmod(c_tmpdir, 0o777)

        self.setTemporary_file_Dir(c_tmpdir)

        # ansible実行時、aah-agentで必要なexpectファイルを所定の場所にコピーする。
        self.CopysshAgentExpectfile()

        return True, mt_rolenames, mt_rolevars, mt_roleglobalvars, mt_role_rolepackage_id, mt_def_vars_list, mt_def_array_vars_list

    def CreateAnsibleWorkingFiles(self,
                                  ina_hosts,
                                  ina_host_vars,
                                  ina_pioneer_template_host_vars,
                                  ina_vault_vars,
                                  ina_vault_host_vars_file_list,
                                  ina_child_playbooks, ina_dialog_files,
                                  ina_rolenames,
                                  ina_role_rolenames,
                                  ina_role_rolevars,
                                  ina_role_roleglobalvars,
                                  ina_hostinfolist,
                                  ina_host_child_vars,
                                  ina_DB_child_vars_master,
                                  ina_MultiArray_vars_list,
                                  ina_def_vars_list,
                                  ina_def_array_vars_list,
                                  in_exec_mode,
                                  in_exec_playbook_hed_def,
                                  in_exec_option):
        """
        ansible用各作業ファイルを作成
        Arguments:
            ina_hosts:              機器一覧ホスト一覧
                                    {SYSTEM_ID:HOST_NAME}, , ,
            ina_host_vars:          ホスト変数配列
                                    [ホスト名][ 変数名 ]=>具体値
            ina_pioneer_template_host_vars:
                                    ホスト変数配列 pioneer template用 変数一覧返却配列 (passwordColumnの具体値がansible-vaultで暗号化)
                                    [ホスト名][ 変数名 ]=>具体値
            vault_vars:             PasswordCoulumn変数一覧(Pioneer用)
                                    [ 変数名 ] = << 変数名 >>
            ina_vault_host_vars_file_list:  PasswordCoulumn変数のみのホスト変数一覧(Pioneer用)
                                            [ホスト名(IP)][ 変数名 ] = 具体値
            ina_child_playbooks:    子PlayBookファイル配列
                                    [INCLUDE順序][素材管理Pkey]=>素材ファイル
                                    ※Legacyの場合のみ必須
            ina_dialog_files:       対話ファイル配列
                                    [ホスト名][INCLUDE順番][素材管理Pkey]=対話ファイル
                                    ※Pioneerの場合のみ必須
            ina_rolenames:          ロール名リスト配列(データベースの登録内容)
                                    ※Legacy-Roleの場合のみ必須
                                    [実行順序][ロールID(Pkey)]=>ロール名
            ina_role_rolenames:     ロール名リスト配列(Role内登録内容)
                                    ※Legacy-Roleの場合のみ必須
                                    [ロール名]
            ina_role_rolevars:      ロール内変数リスト配列(Role内登録内容)
                                    ※Legacy-Roleの場合のみ必須
                                    [ロール名][変数名]=0
            ina_role_roleglobalvars:    ロール内グローバル変数リスト配列(Role内登録内容)
                                        ※Legacy-Roleの場合のみ必須
                                        [ロール名][グローバル変数名]=0
            ina_hostinfolist:       機器一覧ホスト情報
                                    {HOST_NAME:{機器一覧各項目:xx, ....}} ...
            ina_host_child_vars:    配列変数一覧返却配列(変数一覧に配列変数含む)
                                    [ホスト名][ 変数名 ][列順序][メンバー変数]=[具体値]
            ina_DB_child_vars_master:
                                    メンバー変数マスタの配列変数のメンバー変数リスト返却
                                    [変数名][メンバー変数名]=0
            in_exec_mode:           実行エンジン
                                    1: Ansible  2: Ansible Tower
            in_exec_playbook_hed_def: 親playbookヘッダセクション
            in_exec_option:           予約
        Returns:
            bool
        """
        self.lv_hostinfolist = ina_hostinfolist

        # 追加された予約変数生成
        retAry = self.CreateOperationVariables(self.run_operation_id, ina_hostinfolist, ina_host_vars, ina_pioneer_template_host_vars)
        ret = retAry[0]
        ina_host_vars = retAry[1]
        ina_pioneer_template_host_vars = retAry[2]
        if ret is False:
            return False

        # Pioneer LANG用 ローカル変数設定
        retAry = self.CreatePioneerLANGVariables(ina_hostinfolist, ina_host_vars)
        ret = retAry[0]
        ina_host_vars = retAry[1]
        if ret is False:
            return False

        # 収集機能用ディレクトリ生成/ホスト変数生成
        retAry = self.CreateDirectoryForCollectionProcess(ina_hostinfolist, ina_host_vars, ina_pioneer_template_host_vars)
        ret = retAry[0]
        ina_host_vars = retAry[1]
        ina_pioneer_template_host_vars = retAry[2]
        if ret is False:
            return False

        # Movmentインスタンスステータスファイル変数生成
        retAry = self.CreateMovementStatusFileVariables(ina_hostinfolist, ina_host_vars, ina_pioneer_template_host_vars)
        ret = retAry[0]
        ina_host_vars = retAry[1]
        ina_pioneer_template_host_vars = retAry[2]
        if ret is False:
            return False

        # Movmentロールに紐づいているグローバル変数を退避
        if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
            for rokename, global_vars_array in ina_role_roleglobalvars.items():
                for gbl_vars_name, dummy in global_vars_array.items():
                    if gbl_vars_name not in self.lv_use_gbl_vars_list:
                        self.lv_use_gbl_vars_list[gbl_vars_name] = {}
        
        # hostsファイル作成
        pioneer_sshkeyfilelist = {}
        pioneer_sshextraargslist = {}
        # retAry = self.CreateHostsfile(ina_hosts, ina_hostprotcollist, ina_hostinfolist,  pioneer_sshkeyfilelist,  pioneer_sshextraargslist)
        retAry = self.CreateHostsfile(ina_hosts, ina_hostinfolist, pioneer_sshkeyfilelist, pioneer_sshextraargslist)
        ret = retAry[0]
        pioneer_sshkeyfilelist = retAry[1]
        pioneer_sshextraargslist = retAry[2]
        if ret is False:
            return False

        # ドライバ区分を判定
        if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID:
            # Legacyの処理を追加
            pass

        elif self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
            # Pioneerの処理を追加
            pass

        elif self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
            # ホスト変数定義ファイル作成
            if self.CreateRoleHostvarsfiles(ina_host_vars, ina_MultiArray_vars_list, ina_def_vars_list, ina_def_array_vars_list) is False:
                return False

            # Role内で使用しているcopyモジュール変数をホスト変数定義ファイルに追加
            if self.CreateLegacyRoleCopyFiles(ina_hosts, ina_rolenames, self.lva_cpf_vars_list) is False:
                return False

            # Role内で使用しているtemplateモジュール変数をホスト変数定義ファイルに追加
            if self.CreateLegacyRoleTemplateFiles(ina_hosts, ina_rolenames, self.lva_tpf_vars_list) is False:
                return False

        # ドライバ区分を判定
        if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID:
            # Legacyの処理を追加
            pass

        elif self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
            # Pioneerの処理を追加
            pass

        elif self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
            # Legacy-Role PlayBookファイル作成
            if self.CreateLegacyRolePlaybookfiles(ina_rolenames, in_exec_mode, in_exec_playbook_hed_def) is False:
                return False

            # ロール内の変数定義チェック
            if self.CheckLegacyRolePlaybookfiles(ina_hosts,
                                                 ina_host_vars,
                                                 ina_rolenames,
                                                 ina_role_rolenames,
                                                 ina_role_rolevars,
                                                 ina_role_roleglobalvars) is False:
                return False

        # Movement一覧にAnsible Config Fileが設定されている場合にin配下にコピー
        if self.lv_ansible_cnf_file:
            if self.CopyAnsibleConfigFile() is False:
                return False
        return True

    def CreateHostsfile(self, ina_hosts, ina_hostinfolist, mt_pioneer_sshkeyfilelist, mt_pioneer_sshextraargslist):
        """
        hostsファイルを作成する。
        Arguments:
            ina_hosts:                      機器一覧ホスト一覧
            ina_hostinfolist:               機器一覧ホスト情報
            ina_sshkeyfilelist:             SSHSSH秘密鍵ファイルリスト(pioneer専用)
            ina_pioneer_sshextraargslist:   SSH_EXTRA_ARGSリスト(pioneer専用)
        Returns:
            bool, mt_pioneer_sshkeyfilelist mt_pioneer_sshextraargslist
        """
        mt_pioneer_sshkeyfilelist = {}
        mt_pioneer_sshextraargslist = {}

        CreateSSHAgentConfigInfoFile = False
        # ssh-agentの設定に必要な情報を一時ファイル削除
        SSHAgentConfigInfoFile = "{}/{}".format(self.getTemporary_file_Dir(), self.LC_ANS_SSHAGENTCONFIG_FILE)

        file_name = self.getAnsible_hosts_file()
        fd = open(file_name, "w")

        # 固定ファイル出力
        header = ""
        header += "all:\n"
        header += "  children:\n"
        header += "    hostgroups:\n"
        header += "      hosts:\n"
        
        fd.write(header)

        spaceStr = ""
        indento_sp_host = spaceStr.ljust(8)
        indento_sp_param = spaceStr.ljust(10)
        indento_sp12 = spaceStr.ljust(24)
        for host_id, host_name in ina_hosts.items():
            ssh_extra_args = ""
            # ssh_extra_argsの設定の有無を判定しssh_extra_argsの内容を退避
            if ina_hostinfolist[host_name]['SSH_EXTRA_ARGS']:
                # "を\"に置き換え
                ssh_extra_args = ina_hostinfolist[host_name]['SSH_EXTRA_ARGS'].replace('\"', '\\"')
                if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID or \
                   self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
                    # hostsファイルに追加するssh_extra_argsを生成
                    ssh_extra_args = 'ansible_ssh_extra_args: "' + ssh_extra_args + '"'
                else:
                    # Pioneer用にssh_extra_argsを退避
                    mt_pioneer_sshextraargslist[host_name] = ssh_extra_args
                    ssh_extra_args = ""

            hosts_extra_args = ""
            if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID or self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
                # hosts_extra_argsの設定の有無を判定しhosts_extra_argsの内容を退避
                if ina_hostinfolist[host_name]['HOSTS_EXTRA_ARGS']:
                    #
                    errorDetail = ""
                    retAry = self.InventryFileAddOptionCheckFormat(ina_hostinfolist[host_name]['HOSTS_EXTRA_ARGS'], hosts_extra_args, errorDetail)
                    ret = retAry[0]
                    hosts_extra_args = retAry[1]
                    errorDetail = retAry[2]
                    if ret is False:
                        msgstr = g.appmsg.get_api_message("MSG-10625", [host_name, errorDetail])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        return False, mt_pioneer_sshkeyfilelist, mt_pioneer_sshextraargslist
                    # array->文字列に変換
                    hosts_extra_args = "<<<__TAB__>>>".join(hosts_extra_args)
                    hosts_extra_args = hosts_extra_args.replace("<<<__TAB__>>>", "\n" + indento_sp_param)

            param = ""
            passwd = ""
            port = ""

            # sshの接続パラメータ生成
            if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID or self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
                # ユーザー設定
                # enomoto  self.LC_ANS_UNDEFINE_NAMEでチェックしてるなか？
                # if ina_hostinfolist[host_name]['LOGIN_USER'] != self.LC_ANS_UNDEFINE_NAME):
                if ina_hostinfolist[host_name]['LOGIN_USER']:
                    param = "ansible_ssh_user: " + ina_hostinfolist[host_name]['LOGIN_USER']

                # パスワード設定
                if ina_hostinfolist[host_name]['LOGIN_AUTH_TYPE'] == self.AnscObj.DF_LOGIN_AUTH_TYPE_PW or\
                   ina_hostinfolist[host_name]['LOGIN_AUTH_TYPE'] == self.AnscObj.DF_LOGIN_AUTH_TYPE_PW_WINRM:
                    # パスワードが設定されているか WinRMの場合、パスワード未設定の場合あり
                    if ina_hostinfolist[host_name]['LOGIN_PW']:

                        # パスワード暗号化
                        make_vaultpass = self.makeAnsibleVaultPassword(
                            ina_hostinfolist[host_name]['LOGIN_PW'],
                            ina_hostinfolist[host_name]['LOGIN_PW_ANSIBLE_VAULT'],
                            indento_sp12,
                            ina_hostinfolist[host_name]['SYSTEM_ID'])
                        if make_vaultpass is False:
                            return False, mt_pioneer_sshkeyfilelist, mt_pioneer_sshextraargslist

                        passwd = "ansible_ssh_pass: " + make_vaultpass

                # Winrm接続情報
                if ina_hostinfolist[host_name]['LOGIN_AUTH_TYPE'] == self.AnscObj.DF_LOGIN_AUTH_TYPE_PW_WINRM:
                    # WINRM接続プロトコルよりポート番号が未設定時は、self.LC_WINRM_PORTが設定されている
                    port = "ansible_ssh_port: " + str(ina_hostinfolist[host_name]['WINRM_PORT'])
                    port += "\n" + indento_sp_param + "ansible_connection: winrm"

            ssh_key_file = ''
            win_ca_file = ''
            # 秘密鍵ファイルが必要な認証方式か判定
            if ina_hostinfolist[host_name]['LOGIN_AUTH_TYPE'] == self.AnscObj.DF_LOGIN_AUTH_TYPE_KEY or\
               ina_hostinfolist[host_name]['LOGIN_AUTH_TYPE'] == self.AnscObj.DF_LOGIN_AUTH_TYPE_KEY_PP_USE:
                if ina_hostinfolist[host_name]['SSH_KEY_FILE']:
                    # 機器一覧にSSH鍵認証ファイルが登録されている場合はSSH鍵認証ファイルをinディレクトリ配下にコピーする。
                    retAry = self.CreateSSH_key_file(ina_hostinfolist[host_name]['SYSTEM_ID'], ina_hostinfolist[host_name]['SSH_KEY_FILE'])
                    ret = retAry[0]
                    ssh_key_file_path = retAry[1]
                    if ret is not True:
                        return False, mt_pioneer_sshkeyfilelist, mt_pioneer_sshextraargslist

                    # ansible実行時のパスに変更
                    ssh_key_file_path = self.setAnsibleSideFilePath(ssh_key_file_path, self.LC_ITA_IN_DIR)
                    # 秘密鍵認証の場合にssh-agntでパスフレーズの入力を省略する為の情報生成
                    if ina_hostinfolist[host_name]['LOGIN_AUTH_TYPE'] == self.AnscObj.DF_LOGIN_AUTH_TYPE_KEY_PP_USE:
                        if ina_hostinfolist[host_name]["SSH_KEY_FILE_PASSPHRASE"]:
                            CreateSSHAgentConfigInfoFile = True

                            # ssh-agentの設定に必要な情報を一時ファイルに出力
                            if self.CreateSSHAgentConfigInfoFile(SSHAgentConfigInfoFile, ina_hostinfolist[host_name]["HOST_NAME"],
                                                                 ssh_key_file_path,
                                                                 ina_hostinfolist[host_name]["SSH_KEY_FILE_PASSPHRASE"]) is False:
                                return False, mt_pioneer_sshkeyfilelist, mt_pioneer_sshextraargslist
                    if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID or\
                       self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
                        # hostsファイルに追加するSSH鍵認証ファイルのパラメータ生成
                        ssh_key_file = 'ansible_ssh_private_key_file: ' + ssh_key_file_path
                    else:
                        mt_pioneer_sshkeyfilelist[host_name] = ssh_key_file_path

            elif ina_hostinfolist[host_name]['LOGIN_AUTH_TYPE'] == self.AnscObj.DF_LOGIN_AUTH_TYPE_PW_WINRM:
                if ina_hostinfolist[host_name]['WINRM_SSL_CA_FILE']:
                    # 機器一覧にサーバー証明書ファイルが登録されている場合はサーバー証明書ファイルをinディレクトリ配下にコピーする
                    retAry = self.CreateWIN_cs_file(ina_hostinfolist[host_name]['SYSTEM_ID'],
                                                    ina_hostinfolist[host_name]['WINRM_SSL_CA_FILE'])

                    ret = retAry[0]
                    win_ca_file_path = retAry[1]

                    if ret is not True:
                        return False, mt_pioneer_sshkeyfilelist, mt_pioneer_sshextraargslist

                    # ky_encryptで中身がスクランブルされているので、復元
                    ret = ky_file_decrypt(win_ca_file_path, win_ca_file_path)
                    if ret is False:
                        msgstr = g.appmsg.get_api_message("MSG-10646", [ina_hostinfolist[host_name]['SYSTEM_ID']])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        return False, mt_pioneer_sshkeyfilelist, mt_pioneer_sshextraargslist

                    # ansible実行時のパスに変更
                    win_ca_file_path = self.setAnsibleSideFilePath(win_ca_file_path, self.LC_ITA_IN_DIR)

                    if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID or\
                       self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
                        # hostsファイルに追加するサーバー証明書ファイルのパラメータ生成
                        win_ca_file = 'ansible_winrm_ca_trust_path: ' + win_ca_file_path

            now_host_name = ""
            host_name_string = ""
            # ホストアドレス方式がホスト名方式の場合はホスト名をhostsに登録する。
            # hostname:
            #   ansible_ssh_host: ip/dnshost
            #  1: ip  2: host
            if self.lv_hostaddress_type == "2":
                host_name_string = indento_sp_host + ina_hostinfolist[host_name]['HOST_NAME'] + ":\n"
                host_name_string += indento_sp_param + 'ansible_ssh_host: ' + ina_hostinfolist[host_name]['HOST_DNS_NAME'] + "\n"
                now_host_name = ina_hostinfolist[host_name]['HOST_DNS_NAME']
            else:
                # ホストアドレス方式がIPアドレスの場合
                host_name_string = indento_sp_host + ina_hostinfolist[host_name]['HOST_NAME'] + ":\n"
                host_name_string += indento_sp_param + 'ansible_ssh_host: ' + ina_hostinfolist[host_name]['IP_ADDRESS'] + "\n"

            # Pioneerでホスト名がlocalhostの場合に、インベントファイルに
            # ansible_connection: localを追加する
            if now_host_name == 'localhost' and self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
                host_name_string += indento_sp_param + "ansible_connection: local\n"

            if len(param) != 0:
                host_name_string += indento_sp_param + param + "\n"

            if len(passwd) != 0:
                host_name_string += indento_sp_param + passwd + "\n"

            if len(port) != 0:
                host_name_string += indento_sp_param + port + "\n"

            if len(ssh_key_file) != 0:
                host_name_string += indento_sp_param + ssh_key_file + "\n"

            if len(ssh_extra_args) != 0:
                host_name_string += indento_sp_param + ssh_extra_args + "\n"

            if len(hosts_extra_args) != 0:
                host_name_string += indento_sp_param + hosts_extra_args + "\n"

            if len(win_ca_file) != 0:
                host_name_string += indento_sp_param + win_ca_file + "\n"
            
            fd.write(host_name_string)

        fd.close()

        # ssh-agentの設定に必要な情報を一時ファイルをスクランブル
        if CreateSSHAgentConfigInfoFile is True:
            ret = ky_file_encrypt(SSHAgentConfigInfoFile, SSHAgentConfigInfoFile)
            if ret is False:
                #
                msgstr = g.appmsg.get_api_message("MSG-10297", [])
                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                   str(inspect.currentframe().f_lineno), msgstr)
                return False, mt_pioneer_sshkeyfilelist, mt_pioneer_sshextraargslist

        return True, mt_pioneer_sshkeyfilelist, mt_pioneer_sshextraargslist

    def DeleteUnuseData(self, srcData, chkList):
        '''
        辞書型配列から不要なデータを削除
        Arguments:
            srcData: 辞書型配列
            {ロール名: {ファイル名: {行番号: {変数名: 0},,,,}}}
            chkList: 辞書に必要なキーリスト
                    ['role1', 'role2']
        Returns:
            srcData
        '''
        for roleName in list(srcData.keys()):
            useFlag = False
            for useRoleName in chkList:
                if roleName == useRoleName:
                    useFlag = True
                    break
            if useFlag is False:
                del srcData[roleName]
        return srcData

    def InventryFileAddOptionCheckFormat(self, in_string, mt_yaml_array, mt_error_line):
        """
        インベントリファイル追加オプション(YAML形式)を検査
        Arguments:
            in_string: インベントリファイル追加オプション
            mt_yaml_array: インベントリファイル追加オプションを行単位にリスト化
            mt_yamlParse_error: YAML文法エラー時のエラー内容
        Returns:
            True/False, mt_yaml_array, mt_yamlParse_error
        """
        mt_yaml_array = in_string.split("\n")
        tmpFile = "{}/yamlParse_{}".format(get_AnsibleDriverTmpPath(), os.getpid())
        fd = open(tmpFile, 'w')
        fd.write(in_string)
        fd.close()
        obj = YamlParse()
        ret = obj.Parse(tmpFile)
        os.remove(tmpFile)
        if ret is False:
            mt_error_line = obj.GetLastError()
            return False, mt_yaml_array, mt_error_line
        return True, mt_yaml_array, mt_error_line

    def CreateRoleHostvarsfiles(self, ina_host_vars, ina_MultiArray_vars_list, def_vars_list, ina_def_array_vars_list):
        """
        ホスト変数ファイルを作成する。(Role専用)
        Arguments:
            ina_host_vars:        ホスト変数配列
            ina_MultiArray_vars_list:
            def_vars_list:
            ina_def_array_vars_list:
        Returns:
            True/False
        """
        # ホスト分繰返し
        for host_name in ina_host_vars.keys():
            host_vars_file = host_name
            file_name = self.getAnsible_host_var_file(host_vars_file)
            vars_list = ina_host_vars[host_name]

            # ホスト変数定義ファイル作成
            if self.CreateRoleHostvarsfile("VAR",
                                           file_name,
                                           vars_list,
                                           ina_MultiArray_vars_list,
                                           def_vars_list,
                                           ina_def_array_vars_list,
                                           host_name) is False:
                return False
        return True

    def CreateRoleHostvarsfile(self,
                               in_var_type,
                               in_file_name,
                               ina_var_list,
                               ina_MultiArray_vars_list,
                               ina_role_rolevars,
                               ina_def_array_vars_list,
                               in_host_name, in_mode="w"):
        """
        指定ホストのホスト変数定義ファイルを作成する。(Role専用)
        Arguments:
            in_var_type:        登録対象の変数タイプ  "VAR"/"CPF"
            in_file_name:       ホスト変数定義ファイル名
            ina_var_list:       ホスト変数配列
            ina_MultiArray_vars_list:
            ina_role_rolevars:
            ina_def_array_vars_list:
            in_host_name:
            in_mode:            書込モード
                                    "w":上書   デフォルト
                                    "a":追加
            
        Returns:
            True/False
        """
        parent_vars_list = {}

        # LegacyRoleCheckConcreteValueIsVarで必要な情報を退避
        self.LegacyRoleCheckConcreteValueIsVar_use_host_name = in_host_name
        if in_var_type == "VAR":
            if in_host_name not in self.LegacyRoleCheckConcreteValueIsVar_use_var_list:
                self.LegacyRoleCheckConcreteValueIsVar_use_var_list[in_host_name] = {}
            self.LegacyRoleCheckConcreteValueIsVar_use_var_list[in_host_name] = ina_var_list

        if in_host_name not in self.lv_legacy_Role_cpf_vars_list:
            self.lv_legacy_Role_cpf_vars_list[in_host_name] = {}
        if in_host_name not in self.lv_legacy_Role_tpf_vars_list:
            self.lv_legacy_Role_tpf_vars_list[in_host_name] = {}

        var_str = ""

        for var, val in ina_var_list.items():
            # 変数の重複出力防止
            if var in parent_vars_list:
                continue

            # 機器一覧のプロトコルが未登録の場合を判定
            if var == self.AnscObj.ITA_SP_VAR_ANS_PROTOCOL_VAR_NAME and val == self.LC_ANS_UNDEFINE_NAME:
                # __loginprotocol__をホスト変数に出力しない
                continue
            # コピー変数の重複出力防止
            if in_var_type == "CPF":
                if var in self.lv_legacy_Role_cpf_vars_list[in_host_name]:
                    continue
            # テンプレート変数の重複出力防止
            if in_var_type == "TPF":
                if var in self.lv_legacy_Role_tpf_vars_list[in_host_name]:
                    continue

            parent_vars_list[var] = 0

            # 機器一覧のパスワードをansible-vaultで暗号化
            if var == self.AnscObj.ITA_SP_VAR_ANS_PASSWD_VAR_NAME and val != self.LC_ANS_UNDEFINE_NAME:
                # ansible-vaultで暗号化された文字列のインデントを調整
                indento_sp4 = "".ljust(4)

                make_vaultpass = self.makeAnsibleVaultPassword(
                    val,
                    self.lv_hostinfolist[in_host_name]['LOGIN_PW_ANSIBLE_VAULT'],
                    indento_sp4,
                    self.lv_hostinfolist[in_host_name]['SYSTEM_ID'])
                if make_vaultpass is False:
                    return False
                
                val = make_vaultpass

            # ホスト変数ファイルのレコード生成
            # 変数名: 具体値
            NumPadding = 2
            edit_val = self.HostVarEdit(val, NumPadding)
            var_str += "{}: {}\n".format(var, edit_val)

            # 変数の具体値に使用しているテンプレート/コピー変数の情報を確認
            if in_var_type == "VAR":
                retAry = self.LegacyRoleCheckConcreteValueIsVar(val,
                                                                self.lv_legacy_Role_cpf_vars_list[in_host_name],
                                                                self.lv_legacy_Role_tpf_vars_list[in_host_name])
                ret = retAry[0]
                self.lv_legacy_Role_cpf_vars_list[in_host_name] = retAry[1]
                self.lv_legacy_Role_tpf_vars_list[in_host_name] = retAry[2]
                if ret is False:
                    # エラーメッセージは出力しているので、ここでは何も出さない。
                    return False

        # copy/templateモジュール変数のみ登録で呼ばれるケースの対応
        if in_mode == "w":
            parent_vars_list = {}
            MultiArrayVars_str = ""
            retAry = self.MultiArrayVarsToYamlFormatMain(
                ina_MultiArray_vars_list,
                MultiArrayVars_str,
                parent_vars_list,
                in_host_name,
                self.lv_legacy_Role_cpf_vars_list[in_host_name],
                self.lv_legacy_Role_tpf_vars_list[in_host_name])
            ret = retAry[0]
            MultiArrayVars_str = retAry[1]
            parent_vars_list = retAry[2]
            self.lv_legacy_Role_cpf_vars_list[in_host_name] = retAry[3]
            self.lv_legacy_Role_tpf_vars_list[in_host_name] = retAry[4]
            if ret is False:
                msgstr = g.appmsg.get_api_message("MSG-10457", [])
                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                   str(inspect.currentframe().f_lineno), msgstr)
                return False

            var_str += MultiArrayVars_str

            # グローバル変数をホスト変数ファイルに登録する。
            for var, val in self.lva_global_vars_list.items():
                # 作業パターンに紐づいているロール以外で使用しているグローバル変数を除外
                if var not in self.lv_use_gbl_vars_list:
                    continue

                # 二重処理防止
                if var in parent_vars_list:
                    continue

                parent_vars_list[var] = 0
            
                # 変数名: 具体値
                # 複数行具体値の場合に複数行の扱い記号を付ける
                edit_val = self.makeMultilineValue(val)

                NumPadding = 2
                out_val = self.MultilineValueEdit(edit_val, NumPadding)
                var_str += "{}: {}\n".format(var, out_val)

                # グローバル変数の具体値にコピー変数があるか確認
                retAry = self.LegacyRoleCheckConcreteValueIsVar(val,
                                                                self.lv_legacy_Role_cpf_vars_list[in_host_name],
                                                                self.lv_legacy_Role_tpf_vars_list[in_host_name])
                ret = retAry[0]
                self.lv_legacy_Role_cpf_vars_list[in_host_name] = retAry[1]
                self.lv_legacy_Role_tpf_vars_list[in_host_name] = retAry[2]
                if ret is False:
                    return False

            # "VAR"でしかこないルート 多段変数と他変数と同時に出力する。
            #  変数の具体値に使用しているコピー変数の情報をホスト変数ファイルに出力
            for var, val in self.lv_legacy_Role_cpf_vars_list[in_host_name].items():
                # 変数名: 具体値
                var_str += "{}: {}\n".format(var, val)

            # 変数の具体値に使用しているテンプレート変数の情報をホスト変数ファイルに出力
            for var, val in self.lv_legacy_Role_tpf_vars_list[in_host_name].items():
                # 変数名: 具体値
                var_str += "{}: {}\n".format(var, val)

        if var_str:
            fd = open(in_file_name, in_mode)

            fd.write(var_str)

            fd.close()

        return True

    # def CreateHostvarsfile(in_var_type, in_host_name,
    # def CreateVaultHostvarsfiles(ina_vault_host_vars_file_list, ina_host_vars, ina_hostprotcollist)
    def CreatePlaybookfile(self, in_file_name, ina_playbook_list, in_exec_mode, in_exec_playbook_hed_def):
        """
        親Playbook作成
        Arguments:
            in_file_name                親Playbookパス
            ina_playbook_list:          Roleの場合
                                        ロール名リスト配列
                                        {実行順序:{ロールID(Pkey):ロール名}}
            in_exec_mode:               実行エンジン
                                        1: Ansible  2: Ansible Tower
            in_exec_playbook_hed_def:   親playbookヘッダセクション
        Returns:
            True/False
        """

        fd = open(in_file_name, "w")
    
        # ドライバ区分判定
        value = ""
        if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID:
            # Legacyの処理を追加
            pass
        elif self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
            # Pioneerの処理を追加
            pass
        elif self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
            if not in_exec_playbook_hed_def:
                # if in_exec_mode == self.AnscObj.DF_EXEC_MODE_ANSIBLE:
                value = "- hosts: all\n"
                value += "  remote_user: \"{{ " + self.AnscObj.ITA_SP_VAR_ANS_USERNAME_VAR_NAME + " }}\"\n"
                value += "  gather_facts: no\n"

                # 対象ホストがwindowsか判別。windows以外の場合は become: yes を設定
                if self.lv_winrm_id != "1":
                    value += "  become: yes\n"
            else:
                value = in_exec_playbook_hed_def
                value += "\n"

            value = value + "\n"
            value = value + "  roles:\n"
        
        else:
            msgstr = g.appmsg.get_api_message("MSG-10082", [os.path.basename(__file__), self.lineno()])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False

        fd.write(value)
        value = ""
        for no, file_list in ina_playbook_list.items():
            for key, file in file_list.items():
                # ドライバ区分判定
                if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID:
                    # Legacyの処理を追加
                    pass
                elif self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
                    # Pioneerの処理を追加
                    pass
                elif self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
                    value += "    - role: " + file + "\n"
                else:
                    msgstr = g.appmsg.get_api_message("MSG-10082", [os.path.basename(__file__), self.lineno()])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    return False

        fd.write(value)
        fd.close()

        return True

    def setAnsibleDriverID(self, in_val):
        """
        Ansibleドライバ(legacy/pioneer/role)区分を記憶
        Arguments:
            in_val: Ansibleドライバ区分
                    legacy:       self.AnscObj.DF_LEGACY_DRIVER_ID
                    pioneer:      self.AnscObj.DF_PIONEER_DRIVER_ID
                    role:         self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID
        Returns:
            なし
        """
        self.lv_Ansible_driver_id = in_val

    def getAnsibleDriverID(self):
        """
        Ansibleドライバ(legacy/pioneer/role)区分を取得
        Arguments:
            なし
        Returns:
            Ansibleドライバ区分
            legacy:       self.AnscObj.DF_LEGACY_DRIVER_ID
            pioneer:      self.AnscObj.DF_PIONEER_DRIVER_ID
            role:         self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID
        """
        return self.lv_Ansible_driver_id

    def setAnsibleBaseDir(self, in_base_name, in_dir):
        """
        Ansible用 各種ベースディレクトリ名を記憶
        Arguments:
            in_base_name: 共有パス区分
                        ANSIBLE_SH_PATH_ITA:  Ansible作業用 ITA側
                        ANSIBLE_SH_PATH_ANS:  Ansible作業用 Ansible側
                        CONDUCTOR_STORAGE_PATH_ITA: conductor作業用 ITA側
                        CONDUCTOR_STORAGE_PATH_ANS: conductor作業用 Ansible側
            in_dir:       ベースディレクトリ
        Returns:
            なし
        """
        self.lv_Ansible_base_Dir[in_base_name] = in_dir

    def getAnsibleBaseDir(self, in_base_name):
        """
        Ansible用 各種ベースディレクトリ名を取得
        Arguments:
            in_base_name: 共有パス区分
                        ANSIBLE_SH_PATH_ITA:  Ansible作業用 ITA側
                        ANSIBLE_SH_PATH_ANS:  Ansible作業用 Ansible側
                        CONDUCTOR_STORAGE_PATH_ITA: conductor作業用 ITA側
                        CONDUCTOR_STORAGE_PATH_ANS: conductor作業用 Ansible側
        Returns:
            Ansible用 各種ベースディレクトリ名
        """
        return self.lv_Ansible_base_Dir[in_base_name]

    def setAnsible_in_Dir(self, in_indir):
        """
        作業実行inディレクトリパスを記憶
        Arguments:
            in_dir:   作業実行inディレクトリ
        Returns:
            なし
        """
        self.lv_Ansible_in_Dir = in_indir

    def getAnsible_in_Dir(self):
        """
        作業実行inディレクトリパスを取得
        Arguments:
            なし
        Returns:
            作業実行inディレクトリパス
        """
        return self.lv_Ansible_in_Dir

    def setAnsible_child_playbooks_Dir(self, in_indir):
        """
        作業実行inディレクトリ配下のchild_playbooksディレクトリパスを記憶
        Arguments:
            in_dir:      inディレクトリのchild_playbooksディレクトリパス
        Returns:
            なし
        """
        self.lv_Ansible_child_playbooks_Dir = in_indir

    def getAnsible_child_playbooks_Dir(self):
        """
        作業実行inディレクトリ配下のchild_playbooksディレクトリパスを取得
        Arguments:
            なし
        Returns:
            作業実行inディレクトリ配下のchild_playbooksディレクトリパス
        """
        return self.lv_Ansible_child_playbooks_Dir

    def setPlaybook_child_playbooks_Dir(self, in_dir):
        """
        親PlayBook内の子PlayBookディレクトリ格納ディレクトリ名「child_playbooks」を記憶
        Arguments:
            in_dir:      child_playbooks
        Returns:
            なし
        """
        self.lv_Playbook_child_playbooks_Dir = in_dir

    def getPlaybook_child_playbooks_Dir(self):
        """
        親PlayBook内の子PlayBookディレクトリ格納ディレクトリ名「child_playbooks」を取得
        Arguments:
            なし
        Returns:
            child_playbooks
        """
        return self.lv_Playbook_child_playbooks_Dir

    def setAnsible_dialog_files_Dir(self, in_indir):
        """
        作業実行inディレクトリ配下のdialog_filesディレクトリパスを記憶
        Arguments:
            in_dir:  作業実行inディレクトリリ配下のdialog_filesディレクトリパス
        Returns:
            なし
        """
        self.lv_Ansible_dialog_files_Dir = in_indir

    def getAnsible_dialog_files_Dir(self):
        """
        作業実行inディレクトリ配下のdialog_filesディレクトリパスを取得
        Arguments:
            なし
        Returns:
            作業実行inディレクトリリ配下のdialog_filesディレクトリパス
        """
        return self.lv_Ansible_dialog_files_Dir

    def setAnsible_host_vars_Dir(self, in_indir):
        """
        作業実行inディレクトリ配下のhost_varsディレクトリパスを記憶
        Arguments:
            in_dir:  作業実行inディレクトリリ配下のhost_varsディレクトリパス
        Returns:
            なし
        """
        self.lv_Ansible_host_vars_Dir = in_indir

    def getAnsible_host_vars_Dir(self):
        """
        作業実行inディレクトリ配下のhost_varsディレクトリパスを取得
        Arguments:
            なし
        Returns:
            作業実行inディレクトリリ配下のhost_varsディレクトリパス
        """
        return self.lv_Ansible_host_vars_Dir

    def setAnsible_out_Dir(self, in_indir):
        """
        作業実行outディレクトリパスを記憶
        Arguments:
            in_dir: 作業実行outディレクトリパス
        Returns:
            なし
        """
        self.lv_Ansible_out_Dir = in_indir

    def getAnsible_out_Dir(self):
        """
        作業実行outディレクトリパスを記憶
        Arguments:
            なし
        Returns:
            作業実行outディレクトリパス
        """
        return self.lv_Ansible_out_Dir

    def setAnsible_tmp_Dir(self, in_indir):
        """
        作業実行tmpディレクトリパスを記憶
        Arguments:
            in_dir: 作業実行tmpディレクトリパス
        Returns:
            なし
        """
        self.lv_Ansible_tmp_Dir = in_indir

    def getAnsible_tmp_Dir(self):
        """
        作業実行tmpディレクトリパスを記憶
        Arguments:
            なし
        Returns:
            作業実行tmpディレクトリパス
        """
        return self.lv_Ansible_tmp_Dir

    def setAnsible_original_dialog_files_Dir(self, in_indir):
        """
        作業実行tmpディレクトリ配下のoriginal_dialog_filesディレクトリパスを記憶
        Arguments:
            in_dir: 作業実行tmpディレクトリ配下のoriginal_dialog_filesディレクトリパス
        Returns:
            なし
        """
        self.lv_Ansible_original_dialog_files_Dir = in_indir

    def getAnsible_original_dialog_files_Dir(self):
        """
        作業実行tmpディレクトリ配下のoriginal_dialog_filesディレクトリパスを取得
        Arguments:
            なし
        Returns:
            作業実行tmpディレクトリ配下のoriginal_dialog_filesディレクトリパス
        """
        return self.lv_Ansible_original_dialog_files_Dir

    def setAnsible_in_original_dialog_files_Dir(self, in_indir):
        """
        作業実行inディレクトリ配下のoriginal_dialog_filesディレクトリパスを記憶
        Arguments:
            in_dir: 作業実行inディレクトリ配下のoriginal_dialog_filesディレクトリパス
        Returns:
            なし
        """
        self.lv_Ansible_in_original_dialog_files_Dir = in_indir

    def getAnsible_in_original_dialog_files_Dir(self):
        """
        作業実行inディレクトリ配下のoriginal_dialog_filesディレクトリパスを取得
        Arguments:
            なし
        Returns:
            作業実行inディレクトリ配下のoriginal_dialog_filesディレクトリパス
        """
        return self.lv_Ansible_in_original_dialog_files_Dir

    def setAnsible_original_hosts_vars_Dir(self, in_indir):
        """
        作業実行tmpディレクトリ配下のoriginal_hosts_varsディレクトリパスを記録
        Arguments:
            in_dir: 作業実行tmpディレクトリ配下のoriginal_hosts_varsディレクトリパス
        Returns:
            なし
        """
        self.lv_Ansible_original_hosts_vars_Dir = in_indir

    def getAnsible_original_hosts_vars_Dir(self):
        """
        作業実行tmpディレクトリ配下のoriginal_hosts_varsディレクトリパスを取得
        Arguments:
            なし
        Returns:
            作業実行tmpディレクトリ配下のoriginal_hosts_varsディレクトリパス
        """
        return self.lv_Ansible_original_hosts_vars_Dir

    def setAnsible_vault_hosts_vars_Dir(self, in_indir):
        """
        作業実行tmpディレクトリ配下のvault_host_varsディレクトリパスを記録
        暗号化された変数のみのホスト変数ファイル
        Arguments:
            in_dir: 作業実行tmpディレクトリ配下のvault_host_varsディレクトリパス
        Returns:
            なし
        """
        self.lv_Ansible_vault_hosts_vars_Dir = in_indir

    def getAnsible_vault_hosts_vars_Dir(self):
        """
        作業実行tmpディレクトリ配下のvault_host_varsディレクトリパスを取得
        暗号化された変数のみのホスト変数ファイル
        Arguments:
            なし
        Returns:
            作業実行tmpディレクトリ配下のvault_host_varsディレクトリパス
        """
        return self.lv_Ansible_vault_hosts_vars_Dir

    def setAnsible_pioneer_template_hosts_vars_Dir(self, in_indir):
        """
        作業実行tmpディレクトリ配下のpioneer template用 host_varsディレクトリパスを記録
        暗号化された変数のみのホスト変数ファイル
        Arguments:
            in_dir:  作業実行tmpディレクトリ配下のpioneer template用 host_varsディレクトリパス
        Returns:
            なし
        """
        self.lv_Ansible_pioneer_template_hosts_vars_Dir = in_indir

    def getAnsible_pioneer_template_hosts_vars_Dir(self):
        """
        作業実行tmpディレクトリ配下のpioneer template用 host_varsディレクトリパスを取得
        暗号化された変数のみのホスト変数ファイル
        Arguments:
            なし
        Returns:
            作業実行tmpディレクトリ配下のpioneer template用 host_varsディレクトリパス
        """
        return self.lv_Ansible_pioneer_template_hosts_vars_Dir

    # def setITA_child_playbook_Dir(in_indir):
    # def getITA_child_playbook_Dir():
    # def setITA_dialog_files_Dir(self, in_indir):
    # def getITA_dialog_files_Dir(self):
    # lv_ita_dialog_files_Dirと同様、util.pyにfunctionを用意する
    def getAnsible_hosts_file(self):
        """
        作業実行hostsファイル名を取得
        Arguments:
            なし
        Returns:
            作業実行hostsファイル名
        """
        file = self.getAnsible_in_Dir() + "/" + self.LC_ANS_HOSTS_FILE
        return file

    def getAnsible_playbook_file(self):
        """
        playbookファイル名を取得
        Arguments:
            なし
        Returns:
            playbookファイル名
        """
        file = self.getAnsible_in_Dir() + "/" + self.LC_ANS_PLAYBOOK_FILE
        return file

    def getAnsible_pioneer_template_host_var_file(self, in_hostname):
        """
        作業実行tmpディレクトリ配下のpioneer template用 host_vars/host毎のディレクトリを取得
        Arguments:
            in_hostname: ホスト名
        Returns:
            作業実行tmpディレクトリ配下のpioneer template用 host_vars/host毎のディレクトリ
        """
        file = "{}/{}".format(self.getAnsible_pioneer_template_hosts_vars_Dir(), in_hostname)
        return file

    def getAnsible_host_var_file(self, in_hostname):
        """
        作業実行inディレクトリ配下のhost_vars/host毎ディレクトリパスを取得
        Arguments:
            in_hostname: ホスト名
        Returns:
            作業実行inディレクトリ配下のhost_vars/host毎ディレクトリパス
        """
        file = "{}/{}".format(self.getAnsible_host_vars_Dir(), in_hostname)
        return file

    def getAnsible_org_host_var_file(self, in_hostname):
        """
        作業実行tmpディレクトリ配下のoriginal_hosts_vars/host毎ディレクトリパスを取得
        Arguments:
            in_hostname: ホスト名
        Returns:
            作業実行tmpディレクトリ配下のoriginal_hosts_vars/host毎ディレクトリパス
        """
        file = "{}/{}".format(self.getAnsible_original_hosts_vars_Dir(), in_hostname)
        return file

    def LocalLogPrint(self, file, line, errorMsg):
        """
        作業実行のエラーログ枠に紐づくファイル「作業実行/out/error.log」
        にエラーログを出力する。
        「「作業実行/out」ディレクトリが無い場合は標準出力にエラーログを出力する。
        Arguments:
            file: ファイル名
            line: 行番号
            errorMsg: エラーログ
        Returns:
            なし
        """
        logmsg = "File[{}:{}]{}".format(file, line, errorMsg)
        # エラーログファイルのパスが生成されている場合エラーログファイルにログ出力
        logfile = self.getAnsible_out_Dir() + "/" + "error.log"
        f = open(logfile, "a")
        f.write(errorMsg + "\n")
        f.close()
        # enomoto debug
        g.applogger.error(logmsg)

    def getDBHostList(self, in_execute_no, in_pattern_id, in_operation_id, mt_hostlist, mt_hostostypelist, mt_hostinfolist, in_winrm_id):
        """
        Ansible実行の対象機器情報をデータベースより取得する。
        Arguments:
            in_execute_no:      作業番号
            in_pattern_id:      作業パターンID
            in_operation_id:    オペレーションID
            mt_hostlist:        ホスト一覧
                                {機器一覧:SYSTEM_ID: 機器一覧:HOST_NAME},,
            mt_hostostypelist:  ホスト毎OS種別一覧  Pioneerの場合のみ
                                {機器一覧:HOST_NAME': 機器一覧:OS_TYPE_ID'}
            mt_hostinfolist:    {機器一覧:'HOST_NAME' {機器一覧:各項目: 値},,,},,,
            in_winrm_id:        Movement一覧のwinrm接続の設定値
                                "1": winrm接続選択
        Returns:
            True/False, mt_hostlist, mt_hostostypelist, mt_hostinfolist
        """
        mt_hostlist = {}
        mt_hostostypelist = {}
        mt_hostinfolist = {}

        # Movement一覧よりホスト指定形式を取得
        sql = "SELECT ANS_HOST_DESIGNATE_TYPE_ID  FROM {} WHERE MOVEMENT_ID=%s AND DISUSE_FLAG='0'".format(self.AnscObj.vg_ansible_pattern_listDB)
        rows = self.lv_objDBCA.sql_execute(sql, [in_pattern_id])
        if len(rows) == 0:
            #
            msgstr = g.appmsg.get_api_message("MSG-10382", [])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, mt_hostlist, mt_hostostypelist, mt_hostinfolist
        for row in rows:
            HostDesignateTypeId = row['ANS_HOST_DESIGNATE_TYPE_ID']
        
        # 機器一覧に対するDISUSE_FLAG = '0'の条件はSELECT文に入れない。
        sql = """
            SELECT
                TBL_1.PHO_LINK_ID,
                TBL_1.SYSTEM_ID AS PHO_HOST_ID,
                TBL_2.*,
                (
                SELECT
                    TBL_3.PROTOCOL_NAME
                FROM
                    T_ANSC_PIONEER_PROTOCOL_TYPE TBL_3
                WHERE
                    TBL_3.PROTOCOL_ID = TBL_2.PROTOCOL_ID AND
                    TBL_3.DISUSE_FLAG = '0'
                ) AS PROTOCOL_NAME
            FROM
                (
                SELECT
                    TBL_4.PHO_LINK_ID,
                    TBL_4.SYSTEM_ID
                FROM
                    {} TBL_4
                WHERE
                    TBL_4.EXECUTION_NO      = %s AND
                    TBL_4.DISUSE_FLAG       = '0'
                ) TBL_1
            LEFT OUTER JOIN T_ANSC_DEVICE TBL_2 ON ( TBL_1.SYSTEM_ID = TBL_2.SYSTEM_ID )
            ORDER BY TBL_2.HOST_NAME
            """.format(self.AnscObj.vg_ansible_pho_linkDB)

        rows = self.lv_objDBCA.sql_execute(sql, [in_execute_no])
        
        for row in rows:
            if row['DISUSE_FLAG'] == '0':
                mt_hostlist[row['SYSTEM_ID']] = {}
                mt_hostostypelist[row['HOST_NAME']] = {}
                mt_hostinfolist[row['HOST_NAME']] = {}
                
                # 認証方式の設定値確認
                login_auth_type = row['LOGIN_AUTH_TYPE']
                if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID or\
                   self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
                    #
                    # Movement一覧でwinrm接続が選択されている場合
                    # 機器一覧の認証方式がパスワード認証(winrm)以外か判定
                    if in_winrm_id == "1" and login_auth_type != self.AnscObj.DF_LOGIN_AUTH_TYPE_PW_WINRM:
                        #
                        msgstr = g.appmsg.get_api_message("MSG-10207", [row['HOST_NAME']])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        return False, mt_hostlist, mt_hostostypelist, mt_hostinfolist

                    # Movement一覧でwinrm接続が選択されていない場合
                    # 機器一覧の認証方式がパスワード認証(winrm)か判定
                    if in_winrm_id != "1" and login_auth_type == self.AnscObj.DF_LOGIN_AUTH_TYPE_PW_WINRM:
                        #
                        msgstr = g.appmsg.get_api_message("MSG-10208", [row['HOST_NAME']])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        return False, mt_hostlist, mt_hostostypelist, mt_hostinfolist

                if HostDesignateTypeId == "1":
                    # ホスト指定形式がIPの場合、機器一覧のIPアドレスが設定されているか判定
                    if not row['IP_ADDRESS']:
                        #
                        msgstr = g.appmsg.get_api_message("MSG-10690", [row['SYSTEM_ID']])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        return False, mt_hostlist, mt_hostostypelist, mt_hostinfolist
                else:
                    # ホスト指定形式がホストの場合、機器一覧のDNSホストが設定されているか判定
                    if not row['HOST_DNS_NAME']:
                        #
                        msgstr = g.appmsg.get_api_message("MSG-10691", [row['SYSTEM_ID']])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        return False, mt_hostlist, mt_hostostypelist, mt_hostinfolist

                # パスワード管理ありでパスワード退避
                if row['LOGIN_PW']:
                    # パスワード退避
                    row['LOGIN_PW'] = ky_decrypt(row['LOGIN_PW'])
                else:
                    # パスワード未設定を退避
                    row['LOGIN_PW'] = self.LC_ANS_UNDEFINE_NAME
                if row['SSH_KEY_FILE_PASSPHRASE']:
                    row['SSH_KEY_FILE_PASSPHRASE'] = ky_decrypt(row['SSH_KEY_FILE_PASSPHRASE'])

                if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID or\
                   self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
                    if not row['PROTOCOL_NAME']:
                        row['PROTOCOL_ID'] = self.LC_ANS_UNDEFINE_NAME
                    else:
                        row['PROTOCOL_ID'] = row['PROTOCOL_NAME']
                else:
                    row['PROTOCOL_ID'] = row['PROTOCOL_NAME']

                    # OS種別未入力判定
                    if not row['OS_TYPE_ID']:
                        #
                        msgstr = g.appmsg.get_api_message("MSG-10197", [row['SYSTEM_ID']])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        return False, mt_hostlist, mt_hostostypelist, mt_hostinfolist

                    # IPアドレス, OS種別の配列作成 pioneerの場合のみ作成
                    mt_hostostypelist[row['HOST_NAME']] = row['OS_TYPE_ID']

                # Pioneer LNAG のIDを文字コードに置換する
                if self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
                    #
                    if not row['PIONEER_LANG_ID']:
                        row['PIONEER_LANG_ID'] = "1"
                    lang_id2lang_str = {}
                    lang_id2lang_str["1"] = 'utf-8'
                    lang_id2lang_str["2"] = 'shift_jis'
                    lang_id2lang_str["3"] = 'euc_jp'
                    if row['PIONEER_LANG_ID'] in lang_id2lang_str:
                        row['PIONEER_LANG_STRING'] = lang_id2lang_str[row['PIONEER_LANG_ID']]
                    else:
                        msgstr = g.appmsg.get_api_message("MSG-10209", [row['HOST_NAME']])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        return False, mt_hostlist, mt_hostostypelist, mt_hostinfolist
                # 接続タイプが選択されていることを確認
                if not row['CREDENTIAL_TYPE_ID']:
                    #
                    msgstr = g.appmsg.get_api_message("MSG-10295", [row['HOST_NAME']])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    return False, mt_hostlist, mt_hostostypelist, mt_hostinfolist
                
                # ホスト名の配列作成
                mt_hostlist[row['SYSTEM_ID']] = row['HOST_NAME']

                # WINRM接続プロトコル配列作成
                if not row['WINRM_PORT']:
                    # WINRM接続プロトコルが空白の場合はデフォルト値を設定
                    row['WINRM_PORT'] = self.LC_WINRM_PORT

                mt_hostinfolist[row['HOST_NAME']] = row

            # 作業対象ホスト管理に登録されているホストが機器一覧に未登録
            else:
                #
                msgstr = g.appmsg.get_api_message("MSG-10183", [row['PHO_LINK_ID'], row['SYSTEM_ID']])
                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                   str(inspect.currentframe().f_lineno), msgstr)
                return False, mt_hostlist, mt_hostostypelist, mt_hostinfolist

        if len(rows) < 1:
            #
            msgstr = g.appmsg.get_api_message("MSG-10184", [in_pattern_id])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, mt_hostlist, mt_hostostypelist, mt_hostinfolist

        if len(mt_hostlist) < 1:
            #
            msgstr = g.appmsg.get_api_message("MSG-10185", [in_pattern_id])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, mt_hostlist, mt_hostostypelist, mt_hostinfolist
    
        return True, mt_hostlist, mt_hostostypelist, mt_hostinfolist

    def getDBRoleVarList(self, in_execute_no, in_pattern_id, in_operation_id, mt_host_vars, mt_MultiArray_vars_list, mt_All_vars_list):
        """
        ansibleで実行する変数をデータベースより取得する。(Role)
        Arguments:
            in_execute_no:           作業実行番号
            in_pattern_id:           MovementID
            in_operation_id:         オペレーションID
            mt_host_vars:            多段変数以外の変数リスト
            mt_MultiArray_vars_list: 多段変数リスト
            mt_All_vars_list:        未使用(I/Fを合わせる為に残す)
        Returns:
            bool, mt_host_vars, mt_MultiArray_vars_list, mt_All_vars_list
        """
        vars_assign_seq_list = {}
        # unuse child_vars_list = {}
        varerror_flg = True
        # B_ANSIBLE_LNS_PATTERN_VARS_LINKに対するDISUSE_FLAG = '0'の
        # 条件はSELECT文に入れない。
        sql = """
            SELECT
                TBL.*
            FROM
            (
            SELECT
                TBL_1.ASSIGN_ID,
                TBL_1.SYSTEM_ID,
                TBL_1.VARS_ENTRY,
                TBL_1.VARS_ENTRY_FILE,
                TBL_1.SENSITIVE_FLAG,
                TBL_1.ASSIGN_SEQ,
                TBL_2.VARS_NAME,
                TBL_2.VARS_ATTRIBUTE_01,
                TBL_1.COL_SEQ_COMBINATION_ID,
                TBL_3.COL_COMBINATION_MEMBER_ALIAS,
                TBL_4.ARRAY_MEMBER_ID,
                TBL_4.PARENT_VARS_KEY_ID,
                TBL_4.VARS_KEY_ID,
                TBL_4.VARS_NAME AS MEMBER_VARS_NAME,
                TBL_4.ARRAY_NEST_LEVEL,
                TBL_4.ASSIGN_SEQ_NEED,
                TBL_4.COL_SEQ_NEED,
                TBL_4.MEMBER_DISP,
                TBL_4.MAX_COL_SEQ,
                TBL_4.VRAS_NAME_PATH,
                TBL_4.VRAS_NAME_ALIAS,
                TBL_2.DISUSE_FLAG   AS PTN_VARS_LINK_DISUSE_FLAG,
                TBL_3.DISUSE_FLAG   AS MEMBER_COL_COMB_DISUSE_FLAG,
                TBL_4.DISUSE_FLAG   AS ARRAY_MEMBER_DISUSE_FLAG,
                (
                SELECT
                    COUNT(*)
                FROM
                    T_ANSR_TGT_HOST TBL_4
                WHERE
                    TBL_4.EXECUTION_NO      = %s                 AND
                    TBL_4.OPERATION_ID      = %s                 AND
                    TBL_4.MOVEMENT_ID       = %s                 AND
                    TBL_4.SYSTEM_ID         = TBL_1.SYSTEM_ID    AND
                    TBL_4.DISUSE_FLAG       = '0'
                ) AS PHO_LINK_HOST_COUNT,
                (
                SELECT
                    TBL_3.HOST_NAME
                FROM
                    T_ANSC_DEVICE TBL_3
                WHERE
                    TBL_3.SYSTEM_ID   = TBL_1.SYSTEM_ID          AND
                    TBL_3.DISUSE_FLAG = '0'
                ) AS HOST_NAME
            FROM
                (
                SELECT
                    TBL.ASSIGN_ID,
                    TBL.EXECUTION_NO,
                    TBL.SYSTEM_ID,
                    TBL.MVMT_VAR_LINK_ID,
                    TBL.COL_SEQ_COMBINATION_ID,
                    TBL.VARS_ENTRY,
                    TBL.VARS_ENTRY_FILE,
                    TBL.SENSITIVE_FLAG,
                    TBL.ASSIGN_SEQ
                FROM
                    T_ANSR_VALUE TBL
                WHERE
                    TBL.EXECUTION_NO = %s AND
                    TBL.OPERATION_ID = %s AND
                    TBL.MOVEMENT_ID  = %s AND
                    TBL.DISUSE_FLAG  = '0'
                ) TBL_1
            LEFT OUTER JOIN T_ANSR_MVMT_VAR_LINK            TBL_2 ON ( TBL_1.MVMT_VAR_LINK_ID       =
                                                                       TBL_2.MVMT_VAR_LINK_ID )
            LEFT OUTER JOIN T_ANSR_NESTVAR_MEMBER_COL_COMB  TBL_3 ON ( TBL_1.COL_SEQ_COMBINATION_ID =
                                                                       TBL_3.COL_SEQ_COMBINATION_ID )
            LEFT OUTER JOIN T_ANSR_NESTVAR_MEMBER           TBL_4 ON ( TBL_3.ARRAY_MEMBER_ID        =
                                                                       TBL_4.ARRAY_MEMBER_ID )
            ) TBL
            ORDER BY HOST_NAME, VARS_NAME, ARRAY_NEST_LEVEL, VARS_KEY_ID, ASSIGN_SEQ

            """

        rows = self.lv_objDBCA.sql_execute(sql, [in_execute_no,
                                                 in_operation_id,
                                                 in_pattern_id,
                                                 in_execute_no,
                                                 in_operation_id,
                                                 in_pattern_id])
    
        mt_host_vars = {}
        tgt_row = []
        array_tgt_row = []

        # ary = {}
        # ary = {'VARS_ENTRY_FILE': None,
        #       'ASSIGN_SEQ': 1,
        #       'ASSIGN_ID': 'ASSIGN_ID01',
        #       'PTN_VARS_LINK_DISUSE_FLAG': '0',
        #       'PHO_LINK_HOST_COUNT': 1,
        #       'VARS_ATTRIBUTE_01': '2',
        #       'VARS_NAME': 'ttttt',
        #       'SENSITIVE_FLAG': '0',
        #       'VARS_ENTRY': 'aaa',
        #       'HOST_NAME': 'SYSTEM01'}
        # rows = []
        # rows.append(ary)
        for row in rows:
            ret = self.setFileUploadCloumnFileEnv(self.lv_ans_if_info, row)
            if ret is not True:
                return False, mt_host_vars, mt_MultiArray_vars_list, mt_All_vars_list

            if row['VARS_ATTRIBUTE_01'] == self.LC_VARS_ATTR_STRUCT:
                array_tgt_row.append(row)
            else:
                tgt_row.append(row)
        for row in tgt_row:
            assign_seq = True
            if not row['ASSIGN_SEQ']:
                assign_seq = False

            if row['PTN_VARS_LINK_DISUSE_FLAG'] == '0':
                # 作業対象ホストになくて代入値管理のみあるホスト変数をはじく
                if row['PHO_LINK_HOST_COUNT'] == 0:
                    continue

                # 代入値管理のみあるホスト変数(作業対象ホストにない)をはじく
                if row['PHO_LINK_HOST_COUNT'] > 0:
                    # 不要なチェック処理
                    # 多次元変数以外か判定
                    # if row['VARS_ATTRIBUTE_01'] == self.LC_VARS_ATTR_STRUCT:
                    #     if row['MEMBER_COL_COMB_DISUSE_FLAG'] != '0':
                    #         #
                    #         msgstr = g.appmsg.get_api_message("MSG-10452", [row['ASSIGN_ID']])
                    #         self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                    #                            str(inspect.currentframe().f_lineno), msgstr)
                    #         return False, mt_host_vars, mt_MultiArray_vars_list, mt_All_vars_list
                    #
                    #     if row['ARRAY_MEMBER_DISUSE_FLAG'] != '0':
                    #         #
                    #         msgstr = g.appmsg.get_api_message("MSG-10453", [row['ASSIGN_ID']])
                    #         self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                    #         str(inspect.currentframe().f_lineno), msgstr)
                    #         return False, mt_host_vars, mt_MultiArray_vars_list, mt_All_vars_list
                    
                    if row['VARS_ATTRIBUTE_01'] == self.LC_VARS_ATTR_LIST:
                        # 配列変数以外で代入順序がnullの場合はエラーにする。
                        if assign_seq is False:
                            #
                            msgstr = g.appmsg.get_api_message("MSG-10416", [row['ASSIGN_ID'], row['VARS_NAME']])
                            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                               str(inspect.currentframe().f_lineno), msgstr)
                            return False, mt_host_vars, mt_MultiArray_vars_list, mt_All_vars_list

                    if row['VARS_ATTRIBUTE_01'] == self.LC_VARS_ATTR_STD:
                        # 代入順序がnull以外の場合はエラーにする。
                        if assign_seq is True:
                            #
                            msgstr = g.appmsg.get_api_message("MSG-10442", [row['ASSIGN_ID'], row['VARS_NAME']])
                            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                               str(inspect.currentframe().f_lineno), msgstr)
                            return False, mt_host_vars, mt_MultiArray_vars_list, mt_All_vars_list

                    # 多次元変数以外か判定
                    if row['VARS_ATTRIBUTE_01'] != self.LC_VARS_ATTR_STRUCT:
                        # 配列変数以外で代入順序が重複していないか判定する。
                        keyStr = "{}_{}_{}".format(row['HOST_NAME'], row['VARS_NAME'], row['ASSIGN_SEQ'])
                        if keyStr in vars_assign_seq_list:
                            #
                            msgstr = g.appmsg.get_api_message("MSG-10417", [row['ASSIGN_ID'],
                                                                            vars_assign_seq_list[keyStr],
                                                                            row['VARS_NAME'],
                                                                            row['ASSIGN_SEQ']])
                            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                               str(inspect.currentframe().f_lineno), msgstr)
                            return False, mt_host_vars, mt_MultiArray_vars_list, mt_All_vars_list
                        else:
                            # 配列変数以外で代入順序の重複チェックリスト作成
                            vars_assign_seq_list[keyStr] = row['ASSIGN_ID']

                        # 具体値の暗号化が必要か判定
                        if row['SENSITIVE_FLAG'] == self.AnscObj.DF_SENSITIVE_ON:
                            indento_sp = ""
                            valut_value = ""
                            value = ky_decrypt(row['VARS_ENTRY'])
                            make_vaultvalue = self.makeAnsibleVaultValue(value, valut_value, indento_sp, row['ASSIGN_ID'])
                            if make_vaultvalue is False:
                                return False, mt_host_vars, mt_MultiArray_vars_list, mt_All_vars_list

                            # 具体値を暗号化した具体値で上書き
                            row['VARS_ENTRY'] = make_vaultvalue
                        else:
                            # 複数行具体値の場合に複数行の扱い記号を付ける
                            row['VARS_ENTRY'] = self.makeMultilineValue(row['VARS_ENTRY'])

                        if row['VARS_ATTRIBUTE_01'] == self.LC_VARS_ATTR_STD:
                            # ホスト変数配列作成
                            if row['HOST_NAME'] not in mt_host_vars:
                                mt_host_vars[row['HOST_NAME']] = {}
                            mt_host_vars[row['HOST_NAME']][row['VARS_NAME']] = row['VARS_ENTRY']
                        else:
                            if row['HOST_NAME'] not in mt_host_vars:
                                mt_host_vars[row['HOST_NAME']] = {}
                            if row['VARS_NAME'] not in mt_host_vars[row['HOST_NAME']]:
                                mt_host_vars[row['HOST_NAME']][row['VARS_NAME']] = ""
                            # 複数行具体値をjson形式で収める
                            retAry = self.ArrayTypeValue_encode(mt_host_vars[row['HOST_NAME']][row['VARS_NAME']], row['VARS_ENTRY'])
                            mt_host_vars[row['HOST_NAME']][row['VARS_NAME']] = retAry[1]
                            
            elif row['PTN_VARS_LINK_DISUSE_FLAG']:
                #
                msgstr = g.appmsg.get_api_message("MSG-10187", [row['ASSIGN_ID']])
                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                   str(inspect.currentframe().f_lineno), msgstr)
                return False, mt_host_vars, mt_MultiArray_vars_list, mt_All_vars_list

            # DISUSE_FLAG = '1'は読み飛ばし

        if varerror_flg is True:
            retAry = self.getDBVarMultiArrayVarsList(array_tgt_row, mt_MultiArray_vars_list)
            varerror_flg = retAry[0]
            mt_MultiArray_vars_list = retAry[1]

        return varerror_flg, mt_host_vars, mt_MultiArray_vars_list, mt_All_vars_list

    def getDBVarList(self,
                     in_pattern_id,
                     operation_id,
                     mt_host_vars,
                     mt_pionner_template_host_vars,
                     mt_vault_vars,
                     mt_vault_host_vars_file_list,
                     mt_child_vars_list,
                     mt_DB_child_vars_list):
        """
        ansibleで実行する変数をデータベースより取得する。(Legacy/Pioneer)
        2.0では不要な処理なので、空リターンする
        Arguments:
            in_pattern_id:                 作業パターンID
            in_operation_id:                オペレーションID
            mt_host_vars:                   変数一覧返却配列 (pionner:passwordColumnの具体値がky_encryptで暗号化)
                                            [ホスト名(IP)][ 変数名 ]=>具体値
            mt_pionner_template_host_vars:  pioneer template用 変数一覧返却配列 (passwordColumnの具体値がansible-vaultで暗号化)
                                            [ホスト名(IP)][ 変数名 ]=>具体値
            mt_vault_vars:                  PasswordCoulumn変数一覧(Pioneer用)
                                            [ 変数名 ] = << 変数名 >>
            mt_vault_host_vars_file_list:   PasswordCoulumn変数のみのホスト変数一覧(Pioneer用)
                                            [ホスト名(IP)][ 変数名 ] = 具体値
            mt_child_vars_list:             配列変数一覧返却配列
                                            [ホスト名(IP)][ 変数名 ][列順序][メンバー変数]=[具体値]
            mt_DB_child_vars_list:          メンバー変数マスタの配列変数のメンバー変数リスト返却
                                            [ 変数名 ][メンバー変数名]=0
        Returns:
            bool, mt_host_vars, mt_pionner_template_host_vars, mt_vault_vars, mt_vault_host_vars_file_list, mt_child_vars_list, mt_DB_child_vars_list
        """
        return True, mt_host_vars, mt_pionner_template_host_vars, mt_vault_vars, mt_vault_host_vars_file_list, mt_child_vars_list, mt_DB_child_vars_list

    def MultiArrayVarsToYamlFormatMain(self,
                                       ina_MultiArray_vars_list,
                                       mt_str_hostvars,
                                       mt_parent_vars_list,
                                       in_host_name,
                                       mt_legacy_Role_cpf_vars_list,
                                       mt_legacy_Role_tpf_vars_list):
        """
        多段変数の具体値をホスト変数ファイル出力用文字列生成
        Arguments:
            ina_MultiArray_vars_list:      多段変数の具体値リスト
            mt_str_hostvars:               ホスト変数ファイルに出力する文字列
            mt_parent_vars_list:           親変数名リスト
            in_host_name,                  ホスト名
            mt_legacy_Role_cpf_vars_list   ファイル管理変数リスト
            mt_legacy_Role_tpf_vars_list   テンプレート理変数リスト
        Returns:
            True/False, mt_str_hostvars, mt_parent_vars_list, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list
        """
        mt_parent_vars_list = {}

        mt_str_hostvars = ""

        for parent_vars_name, parent_vars_list in ina_MultiArray_vars_list.items():
            # 該当ホストの多段変数が未登録か判定
            if in_host_name not in parent_vars_list:
                continue

            host_vars_array = parent_vars_list[in_host_name]
            mt_parent_vars_list[parent_vars_name] = 1
            cur_str_hostvars = parent_vars_name + ":" + "\n"
            error_code = ""
            line = ""
            before_vars = ""
            indent = ""
            nest_level = 1
            # 多次元配列の具体値構造体から。ホスト変数定義を生成する。
            retAry = self.MultiArrayVarsToYamlFormatSub(host_vars_array,
                                                        cur_str_hostvars,
                                                        before_vars,
                                                        indent,
                                                        nest_level,
                                                        error_code,
                                                        line,
                                                        mt_legacy_Role_cpf_vars_list,
                                                        mt_legacy_Role_tpf_vars_list)
            ret = retAry[0]
            cur_str_hostvars = retAry[1]
            error_code = retAry[2]
            line = retAry[3]
            mt_legacy_Role_cpf_vars_list = retAry[4]
            mt_legacy_Role_tpf_vars_list = retAry[5]

            if ret is False:
                # エラーメッセージを直接出力している場合あり
                if error_code == "":
                    return False, mt_str_hostvars, mt_parent_vars_list, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list
                
                msgstr = g.appmsg.get_api_message(error_code, [parent_vars_name])
                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                   str(inspect.currentframe().f_lineno), msgstr)
                return False, mt_str_hostvars, mt_parent_vars_list, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

            mt_str_hostvars += cur_str_hostvars

        return True, mt_str_hostvars, mt_parent_vars_list, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

    def getDBVarMultiArrayVarsList(self, in_tgt_row, mt_MultiArray_vars_list):
        """
        ansibleで実行する多段変数をデータベースより取得する。(Role)
        Arguments:
            in_tgt_row:              データベースに登録されている多次元変数情報
            mt_MultiArray_vars_list: 多段変数リスト
        Returns:
            bool, mt_MultiArray_vars_list
        """
        vars_seq_list = {}
        
        for row in in_tgt_row:
            # 具体値の暗号化が必要か判定
            if row['SENSITIVE_FLAG'] == self.AnscObj.DF_SENSITIVE_ON:
                indento_sp = ""
                valut_value = ""
                value = ky_decrypt(row['VARS_ENTRY'])
                make_vaultvalue = self.makeAnsibleVaultValue(value, valut_value, indento_sp, row['ASSIGN_ID'])
                if make_vaultvalue is False:
                    return False, mt_MultiArray_vars_list

                # 具体値を暗号化した具体値で上書き
                row['VARS_ENTRY'] = make_vaultvalue
            else:
                # 複数行具体値の場合に複数行の扱い記号を付ける
                row['VARS_ENTRY'] = self.makeMultilineValue(row['VARS_ENTRY'])

            # 多段メンバー変数の廃止レコードを判定
            if row['MEMBER_COL_COMB_DISUSE_FLAG'] != '0':
                continue

            if row['PTN_VARS_LINK_DISUSE_FLAG'] == '0':
                # 代入値管理のみあるホスト変数(作業対象ホストにない)をはじく
                if row['PHO_LINK_HOST_COUNT'] == 0:
                    continue

                if not row['VARS_NAME']:
                    msgstr = g.appmsg.get_api_message("MSG-10188", [row['ASSIGN_ID']])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    return False, mt_MultiArray_vars_list

                if row['ASSIGN_SEQ_NEED'] == '0' and row['ASSIGN_SEQ']:
                    msgstr = g.appmsg.get_api_message("MSG-10442", [row['ASSIGN_ID'], row['COL_COMBINATION_MEMBER_ALIAS']])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    return False, mt_MultiArray_vars_list

                if row['ASSIGN_SEQ_NEED'] == '1' and not row['ASSIGN_SEQ']:
                    msgstr = g.appmsg.get_api_message("MSG-10416", [row['ASSIGN_ID'], row['COL_COMBINATION_MEMBER_ALIAS']])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    return False, mt_MultiArray_vars_list

                # 各変数の代入順序と説順序が重複していないか判定する。
                dup_key = 0

                keyStr = "{}_{}_{}_{}".format(row['HOST_NAME'], row['VARS_NAME'], row['COL_SEQ_COMBINATION_ID'], row['ASSIGN_SEQ'])
                if keyStr not in vars_seq_list:
                    # 各変数の代入順序と説順序が重複リスト生成
                    vars_seq_list[keyStr] = row['ASSIGN_SEQ']
                else:
                    dup_key = vars_seq_list[keyStr]

                if dup_key != 0:
                    msgstr = g.appmsg.get_api_message("MSG-10443", [row['ASSIGN_ID'], dup_key, row['COL_COMBINATION_MEMBER_ALIAS']])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    return False, mt_MultiArray_vars_list

                if row['VARS_NAME'] not in mt_MultiArray_vars_list:
                    mt_MultiArray_vars_list[row['VARS_NAME']] = {}
                if row['HOST_NAME'] not in mt_MultiArray_vars_list[row['VARS_NAME']]:
                    mt_MultiArray_vars_list[row['VARS_NAME']][row['HOST_NAME']] = {}

                if not row['ASSIGN_SEQ']:
                    var_type = AnscConst.GC_VARS_ATTR_STD
                else:
                    var_type = AnscConst.GC_VARS_ATTR_LIST

                var_path_array = []
                # 多次元配列のメンバー変数へのパス配列を生成
                retAry = self.makeHostVarsPath(row['COL_COMBINATION_MEMBER_ALIAS'], var_path_array)
                var_path_array = retAry

                # Noneを空白に設定 host_varsにNoneと出力される為
                if not row['VARS_ENTRY']:
                    row['VARS_ENTRY'] = ""
                # 多次元配列の具体値情報をホスト変数ファイルに戻す為の辞書作成
                src_dict = mt_MultiArray_vars_list[row['VARS_NAME']][row['HOST_NAME']]

                add_dict = self.makeHostVarsArray(var_path_array,
                                            0,
                                            mt_MultiArray_vars_list[row['VARS_NAME']][row['HOST_NAME']],
                                            var_type, row['VARS_ENTRY'],
                                            row['ASSIGN_SEQ'])
                # 辞書をマージ
                merge_dict = deepmerge(src_dict, add_dict)
                mt_MultiArray_vars_list[row['VARS_NAME']][row['HOST_NAME']] = merge_dict
                # mt_MultiArray_vars_list[row['VARS_NAME']][row['HOST_NAME']] = ret
            elif row['PTN_VARS_LINK_DISUSE_FLAG']:
                msgstr = g.appmsg.get_api_message("MSG-10187", [row['ASSIGN_ID']])
                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                   str(inspect.currentframe().f_lineno), msgstr)
                return False, mt_MultiArray_vars_list
            else:
                # DISUSE_FLAG = '1'は読み飛ばし
                continue
        return True, mt_MultiArray_vars_list

    def getDBLegacyPlaybookList(self, in_pattern_id, mt_child_playbooks):
        """
        Legacyで実行する子PlayBookファイルをデータベースより取得する。
        2.0では不要な処理なので、空リターンする
        Arguments:
            in_pattern_id: MovementID
            mt_child_playbooks: PlayBookファイル返却配列
        Returns:
            bool, mt_child_playbooks
        """
        return True, mt_child_playbooks

    def getDBPioneerDialogFileList(self, in_pattern_id, in_operation_id, mt_dialog_files, ina_hostostypelist):
        """
        Pioneerで実行する対話ファイルをデータベースより取得する。
        2.0では不要な処理なので、空リターンする
        Arguments:
            in_pattern_id:      MovementID
            in_operation_id:    オペレーションID
            mt_dialog_files:    子PlayBookファイル返却配列
            ina_hostostypelist: ホスト毎OS種別一覧  Pioneerの場合のみ
                                {機器一覧:HOST_NAME': 機器一覧:OS_TYPE_ID'}
        Returns:
            bool, mt_dialog_files
        """
        return True, mt_dialog_files

    def addSystemvars(self, mt_host_vars, ina_hostinfolist):
        """
        システム予約変数を設定する
        Arguments:
            mt_host_vars: ホスト変数一覧
            hostinfolist: 機器一覧
        Returns:
            mt_host_vars
        """
        for host_name, hostinfo in ina_hostinfolist.items():

            if host_name not in mt_host_vars:
                mt_host_vars[host_name] = {}

            mt_host_vars[host_name][self.AnscObj.ITA_SP_VAR_ANS_PROTOCOL_VAR_NAME] = hostinfo['PROTOCOL_ID']

            mt_host_vars[host_name][self.AnscObj.ITA_SP_VAR_ANS_USERNAME_VAR_NAME] = hostinfo['LOGIN_USER']

            if hostinfo['LOGIN_PW'] != self.LC_ANS_UNDEFINE_NAME:
                mt_host_vars[host_name][self.AnscObj.ITA_SP_VAR_ANS_PASSWD_VAR_NAME] = hostinfo['LOGIN_PW']

            mt_host_vars[host_name][self.AnscObj.ITA_SP_VAR_ANS_LOGINHOST_VAR_NAME] = host_name
            mt_host_vars[host_name][self.AnscObj.ITA_SP_VAR_ANS_OUTDIR_VAR_NAME] = self.lv_user_out_Dir
            mt_host_vars[host_name][self.AnscObj.ITA_SP_VAR_CONDUCTO_DIR_VAR_NAME] = self.lv_conductor_instance_Dir
            if self.lv_conductor_instance_no:
                mt_host_vars[host_name][self.AnscObj.ITA_SP_VAR_CONDUCTOR_ID] = self.lv_conductor_instance_no
            else:
                mt_host_vars[host_name][self.AnscObj.ITA_SP_VAR_CONDUCTOR_ID] = self.LC_ANS_UNDEFINE_NAME
            
        return mt_host_vars

    def getDBTemplateMaster(self, in_tpf_var_name, mt_tpf_key, mt_tpf_file_name, mt_tpf_role_only, mt_tpf_vars_struct):
        """
        テンプレートファイルの情報をデータベースより取得する。
        Arguments:
            in_tpf_var_name:    テンプレート変数名
            mt_tpf_key:         テンプレートKey格納変数
            mt_tpf_file_name:   テンプレートファイル格納変数
            mt_tpf_role_only:   多段/読替表変数を含むテンプレート
                                1:Yes  0:No
            mt_tpf_vars_struct: 変数構造定義
        Returns:
            True/False, mt_tpf_key, mt_tpf_file_name, mt_tpf_role_only, mt_tpf_vars_struct
        """
        sql = "SELECT * FROM T_ANSC_TEMPLATE_FILE WHERE ANS_TEMPLATE_VARS_NAME = %s AND DISUSE_FLAG = '0'"

        rows = self.lv_objDBCA.sql_execute(sql, [in_tpf_var_name])

        if len(rows) < 1:
            # テンプレートが未登録の場合のエラー処理は呼び側にまかせる。
            # Pioneer/Legacy チェック確認
            return False, mt_tpf_key, mt_tpf_file_name, mt_tpf_role_only, mt_tpf_vars_struct

        row = rows[0]

        mt_tpf_key = row["ANS_TEMPLATE_ID"]
        mt_tpf_file_name = row["ANS_TEMPLATE_FILE"]
        mt_tpf_role_only = row["ROLE_ONLY_FLAG"]
        mt_tpf_vars_struct = row["VAR_STRUCT_ANAL_JSON_STRING"]

        return True, mt_tpf_key, mt_tpf_file_name, mt_tpf_role_only, mt_tpf_vars_struct

    def setHostvarsfile_template_file_Dir(self, in_dir):
        """
        inディレクトリ配下のテンプレートファイル格納ディレクトリパスを記憶
        Arguments:
            in_indir: inディレクトリ配下のテンプレートファイル格納ディレクトリパス
        Returns:
            なし
        """
        self.lv_Hostvarsfile_template_file_Dir = in_dir

    def getHostvarsfile_template_file_Dir(self):
        """
        inディレクトリ配下のテンプレートファイル格納ディレクトリパスを取得
        Arguments:
            なし
        Returns:
            in_indir: inディレクトリ配下のテンプレートファイル格納ディレクトリパス
        """
        return self.lv_Hostvarsfile_template_file_Dir

    def setTemporary_file_Dir(self, in_indir):
        """
        ITA側一時ファイル格納ディレクトリ名を記憶
        Arguments:
            in_indir: 一時ファイル格納ディレクトリ
        Returns:
            なし
        """
        self.lv_Ansible_temporary_files_Dir = in_indir

    def getTemporary_file_Dir(self):
        """
        ITA側一時ファイル格納ディレクトリ名を取得
        Arguments:
            なし
        Returns:
            一時ファイル格納ディレクトリ
        """
        return self.lv_Ansible_temporary_files_Dir

    def setAnsible_template_files_Dir(self, in_indir):
        """
        inディレクトリからのtemplate_filesディレクトリパスを記憶
        Arguments:
            in_dir:  inディレクトリからのtemplate_filesディレクトリパス
        Returns:
            なし
        """
        self.lv_Ansible_template_files_Dir = in_indir

    def getAnsible_template_files_Dir(self):
        """
        inディレクトリからのtemplate_filesディレクトリパスを取得
        Arguments:
            なし
        Returns:
            inディレクトリ内のSSH秘密鍵ファイルパス
        """
        return self.lv_Ansible_template_files_Dir

    # del def setITA_template_file_Dir(self, in_indir):
    # del def getITA_template_file_Dir(self):
    # getITA_template_fileに置換え
    def getITA_template_file(self, in_key, in_filename):
        """
        ITAが管理しているテンプレートファイルのパスを取得
        Arguments:
            in_key:     テンプレートファイルのPkey(データベース)
            in_filename:   テンプレートファイル名
        Returns:
            ITAが管理しているテンプレートファイルのパス
        """
        path = "{}/{}/{}".format(getTemplateContentUploadDirPath(), in_key, in_filename)
        return path

    def getHostvarsfile_template_file_path(self, in_pkey, in_file):
        """
        inディレクトリ配下のテンプレートファイルパスを取得
        ホスト変数ファイル内のテンプレートファイルパス
        Arguments:
            in_pkey:    テンプレートファイル Pkey
            in_file:    テンプレートファイル
        Returns:
            inディレクトリ配下のテンプレートファイルパス
        """
        file = "{}/{}-{}".format(self.getHostvarsfile_template_file_Dir(), in_pkey, in_file)
        return file

    def getAnsible_template_file(self, in_pkey, in_filename):
        """
        Ansible実行時のテンプレートファイルパスを取得
            getHostvarsfile_template_file_path と同じパスになる
        Arguments:
            in_pkey:    テンプレートファイル Pkey
            in_file:    テンプレートファイル
        Returns:
            Ansible実行時のテンプレートファイルパス
        """
        file = "{}/{}-{}".format(self.getAnsible_template_files_Dir(), in_pkey, in_filename)
        return file

    def CreateTemplatefiles(self, ina_template_files):
        """
        テンブレートファイルを所定のディレクトリにコピーする。
        Arguments:
            ina_template_files: テンプレートファイル配列
                                {Pkey:テンプレートファイル}
        Returns:
            True/False
        """
        for pkey, template_file in ina_template_files.items():
            # テンプレートファイルが存在しているか確認
            src_file = self.getITA_template_file(pkey, template_file)
            if os.path.isfile(src_file) is False:
                msgstr = g.appmsg.get_api_message("MSG-10121", [pkey, os.path.basename(src_file)])
                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                   str(inspect.currentframe().f_lineno), msgstr)
                return False

            # inディレクトリ配下のテンプレートファイルのパス取得
            dst_file = self.getAnsible_template_file(pkey, template_file)

            if os.path.isfile(dst_file) is True:
                # 既にコピー済み
                continue

            # inディレクトリ配下にテンプレートファイルをコピー
            shutil.copyfile(src_file, dst_file)

        return True

    # function CreateLegacytemplatefiles(ina_hosts, ina_child_playbooks, ina_hostprotcollist, ina_host_vars)
    # function CheckTemplatefile(ina_hosts, ina_host_vars, in_child_playbook, in_tpf_key, in_tpf_file_name,
    def getDBPatternList(self, in_pattern_id):
        """
        Movementロール紐付の情報を取得
        Arguments:
            in_pattern_id:   MovementID
        Returns:
            True/False, pattern_list, single_pkg
            pattern_list: Movementロール紐付の情報返却配列
            single_pkg:   ロールパッケージの複数指定有無
        """
        pattern_list = []
        single_pkg = True
        sql = '''
                SELECT
                    *
                FROM
                    {}
                WHERE
                    MOVEMENT_ID  = %s AND
                    DISUSE_FLAG = 0
                '''.format(self.AnscObj.vg_ansible_pattern_linkDB)

        # DBエラーはExceptionで呼び元に戻る
        rows = self.lv_objDBCA.sql_execute(sql, [in_pattern_id])
    
        # Movementロール紐付登録確認
        if len(rows) < 1:
            msgstr = g.appmsg.get_api_message("MSG-10180", [in_pattern_id])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, pattern_list, single_pkg

        pkgid = 0
        idx = 0

        for row in rows:
            # 複数のロールパッケージが紐付ていないか判定
            if idx == 0:
                pkgid = row['ROLE_PACKAGE_ID']
                # Movementロール紐付設定
                pattern_list.append(row)
            else:
                if pkgid != row['ROLE_PACKAGE_ID']:
                    single_pkg = False
            idx = 1
        return True, pattern_list, single_pkg

    def getDBRolePackage(self, in_role_package_id):
        """
        ロールパッケージ管理の情報を取得
        Arguments:
            in_role_package_id: ロールパッケージID
        Returns:
            [True/False, role_package_list]
            role_package_list:  ロールパッケージ管理の情報
                                [{ROLE_PACKAGE_ID:? ,ROLE_PACKAGE_NAME: ? ,ROLE_PACKAGE_FILE: ?}]
        """
        sql = '''
                SELECT
                    *
                FROM
                    {}
                WHERE
                    ROLE_PACKAGE_ID = %s AND
                    DISUSE_FLAG = 0
                '''.format(self.AnscObj.vg_ansible_master_fileDB)
    
        # DBエラーはExceptionで呼び元に戻る
        rows = self.lv_objDBCA.sql_execute(sql, [in_role_package_id])

        role_package_list = []
        # ロールパッケージID登録確認
        if len(rows) < 1:
            msgstr = g.appmsg.get_api_message("MSG-10264", [in_role_package_id])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, role_package_list

        if not rows[0]['ROLE_PACKAGE_FILE']:
            #
            msgstr = g.appmsg.get_api_message("MSG-10279", [in_role_package_id])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, role_package_list
        
        role_package_list.append(rows[0])

        return True, role_package_list

    def getDBLegactRoleList(self, in_pattern_id, mt_rolenamelist):
        """
        Movementに紐づいているロール名を取得
        Arguments:
            in_pattern_id:      MovementID
            mt_rolenamelist:    ロール一覧
                                {INCLUDE_SEQ:{ROLE_ID:{ROLE_NAME'}}
        Returns:
            True/False, mt_rolenamelist
        """
        sql = '''
                SELECT
                    TBL_1.MVMT_MATL_LINK_ID,
                    TBL_1.ROLE_ID,
                    TBL_1.INCLUDE_SEQ,
                    TBL_2.ROLE_NAME,
                    TBL_2.DISUSE_FLAG
                FROM
                    (
                    SELECT
                        TBL3.MVMT_MATL_LINK_ID,
                        TBL3.MOVEMENT_ID,
                        TBL3.ROLE_ID,
                        TBL3.INCLUDE_SEQ
                    FROM
                        {}  TBL3
                    WHERE
                        TBL3.MOVEMENT_ID  = %s AND
                        TBL3.DISUSE_FLAG = '0'
                    )TBL_1
                    LEFT OUTER JOIN  {}  TBL_2 ON
                        ( TBL_1.ROLE_ID = TBL_2.ROLE_ID)
                    ORDER BY TBL_1.INCLUDE_SEQ
                '''.format(self.AnscObj.vg_ansible_pattern_linkDB, self.AnscObj.vg_ansible_roleDB)

        # DBエラーはExceptionで呼び元に戻る
        rows = self.lv_objDBCA.sql_execute(sql, [in_pattern_id])
        
        mt_rolenamelist = {}
        for row in rows:
            if row['DISUSE_FLAG'] == '0':
                if row['INCLUDE_SEQ'] not in mt_rolenamelist:
                    mt_rolenamelist[row['INCLUDE_SEQ']] = {}
                if row['ROLE_ID'] not in mt_rolenamelist[row['INCLUDE_SEQ']]:
                    mt_rolenamelist[row['INCLUDE_SEQ']][row['ROLE_ID']] = {}
                mt_rolenamelist[row['INCLUDE_SEQ']][row['ROLE_ID']] = row['ROLE_NAME']

            # ロール管理にロールが未登録の場合
            elif not row['DISUSE_FLAG']:
                #
                msgstr = g.appmsg.get_api_message("MSG-10265", row['MVMT_MATL_LINK_ID'])
                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                   str(inspect.currentframe().f_lineno), msgstr)
                return False, mt_rolenamelist
            # DISUSE_FLAG = '1'は読み飛ばし
        if len(rows) < 1:
            #
            msgstr = g.appmsg.get_api_message("MSG-10266", [in_pattern_id])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, mt_rolenamelist
        # 対象ロールの数を確認
        if len(mt_rolenamelist) < 1:
            #
            msgstr = g.appmsg.get_api_message("MSG-10266", [in_pattern_id])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, mt_rolenamelist

        return True, mt_rolenamelist

    def CreateLegacyRolePlaybookfiles(self, ina_rolenames, in_exec_mode, in_exec_playbook_hed_def):
        """
        Legacy-Role用 親PlayBookファイルを作成する。
        Arguments:
            ina_rolenames:              ロール名リスト配列
                                        [実行順序][ロールID(Pkey)]=>ロール名
            in_exec_mode:               実行エンジン
                                        1: Ansible  2: Ansible Tower
            in_exec_playbook_hed_def:   親playbookヘッダセクション
        Returns:
            True/False
        """
        # 親PlayBookファイル作成(Legacy-Role)
        file_name = self.getAnsible_RolePlaybook_file()
        if self.CreatePlaybookfile(file_name, ina_rolenames, in_exec_mode, in_exec_playbook_hed_def) is False:
            return False
        return True

    def CheckLegacyRolePlaybookfiles(self, ina_hosts, ina_host_vars, ina_rolenames, ina_role_rolenames, ina_role_rolevars, ina_role_roleglobalvars):
        """
        Playbookで使用している変数がホスト変数に登録されているかチェックする。
        Arguments:
            ina_hosts:                  機器一覧ホスト一覧
                                        {SYSTEM_ID:HOST_NAME}, , ,
            ina_host_vars:              ホスト変数配列
                                        [ホスト名(IP)][ 変数名 ]=>具体値
            ina_rolenames:              ロール名リスト配列(データベース側)
                                        [実行順序][ロールID(Pkey)]=>ロール名
            ina_role_rolenames:         ロール名リスト配列(Role内登録内容)
                                        [ロール名]
            ina_role_rolevars:          ロール内変数リスト配列(Role内登録内容)
                                        [ロール名][変数名]=0
            ina_role_roleglobalvars:    ロール内グローバル変数リスト配列(Role内登録内容)
                                        [ロール名][グローバル変数名]=0
        Returns:
            True/False
        """
        # グローバル変数以外の変数の具体値が未登録でもエラーにしていないので
        # グローバル変数についてもグローバル変数管理の登録の有無をチェックしない

        result_code = True

        # ロール分の繰返し(データベース側)
        for no, rolename_list in ina_rolenames.items():
            # ロール名取得(データベース側)
            for rolepkey, rolename in rolename_list.items():
                # データベース側のロールがロール内に存在しているか判定
                if rolename not in ina_role_rolenames:
                    # 存在していない
                    msgstr = g.appmsg.get_api_message("MSG-10276", [rolename])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    result_code = False
                    continue
                # ロール内に変数が登録されているか
                if rolename not in ina_role_rolevars:
                    # ロール内に変数が使用されていない場合は以降のチェックをスキップ
                    continue

                # ロールに登録されている変数のデータベース登録確認
                for var_name, dummy in ina_role_rolevars[rolename]:
                    # ホスト配列のホスト分繰り返し
                    for no, host_name in ina_hosts:
                        # 変数配列分繰り返し
                        if var_name not in ina_host_vars[host_name]:
                            if var_name == self.AnscObj.ITA_SP_VAR_ANS_PROTOCOL_VAR_NAME:
                                msgstr = g.appmsg.get_api_message("MSG-10267", [rolename, var_name, host_name])
                                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                                   str(inspect.currentframe().f_lineno), msgstr)

                            elif var_name == self.AnscObj.ITA_SP_VAR_ANS_USERNAME_VAR_NAME:
                                msgstr = g.appmsg.get_api_message("MSG-10268", [rolename, var_name, host_name])
                                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                                   str(inspect.currentframe().f_lineno), msgstr)

                            elif var_name == self.AnscObj.ITA_SP_VAR_ANS_PASSWD_VAR_NAME:
                                msgstr = g.appmsg.get_api_message("MSG-10269", [rolename, var_name, host_name])
                                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                                   str(inspect.currentframe().f_lineno), msgstr)

                            elif var_name == self.AnscObj.ITA_SP_VAR_ANS_LOGINHOST_VAR_NAME:
                                msgstr = g.appmsg.get_api_message("MSG-10270", [rolename, var_name, host_name])
                                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                                   str(inspect.currentframe().f_lineno), msgstr)
                            else:
                                continue

                            # エラーリターンする
                            result_code = False

                        else:
                            # 予約変数を使用している場合に対象システム一覧に該当データが登録されているか判定
                            if ina_host_vars[host_name][var_name] == self.LC_ANS_UNDEFINE_NAME:
                                # プロトコル未登録
                                if var_name == self.AnscObj.ITA_SP_VAR_ANS_PROTOCOL_VAR_NAME:
                                    msgstr = g.appmsg.get_api_message("MSG-10272", [rolename, var_name, host_name])
                                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                                       str(inspect.currentframe().f_lineno), msgstr)
                                    result_code = False

                                # ユーザー名未登録
                                elif var_name == self.AnscObj.ITA_SP_VAR_ANS_USERNAME_VAR_NAME:
                                    msgstr = g.appmsg.get_api_message("MSG-10273", [rolename, var_name, host_name])
                                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                                       str(inspect.currentframe().f_lineno), msgstr)
                                    result_code = False

                                # ログインパスワード未登録
                                elif var_name == self.AnscObj.ITA_SP_VAR_ANS_PASSWD_VAR_NAME:
                                    msgstr = g.appmsg.get_api_message("MSG-10274", [rolename, var_name, host_name])
                                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                                       str(inspect.currentframe().f_lineno), msgstr)
                                    result_code = False

                                # ホスト名未登録
                                elif var_name == self.AnscObj.ITA_SP_VAR_ANS_LOGINHOST_VAR_NAME:
                                    msgstr = g.appmsg.get_api_message("MSG-10275", [rolename, var_name, host_name])
                                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                                       str(inspect.currentframe().f_lineno), msgstr)
                                    result_code = False

        return result_code

    def getAnsible_RolePlaybook_file(self):
        """
        Ansible Role 親Playbookファイルパス取得
        Arguments:
            なし
        Returns:
            Ansible Role 親Playbookファイルパス
        """
        file = "{}/{}".format(self.getAnsible_in_Dir(), self.LC_ANS_ROLE_PLAYBOOK_FILE)
        return file

    def getRolePackageFile(self, in_pattern_id):
        """
        Movement紐付パッケージファイルを取得
        Arguments:
            in_pattern_id:   MovementID
        Returns:
            [{True/False, role_package_pkey, role_package_file}]
            role_package_pkey:  ロールパッケージファイル Pkey返却
            role_package_file:  ロールパッケージファイル(ZIP)返却
        """
        role_package_pkey = ""
        role_package_file = ""
        # Movementロール紐付に登録されているロールパッケージの情報取得
        # Movementロール紐付なし、複数のロールパッケージの紐付をチェック
        retAry = self.getDBPatternList(in_pattern_id)
        ret = retAry[0]
        patternlist = retAry[1]
        single_pkg = retAry[2]
        # [{ ROLE_PACKAGE_ID:? ,ROLE_ID: ?, INCLUDE_SEQ: ? }]
        if ret is not True:
            #
            msgstr = g.appmsg.get_api_message("MSG-10023", [os.path.basename(__file__), self.lineno(), self.lineno()])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, role_package_pkey, role_package_file

        # 作業パターン詳細に複数のロールパッケージが紐づいていないか判定する。
        if single_pkg is False:
            #
            msgstr = g.appmsg.get_api_message("MSG-10263", [])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, role_package_pkey, role_package_file

        role_package_pkey = patternlist[0]["ROLE_PACKAGE_ID"]

        # ロールパッケージ管理の情報取得
        retAry = self.getDBRolePackage(role_package_pkey)
        ret = retAry[0]
        rolepackagelist = retAry[1]
        #  [{ROLE_PACKAGE_ID:? ,ROLE_PACKAGE_NAME: ? ,ROLE_PACKAGE_FILE: ?}]
        if ret is not True:
            msgstr = g.appmsg.get_api_message("MSG-10023", [os.path.basename(__file__),
                                                            str(inspect.currentframe().f_lineno),
                                                            str(inspect.currentframe().f_lineno)])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, role_package_pkey, role_package_file

        role_package_file = rolepackagelist[0]["ROLE_PACKAGE_FILE"]
        role_package_pkey = rolepackagelist[0]["ROLE_PACKAGE_ID"]
        return True, role_package_pkey, role_package_file

    def getAnsible_RolePackage_file(self, in_pkey, in_filename):
        """
        ロールパッケージファイル(ZIP)パスを取得
        Arguments:
            in_pkey:      ロールパッケージファイル(ZIP) Pkey
            in_filename:  ロールパッケージファイル名
        Returns:
            ロールパッケージファイル(ZIP)パス
        """
        file = "{}/{}/{}".format(getRolePackageContentUploadDirPath(), in_pkey, in_filename)
        return file

    def setHostvarsfile_copy_file_Dir(self, in_dir):
        """
        inディレクトリ配下のデcopy_filesィレクトリバスを記憶
        Arguments:
            in_dir:      copy_filesディレクトリ
        Returns:
            なし
        """
        self.lv_Hostvarsfile_copy_file_Dir = in_dir

    def getHostvarsfile_copy_file_Dir(self):
        """
        inディレクトリ配下のデcopy_filesィレクトリバスを取得
        Arguments:
            なし
        Returns:
            inディレクトリ配下のデcopy_filesィレクトリバス
        """
        return self.lv_Hostvarsfile_copy_file_Dir

    def setAnsible_copy_files_Dir(self, in_indir):
        """
        inディレクトリからのcopy_filesディレクトリバスを記憶
        Arguments:
            in_indir: inディレクトリからのcopy_filesディレクトリバス
        Returns:
            なし
        """
        self.lv_Ansible_copy_files_Dir = in_indir

    def getAnsible_copy_files_Dir(self):
        """
        inディレクトリからのcopy_filesディレクトリバスを取得
        Arguments:
            なし
        Returns:
            inディレクトリからのcopy_filesディレクトリバス
        """
        return self.lv_Ansible_copy_files_Dir

    # setITA_copy_file_Dir(self, in_indir):
    # getITA_copy_file_Dir():
    # getITA_copy_fileに置換え
    def getITA_copy_file(self, in_key, in_filename):
        """
        ITAが管理しているcopyファイルのパスを取得
        Arguments:
            in_key:        copyファイルのPkey(データベース)
            in_filename:   copyファイル名
        Returns:
            ITAが管理しているcopyファイルのパス
        """
        path = "{}/{}/{}".format(getFileContentUploadDirPath(), in_key, in_filename)
        return path

    def getHostvarsfile_copy_file_value(self, in_pkey, in_file):
        """
        inディレクトリからのcopy_filesディレクトリバスを取得
        Arguments:
            in_pkey:   ファイル管理 Pkey
            in_file:   ファイル管理 ファイル名
        Returns:
            inディレクトリからのcopy_filesディレクトリバス
        """
        path = "{}/{}-{}".format(self.getHostvarsfile_copy_file_Dir(), in_pkey, in_file)
        return path

    def getAnsible_copy_file(self, in_pkey, in_filename):
        """
        ロールパッケージ管理の情報を取得
        Arguments:
            in_role_package_id: ロールパッケージID
        Returns:
            [True/False, role_package_list]
            role_package_list:  ロールパッケージ管理の情報
                                [{ROLE_PACKAGE_ID:? ,ROLE_PACKAGE_NAME: ? ,ROLE_PACKAGE_FILE: ?}]
        """
        filepath = "{}/{}-{}".format(self.getAnsible_copy_files_Dir(), in_pkey, in_filename)
        return filepath

    def CreateCopyfiles(self, ina_copy_files):
        """
        ファイル管理のファイルを所定のディレクトリにコピーする。
        Arguments:
            ina_copy_files: copyファイル配列
                            {Pkey: copyファイル}..
        Returns:
            True/False
        """
        for pkey, copy_file in ina_copy_files.items():
            # copyファイルが存在しているか確認
            src_file = self.getITA_copy_file(pkey, copy_file)

            if os.path.isfile(src_file) is False:
                msgstr = g.appmsg.get_api_message("MSG-10410", [pkey, os.path.basename(src_file)])
                self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                   str(inspect.currentframe().f_lineno), msgstr)
                return False

            # Ansible実行時のcopyファイル名
            dst_file = self.getAnsible_copy_file(pkey, copy_file)

            if os.path.isfile(dst_file) is True:
                # 既にコピー済み
                return True
            shutil.copyfile(src_file, dst_file)

        return True

    # def CreateLegacyCopyFiles(ina_hosts, ina_child_playbooks, ina_hostprotcollist, ina_host_vars){
    def getDBCopyMaster(self, in_cpf_var_name, mt_cpf_key, mt_cpf_file_name):
        """
        ファイル管理の情報取得
        Arguments:
            in_cpf_var_name: ファイル管理変数名
            mt_cpf_key:      ファイル管理 Pkey
            mt_cpf_file_name: ファイル管理ファイル名
        Returns:
            [True/False, mt_cpf_key, mt_cpf_file_name
        """
        sql = """
                SELECT
                    *
                FROM
                    T_ANSC_CONTENTS_FILE
                WHERE
                    CONTENTS_FILE_VARS_NAME = %s AND
                    DISUSE_FLAG             = '0'
                """
        mt_cpf_key = ""
        mt_cpf_file_name = ""

        rows = self.lv_objDBCA.sql_execute(sql, [in_cpf_var_name])
        
        if len(rows) < 1:
            # ファイル管理が未登録の場合のエラー処理は呼び側にまかせる。
            # Pionner/Legacyのチェック確認
            return False, mt_cpf_key, mt_cpf_file_name

        row = rows[0]

        mt_cpf_key = row["CONTENTS_FILE_ID"]
        mt_cpf_file_name = row["CONTENTS_FILE"]

        return True, mt_cpf_key, mt_cpf_file_name

    def makeHostVarsPath(self, in_var_name_str, mt_var_path_array):
        """
        多段変数のメンバー変数へのパス配列を生成
        Arguments:
            in_var_name_str:     多段変数のメンバー変数へのパス
            mt_var_path_array:  多段変数のメンバー変数へのパス配列
        Returns:
            mt_var_path_array
        """
        # [3].array1.array2[0].array2_2[0].array2_2_2[0].array2_2_2_2
        # []を取り除く
        in_var_name_str = in_var_name_str.replace("[", ".")
        in_var_name_str = in_var_name_str.replace("]", "")
        # 先頭が配列の場合の . を取り除く
        # .array1.array2.0.array2_2.0.array2_2_2.0.array2_2_2_2
        in_var_name_str = re.sub(r'^\.', '', in_var_name_str)
        mt_var_path_array = in_var_name_str.split('.')

        return mt_var_path_array

    def makeHostVarsArray(self, in_key_array, in_idx, mt_out_array, in_var_type, in_var_val, in_ass_no):
        """
        多段／変数メンバー変数の具体値情報をホスト変数ファイルに戻す為の配列作成
        Arguments:
            in_key_array:      多段／変数メンバー変数へのパス配列
            in_idx:            階層番号(0～)
            mt_out_array(out): ホスト変数ファイルに戻す為の配列
            in_var_type:       メンバー変数のタイプ
                                1: Key-Value変数
                                2: 複数具体値変数
            in_var_val:        メンバー変数の具体値
            in_ass_no:         複数具体値変数の場合の代入順序
        Returns:
            なし
        """
        # 末端の変数に達したか判定
        if len(in_key_array) <= in_idx:

            # 末端の変数か判定
            if len(in_key_array) == in_idx:
                # 具体値を埋め込む
                if in_var_type == AnscConst.GC_VARS_ATTR_STD:
                    # Key-Value変数の場合
                    mt_out_array = in_var_val
                else:
                    # 複数具体値の場合
                    mt_out_array[in_ass_no] = in_var_val

                    # 代入順序で昇順ソートする。
                    sortdic = sorted(mt_out_array.items(), key=lambda x: x[0], reverse=False)
                    mt_out_array.clear()
                    mt_out_array.update(sortdic)
                    
            return mt_out_array

        # 該当階層の変数名を取得
        var_name = in_key_array[in_idx]

        # ホスト変数配列に変数名が退避されているか判定
        if var_name not in mt_out_array:
            # 変数名をホスト変数配列に退避
            mt_out_array[var_name] = {}

            # 配列の場合に列順序で昇順ソート
            if var_name.isdigit() is True:
                sortdic = sorted(mt_out_array.items(), key=lambda x: x[0], reverse=False)
                mt_out_array.clear()
                mt_out_array.update(sortdic)

        in_idx += 1
        # 次の階層へ
        ret = self.makeHostVarsArray(in_key_array, in_idx, mt_out_array[var_name], in_var_type, in_var_val, in_ass_no)
        mt_out_array[var_name] = ret
        return mt_out_array
    
    def MultiArrayVarsToYamlFormatSub(self,
                                      ina_host_vars_array,
                                      mt_str_hostvars,
                                      in_before_vars,
                                      in_indent,
                                      nest_level,
                                      mt_error_code,
                                      mt_line,
                                      mt_legacy_Role_cpf_vars_list,
                                      mt_legacy_Role_tpf_vars_list):
        """
        多段変数の具体値をホスト変数ファイル出力用文字列生成
        Arguments:
            ina_host_vars_array:           多段変数の具体値リスト
            mt_str_hostvars:               ホスト変数ファイルに出力する文字列
            in_before_vars:                一つ前の変数構造
            in_indent:                     ホスト変数ファイルに出力際のインデント数
            nest_level:                    階層番号(1～)
            mt_error_code:                 エラー時のメッセージコード
            mt_line:                       エラー発生個所
            mt_legacy_Role_cpf_vars_list   ファイル管理変数リスト
            mt_legacy_Role_tpf_vars_list   テンプレート理変数リスト
        Returns:
            True/False, Dmt_str_hostvars, mt_error_code, mt_line, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list
        """

        idx = 0

        # 配列階層か判定
        array_f = self.is_assoc(ina_host_vars_array)
        if array_f == -1:
            mt_error_code = "MSG-10455"
            mt_line = inspect.currentframe().f_lineno
            return False, mt_str_hostvars, mt_error_code, mt_line, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

        if array_f != 'I':
            indent = in_indent + "  "
            nest_level = nest_level + 1
        else:
            indent = in_indent

        for var, val in ina_host_vars_array.items():
            # 繰返数設定
            idx = idx + 1

            # 現階層の変数名退避
            before_vars = var

            # php 要確認
            # 具体値の配列の場合の判定
            # 具体値の配列の場合は具体値が全てとれない模様
            # - xxxx1
            #   - xxxx2
            # - xxxx3
            # array(2) {
            #    [0]=>
            #      array(1) {
            #      [0]=>
            #        string(5) "xxxxx2"
            var_int = False
            if isinstance(var, int):
                var_int = True
            else:
                if var.isdigit():
                    var_int = True
            if var_int is True:
                # 具体値の配列の場合の判定
                ret = self.is_assoc(val)
                if ret == "I":
                    mt_error_code = "MSG-10456"
                    mt_line = inspect.currentframe().f_lineno
                    return False, mt_str_hostvars, mt_error_code, mt_line, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

            # 複数具体値か判定する。
            if var_int is True:

                # 具体値があるか判定
                if isinstance(val, dict) is False:
                    # 変数の具体値にコピー変数が使用されていないか確認
                    retAry = self.LegacyRoleCheckConcreteValueIsVar(val,
                                                                    mt_legacy_Role_cpf_vars_list,
                                                                    mt_legacy_Role_tpf_vars_list)
                    ret = retAry[0]
                    mt_legacy_Role_cpf_vars_list = retAry[1]
                    mt_legacy_Role_tpf_vars_list = retAry[2]
                    if ret is False:
                        # エラーメッセージは出力しているので、ここでは何も出さない。
                        mt_error_code = ""
                        return False, mt_str_hostvars, mt_error_code, mt_line, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list
                    
                    # 具体値出力
                    # - xxxxxxx
                    NumPadding = len(indent) + 4
                    # 多段変数の複数具体値はJSON形式なっていない
                    edit_str = self.MultilineValueEdit(val, NumPadding)

                    vars_str = "{}  - {}\n".format(indent, edit_str)
                    mt_str_hostvars = mt_str_hostvars + vars_str
                    continue

                else:
                    # 具体値がないので配列階層
                    # 配列階層の場合はインデントを1つ戻す。
                    if idx == 1:
                        indent = "".ljust(len(indent) - 2)
            else:
                # 1つ前の階層が配列階層か判定
                if in_before_vars.isdigit():
                    # Key-Value変数か判定
                    if isinstance(val, dict) is False:
                        # Key-Value変数の場合
                        if idx == 1:
                            # 変数の具体値にコピー変数が使用されていないか確認
                            retAry = self.LegacyRoleCheckConcreteValueIsVar(val,
                                                                            mt_legacy_Role_cpf_vars_list,
                                                                            mt_legacy_Role_tpf_vars_list)
                            ret = retAry[0]
                            mt_legacy_Role_cpf_vars_list = retAry[1]
                            mt_legacy_Role_tpf_vars_list = retAry[2]

                            if ret is False:
                                # エラーメッセージは出力しているので、ここでは何も出さない。
                                mt_error_code = ""
                                return False, mt_str_hostvars, mt_error_code, mt_line, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list
                            # 変数と具体値出力 配列の先頭変数なので - を付ける
                            # - xxxxx: xxxxxxx
                            NumPadding = len(indent) + 4
                            edit_str = self.MultilineValueEdit(val, NumPadding)
                            vars_str = "{}- {}: {}\n".format(indent, var, edit_str)
                            mt_str_hostvars = mt_str_hostvars + vars_str

                            # インデント位置を加算
                            indent = indent + "  "

                        else:

                            # 変数の具体値にコピー変数が使用されていないか確認
                            retAry = self.LegacyRoleCheckConcreteValueIsVar(val,
                                                                            mt_legacy_Role_cpf_vars_list,
                                                                            mt_legacy_Role_tpf_vars_list)
                            ret = retAry[0]
                            mt_legacy_Role_cpf_vars_list = retAry[1]
                            mt_legacy_Role_tpf_vars_list = retAry[2]
                            if ret is False:
                                # エラーメッセージは出力しているので、ここでは何も出さない。
                                mt_error_code = ""
                                return False, mt_str_hostvars, mt_error_code, mt_line, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

                            # 変数と具体値出力 配列の先頭変数ではないので - は付けない
                            #   xxxxx: xxxxxx
                            # インデント位置は加算済み
                            NumPadding = len(indent) + 4
                            edit_str = self.MultilineValueEdit(val, NumPadding)
                            vars_str = "{}{}: {}\n".format(indent, var, edit_str)
                            mt_str_hostvars = mt_str_hostvars + vars_str

                        continue

                    else:
                        # ネスト変数の場合
                        if idx == 1:
                            # 変数出力 配列の先頭変数なので - を付ける
                            vars_str = "{}- {}:\n".format(indent, var)
                            mt_str_hostvars = mt_str_hostvars + vars_str

                            # インデント位置を加算
                            indent = indent + "  "

                        else:
                            # 変数出力 配列の先頭変数ではないので - は付けない
                            vars_str = "{}{}:\n".format(indent, var)
                            mt_str_hostvars = mt_str_hostvars + vars_str

                else:
                    # Key-Value変数か判定
                    if isinstance(val, dict) is False:
                        # 変数の具体値にコピー変数が使用されていないか確認
                        retAry = self.LegacyRoleCheckConcreteValueIsVar(val,
                                                                        mt_legacy_Role_cpf_vars_list,
                                                                        mt_legacy_Role_tpf_vars_list)
                        ret = retAry[0]
                        mt_legacy_Role_cpf_vars_list = retAry[1]
                        mt_legacy_Role_tpf_vars_list = retAry[2]
                        if ret is False:
                            # エラーメッセージは出力しているので、ここでは何も出さない。
                            mt_error_code = ""
                            return False, mt_str_hostvars, mt_error_code, mt_line, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

                        # 変数と具体値出力
                        # xxxxx: xxxxxxx
                        NumPadding = len(indent) + 4
                        edit_str = self.MultilineValueEdit(val, NumPadding)
                        vars_str = "{}{}: {}\n".format(indent, var, edit_str)
                        mt_str_hostvars = mt_str_hostvars + vars_str

                        continue

                    else:
                        # ネスト変数として出力
                        # xxxxx:
                        vars_str = "{}{}:\n".format(indent, var)
                        mt_str_hostvars = mt_str_hostvars + vars_str

            retAry = self.MultiArrayVarsToYamlFormatSub(val,
                                                        mt_str_hostvars,
                                                        before_vars,
                                                        indent,
                                                        nest_level,
                                                        mt_error_code,
                                                        mt_line,
                                                        mt_legacy_Role_cpf_vars_list,
                                                        mt_legacy_Role_tpf_vars_list)
            ret = retAry[0]
            mt_str_hostvars = retAry[1]
            mt_error_code = retAry[2]
            mt_line = retAry[3]
            mt_legacy_Role_cpf_vars_list = retAry[4]
            mt_legacy_Role_tpf_vars_list = retAry[5]
            if ret is False:
                return False, mt_str_hostvars, mt_error_code, mt_line, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

        return True, mt_str_hostvars, mt_error_code, mt_line, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

    def is_assoc(self, in_array):
        """
        多段変数の末端変数の構造判定
        Arguments:
            in_array: 多段変数構造
        Returns:
            -1/"I"/"C"
        """
        key_int = False
        key_char = False
        if isinstance(in_array, dict) is False:
            return -1

        for key, value in in_array.items():
            # 配列構造の場合に数値(index)と文字列が混在していないか判定
            if isinstance(key, int):
                key_int = True
            else:
                if key.isdigit() is False:
                    key_char = True
                else:
                    key_int = True
        if key_char is True and key_int is True:
            return -1
        if key_char is True:
            return "C"
        return "I"

    def getDBGlobalVarsMaster(self, mt_global_vars_list):
        """
          グローバル変数の情報をデータベースより取得
          Arguments:
            mt_global_vars_list: データベースより取得したグローバル変数
          Returns:
            True
        """
        sql = '''
                SELECT
                    VARS_NAME,
                    VARS_ENTRY
                FROM
                    T_ANSC_GLOBAL_VAR
                WHERE
                    DISUSE_FLAG = '0'
                '''
        # DBエラーはExceptionで呼び元に戻る
        rows = self.lv_objDBCA.sql_execute(sql, [])
        for row in rows:
            if row['VARS_NAME'] not in mt_global_vars_list:
                mt_global_vars_list[row['VARS_NAME']] = row['VARS_ENTRY']
        return True, mt_global_vars_list

    def CreateLegacyRoleCopyFiles(self, ina_hosts, ina_rolenames, ina_cpf_vars_list):
        """
        playbook内で使用しているファイル管理のファイルを所定の場所にコピーする
        Arguments:
            ina_hosts:         機器一覧ホスト一覧
            ina_rolenames:     処理対象ロールリスト
            ina_cpf_vars_list: ファイル管理変数リスト
        Returns:
            True/False
        """
        # 処理対象のロール名抽出
        tgt_role_list = {}
        for no, rolename_list in ina_rolenames.items():
            for rolepkey, rolename in rolename_list.items():
                tgt_role_list[rolename] = 1

        # 処理対象のロールで使用しているファイル変数か判定
        la_cpf_files = {}
        la_cpf_path = {}
        for role_name, tgt_file_list in ina_cpf_vars_list.items():
            if role_name not in tgt_role_list:
                continue
            for tgt_file, line_no_list in tgt_file_list.items():
                for line_no, cpf_var_name_list in line_no_list.items():
                    for cpf_var_name, file_info_list in cpf_var_name_list.items():

                        # inディレクトリ配下のcopyファイルバスを取得
                        cpf_path = self.getHostvarsfile_copy_file_value(file_info_list['CONTENTS_FILE_ID'],
                                                                        file_info_list['CONTENTS_FILE'])

                        # ファイルパスをansible側から見たパスに変更する。
                        cpf_path = self.setAnsibleSideFilePath(cpf_path, self.LC_ITA_IN_DIR)

                        # la_cpf_path[copy変数]=inディレクトリ配下ののcopyファイルパス
                        la_cpf_path[cpf_var_name] = cpf_path

                        # copyファイルのpkeyとファイル名を退避
                        la_cpf_files[file_info_list['CONTENTS_FILE_ID']] = file_info_list['CONTENTS_FILE']

        # ファイル管理のファイルを所定の場所にコピー
        if len(la_cpf_files) > 0:
            ret = self.CreateCopyfiles(la_cpf_files)
            if ret is False:
                return False

        # ホスト変数定義ファイルにファイル管理変数を追加
        if len(la_cpf_files) > 0:
            # 作業対象ホスト分ループ
            for id, host_name in ina_hosts.items():
                # ホスト変数定義ファイル名を取得
                file_name = self.getAnsible_host_var_file(host_name)
                # ホスト変数定義ファイルにテンプレート変数を追加
                if self.CreateRoleHostvarsfile("CPF", file_name, la_cpf_path, "", "", "", "", "a") is False:
                    return False

        return True

    # function getDBTranslationTable(in_pattern_id, &ina_translationtable_list){
    def setAnsible_upload_files_Dir(self, in_indir):
        """
        inディレクトリからのFileUpLoadColumnファイル格納ディレクトリパス(upload_files)を記憶
        Arguments:
            inディレクトリからのFileUpLoadColumnファイル格納ディレクトリパス(upload_files)
        Returns:
            なし
        """
        self.lv_Ansible_upload_files_Dir = in_indir

    def getAnsible_upload_files_Dir(self):
        """
        inディレクトリからのFileUpLoadColumnファイル格納ディレクトリパス(upload_files)を取得
        Arguments:
            なし
        Returns:
            inディレクトリからのFileUpLoadColumnファイル格納ディレクトリパス(upload_files)
        """
        return self.lv_Ansible_upload_files_Dir

    def setAnsible_ssh_key_files_Dir(self, in_indir):
        """
        inディレクトリからのSSH秘密鍵ファイル格納ディレクトリパス(ssh_key_files)を記憶
        Arguments:
            in_dir:      ssh_key_filesディレクトリ
        Returns:
            なし
        """
        self.lv_Ansible_ssh_key_files_Dir = in_indir

    def getAnsible_ssh_key_files_Dir(self):
        """
        inディレクトリからのSSH秘密鍵ファイル格納ディレクトリパス(ssh_key_files)を取得
        Arguments:
            なし
        Returns:
            inディレクトリからのSSH秘密鍵ファイル格納ディレクトリパス(ssh_key_files)
        """
        return self.lv_Ansible_ssh_key_files_Dir

    def getITA_ssh_key_file(self, in_key, in_filename):
        """
        ITAが機器一覧で管理しているSSH秘密鍵ファイルのパスを取得
        Arguments:
            in_key:        SSH秘密鍵ファイルのPkey(データベース)
            in_filename:   SSH秘密鍵ファイル名
        Returns:
            ITAが機器一覧で管理しているSSH秘密鍵ファイルのパス
        """
        path = "{}/{}/{}".format(getDeviceListSSHPrivateKeyUploadDirPath(), in_key, in_filename)
        return path

    def getIN_ssh_key_file(self, in_pkey, in_file):
        """
        inディレクトリのSH秘密鍵ファイルパス(ssh_key_files)を取得
        Arguments:
            in_pkey: SSH秘密鍵ファイルのPkey(データベース)
            in_file: SSH秘密鍵ファイル
        Returns:
            inディレクトリ内のSSH認証ファイルパス
        """
        path = "{}/{}-{}".format(self.getAnsible_ssh_key_files_Dir(), in_pkey, in_file)
        return path

    def CreateSSH_key_file(self, in_pkey, in_ssh_key_file):
        """
        inディレクトリからのSSH秘密鍵ファイルパス(ssh_key_files)を取得
        Arguments:
            in_pkey:             SSH秘密鍵ファイルのPkey(データベース)
            in_file:             SSH秘密鍵ファイル
        Returns:
            True/False, mt_dir_ssh_key_file
        """
        ssh_key_file = ""
        # SSH秘密鍵ファイルが存在しているか確認
        src_file = self.getITA_ssh_key_file(in_pkey, in_ssh_key_file)
        if os.path.isfile(src_file) is False:
            #
            msgstr = g.appmsg.get_api_message("MSG-10526", [in_pkey, src_file])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, ssh_key_file

        # Ansible実行時のSSH秘密鍵ファイルパス取得
        dst_file = self.getIN_ssh_key_file(in_pkey, in_ssh_key_file)

        # ky_encryptで中身がスクランブルされているので復元する
        # SSH認証ファイルをansible用ディレクトリにコピーする。
        ret = ky_file_decrypt(src_file, dst_file)
        if ret is False:
            #
            msgstr = g.appmsg.get_api_message("MSG-10647", [src_file])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, ssh_key_file

        # パミッション設定
        os.chmod(dst_file, 0o600)

        # 今後の修正ポイント
        # 実行ユーザーがroot以外の場合、鍵ファイルのオーナーを変更
        # ExecUser = self.getAnsibleExecuteUser()
        # if((ExecUser != 'root') && (self.lv_exec_mode == DF_EXEC_MODE_ANSIBLE)) {
        #    if( !chown( dst_file, ExecUser) ){
        #        msgstr = self.lv_objMTS->getSomeMessage("ITAANSIBLEH-ERR-5000038", array(__LINE__))
        #        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename) + str(inspect.currentframe().f_lineno), msgstr)
        #        return False, mt_dir_ssh_key_file
        #    }
        # }

        # Ansible実行時のSSH秘密鍵ファイルパス退避
        ssh_key_file = dst_file
        return True, ssh_key_file

    def setAnsible_win_ca_files_Dir(self, in_indir):
        """
        inディレクトリからのwinRMサーバー証明書ファイル格納ディレクトリパス(win_ca_files)を記憶
        Arguments:
            in_pkey:    win_ca_filesディレクトリ
        Returns:
            なし
        """
        self.lv_Ansible_win_ca_files_Dir = in_indir

    def getAnsible_win_ca_files_Dir(self):
        """
        inディレクトリからのSSH秘密鍵ファイルパス(ssh_key_files)を取得
        Arguments:
            in_pkey:    SSH秘密鍵ファイルのPkey(データベース)
            in_file:    SSH秘密鍵ファイル
        Returns:
            inディレクトリ内のSSH秘密鍵ファイルパス
        """
        return self.lv_Ansible_win_ca_files_Dir

    def getITA_win_ca_file(self, in_key, in_filename):
        """
        ITAが機器一覧で管理しているwinRMサーバー証明書ファイルのパスを取得
        Arguments:
            in_pkey:    winRMサーバー証明書ファイルのPkey(データベース)
            in_file:    winRMサーバー証明書ファイル名
        Returns:
            ITAが機器一覧で管理しているwinRMサーバー証明書ファイルのパス
        """
        path = "{}/{}/{}".format(getDeviceListServerCertificateUploadDirPath(), in_key, in_filename)
        return path

    def getIN_win_ca_file(self, in_pkey, in_file):
        """
        inディレクトリからのwinRMサーバー証明書ファイルパス(win_ca_files)を取得
        Arguments:
            in_pkey: winRMサーバー証明書ファイルのPkey(データベース)
            in_file: winRMサーバー証明書ファイル名
        Returns:
            inディレクトリ内のSSH認証ファイルパス
        """
        path = "{}/{}-{}".format(self.getAnsible_win_ca_files_Dir(), in_pkey, in_file)
        return path

    def CreateWIN_cs_file(self, in_pkey, in_win_ca_file):
        """
        inディレクトリにwinRMサーバー証明書ファイルをコピーする。
        Arguments:
            in_pkey:    winRMサーバー証明書ファイルのPkey(データベース)
            in_file:    winRMサーバー証明書ファイル名
        Returns:
            inディレクトリにwinRMサーバー証明書ファイルパス
        """
        win_ca_file = ""

        # サーバー証明書が存在しているか確認
        src_file = self.getITA_win_ca_file(in_pkey, in_win_ca_file)
        if os.path.isfile(src_file) is False:
            msgstr = g.appmsg.get_api_message("MSG-10548", [src_file])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, win_ca_file

        #  Ansible実行時のサーバー証明書パス取得
        dst_file = self.getIN_win_ca_file(in_pkey, in_win_ca_file)

        # サーバー証明書をansible用ディレクトリにコピーする。
        shutil.copyfile(src_file, dst_file)

        # パミッション設定
        os.chmod(dst_file, 0o600)

        # 今後修正が必要
        # 実行ユーザーがroot以外の場合、鍵ファイルのオーナーを変更
        # ExecUser = self.getAnsibleExecuteUser()
        # if((ExecUser != 'root') && (self.lv_exec_mode == DF_EXEC_MODE_ANSIBLE)) {
        #    if( !chown( dst_file, ExecUser) ){
        #        msgstr = self.lv_objMTS->getSomeMessage("ITAANSIBLEH-ERR-5000038", array(__LINE__))
        #        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename) + str(inspect.currentframe().f_lineno), msgstr)
        #        return False
        #    }
        # }

        # Ansible実行時のサーバー証明書ファイルパス退避
        win_ca_file = dst_file
        return True, win_ca_file

    # function CheckConcreteValueIsVar(in_temp_vars_chk,
    # function CheckConcreteValueIsVarTemplatefile(in_host_name, ina_var_list,
    def LegacyRoleCheckConcreteValueIsVarTemplatefile(self,
                                                      in_host_name,
                                                      ina_var_list,
                                                      in_tpf_val_name,
                                                      in_tpf_key,
                                                      in_tpf_file_name,
                                                      ina_tpf_vars_struct_json):
        
        """
        テンプレートで使用しているITA独自変数がホストの変数に登録されているか判定
        Arguments:
            in_host_name:         ホスト名
            ina_var_list:         ホスト変数リスト
            in_tpf_val_name:      テンプレート変数名
            in_tpf_key:           テンプレートファイルPkey
            in_tpf_file_name:     テンプレートファイル名
            ina_tpf_vars_struct_json: テンプレートで使用している変数の変数構造(JSON)
        Returns:
            True/False
        """

        result_code = True

        templatefile = self.getITA_template_file(in_tpf_key, in_tpf_file_name)
        if os.path.isfile(templatefile) is False:
            msgstr = g.appmsg.get_api_message("MSG-10121", [in_tpf_key, os.path.basename(templatefile)])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False

        # テンプレートに登録されているITA変数を抜出す。
        fd = open(templatefile)
        dataString = fd.read()
        fd.close()

        objConv = VarStructAnalJsonConv()
        retAry = objConv.TemplateVarStructAnalJsonLoads(ina_tpf_vars_struct_json)
        # Vars_list = retAry[0]
        # Array_vars_list = retAry[1]
        # LCA_vars_use = retAry[2]
        # Array_vars_use = retAry[3]
        GBL_vars_info = retAry[4]
        # VarVal_list = retAry[5]

        use_gbl_vars_list = {}
        # テンプレートに登録されているグローバル変数のデータベース登録確認
        if isinstance(GBL_vars_info, dict):
            if '1' in GBL_vars_info.keys():
                for var_name, dummy in GBL_vars_info['1'].items():
                    if var_name not in self.lva_global_vars_list:
                        msgstr = g.appmsg.get_api_message("MSG-10530", [os.path.basename(templatefile), var_name])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        return False
                    use_gbl_vars_list[var_name] = 1
                    self.lv_use_gbl_vars_list[var_name] = 1

        # ITA独自変数のリスト作成
        local_vars = self.setITALocalVars()

        file_vars_list = {}
        # テンプレートからローカル変数を抜出す
        varsLineArray = []
        file_vars_list = []
        FillterVars = True  # Fillterを含む変数の抜き出しあり
        obj = WrappedStringReplaceAdmin(self.lv_objDBCA)
        retAry = obj.SimpleFillterVerSearch(self.AnscObj.DF_HOST_VAR_HED, dataString, varsLineArray, file_vars_list, local_vars, FillterVars)
        # unuse ret = retAry[0]
        file_vars_list = retAry[1]

        # ITA独自変数以外を除外する。
        ita_var_list = []
        for var_name in local_vars:
            if var_name in file_vars_list:
                ita_var_list.append(var_name)
        file_vars_list = ita_var_list

        # Roleの処理なのでina_tpf_vars_struct_array['Vars_list']にリストアップされている変数をチェックする必要なし

        # Roleの処理なのでテンプレートで変数が使用されているかのチェックも不要

        # テンプレートで使用されているITA独自変数が利用可能か判定
        for var_name in file_vars_list:
            if var_name in ina_var_list:
                if var_name == self.AnscObj.ITA_SP_VAR_ANS_PROTOCOL_VAR_NAME:
                    msgstr = g.appmsg.get_api_message("MSG-10534", [os.path.basename(templatefile), var_name, in_host_name])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    result_code = False

                elif var_name == self.AnscObj.ITA_SP_VAR_ANS_USERNAME_VAR_NAME:
                    msgstr = g.appmsg.get_api_message("MSG-10535", [os.path.basename(templatefile), var_name, in_host_name])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    result_code = False

                elif var_name == self.AnscObj.ITA_SP_VAR_ANS_PASSWD_VAR_NAME:
                    msgstr = g.appmsg.get_api_message("MSG-10536", [os.path.basename(templatefile), var_name, in_host_name])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    result_code = False

                elif var_name == self.AnscObj.ITA_SP_VAR_ANS_LOGINHOST_VAR_NAME:
                    msgstr = g.appmsg.get_api_message("MSG-10537", [os.path.basename(templatefile), var_name, in_host_name])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    result_code = False

            else:
                # 予約変数を使用している場合に対象システム一覧に該当データが登録されているか判定
                if ina_var_list[var_name] == self.LC_ANS_UNDEFINE_NAME:
                    # プロトコル未登録
                    if var_name == self.AnscObj.ITA_SP_VAR_ANS_PROTOCOL_VAR_NAME:
                        msgstr = g.appmsg.get_api_message("MSG-10539", [os.path.basename(templatefile), var_name, in_host_name])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        result_code = False

                    # ユーザー名未登録
                    elif var_name == self.AnscObj.ITA_SP_VAR_ANS_USERNAME_VAR_NAME:
                        msgstr = g.appmsg.get_api_message("MSG-10540", [os.path.basename(templatefile), var_name, in_host_name])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        result_code = False

                    # ログインパスワード未登録
                    elif var_name == self.AnscObj.ITA_SP_VAR_ANS_PASSWD_VAR_NAME:
                        msgstr = g.appmsg.get_api_message("MSG-10541", [os.path.basename(templatefile), var_name, in_host_name])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        result_code = False

                    # ホスト名未登録
                    elif var_name == self.AnscObj.ITA_SP_VAR_ANS_LOGINHOST_VAR_NAME:
                        msgstr = g.appmsg.get_api_message("MSG-10542", [os.path.basename(templatefile), var_name, in_host_name])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                           str(inspect.currentframe().f_lineno), msgstr)
                        result_code = False

        return result_code

    def LegacyRoleCheckConcreteValueIsVar(self, in_var_val, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list):
        """
        変数の具体値にファイル/テンプレート変数が使用されてるかを判定
        使用されている場合に各ファイルを所定のディレクトリにコピーする。
        Arguments:
            in_var_val:                    変数の具体値
            mt_legacy_Role_cpf_vars_list:  変数の具体値にファイル変数が使用されている変数リスト
            mt_legacy_Role_tpf_vars_list:  変数の具体値にテンプレート変数が使用されている変数リスト
        Returns:
            True/False, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list
        """
        vars_list = {}
        var_type = ""

        if not in_var_val:
            return True, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list
        # ファイル管理変数　{{ CPF_[a-zA-Z0-9_] }} を取出す
        keyFilter = r"{{[\s]CPF_[a-zA-Z0-9_]*[\s]}}"
        var_match = re.findall(keyFilter, in_var_val)
        for var_name_str in var_match:
            # 両端の{{}}を取り除く
            keyFilter = r"CPF_[a-zA-Z0-9_]*"
            var_names = re.findall(keyFilter, in_var_val)
            for var_name in var_names:
                if var_name not in mt_legacy_Role_cpf_vars_list:
                    vars_list[var_name] = "CPF"

        # テンプレート変数　{{ TPF_[a-zA-Z0-9_] }} を取出す
        keyFilter = r"{{[\s]TPF_[a-zA-Z0-9_]*[\s]}}"
        var_match = re.findall(keyFilter, in_var_val)
        for var_name_str in var_match:
            # 両端の{{}}を取り除く
            keyFilter = r"TPF_[a-zA-Z0-9_]*"
            var_names = re.findall(keyFilter, in_var_val)
            for var_name in var_names:
                if var_name not in mt_legacy_Role_tpf_vars_list:
                    vars_list[var_name] = "TPF"

        if len(vars_list) == 0:
            return True, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

        tpf_fileInfo = {}
        cpf_fileInfo = {}
        # unuse strErrMsg = ""
        # unuse strErrDetailMsg = ""
        key = ""
        file_name = ""
        for var_name, var_type in vars_list.items():
            if var_type == "CPF":
                if var_name not in mt_legacy_Role_cpf_vars_list:
                    # ファイル管理変数名からコピーファイル名とPkeyを取得する。
                    key = ""
                    file_name = ""
                    retAry = self.getDBCopyMaster(var_name, key, file_name)
                    ret = retAry[0]
                    key = retAry[1]
                    file_name = retAry[2]
                    if ret is False:
                        msgstr = g.appmsg.get_api_message("MSG-10543", [var_name])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                            str(inspect.currentframe().f_lineno), msgstr)
                        return False, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list
                    else:
                        # コピーファイル名が未登録の場合
                        if not file_name:
                            msgstr = g.appmsg.get_api_message("MSG-10544", [var_name])
                            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                               str(inspect.currentframe().f_lineno), msgstr)
                            return False, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

                    # inディレクトリ配下のファイルバスを取得
                    path = self.getHostvarsfile_copy_file_value(key, file_name)
                    path = self.setAnsibleSideFilePath(path, self.LC_ITA_IN_DIR)

                    # mt_legacy_Role_cpf_vars_list[copy変数]=inディレクトリ配下のファイルパス
                    mt_legacy_Role_cpf_vars_list[var_name] = path

                    # copyファイルのpkeyとファイル名を退避
                    cpf_fileInfo[key] = file_name

            else:
                if var_name not in mt_legacy_Role_tpf_vars_list:
                    # template変数名からtemplateファイル名とPkeyを取得する。
                    tpf_var_name = var_name
                    tpf_key = ""
                    tpf_file_name = ""
                    role_only = ""
                    tpf_vars_struct_json = {}
                    retAry = self.getDBTemplateMaster(tpf_var_name, tpf_key, tpf_file_name, role_only, tpf_vars_struct_json)
                    ret = retAry[0]
                    tpf_key = retAry[1]
                    tpf_file_name = retAry[2]
                    role_only = retAry[3]
                    tpf_vars_struct_json = retAry[4]
                    if ret is False:
                        msgstr = g.appmsg.get_api_message("MSG-10531", [tpf_var_name])
                        self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                            str(inspect.currentframe().f_lineno), msgstr)
                        return False, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list
                    else:
                        if not tpf_file_name:
                            # テンプレートファイル名が未登録の場合
                            msgstr = g.appmsg.get_api_message("MSG-10558", [tpf_var_name])
                            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                               str(inspect.currentframe().f_lineno), msgstr)
                            return False, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

                    # inディレクトリ配下のテンプレートファイルバスを取得
                    path = self.getHostvarsfile_template_file_path(tpf_key, tpf_file_name)
                    path = self.setAnsibleSideFilePath(path, self.LC_ITA_IN_DIR)

                    # mt_legacy_Role_tpf_vars_list[copy変数]=inディレクトリ配下のテンプレートファイルパス
                    mt_legacy_Role_tpf_vars_list[tpf_var_name] = path

                    # テンプレートファイルのpkeyとファイル名を退避
                    tpf_fileInfo[tpf_key] = tpf_file_name

                    # 呼び元からパラメータで受け取ることが困難なので、クラス変数経由で受け取る
                    host_name = self.LegacyRoleCheckConcreteValueIsVar_use_host_name

                    # テンプレートファイル内のホスト変数を確認
                    ret = self.LegacyRoleCheckConcreteValueIsVarTemplatefile(host_name,
                                                                             self.LegacyRoleCheckConcreteValueIsVar_use_var_list[host_name],
                                                                             tpf_var_name,
                                                                             tpf_key,
                                                                             tpf_file_name,
                                                                             tpf_vars_struct_json)
                    if ret is False:
                        return False, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

        # ファイル管理ファイルを所定のディレクトリにコピーする。
        if len(cpf_fileInfo) > 0:
            ret = self.CreateCopyfiles(cpf_fileInfo)
            if ret is False:
                return False, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

        # テンプレートファイルを所定のディレクトリにコピーする。
        if len(tpf_fileInfo) > 0:
            ret = self.CreateTemplatefiles(tpf_fileInfo)
            if ret is False:
                return False, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

        return True, mt_legacy_Role_cpf_vars_list, mt_legacy_Role_tpf_vars_list

    # def CommitHostVarsfiles(ina_hosts, ina_hostprotcollist, ina_host_vars, ina_pioneer_template_host_vars){
    # def getHostvarsfile_pioneer_copy_file_value(in_pkey, in_file){
    # def CreatePioneerCopyFiles(ina_hosts, ina_dialog_files, ina_hostprotcollist, ina_host_vars){
    # def setITA_pns_template_file_Dir(self, in_indir):
    #  不要 getTemplateContentUploadDirPath
    # def getITA_pns_template_file_Dir():
    # getITA_template_fileに置換え
    # def getITA_pns_template_file(in_key, in_filename){
    #  getITA_pns_template_fileはgetITA_template_fileに置換える
    # def getHostvarsfile_pioneer_template_file_value(in_pkey, in_file, in_hostname) {
    # def getHostvarsfile_pioneer_template_file(in_pkey, in_file) {
    # def CreatePioneertemplatefiles(ina_hosts, ina_dialog_files, ina_hostprotcollist, ina_host_vars) {
    # def CopyPioneerTemplatefiles(ina_template_files) {
    def CreateLegacyRoleTemplateFiles(self, ina_hosts, ina_rolenames, ina_tpf_vars_list):
        """
        playbook内で使用しているテンプレート管理のファイルを所定の場所にコピーする
        Arguments:
            ina_hosts:         機器一覧ホスト一覧
            ina_rolenames:     処理対象ロールリスト
            ina_tpf_vars_list: テンプレート変数リスト
        Returns:
            True/False
        """
        # 処理対象のロール名抽出
        tgt_role_list = {}
        for no, rolename_list in ina_rolenames.items():
            for rolepkey, rolename in rolename_list.items():
                tgt_role_list[rolename] = 1

        # 処理対象のロールで使用しているテンプレート変数か判定
        la_tpf_files = {}
        la_tpf_path = {}
        for role_name, tgt_file_list in ina_tpf_vars_list.items():
            if role_name not in tgt_role_list:
                continue
            for tgt_file, line_no_list in tgt_file_list.items():
                for line_no, tpf_var_name_list in line_no_list.items():
                    for tpf_var_name, file_info_list in tpf_var_name_list.items():
                        # inディレクトリ配下のcopyファイルバスを取得
                        tpf_path = self.getHostvarsfile_template_file_path(file_info_list['CONTENTS_FILE_ID'], file_info_list['CONTENTS_FILE'])

                        # ファイルパスをansible側から見たパスに変更する。
                        tpf_path = self.setAnsibleSideFilePath(tpf_path, self.LC_ITA_IN_DIR)

                        # la_tpf_path[テンプレート変数]=inディレクトリ配下ののファイルパス
                        la_tpf_path[tpf_var_name] = tpf_path

                        # テンプレートファイルのpkeyとファイル名を退避
                        la_tpf_files[file_info_list['CONTENTS_FILE_ID']] = file_info_list['CONTENTS_FILE']

        # テンプレート変数kのファイルを所定の場所にコピー
        if len(la_tpf_files) > 0:
            ret = self.CreateTemplatefiles(la_tpf_files)
            if ret is False:
                return False

        # ホスト変数定義ファイルにテンプレート変数を追加
        if len(la_tpf_files) > 0:
            # 作業対象ホスト分ループ
            for id, host_name in ina_hosts.items():
                # ホスト変数定義ファイル名を取得
                file_name = self.getAnsible_host_var_file(host_name)
                # ホスト変数定義ファイルにテンプレート変数を追加
                if self.CreateRoleHostvarsfile("TPF", file_name, la_tpf_path, "", "", "", "", "a") is False:
                    return False
                    
        return True

    # def TemplateMmoduleAddPlaybook(in_tpf_path) {
    # def var_check (dialog_file_name, hostname, dialog_file_vars, host_variable_file_array){
    # def value_extraction (array, mae, &dialog_file_vars){
    def makeAnsibleVaultPassword(self, in_pass, in_vaultpass, in_indento, in_system_id):
        """
        指定文字列の暗号化及びインデント付加
        Arguments:
            in_pass: 暗号化する文字列
            in_vaultpass: 暗号化した文字列
            in_indento: 暗号化した文字列に付加するインデント
            in_system_id: 機器一覧のPkey
        Returns:
            False/暗号化された文字列
        """
        out_vaultpass = ""

        update_key = "key_{}_{}".format(in_system_id, in_pass)

        obj = AnsibleVault()
        
        if not in_vaultpass:

            # パスワードが暗号化されているか判定
            if in_pass in self.lv_vault_pass_list:
                out_vaultpass = self.lv_vault_pass_list[in_pass]
            else:
                VaultPasswordFilePath = obj.CreateVaultPasswordFilePath()
                # in_passはrot13+base64で複合化されている
                obj.CreateVaultPasswordFile(VaultPasswordFilePath, self.lv_ans_if_info['ANSIBLE_VAULT_PASSWORD'])
                retAry = obj.Vault(self.lv_ans_if_info['ANSIBLE_CORE_PATH'],
                                   self.getAnsibleExecuteUser(),
                                   VaultPasswordFilePath,
                                   in_pass,
                                   "",
                                   self.lv_engine_virtualenv_name,
                                   True)
                ret = retAry[0]
                out_vaultpass = retAry[1]
                if ret is False:
                    # ansible-vault失敗
                    msgstr = g.appmsg.get_api_message("MSG-10646", [in_system_id])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    # 標準エラー出力を出力
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), out_vaultpass)
                    return False
                self.lv_vault_pass_list[in_pass] = out_vaultpass
            out_vaultpass = " !vault |" + out_vaultpass

            # 機器一覧の暗号化パスワードを更新済みか判定
            if update_key not in self.lv_vault_pass_update_list:

                # 機器一覧にansible-vaultで暗号化した文字列を登録
                UpData = {}
                UpData["LOGIN_PW_ANSIBLE_VAULT"] = out_vaultpass
                UpData["SYSTEM_ID"] = in_system_id
                ret = self.lv_objDBCA.table_update("T_ANSC_DEVICE", UpData, "SYSTEM_ID", False)
                # Autocommitがoffになっており、呼び元でトランザクションもoffなのでcommitする。
                self.lv_objDBCA.db_commit()
                # 機器一覧の暗号化パスワードを更新済設定
                self.lv_vault_pass_update_list[update_key] = 'update'
        else:
            out_vaultpass = in_vaultpass

        # ansible-vaultで暗号化された文字列のインデントを調整
        out_vaultpass = obj.setValutPasswdIndento(out_vaultpass, in_indento)

        return out_vaultpass

    # def makeAnsibleVaultSSHFile(in_exec_user, in_file_id, in_sshKeyFile, in_vault_sshKeyFileData, in_system_id) {
    def makeAnsibleVaultValue(self, in_pass, in_vaultpass, in_indento, in_assign_id):
        """
        指定文字列をansible-vaultで暗号化する
        Arguments:
            in_pass:        暗号化したい文字列
            in_vaultpass:   暗号化されている場合の暗号化文字列
            in_indento:     暗号化文字列に付加するインデント
            in_assign_id:   代入値管理項番
        Returns:
            [ 暗号化された文字列]
        """
        out_vaultpass = ""

        # unuse update_key = "key_{}_{}".format(in_assign_id, in_pass)

        obj = AnsibleVault()

        if not in_vaultpass:

            # パスワードが暗号化されているか判定
            if in_pass in self.lv_vault_value_list:
                # 既に暗号化されている場合
                out_vaultpass = self.lv_vault_value_list[in_pass]
            else:
                # in_passはrot13+base64で暗号化されている
                # unuse enc_in_pass = in_pass
                VaultPasswordFilePath = obj.CreateVaultPasswordFilePath()
                # in_passはrot13+base64で暗号化されている
                obj.CreateVaultPasswordFile(VaultPasswordFilePath, self.lv_ans_if_info['ANSIBLE_VAULT_PASSWORD'])
                retAry = obj.Vault(self.lv_ans_if_info['ANSIBLE_CORE_PATH'],
                                   self.getAnsibleExecuteUser(),
                                   VaultPasswordFilePath,
                                   in_pass,
                                   "",
                                   self.lv_engine_virtualenv_name, True)
                ret = retAry[0]
                out_vaultpass = retAry[1]
                if ret is False:
                    # ansible-vault失敗
                    msgstr = g.appmsg.get_api_message("MSG-10626", [in_assign_id])
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), msgstr)
                    # 標準エラー出力を出力
                    self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                                       str(inspect.currentframe().f_lineno), out_vaultpass)
                    return False
                self.lv_vault_value_list[in_pass] = out_vaultpass
            out_vaultpass = " !vault |" + out_vaultpass
        else:
            # このルートは基本的デットルート
            out_vaultpass = in_vaultpass

        # ansible-vaultで暗号化された文字列のインデントを調整
        out_vaultpass = obj.setValutPasswdIndento(out_vaultpass, in_indento)

        return out_vaultpass

    def getAnsibleExecuteUser(self):
        """
        ansibleコマンド実行ユーザー取得
        Arguments:
        Returns:
            ansibleコマンド実行ユーザー
        """
        return self.ansible_exec_user

    def setAnsibleExecuteUser(self, user_name):
        """
        ansibleコマンド実行ユーザー退避
        Arguments:
            ansibleコマンド実行ユーザー
        Returns:
            なし
        """
        if user_name:
            # 非コンテナ版ではuser名の指定がない場合はrootにする。
            # コンテナ版ではuser名の指定出来ないのでコメントなする
            # user_name = 'root'
            user_name = ""
        self.ansible_exec_user = user_name

    def HostVarEdit(self, val, NumPadding):
        """
        ホスト変数の具体値を指定サイズでパディングする
        Arguments:
            val:
            NumPadding: パディングサイズ
        Returns:
            パディングされたホスト変数の具体値
        """
        # josn形式(複数具体値)か判定
        if self.isJsonString(val) is False:
            val = self.MultilineValueEdit(val, NumPadding)
        else:
            val = self.MultiValueEdit(val, NumPadding)
        return val

    def MultilineValueEdit(self, val, NumPadding):
        """
        複数行複数具体値にインデントを設定する。
            ArrayTypeValue_decode
        Arguments:
            jsonstr: 複数行複数具体値
            NumPadding: パディング文字数
        Returns:
            複数行複数具体値にインデントを設定した文字列
        """
        # 具体値がNoneの場合に空白に置換える
        if not val:
            val = ""
            return val
        strpad = "".ljust(NumPadding)
        if len(val.split("\n")) > 1:
            val = val.replace("\n", "\n" + strpad)
        return val

    def chkMultilineValue(self, val):
        """
        Pioneerの場合に具体値が複数行か判定
        Arguments:
            val: 具体値
        Returns:
            True/False
        """
        if self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
            if len(val.split("\n")) > 1:
                return False
        return True

    def makeMultilineValue(self, val):
        """
        複数行具体値の場合に複数行の扱いの記号を付ける
        Arguments:
            val: 複数行具体値
        Returns:
            複数行の扱いの記号を付加した具体値
        """
        if not val:
            return val
        if len(val.split("\n")) > 1:
            val = "|-\n" + val
        return val

    # def getArrayTypeValuecount(self, val):
    def ArrayTypeValue_encode(seld, mt_jsonstr, val):
        """
        複数行具体値をjson形式で収める
        Arguments:
            mt_jsonstr: 現在の具体値
            val: 追加する具体値
        Returns:
            複数行具体値の数, 追加結果
        """
        if len(mt_jsonstr) == 0:
            ary = []
        else:
            ary = json.loads(mt_jsonstr)

        ary.append(val)
        mt_jsonstr = json.dumps(ary)

        return len(ary), mt_jsonstr

    def MultiValueEdit(self, jsonstr, NumPadding):
        """
        JSON文字列内の複数具体値にインデントを設定する。
            ArrayTypeValue_decode
        Arguments:
            jsonstr: JSON文字列
            NumPadding: パディング文字数
        Returns:
            複数具体にインデントを設定したJSON文字列
        """
        val = ""
        strpad = "".ljust(NumPadding)
        indstrpad = "".ljust(NumPadding + 2)
        # 具体値が空の場合
        ary = json.loads(jsonstr)
        for line in ary:
            # 具体値が空か判定
            if line:
                # 空以外
                if len(line.split("\n")) != 1:
                    line = line.replace("\n", "\n" + indstrpad)
                    val += "\n{}- {}".format(strpad, line)
                else:
                    val += "\n{}- {}".format(strpad, line)
            else:
                # 空
                line = ""
                val += "\n{}- {}".format(strpad, line)
                
        return val

    def isJsonString(self, json_str):
        """
        指定文字列がJSON形式か判定する
            isArrayTypeValue
        Arguments:
            string: 文字列
        Returns:
            True/False
        """
        try:
            ret = json.loads(json_str)
            if isinstance(ret, list) is False:
                return False
            return True
        except Exception as e:
            return False

    def getAnsible_vault_host_var_file(self, in_hostname):
        """
        暗号化されているホスト変数定義ファイルパスを取得
        Arguments:
            in_hostname: ホスト名
        Returns:
            暗号化されているホスト変数定義ファイルパス
        """
        file = "{}/{}".format(self.getAnsible_vault_hosts_vars_Dir(), in_hostname)
        return file

    def CreateDirectoryForCollectionProcess(self, ina_hostinfolist, mt_host_vars, mt_pioneer_template_host_vars):
        """
        収集機能用ディレクトリ生成
        Arguments:
            ina_hostinfolist:   機器一覧ホスト情報
                                {HOST_NAME:{機器一覧各項目:xx, ....}} ...
            mt_host_vars: ホスト変数定義配列
            mt_pioneer_template_host_vars: pioneer tamplate用 ホスト変数定義配列
        Returns:
            True, mt_host_vars mt_pioneer_template_host_vars
        """
        driver_list = {}
        driver_list[self.AnscObj.DF_LEGACY_DRIVER_ID] = 'ansible/legacy'
        driver_list[self.AnscObj.DF_PIONEER_DRIVER_ID] = 'ansible/pioneer'
        driver_list[self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID] = 'ansible/legacy_role'

        # ドライバ種別
        driver_id = self.getAnsibleDriverID()
        # 作業番号
        execute_no = self.lv_exec_no
        # データリレイストレージパス(ITA)
        ita_base_dir = self.getAnsibleBaseDir('ANSIBLE_SH_PATH_ITA')
        # データリレイストレージパス(ansible)
        ans_base_dir = self.getAnsibleBaseDir('ANSIBLE_SH_PATH_ANS')

        for host_name, hostinfo in ina_hostinfolist.items():
            host_var_name = self.AnscObj.ITA_SP_VAR_IN_PARAM_DIR_EPC

            mkdir = "{}/{}/{}/in/_parameters/{}".format(ita_base_dir, driver_list[driver_id], execute_no, host_name)
            scpsrcdir = "{}/{}/{}/in/_parameters".format(ita_base_dir, driver_list[driver_id], execute_no)

            if self.lv_exec_mode == self.AnscObj.DF_EXEC_MODE_ANSIBLE:
                host_var_vaule = "{}/{}/{}/in/_parameters".format(ans_base_dir, driver_list[driver_id], execute_no)
            else:
                host_var_vaule = "{}/_parameters".format(self.getTowerProjectDirPath("ExastroPath"))
                self.setTowerProjectsScpPath(self.AnscObj.DF_SCP_IN_PARAMATERS_ITA_PATH, scpsrcdir)
                self.setTowerProjectsScpPath(self.AnscObj.DF_SCP_IN_PARAMATERS_TOWER_PATH, host_var_vaule)

            # ディレクトリ生成
            self.makeDir(mkdir)

            if host_name not in mt_host_vars:
                mt_host_vars[host_name] = {}
            mt_host_vars[host_name][host_var_name] = host_var_vaule
            if self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
                if host_name not in mt_pioneer_template_host_vars:
                    mt_pioneer_template_host_vars[host_name] = {}
                mt_pioneer_template_host_vars[host_name][host_var_name] = host_var_vaule

            host_var_name = self.AnscObj.ITA_SP_VAR_OUT_PARAM_DIR

            mkdir = "{}/{}/{}/out/_parameters/{}".format(ita_base_dir, driver_list[driver_id], execute_no, host_name)
            host_var_vaule = "{}/{}/{}/out/_parameters".format(ita_base_dir, driver_list[driver_id], execute_no)

            if self.lv_exec_mode == self.AnscObj.DF_EXEC_MODE_ANSIBLE:
                host_var_vaule = "{}/{}/{}/out/_parameters".format(ans_base_dir, driver_list[driver_id], execute_no)
            else:
                host_var_vaule = "{}/{}/_parameters".format(self.getTowerProjectDirPath("ExastroPath"), self.LC_ITA_OUT_DIR)

            # ディレクトリ生成
            self.makeDir(mkdir)

            if host_name not in mt_host_vars:
                mt_host_vars[host_name] = {}
            mt_host_vars[host_name][host_var_name] = host_var_vaule
            if self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
                if host_name not in mt_pioneer_template_host_vars:
                    mt_pioneer_template_host_vars[host_name] = {}
                mt_pioneer_template_host_vars[host_name][host_var_name] = host_var_vaule

            host_var_name = self.AnscObj.ITA_SP_VAR_IN_PARAM_FILE_DIR_EPC

            mkdir = "{}/{}/{}/in/_parameters_file/{}".format(ita_base_dir, driver_list[driver_id], execute_no, host_name)
            scpsrcdir = "{}/{}/{}/in/_parameters_file".format(ita_base_dir, driver_list[driver_id], execute_no)
            host_var_vaule = "{}/{}/{}/in/_parameters_file".format(ita_base_dir, driver_list[driver_id], execute_no)
            if self.lv_exec_mode == self.AnscObj.DF_EXEC_MODE_ANSIBLE:
                host_var_vaule = "{}/{}/{}/in/_parameters_file".format(ans_base_dir, driver_list[driver_id], execute_no)
            else:
                host_var_vaule = "{}/_parameters_file".format(self.getTowerProjectDirPath("ExastroPath"))
                self.setTowerProjectsScpPath(self.AnscObj.DF_SCP_IN_PARAMATERS_FILE_ITA_PATH, scpsrcdir)
                self.setTowerProjectsScpPath(self.AnscObj.DF_SCP_IN_PARAMATERS_FILE_TOWER_PATH, host_var_vaule)

            # ディレクトリ存在確認
            self.makeDir(mkdir)

            if host_name not in mt_host_vars:
                mt_host_vars[host_name] = {}
            mt_host_vars[host_name][host_var_name] = host_var_vaule
            if self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
                if host_name not in mt_pioneer_template_host_vars:
                    mt_pioneer_template_host_vars[host_name] = {}
                mt_pioneer_template_host_vars[host_name][host_var_name] = host_var_vaule

            host_var_name = self.AnscObj.ITA_SP_VAR_OUT_PARAM_FILE_DIR

            mkdir = "{}/{}/{}/out/_parameters_file/{}".format(ita_base_dir, driver_list[driver_id], execute_no, host_name)
            host_var_vaule = "{}/{}/{}/out/_parameters_file".format(ita_base_dir, driver_list[driver_id], execute_no)
            if self.lv_exec_mode == self.AnscObj.DF_EXEC_MODE_ANSIBLE:
                host_var_vaule = "{}/{}/{}/out/_parameters_file".format(ans_base_dir, driver_list[driver_id], execute_no)
            else:
                host_var_vaule = "{}/{}/_parameters_file".format(self.getTowerProjectDirPath("ExastroPath"), self.LC_ITA_OUT_DIR)

            # ディレクトリ存在確認
            self.makeDir(mkdir)

            if host_name not in mt_host_vars:
                mt_host_vars[host_name] = {}
            mt_host_vars[host_name][host_var_name] = host_var_vaule
            if self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
                if host_name not in mt_pioneer_template_host_vars:
                    mt_pioneer_template_host_vars[host_name] = {}
                mt_pioneer_template_host_vars[host_name][host_var_name] = host_var_vaule

        return True, mt_host_vars, mt_pioneer_template_host_vars

    def makeDir(self, mkdir):
        """
        ディレクトリ生成
        Arguments:
            mkdir: ディレクトリパス
        Returns:
            なし
        """
        dirsLlist = mkdir.split("/")
        dirsLlist.pop(0)
        makeDirName = ""
        for dir in dirsLlist:
            makeDirName += "/" + dir
            if os.path.isdir(makeDirName) is False:
                os.mkdir(makeDirName)
                os.chmod(makeDirName, 0o777)

    def CreateMovementStatusFileVariables(self, ina_hostinfolist, mt_host_vars, mt_pioneer_template_host_vars):
        """
        Movementステータスファイル変数生成
        Arguments:
            ina_hostinfolist:   機器一覧ホスト情報
                                {HOST_NAME:{機器一覧各項目:xx, ....}} ...
            mt_host_vars:       ホスト変数定義配列
            mt_pioneer_template_host_vars: pioneer tamplate用 ホスト変数定義配列
        Returns:
            True, mt_host_vars mt_pioneer_template_host_vars
        """
        driver_list = {}
        driver_list[self.AnscObj.DF_LEGACY_DRIVER_ID] = 'ansible/legacy'
        driver_list[self.AnscObj.DF_PIONEER_DRIVER_ID] = 'ansible/pioneer'
        driver_list[self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID] = 'ansible/legacy_role'

        # ドライバ種別
        driver_id = self.getAnsibleDriverID()
        # 作業番号
        execute_no = self.lv_exec_no
        # データリレイストレージパス(ITA)
        # unuse ita_base_dir = self.getAnsibleBaseDir('ANSIBLE_SH_PATH_ITA')
        # データリレイストレージパス(ansible)
        ans_base_dir = self.getAnsibleBaseDir('ANSIBLE_SH_PATH_ANS')

        for host_name, hostinfo in ina_hostinfolist.items():

            host_var_name = self.AnscObj.ITA_SP_VAR_MOVEMENT_STS_FILE

            host_var_vaule = "{}/{}/{}/out/MOVEMENT_STATUS_FILE".format(ans_base_dir, driver_list[driver_id], execute_no)
            if self.lv_exec_mode == self.AnscObj.DF_EXEC_MODE_ANSIBLE:
                host_var_vaule = "{}/{}/{}/out/MOVEMENT_STATUS_FILE".format(ans_base_dir, driver_list[driver_id], execute_no)
            else:
                host_var_vaule = "{}/{}/MOVEMENT_STATUS_FILE".format(self.getTowerProjectDirPath("ExastroPath"), self.LC_ITA_OUT_DIR)

            if host_name not in mt_host_vars:
                mt_host_vars[host_name] = {}
            mt_host_vars[host_name][host_var_name] = host_var_vaule
            if self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
                if host_name not in mt_pioneer_template_host_vars:
                    mt_pioneer_template_host_vars[host_name] = {}
                mt_pioneer_template_host_vars[host_name][host_var_name] = host_var_vaule

        return True, mt_host_vars, mt_pioneer_template_host_vars

    def CreatePioneerLANGVariables(self, ina_hostinfolist, mt_host_vars):
        """
        Pioneer LAMG用 ローカル変数設定
        Arguments:
            ina_hostinfolist: 機器一覧ホスト情報配列
            mt_host_vars:      ホスト変数定義配列
        Returns:
            True, mt_host_vars
        """
        if self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
            for host_name, hostinfo in ina_hostinfolist.items():
                if host_name not in ina_hostinfolist:
                    mt_host_vars[host_name] = {}
                mt_host_vars[host_name][self.LC_ANS_PIONEER_LANG_VAR_NAME] = hostinfo['PIONEER_LANG_STRING']

        return True, mt_host_vars

    def CreateOperationVariables(self, in_operation_id, ina_hostinfolist, mt_host_vars, mt_pioneer_template_host_vars):
        """
        オペレーション用 予約変数設定
        Arguments:
            in_operation_id:                オペレーションID
            ina_hostinfolist:               機器一覧ホスト情報配列
            mt_host_vars:                   ホスト変数定義配列
            mt_pioneer_template_host_vars:  pioneer tamplate用 ホスト変数定義配列
        Returns:
            Bool, mt_host_vars, mt_pioneer_template_host_vars
        """
        sql = '''
        SELECT
            OPERATION_NAME,
            DATE_FORMAT(OPERATION_DATE, '%%Y/%%m/%%d %%H:%%i') OPERATION_DATE
        FROM
            T_COMN_OPERATION
        WHERE
            OPERATION_ID = %s
                '''
        rows = self.lv_objDBCA.sql_execute(sql, [in_operation_id])

        if len(rows) != 1:
            #
            msgstr = g.appmsg.get_api_message("MSG-10178", [os.path.basename(__file__), self.lineno()])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False, mt_host_vars, mt_pioneer_template_host_vars

        operationStr = ""
        operationStr = "{}_{}:{}".format(rows[0]['OPERATION_DATE'], in_operation_id, rows[0]['OPERATION_NAME'])

        # オペレーション用の予約変数生成
        for host_name, hostinfo in ina_hostinfolist.items():
            if host_name not in mt_host_vars:
                mt_host_vars[host_name] = {}
            mt_host_vars[host_name][self.AnscObj.ITA_SP_VAR_OPERATION_VAR_NAME] = operationStr

            # Pioneerの場合の処理
            # switch(self.getAnsibleDriverID()){
            # case DF_PIONEER_DRIVER_ID:
            #    ina_pioneer_template_host_vars[host_ip][self.AnscObj.ITA_SP_VAR_OPERATION_VAR_NAME] = operationStr
            #    break
            # }
        return True, mt_host_vars, mt_pioneer_template_host_vars

    def CreateSSHAgentConfigInfoFile(self, file, hostname, ssh_key_file, pssphrase):
        """
        ssh-agentの設定に必要な情報を一時ファイルに出力
        Arguments:
            file:          一時ファイル名
            hostname:      ホスト名
            ssh_key_file:  秘密鍵ファイル
            pssphrase      パスフレーズ
        Returns:
            True/False
        """
        row = "{}\t{}\t{}\t\n".format(hostname, ssh_key_file, pssphrase)
        fd = open(file, 'a')
        fd.write(row)
        fd.close()
        return True

    def setFileUploadCloumnFileEnv(self, in_ans_if_info, row):
        """
        ロールパッケージ管理の情報を取得
        Arguments:
            in_ans_if_info: インターフェース情報
            row:            代入値管理の情報
        Returns:
            True/False
        """
        if not row['VARS_ENTRY_FILE']:
            return True

        if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID or\
           self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID or\
           self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
            srcFilePath = "{}/{}/{}".format(getFileupLoadColumnPath('20409', 'file'), row['ASSIGN_ID'], row['VARS_ENTRY_FILE'])

        if os.path.isfile(srcFilePath) is False:
            msgstr = g.appmsg.get_api_message("MSG-10171", [row['ASSIGN_ID']])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False

        ITADestDirPath = "{}/{}".format(self.getAnsible_upload_files_Dir(), row['ASSIGN_ID'])

        AnsDestDirPath = self.setAnsibleSideFilePath(ITADestDirPath, self.LC_ITA_IN_DIR)
        if os.path.isdir(ITADestDirPath) is False:
            os.mkdir(ITADestDirPath)
            os.chmod(ITADestDirPath, 0o777)

        ITADestDirPath += "/" + row['VARS_ENTRY_FILE']
        AnsDestDirPath += "/" + row['VARS_ENTRY_FILE']

        shutil.copyfile(srcFilePath, ITADestDirPath)

        row['VARS_ENTRY'] = AnsDestDirPath
        row['VARS_ENTRY_FILE'] = ""
        return True

    def AnsibleEnginVirtualenvPathCheck(self):
        """
        仮想環境存在確認
        2.0ではコンテナ版のみなので空処理にしておく
        Arguments:
            なし
        Returns:
            True
        """
        return True

    # def GetEngineVirtualenvName() {
    def getTowerProjectDirPath(self, PathId):
        """
        Towerプロジェクトパス取得
        Arguments:
            PathId: TowerPath/ExastroPath
        Returns:
            Towerプロジェクトパス
        """
        # lv_TowerInstanceDirPath["TowerPath"]   "Tower Projects Ptah
        # lv_TowerInstanceDirPath["ExastroPath"] "Tower Exastro Projects Ptah
        return self.lv_TowerInstanceDirPath[PathId]

    def getTowerInstanceDirPath(self):
        """
        Tower/Exastorプロジェクトパス取得()
        Arguments:
            なし
        Returns:
            Towerプロジェクトパス
        """
        return self.lv_TowerInstanceDirPath

    def setTowerProjectDirPath(self):
        """
        AAC側のProjectディレクトリパス生成
        Arguments:
            なし
        Returns:
            True
        """
        gobj = AnscConst()

        if self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_DRIVER_ID:
            driver_name = "ita_legacy_executions"
        elif self.getAnsibleDriverID() == self.AnscObj.DF_PIONEER_DRIVER_ID:
            driver_name = "ita_pioneer_executions"
        elif self.getAnsibleDriverID() == self.AnscObj.DF_LEGACY_ROLE_DRIVER_ID:
            driver_name = "ita_legacy_role_executions"

        self.lv_TowerInstanceDirPath = {}

        # /var/lib/awx/projects/{{ driver_name }}-{{ 作業番号 }}
        self.lv_TowerInstanceDirPath["TowerPath"] = "{}/{}_{}".format(gobj.DF_TowerProjectPath, driver_name, self.lv_exec_no)
        # /var/lib/exastro/{{ driver_name }}-{{ 作業番号 }}
        self.lv_TowerInstanceDirPath["ExastroPath"] = "{}/{}_{}".format(gobj.DF_TowerExastroProjectPath, driver_name, self.lv_exec_no)
        
        return True

    def setAnsibleSideFilePath(self, in_Path, in_DirId):
        """
        指定ファイルのパスをAnsible側のパスに変更
        Arguments:
            in_Path: ファイルのパス
            in_DirId: ディレクトリ
        Returns:
            Upd_Path Ansible側のパス
        """
        if self.lv_exec_mode == self.AnscObj.DF_EXEC_MODE_ANSIBLE:
            Upd_Path = in_Path.replace(self.getAnsibleBaseDir('ANSIBLE_SH_PATH_ITA'), self.getAnsibleBaseDir('ANSIBLE_SH_PATH_ANS'))
        else:
            Upd_Path = self.setAnsibleTowerSideFilePath(in_Path, in_DirId)
            
        return Upd_Path

    def setAnsibleTowerSideFilePath(self, in_Path, in_DirId):
        """
        指定ファイルのパスをTower側のパスに変更
        Arguments:
            in_Path: ファイルのパス
            in_DirId: ディレクトリ
        Returns:
            Upd_Path Tower側のパス
        """
        # ホスト変数定義ファイルに記載するパスなのでAnsible側のストレージパスに変更
        if in_DirId == self.LC_ITA_OUT_DIR:
            Aft_Path = "{}/{}".format(self.getTowerProjectDirPath("ExastroPath"), in_DirId)
            Upd_Path = in_Path.replace(self.getAnsible_out_Dir(), Aft_Path)
        elif in_DirId == self.LC_ITA_IN_DIR:
            Aft_Path = self.getTowerProjectDirPath("ExastroPath")
            Upd_Path = in_Path.replace(self.getAnsible_in_Dir(), Aft_Path)
        elif in_DirId == self.LC_ITA_TMP_DIR:
            Aft_Path = "{}/{}".format(self.getTowerProjectDirPath("ExastroPath"), in_DirId)
            Upd_Path = in_Path.replace(self.getAnsible_tmp_Dir(), Aft_Path)

        return Upd_Path

    def setTowerProjectsScpPath(self, id, path):
        """
        AACへのSCPパス退避
        Arguments:
            id:  SCPパスID
            path: AACへのSCPパス
        Returns:
            なし
        """
        self.vg_TowerProjectsScpPathArray[id] = path

    def getTowerProjectsScpPath(self):
        """
        AACへのSCPパス取得
        Arguments:
            なし
        Returns:
            AACへのSCPパス
        """
        return self.vg_TowerProjectsScpPathArray

    def CopyAnsibleConfigFile(self):
        """
        Movement一覧に登録されているansible.cnfを所定の場所にコピーする。
        Arguments:
            なし
        Returns:
            True/False
        """
        src_file = "{}/{}/{}".format(getMovementAnsibleCnfUploadDirPath(), self.run_pattern_id, self.lv_ansible_cnf_file)
        dest_file = "{}/{}".format(self.getAnsible_in_Dir(), "/ansible.cfg")
        if os.path.isfile(src_file) is False:
            msgstr = g.appmsg.get_api_message("MSG-10068", [self.run_pattern_id])
            self.LocalLogPrint(os.path.basename(inspect.currentframe().f_code.co_filename),
                               str(inspect.currentframe().f_lineno), msgstr)
            return False
        shutil.copyfile(src_file, dest_file)
        return True

    def CopysshAgentExpectfile(self):
        """
        Ansible実行時、aah-agentで必要なexpectファイルを所定の場所にコピーする。
        Arguments:
            なし
        Returns:
            True/False
        """
        src_file = "/exastro/common_libs/ansible_driver/shells/{}".format(self.LC_ANS_SSHAGENTEXPECT_FILE)
        dest_file = "{}/.{}".format(self.getTemporary_file_Dir(), self.LC_ANS_SSHAGENTEXPECT_FILE)
        if os.path.isfile(dest_file) is False:
            shutil.copyfile(src_file, dest_file)
        return True
