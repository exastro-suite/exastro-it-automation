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

# from common_libs.common.exception import AppException

from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs
from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.ansibletowerlibs.RestApiCaller import RestApiCaller
from common_libs.ansible_driver.classes.ansibletowerlibs.RestApiCaller import setAACRestAPITimoutVaule
from common_libs.ansible_driver.classes.ansibletowerlibs.restapi_command.AnsibleTowerRestApiPassThrough import AnsibleTowerRestApiPassThrough


def DBUpdate(Contents_array, TableName, TableRows, PkeyItem, NameItem, IDItem, dbAccess, is_register_history):

    db_access_user_id = '20102'

    livingIds = []

    # 既存データの検索用Idカラムを作成する
    Names_inTable = [d[NameItem] for d in TableRows]

    # 新規追加 or 更新
    for Contents_fromTower in Contents_array:
        target_index = None
        if Contents_fromTower['name'] in Names_inTable:
            target_index = Names_inTable.index(Contents_fromTower['name'])

        # 見つからない場合は新規
        if target_index is None:
            newRow = {
                NameItem: Contents_fromTower['name'],
                IDItem: Contents_fromTower['id'],
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_USER': db_access_user_id,
            }
            rowId = dbAccess.table_insert(TableName, newRow, PkeyItem, is_register_history)
            rowId = rowId[0][PkeyItem]

        # 見つかるのであれば更新の可能性 ... 差分があれば更新/復活
        else:
            updateRow = TableRows[target_index]
            rowId = updateRow[PkeyItem]
            if Contents_fromTower['id'] != updateRow[IDItem]:
                updateRow[IDItem] = Contents_fromTower['id']
                updateRow['DISUSE_FLAG'] = '0'
                updateRow['LAST_UPDATE_USER'] = db_access_user_id
                rowId = dbAccess.table_update(TableName, updateRow, PkeyItem, is_register_history)
                rowId = rowId[0][PkeyItem]

            if updateRow['DISUSE_FLAG'] != '0':
                updateRow['DISUSE_FLAG'] = '0'
                updateRow['LAST_UPDATE_USER'] = db_access_user_id
                rowId = dbAccess.table_update(TableName, updateRow, PkeyItem, is_register_history)
                rowId = rowId[0][PkeyItem]

        if rowId is False:
            raise

        livingIds.append(rowId)

    # 廃止
    for row in TableRows:
        # 既に廃止されているレコードは対象外
        if row['DISUSE_FLAG'] != "0":
            continue

        # 登録されている場合はなにもしない
        if row[PkeyItem] in livingIds:
            continue

        row['DISUSE_FLAG'] = '1'
        row['LAST_UPDATE_USER'] = db_access_user_id
        rset = dbAccess.table_update(TableName, row, PkeyItem, is_register_history)
        if rset is False:
            raise

    return True


def RestResultLog(message_list):
    for message in message_list:
        if not isinstance(message, str):
            message = str(message)
        g.applogger.info(message)


