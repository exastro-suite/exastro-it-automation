from flask import g

from common_libs.ansible_driver.functions.chkVarsAssociate import chkVarsAssociate, getChildVars

def external_valid_menu_after(objdbca, objtable, option):
    retBool = True
    msg = ''

    query = ""

    boolExecuteContinue = True
    boolSystemErrorFlag = False

    # --UPD--
    pattan_tbl = "V_ANSR_MOVEMENT"
    
    autoreg_only_item = "0"
    rg_menu_id = ""
    
    if option["cmd_type"] == "Discard" or option["cmd_type"] == "Restore":
        # ----更新前のレコードから、各カラムの値を取得
        rg_column_list_id         = option["current_parameter"]["parameter"]["menu_group_menu_item"]
        
        rg_col_type               = option["current_parameter"]["parameter"]["registration_method"]
        
        rg_col_sub_order       = option["current_parameter"]["parameter"]["column_substitution_order"]
        
        rg_pattern_id             = option["current_parameter"]["parameter"]['movement']
        
        rg_vars_link_id       = option["current_parameter"]["parameter"]["variable_name"]
        
        rg_col_seq_comb_id    = option["current_parameter"]["parameter"]['member_variable_name']
        
        rg_assign_seq         = option["current_parameter"]["parameter"]['substitution_order']
        
        if option["cmd_type"] == "Discard":
            # ----廃止の場合はチェックしない
            boolExecuteContinue = False
            # 廃止の場合はチェックしない----
        else:
            # ----復活の場合
            if len(rg_column_list_id) == 0 or len(rg_col_type) == 0 or len(rg_pattern_id) == 0:
                boolSystemErrorFlag = True
            # 復活の場合----
            
            columnId = option["current_parameter"]["parameter"]["item_no"]
        # 更新前のレコードから、各カラムの値を取得----
    elif option["cmd_type"] == "Register" or option["cmd_type"] == "Update":
        # 登録・更新する各カラムの値を取得
        if "menu_group_menu_item" in option["entry_parameter"]["parameter"]:
            rg_column_list_id = option["entry_parameter"]["parameter"]["menu_group_menu_item"]
        else:
            rg_column_list_id = None
        
        if "registration_method" in option["entry_parameter"]["parameter"]:
            rg_col_type = option["entry_parameter"]["parameter"]["registration_method"]
        else:
            rg_col_type = None
        
        if "column_substitution_order" in option["entry_parameter"]["parameter"]:
            rg_col_sub_order = option["entry_parameter"]["parameter"]["column_substitution_order"]
        else:
            rg_col_sub_order = None
        
        if "movement" in option["entry_parameter"]["parameter"]:
            rg_pattern_id = option["entry_parameter"]["parameter"]["movement"]
        else:
            rg_pattern_id = None
        
        if "variable_name" in option["entry_parameter"]["parameter"]:
            rg_vars_link_id = option["entry_parameter"]["parameter"]["variable_name"]
        else:
            rg_vars_link_id = None
        
        if "member_variable_name" in option["entry_parameter"]["parameter"]:
            rg_col_seq_comb_id = option["entry_parameter"]["parameter"]["member_variable_name"]
        else:
            rg_col_seq_comb_id = None
        
        if "substitution_order" in option["entry_parameter"]["parameter"]:
            rg_assign_seq = option["entry_parameter"]["parameter"]["substitution_order"]
        else:
            rg_assign_seq = None
        
        # 主キーの値を取得する。
        if option["cmd_type"] == "Update":
            # 更新処理の場合
            columnId = option["current_parameter"]["parameter"]["item_no"]
        else:
            # 登録処理の場合
            if "uuid" in option:
                columnId = option["uuid"]
            else:
                columnId = None

    # 紐付け対象メニューに登録されているかの確認。カウント使用して数えて存在しているかの確認
    if boolExecuteContinue is True and boolSystemErrorFlag is False:
        if rg_column_list_id:
            query = "SELECT" \
                + " TBL_A.COLUMN_DEFINITION_ID," \
                + "TBL_A.MENU_ID," \
                + "TBL_A.AUTOREG_ONLY_ITEM," \
                + "COUNT(*) AS COLUMN_LIST_ID_CNT," \
                + "(" \
                + "SELECT" \
                + " COUNT(*)" \
                + " FROM" \
                + " V_ANSC_MENU TBL_B" \
                + " WHERE" \
                + " TBL_B.COLUMN_DEFINITION_ID = %s AND" \
                + " TBL_B.DISUSE_FLAG = '0'" \
                + " ) AS MENU_CNT " \
                + "FROM" \
                + " V_ANSC_COLUMN_LIST TBL_A" \
                + " WHERE" \
                + " TBL_A.COLUMN_DEFINITION_ID = %s AND" \
                + " TBL_A.DISUSE_FLAG = '0'"
            aryForBind = {}
            aryForBind['COLUMN_DEFINITION_ID'] = rg_column_list_id
            row = objdbca.sql_execute(query, bind_value_list=[aryForBind['COLUMN_DEFINITION_ID'], aryForBind['COLUMN_DEFINITION_ID']])
            if len(row) == 1:
                if row[0]['MENU_CNT'] == 1:
                    if row[0]['COLUMN_LIST_ID_CNT'] == 1:
                        rg_menu_id = row[0]['MENU_ID']
                        rg_column_list_id = row[0]['COLUMN_DEFINITION_ID']
                        table_name = "T_ANSR_VALUE_AUTOREG"
                        data_list = [{"COLUMN_ID": columnId, "MENU_ID": rg_menu_id}]
                        primary_key_name = "COLUMN_ID"
                        objdbca.table_update(table_name, data_list, primary_key_name, False)
                        # 変数の無いパラメーターシートのフラグとして使用
                        autoreg_only_item = row[0]['AUTOREG_ONLY_ITEM']
                        if boolExecuteContinue is True:
                            boolExecuteContinue = True
                    #  紐付対象メニューに項目が登録されているかの確認。
                    else:
                        # 紐付対象メニューに項目が未登録です。
                        msg = g.appmsg.get_api_message("MSG-10379")
                        retBool = False
                        boolExecuteContinue = False
                else:
                    # 紐付対象メニュー一覧にメニューが未登録です。
                    msg = g.appmsg.get_api_message("MSG-10378")
                    retBool = False
                    boolExecuteContinue = False
            else:
                # メニューカラム紐付け管理が不正です。
                msg = g.appmsg.get_api_message("MSG-10900", [rg_column_list_id])
                retBool = False
                boolExecuteContinue = False
            del row

    # メニューと項目の組み合わせチェック----
    # 登録方式のチェック
    # key-value型などの確認。
    if boolExecuteContinue is True and boolSystemErrorFlag is False:
        # 変数の無いパラメータシートの場合key,valueどちらが選択されてもOK
        if autoreg_only_item == "1":
            if rg_col_type == "1" or rg_col_type == "2":  # Value, Key
                boolExecuteContinue = True
            else:
                # 登録方式が範囲外です。
                msg = g.appmsg.get_api_message("MSG-10381")
                retBool = False
                boolExecuteContinue = False
        else:
            boolExecuteContinue = False
            if not rg_col_type:
                # 登録方式が未選択です。
                # 1.Value
                # 2.key
                msg = g.appmsg.get_api_message("MSG-10380")
                retBool = False
                boolExecuteContinue = False
            else:
                if rg_col_type == "1" or rg_col_type == "2":  # Value, Key
                    boolExecuteContinue = True
                else:
                    # 登録方式が範囲外です。
                    msg = g.appmsg.get_api_message("MSG-10381")
                    retBool = False
                    boolExecuteContinue = False
                    
    if boolExecuteContinue is True and boolSystemErrorFlag is False:
        chk_pattern_id = rg_pattern_id
        if chk_pattern_id and rg_vars_link_id and rg_col_type == '2':
            # key変数
            strColType = g.appmsg.get_api_message("MSG-10420")
            ret = chkVarsAssociate(objdbca, strColType, rg_vars_link_id, rg_col_seq_comb_id)
            if ret[0] is False:
                retBool = False
                msg = ret[1]
                boolExecuteContinue = False
            else:
                rg_pattern_id = ret[2]
                rg_vars_link_id = ret[3]
                rg_col_seq_comb_id = ret[4]
                # movementが全部同じものか確認。
                if chk_pattern_id != rg_pattern_id:
                    retBool = False
                    boolExecuteContinue = False
                    msg = g.appmsg.get_api_message("MSG-10893")
        elif chk_pattern_id and rg_vars_link_id and rg_col_type == '1':
            # Value変数
            strColType = g.appmsg.get_api_message("MSG-10421")
            ret = chkVarsAssociate(objdbca, strColType, rg_vars_link_id, rg_col_seq_comb_id)
            if ret[0] is False:
                retBool = False
                msg = ret[1]
                boolExecuteContinue = False
            else:
                rg_pattern_id = ret[2]
                rg_vars_link_id = ret[3]
                rg_col_seq_comb_id = ret[4]
                # movementが全部同じものか確認。
                if chk_pattern_id != rg_pattern_id:
                    retBool = False
                    boolExecuteContinue = False
                    msg = g.appmsg.get_api_message("MSG-10893")

    if boolExecuteContinue is True and boolSystemErrorFlag is False:
        # メニュー名 メニューグループ:メニュー:項目
        if not rg_column_list_id:
            # メニューグループ:メニュー:項目が未選択です。
            msg = g.appmsg.get_api_message("MSG-10432")
            boolExecuteContinue = False
            retBool = False
        # 空のパラメータシートの場合を除く
        elif not rg_col_type and autoreg_only_item != "1":
            # 登録方式が未選択です。
            msg = g.appmsg.get_api_message("MSG-10380")
            boolExecuteContinue = False
            retBool = False
        elif not rg_pattern_id:
            # Movementが未選択です。
            msg = g.appmsg.get_api_message("MSG-10433")
            boolExecuteContinue = False
            retBool = False

    # ----作業パターンのチェック
    if boolExecuteContinue is True and boolSystemErrorFlag is False:
        boolExecuteContinue = False
        # movementidを使用してデータが存在するか確認。
        query = "SELECT" \
                +" COUNT(*) AS PATTAN_CNT" \
                +" FROM" \
                +" {} TBL_A".format(pattan_tbl) \
                +" WHERE" \
                +" TBL_A.MOVEMENT_ID = %s AND" \
                +" TBL_A.DISUSE_FLAG = '0'"

        aryForBind = {}
        aryForBind['PATTERN_ID'] = rg_pattern_id

        row = objdbca.sql_execute(query, bind_value_list=[aryForBind['PATTERN_ID']])
        if len(row) == 1:
            if row[0]['PATTAN_CNT'] == 1:
                boolExecuteContinue = True
            else:
                boolExecuteContinue = False
                # Movementが未登録です。
                msg = g.appmsg.get_api_message("MSG-10382")
                retBool = False
                boolExecuteContinue = False
        else:
            boolSystemErrorFlag = True
        del row
    # 作業パターンのチェックの組み合わせチェック----
    
    # ----変数部分のチェック
    if boolExecuteContinue is True and boolSystemErrorFlag is False:
        for i in range(1):
            # rg_col_type 登録方式
            # 1がvalue
            # 2がkey
            # key部分に関して
            # dummyの場合何もしない
            if autoreg_only_item == "1":
                continue
            if rg_col_type in ["2"]:
                intVarsLinkId = rg_vars_link_id
                intColSeqCombId = rg_col_seq_comb_id
                intSeqOfAssign = rg_assign_seq
                strColType = g.appmsg.get_api_message("MSG-10420")
            elif rg_col_type in ["1"]:
                intVarsLinkId = rg_vars_link_id
                intColSeqCombId = rg_col_seq_comb_id
                intSeqOfAssign = rg_assign_seq
                strColType = g.appmsg.get_api_message("MSG-10421")
            else:
                continue
            
            # ----変数タイプを取得
            intVarType = -1
            strQuery = "SELECT" \
                       +" TAB_1.MVMT_VAR_LINK_ID," \
                       +"TAB_1.VARS_ATTRIBUTE_01" \
                       +" FROM" \
                       +" V_ANSR_VAL_VARS_LINK TAB_1" \
                       +" WHERE" \
                       +" TAB_1.DISUSE_FLAG IN ('0')" \
                       +" AND TAB_1.MVMT_VAR_LINK_ID = %s" \
                       +" AND TAB_1.MOVEMENT_ID = %s"

            aryForBind = {}
            aryForBind['MVMT_VAR_LINK_ID'] = intVarsLinkId
            aryForBind['MOVEMENT_ID'] = rg_pattern_id
            row = objdbca.sql_execute(strQuery, bind_value_list=[aryForBind['MVMT_VAR_LINK_ID'], aryForBind['MOVEMENT_ID']])
            if isinstance(row, list):
                if len(row) == 1:
                    # VARS_ATTRIBUTE_01
                    # 1:一般変数
                    # 2:複数具体値変数
                    # 3:多次元変数
                    tmpRow = row[0]
                    if tmpRow['VARS_ATTRIBUTE_01'] in ["1", "2", "3"]:
                        intVarType = tmpRow['VARS_ATTRIBUTE_01']
                    else:
                        boolSystemErrorFlag = True
                        break
                    del tmpRow
                else:
                    # 変数(Key)が未登録です。,変数(Value)が未登録です。
                    strMsgId = "MSG-10402"if rg_col_type == "2" else "MSG-10403"
                    msg = g.appmsg.get_api_message(strMsgId)
                    retBool = False
                    boolExecuteContinue = False
                    break
            else:
                boolSystemErrorFlag = True
                break
            del row
            # 変数タイプを取得----

            # 変数の種類ごとに、バリデーションチェック
            # 変数タイプが「一般変数」の場合 ←分岐
            if "1" == intVarType:
                # メンバー変数名のチェック
                if intColSeqCombId:
                    retBool = False
                    boolExecuteContinue = False
                    # 一般変数の場合は、メンバー変数の入力はできません。
                    msg = g.appmsg.get_api_message("MSG-10422", [strColType])
                    break
                # 代入順序のチェック
                if intSeqOfAssign:
                    retBool = False
                    boolExecuteContinue = False
                    # 一般変数の場合は、代入順序の入力はできません。
                    msg = g.appmsg.get_api_message("MSG-10423", [strColType])
                    break
            # 変数タイプが「複数具体値変数」の場合
            elif "2" == intVarType:
                # メンバー変数名のチェック
                if intColSeqCombId:
                    retBool = False
                    boolExecuteContinue = False
                    # 複数具体値変数の場合は、メンバー変数の入力はできません。
                    msg = g.appmsg.get_api_message("MSG-10425", [strColType])
                    break
                # 代入順序のチェック
                if not intSeqOfAssign:
                    retBool = False
                    boolExecuteContinue = False
                    # 複数具体値変数の場合は、代入順序の入力は必須です。
                    msg = g.appmsg.get_api_message("MSG-10426", [strColType])
                    break
            # 変数タイプが「多次元変数」の場合
            elif "3" == intVarType:
                # メンバー変数名のチェック
                if not intColSeqCombId:
                    retBool = False
                    boolExecuteContinue = False
                    # 多段変数の場合は、メンバー変数の入力は必須です。
                    msg = g.appmsg.get_api_message("MSG-10427", [strColType])
                    break
                else:
                    # メンバー変数管理テーブル取得
                    aryResult = getChildVars(objdbca, intVarsLinkId, intColSeqCombId)
                    if aryResult is False:
                        retBool = False
                        boolSystemErrorFlag = True
                        break
                    elif type([]) == type(aryResult) and 1 == len(aryResult):
                        childData = aryResult[0]
                        # 代入順序のチェック
                        intAssignSeqNeed = childData['ASSIGN_SEQ_NEED']
                    elif type([]) == type(aryResult) and 0 == len(aryResult):
                        retBool = False
                        boolExecuteContinue = False
                        # メンバー変数は、多段変数のメンバーではありません。
                        msg = g.appmsg.get_api_message("MSG-10424", [strColType])
                        break
                    else:
                        boolSystemErrorFlag = True
                        break
                # 代入順序の有無が有の場合
                if 1 == intAssignSeqNeed:
                    if not intSeqOfAssign:
                        retBool = False
                        boolExecuteContinue = False
                        # メンバー変数は、代入順序の入力は必須です。
                        msg = g.appmsg.get_api_message("MSG-10428", [strColType])
                        break
                # 代入順序の有無が無の場合
                else:
                    if intSeqOfAssign:
                        retBool = False
                        boolExecuteContinue = False
                        # メンバー変数は、代入順序の入力はできません。
                        msg = g.appmsg.get_api_message("MSG-10429", [strColType])
                        break
    # 変数部分のチェック----

    # 代入値自動登録設定テーブルの重複レコードチック
    if boolExecuteContinue is True and boolSystemErrorFlag is False:
        strQuery =  "SELECT" \
                    +" COLUMN_ID" \
                    +" FROM" \
                    +" T_ANSR_VALUE_AUTOREG" \
                    +" WHERE" \
                    +" COLUMN_ID <> %s AND" \
                    +" MENU_ID = %s AND " \
                    +" MOVEMENT_ID = %s AND" \
                    +" DISUSE_FLAG = '0'" \
                    +" AND("

        aryForBind = {}
        aryForBind['COLUMN_ID']    = columnId
        aryForBind['MENU_ID']      = rg_menu_id
        aryForBind['MOVEMENT_ID']   = rg_pattern_id

        # Key変数が必須の場合
        strQuery += " ("
        if rg_vars_link_id:
            strQuery += " MVMT_VAR_LINK_ID = '{}'".format(rg_vars_link_id)
        else:
            strQuery += " MVMT_VAR_LINK_ID is NULL"
        if rg_col_seq_comb_id:
            strQuery += " AND COL_SEQ_COMBINATION_ID = '{}'".format(rg_col_seq_comb_id)
        else:
            strQuery += " AND COL_SEQ_COMBINATION_ID is NULL"
        if rg_assign_seq:
            strQuery += " AND ASSIGN_SEQ = '{}'".format(rg_assign_seq)
        else:
            strQuery += " AND ASSIGN_SEQ is NULL"
        strQuery += " )"
        aryForBind['MVMT_VAR_LINK_ID'] = rg_vars_link_id
        strQuery += " )"
        retArray = objdbca.sql_execute(strQuery, bind_value_list=[aryForBind['COLUMN_ID'], aryForBind['MENU_ID'], aryForBind['MOVEMENT_ID']])
        if retArray:
            dupnostr = ""
            for row in retArray:
                dupnostr += "[" + row['COLUMN_ID'] + "]"
            if len(dupnostr) != 0:
                retBool = False
                boolExecuteContinue = False
                # 次の項目が、[項番]:({})のレコードと重複しています。\n[(メニューグループ:メニュー),(Movement),(変数),(代入順序)]
                msg = g.appmsg.get_api_message("MSG-10430", [dupnostr])
        del retArray
        
        # 縦型メニューかの確認。
        table_name = "V_ANSC_COLUMN_LIST"
        where_str = "WHERE COLUMN_DEFINITION_ID = %s"
        bind_value_list = [rg_column_list_id]
        row = objdbca.table_select(table_name, where_str, bind_value_list)
        # 縦型メニューかつ代入順序がない場合
        if row[0]["VERTICAL"] == "1" and not rg_col_sub_order:
            retBool = False
            boolExecuteContinue = False
            msg = g.appmsg.get_api_message("MSG-10895")
        # 縦型メニューではないのに代入順序がある場合
        elif row[0]["VERTICAL"] == "0" and rg_col_sub_order:
            retBool = False
            boolExecuteContinue = False
            msg = g.appmsg.get_api_message("MSG-10899")

    if boolExecuteContinue is True and boolSystemErrorFlag is False:
        # 変数の無いパラメータシート
        if autoreg_only_item == "1":
            if rg_col_sub_order or rg_assign_seq:
                retBool = False
                boolExecuteContinue = False
                msg = g.appmsg.get_api_message("MSG-10896")
            elif rg_vars_link_id or rg_col_seq_comb_id:
                retBool = False
                boolExecuteContinue = False
                msg = g.appmsg.get_api_message("MSG-10897")
    
    if boolSystemErrorFlag is True:
        retBool = False
        # ----システムエラー
        msg = g.appmsg.get_api_message("MSG-10886")

    return retBool, msg, option,
