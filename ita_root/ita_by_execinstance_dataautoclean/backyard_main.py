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
# class MainFunctions():
#   __init__(self):
#   InitFunction(self):
#   MainFunction(self):
#   EndFunction(self, result):
#   getOpeDelMenuList(self, OpeDelLists):
#   getTgtDelOpeList(self, TgtDelDate):
#   LogicalDeleteDB(self, DelList, TgtOpeList):
#   PhysicalDeleteDB(self, DelList, TgtOpeList):
#   getDataRelayStorageDir(self):
#   is_int(self, int_value):
#   DateCalc(self, AddDay):
# backyard_main(organization_id, workspace_id):
import os
import datetime
import shutil

from flask import g

from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs


class MainFunctions():
    """
      オペレーション削除　メイン処理クラス
    """
    def __init__(self):
        if getattr(g, 'USER_ID', None) is None:
            g.USER_ID = '110101'
        self.warning_flag = 0  # 警告フラグ(1：警告発生)
        self.error_flag = 0    # 異常フラグ(1：異常発生)
        self.test_mode = False
        self.ws_db = None
        self.operation_id_column_name = "OPERATION_ID"

    def InitFunction(self):
        """
          初期処理
          Arguments:
            なし
          Returns:
            なし
        """
        # [処理]プロシージャ開始
        FREE_LOG = g.appmsg.get_api_message("MSG-100001")
        g.applogger.debug(FREE_LOG)

        self.ws_db = DBConnectWs()

        # [処理]DBコネクト完了
        FREE_LOG = g.appmsg.get_api_message("MSG-100002")
        g.applogger.debug(FREE_LOG)

        # [処理]トランザクション開始
        FREE_LOG = g.appmsg.get_api_message("MSG-100004")
        self.ws_db.db_transaction_start()

    def MainFunction(self):
        """
          メイン処理
          Arguments:
            なし
          Returns:
            bool True:正常　False:異常
        """
        ret_bool = True
        OpeDelLists = []

        ret_bool, OpeDelLists = self.getOpeDelMenuList(OpeDelLists)

        for DelList in OpeDelLists:

            # [処理] テーブルから保管期限切れデータの削除開始(テーブル名:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100005", [DelList["TABLE_NAME"]])
            g.applogger.debug(FREE_LOG)

            # 論理削除日数に対応するオペレーションのレコードを廃止
            TgtDelDate = DelList['LG_DATE'].strftime('%Y/%m/%d %H:%M:%S')
            TgtLogicalOpeList = self.getTgtDelOpeList(TgtDelDate)
            self.LogicalDeleteDB(DelList, TgtLogicalOpeList)
            # 物理削除日数に対応するオペレーションのレコードを削除
            TgtDelDate = DelList['PH_DATE'].strftime('%Y/%m/%d %H:%M:%S')
            TgtPhysicsOpeList = self.getTgtDelOpeList(TgtDelDate)
            self.PhysicalDeleteDB(DelList, TgtPhysicsOpeList)
            # 削除されているオペレーションに紐づいているレコードを削除
            self.PhysicalDeleteDBbyOperationDelete(DelList)

            # [処理] テーブルから保管期限切れデータの削除完了(テーブル名:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100006", [DelList["TABLE_NAME"]])
            g.applogger.debug(FREE_LOG)
        return ret_bool

    def EndFunction(self, result):
        """
          終了処理
          Arguments:
            なし
          Returns:
            なし
        """
        if result is True:
            # コミット(レコードロックを解除)
            FREE_LOG = g.appmsg.get_api_message("MSG-100016")
            g.applogger.debug(FREE_LOG)

            self.ws_db.db_commit()

            # トランザクション終了
            FREE_LOG = g.appmsg.get_api_message("MSG-100015")
            g.applogger.debug(FREE_LOG)

            self.ws_db.db_transaction_end(True)

            if self.warning_flag == 0:
                # [処理]プロシージャ終了(正常)
                FREE_LOG = g.appmsg.get_api_message("MSG-100003")
                g.applogger.debug(FREE_LOG)

            else:
                # プロシージャ終了(警告)
                FREE_LOG = g.appmsg.get_api_message("MSG-100011")
                g.applogger.debug(FREE_LOG)

        else:
            # ロールバック(レコードロックを解除)
            FREE_LOG = g.appmsg.get_api_message("MSG-100017")
            g.applogger.debug(FREE_LOG)

            self.ws_db.db_rollback()

            # トランザクション終了
            FREE_LOG = g.appmsg.get_api_message("MSG-100015")
            g.applogger.debug(FREE_LOG)

            self.ws_db.db_transaction_end(False)

            # プロシージャ終了(異常)
            FREE_LOG = g.appmsg.get_api_message("MSG-100010")
            g.applogger.debug(FREE_LOG)

    def getOpeDelMenuList(self, OpeDelLists):
        """
          オペレーション削除管理「T_COMN_DEL_OPERATION_LIST」の情報取得
          Arguments:
            OpeDelLists: オペレーション削除管理の取得情報
          Returns:
            bool(True,False), OpeDelLists
        """

        # オペレーション削除管理情報取得
        FREE_LOG = g.appmsg.get_api_message("MSG-100020")
        g.applogger.debug(FREE_LOG)

        OpeDelLists = []
        sql = "SELECT * FROM T_COMN_DEL_OPERATION_LIST WHERE DISUSE_FLAG='0'"
        DelLists = self.ws_db.sql_execute(sql)
        if len(DelLists) == 0:
            # オペレーション削除管理　レコード未登録
            return True, OpeDelLists

        for DelList in DelLists:

            tbl_info = {}

            # メニュー・テーブル紐付からメニュー情報取得
            sql = "SELECT * FROM T_COMN_MENU_TABLE_LINK WHERE MENU_ID = %s AND DISUSE_FLAG='0'"
            MenuTblLinkLists = self.ws_db.sql_execute(sql, [DelList["MENU_NAME"]])

            if len(MenuTblLinkLists) == 0:
                # メニュー・テーブル紐付にメニューが未登録です。 (メニュー:{})
                FREE_LOG = g.appmsg.get_api_message("MSG-100019", [DelList["MENU_NAME"]])
                g.applogger.debug(FREE_LOG)
                self.warning_flag = True
                continue

            MenuTblLinkList = MenuTblLinkLists[0]

            # テーブル名を取得　該当テーブル(view定義がある場合は、View)定義にOPERATION_IDのカラムがあるか確認
            tgt_table = MenuTblLinkList["TABLE_NAME"]
            if MenuTblLinkList["VIEW_NAME"]:
                tgt_table = MenuTblLinkList["VIEW_NAME"]
            table_columns = self.ws_db.table_columns_get(tgt_table)
            if self.operation_id_column_name not in table_columns[0]:
                # メニュー・テーブル紐付にメニューが未登録です。 (メニュー:{})
                FREE_LOG = g.appmsg.get_api_message("MSG-100014", [DelList["MENU_NAME"]])
                g.applogger.debug(FREE_LOG)
                self.warning_flag = True
                continue

            tbl_info['HISTORY_TABLE_FLAG'] = MenuTblLinkList['HISTORY_TABLE_FLAG']
            tbl_info['FILE_UPLOAD_COLUMNS'] = []
            if DelList['DATA_STORAGE_PATH']:
                tbl_info['FILE_UPLOAD_COLUMNS'].append(DelList['DATA_STORAGE_PATH'])
            RestNameConfig = {}
            # メニュー・カラム紐付からメニュー情報取得
            sql = "SELECT * FROM T_COMN_MENU_COLUMN_LINK WHERE MENU_ID = %s and DISUSE_FLAG = '0'"
            MenuColLinkLists = self.ws_db.sql_execute(sql, [DelList["MENU_NAME"]])

            if len(MenuColLinkLists) == 0:
                # メニュー・カラム紐付にカラム情報が未登録です。(メニュー:{})
                FREE_LOG = g.appmsg.get_api_message("MSG-100018", [DelList["MENU_NAME"]])
                g.applogger.debug(FREE_LOG)
                self.warning_flag = True
                continue

            for MenuColLinkList in MenuColLinkLists:
                RestNameConfig[MenuColLinkList["COLUMN_NAME_REST"]] = MenuColLinkList["COL_NAME"]
                # ファイルアップロードカラム判定
                if MenuColLinkList['COLUMN_CLASS'] in ('9', '20'):
                    # ファイルアップロード配置場所が設定されている場合の判定
                    if MenuColLinkList['FILE_UPLOAD_PLACE']:
                        tbl_info['FILE_UPLOAD_COLUMNS'].append(MenuColLinkList['FILE_UPLOAD_PLACE'])
                    else:
                        tbl_info['FILE_UPLOAD_COLUMNS'].append("/uploadfiles/" + DelList["MENU_NAME"] + "/" + MenuColLinkList["COLUMN_NAME_REST"])

            # 主キー名確認
            if MenuTblLinkList['PK_COLUMN_NAME_REST'] not in RestNameConfig:
                # メニュー・カラム紐付にカラム情報が未登録です。(メニュー:{})
                FREE_LOG = g.appmsg.get_api_message("MSG-100018", [DelList["MENU_NAME"]])
                g.applogger.debug(FREE_LOG)
                self.warning_flag = True
                continue

            # p1:廃止までの日数
            tbl_info['LG_DAYS'] = DelList['LG_DAYS']
            # 廃止までの日数の妥当性チェック
            if self.is_int(tbl_info['LG_DAYS']) is False:
                # オペレーション削除管理の項番[{}]：論理削除日数[{}]が妥当ではありません。
                FREE_LOG = g.appmsg.get_api_message("MSG-100012", [DelList["ROW_ID"], DelList["LG_DAYS"]])
                g.applogger.debug(FREE_LOG)
                self.warning_flag = True
                continue

            # p2:物理削除までの日数
            tbl_info['PH_DAYS'] = DelList['PH_DAYS']
            # 廃止までの日数の妥当性チェック
            if self.is_int(tbl_info['PH_DAYS']) is False:
                # オペレーション削除管理の項番[{}]：物理削除日数[{}]が妥当ではありません。
                FREE_LOG = g.appmsg.get_api_message("MSG-100013", [DelList["ROW_ID"], DelList["PH_DAYS"]])
                g.applogger.debug(FREE_LOG)
                self.warning_flag = True
                continue

            # 保存期間算出
            tbl_info['LG_DATE'] = self.DateCalc(tbl_info['LG_DAYS'])

            tbl_info['PH_DATE'] = self.DateCalc(tbl_info['PH_DAYS'])

            # 物理テーブル名
            tbl_info['TABLE_NAME'] = MenuTblLinkList['TABLE_NAME']

            # ビュー名
            tbl_info['VIEW_NAME'] = MenuTblLinkList['VIEW_NAME']

            # 物理テーブル名（ジャーナル）
            tbl_info['TABLE_NAME_JNL'] = MenuTblLinkList['TABLE_NAME'] + "_JNL"

            # 主キー名
            tbl_info['PKEY_NAME'] = RestNameConfig[MenuTblLinkList['PK_COLUMN_NAME_REST']]

            # 最終更新者ID
            tbl_info['LAST_UPD_USER_ID'] = 110101

            # オペレーション削除管理情報 (情報:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100021", [str(tbl_info)])
            g.applogger.debug(FREE_LOG)

            OpeDelLists.append(tbl_info)

        return True, OpeDelLists

    def getTgtDelOpeList(self, TgtDelDate):
        """
          削除対象日時より古い実施予定日のオペレーションを取得
          Arguments:
            TgtDelDate:  削除対象日時
          Returns:
            TgtOpeList: 削除対象日時より古い実施予定日のオペレーション(uuid)
        """
        # 廃止されているレコードも対象にする。
        sql = '''
              SELECT
                CONCAT('"', OPERATION_ID, '"') AS OPERATION_ID
              FROM
                T_COMN_OPERATION
              WHERE
                DATE_FORMAT(OPERATION_DATE, '%%Y/%%m/%%d %%H:%%i') <= %s
              '''
        rows = self.ws_db.sql_execute(sql, [TgtDelDate])
        TgtOpeList = ""
        for row in rows:
            if len(TgtOpeList) != 0:
                TgtOpeList += ","
            TgtOpeList += row['OPERATION_ID']
        return TgtOpeList

    def LogicalDeleteDB(self, DelList, TgtOpeList):
        """
          削除対象日時より古い実施予定日のオペレーションのレコードを廃止
          Arguments:
            DelList: 削除対象のメニュー情報
            TgtOpeList:  削除対象のオペレーション
          Returns:
            なし
        """
        # 削除対象のオペレーションがない場合
        if not TgtOpeList:
            return

        # 対象メニューがビューの場合
        # オペレーションIDがないテーブルの対応「T_COMN_CONDUCTOR_NODE_INSTANCE」
        # 履歴用Viewの作成が必要
        SelectObjName = DelList['TABLE_NAME']
        if DelList['VIEW_NAME']:
            SelectObjName = DelList['VIEW_NAME']

        # 対象メニューがビューの場合、SELECTはビューを使用
        sql = '''SELECT
                   {},
                   DISUSE_FLAG,
                   LAST_UPDATE_USER
                 FROM
                   `{}`
                 WHERE
                   DISUSE_FLAG = '0' AND
                   {} in ({})
              '''.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name, TgtOpeList)

        rows = self.ws_db.sql_execute(sql)

        if len(rows) == 0:
            return

        # [処理] テーブルから保管期限切れレコードの廃止(テーブル名:{})
        FREE_LOG = g.appmsg.get_api_message("MSG-100007", [DelList["TABLE_NAME"]])
        g.applogger.debug(FREE_LOG)

        for row in rows:
            # 論理削除対象のレコードを廃止する。
            row['LAST_UPDATE_USER'] = DelList['LAST_UPD_USER_ID']
            row['DISUSE_FLAG'] = '1'
            history_table = False
            if DelList['HISTORY_TABLE_FLAG'] == '1':
                history_table = True

            self.ws_db.table_update(DelList['TABLE_NAME'], row, DelList['PKEY_NAME'], history_table)

    def PhysicalDeleteDB(self, DelList, TgtOpeList):
        """
          削除対象日時より古い実施予定日のオペレーションのレコードを削除
          Arguments:
            DelList: 削除対象のメニュー情報
            TgtOpeList:  削除対象のオペレーション
          Returns:
            なし
        """
        # 削除対象のオペレーションがない場合
        if not TgtOpeList:
            return

        # 対象メニューがビューの場合
        # オペレーションIDがないテーブルの対応「T_COMN_CONDUCTOR_NODE_INSTANCE」
        # 履歴用Viewの作成が必要
        SelectObjName = DelList['TABLE_NAME']
        if DelList['VIEW_NAME']:
            SelectObjName = DelList['VIEW_NAME']

        # 対象メニューがビューの場合、SELECTはビューを使用
        sql = '''SELECT
                   {}
                 FROM
                   `{}`
                 WHERE
                   {} in ({})
              '''.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name, TgtOpeList)

        rows = self.ws_db.sql_execute(sql)

        PkeyList = []
        PkeyString = ""
        # 物理対象のレコードのPkeyを取得
        for row in rows:
            PkeyList.append(row[DelList['PKEY_NAME']])
            if len(PkeyString) != 0:
                PkeyString += ","
            PkeyString += "'" + row[DelList['PKEY_NAME']] + "'"

        # 削除対象のレコードがない場合
        if len(PkeyList) == 0:
            return

        # 物理対象のレコードに紐づいているファイルアップロードカラムのファイルを削除
        for Pkey in PkeyList:
            for TgtPath in DelList['FILE_UPLOAD_COLUMNS']:
                DelPath = "{}/{}/{}".format(self.getDataRelayStorageDir(), TgtPath, Pkey)
                if os.path.isdir(DelPath):
                    # [処理] テーブルに紐づく不要ディレクトリ削除(テーブル名:({}) ディレクトリ名:({}))
                    FREE_LOG = g.appmsg.get_api_message("MSG-100009", [DelList["TABLE_NAME"], DelPath])
                    g.applogger.debug(FREE_LOG)
                    shutil.rmtree(DelPath)

        # [処理] テーブルから保管期限切れレコードの物理削除(テーブル名:{})
        FREE_LOG = g.appmsg.get_api_message("MSG-100008", [DelList["TABLE_NAME"]])
        g.applogger.debug(FREE_LOG)

        sql = '''DELETE
                 FROM
                   `{}`
                 WHERE
                   {} in ({})
              '''.format(DelList['TABLE_NAME'], DelList['PKEY_NAME'], PkeyString)

        rows = self.ws_db.sql_execute(sql)

        if DelList['HISTORY_TABLE_FLAG'] == '1':
            sql = '''DELETE
                     FROM
                       `{}`
                     WHERE
                       {} in ({})
                  '''.format(DelList['TABLE_NAME_JNL'], DelList['PKEY_NAME'], PkeyString)

            rows = self.ws_db.sql_execute(sql)

            # [処理] テーブルから保管期限切れレコードの物理削除(テーブル名:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100008", [DelList["TABLE_NAME_JNL"]])
            g.applogger.debug(FREE_LOG)

    def PhysicalDeleteDBbyOperationDelete(self, DelList):
        """
          削除されているオペレーションに紐づいているオペレーションのレコードを削除
          Arguments:
            DelList: 削除対象のメニュー情報
          Returns:
            なし
        """
        MasterRows, JournalRows = self.getOperationDeleteRows(DelList)

        PkeyList = []
        PkeyString = ""
        # 物理対象のレコードのPkeyを取得
        for row in MasterRows:
            PkeyList.append(row[DelList['PKEY_NAME']])
            if len(PkeyString) != 0:
                PkeyString += ","
            PkeyString += "'" + row[DelList['PKEY_NAME']] + "'"

        # 削除対象のレコードがある場合
        if len(PkeyList) != 0:
            # 物理対象のレコードに紐づいているファイルアップロードカラムのファイルを削除
            for Pkey in PkeyList:
                for TgtPath in DelList['FILE_UPLOAD_COLUMNS']:
                    DelPath = "{}/{}/{}".format(self.getDataRelayStorageDir(), TgtPath, Pkey)
                    if os.path.isdir(DelPath):
                        # [処理] テーブルに紐づく不要ディレクトリ削除(テーブル名:({}) ディレクトリ名:({}))
                        FREE_LOG = g.appmsg.get_api_message("MSG-100009", [DelList["TABLE_NAME"], DelPath])
                        g.applogger.debug(FREE_LOG)
                        shutil.rmtree(DelPath)

            sql = '''DELETE
                    FROM
                    `{}`
                    WHERE
                    {} in ({})
                '''.format(DelList['TABLE_NAME'], DelList['PKEY_NAME'], PkeyString)

            rows = self.ws_db.sql_execute(sql)

            #	[処理] 削除されたオペレーションに紐づいているレコードの物理削除(テーブル名:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100022", [DelList["TABLE_NAME"]])
            g.applogger.debug(FREE_LOG)

        PkeyList = []
        PkeyString = ""
        # 物理対象の履歴レコードのPkeyを取得
        for row in JournalRows:
            PkeyList.append(row[DelList['PKEY_NAME']])
            if len(PkeyString) != 0:
                PkeyString += ","
            PkeyString += "'" + row[DelList['PKEY_NAME']] + "'"

            sql = '''DELETE
                     FROM
                       `{}`
                     WHERE
                       {} in ({})
                  '''.format(DelList['TABLE_NAME_JNL'], DelList['PKEY_NAME'], PkeyString)

            rows = self.ws_db.sql_execute(sql)

            #	[処理] 削除されたオペレーションに紐づいているレコードの物理削除(テーブル名:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100022", [DelList["TABLE_NAME_JNL"]])
            g.applogger.debug(FREE_LOG)

    def getOperationDeleteRows(self, DelList):
        # 対象メニューがビューの場合
        # オペレーションIDがないテーブルの対応「T_COMN_CONDUCTOR_NODE_INSTANCE」
        # 履歴用Viewの作成が必要
        SelectObjName = DelList['TABLE_NAME']
        if DelList['VIEW_NAME']:
            SelectObjName = DelList['VIEW_NAME']

        MasterRows = []
        JournalRows = []
        # Terraform作業管理系テーブルについて、RUN_MODE:3(リソース削除)の場合オペレーションIDが指定されないので、削除対象として除外する。
        Terrafomesql = '''
                    select {} from `{}` TAB_A
                    where NOT EXISTS
                        (select
                            *
                        from
                            (select * from T_COMN_OPERATION) TAB_B
                        where
                            TAB_A.{} = TAB_B.OPERATION_ID
                        ) AND NOT TAB_A.RUN_MODE = '4'
                    '''

        Otherssql = '''
                    select {} from `{}` TAB_A
                    where NOT EXISTS
                        (select
                            *
                        from
                            (select * from T_COMN_OPERATION) TAB_B
                        where
                            TAB_A.{} = TAB_B.OPERATION_ID
                        )
                    '''

        OpeDelJnlPkeyLists = {}
        # 対象メニューがビューの場合、SELECTはビューを使用
        if DelList['TABLE_NAME'] in ("T_TERE_EXEC_STS_INST","T_TERC_EXEC_STS_INST"):
            sql = Terrafomesql.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name)
        else:
            sql = Otherssql.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name)

        MasterRows = self.ws_db.sql_execute(sql)

        if DelList['HISTORY_TABLE_FLAG'] == '1':
            if DelList['TABLE_NAME'] in ("T_TERE_EXEC_STS_INST","T_TERC_EXEC_STS_INST"):
                sql = Terrafomesql.format(DelList['PKEY_NAME'], SelectObjName + "_JNL", self.operation_id_column_name)
            else:
                sql = Otherssql.format(DelList['PKEY_NAME'], SelectObjName + "_JNL", self.operation_id_column_name)

            JournalRows = self.ws_db.sql_execute(sql)

        return MasterRows, JournalRows

    def getDataRelayStorageDir(self):
        """
          データリレイストレージのパス取得
        Arguments:
          なし
        Returns:
          データリレイストレージのパス
        """
        return os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))

    def is_int(self, int_value):
        """
          数値判定
        Arguments:
          int_value: 数値
        Returns:
          bool True:数値 False:数値以外
        """
        if not int_value:
            return False
        try:
            if not isinstance(int_value, int):
                int(int_value, 10)
        except ValueError:
            return False
        if int_value <= 0:
            return False

    def DateCalc(self, AddDay):
        """
          現在時刻に日数加算
        Arguments:
          AddDay: 加算日数
        Returns:
          現在時刻に日数減算した日時
        """
        NowDate = datetime.datetime.now()
        AddDate = datetime.timedelta(days=AddDay)
        return NowDate - AddDate


def backyard_main(organization_id, workspace_id):
    """
      バックヤードメイン処理
    Arguments:
      organization_id: organization id
      workspace_id: workspace id
    Returns:
      なし
    """
    g.applogger.debug("ita_by_execinstance_dataautoclean backyard_main started")

    obj = MainFunctions()

    obj.InitFunction()

    ret = obj.MainFunction()

    obj.EndFunction(ret)
