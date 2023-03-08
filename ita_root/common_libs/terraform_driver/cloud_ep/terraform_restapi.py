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
import pathlib


def get_tf_organization_list(restApiCaller):
    """
        連携先TerraformからOrganizationの一覧を取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/organizations'
    response_array = restApiCaller.rest_call('GET', api_uri)

    return response_array


def get_tf_workspace_list(restApiCaller, tf_organization_name):
    """
        連携先TerraformからWorkspacenの一覧を取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_organization_name: 対象のOrganization名
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/organizations/%s/workspaces' % (tf_organization_name)
    response_array = restApiCaller.rest_call('GET', api_uri)

    return response_array


def get_tf_workspace_var_list(restApiCaller, tf_manage_workspace_id):
    """
        連携先TerraformからWorkspaceに登録されているVariables(変数)の一覧を取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_manage_workspace_id: Terraformで管理しているWorkspaceのID
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/workspaces/%s/vars' % (tf_manage_workspace_id)
    response_array = restApiCaller.rest_call('GET', api_uri)

    return response_array


def delete_tf_workspace_var(restApiCaller, tf_manage_variable_id):
    """
        連携先Terraformから対象のVariables(変数)を削除する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_manage_variable_id: Terraformで管理しているVarableのID
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/vars/%s' % (tf_manage_variable_id)
    response_array = restApiCaller.rest_call('DELETE', api_uri)

    return response_array


def create_tf_workspace_var(restApiCaller, tf_manage_workspace_id, key, value, hcl=False, sensitive=False, category="terraform"):
    """
        連携先Terraformから対象のVariables(変数)を削除する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_manage_variable_id: Terraformで管理しているVarableのID
            key: 登録する変数のkey
            value: 登録する変数のvalue
            hcl: HCL設定のON/OFF(True or False)
            sensitive: Sensitive設定のON/OFF(True or False)
            category: "terraform" or "env"
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/vars'
    request_contents = {
        "data": {
            "type": "vars",
            "attributes": {
                "key": key,
                "value": value,
                "description": "",
                "category": category,
                "hcl": hcl,
                "sensitive": sensitive
            },
            "relationships": {
                "workspace": {
                    "data": {
                        "id": tf_manage_workspace_id,
                        "type": "workspace"
                    }
                }
            }
        }
    }
    response_array = restApiCaller.rest_call('POST', api_uri, request_contents)

    return response_array


def get_upload_url(restApiCaller, tf_manage_workspace_id):
    """
        tar.gzファイルをアップロードするためのURLを取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_manage_variable_id: Terraformで管理しているVarableのID
            key: 登録する変数のkey
            value: 登録する変数のvalue
            hcl: HCL設定のON/OFF(True or False)
            sensitive: Sensitive設定のON/OFF(True or False)
            category: "terraform" or "env"
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/workspaces/%s/configuration-versions' % (tf_manage_workspace_id)
    # auto-queue-runsはアップロード後自動的にPlanを実行するかどうか。Falseは実行しない。
    request_contents = {
        "data": {
            "type": "configuration-versions",
            "attributes": {
                "auto-queue-runs": False,
                "speculative": False
            }
        }
    }
    response_array = restApiCaller.rest_call('POST', api_uri, request_contents)

    return response_array


def module_upload(restApiCaller, gztar_path, upload_url):
    """
        Terraformにtar.gzファイルをアップロードする
        ARGS:
            restApiCaller: RESTAPIコールクラス
            gztar_path: アップロードするtar.gzファイルのフルパス
            upload_url: アップロード先のURL
        RETRUN:
            response_array: RESTAPI返却値

    """
    # Moduleファイルアップロード用RESTAPIの特殊な仕様として、module_upload_flagをTrueとしてRESTAPIを実行する
    api_uri = None
    content = pathlib.Path(gztar_path).read_bytes()
    header = None
    module_upload_flag = True
    response_array = restApiCaller.rest_call('PUT', api_uri, content, header, module_upload_flag, upload_url)

    return response_array


