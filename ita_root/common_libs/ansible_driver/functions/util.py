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
from flask import g
import os
import shutil
import shlex
import glob
import subprocess

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.AnslConstClass import AnslConst
from common_libs.ansible_driver.classes.AnspConstClass import AnspConst
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst
from common_libs.loadtable import load_table
from common_libs.common.util import retry_rmtree, retry_remove, retry_copytree

"""
  Ansible共通モジュール
"""


def getMovementAnsibleCnfUploadDirPath():
    """
      Movement一覧 ansible.cfgファイル FileUploadColumnディレクトリバスを取得する。
      基本コンソールのMovement一覧の項目に対応したディレクトリにファイルが収まっている
      Arguments:
        なし
      Returns:
         Movement一覧 ansible.cfgファイル ディレクトリバスを取得
    """
    return getDataRelayStorageDir() + "/uploadfiles/10202/Ansible_cfg"


def getRolePackageContentUploadDirPath():
    """
      ロールパッケージ管理FileUploadColumnディレクトリバスを取得する。
      Arguments:
        なし
      Returns:
        ロールパッケージ管理FileUploadColumnディレクトリバス
    """
    return getDataRelayStorageDir() + "/uploadfiles/20403/zip_format_role_package_file"


def getFileContentUploadDirPath():
    """
      ファイル管理FileUploadColumnディレクトリバスを取得する。
      Arguments:
        なし
      Returns:
        ファイル管理FileUploadColumnディレクトリバスを取得
    """
    return getDataRelayStorageDir() + "/uploadfiles/20105/files"


def getTemplateContentUploadDirPath():
    """
      テンプレート管理FileUploadColumnディレクトリバスを取得する。
      Arguments:
        なし
      Returns:
        テンプレート管理FileUploadColumnディレクトリバス
    """
    return getDataRelayStorageDir() + "/uploadfiles/20106/template_files"


def getDeviceListSSHPrivateKeyUploadDirPath():
    """
      機器一覧ssh秘密鍵ファイルディレクトリバスを取得する。
      Arguments:
        なし
      Returns:
        機器一覧ssh秘密鍵ファイルディレクトリバスを取得
    """
    return getDataRelayStorageDir() + "/uploadfiles/20101/ssh_private_key_file"


def getDeviceListWinrmPrivateKeyFileUploadDirPath():
    """
      機器一覧ssh秘密鍵ファイルディレクトリバスを取得する。
      Arguments:
        なし
      Returns:
        機器一覧ssh秘密鍵ファイルディレクトリバスを取得
    """
    return getDataRelayStorageDir() + "/uploadfiles/20101/winrm_private_key_file"

def getDeviceListWinrmPublicKeyFileUploadDirPath():
    """
      機器一覧winrm公開鍵ファイルバスを取得する。
      Arguments:
        なし
      Returns:
        機器一覧winrm公開鍵ファイルディレクトリバスを取得
    """
    return getDataRelayStorageDir() + "/uploadfiles/20101/winrm_public_key_file"

def getAnsibleIFSSHPrivateKeyUploadDirPath():
    """
      Ansibleインターフェースssh秘密鍵ファイルディレクトリバスを取得する。
      Arguments:
        なし
      Returns:
        Ansibleインターフェースssh秘密鍵ファイルディレクトリバス
    """
    return getDataRelayStorageDir() + "/uploadfiles/20102/ssh_private_key_file"


def getAACListSSHPrivateKeyUploadDirPath():
    """
      AACホスト一覧ssh秘密鍵ファイルディレクトリバスを取得する。
      Arguments:
        なし
      Returns:
        AACホスト一覧ssh秘密鍵ファイルディレクトリバス
    """
    return getDataRelayStorageDir() + "/uploadfiles/20103/ssh_private_key_file"


