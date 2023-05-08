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

from flask import g
from common_libs.cicd.functions.util import getColumnValueFromOptionData
from common_libs.cicd.classes.cicd_definition import TD_SYNC_STATUS_NAME_DEFINE, TD_B_CICD_GIT_PROTOCOL_TYPE_NAME, TD_B_CICD_GIT_REPOSITORY_TYPE_NAME


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
    msg = ''
    # 各カラムの入力データを取得
    ColValue, RestNameConfig = getColumnValueFromOptionData(objdbca, objtable, option)

    # プロトコルタイプ: https
    if ColValue['GIT_PROTOCOL_TYPE_ROW_ID'] == TD_B_CICD_GIT_PROTOCOL_TYPE_NAME.C_GIT_PROTOCOL_TYPE_ROW_ID_HTTPS:
        # リポジトリタイプ必須入力チェック
        if not ColValue['GIT_REPO_TYPE_ROW_ID']:
            # プロトコルでhttpsを選択している場合は、入力が必須な項目です。(項目:Visibilityタイプ)
            status_code = "MSG-90018"
            msg_args = []
            if len(msg) != 0:
                msg += "\n"
            msg += g.appmsg.get_api_message(status_code, msg_args)
            retBool = False

        # リポジトリタイプ: Public
        elif ColValue['GIT_REPO_TYPE_ROW_ID'] == TD_B_CICD_GIT_REPOSITORY_TYPE_NAME.C_GIT_REPO_TYPE_ROW_ID_PUBLIC:
            # Gitユーザ未入力チェック
            if ColValue['GIT_USER']:
                # プロトコルでhttpsを選択し、VisibilityタイプでPrivateを選択している場合以外は、入力が不要な項目です。(項目:Gitユーザ)
                status_code = "MSG-90014"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False

            # Gitパスワード未入力チェック
            if ColValue['GIT_PASSWORD']:
                # プロトコルでhttpsを選択し、VisibilityタイプでPrivateを選択している場合以外は、入力が不要な項目です。(項目:Gitパスワード)
                status_code = "MSG-90015"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False

        # リポジトリタイプ: private
        elif ColValue['GIT_REPO_TYPE_ROW_ID'] == TD_B_CICD_GIT_REPOSITORY_TYPE_NAME.C_GIT_REPO_TYPE_ROW_ID_PRIVATE:
            # Gitユーザ必須入力チェック
            if not ColValue['GIT_USER']:
                # プロトコルでhttpsを選択し、VisibilityタイプでPrivateを選択している場合は、入力が必須な項目です。(項目:Gitユーザ)
                status_code = "MSG-90019"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False

            # Gitパスワード未入力チェック
            if not ColValue['GIT_PASSWORD']:
                # プロトコルでhttpsを選択し、VisibilityタイプでPrivateを選択している場合は、入力が必須な項目です。(項目:Gitパスワード)
                status_code = "MSG-90020"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False
        else:
            # リポジトリタイプ不正
            # 選択されているVisibilityタイプが不正です。
            status_code = "MSG-90002"
            msg_args = []
            if len(msg) != 0:
                msg += "\n"
            msg += g.appmsg.get_api_message(status_code, msg_args)
            retBool = False

        # sshパスワード未入力チェック
        if ColValue['SSH_PASSWORD']:
            # プロトコルでsshパスワード認証以外を選択している場合は、入力が不要な項目です。(項目:ssh接続情報/パスワード)
            status_code = "MSG-90011"
            msg_args = []
            if len(msg) != 0:
                msg += "\n"
            msg += g.appmsg.get_api_message(status_code, msg_args)
            retBool = False
        # sshパスフレーズ未入力チェック
        if ColValue['SSH_PASSPHRASE']:
            # プロトコルでssh鍵認証(パスフレーズあり)以外を選択している場合は、入力が不要な項目です。(項目:ssh接続情報/パスフレーズ)
            status_code = "MSG-90012"
            msg_args = []
            if len(msg) != 0:
                msg += "\n"
            msg += g.appmsg.get_api_message(status_code, msg_args)
            retBool = False

    # プロトコルタイプ: ssh(パスワード認証)/ssh(鍵認証パスフレーズあり)/ssh(鍵認証パスフレーズなし)
    elif ColValue['GIT_PROTOCOL_TYPE_ROW_ID'] in (TD_B_CICD_GIT_PROTOCOL_TYPE_NAME.C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_PASS,
                                                  TD_B_CICD_GIT_PROTOCOL_TYPE_NAME.C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_KEY,
                                                  TD_B_CICD_GIT_PROTOCOL_TYPE_NAME.C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_KEY_NOPASS):
        # リポジトリタイプ未入力チェック
        """
        if ColValue['GIT_REPO_TYPE_ROW_ID']:
            # プロトコルでhttps以外を選択している場合は、入力が不要な項目です。(項目:Visibilityタイプ)
            status_code = "MSG-90013"
            msg_args = []
            if len(msg) != 0:
                msg += "\n"
            msg += g.appmsg.get_api_message(status_code, msg_args)
            retBool = False
        """

        # Gitユーザ未入力チェック
        if ColValue['GIT_USER']:
            # プロトコルでhttpsを選択し、VisibilityタイプでPrivateを選択している場合以外は、入力が不要な項目です。(項目:Gitユーザ)
            status_code = "MSG-90014"
            msg_args = []
            if len(msg) != 0:
                msg += "\n"
            msg += g.appmsg.get_api_message(status_code, msg_args)
            retBool = False

        # Gitパスワード未入力チェック
        if ColValue['GIT_PASSWORD']:
            # プロトコルでhttpsを選択し、VisibilityタイプでPrivateを選択している場合以外は、入力が不要な項目です。(項目:Gitパスワード)
            status_code = "MSG-90015"
            msg_args = []
            if len(msg) != 0:
                msg += "\n"
            msg += g.appmsg.get_api_message(status_code, msg_args)
            retBool = False

        # プロトコルタイプ: ssh(パスワード認証)
        if ColValue['GIT_PROTOCOL_TYPE_ROW_ID'] == TD_B_CICD_GIT_PROTOCOL_TYPE_NAME.C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_PASS:
            # sshパスワード必須入力チェック
            if not ColValue['SSH_PASSWORD']:
                # プロトコルでsshパスワード認証を選択している場合は、入力は必須な項目です。(項目:ssh接続情報/パスワード)
                status_code = "MSG-90016"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False
            # sshパスフレーズ未入力チェック
            if ColValue['SSH_PASSPHRASE']:
                # プロトコルでssh鍵認証(パスフレーズあり)以外を選択している場合は、入力が不要な項目です。(項目:ssh接続情報/パスフレーズ)
                status_code = "MSG-90012"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False

        # プロトコルタイプ: ssh(鍵認証パスフレーズあり)
        elif ColValue['GIT_PROTOCOL_TYPE_ROW_ID'] == TD_B_CICD_GIT_PROTOCOL_TYPE_NAME.C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_KEY:
            # sshパスワード未入力チェック
            if ColValue['SSH_PASSWORD']:
                # プロトコルでsshパスワード認証以外を選択している場合は、入力が不要な項目です。(項目:ssh接続情報/パスワード)
                status_code = "MSG-90011"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False

            # sshパスフレーズ必須入力チェック
            if not ColValue['SSH_PASSPHRASE']:
                # プロトコルでssh鍵認証(パスフレーズあり)を選択している場合は、入力が必須な項目です。(項目:ssh接続情報/パスフレーズ)
                status_code = "MSG-90017"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False

        # プロトコルタイプ: ssh(鍵認証パスフレーズなし)
        elif ColValue['GIT_PROTOCOL_TYPE_ROW_ID'] == TD_B_CICD_GIT_PROTOCOL_TYPE_NAME.C_GIT_PROTOCOL_TYPE_ROW_ID_SSH_KEY_NOPASS:
            # sshパスワード未入力チェック
            if ColValue['SSH_PASSWORD']:
                # プロトコルでsshパスワード認証以外を選択している場合は、入力が不要な項目です。(項目:ssh接続情報/パスワード)
                status_code = "MSG-90011"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False

            # sshパスフレーズ未入力チェック
            if ColValue['SSH_PASSPHRASE']:
                # プロトコルでssh鍵認証(パスフレーズあり)以外を選択している場合は、入力が不要な項目です。(項目:ssh接続情報/パスフレーズ)
                status_code = "MSG-90012"
                msg_args = []
                if len(msg) != 0:
                    msg += "\n"
                msg += g.appmsg.get_api_message(status_code, msg_args)
                retBool = False
    else:
        # 選択されているプロトコルが不正です。
        status_code = "MSG-90001"
        msg_args = []
        if len(msg) != 0:
            msg += "\n"
        msg += g.appmsg.get_api_message(status_code, msg_args)
        retBool = False

    # 同期状態・同期エラー情報・同期時刻を更新
    if option["cmd_type"] in ("Register", "Update", "Restore"):
        option["entry_parameter"]["parameter"][RestNameConfig["SYNC_STATUS_ROW_ID"]] = TD_SYNC_STATUS_NAME_DEFINE.STS_NONE
        option["entry_parameter"]["parameter"][RestNameConfig["SYNC_ERROR_NOTE"]] = None
        option["entry_parameter"]["parameter"][RestNameConfig["SYNC_LAST_TIMESTAMP"]] = None

    return retBool, msg, option,
