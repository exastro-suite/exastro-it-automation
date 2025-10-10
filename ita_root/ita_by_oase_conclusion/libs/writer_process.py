# Copyright 2025 NEC Corporation#
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

import os
import psutil
import multiprocessing
import time
from flask import Flask, g
from bson.objectid import ObjectId

from pymongo.operations import InsertOne, UpdateOne
from common_libs.conductor.classes.exec_util import *

from common_libs.common.queuing_logger import QueuingAppLogClient
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.common.message_class import MessageTemplate
from common_libs.common.mongoconnect.const import Const as mongoConst

from common_libs.oase.const import oaseConst

class WriterProcessException(Exception):
    """書き込みプロセス例外クラス
    """
    pass

class WriterProcessManager():
    """書き込みプロセスとのインターフェース
    """
    _queue = None       # 書き込みを要求するQueue (oase conclusionメインプロセス ⇒ 書き込みプロセス)
    _complite = None    # 完了を応答するQueue (書き込みプロセス ⇒ oase conclusionメインプロセス)
    _exited = None      # 書き込みプロセス終了確認用 (0:起動中, 1:終了)
    _process = None     # 書き込みプロセス

    @classmethod
    def start_process(cls):
        """書き込みプロセスの起動
        """
        # 書き込みを要求するQueue
        cls._queue = multiprocessing.Queue()
        # 完了を応答するQueue
        cls._complite = multiprocessing.Queue()

        # 書き込みプロセス終了確認用 (0:起動中, 1:終了)
        #   process.is_alive() / process.join() だけではプロセスが終了しているかどうかの確認ができない場合があるため（数十回に1度程度の頻度で発生）
        #   共有メモリを使用してプロセスを終了していいかを判定する
        cls._exited = multiprocessing.Value('i', 0)

        # 書き込みプロセス起動
        cls._process = multiprocessing.Process(target=WriterProcess.main, args=(os.getpid(), cls._queue, cls._complite, cls._exited), daemon=True)
        cls._process.start()

    @classmethod
    def stop_process(cls):
        """書き込みプロセスの停止
        """
        # 書き込みプロセスに終了指示を送る
        cls._queue.put({"action": "exit"})

        # 書き込みプロセスの終了を待つ
        while cls._exited.value == 0 and cls._process.is_alive():
            time.sleep(0.1)

        # プロセスが終了していないケースもあるのでkillする
        cls._process.kill()

        # cls変数をクリアする
        cls._queue = None
        cls._complite = None
        cls._exited = None
        cls._process = None

    @classmethod
    def start_workspace_processing(cls, oraganization_id: str, workspace_id: str):
        """ワークスペースの処理開始を通知プロセスに伝える

        Args:
            oraganization_id (str): _description_
            workspace_id (str): _description_
        """
        if cls._process.is_alive() is False:
            # プロセスが起動していない場合は起動する
            cls.start_process()

        cls._queue.put({
            "action": "start_workspace_processing",
            "oraganization_id": oraganization_id,
            "workspace_id": workspace_id
        })

    @classmethod
    def flush_buffer(cls):
        """バッファの内容を強制的にDBに書き込む
        """
        cls._queue.put({
            "action": "flush_buffer"
        })
        # 処理の完了を待つ
        while True:
            try:
                cls._complite.get(timeout=5.0)
                break
            except multiprocessing.queues.Empty:
                if cls._process.is_alive() is False:
                    # プロセスが終了してしまった場合は待っても帰ってこないので終了する
                    break
                else:
                    # 再度完了を待つ
                    continue

    @classmethod
    def finish_workspace_processing(cls):
        """ワークスペースの処理終了を通知プロセスに伝える
        """
        cls._queue.put({
            "action": "finish_workspace_processing"
        })
        # 処理の完了を待つ
        while True:
            try:
                cls._complite.get(timeout=5.0)
                break
            except multiprocessing.queues.Empty:
                if cls._process.is_alive() is False:
                    # プロセスが終了してしまった場合は待っても帰ってこないので終了する
                    break
                else:
                    # 再度完了を待つ
                    continue

    @classmethod
    def insert_labeled_event_collection(cls, dict: dict) -> ObjectId:
        """labeled_event_collectionにインサートを依頼する

        Args:
            dict (dict): insertするドキュメント

        Returns:
            ObjectId: 生成したオブジェクトID
        """
        if cls._process.is_alive() is False:
            raise WriterProcessException("WriterProcess is not running.")

        if "_id" not in dict:
            # ObjectIdを作成する
            my_object_id = ObjectId()
            dict["_id"] = my_object_id

        cls._queue.put({
            "action": "insert_labeled_event_collection",
            "dict": dict
        })
        return dict["_id"]
        
    @classmethod
    def update_labeled_event_collection(cls, filter, update):
        """labeled_event_collectionにupdateを依頼する

        Args:
            filter (dict): update対象
            update (dict): updateするドキュメント
        """
        if cls._process.is_alive() is False:
            raise WriterProcessException("WriterProcess is not running.")

        cls._queue.put({
            "action": "update_labeled_event_collection",
            "filter": filter,
            "update": update
        })

    @classmethod
    def insert_oase_action_log(cls, data: dict) -> list[dict]:
        if cls._process.is_alive() is False:
            raise WriterProcessException("WriterProcess is not running.")

        # キーを先に設定する
        data['ACTION_LOG_ID'] = DBConnectWs.genarate_primary_key_value()
        # 書き込みプロセスにインサートを依頼する
        cls._queue.put({
            "action": "insert_oase_action_log",
            "data": data
        })
        return [data]

    @classmethod
    def update_oase_action_log(cls, data: dict):
        if cls._process.is_alive() is False:
            raise WriterProcessException("WriterProcess is not running.")

        # 書き込みプロセスにupdateを依頼する
        cls._queue.put({
            "action": "update_oase_action_log",
            "data": data
        })


