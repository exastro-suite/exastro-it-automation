#   Copyright 2023 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
from flask import g
from dictknife import deepmerge
import re
import json
import uuid


def set_member_vars(objdbca, TFConst, module_matter_id, variable_data, exist_member_vars_list):  # noqa: C901
    """
        メンバー変数テーブルに対する処理を実行する。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            TFConst: 定数呼び出しクラス
            module_matter_id: 対象のmodule素材ID
            variable_data: tfファイルから抽出したvariableブロックのデータ
            exist_member_vars_list: 廃止対象としないメンバー変数のリスト
        RETRUN:
            boolean, msg
    """
    try:
        # 返却値の変数定義
        result = True
        msg = ""

        # メンバー変数関連処理の開始
        child_vars_id = 0
        parent_vars_id = 0
        temp_member_data_list = []
        type_data = variable_data.get('type')
        default_data = variable_data.get('default')
        variable = variable_data.get('variable')
        if not isinstance(type_data, list) and not isinstance(type_data, dict):
            # type_dataがlistでもdictでもない場合はリターン
            return result, msg, exist_member_vars_list

        # 対象のmodule_matter_idとvariableが一致するレコードをModule-変数紐付から取得する
        where_str = 'WHERE MODULE_MATTER_ID = %s AND VARS_NAME = %s AND DISUSE_FLAG = %s'
        record = objdbca.table_select(TFConst.T_MODULE_VAR, where_str, [module_matter_id, variable, 0])
        if record:
            module_vars_link_id = record[0].get('MODULE_VARS_LINK_ID')
        else:
            # メンバー変数レコードの作成において、Module-変数紐付のレコード取得に失敗しました。
            msg = g.appmsg.get_log_message("BKY-50108", [])
            raise Exception(msg)

        g.applogger.debug(g.appmsg.get_log_message("BKY-50006"))
        # データの整形(配列の作成ローカル番号)
        type_nest_dict = {}
        temp_member_data_list, child_vars_id, parent_vars_id = create_member_data(objdbca, TFConst, module_vars_link_id, child_vars_id, parent_vars_id, temp_member_data_list, type_data, default_data, type_nest_dict)  # noqa: E501

        # 整形したメンバー変数データをループ
        for index, temp_member_data in enumerate(temp_member_data_list):
            module_regist_flag = temp_member_data.get('module_regist_flag')
            if module_regist_flag is True:
                max_col_seq = temp_member_data.get('max_col_seq')
                # 変数ネスト管理に「Module-変数紐付ID」のレコードがすでに登録されているかを検索する
                registered_max_col_data = get_regist_max_module_col_data(objdbca, TFConst, module_vars_link_id)

                # 最大繰り返し数が0より大きい場合
                if max_col_seq > 0:
                    if registered_max_col_data.get('is_regist') is False:
                        # 未登録の場合、登録処理を実行
                        res = regist_max_col(objdbca, TFConst, module_vars_link_id, None, max_col_seq)
                        if not res:
                            # 変数ネスト管理へのレコード登録に失敗
                            msg = g.appmsg.get_log_message("BKY-50109", [])
                            raise Exception(msg)
                    else:
                        # 登録済みの場合、登録状況によって処理を分岐
                        # 登録済みの最大繰り返し数と取得した要素数に差があるかつ最終更新者がシステムの場合、最大繰り返し数を更新。
                        if not (str(registered_max_col_data.get('max_col_seq')) == str(max_col_seq)) and registered_max_col_data.get('is_system') is True:  # noqa: E501
                            res = update_max_col(objdbca, TFConst, registered_max_col_data.get('MAX_COL_SEQ_ID'), max_col_seq)
                            if not res:
                                # 変数ネスト管理のレコード更新に失敗
                                msg = g.appmsg.get_log_message("BKY-50110", [])
                                raise Exception(msg)

                        # 最終更新者がバックヤードユーザかつ廃止状態の場合、最大繰り返し数を更新するとともに活性化(復活)。
                        elif str(registered_max_col_data.get('DISUSE_FLAG')) == "1" and registered_max_col_data.get('is_system') is True:
                            res = update_max_col(objdbca, TFConst, registered_max_col_data.get('MAX_COL_SEQ_ID'), max_col_seq)
                            if not res:
                                # 変数ネスト管理のレコード更新に失敗
                                msg = g.appmsg.get_log_message("BKY-50110", [])
                                raise Exception(msg)

                        # 最大更新者がバックヤードユーザ以外の場合、temp_member_data_listのデータを書き換える
                        elif registered_max_col_data.get('is_system') is False:
                            temp_member_data_list[index]["max_col_seq"] = registered_max_col_data.get('max_col_seq')
                            temp_member_data_list[index]["force_max_col_seq_flag"] = True

                # 最大繰り返し数が0以下の場合
                else:
                    # 登録済みのレコードを廃止する
                    if registered_max_col_data.get('is_regist') is True and str(registered_max_col_data.get('DISUSE_FLAG')) == "0":
                        res = discard_max_col(objdbca, TFConst, registered_max_col_data.get('MAX_COL_SEQ_ID'))
                        if not res:
                            # 変数ネスト管理のレコード廃止に失敗
                            msg = g.appmsg.get_log_message("BKY-50111", [])
                            raise Exception(msg)

        # 再度一時格納データの変数をセット
        # temp_member_data_list = []
        temp_member_data_list_2 = []
        temp_member_data_list_3 = []
        member_data_list = []
        type_nest_dict = {}
        child_vars_id = 0
        parent_vars_id = 0
        nest_level = 0

        # # 変数ネスト管理に合わせたタイプの整形
        # type_data = adjust_type_data_by_max_col_seq(objdbca, TFConst, type_data, temp_member_data_list)

        # データの整形
        temp_member_data_list_2, child_vars_id, parent_vars_id = create_member_data(objdbca, TFConst, module_vars_link_id, child_vars_id, parent_vars_id, temp_member_data_list_2, type_data, default_data, type_nest_dict, nest_level)  # noqa: E501

        # ローカルID→項番に差し替え、親番号の取得、変数ネスト管理テーブルから最大繰り返し数の取得
        temp_member_data_list_3 = create_member_data_for_regist(objdbca, TFConst, temp_member_data_list_2)

        # 変数ネスト管理に合わせてタイプ整形
        type_data = adjust_type_data_by_max_col_seq(objdbca, TFConst, type_data, temp_member_data_list_3)

        # 最終的なメンバー変数データを作成(この時点でローカルIDに差し変わるので注意)
        type_nest_dict = {}
        child_vars_id = 0
        parent_vars_id = 0
        nest_level = 0
        member_data_list, child_vars_id, parent_vars_id = create_member_data(objdbca, TFConst, module_vars_link_id, child_vars_id, parent_vars_id, member_data_list, type_data, default_data, type_nest_dict, nest_level)  # noqa: E501

        # ローカルID→項番に差し替え、親番号の取得、変数ネスト管理テーブルから最大繰り返し数の取得
        member_data_list = create_member_data_for_regist(objdbca, TFConst, member_data_list)

        # メンバー変数レコードの処理を分類ごとに振り分ける
        regist_member_data = part_member_data_for_regist(objdbca, TFConst, member_data_list)

        # メンバー変数管理の廃止対象を選定するために、ここで該当のレコードを保管する。
        exist_member_vars_list.extend(regist_member_data.get('update'))
        exist_member_vars_list.extend(regist_member_data.get('skip'))
        exist_member_vars_list.extend(regist_member_data.get('restore'))
        exist_member_vars_list.extend(regist_member_data.get('regist'))

        # メンバー変数管理への登録/更新/復活作業スタート
        primary_key_name = 'CHILD_MEMBER_VARS_ID'

        # 登録対象をループ
        g.applogger.debug(g.appmsg.get_log_message("BKY-50007"))
        for r_member_data in regist_member_data.get('regist'):
            # 登録用に「MAX_COL_SEQ」のkeyを削除する
            temp_r_member_data = r_member_data.copy()
            temp_r_member_data.pop('MAX_COL_SEQ')
            ret_data = objdbca.table_insert(TFConst.T_VAR_MEMBER, temp_r_member_data, primary_key_name)
            if not ret_data:
                # メンバー変数管理へのレコード登録に失敗
                msg = g.appmsg.get_log_message("BKY-50112", [])
                raise Exception(msg)

            # typeが変数ネスト管理の対象である場合
            if int(r_member_data.get('MAX_COL_SEQ')) > 0:
                registed_max_member_col_data = get_regist_max_member_col_data(objdbca, TFConst, r_member_data.get('CHILD_MEMBER_VARS_ID'))
                # 変数ネスト管理に登録された要素数を特定
                registed_max_col_seq = registed_max_member_col_data.get('max_col_seq')
                # tfファイルのdefaultから要素数を特定
                tf_max_col_seq = r_member_data.get('MAX_COL_SEQ')
                # 変数ネスト管理とtfファイルから取得した最大繰り返し数に差分があり、最終更新者がバックヤードシステムの場合は、変数ネスト管理の値を更新
                if registed_max_member_col_data.get('is_regist') is True and not str(registed_max_col_seq) == str(tf_max_col_seq) and registed_max_member_col_data.get('is_system') is True:  # noqa: E501
                    res = update_max_col(objdbca, TFConst, registed_max_member_col_data.get('MAX_COL_SEQ_ID'), tf_max_col_seq)
                    if not res:
                        # 変数ネスト管理のレコード更新に失敗
                        msg = g.appmsg.get_log_message("BKY-50110", [])
                        raise Exception(msg)

                # 変数ネスト管理のレコードが廃止済みかつ最終更新者がバックヤードシステムの場合は、tf_max_col_seqで変数ネスト管理の値を更新(復活)
                elif registed_max_member_col_data.get('is_regist') is True and str(registed_max_member_col_data.get('DISUSE_FLAG')) == "1" and registed_max_member_col_data.get('is_system') is True:  # noqa: E501
                    res = update_max_col(objdbca, TFConst, registed_max_member_col_data.get('MAX_COL_SEQ_ID'), tf_max_col_seq)
                    if not res:
                        # 変数ネスト管理のレコード更新に失敗
                        msg = g.appmsg.get_log_message("BKY-50110", [])
                        raise Exception(msg)

                # 変数ネスト管理のレコードが廃止済みかつ最終更新者がユーザのの場合は、registed_max_col_seqで変数ネスト管理の値を更新(復活)
                elif registed_max_member_col_data.get('is_regist') is True and str(registed_max_member_col_data.get('DISUSE_FLAG')) == "1" and registed_max_member_col_data.get('is_system') is False:  # noqa: E501
                    res = update_max_col(objdbca, TFConst, registed_max_member_col_data.get('MAX_COL_SEQ_ID'), registed_max_col_seq)
                    if not res:
                        # 変数ネスト管理のレコード更新に失敗
                        msg = g.appmsg.get_log_message("BKY-50110", [])
                        raise Exception(msg)

                # 未登録の場合、最大繰り返し数の登録
                if registed_max_member_col_data.get('is_regist') is False:
                    res = regist_max_col(objdbca, TFConst, r_member_data.get('PARENT_VARS_ID'), r_member_data.get('CHILD_MEMBER_VARS_ID'), r_member_data.get('MAX_COL_SEQ'))  # noqa: E501
                    if not res:
                        # 変数ネスト管理へのレコード登録に失敗
                        msg = g.appmsg.get_log_message("BKY-50109", [])
                        raise Exception(msg)

        # 更新対象をループ
        g.applogger.debug(g.appmsg.get_log_message("BKY-50008"))
        for r_member_data in regist_member_data.get('update'):
            # 更新用に「MAX_COL_SEQ」のkeyを削除する
            temp_r_member_data = r_member_data.copy()
            temp_r_member_data.pop('MAX_COL_SEQ')
            ret_data = objdbca.table_update(TFConst.T_VAR_MEMBER, temp_r_member_data, primary_key_name)
            if not ret_data:
                # メンバー変数管理のレコード更新に失敗
                msg = g.appmsg.get_log_message("BKY-50113", [])
                raise Exception(msg)

            # typeが変数ネスト管理の対象である場合
            if int(r_member_data.get('MAX_COL_SEQ')) > 0:
                registed_max_member_col_data = get_regist_max_member_col_data(objdbca, TFConst, r_member_data.get('CHILD_MEMBER_VARS_ID'))
                # 変数ネスト管理に登録された要素数を特定
                registed_max_col_seq = registed_max_member_col_data.get('max_col_seq')
                # tfファイルのdefaultから要素数を特定
                tf_max_col_seq = r_member_data.get('MAX_COL_SEQ')

                # 変数ネスト管理とtfファイルから取得した最大繰り返し数に差分があり、最終更新者がシステムの場合は変数ネスト管理の値を更新
                if registed_max_member_col_data.get('is_regist') is True and str(registed_max_member_col_data.get('DISUSE_FLAG')) == "0" and not str(registed_max_col_seq) == str(tf_max_col_seq) and registed_max_member_col_data.get('is_system') is True:  # noqa: E501
                    res = update_max_col(objdbca, TFConst, registed_max_member_col_data.get('MAX_COL_SEQ_ID'), tf_max_col_seq)
                    if not res:
                        # 変数ネスト管理のレコード更新に失敗
                        msg = g.appmsg.get_log_message("BKY-50110", [])
                        raise Exception(msg)

        # 復活対象をループ
        g.applogger.debug(g.appmsg.get_log_message("BKY-50009"))
        for r_member_data in regist_member_data.get('restore'):
            # 復活用に「MAX_COL_SEQ」のkeyを削除する
            temp_r_member_data = r_member_data.copy()
            temp_r_member_data.pop('MAX_COL_SEQ')
            ret_data = objdbca.table_update(TFConst.T_VAR_MEMBER, temp_r_member_data, primary_key_name)
            if not ret_data:
                # メンバー変数管理のレコード更新に失敗
                msg = g.appmsg.get_log_message("BKY-50113", [])
                raise Exception(msg)

            # typeが変数ネスト管理の対象である場合
            if int(r_member_data.get('MAX_COL_SEQ')) > 0:
                registed_max_member_col_data = get_regist_max_member_col_data(objdbca, TFConst, r_member_data.get('CHILD_MEMBER_VARS_ID'))
                # 変数ネスト管理に登録された要素数を特定
                registed_max_col_seq = registed_max_member_col_data.get('max_col_seq')
                # tfファイルのdefaultから要素数を特定
                tf_max_col_seq = r_member_data.get('MAX_COL_SEQ')

                # 復活を実行
                if registed_max_member_col_data.get('is_regist') is True:
                    res = update_max_col(objdbca, TFConst, registed_max_member_col_data.get('MAX_COL_SEQ_ID'), tf_max_col_seq)
                    if not res:
                        # 変数ネスト管理のレコード更新に失敗
                        msg = g.appmsg.get_log_message("BKY-50110", [])
                        raise Exception(msg)
                else:
                    # is_registがTrueでないなら登録を実行する
                    res = regist_max_col(objdbca, TFConst, r_member_data.get('PARENT_VARS_ID'), r_member_data.get('CHILD_MEMBER_VARS_ID'), r_member_data.get('MAX_COL_SEQ'))  # noqa: E501
                    if not res:
                        # 変数ネスト管理へのレコード登録に失敗
                        msg = g.appmsg.get_log_message("BKY-50109", [])
                        raise Exception(msg)

        # スキップ対象をループ。スキップは変数ネスト管理の更新のみ。
        g.applogger.debug(g.appmsg.get_log_message("BKY-50010"))
        for r_member_data in regist_member_data.get('skip'):
            if int(r_member_data.get('MAX_COL_SEQ')) > 0:
                registed_max_member_col_data = get_regist_max_member_col_data(objdbca, TFConst, r_member_data.get('CHILD_MEMBER_VARS_ID'))
                # 変数ネスト管理に登録された要素数を特定
                registed_max_col_seq = registed_max_member_col_data.get('max_col_seq')
                # tfファイルのdefaultから要素数を特定
                tf_max_col_seq = r_member_data.get('MAX_COL_SEQ')

                # 変数ネスト管理とtfファイルから取得した最大繰り返し数に差分があり、最終更新者がバックヤードシステムの場合は、変数ネスト管理の値を更新
                if registed_max_member_col_data.get('is_regist') is True and not str(registed_max_col_seq) == str(tf_max_col_seq) and registed_max_member_col_data.get('is_system') is True:  # noqa: E501
                    res = update_max_col(objdbca, TFConst, registed_max_member_col_data.get('MAX_COL_SEQ_ID'), tf_max_col_seq)
                    if not res:
                        # 変数ネスト管理のレコード更新に失敗
                        msg = g.appmsg.get_log_message("BKY-50110", [])
                        raise Exception(msg)

                # 変数ネスト管理のレコードが廃止済みかつ最終更新者がバックヤードシステムの場合は、tf_max_col_seqで変数ネスト管理の値を更新(復活)
                elif registed_max_member_col_data.get('is_regist') is True and str(registed_max_member_col_data.get('DISUSE_FLAG')) == "1" and registed_max_member_col_data.get('is_system') is True:  # noqa: E501
                    res = update_max_col(objdbca, TFConst, registed_max_member_col_data.get('MAX_COL_SEQ_ID'), tf_max_col_seq)
                    if not res:
                        # 変数ネスト管理のレコード更新に失敗
                        msg = g.appmsg.get_log_message("BKY-50110", [])
                        raise Exception(msg)

                # 変数ネスト管理のレコードが廃止済みかつ最終更新者がユーザのの場合は、registed_max_col_seqで変数ネスト管理の値を更新(復活)
                elif registed_max_member_col_data.get('is_regist') is True and str(registed_max_member_col_data.get('DISUSE_FLAG')) == "1" and registed_max_member_col_data.get('is_system') is False:  # noqa: E501
                    res = update_max_col(objdbca, TFConst, registed_max_member_col_data.get('MAX_COL_SEQ_ID'), registed_max_col_seq)
                    if not res:
                        # 変数ネスト管理のレコード更新に失敗
                        msg = g.appmsg.get_log_message("BKY-50110", [])
                        raise Exception(msg)

    except Exception as e:
        msg = e
        result = False

    return result, msg, exist_member_vars_list