def getLegayRoleExecutPopulatedDataUploadDirPath():
    """
      作業管理投入データディレクトリバスを取得する。
      Arguments:
        なし
      Returns:
        作業管理投入データディレクトリバス
    """
    return getDataRelayStorageDir() + "/uploadfiles/20412/populated_data"


def getLegayRoleExecutResultDataUploadDirPath():
    """
      作業管理結果データディレクトリバスを取得する。
      Arguments:
        なし
      Returns:
        作業管理結果データディレクトリバス
    """
    return getDataRelayStorageDir() + "/uploadfiles/20412/result_data"


def getLegacyPlaybookUploadDirPath():
    """
      Legacy Playbook素材集のPlaybook素材ディレクトリバスを取得する。
      Arguments:
        なし
      Returns:
        作業管理結果データディレクトリバス
    """
    return getDataRelayStorageDir() + "/uploadfiles/20202/playbook_file"


def getPioneerDialogUploadDirPath():
    """
      Pioneer 対話ファイル素材集の対話ファイル素材ディレクトリバスを取得する。
      Arguments:
        なし
      Returns:
        作業管理結果データディレクトリバス
    """
    return getDataRelayStorageDir() + "/uploadfiles/20304/dialog_file"


def to_str(bstr):
    """
      byte型をstr型に変換
      Arguments:
        bstr: byte型
      Returns:
        str型に変換したデータ
    """
    if isinstance(bstr, bytes):
        toStr = bstr.decode('utf-8')
    else:
        toStr = bstr
    return toStr

def get_OSTmpPath():
    """
      /tmpバスを取得する。
      Azuruの/storage配下はアクセス時間が遅いので、/in・/outディレクトリのアクセス以外は
      get_OSTmpPath()を使用する。
      Arguments:
        なし
      Returns:
        Ansible用tmpバス
    """
    return "/tmp"

def addAnsibleCreateFilesPath(path):
    """
      指定されたファイルをゴミ掃除ファイルリストに追加
      Arguments:
        path: ゴミ掃除ファイルリストに追加するファイル・ディレクトリ
      Returns:
        なし
    """
    file_name = g.AnsibleCreateFilesPath

    # #2079 /storage配下ではないので対象外
    with open(file_name, 'a') as fd:
        fd.write(path + "\n")

def getAnsibleCreateFilesPath():
    """
      ゴミ掃除ファイルリストのファイル・ディレクトリを取得
      Arguments:
        path: ゴミ掃除ファイルリストに追加するファイル・ディレクトリ
      Returns:
        result_path_list: ゴミ掃除ファイルリスト内のァイル・ディレクトリ
    """
    result_path_list = []

    file_name = g.AnsibleCreateFilesPath

    if not os.path.isfile(file_name):
        return result_path_list

    # #2079 /storage配下ではないので対象外
    with open(file_name, 'r') as fd:
        for path in fd.readlines():
            path = path.replace('\n', '')
            result_path_list.append(path)

    return result_path_list

def rmAnsibleCreateFiles():
    """
      ゴミ掃除ファイルリストのファイル・ディレクトリ
      Arguments:
        なし
      Returns:
        なし
    """
    for del_path in getAnsibleCreateFilesPath():
        if os.path.isdir(del_path):
            retry_rmtree(del_path)
        elif os.path.isfile(del_path):
            retry_remove(del_path)

    file_name = g.AnsibleCreateFilesPath

    if os.path.isfile(file_name):
        retry_remove(file_name)

def get_AnsibleDriverTmpPath():
    """
      Ansible用tmpバスを取得する。
      Azuruの/storage配下はアクセス時間が遅いので、/in・/outディレクトリのアクセス以外は
      get_OSTmpPath()を使用する。
      Arguments:
        なし
      Returns:
        Ansible用tmpバス
    """
    return getDataRelayStorageDir() + "/tmp/driver/ansible"


def getFileupLoadColumnPath(menuid, Column):
    """
      FileUploadColumnのパスを取得する。
      Arguments:
        menuid: メニューID
        Column: カラム名
      Returns:
        Ansible用tmpバス
    """
    return getDataRelayStorageDir() + "/uploadfiles/{}/{}".format(menuid, Column)