class WriterProcess():
    """書き込みプロセス
    """
    _process_name = "WriterProcess"
    _objdbca = None
    _ws_mongo = None
    _labeled_event_collection = None
    _t_oase_action_log = None

    @classmethod
    def main(cls, ppid: int, queue: multiprocessing.Queue, complite: multiprocessing.Queue, exited):
        """書き込みプロセスのメインループ

        Args:
            ppid (int): 親プロセスID
            queue (multiprocessing.Queue): 書き込みプロセスに書き込みを依頼するためのQueue
            complite (multiprocessing.Queue): 書き込みプロセスから完了を応答するためのQueue
            exited (multiprocessing.Value): 書き込みプロセス終了確認用 (0:起動中, 1:終了)
        """
        # 初期化処理
        flask_app = Flask(__name__)

        with flask_app.app_context():
            try:
                cls._initialize()
                g.applogger.info(g.appmsg.get_log_message("BKY-90077", [cls._process_name, "Start"]))

                # メインループ処理
                cls._main_loop(ppid, queue, complite)

            finally:
                # DBコネクションを切断
                if cls._objdbca is not None:
                    cls._objdbca.db_disconnect()
                    cls._objdbca = None

                # mongodbを切断
                if cls._ws_mongo is not None:
                    cls._labeled_event_collection = None
                    cls._ws_mongo.disconnect()
                    cls._ws_mongo = None

                # 終了
                g.applogger.info(g.appmsg.get_log_message("BKY-90077", [cls._process_name, "Exit"]))
                # ここまで到達すればprocessは終了して良いので、終了済みフラグをONにする
                exited.value = 1
        exit(0)

    @classmethod
    def _initialize(cls):
        """初期化処理
        """
        g.LANGUAGE = os.environ.get("LANGUAGE")
        g.appmsg = MessageTemplate(g.LANGUAGE)
        g.applogger = QueuingAppLogClient().get_logger()
        g.USER_ID = os.environ.get("USER_ID")
        g.applogger.set_env_message()

    @classmethod
    def _main_loop(cls, ppid: int, queue: multiprocessing.Queue, complite: multiprocessing.Queue):
        """メインループ処理

        Args:
            ppid (int): 親プロセスID
            queue (multiprocessing.Queue): 書き込みプロセスに書き込みを依頼するためのQueue
            complite (multiprocessing.Queue): 書き込みプロセスから完了を応答するためのQueue
        """
        while True:
            try:
                # Queueからの指示を待つ
                data = queue.get(timeout=5)
            except multiprocessing.queues.Empty:
                if psutil.pid_exists(ppid) is False:
                    # 親プロセスが存在しない場合は終了する
                    cls.exit_process()
                    g.applogger.info(g.appmsg.get_log_message("BKY-90078", [cls._process_name]))
                    break
                else:
                    # 再度queueからの指示を待つ
                    continue
            try:
                # 指示に応じた処理を実行する
                if data["action"] == "insert_labeled_event_collection":
                    cls._labeled_event_collection.insert(data["dict"])

                elif data["action"] == "update_labeled_event_collection":
                    cls._labeled_event_collection.update(data["filter"], data["update"])

                elif data["action"] == "insert_oase_action_log":
                    cls._t_oase_action_log.insert(data["data"])

                elif data["action"] == "update_oase_action_log":
                    cls._t_oase_action_log.update(data["data"])

                elif data["action"] == "start_workspace_processing":
                    cls._start_workspace_processing(data["oraganization_id"], data["workspace_id"])
                
                elif data["action"] == "flush_buffer":
                    cls._flush_buffer(complite)

                elif data["action"] == "finish_workspace_processing":
                    cls._finish_workspace_processing(complite)

                elif data["action"] == "exit":
                    cls.exit_process()
                    break

            except Exception as e:
                g.applogger.error(g.appmsg.get_log_message("BKY-90081", [cls._process_name, e]))
                g.applogger.error("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(traceback.format_exc())))

    @classmethod
    def _start_workspace_processing(cls, oraganization_id: str, workspace_id: str):
        """ワークスペースの処理開始

        Args:
            oraganization_id (str): _description_
            workspace_id (str): _description_
        """
        cls._objdbca = DBConnectWs(workspace_id=workspace_id, organization_id=oraganization_id)
        g.ORGANIZATION_ID = oraganization_id
        g.WORKSPACE_ID = workspace_id
        g.applogger.set_env_message()

        g.applogger.debug(g.appmsg.get_log_message("BKY-90079", [cls._process_name]))
        cls._ws_mongo = MONGOConnectWs()
        cls._labeled_event_collection = MongoBufferedWriter(cls._ws_mongo.collection(mongoConst.LABELED_EVENT_COLLECTION))
        cls._t_oase_action_log = DBBufferedWriter(cls._objdbca, oaseConst.T_OASE_ACTION_LOG, 'ACTION_LOG_ID')

    @classmethod
    def _flush_buffer(cls, complite: multiprocessing.Queue):
        """バッファの内容を強制的にDBに書き込む

        Args:
            complite (multiprocessing.Queue): 完了応答メッセージ送信用
        """
        if cls._labeled_event_collection is not None:
            cls._labeled_event_collection.flush()

        if cls._t_oase_action_log is not None:
            cls._t_oase_action_log.flush()

        # バッファの書き込み完了
        g.applogger.debug(f"SubProcess({cls._process_name}) flush buffer completed")

        # 書き込み完了を応答
        complite.put({
            "message": "flush_buffer_completed"
        })

    @classmethod
    def _finish_workspace_processing(cls, complite: multiprocessing.Queue):
        """ワークスペースの処理終了

        Args:
            complite (multiprocessing.Queue): 完了応答メッセージ送信用
        """
        if cls._labeled_event_collection is not None:
            cls._labeled_event_collection.flush()
            cls._labeled_event_collection = None

        if cls._t_oase_action_log is not None:
            cls._t_oase_action_log.flush()
            cls._t_oase_action_log = None
                    
        # DBコネクションを切断
        if cls._objdbca is not None:
            cls._objdbca.db_disconnect()
            cls._objdbca = None

        # mongodbを切断
        if cls._ws_mongo is not None:
            cls._labeled_event_collection = None
            cls._ws_mongo.disconnect()
            cls._ws_mongo = None

        # ワークスペースの処理終了
        g.applogger.info(g.appmsg.get_log_message("BKY-90080", [cls._process_name]))

        # 書き込み完了を応答
        complite.put({
            "message": "workspace_processing_finished"
        })

        # 変数のクリア
        g.ORGANIZATION_ID = None
        g.WORKSPACE_ID = None
        g.applogger.set_env_message()

    @classmethod
    def exit_process(cls):
        """書き込みプロセスの終了
        """
        if cls._labeled_event_collection is not None:
            cls._labeled_event_collection.flush()
            cls._labeled_event_collection = None

        if cls._t_oase_action_log is not None:
            cls._t_oase_action_log.flush()
            cls._t_oase_action_log = None

        if cls._objdbca is not None:
            cls._objdbca.db_disconnect()
            cls._objdbca = None

        if cls._ws_mongo is not None:
            cls._labeled_event_collection = None
            cls._ws_mongo.disconnect()
            cls._ws_mongo = None


class MongoBufferedWriter():
    """mongodb書き込みclass
    """
    def __init__(self, mongo_collection):
        self._mongo_collection = mongo_collection
        self._bulk_buffer = []

    def insert(self, document: dict):
        """insert用のデータをセットする

        Args:
            document (dict): insertするドキュメント
        """
        if self._is_buffer_full():
            self.flush()
        self._bulk_buffer.append(InsertOne(document))

    def update(self, filter: dict, update: dict):
        """update用のデータをセットする

        Args:
            filter (dict): update対象
            update (dict): updateするドキュメント
        """
        if self._is_buffer_full():
            self.flush()
        self._bulk_buffer.append(UpdateOne(filter, update))

    def _is_buffer_full(self) -> bool:
        """バッファが一杯かどうかを判定する

        Returns:
            bool: _description_
        """
        return len(self._bulk_buffer) >= 100

    def flush(self):
        """バッファのデータをDBに書き込む
        """
        if len(self._bulk_buffer) == 0:
            # バッファにデータがない場合は何もしない
            return

        # バッファのデータをDBに書き込む
        g.applogger.debug(g.appmsg.get_log_message("BKY-90082", [len(self._bulk_buffer)]))
        self._mongo_collection.bulk_write(self._bulk_buffer)
        self._bulk_buffer = []


class DBBufferedWriter():
    """DB書き込みClass
        (同じレコードに対してINSERT⇒UPDATEの順で書き込まれているので余計なアクセス回数を減らすためバッファリング）
    """
    def __init__(self, objdbca: DBConnectWs, table_name: str, key_name: str):
        self._objdbca = objdbca
        self._table_name = table_name
        self._key_name = key_name
        self._row_buffer = None
        self._row_insert = None

    def insert(self, data: dict):
        """insert用のデータをセットする

        Args:
            data (dict): _description_
        """
        # バッファをflushする
        self.flush()

        # バッファにデータをセットする
        self._row_buffer = data
        self._row_insert = True

    def update(self, data: dict):
        """update用のデータをセットする

        Args:
            data (dict): _description_
        """
        if self._row_buffer is not None:
            # バッファにデータがある場合はキーを比較して同じならupdate、違うならflushしてからセットする
            if self._row_buffer[self._key_name] == data[self._key_name]:
                self._row_buffer.update(data)
            else:
                self.flush()
                self._row_buffer = data
                self._row_insert = False
        else:
            # バッファにデータがない場合はそのままセットする
            self._row_buffer = data
            self._row_insert = False

    def flush(self):
        """バッファのデータをDBに書き込む
        """
        if self._row_buffer is None:
            # バッファにデータがない場合は何もしない
            return

        # バッファのデータをDBに書き込む
        if self._row_insert:
            self._objdbca.table_insert(self._table_name, self._row_buffer, self._key_name)
        else:
            self._objdbca.table_update(self._table_name, self._row_buffer, self._key_name)
        
        self._row_buffer = None
        self._objdbca.db_commit()
