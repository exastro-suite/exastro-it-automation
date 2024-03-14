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
    msg = []
    cmd_type = option.get('cmd_type')

    # 廃止の場合、バリデーションチェックを行わない。
    if cmd_type == 'Discard':
        return retBool, msg, option,

    current_parameter = option.get('current_parameter', {}).get('parameter')
    entry_parameter = option.get('entry_parameter', {}).get('parameter')

    # 「登録」「更新」の場合、entry_parameterから各値を取得
    if cmd_type == 'Register' or cmd_type == 'Update':
        # オペレーション名
        operation_id = entry_parameter.get('operation_id')
        # イベント連携フラグ
        event_collaboration = entry_parameter.get('event_collaboration')
        # ホスト名
        host_name = entry_parameter.get('host_name')
        # パラメータシート名
        parameter_sheet_name = entry_parameter.get('parameter_sheet_name')

    # 「復活」の場合、currrent_parameterから各値を取得
    elif cmd_type == 'Restore':
        # オペレーション名
        operation_id = current_parameter.get('operation_id')
        # イベント連携フラグ
        event_collaboration = current_parameter.get('event_collaboration')
        # ホスト名
        host_name = current_parameter.get('host_name')
        # パラメータシート名
        parameter_sheet_name = current_parameter.get('parameter_sheet_name')

    else:
        return retBool, msg, option

    # オペレーション名が選択されている場合、イベント連携フラグ＆ホスト名＆パラメータシート名の指定は不可
    if operation_id and (event_collaboration == "1" or host_name or parameter_sheet_name):
        retBool = False
        msg = g.appmsg.get_api_message("499-01819")
        return retBool, msg, option,

    # オペレーション名が選択されていない場合、イベント連携フラグorホスト名andパラメータシート名の指定が必要
    if not operation_id and event_collaboration != "1" and not host_name and not parameter_sheet_name:
        retBool = False
        msg = g.appmsg.get_api_message("499-01820")
        return retBool, msg, option,

    # イベント連携フラグ（True）とホスト名は同時指定不可
    if event_collaboration == "1" and host_name:
        retBool = False
        msg = g.appmsg.get_api_message("499-01821")
        return retBool, msg, option,

    # イベント連携フラグかホスト名が指定されている場合はパラメータシート名の指定が必要
    if (event_collaboration == "1" or host_name) and not parameter_sheet_name:
        retBool = False
        msg = g.appmsg.get_api_message("499-01822")
        return retBool, msg, option,

    return retBool, msg, option