def set_movement_var_member_link(objdbca, TFConst):
    """
        Movement-Module変数紐付に登録されているレコードから、Movement-メンバーModule変数紐テーブルを更新する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            TFConst: 定数呼び出しクラス
        RETRUN:
            rboolean, msg
    """
    try:
        # 変数定義
        result = True
        msg = ''

        # Movement-変数紐付テーブルからレコードを取得
        where_str = 'WHERE DISUSE_FLAG = %s'
        t_movement_var_link_records = objdbca.table_select(TFConst.T_MOVEMENT_VAR, where_str, [0])

        # Movement-メンバー変数紐付テーブルからレコードをすべて取得（廃止含め）
        where_str = ''
        t_movement_var_member_link_records = objdbca.table_select(TFConst.T_MOVEMENT_VAR_MEMBER, where_str, [])

        # メンバー変数管理テーブルからレコードを取得
        where_str = 'WHERE DISUSE_FLAG = %s'
        t_var_member_records = objdbca.table_select(TFConst.T_VAR_MEMBER, where_str, [0])

        # トランザクション開始
        objdbca.db_transaction_start()

        # 不要レコードを特定するため、利用中レコードを格納するlist
        active_record_list = []

        # Movement-変数紐付テーブルのレコードをループ(record1)
        for record1 in t_movement_var_link_records:
            # メンバー変数管理テーブルからレコードをループ(record2)
            for record2 in t_var_member_records:
                # record1とrecord2からModule-変数紐付のIDをそれぞれ取得(メンバー変数管理テーブルのカラム名は「PARENT_VARS_ID」なので注意)
                module_vars_link_id_1 = record1.get('MODULE_VARS_LINK_ID')
                module_vars_link_id_2 = record2.get('PARENT_VARS_ID')

                # record1とrecord2のModule-変数紐付のIDが一致していなければcontinue
                if not module_vars_link_id_1 == module_vars_link_id_2:
                    continue

                # record1からMovementIDを取得
                movement_id_1 = record1.get('MOVEMENT_ID')

                # record2からメンバー変数のIDを取得
                member_vars_id_2 = record2.get('CHILD_MEMBER_VARS_ID')

                # Movement-メンバー変数紐付テーブルからレコードをループ(record3)
                exist_flag = False
                for record3 in t_movement_var_member_link_records:
                    movement_id_3 = record3.get('MOVEMENT_ID')
                    module_vars_link_id_3 = record3.get('MODULE_VARS_LINK_ID')
                    member_vars_id_3 = record3.get('CHILD_MEMBER_VARS_ID')
                    # Movement, Module-変数紐付, メンバー変数のIDがすべて一致しているレコードを特定しbreak
                    if movement_id_1 == movement_id_3 and module_vars_link_id_1 == module_vars_link_id_3 and member_vars_id_2 == member_vars_id_3:
                        exist_flag = True
                        exist_record_id = record3.get('MVMT_VAR_MEMBER_LINK_ID')
                        exist_record_disuse_flag = record3.get('DISUSE_FLAG')
                        break

                if exist_flag:
                    # 一致するレコードがあれば、対象のレコードが対象のレコードが廃止済みかどうかを判定する。廃止されていない場合は何も処理を行わない。
                    if exist_record_disuse_flag == "1":
                        # 対象のレコードが廃止済みであれば、「復活」を実行
                        data_list = {
                            "MVMT_VAR_MEMBER_LINK_ID": exist_record_id,
                            "DISUSE_FLAG": "0",
                            "LAST_UPDATE_USER": g.get('USER_ID'),
                        }
                        primary_key_name = 'MVMT_VAR_MEMBER_LINK_ID'
                        ret_data = objdbca.table_update(TFConst.T_MOVEMENT_VAR_MEMBER, data_list, primary_key_name)
                        if not ret_data:
                            # Movement-メンバー変数紐付のレコード更新に失敗
                            msg = g.appmsg.get_log_message("6", [])
                            raise Exception(msg)

                        # 対象を廃止しないためにactive_record_listに追加
                        active_record_list.append(exist_record_id)
                    else:
                        # 一致するレコードがアクティブ状態なので対象を廃止しないためにactive_record_listに追加
                        active_record_list.append(exist_record_id)

                else:
                    # 一致するレコードがない場合は、レコードを新規登録する
                    data_list = {
                        "MOVEMENT_ID": movement_id_1,
                        "MODULE_VARS_LINK_ID": module_vars_link_id_1,
                        "CHILD_MEMBER_VARS_ID": member_vars_id_2,
                        "DISUSE_FLAG": "0",
                        "LAST_UPDATE_USER": g.get('USER_ID'),
                    }
                    primary_key_name = 'MVMT_VAR_MEMBER_LINK_ID'
                    ret_data = objdbca.table_insert(TFConst.T_MOVEMENT_VAR_MEMBER, data_list, primary_key_name)
                    if not ret_data:
                        # Movement-メンバー変数紐付へのレコード登録に失敗
                        msg = g.appmsg.get_log_message("BKY-50115", [])
                        raise Exception(msg)

        # Module-変数紐付テーブルから不要レコードを廃止する)
        g.applogger.debug(g.appmsg.get_log_message("BKY-50015"))
        for record in t_movement_var_member_link_records:
            disuse_flag = record.get('DISUSE_FLAG')
            mvmt_var_member_link_id = record.get('MVMT_VAR_MEMBER_LINK_ID')
            # アクティブなレコードかつ、active_record_listに含まれていないIDのレコードを廃止する
            if disuse_flag == "0" and mvmt_var_member_link_id not in active_record_list:
                data_list = {
                    "MVMT_VAR_MEMBER_LINK_ID": mvmt_var_member_link_id,
                    "DISUSE_FLAG": "1",
                    "LAST_UPDATE_USER": g.get('USER_ID'),
                }
                primary_key_name = 'MVMT_VAR_MEMBER_LINK_ID'
                ret_data = objdbca.table_update(TFConst.T_MOVEMENT_VAR_MEMBER, data_list, primary_key_name)
                if not ret_data:
                    # Movement-メンバー変数紐付の不要レコード廃止に失敗
                    msg = g.appmsg.get_log_message("BKY-50117", [])
                    raise Exception(msg)

        # トランザクション終了(正常)
        objdbca.db_transaction_end(True)

    except Exception as e:
        msg = e
        result = False

        # トランザクション終了(異常)
        objdbca.db_transaction_end(False)

    return result, msg


