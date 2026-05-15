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

from flask import g

from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs
from common_libs.common.util import retry_rmtree


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
        g.applogger.info(FREE_LOG)

        self.ws_db = DBConnectWs()

        # [処理]DBコネクト完了
        FREE_LOG = g.appmsg.get_api_message("MSG-100002")
        g.applogger.info(FREE_LOG)

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

        # max_allowed_packetの取得
        _sql = "show variables like 'max_allowed_packet';"
        _show_variables = self.ws_db.sql_execute(_sql)
        max_allowed_packet = _show_variables[0]['Value'] if _show_variables[0]['Variable_name'] == 'max_allowed_packet' else 30000
        g.max_allowed_packet = int(max_allowed_packet)
        delete_batch_size = int(os.getenv("DELETE_BATCH_SIZE", 1000))
        # 削除バッチサイズの設定(安全のために、上限値はmax_allowed_packetの値とする)
        g.delete_batch_size = delete_batch_size if delete_batch_size < g.max_allowed_packet else g.max_allowed_packet
        g.applogger.info(f"{g.delete_batch_size=}, {g.max_allowed_packet=}")

        ret_bool, OpeDelLists = self.getOpeDelMenuList(OpeDelLists)
        g.applogger.info(f"OpeDelLists {len(OpeDelLists)}")

        for DelList in OpeDelLists:
            g.applogger.info(f"DelList {DelList['TABLE_NAME']} LG_DATE {DelList['LG_DATE']} PH_DATE {DelList['PH_DATE']}")

            # [処理] テーブルから保管期限切れデータの削除開始(テーブル名:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100005", [DelList["TABLE_NAME"]])
            g.applogger.info(FREE_LOG)

            try:
                g.applogger.info(f"Start LogicalDeleteDB ({DelList['TABLE_NAME']})")
                self.ws_db.db_transaction_start()
                # 論理削除日数に対応するオペレーションのレコードを廃止
                TgtDelDate = DelList['LG_DATE'].strftime('%Y/%m/%d %H:%M:%S')
                TgtLogicalOpeList = self.getTgtDelOpeList(TgtDelDate)
                self.LogicalDeleteDB(DelList, TgtLogicalOpeList)
                self.ws_db.db_transaction_end(True)
                g.applogger.info(f"End LogicalDeleteDB ({DelList['TABLE_NAME']})")
            except Exception as e:
                g.applogger.error(f"Error occurred while logical deleting records from {DelList['TABLE_NAME']}")
                g.applogger.error(e)
                self.ws_db.db_transaction_end(False)

            g.applogger.info(f"Start PhysicalDeleteDB ({DelList['TABLE_NAME']})")
            # 物理削除日数に対応するオペレーションのレコードを削除
            TgtDelDate = DelList['PH_DATE'].strftime('%Y/%m/%d %H:%M:%S')
            TgtPhysicsOpeList = self.getTgtDelOpeList(TgtDelDate)
            self.PhysicalDeleteDB(DelList, TgtPhysicsOpeList)
            g.applogger.info(f"End PhysicalDeleteDB ({DelList['TABLE_NAME']})")

            g.applogger.info(f"Start PhysicalDeleteDBbyOperationDelete ({DelList['TABLE_NAME']})")
            # 削除されているオペレーションに紐づいているレコードを削除
            self.PhysicalDeleteDBbyOperationDelete(DelList)
            g.applogger.info(f"End PhysicalDeleteDBbyOperationDelete ({DelList['TABLE_NAME']})")

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

            # プロシージャ終了(異常)
            FREE_LOG = g.appmsg.get_api_message("MSG-100010")
            g.applogger.debug(FREE_LOG)

        self.ws_db.db_disconnect()
        self.ws_db = None

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
                g.applogger.info(FREE_LOG)
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
                g.applogger.info(FREE_LOG)
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
                g.applogger.info(FREE_LOG)
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
                g.applogger.info(FREE_LOG)
                self.warning_flag = True
                continue

            # p1:廃止までの日数
            tbl_info['LG_DAYS'] = DelList['LG_DAYS']
            # 廃止までの日数の妥当性チェック
            if self.is_int(tbl_info['LG_DAYS']) is False:
                # オペレーション削除管理の項番[{}]：論理削除日数[{}]が妥当ではありません。
                FREE_LOG = g.appmsg.get_api_message("MSG-100012", [DelList["ROW_ID"], DelList["LG_DAYS"]])
                g.applogger.info(FREE_LOG)
                self.warning_flag = True
                continue

            # p2:物理削除までの日数
            tbl_info['PH_DAYS'] = DelList['PH_DAYS']
            # 廃止までの日数の妥当性チェック
            if self.is_int(tbl_info['PH_DAYS']) is False:
                # オペレーション削除管理の項番[{}]：物理削除日数[{}]が妥当ではありません。
                FREE_LOG = g.appmsg.get_api_message("MSG-100013", [DelList["ROW_ID"], DelList["PH_DAYS"]])
                g.applogger.info(FREE_LOG)
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
                OPERATION_ID
              FROM
                T_COMN_OPERATION
              WHERE
                DATE_FORMAT(OPERATION_DATE, '%%Y/%%m/%%d %%H:%%i') <= %s
              '''
        rows = self.ws_db.sql_execute(sql, [TgtDelDate])
        TgtOpeList = [row['OPERATION_ID'] for row in rows]
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
            g.applogger.info(f"No matching operations found for deletion. ({DelList['TABLE_NAME']})")
            return

        # 対象メニューがビューの場合
        # オペレーションIDがないテーブルの対応「T_COMN_CONDUCTOR_NODE_INSTANCE」
        # 履歴用Viewの作成が必要
        SelectObjName = DelList['TABLE_NAME']
        if DelList['VIEW_NAME']:
            SelectObjName = DelList['VIEW_NAME']
        # 削除対象のオペレーションIDリストを分割して処理する。
        # TgtOpeListに、削除日数に該当するオペレーションによって、SQLのIN句のパラメータ数が増減するため、分割して処理する。
        n = min(int(g.delete_batch_size), len(TgtOpeList))
        for i in range(0, len(TgtOpeList), int(n)):
            rows = []
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
                '''.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name, ', '.join(['%s'] * len(TgtOpeList[i: int(i + n)])))

            # 論理削除対象のcursorを取得
            _cursor = self.ws_db.sql_execute_cursor(sql, TgtOpeList[i: int(i + n)])

            # [処理] テーブルから保管期限切れレコードの廃止(テーブル名:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100007", [DelList["TABLE_NAME"]])
            g.applogger.debug(FREE_LOG)

            # 論理削除対象のレコードを分割取得(読み飛ばし防止のため、一度取得してから廃止処理を行う)
            with _cursor as _cur:
                while True:
                    _rows = _cur.fetchmany(g.delete_batch_size)
                    if len(_rows) == 0:
                        del _rows
                        # データ0件の為、break
                        break
                    rows.extend(_rows)
            g.applogger.info(f"Fetched {len(rows)} rows for logical deletion from {DelList['TABLE_NAME']}") if len(rows) else None

            # 論理削除対象のレコードを廃止する。
            for row in rows:
                # 論理削除対象のレコードを廃止する。
                row['LAST_UPDATE_USER'] = DelList['LAST_UPD_USER_ID']
                row['DISUSE_FLAG'] = '1'
                history_table = False
                if DelList['HISTORY_TABLE_FLAG'] == '1':
                    history_table = True

                g.applogger.debug(f"Executing UPDATE: TABLE_NAME: {DelList['TABLE_NAME']}, ID: {row.get(DelList['PKEY_NAME'])}, HISTORY_TABLE: {history_table}")
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

        # 削除対象のオペレーションIDリストを分割して処理する。
        # TgtOpeListに、削除日数に該当するオペレーションによって、SQLのIN句のパラメータ数が増減するため、分割して処理する。
        n = min(int(g.delete_batch_size), len(TgtOpeList))
        for i in range(0, len(TgtOpeList), int(n)):
            # 対象メニューがビューの場合、SELECTはビューを使用
            sql = '''SELECT
                       {}
                     FROM
                       `{}`
                     WHERE
                       {} in ({})
                  '''.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name, ', '.join(['%s'] * len(TgtOpeList[i: int(i + n)])))

            # 物理削除対象のcursorを取得
            _cursor = self.ws_db.sql_execute_cursor(sql, TgtOpeList[i: int(i + n)])

            g.applogger.debug(f"PhysicalDeleteDB: {DelList['TABLE_NAME']} rows to physical delete: {_cursor.rowcount}")

            all_pkeys = []
            # 物理削除対象のレコードを分割取得(読み飛ばし防止のため、一度取得してから廃止処理を行う)
            with _cursor as _cur:
                while True:
                    rows = _cur.fetchmany(g.delete_batch_size)
                    if len(rows) == 0:
                        del rows
                        # データ0件の為、break
                        break
                    # 取得したレコードを一時リストに格納（SELECTカーソルへの影響を避けるため）
                    for row in rows:
                        all_pkeys.append(row[DelList['PKEY_NAME']])
            g.applogger.info(f"Fetched {len(all_pkeys)} rows for physical deletion from {DelList['TABLE_NAME']}")

            # 削除フェーズ：SELECTカーソルを閉じた後にDELETEを実行する
            for j in range(0, len(all_pkeys), int(g.delete_batch_size)):
                PkeyList = all_pkeys[j: j + int(g.delete_batch_size)]

                # 物理削除対象のレコードのファイル削除処理
                for Pkey in PkeyList:
                    # 物理対象のレコードに紐づいているファイルアップロードカラムのファイルを削除
                    for TgtPath in DelList['FILE_UPLOAD_COLUMNS']:
                        DelPath = "{}/{}/{}".format(self.getDataRelayStorageDir(), TgtPath, Pkey)
                        # [処理] テーブルに紐づく不要ディレクトリ削除(テーブル名:({}) ディレクトリ名:({}))
                        FREE_LOG = g.appmsg.get_api_message("MSG-100009", [DelList["TABLE_NAME"], DelPath])
                        g.applogger.debug(FREE_LOG)
                        retry_rmtree(DelPath)

                # [処理] テーブルから保管期限切れレコードの物理削除(テーブル名:{})
                FREE_LOG = g.appmsg.get_api_message("MSG-100008", [DelList["TABLE_NAME"]])
                g.applogger.debug(FREE_LOG)

                # 物理削除対象のレコードのファイル削除処理が完了した後、レコード・履歴レコードを削除する。
                try:
                    g.applogger.debug(f"Processing batch: {DelList['TABLE_NAME']} = {len(PkeyList)}")
                    _prepared_list = ','.join(list(map(lambda a: "%s", PkeyList)))
                    sql = f"DELETE FROM `{DelList['TABLE_NAME']}` WHERE `{DelList['PKEY_NAME']}` in ({_prepared_list})"
                    self.ws_db.db_transaction_start()
                    self.ws_db.sql_execute(sql, PkeyList)
                    self.ws_db.db_transaction_end(True)
                except Exception as e:
                    g.applogger.error(e)
                    g.applogger.error(f"Error occurred while deleting records from {DelList['TABLE_NAME']}")
                    self.ws_db.db_transaction_end(False)

                if DelList['HISTORY_TABLE_FLAG'] == '1':
                    try:
                        g.applogger.debug(f"Processing batch: {DelList['TABLE_NAME_JNL']} = {len(PkeyList)}")
                        _prepared_list_jnl = ','.join(list(map(lambda a: "%s", PkeyList)))
                        sql = f"DELETE FROM `{DelList['TABLE_NAME_JNL']}` WHERE `{DelList['PKEY_NAME']}` in ({_prepared_list_jnl})"
                        self.ws_db.db_transaction_start()
                        self.ws_db.sql_execute(sql, PkeyList)
                        self.ws_db.db_transaction_end(True)
                    except Exception as e:
                        g.applogger.error(e)
                        g.applogger.error(f"Error occurred while deleting records from {DelList['TABLE_NAME_JNL']}")
                        self.ws_db.db_transaction_end(False)

                    # [処理] テーブルから保管期限切れレコードの物理削除(テーブル名:{})
                    FREE_LOG = g.appmsg.get_api_message("MSG-100008", [DelList["TABLE_NAME_JNL"]])
                    g.applogger.debug(FREE_LOG)

    def PhysicalDeleteDBbyOperationDelete(self, DelList):
        """
          削除されているオペレーションに紐づいているメニューのレコードを削除
          Arguments:
            DelList: 削除対象のメニュー情報
          Returns:
            なし
        """
        # 削除対象テーブルのカーソルを取得
        MasterRows, JournalRows = self.getOperationDeleteRows(DelList)

        # 削除対象レコードのブロック基準日時の設定
        # オペレーションに紐づかないレコードは、最終更新日時からXX時間経過したレコードのみ物理削除対象とする。
        block_hours = 24
        block_time = datetime.datetime.now() - datetime.timedelta(hours=block_hours)

        # 読み飛ばし防止のため、カーソルを閉じた後に削除する
        all_master_pkeys = []
        if MasterRows:
            # 削除対象のレコードを分割取得(読み飛ばし防止のため、一度取得してから廃止処理を行う)
            with MasterRows as _cur:
                while True:
                    rows = _cur.fetchmany(g.delete_batch_size)
                    if len(rows) == 0:
                        del rows
                        # データ0件の為、break
                        break
                    # 取得したレコードを一時リストに格納
                    for row in rows:
                        #  取得したレコードの最終更新日時がブロック日時より古い場合、物理削除対象とする
                        if row['LAST_UPDATE_TIMESTAMP'] < block_time:
                            all_master_pkeys.append(row[DelList['PKEY_NAME']])

        g.applogger.info(f"Fetched {len(all_master_pkeys)} rows for physical deletion(OperationDeleted) from {DelList['TABLE_NAME']}")

        # 本体テーブルの削除フェーズ：SELECTカーソルを閉じた後に実行
        for j in range(0, len(all_master_pkeys), int(g.delete_batch_size)):
            PkeyList = all_master_pkeys[j: j + int(g.delete_batch_size)]
            for Pkey in PkeyList:
                # 物理対象のレコードに紐づいているファイルアップロードカラムのファイルを削除
                for TgtPath in DelList['FILE_UPLOAD_COLUMNS']:
                    DelPath = "{}/{}/{}".format(self.getDataRelayStorageDir(), TgtPath, Pkey)
                    # [処理] テーブルに紐づく不要ディレクトリ削除(テーブル名:({}) ディレクトリ名:({}))
                    FREE_LOG = g.appmsg.get_api_message("MSG-100009", [DelList["TABLE_NAME"], DelPath])
                    g.applogger.debug(FREE_LOG)
                    retry_rmtree(DelPath)

            # 物理削除対象のレコードのファイル削除処理が完了した後、レコードを削除する。
            try:
                g.applogger.debug(f"Processing batch: {DelList['TABLE_NAME']} = {len(PkeyList)} / {len(all_master_pkeys)}")
                _prepared_list_mr = ','.join(list(map(lambda a: "%s", PkeyList)))
                sql = f"DELETE FROM `{DelList['TABLE_NAME']}` WHERE `{DelList['PKEY_NAME']}` in ({_prepared_list_mr})"
                self.ws_db.db_transaction_start()
                self.ws_db.sql_execute(sql, PkeyList)
                self.ws_db.db_transaction_end(True)
            except Exception as e:
                g.applogger.error(e)
                g.applogger.error(f"Error occurred while deleting records from {DelList['TABLE_NAME']}")
                self.ws_db.db_transaction_end(False)

        # [処理] 削除されたオペレーションに紐づいているレコードの物理削除(テーブル名:{})
        FREE_LOG = g.appmsg.get_api_message("MSG-100022", [DelList["TABLE_NAME"]])
        g.applogger.debug(FREE_LOG)

        # 履歴テーブルがない場合は、処理を終了する。(HISTORY_TABLE_FLAG='1'の場合のみJournalRowsが返されるため、JournalRowsの有無で判断する)
        if JournalRows is None:
            g.applogger.debug(f"No matching records found for physical deletion by operation delete. ({DelList['TABLE_NAME_JNL']})")
            return

        # 読み飛ばし防止のため、履歴テーブルのPKEYを先行して全件取得する
        all_journal_pkeys = []
        # 削除対象の履歴レコードを分割取得
        with JournalRows as _cur:
            while True:
                rows = _cur.fetchmany(g.delete_batch_size)
                if len(rows) == 0:
                    del rows
                    # データ0件の為、break
                    break
                # 物理対象の履歴レコードのPkeyを取得
                for row in rows:
                    #  取得したレコードの最終更新日時がブロック日時より古い場合、物理削除対象とする
                    if row['LAST_UPDATE_TIMESTAMP'] < block_time:
                        all_journal_pkeys.append(row[DelList['PKEY_NAME']])

        g.applogger.info(f"Fetched {len(all_journal_pkeys)} rows for physical deletion(OperationDeleted) from {DelList['TABLE_NAME_JNL']}")

        # 履歴テーブルの削除フェーズ
        for j in range(0, len(all_journal_pkeys), int(g.delete_batch_size)):
            PkeyList = all_journal_pkeys[j: j + int(g.delete_batch_size)]

            # 物理削除対象のレコードを削除する。
            try:
                g.applogger.debug(f"Processing batch: {DelList['TABLE_NAME_JNL']} = {len(PkeyList)} / {len(all_journal_pkeys)}")
                _prepared_list_jnl = ','.join(list(map(lambda a: "%s", PkeyList)))
                sql = f"DELETE FROM `{DelList['TABLE_NAME_JNL']}` WHERE `{DelList['PKEY_NAME']}` in ({_prepared_list_jnl})"
                self.ws_db.db_transaction_start()
                self.ws_db.sql_execute(sql, PkeyList)
                self.ws_db.db_transaction_end(True)
            except Exception as e:
                g.applogger.error(e)
                g.applogger.error(f"Error occurred while deleting records from {DelList['TABLE_NAME_JNL']}")
                self.ws_db.db_transaction_end(False)

        # [処理] 削除されたオペレーションに紐づいているレコードの物理削除(テーブル名:{})
        FREE_LOG = g.appmsg.get_api_message("MSG-100022", [DelList["TABLE_NAME_JNL"]])
        g.applogger.debug(FREE_LOG)

    def getOperationDeleteRows(self, DelList):
        """
            オペレーション削除対象レコードの取得
        Arguments:
            DelList: 削除対象リスト
        Returns:
            MasterRows: マスターレコードのCursor
            JournalRows: ジャーナルレコードのCursor
        """
        # 対象メニューがビューの場合
        # オペレーションIDがないテーブルの対応「T_COMN_CONDUCTOR_NODE_INSTANCE」
        # 履歴用Viewの作成が必要
        SelectObjName = DelList['TABLE_NAME']
        if DelList['VIEW_NAME']:
            SelectObjName = DelList['VIEW_NAME']

        MasterRows = None
        JournalRows = None
        # Terraform作業管理系テーブルについて、RUN_MODE:3(リソース削除)の場合オペレーションIDが指定されないので、削除対象として除外する。
        Terrafomesql = '''
                    select {}, `LAST_UPDATE_TIMESTAMP` from `{}` TAB_A
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
                    select {}, `LAST_UPDATE_TIMESTAMP` from `{}` TAB_A
                    where NOT EXISTS
                        (select
                            *
                        from
                            (select * from T_COMN_OPERATION) TAB_B
                        where
                            TAB_A.{} = TAB_B.OPERATION_ID
                        )
                    '''

        # 対象メニューがビューの場合、SELECTはビューを使用
        if DelList['TABLE_NAME'] in ("T_TERE_EXEC_STS_INST", "T_TERC_EXEC_STS_INST"):
            sql = Terrafomesql.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name)
        else:
            sql = Otherssql.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name)

        MasterRows = self.ws_db.sql_execute_cursor(sql)

        if DelList['HISTORY_TABLE_FLAG'] == '1':
            if DelList['TABLE_NAME'] in ("T_TERE_EXEC_STS_INST", "T_TERC_EXEC_STS_INST"):
                sql = Terrafomesql.format(DelList['PKEY_NAME'], SelectObjName + "_JNL", self.operation_id_column_name)
            else:
                sql = Otherssql.format(DelList['PKEY_NAME'], SelectObjName + "_JNL", self.operation_id_column_name)
            JournalRows = self.ws_db.sql_execute_cursor(sql)

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
        return True

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

    try:
        ret = False
        ret = obj.MainFunction()
    finally:
        obj.EndFunction(ret)
