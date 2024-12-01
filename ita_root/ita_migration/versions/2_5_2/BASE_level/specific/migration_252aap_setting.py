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
import json

def main(work_dir_path, common_db):

    ###################################
    # Saas向けの機能、organization単位で保持しているINITIAL_DATA_ANSIBLE_IFのデータの設定値を更新する
    # （実行エンジンのリストに、実行エージェント（Ansible Execution Agent）を追加）
    ###################################
    g.applogger.info("[Trace] migration_252aap_setting.py start")

    organization_list = common_db.table_select("T_COMN_ORGANIZATION_DB_INFO", "WHERE `DISUSE_FLAG`=0", [])

    for organization_info in organization_list:
        inistial_data_ansible_if = organization_info.get("INITIAL_DATA_ANSIBLE_IF")
        organization_id = organization_info.get("ORGANIZATION_ID")
        dict_ansible_if = None
        if (inistial_data_ansible_if is not None) and (len(inistial_data_ansible_if) != 0):
            try:
                dict_ansible_if = json.loads(inistial_data_ansible_if)
            except Exception:
                break

            if "execution_engine_list" in dict_ansible_if:
                if "Ansible Execution Agent" not in dict_ansible_if["execution_engine_list"]:
                    # 実行エージェントが、インターフェース情報の実行エンジンの選択リストにない場合に追加
                    dict_ansible_if["execution_engine_list"].append("Ansible Execution Agent")
                    organization_info["INITIAL_DATA_ANSIBLE_IF"] = json.dumps(dict_ansible_if)

                    common_db.db_transaction_start()
                    common_db.table_update('T_COMN_ORGANIZATION_DB_INFO', [organization_info], 'PRIMARY_KEY')
                    common_db.db_commit()
                    g.applogger.info("[Trace] 'Ansible Execution Agent' is added to 'execution_engine_list' of the organization(organization_id={})".format(organization_id))

    g.applogger.info("[Trace] migration_252aap_setting.py end")
    return 0