def discard_member_vars(objdbca, TFConst, exist_member_vars_list):
    """
        メンバー変数テーブルの不要なレコードを廃止する。
        また、関連する変数ネスト管理の不要なレコードも廃止する。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            TFConst: 定数呼び出しクラス
            exist_member_vars_list: 廃止対象としないメンバー変数管理のレコードリスト
        RETRUN:
            boolean, msg
    """
    try:
        # 返却値の変数定義
        result = True
        msg = ""

        # Module-変数紐付テーブルで廃止されているレコードを取得 -> 対象のIDをlist化
        where_str = 'WHERE DISUSE_FLAG = %s'
        t_mod_var_link_discard_records = objdbca.table_select(TFConst.T_MODULE_VAR, where_str, [1])
        mod_var_link_discard_id_list = []
        for record in t_mod_var_link_discard_records:
            module_vars_link_id = record.get('MODULE_VARS_LINK_ID')
            mod_var_link_discard_id_list.append(module_vars_link_id)

        # Module-変数紐付テーブル廃止レコードlistにあるIDをPARENT_VARS_ID(VARS_ID)に持つメンバー変数管理と変数ネスト管理のレコードを廃止する
        for mod_var_link_id in mod_var_link_discard_id_list:
            # メンバー変数管理テーブルから廃止対象を検索し、廃止する。
            g.applogger.debug(g.appmsg.get_log_message("BKY-50012"))
            where_str = 'WHERE PARENT_VARS_ID = %s AND DISUSE_FLAG = %s'
            discard_target_records = objdbca.table_select(TFConst.T_VAR_MEMBER, where_str, [mod_var_link_id, 0])
            for record in discard_target_records:
                child_member_vars_id = record.get('CHILD_MEMBER_VARS_ID')
                data_list = {
                    "CHILD_MEMBER_VARS_ID": child_member_vars_id,
                    "DISUSE_FLAG": "1",
                    "LAST_UPDATE_USER": g.get('USER_ID'),
                }
                primary_key_name = 'CHILD_MEMBER_VARS_ID'
                ret_data = objdbca.table_update(TFConst.T_VAR_MEMBER, data_list, primary_key_name)
                if not ret_data:
                    # メンバー変数管理の不要レコードの廃止に失敗
                    msg = g.appmsg.get_log_message("BKY-50114", [])
                    raise Exception(msg)

            # 変数ネスト管理テーブルから廃止対象を検索し、廃止する。
            g.applogger.debug(g.appmsg.get_log_message("BKY-50013"))
            where_str = 'WHERE VARS_ID = %s AND DISUSE_FLAG = %s'
            discard_target_records = objdbca.table_select(TFConst.T_NESTVARS_MEMBER_MAX, where_str, [mod_var_link_id, 0])
            for record in discard_target_records:
                child_member_vars_id = record.get('MAX_COL_SEQ_ID')
                data_list = {
                    "MAX_COL_SEQ_ID": child_member_vars_id,
                    "DISUSE_FLAG": "1",
                    "LAST_UPDATE_USER": g.get('USER_ID'),
                }
                primary_key_name = 'MAX_COL_SEQ_ID'
                ret_data = objdbca.table_update(TFConst.T_NESTVARS_MEMBER_MAX, data_list, primary_key_name)
                if not ret_data:
                    # 変数ネスト管理の不要レコードの廃止に失敗
                    msg = g.appmsg.get_log_message("BKY-50111", [])
                    raise Exception(msg)

        # 不要なメンバー変数レコード削除処理スタート
        # メンバー変数管理でアクティブなレコードをすべて取得
        where_str = 'WHERE DISUSE_FLAG = %s'
        t_var_member_records = objdbca.table_select(TFConst.T_VAR_MEMBER, where_str, [0])
        for record in t_var_member_records:
            discard_flag = True
            for exist_target in exist_member_vars_list:
                if record.get('CHILD_MEMBER_VARS_ID') == exist_target.get('CHILD_MEMBER_VARS_ID'):
                    discard_flag = False
                    break

            if discard_flag:
                # メンバー変数管理から対象レコードを廃止
                g.applogger.debug(g.appmsg.get_log_message("BKY-50012"))
                child_member_vars_id = record.get('CHILD_MEMBER_VARS_ID')
                data_list = {
                    "CHILD_MEMBER_VARS_ID": child_member_vars_id,
                    "DISUSE_FLAG": "1",
                    "LAST_UPDATE_USER": g.get('USER_ID'),
                }
                primary_key_name = 'CHILD_MEMBER_VARS_ID'
                ret_data = objdbca.table_update(TFConst.T_VAR_MEMBER, data_list, primary_key_name)
                if not ret_data:
                    # メンバー変数管理の不要レコードの廃止に失敗
                    msg = g.appmsg.get_log_message("BKY-50114", [])
                    raise Exception(msg)

                # 変数ネスト管理に廃止した対象のIDを持つレコードがあれば、こちらも廃止する
                g.applogger.debug(g.appmsg.get_log_message("BKY-50013"))
                registered_max_col_data = get_regist_max_module_col_data(objdbca, TFConst, record.get('child_member_vars_id'))
                if registered_max_col_data.get('is_regist') is True and str(registered_max_col_data.get('DISUSE_FLAG')) == "0":
                    max_col_seq_id = registered_max_col_data.get('MAX_COL_SEQ_ID')
                    data_list = {
                        "MAX_COL_SEQ_ID": max_col_seq_id,
                        "DISUSE_FLAG": "1",
                        "LAST_UPDATE_USER": g.get('USER_ID'),
                    }
                    primary_key_name = 'MAX_COL_SEQ_ID'
                    ret_data = objdbca.table_update(TFConst.T_NESTVARS_MEMBER_MAX, data_list, primary_key_name)
                    if not ret_data:
                        # 変数ネスト管理の不要レコードの廃止に失敗
                        msg = g.appmsg.get_log_message("BKY-50111", [])
                        raise Exception(msg)

    except Exception as e:
        msg = e
        result = False

    return result, msg


