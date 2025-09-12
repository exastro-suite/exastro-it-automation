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

from common_libs.conductor.classes.exec_util import *

from common_libs.common.queuing_logger import QueuingAppLogClient
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common.message_class import MessageTemplate
from common_libs.notification.sub_classes.oase import OASE


class NotificationProcessManager():
    """通知プロセスとのインターフェース
    """
    _queue = None
    _exitcode = None
    _process = None

    @classmethod
    def start_process(cls):
        """通知プロセスの起動
        """
        # 通知を要求するQueue
        cls._queue = multiprocessing.Queue()

        # 通知プロセス終了確認用 (0:起動中, 1:終了)
        #   process.is_alive() / process.join() だけではプロセスが終了しているかどうかの確認ができない場合があるため（数十回に1度程度の頻度で発生）
        #   共有メモリを使用してプロセスを終了していいかを判定する
        cls._exited = multiprocessing.Value('i', 0)

        # 通知プロセス起動
        cls._process = multiprocessing.Process(target=NotificationProcess.main, args=(cls._queue, cls._exited), daemon=True)
        cls._process.start()

    @classmethod
    def stop_process(cls):
        """通知プロセスの停止
        """
        # 通知プロセスに終了指示を送る
        cls._queue.put({"action": "exit"})

        # 通知プロセスの終了を待つ
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
    def send_notification(cls, event_list: list, decision_information: dict):
        """通知プロセスに通知を依頼する

        Args:
            event_list (list): _description_
            decision_information (dict): _description_
        """
        cls._queue.put({
            "action": "notification",
            "event_list": event_list,
            "decision_information": decision_information
        })


class NotificationProcess():
    """通知プロセス
    """
    _objdbca = None

    @classmethod
    def main(cls, queue: multiprocessing.Queue, exited):
        """通知プロセスのメイン処理

        Args:
            queue (multiprocessing.Queue): 通知プロセスに通知を依頼するためのQueue
            exited (_type_): 終了済みフラグ(0:起動中, 1:終了)
        """
        # 初期化処理
        flask_app = Flask(__name__)

        with flask_app.app_context():
            try:
                cls._initialize()
                g.applogger.info("NotificationProcess: start")

                # メインループ処理
                cls._main_loop(queue)

            finally:
                # 終了
                g.applogger.info("NotificationProcess: exit")
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
            queue (multiprocessing.Queue): 通知プロセスに通知を依頼するためのQueue
        """
        while True:
            # Queueからの指示を待つ
            data = queue.get()
            try:
                if data["action"] == "notification":
                    # 通知処理
                    OASE.buffered_send(cls._objdbca, data["event_list"], data["decision_information"])

                elif data["action"] == "start_workspace_processing":
                    # ワークスペースの処理開始
                    cls._objdbca = DBConnectWs(workspace_id=data["workspace_id"], organization_id=data["oraganization_id"])
                    g.ORGANIZATION_ID = data["oraganization_id"]
                    g.WORKSPACE_ID = data["workspace_id"]
                    g.applogger.set_env_message()
                    g.applogger.info("NotificationProcess: start workspace processing")

                elif data["action"] == "finish_workspace_processing":
                    # ワークスペースの処理終了
                    
                    # 通知の送信バッファをフラッシュ
                    OASE.flush_send_buffer()
                    
                    # DBコネクションを切断
                    if cls._objdbca is not None:
                        cls._objdbca.db_disconnect()
                        cls._objdbca = None

                    g.applogger.info("NotificationProcess: finish workspace processing")

                    # 変数のクリア
                    g.ORGANIZATION_ID = None
                    g.WORKSPACE_ID = None
                    g.applogger.set_env_message()

                elif data["action"] == "exit":
                    # プロセスの終了指示

                    # 通知の送信バッファをフラッシュ
                    OASE.flush_send_buffer()

                    # DBコネクションを切断
                    if cls._objdbca is not None:
                        cls._objdbca.db_disconnect()
                        cls._objdbca = None

                    # ループを終了
                    break

            except Exception as e:
                g.applogger.info(f"NotificationProcess: error occurred. {e}")
                g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(traceback.format_exc())))
