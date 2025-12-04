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
        try:
            # ルートパスを/tmpに置き換える
            tmp_dir_path = re.sub(os.environ.get('STORAGEPATH'), "/tmp/", os.path.dirname(file_path))
            tmp_file_path = "{}/{}".format(tmp_dir_path, os.path.basename(file_path))
            os.makedirs(tmp_dir_path, exist_ok=True)
        except:  # noqa: E722
            pass
        return tmp_file_path

    def makedir_temp_path(self, file_path: str):
        try:
            tmp_dir_path = os.path.dirname(file_path)
            os.makedirs(tmp_dir_path, exist_ok=True)
        except:  # noqa: E722
            pass
        return file_path

    def path_check(self, file_path):
        root_dir = "^{}".format(os.environ.get('STORAGEPATH'))
        # ファイルパスが /storage か判定
        if re.search(root_dir, file_path) is not None:
            return True
        else:
            return False

    def get_disk_usage(self):
        usage = shutil.disk_usage(os.environ.get('STORAGEPATH'))
        disk_stats = {
            "total_space": usage.total,
            "used_space": usage.used,
            "free_space": usage.free
        }
        return disk_stats

    def validate_disk_space(self, file_size):
        usage = self.get_disk_usage()
        free_space = usage["free_space"]
        # 保存できる容量があるか判定
        can_save = int(free_space) >= int(file_size)
        return can_save, free_space


class storage_read(storage_base):
    def __init__(self):
        self.storage_file_path = None
        self.tmp_file_path = None
        self.tmp_dir_path = None
        self.storage_path_flg = False
        self.fd = None
        self.force_file_del = False

    def open(self, file_path, mode=None, tmp_path=None):
        self.storage_file_path = file_path
        self.tmp_file_path = file_path

        # ファイルパスが /storage か判定
        self.storage_flg = self.path_check(file_path)
        # tmp_pathを使用する場合、強制削除フラグを立てる
        self.force_file_del = False if tmp_path is None else True
        if self.storage_flg is True:
            self.tmp_file_path = self.make_temp_path(file_path) if tmp_path is None else self.makedir_temp_path(tmp_path)
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

    def chunk_read(self, chunk):
        # read by chunk
        return self.fd.read(chunk)

    def close(self, file_del=True):
        # close
        self.fd.close()
        if self.storage_flg is True and file_del is True:
            # /tmpの掃除
            self.remove()
        # openでtmp_path指定している場合は、強制削除
        if self.force_file_del is True:
            # /tmpの掃除: ファイル削除→ディレクトリ削除
            self.remove()
            self.remove_tmpdir()

    def remove(self):
        try:
            os.remove(self.tmp_file_path)
        except:  # noqa: E722
            pass

    def remove_tmpdir(self):
        try:
            # /tmpに作成した作業ディレクトリの削除
            if self.tmp_file_path.startswith("/tmp/"):
                os.rmdir(os.path.dirname(self.tmp_file_path))
        except:  # noqa: E722
            pass


class storage_write(storage_base):
    def __init__(self):
        self.storage_file_path = None
        self.tmp_file_path = None
        self.tmp_dir_path = None
        self.storage_flg = False
        self.fd = None

    def open(self, file_path, mode=None):
        self.storage_file_path = file_path
        self.tmp_file_path = file_path

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
        self.fd.write(value)

    def close(self, file_del=True):
        # close
        self.fd.close()
        if self.storage_flg is True:
            # /tmpから/stargeにコピー
            shutil.copy2(self.tmp_file_path, self.storage_file_path)
            if file_del is True:
                # /tmpの掃除
                self.remove()

    def remove(self):
        try:
            os.remove(self.tmp_file_path)
        except:  # noqa: E722
            pass


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
            try:
                os.remove(tmp_file_path)
            except:  # noqa: E722
                pass


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
            try:
                os.remove(tmp_file_path)
            except:  # noqa: E722
                pass
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

        chunks = []
        with open(tmp_file_path, "rb") as f:
            while chunk := f.read(10000):
                chunks.append(chunk)
        value = b''.join(chunks)
        if storage_flg is True:
            # /tmpの掃除
            try:
                os.remove(tmp_file_path)
            except:  # noqa: E722
                pass
        return value
