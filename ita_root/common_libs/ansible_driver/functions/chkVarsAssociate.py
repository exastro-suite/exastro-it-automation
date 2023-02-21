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


def chkVarsAssociate(objdbca, in_vars_link_id, in_col_seq_comb_id):
    retBool = True
    retStrBody = ""
    out_pattern_id = None
    out_vars_link_id = in_vars_link_id
    out_col_seq_comb_id = in_col_seq_comb_id
    # 代入値値自動登録用Movement+変数名
    # 2 系Role Movement-変数紐付
    query_step1 = "SELECT" \
                  + " TBL_A.MVMT_VAR_LINK_ID," \
                  + " TBL_A.MOVEMENT_ID," \
                  + " COUNT(*) AS VARS_LINK_ID_CNT," \
                  + " TBL_A.VARS_ATTRIBUTE_01" \
                  + " FROM" \
                  + " V_ANSR_VAL_VARS_LINK TBL_A" \
                  + " WHERE" \
                  + " TBL_A.MVMT_VAR_LINK_ID = %s AND" \
                  + " TBL_A.DISUSE_FLAG = '0'"

    aryForBind = {}
    aryForBind['MVMT_VAR_LINK_ID'] = in_vars_link_id
    row = objdbca.sql_execute(query_step1, bind_value_list=[aryForBind['MVMT_VAR_LINK_ID']])
    # レコードが存在するか確認
    if len(row) != 0:
        if row[0]['VARS_LINK_ID_CNT'] == 0:
            # Movement-ロール紐付に登録されているロールまたはロールパッケージに変数が未登録です。
            retStrBody = g.appmsg.get_api_message("MSG-10390")
            retBool = False
        if row[0]['VARS_LINK_ID_CNT'] == 1:
            out_pattern_id = row[0]['MOVEMENT_ID']
            out_vars_link_id = row[0]['MVMT_VAR_LINK_ID']
            # 変数タイプ VARS_ATTRIBUTE_01
            # 1:一般変数
            # 2:複数具体値変数
            # 3:多次元変数
            if row[0]['VARS_ATTRIBUTE_01'] == "1" or row[0]['VARS_ATTRIBUTE_01'] == "2":
                if in_col_seq_comb_id:
                    # メンバー変数は入力できません。
                    retStrBody = g.appmsg.get_api_message("MSG-10434", [])
                    return False, retStrBody
            elif row[0]['VARS_ATTRIBUTE_01'] == "3":
                out_col_seq_comb_id = in_col_seq_comb_id
                if not in_col_seq_comb_id:
                    # メンバー変数が入力されていません。
                    retStrBody = g.appmsg.get_api_message("MSG-10435", [])
                    return False, retStrBody

                # 変数とメンバー変数の組合せ判定
                query_step2 = "SELECT" \
                    + " COUNT(*) AS MEMBER_CNT," \
                    + " TBL_A.MVMT_VAR_LINK_ID,"\
                    + " TBL_A.MOVEMENT_ID"\
                    + " FROM" \
                    + " V_ANSR_VAL_COL_SEQ_COMBINATION TBL_A" \
                    + " WHERE" \
                    + " TBL_A.COL_SEQ_COMBINATION_ID = %s AND" \
                    + " TBL_A.DISUSE_FLAG = '0'"

                aryForBind = {}
                aryForBind['COL_SEQ_COMBINATION_ID'] = in_col_seq_comb_id
                row = objdbca.sql_execute(query_step2, bind_value_list=[aryForBind['COL_SEQ_COMBINATION_ID']])
                if len(row) != 0:
                    if row[0]['MEMBER_CNT'] == 0:
                        # 変数とメンバー変数の組合せが不正です。
                        retStrBody = g.appmsg.get_api_message("MSG-10436", [])
                        return False, retStrBody
                    elif row[0]["MVMT_VAR_LINK_ID"] != out_vars_link_id:
                        # Movement名:変数名とMovement名:変数名:メンバー変数で異なる変数名が選択されています。
                        retStrBody = g.appmsg.get_api_message("MSG-10898", [])
                        return False, retStrBody
                    elif row[0]["MOVEMENT_ID"] != out_pattern_id:
                        # Movement名:変数名とMovement名:変数名:メンバー変数で異なるMovementが選択されています。
                        retStrBody = g.appmsg.get_api_message("MSG-10894", [])
                        return False, retStrBody
            else:
                # Movement-ロール紐付に登録されているロールまたはロールパッケージに変数が未登録です。
                retStrBody = g.appmsg.get_api_message("MSG-10390")
                return False, retStrBody
    return retBool, retStrBody, out_pattern_id, out_vars_link_id, out_col_seq_comb_id


def getChildVars(objdbca, strVarsLinkIdNumeric, strColSeqCombinationId):
    """
    メンバー変数管理テーブル取得
    """
    strQuery = "SELECT" \
               + " TAB_1.MVMT_VAR_LINK_ID" \
               + ",TAB_1.COL_SEQ_NEED" \
               + ",TAB_1.ASSIGN_SEQ_NEED" \
               + " FROM" \
               + " T_ANSR_NESTVAR_MEMBER TAB_1" \
               + " LEFT JOIN T_ANSR_NESTVAR_MEMBER_COL_COMB TAB_2 ON ( TAB_1.ARRAY_MEMBER_ID = TAB_2.ARRAY_MEMBER_ID )" \
               + " WHERE" \
               + " TAB_1.DISUSE_FLAG IN ('0')" \
               + " AND TAB_2.DISUSE_FLAG IN ('0')" \
               + " AND TAB_1.MVMT_VAR_LINK_ID = %s" \
               + " AND TAB_2.COL_SEQ_COMBINATION_ID = %s"

    aryForBind = {}
    aryForBind['MVMT_VAR_LINK_ID'] = strVarsLinkIdNumeric
    aryForBind['COL_SEQ_COMBINATION_ID'] = strColSeqCombinationId

    row = objdbca.sql_execute(strQuery, bind_value_list=[aryForBind['MVMT_VAR_LINK_ID'], aryForBind['COL_SEQ_COMBINATION_ID']])
    if len(row) != 0:
        return row
    else:
        return False