def get_variable_type_id(objdbca, TFConst, str_type):
    """
        variableブロックのtypeからidをreturnする
        ARGS:
        objdbca: DB接クラス DBConnectWs()
            TFConst:
            variable_type: type名称
        RETRUN:
            variable_type_id
    """
    # タイプの指定がない場合はNoneを返却
    if not str_type:
        return None

    # str_typeついている${}を除外
    pattern = r'^\$\{(.*?)\}$'
    match = re.findall(pattern, str_type)
    if match:
        variable_type = match[0]
    else:
        variable_type = str_type

    # list(string)など、()がついている場合は除外し、検索対象とする。list(string) -> list
    pattern = r'^(.*?)\(.*?\)$'
    match = re.findall(pattern, variable_type)
    if match:
        convert_variable_type = match[0]
        where_str = 'WHERE TYPE_NAME = %s OR TYPE_NAME = %s'
        record = objdbca.table_select(TFConst.T_TYPE_MASTER, where_str, [variable_type, convert_variable_type])
    else:
        where_str = 'WHERE TYPE_NAME = %s'
        record = objdbca.table_select(TFConst.T_TYPE_MASTER, where_str, [variable_type])

    # レコードからタイプIDを取得
    if record:
        variable_type_id = record[0].get('TYPE_ID')
    else:
        variable_type_id = None

    return variable_type_id


