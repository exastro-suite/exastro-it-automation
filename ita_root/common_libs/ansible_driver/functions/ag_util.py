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
import json

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.AnslConstClass import AnslConst
from common_libs.ansible_driver.classes.AnspConstClass import AnspConst
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst
from common_libs.ansible_driver.functions.util import get_AnsibleDriverShellPath
from common_libs.ansible_driver.functions.util import getAnsibleExecutDirPath
from common_libs.ansible_driver.functions.util import getDataRelayStorageDir
from common_libs.ansible_driver.functions.util import getFileupLoadColumnPath
from common_libs.ansible_driver.functions.util import getDataRelayStorageDir
from common_libs.ansible_driver.functions.template_render import TemplateRender
from common_libs.common.storage_access import storage_base, storage_read, storage_write, storage_base


"""
  Ansible Agent共通モジュール
"""
def getExecDevTemplateUploadDirPath():
    """
      環境構築定義テンプレートバスを取得する。
      Arguments:
        なし
      Returns:
        作業管理結果データディレクトリバス
    """
    return getDataRelayStorageDir() + "/uploadfiles/20110/template_file"

def getAG_AGOutDirPath(ansConstObj, execution_no):
    """
      ansible-runnerのansible agent側の結果データ(out)パスを取得
      Arguments:
        ansConstObj:  ansible共通定数オブジェクト
        execution_no: 作業番号
      Returns:
        ansible-runnerのansible agent側の結果データ(out)パス
    """
    return get_AGAnsibleExecutDirPath(ansConstObj, execution_no)

def getAG_AGProjectPath(ansConstObj, execution_no):
    """
      ansible-runnerのansible agent側のprojectパスを取得
      Arguments:
        ansConstObj:  ansible共通定数オブジェクト
        execution_no: 作業番号
      Returns:
        ansible-runnerのprojectパス
    """
    return get_AGAnsibleExecutDirPath(ansConstObj, execution_no)

def getAG_ITARunnerShellPath(ansConstObj, execution_no):
    """
      ansible-runner用のita側のshell格納パスを取得
      Arguments:
        ansConstObj:  ansible共通定数オブジェクト
        execution_no: 作業番号
      Returns:
        ansible-runner用のshell格納パス
    """
    return "{}/runner_executable_files".format(getAnsibleExecutDirPath(ansConstObj, execution_no))

def getAG_ITABuilderShellPath(ansConstObj, execution_no):
    """
      ansible-Builder用のita側のshell格納パスを取得
      Arguments:
        ansConstObj:  ansible共通定数オブジェクト
        execution_no: 作業番号
      Returns:
        ansible-Builder用のshell格納パス
    """
    return "{}/builder_executable_files".format(getAnsibleExecutDirPath(ansConstObj, execution_no))

def getAG_AGOUTDirPath():
    """
      ansible-runnerのansible agent側のproject内で使用する出力用パスを取得
      Arguments:
        なし
      Returns:
        ansible-runnerの出力用パス
    """
    return "/outdir"