def get_AnsibleDriverShellPath():
    """
      Ansible用shell格納バスを取得する。
      Arguments:
        なし
      Returns:
        Ansible用shell格納バス
    """
    return "{}common_libs/ansible_driver/shells".format(os.environ["PYTHONPATH"])


def getAnsibleExecutDirPath(ansConstObj, execute_no):
    """
      ansibe作業実行ディレクトリパス取得
      Arguments:
        ansConstObj: ansible共通定数オブジェクト
        execute_no: 作業番号
      Returns:
        ansibe作業実行ディレクトリパスを取得
    """
    return getDataRelayStorageDir() + "/driver/ansible/{}/{}".format(ansConstObj.vg_OrchestratorSubId_dir, execute_no)


def getDataRelayStorageDir():
    return os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))


def getGitRepositorieDir():
    """
      Ansible Gitリポジトリ作成用 作業ディレクトリ「tmp」バスを取得する。
      Arguments:
        なし
      Returns:
        Ansible Gitリポジトリ用 tmpバス
    """
    basePath = get_OSTmpPath() + "/git_repositorie_dir"

    return basePath


def getAnsibleTmpDir(EcecuteNo, DriverName):
    """
      Ansible 作業ディレクトリ「tmp」バスを取得する。
      Arguments:
        EcecuteNo: 作業番号
        DriverName: オケストレータID
      Returns:
        Ansible Gitリポジトリ用 tmpバス
    """
    ary = {}
    basePath = get_OSTmpPath() + "/temporary_dir"
    ary["BASE_DIR"] = basePath
    tgtPath = basePath + "/{}_{}".format(DriverName, EcecuteNo)
    ary["DIR_NAME"] = tgtPath

    return ary


def getAnsibleConst(driver_id):
    """
    ansible共通定数オブジェクト生成
    Arguments
        driver_id: ドライバ区分
    Returns:
        bool
    """
    if driver_id == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:
        ansc_const = AnsrConst()
    elif driver_id == AnscConst.DF_LEGACY_DRIVER_ID:
        ansc_const = AnslConst()
    elif driver_id == AnscConst.DF_PIONEER_DRIVER_ID:
        ansc_const = AnspConst()
    return ansc_const


def getSpecialColumnVaule(column_rest_name, option):
    """
      パスワードカラム入力値取得
      Arguments:
        column_rest_name: カラム名(REST用)
        option: 個別
      Returns:
        Ansible Gitリポジトリ用 tmpバス
    """
    str_token = option.get("current_parameter").get("parameter").get(column_rest_name)
    if column_rest_name in option["entry_parameter"]["parameter"]:
        str_token = option["entry_parameter"]["parameter"][column_rest_name]
    return str_token

def loacl_quote(arg):
    """
      パラメータ文字列をパラメータ毎に分割し、コーテーションで囲む
      Arguments:
        arg:  パラメータ文字列
      Returns:
        加工された、パラメータ文字列
    """
    result_arg = ""
    list = shlex.split(arg)
    for item in list:
        result_arg += shlex.quote(item) + " "
    return result_arg

