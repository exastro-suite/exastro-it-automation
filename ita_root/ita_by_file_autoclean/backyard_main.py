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

from datetime import datetime
from datetime import timedelta
import os
import inspect
import shutil
import glob

backyard_name = 'ita_by_file_autoclean'


def backyard_main(organization_id, workspace_id):
    print("backyard_main ita_by_file_autoclean called")

    """
        ファイル削除機能（backyard）
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
    tmp_msg = 'Process Start'
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # DB接続
    tmp_msg = 'db connect'
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    objdbca = DBConnectWs(workspace_id)  # noqa: F405

    try:
        # ファイル削除管理のデータを取得する
        del_file_list = get_del_file_list(objdbca)
        if len(del_file_list) == 0:
            return retBool, result,

        # 現在時刻を取得
        now_time = datetime.now()

        # ファイル削除カウント(全体)
        all_del_cnt = 0

        # ファイル削除管理のデータ数ループ
        for del_file in del_file_list:
            # ファイル削除カウント(対象ディレクトリ)
            del_cnt = 0

            # 削除日数,　対象ディレクトリ、対象ファイル、サブディレクトリ削除フラグ
            del_days = del_file.get('DEL_DAYS')
            tmp_target_dir = del_file.get('TARGET_DIR')
            target_file = del_file.get('TARGET_FILE')
            del_subdir_flg = del_file.get('DEL_SUB_DIR_FLG')

            # 対象ディレクトリパス補完
            target_dir = get_target_path([tmp_target_dir])
            target_file_path = get_target_path([tmp_target_dir, target_file])

            tmp_msg = "target_dir:{}, target_file:{}, del_days:{}".format(tmp_target_dir, target_file, del_days)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # Check: 削除日数
            if isinstance(del_days, int) is False:
                tmp_msg = "del_days is failed ({})".format(del_days)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                continue

            # Check: パス確認
            isabs_target_dir = os.path.isabs(target_dir)  # noqa: F405
            if isabs_target_dir is False:
                tmp_msg = "target_dir isabs failed  ({})".format(target_dir)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                continue

            # Check: ディレクトリ存在確認
            is_target_dir = os.path.isdir(target_dir)  # noqa: F405
            if is_target_dir is False:
                tmp_msg = "target_dir is not exist  ({})".format(target_dir)
                g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                continue

            # 削除対象ディレクトリ内のファイル一覧取得
            target_df_list = glob.glob(target_file_path)

            tmp_msg = "target file count: {}".format(len(target_df_list))
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

            # 削除対象時刻
            target_time = now_time - timedelta(days=int(del_days))

            for target_path in target_df_list:
                del_flg = False

                # ファイル/ディレクトリ確認
                is_dir_target_path = os.path.isdir(target_path)  # noqa: F405
                is_file_target_path = os.path.isfile(target_path)  # noqa: F405
                # 対象のタイムスタンプ取得
                target_timestamp = datetime.fromtimestamp(os.path.getmtime(target_path))  # noqa: F405

                # ファイル/ディレクトリ削除対象判定
                if is_file_target_path is True:
                    # ファイル:削除対象日経過
                    if target_timestamp < target_time:
                        del_flg = True
                elif is_dir_target_path is True and del_subdir_flg == "1":
                    # サブディレクトリ:削除対象日経過かつサブディレクトリ削除ON
                    if target_timestamp < target_time:
                        del_flg = True
                else:
                    continue

                # ファイル、サブディレクトリ削除
                if del_flg is True:
                    try:
                        # print("del target_path:", del_flg, target_path, target_timestamp, target_time, target_timestamp < target_time)
                        if is_file_target_path:
                            # ファイル削除
                            os.remove(target_path)  # noqa: F405
                        elif is_dir_target_path:
                            # サブディレクトリ削除
                            shutil.rmtree(target_path)
                        else:
                            raise Exception()
                        # 削除件数カウント
                        del_cnt += 1
                        all_del_cnt += 1
                    except Exception as e:
                        tmp_msg = e
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                        tmp_msg = "faild delete target_path: {}".format(target_path)
                        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
                else:
                    pass

            # 削除件数(対象)
            tmp_msg = "Target delete file count: {} ({} {})".format(del_cnt, tmp_target_dir, target_file)
            g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        # 削除件数(全体)
        tmp_msg = "All delete file count: {}".format(all_del_cnt)
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    except Exception as e:
        # 処理終了 Exception
        tmp_msg = e
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
        tmp_msg = 'Process END: Exception'
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    # 処理終了
    tmp_msg = 'Process END'
    g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405

    return retBool, result,


# ファイル削除対象取得
def get_del_file_list(objdbca):
    table_name = 'T_COMN_DEL_FILE_LIST'
    rows = objdbca.table_select(table_name, 'WHERE DISUSE_FLAG = %s', [0])
    result = []
    for row in rows:
        result.append(row)
    return result


# 対象パス生成
def get_base_path(organization_id=None, workspace_id=None):
    if organization_id is None or workspace_id is None:
        base_path = "{}{}/{}/".format(os.environ.get('STORAGEPATH'), g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))   # noqa: F405
    else:
        base_path = "{}{}/{}/".format(os.environ.get('STORAGEPATH'), organization_id, workspace_id)   # noqa: F405
    return base_path


# 削除対象パス生成
def get_target_path(add_path=[], organization_id=None, workspace_id=None):
    if add_path is None:
        base_path = False
    else:
        add_path = '/'.join(map(str, add_path))
        base_path = "{}/{}".format(get_base_path(organization_id, workspace_id), add_path).replace('//', '/').replace('//', '/')   # noqa: F405

    return base_path


def addline_msg(msg=''):
    info = inspect.getouterframes(inspect.currentframe())[1]
    msg_line = "{} ({}:{})".format(msg, os.path.basename(info.filename), info.lineno)
    return msg_line