def CreateAG_ITABuilderShellFiles(objDBCA, AnscObj, out_dir, execution_no, movemrnt_row):
    """
      ansible-Builderの実行に必要なshellを作成する。
      Arguments:
        objDBCA:      DBインスタンス
        AnscObj:      ansible共通定数オブジェクト
        out_dir:      shell出力先ディレクトリ
        execution_no: 作業番号
        movement_row: Movement対象レコード情報
      Returns:
      Returns:
        True:  正常
        False: 異常
    """
    # Movement一覧に紐づけられている実行環境管理のレコード取得
    sql = "SELECT * FROM T_ANSC_EXECDEV WHERE ROW_ID = %s AND DISUSE_FLAG = '0'"
    rows = objDBCA.sql_execute(sql, bind_value_list=[movemrnt_row['AG_EXECUTION_ENVIRONMENT_NAME']])
    if len(rows) == 0:
        msgstr = g.appmsg.get_api_message("MSG-10960", [movemrnt_row['AG_EXECUTION_ENVIRONMENT_NAME']])
        return False, msgstr
    execdev_row = rows[0]
    # Ansible Egent 実行環境構築方法がITA以外の場合
    if execdev_row['BUILD_TYPE'] != AnscConst.DF_AG_BUILD_TYPE_ITA:
        return True, ""
    # 実行環境に紐づくパラメメータシートの情報取得
    # row['EXECUTION_ENVIRONMENT_ID']の中身は"パラメータシートテーブル,パラメータシートテーブルのROW_ID"
    key = execdev_row['EXECUTION_ENVIRONMENT_ID'].split(',')
    if len(key) != 2:
        msgstr = g.appmsg.get_api_message("MSG-10961", [execdev_row['ROW_ID'], execdev_row['EXECUTION_ENVIRONMENT_ID']])
        return False, msgstr
    sheet_table_name = key[0]
    row_id = key[1]

    # 該当パラメータシートに紐づくテーブルがら登録値取得
    sql = "SELECT * FROM `{}` WHERE ROW_ID = '{}' AND DISUSE_FLAG = '0' ".format(sheet_table_name, row_id)
    rows = objDBCA.sql_execute(sql, bind_value_list=[])
    if len(rows) == 0:
        lang = g.get('LANGUAGE')
        lang_menu_name_column = {}
        lang_menu_name_column['ja'] = "MENU_NAME_JA"
        lang_menu_name_column['en'] = "MENU_NAME_EN"
        sql = """
              SELECT {} AS MENU_NAME FROM T_COMN_MENU
              WHERE MENU_ID in (
                SELECT MENU_ID FROM T_MENU_TABLE_LINK WHERE TABLE_NAME = '{}'
                               )
              """.format(lang_menu_name_column[lang], sheet_table_name)
        tblrows = objDBCA.sql_execute(sql, bind_value_list=[])
        if len(tblrows) != 0:
            sheet_name = tblrows[0]['MENU_NAME']
        else:
            sheet_name = sheet_table_name
        msgstr = g.appmsg.get_api_message("MSG-10962", [sheet_name, row_id])
        return False, msgstr
    row = rows[0]
    uploadfiledir_uuid = row['ROW_ID']
    item_array = json.loads(row['DATA_JSON'])

    # 該当パラメータシートのmenu_idを取得
    sql = "SELECT * FROM T_MENU_TABLE_LINK WHERE TABLE_NAME = %s AND DISUSE_FLAG = '0'"
    rows = objDBCA.sql_execute(sql, bind_value_list=[sheet_table_name])
    if len(rows) == 0:
      msgstr = g.appmsg.get_api_message("MSG-10963", [sheet_table_name])
      return False, msgstr
    row = rows[0]

    # /strage/{{org id}}/{{workspace id}}/uploadfiles//メニューID
    strage_menu_id = row['MENU_ID']

    # 該当パラメータシートのパラメータシート項目作成情報を取得
    sql = """
          SELECT
            TBL_4.*
          FROM
            T_MENU_COLUMN TBL_4
          WHERE
            TBL_4.MENU_CREATE_ID IN (
                                      SELECT
                                        TBL_3.MENU_CREATE_ID
                                      FROM
                                        T_MENU_DEFINE TBL_3
                                      WHERE
                                        TBL_3.MENU_NAME_REST IN (
                                                                  SELECT
                                                                    TBL_1.MENU_NAME_REST
                                                                  FROM
                                                                    T_COMN_MENU TBL_1
                                                                    LEFT JOIN T_MENU_TABLE_LINK TBL_2 ON (TBL_1.MENU_ID = TBL_2.MENU_ID)
                                                                  WHERE
                                                                    TBL_2.TABLE_NAME = %s AND
                                                                    TBL_2.DISUSE_FLAG = '0' AND
                                                                    TBL_1.DISUSE_FLAG = '0'
                                                                ) AND
                                        TBL_3.DISUSE_FLAG = '0'
                                    ) AND
            TBL_4.DISUSE_FLAG = '0'
            """.format(sheet_table_name)
    rows = objDBCA.sql_execute(sql, bind_value_list=[sheet_table_name])
    if len(rows) == 0:
        msgstr = g.appmsg.get_api_message("MSG-10964", [sheet_table_name])
        return False, msgstr
    # 実行環境バラメータ定義用のパラメータシートか判定
    hit = False
    j2_item_array = {}
    for column_row in rows:
      if column_row['COLUMN_NAME_REST'] == "execution_environment_name":
        hit = True
      if column_row['COLUMN_NAME_REST'] in item_array:
        j2_item_array[column_row['COLUMN_NAME_JA']] = item_array[column_row['COLUMN_NAME_REST']]
        # None対応
        if not j2_item_array[column_row['COLUMN_NAME_JA']]:
            j2_item_array[column_row['COLUMN_NAME_JA']] = ""
        if column_row['COLUMN_CLASS'] in ('1', '2', '3'): # SingleTextColumn, MultiTextColumn NumColumn
            pass
        elif column_row['COLUMN_CLASS'] in ('9'): # FileUploadColumn
            if item_array[column_row['COLUMN_NAME_REST']]:
                path = getFileupLoadColumnPath(strage_menu_id, column_row['COLUMN_NAME_REST'])
                src_upload_file = "{}/{}/{}".format(path, uploadfiledir_uuid, item_array[column_row['COLUMN_NAME_REST']])
                dest_uoload_file = "{}/{}_{}".format(out_dir, column_row['COLUMN_NAME_REST'], item_array[column_row['COLUMN_NAME_REST']])
                shutil.copy(src_upload_file, dest_uoload_file)
                j2_item_array[column_row['COLUMN_NAME_JA']] = os.path.basename(dest_uoload_file)
            else:
                j2_item_array[column_row['COLUMN_NAME_JA']] = ""
        else:
            msgstr = g.appmsg.get_api_message("MSG-10965", [column_row['COLUMN_CLASS']])
            return False, msgstr
    if hit is not True:
        msgstr = g.appmsg.get_api_message("MSG-10966", [column_row['COLUMN_CLASS']])
        return False, msgstr

    # 実行環境定義テンプレート管理の情報取得
    sql = "SELECT * FROM T_ANSC_EXECDEV_TEMPLATE_FILE WHERE ROW_ID = %s AND DISUSE_FLAG = '0'"
    rows = objDBCA.sql_execute(sql, bind_value_list=[execdev_row['TEMPLATE_ID']])
    if len(rows) == 0:
        msgstr = g.appmsg.get_api_message("MSG-10967", [execdev_row['ROW_ID'], execdev_row['TEMPLATE_ID']])
        return False, msgstr
    row = rows[0]
    if not row['TEMPLATE_FILE']:
        msgstr = g.appmsg.get_api_message("MSG-10968", [execdev_row['ROW_ID']])
        return False, msgstr

    template_path ="{}/{}".format(getExecDevTemplateUploadDirPath(), row['ROW_ID'])
    # テンプレートからexecution-environment.ymlを生成
    template_file = row['TEMPLATE_FILE']
    value = TemplateRender(template_path, template_file, j2_item_array)
    out_file = "{}/{}".format(out_dir, "execution-environment.yml")
    with open(out_file, mode="w") as f:
        f.write(value)

    # builder.sh生成
    template_file = "ky_ansible_builder_shell.j2"
    item = {}
    # item["PROJECT_BASE_DIR"] = "${PROJECT_BASE_DIR}/project/builder_executable_files"

    item['optional_parameters'] = movemrnt_row['AG_BUILDER_OPTIONS']
    item['tag_name'] = execdev_row['TAG_NAME']
    # None対応
    if not item['optional_parameters']:
        item['optional_parameters'] = ""
    if not item['tag_name']:
        item['tag_name'] = ""
    template_file_path = get_AnsibleDriverShellPath()
    value = TemplateRender(template_file_path, template_file, item)
    out_file = "{}/builder.sh".format(out_dir)

    with open(out_file, mode="w") as f:
        f.write(value)

    return True, ""