def createTmpZipFile(execution_no, zip_data_source_dir, zip_type, zip_file_pfx, rmtmpfiles=True):
    ########################################
    # 処理内容
    #  入力/結果ZIPファイル作成
    #
    # Arugments:
    #  execution_no:               作業実行番号
    #  zip_data_source_dir:        zipファイルの[圧縮元]の資材ディレクトリ
    #  zip_type:                   入力/出力の区分
    #                                   入力:FILE_INPUT   出力:FILE_RESULT
    #  zip_file_pfx:               zipファイル名のプレフィックス
    #                                 入力:InputData_   出力:ResultData_
    #  rmtmpfiles:                 zip作成で利用したファイルディレクトリのゴミ掃除有無
    # Returns:
    #   true:正常　false:異常
    #   zip_file_name:           ZIPファイル名返却
    ########################################
    err_msg = ""
    zip_file_name = ""
    zip_temp_save_dir = ""

    if len(glob.glob(zip_data_source_dir + "/*")) > 0:

        tmp_zip_data_source_dir = "/tmp/{}{}_zip".format(zip_file_pfx, execution_no)

        # /tmpにzipに纏めるディレクトリの確認
        retry_rmtree(tmp_zip_data_source_dir)

        # /tmpにzipに纏める資材コピー
        retry_copytree(zip_data_source_dir, tmp_zip_data_source_dir)

        # ----ZIPファイルを作成する
        zip_file_name = zip_file_pfx + execution_no + '.zip'

        # 圧縮先
        zip_temp_save_dir = get_OSTmpPath()
        zip_temp_save_path = zip_temp_save_dir + "/" + zip_file_name

        # ゴミ掃除リストに追加
        if rmtmpfiles is True:
            addAnsibleCreateFilesPath(zip_temp_save_path)
            addAnsibleCreateFilesPath(tmp_zip_data_source_dir)
        else:
            rmtmpfilelist = []
            rmtmpfilelist.append(zip_temp_save_path)
            rmtmpfilelist.append(tmp_zip_data_source_dir)

        tmp_str_command = "cd " + shlex.quote(tmp_zip_data_source_dir) + " && zip -r " + shlex.quote(zip_temp_save_dir + "/" + zip_file_name) + " . -x ssh_key_files/* -x winrm_key_files/*  -x .vault-password-file 1> /dev/null"  # noqa: E501

        ret = subprocess.run(tmp_str_command, check=True, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # zipファイルパス
        zip_temp_save_path = zip_temp_save_dir + "/" + zip_file_name
        # subprocess.runのエラー時は例外発生
        # if ret.returncode != 0:
        #    err_msg = g.appmsg.get_log_message("MSG-10252", [zip_type, tmp_str_command, ret.stdout])
        #    False, err_msg, zip_file_name, zip_temp_save_dir

        # 処理]{}ディレクトリを圧縮(圧縮ファイル:{})
        g.applogger.debug(g.appmsg.get_log_message("MSG-10783", [zip_type, os.path.basename(zip_temp_save_path)]))
    else:
        rmtmpfilelist = []
        g.applogger.info("zip_data_source_dir:({}) not found".format(zip_data_source_dir))

    if rmtmpfiles is True:
        return True, err_msg, zip_file_name
    else:
        return True, err_msg, zip_file_name, rmtmpfilelist

def InstanceRecodeUpdate(wsDb, driver_id, execution_no, execute_data, update_column_name, zip_tmp_save_path, db_update_need_no_jnl=False):
    """
    作業管理更新

    ARGS:
        wsDb:DB接クラス  DBConnectWs()
        driver_id: ドライバ区分　AnscConst().DF_LEGACY_ROLE_DRIVER_ID
        execution_no: 作業番号
        execute_data: 更新内容配列
        update_column_name: 更新対象のFileUpLoadColumn名
        zip_tmp_save_path: 一時的に作成したzipファイルのパス
        db_update_need_no_jnl: 履歴テーブル更新可否
    RETRUN:
        True/False, errormsg
    """
    TableDict = {}
    TableDict["MENU_REST"] = {}
    TableDict["MENU_REST"][AnscConst.DF_LEGACY_DRIVER_ID] = "execution_list_ansible_legacy"
    TableDict["MENU_REST"][AnscConst.DF_PIONEER_DRIVER_ID] = "execution_list_ansible_pioneer"
    TableDict["MENU_REST"][AnscConst.DF_LEGACY_ROLE_DRIVER_ID] = "execution_list_ansible_role"
    TableDict["MENU_ID"] = {}
    TableDict["MENU_ID"][AnscConst.DF_LEGACY_DRIVER_ID] = "20210"
    TableDict["MENU_ID"][AnscConst.DF_PIONEER_DRIVER_ID] = "20312"
    TableDict["MENU_ID"][AnscConst.DF_LEGACY_ROLE_DRIVER_ID] = "20412"
    TableDict["TABLE"] = {}
    TableDict["TABLE"][AnscConst.DF_LEGACY_DRIVER_ID] = AnslConst.vg_exe_ins_msg_table_name
    TableDict["TABLE"][AnscConst.DF_PIONEER_DRIVER_ID] = AnspConst.vg_exe_ins_msg_table_name
    TableDict["TABLE"][AnscConst.DF_LEGACY_ROLE_DRIVER_ID] = AnsrConst.vg_exe_ins_msg_table_name
    MenuName = TableDict["MENU_REST"][driver_id]
    MenuId = TableDict["MENU_ID"][driver_id]

    # loadtyable.pyで使用するCOLUMN_NAME_RESTを取得
    RestNameConfig = {}
    # あえて廃止にしている項目もあり、要確認が必要
    sql = "SELECT COL_NAME,COLUMN_NAME_REST FROM T_COMN_MENU_COLUMN_LINK WHERE MENU_ID = %s and DISUSE_FLAG = '0'"
    restcolnamerow = wsDb.sql_execute(sql, [MenuId])
    for row in restcolnamerow:
        RestNameConfig[row["COL_NAME"]] = row["COLUMN_NAME_REST"]

    ExecStsInstTableConfig = {}

    # 作業番号
    ExecStsInstTableConfig[RestNameConfig["EXECUTION_NO"]] = execution_no

    # ステータス
    if g.LANGUAGE == 'ja':
        sql = "SELECT EXEC_STATUS_NAME_JA AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
    else:
        sql = "SELECT EXEC_STATUS_NAME_EN AS NAME FROM T_ANSC_EXEC_STATUS WHERE EXEC_STATUS_ID = %s AND DISUSE_FLAG = '0'"
    rows = wsDb.sql_execute(sql, [execute_data["STATUS_ID"]])
    # マスタなので件数チェックしない
    row = rows[0]
    ExecStsInstTableConfig[RestNameConfig["STATUS_ID"]] = row["NAME"]

    # 入力データ/投入データ／出力データ/結果データ用zipデータ
    uploadfiles = {}
    if update_column_name == "FILE_INPUT" or update_column_name == "FILE_RESULT":
        if zip_tmp_save_path:
            uploadfiles = {RestNameConfig[update_column_name]: zip_tmp_save_path}
    # 実行中の場合
    if update_column_name == "FILE_INPUT":
        if execute_data["FILE_INPUT"]:
            ExecStsInstTableConfig[RestNameConfig["FILE_INPUT"]] = execute_data["FILE_INPUT"]  # 入力データ/投入データ

        ExecStsInstTableConfig[RestNameConfig["TIME_START"]] = execute_data['TIME_START'].strftime('%Y/%m/%d %H:%M:%S')
        # 終了時間が設定されていない場合がある
        if execute_data['TIME_END']:
            ExecStsInstTableConfig[RestNameConfig["TIME_END"]] = execute_data['TIME_END'].strftime('%Y/%m/%d %H:%M:%S')
        if "MULTIPLELOG_MODE" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["MULTIPLELOG_MODE"]] = execute_data["MULTIPLELOG_MODE"]
        if "LOGFILELIST_JSON" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["LOGFILELIST_JSON"]] = execute_data["LOGFILELIST_JSON"]

    # 実行終了の場合
    if update_column_name == "FILE_RESULT":
        if execute_data["FILE_RESULT"]:
            ExecStsInstTableConfig[RestNameConfig["FILE_RESULT"]] = execute_data["FILE_RESULT"]  # 出力データ/結果データ

        ExecStsInstTableConfig[RestNameConfig["TIME_END"]] = execute_data['TIME_END'].strftime('%Y/%m/%d %H:%M:%S')
        # MULTIPLELOG_MODEとLOGFILELIST_JSONが廃止レコードになっているので0にする
        if "MULTIPLELOG_MODE" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["MULTIPLELOG_MODE"]] = execute_data["MULTIPLELOG_MODE"]
        if "LOGFILELIST_JSON" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["LOGFILELIST_JSON"]] = execute_data["LOGFILELIST_JSON"]

    # その他の場合
    if update_column_name == "UPDATE":
        if "MULTIPLELOG_MODE" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["MULTIPLELOG_MODE"]] = execute_data["MULTIPLELOG_MODE"]
        if "LOGFILELIST_JSON" in execute_data:
            ExecStsInstTableConfig[RestNameConfig["LOGFILELIST_JSON"]] = execute_data["LOGFILELIST_JSON"]

    # 最終更新日時
    # MSG-00005対応で最終更新日時を取得
    sql = "SELECT LAST_UPDATE_TIMESTAMP FROM {} WHERE EXECUTION_NO = %s".format(TableDict["TABLE"][driver_id])
    rows = wsDb.sql_execute(sql, [execution_no])
    row = rows[0]
    ExecStsInstTableConfig[RestNameConfig["LAST_UPDATE_TIMESTAMP"]] = row['LAST_UPDATE_TIMESTAMP'].strftime('%Y/%m/%d %H:%M:%S.%f')

    parameters = {
        "parameter": ExecStsInstTableConfig,
        "type": "Update"
    }
    objmenu = load_table.loadTable(wsDb, MenuName)
    if db_update_need_no_jnl is True:
        objmenu.set_history_flg(False)
    retAry = objmenu.exec_maintenance(parameters, execution_no, "", False, False, True, record_file_paths=uploadfiles)
    result = retAry[0]
    if result is False:
        return False, str(retAry)
    else:
        return True, ""


