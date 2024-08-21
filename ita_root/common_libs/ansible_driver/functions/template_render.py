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
from flask import g
from jinja2 import Template, Environment, FileSystemLoader

"""
  jinja2読み込み共通モジュール
"""
def TemplateRender(path,file,item):
    """
      jinja2の読み込みを行う
      Arguments:
        path: jinja2ファイルのパス
        file: jinja2ファイル
        item: 置換する辞書
      Returns:
        ansible-runnerの出力用パス
    """
    env = Environment(loader=FileSystemLoader(path, encoding='utf8'))
    tmpl = env.get_template(file)
    return tmpl.render(item)
