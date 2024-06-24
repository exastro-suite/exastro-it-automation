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
from jinja2 import Template
from dotenv import load_dotenv  # python-dotenv

# /exastro/
from common_libs.apply import apply
from common_libs.common.dbconnect import * # noqa: F403
from common_libs.common.logger import AppLog
from common_libs.common.message_class import MessageTemplate
from common_libs.common.mongoconnect.mongoconnect import MONGOConnectWs
from common_libs.conductor.classes.exec_util import *
from common_libs.conductor.classes.exec_util import * # noqa: F403
from common_libs.notification.sub_classes.oase import OASE, OASENotificationType
from common_libs.oase.const import oaseConst
from common_libs.oase.manage_events import ManageEvents
from common_libs.common.util import get_upload_file_path
from common_libs.notification.sub_classes.oase import OASE, OASENotificationType

# モジュール探査パス(PYTHONPATH)にita_root/ita_by_oase_conclusionを追加
sys.path.append('/workspace/ita_root/ita_by_oase_conclusion/')
from libs.notification_data import Notification_data # type: ignore
from libs.common_functions import addline_msg # type: ignore


class test_const:
    """通知データクラスのテスト用定数クラス
    """
    # オーガナイゼーションID
    #   「オーガナイゼーション一覧」画面の「オーガナイゼーションID」
    ORGANIZATION_ID = 'org001'
    # ワークスペースID
    #   「ワークスペース一覧」画面の「ワークスペース一ID」
    WORKSPACE_ID = "workspace_001"
    # イベント発生時刻
    # 1. VSCodeで、devcontainer-ita-mongodb_1に接続
    # 2. MongoDBへ接続
    #     環境y変数を参考して、下記のコマンドを投入
    #    $ mongosh mongodb://<MONGO_ADMIN_USER>:<MONGO_ADMIN_PASSWORD>@localhost:27017
    # 3. データベース一覧
    #    > show dbs
    #    ITA_WS_････  100.00 KiB　
    #       └ 各環境で、"ITA_WS_････"は異なる
    # 4, データベース切替
    #    > use ITA_WS_････
    #    switched to db ITA_WS_････
    # 5. コレクション(labeled_event_collection)に登録されているデータを表示
    #    > db.labeled_event_collection.find()
    #    [
    #      {
    #        _id: ObjectId("xxxx"),
    #        labels: {
    #          _exastro_fetched_time: 1716169459、←ここの値
    JUDGETIME = 1716169459
    # ルールID
    #   「OASE > ルール > ルール」画面の「ルールID」
    #   ・「事前通知・通知」と「事前通知・通知」に、テストで使用するテンプレートを登録
    RULE_ID = 'd124b677-568c-4066-8591-80dd2a9a9e8c'
    # アクションID
    #   「OASE > ルール > アクション」画面の（ルールIDに紐づく）「アクションID」
    ACTION_ID = '86240557-95af-4cbb-98fd-a819285fb6e1'
    # conductorクラスID
    #   「Conductor > Conductor一覧]画面の「ConductorクラスID」
    CONDUCTOR_CLASS_ID = '23710c61-cd98-4164-bc4e-b7ed507a578a'
    # conductorインスタンスID
    #   「Conductor > Conductor一覧]画面で、Conductorを選択し、【詳細】
    #   「Conductor > Conductor編集/作業実行」画面で、【作業実行】
    #   「Conductor > Conductor作業一覧]画面の「ConductorインスタンスID」
    CONDUCTOR_INSTANCE_ID = '5474cf36-fc00-458b-9efe-96f07d7caa97'
    # ログレベル(ERROR|INFO|DEBUG)
    LOG_LEVEL = 'INFO'
    # ログ出力言語('ja':日本語  'en':English)
    LANGUAGE = 'ja'
    # 通知テンプレートのテストを(True：成功時みみする False:全てする)
    IsTestTemplateOnlySuccessful = False
    # 通知データをターミナルに出力(True:出力する False：出力しない)
    IsNotificationDataPrinting = False