def create_run(restApiCaller, tf_manage_workspace_id, cv_id):
    """
        連携先TerraformのWorkspace対しRUNを実行する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_manage_variable_id: Terraformで管理しているVarableのID
            cv_id: アップロードURL取得時に取得したcv_id
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/runs'
    request_contents = {
        "data": {
            "type": "runs",
            "attributes": {
                "is-destroy": False,
                "message": ""
            },
            "relationships": {
                "workspace": {
                    "data": {
                        "id": tf_manage_workspace_id,
                        "type": "workspace"
                    }
                },
                "configuration-version": {
                    "data": {
                        "id": cv_id,
                        "type": "configuration-versions"
                    }
                }
            }
        }
    }
    response_array = restApiCaller.rest_call('POST', api_uri, request_contents)

    return response_array


def cancel_run(restApiCaller, tf_run_id):
    """
        RUNをキャンセルする
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_run_id: TerraformのRUN-ID
        RETRUN:
            response_array: RESTAPI返却値
    """
    api_uri = '/runs/%s/actions/cancel' % (tf_run_id)

    response_array = restApiCaller.rest_call('POST', api_uri)

    return response_array


def get_run_data(restApiCaller, tf_run_id):
    """
        連携先TerraformからRUNの詳細を取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_run_id: TerraformのRUN-ID
        RETRUN:
            response_array: RESTAPI返却値
    """
    api_uri = '/runs/%s' % (tf_run_id)
    response_array = restApiCaller.rest_call('GET', api_uri)

    return response_array


def get_plan_data(restApiCaller, tf_plan_id):
    """
        連携先TerraformからPlanの詳細を取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_plan_id: Terraformで管理しているplan_id
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/plans/%s' % (tf_plan_id)
    response_array = restApiCaller.rest_call('GET', api_uri)

    return response_array


def get_policy_check_data(restApiCaller, tf_run_id):
    """
        連携先TerraformからPolicy checkの詳細を取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_run_id: TerraformのRUN-ID
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/runs/%s/policy-checks' % (tf_run_id)
    response_array = restApiCaller.rest_call('GET', api_uri)

    return response_array


def get_apply_data(restApiCaller, tf_apply_id):
    """
        連携先TerraformからApplyの詳細を取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_apply_id: Terraformで管理しているapply_id
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/applies/%s' % (tf_apply_id)
    response_array = restApiCaller.rest_call('GET', api_uri)

    return response_array


def get_run_log(restApiCaller, get_log_url, direct_flag=False):
    """
        TerraformのRUNからログを取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            get_log_url: ログ取得用URL
        RETRUN:
            response_array: RESTAPI返却値

    """
    responseContents = restApiCaller.get_log_data('GET', get_log_url, direct_flag)

    return responseContents


def apply_execution(restApiCaller, tf_run_id):
    """
        Applyを実行する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_run_id: TerraformのRUN-ID
        RETRUN:
            response_array: RESTAPI返却値
    """
    api_uri = '/runs/%s/actions/apply' % (tf_run_id)
    response_array = restApiCaller.rest_call('POST', api_uri)

    return response_array


def apply_discard(restApiCaller, tf_run_id):
    """
        Applyを中止する(RUNを破棄する)
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_run_id: TerraformのRUN-ID
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/runs/%s/actions/discard' % (tf_run_id)
    response_array = restApiCaller.rest_call('POST', api_uri)

    return response_array


def get_workspace_state_version(restApiCaller, tf_organization_name, tf_workspace_name):
    """
        連携先TerraformからPlanの詳細を取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_organization_name: 対象のOrganization名
            tf_workspace_name: 対象のWorkspace名
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = "/state-versions?filter%5Bworkspace%5D%5Bname%5D=" + tf_workspace_name + "&filter%5Borganization%5D%5Bname%5D=" + tf_organization_name + "&page%5Bsize%5D=10"  # noqa: E501
    response_array = restApiCaller.rest_call('GET', api_uri)

    return response_array


def get_policy_set_list(restApiCaller, tf_organization_name):
    """
        連携先TerraformからPolicySetの一覧を取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_organization_name: 対象のOrganization名
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/organizations/%s/policy-sets' % (tf_organization_name)
    response_array = restApiCaller.rest_call('GET', api_uri)

    return response_array


def delete_relationships_workspace(restApiCaller, tf_manage_policy_set_id, tf_manage_workspace_id):
    """
        PolicySetからWorkspaceを切り離す
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_manage_variable_id: Terraformで管理しているVarableのID
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/policy-sets/%s/relationships/workspaces' % (tf_manage_policy_set_id)
    request_contents = {
        "data": [
            {"type": "workspaces", "id": tf_manage_workspace_id}
        ]
    }
    response_array = restApiCaller.rest_call('DELETE', api_uri, request_contents)

    return response_array


def delete_relationships_policy(restApiCaller, tf_manage_policy_set_id, policy_data):
    """
        PolicySetからPolicyを切り離す
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_manage_variable_id: Terraformで管理しているVarableのID
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/policy-sets/%s/relationships/policies' % (tf_manage_policy_set_id)
    request_contents = policy_data
    response_array = restApiCaller.rest_call('DELETE', api_uri, request_contents)

    return response_array


def relationships_workspace(restApiCaller, tf_manage_policy_set_id, tf_manage_workspace_id):
    """
        PolicySetにWorkspaceを紐付ける
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_manage_policy_set_id:Terraformで管理しているPolicySetのID
            tf_manage_workspace_id: Terraformで管理しているWorkspaceのID
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/policy-sets/%s/relationships/workspaces' % (tf_manage_policy_set_id)
    request_contents = {
        "data": [
            {"type": "workspaces", "id": tf_manage_workspace_id}
        ]
    }
    response_array = restApiCaller.rest_call('POST', api_uri, request_contents)

    return response_array