def CreateAG_ITARunnerShellFiles(objDBCA, AnscObj, out_dir, execution_no, movemrnt_row):
    """
      ansible-runnerの実行に必要なshellを作成する。
      Arguments:
        objDBCA:      DBインスタンス
        AnscObj:      ansible共通定数オブジェクト
        out_dir:      shell出力先ディレクトリ
        execution_no: 作業番号
        movement_row: Movement対象レコード情報
      Returns:
        True: 正常
    """
    # Movement一覧に紐づけられている実行環境管理のレコード取得
    sql = "SELECT * FROM T_ANSC_EXECDEV WHERE ROW_ID = %s AND DISUSE_FLAG = '0'".format(AnscObj.vg_ansible_pattern_listDB)
    rows = objDBCA.sql_execute(sql, bind_value_list=[movemrnt_row['AG_EXECUTION_ENVIRONMENT_NAME']])
    if len(rows) == 0:
        msgstr = g.appmsg.get_api_message("MSG-10960", [movemrnt_row['AG_EXECUTION_ENVIRONMENT_NAME']])
        return False, msgstr
    execdev_row = rows[0]
    ee_tag = execdev_row['TAG_NAME']

    project_path = getAG_AGProjectPath(AnscObj, execution_no)
    item = {}
    item["EXECUTION_NO"] = execution_no
    item["TAG_NAME"] = ee_tag
    # item["PROJECT_BASE_DIR"] = "${PROJECT_BASE_DIR}"
    # item['OUT_DIR'] = "${PROJECT_BASE_DIR}" + "/"
    template_file_path = get_AnsibleDriverShellPath()

    # start.sh生成
    template_file = "ky_ansible_runner_start_shell_template.j2"
    value = TemplateRender(template_file_path, template_file, item)
    out_file = "{}/start.sh".format(out_dir)
    with open(out_file, mode="w") as f:
        f.write(value)

    # stop.sh生成
    template_file = "ky_ansible_runner_stop_shell_template.j2"
    value = TemplateRender(template_file_path, template_file, item)
    out_file = "{}/stop.sh".format(out_dir)
    with open(out_file, mode="w") as f:
        f.write(value)

    # alive.sh生成
    template_file = "ky_ansible_runner_alive_shell_template.j2"
    value = TemplateRender(template_file_path, template_file, item)
    out_file = "{}/alive.sh".format(out_dir)
    with open(out_file, mode="w") as f:
        f.write(value)

    return True, ""

