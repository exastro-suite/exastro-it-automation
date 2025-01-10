#   Copyright 2024 NEC Corporation
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
import json
import os
import shutil

from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.util import get_timestamp, put_uploadfiles_jnl

def main(work_dir_path, ws_db):
    ###########################################################
    # jnl_patch_bug_2666
    ###########################################################
    g.applogger.info("[Trace][start] bug fix issue2666")

    common_db = DBConnectCommon()  # noqa: F405

    organization_id = g.ORGANIZATION_ID
    workspace_id = g.WORKSPACE_ID

    # organization単位のドライバ情報を取得する
    org_no_install_driver = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE ORGANIZATION_ID = '{}' AND DISUSE_FLAG = {}".format(organization_id, 0))[0]["NO_INSTALL_DRIVER"]
    common_db.db_disconnect()

    # oaseインストール済みの場合しか対応しない
    org_no_install_driver = json.loads(org_no_install_driver) if org_no_install_driver is not None else {}
    if 'oase' in org_no_install_driver:
        return 0

    table_name = "T_OASE_NOTIFICATION_TEMPLATE_COMMON"
    table_name_jnl = table_name + "_JNL"
    uuid_list = ["1", "2", "3", "4"]
    ja_file_list = ["新規.j2", "既知（判定済）.j2", "既知（時間切れ）.j2", "未知.j2"]
    en_file_list = [["New.j2", "/template_file/1/old/1-2/", "/template_file/1/"], ["Known(evaluated).j2", "/template_file/2/old/2-2/", "/template_file/2/"], ["Known(timeout).j2", "/template_file/3/old/3-2/", "/template_file/3/"], ["Undetected.j2", "/template_file/4/old/4-2/", "/template_file/4/"]]
    python_path = os.environ.get('PYTHONPATH')


    # トランザクション
    ws_db.db_transaction_start()

    """v2.5.0-v2.5.2の間に作成したワークスペースへの対策
        対象の抽出条件
            ・JOURNAL_SEQ_NOが{}-2のレコードが、JOURNAL_ACTION_CLASSがINSERTになっている
            ・JOURNAL_SEQ_NOが{}-2のレコードが、JOURNAL_ACTION_CLASSがUPDATE、JOURNAL_REG_DATETIMEが20240209000001になっている
        対処：
            1.JOURNAL_SEQ_NOが、{}-2のレコードを削除
            2.JOURNAL_SEQ_NOが{}の履歴にあるファイルがなければ、配置する
            3.JOURNAL_SEQ_NOが{}のレコードがない場合、JOURNAL_ACTION_CLASSがINSERTで挿入する
            4.jnlパッチをあてる
    """

    for uuid in uuid_list:
        index = int(uuid) - 1

        # 履歴内の{}-2のレコード
        jnl_id = "{}-2".format(uuid)
        jnl_record = ws_db.table_select(table_name_jnl, "WHERE `JOURNAL_SEQ_NO` = %s", [jnl_id])
        if len(jnl_record) == 0:
            continue

        if jnl_record[0]['JOURNAL_ACTION_CLASS'] == 'INSERT' or (jnl_record[0]['JOURNAL_ACTION_CLASS'] == 'UPDATE' and jnl_record[0]['JOURNAL_REG_DATETIME'].strftime('%Y%m%d%H%M%S') == "20240209000001"):
            # x-2のレコードを削除する
            sql = "DELETE FROM `{}` WHERE `JOURNAL_SEQ_NO` = %s".format(table_name_jnl)
            ws_db.sql_execute(sql, [jnl_id])
            # ファイルもあれば削除しにいく(ディレクトリで削除する)
            en_file = en_file_list[index]
            file_path = os.path.join(work_dir_path, "uploadfiles", "110102") + en_file[1]
            if os.path.exists(file_path):
                shutil.rmtree(file_path)

        # x（新規.j2などの日本語）のファイルがなければ、履歴だけ置く
        config = [
                {"新規.j2":["/template_file/1/old/1/","/template_file/1/"]},
                {"既知（判定済）.j2":["/template_file/2/old/2/","/template_file/2/"]},
                {"既知（時間切れ）.j2":["/template_file/3/old/3/","/template_file/3/"]},
                {"未知.j2":["/template_file/4/old/4/","/template_file/4/"]}
        ]

        src_dir = os.path.join(python_path, "versions", "2_4_0", "WS_level", "files", "110102")
        dest_dir = os.path.join(work_dir_path, "uploadfiles", "110102")

        for file_name, copy_cfg in config[index].items():
            org_file = os.path.join(src_dir, file_name)
            old_file_path = dest_dir + copy_cfg[0]
            # file_path = dest_dir + copy_cfg[1]

            if not os.path.isdir(old_file_path):
                os.makedirs(old_file_path)
                shutil.copy(org_file, old_file_path + file_name)

            # try:
            #     os.symlink(old_file_path + file_name, file_path + file_name)
            # except FileExistsError:
            #     pass

        # x（新規.j2などの日本語）のレコードがなければ、挿入する
        jnl_record = ws_db.table_select(table_name_jnl, "WHERE `JOURNAL_SEQ_NO` = %s", [uuid])
        if len(jnl_record) == 0:
            insert_jnl_data_org = {
                            "JOURNAL_SEQ_NO": uuid,
                            "JOURNAL_REG_DATETIME": "_____DATE_____",
                            "JOURNAL_ACTION_CLASS": "INSERT",
                            "NOTIFICATION_TEMPLATE_ID": uuid,
                            "EVENT_TYPE": uuid,
                            "TEMPLATE_FILE": ja_file_list[index],
                            "NOTE": None,
                            "DISUSE_FLAG": "0",
                            "LAST_UPDATE_TIMESTAMP": "_____DATE_____",
                            "LAST_UPDATE_USER": "1"
                        }

            # _____DATE_____を置換して、SQLを実行する
            journal_reg_datetime = "2024-02-09 00:00:00"
            insert_jnl_data = {}
            for insert_key, insert_val in insert_jnl_data_org.items():
                if type(insert_val) == str:
                    insert_val = insert_val.replace("_____DATE_____", journal_reg_datetime)
                insert_jnl_data[insert_key] = insert_val
            # make sql statement
            column_list = list(insert_jnl_data.keys())
            prepared_list = ["%s"]*len(column_list)
            value_list = list(insert_jnl_data.values())
            sql = "INSERT INTO `{}` ({}) VALUES ({})".format(table_name_jnl, ','.join(column_list), ','.join(prepared_list))
            ws_db.sql_execute(sql, value_list)

    # jnl patchをかける
    src_dir = "versions/2_5_0/WS_level/jnl/"
    config_file_path = os.path.join(src_dir, "oase_config.json")
    dest_dir = os.path.join(work_dir_path, "uploadfiles")
    put_uploadfiles_jnl(ws_db, config_file_path, src_dir, dest_dir)
    # コミット
    ws_db.db_commit()

    g.applogger.info("[Trace][end] bug fix issue2666")
    return 0


