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

import getpass
import os
import shutil
import re
import inspect
import zipfile
import subprocess
import pathlib
import json

from chardet import detect
from flask import g, has_request_context

from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs
from common_libs.common.exception import AppException
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.WrappedStringReplaceAdmin import WrappedStringReplaceAdmin
from common_libs.ansible_driver.classes.ansible_common_libs import AnsibleCommonLibs
from common_libs.ansible_driver.classes.VarStructAnalJsonConvClass import VarStructAnalJsonConv
from common_libs.ansible_driver.classes.AnsibleMakeMessage import AnsibleMakeMessage
from common_libs.ansible_driver.classes.YamlParseClass import YamlParse
from common_libs.ansible_driver.functions.util import get_AnsibleDriverTmpPath, getFileupLoadColumnPath
from common_libs.ansible_driver.classes.WrappedStringReplaceAdmin import WrappedStringReplaceAdmin

#################################################################################
# rolesディレクトリ解析
#################################################################################
class CheckAnsibleRoleFiles():

    """
    【処理概要】
      ・roleディレクトリの内容をチェックする。
    """

    def __init__(self, in_objMTS, ws_db=None):

        """
        処理内容
          コンストラクタ
        パラメータ
          in_errorsave:    エラーメッセージ退避有無(ZIPファイルUpload時)
                           true: Yes   false: no
          in_errorlogfile: ログ出力先ファイル(role実行時のerror.logファイル)
                           不要の場合はnullを設定
        戻り値
          なし
        """

        self.lva_rolename = []
        self.lva_varname = {}
        self.lv_get_rolevar = None
        self.lv_lasterrmsg = []
        self.lv_objMTS = in_objMTS
        self.lva_globalvarname = {}
        self.lva_msg_role_pkg_name = None

        self.ws_db = ws_db

        self.php_array = lambda x: x.items() if isinstance(x, dict) else enumerate(x)
        self.php_keys = lambda x: x.keys() if isinstance(x, dict) else range(len(x))
        self.php_vals = lambda x: x.values() if isinstance(x, dict) else x

    def getvarname(self):

        """
        処理内容
          zipファイル内で定義されているロール変数名を取得
        パラメータ
          なし
        戻り値
          ロール変数名配列
          lva_varname[role名][変数名]=0
        """

        return self.lva_varname

    def getglobalvarname(self):

        """
        処理内容
          zipファイル内で定義されているグローバル変数名を取得
        パラメータ
          なし
        戻り値
          グローバル変数名配列
          lva_globalvarname[role名][グローバル変数名]=0
        """

        return self.lva_globalvarname

    def getrolename(self):

        """
        処理内容
          zipファイル内で定義されているロール名を取得
        パラメータ
          なし
        戻り値
          role名配列
          lva_rolename[role名]
        """

        return self.lva_rolename

    def getlasterror(self):

        """
        処理内容
          エラーメッセージ取得
        パラメータ
          なし
        戻り値
          エラーメッセージ
        """

        return self.lv_lasterrmsg

    def ZipextractTo(self, in_zip_path, in_dist_path, del_flag=True):

        """
        処理内容
          zipファイルを展開する
        パラメータ
          in_zip_path:    zipファイル
          in_dist_path:   zipファイル展開先ディレクトリ
          del_flag:       zipファイル展開先ディレクトリ削除有無
                          作業実行の場合に削除できない為
        戻り値
          true: 正常  false:異常
        """

        try:
            if del_flag is True:
               if os.path.isdir(in_dist_path):
                   shutil.rmtree(in_dist_path)

            with zipfile.ZipFile(in_zip_path) as zip:
                zip.extractall(in_dist_path)

        except Exception:
            msgstr = g.appmsg.get_api_message("MSG-10259")
            self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, msgstr)
            return False

        return True

    def chkRolesDirectory(
        self,
        in_dir, ina_system_vars, in_role_pkg_name,
        ina_def_vars_list, ina_err_vars_list, ina_def_varsval_list, ina_def_array_vars_list,
        in_get_copyvar, ina_copyvars_list,
        in_get_tpfvar,
        ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list, ina_comb_err_vars_list,
        in_get_rolevar=False
    ):

        """
        処理内容
          rolesディレクトリ配下のディレクトリとファイルが妥当かチェックする。
        パラメータ
          in_dir:             rolesディレクトリがあるディレクトリ
          in_getrolevar:      ロール変数取得有無
                                 false: ロール変数取得しない (default値)
                                 true:  ロール変数取得する
          ina_system_vars:    システム変数リスト(機器一覧)
          in_role_pkg_name:   ロールパッケージ名
          ina_def_vars_list:  各ロールのデフォルト変数ファイル内に定義されている
                               変数名のリスト
                                 一般変数
                                   ina_def_vars_list[ロール名][変数名]=0
                                 配列変数
                                   ina_def_vars_list[ロール名][配列数名]=array([子供変数名]=0,...)

          ina_err_vars_list:  ロールパッケージ内で使用している変数で構造が違う変数のリスト
                                   in_err_vars_list[変数名][ロールパッケージ名][ロール名]
          ina_def_varsval_list:
                               各ロールのデフォルト変数ファイル内に定義されている変数名の具体値リスト
                                 一般変数
                                   ina_def_vars_val_list[ロール名][変数名][0]=具体値
                                 複数具体値変数
                                   ina_def_vars_val_list[ロール名][変数名][1]=array(1=>具体値,2=>具体値....)
                                 配列変数
                                   ina_def_vars_val_list[ロール名][変数名][2][メンバー変数]=array(1=>具体値,2=>具体値....)

          in_get_copyvar:     PlaybookからCPF変数を取得の有無  true:取得  false:取得しない
          ina_copyvars_list:  Playbookで使用しているCPF変数のリスト
                                  ina_copyvars_list[ロール名][変数名]=1
          in_get_tpfvar:      PlaybookからTPF変数を取得の有無  true:取得  false:取得しない
          ina_tpfvars_list:   Playbookで使用しているTPF変数のリスト
                                  ina_tpfvars_list[ロール名][変数名]=1
          ina_ITA2User_var_list  読替表の変数リスト  ITA変数=>ユーザ変数
          ina_User2ITA_var_list  読替表の変数リスト  ユーザ変数=>ITA変数
          ina_comb_err_vars_list 読替変数と任意変数の組合せが一意でないリスト

        戻り値
          true: 正常  false:異常
        """

        # パッケージ名の退避
        if not in_role_pkg_name:
            self.lva_msg_role_pkg_name = "Current roll package"

        else:
            self.lva_msg_role_pkg_name = in_role_pkg_name

        # Playbookで使用しているCPF/TPF変数のリスト 初期化
        ina_copyvars_list = {}
        ina_tpfvars_list = {}

        # デフォルト変数定義一覧 初期化
        ina_def_vars_list = {}

        # role名一覧 初期化
        del self.lva_rolename[:]

        # role変数名一覧 初期化
        self.lva_varname.clear()

        # roleグローバル変数名一覧
        self.lva_globalvarname.clear()

        # role変数取得有無
        self.lv_get_rolevar = in_get_rolevar

        # roleディレクトリ抽出
        files = {}
        errormsg = ""
        ret, files, errormsg = self.RoleDirectoryAnalysis(in_dir, files, self.lv_objMTS, errormsg)
        if not ret:
            self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errormsg)
            return False, ina_def_vars_list, ina_err_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list, ina_comb_err_vars_list

        for fullpath, role_name in files.items():
            if os.path.isdir(fullpath):
                # rolesディレクトリ配下のroleディレクトリをチェック
                ret, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list = self.chkRoleDirectory(
                    in_dir,
                    fullpath,
                    ina_system_vars,
                    in_role_pkg_name,
                    role_name,
                    ina_def_vars_list,
                    ina_def_varsval_list,
                    ina_def_array_vars_list,
                    in_get_copyvar,
                    ina_copyvars_list,
                    in_get_tpfvar,
                    ina_tpfvars_list,
                    ina_ITA2User_var_list,
                    ina_User2ITA_var_list
                )
                if not ret:
                    return False, ina_def_vars_list, ina_err_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list, ina_comb_err_vars_list

        chkObj = DefaultVarsFileAnalysis(self.lv_objMTS)

        ina_comb_err_vars_list = {}
        ITA2User_var_list = {}
        User2ITA_var_list = {}
        ITA2User_var_list[in_role_pkg_name] = ina_ITA2User_var_list
        User2ITA_var_list[in_role_pkg_name] = ina_User2ITA_var_list

        # 読替変数と任意変数の組合せを確認する
        """
        ret, ina_comb_err_vars_list = chkObj.chkTranslationTableVarsCombination(
            ITA2User_var_list, User2ITA_var_list, ina_comb_err_vars_list
        )
        if not ret:
            # エラーメッセージは呼び元で編集
            return False, ina_def_vars_list, ina_err_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list, ina_comb_err_vars_list
        """

        # 読替表を元に変数名を更新
        """
        ina_def_vars_list = chkObj.ApplyTranslationTable(ina_def_vars_list, ina_User2ITA_var_list)
        ina_def_array_vars_list = chkObj.ApplyTranslationTable(ina_def_array_vars_list, ina_User2ITA_var_list)
        ina_def_varsval_list = chkObj.ApplyTranslationTable(ina_def_varsval_list, ina_User2ITA_var_list)
        """

        # ロールパッケージ内のデフォルト変数で定義されている変数の構造を確認
        ret, ina_err_vars_list = chkObj.chkVarsStruct(ina_def_vars_list, ina_def_array_vars_list, ina_err_vars_list)
        if not ret:
            chkObj = None
            return False, ina_def_vars_list, ina_err_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list, ina_comb_err_vars_list

        return True, ina_def_vars_list, ina_err_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list, ina_comb_err_vars_list

    def chkRoleDirectory(
        self,
        in_base_dir, in_dir, ina_system_vars, in_role_pkg_name, in_role_name,
        ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list,
        in_get_copyvar, ina_copyvars_list, in_get_tpfvar, ina_tpfvars_list,
        ina_ITA2User_var_list, ina_User2ITA_var_list
    ):

        """
        処理内容
          rolesディレクトリ配下のroleディレクトリとファイルが妥当かチェックする。
        パラメータ
          in_base_dir:        ベースディレクトリ
          in_dir:             rolesディレクトリ
          ina_system_vars     システム変数リスト(機器一覧)
          in_role_pkg_name:   ロールパッケージ名
          in_role_name:       ロール名
          ina_def_vars_list:  各ロールのデフォルト変数ファイル内に定義されている
                               変数名のリスト
                                 一般変数
                                   ina_def_vars_list[ロール名][変数名]=0
                                 配列変数
                                   ina_def_vars_list[ロール名][配列数名]=array([子供変数名]=0,...)
          ina_def_varsval_list:
                               各ロールのデフォルト変数ファイル内に定義されている変数名の具体値リスト
                                 一般変数
                                   ina_def_vars_val_list[ロール名][変数名][0]=具体値
                                 複数具体値変数
                                   ina_def_vars_val_list[ロール名][変数名][1]=array(1=>具体値,2=>具体値....)
                                 配列変数
                                   ina_def_vars_val_list[ロール名][変数名][2][メンバー変数]=array(1=>具体値,2=>具体値....)
          in_base_dir:        zipファイル解凍ディレクトリ
          in_get_copyvar:     PlaybookからCPF変数を取得の有無  true:取得  false:取得しない
          ina_copyvars_list:  Playbookで使用しているCPF変数のリスト
                                  ina_copyvars_list[ロール名][変数名]=1
          in_get_tpfvar:      PlaybookからTPF変数を取得の有無  true:取得  false:取得しない
          ina_tpfvars_list:   Playbookで使用しているTPF変数のリスト
                                  ina_tpfvars_list[ロール名][変数名]=1
          ina_ITA2User_var_list 読替表の変数リスト  ITA変数=>ユーザ変数
          ina_User2ITA_var_list 読替表の変数リスト  ユーザ変数=>ITA変数

        戻り値
          true: 正常  false:異常
        """

        # roleディレクトリを取得
        fullpath = in_dir

        # デフォルト変数定義一覧 初期化
        ina_def_vars_list[in_role_name] = {}

        # role名退避
        self.lva_rolename.append(in_role_name)

        ret, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list = self.chkRoleSubDirectory(
            in_base_dir, fullpath, ina_system_vars, in_role_pkg_name, in_role_name,
            ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list,
            in_get_copyvar, ina_copyvars_list, in_get_tpfvar, ina_tpfvars_list,
            ina_ITA2User_var_list, ina_User2ITA_var_list
        )
        if not ret:
            return False, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list

        return True, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list

    def chkRoleSubDirectory(
        self,
        in_base_dir, in_dir, ina_system_vars, in_role_pkg_name, in_rolename,
        ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list,
        in_get_copyvar, ina_copyvars_list, in_get_tpfvar, ina_tpfvars_list,
        ina_ITA2User_var_list, ina_User2ITA_var_list
    ):

        """
        処理内容
          roleディレクトリ配下のディレクトリとファイルが妥当かチェックする。
        パラメータ
          in_base_dir:        ベースディレクトリ
          in_dir:             roleディレクトリ
          ina_system_vars:    システム変数リスト(機器一覧)
          in_role_pkg_name:   ロールパッケージ名
          in_role_name:       ロール名
          ina_def_vars_list:  各ロールのデフォルト変数ファイル内に定義されている
                               変数名のリスト
                                 一般変数
                                   ina_def_vars_list[ロール名][変数名]=0
                                 配列変数
                                   ina_def_vars_list[ロール名][配列数名]=array([子供変数名]=0,...)
          ina_def_varsval_list:
                               各ロールのデフォルト変数ファイル内に定義されている変数名の具体値リスト
                                 一般変数
                                   ina_def_vars_val_list[ロール名][変数名][0]=具体値
                                 複数具体値変数
                                   ina_def_vars_val_list[ロール名][変数名][1]=array(1=>具体値,2=>具体値....)
                                 配列変数
                                   ina_def_vars_val_list[ロール名][変数名][2][メンバー変数]=array(1=>具体値,2=>具体値....)
          in_base_dir:        zipファイル解凍ディレクトリ
          in_get_copyvar:     PlaybookからCPF変数を取得の有無  true:取得  false:取得しない
          ina_copyvars_list:  Playbookで使用しているCPF変数のリスト
                                 ina_copyvars_list[ロール名][変数名]=1
          in_get_tpfvar:      PlaybookからTPF変数を取得の有無  true:取得  false:取得しない
          ina_tpfars_list:    Playbookで使用しているTPF変数のリスト
                                 ina_copyvars_list[ロール名][変数名]=1
          ina_ITA2User_var_list   読替表の変数リスト  ITA変数=>ユーザ変数
          ina_User2ITA_var_list   読替表の変数リスト  ユーザ変数=>ITA変数

        戻り値
          true: 正常  false:異常
        """

        ###################################
        # 該当ロールの読替表の読込み
        ###################################
        ina_ITA2User_var_list[in_rolename] = {}
        ina_User2ITA_var_list[in_rolename] = {}
        ITA2User_var_list = {}
        User2ITA_var_list = {}
        errmsg = ""

        # ロール名の / を % に置き換える
        edit_role_name = re.sub('/', '%', in_rolename)

        # 該当ロールの読替表のファイル名生成
        translation_table_file = '%s/ita_translation-table_%s.txt' % (in_base_dir, edit_role_name)

        # 該当ロールの読替表のファイルの有無判定
        """
        if os.path.isfile(translation_table_file):
            # 文字コードとBOM付をチェック
            ret, errmsg = self.FileCharacterCodeCheck(translation_table_file, errmsg)
            if not ret:
                self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
                return False, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list

            # 該当ロールの読替表を読込
            ret, ITA2User_var_list, User2ITA_var_list, errmsg = self.readTranslationFile(translation_table_file, ITA2User_var_list, User2ITA_var_list, errmsg)
            if not ret:
                self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
                return False, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list
        """

        ina_ITA2User_var_list[in_rolename] = ITA2User_var_list
        ina_User2ITA_var_list[in_rolename] = User2ITA_var_list

        ###################################
        # 該当ロールのITA readmeの読込み
        ###################################
        all_parent_vars_list = {}
        user_vars_file = '%s/ita_readme_%s.yml' % (in_base_dir, edit_role_name)

        user_vars_list = []
        user_varsval_list = []
        user_array_vars_list = []
        user_vars_file_use = False

        # ユーザー定義変数ファイルの有無判定
        if os.path.isfile(user_vars_file):

            user_vars_file_use = True

            # 文字コードとBOM付をチェック
            ret, errmsg = self.FileCharacterCodeCheck(user_vars_file, errmsg)
            if not ret:
                self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
                return False, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list

            tgt_role_pkg_name = self.lva_msg_role_pkg_name
            tgt_file_name = user_vars_file.replace('%s/' % (in_base_dir), '').strip()
            tgt_role_name = in_rolename

            # 対象ファイルから変数取得
            chkObj = DefaultVarsFileAnalysis(self.lv_objMTS)
            chkObj.setVariableDefineLocation(AnscConst.DF_README_VARS)
            obj = YamlParse()
            yaml_parse_array = obj.Parse(user_vars_file)
            errmsg = obj.GetLastError()
            obj = None
            if yaml_parse_array is False:
                # ITA readmeのYAML解析で想定外のエラーが発生しました。(ロールパッケージ名:{} role:{} file:{})
                errmsg = "%s\n%s" % (
                    errmsg,
                    g.appmsg.get_api_message("MSG-10643", [self.lva_msg_role_pkg_name, in_rolename, tgt_file_name])
                )
                self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
                return False, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list

            parent_vars_list = {}
            errmsg = ""
            f_line = ""
            f_name = ""
            ret, parent_vars_list, errmsg, f_name, f_line = chkObj.FirstAnalysis(
                yaml_parse_array, tgt_role_pkg_name, tgt_role_name, tgt_file_name,
                ina_ITA2User_var_list[in_rolename], ina_User2ITA_var_list[in_rolename],
                parent_vars_list, errmsg, f_name, f_line
            )
            if not ret:
                errmsg = '%s(%s)' % (errmsg, f_line)
                self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
                return False, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list

            user_vars_list = {}
            user_varsval_list = {}
            user_array_vars_list = {}
            errmsg = ""
            f_line = ""
            f_name = ""
            ret, user_vars_list, user_varsval_list, user_array_vars_list, errmsg, f_name, f_line = chkObj.LastAnalysis(
                parent_vars_list, user_vars_list, user_varsval_list, user_array_vars_list,
                tgt_role_name, tgt_file_name,
                errmsg, f_name, f_line,
                tgt_role_pkg_name
            )
            if not ret:
                # defaults=>main.ymlからの変数取得失敗
                errmsg = '%s(%s)' % (errmsg, f_line)
                self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
                return False, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list
            
            # ita readmeに定義されている変数(親)を取り出す
            for parent_var_name, parent_var_info in parent_vars_list.items():
                all_parent_vars_list[parent_var_name] = 0

        ########################################################
        # role内のディレクトリをチェック
        ########################################################
        files = os.listdir(in_dir)
        files = [f for f in files if f not in ['.', '..']]
        tasks_dir = False
        defaults_his = False
        tmp_in_role_pkg_name = ""

        for file in files:
            fullpath = '%s/%s' % (in_dir.rstrip('/'), file)
            if not os.path.isdir(fullpath):
                continue

            if file == "tasks":
                tasks_dir = True
                # p1:ロール変数取得有(true)/無(false)
                # p2:main.yml必須有(true)/無(false)
                # p3:サブディレクトリ(許可(true)/許可しない(false))
                # p4:main.ymlファイル以外のファイル(許可(true)/許可しない(false))
                # p5:TPF/CPF変数取得有(true)/無(false)
                # p6:ファイル文字コードチェック有(true)/無(false)
                ret, ina_copyvars_list, ina_tpfvars_list = self.chkRoleFiles(
                    fullpath, in_rolename, file,
                    # p1    p2    p3    p4    p5    p6
                    True, True, True, True, True, True,
                    in_get_copyvar, ina_copyvars_list, in_get_tpfvar, ina_tpfvars_list, ina_system_vars
                )

            elif file == "handlers":
                ret, ina_copyvars_list, ina_tpfvars_list = self.chkRoleFiles(
                    fullpath, in_rolename, file,
                    # p1    p2     p3    p4    p5    p6
                    True, False, True, True, True, True,
                    in_get_copyvar, ina_copyvars_list, in_get_tpfvar, ina_tpfvars_list, ina_system_vars
                )

            elif file == "templates":
                ret, ina_copyvars_list, ina_tpfvars_list = self.chkRoleFiles(
                    fullpath, in_rolename, file,
                    # p1    p2     p3    p4    p5    p6
                    True, False, True, True, True, False,
                    in_get_copyvar, ina_copyvars_list, in_get_tpfvar, ina_tpfvars_list, ina_system_vars
                )

            elif file == "meta":
                ret, ina_copyvars_list, ina_tpfvars_list = self.chkRoleFiles(
                    fullpath, in_rolename, file,
                    # p1    p2     p3    p4    p5    p6
                    True, False, True, True, True, True,
                    in_get_copyvar, ina_copyvars_list, in_get_tpfvar, ina_tpfvars_list, ina_system_vars
                )

            elif file == "files":
                ret, ina_copyvars_list, ina_tpfvars_list = self.chkRoleFiles(
                    fullpath, in_rolename, file,
                    # p1     p2     p3    p4    p5     p6
                    False, False, True, True, False, False,
                    in_get_copyvar, ina_copyvars_list, in_get_tpfvar, ina_tpfvars_list, ina_system_vars
                )

            elif file == "vars":
                ret, ina_copyvars_list, ina_tpfvars_list = self.chkRoleFiles(
                    fullpath, in_rolename, file,
                    # p1     p2     p3    p4    p5     p6
                    False, False, True, True, False, True,
                    in_get_copyvar, ina_copyvars_list, in_get_tpfvar, ina_tpfvars_list, ina_system_vars
                )

            elif file == "defaults":
                defaults_his = True
                ret, ina_copyvars_list, ina_tpfvars_list = self.chkRoleFiles(
                    fullpath, in_rolename, file,
                    # p1     p2     p3    p4    p5     p6
                    False, False, True, True, False, True,
                    in_get_copyvar, ina_copyvars_list, in_get_tpfvar, ina_tpfvars_list, ina_system_vars
                )

                if ret is True:
                    parent_vars_list = {}
                    vars_list = {}
                    array_vars_list = {}
                    varsval_list = {}

                    # defaultsディレクトリ内の変数定義を読み取る
                    tmp_in_role_pkg_name = self.lva_msg_role_pkg_name
                    ret, parent_vars_list, vars_list, array_vars_list, varsval_list = self.AnalysisDefaultVarsFiles(
                        AnscConst.LC_RUN_MODE_STD,
                        in_base_dir,
                        fullpath,
                        tmp_in_role_pkg_name,
                        in_rolename,
                        parent_vars_list,
                        vars_list,
                        array_vars_list,
                        varsval_list,
                        ITA2User_var_list,
                        User2ITA_var_list
                    )
                    if not ret:
                        return False, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list

                    # ita readmeに定義されている変数(親)とdefault定義に定義されている変数(親)をマージ
                    for parent_var_name, parent_var_info in parent_vars_list.items():
                        all_parent_vars_list[parent_var_name] = 0

                    # 読替表の任意変数がデフォルト変数定義ファイルやita Readmeファイルに登録されているか判定する
                    """
                    ret, errmsg = self.chkTranslationVars(
                        all_parent_vars_list, User2ITA_var_list,
                        os.path.basename(translation_table_file), errmsg
                    )
                    if not ret:
                        self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
                        return False, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list
                    """

                    # ユーザー定義変数ファイルから変数取得
                    chkObj = DefaultVarsFileAnalysis(self.lv_objMTS)

                    # default変数定義ファイルの変数情報とユーザー定義変数ファイル
                    # の変数情報をマージする
                    vars_list, varsval_list, array_vars_list = chkObj.margeDefaultVarsList(
                        vars_list, varsval_list,
                        user_vars_list, user_varsval_list,
                        array_vars_list, user_array_vars_list
                    )
                    chkObj = None

                    # デフォルト変数定義一覧 に変数の情報を登録
                    ina_def_vars_list[in_rolename] = vars_list
                    ina_def_array_vars_list[in_rolename] = array_vars_list

                    # デフォルト変数定義の変数の具体値情報を登録
                    ina_def_varsval_list[in_rolename] = varsval_list

            else:
                # ベストプラクティスのディレクトリ以外はチェックしない
                ret = True

            if not ret:
                return ret, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list

        # ユーザー定義変数ファイルが存在しデフォルト変数定義ファイルが存在しない場合
        if defaults_his is False and user_vars_file_use is True:
            # 読替表の任意変数がita Readmeファイルに登録されているか判定する
            """
            ret, errmsg = self.chkTranslationVars(
                all_parent_vars_list, User2ITA_var_list, os.path.basename(translation_table_file), errmsg
            )
            if not ret:
                self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
                return False, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list
            """

            vars_list = {}
            varsval_list = {}
            array_vars_list = {}

            # default変数定義ファイルは存在しないがユーザー定義変数ファイル
            # の変数情報をマージする処理を呼ぶ(具体値を調整)
            vars_list, varsval_list, array_vars_list = chkObj.margeDefaultVarsList(
                vars_list, varsval_list,
                user_vars_list, user_varsval_list,
                array_vars_list, user_array_vars_list
            )

            # デフォルト変数定義一覧 に変数の情報を登録
            ina_def_vars_list[in_rolename] = vars_list
            ina_def_array_vars_list[in_rolename] = array_vars_list

            # デフォルト変数定義の変数の具体値情報を登録
            ina_def_varsval_list[in_rolename] = varsval_list

        if not tasks_dir:
            # MSG-10260 = "｛｝にtasksディレクトリがありません。"
            msgstr = g.appmsg.get_api_message("MSG-10260", ['./roles/%s' % (in_rolename)])
            self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, msgstr)
            return False, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list

        return True, ina_def_vars_list, ina_def_varsval_list, ina_def_array_vars_list, ina_copyvars_list, ina_tpfvars_list, ina_ITA2User_var_list, ina_User2ITA_var_list

    def AnalysisDefaultVarsFiles(
        self,
        in_mode,  # LC_RUN_MODE_STD
        in_base_dir, in_dir,
        in_role_pkg_name, in_rolename,
        ina_parent_vars_list, ina_vars_list, ina_array_vars_list, ina_varsval_list,
        ina_ITA2User_var_list, ina_User2ITA_var_list
    ):

        """
        処理内容
          defaultディレクトリの変数定義ファイルを読み取る
        パラメータ
          in_mode:               解析ファイル種別  LC_RUN_MODE_STD
          in_base_dir:           ベースディレクトリ
          in_dir:                roleディレクトリ
          in_role_pkg_name:      ロールパッケージ名
          in_rolename:           ロール名
          ina_parent_vars_list:  デフォルト変数定義ファイルやita Readmeファイルに登録されている変数リスト
          ina_vars_list:         各ロールのデフォルト変数ファイル内に定義されている
                                  変数名のリスト
                                    一般変数
                                      ina_vars_list[ロール名][変数名]=0
                                    配列変数
                                      ina_vars_list[ロール名][配列数名]=array([子供変数名]=0,...)
          ina_array_vars_list:   各ロールのデフォルト変数ファイル内に定義されている
                                  多段変数リスト
          ina_varsval_list:      各ロールのデフォルト変数ファイル内に定義されている変数名の具体値リスト
                                    一般変数
                                      ina_varsval_list[ロール名][変数名][0]=具体値
                                    複数具体値変数
                                      ina_varsval_list[ロール名][変数名][1]=array(1=>具体値,2=>具体値....)
                                    配列変数
                                      ina_varsval_list[ロール名][変数名][2][メンバー変数]=array(1=>具体値,2=>具体値....)
          ina_ITA2User_var_list  読替表の変数リスト  ITA変数=>ユーザ変数
          ina_User2ITA_var_list  読替表の変数リスト  ユーザ変数=>ITA変数

        戻り値
          true: 正常  false:異常
        """

        files = []

        # ディレクトリ配下のファイル一覧取得
        filelist = self.getFileList(in_dir)
        for file in filelist:
            files.append(file.replace('%s/' % (in_dir), '').strip())

        for file in files:
            fullpath = '%s/%s' % (in_dir.rstrip('/'), file)
            preg_base_dir = in_base_dir.replace('/', '\\/')
            display_file_name = fullpath.replace('/^%s/' % (preg_base_dir), '')
            if os.path.isdir(fullpath):
                continue

            chkObj = YAMLFileAnalysis(self.lv_objMTS)

            parent_vars_list = {}
            vars_list = {}
            array_vars_list = {}
            varsval_list = {}
            ret, parent_vars_list, vars_list, array_vars_list, varsval_list = chkObj.VarsFileAnalysis(
                in_mode,
                fullpath,
                parent_vars_list,
                vars_list,
                array_vars_list,
                varsval_list,
                in_role_pkg_name,
                in_rolename,
                display_file_name,
                ina_ITA2User_var_list,
                ina_User2ITA_var_list
            )
            if not ret:
                # 解析結果にエラーがある場合
                errmsg = chkObj.GetLastError()
                chkObj = None

                self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg[0])
                return False, ina_parent_vars_list, ina_vars_list, ina_array_vars_list, ina_varsval_list

            chkObj = None

            # 定義されている変数(親)を取り出す
            for parent_var_name, parent_var_info in self.php_array(parent_vars_list):
                # 同じ変数名が複数のdefault定義ファイルに記述されている場合はエラー
                if parent_var_name in ina_parent_vars_list and ina_parent_vars_list[parent_var_name] is not None:
                    # MSG-10614 = ""変数が複数のdefault定義ファイルに記述されています。(ロールパッケージ名:{} ロール名:{} 変数名:{})"
                    msgstr = g.appmsg.get_api_message(
                        "MSG-10614", [in_role_pkg_name, in_rolename, parent_var_name]
                    )
                    self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, msgstr)
                    return False, ina_parent_vars_list, ina_vars_list, ina_array_vars_list, ina_varsval_list

                parent_vars_list[parent_var_name] = 0
                ina_parent_vars_list[parent_var_name] = parent_var_info

            # 変数の情報をマージする
            for var_name, var_info in self.php_array(vars_list):
                ina_vars_list[var_name] = var_info

            for var_name, var_info in self.php_array(array_vars_list):
                ina_array_vars_list[var_name] = var_info

            for var_name, var_info in self.php_array(varsval_list):
                ina_varsval_list[var_name] = var_info

        return True, ina_parent_vars_list, ina_vars_list, ina_array_vars_list, ina_varsval_list

    def chkRoleFiles(
        self,
        in_dir, in_rolename, in_dirname, in_get_rolevar, in_main_yml, in_etc_yml, in_sub_dir, in_get_var_tgt_dir,
        in_CharacterCodeCheck, in_get_copyvar, ina_copyvars_list, in_get_tpfvar, ina_tpfvars_list, ina_system_vars
    ):

        """
        処理内容
          roleの各ディレクトリとファイルが妥当かチェックする。
        パラメータ
          in_base_dir:        ベースディレクトリ
          in_dir:         roleディレクトリ
          in_rolename     ロール名
          in_dirname      ディレクトリ名
          in_get_rolevar  ロール変数取得有(true)/無(false)
          in_main_yml     main.yml必須有(true)/無(false)
          in_etc_yml      main.ymlファイル以外のファイル(許可(true)/許可しない(false))
          in_sub_dir      サブディレクトリ(許可(true)/許可しない(false))
          in_get_var_tgt_dir: CPF/TPF変数を取得対象ディレクトリ判定 true:取得  false:取得しない
          in_CharacterCodeCheck: ファイル文字コードチェック有(true)/無(false)
          in_get_copyvar:    PlaybookからCPF変数を取得の有無  true:取得  false:取得しない
          ina_copyvars_list: Playbookで使用しているCPF変数のリスト
                              ina_copyvars_list[ロール名][変数名]=1
          in_get_tpfvar:     PlaybookからTPF変数を取得の有無  true:取得  false:取得しない
          ina_tpfvars_list:  Playbookで使用しているTPF変数のリスト
                              ina_tpfvars_list[ロール名][変数名]=1
          ina_system_vars システム変数リスト(機器一覧)
        戻り値
          true: 正常  false:異常
        """

        files = []

        # ディレクトリ配下のファイル一覧取得
        filelist = self.getFileList(in_dir)
        for file in filelist:
            files.append(file.replace('%s/' % (in_dir), '').strip())

        main_yml = False
        for file in files:
            fullpath = '%s/%s' % (in_dir.rstrip('/'), file)
            if os.path.isdir(fullpath):
                # サブディレクトリを許可しているか判定
                if not in_sub_dir:
                    # MSG-10277 = "サブディレクトリ(｛｝)が存在します。"
                    msgstr = g.appmsg.get_api_message(
                        "MSG-10277",
                        ['./roles/%s/%s/%s' % (in_rolename, in_dirname, file)]
                    )
                    self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, msgstr)
                    return False, ina_copyvars_list, ina_tpfvars_list

            if os.path.isfile(fullpath):
                if in_CharacterCodeCheck:
                    # 文字コードとBOM付をチェック
                    errmsg = ""
                    ret, errmsg = self.FileCharacterCodeCheck(fullpath, errmsg)
                    if not ret:
                        self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
                        return False, ina_copyvars_list, ina_tpfvars_list

                if file == "main.yml":
                    main_yml = True

                # 変数初期化
                file_vars_list = []
                file_global_vars_list = []

                # ファイルの内容を読込む
                dataString = pathlib.Path(fullpath).read_text()

                # ホスト変数の抜出が指定されている場合
                if in_get_rolevar:
                    # テンプレートからグローバル変数を抜出す
                    local_vars = []
                    varsLineArray = []
                    file_global_vars_list = []
                    FillterVars = True  # Fillterを含む変数の抜き出しあり
                    WrappedStringReplaceAdmin().SimpleFillterVerSearch(
                        AnscConst.DF_HOST_GBL_HED,
                        dataString, varsLineArray, file_global_vars_list, local_vars, FillterVars
                    )

                    # ファイル内で定義されていた変数を退避
                    for var in file_vars_list:
                        if in_rolename not in self.lva_varname:
                            self.lva_varname[in_rolename] = {}

                        if var not in self.lva_varname[in_rolename]:
                            self.lva_varname[in_rolename][var] = None

                        self.lva_varname[in_rolename][var] = 0

                    # ファイル内で定義されていたグローバル変数を退避
                    for var in file_global_vars_list:
                        if in_rolename not in self.lva_globalvarname:
                            self.lva_globalvarname[in_rolename] = {}

                        if var not in self.lva_globalvarname[in_rolename]:
                            self.lva_globalvarname[in_rolename][var] = None

                        self.lva_globalvarname[in_rolename][var] = 0

                # CPF/TPF変数を取得するか判定
                if in_get_var_tgt_dir:
                    tgt_file = '%s/%s/%s' % (in_rolename, in_dirname, file)
                    if in_get_copyvar:
                        local_vars = []
                        la_cpf_vars = []
                        varsArray = []
                        FillterVars = True  # Fillterを含む変数の抜き出しあり
                        WrappedStringReplaceAdmin().SimpleFillterVerSearch(
                            AnscConst.DF_HOST_CPF_HED,
                            dataString, la_cpf_vars, varsArray, local_vars, FillterVars
                        )

                        # ファイル内で定義されていたCPF変数を退避
                        for no, cpf_var_list in enumerate(la_cpf_vars):
                            for line_no, cpf_var_name in cpf_var_list.items():
                                if in_rolename not in ina_copyvars_list:
                                    ina_copyvars_list[in_rolename] = {}

                                if tgt_file not in ina_copyvars_list[in_rolename]:
                                    ina_copyvars_list[in_rolename][tgt_file] = {}

                                if line_no not in ina_copyvars_list[in_rolename][tgt_file]:
                                    ina_copyvars_list[in_rolename][tgt_file][line_no] = {}

                                if cpf_var_name not in ina_copyvars_list[in_rolename][tgt_file][line_no]:
                                    ina_copyvars_list[in_rolename][tgt_file][line_no][cpf_var_name] = None

                                ina_copyvars_list[in_rolename][tgt_file][line_no][cpf_var_name] = 0

                    if in_get_tpfvar:
                        local_vars = []
                        la_tpf_vars = []
                        varsArray = []
                        FillterVars = True  # Fillterを含む変数の抜き出しあり
                        WrappedStringReplaceAdmin().SimpleFillterVerSearch(
                            AnscConst.DF_HOST_TPF_HED,
                            dataString, la_tpf_vars, varsArray, local_vars, FillterVars
                        )

                        # ファイル内で定義されていたCPF変数を退避
                        for no, tpf_var_list in enumerate(la_tpf_vars):
                            for line_no, tpf_var_name in tpf_var_list.items():
                                if in_rolename not in ina_tpfvars_list:
                                    ina_tpfvars_list[in_rolename] = {}

                                if tgt_file not in ina_tpfvars_list[in_rolename]:
                                    ina_tpfvars_list[in_rolename][tgt_file] = {}

                                if line_no not in ina_tpfvars_list[in_rolename][tgt_file]:
                                    ina_tpfvars_list[in_rolename][tgt_file][line_no] = {}

                                if tpf_var_name not in ina_tpfvars_list[in_rolename][tgt_file][line_no]:
                                    ina_tpfvars_list[in_rolename][tgt_file][line_no][tpf_var_name] = None

                                ina_tpfvars_list[in_rolename][tgt_file][line_no][tpf_var_name] = 0

        # main.ymlが必要なディレクトリにmain.ymlがない場合
        if in_main_yml is True and main_yml is False:
            # MSG-10257 = "main.ymlファイルがありません。(ディレクトリ:{})"
            msgstr = g.appmsg.get_api_message(
                "MSG-10257",
                ['./roles/%s/%s/' % (in_rolename, in_dirname)]
            )
            self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, msgstr)
            return False, ina_copyvars_list, ina_tpfvars_list

        return True, ina_copyvars_list, ina_tpfvars_list

    def readTranslationFile(self, in_filepath, ina_ITA2User_var_list, ina_User2ITA_var_list, in_errmsg):

        """
        処理内容
          読替表より変数の情報を取得する。

        パラメータ
          in_filepath:            読替表ファイルパス
          ina_ITA2User_var_list:  読替表の変数リスト  ITA変数=>ユーザ変数
          ina_User2ITA_var_list:  読替表の変数リスト  ユーザ変数=>ITA変数
          in_errmsg:              エラーメッセージリスト

        戻り値
          true:   正常
          false:  異常
        """

        in_errmsg = ""
        ret_code = True
        dataString = pathlib.Path(in_filepath).read_text()
        line = 0

        # 入力データを行単位に分解
        arry_list = dataString.split('\n')
        for strSourceString in arry_list:
            line = line + 1

            # コメント行は読み飛ばす
            if strSourceString.startswith('#'):
                continue

            # 空行を読み飛ばす
            if len(strSourceString.strip()) == 0:
                continue

            # 読替変数の構文を確認
            # LCA_[0-9,a-Z_*]($s*):($s+)playbook内で使用している変数名
            # 読替変数名の構文判定
            ret = re.findall(r'^\s*LCA_[a-zA-Z0-9_]*\s*:\s+', strSourceString)
            if len(ret) == 1:
                # :を取除き、読替変数名取得
                ita_var_name = ret[0].replace(':', '').strip()

                # 任意変数を取得
                user_var_name = re.sub(r'^\s*LCA_[a-zA-Z0-9_]*\s*:\s+', '', strSourceString).strip()
                if len(user_var_name) > 0:
                    # 任意変数がVAR_でないことを判定
                    ret = re.findall(r'^VAR_', user_var_name)
                    if len(ret) == 1:
                        if len(in_errmsg) > 0:
                            in_errmsg = '%s\n' % (in_errmsg)

                        in_errmsg += g.appmsg.get_api_message(
                            "MSG-10514", [os.path.basename(in_filepath), line]
                        )
                        ret_code = False
                        continue

                    # 任意変数が文字列になっているか
                    ret = re.findall(r'^\S+$', user_var_name)
                    if len(ret) != 1:
                        if len(in_errmsg) > 0:
                            in_errmsg = '%s\n' % (in_errmsg)

                        in_errmsg += g.appmsg.get_api_message(
                            "MSG-10515", [os.path.basename(in_filepath), line]
                        )
                        ret_code = False
                        continue

                else:
                    if len(in_errmsg) > 0:
                        in_errmsg = '%s\n' % (in_errmsg)

                    in_errmsg += g.appmsg.get_api_message("MSG-10515", [os.path.basename(in_filepath), line])
                    ret_code = False
                    continue

            else:
                if len(in_errmsg) > 0:
                    in_errmsg = '%s\n' % (in_errmsg)

                in_errmsg += g.appmsg.get_api_message("MSG-10516", [os.path.basename(in_filepath), line])
                ret_code = False
                continue

            # 任意変数が重複登録の二重登録判定
            if  user_var_name in ina_User2ITA_var_list and ina_User2ITA_var_list[user_var_name] is not None \
            and (type(ina_User2ITA_var_list[user_var_name]) not in (list, dict) or len(ina_User2ITA_var_list[user_var_name]) > 0):
                if len(in_errmsg) > 0:
                    in_errmsg = '%s\n' % (in_errmsg)

                in_errmsg += g.appmsg.get_api_message("MSG-10517", [os.path.basename(in_filepath), line])
                ret_code = False
                continue

            else:
                ina_User2ITA_var_list[user_var_name] = ita_var_name

            # 読替変数が重複登録の二重登録判定
            if  ita_var_name in ina_ITA2User_var_list and ina_ITA2User_var_list[ita_var_name] is not None \
            and (type(ina_ITA2User_var_list[ita_var_name]) not in (list, dict) or len(ina_ITA2User_var_list[ita_var_name]) > 0):
                if len(in_errmsg) > 0:
                    in_errmsg = '%s\n' % (in_errmsg)

                in_errmsg += g.appmsg.get_api_message("MSG-10518", [os.path.basename(in_filepath), ita_var_name])
                ret_code = False
                continue

            else:
                ina_ITA2User_var_list[ita_var_name] = user_var_name

        return ret_code, ina_ITA2User_var_list, ina_User2ITA_var_list, in_errmsg

    def chkTranslationVars(self, ina_all_parent_vars_list, ina_User2ITA_var_list, in_translation_table_file, in_errmsg):

        """
        処理内容
          読替表の任意変数がデフォルト変数定義ファイルやita Readmeファイルに登録されているか判定する。

        パラメータ
          ina_all_parent_vars_list:  デフォルト変数定義ファイルやita Readmeファイルに登録されている変数リスト
          ina_User2ITA_var_list:     読替表の変数リスト　ユーザ変数=>ITA変数
          in_translation_table_file: 読替表ファイル
          in_errmsg:                 エラーメッセージリスト

        戻り値
          true:   正常
          false:  異常
        """

        ret_code = True
        in_errmsg = ""
        for user_var_name, rep_var_name in self.php_array(ina_User2ITA_var_list):
            if user_var_name not in ina_all_parent_vars_list \
            or ina_all_parent_vars_list[user_var_name] is None \
            or (type(ina_all_parent_vars_list[user_var_name]) in (list, dict) and len(ina_all_parent_vars_list[user_var_name]) <= 0):
                if len(in_errmsg) > 0:
                    in_errmsg = '%s\n' % (in_errmsg)

                in_errmsg += g.appmsg.get_api_message(
                    "MSG-10519", [os.path.basename(in_translation_table_file), user_var_name]
                )
                ret_code = False
                continue

        return ret_code, in_errmsg

    def SetLastError(self, p1, p2, p3):

        """
        処理内容
          クラス内のエラー情報退避

        パラメータ
          p1:  __FILE__
          p2:  __LINE__
          p3:  エラーメッセージリスト

        戻り値
          なし
        """

        if len(self.lv_lasterrmsg) < 1:
            self.lv_lasterrmsg.append("")

        if len(self.lv_lasterrmsg) < 2:
            self.lv_lasterrmsg.append("")

        self.lv_lasterrmsg[0] = p3
        self.lv_lasterrmsg[1] = "FILE:%s LINE:%s %s" % (p1, p2, p3)

    def FileCharacterCodeCheck(self, Filename, strErrMsg):

        """
        処理内容
          指定ファイルの文字コードがUTF-8のBOMなしか判定

        パラメータ
          Filename:  ファイル名
          strErrMsg: エラー時のエラーメッセージ返却

        戻り値
          true:   正常
          false:  異常
        """

        strErrMsg = ""

        # エラーメッセージのファイル名を生成
        ary = Filename.split('/roles/')
        if len(ary) <= 1:
            # ITAreadmeや読替表の場合
            dispFilename = os.path.basename(Filename)

        else:
            # role内のファイルの場合
            del ary[0:2]
            dispFilename = '/roles/'.join(ary)

        boolRet = True
        yaml = pathlib.Path(Filename).read_bytes()
        # 変数定義ファイルが空の場合
        if len(yaml) == 0:
            return boolRet, strErrMsg
            
        encode = detect(yaml)
        encode = encode['encoding'].upper()
        if encode in ["ASCII", "UTF-8"]:
            if yaml[0:3] == b'\xef\xbb\xbf':
                strErrMsg = g.appmsg.get_api_message('MSG-10642', [dispFilename])
                boolRet = False

        else:
            strErrMsg = g.appmsg.get_api_message('MSG-10641', [dispFilename])
            boolRet = False

        return boolRet, strErrMsg

    def debuglog(self, line, msg):

        pass

    def getDBGlobalVarsMaster(self, ina_global_vars_list, in_msgstr):

        """
        処理内容
          グローバル変数の情報をデータベースより取得する。

        パラメータ
          in_global_vars_list:     グローバル変数のリスト

        戻り値
          true:   正常
          false:  異常
        """

        ws_db = self.ws_db
        if not ws_db:
            ws_db = DBConnectWs()

        sql = (
            "SELECT "
            "  VARS_NAME, "
            "  VARS_ENTRY "
            "FROM "
            "  T_ANSC_GLOBAL_VAR "
            "WHERE "
            "  DISUSE_FLAG='0';"
        )

        data_list = ws_db.sql_execute(sql)

        ina_global_vars_list = {}
        for data in data_list:
            ina_global_vars_list[data['VARS_NAME']] = data['VARS_ENTRY']

        # DBアクセス事後処理
        if not self.ws_db and ws_db:
            ws_db.db_disconnect()
            ws_db = None

        return True, ina_global_vars_list, in_msgstr

    def getFileList(self, dir):

        """
        処理内容
          指定ディレクトリ配下のファイル一覧取得

        パラメータ
          $dir:       ディレクトリ

        戻り値
          ファイル一覧
        """

        files = os.listdir(dir)
        files = [f for f in files if f not in ['.', '..']]

        list = []
        for file in files:
            fullpath = '%s/%s' % (dir.rstrip('/'), file)
            list.append(fullpath)
            if os.path.isdir(fullpath):
                list.extend(self.getFileList(fullpath))

        return list

    def RoleDirectoryAnalysis(self, BaseDir, RoleDirList, objMTS, errormsg):

        """
        処理内容
          指定ディレクトリ配下からroleディレクトリを探す

        パラメータ
          BaseDir:     rolesディレクトリを含む階層のパス
          RoleDirList: roleディレクトリ一覧
                        tasksが定義されているディレクトリ
                        RoleDirList[roleディレクトリパス] = role名
          errormsg:    エラーメッセージ
        戻り値
          true:  roleディレクトリ一覧
          false: rolesディレクトリがない
        """

        RoleDirList = {}

        result_code = False
        role_dir_list = []
        roles_dir = '%s/roles/' % (BaseDir)
        preg_roles_dir = roles_dir.replace("/", "\\/")
        errormsg = ""

        # ディレクトリか判定
        if not os.path.isdir(roles_dir):
            # rolesディレクトリがない
            errormsg = g.appmsg.get_api_message("MSG-10256")
            return result_code, RoleDirList, errormsg

        # ディレクトリリスト取得
        dir_list = self.getFileList(BaseDir)

        # tasksフォルダリスト
        # roles以降は除外
        for dir in dir_list:
            # ディレクトリ確認
            if os.path.isfile(dir):
                continue

            # rolesディレクトリ確認
            if dir + "/" == roles_dir:
                result_code = True

            # rolesディレクトリ以外はスキップ
            if dir.startswith(roles_dir) is False:
                continue

            if os.path.basename(dir) == "tasks":
                if dir == roles_dir + "tasks":
                    continue

                role_dir_list.append(re.sub(r'\/tasks$', '', dir))

        for role_dir in role_dir_list:
            # ディレクトリ名前方一致したものは除外
            if self.childRole(role_dir, role_dir_list) is False:
                continue

            # rolesディレクトリ以降の階層をrole名にする
            role_name = re.sub(r'^' + preg_roles_dir, '', role_dir)
            RoleDirList[role_dir] = role_name

        if result_code is True:
            # roleディレクトリが存在しているか
            if len(RoleDirList) <= 0:
                errormsg = g.appmsg.get_api_message("MSG-10258")
                return False, RoleDirList, errormsg

        if result_code is True:
            # ロール名に%が含まれていないか
            errormsg = ""
            for role_dir, role_name in RoleDirList.items():
                ret = re.search(r'%', role_name)
                if ret:
                    if len(errormsg) > 0:
                        errormsg = '%s\n' % (errormsg)

                    errormsg = g.appmsg.get_api_message("MSG-10612", [role_name])
                    result_code = False

        if result_code is True:
            # ロール名が1024バイト以上あるか
            errormsg = ""
            for role_dir, role_name in RoleDirList.items():
                if len(role_name) > 1024:
                    if len(errormsg) > 0:
                        errormsg = '%s\n' % (errormsg)

                    errormsg = g.appmsg.get_api_message("MSG-10613", [role_name])
                    result_code = False

        if result_code is True:
            # ディレクトリのパーミッションを変更
            cmd = ['find', BaseDir, '-type', 'd', '-exec', 'chmod', '755', '{}', '+']
            subprocess.call(cmd)

        return result_code, RoleDirList, errormsg

    def childRole(self, data, DirList):

        """
        処理内容
          roleディレクトリとして扱うかを判定
          taskディレクトリがあるディレクトリをroleディレクトリとして扱う
          roles
            nest_dir1
              sample_role1
                tasks
                default
            nest_dir2
              sample_role2
                tasks
                default
                sample_role3
                  tasks
         但し、tasksディレクトリがネストしているような階層のroleディレクトリは除外する。
         sample_role3は除外

        パラメータ
          data:        roleディレクトリ
          RoleDirList: rolesディレクトリ配下のtasksが定義されているディレクトリ一覧
        戻り値
          true:   roleディレクトリとして扱わない。
          false:  roleディレクトリとして扱う。
        """

        data = '%s/' % (data)
        for dirs in DirList:
            dirs = '%s/' % (dirs)

            # 完全一致はスキップ(自分自身)
            if data == dirs:
                continue

            # 前方一致は除外
            if data.startswith(dirs):
                return False

        return True


