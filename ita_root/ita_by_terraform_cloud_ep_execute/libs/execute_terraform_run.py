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
from common_libs.common.dbconnect import *  # noqa: F403
from common_libs.common.util import ky_decrypt
from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
from common_libs.driver.functions import operation_LAST_EXECUTE_TIMESTAMP_update
from libs.policySetting import policySetting
from libs.common_functions import update_execution_record
from common_libs.terraform_driver.cloud_ep.terraform_restapi import *  # noqa: F403
from common_libs.terraform_driver.common.by_execute import \
    get_type_info, encode_hcl, get_member_vars_ModuleVarsLinkID_for_hcl, generate_member_vars_array_for_hcl
import json
import os
import shutil


def execute_terraform_run(objdbca, instance_data, destroy_flag=False):  # noqa: C901
    """
        連携先Terraformに対しRUNを実行する
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            instance_data: 対象の作業インスタンスのレコード
            destroy_flag: 作業種別「リソース削除」の場合True
        RETRUN:
            boolean
    """
    try:
        # 変数定義
        execution_no = instance_data.get('EXECUTION_NO')
        run_mode = instance_data.get('RUN_MODE')
        movement_id = instance_data.get('MOVEMENT_ID')
        tf_workspace_id = instance_data.get('I_WORKSPACE_ID')
        tf_workspace_name = instance_data.get('I_WORKSPACE_NAME')
        tf_manage_workspace_id = ''  # Terraform側で管理しているWorkspaceのID
        operation_id = instance_data.get('OPERATION_ID')
        msg = ''
        log_msg = ''
        log_file_list = []
        update_data = {}
        update_data['EXECUTION_NO'] = execution_no

        # ディレクトリ/ログファイル定義
        base_dir = os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
        log_dir = base_dir + TFCloudEPConst.DIR_EXECUTE + '/' + execution_no + '/out'
        error_log = log_dir + '/error.log'
        plan_log = log_dir + '/plan.log'
        policy_check_log = log_dir + '/policyCheck.log'
        apply_log = log_dir + '/apply.log'
        temp_dir = base_dir + TFCloudEPConst.DIR_TEMP + '/' + execution_no
        variables_dir = temp_dir + '/variables'
        variables_json_file = variables_dir + '/variables.json'
        gztar_path = None
        populated_data_rename_path = None
        populated_data_rename_dir_path = None

        # ログ格納用ディレクトリを作成する
        if os.path.isdir(log_dir) is False:
            os.makedirs(log_dir)
        os.chmod(log_dir, 0o777)

        # エラーログファイルを生成
        if os.path.isfile(error_log) is False:
            with open(error_log, 'w'):
                pass

        # Planログファイルを生成
        if os.path.isfile(plan_log) is False:
            with open(plan_log, 'w'):
                pass
        log_file_list.append('plan.log')

        # PolicyCheckログファイルを生成
        if os.path.isfile(policy_check_log) is False:
            with open(policy_check_log, 'w'):
                pass
        log_file_list.append('policyCheck.log')

        if not run_mode == TFCloudEPConst.RUN_MODE_PLAN:
            # Applyログファイルを生成
            if os.path.isfile(apply_log) is False:
                with open(apply_log, 'w'):
                    pass
            log_file_list.append('apply.log')

        # インターフェース情報を取得する
        ret, interface_info_data = get_intarface_info_data(objdbca)  # noqa: F405
        if not ret:
            log_msg = g.appmsg.get_log_message("MSG-82001", [])
            g.applogger.info(log_msg)
            msg = g.appmsg.get_api_message("MSG-82001", [])
            raise Exception(msg)

        # RESTAPIコールクラス
        ret, restApiCaller = call_restapi_class(interface_info_data)  # noqa: F405
        if not ret:
            log_msg = g.appmsg.get_log_message("MSG-82002", [])
            g.applogger.info(log_msg)
            msg = g.appmsg.get_api_message("MSG-82002", [])
            raise Exception(msg)

        # tf_workspace_idをもとにORGANIZATION_WORKSPACEビューからレコードを取得
        where_str = 'WHERE WORKSPACE_ID = %s AND DISUSE_FLAG = %s'
        ret = objdbca.table_select(TFCloudEPConst.V_ORGANIZATION_WORKSPACE, where_str, [tf_workspace_id, 0])
        if not ret:
            g.applogger.debug(g.appmsg.get_log_message("MSG-82003", [tf_workspace_name]))  # 想定内エラーのためdebug
            msg = g.appmsg.get_api_message("MSG-82003", [tf_workspace_name])
            raise Exception(msg)

        # 対象のtf_organizationとtf_workspaceを特定する
        tf_organization_name = ret[0].get('ORGANIZATION_NAME')
        tf_workspace_name = ret[0].get('WORKSPACE_NAME')

        # [RESTAPI]連携先TerraformからOrganization一覧を取得
        g.applogger.info(g.appmsg.get_log_message("BKY-51007", [execution_no]))
        response_array = get_tf_organization_list(restApiCaller)  # noqa: F405
        response_status_code = response_array.get('statusCode')
        # ステータスコードが200以外の場合はエラー判定
        if not response_status_code == 200:
            log_msg = g.appmsg.get_log_message("MSG-82010", [])
            g.applogger.info(log_msg)
            msg = "[API Error]" + g.appmsg.get_api_message("MSG-82010", [])
            raise Exception(msg)
        g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

        # Organization一覧から、対象のtf_organization_nameが存在するかをチェック
        respons_contents_json = response_array.get('responseContents')
        respons_contents = json.loads(respons_contents_json)
        respons_contents_data = respons_contents.get('data')
        org_exist_flag = False
        for data in respons_contents_data:
            attributes = data.get('attributes')
            if tf_organization_name == attributes.get('name'):
                org_exist_flag = True
                break
        # OrganizationがTerraformに登録されていない場合はエラー
        if not org_exist_flag:
            g.applogger.debug(g.appmsg.get_log_message("MSG-82011", []))  # 想定内エラーのためdebug
            msg = g.appmsg.get_api_message("MSG-82011", [])
            raise Exception(msg)

        # [RESTAPI]連携先TerraformからWorkspace一覧を取得
        g.applogger.info(g.appmsg.get_log_message("BKY-51008", [execution_no]))
        response_array = get_tf_workspace_list(restApiCaller, tf_organization_name)  # noqa: F405
        response_status_code = response_array.get('statusCode')
        if not response_status_code == 200:
            log_msg = g.appmsg.get_log_message("MSG-82012", [])
            g.applogger.info(log_msg)
            msg = "[API Error]" + g.appmsg.get_api_message("MSG-82012", [])
            raise Exception(msg)
        g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

        # Workspace一覧から、対象のtf_workspace_nameが存在するかをチェック
        respons_contents_json = response_array.get('responseContents')
        respons_contents = json.loads(respons_contents_json)
        respons_contents_data = respons_contents.get('data')
        work_exist_flag = False
        for data in respons_contents_data:
            attributes = data.get('attributes')
            if tf_workspace_name == attributes.get('name'):
                tf_manage_workspace_id = data.get('id')  # Terraformで管理しているのWorkspaceIDを取得
                work_exist_flag = True
                terraform_auto_apply = attributes.get('auto-apply')
                break
        # WorkspaceがTerraformに登録されていない場合はエラー
        if not work_exist_flag:
            log_msg = g.appmsg.get_log_message("MSG-82003", [])  # 想定内エラーのためdebug
            g.applogger.info(log_msg)
            msg = g.appmsg.get_api_message("MSG-82003", [])
            raise Exception(msg)

        # WorkspaceのApplyMethodの設定がAuto Applyになっていないことをチェック。
        if run_mode == TFCloudEPConst.RUN_MODE_PLAN:
            if terraform_auto_apply is True:
                log_msg = g.appmsg.get_log_message("MSG-82004", [])  # 想定内エラーのためdebug
                g.applogger.info(log_msg)
                msg = g.appmsg.get_api_message("MSG-82004", [])
                raise Exception(msg)

        # -----[START]実行種別が「作業実行」「Plan確認」の場合のみ実施-----
        if not destroy_flag:
            # Operationの最終実施日を更新
            result = operation_LAST_EXECUTE_TIMESTAMP_update(objdbca, operation_id)
            if result[0] is True:
                objdbca.db_commit()
                g.applogger.debug(g.appmsg.get_log_message("BKY-10003", [execution_no]))

            # [RESTAPI]連携先Terraformに登録されているVariableの一覧を取得(削除対象を特定するため)
            g.applogger.info(g.appmsg.get_log_message("BKY-51009", [execution_no]))
            response_array = get_tf_workspace_var_list(restApiCaller, tf_manage_workspace_id)  # noqa: F405
            response_status_code = response_array.get('statusCode')
            if not response_status_code == 200:
                log_msg = g.appmsg.get_log_message("MSG-82014", [])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82014", [])
                raise Exception(msg)
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # [RESTAPI]取得したVariable一覧について、削除するRESTAPIを実行する
            g.applogger.info(g.appmsg.get_log_message("BKY-51010", [execution_no]))
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            for data in respons_contents_data:
                tf_manage_variable_id = data.get('id')
                response_array = delete_tf_workspace_var(restApiCaller, tf_manage_variable_id)  # noqa: F405
                response_status_code = response_array.get('statusCode')
                if not response_status_code == 204:
                    log_msg = g.appmsg.get_log_message("MSG-82015", [])
                    g.applogger.info(log_msg)
                    msg = "[API Error]" + g.appmsg.get_api_message("MSG-82015", [])
                    raise Exception(msg)
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # [RESTAPI]連携先Terraformに文字化け防止用の環境変数を設定する
            g.applogger.info(g.appmsg.get_log_message("BKY-51011", [execution_no]))
            key = 'TF_CLI_ARGS'
            value = '-no-color'
            response_array = create_tf_workspace_var(restApiCaller, tf_manage_workspace_id, key, value, hcl=False, sensitive=False, category="env")  # noqa: F405, E501
            response_status_code = response_array.get('statusCode')
            if not response_status_code == 201:
                log_msg = g.appmsg.get_log_message("MSG-82016", [])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82016", [])
                raise Exception(msg)
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # 連携先Terraformに代入値管理に登録されている値があれば、Variableを設定する
            ret = prepare_variables(objdbca, restApiCaller, instance_data, tf_manage_workspace_id)
            if not ret:
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82017", [])
                raise Exception(msg)
        # -----[END]実行種別が「作業実行」「Plan確認」の場合のみ実施-----

        # Policy関連の処理スタート
        policy_setting = policySetting(objdbca, TFCloudEPConst, restApiCaller, tf_organization_name, tf_workspace_name, tf_workspace_id, tf_manage_workspace_id, execution_no)  # noqa: F405, E501
        result, msg, policy_data_dict = policy_setting.policy_setting_main()
        if not result:
            raise Exception(msg)

        # -----[START]実行種別が「作業実行」「Plan確認」の場合のみ実施-----
        if not destroy_flag:
            # movement_idをもとにMovement-Module紐付テーブルから対象のレコードを取得
            where_str = 'WHERE MOVEMENT_ID = %s AND DISUSE_FLAG = %s'
            ret = objdbca.table_select(TFCloudEPConst.T_MOVEMENT_MODULE, where_str, [movement_id, 0])
            if not ret:
                g.applogger.debug(g.appmsg.get_log_message("MSG-82005", []))  # 想定内エラーのためdebug
                msg = g.appmsg.get_api_message("MSG-82005", [])
                raise Exception(msg)
            movement_module_list = ret

            # Movement-Module紐付から対象のModuleを取得
            module_id_list = []
            for record in movement_module_list:
                module_matter_id = record.get('MODULE_MATTER_ID')
                module_id_list.append(module_matter_id)

            # Module素材集から対象のファイル名を取得し格納する
            str_module_id_list = ', '.join(['%s'] * len(module_id_list))  # listの数だけIN()の中に%sを挿入する
            where_str = 'WHERE MODULE_MATTER_ID IN (' + str_module_id_list + ') AND DISUSE_FLAG = "0"'
            ret = objdbca.table_select(TFCloudEPConst.T_MODULE, where_str, module_id_list)
            if not ret:
                log_msg = g.appmsg.get_log_message("MSG-82006", [])
                g.applogger.info(log_msg)
                msg = g.appmsg.get_api_message("MSG-82006", [])
                raise Exception(msg)
            module_file_list = []
            for record in ret:
                module_matter_id = record.get('MODULE_MATTER_ID')
                module_matter_file = record.get('MODULE_MATTER_FILE')
                module_data = {'module_matter_id': module_matter_id, 'module_matter_file': module_matter_file}
                module_file_list.append(module_data)

            # 作業用tempディレクトリを作成する
            if os.path.isdir(temp_dir) is False:
                os.makedirs(temp_dir)
            os.chmod(temp_dir, 0o777)

            # 作業対象のファイルをtempディレクトリにコピーする
            module_file_dir = base_dir + TFCloudEPConst.DIR_MODULE
            for module_data in module_file_list:
                module_file_full_path = module_file_dir + '/' + module_data.get('module_matter_id') + '/' + module_data.get('module_matter_file')
                # ファイルのコピーを実行
                shutil.copy(module_file_full_path, temp_dir)

            # tempディレクトリにコピーしたファイルをtar.gzファイルにまとめる
            gztar_path = shutil.make_archive(base_name=temp_dir, format="gztar", root_dir=temp_dir)
            if os.path.exists(gztar_path) is False:
                log_msg = g.appmsg.get_log_message("MSG-82007", [])
                g.applogger.error(log_msg)
                msg = g.appmsg.get_api_message("MSG-82007", [])
                raise Exception(msg)

            # [RESTAPI]作成したtar.gzファイルをアップロードするためのURLを取得する
            g.applogger.info(g.appmsg.get_log_message("BKY-51037", [execution_no]))
            response_array = get_upload_url(restApiCaller, tf_manage_workspace_id)  # noqa: F405
            response_status_code = response_array.get('statusCode')
            if not response_status_code == 201:
                log_msg = g.appmsg.get_log_message("MSG-82029", [])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82029", [])
                raise Exception(msg)
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            attributes = respons_contents_data.get('attributes')
            upload_url = attributes.get('upload-url')
            cv_id = respons_contents_data.get('id')
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # [RESTAPI]作成したtar.gzファイルを連携先Terraformにアップロードする。
            g.applogger.info(g.appmsg.get_log_message("BKY-51038", [execution_no]))
            response_array = module_upload(restApiCaller, gztar_path, upload_url)  # noqa: F405
            if not response_status_code == 201:
                log_msg = g.appmsg.get_log_message("MSG-82030", [])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82030", [])
                raise Exception(msg)
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # [RESTAPI]連携先Terraformに登録されているVariableの一覧を取得(設定値を保存するため)
            g.applogger.info(g.appmsg.get_log_message("BKY-51009", [execution_no]))
            response_array = get_tf_workspace_var_list(restApiCaller, tf_manage_workspace_id)  # noqa: F405
            response_status_code = response_array.get('statusCode')
            if not response_status_code == 200:
                log_msg = g.appmsg.get_log_message("MSG-82014", [])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82014", [])
                raise Exception(msg)
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # 取得したVariable一覧から、variables.jsonを作成する(登録した代入値をまとめたファイル)
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            variables_list = []
            for data in respons_contents_data:
                variable_data = {}
                attributes = data.get('attributes')
                if attributes.get('category') == 'terraform':
                    variable_data['key'] = attributes.get('key')
                    variable_data['value'] = attributes.get('value')
                    variable_data['sensitive'] = attributes.get('sensitive')
                    variable_data['hcl'] = attributes.get('hcl')
                    variables_list.append(variable_data)

            # variables.jsonを格納するためのディレクトリを作成
            if os.path.isdir(variables_dir) is False:
                os.makedirs(variables_dir)
            os.chmod(variables_dir, 0o777)

            # variables.jsonファイルを書き出し
            with open(variables_json_file, 'w') as f:
                json.dump(variables_list, f, indent=4)

            # [RESTAPI]TerraformのRUNを実行する
            g.applogger.info(g.appmsg.get_log_message("BKY-51039", [execution_no]))
            response_array = create_run(restApiCaller, tf_manage_workspace_id, cv_id)  # noqa: F405
            response_status_code = response_array.get('statusCode')
            if not response_status_code == 201:
                log_msg = g.appmsg.get_log_message("MSG-82031", [])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82031", [])
                raise Exception(msg)
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # Terraform Runの実行返却値からRUN-IDを取得する
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            tf_run_id = respons_contents_data.get('id')

            # policy_id_listに値が入っていれば、policyファイルを投入データ用に入れるため、temp_dirにコピーする
            for policy_id, policy_data in policy_data_dict.items():
                policy_file_dir = base_dir + TFCloudEPConst.DIR_POLICY
                policy_file_full_path = policy_file_dir + '/' + policy_id + '/' + policy_data.get('policy_file')
                # ファイルのコピーを実行
                shutil.copy(policy_file_full_path, temp_dir)

            # 投入データ用のZIPファイルを作成する
            populated_data_path = shutil.make_archive(base_name=temp_dir, format="zip", root_dir=temp_dir)
            if os.path.exists(populated_data_path) is False:
                log_msg = g.appmsg.get_log_message("MSG-82008", [])
                g.applogger.error(log_msg)
                msg = g.appmsg.get_api_message("MSG-82008", [])
                raise Exception(msg)
            else:
                # zipファイル名を変更 [execution_no].zip > InputData_[execution_no].zip
                populated_data_rename_dir_path = base_dir + TFCloudEPConst.DIR_TEMP
                populated_data_rename_path = populated_data_rename_dir_path + '/InputData_' + execution_no + '.zip'
                os.rename(populated_data_path, populated_data_rename_path)
                if os.path.exists(populated_data_rename_path) is False:
                    log_msg = g.appmsg.get_log_message("MSG-82008", [])
                    g.applogger.error(log_msg)
                    msg = g.appmsg.get_api_message("MSG-82008", [])
                    raise Exception(msg)

            # 作業インスタンスのステータスを更新
            zip_file_name = "InputData_" + execution_no + ".zip"
            update_data['FILE_INPUT'] = zip_file_name
            update_data['TERRAFORM_RUN_ID'] = tf_run_id
            update_data['MULTIPLELOG_MODE'] = 1
            update_data['LOGFILELIST_JSON'] = json.dumps(log_file_list)
            update_data['STATUS_ID'] = TFCloudEPConst.STATUS_PROCESSING
            ret, execute_data = update_execution_record(objdbca, TFCloudEPConst, update_data, populated_data_rename_dir_path)
            if ret:
                objdbca.db_commit()
                g.applogger.debug(g.appmsg.get_log_message("BKY-51002", [execution_no]))
            else:
                log_msg = g.appmsg.get_log_message("BKY-50101", [])  # Failed to update status.
                g.applogger.error(log_msg)
                raise Exception(log_msg)

            # 一時利用ディレクトリを削除する
            shutil.rmtree(temp_dir)

            # tar.gzファイルとzipファイルを削除する
            os.remove(gztar_path)
            os.remove(populated_data_rename_path)
        # -----[END]実行種別が「作業実行」「Plan確認」の場合のみ実施-----
        # -----[START]実行種別が「リソース削除」の場合のみ実施-----
        else:
            # [RESTAPI]TerraformのDestroyを実行する
            g.applogger.info(g.appmsg.get_log_message("BKY-51040", [execution_no]))
            response_array = destroy_workspace(restApiCaller, tf_manage_workspace_id)  # noqa: F405
            response_status_code = response_array.get('statusCode')
            if not response_status_code == 201:
                log_msg = g.appmsg.get_log_message("MSG-82031", [])
                g.applogger.info(log_msg)
                msg = "[API Error]" + g.appmsg.get_api_message("MSG-82031", [])
                raise Exception(msg)
            g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

            # Terraform Runの実行返却値からRUN-IDを取得する
            respons_contents_json = response_array.get('responseContents')
            respons_contents = json.loads(respons_contents_json)
            respons_contents_data = respons_contents.get('data')
            tf_run_id = respons_contents_data.get('id')

            # 作業インスタンスのステータスを更新
            update_data['TERRAFORM_RUN_ID'] = tf_run_id
            update_data['MULTIPLELOG_MODE'] = 1
            update_data['LOGFILELIST_JSON'] = json.dumps(log_file_list)
            update_data['STATUS_ID'] = TFCloudEPConst.STATUS_PROCESSING
            ret, execute_data = update_execution_record(objdbca, TFCloudEPConst, update_data)
            if ret:
                objdbca.db_commit()
                g.applogger.debug(g.appmsg.get_log_message("BKY-51002", [execution_no]))
            else:
                log_msg = g.appmsg.get_log_message("BKY-50101", [])  # Failed to update status.
                g.applogger.error(log_msg)
                raise Exception(log_msg)
        # -----[END]実行種別が「リソース削除」の場合のみ実施-----

        return True

    except Exception as msg:
        # 受け取ったメッセージをerror_logに書き込み
        with open(error_log, 'w') as f:
            f.write(str(msg))

        # ディレクトリ/ファイル削除
        if temp_dir:
            if os.path.isdir(temp_dir) is True:
                shutil.rmtree(temp_dir)
        if gztar_path:
            if os.path.isfile(gztar_path) is True:
                os.remove(gztar_path)
        if populated_data_rename_path:
            if os.path.isfile(populated_data_rename_path) is True:
                os.remove(populated_data_rename_path)

        return False


