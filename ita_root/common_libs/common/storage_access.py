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
/storage配下のファイルアクセスを/tmp経由で行うモジュール
"""
from flask import g
import re
import os
import uuid
import shutil
from pathlib import Path
import traceback
import inspect

class storage_base:
    def make_temp_path(self, file_path):
        # ルートパスを/tmpに置き換える
        tmp_dir_path = re.sub(os.environ.get('STORAGEPATH'), "/tmp/", os.path.dirname(file_path))
        # ディレクトリが無いことを確認
        if os.path.isdir(tmp_dir_path) is False:
            os.makedirs(tmp_dir_path)
        tmp_file_path = "{}/{}".format(tmp_dir_path, os.path.basename(file_path))
        return tmp_file_path

    def path_check(self, file_path):
        root_dir = "^{}".format(os.environ.get('STORAGEPATH'))
        # ファイルパスが /storage か判定
        if re.search(root_dir, file_path) is not None:
            return True
        else:
            return False

    def DebugPrint(title, log):
        frame = inspect.currentframe().f_back
        log = '<<%s>><<%s>><<%s>>%s\n%s\n' % (os.path.basename(frame.f_code.co_filename), frame.f_code.co_name, str(frame.f_lineno), str(title), str(log))
        print(log)

class storage_read(storage_base):
    def __init__(self):
        storage_file_path = None
        tmp_file_path = None
        tmp_dir_path = None
        storage_path_flg = False
        fd = None

    def open(self, file_path, mode = None):
        self.storage_file_path = file_path
        self.tmp_file_path = file_path
        root_dir = "^{}".format(os.environ.get('STORAGEPATH'))
        # ファイルパスが /storage か判定
        self.storage_flg = self.path_check(file_path)
        if self.storage_flg is True:
            self.tmp_file_path = self.make_temp_path(file_path)
            #  /storageから/tmpにファイルコピー(パーミッション維持)
            shutil.copy2(self.storage_file_path, self.tmp_file_path)
        else:
            self.tmp_file_path = file_path
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
        if self.storage_flg is True:
            if file_del is True:
                # /tmpの掃除
                self.remove()

    def remove(self):
        if os.path.isfile(self.tmp_file_path) is True:
            os.remove(self.tmp_file_path)


class storage_write(storage_base):
    def __init__(self):
        storage_file_path = None
        tmp_file_path = None
        tmp_dir_path = None
        storage_flg = False
        fd = None

    def open(self, file_path, mode = None):
        self.storage_file_path = file_path
        self.tmp_file_path = file_path
        root_dir = "^{}".format(os.environ.get('STORAGEPATH'))
        # ファイルパスが /storage か判定
        self.storage_flg = self.path_check(file_path)
        if self.storage_flg is True:
            self.tmp_file_path = self.make_temp_path(file_path)
            # open('xxx', 'a')のケースがあるのでファイルコピー
            if os.path.isfile(file_path) is True:
                shutil.copy2(self.storage_file_path, self.tmp_file_path)
        else:
            self.tmp_file_path = file_path
        # open
        self.fd = open(self.tmp_file_path, mode)
        return self.fd

    def write(self, value):
        # write
        resule = self.fd.write(value)

    def close(self, file_del = True):
        # close
        self.fd.close()
        if self.storage_flg is True:
            # /tmpから/stargeにコピー
            shutil.copy2(self.tmp_file_path, self.storage_file_path)
            if file_del is True:
                # /tmpの掃除
                self.remove()

    def remove(self):
        if os.path.isfile(self.tmp_file_path) is True:
            os.remove(self.tmp_file_path)

class storage_write_text(storage_base):
    def write_text(self, file_path, value, encoding="utf-8"):
        # ルートパスを判定
        storage_flg = self.path_check(file_path)
        if storage_flg is True:
            # /storage
            tmp_file_path = self.make_temp_path(file_path)
        else:
            # not /storage
            tmp_file_path = file_path

        Path(tmp_file_path).write_text(value, encoding=encoding)
        if storage_flg is True:
            # /tmpから/stargeにコピー
            shutil.copy2(tmp_file_path, file_path)
            # /tmpの掃除
            if os.path.isfile(self.tmp_file_path) is True:
                os.remove(tmp_file_path)

class storage_read_text(storage_base):
    def read_text(self, file_path, encoding="utf-8"):
        # ルートパスを判定
        storage_flg = self.path_check(file_path)
        if storage_flg is True:
            # /storage
            tmp_file_path = self.make_temp_path(file_path)
            # /storageから/tmpにコピー
            shutil.copy2(file_path, tmp_file_path)
        else:
            # not /storage
            tmp_file_path = file_path

        value = Path(tmp_file_path).read_text(encoding=encoding)
        if storage_flg is True:
            # /tmpの掃除
            if os.path.isfile(self.tmp_file_path) is True:
                os.remove(tmp_file_path)
        return value

class storage_read_bytes(storage_base):
    def read_bytes(self, file_path):
        # ルートパスを判定
        storage_flg = self.path_check(file_path)
        if storage_flg is True:
            # /storage
            tmp_file_path = self.make_temp_path(file_path)
            # /storageから/tmpにコピー
            shutil.copy2(file_path, tmp_file_path)
        else:
            # not /storage
            tmp_file_path = file_path

        value = Path(tmp_file_path).read_bytes()
        if storage_flg is True:
            # /tmpの掃除
            if os.path.isfile(self.tmp_file_path) is True:
                os.remove(tmp_file_path)
        return value