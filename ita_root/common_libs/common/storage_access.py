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
import time
import datetime
import pytz


class storage_base:
    def make_temp_path(self, file_path):
        try:
            # ルートパスを/tmpに置き換える
            tmp_dir_path = re.sub(os.environ.get('STORAGEPATH'), "/tmp/", os.path.dirname(file_path))
            tmp_file_path = "{}/{}".format(tmp_dir_path, os.path.basename(file_path))
            retry_makedirs(tmp_dir_path)
        except:  # noqa: E722
            pass
        return tmp_file_path

    def makedir_temp_path(self, file_path: str):
        try:
            tmp_dir_path = os.path.dirname(file_path)
            retry_makedirs(tmp_dir_path)
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
            retry_copy2(self.storage_file_path, self.tmp_file_path)
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
            retry_remove(self.tmp_file_path)
        except:  # noqa: E722
            pass

    def remove_tmpdir(self):
        try:
            # /tmpに作成した作業ディレクトリの削除
            if self.tmp_file_path.startswith("/tmp/"):
                retry_rmdir(os.path.dirname(self.tmp_file_path))
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
            # 新規作成でコピー元が存在しないこともある
            if os.path.isfile(file_path) is True:
                retry_copy2(self.storage_file_path, self.tmp_file_path)
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
            retry_copy2(self.tmp_file_path, self.storage_file_path)
            if file_del is True:
                # /tmpの掃除
                self.remove()

    def remove(self):
        try:
            retry_remove(self.tmp_file_path)
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
            # /tmpから/storageにコピー
            retry_copy2(tmp_file_path, file_path)
            # /tmpの掃除
            try:
                retry_remove(tmp_file_path)
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
            retry_copy2(file_path, tmp_file_path)
        else:
            # not /storage
            tmp_file_path = file_path

        value = Path(tmp_file_path).read_text(encoding=encoding)
        if storage_flg is True:
            # /tmpの掃除
            try:
                retry_remove(tmp_file_path)
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
            retry_copy2(file_path, tmp_file_path)
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
                retry_remove(tmp_file_path)
            except:  # noqa: E722
                pass
        return value


# 低速ストレージ対応: @file_read_retry デコレータでリトライ処理を付与
# storage_access.pyの中ではutil.pyの関数は使用できないため、個別で記載する
def print_exception_msg(e):
    """
    例外メッセージを、infoログに出力する
    """

    # 例外と、発生したファイ名と行番号を出力
    info = inspect.getouterframes(inspect.currentframe())[1]
    msg_line = "({}:{})".format(os.path.basename(info.filename), info.lineno)
    exception_msg = "exception_msg='{}'".format(e)
    g.applogger.info('[timestamp={}] {} {}'.format(datetime_to_str(datetime.datetime.now()), exception_msg, msg_line))


def datetime_to_str(p_datetime):
    """datetime to string (ISO format)
    Args:
        p_datetime (datetime): datetime
    Returns:
        str: datetime formated string (UTC)
    """
    if p_datetime is None:
        return None

    if p_datetime.tzinfo is None:
        aware_datetime = pytz.timezone(os.environ.get('TZ', 'UTC')).localize(p_datetime)
    else:
        aware_datetime = p_datetime

    utc_datetime = aware_datetime.astimezone(datetime.timezone.utc)
    return utc_datetime.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def file_read_retry(func):
    """
    file_read_retry
        ファイルストレージへの書き込み直後の読み込みが遅い場合向けの対策
        Measures to take when reading is slow immediately after writing to file storage

        「FileNotFoundError: [Errno 2] No such file or directory」が出るため、リトライを行う
        "FileNotFoundError: [Errno 2] No such file or directory" appears, so retry.

        デコレーター関数 / decorator function
        ・util.pyと同等
    """
    #
    def wrapper(*args, **kwargs):
        retry_delay_time = 0.1  # リトライのインターバル
        retBool = False
        i = 1
        max = 3  # リトライ回数
        while True:
            try:
                retBool = func(*args, **kwargs)
                if retBool is True:
                    break
            except Exception as e:
                # raiseしたくない場合は、funcの中でログを出力し、（エラーを抑止して）Falseを返却してください
                if i == max:
                    # 最後のログ出力のみ、stacktraceを出力
                    # Output stacktrace only the last log output
                    t = traceback.format_exc()
                    g.applogger.debug(str(t))
                    raise e
                else:
                    # retry分は、メッセージのみを出力
                    # For retry minutes, only the message is output
                    g.applogger.info(print_exception_msg(e))

            if i == max:
                break
            time.sleep(retry_delay_time)
            i = i + 1

    return wrapper


# ディレクトリ作成
@file_read_retry
def retry_makedirs(dir_path, raise_error=True):
    """
        `os.makedirs(dir_path, exist_ok=True)` を`@file_read_retry`付きで実行する
        Args:
            dir_path: 作成するディレクトリパス
            raise_error: リトライを実施してもエラーが発生した際に例外スローするか (True: 例外スロー&ログ出力/ False: ログ出力のみ)
    """
    g.applogger.debug(f"os.makedirs({dir_path})")
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        g.applogger.info("retry_makedirs failed. dir_path={}".format(dir_path))
        t = traceback.format_exc()
        g.applogger.debug(str(t))
        if raise_error is True:
            raise e
        else:
            return False


# ファイルコピー(shutil.copy2)
@file_read_retry
def retry_copy2(src_path, dest_path, raise_error=True):
    """
        `shutil.copy(src_path, dest_path)` を`@file_read_retry`付きで実行する
        Args:
            src_path: コピー元のファイルパス
            dest_path: コピー先のファイルパス
            raise_error: リトライを実施してもエラーが発生した際に例外スローするか (True: 例外スロー&ログ出力/ False: ログ出力のみ)
    """
    g.applogger.debug(f"shutil.copy2({src_path, dest_path})")
    try:
        shutil.copy2(src_path, dest_path)
        return True
    except Exception as e:
        g.applogger.info("retry_copy2 failed. src_path={}, dest_path={}".format(src_path, dest_path))
        t = traceback.format_exc()
        g.applogger.debug(str(t))
        if raise_error is True:
            raise e
        else:
            return False


# 空ディレクトリ削除(os.rmdir)
@file_read_retry
def retry_rmdir(dir_path, raise_error=True):
    """
        `os.rmdir(dir_path)` を`@file_read_retry`付きで実行する
        Args:
            dir_path: 削除するディレクトリパス
            raise_error: リトライを実施してもエラーが発生した際に例外スローするか (True: 例外スロー&ログ出力/ False: ログ出力のみ)
    """
    g.applogger.debug(f"os.rmdir({dir_path})")
    try:
        os.rmdir(dir_path)
        return True
    except Exception as e:
        g.applogger.info("retry_rmdir failed. dir_path={}".format(dir_path))
        t = traceback.format_exc()
        g.applogger.debug(str(t))
        if raise_error is True:
            raise e
        else:
            return False


# ファイル削除(os.remove)
@file_read_retry
def retry_remove(file_path, raise_error=True):
    """
        `os.remove(file_path)` を`@file_read_retry`付きで実行する
        Args:
            file_path: 削除するファイルパス
            raise_error: リトライを実施してもエラーが発生した際に例外スローするか (True: 例外スロー&ログ出力/ False: ログ出力のみ)
    """
    g.applogger.debug(f"os.remove({file_path})")
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        g.applogger.info("retry_remove failed. file_path={}".format(file_path))
        t = traceback.format_exc()
        g.applogger.debug(str(t))
        if raise_error is True:
            raise e
        else:
            return False
