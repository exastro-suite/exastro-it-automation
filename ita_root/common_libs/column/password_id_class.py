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

from flask import g  # noqa: F401
from common_libs.common import *  # noqa: F401,F403

# import column_class
from .id_class import IDColumn


class PasswordIDColumn(IDColumn):
    """
    カラムクラス個別処理(PasswordIDColumn)
    """
    
    def convert_value_output(self, val=''):
        """
            値を暗号化
            ARGS:
                val:値
            RETRUN:
                retBool, msg, val
        """
        retBool = True
        msg = ''
        val = None

        return retBool, msg, val
