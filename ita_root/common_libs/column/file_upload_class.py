# Copyright 2022 NEC Corporation#
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
import re
import os
import base64
import textwrap
import filecmp
import pathlib
from flask import g
from .column_class import Column
from common_libs.common import *  # noqa: F403


class FileUploadColumn(Column):
    """
    カラムクラス個別処理(FileUploadColumn)
    """
    def __init__(self, objdbca, objtable, rest_key_name, cmd_type):

        # カラムクラス名
        self.class_name = self.__class__.__name__
        # メッセージ
        self.message = ''
        # バリデーション閾値
        self.dict_valid = {}
        # テーブル情報
        self.objtable = objtable

        # テーブル名
        table_name = ''
        objmenu = objtable.get('MENUINFO')
        if objmenu is not None:
            table_name = objmenu.get('TABLE_NAME')
        self.table_name = table_name

        # カラム名
        col_name = ''
        objcols = objtable.get('COLINFO')
        if objcols is not None:
            objcol = objcols.get(rest_key_name)
            if objcol is not None:
                col_name = objcol.get('COL_NAME')

        self.col_name = col_name

        # rest用項目名
        self.rest_key_name = rest_key_name

        self.db_qm = "'"

        self.objdbca = objdbca

        self.cmd_type = cmd_type

    def check_basic_valid(self, val, option={}):
        """
            バリデーション処理
            ARGS:
                val:値
                dict_valid:バリデーション閾値
            RETRUN:
                True / エラーメッセージ
        """
        retBool = True
        min_length = 0
        max_length = 255
        # 閾値(最大値)
        upload_max_size = None
        # ファイル名正規表現　カンマとダブルクォートとタブとスラッシュと改行以外の文字
        preg_match = r"^[^,\"\t\/\r\n]*$"

        if val is not None:

            # 禁止拡張子
            forbidden_extension_arry = self.objdbca.table_select("T_COMN_SYSTEM_CONFIG", "WHERE CONFIG_ID = %s", bind_value_list=['FORBIDDEN_UPLOAD'])  # noqa:E501
            forbidden_extension = forbidden_extension_arry[0]["VALUE"]

            # カラムの閾値を取得
            objcols = self.get_objcols()
            if objcols is not None:
                if self.get_rest_key_name() in objcols:
                    dict_valid = self.get_dict_valid()
                    # 閾値(文字列長)
                    upload_max_size = dict_valid.get('upload_max_size')

            # Organization毎のアップロードファイルサイズ上限取得
            org_upload_file_size_limit = get_org_upload_file_size_limit(g.get("ORGANIZATION_ID"))

            # 比較するアップロードファイルサイズ上限を設定
            if upload_max_size is None and org_upload_file_size_limit is None:
                compare_upload_max_size = None
            elif upload_max_size is not None and org_upload_file_size_limit is None:
                compare_upload_max_size = upload_max_size
            elif upload_max_size is None and org_upload_file_size_limit is not None:
                compare_upload_max_size = org_upload_file_size_limit
            else:
                if int(upload_max_size) < int(org_upload_file_size_limit):
                    compare_upload_max_size = upload_max_size
                else:
                    compare_upload_max_size = org_upload_file_size_limit

            # ファイル名の文字列長チェック
            if max_length is not None:
                check_val = len(str(val).encode('utf-8'))
                if check_val != 0:
                    if int(min_length) <= check_val <= int(max_length):
                        retBool = True
                    else:
                        retBool = False
                        msg = g.appmsg.get_api_message('MSG-00008', [max_length, check_val])
                        return retBool, msg

            # ファイル名の正規表現チェック
            if preg_match is not None:
                if len(preg_match) != 0:
                    pattern = re.compile(preg_match, re.DOTALL)
                    tmp_result = pattern.fullmatch(val)
                    if tmp_result is None:
                        retBool = False
                        msg = g.appmsg.get_api_message('MSG-00009', [preg_match, val])
                        return retBool, msg

            # 禁止拡張子チェック
            if forbidden_extension is not None:
                forbidden_extensions = forbidden_extension.split(';')
                extension_arr = os.path.splitext(val)
                extension_val = extension_arr[1].lower()
                # リストの中身を全て小文字に変更
                forbidden_extensions = list(map(lambda e: e.lower(), forbidden_extensions))
                if extension_val in forbidden_extensions:
                    msg = g.appmsg.get_api_message('MSG-00022', [forbidden_extensions, extension_val])
                    retBool = False
                    return retBool, msg

            # ファイルがある場合
            if option.get("file_path") is not None and len(option.get("file_path")) > 0:
                # ファイルサイズを取得
                file_size = os.path.getsize(option.get("file_path"))

                # バイト数比較
                if compare_upload_max_size is not None:
                    if file_size > int(compare_upload_max_size):
                        retBool = False
                        msg = g.appmsg.get_api_message('MSG-00010', [compare_upload_max_size, file_size])
                        return retBool, msg

            elif option.get('cmd_type') == 'Register':
                # 登録時、ファイル名はあるけどファイルの実態がない場合はエラー
                retBool = False
                msg = g.appmsg.get_api_message('MSG-00012', [val])
                return retBool, msg
            elif option.get('cmd_type') == 'Update':
                current_file_path = option.get("current_parameter").get("file_path").get(option.get("rest_key_name"))
                # 更新時、ファイル名はあるけどファイルの実態がない、かつ既存レコードにもファイルの実態がない場合はエラー
                if current_file_path is None or len(current_file_path) == 0:
                    retBool = False
                    msg = g.appmsg.get_api_message('MSG-00012', [val])
                    return retBool, msg
        return retBool,

    def after_iud_common_action(self, val="", option={}):
        """
            カラムクラス毎の個別処理 レコード操作後
            ARGS:
                val:値
                option:オプション
            RETRUN:
                True / エラーメッセージ
        """
        retBool = True
        cmd_type = self.get_cmd_type()
        copy_flg = False
        move_flg = False

        # 廃止の場合return
        if cmd_type == "Discard":
            return retBool,
        # ファイル名の設定がない場合return
        if val is None or len(str(val)) == 0:
            return retBool,

        current_file_name = option.get("current_parameter").get("parameter").get(option.get("rest_key_name"))
        current_file_path = option.get("current_parameter").get("file_path").get(option.get("rest_key_name"))
        entry_file_name = option.get("entry_parameter").get("parameter").get(option.get("rest_key_name"))
        entry_file_path = option.get("entry_parameter").get("file_path").get(option.get("rest_key_name"))

        # ファイルパスがない場合
        if entry_file_path is None:
            # ファイル名変更があれば処理対象
            if current_file_name != entry_file_name and current_file_path is not None and os.path.isfile(current_file_path):
                copy_flg = True

        # ファイルパスがある場合
        else:
            # 登録の場合は処f理対象
            if cmd_type == "Register":
                move_flg = True
            # 更新前のファイルがないなら処理対象
            elif current_file_name is None or len(current_file_name) == 0:
                move_flg = True
            # ファイル名変更があれば処理対象
            elif current_file_name != entry_file_name:
                move_flg = True
            # ファイルの内容に変更があれば処理対象
            elif filecmp.cmp(current_file_path, entry_file_path, shallow=False) is False:
                move_flg = True

        # 処理対象でない場合return
        if copy_flg is False and move_flg is False:
            return retBool,

        uuid = option["uuid"]
        uuid_jnl = option["uuid_jnl"]
        workspace_id = g.get("WORKSPACE_ID")
        menu_id = self.get_menu()
        rest_name = self.get_rest_key_name()

        # ファイルパス取得
        ret = self.get_file_upload_place()
        if not ret:
            path = get_upload_file_path(workspace_id, menu_id, uuid, rest_name, val, uuid_jnl)   # noqa:F405
        else:
            path = get_upload_file_path_specify(workspace_id, ret, uuid, val, uuid_jnl)   # noqa:F405

        dir_path = path["file_path"]
        old_dir_path = path["old_file_path"]
        os.makedirs(os.path.dirname(old_dir_path))

        if copy_flg:
            shutil.copy(current_file_path, old_dir_path)

        if move_flg:
            # old配下にファイルアップロード
            if len(old_dir_path) > 0:
                if os.path.isfile(entry_file_path):
                    shutil.copy(entry_file_path, old_dir_path)
            else:
                retBool = False
                msg = g.appmsg.get_api_message('MSG-00013', [])
                return retBool, msg

        # 更新、復活の場合シンボリックリンクを削除
        if cmd_type == "Update" or cmd_type == "Restore":
            # 更新前のファイルパス取得
            filepath = os.path.dirname(dir_path)
            # 更新前のファイル名取得
            filelist = []
            for f in os.listdir(filepath):
                if os.path.isfile(os.path.join(filepath, f)):
                    filelist.append(f)
            if len(filelist) != 0:
                old_file_path = filepath + "/" + filelist[0]

                try:
                    os.unlink(old_file_path)
                except Exception:
                    retBool = False
                    msg = g.appmsg.get_api_message('MSG-00014', [old_file_path])
                    return retBool, msg

        # シンボリックリンクが既にある場合は削除してから作成を行う
        if os.path.isfile(dir_path):
            os.unlink(dir_path)

        # シンボリックリンク作成
        try:
            os.symlink(old_dir_path, dir_path)
        except Exception:
            retBool = False
            msg = g.appmsg.get_api_message('MSG-00015', [old_dir_path, dir_path])
            return retBool, msg


        return retBool,

    def get_file_data(self, file_name, target_uuid, target_uuid_jnl=''):
        """
            ファイル(base64)を取得
            ARGS:
                file_name:ファイル名
                target_uuid:uuid
                target_uuid_jnl:uuid
            RETRUN:
                base64 string
        """
        result = None


        if file_name is not None:
            if len(str(file_name)) != 0:
                workspace_id = g.get("WORKSPACE_ID")
                menu_id = self.get_menu()
                rest_name = self.get_rest_key_name()

                ret = self.get_file_upload_place()
                if not ret:
                    path = get_upload_file_path(workspace_id, menu_id, target_uuid, rest_name, file_name, target_uuid_jnl)   # noqa:F405
                else:
                    path = get_upload_file_path_specify(workspace_id, ret, target_uuid, file_name, target_uuid_jnl)   # noqa:F405
                dir_path = path["file_path"]
                old_file_path = path["old_file_path"]
                if target_uuid_jnl:
                    # target_uuid_jnl指定時
                    # ファイルの中身を読み込んでbase64に変換してreturn　読み込めなかったらFalse
                    result = file_encode(old_file_path)  # noqa: F405
                    # 履歴からファイルの実態まで検索
                    if isinstance(result, str) and len(result) == 0:
                        target_uuid_jnls = []
                        column_list, primary_key_list = self.objdbca.table_columns_get(self.get_table_name())
                        self.set_column_list(column_list)
                        self.set_primary_key(primary_key_list[0])
                        query_str = textwrap.dedent("""
                            SELECT * FROM `{table_name}`
                            WHERE `{primary_key}` = %s
                            AND `DISUSE_FLAG` = 0
                            AND `JOURNAL_REG_DATETIME` <
                                (
                                    SELECT `JOURNAL_REG_DATETIME` FROM `{table_name}`
                                    WHERE `JOURNAL_SEQ_NO` = %s
                                    ORDER BY `JOURNAL_REG_DATETIME` DESC LIMIT 1
                                )
                        """).format(table_name=f"{self.get_table_name()}_JNL", primary_key=self.get_primary_key()).strip()
                        query_result = self.objdbca.sql_execute(query_str, [target_uuid, target_uuid_jnl])
                        target_uuid_jnls = [ _row["JOURNAL_SEQ_NO"] for _row in query_result] if isinstance(query_result, list) else []
                        target_uuid_jnls.append('00000000-0000-0000-0000-000000000000')   # 2.3.0 以下対応
                        for _tuj in target_uuid_jnls:
                            if not ret:
                                path = get_upload_file_path(workspace_id, menu_id, target_uuid, rest_name, file_name, _tuj)   # noqa:F405
                            else:
                                path = get_upload_file_path_specify(workspace_id, ret, target_uuid, file_name, _tuj)   # noqa:F405
                            if os.path.isfile(path["old_file_path"]):
                                old_file_path = path["old_file_path"]
                                break
                        result = file_encode(old_file_path)  # noqa: F405

                    if not os.path.isfile(old_file_path):
                        return None
                else:
                    if not os.path.isfile(dir_path):
                        return None
                    # ファイルの中身を読み込んでbase64に変換してreturn　読み込めなかったらFalse
                    result = file_encode(dir_path)  # noqa: F405

        return result

    def get_decrypt_file_data(self, file_name, target_uuid, target_uuid_jnl=''):
        """
            複合化されたファイル(base64)を取得
            ARGS:
                file_name:ファイル名
                target_uuid:uuid
                target_uuid_jnl:uuid
            RETRUN:
                base64 string
        """
        result = None

        if file_name is not None:
            if len(file_name) != 0:
                workspace_id = g.get("WORKSPACE_ID")
                menu_id = self.get_menu()
                rest_name = self.get_rest_key_name()

                ret = self.get_file_upload_place()
                if not ret:
                    path = get_upload_file_path(workspace_id, menu_id, target_uuid, rest_name, file_name, target_uuid_jnl)   # noqa:F405
                else:
                    path = get_upload_file_path_specify(workspace_id, ret, target_uuid, file_name, target_uuid_jnl)   # noqa:F405
                dir_path = path["file_path"]
                old_file_path = path["old_file_path"]
                if target_uuid_jnl:
                    # target_uuid_jnl指定時
                    # ファイルの中身を読み込んでbase64に変換してreturn　読み込めなかったらFalse
                    result = file_decode(old_file_path)  # noqa: F405
                    # 履歴からファイルの実態まで検索
                    if isinstance(result, str) and len(result) == 0:
                        target_uuid_jnls = []
                        column_list, primary_key_list = self.objdbca.table_columns_get(self.get_table_name())
                        self.set_column_list(column_list)
                        self.set_primary_key(primary_key_list[0])
                        query_str = textwrap.dedent("""
                            SELECT * FROM `{table_name}`
                            WHERE `{primary_key}` = %s
                            AND `DISUSE_FLAG` = 0
                            AND `JOURNAL_REG_DATETIME` <
                                (
                                    SELECT `JOURNAL_REG_DATETIME` FROM `{table_name}`
                                    WHERE `JOURNAL_SEQ_NO` = %s
                                    ORDER BY `JOURNAL_REG_DATETIME` DESC LIMIT 1
                                )
                        """).format(table_name=f"{self.get_table_name()}_JNL", primary_key=self.get_primary_key()).strip()
                        query_result = self.objdbca.sql_execute(query_str, [target_uuid, target_uuid_jnl])
                        target_uuid_jnls = [ _row["JOURNAL_SEQ_NO"] for _row in query_result] if isinstance(query_result, list) else []
                        target_uuid_jnls.append('00000000-0000-0000-0000-000000000000')   # 2.3.0 以下対応
                        for _tuj in target_uuid_jnls:
                            if not ret:
                                path = get_upload_file_path(workspace_id, menu_id, target_uuid, rest_name, file_name, _tuj)   # noqa:F405
                            else:
                                path = get_upload_file_path_specify(workspace_id, ret, target_uuid, file_name, _tuj)   # noqa:F405
                            if os.path.isfile(path["old_file_path"]):
                                old_file_path = path["old_file_path"]
                                break
                        result = file_decode(old_file_path)  # noqa: F405

                    if not os.path.isfile(old_file_path):
                        return None
                else:
                    # ファイルの中身を読み込んでbase64に変換してreturn　読み込めなかったらFalse
                    result = file_decode(dir_path)  # noqa: F405

        return result

    def get_file_data_path(self, file_name, target_uuid, target_uuid_jnl='', file_chk=False):
        """
            ファイルのパスを取得
            ARGS:
                file_name:ファイル名
                target_uuid:uuid
                target_uuid_jnl:uuid
            RETRUN:
                file_path string
        """
        result = None

        if file_name is not None:
            if len(file_name) != 0:
                workspace_id = g.get("WORKSPACE_ID")
                menu_id = self.get_menu()
                rest_name = self.get_rest_key_name()

                ret = self.get_file_upload_place()
                if not ret:
                    path = get_upload_file_path(workspace_id, menu_id, target_uuid, rest_name, file_name, target_uuid_jnl)   # noqa:F405
                else:
                    path = get_upload_file_path_specify(workspace_id, ret, target_uuid, file_name, target_uuid_jnl)   # noqa:F405
                dir_path = path["file_path"]
                old_file_path = path["old_file_path"]
                if target_uuid_jnl:
                    result = old_file_path  # noqa: F405
                    if file_chk is True:
                        # target_uuid_jnl指定時
                        # ファイルの中身を読み込んでbase64に変換してreturn　読み込めなかったらFalse
                        result = file_encode(old_file_path)  # noqa: F405
                        if result is False or result == "":
                            result = None
                else:
                    result = dir_path  # noqa: F405
                    if file_chk is True:
                        # ファイルの中身を読み込んでbase64に変換してreturn　読み込めなかったらFalse
                        result = file_encode(dir_path)  # noqa: F405
                        if result is False or result == "":
                            result = None

        return result

    def after_iud_restore_action(self, val="", option={}):
        """
            カラムクラス毎の個別処理 レコード操作後の状態回復処理
            ARGS:
                option:オプション
            RETRUN:
                True / エラーメッセージ
        """
        retBool = True
        msg = ''
        cmd_type = self.get_cmd_type()

        # 廃止の場合return
        if cmd_type == "Discard":
            return retBool, msg

        if val is not None:
            if len(str(val)) != 0:
                uuid = option["uuid"]
                uuid_jnl = option["uuid_jnl"]
                workspace_id = g.get("WORKSPACE_ID")
                menu_id = self.get_menu()
                rest_name = self.get_rest_key_name()

                # 削除対象のold配下のファイルパス取得
                ret = self.get_file_upload_place()
                if not ret:
                    path = get_upload_file_path(workspace_id, menu_id, uuid, rest_name, val, uuid_jnl)   # noqa:F405
                else:
                    path = get_upload_file_path_specify(workspace_id, ret, uuid, val, uuid_jnl)   # noqa:F405
                dir_path = path["file_path"]
                old_dir_path = path["old_file_path"]

                # ファイルの削除
                if cmd_type != "Discard":
                    try:
                        # シンボリックリンク,oldのファイル,ディレクトリの削除
                        os.unlink(dir_path)

                        os.remove(old_dir_path)

                        os.rmdir(old_dir_path.replace(val, ''))
                        # 登録時は、対象のIDのディレクトリ削除
                        if cmd_type == "Register":
                            os.rmdir(dir_path.replace(val, ''))

                    except Exception:
                        retBool = False
                        msg = g.appmsg.get_api_message('MSG-00016', [old_dir_path])

                    try:
                        # ファイルの更新があった最終更新時点のファイルでシンボリックリンク生成
                        for jnlid in option.get('target_jnls'):
                            # JNLのoldのファイルパス取得
                            jnl_id = jnlid.get('JOURNAL_SEQ_NO')
                            jnl_val = jnlid.get(self.get_col_name())
                            ret = self.get_file_upload_place()
                            if not ret:
                                tmp_recovery_path = get_upload_file_path(workspace_id, menu_id, uuid, rest_name, jnl_val, jnl_id)   # noqa:F405
                            else:
                                tmp_recovery_path = get_upload_file_path_specify(workspace_id, ret, uuid, jnl_val, jnl_id)   # noqa:F405
                            recovery_path = tmp_recovery_path.get('file_path')
                            old_recovery_path = tmp_recovery_path.get('old_file_path')
                            if old_recovery_path is not None:
                                if os.path.isfile(old_recovery_path) is True:
                                    os.symlink(old_recovery_path, recovery_path)
                                    break
                    except Exception:
                        retBool = False
                        msg = g.appmsg.get_api_message('MSG-00017', [old_dir_path])

        return retBool, msg


    def get_file_path_info(self, file_name, target_uuid, target_uuid_jnl='', journal_type='1'):
        """
            ファイル配置先のパス情報を取得
            ARGS:
                file_name:ファイル名
                target_uuid: uuid
                target_uuid_jnl: uuid
                journal_type:
                    "1": 全ての履歴 - ファイル配置先(ファイル変更が発生した履歴ID)のパス
                    "2": 最新の履歴のみ - ファイル配置先(最後に変更した履歴ID)のパス
            RETRUN:
                result {} / None
                {
                    name: File name
                    class_name: Column class name
                    dst: SymbolicLink Path,
                    src: File Path
                }
        """
        result = None
        if file_name is not None and len(file_name) != 0:
            organization_id = g.get("ORGANIZATION_ID")
            workspace_id = g.get("WORKSPACE_ID")
            menu_id = self.get_menu()
            rest_name = self.get_rest_key_name()

            ret = self.get_file_upload_place()
            if not ret:
                path = get_upload_file_path(workspace_id, menu_id, target_uuid, rest_name, file_name, target_uuid_jnl)   # noqa:F405
            else:
                path = get_upload_file_path_specify(workspace_id, ret, target_uuid, file_name, target_uuid_jnl)   # noqa:F405

            dir_path = path["file_path"]
            old_file_path = path["old_file_path"]
            entity_file_path = path["old_file_path"]

            # 履歴からファイルの配置先まで検索
            if os.path.isfile(old_file_path) is False:
                target_uuid_jnls = []
                column_list, primary_key_list = self.objdbca.table_columns_get(self.get_table_name())
                self.set_column_list(column_list)
                self.set_primary_key(primary_key_list[0])
                if journal_type == "1":
                    query_str = textwrap.dedent("""
                        SELECT * FROM `{table_name}`
                        WHERE `{primary_key}` = %s
                        AND `DISUSE_FLAG` = 0
                        ORDER BY `JOURNAL_REG_DATETIME` DESC
                    """).format(table_name=f"{self.get_table_name()}_JNL", primary_key=self.get_primary_key()).strip()
                else:
                    query_str = textwrap.dedent("""
                        SELECT * FROM `{table_name}`
                        WHERE `{primary_key}` = %s
                        ORDER BY `JOURNAL_REG_DATETIME` DESC
                    """).format(table_name=f"{self.get_table_name()}_JNL", primary_key=self.get_primary_key()).strip()
                query_result = self.objdbca.sql_execute(query_str, [target_uuid])
                target_uuid_jnls = [ _row["JOURNAL_SEQ_NO"] for _row in query_result] if isinstance(query_result, list) else []
                for _tuj in target_uuid_jnls:
                    if not ret:
                        path = get_upload_file_path(workspace_id, menu_id, target_uuid, rest_name, file_name, _tuj)   # noqa:F405
                    else:
                        path = get_upload_file_path_specify(workspace_id, ret, target_uuid, file_name, _tuj)   # noqa:F405
                    # 最新のファイル配置先を検索
                    if os.path.isfile(path["old_file_path"]):
                        old_file_path = path["old_file_path"]
                        entity_file_path = path["old_file_path"]
                        # エクスポート時(履歴なし)、履歴IDを最後に変更した履歴IDに置換
                        if journal_type == "2":
                            old_file_path = path["old_file_path"].replace(f"/old/{_tuj}/", f"/old/{target_uuid_jnls[0]}/")
                        break
            result = {}
            result["name"] = file_name
            result["class_name"] = self.class_name
            result["dst"] = dir_path.replace(f"/storage/{organization_id}/{workspace_id}", "")
            result["src"] = old_file_path.replace(f"/storage/{organization_id}/{workspace_id}", "")
            result["ori_dst"] = dir_path
            result["ori_src"] = old_file_path
            result["entity"] = entity_file_path if entity_file_path != "" else old_file_path

        return result