def relationships_policy(restApiCaller, tf_manage_policy_set_id, policy_data):
    """
        PolicySetにPolicyを紐付ける
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_manage_variable_id: Terraformで管理しているVarableのID
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/policy-sets/%s/relationships/policies' % (tf_manage_policy_set_id)
    request_contents = policy_data
    response_array = restApiCaller.rest_call('POST', api_uri, request_contents)

    return response_array


def get_policy_list(restApiCaller, tf_organization_name):
    """
        連携先TerraformからPolicyの一覧を取得する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_organization_name: 対象のOrganization名
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/organizations/%s/policies' % (tf_organization_name)
    response_array = restApiCaller.rest_call('GET', api_uri)

    return response_array


def create_policy(restApiCaller, tf_organization_name, policy_name, policy_file, policy_note):
    """
        Policyを作成する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_organization_name: Terraformで管理しているVarableのID
            policy_name: policy名
            policy_file: policyファイル名
            policy_note: policyの備考
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/organizations/%s/policies' % (tf_organization_name)
    request_contents = {
        "data": {
            "type": "policies",
            "attributes": {
                "enforce": [
                    {"path": policy_file, "mode": "hard-mandatory"}
                ],
                "name": policy_name,
                "description": policy_note
            }
        }
    }
    response_array = restApiCaller.rest_call('POST', api_uri, request_contents)

    return response_array


def update_policy(restApiCaller, tf_manage_policy_id, policy_name, policy_file, policy_note):
    """
        Policyを更新する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_manage_policy_id: Terraformで管理しているpolicyID
            policy_name: policy名
            policy_file: policyファイル名
            policy_note: policyの備考
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/policies/%s' % (tf_manage_policy_id)
    request_contents = {
        "data": {
            "type": "policies",
            "attributes": {
                "enforce": [
                    {"path": policy_file, "mode": "hard-mandatory"}
                ],
                "name": policy_name,
                "description": policy_note
            }
        }
    }
    response_array = restApiCaller.rest_call('PATCH', api_uri, request_contents)

    return response_array


def create_policy_set(restApiCaller, tf_organization_name, policy_set_name, policy_set_note):
    """
        PolicySetを作成する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_organization_name: Terraformで管理しているVarableのID
            policy_set_name: policySet名
            policy_set_note: policySetの備考
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/organizations/%s/policy-sets' % (tf_organization_name)
    request_contents = {
        "data": {
            "type": "policy-sets",
            "attributes": {
                "name": policy_set_name,
                "description": policy_set_note,
                "global": False
            }
        }
    }
    response_array = restApiCaller.rest_call('POST', api_uri, request_contents)

    return response_array


def update_policy_set(restApiCaller, tf_manage_policy_set_id, policy_set_name, policy_set_note):
    """
        PolicySetを更新する
        ARGS:
            restApiCaller: RESTAPIコールクラス
            tf_manage_policy_set_id: Terraformで管理しているpolicySetID
            policy_set_name: policySet名
            policy_set_note: policySetの備考
        RETRUN:
            response_array: RESTAPI返却値

    """
    api_uri = '/policy-sets/%s' % (tf_manage_policy_set_id)
    request_contents = {
        "data": {
            "type": "policy-sets",
            "attributes": {
                "name": policy_set_name,
                "description": policy_set_note,
                "global": False
            }
        }
    }
    response_array = restApiCaller.rest_call('PATCH', api_uri, request_contents)

    return response_array


def policy_file_upload(restApiCaller, tf_manage_policy_id, policy_file_data):
    """
        Terraformにtar.gzファイルをアップロードする
        ARGS:
            restApiCaller: RESTAPIコールクラス
            gztar_path: アップロードするtar.gzファイルのフルパス
            upload_url: アップロード先のURL
        RETRUN:
            response_array: RESTAPI返却値

    """
    # Moduleファイルアップロード用RESTAPIの特殊な仕様として、module_upload_flagをTrueとしてRESTAPIを実行する
    api_uri = '/policies/%s/upload' % (tf_manage_policy_id)
    # ####メモ：アップロードURLは通常のapi_urlなので、仕様をちょっと変える必要があるかも。
    # そのままupload_urlに入れちゃうと、httpsとかのプロトコルが違くなっちゃう。
    upload_url = None
    content = pathlib.Path(policy_file_data).read_bytes()
    header = None
    module_upload_flag = True
    response_array = restApiCaller.rest_call('PUT', api_uri, content, header, module_upload_flag, upload_url)

    return response_array
