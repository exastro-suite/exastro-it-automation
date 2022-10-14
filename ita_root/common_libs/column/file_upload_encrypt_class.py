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
import os
import base64
from flask import g

from .file_upload_class import FileUploadColumn
from common_libs.common import *  # noqa: F403


class FileUploadEncryptColumn(FileUploadColumn):
    """
    カラムクラス個別処理(FileUploadEncryptColumn)
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
            if len(val) != 0:
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
                    encrypt_upload_file(old_dir_path, decode_option)  # noqa: F405
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
