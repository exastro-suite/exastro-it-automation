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
import json

from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate
from common_libs.ci.util import exception
from common_libs.migration import *
from libs.functions import util

ITA_INIT_USER_ID = 1


def __wrapper():
    """ita migration wrapper

    Returns:
        int: result(0=succeed / other=failed)
    """

    # load environ variables
    load_dotenv(override=True)

    flask_app = Flask(__name__)

    with flask_app.app_context():
        g.USER_ID = os.environ.get("USER_ID", ITA_INIT_USER_ID)
        g.LANGUAGE = os.environ.get("LANGUAGE", "en")
        g.STORAGEPATH = os.environ.get('STORAGEPATH')
        g.APPPATH = os.path.dirname(__file__)
        # create app log instance and message class instance
        g.applogger = AppLog()
        # g.applogger.set_level("DEBUG")  # 試験中は有効にする
        g.appmsg = MessageTemplate(g.LANGUAGE)

        try:
            g.applogger.info("Begin ITA migration.")

            versions = util.get_migration_target_versions()
            if len(versions) == 0:
                g.applogger.info("No need to work.")
                return 0

            g.applogger.info("stop_all_backyards")
            util.stop_all_backyards()

            # バージョンアップ
            for version in versions:
                __migration_main(version)

            # set latest version
            util.set_version(versions[-1])

            return 0

        except Exception as e:
            # exception(e, True)
            exception(e, True)
            return 1
        finally:
            g.applogger.info("restart_all_backyards")
            util.restart_all_backyards()
            g.applogger.info("End ITA migration.")


def __migration_main(version):
    """
    ita migration main

    Returns:
        int: result(0=succeed / other=failed)
    """
    g.applogger.info("ita_migration called.")

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # 実行準備
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

    # 対象バージョンのディレクトリ確認
    version_dir = version.replace('.', '_')
    version_dir_path = os.path.join(g.APPPATH, "versions", version_dir)
    if not os.path.isdir(version_dir_path):
        raise Exception(f"No such directory. path:{version_dir_path}")

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # メイン処理開始
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    g.applogger.info(f"Begin apply version:{version}")

    # BASE level の処理
    resource_dir_path = os.path.join(version_dir_path, "BASE_level")
    if os.path.isdir(resource_dir_path):
        common_db = DBConnectCommon()  # noqa: F405
        work_dir_path = g.STORAGEPATH
        worker = Migration(resource_dir_path, work_dir_path, common_db)

        g.applogger.info("[Trace] Begin BASE migrate.")
        worker.migrate()
        g.applogger.info("[Trace] End BASE migrate.")

    org_list = util.get_organization_ids()
    for organization_data in org_list:
        organization_id = organization_data[0]
        no_install_driver = json.loads(organization_data[1]) if organization_data[1] is not None else {}
        g.ORGANIZATION_ID = organization_id
        g.applogger.set_env_message()

        # ORG level の処理
        resource_dir_path = os.path.join(version_dir_path, "ORG_level")
        if os.path.isdir(resource_dir_path):
            org_db = DBConnectOrg(organization_id)  # noqa: F405
            work_dir_path = os.path.join(g.STORAGEPATH, organization_id)
            org_worker = Migration(resource_dir_path, work_dir_path, org_db, no_install_driver)

            g.applogger.info("[Trace] Begin ORG migrate.")
            org_worker.migrate()
            g.applogger.info("[Trace] End ORG migrate.")

        ws_id_list = util.get_workspace_ids(organization_id)
        for workspace_id in ws_id_list:
            g.WORKSPACE_ID = workspace_id
            g.applogger.set_env_message()
            # WS level の処理
            resource_dir_path = os.path.join(version_dir_path, "WS_level")
            if os.path.isdir(resource_dir_path):
                ws_db = DBConnectWs(workspace_id, organization_id)  # noqa: F405
                work_dir_path = os.path.join(g.STORAGEPATH, organization_id, workspace_id)
                ws_worker = Migration(resource_dir_path, work_dir_path, ws_db, no_install_driver)

                g.applogger.info("[Trace] Begin WS migrate.")
                ws_worker.migrate()
                g.applogger.info("[Trace] End WS migrate.")

            del g.WORKSPACE_ID
            g.applogger.set_env_message()
        del g.ORGANIZATION_ID
        g.applogger.set_env_message()

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # 終了処理
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

    g.applogger.info(f"End apply version:{version}")


if __name__ == '__main__':
    ret = __wrapper()
    exit(ret)
