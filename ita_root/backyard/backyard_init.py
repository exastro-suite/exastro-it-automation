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

from common_libs.common.exception import AppException
from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate
from common_libs.ci.util import wrapper_job, app_exception, exception
from backyard_main import backyard_main as main_logic


def main():
    # load environ variables
    load_dotenv(override=True)

    flask_app = Flask(__name__)

    with flask_app.app_context():
        try:
            g.USER_ID = os.environ.get("USER_ID")
            g.LANGUAGE = os.environ.get("LANGUAGE")
            # create app log instance and message class instance
            g.applogger = AppLog()
            g.appmsg = MessageTemplate(g.LANGUAGE)

            wrapper_job(main_logic)
        except AppException as e:
            # catch - raise AppException("xxx-xxxxx", log_format)
            app_exception(e)
        except Exception as e:
            # catch - other all error
            exception(e)


if __name__ == '__main__':
    main()