def Replace_HostVrasFilepath(rsplase_path, file_path,insert_path=""):
    """
      ファイルバス系のホスト変数の具体値を加工する
      /exastro/org_id/workdspace_id/driver/ansible/deiverid/in/xx/xxxxx
      ↓
      xx/xxxx
      Arguments:
        rsplase_path: splitするパス名      "/"は不要
        file_path:    ファイルバス
        insert_path:  inの前に付加かるバス  "/"は不要
      Returns:
        ファイルバス系のホスト変数の具体値を加工したパス
    """
    ary = file_path.split("/" + rsplase_path + "/")
    if len(insert_path):
        insert_path = "/" + insert_path + "/"
    ret_file_path = "{}{}".format(insert_path,ary[1])
    return ret_file_path

def get_AGStatusFilepath(ansConstObj, execute_no):
    """
      ansibe agent作業状態通知受信ファイルパス取得
      Arguments:
        ansConstObj: ansible共通定数オブジェクト
        execute_no: 作業番号
      Returns:
        ansibe agent作業状態通知受信ファイルパス
    """
    return "{}/tmp/ansible_agent_status_file.txt".format(getAnsibleExecutDirPath(ansConstObj, execute_no))

def get_AGChildProcessRestartCountFilepath(ansConstObj, execute_no):
    """
      ansibe agent用 ansible execution 子プロセス再起動カウントファイルパス取得
      Arguments:
        ansConstObj: ansible共通定数オブジェクト
        execute_no: 作業番号
      Returns:
        ansibe agent作業状態通知受信ファイルパス
    """
    return "{}/tmp/Child_Process_restart_count.txt".format(getAnsibleExecutDirPath(ansConstObj, execute_no))

def get_AGAnsibleExecutDirPath(ansConstObj, execute_no):
    """
      ansibe作業実行ディレクトリパス取得
      Arguments:
        ansConstObj: ansible共通定数オブジェクト
        execute_no: 作業番号
      Returns:
        ansibe作業実行ディレクトリパスを取得
    """
    return getDataRelayStorageDir() + "/driver/ag_ansible_execution/{}/{}".format(ansConstObj.vg_OrchestratorSubId_dir, execute_no)
