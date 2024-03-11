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
import logging

# from common_libs.common.exception import AppException
from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate
from common_libs.common.util import get_maintenance_mode_setting
from common_libs.ci.util import wrapper_job, wrapper_job_all_org
from backyard_main import backyard_main as main_logic


def main():
    print("")
    # load environ variables
    load_dotenv(override=True)

    flask_app = Flask(__name__)

    with flask_app.app_context():
        g.LANGUAGE = os.environ.get("LANGUAGE")
        g.appmsg = MessageTemplate(g.LANGUAGE)

        # メンテナンスモードの確認
        try:
            maintenance_mode = get_maintenance_mode_setting()
            # data_update_stopの値が"1"の場合、メンテナンス中のためreturnする。
            if str(maintenance_mode['data_update_stop']) == "1":
                logging.debug(g.appmsg.get_log_message("BKY-00005", []))
                return
        except Exception:
            # エラーログ出力
            logging.error(g.appmsg.get_log_message("BKY-00007", []))
            return

        g.USER_ID = os.environ.get("USER_ID")
        g.SERVICE_NAME = os.environ.get("SERVICE_NAME")
        # create app log instance and message class instance
        g.applogger = AppLog()

        args = sys.argv
        loop_count = 500 if len(args) == 1 else args[1]
        if g.SERVICE_NAME == "ita-by-ansible-execute":
            wrapper_job_all_org(main_logic, loop_count)
        else:
            wrapper_job(main_logic, None, None, loop_count)


if __name__ == '__main__':
    main()
