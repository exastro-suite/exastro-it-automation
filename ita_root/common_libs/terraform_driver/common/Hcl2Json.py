#   Copyright 2023 NEC Corporation
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
import hcl2
import json
import re


class HCL2JSONParse():
    """
    【概要】
        hcl(tfファイル)をjson形式にparseする
    """
    def __init__(self, file_path):
        """
        コンストラクタ
        Arguments:
        Returns:
        """
        self.file_path = file_path
        self.variable_block_list = []
        self.res = True
        self.error_msg = ""

    def getParseResult(self):
        """
        解析結果を返却
        Arguments:
        Returns:
            result(dict)
        """
        result = {
            "res": self.res,
            "variables": self.variable_block_list,
            "error_msg": self.error_msg
        }

        return result

    def executeParse(self, valid_check=False):  # noqa: C901
        """
        hcl -> jsonパーサーを実行する
        Arguments:
        Returns:
            result(dict)
        """
        try:
            result = True

            # 対象ファイルの解析を実行
            with open(self.file_path, 'r') as file:
                parse_result = hcl2.load(file)
                result_json = json.dumps(parse_result)

            # typeがnullの場合を考慮し、処理しやすい形に変換
            pattern = r'\"type\"\:\s(null)'
            replacement = r'"type": "${null}"'
            result_json = re.sub(pattern, replacement, result_json)

            # jsonをdict化
            result_dict = json.loads(result_json)

            # variableブロックのみを抽出
            variable_list = result_dict.get('variable')

            # variableブロックがない場合は終了
            if not variable_list:
                self.res = result
                return result

            # variableブロックのtypeを形成する
            for variable_block in variable_list:
                for variable, block in variable_block.items():
                    convert_block = {}
                    block_type = None
                    block_type_str = None
                    block_variable = variable
                    block_default = block.get('default')
                    type_str = block.get('type')

                    # block_variable(変数名)のバリデーションチェック（ファイル登録時のみ処理を通る）
                    if valid_check is True:
                        # 変数名が128byte以上の場合はバリデーションエラー
                        if len(block_variable.encode()) > 128:
                            msg = g.appmsg.get_api_message("MSG-80025", [block_variable])
                            raise Exception(msg)

                    # type_strがNoneではない場合は整形処理を通す
                    if type_str:
                        # typeのエスケープ文字を消去
                        pattern = r'\\'
                        replacement = r''
                        match = re.findall(pattern, type_str)
                        if match:
                            type_str = re.sub(pattern, replacement, type_str)

                        pattern = r'/\"(.*?)\"/'
                        replacement = r'\'\1\''
                        match = re.findall(pattern, type_str)
                        if match:
                            type_str = re.sub(pattern, replacement, type_str)

                        pattern = r'\'(.*?)\''
                        replacement = r'"\1"'
                        match = re.findall(pattern, type_str)
                        if match:
                            type_str = re.sub(pattern, replacement, type_str)

                        type_str = '"' + type_str + '"'

                        # ),)のカンマを削除
                        pattern = r'\)\,\)'
                        replacement = r'))'
                        match = re.findall(pattern, type_str)
                        while match:
                            type_str = re.sub(pattern, replacement, type_str)
                            match = re.findall(pattern, type_str)

                        # typeがlist/setの場合の対応(1~4)
                        # 1. list(string) => list(string) 代入順序なし、メンバー変数なしの場合は対応なし
                        # pattern = r'\$\{([a-z]+?)\(([a-z]+?)\((.*?)\)\)\}'
                        # replacement = r'"${\1(\2)}"'

                        # 2. list(list(string)) => ${list(list)} + ${list(string)}
                        pattern = r'\"\$\{([a-z]+?)\(([a-z]+?)\((.*?)\)\)\}\"'
                        replacement = r'{"${\1(\2)}": ["${\2(\3)}"]}'
                        match = re.findall(pattern, type_str)
                        while match:
                            type_str = re.sub(pattern, replacement, type_str)
                            match = re.findall(pattern, type_str)

                        # 3. tuple
                        pattern = r'\"\$\{([a-z]+?)\(([a-z]+?)\(\[(.*)\]\)\)\}\"'
                        replacement = r'{"${\1}": ["${\2([\3])}"]}'
                        match = re.findall(pattern, type_str)
                        while match:
                            type_str = re.sub(pattern, replacement, type_str)
                            match = re.findall(pattern, type_str)

                        # 4. object
                        pattern = r'\"\$\{([a-z]+?)\(([a-z]+?)\(\{(.*)\}\)\)\}\"'
                        replacement = r'{"${\1}": ["${\2({\3})}"]}'
                        match = re.findall(pattern, type_str)
                        while match:
                            type_str = re.sub(pattern, replacement, type_str)
                            match = re.findall(pattern, type_str)

                        # typeがtupleの場合の対応
                        # 入れ子になっている場合
                        pattern = r'\"\$\{([a-z]+?)\(\[(.*)\]\)\}\"'
                        replacement = r'{"${\1}": [\2]}'
                        match = re.findall(pattern, type_str)
                        while match:
                            type_str = re.sub(pattern, replacement, type_str)
                            match = re.findall(pattern, type_str)

                        pattern = r'\$\{([a-z]+?)\(\[(.*)\]\)\}'
                        replacement = r'{"${\1}": [\2]}'
                        match = re.findall(pattern, type_str)
                        while match:
                            type_str = re.sub(pattern, replacement, type_str)
                            match = re.findall(pattern, type_str)

                        # 入れ子以外で並んでいる場合
                        pattern = r'\"\$\{([a-z]*?)\(\[(.*)\]\)\}\"'
                        replacement = r'{"${\1}": [\2]}'
                        match = re.findall(pattern, type_str)
                        if match:
                            type_str = re.sub(pattern, replacement, type_str)

                        pattern = r'\]\)\}\"(.*)\"\$\{([a-z]*?)\(\[(.*)'
                        replacement = r']}\1{"${\2}": [\3'
                        match = re.findall(pattern, type_str)
                        if match:
                            type_str = re.sub(pattern, replacement, type_str)

                        # typeがobjectの場合
                        # 入れ子になっている場合
                        pattern = r'\"\$\{([a-z]+?)\(\{(.*)\}\)\}\"'
                        replacement = r'{"${\1}": {\2}}'
                        match = re.findall(pattern, type_str)
                        while match:
                            type_str = re.sub(pattern, replacement, type_str)
                            match = re.findall(pattern, type_str)

                        # 入れ子以外で並んでいる場合
                        pattern = r'\"\$\{([a-z]*?)\(\{(.*)\}\)\}\"'
                        replacement = r'{"${\1}": {\2}}'
                        match = re.findall(pattern, type_str)
                        if match:
                            type_str = re.sub(pattern, replacement, type_str)

                        pattern = r'\}\)\}\"(.*)\"\$\{([a-z]*?)\(\{(.*)'
                        replacement = r'}}\1{"${\2}": {\3'
                        match = re.findall(pattern, type_str)
                        if match:
                            type_str = re.sub(pattern, replacement, type_str)

                        # typeがNoneの場合の対応
                        pattern = r'\"(.*?)\\:\s(None)\"'
                        replacement = r'\1: "${null}"'
                        match = re.findall(pattern, type_str)
                        if match:
                            type_str = re.sub(pattern, replacement, type_str)

                        # json.loads可能かどうかを判定し、可能であれば実行
                        try:
                            block_type = json.loads(type_str)
                        except Exception:
                            block_type = type_str

                        # map型が含まれる場合はすべてをmap型とみなす
                        is_map_flag = self.isMapCheck(block_type, False)
                        if is_map_flag:
                            block_type = '${map}'

                        # Module変数紐付管理に登録するための値に変換
                        module_record_type = self.getModuleRecord(block_type)

                        # typeのvalueについている${}を除外
                        pattern = r'^\$\{(.*?)\}$'
                        match = re.findall(pattern, module_record_type)
                        if match:
                            block_type_str = match[0]

                    # 変換前のtypeをセット
                    convert_block['type'] = block_type

                    # string型に変換したtypeをセット
                    convert_block['type_str'] = block_type_str

                    # variableをセット
                    convert_block['variable'] = block_variable

                    # defaultをセット
                    convert_block['default'] = block_default
                    # variable_block_listに格納
                    self.variable_block_list.append(convert_block)

        except Exception as e:
            self.error_msg = e
            result = False

        self.res = result
        return result

    def getModuleRecord(self, block_type):
        """
        Module変数紐付管理に登録する用の値を取得する
        Arguments:
            block_type
        Returns:
            result(dict)
        """
        if isinstance(block_type, dict):
            for type_key, type_value in block_type.items():
                first_type_key = type_key
                return first_type_key
        else:
            first_type_key = block_type
            return first_type_key

    def isMapCheck(self, block_type, is_map_flag):
        """
        map型かどうかの判定
        Arguments:
        Returns:
            boolean
        """
        ret = False
        pattern1 = r'^\$\{map(.*?)\}$'
        pattern2 = r'^\$\{map\}$'
        if isinstance(block_type, dict) and is_map_flag is False:
            # mapの存在をチェックする
            for type_key, type_value in block_type.items():
                if re.findall(pattern1, type_key) or re.findall(pattern2, type_key):  # noqa: E501
                    ret = True

                if ret is False:
                    # type_valueが入れ子になっている場合は再度isMapCheckを実行
                    if isinstance(type_value, dict) or isinstance(type_value, list):
                        ret2 = self.isMapCheck(type_value, False)
                        if ret2:
                            ret = True
                    else:
                        if re.findall(pattern1, type_key) or re.findall(pattern2, type_key) or re.findall(pattern1, type_value) or re.findall(pattern2, type_value):  # noqa: E501
                            ret = True

        elif isinstance(block_type, list) and is_map_flag is False:
            # mapの存在をチェックする
            for type_value in block_type:
                # type_valueが入れ子になっている場合は再度isMapCheckを実行
                if isinstance(type_value, dict) or isinstance(type_value, list):
                    ret2 = self.isMapCheck(type_value, False)
                    if ret2:
                        ret = True
                else:
                    if re.findall(pattern1, type_value) or re.findall(pattern2, type_value):  # noqa: E501
                        ret = True

        else:
            if re.findall(pattern1, block_type) or re.findall(pattern2, block_type):
                ret = True

        return ret
