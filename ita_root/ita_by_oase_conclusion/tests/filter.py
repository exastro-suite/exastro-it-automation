#   Copyright 2025 NEC Corporation
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

from common_libs.oase.const import oaseConst
from tests.common import create_filter_row

# 参考データ
f_a6 = create_filter_row(
    oaseConst.DF_SEARCH_CONDITION_GROUPING,
    [
        ("excluded_flg", oaseConst.DF_TEST_EQ, "0"),
        ("_exastro_host", oaseConst.DF_TEST_NE, "systemZ"),
    ],
    oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET,
    ["node", "msg", "clock", "eventid"],
)
f_a4 = create_filter_row(
    oaseConst.DF_SEARCH_CONDITION_GROUPING,
    [
        ("excluded_flg", oaseConst.DF_TEST_EQ, "0"),
        ("service", oaseConst.DF_TEST_EQ, "Httpd"),
        ("status", oaseConst.DF_TEST_EQ, "Down"),
    ],
    oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET,
    ["node", "msg", "clock", "eventid", "_exastro_host"],
)
