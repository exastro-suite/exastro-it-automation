#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from flask import g
from common_libs.loadtable import *  # noqa: F403
import ast

def set_reference_value(objdbca, objtable, option):
    retBool = True
    msg = ''
    
    # カラムインフォを取得
    rest_key_name = option.get('rest_key_name')
    menu_name_rest = objtable.get('MENUINFO').get('MENU_NAME_REST')
    objcols = objtable.get('COLINFO')
    objcol = objcols.get(rest_key_name)
    
    # 参照項目の対象を取得
    reference_item_list = objcol.get('REFERENCE_ITEM')
    reference_item_list = ast.literal_eval(reference_item_list)
    
    # 設定値を取得
    entry_reference_value = option.get('entry_parameter').get('parameter').get(rest_key_name)
    objmenu = load_table.loadTable(objdbca, menu_name_rest)
    objcolumn = objmenu.get_columnclass(rest_key_name)
    tmp_exec = objcolumn.convert_value_input(entry_reference_value)
    if tmp_exec[0] is True:
        entry_reference_value = tmp_exec[2]
        
    # 参照項目の数だけ、参照項目用の値を代入する
    if type(reference_item_list) is list:
        for target_column_name_rest in reference_item_list:
            option['entry_parameter']['parameter'][target_column_name_rest] = entry_reference_value
    
    return retBool, msg, option, False
