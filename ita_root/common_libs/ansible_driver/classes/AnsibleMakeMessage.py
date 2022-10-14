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

"""
Ansibleメッセージ作成module
"""

from flask import g

from .AnscConstClass import AnscConst


class AnsibleMakeMessage():
    
    def AnsibleMakeMessage(self, chkmode, msgcode, paramAry=[]):
    
        # 変数定義の解析に失敗しました。{}
        msgtbldict = {'MSG-10301': 'value'}
        msgtbldict['MSG-10301'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue'}
        msgtbldict['MSG-10301']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10577', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10578'}
        msgtbldict['MSG-10301']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '0,3'}
        # 変数定義が想定外なので解析に失敗しました。{}
        msgtbldict['MSG-10302'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue'}
        msgtbldict['MSG-10302']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10312', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10313'}
        msgtbldict['MSG-10302']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '0'}
        # 繰返階層の変数定義が一致していません。{}
        msgtbldict['MSG-10303'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue'}
        msgtbldict['MSG-10303']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10577', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10578'}
        msgtbldict['MSG-10303']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '0,3'}
        # 代入順序が複数必要な変数定義になっています。{}
        msgtbldict['MSG-10304'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue2'}
        msgtbldict['MSG-10304']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10577', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10578'}
        msgtbldict['MSG-10304']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '0,3'}
        # 繰返構造の繰返数が99999999を超えてた定義です。{}
        msgtbldict['MSG-10444'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue2'}
        msgtbldict['MSG-10444']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10577', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10578'}
        msgtbldict['MSG-10444']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '0,3'}
        # 変数が二重定義されています。{}
        msgtbldict['MSG-10568'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue2'}
        msgtbldict['MSG-10568']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10577', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10578'}
        msgtbldict['MSG-10568']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '0,3'}
        # ファイル埋込変数がファイル管理に登録されていません。{}
        msgtbldict['MSG-10408'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue2'}
        msgtbldict['MSG-10408']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10583', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10584'}
        msgtbldict['MSG-10408']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '2,3'}
        # ファイル埋込変数に紐づくファイルがファイル管理に登録されていません。 {}
        msgtbldict['MSG-10409'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue2'}
        msgtbldict['MSG-10409']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10583', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10584'}
        msgtbldict['MSG-10409']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '2,3'}
        # テンプレート埋込変数に紐づくファイルがテンプレート管理に登録されていません。{}
        msgtbldict['MSG-10557'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue2'}
        msgtbldict['MSG-10557']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10585', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10586'}
        msgtbldict['MSG-10557']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '2,3'}
        # テンプレート埋込変数がテンプレート管理に登録されていません。{}
        msgtbldict['MSG-10559'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue2'}
        msgtbldict['MSG-10559']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10585', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10586'}
        msgtbldict['MSG-10559']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '2,3'}
        # グローバル変数がグローバル管理に登録されていません。 {})
        msgtbldict['MSG-10571'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue2'}
        msgtbldict['MSG-10571']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10587', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10588'}
        msgtbldict['MSG-10571']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '2,3'}
        # 変数名が不正です。{}
        msgtbldict['MSG-10306'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue2'}
        msgtbldict['MSG-10306']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10307', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-10308'}
        msgtbldict['MSG-10306']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '0,3'}
        # メンバー変数名が不正です。メンバー変数名に 「 ．(ドット)  [  ] 」の3記号は使用できません。{}
        msgtbldict['MSG-10309'] = {'msgcode': 'subvalue', 'paramlist': 'subvalue2'}
        msgtbldict['MSG-10309']['msgcode'] = {AnscConst.LC_RUN_MODE_STD: 'MSG-10310', AnscConst.LC_RUN_MODE_VARFILE: 'MSG-1031'}
        msgtbldict['MSG-10309']['paramlist'] = {AnscConst.LC_RUN_MODE_STD: 'all', AnscConst.LC_RUN_MODE_VARFILE: '0,3,4'}

        pram_code = ""
        result_msg = ""
        param_list = ""
        
        if msgcode not in msgtbldict.keys():
            result_msg = g.appmsg.get_api_message(msgcode, paramAry)
        else:
            for mode, code in msgtbldict[msgcode]['msgcode'].items():
                if chkmode == mode:
                    pram_code = code
                    break
            for mode, plist in msgtbldict[msgcode]['paramlist'].items():
                if chkmode == mode:
                    param_list = plist
                    break
            if pram_code != "":
                if param_list == 'all':
                    parm_msg = g.appmsg.get_api_message(pram_code, paramAry)
                    result_msg = g.appmsg.get_api_message(msgcode, [parm_msg])
                else:
                    param_msg = []
                    for param_no in param_list.split(','):
                        param_msg.append(paramAry[int(param_no)])

                    parm_msg = g.appmsg.get_api_message(pram_code, param_msg)
                    result_msg = g.appmsg.get_api_message(msgcode, [parm_msg])

        return result_msg
