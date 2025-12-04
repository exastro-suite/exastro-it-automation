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
import sys
import logging
import logging.handlers
import multiprocessing
import threading
from flask import g


LOGGER_NAME = 'queueAppLogger'

# env_messageの保持用
_thread_local = threading.local()


class QueuingAppLogServer():
    """Queuing Log Server
    """
    def __init__(self):
        """コンストラクタ
        """
        self.__log_queue = None
        self.__log_listener = None
        self.__queue_handler = None

    def get_logger(self) -> logging.Logger:
        """ロガーの取得（queueへloggingする）

        Returns:
            logging.Logger: queue出力logger
        """
        logging.setLoggerClass(QueuingAppLogger)
        return logging.getLogger(LOGGER_NAME)

    def start_server(self):
        """queueからログを出力するサーバー処理を起動する
        """
        self.__log_queue = multiprocessing.Queue()
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter('[%(asctime)s] [PID:%(process)06d] [%(levelname)s] %(env_message)s %(message)s (%(filename)s:%(lineno)d)')
        console_handler.setFormatter(console_formatter)

        self.__queue_handler = logging.handlers.QueueHandler(self.__log_queue)
        logger = self.get_logger()
        logger.addHandler(self.__queue_handler)
        logger.setLevel(logging.INFO)

        self.__queue_handler.addFilter(CustomLoggingFilter())
        self.__log_listener = logging.handlers.QueueListener(self.__log_queue, console_handler)
        self.__log_listener.start()

    def stop_server(self):
        """queueからログを出力するサーバー処理を終了する
        """
        try:
            if self.__log_listener is not None:
                self.__log_listener.stop()
        except Exception:
            # 停止に失敗しても無視
            pass


class QueuingAppLogClient():
    """Queuing Log Client
    """
    def get_logger(self):
        """ロガーの取得（queueへloggingする）

        Returns:
            logging.Logger: queue出力logger
        """
        logging.setLoggerClass(QueuingAppLogger)
        return logging.getLogger(LOGGER_NAME)


class QueuingAppLogger(logging.Logger):
    """Loggerの拡張class（既存(AppLog)のmethodを準備）
    """
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)

    def set_level(self, level):
        super().setLevel(level)

    def set_env_message(self):
        _thread_local.env_message = ""
        if "ORGANIZATION_ID" in g and g.ORGANIZATION_ID:
            _thread_local.env_message += f'[ORGANIZATION_ID:{g.ORGANIZATION_ID}]'

        if "WORKSPACE_ID" in g and g.WORKSPACE_ID:
            _thread_local.env_message += f'[WORKSPACE_ID:{g.WORKSPACE_ID}]'

        if "USER_ID" in g and g.USER_ID:
            _thread_local.env_message += f'[USER_ID:{g.USER_ID}]'


class CustomLoggingFilter(logging.Filter):
    """log formatにenv_messageを追加するためのloggingFilter
    """
    def filter(self, record: logging.LogRecord):
        record.env_message = getattr(_thread_local, 'env_message', '')
        return True
