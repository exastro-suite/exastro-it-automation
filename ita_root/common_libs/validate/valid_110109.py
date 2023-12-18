# Copyright 2023 NEC Corporation#
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
from flask import g


def external_valid_menu_before(objdbca, objtable, option):
    """
    メニューバリデーション(登録/更新)
    ARGS:
        objdbca :DB接続クラスインスタンス
        objtabl :メニュー情報、カラム紐付、関連情報
        option :パラメータ、その他設定値
    RETRUN:
        retBoo :True/ False
        msg :エラーメッセージ
        option :受け取ったもの
    """
    retBool = True
    msg = ""
    cmd_type = option.get('cmd_type')

    # 廃止の場合、バリデーションチェックを行わない。
    if cmd_type == 'Discard':
        return retBool, msg, option,

    current_parameter = option.get('current_parameter', {}).get('parameter')
    entry_parameter = option.get('entry_parameter', {}).get('parameter')

    # 「登録」「更新」の場合、entry_parameterから各値を取得
    if cmd_type == 'Register' or cmd_type == 'Update':
        filter_a = entry_parameter.get('filter_a')
        filter_b = entry_parameter.get('filter_b')
        filter_operator = entry_parameter.get('filter_operator')
        before_notice = entry_parameter.get('before_notification')  # 通知
        before_notice_dest = entry_parameter.get('before_notification_destination') # 通知先
        after_notice = entry_parameter.get('after_notification') # 通知
        after_notice_dest = entry_parameter.get('after_notification_destination') # 通知先
        before_rule_label_name = entry_parameter.get('rule_label_name')  # 変更後　ルールラベル名
        after_rule_label_name = current_parameter.get('rule_label_name') # 変更前　ルールラベル名

    # 「復活」の場合、currrent_parameterから各値を取得
    elif cmd_type == 'Restore':
        filter_a = current_parameter.get('filter_a')
        filter_b = current_parameter.get('filter_b')
        filter_operator = current_parameter.get('filter_operator')
        before_notice = current_parameter.get('before_notification')
        before_notice_dest = current_parameter.get('before_notification_destination')
        after_notice = current_parameter.get('after_notification')
        after_notice_dest = current_parameter.get('after_notification_destination')

    else:
        return retBool, msg, option

    if filter_a == filter_b:
        retBool = False
        msg = g.appmsg.get_api_message("499-01808")
        return retBool, msg, option,
    # フィルタABどちらか未選択で演算子が選択されている場合
    if (not filter_a or not filter_b) and filter_operator:
        retBool = False
        msg = g.appmsg.get_api_message("499-01809")
        return retBool, msg, option,
    # フィルタABの両方が選択されていて演算子が未選択の場合
    if (filter_a and filter_b) and not filter_operator:
        retBool = False
        msg = g.appmsg.get_api_message("499-01810")
        return retBool, msg, option,
    # 作業前の通知先が選択されていて、通知が未選択の場合
    if before_notice_dest and not before_notice:
        retBool = False
        msg = g.appmsg.get_api_message("499-01811")
        return retBool, msg, option,
    # 作業後の通知先が選択されていて、通知が未選択の場合
    if after_notice_dest and not after_notice:
        retBool = False
        msg = g.appmsg.get_api_message("499-01812")
        return retBool, msg, option,

    # 更新の場合、ルールラベル名が変更されていない事を確認
    if cmd_type == 'Update':
        if before_rule_label_name != after_rule_label_name:
            retBool = False
            msg = g.appmsg.get_api_message("499-01813")
            return retBool, msg, option,


    return retBool, msg, option,