def gbl_variable_unique_check(wsDb, gbl_name, menu_id="20104"):
    """グローバル変数の一意制約

    Args:
        wsDb:DB接クラス  DBConnectWs()
        gbl_name : グローバル変数名(GBL_xxxx)
        menu_id: メニューID. Defaults to "20104".

    Returns:
        bool, get_api_message(str)
    """
    # TABLE:  T_ANSC_GLOBAL_VAR / T_ANSC_GLOBAL_VAR_SENSITIVE
    # COLUMN: GBL_VARS_NAME_ID, VARS_NAME
    # 20104: グローバル変数管理 / 20113: グローバル変数（センシティブ）管理
    # menu_id: 20104 (入力：グローバル変数管理→検索対象：グローバル変数（センシティブ）管理)
    # menu_id: 20113 (入力：グローバル変数（センシティブ）→検索対象：管理グローバル変数管理)
    search_table = "T_ANSC_GLOBAL_VAR_SENSITIVE" \
        if menu_id == "20104" else "T_ANSC_GLOBAL_VAR"

    sql = f"SELECT GBL_VARS_NAME_ID, VARS_NAME FROM `{search_table}` WHERE DISUSE_FLAG = '0' AND VARS_NAME = %s"
    _rows = wsDb.sql_execute(sql, [gbl_name])
    g.applogger.debug(f"gbl_variable_unique_check: {sql} {gbl_name} {_rows}")

    if len(_rows) == 0:
        return True, ""
    else:
        # グローバル変数名「{}」は、グローバル変数管理で使用されています。(項番:{})
        # グローバル変数名「{}」は、グローバル変数(センシティブ)管理で使用されています。(項番:{})
        _row_ids = [_r.get("GBL_VARS_NAME_ID") for _r in _rows]
        status_code = 'MSG-11013' if menu_id == "20104" else  'MSG-11014'
        msg_args = [gbl_name, ", ".join(_row_ids)]
        msg = g.appmsg.get_api_message(status_code, msg_args)
        return False, msg