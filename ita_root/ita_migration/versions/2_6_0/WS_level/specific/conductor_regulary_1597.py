#   Copyright 2024 NEC Corporation
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

import json
from flask import g


def main(work_dir_path, wsdb):
    g.applogger.info("[Trace] Begin Conductor Regulary migrate(specific). #issue1597")


    table_name = "t_comn_conductor_regularly_list"
    data_list = wsdb.table_select(table_name, "WHERE REGULARLY_PERIOD_ID = %s", ["3"])
    for data in data_list:
        weekday_id_dict = {"id": [data["PATTERN_DAY_OF_WEEK_ID"]]}
        update_data = {
            "REGULARLY_ID": data["REGULARLY_ID"],
            "PATTERN_DAY_OF_WEEK_ID": json.dumps(weekday_id_dict)
        }
        wsdb.table_update(table_name, update_data, "REGULARLY_ID", True)

    wsdb.db_commit()

    return 0