def create_member_data(objdbca, TFConst, module_vars_link_id, child_vars_id, parent_vars_id, temp_member_data_list, type_data, default_data, type_nest_dict={}, nest_level=0, trg_default_key_list=[]):  # noqa: E501, C901
    """
        メンバー変数登録用レコード作成前のデータ整形
        ARGS:
        objdbca: DB接クラス DBConnectWs()
            variable_type: type名称
        RETRUN:
            variable_type_id
    """
    # 変数定義
    child_member_vars_nest = ''
    module_regist_flag = True  # Module変数紐付に登録するかどうかのフラグ
    assign_seq = 0  # 代入順序
    child_member_vars_key = None
    trg_default_key = None
    org_type_nest_dict = type_nest_dict.copy()  # 実行開始時のtype_nest_dictの値を保管

    # type_dataがlist型の場合、インデックスをkeyにしたdict型に変換する
    if isinstance(type_data, list):
        temp_type_data = {}
        for type_key, type_value in enumerate(type_data):
            temp_type_data[str(type_key)] = type_value
        type_data = temp_type_data

    if isinstance(type_data, dict):
        for type_key, type_value in type_data.items():
            # メンバー変数(key)を特定
            org_type_nest_dict[nest_level] = type_key
            if isinstance(type_value, dict) or isinstance(type_value, list):
                # type_idを取得
                type_id = get_variable_type_id(objdbca, TFConst, type_key)

                # 階層の管理
                nest_level += 1

                # 階層の分だけ本処理をループする
                temp_member_data_list, child_vars_id, parent_vars_id = create_member_data(objdbca, TFConst, module_vars_link_id, child_vars_id, parent_vars_id, temp_member_data_list, type_value, default_data, org_type_nest_dict, nest_level)  # noqa: E501

                # 階層の管理
                nest_level -= 1

            # 階層ではなくなった際にループから抜ける
            else:
                # type_valueがboolean形式の場合、文字列に書き換える
                if type(type_value) == bool:
                    type_value = 'True' if type_value else 'False'

                # type_idを取得
                type_id = get_variable_type_id(objdbca, TFConst, type_value)

            # type_idをchild_vars_type_idに代入
            child_vars_type_id = type_id

            if (type_key or type_key == 0) and child_vars_type_id:
                parent_vars_id = child_vars_id
                for type_nest_key in org_type_nest_dict.values():
                    # タイプ名はメンバー変数に含まないため、type_nest_keyに${}がある場合は除外
                    pattern = r'^\$\{(.*?)\}$'
                    match = re.findall(pattern, type_nest_key)
                    if not match:
                        # type_nest_keyが数字の文字列なら[]で囲む
                        if type_nest_key.isdecimal():
                            if not child_member_vars_nest:
                                child_member_vars_nest = "[{}]".format(str(type_nest_key))
                            else:
                                child_member_vars_nest = child_member_vars_nest + ".[{}]".format(str(type_nest_key))
                            child_member_vars_key = "[{}]".format(str(type_nest_key))
                        # int以外(文字列)の場合
                        else:
                            if not child_member_vars_nest:
                                child_member_vars_nest = str(type_nest_key)
                            else:
                                child_member_vars_nest = child_member_vars_nest + ".{}".format(str(type_nest_key))
                            child_member_vars_key = "{}".format(str(type_nest_key))

                        # デフォルト値を特定するためのキーをセット
                        trg_default_key = type_nest_key

                # Module変数紐付に登録するレコードかどうかを判定
                if nest_level > 0:
                    module_regist_flag = False

                # デフォルト値を特定
                trg_default_key_list = []
                for type_nest in org_type_nest_dict.values():
                    # type_nestに${}がある場合は除外
                    pattern = r'^\$\{(.*?)\}$'
                    match = re.findall(pattern, type_nest)
                    if not match:
                        if type_nest.isdecimal():
                            trg_default_key_list.append(int(type_nest))
                        else:
                            trg_default_key_list.append(str(type_nest))
                child_member_vars_value = None
                child_member_vars_value = search_child_member_vars_value_in_default(objdbca, TFConst, trg_default_key_list, default_data, child_vars_type_id)  # noqa: E501

                # ローカルIDの割り当て
                child_vars_id += 1

                # Module変数から私大繰り返し数を取得
                max_col_seq = count_max_col_seq_by_module(objdbca, TFConst, trg_default_key_list, default_data, child_vars_type_id, module_regist_flag)  # noqa: E501

                # child_member_vars_value(デフォルト値)がboolean形式の場合、文字列に書き換える
                if type(child_member_vars_value) == bool:
                    child_member_vars_value = 'True' if child_member_vars_value else 'False'

                # 格納用データを作成
                set_type_nest_dict = org_type_nest_dict.copy()
                ret_data = {
                    "module_vars_link_id": module_vars_link_id,  # Module-変数紐付のID
                    "child_member_vars_id": child_vars_id,  # 自身のローカルID
                    "parent_member_vars_id": parent_vars_id,  # 親のローカルId
                    "child_member_vars_nest": child_member_vars_nest,  # メンバー変数(フル)
                    "child_member_vars_key": child_member_vars_key,  # メンバー変数のキー
                    "child_member_vars_value": child_member_vars_value,  # デフォルト値
                    "nest_level": nest_level,  # 階層
                    "trg_default_key": trg_default_key,  # デフォルト値のキー
                    "child_vars_type_id": child_vars_type_id,  # タイプId
                    "assign_seq": assign_seq,  # 代入順序
                    "module_regist_flag": module_regist_flag,  # Module変数紐付に代入するかどうかのフラグ
                    "type_nest_dict": set_type_nest_dict,  # 自身までキー/インデックス一覧
                    "max_col_seq": max_col_seq  # 最大繰り返し数
                }

                # 代入順序をカウントアップ
                assign_seq += 1

                # 返却値に格納
                temp_member_data_list.append(ret_data)

            elif (not type_key == "" or type_key == 0) and child_vars_type_id == "":
                trg_index = int(child_vars_id) - 1
                temp_member_data_list[trg_index]["nest_level"] = nest_level
                temp_member_data_list[trg_index]["assign_seq"] = assign_seq

                # 代入順序をカウントアップ
                assign_seq += 1

            # メンバー変数(フル)をリセット
            child_member_vars_nest = ''

    else:
        # タイプの特定
        child_vars_type_id = None
        child_member_vars_value = None
        # type_dataついている${}を除外
        pattern = r'^\$\{(.*?)\}$'
        match = re.findall(pattern, type_data)
        if match:
            # type情報を取得
            convert_type_name = match[0]
            child_vars_type_id = get_variable_type_id(objdbca, TFConst, convert_type_name)
            type_info = get_type_info(objdbca, TFConst, child_vars_type_id)
            encode_flag = type_info.get('ENCODE_FLAG')
            member_vars_flag = type_info.get('MEMBER_VARS_FLAG')
            # 取得したtype情報からデフォルト値を設定
            if str(encode_flag) == '1':
                child_member_vars_value = encode_hcl(default_data)
            elif str(member_vars_flag) == '1':
                child_member_vars_value = None

        # child_member_vars_valueeがboolean形式の場合、文字列に書き換える
        if type(child_member_vars_value) == bool:
            child_member_vars_value = 'True' if child_member_vars_value else 'False'

        # 空文字を固定で設定する
        child_member_vars_key = ''
        trg_default_key = ''

        # Module変数から最大繰り返し数を取得
        max_col_seq = count_max_col_seq_by_module(objdbca, TFConst, trg_default_key_list, default_data, child_vars_type_id, module_regist_flag)

        # 格納用データを作成
        set_type_nest_dict = org_type_nest_dict.copy()
        ret_data = {
            "module_vars_link_id": module_vars_link_id,  # Module-変数紐付のID
            "child_member_vars_id": child_vars_id,  # 自身のローカルID
            "parent_member_vars_id": parent_vars_id,  # 親のローカルId
            "child_member_vars_nest": child_member_vars_nest,  # メンバー変数(フル)
            "child_member_vars_key": child_member_vars_key,  # メンバー変数のキー
            "child_member_vars_value": child_member_vars_value,  # デフォルト値
            "nest_level": int(nest_level) - 1,  # 階層
            "trg_default_key": trg_default_key,  # デフォルト値のキー
            "child_vars_type_id": child_vars_type_id,  # タイプId
            "assign_seq": assign_seq,  # 代入順序
            "module_regist_flag": module_regist_flag,  # Module変数紐付に代入するかどうかのフラグ
            "type_nest_dict": set_type_nest_dict,  # 自身までキー/インデックス一覧
            "max_col_seq": max_col_seq  # 最大繰り返し数
        }

        # 返却値に格納
        temp_member_data_list.append(ret_data)

    # return temp_member_data_list, child_vars_id, parent_vars_id, org_type_nest_dict
    return temp_member_data_list, child_vars_id, parent_vars_id


def create_member_data_for_regist(objdbca, TFConst, temp_member_data_list):  # noqa: C901
    """
        メンバー変数をレコードに登録するための配列に整形して返却
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        variable_type: type名称
        RETRUN:
            default
    """
    member_data_list = []

    # ネストをすべて取得し、重複を削除。
    nest_level_list = [x['nest_level'] for x in temp_member_data_list]
    nest_level_list = sorted(set(nest_level_list))

    # ネスト番号を振り直し
    new_nest_level = 0
    copy_member_data_list = temp_member_data_list.copy()
    for nest_level_key in nest_level_list:
        trg_flag = False
        for index, member_data in enumerate(temp_member_data_list):
            if nest_level_key == temp_member_data_list[index].get('nest_level'):
                copy_member_data_list[index]['nest_level'] = new_nest_level
                trg_flag = True
        if trg_flag:
            new_nest_level += 1
    temp_member_data_list = copy_member_data_list.copy()

    # nest_levelとassign_seqをもとにtemp_member_data_listを昇順で並び替え
    temp_member_data_list = sorted(temp_member_data_list, key=lambda x: (x['nest_level'], x['assign_seq']))

    # module_vars_link_idがあるものだけを別のlistに格納する
    temp_member_data_list_2 = []
    for member_data in temp_member_data_list:
        if member_data.get('module_vars_link_id'):
            temp_member_data_list_2.append(member_data)
    temp_member_data_list = temp_member_data_list_2.copy()

    # ローカルIDを仮のIDに割り振る
    for index, member_data in enumerate(temp_member_data_list):
        # 既存レコードの検索
        search_data = {
            "PARENT_VARS_ID": member_data.get('module_vars_link_id'),  # Module-変数紐付ID
            "CHILD_MEMBER_VARS_KEY": member_data.get('child_member_vars_key'),  # メンバー変数
            "CHILD_MEMBER_VARS_NEST": member_data.get('child_member_vars_nest'),  # メンバー変数(フルパス)
            "ARRAY_NEST_LEVEL": member_data.get('nest_level'),  # 階層
            "CHILD_VARS_TYPE_ID": member_data.get('child_vars_type_id'),  # タイプID
            "ASSIGN_SEQ": member_data.get('assign_seq'),  # 代入順序
        }
        duplicate_member_vars = get_member_vars_by_member_data(objdbca, TFConst, search_data)

        if not duplicate_member_vars:
            if not member_data.get('module_regist_flag'):
                # 既存レコードがない場合、child_member_vars_idに登録用のIDを割り振る
                temp_member_data_list[index]['child_member_vars_id'] = str(uuid.uuid4())
        else:
            # 既存レコードがある場合、各対応フラグを格納する
            if not str(duplicate_member_vars.get('CHILD_MEMBER_VARS_VALUE')) == str(member_data.get('child_member_vars_value')):
                # 具体値に差分がある場合、更新フラグを立てる
                temp_member_data_list[index]['update_flag'] = "1"
            elif not str(duplicate_member_vars.get('CHILD_VARS_TYPE_ID')) == str(member_data.get('child_vars_type_id')):
                # タイプに差分がある場合、更新フラグを立てる
                temp_member_data_list[index]['update_flag'] = "1"
            elif str(duplicate_member_vars.get('DISUSE_FLAG')) == "1":
                # 具体値に差分がなく、廃止状態なら復活フラグを立てる
                temp_member_data_list[index]['restore_flag'] = "1"
            else:
                # どれにも該当しない場合はスキップフラグを立てる
                temp_member_data_list[index]['skip_flag'] = "1"

            # child_member_vars_idをセット
            temp_member_data_list[index]['child_member_vars_id'] = duplicate_member_vars.get('CHILD_MEMBER_VARS_ID')

    # 親変数を検索
    for index, member_data in enumerate(temp_member_data_list):
        if not member_data.get('module_regist_flag'):
            # 一番後ろのキーを削除して親を探す
            parent_member_data = member_data.get('type_nest_dict').copy()
            if isinstance(parent_member_data, dict) and len(parent_member_data) > 0:
                # 削除対象のキーを特定して削除
                parent_member_key_list = []
                for key in parent_member_data.keys():
                    parent_member_key_list.append(key)
                delete_key = parent_member_key_list[-1]
                parent_member_data.pop(delete_key)

            # メンバー変数は2つ前までキーを削除する
            type_info = get_type_info(objdbca, TFConst, member_data.get('child_vars_type_id'))
            if member_data.get('child_vars_type_id') and str(type_info.get('MEMBER_VARS_FLAG')) == "1":
                if len(parent_member_data) > 0:
                    # 削除対象のキーを特定して削除
                    parent_member_key_list = []
                    for key in parent_member_data.keys():
                        parent_member_key_list.append(key)
                    delete_key = parent_member_key_list[-1]
                    parent_member_data.pop(delete_key)

            # ネストレベルからparent_member_vars_idを設定
            if member_data.get('nest_level'):
                if not str(member_data.get('nest_level')) == "1":
                    parent_dict_index = [x['type_nest_dict'] for x in temp_member_data_list]
                    parent_member_data_json = json.dumps(parent_member_data)
                    target_key = None
                    for parent_index, type_nest_data in enumerate(parent_dict_index):
                        type_nest_data_json = json.dumps(type_nest_data)
                        if parent_member_data_json == type_nest_data_json:
                            target_key = parent_index
                        if target_key:
                            break

                    if target_key is None:
                        member_data['parent_member_vars_id'] = None
                    else:
                        member_data['parent_member_vars_id'] = temp_member_data_list[target_key]['child_member_vars_id']

                else:
                    # ネストが1であれば親がいないので探さない
                    member_data['parent_member_vars_id'] = None

            # 変数ネスト管理が存在するか検索
            registered_max_col_data = get_regist_max_module_col_data(objdbca, TFConst, member_data.get('child_member_vars_id'))
            if registered_max_col_data.get('is_regist') is True and registered_max_col_data.get('is_system') is False:
                temp_member_data_list[index]['max_col_seq'] = registered_max_col_data.get('max_col_seq')

    member_data_list = temp_member_data_list.copy()

    return member_data_list


