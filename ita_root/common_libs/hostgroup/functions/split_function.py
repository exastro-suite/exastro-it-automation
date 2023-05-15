#   Copyright 2023 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License")
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http:#www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from flask import g
from common_libs.common.dbconnect import DBConnectWs  # noqa: F401

from common_libs.common import *  # noqa: F403
from common_libs.loadtable import *  # noqa: F403
from common_libs.column import *  # noqa: F403

from common_libs.hostgroup.classes.hostgroup_table_class import *  # noqa: F403
from common_libs.hostgroup.classes.hostgroup_const import *  # noqa: F403

import json
import textwrap
import sys
import traceback
import inspect
import os
import copy

from pprint import pprint  # noqa: F401
import shutil
from datetime import date
from datetime import datetime

hostgroup_const = hostGroupConst()  # noqa: F405


# 処理対象メニュー取得
def get_target_menu(objdbca):
    """
    get_target_menu: 処理対象メニュー取得
    Args:
        objdbca : DBConnectWs(object) # DB接続クラス
    Returns:
        (retBool, target_array)
            retBool: bool
            target_array: list
    """
    try:
        tmp_msg = 'get_target_menu start'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # ホストグループ分割対象テーブルを検索:SQL実行
        split_target_table = SplitTargetTable(objdbca)  # noqa: F405
        sql = split_target_table.create_sselect("WHERE DISUSE_FLAG = '0'")
        result = split_target_table.select_table(sql)
        if result is False:
            tmp_msg = 'select table error SplitTargetTable'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()
        split_target_array = result

        # メニュー管理テーブルを検索:SQL実行
        menu_list_table = MenuListTable(objdbca)  # noqa: F405
        sql = menu_list_table.create_sselect("WHERE DISUSE_FLAG = '0'")
        result = menu_list_table.select_table(sql)
        if result is False:
            tmp_msg = 'select table error MenuListTable'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()
        menu_list_array = result
        menu_id_array = [(v.get('MENU_ID')) for v in menu_list_array]

        # メニュー・テーブル紐付テーブルを検索:SQL実行
        menu_table_link_table = MenuTableLinkTable(objdbca)  # noqa: F405
        sql = menu_table_link_table.create_sselect("WHERE DISUSE_FLAG = '0'")
        result = menu_table_link_table.select_table(sql)
        if result is False:
            tmp_msg = 'select table error MenuTableLinkTable'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()
        menu_tablelink_array = result
        menu_table_link_id_array = [(v.get('MENU_ID')) for v in menu_tablelink_array]

        target_array = []
        # ホストグループ分割対象の件数分ループ
        for split_target in split_target_array:
            # メニューIDが有効ではない場合はスキップ
            if split_target['INPUT_MENU_ID'] in menu_id_array is False or split_target['OUTPUT_MENU_ID'] in menu_id_array is False:
                continue

            # メニュー・テーブル紐付テーブルが特定できない場合はスキップ
            input_menu_table_link = split_target['INPUT_MENU_ID'] in menu_table_link_id_array
            output_menu_table_link = split_target['OUTPUT_MENU_ID'] in menu_table_link_id_array
            if input_menu_table_link is False or output_menu_table_link is False:
                continue

            input_table_name = [tmt.get("TABLE_NAME") for tmt in menu_tablelink_array if tmt.get("MENU_ID") == split_target['INPUT_MENU_ID']]
            output_table_name = [tmt.get("TABLE_NAME") for tmt in menu_tablelink_array if tmt.get("MENU_ID") == split_target['OUTPUT_MENU_ID']]
            input_view_name = [tmt.get("VIEW_NAME") for tmt in menu_tablelink_array if tmt.get("MENU_ID") == split_target['INPUT_MENU_ID']]
            output_view_name = [tmt.get("VIEW_NAME") for tmt in menu_tablelink_array if tmt.get("MENU_ID") == split_target['OUTPUT_MENU_ID']]
            input_vertical = [tmt.get("VERTICAL") for tmt in menu_tablelink_array if tmt.get("MENU_ID") == split_target['INPUT_MENU_ID']]
            output_vertical = [tmt.get("VERTICAL") for tmt in menu_tablelink_array if tmt.get("MENU_ID") == split_target['OUTPUT_MENU_ID']]

            input_menu_name_rest = [tmt.get("MENU_NAME_REST") for tmt in menu_list_array if tmt.get("MENU_ID") == split_target['INPUT_MENU_ID']]
            output_menu_name_rest = [tmt.get("MENU_NAME_REST") for tmt in menu_list_array if tmt.get("MENU_ID") == split_target['OUTPUT_MENU_ID']]

            # 縦メニュー
            if input_vertical[0] == '1' and output_vertical[0] == '1':
                vertical = True
            elif input_vertical[0] == '0' and output_vertical[0] == '0':
                vertical = False
            else:
                # ホストグループ分割対象不備
                tmp_msg = 'split target is Faild: split menu({}) -> input menu({})'.format(input_menu_name_rest, output_menu_name_rest)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                raise Exception()

            tmp_target_array = {
                'INPUT_TABLE_NAME': input_table_name[0],
                'OUTPUT_TABLE_NAME': output_table_name[0],
                'INPUT_VIEW_NAME': input_view_name[0],
                'OUTPUT_VIEW_NAME': output_view_name[0],
                'ROW_ID': split_target['ROW_ID'],
                'DIVIDED_FLG': split_target['DIVIDED_FLG'],
                'TIMESTAMP': split_target['LAST_UPDATE_TIMESTAMP'],
                'INPUT_MENU_ID': split_target['INPUT_MENU_ID'],
                'OUTPUT_MENU_ID': split_target['OUTPUT_MENU_ID'],
                'INPUT_MENU_NAME_REST': input_menu_name_rest[0],
                'OUTPUT_MENU_NAME_REST': output_menu_name_rest[0],
                'VERTICAL': vertical,
            }
            target_array.append(tmp_target_array)

        tmp_msg = 'get_target_menu end'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        return True, target_array

    except Exception as e:
        tmp_msg = g.appmsg.get_log_message("BKY-70009", ['get_target_menu'])
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        g.applogger.info(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.info(msg)
        return False, []


# ツリー作成
def make_tree(objdbca, hierarchy=0):
    """
    make_tree:ツリー作成
    Args:
        objdbca: DBConnectWs(object) # DB接続クラス
        hierarchy: (int, optional)   # 階層数
    Returns:
        (tree_array, hierarchy)
            tree_array: list
            hierarchy: int
    """
    try:
        tmp_msg = 'make_tree start'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # ホストグループ親子紐付テーブルを検索:SQL実行
        hostLinkListTable = HostLinkListTable(objdbca)  # noqa: F405
        sql = hostLinkListTable.create_sselect("WHERE DISUSE_FLAG = '0'")
        result = hostLinkListTable.select_table(sql)
        if result is False:
            tmp_msg = 'select table error HostLinkListTable'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()
        hostLinkListArray = result

        # ホスト紐付管理テーブルを検索:SQL実行
        hostLinkTable = HostLinkTable(objdbca)  # noqa: F405
        sql = hostLinkTable.create_sselect("WHERE DISUSE_FLAG = '0'")
        result = hostLinkTable.select_table(sql)
        if result is False:
            tmp_msg = 'select table error HostLinkTable'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()
        hostLinkArray = result

        tree_array = []
        # ホスト紐付管理テーブルのレコード数分ループ
        for hostLink in hostLinkArray:
            parent_match_flg = False
            child_match_flg = False
            # ツリー用配列の数分ループ
            for tree_data in tree_array:
                tree_data_key = tree_array.index(tree_data)
                # すでに子が登録されている場合
                if tree_data['HOST_ID'] == hostLink['HOSTNAME']:
                    # 親を配列に追加
                    tree_array[tree_data_key]['PARENT_IDS'].append(hostLink['HOSTGROUP_NAME'])
                    tree_array[tree_data_key]['OPERATION'].append(hostLink['OPERATION_ID'])
                    child_match_flg = True

                # すでに親が登録されている場合
                if tree_array[tree_data_key]['HOST_ID'] == hostLink['HOSTGROUP_NAME']:
                    # 子を配列に追加
                    tree_array[tree_data_key]['CHILD_IDS'].append(hostLink['HOSTNAME'])
                    tree_array[tree_data_key]['ALL_CHILD_IDS'].append(hostLink['HOSTNAME'])
                    parent_match_flg = True

            if child_match_flg is False:
                # 子追加
                tree_array.append(
                    {
                        'HOST_ID': hostLink['HOSTNAME'],
                        'OPERATION': [hostLink['OPERATION_ID']],
                        'HIERARCHY': 1,
                        'DATA': None,
                        'PARENT_IDS': [hostLink['HOSTGROUP_NAME']],
                        'CHILD_IDS': [],
                        'ALL_CHILD_IDS': [],
                        'UPLOAD_FILES': {},
                    }
                )

            if parent_match_flg is False:
                # 親追加
                tree_array.append(
                    {
                        'HOST_ID': hostLink['HOSTGROUP_NAME'],
                        'OPERATION': [],
                        'HIERARCHY': 2,
                        'DATA': None,
                        'PARENT_IDS': [],
                        'CHILD_IDS': [hostLink['HOSTNAME']],
                        'ALL_CHILD_IDS': [hostLink['HOSTNAME']],
                        'UPLOAD_FILES': {},
                    }
                )

        # tree_array
        tmp_msg = 'set tree_array'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = tree_array
        # ### g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        stop_flg = False
        hierarchy = 1

        while stop_flg is False:
            hierarchy += 1

            # 階層が一定数に達した場合、処理を終了する
            if hostgroup_const.HIERARCHY_LIMIT_BKY < hierarchy:
                tmp_msg = 'hierarchy over the limit'
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                return False, [], hierarchy

            tree_upd_flg = False

            # ツリー用配列の数分ループ
            for tree_data in tree_array:
                tree_data_key = tree_array.index(tree_data)
                if tree_array[tree_data_key]['HIERARCHY'] != hierarchy:
                    continue

                # ホストグループ親子紐付テーブルのレコード数分ループ
                for hostLinkList in hostLinkListArray:
                    if tree_array[tree_data_key]['HOST_ID'] != hostLinkList['CH_HOSTGROUP']:
                        continue

                    tree_upd_flg = True

                    # 親を配列に追加
                    tree_array[tree_data_key]['PARENT_IDS'].append(hostLinkList['PA_HOSTGROUP'])

                    # すでに親が登録されているか確認
                    tree_match_flg = False
                    for tree_data2 in tree_array:
                        tree_data_key2 = tree_array.index(tree_data2)
                        if tree_array[tree_data_key2]['HOST_ID'] == hostLinkList['PA_HOSTGROUP'] \
                                and tree_array[tree_data_key2]['HIERARCHY'] == hierarchy + 1:
                            # 子を配列に追加
                            tree_array[tree_data_key2]['CHILD_IDS'].append(hostLinkList['CH_HOSTGROUP'])
                            tree_array[tree_data_key2]['ALL_CHILD_IDS'].append(tree_data['ALL_CHILD_IDS'])

                            tree_match_flg = True
                            break

                    if tree_match_flg is False:
                        # 親追加
                        tree_array.append(
                            {
                                'HOST_ID': hostLinkList['PA_HOSTGROUP'],
                                'OPERATION': None,
                                'HIERARCHY': hierarchy + 1,
                                'DATA': None,
                                'PARENT_IDS': [],
                                'CHILD_IDS': [hostLinkList['CH_HOSTGROUP']],
                                'ALL_CHILD_IDS': tree_data['ALL_CHILD_IDS'],
                                'UPLOAD_FILES': {},
                            }
                        )
            if tree_upd_flg is False:
                stop_flg = True

        # tree_array add hierarchy
        tmp_msg = 'tree_array add hierarchy'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = tree_array
        # ### g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        tmp_msg = 'make_tree end'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        return True, tree_array, hierarchy

    except Exception as e:
        tmp_msg = g.appmsg.get_log_message("BKY-70009", ['make_tree'])
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        g.applogger.info(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.info(msg)
        return False, tree_array, hierarchy


# ホストグループ分解
def split_host_grp(hgsp_config, hgsp_data):
    """
    split_host_grp
    Args:
        hgsp_config : {
            'objdbca', #
            'input_table',    # 分割対象のテーブルクラス
            'input_view',     # 分割対象のビュークラス
            'output_table',   # 入力対象のテーブルクラス
            'output_view',    # 入力対象のテーブルクラス
            'target_row_id',  # ホストグループ分割対象ID
            'input_menu_id',  # 分割対象のメニューID
            'output_menu_id', # 入力対象のメニューID
            'vertical_flg'    # 縦型フラグ
        }
        hgsp_data: {
            'update_cnt', # 更新件数
            'insert_cnt', # 登録件数
            'disuse_cnt', # 廃止件数
            'tree_array', # ホストグループ親子関係構造
            'hierarchy',  # 階層数
            ,,,
        }
    Returns:
        (hgsp_config, hgsp_data)
    """

    tranStartFlg = False
    idxs = {}
    copy_file_array = []
    operation_ids = {}
    input_data = []
    try:
        objdbca = hgsp_config.get('objdbca')
        input_table = hgsp_config.get('input_table')
        output_table = hgsp_config.get('output_table')
        input_view = hgsp_config.get('input_view')
        input_view = hgsp_config.get('input_view')
        output_view = hgsp_config.get('output_view')
        target_row_id = hgsp_config.get('target_row_id')
        vertical_flg = hgsp_config.get('vertical_flg')

        # update_cnt = hgsp_data.get('update_cnt')
        # insert_cnt = hgsp_data.get('insert_cnt')
        disuse_cnt = hgsp_data.get('disuse_cnt')

        # トランザクション開始
        tmp_msg = 'db_transaction_start'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        result = objdbca.db_transaction_start()
        if result is not True:
            raise Exception()
        tranStartFlg = True

        # 入力用と出力用の可変部分のキーを取得する
        if vertical_flg is False:
            tmp_idindex = input_table.column_names.index('OPERATION_ID')
        else:
            tmp_idindex = input_table.column_names.index('INPUT_ORDER')
        idxs['FREE_START'] = tmp_idindex
        if idxs['FREE_START'] is None:
            raise Exception()
        idxs['FREE_START'] += 1

        tmp_idindex = input_table.column_names.index('NOTE')
        idxs['FREE_END'] = tmp_idindex
        if idxs['FREE_END'] is None:
            raise Exception()
        idxs['FREE_END'] -= 1

        # 入力用と出力用の項目が一致しているか確認する:TABLE
        if len(input_table.column_names) != len(output_table.column_names):
            tmp_msg = 'split/input table column num error'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()

        # 入力用と出力用の項目が一致しているか確認する:VIEW
        if len(input_view.column_names) != len(output_view.column_names):
            tmp_msg = 'split/input view column num error'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()

        for i in range(idxs['FREE_START'], idxs['FREE_END']):
            if input_table.column_names[i] != output_table.column_names[i]:
                tmp_msg = 'split/input column name error'
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                raise Exception()

        # 入力用テーブルを検索(ソート用にVIEW対象):SQL実行
        sql = input_view.create_sselect("WHERE DISUSE_FLAG = '0'")
        result = input_view.select_table(sql)
        if result is False:
            tmp_msg = 'select table error input_view'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()
        input_data_array = result

        #  配列が空ではない・HOST_IDが存在しない場合はホストグループ分割対象の分割済みフラグをONにし処理を終了する
        if 0 < len(input_data_array):
            for input_data in input_data_array:
                if 'HOST_ID' in input_data is False:
                    result = update_split_target_flg(objdbca, target_row_id, "1")
                    result = objdbca.db_transaction_end(True)
                    tmp_msg = 'db_transaction_end: {}'.format(result)
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    return result, hgsp_data,

        # オペレーションID(実施予定日_ID_オペレーション名)の順に昇順に並べ替える
        if 0 < len(input_data_array):
            if vertical_flg is False:
                input_data_array = sorted(
                    input_data_array,
                    key=lambda x: (x['BASE_TIMESTAMP'], x['OPERATION_NAME'])
                )
            else:
                input_data_array = sorted(
                    input_data_array,
                    key=lambda x: (x['BASE_TIMESTAMP'], x['OPERATION_NAME'], x['INPUT_ORDER'])
                )
        # 出力用テーブルを検索:SQL実行
        sql = output_table.create_sselect("WHERE DISUSE_FLAG = '0'")
        result = output_table.select_table(sql)
        if result is False:
            tmp_msg = 'select table error output_table'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()
        output_data_array = result

        # 分割対象、入力対象0件: 処理終了
        if len(input_data_array) == 0 and len(output_data_array) == 0:
            tmp_msg = 'update_split_target_flg 0 -> 1'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            result = update_split_target_flg(objdbca, target_row_id, "1")
            tmp_msg = 'split, input menu no data'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            result = objdbca.db_transaction_end(True)
            tmp_msg = 'db_transaction_end: {}'.format(result)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            return True, hgsp_data

        # 優先順位を取得するためにホストグループ一覧を検索:SQL実行
        host_group_listTable = HostgroupListTable(objdbca)  # noqa: F405
        sql = host_group_listTable.create_sselect("WHERE DISUSE_FLAG = '0' ORDER BY PRIORITY ASC")
        result = host_group_listTable.select_table(sql)
        if result is False:
            tmp_msg = 'select table error HostgroupListTable'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()
        host_group_list_array = result
        host_group_id_list = [hgd.get('ROW_ID') for hgd in host_group_list_array]

        hold_host_id = []
        sameid_array = None

        # コンフィグ設定
        hgsp_data.setdefault('idxs', idxs)
        hgsp_data.setdefault('host_group_list_array', host_group_list_array)
        hgsp_data.setdefault('host_group_id_list', host_group_id_list)
        hgsp_data.setdefault('output_data_array', output_data_array)
        hgsp_data.setdefault('copy_file_array', copy_file_array)
        hgsp_data.setdefault('operation_ids', operation_ids)
        hgsp_data.setdefault('sameid_array', None)
        hgsp_data.setdefault('hold_host_id', [])

        # 入力用,代入値自動登録用のレコード件数
        tmp_msg = 'recode count split:{} input:{}'.format(len(input_data_array), len(output_data_array))
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # 対象ホスト、ホストグループ-オペレーション
        tmp_msg = "target hostgroup-operation"
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = [[hgsp_config['alllist'][_t['HOST_ID']], _t['OPERATION_NAME']] for _t in input_data_array]
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = "target hostgroup-operation id->name"
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = [[hgsp_config['alllist'][_t['HOST_ID']], _t['OPERATION_NAME']] for _t in input_data_array]
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # オペレーションID毎にホストデータ作成(基準日時->オペレーション名:昇順)
        for input_data in input_data_array:
            input_data_key = input_data_array.index(input_data)

            # 優先順位を入力データと紐付ける
            match_flg = False
            for host_group_list in host_group_list_array:
                if input_data['HOST_ID'] == host_group_list['ROW_ID']:
                    input_data_array[input_data_key]['PRIORITY'] = host_group_list['PRIORITY']
                    match_flg = True

            # ホストの場合, PRIORITY:最大設定(0-2147483647)
            if match_flg is False or input_data['HOST_ID'] not in host_group_id_list:
                input_data_array[input_data_key]['PRIORITY'] = hostgroup_const.MAX_PRIORITY

            # 一回目の場合
            if sameid_array is None:
                sameid_array = [input_data]
                continue

            if vertical_flg is False:
                # オペレーションIDが一致した場合
                if sameid_array[0]['OPERATION_ID'] == input_data['OPERATION_ID']:
                    sameid_array.append(input_data)
                    continue
            else:
                # オペレーションIDと入力順序が一致した場合
                if sameid_array[0]['OPERATION_ID'] == input_data['OPERATION_ID']\
                        and sameid_array[0]['INPUT_ORDER'] == input_data['INPUT_ORDER']:
                    sameid_array.append(input_data)
                    continue

            # オペレーションIDが異なっていた場合、ホストデータを作成する

            hgsp_data['sameid_array'] = sameid_array
            result, hgsp_config, hgsp_data = make_host_data(hgsp_config, hgsp_data)
            if result is False:
                return False

            sameid_array = hgsp_data.get('sameid_array')
            output_data_array = hgsp_data.get('output_data_array')

            # 次のオペレーションのデータSET
            sameid_array = [input_data]

        if sameid_array is not None:
            # オペレーションIDが異なっていた場合、ホストデータを作成する

            hgsp_data['sameid_array'] = sameid_array
            result, hgsp_config, hgsp_data = make_host_data(hgsp_config, hgsp_data)
            if result is False:
                return False

        # ホストデータの廃止を行うために対象のレコードを特定する
        hold_host_id = hgsp_data.get('hold_host_id')
        tmp_msg = 'hold_host_id'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = hold_host_id
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        tmp_msg = 'hold_host_id id->name'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = id_conv(hold_host_id, hgsp_config['alllist'])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        for output_data in output_data_array:
            # 分割データにある場合は廃止しない
            hold_key = create_hold_key(vertical_flg, output_data.get('HOST_ID'), output_data.get('OPERATION_ID'), output_data.get('INPUT_ORDER'))
            if hold_key in hold_host_id:
                tmp_msg = 'not discard in split data:({}[{}])'.format(id_conv(hold_key, hgsp_config['alllist']), hold_key)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                continue

            # すでに廃止の場合は廃止しない
            if output_data['DISUSE_FLAG'] == "1":
                tmp_msg = 'already discard in split data:({}[{}])'.format(id_conv(hold_key, hgsp_config['alllist']), hold_key)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                continue

            #  廃止する
            update_data = output_data
            update_data['DISUSE_FLAG'] = "1"  # 廃止フラグ
            update_data['LAST_UPDATE_USER'] = g.USER_ID   # 最終更新者

            # 出力用テーブルを更新
            result = output_table.update_table(update_data)
            tmp_msg = 'discard: data'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            tmp_msg = update_data
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            tmp_msg = 'discard: result'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            tmp_msg = result
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            if result is False:
                tmp_msg = 'update_table is faild'
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                raise Exception()

            disuse_cnt += 1
        hgsp_data['disuse_cnt'] = disuse_cnt

        # ホストグループ分割対象テーブルを検索:SQL実行
        split_target_table = SplitTargetTable(objdbca)  # noqa: F405
        sql = split_target_table.create_sselect(
            "WHERE DISUSE_FLAG = '0' AND ROW_ID = '{}'".format(hgsp_config['target_row_id'])
        )
        result = split_target_table.select_table(sql)
        if result is False:
            tmp_msg = 'select table error SplitTargetTable'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            raise Exception()
        split_target_array = result

        target_timestamp = hgsp_config['target_timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')
        target_timestamp_now = split_target_array[0]['LAST_UPDATE_TIMESTAMP'].strftime('%Y-%m-%d %H:%M:%S.%f')

        # 分割処理の開始時、終了時の最終更新日時が一致した場合、ホストグループ分割対象の分割済みフラグをONにする
        if target_timestamp == target_timestamp_now:
            tmp_msg = 'update_split_target_flg 0 -> 1'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            result = update_split_target_flg(objdbca, target_row_id, "1")
        else:
            tmp_msg = 'updated split_target: split_target_flg no update and next cycle'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # アップロードファイルコピー
        tmp_msg = 'copy_upload_file split->input'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        copy_file_array = hgsp_data.get('copy_file_array')
        result = copy_upload_file(copy_file_array)
        if result is False:
            raise Exception()

        # コミット
        result = objdbca.db_transaction_end(True)  # True / False
        tmp_msg = 'db_transaction_end: {}'.format(result)
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        if result is not True:
            raise Exception()

        tranStartFlg = False

        return True, hgsp_data

    except Exception as e:
        g.applogger.info(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.info(msg)

        if tranStartFlg is True:
            # ロールバック
            result = objdbca.db_transaction_end(False)
            tmp_msg = 'db_transaction_end rollback: {}'.format(result)
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        return False, hgsp_data


# ホストデータ作成
def make_host_data(hgsp_config, hgsp_data):
    """
    make_host_data: ホストデータ作成
    Args:
        hgsp_config : {
            'objdbca', #
            'input_table',    # 分割対象のテーブルクラス
            'input_view',     # 分割対象のビュークラス
            'output_table',   # 入力対象のテーブルクラス
            'output_view',    # 入力対象のテーブルクラス
            'target_row_id',  # ホストグループ分割対象ID
            'input_menu_id',  # 分割対象のメニューID
            'output_menu_id', # 入力対象のメニューID
            'vertical_flg'    # 縦型フラグ
        }
        hgsp_data: {
            'update_cnt', # 更新件数
            'insert_cnt', # 登録件数
            'disuse_cnt', # 廃止件数
            'tree_array', # ホストグループ親子関係構造
            'hierarchy',  # 階層数

            'host_group_list_array', # ホストグループデータ
            'host_group_id_list',    # ホストグループIDリスト
            'output_data_array',     # 入力対象のデータ
            'copy_file_array',       # ファイルコピー情報設定
            'sameid_array',          # 同一処理対象(オペレーション or オペレーション + 代入順序)
            'hold_host_id',          # 廃止除外対象
        }
    Returns:
        (bool, hgsp_config, hgsp_data)
    """
    tmp_msg = 'make_host_data Start'
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    try:
        output_table = hgsp_config.get('output_table')
        file_columns_info = hgsp_config.get('file_columns_info')
        vertical_flg = hgsp_config.get('vertical_flg')

        tree_array = copy.deepcopy(hgsp_data.get('tree_array'))
        hierarchy = hgsp_data.get('hierarchy')
        idxs = hgsp_data.get('idxs')
        host_group_id_list = hgsp_data.get('host_group_id_list')
        output_data_array = hgsp_data.get('output_data_array')
        sameid_array = copy.deepcopy(hgsp_data.get('sameid_array'))

        # return
        hold_host_id = hgsp_data.get('hold_host_id')
        update_cnt = hgsp_data.get('update_cnt')
        insert_cnt = hgsp_data.get('insert_cnt')
        disuse_cnt = hgsp_data.get('disuse_cnt')
        copy_file_array = hgsp_data.get('copy_file_array')

        alone_data_array = []

        # 処理対象オペレーション
        target_op_name = list(set(id_conv([x['OPERATION_ID'] for x in sameid_array], hgsp_config['alllist'])))[0]
        target_opid = list(set([x['OPERATION_ID'] for x in sameid_array]))[0]
        tmp_msg = 'operation: {}({})'.format(target_op_name, target_opid)
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # ツリー配列にデータを設定する
        for sameid_data in sameid_array:
            treematch_flg = False
            for tree_data in tree_array:
                tree_data_key = tree_array.index(tree_data)
                parent_ids_list = copy.deepcopy(tree_array[tree_data_key]['PARENT_IDS'])
                operation_list = copy.deepcopy(tree_array[tree_data_key]['OPERATION'])
                # 該当以外削除:OPERATION-PARENT_ID
                if operation_list is None:
                    pass
                elif len(operation_list) != 0:
                    parent_ids = []
                    operation = []
                    p_idx = 0
                    for tmp_opid in operation_list:
                        tmp_parent_id = parent_ids_list[p_idx]
                        if tmp_opid == target_opid:
                            operation.append(tmp_opid)
                            parent_ids.append(tmp_parent_id)
                        p_idx += 1
                if len(parent_ids) != 0 and len(parent_ids) != 0:
                    parent_ids_list = parent_ids
                    operation_list = operation

                tree_array[tree_data_key]['PARENT_IDS'] = copy.deepcopy(parent_ids_list)
                tree_array[tree_data_key]['ALL_PARENT_IDS'] = copy.deepcopy(parent_ids_list)
                tree_array[tree_data_key]['OPERATION'] = copy.deepcopy(operation_list)
                if sameid_data.get('HOST_ID') == tree_data.get('HOST_ID'):
                    treematch_flg = True
                    tree_array[tree_data_key]['DATA'] = copy.deepcopy(sameid_data)
                    tree_array[tree_data_key]['DATA_HIERARCHY'] = copy.deepcopy(tree_array[tree_data_key]['HIERARCHY'])
                    # アップロードファイルがあるか確認
                    data_json = json.loads(sameid_data.get("DATA_JSON"))
                    row_id = sameid_data.get('ROW_ID')
                    for rest_key, file_name in data_json.items():
                        if rest_key in file_columns_info['target_rest_name']:
                            tree_array[tree_data_key]['UPLOAD_FILES'].setdefault(rest_key, None)
                            tree_array[tree_data_key]['UPLOAD_FILES'][rest_key] = {"id": row_id, "name": file_name}
            if treematch_flg is False:
                alone_data_array.append(sameid_data)

        tmp_msg = 'set data tree/alone'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = tree_array
        # ### g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        tmp_msg = 'set data tree_array id->name'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = id_conv([v for v in tree_array if v['HOST_ID'] not in host_group_id_list], hgsp_config['alllist'], 'dict')
        # ### g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        tmp_msg = 'set alone_data_array'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = alone_data_array
        # ### g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        tmp_msg = 'set alone_data_array id->name'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = id_conv([v for v in alone_data_array if v['HOST_ID'] not in host_group_id_list], hgsp_config['alllist'], 'dict')
        # ### g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        # ツリー上にいなかったデータを単独で登録する
        for alone_data in alone_data_array:
            # ホストグループの場合は無視する
            if alone_data['HOST_ID'] in host_group_id_list:
                continue

            # 保有しているホストIDを退避しておく
            hold_key = create_hold_key(vertical_flg, alone_data.get('HOST_ID'), alone_data.get('OPERATION_ID'), alone_data.get('INPUT_ORDER'))
            hold_host_id.append(hold_key)

            # 代入値自動登録用のデータ検索
            match_flg = False
            for output_data in output_data_array:
                update_data = None
                insert_data = None

                # ホストIDとオペレーションIDが一致した場合
                if vertical_flg is False:
                    # ホストIDとオペレーションIDが一致しなかった場合
                    if output_data['HOST_ID'] != alone_data['HOST_ID'] or \
                            output_data['OPERATION_ID'] != alone_data['OPERATION_ID']:
                        continue
                else:
                    # ホストIDとオペレーションIDと入力順序が一致しなかった場合
                    if output_data['HOST_ID'] != alone_data['HOST_ID'] or \
                            output_data['OPERATION_ID'] != alone_data['OPERATION_ID'] or \
                            output_data['INPUT_ORDER'] != alone_data['INPUT_ORDER']:
                        continue

                match_flg = True

                # 自由部分＋備考に差分があるか確認
                chgFlg = False
                for i in range(idxs['FREE_START'], idxs['FREE_END'] + 2):
                    tmp_column_name = output_table.column_names[i]
                    if output_data[tmp_column_name] != alone_data[tmp_column_name]:
                        chgFlg = True

                # アップロードファイルの比較
                for rest_key in file_columns_info['target_rest_name']:
                    alone_id = alone_data['ROW_ID']
                    alone_data_json = json.loads(alone_data.get("DATA_JSON"))
                    output_data_json = json.loads(output_data.get("DATA_JSON"))
                    alone_file_name = alone_data_json.get(rest_key) if rest_key in alone_data_json else None
                    output_file_name = output_data_json.get(rest_key) if rest_key in output_data_json else None
                    input_file_data = None
                    output_file_data = None
                    if alone_file_name:
                        # input_file_path = file_columns_info['input'][rest_key].get_file_data_path(alone_file_name, alone_id, None, False)
                        input_file_data = file_columns_info['input'][rest_key].get_file_data(alone_file_name, alone_id)
                    if output_file_name:
                        # output_file_path = file_columns_info['output'][rest_key].get_file_data_path(output_file_name, alone_id, None, False)
                        output_file_data = file_columns_info['input'][rest_key].get_file_data(alone_file_name, alone_id)

                    # ファイル名,ファイルに差分があるか判定
                    if alone_file_name != output_file_name and input_file_data != output_file_data:
                        chgFlg = True

                    # ファイル解放
                    input_file_data = None
                    output_file_data = None

                if chgFlg is True:
                    # 更新する
                    update_data = output_data
                    for i in range(idxs['FREE_START'], idxs['FREE_END'] + 2):
                        tmp_column_name = output_table.column_names[i]
                        update_data[tmp_column_name] = alone_data[tmp_column_name]
                    update_data['LAST_UPDATE_USER'] = g.USER_ID   # 最終更新者

                    # 出力用テーブルを更新
                    result = output_table.update_table(update_data)

                    tmp_msg = 'update: data'
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    tmp_msg = update_data
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    tmp_msg = 'update: result'
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    tmp_msg = result
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                    if result is False:
                        tmp_msg = 'update_table is faild'
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                        raise Exception()

                    # ファイルコピー情報設定
                    copy_file_array = chk_file_file_columns(file_columns_info, output_table, alone_data, result[0], copy_file_array)

                    update_cnt += 1
                break

            if match_flg is False:
                # 登録する
                insert_data = {}
                insert_data['HOST_ID'] = alone_data['HOST_ID']  # ホスト名
                insert_data['OPERATION_ID'] = alone_data['OPERATION_ID']  # オペレーション/オペレーション
                if vertical_flg is True:
                    insert_data['INPUT_ORDER'] = alone_data['INPUT_ORDER']  # 入力順序

                for i in range(idxs['FREE_START'], idxs['FREE_END'] + 2):
                    tmp_column_name = output_table.column_names[i]
                    insert_data[tmp_column_name] = alone_data[tmp_column_name]

                insert_data['DISUSE_FLAG'] = "0"  # 廃止フラグ
                insert_data['LAST_UPDATE_USER'] = g.USER_ID  # 最終更新者

                # 出力用テーブルに登録
                result = output_table.insert_table(insert_data)

                tmp_msg = 'insert: data'
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                tmp_msg = insert_data
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                tmp_msg = 'insert: result'
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                tmp_msg = result
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                if result is False:
                    tmp_msg = 'insert_table is faild'
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    raise Exception()

                # ファイルコピー情報設定
                copy_file_array = chk_file_file_columns(file_columns_info, output_table, alone_data, result[0], copy_file_array)

                insert_cnt += 1

        # ホストデータを作成するために親から子にデータをコピーしていく
        i = hierarchy
        while i > 0:
            for parent_data in tree_array:
                parent_key = tree_array.index(parent_data)

                if i != tree_array[parent_key]['HIERARCHY']:
                    continue

                # 親のデータが入っていない場合
                if parent_data.get('DATA') is None:
                    continue
                # 子のID分ループ
                for child_id in tree_array[parent_key]['CHILD_IDS']:
                    # 子を特定するためにツリー配列分ループ
                    for tree_data_child in tree_array:
                        tree_data_child_key = tree_array.index(tree_data_child)

                        # 階層が親の階層の一つ下であること
                        if i - 1 != tree_array[tree_data_child_key]['HIERARCHY']:
                            continue
                        # 子のIDと親のIDが紐づいている場合
                        if child_id == tree_array[tree_data_child_key]['HOST_ID'] and \
                                tree_array[parent_key]['HOST_ID'] in tree_array[tree_data_child_key]['PARENT_IDS']:
                            if 0 < len(tree_array[tree_data_child_key]['ALL_PARENT_IDS']):
                                tree_array[tree_data_child_key]['ALL_PARENT_IDS'] = copy.deepcopy(
                                    tree_array[tree_data_child_key]['ALL_PARENT_IDS'] + tree_array[parent_key]['PARENT_IDS']
                                )
                            else:
                                tree_array[tree_data_child_key]['ALL_PARENT_IDS'] = copy.deepcopy(
                                    tree_array[tree_data_child_key]['PARENT_IDS'] + tree_array[parent_key]['PARENT_IDS']
                                )

                            tree_array[tree_data_child_key]['ALL_PARENT_IDS'] = copy.deepcopy(
                                list(set(tree_array[tree_data_child_key]['ALL_PARENT_IDS']))
                            )

                            # 子のデータが入っていない場合
                            if tree_data_child.get('DATA') is None:
                                # 親のデータをそのままコピー
                                tree_array[tree_data_child_key]['DATA'] = copy.deepcopy(tree_array[parent_key]['DATA'])
                                tree_array[tree_data_child_key]['DATA_HIERARCHY'] = copy.copy(tree_array[parent_key]['DATA_HIERARCHY'])
                                tree_array[tree_data_child_key]['UPLOAD_FILES'] = copy.copy(tree_array[parent_key]['UPLOAD_FILES'])
                            # 親も子もデータが入っている場合
                            else:
                                chgFlg = False
                                # 親のデータと差分があるかすべての対象データで確認
                                for j in range(idxs['FREE_START'], idxs['FREE_END'] + 2):
                                    tmp_column_name = output_table.column_names[j]
                                    parent_data_hierarchy = tree_array[parent_key]['DATA_HIERARCHY']
                                    child_data_hierarchy = tree_array[tree_data_child_key]['DATA_HIERARCHY']
                                    # parent_hierarchy = tree_array[parent_key]['HIERARCHY']
                                    # child_hierarchy = tree_array[tree_data_child_key]['HIERARCHY']
                                    parent_priority = tree_array[parent_key]['DATA']['PRIORITY']
                                    child_priority = tree_array[tree_data_child_key]['DATA']['PRIORITY']
                                    parent_priority = parent_priority if parent_priority else hostgroup_const.MAX_PRIORITY
                                    child_priority = child_priority if child_priority else hostgroup_const.MAX_PRIORITY
                                    parent_data = copy.copy(tree_array[parent_key]['DATA'][tmp_column_name])
                                    child_data = copy.copy(tree_array[tree_data_child_key]['DATA'][tmp_column_name])
                                    if tmp_column_name == "DATA_JSON":
                                        parent_data_json = json.loads(parent_data)
                                        child_data_json = json.loads(child_data)
                                        base_data_json = dict((x, y) for x, y in sorted(output_table.objmenu.get_json_cols_base().items()))
                                        for rest_name in base_data_json.keys():
                                            # 空文字の扱いを統一してNoneとして扱う  "" '' -> None
                                            child_val = length0_empty_conv(child_data_json.get(rest_name))
                                            parent_val = length0_empty_conv(parent_data_json.get(rest_name))
                                            # 親も子も値が入っていない場合
                                            if child_val is None and parent_val is None:
                                                base_data_json[rest_name] = None
                                            # 親のみに値が入っている場合
                                            elif child_val is None and parent_val is not None:
                                                base_data_json[rest_name] = parent_val
                                            # 子のみに値が入っている場合
                                            elif child_val is not None and parent_val is None:
                                                base_data_json[rest_name] = child_val
                                            # 親も子も値が入っている場合
                                            else:
                                                # 子のデータの階層が親のデータの階層よりも大きい場合
                                                if child_data_hierarchy > parent_data_hierarchy:
                                                    base_data_json[rest_name] = parent_val
                                                    chgFlg = True
                                                # 子のデータの階層と親のデータの階層が同じ場合
                                                elif child_data_hierarchy == parent_data_hierarchy:
                                                    # 子のデータの優先順位が親のデータの優先順位より小さい場合
                                                    if child_priority < parent_priority:
                                                        # 親のデータ利用:None場合、子のデータ使用
                                                        if parent_val is not None:
                                                            base_data_json[rest_name] = parent_val
                                                        else:
                                                            base_data_json[rest_name] = child_val
                                                        chgFlg = True
                                                    else:
                                                        # 子のデータ利用:Noneの場合、親のデータ使用
                                                        if child_val is not None:
                                                            base_data_json[rest_name] = child_val
                                                        else:
                                                            base_data_json[rest_name] = parent_val
                                                        chgFlg = True
                                                else:
                                                    base_data_json[rest_name] = child_val
                                                    chgFlg = True
                                                    # 何もしない
                                                    pass
                                        tree_array[tree_data_child_key]['DATA'][tmp_column_name] = json.dumps(base_data_json, ensure_ascii=False)
                                    else:
                                        # 空文字の扱いを統一してNoneとして扱う  "" '' -> None
                                        child_data = length0_empty_conv(child_data)
                                        parent_data = length0_empty_conv(parent_data)

                                        # 親も子も値が入っていない場合
                                        if child_data is None and parent_data is None:
                                            tree_array[tree_data_child_key]['DATA'][tmp_column_name] = None
                                            pass
                                        # 親のみに値が入っている場合
                                        elif child_data is None and parent_data is not None:
                                            tree_array[tree_data_child_key]['DATA'][tmp_column_name] = copy.copy(parent_data)
                                        # 子のみに値が入っている場合
                                        elif child_data is not None and parent_data is None:
                                            tree_array[tree_data_child_key]['DATA'][tmp_column_name] = copy.copy(child_data)
                                            pass
                                        # 親も子も値が入っている場合
                                        else:
                                            # 子のデータの階層が親のデータの階層よりも大きい場合
                                            if child_data_hierarchy > parent_data_hierarchy:
                                                tree_array[tree_data_child_key]['DATA'][tmp_column_name] = copy.copy(parent_data)
                                                chgFlg = True
                                            # 子のデータの階層と親のデータの階層が同じ場合
                                            elif child_data_hierarchy == parent_data_hierarchy:
                                                # 子のデータの優先順位が親のデータの優先順位より小さい場合
                                                if child_priority < parent_priority:
                                                    # 親のデータ利用:None場合、子のデータ使用
                                                    if parent_val is not None:
                                                        tree_array[tree_data_child_key]['DATA'][tmp_column_name] = copy.copy(parent_data)
                                                    else:
                                                        tree_array[tree_data_child_key]['DATA'][tmp_column_name] = copy.copy(child_data)
                                                    chgFlg = True
                                                else:
                                                    # 子のデータ利用:Noneの場合、親のデータ使用
                                                    if child_val is not None:
                                                        tree_array[tree_data_child_key]['DATA'][tmp_column_name] = copy.copy(child_data)
                                                    else:
                                                        tree_array[tree_data_child_key]['DATA'][tmp_column_name] = copy.copy(parent_data)
                                                    chgFlg = True
                                            # 子のデータの階層が親のデータの階層よりも小さい場合
                                            else:
                                                # 何もしない
                                                pass
                                if chgFlg is False:
                                    tree_array[tree_data_child_key]['DATA_HIERARCHY'] = copy.copy(tree_array[parent_key]['DATA_HIERARCHY'])
                                    tree_array[tree_data_child_key]['DATA']['PRIORITY'] = copy.copy(tree_array[parent_key]['DATA']['PRIORITY'])
            i -= 1

        tmp_msg = 'set parent->child copy data tree_array'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = tree_array
        # ### g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        tmp_msg = 'set parent->child copy data tree_array id->name'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = id_conv([v for v in tree_array if v['HOST_ID'] not in host_group_id_list], hgsp_config['alllist'], 'dict')
        # ### g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        kykey_array = [tmp_tree.get('HOST_ID') for tmp_tree in tree_array]

        # ホストデータの作成を行う
        for host_data in tree_array:
            # key = tree_array.index(host_data)
            if 1 != host_data['HIERARCHY']:
                continue

            if host_data['DATA'] is None:
                continue

            try:
                match_kyKey_idx = kykey_array.index(host_data['DATA']['HOST_ID'])
            except Exception:
                match_kyKey_idx = False

            if match_kyKey_idx is False:
                continue

            opematch_flg = False
            if 1 == tree_array[match_kyKey_idx]['HIERARCHY']:
                opematch_flg = True
            else:
                for parent_id in host_data['PARENT_IDS']:
                    parent_id_Key = host_data['PARENT_IDS'].index(parent_id)
                    match_parent_kykey_idx = kykey_array.index(parent_id)

                    try:
                        match_parent_kykey_idx = kykey_array.index(parent_id)
                    except Exception:
                        match_parent_kykey_idx = False

                    if match_parent_kykey_idx is False:
                        continue

                    if host_data['DATA']['HOST_ID'] == parent_id \
                            or host_data['DATA']['HOST_ID'] in tree_array[match_parent_kykey_idx]['ALL_PARENT_IDS'] is not False:

                        # if "" == host_data['OPERATION'][parent_id_Key] \
                        #         or host_data['DATA']['OPERATION_ID'] in host_data['OPERATION']:
                        #     opematch_flg = True
                        if len(host_data['OPERATION']) >= parent_id_Key \
                                or host_data['DATA']['OPERATION_ID'] in host_data['OPERATION']:
                            opematch_flg = True

            if opematch_flg is False:
                continue

            # 上から継承されてきたデータのHOST_IDを自分のHOST_IDにする
            host_data['DATA']['HOST_ID'] = host_data['HOST_ID']

            match_flg = False
            for output_data in output_data_array:
                update_data = {}
                insert_data = {}

                # ホストIDとオペレーションIDが一致した場合
                if vertical_flg is False:

                    # ホストIDとオペレーションIDが一致しなかった場合
                    if output_data['HOST_ID'] != host_data['DATA']['HOST_ID'] \
                            or output_data['OPERATION_ID'] != host_data['DATA']['OPERATION_ID']:
                        continue
                else:
                    # ホストIDとオペレーションIDと入力順序が一致しなかった場合
                    if output_data['HOST_ID'] != host_data['DATA']['HOST_ID'] \
                        or output_data['OPERATION_ID'] != host_data['DATA']['OPERATION_ID'] \
                            or output_data['INPUT_ORDER'] != host_data['DATA']['INPUT_ORDER']:
                        continue

                # 保有しているホストIDを退避しておく
                hold_key = create_hold_key(
                    vertical_flg,
                    host_data.get('HOST_ID'),
                    host_data['DATA'].get('OPERATION_ID'),
                    host_data['DATA'].get('INPUT_ORDER')
                )
                hold_host_id.append(hold_key)

                match_flg = True

                # 自由部分＋備考に差分があるか確認
                chgFlg = False
                for i in range(idxs['FREE_START'], idxs['FREE_END'] + 2):
                    tmp_column_name = output_table.column_names[i]
                    if output_data[tmp_column_name] != host_data['DATA'][tmp_column_name]:
                        chgFlg = True

                # アップロードファイルの比較
                for rest_key in file_columns_info['target_rest_name']:
                    host_id = host_data['DATA']['ROW_ID']
                    alone_data_json = json.loads(host_data['DATA'].get("DATA_JSON"))
                    output_data_json = json.loads(output_data.get("DATA_JSON"))
                    alone_file_name = alone_data_json.get(rest_key) if rest_key in alone_data_json else None
                    output_file_name = output_data_json.get(rest_key) if rest_key in output_data_json else None
                    input_file_data = None
                    output_file_data = None
                    if alone_file_name:
                        # input_file_path = file_columns_info['input'][rest_key].get_file_data_path(alone_file_name, host_id, None, False)
                        input_file_data = file_columns_info['input'][rest_key].get_file_data(alone_file_name, host_id)
                    if output_file_name:
                        # output_file_path = file_columns_info['output'][rest_key].get_file_data_path(output_file_name, host_id, None, False)
                        output_file_data = file_columns_info['input'][rest_key].get_file_data(alone_file_name, host_id)
                    if alone_file_name != output_file_name and input_file_data != output_file_data:
                        chgFlg = True

                    # ファイル解放
                    input_file_data = None
                    output_file_data = None

                # 廃止になっている場合は復活する
                if "1" == output_data['DISUSE_FLAG']:
                    chgFlg = True

                if chgFlg is True:
                    # 更新する
                    update_data = output_data
                    for i in range(idxs['FREE_START'], idxs['FREE_END'] + 2):
                        tmp_column_name = output_table.column_names[i]
                        update_data[tmp_column_name] = host_data['DATA'][tmp_column_name]
                    update_data['DISUSE_FLAG'] = "0"  # 廃止フラグ
                    update_data['LAST_UPDATE_USER'] = g.USER_ID  # 最終更新者

                    # 出力用テーブルを更新
                    result = output_table.update_table(update_data)

                    tmp_msg = 'update: data'
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    tmp_msg = update_data
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    tmp_msg = 'update: result'
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    tmp_msg = result
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                    if result is False:
                        tmp_msg = 'update_table is faild'
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                        raise Exception()

                    # ファイルコピー情報設定
                    copy_file_array = chk_file_file_columns(file_columns_info, output_table, host_data['DATA'], result[0], copy_file_array)

                    update_cnt += 1

            if match_flg is False:
                if host_data['DATA'].get('OPERATION_ID') not in host_data['OPERATION']:
                    continue

                # 保有しているホストIDを退避しておく
                hold_key = create_hold_key(
                    vertical_flg,
                    host_data.get('HOST_ID'),
                    host_data['DATA'].get('OPERATION_ID'),
                    host_data['DATA'].get('INPUT_ORDER')
                )
                hold_host_id.append(hold_key)

                # 登録する
                insert_data = {
                    'HOST_ID': None,
                    'OPERATION_ID': None,
                    'INPUT_ORDER': None,
                    'DATA_JSON': None,
                    'DISUSE_FLAG': None,
                    'LAST_UPDATE_USER': None,
                }
                insert_data['HOST_ID'] = host_data['DATA']['HOST_ID']  # ホスト名
                insert_data['OPERATION_ID'] = host_data['DATA']['OPERATION_ID']  # オペレーション/オペレーション
                if vertical_flg is True:
                    insert_data['INPUT_ORDER'] = host_data['DATA']['INPUT_ORDER']  # 入力順序
                else:
                    del insert_data['INPUT_ORDER']
                for i in range(idxs['FREE_START'], idxs['FREE_END'] + 2):
                    tmp_column_name = output_table.column_names[i]
                    insert_data[tmp_column_name] = host_data['DATA'][tmp_column_name]

                insert_data['DISUSE_FLAG'] = "0"  # 廃止フラグ
                insert_data['LAST_UPDATE_USER'] = g.USER_ID  # 最終更新者

                # 出力用テーブルに登録
                result = output_table.insert_table(insert_data)

                tmp_msg = 'insert: data'
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                tmp_msg = insert_data
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                tmp_msg = 'insert: result'
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                tmp_msg = result
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

                if result is False:
                    tmp_msg = 'insert_table is faild'
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    raise Exception()

                # ファイルコピー情報設定
                copy_file_array = chk_file_file_columns(file_columns_info, output_table, host_data['DATA'], result[0], copy_file_array)

                insert_cnt += 1

        # 返却値設定
        hgsp_data['copy_file_array'] = copy_file_array
        hgsp_data['hold_host_id'] = hold_host_id
        hgsp_data['insert_cnt'] = insert_cnt
        hgsp_data['update_cnt'] = update_cnt
        hgsp_data['disuse_cnt'] = disuse_cnt

        tmp_msg = 'make_host_data End'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

        return True, hgsp_config, hgsp_data

    except Exception as e:
        tmp_msg = g.appmsg.get_log_message("BKY-70009", ['make_host_data'])
        g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        g.applogger.info(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.info(msg)
        return False, hgsp_config, hgsp_data


# ファイルアップロード対象のカラムクラス取得
def get_file_columns_info(objdbca, input_table, output_table):
    """
    get_file_columns_info: ファイルアップロード対象のカラムクラス取得
    Args:
        file_columns_info: {} file column info
        input_table: split BaseTable class
        output_table: input BaseTable class
    Returns:
        (bool, result)
    """
    try:
        target_columns = [
            "FileUploadColumn",
            "FileUploadEncryptColumn"
        ]

        result = {
            'target_rest_name': None,
            'input': {},
            'output': {}
        }

        # load_table
        objinput = input_table.get_load_table()
        objoutput = output_table.get_load_table()

        # 分割対象/入力対象のファイルアップロード系項目取得
        input_fupcol_list = [_key for _key in objinput.restkey_list if objinput.get_col_class_name(_key) in target_columns]
        output_fupcol_list = [_key for _key in objinput.restkey_list if objinput.get_col_class_name(_key) in target_columns]
        input_fupcol_list = set(input_fupcol_list)
        output_fupcol_list = set(output_fupcol_list)

        # 分割対象/入力対象の項目一致
        if input_fupcol_list != output_fupcol_list:
            raise Exception()

        result['target_rest_name'] = input_fupcol_list

        # カラムクラス生成
        for rest_key in input_fupcol_list:
            class_name = objinput.get_col_class_name(rest_key)
            obj_column_input = load_objcolumn(objdbca, objinput.objtable, rest_key, col_class_name=class_name)
            obj_column_output = load_objcolumn(objdbca, objoutput.objtable, rest_key, col_class_name=class_name)
            result['input'].setdefault(rest_key, obj_column_input)
            result['output'].setdefault(rest_key, obj_column_output)

        return True, result

    except Exception as e:
        g.applogger.info(addline_msg('{}{}'.format(e, sys._getframe().f_code.co_name)))
        type_, value, traceback_ = sys.exc_info()
        msg = traceback.format_exception(type_, value, traceback_)
        g.applogger.info(msg)
        return False, []


# アップロードファイルのコピー用情報収集
def chk_file_file_columns(file_columns_info, output_table, input_data, target_data, copy_file_array=[]):
    """
    copy_upload_file: アップロードファイルのコピー、リンク生成
    Args:
        file_columns_info: {} file column info
        output_table: BaseTable class
        input_data: split table data
        target_data:  input table data
        copy_file_array: copy file info
    Returns:
        copy_file_array
    """
    for rest_key in file_columns_info['target_rest_name']:
        alone_data_json = json.loads(target_data.get("DATA_JSON"))
        alone_file_name = alone_data_json.get(rest_key) if rest_key in alone_data_json else None
        if alone_file_name:
            input_file_path = file_columns_info['input'][rest_key].get_file_data_path(alone_file_name, input_data['ROW_ID'], None, False)
            jnl_data = output_table.objmenu.get_maintenance_uuid(target_data['ROW_ID'])
            jnl_uuid = jnl_data[0]["JOURNAL_SEQ_NO"]
            output_file_path = file_columns_info['output'][rest_key].get_file_data_path(alone_file_name, target_data['ROW_ID'], jnl_uuid, False)
            link_file_path = file_columns_info['output'][rest_key].get_file_data_path(alone_file_name, target_data['ROW_ID'], None, False)
            # 現在のリンク先のパスを取得
            try:
                old_dest_file_path = os.readlink(link_file_path)
            except Exception:
                old_dest_file_path = None
            copy_data_info = {
                'file': alone_file_name,  # 現在のファイル名
                'src_dir': input_file_path.replace(alone_file_name, ''),  # ディレクトリパス:入力用
                'dest_dir': output_file_path.replace(alone_file_name, ''),  # ディレクトリ:代入値自動登録用
                'src': input_file_path,  # ファイルパス:入力用
                'dest': output_file_path,  # ファイルパス:代入値自動登録用
                'link': link_file_path,  # 作成するリンクパス:代入値自動登録用
                'old_dest': old_dest_file_path,  # 現在のリンク参照先パス:代入値自動登録用
            }
            copy_file_array.append(copy_data_info)

            # アップロードファイルのコピー用情報
            tmp_msg = 'add copy_file_array'
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            tmp_msg = copy_data_info
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    return copy_file_array


# アップロードファイルのコピー、リンク生成
def copy_upload_file(copy_file_array):
    """
    copy_upload_file: アップロードファイルのコピー、リンク生成
    Args:
        copy_file_array:
    Returns:
        bool
    """
    for copy_file in copy_file_array:
        try:
            # ファイル、ディレクトリの確認
            tmp_isdir = os.path.isdir(copy_file['dest_dir'])  # noqa: F405
            tmp_isfile = os.path.isfile(copy_file['src'])  # noqa: F405
            if tmp_isdir is False and tmp_isfile is True:

                # コピー先のディレクトリ作成
                tmp_msg = 'makedir: {}'.format(copy_file['dest_dir'])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                os.makedirs(copy_file['dest_dir'], exist_ok=True)  # noqa: F405

                # ファイルコピー
                tmp_msg = 'copy src:{} dest:{}'.format(copy_file['src'], copy_file['dest'])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                shutil.copy2(copy_file['src'], copy_file['dest'])

                # シンボリックリンク解除
                if os.path.islink(copy_file['link']):
                    tmp_msg = 'unlink: {}'.format(copy_file['link'])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    os.unlink(copy_file['link'])

                # シンボリックリンク作成
                tmp_msg = 'symlink src:{} link:{}'.format(copy_file['dest'], copy_file['link'])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                os.symlink(copy_file['dest'], copy_file['link'])  # noqa: F405

        except Exception as e:
            tmp_msg = e
            g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
            try:
                # パス回復
                # シンボリックリンク解除
                if os.path.islink(copy_file['link']):
                    tmp_msg = g.appmsg.get_log_message("BKY-70010", [copy_file['link']])
                    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                    os.unlink(copy_file['link'])

                # シンボリックリンク作成
                tmp_msg = g.appmsg.get_log_message("BKY-70011", [copy_file['dest'], copy_file['link']])
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                os.symlink(copy_file['old_dest'], copy_file['link'])  # noqa: F405
            except Exception as e:
                tmp_msg = e
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                tmp_msg = g.appmsg.get_log_message("BKY-70012", [copy_file['link'], copy_file['old_dest']])
                g.applogger.info(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    return True


# ホストグループ分割対象のフラグ更新:全メニュー DIVIDED_FLG 1->0
def reset_split_target_flg(objdbca):
    """
    update_split_target_flg: ホストグループ分割対象のフラグ更新:全メニュー DIVIDED_FLG 1->0
    Args:
        objdbca:
    Returns:
        bool
    """
    # ホストグループ分割対象テーブルを検索:SQL実行(UPDATE)
    split_target_table = SplitTargetTable(objdbca)  # noqa: F405
    sql = textwrap.dedent("""
        UPDATE
            `T_HGSP_SPLIT_TARGET` SET `DIVIDED_FLG` = '0'
        WHERE `T_HGSP_SPLIT_TARGET`.`DISUSE_FLAG` = '0'
    """).format().strip()
    result = split_target_table.exec_query(sql)
    if result is False:
        return False
    return True


# ホストグループ分割対象のフラグ更新:対象メニュー DIVIDED_FLG 1->0
def update_split_target_flg(objdbca, target_row_id, divided_flg):
    """
    update_split_target_flg: ホストグループ分割対象のフラグ更新:対象メニュー DIVIDED_FLG 1->0
    Args:
        objdbca:
        target_row_id:
        divided_flg:
    Returns:
        bool
    """
    # ホストグループ分割対象テーブルを検索:UPDATE実行
    split_target_table = SplitTargetTable(objdbca)  # noqa: F405
    update_data = {
        'ROW_ID': target_row_id,
        'DIVIDED_FLG': divided_flg,
        'LAST_UPDATE_TIMESTAMP': get_now_datetime(),
        'LAST_UPDATE_USER': g.USER_ID
    }
    result = split_target_table.update_record(update_data)
    if result is False:
        return False
    return True


# ホストグループ分割対象のレコード取得
def get_split_target_data(objdbca, menu_id):
    """
    get_split_target_data: ホストグループ分割対象のレコード取得
    Args:
        vertical_flg:
        menu_id:
    Returns:
        result: split_target list
    """
    # ホストグループ分割対象テーブルを検索:SQL実行
    split_target_table = SplitTargetTable(objdbca)  # noqa: F405
    sql = split_target_table.create_sselect("WHERE DISUSE_FLAG = '0' and INPUT_MENU_ID = '{}'".format(menu_id))
    result = split_target_table.select_table(sql)
    if result is False:
        raise Exception()
    return result


# 代入値自動登録設定のbackyard処理の処理済みフラグ更新
def update_ploc_loaded_flg(objdbca, loaded_flg="0"):
    """
    update_ploc_loaded_flg: 代入値自動登録設定のbackyard処理の処理済みフラグ更新
    Args:
        objdbca:
        loaded_flg:
    Returns:
        bool
    """
    comn_proc_loaded_table = PlocLoadedTable(objdbca)  # noqa: F405
    sql = textwrap.dedent("""
        UPDATE
            `{tablename}`
        SET `LOADED_FLG` = %s, `LAST_UPDATE_TIMESTAMP` = %s
            WHERE ROW_ID IN (202, 203, 204)
        ;
    """).format(tablename=comn_proc_loaded_table.table_name).strip()
    result = comn_proc_loaded_table.exec_query(sql, [loaded_flg, get_now_datetime()])
    if result is False:
        return False
    return True


# キー生成:host operation input_order
def create_hold_key(vertical_flg, host_id, operation_id, input_order):
    """
    create_hold_key: create host_id + operation_id (+ input_order)
    Args:
        vertical_flg:
        host_id:
        operation_id:
        input_order:
    Returns:
        host_id + operation_id (+ input_order)
    """
    if vertical_flg is False:
        return "{}{}".format(host_id, operation_id)
    else:
        return "{}{}{}".format(host_id, operation_id, input_order)


# カラムクラス呼び出し
def load_objcolumn(objdbca, objtable, rest_key, col_class_name='TextColumn', ):
    """
    load_objcolumn
    Args:
        objdbca: db class
        objtable: loadtable class
        rest_key: rest key
        col_class_name: column class name. Defaults to 'TextColumn'.

    Returns:
        objcolumn: column class
    """
    try:
        eval_class_str = "{}(objdbca,objtable,rest_key,'')".format(col_class_name)
        objcolumn = eval(eval_class_str)
    except Exception:
        return False
    return objcolumn


def get_all_list(objdbca):
    """
    json_serial: datetime, date -> str
    Args:
        obj:
    Returns:
        xxxx :
    """
    sql = textwrap.dedent("""
        SELECT
            SYSTEM_ID AS KID,
            HOST_NAME AS KVAL
        FROM
            `T_ANSC_DEVICE`
        WHERE
            `DISUSE_FLAG` = '0'
        UNION
        SELECT
            OPERATION_ID AS KID,
            OPERATION_NAME AS KVAL
        FROM
            `T_COMN_OPERATION`
        WHERE
            `DISUSE_FLAG` = '0'
        UNION
        SELECT
            ROW_ID AS KID,
            HOSTGROUP_NAME AS KVAL
        FROM
            `T_HGSP_HOSTGROUP_LIST`
        WHERE
            `DISUSE_FLAG` = '0';
    """).format().strip()
    tmp_result = objdbca.sql_execute(sql, [])
    result = {}
    for x in tmp_result:
        result.setdefault(x['KID'], x['KVAL'])
    return result


def addline_msg(msg=''):
    info = inspect.getouterframes(inspect.currentframe())[1]
    msg_line = "{} ({}:{})".format(msg, os.path.basename(info.filename), info.lineno)
    return msg_line


def json_serial(obj):
    """
    json_serial: datetime, date -> str
    Args:
        obj:
    Returns:
        xxxx :
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()


def id_conv(data, iddict={}, mode='dict'):
    """
    id_conv: id -> name convert dict use
    Args:
        data: dict
        iddict: dict
        mode: return type
    Returns:
        xxxx :
    """
    xxxx = json.dumps(data, default=json_serial)
    for _k, _v in iddict.items():
        xxxx = xxxx.replace(_k, _v)
    if mode == 'dict':
        xxxx = json.loads(xxxx)
    return xxxx


def length0_empty_conv(str_data):
    """
    length0_empty_conv: "" -> None convert
    Args:
        str_data: str
    Returns:
        str_data or None
    """
    if str_data is None:
        return None
    elif len(str_data) == 0:
        return None
    else:
        return str_data


def get_now_datetime(format='%Y/%m/%d %H:%M:%S', type='str'):
    """
    get_now_datetime:
    Args:
        format (str, optional): format. Defaults to '%Y/%m/%d %H:%M:%S'.
        type (str, optional): return type. Defaults to 'str'.

    Returns:
        dt : datetime. Defaults to str(%Y/%m/%d %H:%M:%S).
    """
    dt = datetime.now().strftime(format)
    if type == 'str':
        return '{}'.format(dt)
    else:
        return dt
