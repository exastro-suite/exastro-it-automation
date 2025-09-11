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
from flask import Flask, g
from dotenv import load_dotenv  # python-dotenv
import os
import sys
import traceback
import importlib

# from common_libs.common.exception import AppException
from common_libs.common.logger import AppLog
from common_libs.common.queuing_logger import QueuingAppLogServer
from common_libs.common.message_class import MessageTemplate
from common_libs.common.util import get_maintenance_mode_setting, get_iso_datetime, arrange_stacktrace_format
from common_libs.ci.util import wrapper_job, wrapper_job_all_org
from backyard_main import backyard_main as main_logic


def main():
    # load environ variables
    load_dotenv(override=True)

    flask_app = Flask(__name__)

    with flask_app.app_context():
        g.LANGUAGE = os.environ.get("LANGUAGE")
        g.appmsg = MessageTemplate(g.LANGUAGE)
        # create app log instance and message class instance
        if not use_log_queue():
            g.applogger = AppLog()
        else:
            # QueueAppLogでログをメインプロセスに集約して出力するようにloggerを設定
            log_server = QueuingAppLogServer()
            log_server.start_server()
            g.applogger = log_server.get_logger()

        try:
            maintenance_mode = get_maintenance_mode_setting()
            # data_update_stopの値が"1"の場合、メンテナンス中のためreturnする。
            if str(maintenance_mode['data_update_stop']) == "1":
                g.applogger.debug(g.appmsg.get_log_message("BKY-00005", []))
                return
        except Exception:
            # エラーログ出力
            t = traceback.format_exc()
            g.applogger.error("[timestamp={}] {}".format(get_iso_datetime(), arrange_stacktrace_format(t)))

            g.applogger.error(g.appmsg.get_log_message("BKY-00007", []))
            return

        g.USER_ID = os.environ.get("USER_ID")
        g.SERVICE_NAME = os.environ.get("SERVICE_NAME")

        if enable_on_start_process():
            # 処理開始時のコンテ独自処理(backyard_main.on_start_process)がある場合はそれを実行します
            func = getattr(importlib.import_module('backyard_main'), 'on_start_process')
            func()

        args = sys.argv
        loop_count = 500 if len(args) == 1 else args[1]
        if g.SERVICE_NAME == "ita-by-ansible-execute":
            wrapper_job_all_org(main_logic, loop_count)
        else:
            wrapper_job(main_logic, None, None, loop_count)

        if enable_on_exit_process():
            # 処理終了時のコンテ独自処理(backyard_main.on_exit_process)がある場合はそれを実行します
            func = getattr(importlib.import_module('backyard_main'), 'on_exit_process')
            func()

        if use_log_queue():
            # log queue serverを終了します
            log_server.stop_server()


def use_log_queue() -> bool:
    """QueuingAppLogServerを使うかを返します

    Returns:
        bool: True=QueuingAppLogServerを使う / False=既存のAppLogを使用する
    """
    return os.environ.get("SERVICE_NAME") in ["ita-by-oase-conclusion"]


def enable_on_start_process() -> bool:
    """開始前に独自の初期処理を行うかを返します

    Returns:
        bool: True=独自の初期処理を行う / False=独自の初期処理を行わない
    """
    return os.environ.get("SERVICE_NAME") in ["ita-by-oase-conclusion"]


def enable_on_exit_process() -> bool:
    """終了前に独自の終了処理を行うかを返します

    Returns:
        bool: True=独自の終了処理を行う / False=独自の終了処理を行わない
    """
    return os.environ.get("SERVICE_NAME") in ["ita-by-oase-conclusion"]


if __name__ == '__main__':
    main()
