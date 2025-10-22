# Copyright 2024 NEC Corporation#
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

class oaseConst():
    # テーブル名
    T_OASE_LABEL_KEY_INPUT = 'T_OASE_LABEL_KEY_INPUT'  # ラベル入力用マスタ
    V_OASE_LABEL_KEY_GROUP = 'V_OASE_LABEL_KEY_GROUP'  # ラベルマスタ（固定+入力）

    T_OASE_EVENT_COLLECTION_SETTINGS = 'T_OASE_EVENT_COLLECTION_SETTINGS'  # イベント収集の設定
    T_OASE_EVENT_COLLECTION_PROGRESS = 'T_OASE_EVENT_COLLECTION_PROGRESS'  # 収集時間の履歴
    T_OASE_LABELING_SETTINGS = 'T_OASE_LABELING_SETTINGS'  # ラベル付与の設定
    T_OASE_DEDUPLICATION_SETTINGS = 'T_OASE_DEDUPLICATION_SETTINGS'  # 重複排除の設定

    T_OASE_FILTER = 'T_OASE_FILTER'  # フィルター
    T_OASE_RULE = 'T_OASE_RULE'  # ルール
    T_OASE_ACTION = 'T_OASE_ACTION'  # アクション
    T_OASE_ACTION_LOG = 'T_OASE_ACTION_LOG'  # 評価結果

    # 接続方式
    DF_CON_METHOD_NOT_AGENT = "99"  # エージェント不使用

    # イベントの状態名
    DF_EVENT_STATUS_NEW = "1"
    DF_EVENT_STATUS_UNDETECTED = "2"
    DF_EVENT_STATUS_EVALUATED = "3"
    DF_EVENT_STATUS_TIMEOUT = "4"

    # イベントのタイプ名
    DF_EVENT_TYPE_EVENT = "1"
    DF_EVENT_TYPE_CONCLUSION = "2"

    # フィルター検索条件 / Filter search conditions
    DF_SEARCH_CONDITION_UNIQUE = '1'    # ユニーク / Unique
    DF_SEARCH_CONDITION_QUEUING = '2'   # キューイング / Queuing
    DF_SEARCH_CONDITION_GROUPING = '3'  # グルーピング / Grouping

    # グルーピング条件 / Grouping conditions
    DF_GROUP_CONDITION_ID_TARGET = '1'      # を対象とする / is the target
    """グルーピング条件「を対象とする」"""
    DF_GROUP_CONDITION_ID_NOT_TARGET = '2'  # 以外を対象とする / is not a target
    """グルーピング条件「以外を対象とする」"""

    # イベントデータに一時的に追加する項目定期

    # 親ラベル
    DF_LOCAL_LABLE_NAME = "__exastro_local_labels__"
    # 子ラベル イベント状態
    DF_LOCAL_LABLE_STATUS = "status"
    # DF_LOCAL_LABLE_STATUSの状態
    DF_PROC_EVENT = '0'             # 処理対象:〇
    DF_POST_PROC_TIMEOUT_EVENT = '1'    # 処理対象　処理後タイムアウト:●
    DF_TIMEOUT_EVENT = '2'           # タイムアウト（TTL*2）
    DF_NOT_PROC_EVENT = '3'       # 対象外
    # 子ラベル グループキー
    DF_LOCAL_LABLE_ATTRIBUTE_KEY = "group_key"
    """子ラベル グループキー"""

    # ルール・フィルタ管理　JSON内の演算子・条件
    # 条件
    DF_TEST_EQ = '1'    # =
    DF_TEST_NE = '2'    # !=
    # 演算子
    DF_OPE_NONE = ''    # None
    DF_OPE_OR = '1'     # OR
    DF_OPE_AND = '2'    # AND
    DF_OPE_ORDER = '3'  # ->

    # OASE 評価結果　ステータス値
    OSTS_Rule_Match = "1"               # 判定済み
    OSTS_Executing = "2"                # 実行中
    OSTS_Wait_Approval = "3"            # 承認待ち
    OSTS_Approved = "4"                 # 承認済み
    OSTS_Rejected = "5"                 # 承認却下済み
    OSTS_Completed = "6"                # 完了
    OSTS_Completed_Abend = "7"          # 完了（異常）
    OSTS_Wait_For_Comp_Conf = "8"       # 完了確認待ち
    OSTS_Completion_Conf = "9"          # 完了確認済み
    OSTS_Completion_Conf_Reject = "10"  # 完了確認却下済み

    # Conductor ステータス値
    CSTS_Unexecuted = "1"               # 未実行
    CSTS_Unexecuted_Schedule = "2"      # 未実行(予約)
    CSTS_Executing = "3"                # 実行中
    CSTS_Executing_Delay = "4"          # 実行中(遅延)
    CSTS_Pause = "5"                    # 一時停止
    CSTS_Completed = "6"                # 正常終了
    CSTS_Abend = "7"                    # 異常終了
    CSTS_Warning_end = "8"              # 警告終了
    CSTS_Emergency_stop = "9"           # 緊急停止
    CSTS_Schedule_Cancel = "10"         # 予約取消
    CSTS_Unexpected_Error = "11"        # 想定外エラー

    # OASEエージェントの識別情報(未設定時)
    DF_AGENT_NAME = "Unknown"           # エージェント名未設定
    DF_AGENT_VERSION = "Unknown"        # バージョン未設定