#################################################################################
# defalte変数ファイルに登録されている変数を解析
#################################################################################
class DefaultVarsFileAnalysis():

    """
    処理概要
      defalte変数ファイルに登録されている変数を解析
    """

    LC_IDEL = "0"
    LC_VAR_VAL = "1"
    LC_ARRAY_VAR_VAL = "2"
    LC_MULTI_VAR_VAL = "3"
    LC_LISTARRAY_VAR_VAL = "4"
    LC_LIST_IDEL = "0"
    LC_LIST_VAR = "1"
    LC_LIST_VAL = "2"

    # 変数定義を判定する正規表記  /^VAR_(\S+):/ => /^VAR_(\S+)(\s*):/
    LC_VARNAME_MATCHING = r"^VAR_(\S+)(\s*):"
    LC_USER_VARNAME_MATCHING = r"^[a-zA-Z0-9_]*(\s*):"

    # 変数タイプ
    LC_VAR_TYPE_ITA = "0"  # ITA (VAR_)
    LC_VAR_TYPE_USER = "1"  # ユーザー
    LC_VAR_TYPE_USER_ITA = "2"  # ユーザー読替(LCA_)

    def __init__(self, in_objMTS):

        """
        処理内容
          コンストラクタ

        パラメータ
          なし

        戻り値
          なし
        """

        self.lv_objMTS = in_objMTS
        self.lv_msg_pkg_name = None
        self.lv_run_mode = AnscConst.LC_RUN_MODE_STD
        self.lv_setVariableDefineLocation = None

        self.php_array = lambda x: x.items() if isinstance(x, dict) else enumerate(x)
        self.php_keys = lambda x: x.keys() if isinstance(x, dict) else range(len(x))
        self.php_vals = lambda x: x.values() if isinstance(x, dict) else x

    def is_num(self, s):
        try:
            float(s)
        except ValueError:
            return False
        else:
            return True

    def chkVarsStruct(self, ina_vars_list, ina_def_array_vars_list, ina_err_vars_list):

        """
        処理内容
          ロールパッケージ内のデェフォルト変数ファイルで定義されている配列変数の
          構造が一致しているか判定

        パラメータ
          ina_vars_list:            defalte変数ファイルの変数リスト格納
                                       非配列変数　ina_vars_list[ロール名][変数名] = 0;
                                       配列変数　  ina_vars_list[ロール名][変数名] = array(配列変数名, ....)
          ina_def_array_vars_list:  defalte変数ファイルの多次元変数リスト格納
          ina_err_vars_list:        ロールパッケージ内で使用している変数で構造が違う変数のリスト
                                       in_err_vars_list[変数名][ロールパッケージ名][ロール名]

        戻り値
          true:   正常
          false:  異常
        """

        ret_code = True
        chk_role_name = None

        # 多次元変数をKeyに他ロールに多次元変数以外の変数があるか判定
        for role_name, vars_list in self.php_array(ina_def_array_vars_list):
            for var_name, chl_vars_list in self.php_array(vars_list):
                # 他のロールで同じ変数名で構造が異なるのものがあるか確認
                for chk_role_name, chk_vars_list in self.php_array(ina_vars_list):
                    if role_name == chk_role_name:
                        # 同一のロール内のチェックはスキップする
                        continue

                    if  chk_role_name in ina_vars_list and var_name in ina_vars_list[chk_role_name] \
                    and ina_vars_list[chk_role_name][var_name] is not None \
                    and (type(ina_vars_list[chk_role_name][var_name]) not in (dict, list) or len(ina_vars_list[chk_role_name][var_name]) > 0):
                        # エラーになった変数とロールを退避
                        if var_name not in ina_err_vars_list:
                            ina_err_vars_list[var_name] = {}
                            ina_err_vars_list[var_name][chk_role_name] = None
                            ina_err_vars_list[var_name][role_name] = None

                        ina_err_vars_list[var_name][chk_role_name] = 0
                        ina_err_vars_list[var_name][role_name] = 0
                        ret_code = False

        # 同じ多次元変数が他ロールにある場合に構造が同じか判定する
        for role_name, vars_list in self.php_array(ina_def_array_vars_list):
            for var_name, chl_vars_list in self.php_array(vars_list):
                for chk_role_name, chk_vars_list in self.php_array(ina_def_array_vars_list):
                    if role_name == chk_role_name:
                        # 同一のロール内のチェックはスキップする
                        continue

                    # 他ロールに同じ多次元変数がある場合
                    if  chk_role_name in ina_def_array_vars_list \
                    and var_name in ina_def_array_vars_list[chk_role_name] \
                    and ina_def_array_vars_list[chk_role_name][var_name] is not None \
                    and (
                        type(ina_def_array_vars_list[chk_role_name][var_name]) not in (dict, list)
                        or len(ina_def_array_vars_list[chk_role_name][var_name]) > 0
                    ):
                        # 多次元構造を比較する
                        diff_vars_list = []
                        diff_vars_list.append(ina_def_array_vars_list[role_name][var_name]['DIFF_ARRAY'])
                        diff_vars_list.append(ina_def_array_vars_list[chk_role_name][var_name]['DIFF_ARRAY'])
                        error_code = ""
                        line = ""

                        ret, error_code, line = self.InnerArrayDiff(diff_vars_list, error_code, line)
                        if not ret:
                            # エラーになった変数とロールを退避
                            if var_name not in ina_err_vars_list:
                                ina_err_vars_list[var_name] = {}
                                ina_err_vars_list[var_name][chk_role_name] = None
                                ina_err_vars_list[var_name][role_name] = None

                            ina_err_vars_list[var_name][chk_role_name] = 0
                            ina_err_vars_list[var_name][role_name] = 0
                            ret_code = False

        # 変数検索  ロール=>変数名
        for role_name, vars_list in self.php_array(ina_vars_list):
            if type(vars_list) in (list, dict):
                if len(vars_list) > 0:
                    # 変数名リスト=>変数名
                    for var_name, var_type in self.php_array(vars_list):
                        # 多次元配列に同じ変数名があるか判定
                        if  chk_role_name in ina_def_array_vars_list \
                        and var_name in ina_def_array_vars_list[chk_role_name] \
                        and ina_def_array_vars_list[chk_role_name][var_name] is not None \
                        and (
                            type(ina_def_array_vars_list[chk_role_name][var_name]) not in (dict, list)
                            or len(ina_def_array_vars_list[chk_role_name][var_name]) > 0
                        ):
                            # エラーになった変数とロールを退避
                            if var_name not in ina_err_vars_list:
                                ina_err_vars_list[var_name] = {}
                                ina_err_vars_list[var_name][chk_role_name] = None
                                ina_err_vars_list[var_name][role_name] = None

                            ina_err_vars_list[var_name][chk_role_name] = 0
                            ina_err_vars_list[var_name][role_name] = 0
                            ret_code = False

                        # 他のロールで同じ変数名で構造が異なるのものがあるか確認
                        for chk_role_name, chk_vars_list in self.php_array(ina_vars_list):
                            if role_name == chk_role_name:
                                # 同一のロール内のチェックはスキップする
                                continue

                            if chk_role_name not in ina_vars_list or var_name not in ina_vars_list[chk_role_name] \
                            or ina_vars_list[chk_role_name][var_name] is None \
                            or (type(ina_vars_list[chk_role_name][var_name]) in (list, dict) and len(ina_vars_list[chk_role_name][var_name]) <= 0):
                                # 同じ変数名なし
                                continue

                            else:
                                # 配列変数以外の場合に一般変数と複数具体値変数の違いを判定
                                if ina_vars_list[chk_role_name][var_name] != ina_vars_list[role_name][var_name]:
                                    # エラーになった変数とロールを退避
                                    if var_name not in ina_err_vars_list:
                                        ina_err_vars_list[var_name] = {}
                                        ina_err_vars_list[var_name][chk_role_name] = None
                                        ina_err_vars_list[var_name][role_name] = None

                                    ina_err_vars_list[var_name][chk_role_name] = 0
                                    ina_err_vars_list[var_name][role_name] = 0
                                    ret_code = False

        return ret_code, ina_err_vars_list

    def chkallVarsStruct(self, ina_vars_list, ina_def_array_vars_list, ina_err_vars_list):

        """
        処理内容
          指定されているロールパッケージ内のデェフォルト変数ファイルで定義されている配列変数の
          構造が一致しているか判定

        パラメータ
          ina_vars_list:            defalte変数ファイルの変数リスト格納
                                       非配列変数  ina_vars_list[ロールパッケージ名][ロール名][変数名] = 0;
                                       配列変数    ina_vars_list[ロールパッケージ名][ロール名][変数名] = array(配列変数名, ....)
          ina_def_array_vars_list:  defalte変数ファイルの多次元変数リスト格納
          ina_err_vars_list:        ロールパッケージ内で使用している変数で構造が違う変数のリスト
                                       in_err_vars_list[変数名][ロールパッケージ名][ロール名]

        戻り値
          true:   正常
          false:  異常
        """

        ret_code = True
        var_name = ''
        pkg_name = ''
        role_name = ''
        chk_pkg_name = ''
        chk_role_name = ''

        # 多次元変数をKeyに他ロールに多次元変数以外の変数があるか判定
        for pkg_name, role_list in self.php_array(ina_def_array_vars_list):
            for role_name, vars_list in self.php_array(role_list):
                for var_name, chl_vars_list in self.php_array(vars_list):
                    # 他のロールで同じ変数名で構造が異なるのものがあるか確認
                    for chk_pkg_name, chk_role_list in self.php_array(ina_vars_list):
                        for chk_role_name, chk_vars_list in self.php_array(chk_role_list):
                            # 同一ロールパッケージ+ロールのチェックはスキップする
                            if pkg_name == chk_pkg_name and role_name == chk_role_name:
                                # 同一のロール内のチェックはスキップする
                                continue

                            if  chk_pkg_name in ina_vars_list \
                            and chk_role_name in ina_vars_list[chk_pkg_name] \
                            and var_name in ina_vars_list[chk_pkg_name][chk_role_name] \
                            and ina_vars_list[chk_pkg_name][chk_role_name][var_name] is not None \
                            and (
                                type(ina_vars_list[chk_pkg_name][chk_role_name][var_name]) not in (list, dict) 
                                or len(ina_vars_list[chk_pkg_name][chk_role_name][var_name]) > 0
                            ):
                                # エラーになった変数とロールを退避
                                if var_name not in ina_err_vars_list:
                                    ina_err_vars_list[var_name] = {}

                                if pkg_name not in ina_err_vars_list[var_name]:
                                    ina_err_vars_list[var_name][pkg_name] = {}

                                if chk_pkg_name not in ina_err_vars_list[var_name]:
                                    ina_err_vars_list[var_name][chk_pkg_name] = {}

                                if role_name not in ina_err_vars_list[var_name][pkg_name]:
                                    ina_err_vars_list[var_name][pkg_name][role_name] = None

                                if chk_role_name not in ina_err_vars_list[var_name][chk_pkg_name]:
                                    ina_err_vars_list[var_name][chk_pkg_name][chk_role_name] = None

                                ina_err_vars_list[var_name][pkg_name][role_name] = 0
                                ina_err_vars_list[var_name][chk_pkg_name][chk_role_name] = 0
                                ret_code = False

        # 同じ多次元変数が他ロールにある場合に構造が同じか判定する
        for pkg_name, role_list in self.php_array(ina_def_array_vars_list):
            for role_name, vars_list in self.php_array(role_list):
                for var_name, chl_vars_list in self.php_array(vars_list):
                    for chk_pkg_name, chk_role_list in self.php_array(ina_def_array_vars_list):
                        for chk_role_name, chk_vars_list in self.php_array(chk_role_list):
                            # 同一ロールパッケージ+ロールのチェックはスキップする
                            if pkg_name == chk_pkg_name and role_name == chk_role_name:
                                # 同一のロール内のチェックはスキップする
                                continue

                            # 他ロールに同じ多次元変数がある場合
                            if  chk_pkg_name in ina_def_array_vars_list \
                            and chk_role_name in ina_def_array_vars_list[chk_pkg_name] \
                            and var_name in ina_def_array_vars_list[chk_pkg_name][chk_role_name] \
                            and ina_def_array_vars_list[chk_pkg_name][chk_role_name][var_name] is not None \
                            and (
                                type(ina_def_array_vars_list[chk_pkg_name][chk_role_name][var_name]) not in (list, dict) 
                                or len(ina_def_array_vars_list[chk_pkg_name][chk_role_name][var_name]) > 0
                            ):
                                # 多次元構造を比較する
                                diff_vars_list = []
                                diff_vars_list.append(ina_def_array_vars_list[pkg_name][role_name][var_name]['DIFF_ARRAY'])
                                diff_vars_list.append(ina_def_array_vars_list[chk_pkg_name][chk_role_name][var_name]['DIFF_ARRAY'])
                                error_code = ""
                                line = ""

                                ret, error_code, line = self.InnerArrayDiff(diff_vars_list, error_code, line)
                                if not ret:
                                    # エラーになった変数とロールを退避
                                    if var_name not in ina_err_vars_list:
                                        ina_err_vars_list[var_name] = {}

                                    if pkg_name not in ina_err_vars_list[var_name]:
                                        ina_err_vars_list[var_name][pkg_name] = {}

                                    if chk_pkg_name not in ina_err_vars_list[var_name]:
                                        ina_err_vars_list[var_name][chk_pkg_name] = {}

                                    if role_name not in ina_err_vars_list[var_name][pkg_name]:
                                        ina_err_vars_list[var_name][pkg_name][role_name] = None

                                    if chk_role_name not in ina_err_vars_list[var_name][chk_pkg_name]:
                                        ina_err_vars_list[var_name][chk_pkg_name][chk_role_name] = None

                                    ina_err_vars_list[var_name][pkg_name][role_name] = 0
                                    ina_err_vars_list[var_name][chk_pkg_name][chk_role_name] = 0
                                    ret_code = False

        # 多次元変数以外をKeyに他ロールに多次元変数以外の変数があるか判定
        # 変数検索  ロールパッケージ名=>ロールリスト
        for pkg_name, role_list in self.php_array(ina_vars_list):
            # 変数検索  ロール=>変数名リスト
            for role_name, vars_list in self.php_array(role_list):
                if type(vars_list) in (list, dict):
                    if len(vars_list) > 0:
                        # 変数名リスト=>変数名
                        for var_name, var_type in self.php_array(vars_list):
                            # 多次元変数に同じ変数名があるか判定
                            if  chk_pkg_name in ina_def_array_vars_list \
                            and chk_role_name in ina_def_array_vars_list[chk_pkg_name] \
                            and var_name in ina_def_array_vars_list[chk_pkg_name][chk_role_name] \
                            and ina_def_array_vars_list[chk_pkg_name][chk_role_name][var_name] is not None \
                            and (
                                type(ina_def_array_vars_list[chk_pkg_name][chk_role_name][var_name]) not in (list, dict)
                                or len(ina_def_array_vars_list[chk_pkg_name][chk_role_name][var_name]) > 0
                            ):
                                # エラーになった変数とロールを退避
                                if var_name not in ina_err_vars_list:
                                    ina_err_vars_list[var_name] = {}

                                if pkg_name not in ina_err_vars_list[var_name]:
                                    ina_err_vars_list[var_name][pkg_name] = {}

                                if chk_pkg_name not in ina_err_vars_list[var_name]:
                                    ina_err_vars_list[var_name][chk_pkg_name] = {}

                                if role_name not in ina_err_vars_list[var_name][pkg_name]:
                                    ina_err_vars_list[var_name][pkg_name][role_name] = None

                                if chk_role_name not in ina_err_vars_list[var_name][chk_pkg_name]:
                                    ina_err_vars_list[var_name][chk_pkg_name][chk_role_name] = None

                                ina_err_vars_list[var_name][pkg_name][role_name] = 0
                                ina_err_vars_list[var_name][chk_pkg_name][chk_role_name] = 0
                                ret_code = False
                                continue

                            # 他ロールパッケージ変数検索  ロールパッケージ名=>ロールリスト
                            for chk_pkg_name, chk_role_list in self.php_array(ina_vars_list):
                                # 他のロールで同じ変数名で構造が異なるのものがあるか確認
                                for chk_role_name, chk_vars_list in self.php_array(chk_role_list):
                                    # 同一ロールパッケージ+ロールのチェックはスキップする
                                    if pkg_name == chk_pkg_name and role_name == chk_role_name:
                                        continue

                                    if var_name not in chk_vars_list \
                                    or chk_vars_list[var_name] is None \
                                    or (type(chk_vars_list[var_name]) in (list, dict) and len(chk_vars_list[var_name]) <= 0):
                                        # 同じ変数名なし
                                        continue

                                    # 一般変数と複数具体値変数の違いを判定
                                    if ina_vars_list[chk_pkg_name][chk_role_name][var_name] != ina_vars_list[pkg_name][role_name][var_name]:
                                        # エラーになった変数とロールを退避
                                        if var_name not in ina_err_vars_list:
                                            ina_err_vars_list[var_name] = {}

                                        if pkg_name not in ina_err_vars_list[var_name]:
                                            ina_err_vars_list[var_name][pkg_name] = {}

                                        if chk_pkg_name not in ina_err_vars_list[var_name]:
                                            ina_err_vars_list[var_name][chk_pkg_name] = {}

                                        if role_name not in ina_err_vars_list[var_name][pkg_name]:
                                            ina_err_vars_list[var_name][pkg_name][role_name] = None

                                        if chk_role_name not in ina_err_vars_list[var_name][chk_pkg_name]:
                                            ina_err_vars_list[var_name][chk_pkg_name][chk_role_name] = None

                                        ina_err_vars_list[var_name][pkg_name][role_name] = 0
                                        ina_err_vars_list[var_name][chk_pkg_name][chk_role_name] = 0
                                        ret_code = False

        return ret_code, ina_err_vars_list

    def VarsStructErrmsgEdit(self, ina_err_vars_list):

        """
        処理内容
          配列変数の構造が違う場合のエラーメッセージを編集

        パラメータ
          ina_err_vars_list:      ロールパッケージ内で使用している変数で構造が違う変数のリスト
                                     in_err_vars_list[変数名][ロール名]

        戻り値
          エラーメッセージ
        """

        # MSG-10289 = "default変数ファイルに登録されている変数の属性が不一致。\n"
        errmsg = g.appmsg.get_api_message("MSG-10289")

        # err_vars_list[変数名][ロール名]
        for err_var_name, err_role_list in self.php_array(ina_err_vars_list):
            err_files = ""
            for err_role_name, dummy in self.php_array(err_role_list):
                err_files = '%sroles/%s\n' % (err_files, err_role_name)

            if err_files:
                errmsg = '%s%s' % (errmsg, g.appmsg.get_api_message("MSG-10290", [err_var_name, err_files]))

        return errmsg

    def allVarsStructErrmsgEdit(self, ina_err_vars_list):

        """
        処理内容
          配列変数の構造が違う場合のエラーメッセージを編集

        パラメータ
          ina_err_vars_list:      ロールパッケージ内で使用している変数で構造が違う変数のリスト
                                     in_err_vars_list[変数名][ロールパッケージ名][ロール名]

        戻り値
          エラーメッセージ
        """

        errmsg = g.appmsg.get_api_message("MSG-10289")
        for err_var_name, err_pkg_list in self.php_array(ina_err_vars_list):
            err_files = ""
            for err_pkg_name, err_role_list in self.php_array(err_pkg_list):
                for err_role_name, dummy in self.php_array(err_role_list):
                    err_files = '%s%s' % (err_files, g.appmsg.get_api_message("MSG-10291", [err_pkg_name]))
                    err_files = '%sroles/%s\n' % (err_files, err_role_name)

            if err_files:
                errmsg = '%s%s' % (errmsg, g.appmsg.get_api_message("MSG-10290", [err_var_name, err_files]))

        return errmsg

    def chkDefVarsListPlayBookVarsList(self, ina_play_vars_list, ina_def_vars_list, ina_def_array_vars_list, in_errmsg, ina_system_vars):

        """
        処理内容
          ロールパッケージ内のPlaybookで定義されている変数がデェフォルト変数定義
          ファイルで定義されているか判定
       
        パラメータ
          ina_play_vars_list:     ロールパッケージ内のPlaybookで定義している変数リスト
                                     [role名][変数名]=0
          ina_def_vars_list:      defalte変数ファイルの変数リスト
                                     非配列変数  ina_vars_list[ロール名][変数名] = 0;
                                     配列変数    ina_vars_list[ロール名][変数名] = array(配列変数名, ....)
       
        戻り値
          true:   正常
          false:  異常
        """

        in_errmsg = ""
        ret_code = True

        # ロールパッケージ内のPlaybookで定義している変数が無い場合は処理しない
        if len(ina_play_vars_list) <= 0:
            return ret_code, in_errmsg

        for role_name, vars_list in self.php_array(ina_play_vars_list):
            for vars_name, dummy in self.php_array(vars_list):
                # ITA独自変数はチェック対象外とする
                if vars_name in ina_system_vars:
                    continue

                if role_name not in ina_def_vars_list \
                or vars_name not in ina_def_vars_list[role_name] \
                or ina_def_vars_list[role_name][vars_name] is None \
                or (type(ina_def_vars_list[role_name][vars_name]) in (list, dict) and len(ina_def_vars_list[role_name][vars_name]) <= 0):
                    if role_name not in ina_def_array_vars_list \
                    or vars_name not in ina_def_array_vars_list[role_name] \
                    or ina_def_array_vars_list[role_name][vars_name] is None \
                    or (type(ina_def_array_vars_list[role_name][vars_name] is None) in (list, dict) and len(ina_def_array_vars_list[role_name][vars_name]) <= 0):
                        in_errmsg = '%s\n%s' % (in_errmsg, g.appmsg.get_api_message("MSG-10294", [role_name, vars_name]))
                        ret_code = False

        return ret_code, in_errmsg

    def margeDefaultVarsList(
        self,
        ina_vars_list, ina_vars_val_list,
        ina_user_vars_list, ina_user_vars_val_list,
        ina_array_vars_list, ina_user_array_vars_list
    ):

        """
        処理内容
          デフォルト定義変数ファイルとユーザー義変数ファイルに定義されている変数
          の情報をマージする。

          ina_vars_list:          デフォルト定義変数ファイル内に定義されている変数リスト
                                     非配列変数  ina_vars_list[変数名]
                                     配列変数    ina_vars_list[変数名] = array(配列変数名, ....)
          ina_vars_val_list:      デフォルト定義変数ファイル内に定義されている変数具体値リスト
                                     一般変数
                                       ina_vars_val_list[変数名][0]=具体値
                                     複数具体値変数
                                       ina_vars_val_list[変数名][2][メンバー変数]=array(1=>具体値,2=>具体値....)
          ina_user_vars_list:     ユーザー義変数ファイル内に定義されている変数リスト
                                     非配列変数  ina_vars_list[変数名]
                                     配列変数    ina_vars_list[変数名] = array(配列変数名, ....)
          ina_user_vars_val_list: ユーザー義変数ファイル内に定義されている変数具体値リスト
                                     一般変数
                                       ina_vars_val_list[変数名][0]=具体値
                                     複数具体値変数
          ina_array_vars_list:    デフォルト定義変数ファイル内に定義されている多次元変数リスト
          ina_user_array_vars_list: ユーザー義変数ファイル内に定義されている多次元変数リスト

        戻り値
          なし
        """

        del_user_vars_keys = []

        if  ina_user_vars_list is not None \
        and (type(ina_user_vars_list) not in (list, dict) or len(ina_user_vars_list) > 0):
            # ユーザー変数定義ファイルに登録されている変数をキーにループ
            for var_name, vars_list in self.php_array(ina_user_vars_list):
                # default変数定義ファイルに変数が登録されているか判定
                if  var_name in ina_vars_list \
                and ina_vars_list[var_name] is not None \
                and (type(ina_vars_list[var_name]) not in (list, dict) or len(ina_vars_list[var_name]) > 0):
                    # ユーザー変数定義ファイルとdefault変数定義ファイルの両方にある変数のルート
                    # default変数定義ファイルに変数が登録されている

                    # 変数の型を判定する
                    if ina_vars_list[var_name] != ina_user_vars_list[var_name]:
                        # 変数の型が一致しない場合はdefault変数定義ファイルの変数具体値情報から該当変数の情報を削除する
                        del ina_vars_val_list[var_name]

                    # default変数定義ファイルの変数情報から該当変数の情報を削除する
                    del ina_vars_list[var_name]

                    # default変数定義ファイルの変数情報にユーザー変数定義ファイルに
                    # 登録されている変数情報を追加
                    ina_vars_list[var_name] = ina_user_vars_list[var_name]

                    # ユーザー変数定義ファイルの変数具体値情報は使わない

                    # ユーザー変数定義ファイルの変数情報から削除
                    del_user_vars_keys.append(var_name)

                else:
                    # default変数定義ファイルに変数が登録されていない

                    # default変数定義ファイルに多次元変数として登録されているか判定
                    if var_name in ina_array_vars_list and len(ina_array_vars_list[var_name]) > 0:
                        # ユーザー変数定義ファイルとdefault多次元変数定義ファイルの両方にある変数のルート
                        # default変数定義ファイルの多次元変数の情報を削除
                        del ina_array_vars_list[var_name]

                    else:
                        # ユーザー変数定義ファイルにあるがdefault変数定義ファイルのない変数のルート
                        pass

                    # default変数定義ファイルの変数情報にユーザー変数定義ファイルに
                    # 登録されている変数情報を追加
                    ina_vars_list[var_name] = ina_user_vars_list[var_name]

                    # ユーザー変数定義ファイルの変数情報から削除
                    del_user_vars_keys.append(var_name)

                    # ユーザー変数定義ファイルの変数具体値情報は使わない

        for k in del_user_vars_keys:
            if k in ina_user_vars_list:
                del ina_user_vars_list[k]

        del_user_vars_keys = []

        if  ina_user_array_vars_list is not None \
        and (type(ina_user_array_vars_list) not in (list, dict) or len(ina_user_array_vars_list) > 0):
            # ユーザー変数定義ファイルに登録されている多次元変数をキーにループ
            for var_name, vars_list in self.php_array(ina_user_array_vars_list):
                # default変数定義ファイルに多次元変数が登録されているか判定
                if  var_name in ina_array_vars_list \
                and ina_array_vars_list[var_name] is not None \
                and (type(ina_array_vars_list[var_name]) not in (list, dict) or len(ina_array_vars_list[var_name]) > 0):
                    # default変数定義ファイルに多次元変数が登録されている

                    # 変数構造が同じか判定する
                    # 多次元構造を比較する
                    diff_vars_list = []
                    diff_vars_list.append(ina_array_vars_list[var_name]['DIFF_ARRAY'])
                    diff_vars_list.append(ina_user_array_vars_list[var_name]['DIFF_ARRAY'])
                    error_code = ""
                    line = ""

                    ret, error_code, line = self.InnerArrayDiff(diff_vars_list, error_code, line)
                    if not ret:
                        # 変数構造が一致しない
                        # ユーザー変数定義ファイルの情報をdefault変数定義ファイルに設定
                        del ina_array_vars_list[var_name]
                        ina_array_vars_list[var_name] = ina_user_array_vars_list[var_name]

                        # 具体値はなしにする
                        del ina_array_vars_list[var_name]['VAR_VALUE']
                        ina_array_vars_list[var_name]['VAR_VALUE'] = []
                        # ユーザー多次元変数定義ファイルとdefault多次元変数定義ファイルの両方にあり型が一致しない変数のルート

                    else:
                        # ユーザー多次元変数定義ファイルとdefault多次元変数定義ファイルの両方にあり型が一致する変数のルート
                        # 変数の構造が同じなのでdefault変数定義ファイルの内容をそのまま使う
                        pass

                    # ユーザー変数定義ファイルの変数情報を削除する
                    del_user_vars_keys.append(var_name)

                else:
                    # default変数定義ファイルに多次元変数が登録されていない

                    # default変数定義ファイルに変数が登録されているか判定
                    if var_name in ina_vars_list and len(ina_vars_list[var_name]) > 0:
                        # ユーザー多次元変数定義ファイルとdefault変数定義ファイルの両方にある変数のルート
                        # default変数定義ファイルに変数が登録されている

                        # default変数定義ファイルの変数情報から該当変数の情報を削除する
                        del ina_vars_list[var_name]

                        # default変数定義ファイルの変数具体値情報から該当変数の情報を削除する
                        del ina_vars_val_list[var_name]

                        # default変数定義ファイルの変数情報にユーザー変数定義ファイルに
                        # 登録されている多次元変数情報を追加
                        ina_array_vars_list[var_name] = ina_user_array_vars_list[var_name]

                        # ユーザー変数定義ファイルの変数具体値情報は使わない
                        del ina_array_vars_list[var_name]['VAR_VALUE']
                        ina_array_vars_list[var_name]['VAR_VALUE'] = []

                        # ユーザー変数定義ファイルの変数情報から削除
                        if var_name in ina_user_vars_list:
                            del ina_user_vars_list[var_name]

                    else:
                        # ユーザー多次元変数定義ファイルにのみある変数のルート

                        # default変数定義ファイルに変数が登録されていない

                        # default変数定義ファイルの変数情報にユーザー変数定義ファイルに
                        # 登録されている変数情報を追加
                        ina_array_vars_list[var_name] = ina_user_array_vars_list[var_name]

                        # 具体値はなしにする
                        del ina_array_vars_list[var_name]['VAR_VALUE']
                        ina_array_vars_list[var_name]['VAR_VALUE'] = []

                        # ユーザー変数定義ファイルの変数情報を削除する
                        del_user_vars_keys.append(var_name)

        for k in del_user_vars_keys:
            if k in ina_user_array_vars_list:
                del ina_user_array_vars_list[k]

        return ina_vars_list, ina_vars_val_list, ina_array_vars_list

    def debuglog(self, line, msg):

        pass

    def chkStandardVariable(self, in_var, in_var_array, ina_vars_list, ina_varsval_list, in_var_type):

        """
        処理内容
          YAMLパーサーから取得した配列構造が一般変数か判定
        パラメータ
          in_var_array:               YAMLパーサーから取得した配列構造
        戻り値
          true: 正常  false:異常
        """

        if type(in_var_array) not in (list, dict):
            # VAR_か読替変数のみ変数情報退避
            if in_var_type in [self.LC_VAR_TYPE_ITA, self.LC_VAR_TYPE_USER_ITA] or self.GetRunModeVarFile() == AnscConst.LC_RUN_MODE_VARFILE:
                if  in_var not in ina_vars_list:
                    ina_vars_list[in_var] = None

                if in_var not in ina_varsval_list:
                    ina_varsval_list[in_var] = [None,]

                ina_vars_list[in_var] = 0
                ina_varsval_list[in_var][0] = in_var_array

            return True, ina_vars_list, ina_varsval_list

        return False, ina_vars_list, ina_varsval_list

    def chkMultiValueVariable(self, in_var, in_var_array, ina_vars_list, ina_varsval_list, in_var_type):

        """
        処理内容
          YAMLパーサーから取得した配列構造が複数具体値の変数か判定
        パラメータ
          in_var_array:               YAMLパーサーから取得した配列構造
        戻り値
          true: 正常  false:異常
        """

        ret = self.chkMultiValueVariableSub(in_var_array)
        if not ret:
            return False, ina_vars_list, ina_varsval_list

        # VAR_か読替変数のみ変数情報退避
        if in_var_type in [self.LC_VAR_TYPE_ITA, self.LC_VAR_TYPE_USER_ITA] or self.GetRunModeVarFile() == AnscConst.LC_RUN_MODE_VARFILE:
            if in_var not in ina_vars_list:
                ina_vars_list[in_var] = None

            ina_vars_list[in_var] = 1
            if len(in_var_array) <= 0:
                pass

            line = 1
            for chk_array in in_var_array:
                if in_var not in ina_varsval_list:
                    ina_varsval_list[in_var] = {1:{}}

                if line in ina_varsval_list[in_var][1]:
                    ina_varsval_list[in_var][1][line] = None

                ina_varsval_list[in_var][1][line] = chk_array
                line = line + 1

        return True, ina_vars_list, ina_varsval_list

    def chkMultiValueVariableSub(self, in_var_array):

        """
        処理内容
          配列構造が複数具体値の変数か判定
        パラメータ
          in_var_array:               YAMLパーサーから取得した配列構造
        戻り値
          true: 正常  false:異常
        """

        if type(in_var_array) in (list, dict):
            if len(in_var_array) <= 0:
                return True

            for key, chk_array in self.php_array(in_var_array):
                if not self.is_num(key):
                    return False

                if type(chk_array) in (list, dict):
                    return False

            return True

        return False

    def chkMultiArrayVariable(
        self,
        in_var, in_var_array, ina_vars_list, ina_varsval_list,
        in_var_type, in_parent_var_name,
        ina_array_vars_list,
        in_role_name, in_file_name,
        in_errmsg, in_f_name, in_f_line,
        in_msg_role_pkg_name
    ):

        """
        処理内容
          YAMLパーサーから取得した配列構造を解析する。
        パラメータ
          in_var:                     親変数名
          in_var_array:               YAMLパーサーから取得した配列構造
          ina_vars_list:              現在未使用
          ina_varsval_list:           現在未使用
          in_var_type:                変数区分 VAR_かどうか
          in_parent_var_name:         親変数名
          ina_array_vars_list:        配列構造の解析結果
          in_role_name:               対象のロール名
          in_file_name:               対象のパッケージファイル名
          in_errmsg:                  エラー時のエラーメッセージ
          in_f_name:                  エラー時のファイル名
          in_f_line:                  エラー時の行番号
          
        戻り値
          true: 正常  false:異常
        """

        in_f_line = os.path.basename(inspect.currentframe().f_code.co_filename)
        if type(in_var_array) in (dict, list):
            ret = self.is_assoc(in_var_array)
            if ret == -1:
                # MSG-10301 = "変数定義の解析に失敗しました。{}"
                in_errmsg = AnsibleMakeMessage().AnsibleMakeMessage(
                    self.GetRunModeVarFile(),
                    'MSG-10301',
                    [in_msg_role_pkg_name, in_role_name, in_file_name, in_parent_var_name]
                )
                in_f_line = inspect.currentframe().f_lineno
                return False, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line

            col_count = 0
            assign_count = 0
            error_code = ""
            line = ""
            diff_vars_list = {}
            varval_list = {}
            array_col_count_list = {}

            # YAMLパーサーが取得した多次元配列の構造から具体値を排除する。また配列階層の配列数と具体値を取得する
            ret, diff_vars_list, varval_list, array_col_count_list, error_code, line, col_count, assign_count = self.MakeMultiArrayToDiffMultiArray(
                in_var_array,
                diff_vars_list,
                varval_list,
                "",
                array_col_count_list,
                "",  # 配列要素番号
                error_code, line, col_count, assign_count
            )
            if not ret:
                in_errmsg = AnsibleMakeMessage().AnsibleMakeMessage(
                    self.GetRunModeVarFile(),
                    error_code,
                    [in_msg_role_pkg_name, in_role_name, in_file_name, in_parent_var_name]
                )
                in_f_line = line
                return False, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line

            error_code = ""
            line = ""
            ret, error_code, line = self.InnerArrayDiff(diff_vars_list, error_code, line)
            if not ret:
                in_errmsg = AnsibleMakeMessage().AnsibleMakeMessage(
                    self.GetRunModeVarFile(),
                    error_code,
                    [in_msg_role_pkg_name, in_role_name, in_file_name, in_parent_var_name]
                )
                in_f_line = line
                return False, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line

            col_count = 0
            assign_count = 0
            error_code = ""
            line = ""
            parent_var_key = 0
            chl_var_key = 0
            nest_lvl = 0
            vars_chain_list = {}

            chain_make_array = in_var_array

            ret, vars_chain_list, error_code, line, col_count, assign_count, chl_var_key = self.MakeMultiArrayToFirstVarChainArray(
                False, "", "",
                chain_make_array,
                vars_chain_list,
                error_code,
                line,
                col_count,
                assign_count,
                parent_var_key,
                chl_var_key,
                nest_lvl
            )
            if not ret:
                in_errmsg = AnsibleMakeMessage().AnsibleMakeMessage(
                    self.GetRunModeVarFile(),
                    error_code,
                    [in_msg_role_pkg_name, in_role_name, in_file_name, in_parent_var_name]
                )
                in_f_line = line
                return False, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line

            # VAR_か読替変数のみ変数情報退避
            if in_var_type in [self.LC_VAR_TYPE_ITA, self.LC_VAR_TYPE_USER_ITA] or self.GetRunModeVarFile() == AnscConst.LC_RUN_MODE_VARFILE:

                vars_last_chain_list = []
                ret, vars_last_chain_list, error_code, line = self.MakeMultiArrayToLastVarChainArray(vars_chain_list, array_col_count_list, vars_last_chain_list, error_code, line)
                if not ret:
                    in_errmsg = AnsibleMakeMessage().AnsibleMakeMessage(
                        self.GetRunModeVarFile(),
                        error_code,
                        [in_msg_role_pkg_name, in_role_name, in_file_name, in_parent_var_name]
                    )
                    in_f_line = line
                    return False, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line

                if in_var not in ina_array_vars_list:
                    ina_array_vars_list[in_var] = {
                        'DIFF_ARRAY' : None,
                        'CHAIN_ARRAY' : None,
                        'COL_COUNT_LIST' : None,
                        'VAR_VALUE' : None,
                    }

                # 多次元変数構造比較用配列を退避
                ina_array_vars_list[in_var]['DIFF_ARRAY'] = diff_vars_list

                # 多次元変数親子関係のチェーン構造を退避
                ina_array_vars_list[in_var]['CHAIN_ARRAY'] = vars_last_chain_list

                # 配列階層の配列数を退避
                ina_array_vars_list[in_var]['COL_COUNT_LIST'] = array_col_count_list

                # 各変数の具体値を退避
                ina_array_vars_list[in_var]['VAR_VALUE'] = varval_list

        return True, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line

    def MakeMultiArrayToDiffMultiArray(
        self,
        ina_parent_var_array, ina_vars_list, ina_varval_list, in_var_name_path,
        ina_array_col_count_list, in_col_index_str,
        in_error_code, in_line,
        in_col_count, in_assign_count
    ):

        """
        処理内容(再帰処理)
          YAMLパーサーから取得し配列構造にはメンバー変数の具体値が含まれているので、
          具体値を取り除き配列数が1の配列構造(ina_vars_list)を作成する。
          各メンバー変数の具体値をina_varval_listに退避する。
          各配列階層の配列数退避をina_array_col_count_listに退避する。
        パラメータ
          ina_parent_var_array:       YAMLパーサーから取得し配列構造
          ina_vars_list:              具体値を取り除き配列数が1の配列構造退避
          ina_varval_list:            各メンバー変数の具体値退避
          in_var_name_path:           1つ前の階層までのメンバー変数のパス
          ina_array_col_count_list:   配列階層の配列数退避
          in_col_index_str:           各メンバー変数が属している配列の位置(1配列毎に3桁で位置を表した文字列)
          in_error_code:              エラー時のエラーコード
          in_line:                    エラー時の行番号格納
          in_col_count:               現在未使用
          in_assign_count:            現在未使用

        戻り値
          true: 正常  false:異常
        """

        demiritta_ch = "."

        # 配列階層か判定
        array_f = self.is_assoc(ina_parent_var_array)
        if array_f == -1:
            # MSG-10301 = "変数定義の解析に失敗しました。{}"
            in_error_code = "MSG-10301"
            in_line = inspect.currentframe().f_lineno
            return False, ina_vars_list, ina_varval_list, ina_array_col_count_list, in_error_code, in_line, in_col_count, in_assign_count
        
        for var, val in self.php_array(ina_parent_var_array):
            # 多次元複数具体値の判定
            # VAR_list:
            #  -
            #    - val1
            #    - val2
            # [VAR_list] => Array
            #    (
            #        [0] => Array
            #            (
            #                [0] => val1
            #                [1] => val2
            #            )
            #    )
            if self.is_num(var):
                # 多次元複数具体値の判定
                ret = self.is_assoc(val)
                if ret == "I":
                    # MSG-10304 = "代入順序が複数必要な変数定義になっています。{}"
                    in_error_code = "MSG-10304"
                    in_line = inspect.currentframe().f_lineno
                    return False, ina_vars_list, ina_varval_list, ina_array_col_count_list, in_error_code, in_line, in_col_count, in_assign_count

                # 繰返構造の繰返数が99999999以上あった場合はエラーにする。
                # VAR_struct:
                #   - item1:
                #     item2:
                #     ・・・
                #   - item1:
                #     item2:
                #
                #    [VAR_struct] => Array
                #        (
                #            [0] => Array
                #                (
                #                    [item1] =>
                #                    [item2] => a1
                #                )
                #
                #            [99999999] => Array
                #                (
                #                    [item1] =>
                #                    [item2] => a2
                #                )
                if var >= 99999999:
                    # 繰返構造の繰返数が99999999以上あった
                    if array_f == "I":
                        # MSG-10444 = "繰返構造の繰返数が99999999を超えてた定義です。{}"
                        in_error_code = "MSG-10444"
                        in_line = inspect.currentframe().f_lineno
                        return False, ina_vars_list, ina_varval_list, ina_array_col_count_list, in_error_code, in_line, in_col_count, in_assign_count

            # 複数具体値か判定する
            if self.is_num(var):
                # 具体値がある場合は排除する
                if type(val) not in (dict, list):
                    if in_var_name_path not in ina_varval_list:
                        ina_varval_list[in_var_name_path] = {}

                    if 1 not in ina_varval_list[in_var_name_path]:
                        ina_varval_list[in_var_name_path][1] = {}

                    if in_col_index_str not in ina_varval_list[in_var_name_path][1]:
                        ina_varval_list[in_var_name_path][1][in_col_index_str] = {}

                    if var + 1 not in ina_varval_list[in_var_name_path][1][in_col_index_str]:
                        ina_varval_list[in_var_name_path][1][in_col_index_str][var + 1] = None

                    # 代入順序を1オリジンにする
                    ina_varval_list[in_var_name_path][1][in_col_index_str][var + 1] = val
                    continue

            # 配列階層か判定
            if array_f == 'I':
                # 配列階層の列番号を退避 各配列の位置を8桁の数値文字列で結合していく
                wk_col_index_str = '%s%08d' % (in_col_index_str, var)

                # 配列階層の場合の変数名を設定 変数名を0に設定する
                if not in_var_name_path:
                    wk_var_name_path = '0'

                else:
                    wk_var_name_path = '%s%s0' % (in_var_name_path, demiritta_ch)

                if wk_var_name_path not in ina_array_col_count_list \
                or ina_array_col_count_list[wk_var_name_path] is None \
                or (type(ina_array_col_count_list[wk_var_name_path]) in (list, dict) and len(ina_array_col_count_list[wk_var_name_path]) <= 0):
                    # 配列階層の配列数を退避
                    ina_array_col_count_list[wk_var_name_path] = len(ina_parent_var_array)

            else:
                # 配列階層の列番号を退避
                wk_col_index_str = in_col_index_str

                # 配列階層の以外の場合の変数名を設定
                if not in_var_name_path:
                    wk_var_name_path = var

                else:
                    wk_var_name_path = '%s%s%s' % (in_var_name_path, demiritta_ch, var)

            ina_vars_list[var] = {}
            # Key-Value変数か判定
            if type(val) not in (dict, list):
                if wk_var_name_path not in ina_varval_list:
                    ina_varval_list[wk_var_name_path] = {0:{}}

                if wk_col_index_str not in ina_varval_list[wk_var_name_path][0]:
                    ina_varval_list[wk_var_name_path][0][wk_col_index_str] = None

                # 具体値がある場合は排除する
                ina_varval_list[wk_var_name_path][0][wk_col_index_str] = val
                continue

            ret, ina_vars_list[var], ina_varval_list, ina_array_col_count_list, in_error_code, in_line, in_col_count, in_assign_count = self.MakeMultiArrayToDiffMultiArray(
                val, ina_vars_list[var], ina_varval_list, wk_var_name_path, ina_array_col_count_list,
                wk_col_index_str, in_error_code, in_line, in_col_count, in_assign_count
            )
            if not ret:
                return False, ina_vars_list, ina_varval_list, ina_array_col_count_list, in_error_code, in_line, in_col_count, in_assign_count

        return True, ina_vars_list, ina_varval_list, ina_array_col_count_list, in_error_code, in_line, in_col_count, in_assign_count

    def MultiArrayDiff(self, in_arrrayLeft, in_arrayRight, in_diff_array):

        """
        処理内容(再帰処理)
          指定された配列の構造が一致しているか判定
          左辺の内容が右辺に含まれているか
          同一かどうかは左右入れ替えて確認する
        パラメータ
          in_arrrayLeft:       左辺の配列構造
          in_arrayRight:       右辺の配列構造
          in_diff_array:       一致していない場合の簡易エラー情報

        戻り値
          true: 正常  false:異常
        """

        if type(in_arrrayLeft) in (dict, list):
            for key, item in self.php_array(in_arrrayLeft):
                if key not in in_arrayRight or type(in_arrayRight[key]) not in (dict, list):
                    in_diff_array[key] = "key is not found"
                    return False, in_diff_array

                # 配列なら再帰呼び出し
                if type(item) in (list, dict):
                    ret, in_diff_array = self.MultiArrayDiff(item, in_arrayRight[key], in_diff_array)
                    if ret is False:
                        return False, in_diff_array

                else:
                    in_diff_array[key] = "item is not array"
                    return False, in_diff_array

        else:
            in_diff_array["arrrayLeft"] = "arrrayLeft is not array"
            return False, in_diff_array

        return True, in_diff_array

    def InnerArrayDiff(self, ina_parent_var_array, in_error_code, in_line):

        """
        処理内容(再帰処理)
          多次元変数で配列構造を含んでいる場合、各配列の定義が一致しているか判定
        パラメータ
          ina_parent_var_array:       多次元変数の構造
          in_error_code:              エラー時のエラーコード
          in_line:                    エラー時の行番号格納

        戻り値
          true: 正常  false:異常
        """

        diff_array = []
        if type(ina_parent_var_array) not in (dict, list):
            return True, in_error_code, in_line

        is_key_array = self.is_assoc(ina_parent_var_array)
        if is_key_array == -1:
            # MSG-10301 = "変数定義の解析に失敗しました。{}"
            in_error_code = "MSG-10301"
            in_line = inspect.currentframe().f_lineno
            return False, in_error_code, in_line

        idx = 0
        for var1, val1 in self.php_array(ina_parent_var_array):
            if self.is_num(var1):
                if type(val1) in (dict, list):
                    if idx != 0:
                        diff_array = {}
                        ret, diff_array = self.MultiArrayDiff(self.get_array_data(ina_parent_var_array, 0), self.get_array_data(ina_parent_var_array, idx), diff_array)
                        if not ret:
                            # ary[70089] = "繰返階層の変数定義が一致していません。{}"
                            in_error_code = "MSG-10303"
                            in_line = inspect.currentframe().f_lineno
                            return False, in_error_code, in_line

                        ret, diff_array = self.MultiArrayDiff(self.get_array_data(ina_parent_var_array, idx), self.get_array_data(ina_parent_var_array, 0), diff_array)
                        if not ret:
                            # ary[70089] = "繰返階層の変数定義が一致していません。{}"
                            in_error_code = "MSG-10303"
                            in_line = inspect.currentframe().f_lineno
                            return False, in_error_code, in_line

            ret, in_error_code, in_line = self.InnerArrayDiff(val1, in_error_code, in_line)
            if not ret:
                return False, in_error_code, in_line

            idx = idx + 1

        return True, in_error_code, in_line

    def get_array_data(self, php_array, idx):

        """
        処理内容
            PHP処理の流用対応

        パラメータ
            php_array:                  なんらかの配列/連想配列
            idx:                        取得したいインデックス

        戻り値
            配列の値
        """

        if type(php_array) is dict:
            result = None
            try:
                result = php_array[str(idx)]
            except KeyError:
                try:
                    result = php_array[idx]
                except KeyError:
                    raise AppException("MSG-40004", [], [])

            return result

        if type(php_array) is list:
            return php_array[idx]

        raise AppException("MSG-40004", [], [])

    def is_assoc(self, in_array):

        """
        処理内容
          多次元変数の特定階層が配列か判定する。
        パラメータ
           in_array:                   多次元変数の特定階層

        戻り値
          -1: 配列でない
          C:  string  (具体値)
          I:  数値    (繰返し)
        """

        key_int = False
        key_char = False

        if type(in_array) not in (list, dict):
            return -1

        keys = self.php_keys(in_array)
        for i, value in enumerate(keys):
            if isinstance(value, int) is False:
                key_char = True

            else:
                key_int = True

        if key_char is True and key_int is True:
            return -1

        if key_char is True:
            return "C"

        return "I"

    def is_stroc(self, in_array):

        """
        処理内容
          多次元変数の特定階層がKey-Value形式か判定する。
        パラメータ
           in_array:                   多次元変数の特定階層

        戻り値
          true: 正常  false:異常
        """

        vals = self.php_vals(in_array)
        for value in vals:
            if isinstance(value, str) is False:
                return False

        return True

    def MakeMultiArrayToFirstVarChainArray(
        self,
        in_fastarry_f, in_var_name, in_var_name_path,
        ina_parent_var_array, ina_vars_chain_list,
        in_error_code, in_line, in_col_count, in_assign_count,
        ina_parent_var_key,
        in_chl_var_key, in_nest_lvl
    ):

        """
        処理内容
          多次元変数の構造を解析。ina_vars_chain_listに解析データを退避する。
        パラメータ
          in_fastarry_f:              配列定義内かを判定
          in_var_name:                1つ前の階層のメンバー変数
          in_var_name_path:           1つ前の階層のメンバー変数のパス
          ina_parent_var_array:       多次元変数の階層構造
          ina_vars_chain_list:        多次元変数の解析データ格納
          in_error_code:              エラー時のエラーコード
          in_line:                    エラー時の行番号格納
          in_col_count:               未使用
          in_assign_count:            未使用
          ina_parent_var_key:         1つ前の階層のメンバー変数のID（0～）
          in_chl_var_key:             同一階層の1つ前のメンバー変数のID（0～）
          in_nest_lvl:                階層レベル（1～）

        戻り値
          true: 正常  false:異常
        """

        demiritta_ch = "."
        in_nest_lvl = in_nest_lvl + 1
        parent_var_key = ina_parent_var_key
        ret = self.is_assoc(ina_parent_var_array)
        if ret == -1:
            # MSG-10301 = "変数定義の解析に失敗しました。{}"
            in_error_code = "MSG-10301"
            in_line = inspect.currentframe().f_lineno
            return False, ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count, in_chl_var_key

        fastarry_f_on = False
        for var, val in self.php_array(ina_parent_var_array):
            col_array_f = ""

            # 複数具体値の場合
            if self.is_num(var):
                if type(val) not in (dict, list):
                    continue

                else:
                    col_array_f = "I"

            MultiValueVar_f = self.chkMultiValueVariableSub(val)
            if len(str(in_var_name)) > 0:
                wk_var_name_path = '%s%s%s' % (in_var_name_path, demiritta_ch, var)
                if self.is_num(var) is False:
                    wk_var_name = '%s%s%s' % (in_var_name, demiritta_ch, var)

                else:
                    wk_var_name = in_var_name

            else:
                wk_var_name_path = var
                wk_var_name = var

            # 配列の開始かを判定する
            if col_array_f == "I":
                if in_fastarry_f is False:
                    in_fastarry_f = True
                    fastarry_f_on = True

            in_chl_var_key = in_chl_var_key + 1
            if parent_var_key not in ina_vars_chain_list:
                ina_vars_chain_list[parent_var_key] = {}

            if in_chl_var_key not in ina_vars_chain_list[parent_var_key]:
                ina_vars_chain_list[parent_var_key][in_chl_var_key] = {
                    'VAR_NAME' : None,
                    'NEST_LEVEL' : None,
                    'LIST_STYLE' : None,
                    'VAR_NAME_PATH' : None,
                    'VAR_NAME_ALIAS' : None,
                    'ARRAY_STYLE' : None,
                }

            ina_vars_chain_list[parent_var_key][in_chl_var_key]['VAR_NAME'] = var
            ina_vars_chain_list[parent_var_key][in_chl_var_key]['NEST_LEVEL'] = in_nest_lvl
            ina_vars_chain_list[parent_var_key][in_chl_var_key]['LIST_STYLE'] = "0"
            ina_vars_chain_list[parent_var_key][in_chl_var_key]['VAR_NAME_PATH'] = wk_var_name_path
            ina_vars_chain_list[parent_var_key][in_chl_var_key]['VAR_NAME_ALIAS'] = wk_var_name
            ina_vars_chain_list[parent_var_key][in_chl_var_key]['ARRAY_STYLE'] = "0"
            MultiValueVar_f = self.chkMultiValueVariableSub(val)
            if MultiValueVar_f is True:
                ina_vars_chain_list[parent_var_key][in_chl_var_key]['LIST_STYLE'] = "5"

            # 配列の中の変数の場合
            if in_fastarry_f is True:
                ina_vars_chain_list[parent_var_key][in_chl_var_key]['ARRAY_STYLE'] = "1"

            if type(val) not in (dict, list):
                continue

            ret, ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count, in_chl_var_key = self.MakeMultiArrayToFirstVarChainArray(
                in_fastarry_f,
                wk_var_name,
                wk_var_name_path,
                val,
                ina_vars_chain_list,
                in_error_code,
                in_line,
                in_col_count,
                in_assign_count,
                in_chl_var_key,
                in_chl_var_key,
                in_nest_lvl
            )

            if not ret:
                return False, ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count, in_chl_var_key

            # 配列開始のマークを外す
            if fastarry_f_on is True:
                in_fastarry_f = False

            if self.is_num(var):
                if var == 0:
                    break
            
        return True, ina_vars_chain_list, in_error_code, in_line, in_col_count, in_assign_count, in_chl_var_key

    def MakeMultiArrayToLastVarChainArray(
        self,
        ina_first_vars_chain_list, array_col_count_list, ina_vars_chain_list, in_error_code, in_line
    ):

        """
        処理内容
          多次元変数の各メンバー構造で代入値管理系で列順序と代入順序が必要となる変数をマークする。
          配列の場合に配列数を設定する。
        パラメータ
          ina_first_vars_chain_list:
          array_col_count_list:
          ina_vars_chain_list:
          in_error_code:              エラー時のエラーコード
          in_line:                    エラー時の行番号格納

        戻り値
          true: 正常  false:異常
        """

        # 代入値管理系で列順序になる変数の候補にマークする。と代入順序が必要な変数を設定する
        ina_vars_chain_list = []
        for parent_vars_key_id, chl_vars_list in self.php_array(ina_first_vars_chain_list):
            for vars_key_id, vars_info in self.php_array(chl_vars_list):
                info_array = {}
                info_array['PARENT_VARS_KEY_ID'] = parent_vars_key_id
                info_array['VARS_KEY_ID'] = vars_key_id
                info_array['VARS_NAME'] = vars_info['VAR_NAME']
                info_array['ARRAY_NEST_LEVEL'] = vars_info['NEST_LEVEL']

                # 複数具体値なので代入順序が必要なのでマークする
                if str(vars_info['LIST_STYLE']) != "0":
                    info_array['ASSIGN_SEQ_NEED'] = "1"

                else:
                    info_array['ASSIGN_SEQ_NEED'] = "0"

                # 配列変数より下の階層にある変数なので列順序になる変数の候補にマークする
                if str(vars_info['ARRAY_STYLE']) != "0":
                    info_array['COL_SEQ_MEMBER'] = "1"

                else:
                    info_array['COL_SEQ_MEMBER'] = "0"

                info_array['COL_SEQ_NEED'] = "0"
                info_array['MEMBER_DISP'] = "0"
                info_array['VRAS_NAME_PATH'] = vars_info['VAR_NAME_PATH']
                info_array['VRAS_NAME_ALIAS'] = vars_info['VAR_NAME_ALIAS']

                # 配列階層(変数名が0)の場合に配列数を設定する
                if str(info_array['VARS_NAME']) == "0":
                    if str(info_array['VRAS_NAME_PATH']) not in array_col_count_list \
                    or array_col_count_list[str(info_array['VRAS_NAME_PATH'])] is None \
                    or (
                        type(array_col_count_list[str(info_array['VRAS_NAME_PATH'])]) in (list, dict)
                        and len(array_col_count_list[str(info_array['VRAS_NAME_PATH'])]) <= 0
                    ):
                        # MSG-10301 = "変数定義の解析に失敗しました。{}"
                        in_error_code = "MSG-10301"
                        in_line = inspect.currentframe().f_lineno
                        return False, ina_vars_chain_list, in_error_code, in_line

                    else:
                        info_array['MAX_COL_SEQ'] = array_col_count_list[str(info_array['VRAS_NAME_PATH'])]

                else:
                    info_array['MAX_COL_SEQ'] = "0"

                ina_vars_chain_list.append(info_array)
        
        # 代入値管理系で表示する変数をマークする。列順序が必要な変数をマークする
        row_count = len(ina_vars_chain_list)
        var_key_list = []
        for idx in range(row_count):
            var_key_list.append(ina_vars_chain_list[idx]['VARS_KEY_ID'])

        # 自分より下の階層がない変数を表示対象にする
        for key_idx in range(len(var_key_list)):
            hit = False
            for idx in range(row_count):
                # 自分より下の階層がある
                if var_key_list[key_idx] == ina_vars_chain_list[idx]['PARENT_VARS_KEY_ID']:
                    hit = True
                    break

            # 自分より下の階層がなかった
            if hit is False:
                # 代入値管理系に表示する変数なのでマークする
                ina_vars_chain_list[key_idx]['MEMBER_DISP'] = "1"

                # 代入値管理系で列順序が必要なのでマークする
                if ina_vars_chain_list[key_idx]['COL_SEQ_MEMBER'] == "1":
                    ina_vars_chain_list[key_idx]['COL_SEQ_NEED'] = "1"

        return True, ina_vars_chain_list, in_error_code, in_line

    def chkDefVarsListPlayBookGlobalVarsList(self, ina_play_global_vars_list, ina_global_vars_list, in_errmsg):

        """
        処理内容
          ロールパッケージ内のPlaybookで定義されているグローバル変数が
          グローバル変数管理で定義されているか判定

        パラメータ
          ina_play_global_vars_list:     ロールパッケージ内のPlaybookで定義している変数リスト
                                          [role名][変数名]=0
          ina_global_vars_list:          グローバル変数管理の変数リスト

        戻り値
          true:   正常
          false:  異常
        """

        in_errmsg = ""
        ret_code = True
        if ina_play_global_vars_list is None \
        or (type(ina_play_global_vars_list) in (list, dict) and len(ina_play_global_vars_list) <= 0):
            return ret_code, in_errmsg

        for role_name, vars_list in self.php_array(ina_play_global_vars_list):
            for vars_name, dummy in self.php_array(vars_list):
                if vars_name not in ina_global_vars_list:
                    in_errmsg = '%s\n%s' % (in_errmsg, g.appmsg.get_api_message("MSG-10465", [role_name, vars_name]))
                    ret_code = False

        return ret_code, in_errmsg

    def readTranslationFile(self, in_filepath, ina_ITA2User_var_list, ina_User2ITA_var_list, in_errmsg):

        """
        処理内容
          読替表より変数の情報を取得する。

        パラメータ
          in_filepath:            読替表ファイルパス
          ina_ITA2User_var_list:  読替表の変数リスト　ITA変数=>ユーザ変数
          ina_User2ITA_var_list:  読替表の変数リスト　ユーザ変数=>ITA変数
          in_errmsg:              エラーメッセージリスト

        戻り値
          true:   正常
          false:  異常
        """

        in_errmsg = ""
        ret_code = True
        dataString = pathlib.Path(in_filepath).read_text()
        line = 0

        # 入力データを行単位に分解
        arry_list = dataString.split('\n')
        for strSourceString in arry_list:
            line = line + 1

            # コメント行は読み飛ばす
            if strSourceString.startswith('#'):
                continue

            # 空行を読み飛ばす
            if len(strSourceString.strip()) <= 0:
                continue

            # 読替変数の構文を確認
            # LCA_[0-9,a-Z_*]($s*):($s+)playbook内で使用している変数名
            # 読替変数名の構文判定
            #ita_var_match = re.findall(r'^(\s*)LCA_[a-zA-Z0-9_]*(\s*):(\s+)', strSourceString)
            ita_var_match = re.findall(r'^\s*LCA_[a-zA-Z0-9_]*\s*:\s+', strSourceString)
            if len(ita_var_match) == 1:
                # :を取除き、読替変数名取得
                ita_var_name = ita_var_match[0].replace(':', '').strip()

                # 任意変数を取得
                #user_var_name = (re.sub(r'^(\s*)LCA_[a-zA-Z0-9_]*(\s*):(\s+)', '', strSourceString)).strip()
                user_var_name = (re.sub(r'^\s*LCA_[a-zA-Z0-9_]*\s*:\s+', '', strSourceString)).strip()
                if len(user_var_name) > 0:
                    # 任意変数がVAR_でないことを判定
                    user_var_match = re.findall(r'^VAR_', user_var_name)
                    if len(user_var_match) == 1:
                        in_errmsg = '%s\n%s' % (
                            in_errmsg,
                            g.appmsg.get_api_message("MSG-10514", [os.path.basename(in_filepath), line])
                        )
                        ret_code = False
                        continue

                else:
                    in_errmsg = '%s\n%s' % (
                        in_errmsg,
                        g.appmsg.get_api_message("MSG-10515", [os.path.basename(in_filepath), line])
                    )
                    ret_code = False
                    continue

            else:
                in_errmsg = '%s\n%s' % (in_errmsg, g.appmsg.get_api_message("MSG-10516", [os.path.basename(in_filepath), line]))
                ret_code = False
                continue
            
            # 任意変数が重複登録の二重登録判定
            if  user_var_name in ina_User2ITA_var_list \
            and ina_User2ITA_var_list[user_var_name] is not None \
            and (type(ina_User2ITA_var_list[user_var_name]) not in (list, dict)
                 or len(ina_User2ITA_var_list[user_var_name]) > 0
            ):
                in_errmsg = '%s\n%s' % (
                    in_errmsg,
                    g.appmsg.get_api_message("MSG-10517", [os.path.basename(in_filepath), user_var_name])
                )
                ret_code = False
                continue

            else:
                ina_User2ITA_var_list[user_var_name] = ita_var_name

            # 読替変数が重複登録の二重登録判定
            if  ita_var_name in ina_ITA2User_var_list \
            and ina_ITA2User_var_list[ita_var_name] is not None \
            and (type(ina_ITA2User_var_list[ita_var_name]) not in (list, dict)
                 or len(ina_ITA2User_var_list[ita_var_name]) > 0
            ):
                in_errmsg = '%s\n%s' % (
                    in_errmsg,
                    g.appmsg.get_api_message("MSG-10518", [os.path.basename(in_filepath), ita_var_name])
                )
                ret_code = False
                continue

            else:
                ina_ITA2User_var_list[ita_var_name] = user_var_name

        return ret_code, ina_ITA2User_var_list, ina_User2ITA_var_list, in_errmsg

    def chkTranslationTableVarsCombination(self, ina_ITA2User_var_list, ina_User2ITA_var_list, ina_comb_err_vars_list):

        """
        処理内容
          読替表に定義されている読替変数と任意変数の組合せが一意か判定

        パラメータ
          ina_ITA2User_var_list:   読替表の変数リスト  ITA変数=>ユーザ変数
          ina_User2ITA_var_list:   読替表の変数リスト  ユーザ変数=>ITA変数
          ina_comb_err_vars_list:  ロールパッケージ内で使用している変数で構造が違う変数のリスト

        戻り値
          true:   正常
          false:  異常
        """

        ret_code = True
        ina_comb_err_vars_list = {}

        # 読替変数と任意変数の組合せが一意か確認する
        # 読替変数をキーに読替変数と任意変数の組合せを確認
        for pkg_name, role_list in self.php_array(ina_ITA2User_var_list):
            for role_name, vars_list in self.php_array(role_list):
                for ita_vars_name, user_vars_name in self.php_array(vars_list):
                    for chk_pkg_name, chk_role_list in self.php_array(ina_ITA2User_var_list):
                        for chk_role_name, chk_vars_list in self.php_array(chk_role_list):
                            # 同一ロールパッケージ+ロールのチェックはスキップする
                            if pkg_name == chk_pkg_name and role_name == chk_role_name:
                                # 同一のロール内のチェックはスキップする
                                continue

                            for chk_ita_vars_name, chk_user_vars_name in self.php_array(chk_vars_list):
                                if ita_vars_name == chk_ita_vars_name and user_vars_name != chk_user_vars_name:
                                    # エラーになった変数とロールを退避
                                    if 'USER_VAR' not in ina_comb_err_vars_list:
                                        ina_comb_err_vars_list['USER_VAR'] = {}

                                    if ita_vars_name not in ina_comb_err_vars_list['USER_VAR']:
                                        ina_comb_err_vars_list['USER_VAR'][ita_vars_name] = {}

                                    if pkg_name not in ina_comb_err_vars_list['USER_VAR'][ita_vars_name]:
                                        ina_comb_err_vars_list['USER_VAR'][ita_vars_name][pkg_name] = {}

                                    if chk_pkg_name not in ina_comb_err_vars_list['USER_VAR'][ita_vars_name]:
                                        ina_comb_err_vars_list['USER_VAR'][ita_vars_name][chk_pkg_name] = {}

                                    if role_name not in ina_comb_err_vars_list['USER_VAR'][ita_vars_name][pkg_name]:
                                        ina_comb_err_vars_list['USER_VAR'][ita_vars_name][pkg_name][role_name] = None

                                    if chk_role_name not in ina_comb_err_vars_list['USER_VAR'][ita_vars_name][chk_pkg_name]:
                                        ina_comb_err_vars_list['USER_VAR'][ita_vars_name][chk_pkg_name][chk_role_name] = None

                                    ina_comb_err_vars_list['USER_VAR'][ita_vars_name][pkg_name][role_name] = user_vars_name
                                    ina_comb_err_vars_list['USER_VAR'][ita_vars_name][chk_pkg_name][chk_role_name] = chk_user_vars_name
                                    ret_code = False

                                # 読替変数が同じ場合は、以降のチェックをスキップ
                                if ita_vars_name == chk_ita_vars_name:
                                    break

        # 任意変数をキーに読替変数と任意変数の組合せを確認
        for pkg_name, role_list in self.php_array(ina_User2ITA_var_list):
            for role_name, vars_list in self.php_array(role_list):
                for user_vars_name, ita_vars_name in self.php_array(vars_list):
                    for chk_pkg_name, chk_role_list in self.php_array(ina_User2ITA_var_list):
                        for chk_role_name, chk_vars_list in self.php_array(chk_role_list):
                            # 同一ロールパッケージ+ロールのチェックはスキップする
                            if pkg_name == chk_pkg_name and role_name == chk_role_name:
                                # 同一のロール内のチェックはスキップする
                                continue

                            for chk_user_vars_name, chk_ita_vars_name in self.php_array(chk_vars_list):
                                if user_vars_name == chk_user_vars_name and ita_vars_name != chk_ita_vars_name:
                                    # エラーになった変数とロールを退避
                                    if 'ITA_VAR' not in ina_comb_err_vars_list:
                                        ina_comb_err_vars_list['ITA_VAR'] = {}

                                    if user_vars_name not in ina_comb_err_vars_list['ITA_VAR']:
                                        ina_comb_err_vars_list['ITA_VAR'][user_vars_name] = {}

                                    if pkg_name not in ina_comb_err_vars_list['ITA_VAR'][user_vars_name]:
                                        ina_comb_err_vars_list['ITA_VAR'][user_vars_name][pkg_name] = {}

                                    if chk_pkg_name not in ina_comb_err_vars_list['ITA_VAR'][user_vars_name]:
                                        ina_comb_err_vars_list['ITA_VAR'][user_vars_name][chk_pkg_name] = {}

                                    if role_name not in ina_comb_err_vars_list['ITA_VAR'][user_vars_name][pkg_name]:
                                        ina_comb_err_vars_list['ITA_VAR'][user_vars_name][pkg_name][role_name] = None

                                    if chk_role_name not in ina_comb_err_vars_list['ITA_VAR'][user_vars_name][chk_pkg_name]:
                                        ina_comb_err_vars_list['ITA_VAR'][user_vars_name][chk_pkg_name][chk_role_name] = None

                                    ina_comb_err_vars_list['ITA_VAR'][user_vars_name][pkg_name][role_name] = ita_vars_name
                                    ina_comb_err_vars_list['ITA_VAR'][user_vars_name][chk_pkg_name][chk_role_name] = chk_ita_vars_name
                                    ret_code = False

                                # 読替変数が同じ場合は、以降のチェックをスキップ
                                if user_vars_name == chk_user_vars_name:
                                    break

        return ret_code, ina_comb_err_vars_list

    def TranslationTableCombinationErrmsgEdit(self, in_pkg_flg, ina_comb_err_vars_list):

        """
        処理内容
          読替表の読替変数と任意変数の組合せが一致していないエラーメッセージを編集

        パラメータ
          in_pkg_flg:             パッケージ名表示有無
          ina_comb_err_vars_list: ロールパッケージ内で使用している変数で構造が違う変数のリスト
                                  array(2) {
                                     ["USER_VAR"]=>
                                       array(1) {
                                         ["LCA_sample_02"]=>
                                         array(1) {
                                           ["dummy pkg"]=>
                                           array(2) {
                                             ["ITAOrigVar"]=>
                                             string(14) "user_sample_02"
                                             ["test"]=>
                                             string(14) "user_sample_05"
                                       } } }
                                       ["ITA_VAR"]=>
                                       array(1) {
                                         ["user_sample_03"]=>
                                         array(1) {
                                           ["dummy pkg"]=>
                                           array(2) {
                                             ["ITAOrigVar"]=>
                                             string(13) "LCA_sample_03"
                                             ["test"]=>
                                             string(13) "LCA_sample_04"
                                     } } } }

        戻り値
          エラーメッセージ
        """

        errmsg = ""
        errmsg = g.appmsg.get_api_message("MSG-10520")

        if  "USER_VAR" in ina_comb_err_vars_list \
        and ina_comb_err_vars_list["USER_VAR"] is not None \
        and (
            type(ina_comb_err_vars_list["USER_VAR"]) not in (list, dict)
            or len(ina_comb_err_vars_list["USER_VAR"]) > 0
        ):
            for ita_vars_name, pkg_list in self.php_array(ina_comb_err_vars_list["USER_VAR"]):
                for pkg_name, role_list in self.php_array(pkg_list):
                    for role_name, user_vars_name in self.php_array(role_list):
                        if in_pkg_flg is True:
                            errmsg = '%s%s' % (
                                errmsg,
                                g.appmsg.get_api_message("MSG-10523", [pkg_name, role_name, ita_vars_name, user_vars_name])
                            )

                        else:
                            errmsg = '%s%s' % (
                                errmsg,
                                g.appmsg.get_api_message("MSG-10521", [role_name, ita_vars_name, user_vars_name])
                            )

        if  "ITA_VAR" in ina_comb_err_vars_list \
        and ina_comb_err_vars_list["ITA_VAR"] is not None \
        and (
            type(ina_comb_err_vars_list["ITA_VAR"]) not in (list, dict) \
            or len(ina_comb_err_vars_list["ITA_VAR"]) > 0
        ):
            for user_vars_name, pkg_list in self.php_array(ina_comb_err_vars_list["ITA_VAR"]):
                for pkg_name, role_list in self.php_array(pkg_list):
                    for role_name, ita_vars_name in self.php_array(role_list):
                        if in_pkg_flg is True:
                            errmsg = '%s%s' % (
                                errmsg,
                                g.appmsg.get_api_message("MSG-10524", [pkg_name, role_name, user_vars_name, ita_vars_name])
                            )

                        else:
                            errmsg = '%s%s' % (
                                errmsg,
                                g.appmsg.get_api_message("MSG-10522", [role_name, user_vars_name, ita_vars_name])
                            )

        return errmsg

    def ApplyTranslationTable(self, ina_vars_list, ina_User2ITA_var_list):

        """
        処理内容
          ロールパッケージから抜出した変数名を読替表の情報を置換える。
          任意変数=>読替変数

        パラメータ
          ina_vars_list: ロールパッケージから抜出した変数情報
                         [ロール名][変数名].....
          ina_User2ITA_var_list  読替表の変数リスト　ユーザ変数=>ITA変数

        戻り値
          エラーメッセージ
        """

        wk_ina_vars_list = {}
        for role_name, var_list in self.php_array(ina_vars_list):
            for vars_name, info_list in self.php_array(var_list):
                if role_name not in ina_User2ITA_var_list or vars_name not in ina_User2ITA_var_list[role_name] \
                or ina_User2ITA_var_list[role_name][vars_name] is None \
                or (type(ina_User2ITA_var_list[role_name][vars_name]) in (dict, list) and len(ina_User2ITA_var_list[role_name][vars_name]) <= 0):
                    if role_name not in wk_ina_vars_list:
                        wk_ina_vars_list[role_name] = {}

                    if vars_name not in wk_ina_vars_list[role_name]:
                        wk_ina_vars_list[role_name][vars_name] = None

                    wk_ina_vars_list[role_name][vars_name] = info_list
                    continue

                ita_vars_name = ina_User2ITA_var_list[role_name][vars_name]
                if role_name not in wk_ina_vars_list:
                    wk_ina_vars_list[role_name] = {}

                if ita_vars_name not in wk_ina_vars_list[role_name]:
                    wk_ina_vars_list[role_name][ita_vars_name] = None

                wk_ina_vars_list[role_name][ita_vars_name] = info_list

        ina_vars_list = {}
        ina_vars_list = wk_ina_vars_list

        return ina_vars_list

    def SetRunModeVarFile(self, mode):

        """
        処理内容
          テンプレートの変数定義かロールパッケージのdefault定義ファイルかを判別

        パラメータ
          run_mode:  モード
                     LC_RUN_MODE_VARFILE: テンプレートの変数定義
                     LC_RUN_MODE_STD:     ロールパッケージのdefault定義ファイル

        戻り値
          なし
        """

        self.lv_run_mode = mode

    def GetRunModeVarFile(self):

        """
        処理内容
          処理モード取得

        パラメータ
          なし

        戻り値
          なし
        """

        return self.lv_run_mode

    def setVariableDefineLocation(self, id):

        """
        処理内容
          VarPosAnalysisで変数定義を解析する元データの種別を設定する
          (テンプレート変数の変数定義、default変数定義,ITA-radme)
       
        パラメータ
          種別
          DF_DEF_VARS:    default変数定義
          DF_TEMP_VARS:   テンプレート変数の変数定義
          DF_README_VARS: ITA-Readme
        戻り値
          なし
        """

        self.lv_setVariableDefineLocation = id

    def getVariableDefineLocation(self):

        """
        処理内容
          VarPosAnalysisで変数定義を解析する元データの種別を取得する。
          (テンプレート変数の変数定義、default変数定義,ITA-radme)

        パラメータ
          なし
        戻り値
          種別
          DF_DEF_VARS:    default変数定義
          DF_TEMP_VARS:   テンプレート変数の変数定義
          DF_README_VARS: ITA-Readme
        """

        return self.lv_setVariableDefineLocation

    def FirstAnalysis(
        self,
        yaml_parse_array,
        role_pkg_name, role_name, file_name,
        ina_ITA2User_var_list, ina_User2ITA_var_list,
        parent_vars_list, out_errmsg, in_f_name, in_f_line
    ):

        """
        処理内容
          YAMLパーサーでパースした変数構造を親変数毎に分解し、親変数名の妥当性を判定

                parent_vars_list[ParentVarName] = array('VAR_NAME'=>ParentVarName,
                                                        'VAR_TYPE'=>var_type,
                                                        'VAR_STRUCT'=>VarStruct);
        パラメータ
          in_string:              YAMLパーサーでパースした変数構造
          ina_parent_vars_list:   親変数毎に分解されたYAMLパーサーでパースした変数構造
                                  [親変数名]['VAR_NAME']  親変数名
                                            ['VAR_TYPE']  変数タイプ
                                                          self::LC_VAR_TYPE_ITA / self::LC_VAR_TYPE_USER / self::LC_VAR_TYPE_USER_ITA
                                            [VAR_STRUCT]  YAMLパーサーでパースした変数構造
          in_role_name:           ロール名
          in_file_name:           defalte変数ファイル名
          ina_ITA2User_var_list   読替表の変数リスト　ITA変数=>ユーザ変数
          ina_User2ITA_var_list   読替表の変数リスト　ユーザ変数=>ITA変数
          in_errmsg:              エラー時のメッセージ格納
          in_f_name:
          in_f_line:

        戻り値
          true:   正常
          false:  異常
        """
        # 変数定義で除外変数をチェックする為の前準備
        objdbca = DBConnectWs()
        chkobj = WrappedStringReplaceAdmin(objdbca)
        objdbca.db_disconnect()
        # テンプレート管理の変数定義で除外変数チェックでGBL変数を除外対象外に設定
        if self.GetRunModeVarFile() == AnscConst.LC_RUN_MODE_VARFILE:
            local_vars = [AnscConst.ITA_SP_VAR_GBL_VAR_NAME]
        else:
            local_vars = []

        in_f_name = os.path.basename(inspect.currentframe().f_code.co_filename)
        out_errmsg = ""
        parent_vars_list = {}
        Duplicat_list = {}
        if type(yaml_parse_array) not in (list, dict):
            # MSG-10302 = "変数定義が想定外なので解析に失敗しました。{}";
            out_errmsg = AnsibleMakeMessage().AnsibleMakeMessage(
                self.GetRunModeVarFile(),
                "MSG-10302",
                [role_pkg_name, role_name, file_name]
            )
            in_f_line = inspect.currentframe().f_lineno
            return False, parent_vars_list, out_errmsg, in_f_name, in_f_line

        # 親変数名の妥当性を確認
        for ParentVarName, VarStruct in self.php_array(yaml_parse_array):
            ret, pattern = self.ParentVariableNamePattenMatch(ParentVarName)
            if not ret:
                # 変数名不正
                out_errmsg = AnsibleMakeMessage().AnsibleMakeMessage(
                    self.GetRunModeVarFile(),
                    "MSG-10306",
                    [role_pkg_name, role_name, file_name, ParentVarName]
                )
                in_f_line = inspect.currentframe().f_lineno
                return False, parent_vars_list, out_errmsg, in_f_name, in_f_line

            # 変数名の二重定義を確認
            if ParentVarName in Duplicat_list and Duplicat_list[ParentVarName] is not None:
                # パーサーを変更したことでデットルート
                out_errmsg = AnsibleMakeMessage().AnsibleMakeMessage(
                    self.GetRunModeVarFile(),
                    "MSG-10568",
                    [role_pkg_name, role_name, file_name, ParentVarName]
                )
                in_f_line = inspect.currentframe().f_lineno
                return False, parent_vars_list, out_errmsg, in_f_name, in_f_line

            Duplicat_list[ParentVarName] = 0

            # 変数のタイプがITAで扱う変数かを判定
            var_type = self.LC_VAR_TYPE_USER
            if pattern['type'] in [AnscConst.DF_VAR_TYPE_VAR, AnscConst.DF_VAR_TYPE_GBL]:
                # ITAで扱う変数
                var_type = self.LC_VAR_TYPE_ITA

            #elif pattern['type'] == "USER":  # ToDo DF_VAR_TYPE_USER
            #    # 読替表にある変数はITA変数として扱う
            #    if len(ina_User2ITA_var_list[ParentVarName]) > 0:
            #        # 読替変数
            #        var_type = self.LC_VAR_TYPE_USER_ITA

            #    else:
            #        # USER変数
            #        var_type = self.LC_VAR_TYPE_USER

            # 除外変数かチェック
            ret = chkobj.chkUnmanagedVarname(AnscConst.DF_HOST_VAR_HED,ParentVarName,local_vars)
            if ret is False:
                parent_vars_list[ParentVarName] = {
                    'VAR_NAME': ParentVarName,
                    'VAR_TYPE': var_type,
                    'VAR_STRUCT': VarStruct
                }

        return True, parent_vars_list, out_errmsg, in_f_name, in_f_line

    def LastAnalysis(
        self,
        ina_parent_vars_list, ina_vars_list, ina_varsval_list,
        ina_array_vars_list,
        in_role_name, in_file_name,
        in_errmsg, in_f_name, in_f_line,
        in_msg_role_pkg_name
    ):

        """
        処理内容
          YAMLパーサーから取得した配列構造を解析しITAで処理出来る構造に変換
        パラメータ
          ina_parent_vars_list:   親変数毎に分解されたYAMLパーサーでパースした変数構造
                                  [親変数名]['VAR_NAME']  親変数名
                                            ['VAR_TYPE']  変数タイプ
                                                          self::LC_VAR_TYPE_ITA / self::LC_VAR_TYPE_USER / self::LC_VAR_TYPE_USER_ITA
                                            [VAR_STRUCT]  YAMLパーサーでパースした変数構造
          ina_vars_list:              多段変数以外の変数の解析結果
          ina_varsval_list:           各変数の具体値格納
          ina_array_vars_list:        多段変数の解析結果
          in_role_name:               対象のロール名
          in_file_name:               対象のパッケージファイル名
          in_errmsg:                  エラー時のエラーメッセージ
          in_f_name:                  エラー時のファイル名
          in_f_line:                  エラー時の行番号
          in_msg_role_pkg_name:       ロールパッケージ名

        戻り値
          true: 正常  false:異常
        """

        ina_vars_list = {}
        ina_varsval_list = {}
        ina_array_vars_list = {}

        # 加工されたdefalte変数ファイルの情報を一時ファイルに出力
        for parent_var, parent_var_info in ina_parent_vars_list.items():
            var_array = {}
            var_array[parent_var] = parent_var_info['VAR_STRUCT']
            var_type = parent_var_info['VAR_TYPE']
            in_f_line = ""
            if isinstance(var_array, dict):
                if len(var_array) != 1:
                    in_f_line = inspect.currentframe().f_lineno

            else:
                in_f_line = inspect.currentframe().f_lineno

            if in_f_line != "":
                # MSG-10301 = "変数定義の解析に失敗しました。{}"
                in_errmsg = AnsibleMakeMessage().AnsibleMakeMessage(
                    self.GetRunModeVarFile(),
                    "MSG-10301",
                    [in_msg_role_pkg_name, in_role_name, in_file_name, parent_var]
                )
                in_f_line = inspect.currentframe().f_lineno
                return False, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line

            # 一般変数か判定
            ret, ina_vars_list, ina_varsval_list = self.chkStandardVariable(parent_var, var_array[parent_var], ina_vars_list, ina_varsval_list, var_type)
            if ret is True:
                continue

            # 複数具体値変数か判定
            ret, ina_vars_list, ina_varsval_list = self.chkMultiValueVariable(parent_var, var_array[parent_var], ina_vars_list, ina_varsval_list, var_type)
            if ret is True:
                continue

            # 多次元配列変数か判定　配列変数も多次元配列として扱う
            ret, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line = self.chkMultiArrayVariable(
                parent_var, var_array[parent_var], ina_vars_list, ina_varsval_list,
                var_type,
                parent_var,
                ina_array_vars_list,
                in_role_name, in_file_name,
                in_errmsg, in_f_name, in_f_line,
                in_msg_role_pkg_name
            )
            if ret is True:
                continue

            return False, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line

        # メンバー変数名に許容されていない文字が使用されていないか判定
        for parent_var, parent_var_info in ina_array_vars_list.items():
            if 'CHAIN_ARRAY' in parent_var_info and parent_var_info['CHAIN_ARRAY'] is not None:
                for member_vars_info in parent_var_info['CHAIN_ARRAY']:
                    member_var_name = str(member_vars_info['VARS_NAME'])
                    ret = self.MemberVariableNamePattenMatch(member_var_name)
                    if not ret:
                        # MSG-10309 = "メンバー変数名が不正です。メンバー変数名に 「 ．(ドット)  [  ] 」の3記号は使用できません。{}"
                        in_errmsg = AnsibleMakeMessage().AnsibleMakeMessage(
                            self.GetRunModeVarFile(),
                            "MSG-10309",
                            [in_msg_role_pkg_name, in_role_name, in_file_name, parent_var, member_var_name]
                        )
                        in_f_line = inspect.currentframe().f_lineno
                        return False, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line

            else:
                # MSG-10301 = "変数定義の解析に失敗しました。{}"
                in_errmsg = AnsibleMakeMessage().AnsibleMakeMessage(
                    self.GetRunModeVarFile(),
                    "MSG-10301",
                    [in_msg_role_pkg_name, in_role_name, in_file_name, parent_var]
                )
                in_f_line = inspect.currentframe().f_lineno
                return False, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line

        return True, ina_vars_list, ina_varsval_list, ina_array_vars_list, in_errmsg, in_f_name, in_f_line

    def ParentVariableNamePattenMatch(self, in_string):

        """
        処理内容
          親変数名の妥当性を判定する。

        パラメータ
          in_string: 変数名

        戻り値
          true:正常  false:異常
        """

        result_code = False
        match_pattern = ""
        DefineLocation = self.getVariableDefineLocation()
        for pattern in AnscConst.DF_VarName_pattenAry[DefineLocation]:
            match_pattern = pattern['pattern']
            if isinstance(in_string, int):
                in_string = str(in_string)

            ret = re.finditer(match_pattern, in_string)
            if len(list(ret)) == 0:
                continue

            else:
                result_code = pattern['parent']
                break

        return result_code, pattern

    def MemberVariableNamePattenMatch(self, in_string):

        """
        処理内容
          メンバー変数名の妥当性を判定する。
          メンバー変数で許容しない記号  . [ ]  合計3文字

        パラメータ
          in_string: 変数名

        戻り値
          true:正常  false:異常
        """

        # メンバー変数で許容しない記号  . [ ]  合計3文字
        fail_char_string = ".[]"
        for ch in fail_char_string:
            ret = in_string.find(ch)
            if ret >= 0:
                return False

            else:
                continue

        return True


