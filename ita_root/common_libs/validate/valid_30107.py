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

from flask import g  # noqa: F401
import datetime
import re


# バリデーションチェック
def conductor_regularly_valid(objdbca, objtable, option):  # noqa: C901

    retBool = True
    msg = []
    user_env = g.LANGUAGE.upper()
    entry_parameter = option.get('entry_parameter').get('parameter')

    # 定数 -----------------------------------
    # ステータス 準備中/In preparation
    REGULARLY_STATUS_ID_INPREPARATION = '1'
    # 周期　時
    REGULARLY_PERIOD_ID_TIME = '1'
    # 周期　日
    REGULARLY_PERIOD_ID_DAY = '2'
    # 周期　週
    REGULARLY_PERIOD_ID_WEEK = '3'
    # 周期　月（日付指定）
    REGULARLY_PERIOD_ID_MONTH_DAY = '4'
    # 周期　月（曜日指定）
    REGULARLY_PERIOD_ID_MONTH_DAY_OF_WEEK = '5'
    # 周期　月末
    REGULARLY_PERIOD_ID_END_OF_MONTH = '6'

    # 作業期間 チェック --------------------------------------------------
    start_date = str(entry_parameter.get('start_date') or '').strip()
    end_date = str(entry_parameter.get('end_date') or '').strip()
    dt_start_date = ''
    dt_end_date = ''

    if end_date:
        check_bool = True
        if start_date:
            try:
                dt_start_date = datetime.datetime.strptime(start_date, '%Y/%m/%d %H:%M:%S')
            except Exception:
                # 日時のフォーマットチェックは、カラムクラスのバリデーションチェックでエラー内容を返す
                check_bool = False

            try:
                dt_end_date = datetime.datetime.strptime(end_date, '%Y/%m/%d %H:%M:%S')
            except Exception:
                # 日時のフォーマットチェックは、カラムクラスのバリデーションチェックでエラー内容を返す
                check_bool = False

            if check_bool:
                # 日時フォーマットに問題なければ開始日時と終了日時の値を比較する
                if dt_start_date != dt_end_date:
                    if dt_start_date > dt_end_date:
                        # 開始日時より終了日時が過去日の場合、エラー
                        msg.append(g.appmsg.get_api_message("MSG-40030"))
                else:
                    # 開始日時と終了日時が同日同時刻の場合、エラー
                    msg.append(g.appmsg.get_api_message("MSG-40029"))
        # else:
        # 本来はエラーだが、開始日時は必須項目チェックでエラー内容を返す

    # 実行ユーザの入力 -------------------------------------------
    entry_parameter["execution_user"] = g.USER_ID

    # 周期と入力項目　チェック -------------------------------------------

    # 必須項目の場合、スペース除去。
    period = str(entry_parameter.get('period') or '').strip()
    interval = entry_parameter.get('interval')
    interval = str('' if interval is None else interval).strip()
    # 必要に応じてスペース除去。
    week_number = str(entry_parameter.get('week_number') or '')
    day_of_week = str(entry_parameter.get('day_of_week') or '')
    day = entry_parameter.get('day')
    day = str('' if day is None else day)
    time = str(entry_parameter.get('time') or '')

    if (period) and (interval):
        # 間隔 のパターンチェック（1～99）
        interval_valida_rule = '[1-9]|[1-9][0-9]'
        if re.fullmatch(interval_valida_rule, interval) is None:
            msg.append(g.appmsg.get_api_message("MSG-40031"))

        not_need_items = {}
        # 周期　時 の入力チェック
        if period == REGULARLY_PERIOD_ID_TIME:
            # 入力不要項目をセット（週番号、曜日、日、時間）
            not_need_items = {
                'week_number': week_number,
                'day_of_week': day_of_week,
                'day': day,
                'time': time
            }

        # 周期　日 の入力チェック
        if period == REGULARLY_PERIOD_ID_DAY:
            # 時間 チェックは下で行う
            # 入力不要項目をセット（週番号、曜日、日）
            not_need_items = {
                'week_number': week_number,
                'day_of_week': day_of_week,
                'day': day
            }

        # 周期　週　の入力チェック
        if period == REGULARLY_PERIOD_ID_WEEK:
            # 曜日 の入力チェック(妥当性チェックはカラムクラスチェックで行う)
            day_of_week = day_of_week.strip()
            if not day_of_week:
                msg.append(g.appmsg.get_api_message("MSG-40033"))
            # 時間 チェックは下で行う
            # 入力不要項目をセット（週番号、日）
            not_need_items = {
                'week_number': week_number,
                'day': day
            }

        # 周期　月（日付指定）
        if period == REGULARLY_PERIOD_ID_MONTH_DAY:
            day = day.strip()
            if day:
                # 日 のパターンチェック（1～31）
                day_rule = '[^0]|[1-2][0-9]|3[0-1]'
                if re.fullmatch(day_rule, day) is None:
                    msg.append(g.appmsg.get_api_message("MSG-40035"))
            else:
                # 日が入力されていない場合、エラー
                msg.append(g.appmsg.get_api_message("MSG-40034"))
            # 時間 チェックは下で行う
            # 入力不要項目をセット（週番号、曜日）
            not_need_items = {
                'week_number': week_number,
                'day_of_week': day_of_week
            }

        # 周期　月（曜日指定）
        if period == REGULARLY_PERIOD_ID_MONTH_DAY_OF_WEEK:
            # 週番号 の入力チェック(妥当性チェックはカラムクラスチェックで行う)
            week_number = week_number.strip()
            if not week_number:
                msg.append(g.appmsg.get_api_message("MSG-40032"))
            # 曜日 の入力チェック(妥当性チェックはカラムクラスチェックで行う)
            day_of_week = day_of_week.strip()
            if not day_of_week:
                msg.append(g.appmsg.get_api_message("MSG-40033"))
            # 時間 チェックは下で行う
            # 入力不要項目をセット（日）
            not_need_items = {'day': day}

        # 周期　月末
        if period == REGULARLY_PERIOD_ID_END_OF_MONTH:
            # 時間 チェックは下で行う
            # 入力不要項目をセット（週番号、曜日、日）
            not_need_items = {
                'week_number': week_number,
                'day_of_week': day_of_week,
                'day': day
            }

        # 周期の不正、入力チェックは必須項目チェック、カラムクラスチェックで行う

        # 時間 のパターンチェック（hh:mm:ss、0なしは許容しない）
        if period != REGULARLY_PERIOD_ID_TIME:
            time = time.strip()
            if time:
                time_validation_rule = '((0|1)[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]'
                if re.fullmatch(time_validation_rule, time) is None:
                    msg.append(g.appmsg.get_api_message("MSG-40037"))
            else:
                msg.append(g.appmsg.get_api_message("MSG-40036"))

        # 入力不要項目のチェック
        not_need_inputs = []
        for k, v in not_need_items.items():
            # 入力不要な項目に値が入っている場合、not_need_inputsに追加する
            if v:
                not_need_inputs.append(k)

        if len(not_need_inputs) >= 1:
            # 値が入っている入力不要項目が1つ以上あれば、『メニュー-カラム紐付管理』テーブルデータを取得
            t_common_menu_column_link = 'T_COMN_MENU_COLUMN_LINK'
            menu_id = '30107'
            ret = objdbca.table_select(t_common_menu_column_link, 'WHERE MENU_ID = %s AND DISUSE_FLAG = %s ORDER BY COLUMN_DISP_SEQ ASC', [menu_id, 0])  # noqa: E501

            msg_not_need = ''
            for not_need_input in not_need_inputs:
                # テーブルからメッセージ表示用に該当の項目名を取得（ja/en対応）
                for record in ret:
                    if record.get('COLUMN_NAME_REST') == not_need_input:
                        msg_not_need = msg_not_need + ',' + record.get('COLUMN_NAME_' + user_env)
                        break
            msg.append(g.appmsg.get_api_message("MSG-40038", [msg_not_need.strip(',')]))
    # else:
    # 本来はエラーだが、周期と間隔は必須項目なので個別バリデエラーにはしない

    # 作業停止期間 チェック ----------------------------------------------
    execution_stop_start_date = str(entry_parameter.get('execution_stop_start_date') or '').strip()
    execution_stop_end_date = str(entry_parameter.get('execution_stop_end_date') or '').strip()
    dt_execution_stop_start_date = ''
    dt_execution_stop_end_date = ''
    check_bool = True
    if (execution_stop_start_date) and (execution_stop_end_date):
        # 開始と終了が両方入力されている場合、チェック
        try:
            dt_execution_stop_start_date = datetime.datetime.strptime(execution_stop_start_date, '%Y/%m/%d %H:%M:%S')
        except Exception:
            check_bool = False
            # 日時のフォーマットチェックは、カラムクラスのバリデーションチェックでエラー内容を返す

        try:
            dt_execution_stop_end_date = datetime.datetime.strptime(execution_stop_end_date, '%Y/%m/%d %H:%M:%S')
        except Exception:
            check_bool = False
            # 日時のフォーマットチェックは、カラムクラスのバリデーションチェックでエラー内容を返す

        if check_bool:
            # 日時フォーマットに問題なければ開始と終了の値を比較する
            if dt_execution_stop_start_date != dt_execution_stop_end_date:
                if dt_execution_stop_start_date > dt_execution_stop_end_date:
                    # 開始より終了が過去日の場合、エラー
                    msg.append(g.appmsg.get_api_message("MSG-40040"))
            else:
                # 開始と終了が同日同時刻の場合、エラー
                msg.append(g.appmsg.get_api_message("MSG-40039"))

    if ((execution_stop_start_date) and (not execution_stop_end_date)) or ((not execution_stop_start_date) and (execution_stop_end_date)):
        # 開始、終了どちらか一方しか入力されていない場合、エラー
        msg.append(g.appmsg.get_api_message("MSG-40041"))

    if len(msg) >= 1:
        # msg に値がある場合は個別バリデエラー
        retBool = False

    if retBool:
        # 正常終了の場合、固定値のセット
        entry_parameter['status'] = REGULARLY_STATUS_ID_INPREPARATION
        entry_parameter['next_execution_date'] = None

    return retBool, msg, option
