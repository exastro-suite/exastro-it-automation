from flask import g
import os
import inspect


def chkVarsAssociate(objdbca, in_type, in_vars_link_id, in_col_seq_comb_id):
    retBool = True
    retStrBody = ""
    out_pattern_id = None
    out_vars_link_id = in_vars_link_id
    out_col_seq_comb_id = in_col_seq_comb_id
    # 代入値値自動登録用Movement+変数名
    # 2 系Role Movement-変数紐付
    query_step1 = "SELECT" \
                    +" TBL_A.MVMT_VAR_LINK_ID," \
                    +"TBL_A.MOVEMENT_ID," \
                    +"COUNT(*) AS VARS_LINK_ID_CNT," \
                    +"TBL_A.VARS_ATTRIBUTE_01" \
                    +" FROM" \
                    +" V_ANSR_VAL_VARS_LINK TBL_A" \
                    +" WHERE" \
                    +" TBL_A.MVMT_VAR_LINK_ID = %s AND" \
                    +" TBL_A.DISUSE_FLAG = '0'"
                    
    aryForBind = {}
    aryForBind['MVMT_VAR_LINK_ID'] = in_vars_link_id
    row = objdbca.sql_execute(query_step1, bind_value_list=[aryForBind['MVMT_VAR_LINK_ID']])
    # レコードが存在するか確認
    if len(row) != 0:
        if row[0]['VARS_LINK_ID_CNT'] == 0:
            # ロールに変数が登録されていない、Movement-ロール紐付に登録されているロールまたはロールパッケージに変数が未登録です。
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
                    # メンバー変数入力不可　in_type = col_type
                    retStrBody = g.appmsg.get_api_message("MSG-10434", [in_type])
                    return False, retStrBody
            elif row[0]['VARS_ATTRIBUTE_01'] == "3":
                out_col_seq_comb_id = in_col_seq_comb_id
                if not in_col_seq_comb_id:
                    # メンバー変数が入力されていません
                    retStrBody = g.appmsg.get_api_message("MSG-10435", [in_type])
                    return False, retStrBody

                # 変数とメンバー変数の組合せ判定
                query_step2 = "SELECT" \
                    +" COUNT(*) AS MEMBER_CNT," \
                    +" TBL_A.MVMT_VAR_LINK_ID,"\
                    +" TBL_A.MOVEMENT_ID"\
                    +" FROM" \
                    +" V_ANSR_VAL_COL_SEQ_COMBINATION TBL_A" \
                    +" WHERE" \
                    +" TBL_A.COL_SEQ_COMBINATION_ID = %s AND" \
                    +" TBL_A.DISUSE_FLAG = '0'"
                
                aryForBind = {}
                aryForBind['COL_SEQ_COMBINATION_ID'] = in_col_seq_comb_id
                row = objdbca.sql_execute(query_step2, bind_value_list=[aryForBind['COL_SEQ_COMBINATION_ID']])
                if len(row) != 0:
                    if row[0]['MEMBER_CNT'] == 0:
                        retStrBody = g.appmsg.get_api_message("MSG-10436", [in_type])
                        return False, retStrBody
                    elif row[0]["MVMT_VAR_LINK_ID"] != out_vars_link_id:
                        retStrBody = g.appmsg.get_api_message("MSG-10898", [in_type])
                        return False, retStrBody
                    elif row[0]["MOVEMENT_ID"] != out_pattern_id:
                        retStrBody = g.appmsg.get_api_message("MSG-10894", [in_type])
                        return False, retStrBody
            else:
                retStrBody = g.appmsg.get_api_message("MSG-10390")
                return False, retStrBody
    return retBool, retStrBody, out_pattern_id, out_vars_link_id, out_col_seq_comb_id

"""
メンバー変数管理テーブル取得
"""
def getChildVars(objdbca, strVarsLinkIdNumeric, strColSeqCombinationId):

    strQuery = "SELECT" \
               +" TAB_1.MVMT_VAR_LINK_ID" \
               +",TAB_1.COL_SEQ_NEED" \
               +",TAB_1.ASSIGN_SEQ_NEED" \
               +" FROM" \
               +" T_ANSR_NESTVAR_MEMBER TAB_1" \
               +" LEFT JOIN T_ANSR_NESTVAR_MEMBER_COL_COMB TAB_2 ON ( TAB_1.ARRAY_MEMBER_ID = TAB_2.ARRAY_MEMBER_ID )" \
               +" WHERE" \
               +" TAB_1.DISUSE_FLAG IN ('0')" \
               +" AND TAB_2.DISUSE_FLAG IN ('0')" \
               +" AND TAB_1.MVMT_VAR_LINK_ID = %s" \
               +" AND TAB_2.COL_SEQ_COMBINATION_ID = %s"

    aryForBind = {}
    aryForBind['MVMT_VAR_LINK_ID'] = strVarsLinkIdNumeric
    aryForBind['COL_SEQ_COMBINATION_ID'] = strColSeqCombinationId
    
    row = objdbca.sql_execute(strQuery, bind_value_list=[aryForBind['MVMT_VAR_LINK_ID'], aryForBind['COL_SEQ_COMBINATION_ID']])
    if len(row) != 0:
        return row
    else:
        return False