def backyard_main(organization_id, workspace_id):

    warning_flag = 0
    error_flag = 0
    dbAccess = None

    try:
        g.applogger.debug("Start Procedure.")

        ################################
        # DBコネクト
        ################################
        g.applogger.debug("db connect.")
        dbAccess = DBConnectWs()

        ################################
        # AAC向けRestAPIタイムアウト値設定
        ################################
        setAACRestAPITimoutVaule(dbAccess)
        ################################
        # インターフェース情報を取得する
        ################################
        g.applogger.debug("Get interface info.")
        cols = ""
        cols_a = dbAccess.table_columns_get("T_ANSC_IF_INFO")
        cols_b = dbAccess.table_columns_get("T_ANSC_TOWER_HOST")
        for col in cols_a[0]:
            if cols:
                cols += ", "

            cols += "TAB_A.%s" % (col)

        for col in cols_b[0]:
            if cols:
                cols += ", "

            cols += "TAB_B.%s" % (col)

        sql = (
            "SELECT                     \n"
            "  %s                       \n"
            "FROM                       \n"
            "  T_ANSC_IF_INFO TAB_A     \n"
            "INNER JOIN                 \n"
            "  T_ANSC_TOWER_HOST TAB_B  \n"
            "ON                         \n"
            "  TAB_A.ANSTWR_HOST_ID = TAB_B.ANSTWR_HOST_ID \n"
            "WHERE                      \n"
            "  TAB_A.DISUSE_FLAG = '0'  \n"
            "AND                        \n"
            "  TAB_B.DISUSE_FLAG = '0'; \n"
        ) % (cols)
        ifInfoRows = dbAccess.sql_execute(sql)
        num_of_rows = len(ifInfoRows)

        # 設定なしの場合
        if num_of_rows == 0:
            raise Exception("No records in if_info.")

        # 重複登録の場合
        elif num_of_rows > 1:
            raise Exception("More than one record in if_info.")

        # 実行エンジンがAnsible Towerの場合のみ処理続行
        if ifInfoRows[0]['ANSIBLE_EXEC_MODE'] != AnscConst.DF_EXEC_MODE_AAC:
            return 0

        if ('ANSTWR_AUTH_TOKEN' not in ifInfoRows[0] or ifInfoRows[0]['ANSTWR_AUTH_TOKEN'] is None or len(ifInfoRows[0]['ANSTWR_AUTH_TOKEN'].strip()) <= 0) \
        or ('ANSTWR_HOST_ID' not in ifInfoRows[0] or ifInfoRows[0]['ANSTWR_HOST_ID'] is None or len(ifInfoRows[0]['ANSTWR_HOST_ID'].strip()) <= 0):
            return 0

        ansibleTowerIfInfo = ifInfoRows[0]

        proxySetting = {}
        proxySetting['address'] = ansibleTowerIfInfo["ANSIBLE_PROXY_ADDRESS"]
        proxySetting['port'] = ansibleTowerIfInfo["ANSIBLE_PROXY_PORT"]

        ################################
        # RESTの認証
        ################################
        g.applogger.debug("Authorize Ansible Automation Controller.")

        restApiCaller = RestApiCaller(
            ansibleTowerIfInfo['ANSTWR_PROTOCOL'],
            ansibleTowerIfInfo['ANSTWR_HOSTNAME'],
            ansibleTowerIfInfo['ANSTWR_PORT'],
            ansibleTowerIfInfo['ANSTWR_AUTH_TOKEN'],
            proxySetting
        )

        response_array = restApiCaller.authorize()
        if not response_array['success']:
            raise Exception("Faild to authorize to Ansible Automation Controller. %s" % (response_array['responseContents']['errorMessage']))

        ############################################################
        # 接続トークンに対応したユーザー情報取得
        ############################################################
        url = "/api/v2/me/"
        response_array = AnsibleTowerRestApiPassThrough.get(restApiCaller, url)
        if not response_array['success']:
            RestResultLog(restApiCaller.getRestResultList())
            raise Exception("Faild to get users data from %s" % (url))

        if 'responseContents' not in response_array:
            RestResultLog(restApiCaller.getRestResultList())
            raise Exception("responseContents tag is not found in %s" % (url))

        if 'results' not in response_array['responseContents']:
            RestResultLog(restApiCaller.getRestResultList())
            raise Exception("responseContents->results tag not found in %s" % (url))

        if 'count' not in response_array['responseContents']:
            RestResultLog(restApiCaller.getRestResultList())
            raise Exception("responseContents->count tag not found in %s" % (url))

        if response_array['responseContents']['count'] != 1:
            RestResultLog(restApiCaller.getRestResultList())
            raise Exception("responseContents->count is not 1 in %s" % (url))

        # 管理者ユーザー区分取得
        is_superuser = response_array['responseContents']['results'][0]['is_superuser']

        users_response_array = response_array

        ############################################################
        # ユーザーに紐づく組織情報更新
        ############################################################
        try:
            ############################################################
            # ユーザーに紐づく組織情報取得
            ############################################################
            url = users_response_array['responseContents']['results'][0]['related']['organizations']
            response_array = AnsibleTowerRestApiPassThrough.get(restApiCaller, url)
            if not response_array['success']:
                RestResultLog(restApiCaller.getRestResultList())
                raise Exception("Faild to get organization data from %s" % (url))

            if 'responseContents' not in response_array:
                RestResultLog(restApiCaller.getRestResultList())
                raise Exception("responseContents tag is not found in %s" % (url))

            if 'results' not in response_array['responseContents']:
                RestResultLog(restApiCaller.getRestResultList())
                raise Exception("responseContents->results tag not found in %s" % (url))

            if 'count' not in response_array['responseContents']:
                RestResultLog(restApiCaller.getRestResultList())
                raise Exception("responseContents->count tag not found in %s" % (url))

            org_response_array = response_array
            is_organizations = True
            # 組織の紐付けが無い場合、Defaultの組織を適用する。
            if response_array['responseContents']['count'] == 0:
                url = "/api/v2/organizations/1/"
                response_array = AnsibleTowerRestApiPassThrough.get(restApiCaller, url)
                if not response_array['success']:
                    RestResultLog(restApiCaller.getRestResultList())
                    raise Exception("Faild to get organization data from %s" % (url))

                if 'responseContents' not in response_array:
                    RestResultLog(restApiCaller.getRestResultList())
                    raise Exception("responseContents tag is not found in %s" % (url))

                org_response_array = {}
                org_response_array['responseContents'] = {}
                org_response_array['responseContents']['results'] = []
                Contents = {}
                Contents['id'] = response_array['responseContents']['id']
                Contents['name'] = response_array['responseContents']['name']
                Contents['related'] = {}
                Contents['related']['instance_groups'] = response_array['responseContents']['related']['instance_groups']
                org_response_array['responseContents']['results'].append(Contents)

                is_organizations = False

            ############################################################
            # トランザクション開始
            ############################################################
            dbAccess.db_transaction_start()

            ############################################################
            # ITA側の既に登録済みの組織名情報を取得する
            ############################################################
            TableName = "T_ANSC_TWR_ORGANIZATION"
            cols = dbAccess.table_columns_get(TableName)
            cols = (',').join(cols[0])
            sql = (
                "SELECT \n"
                "  %s   \n"
                "FROM   \n"
                "  %s ; \n"
            ) % (cols, TableName)
            OrganizationRows = dbAccess.sql_execute(sql)

            ############################################################
            # データベース更新
            ############################################################
            PkeyItem = "ORGANIZATION_ITA_MANAGED_ID"
            NameItem = "ORGANIZATION_NAME"
            IDItem = "ORGANIZATION_ID"
            Contents_array = []
            igrp_url = None
            my_org_id = None
            for info in org_response_array['responseContents']['results']:
                Contents_array.append(
                    {
                        'name': info['name'],
                        'id': int(info['id']),
                    }
                )
                # インタフェース情報の組織が未登録場合
                # 先頭の組織に紐づくインスタンスグループ取得

                if not ifInfoRows[0]['ANSTWR_ORGANIZATION']:
                    igrp_url = org_response_array['responseContents']['results'][0]['related']['instance_groups']
                    my_org_id = int(org_response_array['responseContents']['results'][0]['id'])
                else:
                    if info['name'] == ifInfoRows[0]['ANSTWR_ORGANIZATION']:
                        igrp_url = info['related']['instance_groups']
                        my_org_id = int(info['id'])

            # 組織が紐づいていないユーザーで管理者ユーザーの場合
            if is_organizations == False and is_superuser == True:
                igrp_url = "/api/v2/instance_groups/"

            DBUpdate(Contents_array, TableName, OrganizationRows, PkeyItem, NameItem, IDItem, dbAccess, False)

            ############################################################
            # トランザクション終了
            ############################################################
            dbAccess.db_commit()

        except Exception as e:
            raise Exception(e)

        ############################################################
        # インスタンスグループ情報更新
        ############################################################
        try:
            ############################################################
            # 組織で利用可能なインスタンスグループ情報取得
            ############################################################
            # インタフェース情報の組織が未登録場合
            # インスタンスグループは空にする
            if igrp_url:
                url = igrp_url
                response_array = AnsibleTowerRestApiPassThrough.get(restApiCaller, url)
                if not response_array['success']:
                    RestResultLog(restApiCaller.getRestResultList())
                    raise Exception("Faild to get instance groups data from %s" % (url))

                if 'responseContents' not in response_array:
                    RestResultLog(restApiCaller.getRestResultList())
                    raise Exception("responseContents tag is not found in %s" % (url))

                if 'results' not in response_array['responseContents']:
                    RestResultLog(restApiCaller.getRestResultList())
                    raise Exception("responseContents->results tag not found in %s" % (url))

                if 'count' not in response_array['responseContents']:
                    RestResultLog(restApiCaller.getRestResultList())
                    raise Exception("responseContents->count tag not found in %s" % (url))

                igrp_response_array = response_array
            else:
                igrp_response_array = {}
                igrp_response_array['responseContents'] = {}
                igrp_response_array['responseContents']['results'] = []

            ############################################################
            # トランザクション開始
            ############################################################
            dbAccess.db_transaction_start()

            ############################################################
            # インスタンスグループ情報取得
            ############################################################
            TableName = "T_ANSC_TWR_INSTANCE_GROUP"
            cols = dbAccess.table_columns_get(TableName)
            cols = (',').join(cols[0])
            sql = (
                "SELECT \n"
                "  %s   \n"
                "FROM   \n"
                "  %s ; \n"
            ) % (cols, TableName)
            instanceGroupRows = dbAccess.sql_execute(sql)

            ############################################################
            # データベース更新
            ############################################################
            PkeyItem = "INSTANCE_GROUP_ITA_MANAGED_ID"
            NameItem = "INSTANCE_GROUP_NAME"
            IDItem = "INSTANCE_GROUP_ID"
            Contents_array = []
            for info in igrp_response_array['responseContents']['results']:
                Contents_array.append(
                    {
                        'name': info['name'],
                        'id': int(info['id']),
                    }
                )

            DBUpdate(Contents_array, TableName, instanceGroupRows, PkeyItem, NameItem, IDItem, dbAccess, False)

            ############################################################
            # トランザクション終了(分割コミット)
            ############################################################
            dbAccess.db_commit()

        except Exception as e:
            raise Exception(e)

        ############################################################
        # 該当ユーザーの組織が利用可能な実行環境情報更新
        ############################################################
        try:
            #  該当ユーザーの組織が利用可能な実行環境取得
            # /api/v2/organizations/12/execution_environments/だと組織共通の実行環境が取得できない
            url = "/api/v2/execution_environments/"
            response_array = AnsibleTowerRestApiPassThrough.get(restApiCaller, url)

            if not response_array['success']:
                RestResultLog(restApiCaller.getRestResultList())
                raise Exception("Faild to get execution environments data from %s" % (url))

            if 'responseContents' not in response_array:
                RestResultLog(restApiCaller.getRestResultList())
                raise Exception("responseContents tag is not found in %s" % (url))

            if 'results' not in response_array['responseContents']:
                RestResultLog(restApiCaller.getRestResultList())
                raise Exception("responseContents->results tag not found in %s" % (url))

            if 'count' not in response_array['responseContents']:
                RestResultLog(restApiCaller.getRestResultList())
                raise Exception("responseContents->count tag not found in %s" % (url))

            ee_response_array = response_array
            ############################################################
            # トランザクション開始
            ############################################################
            dbAccess.db_transaction_start()

            ############################################################
            # ITA側の既に登録済みの実行環境情報取得
            ############################################################
            TableName = "T_COMN_AAC_EXECUTION_ENVIRONMENT"
            cols = dbAccess.table_columns_get(TableName)
            cols = (',').join(cols[0])
            sql = (
                "SELECT \n"
                "  %s   \n"
                "FROM   \n"
                "  %s ; \n"
            ) % (cols, TableName)
            VirtualEnvRows = dbAccess.sql_execute(sql)

            ############################################################
            # データベース更新
            ############################################################
            PkeyItem = "EXECUTION_ENVIRONMENT_ID"
            NameItem = "EXECUTION_ENVIRONMENT_NAME"
            IDItem = "EXECUTION_ENVIRONMENT_AAC_ID"
            Contents_array = []
            for info in ee_response_array['responseContents']['results']:
                # 組織が紐づいていないユーザーで管理者ユーザーの場合か
                # 複数の組織に属している場合、他組織に属している実行環境も取得出来てしまうので
                # 全組織共通の実行環境と自組織に属している実行環境だけを選択する。
                if (is_organizations == False and is_superuser == True) or \
                   (not info['organization'] or info['organization'] == my_org_id):
                    Contents_array.append(
                        {
                            'name': info['name'],
                            'id': info['id'],
                        }
                    )

            DBUpdate(Contents_array, TableName, VirtualEnvRows, PkeyItem, NameItem, IDItem, dbAccess, False)

            ############################################################
            # トランザクション終了
            ############################################################
            dbAccess.db_commit()

        except Exception as e:
            raise Exception(e)

    except Exception as e:
        error_flag = 1
        if dbAccess and dbAccess._is_transaction:
            # ロールバック
            dbAccess.db_rollback()

        raise Exception(e)

    finally:
        dbAccess = None
        restApiCaller = None

    if error_flag != 0:
        g.applogger.debug("Finished Procedure. [state: ERROR]")
        return 2

    elif warning_flag != 0:
        g.applogger.debug("Finished Procedure. [state: WARNING]")
        return 2

    else:
        g.applogger.debug("Finished Procedure. [state: SUCCESS]")
        return 0
