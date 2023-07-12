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


from flask import g
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.common.util import get_timestamp, get_all_execution_limit, get_org_execution_limit
from common_libs.ci.util import log_err

# from libs import common_functions as cm


def backyard_main(organization_id, workspace_id):
    """
    [ita_by_ansible_execute]
    main logicのラッパー
    called 実行君
    """
    g.applogger.debug(g.appmsg.get_log_message("BKY-00001"))

    retBool = main_logic(organization_id, workspace_id)
    if retBool is True:
        # 正常終了
        g.applogger.debug(g.appmsg.get_log_message("BKY-00002"))
    else:
        g.applogger.debug(g.appmsg.get_log_message("BKY-00003"))


def main_logic(organization_id, workspace_id):
    """
    main logic
    """
    g.applogger.debug("organization_id=" + organization_id)
    g.applogger.debug("workspace_id=" + workspace_id)

    wsMong = MONGOConnectWs()
    g.applogger.debug("mongodb-ws can connet")

    test_collection = wsMong.collection("test_collection")
    # test_collection.insert_many([
    #     {'名前': '太郎', '住所': '東京'},
    #     {'名前': '次郎', '住所': '千葉'}
    # ])
    data_list = test_collection.find()
    for data in data_list:
        g.applogger.debug(data)

    return True
