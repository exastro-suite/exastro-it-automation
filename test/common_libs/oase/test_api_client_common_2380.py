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
import sys
from flask import Flask, g
import json
from dotenv import load_dotenv  # python-dotenv
import jmespath

# /exastro/
from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate
from common_libs.conductor.classes.exec_util import *

# モジュール探査パス(PYTHONPATH)にita_root/ita_by_oase_conclusionを追加
sys.path.append('/workspace/ita_root/common_libs/oase/')
from api_client_common import APIClientCommon # type: ignore

class test_const:
    """通知データクラスのテスト用定数クラス
    """
    # オーガナイゼーションID
    #   「オーガナイゼーション一覧」画面の「オーガナイゼーションID」
    ORGANIZATION_ID = 'org001'
    # ワークスペースID
    #   「ワークスペース一覧」画面の「ワークスペース一ID」
    WORKSPACE_ID = "workspace_001"
    # ログレベル(ERROR|INFO|DEBUG)
    LOG_LEVEL = 'INFO'
    # ログ出力言語('ja':日本語  'en':English)
    LANGUAGE = 'ja'
    # レスポンスリストフラグが、オブジェクト
    OBJ = '0'
    # レスポンスリストフラグが、配列
    LIST = '1'

def main():
    """ #2380
        【要望】【OASE】レスポンスキー・レスポンスリストフラグ・レスポンスIDキー
        が間違っていても、イベントとして取り込めるようにしたい
        https://github.com/exastro-suite/exastro-it-automation/issues/2380

        ▼前提条件
        ・ita-api-organizationコンテナでテストを行う
        ・パッケージ「jmespath」がインストールできていないのでテストできないため、
          下記の操作で、「jmespath」をインストールを行う
          - ターミナルで下記コマンドを投入して、パッケージ「jmespath」の有無を確認
            $ poetry show
          - 「jmespath」を下記のコマンドを投入してインストール
            $ poetry add --group develop_build "jmespath>=0.0.0"
          - 再度下記のコマンドで、「jmespath」がインストールできたことを確認
            $ poetry show
            jmespath     1.0.1     JSON Matching Expressions
          - VM環境へログインし、dockerを再起動（再起動しないと、反映されない）
            $ cd ~/<ユーザー名>/exastro-it-automation-dev/.devcontainer
            $ docker-compose up -d
            （VMの空きディスク容量が不足し、正常に起動しない場合、
              VMにログイン>dockerコンテナ停止>Dockerイメージ削除>docerkキャッシュ削除>
              構築手順>開発コンテナ環境 起動確認から操作して、コンテナを起動する）

          -【注意】
             -  ソース管理に、下記の２ファイルが追加されるが、コミットとプッシュはしないこと
               - poetry.log
               - pyproject.toml
             - テスト完了後は、「変更の取り消し」で元に戻す
        ・本ファイルをデバッグ・実行する場合、

        ▼テストケース
                | ﾚｽﾎﾟﾝｽｷｰ |ﾚｽﾎﾟﾝｽﾘｽﾄﾌﾗｸﾞ |ｲﾍﾞﾝﾄIDｷｰ| 重複     | 素イベント                         | 返却イベント                              | _exastro_oase_event_id
        ケース1  | 未指定   | オブジェクト | 未指定  | ー       | {…}                               | {…}                                      | 日時シリアル値
        ケース2  | 未指定   | オブジェクト | 指定    | 空       | {…}                               | {…}                                      | イベントIDキーの値
        ケース3  | 未指定   | オブジェクト | 指定    | 指定     | {…}                               | { } 空JSON                                | ー
        ケース4  | 未指定   | 配列         | 未指定  | ー       | [ {…}, {…} ]                     | [ {…}, {…} ]                            | 日時シリアル値
        ケース5  | 未指定   | 配列         | 指定    | 空       | [ {…}, {…} ]                     | [ {…}, {…} ]                            | イベントIDキーの値
        ケース6  | 未指定   | 配列         | 指定    | １件指定 | [ {…}, {…} ]                     | [ {…}]                                   | イベントIDキーの値
        ケース7  | 未指定   | 配列         | 指定    | 全件指定 | [ {…}, {…} ]                     | { } 空JSON                                | ー
        ケース8  | 指定     | オブジェクト | 未指定  | ー       | {"RESPONS_KEY": {…}}              | RESPONS_KEYの値 { …  }                   | 日時シリアル値
        ケース9  | 指定     | オブジェクト | 指定    | 空       | {"RESPONS_KEY": {…}}              | RESPONS_KEYの値 { …  }                   | イベントIDキーの値
        ケース10 | 指定     | オブジェクト | 指定    | 指定     | {"RESPONS_KEY": {…}}              | { } 空JSON                                | イベントIDキーの値
        ケース11 | 指定     | 配列         | 未指定  | ー       | {"RESPONS_KEY": [  {…}, {…}} ] } | RESPONS_KEYの値  [ {…}, {…} ]           | 日時シリアル値
        ケース12 | 指定     | 配列         | 指定    | 空       | {"RESPONS_KEY": [  {…}, {…}} ] } | RESPONS_KEYの値  [ {…}, {…} ]           | イベントIDキーの値
        ケース13 | 指定     | 配列         | 指定    | １件指定 | {"RESPONS_KEY": [  {…}, {…}} ] } | RESPONS_KEYの値で、重複しない  [ {…}  ]  | イベントIDキーの値
        ケース14 | 指定     | 配列         | 指定    | 全件指定 | {"RESPONS_KEY": [  {…}, {…}} ] } | { } 空JSON                                | ー
        ケース15 | 間違い   | オブジェクト | ー      | ー       | {…}                               | {…}                                      | 日時シリアル値
        ケース16 | 間違い   | オブジェクト | ー      | ー       | [ {…}, {…} ]                     | { [ {…}, {…} ] }                        | 日時シリアル値
        ケース17 | 間違い   | 配列         | ー      | ー       | {…}                               | [ {…} ]                                  | 日時シリアル値
        ケース18 | 間違い   | 配列         | ー      | ー       | [ {…}, {…} ]                     | [ {…}, {…} ]                            | 日時シリアル値
        ケース19 | 未指定   | OBJ間違え    | ー      | ー       | [ {…}, {…} ]                     | [ {…}, {…} ]                            | 日時シリアル値
        ケース20 | 未指定   | 配列間違え   | ー      | ー       | {…}                               | {…}                                      | 日時シリアル値
        ケース21 | 指定     | OBJ間違え    | ー      | ー       | {"RESPONS_KEY": [  {…}, {…}} ] } | {"RESPONS_KEY": [  {…}, {…}} ] }        | 日時シリアル値
        ケース22 | 指定     | 配列間違え   | ー      | ー       | {"RESPONS_KEY": {…}}              | {"RESPONS_KEY": {…}}                     | 日時シリアル値
        ケース23 | 未指定   | オブジェクト | 間違い  | ー       | {…}                               | {…}                                      | 日時シリアル値
        ケース24 | 未指定   | 配列         | 間違い  | ー       | [ {…}, {…} ]                     | [ {…}, {…} ]                            | 日時シリアル値
        ケース25 | 指定     | オブジェクト | 間違い  | ー       | {"RESPONS_KEY": {…}}              | RESPONS_KEYの値 { …  }                   | 日時シリアル値
        ケース26 | 指定     | 配列         | 間違い  | ー       | {"RESPONS_KEY": [  {…}, {…}} ] } | RESPONS_KEYの値  [ {…}, {…} ]           | 日時シリアル値

    """

    # 環境変数取得
    load_dotenv(override=True)
    os.environ['EXASTRO_ORGANIZATION_ID'] = test_const.ORGANIZATION_ID
    os.environ['EXASTRO_WORKSPACE_ID'] = test_const.WORKSPACE_ID
    os.environ['LANGUAGE'] = test_const.LANGUAGE

    flask_app = Flask(__name__)
    with flask_app.app_context():
        try:

            # ログ設定
            setLog()

            print("==========")
            print("")

            # テストケースNoをグローバル変数として利用
            global test_case
            test_case = 0

            # 既存機能
            existingFunctions()

            # ↓ここでブレイクポイントを設定しないと、既存機能のログが消える。
            print("==========")

            # 追加機能 - レスポンスキーが間違い
            wrongResponsKey()

            # 追加機能 - レスポンスリストフラフ間違い
            wrongResponsListFlag()

            # 追加機能 - イベントIDキーが間違い
            wrongEventIdKey()

            print("ooooo テスト【正常】終了 ooooo")

        except Exception as e:
            t = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
            print("xxxxx   テスト【失敗】終了   xxxxx")
        finally:
            print("----- コンソールsh通力要確認 -----")


