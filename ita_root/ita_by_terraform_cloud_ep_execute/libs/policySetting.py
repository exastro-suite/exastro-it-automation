# Copyright 2023 NEC Corporation#
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
from common_libs.terraform_driver.cloud_ep.terraform_restapi import *  # noqa: F403
import json
import os


class policySetting():
    """
    Policyに関するレコードを見て、Terraform Cloud/Enterprise側にPolicyおよびPolicySetの登録処理を行う。
    """
    def __init__(self, ws_db=None, TFConst=None, restApiCaller=None, tf_organization_name=None, tf_workspace_name=None, tf_workspace_id=None, tf_manage_workspace_id=None, execution_no=None):  # noqa: E501

        """
        処理内容
            コンストラクタ
        パラメータ
            ws_db: WorkspaceDBインスタンス
            TFConset: 定数クラス
            restApiCaller: RESTAPIコールクラス
            tf_organization_name: TerraformのOrganization名
            tf_workspace_name: TerraformのWorkspace名
            tf_workspace_id: WorkspaceID(ITAのレコードのID)
            tf_manage_workspace_id: WorkspaceID(Terraformで管理するID)
        戻り値
            なし
        """
        self.TFConst = TFConst
        self.ws_db = ws_db
        self.restApiCaller = restApiCaller
        self.tf_organization_name = tf_organization_name
        self.tf_workspace_name = tf_workspace_name
        self.tf_workspace_id = tf_workspace_id
        self.tf_manage_workspace_id = tf_manage_workspace_id
        self.execution_no = execution_no

    def policy_setting_main(self):  # noqa: C901
        """
        Policyに関するメイン処理
        """
        # 変数定義
        base_dir = os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
        result = True
        msg = ''
        log_msg = ''
        policy_data_dict = {}

        try:
            # [RESTAPI]連携先TerraformからPolicySetの一覧を取得する
            g.applogger.info(g.appmsg.get_log_message("BKY-51013", [self.execution_no]))
            response_array = get_tf_policy_set_list(self.restApiCaller, self.tf_organization_name)  # noqa: F405
            response_status_code = response_array.get('statusCode')
            # ステータスコードが200以外の場合はエラー判定
            if not response_status_code == 200:
                log_msg = g.appmsg.get_log_message("MSG-82018", [])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82018", [])
                return False, msg, policy_data_dict
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # PolicySet一覧を格納
            tf_policy_set_list = []
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                tf_policy_set_list.append(data)

            # PolicySetに紐づくWorkspaceの中で、今回の対象Workspaceがあればすべて切り離す
            for policy_set_data in tf_policy_set_list:
                tf_manage_policy_set_id = policy_set_data.get('id')
                relationships_workspace_data = policy_set_data.get('relationships', {}).get('workspaces', {}).get('data')
                for workspace_data in relationships_workspace_data:
                    if workspace_data.get('id') == self.tf_manage_workspace_id:
                        # [RESTAPI]一致するWorkspaceIDについて、切り離しを実行
                        g.applogger.info(g.appmsg.get_log_message("BKY-51015", [self.execution_no]))
                        response_array = delete_relationships_workspace(self.restApiCaller, tf_manage_policy_set_id, self.tf_manage_workspace_id)  # noqa: F405, E501
                        response_status_code = response_array.get('statusCode')
                        # ステータスコードが204以外の場合はエラー判定
                        if not response_status_code == 204:
                            log_msg = g.appmsg.get_log_message("MSG-82019", [])
                            g.applogger.info(log_msg)
                            msg = "[API Error]" + g.appmsg.get_api_message("MSG-82019", [])
                            return False, msg, policy_data_dict
                        g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # tf_workspace_idからPolicySet-Workspace紐付管理テーブルに登録されているレコードを取得
            where_str = 'WHERE WORKSPACE_ID = %s AND DISUSE_FLAG = %s'
            ret = self.ws_db.table_select(self.TFConst.T_POLICYSET_WORKSPACE, where_str, [self.tf_workspace_id, 0])
            if not ret:
                # 対象のレコードがない場合は、Policy処理を行わない。
                return result, msg, policy_data_dict

            # 対象のPolicySetIDを取得(対象は複数の可能性があるため、list化する)
            policy_set_id_list = []
            for record in ret:
                policy_set_id_list.append(record.get('POLICY_SET_ID'))

            # Policy set管理テーブルからレコードを取得
            policy_set_data_dict = {}
            policy_set_exclusion_list = []
            for policy_set_id in policy_set_id_list:
                where_str = 'WHERE POLICY_SET_ID = %s AND DISUSE_FLAG = %s'
                ret = self.ws_db.table_select(self.TFConst.T_POLICYSET, where_str, [policy_set_id, 0])
                if not ret:
                    # 除外リストにIDを追加
                    policy_set_exclusion_list.append(policy_set_id)
                    # 対象のレコードがない場合はcontinue
                    continue

                # policySetの登録情報を格納
                policy_set_data_dict[policy_set_id] = {"policy_set_id": policy_set_id, "policy_set_name": ret[0].get('POLICY_SET_NAME'), "policy_set_note": ret[0].get('NOTE')}  # noqa: E501

            # 除外リストにあるIDを除外する
            excluded_policy_set_id_list = set(policy_set_id_list) - set(policy_set_exclusion_list)
            policy_set_id_list = list(excluded_policy_set_id_list)

            # policy_set_idからPolicySet-Policy紐付管理テーブルに登録されているレコードを取得
            policy_set_policy_data_dict = {}
            policy_id_list = []
            for policy_set_id in policy_set_id_list:
                temp_policy_id_list = []
                where_str = 'WHERE POLICY_SET_ID = %s AND DISUSE_FLAG = %s'
                ret = self.ws_db.table_select(self.TFConst.T_POLICYSET_POLICY, where_str, [policy_set_id, 0])
                if not ret:
                    # 対象のpolicySetのIDでレコードが無い場合、policy_set_data_dictから対象のkeyを削除
                    policy_set_data_dict.pop(policy_set_id)

                    # 対象のレコードがない場合はcontinue
                    continue

                # 対象のPolicyIDを取得(対象は複数の可能性があるため、list化する)
                for record in ret:
                    temp_policy_id_list.append(record.get('POLICY_ID'))
                    policy_id_list.append(record.get('POLICY_ID'))

                # policy_set_idをkeyに、policy_id_listを格納する
                policy_set_policy_data_dict[policy_set_id] = temp_policy_id_list

            # policy_id_listの重複を削除
            policy_id_list = list(dict.fromkeys(policy_id_list))

            # Policy管理テーブルからレコードを取得
            for policy_id in policy_id_list:
                where_str = 'WHERE POLICY_ID = %s AND DISUSE_FLAG = %s'
                ret = self.ws_db.table_select(self.TFConst.T_POLICY, where_str, [policy_id, 0])
                if not ret:
                    # 対象のレコードがない場合は、Policy処理を行わない。
                    return result, msg, policy_data_dict

                # policyの登録情報を格納
                policy_data_dict[policy_id] = {"policy_id": policy_id, "policy_name": ret[0].get('POLICY_NAME'), "policy_file": ret[0].get('POLICY_MATTER_FILE'), "policy_note": ret[0].get('NOTE')}  # noqa: E501

            # [RESTAPI]連携先TerraformからPolicyの一覧を取得する
            g.applogger.info(g.appmsg.get_log_message("BKY-51014", [self.execution_no]))
            response_array = get_tf_policy_list(self.restApiCaller, self.tf_organization_name)  # noqa: F405
            response_status_code = response_array.get('statusCode')
            # ステータスコードが200以外の場合はエラー判定
            if not response_status_code == 200:
                log_msg = g.appmsg.get_log_message("MSG-82020", [])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82020", [])
                return False, msg, policy_data_dict
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # Policy一覧を格納
            tf_policy_list = []
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                tf_policy_list.append(data)

            # ITA側とTerraform側でPolicyの登録状態を照らし合わせ、登録/更新を実行する
            ita_tf_policy_link = {}  # ITAとTerraformのポリシーIDの結びつけ
            for policy_id, policy_data in policy_data_dict.items():
                exist_flag = False
                tf_manage_policy_id = None
                policy_name = policy_data.get('policy_name')
                policy_file = policy_data.get('policy_file')
                policy_note = policy_data.get('policy_note')

                # tf_policy_listから、対象のpolicyがTerraformに登録済みかどうかを確認する
                for tf_policy_data in tf_policy_list:
                    attributes = tf_policy_data.get('attributes')
                    tf_policy_name = attributes.get('name')
                    if tf_policy_name == policy_name:
                        # Terraform側のpolicyIDの取得と、登録済みフラグをTrueにしてbreak
                        tf_manage_policy_id = tf_policy_data.get('id')
                        exist_flag = True
                        break

                if exist_flag:
                    # [RESTAPI]policyが既にTerraform側に登録されている場合、更新APIを実行する
                    g.applogger.info(g.appmsg.get_log_message("BKY-51018", [self.execution_no, policy_name]))
                    response_array = update_policy(self.restApiCaller, tf_manage_policy_id, policy_name, policy_file, policy_note)  # noqa: F405
                    response_status_code = response_array.get('statusCode')
                    # ステータスコードが200以外の場合はエラー判定
                    if not response_status_code == 200:
                        log_msg = g.appmsg.get_log_message("MSG-82021", [])
                        g.applogger.info(log_msg)
                        msg = "[API Error]" + g.appmsg.get_api_message("MSG-82021", [])
                        return False, msg, policy_data_dict
                    g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

                    # IDの結び付け用dictに格納
                    ita_tf_policy_link[policy_id] = tf_manage_policy_id

                else:
                    # [RESTAPI]plicyが登録されていない場合、登録APIを実行する
                    g.applogger.info(g.appmsg.get_log_message("BKY-51017", [self.execution_no, policy_name]))
                    response_array = create_policy(self.restApiCaller, self.tf_organization_name, policy_name, policy_file, policy_note)  # noqa: F405
                    response_status_code = response_array.get('statusCode')
                    # ステータスコードが201以外の場合はエラー判定
                    if not response_status_code == 201:
                        log_msg = g.appmsg.get_log_message("MSG-82022", [])
                        g.applogger.info(log_msg)
                        msg = "[API Error]" + g.appmsg.get_api_message("MSG-82022", [])
                        return False, msg, policy_data_dict
                    g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

                    # API返却値からTerraformのpolicyIDを取得
                    respons_contents_json = response_array.get('responseContents')
                    respons_contents = json.loads(respons_contents_json)
                    respons_contents_data = respons_contents.get('data')
                    tf_manage_policy_id = respons_contents_data.get('id')

                    # IDの結び付け用dictに格納
                    ita_tf_policy_link[policy_id] = tf_manage_policy_id

                # [RESTAPI]登録/更新したPolicyにファイルを適用する
                g.applogger.info(g.appmsg.get_log_message("BKY-51019", [self.execution_no]))
                policy_file_dir = base_dir + self.TFConst.DIR_POLICY
                policy_file_path = policy_file_dir + '/' + policy_id + '/' + policy_file
                response_array = policy_file_upload(self.restApiCaller, tf_manage_policy_id, policy_file_path)  # noqa: F405
                response_status_code = response_array.get('statusCode')
                # ステータスコードが200以外の場合はエラー判定
                if not response_status_code == 200:
                    log_msg = g.appmsg.get_log_message("MSG-82023", [])
                    g.applogger.info(log_msg)
                    msg = "[API Error]" + g.appmsg.get_api_message("MSG-82023", [])
                    return False, msg, policy_data_dict
                g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # ITA側とTerraform側でPolicySetの登録状態を照らし合わせ、登録/更新を実行する
            for policy_set_id, policy_set_data in policy_set_data_dict.items():
                exist_flag = False
                tf_manage_policy_set_id = None
                policy_set_name = policy_set_data.get('policy_set_name')
                policy_set_note = policy_set_data.get('policy_set_note')

                # tf_policy_set_listから、対象のpolicyがTerraformに登録済みかどうかを確認する
                for tf_policy_set_data in tf_policy_set_list:
                    attributes = tf_policy_set_data.get('attributes')
                    tf_policy_set_name = attributes.get('name')
                    if tf_policy_set_name == policy_set_name:
                        # Terraform側のpolicyIDの取得と、登録済みフラグをTrueにしてbreak
                        tf_manage_policy_set_id = tf_policy_set_data.get('id')
                        exist_flag = True
                        break

                if exist_flag:
                    # [RESTAPI]policySetが既にTerraform側に登録されている場合、更新APIを実行する
                    g.applogger.info(g.appmsg.get_log_message("BKY-51021", [self.execution_no, policy_set_name]))
                    response_array = update_policy_set(self.restApiCaller, tf_manage_policy_set_id, policy_set_name, policy_set_note)  # noqa: F405
                    response_status_code = response_array.get('statusCode')
                    # ステータスコードが200以外の場合はエラー判定
                    if not response_status_code == 200:
                        log_msg = g.appmsg.get_log_message("MSG-82024", [])
                        g.applogger.info(log_msg)
                        msg = "[API Error]" + g.appmsg.get_api_message("MSG-82024", [])
                        return False, msg, policy_data_dict
                    g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

                    # [RESTAPI]紐づいているpolicyをすべて切り離す
                    g.applogger.info(g.appmsg.get_log_message("BKY-51016", [self.execution_no]))
                    respons_contents_json = response_array.get('responseContents')
                    respons_contents = json.loads(respons_contents_json)
                    respons_contents_data = respons_contents.get('data')
                    relationships = respons_contents_data.get('relationships')
                    registered_policy_set_policy = relationships.get('policies')
                    response_array = delete_relationships_policy(self.restApiCaller, tf_manage_policy_set_id, registered_policy_set_policy)  # noqa: F405, E501
                    response_status_code = response_array.get('statusCode')
                    # ステータスコードが204以外の場合はエラー判定
                    if not response_status_code == 204:
                        log_msg = g.appmsg.get_log_message("MSG-82025", [])
                        g.applogger.info(log_msg)
                        msg = "[API Error]" + g.appmsg.get_api_message("MSG-82025", [])
                        return False, msg, policy_data_dict
                    g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

                else:
                    # [RESTAPI]plicySetが登録されていない場合、登録APIを実行する
                    g.applogger.info(g.appmsg.get_log_message("BKY-51020", [self.execution_no, policy_set_name]))
                    response_array = create_policy_set(self.restApiCaller, self.tf_organization_name, policy_set_name, policy_set_note)  # noqa: F405
                    response_status_code = response_array.get('statusCode')
                    # ステータスコードが201以外の場合はエラー判定
                    if not response_status_code == 201:
                        log_msg = g.appmsg.get_log_message("MSG-82026", [])
                        g.applogger.info(log_msg)
                        msg = "[API Error]" + g.appmsg.get_api_message("MSG-82026", [])
                        return False, msg, policy_data_dict
                    g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

                    # policySetのIDを格納
                    respons_contents_json = response_array.get('responseContents')
                    respons_contents = json.loads(respons_contents_json)
                    respons_contents_data = respons_contents.get('data')
                    tf_manage_policy_set_id = respons_contents_data.get('id')

                # [RESTAPI]policySetとWorkspaceの紐付け処理を実行
                g.applogger.info(g.appmsg.get_log_message("BKY-51022", [self.execution_no, policy_set_name, self.tf_workspace_name]))
                response_array = relationships_workspace(self.restApiCaller, tf_manage_policy_set_id, self.tf_manage_workspace_id)  # noqa: F405
                response_status_code = response_array.get('statusCode')
                # ステータスコードが204以外の場合はエラー判定
                if not response_status_code == 204:
                    log_msg = g.appmsg.get_log_message("MSG-82027", [])
                    g.applogger.info(log_msg)
                    msg = "[API Error]" + g.appmsg.get_api_message("MSG-82027", [])
                    return False, msg, policy_data_dict
                g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

                # [RESTAPI]policySetとpolicyの紐付け処理を実行
                g.applogger.info(g.appmsg.get_log_message("BKY-51023", [self.execution_no, policy_set_name, policy_name]))
                registered_policy_set_policy = {"data": []}
                target_policy_id_list = policy_set_policy_data_dict.get(policy_set_id)
                for policy_id in target_policy_id_list:
                    tf_policy_id = ita_tf_policy_link.get(policy_id)
                    add_policy_data = {"id": tf_policy_id, "type": "policies"}
                    registered_policy_set_policy["data"].append(add_policy_data)

                response_array = relationships_policy(self.restApiCaller, tf_manage_policy_set_id, registered_policy_set_policy)  # noqa: F405
                response_status_code = response_array.get('statusCode')
                # ステータスコードが204以外の場合はエラー判定
                if not response_status_code == 204:
                    log_msg = g.appmsg.get_log_message("MSG-82028", [])
                    g.applogger.info(log_msg)
                    msg = "[API Error]" + g.appmsg.get_api_message("MSG-82028", [])
                    return False, msg, policy_data_dict
                g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

        except Exception as e:
            result = False
            msg = e

        return result, msg, policy_data_dict