def part_member_data_for_regist(objdbca, TFConst, member_data_list):  # noqa: C901
    """
        メンバー変数レコードの処理を分類ごとに振り分ける
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        TFConst:
        member_data_list:
        RETRUN:
            regist_member_data
    """
    regist_member_data = {
        "regist": [],
        "update": [],
        "skip": [],
        "restore": []
    }
    temp_member_data_list = member_data_list.copy()

    # ネストをすべて取得し、重複を削除。
    nest_level_list = [x['nest_level'] for x in temp_member_data_list]
    nest_level_list = sorted(set(nest_level_list))

    # ネスト番号を振り直し
    new_nest_level = 0
    copy_member_data_list = temp_member_data_list.copy()
    for nest_level_key in nest_level_list:
        trg_flag = False
        for index, member_data in enumerate(temp_member_data_list):
            if nest_level_key == temp_member_data_list[index].get('nest_level'):
                copy_member_data_list[index]['nest_level'] = new_nest_level
                trg_flag = True
        if trg_flag:
            new_nest_level += 1
    temp_member_data_list = copy_member_data_list.copy()

    # nest_levelとassign_seqをもとにtemp_member_data_listを昇順で並び替え
    temp_member_data_list = sorted(temp_member_data_list, key=lambda x: (x['nest_level'], x['assign_seq']))

    # ローカルIDを仮のIDに割り振る
    for index, member_data in enumerate(temp_member_data_list):
        # 既存レコードの検索
        search_data = {
            "PARENT_VARS_ID": member_data.get('module_vars_link_id'),  # Module-変数紐付ID
            "CHILD_MEMBER_VARS_KEY": member_data.get('child_member_vars_key'),  # メンバー変数
            "CHILD_MEMBER_VARS_NEST": member_data.get('child_member_vars_nest'),  # メンバー変数(フルパス)
            "ARRAY_NEST_LEVEL": member_data.get('nest_level'),  # 階層
            "CHILD_VARS_TYPE_ID": member_data.get('child_vars_type_id'),  # タイプID
            "ASSIGN_SEQ": member_data.get('assign_seq'),  # 代入順序
        }
        duplicate_member_vars = get_member_vars_by_member_data(objdbca, TFConst, search_data)

        if not duplicate_member_vars:
            if not member_data.get('module_regist_flag'):
                # 既存レコードがない場合、child_member_vars_idに登録用のIDを割り振る
                temp_member_data_list[index]['child_member_vars_id'] = str(uuid.uuid4())
        else:
            # 既存レコードがある場合、各対応フラグを格納する
            if not str(duplicate_member_vars.get('CHILD_MEMBER_VARS_VALUE')) == str(member_data.get('child_member_vars_value')):
                # 具体値に差分がある場合、更新フラグを立てる
                temp_member_data_list[index]['update_flag'] = "1"
            elif not str(duplicate_member_vars.get('PARENT_MEMBER_VARS_ID')) == str(member_data.get('parent_member_vars_id')):
                # 親メンバー変数IDに更新がある場合、更新フラグを立てる
                temp_member_data_list[index]['update_flag'] = "1"
            elif not str(duplicate_member_vars.get('CHILD_VARS_TYPE_ID')) == str(member_data.get('child_vars_type_id')):
                # タイプに差分がある場合、更新フラグを立てる
                temp_member_data_list[index]['update_flag'] = "1"
            elif str(duplicate_member_vars.get('DISUSE_FLAG')) == "1":
                # 具体値に差分がなく、廃止状態なら復活フラグを立てる
                temp_member_data_list[index]['restore_flag'] = "1"
            else:
                # どれにも該当しない場合はスキップフラグを立てる
                temp_member_data_list[index]['skip_flag'] = "1"

            # child_member_vars_idをセット
            temp_member_data_list[index]['child_member_vars_id'] = duplicate_member_vars.get('CHILD_MEMBER_VARS_ID')

    # 親変数を検索
    for index, member_data in enumerate(temp_member_data_list):
        if not member_data.get('module_regist_flag'):
            # 一番後ろのキーを削除して親を探す
            parent_member_data = member_data.get('type_nest_dict').copy()
            if isinstance(parent_member_data, dict) and len(parent_member_data) > 0:
                # 削除対象のキーを特定して削除
                parent_member_key_list = []
                for key in parent_member_data.keys():
                    parent_member_key_list.append(key)
                delete_key = parent_member_key_list[-1]
                parent_member_data.pop(delete_key)

            # メンバー変数は2つ前までキーを削除する
            type_info = get_type_info(objdbca, TFConst, member_data.get('child_vars_type_id'))
            if member_data.get('child_vars_type_id') and str(type_info.get('MEMBER_VARS_FLAG')) == "1":
                if len(parent_member_data) > 0:
                    # 削除対象のキーを特定して削除
                    parent_member_key_list = []
                    for key in parent_member_data.keys():
                        parent_member_key_list.append(key)
                    delete_key = parent_member_key_list[-1]
                    parent_member_data.pop(delete_key)

            # ネストレベルからparent_member_vars_idを設定
            if member_data.get('nest_level'):
                if not str(member_data.get('nest_level')) == "1":
                    parent_dict_index = [x['type_nest_dict'] for x in temp_member_data_list]
                    # parent_member_dataと構造が一致している対象のkeyを取得
                    parent_member_data_json = json.dumps(parent_member_data)
                    target_key = None
                    for parent_index, type_nest_data in enumerate(parent_dict_index):
                        type_nest_data_json = json.dumps(type_nest_data)
                        if parent_member_data_json == type_nest_data_json:
                            target_key = parent_index
                        if target_key:
                            break

                    if target_key is None:
                        member_data['parent_member_vars_id'] = None
                    else:
                        member_data['parent_member_vars_id'] = temp_member_data_list[target_key]['child_member_vars_id']

                else:
                    # ネストが1であれば親がいないので探さない
                    member_data['parent_member_vars_id'] = None

            # type_nest_dataがあれば、各種処理に割り当て
            # デフォルト値はdict/listの可能性があるため、json形式に変換する。
            child_member_vars_value = member_data.get('child_member_vars_value')
            if isinstance(child_member_vars_value, dict) or isinstance(child_member_vars_value, list):
                child_member_vars_value = json.dumps(child_member_vars_value)

            if member_data.get('type_nest_dict'):
                regist_data = {
                    "CHILD_MEMBER_VARS_ID": member_data.get('child_member_vars_id'),  # メンバー変数ID
                    "PARENT_VARS_ID": member_data.get('module_vars_link_id'),  # Module-変数紐付ID
                    "PARENT_MEMBER_VARS_ID": member_data.get('parent_member_vars_id'),  # 親のメンバー変数ID
                    "CHILD_MEMBER_VARS_KEY": member_data.get('child_member_vars_key'),  # メンバー変数
                    "CHILD_MEMBER_VARS_NEST": member_data.get('child_member_vars_nest'),  # メンバー変数(フル)
                    "CHILD_MEMBER_VARS_VALUE": child_member_vars_value,  # デフォルト値
                    "ARRAY_NEST_LEVEL": member_data.get('nest_level'),  # 階層
                    "CHILD_VARS_TYPE_ID": member_data.get('child_vars_type_id'),  # タイプID
                    "ASSIGN_SEQ": member_data.get('assign_seq'),  # 代入順序
                    "MAX_COL_SEQ": member_data.get('max_col_seq'),  # 最大繰り返し数
                    "DISUSE_FLAG": "0",
                    "LAST_UPDATE_USER": g.get('USER_ID'),
                }

                # 各種処理に割り当て
                if member_data.get('regist_flag'):
                    regist_member_data['regist'].append(regist_data.copy())
                elif member_data.get('update_flag'):
                    regist_member_data['update'].append(regist_data.copy())
                elif member_data.get('restore_flag'):
                    regist_member_data['restore'].append(regist_data.copy())
                elif member_data.get('skip_flag'):
                    regist_member_data['skip'].append(regist_data.copy())
                else:
                    # フラグがない場合は「登録」にセット
                    regist_member_data['regist'].append(regist_data.copy())

    return regist_member_data


