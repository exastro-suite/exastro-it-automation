# Copyright 2023 NEC Corporation#
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

import chardet
import jinja2
import re


def is_binary_file(template_data_binary):
    """ファイルの形式をチェックする。バイナリファイルの場合はエラーを返す。
    空のファイルの場合も本判定でエラーとする

    Args:
        template_data_binary (bytes): base64.b64decodeで取得したbytes
    RETRUN:
        result :True（正常）/ False（エラー）
    """

    encode = chardet.detect(template_data_binary)
    return encode['encoding'] is None


def is_jinja2_template(template_data_decoded):
    """jinja2のテンプレートとして問題無いかチェックする。

    Args:
        template_data_decoded (str): 評価する文字列
    RETRUN:
        result :True（正常）/ False（エラー）
    """

    try:
        jinja2.Template(template_data_decoded)
    except Exception:
        return False

    return True


def contains_title(template_data_decoded):
    """テンプレートに[TITLE]を含むかチェックする。
    含まない、もしくは複数含む場合はエラーとする。

    Args:
        template_data_decoded (str): 評価する文字列
    RETRUN:
        result :True（正常）/ False（エラー）
    """

    title_count = len(re.findall(r'\[TITLE\]', template_data_decoded))
    return title_count == 1


def contains_body(template_data_decoded):
    """テンプレートに[BODY]を含むかチェックする。
    含まない、もしくは複数含む場合はエラーとする。

    Args:
        template_data_decoded (str): 評価する文字列
    RETRUN:
        result :True（正常）/ False（エラー）
    """

    body_count = len(re.findall(r'\[BODY\]', template_data_decoded))
    return body_count == 1
