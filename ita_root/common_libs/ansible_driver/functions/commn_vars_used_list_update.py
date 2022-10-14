import inspect
from flask import g
import os

def CommnVarsUsedListUpdate(objdbca, option, ContensID, FileID, VarsAry):
    MasterTableName = "T_ANSC_COMVRAS_USLIST"
    MemberAry = {}
    PkeyMember = ""
    UsedPkeyList = []
    msg = ""
    # テーブルカラム取得
    ret = objdbca.table_columns_get(MasterTableName)
    for i in ret[0]:
        MemberAry[i] = ""
    
    PkeyMember = ret[1][0]
    for VarID, VarNameList in VarsAry.items():
        for VarName, dummy in VarNameList.items():
            sql = "WHERE FILE_ID= %s AND VRA_ID= %s AND CONTENTS_ID= %s AND VAR_NAME= %s"
            ret = objdbca.table_select(MasterTableName, sql, [FileID, VarID, ContensID, VarName])
            arrayValue = MemberAry
            arrayConfig = MemberAry
            if len(ret) == 0:
                action = 'INSERT'
                arrayValue['FILE_ID'] = FileID
                arrayValue['VRA_ID']                 = VarID
                arrayValue['CONTENTS_ID']            = ContensID
                arrayValue['VAR_NAME']               = VarName
                arrayValue['REVIVAL_FLAG']           = '0'
                arrayValue['DISUSE_FLAG']            = '0'
                arrayValue['LAST_UPDATE_USER']       = option["user"]
            elif len(ret) != 0:
                row = ret[0]
                for col, dummy in row.items():
                    arrayValue[col] = row[col]
                if row['DISUSE_FLAG'] == '0':
                    action = 'NONE'
                else:
                    action = 'UPDATE'
                    arrayValue['REVIVAL_FLAG']           = '0'
                    arrayValue['DISUSE_FLAG']            = '0'
                    arrayValue['LAST_UPDATE_USER']       = option["user"]  # 最終更新者
                    # 最終更新日時は振ってくれるので問題なし
            else:
                msg = "Duplicate error. (Table:{} {}".format(MasterTableName, sql)
                return False, msg
            if action == 'NONE':
                UsedPkeyList.append(arrayValue[PkeyMember])
            elif action == 'INSERT':
                PkeyID = ''
                # pkeyidの取得に関して
                data_list = {
                    'FILE_ID': arrayValue['FILE_ID'],
                    'VRA_ID': arrayValue['VRA_ID'],
                    'CONTENTS_ID': arrayValue['CONTENTS_ID'],
                    'VAR_NAME': arrayValue['VAR_NAME'],
                    'REVIVAL_FLAG': arrayValue['REVIVAL_FLAG'],
                    'DISUSE_FLAG': arrayValue['DISUSE_FLAG'],
                    'LAST_UPDATE_USER': arrayValue['LAST_UPDATE_USER']
                }
                ret = objdbca.table_insert(MasterTableName, data_list, PkeyMember, False)
                if ret is False:
                    msg = g.appmsg.get_api_message("MSG-10178", [os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno])
                    return False, msg
                PkeyID = ret[0]["ROW_ID"]
                UsedPkeyList.append(PkeyID)
            elif action == 'UPDATE':
                data_list = {PkeyMember: arrayValue[PkeyMember], 'REVIVAL_FLAG': arrayValue['REVIVAL_FLAG'], 'DISUSE_FLAG': arrayValue['DISUSE_FLAG'], 'LAST_UPDATE_USER': arrayValue['LAST_UPDATE_USER']}
                # Pkey退避
                UsedPkeyList.append(arrayValue[PkeyMember])
                ret = objdbca.table_update(MasterTableName, data_list, PkeyMember, False)
                if ret is False:
                    msg = g.appmsg.get_api_message("MSG-10178", [os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno])

                    return False, msg

    if len(UsedPkeyList) != 0:
        # 不要レコードを抽出
        key_list = ""
        for i in range(len(UsedPkeyList)):
            if i == 0:
                key_list = "'" + UsedPkeyList[i] + "'"
            else:
                key_list += "," + "'" + UsedPkeyList[i] + "'"
        sql = "WHERE FILE_ID = %s AND CONTENTS_ID= %s AND " + PkeyMember + " NOT IN (" + key_list + ")"
        ret = objdbca.table_select(MasterTableName, sql, [FileID, ContensID])
    else:
        sql = "WHERE FILE_ID = %s AND CONTENTS_ID= %s "
        ret = objdbca.table_select(MasterTableName, sql, [FileID, ContensID])

    # 不要なレコードを廃止
    for row in ret:
        arrayValue = MemberAry
        arrayConfig = MemberAry
        for col, dummy in row.items():
            arrayValue[col] = row[col]
        if row['DISUSE_FLAG'] == '1':
            continue
        else:
            arrayValue['REVIVAL_FLAG'] = '0'
            arrayValue['DISUSE_FLAG'] = '1'
            arrayValue['LAST_UPDATE_USER'] = option["user"]
            primary_key_name = "ROW_ID"
            data_list = {primary_key_name: row[primary_key_name], 'REVIVAL_FLAG': arrayValue['REVIVAL_FLAG'], 'DISUSE_FLAG': arrayValue['DISUSE_FLAG'], 'LAST_UPDATE_USER': option["user"]}
            primary_key_name = "ROW_ID"
            result = objdbca.table_update(MasterTableName, data_list, primary_key_name, False)
            if result is False:
                msg = g.appmsg.get_api_message("MSG-10178", [os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno])
                return False, msg

    return True, msg


