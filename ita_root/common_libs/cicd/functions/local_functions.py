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
import re

from common_libs.cicd.classes.cicd_definition import *


def MatlLinkColumnValidator1(ColumnValueArray, MatlLinkId, retStrBody):
    retBool = True

    # 紐付け先 素材集タイプ毎の必須入力チェック
    if ColumnValueArray['MATL_TYPE_ROW_ID'] == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_LEGACY:       # Playbook素材集
        pass

    if ColumnValueArray['MATL_TYPE_ROW_ID'] == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_PIONEER:      # 対話ファイル素材集
        if not ColumnValueArray['DIALOG_TYPE_ID']:
            # 対話種別
            ColumnName = g.appmsg.get_api_message("MSG-90044", [])
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)
            # 紐付先資材タイプがAnsible-Pioneerコンソール/対話ファイル素材集の場合は必須項目です。(項目:{}) (資材紐付 項番:{})
            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90024", [ColumnName, MatlLinkId]))
            retBool = False
        if not ColumnValueArray['OS_TYPE_ID']:
            # OS種別
            ColumnName = g.appmsg.get_api_message("MSG-90045", [])
            # 紐付先資材タイプがAnsible-Pioneerコンソール/対話ファイル素材集の場合は必須項目です。(項目:{}) (資材紐付 項番:{})
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)
            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90024", [ColumnName, MatlLinkId]))
            retBool = False

    if ColumnValueArray['MATL_TYPE_ROW_ID'] == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_ROLE:         # ロールパッケージ管理
        pass

    if ColumnValueArray['MATL_TYPE_ROW_ID'] == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_CONTENT:      # ファイル管理
        if ColumnValueArray['MATL_LINK_NAME']:
            keyFilter = r"^CPF_[0-9a-zA-Z_]*$"
            ret = re.findall(keyFilter, ColumnValueArray['MATL_LINK_NAME'])
            if len(ret) != 1:
                # 紐付先資材タイプがAnsible共通コンソール/ファイル管理の場合、紐付先資材名は正規表記(/^CPF_[_a-zA-Z0-9]+$/)に一致するデータを入力してください。(資材紐付   項番:{})
                if len(retStrBody) > 0:
                    retStrBody = "%s\n" % (retStrBody)
                retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90021", [MatlLinkId]))
                retBool = False

    if ColumnValueArray['MATL_TYPE_ROW_ID'] == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_TEMPLATE:     # テンプレート管理
        if ColumnValueArray['MATL_LINK_NAME']:
            keyFilter = r"^TPF_[0-9a-zA-Z_]*$"
            ret = re.findall(keyFilter, ColumnValueArray['MATL_LINK_NAME'])
            if len(ret) != 1:
                # 紐付先資材タイプがAnsible共通コンソール／テンプレート管理の場合の紐付先資材名は正規表記(/^TPF_[_a-zA-Z0-9]+/)に一致するデータを入力してください。
                if len(retStrBody) > 0:
                    retStrBody = "%s\n" % (retStrBody)
                retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90022", [MatlLinkId]))
                retBool = False

    if ColumnValueArray['MATL_TYPE_ROW_ID'] in (TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE,       # Module素材
                                                TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE_CLI):   # Terraform-CLI/Module素材
        pass

    if ColumnValueArray['MATL_TYPE_ROW_ID'] == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_POLICY:       # Policy管理
        if ColumnValueArray['MATL_LINK_NAME']:
            keyFilter = r"^[0-9a-zA-Z_\-]+$"
            ret = re.findall(keyFilter, ColumnValueArray['MATL_LINK_NAME'])
            if len(ret) != 1:
                # 紐付先資材タイプがTerraformコンソール/Policy管理の場合、紐付先資材名は正規表記(/^[a-zA-Z0-9_\-]+/)に一致するデータを入力してください。(資材紐付 項番:{})";
                if len(retStrBody) > 0:
                    retStrBody = "%s\n" % (retStrBody)
                retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90040", [MatlLinkId]))
                retBool = False

    # オペレーションIDとMovementの未入力チェック
    ColumnNameOpe = g.appmsg.get_api_message("MSG-90046", [])
    ColumnNameMove = g.appmsg.get_api_message("MSG-90047", [])
    if ColumnValueArray['DEL_OPE_ID']:
        if not ColumnValueArray['DEL_MOVE_ID']:
            # オペレーションが選択されている場合は必須項目です。(項目:{}) (資材紐付管理 項番:{})
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)
            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90023", [ColumnNameMove, MatlLinkId]))
            retBool = False

    if ColumnValueArray['DEL_MOVE_ID']:
        if not ColumnValueArray['DEL_OPE_ID']:
            # Movementが選択されている場合は必須項目です。(項目:{}) (資材紐付管理 項番:{})
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)
            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90025", [ColumnNameOpe, MatlLinkId]))
            retBool = False

    return retBool, retStrBody