def main():
    """「通知データクラス」の単体テスト・モジュール
        ・事前通知・事後通知用のモック・データを作成し
          「通知データクラス」に、モック・データを引数で指定し
          「事前通知」、「事後通知」のテストを行う。
        ・「通知データクラス」で、不具合があれば、Exceptionで停止する。
        ・「通知データクラス」が正常に動作した場合、通知データがターミナルに出力する。
          （※test_const.IsNotificationDataPrintingで制御している）
          ターミナルの通知データが、正しく作成されているか検証をが必要。
        ・また、作成された「通知データ」を「ルール」画面の「事前通知・通知」
          「事後通知・通知」のテンプレートに適用し、通知するメッセージまを出力し、
          テンプレートが正しく適用されているかのテストも行う。
          （※test_const.IsTestTemplateOnlySuccessfulで制御している）

        ▼テストケース
            ・ 事前#1 正常系
            ・ 事前#2 異常系・引数が空（評価結果/ルール/アクションがない）
            ・ 事前#3 異常系・引数がNone（評価結果/ルール/アクションがない）
            ・ 事前#4 キーがNone（T_FILTER/T_OPERATION/T_CONDUCTOR_CLASSが取得できない）
            ・ 事前#5 キーが存在しない値（T_FILTER/T_OPERATION/T_CONDUCTOR_CLASSが取得できない）

            ・事後#1 正常系
            ・事後#2 異常系・引数が空（評価結果が無い場合）
            ・事後#3 異常系・引数がNone（評価結果が無い場合）
            ・事後#4 異常系・EVENT_ID_LISTが存在しない値（イベントが取得できな場合）
            ・事後#5 異常系・キーがNone（T_RULE/T_ACTIOM/T_COMN_CONDUCTOR_INSTANCEが取得できない）
            ・事後#6 異常系・キーがが存在しない値（T_RULE/T_ACTIOM/T_COMN_CONDUCTOR_INSTANCEが取得できない）

            ・異常系#1 日付書式変換で、日付がNone
            ・異常系#2 日付書式変換で、日付が不正な値
            ・異常系#3 区分値名称変換で、区分値がNone
            ・異常系#4 区分値名称変換で、区分値が不正な値
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

            # connect MongoDB
            wsMongo = MONGOConnectWs()
            # connect MariaDB
            wsDb = DBConnectWs(test_const.WORKSPACE_ID)  # noqa: F405
            # イベント操作クラス
            judgetime = int(test_const.JUDGETIME)
            EventObj = ManageEvents(wsMongo, judgetime)

            # 通知データクラス生成【テスト対象】
            notification_data = Notification_data(wsDb, EventObj)

            # 事前用セットアップ
            (UseEventIdList, action_log_row, ruleInfo, ret_action) = setupBefore(wsDb, wsMongo, judgetime)

            # 事前通知
            notification_type = OASENotificationType.BEFORE_ACTION

            test_case = 1
            print("----- 事前#%02d 正常系 -----" % test_case)
            print("  ・期待値")
            print("    ・全ての項目が、MpngoDBや各画面通りに表示")
            before_Action_Event_List = notification_data.getBeforeActionEventList(UseEventIdList, action_log_row, ruleInfo, ret_action)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(before_Action_Event_List)
            NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, before_Action_Event_List)

            test_case += 1
            print("----- #%02d 事前・異常系・引数空 -----" % test_case)
            print("  ・[使用イベントIDリスト] = []")
            print("  ・[評価結果] = {}}")
            print("  ・[ルール] = {}")
            print("  ・[アクション]  {}")
            print("  ・期待値")
            print("    ・全ての項目が空")
            before_Action_Event_List = notification_data.getBeforeActionEventList([], {}, {}, {})
            if test_const.IsNotificationDataPrinting:
                printActionEventist(before_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, before_Action_Event_List)

            test_case += 1
            print("----- #%02d 事前・異常系・引数はNone -----" % test_case)
            print("  ・[使用イベントIDリスト] = None")
            print("  ・[評価結果] = None")
            print("  ・[ルール] = None")
            print("  ・[アクション]  None")
            print("  ・期待値")
            print("    ・全ての項目が空")
            before_Action_Event_List = notification_data.getBeforeActionEventList(None, None, None, None)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(before_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, before_Action_Event_List)

            test_case += 1
            print("----- #%02d 事前・異常系・キーがNone -----" % test_case)
            print("  ・[ルール]FILTER_A = None")
            print("  ・[ルール]FILTER_B = None")
            print("  ・[アクション]OPERATION_ID = None")
            print("  ・[アクション]CONDUCTOR_CLASS_ID = None")
            print("  ・期待値")
            print("    ・[ルール情報]フィルターA、Bが空")
            print("    ・[アクション情報]オペレーション名が空")
            print("    ・[アクション情報]実行するConductor名が空")
            ruleInfo['FILTER_A'] = None
            ruleInfo['FILTER_B'] = None
            ret_action['OPERATION_ID'] = None
            ret_action['CONDUCTOR_CLASS_ID'] = None
            before_Action_Event_List = notification_data.getBeforeActionEventList(UseEventIdList, action_log_row, ruleInfo, ret_action)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(before_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, before_Action_Event_List)

            test_case += 1
            print("----- #%02d 事前・異常系・キーが存在しない値 -----" % test_case)
            print("  ・[使用イベントIDリスト]  = ['xxx','yyyy']")
            print("  ・[ルール]FILTER_A = 'xxx'")
            print("  ・[ルール]FILTER_B = 'xxx'")
            print("  ・[アクション]OPERATION_ID = 'xxx'")
            print("  ・[アクション]CONDUCTOR_CLASS_ID = 'xxx'")
            print("  ・期待値")
            print("    ・[イベント]が空")
            print("    ・[ルール情報]フィルターA、Bのィルター名、ィルター条件 が空")
            print("    ・[アクション情報]オペレーション名が空")
            print("    ・[アクション情報]実行するConductor名が空")
            ruleInfo['FILTER_A'] = 'xxx'
            ruleInfo['FILTER_B'] = 'xxx'
            ret_action['OPERATION_ID'] = 'xxx'
            ret_action['CONDUCTOR_CLASS_ID'] = 'xxx'
            before_Action_Event_List = notification_data.getBeforeActionEventList(['xxx','yyyy'], action_log_row, ruleInfo, ret_action)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(before_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, before_Action_Event_List)

            # 事後
            notification_type = OASENotificationType.AFTER_ACTION

            # 事後用セットアップ
            action_log_row = setupActionlogEntiry(UseEventIdList, test_const.CONDUCTOR_INSTANCE_ID)

            test_case += 1
            print("----- #%02d 事後・正常系 -----" % test_case)
            print("  ・期待値")
            print("    ・全ての項目が、MpngoDBや各画面通りに表示")
            after_Action_Event_List = notification_data.getAfterActionEventList(action_log_row)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(after_Action_Event_List)
            NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, after_Action_Event_List)

            test_case += 1
            print("----- #%02d 事後・異常系・引数が空 -----" % test_case)
            print("  ・[評価結果] = {}")
            print("  ・期待値")
            print("    ・全ての項目が空")
            after_Action_Event_List = notification_data.getAfterActionEventList({})
            if test_const.IsNotificationDataPrinting:
                printActionEventist(after_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, after_Action_Event_List)

            test_case += 1
            print("----- #%02d 事後・異常系・引数がNone -----" % test_case)
            print("  ・[評価結果] = None")
            print("  ・期待値")
            print("    ・全ての項目が空")
            after_Action_Event_List = notification_data.getAfterActionEventList(None)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(after_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, after_Action_Event_List)

            test_case += 1
            print("----- #%02d 事後・異常系・EVENT_ID_LISTが不正な値 -----" % test_case)
            print("  ・[評価結果]EVENT_ID_LIST = ObjectId('xxxx'), ObjectId('yyyy')")
            print("  ・期待値")
            print("    ・[イベント]が空")
            action_log_row['EVENT_ID_LIST'] = "ObjectId('xxxx'), ObjectId('yyyy')"
            after_Action_Event_List = notification_data.getAfterActionEventList(action_log_row)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(after_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, after_Action_Event_List)

            test_case += 1
            print("----- #%02d 事後・異常系・キーがNone -----" % test_case)
            print("  ・[評価結果]EVENT_ID_LIST = None")
            print("  ・[評価結果]RULE_ID = None")
            print("  ・[評価結果]ACTION_ID = None")
            print("  ・[評価結果]CONDUCTOR_INSTANCE_ID = None")
            print("  ・期待値")
            print("    ・[イベント]が、空")
            print("    ・[マッチした結果]実行したConductorIDが、空")
            print("    ・[ルール情報]が、空")
            print("    ・[アクション情報]が、空")
            print("    ・[Conductor情報]が、空")
            action_log_row['EVENT_ID_LIST'] = None
            action_log_row['RULE_ID'] = None
            action_log_row['ACTION_ID'] = None
            action_log_row['CONDUCTOR_INSTANCE_ID'] = None
            after_Action_Event_List = notification_data.getAfterActionEventList(action_log_row)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(after_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, after_Action_Event_List)

            test_case += 1
            print("----- #%02d 事後・異常系・キーがが存在しない値 -----" % test_case)
            print("  ・[評価結果]EVENT_ID_LIST = '存在する値,存在しない値'")
            print("  ・[評価結果]RULE_ID = xxxx")
            print("  ・[評価結果]ACTION_ID = xxxx")
            print("  ・[評価結果]CONDUCTOR_INSTANCE_ID = xxxx")
            print("  ・期待値")
            print("    ・[イベント]で、存在しない値のイベントは出力されない")
            print("    ・[ルール情報]が、空")
            print("    ・[アクション情報]が、空")
            print("    ・[Conductor情報]が、空")
            action_log_row['EVENT_ID_LIST'] = ','.join(map(repr, UseEventIdList)) + ',' + "ObjectId('777777777777777777777777')"
            action_log_row['RULE_ID'] = 'xxxx'
            action_log_row['ACTION_ID'] = 'xxxx'
            action_log_row['CONDUCTOR_INSTANCE_ID'] = 'xxxx'
            after_Action_Event_List = notification_data.getAfterActionEventList(action_log_row)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(after_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, after_Action_Event_List)

            test_case += 1
            print("----- #%02d 異常系・日付書式変換で、日付がNone -----" % test_case)
            print("  ・[評価結果]TIME_REGISTER = None")
            print("  ・期待値")
            print("    ・[マッチした結果]登録日時が、空")
            action_log_row = setupActionlogEntiry(UseEventIdList, test_const.CONDUCTOR_INSTANCE_ID)
            action_log_row['TIME_REGISTER'] = None
            after_Action_Event_List = notification_data.getAfterActionEventList(action_log_row)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(after_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, after_Action_Event_List)

            test_case += 1
            print("----- #%02d 異常系・日付書式変換で、日付が不正な値 -----" % test_case)
            print("  ・[評価結果]TIME_REGISTER = -99999999.99")
            print("  ・期待値")
            print("    ・[マッチした結果]登録日時が、不正な値(-99999999.99)")
            action_log_row = setupActionlogEntiry(UseEventIdList, test_const.CONDUCTOR_INSTANCE_ID)
            action_log_row['TIME_REGISTER'] = -99999999.99
            after_Action_Event_List = notification_data.getAfterActionEventList(action_log_row)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(after_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, after_Action_Event_List)

            test_case += 1
            print("----- #%02d 異常系・区分値名称変換で、区分値がNone -----" % test_case)
            print("  ・[評価結果]STATUS_ID = None")
            print("  ・期待値")
            print("    ・[マッチした結果]ステータスが、空")
            action_log_row = setupActionlogEntiry(UseEventIdList, test_const.CONDUCTOR_INSTANCE_ID)
            action_log_row['STATUS_ID'] = None
            after_Action_Event_List = notification_data.getAfterActionEventList(action_log_row)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(after_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, after_Action_Event_List)

            test_case += 1
            print("----- #%02d 異常系・区分値名称変換で、区分値が不正な値 -----" % test_case)
            print("  ・[評価結果]STATUS_ID = 'xxx'")
            print("  ・期待値")
            print("    ・[マッチした結果]ステータスが、空")
            action_log_row['STATUS_ID'] = 'xxx'
            after_Action_Event_List = notification_data.getAfterActionEventList(action_log_row)
            if test_const.IsNotificationDataPrinting:
                printActionEventist(after_Action_Event_List)
            if not test_const.IsTestTemplateOnlySuccessful:
                NotificationMessaget.printNotification(wsDb, test_const.RULE_ID, notification_type, after_Action_Event_List)

            print("OOOOO テスト【正常】終了 OOOOO")
            print("      期待値通りか要確認")

        except Exception as e:
            t = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
            print("xxxxx テスト【エラー】終了 xxxxx")
        finally:
            if wsDb is None:
                wsDb.db_transaction_end(False)


def setupBefore(wsDb, wsMongo, judgetime):
    """_summary_

    Args:
        wsDb (DBConnectWs): データベースコネクション
        wsMongo (MONGOConnectWs): MongoDBコネクション
        judgetime (datetime): イベント発生時刻

    Returns:
        List: セットアップ・イベントIDリスト
        Dict: 評価結果(action_log)モック
        Dict: ルール(rule)モック
        Dict: アクション(action)モック
    """

        # セットアップ・イベントIDリスト取得
    UseEventIdList = setupUseEventIdList(wsMongo, judgetime)
    # セットアップ・評価結果(action_log)モック作成
    action_log_row = setupActionlogEntiry(UseEventIdList, test_const.CONDUCTOR_CLASS_ID)
    # セットアップ・ルール(rule)モック作成
    ruleInfo = setupRuleEntiry(wsDb, test_const.RULE_ID)
    # セットアップ・アクション(action)モック作成
    ret_action = setupActionEntiry(wsDb, test_const.ACTION_ID)

    return UseEventIdList, action_log_row, ruleInfo, ret_action

def setupUseEventIdList(wsMongo, judgetime):
    """イベントIDリスト取得

    Args:
        wsMongo (any): MongoDBコネクション
        judgetime (int): 取得日時

    Returns:
        List: イベントIDリスト
    """
    EventObjEx = ManageEventsEx(wsMongo, judgetime)
    useEventIdList = EventObjEx.get_events_id()
    return useEventIdList


def setupActionlogEntiry(UseEventIdList, conductor_instance_id):
    """評価結果(action_log)モック作成

    Args:
        UseEventIdList (List): イベントIDリスト

    Returns:
        Dict: 評価結果(action_log)モック
    """
    return {
        "RULE_ID": test_const.RULE_ID,
        "RULE_NAME": 'Platform_rule',
        "STATUS_ID": oaseConst.OSTS_Rule_Match, # 1:判定済み
        "ACTION_ID": test_const.ACTION_ID,
        "ACTION_NAME": 'action_001',
        "CONDUCTOR_INSTANCE_ID": conductor_instance_id,
        "CONDUCTOR_INSTANCE_NAME": 'conductor_01',
        "OPERATION_ID": 'operation_id',
        "OPERATION_NAME": 'operation_name',
        "EVENT_COLLABORATION": 'event_collaboration',
        "HOST_ID": 'host_id',
        "HOST_NAME": 'host_name',
        "PARAMETER_SHEET_ID": 'parameter_sheet_id',
        "PARAMETER_SHEET_NAME": 'parameter_sheet_name',
        "PARAMETER_SHEET_NAME_REST": 'parameter_sheet_name_rest',
        "EVENT_ID_LIST": ','.join(map(repr, UseEventIdList)),
        "ACTION_LABEL_INHERITANCE_FLAG": '1',
        "EVENT_LABEL_INHERITANCE_FLAG": '1',
        "ACTION_PARAMETERS": 'action_parameters',
        "CONCLUSION_EVENT_LABELS": 'conclusion_event_lables',
        "TIME_REGISTER": 1716169459,
        "NOTE": None,
        "DISUSE_FLAG": "0",
        "LAST_UPDATE_USER": g.get('USER_ID')
    }

def setupRuleEntiry(wsDb, rule_id):
    """ルール(rule)モック作成

    Args:
        wsDb (any): データベース
        rule_id (string): ルールID

    Returns:
        _type_: ルール(rule)モック
    """
    # RULE_ID :
    rule = {}

    _ruleList = wsDb.table_select(oaseConst.T_OASE_RULE, 'WHERE DISUSE_FLAG = %s AND RULE_ID = %s ', [0, rule_id])
    if not _ruleList:
        tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_RULE])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    else:
        rule = _ruleList[0]

    return rule

def setupActionEntiry(wsDb, action_id):
    """アクション(action)モック作成

    Args:
        wsDb (any): データベース
        action_id (string): アクションID

    Returns:
        Dict: アクション(action)モック
    """
    # ACTION_ID :
    action = {}

    _actionList = wsDb.table_select(oaseConst.T_OASE_ACTION, 'WHERE DISUSE_FLAG = %s AND ACTION_ID = %s ', [0, action_id])
    if not _actionList:
        tmp_msg = g.appmsg.get_log_message("BKY-90009", [oaseConst.T_OASE_ACTION])
        g.applogger.debug(addline_msg('{}'.format(tmp_msg)))  # noqa: F405
    else:
        action = _actionList[0]

    return action

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


def printActionEventist(actionEventList):
    """アクションイベントをprint出力する
       アクションイベント中のObjectID('xxxx')を
       文字列変換しないとJSON形式変換できない

    Args:
        actionEventList (List): アクション・イベント・リスト
    """
    _actionEventList =  copy.deepcopy(actionEventList)
    for _event in _actionEventList[0]['events']:
        if '_exastro_events' in _event:
            if '_id' in _event['_exastro_events']:
                _event['_exastro_events']['_id'] = str(_event['_exastro_events']['_id'])

    print(json.dumps(_actionEventList, indent=2))


class ManageEventsEx(ManageEvents):
    """拡張エベント管理クラス
        継承関係
        ManageEvents (ita_root/common_libs/oase/manage_events.py)
            └ ManageEventsEx (本ファイル)
    """
    def get_events_id(self):
        """イベントID取得

        Returns:
            List: イベントIDリスト
        """
        keys = []
        for key in self.labeled_events_dict:
            keys.append(key)
        return keys

class NotificationMessaget(OASE):
    """通知メッセージ。クラス
        継承関係
        Notification (ita_root/common_libs/notification/notification_base.py)
            └ OASE (ita_root/common_libs/notification/sub_classes/oase.py)
                └ NotificationMessaget (test/ita_by_oase_conclusion/test_notification_data.py)
    """

    @classmethod
    def printNotification(cls, wsDb: DBConnectWs, rule_id: string, notification_type: int, event_list: list):
        """通知をprint

        Args:
            wsDb (DBConnectWs): データベースコネクション
            rule_id (string): ルールID
            event_list (list): 通知データ
            isBefore (bool): 事前フラグ(事前:true 事後:false)

        Returns:
            _type_: _description_
        """

        # 通知情報を作成
        decision_information = {"notification_type": notification_type, "rule_id": rule_id}

        # 通知ルール取得
        fetch_data = cls._fetch_table(wsDb, decision_information)
        if fetch_data is None:
            return

        # テンプレート取得
        template = cls._get_template(fetch_data, decision_information)
        if template is None:
            return

        # 通知メッセージ作成
        print("  ▼通知メッセージ")
        print("")
        for index, item in enumerate(event_list):
            tmp_item = copy.deepcopy(item)
            result = cls._create_notise_message(tmp_item, template)
            print(result['message'])

        print("")
        return

if __name__ == '__main__':
    main()