#################################################################################
# 指定されたファイルの変数定義を解析する
#################################################################################
class YAMLFileAnalysis():

    """
    処理概要
      指定されたファイルの変数定義を解析する。
    """

    def __init__(self, in_objMTS):

        self.lv_objMTS = in_objMTS
        self.lv_lasterrmsg = []

        self.php_array = lambda x: x.items() if isinstance(x, dict) else enumerate(x)
        self.php_keys = lambda x: x.keys() if isinstance(x, dict) else range(len(x))
        self.php_vals = lambda x: x.values() if isinstance(x, dict) else x

    def SetLastError(self, p1, p2, p3):

        if len(self.lv_lasterrmsg) < 1:
            self.lv_lasterrmsg.append("")

        if len(self.lv_lasterrmsg) < 2:
            self.lv_lasterrmsg.append("")

        self.lv_lasterrmsg[0] = p3
        self.lv_lasterrmsg[1] = "FILE:%s LINE:%s %s" % (p1, p2, p3)

    def GetLastError(self):

        return self.lv_lasterrmsg

    def VarsFileAnalysis(
        self,
        in_mode, in_yaml_file,
        in_parent_vars_list, ina_vars_list, ina_array_vars_list, ina_varval_list,
        in_role_pkg_name, in_rolename, in_display_file_name, ina_ITA2User_var_list, ina_User2ITA_var_list
    ):

        # 対象ファイル名
        defvarfile = in_yaml_file

        # 対象ファイルから変数取得
        chkObj = DefaultVarsFileAnalysis(self.lv_objMTS)

        # テンプレートの変数定義ファイルか
        # ロールパッケージのdefault定義ファイルかを判別する設定
        chkObj.SetRunModeVarFile(in_mode)

        vars_list = []
        varsval_list = []
        array_vars_list = []

        parent_vars_list = []

        error_code = ""
        error_ary = []
        tgt_role_pkg_name = in_role_pkg_name  # ロールパッケージ名／テンプレート変数名
        tgt_role_name = in_rolename
        tgt_file_name = in_display_file_name

        # 変数定義の場所を設定
        if in_mode == AnscConst.LC_RUN_MODE_STD:
            # 変数定義の場所(Role default変数定義)を設定
            chkObj.setVariableDefineLocation(AnscConst.DF_DEF_VARS)

            # MSG-10644 = "ロールパッケージ内のYAML解析で想定外のエラーが発生しました。(ロールパッケージ名:{} role:{} file:{})"
            error_code = "MSG-10644"
            error_ary = [tgt_role_pkg_name, tgt_role_name, tgt_file_name]

        elif in_mode == AnscConst.LC_RUN_MODE_VARFILE:
            # 変数定義の場所(テンプレート管理  変数定義)を設定
            chkObj.setVariableDefineLocation(AnscConst.DF_TEMP_VARS)

            # MSG-10645 = "変数定義のYAML解析で想定外のエラーが発生しました。(テンプレート変数:{})"
            error_code = "MSG-10645"
            error_ary = [in_role_pkg_name]

        obj = YamlParse()
        yaml_parse_array = obj.Parse(defvarfile)
        errmsg = obj.GetLastError()
        obj = None

        if yaml_parse_array is None:
            yaml_parse_array = {}

        if yaml_parse_array is False:
            errmsg = "%s\n%s" % (errmsg, g.appmsg.get_api_message(error_code, error_ary))
            self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
            return False, in_parent_vars_list, ina_vars_list, ina_array_vars_list, ina_varval_list

        parent_vars_list = []
        errmsg = ""
        f_line = ""
        f_name = ""
        ret, parent_vars_list, errmsg, f_name, f_line = chkObj.FirstAnalysis(
            yaml_parse_array, tgt_role_pkg_name, tgt_role_name, tgt_file_name,
            ina_ITA2User_var_list, ina_User2ITA_var_list, parent_vars_list,
            errmsg, f_name, f_line
        )
        if not ret:
            errmsg = "%s(%s)" % (errmsg, f_line)
            self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
            return False, in_parent_vars_list, ina_vars_list, ina_array_vars_list, ina_varval_list

        vars_list = {}
        varsval_list = {}
        array_vars_list = {}
        errmsg = ""
        f_line = ""
        f_name = ""
        ret, vars_list, varsval_list, array_vars_list, errmsg, f_name, f_line = chkObj.LastAnalysis(
            parent_vars_list, vars_list, varsval_list, array_vars_list, tgt_role_name,
            in_display_file_name,  # rolesからしたの階層
            errmsg, f_name, f_line,
            in_role_pkg_name
        )
        if not ret:
            # 変数取得失敗
            errmsg = "%s(%s)" % (errmsg, f_line)
            self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, errmsg)
            return False, in_parent_vars_list, ina_vars_list, ina_array_vars_list, ina_varval_list

        # ファイルに定義されている変数(親)を取り出す
        in_parent_vars_list = parent_vars_list
        ina_vars_list = vars_list
        ina_array_vars_list = array_vars_list
        ina_varval_list = varsval_list

        return True, in_parent_vars_list, ina_vars_list, ina_array_vars_list, ina_varval_list