def existingFunctions():
    """既存機能のテスト
    """

    # ここから、既存機能・レスポンスキー未指定

    comment = {
        'name': '既存機能・レスポンスキー未指定 その１',
        'content1' : 'レスポンスリストフラグをオブジェクト',
        'content2' : 'イベントIDキー未指定',
        'content3' : '重複キーチェックなし',
        'content4' : 'イベントモック：トップがオブジェクト型( {...} )',
        'expect': '素イベントの内容が返却、_exastro_oase_event_idは日時シリアル値'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = None
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = None
    event_settings["SAVED_IDS"] = []
    # トップがオブジェクト型のイベントモックを取得
    json_raw = getTopLevelObject_Event()
    respons_json = execTest(comment, event_settings, json_raw)

    comment = {
        'name': '既存機能・レスポンスキー未指定 その２',
        'content1' : 'レスポンスリストフラグをオブジェクト',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型( {...} )',
        'expect': '素イベントの内容が返却、_exastro_oase_event_idはイベントIDキー'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = None
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # トップがオブジェクト型のイベントモックを取得
    json_raw = getTopLevelObject_Event()
    respons_json = execTest(comment, event_settings, json_raw)


    comment = {
        'name': '既存機能・レスポンスキー未指定 その３',
        'content1' : 'レスポンスリストフラグをオブジェクト',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キー1件あり',
        'content4' : 'イベントモック：トップがオブジェクト型( {...} )',
        'expect': '空のイベント返却'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = None
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = ['e554be49-ef18-4603-9c90-35cb8a7b8cf2']
    # トップがオブジェクト型のイベントモックを取得
    json_raw = getTopLevelObject_Event()
    respons_json = execTest(comment, event_settings, json_raw)


    comment = {
        'name': '既存機能・レスポンスキー未指定 その４',
        'content1' : 'レスポンスリストフラグを配列',
        'content2' : 'イベントIDキー未指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップが配列型( [ {...}, {...} ] )',
        'expect': '素イベントの内容が返却、_exastro_oase_event_idは日時シリアル値'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = None
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = None
    event_settings["SAVED_IDS"] = []
    # トップが配列型のイベントモックを取得
    json_raw = getTopLevelList_Events()
    respons_json = execTest(comment, event_settings, json_raw)


    comment = {
        'name': '既存機能・レスポンスキー未指定 その５',
        'content1' : 'レスポンスリストフラグを配列',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップが配列型( [ {...}, {...} ] )',
        'expect': '素イベントの内容が返却、_exastro_oase_event_idはイベントIDキー'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = None
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # トップが配列型のイベントモックを取得
    json_raw = getTopLevelList_Events()
    respons_json = execTest(comment, event_settings, json_raw)


    comment = {
        'name': '既存機能・レスポンスキー未指定 その５',
        'content1' : 'レスポンスリストフラグを配列',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キー１件あり',
        'content4' : 'イベントモック：トップが配列型( [ {...}, {...} ] )',
        'expect': '2件中1件（重複なし）のイベント返却'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = None
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = ['f554be49-ef18-4603-9c90-35cb8a7b8cf2']
    # トップが配列型のイベントモックを取得
    json_raw = getTopLevelList_Events()
    respons_json = execTest(comment, event_settings, json_raw)

    comment = {
        'name': '既存機能・レスポンスキー未指定 その７',
        'content1' : 'レスポンスリストフラグを配列',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キー全件あり',
        'content4' : 'イベントモック：トップが配列型( [ {...}, {...} ] )',
        'expect': '空のイベント返却'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = None
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = ['f554be49-ef18-4603-9c90-35cb8a7b8cf2', 'e554be49-ef18-4603-9c90-35cb8a7b8cf2']
    # トップが配列型のイベントモックを取得
    json_raw = getTopLevelList_Events()
    respons_json = execTest(comment, event_settings, json_raw)


    # ここから、既存機能・レスポンスキー指定

    comment = {
        'name': '既存機能・レスポンスキー指定 その１',
        'content1' : 'レスポンスリストフラグをオブジェクト',
        'content2' : 'イベントIDキー未指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型のオブジェクトイベント( { "xxx" : {...} } )',
        'expect': '素イベントの内容が返却、_exastro_oase_event_idは日時シリアル値'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'data'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = None
    event_settings["SAVED_IDS"] = []
    # トップがオブジェクト型のオブジェクトイベントモックを取得
    json_raw = getTopLevelObject_ObjectEvent()
    respons_json = execTest(comment, event_settings, json_raw)

    comment = {
        'name': '既存機能・レスポンスキー指定 その２',
        'content1' : 'レスポンスリストフラグをオブジェクト',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型のオブジェクトイベント( { "xxx" : {...} } )',
        'expect': '素イベントの内容が返却、_exastro_oase_event_idはイベントIDキー'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'data'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # トップがオブジェクト型のイベントモックを取得
    json_raw = getTopLevelObject_ObjectEvent()
    respons_json = execTest(comment, event_settings, json_raw)


    comment = {
        'name': '既存機能・レスポンスキー指定 その３',
        'content1' : 'レスポンスリストフラグをオブジェクト',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キー1件あり',
        'content4' : 'イベントモック：トップがオブジェクト型のオブジェクトイベント( { "xxx" : {...} } )',
        'expect': '空のイベント返却'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'data'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = ['e554be49-ef18-4603-9c90-35cb8a7b8cf2']
    # トップがオブジェクト型のイベントモックを取得
    json_raw = getTopLevelObject_ObjectEvent()
    respons_json = execTest(comment, event_settings, json_raw)

    comment = {
        'name': '既存機能・レスポンスキー指定 その４',
        'content1' : 'レスポンスリストフラグを配列',
        'content2' : 'イベントIDキー未指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型の配列イベント( { "xxx" : [ {...}, {...} ] } )',
        'expect': '素イベントの内容が返却、_exastro_oase_event_idは日時シリアル値'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'data'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = None
    event_settings["SAVED_IDS"] = []
    # トップがオブジェクト型でキー："data"が配列型のイベントモックを取得
    json_raw = getTopLevelObject_ObjectEventList()
    respons_json = execTest(comment, event_settings, json_raw)


    comment = {
        'name': '既存機能・レスポンスキー指定 その５',
        'content1' : 'レスポンスリストフラグを配列',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型の配列イベント( { "xxx" : [ {...}, {...} ] } )',
        'expect': '素イベントの内容が返却、_exastro_oase_event_idはイベントIDキー'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'data'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # トップがオブジェクト型でキー："data"が配列型のイベントモックを取得
    json_raw = getTopLevelObject_ObjectEventList()
    respons_json = execTest(comment, event_settings, json_raw)


    comment = {
        'name': '既存機能・レスポンスキー指定 その５',
        'content1' : 'レスポンスリストフラグを配列',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キー1件あり',
        'content4' : 'イベントモック：トップがオブジェクト型の配列イベント( { "xxx" : [ {...}, {...} ] } )',
        'expect': '2件中1件（重複なし）のイベント返却'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'data'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = ['f554be49-ef18-4603-9c90-35cb8a7b8cf2']
    # トップがオブジェクト型でキー："data"が配列型のイベントモックを取得
    json_raw = getTopLevelObject_ObjectEventList()
    respons_json = execTest(comment, event_settings, json_raw)

    comment = {
        'name': '既存機能・レスポンスキー指定 その７',
        'content1' : 'レスポンスリストフラグを配列',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キー全件あり',
        'content4' : 'イベントモック：トップがオブジェクト型の配列イベント( { "xxx" : [ {...}, {...} ] } )',
        'expect': '空のイベント返却'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'data'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = ['f554be49-ef18-4603-9c90-35cb8a7b8cf2', 'e554be49-ef18-4603-9c90-35cb8a7b8cf2']
    # トップがオブジェクト型でキー："data"が配列型のイベントモックを取得
    json_raw = getTopLevelObject_ObjectEventList()
    respons_json = execTest(comment, event_settings, json_raw)


def wrongResponsKey():
    """レスポンスキーが間違い
    """

    comment = {
        'name': '新機能・レスポンスキー間違い その１',
        'content1' : 'レスポンスリストフラグをオブジェクトで、イベントがオブジェクト型',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型( {...} )',
        'expect': '素イベントが、オブジェクト型で取得できること'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'xxx'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # オブジェクト型イベントモックを取得
    json_raw = getTopLevelObject_Event()
    respons_json = execTest(comment, event_settings, json_raw)

    comment = {
        'name': '新機能・レスポンスキー間違い その２',
        'content1' : 'レスポンスリストフラグをオブジェクトで、イベントが配列型',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップが配列型( [ {...}, {...} ] )',
        'expect': '素イベントが、配列型で取得できること'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'xxx'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # 配列型イベントモックを取得
    json_raw = getTopLevelList_Events()
    respons_json = execTest(comment, event_settings, json_raw)


    comment = {
        'name': '新機能・レスポンスキー間違い その３',
        'content1' : 'レスポンスリストフラグを配列で、イベントがオブジェクト型',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型のオブジェクトイベント( { "xxx": {...} } )',
        'expect': '素イベントが、オブジェクト型で"data"キーがあるイベントが取得できること'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'xxx'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # オブジェクト型イベントモックを取得
    json_raw = getTopLevelObject_ObjectEvent()
    respons_json = execTest(comment, event_settings, json_raw)


    comment = {
        'name': '新機能・レスポンスキー間違い その４',
        'content1' : 'レスポンスリストフラグを配列で、イベントが配列',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型の配列イベント( { "xxx" : [ {...}, {...} ] } )',
        'expect': '素イベントが、配列型で取得できること'
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'xxx'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # 配列型型イベントモックを取得
    json_raw = getTopLevelObject_ObjectEventList()
    respons_json = execTest(comment, event_settings, json_raw)

def wrongResponsListFlag():
    """レスポンスリストフラフ間違い
    """
    comment = {
        'name': '新機能・レスポンスリストフラグが(オブジェクト）間違い その１',
        'content1' : 'レスポンスキーを未指定',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップが配列型( [ {...}, {...} ] )',
        'expect': '素イベントが取得できること、_exastro_oase_event_idは日時シリアル値 '
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = None
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # 配列型イベントモックを取得
    json_raw = getTopLevelList_Events()
    respons_json = execTest(comment, event_settings, json_raw)

    comment = {
        'name': '新機能・レスポンスリストフラグが(オブジェクト）間違い その２',
        'content1' : 'レスポンスキーを指定',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型の配列イベント( { "xxx": [ {...}, {... } ] } )',
        'expect': '素イベントが取得できること、_exastro_oase_event_idは日時シリアル値 '
    }
    # レスポンスキー：None(未指定)
    # レスポンスリストフラグ: 0(オブジェクト)
    # イベントIDキー: "labels.__alert_rule_uid__"
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'data'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # 配列型イベントモックを取得
    json_raw = getTopLevelObject_ObjectEventList()
    respons_json = execTest(comment, event_settings, json_raw)


    comment = {
        'name': '新機能・レスポンスリストフラグが（配列）間違い その１',
        'content1' : 'レスポンスキーを未指定',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型( {...} )',
        'expect': '素イベントが取得できること、_exastro_oase_event_idは日時シリアル値 '
    }
    event_settings["RESPONSE_KEY"] = None
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # オブジェクト型イベントモックを取得
    json_raw = getTopLevelObject_Event()
    respons_json = execTest(comment, event_settings, json_raw)

    comment = {
        'name': '新機能・レスポンスリストフラグが（配列）間違い その２',
        'content1' : 'レスポンスキーを指定',
        'content2' : 'イベントIDキー指定',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型のオブジェクトイベント( { "xxx": {...} } )',
        'expect': '素イベントが取得できること、_exastro_oase_event_idは日時シリアル値 '
    }
    event_settings["RESPONSE_KEY"] = 'data'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    event_settings["SAVED_IDS"] = []
    # オブジェクト型イベントモックを取得
    json_raw = getTopLevelObject_ObjectEvent()
    respons_json = execTest(comment, event_settings, json_raw)

def wrongEventIdKey():
    """イベントIDキーが間違い
    """
    comment = {
        'name': '新機能・イベントIDキーが間違い その１',
        'content1' : 'レスポンスキーを未指定',
        'content2' : 'レスポンスリストフラグがオブジェクト',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型( {...} )',
        'expect': '素イベントが取得できること、_exastro_oase_event_idは日時シリアル値 '
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = None
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = 'labels.xxx'
    event_settings["SAVED_IDS"] = []
    # 配列型イベントモックを取得
    json_raw = getTopLevelObject_Event()
    respons_json = execTest(comment, event_settings, json_raw)

    comment = {
        'name': '新機能・イベントIDキーが間違い その２',
        'content1' : 'レスポンスキーを未指定',
        'content2' : 'レスポンスリストフラグが配列',
        'content3' : '重複キーなし',
         'content4' : 'イベントモック：トップが配列型( [ {...}, {...} ] )',
       'expect': '素イベントが取得できること、_exastro_oase_event_idは日時シリアル値 '
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = None
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.xxx'
    event_settings["SAVED_IDS"] = []
    # 配列型イベントモックを取得
    json_raw = getTopLevelList_Events()
    respons_json = execTest(comment, event_settings, json_raw)

    comment = {
        'name': '新機能・イベントIDキーが間違い その３',
        'content1' : 'レスポンスキーを指定',
        'content2' : 'レスポンスリストフラグがオブジェクト',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型のオブジェクトイベント( { "xxx" : {...} } )',
        'expect': 'レスポンスキーの値が取得できること、_exastro_oase_event_idは日時シリアル値 '
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'data'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.OBJ
    event_settings["EVENT_ID_KEY"]  = 'labels.xxx'
    event_settings["SAVED_IDS"] = []
    # 配列型イベントモックを取得
    json_raw = getTopLevelObject_ObjectEvent()
    respons_json = execTest(comment, event_settings, json_raw)

    comment = {
        'name': '新機能・イベントIDキーが間違い',
        'content1' : 'レスポンスキーを指定',
        'content2' : 'レスポンスリストフラグが配列',
        'content3' : '重複キーなし',
        'content4' : 'イベントモック：トップがオブジェクト型の配列イベント( { "xxx": [ {...}, {...} ] } )',
        'expect': 'レスポンスキーの値の配列が取得できること、_exastro_oase_event_idは日時シリアル値 '
    }
    event_settings = getDefaultEventSettings()
    event_settings["RESPONSE_KEY"] = 'data'
    event_settings["RESPONSE_LIST_FLAG"] = test_const.LIST
    event_settings["EVENT_ID_KEY"]  = 'labels.xxx'
    event_settings["SAVED_IDS"] = []
    # 配列型イベントモックを取得
    json_raw = getTopLevelObject_ObjectEventList()
    respons_json = execTest(comment, event_settings, json_raw)


def execTest(comment, setting, json_raw):
    """テスト実行

    Args:
        event_settings (_type_): _description_
        json_raw (_type_): _description_

    Returns:
        _type_: _description_
    """
    global test_case
    test_case += 1
    events = []
    fetched_time = datetime.datetime.now()  # API取得時間

    print("#%02d %s ---------" % (test_case, comment["name"]))
    print("  %s " % comment["content1"])
    print("  %s " % comment["content2"])
    print("  %s " % comment["content3"])
    print("  %s " % comment["content4"])
    print("....▼引数")
    respons_key = setting["RESPONSE_KEY"] if setting["RESPONSE_KEY"] else "None"
    respons_list_flag =  setting["RESPONSE_LIST_FLAG"] if setting["RESPONSE_LIST_FLAG"] else "None"
    event_id_key = setting["EVENT_ID_KEY"] if setting["EVENT_ID_KEY"] else "None"
    saved_ids = setting["SAVED_IDS"] if setting["SAVED_IDS"] else "None"
    print("     RESPONSE_KEY: '%s'" % respons_key)
    print("     RESPONSE_LIST_FLAG: '%s'" % respons_list_flag)
    print("     EVENT_ID_KEY: '%s'" % event_id_key)
    print("     SAVED_IDS: '%s'" % saved_ids)
    print("....▼期待値")
    print("      %s " % comment["expect"])
    #print("....▼素イベント")
    #print("")
    #print(json.dumps(json_raw, indent=2))

    # テスト対象を生成
    apiClientCommon = APIClientCommon(setting)
    # 新規イベント取得
    call_api_result, json_data = apiClientCommon.get_new_events(json_raw)


    if len(json_data) == 0:
      # collect_event.pyでは、イベントが空の場合、読み飛ばし（78行目のif）
      pass
    else:
      # api_client_commonからイベントが返却され、
      # collect_event.pyの82行～112行までの処理と同等な処理をテストする
    # 設定で指定したキーの値を取得
      if call_api_result:
          respons_key_json_data = get_value_from_jsonpath(setting["RESPONSE_KEY"], json_data)
          if respons_key_json_data is None:
              # レスポンスキーが未指定、または間違っている場合、受信したイベントで以降処理する。
              g.applogger.info(g.appmsg.get_log_message("AGT-10002", [setting["RESPONSE_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"]]))
          else:
              # レスポンスキーで取得できた場合、レスポンスキーの値で以降処理する。
              json_data = respons_key_json_data

      # RESPONSE_LIST_FLAGの値がリスト形式ではない場合、そのまま辞書に格納する
      if setting["RESPONSE_LIST_FLAG"] == "0":
          # 値がリスト形式かチェック
          if isinstance(json_data, list) is True:
              g.applogger.info(g.appmsg.get_log_message("AGT-10031", [setting["RESPONSE_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"]]))
              for data in json_data:
                  event = init_label(data, fetched_time, setting)
                  events.append(event)
          else:
              if len(json_data) > 0:
                  event = init_label(json_data, fetched_time, setting)
                  events.append(event)

      # RESPONSE_LIST_FLAの値がリスト形式の場合、1つずつ辞書に格納
      else:
          # 値がリスト形式かチェック
          if isinstance(json_data, list) is False:
              g.applogger.info(g.appmsg.get_log_message("AGT-10003", [setting["RESPONSE_KEY"], setting["EVENT_COLLECTION_SETTINGS_ID"]]))
              if len(json_data) > 0:
                  event = init_label(json_data, fetched_time, setting)
                  events.append(event)
          else:
              for data in json_data:
                  event = init_label(data, fetched_time, setting)
                  events.append(event)

    print("....▼レスポンス・イベント")
    print("")
    print(json.dumps(events, indent=2))
    print("")
    print("-------------------")

def setLog():
    """
    ログの設定
    """
    organization_id = os.environ.get("EXASTRO_ORGANIZATION_ID")
    workspace_id = os.environ.get("EXASTRO_WORKSPACE_ID")
    g.ORGANIZATION_ID = organization_id
    g.WORKSPACE_ID = workspace_id
    g.AGENT_NAME = os.environ.get("AGENT_NAME", "agent-oase-01")
    g.USER_ID = os.environ.get("USER_ID")
    g.LANGUAGE = os.environ.get("LANGUAGE")

    # create app log instance and message class instance
    g.applogger = AppLog()
    g.applogger.set_level(os.environ.get("LOG_LEVEL", test_const.LOG_LEVEL))
    g.appmsg = MessageTemplate(g.LANGUAGE)


def getDefaultEventSettings():
    """_summary_イベント設定取得
    """

    event_settings = {}
    # イベント設定ID
    event_settings["EVENT_COLLECTION_SETTINGS_ID"] = 'a30e9dfd-d178-4842-9ed5-cb6a1d0c4ee9'
    event_settings["EVENT_COLLECTION_SETTINGS_NAME"] = 'Issues #2380'
    event_settings["REQUEST_METHOD_ID"] = '1'
    event_settings["URL"] = 'http://localhost'
    event_settings["PORT"] = None
    event_settings["REQUEST_HEADER"] = None
    event_settings["PROXY"] = None
    event_settings["AUTH_TOKEN"] = None
    event_settings["USERNAME"] = None
    event_settings["PASSWORD"] = None
    event_settings["ACCESS_KEY_ID"] = None
    event_settings["SECRET_ACCESS_KEY"] = None
    event_settings["MAILBOXNAME"] = None
    event_settings["PARAMETER"] = None
    event_settings["LAST_FETCHED_TIMESTAMP"] = None
    event_settings["TTL"] = 6000

    # レスポンスキー
    event_settings["RESPONSE_KEY"] = None # 最上位をイベントとして扱う
    # レスポンスリストフラグ
    event_settings["RESPONSE_LIST_FLAG"] = '1'  # 配列
    # イベントIDキー
    event_settings["EVENT_ID_KEY"]  = 'labels.__alert_rule_uid__'
    # 保存済みキー配列
    event_settings["SAVED_IDS"] = []
    return event_settings

# ドット区切りの文字列で辞書を指定して値を取得
def get_value_from_jsonpath(jsonpath=None, data=None):
    if jsonpath is None:
        return data

    value = jmespath.search(jsonpath, data)
    return value

def init_label(data, fetched_time, setting):
    event = {}
    event = data
    event["_exastro_event_collection_settings_name"] = setting["EVENT_COLLECTION_SETTINGS_NAME"]
    event["_exastro_event_collection_settings_id"] = setting["EVENT_COLLECTION_SETTINGS_ID"]
    event["_exastro_fetched_time"] = int(fetched_time.timestamp())
    event["_exastro_end_time"] = int((fetched_time + datetime.timedelta(seconds=setting["TTL"])).timestamp())

    return event


def getTopLevelObject_Event():
    """最上位がオブジェクトのイベント
    """
    return 	{
		    "endsAt": "2023-07-18T09:51:30.000Z",
		    "fingerprint": "eb977b43836c0ce9",
		    "startsAt": "2023-07-18T09:50:00.000Z",
		    "status": {
		      "inhibitedBy": [],
		      "silencedBy": [],
		      "state": "active"
		    },
		    "updatedAt": "2023-07-18T09:50:00.018Z",
		    "generatorURL": "http://localhost:3000/alerting/grafana/e554be49-ef18-4603-9c90-35cb8a7b8cf2/view",
		    "labels": {
		      "__alert_rule_uid__": "e554be49-ef18-4603-9c90-35cb8a7b8cf2",
		      "alertname": "fundamentals-test",
		      "grafana_folder": "fundamentals"
		    }
		  }

def getTopLevelList_Events():
    """最上位が配列のイベント
    """
    return  [
		  {
		    "endsAt": "2023-07-18T09:51:30.000Z",
		    "fingerprint": "eb977b43836c0ce9",
		    "startsAt": "2023-07-18T09:50:00.000Z",
		    "status": {
		      "inhibitedBy": [],
		      "silencedBy": [],
		      "state": "active"
		    },
		    "updatedAt": "2023-07-18T09:50:00.018Z",
		    "generatorURL": "http://localhost:3000/alerting/grafana/e554be49-ef18-4603-9c90-35cb8a7b8cf2/view",
		    "labels": {
		      "__alert_rule_uid__": "f554be49-ef18-4603-9c90-35cb8a7b8cf2",
		      "alertname": "fundamentals-test",
		      "grafana_folder": "fundamentals"
		    }
		  },
		  {
		    "endsAt": "2023-07-18T10:51:30.000Z",
		    "fingerprint": "eb977b43836c0ce9",
		    "startsAt": "2023-07-18T10:50:00.000Z",
		    "status": {
		      "inhibitedBy": [],
		      "silencedBy": [],
		      "state": "active"
		    },
		    "updatedAt": "2023-07-18T10:50:00.018Z",
		    "generatorURL": "http://localhost:3000/alerting/grafana/e554be49-ef18-4603-9c90-35cb8a7b8cf2/view",
		    "labels": {
		      "__alert_rule_uid__": "e554be49-ef18-4603-9c90-35cb8a7b8cf2",
		      "alertname": "fundamentals-test",
		      "grafana_folder": "fundamentals"
		    }
		  }
		]


def getTopLevelObject_ObjectEvent():
    """最上位がオブジェクトのオブジェクトイベント
    """
    return 	{
		    "endsAt": "2023-07-18T09:51:30.000Z",
		    "fingerprint": "eb977b43836c0ce9",
		    "startsAt": "2023-07-18T09:50:00.000Z",
		    "status": {
		      "inhibitedBy": [],
		      "silencedBy": [],
		      "state": "active"
		    },
		    "updatedAt": "2023-07-18T09:50:00.018Z",
        "data" : {
          "updatedAt": "2023-07-18T09:50:00.018Z",
          "generatorURL": "http://localhost:3000/alerting/grafana/e554be49-ef18-4603-9c90-35cb8a7b8cf2/view",
          "labels": {
            "__alert_rule_uid__": "e554be49-ef18-4603-9c90-35cb8a7b8cf2",
            "alertname": "fundamentals-test",
            "grafana_folder": "fundamentals"
          }
        }
		  }

def getTopLevelObject_ObjectEventList():
    """最上位がオブジェクトのイベントリスト
    """
    return  {
		    "endsAt": "2023-07-18T09:51:30.000Z",
		    "fingerprint": "eb977b43836c0ce9",
		    "startsAt": "2023-07-18T09:50:00.000Z",
		    "status": {
		      "inhibitedBy": [],
		      "silencedBy": [],
		      "state": "active"
		    },
        "data" : [
            {
              "updatedAt": "2023-07-18T09:50:00.018Z",
              "generatorURL": "http://localhost:3000/alerting/grafana/e554be49-ef18-4603-9c90-35cb8a7b8cf2/view",
              "labels": {
                "__alert_rule_uid__": "f554be49-ef18-4603-9c90-35cb8a7b8cf2",
                "alertname": "fundamentals-test",
                "grafana_folder": "fundamentals"
              }
            },
            {
              "updatedAt": "2023-07-18T10:50:00.018Z",
              "generatorURL": "http://localhost:3000/alerting/grafana/e554be49-ef18-4603-9c90-35cb8a7b8cf2/view",
              "labels": {
                "__alert_rule_uid__": "e554be49-ef18-4603-9c90-35cb8a7b8cf2",
                "alertname": "fundamentals-test",
                "grafana_folder": "fundamentals"
              }
            }
        ]
    }

if __name__ == '__main__':
    main()
