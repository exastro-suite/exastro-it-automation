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

from common_libs.common.exception import AppException
from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate
from common_libs.ci.util import wrapper_job, app_exception, exception
from backyard_child_main import backyard_child_main as main_logic


def main():
    # コマンドラインから引数を受け取る["自身のファイル名", "organization_id", "workspace_id"]
    args = sys.argv
    # print(args)
    organization_id = args[1]
    workspace_id = args[2]

    # load environ variables
    load_dotenv(override=True)

    flask_app = Flask(__name__)

    with flask_app.app_context():
        try:
            g.ORGANIZATION_ID = organization_id
            g.WORKSPACE_ID = workspace_id

            g.USER_ID = os.environ.get("USER_ID")
            g.LANGUAGE = os.environ.get("LANGUAGE")
            # create app log instance and message class instance
            g.applogger = AppLog()
            g.appmsg = MessageTemplate(g.LANGUAGE)

            wrapper_job(main_logic, organization_id, workspace_id)
        except AppException as e:
            # catch - raise AppException("xxx-xxxxx", log_format)
            app_exception(e)
        except Exception as e:
            # catch - other all error
            exception(e)


if __name__ == '__main__':
    main()
