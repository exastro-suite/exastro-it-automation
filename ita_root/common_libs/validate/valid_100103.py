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

from flask import g
from common_libs.cicd.functions.util import getColumnValueFromOptionData
from common_libs.cicd.classes.cicd_definition import TD_SYNC_STATUS_NAME_DEFINE, TD_B_CICD_MATERIAL_TYPE_NAME, TD_C_PATTERN_PER_ORCH
from common_libs.cicd.functions.local_functions import MatlLinkColumnValidator1, MatlLinkColumnValidator2, MatlLinkColumnValidator5

def external_valid_menu_before(objdbca, objtable, option):
    """
    メニューバリデーション(登録/更新)
    ARGS:
        objdbca :DB接続クラスインスタンス
        objtabl :メニュー情報、カラム紐付、関連情報
        option :パラメータ、その他設定値
    RETRUN:
        retBoo :True/ False
        msg :エラーメッセージ
        option :受け取ったもの
    """
    PkeyID = option.get('uuid')
    if not PkeyID:
        # 新規の場合、Noneなので固定値設定
        PkeyID = "new record"
    retBool = True
    ExtStMId = None
    MatlListRow = {}
    msg = ''
    # 各カラムの入力データを取得
    ColValue, RestNameConfig = getColumnValueFromOptionData(objdbca, objtable, option)

    # 資材パス必須入力チェック
    if not ColValue['MATL_ROW_ID']:
        # 必須入力です。(項目：資材パス)
        status_code = "MSG-90010"
        msg_args = []
        if len(msg) != 0:
            msg += "\n"
        msg += g.appmsg.get_api_message(status_code, msg_args)
        retBool = False

    else:
        if option["cmd_type"] in ("Register", "Update", "Discard", "Restore"):
            # 隠しカラムの設定:　リモートリポジトリ
            # 選択されている資材よりリモートリポジトリを取得し設定
            sql = "SELECT * FROM T_CICD_MATL_LIST WHERE DISUSE_FLAG='0' AND MATL_ROW_ID = %s"
            rows = objdbca.sql_execute(sql, [ColValue['MATL_ROW_ID']])
            if len(rows) == 0:
                # 資材パスからリモートリポジトリを特定できませんでした。
                status_code = "MSG-90007"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False

            else:
                # リモートリポジトリのPkeyを設定・更新
                MatlListRow = rows[0]
                option["entry_parameter"]["parameter"][RestNameConfig["REPO_ROW_ID"]] = MatlListRow["REPO_ROW_ID"]

    if retBool is True:
        # 紐付先素材集タイプ毎のOS種別・対話種別未入力チェック
        if ColValue['MATL_TYPE_ROW_ID'] in (TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_LEGACY,       # Legacy/Playbook素材集
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_ROLE,         # LegacyRole/ロールパッケージ管理
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_CONTENT,      # Ansible共通/ファイル管理
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_TEMPLATE,     # Ansible共通/テンプレート管理
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE,       # Terraform/Module素材
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_POLICY,       # Terraform/Policy管理
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE_CLI):  # Terraform-CLI/Module素材
            # OS種別未入力チェック
            if ColValue['OS_TYPE_ID']:
                # 資材紐付先タイプがAnsible-Pioneerコンソール/対話ファイル素材集以外の場合は入力不要な項目です。(項目:OS種別)
                status_code = "MSG-90004"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False
            # 対話種別未入力チェック
            if ColValue['DIALOG_TYPE_ID']:
                # 資材紐付先タイプがAnsible-Pioneerコンソール/対話ファイル素材集以外の場合は入力不要な項目です。(項目:対話種別)
                status_code = "MSG-90005"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False

        # 紐付先素材集タイプ毎のOS種別・対話種別入力組み合わせ重複チェック
        if ColValue['MATL_TYPE_ROW_ID'] in (TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_PIONEER):
            if ColValue['OS_TYPE_ID'] and ColValue['DIALOG_TYPE_ID']:
                sql = "SELECT MATL_LINK_ROW_ID FROM T_CICD_MATL_LINK WHERE DISUSE_FLAG='0' AND DIALOG_TYPE_ID = %s AND OS_TYPE_ID = %s AND MATL_LINK_ROW_ID <> %s "
                rows = objdbca.sql_execute(sql, [ColValue['DIALOG_TYPE_ID'], ColValue['OS_TYPE_ID'], PkeyID])
                if len(rows) > 0:
                    # 組み合わせが不正です。
                    status_code = "MSG-00006"
                    msg_args = [[RestNameConfig.get('DIALOG_TYPE_ID'), RestNameConfig.get('OS_TYPE_ID')], PkeyID]
                    if len(msg) != 0:
                        msg += "\n"
                    msg += g.appmsg.get_api_message(status_code, msg_args)
                    retBool = False

        # 紐付先素材集タイプ毎の変数定義未入力チェック
        if ColValue['MATL_TYPE_ROW_ID'] in (TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_LEGACY,       # Legacy/Playbook素材集
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_PIONEER,      # Pioneer/対話ファイル素材集
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_ROLE,         # LegacyRole/ロールパッケージ管理
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_CONTENT,      # Ansible共通/ファイル管理
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE,       # Terraform/Module素材
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_POLICY,       # Terraform/Policy管理
                                            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE_CLI):  # Terraform-CLI/Module素材
            if ColValue['TEMPLATE_FILE_VARS_LIST']:
                # MSG-90003 資材紐付先タイプがAnsible共通コンソール/テンプレート管理以外の場合は入力不要な項目です。(項目:変数定義)
                status_code = "MSG-90003"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False

    # 資材パスと紐付先資材タイプの組合せチェック
    if retBool is True:
        retBool, msg = MatlLinkColumnValidator2(ColValue['MATL_TYPE_ROW_ID'], MatlListRow['MATL_FILE_TYPE_ROW_ID'], ColValue['REPO_ROW_ID'], PkeyID, msg)

    # 資材紐付管理必須入力チェック処理
    if retBool is True:
        retBool, msg = MatlLinkColumnValidator1(ColValue, PkeyID, msg)

    # デリバリオペレーション確認
    if retBool is True:
        if ColValue['DEL_OPE_ID']:
            sql = "SELECT * FROM T_COMN_OPERATION WHERE DISUSE_FLAG='0' AND OPERATION_ID = %s"
            rows = objdbca.sql_execute(sql, [ColValue['DEL_OPE_ID']])
            if len(rows) == 0:
                # オペレーションを特定できませんでした。
                status_code = "MSG-90049"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False

    # デリバリMOVEMENT_ID確認
    if retBool is True:
        if ColValue['DEL_MOVE_ID']:
            sql = "SELECT COUNT(*) AS MOVEMENT_COUNT, ITA_EXT_STM_ID FROM T_COMN_MOVEMENT WHERE DISUSE_FLAG='0' AND MOVEMENT_ID = %s"
            rows = objdbca.sql_execute(sql, [ColValue['DEL_MOVE_ID']])
            if len(rows) == 0:
                # Movementを特定できませんでした。
                status_code = "MSG-90048"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False
            else:
                row = rows[0]
                if row['MOVEMENT_COUNT'] == 1:
                    ExtStMId = row['ITA_EXT_STM_ID']
                    # 資材紐付管理 紐付先資材タイプとMovementタイプの組み合わせチェック
                    retBool, msg = MatlLinkColumnValidator5(ColValue['REPO_ROW_ID'],
                                                            PkeyID,
                                                            ExtStMId,
                                                            ColValue['MATL_TYPE_ROW_ID'],
                                                            msg)

    if retBool is True:
        # 同期状態・同期エラー情報・同期時刻を更新
        if option["cmd_type"] in ("Register", "Update", "Restore"):
            option["entry_parameter"]["parameter"][RestNameConfig["SYNC_STATUS_ROW_ID"]] = TD_SYNC_STATUS_NAME_DEFINE.STS_NONE
            option["entry_parameter"]["parameter"][RestNameConfig["SYNC_ERROR_NOTE"]] = None
            option["entry_parameter"]["parameter"][RestNameConfig["SYNC_LAST_TIME"]] = None
            option["entry_parameter"]["parameter"][RestNameConfig["DEL_ERROR_NOTE"]] = None
            option["entry_parameter"]["parameter"][RestNameConfig["DEL_EXEC_INS_NO"]] = None
            option["entry_parameter"]["parameter"][RestNameConfig["DEL_MENU_NO"]] = None
            if ExtStMId:
                option["entry_parameter"]["parameter"][RestNameConfig["DEL_MENU_NO"]] = TD_C_PATTERN_PER_ORCH.C_CHECK_OPERATION_STATUS_MENU_NAME[ExtStMId]
    return retBool, msg, option,