#################################################################################
# ロールパッケージ内の変数定義を解析。解析結果をファイルに保存
#################################################################################
class VarStructAnalysisFileAccess():

    """
    処理概要
      ロールパッケージ内の変数定義を解析。解析結果をファイルに保存
    """

    def __init__(self, in_objMTS, in_objDBCA, in_global_vars_master_list, in_template_master_list, in_log_level, master_non_reg_chk=True, vars_struct_anal_only=False, request=None):

        self.lv_objMTS = in_objMTS
        self.lv_ws_db = in_objDBCA
        self.lva_global_vars_master_list = in_global_vars_master_list
        self.lva_template_master_list = in_template_master_list
        self.log_level = in_log_level
        self.web_mode = False
        self.master_non_reg_chk = master_non_reg_chk
        self.vars_struct_anal_only = vars_struct_anal_only
        self.lv_lasterrmsg = []

        self.php_array = lambda x: x.items() if isinstance(x, dict) else enumerate(x)
        self.php_keys = lambda x: x.keys() if isinstance(x, dict) else range(len(x))
        self.php_vals = lambda x: x.values() if isinstance(x, dict) else x

        if request and has_request_context() and 'HTTP_HOST' in request:
            self.web_mode = True

    def SetLastError(self, p1, p2, p3):

        if len(self.lv_lasterrmsg) < 1:
            self.lv_lasterrmsg.append("")

        if len(self.lv_lasterrmsg) < 2:
            self.lv_lasterrmsg.append("")

        self.lv_lasterrmsg[0] = p3
        self.lv_lasterrmsg[1] = "FILE:%s LINE:%s %s" % (p1, p2, p3)

    def GetLastError(self):

        return self.lv_lasterrmsg

    def getVarStructAnalJsonStringFileInfo(self, json_data, vars_list, array_vars_list, tpf_vars_list, ITA2User_var_list, GBL_vars_list):

        obj = VarStructAnalJsonConv()
        retAry = obj.VarStructAnalJsonLoads(json_data)
        vars_list = retAry[0]
        array_vars_list = retAry[1]
        tpf_vars_list = retAry[2]
        ITA2User_var_list = retAry[3]
        GBL_vars_list = retAry[4]
        Role_name_list = retAry[5]

        return True, vars_list, array_vars_list, tpf_vars_list, ITA2User_var_list, GBL_vars_list

    def getRolePackageInfo(self, role_package_master_list):

        dbObj = AnsibleCommonLibs()
        ws_db = self.lv_ws_db
        if not ws_db:
            ws_db = DBConnectWs()

        ##############################################################################
        # ロールパッケージ管理の情報を取得
        ##############################################################################
        sql = (
            "SELECT                          \n"
            "    ROLE_PACKAGE_ID             \n"
            "   ,ROLE_PACKAGE_NAME           \n"
            "   ,ROLE_PACKAGE_FILE           \n"
            "   ,VAR_STRUCT_ANAL_JSON_STRING \n"
            "FROM                            \n"
            "    T_ANSR_MATL_COLL            \n"
            "WHERE                           \n"
            "    DISUSE_FLAG='0';            \n"
        )
        role_package_master_list = dbObj.select_db_recodes(sql, 'ROLE_PACKAGE_ID', ws_db)

        if not self.lv_ws_db and ws_db:
            ws_db.db_disconnect()
            ws_db = None

        return True, role_package_master_list

    def getVarEntryISTPFvars(self, role_package_name, role_name_list, tpf_vars_list, uuid, role_disuse_check=False):

        """
        処理内容
          代入値管理の具体値に登録されているテンプレート変数を取得

        パラメータ
          role_package_name:    ロールパッケージ名
          role_name_list:       ロール名リスト
          tpf_vars_list:        代入値管理の具体値に登録されているテンプレート変数リスト
          role_disuse_check:    ロールパッケージ・ロールが有効かりチェック有無
                                有:true  無:false
                                ロールパッケージ登録の場合は、true

        戻り値
          True:正常    False:異常
        """

        ws_db = self.lv_ws_db
        if not ws_db:
            ws_db = DBConnectWs()

        ################################################################
        # 代入値管理の具体値に登録されているテンプレート変数を取得
        ################################################################
        sqlUtnBody = (
            "SELECT DISTINCT                                 \n"
            "   TAB_A.MOVEMENT_ID                            \n"
            "  ,TAB_B.MOVEMENT_NAME                          \n"
            "  ,TAB_C.ROLE_PACKAGE_ID                        \n"
            "  ,TAB_F.ROLE_PACKAGE_NAME                      \n"
            "  ,TAB_C.ROLE_ID                                \n"
            "  ,TAB_G.ROLE_NAME                              \n"
            "  ,TAB_A.VARS_ENTRY                             \n"
            "  ,TAB_D.DISUSE_FLAG  PTN_VARS_LINK_DISUSE_FLAG \n"
            "  ,TAB_F.DISUSE_FLAG  ROLE_PACKAGE_DISUSE_FLAG  \n"
            "  ,TAB_G.DISUSE_FLAG  ROLE_DISUSE_FLAG          \n"
            "FROM                                            \n"
            "   T_ANSR_VALUE                     TAB_A       \n"
            "   LEFT JOIN V_ANSR_MOVEMENT        TAB_B       \n"
            "   ON ( TAB_A.MOVEMENT_ID      = TAB_B.MOVEMENT_ID      ) \n"
            "   LEFT JOIN T_ANSR_MVMT_MATL_LINK  TAB_C       \n"
            "   ON ( TAB_A.MOVEMENT_ID      = TAB_C.MOVEMENT_ID      ) \n"
            "   LEFT JOIN T_ANSR_MVMT_VAR_LINK   TAB_D       \n"
            "   ON ( TAB_A.MVMT_VAR_LINK_ID = TAB_D.MVMT_VAR_LINK_ID ) \n"
            "   LEFT JOIN T_ANSR_MATL_COLL       TAB_F       \n"
            "   ON ( TAB_C.ROLE_PACKAGE_ID  = TAB_F.ROLE_PACKAGE_ID  ) \n"
            "   LEFT JOIN T_ANSR_ROLE_NAME       TAB_G       \n"
            "   ON ( TAB_C.ROLE_ID          = TAB_G.ROLE_ID          ) \n"
            "WHERE                                           \n"
            "   TAB_A.EXECUTION_NO = '%s'  AND               \n"
            "   TAB_A.VARS_ENTRY_USE_TPFVARS = '1' AND       \n"
            "   TAB_A.DISUSE_FLAG = '0' AND                  \n"
            "   TAB_B.DISUSE_FLAG = '0' AND                  \n"
            "   TAB_C.DISUSE_FLAG = '0'                      \n"
        )

        rset = ws_db.sql_execute(sqlUtnBody, [uuid,])

        dbObj = AnsibleCommonLibs()
        for row in rset:
            # テンプレート変数名の書式確認
            tpf_var_name = ''
            ret, tpf_var_name = self.chkValueIsVariable('TPF_', row['VARS_ENTRY'], tpf_var_name)
            if ret is False:
                continue

            # ロールパッケージ名が不一致の場合は除外
            # 復活のケースがあるので、廃止かは判定しない
            if row['ROLE_PACKAGE_NAME'] != role_package_name:
                continue

            hit = False
            for role_name in role_name_list:
                # ロールパッケージ内のロール名と不一致の場合
                # 復活のケースがあるので、廃止かは判定しない
                if row['ROLE_NAME'] != role_name:
                    continue

                hit = True

            # ロール名が不一致の場合は除外
            if hit is False:
                continue

            # Movementに紐づいているロールを取得
            # これより前で、廃止されているMovementでないことは確認済み
            sql = (
                "SELECT                    \n"
                "  TAB_A.MVMT_MATL_LINK_ID \n"
                " ,TAB_A.MOVEMENT_ID       \n"
                " ,TAB_B.MOVEMENT_NAME     \n"
                " ,TAB_A.ROLE_PACKAGE_ID   \n"
                " ,TAB_C.ROLE_PACKAGE_NAME \n"
                " ,TAB_A.ROLE_ID           \n"
                " ,TAB_D.ROLE_NAME         \n"
                "FROM                      \n"
                "   T_ANSR_MVMT_MATL_LINK       TAB_A \n"
                "   LEFT JOIN V_ANSR_MOVEMENT   TAB_B \n"
                "   ON (TAB_A.MOVEMENT_ID     = TAB_B.MOVEMENT_ID )     \n"
                "   LEFT JOIN T_ANSR_MATL_COLL  TAB_C \n"
                "   ON (TAB_A.ROLE_PACKAGE_ID = TAB_C.ROLE_PACKAGE_ID ) \n"
                "   LEFT JOIN T_ANSR_ROLE_NAME  TAB_D \n"
                "   ON (TAB_A.ROLE_ID         = TAB_D.ROLE_ID         ) \n"
                "WHERE                          \n"
                "       TAB_A.DISUSE_FLAG = '0' \n"
                "   AND TAB_A.MOVEMENT_ID = %s  \n"
            ) % (row['MOVEMENT_ID'])

            # ロールパッケージ管理からの場合で、新規・変更の場合の条件
            # 復活の場合は条件から除外
            if role_disuse_check is True:
                sql += (
                    "   AND TAB_C.DISUSE_FLAG = '0' \n"
                    "   AND TAB_D.DISUSE_FLAG = '0' \n"
                )

            errmsg = ""
            errdetailmsg = ""
            movement_use_role_name_row = dbObj.select_db_recodes(sql, 'MVMT_MATL_LINK_ID', ws_db)

            # Movementに紐づいているロールを取得
            movement_use_role_name_list = {}
            for linkid, movement_row in movement_use_role_name_row.items():
                movement_use_role_name_list[movement_row['ROLE_NAME']] = 0

            movement_use_role_name_row = None

            # ロールパッケージのロールでMovementに紐づいているロールを取得
            for role_name in role_name_list:
                if role_name in movement_use_role_name_list and movement_use_role_name_list[role_name] is not None:
                    if role_name not in tpf_vars_list:
                        tpf_vars_list[role_name] = {}

                    if 'file' not in tpf_vars_list[role_name]:
                        tpf_vars_list[role_name]['file'] = {}

                    if 'line' not in tpf_vars_list[role_name]['file']:
                        tpf_vars_list[role_name]['file']['line'] = {}

                    if tpf_var_name not in tpf_vars_list[role_name]['file']['line']:
                        tpf_vars_list[role_name]['file']['line'][tpf_var_name] = None

                    tpf_vars_list[role_name]['file']['line'][tpf_var_name] = 0

            movement_use_role_name_list = None

        # DBアクセス事後処理
        dbObj = None
        if not self.lv_ws_db and ws_db:
            ws_db.db_disconnect()
            ws_db = None

        return True, tpf_vars_list

    def getTemplateUseVarsStructiMain(self, tpf_vars_list, ITA2User_var_list, gbl_vars_list, tpf_vars_struct, errormsg):

        """
        処理内容
          テンプレートで使用している変数を取得

        パラメータ
          tpf_vars_list:       使用しているテンプレート変数リスト
          ITA2User_var_list:   読替表(読替変数->ユーザー変数)
          gbl_vars_list:       テンプレートで使用しているグローバル変数のリスト
          tpf_vars_struct:     テンプレートで使用している変数の変数構造リスト
          errormsg:            エラー時のメッセージ

        戻り値
          なし
        """

        errormsg = ""
        for rolename, tpf_vars_array1 in self.php_array(tpf_vars_list):
            for tgt_file_name, tpf_vars_array2 in self.php_array(tpf_vars_array1):
                for line_no, tpf_vars_array3 in self.php_array(tpf_vars_array2):
                    for tpf_var_name, dummy in self.php_array(tpf_vars_array3):
                        gbl_vars_list, tpf_vars_struct, errormsg = self.getTemplateUseVarsStructSub(
                            tpf_var_name, rolename, ITA2User_var_list, gbl_vars_list, tpf_vars_struct, errormsg
                        )

        return gbl_vars_list, tpf_vars_struct, errormsg

    def getTemplateUseVarsStructSub(self, tpf_var_name, rolename, ITA2User_var_list, gbl_vars_list, tpf_vars_struct, errormsg):

        """
        処理内容
          指定された変数の変数構造を取得

        パラメータ
          tpf_vars_list:       使用しているテンプレート変数リスト
          ITA2User_var_list:   読替表(読替変数->ユーザー変数)
          gbl_vars_list:       テンプレートで使用しているグローバル変数のリスト
          tpf_vars_struct:     テンプレートで使用している変数の変数構造リスト
          errormsg:            エラー時のメッセージ

        戻り値
          なし
        """

        if tpf_var_name in self.lva_template_master_list and self.lva_template_master_list[tpf_var_name] is not None:
            # 変数構造解析結果
            php_array = json.loads(self.lva_template_master_list[tpf_var_name]['VAR_STRUCT_ANAL_JSON_STRING'])
            if 'Vars_list' in php_array and php_array['Vars_list'] is not None:
                for var_name, var_struct in self.php_array(php_array['Vars_list']):
                    # 変数の種類確認
                    var_type = self.chkVariableType(var_name)
                    if var_type == "VAR":
                        # 変数の情報をマージする
                        if 'Vars_list' not in tpf_vars_struct:
                            tpf_vars_struct['Vars_list'] = {}

                        if rolename not in tpf_vars_struct['Vars_list']:
                            tpf_vars_struct['Vars_list'][rolename] = {}

                        if var_name not in tpf_vars_struct['Vars_list'][rolename]:
                            tpf_vars_struct['Vars_list'][rolename][var_name] = None

                        tpf_vars_struct['Vars_list'][rolename][var_name] = var_struct

                    """
                    if var_type == "LCA":
                        # 読替表に読替変数が設定されているか判定する
                        if rolename in ITA2User_var_list \
                        and var_name in ITA2User_var_list[rolename] and ITA2User_var_list[rolename][var_name] is not None:
                            # 読替表に読替変数未登録
                            if self.log_level == "DEBUG":
                                # MSG-10602 = "テンプレート管理に登録されている読替変数が読替表に登録されていません。この読替変数の処理をスキップします。(テ>ンプレート埋込変数:{} 読替変数:{})"
                                if len(errormsg) > 0:
                                    errormsg = '%s\n' % (errormsg)

                                errormsg += g.appmsg.get_api_message("MSG-10602", [tpf_var_name, var_name])

                            # webから呼ばれている場合
                            if self.web_mode is True:
                                # MSG-10597 = "テンプレート管理で定義している読替変数が読替表に登録されていません。(ロール名:{} 読替変数:{} テンプレート埋込>変数名:{})"
                                if len(errormsg) > 0:
                                    errormsg = '%s\n' % (errormsg)

                                errormsg += g.appmsg.get_api_message("MSG-10597", [rolename, var_name, tpf_var_name])

                            else:
                                if self.log_level == "DEBUG":
                                    # MSG-10602 = "テンプレート管理に登録されている読替変数が読替表に登録されていません。この読替変数の処理をスキップします。(テ>ンプレート埋込変数:{} 読替変数:{})"
                                    if len(errormsg) > 0:
                                        errormsg = '%s\n' % (errormsg)

                                    errormsg += g.appmsg.get_api_message("MSG-10602", [tpf_var_name, var_name])

                            # 次の変数へ
                            continue

                        # 変数の情報をマージする
                        tpf_vars_struct['Vars_list'][rolename][var_name] = var_struct
                    """

                    if var_type == "GBL":
                        # グローバル変数の具体値にテンプレート変数が設定されているか判定する
                        if var_name in self.lva_global_vars_master_list and self.lva_global_vars_master_list[var_name] is not None:
                            # webから呼ばれている場合
                            if self.web_mode is True:
                                # MSG-10582 = "(テンプレート埋込変数:{} グローバル変数:{})"
                                if len(errormsg) > 0:
                                    errormsg = '%s\n' % (errormsg)

                                parammsg = g.appmsg.get_api_message("MSG-10582", [tpf_var_name, var_name])

                                # MSG-10581 = "テンプレート管理で使用しているグローバル変数がグローバル変数管理に登録されていません。{}"
                                errormsg += g.appmsg.get_api_message("MSG-10581", [parammsg])

                            else:
                                if self.log_level == "DEBUG":
                                    # グローバル変数管理に変数未登録
                                    # MSG-10600 = "グローバル変数管理にグローバル変数が登録されていません。このグローバル変数の処理をスキップします。(グローバル>変数:{})"
                                    if len(errormsg) > 0:
                                        errormsg = '%s\n' % (errormsg)

                                    errormsg += g.appmsg.get_api_message("MSG-10600", [var_name])

                            # 次の変数へ
                            continue

                        if rolename not in gbl_vars_list:
                            gbl_vars_list[rolename] = {}

                        if var_name not in gbl_vars_list[rolename]:
                            gbl_vars_list[rolename][var_name] = None

                        gbl_vars_list[rolename][var_name] = 0

            if 'Array_vars_list' in php_array and php_array['Array_vars_list'] is not None:
                for var_name, var_struct in self.php_array(php_array['Array_vars_list']):
                    # 変数の種類確認
                    var_type = self.chkVariableType(var_name)
                    """
                    if var_type == "LCA":
                        # 読替表に読替変数が設定されているか判定する
                        if rolename not in ITA2User_var_list \
                        or var_name not in ITA2User_var_list[rolename] or ITA2User_var_list[rolename][var_name] is None:
                            # webから呼ばれている場合
                            if self.web_mode is True:
                                # MSG-10597
                                if len(errormsg) > 0:
                                    errormsg = '%s\n' % (errormsg)

                                errormsg += g.appmsg.get_api_message("MSG-10597", [rolename, var_name, tpf_var_name])

                            else:
                                if self.log_level == "DEBUG":
                                    # 読替表に読替変数未登録
                                    if len(errormsg) > 0:
                                        errormsg = '%s\n' % (errormsg)

                                    errormsg += g.appmsg.get_api_message("MSG-10602", [tpf_var_name, var_name])

                            # 次の変数へ
                            continue
                    """

                    # 変数の情報をマージする
                    if 'Array_vars_list' not in tpf_vars_struct:
                        tpf_vars_struct['Array_vars_list'] = {}

                    if rolename not in tpf_vars_struct['Array_vars_list']:
                        tpf_vars_struct['Array_vars_list'][rolename] = {}

                    if var_name not in tpf_vars_struct['Array_vars_list'][rolename]:
                        tpf_vars_struct['Array_vars_list'][rolename][var_name] = None

                    tpf_vars_struct['Array_vars_list'][rolename][var_name] = var_struct

        else:
            if self.master_non_reg_chk is True:
                # webから呼ばれている場合
                if self.web_mode is True:
                    # テンプレート管理に変数未登録
                    if len(errormsg) > 0:
                        errormsg = '%s\n' % (errormsg)

                    errormsg += g.appmsg.get_api_message("MSG-10606", [rolename, tpf_var_name])

                else:
                    if self.log_level == "DEBUG":
                        # テンプレート管理に変数未登録
                        if len(errormsg) > 0:
                            errormsg = '%s\n' % (errormsg)

                        errormsg += g.appmsg.get_api_message("MSG-10601", [rolename, tpf_var_name])

        return gbl_vars_list, tpf_vars_struct, errormsg

    def chkVariableType(self, var_name):

        """
        処理内容
          指定された変数の種類を判定する

        パラメータ
          var_name:            変数名

        戻り値
          変数の種類 VAR/LCA/GBL
        """

        ret = re.search(r'^VAR_[a-zA-Z0-9_]*', var_name)
        if ret:
            return "VAR"

        # 読替変数の場合
        """
        ret = re.search(r'^LCA_[a-zA-Z0-9_]*', var_name)
        if ret:
            return "LCA"
        """

        # グローバル変数の場合
        ret = re.search(r'^GBL_[a-zA-Z0-9_]*', var_name)
        if ret:
            return "GBL"

        return False

    def chkValueIsVariable(self, var_heder_id, var_value, var_name):

        """
        処理内容
          変数名の書式を判定する。

        パラメータ
          var_heder_id:     変数種別(TPF_)
          var_value:        変数名({{ xxxx }}
          var_name:         {{}}を取り除いた変数名

        戻り値
          True:正常  False:異常
        """

        var_name = ''

        # 変数名 {{ ???_[a-zA-Z0-9_] }} を取出す
        var_match = re.findall(r'{{\s' + var_heder_id + r'[a-zA-Z0-9_]*\s}}', var_value)
        if len(var_match) > 0:
            var_name_match = re.findall(var_heder_id + r'[a-zA-Z0-9_]*', var_match[0])
            var_name = var_name_match[0].strip()
            return True, var_name

        return False, var_name

    def getGlobalVarsUseTemplateUseVars(self, gbl_vars_list, tpf_vars_list, errormsg):

        """
        処理内容
          グローバル変数の具体値に設定されているテンプレート変数を取得

        パラメータ
          gbl_vars_list:    クローバル変数リスト
          tpf_vars_lists:   グローバル変数の具体値に設定されているテンプレート変数のリスト
          errormsg:         エラー時のメッセージ

        戻り値
          True:正常  False:異常
        """

        errormsg = ""

        for rolename, gbl_vars_array1 in self.php_array(gbl_vars_list):
            for var_name, dummy in self.php_array(gbl_vars_array1):
                # グローバル変数の具体値にテンプレート変数が設定されているか判定する
                if var_name in self.lva_global_vars_master_list and self.lva_global_vars_master_list[var_name] is not None:
                    var_value = self.lva_global_vars_master_list[var_name]['VARS_ENTRY']
                    value_var_name = ""
                    ret, value_var_name = self.chkValueIsVariable('TPF_', var_value, value_var_name)
                    if ret is True:
                        # テンプレート変数退避
                        if rolename not in tpf_vars_list:
                            tpf_vars_list[rolename] = {}

                        if 'file' not in tpf_vars_list[rolename]:
                            tpf_vars_list[rolename]['file'] = {}

                        if 'line' not in tpf_vars_list[rolename]['file']:
                            tpf_vars_list[rolename]['file']['line'] = {}

                        if value_var_name not in tpf_vars_list[rolename]['file']['line']:
                            tpf_vars_list[rolename]['file']['line'][value_var_name] = None

                        tpf_vars_list[rolename]['file']['line'][value_var_name] = 0

                else:
                    if self.master_non_reg_chk is True:
                        # グローバル変数管理に変数未登録
                        # webから呼ばれている場合
                        if self.web_mode is True:
                            # MSG-10605 "グローバル変数管理にグローバル変数が登録されていません。(グローバル変数:{})"
                            if len(errormsg) > 0:
                                errormsg = '%s\n' % (errormsg)

                            errormsg += g.appmsg.get_api_message("MSG-10605", [var_name])

                        else:
                            if self.log_level == "DEBUG":
                                # MSG-10600 "グローバル変数管理にグローバル変数が登録されていません。このグローバル変数の処理をスキップします。(グローバル>変数:{})"
                                if len(errormsg) > 0:
                                    errormsg = '%s\n' % (errormsg)

                                errormsg += g.appmsg.get_api_message("MSG-10600", [var_name])

        return tpf_vars_list, errormsg

    def RolePackageAnalysis(
        self,
        strTempFileFullname, PkeyID, role_package_name, disuse_role_chk,
        def_vars_list, def_varsval_list, def_array_vars_list,
        cpf_vars_chk, cpf_vars_list,
        tpf_vars_chk, tpf_vars_list, gbl_vars_list,
        ITA2User_var_list, User2ITA_var_list, save_vars_list
    ):

        boolRet = True
        intErrorType = None
        aryErrMsgBody = []
        strErrMsg = None
        arysystemvars = []

        # ロールパッケージファイル(ZIP)を解析するクラス生成
        # ToDo fileuploadカラムのパスが変更になっている
        roleObj = CheckAnsibleRoleFiles(self.lv_objMTS)

        # ロールパッケージファイル(ZIP)の解凍先
        outdir = "%s/LegacyRoleZipFileUpload_%s" % (get_AnsibleDriverTmpPath(), os.getpid())

        def_vars_list = {}
        err_vars_list = {}
        def_varsval_list = {}
        cpf_vars_list = {}
        tpf_vars_list = {}
        ITA2User_var_list = {}
        User2ITA_var_list = {}
        comb_err_vars_list = {}
        role_name_list = {}

        # ロールパッケージファイル(ZIP)の解凍
        if roleObj.ZipextractTo(strTempFileFullname, outdir) == False:
            boolRet = False
            arryErrMsg = roleObj.getlasterror()
            strErrMsg = arryErrMsg[0]

        else:

            # ロールパッケージファイル(ZIP)の解析
            ret, def_vars_list, err_vars_list, def_varsval_list, def_array_vars_list, cpf_vars_list, tpf_vars_list, ITA2User_var_list, User2ITA_var_list, comb_err_vars_list = roleObj.chkRolesDirectory(
                outdir, arysystemvars, "", def_vars_list, err_vars_list, def_varsval_list, def_array_vars_list,
                cpf_vars_chk, cpf_vars_list, tpf_vars_chk, tpf_vars_list,
                ITA2User_var_list, User2ITA_var_list, comb_err_vars_list, True
            )

            if not ret:
                # ロール内の読替表で読替変数と任意変数の組合せが一致していない
                """
                if len(comb_err_vars_list) > 0:
                    msgObj = DefaultVarsFileAnalysis(self.lv_objMTS)
                    strErrMsg = msgObj.TranslationTableCombinationErrmsgEdit(False, comb_err_vars_list)
                    msgObj = None
                    boolRet = False
                """

                # defaults定義ファイルに定義されている変数で形式が違う変数がある場合
                if len(err_vars_list) > 0:
                    # エラーメッセージ編集
                    msgObj = DefaultVarsFileAnalysis(self.lv_objMTS)
                    strErrMsg = msgObj.VarsStructErrmsgEdit(err_vars_list)
                    msgObj = None
                    boolRet = False

                else:
                    boolRet = False
                    arryErrMsg = roleObj.getlasterror()
                    strErrMsg = arryErrMsg[0]

            # zipファイルがからの場合、ディレクトリが作成されない
            is_dir = os.path.isdir(outdir)
            if is_dir is True:
                shutil.rmtree(outdir)

            # ロール名一覧取得
            role_name_list = roleObj.getrolename()

            # グローバル変数の一覧取得
            gbl_vars_list = roleObj.getglobalvarname()
            if type(gbl_vars_list) not in  (list, dict):
                gbl_vars_list = {}

            # 変数構造の解析のみの場合
            if self.vars_struct_anal_only is True:
                boolRet = True
                retArray = [boolRet, intErrorType, aryErrMsgBody, strErrMsg]
                return retArray, def_vars_list, def_varsval_list, def_array_vars_list, cpf_vars_list, tpf_vars_list, gbl_vars_list, ITA2User_var_list, User2ITA_var_list, save_vars_list, role_name_list

            dbObj = AnsibleCommonLibs()
            ws_db = self.lv_ws_db
            if not ws_db:
                ws_db = DBConnectWs()

            if boolRet is True:
                ##############################################################################
                # グローバル変数の情報を取得
                ##############################################################################
                self.lva_global_vars_master_list = {}
                sql = (
                    "SELECT                 \n"
                    "    VARS_NAME,         \n"
                    "    VARS_ENTRY         \n"
                    "FROM                   \n"
                    "    T_ANSC_GLOBAL_VAR  \n"
                    "WHERE                  \n"
                    "    DISUSE_FLAG = '0'; \n"
                )

                self.lva_global_vars_master_list = dbObj.select_db_recodes(sql, 'VARS_NAME', ws_db)

            if boolRet is True:
                ##############################################################################
                # iコンテンツ管理(CPF変数Iの情報を取得
                ##############################################################################
                lva_contents_vars_master_list = {}
                sql = (
                    "SELECT                            \n"
                    "    CONTENTS_FILE_ID,             \n"
                    "    CONTENTS_FILE_VARS_NAME       \n"
                    "FROM                              \n"
                    "    T_ANSC_CONTENTS_FILE          \n"
                    "WHERE                             \n"
                    "    DISUSE_FLAG            = '0'; \n"
                )

                lva_contents_vars_master_list = dbObj.select_db_recodes(sql, 'CONTENTS_FILE_VARS_NAME', ws_db)

            if boolRet is True:
                ##############################################################################
                # テンプレート管理の情報を取得
                ##############################################################################
                self.lva_template_master_list = {}
                sql = (
                    "SELECT                            \n"
                    "    ANS_TEMPLATE_ID,              \n"
                    "    ANS_TEMPLATE_VARS_NAME,       \n"
                    "    VARS_LIST,                    \n"
                    "    VAR_STRUCT_ANAL_JSON_STRING   \n"
                    "FROM                              \n"
                    "    T_ANSC_TEMPLATE_FILE          \n"
                    "WHERE                             \n"
                    "    DISUSE_FLAG            = '0'; \n"
                )

                self.lva_template_master_list = dbObj.select_db_recodes(sql, 'ANS_TEMPLATE_VARS_NAME', ws_db)
                for strVarName, row in self.lva_template_master_list.items():
                    Vars_list = []
                    Array_vars_list =[]
                    LCA_vars_use = False
                    Array_vars_use = False
                    GBL_vars_info = []
                    VarVal_list = []
                    strPkeyID = row['ANS_TEMPLATE_ID']
                    strVarsList = row['VARS_LIST']

                    # 変数定義の解析結果を取得
                    # ToDo 別処理に置き換え(TemplateVarsStructAnalFileAccess)
                    """
                    fileObj = TemplateVarsStructAnalFileAccess(self.lv_objMTS, self.lv_objDBCA)

                    # 変数定義の解析結果をファイルから取得
                    # ファイルがない場合は、変数定義を解析し解析結果をファイルに保存
                    ret = fileObj.getVarStructAnalysis(
                        strPkeyID, strVarName, strVarsList, Vars_list, Array_vars_list,
                        LCA_vars_use, Array_vars_use, GBL_vars_info, VarVal_list
                    )
                    if ret is False:
                        errmsg = fileObj.GetLastError()
                        strErrMsg = errmsg[0]
                        boolRet = False

                    # 変数定義の解析結果をjson形式の文字列に変換
                    php_array = fileObj.ArrayTOjsonString(
                        Vars_list, Array_vars_list, LCA_vars_use, Array_vars_use, GBL_vars_info, VarVal_list
                    )

                    # 配列に保存
                    self.lva_template_master_list[strVarName]['VAR_STRUCT_ANAL_JSON_STRING'] = php_array
                    fileObj = None
                    if boolRet is False:
                        break
                    """

            dbObj = None
            if not self.lv_ws_db and ws_db:
                ws_db.db_disconnect()
                ws_db = None

            GBLVars = '1'
            CPFVars = '2'
            TPFVars = '3'
            save_vars_list = {}
            save_vars_list[GBLVars] = {}
            save_vars_list[CPFVars] = {}
            save_vars_list[TPFVars] = {}
            objLibs = AnsibleCommonLibs(AnscConst.LC_RUN_MODE_STD)
            if boolRet is True:
                strErrMsg = ""
                strErrDetailMsg = ""
                for role_name, tgt_file_list in self.php_array(cpf_vars_list):
                    for tgt_file, line_no_list in self.php_array(tgt_file_list):
                        for line_no, cpf_var_name_list in self.php_array(line_no_list):
                            for cpf_var_name, dummy in self.php_array(cpf_var_name_list):
                                if cpf_var_name not in save_vars_list[CPFVars]:
                                    save_vars_list[CPFVars][cpf_var_name] = None

                                save_vars_list[CPFVars][cpf_var_name]  = 0

            if boolRet is True:
                # テンプレート管理の変数定義とロール内の変数定義が一致しているか確認する
                for role_name, tgt_file_list in self.php_array(tpf_vars_list):
                    for tgt_file, line_no_list in self.php_array(tgt_file_list):
                        for line_no, tpf_var_name_list in self.php_array(line_no_list):
                            for tpf_var_name, row in self.php_array(tpf_var_name_list):
                                if tpf_var_name not in save_vars_list[TPFVars]:
                                    save_vars_list[TPFVars][tpf_var_name] = None

                                save_vars_list[TPFVars][tpf_var_name] = 0

                chk_list = {}
                for tpf_var_name, row in self.lva_template_master_list.items():
                    # 重複チェック防止
                    if tpf_var_name in chk_list and chk_list[tpf_var_name] is not None:
                        continue

                    chk_list[tpf_var_name] = 0

                    # テンプレート管理の変数定義取得
                    chk_json_Ary = row['VAR_STRUCT_ANAL_JSON_STRING']
                    chk_php_array = json.loads(chk_json_Ary)

                    chk_vars_list = {}
                    chk_Array_vars_list = {}

                    if tpf_var_name not in chk_vars_list:
                        chk_vars_list[tpf_var_name] = {}

                    if 'dummy' not in chk_vars_list[tpf_var_name]:
                        chk_vars_list[tpf_var_name]['dummy'] = None

                    if tpf_var_name not in chk_Array_vars_list:
                        chk_Array_vars_list[tpf_var_name] = {}

                    if 'dummy' not in chk_Array_vars_list[tpf_var_name]:
                        chk_Array_vars_list[tpf_var_name]['dummy'] = None

                    chk_vars_list[tpf_var_name]['dummy'] = chk_php_array['Vars_list']
                    chk_Array_vars_list[tpf_var_name]['dummy'] = chk_php_array['Array_vars_list']

                    # ロール毎の変数定義とテンプレート管理の変数定義が一致しているか確認
                    for no, crt_role_name in self.php_array(role_name_list):
                        if tpf_var_name not in chk_vars_list:
                            chk_vars_list[tpf_var_name] = {}

                        if 'role' not in chk_vars_list[tpf_var_name]:
                            chk_vars_list[tpf_var_name]['role'] = None

                        if tpf_var_name not in chk_Array_vars_list:
                            chk_Array_vars_list[tpf_var_name] = {}

                        if 'role' not in chk_Array_vars_list[tpf_var_name]:
                            chk_Array_vars_list[tpf_var_name]['role'] = None

                        chk_vars_list[tpf_var_name]['role'] = []
                        chk_Array_vars_list[tpf_var_name]['role'] = []

                        # ロール毎の変数定義取得
                        # 通常・複数具体値変数
                        if crt_role_name in def_vars_list and def_vars_list[crt_role_name] is not None:
                            chk_vars_list[tpf_var_name]['role'] = def_vars_list[crt_role_name]

                        # 多段変数
                        if crt_role_name in def_array_vars_list and def_array_vars_list[crt_role_name] is not None:
                            chk_Array_vars_list[tpf_var_name]['role'] = def_array_vars_list[crt_role_name]

                        chkObj = DefaultVarsFileAnalysis(self.lv_objMTS)
                        err_vars_list = {}

                        # 変数構造が一致していない変数があるか確認
                        ret, err_vars_list = chkObj.chkallVarsStruct(chk_vars_list, chk_Array_vars_list, err_vars_list)
                        if ret is False:
                            # 変数構造が一致していない変数あり
                            for err_var_name, dummy in self.php_array(err_vars_list):
                                if len(strErrMsg) > 0:
                                    strErrMsg = '%s\n' % (strErrMsg)

                                strErrMsg += g.appmsg.get_api_message(
                                    "MSG-10596", [crt_role_name, err_var_name, tpf_var_name]
                                )
                                boolRet = False

                            chkObj = None

            if boolRet is True:
                # ロール内で使用しているグローバル変数の登録確認は実施済み
                for role_name, gbl_var_name_list in self.php_array(gbl_vars_list):
                    for gbl_var_name, dummy in self.php_array(gbl_var_name_list):
                        if gbl_var_name not in save_vars_list[GBLVars]:
                            save_vars_list[GBLVars][gbl_var_name] = None

                        save_vars_list[GBLVars][gbl_var_name] = 0

            objLibs = None

        roleObj = None

        retArray = [boolRet, intErrorType, aryErrMsgBody, strErrMsg]

        return retArray, def_vars_list, def_varsval_list, def_array_vars_list, cpf_vars_list, tpf_vars_list, gbl_vars_list, ITA2User_var_list, User2ITA_var_list, save_vars_list, role_name_list

    def AllRolePackageAnalysis(self, tgt_PkeyID, tgt_role_pkg_name, tgt_vars_list, tgt_array_vars_list, error_msg_code="MSG-10607"):

        def_vars_list = {}
        def_array_vars_list = {}
        var_struct_errmag = ""
        all_err_vars_list = {}

        role_package_master_list = []
        ret, role_package_master_list = self.getRolePackageInfo(role_package_master_list)
        if ret is False:
            return False

        for PkeyID, PkgRow in role_package_master_list.items():
            if tgt_PkeyID == PkeyID:
                continue

            # 変数構造解析結果ファイルから変数構造取得
            obj = VarStructAnalJsonConv()
            retAry = obj.VarStructAnalJsonLoads(PkgRow['VAR_STRUCT_ANAL_JSON_STRING'])
            def_vars_list = retAry[0]
            def_array_vars_list = retAry[1]
            tpf_vars_list = retAry[2]
            ITA2User_var_list = retAry[3]
            gbl_vars_list = retAry[4]
            Role_name_list = retAry[5]

            all_def_vars_list = {}
            all_def_array_vars_list = {}

            # 比較元ロールパッケージファイル default定義数名リスト退避
            all_def_vars_list[tgt_role_pkg_name] = tgt_vars_list

            # 比較元ロールパッケージファイル default定義 多次元配列リスト退避
            all_def_array_vars_list[tgt_role_pkg_name] = tgt_array_vars_list

            # 比較元ロールパッケージファイル default定義数名リスト退避
            all_def_vars_list[PkgRow['ROLE_PACKAGE_NAME']] = def_vars_list

            # 比較元ロールパッケージファイル default定義 多次元配列リスト退避
            all_def_array_vars_list[PkgRow['ROLE_PACKAGE_NAME']] = def_array_vars_list

            Obj = DefaultVarsFileAnalysis(self.lv_objMTS)
            err_vars_list = {}
            ret, err_vars_list = Obj.chkallVarsStruct(all_def_vars_list, all_def_array_vars_list, err_vars_list)

            # 変数の構造が一致していないロールパッケージする
            if ret is False:
                for err_var_name, err_pkg_list in err_vars_list.items():
                    for err_pkg_name, err_role_list in err_pkg_list.items():
                        if err_var_name not in all_err_vars_list:
                            all_err_vars_list[err_var_name] = {}

                        if err_pkg_name not in all_err_vars_list[err_var_name]:
                            all_err_vars_list[err_var_name][err_pkg_name] = None

                        all_err_vars_list[err_var_name][err_pkg_name] = err_role_list

            Obj = None

        if len(all_err_vars_list) > 0:
            var_struct_errmag = self.VarsStructErrmsgEdit(all_err_vars_list, tgt_role_pkg_name, error_msg_code)
            self.SetLastError(os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno, var_struct_errmag)
            return False

        return True

    def VarsStructErrmsgEdit(self, ina_err_vars_list, tgt_role_pkg_name, error_msg_code):

        errmsg = g.appmsg.get_api_message(error_msg_code)
        for err_var_name, err_pkg_list in self.php_array(ina_err_vars_list):
            err_files = ""
            for err_pkg_name, err_role_list in self.php_array(err_pkg_list):
                if err_pkg_name == tgt_role_pkg_name:
                    continue

                for err_role_name, dummy in self.php_array(err_role_list):
                    err_files = '%s%s\n' % (
                        err_files,
                        g.appmsg.get_api_message("MSG-10609", [err_pkg_name, err_role_name])
                    )

            if err_files:
                errmsg += g.appmsg.get_api_message("MSG-10608", [err_var_name, err_files])

        return errmsg

    def getVarStructAnalInfo(
        self,
        tgt_PkeyID, tgt_role_pkg_name, tgt_zipfile,
        tgt_def_vars_list, tgt_def_array_vars_list, tgt_tpf_vars_list, tgt_ITA2User_var_list, tgt_gbl_vars_list
    ):

        dbObj = AnsibleCommonLibs()
        ws_db = self.lv_ws_db
        if not ws_db:
            ws_db = DBConnectWs()

        sql = (
            "SELECT                          \n"
            "    ROLE_PACKAGE_ID             \n"
            "   ,ROLE_PACKAGE_NAME           \n"
            "   ,ROLE_PACKAGE_FILE           \n"
            "   ,VAR_STRUCT_ANAL_JSON_STRING \n"
            "FROM                            \n"
            "    T_ANSR_MATL_COLL            \n"
            "WHERE                           \n"
            "    ROLE_PACKAGE_ID = '%s' AND  \n"
            "    DISUSE_FLAG='0';            \n"
        ) % (tgt_PkeyID)

        rset = dbObj.select_db_recodes(sql, 'ROLE_PACKAGE_ID', ws_db)
        if len(rset) <= 0:
            False, tgt_def_vars_list, tgt_def_array_vars_list, tgt_tpf_vars_list, tgt_ITA2User_var_list, tgt_gbl_vars_list

        PkgRow = rset[str(tgt_PkeyID)]

        # 変数構造解析結果ファイルから変数構造取得
        obj = VarStructAnalJsonConv()
        retAry = obj.VarStructAnalJsonLoads(PkgRow['VAR_STRUCT_ANAL_JSON_STRING'])
        tgt_def_vars_list = retAry[0]
        tgt_def_array_vars_list = retAry[1]
        tgt_tpf_vars_list = retAry[2]
        tgt_ITA2User_var_list = retAry[3]
        tgt_gbl_vars_list = retAry[4]
        Role_name_list = retAry[5]

        if not self.lv_ws_db and ws_db:
            ws_db.db_disconnect()
            ws_db = None

        return True, tgt_def_vars_list, tgt_def_array_vars_list, tgt_tpf_vars_list, tgt_ITA2User_var_list, tgt_gbl_vars_list
