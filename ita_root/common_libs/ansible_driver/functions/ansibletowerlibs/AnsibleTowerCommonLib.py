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


from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from common_libs.ansible_driver.classes.AnsrConstClass import AnsrConst


def addPadding(num):

    return str(num).zfill(10)

def isScrammedExecution(dbAccess, tgt_execution_no):

    vg_exe_ins_msg_table_name = AnsrConst.vg_exe_ins_msg_table_name

    sql = (
        "SELECT                \n"
        "  STATUS_ID           \n"
        "FROM                  \n"
        "  %s \n"
        "WHERE                 \n"
        "  DISUSE_FLAG='0'     \n"
        "  AND EXECUTION_NO = %%s; \n"
    ) % (vg_exe_ins_msg_table_name)

    row = dbAccess.sql_execute(sql, [tgt_execution_no])
    if len(row) >= 2:
        raise Exception("There are multiple rows returned for the primary key specification.: %s: %s" % (vg_exe_ins_msg_table_name, sql))

    if len(row) < 1:
        return False

    if row[0]['STATUS_ID'] == AnscConst.SCRAM:
        return True

    return False
