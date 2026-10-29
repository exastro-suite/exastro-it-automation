# Copyright 2026 NEC Corporation#
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

"""searchUploadFilePath() のテスト

収集項目値管理で指定されたファイル名(YAML の値)を、収集結果(_parameters_file)の添付ファイル一覧から探す。
照合は「ファイル名だけで一致」「フルパスの末尾で一致」の 2 通りで、拡張子まで含めて一致する必要がある。
見つからない場合は空文字を返し、呼び出し側はその項目を空で登録・更新したうえで収集ログに通知する(収集済み(通知あり))。
"""
from backyard_main import searchUploadFilePath

from tests.common import HOST_NAME, PARAMETERS_FILE_PATH, create_upload_lists

UPLOAD_FILE_PATH = "%s/%s/OS/RH_DISK/COMMAND/0/parted.result.txt" % (PARAMETERS_FILE_PATH, HOST_NAME)
OTHER_UPLOAD_FILE_PATH = "%s/%s/OS/RH_DISK/COMMAND/1/pvdisplay.result.txt" % (PARAMETERS_FILE_PATH, HOST_NAME)


def test_match_by_file_name():
    """ファイル名だけで一致する"""
    upload_lists, upload_list_fullpath = create_upload_lists([UPLOAD_FILE_PATH, OTHER_UPLOAD_FILE_PATH])

    ret = searchUploadFilePath(HOST_NAME, "parted.result.txt", upload_lists, upload_list_fullpath)

    assert ret == UPLOAD_FILE_PATH


def test_match_by_path_suffix():
    """フルパスの末尾で一致する"""
    upload_lists, upload_list_fullpath = create_upload_lists([UPLOAD_FILE_PATH, OTHER_UPLOAD_FILE_PATH])

    ret = searchUploadFilePath(HOST_NAME, "COMMAND/0/parted.result.txt", upload_lists, upload_list_fullpath)

    assert ret == UPLOAD_FILE_PATH


def test_not_match_without_extension():
    """拡張子を付けずに指定すると見つからない(Issue #2847 の再現)"""
    upload_lists, upload_list_fullpath = create_upload_lists([UPLOAD_FILE_PATH, OTHER_UPLOAD_FILE_PATH])

    ret = searchUploadFilePath(HOST_NAME, "parted.result", upload_lists, upload_list_fullpath)

    assert ret == ""


def test_empty_file_name():
    """ファイル名が空の場合は検索しない"""
    upload_lists, upload_list_fullpath = create_upload_lists([UPLOAD_FILE_PATH])

    ret = searchUploadFilePath(HOST_NAME, "", upload_lists, upload_list_fullpath)

    assert ret == ""


def test_no_upload_files_for_host():
    """該当ホストの添付ファイル一覧が無い場合は見つからない"""
    upload_lists, upload_list_fullpath = create_upload_lists([UPLOAD_FILE_PATH])

    ret = searchUploadFilePath("host99", "parted.result.txt", upload_lists, upload_list_fullpath)

    assert ret == ""


def test_empty_upload_lists():
    """添付ファイル一覧(ファイル名の索引, フルパスの索引)が両方とも空の場合は見つからない"""
    upload_lists, upload_list_fullpath = create_upload_lists([])

    ret = searchUploadFilePath(HOST_NAME, "parted.result.txt", upload_lists, upload_list_fullpath)

    assert ret == ""


def test_match_by_full_path():
    """フルパスをまるごと指定すると、そのパスが見つかる"""
    upload_lists, upload_list_fullpath = create_upload_lists([UPLOAD_FILE_PATH, OTHER_UPLOAD_FILE_PATH])

    ret = searchUploadFilePath(HOST_NAME, OTHER_UPLOAD_FILE_PATH, upload_lists, upload_list_fullpath)

    assert ret == OTHER_UPLOAD_FILE_PATH


def test_match_by_path_suffix_returns_first_candidate():
    """フルパスの末尾で一致する候補が複数ある場合は、先に登録された候補を返す"""
    first_path = "%s/%s/OS/RH_DISK/COMMAND/0/parted.result.txt" % (PARAMETERS_FILE_PATH, HOST_NAME)
    second_path = "%s/%s/OS/RH_LVM/COMMAND/0/parted.result.txt" % (PARAMETERS_FILE_PATH, HOST_NAME)
    upload_lists, upload_list_fullpath = create_upload_lists([first_path, second_path])

    ret = searchUploadFilePath(HOST_NAME, "COMMAND/0/parted.result.txt", upload_lists, upload_list_fullpath)

    assert ret == first_path


def test_match_by_file_name_returns_first_registered():
    """同じファイル名が別ディレクトリに 2 つある場合、ファイル名だけの指定では先に登録された方を返す

    backyard_main() のファイル名の索引は、同じファイル名が既に登録されていれば上書きしない(先勝ち)。
    """
    first_path = "%s/%s/OS/RH_DISK/COMMAND/0/parted.result.txt" % (PARAMETERS_FILE_PATH, HOST_NAME)
    second_path = "%s/%s/OS/RH_DISK/COMMAND/1/parted.result.txt" % (PARAMETERS_FILE_PATH, HOST_NAME)
    upload_lists, upload_list_fullpath = create_upload_lists([first_path, second_path])

    ret = searchUploadFilePath(HOST_NAME, "parted.result.txt", upload_lists, upload_list_fullpath)

    assert ret == first_path


def test_not_match_file_of_other_host():
    """別ホストに同名ファイルがあっても、対象ホストに無ければ見つからない"""
    other_host_path = "%s/%s/OS/RH_DISK/COMMAND/0/parted.result.txt" % (PARAMETERS_FILE_PATH, "host02")
    upload_lists, upload_list_fullpath = create_upload_lists([OTHER_UPLOAD_FILE_PATH, other_host_path])

    ret = searchUploadFilePath(HOST_NAME, "parted.result.txt", upload_lists, upload_list_fullpath)

    assert ret == ""