def prepare_variables(objdbca, restApiCaller, instance_data, tf_manage_workspace_id):  # noqa: C901
    """
        代入値管理に登録された変数を、連携先TerraformのWorkspaceのVariablesに登録する。
        ARGS:
            objdbca: DB接クラス DBConnectWs()
            instancce_data: 作業実行データ
            restApiCaller: RESTAPIコールクラス
            tf_manage_workspace_id: Terraformで管理するWorkspaceのID
        RETRUN:
            boolean

    """
    vars_set_flag = False  # 変数追加処理を行うかの判定
    vars_data_arr = {}  # 対象の変数を格納する配列

    try:
        # 作業実行データ
        execution_no = instance_data['EXECUTION_NO']
        movement_id = instance_data['MOVEMENT_ID']
        operation_id = instance_data['OPERATION_ID']

        # operation_idとmovement_idから変数名と代入値を取得
        # 下記のSQLについて
        # `T_TERE_VALUE`.`MEMBER_VARS_ID` は、movementメンバー変数紐づけのID（`V_TERE_MVMT_VAR_MEMBER_LINK`.`MVMT_VAR_MEMBER_LINK_ID`）
        # なので　AS `MVMT_VAR_MEMBER_LINK_ID` と名づけ
        # `V_TERE_MVMT_VAR_MEMBER_LINK`.`CHILD_MEMBER_VARS_ID`
        # を　AS `MEMBER_VARS_ID` と名づける（メンバー変数テーブルのIDとして分かるように）
        sql = "SELECT \
                D_TERRAFORM_VARS_DATA.MODULE_VARS_LINK_ID, \
                D_TERRAFORM_VARS_DATA.VARS_NAME, \
                D_TERRAFORM_VARS_DATA.HCL_FLAG, \
                D_TERRAFORM_VARS_DATA.SENSITIVE_FLAG, \
                D_TERRAFORM_VARS_DATA.VARS_ENTRY, \
                D_TERRAFORM_VARS_DATA.MEMBER_VARS_ID, \
                D_TERRAFORM_VARS_DATA.ASSIGN_SEQ, \
                T_TERE_MOD_VAR_LINK.TYPE_ID, \
                V_TERE_VAR_MEMBER.VARS_ASSIGN_FLAG, \
                D_TERRAFORM_VARS_DATA.LAST_UPDATE_TIMESTAMP \
            FROM ( \
                SELECT \
                    `T_TERE_VALUE`.`ASSIGN_ID` AS `ASSIGN_ID`, \
                    `T_TERE_VALUE`.`EXECUTION_NO` AS `EXECUTION_NO`, \
                    `T_TERE_VALUE`.`OPERATION_ID` AS `OPERATION_ID`, \
                    `T_TERE_VALUE`.`MOVEMENT_ID` AS `MOVEMENT_ID`, \
                    `V_TERE_MVMT_VAR_LINK`.`MODULE_VARS_LINK_ID` AS `MODULE_VARS_LINK_ID`, \
                    `V_TERE_MVMT_VAR_LINK`.`VARS_NAME` AS `VARS_NAME`, \
                    `T_TERE_VALUE`.`VARS_ENTRY` AS `VARS_ENTRY`, \
                    `T_TERE_VALUE`.`MEMBER_VARS_ID` AS `MVMT_VAR_MEMBER_LINK_ID`, \
                    `V_TERE_MVMT_VAR_MEMBER_LINK`.`CHILD_MEMBER_VARS_ID` AS `MEMBER_VARS_ID`, \
                    `T_TERE_VALUE`.`ASSIGN_SEQ` AS `ASSIGN_SEQ`, \
                    `T_TERE_VALUE`.`HCL_FLAG` AS `HCL_FLAG`, \
                    `T_TERE_VALUE`.`SENSITIVE_FLAG` AS `SENSITIVE_FLAG`, \
                    `T_TERE_VALUE`.`DISUSE_FLAG` AS `DISUSE_FLAG`, \
                    `T_TERE_VALUE`.`LAST_UPDATE_TIMESTAMP` AS `LAST_UPDATE_TIMESTAMP` \
                FROM `T_TERE_VALUE`  \
                    LEFT JOIN `V_TERE_MVMT_VAR_LINK`  \
                        ON( \
                            `V_TERE_MVMT_VAR_LINK`.`MOVEMENT_ID` = `T_TERE_VALUE`.`MOVEMENT_ID` AND  \
                            `V_TERE_MVMT_VAR_LINK`.`MVMT_VAR_LINK_ID` = `T_TERE_VALUE`.`MVMT_VAR_LINK_ID` \
                        ) \
                    LEFT JOIN `V_TERE_MVMT_VAR_MEMBER_LINK`  \
                        ON( \
                            `V_TERE_MVMT_VAR_MEMBER_LINK`.`MOVEMENT_ID` = `T_TERE_VALUE`.`MOVEMENT_ID` AND  \
                            `V_TERE_MVMT_VAR_MEMBER_LINK`.`MVMT_VAR_MEMBER_LINK_ID` = `T_TERE_VALUE`.`MEMBER_VARS_ID` \
                        ) \
                WHERE \
                    T_TERE_VALUE.EXECUTION_NO = %s \
                    AND T_TERE_VALUE.OPERATION_ID = %s \
                    AND T_TERE_VALUE.MOVEMENT_ID = %s  \
                ) AS D_TERRAFORM_VARS_DATA \
                LEFT OUTER JOIN T_TERE_MOD_VAR_LINK \
                    ON D_TERRAFORM_VARS_DATA.MODULE_VARS_LINK_ID = T_TERE_MOD_VAR_LINK.MODULE_VARS_LINK_ID \
                LEFT OUTER JOIN V_TERE_VAR_MEMBER \
                    ON D_TERRAFORM_VARS_DATA.MEMBER_VARS_ID = V_TERE_VAR_MEMBER.CHILD_MEMBER_VARS_ID \
            WHERE \
                T_TERE_MOD_VAR_LINK.DISUSE_FLAG = '0' "
        records = objdbca.sql_execute(sql, [execution_no, operation_id, movement_id])

        # 代入値（変数）の有無フラグ
        vars_set_flag = False if len(records) == 0 else True
        # メンバー変数
        vars_list = []
        # メンバー変数以外の代入値
        member_vars_link_id_list = []

        for record in records:
            if "MEMBER_VARS_ID" in record and record["MEMBER_VARS_ID"] is not None:
                member_vars_link_id_list.append(record)
            else:
                vars_list.append(record)

        for vars in vars_list:
            vars_link_id = vars['MODULE_VARS_LINK_ID']
            vars_name = vars['VARS_NAME']
            vars_entry = vars['VARS_ENTRY']
            vars_assign_seq = vars['ASSIGN_SEQ']
            vars_type_id = vars['TYPE_ID']
            last_update_timestamp = vars['LAST_UPDATE_TIMESTAMP']
            vars_list = []

            # HCL設定を判定
            hcl_flag = False
            if vars['HCL_FLAG'] == '0':
                hcl_flag = False  # 0(OFF)ならfalse
            elif vars['HCL_FLAG'] == '1':
                hcl_flag = True  # 1(ON)ならtrue

            # Sensitive設定を判定
            sensitive_flag = False
            if vars['SENSITIVE_FLAG'] == '0':
                sensitive_flag = False  # 0(OFF)ならfalse
            elif vars['SENSITIVE_FLAG'] == '1':
                sensitive_flag = True  # 1(ON)ならtrue
                vars_entry = ky_decrypt(vars_entry)  # 具体値をデコード

            if vars_link_id not in vars_data_arr:
                vars_data_arr[vars_link_id] = {
                    'VARS_NAME': vars_name,
                    'VARS_ENTRY': vars_entry,
                    'ASSIGN_SEQ': vars_assign_seq,
                    'MEMBER_VARS_ID': [],
                    'HCL_FLAG': hcl_flag,
                    'SENSITIVE_FLAG': sensitive_flag,
                    'VARS_TYPE_ID': vars_type_id,
                    'VARS_LIST': {}
                }
            # 代入値順序のためにキーを生成
            vars_list_len = str(len(vars_data_arr[vars_link_id]['VARS_LIST']))
            if not vars_assign_seq:
                # 代入値順序の値がないものは、ソート時に後ろにいけるようにしておく
                key_name = vars_list_len + "_1_" + str(last_update_timestamp)
            else:
                key_name = str(vars_assign_seq) + "_0_" + str(last_update_timestamp)
            vars_data_arr[vars_link_id]['VARS_LIST'][key_name] = vars_entry

        for vars in member_vars_link_id_list:
            vars_link_id = vars['MODULE_VARS_LINK_ID']
            vars_name = vars['VARS_NAME']
            vars_entry = vars['VARS_ENTRY']
            vars_assign_seq = vars['ASSIGN_SEQ']
            vars_type_id = vars['TYPE_ID']
            # vars_type_info = get_type_info(vars_type_id)
            vars_member_vars = vars['MEMBER_VARS_ID']
            vars_assign_flag = vars["VARS_ASSIGN_FLAG"]  # 代入値系管理フラグ

            # HCL設定を判定
            hcl_flag = False

            # Sensitive設定を判定
            sensitive_flag = False
            if vars['SENSITIVE_FLAG'] == '0':
                sensitive_flag = False  # 0(OFF)ならFalse
            elif vars['SENSITIVE_FLAG'] == '1':
                sensitive_flag = True  # 1(ON)ならTrue
                vars_entry = ky_decrypt(vars_entry)  # 具体値をデコード

            if vars_link_id not in vars_data_arr:
                vars_data_arr[vars_link_id] = {
                    'VARS_NAME': vars_name,
                    'VARS_ENTRY': vars_entry,
                    'ASSIGN_SEQ': vars_assign_seq,
                    'MEMBER_VARS_ID': vars_member_vars,
                    'HCL_FLAG': hcl_flag,
                    'SENSITIVE_FLAG': sensitive_flag,
                    'VARS_TYPE_ID': vars_type_id,
                    'MEMBER_VARS_LIST': []
                }
            vars_data_arr[vars_link_id]['MEMBER_VARS_LIST'].append({
                'VARS_ENTRY': vars_entry,
                'ASSIGN_SEQ': vars_assign_seq,
                'MEMBER_VARS_ID': vars_member_vars,
                'SENSITIVE_FLAG': sensitive_flag,
                "VARS_ASSIGN_FLAG": vars_assign_flag
            })

        # Movementに紐づく代入値がある場合、代入値(Variables)登録処理を実行
        if vars_set_flag is True:
            for vars_link_id, data in vars_data_arr.items():
                var_key = data['VARS_NAME']
                var_value = data['VARS_ENTRY']
                # assign_seq = data['ASSIGN_SEQ']
                vars_list = data['VARS_LIST'] if 'VARS_LIST' in data else {}
                member_vars_list = data['MEMBER_VARS_LIST'] if 'MEMBER_VARS_LIST' in data else []
                hclFlag = data['HCL_FLAG']
                sensitiveFlag = data['SENSITIVE_FLAG']
                vars_type_id = data['VARS_TYPE_ID']
                vars_type_info = get_type_info(objdbca, TFCloudEPConst, vars_type_id)

                # HCL組み立て
                #########################################
                # 1.Module変数紐付けのタイプが配列型でない場合
                # 2.Module変数紐付けのタイプが配列型且つメンバー変数がない場合
                # 3.Module変数紐付けのタイプが配列型且つメンバー変数である場合
                #########################################
                # 1.Module変数紐付けのタイプが配列型でない場合
                if hclFlag is True or vars_type_info["MEMBER_VARS_FLAG"] == '0' and vars_type_info["ASSIGN_SEQ_FLAG"] == '0' and vars_type_info["ENCODE_FLAG"] == 0:  # noqa:E501
                    pass
                # 2.Module変数紐付けのタイプが配列型且つメンバー変数がない場合
                elif vars_type_info["MEMBER_VARS_FLAG"] == '0' and vars_type_info["ASSIGN_SEQ_FLAG"] == '1' and vars_type_info["ENCODE_FLAG"] == '1':
                    if len(vars_list) > 0:
                        # 代入値順序のために並び替え
                        vars_list2 = dict(sorted(vars_list.items()))
                        # HCLに変換
                        var_value = encode_hcl(list(vars_list2.values()))
                    hclFlag = True
                # 3.Module変数紐付けのタイプが配列型且つメンバー変数である場合
                else:
                    # HCL組み立て(メンバー変数)
                    if len(member_vars_list) > 0 and hclFlag is False:
                        tmp_member_vars_list = []
                        # １．対象変数のメンバー変数を全て取得（引数：Module変数紐付け/MODULE_VARS_LINK_ID）
                        trg_member_vars_records = get_member_vars_ModuleVarsLinkID_for_hcl(objdbca, TFCloudEPConst, vars_link_id)
                        # MEMBER_VARS_IDのリスト（重複の削除）
                        member_vars_ids_array = list(set([m.get('MEMBER_VARS_ID') for m in member_vars_list]))

                        # ２．配列型の変数を配列にする
                        for member_vars_id in member_vars_ids_array:
                            # メンバー変数IDからタイプ情報を取得する
                            key = [m.get('CHILD_MEMBER_VARS_ID') for m in trg_member_vars_records].index(member_vars_id)
                            type_info = get_type_info(objdbca, TFCloudEPConst, trg_member_vars_records[key]["CHILD_VARS_TYPE_ID"])
                            # メンバー変数対象でない配列型のみ配列型に形成する
                            if type_info["MEMBER_VARS_FLAG"] == '0' and type_info["ASSIGN_SEQ_FLAG"] == '1' and type_info["ENCODE_FLAG"] == '1':
                                tmp_list = {}
                                # 代入順序をキーインデックスにして具体値をtemp_aryに収める
                                for member_vars_data in member_vars_list:
                                    if member_vars_id == member_vars_data["MEMBER_VARS_ID"]:
                                        tmp_list[member_vars_data["ASSIGN_SEQ"]] = member_vars_data["VARS_ENTRY"]
                                # 並べ替え
                                tmp_list2 = dict(sorted(tmp_list.items()))
                                tmp_arr = list(tmp_list2.values())
                                sensitive_flag = False
                                if "SENSITIVE_FLAG" in trg_member_vars_records[key]:
                                    sensitive_flag = trg_member_vars_records[key]["SENSITIVE_FLAG"]
                                tmp_member_vars_list.append({
                                    "MEMBER_VARS": member_vars_id,
                                    "SENSITIVE_FLAG": sensitive_flag,
                                    "VARS_ENTRY": tmp_arr,
                                    "VARS_ASSIGN_FLAG": trg_member_vars_records[key]["VARS_ASSIGN_FLAG"]
                                })
                            else:
                                key = [m.get('MEMBER_VARS_ID') for m in member_vars_list].index(member_vars_id)
                                tmp_member_vars_list.append({
                                    "MEMBER_VARS": member_vars_id,
                                    "SENSITIVE_FLAG": member_vars_list[key]["SENSITIVE_FLAG"],
                                    "VARS_ENTRY": member_vars_list[key]["VARS_ENTRY"],
                                    "VARS_ASSIGN_FLAG": member_vars_list[key]["VARS_ASSIGN_FLAG"]
                                })

                        # MEMBER_VARS_LISTの中身を入れ替える
                        member_vars_list = tmp_member_vars_list

                        # ３．代入値管理で取得した値を置き換え
                        for member_vars_data in member_vars_list:
                            for trg_member_vars_record in trg_member_vars_records:
                                if member_vars_data["MEMBER_VARS"] == trg_member_vars_record["CHILD_MEMBER_VARS_ID"]:
                                    trg_member_vars_record["CHILD_MEMBER_VARS_VALUE"] = member_vars_data["VARS_ENTRY"]
                                    trg_member_vars_record["VARS_ENTRY_FLAG"] = '1'
                                    trg_member_vars_record["VARS_ASSIGN_FLAG"] = member_vars_data["VARS_ASSIGN_FLAG"]

                            # sensitive設定をチェック
                            # 対象代入値に一つでもsensitive設定があればseneitiveはON
                            if sensitiveFlag is False and member_vars_data["SENSITIVE_FLAG"] == '1':
                                sensitiveFlag = True

                        # ４．置換する値がなかった場合、エラーとする
                        err_id_list = []
                        for trg_member_vars_record in trg_member_vars_records:
                            if trg_member_vars_record["VARS_ENTRY_FLAG"] == '0' and trg_member_vars_record["VARS_ASSIGN_FLAG"] == '1':
                                err_id_list.append(trg_member_vars_record["CHILD_MEMBER_VARS_ID"])

                        if len(err_id_list) > 0:
                            ids_string = json.dumps(err_id_list)
                            # error_logにメッセージを追記
                            # メンバー変数の取得に失敗しました。ID:[]
                            g.applogger.info(ids_string)

                        # ５．取得したデータから配列を形成
                        trg_member_vars_arr = generate_member_vars_array_for_hcl(objdbca, TFCloudEPConst, trg_member_vars_records)
                        # ６．HCLに変換
                        var_value = encode_hcl(trg_member_vars_arr)
                        hclFlag = True

                # [RESTAPI]連携先Terraformにvariablesを設定する
                g.applogger.info(g.appmsg.get_log_message("BKY-51012", [execution_no, var_key]))
                response_array = create_tf_workspace_var(restApiCaller, tf_manage_workspace_id, var_key, var_value, hclFlag, sensitiveFlag, category="terraform")  # noqa: F405, E501
                response_status_code = response_array.get('statusCode')
                if not response_status_code == 201:
                    return False
                g.applogger.info(g.appmsg.get_log_message("BKY-51041", []))

    except Exception as msg:
        g.applogger.error(msg)
        return False

    return True
