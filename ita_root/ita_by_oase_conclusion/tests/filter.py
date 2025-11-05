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

# pytest用フィルター定義
event_templates = {}
"Fillter F_A1定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_TARGET
p_group_label_names = (
    "_exastro_host,severity,service,status,severity,used_space,excluded_flg".split(",")
)
p_search_conditions = []
f_a1 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A1定義"
"Fillter F_A2定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET
p_group_label_names = "node,msg,clock,eventid".split(",")
p_search_conditions = []
f_a2 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A2定義"
"Fillter F_A3定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_TARGET
p_group_label_names = "_exastro_host,severity,service,status,severity".split(",")
p_search_conditions = []
f_a3 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A3定義"
"Fillter F_A4定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET
p_group_label_names = "node,msg,clock,eventid".split(",")
p_search_conditions = []
p_search_conditions.append(("excluded_flg", oaseConst.DF_TEST_EQ, "0"))
p_search_conditions.append(("_exastro_host", oaseConst.DF_TEST_NE, "systemZ"))
f_a4 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A4定義"
"Fillter F_A5定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_TARGET
p_group_label_names = "_exastro_host,severity,service,status,severity,used_space".split(
    ","
)
p_search_conditions = []
p_search_conditions.append(("excluded_flg", oaseConst.DF_TEST_EQ, "0"))
p_search_conditions.append(("_exastro_host", oaseConst.DF_TEST_NE, "systemZ"))
f_a5 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A5定義"
"Fillter F_A6定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET
p_group_label_names = "node,msg,clock,eventid,_exastro_host".split(",")
p_search_conditions = []
p_search_conditions.append(("excluded_flg", oaseConst.DF_TEST_EQ, "0"))
p_search_conditions.append(("service", oaseConst.DF_TEST_EQ, "Httpd"))
p_search_conditions.append(("status", oaseConst.DF_TEST_EQ, "Down"))
f_a6 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A6定義"
"Fillter F_A7定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_TARGET
p_group_label_names = "service,status,severity".split(",")
p_search_conditions = []
p_search_conditions.append(("excluded_flg", oaseConst.DF_TEST_EQ, "0"))
p_search_conditions.append(("service", oaseConst.DF_TEST_EQ, "Httpd"))
p_search_conditions.append(("status", oaseConst.DF_TEST_EQ, "Down"))
f_a7 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A7定義"
"Fillter F_A8定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET
p_group_label_names = "node,msg,clock,eventid".split(",")
p_search_conditions = []
p_search_conditions.append(("excluded_flg", oaseConst.DF_TEST_EQ, "0"))
p_search_conditions.append(("service", oaseConst.DF_TEST_EQ, "Mysqld"))
p_search_conditions.append(("status", oaseConst.DF_TEST_EQ, "Down"))
f_a8 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A8定義"
"Fillter F_A9定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_TARGET
p_group_label_names = "_exastro_host,severity,service,status,severity".split(",")
p_search_conditions = []
p_search_conditions.append(("excluded_flg", oaseConst.DF_TEST_EQ, "0"))
p_search_conditions.append(("service", oaseConst.DF_TEST_EQ, "Disk"))
p_search_conditions.append(("status", oaseConst.DF_TEST_EQ, "Full"))
f_a9 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A9定義"
"Fillter F_A10定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_TARGET
p_group_label_names = "_exastro_host,severity,service,status,severity".split(",")
p_search_conditions = []
p_search_conditions.append(("service", oaseConst.DF_TEST_EQ, "Disk"))
p_search_conditions.append(("status", oaseConst.DF_TEST_EQ, "Full"))
f_a10 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A10定義"
"Fillter F_A11定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET
p_group_label_names = "_exastro_host,severity,service,status,severity".split(",")
p_search_conditions = []
p_search_conditions.append(("service", oaseConst.DF_TEST_EQ, "Disk"))
p_search_conditions.append(("status", oaseConst.DF_TEST_EQ, "Full"))
f_a11 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A11定義"
"Fillter F_A12定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_TARGET
p_group_label_names = "node,msg,clock,eventid".split(",")
p_search_conditions = []
p_search_conditions.append(("excluded_flg", oaseConst.DF_TEST_EQ, "0"))
p_search_conditions.append(("service", oaseConst.DF_TEST_EQ, "Mysqld"))
p_search_conditions.append(("status", oaseConst.DF_TEST_EQ, "Down"))
f_a12 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A12定義"
"Fillter F_A13定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_TARGET
p_group_label_names = "node,msg,clock,eventid".split(",")
p_search_conditions = []
p_search_conditions.append(("service", oaseConst.DF_TEST_EQ, "Mysqld"))
p_search_conditions.append(("status", oaseConst.DF_TEST_EQ, "Down"))
f_a13 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A13定義"
"Fillter F_A14定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_TARGET
p_group_label_names = "node,service".split(",")
p_search_conditions = []
p_search_conditions.append(("service", oaseConst.DF_TEST_EQ, "Mysqld"))
p_search_conditions.append(("status", oaseConst.DF_TEST_EQ, "Down"))
f_a14 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A14定義"
"Fillter F_A15定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_TARGET
p_group_label_names = "service,status,severity".split(",")
p_search_conditions = []
p_search_conditions.append(("excluded_flg", oaseConst.DF_TEST_EQ, "1"))
p_search_conditions.append(("service", oaseConst.DF_TEST_EQ, "Httpd"))
p_search_conditions.append(("status", oaseConst.DF_TEST_EQ, "Down"))
f_a15 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A15定義"
"Fillter F_U_a定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_UNIQUE
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("type", oaseConst.DF_TEST_EQ, "a"))
f_u_a = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_U_a定義"
"Fillter F_U_b定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_UNIQUE
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("type", oaseConst.DF_TEST_EQ, "b"))
f_u_b = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_U_b定義"
"Fillter F_U_c定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_UNIQUE
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("type", oaseConst.DF_TEST_EQ, "c"))
f_u_c = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_U_c定義"
"Fillter F_U_d定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_UNIQUE
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("type", oaseConst.DF_TEST_EQ, "d"))
f_u_d = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_U_d定義"

