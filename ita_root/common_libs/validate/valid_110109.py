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

import os
import base64

from common_libs.notification import validator
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
    # 事前通知の通知先が選択されていて、通知が未選択の場合
    if before_notice_dest and not before_notice:
        retBool = False
        msg = g.appmsg.get_api_message("499-01811")
        return retBool, msg, option,
    # 事後通知の通知先が選択されていて、通知が未選択の場合
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

    # 以降通知テンプレートのチェック
    target = {}
    if cmd_type == 'Register' or cmd_type == 'Update':
        # ファイルがUpdadeされているかチェック
        file_name = entry_parameter.get('before_notification')
        if file_name:
            # ファイルの中身を取得
            file_path = option.get('entry_parameter', {}).get('file_path', {}).get('before_notification', '')
            if file_path is not None and os.path.isfile(file_path):
                with open(file_path, 'rb') as f:  # バイナリファイルとしてファイルをオープン
                    template_data_binary = f.read()
                target["before_notification"] = template_data_binary

        # ファイルがUpdadeされているかチェック
        file_name = entry_parameter.get('after_notification')
        if file_name:
            # ファイルの中身を取得
            file_path = option.get('entry_parameter', {}).get('file', {}).get('after_notification', '')
            if file_path is not None and os.path.isfile(file_path):
                with open(file_path, 'rb') as f:  # バイナリファイルとしてファイルをオープン
                    template_data_binary = f.read()
                target["after_notification"] = template_data_binary

    # テンプレートのアップロードが無い場合は以降のチェックが不要となるためこの時点で返却する
    if len(target) == 0:
        return retBool, msg, option,

    target_lang = g.LANGUAGE if g.LANGUAGE is not None else "ja"

    # ここまで処理が流れた時点で、前段のチェックは通過しているので上書きで問題なしと判断
    msg = []

    for key, value in target.items():
        target_column_name = {
            "ja": objtable["COLINFO"][key]["COLUMN_NAME_JA"],
            "en": objtable["COLINFO"][key]["COLUMN_NAME_EN"],
        }

        target_column_group_id = objtable["COLINFO"][key]["COL_GROUP_ID"]

        # 後続のチェックが不要になる場合を考慮し、ループ継続の判定に使用するのboolを定義
        tmp_bool = True
        # 複数メッセージの返却を考慮し、配列で定義し直す。

        template_data_binary = value

        # 文字コードをチェック バイナリファイルの場合、encode['encoding']はNone
        if validator.is_binary_file(template_data_binary):
            tmp_bool = False
            retBool = False
            msg_tmp = g.appmsg.get_api_message("499-01814",
                                               [__fetch_column_group_name(objdbca, target_column_group_id)[target_lang] + ' ' +
                                                target_column_name[target_lang]])
            msg.append(msg_tmp)

        template_data_decoded = template_data_binary.decode('utf-8', 'ignore')
        if tmp_bool:
            # jinja2の形式として問題無いか確認する
            if not validator.is_jinja2_template(template_data_decoded):
                tmp_bool = False
                retBool = False
                msg_tmp = g.appmsg.get_api_message("499-01815",
                                                   [__fetch_column_group_name(objdbca, target_column_group_id)[target_lang] + ' ' +
                                                    target_column_name[target_lang]])
                msg.append(msg_tmp)

        if tmp_bool:
            # 特有の構文チェック
            if not validator.contains_title(template_data_decoded):
                retBool = False
                msg_tmp = g.appmsg.get_api_message("499-01816",
                                                   [__fetch_column_group_name(objdbca, target_column_group_id)[target_lang] + ' ' +
                                                    target_column_name[target_lang]])
                msg.append(msg_tmp)

            if not validator.contains_body(template_data_decoded):
                retBool = False
                msg_tmp = g.appmsg.get_api_message("499-01817",
                                                   [__fetch_column_group_name(objdbca, target_column_group_id)[target_lang] + ' ' +
                                                    target_column_name[target_lang]])
                msg.append(msg_tmp)

    return retBool, msg, option,


def __fetch_column_group_name(objdbca, col_group_id):
    """カラムグループの日本語名、英語名を取得する

    Args:
        objdbca :DB接続クラスインスタンス
    """

    sql = "SELECT COL_GROUP_NAME_JA,COL_GROUP_NAME_EN FROM t_comn_column_group WHERE COL_GROUP_ID = '%s' and DISUSE_FLAG = '0'" % (col_group_id)
    fetch_result = objdbca.sql_execute(sql, [])

    return dict(
        {
            "ja": fetch_result[0]["COL_GROUP_NAME_JA"],
            "en": fetch_result[0]["COL_GROUP_NAME_EN"]
        }
    )
