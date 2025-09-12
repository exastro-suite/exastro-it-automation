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
import multiprocessing
import time
from flask import Flask, g
from bson.objectid import ObjectId

from common_libs.conductor.classes.exec_util import *

from common_libs.common.queuing_logger import QueuingAppLogClient
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.common.message_class import MessageTemplate
from common_libs.common.mongoconnect.const import Const as mongoConst


class WriterProcessManager():
    """書き込みプロセスとのインターフェース
    """
    _queue = None
    _exitcode = None
    _process = None

    @classmethod
    def start_process(cls):
        """書き込みプロセスの起動
        """
        # 書き込みを要求するQueue
        cls._queue = multiprocessing.Queue()

        # 書き込みプロセス終了確認用 (0:起動中, 1:終了)
        #   process.is_alive() / process.join() だけではプロセスが終了しているかどうかの確認ができない場合があるため（数十回に1度程度の頻度で発生）
        #   共有メモリを使用してプロセスを終了していいかを判定する
        cls._exited = multiprocessing.Value('i', 0)

        # 書き込みプロセス起動
        cls._process = multiprocessing.Process(target=WriterProcess.main, args=(cls._queue, cls._exited), daemon=True)
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
        cls._process = None

    @classmethod
    def start_workspace_processing(cls, oraganization_id: str, workspace_id: str):
        """ワークスペースの処理開始を通知プロセスに伝える

        Args:
            oraganization_id (str): _description_
            workspace_id (str): _description_
        """
        cls._queue.put({
            "action": "start_workspace_processing",
            "oraganization_id": oraganization_id,
            "workspace_id": workspace_id
        })

    @classmethod
    def finish_workspace_processing(cls):
        """ワークスペースの処理終了を通知プロセスに伝える
        """
        cls._queue.put({
            "action": "finish_workspace_processing"
        })

    @classmethod
    def insert_labeled_event_collection(cls, dict: dict) -> ObjectId:
        """labeled_event_collectionにインサートを依頼する

        Args:
            dict (dict): insertするドキュメント

        Returns:
            ObjectId: 生成したオブジェクトID
        """
        # ObjectIdを作成する
        if "_id" not in dict:
            # 一意なObjectIdを生成
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

        cls._queue.put({
            "action": "update_labeled_event_collection",
            "filter": filter,
            "update": update
        })


class WriterProcess():
    """書き込みプロセス
    """
    _objdbca = None
    _wsMongo = None
    _labeled_event_collection = None

    @classmethod
    def main(cls, queue, exited):
        """書き込みプロセスのメインループ

        Args:
            queue (multiprocessing.Queue): 書き込みプロセスに書き込みを依頼するためのQueue
            exited (multiprocessing.Value): 書き込みプロセス終了確認用 (0:起動中, 1:終了)
        """
        # 初期化処理
        flask_app = Flask(__name__)

        with flask_app.app_context():
            try:
                cls._initialize()
                g.applogger.info("WriterProcess: start")

                # メインループ処理
                cls._main_loop(queue)

            finally:
                # 終了
                g.applogger.info("WriterProcess: exit")
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
    def _main_loop(cls, queue: multiprocessing.Queue):
        """メインループ処理

        Args:
            queue (multiprocessing.Queue): 書き込みプロセスに処理を依頼するためのQueue
        """
        while True:
            # Queueからの指示を待つ
            data = queue.get()
            try:
                if data["action"] == "insert_labeled_event_collection":
                    # wsMongo = MONGOConnectWs()
                    # self.labeled_event_collection = wsMongo.collection(mongoConst.LABELED_EVENT_COLLECTION)
                    # self.labeled_event_collection.insert_one(dict)
                    cls._labeled_event_collection.insert_one(data["dict"])

                elif data["action"] == "update_labeled_event_collection":
                    cls._labeled_event_collection.update_one(data["filter"], data["update"])

                elif data["action"] == "start_workspace_processing":
                    # ワークスペースの処理開始
                    cls._objdbca = DBConnectWs(workspace_id=data["workspace_id"], organization_id=data["oraganization_id"])
                    g.ORGANIZATION_ID = data["oraganization_id"]
                    g.WORKSPACE_ID = data["workspace_id"]
                    g.applogger.set_env_message()

                    g.applogger.info("WriterProcess: start workspace processing")
                    cls._wsMongo = MONGOConnectWs()
                    cls._labeled_event_collection = cls._wsMongo.collection(mongoConst.LABELED_EVENT_COLLECTION)

                elif data["action"] == "finish_workspace_processing":
                    # ワークスペースの処理終了
                    g.applogger.info("WriterProcess: finish workspace processing")
                    
                    # 通知の送信バッファをフラッシュ
                    # OASE.flush_send_buffer()
                    
                    # DBコネクションを切断
                    if cls._objdbca is not None:
                        cls._objdbca.db_disconnect()
                        cls._objdbca = None

                    # mongodbを切断
                    if cls._wsMongo is not None:
                        cls._labeled_event_collection = None
                        cls._wsMongo.disconnect()
                        cls._wsMongo = None

                    # 変数のクリア
                    g.ORGANIZATION_ID = None
                    g.WORKSPACE_ID = None
                    g.applogger.set_env_message()

                elif data["action"] == "exit":
                    # プロセスの終了指示

                    # 通知の送信バッファをフラッシュ
                    # OASE.flush_send_buffer()

                    # DBコネクションを切断
                    if cls._objdbca is not None:
                        cls._objdbca.db_disconnect()
                        cls._objdbca = None

                    # mongodbを切断
                    if cls._wsMongo is not None:
                        cls._labeled_event_collection = None
                        cls._wsMongo.disconnect()
                        cls._wsMongo = None
                    
                    # ループを終了
                    break

            except Exception as e:
                g.applogger.info(f"WriterProcess: error occurred. {e}")
                g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(traceback.format_exc())))