def CommnVarsUsedListDisuseSet(objdbca, option, ContensID, FileID):
    
    MasterTableName = "T_ANSC_COMVRAS_USLIST"
    MemberAry = {}
    PkeyMember = ""
    msg = ""
    ret = objdbca.table_columns_get(MasterTableName)
    for i in ret[0]:
        MemberAry[i] = ""
    # get directory
    PkeyMember = ret[1][0]
    sql = "WHERE FILE_ID = %s AND CONTENTS_ID = %s "
    ret = objdbca.table_select(MasterTableName, sql, [FileID, ContensID])

    for row in ret:
        arrayValue = MemberAry
        arrayConfig = MemberAry
        for col, dummy in row.items():
            arrayValue[col] = row[col]

        if option["cmd_type"] == 'Discard':
            # 廃止の場合、復活時の有効レコードフラグを設定
            if arrayValue['DISUSE_FLAG'] == '0':
                arrayValue['DISUSE_FLAG'] = '1'
                arrayValue['REVIVAL_FLAG'] = '1'
            else:
                continue
            data_list = {PkeyMember: arrayValue[PkeyMember], 'REVIVAL_FLAG': arrayValue['REVIVAL_FLAG'], 'DISUSE_FLAG': arrayValue['DISUSE_FLAG'], 'LAST_UPDATE_USER': option["user"]}
            result = objdbca.table_update(MasterTableName, data_list, PkeyMember, False)
            if result is False:
                msg = g.appmsg.get_api_message("MSG-10178", [os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno])
                return False, msg

        else:
            # 復活時の有効レコードフラグが設定されているレコードのみ復活
            if arrayValue['DISUSE_FLAG'] == '1' and arrayValue['REVIVAL_FLAG'] == '1':
                arrayValue['DISUSE_FLAG'] = '0'
                arrayValue['REVIVAL_FLAG'] = '0'
            else:
                continue
            data_list = {PkeyMember: row[PkeyMember], 'REVIVAL_FLAG': arrayValue['REVIVAL_FLAG'], 'DISUSE_FLAG': arrayValue['DISUSE_FLAG'], 'LAST_UPDATE_USER': option["user"]}
            result = objdbca.table_update(MasterTableName, data_list, PkeyMember, False)
            if ret is False:
                msg = g.appmsg.get_api_message("MSG-10178", [os.path.basename(inspect.currentframe().f_code.co_filename), inspect.currentframe().f_lineno])
                return False, msg
    return True, msg
