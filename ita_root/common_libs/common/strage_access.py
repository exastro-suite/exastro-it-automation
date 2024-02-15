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
"""
/strage配下のファイルアクセスを/tmp経由で行うモジュール
"""
from flask import g
import re
import os
import uuid
import shutil


class strage_read:
    def __init__(self):
        strage_file_path = None
        tmp_file_path = None
        tmp_dir_path = None
        fd = None

    def open(self, file_path, mode = None):
        self.strage_file_path = file_path
        self.tmp_file_path = file_path
        root_dir = "^{}".format(os.environ.get('STORAGEPATH'))
        # ファイルパスが /strage か判定
        if re.search(root_dir, file_path) is not None:
            # ORGANIZATION_ID/WORKSPACE_IDのディレクトリが無いことを確認し、ORGANIZATION_ID/WORKSPACE_IDで一時ディレクトリ作成
            tmp_dir_path = "/tmp/{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
            if os.path.isdir(tmp_dir_path) is False:
                os.makedirs(tmp_dir_path)
            #  /strageから/tmpにファイルコピー(パーミッション維持)
            self.tmp_file_path = "{}/{}".format(tmp_dir_path, os.path.basename(file_path))
            shutil.copy2(self.strage_file_path, self.tmp_file_path)
        else:
           msg = "Paths other than /storage cannot be processed by this module. (path:{})".format(file_path)
           raise Exception(msg)
        # open
        if mode is not None:
            self.fd = open(self.tmp_file_path, mode)
        else:
            self.fd = open(self.tmp_file_path)
        return self.fd

    def read(self):
        # read
        return self.fd.read()

    def close(self, file_del = True):
        # close
        self.fd.close()
        if file_del is True:
            # /tmpの掃除
            self.remove()

    def remove(self):
        os.remove(self.tmp_file_path)


class strage_write:
    def __init__(self):
        strage_file_path = None
        tmp_file_path = None
        tmp_dir_path = None
        fd = None

    def open(self, file_path, mode = None):
        self.strage_file_path = file_path
        self.tmp_file_path = file_path
        root_dir = "^{}".format(os.environ.get('STORAGEPATH'))
        # ファイルパスが /strage か判定
        if re.search(root_dir, file_path) is not None:
            # 同名のディレクトリが無いことを確認し、uuid名で一時ディレクトリ作成
            tmp_dir_path = "/tmp/{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))
            if os.path.isdir(tmp_dir_path) is False:
                os.makedirs(tmp_dir_path)
            self.tmp_file_path = "{}/{}".format(tmp_dir_path, os.path.basename(file_path))
        # open
        self.fd = open(self.tmp_file_path, mode)
        return self.fd

    def write(self, value):
        # write
        resule = self.fd.write(value)

    def close(self, file_del = True):
        # close
        self.fd.close()
        if file_del is True:
            # /tmpから/stargeにコピー
            shutil.copy2(self.tmp_file_path, self.strage_file_path)
            # /tmpの掃除
            self.remove()

    def remove(self):
        os.remove(self.tmp_file_path)
