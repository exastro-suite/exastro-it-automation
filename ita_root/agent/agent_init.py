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
import re
import traceback

from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate
from common_libs.common.util import get_iso_datetime, arrange_stacktrace_format
from agent_main import agent_main as main_logic


def main():
    # load environ variables
    load_dotenv(override=True)

    flask_app = Flask(__name__)

    with flask_app.app_context():
        try:
            organization_id = os.environ.get("EXASTRO_ORGANIZATION_ID")
            workspace_id = os.environ.get("EXASTRO_WORKSPACE_ID")
            g.ORGANIZATION_ID = organization_id
            g.WORKSPACE_ID = workspace_id

            g.AGENT_NAME = os.environ.get("AGENT_NAME", "agent-oase-01")
            g.USER_ID = os.environ.get("USER_ID")
            g.LANGUAGE = os.environ.get("LANGUAGE")

            # create app log instance and message class instance
            g.applogger = AppLog()
            g.applogger.set_level(os.environ.get("LOG_LEVEL", "INFO"))
            g.appmsg = MessageTemplate(g.LANGUAGE)

            # 実行インターバル
            interval = int(os.environ.get("EXECUTE_INTERVAL", 5))  # デフォルト 5s
            interval = 3 if interval <= 3 else interval  # 下限値 3s

            # コマンドラインから引数を受け取る["自身のファイル名", "ループ回数"]
            args = sys.argv
            # （一連の処理の）ループ回数
            loop_count = int(os.environ.get("ITERATION", 10))  # デフォルト 10回
            loop_count = 10 if loop_count <= 10 else loop_count  # 下限値 10回
            loop_count = 120 if loop_count > 120 else loop_count  # 上限値 120回
            if interval * loop_count >= 86400:
                # EXECUTE_INTERVAL × ITERATIONが1日をこえるような場合は
                # インターバルを優先して、調整をかける
                loop_count = 86400 // (interval + 10)
                if loop_count < 1:
                    interval = 86400 - 10
                    loop_count = 1
            # print(f'{interval=}')
            # print(f'{loop_count=}')
            loop_count = loop_count if len(args) == 1 else int(args[1])  # コマンドライン指定すると上書き

            # 妥当な設定（organization_id, workspace_id）でなければ、メイン処理に回さない
            is_setting_check = setting_check(organization_id, workspace_id)
            if is_setting_check is False:
                g.applogger.info("setting is invalid(organization_id or workspace_id). so, main_logic is skipped")
                time.sleep(interval)
            else:
                main_logic(organization_id, workspace_id, loop_count, interval)
        except Exception as e:
            # catch - other all error
            t = traceback.format_exc()
            g.applogger.error("[timestamp={}] {}".format(get_iso_datetime(), arrange_stacktrace_format(t)))

            time.sleep(interval)

# 妥当な設定（organization_id, workspace_id）でなければ、メイン処理に回さない
def setting_check(organization_id, workspace_id):
    if organization_id is None or workspace_id is None:
        return False

    if not organization_id or not workspace_id or organization_id.isspace() or workspace_id.isspace():
        return False

    # 不正な文字列チェック
    try:
        pattern = re.compile(r'^[a-zA-Z0-9-_]{1,36}$')
        match = re.match(pattern, organization_id)
        if match is None:
            return False
        match = re.match(pattern, workspace_id)
        if match is None:
            return False
    except Exception:
        return False

    return True

if __name__ == '__main__':
    main()
