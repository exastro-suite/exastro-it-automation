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
import os
import inspect
import json
import time
import pathlib
import shutil
import ast
import traceback
from flask import g

from common_libs.common import *  # noqa: F403
from common_libs.common.dbconnect import DBConnectWs
from common_libs.common import menu_excel
from common_libs.common import storage_access
from common_libs.common.util import get_iso_datetime, arrange_stacktrace_format, print_exception_msg
import util


def backyard_main(organization_id, workspace_id):
    """
        Excelエクスポート機能backyardメイン処理
        ARGS:
            organization_id: Organization ID
            workspace_id: Workspace ID
        RETRUN:

    """

    EXPORT_PATH = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/tmp/bulk_excel/export"
    IMPORT_PATH = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/tmp/bulk_excel/import"
    DST_PATH = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/uploadfiles/60106/file_name"
    RESULT_PATH = os.environ.get('STORAGEPATH') + "/".join([organization_id, workspace_id]) + "/uploadfiles/60106/result_file"

    STATUS_RUNNING = "2"
    STATUS_PROCESSED = "3"
    STATUS_FAILURE = "4"

    # メイン処理開始
    debug_msg = g.appmsg.get_log_message("BKY-20001", [])
    g.applogger.debug(debug_msg)

    try:
        # DB接続
        objdbca = DBConnectWs(workspace_id)  # noqa: F405

        # インポート実行用のアップロードID
        upload_id = ""

        # メンテナンスモードのチェック
        try:
            maintenance_mode = get_maintenance_mode_setting()
            # data_update_stopの値が"1"の場合、メンテナンス中のためreturnする。
            if str(maintenance_mode['data_update_stop']) == "1":
                g.applogger.debug(g.appmsg.get_log_message("BKY-00005", []))
                return

            # backyard_execute_stopの値が"1"の場合、メンテナンス中のためreturnする。
            if str(maintenance_mode['backyard_execute_stop']) == "1":
                g.applogger.debug(g.appmsg.get_log_message("BKY-00006", []))
                return
        except Exception:
            # スタックトレース出力
            t = traceback.format_exc()
            g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))
            # エラーログ出力
            g.applogger.error(g.appmsg.get_log_message("BKY-00008", []))
            return

        # 未実行のレコードを取得する
        ret = objdbca.table_select("T_BULK_EXCEL_EXPORT_IMPORT", 'WHERE STATUS = %s AND DISUSE_FLAG = %s', [1, 0])

        # 0件なら処理を終了
        if not ret:
            debug_msg = g.appmsg.get_log_message("BKY-20003", [])
            g.applogger.debug(debug_msg)

            debug_msg = g.appmsg.get_log_message("BKY-20002", [])
            g.applogger.debug(debug_msg)
            return

        for task in ret:

            # 言語情報
            lang = task['LANGUAGE']
            g.LANGUAGE = lang

            g.appmsg.set_lang(lang)

            # 実行ユーザー
            g.USER_ID = '60102'

            result, msg = util.setStatus(task['EXECUTION_NO'], STATUS_RUNNING, objdbca, True)
            if result is False:
                # エラーログ出力
                frame = inspect.currentframe().f_back
                msgstr = g.appmsg.get_api_message("MSG-30023", ["T_BULK_EXCEL_EXPORT_IMPORT", os.path.basename(__file__), str(frame.f_lineno)])
                g.applogger.info(msgstr)
                # ステータスを完了(異常)に更新
                result, msg = util.setStatus(task['EXECUTION_NO'], STATUS_FAILURE, objdbca)
                continue

            # エクスポート
            if task["EXECUTION_TYPE"] == "1":
                taskId = task["EXECUTION_NO"]

                # タスクIDでディレクトリづくり
                if not os.path.isdir(EXPORT_PATH + "/" + taskId + "/tmp_zip"):
                    os.makedirs(EXPORT_PATH + "/" + taskId + "/tmp_zip")
                    os.chmod(EXPORT_PATH + "/" + taskId + "/tmp_zip", 0o777)
                if not os.path.isdir(EXPORT_PATH + "/" + taskId):
                    frame = inspect.currentframe().f_back
                    msgstr = g.appmsg.get_api_message("MSG-30023", ["T_BULK_EXCEL_EXPORT_IMPORT", os.path.basename(__file__), str(frame.f_lineno)])
                    g.applogger.error(msgstr)
                    # ステータスを完了(異常)に更新
                    result, msg = util.setStatus(task['EXECUTION_NO'], STATUS_FAILURE, objdbca)
                    # 一時ディレクトリ削除
                    shutil.rmtree(EXPORT_PATH + "/" + taskId)
                    continue

                fileNameList = ""

                request = {}

                json_storage_item = json.loads(str(task['JSON_STORAGE_ITEM']))
                menu_list = json_storage_item["menu"]
                for menu in menu_list:
                    sql = " SELECT MENU_ID, MENU_NAME_REST FROM T_COMN_MENU WHERE DISUSE_FLAG <> 1 AND MENU_NAME_REST = %s "
                    data_list = objdbca.sql_execute(sql, [menu])
                    for data in data_list:
                        menuId = data['MENU_ID']
                        menuNameRest = data['MENU_NAME_REST']
                    # ファイル名が重複しないためにsleep
                    time.sleep(1)
                    menuInfo = util.getMenuInfoByMenuId(menuNameRest, objdbca)

                    # メニュー周りの情報
                    menuGroupId = menuInfo["MENU_GROUP_ID"]
                    if lang == 'ja':
                        menuGroupName = menuInfo["MENU_GROUP_NAME_JA"]
                    else:
                        menuGroupName = menuInfo["MENU_GROUP_NAME_EN"]

                    # メニューの存在確認
                    menu_record = util.check_menu_info(menuNameRest, objdbca)

                    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
                    sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
                    menu_table_link_record = util.check_sheet_type(menuNameRest, sheet_type_list, objdbca)

                    filter_parameter = {}
                    # 廃止情報
                    if task["ABOLISHED_TYPE"] == "2":
                        # 廃止情報の取得 廃止情報を除く
                        filter_parameter = {"discard": {"NORMAL": "0"}}
                    elif task["ABOLISHED_TYPE"] == "3":
                        # 廃止情報の取得 廃止情報のみ
                        filter_parameter = {"discard": {"NORMAL": "1"}}

                    # ダミー情報設定
                    g.USER_ID = task["EXECUTION_USER"]
                    g.ROLES = "dummy"
                    filePath = menu_excel.collect_excel_filter(objdbca, organization_id, workspace_id, menuNameRest, menu_record, menu_table_link_record, filter_parameter, True, lang)
                    g.USER_ID = '60102'

                    # メニューグループごとにまとめる
                    # スペース、バックスラッシュがあるとzip解凍に失敗するので「_」に変換
                    folder_name = menuGroupId + "_" + menuGroupName.replace("/", "_")
                    if not os.path.exists(EXPORT_PATH + "/" + taskId + "/tmp_zip/" + folder_name):
                        os.makedirs(EXPORT_PATH + "/" + taskId + "/tmp_zip/" + folder_name)
                        os.chmod(EXPORT_PATH + "/" + taskId + "/tmp_zip/" + folder_name, 0o777)

                    shutil.move(filePath, EXPORT_PATH + "/" + taskId + "/tmp_zip/" + folder_name)

                    # ファイルリスト
                    fileNamelist = filePath.split("/")
                    fileName = ""
                    for value in fileNamelist:
                        if "xlsx" in value:
                            fileName = value

                    if menuGroupId in request:
                        request[menuGroupId] = {"menu_group_name": menuGroupName, "menu": []}
                        request[menuGroupId]["menu"] = {}
                        request[menuGroupId]["menu"][""] = {"menu_id": menuId, "menu_name": menuNameRest}
                    else:
                        request[menuGroupId] = {}
                        request[menuGroupId]["menu"] = {}
                        request[menuGroupId]["menu"][""] = {"menu_id": menuId, "menu_name": menuNameRest}

                    fileNameList += "#" + menuGroupName + "\n" + menuNameRest + ":" + fileName + "\n"

                # ファイル一覧をJSONに変換
                tmpExportPath = EXPORT_PATH + "/" + taskId + "/tmp_zip"

                # MENU_LIST作成
                file_write = storage_access.storage_write()
                file_write.open(tmpExportPath + "/MENU_LIST.txt", mode="w")
                file_write.write(fileNameList)
                file_write.close()

                # パスの有無を確認
                if not os.path.exists(DST_PATH):
                    os.makedirs(DST_PATH)
                    os.chmod(DST_PATH, 0o777)
                else:
                    os.chmod(DST_PATH, 0o777)

                # ZIPを固めて、ステータスを完了にする
                t_delta = datetime.timedelta(hours=9)
                JST = datetime.timezone(t_delta, 'JST')
                now = datetime.datetime.now(JST)
                now_date = now.date().strftime('%Y%m%d')
                now_time = now.time().strftime('%X')
                now_time = now_time.replace(":", "")
                dstFileName = "ITA_FILES_" + now_date + now_time + ".zip"
                res = util.zip(task['EXECUTION_NO'], EXPORT_PATH + "/" + taskId, STATUS_PROCESSED, dstFileName, objdbca)
                if res == 0:
                    frame = inspect.currentframe().f_back
                    msgstr = g.appmsg.get_api_message("MSG-30023", ["T_BULK_EXCEL_EXPORT_IMPORT", os.path.basename(__file__), str(frame.f_lineno)])
                    g.applogger.info(msgstr)
                    # ステータスを完了(異常)に更新
                    result, msg = util.setStatus(task['EXECUTION_NO'], STATUS_FAILURE, objdbca)
                    # 一時ディレクトリ削除
                    shutil.rmtree(EXPORT_PATH + "/" + taskId)
                    continue

                # 一時ディレクトリ削除
                shutil.rmtree(EXPORT_PATH + "/" + taskId)

            # インポート
            elif task["EXECUTION_TYPE"] == "2":
                taskId = task["EXECUTION_NO"]
                json_storage_item = json.loads(str(task['JSON_STORAGE_ITEM']))
                upload_id = json_storage_item["upload_id"]
                import_menu_list = []
                menu = json_storage_item["menu"]
                for menu_id_list in menu.values():
                    for menu_id in menu_id_list:
                        import_menu_list.append(menu_id)

                targetImportPath = IMPORT_PATH + "/import/" + upload_id

                # tmp配下で読み取り
                file_read = storage_access.storage_read()
                file_read.open(targetImportPath + "/MENU_LIST.txt")
                tmpMenuIdFileAry = file_read.read().split("\n")
                file_read.close()

                menuIdFileInfo = []
                retImportAry = {}
                for value in tmpMenuIdFileAry:
                    # 頭に#がついているものはコメントなのではじく
                    result = re.match('^#', value)
                    if not result:
                        if not value == "":
                            menuIdFileInfo = value.split(":")
                            if len(menuIdFileInfo) == 2:
                                menuNameRest = menuIdFileInfo[0]
                                menuFileName = menuIdFileInfo[1]
                                retImportAry[menuNameRest] = menuFileName

                for menuNameRest, fileName in retImportAry.items():
                    menuInfo = util.getMenuInfoByMenuId(menuNameRest, objdbca)
                    menuId = menuInfo["MENU_ID"]
                    # メニューが画面でチェックされているか確認
                    if menuId not in import_menu_list:
                        continue
                    chk_path1 = IMPORT_PATH + "/import/" + upload_id + "/" + menuInfo["MENU_GROUP_ID"] + "_" + menuInfo["MENU_GROUP_NAME_JA"].replace("/", "_") + "/" + fileName
                    chk_path2 = IMPORT_PATH + "/import/" + upload_id + "/" + menuInfo["MENU_GROUP_ID"] + "_" + menuInfo["MENU_GROUP_NAME_EN"].replace("/", "_") + "/" + fileName
                    if not os.path.exists(chk_path1) and not os.path.exists(chk_path2) or fileName == "":
                        # ファイルがないエラー
                        resFilePath = RESULT_PATH + "/ResultData_" + taskId + ".log"
                        title = menuInfo["MENU_GROUP_ID"] + "_" + menuInfo["MENU_GROUP_NAME_" + lang.upper()] + ":" + menuId + "_" + menuInfo["MENU_NAME_" + lang.upper()]
                        msg = title + "\n" + g.appmsg.get_api_message("MSG-30026") + "\n"

                        util.dumpResultMsg(msg, taskId, RESULT_PATH)
                        continue

                    if os.path.exists(chk_path1):
                        targetImportPath = chk_path1
                    elif os.path.exists(chk_path2):
                        targetImportPath = chk_path2

                    excel_data = targetImportPath

                    # メニューの存在確認
                    menu_record = util.check_menu_info(menuNameRest, objdbca)

                    # 『メニュー-テーブル紐付管理』の取得とシートタイプのチェック
                    sheet_type_list = ['0', '1', '2', '3', '4', '5', '6']
                    menu_table_link_record = util.check_sheet_type(menuNameRest, sheet_type_list, objdbca)

                    # アップロード
                    g.ROLES = "dummy"
                    g.USER_ID = task["EXECUTION_USER"]
                    aryRetBody = menu_excel.execute_excel_maintenance(objdbca, organization_id, workspace_id, menuNameRest, menu_record, excel_data, True, lang)
                    g.USER_ID = "60102"

                    # リザルトファイルの作成
                    menuInfo = util.getMenuInfoByMenuId(menuNameRest, objdbca)
                    msg = menuInfo["MENU_GROUP_ID"] + "_" + menuInfo["MENU_GROUP_NAME_" + lang.upper()] + ":" + menuId + "_" + menuInfo["MENU_NAME_" + lang.upper()] + "\n"

                    strErrCountExplainTail = g.appmsg.get_api_message("MSG-30027")
                    msg += g.appmsg.get_api_message("MSG-30028", [fileName])
                    msg += "\n"
                    idx = 0
                    file_err_msg = ""
                    msg_result = []
                    msg_result.append(g.appmsg.get_api_message('MSG-30004'))
                    msg_result.append(g.appmsg.get_api_message('MSG-30005'))
                    msg_result.append(g.appmsg.get_api_message('MSG-30007'))
                    msg_result.append(g.appmsg.get_api_message('MSG-30006'))
                    msg_result.append(g.appmsg.get_api_message('MSG-30034'))
                    if "登録" not in aryRetBody and "Register" not in aryRetBody:
                        if type(aryRetBody) is str and aryRetBody == "499-00402":
                            # 編集用エクセルファイルでないファイルをインポートしたときのエラー
                            file_err_msg = g.appmsg.get_api_message("499-00402")
                            aryRetBody = {}
                        else:
                            # バリデーションエラー時はエラー内容しか返ってこないので、各処理を0件で登録
                            tmp_result = aryRetBody
                            aryRetBody = {msg_result[0]: 0, msg_result[1]: 0, msg_result[2]: 0, msg_result[3]: 0, msg_result[4]: len(aryRetBody)}
                    else:
                        aryRetBody[msg_result[4]] = 0

                    if len(aryRetBody) > 0:
                        for name, ct in aryRetBody.items():
                            if not isinstance(ct, int) or name == "IdList":
                                continue
                            msg += msg_result[idx] + ":    " + str(ct) + strErrCountExplainTail + "\n"
                            idx += 1

                        if aryRetBody[msg_result[4]] != 0:
                            for value in tmp_result.values():
                                for key, err_msg in value.items():
                                    msg += str(key) + ": " + str(err_msg) + "\n"
                    else:
                        msg += "\n"
                        msg += file_err_msg

                    msg += "\n"

                    util.dumpResultMsg(msg, taskId, RESULT_PATH)

                    # 結果ファイルの登録
                    res = util.registerResultFile(taskId, objdbca)

                    if res == 0:
                        frame = inspect.currentframe().f_back
                        msgstr = g.appmsg.get_api_message("MSG-30023", ["T_BULK_EXCEL_EXPORT_IMPORT", os.path.basename(__file__), str(frame.f_lineno)])
                        g.applogger.info(msgstr)
                        # ステータスを完了(異常)に更新
                        result, msg = util.setStatus(task['EXECUTION_NO'], STATUS_FAILURE, objdbca)
                        continue

                # ステータスを完了にする
                res = util.setStatus(task['EXECUTION_NO'], STATUS_PROCESSED, objdbca)
                if res == 0:
                    frame = inspect.currentframe().f_back
                    msgstr = g.appmsg.get_api_message("MSG-30023", ["T_BULK_EXCEL_EXPORT_IMPORT", os.path.basename(__file__), str(frame.f_lineno)])
                    g.applogger.info(msgstr)
                    # ステータスを完了(異常)に更新
                    result, msg = util.setStatus(task['EXECUTION_NO'], STATUS_FAILURE, objdbca)
                    continue

                # 一時ディレクトリ削除
                # アップロード後インポート実行しない場合、一時ディレクトリが残るのでimportディレクトリを削除してから、もう一度ディレクトリを作り直す
                shutil.rmtree(IMPORT_PATH + "/import")
                os.makedirs(IMPORT_PATH + "/import")
                os.chmod(IMPORT_PATH + "/import", 0o777)

    except Exception as e:
        # エラーログ出力
        t = traceback.format_exc()
        g.applogger.info("[timestamp={}] {}".format(str(get_iso_datetime()), arrange_stacktrace_format(t)))

        # 一時ディレクトリ削除
        if os.path.exists(EXPORT_PATH + "/" + taskId):
            shutil.rmtree(EXPORT_PATH + "/" + taskId)
        if os.path.exists(IMPORT_PATH + "/import/" + upload_id):
            shutil.rmtree(IMPORT_PATH + "/import")
            os.makedirs(IMPORT_PATH + "/import")
            os.chmod(IMPORT_PATH + "/import", 0o777)

        # ステータスを完了(異常)に更新
        util.setStatus(task['EXECUTION_NO'], STATUS_FAILURE, objdbca)
    return
