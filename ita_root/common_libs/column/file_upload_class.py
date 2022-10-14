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
            if option.get("file_data") is not None:
                # デコード値
                try:
                    decode_option = base64.b64decode(option["file_data"].encode())
                except Exception:
                    retBool = False
                    msg = g.appmsg.get_api_message('MSG-00011')
                    # msg = "base64decodeに失敗しました"
                    return retBool, msg

                # 禁止拡張子
                forbidden_extension_arry = self.objdbca.table_select("T_COMN_SYSTEM_CONFIG", "WHERE CONFIG_ID = %s", bind_value_list=['FORBIDDEN_UPLOAD'])
                
                forbidden_extension = forbidden_extension_arry[0]["VALUE"]
                
                # カラムの閾値を取得
                objcols = self.get_objcols()
                if objcols is not None:
                    if self.get_rest_key_name() in objcols:
                        dict_valid = self.get_dict_valid()
                        # 閾値(文字列長)
                        upload_max_size = dict_valid.get('upload_max_size')

                # 文字列長
                if max_length is not None:
                    check_val = len(str(val).encode('utf-8'))
                    if check_val != 0:
                        if int(min_length) <= check_val <= int(max_length):
                            retBool = True
                        else:
                            retBool = False
                            msg = g.appmsg.get_api_message('MSG-00008', [max_length, check_val])
                            return retBool, msg
                
                # ファイル名のチェック
                if preg_match is not None:
                    if len(preg_match) != 0:
                        pattern = re.compile(preg_match, re.DOTALL)
                        tmp_result = pattern.fullmatch(val)
                        if tmp_result is None:
                            retBool = False
                            msg = g.appmsg.get_api_message('MSG-00009', [preg_match, val])
                            return retBool, msg

                # バイト数比較
                if decode_option and upload_max_size is not None:
                    if len(decode_option) > int(upload_max_size):
                        retBool = False
                        msg = g.appmsg.get_api_message('MSG-00010', [upload_max_size, len(decode_option)])
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
            else:
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
        # 廃止の場合return
        if cmd_type == "Discard":
            return retBool
        
        if val is not None:
            if len(str(val)) != 0:
                decode_option = option.get("file_data")

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
                        
                # old配下にファイルアップロード
                if len(old_dir_path) > 0:
                    upload_file(old_dir_path, decode_option)  # noqa: F405
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
                    result = file_encode(old_file_path)  # noqa: F405
                else:
                    # ファイルの中身を読み込んでbase64に変換してreturn　読み込めなかったらFalse
                    result = file_encode(dir_path)  # noqa: F405

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
                        print(msg)
                        # return retBool, msg
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
                            retmp_recovery_pathc = tmp_recovery_path.get('old_file_path')
                            if retmp_recovery_pathc is not None:
                                if os.path.isfile(retmp_recovery_pathc) is True:
                                    os.symlink(retmp_recovery_pathc, dir_path)
                                    break
                    except Exception:
                        retBool = False
                        msg = g.appmsg.get_api_message('MSG-00017', [old_dir_path])
                        print(msg)
                        # return retBool, msg
        return retBool, msg
