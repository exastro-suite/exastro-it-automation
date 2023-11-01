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
import time

from common_libs.common.exception import AppException
from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate
from common_libs.ci.util import app_exception, exception
from agent_main import agent_main as main_logic


def main():
    # load environ variables
    load_dotenv(override=True)

    flask_app = Flask(__name__)

    with flask_app.app_context():
        try:
            organization_id = os.environ.get("ORGANIZATION_ID")
            workspace_id = os.environ.get("WORKSPACE_ID")
            g.ORGANIZATION_ID = organization_id
            g.WORKSPACE_ID = workspace_id

            g.AGENT_NAME = os.environ.get("AGENT_NAME", "agent-oase-01")
            g.USER_ID = os.environ.get("USER_ID")
            g.LANGUAGE = os.environ.get("LANGUAGE")

            # create app log instance and message class instance
            g.applogger = AppLog()
            g.applogger.set_level(os.environ.get("LOG_LEVEL"), "INFO")
            g.appmsg = MessageTemplate(g.LANGUAGE)

            # storageにdbの保存場所を作成
            db_dir = "/storage/{}/{}/sqlite".format(organization_id, workspace_id)
            os.makedirs(db_dir, exist_ok=True)

            # コマンドラインから引数を受け取る["自身のファイル名", "ループ回数"]
            args = sys.argv
            loop_count = int(os.environ.get("ITERATION", 500)) if len(args) == 1 else int(args[1])
            interval = int(os.environ.get("EXECUTE_INTERVAL", 30))

            main_logic(organization_id, workspace_id, loop_count, interval)
        except AppException as e:
            app_exception(e)
            time.sleep(interval)
        except Exception as e:
            # catch - other all error
            exception(e)
            time.sleep(interval)


if __name__ == '__main__':
    main()
