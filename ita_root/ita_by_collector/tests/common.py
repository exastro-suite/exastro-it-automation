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

"""ita_by_collector のテスト共通ヘルパー"""
import os

# 収集結果の添付ファイル置き場(_parameters_file)のパス
PARAMETERS_FILE_PATH = "/storage/org/ws/driver/ansible/legacy/0000001/in/_parameters_file"
HOST_NAME = "host01"


def create_upload_lists(target_upload_files, base_path=PARAMETERS_FILE_PATH):
    """添付ファイル一覧(ファイル名の索引, フルパスの索引)を作成する

    backyard_main() の「対象ホスト、ファイルのリスト作成」と同じ組み立て方をする。
    """
    arrTargetUploadLists = {}
    arrTargetUploadListFullpath = {}
    for strTargetUploadfile in target_upload_files:
        targetHosts = strTargetUploadfile.replace(base_path, "").split('/')
        keyname = os.path.basename(strTargetUploadfile)
        if targetHosts[1] not in arrTargetUploadLists:
            arrTargetUploadLists[targetHosts[1]] = {}

        if keyname not in arrTargetUploadLists[targetHosts[1]]:
            arrTargetUploadLists[targetHosts[1]][keyname] = strTargetUploadfile

        if targetHosts[1] not in arrTargetUploadListFullpath:
            arrTargetUploadListFullpath[targetHosts[1]] = {}

        if strTargetUploadfile not in arrTargetUploadListFullpath[targetHosts[1]]:
            arrTargetUploadListFullpath[targetHosts[1]][strTargetUploadfile] = strTargetUploadfile

    return arrTargetUploadLists, arrTargetUploadListFullpath
