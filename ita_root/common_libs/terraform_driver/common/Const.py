# Copyright 2023 NEC Corporation#
# Licensed under the Apache License, Version 2.2 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.2
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
terraformドライバーに必要な共通の定数定義モジュール
"""


class Const:
    """
    terraformドライバーに必要な共通の定数定義クラス
    """

    # ステータス定義(DBの値と同期させること)
    STATUS_NOT_YET = '1'            # 未実行
    STATUS_PREPARE = '2'            # 準備中
    STATUS_PROCESSING = '3'         # 実行中
    STATUS_PROCESS_DELAYED = '4'    # 実行中(遅延)
    STATUS_COMPLETE = '5'           # 完了
    STATUS_FAILURE = '6'            # 完了(異常)
    STATUS_EXCEPTION = '7'          # 想定外エラー
    STATUS_SCRAM = '8'              # 緊急停止
    STATUS_RESERVE = '9'            # 未実行(予約中)
    STATUS_RESERVE_CANCEL = '10'    # 予約取消

    # RUN_MODE
    RUN_MODE_APPLY = '1'    # 実行モード(apply)
    RUN_MODE_PLAN = '2'     # 実行モード(plan)
    RUN_MODE_PARAM = '3'    # 実行モード(パラメータ確認)
    RUN_MODE_DESTROY = '4'  # 実行モード(destroy)

    # ドライバ識別子
    DRIVER_TERRAFORM_CLOUD_EP = 'TERE'
    DRIVER_TERRAFORM_CLI = 'TERC'

    # カラムタイプ
    COL_TYPE_VAL = '1'    # Value型
    COL_TYPE_KEY = '2'    # Key型

    # テーブル/ビュー名
    T_EXEC_STATUS = 'T_TERF_EXEC_STATUS'
    T_EXEC_MODE = 'T_TERF_EXEC_MODE'
    T_TYPE_MASTER = 'T_TERF_TYPE_MASTER'
    V_COLUMN_LIST = 'V_TERF_COLUMN_LIST'