"Fillter F_Q_a定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_QUEUING
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("type", oaseConst.DF_TEST_EQ, "qa"))
f_q_a = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_Q_a定義"
"Fillter F_Q_b定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_QUEUING
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("type", oaseConst.DF_TEST_EQ, "qb"))
f_q_b = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_Q_b定義"
"Fillter F_Q_c定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_QUEUING
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("type", oaseConst.DF_TEST_EQ, "qc"))
f_q_c = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_Q_c定義"
"Fillter F_Q_d定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_QUEUING
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("type", oaseConst.DF_TEST_EQ, "qd"))
f_q_d = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_Q_d定義"
"Fillter F_Q_1定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_QUEUING
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("mode", oaseConst.DF_TEST_EQ, "q1"))
f_q_1 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_Q_1定義"
"Fillter F_Q_2定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_QUEUING
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("mode", oaseConst.DF_TEST_EQ, "q2"))
f_q_2 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_Q_2定義"
"Fillter F_Q_3定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_QUEUING
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("mode", oaseConst.DF_TEST_EQ, "q3"))
f_q_3 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_Q_3定義"
"Fillter F_Q_4定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_QUEUING
p_group_condition_id = None
p_group_label_names = None
p_search_conditions = []
p_search_conditions.append(("mode", oaseConst.DF_TEST_EQ, "q4"))
f_q_4 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_Q_4定義"

"Fillter F_A99定義 ～"
p_search_condition_id = oaseConst.DF_SEARCH_CONDITION_GROUPING
p_group_condition_id = oaseConst.DF_GROUP_CONDITION_ID_NOT_TARGET
p_group_label_names = "node,msg,clock,eventid".split(",")
p_search_conditions = []
p_search_conditions.append(("excluded_flg", oaseConst.DF_TEST_EQ, "1"))
f_a99 = create_filter_row(
    p_search_condition_id,
    (p_search_conditions if len(p_search_conditions) > 0 else None),
    p_group_condition_id,
    p_group_label_names,
)
"Fillter F_A99定義"
# pytest用フィルター定義
