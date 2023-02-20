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
"""
  CICD共通モジュール
"""
# from flask import g


def getSpecialColumnVaule(column_rest_name, option):
    """
      パスワードカラム入力値取得
      Arguments:
        column_rest_name: カラム名(REST用)
        option: 個別
      Returns:
        カラム入力値
    """
    str_token = option.get("current_parameter").get("parameter").get(column_rest_name)
    if column_rest_name in option["entry_parameter"]["parameter"]:
        str_token = option["entry_parameter"]["parameter"][column_rest_name]
    return str_token


def getColumnValue(option, RsetColName, PasswordCol=False):
    """
      カラム入力値取得
      Arguments:
        column_rest_name: カラム名(REST用)
        option: 個別
        PasswordCol: Password系カラム
      Returns:
        カラム入力値
    """
    ColValue = None
    if option["cmd_type"] == "Register":
        ColValue = option["entry_parameter"].get("parameter").get(RsetColName)

    elif option["cmd_type"] == "Update":
        ColValue = option["entry_parameter"].get("parameter").get(RsetColName)
        if PasswordCol:
            ColValue = getSpecialColumnVaule(RsetColName, option)
        else:
            ColValue = option["entry_parameter"].get("parameter").get(RsetColName)

    elif option["cmd_type"] == "Discard" or option["cmd_type"] == "Restore":
        ColValue = option["current_parameter"].get("parameter").get(RsetColName)
    return ColValue


def getColumnValueFromOptionData(objdbca, objtable, option):
    """
      Optionデータからカラム入力値取得
      Arguments:
        objdbca :DB接続クラスインスタンス
        objtabl :メニュー情報、カラム紐付、関連情報
        option :パラメータ、その他設定値
      Returns:
        ColValue: カラム入力値
        RestNameConfig: Restカラム名辞書
    """
    RestNameConfig = {}
    MenuId = objtable['MENUINFO']['MENU_ID']
    sql = "SELECT COL_NAME,COLUMN_NAME_REST,COLUMN_CLASS FROM T_COMN_MENU_COLUMN_LINK WHERE MENU_ID = '%s' and DISUSE_FLAG = '0'" % (MenuId)
    restcolnamerow = objdbca.sql_execute(sql, [])
    ColValue = {}
    for row in restcolnamerow:
        RestNameConfig[row["COL_NAME"]] = row["COLUMN_NAME_REST"]
        PasswordCol = False
        if row['COLUMN_CLASS'] == '8': # PasswordColumn	パスワード
            PasswordCol = True
        ColValue[row["COL_NAME"]] = getColumnValue(option, RestNameConfig[row["COL_NAME"]], PasswordCol)
    return ColValue, RestNameConfig
