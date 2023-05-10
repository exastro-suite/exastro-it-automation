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
from common_libs.terraform_driver.common.Hcl2Json import HCL2JSONParse
from common_libs.terraform_driver.common.member_vars_function import *  # noqa: F403
import os
import re
# import json


def has_changes_related_tables(objdbca, proc_loaded_row_id):
    """
        関連データベースが更新されバックヤード処理が必要か判定
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            proc_loaded_row_id: 対象の識別ID
        RETRUN:
            boolean
    """
    where_str = " WHERE  ROW_ID = %s AND (LOADED_FLG is NULL OR LOADED_FLG <> '1')"
    bind_value_list = [proc_loaded_row_id]
    not_loaded_count = objdbca.table_count("T_COMN_PROC_LOADED_LIST", where_str, bind_value_list)

    return (not_loaded_count > 0)


def get_variable_block(file_path):
    """
        tfファイルからvariableブロックを抽出した結果を返却する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            proc_loaded_row_id: 対象の識別ID
        RETRUN:
            result(dict)
    """
    hcl2json = HCL2JSONParse(file_path)
    hcl2json.executeParse()
    result = hcl2json.getParseResult()

    return result


def set_module_vars_link(objdbca, TFConst):  # noqa: C901
    """
        Module素材集に登録されたtfファイルからvariableブロックが記載されたものをModule-変数紐付テーブルに対し更新する
        また階層のある変数についてはメンバー変数管理テーブルに対しての処理も行う
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
        exist_member_vars_list = []
        base_path = os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
        variable_block_data = {}  # すべてのModule素材に記載されているvariableブロックを格納

        # Module素材集テーブルからレコードを取得
        where_str = 'WHERE DISUSE_FLAG = %s'
        t_module_records = objdbca.table_select(TFConst.T_MODULE, where_str, [0])

        # 登録されているModule素材集のファイルからvariableブロックを抽出
        for record in t_module_records:
            module_matter_id = record.get('MODULE_MATTER_ID')
            module_matter_file = record.get('MODULE_MATTER_FILE')

            # ファイルが「.tf」形式ではない場合はスキップ
            pattern = r'\.tf$'
            match = re.findall(pattern, module_matter_file)
            if not match:
                continue

            file_path = base_path + TFConst.DIR_MODULE + '/' + module_matter_id + '/' + module_matter_file
            parse_result = get_variable_block(file_path)
            if parse_result.get('res'):
                variables = parse_result.get('variables')
                variable_block_data[module_matter_id] = variables
            else:
                # 解析処理に失敗した場合は強制終了
                raise Exception(parse_result.get('error_msg'))

        # Module変数紐付テーブルからレコードをすべて取得（廃止含め）
        where_str = ''
        t_mod_var_link_records = objdbca.table_select(TFConst.T_MODULE_VAR, where_str, [])

        # トランザクション開始
        objdbca.db_transaction_start()

        # 不要レコードを特定するため、利用中レコードを格納するlist
        active_record_list = []

        # variable_block_dataをループし、Module-変数紐付テーブルにレコードの「登録」または「廃止」を実施する
        for module_matter_id, variable_list in variable_block_data.items():
            for variable_data in variable_list:
                variable_name = variable_data.get('variable')
                variable_type = variable_data.get('type_str')
                variable_type_id = get_variable_type_id(objdbca, TFConst, variable_type)  # noqa: F405
                default = variable_data.get('default')
                if isinstance(default, dict) or isinstance(default, list):
                    default = encode_hcl(default)  # noqa: F405

                # Module変数紐付テーブルのレコードから、登録値が一致する対象があるか確認
                exist_flag = False
                exist_record_id = None
                exist_record_disuse_flag = None
                for record in t_mod_var_link_records:
                    r_module_vars_link_id = record.get('MODULE_VARS_LINK_ID')
                    r_module_matter_id = record.get('MODULE_MATTER_ID')
                    r_variable_name = record.get('VARS_NAME')
                    r_variable_type = record.get('TYPE_ID')
                    r_default = record.get('VARS_VALUE')
                    if module_matter_id == r_module_matter_id and variable_name == r_variable_name and variable_type_id == r_variable_type:  # noqa: F405, E501
                        # 一致するレコードがあればexist_flagをTrueにしbreak
                        exist_flag = True
                        exist_record_id = r_module_vars_link_id
                        exist_record_disuse_flag = record.get('DISUSE_FLAG')
                        break

                if exist_flag:
                    # 一致するレコードがあれば、対象のレコードが対象のレコードが廃止済みかどうかを判定する。廃止されていない場合は何も処理を行わない。
                    if exist_record_disuse_flag == "1":
                        # 対象のレコードが廃止済みであれば、「復活」を実行
                        data_list = {
                            "MODULE_VARS_LINK_ID": exist_record_id,
                            "VARS_VALUE": default,
                            "DISUSE_FLAG": "0",
                            "LAST_UPDATE_USER": g.get('USER_ID'),
                        }
                        primary_key_name = 'MODULE_VARS_LINK_ID'
                        ret_data = objdbca.table_update(TFConst.T_MODULE_VAR, data_list, primary_key_name)
                        if not ret_data:
                            # Module-変数紐付テーブルのレコード更新に失敗
                            msg = g.appmsg.get_log_message("BKY-50103", [])
                            raise Exception(msg)

                        # 対象を廃止しないためにactive_record_listに追加
                        active_record_list.append(exist_record_id)
                    else:
                        # 一致するレコードのデフォルト値が違う場合は更新
                        if not default == r_default:
                            data_list = {
                                "MODULE_VARS_LINK_ID": exist_record_id,
                                "VARS_VALUE": default,
                                "LAST_UPDATE_USER": g.get('USER_ID'),
                            }
                            primary_key_name = 'MODULE_VARS_LINK_ID'
                            ret_data = objdbca.table_update(TFConst.T_MODULE_VAR, data_list, primary_key_name)
                            if not ret_data:
                                # Module-変数紐付テーブルのレコード更新に失敗
                                msg = g.appmsg.get_log_message("BKY-50103", [])
                                raise Exception(msg)

                        # 一致するレコードがアクティブ状態なので対象を廃止しないためにactive_record_listに追加
                        active_record_list.append(exist_record_id)

                else:
                    # 一致するレコードがない場合は、レコードの新規登録
                    data_list = {
                        "MODULE_MATTER_ID": module_matter_id,
                        "VARS_NAME": variable_name,
                        "TYPE_ID": variable_type_id,
                        "VARS_VALUE": default,
                        "DISUSE_FLAG": "0",
                        "LAST_UPDATE_USER": g.get('USER_ID'),
                    }
                    primary_key_name = 'MODULE_VARS_LINK_ID'
                    ret_data = objdbca.table_insert(TFConst.T_MODULE_VAR, data_list, primary_key_name)
                    if not ret_data:
                        # Module-変数紐付テーブルへのレコード登録に失敗
                        msg = g.appmsg.get_log_message("BKY-50102", [])
                        raise Exception(msg)

                # メンバー変数テーブルに対する処理を実行
                g.applogger.debug(g.appmsg.get_log_message("BKY-50005"))
                ret, msg, exist_member_vars_list = set_member_vars(objdbca, TFConst, module_matter_id, variable_data, exist_member_vars_list)  # noqa F405
                if not ret:
                    raise Exception(msg)

        # Module-変数紐付テーブルから不要レコードを廃止する
        g.applogger.debug(g.appmsg.get_log_message("BKY-50011"))
        for record in t_mod_var_link_records:
            disuse_flag = record.get('DISUSE_FLAG')
            module_vars_link_id = record.get('MODULE_VARS_LINK_ID')
            # アクティブなレコードかつ、active_record_listに含まれていないIDのレコードを廃止する
            if disuse_flag == "0" and module_vars_link_id not in active_record_list:
                data_list = {
                    "MODULE_VARS_LINK_ID": module_vars_link_id,
                    "DISUSE_FLAG": "1",
                    "LAST_UPDATE_USER": g.get('USER_ID'),
                }
                primary_key_name = 'MODULE_VARS_LINK_ID'
                ret_data = objdbca.table_update(TFConst.T_MODULE_VAR, data_list, primary_key_name)
                if not ret_data:
                    # Module-変数紐付テーブルの不要レコード廃止に失敗
                    msg = g.appmsg.get_log_message("BKY-50104", [])
                    raise Exception(msg)

        # メンバー変数管理/変数ネスト管理から不要なレコードを廃止する
        ret, msg = discard_member_vars(objdbca, TFConst, exist_member_vars_list)  # noqa: F405
        if not ret:
            raise Exception(msg)

        # トランザクション終了(正常)
        objdbca.db_transaction_end(True)

    except Exception as msg:
        g.applogger.error(str(msg))
        result = False

        # トランザクション終了(異常)
        objdbca.db_transaction_end(False)

    return result


def set_movement_var_link(objdbca, TFConst):
    """
        Movement-Module紐付テーブルに登録されたレコードから、Movement-変数紐付テーブルを更新する
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

        # Movement-Module紐付テーブルからレコードを取得
        where_str = 'WHERE DISUSE_FLAG = %s'
        t_movement_module_records = objdbca.table_select(TFConst.T_MOVEMENT_MODULE, where_str, [0])

        # Module-変数紐付テーブルからレコードを取得
        where_str = 'WHERE DISUSE_FLAG = %s'
        t_mod_var_link_records = objdbca.table_select(TFConst.T_MODULE_VAR, where_str, [0])

        # Movement-変数紐付テーブルからレコードをすべて取得（廃止含め）
        where_str = ''
        t_movement_var_link_records = objdbca.table_select(TFConst.T_MOVEMENT_VAR, where_str, [])

        # トランザクション開始
        objdbca.db_transaction_start()

        # 不要レコードを特定するため、利用中レコードを格納するlist
        active_record_list = []

        # Movement-Module紐付テーブルのレコードをループ(record1)
        for record1 in t_movement_module_records:
            # Module-変数紐付テーブルのレコードをループ(record2)
            for record2 in t_mod_var_link_records:
                if record1.get('MODULE_MATTER_ID') == record2.get('MODULE_MATTER_ID'):
                    exist_flag = False
                    # Movement-変数紐付テーブルのレコードをループ(record3)
                    for record3 in t_movement_var_link_records:
                        if record2.get('MODULE_VARS_LINK_ID') == record3.get('MODULE_VARS_LINK_ID') and record1.get('MOVEMENT_ID') == record3.get('MOVEMENT_ID'):  # noqa: F405, E501
                            # 一致するレコードがあればexist_flagをTrueにしbreak
                            exist_flag = True
                            exist_record_id = record3.get('MVMT_VAR_LINK_ID')
                            exist_record_disuse_flag = record3.get('DISUSE_FLAG')
                            break

                    if exist_flag:
                        # 一致するレコードがあれば、対象のレコードが廃止済みかどうかを判定する。廃止されていない場合は何も処理を行わない。
                        if exist_record_disuse_flag == "1":
                            # 対象のレコードが廃止済みであれば、「復活」を実行
                            data_list = {
                                "MVMT_VAR_LINK_ID": exist_record_id,
                                "DISUSE_FLAG": "0",
                                "LAST_UPDATE_USER": g.get('USER_ID'),
                            }
                            primary_key_name = 'MVMT_VAR_LINK_ID'
                            ret_data = objdbca.table_update(TFConst.T_MOVEMENT_VAR, data_list, primary_key_name)
                            if not ret_data:
                                # Movement-変数紐付テーブルのレコード更新に失敗
                                msg = g.appmsg.get_log_message("BKY-50106", [])
                                raise Exception(msg)

                            # 対象を廃止しないためにactive_record_listに追加
                            active_record_list.append(exist_record_id)
                        else:
                            # 一致するレコードがアクティブ状態なので対象を廃止しないためにactive_record_listに追加
                            active_record_list.append(exist_record_id)

                    else:
                        # 一致するレコードがない場合は、レコードの新規登録
                        data_list = {
                            "MOVEMENT_ID": record1.get('MOVEMENT_ID'),
                            "MODULE_VARS_LINK_ID": record2.get('MODULE_VARS_LINK_ID'),
                            "DISUSE_FLAG": "0",
                            "LAST_UPDATE_USER": g.get('USER_ID'),
                        }
                        primary_key_name = 'MVMT_VAR_LINK_ID'
                        ret_data = objdbca.table_insert(TFConst.T_MOVEMENT_VAR, data_list, primary_key_name)
                        if not ret_data:
                            # Movement-変数紐付テーブルへのレコード登録に失敗
                            msg = g.appmsg.get_log_message("BKY-50105", [])
                            raise Exception(msg)

        # Movement-変数紐付テーブルから不要レコードを廃止する)
        g.applogger.debug(g.appmsg.get_log_message("BKY-50014"))
        for record in t_movement_var_link_records:
            disuse_flag = record.get('DISUSE_FLAG')
            mvmt_var_link_id = record.get('MVMT_VAR_LINK_ID')
            # アクティブなレコードかつ、active_record_listに含まれていないIDのレコードを廃止する
            if disuse_flag == "0" and mvmt_var_link_id not in active_record_list:
                data_list = {
                    "MVMT_VAR_LINK_ID": mvmt_var_link_id,
                    "DISUSE_FLAG": "1",
                    "LAST_UPDATE_USER": g.get('USER_ID'),
                }
                primary_key_name = 'MVMT_VAR_LINK_ID'
                ret_data = objdbca.table_update(TFConst.T_MOVEMENT_VAR, data_list, primary_key_name)
                if not ret_data:
                    # Movement-変数紐付テーブルの不要レコード廃止に失敗
                    msg = g.appmsg.get_log_message("BKY-50107", [])
                    raise Exception(msg)

        # トランザクション終了(正常)
        objdbca.db_transaction_end(True)

    except Exception as msg:
        g.applogger.error(str(msg))
        result = False

        # トランザクション終了(異常)
        objdbca.db_transaction_end(False)

    return result
