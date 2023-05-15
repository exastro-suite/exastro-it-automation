# Copyright 2023 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License")
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

from common_libs.hostgroup.classes.hostgroup_table_class import *  # noqa: F403
from common_libs.hostgroup.functions.split_function import *  # noqa: F403


backyard_name = 'ita_by_hostgroup_split'


def backyard_main(organization_id, workspace_id):
    g.applogger.debug("backyard_main ita_by_hostgroup_split called")

    """
        ホストグループ分割機能（backyard）
            DB接続
            ツリー作成
            処理対象メニュー取得
            ホストグループ分解
        ARGS:
            organization_id: Organization ID
            workspace_id: Workspace ID
        RETURN:
            (retBool, result,)
    """
    retBool = True
    result = {}
    # g.applogger.set_level("INFO") # ["ERROR", "INFO", "DEBUG"]

    # 環境情報設定
    # 言語情報  ja / en
    g.LANGUAGE = 'en'

    # 処理開始
    tmp_msg = g.appmsg.get_log_message("BKY-70000", ['Start'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # DB接続
    tmp_msg = 'db connect'
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        hierarchy = 0
        # ツリー作成
        retBool, tree_array, hierarchy = make_tree(objdbca, hierarchy)  # noqa: F405
        if retBool is False:
            tmp_msg = g.appmsg.get_log_message("BKY-70001", [])
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()

        # 対象ホスト-オペレーション-ホストグループ
        tmp_hosts = [[_t['HOST_ID'], _t['OPERATION'], _t['PARENT_IDS']] for _t in tree_array if _t['OPERATION'] is not None if _t['OPERATION'] != []]
        all_ids = get_all_list(objdbca)  # noqa: F405
        tmp_target_host = [[x[0], [y for y in x[1]], [z for z in x[2]]] for x in tmp_hosts]
        tmp_msg = g.appmsg.get_log_message("BKY-70002", ['target_host - operation, hostgroup:', tmp_target_host])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_target_host = [[all_ids.get(x[0]), [all_ids.get(y) for y in x[1]], [all_ids.get(z) for z in x[2]]] for x in tmp_hosts]
        tmp_msg = g.appmsg.get_log_message("BKY-70002", ['target_host - operation, hostgroup id->name:', tmp_target_host])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # 処理対象メニュー取得
        retBool, result = get_target_menu(objdbca)  # noqa: F405
        if retBool:
            target_menus = result
            for target in target_menus:
                # 対象メニュー処理開始: 入力用→代入値自動登録用
                tmp_msg = g.appmsg.get_log_message("BKY-70003", ['Start', target['INPUT_MENU_NAME_REST'], target['OUTPUT_MENU_NAME_REST'], target['ROW_ID']])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                # 分割済みフラグ
                divided_flg = target['DIVIDED_FLG']
                # TABLE/VIEW:(分割対象:input)
                input_table_name = target['INPUT_TABLE_NAME']
                input_view_name = target['INPUT_VIEW_NAME']
                # TABLE/VIEW:(登録対象:output)
                output_table_name = target['OUTPUT_TABLE_NAME']
                output_view_name = target['OUTPUT_VIEW_NAME']

                # 分割済みの場合、次へ
                if "1" == divided_flg:
                    tmp_msg = g.appmsg.get_log_message(
                        "BKY-70004",
                        [target['INPUT_MENU_NAME_REST'], target['OUTPUT_MENU_NAME_REST'], target['ROW_ID']]
                    )
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    continue

                # 分割対象のテーブル構造を取得
                input_table = BaseTable(objdbca, input_table_name)  # noqa: F405
                input_view = BaseTable(objdbca, input_view_name)  # noqa: F405

                # 登録対象のテーブル構造を取得
                output_table = BaseTable(objdbca, output_table_name, 0)  # noqa: F405
                output_view = BaseTable(objdbca, output_view_name)  # noqa: F405

                # 入力用→代入値自動登録用テーブル
                tmp_msg = g.appmsg.get_log_message("BKY-70005", [input_table_name, output_table_name])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                # ファイルアップロード対象取得
                result, file_columns_info = get_file_columns_info(objdbca, input_table, output_table)  # noqa: F405
                if result is False:
                    tmp_msg = g.appmsg.get_log_message("BKY-70006", [])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    continue

                # config
                hgsp_config = {
                    "objdbca": objdbca,
                    "input_table": input_table,
                    "input_view": input_view,
                    "output_table": output_table,
                    "output_view": output_view,
                    "file_columns_info": file_columns_info,
                    "target_row_id": target['ROW_ID'],
                    "target_timestamp": target['TIMESTAMP'],
                    "input_menu_id": target['INPUT_MENU_ID'],
                    "output_menu_id": target['OUTPUT_MENU_ID'],
                    "vertical_flg": target['VERTICAL'],
                    "alllist": all_ids,
                }

                # data
                hgsp_data = {
                    "update_cnt": 0,
                    "insert_cnt": 0,
                    "disuse_cnt": 0,
                    "tree_array": tree_array,
                    "hierarchy": hierarchy,
                }

                # ホストグループ分解
                result, hgsp_data = split_host_grp(hgsp_config, hgsp_data)  # noqa: F405
                if result is False:
                    # ホストグループ分解エラー、次へ
                    tmp_msg = g.appmsg.get_log_message(
                        "BKY-70007",
                        [target['INPUT_MENU_NAME_REST'], target['OUTPUT_MENU_NAME_REST'], target['ROW_ID']]
                    )
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    continue

                # 件数ログ
                tmp_msg = g.appmsg.get_log_message(
                    "BKY-70008",
                    [hgsp_data['insert_cnt'], hgsp_data['update_cnt'], hgsp_data['disuse_cnt']]
                )
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                # 対象メニュー処理終了: 入力用→代入値自動登録用
                tmp_msg = g.appmsg.get_log_message("BKY-70003", ['End', target['INPUT_MENU_NAME_REST'], target['OUTPUT_MENU_NAME_REST'], target['ROW_ID']])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    except Exception as e:
        # 処理終了 Exception
        tmp_msg = e
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = g.appmsg.get_log_message("BKY-70000", ['End: Exception'])
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # 処理終了
    tmp_msg = g.appmsg.get_log_message("BKY-70000", ['End'])
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    return retBool, result,
