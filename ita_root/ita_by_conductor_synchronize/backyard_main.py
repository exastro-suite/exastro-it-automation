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
from flask import g  # noqa: F401
from common_libs.common.exception import AppException  # noqa: F401

from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from common_libs.conductor.classes.util import ConductorCommonLibs  # noqa: F401
from common_libs.conductor.classes.exec_util import *  # noqa: F403

import sys
import traceback
backyard_name = 'ita_by_conductor_synchronize'


def backyard_main(organization_id, workspace_id):
    g.applogger.debug("backyard_main ita_by_conductor_synchronize called")

    """
        Conductor作業実行処理（backyard）

        DB接続
        環境設定(言語,Lib読込,etc...)
        対象Conductor取得
            Conductor処理(※繰り返し開始)
                transaction開始
                Conductor処理1
                    共有パスを生成
                Node処理開始(※繰り返し)
                    Node処理
                Conductor処理2
                    ステータス反映
                transaction終了
            Conductor処理終了(※繰り返し終了)
    """
    retBool = True
    result = {}
    # g.applogger.set_level("INFO") # ["ERROR", "INFO", "DEBUG"]

    # 環境情報設定
    # 言語情報  ja / en
    g.LANGUAGE = 'en'

    tmp_msg = g.appmsg.get_log_message("BKY-41000", ['Start'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # DB接続
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    # conductor backyard lib読込
    objcbkl = ConductorExecuteBkyLibs(objdbca)  # noqa: F405
    if objcbkl.get_objmenus() is False:
        # DB切断
        objdbca.db_disconnect()
        tmp_msg = g.appmsg.get_log_message("BKY-41001", [])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False,

    # storage path 設定
    tmp_result = objcbkl.set_storage_path()
    if tmp_result[0] is not True:
        # DB切断
        objdbca.db_disconnect()
        tmp_msg = g.appmsg.get_log_message("BKY-41002", [])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False,
    base_conductor_storage_path = objcbkl.get_conductor_storage_path()

    # 作業対象のConductorの取得
    tmp_result = objcbkl.get_execute_conductor_list()
    if tmp_result[0] is not True:
        # DB切断
        objdbca.db_disconnect()
        tmp_msg = g.appmsg.get_log_message("BKY-41003", [])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return False,
    target_conductor_list = tmp_result[1]

    # 作業対象無しで終了
    if len(target_conductor_list) == 0:
        # DB切断
        objdbca.db_disconnect()
        tmp_msg = g.appmsg.get_log_message("BKY-41004", [])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        return True,

    # Conductor毎に繰り返し処理
    execute_conductor_cnt = 0
    for conductor_instance_id, tmp_info in target_conductor_list.items():
        tmp_msg = g.appmsg.get_log_message("BKY-41005", ['Start', conductor_instance_id])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        ci_status = tmp_info.get('status')

        # トランザクション開始
        objdbca.db_transaction_start()
        tmp_msg = g.appmsg.get_log_message("BKY-41006", [])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # テーブルロック
        locktable_list = ['T_COMN_CONDUCTOR_INSTANCE', 'T_COMN_CONDUCTOR_NODE_INSTANCE']
        tmp_result = objdbca.table_lock(locktable_list)
        tmp_msg = g.appmsg.get_log_message("BKY-41007", [",".join(locktable_list)])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # update_flg = ON
        ci_update_flg = 1
        ni_update_flg = 1

        # Conductor instance処理_1
        tmp_msg = g.appmsg.get_log_message("BKY-41008", ['Start'])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        try:
            # 共有パスを生成
            conductor_storage_path = "{}/{}".format(base_conductor_storage_path, conductor_instance_id)
            ci_status_id = tmp_info.get('status')
            tmp_result = objcbkl.create_data_storage_path(conductor_storage_path, ci_status_id)
            if tmp_result is False:
                tmp_msg = g.appmsg.get_log_message("BKY-41009", [])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                raise Exception()

            # 未実行,未実行(予約)時、ステータス更新＋開始時刻
            if ci_status in ['1', '2']:
                # Conductor instanceステータス更新
                tmp_result = objcbkl.conductor_status_update(conductor_instance_id)
                if tmp_result[0] is not True:
                    tmp_msg = g.appmsg.get_log_message("BKY-41010", [])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    raise Exception()

        except Exception:
            ci_update_flg = 0
            tmp_msg = g.appmsg.get_log_message("BKY-41008", ['Failed'])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            g.applogger.info(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))  # noqa: F405
            type_, value, traceback_ = sys.exc_info()
            msg = ''.join(traceback.format_exception(type_, value, traceback_))
            g.applogger.info(msg)

        tmp_msg = g.appmsg.get_log_message("BKY-41008", ['End'])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # Node instance処理
        tmp_msg = g.appmsg.get_log_message("BKY-41011", ['Start'])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        try:
            if ni_update_flg != 1 and ci_update_flg != 1:
                tmp_msg = g.appmsg.get_log_message("BKY-41012", [])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                raise Exception()

            # Node instance取得
            tmp_result = objcbkl.get_filter_node(conductor_instance_id)
            if tmp_result[0] is not True:
                tmp_msg = g.appmsg.get_log_message("BKY-41013", [])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                raise Exception()
            all_node_filter = tmp_result[1]

            # 全 Nodeのステータス取得
            tmp_result = objcbkl.get_execute_all_node_list(conductor_instance_id)
            if tmp_result[0] is not True:
                tmp_msg = g.appmsg.get_log_message("BKY-41014", [])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                raise Exception()
            target_all_node_list = tmp_result[1]

            # Start Nodeのnode_instance_id取得
            tmp_result = objcbkl.get_start_node(conductor_instance_id)
            if tmp_result[0] is not True:
                tmp_msg = g.appmsg.get_log_message("BKY-41015", [])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                raise Exception()
            start_node_instance_id = tmp_result[1]

            # Start Nodeが未実行か判定
            start_node_execute_flg = objcbkl.chk_conductor_start(start_node_instance_id, target_all_node_list)
            if start_node_execute_flg is True:
                # START Node開始処理
                tmp_result = objcbkl.execute_node_action(conductor_instance_id, start_node_instance_id, all_node_filter)
                if tmp_result[0] is not True:
                    tmp_msg = g.appmsg.get_log_message("BKY-41016", [start_node_instance_id])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    raise Exception()

            # Conductor実行中
            if start_node_execute_flg is False:
                # Node毎の処理
                for target_status, target_node in target_all_node_list['status'].items():
                    # 実行中,実行中(遅延),一時停止を処理
                    if target_status in ['3', '4', '11']:
                        for node_instance_id in target_node:
                            #  Node処理
                            tmp_result = objcbkl.execute_node_action(conductor_instance_id, node_instance_id, all_node_filter)
                            if tmp_result[0] is not True:
                                tmp_msg = g.appmsg.get_log_message("BKY-41017", [node_instance_id])
                                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                                raise Exception()
        except Exception as e:
            ni_update_flg = 0
            tmp_msg = g.appmsg.get_log_message("BKY-41011", ['Failed'])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            g.applogger.info(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))  # noqa: F405
            type_, value, traceback_ = sys.exc_info()
            msg = ''.join(traceback.format_exception(type_, value, traceback_))
            g.applogger.info(msg)

        tmp_msg = 'node instance process end'
        tmp_msg = g.appmsg.get_log_message("BKY-41011", ['End'])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # Conductor instance処理_2
        tmp_msg = g.appmsg.get_log_message("BKY-41018", ['Start'])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        try:
            if ni_update_flg != 1 or ci_update_flg != 1:
                tmp_msg = g.appmsg.get_log_message("BKY-41019", [conductor_instance_id])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                raise Exception()
            # Conductor instanceステータス更新
            tmp_result = objcbkl.conductor_status_update(conductor_instance_id)
            if tmp_result[0] is not True:
                tmp_msg = g.appmsg.get_log_message("BKY-41020", [conductor_instance_id])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                raise Exception()

        except Exception as e:
            ci_update_flg = 0
            tmp_msg = g.appmsg.get_log_message("BKY-41018", ['Failed'])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            g.applogger.info(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))  # noqa: F405
            type_, value, traceback_ = sys.exc_info()
            msg = ''.join(traceback.format_exception(type_, value, traceback_))
            g.applogger.info(msg)

        tmp_msg = g.appmsg.get_log_message("BKY-41018", ['End'])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        try:
            if (ni_update_flg == 1 and ci_update_flg == 1) is True:
                # トランザクション終了
                objdbca.db_transaction_end(True)
                tmp_msg = g.appmsg.get_log_message("BKY-41021", ['True'])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            else:
                retBool = False
                # トランザクション終了
                objdbca.db_transaction_end(False)
                tmp_msg = g.appmsg.get_log_message("BKY-41021", ['False'])

                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        except Exception as e:
            retBool = False
            # トランザクション終了
            objdbca.db_transaction_end(False)
            tmp_msg = g.appmsg.get_log_message("BKY-41021", ['False'])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            g.applogger.info(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))  # noqa: F405
            type_, value, traceback_ = sys.exc_info()
            msg = ''.join(traceback.format_exception(type_, value, traceback_))
            g.applogger.info(msg)
        finally:
            execute_conductor_cnt = execute_conductor_cnt + 1

        tmp_msg = g.appmsg.get_log_message("BKY-41005", ['End', conductor_instance_id])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # DB切断
    objdbca.db_disconnect()

    tmp_msg = g.appmsg.get_log_message("BKY-41022", [execute_conductor_cnt])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    tmp_msg = g.appmsg.get_log_message("BKY-41000", ['End'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    return retBool, result,
