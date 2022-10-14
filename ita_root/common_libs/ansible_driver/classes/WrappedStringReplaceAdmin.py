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
import re
from common_libs.ansible_driver.classes.AnsrConstClass import AnscConst
"""
  指定文字列からの変数抜出及び変数具体値置き換モジュール
"""


class WrappedStringReplaceAdmin:
    """
      指定文字列からの変数抜出及び変数具体値置き換えクラス
    """
    def __init__(self, objdbca=None):
        AnscObj = AnscConst()
        self.strReplacedString = ''
        self.UnmngRows = []
        if objdbca:
            # 管理対象外変数取得
            sql = "SELECT VAR_NAME FROM T_ANSC_UNMANAGED_VARLIST WHERE DISUSE_FLAG='0'"
            Rows = objdbca.sql_execute(sql, [])
            for row in Rows:
                self.UnmngRows.append(row["VAR_NAME"])
            self.UnmngRows.extend(AnscObj.Unmanaged_ITA_sp_varlist)

    def stringReplace(self, strSourceString, aryReplaceSource):
        """
          変数を具体値に置き換え
          Arguments:
            strSourceString:(in)   置き換え対象の文字列
            aryReplaceSource:(in)  置換えする変数と具体値の辞書リスト
                                    [{変数名:具体値} , ...]
          Returns:
            True(bool)
        """
        boolRet = True

        strHeadPattern = "{{ "
        strTailPattern = " }}"
        self.strReplacedString = ""

        if strSourceString is None:
            strSourceString = ""

        # 入力データを行単位に分解
        arry_list = strSourceString.split("\n")
        for lineString in arry_list:
            lineString = lineString + "\n"
            if lineString.find("#") == 0:
                self.strReplacedString += lineString
            else:
                # エスケープコード付きの#を一時的に改行に置換
                wstr = lineString
                rpstr = wstr.replace("\\\#", "\n\n")
                # コメント( #)マーク以降の文字列を削除した文字列で変数の具体値置換
                # #の前の文字がスペースの場合にコメントとして扱う
                splitList = rpstr.split(' #')
                lineString = splitList[0]
                splitList.pop(0)
                # 各変数を具体値に置換
                for dectReplace in aryReplaceSource:
                    for strVar, strVal in dectReplace.items():
                        # 変数を具体値に置換
                        strVarName = strHeadPattern + strVar + strTailPattern
                        strReplace = lineString.replace(strVarName, strVal)
                        lineString = strReplace
                # コメント(#)以降の文字列を元に戻す。
                for strLine in splitList:
                    lineString += " #" + strLine
                # エスケープコード付きの#を元に戻す。
                rpstr = lineString.replace("\n\n", "\#")
                self.strReplacedString += rpstr
        return boolRet

    def getReplacedString(self):
        """
          stringReplaceで変数を具体値に置き換えた結果取得
          Arguments:
            None
          Returns:
            変数を具体値に置き換えた結果文字列
        """
        return self.strReplacedString

    def SimpleFillterVerSearch(self, var_heder_id, strSourceString, mt_varsLineArray, mt_varsArray, arryLocalMnageVars, FillterVars=False):
        """
          指定された文字列から指定された変数を抜出す。
          Arguments:
            var_heder_id:(in)            変数名の先頭文字列　TPF_, ""
            in_strSourceString:(in)      変数を抜出す文字列
            mt_varsLineArray:(out)       抜出した変数リスト       呼出元で空リストで初期化必須
                                         [{行番号:変数名}, ...]
            mt_varsarray:(out)           抜出した変数リスト       呼出元で空リストで初期化必須
                                         [変数名, .....]
            arryLocalMnageVars:               管理対象外変数のリストから除外したい変数リスト
            FillterVars:(in)             Fillter設定されている変数抜出有無(bool)
          Returns:
            True(bool)
        """
        # Fillter定義されている変数も抜出すか判定
        tailmarke = []
        if FillterVars is True:
            tailmarke.append("[\s]}}")
            tailmarke.append("[\s]+\|")
        else:
            tailmarke.append("[\s]}}")

        if strSourceString is None:
            strSourceString = ""

        # 入力データを行単位に分解
        arry_list = strSourceString.split("\n")
        line = 0
        for lineString in arry_list:
            # 行番号
            line += 1
    
            lineString += "\n"
            # コメント行は読み飛ばす
            if lineString.find("#") == 0:
                continue

            # エスケープコード付きの#を一時的に改行に置換
            wstr = lineString
            # コメント( #)マーク以降の文字列を削除する。
            # #の前の文字がスペースの場合にコメントとして扱う
            splitList = wstr.split(' #')
            strRemainString = splitList[0]
            if len(str.strip(strRemainString)) == 0:
                # 空行は読み飛ばす
                continue
            # 変数名　{{ ???_[a-zA-Z0-9_] | Fillter function }} または{{ ???_[a-zA-Z0-9_] }}　を取出す
            match_list = []
            for key in tailmarke:
                keyFilter = "{{[\s]" + var_heder_id + "[a-zA-Z0-9_]*" + key
                match = re.findall(keyFilter, strRemainString)
                for row in match:
                    # 変数名を抜出す
                    keyFilter = "[\s]" + var_heder_id + "[a-zA-Z0-9_]*" + "[\s]"
                    var_name = re.findall(keyFilter, row)
                    var_name = var_name[0].strip()
                    # 管理対象外変数確認
                    ret = self.chkUnmanagedVarname(var_heder_id, var_name, [])
                    if ret is False:
                        match_list.append(var_name)
            if len(match_list) != 0:
                # 重複値を除外
                unique_set = set(match_list)
            else:
                unique_set = []
            for var_name in unique_set:
                # 変数位置退避
                var_dict = {}
                var_dict[line] = var_name
                mt_varsLineArray.append(var_dict)

                # 変数名の重複チェック
                if mt_varsArray.count(var_name) == 0:
                    mt_varsArray.append(var_name)

            # --- 予約変数　{{ 予約変数 | Fillter function }}　の抜き出し
            for localvarname in arryLocalMnageVars:
                match_list = []
                for key in tailmarke:
                    keyFilter = "{{[\s]" + localvarname + key
                    match = re.findall(keyFilter, strRemainString)

                    for row in match:
                        # 変数名を抜出す
                        keyFilter = "[\s]" + localvarname + "[\s]"
                        var_name = re.findall(keyFilter, row)
                        if len(var_name) == 0:
                            continue
                        match_list.append(var_name[0].strip())

                if len(match_list) != 0:
                    # 重複値を除外
                    unique_set = set(match_list)
                else:
                    unique_set = []

                for var_name in unique_set:

                    # 変数位置退避
                    var_dict = {}
                    var_dict[line] = var_name
                    mt_varsLineArray.append(var_dict)

                    # 変数名の重複チェック
                    if mt_varsArray.count(var_name) == 0:
                        mt_varsArray.append(var_name)
                        
            # 予約変数　{{ 予約変数 | Fillter function }}　の抜き出し ---
        return True, mt_varsLineArray
    
    def chkUnmanagedVarname(self, var_heder_id, var_name, arryLocalMnageVars=[]):
        """
          指定された変数名が管理対象外か判定する。
          Arguments:
            var_heder_id:(in)  変数名の先頭文字列　VAR_, ""
            var_name: 変数名
            arryLocalMnageVars: 管理対象外変数のリストから除外したい変数リスト
          Returns:
            True:   除外
            False:  適用
        """
        AnscObj = AnscConst()
        # VAR変数以外の場合は除外判定はしない
        if var_heder_id != AnscObj.DF_HOST_VAR_HED:
            return False
        # 除外リストに含まれる変数か判定
        retBool = False
        for key in self.UnmngRows:
            keyFilter = "^" + key + "$"
            match = re.findall(keyFilter, var_name)
            if len(match) != 0:
                # 管理対象外変数のリストから除外したい変数か判定
                if key in arryLocalMnageVars:
                    retBool = False
                else:
                    retBool = True
                break
        return retBool