def search_child_member_vars_value_in_default(objdbca, TFConst, trg_default_key_list, default_data, type_id):
    """
        デフォルト値を取得する
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        variable_type: type名称
        RETRUN:
            default
    """
    # 変数定義
    default = None
    temp_default_data = default_data.copy()
    temp_trg_default_key_list = trg_default_key_list.copy()

    # temp_default_dataがlist型の場合、インデックスをkeyにしたdict型に変換する
    if isinstance(temp_default_data, list):
        dict_temp_default_data = {}
        for key, value in enumerate(temp_default_data):
            dict_temp_default_data[str(key)] = value
        temp_default_data = dict_temp_default_data.copy()

    # デフォルト値を特定
    for default_key in temp_trg_default_key_list:
        if isinstance(temp_default_data, dict):
            default = temp_default_data.get(str(default_key))
        else:
            default = None

        # defaultがlist型の場合、インデックスをkeyにしたdict型に変換したものをtemp_default_dataにセットする。
        if isinstance(default, list):
            dict_default = {}
            for key, value in enumerate(default):
                dict_default[str(key)] = value
            temp_default_data = dict_default.copy()
        else:
            temp_default_data = default

    # HCLにエンコードするフラグが立っていたらエンコード
    type_info = get_type_info(objdbca, TFConst, type_id)
    encode_flag = type_info.get('ENCODE_FLAG')
    member_vars_flag = type_info.get('MEMBER_VARS_FLAG')
    if str(encode_flag) == '1':
        if isinstance(default, dict) or isinstance(default, list):
            default = encode_hcl(default)
    elif str(member_vars_flag) == '1':
        default = None

    return default


def get_type_info(objdbca, TFConst, type_id):
    """
        タイプの情報を取得する
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        type_id: typeID
        RETRUN:
            type_info
    """
    type_info = {}
    where_str = 'WHERE TYPE_ID = %s'
    ret = objdbca.table_select(TFConst.T_TYPE_MASTER, where_str, [str(type_id)])
    if ret:
        type_info = ret[0]

    return type_info


def encode_hcl(data):
    """
        HCL形式にエンコードする
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        type_id: typeID
        RETRUN:
            type_info
    """
    res = None
    if isinstance(data, dict) or isinstance(data, list):
        res_json = json.dumps(data, ensure_ascii=False)
        pattern = r'\"(.*?)\"\:(.*?)'
        replacement = r'"\1" =\2'
        res = re.sub(pattern, replacement, res_json)

    return res


def decode_hcl(data):
    """
        HCL形式から配列にデコードする
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        type_id: typeID
        RETRUN:
            res(dict or list)
    """
    res = None
    if not isinstance(data, dict) or not isinstance(data, list):
        pattern = r'\"(.*?)\"\ = \"(.*?)\"'
        replacement = r'"\1": "\2"'
        res = re.sub(pattern, replacement, data)
        res = json.loads(res)

    return res


def count_max_col_seq_by_module(objdbca, TFConst, trg_default_key_list, default_data, type_id, module_regist_flag=False):
    """
        最大繰り返し数をModule変数から取得する
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        trg_default_key_list:
        default_data:
        type_id: typeID
        module_regist_flag:
        RETRUN:
            max_col_seq(int)
    """
    # 変数定義
    default = None
    max_col_seq = 0

    # 変数ネスト管理対象かを判定
    type_info = get_type_info(objdbca, TFConst, type_id)
    if type_info:
        member_vars_flag = type_info.get('MEMBER_VARS_FLAG')
        assign_seq_flag = type_info.get('ASSIGN_SEQ_FLAG')
        encode_flag = type_info.get('ENCODE_FLAG')

        if module_regist_flag is True and str(member_vars_flag) == '1' and str(assign_seq_flag) == '1' and str(encode_flag) == '0':
            # dict/listの場合は要素数をカウントする。それ以外は1とする。
            if isinstance(default_data, dict) or isinstance(default_data, list):
                max_col_seq = len(default_data)
            else:
                max_col_seq = 1

        elif str(member_vars_flag) == '1' and str(assign_seq_flag) == '1' and str(encode_flag) == '0':
            # default_dataがlist型の場合、インデックスをkeyにしたdict型に変換する
            if isinstance(default_data, list):
                dict_default_data = {}
                for key, value in enumerate(default_data):
                    dict_default_data[str(key)] = value
                default_data = dict_default_data.copy()

            # キーの一覧をループしてデフォルト値を確認
            temp_default_data = default_data.copy()
            for default_key in trg_default_key_list:
                if isinstance(temp_default_data, dict):
                    default = temp_default_data.get(str(default_key))
                else:
                    default = None
                temp_default_data = default

                # dict/listの場合は要素数をカウントする。それ以外は1とする。
                if isinstance(default, dict) or isinstance(default, list):
                    max_col_seq = len(default)
                else:
                    max_col_seq = 1

    return max_col_seq


def get_regist_max_module_col_data(objdbca, TFConst, module_vars_link_id):
    """
        変数ネスト管理情報の取得(Module-変数紐付IDのレコードが登録済みかどうか/最大更新者/最大繰り返し数)
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        TFConst:
        module_vars_link_id:
        RETRUN:
            max_col_data
    """
    max_col_data = {
        "is_regist": False,  # 登録済みフラグ
        "is_system": True,  # 最終更新者がバックヤードシステム
        "max_col_seq": 0,
        "MAX_COL_SEQ_ID": None,  # UUID
        "DISUSE_FLAG": None  # 廃止フラグ
    }

    where_str = 'WHERE VARS_ID = %s AND MEMBER_VARS_ID IS NULL'
    record = objdbca.table_select(TFConst.T_NESTVARS_MEMBER_MAX, where_str, [module_vars_link_id])
    if record:
        max_col_data["is_regist"] = True
        if not str(record[0].get('LAST_UPDATE_USER')) == str(g.get('USER_ID')):
            max_col_data["is_system"] = False

        max_col_data["max_col_seq"] = record[0].get('MAX_COL_SEQ')
        max_col_data["MAX_COL_SEQ_ID"] = record[0].get('MAX_COL_SEQ_ID')
        max_col_data["DISUSE_FLAG"] = record[0].get('DISUSE_FLAG')

    return max_col_data


def get_regist_max_member_col_data(objdbca, TFConst, module_vars_link_id):
    """
        変数ネスト管理情報の取得(メンバー変数が登録済みかどうか/最大更新者/最大繰り返し数)
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        TFConst:
        module_vars_link_id:
        RETRUN:
            max_col_data
    """
    max_col_data = {
        "is_regist": False,  # 登録済みフラグ
        "is_system": True,  # 最終更新者がバックヤードシステム
        "max_col_seq": 0,
        "MAX_COL_SEQ_ID": None,  # UUID
        "DISUSE_FLAG": None  # 廃止フラグ
    }

    where_str = 'WHERE MEMBER_VARS_ID = %s'
    record = objdbca.table_select(TFConst.T_NESTVARS_MEMBER_MAX, where_str, [module_vars_link_id])
    if record:
        max_col_data["is_regist"] = True
        if not str(record[0].get('LAST_UPDATE_USER')) == str(g.get('USER_ID')):
            max_col_data["is_system"] = False

        max_col_data["max_col_seq"] = record[0].get('MAX_COL_SEQ')
        max_col_data["MAX_COL_SEQ_ID"] = record[0].get('MAX_COL_SEQ_ID')
        max_col_data["DISUSE_FLAG"] = record[0].get('DISUSE_FLAG')

    return max_col_data


def regist_max_col(objdbca, TFConst, module_vars_link_id, member_vars_id, max_col_seq):
    """
        変数ネスト管理にレコードを登録する
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        TFConst:
        module_vars_link_id:
        member_vars_id:
        max_col_seq
        RETRUN:
            boolean
    """
    result = True
    data_list = {
        "VARS_ID": module_vars_link_id,
        "MEMBER_VARS_ID": member_vars_id,
        "MAX_COL_SEQ": max_col_seq,
        "DISUSE_FLAG": "0",
        "LAST_UPDATE_USER": g.get('USER_ID'),
    }
    primary_key_name = 'MAX_COL_SEQ_ID'
    ret_data = objdbca.table_insert(TFConst.T_NESTVARS_MEMBER_MAX, data_list, primary_key_name)
    if not ret_data:
        result = False

    return result


