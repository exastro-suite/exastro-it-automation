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
from flask import g
from common_libs.common.dbconnect import *  # noqa: F403


def backyard_main(organization_id, workspace_id):

    print("backyard_main ita_by_collector called")

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # 実行準備
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

    # 環境情報設定
    # 言語情報
    # if 'LANGUAGE' not in g:
    g.LANGUAGE = 'en'
    # if 'USER_ID' not in g:
    g.USER_ID = '20501'

    print("backyard_main ita_by_collector end")