def MatlLinkColumnValidator2(MatlTypeId, MatlFileTypeId, RepoId, MatlLinkId, retStrBody):
    if MatlTypeId in [
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_LEGACY,
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_PIONEER,
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_CONTENT,
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_TEMPLATE,
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE,
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_POLICY,
            TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE_CLI
    ]:
        if MatlFileTypeId != TD_B_CICD_MATERIAL_FILE_TYPE_NAME.C_MATL_FILE_TYPE_ROW_ID_FILE:
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)
            # 紐付先資材タイプがAnsible-LegacyRoleコンソール/パッケージ管理以外の場合、資材パスはファイルパスを選択して下さい。(リモートリポジトリ 項番:{} 資材紐付 項番:{})
            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90036", [RepoId, MatlLinkId]))
            return False, retStrBody

    elif MatlTypeId == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_ROLE:
        if MatlFileTypeId != TD_B_CICD_MATERIAL_FILE_TYPE_NAME.C_MATL_FILE_TYPE_ROW_ID_ROLES:
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)

            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90035", [RepoId, MatlLinkId]))
            return False, retStrBody

    return True, retStrBody


def MatlLinkColumnValidator3(row, retStrBody):

    retBool = True

    # リモートリポジトリ管理が廃止レコードか判定
    if row['REPO_ROW_ID'] is not None and len(row['REPO_ROW_ID']) > 0:
        if row['REPO_DISUSE_FLAG'] is None or row['REPO_DISUSE_FLAG'] == '1':
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)

            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90028", [row['MATL_LINK_ROW_ID'], row['REPO_ROW_ID']]))
            retBool = False

    # 資材一覧が廃止レコードか判定
    if row['MATL_ROW_ID'] is not None and len(row['MATL_ROW_ID']) > 0:
        if row['MATL_DISUSE_FLAG'] is None or row['MATL_DISUSE_FLAG'] == '1':
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)

            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90029", [row['MATL_LINK_ROW_ID'], row['MATL_ROW_ID']]))
            retBool = False

    # オペレーションIDとMovemnetIDが両方設定されている場合に オペレーションIDとMovemnetIDが廃止レコードか判定
    if row['DEL_OPE_ID'] is not None and len(row['DEL_OPE_ID']) > 0 and row['DEL_MOVE_ID'] is not None and len(row['DEL_MOVE_ID']) > 0:
        if row['OPE_DISUSE_FLAG'] is None or row['OPE_DISUSE_FLAG'] == '1':
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)

            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90033", [row['MATL_LINK_ROW_ID'], row['DEL_OPE_ID']]))
            retBool = False

        if row['PTN_DISUSE_FLAG'] is None or row['PTN_DISUSE_FLAG'] == '1':
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)

            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90034", [row['MATL_LINK_ROW_ID'], row['DEL_MOVE_ID']]))
            retBool = False

    # 紐付先資材タイプが対話ファイル素材集の場合 対話種別とOS種別の廃止レコードか判定
    if row['MATL_TYPE_ROW_ID'] == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_PIONEER:
        if row['DALG_DISUSE_FLAG'] is None or row['DALG_DISUSE_FLAG'] == '1':
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)

            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90037", [row['MATL_LINK_ROW_ID'], row['M_DIALOG_TYPE_ID']]))
            retBool = False

        if row['OS_DISUSE_FLAG'] is None or row['OS_DISUSE_FLAG'] == '1':
            if len(retStrBody) > 0:
                retStrBody = "%s\n" % (retStrBody)

            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90038", [row['MATL_LINK_ROW_ID'], row['M_OS_TYPE_ID']]))
            retBool = False

    return retBool, retStrBody


def MatlLinkColumnValidator5(RepoId, MatlLinkId, ExtStnId, MatlTypeId, retStrBody):

    if not ExtStnId:
        return True, retStrBody

    # Playbook素材集
    if MatlTypeId == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_LEGACY:
        if ExtStnId != TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_LEGACY:
            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90039", [RepoId, MatlLinkId]))
            return False, retStrBody

    # 対話ファイル素材集
    elif MatlTypeId == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_PIONEER:
        if ExtStnId != TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_PIONEER:
            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90039", [RepoId, MatlLinkId]))
            return False, retStrBody

    # ロールパッケージ管理
    elif MatlTypeId == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_ROLE:
        if ExtStnId != TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_ROLE:
            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90039", [RepoId, MatlLinkId]))
            return False, retStrBody

    # ファイル管理、または、テンプレート管理
    elif MatlTypeId in [TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_CONTENT, TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_TEMPLATE]:
        if ExtStnId not in [TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_LEGACY, TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_PIONEER, TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_ROLE]:
            # 選択されている紐付先資材タイプとMovementの組み合わせが不正です。(リモートリポジトリ 項番:{} 資材紐付 項番:{})
            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90039", [RepoId, MatlLinkId]))
            return False, retStrBody

    # Module素材、または、Policy管理
    elif MatlTypeId in [TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE, TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_POLICY]:
        if ExtStnId != TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_TERRAFORM:
            # 選択されている紐付先資材タイプとMovementの組み合わせが不正です。(リモートリポジトリ 項番:{} 資材紐付 項番:{})
            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90039", [RepoId, MatlLinkId]))
            return False, retStrBody

    # CLI Module素材
    elif MatlTypeId == TD_B_CICD_MATERIAL_TYPE_NAME.C_MATL_TYPE_ROW_ID_MODULE_CLI:
        if ExtStnId != TD_C_PATTERN_PER_ORCH.C_EXT_STM_ID_TERRAFORM_CLI:
            # 選択されている紐付先資材タイプとMovementの組み合わせが不正です。(リモートリポジトリ 項番:{} 資材紐付 項番:{})
            retStrBody = "%s%s" % (retStrBody, g.appmsg.get_api_message("MSG-90039", [RepoId, MatlLinkId]))
            return False, retStrBody

    return True, retStrBody