def update_max_col(objdbca, TFConst, max_col_seq_id, max_col_seq):
    """
        変数ネスト管理にレコードを更新する
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        TFConst:
        max_col_seq_id:
        max_col_seq
        RETRUN:
            boolean
    """
    result = True
    data_list = {
        "MAX_COL_SEQ_ID": max_col_seq_id,
        "MAX_COL_SEQ": int(max_col_seq),
        "DISUSE_FLAG": "0",
        "LAST_UPDATE_USER": g.get('USER_ID'),
    }
    primary_key_name = 'MAX_COL_SEQ_ID'
    ret_data = objdbca.table_update(TFConst.T_NESTVARS_MEMBER_MAX, data_list, primary_key_name)
    if not ret_data:
        result = False

    return result


def discard_max_col(objdbca, TFConst, max_col_seq_id):
    """
        変数ネスト管理にレコードを廃止する
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        TFConst:
        max_col_seq_id:
        RETRUN:
            boolean
    """
    result = True
    data_list = {
        "MAX_COL_SEQ_ID": max_col_seq_id,
        "DISUSE_FLAG": "1",
        "LAST_UPDATE_USER": g.get('USER_ID'),
    }
    primary_key_name = 'MAX_COL_SEQ_ID'
    ret_data = objdbca.table_update(TFConst.T_NESTVARS_MEMBER_MAX, data_list, primary_key_name)
    if not ret_data:
        result = False

    return result


def adjust_type_data_by_max_col_seq(objdbca, TFConst, type_data, temp_member_data_list):
    """
        type_dataを最大繰り返し数を反映させたものに変換し返却
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        TFConst:
        type_data::
        temp_member_data_list:
        RETRUN:
            boolean
    """
    member_vars_data = {}

    for member_data in temp_member_data_list:
        if member_data.get('max_col_seq'):
            if int(member_data.get('max_col_seq')) > 0 and member_data.get('child_vars_type_id'):
                trg_max_col_seq = member_data.get('max_col_seq')
                type_id = member_data.get('child_vars_type_id')
                type_info = get_type_info(objdbca, TFConst, type_id)
                if type_info:
                    member_vars_flag = type_info.get('MEMBER_VARS_FLAG')
                    assign_seq_flag = type_info.get('ASSIGN_SEQ_FLAG')
                    encode_flag = type_info.get('ENCODE_FLAG')
                    if str(member_vars_flag) == "1" and str(assign_seq_flag) == "1" and str(encode_flag) == "0":
                        trg_default_key_data = member_data.get('type_nest_dict')
                        temp_type_data = type_data.copy()
                        for key, value in trg_default_key_data.items():
                            if isinstance(temp_type_data, list):
                                if value.isdecimal:
                                    if len(temp_type_data) >= int(value):
                                        temp_type_data = temp_type_data[int(value)]

                            if isinstance(temp_type_data, dict):
                                if temp_type_data.get(value):
                                    temp_type_data = temp_type_data[value]

                        # 変数ネスト管理対象
                        trg_nest_type_data = temp_type_data
                        if member_data.get('module_regist_flag') is True:
                            registered_max_col_data = get_regist_max_module_col_data(objdbca, TFConst, member_data.get('module_vars_link_id'))
                            if registered_max_col_data.get('is_regist') is True and registered_max_col_data.get('is_system') is False:
                                trg_max_col_seq = registered_max_col_data.get('max_col_seq')

                        else:
                            registered_max_col_data = get_regist_max_member_col_data(objdbca, TFConst, member_data.get('child_member_vars_id'))
                            # 変数ネスト管理に対象レコードが存在し、最終更新者がバックヤードユーザではない場合は最大繰り返し数を取得する
                            if registered_max_col_data.get('is_regist') is True and registered_max_col_data.get('is_system') is False:
                                trg_max_col_seq = registered_max_col_data.get('max_col_seq')

                        # 変数ネスト管理対象の現在の最大繰り返し数
                        nest_type_count = 0
                        # if isinstance(trg_nest_type_data, dict) or isinstance(trg_nest_type_data, list):
                        if isinstance(trg_nest_type_data, list):
                            nest_type_count = len(trg_nest_type_data)

                        # 0番目が変数ネスト管理対象
                        trg_nest_type_data_0 = ""
                        # if isinstance(trg_nest_type_data, dict) or isinstance(trg_nest_type_data, list):
                        if isinstance(trg_nest_type_data, list):
                            trg_nest_type_data_0 = trg_nest_type_data[0]

                        # 変更後の最大繰り返し数ともともとの最大繰り返し数の差分
                        max_col_seq_diff = int(trg_max_col_seq) - int(nest_type_count)

                        # 返却するデータの原型を作成
                        member_vars_data = type_data.copy()

                        # マップ作成
                        map_data = trg_default_key_data

                        # 最大繰り返し数を調整
                        if not int(max_col_seq_diff) == 0 or member_data.get('force_max_col_seq_flag'):
                            member_vars_data = generate_member_vars_type_data(objdbca, TFConst, member_vars_data, trg_max_col_seq, trg_nest_type_data_0, type_info, map_data)  # noqa: E501

    if not member_vars_data:
        member_vars_data = type_data.copy()

    return member_vars_data


def get_member_vars_by_member_data(objdbca, TFConst, search_data):
    """
        対象のメンバー変数を取得する
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        TFConst:
        search_data:
        RETRUN:
            return_data
    """
    return_data = None

    parent_vars_id = search_data.get('PARENT_VARS_ID')
    child_member_vars_nest = search_data.get('CHILD_MEMBER_VARS_NEST')
    child_member_vars_key = search_data.get('CHILD_MEMBER_VARS_KEY')
    child_vars_type_id = search_data.get('CHILD_VARS_TYPE_ID')
    array_nest_level = search_data.get('ARRAY_NEST_LEVEL')
    assign_seq = search_data.get('ASSIGN_SEQ')
    where_str = 'WHERE PARENT_VARS_ID <=> %s \
                AND CHILD_MEMBER_VARS_NEST <=> %s \
                AND CHILD_MEMBER_VARS_KEY <=> %s \
                AND (CHILD_VARS_TYPE_ID <=> %s OR CHILD_VARS_TYPE_ID IS NULL) \
                AND ARRAY_NEST_LEVEL <=> %s \
                AND ASSIGN_SEQ <=> %s \
                ORDER BY LAST_UPDATE_TIMESTAMP ASC'
    ret = objdbca.table_select(TFConst.T_VAR_MEMBER, where_str, [parent_vars_id, child_member_vars_nest, child_member_vars_key, child_vars_type_id, array_nest_level, assign_seq])  # noqa: E501
    record_count = len(ret)

    # レコードが1つなら対象をreturnする
    if record_count == 1:
        return_data = ret[0]

    # 複数のレコードがある場合優先順位に従って対象のレコードを特定する
    if record_count > 1:
        # 優先順位
        # 1. DISUSE_FLAGが0の対象
        # 2. 1が複数あれば、最終更新日が新しいものが対象
        disuse_flag_0 = None
        disuse_flag_1 = None
        for record in ret:
            if str(record.get('DISUSE_FLAG')) == "0":
                disuse_flag_0 = record
            else:
                disuse_flag_1 = record

            if disuse_flag_0:
                return_data = disuse_flag_0
            else:
                return_data = disuse_flag_1

    return return_data


def generate_member_vars_type_data(objdbca, TFConst, member_vars_data, trg_max_col_seq, trg_nest_type_data, type_info, map_data):
    """
        最大繰り返し数を適用させたtypeを返却する
        ARGS:
        objdbca: DB接クラス DBConnectWs()
        TFConst:
        RETRUN:
            return_data
    """
    return_data = {}
    member_vars_key = map_data[len(map_data) - 1]

    # map_dataのkeyが一番後ろの対象を削除
    temp_list = []
    for key in map_data.keys():
        temp_list.append(key)
    delete_key = temp_list[-1]
    map_data.pop(delete_key)

    if not map_data:
        temp_list = []
        # マップデータが空の場合
        for i in range(int(trg_max_col_seq)):
            temp_list.append(trg_nest_type_data)

        # 仮配列と返却用配列をマージ
        return_data[member_vars_key] = temp_list

    else:
        # マップデータがある場合
        # メンバー変数を設定・具体値を代入
        if str(type_info.get('ENCODE_FLAG')) == "1":
            trg_nest_type_data = decode_hcl(trg_nest_type_data)

        ref = {}
        temp_list = []

        for i in range(int(trg_max_col_seq)):
            temp_list.append(trg_nest_type_data)

        ref[member_vars_key] = temp_list

        # map_dataをlist型に変換する
        map_data_list = []
        for index, key in map_data.items():
            map_data_list.append(key)

        # map_dataをもとにtemp_dictを生成する
        temp_dict = {}

        def create_map_data_dict(map_data_list, ref, temp_dict, n=0):
            if n < len(map_data) - 1:
                temp_dict[map_data[n]] = {}
                create_map_data_dict(list, ref, temp_dict[map_data[n]], n + 1)
            else:
                temp_dict[map_data[n]] = ref

        create_map_data_dict(map_data, ref, temp_dict)

        # 仮配列と返却用配列をマージ
        try:
            return_data = deepmerge(temp_dict, member_vars_data)
        except Exception:
            return_data = temp_dict

    return return_data
